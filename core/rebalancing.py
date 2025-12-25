from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

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

DEFAULT_PARAMS: Dict[str, float | int | bool] = {
    "min_rebal_usd": 20.0,
    "max_shift_ratio": 0.3,
    "min_total_usd": 50.0,
    "journaliser_plan": True,
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _normaliser_profil(profil: str) -> str:
    p = (profil or "").strip().lower()
    if p in ("prudent", "prudente"):
        return "prudent"
    if p in ("modere", "modéré", "moderee", "modérée"):
        return "modere"
    if p in ("risque", "risqué", "agressif", "agressive"):
        return "risque"
    return "modere"


def _normaliser_contexte(contexte: str) -> str:
    c = (contexte or "").strip().lower()
    if c in ("defavorable", "défavorable", "bear", "risk_off", "crise"):
        return "defavorable"
    if c in ("favorable", "haussier", "bull", "risk_on"):
        return "favorable"
    return "neutre"


def _normaliser_allocation(allocation_actuelle_usd: Mapping[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {cat: 0.0 for cat in CATEGORIES}
    for cat in CATEGORIES:
        out[cat] = _safe_float(allocation_actuelle_usd.get(cat), 0.0)
    return out


def _total_usd(allocation_actuelle_usd: Mapping[str, Any]) -> float:
    alloc = _normaliser_allocation(allocation_actuelle_usd)
    return sum(alloc.values())


def _calculer_allocation_cible_usd(
    profil: str,
    contexte: str,
    total_usd: float,
    signaux_summary: Mapping[str, Any] | None,
) -> Dict[str, float]:
    p = _normaliser_profil(profil)
    c = _normaliser_contexte(contexte)

    ratios = ALLOCATION_MATRIX.get(p, ALLOCATION_MATRIX["modere"]).get(
        c, ALLOCATION_MATRIX["modere"]["neutre"]
    )

    allocation: Dict[str, float] = {cat: 0.0 for cat in CATEGORIES}
    for cat in CATEGORIES:
        allocation[cat] = float(ratios.get(cat, 0.0)) * float(total_usd)

    if signaux_summary and isinstance(signaux_summary, Mapping):
        ai_score = signaux_summary.get("ai_score_moyen")
        ai_score_f = _safe_float(ai_score, default=float("nan"))
        if ai_score_f == ai_score_f:
            tilt = 0.0
            if ai_score_f >= 0.70:
                tilt = 0.05
            elif ai_score_f <= 0.30:
                tilt = -0.05
            if tilt != 0.0:
                delta = tilt * float(total_usd)
                allocation["Risque"] = max(0.0, allocation["Risque"] + delta)
                allocation["Prudent"] = max(0.0, allocation["Prudent"] - delta)

    return allocation


def _construire_actions(
    allocation_actuelle: Dict[str, float],
    allocation_cible: Dict[str, float],
    contexte: str,
    options: Mapping[str, Any],
    total_usd: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    min_rebal_usd = _safe_float(options.get("min_rebal_usd"), float(DEFAULT_PARAMS["min_rebal_usd"]))
    max_shift_ratio = _safe_float(options.get("max_shift_ratio"), float(DEFAULT_PARAMS["max_shift_ratio"]))

    safety: Dict[str, Any] = {"plan_reduit": False, "motif_annulation": None}
    actions: List[Dict[str, Any]] = []

    deltas: Dict[str, float] = {}
    for cat in CATEGORIES:
        deltas[cat] = float(allocation_cible.get(cat, 0.0)) - float(allocation_actuelle.get(cat, 0.0))

    candidats: List[tuple[str, float]] = []
    for cat, delta in deltas.items():
        if abs(delta) >= min_rebal_usd:
            candidats.append((cat, delta))

    if not candidats:
        return actions, safety

    total_mouvements = sum(abs(delta) for _, delta in candidats)
    plafond = max_shift_ratio * float(total_usd) if total_usd > 0 else 0.0

    if plafond > 0 and total_mouvements > plafond:
        ratio = plafond / total_mouvements
        safety["plan_reduit"] = True
        for cat, delta in candidats:
            delta *= ratio
            actions.append(
                {
                    "categorie": cat,
                    "action": "augmenter" if delta > 0 else "reduire",
                    "montant_usd": round(abs(delta), 6),
                    "delta_usd": round(delta, 6),
                }
            )
    else:
        for cat, delta in candidats:
            actions.append(
                {
                    "categorie": cat,
                    "action": "augmenter" if delta > 0 else "reduire",
                    "montant_usd": round(abs(delta), 6),
                    "delta_usd": round(delta, 6),
                }
            )

    if _normaliser_contexte(contexte) == "defavorable":
        for action in actions:
            if action["categorie"] == "Risque" and action["action"] == "augmenter":
                safety["motif_annulation"] = "Protection risque : aucune augmentation de la poche Risque en contexte défavorable."
                return [], safety

    return actions, safety


def _journaliser_plan(plan: Mapping[str, Any], journal_path: str | Path | None) -> None:
    if not journal_path:
        return
    try:
        path = Path(journal_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(plan, ensure_ascii=False) + chr(10))
    except Exception:
        return


def generer_plan_reequilibrage_contexte(
    profil: str | None = None,
    contexte: str | None = None,
    allocation_actuelle_usd: Mapping[str, Any] | None = None,
    signaux_summary: Mapping[str, Any] | None = None,
    options: Mapping[str, Any] | None = None,
    journal_path: str | Path | None = None,
    run_id: str | None = None,
    dry_run_only: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    opts: Dict[str, Any] = dict(DEFAULT_PARAMS)
    if options:
        opts.update(dict(options))

    profil_actif = kwargs.get("profil_actif") or kwargs.get("profil_effectif")
    if (not isinstance(profil, str)) or (not profil.strip()):
        if isinstance(profil_actif, str) and profil_actif.strip():
            profil = profil_actif
        else:
            profil = "modere"

    context_label = kwargs.get("context_label")
    context = kwargs.get("context")
    contexte_effectif = contexte
    if (not isinstance(contexte_effectif, str)) or (not contexte_effectif.strip()):
        for candidate in (context_label, context):
            if isinstance(candidate, str) and candidate.strip():
                contexte_effectif = candidate
                break
    contexte_effectif = _normaliser_contexte(contexte_effectif or "neutre")

    allocation_actuelle_usd = allocation_actuelle_usd or {}
    allocation_actuelle = _normaliser_allocation(allocation_actuelle_usd)
    total = _total_usd(allocation_actuelle)

    safety: Dict[str, Any] = {
        "max_shift_ratio_applique": _safe_float(opts.get("max_shift_ratio"), float(DEFAULT_PARAMS["max_shift_ratio"])),
        "plan_reduit": False,
        "motif_annulation": None,
        "mode": "simulation" if dry_run_only else "reel",
    }

    plan: Dict[str, Any] = {
        "context": contexte_effectif,
        "profil": _normaliser_profil(profil),
        "run_id": run_id,
        "total_usd": round(float(total), 6),
        "allocation_actuelle_usd": allocation_actuelle,
        "allocation_cible_usd": {cat: 0.0 for cat in CATEGORIES},
        "actions": [],
        "safety": safety,
        "signals_summary": dict(signaux_summary) if isinstance(signaux_summary, Mapping) else None,
        "cfg_version": opts.get("cfg_version"),
        "dry_run_only": bool(dry_run_only),
    }

    if total <= 0:
        safety["motif_annulation"] = "Total du portefeuille non valide."
        _journaliser_plan(plan, journal_path)
        return plan

    if total < _safe_float(opts.get("min_total_usd"), float(DEFAULT_PARAMS["min_total_usd"])):
        safety["motif_annulation"] = "Portefeuille trop faible pour un rééquilibrage sécurisé."
        _journaliser_plan(plan, journal_path)
        return plan

    allocation_cible = _calculer_allocation_cible_usd(
        profil=plan["profil"],
        contexte=plan["context"],
        total_usd=float(total),
        signaux_summary=signaux_summary,
    )
    plan["allocation_cible_usd"] = {k: round(float(v), 6) for k, v in allocation_cible.items()}

    actions, meta_safety = _construire_actions(
        allocation_actuelle=allocation_actuelle,
        allocation_cible=allocation_cible,
        contexte=plan["context"],
        options=opts,
        total_usd=float(total),
    )

    safety["plan_reduit"] = bool(safety.get("plan_reduit")) or bool(meta_safety.get("plan_reduit"))
    if meta_safety.get("motif_annulation"):
        safety["motif_annulation"] = meta_safety["motif_annulation"]

    plan["actions"] = actions

    somme_mouvements = sum(_safe_float(action.get("montant_usd"), 0.0) for action in actions)
    if total > 0:
        safety["max_shift_ratio_applique"] = min(
            _safe_float(safety.get("max_shift_ratio_applique"), float(DEFAULT_PARAMS["max_shift_ratio"])),
            somme_mouvements / float(total) if total else 0.0,
        )

    _journaliser_plan(plan, journal_path)
    return plan
