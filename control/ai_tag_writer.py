from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
from .ai_integration import compute_and_merge_ai_signals


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False))
        f.write("\n")


def _cli(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="control.ai_tag_writer",
        description="Calcule les tendances IA et les écrit dans journal_signaux.jsonl avec un tag AI_context.",
    )
    ap.add_argument("--input", required=True, help="journal_signaux.jsonl source (lecture)")
    ap.add_argument("--output", required=True, help="journal_signaux.jsonl destination (append)")
    ap.add_argument("--last", type=int, default=32, help="Fenêtre (n dernières lignes)")
    ap.add_argument("--minutes", type=int, default=None)
    args = ap.parse_args(argv)

    merged = compute_and_merge_ai_signals({}, args.input, last=args.last, minutes=args.minutes)
    # Ajoute un tag explicite pour filtrage
    merged["tag"] = "AI_context"
    _append_jsonl(Path(args.output), merged)
    print(json.dumps({"status": "ok", "wrote": True, "output": args.output, "AI_context": merged.get("AI_context"), "AI_confidence": merged.get("AI_confidence")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())
