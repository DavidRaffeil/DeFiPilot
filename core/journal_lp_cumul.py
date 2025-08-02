import csv
import os

def enregistrer_lp_cumul(nom_pool, plateforme, montant_lp, gain_farming):
    """Enregistre un suivi cumulatif des investissements LP."""
    dossier = "logs"
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, "journal_lp_cumul.csv")

    lignes = []
    if os.path.isfile(fichier):
        with open(fichier, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            lignes = list(reader)

    trouve = False
    for ligne in lignes:
        if ligne.get("nom_pool") == nom_pool and ligne.get("plateforme") == plateforme:
            ligne["jours_investi"] = str(int(ligne.get("jours_investi", 0)) + 1)
            ligne["montant_lp_total"] = str(round(float(ligne.get("montant_lp_total", 0)) + montant_lp, 4))
            ligne["gain_farming_total"] = str(round(float(ligne.get("gain_farming_total", 0)) + gain_farming, 4))
            trouve = True
            break

    if not trouve:
        lignes.append({
            "nom_pool": nom_pool,
            "plateforme": plateforme,
            "jours_investi": "1",
            "montant_lp_total": str(round(montant_lp, 4)),
            "gain_farming_total": str(round(gain_farming, 4)),
        })

    with open(fichier, mode="w", newline="", encoding="utf-8") as f:
        entetes = ["nom_pool", "plateforme", "jours_investi", "montant_lp_total", "gain_farming_total"]
        writer = csv.DictWriter(f, fieldnames=entetes)
        writer.writeheader()
        writer.writerows(lignes)
