#!/usr/bin/env python3
# journal_daemon.py — V5.3.0
"""Journaliseur continu de signaux pour DeFiPilot avec sauvegarde, restauration d'état,
lecture des soldes du wallet au démarrage et génération d'un plan de rééquilibrage simulé.

Boucle simple :
- lit les stats de pools depuis un fichier JSON,
- calcule contexte + policy via core.market_signals_adapter,
- écrit dans un fichier journal JSONL à chaque itération,
- persiste l'état via core.state_manager,
- lit les soldes du wallet en lecture seule via core.wallet_reader au démarrage,
- génère et journalise un plan de rééquilibrage simulé via core.rebalancing,
- V5.1.2 : intègre les signaux consolidés + normalisés (ControlPilot + signals_normalizer)
  dans le plan de rééquilibrage.
- V5.1.3 : intègre le scoring des pools (core.scoring) dans l'état global
  sous la clé `dernier_scoring_pools`.
- V5.1.4 : calcule et stocke une allocation simulée après rééquilibrage
  dans l'état sous la clé `allocation_simulee_apres_reequilibrage`.
- V5.1.5 : journalise un snapshot complet stratégie/portefeuille à chaque itération
  dans data/logs/journal_strategie.jsonl.
- V5.3.0 : ajoute un journal stratégique dédié (journal_strategy.jsonl)
  via core.journal_strategy.journaliser_entree_strategique().
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from control.control_pilot import lire_signaux_consolides
from core.market_signals_adapter import calculer_contexte_et_policy
from core.rebalancing import generer_plan_reequilibrage_contexte
from core.signals_normalizer import normaliser_signaux, SignalNormalise
from core.state_manager import get_state, update_state, save_state
from core.wallet_reader import lire_soldes_depuis_env
from core.scoring import calculer_scores_et_gains, charger_ponderations
from core.strategy_snapshot import journaliser_decision
from core.journal_strategy import journaliser_entree_strategique


VERSION = "V5.3.0"
DECISIONS_JOURNAL_PATH = Path("journal_decisions.jsonl")
STRATEGY_JOURNAL_PATH = Path("data/logs/journal_strategie.jsonl")
StateDict = dict[str, Any]


# ---------------------------------------------------------------------------
# Utilitaires génériques
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> Any:
    """Lit un fichier JSON et renvoie l'objet Python associé."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _ensure_mapping(obj: Any) -> Mapping[str, Any]:
    """Garantit qu'un objet est un mapping clé/valeur."""
    if isinstance(obj, Mapping):
        return obj
    return {}


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    """Ajoute un événement JSON sérialisé sur une ligne dans le fichier JSONL donné."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)
        handle.write("\n")


def _to_float(value: Any) -> float | None:
    """Convertit une valeur en float si possible, sinon renvoie None."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Calculs d'allocation & scoring
# ---------------------------------------------------------------------------


def _calculer_allocation_categorielle(etat: StateDict) -> dict[str, float]:
    """Calcule l'allocation actuelle par catégorie de risque à partir de l'état."""
    allocation: dict[str, float] = {"Prudent": 0.0, "Modere": 0.0, "Risque": 0.0}
    positions = etat.get("positions")
    if not isinstance(positions, list):
        return allocation

    for pos in positions:
        if not isinstance(pos, Mapping):
            continue

        montant = pos.get("montant_investi_usd")
        if not isinstance(montant, (int, float)):
            try:
                montant = float(montant)
            except (TypeError, ValueError):
                continue

        categorie = pos.get("categorie_risque") or pos.get("categorie")
        if isinstance(categorie, str):
            cat_lower = categorie.lower()
            if "prudent" in cat_lower:
                categorie_norm = "Prudent"
            elif "risque" in cat_lower:
                categorie_norm = "Risque"
            else:
                categorie_norm = "Modere"
        else:
            categorie_norm = "Modere"

        allocation[categorie_norm] += float(montant)

    return allocation


