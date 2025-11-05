#!/usr/bin/env python3
# journal_daemon.py — V4.2.0
"""
DeFiPilot — Journaliseur continu de signaux.

Boucle simple :
- lit les stats de pools depuis un fichier JSON,
- calcule contexte + policy via core.market_signals_adapter,
- écrit dans journal_signaux.jsonl à chaque itération.

Usage typique :
    python journal_daemon.py --pools data/pools_sample.json --interval 30

Options :
    --pools      : fichier JSON des stats de pools (obligatoire)
    --cfg        : fichier JSON de config (optionnel)
    --interval   : intervalle entre deux écritures (secondes, défaut 30)
    --max-loops  : nombre max d’itérations (0 = boucle infinie)
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from core.market_signals_adapter import calculer_contexte_et_policy

VERSION = "V4.2.0"


def _read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _ensure_mapping(obj: Any) -> Mapping[str, Any]:
    if isinstance(obj, Mapping):
        return obj
    return {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DeFiPilot – Journaliseur continu de signaux")
    parser.add_argument("--pools", required=True, help="Fichier JSON des stats de pools (liste de dicts)")
    parser.add_argument("--cfg", default=None, help="Fichier JSON de configuration (optionnel)")
    parser.add_argument("--interval", type=int, default=30, help="Intervalle en secondes entre deux écritures (défaut: 30)")
    parser.add_argument("--max-loops", type=int, default=0, help="Nombre max d’itérations (0 = infini)")
    parser.add_argument("--journal", default="journal_signaux.jsonl", help="Chemin du journal JSONL (défaut: journal_signaux.jsonl)")
    args = parser.parse_args(argv)

    pools_path = Path(args.pools)
    cfg_path = Path(args.cfg) if args.cfg else None
    journal_path = args.journal
    interval_s = max(1, int(args.interval))
    max_loops = int(args.max_loops)

    # Chargement de la config (une fois)
    cfg: Mapping[str, Any] = {}
    if cfg_path:
        try:
            cfg = _ensure_mapping(_read_json(cfg_path))
        except Exception as exc:
            print(f"[WARN] Config illisible ({cfg_path}): {exc} — utilisation des paramètres par défaut")
            cfg = {}

    last_context: str | None = None
    loop_idx = 0

    print(f"[INFO] Journaliseur continu démarré.")
    print(f"       pools   = {pools_path}")
    print(f"       cfg     = {cfg_path if cfg_path else '(aucune)'}")
    print(f"       journal = {journal_path}")
    print(f"       interval= {interval_s}s, max_loops={max_loops or 'infini'}")

    while True:
        loop_idx += 1

        # Chargement des pools à chaque itération (pour prendre en compte un fichier mis à jour)
        try:
            pools_obj = _read_json(pools_path)
            if not isinstance(pools_obj, list):
                raise ValueError("Le fichier pools doit contenir une liste de dictionnaires JSON.")
            pools_stats = [x for x in pools_obj if isinstance(x, dict)]
        except Exception as exc:
            print(f"[ERROR] Impossible de lire pools ({pools_path}) : {exc}")
            time.sleep(interval_s)
            continue

        run_id = f"journal_daemon-{datetime.utcnow().isoformat(timespec='seconds')}Z"

        try:
            decision, policy = calculer_contexte_et_policy(
                pools_stats=pools_stats,
                cfg=dict(cfg),
                last_context=last_context,
                run_id=run_id,
                version=VERSION,
                journal_path=journal_path,
            )
        except Exception as exc:
            print(f"[ERROR] Échec du calcul stratégie: {exc}")
            time.sleep(interval_s)
            continue

        last_context = decision.context

        print(
            f"[OK] #{loop_idx} {decision.context} "
            f"(score={decision.score:.4f}) "
            f"→ run_id={run_id}"
        )

        if max_loops > 0 and loop_idx >= max_loops:
            print("[INFO] Limite max_loops atteinte, arrêt propre.")
            break

        time.sleep(interval_s)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
