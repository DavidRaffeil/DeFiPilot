<p align="center">
  <img src="assets/defipilot_banner.png" alt="DeFiPilot banner" width="100%">
</p>

> 🗣️ **Langue / Language :** le bot fonctionne uniquement en **français** pour le moment.  
> The bot currently works **in French only** for the moment.

![Version](https://img.shields.io/badge/Version-V4.3%20Stable-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Made in France](https://img.shields.io/badge/Made%20in-France-lightgrey)
![Developed with ChatGPT](https://img.shields.io/badge/Developed%20with-ChatGPT-orange)
![Open Source](https://img.shields.io/badge/Open%20Source-Non%20Commercial-green)
![Polygon Network](https://img.shields.io/badge/Network-Polygon-purple)


---

## 📚 Sommaire / Table of Contents

1. [Introduction / Introduction](#-introduction--introduction)  
2. [Fonctionnalités principales / Key Features](#-fonctionnalités-principales--key-features)  
3. [Nouveautés / What's New — Version 4.4](#-nouveautés--whats-new--version-44)  
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
DeFiPilot est un bot DeFi autonome conçu pour analyser, sélectionner et gérer automatiquement les pools de liquidité les plus rentables sur différents DEX. Le projet vise à démontrer qu’un investisseur individuel peut construire un outil avancé de pilotage DeFi, sans formation technique, grâce à l’assistance de l’IA.

**EN :**  
DeFiPilot is an autonomous DeFi bot designed to analyze, select, and automatically manage the most profitable liquidity pools across multiple DEXs. The project demonstrates that an individual investor can build a sophisticated DeFi management tool with AI assistance, without a technical background.

---

## ⚙️ Fonctionnalités principales / Key Features

**FR :**  
DeFiPilot offre un ensemble de fonctionnalités avancées pour automatiser la gestion des investissements en DeFi. Il analyse en continu les principales métriques des pools (APR, TVL, volume, volatilité, tendance APR) et applique un calcul de score pondéré selon le profil d’investissement (Prudent, Modéré ou Risqué). Le bot peut ensuite exécuter automatiquement les opérations nécessaires : swaps, ajouts de liquidité, staking, unstake et récolte des rewards. Toutes les actions sont journalisées dans des fichiers CSV et JSONL, et une interface graphique Tkinter permet de visualiser les performances et les métriques en temps réel. Cette approche assure un contrôle total et prépare l’intégration future avec **ControlPilot**, l’agent IA centralisé de supervision.

**EN :**  
DeFiPilot provides a comprehensive feature set for automating DeFi investment management. It continuously analyzes key pool metrics (APR, TVL, volume, volatility, APR trend) and applies a weighted scoring model based on the user’s investment profile (Conservative, Moderate, or Aggressive). The bot can then automatically perform the necessary operations such as swaps, liquidity additions, staking, unstaking, and reward harvesting. All actions are logged to CSV and JSONL files, while a Tkinter-based GUI displays real-time performance and key metrics. This architecture ensures full control and prepares the upcoming integration with **ControlPilot**, the centralized AI supervision agent.

---

🆕 Nouveautés / What's New — Version 4.4

FR :
La version 4.4 marque une étape majeure dans la stabilité et l’autonomie de DeFiPilot, avec l’ajout d’un socle complet de supervision globale et d’un lanceur unifié.
Le nouveau script start_defipilot.py permet désormais de démarrer simultanément le daemon de journaux, le module d’observation ControlPilot, et l’interface graphique principale.
Cette version introduit également la supervision console en temps réel, affichant directement le contexte global, l’APR moyen et le TVL total sans ouvrir les fichiers de logs.
Le tout s’accompagne d’un arrêt propre des processus via Ctrl + C, garantissant un fonctionnement fluide et contrôlé.
Cette évolution prépare la transition vers la phase 4.5, centrée sur l’enrichissement du tableau de bord et la stratégie en mode réel.

EN :
Version 4.4 represents a major step toward stability and autonomy for DeFiPilot, introducing a complete global supervision framework and a unified launcher.
The new start_defipilot.py script now launches simultaneously the logging daemon, the ControlPilot observer module, and the main graphical interface.
This version also adds real-time console supervision, displaying the global context, average APR, and total TVL directly without opening log files.
It includes clean process termination via Ctrl + C, ensuring smooth and controlled operation.
This release sets the stage for version 4.5, focused on GUI enhancement and real-mode strategic execution.
---

🕰️ Historique des versions / Past Versions
FR :
DeFiPilot a connu une évolution continue à travers plusieurs versions majeures, passant d’un simple simulateur de rendement à un outil pleinement opérationnel capable d’interagir avec la blockchain Polygon.
Chaque itération a apporté de nouvelles briques — de la simulation des pools à la connexion à un wallet réel, jusqu’au farming automatisé via SushiSwap et MiniChef.
Ces étapes successives ont renforcé la stabilité, la transparence des journaux et la sécurité des transactions.
Les principales versions incluent :
V4.3 — interface graphique complète, suivi en temps réel des contextes et affichage dynamique des pools.
V4.2 — moteur de stratégie optimisé, signaux enrichis et compatibilité GUI.
V4.1 — interface graphique minimale (barre de statut, cartes principales).
V4.0 — stratégie de marché et allocation dynamique.
V3.9 — farming LP réel via MiniChef SushiSwap Polygon.
V3.8 — ajout de liquidité réel sur Polygon (SushiSwap V2).
V3.7 — swap réel avec gestion du slippage et logs complets.
V3.6 — connexion multi-wallet réelle (Polygon).
V1.x → V2.x — simulation complète, scoring et intégration DefiLlama.
EN :
DeFiPilot has evolved continuously through several major releases, progressing from a simple yield simulator to a fully operational tool interacting with the Polygon blockchain.
Each iteration introduced new foundations — from pool simulation to real wallet connection, and automated farming through SushiSwap and MiniChef.
These successive updates have strengthened stability, log transparency, and transaction security.
The main versions include:
V4.3 — complete graphical interface, real-time context tracking, and dynamic pool display.
V4.2 — optimized strategy engine, enriched signals, and GUI compatibility.
V4.1 — minimal graphical interface (status bar, main cards).
V4.0 — market strategy and dynamic allocation.
V3.9 — real LP farming through MiniChef SushiSwap Polygon.
V3.8 — real add-liquidity on Polygon (SushiSwap V2).
V3.7 — real swap with slippage management and full logs.
V3.6 — real multi-wallet connection (Polygon).
V1.x → V2.x — full simulation, scoring, and DefiLlama integration.
---

## 🧩 Caractéristiques techniques / Technical Highlights

**FR :**  
Cette section décrit les aspects techniques essentiels de DeFiPilot. Le projet est entièrement développé en **Python 3.11+**, compatible avec la blockchain **Polygon** et les DEX **SushiSwap V2** et **MiniChef** pour le farming. Les principales données DeFi (APR, TVL, volumes) proviennent de **DefiLlama**, assurant une source publique et fiable. Le bot repose sur une architecture modulaire, avec des fichiers de configuration simples (`.env`, `PROFILS.json`, `VISION.md`) et un système de journaux détaillés (CSV et JSONL) pour tracer chaque action. DeFiPilot peut fonctionner sur un ordinateur classique ou sur un **SBC** tel qu’un Orange Pi ou Raspberry Pi, garantissant une exécution légère et continue 24/7.

**EN :**  
This section describes the essential technical aspects of DeFiPilot. The project is fully developed in **Python 3.11+**, compatible with the **Polygon** blockchain and the **SushiSwap V2** and **MiniChef** DEXes for farming operations. Core DeFi data (APR, TVL, volumes) is sourced from **DefiLlama**, providing a reliable public reference. The bot uses a modular architecture with straightforward configuration files (`.env`, `PROFILS.json`, `VISION.md`) and detailed logging (CSV and JSONL) to record every action. DeFiPilot can run on a regular computer or on an **SBC** such as an Orange Pi or Raspberry Pi, ensuring lightweight 24/7 execution.

---

## 💻 Prérequis / Requirements

**FR :**  
Pour exécuter DeFiPilot correctement, il est nécessaire de disposer d’un environnement Python **3.11 ou supérieur** et d’un accès RPC valide au réseau **Polygon** (via Infura, Alchemy ou équivalent). Un wallet compatible, comme **Metamask** ou **Rabby**, est requis pour les tests et les opérations réelles. Le bot peut être installé aussi bien sur un ordinateur de bureau que sur un **SBC** (Orange Pi, Raspberry Pi) pour une exécution continue à faible consommation énergétique. Une connexion Internet stable en Ethernet est recommandée pour garantir la fiabilité des transactions et des journaux.

**EN :**  
To run DeFiPilot properly, you need a Python environment **3.11 or higher** and a valid **Polygon** RPC endpoint (via Infura, Alchemy, or equivalent). A compatible wallet such as **Metamask** or **Rabby** is required for testing and real operations. The bot can be installed either on a desktop computer or on an **SBC** (Orange Pi, Raspberry Pi) for continuous low-power operation. A stable Ethernet Internet connection is recommended to ensure reliable transactions and logging.

---

⚙️ Installation / Installation

FR :
L’installation de DeFiPilot reste simple et rapide.
Elle peut être effectuée sur tout système disposant de Python 3.11+.
Clonez le dépôt GitHub, créez un environnement virtuel, installez les dépendances, puis configurez le fichier .env.
La version 4.4 introduit un script de lancement global (start_defipilot.py) qui démarre automatiquement le daemon, ControlPilot et l’interface graphique.

# 1. Cloner le dépôt
git clone https://github.com/DavidRaffeil/DeFiPilot.git
cd DeFiPilot

# 2. Créer un environnement virtuel (optionnel)
python -m venv .venv
source .venv/bin/activate  # sous Windows : .venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer l'environnement
cp .env.example .env
# Éditer le fichier .env pour y renseigner :
# - Clé RPC Polygon (Infura / Alchemy)
# - Clé privée du wallet
# - Chemins des journaux (facultatif)


EN :
Installing DeFiPilot is quick and straightforward.
It works on any system running Python 3.11+.
Clone the GitHub repository, create a virtual environment, install the dependencies, and set up your .env file.
Version 4.4 introduces a global launcher (start_defipilot.py) that automatically starts the daemon, ControlPilot, and the graphical interface.

# 1. Clone the repository
git clone https://github.com/DavidRaffeil/DeFiPilot.git
cd DeFiPilot

# 2. Create a virtual environment (optional)
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure the environment
cp .env.example .env
# Edit the .env file to include:
# - Polygon RPC key (Infura / Alchemy)
# - Private wallet key
# - Log file paths (optional)

---

🚀 Utilisation / Usage
FR :
La version 4.4 introduit un mode de lancement global simplifié permettant de démarrer automatiquement l’ensemble des composants de DeFiPilot :
le daemon de journaux, le module d’observation ControlPilot, et l’interface graphique principale.
Ce mode permet de visualiser en direct le contexte global, les métriques (APR, TVL) et les signaux de marché via la console et la GUI.
Le mode stratégie reste disponible pour des analyses ciblées, tandis que le mode simulation (dry-run) permet de tester sans transactions réelles.
# 🚀 Lancement complet (daemon + ControlPilot + GUI)
python start_defipilot.py

# ⚙️ Mode stratégie seul
python strategy_cli.py --pools data/pools_sample.json --journal journal_signaux.jsonl

EN :
Version 4.4 introduces a simplified global launch mode that automatically starts all DeFiPilot components:
the logging daemon, the ControlPilot observer module, and the main graphical interface.
This mode provides real-time visibility of the global context, key metrics (APR, TVL), and market signals directly in both the console and the GUI.
The strategy mode remains available for targeted analysis, while the simulation (dry-run) mode allows testing without real transactions.
# 🚀 Full launch (daemon + ControlPilot + GUI)
python start_defipilot.py

# ⚙️ Strategy mode only
python strategy_cli.py --pools data/pools_sample.json --journal journal_signaux.jsonl


---

🗺️ Feuille de route / Roadmap
FR :
La feuille de route de DeFiPilot vise désormais à faire évoluer l’écosystème complet vers une autonomie totale.
La version 4.4 marque le point de départ de cette phase, avec l’intégration du module ControlPilot et du lancement global automatisé.
Les prochaines versions poursuivront la stabilisation du mode réel, l’enrichissement de la GUI, puis l’extension progressive vers ControlPilot et ArbiPilot, développés en parallèle.
À terme, ces trois modules fonctionneront de manière coordonnée pour former un cluster intelligent et auto-adaptatif.
Prochaines versions :


V4.4 → V4.7 — DeFiPilot : stabilisation du mode réel complet + enrichissement GUI (suivi, stratégie, journaux).


V4.5 → V4.7 — ControlPilot : observation et supervision globale en parallèle du développement DeFiPilot.


V4.6 → V4.8 — ArbiPilot : préparation et premiers tests d’arbitrage inter-DEX / inter-chaînes.


V4.8 → V5.0 — DeFiPilot & ControlPilot : unification partielle, collecte et analyse IA des métriques.


V5.1 → V5.3 — ControlPilot (Phase 2) : supervision IA complète + interconnexion multi-bots.


V5.4+ — ArbiPilot : arbitrage opérationnel entre DEX et blockchains.


V6.x+ — Cluster multi-bots : automatisation complète et orchestration sur SBC (Orange Pi, Raspberry Pi, etc.).


EN :
The DeFiPilot roadmap now aims to evolve the entire ecosystem toward full autonomy.
Version 4.4 marks the beginning of this phase, introducing the ControlPilot module and the unified global launcher.
Next versions will strengthen real-mode stability, enrich the GUI, and expand in parallel through ControlPilot and ArbiPilot development.
Ultimately, these three modules will operate together as an intelligent, self-adaptive cluster.
Upcoming Versions:


V4.4 → V4.7 — DeFiPilot: full real-mode stabilization + enhanced GUI (monitoring, strategy, logs).


V4.5 → V4.7 — ControlPilot: observation and global supervision developed in parallel with DeFiPilot.


V4.6 → V4.8 — ArbiPilot: preparation and early inter-DEX / cross-chain arbitrage tests.


V4.8 → V5.0 — DeFiPilot & ControlPilot: partial unification, metric collection and AI-driven analysis.


V5.1 → V5.3 — ControlPilot (Phase 2): full AI supervision + multi-bot interconnection.


V5.4+ — ArbiPilot: operational arbitrage across DEXs and chains.


V6.x+ — Multi-bot cluster: complete automation and orchestration on SBC (Orange Pi, Raspberry Pi, etc.).



---

## 🎯 Vision du projet / Project Vision

**FR :**  
DeFiPilot est le premier maillon d’un écosystème d’agents DeFi entièrement automatisés.  
Son rôle est d’analyser les opportunités de rendement, d’évaluer le contexte de marché et de gérer les positions de manière autonome, tout en assurant une traçabilité complète via des journaux CSV et JSONL.  
Chaque version vise à renforcer la précision, la réactivité et la stabilité du bot, en passant progressivement du mode simulation à la gestion réelle sur la blockchain Polygon.  
L’écosystème complet comprendra plusieurs modules interconnectés :  

- **DeFiPilot** — cœur d’exécution et de stratégie (analyse, scoring, investissement).  
- **ControlPilot** — supervision centrale et intelligence artificielle (analyse, signaux, pilotage multi-bots).  
- **ArbiPilot** — arbitrage inter-DEX et inter-chaînes.  
- **LabPilot** — expérimentation IA, amélioration continue des algorithmes et stratégies.  

L’objectif final est d’obtenir un système autonome, tournant sur un cluster de SBC (ex. Orange Pi), capable d’évaluer les pools, d’ajuster les positions et de composer les gains sans intervention manuelle, tout en conservant transparence et contrôle total de l’utilisateur.

**EN :**  
DeFiPilot is the first component of a fully automated DeFi agent ecosystem.  
Its purpose is to analyze yield opportunities, assess market context, and manage positions autonomously while maintaining full transparency through CSV and JSONL logs.  
Each release improves accuracy, responsiveness, and stability — progressively transitioning from simulation mode to full real blockchain operations on Polygon.  
The complete ecosystem will include several interconnected modules:  

- **DeFiPilot** — core engine for strategy, scoring, and investment execution.  
- **ControlPilot** — central supervision and AI intelligence (analysis, signals, multi-bot management).  
- **ArbiPilot** — inter-DEX and cross-chain arbitrage.  
- **LabPilot** — AI experimentation and continuous optimization of algorithms and strategies.  

The ultimate goal is a self-governing system running on a cluster of SBCs (e.g., Orange Pi), capable of evaluating pools, adjusting positions, and compounding profits automatically — while remaining fully transparent and user-controlled.


---

❓ FAQ / Foire aux questions

FR :

Q1. DeFiPilot est-il vraiment utilisable sans grosses connaissances techniques ?
Oui. Le projet est pensé pour être accessible aux autodidactes. Il s’utilise via des commandes simples (CLI) ou une interface graphique Tkinter.
Tant que le mode réel n’est pas activé, tout fonctionne en simulation sécurisée (dry-run), ce qui permet d’apprendre sans risque.

Q2. Sur quelle blockchain fonctionne DeFiPilot actuellement ?
DeFiPilot fonctionne actuellement sur Polygon (RPC Infura / Alchemy ou équivalent).
Le multi-blockchain et le multi-DEX sont prévus dans la roadmap et seront intégrés progressivement (notamment avec ArbiPilot).

Q3. Quels DEX sont pris en charge ?
Principalement SushiSwap V2 et MiniChef pour le farming.
Le support d’autres DEX (QuickSwap, Uniswap V3, etc.) arrivera dans les versions ultérieures, parallèlement à l’évolution de ControlPilot et LabPilot.

Q4. L’IA est-elle déjà active dans DeFiPilot ?
Pas encore.
Les versions 4.2 → 4.4 posent les fondations via les signaux de marché et la supervision ControlPilot.
L’intégration IA (analyse contextuelle, recommandations, décisions automatiques) commencera avec la série 5.x.

Q5. Puis-je faire tourner DeFiPilot sur un Orange Pi / Raspberry Pi ?
Oui, c’est même un objectif prioritaire du projet :
exécution légère, 24/7, faible consommation, et compatibilité SBC.
DeFiPilot est testé en environnement Orange Pi 5 Pro, mais reste compatible avec Raspberry Pi ou tout mini-PC équivalent.

Q6. À quoi sert ControlPilot ?
ControlPilot est le module de supervision de l’écosystème.
Il observe les journaux de DeFiPilot, produit des résumés globaux (APR moyen, TVL total, contexte dominant) et assure une surveillance continue du comportement du bot.
Les futures versions y intégreront de l’analyse IA et la coordination entre plusieurs bots.

Q7. Quelle différence entre DeFiPilot, ControlPilot et ArbiPilot ?

DeFiPilot → investit, gère les pools, effectue swaps, ajouts et retraits de liquidité.

ControlPilot → observe, analyse et fournit des recommandations ou alertes.

ArbiPilot → exploite les écarts de prix entre DEX et blockchains (arbitrage).
Ces modules fonctionneront ensemble dans un cluster intelligent multi-bots à partir de la version 6.x.

Q8. Mes clés privées sont-elles en sécurité ?
Oui. Elles sont stockées localement dans le fichier .env, jamais transmises ni partagées.
Le code est entièrement open source et ne communique avec aucune API externe autre que les RPC blockchain spécifiés par l’utilisateur.

EN :

Q1. Can I use DeFiPilot without technical expertise?
Yes. The project is designed to be accessible to self-learners.
It can be used through simple CLI commands or a Tkinter GUI.
As long as real mode is disabled, everything runs in safe simulation (dry-run) mode.

Q2. Which blockchain does DeFiPilot currently support?
DeFiPilot currently runs on Polygon (via Infura / Alchemy RPC or equivalent).
Multi-chain and multi-DEX support are planned for upcoming versions, especially with ArbiPilot.

Q3. Which DEXes are supported?
Mainly SushiSwap V2 and MiniChef for LP farming.
Other DEXes (QuickSwap, Uniswap V3, etc.) will be added gradually alongside the evolution of ControlPilot and LabPilot.

Q4. Is AI already integrated into DeFiPilot?
Not yet.
Versions 4.2 → 4.4 establish the foundation through market signal tracking and ControlPilot supervision.
AI integration (context analysis, recommendations, automated decisions) will begin in the 5.x series.

Q5. Can I run DeFiPilot on an Orange Pi / Raspberry Pi?
Yes — that’s one of the core goals:
lightweight, 24/7 operation with minimal power consumption.
DeFiPilot is tested on Orange Pi 5 Pro, but also works on Raspberry Pi or similar SBCs.

Q6. What is ControlPilot for?
ControlPilot is the ecosystem’s supervision module.
It monitors DeFiPilot logs, produces global summaries (average APR, total TVL, dominant context), and ensures continuous monitoring of bot activity.
Future releases will integrate AI-based analysis and multi-bot coordination.

Q7. What’s the difference between DeFiPilot, ControlPilot, and ArbiPilot?

DeFiPilot → invests, manages pools, performs swaps and liquidity operations.

ControlPilot → observes, analyzes, and provides recommendations or alerts.

ArbiPilot → exploits price discrepancies between DEXes and blockchains.
Together, they will form a smart multi-bot cluster starting from version 6.x.

Q8. Are my private keys safe?
Yes. They’re stored locally in the .env file, never transmitted or shared.
The code is fully open source and interacts only with blockchain RPCs explicitly configured by the user.
---

## 📄 Licence / License

**FR :**  
DeFiPilot est un projet **ouvert à la consultation** et documenté publiquement, mais il reste **à usage personnel et non commercial**. Toute réutilisation publique, redistribution ou intégration dans un produit commercial doit faire l’objet d’un accord préalable explicite de l’auteur. Le but est de partager le cheminement (IA + autodidacte) sans que le projet soit récupéré tel quel à des fins commerciales.

**EN :**  
DeFiPilot is **open for consultation** and publicly documented, but it remains **for personal, non‑commercial use**. Any public redistribution, reuse, or integration into a commercial product must be explicitly approved by the author. The goal is to share the journey (AI‑assisted + self‑taught) without having the project reused as‑is for commercial purposes.

---

**© 2025 — DeFiPilot Project — Développement personnel, non commercial / Personal non-commercial project.**
