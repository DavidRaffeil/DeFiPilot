# stats.py

class Statistiques:
    def __init__(self):
        self.cycles = 0
        self.total_pools = 0
        self.total_invest = 0
        self.total_desinvest = 0
        self.total_score = 0.0

    def ajouter_cycle(self, tableau):
        self.cycles += 1
        self.total_pools += len(tableau)
        self.total_invest += sum(1 for l in tableau if l["decision"] == "INVESTIR")
        self.total_desinvest += sum(1 for l in tableau if l["decision"] != "INVESTIR" and l.get("compounding"))
        self.total_score += sum(l["score"] for l in tableau)

    def afficher_stats_globales(self):
        print("📊 Statistiques cumulées depuis le démarrage")
        print("-" * 80)
        print(f"Cycles effectués             : {self.cycles}")
        print(f"Pools analysées au total    : {self.total_pools}")
        print(f"Total investissements       : {self.total_invest}")
        print(f"Total désinvestissements    : {self.total_desinvest}")
        if self.total_pools > 0:
            print(f"Score moyen global          : {round(self.total_score / self.total_pools, 4)}")
        print("-" * 80 + "\n")
