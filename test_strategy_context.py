from core.strategy_context import construire_contexte_strategie, est_contexte_favorable

# Deux signaux normalisés de test
signaux = [
    {
        "timestamp": "2025-11-15T09:00:00Z",
        "context_label": "test",
        "metrics": {"apr": 120, "tvl": 1_000_000},
        "ai_score": 0.72,
    },
    {
        "timestamp": "2025-11-15T09:01:00Z",
        "context_label": "test",
        "metrics": {"apr": 80, "tvl": 500_000},
        "ai_score": 0.68,
    },
]

contexte = construire_contexte_strategie(signaux, contexte_precedent="neutre")

print("Contexte:", contexte)
print("Label:", contexte.label)
print("Confiance:", contexte.confiance)
print("Résumé:", contexte.resume)
print("Favorable ?", est_contexte_favorable(contexte))
