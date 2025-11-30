# core/rebalancing.py – V5.1.0
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

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
    "max_actions": 6,
    "min_total_usd": 50.0,
    "mode_simulation": True,
}


def _normaliser_profil(profil: str | None) -> str:
    """Normalise un profil utilisateur en l'une des trois valeurs supportées."""

    if not isinstance(profil, str):
        return "modere"
    profil_normalise = profil.strip().lower()
    if profil_normalise not in {"prudent", "modere", "risque"}:
        return "modere"
    return profil_normalise


def _normaliser_contexte(context_label: str | None) -> str:
    """Normalise un libellé de contexte vers défavorable, neutre ou favorable."""

    if not isinstance(context_label, str):
        return "neutre"
    contexte_normalise = context_label.strip().lower()
    if contexte_normalise not in {"defavorable", "neutre", "favorable"}:
        return "neutre"
    return contexte_normalise


def _normaliser_allocation(allocation: Dict[str, Any] | None) -> Dict[str, float]:
    """Convertit un dictionnaire d'allocation vers un format complet et numérique."""

    allocation = allocation or {}
    resultats: Dict[str, float] = {}
    for categorie in CATEGORIES:
        valeur = allocation.get(categorie, 0.0)
        try:
            resultats[categorie] = float(valeur)
        except (TypeError, ValueError):
            resultats[categorie] = 0.0
    return resultats


def _fusionner_params(params: Dict[str, Any] | None) -> Dict[str, Any]:
    """Fusionne les paramètres fournis avec les valeurs par défaut du moteur."""

    valeurs = dict(DEFAULT_PARAMS)
    if params:
        for cle, valeur in params.items():
            valeurs[cle] = valeur
    valeurs["mode_simulation"] = bool(valeurs.get("mode_simulation", True))
    return valeurs


def _renormaliser_poids(poids: Dict[str, float]) -> Dict[str, float]:
    """Renormalise un dictionnaire de poids pour garantir des valeurs positives et une somme de 1."""

    valeurs_non_negatives = {cat: max(float(valeur), 0.0) for cat, valeur in poids.items()}
    total = sum(valeurs_non_negatives.values())
    if total <= 0.0:
        uniforme = 1.0 / len(CATEGORIES)
        return {cat: uniforme for cat in CATEGORIES}
    return {cat: valeurs_non_negatives.get(cat, 0.0) / total for cat in CATEGORIES}


def _resumer_signaux(signaux: List[Dict[str, Any]] | None) -> Dict[str, Any]:
    """Synthétise les signaux d'IA en moyenne d'aiscore et contexte observé."""

    if not signaux:
        return {"ai_score_moyen": None, "nb_signaux": 0, "context_labels": []}
    scores: List[float] = []
    context_labels: List[str] = []
    for signal in signaux:
        valeur = signal.get("ai_score") if isinstance(signal, dict) else None
        if isinstance(valeur, (int, float)) and 0.0 <= float(valeur) <= 1.0:
            scores.append(float(valeur))
        label = signal.get("context_label") if isinstance(signal, dict) else None
        if isinstance(label, str) and label not in context_labels:
            context_labels.append(label)
    ai_score_moyen = sum(scores) / len(scores) if scores else None
    return {
        "ai_score_moyen": ai_score_moyen,
        "nb_signaux": len(signaux),
        "context_labels": context_labels,
    }


def _ajuster_poids_par_signaux(poids: Dict[str, float], ai_score_moyen: float | None) -> Dict[str, float]:
    """Ajuste légèrement les poids prudent/risque selon la moyenne des scores IA."""

    ajustements = dict(poids)
    if ai_score_moyen is None:
        return _renormaliser_poids(ajustements)
    if ai_score_moyen > 0.7:
        ajustements["Risque"] = ajustements.get("Risque", 0.0) + 0.05
        ajustements["Prudent"] = ajustements.get("Prudent", 0.0) - 0.05
    elif ai_score_moyen < 0.3:
        ajustements["Risque"] = ajustements.get("Risque", 0.0) - 0.05
        ajustements["Prudent"] = ajustements.get("Prudent", 0.0) + 0.05
    return _renormaliser_poids(ajustements)


def _calculer_allocation_cible_usd(
    profil: str,
    contexte: str,
    total_usd: float,
    signaux_summary: Dict[str, Any],
) -> Dict[str, float]:
    """Calcule une allocation cible en USD à partir des poids ajustés et du total."""

    base = ALLOCATION_MATRIX.get(profil, ALLOCATION_MATRIX["modere"])
    poids = base.get(contexte, base["neutre"])
    poids_ajustes = _ajuster_poids_par_signaux(poids, signaux_summary.get("ai_score_moyen"))
    return {categorie: poids_ajustes[categorie] * total_usd for categorie in CATEGORIES}


