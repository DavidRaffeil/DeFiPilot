# strategy.py

from config_loader import get
from profil_loader import charger_profil

def get_filtres_profil():
    """
    Récupère les filtres adaptés au profil actif depuis profil_invest.json.
    """
    nom_profil = get("profil_defaut", "modéré")
    profil_data = charger_profil(nom_profil)

    return {
        "SEUIL_RISK_MAX": profil_data.get("risk", 0.6),
        "TVL_MINIMUM": profil_data.get("tvl_min", 500000)
    }

def should_invest(score, pool, threshold):
    filtres = get_filtres_profil()
    
    if pool.get("risk", 0) > filtres["SEUIL_RISK_MAX"]:
        return False
    if pool.get("tvl", 0) < filtres["TVL_MINIMUM"]:
        return False
    return score >= threshold

def make_decision(pool, score, threshold):
    if should_invest(score, pool, threshold):
        decision = "INVESTIR"
    else:
        decision = "NE PAS investir"
    return {
        "pool": pool["name"],
        "score": score,
        "decision": decision
    }

def afficher_profil():
    nom_profil = get("profil_defaut", "modéré")
    profil_data = charger_profil(nom_profil)

    risk = profil_data.get("risk", "Non défini")
    tvl_min = profil_data.get("tvl_min", "Non défini")

    print(f"🎯 Profil actuel : {nom_profil}")
    print(f"   ▸ Risque maximum autorisé : {risk}")
    print(f"   ▸ TVL minimum acceptée    : {tvl_min}")
