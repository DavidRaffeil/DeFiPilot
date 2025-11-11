# control/risk_signals.py — V4.8.1
from __future__ import annotations

"""Ce module calcule des signaux de risque simples à partir des indicateurs agrégés
issus de ``extraire_indicateurs_de_base``."""

from typing import Any, Iterable

_NIVEAUX_ORDONNES = ("OK", "A_SURVEILLER", "RISQUE")
_ORDRE_NIVEAUX = {niveau: index for index, niveau in enumerate(_NIVEAUX_ORDONNES)}


def _niveau_max(n1: str, n2: str) -> str:
    """Retourne le niveau le plus sévère entre n1 et n2."""
    ordre_n1 = _ORDRE_NIVEAUX.get(n1, -1)
    ordre_n2 = _ORDRE_NIVEAUX.get(n2, -1)
    if ordre_n1 >= ordre_n2:
        return n1
    return n2


def calculer_signaux_risque(indicateurs: dict[str, Any]) -> list[dict[str, Any]]:
    """Calcule les signaux de risque globaux à partir des indicateurs fournis."""
    nb_evenements = indicateurs.get("nb_evenements", 0)
    if nb_evenements == 0:
        signal = {
            "type": "global",
            "niveau": "A_SURVEILLER",
            "motifs": ["AUCUNE_DONNEE_RECENTE"],
            "details": {
                "nb_evenements": indicateurs.get("nb_evenements"),
                "ts_debut": indicateurs.get("ts_debut"),
                "ts_fin": indicateurs.get("ts_fin"),
            },
        }
        return [signal]

    niveau = "OK"
    motifs: list[str] = []

    context_courant = indicateurs.get("context_courant")
    score_moyen = indicateurs.get("score_moyen")
    metrics_brutes = indicateurs.get("metrics_locales_moyennes")
    metrics = metrics_brutes if isinstance(metrics_brutes, dict) else {}

    if context_courant == "defavorable":
        niveau = _niveau_max(niveau, "A_SURVEILLER")
        motifs.append("CONTEXTE_DEFAVORABLE")

    if isinstance(score_moyen, (int, float)) and not isinstance(score_moyen, bool):
        if score_moyen < 0.7:
            niveau = _niveau_max(niveau, "A_SURVEILLER")
            motifs.append("SCORE_FAIBLE")

    tvl_sum = metrics.get("tvl_sum")
    if isinstance(tvl_sum, (int, float)) and not isinstance(tvl_sum, bool):
        if tvl_sum < 500_000:
            niveau = _niveau_max(niveau, "A_SURVEILLER")
            motifs.append("TVL_FAIBLE")

    apr_mean = metrics.get("apr_mean")
    if isinstance(apr_mean, (int, float)) and not isinstance(apr_mean, bool):
        if apr_mean > 0.5:
            niveau = _niveau_max(niveau, "RISQUE")
            motifs.append("APR_TRES_ELEVE")

    volatility_cv = metrics.get("volatility_cv")
    if isinstance(volatility_cv, (int, float)) and not isinstance(volatility_cv, bool):
        if volatility_cv > 0.8:
            niveau = _niveau_max(niveau, "RISQUE")
            motifs.append("VOLATILITE_ELEVEE")

    motifs_uniques: list[str] = []
    motifs_vus = set()
    for motif in motifs:
        if motif not in motifs_vus:
            motifs_uniques.append(motif)
            motifs_vus.add(motif)

    signal = {
        "type": "global",
        "niveau": niveau,
        "motifs": motifs_uniques,
        "details": {
            "nb_evenements": indicateurs.get("nb_evenements"),
            "ts_debut": indicateurs.get("ts_debut"),
            "ts_fin": indicateurs.get("ts_fin"),
            "context_courant": context_courant,
            "context_precedent": indicateurs.get("context_precedent"),
            "score_moyen": score_moyen,
            "metrics_locales_moyennes": metrics or {},
        },
    }
    return [signal]


def resumer_niveau_risque(signaux: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Retourne un résumé agrégé des niveaux de risque observés dans les signaux."""
    signaux_list = list(signaux)
    if not signaux_list:
        return {
            "niveau_global": "INCONNU",
            "nb_signaux": 0,
            "repartition_niveaux": {},
            "signal_principal": None,
        }

    repartition_niveaux: dict[str, int] = {}
    niveau_global_valide: str | None = None

    for signal in signaux_list:
        niveau_signal = signal.get("niveau")
        if isinstance(niveau_signal, str):
            repartition_niveaux[niveau_signal] = repartition_niveaux.get(niveau_signal, 0) + 1
            if niveau_signal in _ORDRE_NIVEAUX:
                if niveau_global_valide is None:
                    niveau_global_valide = niveau_signal
                else:
                    niveau_global_valide = _niveau_max(niveau_global_valide, niveau_signal)

    niveau_global = niveau_global_valide if niveau_global_valide is not None else "INCONNU"

    signal_principal = None
    if niveau_global != "INCONNU":
        for signal in signaux_list:
            if signal.get("niveau") == niveau_global:
                signal_principal = signal
                break

    return {
        "niveau_global": niveau_global,
        "nb_signaux": len(signaux_list),
        "repartition_niveaux": repartition_niveaux,
        "signal_principal": signal_principal,
    }