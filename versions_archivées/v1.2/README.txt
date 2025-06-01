🧠 DeFiPilot – Bot d’analyse de pools DeFi automatisé

📁 Contenu du projet :
├── main.py                ← Lancement principal du bot
├── settings.py           ← Tous les réglages simples (profil, intervalle, seuils)
├── config.py             ← Pondérations de scoring selon le profil
├── scanner_pools.py      ← Pools simulées (à remplacer plus tard par de vraies API)
├── strategy.py           ← Filtres et logique de décision selon le profil
├── scoring.py            ← Calcul du score pondéré d’une pool
├── executor.py           ← Simule les investissements/désinvestissements
├── portfolio.py          ← Gestion de la mémoire d’investissement
├── compounder.py         ← Taux de réinvestissement dégressif
├── logger.py             ← Création des logs journaliers
├── error_logger.py       ← Fichier `errors.log` pour enregistrer les erreurs
├── daily_summary.py      ← Résumé automatique à chaque cycle
├── logs/                 ← CSV par jour (YYYY-MM-DD.csv)
├── snapshots/            ← Sauvegarde du portefeuille après chaque cycle
├── portfolio.json        ← État actuel des investissements
└── errors.log            ← Erreurs rencontrées par le bot


🚀 Comment lancer le bot :
1. Ouvre un terminal dans le dossier du projet
2. Tape :  
   python main.py

📅 Le bot tourne en boucle (voir `settings.py` pour changer le temps entre les cycles)

🔧 Réglages rapides dans settings.py :
- INTERVAL_SECONDES = 600       ← temps entre chaque cycle (en secondes)
- PROFIL_INVESTISSEUR = "modéré"  ← ou "prudent" / "agressif"
- SEUIL_INVESTISSEMENT = 0.6    ← score minimum pour investir

💡 Modifier le comportement :
- Pour tester plus vite : INTERVAL_SECONDES = 10
- Les pondérations changent automatiquement selon le profil

🧠 À venir (idées futures) :
- IA pour recommandations
- Connexion à un vrai DEX via Web3
- Interface graphique
