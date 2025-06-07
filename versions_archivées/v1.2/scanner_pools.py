# scanner_pools.py

def get_pools():
    pools = [
        {
            "name": "USDC/ETH",
            "apy": 0.12,
            "tvl": 900000,
            "volume_24h": 200000,
            "duree": 30
        },
        {
            "name": "SHIBA/PEPE",
            "apy": 0.25,
            "tvl": 600000,
            "volume_24h": 180000,
            "duree": 15
        },
        {
            "name": "DAI/MATIC",
            "apy": 0.08,
            "tvl": 700000,
            "volume_24h": 150000,
            "duree": 60
        }
    ]
    return pools
