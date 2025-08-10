# DeFiPilot

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-stable-brightgreen)]()
![License: Personal Use Only](https://img.shields.io/badge/license-Personal--Use--Only-lightgrey)
[![Built with ChatGPT](https://img.shields.io/badge/built%20with-ChatGPT-10a37f?logo=openai&logoColor=white)](https://openai.com/chatgpt)
![Made in France](https://img.shields.io/badge/Made%20in-France-blue)

---

> Bot personnel d’analyse et d’investissement automatisé en DeFi.  
> Personal bot for automated analysis and investment in DeFi.

---

## Présentation / About

⚠️ *Actuellement, seule la version française du bot est disponible. L’interface et les logs sont en français uniquement.*  
⚠️ *Currently, only the French version of the bot is available. The interface and logs are in French only.*

**DeFiPilot** est un projet open-source (usage non commercial) développé pour apprendre, expérimenter et automatiser l’investissement en finance décentralisée (DeFi), avec **Python** et de l’**IA**.  
**DeFiPilot** is an open-source project (non-commercial use) to learn, experiment, and automate decentralized finance (DeFi) investing, using **Python** and **AI**.

Le projet évolue en public, étape par étape, avec une démarche transparente et progressive.  
The project evolves publicly, step by step, with a transparent and progressive approach.

Vision complète de l’écosystème et futurs bots :  
👉 [VISION.md](https://github.com/DavidRaffeil/DeFiPilot/blob/main/VISION.md)

---

## Nouveautés / What's New

### 🔹 Version V3.7 – Swap réel sur DEX Polygon (2025-08-10)

- **FR :** Exécution de **swaps réels** sur Polygon via un router **Uniswap V2** (SushiSwap V2), avec **slippage**, **approve automatique**, **confirmation avant envoi**, et **journalisation**.
- **EN :** Perform **real swaps** on Polygon via an **Uniswap V2**-style router (SushiSwap V2), with **slippage**, **auto-approve**, **pre-send confirmation**, and **logging**.

Fichiers concernés :
- `core/swap_reel.py` — fonction `effectuer_swap_reel(...)` (slippage_bps, require_confirmation/confirm, dry_run, wait_receipt, gas override).
- `test_swap_reel_cli.py` — CLI de test (dry-run / envoi réel).

### 🔹 Version V3.6 – Wallet réel (2025-08-10)

- **FR :** Wallet réel `core/real_wallet.py` (Polygon RPC), gestion multi-wallets via `wallets_manager`, logs `wallet_connect` / `wallet_disconnect`, signature de message.
- **EN :** Real wallet `core/real_wallet.py` (Polygon RPC), multi-wallet via `wallets_manager`, `wallet_connect` / `wallet_disconnect` logging, message signing.

---

## 🚀 Roadmap

| Version | État | Contenu FR / EN |
| ------: | :--: | --------------- |
| `v3.7`  | ✅   | **FR :** Swap réel sur Polygon (SushiSwap V2). **EN:** Real swap on Polygon (SushiSwap V2). |
| `v3.8`  | 🛠️  | **FR :** Ajout de liquidité réelle sur DEX (LP). **EN:** Real DEX liquidity add (LP). |
| `v3.9`  | 🛠️  | **FR :** Farming LP réel (staking, récolte). **EN:** Real LP farming (staking, harvest). |
| `v4.0`  | 🛠️  | **FR :** Mode réel complet (stratégie auto, retraits, reprise). **EN:** Full real mode (auto strategy, withdrawals, resume). |

*La roadmap peut évoluer en fonction de l’avancement.*  
*Roadmap may change as the project evolves.*

---

## Fonctionnalités / Features

- **FR :** Analyse automatique des pools DeFi (via agrégateurs), simulation multi-profils et scoring.  
  **EN :** Automatic DeFi pool analysis (via aggregators), multi-profile simulation and scoring.
- **FR :** Journalisation détaillée (résultats, CSV, résumés).  
  **EN :** Detailed logging (results, CSV, summaries).
- **FR :** Wallet réel Polygon, multi-wallets.  
  **EN :** Real wallet on Polygon, multi-wallet support.
- **FR :** **Swaps réels** sur Polygon (SushiSwap V2) avec slippage et confirmation.  
  **EN :** **Real swaps** on Polygon (SushiSwap V2) with slippage and confirmation.
- **FR :** Interface graphique simple (Tkinter) pour la simulation.  
  **EN :** Simple GUI (Tkinter) for simulation.

---

## Installation

1) **Cloner le dépôt**
```bash
git clone https://github.com/DavidRaffeil/DeFiPilot.git
cd DeFiPilot
Installer les dépendances

bash
Copier
Modifier
pip install -r requirements.txt
Configurer l’environnement Polygon

Définir POLYGON_RPC_URL (ex : https://polygon-rpc.com ou votre provider).

Linux/macOS :

bash
Copier
Modifier
export POLYGON_RPC_URL="https://polygon-rpc.com"
Windows (Git Bash, session courante) :

bash
Copier
Modifier
export POLYGON_RPC_URL="https://polygon-rpc.com"
Vérifier :

bash
Copier
Modifier
python -c "import os; print(os.getenv('POLYGON_RPC_URL'))"
Configurer le wallet par défaut

Éditer config/wallets.json (respecter la casse et le format) :

json
Copier
Modifier
[
  {
    "name": "wallet_invest_long_terme",
    "address": "0xVotreAdresseChecksumIci",
    "private_key": "0xVotreClePriveeHex66car"
  }
]
Vérifier que l’adresse correspond à la clé :

bash
Copier
Modifier
python - <<'PY'
from eth_account import Account
import json, sys
w = json.load(open("config/wallets.json","r",encoding="utf-8"))[0]
print(Account.from_key(w["private_key"]).address == w["address"])
PY
Utilisation
Mode simulation (analyse)
bash
Copier
Modifier
python main.py
Swaps réels (Polygon, SushiSwap V2)
Dry-run (aucun envoi) :

bash
Copier
Modifier
python test_swap_reel_cli.py --token-in 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174 --token-out 0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619 --amount-in-wei 1000000 --slippage-bps 50 --dry-run
Aperçu avec confirmation requise :

bash
Copier
Modifier
python test_swap_reel_cli.py --token-in 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174 --token-out 0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619 --amount-in-wei 1000000 --slippage-bps 50
Envoi réel (confirmation explicite) :

bash
Copier
Modifier
python test_swap_reel_cli.py --token-in 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174 --token-out 0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619 --amount-in-wei 1000000 --slippage-bps 50 --confirm
Notes :

--amount-in-wei est exprimé en wei du token d’entrée (USDC a 6 décimales : 1 USDC = 1_000_000).

Le script gère l’approve automatique si l’allowance est insuffisante (spender = router SushiSwap V2 en checksum).

slippage_bps=50 => 0,50% de slippage max.

require_confirmation est activé par défaut côté API : sans --confirm, la transaction n’est pas envoyée.

Sécurité / Security
Ne jamais committer la clé privée. Conservez config/wallets.json en privé.

Utilisez des comptes de montants limités pour les tests.

Vérifiez les adresses checksum (tokens, router, wallet).

Surveillez les allowances et révoquez-les si nécessaire.

Dépannage / Troubleshooting
Web3 non connecté → vérifier POLYGON_RPC_URL.

execution reverted: TRANSFER_FROM_FAILED → allowance USDC insuffisante ou incohérente ; refaire approve.

only accepts checksum addresses → convertir avec Web3.to_checksum_address(...).

Pas de logs visibles → lancer avec logging.basicConfig(level=logging.INFO) dans vos scripts.

Licence / License
FR : Projet gratuit pour usage personnel uniquement (non commercial).
EN : Free project for personal use only (non-commercial).

Voir les conditions complètes dans License.md
See full terms in License.md

FAQ
Peut-on utiliser DeFiPilot avec un exchange centralisé ?
FR : ❌ Non, DeFiPilot vise la DeFi uniquement.

EN : ❌ No, DeFiPilot targets DeFi only.

Est-ce que DeFiPilot fonctionne en mode réel ?
FR : ✅ Partiellement : swaps réels sur Polygon (SushiSwap V2) sont disponibles. Le reste (LP, farming) arrive dans v3.8–v3.9.

EN : ✅ Partially: real swaps on Polygon (SushiSwap V2) are available. LP and farming coming in v3.8–v3.9.

Peut-on personnaliser les critères d’analyse des pools ?
FR : ✅ Oui, via les profils (prudent, modéré, agressif…).

EN : ✅ Yes, via profiles (cautious, moderate, aggressive…).

Comment signaler un bug ou proposer une idée ?
FR : Ouvrir une issue GitHub.

EN : Open a GitHub issue.

Développeur / Developer
FR : Projet initié et développé par David Raffeil avec assistance IA.
EN : Project initiated and developed by David Raffeil with AI assistance.

Voir aussi : VISION.md

sql
Copier
Modifier
