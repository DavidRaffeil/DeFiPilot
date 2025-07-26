import json
from datetime import datetime
from core.profil import charger_profil
from core.historique import charger_historique, maj_historique, sauvegarder_historique
from core.simulation import calculer_score_pool, simuler_gains
from core.config import charger_config
from core.utils import ligne_deja_presente
from core.journal import (
    enregistrer_swap_lp_csv,
    afficher_journal_swaps_lp,
    enregistrer_historique_swap_lp,
    afficher_stats_historique_swaps_lp
)
from core.journalisation import log_gain_simule, afficher_resume_journalier
from defi_sources.defillama import recuperer_pools
from simulateur_wallet import charger_solde, mettre_a_jour_solde, journaliser_resultats

# Chargement config, profil, historique, solde
config = charger_config()
profil_nom = config.get("profil_defaut", "modéré")
profil_utilisateur = charger_profil(profil_nom)
ponderations = profil_utilisateur["ponderations"]
historique_pools = charger_historique()
solde = charger_solde()
date_str = datetime.now().strftime("%Y-%m-%d")

print(f"[{date_str}] ℹ️ Démarrage d’un cycle DeFiPilot")
print(f"[{date_str}] ℹ️ Profil : {profil_nom} (APR {ponderations['apr']}, TVL {ponderations['tvl']})")

pools = recuperer_pools()
print(f"[{date_str}] ✅ {len(pools)} pools récupérées")

for pool in pools:
    pool["score"] = calculer_score_pool(pool, ponderations, historique_pools, profil_utilisateur)

pools = sorted(pools, key=lambda x: x["score"], reverse=True)
seuil = config.get("seuil_score_investissement", 30000)
top_pools = [p for p in pools if p["score"] >= seuil][:3]
autres = [p for p in pools if p["score"] < seuil]

print(f"[{date_str}] ℹ️ Seuil dynamique : {seuil}")
for i, pool in enumerate(top_pools, 1):
    gain_str, _ = simuler_gains(pool, solde / 3)
    print(f"[{date_str}]    {i}. {pool.get('plateforme')} | {pool.get('nom')} | Score : {pool['score']:.2f} | Gain simulé : {gain_str} USDC")

solde_avant = round(solde, 2)

if not top_pools:
    print(f"[{date_str}] ❌ Aucune pool au-dessus du seuil")
else:
    montants = [solde / len(top_pools)] * len(top_pools)
    total_gain = 0.0

    for i, pool in enumerate(top_pools):
        montant = montants[i]
        gain_str, gain_val = simuler_gains(pool, montant)
        maj_historique(historique_pools, pool["nom"], gain_val)
        total_gain += gain_val

        tokens = pool["nom"].split("-") if "-" in pool["nom"] else ["TOKEN1", "TOKEN2"]
        token_a = tokens[0]
        token_b = tokens[1] if len(tokens) > 1 else "UNKNOWN"

        enregistrer_swap_lp_csv(date_str, pool["id"], token_a, round(montant/2, 6), token_b, round(montant/2, 6))
        enregistrer_historique_swap_lp(
            date_str=date_str,
            pool=pool["id"],
            token_a=token_a,
            amount_a=round(montant / 2, 6),
            token_b=token_b,
            amount_b=round(montant / 2, 6),
            score=pool["score"],
            profil=profil_nom,
            gain_simule=gain_val
        )

    sauvegarder_historique(historique_pools)
    solde_apres = mettre_a_jour_solde(total_gain)

    gain_journalier = round(solde_apres - solde_avant, 2)
    gain_pourcent = round((gain_journalier / solde_avant) * 100, 2) if solde_avant > 0 else 0.0

    journaliser_resultats(profil_nom, solde_apres, top_pools, montants, autres)

    pool_principale = top_pools[0]
    log_gain_simule(
        date=date_str,
        solde_avant=solde_avant,
        solde_apres=solde_apres,
        gain_journalier=gain_journalier,
        gain_percent=gain_pourcent,
        pool=pool_principale.get("nom", "unknown"),
        apr=pool_principale.get("apr", "unknown"),
        tvl=pool_principale.get("tvlUsd", "unknown"),
        score=pool_principale.get("score", 0)
    )

    afficher_resume_journalier(
        date=date_str,
        gain_journalier=gain_journalier,
        gain_percent=gain_pourcent,
        pool=pool_principale.get("nom", "unknown"),
        apr=pool_principale.get("apr", "unknown"),
        tvl=pool_principale.get("tvlUsd", "unknown"),
        score=pool_principale.get("score", 0)
    )

    afficher_journal_swaps_lp(date_str)

afficher_stats_historique_swaps_lp()
