# DeFiPilot

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB?logo=python\&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-stable-brightgreen)]()
![License: Personal Use Only](https://img.shields.io/badge/license-Personal--Use--Only-lightgrey)
[![Built with ChatGPT](https://img.shields.io/badge/built%20with-ChatGPT-10a37f?logo=openai\&logoColor=white)](https://openai.com/chatgpt)
![Made in France](https://img.shields.io/badge/Made%20in-France-blue?logo=france\&logoColor=white)

---

> Bot personnel d’analyse et d’investissement automatisé en DeFi.
> Personal bot for automated analysis and investment in DeFi.

---

## Présentation / About

⚠️ *Actuellement, seule la version française du bot est disponible. L’interface et les logs sont en français uniquement.*
⚠️ *Currently, only the French version of the bot is available. The interface and logs are in French only.*

**DeFiPilot** est un projet open-source (usage non commercial) développé par un autodidacte pour apprendre, expérimenter et automatiser l’investissement sur la finance décentralisée (DeFi), en utilisant Python et l’IA.
**DeFiPilot** is an open-source project (non-commercial use) developed by a self-taught enthusiast to learn, experiment, and automate investment in decentralized finance (DeFi), using Python and AI.

Ce projet évolue en public, étape par étape, avec une démarche transparente, accessible et progressive.
This project evolves publicly, step by step, with a transparent, accessible and progressive approach.

Pour la vision complète de l’écosystème et des futurs bots associés, voir :
For the full vision of the ecosystem and future bots, see:
👉 [VISION.md](https://github.com/DavidRaffeil/DeFiPilot/blob/main/VISION.md)

---

## Nouveautés / What's New

### V2.1 – Simulation complète avec journalisation avancée

* Nouvelle simulation sur 30 jours avec comportement réaliste (test réel simulé)
* Journalisation complète des **gains journaliers simulés**
* Affichage automatique des **TOP 3 pools par jour**
* Application dynamique du **bonus historique**
* **Plafonnement automatique à +20 % de rendement par jour**
* Résumé final affiché (solde, gain total, pool la plus fréquente, bonus moyen)

—

### V2.1 – Full simulation with advanced logging

* New 30-day simulation with realistic behavior (real-mode simulation)
* Full logging of **daily simulated gains**
* Automatic display of **daily TOP 3 pools**
* Dynamic application of **historical bonus**
* **Daily yield capped at +20%** to prevent unrealistic results
* Final summary printed (balance, total gain, most frequent pool, avg bonus)

---

## Fonctionnalités principales / Main features

* Analyse automatique des pools DeFi via DefiLlama
* Simulation d’investissement multi-profils avec score pondéré
* Journalisation détaillée (résultats, historique CSV, log résumé quotidien)
* Interface graphique simple (Tkinter)
* Sélection des meilleures opportunités selon le profil d’investisseur
* Préparation à l’intégration multi-blockchains et de fonctions avancées (voir roadmap)

## Architecture simplifiée DeFiPilot / Simplified architecture

Utilisateur / User
│
▼
Interface graphique (Tkinter) / GUI (Tkinter)
│
▼
Sélection du profil & chargement des paramètres
Profile selection & parameter loading
│
▼
Moteur principal DeFiPilot / Main Engine
│
├─ Récupération des pools via DefiLlama / Pool retrieval via DefiLlama
├─ Calcul des scores & simulation / Score calculation & simulation
├─ Journalisation avancée (logs, CSV) / Advanced logging (logs, CSV)
│
▼
Recommandations à l'utilisateur / User recommendations
│
▼
Historique, fichiers CSV, journal quotidien / History, CSV files, daily log

---

## 🚣️ Roadmap des prochaines versions / Upcoming roadmap

| Version | Contenu prévu / Planned content                                                                                                                        |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `v2.1`  | Journalisation avancée des gains réels, interface sécurisée / Advanced real-yield logging, secured interface                                           |
| `v2.2`  | Gestion des LP tokens + seuils de slippage dynamiques / LP token management + dynamic slippage thresholds                                              |
| `v2.3`  | Mode auto-compounding quotidien + suivi des performances / Daily auto-compounding mode + performance tracking                                          |
| `v2.4`  | Ajout d’un simulateur de gas et estimation des coûts / Gas simulator and cost estimation tool                                                          |
| `v2.5`  | Export complet vers CSV et intégration ControlPilot (centralisation) / Full CSV export + ControlPilot integration (central hub)                        |
| `v2.6+` | Intégration IA avancée avec LabPilot : stratégies adaptatives, auto-réglages / Advanced AI integration with LabPilot: adaptive strategies, auto-tuning |

*La roadmap s’adapte selon l’avancement du projet / The roadmap adapts as the project evolves.*

---

## Installation

1. Cloner ce dépôt :
   `git clone https://github.com/DavidRaffeil/DeFiPilot.git`
   Clone this repository:
   `git clone https://github.com/DavidRaffeil/DeFiPilot.git`

2. Installer les dépendances :
   `pip install -r requirements.txt`
   Install dependencies:
   `pip install -r requirements.txt`

3. Lancer le bot en mode simulation :
   `python main.py`
   Run the bot in simulation mode:
   `python main.py`

---

## Utilisation / Usage

* Lancer `main.py` pour démarrer une analyse et une simulation d’investissement selon le profil choisi (modéré par défaut).
  Run `main.py` to start an analysis and investment simulation based on the selected profile (default is moderate).
* Consulter les logs et fichiers CSV générés pour suivre l’évolution des rendements simulés.
  Check the logs and generated CSV files to track simulated yield performance.

---

## Licence / License

Ce projet est mis à disposition gratuitement pour un usage personnel et non commercial.
This project is made available free of charge for personal and non-commercial use only.

Voir les conditions complètes dans le fichier [License.md](./License.md)
See full terms in the [License.md](./License.md) file

---

## FAQ – Questions fréquentes / Frequently Asked Questions

### Peut-on utiliser DeFiPilot avec un exchange centralisé ?

Can DeFiPilot be used with a centralized exchange?
❌ Non. DeFiPilot est dédié exclusivement à la finance décentralisée. Il ne prend pas en charge les plateformes CeFi.
❌ No. DeFiPilot is strictly focused on decentralized finance and does not support CeFi platforms.

### Est-ce que DeFiPilot fonctionne avec tous les wallets ?

Does DeFiPilot work with all wallets?
🧪 Actuellement, seul un wallet en lecture seule (adresse publique) est utilisé pour la simulation. Les intégrations complètes viendront plus tard.
🧪 Currently, only read-only (public address) wallets are supported for simulation. Full integration will come later.

### Peut-on utiliser DeFiPilot en mode réel ?

Can I use DeFiPilot in real mode?
🔒 Pas encore. À partir de la version 2.0, un mode réel avec montants de test sera disponible. Avant cela, tout est simulation.
🔒 Not yet. From version 2.0, a real mode with test amounts will be available. Until then, everything is simulation only.

### Peut-on personnaliser les critères d’analyse des pools ?

Can pool analysis criteria be customized?
✅ Oui. Le profil choisi (prudent, modéré, agressif…) influence la pondération APR/TVL et la sélection des pools.
✅ Yes. The selected profile (cautious, moderate, aggressive...) influences APR/TVL weighting and pool selection.

### Comment signaler un bug ou une suggestion ?

How to report a bug or suggestion?
💬 Ouvre une "issue" sur GitHub ou contacte le développeur via le dépôt.
💬 Open an issue on GitHub or contact the developer through the repository.

---

## Développeur / Developer

Projet initié et développé par **David Raffeil** avec l’assistance de ChatGPT.
Project initiated and developed by **David Raffeil** with ChatGPT assistance.

---

Pour toute question ou suggestion : issues GitHub ou [voir la vision du projet](https://github.com/DavidRaffeil/DeFiPilot/blob/main/VISION.md)
