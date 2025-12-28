# journal_daemon.py – V5.5.0
#!/usr/bin/env python3
"""Journaliseur continu de signaux pour DeFiPilot.

- lit les stats de pools depuis un fichier JSON,
- charge une configuration stratégie via DEFIPILOT_STRATEGY_CFG (optionnel),
- calcule contexte + policy via core.market_signals_adapter,
- calcule le mode global V5.5 via core.mode_engine_v5_5,
- génère et journalise un plan de rééquilibrage simulé via core.rebalancing,
- calcule un scoring des pools via core.scoring (best effort),
- journalise un snapshot complet dans data/logs/journal_strategie.jsonl,
- persiste l'état via core.state_manager.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping

from control.control_pilot import lire_signaux_consolides
from core.journal_strategy import journaliser_entree_strategique
from core.market_signals_adapter import calculer_contexte_et_policy
from core.mode_engine_v5_5 import determiner_mode_global_v5_5
from core.rebalancing import generer_plan_reequilibrage_contexte
from core.scoring import calculer_scores_et_gains, charger_ponderations
from core.signals_normalizer import SignalNormalise, normaliser_signaux
from core.state_manager import get_state, save_state, update_state
from core.strategy_snapshot import journaliser_decision
from core.wallet_reader import lire_soldes_depuis_env

VERSION = "V5.5.0"

DECISIONS_JOURNAL_PATH = Path("data/logs/journal_decisions.jsonl")
STRATEGY_JOURNAL_PATH = Path("data/logs/journal_strategie.jsonl")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _ensure_mapping(obj: Any) -> Mapping[str, Any]:
    return obj if isinstance(obj, Mapping) else {}


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        json.dump(dict(payload), f, ensure_ascii=False)
        f.write("\n")


def _charger_config_strategy_env() -> tuple[Mapping[str, Any], str | None]:
    """Charge la config stratégie depuis DEFIPILOT_STRATEGY_CFG (best effort)."""
    env_path = os.environ.get("DEFIPILOT_STRATEGY_CFG", "").strip()
    if not env_path:
        return {}, None

    p = Path(env_path)
    if not p.exists():
        print(f"[WARN] Fichier stratégie introuvable : {p}")
        return {}, env_path

    try:
        cfg = _ensure_mapping(_read_json(p))
        print(f"[INFO] Configuration stratégie chargée depuis {p.as_posix().replace('/', chr(92))}")
        return cfg, env_path
    except Exception as exc:
        print(f"[WARN] Impossible de lire la config stratégie {p}: {exc}")
        return {}, env_path


def _charger_pools(pools_path: Path) -> List[Dict[str, Any]]:
    pools_data = _read_json(pools_path)

    if isinstance(pools_data, list):
        return [p for p in pools_data if isinstance(p, Mapping)]

    if isinstance(pools_data, Mapping) and isinstance(pools_data.get("pools"), list):
        return [p for p in pools_data.get("pools", []) if isinstance(p, Mapping)]

    raise ValueError("Format pools invalide (attendu: liste de dicts ou clé 'pools').")


def _calculer_allocation_categorielle(etat: Mapping[str, Any]) -> Dict[str, float]:
    """Best effort: retourne une allocation par catégories (Prudent/Modere/Risque)."""
    allocation = {"Prudent": 0.0, "Modere": 0.0, "Risque": 0.0}

    # Si l'état contient déjà une allocation
    existing = etat.get("allocation_actuelle_usd")
    if isinstance(existing, Mapping):
        for k in allocation.keys():
            try:
                allocation[k] = float(existing.get(k, 0.0))
            except (TypeError, ValueError):
                allocation[k] = 0.0
        return allocation

    return allocation


def _charger_signaux_normalises(limit: int = 50) -> List[SignalNormalise]:
    """Lit les signaux consolidés et les normalise (best effort)."""
    try:
        signaux_consolides = lire_signaux_consolides(limit=limit, include_ai=True)
    except Exception as exc:
        print(f"[WARN] Impossible de lire les signaux consolidés : {exc}")
        return []

    bruts: List[Dict[str, Any]] = []
    for s in signaux_consolides:
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
    except Exception as exc:
        print(f"[WARN] Normalisation des signaux impossible : {exc}")
        return []

    print(f"[INFO] {len(signaux_norm)} signal(s) normalisé(s) chargé(s) pour le rééquilibrage.")
    return signaux_norm


def _calculer_scoring_pools(
    pools_stats: List[Dict[str, Any]],
    profil_nom: str,
    solde_total_usd: float,
    historique_pools: Mapping[str, Any] | None,
) -> Dict[str, Any]:
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

    hist = dict(historique_pools) if isinstance(historique_pools, Mapping) else {}

    try:
        solde_ref = float(solde_total_usd)
    except (TypeError, ValueError):
        solde_ref = 0.0

    resultats_top3, gain_total = calculer_scores_et_gains(
        pools=list(pools_stats),
        profil=profil,
        solde=solde_ref,
        historique_pools=hist,
    )

    return {
        "profil": profil_nom,
        "solde_reference_usd": solde_ref,
        "resultats_top3": resultats_top3,
        "gain_total_journalier_usd": gain_total,
    }


def _simuler_allocation_apres_reequilibrage(
    allocation_actuelle_usd: Mapping[str, float],
    actions: List[Mapping[str, Any]],
) -> Dict[str, float]:
    allocation = {
        "Prudent": float(allocation_actuelle_usd.get("Prudent", 0.0)),
        "Modere": float(allocation_actuelle_usd.get("Modere", 0.0)),
        "Risque": float(allocation_actuelle_usd.get("Risque", 0.0)),
    }

    for act in actions:
        cat = act.get("categorie")
        action = act.get("action")
        montant = act.get("montant_usd")
        if cat not in allocation:
            continue
        try:
            m = float(montant)
        except (TypeError, ValueError):
            continue
        if action == "augmenter":
            allocation[cat] += m
        elif action == "diminuer":
            allocation[cat] = max(0.0, allocation[cat] - m)

    return allocation


def _journaliser_snapshot_strategie(
    run_id: str,
    decision: Any,
    profil_effectif: str,
    nb_signaux: int,
    policy: Any,
    mode_global_v5_5: str,
    mode_details_v5_5: Mapping[str, Any] | None,
    allocation_actuelle: Mapping[str, float] | None,
    allocation_simulee: Mapping[str, float] | None,
    scoring_info: Mapping[str, Any] | None,
) -> None:
    payload: Dict[str, Any] = {
        "timestamp": _utc_now_iso(),
        "run_id": run_id,
        "version": VERSION,
        "context": getattr(decision, "context", None) if decision is not None else None,
        "decision_score": getattr(decision, "score", None) if decision is not None else None,
        "profil": profil_effectif,
        "profil_effectif": profil_effectif,
        "nb_signaux": int(nb_signaux),
        "policy": policy if isinstance(policy, Mapping) else policy,
        "mode_global_v5_5": mode_global_v5_5,
    }

    if isinstance(mode_details_v5_5, Mapping):
        fired_levels = (
            mode_details_v5_5.get("triggers", {})
            .get("summary", {})
            .get("fired_levels", [])
        )
        unavailable = (
            mode_details_v5_5.get("triggers", {})
            .get("summary", {})
            .get("unavailable", [])
        )
        payload["mode_details_v5_5"] = {
            "rule_applied": mode_details_v5_5.get("rule_applied"),
            "ai_score_moyen": mode_details_v5_5.get("ai_score_moyen"),
            "fired_levels": fired_levels,
            "unavailable": unavailable,
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
        top3 = scoring_info.get("resultats_top3")
        payload["scoring"] = {
            "solde_reference_usd": float(scoring_info.get("solde_reference_usd", 0.0)),
            "gain_total_journalier_usd": float(scoring_info.get("gain_total_journalier_usd", 0.0)),
            "resultats_top3": top3,
            "profil_scoring": scoring_info.get("profil"),
            "top1": (
                {"label": top3[0][0], "score": top3[0][1], "gain_usd": top3[0][2]}
                if isinstance(top3, list) and len(top3) > 0 and isinstance(top3[0], (list, tuple)) and len(top3[0]) >= 3
                else None
            ),
        }
        if payload["scoring"]["top1"] is None:
            payload["scoring"].pop("top1", None)

    # Journal stratégique dédié (best effort)
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
    except Exception as exc:
        print(f"[WARN] Impossible de journaliser dans journal_strategy.jsonl : {exc}")

    # Journal décisions global (best effort)
    try:
        journaliser_decision(payload)
    except Exception as exc:
        print(f"[WARN] Impossible de journaliser la décision : {exc}")

    # Snapshot complet pour GUI / historique
    try:
        _append_jsonl(STRATEGY_JOURNAL_PATH, payload)
    except Exception as exc:
        print(f"[WARN] Impossible d'écrire le snapshot stratégie : {exc}")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DeFiPilot – Journaliseur continu de signaux")
    parser.add_argument("--pools", required=True, help="Fichier JSON des stats de pools")
    parser.add_argument("--interval", type=int, default=30, help="Intervalle en secondes (défaut: 30)")
    parser.add_argument("--max-loops", type=int, default=0, help="Nombre maximal de boucles (0 = illimité)")
    args = parser.parse_args(argv)

    pools_path = Path(args.pools)
    if not pools_path.exists():
        print(f"[ERROR] Fichier pools introuvable : {pools_path}")
        return 1

    try:
        pools_stats = _charger_pools(pools_path)
    except Exception as exc:
        print(f"[ERROR] Impossible de charger les pools : {exc}")
        return 1

    config, strategy_path = _charger_config_strategy_env()

    etat: Dict[str, Any] = get_state() or {}

    # Lecture wallet (best effort)
    try:
        soldes_wallet = lire_soldes_depuis_env()
        if isinstance(soldes_wallet, Mapping):
            etat.setdefault("soldes_wallet", {}).update(dict(soldes_wallet))
    except Exception as exc:
        print(f"[WARN] Variables d'environnement RPC/wallet manquantes : {exc}")

    interval = max(1, int(args.interval))
    max_loops = int(args.max_loops or 0)

    print("[INFO] Journaliseur continu démarré.")
    print(f"    pools    = {str(pools_path).replace('/', chr(92))}")
    print("    cfg      = (aucune)")
    print(f"    strategy = {strategy_path if strategy_path else '(aucune)'}")
    print(f"    journal  = {str(STRATEGY_JOURNAL_PATH).replace('/', chr(92))}")
    print(f"    interval = {interval}s, max_loops={max_loops}")

    loop_count = 0
    while True:
        loop_count += 1
        run_id = _utc_now_iso()

        print(f"[LOOP] run_id={run_id} (boucle {loop_count})")

        signaux_norm = _charger_signaux_normalises(limit=50)
        nb_signaux = len(signaux_norm)

        signaux_dicts: List[Dict[str, Any]] = []
        for s in signaux_norm:
            if hasattr(s, "to_dict"):
                try:
                    signaux_dicts.append(s.to_dict())  # type: ignore[call-arg]
                    continue
                except Exception:
                    pass
            if isinstance(s, Mapping):
                signaux_dicts.append(dict(s))

        # Contexte + policy
        try:
            decision, profil_effectif = calculer_contexte_et_policy(signaux_norm, config)
        except Exception as exc:
            print(f"[ERROR] Echec de calcul du contexte/policy : {exc}")
            if max_loops and loop_count >= max_loops:
                print("[INFO] Nombre maximal de boucles atteint, arrêt du daemon.")
                break
            time.sleep(interval)
            continue

        context_value = getattr(decision, "context", None) if decision is not None else None
        policy_value = getattr(decision, "policy", None) if decision is not None else None

        # Mode global V5.5
        try:
            mode_global_v5_5, mode_details_v5_5 = determiner_mode_global_v5_5(
                cfg=config,
                contexte=context_value,
                signaux_normalises=signaux_dicts,
                etat=etat,
            )
        except Exception as exc:
            mode_global_v5_5 = "NORMAL"
            mode_details_v5_5 = {"error": str(exc)}

        fired_levels = (
            mode_details_v5_5.get("triggers", {}).get("summary", {}).get("fired_levels", [])
            if isinstance(mode_details_v5_5, Mapping)
            else []
        )
        unavailable = (
            mode_details_v5_5.get("triggers", {}).get("summary", {}).get("unavailable", [])
            if isinstance(mode_details_v5_5, Mapping)
            else []
        )
        rule_applied = mode_details_v5_5.get("rule_applied") if isinstance(mode_details_v5_5, Mapping) else None

        print(
            f"[INFO] mode_global_v5_5={mode_global_v5_5} "
            f"(rule={rule_applied}, fired={len(fired_levels)}, unavailable={len(unavailable)})"
        )

        etat["mode_global_v5_5"] = mode_global_v5_5
        etat["mode_details_v5_5"] = mode_details_v5_5

        allocation_actuelle = _calculer_allocation_categorielle(etat)
        solde_total = float(sum(allocation_actuelle.values()))

        scoring_info = None
        try:
            scoring_info = _calculer_scoring_pools(
                pools_stats=pools_stats,
                profil_nom=str(profil_effectif),
                solde_total_usd=solde_total,
                historique_pools=etat.get("historique_pools"),
            )
            etat["dernier_scoring_pools"] = scoring_info
        except Exception as exc:
            print(f"[WARN] Echec du calcul de scoring des pools : {exc}")

        # Rééquilibrage (signature réelle)
        try:
            _ = generer_plan_reequilibrage_contexte(
                context_label=str(context_value),
                profil_actif=str(profil_effectif),
                allocation_actuelle_usd=dict(allocation_actuelle),
                total_usd=float(solde_total),
                signaux_normalises=signaux_dicts,
                params=dict(config) if isinstance(config, dict) else None,
                run_id=run_id,
                journal_path=str(DECISIONS_JOURNAL_PATH),
            )
        except Exception as exc:
            print(f"[WARN] Impossible de générer le plan de rééquilibrage : {exc}")

        # Calcul allocation simulée après rééquilibrage à partir du dernier plan écrit
        # (best effort : on relit la dernière ligne du fichier decisions)
        allocation_simulee = None
        try:
            if DECISIONS_JOURNAL_PATH.exists():
                last = DECISIONS_JOURNAL_PATH.read_text(encoding="utf-8").strip().splitlines()[-1]
                plan_obj = json.loads(last)
                actions = plan_obj.get("actions")
                if isinstance(actions, list):
                    allocation_simulee = _simuler_allocation_apres_reequilibrage(allocation_actuelle, actions)
                    etat["allocation_simulee_apres_reequilibrage"] = allocation_simulee
        except Exception:
            allocation_simulee = None

        # Snapshot complet stratégie
        _journaliser_snapshot_strategie(
            run_id=run_id,
            decision=decision,
            profil_effectif=str(profil_effectif),
            nb_signaux=nb_signaux,
            policy=policy_value,
            mode_global_v5_5=mode_global_v5_5,
            mode_details_v5_5=mode_details_v5_5 if isinstance(mode_details_v5_5, Mapping) else None,
            allocation_actuelle=allocation_actuelle,
            allocation_simulee=allocation_simulee,
            scoring_info=scoring_info,
        )

        # Save state
        try:
            update_state(etat)
            save_state()
        except Exception as exc:
            print(f"[WARN] Impossible de sauvegarder l'état : {exc}")

        if max_loops and loop_count >= max_loops:
            print("[INFO] Nombre maximal de boucles atteint, arrêt du daemon.")
            break

        time.sleep(interval)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
