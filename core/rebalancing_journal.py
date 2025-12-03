# core/rebalancing_journal.py – V5.2.0
from __future__ import annotations

from typing import Any, Mapping, Dict
import json
from datetime import datetime
import os
import logging

from core.rebalancing_simulator import RebalancePlan

logger = logging.getLogger(__name__)


def _is_json_compatible(value: Any) -> bool:
    """Vérifie si une valeur est JSON-compatibles (types simples)."""
    return isinstance(value, (str, int, float, bool)) or value is None


def construire_enregistrement_reequilibrage(
    plan: RebalancePlan,
    snapshot: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Construit un enregistrement JSON sérialisable décrivant un plan de rééquilibrage.

    - plan : RebalancePlan produit par core.rebalancing_simulator ou
      core.rebalancing_engine.
    - snapshot : snapshot brut optionnel (dernier snapshot de stratégie, tel que
      retourné par core.strategy_snapshot.lire_dernier_snapshot).

    L'enregistrement contient au minimum :
    - "timestamp" : ISO 8601 (UTC) via datetime.utcnow().isoformat() + "Z"
    - "contexte" : plan["contexte"]
    - "total_a_deplacer_usd" : plan["total_a_deplacer_usd"]
    - "actions" : plan["actions"] (liste de dicts from_profil/to_profil/montant_usd)

    Les champs issus du snapshot peuvent être ajoutés si disponibles.
    """

    enregistrement: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "contexte": plan.get("contexte"),
        "total_a_deplacer_usd": plan.get("total_a_deplacer_usd"),
        "actions": plan.get("actions", []),
    }

    if isinstance(snapshot, Mapping):
        run_id = snapshot.get("run_id")
        version = snapshot.get("version")
        if run_id is not None:
            enregistrement["snapshot_run_id"] = run_id
        if version is not None:
            enregistrement["snapshot_version"] = version

        extras: Dict[str, Any] = {}
        for cle, valeur in snapshot.items():
            if cle in {"run_id", "version"}:
                continue
            if _is_json_compatible(valeur):
                extras[cle] = valeur
        if extras:
            enregistrement["snapshot_extra"] = extras

    return enregistrement


def journaliser_plan_reequilibrage(
    plan: RebalancePlan,
    snapshot: Mapping[str, Any] | None = None,
    chemin_fichier: str = "data/journal_reequilibrage.jsonl",
) -> None:
    """
    Ajoute une ligne JSONL dans le fichier de journalisation des rééquilibrages.

    - plan : RebalancePlan à journaliser.
    - snapshot : snapshot optionnel associé à ce plan.
    - chemin_fichier : chemin vers le fichier JSONL.

    La fonction construit un enregistrement, s'assure que le dossier existe,
    écrit la ligne JSON et loggue le résultat. En cas d'erreur, un warning est
    produit sans propagation de l'exception.
    """

    enregistrement = construire_enregistrement_reequilibrage(plan, snapshot)

    repertoire = os.path.dirname(chemin_fichier)
    try:
        if repertoire:
            os.makedirs(repertoire, exist_ok=True)

        with open(chemin_fichier, "a", encoding="utf-8") as fichier:
            ligne = json.dumps(enregistrement, ensure_ascii=False)
            fichier.write(ligne + "\n")

        logger.debug("Plan de rééquilibrage journalisé dans %s", chemin_fichier)
    except OSError as exc:
        logger.warning("Échec de journalisation du plan de rééquilibrage: %s", exc)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # Plan minimal de test
    plan_test: RebalancePlan = {
        "contexte": "neutre",
        "total_a_deplacer_usd": 100.0,
        "actions": [
            {
                "from_profil": "Prudent",
                "to_profil": "Modere",
                "montant_usd": 100.0,
            }
        ],
    }

    # Snapshot minimal de test
    snapshot_test = {
        "run_id": "test-run-123",
        "version": "V5.2.0",
    }

    journaliser_plan_reequilibrage(plan_test, snapshot_test)
    print(
        "Entrée de journal de rééquilibrage écrite (voir data/journal_reequilibrage.jsonl)."
    )


__all__ = [
    "construire_enregistrement_reequilibrage",
    "journaliser_plan_reequilibrage",
]