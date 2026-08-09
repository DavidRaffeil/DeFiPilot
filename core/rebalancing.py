# core/rebalancing.py — V6.0.0
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

def _valider_parametres(*args, **kwargs):
    pass


# =====================
# Constantes & matrices
# =====================

CATEGORIES: Tuple[str, str, str] = ("Prudent", "Modere", "Risque")

ALLOCATION_MATRIX: Dict[str, Dict[str, Dict[str, float]]] = {
    "prudent": {
        "defavorable": {"Prudent": 0.70, "Modere": 0.25, "Risque": 0.05},
        "neutre": {"Prudent": 0.60, "Modere": 0.30, "Risque": 0.10},
        "favorable": {"Prudent": 0.50, "Modere": 0.35, "Risque": 0.15},
    },
    "modere": {
        "defavorable": {"Prudent": 0.40, "Modere": 0.40, "Risque": 0.20},
        "neutre": {"Prudent": 0.30, "Modere": 0.40, "Risque": 0.30},
        "favorable": {"Prudent": 0.20, "Modere": 0.40, "Risque": 0.40},
    },
    "risque": {
        "defavorable": {"Prudent": 0.20, "Modere": 0.40, "Risque": 0.40},
        "neutre": {"Prudent": 0.10, "Modere": 0.30, "Risque": 0.60},
        "favorable": {"Prudent": 0.05, "Modere": 0.25, "Risque": 0.70},
    },
}

DEFAULT_PARAMS: Dict[str, Any] = {
    "max_shift_ratio": 0.3,
    "min_total_usd": 10.0,
    "max_actions": 20,
    "min_trade_amount_usd": 1.0,
    "min_profitability_ratio": 1.5,
    "estimated_gas_usd_per_action": 0.05,
    "slippage_pct": 0.5,
    "min_score_delta": 0.5,
}

# =====================
# Helpers de normalisation
# =====================


def _normaliser_profil(profil: str | None) -> str:
    if not isinstance(profil, str):
        return "modere"
    p = profil.strip().lower()
    return p if p in {"prudent", "modere", "risque"} else "modere"


def _normaliser_contexte(context_label: str | None) -> str:
    if not isinstance(context_label, str):
        return "neutre"
    c = context_label.strip().lower()
    return c if c in {"defavorable", "neutre", "favorable"} else "neutre"


def _normaliser_allocation(allocation: Dict[str, Any] | None) -> Dict[str, float]:
    allocation = allocation or {}
    resultats: Dict[str, float] = {}
    for categorie in CATEGORIES:
        try:
            resultats[categorie] = float(allocation.get(categorie, 0.0))
        except (TypeError, ValueError):
            resultats[categorie] = 0.0
    return resultats


def _renormaliser_poids(poids: Dict[str, float]) -> Dict[str, float]:
    valeurs = {cat: max(float(val), 0.0) for cat, val in poids.items()}
    total = sum(valeurs.values())
    if total <= 0.0:
        uniforme = 1.0 / len(CATEGORIES)
        return {cat: uniforme for cat in CATEGORIES}
    return {cat: valeurs.get(cat, 0.0) / total for cat in CATEGORIES}


# =====================
# Signaux & allocation
# =====================


def _resumer_signaux(signaux: List[Dict[str, Any]] | None) -> Dict[str, Any]:
    if not signaux:
        return {"ai_score_moyen": None, "nb_signaux": 0, "context_labels": []}
    scores = [
        s.get("ai_score")
        for s in signaux
        if isinstance(s, dict) and isinstance(s.get("ai_score"), (int, float))
    ]
    contexts = [
        s.get("context")
        for s in signaux
        if isinstance(s, dict) and isinstance(s.get("context"), str)
    ]
    return {
        "ai_score_moyen": (sum(scores) / len(scores)) if scores else None,
        "nb_signaux": len(signaux),
        "context_labels": contexts,
    }


def _determiner_total_usd(allocation: Dict[str, float], total_usd: float | None) -> float:
    if isinstance(total_usd, (int, float)):
        return float(total_usd)
    return float(sum(allocation.values()))


def _calculer_allocation_cible_usd(
    profil: str, contexte: str, total_usd: float, signaux_summary: Dict[str, Any]
) -> Dict[str, float]:
    base = ALLOCATION_MATRIX.get(profil, ALLOCATION_MATRIX["modere"]).get(contexte, {})
    poids = _renormaliser_poids(base)
    return {cat: poids.get(cat, 0.0) * total_usd for cat in CATEGORIES}


# =====================
# Arbitrage & Rentabilité Nette
# =====================


