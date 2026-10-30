# Changelog — DeFiPilot

Toutes les évolutions notables du projet DeFiPilot sont documentées dans ce fichier.

---

## [v6.6.0-dev] — 2026-10-30

### Ajouté (Phase 4 : Gestion Automatisée du Carburant et Wrapping Natif WPOL ⇄ POL)
- **Module `GasTankManager` (`core/execution/gas_tank.py`)** :
  - Lecture des soldes on-chain en POL natif et WPOL (`0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270`) convertis en unités lisibles (18 décimales).
  - Ravitaillement automatique pré-swap (`check_and_refuel()`) par désenveloppement (`withdraw`) de WPOL lorsque la réserve de POL natif descend sous le seuil minimal.
  - Détection du seuil critique bloquant (`is_gas_critical()`) et exception `GasCriticalError`.
  - Conversion automatique du surplus de POL natif en WPOL (`check_and_sweep_excess_gas()`) via `deposit()` lorsque le solde dépasse le plafond configuré.
  - Respect strict du mode `dry_run=True` (simulation journalisée sans signature ni transaction on-chain).
- **Intégration Exécuteur & Moteur de Stratégie** :
  - Contrôle et ravitaillement pré-swap intégrés dans `core/executor_real.py` (`RealExecutor`, `executer_action_reelle`), `core/execution/executor_real.py` et `core/swap_reel.py`.
  - Vérification pré-cycle (suspension propre en cas de gas critique) et sweep de l'excédent en fin de cycle dans `core/strategy_engine.py`.
- **Configuration centralisée (`config.py` & `core/config.py`)** :
  - `GAS_MIN_POL_RESERVE` (défaut : `5.0`)
  - `GAS_TARGET_POL_RESERVE` (défaut : `10.0`)
  - `GAS_CRITICAL_THRESHOLD` (défaut : `1.0`)
  - `GAS_MAX_POL_RESERVE` (défaut : `25.0`)
  - `GAS_AUTO_WRAP_ENABLED` (défaut : `True`)
- **Tests automatisés** :
  - Suite de tests unitaires `tests/unit/test_gas_tank.py`, `tests/unit/test_executor_real.py`, `tests/unit/test_strategy_gas_integration.py`.
  - Test E2E du cycle de vie complet `tests/e2e/test_e2e_gas_tank_lifecycle.py` (total : **214 tests au vert**).

---

## [v6.5.0] — 2026-10-30

### Ajouté (Phase 3 : Architecture Multi-DEX sur Polygon)
- Adaptateurs DEX (`UniswapV3Adapter`, `QuickswapAdapter`, `SushiswapAdapter`) et routeur d'arbitrage concurrent `DEXRouter` (`core/dex/`).
- Intégration du routage Multi-DEX dans `StrategyEngine`, `executor_real.py` et `swap_reel.py` sous le feature flag `FEATURE_MULTI_DEX`.
- Couverture portée à **190 tests unitaires et E2E au vert**.

---

## [v6.4.0] — 2026-10-19

### Ajouté (Phase 2 : Gestion Active du Capital)
- Articulation complète de `TimeDecayCompounder` et `ProfitSweeper` via `CapitalCycleManager` dans `main_v6_core.py`.
- Callbacks sécurisés `reinvest_action` et `secure_action` avec validation stricte de l'adresse de réserve (`CapitalActionError`).
