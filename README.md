🗣️ Langue / Language : le bot fonctionne uniquement en français pour le moment.

The bot currently works in French only for the moment.

📚 Sommaire / Table of Contents
Introduction / Introduction

Fonctionnalités principales / Key Features

Aperçu visuel / Visual Overview

Nouveautés / What's New — Version 6.1

Historique des versions / Past Versions

Caractéristiques techniques / Technical Highlights

Prérequis / Requirements

Installation / Installation

Utilisation / Usage

Feuille de route / Roadmap

Vision du projet / Project Vision

FAQ / Foire aux questions

À propos de l’auteur / About the Author

Crédits techniques / Technical Credits

Licence / License

Dernière révision / Last Review

1. 🧭 Introduction / Introduction
FR
DeFiPilot est un bot DeFi autonome conçu pour analyser en continu les opportunités disponibles sur les échanges décentralisés (DEX), calculer la rentabilité réelle des pools, puis sélectionner les meilleures options en fonction d’un profil d’investissement configurable. Le système fonctionne aussi bien en mode simulation qu’en mode réel selon la configuration utilisateur.

Son architecture repose sur quatre principes :

Robustesse : tolérance aux erreurs réseau, redondances, vérifications multiples.

Modularité : possibilité d’étendre facilement les fonctionnalités via modules.

Transparence : journalisation complète (CSV + JSONL), état sauvegardé, historique visible.

Automatisation : analyse continue, décisions guidées par les profils, reprise automatique.

DeFiPilot vise à constituer une base sérieuse et pérenne pour gérer des investissements DeFi automatisés, tout en intégrant des mécanismes de sécurité pour réduire les risques opérationnels.

EN
DeFiPilot is an autonomous DeFi bot designed to continuously analyze opportunities across decentralized exchanges (DEX), compute real profitability for liquidity pools, and select the best options according to a configurable investment profile. The system runs in both simulation and real execution modes depending on user configuration.

Its architecture relies on four core principles:

Robustness: tolerance to network failures, redundancy, multiple safety checks.

Modularity: easily extendable through additional modules.

Transparency: full logging (CSV + JSONL), state storage, visible history.

Automation: continuous analysis, profile‑driven decisions, automatic state recovery.

DeFiPilot aims to be a serious and sustainable foundation for automated DeFi investment management while embedding safety mechanisms to minimize operational risks.

2. ⚙️ Fonctionnalités principales / Key Features
FR
Analyse automatique des pools (APR, TVL, volume, volatilité, slippage).

Scoring pondéré basé sur plusieurs profils (Prudent, Modéré, Risque).

Mode simulation complet avec garde-fou (Dry-Run Guard) pour tests sécurisés sans risque.

Mode réel avec gestion du slippage, limites, confirmations.

Interface graphique Tkinter avec rafraîchissement automatique.

Multi-wallets avec séparation des usages.

Supervision IA via ControlPilot (signaux contextuels).

Résilience et reprise automatique après coupure (fichiers state.json et health.json).

Journalisation détaillée (JSONL + CSV).

Architecture modulaire extensible.

EN
Automatic pool analysis (APR, TVL, volume, volatility, slippage).

Weighted scoring based on multiple profiles (Conservative, Moderate, Risk).

Full simulation mode with safety guard (Dry-Run Guard) for zero-risk testing.

Real mode with slippage management, limits, confirmations.

Tkinter GUI with automatic refresh.

Multi‑wallet support.

AI supervision via ControlPilot (context signals).

System resilience and automatic resume after shutdown (state.json and health.json).

Detailed logging (JSONL + CSV).

Modular and extensible architecture.

3. 🖥️ Aperçu visuel / Visual Overview
FR
L’interface graphique de DeFiPilot présente les métriques clés, l’état du bot, les signaux AI de ControlPilot, la liste des pools analysées, et les indicateurs de stratégie actifs.

EN
DeFiPilot’s graphical interface displays key metrics, bot status, ControlPilot AI signals, list of analyzed pools, and active strategy indicators.

4. 🆕 Nouveautés / What's New — Version 6.1
📘 Fr
Mode Dry-Run sécurisé : Implémentation du DryRunGuard garantissant zéro interaction blockchain réelle en mode simulation.

Scoring & Décisions : Algorithme de scoring de rééquilibrage affiné et directement couplé aux flux de décision.

Résilience système : Gestion de l'état de santé globale via system_health.py et journalisation dans data/health.json avec auto-récupération.

Suite de tests E2E complète : Validation totale de la chaîne de décision et des garde-fous avec 29 tests d'intégration au vert.

