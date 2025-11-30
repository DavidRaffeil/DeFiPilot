# control/ai_adapter.py — V5.0.0
from __future__ import annotations

import argparse
import json
from typing import Any, Iterable

from .ai_analyzer import infer_ai_context


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def compute_ai_context_from_jsonl(path: str, last: int | None = 32, minutes: int | None = None) -> dict[str, Any]:
    from .ai_analyzer import _select_window  # reuse tested windowing
    data = _load_jsonl(path)
    window = _select_window(data, last=last, minutes=minutes)
    res = infer_ai_context(window)
    return {
        "AI_context": res.ai_context,
        "AI_confidence": res.confidence,
        "AI_score": res.score,
        "AI_features": res.features,
        "AI_window": res.window,
    }


def merge_signals(classic: dict[str, Any] | None, ai: dict[str, Any]) -> dict[str, Any]:
    base = dict(classic) if isinstance(classic, dict) else {}
    base.update(ai)
    return base


# --- CLI de diagnostic (facultatif) ---

def _cli(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="control.ai_adapter", description="Calcule et affiche les signaux IA (diagnostic)")
    ap.add_argument("--file", required=True, help="journal_signaux.jsonl")
    ap.add_argument("--last", type=int, default=32)
    ap.add_argument("--minutes", type=int, default=None)
    args = ap.parse_args(argv)

    ai = compute_ai_context_from_jsonl(args.file, last=args.last, minutes=args.minutes)
    print(json.dumps(ai, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())