def _verifier_rentabilite_nette(
    actions: List[Dict[str, Any]],
    options: Dict[str, Any],
    total_usd: float,
    expected_apr_gain_pct: float = 0.02,
) -> Tuple[bool, Optional[str], float, float]:
    """Vérifie si les gains de rendement projetés dépassent les frais de Gas et de slippage."""
    if not actions:
        return True, None, 0.0, 0.0

    gas_per_action = float(options.get("estimated_gas_usd_per_action", DEFAULT_PARAMS["estimated_gas_usd_per_action"]))
    slippage_pct = float(options.get("slippage_pct", DEFAULT_PARAMS["slippage_pct"]))
    min_profitability_ratio = float(options.get("min_profitability_ratio", DEFAULT_PARAMS["min_profitability_ratio"]))

    nb_actions = len(actions)
    total_gas = nb_actions * gas_per_action
    total_slippage = sum(float(a.get("montant_usd", 0.0)) * (slippage_pct / 100.0) for a in actions)
    frais_totaux = total_gas + total_slippage

    volume_realloue = sum(float(a.get("montant_usd", 0.0)) for a in actions if a.get("action") == "augmenter")
    gain_projetes = volume_realloue * expected_apr_gain_pct

    if frais_totaux > 0 and gain_projetes < frais_totaux * min_profitability_ratio:
        motif = (
            f"Rentabilité nette insuffisante : frais estimatifs ({frais_totaux:.2f} USD) "
            f"supérieurs au gain net projeté ({gain_projetes:.2f} USD x ratio {min_profitability_ratio})."
        )
        return False, motif, frais_totaux, gain_projetes

    return True, None, frais_totaux, gain_projetes


# =====================
# Construction des actions
# =====================


