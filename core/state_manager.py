# core/state_manager.py — V6.0.0
from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock, Event, Thread
from time import monotonic, sleep
from typing import Any, Dict, Optional

STATE_PATH = Path("data/state.json")
_TMP_SUFFIX = ".tmp"
AUTO_SAVE_INTERVAL_SECONDS = 10.0

_state_lock = Lock()
_state: Dict[str, Any] = {}
_state_loaded = False
_dirty = False
_auto_save_thread: Optional[Thread] = None
_auto_save_stop = Event()
_auto_save_interval = AUTO_SAVE_INTERVAL_SECONDS
_auto_save_last = 0.0


def _ensure_state_loaded(path: Path) -> None:
    global _state_loaded
    if _state_loaded:
        return
    load_state(path)


def _load_state_from_disk(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
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
    global _state_loaded, _state, _dirty
    with _state_lock:
        _state = _load_state_from_disk(path)
        _state_loaded = True
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
                pass


def start_auto_save(interval_seconds: float = AUTO_SAVE_INTERVAL_SECONDS, path: Path = STATE_PATH) -> None:
    global _auto_save_thread, _auto_save_interval
    _auto_save_interval = float(interval_seconds)
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
        sleep(0.5)
        now = monotonic()
        if now - _auto_save_last < _auto_save_interval:
            continue
        try:
            save_state(None, path)
        except Exception:
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