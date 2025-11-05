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
3. [Nouveautés / What's New — Version 4.3](#-nouveautés--whats-new--version-43)  
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

## 🆕 Nouveautés / What's New — Version 4.3

**FR :**  
La version **4.3** introduit l’interface graphique complète de **DeFiPilot**, permettant un suivi visuel clair et fluide des stratégies, du contexte de marché et des scores de pools en temps réel.  
Cette version consolide la stabilité du mode simulation et intègre un rafraîchissement automatique des données, un affichage dynamique du statut (🟢 favorable, 🟡 neutre, 🔴 défavorable) et un tableau de bord ergonomique.  
Le moteur de stratégie et le journaliseur continu travaillent désormais de concert avec l’interface pour offrir une vue instantanée des signaux de marché et des allocations actives.  
Cette étape prépare le terrain pour la future intégration du module **ControlPilot** (analyse IA et pilotage multi-bots).

**EN :**  
Version **4.3** introduces the complete graphical interface of **DeFiPilot**, offering a clear and smooth visual overview of strategies, market context, and pool scores in real time.  
This release enhances simulator stability and adds automatic data refresh, dynamic status indicators (🟢 favorable, 🟡 neutral, 🔴 unfavorable), and an ergonomic dashboard.  
The strategy engine and continuous logger now work seamlessly with the interface to provide instant insights into market signals and active allocations.  
This version lays the foundation for upcoming integration with **ControlPilot**, the AI-driven multi-bot management module.

---

## 🕰️ Historique des versions / Past Versions

**FR :**  
DeFiPilot a connu une évolution continue à travers plusieurs versions majeures, passant d’un simple simulateur de rendement à un outil pleinement opérationnel capable d’interagir avec la blockchain Polygon. Chaque itération a apporté de nouvelles fonctionnalités — de la simulation des pools à la connexion à un wallet réel, jusqu’au farming automatisé via SushiSwap et MiniChef. Ces étapes successives ont renforcé la stabilité, la transparence des journaux et la sécurité des transactions.  

Les principales versions incluent :  
V4.2 — moteur de stratégie optimisé, signaux enrichis et compatibilité GUI.  
V4.1 — interface graphique minimale (barre de statut, cartes principales).  
V4.0 — stratégie de marché et allocation dynamique.  
V3.9 — farming LP réel via MiniChef SushiSwap Polygon.  
V3.8 — ajout de liquidité réel sur Polygon (SushiSwap V2).  
V3.7 — swap réel avec gestion du slippage et logs complets.  
V3.6 — connexion multi-wallet réelle (Polygon).  
V1.x → V2.x — simulation complète, scoring et intégration DefiLlama.

**EN :**  
DeFiPilot has evolved continuously through several major versions, progressing from a simple yield simulator to a fully operational tool capable of interacting with the Polygon blockchain. Each iteration added new features — from pool simulation to real wallet connection and automated farming via SushiSwap and MiniChef. These successive updates improved stability, transparency of logs, and transaction security.  

The main versions include:  
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

## ⚙️ Installation / Installation

**FR :**  
L’installation de DeFiPilot est simple et rapide. Elle peut être effectuée sur tout système disposant de Python 3.11 ou supérieur. Il suffit de cloner le dépôt GitHub, de créer un environnement virtuel et d’installer les dépendances nécessaires. Enfin, renommez le fichier `.env.example` en `.env` puis complétez les informations requises (clé RPC Polygon, clé privée, chemins de journaux, etc.).

```bash
# 1. Cloner le dépôt
git clone https://github.com/DavidRaffeil/DeFiPilot.git
cd DeFiPilot

# 2. Créer un environnement virtuel (optionnel)
python -m venv .venv
source .venv/bin/activate  # sous Windows : .venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt
```

**EN :**  
Installing DeFiPilot is straightforward and can be done on any system with Python 3.11 or higher. Clone the GitHub repository, create a virtual environment, and install the required dependencies. Finally, rename the `.env.example` file to `.env` and fill in the necessary information (Polygon RPC key, private key, log paths, etc.).

```bash
# 1. Clone the repository
git clone https://github.com/DavidRaffeil/DeFiPilot.git
cd DeFiPilot

# 2. Create a virtual environment (optional)
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Utilisation / Usage

**FR :**  
DeFiPilot peut être utilisé en mode stratégie ou en mode simulation. Le mode stratégie exécute le moteur d’analyse pour détecter le contexte de marché et déterminer la répartition optimale entre les profils Risqué, Modéré et Prudent. Le mode simulation (dry-run) permet de tester toutes les fonctionnalités sans effectuer de transactions réelles, ce qui est idéal pour valider les paramètres et observer le comportement du bot avant un déploiement réel.

```bash
# Mode stratégie
python strategy_cli.py --pools data/pools_sample.json --journal journal_signaux.jsonl
```

**EN :**  
DeFiPilot can be used either in strategy mode or in simulation mode. The strategy mode runs the analysis engine to detect the market context and determine the optimal allocation among Risk, Moderate, and Conservative profiles. The simulation (dry-run) mode allows testing all features without performing real transactions, making it ideal to validate parameters and observe the bot’s behavior before real deployment.

```bash
# Strategy mode
python strategy_cli.py --pools data/pools_sample.json --journal journal_signaux.jsonl
```

---

## 🗺️ Feuille de route / Roadmap

**FR :**  
La feuille de route de DeFiPilot poursuit son objectif : atteindre un écosystème DeFi entièrement automatisé et intelligent.  
Après la version **4.3**, qui introduit l’interface graphique complète et le monitoring temps réel, la priorité est donnée à la consolidation du mode réel complet et à la supervision via **ControlPilot**.  
Ce dernier assurera la collecte, l’analyse et l’interprétation des métriques de marché pour assister les décisions d’investissement.  
Les futures versions introduiront progressivement des capacités d’intelligence artificielle pour la détection contextuelle, l’optimisation de stratégie et la communication entre les différents bots (DeFiPilot, ControlPilot, ArbiPilot, LabPilot).  
L’ambition finale reste inchangée : un système autonome, transparent et documenté, capable d’analyser, d’investir et d’évoluer sans intervention manuelle.

**Prochaines versions :**  
- **V4.4 → V4.7** — Stabilisation du mode réel complet + enrichissement GUI (suivi, stratégie, journaux).  
- **V4.8 → V5.0** — **ControlPilot (Phase 1)** : collecte et analyse IA des métriques.  
- **V5.1 → V5.3** — **ControlPilot (Phase 2)** : supervision IA + interconnexion multi-bots.  
- **V5.4+** — **ArbiPilot** : arbitrage inter-DEX / inter-chaînes.  
- **V6.x+** — **Cluster multi-bots** : automatisation complète sur SBC.

**EN :**  
DeFiPilot’s roadmap continues its mission to achieve a fully automated and intelligent DeFi ecosystem.  
After version **4.3**, which introduced the complete graphical interface and real-time monitoring, the focus shifts to strengthening full real-mode operation and introducing intelligent supervision through **ControlPilot**.  
ControlPilot will handle the collection, analysis, and interpretation of market metrics to support investment decisions.  
Future releases will progressively integrate AI capabilities for contextual detection, strategy optimization, and communication between bots (DeFiPilot, ControlPilot, ArbiPilot, LabPilot).  
The long-term goal remains unchanged: a self-sufficient, transparent, and documented system capable of analyzing, investing, and evolving without manual input.

**Upcoming Versions:**  
- **V4.4 → V4.7** — Full real-mode stabilization + enhanced GUI (monitoring, strategy, logs).  
- **V4.8 → V5.0** — **ControlPilot (Phase 1)**: metric collection and AI analysis.  
- **V5.1 → V5.3** — **ControlPilot (Phase 2)**: AI supervision + multi-bot interconnection.  
- **V5.4+** — **ArbiPilot**: inter-DEX / cross-chain arbitrage.  
- **V6.x+** — **Multi-bot cluster**: full automation on SBC.

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

## ❓ FAQ / Foire aux questions

**FR :**  
**Q1. DeFiPilot est-il vraiment utilisable sans grosses connaissances techniques ?**  
Oui. Le projet est construit pas à pas, avec des commandes CLI simples et maintenant une interface Tkinter minimale. Tant que le mode réel n’est pas activé, tout fonctionne en simulation (dry-run), ce qui évite les erreurs coûteuses.  
**Q2. Sur quelle blockchain fonctionne DeFiPilot actuellement ?**  
Actuellement sur **Polygon** (RPC Infura / Alchemy ou équivalent). Le multi‑blockchain et le multi‑DEX sont prévus dans la roadmap, mais seront intégrés progressivement.  
**Q3. Quels DEX sont pris en charge ?**  
Principalement **SushiSwap V2** et **MiniChef** pour le farming. D’autres DEX pourront être ajoutés dans les versions V4.3+ et surtout avec ControlPilot/LabPilot.  
**Q4. L’IA est-elle déjà active dans DeFiPilot ?**  
Pas encore. La V4.2 prépare les **signaux** pour que ControlPilot puisse les exploiter. L’IA arrivera dans les versions 4.4 → 5.x.  
**Q5. Puis-je faire tourner DeFiPilot sur un Orange Pi / Raspberry Pi ?**  
Oui, c’est même un objectif du projet : exécution légère, 24/7, faible consommation.

**EN :**  
**Q1. Can I use DeFiPilot without being a developer?**  
Yes. The project is built step by step, with simple CLI commands and now a minimal Tkinter GUI. As long as real mode is not enabled, everything runs in simulation (dry-run), which prevents costly mistakes.  
**Q2. Which blockchain does DeFiPilot run on right now?**  
Currently on **Polygon** (Infura / Alchemy RPC or equivalent). Multi‑chain and multi‑DEX support are planned and will be added gradually.  
**Q3. Which DEXes are supported?**  
Mainly **SushiSwap V2** and **MiniChef** for farming. More DEXes will be added in V4.3+ and especially when ControlPilot/LabPilot are active.  
**Q4. Is AI already integrated in DeFiPilot?**  
Not yet. V4.2 prepares the **signals** so that ControlPilot can consume them. AI will arrive in versions 4.4 → 5.x.  
**Q5. Can I run DeFiPilot on an Orange Pi / Raspberry Pi?**  
Yes, this is one of the project goals: lightweight, 24/7, low‑power execution.

---

## 📄 Licence / License

**FR :**  
DeFiPilot est un projet **ouvert à la consultation** et documenté publiquement, mais il reste **à usage personnel et non commercial**. Toute réutilisation publique, redistribution ou intégration dans un produit commercial doit faire l’objet d’un accord préalable explicite de l’auteur. Le but est de partager le cheminement (IA + autodidacte) sans que le projet soit récupéré tel quel à des fins commerciales.

**EN :**  
DeFiPilot is **open for consultation** and publicly documented, but it remains **for personal, non‑commercial use**. Any public redistribution, reuse, or integration into a commercial product must be explicitly approved by the author. The goal is to share the journey (AI‑assisted + self‑taught) without having the project reused as‑is for commercial purposes.

---

**© 2025 — DeFiPilot Project — Développement personnel, non commercial / Personal non-commercial project.**
