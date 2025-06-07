# test_defillama.py

from dex_defillama import get_pools_defillama

pools = get_pools_defillama()

for i, pool in enumerate(pools):
    print(f"#{i+1} - {pool['dex']} - {pool['token0']}/{pool['token1']} - TVL: ${pool['tvl_usd']:.2f} - APR: {pool['apr']:.2f}%")
