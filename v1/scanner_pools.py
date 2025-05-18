# scanner_pools.py

def get_pools():
    """
    Simule la récupération de pools de liquidité avec quelques données fictives.
    Chaque pool est un dictionnaire avec des infos basiques.
    """
    pools = [
        {
            "name": "USDC/ETH",
            "apy": 0.4,
            "tvl": 9000000,
            "volume_24h": 900000,
            "stability": 1.0,
            "risk": 0
        },
        {
            "name": "SHIBA/PEPE",
            "apy": 0.10,
            "tvl": 800000,
            "volume_24h": 50000,
            "stability": 0.3,
            "risk": 1
        },
        {
            "name": "DAI/MATIC",
            "apy": 0.08,
            "tvl": 3000000,
            "volume_24h": 250000,
            "stability": 0.8,
            "risk": 0
        }
    ]
    return pools
