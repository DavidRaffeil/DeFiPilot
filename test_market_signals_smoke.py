# test_market_signals_smoke.py — V4.0.4
# Exécution :
#   python test_market_signals_smoke.py
#
# NOTE IMPORT :
# - Si ton fichier est à core/market_signals.py, lance ce test depuis la racine du projet
#   et utilise l'import "from core.market_signals import ...".
# - Si besoin : set PYTHONPATH=.; python test_market_signals_smoke.py (Windows)
#               PYTHONPATH=. python test_market_signals_smoke.py (Linux/Mac)

from core.market_signals import (
    MarketParams,
    load_params_from_config,
    detect_market_context,
    journaliser_signaux,
)

# ---- Config simple pour les tests (identique à _DEFAULT_PARAMS, sauf min_samples=3 pour aller plus vite)
cfg = {
    "MARKET_SIGNALS": {
        "apr_up_threshold_pct": 5.0,
        "apr_down_threshold_pct": -5.0,
        "tvl_up_threshold_pct": 3.0,
        "tvl_down_threshold_pct": -3.0,
        "min_samples": 3,          # abaissé pour les tests
        "smoothing_alpha": 0.3,
        "cooldown_cycles": 0,
        "hysteresis_margin": 0.0,
        "weights_apr": 0.6,
        "weights_tvl": 0.4,
        "override_context": None,
    }
}
params: MarketParams = load_params_from_config(cfg)

RUN_VERSION = "V4.0.4-smoke"
RUN_ID = "smoke-tests"

def show(decision, label):
    print(f"\n[{label}] context={decision.context} score={decision.score:.3f} "
          f"apr_med={decision.indicators.apr_change_pct_median:.3f} "
          f"tvl_med={decision.indicators.tvl_change_pct_median:.3f} "
          f"samples={decision.indicators.sample_size} reason={decision.reason}")
    journaliser_signaux(decision, run_id=f"{RUN_ID}-{label}", version=RUN_VERSION, path_jsonl="journal_signaux.jsonl")

# ---- Cas 1 : BULL clair (APR et TVL en hausse nette)
pools_bull = [
    {"apr_change_pct": +10.0, "tvl_change_pct": +7.0},
    {"apr_change_pct": +9.0,  "tvl_change_pct": +5.5},
    {"apr_change_pct": +11.0, "tvl_change_pct": +6.0},
]

dec1 = detect_market_context(pools_bull, params, last_context="none")
show(dec1, "BULL")

# ---- Cas 2 : FLAT neutre (variations faibles)
pools_flat = [
    {"apr_change_pct": +1.0, "tvl_change_pct": 0.0},
    {"apr_change_pct": +0.5, "tvl_change_pct": +0.2},
    {"apr_change_pct":  0.0, "tvl_change_pct": -0.3},
]
dec2 = detect_market_context(pools_flat, params, last_context="flat")
show(dec2, "FLAT")

# ---- Cas 3 : BEAR clair (APR et TVL en baisse nette)
pools_bear = [
    {"apr_change_pct": -10.0, "tvl_change_pct": -6.0},
    {"apr_change_pct": -9.0,  "tvl_change_pct": -5.5},
    {"apr_change_pct": -11.0, "tvl_change_pct": -6.5},
]

dec3 = detect_market_context(pools_bear, params, last_context="none")
show(dec3, "BEAR")

print("\nJournal écrit dans: journal_signaux.jsonl")
print("Attendus rapides : BULL→context=bull, FLAT→context=flat, BEAR→context=bear")
