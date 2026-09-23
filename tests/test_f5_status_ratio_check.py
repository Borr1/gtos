"""`f5_status._ratio_verdict` must pass correct wiring at ANY selected-cell risk.

The defect this pins, from the live VPS on 2026-08-12: the notional/actual check used a fixed
50-500x OK band reasoned from a full-dial trade (2.00 % of $100k / $10 = 200x). The first real
F5 fill selected a 0.2244 % cell, so its honest ratio was $224.40/$9.91 = 22.6x -- the check
would have reported FAIL at 5 closes while the wiring was perfectly correct.

The numbers in `test_live_fill_*` are the real ones from ticket 174957638 (UK100.cash idxrev).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from f5_status import _ratio_verdict  # noqa: E402


def _close(nominal, actual, intended=10.0, **kw):
    row = {"f5_nominal_risk_usd": nominal, "f5_actual_risk_usd": actual,
           "f5_intended_risk_usd": intended,
           "f5_notional_over_actual": (nominal / actual) if actual else None,
           "symbol": "UK100", "sleeve": "idxrev", "ticket": 1}
    row.update(kw)
    return row


# --- the trade that would have false-alarmed -----------------------------------------
def test_live_fill_sub_ceiling_cell_passes():
    """0.2244 % of a $100,000 notional against $9.91 actual == 22.6x. Correct, not a fault."""
    v = _ratio_verdict(_close(nominal=224.40, actual=9.91))
    assert round(v["observed"], 1) == 22.6
    assert v["ok"] is True
    assert v["looks_unwired"] is False


def test_live_fill_would_have_failed_the_old_fixed_band():
    """Regression guard: 22.6x is outside the retired 50-500x band."""
    v = _ratio_verdict(_close(nominal=224.40, actual=9.91))
    assert not (50 <= v["observed"] <= 500)


# --- the check still passes a full-dial trade ----------------------------------------
def test_full_dial_cell_passes():
    v = _ratio_verdict(_close(nominal=2000.0, actual=10.0))
    assert v["observed"] == 200.0 and v["ok"] is True


# --- the failure it exists for ---------------------------------------------------------
def test_unwired_scaler_is_caught():
    """Scaler out of the path: actual == nominal, so the book risks the full dial for real."""
    v = _ratio_verdict(_close(nominal=224.40, actual=224.40))
    assert v["looks_unwired"] is True and v["ok"] is False


def test_round_up_is_allowed_slack_not_a_failure():
    """volume_min round-up raises actual above intended; that is legitimate."""
    v = _ratio_verdict(_close(nominal=224.40, actual=40.0))   # 4x round-up
    assert round(v["roundup"], 2) == 4.0
    assert v["ok"] is True


def test_live_broker_step_underfill_is_allowed_grid_slack():
    """Ordinary broker-step normalisation safely floors $10 to the nearest tradable lot."""
    v = _ratio_verdict(_close(nominal=148.65, actual=9.45, symbol="USDJPY",
                               sleeve="fx_jpy_ny", ticket=175157253))
    assert round(v["observed"], 6) == round(148.65 / 9.45, 6)
    assert v["broker_grid_direction"] == "underfill"
    assert v["ok"] is True
    assert v["looks_unwired"] is False


def test_inconsistent_recorded_ratio_still_fails():
    """Grid slack must not hide a corrupt nominal/actual identity."""
    row = _close(nominal=148.65, actual=9.45)
    row["f5_notional_over_actual"] = 9.0
    v = _ratio_verdict(row)
    assert v["ok"] is False


def test_incomplete_row_returns_none_rather_than_a_verdict():
    assert _ratio_verdict({"f5_nominal_risk_usd": 224.4}) is None
    assert _ratio_verdict(_close(nominal=224.4, actual=0.0)) is None
