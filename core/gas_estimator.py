# ✅ Module d’estimation de gas à partir de config.json

import json
import os

CONFIG_PATH = "config.json"

def charger_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError("Le fichier config.json est introuvable")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def estimer_cout_gas(operation: str, reseau: str) -> float:
    """
    Estime le coût en $ de gas pour une opération donnée sur un réseau donné.

    :param operation: "swap" ou "add_liquidity"
    :param reseau: "polygon" ou "ethereum"
    :return: coût estimé en USD
    """
    config = charger_config()
    try:
        return config["gas_simulation"][operation][reseau]
    except KeyError:
        raise ValueError(f"Paramètre gas_simulation manquant pour {operation} sur {reseau}")

# Exemple d'utilisation
if __name__ == "__main__":
    print("Swap sur Polygon :", estimer_cout_gas("swap", "polygon"), "$")
    print("Ajout de liquidité sur Ethereum :", estimer_cout_gas("add_liquidity", "ethereum"), "$")
