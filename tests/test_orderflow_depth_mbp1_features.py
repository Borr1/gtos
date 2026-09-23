from __future__ import annotations

import pandas as pd
import pytest

from scripts import analyze_orderflow_depth_mbp1_features as mod


def test_depth_stats_computes_top_book_features():
    df = pd.DataFrame(
        {
            "ts_event": pd.to_datetime(
                ["2026-04-17T12:00:00Z", "2026-04-17T12:01:00Z", "2026-04-17T12:02:00Z"],
                utc=True,
            ),
            "bid_px_00": [100.0, 100.25, 100.5],
            "ask_px_00": [100.25, 100.5, 100.75],
            "bid_sz_00": [10, 4, 2],
            "ask_sz_00": [2, 4, 10],
        }
    )
    out = mod.depth_stats(df, "NQ.v.0", "event15", thin_threshold=8)
    assert out["event15_update_count"] == 3
    assert out["event15_median_spread_ticks"] == 1
    assert out["event15_median_book_imbalance"] == 0
    assert out["event15_last_book_imbalance"] == pytest.approx(-0.6666666667)
    assert out["event15_thin_top_book_rate"] == pytest.approx(1 / 3)
    assert out["event15_mid_change_ticks"] == 2


def test_attach_outcomes_uses_normalized_symbol_key():
    rows = [
        {
            "symbol": "US30_cash",
            "canonical_m15_close_utc": "2026-04-17T15:00:00+00:00",
        }
    ]
    outcome_index = {
        ("US30", "2026-04-17T15:00:00+00:00"): {
            "candidate__synthetic_realized_r": -1.0,
            "candidate__synthetic_outcome": "SL",
            "candidate__realized_r": None,
            "candidate__realized_r_available": False,
        }
    }
    mod.attach_outcomes(rows, outcome_index)
    assert rows[0]["candidate_outcome_join_matched"] is True
    assert rows[0]["candidate__synthetic_realized_r"] == -1.0


def test_primary_proxy_uses_current_manifest_map_for_expanded_symbols():
    assert mod.is_primary_proxy("XAGUSD", "SI.v.0") is True
    assert mod.is_primary_proxy("GBPUSD", "6B.v.0") is True
    assert mod.is_primary_proxy("US30_cash", "YM.v.0") is True
    assert mod.is_primary_proxy("US30_cash", "ES.v.0") is False
