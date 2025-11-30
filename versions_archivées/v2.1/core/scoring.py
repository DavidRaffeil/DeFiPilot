#!/usr/bin/env python3
# journal_daemon.py — V5.1.3
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


VERSION = "V5.1.3"
DECISIONS_JOURNAL_PATH = Path("journal_decisions.jsonl")
StateDict = dict[str, Any]


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
    except Exception as exc:
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
        "profil": profil,
        "solde_reference_usd": solde_ref,
        "resultats_top3": resultats_top3,
        "gain_total_journalier_usd": gain_total,
    }
    return scoring_info


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


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée du journaliseur continu de signaux."""
    parser = argparse.ArgumentParser(description="DeFiPilot – Journaliseur continu de signaux")
    parser.add_argument("--pools", required=True, help="Fichier JSON des stats de pools (liste de dicts)")
    parser.add_argument("--cfg", default=None, help="Fichier JSON de configuration (optionnel)")
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
        help="Nombre max d’itérations (0 = infini)",
    )
    parser.add_argument(
        "--journal",
        default="journal_signaux.jsonl",
        help="Chemin du journal JSONL (défaut: journal_signaux.jsonl)",
    )
    args = parser.parse_args(argv)

    pools_path = Path(args.pools)
    cfg_path = Path(args.cfg) if args.cfg else None
    journal_path = args.journal
    interval_s = max(1, int(args.interval))
    max_loops = int(args.max_loops)

    # Chargement de la config (une fois)
    cfg: Mapping[str, Any] = {}
    if cfg_path:
        try:
            cfg = _ensure_mapping(_read_json(cfg_path))
        except Exception as exc:
            print(f"[WARN] Config illisible ({cfg_path}): {exc} — utilisation des paramètres par défaut")
            cfg = {}

    etat: StateDict = get_state()

    contexte_prec = etat.get("contexte_marche")
    if isinstance(contexte_prec, str) and contexte_prec:
        last_context: str | None = contexte_prec
    else:
        last_context = None

    print("[INFO] Journaliseur continu démarré.")
    print(f"       pools   = {pools_path}")
    print(f"       cfg     = {cfg_path if cfg_path else '(aucune)'}")
    print(f"       journal = {journal_path}")
    print(f"       interval= {interval_s}s, max_loops={max_loops or 'infini'}")

    profil_actif_etat = etat.get("profil_actif")
    if not isinstance(profil_actif_etat, str) or not profil_actif_etat:
        profil_actif_etat = "modere"

    contexte_precis = contexte_prec if isinstance(contexte_prec, str) and contexte_prec else "neutre"

    journaux = etat.get("journaux")
    chemin_journal_prec: str | None = None
    if isinstance(journaux, dict):
        journal_signaux = journaux.get("journal_signaux")
        if isinstance(journal_signaux, dict):
            path_prec = journal_signaux.get("path")
            if isinstance(path_prec, str) and path_prec:
                chemin_journal_prec = path_prec

    if chemin_journal_prec is None:
        chemin_journal_prec = str(journal_path)

    print(
        f"[STATE] Profil : {profil_actif_etat} | "
        f"Contexte précédent : {contexte_precis} | "
        f"Journal précédent : {chemin_journal_prec}"
    )

    # Lecture des soldes du wallet (lecture seule) au démarrage
    try:
        tokens_cfg = {
            "USDC": {
                "address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "decimals": 6,
            },
            "WETH": {
                "address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
                "decimals": 18,
            },
        }
        soldes = lire_soldes_depuis_env(tokens_cfg)

        solde_native = soldes.get("native") if isinstance(soldes, Mapping) else None
        solde_usdc = soldes.get("USDC") if isinstance(soldes, Mapping) else None
        solde_weth = soldes.get("WETH") if isinstance(soldes, Mapping) else None

        if isinstance(solde_native, (int, float)):
            native_txt = f"{float(solde_native):.6f}"
        else:
            native_txt = "n/a"

        usdc_val = float(solde_usdc) if isinstance(solde_usdc, (int, float)) else 0.0
        weth_val = float(solde_weth) if isinstance(solde_weth, (int, float)) else 0.0

        print(
            "[BALANCES] "
            f"Native={native_txt} | USDC={usdc_val:.6f} | WETH={weth_val:.6f}"
        )

        total_investi = 0.0
        positions = etat.get("positions")
        if isinstance(positions, list):
            for pos in positions:
                if isinstance(pos, dict):
                    montant = pos.get("montant_investi_usd")
                    if isinstance(montant, (int, float)):
                        total_investi += float(montant)

        print(f"[CHECK] Total investi (état) = {total_investi:.2f} USD")
    except ValueError as exc:
        print(f"[WARN] Impossible de lire les soldes du wallet : {exc}")
        total_investi = 0.0
    except Exception as exc:
        print(f"[WARN] Erreur inattendue lors de la lecture des soldes : {exc}")
        total_investi = 0.0

    loop_idx = 0

    while True:
        loop_idx += 1

        # Chargement des pools à chaque itération (pour prendre en compte un fichier mis à jour)
        try:
            pools_obj = _read_json(pools_path)
            if not isinstance(pools_obj, list):
                raise ValueError("Le fichier pools doit contenir une liste de dictionnaires JSON.")
            pools_stats = [x for x in pools_obj if isinstance(x, dict)]
            # Le scoring des pools est calculé plus bas via _calculer_scoring_pools().
        except Exception as exc:
            print(f"[ERROR] Impossible de lire pools ({pools_path}) : {exc}")
            time.sleep(interval_s)
            continue

        run_id = "journal_daemon-" + datetime.now(timezone.utc).isoformat(
            timespec="seconds"
        ).replace("+00:00", "Z")

        # 1) Calcul du contexte et de la policy à partir des pools
        try:
            decision, policy = calculer_contexte_et_policy(
                pools_stats=pools_stats,
                cfg=dict(cfg),
                last_context=last_context,
                run_id=run_id,
                version=VERSION,
                journal_path=journal_path,
            )
        except Exception as exc:
            print(f"[ERROR] Échec du calcul stratégie: {exc}")
            time.sleep(interval_s)
            continue

        last_context = decision.context

        # 2) Chargement des signaux normalisés pour le rééquilibrage (V5.1.2)
        signaux_norm = _charger_signaux_normalises(limit=50)

        # 3) Mise à jour de l'état global
        updates: StateDict = {}
        updates["contexte_marche"] = decision.context

        profil_cfg = cfg.get("profil_actif") if isinstance(cfg, Mapping) else None
        if isinstance(profil_cfg, str) and profil_cfg:
            updates["profil_actif"] = profil_cfg
        else:
            profil_state = etat.get("profil_actif")
            if isinstance(profil_state, str) and profil_state:
                updates["profil_actif"] = profil_state
            else:
                updates["profil_actif"] = "modere"

        journaux_etat = etat.get("journaux")
        if isinstance(journaux_etat, dict):
            journaux_local = dict(journaux_etat)
        else:
            journaux_local = {}
        journal_signaux_etat = journaux_local.get("journal_signaux")
        if isinstance(journal_signaux_etat, dict):
            journal_signaux_local = dict(journal_signaux_etat)
        else:
            journal_signaux_local = {}
        journal_signaux_local["path"] = str(journal_path)
        journaux_local["journal_signaux"] = journal_signaux_local
        updates["journaux"] = journaux_local

        allocation_actuelle_usd = _calculer_allocation_categorielle(etat)

        cfg_profil = cfg.get("profil_actif") if isinstance(cfg, Mapping) else None
        if isinstance(cfg_profil, str) and cfg_profil.strip():
            profil_effectif = cfg_profil.strip()
        else:
            profil_state_eff = updates.get("profil_actif") or etat.get("profil_actif")
            if isinstance(profil_state_eff, str) and profil_state_eff:
                profil_effectif = profil_state_eff
            else:
                profil_effectif = "modere"

        # 4) Calcul du scoring des pools (V5.1.3)
        try:
            scoring_info = _calculer_scoring_pools(
                pools_stats=pools_stats,
                profil_nom=profil_effectif,
                solde_total_usd=total_investi,
                historique_pools=etat.get("historique_pools"),
            )
        except Exception as exc:
            print(f"[WARN] Scoring des pools impossible : {exc}")
        else:
            updates["dernier_scoring_pools"] = scoring_info

        # 5) Génération du plan de rééquilibrage « contexte + signaux normalisés »
        try:
            plan_reeq = generer_plan_reequilibrage_contexte(
                context_label=decision.context,
                profil_actif=profil_effectif,
                allocation_actuelle_usd=allocation_actuelle_usd,
                total_usd=None,
                signaux_normalises=signaux_norm or None,
                params={"mode_simulation": True},
                run_id=run_id,
                journal_path="journal_rebalancing.jsonl",
            )
        except Exception as exc:
            print(f"[WARN] Rééquilibrage simulé impossible : {exc}")
        else:
            updates["dernier_plan_reequilibrage"] = plan_reeq
            actions = plan_reeq.get("actions")
            if isinstance(actions, list) and actions:
                print(f"[REEQ] {len(actions)} action(s) de rééquilibrage proposées.")
            else:
                print("[REEQ] Aucune action de rééquilibrage proposée.")

            _journaliser_decisions(
                plan=plan_reeq,
                run_id=run_id,
                context=decision.context,
                profil=profil_effectif,
                mode="simulation",
            )

        # 6) Sauvegarde de l'état
        etat = update_state(updates)

        try:
            save_state()
        except Exception as exc:
            print(f"[WARN] Impossible de sauvegarder l'état : {exc}")

        print(
            f"[OK] #{loop_idx} {decision.context} "
            f"(score={decision.score:.4f}) "
            f"→ run_id={run_id}"
        )

        if max_loops > 0 and loop_idx >= max_loops:
            print("[INFO] Limite max_loops atteinte, arrêt propre.")
            break

        time.sleep(interval_s)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
