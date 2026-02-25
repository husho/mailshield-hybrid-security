from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from torch.utils.data import DataLoader, Subset

from .dataset import HybridDataset, class_weights, prepare_data
from .features import IDX_TO_LABEL, LABEL_TO_IDX, SEQ_FEATURES, STATIC_FEATURES, build_window_samples
from .model import HybridDeepMailModel
from .parsers import iter_events, list_discovered_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train deep hybrid spam/anomaly detector")
    parser.add_argument("--logs-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--salt", type=str, default="mailshield-default-salt")
    parser.add_argument("--window-minutes", type=int, default=15)
    parser.add_argument("--seq-len", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--max-files-per-source", type=int, default=0)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def evaluate(
    model: HybridDeepMailModel,
    loader: DataLoader,
    device: torch.device,
) -> Dict[str, float]:
    model.eval()
    y_true = []
    y_pred = []
    with torch.no_grad():
        for seq_x, static_x, host_idx, y, _weights in loader:
            seq_x = seq_x.to(device)
            static_x = static_x.to(device)
            host_idx = host_idx.to(device)
            logits = model(seq_x, static_x, host_idx)
            pred = torch.argmax(logits, dim=1).cpu().numpy()
            y_pred.append(pred)
            y_true.append(y.numpy())

    if not y_true:
        return {
            "accuracy": 0.0,
            "precision_macro": 0.0,
            "recall_macro": 0.0,
            "f1_macro": 0.0,
        }

    y_true_arr = np.concatenate(y_true)
    y_pred_arr = np.concatenate(y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true_arr,
        y_pred_arr,
        labels=list(IDX_TO_LABEL.keys()),
        average="macro",
        zero_division=0,
    )
    metrics = {
        "accuracy": float(accuracy_score(y_true_arr, y_pred_arr)),
        "precision_macro": float(precision),
        "recall_macro": float(recall),
        "f1_macro": float(f1),
    }

    per_class = precision_recall_fscore_support(
        y_true_arr,
        y_pred_arr,
        labels=list(IDX_TO_LABEL.keys()),
        average=None,
        zero_division=0,
    )
    for idx, label in IDX_TO_LABEL.items():
        metrics[f"precision_{label}"] = float(per_class[0][idx])
        metrics[f"recall_{label}"] = float(per_class[1][idx])
        metrics[f"f1_{label}"] = float(per_class[2][idx])

    return metrics


def train_model(
    prepared,
    output_dir: Path,
    epochs: int,
    batch_size: int,
    lr: float,
    num_workers: int,
    device: torch.device,
    window_minutes: int,
    seq_len: int,
) -> Dict[str, Dict[str, float]]:
    dataset = HybridDataset(prepared.x_seq, prepared.x_static, prepared.host_idx, prepared.y, prepared.weights)

    train_loader = DataLoader(
        Subset(dataset, prepared.train_idx.tolist()),
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
    )
    val_loader = DataLoader(
        Subset(dataset, prepared.val_idx.tolist()),
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
    )
    test_loader = DataLoader(
        Subset(dataset, prepared.test_idx.tolist()),
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
    )

    model = HybridDeepMailModel(
        seq_input_dim=len(SEQ_FEATURES),
        static_input_dim=len(STATIC_FEATURES),
        num_hosts=len(prepared.host_to_idx),
        num_classes=len(LABEL_TO_IDX),
    ).to(device)

    y_train = prepared.y[prepared.train_idx]
    ce_weights = class_weights(y_train).to(device)
    criterion = torch.nn.CrossEntropyLoss(weight=ce_weights, reduction="none")
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    best_val_f1 = -1.0
    best_state = None

    history = []
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        steps = 0

        for seq_x, static_x, host_idx, y, sample_weight in train_loader:
            seq_x = seq_x.to(device)
            static_x = static_x.to(device)
            host_idx = host_idx.to(device)
            y = y.to(device)
            sample_weight = sample_weight.to(device)

            optimizer.zero_grad(set_to_none=True)
            logits = model(seq_x, static_x, host_idx)
            per_sample_loss = criterion(logits, y)
            loss = (per_sample_loss * sample_weight).mean()
            loss.backward()
            optimizer.step()

            running_loss += float(loss.item())
            steps += 1

        val_metrics = evaluate(model, val_loader, device)
        epoch_info = {
            "epoch": epoch,
            "loss": float(running_loss / max(steps, 1)),
            "val_f1_macro": val_metrics["f1_macro"],
            "val_recall_macro": val_metrics["recall_macro"],
        }
        history.append(epoch_info)

        if val_metrics["f1_macro"] > best_val_f1:
            best_val_f1 = val_metrics["f1_macro"]
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    val_metrics = evaluate(model, val_loader, device)
    test_metrics = evaluate(model, test_loader, device)

    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_dir / "model.pt")

    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "window_minutes": window_minutes,
        "seq_len": seq_len,
        "seq_features": SEQ_FEATURES,
        "static_features": STATIC_FEATURES,
        "host_to_idx": prepared.host_to_idx,
        "label_to_idx": LABEL_TO_IDX,
        "idx_to_label": IDX_TO_LABEL,
        "seq_mean": prepared.seq_mean.tolist(),
        "seq_std": prepared.seq_std.tolist(),
        "static_mean": prepared.static_mean.tolist(),
        "static_std": prepared.static_std.tolist(),
        "reason_thresholds": prepared.reason_thresholds,
        "model_config": {
            "seq_input_dim": len(SEQ_FEATURES),
            "static_input_dim": len(STATIC_FEATURES),
            "num_hosts": len(prepared.host_to_idx),
            "num_classes": len(LABEL_TO_IDX),
            "gru_hidden": 64,
            "host_emb_dim": 8,
            "dropout": 0.2,
        },
    }
    with (output_dir / "metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=True, indent=2)

    summary = {
        "history": history,
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
        "class_distribution_train": {
            IDX_TO_LABEL[i]: int(np.sum(y_train == i)) for i in IDX_TO_LABEL
        },
        "num_samples": int(prepared.y.shape[0]),
        "num_train": int(prepared.train_idx.size),
        "num_val": int(prepared.val_idx.size),
        "num_test": int(prepared.test_idx.size),
    }
    with (output_dir / "training_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=True, indent=2)

    return {"val": val_metrics, "test": test_metrics}


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    logs_dir = args.logs_dir
    output_dir = args.output_dir
    device = torch.device(args.device)

    discovered = list_discovered_files(logs_dir)
    print(f"[info] discovered_files={discovered}")

    events = iter_events(
        logs_dir,
        include_httpmail=False,
        max_files_per_source=args.max_files_per_source,
    )
    samples = build_window_samples(
        events=events,
        salt=args.salt,
        window_minutes=args.window_minutes,
    )
    print(f"[info] window_samples={len(samples)}")

    prepared = prepare_data(samples=samples, seq_len=args.seq_len)
    metrics = train_model(
        prepared=prepared,
        output_dir=output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        num_workers=args.num_workers,
        device=device,
        window_minutes=args.window_minutes,
        seq_len=args.seq_len,
    )

    print("[info] training_complete")
    print(json.dumps(metrics, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
