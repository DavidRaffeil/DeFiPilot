# main.py – Version V2.7 complète et corrigée

import os
import sys
import datetime
from core import scoring, historique, defi_sources, wallet_lp, journal

# Initialisation du portefeuille LP
lp_wallet = wallet_lp.WalletLP()

def main():
    print("\U0001F680 Lancement de DeFiPilot")

    # Charger le profil utilisateur
    profil = scoring.charger_profil_utilisateur()
    print(f"[{datetime.date.today()}] INFO \U0001F3D7 Profil actif : {profil['nom']} (APR {profil['ponderations']['apr']}, TVL {profil['ponderations']['tvl']})")

    # Charger l'historique des performances
    historique_pools = historique.charger_historique()

    # Récupération des pools
    print("[2025-08-03] INFO \U0001F9EA Récupération des pools via DefiLlama")
    pools = defi_sources.defillama.get_pools()
    print(f"[2025-08-03] INFO ✅ {len(pools)} pools récupérées")

    # Calcul des scores et gains simulés
    solde_usdc = 5000.00
    resultats, gain_total = scoring.calculer_scores_et_gains(pools, profil, solde_usdc, historique_pools)

    date_du_jour = str(datetime.date.today())
    for nom, apr, gain in resultats:
        print(f"  • {nom} | APR : {apr:.2f}% | Gain simulé : {gain:.2f} $ USDC")

    # Simuler les investissements et journaux LP
    for nom, apr, gain in resultats:
        solde_usdc += gain
        print(f"💰 Gain simulé : +{gain:.2f} $ USDC → Nouveau solde : {solde_usdc:.2f} $ USDC")

        parts = nom.split(" | ")
        plateforme = parts[0]
        token_lp = "LP-" + parts[1]
        montant_lp = round(gain / 2, 4)  # simulation de réception de LP token

        lp_wallet.ajouter(token_lp, montant_lp)
        print(f"🗓️ LP simulé reçu : {montant_lp:.4f} {token_lp}")

        # Récupérer l'APR de farming de la pool
        pool = next((p for p in pools if f"{p['plateforme']} | {p['nom']}" == nom), None)
        farming_apr = pool.get("farming_apr", 0) if pool else 0
        gain_farming = scoring.simuler_gain_farming_lp(montant_lp, farming_apr)

        print(f"🌾 Farming LP simulé : {gain_farming:.4f} $ USDC générés avec {farming_apr:.2f}% APR")

        # Journalisation
        poids_profil = profil["ponderations"]
        token_parts = token_lp.split('-')
        journal.enregistrer_lp(
            date_du_jour,
            profil["nom"],
            nom,
            token_parts[1],
            token_parts[2],
            gain,
            round(poids_profil["apr"], 4),
            round(poids_profil["tvl"], 4)
        )

        # Mise à jour de l'historique pour bonus futur
        historique.maj_historique(historique_pools, nom, gain)

    # Affichage des soldes LP
    lp_wallet.afficher_soldes()

    # Sauvegarde de l'historique
    historique.sauvegarder_historique(historique_pools)

if __name__ == "__main__":
    main()
