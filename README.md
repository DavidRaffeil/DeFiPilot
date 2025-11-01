<p align="center">
  <img src="assets/defipilot_banner.png" alt="DeFiPilot banner" width="100%">
</p>

> 🗣️ **Langue / Language :** le bot fonctionne uniquement en **français** pour le moment.  
> The bot currently works **in French only** for the moment.

![Version](https://img.shields.io/badge/Version-V4.2%20Stable-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Made in France](https://img.shields.io/badge/Made%20in-France-lightgrey)
![Developed with ChatGPT](https://img.shields.io/badge/Developed%20with-ChatGPT-orange)
![Open Source](https://img.shields.io/badge/Open%20Source-Non%20Commercial-green)
![Polygon Network](https://img.shields.io/badge/Network-Polygon-purple)

---

## 📚 Sommaire / Table of Contents

1. [Introduction / Introduction](#-introduction--introduction)  
2. [Fonctionnalités principales / Key Features](#-fonctionnalités-principales--key-features)  
3. [Nouveautés / What's New — Version 4.2](#-nouveautés--whats-new--version-42)  
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

## 🆕 Nouveautés / What's New — Version 4.2

**FR :**  
La version **4.2** marque une étape importante dans l’évolution de DeFiPilot. Elle introduit un moteur de stratégie optimisé, capable de prendre en compte la volatilité du marché, la tendance des APR et le TVL global afin d’ajuster dynamiquement les allocations de risque. Cette version renforce également la détection du contexte de marché (favorable, neutre, défavorable) et améliore la précision du calcul de score. Les nouvelles métriques sont désormais journalisées dans `journal_signaux.jsonl` et intégrées à l’interface graphique pour un suivi visuel en temps réel. L’ensemble prépare le terrain pour la communication inter-module avec **ControlPilot**, le futur module d’analyse IA.

**EN :**  
Version **4.2** marks a major milestone in DeFiPilot’s evolution. It introduces an optimized strategy engine capable of factoring in market volatility, APR trends, and global TVL to dynamically adjust risk allocations. This release also enhances market context detection (favorable, neutral, unfavorable) and improves scoring accuracy. New metrics are now logged in `journal_signaux.jsonl` and integrated into the graphical interface for real-time visual monitoring. Overall, this version lays the groundwork for future inter‑module communication with **ControlPilot**, the upcoming AI analysis module.

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
La feuille de route de DeFiPilot trace les prochaines étapes vers un écosystème DeFi complet et entièrement automatisé. Après la version 4.2, l’objectif est de perfectionner l’interface graphique et d’introduire un système de supervision intelligente via **ControlPilot**, qui analysera les métriques de marché et les signaux de stratégie. Les futures versions intégreront progressivement des modules d’intelligence artificielle pour la prise de décision automatisée, la gestion du risque et l’interconnexion entre bots (DeFiPilot, ControlPilot, ArbiPilot, LabPilot). L’ambition finale est d’obtenir un système autonome capable d’évaluer, d’investir et de s’ajuster sans intervention manuelle, tout en restant transparent et documenté.

**Prochaines versions :**  
- **V4.3** — Interface complète et suivi temps réel (GUI avancée).  
- **V4.4** — **ControlPilot (Phase 1)** : collecte de métriques et signaux IA.  
- **V4.5 → V5.0** — **ControlPilot (Phase 2)** : intégration IA + interconnexion multi-bots.  
- **V5.x+** — **ArbiPilot** : arbitrage inter-DEX / inter-chaînes.  
- **V6.x+** — **Cluster multi-bots** : automatisation complète sur SBC.

**EN :**  
DeFiPilot’s roadmap outlines the next steps toward a fully automated DeFi ecosystem. After version 4.2, the goal is to enhance the graphical interface and introduce intelligent supervision through **ControlPilot**, which will analyze market metrics and strategic signals. Future releases will gradually integrate AI modules for automated decision-making, risk management, and cross-bot interconnection (DeFiPilot, ControlPilot, ArbiPilot, LabPilot). The ultimate aim is a self-governing system that can evaluate, invest, and adapt without manual intervention while remaining transparent and documented.

**Upcoming Versions:**  
- **V4.3** — Full interface with real-time monitoring (advanced GUI).  
- **V4.4** — **ControlPilot (Phase 1)**: metrics collection and AI signals.  
- **V4.5 → V5.0** — **ControlPilot (Phase 2)**: AI integration + multi-bot interconnection.  
- **V5.x+** — **ArbiPilot**: inter-DEX / cross-chain arbitrage.  
- **V6.x+** — **Multi-bot cluster**: full automation on SBC.

---

## 🌐 Vision du projet / Project Vision

**FR :**  
La vision de DeFiPilot est de créer un écosystème complet et cohérent de bots DeFi autonomes travaillant ensemble de manière intelligente et transparente. Chaque composant a un rôle spécifique : **DeFiPilot** gère l’investissement et la sélection des pools, **ControlPilot** assure la supervision et l’analyse du contexte de marché, **ArbiPilot** exploite les opportunités d’arbitrage inter-DEX et inter-chaînes, et **LabPilot** sert de laboratoire d’expérimentation pour tester de nouvelles stratégies et intégrer des modèles d’IA. À long terme, l’objectif est d’obtenir un réseau autonome capable de fonctionner sur du matériel léger (SBC) tout en maintenant un contrôle total, une documentation claire et une traçabilité complète des décisions.

**EN :**  
DeFiPilot’s vision is to build a complete and coherent ecosystem of autonomous DeFi bots working together intelligently and transparently. Each component plays a specific role: **DeFiPilot** manages investments and pool selection, **ControlPilot** handles supervision and market context analysis, **ArbiPilot** takes advantage of inter-DEX and cross-chain arbitrage opportunities, and **LabPilot** acts as an experimental lab to test new strategies and integrate AI models. In the long term, the goal is to achieve a self-sustaining network running on lightweight hardware (SBC) while maintaining full control, clear documentation, and complete traceability of decisions.

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
