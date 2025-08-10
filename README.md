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

### 🔹 Version V3.6 – Wallet réel (2025-08-10)

* **FR :** Ajout du wallet réel `core/real_wallet.py` (Polygon RPC), gestion multi-wallets via `wallets_manager`, journalisation `wallet_connect` / `wallet_disconnect`, et signature de message.
* **EN :** Added real wallet `core/real_wallet.py` (Polygon RPC), basic multi-wallet via `wallets_manager`, `wallet_connect` / `wallet_disconnect` logging, and message signing.

---

## 🚀 Roadmap des prochaines versions / Upcoming roadmap

| Version | Contenu prévu / Planned content                                                                                                                                                                                   |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `v3.7`  | **FR :** Swap réel sur DEX Polygon : gestion du slippage, confirmation avant exécution.  <br> **EN :** Real swap on Polygon DEX: slippage handling, pre-execution confirmation.                                   |
| `v3.8`  | **FR :** Ajout de liquidité réelle sur DEX, réception de LP tokens.  <br> **EN :** Real liquidity provision on DEX, LP token handling.                                                                            |
| `v3.9`  | **FR :** Farming LP réel : staking des LP tokens et récolte auto des récompenses.  <br> **EN :** Real LP farming: staking and auto reward collection.                                                             |
| `v4.0`  | **FR :** Mode réel complet : stratégie automatisée, retraits si non rentable, reprise après coupure.  <br> **EN :** Full real mode: automated strategy, auto-withdraw if unprofitable, resume after interruption. |

*La roadmap s’adapte selon l’avancement du projet.*
*The roadmap adapts as the project evolves.*

---

## Fonctionnalités principales / Main features

* **FR :** Analyse automatique des pools DeFi via DefiLlama.
  **EN :** Automatic analysis of DeFi pools via DefiLlama.
* **FR :** Simulation d’investissement multi-profils avec score pondéré.
  **EN :** Multi-profile investment simulation with weighted score.
* **FR :** Journalisation détaillée (résultats, historique CSV, log résumé quotidien).
  **EN :** Detailed logging (results, CSV history, daily summary log).
* **FR :** Interface graphique simple (Tkinter).
  **EN :** Simple graphical interface (Tkinter).
* **FR :** Sélection des meilleures opportunités selon le profil d’investisseur.
  **EN :** Selection of best opportunities according to investor profile.
* **FR :** Préparation à l’intégration multi-blockchains et de fonctions avancées (voir roadmap).
  **EN :** Preparation for multi-chain integration and advanced features (see roadmap).

---

## Installation

1. **Cloner ce dépôt :**

```bash
git clone https://github.com/DavidRaffeil/DeFiPilot.git
```

2. **Installer les dépendances :**

```bash
pip install -r requirements.txt
```

3. **Lancer le bot en mode simulation :**

```bash
python main.py
```

---

## Utilisation / Usage

* **FR :** Lancer `main.py` pour démarrer une analyse et une simulation d’investissement selon le profil choisi (modéré par défaut).
  **EN :** Run `main.py` to start an analysis and investment simulation based on the selected profile (default is moderate).
* **FR :** Consulter les logs et fichiers CSV générés pour suivre l’évolution des rendements simulés.
  **EN :** Check logs and generated CSV files to track simulated yield performance.

---

## Licence / License

**FR :** Ce projet est mis à disposition gratuitement pour un usage personnel et non commercial.
**EN :** This project is made available free of charge for personal and non-commercial use only.

Voir les conditions complètes dans le fichier [License.md](./License.md)
See full terms in the [License.md](./License.md) file.

---

## FAQ – Questions fréquentes / Frequently Asked Questions

### Peut-on utiliser DeFiPilot avec un exchange centralisé ?

* **FR :** ❌ Non. DeFiPilot est dédié exclusivement à la finance décentralisée. Il ne prend pas en charge les plateformes CeFi.
* **EN :** ❌ No. DeFiPilot is strictly focused on decentralized finance and does not support CeFi platforms.

### Est-ce que DeFiPilot fonctionne avec tous les wallets ?

* **FR :** 🧪 Actuellement, seul un wallet en lecture seule (adresse publique) est utilisé pour la simulation. Les intégrations complètes viendront plus tard.
* **EN :** 🧪 Currently, only read-only (public address) wallets are supported for simulation. Full integration will come later.

### Peut-on utiliser DeFiPilot en mode réel ?

* **FR :** 🔒 Pas encore. À partir de la version 4.0, le mode réel complet sera disponible. Avant cela, tout est simulation.
* **EN :** 🔒 Not yet. From version 4.0, the full real mode will be available. Until then, everything is simulation only.

### Peut-on personnaliser les critères d’analyse des pools ?

* **FR :** ✅ Oui. Le profil choisi (prudent, modéré, agressif…) influence la pondération APR/TVL et la sélection des pools.
* **EN :** ✅ Yes. The selected profile (cautious, moderate, aggressive...) influences APR/TVL weighting and pool selection.

### Comment signaler un bug ou une suggestion ?

* **FR :** 💬 Ouvre une "issue" sur GitHub ou contacte le développeur via le dépôt.
* **EN :** 💬 Open an issue on GitHub or contact the developer through the repository.

---

## Développeur / Developer

**FR :** Projet initié et développé par **David Raffeil** avec l’assistance de ChatGPT.
**EN :** Project initiated and developed by **David Raffeil** with ChatGPT assistance.

Pour toute question ou suggestion : issues GitHub ou [voir la vision du projet](https://github.com/DavidRaffeil/DeFiPilot/blob/main/VISION.md)
