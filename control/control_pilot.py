# control/control_pilot.py — V5.1.0
from __future__ import annotations

"""
Module d'observation produisant des synthèses sur les journaux DeFiPilot.

- Lecture protégée (attente si lock présent) via core.sync_guard
- Écriture protégée (lock en append) du journal de contrôle
- Comportement inchangé côté API/CLI
- V5.1 introduit la lecture consolidée des signaux issus des journaux JSONL.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import argparse
import json
import logging
import time

from .aggregator import AggregatedSnapshot, aggregate_from_config
from .anomaly_detector import Anomaly, detect_anomalies, summarize_anomalies
from core.exchange_format import build_payload, write_exchange_payload
from core.sync_guard import safe_read_jsonl, acquire_lock, release_lock

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structures de données
# ---------------------------------------------------------------------------

@dataclass
class ResumeGlobal:
    """Structure de données représentant la synthèse globale calculée."""

    timestamp: str
    context: str
    apr_mean: float
    tvl_total: float
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Retourne une représentation dictionnaire du résumé global."""
        return {
            "timestamp": self.timestamp,
            "context": self.context,
            "apr_mean": self.apr_mean,
            "tvl_total": self.tvl_total,
            "message": self.message,
        }


@dataclass
class ResumeAnomalies:
    """Résumé global des anomalies détectées par le ControlPilot."""

    timestamp: str
    total_anomalies: int
    by_severity: dict[str, int]
    codes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_anomalies": self.total_anomalies,
            "by_severity": self.by_severity,
            "codes": self.codes,
        }


@dataclass
class SignalConsolide:
    """Représentation structurée d'un signal consolidé marché/IA."""

    timestamp: str
    context: Optional[str] = None
    apr_mean: Optional[float] = None
    tvl_total: Optional[float] = None
    message: Optional[str] = None
    AI_context: Optional[str] = None
    AI_confidence: Optional[float] = None
    AI_score: Optional[float] = None
    AI_features: Optional[dict[str, Any]] = None
    AI_window: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        """Retourne le signal consolidé sous forme de dictionnaire sérialisable."""
        return {
            "timestamp": self.timestamp,
            "context": self.context,
            "apr_mean": self.apr_mean,
            "tvl_total": self.tvl_total,
            "message": self.message,
            "AI_context": self.AI_context,
            "AI_confidence": self.AI_confidence,
            "AI_score": self.AI_score,
            "AI_features": self.AI_features,
            "AI_window": self.AI_window,
        }


# ---------------------------------------------------------------------------
# I/O protégées et utilitaires JSONL
# ---------------------------------------------------------------------------

def charger_evenements(journal_path: Path, max_events: int) -> list[dict[str, Any]]:
    """Charge *au plus* max_events événements récents du JSONL, avec lecture sûre.

    - Attend la libération d'un lock éventuel (écriture en cours).
    - Parse uniquement les lignes JSON valides.
    """
    parsed = safe_read_jsonl(
        journal_path,
        max_lines=max_events if max_events > 0 else 0,
        wait_if_locked=True,
        timeout_s=2.0,
        parse=True,
    )
    events: list[dict[str, Any]] = [obj for obj in parsed if isinstance(obj, dict)]
    return events


