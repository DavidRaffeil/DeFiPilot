![DeFiPilot banner](assets/defipilot_banner.png)

> 🗣️ **Langue / Language :** le bot fonctionne uniquement en **français** pour le moment.  
> The bot currently works **in French only** for the moment.

![Version](https://img.shields.io/badge/Version-V6.5.0%20Stable-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Made in France](https://img.shields.io/badge/Made%20in-France-lightgrey)
![Developed with Antigravity & Gemini](https://img.shields.io/badge/Developed%20with-Antigravity%20%26%20Gemini-purple)
![Open Source](https://img.shields.io/badge/License-CC--BY--NC--SA%204.0-green)
![Polygon Network](https://img.shields.io/badge/Network-Polygon-purple)

---

## 📚 Sommaire / Table of Contents
1. [Introduction / Introduction](#1-introduction--introduction)  
2. [Fonctionnalités principales / Key Features](#2-fonctionnalites-principales--key-features)  
3. [Aperçu visuel / Visual Overview](#3-apercu-visuel--visual-overview)  
4. [Nouveautés / What's New — Version 6.5.0](#4-nouveautes--whats-new--version-650)  
5. [Historique des versions / Past Versions](#5-historique-des-versions--past-versions)  
6. [Caractéristiques techniques / Technical Highlights](#6-caracteristiques-techniques--technical-highlights)  
7. [Prérequis / Requirements](#7-prerequis--requirements)  
8. [Installation / Installation](#8-installation--installation)  
9. [Utilisation / Usage](#9-utilisation--usage)  
10. [Feuille de route / Roadmap](#10-feuille-de-route--roadmap)  
11. [Vision du projet / Project Vision](#11-vision-du-projet--project-vision)  
12. [FAQ / Foire aux questions](#12-faq--foire-aux-questions)  
13. [À propos de l’auteur / About the Author](#13-a-propos-de-lauteur--about-the-author)  
14. [Crédits techniques / Technical Credits](#14-credits-techniques--technical-credits)  
15. [Licence / License](#15-licence--license)  
16. [Dernière révision / Last Review](#16-derniere-revision--last-review)

---

# 1. 🧭 Introduction / Introduction

## FR
DeFiPilot est un bot DeFi autonome conçu pour analyser en continu les opportunités disponibles sur les échanges décentralisés (DEX), calculer la rentabilité réelle des pools, puis sélectionner les meilleures options en fonction d’un profil d’investissement configurable. Le système fonctionne aussi bien en mode simulation qu’en mode réel selon la configuration utilisateur.

Son architecture repose sur quatre principes :  
- **Robustesse** : tolérance aux erreurs réseau, redondances RPC, vérifications multiples et garde-fous on-chain.  
- **Modularité** : possibilité d’étendre facilement les fonctionnalités via des adaptateurs et modules spécialisés.  
- **Transparence** : journalisation complète (CSV + JSONL), état sauvegardé, historique visible.  
- **Automatisation** : analyse continue, décisions guidées par les profils, routage optimal et reprise automatique.

DeFiPilot vise à constituer une base sérieuse et pérenne pour gérer des investissements DeFi automatisés, tout en intégrant des mécanismes de sécurité rigoureux pour réduire les risques opérationnels.

## EN
DeFiPilot is an autonomous DeFi bot designed to continuously analyze opportunities across decentralized exchanges (DEX), compute real profitability for liquidity pools, and select the best options according to a configurable investment profile. The system runs in both simulation and real execution modes depending on user configuration.

Its architecture relies on four core principles:  
- **Robustness**: tolerance to network failures, RPC redundancy, multiple safety checks, and on-chain guardrails.  
- **Modularity**: easily extendable through specialized adapters and modular components.  
- **Transparency**: full logging (CSV + JSONL), state storage, visible history.  
- **Automation**: continuous analysis, profile‑driven decisions, optimal routing, and automatic state recovery.

DeFiPilot aims to be a serious and sustainable foundation for automated DeFi investment management while embedding safety mechanisms to minimize operational risks.

---

# 2. ⚙️ Fonctionnalités principales / Key Features

## FR
- Analyse automatique des pools (APR, TVL, volume, volatilité, slippage).  
- Scoring pondéré basé sur plusieurs profils (Prudent, Modéré, Risque).  
- **Routage Multi-DEX dynamique (Nouveau v6.5.0)** : interrogation concurrente et arbitrage de cotation en direct entre Uniswap V3, QuickSwap V3 et SushiSwap V2 sur Polygon Mainnet.  
- Mode simulation complet avec garde-fou (`DryRunGuard`) pour tests sécurisés sans risque financier.  
- Mode réel unifié avec moteur d'exécution Web3, gestion EIP-1559, slippage guard, normalisation automatique des décimales ERC-20 (6 vs 18 décimales) et confirmations on-chain.  
- **Gestion active du capital** : sécurisation automatique des profits (`ProfitSweeper`), réinvestissement dégressif (`TimeDecayCompounder`), et callbacks d'arbitrage sécurisés avec injection de dépendances.  
- Interface graphique Tkinter avec rafraîchissement automatique.  
- Multi-wallets avec séparation des usages.  
- Supervision IA via ControlPilot (signaux contextuels).  
- Résilience et reprise automatique après coupure (fichiers `state.json` et `health.json`).  
- Journalisation détaillée (JSONL + CSV).  
- Architecture modulaire extensible.

## EN
- Automatic pool analysis (APR, TVL, volume, volatility, slippage).  
- Weighted scoring based on multiple profiles (Conservative, Moderate, Risk).  
- **Dynamic Multi-DEX Routing (New v6.5.0)**: concurrent quoting and route comparison across Uniswap V3, QuickSwap V3, and SushiSwap V2 on Polygon Mainnet.  
- Full simulation mode with safety guard (`DryRunGuard`) for zero-risk testing.  
- Unified real execution engine with Web3 broadcast, EIP-1559 gas calibration, slippage protection, dynamic ERC-20 decimal handling (6 vs 18 decimals), and on-chain confirmations.  
- **Active capital management**: automated profit sweeping (`ProfitSweeper`), dynamic time-decay compounding (`TimeDecayCompounder`), and secured routing callbacks with dependency injection.  
- Tkinter GUI with automatic refresh.  
- Multi‑wallet support.  
- AI supervision via ControlPilot (context signals).  
- System resilience and automatic resume after shutdown (`state.json` and `health.json`).  
- Detailed logging (JSONL + CSV).  
- Modular and extensible architecture.

---

# 3. 🖥️ Aperçu visuel / Visual Overview

![Interface DeFiPilot V5.0](assets/screenshot_defipilot_gui_v50.png)

## FR
L’interface graphique de DeFiPilot présente les métriques clés, l’état du bot, les signaux AI de ControlPilot, la liste des pools analysées, et les indicateurs de stratégie actifs.

## EN
DeFiPilot’s graphical interface displays key metrics, bot status, ControlPilot AI signals, list of analyzed pools, and active strategy indicators.

---

# 4. 🆕 Nouveautés / What's New — Version 6.5.0

## 📘 Fr
- **Agrégateur & Routeur Multi-DEX (`FEATURE_MULTI_DEX=True`) :**
  - Architecture modulaire avec interface unifiée `BaseDEXAdapter` et implémentation de 3 adaptateurs natifs Polygon Mainnet : **Uniswap V3** (QuoterV2 multi-tiers), **QuickSwap V3** (Algebra Quoter), et **SushiSwap V2** (UniswapV2Router02).
  - Moteur de comparaison parallèle `DEXRouter` sélectionnant automatiquement la route optimale maximisant le montant net reçu avec isolation des timeouts réseau.
- **Unification du Moteur d'Exécution Réelle (`swap_reel.py` & `executor_real.py`) :**
  - Passage direct des blueprints de cotation et de transaction (`prebuilt_quote`, `prebuilt_tx`) sans double appel RPC.
  - Gestion dynamique et automatique des décimales ERC-20 (`6` décimales pour `USDC`/`USDT`, `18` décimales pour `POL`/`WPOL`/`WETH`).
  - Pipeline Web3 complet et sécurisé : failover RPC (`RPCManager`), approbation conditionnelle (`approve`), frais dynamiques EIP-1559 (`GasEstimator`), et contrôle strict du verrou `DryRunGuard`.
  - Repli automatique (fallback) transparent vers l'adaptateur nominal en cas de désactivation du mode multi-DEX.
- **Validation On-Chain réelle sur Polygon Mainnet :**
  - Micro-swap réel exécuté et validé avec succès (1.0 USDC -> 10.679262 WPOL sur SushiSwap V2, bloc #96432559).
  - Script dédié d'audit et d'exécution sécurisée `execute_multidex_real_swap.py` avec diagnostic comptable précis (USDC, gaz natif POL et crédit WPOL).
- **Suite de tests automatisés :** Portée à **190 tests unitaires et d'intégration validés à 100 %**.

---

## 📗 En
- **Multi-DEX Aggregator & Router (`FEATURE_MULTI_DEX=True`):**
  - Modular architecture built on unified `BaseDEXAdapter` with 3 production adapters for Polygon Mainnet: **Uniswap V3** (QuoterV2 dynamic fee tiers), **QuickSwap V3** (Algebra Quoter), and **SushiSwap V2** (UniswapV2Router02).
  - Parallel routing engine `DEXRouter` with isolated timeouts, automatically executing on the highest yielding route.
- **Real Execution Engine Unification (`swap_reel.py` & `executor_real.py`):**
  - Direct pipeline forwarding of transaction blueprints (`prebuilt_quote`, `prebuilt_tx`), avoiding duplicate RPC roundtrips.
  - Dynamic ERC-20 decimal parsing (`6` decimals for `USDC`/`USDT`, `18` decimals for `POL`/`WPOL`/`WETH`).
  - Hardened Web3 pipeline: multi-node failover (`RPCManager`), conditional ERC-20 allowances (`approve`), EIP-1559 dynamic gas estimation (`GasEstimator`), and strict safety checks (`DryRunGuard`).
  - Transparent single-DEX fallback when multi-DEX routing is disabled or unavailable.
- **Live On-Chain Polygon Mainnet Validation:**
  - Real micro-swap executed and confirmed (1.0 USDC -> 10.679262 WPOL on SushiSwap V2, block #96432559).
  - Dedicated diagnostic execution script `execute_multidex_real_swap.py` providing detailed balance deltas (USDC, POL gas, WPOL credited).
- **Automated Test Suite:** Upgraded to **190 passing unit and integration tests (100% green)**.

---

# 5. 🕓 Historique des versions / Past Versions

## 📘 Fr
- **V6.5.0 :** Architecture de routage Multi-DEX (Uniswap V3, QuickSwap V3, SushiSwap V2), validation réelle on-chain sur Polygon Mainnet (1.0 USDC -> 10.68 WPOL), unification complète du moteur d'exécution réelle et 190 tests au vert.  
- **V6.4.0 :** Finalisation Phase 2.3 (articulation Option B du capital, callbacks sécurisés simulation/réel avec injection d'exécuteurs, garde-fous stricts sur l'adresse de réserve, 93 tests au vert).  
- **V6.3.0 :** Couche de gestion active du capital (`ProfitSweeper` + `TimeDecayCompounder`), orchestration `CapitalCycleManager` dans `main_v6_core.py` et validation de 72 tests au vert.  
- **V6.2.0 :** Moteur d'exécution on-chain réel validé sur Polygon Mainnet, intégration PoA Bor, GasEstimator EIP-1559 calibré, SlippageGuard, script de swap sécurisé et 45 tests unitaires au vert.  
- **V6.1 :** Moteur de simulation sécurisé (Dry-Run Guard), algorithme de scoring fiabilisé, gestion de résilience système (`system_health.py`) et validation complète par tests E2E (29 tests au vert).  
- **V6.0 :** Refonte Core V6, scoring des pools, daemon de journalisation de stratégie sécurisé, refonte de la couche d'exécution réelle et nettoyage legacy.  
- **V5.5 :** Exits automatiques basés sur le contexte, application des seuils Deep Search V5.4, stratégie finalisée (`strategy_v5_5.json`), stabilisation complète du daemon.  
- **V5.3 :** Journal stratégique dédié (`journal_strategy.jsonl`), intégration complète des signaux normalisés de ControlPilot, stabilisation du daemon.  
- **V5.2 :** Rééquilibrage automatique du portefeuille, signaux pondérés, snapshots de rééquilibrage, mise à jour scoring/stratégie.  
- **V5.1 :** Nouveau moteur de signaux IA, normalisation avancée, scoring dynamique, stratégie enrichie.  
- **V5.0 :** Intégration IA ControlPilot, stabilité renforcée, dashboard optimisé.  
- **V4.9 :** Agrégation avancée des signaux + détection d’anomalies.  
- **V4.8 :** Collecte des signaux simples (début ControlPilot).  
- **V4.7 :** Stabilisation complète du mode réel + reprise automatique.  
- **V4.6 :** Stratégie dynamique avec ajustements automatiques.  
- **V4.5 :** Améliorations GUI + affichage contextuel.  
- **V4.2 :** Scoring pondéré + gestion des profils.  
- **V4.0 :** Passage au simulateur complet.

---

## 📗 En
- **V6.5.0:** Multi-DEX routing architecture (Uniswap V3, QuickSwap V3, SushiSwap V2), live on-chain validation on Polygon Mainnet (1.0 USDC -> 10.68 WPOL), unified real execution engine, and 190 passing tests.  
- **V6.4.0:** Completed Phase 2.3 (Option B capital flow articulation, secured simulation/real callbacks with executor injection, strict reserve wallet safeguards, 93 passing tests).  
- **V6.3.0:** Active capital management layer (`ProfitSweeper` + `TimeDecayCompounder`), `CapitalCycleManager` orchestration in `main_v6_core.py`, and 72 passing tests.  
- **V6.2.0:** Validated live on-chain execution engine on Polygon Mainnet, Bor PoA middleware integration, calibrated EIP-1559 GasEstimator, SlippageGuard, guarded test swap script, and 45 passing unit tests.  
- **V6.1:** Secured dry-run simulation mode (Dry-Run Guard), refined scoring algorithm, system health resilience (`system_health.py`), and full validation with 29 E2E integration tests.  
- **V6.0:** Core V6 refactoring, pool scoring engine, secure strategy logging daemon, execution layer fixes and workspace reorganization.  
- **V5.5:** Automatic exits based on market context, integration of Deep Search V5.4 thresholds, finalized strategy file (`strategy_v5_5.json`), full daemon stabilization.  
- **V5.3:** Dedicated strategic journal (`journal_strategy.jsonl`), full ControlPilot signal integration.  
- **V5.2:** Automatic portfolio rebalancing, weighted signals, snapshots, and stabilized pipeline.  
- **V5.1:** New AI signal engine, dynamic scoring, enriched strategy.  
- **V5.0:** ControlPilot AI integration + real-mode stabilization.  
- **V4.9:** Advanced signal aggregation + anomaly detection.  
- **V4.8:** Simple signal collection (start of ControlPilot).  
- **V4.7:** Full real-mode stabilization + auto-resume.  
- **V4.6:** Dynamic strategy with automatic adjustments.  
- **V4.5:** GUI improvements + contextual display.  
- **V4.2:** Weighted scoring + profile management.  
- **V4.0:** Full simulation mode.

---

# 6. 🧱 Caractéristiques techniques / Technical Highlights

## FR
DeFiPilot repose sur une architecture modulaire, pensée pour garantir évolutivité et stabilité :

- **`main_v6_core.py` / `run_defipilot_v6.py`** — Points d'entrée principaux du moteur V6, orchestration unifiée du capital (`CapitalCycleManager`) et callbacks d'exécution (`reinvest_action`, `secure_action`).  
- **`core/dex/`** — Couche de routage Multi-DEX : adaptateur de base (`base.py`), adaptateurs DEX (`uniswap_v3.py`, `quickswap.py`, `sushiswap.py`), comparateur parallèle (`router.py`) et factory d'initialisation (`factory.py`).  
- **`core/`** — Analyse, scoring des pools, gestion active du capital (`capital/`), garde-fous (`guardrails.py`, `dry_run_guard.py`), suivi de santé système (`system_health.py`), validation d'environnement (`env_validator.py`), moteur d'exécution unifié (`swap_reel.py`, `executor_real.py`) et connecteurs Web3 (`execution/` avec `rpc_manager.py`, `gas_estimator.py`, `slippage_guard.py`).  
- **`scripts/`** — Outils opérationnels contrôlés (`execute_multidex_real_swap.py`, `execute_controlled_test_swap.py`, `preflight_check.py`).  
- **`config/`** — Configurations stratégiques (`strategy_v6_0.json`, `strategy_v5_5.json`), paramètres de seuil et de compounding.  
- **`journal_daemon_v6_secure.py` / `analyser_logs.py`** — Daemon de suivi de stratégie et utilitaire d'analyse des journaux.  
- **`tests/`** — Suite de 190 tests automatisés couvrant les adaptateurs multi-DEX, la sélection de route, la résilience, le gaz EIP-1559, le slippage, le mode dry-run, le balayage de profits, le compounding et l'exécution réelle mockée.  
- **`data/`** — État persistant du bot (`state.json`, `health.json`).

Le bot utilise principalement **Python 3.11**, **Web3.py**, **Tkinter**, **Pandas**, et l’API **DefiLlama**.

## EN
DeFiPilot is built on a modular architecture designed for scalability and stability:

- **`main_v6_core.py` / `run_defipilot_v6.py`** — Core entry points for the V6 engine execution, unified capital orchestration (`CapitalCycleManager`), and execution callbacks (`reinvest_action`, `secure_action`).  
- **`core/dex/`** — Multi-DEX routing layer: base adapter (`base.py`), DEX adapters (`uniswap_v3.py`, `quickswap.py`, `sushiswap.py`), parallel comparison router (`router.py`), and factory (`factory.py`).  
- **`core/`** — Analysis, pool scoring, active capital management (`capital/`), safety guards (`guardrails.py`, `dry_run_guard.py`), system health management (`system_health.py`), environment validation (`env_validator.py`), unified execution engine (`swap_reel.py`, `executor_real.py`), and Web3 toolset (`execution/` with `rpc_manager.py`, `gas_estimator.py`, `slippage_guard.py`).  
- **`scripts/`** — Controlled operational tools (`execute_multidex_real_swap.py`, `execute_controlled_test_swap.py`, `preflight_check.py`).  
- **`config/`** — Strategic configurations (`strategy_v6_0.json`, `strategy_v5_5.json`), sweeping thresholds, and compounding parameters.  
- **`journal_daemon_v6_secure.py` / `analyser_logs.py`** — Secure background strategy daemon and log analytics tool.  
- **`tests/`** — Automated test suite with 190 tests covering multi-DEX adapters, routing selection, resilience, EIP-1559 gas estimation, slippage, dry-run safety, profit sweeping, dynamic compounding, and mocked live execution.  
- **`data/`** — State persistence engine (`state.json`, `health.json`).

The bot relies mainly on **Python 3.11**, **Web3.py**, **Tkinter**, **Pandas**, and the **DefiLlama** API.

---

# 7. 🔧 Prérequis / Requirements

## FR
- Python **3.11+**  
- Accès RPC Polygon (Infura, Alchemy, QuickNode ou PublicNode)  
- Wallet compatible (Rabby, MetaMask)  
- Connexion Internet stable  
- Git installé

## EN
- Python **3.11+**  
- Polygon RPC access (Infura, Alchemy, QuickNode, or PublicNode)  
- Compatible wallet (Rabby, MetaMask)  
- Stable Internet connection  
- Git installed

---

# 8. ⚙️ Installation / Installation

## FR
1. **Cloner le dépôt :**  
`git clone https://github.com/DavidRaffeil/DeFiPilot.git`  
`cd DeFiPilot`

2. **Créer l’environnement virtuel et installer les dépendances :**  
`python3.11 -m venv .venv`  
`source .venv/bin/activate` *(Windows : `.venv\Scripts\activate`)*  
`pip install -U pip`  
`pip install -r requirements.txt`

3. **Configurer le fichier `.env` :**  
`NETWORK=polygon`  
`POLYGON_RPC_URL=https://polygon-mainnet.infura.io/v3/YOUR_PROJECT_ID`  
`WALLET_ADDRESS=YOUR_WALLET_ADDRESS`  
`LOG_LEVEL=INFO`

4. **Vérifier l’installation :**  
`python scripts/preflight_check.py`

## EN
1. **Clone the repository:**  
`git clone https://github.com/DavidRaffeil/DeFiPilot.git`  
`cd DeFiPilot`

2. **Create a virtual environment and install dependencies:**  
`python3.11 -m venv .venv`  
`source .venv/bin/activate` *(Windows: `.venv\Scripts\activate`)*  
`pip install -U pip`  
`pip install -r requirements.txt`

3. **Configure the `.env` file:**  
`NETWORK=polygon`  
`POLYGON_RPC_URL=https://polygon-mainnet.infura.io/v3/YOUR_PROJECT_ID`  
`WALLET_ADDRESS=YOUR_WALLET_ADDRESS`  
`LOG_LEVEL=INFO`

4. **Verify installation:**  
`python scripts/preflight_check.py`

---

# 9. ▶️ Utilisation / Usage

## FR
- **Lancement V6 Core (Mode principal) :** `python run_defipilot_v6.py`
- **Exécution de la suite de tests automatisés (190 tests) :** `pytest`
- **Test de pré-vol environnement :** `python scripts/preflight_check.py`
- **Diagnostic de routage Multi-DEX (Simulation Dry-Run) :** `python scripts/execute_multidex_real_swap.py`
- **Test de swap contrôlé (Dry-Run historique) :** `python scripts/execute_controlled_test_swap.py --dry-run`
- **Lancement du Daemon de Journalisation :** `python journal_daemon_v6_secure.py`
- **Analyse des journaux d'exécution :** `python analyser_logs.py`

## EN
- **Launch V6 Core Engine (Main mode):** `python run_defipilot_v6.py`
- **Run automated test suite (190 tests):** `pytest`
- **Environment preflight check:** `python scripts/preflight_check.py`
- **Multi-DEX Routing Diagnostic (Simulation Dry-Run):** `python scripts/execute_multidex_real_swap.py`
- **Controlled test swap (Legacy Dry-Run):** `python scripts/execute_controlled_test_swap.py --dry-run`
- **Launch Secure Background Logging Daemon:** `python journal_daemon_v6_secure.py`
- **Analyze execution logs:** `python analyser_logs.py`

---

# 10. 🚀 Feuille de route / Roadmap

## 📘 Fr

### Prochaines versions
- **V6.6 :** Gestion automatisée du wrap/unwrap de tokens natifs (WPOL <-> POL) et gestion dynamique des réserves de gaz.  
- **V6.7 :** Extension multi-chain (Arbitrum, Optimism, Base).  
- **V7.0 :** Synchronisation multi-bots (DeFiPilot + ControlPilot).  

### Versions finalisées
- **V6.5.0 :** Routage Multi-DEX (Uniswap V3, QuickSwap V3, SushiSwap V2), micro-swap réel validé on-chain sur Polygon Mainnet, unification du moteur d'exécution et 190 tests unitaires/E2E passants.  
- **V6.4.0 :** Finalisation Phase 2.3 (articulation Option B du capital, callbacks sécurisés simulation/réel avec injection d'exécuteurs, garde-fous stricts sur l'adresse de réserve, 93 tests au vert).  
- **V6.3.0 :** Gestion du capital (`ProfitSweeper`, `TimeDecayCompounder`), orchestration `CapitalCycleManager` et 72 tests automatisés validés.  
- **V6.2.0 :** Moteur d'exécution on-chain validé en direct sur Polygon, intégration PoA Bor, gestion EIP-1559, SlippageGuard et 45 tests unitaires.  
- **V6.1 :** Simulation sécurisée (Dry-Run Guard), scoring de rééquilibrage, gestion de santé système et suite de 29 tests E2E.  
- **V6.0 :** Mode unifié V6 Core, scoring des pools, daemon de journalisation sécurisé, réorganisation du dépôt.  
- **V5.5 :** Exits automatiques, intégration des seuils Deep Search, stratégie finalisée `strategy_v5_5.json`, stabilisation du daemon.  
- **V5.3 :** Journal stratégique dédié (`journal_strategy.jsonl`), intégration complète des signaux ControlPilot.  
- **V5.2 :** Rééquilibrage automatique, signaux pondérés, snapshots et pipeline stabilisé.  
- **V5.1 :** Nouveau moteur de signaux IA, scoring dynamique et stratégie enrichie.  
- **V5.0 :** Intégration ControlPilot + stabilisation mode réel.

---

## 📗 En

### Upcoming Versions
- **V6.6:** Automated native token wrapping/unwrapping (WPOL <-> POL) and dynamic gas reserve management.  
- **V6.7:** Multi-chain expansion (Arbitrum, Optimism, Base).  
- **V7.0:** Multi-bot orchestration and synchronization (DeFiPilot + ControlPilot).  

### Completed Versions
- **V6.5.0:** Multi-DEX routing (Uniswap V3, QuickSwap V3, SushiSwap V2), live on-chain micro-swap validation on Polygon Mainnet, unified execution engine, and 190 unit/E2E tests passing.  
- **V6.4.0:** Completed Phase 2.3 (Option B capital flow articulation, secured simulation/real callbacks with executor injection, strict reserve wallet safeguards, 93 passing tests).  
- **V6.3.0:** Capital management layer (`ProfitSweeper`, `TimeDecayCompounder`), `CapitalCycleManager` orchestration, and 72 validated automated tests.  
- **V6.2.0:** Validated live on-chain execution on Polygon Mainnet, Bor PoA integration, EIP-1559 handling, SlippageGuard, and 45 unit tests.  
- **V6.1:** Secured dry-run simulation, rebalancing scoring, system health resilience, and 29 E2E test suite.  
- **V6.0:** Unified V6 Core mode, pool scoring engine, secure background logging daemon, codebase cleanup.  
- **V5.5:** Automatic exits, Deep Search threshold integration, finalized `strategy_v5_5.json`, full daemon stabilization.  
- **V5.3:** Dedicated strategic journal (`journal_strategy.jsonl`), full ControlPilot signal integration.  
- **V5.2:** Automatic rebalancing, weighted signals, snapshots, and stabilized pipeline.  
- **V5.1:** New AI signal engine, dynamic scoring, enriched strategy.  
- **V5.0:** ControlPilot integration + real-mode stabilization.

---

# 11. 🌍 Vision du projet / Project Vision

## FR
DeFiPilot vise à devenir une plateforme de gestion automatisée complète regroupant :  
- Analyse multi‑DEX, multi‑blockchains.  
- Stratégies dynamiques ajustées selon le marché.  
- Modules complémentaires (ControlPilot, LabPilot).  
- Architecture transparente et robuste centrée sur la sécurité et la pédagogie.

## EN
DeFiPilot aims to evolve into a complete automated management platform including:  
- Multi‑DEX, multi‑chain analysis.  
- Dynamic strategies adjusted to market conditions.  
- Complementary modules (ControlPilot, LabPilot).  
- Transparent and robust architecture focused on safety and clarity.

---

# 12. ❓ Foire aux questions / FAQ

## FR
**1. DeFiPilot effectue‑t‑il des transactions automatiquement ?**  
Oui, si le mode réel est activé et confirmé via l'environnement d'exécution. En mode simulation, aucune transaction blockchain n’est envoyée grâce au garde-fou `DryRunGuard`.

**2. Comment fonctionne le routage Multi-DEX ?**  
Le routeur interroge en parallèle les cotations de plusieurs DEX (Uniswap V3, QuickSwap V3, SushiSwap V2) et sélectionne dynamiquement l'échange offrant le meilleur rendement net après déduction des frais de gaz estimés.

**3. Puis‑je utiliser DeFiPilot sans interface graphique ?**  
Oui, le bot fonctionne en ligne de commande de façon optimale avec `run_defipilot_v6.py`.

**4. Quels réseaux sont supportés ?**  
Polygon est supporté en natif avec gestion des spécificités Bor PoA. D’autres blockchains seront ajoutées progressivement.

**5. Les clés privées sont‑elles stockées en clair ?**  
Elles sont chargées via `.env` et jamais écrites dans les journaux.

**6. Quelle est la fréquence d’analyse ?**  
Elle dépend de la configuration, généralement quelques secondes.

**7. Comment fonctionne la reprise automatique ?**  
L’état est stocké dans le dossier `data/` (`state.json` et `health.json`), permettant au bot de reprendre après une coupure.

**8. Comment fonctionne la supervision IA ?**  
ControlPilot fournit des signaux contextuels (favorable, neutre, défavorable) influençant la stratégie.

**9. Les données de marché proviennent d’où ?**  
Principalement de DefiLlama, des Quoters on-chain des DEX et des RPC blockchain.

**10. Puis‑je ajouter mes propres stratégies ?**  
Oui, l’architecture modulaire permet d’étendre facilement les stratégies via le dossier `config/`.

**11. Le projet est‑il open source ?**  
Oui, sous licence CC‑BY‑NC‑SA 4.0.

---

# 13. 👤 À propos de l’auteur / About the Author

## 📘 Fr

**David Raffeil** est un passionné d’automatisation, de finance décentralisée et d’ingénierie logicielle appliquée.  
Il développe DeFiPilot depuis 2023 avec l’objectif de construire un écosystème complet et pédagogique autour de la DeFi, accessible aux utilisateurs motivés mais non spécialistes du développement.

Issu d’un parcours autodidacte, il a progressivement acquis des compétences en :
- architecture logicielle (Python 3.11, modules multi-couches)
- analyse on-chain et extraction de signaux DeFi
- routage multi-DEX et optimisation d'exécution Web3
- automatisation, gestion d’état et reprise après coupure
- intégration Web3 et interactions blockchain sécurisées
- conception d’interfaces graphiques (Tkinter)
- structuration de journaux avancés (CSV/JSONL)
- méthodologie Git (branches, versions, tags, releases)

Son approche se caractérise par :
- un souci permanent de **fiabilité**
- une obsession de la **transparence**
- une volonté d’apprendre en construisant
- un usage pragmatique de l’IA (**Antigravity avec Gemini** et **ChatGPT**) comme copilotes de développement

DeFiPilot est conçu comme un projet de long terme :  
une plateforme modulaire, extensible, méthodologiquement propre, pouvant évoluer vers un ensemble multi-modules coordonnés (DeFiPilot, ControlPilot, LabPilot).

David souhaite également partager son expérience pour inspirer d’autres autodidactes à se lancer dans des projets techniques ambitieux, même en partant de zéro.

---

## 📗 En

**David Raffeil** is an enthusiast of automation, decentralized finance and applied software engineering.  
He has been developing DeFiPilot since 2023 with the goal of building a complete and educational DeFi ecosystem, accessible to motivated users—even those without a technical background.

Coming from a fully self-taught path, he progressively developed skills in:
- software architecture (Python 3.11, multi-layer modules)
- on-chain analysis and DeFi signal extraction
- multi-DEX routing and Web3 execution optimization
- automation, state management and crash-safe recovery
- Web3 integration and secure blockchain interactions
- graphical interface design (Tkinter)
- advanced logging systems (CSV/JSONL)
- Git methodology (branches, versions, tags, releases)

His approach is guided by:
- a constant focus on **reliability**
- strong commitment to **transparency**
- learning by building real projects
- pragmatic use of AI (**Antigravity with Gemini** and **ChatGPT**) as development copilots

DeFiPilot is intended as a long-term project:  
a modular, scalable platform that will evolve into a coordinated multi-module setup (DeFiPilot, ControlPilot, LabPilot).

David also hopes to share his journey to inspire other self-taught developers to tackle ambitious technical projects, even starting from scratch.

---

# 14. 🧩 Crédits techniques / Technical Credits

## FR
- Développement assisté par **Antigravity & Gemini** et **ChatGPT**.  
- Icônes, badges et éléments visuels issus de ressources libres.  
- Utilisation de **Web3.py**, **Tkinter**, **Pandas**, **DefiLlama API**.

## EN
- Development assisted by **Antigravity & Gemini** and **ChatGPT**.  
- Icons, badges and visuals use open free resources.  
- Built on **Web3.py**, **Tkinter**, **Pandas**, **DefiLlama API**.

---

# 15. 📜 Licence / License

## 📘 Fr — Licence d’utilisation

DeFiPilot est distribué sous une **licence d’utilisation personnelle et non commerciale**, sauf accord formel avec l’auteur.

Vous êtes autorisé à :
- utiliser le logiciel pour un usage **strictement personnel** ;
- modifier le code pour vos propres besoins ;
- étudier et analyser le fonctionnement du projet ;
- exécuter le logiciel en mode simulation ou réel sous votre propre responsabilité.

Vous n’êtes pas autorisé à :
- utiliser le logiciel dans un cadre **commercial**, professionnel ou lucratif **sans un contrat écrit signé avec l’auteur (David Raffeil)** ;
- vendre, louer, héberger ou distribuer une version modifiée ou non modifiée à des fins commerciales ;
- intégrer tout ou partie du projet dans un produit ou service commercial sans accord contractuel.

Toute redistribution non commerciale doit :
- créditer clairement l’auteur original (**David Raffeil**) ;
- inclure un lien vers le dépôt GitHub d’origine ;
- mentionner les éventuelles modifications.

### 🛡️ Clause de non-responsabilité

Le logiciel est fourni **“tel quel”, sans garantie** d’exactitude, de performance ou de sécurité.  
L’auteur ne peut être tenu responsable :
- de pertes financières directes ou indirectes ;
- d’une mauvaise configuration ou d'un usage inadapté ;
- d’erreurs liées à la blockchain ou à des RPC tiers ;
- de comportements inattendus dus à des smart contracts externes ;
- d’une utilisation non conforme aux recommandations.

L’utilisateur reconnaît utiliser DeFiPilot **à ses propres risques**, en comprenant les risques inhérents à la DeFi et aux interactions on-chain.

---

## 📗 En — Usage License

DeFiPilot is distributed under a **personal and non-commercial use license**, unless a formal agreement is signed with the author.

You are allowed to:
- use the software for **personal use only**;
- modify the code for your own needs;
- study and analyze the project;
- run the software in simulation or real mode at your own risk.

You are not allowed to:
- use the software in any **commercial, professional, or profit-oriented context without a written contract signed with the author (David Raffeil)**;
- sell, rent, host, or distribute modified or unmodified versions for commercial purposes;
- integrate any part of the project into a commercial product or service without contractual approval.

Any non-commercial redistribution must:
- clearly credit the original author (**David Raffeil**) ;
- include a link to the original GitHub repository ;
- state any modifications made.

### 🛡️ Disclaimer

This software is provided **“as is”, without any warranty** of accuracy, performance, or safety.  
The author cannot be held responsible for:
- direct or indirect financial losses ;
- misconfiguration or improper usage ;
- blockchain or third-party RPC failures ;
- unexpected behavior due to external smart contracts ;
- any use that does not follow the recommendations.

The user acknowledges that they use DeFiPilot **at their own risk**, understanding the inherent risks of DeFi and on-chain operations.

---

# 16. 🔍 Dernière révision / Last Review

**README V6.5.0 — mis à jour et consolidé.**  
**README V6.5.0 — updated and consolidated.**

---

© 2023-2026 DeFiPilot — Tous droits réservés.  
Projet distribué sous licence CC-BY-NC-SA 4.0.  
© 2023-2026 DeFiPilot — All rights reserved.  
Project distributed under the CC-BY-NC-SA 4.0 license.
