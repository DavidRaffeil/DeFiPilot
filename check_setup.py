# check_setup.py

import os
import importlib

FICHIERS_IMPORTANTS = [
    "main.py",
    "simulateur_logique.py",
    "simulateur_wallet.py",
    "core/defi_sources/defillama.py",
    "core/profil.py",
    "core/scoring.py",
    "core/config.py"
]

MODULES_IMPORTS = [
    "simulateur_logique",
    "simulateur_wallet",
    "core.defi_sources.defillama",
    "core.profil",
    "core.scoring",
    "core.config"
]

def verifier_fichiers():
    print("📁 Vérification des fichiers essentiels...")
    for fichier in FICHIERS_IMPORTANTS:
        if not os.path.exists(fichier):
            print(f"❌ Fichier manquant : {fichier}")
        else:
            print(f"✅ Fichier présent : {fichier}")

def verifier_imports():
    print("\n📦 Vérification des modules importables...")
    for module in MODULES_IMPORTS:
        try:
            importlib.import_module(module)
            print(f"✅ Import OK : {module}")
        except ImportError as e:
            print(f"❌ Import échoué : {module} → {e}")

if __name__ == "__main__":
    print("🔍 Démarrage de check_setup.py\n")
    verifier_fichiers()
    verifier_imports()
