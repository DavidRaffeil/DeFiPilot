from core.rendement import enregistrer as enregistrer_rendement
from core.scoring import calculer_score_pool
from core.wallet import obtenir_solde_usdc
from core.swaps import enregistrer_swap_simule
from core.journal import enregistrer_swap_lp_csv  # ✅ Nouveau pour V2.3
from datetime import datetime

def simuler_investissement(pools, profil, seuil, historique_pools):
    """
    Simule un investissement en sélectionnant les meilleures pools au-dessus du seuil.
    Enregistre les rendements et les swaps associés.
    """
    solde_initial = obtenir_solde_usdc()
    pools_filtrees = []

    for pool in pools:
        score = calculer_score_pool(pool, profil["ponderations"], historique_pools, profil)
        if score >= seuil:
            pools_filtrees.append((pool, score))

    if not pools_filtrees:
        print("❌ Aucune pool ne dépasse le seuil actuel.")
        return solde_initial

    # Trier par score décroissant
    pools_filtrees.sort(key=lambda x: x[1], reverse=True)

    # Sélection de la meilleure pool
    meilleure_pool, meilleur_score = pools_filtrees[0]
    pool_nom = meilleure_pool["id"]
    tokens = meilleure_pool["nom"].split("-") if "-" in meilleure_pool["nom"] else ["TOKEN1", "TOKEN2"]
    token_a = tokens[0]
    token_b = tokens[1] if len(tokens) > 1 else "UNKNOWN"

    solde_avant = solde_initial
    gain_brut = solde_avant * 0.20  # gain simulé brut de 20%
    solde_apres = solde_avant + gain_brut

    date_str = datetime.now().strftime("%Y-%m-%d")

    # Enregistrer rendement
    enregistrer_rendement(gain_brut, solde_avant, solde_apres, bonus_applique=None)

    # Enregistrer le swap simulé (moitié vers chaque token)
    enregistrer_swap_simule(
        date_str=date_str,
        pool=pool_nom,
        token_a=token_a,
        amount_a=solde_avant / 2,
        token_b=token_b,
        amount_b=solde_avant / 2
    )

    # ✅ Journalisation LP dans fichier CSV (nouveau)
    enregistrer_swap_lp_csv(
        date_str=date_str,
        pool=pool_nom,
        token_a=token_a,
        amount_a=solde_avant / 2,
        token_b=token_b,
        amount_b=solde_avant / 2
    )

    # ✅ Affichage console résumé du swap LP
    print(f"🪙 Swap simulé LP : {round(solde_avant/2,2)} {token_a} + {round(solde_avant/2,2)} {token_b} (pool : {pool_nom})")

    print(f"✅ Simulation effectuée sur la pool {pool_nom} – gain simulé : {round(gain_brut, 2)} USDC")
    return solde_apres


def simuler_gains(pool: dict, montant: float) -> tuple[str, float]:
    """Calcule un gain simulé sur la base de l'APR indiquée."""
    apr = pool.get("apr", 0)
    gain_annuel = montant * (apr / 100)
    gain_journalier = gain_annuel / 365
    return f"{gain_journalier:.2f} $", gain_journalier