📗 En
Secured Dry-Run Mode: Implementation of DryRunGuard ensuring zero real blockchain interactions during simulation runs.

Scoring & Decision Logic: Refined rebalancing scoring engine tightly coupled with execution decision workflows.

System Resilience: Health state management via system_health.py and persistent tracking in data/health.json with auto-recovery features.

Complete E2E Test Suite: Full validation of the decision pipeline and safety mechanics with 29 passing integration tests.

5. 🕓 Historique des versions / Past Versions
📘 Fr
V6.1 : Moteur de simulation sécurisé (Dry-Run Guard), algorithme de scoring fiabilisé, gestion de résilience système (system_health.py) et validation complète par tests E2E (29 tests au vert).

V6.0 : Refonte Core V6, scoring des pools, daemon de journalisation de stratégie sécurisé, refonte de la couche d'exécution réelle et nettoyage legacy.

V5.5 : Exits automatiques basés sur le contexte, application des seuils Deep Search V5.4, stratégie finalisée (strategy_v5_5.json), stabilisation complète du daemon.

V5.3 : Journal stratégique dédié (journal_strategy.jsonl), intégration complète des signaux normalisés de ControlPilot, stabilisation du daemon.

V5.2 : Rééquilibrage automatique du portefeuille, signaux pondérés, snapshots de rééquilibrage, mise à jour scoring/stratégie.

V5.1 : Nouveau moteur de signaux IA, normalisation avancée, scoring dynamique, stratégie enrichie.

V5.0 : Intégration IA ControlPilot, stabilité renforcée, dashboard optimisé.

V4.9 : Agrégation avancée des signaux + détection d’anomalies.

V4.8 : Collecte des signaux simples (début ControlPilot).

V4.7 : Stabilisation complète du mode réel + reprise automatique.

V4.6 : Stratégie dynamique avec ajustements automatiques.

V4.5 : Améliorations GUI + affichage contextuel.

V4.4 : Lancement global + supervision initiale.

V4.3 : Simulation LP + journalisation complète.

V4.2 : Scoring pondéré + gestion des profils.

V4.0 : Passage au simulateur complet.

📗 En
V6.1: Secured dry-run simulation mode (Dry-Run Guard), refined scoring algorithm, system health resilience (system_health.py), and full validation with 29 E2E integration tests.

V6.0: Core V6 refactoring, pool scoring engine, secure strategy logging daemon, execution layer fixes and workspace reorganization.

V5.5: Automatic exits based on market context, integration of Deep Search V5.4 thresholds, finalized strategy file (strategy_v5_5.json), full daemon stabilization.

V5.3: Dedicated strategic journal (journal_strategy.jsonl), full ControlPilot signal integration.

V5.2: Automatic portfolio rebalancing, weighted signals, snapshots, and stabilized pipeline.

V5.1: New AI signal engine, dynamic scoring, enriched strategy.

V5.0: ControlPilot integration + real-mode stabilization.

6. 🧱 Caractéristiques techniques / Technical Highlights
FR
DeFiPilot repose sur une architecture modulaire, pensée pour garantir évolutivité et stabilité :

main_v6_core.py / run_defipilot_v6.py — Points d'entrée principaux du moteur V6.

core/ — Analyse, scoring des pools, garde-fous (guardrails.py, dry_run_guard.py), suivi de santé système (system_health.py), validation d'environnement (env_validator.py), CLI (cli.py), exécution réelle des transactions (execution/).

config/ — Configurations stratégiques (strategy_v6_0.json, strategy_v5_5.json), paramètres généraux.

journal_daemon_v6_secure.py / analyser_logs.py — Daemon de suivi de stratégie et utilitaire d'analyse des journaux.

tests/ — Suite de tests automatisés couvrant les simulations E2E, le scoring, la résilience et la sécurité du mode dry-run.

data/ — État persistant du bot (state.json, health.json).

Le bot utilise principalement Python 3.11, Web3.py, Tkinter, Pandas, et l’API DefiLlama.

EN
DeFiPilot is built on a modular architecture designed for scalability and stability:

main_v6_core.py / run_defipilot_v6.py — Core entry points for the V6 engine execution.

core/ — Analysis, pool scoring, safety guards (guardrails.py, dry_run_guard.py), system health management (system_health.py), environment validation (env_validator.py), CLI (cli.py), real-world execution scripts (execution/).

config/ — Strategic configurations (strategy_v6_0.json, strategy_v5_5.json), global parameters.

journal_daemon_v6_secure.py / analyser_logs.py — Secure background strategy daemon and log analytics tool.

