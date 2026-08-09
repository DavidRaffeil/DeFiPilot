# core/system_health.py — V6.0.0 (Log Rotation, Heartbeat & Health Check)
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import time
from typing import Any, Dict, List, Optional

HEALTH_PATH = Path("data/health.json")
START_TIME = time.time()


def rotate_log_file(path: Path, max_bytes: int = 5_000_000, backup_count: int = 5) -> bool:
    """Effectue la rotation d'un fichier journal s'il dépasse max_bytes.

    Décale path.N -> path.N+1, path.1 -> path.2, path -> path.1 et supprime les backups > backup_count.
    """
    if not isinstance(path, Path):
        path = Path(path)

    if not path.exists() or not path.is_file():
        return False

    try:
        if path.stat().st_size < max_bytes:
            return False
    except OSError:
        return False

    # Suppression du dernier backup excédentaire s'il existe
    oldest_backup = Path(f"{path}.{backup_count}")
    if oldest_backup.exists():
        try:
            oldest_backup.unlink()
        except OSError:
            pass

    # Décalage des backups existants (N-1 -> N)
    for i in range(backup_count - 1, 0, -1):
        src = Path(f"{path}.{i}")
        dest = Path(f"{path}.{i + 1}")
        if src.exists():
            try:
                os.replace(src, dest)
            except OSError:
                pass

    # Déplacement du fichier principal courant vers path.1
    backup_1 = Path(f"{path}.1")
    try:
        os.replace(path, backup_1)
        return True
    except OSError:
        return False


def enregistrer_heartbeat(
    health_path: Path = HEALTH_PATH,
    loop_count: int = 0,
    run_id: str = "",
    extra_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Écrit ou met à jour l'état de santé (heartbeat) du daemon dans health_path."""
    if not isinstance(health_path, Path):
        health_path = Path(health_path)

    health_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = health_path.with_suffix(health_path.suffix + ".tmp")

    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    uptime_sec = round(time.time() - START_TIME, 2)

    payload: Dict[str, Any] = {
        "timestamp": now_utc,
        "status": "HEALTHY",
        "loop_count": loop_count,
        "run_id": run_id,
        "uptime_seconds": uptime_sec,
        "tag": "[SIMULATION / DRY-RUN]",
    }

    if isinstance(extra_data, dict):
        payload.update(extra_data)

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, health_path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass

    return payload


def verifier_sante_daemon(health_path: Path = HEALTH_PATH, max_lag_seconds: float = 30.0) -> Dict[str, Any]:
    """Vérifie la fraîcheur et la validité du heartbeat du daemon."""
    if not isinstance(health_path, Path):
        health_path = Path(health_path)

    if not health_path.exists() or not health_path.is_file():
        return {
            "healthy": False,
            "status": "MISSING_HEARTBEAT",
            "message": f"Le fichier de heartbeat {health_path} est introuvable.",
        }

    try:
        with open(health_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        return {
            "healthy": False,
            "status": "CORRUPT_HEARTBEAT",
            "message": f"Impossible de lire le heartbeat : {exc}",
        }

    timestamp_str = data.get("timestamp")
    if not isinstance(timestamp_str, str):
        return {
            "healthy": False,
            "status": "INVALID_TIMESTAMP",
            "message": "Horodatage absent ou invalide dans le heartbeat.",
        }

    try:
        if timestamp_str.endswith("Z"):
            ts_norm = timestamp_str[:-1] + "+00:00"
        else:
            ts_norm = timestamp_str
        hb_dt = datetime.fromisoformat(ts_norm)
        now_dt = datetime.now(timezone.utc)
        lag_seconds = abs((now_dt - hb_dt).total_seconds())
    except Exception as exc:
        return {
            "healthy": False,
            "status": "TIMESTAMP_PARSE_ERROR",
            "message": f"Échec de conversion de l'horodatage : {exc}",
        }

    is_healthy = lag_seconds <= max_lag_seconds
    return {
        "healthy": is_healthy,
        "status": "HEALTHY" if is_healthy else "STALE_HEARTBEAT",
        "lag_seconds": round(lag_seconds, 2),
        "data": data,
    }


def nettoyer_fichiers_temporaires(dir_path: Path = Path("data"), max_age_seconds: float = 86400.0) -> List[Path]:
    """Nettoie les fichiers temporaires .tmp obsolètes créés depuis plus de max_age_seconds."""
    if not isinstance(dir_path, Path):
        dir_path = Path(dir_path)

    fichiers_nettoyes: List[Path] = []
    if not dir_path.exists() or not dir_path.is_dir():
        return fichiers_nettoyes

    now = time.time()
    for root, _, files in os.walk(dir_path):
        for f in files:
            if f.endswith(".tmp"):
                fpath = Path(root) / f
                try:
                    mtime = fpath.stat().st_mtime
                    if now - mtime > max_age_seconds:
                        fpath.unlink()
                        fichiers_nettoyes.append(fpath)
                except OSError:
                    pass

    return fichiers_nettoyes


__all__ = [
    "HEALTH_PATH",
    "rotate_log_file",
    "enregistrer_heartbeat",
    "verifier_sante_daemon",
    "nettoyer_fichiers_temporaires",
]
