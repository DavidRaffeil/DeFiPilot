# core/config.py – V3.8
import json
import os
from pathlib import Path

# === Chargement configuration utilisateur ===
def charger_config():
    """
    Charge la configuration depuis config.json si présent.
    Sinon retourne les valeurs par défaut.
    """
    chemin = Path("config.json")
    if chemin.is_file():
        with chemin.open("r", encoding="utf-8") as f:
            return json.load(f)

    # Valeurs par défaut si config.json absent
    return {
        "profil_defaut": "modere",
        "dry_run": True,
    }

# === Profils d’investissement ===
PROFILS = {
    "prudent": {
        "apr": 0.2,
        "tvl": 0.8,
        "historique_max_bonus": 0.10,
        "historique_max_malus": -0.05,
        "poids_slippage": 0.5,
    },
    "modere": {
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

# === Chargement unique de la configuration ===
_config = charger_config()

# Variables globales exportées
PROFIL_ACTIF = _config.get("profil_defaut", "modere")
SWAP_REEL = not _config.get("dry_run", True)

# Activation IA – pondération dynamique (désactivée en V3.3)
AI_PONDERATION_ACTIVE = False

# Journaux spécifiques à l’ajout de liquidité (V3.8)
JOURNAL_LIQUIDITY_CSV = "logs/liquidity.csv"
JOURNAL_LIQUIDITY_JSONL = "logs/liquidity.jsonl"
