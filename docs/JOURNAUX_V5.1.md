# Spécification journaux V5.1 / V5.1 logs specification

## 1. Objectif / Goal

**FR :**  
L’objectif de cette spécification est d’unifier la journalisation des informations utilisées par DeFiPilot V5.1 :
- les signaux et le contexte marché,
- les décisions de la stratégie,
- les exécutions réelles sur la blockchain.

Cela permet :
- une meilleure traçabilité des décisions,
- une exploitation plus simple par ControlPilot / LabPilot,
- un affichage propre dans la GUI V5.1.1 (et futures versions).

**EN:**  
The goal of this specification is to unify logging for DeFiPilot V5.1:
- signals and market context,
- strategy decisions,
- real blockchain executions.

This enables:
- better traceability of decisions,
- easier use by ControlPilot / LabPilot,
- clean display in the V5.1.1 GUI (and future versions).

---

## 2. Journal des signaux (`journal_signaux.jsonl`)

### 2.1 Description / Description

**FR :**  
Une ligne = un instantané global des signaux : contexte, score, métriques et policy.  
Ce journal est déjà utilisé par la GUI V5.1.1 (onglets *Résumé actuel* et *Historique des signaux*).

**EN:**  
One line = a global snapshot of signals: context, score, metrics and policy.  
This log is already used by the V5.1.1 GUI (*Current summary* and *Signals history* tabs).

### 2.2 Schéma / Schema

Champs minimum / Minimal fields :

- `timestamp` (str, ISO 8601, ex. `"2025-11-16T15:10:11Z"`)
- `context` (str, ex. `"favorable"`, `"neutre"`, `"risque"`)
- `last_context` ou `previous_context` (str)
- `score` (float, score global de contexte)
- `defipilot_version` (str, ex. `"V5.1.1"`)
- `run_id` (str, identifiant de run ou de cycle)

Bloc metrics / Metrics block (dict, clé `metrics` ou `metrics_locales`) :

- `apr_mean` (float)
- `tvl_sum` (float, USD)
- `volume_sum` (float, USD, 24h)
- `volatility_cv` (float)
- `apr_trend_avg` (float)

Bloc policy (dict, clé `policy`) :

- `modere` (float, 0–1)
- `prudent` (float, 0–1)
- `risque` (float, 0–1)

Champs optionnels / Optional fields :

- `source` (str, ex. `"controlpilot"`, `"defipilot-core"`)
- `note` / `comment` (str, commentaire humain ou IA)

### 2.3 Exemple / Example

