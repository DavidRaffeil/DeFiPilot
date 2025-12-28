# core/risk_analysis.py — V5.5.0
"""Analyse de risque pour DeFiPilot V5.5 en mode global.

Ce module traduit le mode global "mode_v5_5" en une décision de risque
structurée, exploitable par la stratégie et le rééquilibrage. Toutes les
informations produites sont destinées à un usage en dry-run : aucune action
métier réelle n'est exécutée ici.
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping

# Mappage des modes vers les niveaux de risque standards.
_MODE_TO_RISK = {
    "NORMAL": "LOW",
    "TENSION": "MEDIUM",
    "ALERTE": "HIGH",
    "CRISE": "CRITICAL",
    "PANIC": "CRITICAL",
}

# Paramètres par défaut pour chaque mode : sécurité prioritaire.
_DEFAULT_RULES: dict[str, MutableMapping[str, Any]] = {
    "NORMAL": {
        "allow_new_positions": True,
        "allow_rebalance": True,
        "allow_exit": True,
        "prefer_stables": False,
    },
    "TENSION": {
        "allow_new_positions": True,
        "allow_rebalance": True,
        "allow_exit": True,
        "prefer_stables": False,
    },
    "ALERTE": {
        "allow_new_positions": False,
        "allow_rebalance": True,
        "allow_exit": True,
        "prefer_stables": False,
    },
    "CRISE": {
        "allow_new_positions": False,
        "allow_rebalance": True,
        "allow_exit": True,
        "prefer_stables": False,
    },
    "PANIC": {
        "allow_new_positions": False,
        "allow_rebalance": False,
        "allow_exit": True,
        "prefer_stables": True,
    },
}


def _safe_get(mapping: Mapping[str, Any] | None, *keys: str) -> Any:
    """Récupère une valeur imbriquée en best-effort.

    Si une clé manque ou si la structure n'est pas indexable, None est retourné.
    """

    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)  # type: ignore[assignment]
    return current


def _normalize_mode(raw_mode: Any) -> str:
    """Normalise un mode brut en mode connu.

    Si le mode n'est pas reconnu, ``NORMAL`` est utilisé comme repli sûr.
    """

    if isinstance(raw_mode, str):
        candidate = raw_mode.strip().upper()
        if candidate in _MODE_TO_RISK:
            return candidate
    return "NORMAL"


def _apply_mode_policy(result: dict[str, Any], mode_policy: Any, reasons: list[str]) -> None:
    """Applique une éventuelle politique spécifique au mode.

    Les clés reconnues sont appliquées en best-effort pour ajuster les
    autorisations ou préférences calculées par défaut.
    """

    if not isinstance(mode_policy, Mapping):
        return

    for key in ("allow_new_positions", "allow_rebalance", "allow_exit", "prefer_stables"):
        if key in mode_policy:
            result[key] = bool(mode_policy[key])
            reasons.append(f"Override config : {key}={result[key]} d'après modes[{result['mode']}].")



def analyser_risque_v5_5(decision: Any, strategy_cfg: Mapping[str, Any] | None) -> dict[str, Any]:
    """Analyse la décision de risque en V5.5.

    Args:
        decision: Objet contenant ``mode_v5_5`` (optionnel).
        strategy_cfg: Configuration de stratégie (peut être None).

    Returns:
        Un dictionnaire détaillant le niveau de risque et les actions permises.
    """

    reasons: list[str] = []
    raw_mode = getattr(decision, "mode_v5_5", "NORMAL")
    mode = _normalize_mode(raw_mode)
    if mode != raw_mode:
        reasons.append("Mode non reconnu, repli sur NORMAL.")

    risk_level = _MODE_TO_RISK.get(mode, "LOW")

    # Base sécurisée.
    base = dict(_DEFAULT_RULES.get(mode, _DEFAULT_RULES["NORMAL"]))
    reasons.append(f"Règles par défaut appliquées pour le mode {mode}.")

    # Lecture configuration globale dry-run.
    dry_run_cfg = _safe_get(strategy_cfg, "global", "dry_run_only")
    dry_run_only = bool(dry_run_cfg) if dry_run_cfg is not None else True
    if dry_run_cfg is not None:
        reasons.append(f"Paramètre global dry_run_only détecté: {dry_run_only}.")
    else:
        reasons.append("Paramètre global dry_run_only absent, défaut True (sécurité).")

    # Politique spécifique au mode.
    mode_policy = _safe_get(strategy_cfg, "modes", mode, "policy")
    _apply_mode_policy(base, mode_policy, reasons)

    # Lectures des politiques de portefeuille.
    target_allocations = _safe_get(strategy_cfg, "portfolio_actions", "target_allocations", mode)
    if target_allocations is not None:
        reasons.append("Cible d'allocation spécifique au mode chargée.")

    rebalance_policy = _safe_get(strategy_cfg, "portfolio_actions", "rebalance_policy")
    if rebalance_policy is not None:
        reasons.append("Politique de rééquilibrage détectée.")

    exit_policy = _safe_get(strategy_cfg, "portfolio_actions", "exit_policy")
    if exit_policy is not None:
        reasons.append("Politique de sortie détectée.")

    hard_stops = _safe_get(strategy_cfg, "safety", "hard_stops")
    if hard_stops is not None:
        reasons.append("Seuils de sécurité (hard stops) détectés.")

    result = {
        "mode": mode,
        "risk_level": risk_level,
        "allow_new_positions": bool(base.get("allow_new_positions")),
        "allow_rebalance": bool(base.get("allow_rebalance")),
        "allow_exit": bool(base.get("allow_exit")),
        "prefer_stables": bool(base.get("prefer_stables")),
        "dry_run_only": dry_run_only,
        "target_allocations": target_allocations if isinstance(target_allocations, Mapping) else None,
        "rebalance_policy": rebalance_policy if isinstance(rebalance_policy, Mapping) else None,
        "exit_policy": exit_policy if isinstance(exit_policy, Mapping) else None,
        "hard_stops": hard_stops if isinstance(hard_stops, Mapping) else None,
        "reasons": reasons,
    }

    return result


__all__ = ["analyser_risque_v5_5"]