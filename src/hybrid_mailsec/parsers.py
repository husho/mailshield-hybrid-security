from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional

HOST_RE = re.compile(r"(host\d+)-Logging", re.IGNORECASE)
IP_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
HOSTNAME_RE = re.compile(r"^HOST\d+$", re.IGNORECASE)
MTA_MSG_ID_RE = re.compile(r"\[([A-F0-9]{8,}\.MAI)\]", re.IGNORECASE)
MTA_SENDER_RE = re.compile(r"\[SMTP:([^\]]+)\]", re.IGNORECASE)
MTA_CONNECTOR_RE = re.compile(r"from \(([^\)]+)\)", re.IGNORECASE)
EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)")


@dataclass
class ParsedEvent:
    timestamp: dt.datetime
    host_id: str
    service: str
    account: str
    sender: str
    src_ip: str
    event_type: str
    success: Optional[bool]
    bytes_in: int
    bytes_out: int
    latency_ms: int
    message_id: str
    spam_hint: str


def infer_host_id(path: Path) -> str:
    match = HOST_RE.search(str(path))
    return match.group(1).lower() if match else "unknown"


def _parse_dt(value: str, fmt: str) -> Optional[dt.datetime]:
    try:
        return dt.datetime.strptime(value, fmt)
    except ValueError:
        return None


def iter_smtp_events(path: Path) -> Iterator[ParsedEvent]:
    host_id = infer_host_id(path)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            tokens = line.split()
            if len(tokens) < 10:
                continue

            ts = _parse_dt(f"{tokens[0]} {tokens[1]}", "%Y-%m-%d %H:%M:%S")
            if ts is None:
                continue

            c_ip = tokens[2]
            agent = tokens[3]

            # SMTP lines may contain empty account/cs-username fields, so parse around s-ip marker.
            ip_index = None
            for i in range(4, len(tokens)):
                if IP_RE.match(tokens[i]):
                    ip_index = i
                    break
            if ip_index is None or ip_index + 2 >= len(tokens):
                continue

            account = " ".join(tokens[4:ip_index]).strip()
            s_ip = tokens[ip_index]

            # s-port exists at ip_index + 1, we keep it out of canonical event.
            host_token_idx = None
            for i in range(len(tokens) - 1, ip_index, -1):
                if HOSTNAME_RE.match(tokens[i]):
                    host_token_idx = i
                    break
            if host_token_idx is None:
                continue

            mid = tokens[ip_index + 2 : host_token_idx]
            method = mid[0] if len(mid) >= 1 else ""
            uri_stem = mid[1] if len(mid) >= 2 else ""
            uri_query = mid[2] if len(mid) >= 3 else ""

            sc_bytes = 0
            cs_bytes = 0
            cs_username = ""
            try:
                if host_token_idx + 1 < len(tokens):
                    sc_bytes = int(tokens[host_token_idx + 1])
                if host_token_idx + 2 < len(tokens):
                    cs_bytes = int(tokens[host_token_idx + 2])
            except ValueError:
                pass
            if host_token_idx + 3 < len(tokens):
                cs_username = tokens[host_token_idx + 3] if tokens[host_token_idx + 3] != "-" else ""

            auth_failed = "Invalid+Username+or+Password" in uri_query
            success = None
            if method == "AUTH":
                success = not auth_failed

            account_value = account or cs_username
            yield ParsedEvent(
                timestamp=ts,
                host_id=host_id,
                service="smtp",
                account=account_value,
                sender=cs_username,
                src_ip=c_ip or s_ip,
                event_type=f"{agent}:{method}:{uri_stem}",
                success=success,
                bytes_in=cs_bytes,
                bytes_out=sc_bytes,
                latency_ms=0,
                message_id="",
                spam_hint="",
            )


