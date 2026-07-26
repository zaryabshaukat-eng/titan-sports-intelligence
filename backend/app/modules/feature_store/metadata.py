"""Canonical, deterministic metadata helpers for versioned Feature Store artifacts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, is_dataclass


def canonical_json(value: object) -> str:
    """Serialize configuration with stable ordering for reproducible fingerprints."""
    if is_dataclass(value):
        value = asdict(value)
    return json.dumps(value, default=str, sort_keys=True, separators=(",", ":"))


def fingerprint(value: object) -> str:
    """Return a SHA-256 checksum for an immutable metadata or input snapshot."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def feature_set_checksum(definitions: Iterable[object]) -> str:
    """Fingerprint a complete ordered definition list instead of mutable implementation state."""
    return fingerprint(list(definitions))
