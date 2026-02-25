from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np
import torch

from .model import HybridDeepMailModel


@dataclass
class ModelArtifacts:
    model: HybridDeepMailModel
    metadata: Dict
    device: torch.device


def load_artifacts(model_dir: Path, device: str = "cpu") -> ModelArtifacts:
    metadata_path = model_dir / "metadata.json"
    weights_path = model_dir / "model.pt"

    with metadata_path.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)

    cfg = metadata["model_config"]
    model = HybridDeepMailModel(
        seq_input_dim=cfg["seq_input_dim"],
        static_input_dim=cfg["static_input_dim"],
        num_hosts=cfg["num_hosts"],
        num_classes=cfg["num_classes"],
        gru_hidden=cfg.get("gru_hidden", 64),
        host_emb_dim=cfg.get("host_emb_dim", 8),
        dropout=cfg.get("dropout", 0.2),
    )

    torch_device = torch.device(device)
    state = torch.load(weights_path, map_location=torch_device)
    model.load_state_dict(state)
    model.to(torch_device)
    model.eval()

    return ModelArtifacts(model=model, metadata=metadata, device=torch_device)


def score_window(
    artifacts: ModelArtifacts,
    host_id: str,
    static_features: Dict[str, float],
    history_features: Sequence[Dict[str, float]],
) -> Dict:
    metadata = artifacts.metadata

    seq_names = metadata["seq_features"]
    static_names = metadata["static_features"]
    seq_len = int(metadata["seq_len"])

    seq_values = np.zeros((seq_len, len(seq_names)), dtype=np.float32)
    rows = list(history_features)[-seq_len:]
    start = max(0, seq_len - len(rows))

    for i, row in enumerate(rows):
        seq_values[start + i] = np.array([float(row.get(name, 0.0)) for name in seq_names], dtype=np.float32)

    current_seq = np.array([float(static_features.get(name, 0.0)) for name in seq_names], dtype=np.float32)
    seq_values = np.roll(seq_values, shift=-1, axis=0)
    seq_values[-1] = current_seq

    static_values = np.array([float(static_features.get(name, 0.0)) for name in static_names], dtype=np.float32)

    seq_mean = np.array(metadata["seq_mean"], dtype=np.float32)
    seq_std = np.array(metadata["seq_std"], dtype=np.float32)
    static_mean = np.array(metadata["static_mean"], dtype=np.float32)
    static_std = np.array(metadata["static_std"], dtype=np.float32)

    seq_values = (seq_values - seq_mean.reshape(1, -1)) / seq_std.reshape(1, -1)
    static_values = (static_values - static_mean) / static_std

    host_to_idx = metadata["host_to_idx"]
    host_idx = int(host_to_idx.get(host_id, 0))

    seq_tensor = torch.tensor(seq_values, dtype=torch.float32, device=artifacts.device).unsqueeze(0)
    static_tensor = torch.tensor(static_values, dtype=torch.float32, device=artifacts.device).unsqueeze(0)
    host_tensor = torch.tensor([host_idx], dtype=torch.int64, device=artifacts.device)

    with torch.no_grad():
        logits = artifacts.model(seq_tensor, static_tensor, host_tensor)
        probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

    idx_to_label = {int(k): v for k, v in metadata["idx_to_label"].items()}
    pred_idx = int(np.argmax(probs))
    pred_label = idx_to_label[pred_idx]

    spam_prob = float(probs[2]) if probs.shape[0] > 2 else 0.0
    anomaly_prob = float(probs[1]) if probs.shape[0] > 1 else 0.0
    risk_score = float(np.clip((0.6 * spam_prob + 0.4 * anomaly_prob) * 100.0, 0.0, 100.0))

    reasons = explain_reasons(static_features, metadata.get("reason_thresholds", {}), pred_label, probs)
    recommendation = recommend_action(pred_label, risk_score)

    return {
        "class_label": pred_label,
        "risk_score": risk_score,
        "class_probabilities": {
            "normal": float(probs[0]),
            "anomaly": float(probs[1]),
            "spam": float(probs[2]),
        },
        "reasons": reasons,
        "recommendation": recommendation,
        "model_version": metadata.get("created_at", "unknown"),
    }


def explain_reasons(
    static_features: Dict[str, float],
    thresholds: Dict[str, float],
    pred_label: str,
    probs: np.ndarray,
) -> List[str]:
    reasons: List[str] = []

    if static_features.get("smtp_auth_failures", 0.0) >= thresholds.get("smtp_auth_failures_p95", 15.0):
        reasons.append("high_auth_failure_burst")

    if static_features.get("smtp_events", 0.0) >= thresholds.get("smtp_events_p95", 50.0):
        reasons.append("sudden_smtp_volume_spike")

    if static_features.get("smtp_unique_src_ip", 0.0) >= thresholds.get("smtp_unique_src_ip_p95", 4.0):
        reasons.append("source_ip_diversity_anomaly")

    if static_features.get("mtafilter_spam_delete", 0.0) > 0.0:
        reasons.append("mtafilter_delete_detected")

    if static_features.get("mtafilter_spam_high", 0.0) > 0.0:
        reasons.append("mtafilter_high_spam_score")

    if pred_label == "spam" and float(probs[2]) > 0.8:
        reasons.append("high_spam_confidence")

    if pred_label == "anomaly" and float(probs[1]) > 0.7:
        reasons.append("behavioral_sequence_shift")

    return reasons or ["baseline_deviation_detected"]


def recommend_action(label: str, risk_score: float) -> str:
    if label == "spam":
        return "Review outbound sender account and queue immediately; keep auto-block disabled in pilot mode."
    if label == "anomaly":
        if risk_score >= 60:
            return "Escalate to security analyst and verify authentication pattern for the account."
        return "Monitor account behavior in next windows and keep under watch list."
    return "No immediate action; continue monitoring."