tests/ — Automated test suite covering E2E simulations, scoring, resilience, and dry-run safety.

data/ — State persistence engine (state.json, health.json).

The bot relies mainly on Python 3.11, Web3.py, Tkinter, Pandas, and the DefiLlama API.

7. 🔧 Prérequis / Requirements
FR
Python 3.11+

Accès RPC Polygon (Infura, Alchemy, QuickNode)

Wallet compatible (Rabby, MetaMask)

Connexion Internet stable

Git installé

EN
Python 3.11+

Polygon RPC access (Infura, Alchemy, QuickNode)

Compatible wallet (Rabby, MetaMask)

Stable Internet connection

Git installed

8. ⚙️ Installation / Installation
FR
Cloner le dépôt :
git clone https://github.com/DavidRaffeil/DeFiPilot.git
cd DeFiPilot

Créer l’environnement virtuel et installer les dépendances :
python3.11 -m venv .venv
source .venv/bin/activate  # Windows : .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt

Configurer le fichier .env :
NETWORK=polygon
RPC_URL=https://polygon-mainnet.infura.io/v3/<PROJECT_ID>
WALLET_ADDRESS=<VOTRE_ADRESSE_WALLET> # remplacer par votre adresse
LOG_LEVEL=INFO

Vérifier l’installation :
python check_setup.py

EN
Clone the repository:
git clone https://github.com/DavidRaffeil/DeFiPilot.git
cd DeFiPilot

Create a virtual environment and install dependencies:
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt

Configure the .env file:
NETWORK=polygon
RPC_URL=https://polygon-mainnet.infura.io/v3/<PROJECT_ID>
WALLET_ADDRESS=<YOUR_WALLET_ADDRESS> # replace with your address
LOG_LEVEL=INFO

Verify installation:
python check_setup.py

9. ▶️ Utilisation / Usage
FR
Lancement V6 Core (Mode principal) :
python run_defipilot_v6.py

Exécution des tests d'intégration et de sécurité :
pytest

Lancement du Daemon de Journalisation Sécurisé :
python journal_daemon_v6_secure.py

Analyse des journaux d'exécution :
python analyser_logs.py

EN
Launch V6 Core Engine (Main mode):
python run_defipilot_v6.py

Run integration and safety tests:
pytest

Launch Secure Background Logging Daemon:
python journal_daemon_v6_secure.py

Analyze execution logs:
python analyser_logs.py

10. 🚀 Feuille de route / Roadmap
📘 Fr
Prochaines versions
V6.2 : Synchronisation multi-bots (DeFiPilot + ControlPilot + ArbiPilot).

V6.3 : Déploiement sur Orange Pi / infrastructure SBC.

Versions finalisées
V6.1 : Simulation sécurisée (Dry-Run Guard), scoring de rééquilibrage, gestion de santé système et suite de 29 tests E2E.

V6.0 : Mode unifié V6 Core, scoring des pools, daemon de journalisation sécurisé, réorganisation du dépôt.

V5.5 : Exits automatiques, intégration des seuils Deep Search, stratégie finalisée strategy_v5_5.json, stabilisation du daemon.

V5.3 : Journal stratégique dédié (journal_strategy.jsonl), intégration complète des signaux ControlPilot.

V5.2 : Rééquilibrage automatique, signaux pondérés, snapshots et pipeline stabilisé.

V5.1 : Nouveau moteur de signaux IA, scoring dynamique et stratégie enrichie.

V5.0 : Intégration ControlPilot + stabilisation mode réel.

📗 En
Upcoming Versions
V6.2: Multi-bot synchronization (DeFiPilot + ControlPilot + ArbiPilot).

V6.3: Deployment on Orange Pi / SBC architecture.

Completed Versions
V6.1: Secured dry-run simulation, rebalancing scoring, system health resilience, and 29 E2E test suite.

V6.0: Unified V6 Core mode, pool scoring engine, secure background logging daemon, codebase cleanup.

V5.5: Automatic exits, Deep Search threshold integration, finalized strategy_v5_5.json, full daemon stabilization.

V5.3: Dedicated strategic journal (journal_strategy.jsonl), full ControlPilot signal integration.

V5.2: Automatic rebalancing, weighted signals, snapshots, and stabilized pipeline.

V5.1: New AI signal engine, dynamic scoring, enriched strategy.

V5.0: ControlPilot integration + real-mode stabilization.

11. 🌍 Vision du projet / Project Vision
FR
DeFiPilot vise à devenir une plateforme de gestion automatisée complète regroupant :

Analyse multi‑DEX, multi‑blockchains.

Stratégies dynamiques ajustées selon le marché.

