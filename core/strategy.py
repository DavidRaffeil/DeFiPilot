# core/strategy.py – V4.0.3
"""Outils de stratégie et allocation dynamique basés sur le contexte de marché."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from core.market_context import evaluer_contexte_marche, diagnostiquer_contexte

__all__ = [
    "adapter_allocations_selon_marche",
    "determiner_allocation_adaptative",
]


def adapter_allocations_selon_marche(context_marche: str, chemin_config: str = "core/allocations.json") -> Dict[str, float]:
    """Charge une allocation cible en fonction d'un contexte marché.

    Cette fonction lit un fichier JSON contenant les allocations par contexte et
    retourne le dictionnaire d'allocation pour le contexte demandé. Si le fichier
    n'existe pas ou que le contexte n'est pas défini, un dictionnaire vide est
    renvoyé.
    """

    if not isinstance(context_marche, str):
        return {}

    chemin = Path(chemin_config)
    if not chemin.is_file():
        return {}

    try:
        with chemin.open("r", encoding="utf-8") as fichier:
            configuration = json.load(fichier)
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(configuration, dict):
        return {}

    contexte = context_marche.strip().lower()

    # Supporte deux formats:
    # 1) Top-level direct: {"favorable": {...}, "neutre": {...}, ...}
    # 2) Avec clé "allocations": {"allocations": {"favorable": {...}, ...}}
    allocations_brutes = configuration.get("allocations") if "allocations" in configuration else configuration
    if not isinstance(allocations_brutes, dict):
        return {}

    allocations_normalisees: Dict[str, Dict[str, float]] = {}
    for cle_contexte, allocation in allocations_brutes.items():
        if not isinstance(cle_contexte, str) or not isinstance(allocation, dict):
            continue
        try:
            allocations_normalisees[cle_contexte.strip().lower()] = {
                str(nom).strip(): float(valeur)
                for nom, valeur in allocation.items()
            }
        except (TypeError, ValueError):
            continue

    allocation_cible = allocations_normalisees.get(contexte)
    if allocation_cible:
        return allocation_cible

    return {}


def determiner_allocation_adaptative(
    metrics: Dict[str, Any],
    chemin_config: str = "core/allocations.json",
    diagnostic: bool = False,
) -> Dict[str, Any]:
    """Détermine l'allocation adaptée selon les métriques de marché fournies."""

    def _erreur(message: str) -> Dict[str, Any]:
        return {"contexte": "inconnu", "allocation_cible": {}, "diagnostic": {"erreur": message}}

    metrics = metrics or {}

    try:
        contexte = evaluer_contexte_marche(metrics)
    except Exception as exc:  # pragma: no cover - garde-fou
        return _erreur(f"Évaluation du contexte impossible: {exc}")

    if contexte not in {"favorable", "neutre", "defavorable"}:
        return _erreur(f"Contexte de marché inattendu: {contexte}")

    try:
        allocation = adapter_allocations_selon_marche(contexte, chemin_config=chemin_config)
    except Exception as exc:  # pragma: no cover - robustesse
        return _erreur(f"Lecture des allocations impossible: {exc}")

    if not allocation:
        return _erreur(f"Allocation introuvable pour le contexte '{contexte}'")

    try:
        total = sum(float(valeur) for valeur in allocation.values())
    except (TypeError, ValueError) as exc:
        return _erreur(f"Allocation invalide pour le contexte '{contexte}': {exc}")

    if not 0.99 <= total <= 1.01:
        print("[WARN] Somme des allocations en dehors de la tolérance.")
        return _erreur(
            f"Somme des allocations incohérente ({total:.4f}) pour le contexte '{contexte}'"
        )

    resultat: Dict[str, Any] = {
        "contexte": contexte,
        "allocation_cible": allocation,
    }

    if diagnostic:
        try:
            diag = diagnostiquer_contexte(metrics)
        except Exception as exc:  # pragma: no cover - robustesse
            diag = {"erreur_diagnostic": str(exc)}
        resultat["diagnostic"] = diag

    return resultat


if __name__ == "__main__":
    # Scénarios de test alignés sur core.market_context
    scenarios = {
    "bull": {
        "apr_mean_change_24h": 0.06,
        "tvl_change_24h": 0.03,
        "volume_tvl_ratio": 0.25,
        "volatilite_index": 0.14,
    },
    "flat": {
        "apr_mean_change_24h": 0.00,
        "tvl_change_24h": 0.00,
        "volume_tvl_ratio": 0.10,
        "volatilite_index": 0.05,
    },
    "risk_off": {
        "apr_mean_change_24h": -0.04,
        "tvl_change_24h": -0.05,
        "volume_tvl_ratio": 0.05,
        "volatilite_index": 0.60,
    },
}


    for nom, metriques in scenarios.items():
        resultat = determiner_allocation_adaptative(metriques, diagnostic=True)
        score = resultat.get("diagnostic", {}).get("score")
        print(
            f"{nom}: contexte={resultat.get('contexte')}, allocation_cible={resultat.get('allocation_cible')}, score={score}"
        )
