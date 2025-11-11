# controlpilot_cli.py — V4.8.0
"""Interface en ligne de commande pour lancer une analyse ControlPilot."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from control.data_collector import (
    charger_evenements_signaux,
    extraire_indicateurs_de_base,
)
from control.risk_signals import calculer_signaux_risque, resumer_niveau_risque


def main(argv: Iterable[str] | None = None) -> int:
    """Point d'entrée principal de l'interface en ligne de commande."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="Analyse les signaux et produit un résumé des niveaux de risque.",
    )
    parser.add_argument(
        "--journal-signaux",
        default="journal_signaux.jsonl",
        help="Chemin vers le journal JSONL contenant les signaux bruts.",
    )
    parser.add_argument(
        "--journal-risques",
        default="journal_risques.jsonl",
        help="Chemin vers le journal JSONL où consigner les signaux de risque.",
    )

    argv_list = list(argv) if argv is not None else list(sys.argv[1:])
    args = parser.parse_args(argv_list)

    chemin_signaux = Path(args.journal_signaux)
    chemin_risques = Path(args.journal_risques)

    evenements = charger_evenements_signaux(chemin_signaux)
    indicateurs = extraire_indicateurs_de_base(evenements)
    signaux = list(calculer_signaux_risque(indicateurs))
    resume = resumer_niveau_risque(signaux)

    def _ecrire_signaux_dans_journal(
        chemin: Path,
        signaux: Iterable[dict[str, Any]],
        source: str = "controlpilot",
    ) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        run_id = f"{source}-{ts}"

        try:
            chemin.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logging.error(
                "Impossible de préparer le répertoire du journal des risques %s: %s",
                chemin,
                exc,
            )
            return

        try:
            with chemin.open("a", encoding="utf-8") as flux:
                for signal in signaux:
                    if not isinstance(signal, dict):
                        continue
                    entree = {
                        "ts": ts,
                        "timestamp": ts,
                        "source": source,
                        "run_id": run_id,
                        "niveau": signal.get("niveau"),
                        "type": signal.get("type"),
                        "motifs": signal.get("motifs") or [],
                        "details": signal.get("details") or {},
                    }
                    json.dump(entree, flux, ensure_ascii=False)
                    flux.write("\n")
        except OSError as exc:
            logging.error(
                "Impossible d'écrire dans le journal des risques %s: %s", chemin, exc
            )

    _ecrire_signaux_dans_journal(chemin_risques, signaux)

    niveau_global = "INCONNU"
    nb_signaux = len(signaux)
    repartition: dict[str, Any] = {}
    if isinstance(resume, dict):
        niveau_global = str(resume.get("niveau_global", niveau_global))
        try:
            nb_signaux = int(resume.get("nb_signaux", nb_signaux))
        except (TypeError, ValueError):
            nb_signaux = len(signaux)
        repartition_candidate = resume.get("repartition_niveaux", repartition)
        if isinstance(repartition_candidate, dict):
            repartition = repartition_candidate

    print("=== ControlPilot V4.8 — Résumé du risque ===")
    print(f"Niveau global : {niveau_global}")
    print(f"Nombre de signaux : {nb_signaux}")
    print(f"Répartition : {repartition}")

    if niveau_global == "RISQUE":
        return 2
    if niveau_global == "A_SURVEILLER":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())