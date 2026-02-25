from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset

from .features import IDX_TO_LABEL, LABEL_TO_IDX, SEQ_FEATURES, STATIC_FEATURES, WindowSample


@dataclass
class PreparedData:
    x_seq: np.ndarray
    x_static: np.ndarray
    host_idx: np.ndarray
    y: np.ndarray
    weights: np.ndarray
    timestamps: np.ndarray
    host_to_idx: Dict[str, int]
    seq_mean: np.ndarray
    seq_std: np.ndarray
    static_mean: np.ndarray
    static_std: np.ndarray
    train_idx: np.ndarray
    val_idx: np.ndarray
    test_idx: np.ndarray
    reason_thresholds: Dict[str, float]


class HybridDataset(Dataset):
    def __init__(
        self,
        x_seq: np.ndarray,
        x_static: np.ndarray,
        host_idx: np.ndarray,
        y: np.ndarray,
        weights: np.ndarray,
    ) -> None:
        self.x_seq = torch.tensor(x_seq, dtype=torch.float32)
        self.x_static = torch.tensor(x_static, dtype=torch.float32)
        self.host_idx = torch.tensor(host_idx, dtype=torch.int64)
        self.y = torch.tensor(y, dtype=torch.int64)
        self.weights = torch.tensor(weights, dtype=torch.float32)

    def __len__(self) -> int:
        return int(self.y.shape[0])

    def __getitem__(self, idx: int):
        return (
            self.x_seq[idx],
            self.x_static[idx],
            self.host_idx[idx],
            self.y[idx],
            self.weights[idx],
        )


def prepare_data(samples: Sequence[WindowSample], seq_len: int = 8) -> PreparedData:
    if not samples:
        raise ValueError("No samples available for training.")

    host_values = sorted({sample.host_id for sample in samples})
    host_to_idx = {host: idx for idx, host in enumerate(host_values)}

    grouped: Dict[Tuple[str, str], List[WindowSample]] = {}
    for sample in samples:
        grouped.setdefault((sample.host_id, sample.account_hash), []).append(sample)

    seq_rows: List[np.ndarray] = []
    static_rows: List[np.ndarray] = []
    host_rows: List[int] = []
    y_rows: List[int] = []
    weight_rows: List[float] = []
    time_rows: List[np.datetime64] = []

    for (host_id, _), account_samples in grouped.items():
        account_samples.sort(key=lambda s: s.window_start)
        seq_buffer = np.zeros((seq_len, len(SEQ_FEATURES)), dtype=np.float32)

        for sample in account_samples:
            seq_buffer = np.roll(seq_buffer, shift=-1, axis=0)
            seq_buffer[-1] = np.array([sample.features[name] for name in SEQ_FEATURES], dtype=np.float32)

            seq_rows.append(seq_buffer.copy())
            static_rows.append(np.array([sample.features[name] for name in STATIC_FEATURES], dtype=np.float32))
            host_rows.append(host_to_idx[host_id])
            y_rows.append(LABEL_TO_IDX[sample.label])
            weight_rows.append(sample.label_weight)
            time_rows.append(np.datetime64(sample.window_start))

    x_seq = np.stack(seq_rows)
    x_static = np.stack(static_rows)
    raw_static = x_static.copy()
    host_idx = np.array(host_rows, dtype=np.int64)
    y = np.array(y_rows, dtype=np.int64)
    weights = np.array(weight_rows, dtype=np.float32)
    timestamps = np.array(time_rows)

    train_idx, val_idx, test_idx = _time_split_indices(timestamps)

    seq_mean = x_seq[train_idx].mean(axis=(0, 1))
    seq_std = x_seq[train_idx].std(axis=(0, 1))
    seq_std = np.where(seq_std < 1e-6, 1.0, seq_std)

    static_mean = x_static[train_idx].mean(axis=0)
    static_std = x_static[train_idx].std(axis=0)
    static_std = np.where(static_std < 1e-6, 1.0, static_std)

    x_seq = (x_seq - seq_mean.reshape(1, 1, -1)) / seq_std.reshape(1, 1, -1)
    x_static = (x_static - static_mean.reshape(1, -1)) / static_std.reshape(1, -1)

    reason_thresholds = {
        "smtp_auth_failures_p95": float(
            np.percentile(_safe_slice(raw_static, train_idx, STATIC_FEATURES, "smtp_auth_failures"), 95)
        ),
        "smtp_events_p95": float(
            np.percentile(_safe_slice(raw_static, train_idx, STATIC_FEATURES, "smtp_events"), 95)
        ),
        "smtp_unique_src_ip_p95": float(
            np.percentile(_safe_slice(raw_static, train_idx, STATIC_FEATURES, "smtp_unique_src_ip"), 95)
        ),
        "mtafilter_spam_delete_p90": float(
            np.percentile(_safe_slice(raw_static, train_idx, STATIC_FEATURES, "mtafilter_spam_delete"), 90)
        ),
    }

    return PreparedData(
        x_seq=x_seq,
        x_static=x_static,
        host_idx=host_idx,
        y=y,
        weights=weights,
        timestamps=timestamps,
        host_to_idx=host_to_idx,
        seq_mean=seq_mean,
        seq_std=seq_std,
        static_mean=static_mean,
        static_std=static_std,
        train_idx=train_idx,
        val_idx=val_idx,
        test_idx=test_idx,
        reason_thresholds=reason_thresholds,
    )


def _safe_slice(matrix: np.ndarray, idx: np.ndarray, columns: Sequence[str], column_name: str) -> np.ndarray:
    col_idx = columns.index(column_name)
    values = matrix[idx, col_idx]
    return values if values.size else np.array([0.0], dtype=np.float32)


def _time_split_indices(timestamps: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    unique_times = np.unique(timestamps)
    unique_times.sort()

    if unique_times.size < 10:
        n = timestamps.shape[0]
        all_idx = np.arange(n)
        split1 = int(n * 0.7)
        split2 = int(n * 0.85)
        return all_idx[:split1], all_idx[split1:split2], all_idx[split2:]

    t70 = unique_times[int(unique_times.size * 0.70)]
    t85 = unique_times[int(unique_times.size * 0.85)]

    train_idx = np.where(timestamps <= t70)[0]
    val_idx = np.where((timestamps > t70) & (timestamps <= t85))[0]
    test_idx = np.where(timestamps > t85)[0]

    if val_idx.size == 0 or test_idx.size == 0:
        n = timestamps.shape[0]
        all_idx = np.argsort(timestamps)
        split1 = int(n * 0.7)
        split2 = int(n * 0.85)
        train_idx = all_idx[:split1]
        val_idx = all_idx[split1:split2]
        test_idx = all_idx[split2:]

    return train_idx, val_idx, test_idx


def class_weights(y_train: np.ndarray) -> torch.Tensor:
    counts = np.bincount(y_train, minlength=len(IDX_TO_LABEL)).astype(np.float32)
    counts = np.where(counts <= 0, 1.0, counts)
    inv = 1.0 / counts
    weights = inv / inv.sum() * len(IDX_TO_LABEL)
    return torch.tensor(weights, dtype=torch.float32)
