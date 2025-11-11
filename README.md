![DeFiPilot banner](assets/defipilot_banner.png)

> 🗣️ **Langue / Language :** le bot fonctionne uniquement en **français** pour le moment.  
> The bot currently works **in French only** for the moment.

![Version](https://img.shields.io/badge/Version-V4.8%20Stable-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Made in France](https://img.shields.io/badge/Made%20in-France-lightgrey)
![Developed with ChatGPT](https://img.shields.io/badge/Developed%20with-ChatGPT-orange)
![Open Source](https://img.shields.io/badge/Open%20Source-Non%20Commercial-green)
![Polygon Network](https://img.shields.io/badge/Network-Polygon-purple)

---

## 📚 Sommaire / Table of Contents

1. [Introduction / Introduction](#-introduction--introduction)  
2. [Fonctionnalités principales / Key Features](#-fonctionnalités-principales--key-features)  
3. [Nouveautés / What's New — Version 4.8](#-nouveautés--whats-new--version-48)  
4. [Historique des versions / Past Versions](#-historique-des-versions--past-versions)  
5. [Caractéristiques techniques / Technical Highlights](#-caractéristiques-techniques--technical-highlights)  
6. [Prérequis / Requirements](#-prérequis--requirements)  
7. [Installation / Installation](#-installation--installation)  
8. [Utilisation / Usage](#-utilisation--usage)  
9. [Feuille de route / Roadmap](#-feuille-de-route--roadmap)  
10. [Vision du projet / Project Vision](#-vision-du-projet--project-vision)  
11. [FAQ / Foire aux questions](#-faq--foire-aux-questions)  
12. [Licence / License](#-licence--license)

---

## 🧭 Introduction / Introduction

**FR :**  
DeFiPilot est un bot DeFi autonome conçu pour analyser, sélectionner et gérer automatiquement les pools de liquidité les plus rentables sur différents DEX.  
Le projet vise à démontrer qu’un investisseur individuel peut construire un outil avancé de pilotage DeFi, sans formation technique, grâce à l’assistance de l’IA.

**EN :**  
DeFiPilot is an autonomous DeFi bot designed to analyze, select, and automatically manage the most profitable liquidity pools across multiple DEXs.  
The project demonstrates that an individual investor can build a sophisticated DeFi management tool with AI assistance, without a technical background.

---

## ⚙️ Fonctionnalités principales / Key Features

**FR :**  
DeFiPilot automatise l'analyse et la gestion des investissements DeFi via :  
- Un **moteur de stratégie** qui calcule un score pondéré par pool (APR, TVL, volume, volatilité, tendance APR, slippage prévu, etc.).  
- Des **profils d’investissement** (Prudent, Modéré, Risqué) qui ajustent les seuils, pondérations et limites d’exposition.  
- Un **mode réel** capable d’exécuter : swaps, ajout de liquidité, retrait, staking / unstaking, récolte des rewards (SushiSwap V2 + MiniChef sur Polygon).  
- Une **interface graphique Tkinter** affichant en temps réel le contexte de marché, la stratégie active, les pools analysées et les journaux.  
- Une **journalisation exhaustive** en CSV et JSONL de tous les événements (signaux, stratégies, transactions, erreurs, métriques système).  
- Une **gestion d’état persistante** via un fichier `.state` : chargement au démarrage, sauvegarde automatique, écriture atomique crash-safe et CLI dédiée (`state_cli.py`).  

**EN :**  
DeFiPilot automates DeFi investment analysis and management through:  
- A **strategy engine** computing a weighted score per pool (APR, TVL, volume, volatility, APR trend, expected slippage, etc.).  
- **Investment profiles** (Conservative, Moderate, Aggressive) that adjust thresholds, weights, and exposure limits.  
- A **real mode** able to perform swaps, add/remove liquidity, stake/unstake LP tokens, and harvest rewards (SushiSwap V2 + MiniChef on Polygon).  
- A **Tkinter GUI** that displays market context, active strategy, analyzed pools, and logs in real time.  
- **Extensive logging** to CSV and JSONL for all events (signals, strategies, transactions, errors, system metrics).  
- **Persistent state management** through a `.state` file: load on startup, automatic saving, crash-safe atomic writes and a dedicated CLI (`state_cli.py`).  

---

## 🆕 Nouveautés / What's New — Version 4.8

**FR :**  
La version **4.8** renforce la stabilité du mode réel et introduit la première phase de **supervision** avec des **signaux de risque simples**.  
Elle prépare également l’arrivée de ControlPilot, futur module d’analyse et de supervision IA.  

Principales évolutions :  
- Nouveau module `control/signaux_risque.py` : détection d’anomalies APR/TVL et cohérence des données.  
- Intégration des signaux de risque dans `journal_signaux.jsonl`.  
- Amélioration de la GUI (filtres dynamiques, tri historique, affichage plein écran).  
- Optimisation des threads de sauvegarde d’état et stabilité accrue après redémarrage.  
- Correction de latences d’affichage et de blocages mineurs sous Windows.

**EN :**  
Version **4.8** improves full real-mode stability and introduces the first **supervision phase** with **basic risk signals**.  
It also prepares for ControlPilot, the upcoming AI supervision module.  

Main improvements:  
- New `control/signaux_risque.py` module detecting APR/TVL anomalies and data inconsistencies.  
- Risk signal integration in `journal_signaux.jsonl`.  
- GUI improvements (dynamic filters, history sorting, fullscreen display).  
- Optimized state-save threads and increased restart stability.  
- Fixed display latency and minor freezes on Windows.
---

## 🕰️ Historique des versions / Past Versions

**FR :**  
DeFiPilot a évolué d'un simple simulateur de rendement à un bot opérationnel complet connecté à Polygon.  
Chaque version a renforcé la robustesse, la clarté des journaux et la sécurité :  

- **V4.8** — Signaux de risque, supervision de base, optimisation GUI, stabilité renforcée.  
- **V4.7** — Gestion d’état persistante, écriture crash-safe, CLI `state_cli.py`.  
- **V4.6** — Moteur de répartition intra-catégorie, deltas par pool pondérés par les scores, cas extrêmes bornés.  
- **V4.5** — Intégration initiale de ControlPilot (métriques unifiées, supervision dans la GUI).  
- **V4.4** — Socle de supervision et lancement global (ControlPilot observateur minimal).  
- **V4.3** — Interface graphique complète, suivi des contextes et des pools en temps réel.  
- **V4.2** — Moteur de stratégie optimisé, signaux enrichis et compatibilité GUI.  
- **V4.1** — Interface graphique minimale (barre de statut, cartes principales).  
- **V4.0** — Stratégie de marché et allocation dynamique.  
- **V3.9** — Farming LP réel via MiniChef SushiSwap (Polygon).  
- **V3.8** — Ajout de liquidité réel (SushiSwap V2).  
- **V3.7** — Swap réel avec gestion du slippage et journaux détaillés.  
- **V3.6** — Connexion multi-wallet réelle (Polygon).  
- **V1.x → V2.x** — Simulation complète, scoring et intégration DefiLlama.  

**EN :**  
DeFiPilot has evolved from a basic yield simulator into a full operational bot connected to Polygon.  
Each version improved robustness, log clarity, and security:  

- **V4.8** — Risk signals, basic supervision, GUI optimization, improved stability.  
- **V4.7** — Persistent state, crash-safe writes, `state_cli.py` CLI.  
- **V4.6** — Intra-category allocation engine, per-pool deltas weighted by scores, capped edge cases.  
- **V4.5** — Initial ControlPilot integration (unified metrics, GUI supervision).  
- **V4.4** — Supervision foundation and global launcher (ControlPilot minimal observer).  
- **V4.3** — Full GUI with real-time contexts and pool monitoring.  
- **V4.2** — Optimized strategy engine, enriched signals, and GUI compatibility.  
- **V4.1** — Minimal GUI (status bar, main cards).  
- **V4.0** — Market strategy and dynamic allocation.  
- **V3.9** — Real LP farming via SushiSwap MiniChef (Polygon).  
- **V3.8** — Real add-liquidity on SushiSwap V2.  
- **V3.7** — Real swaps with slippage control and detailed logs.  
- **V3.6** — Real multi-wallet connection (Polygon).  
- **V1.x → V2.x** — Full simulation, scoring, and DefiLlama integration.  

---

## 🛠️ Caractéristiques techniques / Technical Highlights

**FR :**  
- Langage : **Python 3.11+**  
- Interface : **Tkinter** (GUI locale, compatible Windows / Linux / SBC type Orange Pi).  
- Réseau principal : **Polygon PoS** (RPC externe type Infura / Alchemy).  
- DEX supporté (mode réel actuel) : **SushiSwap V2 + MiniChef**.  
- Journaux : fichiers **CSV** (transactions, farming, liquidité) et **JSONL** (signaux, stratégie, supervision).  
- Gestion d’état : fichier **`defipilot.state`** avec chargement au démarrage, sauvegarde automatique, écriture atomique et CLI (`state_cli.py`).  
- Architecture : modules séparés (`core/`, `gui/`, `defi_sources/`, `strategy/`, `control/`, etc.) pour faciliter l’évolution du projet.  

**EN :**  
- Language: **Python 3.11+**  
- Interface: **Tkinter** (local GUI, Windows / Linux / SBC such as Orange Pi).  
- Main network: **Polygon PoS** (external RPC such as Infura / Alchemy).  
- Supported DEX (current real mode): **SushiSwap V2 + MiniChef**.  
- Logging: **CSV** files (transactions, farming, liquidity) and **JSONL** files (signals, strategy, supervision).  
- State management: **`defipilot.state`** file with startup loading, automatic saving, atomic writes and CLI (`state_cli.py`).  
- Architecture: separated modules (`core/`, `gui/`, `defi_sources/`, `strategy/`, `control/`, etc.) to make the project easier to extend.  

---

## 💻 Prérequis / Requirements

**FR :**  
- Python **3.11+** installé.  
- Accès à un **RPC Polygon** (Infura, Alchemy, ou équivalent).  
- Un wallet compatible (par exemple Rabby, Metamask) avec quelques MATIC/POL pour les frais de gas.  
- Environnement recommandé : PC ou **Single Board Computer** (Orange Pi, Raspberry Pi) dédié.  

**EN :**  
- Python **3.11+** installed.  
- Access to a **Polygon RPC** endpoint (Infura, Alchemy, or similar).  
- A compatible wallet (e.g. Rabby, Metamask) with some MATIC/POL for gas fees.  
- Recommended environment: a PC or dedicated **Single Board Computer** (Orange Pi, Raspberry Pi).  

---

## 🧩 Installation / Installation

**FR :**  
1. Cloner le dépôt : `git clone https://github.com/DavidRaffeil/DeFiPilot.git`  
   puis `cd DeFiPilot`  
2. Créer un environnement virtuel (recommandé) : `python -m venv venv`  
   puis activer : `source venv/bin/activate` (Linux/macOS) ou `venv\Scripts\activate` (Windows).  
3. Installer les dépendances : `pip install -r requirements.txt`  
4. Configurer les variables d’environnement : créer un fichier `.env` à la racine (voir `.env.example`).  
   Renseigner le **RPC Polygon** (Infura, Alchemy, etc.) et la **clé privée locale**.  
5. Tester le lancement du bot : `python main.py --dryrun`  

**EN :**  
1. Clone the repository: `git clone https://github.com/DavidRaffeil/DeFiPilot.git`  
   then `cd DeFiPilot`  
2. Create a virtual environment (recommended): `python -m venv venv`  
   then activate it: `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows).  
3. Install dependencies: `pip install -r requirements.txt`  
4. Configure environment variables: create a `.env` file at the root (see `.env.example`).  
   Fill in your **Polygon RPC** and **local private key**.  
5. Test bot startup: `python main.py --dryrun`  
---

## ▶️ Utilisation / Usage

**FR :**

### 🧩 Mode journal + GUI

1. Lancer le journaliseur continu (signaux de marché) :  
   `python journal_daemon.py --pools data/pools_sample.json --interval 30 --journal journal_signaux.jsonl`  
2. Ouvrir l’interface graphique dans un second terminal :  
   `python gui/main_window.py`  
3. Dans la GUI :  
   - Sélectionner le fichier `journal_signaux.jsonl` si nécessaire.  
   - Observer les mises à jour en temps réel (scores, signaux, stratégie active).  

### 💼 Mode réel

1. Activer le mode réel dans la configuration.  
2. Exécuter les commandes CLI correspondantes (swap, add-liquidity, farming).  
3. Toujours vérifier les montants et adresses avant validation.  

⚠️ **Attention :** toute transaction en mode réel est signée avec la clé privée locale.  
Aucune donnée sensible n’est transmise en ligne.  

**EN :**

### 🧩 Journal + GUI mode

1. Start the continuous journal (market signals):  
   `python journal_daemon.py --pools data/pools_sample.json --interval 30 --journal journal_signaux.jsonl`  
2. Open the GUI in a second terminal:  
   `python gui/main_window.py`  
3. In the GUI:  
   - Select `journal_signaux.jsonl` if needed.  
   - Observe real-time updates (scores, signals, active strategy).  

### 💼 Real mode

1. Enable real mode in the configuration.  
2. Run the related CLI commands (swap, add-liquidity, farming).  
3. Always double-check amounts and addresses before confirming.  

⚠️ **Warning:** every real transaction is signed with your local private key.  
No sensitive data is ever sent online.  

---

## 🗺️ Feuille de route / Roadmap

**FR :**

- **V4.8 – V4.9** — Supervision et signaux de risque (phase 1 ControlPilot).  
- **V5.x — ControlPilot** : agent central de supervision, agrégation multi-bots, premières briques IA.  
- **V6.x — ArbiPilot** : bot d’arbitrage inter-DEX / inter-chaînes, basé sur l’infrastructure de DeFiPilot.  
- **V7.x — LabPilot** : expérimentations IA et optimisation des stratégies.

**EN :**

- **V4.8 – V4.9** — Supervision and risk signals (ControlPilot phase 1).  
- **V5.x — ControlPilot**: central supervision agent, multi-bot aggregation, first AI features.  
- **V6.x — ArbiPilot**: inter-DEX / cross-chain arbitrage bot built on DeFiPilot’s infrastructure.  
- **V7.x — LabPilot**: AI experimentation and strategy optimization.

---

## 🌌 Vision du projet / Project Vision

**FR :**

DeFiPilot n’est pas seulement un bot DeFi, c’est un **laboratoire public** montrant qu’un autodidacte, accompagné par l’IA,  
peut construire pas à pas un écosystème complet :  

- Un bot principal (**DeFiPilot**) qui gère des investissements réels de manière transparente.  
- Un centre de contrôle (**ControlPilot**) qui observe, agrège et analyse.  
- Des modules spécialisés (**ArbiPilot**, **LabPilot**, etc.) qui viendront explorer d’autres stratégies.  

L’objectif est autant pédagogique que pratique : documenter chaque étape pour inspirer d’autres personnes à construire leurs propres outils.

**EN :**

DeFiPilot is not only a DeFi bot — it is a **public lab** proving that a self-taught user, assisted by AI,  
can progressively build a complete ecosystem:  

- A main bot (**DeFiPilot**) managing real investments with transparency.  
- A control center (**ControlPilot**) that observes, aggregates, and analyzes.  
- Specialized modules (**ArbiPilot**, **LabPilot**, etc.) to explore additional strategies.  

The goal is both educational and practical: to document every step and inspire others to build their own tools.  
