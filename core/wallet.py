# core/wallet.py (nouveau fichier créé)

solde_simule = 1000.0


def get_solde():
    """
    Retourne le solde simulé actuel du portefeuille.
    """
    return solde_simule


def investir(montant):
    """
    Simule un investissement :
    - Déduit le montant du solde simulé
    - Calcule un gain simulé (pour le moment identique au montant investi)
    - Retourne (solde_avant, gain_simulé, nouveau_solde)
    """
    global solde_simule
    solde_avant = solde_simule
    gain_simule = montant  # simplification pour la simulation
    solde_simule -= montant
    nouveau_solde = solde_simule
    return solde_avant, gain_simule, nouveau_solde
