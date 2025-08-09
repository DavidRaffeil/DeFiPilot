# main.py – V3.2
# Intégration : risk_analysis.analyser_risque + journal.enregistrer_pools_risquées
# Objectif : conserver les sorties existantes et ajouter la journalisation des pools risquées.

import sys
import os
from datetime import datetime

# ────────────────────────────────────────────────────────────────────────────────
# Imports robustes (garde-fous sur noms/chemins)
# ────────────────────────────────────────────────────────────────────────────────
def _safe_import_profil():
    """
    Essaie d'importer le profil depuis core.config puis core.profil.
    Doit fournir :
      - PROFILS : dict des profils
      - PROFIL_ACTIF (str) ou get_profil_actif() -> str
    """
    profils, actif = None, None
    try:
        # cas 1 : core.config
        from core.config import PROFILS as _PROFILS
        profils = _PROFILS
        try:
            from core.config import PROFIL_ACTIF as _ACTIF
            actif = _ACTIF
        except Exception:
            pass
        try:
            from core.config import get_profil_actif as _get
            actif = actif or _get()
        except Exception:
            pass
    except Exception:
        pass

    if profils is None:
        try:
            # cas 2 : core.profil
            from core.profil import PROFILS as _PROFILS
            profils = _PROFILS
            try:
                from core.profil import PROFIL_ACTIF as _ACTIF
                actif = _ACTIF
            except Exception:
                pass
            try:
                from core.profil import get_profil_actif as _get
                actif = actif or _get()
            except Exception:
                pass
        except Exception:
            pass

    # Défaut raisonnable
    if profils is None:
        profils = {
            "modere": {"nom": "modere", "ponderations": {"apr": 0.3, "tvl": 0.7}}
        }
    if not actif:
        actif = "modere"
    return profils, actif


def _safe_import_pools_fetcher():
    """
    Essaie d'importer la récupération des pools depuis DefiLlama.
    Cherche d'abord core.defi_sources.defillama, sinon core.defillama.
    Attend une fonction 'recuperer_pools' (signature libre).
    """
    fetcher = None
    tried = []
    for mod_name in (
        "core.defi_sources.defillama",
        "core.defillama",
        "defillama",
    ):
        try:
            mod = __import__(mod_name, fromlist=["*"])
            if hasattr(mod, "recuperer_pools"):
                fetcher = getattr(mod, "recuperer_pools")
                return fetcher
            elif hasattr(mod, "get_pools"):
                fetcher = getattr(mod, "get_pools")
                return fetcher
            else:
                tried.append(mod_name)
        except Exception:
            tried.append(mod_name)
            continue
    return None


def _safe_import_scoring():
    """
    Essaie d’importer les fonctions de scoring/simulation.
    Retourne (calculer_score_pool, simuler_gains) — chacun peut être None.
    """
    calc, simu = None, None
    try:
        from core.scoring import calculer_score_pool as _calc
        calc = _calc
    except Exception:
        try:
            from core.scoring import calcul_score_pool as _calc2
            calc = _calc2
        except Exception:
            calc = None
    try:
        from core.scoring import simuler_gains as _sim
        simu = _sim
    except Exception:
        simu = None
    return calc, simu


def _safe_import_risk():
    """
    Importe analyser_risque depuis risk_analysis.py
    """
    try:
        from risk_analysis import analyser_risque
        return analyser_risque
    except Exception:
        pass
    try:
        from core.risk_analysis import analyser_risque
        return analyser_risque
    except Exception:
        return None


def _safe_import_journal():
    """
    Importe les fonctions de journalisation nécessaires.
    """
    enregistrer_top3 = None
    journaliser_scores = None
    enregistrer_pools_risquees = None

    try:
        from core.journal import enregistrer_top3 as _top3
        enregistrer_top3 = _top3
    except Exception:
        pass
    try:
        from core.journal import journaliser_scores as _scores
        journaliser_scores = _scores
    except Exception:
        pass
    # Attention : nom avec accent dans le code existant
    try:
        from core.journal import enregistrer_pools_risquées as _risques
        enregistrer_pools_risquees = _risques
    except Exception:
        # fallback sans accent, au cas où
        try:
            from core.journal import enregistrer_pools_risquees as _risques2
            enregistrer_pools_risquees = _risques2
        except Exception:
            pass

    return enregistrer_top3, journaliser_scores, enregistrer_pools_risquees


# ────────────────────────────────────────────────────────────────────────────────
# Utilitaires
# ────────────────────────────────────────────────────────────────────────────────
def _fmt_date_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def _afficher_entete(profil_nom: str, profil_data: dict):
    today = datetime.now()
    print("🚀 Lancement de DeFiPilot")
    apr_w = profil_data.get("ponderations", {}).get("apr", 0.3)
    tvl_w = profil_data.get("ponderations", {}).get("tvl", 0.7)
    print(f"[{_fmt_date_iso(today)}] INFO 🏗 Profil actif : {profil_nom} (APR {apr_w}, TVL {tvl_w})")


def _nom_pool_court(pool: dict) -> str:
    # Ex : "uniswap | USDC-ETH" ou "plateforme | nom"
    plateforme = pool.get("platform") or pool.get("plateforme") or "?"
    nom = (
        pool.get("nom")
        or pool.get("name")
        or pool.get("pair")
        or f"{pool.get('token0', '?')}-{pool.get('token1', '?')}"
    )
    return f"{plateforme} | {nom}"


