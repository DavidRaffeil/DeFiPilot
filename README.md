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

## 🆕 Nouveautés / What's New – V3.9

### Version française
- Finalisation du **farming LP réel complet** sur **SushiSwap (Polygon)** : **stake, harvest et unstake** opérationnels.  
- Journalisation enrichie avec `tx_hash`, `gas_used`, `tx_cost_native` et suivi automatique dans les CSV/JSONL.  
- Ajout du **journal des risques** (`journal_risques.csv`).  
- Validation complète du module CLI `farming_cli.py`.  
- Nettoyage et stabilisation des tests dry-run / réels.

### English version
- Completion of **full real LP farming** on **SushiSwap (Polygon)**: **stake, harvest, and unstake** all operational.  
- Enhanced logging with `tx_hash`, `gas_used`, `tx_cost_native` and automatic tracking in CSV/JSONL.  
- Added **risk journal** (`journal_risques.csv`).  
- Full validation of the `farming_cli.py` CLI module.  
- Cleanup and stabilization of dry-run and real tests.

---

## Historique des versions / Past Versions

### 🔹 Version V3.8 – Ajout de liquidité réel (2025-09-24)

- **FR :** Première exécution réussie d’**ajout de liquidité réel** sur Polygon (SushiSwap, paire USDC/WETH), avec réception de tokens LP. Intégration des **approvals**, du **contrôle du ratio et slippage**, du **post-check des soldes** et de la **journalisation CSV/JSONL**. Ajout d’un **CLI** (dry-run et réel).  
- **EN :** First successful **real liquidity add** on Polygon (SushiSwap, USDC/WETH pair), with LP tokens received. Includes **approvals**, **ratio and slippage checks**, **post-check of balances**, and **CSV/JSONL logging**. Added a **CLI** (dry-run and real).

Fichiers concernés / Related files :  
- `core/liquidity_real_tx.py` — fonction `ajouter_liquidite_reelle(...)`  
- `core/liquidity_dryrun.py` — fonction `ajouter_liquidite_dryrun(...)`  
- `core/journal.py` — journaux enrichis (CSV + JSONL)  
- `liquidity_cli.py` — CLI pour dry-run et réel

---

## 🚀 Roadmap

| Version | État | Contenu FR / EN |
| ------: | :--: | --------------- |
| `v3.8`  | ✅   | **FR :** Ajout de liquidité réelle sur DEX (LP). **EN:** Real DEX liquidity add (LP). |
| `v3.9`  | ✅   | **FR :** Farming LP réel complet (staking, récolte, unstake). **EN:** Full real LP farming (staking, harvest, unstake). |
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
- **FR :** **Ajout de liquidité réel** (SushiSwap V2, Polygon) avec tokens LP reçus et post-check.  
  **EN :** **Real liquidity add** (SushiSwap V2, Polygon) with LP tokens received and post-check.
- **FR :** **Farming LP réel complet** (MiniChef SushiSwap, Polygon) avec staking, harvest et unstake réels.  
  **EN :** **Full real LP farming** (MiniChef SushiSwap, Polygon) including staking, harvest and unstake.
- **FR :** Interface graphique simple (Tkinter) pour la simulation.  
  **EN :** Simple GUI (Tkinter) for simulation.

---

## Installation

1) **Cloner le dépôt**
```bash
git clone https://github.com/DavidRaffeil/DeFiPilot.git
cd DeFiPilot
```

2) **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3) **Configurer l’environnement Polygon**

Définir `POLYGON_RPC_URL` (ex : https://polygon-rpc.com ou votre provider).

Linux/macOS :
```bash
export POLYGON_RPC_URL="https://polygon-rpc.com"
```
Windows (Git Bash, session courante) :
```bash
export POLYGON_RPC_URL="https://polygon-rpc.com"
```
Vérifier :
```bash
python -c "import os; print(os.getenv('POLYGON_RPC_URL'))"
```

4) **Configurer le wallet par défaut**

