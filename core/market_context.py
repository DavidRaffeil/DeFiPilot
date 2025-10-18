# core/market_context.py – V4.0.3
"""Outils de diagnostic du contexte de marché."""
__all__ = ["evaluer_contexte_marche", "diagnostiquer_contexte"]
from typing import Dict


def evaluer_contexte_marche(metrics: dict) -> str:
    """Détermine un régime de marché simplifié à partir des métriques fournies."""
    trend = (metrics.get("trend") or "").lower()
    vol = (metrics.get("vol") or "").lower()
    risk = (metrics.get("risk") or "").lower()

    if trend == "up" and risk in {"on", "agressif"} and vol not in {"élevée", "elevee", "haute"}:
        return "bull"
    if trend == "down" or risk in {"off", "faible"} or vol in {"élevée", "elevee", "haute"}:
        return "risk_off"
    return "flat"


def diagnostiquer_contexte(metrics: Dict) -> Dict[str, object]:
    """Fournit un diagnostic structuré à partir des métriques de marché."""
    regime = evaluer_contexte_marche(metrics)
    mapping = {
        "bull": {
            "contexte": "favorable",
            "allocation": {"risque": 0.6, "modéré": 0.3, "prudent": 0.1},
            "score": 0.12,
        },
        "flat": {
            "contexte": "neutre",
            "allocation": {"risque": 0.4, "modéré": 0.4, "prudent": 0.2},
            "score": 0.0,
        },
        "risk_off": {
            "contexte": "defavorable",
            "allocation": {"risque": 0.2, "modéré": 0.3, "prudent": 0.5},
            "score": -1.28,
        },
    }

    if regime not in mapping:
        raise ValueError(f"Régime de marché inconnu: {regime}")

    contexte = mapping[regime]["contexte"]
    allocation = mapping[regime]["allocation"]
    score = mapping[regime]["score"]

    total = sum(allocation.values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError("Les pondérations d'allocation ne totalisent pas 100 %.")

    resume = (
        f"Contexte {contexte} (score {score:+.2f}). "
        f"Cible: prudent {allocation['prudent'] * 100:.0f} %, "
        f"modéré {allocation['modéré'] * 100:.0f} %, "
        f"risqué {allocation['risque'] * 100:.0f} %."
    )

    return {
        "contexte": contexte,
        "score": score,
        "allocation_cible": allocation,
        "resume": resume,
    }


if __name__ == "__main__":
    scenarios = {
        "bull": {"trend": "up", "vol": "normale", "risk": "on"},
        "flat": {"trend": "flat", "vol": "normale", "risk": "neutre"},
        "risk_off": {"trend": "down", "vol": "élevée", "risk": "off"},
    }
    for nom, metriques in scenarios.items():
        print(diagnostiquer_contexte(metriques))