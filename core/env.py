import os
from pathlib import Path


def load_env(path: str = ".env") -> dict:
    """Charge les variables d'environnement depuis un fichier .env et les retourne.

    Parameters
    ----------
    path : str
        Chemin vers le fichier .env, par défaut ".env".

    Returns
    -------
    dict
        Dictionnaire contenant les variables d'environnement utiles.
    """
    env_data: dict[str, str] = {}
    env_path = Path(path)
    if env_path.exists():
        with env_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_data[key.strip()] = value.strip().strip("'\"")

    env_vars = {
        "mode": os.getenv("MODE", env_data.get("MODE", "SIMULATEUR")),
        "wallet_address": os.getenv("WALLET_ADDRESS", env_data.get("WALLET_ADDRESS", "")),
        "private_key": os.getenv("PRIVATE_KEY", env_data.get("PRIVATE_KEY", "")),
        "max_invest": os.getenv("MAX_INVEST", env_data.get("MAX_INVEST", "")),
    }
    return env_vars