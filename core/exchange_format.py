# core/exchange_format.py — V5.1.0
from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

from .sync_guard import acquire_lock, release_lock, safe_read_jsonl

def now_iso_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def compute_signature(payload: Dict[str, Any]) -> str:
    tmp = dict(payload)
    integ = tmp.get("integrity")
    if isinstance(integ, dict) and "signature" in integ:
        integ = dict(integ)
        integ.pop("signature", None)
        tmp["integrity"] = integ
    h = hashlib.sha256(_canonical_json(tmp).encode("utf-8")).hexdigest()
    return h

_REQUIRED_TOP = ["timestamp", "source", "version"]
_ALLOWED_TOP  = {
    "timestamp": str,
    "source": str,
    "run_id": str,
    "context": str,
    "ai_context": str,
    "ai_confidence": (int, float),
    "metrics": dict,
    "decision": dict,
    "risk": dict,
    "integrity": dict,
    "version": str,
}

def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def validate_exchange_payload(obj: Any) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not isinstance(obj, dict):
        return False, ["payload must be a JSON object"]
    for k in _REQUIRED_TOP:
        if k not in obj:
            errors.append(f"missing required key: {k}")
    for k, v in obj.items():
        expected = _ALLOWED_TOP.get(k)
        if expected and not isinstance(v, expected):
            errors.append(f"bad type for {k}")
    metrics = obj.get("metrics")
    if metrics is not None and not isinstance(metrics, dict):
        errors.append("metrics must be dict")
    return (len(errors) == 0), errors

def write_exchange_payload(path: str | Path, payload: Dict[str, Any]) -> None:
    out = Path(path)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    integrity = payload.get("integrity")
    if not isinstance(integrity, dict):
        integrity = {}
    if "signature" not in integrity:
        integrity["signature"] = compute_signature(payload)
    payload["integrity"] = integrity
    locked = acquire_lock(out, timeout_s=2.0, poll_s=0.05, stale_s=300)
    try:
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False))
            f.write("\n")
    finally:
        if locked:
            release_lock(out)

def read_last_exchange(path: str | Path):
    parsed = safe_read_jsonl(Path(path), max_lines=1, wait_if_locked=True, timeout_s=2.0, parse=True)
    if not parsed:
        return None
    obj = parsed[-1]
    return obj if isinstance(obj, dict) else None

def build_payload(*, source: str, version: str, context=None, ai_context=None, ai_confidence=None, metrics=None):
    payload = {
        "timestamp": now_iso_z(),
        "source": source,
        "version": version,
    }
    if context: payload["context"] = context
    if ai_context: payload["ai_context"] = ai_context
    if ai_confidence: payload["ai_confidence"] = ai_confidence
    if metrics: payload["metrics"] = dict(metrics)
    return payload