Modules complémentaires (ControlPilot, ArbiPilot, LabPilot).

Architecture transparente et robuste centrée sur la sécurité et la pédagogie.

EN
DeFiPilot aims to evolve into a complete automated management platform including:

Multi‑DEX, multi‑chain analysis.

Dynamic strategies adjusted to market conditions.

Complementary modules (ControlPilot, ArbiPilot, LabPilot).

Transparent and robust architecture focused on safety and clarity.

12. ❓ Foire aux questions / FAQ
FR
1. DeFiPilot effectue‑t‑il des transactions automatiquement ?

Oui, si le mode réel est activé et correctement configuré. En mode simulation, aucune transaction blockchain n’est envoyée grâce au garde-fou DryRunGuard.

2. Puis‑je utiliser DeFiPilot sans interface graphique ?

Oui, le bot fonctionne en ligne de commande de façon optimale avec run_defipilot_v6.py.

3. Quels réseaux sont supportés ?

Polygon est supporté en natif. D’autres blockchains seront ajoutées progressivement.

4. Les clés privées sont‑elles stockées en clair ?

Elles sont chargées via .env et jamais écrites dans les journaux.

5. Quelle est la fréquence d’analyse ?

Elle dépend de la configuration, généralement quelques secondes.

6. Comment fonctionne la reprise automatique ?

L’état est stocké dans le dossier data/ (state.json et health.json), permettant au bot de reprendre après une coupure.

7. Comment fonctionne la supervision IA ?

ControlPilot fournit des signaux contextuels (favorable, neutre, défavorable) influençant la stratégie.

8. Les données de marché proviennent d’où ?

Principalement de DefiLlama et des RPC blockchain.

9. Puis‑je ajouter mes propres stratégies ?

Oui, l’architecture modulaire permet d’étendre facilement les stratégies via le dossier config/.

10. Le projet est‑il open source ?

Oui, sous licence CC‑BY‑NC‑SA 4.0.

EN
1. Does DeFiPilot perform transactions automatically?

Yes, if real mode is enabled and properly configured. In simulation mode, no blockchain transactions are sent thanks to the DryRunGuard safety layer.

2. Can I run DeFiPilot without the GUI?

Yes, the bot runs efficiently via CLI using run_defipilot_v6.py.

3. Which networks are supported?

Polygon is supported natively; other networks will be added later.

4. Are private keys stored in plain text?

They are loaded via .env and never written to logs.

5. What is the analysis frequency?

It depends on configuration, usually a few seconds.

6. How does auto‑resume work?

Bot state is stored in data/ (state.json and health.json), allowing recovery after a shutdown.

7. How does AI supervision work?

ControlPilot provides contextual signals (favorable, neutral, unfavorable) affecting strategy.

8. Where does market data come from?

Mainly from DefiLlama and blockchain RPC endpoints.

9. Can I add my own strategies?

Yes, the modular architecture supports custom strategy configurations in config/.

10. Is the project open source?

Yes, licensed under CC‑BY‑NC‑SA 4.0.

13. 👤 À propos de l’auteur / About the Author
📘 Fr
David Raffeil est un passionné d’automatisation, de finance décentralisée et d’ingénierie logicielle appliquée.

Il développe DeFiPilot depuis 2023 avec l’objectif de construire un écosystème complet et pédagogique autour de la DeFi, accessible aux utilisateurs motivés mais non spécialistes du développement.

Issu d’un parcours autodidacte, il a progressivement acquis des compétences en :

architecture logicielle (Python 3.11, modules multi-couches)

analyse on-chain et extraction de signaux DeFi

automatisation, gestion d’état et reprise après coupure

intégration Web3 et interactions blockchain sécurisées

conception d’interfaces graphiques (Tkinter)

structuration de journaux avancés (CSV/JSONL)

méthodologie Git (branches, versions, tags, releases)

Son approche se caractérise par :

un souci permanent de fiabilité

une obsession de la transparence

une volonté d’apprendre en construisant

un usage pragmatique de l’IA (Antigravity avec Gemini et ChatGPT) comme copilotes de développement

DeFiPilot est conçu comme un projet de long terme :

une plateforme modulaire, extensible, méthodologiquement propre, pouvant évoluer vers un cluster multi-bots (DeFiPilot, ControlPilot, ArbiPilot, LabPilot).

David souhaite également partager son expérience pour inspirer d’autres autodidactes à se lancer dans des projets techniques ambitieux, même en partant de zéro.

📗 En
David Raffeil is an enthusiast of automation, decentralized finance and applied software engineering.

