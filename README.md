<p align="center">
  <img src="assets/defipilot_banner.png" alt="DeFiPilot banner" width="100%">
</p>

> 🗣️ **Langue / Language :** le bot fonctionne uniquement en **français** pour le moment.  
> The bot currently works **in French only** for the moment.


![Version](https://img.shields.io/badge/Version-V4.0%20Stable-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Made in France](https://img.shields.io/badge/Made%20in-France-lightgrey)
![Developed with ChatGPT](https://img.shields.io/badge/Developed%20with-ChatGPT-orange)
![Open Source](https://img.shields.io/badge/Open%20Source-Non%20Commercial-green)
![Polygon Network](https://img.shields.io/badge/Network-Polygon-purple)
---

## 📚 Sommaire / Table of Contents

1. [Introduction / Introduction](#-introduction--introduction)  
2. [Installation / Installation](#️-installation--installation)  
3. [Fonctionnalités principales / Key Features](#-fonctionnalités-principales--key-features)  
4. [Nouveautés / What's New — Version 4.0](#-nouveautés--whats-new--version-40)  
5. [Feuille de route / Roadmap](#-feuille-de-route--roadmap-évolution-prévue--planned-evolution)  
6. [Vision complète du projet / Complete Project Vision](#-vision-complète-du-projet--complete-project-vision)  
7. [FAQ / FAQ](#-faq--faq)  
8. [À propos / About](#-à-propos--about)  

---

## 🚀 Introduction / Introduction

**FR :**  
**DeFiPilot** est un bot d’investissement automatisé conçu pour interagir directement avec la finance décentralisée (**DeFi**).  
Il exécute des opérations réelles sur la blockchain, notamment les **swaps de tokens**, l’**ajout de liquidité** et le **farming des tokens LP**, tout en appliquant une stratégie de gestion des risques fondée sur le contexte de marché.  

Le projet repose sur une **architecture modulaire**, composée de :  
- un moteur de stratégie adaptatif,  
- un module d’analyse du marché (signaux et contexte),  
- un moteur d’exécution pour les opérations réelles,  
- un système complet de **journalisation CSV/JSONL** pour la traçabilité.  

L’objectif est double : offrir un outil **fiable et transparent** pour automatiser la gestion de pools de liquidité,  
et poser les bases d’un **écosystème intelligent** capable d’analyser la rentabilité, de réallouer automatiquement les ressources et de s’adapter à la dynamique des marchés.  

Développé entièrement en **Python**, DeFiPilot fonctionne actuellement sur **Polygon**, avec compatibilité multi-chaînes prévue.  
L’architecture suit des standards sécurisés (Web3, RPC Infura, transactions validées et confirmées)  
et chaque version progresse vers une intégration complète de l’IA (via **ControlPilot**, **LabPilot** et **ArbiPilot**).  

•••

**EN :**  
**DeFiPilot** is an automated investment bot built to interact directly with decentralized finance (**DeFi**).  
It performs real blockchain operations such as **token swaps**, **liquidity addition**, and **LP token farming**,  
while applying a risk-based market strategy.  

The project relies on a **modular architecture** that includes :  
- an adaptive strategy engine,  
- a market signal and context analysis module,  
- a real transaction execution engine,  
- and a complete **CSV/JSONL logging system** for transparency.  

Its goal is to provide a **reliable and transparent tool** for liquidity pool automation  
and to establish the foundation of an **intelligent DeFi ecosystem** capable of analyzing profitability,  
reallocating funds, and adapting to market dynamics.  

Developed entirely in **Python**, DeFiPilot currently runs on **Polygon**,  
with future multi-chain support planned.  
The system follows secure standards (Web3, Infura RPC, validated transactions),  
and each release advances toward full AI integration (via **ControlPilot**, **LabPilot**, and **ArbiPilot**).  

---

## ⚙️ Installation / Installation

**FR :**  
Suivez ces étapes pour installer et exécuter **DeFiPilot** localement :  

1. **Cloner le dépôt :**  
   ```bash
   git clone https://github.com/DavidRaffeil/DeFiPilot.git
   cd DeFiPilot
   ```
2. **Créer un environnement virtuel (recommandé) :**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # sous Linux/macOS
   venv\\Scripts\\activate      # sous Windows
   ```
3. **Installer les dépendances :**  
   ```bash
   pip install -r requirements.txt
   ```
4. **Lancer le mode simulation :**  
   ```bash
   python main.py --dry-run
   ```

**Exemple de sortie console :**  
```
Simulation en cours...
Analyse des pools Polygon...
Pool USDC/WETH détectée — Score : 0.87
Simulation terminée : aucun fonds réel utilisé.
```

**Compatibilité :**  
Fonctionne sur Windows, Linux, macOS, **Orange Pi** et **Raspberry Pi**.  

•••

**EN :**  
Follow these steps to install and run **DeFiPilot** locally :  

1. **Clone the repository:**  
   ```bash
   git clone https://github.com/DavidRaffeil/DeFiPilot.git
   cd DeFiPilot
   ```
2. **Create a virtual environment (recommended):**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\\Scripts\\activate      # Windows
   ```
3. **Install dependencies:**  
   ```bash
   pip install -r requirements.txt
   ```
4. **Run in simulation mode:**  
   ```bash
   python main.py --dry-run
   ```

**Example console output:**  
```
Simulation running...
Analyzing Polygon pools...
USDC/WETH pool detected — Score: 0.87
Simulation complete: no real funds used.
```

**Compatibility:**  
Works on Windows, Linux, macOS, **Orange Pi**, and **Raspberry Pi** SBCs.  

---
## 🧩 Fonctionnalités principales / Key Features

**FR :**  
Les fonctionnalités de **DeFiPilot** sont structurées autour de trois axes : **sécurité**, **analyse** et **automatisation**.  

### 🔐 1. Connexion et sécurité
- Connexion à un **wallet réel** via RPC sécurisé (Polygon / Infura).  
- Gestion **multi-wallets** pour répartir les fonds selon le profil d’investissement.  
- Vérification des autorisations (**allowances**) avant chaque transaction.  
- Validation complète des transactions (statut, gas, coût, confirmation).  

### 📊 2. Analyse et stratégie
- Calcul du **contexte de marché** (favorable, neutre, défavorable) à partir de données de pools.  
- Détermination d’une **allocation dynamique** selon le profil d’investisseur (prudent, modéré, risqué).  
- Intégration d’un moteur de **scoring pondéré** pour classer les pools selon leur rentabilité.  
- Préparation d’une intégration future avec un moteur **IA** pour l’optimisation des décisions.  

### ⚙️ 3. Exécution et journalisation
- **Swaps réels** sur DEX (ex. SushiSwap) avec gestion du slippage et des confirmations.  
- **Ajout et retrait de liquidité** automatisé, avec suivi précis des LP tokens reçus.  
- **Farming LP réel** : stake, harvest et unstake sur SushiSwap MiniChef (Polygon).  
- **Mode simulation complet** (dry-run) pour tester toutes les stratégies sans risque.  
- **Journaux CSV/JSONL détaillés** (exécution, gas, statuts, contexte, allocation).  
- **Interface CLI** claire et intégralement en français.  

**Exigences système minimales :**  
- Python **3.11+**  
- Accès RPC Polygon (ex. Infura, Alchemy)  
- Environnement local ou SBC (Orange Pi, Raspberry Pi) compatible  

•••

**EN :**  
The features of **DeFiPilot** are organized around three key areas: **security**, **analysis**, and **automation**.  

### 🔐 1. Connection and Security
- Connect to a **real wallet** via secure RPC (Polygon / Infura).  
- **Multi-wallet management** to allocate funds per investment profile.  
- Authorization checks (**allowances**) before every transaction.  
- Full transaction validation (status, gas, cost, confirmation).  

### 📊 2. Analysis and Strategy
- Calculation of **market context** (favorable, neutral, unfavorable) from pool data.  
- Determination of **dynamic allocation** based on investor profile (prudent, moderate, risky).  
- Integration of a **weighted scoring engine** to rank pools by profitability.  
- Prepared for future integration with an **AI engine** for decision optimization.  

### ⚙️ 3. Execution and Logging
- **Real swaps** on DEXs (e.g., SushiSwap) with slippage control and confirmations.  
- **Automated add/remove liquidity** with precise tracking of received LP tokens.  
- **Real LP farming**: stake, harvest, and unstake on SushiSwap MiniChef (Polygon).  
- Full **simulation mode** (dry-run) to test all strategies safely.  
- Detailed **CSV/JSONL logs** (execution, gas, status, context, allocation).  
- **CLI interface** fully in French.  

**Minimum system requirements:**  
- Python **3.11+**  
- Polygon RPC access (e.g., Infura, Alchemy)  
- Compatible local or SBC environment (Orange Pi, Raspberry Pi)  

---

## 🆕 Nouveautés / What's New — Version 4.0
---

## 🖼️ Aperçu visuel / Visual Preview

> **Note :** ces aperçus sont affichés en français car le bot ne fonctionne qu’en français pour le moment.  
> **Note:** these previews are shown in French because the bot currently works in French only.

**FR :**  
Exemples d’exécution réelle de **DeFiPilot** en ligne de commande (CLI).  
Ces aperçus montrent le fonctionnement du bot en mode réel et en simulation.

```
$ python strategy_cli.py --pools data/pools_sample.json --cfg config/defipilot_config.json
Contexte détecté : favorable
Allocation cible : Risqué 60% | Modéré 30% | Prudent 10%
Score global : 0.67
Journal mis à jour : journal_signaux.jsonl
```

```
$ python liquidity_cli.py --dry-run
Simulation d’ajout de liquidité...
Pair USDC/WETH détectée (SushiSwap)
Montant simulé : 0.50 USDC + 0.00012 WETH
Aucune transaction réelle effectuée.
```

---

**FR :**  
La version **4.0** marque une étape clé : le passage du **mode simulation** à l’**exécution réelle** sur la blockchain.  
Elle introduit de nouvelles briques fonctionnelles, un moteur de stratégie amélioré et une refonte complète de la structure de journalisation.  

### 🧠 Principales améliorations techniques
- **Mode réel complet** : toutes les opérations principales (swap, ajout de liquidité, farming) sont désormais exécutées directement sur la blockchain Polygon avec vérification des statuts de transaction.  
- **Gestion du slippage et validation de prix** : calcul automatique des tolérances et vérifications des ratios avant chaque opération.  
- **Moteur de stratégie adaptatif** : détecte le contexte de marché et ajuste dynamiquement l’allocation selon le profil d’investisseur.  
- **Journalisation unifiée** : chaque opération génère une entrée structurée dans les fichiers CSV et JSONL, incluant le run_id, le gas utilisé, le coût, le statut et le contexte de décision.  
- **Renforcement de la robustesse** : contrôles d’erreur étendus, validation des entrées et gestion propre des échecs de transaction.  
- **Préparation de l’interface graphique (GUI)** : la base de données des pools et la couche de stratégie sont désormais prêtes pour l’intégration visuelle prévue en V4.1.  

**Impact global :**  
La V4.0 transforme DeFiPilot d’un simple simulateur d’investissement en un **bot DeFi réellement opérationnel**, capable d’exécuter, vérifier et enregistrer des opérations en temps réel.  
Cette transition constitue la base du futur moteur de décision intelligent.  

•••

**EN :**  
Version **4.0** represents a key milestone: the transition from **simulation mode** to **real on-chain execution**.  
It introduces new functional modules, an improved strategy engine, and a complete overhaul of the logging structure.  

### 🧠 Main Technical Improvements
- **Full real mode:** all core operations (swap, add liquidity, farming) are now executed directly on the Polygon blockchain with full transaction verification.  
- **Slippage and price validation management:** automatic calculation of tolerances and pre-check of ratios before each transaction.  
- **Adaptive strategy engine:** detects market context and dynamically adjusts allocation based on investor profile.  
- **Unified logging:** every operation produces a structured entry in CSV and JSONL logs, including run_id, gas used, cost, status, and decision context.  
- **Improved robustness:** extended error handling, input validation, and clean transaction failure management.  
- **Graphical Interface (GUI) preparation:** pool database and strategy layer are now ready for integration in V4.1.  

**Overall impact:**  
V4.0 transforms DeFiPilot from a simple investment simulator into a **fully operational DeFi bot**, capable of executing, validating, and logging real-time blockchain operations.  
This marks the foundation of the future intelligent decision engine.  

---
## 🗺️ Feuille de route / Roadmap (évolution prévue / Planned Evolution)

**FR :**  
La feuille de route de **DeFiPilot** est conçue pour une progression claire et maîtrisée, version après version. Chaque mise à jour introduit une nouvelle brique fonctionnelle ou une amélioration majeure en stabilité, performance ou autonomie.  

### 🔸 V4.1 — Interface graphique (GUI) initiale
Ajout d’une interface utilisateur simple permettant de visualiser les pools, les scores et les allocations en temps réel. Cette version introduira les premiers éléments d’affichage dynamique et la gestion visuelle des profils d’investissement.  

### 🔸 V4.2 — Optimisation du moteur de stratégie et signaux de marché
Amélioration de la détection du contexte de marché et intégration de métriques avancées (volatilité, tendance des APR, TVL global). Consolidation du moteur de stratégie et préparation de la communication inter-module.  

### 🔸 V4.3 — Interface complète et monitoring
Déploiement d’une interface complète avec suivi temps réel des transactions, affichage des journaux et tableaux de bord personnalisables. Le système deviendra un véritable poste de pilotage visuel du bot.  

### 🔸 V4.4 — Développement de ControlPilot (IA de supervision)
Création d’un agent de surveillance intelligent collectant les métriques du bot, du marché et du wallet. Il permettra de générer des signaux de risque ou d’opportunité en temps réel.  

### 🔸 V4.5 – V5.0 — Intégration IA et multi-bots
Connexion de DeFiPilot à un réseau d’agents IA capables d’analyser, recommander et coordonner les décisions entre plusieurs bots (DeFiPilot, ArbiPilot, LabPilot). Passage progressif vers un cluster DeFi autonome et intelligent.  

•••

**EN :**  
The **DeFiPilot** roadmap is designed for a clear, controlled progression — version by version. Each release introduces a new core feature or major improvement in stability, performance, or autonomy.  

### 🔸 V4.1 — Initial Graphical Interface (GUI)
Adds a simple user interface to visualize pools, scores, and real-time allocations. This version introduces the first dynamic display elements and visual management of investment profiles.  

### 🔸 V4.2 — Strategy Engine and Market Signal Optimization
Improves market context detection and integrates advanced metrics (volatility, APR trends, global TVL). Strengthens the strategy engine and prepares for inter-module communication.  

### 🔸 V4.3 — Full Interface and Monitoring
Deploys a complete GUI with real-time transaction tracking, log visualization, and customizable dashboards. The system will become a true control center for bot activity.  

### 🔸 V4.4 — Development of ControlPilot (AI Supervision)
Creates an intelligent monitoring agent that collects metrics from the bot, market, and wallet. It will generate real-time risk and opportunity signals.  

### 🔸 V4.5 – V5.0 — AI Integration and Multi-Bot Network
Connects DeFiPilot to an AI-driven network of agents capable of analyzing, recommending, and coordinating decisions across multiple bots (DeFiPilot, ArbiPilot, LabPilot). Progressive transition toward an autonomous and intelligent DeFi cluster.  

---

## 🌐 Vision complète du projet / Complete Project Vision

**FR :**  
**DeFiPilot** s’inscrit dans une démarche ouverte et progressive : **apprendre, tester, partager et inspirer**.  
Le projet évolue au sein d’un écosystème plus large comprenant :  
- **ControlPilot** — centre de commande intelligent et agent d’observation IA ;  
- **ArbiPilot** — bot d’arbitrage inter-DEX et inter-chaînes ;  
- **LabPilot** — laboratoire d’expérimentation et d’optimisation IA.  

Cet écosystème vise à créer un **cluster de bots DeFi autonomes**, coopératifs et adaptatifs, capable de gérer plusieurs stratégies simultanément selon les conditions du marché.  
Chaque composant communiquera via une couche d’échange de données sécurisée, orchestrée par **ControlPilot**.  

> 📘 Pour découvrir l’architecture complète, la philosophie et la vision long terme du projet, consultez le document [VISION.md](VISION.md).  

•••

**EN :**  
**DeFiPilot** follows an open and progressive philosophy: **learn, experiment, share, and inspire**.  
The project evolves within a broader ecosystem including:  
- **ControlPilot** — intelligent command center and AI observation agent;  
- **ArbiPilot** — inter-DEX and cross-chain arbitrage bot;  
- **LabPilot** — AI experimentation and optimization lab.  

This ecosystem aims to create an **autonomous cluster of DeFi bots** that are cooperative and adaptive, able to manage multiple strategies simultaneously based on market conditions.  
Each component will communicate through a secure data exchange layer, orchestrated by **ControlPilot**.  

> 📘 For the full architecture, philosophy, and long-term vision of the project, see [VISION.md](VISION.md).  

---
## ❓ FAQ / FAQ

**FR :**  
### 🔹 1. DeFiPilot est-il sûr à utiliser ?
Oui. Toutes les opérations sont validées avant exécution (balances, allowances, statuts des transactions). Le mode **simulation (dry-run)** permet de tout tester sans utiliser de fonds réels.  

### 🔹 2. Peut-on perdre de l’argent ?
En mode simulation : non.  
En mode réel : comme tout investissement DeFi, les risques existent (slippage, baisse de valeur, erreurs de configuration). DeFiPilot minimise ces risques par une vérification stricte des opérations et un suivi complet des logs.  

### 🔹 3. Quelles blockchains sont supportées ?
Actuellement : **Polygon**.  
Les prochaines versions ajouteront la compatibilité multi-chaînes (Avalanche, Fantom, etc.).  

### 🔹 4. Peut-on personnaliser les profils d’investissement ?
Oui. Les profils (prudent, modéré, risqué) peuvent être ajustés via le fichier de configuration JSON pour modifier les pondérations et seuils de rentabilité.  

### 🔹 5. Quelle est la différence entre simulation et mode réel ?
- **Simulation** : aucune transaction réelle, tous les swaps et investissements sont simulés et consignés dans les journaux.  
- **Mode réel** : transactions vérifiées, envoyées et confirmées sur la blockchain.  

•••

**EN :**  
### 🔹 1. Is DeFiPilot safe to use?
Yes. All operations are validated before execution (balances, allowances, transaction status). The **simulation (dry-run)** mode allows testing everything without using real funds.  

### 🔹 2. Can I lose money?
In simulation mode: no.  
In real mode: as with any DeFi investment, risks exist (slippage, token value drops, configuration errors). DeFiPilot minimizes them through strict verification and full transaction logging.  

### 🔹 3. Which blockchains are supported?
Currently: **Polygon**.  
Upcoming versions will add multi-chain compatibility (Avalanche, Fantom, etc.).  

### 🔹 4. Can investment profiles be customized?
Yes. Profiles (prudent, moderate, risky) can be edited via the JSON configuration file to adjust weightings and profitability thresholds.  

### 🔹 5. What’s the difference between simulation and real mode?
- **Simulation**: no real transaction, all swaps and investments are simulated and logged.  
- **Real mode**: transactions are verified, sent, and confirmed on-chain.  

---

## 🧾 À propos / About

**FR :**  
**Auteur :** David RAFFEIL  
**Projet :** DeFiPilot (open source, usage personnel et éducatif)  
**Développé avec :** l’IA **ChatGPT (OpenAI)** pour la rédaction, la structuration et le support technique.  

DeFiPilot est un projet open source non commercial, conçu pour apprendre, expérimenter et documenter l’automatisation des stratégies DeFi. Il n’est pas destiné à un usage institutionnel ou commercial.  

### ⚖️ Licence / License

> #### 🧱 Licence Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)
> 
> **FR :**  
> Ce projet est distribué sous licence **Creative Commons Attribution – Pas d’Utilisation Commerciale 4.0 International (CC BY-NC 4.0)**.  
> Vous êtes libre de partager, modifier et réutiliser le code à condition de :  
> - Mentionner l’auteur original (**David RAFFEIL**) ;  
> - Fournir un lien vers ce dépôt GitHub ;  
> - Ne pas l’utiliser à des fins commerciales ;  
> - Indiquer clairement les modifications apportées.  
>  
> Le projet est fourni **“tel quel”**, sans garantie explicite ni implicite. L’auteur ne saurait être tenu responsable d’éventuelles pertes, erreurs de transaction, ou dommages résultant de l’utilisation du code.  
> 
> **EN :**  
> This project is licensed under the **Creative Commons Attribution – NonCommercial 4.0 International (CC BY-NC 4.0)** license.  
> You are free to share, adapt, and reuse the code provided that you:  
> - Give appropriate credit to the original author (**David RAFFEIL**);  
> - Include a link to this GitHub repository;  
> - Do not use the code for commercial purposes;  
> - Clearly indicate any modifications made.  
>  
> The project is provided **“as is”**, without warranty of any kind. The author assumes no liability for any loss, failed transactions, or damages resulting from its use.  

---

*Développé en France avec passion et curiosité.*  
*Developed in France with passion and curiosity.*  

---