# test_liquidite_log.py – V3.8
from __future__ import annotations

import json
from core.liquidity_dryrun import simuler_ajout_liquidite
from core.journal import enregistrer_liquidite_dryrun

pool = {
    "platform": "sushiswap",
    "chain": "polygon",
    "tokenA_symbol": "USDC",
    "tokenB_symbol": "WETH",
    "reservesA": 1_000_000.0,
    "reservesB": 1_000.0,
    "decimalsA": 6,
    "decimalsB": 18,
    "totalSupplyLP": 50_000.0,
}

res = simuler_ajout_liquidite(pool, amountA=10.0, amountB=0.01, slippage_bps=50)
print(json.dumps(res, ensure_ascii=False, indent=2))
enregistrer_liquidite_dryrun(res)
print("Écrit dans journal_liquidite.csv ✅")
