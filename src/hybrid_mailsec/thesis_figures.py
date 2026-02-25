from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

LABELS = ["normal", "anomaly", "spam"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate thesis-ready figures from evaluation outputs")
    parser.add_argument("--eval-dir", type=Path, required=True)
    parser.add_argument("--train-summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_confusion_csv(path: Path) -> Tuple[List[str], np.ndarray]:
    rows: List[List[str]] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            rows.append(row)

    labels = rows[0][1:]
    matrix = np.array([[int(v) for v in row[1:]] for row in rows[1:]], dtype=np.int64)
    return labels, matrix


def _plot_macro_metrics(eval_summary: Dict, output_path: Path) -> None:
    model_names = ["Deep Hybrid", "RandomForest", eval_summary["baselines"]["secondary_name"]]
    deep = eval_summary["deep_model"]["metrics"]
    rf = eval_summary["baselines"]["random_forest"]["metrics"]
    sec = eval_summary["baselines"]["secondary"]["metrics"]

    precision = [deep["precision_macro"], rf["precision_macro"], sec["precision_macro"]]
    recall = [deep["recall_macro"], rf["recall_macro"], sec["recall_macro"]]
    f1 = [deep["f1_macro"], rf["f1_macro"], sec["f1_macro"]]

    x = np.arange(len(model_names))
    width = 0.24

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width, precision, width, label="Precision (macro)")
    ax.bar(x, recall, width, label="Recall (macro)")
    ax.bar(x + width, f1, width, label="F1 (macro)")

    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Model Comparison on Test Set (Macro Metrics)")
    ax.set_xticks(x)
    ax.set_xticklabels(model_names)
    ax.legend()
    ax.grid(axis="y", alpha=0.2)

    for container in ax.containers:
        ax.bar_label(container, fmt="%.3f", padding=2, fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def _plot_class_recall(eval_summary: Dict, output_path: Path) -> None:
    model_names = ["Deep Hybrid", "RandomForest", eval_summary["baselines"]["secondary_name"]]
    deep = eval_summary["deep_model"]["metrics"]
    rf = eval_summary["baselines"]["random_forest"]["metrics"]
    sec = eval_summary["baselines"]["secondary"]["metrics"]

    recalls = {
        "normal": [deep["recall_normal"], rf["recall_normal"], sec["recall_normal"]],
        "anomaly": [deep["recall_anomaly"], rf["recall_anomaly"], sec["recall_anomaly"]],
        "spam": [deep["recall_spam"], rf["recall_spam"], sec["recall_spam"]],
    }

    x = np.arange(len(model_names))
    width = 0.24

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width, recalls["normal"], width, label="Recall normal")
    ax.bar(x, recalls["anomaly"], width, label="Recall anomaly")
    ax.bar(x + width, recalls["spam"], width, label="Recall spam")

    ax.set_ylim(0.0, 1.05)
    ax.set_ylabel("Recall")
    ax.set_title("Per-Class Recall Comparison")
    ax.set_xticks(x)
    ax.set_xticklabels(model_names)
    ax.legend()
    ax.grid(axis="y", alpha=0.2)

    for container in ax.containers:
        ax.bar_label(container, fmt="%.3f", padding=2, fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def _plot_roc_auc(eval_summary: Dict, output_path: Path) -> None:
    secondary_name = eval_summary["baselines"]["secondary_name"]
    model_names = ["Deep Hybrid", "RandomForest", secondary_name]
    values = [
        eval_summary["deep_model"]["roc_auc"]["macro_ovr"],
        eval_summary["baselines"]["random_forest"]["roc_auc"]["macro_ovr"],
        eval_summary["baselines"]["secondary"]["roc_auc"]["macro_ovr"],
    ]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(model_names, values)
    ax.set_ylim(0.95, 1.01)
    ax.set_ylabel("ROC-AUC (macro OVR)")
    ax.set_title("Macro ROC-AUC Comparison")
    ax.grid(axis="y", alpha=0.2)
    ax.bar_label(bars, fmt="%.4f", padding=3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def _plot_class_distribution(train_summary: Dict, output_path: Path) -> None:
    dist = train_summary["class_distribution_train"]
    labels = list(dist.keys())
    values = [dist[k] for k in labels]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(labels, values)
    ax.set_title("Training Class Distribution")
    ax.set_ylabel("Count")
    ax.grid(axis="y", alpha=0.2)

    for bar in bars:
        h = int(bar.get_height())
        ax.annotate(f"{h:,}", (bar.get_x() + bar.get_width() / 2, h), ha="center", va="bottom", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def _plot_confusion_heatmap(csv_path: Path, title: str, output_path: Path) -> None:
    labels, matrix = _load_confusion_csv(csv_path)

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(matrix, cmap="Blues")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix[i, j]}", ha="center", va="center", color="black", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def _write_figure_index(output_dir: Path, secondary_name: str) -> None:
    lines = [
        "# Thesis Figure Index",
        "",
        "Generated figures:",
        "- fig_macro_metrics.png",
        "- fig_per_class_recall.png",
        "- fig_roc_auc_macro.png",
        "- fig_train_class_distribution.png",
        "- fig_confusion_deep.png",
        "- fig_confusion_random_forest.png",
        f"- fig_confusion_{secondary_name}.png",
    ]
    (output_dir / "FIGURE_INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()

    eval_summary = _load_json(args.eval_dir / "evaluation_summary.json")
    train_summary = _load_json(args.train_summary)
    secondary_name = eval_summary["baselines"]["secondary_name"]

    args.output_dir.mkdir(parents=True, exist_ok=True)

    _plot_macro_metrics(eval_summary, args.output_dir / "fig_macro_metrics.png")
    _plot_class_recall(eval_summary, args.output_dir / "fig_per_class_recall.png")
    _plot_roc_auc(eval_summary, args.output_dir / "fig_roc_auc_macro.png")
    _plot_class_distribution(train_summary, args.output_dir / "fig_train_class_distribution.png")

    _plot_confusion_heatmap(
        args.eval_dir / "confusion_matrix_deep.csv",
        "Confusion Matrix - Deep Hybrid",
        args.output_dir / "fig_confusion_deep.png",
    )
    _plot_confusion_heatmap(
        args.eval_dir / "confusion_matrix_random_forest.csv",
        "Confusion Matrix - RandomForest",
        args.output_dir / "fig_confusion_random_forest.png",
    )
    _plot_confusion_heatmap(
        args.eval_dir / f"confusion_matrix_{secondary_name}.csv",
        f"Confusion Matrix - {secondary_name}",
        args.output_dir / f"fig_confusion_{secondary_name}.png",
    )

    _write_figure_index(args.output_dir, secondary_name)
    print(f"[info] figures_generated={args.output_dir}")


if __name__ == "__main__":
    main()
