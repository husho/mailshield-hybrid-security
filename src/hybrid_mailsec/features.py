from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

import numpy as np

from .parsers import ParsedEvent
from .privacy import hmac_hash

SEQ_FEATURES = [
    "smtp_events",
    "smtp_auth_attempts",
    "smtp_auth_failures",
    "smtp_auth_failure_rate",
    "smtp_data_events",
    "smtp_unique_src_ip",
    "mta_routes_total",
    "mta_routes_smtp",
    "mtafilter_exec_count",
]

STATIC_FEATURES = [
    "smtp_events",
    "smtp_auth_attempts",
    "smtp_auth_failures",
    "smtp_auth_failure_rate",
    "smtp_data_events",
    "smtp_unique_src_ip",
    "smtp_bytes_in",
    "smtp_bytes_out",
    "mta_routes_total",
    "mta_routes_smtp",
    "mta_routes_sf",
    "mta_unique_senders",
    "mtafilter_exec_count",
    "mtafilter_spam_delete",
    "mtafilter_spam_high",
    "mtafilter_spam_low",
]

LABEL_TO_IDX = {"normal": 0, "anomaly": 1, "spam": 2}
IDX_TO_LABEL = {idx: label for label, idx in LABEL_TO_IDX.items()}


@dataclass(frozen=True)
class WindowKey:
    host_id: str
    account_hash: str
    window_start: dt.datetime


@dataclass
class WindowAccumulator:
    smtp_events: int = 0
    smtp_auth_attempts: int = 0
    smtp_auth_failures: int = 0
    smtp_data_events: int = 0
    smtp_bytes_in: int = 0
    smtp_bytes_out: int = 0

    mta_routes_total: int = 0
    mta_routes_smtp: int = 0
    mta_routes_sf: int = 0
    mta_unique_senders_set: set[str] = field(default_factory=set)

    mtafilter_exec_count: int = 0
    mtafilter_spam_delete: int = 0
    mtafilter_spam_high: int = 0
    mtafilter_spam_low: int = 0

    smtp_unique_src_ip_set: set[str] = field(default_factory=set)


@dataclass
class WindowSample:
    host_id: str
    account_hash: str
    window_start: dt.datetime
    features: Dict[str, float]
    label: str
    label_weight: float


