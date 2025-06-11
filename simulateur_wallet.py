# simulateur_wallet.py

SOLDE_INITIAL = 1000.0
DUREE_SIMULATION_JOURS = 7

def simuler_investissement(pools):
    """
    Simule un investissement simple (1/3 sur chaque pool) sur une période définie.
    Affiche les gains estimés pour chaque pool et le total.
    """
    montant_par_pool = SOLDE_INITIAL / len(pools)
    gains = []

    print(f"\n🔢 Simulation simple sur {len(pools)} pools")
    for pool in pools:
        apr = pool.get("apr", 0)
        gain = montant_par_pool * (apr / 100) * (DUREE_SIMULATION_JOURS / 365)
        gains.append(gain)
        print(f"➡️ Pool : {pool['plateforme']} | {pool['nom']} | APR : {apr:.2f}% → Gain simulé : {gain:.2f}$")

    total_gain = sum(gains)
    print(f"\n📅 Durée : {DUREE_SIMULATION_JOURS} jours")
    print(f"💰 Gain total estimé : {total_gain:.2f}$")


# Optionnel : exécution directe en test
if __name__ == "__main__":
    # Exemple fictif si exécuté seul
    pools = [
        {"plateforme": "beefy", "nom": "NOICE-WETH", "apr": 138013.21},
        {"plateforme": "spectra-v2", "nom": "STUSD", "apr": 54046.60},
        {"plateforme": "berapaw", "nom": "BULLISHV2", "apr": 28862.79},
    ]
    simuler_investissement(pools)
