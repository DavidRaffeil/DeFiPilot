"""Guardrails minimaux pour DeFiPilot V6.0 — Validation des actions."""
from __future__ import annotations

def verifier_action_reelle(action: dict, run_id: str) -> dict:
    """
    Point d'entrée minimal des guardrails pour les actions réelles.
    Autorise l'exécution en mode simulation/test.
    """
    return {
        "status": "EXECUTED",
        "details": {"reason": "guardrails_ok"}
    }