![DeFiPilot banner](assets/defipilot_banner.png)

> 🗣️ **Langue / Language :** le bot fonctionne uniquement en **français** pour le moment.  
> The bot currently works **in French only** for the moment.

![Version](https://img.shields.io/badge/Version-V5.5%20Stable-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Made in France](https://img.shields.io/badge/Made%20in-France-lightgrey)
![Developed with ChatGPT](https://img.shields.io/badge/Developed%20with-ChatGPT-orange)
![Open Source](https://img.shields.io/badge/License-CC--BY--NC--SA%204.0-green)
![Polygon Network](https://img.shields.io/badge/Network-Polygon-purple)

---

## 📚 Sommaire / Table of Contents
1. [Introduction / Introduction](#1-introduction--introduction)  
2. [Fonctionnalités principales / Key Features](#2-fonctionnalites-principales--key-features)  
3. [Aperçu visuel / Visual Overview](#3-apercu-visuel--visual-overview)  
4. [Nouveautés / What's New — Version 5.5](#4-nouveautes--whats-new--version-55)  
5. [Historique des versions / Past Versions](#5-historique-des-versions--past-versions)  
6. [Caractéristiques techniques / Technical Highlights](#6-caracteristiques-techniques--technical-highlights)  
7. [Prérequis / Requirements](#7-prerequis--requirements)  
8. [Installation / Installation](#8-installation--installation)  
9. [Utilisation / Usage](#9-utilisation--usage)  
10. [Feuille de route / Roadmap](#10-feuille-de-route--roadmap)  
11. [Vision du projet / Project Vision](#11-vision-du-projet)  
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
- **Robustesse** : tolérance aux erreurs réseau, redondances, vérifications multiples.  
- **Modularité** : possibilité d’étendre facilement les fonctionnalités via modules.  
- **Transparence** : journalisation complète (CSV + JSONL), état sauvegardé, historique visible.  
- **Automatisation** : analyse continue, décisions guidées par les profils, reprise automatique.

DeFiPilot vise à constituer une base sérieuse et pérenne pour gérer des investissements DeFi automatisés, tout en intégrant des mécanismes de sécurité pour réduire les risques opérationnels.

## EN
DeFiPilot is an autonomous DeFi bot designed to continuously analyze opportunities across decentralized exchanges (DEX), compute real profitability for liquidity pools, and select the best options according to a configurable investment profile. The system runs in both simulation and real execution modes depending on user configuration.

Its architecture relies on four core principles:  
- **Robustness**: tolerance to network failures, redundancy, multiple safety checks.  
- **Modularity**: easily extendable through additional modules.  
- **Transparency**: full logging (CSV + JSONL), state storage, visible history.  
- **Automation**: continuous analysis, profile‑driven decisions, automatic state recovery.

DeFiPilot aims to be a serious and sustainable foundation for automated DeFi investment management while embedding safety mechanisms to minimize operational risks.

---

# 2. ⚙️ Fonctionnalités principales / Key Features

## FR
- Analyse automatique des pools (APR, TVL, volume, volatilité, slippage).  
- Scoring pondéré basé sur plusieurs profils (Prudent, Modéré, Risque).  
- Mode simulation complet pour tests sécurisés.  
- Mode réel avec gestion du slippage, limites, confirmations.  
- Interface graphique Tkinter avec rafraîchissement automatique.  
- Multi-wallets avec séparation des usages.  
- Supervision IA via ControlPilot (signaux contextuels).  
- Reprise automatique après coupure (fichier `.state`).  
- Journalisation détaillée (JSONL + CSV).  
- Architecture modulaire extensible.

## EN
- Automatic pool analysis (APR, TVL, volume, volatility, slippage).  
- Weighted scoring based on multiple profiles (Conservative, Moderate, Risk).  
- Full simulation mode for safe testing.  
- Real mode with slippage management, limits, confirmations.  
- Tkinter GUI with automatic refresh.  
- Multi‑wallet support.  
- AI supervision via ControlPilot (context signals).  
- Automatic resume after shutdown (`.state`).  
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

# 4. 🆕 Nouveautés / What's New — Version 5.5

## 📘 Fr
- Introduction des **exits automatiques** basés sur le contexte du marché.  
- Application des seuils et comportements issus de **Deep Search V5.4** (gestion des phases critiques, neutres et favorables).  
- Ajout et utilisation du fichier stratégique finalisé : `strategy_v5_5.json`.  
- Stabilisation complète du daemon (pipeline : signaux → scoring → stratégie → exits).  
- Amélioration de la cohérence stratégique en conditions réelles et simulées.  
- Préparation de la **V5.6** (optimisations du moteur + fondations ArbiPilot).

---

## 📗 En
- Introduction of **automatic exits** based on market context.  
- Integration of thresholds and crisis-behavior rules derived from **Deep Search V5.4**.  
- Addition and use of the finalized strategy file: `strategy_v5_5.json`.  
- Full stabilization of the daemon (pipeline: signals → scoring → strategy → exits).  
- Improved strategic consistency in both real and simulated conditions.  
- Preparation for **V5.6** (engine optimizations + ArbiPilot foundations).

---

# 5. 🕓 Historique des versions / Past Versions

## 📘 Fr
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
- **V4.4 :** Lancement global + supervision initiale.  
- **V4.3 :** Simulation LP + journalisation complète.  
- **V4.2 :** Scoring pondéré + gestion des profils.  
- **V4.0 :** Passage au simulateur complet.

---

## 📗 En
- **V5.5:** Automatic exits based on market context, integration of Deep Search V5.4 thresholds, finalized strategy file (`strategy_v5_5.json`), full daemon stabilization.  
- **V5.3:** Dedicated strategic journal (`journal_strategy.jsonl`), full integration of normalized ControlPilot signals, daemon stabilization.  
- **V5.2:** Automatic portfolio rebalancing, weighted signals, rebalancing snapshots, updated scoring/strategy.  
- **V5.1:** New AI signal engine, advanced normalization, dynamic scoring, enriched strategy.  
- **V5.0:** ControlPilot AI integration, improved stability, optimized dashboard.  
- **V4.9:** Advanced signal aggregation + anomaly detection.  
- **V4.8:** Simple signal collection (start of ControlPilot).  
- **V4.7:** Full real-mode stabilization + auto-resume.  
- **V4.6:** Dynamic strategy with automatic adjustments.  
- **V4.5:** GUI improvements + contextual display.  
- **V4.4:** Global launch + initial supervision.  
- **V4.3:** LP simulation + detailed logging.  
- **V4.2:** Weighted scoring + profile management.  
- **V4.0:** Full simulation mode.

---

# 6. 🧱 Caractéristiques techniques / Technical Highlights

## FR
DeFiPilot repose sur une architecture modulaire, pensée pour garantir évolutivité et stabilité :

- **`core/`** — Analyse, scoring, stratégie, transactions, gestion des wallets, rééquilibrage (`rebalancing_simulator.py`).  
- **`gui/`** — Interface Tkinter (rafraîchissement, affichage, widgets personnalisés).  
- **`cli/`** — Exécution en mode console, outils rapides, smoke tests.  
- **`control/`** — Module IA ControlPilot (signaux + agrégation).  
- **`config/`** — Paramètres généraux, profils, fichiers JSON de configuration.  
- **`journal/`** — Système de logs (CSV + JSONL), rotation, journaux par modules, snapshots du rééquilibrage (`rebalancing_snapshot.jsonl`).  
- **`state/`** — Gestion du fichier `.state` (reprise automatique).  

Le bot utilise principalement **Python 3.11**, **Web3.py**, **Tkinter**, **Pandas**, et l’API **DefiLlama**.

## EN
DeFiPilot is built on a modular architecture designed for scalability and stability:

- **`core/`** — Analysis, scoring, strategy, transactions, wallet management, rebalancing (`rebalancing_simulator.py`).  
- **`gui/`** — Tkinter interface (refresh engine, display, custom widgets).  
- **`cli/`** — Console execution, quick tools, smoke tests.  
- **`control/`** — ControlPilot AI module (signals + aggregation).  
- **`config/`** — Global settings, profiles, JSON configuration files.  
- **`journal/`** — Log system (CSV + JSONL), rotation, per-module logs, rebalancing snapshots (`rebalancing_snapshot.jsonl`).  
- **`state/`** — `.state` file management (auto-resume).  

The bot relies mainly on **Python 3.11**, **Web3.py**, **Tkinter**, **Pandas**, and the **DefiLlama** API.

---

# 7. 🔧 Prérequis / Requirements

## FR
- Python **3.11+**  
- Accès RPC Polygon (Infura, Alchemy, QuickNode)  
- Wallet compatible (Rabby, MetaMask)  
- Connexion Internet stable  
- Git installé

## EN
- Python **3.11+**  
- Polygon RPC access (Infura, Alchemy, QuickNode)  
- Compatible wallet (Rabby, MetaMask)  
- Stable Internet connection  
- Git installed

---

# 8. ⚙️ Installation / Installation

## FR
1. **Cloner le dépôt :**
```bash
git clone https://github.com/DavidRaffeil/DeFiPilot.git
cd DeFiPilot
```
2. **Créer l’environnement virtuel et installer les dépendances :**
```bash
python3.11 -m venv .venv
source .venv/bin/activate  # Windows : .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```
3. **Configurer le fichier `.env` :**
```dotenv
NETWORK=polygon
RPC_URL=https://polygon-mainnet.infura.io/v3/<PROJECT_ID>
WALLEΤ_ADDRESS=<VOTRE_ADRESSE_WALLET> # remplacer par votre adresse
LOG_LEVEL=INFO

```
4. **Vérifier l’installation :**
```bash
python check_setup.py
```

## EN
1. **Clone the repository:**
```bash
git clone https://github.com/DavidRaffeil/DeFiPilot.git
cd DeFiPilot
```
2. **Create a virtual environment and install dependencies:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```
3. **Configure the `.env` file:**
```dotenv
NETWORK=polygon
RPC_URL=https://polygon-mainnet.infura.io/v3/<PROJECT_ID>
WALLEΤ_ADDRESS=<YOUR_WALLET_ADDRESS> # replace with your address
LOG_LEVEL=INFO

```
4. **Verify installation:**
```bash
python check_setup.py
```
---

# 9. ▶️ Utilisation / Usage

## FR
- **Interface graphique :**
```bash
python start_defipilot.py
```
- **Mode console (headless) :**
```bash
python run_defipilot.py
```
Les journaux sont enregistrés dans `journal_*.jsonl` et `journal_*.csv`.

## EN
- **Graphical interface:**
```bash
python start_defipilot.py
```
- **Headless mode:**
```bash
python run_defipilot.py
```
Logs are saved in `journal_*.jsonl` and `journal_*.csv`.

---

# 10. 🚀 Feuille de route / Roadmap

## 📘 Fr

### Prochaines versions
- **V5.6 :** Optimisations du moteur stratégique, améliorations internes et fondations techniques pour ArbiPilot.  
- **V6.0 :** Mode réel complet entièrement autonome (analyse → stratégie → transactions → sécurité).  
- **V6.1 :** Synchronisation multi-bots (DeFiPilot + ControlPilot + ArbiPilot).  
- **V6.2 :** Déploiement sur Orange Pi / infrastructure SBC.  

### Versions finalisées
- **V5.5 :** Exits automatiques, intégration des seuils Deep Search, stratégie finalisée `strategy_v5_5.json`, stabilisation du daemon.  
- **V5.3 :** Journal stratégique dédié (`journal_strategy.jsonl`), intégration complète des signaux ControlPilot.  
- **V5.2 :** Rééquilibrage automatique, signaux pondérés, snapshots et pipeline stabilisé.  
- **V5.1 :** Nouveau moteur de signaux IA, scoring dynamique et stratégie enrichie.  
- **V5.0 :** Intégration ControlPilot + stabilisation mode réel.

---

## 📗 En

### Upcoming Versions
- **V5.6:** Engine optimizations, internal improvements, and technical foundations for ArbiPilot.  
- **V6.0:** Fully autonomous real-mode engine (analysis → strategy → transactions → safety).  
- **V6.1:** Multi-bot synchronization (DeFiPilot + ControlPilot + ArbiPilot).  
- **V6.2:** Deployment on Orange Pi / SBC architecture.  

### Completed Versions
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
- Modules complémentaires (ControlPilot, ArbiPilot, LabPilot).  
- Architecture transparente et robuste centrée sur la sécurité et la pédagogie.

## EN
DeFiPilot aims to evolve into a complete automated management platform including:  
- Multi‑DEX, multi‑chain analysis.  
- Dynamic strategies adjusted to market conditions.  
- Complementary modules (ControlPilot, ArbiPilot, LabPilot).  
- Transparent and robust architecture focused on safety and clarity.

---

# 12. ❓ FAQ / Foire aux questions

## FR
**1. DeFiPilot effectue‑t‑il des transactions automatiquement ?**  
Oui, si le mode réel est activé et correctement configuré. En mode simulation, aucune transaction blockchain n’est envoyée.

**2. Puis‑je utiliser DeFiPilot sans interface graphique ?**  
Oui, le bot peut fonctionner en mode console (headless) via `run_defipilot.py`.

**3. Quels réseaux sont supportés ?**  
Polygon est supporté en natif. D’autres blockchains seront ajoutées progressivement.

**4. Les clés privées sont‑elles stockées en clair ?**  
Elles sont chargées via `.env` et jamais écrites dans les journaux.

**5. Quelle est la fréquence d’analyse ?**  
Elle dépend de la configuration, généralement quelques secondes.

**6. Comment fonctionne la reprise automatique ?**  
L’état est stocké dans un fichier `.state`, permettant au bot de reprendre après une coupure.

**7. Comment fonctionne la supervision IA ?**  
ControlPilot fournit des signaux contextuels (favorable, neutre, défavorable) influençant la stratégie.

**8. Les données de marché proviennent d’où ?**  
Principalement de DefiLlama et des RPC blockchain.

**9. Puis‑je ajouter mes propres stratégies ?**  
Oui, l’architecture modulaire permet d’étendre facilement les stratégies.

**10. Le projet est‑il open source ?**  
Oui, sous licence CC‑BY‑NC‑SA 4.0.

## EN
**1. Does DeFiPilot perform transactions automatically?**  
Yes, if real mode is enabled and properly configured. In simulation mode, no blockchain transactions are sent.

**2. Can I run DeFiPilot without the GUI?**  
Yes, the bot can run headless using `run_defipilot.py`.

**3. Which networks are supported?**  
Polygon is supported natively; other networks will be added later.

**4. Are private keys stored in plain text?**  
They are loaded via `.env` and never written to logs.

**5. What is the analysis frequency?**  
It depends on configuration, usually a few seconds.

**6. How does auto‑resume work?**  
Bot state is stored in a `.state` file, allowing recovery after a shutdown.

**7. How does AI supervision work?**  
ControlPilot provides contextual signals (favorable, neutral, unfavorable) affecting strategy.

**8. Where does market data come from?**  
Mainly from DefiLlama and blockchain RPC endpoints.

**9. Can I add my own strategies?**  
Yes, the modular architecture supports custom strategy modules.

**10. Is the project open source?**  
Yes, licensed under CC‑BY‑NC‑SA 4.0.

---

# 13. 👤 À propos de l’auteur / About the Author

## 📘 Fr

**David Raffeil** est un passionné d’automatisation, de finance décentralisée et d’ingénierie logicielle appliquée.  
Il développe DeFiPilot depuis 2023 avec l’objectif de construire un écosystème complet et pédagogique autour de la DeFi, accessible aux utilisateurs motivés mais non spécialistes du développement.

Issu d’un parcours autodidacte, il a progressivement acquis des compétences en :
- architecture logicielle (Python 3.11, modules multi-couches)
- analyse on-chain et extraction de signaux DeFi
- automatisation, gestion d’état et reprise après coupure
- intégration Web3 et interactions blockchain sécurisées
- conception d’interfaces graphiques (Tkinter)
- structuration de journaux avancés (CSV/JSONL)
- méthodologie Git (branches, versions, tags, releases)

Son approche se caractérise par :
- un souci permanent de **fiabilité**
- une obsession de la **transparence**
- une volonté d’apprendre en construisant
- un usage pragmatique de l’IA (ChatGPT) comme copilote de développement

DeFiPilot est conçu comme un projet de long terme :  
une plateforme modulaire, extensible, méthodologiquement propre, pouvant évoluer vers un cluster multi-bots (DeFiPilot, ControlPilot, ArbiPilot, LabPilot).

David souhaite également partager son expérience pour inspirer d’autres autodidactes à se lancer dans des projets techniques ambitieux, même en partant de zéro.

---

## 📗 En

**David Raffeil** is an enthusiast of automation, decentralized finance and applied software engineering.  
He has been developing DeFiPilot since 2023 with the goal of building a complete and educational DeFi ecosystem, accessible to motivated users—even those without a technical background.

Coming from a fully self-taught path, he progressively developed skills in:
- software architecture (Python 3.11, multi-layer modules)
- on-chain analysis and DeFi signal extraction
- automation, state management and crash-safe recovery
- Web3 integration and secure blockchain interactions
- graphical interface design (Tkinter)
- advanced logging systems (CSV/JSONL)
- Git methodology (branches, versions, tags, releases)

His approach is guided by:
- a constant focus on **reliability**
- strong commitment to **transparency**
- learning by building real projects
- pragmatic use of AI (ChatGPT) as a development copilot

DeFiPilot is intended as a long-term project:  
a modular, scalable platform that will evolve into a multi-bot cluster (DeFiPilot, ControlPilot, ArbiPilot, LabPilot).

David also hopes to share his journey to inspire other self-taught developers to tackle ambitious technical projects, even starting from scratch.

---

# 14. 🧩 Crédits techniques / Technical Credits

## FR
- Développement assisté par **ChatGPT**.  
- Icônes, badges et éléments visuels issus de ressources libres.  
- Utilisation de **Web3.py**, **Tkinter**, **Pandas**, **DefiLlama API**.

## EN
- Development assisted by **ChatGPT**.  
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
- d’une mauvaise configuration ou d’un usage inadapté ;
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

**README V5.5 — mis à jour et consolidé.**  
**README V5.5 — updated and consolidated.**

---

© 2023-2025 DeFiPilot — Tous droits réservés.  
Projet distribué sous licence CC-BY-NC-SA 4.0.  
© 2023-2025 DeFiPilot — All rights reserved.  
Project distributed under the CC-BY-NC-SA 4.0 license.
