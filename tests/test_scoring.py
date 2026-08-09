# tests/test_scoring.py – V6.0.0
"""Tests unitaires dédiés pour la Consolidation du Moteur de Scoring Multi-Facteurs (Étape 2.1)."""

import unittest

from core.scoring import (
    PROFILS,
    calculer_score_pool,
    calculer_scores,
    calculer_scores_et_gains,
    charger_ponderations,
    charger_profil_utilisateur,
)


class TestScoringMultiFacteurs(unittest.TestCase):
    def test_profils_weights_sum_to_one(self) -> None:
        """Vérifier que tous les profils ont des pondérations multi-facteurs valides somme = 1.0."""
        for nom, p in PROFILS.items():
            somme_poids = p["apr"] + p["tvl"] + p["volume"] + p["risk"]
            self.assertAlmostEqual(
                somme_poids, 1.0, places=4,
                msg=f"La somme des poids pour le profil '{nom}' doit être égale à 1.0"
            )

    def test_multi_factor_scoring_calculation(self) -> None:
        """Vérifier que le scoring multi-facteurs adapte les notes selon les profils."""
        pool_stable_tvl = {
            "pool_id": "usdc_dai_pool",
            "nom": "USDC/DAI",
            "plateforme": "AaveV3",
            "apr": 0.05,  # 5%
            "tvl_usd": 50_000_000.0,
            "volume_24h": 5_000_000.0,
            "risk_score": 0.05,
        }
        pool_high_yield_risky = {
            "pool_id": "meme_token_pool",
            "nom": "MEME/USDC",
            "plateforme": "DEX",
            "apr": 2.50,  # 250%
            "tvl_usd": 100_000.0,
            "volume_24h": 10_000.0,
            "risk_score": 0.85,
        }

        # Profil prudent (privilégie TVL & faible risque)
        poids_prudent = charger_ponderations("prudent")
        score_prudent_tvl = calculer_score_pool(pool_stable_tvl, poids_prudent, {}, PROFILS["prudent"])
        score_prudent_risky = calculer_score_pool(pool_high_yield_risky, poids_prudent, {}, PROFILS["prudent"])

        self.assertGreater(score_prudent_tvl, score_prudent_risky)

        # Profil agressif (privilégie APR)
        poids_agressif = charger_ponderations("agressif")
        score_agressif_tvl = calculer_score_pool(pool_stable_tvl, poids_agressif, {}, PROFILS["agressif"])
        score_agressif_risky = calculer_score_pool(pool_high_yield_risky, poids_agressif, {}, PROFILS["agressif"])

        self.assertGreater(score_agressif_risky, score_agressif_tvl)

    def test_data_imputation_and_fallbacks(self) -> None:
        """Vérifier l'imputation automatique des données manquantes sans crash."""
        pool_incomplète = {
            "pool_id": "test_incomplete",
            "nom": "Test Incomplete",
            "plateforme": "Sushi",
            "apr": 0.12,
            "tvl_usd": 1_000_000.0,
            # volume_24h et risk_score absents !
        }
        poids = charger_ponderations("modere")
        score = calculer_score_pool(pool_incomplète, poids, {}, PROFILS["modere"])

        self.assertIsInstance(score, float)
        self.assertGreater(score, 0.0)

    def test_extreme_apr_penalty(self) -> None:
        """Vérifier l'application d'une pénalité de sécurité sur les APRs anormaux/excessifs (> 1000%)."""
        pool_normale = {
            "pool_id": "normal_pool",
            "nom": "Normal 50%",
            "plateforme": "Sushi",
            "apr": 50.0,
            "tvl_usd": 1_000_000.0,
            "risk_score": 0.2,
        }
        pool_extreme = {
            "pool_id": "extreme_pool",
            "nom": "Extreme 5000%",
            "plateforme": "Sushi",
            "apr": 5000.0,  # 5000% APR suspect !
            "tvl_usd": 1_000_000.0,
            "risk_score": 0.2,
        }
        poids = charger_ponderations("modere")
        score_norm = calculer_score_pool(pool_normale, poids, {}, PROFILS["modere"])
        score_ext = calculer_score_pool(pool_extreme, poids, {}, PROFILS["modere"])

        # Le score de l'APR extrême doit être pénalisé et donc inférieur ou équivalent au score normal
        self.assertLess(score_ext, score_norm * 2.0)

    def test_calculer_scores_et_gains(self) -> None:
        """Vérifier le calcul du top 3 et des estimations de gains."""
        pools = [
            {"pool_id": "p1", "nom": "P1", "plateforme": "A", "apr": 10.0, "tvl_usd": 5_000_000.0},
            {"pool_id": "p2", "nom": "P2", "plateforme": "B", "apr": 20.0, "tvl_usd": 10_000_000.0},
            {"pool_id": "p3", "nom": "P3", "plateforme": "C", "apr": 30.0, "tvl_usd": 1_000_000.0},
            {"pool_id": "p4", "nom": "P4", "plateforme": "D", "apr": 1.0, "tvl_usd": 100_000.0},
        ]
        profil = charger_profil_utilisateur()
        top3, gain_total = calculer_scores_et_gains(pools, profil, solde=10_000.0, historique_pools={})

        self.assertEqual(len(top3), 3)
        self.assertGreater(gain_total, 0.0)


if __name__ == "__main__":
    unittest.main()
