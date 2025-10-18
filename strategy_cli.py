# strategy_cli.py — V4.0.17
"""Interface en ligne de commande pour le calcul de contexte et de policy.

Exemples:
    python strategy_cli.py --pools data/pools_stats.json --cfg config/strategy.json
    python strategy_cli.py --pools data/pools_stats.json --json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any, MutableMapping, Sequence, Mapping

from core.strategy_adapter import calculer_contexte_et_policy

VERSION: str = "V4.0.17"
DEFAULT_JOURNAL: str = "journal_signaux.jsonl"


def _load_json_file(path_str: str) -> Any:
    """Charge un fichier JSON et retourne le contenu Python associé."""
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {path}")
    try:
        with path.open("r", encoding="utf-8") as stream:
            return json.load(stream)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON invalide dans {path}: {exc}") from exc


def _ensure_cfg_mapping(data: Any) -> MutableMapping[str, Any]:
    """Valide que la configuration est un mapping mutable, sinon lève une erreur."""
    if data is None:
        return {}
    if isinstance(data, MutableMapping):
        return dict(data)
    if isinstance(data, Mapping):
        return dict(data)
    raise TypeError("Le fichier de configuration doit contenir un objet JSON (mapping).")


def _normalize_pools(data: Any) -> Sequence[Any]:
    """Normalise les données de pools en une séquence exploitable."""
    if isinstance(data, Mapping):
        if "pools" not in data:
            raise TypeError("Le fichier des pools doit contenir une clé 'pools'.")
        pools_value = data["pools"]
    else:
        pools_value = data

    if isinstance(pools_value, Sequence) and not isinstance(pools_value, (str, bytes, bytearray)):
        return list(pools_value)

    raise TypeError("Les pools doivent être une liste ou un objet JSON avec une clé 'pools'.")


def _to_jsonable(obj: Any) -> Any:
    """Convertit récursivement un objet en structure compatible JSON."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, Mapping):
        return {str(key): _to_jsonable(value) for key, value in obj.items()}

    if isinstance(obj, (list, tuple, set, frozenset)):
        return [_to_jsonable(item) for item in obj]

    if dataclasses.is_dataclass(obj):
        return _to_jsonable(dataclasses.asdict(obj))

    if hasattr(obj, "_asdict"):
        return _to_jsonable(obj._asdict())

    if isinstance(obj, Enum):
        return _to_jsonable(obj.value)

    if hasattr(obj, "__dict__"):
        return _to_jsonable(vars(obj))

    return str(obj)


def _prepare_result_payload(result: Any) -> MutableMapping[str, Any]:
    """Construit la charge utile normalisée à partir du résultat brut."""
    jsonable = _to_jsonable(result)
    if isinstance(jsonable, MutableMapping):
        payload: MutableMapping[str, Any] = dict(jsonable)
    elif isinstance(jsonable, Mapping):
        payload = dict(jsonable)
    else:
        payload = {"result": jsonable}

    payload.setdefault("version", VERSION)
    payload.setdefault("journal_path", DEFAULT_JOURNAL)
    return payload


def _build_parser() -> argparse.ArgumentParser:
    """Construit l'analyseur d'arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Calcule le contexte et la policy à partir des statistiques de pools."
    )
    parser.add_argument(
        "--pools",
        required=True,
        help="Chemin du fichier JSON contenant les statistiques des pools.",
    )
    parser.add_argument(
        "--cfg",
        help="Chemin du fichier JSON de configuration optionnel.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Force une sortie JSON sur une seule ligne.",
    )
    return parser


def _print_human_readable(payload: MutableMapping[str, Any]) -> None:
    """Affiche un résultat lisible pour un humain."""
    def _format(obj: Any) -> str:
        return json.dumps(_to_jsonable(obj), ensure_ascii=False, indent=2)

    print(f"Version: {payload.get('version')}")
    print(f"Journal: {payload.get('journal_path')}")

    if "context" in payload:
        print("Context:")
        print(_format(payload["context"]))

    if "policy" in payload:
        print("Policy:")
        print(_format(payload["policy"]))

    if "metrics" in payload:
        print("Metrics:")
        print(_format(payload["metrics"]))

    if "metrics_locales" in payload:
        print("Metrics locales:")
        print(_format(payload["metrics_locales"]))

    for key, value in payload.items():
        if key in {"context", "policy", "metrics", "metrics_locales", "version", "journal_path"}:
            continue
        print(f"{key}:")
        print(_format(value))


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée principal du CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        pools_data = _load_json_file(args.pools)
        pools = _normalize_pools(pools_data)

        if args.cfg:
            cfg_data = _load_json_file(args.cfg)
            cfg = _ensure_cfg_mapping(cfg_data)
        else:
            cfg = {}

        result = calculer_contexte_et_policy(
            pools_stats=list(pools),
            cfg=cfg,
            last_context=None,
            run_id=None,
            version=VERSION,
            journal_path=DEFAULT_JOURNAL,
        )

        payload = _prepare_result_payload(result)

        if args.json:
            print(json.dumps(_to_jsonable(payload), ensure_ascii=False, separators=(",", ":")))
        else:
            _print_human_readable(payload)

        return 0

    except FileNotFoundError as exc:
        print(f"Erreur de fichier: {exc}", file=sys.stderr)
    except ValueError as exc:
        print(f"Erreur de parsing JSON: {exc}", file=sys.stderr)
    except TypeError as exc:
        print(f"Erreur de typage: {exc}", file=sys.stderr)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Erreur lors du calcul: {exc}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())