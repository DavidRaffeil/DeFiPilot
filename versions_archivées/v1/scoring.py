# scoring.py

from profil_loader import charger_profil
from settings import PROFIL_INVESTISSEUR

def score_pool(pool, max_apy=1.0, max_tvl=10_000_000, max_volume=1_000_000):
    """
    Calcule le score d'une pool en fonction du profil d'investisseur actif
    et des pondérations définies dans profils.json.
    """
    profil = charger_profil(PROFIL_INVESTISSEUR)

    if not profil:
        print(f"❌ Profil '{PROFIL_INVESTISSEUR}' introuvable dans profils.json")
        return 0.0

    apy = pool.get("apy", 0) / max_apy if max_apy else 0
    volume = pool.get("volume_24h", 0) / max_volume if max_volume else 0
    tvl = pool.get("tvl", 0) / max_tvl if max_tvl else 0
    stability = pool.get("stability", 0)
    risk = pool.get("risk", 0)

    score = (
        profil["apy"] * apy +
        profil["volume"] * volume +
        profil["tvl"] * tvl +
        profil["stability"] * stability +
        profil["risk"] * risk  # peut être négatif
    )

    return round(score, 4)
