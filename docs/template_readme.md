# 🧠 Modèle de README DeFiPilot

Ce fichier sert de **modèle de structure complète** pour les futures mises à jour du README officiel.  
Il contient la disposition correcte des sections, dans l’ordre exact du sommaire, afin de garantir un rendu Markdown propre sur GitHub.

---
## 📚 Sommaire / Table of Contents

1. [Introduction / Introduction](#-introduction--introduction)  
2. [Fonctionnalités principales / Key Features](#-fonctionnalités-principales--key-features)  
3. [Aperçu visuel / Visual Overview](#-aperçu-visuel--visual-overview)  
4. [Nouveautés / What's New — Version 5.0](#-nouveautés--whats-new--version-50)  
5. [Historique des versions / Past Versions](#-historique-des-versions--past-versions)  
6. [Caractéristiques techniques / Technical Highlights](#-caractéristiques-techniques--technical-highlights)  
7. [Prérequis / Requirements](#-prérequis--requirements)  
8. [Installation / Installation](#-installation--installation)  
9. [Utilisation / Usage](#-utilisation--usage)  
10. [Feuille de route / Roadmap](#-feuille-de-route--roadmap)  
11. [Vision du projet / Project Vision](#-vision-du-projet--project-vision)  
12. [FAQ / Foire aux questions](#-faq--foire-aux-questions)  
13. [À propos de l’auteur / About the Author](#-à-propos-de-lauteur--about-the-author)  
14. [Licence / License](#-licence--license)

---
## 🧭 Introduction / Introduction

**FR :**  
DeFiPilot est un bot DeFi autonome conçu pour analyser, sélectionner et gérer automatiquement les pools de liquidité les plus rentables sur différents DEX.  
Le projet démontre qu’un investisseur individuel peut bâtir un outil avancé de pilotage DeFi sans formation technique, grâce à l’assistance de l’IA.

**EN :**  
DeFiPilot is an autonomous DeFi bot designed to analyze, select, and automatically manage the most profitable liquidity pools across various DEXs.  
The project demonstrates that an individual investor can build an advanced DeFi management tool without a technical background, using AI assistance.

---
## ⚙️ Fonctionnalités principales / Key Features

**FR :**  
DeFiPilot automatise l’analyse et la gestion des investissements DeFi à travers :  
- Un **moteur de stratégie** calculant un score pondéré par pool (APR, TVL, volume, volatilité, tendance APR, slippage prévu, etc.)  
- Des **profils d’investissement** (Prudent, Modéré, Risqué) ajustant seuils, pondérations et limites d’exposition  
- Un **mode réel complet** capable d’exécuter swaps, ajouts/retraits de liquidité, staking/unstaking et récolte de récompenses (SushiSwap V2 + MiniChef sur Polygon)  
- Une **interface graphique Tkinter** affichant en temps réel contexte, stratégie, pools et journaux  
- Une **journalisation exhaustive** en CSV et JSONL de tous les événements (signaux, stratégies, transactions, erreurs, métriques système)  
- Une **gestion d’état persistante** via un fichier `.state` (chargement au démarrage, sauvegarde automatique, reprise après coupure)

**EN :**  
DeFiPilot automates DeFi investment analysis and management through:  
- A **strategy engine** computing a weighted score per pool (APR, TVL, volume, volatility, APR trend, expected slippage, etc.)  
- **Investment profiles** (Conservative, Moderate, Aggressive) adjusting thresholds, weights, and exposure limits  
- A **full real mode** able to perform swaps, add/remove liquidity, stake/unstake LP tokens, and harvest rewards (SushiSwap V2 + MiniChef on Polygon)  
- A **Tkinter GUI** displaying real-time market context, strategy, pools, and logs  
- **Extensive logging** to CSV and JSONL for all events (signals, strategies, transactions, errors, system metrics)  
- **Persistent state management** through a `.state` file (load on startup, automatic saving, and crash-safe recovery)

---
## 🖼️ Aperçu visuel / Visual Overview

![Capture d’écran DeFiPilot V5.0](assets/screenshot_defipilot_gui_v50.png)

**FR :**  
Aperçu de l’interface principale de DeFiPilot V5.0 — le tableau de bord affiche les pools, les signaux et les anomalies détectées par ControlPilot.

**EN :**  
Preview of DeFiPilot V5.0 main interface — the dashboard shows pools, signals, and anomalies detected by ControlPilot.

---
