from __future__ import annotations

import hashlib
import hmac
from typing import Optional


def hmac_hash(value: Optional[str], salt: str) -> str:
    """Return a deterministic hash for PII-like fields."""
    if not value:
        return ""
    digest = hmac.new(salt.encode("utf-8"), value.strip().lower().encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()
