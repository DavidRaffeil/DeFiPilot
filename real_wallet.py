# real_wallet.py
from dotenv import load_dotenv
import os

# Charger les variables depuis le .env (optionnel ici)
load_dotenv()

# 👉 Remplace par ton adresse publique EVM (copie depuis Rabby ou Metamask)
ADRESSE_MANUELLE = "0x9A06D2cd867589889A6330d84Ef17414EB2b98f8"

def detecter_adresse_wallet():
    if not ADRESSE_MANUELLE.startswith("0x") or len(ADRESSE_MANUELLE) != 42:
        print("❌ Adresse manuelle invalide. Vérifie le format.")
        return None

    print(f"✅ Adresse définie manuellement : {ADRESSE_MANUELLE}")
    return ADRESSE_MANUELLE
