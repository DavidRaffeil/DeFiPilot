# core/exits_v5_5.py — V5.5.0
"""Logique d'exits automatique V5.5.

Cette version fournit une logique déterministe et minimale destinée à être
appelée par d'autres composants (ex: ``journal_daemon.py``). Elle repose
exclusivement sur la valeur ``mode_global_v5_5`` et n'utilise pas de dépendances
externes.
"""

from __future__ import annotations

from typing import Any, Mapping

VERSION: str = "5.5.0"


def _normaliser_mode(mode_global_v5_5: str | None) -> str | None:
    """Normalise le mode global pour faciliter les comparaisons.

    Parameters
    ----------
    mode_global_v5_5 : str | None
        Valeur brute, potentiellement vide ou non renseignée.

    Returns
    -------
    str | None
        Chaîne en majuscules sans espaces superflus, ou ``None`` si absente ou
        vide.
    """

    if mode_global_v5_5 is None:
        return None
    if not isinstance(mode_global_v5_5, str):
        raise ValueError("mode_global_v5_5 doit être une chaîne ou None.")

    normalise = mode_global_v5_5.strip()
    return normalise.upper() if normalise else None


def est_mode_exit_total(mode_global_v5_5: str | None) -> bool:
    """Indique si le mode impose une sortie totale.

    Parameters
    ----------
    mode_global_v5_5 : str | None
        Mode global tel que reçu (avant normalisation).

    Returns
    -------
    bool
        ``True`` si le mode correspond à « PANIC » (sortie complète), sinon
        ``False``.
    """

    mode_normalise = _normaliser_mode(mode_global_v5_5)
    return mode_normalise == "PANIC"


def determiner_exits_v5_5(
    *, mode_global_v5_5: str | None, strategy_cfg: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Détermine les exits à appliquer selon ``mode_global_v5_5``.

    La logique actuelle (C.1) applique des règles simples :

    - ``PANIC``  ➜ sortie totale (segments Prudent, Modere, Risque)
    - ``CRISE``  ➜ sortie sur le segment Risque uniquement
    - Autre/None ➜ aucune sortie

    Parameters
    ----------
    mode_global_v5_5 : str | None
        Mode global à interpréter. Les valeurs sont normalisées via
        ``strip().upper()``. Les valeurs vides ou None sont considérées comme
        absence d'exit.
    strategy_cfg : Mapping[str, Any] | None, optional
        Configuration de stratégie (ignorée en version C.1). Si fournie, doit
        être un ``Mapping`` sous peine de lever ``ValueError``.

    Returns
    -------
    dict[str, Any]
        Dictionnaire JSON-sérialisable décrivant les sorties demandées.

    Raises
    ------
    ValueError
        Si ``strategy_cfg`` n'est pas ``None`` ni un ``Mapping``.
    """

    if strategy_cfg is not None and not isinstance(strategy_cfg, Mapping):
        raise ValueError("strategy_cfg doit être un Mapping ou None.")

    mode_normalise = _normaliser_mode(mode_global_v5_5)

    if mode_normalise == "PANIC":
        cibles = {"Prudent": True, "Modere": True, "Risque": True}
        exit_global = True
        motif = "Mode PANIC : sortie totale sur tous les segments."
    elif mode_normalise == "CRISE":
        cibles = {"Prudent": False, "Modere": False, "Risque": True}
        exit_global = True
        motif = "Mode CRISE : sortie ciblée sur le segment Risque."
    else:
        cibles = {"Prudent": False, "Modere": False, "Risque": False}
        exit_global = False
        motif = "Aucun exit demandé par le mode global."

    return {
        "mode_global_v5_5": mode_normalise,
        "exit": exit_global,
        "cibles": cibles,
        "motif": motif,
        "version": VERSION,
    }


if __name__ == "__main__":
    exemples = ["PANIC", "CRISE", "   "]
    for exemple in exemples:
        resultat = determiner_exits_v5_5(mode_global_v5_5=exemple)
        print(f"Entrée: {exemple!r} -> {resultat}")