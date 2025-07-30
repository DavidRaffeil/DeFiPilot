import os
import sys
import importlib
import logging
import random

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)

REQUIRED_FILES = [
    "main.py",
    "core/scoring.py",
    "core/profil.py",
    "core/defi_sources/defillama.py",
    "config.json"
]

REQUIRED_FUNCTIONS = {
    "core.scoring": ["calculer_scores_et_gains", "trier_pools", "charger_profil_utilisateur"],
    "core.profil": ["charger_profil"],
    "core.defi_sources.defillama": ["recuperer_pools"]
}

REQUIRED_KEYS_IN_POOL = ["nom", "plateforme", "apr", "tvl_usd", "lp", "farming_apr"]

def check_files():
    success = True
    logging.info("\n🔍 Vérification des fichiers essentiels...")
    for file in REQUIRED_FILES:
        if not os.path.isfile(file):
            logging.error(f"❌ Fichier manquant : {file}")
            success = False
        else:
            logging.info(f"✅ {file}")
    return success

def check_imports():
    success = True
    logging.info("\n🔍 Vérification des imports de modules...")
    for module in REQUIRED_FUNCTIONS:
        try:
            importlib.import_module(module)
            logging.info(f"✅ Import réussi : {module}")
        except Exception as e:
            logging.error(f"❌ Échec import {module} : {e}")
            success = False
    return success

def check_functions():
    success = True
    logging.info("\n🔍 Vérification des fonctions attendues...")
    for module_name, functions in REQUIRED_FUNCTIONS.items():
        try:
            module = importlib.import_module(module_name)
            for func in functions:
                if not hasattr(module, func):
                    logging.error(f"❌ Fonction manquante : {func} dans {module_name}")
                    success = False
                else:
                    logging.info(f"✅ Fonction trouvée : {func} dans {module_name}")
        except Exception as e:
            logging.error(f"❌ Impossible d’analyser {module_name} : {e}")
            success = False
    return success

def check_pool_structure():
    logging.info("\n🔍 Vérification de la structure d'une pool simulée...")
    try:
        from core.defi_sources import defillama
        pools = defillama.recuperer_pools()
        if not pools:
            raise ValueError("Liste des pools vide")

        # Chercher une pool LP pour tester farming_apr
        pool = next((p for p in pools if p.get("lp")), pools[0])

        success = True
        for key in REQUIRED_KEYS_IN_POOL:
            if key not in pool:
                logging.error(f"❌ Clé manquante dans pool : {key}")
                success = False
            else:
                logging.info(f"✅ Clé trouvée : {key}")
        return success
    except Exception as e:
        logging.error(f"❌ Erreur lors de la récupération/lecture d'une pool : {e}")
        return False

def run_all_checks():
    all_passed = True
    if not check_files():
        all_passed = False
    if not check_imports():
        all_passed = False
    if not check_functions():
        all_passed = False
    if not check_pool_structure():
        all_passed = False

    if all_passed:
        logging.info("\n✅ Toutes les vérifications sont passées avec succès.")
        sys.exit(0)
    else:
        logging.error("\n❌ Des erreurs ont été détectées. Veuillez corriger avant de relancer.")
        sys.exit(1)

if __name__ == "__main__":
    run_all_checks()
