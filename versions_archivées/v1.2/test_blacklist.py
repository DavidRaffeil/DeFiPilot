from blacklist import enregistrer_rejet
from settings import CYCLE_ACTUEL

# Ajouter manuellement une pool à la blacklist
nom_pool = "beefy_NOICE-WETH"
enregistrer_rejet(nom_pool, CYCLE_ACTUEL)
print(f"✅ Pool '{nom_pool}' ajoutée à la blacklist pour le cycle {CYCLE_ACTUEL}")