```json
{
  "timestamp": "2025-11-16T15:10:11Z",
  "context": "favorable",
  "previous_context": "neutre",
  "score": 1.0,
  "defipilot_version": "V5.1.1",
  "run_id": "journal_daemon-2025-11-16T15:10:11Z",
  "metrics": {
    "apr_mean": 0.1167,
    "tvl_sum": 2.15e7,
    "volume_sum": 2.35e6,
    "volatility_cv": 0.301,
    "apr_trend_avg": 0.0439
  },
  "policy": {
    "modere": 0.30,
    "prudent": 0.10,
    "risque": 0.60
  },
  "source": "controlpilot",
  "note": "Contexte global favorable sur les pools suivies."
}
3. Journal des décisions (journal_decisions.jsonl)
3.1 Description / Description
FR :
Une ligne = une décision de la stratégie (simulation ou réel) concernant une pool ou un portefeuille :

entrer,

renforcer,

réduire,

sortir,

rééquilibrer,

ou ignorer (skip).

EN:
One line = one strategy decision (simulation or real) regarding a pool or portfolio:

enter,

increase,

decrease,

exit,

rebalance,

or skip.

3.2 Schéma / Schema
Contexte général / General context :

timestamp (str)

run_id (str)

defipilot_version (str)

mode (str, "simulation" ou "reel")

context (str, contexte au moment de la décision)

profil (str, ex. "prudent", "modere", "agressif")

Action / Action :

action_type (str, ex. "enter_pool", "increase_position", "decrease_position", "exit_pool", "rebalance", "skip")

reason (str, ex. "score_below_threshold", "better_pool_found", "risk_too_high")

Cible / Target :

pool_id (str)

platform (str, ex. "sushiswap")

chain (str, ex. "polygon")

token_in / token_out ou lp_token (str) selon le type d’action

Montants / Amounts :

amount_usd (float, estimation en USD)

amount_token_in / amount_token_out (float) ou amount_lp (float)

Lien avec signaux / Link with signals :

signal_ref (str, ex. run_id ou autre identifiant provenant de journal_signaux.jsonl)

3.3 Exemple / Example
json
Copier le code
{
  "timestamp": "2025-11-16T15:12:03Z",
  "run_id": "journal_daemon-2025-11-16T15:10:11Z",
  "defipilot_version": "V5.1.1",
  "mode": "simulation",
  "context": "favorable",
  "profil": "modere",
  "action_type": "enter_pool",
  "reason": "top_score_and_risk_ok",
  "pool_id": "polygon_sushi_usdc_weth",
  "platform": "sushiswap",
  "chain": "polygon",
  "token_in": "USDC",
  "token_out": "WETH",
  "amount_usd": 150.0,
  "amount_token_in": 150.0,
  "signal_ref": "journal_daemon-2025-11-16T15:10:11Z"
}
4. Journal des exécutions (journal_exec.jsonl)
4.1 Description / Description
FR :
Une ligne = une exécution réelle sur la blockchain (swap, ajout de liquidité, retrait, staking, unstake, harvest…).
Ce journal complète les décisions : il permet de vérifier ce qui a réellement été fait, combien ça a coûté en gas, etc.

EN:
One line = a real on-chain execution (swap, add liquidity, remove, stake, unstake, harvest…).
This log complements the decisions: it allows checking what was actually done, and how much gas it cost.

4.2 Schéma / Schema
Transaction / Transaction :

timestamp (str)

tx_hash (str)

chain (str)

dex ou platform (str)

operation (str, "swap", "add_liquidity", "remove_liquidity", "stake", "unstake", "harvest", etc.)

status (str, "success", "failed", "reverted")

Montants / Amounts :

amount_in (float)

amount_out (float)

amount_usd_estimate (float)

gas_used (int)

effective_gas_price (int ou float, en wei)

tx_cost_native (float, ex. POL)

tx_cost_usd (float)

Traçabilité / Traceability :

decision_ref (str, référence vers journal_decisions.jsonl)

signal_ref (str, référence vers journal_signaux.jsonl si pertinent)

4.3 Exemple / Example
json
Copier le code
{
  "timestamp": "2025-11-16T15:12:15Z",
  "tx_hash": "0xabc123...",
  "chain": "polygon",
  "platform": "sushiswap",
  "operation": "add_liquidity",
  "status": "success",
  "amount_in": 150.0,
  "amount_out": 0.0000000048,
  "amount_usd_estimate": 150.3,
  "gas_used": 153421,
  "effective_gas_price": 21000000000,
  "tx_cost_native": 0.00322,
  "tx_cost_usd": 0.54,
  "decision_ref": "decision-2025-11-16T15:12:03Z",
  "signal_ref": "journal_daemon-2025-11-16T15:10:11Z"
}
5. Intégration V5.1 / V5.1 Integration
FR :

La GUI V5.1.1 lit déjà journal_signaux.jsonl et journal_control.jsonl.

À partir de cette spécification, les modules suivants devront respecter ces formats :

générateur de signaux / daemon de contexte,

moteur de stratégie (journalisation des décisions),

couche d’exécution réelle (journalisation des transactions).

EN:

The V5.1.1 GUI already reads journal_signaux.jsonl and journal_control.jsonl.

Based on this specification, the following modules must respect these formats:

signal generator / context daemon,

strategy engine (decisions logging),

real execution layer (transactions logging).