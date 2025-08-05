# Version : V2.9 – Simulation LP + slippage journalisé

"""Simulation du farming de tokens LP avec journalisation du slippage."""

from datetime import date

from core.journal import enregistrer_slippage_lp


def simuler_farming_lp(montant_lp, apr_farming, nom_pool, plateforme, profil):
    """Simule un farming de LP en appliquant un slippage fictif de 2 %.

    Parameters
    ----------
    montant_lp : float
        Montant de LP tokens reçu avant application du slippage.
    apr_farming : float
        Taux annuel de rendement farming en pourcentage.
    nom_pool : str
        Nom de la pool concernée.
    plateforme : str
        Plateforme où se trouve la pool.
    profil : Any
        Profil de l'utilisateur, journalisé tel quel.

    Returns
    -------
    float
        Gain journalier simulé, arrondi à 4 décimales.
    """

    try:
        slippage = montant_lp * 0.02
        montant_apres_slippage = montant_lp - slippage
        gain = (montant_apres_slippage * apr_farming / 100) / 365

        enregistrer_slippage_lp(
            date.today(),
            nom_pool,
            plateforme,
            montant_apres_slippage,
            slippage,
            profil,
        )

        return round(gain, 4)
    except Exception as e:
        print(f"[ERREUR] {e}")
        return 0.0
