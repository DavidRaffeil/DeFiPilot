![DeFiPilot banner](assets/defipilot_banner.png)

> 🗣️ **Langue / Language :** le bot fonctionne uniquement en **français** pour le moment.  
> The bot currently works **in French only** for the moment.

![Version](https://img.shields.io/badge/Version-V4.5%20Stable-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Made in France](https://img.shields.io/badge/Made%20in-France-lightgrey)
![Developed with ChatGPT](https://img.shields.io/badge/Developed%20with-ChatGPT-orange)
![Open Source](https://img.shields.io/badge/Open%20Source-Non%20Commercial-green)
![Polygon Network](https://img.shields.io/badge/Network-Polygon-purple)

---

## 📚 Sommaire / Table of Contents

1. [Introduction / Introduction](#-introduction--introduction)  
2. [Fonctionnalités principales / Key Features](#-fonctionnalités-principales--key-features)  
3. [Nouveautés / What's New — Version 4.5](#-nouveautés--whats-new--version-45)  
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

**EN :**  
DeFiPilot automates DeFi investment analysis and management through:  
- A **strategy engine** computing a weighted score per pool (APR, TVL, volume, volatility, APR trend, expected slippage, etc.).  
- **Investment profiles** (Conservative, Moderate, Aggressive) that adjust thresholds, weights, and exposure limits.  
- A **real mode** able to perform swaps, add/remove liquidity, stake/unstake LP tokens, and harvest rewards (SushiSwap V2 + MiniChef on Polygon).  
- A **Tkinter GUI** that displays market context, active strategy, analyzed pools, and logs in real time.  
- **Extensive logging** to CSV and JSONL for all events (signals, strategies, transactions, errors, system metrics).  

---
## 🆕 Nouveautés / What's New — Version 4.5

**FR :**  
La version **4.5** marque le début de l'intégration de **ControlPilot**, l’agent central de supervision et d’analyse :  
- Collecte unifiée des **métriques opérationnelles** de DeFiPilot (APR moyen, TVL total, contexte de marché, stratégie active, latence, erreurs récentes, etc.).  
- Ajout d’un **module de supervision** dans la GUI : zone dédiée qui affiche l’état global du système, le dernier signal reçu et la stratégie actuellement appliquée.  
- Préparation de la **communication inter-bots** (DeFiPilot ↔ ControlPilot) via des journaux structurés pensés pour être relus et agrégés.  
- Nettoyage et harmonisation des journaux (noms de fichiers, formats de timestamps, champs obligatoires) pour faciliter l’analyse externe.  

**EN :**  
Version **4.5** marks the beginning of **ControlPilot** integration, the central supervision and analysis agent:  
- Unified collection of DeFiPilot **operational metrics** (average APR, total TVL, market context, active strategy, latency, recent errors, etc.).  
- Addition of a **supervision module** in the GUI: a dedicated area displaying global system status, latest signal, and currently applied strategy.  
- Preparation for **inter-bot communication** (DeFiPilot ↔ ControlPilot) through structured logs designed for external reading and aggregation.  
- Cleanup and harmonization of log formats (file names, timestamp formats, required fields) to ease external analysis.

---
## 🕰️ Historique des versions / Past Versions

**FR :**  
DeFiPilot a évolué d'un simple simulateur de rendement à un bot opérationnel complet connecté à Polygon.  
Chaque version a renforcé la robustesse, la clarté des journaux et la sécurité :  

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
- Architecture : modules séparés (`core/`, `gui/`, `defi_sources/`, `strategy/`, etc.) pour faciliter l’évolution du projet.  

**EN :**  
- Language: **Python 3.11+**  
- Interface: **Tkinter** (local GUI, Windows / Linux / SBC such as Orange Pi).  
- Main network: **Polygon PoS** (external RPC such as Infura / Alchemy).  
- Supported DEX (current real mode): **SushiSwap V2 + MiniChef**.  
- Logging: **CSV** files (transactions, farming, liquidity) and **JSONL** files (signals, strategy, supervision).  
- Architecture: separated modules (`core/`, `gui/`, `defi_sources/`, `strategy/`, etc.) to make the project easier to extend.  

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
## ▶️ Utilisation / Usage
FR :

Mode journal + GUI

Lancer le journaliseur continu (signaux de marché) :

python journal_daemon.py --pools data/pools_sample.json --interval 30 --journal journal_signaux.jsonl

Lancer l’interface graphique dans un second terminal :

python gui/main_window.py

Sélectionner le fichier journal_signaux.jsonl dans la GUI si nécessaire,
puis observer les mises à jour en temps réel.

Mode réel

Lorsque le mode réel est activé, exécuter les commandes CLI prévues (swap, add-liquidity, farming) avec prudence,
et toujours vérifier les montants et les adresses avant validation.

EN :

Journal + GUI mode

Start the continuous journal (market signals):

python journal_daemon.py --pools data/pools_sample.json --interval 30 --journal journal_signaux.jsonl

Launch the GUI in a second terminal:

python gui/main_window.py

Select the file journal_signaux.jsonl in the GUI if needed,
then watch real-time updates.

Real mode

When the real mode is enabled, run the provided CLI commands (swap, add-liquidity, farming) carefully,
and always double-check amounts and addresses before confirming any on-chain transaction.

---

## 🗺️ Feuille de route / Roadmap

**FR :**

- **V4.5** — Intégration initiale de ControlPilot (métriques unifiées, supervision dans la GUI).  
- **V4.6 – V4.7** — Stabilisation du mode réel complet avec stratégie automatisée (sélection / retrait des pools, ajustement selon le risque).  
- **V4.8+** — Amélioration de la GUI (filtres avancés, vues historiques, export simplifié).  
- **V5.x — ControlPilot** : agent central de supervision, agrégation multi-bots, premières briques IA.  
- **V6.x — ArbiPilot** : bot d’arbitrage inter-DEX / inter-chaînes, basé sur l’infrastructure de DeFiPilot.  

---

**EN :**

- **V4.5** — Initial ControlPilot integration (unified metrics, supervision in GUI).  
- **V4.6 – V4.7** — Stabilizing the full real mode with automated strategy (pool selection/exit, risk-based adjustments).  
- **V4.8+** — GUI improvements (advanced filters, historical views, easy exports).  
- **V5.x — ControlPilot**: central supervision agent, multi-bot aggregation, first AI bricks.  
- **V6.x — ArbiPilot**: inter-DEX / cross-chain arbitrage bot built on DeFiPilot’s infrastructure.  

---
## 🌌 Vision du projet / Project Vision

**FR :**

DeFiPilot n’est pas seulement un bot DeFi, c’est un **laboratoire public** montrant qu’un autodidacte, accompagné par l’IA,  
peut construire pas à pas un écosystème complet :  

- Un bot principal (**DeFiPilot**) qui gère des investissements réels de manière transparente.  
- Un centre de contrôle (**ControlPilot**) qui observe, agrège et analyse.  
- Des modules spécialisés (**ArbiPilot**, **LabPilot**, etc.) qui viendront explorer d’autres stratégies.  

L’objectif est autant pédagogique que pratique : documenter chaque étape pour inspirer d’autres personnes à construire leurs propres outils.

---

**EN :**

DeFiPilot is not only a DeFi bot — it is a **public lab** proving that a self-taught user, assisted by AI,  
can progressively build a complete ecosystem:  

- A main bot (**DeFiPilot**) managing real investments with transparency.  
- A control center (**ControlPilot**) that observes, aggregates, and analyzes.  
- Specialized modules (**ArbiPilot**, **LabPilot**, etc.) to explore additional strategies.  

The goal is both educational and practical: to document every step and inspire others to build their own tools.

---
## ❓ FAQ / Foire aux questions

**FR :**

**Q : Puis-je utiliser DeFiPilot pour gérer de gros montants ?**  
R : Le projet est expérimental et développé par une seule personne.  
Il n’est **pas recommandé** de l’utiliser pour des montants importants sans audits externes ni revue approfondie du code.  

**Q : Le bot est-il multi-chaînes ?**  
R : La version actuelle se concentre sur **Polygon**.  
L’extension à d’autres blockchains est prévue, mais pas prioritaire.  

**Q : Pourquoi la langue principale est-elle le français ?**  
R : Le projet est mené par un auteur francophone et sert aussi de support d’apprentissage personnel.  
L’anglais est ajouté pour le rendre compréhensible au plus grand nombre.  

**Q : DeFiPilot nécessite-t-il une clé privée réelle ?**  
R : Oui, en mode réel, une clé privée est utilisée pour signer les transactions.  
Cependant, elle reste stockée localement sur votre machine.  
Aucune donnée n’est envoyée en ligne ni stockée sur un serveur externe.  

**Q : Le bot peut-il fonctionner sans interface graphique ?**  
R : Oui, le bot peut être utilisé entièrement en ligne de commande (CLI).  
La GUI Tkinter n’est qu’une interface de visualisation et de contrôle optionnelle.  

**Q : Est-ce que DeFiPilot peut tourner en continu ?**  
R : Oui, il est conçu pour fonctionner en tâche de fond.  
Il peut être exécuté en permanence sur un PC, un mini-serveur ou un SBC comme un **Orange Pi**.  

**Q : Quelle est la consommation de ressources du bot ?**  
R : Le bot est très léger.  
Il consomme peu de mémoire et de CPU, ce qui permet de le faire tourner sur un mini-PC ou un micro-ordinateur à faible puissance.  

**Q : Les données sont-elles sauvegardées ?**  
R : Oui, toutes les opérations sont enregistrées dans des journaux CSV et JSONL.  
Ces fichiers permettent d’analyser les performances, les transactions et les stratégies après exécution.  

**Q : Comment sont calculés les scores des pools ?**  
R : Un algorithme interne combine plusieurs métriques (APR, TVL, volume, volatilité, tendance APR, slippage estimé).  
Ces valeurs sont pondérées selon le profil d’investissement choisi (Prudent, Modéré ou Risqué).  

**Q : Le projet deviendra-t-il open source complet ?**  
R : Le code est consultable librement sur GitHub, mais il reste à usage **personnel et non commercial**.  
Toute réutilisation publique ou intégration commerciale nécessitera une autorisation de l’auteur.  

---

**EN :**

**Q: Can I use DeFiPilot to manage large amounts of capital?**  
A: The project is experimental and developed by a single person.  
It is **not recommended** to use it for large amounts without external audits and a full code review.  

**Q: Is the bot multi-chain?**  
A: The current version focuses on **Polygon**.  
Support for other blockchains is planned but not a short-term priority.  

**Q: Why is French the main language?**  
A: The author is a French speaker and uses this project as a personal learning experience.  
English is added to make the documentation accessible worldwide.  

**Q: Does DeFiPilot require a real private key?**  
A: Yes, in real mode a private key is used to sign transactions,  
but it is stored locally on your device and never sent online or saved remotely.  

**Q: Can the bot run without the graphical interface?**  
A: Yes, it can be fully operated through the command line (CLI).  
The Tkinter GUI is optional and meant for visual monitoring.  

**Q: Can DeFiPilot run continuously?**  
A: Yes, it is designed to run in the background on a PC or **Single Board Computer** (like an Orange Pi).  

**Q: What about resource usage?**  
A: The bot is lightweight, consuming very little memory or CPU,  
making it ideal for small, low-power machines.  

**Q: Are operations logged?**  
A: Yes, all activities are recorded in CSV and JSONL files  
to track performance, transactions, and strategies afterward.  

**Q: How are pool scores calculated?**  
A: An internal algorithm combines several metrics (APR, TVL, volume, volatility, APR trend, estimated slippage)  
and applies profile-based weights (Conservative, Moderate, Aggressive).  

**Q: Will the project become fully open source?**  
A: The code is publicly viewable but remains **personal and non-commercial**.  
Any redistribution or commercial use requires explicit permission from the author.  

---
## 📄 Licence / License

**FR :**

DeFiPilot est un projet **ouvert à la consultation** et documenté publiquement,  
mais il reste **à usage personnel et non commercial**.  

Toute redistribution, réutilisation ou intégration dans un produit commercial  
nécessite un **accord explicite** de l'auteur.  

L’objectif du projet est de partager une démarche d’apprentissage et d’autonomie assistée par l’IA,  
sans exploitation commerciale directe.  

---

**EN :**

DeFiPilot is **open for consultation** and publicly documented,  
but it remains **for personal, non-commercial use**.  

Any redistribution, reuse, or integration into a commercial product  
requires the **explicit consent** of the author.  

The goal of this project is to share an AI-assisted learning and self-development journey,  
without any direct commercial exploitation.  

---

**© 2025 — DeFiPilot Project — Développement personnel, non commercial / Personal non-commercial project.**
