from dex_uniswap import get_pools_uniswap

pools = get_pools_uniswap()

for i, pool in enumerate(pools):
    print(f"#{i+1} - {pool['token0']}/{pool['token1']} - TVL: ${pool['tvl_usd']:.2f} - APR: {pool['apr']:.2f}%")
