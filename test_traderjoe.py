# test_traderjoe.py

from dex_traderjoe import get_pools_traderjoe

pools = get_pools_traderjoe()

for i, pool in enumerate(pools):
    print(f"#{i+1} - {pool['token0']}/{pool['token1']} - TVL: ${pool['tvl_usd']:.2f} - APR: {pool['apr']:.2f}%")
