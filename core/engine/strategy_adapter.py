"""Adaptateur de stratégie pour la sélection de contexte et de politique (V4.0.23).

Ce module encapsule l'orchestration entre la détection de contexte de marché et la
récupération de la politique d'allocation correspondante tout en gérant une
journalisation résiliente et silencieuse en cas de repli JSONL.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence
import sys

from core.market_signals import (
    MarketDecision,
    MarketParams,
    detect_market_context,
    get_allocation_policy_for_context,
    journaliser_signaux,
    load_params_from_config,
)


__all__ = ["calculer_contexte_et_policy"]


def _ensure_dict(value: Mapping[str, Any] | Iterable[tuple[str, Any]] | None) -> dict[str, Any]:
    """Retourner un dictionnaire à partir d'une structure compatible.

    Les entrées `None` produisent un dictionnaire vide. Les objets possédant un
    attribut ``items`` ou ``__iter__`` sont convertis de manière tolérante.
    """

    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, Mapping):
        return {str(key): val for key, val in value.items()}
    if isinstance(value, Iterable):
        converted: dict[str, Any] = {}
        for element in value:
            try:
                key, val = element  # type: ignore[misc]
            except Exception:
                continue
            converted[str(key)] = val
        if converted:
            return converted
    if hasattr(value, "__dict__"):
        return {
            str(key): val
            for key, val in vars(value).items()
            if not key.startswith("_")
        }
    return {}


def _ensure_list_of_dicts(value: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    """Sécuriser une séquence de dictionnaires décrivant les pools.

    Tout élément ``None`` ou non itérable est ignoré pour garantir une liste
    exploitable par les appels en aval.
    """

    if value is None:
        return []
    result: list[dict[str, Any]] = []
    iterator: Iterable[Any]
    if isinstance(value, Sequence):
        iterator = value
    else:
        iterator = list(value)
    for element in iterator:
        if element is None:
            continue
        result.append(_ensure_dict(element))
    return result


def _normaliser_policy(policy: Mapping[str, Any] | Iterable[tuple[str, Any]] | None) -> dict[str, Any]:
    """Normaliser une politique d'allocation sous forme de dictionnaire.

    Les clés sont converties en chaînes afin de faciliter la sérialisation.
    """

    if isinstance(policy, dict):
        return {str(key): value for key, value in policy.items()}
    if isinstance(policy, Mapping):
        return {str(key): value for key, value in policy.items()}
    if isinstance(policy, Iterable):
        normalized: dict[str, Any] = {}
        for element in policy:
            try:
                key, value = element  # type: ignore[misc]
            except Exception:
                continue
            normalized[str(key)] = value
        if normalized:
            return normalized
    if hasattr(policy, "__dict__"):
        return {
            str(key): value
            for key, value in vars(policy).items()
            if not key.startswith("_")
        }
    return {}


def _normalize_decision(decision: Any) -> tuple[str, Any | None, Mapping[str, Any]]:
    """Uniformiser une décision de marché en triplet (contexte, score, métriques)."""

    context: str = "inconnu"
    score: Any | None = None
    metrics: Mapping[str, Any] = {}

    if isinstance(decision, MarketDecision):
        context = getattr(decision, "context", context)
        score = getattr(decision, "score", None)
        metrics = _ensure_dict(getattr(decision, "metrics", None))
    elif isinstance(decision, Mapping):
        context = str(decision.get("context", context))
        score = decision.get("score")
        metrics = _ensure_dict(decision.get("metrics"))
    elif isinstance(decision, (list, tuple)):
        if decision:
            context = str(decision[0])
        if len(decision) > 1:
            score = decision[1]
        if len(decision) > 2:
            metrics = _ensure_dict(decision[2])
    elif decision is not None:
        context = str(decision)

    return context, score, metrics


def _append_jsonl(path: str, record: dict[str, Any]) -> None:
    """Ajouter un enregistrement JSONL en mode meilleur effort."""

    try:
        with open(path, "a", encoding="utf-8") as f:
            import json as _json

            f.write(_json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:  # best-effort
        print(f"[strategy_adapter] Fallback JSONL échoué: {exc}", file=sys.stderr)


def _journaliser_decision(
    *,
    context: str,
    score: Any | None,
    metrics: Mapping[str, Any],
    policy: Mapping[str, Any] | Iterable[tuple[str, Any]],
    last_context: str | None,
    run_id: str | None,
    journal_path: str,
    version: str,
) -> None:
    """Journaliser la décision en tentant plusieurs signatures avant repli."""

    policy_dict = _normaliser_policy(policy)
    record = {
        "context": context,
        "policy": dict(policy_dict),
        "score": score,
        "metrics": dict(metrics),
        "last_context": last_context,
        "run_id": run_id,
        "version": version,
    }

    attempts = (
        lambda: journaliser_signaux(journal_path=journal_path, **record),
        lambda: journaliser_signaux(journal_path, **record),
        lambda: journaliser_signaux(
            context=context,
            policy=policy_dict,
            journal_path=journal_path,
            score=score,
            metrics=record["metrics"],
            last_context=last_context,
            run_id=run_id,
            version=version,
        ),
        lambda: journaliser_signaux(
            context,
            policy_dict,
            journal_path,
            score,
            record["metrics"],
            last_context,
            run_id,
            version,
        ),
        lambda: journaliser_signaux(journal_path=journal_path, data=record),
        lambda: journaliser_signaux(journal_path, record),
        lambda: journaliser_signaux(data=record, journal_path=journal_path),
        lambda: journaliser_signaux(
            context=context,
            policy=policy_dict,
            journal_path=journal_path,
        ),
        lambda: journaliser_signaux(context, policy_dict, journal_path),
    )

    for attempt in attempts:
        try:
            attempt()
            return
        except TypeError:
            continue
        except Exception:
            continue

    try:
        journaliser_signaux(journal_path)
        return
    except Exception:
        pass

    _append_jsonl(journal_path, {**record, "_fallback": "jsonl"})


def calculer_contexte_et_policy(
    pools_stats: list[dict[str, Any]],
    cfg: dict[str, Any],
    last_context: str | None = None,
    run_id: str | None = None,
    version: str = "V4.0.23",
    journal_path: str = "journal_signaux.jsonl",
) -> dict[str, Any]:
    """Calculer le contexte de marché courant et la politique associée.

    Les paramètres de stratégie sont chargés à partir de la configuration et la
    journalisation est gérée avec des mécanismes de secours silencieux.
    """

    pools_valides = _ensure_list_of_dicts(pools_stats)
    cfg_valide = _ensure_dict(cfg)

    params: MarketParams | Mapping[str, Any] | None = None
    strategy_cfg = _ensure_dict(cfg_valide.get("strategy"))
    try:
        params = load_params_from_config(strategy_cfg)
    except TypeError:
        try:
            params = load_params_from_config(strategy_cfg, cfg_valide)
        except TypeError:
            try:
                params = load_params_from_config(cfg_valide)
            except Exception:
                params = None
    except Exception:
        params = None

    def _detect() -> MarketDecision | Mapping[str, Any] | Any:
        try:
            return detect_market_context(
                pools_valides,
                params=params,
                last_context=last_context,
            )
        except TypeError:
            pass
        try:
            return detect_market_context(
                pools_valides,
                params,
                last_context=last_context,
            )
        except TypeError:
            pass
        try:
            return detect_market_context(
                pools_valides,
                params=params,
            )
        except TypeError:
            pass
        try:
            return detect_market_context(pools_valides, params)
        except TypeError:
            pass
        try:
            return detect_market_context(
                pools_valides,
                last_context=last_context,
            )
        except TypeError:
            pass
        try:
            return detect_market_context(pools_valides, last_context)
        except TypeError:
            pass
        return detect_market_context(pools_valides)

    try:
        raw_decision = _detect()
    except Exception:
        raw_decision = {"context": "inconnu", "score": None, "metrics": {}}

    context, score, metrics = _normalize_decision(raw_decision)

    def _obtenir_policy() -> Mapping[str, Any] | Iterable[tuple[str, Any]]:
        try:
            return get_allocation_policy_for_context(context, params)
        except TypeError:
            pass
        try:
            return get_allocation_policy_for_context(context=context, params=params)
        except TypeError:
            pass
        try:
            return get_allocation_policy_for_context(context)
        except TypeError:
            pass
        return get_allocation_policy_for_context(context=context)

    try:
        policy_initiale = _obtenir_policy()
    except Exception:
        policy_initiale = {}

    policy_dict = _normaliser_policy(policy_initiale)

    _journaliser_decision(
        context=context,
        score=score,
        metrics=metrics,
        policy=policy_dict,
        last_context=last_context,
        run_id=run_id,
        journal_path=journal_path,
        version=version,
    )

    return {
        "context": context,
        "policy": dict(policy_dict),
        "metrics_locales": dict(metrics),
        "score": score,
        "last_context": last_context,
        "run_id": run_id,
        "version": version,
        "journal": journal_path,
    }