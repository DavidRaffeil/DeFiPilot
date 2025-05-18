# strategy.py

from config import THRESHOLD_SCORE
from settings import PROFIL_INVESTISSEUR

def get_filtres_profil():
    """
    Retourne les filtres adaptés au profil sélectionné.
    """
    if PROFIL_INVESTISSEUR == "prudent":
        return {
            "SEUIL_RISK_MAX": 0.3,
            "TVL_MINIMUM": 1_000_000
        }
    elif PROFIL_INVESTISSEUR == "agressif":
        return {
            "SEUIL_RISK_MAX": 0.8,
            "TVL_MINIMUM": 200_000
        }
    else:  # modéré par défaut
        return {
            "SEUIL_RISK_MAX": 0.6,
            "TVL_MINIMUM": 500_000
        }

def should_invest(score, pool, threshold=THRESHOLD_SCORE):
    filtres = get_filtres_profil()
    
    if pool["risk"] > filtres["SEUIL_RISK_MAX"]:
        return False
    if pool["tvl"] < filtres["TVL_MINIMUM"]:
        return False
    return score >= threshold

def make_decision(pool, score, threshold=THRESHOLD_SCORE):
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
    filtres = get_filtres_profil()
    print(f"🎯 Profil actuel : {PROFIL_INVESTISSEUR}")
    print(f"   ▸ Risque maximum autorisé : {filtres['SEUIL_RISK_MAX']}")
    print(f"   ▸ TVL minimum acceptée    : {filtres['TVL_MINIMUM']}")
