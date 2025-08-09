# test_journal_risques.py – V3.2
import os

fichier = "logs/journal_risques.csv"

if os.path.exists(fichier):
    print(f"✅ Le fichier {fichier} existe.")
    if os.path.getsize(fichier) > 0:
        print(f"📄 Contenu détecté – taille : {os.path.getsize(fichier)} octets")
    else:
        print("⚠️ Le fichier existe mais est vide.")
else:
    print(f"❌ Le fichier {fichier} n'existe pas.")
