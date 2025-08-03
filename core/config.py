# core/config.py
# 🧩 Version : V2.8 – Étape 2
# 🎯 Ajout du champ `poids_slippage` dans les profils + export PROJETS

def charger_config():
    config = {
        "seuil_invest": 30000,         # Seuil de score minimum pour investir
        "slippage_simule": 0.005,      # Slippage simulé (0.5 %)
        "nombre_max_invest": 3,        # Nombre max de pools actives
        "profil_defaut": "modere",     # ⚠️ Sans accent !
        "dry_run": True,               # Mode simulation activé
        "gas_simulation": {},          # Paramètres de simulation du gas (à compléter dans V2.5)
        "network": "polygon"           # Réseau par défaut (Polygon)
    }
    return config


# Pondérations des différents profils utilisateurs
PROFILS = {
    "prudent": {
        "apr": 0.2,
        "tvl": 0.8,
        "historique_max_bonus": 0.10,
        "historique_max_malus": -0.05,
        "poids_slippage": 0.9,
    },
    "modere": {
        "apr": 0.3,
        "tvl": 0.7,
        "historique_max_bonus": 0.15,
        "historique_max_malus": -0.10,
        "poids_slippage": 0.5,
    },
    "equilibre": {
        "apr": 0.5,
        "tvl": 0.5,
        "historique_max_bonus": 0.20,
        "historique_max_malus": -0.10,
        "poids_slippage": 0.3,
    },
    "dynamique": {
        "apr": 0.7,
        "tvl": 0.3,
        "historique_max_bonus": 0.25,
        "historique_max_malus": -0.15,
        "poids_slippage": 0.2,
    },
    "agressif": {
        "apr": 0.8,
        "tvl": 0.2,
        "historique_max_bonus": 0.30,
        "historique_max_malus": -0.20,
        "poids_slippage": 0.1,
    },
}

# 🔁 Rend la variable PROFILS accessible depuis les autres modules
PROFILS = PROFILS
