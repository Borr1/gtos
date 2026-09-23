from __future__ import annotations

import pandas as pd
import pytest

from scripts import analyze_orderflow_depth_mbp10_features as mod


def _row(ts: str, bid0: float, ask0: float, bid_sizes: list[int], ask_sizes: list[int]) -> dict:
    row = {"ts_event": pd.Timestamp(ts), "symbol": "NQ.v.0", "bid_px_00": bid0, "ask_px_00": ask0}
    for idx in range(10):
        tag = f"{idx:02d}"
        row[f"bid_px_{tag}"] = bid0 - 0.25 * idx
        row[f"ask_px_{tag}"] = ask0 + 0.25 * idx
        row[f"bid_sz_{tag}"] = bid_sizes[idx]
        row[f"ask_sz_{tag}"] = ask_sizes[idx]
    return row


def test_ladder_stats_computes_depth10_features():
    df = pd.DataFrame(
        [
            _row("2026-04-28T10:00:00Z", 100.0, 100.25, [10] * 10, [5] * 10),
            _row("2026-04-28T10:00:01Z", 100.25, 100.5, [4] * 10, [8] * 10),
        ]
    )
    out = mod.ladder_stats(df, "NQ.v.0", "event15", thin_threshold=130)
    assert out["event15_sample_count"] == 2
    assert out["event15_median_spread_ticks"] == 1
    assert out["event15_median_total_depth10"] == 135
    assert out["event15_median_depth10_imbalance"] == pytest.approx(0.0)
    assert out["event15_thin_depth10_rate"] == pytest.approx(0.5)
    assert out["event15_mid_change_ticks"] == 1


def test_candidate_context_by_symbol_returns_deltas():
    rows = [
        {
            "symbol": "NAS100",
            "is_primary_proxy": True,
            "data_status": "ok",
            "event_class": "candidate",
            "event15_median_total_depth10": 100,
        },
        {
            "symbol": "NAS100",
            "is_primary_proxy": True,
            "data_status": "ok",
            "event_class": "structural_context",
            "event15_median_total_depth10": 120,
        },
    ]
    out = mod.candidate_context_by_symbol(rows)
    assert out["NAS100"]["candidate"]["n"] == 1
    assert out["NAS100"]["candidate_minus_context"]["event15_median_total_depth10"] == -20


def test_primary_proxy_uses_current_manifest_map_for_expanded_symbols():
    assert mod.is_primary_proxy("XAGUSD", "SI.v.0") is True
    assert mod.is_primary_proxy("GBPUSD", "6B.v.0") is True
    assert mod.is_primary_proxy("US30_cash", "YM.v.0") is True
    assert mod.is_primary_proxy("US30_cash", "ES.v.0") is False
