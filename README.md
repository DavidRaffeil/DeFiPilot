o# DeFiPilot

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-stable-brightgreen)]()
![License: Personal Use Only](https://img.shields.io/badge/license-Personal--Use--Only-lightgrey)
[![Built with ChatGPT](https://img.shields.io/badge/built%20with-ChatGPT-10a37f?logo=openai&logoColor=white)](https://openai.com/chatgpt)
![Made in France](https://img.shields.io/badge/Made%20in-France-blue?logo=france&logoColor=white)

---

> Bot personnel d’analyse et d’investissement automatisé en DeFi.  
> Personal bot for automated analysis and investment in DeFi.

---

## Présentation / About

**DeFiPilot** est un projet open-source (usage non commercial) développé par un autodidacte pour apprendre, expérimenter et automatiser l’investissement sur la finance décentralisée (DeFi), en utilisant Python et l’IA.  
**DeFiPilot** is an open-source project (non-commercial use) developed by a self-taught enthusiast to learn, experiment, and automate investment in decentralized finance (DeFi), using Python and AI.

Ce projet évolue en public, étape par étape, avec une démarche transparente, accessible et progressive.  
This project evolves publicly, step by step, with a transparent, accessible and progressive approach.

Pour la vision complète de l’écosystème et des futurs bots associés, voir :  
For the full vision of the ecosystem and future bots, see:  
👉 [VISION.md](https://github.com/DavidRaffeil/DeFiPilot/blob/main/VISION.md)

---

## Nouveautés V1.4 / What's new in V1.4

- Simulation d’investissement multi-profils (prudent, modéré, agressif…)
- Journalisation enrichie : résultats, rendements simulés, historique CSV, résumé par jour
- Interface améliorée pour la sélection et l’affichage des profils d’investissement
- Roadmap et README mis à jour (toujours bilingue, sans drapeau)
- Préparation des prochaines étapes (connexion wallet test, analyse de wallet…)

---

## Fonctionnalités principales / Main features

- Analyse automatique des pools DeFi via DefiLlama
- Simulation d’investissement multi-profils avec score pondéré
- Journalisation détaillée (résultats, historique CSV, log résumé quotidien)
- Interface graphique simple (Tkinter)
- Sélection des meilleures opportunités selon le profil d’investisseur
- Préparation à l’intégration multi-blockchains et de fonctions avancées (voir roadmap)

## Architecture simplifiée DeFiPilot

Utilisateur  
   │  
   ▼  
Interface graphique (Tkinter)  
   │  
   ▼  
Sélection du profil & chargement des paramètres  
   │  
   ▼  
Moteur principal DeFiPilot  
   │  
   ├─ Récupération des pools via DefiLlama  
   ├─ Calcul des scores & simulation  
   ├─ Journalisation avancée (logs, CSV)  
   │  
   ▼  
Recommandations à l'utilisateur  
   │  
   ▼  
Historique, fichiers CSV, journal quotidien


---

## 🛣️ Roadmap des prochaines versions / Upcoming roadmap

| Version | FR : Contenu prévu | EN: Planned content |
|---------|--------------------|---------------------|
| `v1.4`  | Simulation d’investissement multi-profils + journalisation enrichie | Multi-profile investment simulation + enriched logging |
| `v1.5`  | Connexion réelle à un portefeuille test (lecture seule) + analyse de wallet | Real test wallet connection (read-only) + wallet analysis |
| `v1.6`  | Support multi-blockchains (Polygon, Fantom...) + filtres dynamiques | Multi-chain support (Polygon, Fantom...) + dynamic filters |
| `v2.0`  | Passage au mode réel (hors simulation) avec montants de test | Switch to real (non-simulated) mode with small test funds |
| `v2.1+` | Ajout d’une IA embarquée, intégration ArbiPilot/LabPilot, amélioration continue | Embedded AI, ArbiPilot/LabPilot integration, continuous improvements |

*La roadmap s’adapte selon l’avancement du projet / The roadmap adapts as the project evolves.*

---

## Installation

### FR  
1. Cloner ce dépôt :  
   `git clone https://github.com/DavidRaffeil/DeFiPilot.git`  
2. Installer les dépendances :  
   `pip install -r requirements.txt`  
3. Lancer le bot en mode simulation :  
   `python main.py`  

### EN  
1. Clone this repository:  
   `git clone https://github.com/DavidRaffeil/DeFiPilot.git`  
2. Install dependencies:  
   `pip install -r requirements.txt`  
3. Run the bot in simulation mode:  
   `python main.py`  

---

## Utilisation / Usage

- Lancer `main.py` pour démarrer une analyse et une simulation d’investissement selon le profil choisi (modéré par défaut).
- Consulter les logs et fichiers CSV générés pour suivre l’évolution des rendements simulés.

---

### 📜 Licence / License

Ce projet est mis à disposition gratuitement pour un usage personnel et non commercial.  
This project is made available free of charge for personal and non-commercial use only.
=======
## Licence / License

Ce projet est mis à disposition gratuitement pour un usage personnel et non commercial.
This project is made available free of charge for personal and non-commercial use only.

Voir les conditions complètes dans le fichier License.md
See full terms in the License.md file
(docs: mise à jour README pour V1.4)

Voir les conditions complètes dans le fichier [License.md](./License.md)  
See full terms in the [License.md](./License.md) file
---

## Développeur / Developer

Projet initié et développé par **David Raffeil** (France) avec l’assistance de ChatGPT.  
Project initiated and developed by **David Raffeil** (France) with ChatGPT assistance.

---

Pour toute question ou suggestion : issues GitHub ou [voir la vision du projet](https://github.com/DavidRaffeil/DeFiPilot/blob/main/VISION.md)

---
