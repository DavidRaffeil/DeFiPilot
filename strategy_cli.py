#!/usr/bin/env python3
# strategy_cli.py — V4.2.0
"""
DeFiPilot — CLI stratégie (V4.2)

FR : Calcule le contexte de marché et la policy d'allocation à partir d'un fichier de
      statistiques de pools (JSON) et d'une configuration optionnelle (JSON).
EN : Computes market context and allocation policy from pool stats (JSON) and an
      optional config (JSON).

Sorties :
- Par défaut : affichage lisible en français (texte court).
- Option --json : sortie JSON compacte (machine‑readable).

Compat : utilise core.market_signals_adapter.calculer_contexte_et_policy (V4.2)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping
from datetime import datetime

from core.market_signals_adapter import calculer_contexte_et_policy

VERSION = "V4.2.0"


def _read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _ensure_list_of_dicts(obj: Any) -> List[Dict[str, Any]]:
    if isinstance(obj, list) and all(isinstance(x, dict) for x in obj):
        return obj  # type: ignore[return-value]
    raise ValueError("Le fichier pools doit contenir une liste de dictionnaires JSON.")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="DeFiPilot – Stratégie (contexte + policy)")
    p.add_argument("--pools", required=True, help="Fichier JSON des stats de pools (liste de dicts)")
    p.add_argument("--cfg", default=None, help="Fichier JSON de configuration (optionnel)")
    p.add_argument("--last-context", default=None, help="Contexte précédent (facultatif)")
    p.add_argument("--json", action="store_true", default=False, help="Sortie JSON compacte")
    args = p.parse_args(argv)

    pools_path = Path(args.pools)
    cfg_path = Path(args.cfg) if args.cfg else None

    try:
        pools_obj = _read_json(pools_path)
        pools_stats = _ensure_list_of_dicts(pools_obj)
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": f"Impossible de lire pools: {exc}"}, ensure_ascii=False))
        else:
            print(f"Erreur: impossible de lire le fichier pools — {exc}")
        return 2

    cfg: Mapping[str, Any] = {}
    if cfg_path:
        try:
            cfg = _read_json(cfg_path)
        except Exception as exc:
            if args.json:
                print(json.dumps({"status": "error", "error": f"Impossible de lire config: {exc}"}, ensure_ascii=False))
            else:
                print(f"Avertissement: config illisible — {exc} (utilisation des paramètres par défaut)")
            cfg = {}

    try:
        decision, policy = calculer_contexte_et_policy(
            pools_stats=pools_stats,
            cfg=dict(cfg),
            last_context=args.last_context,
            run_id=f"strategy_cli-{datetime.utcnow().isoformat(timespec='seconds')}Z",
            version=VERSION,
            journal_path="journal_signaux.jsonl",
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"Erreur: échec du calcul stratégie — {exc}")
        return 1

    # Sortie
    metrics = decision.metrics or {}
    out = {
        "status": "ok",
        "context": decision.context,
        "score": round(float(decision.score), 6),
        "policy": policy,
        "metrics": metrics,
        "version": VERSION,
    }

    if args.json:
        print(json.dumps(out, ensure_ascii=False))
    else:
        print(f"Contexte détecté : {out['context']}")
        print(f"Score global     : {out['score']}")
        # métriques principales
        if "apr_mean" in metrics:
            print(f"APR moyen        : {metrics['apr_mean']:.4f}")
        if "volume_sum" in metrics:
            print(f"Volume 24h (sum) : {metrics['volume_sum']}")
        if "tvl_sum" in metrics:
            print(f"TVL (sum)        : {metrics['tvl_sum']}")
        # nouvelles métriques V4.2 (si présentes)
        if "volatility_cv" in metrics:
            print(f"Volatilité (CV)  : {metrics['volatility_cv']:.4f}")
        if "apr_trend_avg" in metrics:
            print(f"Tendance APR avg : {metrics['apr_trend_avg']:.4f}")
        print(
            "Allocation cible : "
            + " | ".join(
                [
                    f"{k.capitalize()} {int(v*100)}%"
                    for k, v in sorted(out["policy"].items(), key=lambda kv: -kv[1])
                ]
            )
        )
        print("Journal mis à jour : journal_signaux.jsonl")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
