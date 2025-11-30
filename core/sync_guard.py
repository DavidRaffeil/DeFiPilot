from __future__ import annotations
"""core/sync_guard.py — V5.0.0
Utilitaires de synchronisation lecture/écriture pour journaux JSONL.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List
import json, os, time

LOCK_SUFFIX = ".lock"

def lock_path_for(target: os.PathLike | str) -> Path:
    p = Path(target)
    return p.with_name(p.name + LOCK_SUFFIX)

def _try_create_lock(lock_path: Path) -> bool:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(lock_path), flags, 0o644)
    except (FileExistsError, OSError):
        return False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(f"pid={os.getpid()}\\n")
            f.write(f"ts={int(time.time())}\\n")
    except OSError:
        try: lock_path.unlink(missing_ok=True)
        except OSError: pass
        return False
    return True

def _is_stale(lock_path: Path, stale_s: int) -> bool:
    try: mtime = lock_path.stat().st_mtime
    except OSError: return False
    return (time.time() - mtime) > stale_s

def acquire_lock(target: os.PathLike | str, *, timeout_s: float = 2.0,
                 poll_s: float = 0.05, stale_s: int = 300) -> bool:
    lock = lock_path_for(target)
    deadline = time.time() + timeout_s
    while True:
        if _try_create_lock(lock): return True
        if _is_stale(lock, stale_s):
            try: lock.unlink()
            except OSError: pass
        if time.time() >= deadline: return False
        time.sleep(poll_s)

def release_lock(target: os.PathLike | str) -> None:
    try: lock_path_for(target).unlink(missing_ok=True)
    except OSError: pass

def is_locked(target: os.PathLike | str) -> bool:
    return lock_path_for(target).exists()

def is_fresh(target: os.PathLike | str, max_age_s: int) -> bool:
    p = Path(target)
    if not p.exists(): return False
    try: mtime = p.stat().st_mtime
    except OSError: return False
    return (time.time() - mtime) <= max_age_s

def _tail_lines(p: Path, max_lines: int) -> List[str]:
    try:
        with p.open("r", encoding="utf-8") as f:
            lines = [ln.rstrip("\\n") for ln in f if ln.strip()]
    except OSError: return []
    return lines[-max_lines:] if max_lines>0 else lines

def safe_read_jsonl(target: os.PathLike | str, *, max_lines: int = 100,
                    wait_if_locked: bool = True, timeout_s: float = 2.0,
                    parse: bool = True) -> List[Any]:
    p = Path(target)
    deadline = time.time() + timeout_s
    while is_locked(p):
        if not wait_if_locked or time.time() >= deadline: break
        time.sleep(0.02)
    lines = _tail_lines(p, max_lines)
    if not parse: return lines
    out: List[Any] = []
    for ln in lines:
        try: out.append(json.loads(ln))
        except json.JSONDecodeError: continue
    return out

@dataclass
class ReadSnapshot:
    lines: List[str]
    parsed: List[Any]
    fresh: bool

def read_snapshot(target: os.PathLike | str, *, max_lines: int = 100,
                  freshness_s: int = 120) -> ReadSnapshot:
    p = Path(target)
    raw = safe_read_jsonl(p, max_lines=max_lines, wait_if_locked=True,
                          timeout_s=2.0, parse=False)
    parsed: List[Any] = []
    for ln in raw:
        try: parsed.append(json.loads(ln))
        except json.JSONDecodeError: continue
    return ReadSnapshot(lines=raw, parsed=parsed, fresh=is_fresh(p, freshness_s))
