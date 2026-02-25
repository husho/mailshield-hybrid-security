from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.utils.class_weight import compute_sample_weight

from .dataset import LABEL_TO_IDX, IDX_TO_LABEL, prepare_data
from .features import build_window_samples
from .infer import load_artifacts
from .parsers import iter_events


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate deep model and baselines")
    parser.add_argument("--logs-dir", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--salt", type=str, default="mailshield-default-salt")
    parser.add_argument("--window-minutes", type=int, default=15)
    parser.add_argument("--seq-len", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=2048)
    parser.add_argument("--max-files-per-source", type=int, default=0)
    parser.add_argument("--baseline-max-train", type=int, default=250000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)


def _classification_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=list(IDX_TO_LABEL.keys()),
        average="macro",
        zero_division=0,
    )
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision),
        "recall_macro": float(recall),
        "f1_macro": float(f1),
    }

    per_class = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=list(IDX_TO_LABEL.keys()),
        average=None,
        zero_division=0,
    )
    for idx, label in IDX_TO_LABEL.items():
        metrics[f"precision_{label}"] = float(per_class[0][idx])
        metrics[f"recall_{label}"] = float(per_class[1][idx])
        metrics[f"f1_{label}"] = float(per_class[2][idx])

    return metrics


def _roc_auc_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    out: Dict[str, float] = {}
    try:
        out["macro_ovr"] = float(
            roc_auc_score(y_true, y_prob, multi_class="ovr", average="macro", labels=list(IDX_TO_LABEL.keys()))
        )
    except ValueError:
        out["macro_ovr"] = float("nan")

    for idx, label in IDX_TO_LABEL.items():
        binary_true = (y_true == idx).astype(np.int32)
        if np.unique(binary_true).size < 2:
            out[f"{label}_ovr"] = float("nan")
            continue
        try:
            out[f"{label}_ovr"] = float(roc_auc_score(binary_true, y_prob[:, idx]))
        except ValueError:
            out[f"{label}_ovr"] = float("nan")

    return out


def _write_confusion_csv(path: Path, y_true: np.ndarray, y_pred: np.ndarray) -> None:
    labels = [IDX_TO_LABEL[i] for i in sorted(IDX_TO_LABEL.keys())]
    matrix = confusion_matrix(y_true, y_pred, labels=sorted(IDX_TO_LABEL.keys()))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["true\\pred", *labels])
        for i, row in enumerate(matrix):
            writer.writerow([labels[i], *row.tolist()])


def _downsample_train(
    x_train: np.ndarray,
    y_train: np.ndarray,
    max_items: int,
    seed: int,
) -> Tuple[np.ndarray, np.ndarray]:
    if x_train.shape[0] <= max_items:
        return x_train, y_train

    rng = np.random.default_rng(seed)
    idx = np.arange(x_train.shape[0])
    rng.shuffle(idx)
    idx = idx[:max_items]
    return x_train[idx], y_train[idx]


def _fit_random_forest(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    seed: int,
) -> Tuple[np.ndarray, np.ndarray]:
    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=1,
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=seed,
    )
    sw = compute_sample_weight(class_weight="balanced", y=y_train)
    clf.fit(x_train, y_train, sample_weight=sw)
    y_pred = clf.predict(x_test)
    y_prob = clf.predict_proba(x_test)
    return y_pred, y_prob


def _fit_xgboost_or_fallback(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
    seed: int,
) -> Tuple[str, np.ndarray, np.ndarray]:
    try:
        from xgboost import XGBClassifier

        clf = XGBClassifier(
            objective="multi:softprob",
            num_class=len(IDX_TO_LABEL),
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            random_state=seed,
            n_jobs=-1,
            eval_metric="mlogloss",
            verbosity=0,
        )
        sw = compute_sample_weight(class_weight="balanced", y=y_train)
        clf.fit(x_train, y_train, sample_weight=sw)
        return "xgboost", clf.predict(x_test), clf.predict_proba(x_test)
    except Exception:
        from sklearn.ensemble import HistGradientBoostingClassifier

        clf = HistGradientBoostingClassifier(
            learning_rate=0.1,
            max_iter=300,
            max_depth=8,
            random_state=seed,
        )
        sw = compute_sample_weight(class_weight="balanced", y=y_train)
        clf.fit(x_train, y_train, sample_weight=sw)
        y_prob = clf.predict_proba(x_test)
        y_pred = np.argmax(y_prob, axis=1)
        return "hist_gradient_boosting", y_pred, y_prob


def _deep_predict(
    model_dir: Path,
    x_seq: np.ndarray,
    x_static: np.ndarray,
    host_idx: np.ndarray,
    batch_size: int,
) -> Tuple[np.ndarray, np.ndarray]:
    artifacts = load_artifacts(model_dir=model_dir)
    device = artifacts.device

    seq_tensor = torch.tensor(x_seq, dtype=torch.float32)
    static_tensor = torch.tensor(x_static, dtype=torch.float32)
    host_tensor = torch.tensor(host_idx, dtype=torch.int64)

    probs_all: List[np.ndarray] = []
    preds_all: List[np.ndarray] = []

    artifacts.model.eval()
    with torch.no_grad():
        for start in range(0, seq_tensor.shape[0], batch_size):
            end = min(start + batch_size, seq_tensor.shape[0])
            logits = artifacts.model(
                seq_tensor[start:end].to(device),
                static_tensor[start:end].to(device),
                host_tensor[start:end].to(device),
            )
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            preds = np.argmax(probs, axis=1)
            probs_all.append(probs)
            preds_all.append(preds)

    return np.concatenate(preds_all), np.concatenate(probs_all)


