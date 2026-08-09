# core/state_manager.py — V6.0.0 (Resilient & Atomic State Management)
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
from threading import Event, Lock, Thread
from time import monotonic, sleep
from typing import Any, Dict, Optional

try:
    import fcntl
except ImportError:
    fcntl = None  # Support pour les environnements sans fcntl


class StateLockError(Exception):
    """Exception levée lorsqu'une autre instance détient déjà le verrou d'état."""
    pass


STATE_PATH = Path("data/state.json")
LOCK_PATH = Path("data/defipilot.lock")
_TMP_SUFFIX = ".tmp"
_BAK_SUFFIX = ".bak"
AUTO_SAVE_INTERVAL_SECONDS = 10.0

_state_lock = Lock()
_state: Dict[str, Any] = {}
_state_loaded = False
_current_loaded_path: Optional[Path] = None
_dirty = False
_auto_save_thread: Optional[Thread] = None
_auto_save_stop = Event()
_auto_save_interval = AUTO_SAVE_INTERVAL_SECONDS
_auto_save_last = 0.0

_file_lock_fd: Optional[int] = None
_file_lock_path: Optional[Path] = None


def acquire_state_lock(lock_path: Path = LOCK_PATH) -> None:
    """Acquiert un verrou exclusif non-bloquant sur le fichier lock_path.

    Lève StateLockError si une autre instance s'exécute simultanément.
    """
    global _file_lock_fd, _file_lock_path
    if not isinstance(lock_path, Path):
        lock_path = Path(lock_path)

    lock_path.parent.mkdir(parents=True, exist_ok=True)

    if fcntl is None:
        return

    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o666)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _file_lock_fd = fd
        _file_lock_path = lock_path
    except (IOError, OSError) as exc:
        if 'fd' in locals():
            try:
                os.close(fd)
            except OSError:
                pass
        raise StateLockError(
            f"Une autre instance de DeFiPilot est déjà en cours d'exécution (verrou {lock_path} actif)."
        ) from exc


def release_state_lock() -> None:
    """Libère le verrou d'instance processeur s'il est détenu."""
    global _file_lock_fd, _file_lock_path
    if _file_lock_fd is not None:
        try:
            if fcntl is not None:
                fcntl.flock(_file_lock_fd, fcntl.LOCK_UN)
            os.close(_file_lock_fd)
        except OSError:
            pass
        _file_lock_fd = None
        _file_lock_path = None


def _ensure_state_loaded(path: Path) -> None:
    global _state_loaded, _current_loaded_path
    if not isinstance(path, Path):
        path = Path(path)
    if _state_loaded and _current_loaded_path == path:
        return
    load_state(path)


def _load_state_from_disk(path: Path) -> Dict[str, Any]:
    bak_path = path.with_suffix(path.suffix + _BAK_SUFFIX)

    # 1. Essayer de charger le fichier principal
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, dict):
                    return data
        except Exception as exc:
            print(f"[WARN] Fichier d'état corrompu ou illisible ({path}) : {exc}. Restauration depuis le backup...")

    # 2. Restauration depuis le backup .bak en cas de corruption ou fichier principal absent
    if bak_path.exists():
        try:
            with open(bak_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, dict):
                    print(f"[INFO] État restauré avec succès depuis le backup ({bak_path}).")
                    try:
                        shutil.copy2(bak_path, path)
                    except OSError:
                        pass
                    return data
        except Exception as exc:
            print(f"[WARN] Impossible de lire le fichier backup ({bak_path}) : {exc}")

    return {}


def _validate_state(state: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(state, dict):
        return {}
    return state


def get_state(path: Path = STATE_PATH) -> Dict[str, Any]:
    _ensure_state_loaded(path)
    with _state_lock:
        return dict(_state)


def update_state(new_state: Dict[str, Any], path: Path = STATE_PATH) -> Dict[str, Any]:
    global _dirty
    if not isinstance(new_state, dict):
        raise TypeError("L'état doit être un dictionnaire")
    _ensure_state_loaded(path)
    with _state_lock:
        _state.clear()
        _state.update(_validate_state(new_state))
        _dirty = True
        return dict(_state)


def set_balances(balances: Dict[str, Any], path: Path = STATE_PATH) -> Dict[str, Any]:
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
    global _state_loaded, _state, _dirty, _current_loaded_path
    if not isinstance(path, Path):
        path = Path(path)
    with _state_lock:
        _state = _load_state_from_disk(path)
        _state_loaded = True
        _current_loaded_path = path
        _dirty = False
        return dict(_state)


def save_state(state: Optional[Dict[str, Any]] = None, path: Optional[Path] = None) -> None:
    global _dirty, _auto_save_last

    if path is None:
        path = STATE_PATH
    if not isinstance(path, Path):
        try:
            path = Path(path)
        except Exception:
            path = STATE_PATH

    _ensure_state_loaded(path)

    with _state_lock:
        if state is None:
            if not _dirty:
                return
            state_to_save = json.loads(json.dumps(_state))
        else:
            if not isinstance(state, dict):
                raise TypeError("L'état à sauvegarder doit être un dictionnaire")
            state_to_save = json.loads(json.dumps(state))
        _write_state_to_disk(state_to_save, path)
        _dirty = False
        _auto_save_last = monotonic()


def _write_state_to_disk(state: Dict[str, Any], path: Path) -> None:
    if not isinstance(path, Path):
        path = Path(path)
    tmp_path = path.with_suffix(path.suffix + _TMP_SUFFIX)
    bak_path = path.with_suffix(path.suffix + _BAK_SUFFIX)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        try:
            shutil.copy2(path, bak_path)
        except OSError:
            pass

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
                pass


def start_auto_save(interval_seconds: float = AUTO_SAVE_INTERVAL_SECONDS, path: Path = STATE_PATH) -> None:
    global _auto_save_thread, _auto_save_interval, _auto_save_last
    _auto_save_interval = float(interval_seconds)
    _auto_save_last = 0.0  # Forcer le premier déclenchement sans attendre interval
    _ensure_state_loaded(path)
    if _auto_save_thread and _auto_save_thread.is_alive():
        return
    _auto_save_stop.clear()
    _auto_save_thread = Thread(target=_auto_save_worker, args=(path,), daemon=True)
    _auto_save_thread.start()


def stop_auto_save() -> None:
    _auto_save_stop.set()


def _auto_save_worker(path: Path) -> None:
    global _auto_save_last
    while not _auto_save_stop.is_set():
        sleep(0.05)
        now = monotonic()
        if now - _auto_save_last < _auto_save_interval:
            continue
        try:
            save_state(None, path)
        except Exception:
            pass
        _auto_save_last = monotonic()


__all__ = [
    "STATE_PATH",
    "LOCK_PATH",
    "AUTO_SAVE_INTERVAL_SECONDS",
    "StateLockError",
    "acquire_state_lock",
    "release_state_lock",
    "get_state",
    "update_state",
    "set_balances",
    "load_state",
    "save_state",
    "start_auto_save",
    "stop_auto_save",
]