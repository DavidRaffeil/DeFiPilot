import os
import json
from datetime import datetime

FICHIER_PORTFOLIO = "portfolio.json"
DOSSIER_SNAPSHOTS = "snapshots"

def charger_portefeuille():
    if not os.path.exists(FICHIER_PORTFOLIO):
        return {}
    with open(FICHIER_PORTFOLIO, "r", encoding="utf-8") as f:
        return json.load(f)

def sauvegarder_portefeuille(data):
    with open(FICHIER_PORTFOLIO, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def ajouter_pool(pool_name):
    data = charger_portefeuille()
    aujourd_hui = datetime.now().strftime("%Y-%m-%d")
    data[pool_name] = aujourd_hui
    sauvegarder_portefeuille(data)

def retirer_pool(pool_name):
    data = charger_portefeuille()
    if pool_name in data:
        del data[pool_name]
        sauvegarder_portefeuille(data)

def est_investi(pool_name):
    data = charger_portefeuille()
    return pool_name in data

def get_date_investissement(pool_name):
    data = charger_portefeuille()
    return data.get(pool_name)

def init_portefeuille():
    if not os.path.exists(FICHIER_PORTFOLIO):
        with open(FICHIER_PORTFOLIO, "w", encoding="utf-8") as f:
            json.dump({}, f)

def sauvegarder_snapshot_portefeuille():
    data = charger_portefeuille()
    if not os.path.exists(DOSSIER_SNAPSHOTS):
        os.makedirs(DOSSIER_SNAPSHOTS)
    horodatage = datetime.now().strftime("%Y-%m-%d_%H-%M")
    nom_fichier = f"{DOSSIER_SNAPSHOTS}/auto_snapshot_{horodatage}.json"
    with open(nom_fichier, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def snapshot_portefeuille():
    data = charger_portefeuille()
    if not os.path.exists(DOSSIER_SNAPSHOTS):
        os.makedirs(DOSSIER_SNAPSHOTS)
    horodatage = datetime.now().strftime("%Y-%m-%d_%H-%M")
    nom_fichier = f"{DOSSIER_SNAPSHOTS}/snapshot_{horodatage}.json"
    with open(nom_fichier, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"📦 Snapshot enregistré dans {nom_fichier}")

def exporter_portefeuille(nom_fichier="export_portefeuille.json"):
    data = charger_portefeuille()
    with open(nom_fichier, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Portefeuille exporté dans {nom_fichier}")
