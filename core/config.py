# core/config.py
# 🧩 Version : V3.2 – Chargement dynamique + export des variables globales

def charger_config():
    config = {
        "seuil_invest": 30000,
        "slippage_simule": 0.005,
        "nombre_max_invest": 3,
        "profil_defaut": "modere",  # ⚠️ Sans accent
        "dry_run": True,
        "gas_simulation": {},
        "network": "polygon"
    }
    return config

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

# Chargement unique de la configuration
_config = charger_config()

# Variables globales exportées
PROFIL_ACTIF = _config["profil_defaut"]
SWAP_REEL = not _config["dry_run"]

# Activation IA – pondération dynamique
AI_PONDERATION_ACTIVE = True
