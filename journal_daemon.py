#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from control.control_pilot import lire_signaux_consolides
from core.exits_v5_5 import determiner_exits_v5_5
from core.journal_strategy import journaliser_entree_strategique
from core.market_signals_adapter import calculer_contexte_et_policy
from core.rebalancing import generer_plan_reequilibrage_contexte
from core.scoring import calculer_scores_et_gains, charger_ponderations
from core.signals_normalizer import SignalNormalise, normaliser_signaux
from core.state_manager import get_state, save_state, update_state
from core.strategy_snapshot import journaliser_decision
from core.wallet_reader import lire_soldes_depuis_env

VERSION = "V5.5.0"
DECISIONS_JOURNAL_PATH = Path("data/logs/journal_decisions.jsonl")
STRATEGY_JOURNAL_PATH = Path("data/logs/journal_strategie.jsonl")
StateDict = dict[str, Any]


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _ensure_mapping(obj: Any) -> Mapping[str, Any]:
    return obj if isinstance(obj, Mapping) else {}


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)
        handle.write("\n")


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _normaliser_profil(profil: str | None) -> str:
    if not isinstance(profil, str):
        return "modere"
    texte = profil.strip().lower().replace("é", "e").replace("è", "e")
    if texte not in {"prudent", "modere", "risque"}:
        return "modere"
    return texte


def _determine_profil_effectif(config: Mapping[str, Any], policy: Mapping[str, Any]) -> str:
    for cle in ("profil", "profil_actif", "profil_defaut"):
        val = config.get(cle) if isinstance(config, Mapping) else None
        if isinstance(val, str) and val.strip():
            return _normaliser_profil(val)
    val_policy = policy.get("profil") if isinstance(policy, Mapping) else None
    if isinstance(val_policy, str) and val_policy.strip():
        return _normaliser_profil(val_policy)
    return "modere"


def _calculer_allocation_categorielle(etat: StateDict) -> dict[str, float]:
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
    try:
        signaux_consolides = lire_signaux_consolides(limit=limit, include_ai=True)
    except Exception as exc:
        print(f"[WARN] Impossible de lire les signaux consolidés : {exc}")
        return []

    bruts: list[dict[str, Any]] = []
    for signal in signaux_consolides:
        if hasattr(signal, "to_dict"):
            try:
                bruts.append(signal.to_dict())
                continue
            except Exception:
                pass
        if isinstance(signal, Mapping):
            bruts.append(dict(signal))

    if not bruts:
        return []

    try:
        signaux_norm = normaliser_signaux(bruts)
    except Exception as exc:
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
    actions: list[Mapping[str, Any]],
) -> dict[str, float]:
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
            or _to_float(action.get("montant_usd"))
            or 0.0
        )

        nouvelle_alloc[categorie_norm] = float(nouvelle_alloc.get(categorie_norm, 0.0)) + float(delta)

    return nouvelle_alloc


def _journaliser_snapshot_strategie(
    path: Path,
    run_id: str,
    decision: Any,
    profil_effectif: str,
    policy: Mapping[str, Any] | None,
    allocation_actuelle: Mapping[str, float] | None,
    allocation_simulee: Mapping[str, float] | None,
    scoring_info: Mapping[str, Any] | None,
    nb_signaux: int,
    mode_global: str | None = None,
    exits_info: Mapping[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "run_id": run_id,
        "version": VERSION,
        "context": getattr(decision, "context", None) if decision is not None else None,
        "decision_score": getattr(decision, "score", None) if decision is not None else None,
        "profil": profil_effectif,
        "profil_effectif": profil_effectif,
        "nb_signaux": int(nb_signaux),
        "policy": dict(policy) if isinstance(policy, Mapping) else {},
    }

    if mode_global:
        payload["mode_global_v5_5"] = mode_global

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
            "gain_total_journalier_usd": float(scoring_info.get("gain_total_journalier_usd", 0.0)),
            "resultats_top3": scoring_info.get("resultats_top3"),
            "profil_scoring": scoring_info.get("profil"),
        }

    if isinstance(exits_info, Mapping):
        payload["exits_v5_5"] = dict(exits_info)

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
        print(f"[WARN] Impossible de journaliser la stratégie dans journal_strategy.jsonl : {exc}")

    try:
        journaliser_decision(payload)
    except Exception as exc:
        print(f"[WARN] Impossible de journaliser la décision dans journal_decisions.jsonl : {exc}")

    try:
        _append_jsonl(path, payload)
    except Exception as exc:
        print(f"[WARN] Impossible d'écrire le snapshot stratégie dans {path}: {exc}")


