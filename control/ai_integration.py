# control/ai_integration.py — V5.0.0
from __future__ import annotations

from typing import Any

from .ai_adapter import compute_ai_context_from_jsonl, merge_signals


def compute_and_merge_ai_signals(
    classic: dict[str, Any] | None,
    journal_path: str,
    *,
    last: int | None = 32,
    minutes: int | None = None,
) -> dict[str, Any]:
    ai = compute_ai_context_from_jsonl(journal_path, last=last, minutes=minutes)
    return merge_signals(classic, ai)
