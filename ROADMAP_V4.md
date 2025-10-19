# DeFiPilot — Roadmap V4.x (SushiSwap Polygon)

> Objectif global : activer un **mode réel complet** piloté par stratégie (stake / harvest / unstake / add/remove) avec sécurité forte et journalisation riche.

---

## Versioning

* **Série 4.0.x** : incréments rapides et compatibles, orientés stabilisation et complétude de la stratégie.
* Nommage : **V4.0.1**, **V4.0.2**, **V4.0.3**, … (patch releases).

---

## V4.0.1 — Orchestrateur & Préflight (MVP Dry‑Run)

**But :** poser les fondations du moteur de décision, en **dry‑run uniquement**.

### Livrables

* `strategy_orchestrator.py` : boucle `preflight -> decide -> act(plan) -> log` (sans envoi réel).
* `config/strategy.yaml` : paramètres (seuil harvest, min_dust_lp, slippage_bps max, max_tx_cost_native,…).
* Préflight on‑chain : pending rewards, soldes LP, allowances, prix gas courant.
* Journalisation : entrée unique `journal_risques.csv` (rule_id, risk_level, reason) + trace contextuelle JSON.
* CLI : `python strategy_orchestrator.py decide --pool usdc-weth --dry-run` (affiche l’action recommandée ou no‑op).

### Critères d’acceptation

* Décision **déterministe** (mêmes entrées → même sortie).
* Aucune émission on‑chain ; logs complets CSV/JSONL.
* Au moins **5 règles risques** actives (low/medium/high).

---

## V4.0.2 — Politiques Harvest/Unstake & Math de Liquidité

**But :** implémenter la logique de décision **utile** et les calculs critiques.

### Livrables

* **Harvest policy** : déclenchement si `valeur_rewards >= k × coût_gas_estimé` (k paramétrable). No‑op sinon.
* **Unstake policy** : partiel/total avec garde‑fou `min_dust_lp` et `max_unstake_pct`.
* **liquidity_math.py** : `amountB_optimal`, contrôle ratio, `amountMin` à partir de `slippage_bps`.
* **Gas strategy** : buffer `gas_limit`, plafond `max_tx_cost_native` (bloque l’action si dépassé).
* Enrichissement logs : `balance_SLP_after`, `rewards_token/amount`, `context.json`.
* Tests unitaires : math (bords, arrondis), règles de décision.

### Critères d’acceptation

* 100% des tests unitaires verts sur le module math/règles.
* Dry‑runs complets pour 10 cas (récompenses=0, gas élevé, dust, unstake partiel/total, etc.).

---

## V4.0.3 — Exécution Réelle & Sécurité Avancée

**But :** autoriser l’envoi **réel** de transactions de façon sû re.

### Livrables

* Envoi réel **opt‑in** via `--confirm` (sinon dry‑run).
* **Panic‑stop** (flag global désactivant toute action réelle).
* **Idempotence** par `run_id` (éviter doublons si retry).
* **Taxonomie d’erreurs** : ré‑essayables vs fatales ; messages actionnables.
* Documentation : README (section V4.0), exemples CLI, troubleshooting mis à jour.

### Critères d’acceptation

* **5 runs consécutifs en réel** sans erreur fatale.
* Journaux cohérents (`tx_hash`, `gas_used`, `tx_cost_native`, balances après action).
* Harvest **no‑op** quand rewards = 0 ou < seuil.
* Unstake total remet LP ≈ 0, partiel respecte `min_dust_lp`.

---

## (Prévision) Suites 4.x

* **V4.1** — Profits & retraits automatisés (distribution, seuils hebdo/mensuels).
* **V4.2** — Multi‑wallets & sécurité renforcée (rôles, limites par wallet).
* **V4.3** — Multi‑pool / cross‑DEX (sélection, rotation simple).

---

## Fichiers impactés (prévision)

* `strategy_orchestrator.py`, `config/strategy.yaml`
* `farming_cli.py`, `liquidity_cli.py`, `core/liquidity_math.py`
* `core/farming_sushi_polygon.py`, `core/farming_api.py`
* `journal_farming.csv`, `journal_liquidite.csv`, `journal_risques.csv`
* `README.md`

---

## Commandes (exemples)

```bash
# Décision (dry‑run)
python strategy_orchestrator.py decide --pool usdc-weth --dry-run

# Harvest si rentable (réel)
python strategy_orchestrator.py harvest --pool usdc-weth --confirm

# Unstake partiel sécurisé (réel)
python strategy_orchestrator.py unstake --pool usdc-weth --amount-lp 0.1 --confirm

# Panic stop (désactive toute action réelle)
python strategy_orchestrator.py panic-stop --enable
```