def _determiner_total_usd(allocation_actuelle: Dict[str, float], total_usd: float | None) -> float:
    """Détermine le total à utiliser pour la conversion en montants absolus."""

    if total_usd is not None:
        try:
            return float(total_usd)
        except (TypeError, ValueError):
            return 0.0
    return float(sum(allocation_actuelle.values()))


def _filtrer_actions_par_seuil(actions: List[Dict[str, Any]], seuil: float) -> List[Dict[str, Any]]:
    """Retire les actions dont l'impact est inférieur au seuil minimal de rééquilibrage."""

    return [action for action in actions if action["montant_usd"] >= seuil]


def _appliquer_limite_globale(
    actions: List[Dict[str, Any]],
    total_usd: float,
    max_shift_ratio: float,
) -> Tuple[List[Dict[str, Any]], bool]:
    """Applique la contrainte de déplacement global exprimée en pourcentage du portefeuille."""

    somme = sum(action["montant_usd"] for action in actions)
    limite = max_shift_ratio * total_usd
    if limite <= 0.0 or somme <= limite:
        return actions, False
    facteur = limite / somme if somme > 0 else 0.0
    nouvelles_actions: List[Dict[str, Any]] = []
    for action in actions:
        nouvelle_valeur = action["montant_usd"] * facteur
        if nouvelle_valeur <= 0.0:
            continue
        nouvelle_action = dict(action)
        nouvelle_action["montant_usd"] = nouvelle_valeur
        nouvelles_actions.append(nouvelle_action)
    return nouvelles_actions, True


def _limiter_nombre_actions(actions: List[Dict[str, Any]], max_actions: int) -> Tuple[List[Dict[str, Any]], bool]:
    """Applique la limite sur le nombre d'actions à exécuter et conserve les plus significatives."""

    if max_actions <= 0 or len(actions) <= max_actions:
        return actions, False
    actions_tries = sorted(actions, key=lambda a: a["montant_usd"], reverse=True)
    return actions_tries[:max_actions], True


def _equilibrer_actions(actions: List[Dict[str, Any]], total_usd: float) -> Tuple[List[Dict[str, Any]], bool, str | None]:
    """Garantit que le total des augmentations est proche de celui des réductions."""

    tolerance = max(1.0, 0.01 * max(total_usd, 1.0))
    somme_augmenter = sum(action["montant_usd"] for action in actions if action["action"] == "augmenter")
    somme_reduire = sum(action["montant_usd"] for action in actions if action["action"] == "reduire")
    difference = somme_augmenter - somme_reduire
    if abs(difference) <= tolerance:
        return actions, False, None
    ajustement_effectue = False
    if difference > 0:
        difference_restante = difference
        for action in reversed(actions):
            if action["action"] != "augmenter":
                continue
            disponible = action["montant_usd"]
            retrait = min(disponible, difference_restante)
            action["montant_usd"] = max(disponible - retrait, 0.0)
            difference_restante -= retrait
            ajustement_effectue = True
            if difference_restante <= tolerance:
                break
    else:
        difference_restante = -difference
        for action in reversed(actions):
            if action["action"] != "reduire":
                continue
            disponible = action["montant_usd"]
            retrait = min(disponible, difference_restante)
            action["montant_usd"] = max(disponible - retrait, 0.0)
            difference_restante -= retrait
            ajustement_effectue = True
            if difference_restante <= tolerance:
                break
    actions = [action for action in actions if action["montant_usd"] > 0.0]
    somme_augmenter = sum(action["montant_usd"] for action in actions if action["action"] == "augmenter")
    somme_reduire = sum(action["montant_usd"] for action in actions if action["action"] == "reduire")
    if abs(somme_augmenter - somme_reduire) <= tolerance:
        return actions, ajustement_effectue, None
    return [], True, "Plan incohérent après équilibrage des montants."