def _construire_actions(
    allocation_actuelle: Dict[str, float],
    allocation_cible: Dict[str, float],
    contexte: str,
    options: Dict[str, Any],
    total_usd: float,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []
    plan_reduit = False
    motif_annulation = None

    max_shift_ratio = float(options.get("max_shift_ratio", DEFAULT_PARAMS["max_shift_ratio"]))
    min_trade_amount_usd = float(options.get("min_trade_amount_usd", DEFAULT_PARAMS["min_trade_amount_usd"]))
    plafond = max_shift_ratio * total_usd

    for cat in CATEGORIES:
        actuel = allocation_actuelle.get(cat, 0.0)
        cible = allocation_cible.get(cat, 0.0)
        delta = cible - actuel
        if abs(delta) <= 0:
            continue

        montant = abs(delta)
        # Filtrage par montant minimum de transaction
        if montant < min_trade_amount_usd:
            continue

        action = "augmenter" if delta > 0 else "reduire"
        actions.append({
            "categorie": cat,
            "action": action,
            "montant_usd": montant,
        })

    somme = sum(a["montant_usd"] for a in actions)
    if somme > plafond and plafond > 0:
        ratio = plafond / somme
        for a in actions:
            a["montant_usd"] *= ratio
        plan_reduit = True

    max_actions = int(options.get("max_actions", DEFAULT_PARAMS["max_actions"]))
    if len(actions) > max_actions:
        actions = actions[:max_actions]
        plan_reduit = True

    return actions, {"plan_reduit": plan_reduit, "motif_annulation": motif_annulation}


# =====================
# Normalisation actions V6.0
# =====================


def _preparer_actions_executables(
    *,
    actions_brutes: list[dict],
    contexte: str,
    pool_id: str | None,
) -> list[dict]:
    actions_normalisees: list[dict] = []

    if not isinstance(pool_id, str) or not pool_id.strip():
        return actions_normalisees

    for action in actions_brutes:
        if not isinstance(action, dict):
            continue

        categorie = action.get("categorie")
        if categorie not in CATEGORIES:
            continue

        montant_usd = action.get("montant_usd")
        if not isinstance(montant_usd, (int, float)) or montant_usd <= 0:
            continue

        action_type = action.get("action")
        if action_type == "augmenter":
            direction = "in"
        elif action_type == "reduire":
            direction = "out"
        else:
            continue

        actions_normalisees.append(
            {
                "type": "swap",
                "bucket": categorie,
                "pool_id": pool_id,
                "amount_usd": float(montant_usd),
                "params": {
                    "direction": direction,
                    "context": contexte,
                },
            }
        )

    return actions_normalisees


# =====================
# Journalisation
# =====================


def _journaliser_plan(plan: Dict[str, Any], journal_path: str | None) -> None:
    if not journal_path:
        return
    try:
        with open(journal_path, "a", encoding="utf-8") as journal:
            journal.write(json.dumps(plan, ensure_ascii=False))
            journal.write("\n")
    except OSError as exc:
        plan.setdefault("safety", {})["journal_error"] = str(exc)


# =====================
# API publique V6.0
# =====================


def generer_plan_reequilibrage_contexte(
    *,
    context: str,
    profil_effectif: str,
    allocation_actuelle_usd: dict[str, float],
    total_usd: float,
    signaux_normalises: list[dict],
    params_strategie: dict,
    run_id: str,
    journal_path: str,
) -> dict:
    _valider_parametres(
        context=context,
        profil_effectif=profil_effectif,
        allocation_actuelle_usd=allocation_actuelle_usd,
        total_usd=total_usd,
        signaux_normalises=signaux_normalises,
        params_strategie=params_strategie,
    )

    profil = _normaliser_profil(profil_effectif)
    contexte = _normaliser_contexte(context)
    allocation_actuelle = _normaliser_allocation(allocation_actuelle_usd)
    total = _determiner_total_usd(allocation_actuelle, total_usd)

    limites = params_strategie.get("limites", {})
    rebalance_cfg = params_strategie.get("rebalance", {})
    if isinstance(rebalance_cfg, dict):
        options = {**DEFAULT_PARAMS, **limites, **rebalance_cfg}
    else:
        options = {**DEFAULT_PARAMS, **limites}

    mode_execution = params_strategie.get("mode_execution", "simulation")
    mode_safety = "reel" if isinstance(mode_execution, str) and mode_execution.lower() == "reel" else "simulation"

    safety = {
        "max_shift_ratio_applique": float(options.get("max_shift_ratio", DEFAULT_PARAMS["max_shift_ratio"])),
        "plan_reduit": False,
        "motif_annulation": None,
        "mode": mode_safety,
    }

    signaux_summary = _resumer_signaux(signaux_normalises)
    plan: Dict[str, Any] = {
        "tag": "[SIMULATION / DRY-RUN]" if mode_safety == "simulation" else "[REEL]",
        "context": contexte,
        "profil": profil,
        "run_id": run_id,
        "total_usd": total,
        "allocation_actuelle_usd": allocation_actuelle,
        "allocation_cible_usd": {cat: 0.0 for cat in CATEGORIES},
        "actions": [],
        "safety": safety,
        "signals_summary": signaux_summary,
        "journal_path": journal_path,
    }

    mode_global = params_strategie.get("mode_global")
    exits = params_strategie.get("exits", {})
    if mode_global == "EXIT" or (isinstance(exits, dict) and exits.get("global") is True):
        safety["motif_annulation"] = "EXIT global actif"
        _journaliser_plan(plan, journal_path)
        return plan

    if isinstance(rebalance_cfg, dict):
        if rebalance_cfg.get("enabled") is False:
            safety["motif_annulation"] = "Rééquilibrage désactivé dans la stratégie (rebalance.enabled = False)."
            _journaliser_plan(plan, journal_path)
            return plan

    if total <= 0.0:
        safety["motif_annulation"] = "Total du portefeuille non valide."
        _journaliser_plan(plan, journal_path)
        return plan

    if total < float(options.get("min_total_usd", DEFAULT_PARAMS["min_total_usd"])):
        safety["motif_annulation"] = "Portefeuille trop faible pour un rééquilibrage sécurisé."
        _journaliser_plan(plan, journal_path)
        return plan

    # Arbitrage par écart de score minimum (min_score_delta)
    min_score_delta = options.get("min_score_delta")
    score_delta = params_strategie.get("score_delta")
    if isinstance(min_score_delta, (int, float)) and isinstance(score_delta, (int, float)):
        if float(score_delta) < float(min_score_delta):
            safety["motif_annulation"] = (
                f"Écart de score ({float(score_delta):.2f}) inférieur au seuil d'arbitrage minimum ({float(min_score_delta):.2f})."
            )
            _journaliser_plan(plan, journal_path)
            return plan

    allocation_cible = _calculer_allocation_cible_usd(profil, contexte, total, signaux_summary)
    plan["allocation_cible_usd"] = allocation_cible

    # Vérification du seuil de rééquilibrage threshold_pct
    if isinstance(rebalance_cfg, dict) and "threshold_pct" in rebalance_cfg:
        threshold_pct = float(rebalance_cfg.get("threshold_pct", 0.05))
        max_delta_pct = max(
            abs((allocation_cible.get(cat, 0.0) - allocation_actuelle.get(cat, 0.0)) / total)
            for cat in CATEGORIES
        ) if total > 0 else 0.0

        if max_delta_pct < threshold_pct:
            safety["motif_annulation"] = (
                f"Écarts d'allocation ({max_delta_pct*100:.2f}%) inférieurs au seuil configuré ({threshold_pct*100:.2f}%)."
            )
            _journaliser_plan(plan, journal_path)
            return plan

    actions, meta_safety = _construire_actions(
        allocation_actuelle, allocation_cible, contexte, options, total
    )
    safety["plan_reduit"] = meta_safety.get("plan_reduit", False)
    if meta_safety.get("motif_annulation"):
        safety["motif_annulation"] = meta_safety.get("motif_annulation")

    # Arbitrage par rentabilité nette (frais de gas et slippage vs gain projeté)
    est_rentable, motif_rentabilite, frais_totaux, gain_projetes = _verifier_rentabilite_nette(actions, options, total)
    if not est_rentable:
        safety["motif_annulation"] = motif_rentabilite
        plan["actions"] = []
        _journaliser_plan(plan, journal_path)
        return plan

    plan["actions"] = _preparer_actions_executables(
        actions_brutes=actions,
        contexte=contexte,
        pool_id=params_strategie.get("pool_id"),
    )

    if contexte == "defavorable":
        if any(a.get("categorie") == "Risque" and a.get("action") == "augmenter" for a in actions):
            safety["motif_annulation"] = (
                "Protection risque : aucune augmentation de la poche Risque en contexte défavorable."
            )
            plan["actions"] = []

    _journaliser_plan(plan, journal_path)
    return plan