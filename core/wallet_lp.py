# core/wallet_lp.py – Version V2.7

class WalletLP:
    """
    Représente un portefeuille simulé pour les tokens LP.
    """

    def __init__(self):
        self.soldes = {}

    def ajouter(self, nom_token, montant):
        """
        Ajoute un montant de tokens LP au portefeuille.
        """
        if nom_token in self.soldes:
            self.soldes[nom_token] += montant
        else:
            self.soldes[nom_token] = montant

    def get_solde(self, nom_token):
        """
        Retourne le solde d’un token LP donné.
        """
        return self.soldes.get(nom_token, 0)

    def afficher_soldes(self):
        """
        Affiche les soldes des tokens LP simulés.
        """
        print("\n📊 Solde LP simulé :")
        for token, montant in self.soldes.items():
            print(f" - {token} : {montant:.4f}")