def floor_to_window(ts: dt.datetime, window_minutes: int) -> dt.datetime:
    minute = (ts.minute // window_minutes) * window_minutes
    return ts.replace(minute=minute, second=0, microsecond=0)


def build_window_samples(
    events: Iterable[ParsedEvent],
    salt: str,
    window_minutes: int = 15,
) -> List[WindowSample]:
    buckets: Dict[WindowKey, WindowAccumulator] = {}

    for event in events:
        entity_value = event.account or event.sender or (f"ip:{event.src_ip}" if event.src_ip else "unknown")
        account_hash = hmac_hash(entity_value, salt)
        if not account_hash:
            continue

        key = WindowKey(
            host_id=event.host_id,
            account_hash=account_hash,
            window_start=floor_to_window(event.timestamp, window_minutes),
        )
        acc = buckets.setdefault(key, WindowAccumulator())

        if event.service == "smtp":
            acc.smtp_events += 1
            if ":AUTH:" in event.event_type:
                acc.smtp_auth_attempts += 1
                if event.success is False:
                    acc.smtp_auth_failures += 1
            if ":DATA:" in event.event_type:
                acc.smtp_data_events += 1
            acc.smtp_bytes_in += max(event.bytes_in, 0)
            acc.smtp_bytes_out += max(event.bytes_out, 0)
            if event.src_ip:
                acc.smtp_unique_src_ip_set.add(hmac_hash(event.src_ip, salt))

        elif event.service == "mta":
            acc.mta_routes_total += 1
            if "ROUTE:SMTP" in event.event_type:
                acc.mta_routes_smtp += 1
            if "ROUTE:SF" in event.event_type:
                acc.mta_routes_sf += 1
            if event.sender:
                acc.mta_unique_senders_set.add(hmac_hash(event.sender, salt))

        elif event.service == "mtafilter":
            acc.mtafilter_exec_count += 1
            if event.spam_hint == "spam_delete":
                acc.mtafilter_spam_delete += 1
            elif event.spam_hint == "spam_high":
                acc.mtafilter_spam_high += 1
            elif event.spam_hint == "spam_low":
                acc.mtafilter_spam_low += 1

    raw_samples: List[WindowSample] = []
    for key, acc in buckets.items():
        auth_rate = (acc.smtp_auth_failures / acc.smtp_auth_attempts) if acc.smtp_auth_attempts else 0.0
        features = {
            "smtp_events": float(acc.smtp_events),
            "smtp_auth_attempts": float(acc.smtp_auth_attempts),
            "smtp_auth_failures": float(acc.smtp_auth_failures),
            "smtp_auth_failure_rate": float(auth_rate),
            "smtp_data_events": float(acc.smtp_data_events),
            "smtp_unique_src_ip": float(len(acc.smtp_unique_src_ip_set)),
            "smtp_bytes_in": float(acc.smtp_bytes_in),
            "smtp_bytes_out": float(acc.smtp_bytes_out),
            "mta_routes_total": float(acc.mta_routes_total),
            "mta_routes_smtp": float(acc.mta_routes_smtp),
            "mta_routes_sf": float(acc.mta_routes_sf),
            "mta_unique_senders": float(len(acc.mta_unique_senders_set)),
            "mtafilter_exec_count": float(acc.mtafilter_exec_count),
            "mtafilter_spam_delete": float(acc.mtafilter_spam_delete),
            "mtafilter_spam_high": float(acc.mtafilter_spam_high),
            "mtafilter_spam_low": float(acc.mtafilter_spam_low),
        }

        label = "normal"
        label_weight = 1.0
        if acc.mtafilter_spam_delete > 0 or acc.mtafilter_spam_high > 0:
            label = "spam"
            label_weight = 1.0
        elif acc.mtafilter_spam_low > 0:
            label = "anomaly"
            label_weight = 0.5

        raw_samples.append(
            WindowSample(
                host_id=key.host_id,
                account_hash=key.account_hash,
                window_start=key.window_start,
                features=features,
                label=label,
                label_weight=label_weight,
            )
        )

    _apply_behavioral_anomaly_labels(raw_samples)
    raw_samples.sort(key=lambda s: (s.window_start, s.host_id, s.account_hash))
    return raw_samples


def _apply_behavioral_anomaly_labels(samples: List[WindowSample]) -> None:
    grouped: Dict[Tuple[str, str], List[WindowSample]] = {}
    for sample in samples:
        grouped.setdefault((sample.host_id, sample.account_hash), []).append(sample)

    for _, account_samples in grouped.items():
        smtp_events = np.array([s.features["smtp_events"] for s in account_samples], dtype=np.float32)
        auth_fails = np.array([s.features["smtp_auth_failures"] for s in account_samples], dtype=np.float32)
        unique_ips = np.array([s.features["smtp_unique_src_ip"] for s in account_samples], dtype=np.float32)

        ev_med, ev_mad = _median_and_mad(smtp_events)
        af_med, af_mad = _median_and_mad(auth_fails)
        ip_med, ip_mad = _median_and_mad(unique_ips)

        for sample in account_samples:
            if sample.label == "spam":
                continue
            ev = sample.features["smtp_events"]
            af = sample.features["smtp_auth_failures"]
            ipn = sample.features["smtp_unique_src_ip"]
            auth_rate = sample.features["smtp_auth_failure_rate"]

            burst_events = ev > max(40.0, ev_med + 8.0 * ev_mad)
            burst_auth = af > max(12.0, af_med + 6.0 * af_mad)
            burst_ip = ipn > max(4.0, ip_med + 5.0 * ip_mad)
            hostile_auth_pattern = sample.features["smtp_auth_attempts"] >= 10 and auth_rate >= 0.85

            if burst_events or burst_auth or burst_ip or hostile_auth_pattern:
                if sample.label == "normal":
                    sample.label = "anomaly"
                    sample.label_weight = 1.0


def _median_and_mad(values: np.ndarray) -> Tuple[float, float]:
    if values.size == 0:
        return 0.0, 1.0
    med = float(np.median(values))
    mad = float(np.median(np.abs(values - med)))
    return med, max(mad, 1.0)