def _charger_signaux_normalises(limit: int = 50) -> list[SignalNormalise]:
    """Lit les signaux consolidés (ControlPilot) et les normalise pour la stratégie.

    Étapes :
    - lecture via control.control_pilot.lire_signaux_consolides(),
    - conversion en dict(),
    - normalisation via core.signals_normalizer.normaliser_signaux().

    En cas d'erreur, retourne une liste vide et loggue un avertissement simple.
    """
    try:
        signaux_consolides = lire_signaux_consolides(limit=limit, include_ai=True)
    except Exception as exc:  # best effort
        print(f"[WARN] Impossible de lire les signaux consolidés : {exc}")
        return []

    bruts: list[dict[str, Any]] = []
    for s in signaux_consolides:
        # SignalConsolide possède to_dict(), mais on garde une compatibilité large
        if hasattr(s, "to_dict"):
            try:
                bruts.append(s.to_dict())  # type: ignore[call-arg]
                continue
            except Exception:
                pass
        if isinstance(s, Mapping):
            bruts.append(dict(s))

    if not bruts:
        return []

    try:
        signaux_norm = normaliser_signaux(bruts)
    except Exception as exc:  # best effort
        print(f"[WARN] Normalisation des signaux impossible : {exc}")
        return []

    if signaux_norm:
        print(f"[INFO] {len(signaux_norm)} signal(s) normalisé(s) chargé(s) pour le rééquilibrage.")
    return signaux_norm


def _calculer_scoring_pools(
    pools_stats: list[dict[str, Any]],
    profil_nom: str,
    solde_total_usd: float,
    historique_pools: Any,
) -> dict[str, Any]:
    """Calcule le scoring des pools à partir de core.scoring.

    - Utilise charger_ponderations(profil_nom) pour récupérer les pondérations.
    - Construit un dict de profil compatible avec calculer_scores_et_gains().
    - Passe un historique_pools si disponible, sinon un dict vide.
    - Retourne un résumé (profil, solde de référence, top3, gain total/jour).
    """
    base = charger_ponderations(profil_nom)

    profil = {
        "nom": profil_nom,
        "ponderations": {
            "apr": float(base.get("apr", 0.0)),
            "tvl": float(base.get("tvl", 0.0)),
        },
        "historique_max_bonus": float(base.get("historique_max_bonus", 0.0)),
        "historique_max_malus": float(base.get("historique_max_malus", 0.0)),
    }

    if isinstance(historique_pools, Mapping):
        hist = dict(historique_pools)
    else:
        hist = {}

    try:
        solde_ref = float(solde_total_usd)
    except (TypeError, ValueError):
        solde_ref = 0.0

    # calculer_scores_et_gains modifie les pools pour ajouter "score"
    resultats_top3, gain_total = calculer_scores_et_gains(
        pools=list(pools_stats),
        profil=profil,
        solde=solde_ref,
        historique_pools=hist,
    )

    scoring_info: dict[str, Any] = {
        "profil": profil_nom,
        "solde_reference_usd": solde_ref,
        "resultats_top3": resultats_top3,
        "gain_total_journalier_usd": gain_total,
    }
    return scoring_info


def _simuler_allocation_apres_reequilibrage(
    allocation_actuelle_usd: Mapping[str, float],
    actions: list[Mapping[str, Any]],
) -> dict[str, float]:
    """Calcule une allocation simulée après rééquilibrage à partir des actions.

    On part de l'allocation actuelle (par catégorie de risque) et on applique
    les variations USD (delta_usd / variation_usd / amount_usd) par catégorie.
    """
    nouvelle_alloc: dict[str, float] = {
        "Prudent": float(allocation_actuelle_usd.get("Prudent", 0.0)),
        "Modere": float(allocation_actuelle_usd.get("Modere", 0.0)),
        "Risque": float(allocation_actuelle_usd.get("Risque", 0.0)),
    }

    for action in actions:
        if not isinstance(action, Mapping):
            continue

        categorie = action.get("categorie") or action.get("categorie_risque")
        if isinstance(categorie, str):
            cat_lower = categorie.lower()
            if "prudent" in cat_lower:
                categorie_norm = "Prudent"
            elif "risque" in cat_lower:
                categorie_norm = "Risque"
            else:
                categorie_norm = "Modere"
        else:
            categorie_norm = "Modere"

        delta = (
            _to_float(action.get("delta_usd"))
            or _to_float(action.get("variation_usd"))
            or _to_float(action.get("amount_usd"))
            or 0.0
        )

        actuelle = nouvelle_alloc.get(categorie_norm, 0.0)
        nouvelle_alloc[categorie_norm] = float(actuelle) + float(delta)

    return nouvelle_alloc


