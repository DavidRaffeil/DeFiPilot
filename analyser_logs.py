cat << 'EOF' > analyser_log.py
#!/usr/bin/env python3
# analyser_log.py — Outil de lecture des journaux DeFiPilot V6

import json
from pathlib import Path
from datetime import datetime

STRATEGY_LOG = Path("data/logs/journal_strategie.jsonl")
DECISIONS_LOG = Path("journal_decisions.jsonl")

def formater_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return iso_str

def analyser_strategie():
    print("\n=== DERNIÈRES DÉCISIONS STRATÉGIQUES ===")
    if not STRATEGY_LOG.exists():
        print(f"[Alerte] Le fichier {STRATEGY_LOG} n'existe pas encore.")
        return

    with STRATEGY_LOG.open("r", encoding="utf-8") as f:
        lignes = f.readlines()
        
    # On prend les 5 dernières entrées
    dernieres_entrees = lignes[-5:] if len(lignes) > 5 else lignes
    
    for ligne in dernieres_entrees:
        try:
            data = json.loads(ligne.strip())
            date_fmt = formater_date(data.get("timestamp", ""))
            print(f"[{date_fmt}] Run: {data.get('run_id', 'N/A')}")
            print(f"  • Profil appliqué : {data.get('profil', 'Inconnu')}")
            print(f"  • Contexte global : {data.get('context', 'N/A')}")
            
            alloc_av = data.get("allocation_actuelle_usd", {})
            alloc_ap = data.get("allocation_simulee_apres_reequilibrage", {})
            if alloc_av:
                print(f"  • Alloc Actuelle   : Prudent: {alloc_av.get('Prudent', 0):.2f}$ | Modéré: {alloc_av.get('Modere', 0):.2f}$ | Risqué: {alloc_av.get('Risque', 0):.2f}$")
            if alloc_ap:
                print(f"  • Alloc Simulée    : Prudent: {alloc_ap.get('Prudent', 0):.2f}$ | Modéré: {alloc_ap.get('Modere', 0):.2f}$ | Risqué: {alloc_ap.get('Risque', 0):.2f}$")
            
            scoring = data.get("scoring", {})
            if scoring:
                print(f"  • Estimation gains : +{scoring.get('gain_total_journalier_usd', 0):.4f}$/jour")
            print("-" * 50)
        except Exception as e:
            print(f"[Erreur lecture ligne] {e}")

def main():
    analyser_strategie()

if __name__ == "__main__":
    main()
EOF
chmod +x analyser_log.py
