from __future__ import annotations

from scripts import build_vnext_lane01_fixed_friday_portfolio_replay as lane01


EXPECTED_ACCEPTED_IDS = [
    "AUDJPY_2026-05-29_london_0715",
    "EURJPY_2026-05-29_london_0715",
    "GBPJPY_2026-05-29_london_0715",
    "GBPUSD_2026-05-29_london_0715",
    "AUDJPY_2026-05-29_london_0745",
    "XAUUSD_2026-05-29_london_0800",
    "CHFJPY_2026-05-29_london_0830",
    "EURUSD_2026-05-29_london_0830",
    "AUDJPY_2026-05-29_london_0900",
    "AUDUSD_2026-05-29_london_0900",
    "EURUSD_2026-05-29_london_0915",
    "EURGBP_2026-05-29_london_1100",
    "UKOIL_cash_2026-05-29_london_1100",
    "USOIL_cash_2026-05-29_london_1100",
    "USDCHF_2026-05-29_london_1115",
    "USDCAD_2026-05-29_london_1130",
    "GER40_2026-05-29_london_1200",
    "USDCAD_2026-05-29_london_1200",
]


def test_lane01_partial_be_lifecycle_cash_contract():
    assert lane01.lifecycle_cash_events(2.0, 1000.0) == {
        "partial_release_realized_dollars": 500.0,
        "final_close_realized_dollars": 1500.0,
    }
    assert lane01.lifecycle_cash_events(0.5, 1000.0) == {
        "partial_release_realized_dollars": 500.0,
        "final_close_realized_dollars": 0.0,
    }
    assert lane01.lifecycle_cash_events(-1.0, 1000.0) == {
        "partial_release_realized_dollars": 0.0,
        "final_close_realized_dollars": -1000.0,
    }

    state = lane01.lifecycle_cash_state_at(
        {
            "gross_r": 2.0,
            "effective_risk_amount": 1000.0,
            "effective_gross_dollars": 2000.0,
            "partial_trigger_utc": "2026-05-29T08:00:00+00:00",
            "final_close_utc": "2026-05-29T10:00:00+00:00",
        },
        lane01.parse_dt("2026-05-29T09:00:00+00:00"),
    )
    assert state["realized_effective_pnl_dollars"] == 500.0
    assert state["scheduled_open_effective_pnl_dollars"] == 1500.0
    assert state["final_closed"] is False


