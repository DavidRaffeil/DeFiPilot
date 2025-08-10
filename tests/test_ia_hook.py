# tests/test_ia_hook.py – V3.3
try:
    from core.config import AI_PONDERATION_ACTIVE
except Exception as e:
    print("❌ Impossible d'importer AI_PONDERATION_ACTIVE :", e)
else:
    print("✅ AI_PONDERATION_ACTIVE =", AI_PONDERATION_ACTIVE)

try:
    from core.ai.ponderation import calculer_ponderations_dynamiques
except Exception as e:
    print("❌ Import calculer_ponderations_dynamiques KO :", e)
else:
    print("✅ calculer_ponderations_dynamiques importé ?",
          calculer_ponderations_dynamiques is not None)