def ecrire_resume(resume: ResumeGlobal, output_path: Path) -> None:
    """Écrit le résumé global dans un fichier JSONL en section critique protégée."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return

    locked = acquire_lock(output_path, timeout_s=2.0, poll_s=0.05, stale_s=300)
    try:
        with output_path.open("a", encoding="utf-8") as flux:
            flux.write(json.dumps(resume.to_dict(), ensure_ascii=False))
            flux.write("\n")
    except OSError:
        pass
    finally:
        if locked:
            release_lock(output_path)


def _charger_jsonl_brut(path: Path, max_lines: int | None = None) -> list[dict[str, Any]]:
    """Lit un fichier JSONL via safe_read_jsonl et retourne une liste de dicts.

    Si le fichier n'existe pas ou ne peut pas être lu, retourne une liste vide.
    """
    if not path.exists():
        logger.warning("Fichier JSONL introuvable : %s", path)
        return []

    try:
        parsed = safe_read_jsonl(
            path,
            max_lines=max_lines if (max_lines is not None and max_lines > 0) else 0,
            wait_if_locked=True,
            timeout_s=2.0,
            parse=True,
        )
    except OSError as exc:
        logger.warning("Erreur lors de la lecture du JSONL %s : %s", path, exc)
        return []

    events: list[dict[str, Any]] = [obj for obj in parsed if isinstance(obj, dict)]
    return events


# ---------------------------------------------------------------------------
# Agrégations & calculs
# ---------------------------------------------------------------------------

def calculer_resume(evenements: list[dict[str, Any]]) -> Optional[ResumeGlobal]:
    """Synthétise les événements fournis en un résumé global."""
    if not evenements:
        return None

    occurrences: dict[str, int] = {}
    for evenement in evenements:
        contexte = evenement.get("context")
        if isinstance(contexte, str) and contexte:
            occurrences[contexte] = occurrences.get(contexte, 0) + 1

    contexte_dominant = max(occurrences.items(), key=lambda item: item[1])[0] if occurrences else "inconnu"

    apr_valeurs: list[float] = []
    tvl_valeurs: list[float] = []
    for evenement in evenements:
        for cle in ("metrics", "metrics_locales"):
            bloc = evenement.get(cle)
            if isinstance(bloc, dict):
                apr = bloc.get("apr_mean")
                if isinstance(apr, (int, float)):
                    apr_valeurs.append(float(apr))
                tvl = bloc.get("tvl_sum")
                if isinstance(tvl, (int, float)):
                    tvl_valeurs.append(float(tvl))

    apr_moyen = (sum(apr_valeurs) / len(apr_valeurs)) if apr_valeurs else 0.0
    tvl_total = sum(tvl_valeurs) if tvl_valeurs else 0.0

    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    message = f"Analyse globale sur {len(evenements)} événements."

    return ResumeGlobal(
        timestamp=timestamp,
        context=contexte_dominant,
        apr_mean=apr_moyen,
        tvl_total=tvl_total,
        message=message,
    )


def analyser_anomalies(files: list[Path]) -> Optional[ResumeAnomalies]:
    """Produit un résumé des anomalies détectées à partir d'une liste de fichiers."""
    if not files:
        return None

    config: dict[str, Any] = {"files": [str(path) for path in files]}

    try:
        snapshot: AggregatedSnapshot = aggregate_from_config(config)
    except (FileNotFoundError, OSError):
        logger.debug("Fichiers d'entrée indisponibles pour l'analyse des anomalies.")
        return None

    anomalies: list[Anomaly] = detect_anomalies(snapshot)
    summary: dict[str, Any] = summarize_anomalies(anomalies)

    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    total = summary.get("total", len(anomalies))
    total_anomalies = int(total) if isinstance(total, int) else len(anomalies)

    by_severity_raw = summary.get("by_severity", {})
    if isinstance(by_severity_raw, dict):
        by_severity: dict[str, int] = {
            str(key): int(value)
            for key, value in by_severity_raw.items()
            if isinstance(key, str) and isinstance(value, int)
        }
    else:
        by_severity = {}

    codes_raw = summary.get("codes", [])
    if isinstance(codes_raw, list):
        codes = [str(code) for code in codes_raw if isinstance(code, str)]
    else:
        codes = []

    if not codes:
        codes = [
            anomaly_code
            for anomaly_code in (
                getattr(anomaly, "code", None)
                for anomaly in anomalies
            )
            if isinstance(anomaly_code, str)
        ]

    return ResumeAnomalies(
        timestamp=timestamp,
        total_anomalies=total_anomalies,
        by_severity=by_severity,
        codes=codes,
    )


# ---------------------------------------------------------------------------
# Signaux consolidés (V5.1)
# ---------------------------------------------------------------------------

