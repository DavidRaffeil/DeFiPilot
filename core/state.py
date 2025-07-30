# core/state.py

"""Gestion de l'état persistant de DeFiPilot."""

import json
import os

from core import logger


def etat_existe(filename: str = "defipilot.state") -> bool:
    """Vérifie si le fichier d'état existe."""
    existe = os.path.exists(filename)
    if existe:
        logger.log_info(f"🗄️ Fichier d'état détecté : {filename}")
    else:
        logger.log_warning(f"❌ Aucun fichier d'état trouvé : {filename}")
    return existe


def charger_etat(filename: str = "defipilot.state") -> dict:
    """Charge le fichier d'état JSON et le retourne."""
    if not os.path.exists(filename):
        logger.log_warning(f"🔍 Aucun état sauvegardé dans {filename}")
        return {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            state = json.load(f)
        logger.log_succes(f"📥 État chargé depuis {filename}")
        return state
    except Exception as exc:
        logger.log_erreur(f"Erreur lors du chargement de l'état : {exc}")
        return {}


def sauvegarder_etat(state: dict, filename: str = "defipilot.state") -> None:
    """Enregistre le dictionnaire d'état au format JSON."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        logger.log_succes(f"💾 État sauvegardé dans {filename}")
    except Exception as exc:
        logger.log_erreur(f"Erreur lors de la sauvegarde de l'état : {exc}")
