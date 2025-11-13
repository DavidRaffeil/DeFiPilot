# control/ai_evaluator.py — V5.0.0
from __future__ import annotations
"""Évaluation de la cohérence entre signaux IA et contextes classiques.

- Lit :
  • journal_signaux.jsonl (classique) — champs: timestamp, context, ...
  • journal_control.jsonl (IA) — champs: AI_context, AI_confidence, ...
    (fallback IA possible depuis journal_signaux.jsonl si tag == "AI_context")
- Fenêtrage : --last N ou --minutes M (sur le journal classique)
- Appariement temporel IA ↔ classique par plus proche voisin dans une tolérance
  configurable (--tolerance secondes, défaut 900s = 15min)
- Produit des métriques : taux d'accord, matrice de confusion, contexte modal,
  résumé IA (dernier contexte + confiance), etc.
- Sortie : impression JSON (stdout) et optionnel append JSONL (--output)

Dépendances : standard library uniquement.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import argparse
import json

# ------------------ utilitaires généraux ------------------

def _parse_ts(value: Any) -> Optional[datetime]:
    """Parse un horodatage varié en datetime aware (localisée UTC→local)."""
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).astimezone()
        except Exception:
            return None
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(text).astimezone()
        except Exception:
            return None
    return None


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not path.exists():
        return out
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict):
                    out.append(obj)
    except OSError:
        return out
    return out


# ------------------ sélection fenêtrée ------------------

def _select_window(data: List[Dict[str, Any]], *, last: Optional[int], minutes: Optional[int]) -> List[Dict[str, Any]]:
    """Sous-sélectionne une fenêtre depuis la fin selon last|minutes.
    Priorité à minutes si fourni; sinon last; sinon tout le flux.
    """
    if not data:
        return []

    lines = data
    if minutes is not None and minutes > 0:
        # borne basse sur timestamp
        try:
            latest_ts = None
            for obj in reversed(lines):
                ts = _parse_ts(obj.get("timestamp") or obj.get("ts"))
                if ts is not None:
                    latest_ts = ts
                    break
            if latest_ts is None:
                return lines[-last:] if last else lines
            cutoff = latest_ts - timedelta(minutes=minutes)
            window = [o for o in lines if (_parse_ts(o.get("timestamp") or o.get("ts")) or datetime.min.replace(tzinfo=timezone.utc)) >= cutoff]
            return window
        except Exception:
            return lines[-last:] if last else lines

    if last is not None and last > 0:
        return lines[-last:]

    return lines


# ------------------ extraction contextes ------------------

def _extract_classic_contexts(data: Iterable[Dict[str, Any]]) -> List[Tuple[datetime, str]]:
    out: List[Tuple[datetime, str]] = []
    for obj in data:
        ctx = obj.get("context")
        if not isinstance(ctx, str):
            continue
        ts = _parse_ts(obj.get("timestamp") or obj.get("ts"))
        if ts is None:
            continue
        out.append((ts, ctx.strip()))
    return out


def _extract_ai_from_control(control_data: Iterable[Dict[str, Any]]) -> List[Tuple[datetime, str, Optional[float]]]:
    out: List[Tuple[datetime, str, Optional[float]]] = []
    for obj in control_data:
        ctx = obj.get("AI_context")
        if not isinstance(ctx, str):
            continue
        ts = _parse_ts(obj.get("timestamp") or obj.get("ts"))
        if ts is None:
            continue
        conf = obj.get("AI_confidence")
        try:
            conf_f = float(conf) if isinstance(conf, (int, float, str)) else None
        except Exception:
            conf_f = None
        out.append((ts, ctx.strip(), conf_f))
    return out


def _extract_ai_from_signals(signals_data: Iterable[Dict[str, Any]]) -> List[Tuple[datetime, str, Optional[float]]]:
    out: List[Tuple[datetime, str, Optional[float]]] = []
    for obj in signals_data:
        if obj.get("tag") != "AI_context":
            continue
        ctx = obj.get("AI_context")
        if not isinstance(ctx, str):
            continue
        ts = _parse_ts(obj.get("timestamp") or obj.get("ts"))
        if ts is None:
            continue
        conf = obj.get("AI_confidence")
        try:
            conf_f = float(conf) if isinstance(conf, (int, float, str)) else None
        except Exception:
            conf_f = None
        out.append((ts, ctx.strip(), conf_f))
    return out


# ------------------ appariement & métriques ------------------

def _norm_ctx(ctx: str) -> str:
    c = ctx.strip().lower()
    if c in {"favorable", "favourable", "bullish"}:
        return "favorable"
    if c in {"neutre", "neutral"}:
        return "neutre"
    if c in {"defavorable", "unfavorable", "bearish"}:
        return "defavorable"
    return c


def _pair_by_time(
    ai_list: List[Tuple[datetime, str, Optional[float]]],
    cl_list: List[Tuple[datetime, str]],
    *,
    tolerance: timedelta,
) -> List[Tuple[str, str]]:
    """Apparie chaque point IA au classique le plus proche dans la tolérance.
    Retourne la liste des paires (ai_ctx_norm, classic_ctx_norm).
    """
    pairs: List[Tuple[str, str]] = []
    if not ai_list or not cl_list:
        return pairs

    cl_sorted = sorted(cl_list, key=lambda x: x[0])
    for ts_ai, ctx_ai, _ in ai_list:
        # recherche plus proche voisin
        best_dt = None
        best_ctx = None
        for ts_c, ctx_c in cl_sorted:
            dt = abs((ts_ai - ts_c).total_seconds())
            if best_dt is None or dt < best_dt:
                best_dt = dt
                best_ctx = ctx_c
        if best_dt is not None and best_dt <= tolerance.total_seconds():
            pairs.append((_norm_ctx(ctx_ai), _norm_ctx(best_ctx or "")))
    return pairs


@dataclass
class EvalResult:
    window_info: Dict[str, Any]
    samples: int
    paired: int
    agreement: float
    confusion: Dict[str, Dict[str, int]]
    classic_modal: Optional[str]
    ai_latest: Optional[str]
    ai_latest_confidence: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "window": self.window_info,
            "samples": self.samples,
            "paired": self.paired,
            "agreement": self.agreement,
            "confusion": self.confusion,
            "classic_modal": self.classic_modal,
            "ai_latest": self.ai_latest,
            "ai_latest_confidence": self.ai_latest_confidence,
        }


def evaluate(
    signals_path: Path,
    control_path: Optional[Path],
    *,
    last: Optional[int] = 64,
    minutes: Optional[int] = None,
    tolerance_seconds: int = 900,
) -> EvalResult:
    # charge données
    signals = _load_jsonl(signals_path)
    window = _select_window(signals, last=last, minutes=minutes)

    cl_ctx = _extract_classic_contexts(window)
    samples = len(cl_ctx)

    ai_list: List[Tuple[datetime, str, Optional[float]]] = []
    ai_latest_ctx: Optional[str] = None
    ai_latest_conf: Optional[float] = None

    # IA depuis control si dispo
    if control_path is not None and control_path.exists():
        control_data = _load_jsonl(control_path)
        ai_list = _extract_ai_from_control(control_data)
        if ai_list:
            ts, c, conf = ai_list[-1]
            ai_latest_ctx = _norm_ctx(c)
            ai_latest_conf = conf

    # Fallback IA depuis signals (tag)
    if not ai_list:
        ai_list = _extract_ai_from_signals(signals)
        if ai_list:
            ts, c, conf = ai_list[-1]
            ai_latest_ctx = _norm_ctx(c)
            ai_latest_conf = conf

    # appariement
    pairs = _pair_by_time(ai_list, cl_ctx, tolerance=timedelta(seconds=tolerance_seconds))

    # confusion & taux d'accord
    confusion: Dict[str, Dict[str, int]] = {}
    agree = 0
    for ai_c, cl_c in pairs:
        confusion.setdefault(ai_c, {})[cl_c] = confusion.get(ai_c, {}).get(cl_c, 0) + 1
        if ai_c == cl_c:
            agree += 1

    agreement = (agree / len(pairs)) if pairs else 0.0

    # contexte modal classique
    modal = None
    if cl_ctx:
        counts: Dict[str, int] = {}
        for _, c in cl_ctx:
            counts[_norm_ctx(c)] = counts.get(_norm_ctx(c), 0) + 1
        modal = max(counts.items(), key=lambda kv: kv[1])[0]

    # infos fenêtre
    w_from = None
    w_to = None
    for obj in window:
        ts = _parse_ts(obj.get("timestamp") or obj.get("ts"))
        if ts is None:
            continue
        if w_from is None or ts < w_from:
            w_from = ts
        if w_to is None or ts > w_to:
            w_to = ts

    window_info = {
        "count": len(window),
        "from": w_from.astimezone().isoformat() if w_from else None,
        "to": w_to.astimezone().isoformat() if w_to else None,
        "basis": "minutes" if (minutes and minutes > 0) else "last",
        "value": minutes if (minutes and minutes > 0) else last,
        "tolerance_seconds": tolerance_seconds,
    }

    return EvalResult(
        window_info=window_info,
        samples=samples,
        paired=len(pairs),
        agreement=agreement,
        confusion=confusion,
        classic_modal=modal,
        ai_latest=ai_latest_ctx,
        ai_latest_confidence=ai_latest_conf,
    )


# ------------------ CLI ------------------

def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False))
        f.write("\n")


def _cli(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="control.ai_evaluator",
        description="Évalue l'accord IA vs contexte classique et produit un résumé JSON.",
    )
    ap.add_argument("--signals", default="journal_signaux.jsonl", help="journal classique (JSONL)")
    ap.add_argument("--control", default="journal_control.jsonl", help="journal IA (JSONL)")
    ap.add_argument("--last", type=int, default=64, help="fenêtre: n dernières lignes (classique)")
    ap.add_argument("--minutes", type=int, default=None, help="fenêtre: n dernières minutes (prioritaire)")
    ap.add_argument("--tolerance", type=int, default=900, help="tolérance d'appariement en secondes (défaut 900)")
    ap.add_argument("--output", default=None, help="chemin JSONL pour append du résultat")
    args = ap.parse_args(argv)

    signals_path = Path(args.signals)
    control_path = Path(args.control) if args.control else None

    res = evaluate(
        signals_path=signals_path,
        control_path=control_path,
        last=args.last,
        minutes=args.minutes,
        tolerance_seconds=args.tolerance,
    )

    payload = res.to_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.output:
        try:
            _append_jsonl(Path(args.output), payload)
        except Exception:
            # pas bloquant pour le CLI
            pass

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())
