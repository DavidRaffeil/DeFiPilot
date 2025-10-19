import csv

from core.execution import journal


def test_enregistrer_liquidite_dryrun(tmp_path, monkeypatch):
    path = tmp_path / "journal_liquidite.csv"
    monkeypatch.setattr(journal, "JOURNAL_LIQUIDITE", path)
    data = {
        "platform": "Uniswap",
        "chain": "Polygon",
        "tokenA_symbol": "USDC",
        "tokenB_symbol": "ETH",
        "amountA": 100,
        "amountB": 0.1,
        "lp_tokens_estimes": 1.23,
        "slippage_applique_pct": 0.5,
        "ratio_contraint": False,
        "details": "test",
    }
    journal.enregistrer_liquidite_dryrun(data)
    assert path.exists()
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["platform"] == "Uniswap"
    assert rows[0]["tokenA"] == "USDC"