# ---------------------------------------------------------------------------
# Journalisation détaillée
# ---------------------------------------------------------------------------


def _journaliser_decisions(
    plan: Mapping[str, Any] | None,
    run_id: str,
    context: str,
    profil: str,
    mode: str = "simulation",
    path: Path = DECISIONS_JOURNAL_PATH,
) -> None:
    """Journalise les actions de rééquilibrage simulées dans un fichier JSONL.

    Une ligne est écrite par action contenue dans le plan.
    """
    if not isinstance(plan, Mapping):
        return

    actions = plan.get("actions")
    if not isinstance(actions, list) or not actions:
        return

    allocation_actuelle = plan.get("allocation_actuelle_usd")

    for idx, action in enumerate(actions):
        if not isinstance(action, Mapping):
            continue

        action_type_raw = action.get("type") or action.get("action") or action.get("operation")
        if isinstance(action_type_raw, str) and action_type_raw.strip():
            action_type = action_type_raw.strip()
        else:
            action_type = "adjust_allocation"

        categorie = action.get("categorie") or action.get("categorie_risque")
        categorie_val: str | None
        if isinstance(categorie, str):
            categorie_val = categorie
        else:
            categorie_val = None

        pool_id = action.get("pool_id") or action.get("pool") or action.get("id")
        if isinstance(pool_id, (int, float)):
            pool_id = str(pool_id)
        elif not isinstance(pool_id, str):
            pool_id = None

        event: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z"),
            "run_id": run_id,
            "version": VERSION,
            "source": "reequilibrage_simule",
            "mode": mode,
            "context": context,
            "profil": profil,
            "action_type": action_type,
            "categorie": categorie_val or "inconnue",
            "pool_id": pool_id,
            "amount_usd": _to_float(action.get("amount_usd") or action.get("montant_usd")),
            "delta_usd": _to_float(action.get("delta_usd") or action.get("variation_usd")),
        }

        details: dict[str, Any] = {}
        if allocation_actuelle is not None:
            details["allocation_actuelle_usd"] = allocation_actuelle
        details["raw_action"] = dict(action)
        details["action_index"] = idx
        event["details"] = details

        try:
            _append_jsonl(path, event)
        except Exception as exc:  # best effort
            print(f"[WARN] Impossible d'écrire dans {path}: {exc}")
            break


def _journaliser_snapshot_strategie(
    path: Path,
    run_id: str,
    decision: Any,
    profil_effectif: str,
    allocation_actuelle: Mapping[str, float] | None,
    allocation_simulee: Mapping[str, float] | None,
    scoring_info: Mapping[str, Any] | None,
    nb_signaux: int,
) -> None:
    """Journalise un snapshot complet de la stratégie et du portefeuille.

    Ce snapshot servira pour la GUI et pour l'analyse historique des décisions.
    """
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "run_id": run_id,
        "version": VERSION,
        "context": getattr(decision, "context", None),
        "decision_score": getattr(decision, "score", None),
        "profil": profil_effectif,
        "nb_signaux": int(nb_signaux),
    }

    if isinstance(allocation_actuelle, Mapping):
        payload["allocation_actuelle_usd"] = {
            "Prudent": float(allocation_actuelle.get("Prudent", 0.0)),
            "Modere": float(allocation_actuelle.get("Modere", 0.0)),
            "Risque": float(allocation_actuelle.get("Risque", 0.0)),
        }

    if isinstance(allocation_simulee, Mapping):
        payload["allocation_simulee_apres_reequilibrage"] = {
            "Prudent": float(allocation_simulee.get("Prudent", 0.0)),
            "Modere": float(allocation_simulee.get("Modere", 0.0)),
            "Risque": float(allocation_simulee.get("Risque", 0.0)),
        }

    if isinstance(scoring_info, Mapping):
        payload["scoring"] = {
            "solde_reference_usd": float(scoring_info.get("solde_reference_usd", 0.0)),
            "gain_total_journalier_usd": float(
                scoring_info.get("gain_total_journalier_usd", 0.0)
            ),
            "resultats_top3": scoring_info.get("resultats_top3"),
            "profil_scoring": scoring_info.get("profil", {}),
        }

    # Journal stratégique V5.3 (journal_strategy.jsonl)
    try:
        journaliser_entree_strategique(
            event_type="strategy_decision",
            version=VERSION,
            run_id=run_id,
            context=payload.get("context"),
            profil=profil_effectif,
            allocation_avant_usd=payload.get("allocation_actuelle_usd"),
            allocation_apres_usd=payload.get("allocation_simulee_apres_reequilibrage"),
        )
    except Exception as exc:  # best effort
        print(
            "[WARN] Impossible de journaliser la stratégie dans journal_strategy.jsonl : "
            f"{exc}"
        )

    # Journal de décisions globales (V5.1.1+)
    try:
        journaliser_decision(payload)
    except Exception as exc:
        print(
            f"[WARN] Impossible de journaliser la décision dans journal_decisions.jsonl : {exc}"
        )

    try:
        _append_jsonl(path, payload)
    except Exception as exc:
        print(f"[WARN] Impossible d'écrire le snapshot stratégie dans {path}: {exc}")


