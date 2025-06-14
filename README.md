# DeFiPilot

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-stable-brightgreen)]()
![License: Personal Use Only](https://img.shields.io/badge/license-Personal--Use--Only-lightgrey)
[![Built with ChatGPT](https://img.shields.io/badge/built%20with-ChatGPT-10a37f?logo=openai&logoColor=white)](https://openai.com/chatgpt)
![Made in France](https://img.shields.io/badge/Made%20in-France-blue?logo=france&logoColor=white)

---

> Bot personnel d’analyse automatisée de pools DeFi (finance décentralisée, crypto-monnaies) – Projet autodidacte non commercial  
> Personal bot for automated DeFi (decentralized finance, cryptocurrency) pool analysis – Non-commercial self-taught project

⚠️ **FR : Le bot (messages, interface, logs) est pour l’instant uniquement en français.**  
**EN: The bot (messages, interface, logs) is currently available only in French.**

---

## 📌 Présentation / Overview

**FR :**  
DeFiPilot est un bot crypto personnel conçu pour analyser automatiquement les pools de liquidité sur les plateformes DeFi, dans le domaine de la finance décentralisée et des crypto-monnaies.  
Le projet est développé par un autodidacte sans formation technique, à l’aide de l’intelligence artificielle ChatGPT.

**EN :**  
DeFiPilot is a personal crypto bot designed to automatically analyze liquidity pools on DeFi platforms, in the field of decentralized finance and cryptocurrencies.  
It is built by a self-taught developer using ChatGPT AI, with no formal technical background.

---

## 🟦 Vision du projet / Project vision

Ce dépôt fait partie d’un écosystème progressif de bots et d’agents (DeFiPilot, ControlPilot, LabPilot, ArbiPilot…)  
L’objectif est d’apprendre, d’expérimenter et d’automatiser l’analyse et la gestion d’investissements DeFi en toute autonomie, avec une documentation transparente à chaque étape.  
Le projet s’adresse à tous les autodidactes souhaitant progresser dans la crypto, la blockchain, l’automatisation et l’IA – sans élitisme, sans prérequis technique.

> _(EN: This repo is part of a progressive ecosystem of bots and agents (DeFiPilot, ControlPilot, LabPilot, ArbiPilot…). The aim is to learn, experiment and automate DeFi investment analysis and management, documenting every step transparently. The project is for all self-taught people wanting to progress in crypto, blockchain, automation and AI – no elitism, no technical prerequisites.)_

Pour la vision détaillée : [Voir la page dédiée / See dedicated page](https://github.com/DavidRaffeil/DeFiPilot/blob/main/VISION.md)

---

## 🆕 Nouveautés V1.3 / What’s new in V1.3

- Simulateur de wallet (solde virtuel, simulation d’investissements, retraits)
- Journalisation avancée (résultats, rendements simulés, historique CSV, log résumé quotidien)
- Gestion automatique du seuil d’investissement (ajustement intelligent selon le score/risque)
- Préparation à l’intégration de fonctions réelles
- Interface et README enrichis, toujours bilingue

**EN :**
- Wallet simulator (virtual balance, simulated investments and withdrawals)
- Advanced logging (results, simulated returns, CSV history, daily summary log)
- Automatic investment threshold management (smart adjustment based on score/risk)
- Preparing for integration of real features
- Enhanced interface and README, always bilingual

---

## ⚙️ Fonctionnement du bot / How the bot works

**FR :**  
- Scanne automatiquement une liste de pools de liquidité simulées (connexion réelle prévue plus tard)
- Applique des filtres (APR, TVL) et blacklist dynamique
- Calcule un score de rentabilité selon plusieurs critères (rendement, volatilité, durée, risque…)
- Sélectionne les meilleures opportunités selon un profil (prudent, modéré, agressif)
- **Simule des investissements** : gestion de wallet virtuel, investissements/retraits simulés, affichage des gains/pertes estimés à chaque cycle
- **Journalisation avancée** : enregistre l’historique complet (CSV), écrit un log résumé quotidien, traque les erreurs
- Génère des logs détaillés, résumés quotidiens et historiques d’erreurs
- Fonctionne pour l’instant en mode simulation uniquement

**EN :**  
- Automatically scans a list of simulated liquidity pools (real DEX connection planned for the future)
- Applies filters (APR, TVL) and dynamic blacklist
- Calculates a profitability score using several criteria (yield, volatility, duration, risk, etc.)
- Selects best opportunities based on profile (conservative, moderate, aggressive)
- **Simulates investments**: manages a virtual wallet, simulated investments/withdrawals, shows estimated gains/losses each cycle
- **Advanced logging**: saves complete history (CSV), writes daily summary log, tracks errors
- Generates detailed logs, daily summaries, and error history
- Runs in simulation mode only for now

---

## 🚀 Versions disponibles / Available Versions

| Version | Description (FR / EN) | Lien |
|--------|------------------------|------|
| `v1.3` | Simulateur de wallet, rendement simulé, historique des positions, préparation au mode réel / Wallet simulator, simulated yield logging, position history, prep for real mode | [GitHub v1.3](https://github.com/DavidRaffeil/DeFiPilot/releases/tag/v1.3) |
| `v1.2` | Filtres, logs enrichis, blacklist, profils pondérés / Filters, enhanced logs, weighted profiles | [GitHub v1.2](https://github.com/DavidRaffeil/DeFiPilot/releases/tag/v1.2) |
| `v1.1` | Version stable, structure améliorée / Stable version, improved structure | [GitHub v1.1](https://github.com/DavidRaffeil/DeFiPilot/releases/tag/v1.1) |
| `v1.0` | Version de simulation uniquement / Simulation only | [GitHub v1.0](https://github.com/DavidRaffeil/DeFiPilot/releases/tag/v1.0) |

---

## 🛣️ Roadmap des prochaines versions / Upcoming roadmap

| Version | Contenu prévu (FR)                                                            | Planned content (EN)                                                    |
|---------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| `v1.4`  | Interface graphique de base (Tkinter), affichage dynamique des scores et logs | Basic GUI (Tkinter), dynamic score and log display                      |
| `v1.5`  | Mode interactif + possibilité de lancer manuellement ou automatiquement un cycle | Interactive mode + manual or automatic launch                        |
| `v1.6`  | Simulation d’investissement multi-profils + journalisation enrichie           | Multi-profile investment simulation + enriched logging                   |
| `v1.7`  | Connexion réelle à un portefeuille (read-only) + analyse de wallet            | Real wallet connection (read-only) + wallet analysis                     |
| `v1.8`  | Support multi-blockchains (Polygon, Fantom...) + filtres dynamiques           | Multi-chain support (Polygon, Fantom...) + dynamic filters               |
| `v2.0`  | Passage au mode réel (hors simulation) avec montants de test                  | Switch to real (non-simulated) mode with small test funds                |
| `v2.1+` | Ajout d’une IA embarquée, intégration à ControlPilot, décisions autonomes      | Embedded AI, ControlPilot integration, autonomous decisions              |

---

## ✅ Historique des versions précédentes / Previous version history

| Version | Contenu (FR)                                                                                   | Content (EN)                                                                   |
|---------|------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| `v1.3`  | Simulateur de wallet, rendement simulé, historique des positions, préparation au mode réel     | Wallet simulator, simulated yield logging, position history, prep for real mode |
| `v1.2`  | Mode simulation (dryrun) complet, historique CSV, journalisation par cycle, gestion de blacklist | Full dryrun mode, CSV history, per-cycle logging, blacklist management         |
| `v1.1`  | Ajout des profils d’investisseur (prudent, modéré, agressif), tri dynamique                    | Investor profiles added (conservative, moderate, aggressive), dynamic sorting  |
| `v1.0`  | Structure initiale du projet, récupération des pools via DefiLlama, calcul de scores de base   | Initial project structure, pool fetching from DefiLlama, basic score calculation |

---

## 🧠 Intelligence artificielle utilisée / Artificial Intelligence Used

- Génération de code, structuration, corrections et accompagnement assurés par ChatGPT (OpenAI)  
- Code generation, structure and guidance provided by ChatGPT (OpenAI)

---

### 📜 Licence / License

Ce projet est mis à disposition gratuitement pour un usage personnel et non commercial.  
This project is made available free of charge for personal and non-commercial use only.

Voir les conditions complètes dans le fichier [LICENSE.md](./LICENSE.md)  
See full terms in the [LICENSE.md](./LICENSE.md) file
---

## 👤 À propos de l’auteur / About the Author

**FR :**  
Ce projet est né de ma curiosité et de mon envie d’apprendre la programmation, sans aucune formation technique.  
J’ai voulu explorer la blockchain, l’automatisation et l’IA, guidé à chaque étape par ChatGPT.  
J’ai tout construit étape par étape, avec erreurs, essais et persévérance.  
Je partage ce dépôt pour encourager d’autres débutants à oser se lancer, même sans expérience.

**EN :**  
This project was born from my curiosity and my desire to learn programming, starting with no technical background.  
I wanted to explore blockchain, automation, and AI, guided at every step by ChatGPT.  
Everything has been built step by step, through mistakes, experiments, and persistence.  
I share this repository to encourage other beginners to take the leap, even with no prior experience.

---

## 🌱 Message aux débutants / Message for beginners

**FR :**  
Si vous débutez en programmation, en DeFi ou avec l’IA, sachez que ce projet a été lancé sans aucune formation technique !  
N’ayez pas peur de commencer petit, d’apprendre en faisant des erreurs et de demander de l’aide à l’IA.  
La curiosité et la persévérance sont les clés. Lancez-vous !

**EN:**  
If you are a beginner in coding, DeFi, or AI, know that this project was started with zero formal technical background!  
Don’t be afraid to start small, learn from mistakes, and ask for help from AI.  
Curiosity and persistence are what matter most. Just go for it!

---

📫 Merci de votre visite – ce dépôt est aussi là pour inspirer d'autres autodidactes.  
📫 Thanks for visiting – this repository also aims to inspire other self-taught explorers.

---

> **📖 La vision détaillée du projet DeFiPilot et de son écosystème est consultable [ici (VISION.md)](https://github.com/DavidRaffeil/DeFiPilot/blob/main/VISION.md).**
