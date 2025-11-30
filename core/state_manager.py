# core/state_manager.py — V4.7.x
"""Gestion centralisée de l'état persistant de DeFiPilot.

Ce module charge, valide et sauvegarde l'état du bot dans un fichier
``.state`` placé à la racine du projet. L'état est conservé en mémoire
et une tâche optionnelle de sauvegarde automatique peut l'écrire
périodiquement sur le disque. Les soldes sont validés pour éviter les
valeurs négatives ou incohérentes.

Étape 5.1 : la sauvegarde est désormais effectuée de manière atomique
pour résister aux coupures ou aux crashs durant l'écriture du fichier.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from threading import Event, Lock, Thread
from time import monotonic, sleep
from typing import Any, Dict, Optional

LOGGER = logging.getLogger(__name__)

STATE_PATH = Path("defipilot.state")
AUTO_SAVE_INTERVAL_SECONDS = 30.0
_TMP_SUFFIX = ".tmp"

_state_lock = Lock()
_state: Dict[str, Any] = {}
_state_loaded = False
_dirty = False

_auto_save_thread: Optional[Thread] = None
_auto_save_stop = Event()
_auto_save_interval = AUTO_SAVE_INTERVAL_SECONDS
_auto_save_last = 0.0


def _ensure_state_loaded(path: Path) -> None:
    """Charger l'état depuis le disque si cela n'a pas déjà été fait."""
    global _state_loaded, _state

    if _state_loaded:
        return

    with _state_lock:
        if _state_loaded:
            return
        try:
            _state = _load_state_from_disk(path)
        except Exception as exc:  # pragma: no cover - journalisation informative
            LOGGER.error("Impossible de charger l'état depuis %s: %s", path, exc)
            _state = {}
        else:
            _state_loaded = True


def _load_state_from_disk(path: Path) -> Dict[str, Any]:
    """Lire l'état depuis le disque et le valider."""
    if not path.exists():
        return {"balances": {}, "metadata": {}}

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {"balances": {}, "metadata": {}}

    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Le fichier d'état doit contenir un objet JSON")

    return _validate_state(data)


def _validate_state(data: Dict[str, Any]) -> Dict[str, Any]:
    """Valider la structure de l'état persistant."""
    balances = data.get("balances", {})
    if not isinstance(balances, dict):
        raise ValueError("La clé 'balances' doit être un objet JSON")

    for adresse, valeur in list(balances.items()):
        if not isinstance(adresse, str) or not adresse:
            raise ValueError("Les clés de 'balances' doivent être des chaînes non vides")
        if not isinstance(valeur, (int, float)):
            raise ValueError("Les soldes doivent être numériques")
        if valeur < 0:
            raise ValueError("Les soldes ne peuvent pas être négatifs")

    data.setdefault("balances", balances)
    data.setdefault("metadata", {})
    if not isinstance(data["metadata"], dict):
        raise ValueError("La clé 'metadata' doit être un objet JSON")

    return data


def get_state(path: Path = STATE_PATH) -> Dict[str, Any]:
    """Retourner une copie de l'état courant."""
    _ensure_state_loaded(path)
    with _state_lock:
        return json.loads(json.dumps(_state))  # copie profonde sûre


def update_state(updates: Dict[str, Any], path: Path = STATE_PATH) -> Dict[str, Any]:
    """Mettre à jour l'état en mémoire et le retourner."""
    global _dirty

    _ensure_state_loaded(path)
    if not isinstance(updates, dict):
        raise TypeError("Les mises à jour doivent être fournies sous forme de dictionnaire")

    with _state_lock:
        merged = dict(_state)
        for key, value in updates.items():
            merged[key] = value
        _validate_state(merged)
        _state.clear()
        _state.update(merged)
        _dirty = True
        return dict(_state)


def set_balances(balances: Dict[str, Any], path: Path = STATE_PATH) -> Dict[str, Any]:
    """Remplacer le dictionnaire des soldes en s'assurant de leur validité."""
    global _dirty

    if not isinstance(balances, dict):
        raise TypeError("Les soldes doivent être fournis sous forme de dictionnaire")

    _ensure_state_loaded(path)
    with _state_lock:
        state = dict(_state)
        state["balances"] = balances
        validated = _validate_state(state)
        _state.clear()
        _state.update(validated)
        _dirty = True
        return dict(_state)


def load_state(path: Path = STATE_PATH) -> Dict[str, Any]:
    """Forcer le rechargement du fichier d'état depuis le disque."""
    global _state_loaded, _state, _dirty

    with _state_lock:
        _state = _load_state_from_disk(path)
        _state_loaded = True
        _dirty = False
        return dict(_state)


def save_state(path: Path = STATE_PATH) -> None:
    """Sauvegarder l'état courant sur le disque de manière atomique."""
    global _dirty, _auto_save_last

    _ensure_state_loaded(path)

    with _state_lock:
        if not _dirty:
            return
        state_to_save = json.loads(json.dumps(_state))
        _write_state_to_disk(state_to_save, path)
        _dirty = False
        _auto_save_last = monotonic()


def _write_state_to_disk(state: Dict[str, Any], path: Path) -> None:
    """Écrire l'état sur le disque en utilisant une écriture atomique."""
    tmp_path = path.with_suffix(path.suffix + _TMP_SUFFIX)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = json.dumps(state, ensure_ascii=False, indent=2)

    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                LOGGER.debug("Suppression impossible du fichier temporaire %s", tmp_path)


def start_auto_save(interval_seconds: float = AUTO_SAVE_INTERVAL_SECONDS, path: Path = STATE_PATH) -> None:
    """Démarrer la sauvegarde automatique de l'état."""
    global _auto_save_thread, _auto_save_interval

    _ensure_state_loaded(path)

    with _state_lock:
        _auto_save_interval = max(1.0, float(interval_seconds))
        if _auto_save_thread and _auto_save_thread.is_alive():
            return
        _auto_save_stop.clear()
        _auto_save_thread = Thread(
            target=_auto_save_worker,
            name="defipilot-state-auto-save",
            args=(path,),
            daemon=True,
        )
        _auto_save_thread.start()


def stop_auto_save() -> None:
    """Arrêter la sauvegarde automatique."""
    if _auto_save_thread and _auto_save_thread.is_alive():
        _auto_save_stop.set()
        _auto_save_thread.join(timeout=_auto_save_interval * 2)



def _auto_save_worker(path: Path) -> None:
    """Tâche d'arrière-plan responsable des sauvegardes périodiques."""
    global _auto_save_last
    while not _auto_save_stop.is_set():
        sleep(0.5)
        if _auto_save_stop.is_set():
            break
        now = monotonic()
        if now - _auto_save_last < _auto_save_interval:
            continue
        try:
            save_state(path)
        except Exception as exc:  # pragma: no cover - journalisation informative
            LOGGER.error("Erreur lors de la sauvegarde automatique de l'état: %s", exc)
            _auto_save_last = monotonic()


__all__ = [
    "STATE_PATH",
    "AUTO_SAVE_INTERVAL_SECONDS",
    "get_state",
    "update_state",
    "set_balances",
    "load_state",
    "save_state",
    "start_auto_save",
    "stop_auto_save",
]