# ---------------------------------------------------------------------------
# Boucle principale
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée du journaliseur continu de signaux.

    - Charge les stats de pools.
    - Charge une configuration optionnelle.
    - Lit/initialise l'état.
    - Lit les soldes du wallet au démarrage (lecture seule).
    - Boucle à intervalle régulier pour :
      - charger les signaux normalisés,
      - calculer le contexte & la policy,
      - générer un plan de rééquilibrage simulé,
      - calculer un scoring des pools,
      - journaliser un snapshot de stratégie + décisions + journal stratégique V5.3.
    """
    parser = argparse.ArgumentParser(description="DeFiPilot – Journaliseur continu de signaux")
    parser.add_argument(
        "--pools",
        required=True,
        help="Fichier JSON des stats de pools (liste de dicts)",
    )
    parser.add_argument(
        "--cfg",
        default=None,
        help="Fichier JSON de configuration (optionnel)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Intervalle en secondes entre deux écritures (défaut: 30)",
    )
    parser.add_argument(
        "--max-loops",
        type=int,
        default=0,
        help=(
            "Nombre maximal de boucles à exécuter (0 = illimité). "
            "Utile pour les tests manuels."
        ),
    )

    args = parser.parse_args(argv)

    pools_path = Path(args.pools)
    if not pools_path.exists():
        print(f"[ERROR] Fichier pools introuvable : {pools_path}")
        return 1

    try:
        pools_data = _read_json(pools_path)
    except Exception as exc:
        print(f"[ERROR] Impossible de lire le fichier pools {pools_path} : {exc}")
        return 1

    if isinstance(pools_data, list):
        pools_stats: list[dict[str, Any]] = [
            p for p in pools_data if isinstance(p, Mapping)
        ]
    elif isinstance(pools_data, Mapping) and isinstance(pools_data.get("pools"), list):
        pools_stats = [
            p for p in pools_data.get("pools", []) if isinstance(p, Mapping)
        ]
    else:
        print("[ERROR] Format de pools invalide (attendu: liste de dicts ou clé 'pools').")
        return 1

    config: Mapping[str, Any] = {}
    if args.cfg is not None:
        cfg_path = Path(args.cfg)
        if cfg_path.exists():
            try:
                config_obj = _read_json(cfg_path)
                config = _ensure_mapping(config_obj)
            except Exception as exc:
                print(f"[WARN] Impossible de lire la configuration {cfg_path} : {exc}")
        else:
            print(f"[WARN] Fichier de configuration introuvable : {cfg_path}")

    # Chargement/initialisation de l'état
    etat: StateDict = get_state() or {}

    # Lecture des soldes du wallet au démarrage (lecture seule, best effort)
    try:
        soldes_wallet = lire_soldes_depuis_env()
        if isinstance(soldes_wallet, Mapping):
            etat.setdefault("soldes_wallet", {}).update(dict(soldes_wallet))
    except Exception as exc:
        print(f"[WARN] Impossible de lire les soldes du wallet : {exc}")

    # Boucle principale
    interval = max(1, int(args.interval))
    max_loops = int(args.max_loops or 0)
    loop_count = 0

    print(
        f"[INFO] Journaliseur continu démarré.\n"
        f"       pools   = {pools_path}\n"
        f"       cfg     = {args.cfg or '(aucune)'}\n"
        f"       journal = {STRATEGY_JOURNAL_PATH}\n"
        f"       interval= {interval}s, max_loops={max_loops or 'illimité'}"
    )

    while True:
        loop_count += 1
        run_id = (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )

        print(f"[LOOP] run_id={run_id} (boucle {loop_count})")

        # 1) Charger les signaux normalisés
        signaux_norm = _charger_signaux_normalises(limit=50)
        nb_signaux = len(signaux_norm)

        # 2) Calculer contexte + policy via core.market_signals_adapter
        try:
            decision, profil_effectif = calculer_contexte_et_policy(
                signaux_norm,
                config,
            )
        except Exception as exc:
            print(f"[ERROR] Echec de calcul du contexte/policy : {exc}")
            time.sleep(interval)
            if max_loops and loop_count >= max_loops:
                break
            continue

        # 3) Calculer l'allocation actuelle par catégorie de risque
        allocation_actuelle = _calculer_allocation_categorielle(etat)

        # 4) Calculer le scoring des pools
        solde_total = sum(allocation_actuelle.values())
        historique_pools = etat.get("historique_pools")
        try:
            scoring_info = _calculer_scoring_pools(
                pools_stats=pools_stats,
                profil_nom=profil_effectif,
                solde_total_usd=solde_total,
                historique_pools=historique_pools,
            )
            etat["dernier_scoring_pools"] = scoring_info
        except Exception as exc:
            print(f"[WARN] Echec du calcul de scoring des pools : {exc}")
            scoring_info = None

        # 5) Générer un plan de rééquilibrage simulé via core.rebalancing
        try:
            plan_reeq = generer_plan_reequilibrage_contexte(
                decision=decision,
                allocation_actuelle_usd=allocation_actuelle,
                scoring_info=scoring_info,
                state=etat,
                config=config,
                signaux_norm=signaux_norm,
            )
        except TypeError:
            # Fallback si la signature est plus simple dans la version actuelle
            try:
                plan_reeq = generer_plan_reequilibrage_contexte(
                    decision,
                    allocation_actuelle,
                )
            except Exception as exc:
                print(f"[WARN] Impossible de générer le plan de rééquilibrage : {exc}")
                plan_reeq = None
        except Exception as exc:
            print(f"[WARN] Impossible de générer le plan de rééquilibrage : {exc}")
            plan_reeq = None

        # 6) Simuler l'allocation après rééquilibrage
        allocation_simulee = None
        if isinstance(plan_reeq, Mapping):
            actions = plan_reeq.get("actions")
            if isinstance(actions, list):
                allocation_simulee = _simuler_allocation_apres_reequilibrage(
                    allocation_actuelle_usd=allocation_actuelle,
                    actions=actions,
                )
                etat["allocation_simulee_apres_reequilibrage"] = allocation_simulee

        # 7) Journaliser les décisions de rééquilibrage simulées (journal_decisions.jsonl)
        try:
            context_value = getattr(decision, "context", None)
            context_str = context_value or "inconnu"
            _journaliser_decisions(
                plan=plan_reeq,
                run_id=run_id,
                context=context_str,
                profil=profil_effectif,
                mode="simulation",
            )
        except Exception as exc:
            print(f"[WARN] Echec de la journalisation des décisions : {exc}")

        # 8) Journaliser le snapshot stratégie (STRATEGY_JOURNAL_PATH + journal stratég."""
        try:
            _journaliser_snapshot_strategie(
                path=STRATEGY_JOURNAL_PATH,
                run_id=run_id,
                decision=decision,
                profil_effectif=profil_effectif,
                allocation_actuelle=allocation_actuelle,
                allocation_simulee=allocation_simulee,
                scoring_info=scoring_info,
                nb_signaux=nb_signaux,
            )
        except Exception as exc:
            print(f"[WARN] Echec de la journalisation du snapshot stratégie : {exc}")

        # 9) Sauvegarder l'état mis à jour
        try:
            update_state(etat)
            save_state()
        except Exception as exc:
            print(f"[WARN] Impossible de sauvegarder l'état : {exc}")

        # 10) Gestion de la boucle (max_loops / interval)
        if max_loops and loop_count >= max_loops:
            print("[INFO] Nombre maximal de boucles atteint, arrêt du daemon.")
            break

        time.sleep(interval)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