def _gain_simule_usdc(pool: dict, simuler_gains_fn):
    """
    Retourne un float 'gain simulé' si possible, sinon 0.0
    """
    try:
        if callable(simuler_gains_fn):
            val = simuler_gains_fn(pool)  # V3.3 : appelé sans paramètre supplémentaire
            if isinstance(val, (int, float)):
                return float(val)
            # si la fn renvoie un dict
            if isinstance(val, dict):
                for k in ("gain_usdc", "gain", "gain_simule"):
                    if k in val and isinstance(val[k], (int, float)):
                        return float(val[k])
        # fallback simple si pas de fonction
        apr = float(pool.get("apr", 0) or 0)
        tvl = float(pool.get("tvl_usd", pool.get("tvl", 0)) or 0)
        # Simple proxy : gain ~ APR (en %) * échelle fixe (arbitraire pour affichage)
        return round(apr / 100 * 27, 2) if (apr > 0) else 0.0
    except Exception:
        return 0.0


def _score(pool: dict, profil: dict, calculer_score_fn):
    if callable(calculer_score_fn):
        try:
            return float(calculer_score_fn(pool, profil))
        except Exception:
            pass
    # Fallback : score pondéré simple
    apr = float(pool.get("apr", 0) or 0)
    tvl = float(pool.get("tvl_usd", pool.get("tvl", 0)) or 0)
    w_apr = float(profil.get("ponderations", {}).get("apr", 0.3))
    w_tvl = float(profil.get("ponderations", {}).get("tvl", 0.7))
    return apr * w_apr + tvl * w_tvl


# ────────────────────────────────────────────────────────────────────────────────
# Programme principal
# ────────────────────────────────────────────────────────────────────────────────
def main():
    # Profils
    PROFILS, PROFIL_ACTIF = _safe_import_profil()
    profil_nom = PROFIL_ACTIF if isinstance(PROFIL_ACTIF, str) else "modere"
    profil = PROFILS.get(profil_nom, {"nom": profil_nom, "ponderations": {"apr": 0.3, "tvl": 0.7}})
    profil["nom"] = profil.get("nom", profil_nom)

    _afficher_entete(profil_nom, profil)

    # Récupération des pools
    fetch_pools = _safe_import_pools_fetcher()
    if not callable(fetch_pools):
        print("[INFO] 🧪 Récupération des pools via DefiLlama (fallback)")
        pools = []
    else:
        print("[INFO] 🧪 Récupération des pools via DefiLlama")
        try:
            # Essaye avec profil si la signature le permet
            try:
                pools = fetch_pools(profil)
            except TypeError:
                pools = fetch_pools()
        except Exception:
            pools = []

    print(f"[{_fmt_date_iso(datetime.now())}] INFO ✅ {len(pools)} pools récupérées")

    # Scoring & Simulation
    calculer_score_fn, simuler_gains_fn = _safe_import_scoring()
    analyser_risque = _safe_import_risk()
    enreg_top3, journal_scores, enreg_risque = _safe_import_journal()

    # Calcul score, gain, risque
    for pool in pools:
        # 1) score
        score_val = _score(pool, profil, calculer_score_fn)
        pool["score"] = score_val

        # Log style déjà observé (si fn scoring affiche déjà, ça fera doublon visuel, mais non bloquant)
        try:
            plateforme = pool.get("platform") or pool.get("plateforme") or "?"
            nom = pool.get("nom") or pool.get("name") or pool.get("pair") or f"{pool.get('token0', '?')}-{pool.get('token1', '?')}"
            apr = float(pool.get("apr", 0) or 0)
            tvl = float(pool.get("tvl_usd", pool.get("tvl", 0)) or 0)
            w_apr = float(profil.get("ponderations", {}).get("apr", 0.3))
            w_tvl = float(profil.get("ponderations", {}).get("tvl", 0.7))
            score_brut = apr * w_apr + tvl * w_tvl
            bonus_pct = 0.0
            if score_brut:
                bonus_pct = ((score_val / score_brut) - 1.0) * 100.0
            print(f"[SCORE] {plateforme} | {nom} | Score base : {round(score_brut, 2)} | Bonus : {round(bonus_pct, 1)}% → Score final : {round(score_val, 2)}")
        except Exception:
            pass

        # 2) gain simulé
        pool["gain_simule_usdc"] = _gain_simule_usdc(pool, simuler_gains_fn)

        # 3) analyse de risque
        if callable(analyser_risque):
            try:
                analyser_risque(pool)
            except Exception:
                # en cas d'erreur, on n'interrompt pas
                pass

    # Tri par score décroissant
    pools_sorted = sorted(pools, key=lambda p: float(p.get("score", 0) or 0), reverse=True)

    # Affichage résumé (comme tes runs)
    for pool in pools_sorted:
        apr = float(pool.get("apr", 0) or 0)
        nom_simple = _nom_pool_court(pool).split(" | ")[1]
        gain = float(pool.get("gain_simule_usdc", 0.0))
        print(f"  • {nom_simple} | APR : {apr:.2f}% | Gain simulé : {gain:.2f} $ USDC")

    # Journalisations
    date_iso = _fmt_date_iso(datetime.now())

    # Top3
    if pools_sorted and callable(enreg_top3):
        top3 = []
        for p in pools_sorted[:3]:
            nom_simple = _nom_pool_court(p)
            apr = float(p.get("apr", 0) or 0)
            gain = float(p.get("gain_simule_usdc", 0.0))
            top3.append((nom_simple, apr, gain))
        try:
            enreg_top3(date_iso, top3, profil.get("nom", profil_nom))
        except Exception:
            pass

    # Scores détaillés
    if pools_sorted and callable(journal_scores):
        try:
            journal_scores(date_iso, profil, pools_sorted, historique_pools=[])
        except Exception:
            pass

    # Pools risquées (NOUVEAU)
    if pools_sorted and callable(enreg_risque):
        try:
            enreg_risque(pools_sorted, date_iso, profil.get("nom", profil_nom))
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
