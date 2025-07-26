# core/swaps.py

import csv
import os
from datetime import datetime

SWAPS_PATH = "logs/journal_swaps.csv"

def enregistrer_swap_simule(date_str, pool, token_a, amount_a, token_b, amount_b):
    """Enregistre un swap simulé dans le journal CSV"""
    
    # Créer le fichier avec l'en-tête si besoin
    if not os.path.exists(SWAPS_PATH):
        with open(SWAPS_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "pool", "token_a", "amount_a", "token_b", "amount_b"])
    
    # Ajouter la ligne du jour
    with open(SWAPS_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([date_str, pool, token_a, amount_a, token_b, amount_b])
