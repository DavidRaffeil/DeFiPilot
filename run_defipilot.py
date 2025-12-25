#!/usr/bin/env python3
# run_defipilot.py — V5.5.0
"""
run_defipilot.py — lance le journal_daemon + le dashboard GUI.

Usage typique :
    python run_defipilot.py --pools data/pools_sample.json --interval 30

Options :
    --pools      : fichier JSON des stats de pools (liste de dicts) [OBLIGATOIRE]
    --cfg        : fichier JSON de config (optionnel)
    --interval   : intervalle entre deux écritures (secondes, défaut 30)
    --max-loops  : nombre max d’itérations pour le daemon (0 = infini)
    --journal    : chemin du journal JSONL (défaut: journal_signaux.jsonl)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DeFiPilot — Lanceur complet (daemon + dashboard)")
    parser.add_argument(
        "--pools",
        required=True,
        help="Fichier JSON des stats de pools (liste de dicts)",
    )
    parser.add_argument(
        "--cfg",
        default=None,
        help="Fichier JSON de configuration (optionnel)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Intervalle en secondes entre deux écritures par le daemon (défaut: 30)",
    )
    parser.add_argument(
        "--max-loops",
        type=int,
        default=0,
        help="Nombre max d’itérations pour le daemon (0 = infini)",
    )
    parser.add_argument(
        "--journal",
        default="journal_signaux.jsonl",
        help="Chemin du journal JSONL (défaut: journal_signaux.jsonl)",
    )
    args = parser.parse_args(argv)

    root_dir = Path(__file__).resolve().parent
    journal_path = (root_dir / args.journal).resolve()
    pools_path = (root_dir / args.pools).resolve()
    cfg_path = (root_dir / args.cfg).resolve() if args.cfg else None

    strategy_cfg_default = (root_dir / "config" / "strategy_v5_5.json").resolve()
    if "DEFIPILOT_STRATEGY_CFG" not in os.environ and strategy_cfg_default.exists():
        os.environ["DEFIPILOT_STRATEGY_CFG"] = str(strategy_cfg_default)

    os.environ["DEFIPILOT_JOURNAL"] = str(journal_path)

    daemon_cmd = [
        sys.executable,
        str(root_dir / "journal_daemon.py"),
        "--pools",
        str(pools_path),
        "--interval",
        str(args.interval),
        "--journal",
        str(journal_path),
        "--max-loops",
        str(args.max_loops),
    ]
    if cfg_path is not None:
        daemon_cmd.extend(["--cfg", str(cfg_path)])

    strategy_cfg_env = os.environ.get("DEFIPILOT_STRATEGY_CFG", "(non défini)")

    print("========================================")
    print(" DeFiPilot — Lancement global")
    print("========================================")
    print(f"Daemon :  {daemon_cmd}")
    print(f"Journal : {journal_path}")
    print(f"GUI     : gui/main_window.py")
    print(f"Strategy: {strategy_cfg_env}")
    print("========================================")

    try:
        daemon_proc = subprocess.Popen(daemon_cmd)
    except Exception as exc:
        print(f"[ERROR] Impossible de lancer journal_daemon.py : {exc}")
        return 1

    time.sleep(1.0)

    try:
        from gui.main_window import MainWindow  # type: ignore

        app = MainWindow()
        app.mainloop()
    except KeyboardInterrupt:
        print("[INFO] Arrêt demandé par l'utilisateur (Ctrl+C).")
    finally:
        if daemon_proc.poll() is None:
            print("[INFO] Arrêt du daemon…")
            try:
                daemon_proc.terminate()
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
