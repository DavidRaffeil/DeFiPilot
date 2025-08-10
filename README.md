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
👉 [VISION.md](https://github.com/DavidRaffeil/DeFiPilot/blob/main/VISION.md)

---

## Nouveautés / What's New

### 🔹 Version V3.5 – Multi-wallet (2025-08-10)

– Gestion de plusieurs portefeuilles simultanés (lecture seule) pour la simulation.
Multi-wallet support (read-only) for simulation mode.
– Journalisation des connexions/déconnexions dans `logs/journal_wallet_actions.csv`.
Logging of wallet connections/disconnections in `logs/journal_wallet_actions.csv`.

---

## 🚀 Roadmap des prochaines versions / Upcoming roadmap

| Version | Contenu prévu / Planned content                                                                                                                                                           |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `v3.6`  | Compatibilité multi-blockchains (Polygon, Avalanche, Fantom…) / Multi-chain compatibility (Polygon, Avalanche, Fantom…)                                                                   |
| `v3.7`  | Swap réel sur DEX Polygon : gestion du slippage, confirmation avant exécution / Real swap on Polygon DEX: slippage handling, pre-execution confirmation                                   |
| `v3.8`  | Ajout de liquidité réelle sur DEX, réception de LP tokens / Real liquidity provision on DEX, LP token handling                                                                            |
| `v3.9`  | Farming LP réel : staking des LP tokens et récolte auto des récompenses / Real LP farming: staking and auto reward collection                                                             |
| `v4.0`  | Mode réel complet : stratégie automatisée, retraits si non rentable, reprise après coupure / Full real mode: automated strategy, auto-withdraw if unprofitable, resume after interruption |

*La roadmap s’adapte selon l’avancement du projet / The roadmap adapts as the project evolves.*

---

## Fonctionnalités principales / Main features

* Analyse automatique des pools DeFi via DefiLlama
* Simulation d’investissement multi-profils avec score pondéré
* Journalisation détaillée (résultats, historique CSV, log résumé quotidien)
* Interface graphique simple (Tkinter)
* Sélection des meilleures opportunités selon le profil d’investisseur
* Préparation à l’intégration multi-blockchains et de fonctions avancées (voir roadmap)

---

## Installation

1. Cloner ce dépôt :

   ```bash
   ```

git clone [https://github.com/DavidRaffeil/DeFiPilot.git](https://github.com/DavidRaffeil/DeFiPilot.git)

````
   Clone this repository:
   ```bash
git clone https://github.com/DavidRaffeil/DeFiPilot.git
````

2. Installer les dépendances :

   ```bash
   ```

pip install -r requirements.txt

````
   Install dependencies:
   ```bash
pip install -r requirements.txt
````

3. Lancer le bot en mode simulation :

   ```bash
   ```

python main.py

````
   Run the bot in simulation mode:
   ```bash
python main.py
````

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

❌ Non. DeFiPilot est dédié exclusivement à la finance décentralisée. Il ne prend pas en charge les plateformes CeFi.
❌ No. DeFiPilot is strictly focused on decentralized finance and does not support CeFi platforms.

### Est-ce que DeFiPilot fonctionne avec tous les wallets ?

🧪 Actuellement, seul un wallet en lecture seule (adresse publique) est utilisé pour la simulation. Les intégrations complètes viendront plus tard.
🧪 Currently, only read-only (public address) wallets are supported for simulation. Full integration will come later.

### Peut-on utiliser DeFiPilot en mode réel ?

🔒 Pas encore. À partir de la version 4.0, le mode réel complet sera disponible. Avant cela, tout est simulation.
🔒 Not yet. From version 4.0, the full real mode will be available. Until then, everything is simulation only.

### Peut-on personnaliser les critères d’analyse des pools ?

✅ Oui. Le profil choisi (prudent, modéré, agressif…) influence la pondération APR/TVL et la sélection des pools.
✅ Yes. The selected profile (cautious, moderate, aggressive...) influences APR/TVL weighting and pool selection.

### Comment signaler un bug ou une suggestion ?

💬 Ouvre une "issue" sur GitHub ou contacte le développeur via le dépôt.
💬 Open an issue on GitHub or contact the developer through the repository.

---

## Développeur / Developer

Projet initié et développé par **David Raffeil** avec l’assistance de ChatGPT.
Project initiated and developed by **David Raffeil** with ChatGPT assistance.

Pour toute question ou suggestion : issues GitHub ou [voir la vision du projet](https://github.com/DavidRaffeil/DeFiPilot/blob/main/VISION.md)
