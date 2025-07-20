import json

with open("wallet_simulation.json", "w", encoding="utf-8") as f:
    json.dump({"solde": 100.0}, f, indent=2)

print("Solde simulé réinitialisé à 100.0")