Éditer `config/wallets.json` (respecter la casse et le format) :
```json
[
  {
    "name": "wallet_invest_long_terme",
    "address": "0xVotreAdresseChecksumIci",
    "private_key": "0xVotreClePriveeHex66car"
  }
]
```
Vérifier que l’adresse correspond à la clé :
```bash
python - <<'PY'
from eth_account import Account
import json
w = json.load(open("config/wallets.json","r",encoding="utf-8"))[0]
print(Account.from_key(w["private_key"]).address == w["address"])
PY
```

---

## Utilisation

### Mode simulation (analyse)
```bash
python main.py
```

### Swaps réels (Polygon, SushiSwap V2)

Dry-run (aucun envoi) :
```bash
python test_swap_reel_cli.py --token-in 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174 --token-out 0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619 --amount-in-wei 1000000 --slippage-bps 50 --dry-run
```

Envoi réel (confirmation explicite) :
```bash
python test_swap_reel_cli.py --token-in 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174 --token-out 0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619 --amount-in-wei 1000000 --slippage-bps 50 --confirm
```

### Ajout de liquidité (Polygon, SushiSwap V2)

Dry-run :
```bash
python liquidity_cli.py add_liquidity --platform sushiswap --chain polygon \
  --tokenA USDC --tokenB WETH --amountA 1 --amountB 0.001080405 \
  --slippage-bps 50 --dry-run
```

Envoi réel (confirmation explicite) :
```bash
python liquidity_cli.py add_liquidity --platform sushiswap --chain polygon \
  --tokenA USDC --tokenB WETH --amountA 1 --amountB 0.001080405 \
  --slippage-bps 50 --confirm
```

---

## Sécurité / Security

- **FR :** Ne jamais committer la clé privée. Conservez `config/wallets.json` en privé.  
- **EN :** Never commit your private key. Keep `config/wallets.json` private.

- **FR :** Utilisez des comptes de montants limités pour les tests.  
- **EN :** Use low-balance accounts for testing.

- **FR :** Vérifiez les adresses checksum (tokens, router, wallet).  
- **EN :** Verify checksum addresses (tokens, router, wallet).

- **FR :** Surveillez les allowances et révoquez-les si nécessaire.  
- **EN :** Monitor allowances and revoke if needed.

---

## Dépannage / Troubleshooting

- **Web3 non connecté** → vérifier `POLYGON_RPC_URL`.  
- **execution reverted: TRANSFER_FROM_FAILED** → allowance USDC insuffisante ou incohérente ; refaire approve.  
- **only accepts checksum addresses** → convertir avec `Web3.to_checksum_address(...)`.  
- **Pas de logs visibles** → lancer avec `logging.basicConfig(level=logging.INFO)` dans vos scripts.

---

## Licence / License

- **FR :** Projet gratuit pour usage personnel uniquement (non commercial).  
- **EN :** Free project for personal use only (non-commercial).

Voir les conditions complètes dans License.md  
See full terms in License.md

---

## FAQ

**Peut-on utiliser DeFiPilot avec un exchange centralisé ?**  
FR : ❌ Non, DeFiPilot vise la DeFi uniquement.  
EN : ❌ No, DeFiPilot targets DeFi only.

**Est-ce que DeFiPilot fonctionne en mode réel ?**  
FR : ✅ Oui, en partie : swaps, ajout de liquidité et farming LP sont maintenant réels.  
EN : ✅ Yes, partially: swaps, liquidity add and LP farming are now real.

**Peut-on personnaliser les critères d’analyse des pools ?**  
FR : ✅ Oui, via les profils (prudent, modéré, agressif…).  
EN : ✅ Yes, via profiles (cautious, moderate, aggressive…).

**Comment signaler un bug ou proposer une idée ?**  
FR : Ouvrir une issue GitHub.  
EN : Open a GitHub issue.

---

## Développeur / Developer

FR : Projet initié et développé par David Raffeil avec assistance IA.  
EN : Project initiated and developed by David Raffeil with AI assistance.

Voir aussi : VISION.md