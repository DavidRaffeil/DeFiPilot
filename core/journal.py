import os
import csv
from collections import defaultdict

def enregistrer_swap_lp_csv(date_str, pool, token_a, amount_a, token_b, amount_b):
    """
    Journalise un swap simulé dans journal_swap_lp.csv,
    avec protection anti-duplication sur (date + pool).
    """
    chemin = "logs/journal_swap_lp.csv"
    fichier_existe = os.path.exists(chemin)
    pool_id = pool.lower()

    if fichier_existe:
        with open(chemin, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for ligne in list(reader)[1:]:
                if ligne and ligne[0] == date_str and ligne[1].lower() == pool_id:
                    print(f"⚠️ Swap LP déjà enregistré pour {date_str} | {pool}")
                    return

    with open(chemin, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not fichier_existe:
            writer.writerow(["date", "pool", "token_a", "amount_a", "token_b", "amount_b"])
        writer.writerow([date_str, pool, token_a, amount_a, token_b, amount_b])
        print(f"📝 Swap LP enregistré pour {pool} le {date_str}")


def afficher_journal_swaps_lp(date_str):
    """
    Affiche les swaps LP du jour donné.
    """
    chemin = "logs/journal_swap_lp.csv"
    if not os.path.exists(chemin):
        print("⚠️ Aucun journal LP trouvé.")
        return

    with open(chemin, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        lignes = [row for row in reader if row["date"] == date_str]

        if not lignes:
            print(f"📄 Aucun swap LP pour le {date_str}.")
            return

        print(f"📄 Journal des swaps LP simulés du {date_str} :")
        for ligne in lignes:
            print(f"  • {ligne['pool']} → {ligne['amount_a']} {ligne['token_a']} + {ligne['amount_b']} {ligne['token_b']}")


def enregistrer_historique_swap_lp(date_str, pool, token_a, amount_a, token_b, amount_b, score, profil, gain_simule):
    """
    Enregistre les détails complets d’un swap LP dans un fichier journalisé jour par jour.
    """
    chemin = f"logs/historique_lp_{profil}.csv"
    fichier_existe = os.path.exists(chemin)

    with open(chemin, mode="a", newline="", encoding="utf-8") as fichier_csv:
        writer = csv.writer(fichier_csv)
        if not fichier_existe:
            writer.writerow([
                "date", "pool", "token_a", "amount_a", "token_b", "amount_b",
                "score", "profil", "gain_simule"
            ])

        writer.writerow([
            date_str, pool, token_a, amount_a, token_b, amount_b,
            round(score, 2), profil, round(gain_simule, 4)
        ])


def afficher_stats_historique_swaps_lp():
    """
    Affiche des statistiques basées sur les fichiers historiques LP.
    """
    dossier = "logs"
    fichiers = [f for f in os.listdir(dossier) if f.startswith("historique_lp_") and f.endswith(".csv")]
    stats = defaultdict(lambda: {"count": 0, "gain_total": 0.0, "score_total": 0.0})

    for fichier in fichiers:
        with open(os.path.join(dossier, fichier), mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pool = row["pool"]
                stats[pool]["count"] += 1
                stats[pool]["gain_total"] += float(row["gain_simule"])
                stats[pool]["score_total"] += float(row["score"])

    if not stats:
        print("📊 Aucune donnée historique à afficher.")
        return

    print("📊 Statistiques historiques LP (top 10 pools) :")
    top_pools = sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True)[:10]
    for pool, data in top_pools:
        moy_gain = data["gain_total"] / data["count"]
        moy_score = data["score_total"] / data["count"]
        print(f"  • {pool} : {data['count']}x | gain moyen : {moy_gain:.4f} USDC | score moyen : {moy_score:.2f}")
