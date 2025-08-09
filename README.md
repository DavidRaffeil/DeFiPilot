# DeFiPilot

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

### 🔹 Version V3.2 – Journalisation des pools risquées (9 août 2025)

– Ajout de `enregistrer_pools_risquées()` pour tracer automatiquement les pools à risque  
  Added `enregistrer_pools_risquées()` to automatically log risky pools  
– Journalisation automatique dans `logs/journal_risques.csv`  
  Automatic logging in `logs/journal_risques.csv`  
– Analyse simple du risque via APR et TVL  
  Simple risk analysis via APR and TVL  

---

## 📜 Historique des versions / Past Versions

### 🔹 Version V3.1 – Signature des transactions Web3 (7 août 2025)

– Signature locale des swaps via Web3 avec clé privée sécurisée  
  Local swap signing via Web3 with secure private key  
– Connexion stable au réseau Polygon via Infura  
  Stable connection to Polygon network via Infura  
– Test de signature avec `test_signer_transaction.py`  
  Signature test with `test_signer_transaction.py`

### 🔹 Version V3.0 – Simulation LP & Swap simulé (6 août 2025)

– Ajout de `swap_reel.py` pour simuler un swap "réel" avec wallet  
  Added `swap_reel.py` to simulate wallet-based swaps  
– Intégration du wallet simulé via `real_wallet.py`  
  Simulated wallet integration via `real_wallet.py`  
– Journalisation détaillée des swaps LP dans `journal_swap_lp.csv`  
  Detailed LP swap logging in `journal_swap_lp.csv`  
– Préparation à la gestion réelle des transactions  
  Preparing for real transaction execution

### 🔹 Version V2.9 – Journalisation du slippage LP (5 août 2025)

– Journalisation automatique du slippage LP simulé dans `journal_slippage_lp.csv`  
  Automatic logging of simulated LP slippage in `journal_slippage_lp.csv`  
– Chaque ligne contient 7 colonnes : date, pool, plateforme, montant LP, slippage, profil  
  Each line contains 7 columns: date, pool, platform, LP amount, slippage, profile  
– Utilisation de `simuler_farming_lp()` pour tracer les pertes simulées dues au slippage  
  Uses `simuler_farming_lp()` to log simulated losses due to slippage

### 🔹 Version V2.8 – Pondération du slippage LP (3 août 2025)

– Intégration du paramètre `poids_slippage` dans les profils  
  `poids_slippage` parameter added to profiles  
– Application d’un malus pondéré sur les pools utilisant des tokens LP  
  Weighted malus applied to LP-based pools  
– Score final ajusté automatiquement selon le profil  
  Final score adjusted automatically based on the active profile

### 🔹 Version V2.7 – Intégration complète farming LP (3 août 2025)

– Simulation complète du farming LP avec APR (rendement annualisé)  
  Full simulation of LP farming with APR (annual yield)  
– Nouveau fichier `journal_farming.csv` pour tracer les gains simulés par pool  
  New `journal_farming.csv` file to track simulated pool yields  
– Journalisation cumulée des LP dans `journal_lp_cumul.csv`  
  Cumulative LP logging in `journal_lp_cumul.csv`  
– Vérification complète des logs avant passage au mode réel  
  Full log validation before entering real mode

### 🔹 Version V2.6 – Mode simulateur amélioré (2 août 2025)

– Amélioration du simulateur avec enregistrement du solde LP simulé  
  Improved simulator with LP balance logging  
– Nouveau fichier `journal_lp_cumul.csv` pour le suivi des LP  
  New `journal_lp_cumul.csv` for LP tracking  
– Nouvelle fonction de journalisation des rendements LP par pool  
  New LP farming yield logger by pool

### 🔹 Version V2.5 – Journalisation LP & check système (30 juillet 2025)

– Journalisation CSV complète des deux swaps simulés pour les pools LP  
  Full CSV logging of both simulated swaps for LP pools  
– Intégration du fichier check_setup.py pour vérifier la stabilité avant exécution  
  Integration of check_setup.py for stability checks before running  
– Refonte des logs et résumé journalier pour un meilleur suivi  
  Redesigned logs and daily summaries for better tracking

---

## Fonctionnalités principales / Main features

* Analyse automatique des pools DeFi via DefiLlama  
* Simulation d’investissement multi-profils avec score pondéré  
* Journalisation détaillée (résultats, historique CSV, log résumé quotidien)  
* Interface graphique simple (Tkinter)  
* Sélection des meilleures opportunités selon le profil d’investisseur  
* Préparation à l’intégration multi-blockchains et de fonctions avancées (voir roadmap)

---

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

| Version | Contenu prévu / Planned content                                                                                                                       |
|---------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| ~~`v3.2`~~ | ✅ Journalisation des pools risquées / Risky pool logging                                                                                            |
| `v3.3`  | Réglages intelligents des pondérations via IA (LabPilot) / AI-powered weighting strategy (via LabPilot)                                               |
| `v3.4`  | Multi-wallet : gestion de plusieurs portefeuilles simultanés / Multi-wallet support: manage several wallets simultaneously                            |
| `v3.5`  | Compatibilité multi-blockchains (Polygon, Avalanche, Fantom…) / Multi-chain compatibility (Polygon, Avalanche, Fantom…)                              |

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

Pour toute question ou suggestion : issues GitHub ou [voir la vision du projet](https://github.com/DavidRaffeil/DeFiPilot/blob/main/VISION.md)