def _parse_timestamp(value: Any) -> Optional[datetime]:
    """Tente de parser un timestamp varié en datetime timezone-aware."""
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except Exception:
            return None

    if isinstance(value, str):
        texte = value.strip()
        if not texte:
            return None
        if texte.endswith("Z"):
            texte = texte[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(texte)
        except Exception:
            return None

    return None


def _build_signal_from_obj(obj: dict[str, Any]) -> SignalConsolide:
    """Construit un SignalConsolide à partir d'un dictionnaire brut."""
    # Timestamp
    ts_raw = obj.get("timestamp") or obj.get("ts")
    ts_str: str
    if isinstance(ts_raw, str):
        ts_str = ts_raw
    elif isinstance(ts_raw, (int, float)):
        try:
            ts_dt = datetime.fromtimestamp(float(ts_raw), tz=timezone.utc)
            ts_str = ts_dt.isoformat().replace("+00:00", "Z")
        except Exception:
            ts_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    else:
        ts_str = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Contexte
    context_val = obj.get("context")
    context = context_val if isinstance(context_val, str) else None

    # APR / TVL (directs ou dans metrics)
    apr_mean: Optional[float] = None
    tvl_total: Optional[float] = None

    apr_direct = obj.get("apr_mean")
    if isinstance(apr_direct, (int, float)):
        apr_mean = float(apr_direct)

    tvl_direct = obj.get("tvl_total")
    if isinstance(tvl_direct, (int, float)):
        tvl_total = float(tvl_direct)

    metrics_block = None
    for key in ("metrics", "metrics_locales"):
        bloc = obj.get(key)
        if isinstance(bloc, dict):
            metrics_block = bloc
            break

    if metrics_block:
        metr_apr = metrics_block.get("apr_mean")
        if apr_mean is None and isinstance(metr_apr, (int, float)):
            apr_mean = float(metr_apr)

        metr_tvl = metrics_block.get("tvl_sum")
        if tvl_total is None and isinstance(metr_tvl, (int, float)):
            tvl_total = float(metr_tvl)

    # Message
    msg = obj.get("message") if isinstance(obj.get("message"), str) else None

    # Champs IA
    ai_ctx = obj.get("AI_context") if isinstance(obj.get("AI_context"), str) else None
    ai_conf = obj.get("AI_confidence")
    ai_conf_f: Optional[float] = float(ai_conf) if isinstance(ai_conf, (int, float)) else None

    ai_score_val = obj.get("AI_score")
    ai_score_f: Optional[float] = float(ai_score_val) if isinstance(ai_score_val, (int, float)) else None

    ai_features = obj.get("AI_features") if isinstance(obj.get("AI_features"), dict) else None
    ai_window = obj.get("AI_window") if isinstance(obj.get("AI_window"), dict) else None

    return SignalConsolide(
        timestamp=ts_str,
        context=context,
        apr_mean=apr_mean,
        tvl_total=tvl_total,
        message=msg,
        AI_context=ai_ctx,
        AI_confidence=ai_conf_f,
        AI_score=ai_score_f,
        AI_features=ai_features,
        AI_window=ai_window,
    )


def lire_signaux_consolides(limit: int = 50, include_ai: bool = True) -> list[SignalConsolide]:
    """Lit et retourne les derniers signaux consolidés pour DeFiPilot.

    La fonction :
    - lit les journaux JSONL pertinents,
    - combine les informations marché + AI si possible,
    - retourne une liste de signaux consolidés, ordonnés du plus récent au plus ancien,
    - tronque la liste à `limit` entrées au maximum.
    """
    chemin_signaux = Path("data/logs/journal_signaux.jsonl")
    chemin_ai = Path("data/logs/ai_evaluation.jsonl")

    max_lines = limit * 5 if limit > 0 else None

    signaux_bruts = _charger_jsonl_brut(chemin_signaux, max_lines=max_lines)
    signaux_ai = _charger_jsonl_brut(chemin_ai, max_lines=max_lines) if include_ai else []

    signaux: list[SignalConsolide] = []

    for brut in signaux_bruts:
        signaux.append(_build_signal_from_obj(brut))

    for brut_ai in signaux_ai:
        signaux.append(_build_signal_from_obj(brut_ai))

    def _score_tri(signal: SignalConsolide) -> float:
        ts = _parse_timestamp(signal.timestamp)
        if ts is not None:
            return ts.timestamp()
        return 0.0

    signaux_tries = sorted(signaux, key=_score_tri, reverse=True)
    if limit > 0:
        signaux_tries = signaux_tries[:limit]

    logger.info("%d signaux consolidés chargés (limit=%s)", len(signaux_tries), limit)
    return signaux_tries


def lire_dernier_signal_consolide(include_ai: bool = True) -> Optional[SignalConsolide]:
    """Raccourci pour obtenir le signal consolidé le plus récent."""
    signaux = lire_signaux_consolides(limit=1, include_ai=include_ai)
    if not signaux:
        return None
    return signaux[0]


# ---------------------------------------------------------------------------
# Boucle principale
# ---------------------------------------------------------------------------

class ControlPilot:
    """Moteur d'analyse chargé de produire des résumés observateurs."""

    def __init__(self, input_path: Path, output_path: Path, max_events: int = 100) -> None:
        self.input_path = input_path
        self.output_path = output_path
        self.max_events = max_events

    def _publish_exchange(
        self,
        events: list[dict[str, Any]],
        resume: ResumeGlobal,
        bus_path: Path = Path("exchange_bus.jsonl"),
    ) -> None:
        """Construit et publie un payload inter-bots minimal dans exchange_bus.jsonl.

        - context: pris depuis le dernier événement qui possède 'context'
        - ai_context/confidence: pris depuis la dernière ligne AI (tag ou ligne contenant AI_context)
        - metrics: pris depuis le dernier événement qui possède metrics(_locales)
        """
        context_val: Optional[str] = None
        metrics_val: Optional[dict[str, Any]] = None
        ai_ctx: Optional[str] = None
        ai_conf: Optional[float] = None

        for ev in reversed(events):
            if context_val is None:
                c = ev.get("context")
                if isinstance(c, str) and c:
                    context_val = c

            if metrics_val is None:
                m = ev.get("metrics_locales") or ev.get("metrics")
                if isinstance(m, dict):
                    metrics_val = m

            if ai_ctx is None or ai_conf is None:
                if isinstance(ev, dict) and ("AI_context" in ev or ev.get("tag") == "AI_context"):
                    ac = ev.get("AI_context")
                    if isinstance(ac, str) and ac:
                        ai_ctx = ac
                    cf = ev.get("AI_confidence")
                    if isinstance(cf, (int, float)):
                        ai_conf = float(cf)

            if context_val and metrics_val and (ai_ctx is not None) and (ai_conf is not None):
                break

        payload = build_payload(
            source="ControlPilot",
            version="V5.1",
            context=context_val or getattr(resume, "context", None),
            ai_context=ai_ctx,
            ai_confidence=ai_conf,
            metrics=metrics_val,
        )
        write_exchange_payload(bus_path, payload)

    def run_once(self) -> bool:
        """Effectue une analyse unique en produisant éventuellement un résumé."""
        evenements = charger_evenements(self.input_path, self.max_events)
        if not evenements:
            return False

        resume = calculer_resume(evenements)
        if resume is None:
            return False

        ecrire_resume(resume, self.output_path)
        # Publier sur le bus d'échange pour les autres bots
        self._publish_exchange(evenements, resume)
        return True

    def run_loop(self, interval_seconds: int) -> None:
        """Exécute continuellement l'analyse à intervalle régulier."""
        while True:
            try:
                self.run_once()
            except Exception as exc:  # pragma: no cover - protection runtime
                logger.exception("Erreur lors de l'exécution de ControlPilot : %s", exc)
            time.sleep(interval_seconds)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def creer_argument_parser() -> argparse.ArgumentParser:
    """Construit le parseur d'arguments pour l'exécution en ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Analyse les journaux de DeFiPilot pour produire un résumé global.",
    )
    parser.add_argument("--input", required=True, help="Chemin du journal DeFiPilot à analyser.")
    parser.add_argument(
        "--output",
        default="journal_control.jsonl",
        help="Chemin du journal de contrôle généré.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Intervalle en secondes entre deux analyses en mode boucle.",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=100,
        help="Nombre maximal d'événements utilisés pour la synthèse.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Exécute une seule analyse sans boucle continue.",
    )
    return parser


if __name__ == "__main__":
    parser = creer_argument_parser()
    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    control = ControlPilot(input_path=input_path, output_path=output_path, max_events=args.max_events)
    if args.once:
        control.run_once()
    else:
        control.run_loop(interval_seconds=args.interval)