He has been developing DeFiPilot since 2023 with the goal of building a complete and educational DeFi ecosystem, accessible to motivated users—even those without a technical background.

Coming from a fully self-taught path, he progressively developed skills in:

software architecture (Python 3.11, multi-layer modules)

on-chain analysis and DeFi signal extraction

automation, state management and crash-safe recovery

Web3 integration and secure blockchain interactions

graphical interface design (Tkinter)

advanced logging systems (CSV/JSONL)

Git methodology (branches, versions, tags, releases)

His approach is guided by:

a constant focus on reliability

strong commitment to transparency

learning by building real projects

pragmatic use of AI (Antigravity with Gemini and ChatGPT) as development copilots

DeFiPilot is intended as a long-term project:

a modular, scalable platform that will evolve into a multi-bot cluster (DeFiPilot, ControlPilot, ArbiPilot, LabPilot).

David also hopes to share his journey to inspire other self-taught developers to tackle ambitious technical projects, even starting from scratch.

14. 🧩 Crédits techniques / Technical Credits
FR
Développement assisté par Antigravity & Gemini et ChatGPT.

Icônes, badges et éléments visuels issus de ressources libres.

Utilisation de Web3.py, Tkinter, Pandas, DefiLlama API.

EN
Development assisted by Antigravity & Gemini and ChatGPT.

Icons, badges and visuals use open free resources.

Built on Web3.py, Tkinter, Pandas, DefiLlama API.

15. 📜 Licence / License
📘 Fr — Licence d’utilisation
DeFiPilot est distribué sous une licence d’utilisation personnelle et non commerciale, sauf accord formel avec l’auteur.

Vous êtes autorisé à :

utiliser le logiciel pour un usage strictement personnel ;

modifier le code pour vos propres besoins ;

étudier et analyser le fonctionnement du projet ;

exécuter le logiciel en mode simulation ou réel sous votre propre responsabilité.

Vous n’êtes pas autorisé à :

utiliser le logiciel dans un cadre commercial, professionnel ou lucratif sans un contrat écrit signé avec l’auteur (David Raffeil) ;

vendre, louer, héberger ou distribuer une version modifiée ou non modifiée à des fins commerciales ;

intégrer tout ou partie du projet dans un produit ou service commercial sans accord contractuel.

Toute redistribution non commerciale doit :

créditer clairement l’auteur original (David Raffeil) ;

inclure un lien vers le dépôt GitHub d’origine ;

mentionner les éventuelles modifications.

🛡️ Clause de non-responsabilité
Le logiciel est fourni “tel quel”, sans garantie d’exactitude, de performance ou de sécurité.

L’auteur ne peut être tenu responsable :

de pertes financières directes ou indirectes ;

d’une mauvaise configuration ou d'un usage inadapté ;

d’erreurs liées à la blockchain ou à des RPC tiers ;

de comportements inattendus dus à des smart contracts externes ;

d’une utilisation non conforme aux recommandations.

L’utilisateur reconnaît utiliser DeFiPilot à ses propres risques, en comprenant les risques inherents à la DeFi et aux interactions on-chain.

📗 En — Usage License
DeFiPilot is distributed under a personal and non-commercial use license, unless a formal agreement is signed with the author.

You are allowed to:

use the software for personal use only;

modify the code for your own needs;

study and analyze the project;

run the software in simulation or real mode at your own risk.

You are not allowed to:

use the software in any commercial, professional, or profit-oriented context without a written contract signed with the author (David Raffeil);

sell, rent, host, or distribute modified or unmodified versions for commercial purposes;

integrate any part of the project into a commercial product or service without contractual approval.

Any non-commercial redistribution must:

clearly credit the original author (David Raffeil) ;

include a link to the original GitHub repository ;

state any modifications made.

🛡️ Disclaimer
This software is provided “as is”, without any warranty of accuracy, performance, or safety.

The author cannot be held responsible for:

direct or indirect financial losses ;

misconfiguration or improper usage ;

blockchain or third-party RPC failures ;

unexpected behavior due to external smart contracts ;

any use that does not follow the recommendations.

The user acknowledges that they use DeFiPilot at their own risk, understanding the inherent risks of DeFi and on-chain operations.

16. 🔍 Dernière révision / Last Review
README V6.1 — mis à jour et consolidé.

README V6.1 — updated and consolidated.

© 2023-2026 DeFiPilot — Tous droits réservés.

Projet distribué sous licence CC-BY-NC-SA 4.0.

© 2023-2026 DeFiPilot — All rights reserved.

Project distributed under the CC-BY-NC-SA 4.0 licens
