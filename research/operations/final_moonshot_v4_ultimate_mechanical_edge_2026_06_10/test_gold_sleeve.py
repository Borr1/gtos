"""Regression test: pins the gold sleeve reference to its audited reproduction.
Guards against silent drift in entry/gate/sizing. Uses tested geometry_lib fills."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gold_sleeve_strategy as g

def test_backtest_reproduces_audited_edge():
    r = g.backtest(risk_per_unit=0.0025)
    assert r["n_trades"] >= 500, r["n_trades"]
    assert 0.15 <= r["full_per_trade_R"] <= 0.30, r["full_per_trade_R"]   # audited ~+0.22R
    assert r["pos_years"] >= 7, r["per_year_R"]                          # >=7/12 positive years
    assert r["per_year_R"].get(2025, -9) > 0 and r["per_year_R"].get(2026, -9) > 0  # forward positive
    assert r["ftmo_ok"] is True                                          # 0.25%/unit is FTMO-safe

def test_conservative_sizing_is_ftmo_safe_aggressive_is_not():
    assert g.backtest(0.0025)["ftmo_ok"] is True
    assert g.backtest(0.01)["ftmo_ok"] is False   # honest: 1.0%/unit breaches at fixed gate/full period

def test_gate_reduces_tradecount_vs_ungated():
    gated = g.backtest(0.0025, gate_k=1.2)["n_trades"]
    loose = g.backtest(0.0025, gate_k=0.0)["n_trades"]
    assert loose > gated, (loose, gated)   # the vol gate is selective
