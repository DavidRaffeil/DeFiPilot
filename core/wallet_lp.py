# core/wallet_lp.py

class WalletLP:
    def __init__(self):
        self.solde_lp = {}

    def ajouter(self, token_lp: str, montant: float):
        if token_lp in self.solde_lp:
            self.solde_lp[token_lp] += montant
        else:
            self.solde_lp[token_lp] = montant
        print(f"💼 Ajout simulé : {montant:.4f} {token_lp} dans le wallet LP")

    def ajouter_lp(self, token_lp: str, montant: float):
        self.ajouter(token_lp, montant)

    def afficher_soldes(self):
        print("\n📊 Solde LP simulé :")
        if not self.solde_lp:
            print("(vide)")
        for token, montant in self.solde_lp.items():
            print(f" - {token} : {montant:.4f}")