def _construire_actions(
    allocation_actuelle: Dict[str, float],
    allocation_cible: Dict[str, float],
    contexte: str,
    params: Dict[str, Any],
    total_usd: float,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Construit la liste d'actions après application des différentes règles de sécurité."""

    actions_brutes: List[Dict[str, Any]] = []
    min_rebal_usd = float(params.get("min_rebal_usd", DEFAULT_PARAMS["min_rebal_usd"]))
    for categorie in CATEGORIES:
        delta = allocation_cible.get(categorie, 0.0) - allocation_actuelle.get(categorie, 0.0)
        if abs(delta) < min_rebal_usd:
            continue
        if contexte == "defavorable" and categorie == "Risque" and delta > 0:
            continue
        action_type = "augmenter" if delta > 0 else "reduire"
        actions_brutes.append(
            {
                "categorie": categorie,
                "action": action_type,
                "montant_usd": abs(delta),
                "raison": f"Aligner la catégorie {categorie} sur la cible contextuelle.",
            }
        )
    plan_reduit = False
    motif_annulation: str | None = None
    actions_filtrees = _filtrer_actions_par_seuil(actions_brutes, min_rebal_usd)
    if not actions_filtrees:
        return [], {"plan_reduit": plan_reduit, "motif_annulation": motif_annulation}
    actions_limitees, reduction = _appliquer_limite_globale(
        actions_filtrees,
        total_usd,
        float(params.get("max_shift_ratio", DEFAULT_PARAMS["max_shift_ratio"])),
    )
    plan_reduit = plan_reduit or reduction
    if not actions_limitees:
        return [], {"plan_reduit": plan_reduit, "motif_annulation": "Limite globale atteinte."}
    actions_limitees, reduction_nombre = _limiter_nombre_actions(
        actions_limitees,
        int(params.get("max_actions", DEFAULT_PARAMS["max_actions"])),
    )
    plan_reduit = plan_reduit or reduction_nombre
    actions_equilibrees, ajustement_effectue, motif_equilibre = _equilibrer_actions(actions_limitees, total_usd)
    plan_reduit = plan_reduit or ajustement_effectue
    if motif_equilibre:
        motif_annulation = motif_equilibre
        actions_equilibrees = []
    return actions_equilibrees, {"plan_reduit": plan_reduit, "motif_annulation": motif_annulation}


def _journaliser_plan(plan: Dict[str, Any], journal_path: str | None) -> None:
    """Ajoute une ligne JSONL au journal si un chemin est configuré."""

    if not journal_path:
        return
    try:
        with open(journal_path, "a", encoding="utf-8") as journal:
            journal.write(json.dumps(plan, ensure_ascii=False))
            journal.write("\n")
    except OSError as exc:
        plan.setdefault("safety", {})["journal_error"] = str(exc)


def generer_plan_reequilibrage_contexte(
    context_label: str,
    profil_actif: str,
    allocation_actuelle_usd: Dict[str, float],
    total_usd: float | None = None,
    signaux_normalises: List[Dict[str, Any]] | None = None,
    params: Dict[str, Any] | None = None,
    run_id: str | None = None,
    journal_path: str | None = None,
) -> Dict[str, Any]:
    """Génère un plan de rééquilibrage catégoriel tenant compte du contexte et des signaux."""

    profil = _normaliser_profil(profil_actif)
    contexte = _normaliser_contexte(context_label)
    allocation_actuelle = _normaliser_allocation(allocation_actuelle_usd)
    options = _fusionner_params(params)
    total = _determiner_total_usd(allocation_actuelle, total_usd)
    safety = {
        "max_shift_ratio_applique": float(options.get("max_shift_ratio", DEFAULT_PARAMS["max_shift_ratio"])),
        "plan_reduit": False,
        "motif_annulation": None,
        "mode": "simulation" if options.get("mode_simulation", True) else "reel",
    }
    signaux_summary = _resumer_signaux(signaux_normalises)
    plan: Dict[str, Any] = {
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
    if total <= 0.0:
        safety["motif_annulation"] = "Total du portefeuille non valide."
        _journaliser_plan(plan, journal_path)
        return plan
    if total < float(options.get("min_total_usd", DEFAULT_PARAMS["min_total_usd"])):
        safety["motif_annulation"] = "Portefeuille trop faible pour un rééquilibrage sécurisé."
        _journaliser_plan(plan, journal_path)
        return plan
    allocation_cible = _calculer_allocation_cible_usd(profil, contexte, total, signaux_summary)
    plan["allocation_cible_usd"] = allocation_cible
    actions, meta_safety = _construire_actions(allocation_actuelle, allocation_cible, contexte, options, total)
    safety["plan_reduit"] = safety["plan_reduit"] or meta_safety["plan_reduit"]
    if meta_safety["motif_annulation"]:
        safety["motif_annulation"] = meta_safety["motif_annulation"]
    plan["actions"] = actions
    somme_mouvements = sum(action["montant_usd"] for action in actions)
    if total > 0:
        safety["max_shift_ratio_applique"] = min(
            safety["max_shift_ratio_applique"],
            somme_mouvements / total if total else 0.0,
        )
    if contexte == "defavorable":
        risque_augment = any(
            action["categorie"] == "Risque" and action["action"] == "augmenter" for action in actions
        )
        if risque_augment:
            safety["motif_annulation"] = "Protection risque : aucune augmentation de la poche Risque en contexte défavorable."
            plan["actions"] = []
    _journaliser_plan(plan, journal_path)
    return plan