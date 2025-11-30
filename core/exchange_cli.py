# core/exchange_cli.py — V5.1.0
from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Optional

from .exchange_format import validate_exchange_payload
from .sync_guard import safe_read_jsonl


def _load(path: str, last: int | None, wait_if_locked: bool = True) -> List[Dict[str, Any]]:
    max_lines = last if (isinstance(last, int) and last > 0) else 0
    parsed = safe_read_jsonl(path, max_lines=max_lines, wait_if_locked=wait_if_locked, timeout_s=2.0, parse=True)
    out: List[Dict[str, Any]] = []
    for obj in parsed:
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _filter(rows: List[Dict[str, Any]], source: Optional[str], ai_only: bool) -> List[Dict[str, Any]]:
    def keep(obj: Dict[str, Any]) -> bool:
        if source and obj.get("source") != source:
            return False
        if ai_only and ("ai_context" not in obj):
            return False
        return True
    return [r for r in rows if keep(r)]


def _validate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    ok = 0
    errors: List[Dict[str, Any]] = []
    for i, r in enumerate(rows):
        valid, errs = validate_exchange_payload(r)
        if valid:
            ok += 1
        elif errs:
            errors.append({"index": i, "errors": errs})
    return {"total": total, "valid": ok, "invalid": total - ok, "errors": errors}


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="core.exchange_cli", description="Inspecte et filtre le bus d'échange inter-bots (JSONL).")
    ap.add_argument("--file", default="exchange_bus.jsonl", help="Chemin du bus JSONL (def: exchange_bus.jsonl)")
    ap.add_argument("--last", type=int, default=50, help="Nombre de lignes récentes à lire (0 = tout)")
    ap.add_argument("--source", type=str, default=None, help="Filtrer par source (ex: ControlPilot, DeFiPilot, ArbiPilot)")
    ap.add_argument("--ai-only", action="store_true", help="Ne garder que les messages contenant ai_context")
    ap.add_argument("--validate", action="store_true", help="Valider le schéma des messages")
    ap.add_argument("--pretty", action="store_true", help="Affichage JSON pretty-print")
    args = ap.parse_args(argv)

    rows = _load(args.file, args.last)
    rows = _filter(rows, args.source, args.ai_only)

    if args.validate:
        report = _validate(rows)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    if args.pretty:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            print(json.dumps(r, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