def _charger_config_strategie_env() -> Mapping[str, Any]:
    env_path = os.environ.get("DEFIPILOT_STRATEGY_CFG", "").strip()
    if not env_path:
        return {}
    path = Path(env_path)
    if not path.exists():
        print(f"[WARN] Fichier de configuration stratégie introuvable : {path}")
        return {}
    try:
        cfg_obj = _read_json(path)
        cfg = _ensure_mapping(cfg_obj)
        print(f"[INFO] Configuration stratégie chargée depuis {path}")
        return cfg
    except Exception as exc:
        print(f"[WARN] Impossible de charger la configuration stratégie ({path}) : {exc}")
        return {}


def _initialiser_soldes_wallet(etat: StateDict) -> None:
    try:
        soldes_wallet = lire_soldes_depuis_env()
        if isinstance(soldes_wallet, Mapping):
            etat.setdefault("soldes_wallet", {}).update(dict(soldes_wallet))
            print("[INFO] Soldes wallet chargés depuis l'environnement.")
    except ValueError as exc:
        print(f"[WARN] Variables d'environnement RPC/wallet manquantes : {exc}")
    except Exception as exc:
        print(f"[WARN] Impossible de lire les soldes du wallet : {exc}")


def _extraire_context(decision: Any) -> str:
    if decision is None:
        return "inconnu"
    if isinstance(decision, Mapping):
        ctx_val = decision.get("context")
        if isinstance(ctx_val, str) and ctx_val.strip():
            return ctx_val
    ctx_attr = getattr(decision, "context", None)
    if isinstance(ctx_attr, str) and ctx_attr.strip():
        return ctx_attr
    return "inconnu"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DeFiPilot – Journaliseur continu de signaux")
    parser.add_argument("--pools", required=True, help="Fichier JSON des stats de pools (liste de dicts)")
    parser.add_argument("--cfg", default=None, help="Fichier JSON de configuration (optionnel)")
    parser.add_argument("--interval", type=int, default=30, help="Intervalle en secondes (défaut: 30)")
    parser.add_argument(
        "--max-loops",
        type=int,
        default=0,
        help="Nombre maximal de boucles à exécuter (0 = illimité).",
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
        pools_stats: list[dict[str, Any]] = [p for p in pools_data if isinstance(p, Mapping)]
    elif isinstance(pools_data, Mapping) and isinstance(pools_data.get("pools"), list):
        pools_stats = [p for p in pools_data.get("pools", []) if isinstance(p, Mapping)]
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

    etat: StateDict = get_state() or {}

    env_strategy_cfg = _charger_config_strategie_env()
    if env_strategy_cfg:
        config = {**dict(config), **dict(env_strategy_cfg)}

    _initialiser_soldes_wallet(etat)

    interval = max(1, int(args.interval))
    max_loops = int(args.max_loops or 0)
    loop_count = 0

    strategy_path_str = os.environ.get("DEFIPILOT_STRATEGY_CFG", "").strip()
    strategy_display = strategy_path_str if strategy_path_str else "(aucune)"

    print(
        "[INFO] Journaliseur continu démarré.\n"
        f"    pools    = {pools_path}\n"
        f"    cfg      = {args.cfg or '(aucune)'}\n"
        f"    strategy = {strategy_display}\n"
        f"    journal  = {STRATEGY_JOURNAL_PATH}\n"
        f"    interval = {interval}s, max_loops={max_loops if max_loops else 'illimité'}"
    )

    last_context = etat.get("dernier_contexte") if isinstance(etat, Mapping) else None

    while True:
        loop_count += 1
        run_id = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        print(f"[LOOP] run_id={run_id} (boucle {loop_count})")

        signaux_norm = _charger_signaux_normalises(limit=50)
        nb_signaux = len(signaux_norm)

        try:
            decision, policy = calculer_contexte_et_policy(
                pools_stats,
                dict(config),
                last_context=last_context,
                run_id=run_id,
                version=VERSION,
            )
        except Exception as exc:
            print(f"[ERROR] Echec de calcul du contexte/policy : {exc}")
            time.sleep(interval)
            if max_loops and loop_count >= max_loops:
                break
            continue

        context_value = _extraire_context(decision)
        last_context = context_value

        policy_mapping = dict(policy) if isinstance(policy, Mapping) else {}
        profil_effectif = _determine_profil_effectif(config, policy_mapping)

        mode_global: str | None = None
        for source in (decision, policy_mapping):
            if isinstance(source, Mapping):
                candidate = source.get("mode_global")
            else:
                candidate = getattr(source, "mode_global", None)
            if isinstance(candidate, str) and candidate.strip():
                mode_global = candidate.strip()
                break

        params_for_rebal: dict[str, Any] = dict(config)
        if (
            "mode_global" not in params_for_rebal
            or not isinstance(params_for_rebal.get("mode_global"), str)
            or not str(params_for_rebal.get("mode_global")).strip()
        ):
            params_for_rebal["mode_global"] = "NORMAL"
        if not mode_global:
            mode_global = str(params_for_rebal.get("mode_global", "NORMAL"))

        try:
            exits_info = determiner_exits_v5_5(mode_global_v5_5=mode_global, strategy_cfg=params_for_rebal)
        except Exception as exc:
            print(f"[WARN] Impossible de déterminer exits_v5_5 : {exc}")
            exits_info = None

        if isinstance(exits_info, Mapping) and exits_info.get("exit") is True:
            motif = exits_info.get("motif")
            suffix = f" : {motif}" if isinstance(motif, str) and motif.strip() else ""
            print(f"[EXIT] exits_v5_5 actif{suffix}")

        allocation_actuelle = _calculer_allocation_categorielle(etat)

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

        if isinstance(exits_info, Mapping):
            etat["exits_v5_5"] = dict(exits_info)
        else:
            try:
                etat.pop("exits_v5_5")
            except Exception:
                pass

        signaux_dicts: list[dict[str, Any]] = [dict(s) for s in signaux_norm if isinstance(s, Mapping)]

        try:
            plan_reeq = generer_plan_reequilibrage_contexte(
                context_label=context_value,
                profil_actif=profil_effectif,
                allocation_actuelle_usd=allocation_actuelle,
                total_usd=solde_total,
                signaux_normalises=signaux_dicts,
                params=params_for_rebal,
                run_id=run_id,
                journal_path=str(DECISIONS_JOURNAL_PATH),
            )
        except Exception as exc:
            print(f"[WARN] Impossible de générer le plan de rééquilibrage : {exc}")
            plan_reeq = None

        allocation_simulee = None
        if isinstance(plan_reeq, Mapping):
            actions = plan_reeq.get("actions")
            if isinstance(actions, list):
                allocation_simulee = _simuler_allocation_apres_reequilibrage(
                    allocation_actuelle_usd=allocation_actuelle,
                    actions=actions,
                )
                etat["allocation_simulee_apres_reequilibrage"] = allocation_simulee

        try:
            _journaliser_snapshot_strategie(
                path=STRATEGY_JOURNAL_PATH,
                run_id=run_id,
                decision=decision,
                profil_effectif=profil_effectif,
                policy=policy_mapping,
                allocation_actuelle=allocation_actuelle,
                allocation_simulee=allocation_simulee,
                scoring_info=scoring_info,
                nb_signaux=nb_signaux,
                mode_global=mode_global,
                exits_info=exits_info,
            )
        except Exception as exc:
            print(f"[WARN] Echec de la journalisation du snapshot stratégie : {exc}")

        etat["dernier_contexte"] = context_value
        etat["policy_active"] = policy_mapping
        etat["profil_effectif"] = profil_effectif
        etat["mode_global_v5_5"] = mode_global
        etat["dernier_run_id"] = run_id

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
