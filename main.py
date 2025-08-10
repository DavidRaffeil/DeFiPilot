# main.py – V3.5
# Intégration : core.journal_wallet (init_logs, log_wallet_action, log_wallet_balance)
# Conserver le flux existant ; ajouts discrets et robustes.

from __future__ import annotations

import sys
import os
import logging
from datetime import datetime
from typing import Any, Callable, Tuple

# Journal wallet (obligatoire à cette version)
from core.journal_wallet import init_logs, log_wallet_action, log_wallet_balance

# Wallet réel optionnel (adresse uniquement si dispo)
try:
    from core.real_wallet import get_wallet_address  # type: ignore
except Exception:  # pragma: no cover
    get_wallet_address = None  # type: ignore

# ────────────────────────────────────────────────────────────────────────────────
# Utilitaires d’affichage
# ────────────────────────────────────────────────────────────────────────────────

def _fmt_date_iso(dt: datetime | None = None) -> str:
    dt = dt or datetime.now()
    return dt.strftime("%Y-%m-%d")


def _afficher_entete(profil_nom: str, profil: dict) -> None:
    print("🚀 Lancement de DeFiPilot")
    print(f"[{_fmt_date_iso(datetime.now())}] INFO 🏗 Profil actif : {profil_nom} (APR {profil.get('ponderations',{}).get('apr',0.3)}, TVL {profil.get('ponderations',{}).get('tvl',0.7)})")

# ────────────────────────────────────────────────────────────────────────────────
# Imports robustes (garde-fous sur noms/chemins)
# ────────────────────────────────────────────────────────────────────────────────

def _safe_import_profil() -> Tuple[dict, str]:
    """
    Essaie d’importer le profil depuis core.config puis core.profil.
    Doit fournir :
      - PROFILS : dict des profils
      - PROFIL_ACTIF (str) ou get_profil_actif() -> str
    """
    profils, actif = None, None
    try:
        # cas 1 : core.config
        from core.config import PROFILS as _PROFILS  # type: ignore
        profils = _PROFILS
        try:
            from core.config import PROFIL_ACTIF as _ACTIF  # type: ignore
            actif = _ACTIF
        except Exception:
            pass
        try:
            from core.config import get_profil_actif as _get  # type: ignore
            actif = actif or _get()
        except Exception:
            pass
    except Exception:
        pass

    if not profils:
        try:
            # cas 2 : core.profil (fallback historique)
            from core.profil import PROFILS as _PROFILS  # type: ignore
            profils = _PROFILS
            try:
                from core.profil import PROFIL_ACTIF as _ACTIF  # type: ignore
                actif = _ACTIF
            except Exception:
                pass
        except Exception:
            profils = {"modere": {"nom": "modere", "ponderations": {"apr": 0.3, "tvl": 0.7}}}

    actif_str = actif if isinstance(actif, str) else "modere"
    return profils, actif_str


def _safe_import_pools_fetcher() -> Callable[..., list] | None:
    try:
        # Emplacement actuel du projet
        from core.defi_sources.defillama import fetch_pools  # type: ignore
        return fetch_pools
    except Exception:
        try:
            # Fallback ancien nom
            from core.defillama import fetch_pools  # type: ignore
            return fetch_pools
        except Exception:
            return None


def _safe_import_scoring() -> Tuple[Callable[[dict, dict], float] | None, Callable[[dict, dict], float] | None]:
    calculer_score_fn = None
    simuler_gains_fn = None
    try:
        from core.scoring import calculer_score as _calc  # type: ignore
        calculer_score_fn = _calc
    except Exception:
        pass
    try:
        from core.scoring import simuler_gains as _sim  # type: ignore
        simuler_gains_fn = _sim
    except Exception:
        pass
    return calculer_score_fn, simuler_gains_fn


def _safe_import_risk() -> Callable[[dict], dict] | None:
    try:
        from risk_analysis import analyser_risque  # type: ignore
        return analyser_risque
    except Exception:
        try:
            from core.risk_analysis import analyser_risque  # type: ignore
            return analyser_risque
        except Exception:
            return None


def _safe_import_journal() -> Tuple[Callable[..., None] | None, Callable[..., None] | None, Callable[..., None] | None]:
    enreg_top3 = None
    journal_scores = None
    enreg_risque = None
    try:
        from core.journal import enregistrer_top3 as _top3  # type: ignore
        enreg_top3 = _top3
    except Exception:
        pass
    try:
        from core.journal import journaliser_scores as _js  # type: ignore
        journal_scores = _js
    except Exception:
        pass
    try:
        from core.journal import enregistrer_pools_risquées as _jr  # type: ignore
        enreg_risque = _jr
    except Exception:
        pass
    return enreg_top3, journal_scores, enreg_risque

# ────────────────────────────────────────────────────────────────────────────────
# Calculs de secours
# ────────────────────────────────────────────────────────────────────────────────

