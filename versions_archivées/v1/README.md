🧠 DeFiPilot – Bot d’analyse de pools DeFi automatisé  
🧠 DeFiPilot – Automated DeFi pool analysis bot

---

📁 Contenu du projet / Project structure:

├── main.py                ← Lancement principal du bot  
│                          ← Main bot launcher  
├── settings.py           ← Tous les réglages simples (profil, intervalle, seuils)  
│                          ← Basic settings (profile, interval, thresholds)  
├── config.py             ← Pondérations de scoring selon le profil  
│                          ← Scoring weights based on the selected profile  
├── scanner_pools.py      ← Pools simulées (à remplacer plus tard par de vraies API)  
│                          ← Simulated pools (to be replaced later by real APIs)  
├── strategy.py           ← Filtres et logique de décision selon le profil  
│                          ← Filters and decision logic based on profile  
├── scoring.py            ← Calcul du score pondéré d’une pool  
│                          ← Weighted score calculation for a pool  
├── executor.py           ← Simule les investissements/désinvestissements  
│                          ← Simulates investments/uninvestments  
├── portfolio.py          ← Gestion de la mémoire d’investissement  
│                          ← Manages portfolio memory  
├── compounder.py         ← Taux de réinvestissement dégressif  
│                          ← Gradual reinvestment rate (auto-compounding)  
├── logger.py             ← Création des logs journaliers  
│                          ← Daily logs generator  
├── error_logger.py       ← Fichier `errors.log` pour enregistrer les erreurs  
│                          ← `errors.log` file to track errors  
├── daily_summary.py      ← Résumé automatique à chaque cycle  
│                          ← Automatic summary after each cycle  
├── logs/                 ← CSV par jour (YYYY-MM-DD.csv)  
│                          ← Daily CSV log files  
├── snapshots/            ← Sauvegarde du portefeuille après chaque cycle  
│                          ← Portfolio snapshot after each cycle  
├── portfolio.json        ← État actuel des investissements  
│                          ← Current portfolio state  
└── errors.log            ← Erreurs rencontrées par le bot  
                           ← Bot-detected errors

---

🚀 Comment lancer le bot :  
🚀 How to launch the bot:

1. Ouvre un terminal dans le dossier du projet  
   Open a terminal in the project folder  
2. Tape / Type :  
   python main.py

📅 Le bot tourne en boucle (voir `settings.py` pour changer le temps entre les cycles)  
📅 The bot runs in a loop (see `settings.py` to change cycle interval)

---

🔧 Réglages rapides dans `settings.py` :  
🔧 Quick settings in `settings.py`:

- INTERVAL_SECONDES = 600       ← temps entre chaque cycle (en secondes)  
  → Time between each cycle (in seconds)  
- PROFIL_INVESTISSEUR = "modéré" ← ou "prudent" / "agressif"  
  → Profile: "moderate", "conservative", or "aggressive"  
- SEUIL_INVESTISSEMENT = 0.6    ← score minimum pour investir  
  → Minimum score required to invest

💡 Modifier le comportement :  
💡 Modify behavior:

- Pour tester plus vite : INTERVAL_SECONDES = 10  
  → For faster testing: set INTERVAL_SECONDES = 10  
- Les pondérations changent automatiquement selon le profil  
  → Scoring weights automatically adapt to selected profile

---

🧠 À venir (idées futures) / Coming soon:

- IA pour recommandations  
  → AI-driven recommendations  
- Connexion à un vrai DEX via Web3  
  → Connection to real DEX via Web3  
- Interface graphique  
  → Graphical user interface (GUI)
