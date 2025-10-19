# test_journal_read.py
from pathlib import Path
import json

p = Path("journal_signaux.jsonl")
if not p.exists():
    print("Journal introuvable :", p)
else:
    *_, last = p.read_text(encoding="utf-8").rstrip("\n").splitlines()
    print("Dernière ligne du journal :")
    print(last)
    try:
        obj = json.loads(last)
        print("\nChamps clés:")
        print(" run_id    =", obj.get("run_id"))
        print(" version   =", obj.get("version"))
        print(" context   =", obj.get("context"))
        print(" score     =", obj.get("score"))
        print(" policy    =", obj.get("policy"))
    except json.JSONDecodeError:
        print("⚠️ Ligne finale non-JSON")
