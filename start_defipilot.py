# start_defipilot.py — V4.4.3
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Dict, Any
import subprocess
import sys
import json
import time

"""Lance DeFiPilot en mode complet en démarrant le daemon, ControlPilot et la GUI tout en supervisant le journal de contrôle et en assurant un arrêt propre via Ctrl+C."""

base_dir = Path(__file__).resolve().parent
journal_daemon_script = base_dir / "journal_daemon.py"
controlpilot_script = base_dir / "launch_controlpilot.py"
gui_script = base_dir / "gui" / "main_window.py"
pools_path = base_dir / "data" / "pools_sample.json"
journal_path = base_dir / "journal_signaux.jsonl"
control_output_path = base_dir / "journal_control.jsonl"

def start_processes() -> List[subprocess.Popen[bytes]]:
    cmd_daemon = [
        sys.executable,
        str(journal_daemon_script),
        "--pools",
        str(pools_path),
        "--interval",
        "30",
        "--journal",
        str(journal_path),
        "--max-loops",
        "0",
    ]
    cmd_control = [
        sys.executable,
        str(controlpilot_script),
        "--input",
        str(journal_path),
        "--output",
        str(control_output_path),
        "--interval",
        "60",
        "--max-events",
        "100",
    ]
    cmd_gui = [
        sys.executable,
        str(gui_script),
    ]
    print("========================================")
    print(" DeFiPilot — Lancement global")
    print("========================================")
    print(f"Daemon   : {' '.join(cmd_daemon)}")
    print(f"Control  : {' '.join(cmd_control)}")
    print(f"GUI      : {cmd_gui[-1]}")
    print(f"Journal  : {journal_path}")
    print("========================================")
    proc_daemon = subprocess.Popen(cmd_daemon, cwd=str(base_dir))
    proc_control = subprocess.Popen(cmd_control, cwd=str(base_dir))
    proc_gui = subprocess.Popen(cmd_gui, cwd=str(base_dir))
    return [proc_daemon, proc_control, proc_gui]

def lire_dernier_resume(fichier: Path) -> Optional[Dict[str, Any]]:
    if not fichier.exists():
        return None
    try:
        with fichier.open("r", encoding="utf-8") as flux:
            lignes = [ligne.strip() for ligne in flux.readlines() if ligne.strip()]
    except OSError:
        return None
    if not lignes:
        return None
    derniere = lignes[-1]
    try:
        donnees = json.loads(derniere)
    except json.JSONDecodeError:
        return None
    if isinstance(donnees, dict):
        return donnees
    return None

def afficher_resume_console(resume: Dict[str, Any]) -> None:
    ts = resume.get("timestamp", "?")
    contexte = resume.get("context", "?")
    apr_valeur = resume.get("apr_mean")
    tvl_valeur = resume.get("tvl_total")
    if isinstance(apr_valeur, (int, float)):
        apr_texte = f"{float(apr_valeur):.4f}"
    else:
        apr_texte = "?"
    if isinstance(tvl_valeur, (int, float)):
        tvl_texte = str(tvl_valeur)
    else:
        tvl_texte = "?"
    print(f"[SUPERVISION] {ts} | contexte={contexte} | APR={apr_texte} | TVL={tvl_texte}")

def main() -> int:
    processes = start_processes()
    interval_supervision = 30
    derniere_signature: Optional[str] = None
    try:
        while True:
            etats = [process.poll() for process in processes]
            if any(etat is not None for etat in etats):
                break
            resume = lire_dernier_resume(control_output_path)
            if resume is not None:
                signature = json.dumps(resume, sort_keys=True)
                if signature != derniere_signature:
                    afficher_resume_console(resume)
                    derniere_signature = signature
            time.sleep(interval_supervision)
    except KeyboardInterrupt:
        print("Interruption demandée, arrêt des processus...")
        for process in processes:
            if process.poll() is None:
                try:
                    process.terminate()
                except OSError:
                    pass
        for process in processes:
            try:
                process.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                pass
        return 1
    for process in processes:
        if process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
    for process in processes:
        try:
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass
    return 0

if __name__ == "__main__":
    sys.exit(main())