def _score(pool: dict, profil: dict, calculer_score_fn: Callable[[dict, dict], float] | None) -> float:
    if callable(calculer_score_fn):
        try:
            return float(calculer_score_fn(pool, profil))
        except Exception:
            pass
    # Fallback simple : pondération APR/TVL
    apr = float(pool.get("apr", 0) or 0)
    tvl = float(pool.get("tvl_usd", pool.get("tvl", 0)) or 0)
    w_apr = float(profil.get("ponderations", {}).get("apr", 0.3))
    w_tvl = float(profil.get("ponderations", {}).get("tvl", 0.7))
    return apr * w_apr + tvl * w_tvl


def _nom_pool_court(p: dict) -> str:
    plat = str(p.get("platform", p.get("plateforme", "?")))
    t0 = str(p.get("token0", p.get("base", "?")))
    t1 = str(p.get("token1", p.get("quote", "?")))
    return f"{plat} | {t0}-{t1}"

# ────────────────────────────────────────────────────────────────────────────────
# Programme principal
# ────────────────────────────────────────────────────────────────────────────────

def main() -> None:
    # Profil actif
    PROFILS, PROFIL_ACTIF = _safe_import_profil()
    profil_nom = PROFIL_ACTIF if isinstance(PROFIL_ACTIF, str) else "modere"
    profil = PROFILS.get(profil_nom, {"nom": profil_nom, "ponderations": {"apr": 0.3, "tvl": 0.7}})
    profil["nom"] = profil.get("nom", profil_nom)

    _afficher_entete(profil_nom, profil)

    # Journal wallet (début de run)
    init_logs()
    log_wallet_action(action="run_start", notes="début exécution DeFiPilot")

    # Récupération des pools
    fetch_pools = _safe_import_pools_fetcher()
    if not callable(fetch_pools):
        print("[INFO] 🧪 Récupération des pools via DefiLlama (fallback)")
        pools: list[dict] = []
    else:
        print("[INFO] 🧪 Récupération des pools via DefiLlama")
        try:
            try:
                pools = fetch_pools(profil)  # certains fetchers acceptent le profil
            except TypeError:
                pools = fetch_pools()
        except Exception:
            pools = []

    print(f"[{_fmt_date_iso(datetime.now())}] INFO ✅ {len(pools)} pools récupérées")

    # Scoring / gains / risque
    calculer_score_fn, simuler_gains_fn = _safe_import_scoring()
    analyser_risque = _safe_import_risk()
    enreg_top3, journal_scores, enreg_risque = _safe_import_journal()

    for pool in pools:
        # Score
        try:
            s = _score(pool, profil, calculer_score_fn)
            pool["score"] = float(s)
        except Exception:
            pool["score"] = 0.0
        # Gains simulés
        if callable(simuler_gains_fn):
            try:
                pool["gain_simule_usdc"] = float(simuler_gains_fn(pool, profil))
            except Exception:
                pool["gain_simule_usdc"] = 0.0
        # Risque
        if callable(analyser_risque):
            try:
                analyser_risque(pool)  # ajoute champs "risque" et "raisons_risque"
            except Exception:
                pass

        # Affichage score (style historique)
        plat = str(pool.get("platform", pool.get("plateforme", "?")))
        pair = f"{pool.get('token0','?')}-{pool.get('token1','?')}"
        print(f"[SCORE] {plat} | {pair} | Score : {pool.get('score',0)}")

    # Tri scores
    pools_sorted = sorted(pools, key=lambda x: float(x.get("score", 0.0)), reverse=True) if pools else []

    # Résumé TOP 3 (affichage + journal optionnel)
    date_iso = _fmt_date_iso(datetime.now())
    if pools_sorted:
        print()  # espace visuel
        for p in pools_sorted[:3]:
            nom_simple = _nom_pool_court(p)
            apr = float(p.get("apr", 0) or 0)
            gain = float(p.get("gain_simule_usdc", 0.0))
            print(f"  • {nom_simple} | APR : {apr:.2f}% | Gain simulé : {gain:.2f} $ USDC")
        try:
            if callable(enreg_top3):
                top3 = []
                for p in pools_sorted[:3]:
                    nom_simple = _nom_pool_court(p)
                    apr = float(p.get("apr", 0) or 0)
                    gain = float(p.get("gain_simule_usdc", 0.0))
                    top3.append((nom_simple, apr, gain))
                enreg_top3(date_iso, top3, profil.get("nom", profil_nom))
        except Exception:
            pass

    # Scores détaillés (journal)
    if pools_sorted and callable(journal_scores):
        try:
            journal_scores(date_iso, profil, pools_sorted, historique_pools=[])
        except Exception:
            pass

    # Pools risquées (journal)
    if pools_sorted and callable(enreg_risque):
        try:
            enreg_risque(pools_sorted, date_iso, profil.get("nom", profil_nom))
        except Exception:
            pass

    # Fin de run + snapshot optionnel
    log_wallet_action(action="run_end", notes="fin exécution DeFiPilot")

    wallet_address = get_wallet_address() if callable(get_wallet_address) else None
    chain_name = os.getenv("CHAIN_NAME", "polygon")
    if wallet_address:
        try:
            log_wallet_balance(wallet=wallet_address, chain=chain_name, balances={}, notes="snapshot fin de run")
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
