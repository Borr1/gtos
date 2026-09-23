from __future__ import annotations

from scripts import build_cost_slippage_exit_coverage as mod


def test_cost_coverage_counts_entry_spread_and_slippage():
    payload = mod.build_payload(
        slippage_rows=[
            {"spread_at_request": 10.0, "slippage_directional": 0.1},
            {"spread_at_request": None, "slippage_directional": None},
            {
                "slippage_event_type": "close",
                "slippage_directional": 0.2,
                "commission": -0.7,
                "swap": 0.0,
                "mt5_deal_id": 123,
            },
        ],
        time_in_trade_rows=[{"trade_id": "t1"}],
        lifecycle_rows=[{"actual_r": None}, {"actual_r": -1.0}],
    )

    assert payload["coverage"]["slippage_rows"] == 3
    assert payload["coverage"]["entry_slippage_log_rows"] == 2
    assert payload["coverage"]["close_slippage_log_rows"] == 1
    assert payload["coverage"]["entry_spread_rows"] == 1
    assert payload["coverage"]["entry_slippage_rows"] == 1
    assert payload["coverage"]["close_slippage_rows"] == 1
    assert payload["coverage"]["close_commission_rows"] == 1
    assert payload["coverage"]["close_swap_rows"] == 1
    assert payload["coverage"]["close_deal_id_rows"] == 1
    assert payload["coverage"]["close_side_cost_rows"] == 4
    assert payload["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_render_md_contains_blocker():
    payload = mod.build_payload(slippage_rows=[], time_in_trade_rows=[], lifecycle_rows=[])
    md = mod.render_md(payload)
    assert "Close-side spread/cost" in md
    assert "NO_PROMOTION_VERDICT" in md
