# === V3.2 – Correction : enregistrer_pools_risquées (robuste) ===

def enregistrer_pools_risquées(pools: list, date: str, profil: str):
    dossier = "logs"
    os.makedirs(dossier, exist_ok=True)
    fichier = os.path.join(dossier, "journal_risques.csv")

    existe = os.path.isfile(fichier)
    with open(fichier, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not existe:
            writer.writerow(["date", "profil", "plateforme", "nom_pool", "apr", "tvl", "risque", "raisons"])

        for pool in pools:
            # Ne journaliser que les pools marquées à risque
            if not bool(pool.get("risque", False)):
                continue

            plateforme = pool.get("platform") or pool.get("plateforme") or ""
            nom_pool = (
                pool.get("name")
                or pool.get("nom")
                or pool.get("pair")
                or f"{pool.get('token0', '?')}-{pool.get('token1', '?')}"
            )
            apr = pool.get("apr", pool.get("apr_percent", 0)) or 0
            tvl = pool.get("tvl_usd", pool.get("tvl", 0)) or 0
            raisons_list = pool.get("raisons_risque") or []
            raisons = ", ".join(map(str, raisons_list))

            writer.writerow([
                date,
                profil,
                plateforme,
                nom_pool,
                round(float(apr), 4) if isinstance(apr, (int, float)) else apr,
                round(float(tvl), 4) if isinstance(tvl, (int, float)) else tvl,
                1,
                raisons
            ])
