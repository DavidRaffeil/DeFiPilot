# core/config.py

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
