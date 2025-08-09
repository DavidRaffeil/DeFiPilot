# test_simuler_pools_risquees.py – V3.2
# But : créer artificiellement des pools "à risque" et les journaliser dans logs/journal_risques.csv

import os, csv, datetime

# 1) Essaye d'utiliser l'analyse réelle si dispo, sinon fallback simple
def analyser(pool: dict) -> dict:
    try:
        # risk_analysis.py à la racine du projet (V3.2)
        from risk_analysis import analyser_risque
        return analyser_risque(pool)
    except Exception:
        # Règles minimales (fallback) : APR > 5000, TVL < 500, plateforme non reconnue
        raisons = []
        apr = pool.get("apr", 0)
        tvl = pool.get("tvl", 0)
        platform = pool.get("platform", "")
        plateformes_reconnues = {"uniswap", "sushiswap", "curve", "balancer"}

        if apr > 5000:
            raisons.append("APR > 5000")
        if tvl < 500:
            raisons.append("TVL < 500")
        if platform not in plateformes_reconnues:
            raisons.append("Plateforme inconnue")

        pool["risque"] = bool(raisons)
        pool["raisons_risque"] = raisons
        return pool

# 2) Pools “à risque” pour déclencher la journalisation
pools_test = [
    {"platform": "unknowndex", "pool": "XYZ-ABC", "apr": 6200, "tvl": 450},
    {"platform": "uniswap",    "pool": "TST-ETH", "apr": 150,  "tvl": 300},
]

# 3) Prépare le CSV
logs_dir = "logs"
csv_path = os.path.join(logs_dir, "journal_risques.csv")
os.makedirs(logs_dir, exist_ok=True)
existe_deja = os.path.exists(csv_path)

with open(csv_path, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter=";")
    if not existe_deja:
        writer.writerow(["date", "platform", "pool", "apr", "tvl", "raisons"])
    for p in pools_test:
        p = analyser(p)
        if p.get("risque"):
            writer.writerow([
                datetime.date.today().isoformat(),
                p.get("platform", ""),
                p.get("pool", ""),
                p.get("apr", 0),
                p.get("tvl", 0),
                ", ".join(p.get("raisons_risque", [])),
            ])

print(f"✅ Simulation terminée. Vérifie : {csv_path}")
