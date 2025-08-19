# liquidity_cli.py – V3.8
import argparse, json, logging, sys
from typing import Any, Dict, Optional, List
from core.liquidity_real_tx import ajouter_liquidite_reelle

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="liquidity_cli", description="DeFiPilot V3.8 — Add Liquidity (UniswapV2-like)")
    sub = p.add_subparsers(dest="cmd", required=True)
    add = sub.add_parser("add_liquidity", help="Ajouter de la liquidité (réel ou dry-run)")
    add.add_argument("--pool-json", type=str, required=True, help="Objet JSON décrivant la pool")
    add.add_argument("--amountA", type=float, required=True, help="Montant token A")
    add.add_argument("--amountB", type=float, required=True, help="Montant token B")
    add.add_argument("--wallet", type=str, required=True, help="Nom du wallet (real_wallet)")
    add.add_argument("--slippage", type=float, default=0.005, help="Tolérance slippage (ex: 0.005 = 0.5%)")
    add.add_argument("--deadline", type=int, default=None, help="Timestamp limite (int)")
    grp = add.add_mutually_exclusive_group()
    grp.add_argument("--dry-run", action="store_true", help="Simulation (par défaut)")
    grp.add_argument("--real", action="store_true", help="Envoi réel")
    add.add_argument("--confirm", type=str, default="", help='Obligatoire si --real: taper "ADD_LIQUIDITY"')
    return p

def _parse_pool(s: str) -> Dict[str, Any]:
    try:
        d = json.loads(s)
        if not isinstance(d, dict):
            raise ValueError("pool-json doit être un objet JSON")
        return d
    except Exception as e:
        raise ValueError(f"pool-json invalide: {e}")

def _validate_pool(pool: Dict[str, Any]) -> None:
    req = ["platform","chain","router_address","tokenA_symbol","tokenB_symbol","tokenA_address","tokenB_address"]
    miss = [k for k in req if k not in pool]
    if miss: raise ValueError(f"Clés manquantes dans pool: {', '.join(miss)}")

def cmd_add_liquidity(args: argparse.Namespace) -> int:
    pool = _parse_pool(args.pool_json); _validate_pool(pool)
    if args.amountA <= 0 or args.amountB <= 0:
        print("[V3.8] ⚠️ Échec: amountA et amountB doivent être > 0"); return 2
    dry_run = True if (args.dry_run or not args.real) else False
    if not dry_run and args.confirm != "ADD_LIQUIDITY":
        print('[V3.8] ⚠️ Sécurité: utilisez --confirm "ADD_LIQUIDITY" avec --real'); return 2

    print("[V3.8] 🔧 Params CLI: platform={plat}, chain={chain}, pair={a}-{b}, amountA={A}, amountB={B}, slippage={s}, dry_run={dr}".format(
        plat=pool.get("platform"), chain=pool.get("chain"),
        a=pool.get("tokenA_symbol"), b=pool.get("tokenB_symbol"),
        A=args.amountA, B=args.amountB, s=args.slippage, dr=dry_run
    ))

    res = ajouter_liquidite_reelle(pool=pool, amountA=args.amountA, amountB=args.amountB,
                                   wallet_name=args.wallet, slippage=args.slippage,
                                   deadline=args.deadline, dry_run=dry_run)

    if res.get("success"):
        print("[V3.8] ✅ OK tx={tx} lp={lp}".format(tx=res.get("tx_hash"), lp=res.get("lp_tokens"))); return 0
    else:
        print("[V3.8] ⚠️ Échec: {err}".format(err=res.get("error"))); return 1

def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO)
    pa = _build_parser(); args = pa.parse_args(argv)
    if args.cmd == "add_liquidity": return cmd_add_liquidity(args)
    print("Commande inconnue"); return 1

if __name__ == "__main__":
    sys.exit(main())