def iter_mta_activity_events(path: Path) -> Iterator[ParsedEvent]:
    host_id = infer_host_id(path)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if "LOG FILE STARTED" in line:
                continue
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue

            ts = _parse_dt(parts[0], "%m/%d/%y %H:%M:%S")
            if ts is None:
                continue

            msg = parts[1]
            sender_match = MTA_SENDER_RE.search(msg)
            sender = sender_match.group(1) if sender_match else ""
            connector_match = MTA_CONNECTOR_RE.search(msg)
            connector = connector_match.group(1).upper() if connector_match else ""
            msg_id_match = MTA_MSG_ID_RE.search(msg)
            msg_id = msg_id_match.group(1) if msg_id_match else ""

            yield ParsedEvent(
                timestamp=ts,
                host_id=host_id,
                service="mta",
                account=_account_from_sender(sender),
                sender=sender,
                src_ip="",
                event_type=f"ROUTE:{connector or 'UNK'}",
                success=None,
                bytes_in=0,
                bytes_out=0,
                latency_ms=0,
                message_id=msg_id,
                spam_hint="",
            )


def iter_mtafilter_events(path: Path) -> Iterator[ParsedEvent]:
    host_id = infer_host_id(path)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.rstrip("\n")
            if not line or line.startswith("Time\tAction"):
                continue

            cols = line.split("\t")
            if len(cols) < 2:
                continue

            ts = _parse_dt(cols[0], "%m/%d/%y %H:%M:%S")
            if ts is None:
                continue

            action = cols[1].strip()
            if action != "Executed":
                continue

            cols = cols + [""] * (11 - len(cols))
            message_id = cols[2].strip()
            filter_name = cols[4].strip()
            result = cols[5].strip()
            account = cols[6].strip()
            sender = cols[7].strip()
            src_ip = cols[8].strip()
            data = cols[9].strip()

            hint = ""
            if result.upper() == "DELETE":
                hint = "spam_delete"
            elif filter_name == "[System Spam Filter]" and "High" in data:
                hint = "spam_high"
            elif filter_name == "[System Spam Filter]" and "Low" in data:
                hint = "spam_low"

            account_value = account or _account_from_sender(sender)
            sender_email = _extract_email(sender)
            yield ParsedEvent(
                timestamp=ts,
                host_id=host_id,
                service="mtafilter",
                account=account_value,
                sender=sender_email,
                src_ip=src_ip,
                event_type=f"FILTER:{filter_name}:{result}",
                success=(result.upper() != "DELETE"),
                bytes_in=0,
                bytes_out=0,
                latency_ms=0,
                message_id=message_id,
                spam_hint=hint,
            )


def _extract_email(value: str) -> str:
    if not value:
        return ""
    found = EMAIL_RE.search(value)
    return found.group(1).lower() if found else value.lower().strip("[]")


def _account_from_sender(sender: str) -> str:
    sender_email = _extract_email(sender)
    if "@" not in sender_email:
        return ""
    return sender_email.split("@", 1)[1]


def iter_events(
    logs_dir: Path,
    include_httpmail: bool = False,
    max_files_per_source: int = 0,
) -> Iterator[ParsedEvent]:
    patterns: Dict[str, str] = {
        "smtp": "*/SMTP/ex*.log",
        "mta": "*/MTA/MTA-Activity-*.log",
        "mtafilter": "*/MTA/MTAFILTER-Report-*.log",
    }
    if include_httpmail:
        # Kept for phase-2 extensibility; parsing is not enabled in MVP.
        patterns["httpmail"] = "*/HTTPMAIL/ex*.log"

    for service, pattern in patterns.items():
        files = sorted(logs_dir.glob(pattern))
        if max_files_per_source > 0:
            files = files[:max_files_per_source]
        for file_path in files:
            if service == "smtp":
                yield from iter_smtp_events(file_path)
            elif service == "mta":
                yield from iter_mta_activity_events(file_path)
            elif service == "mtafilter":
                yield from iter_mtafilter_events(file_path)


def list_discovered_files(logs_dir: Path) -> Dict[str, int]:
    return {
        "smtp": len(list(logs_dir.glob("*/SMTP/ex*.log"))),
        "mta": len(list(logs_dir.glob("*/MTA/MTA-Activity-*.log"))),
        "mtafilter": len(list(logs_dir.glob("*/MTA/MTAFILTER-Report-*.log"))),
    }