def _render_markdown(summary: Dict) -> str:
    deep = summary["deep_model"]
    rf = summary["baselines"]["random_forest"]
    xb_name = summary["baselines"]["secondary_name"]
    xb = summary["baselines"]["secondary"]

    return "\n".join(
        [
            "# Model Comparison Report",
            "",
            "## Test split metrics",
            "",
            "| Model | Accuracy | Precision Macro | Recall Macro | F1 Macro | Recall Normal | Recall Anomaly | Recall Spam |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
            f"| Deep Hybrid (GRU+MLP) | {deep['metrics']['accuracy']:.6f} | {deep['metrics']['precision_macro']:.6f} | {deep['metrics']['recall_macro']:.6f} | {deep['metrics']['f1_macro']:.6f} | {deep['metrics']['recall_normal']:.6f} | {deep['metrics']['recall_anomaly']:.6f} | {deep['metrics']['recall_spam']:.6f} |",
            f"| RandomForest | {rf['metrics']['accuracy']:.6f} | {rf['metrics']['precision_macro']:.6f} | {rf['metrics']['recall_macro']:.6f} | {rf['metrics']['f1_macro']:.6f} | {rf['metrics']['recall_normal']:.6f} | {rf['metrics']['recall_anomaly']:.6f} | {rf['metrics']['recall_spam']:.6f} |",
            f"| {xb_name} | {xb['metrics']['accuracy']:.6f} | {xb['metrics']['precision_macro']:.6f} | {xb['metrics']['recall_macro']:.6f} | {xb['metrics']['f1_macro']:.6f} | {xb['metrics']['recall_normal']:.6f} | {xb['metrics']['recall_anomaly']:.6f} | {xb['metrics']['recall_spam']:.6f} |",
            "",
            "## ROC-AUC (One-vs-Rest)",
            "",
            f"- Deep Hybrid macro OVR AUC: {deep['roc_auc'].get('macro_ovr', float('nan')):.6f}",
            f"- RandomForest macro OVR AUC: {rf['roc_auc'].get('macro_ovr', float('nan')):.6f}",
            f"- {xb_name} macro OVR AUC: {xb['roc_auc'].get('macro_ovr', float('nan')):.6f}",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    _set_seed(args.seed)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    events = iter_events(
        logs_dir=args.logs_dir,
        include_httpmail=False,
        max_files_per_source=args.max_files_per_source,
    )
    samples = build_window_samples(events=events, salt=args.salt, window_minutes=args.window_minutes)
    prepared = prepare_data(samples=samples, seq_len=args.seq_len)

    y_test = prepared.y[prepared.test_idx]

    deep_pred, deep_prob = _deep_predict(
        model_dir=args.model_dir,
        x_seq=prepared.x_seq[prepared.test_idx],
        x_static=prepared.x_static[prepared.test_idx],
        host_idx=prepared.host_idx[prepared.test_idx],
        batch_size=args.batch_size,
    )
    deep_metrics = _classification_metrics(y_test, deep_pred)
    deep_auc = _roc_auc_metrics(y_test, deep_prob)

    x_train = prepared.x_static[prepared.train_idx]
    y_train = prepared.y[prepared.train_idx]
    x_test = prepared.x_static[prepared.test_idx]

    x_train_ds, y_train_ds = _downsample_train(
        x_train=x_train,
        y_train=y_train,
        max_items=args.baseline_max_train,
        seed=args.seed,
    )

    rf_pred, rf_prob = _fit_random_forest(x_train_ds, y_train_ds, x_test, args.seed)
    rf_metrics = _classification_metrics(y_test, rf_pred)
    rf_auc = _roc_auc_metrics(y_test, rf_prob)

    secondary_name, sec_pred, sec_prob = _fit_xgboost_or_fallback(x_train_ds, y_train_ds, x_test, args.seed)
    sec_metrics = _classification_metrics(y_test, sec_pred)
    sec_auc = _roc_auc_metrics(y_test, sec_prob)

    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "window_minutes": args.window_minutes,
            "seq_len": args.seq_len,
            "baseline_max_train": args.baseline_max_train,
            "test_size": int(prepared.test_idx.size),
        },
        "class_distribution_train": {
            IDX_TO_LABEL[i]: int(np.sum(y_train == i)) for i in IDX_TO_LABEL
        },
        "deep_model": {
            "metrics": deep_metrics,
            "roc_auc": deep_auc,
        },
        "baselines": {
            "random_forest": {
                "metrics": rf_metrics,
                "roc_auc": rf_auc,
            },
            "secondary_name": secondary_name,
            "secondary": {
                "metrics": sec_metrics,
                "roc_auc": sec_auc,
            },
        },
    }

    with (args.output_dir / "evaluation_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=True, indent=2)

    _write_confusion_csv(args.output_dir / "confusion_matrix_deep.csv", y_test, deep_pred)
    _write_confusion_csv(args.output_dir / "confusion_matrix_random_forest.csv", y_test, rf_pred)
    _write_confusion_csv(args.output_dir / f"confusion_matrix_{secondary_name}.csv", y_test, sec_pred)

    with (args.output_dir / "roc_auc.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "deep_model": deep_auc,
                "random_forest": rf_auc,
                secondary_name: sec_auc,
            },
            handle,
            ensure_ascii=True,
            indent=2,
        )

    with (args.output_dir / "baseline_comparison.md").open("w", encoding="utf-8") as handle:
        handle.write(_render_markdown(summary))

    print("[info] evaluation_complete")
    print(json.dumps(summary["deep_model"]["metrics"], ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
