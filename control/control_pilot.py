# control/control_pilot.py — V4.4.0
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import argparse
import json
import time

"""Module d'observation produisant un résumé global des journaux DeFiPilot.
Le mode "once" lance une seule analyse tandis que le mode "boucle" répète
l'analyse à intervalle régulier.
Ce module agit uniquement comme observateur sans modifier les stratégies."""


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


def charger_evenements(journal_path: Path, max_events: int) -> list[dict[str, Any]]:
    """Charge les événements JSON les plus récents du journal fourni."""

    if not journal_path.exists():
        return []
    try:
        with journal_path.open("r", encoding="utf-8") as flux:
            lignes = flux.readlines()
    except OSError:
        return []
    if max_events > 0:
        lignes = lignes[-max_events:]
    evenements: list[dict[str, Any]] = []
    for ligne in lignes:
        contenu = ligne.strip()
        if not contenu:
            continue
        try:
            evenement = json.loads(contenu)
        except json.JSONDecodeError:
            continue
        if isinstance(evenement, dict):
            evenements.append(evenement)
    return evenements


def calculer_resume(evenements: list[dict[str, Any]]) -> Optional[ResumeGlobal]:
    """Synthétise les événements fournis en un résumé global."""

    if not evenements:
        return None
    occurrences: dict[str, int] = {}
    for evenement in evenements:
        contexte = evenement.get("context")
        if isinstance(contexte, str) and contexte:
            occurrences[contexte] = occurrences.get(contexte, 0) + 1
    if occurrences:
        contexte_dominant = max(occurrences.items(), key=lambda item: item[1])[0]
    else:
        contexte_dominant = "inconnu"
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
    if apr_valeurs:
        apr_moyen = sum(apr_valeurs) / len(apr_valeurs)
    else:
        apr_moyen = 0.0
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


def ecrire_resume(resume: ResumeGlobal, output_path: Path) -> None:
    """Écrit le résumé global dans un fichier JSONL de contrôle."""

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return
    try:
        with output_path.open("a", encoding="utf-8") as flux:
            flux.write(json.dumps(resume.to_dict(), ensure_ascii=False))
            flux.write("\n")
    except OSError:
        return


class ControlPilot:
    """Moteur d'analyse chargée de produire des résumés observateurs."""

    def __init__(self, input_path: Path, output_path: Path, max_events: int = 100) -> None:
        self.input_path = input_path
        self.output_path = output_path
        self.max_events = max_events

    def run_once(self) -> bool:
        """Effectue une analyse unique en produisant éventuellement un résumé."""

        evenements = charger_evenements(self.input_path, self.max_events)
        if not evenements:
            return False
        resume = calculer_resume(evenements)
        if resume is None:
            return False
        ecrire_resume(resume, self.output_path)
        return True

    def run_loop(self, interval_seconds: int) -> None:
        """Exécute continuellement l'analyse à intervalle régulier."""

        while True:
            self.run_once()
            time.sleep(interval_seconds)


def creer_argument_parser() -> argparse.ArgumentParser:
    """Construit le parseur d'arguments pour l'exécution en ligne de commande."""

    parser = argparse.ArgumentParser(
        description="Analyse les journaux de DeFiPilot pour produire un résumé global."
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