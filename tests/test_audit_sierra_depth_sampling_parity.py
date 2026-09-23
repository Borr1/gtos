from __future__ import annotations

import pytest

from scripts import audit_sierra_depth_sampling_parity as mod


def test_sample_coverage_counts_common_and_source_only_seconds():
    out = mod.sample_coverage(
        {
            10: {"total_depth10": 1},
            11: {"total_depth10": 1},
            12: {"total_depth10": 1},
        },
        {
            11: {"total_depth10": 1},
            12: {"total_depth10": 1},
            13: {"total_depth10": 1},
        },
    )

    assert out["sierra_count"] == 3
    assert out["databento_count"] == 3
    assert out["common_count"] == 2
    assert out["sierra_only_count"] == 1
    assert out["databento_only_count"] == 1
    assert out["coverage_jaccard"] == pytest.approx(0.5)


def test_second_iso_uses_unix_epoch_seconds():
    assert mod.second_iso(0) == "1970-01-01T00:00:00+00:00"


def test_build_window_audit_detects_sampling_clock_only_common_match():
    sierra_samples = {
        1: {"total_depth10": 100, "depth10_imbalance": 0.0, "near_far_ratio": 0.3, "max_bid_wall10": 10, "max_ask_wall10": 10, "mid_px": 100.0},
        2: {"total_depth10": 110, "depth10_imbalance": 0.1, "near_far_ratio": 0.4, "max_bid_wall10": 11, "max_ask_wall10": 12, "mid_px": 100.5},
        3: {"total_depth10": 999, "depth10_imbalance": 0.9, "near_far_ratio": 9.0, "max_bid_wall10": 99, "max_ask_wall10": 99, "mid_px": 101.0},
    }
    databento_samples = {
        1: {"total_depth10": 100, "depth10_imbalance": 0.0, "near_far_ratio": 0.3, "max_bid_wall10": 10, "max_ask_wall10": 10, "mid_px": 100.0},
        2: {"total_depth10": 110, "depth10_imbalance": 0.1, "near_far_ratio": 0.4, "max_bid_wall10": 11, "max_ask_wall10": 12, "mid_px": 100.5},
    }

    out = mod.build_window_audit(
        prefix="event15",
        sierra_samples=sierra_samples,
        databento_samples=databento_samples,
        tick_size=0.5,
    )

    assert out["classification"] == "SAMPLING_CLOCK_ONLY_COMMON_SECONDS_EXACT"
    assert out["coverage"]["common_count"] == 2
    assert out["all_seconds"]["delta_summary"]["max_abs_delta"] > 0
    assert out["common_seconds"]["delta_summary"]["max_abs_delta"] == 0


def test_build_window_audit_detects_source_difference_on_common_seconds():
    sierra_samples = {
        1: {"total_depth10": 80, "depth10_imbalance": -0.1, "near_far_ratio": 0.2, "max_bid_wall10": 4, "max_ask_wall10": 8, "mid_px": 100.0},
        2: {"total_depth10": 90, "depth10_imbalance": -0.2, "near_far_ratio": 0.2, "max_bid_wall10": 4, "max_ask_wall10": 8, "mid_px": 100.5},
    }
    databento_samples = {
        1: {"total_depth10": 120, "depth10_imbalance": 0.1, "near_far_ratio": 0.4, "max_bid_wall10": 8, "max_ask_wall10": 4, "mid_px": 100.0},
        2: {"total_depth10": 130, "depth10_imbalance": 0.2, "near_far_ratio": 0.4, "max_bid_wall10": 8, "max_ask_wall10": 4, "mid_px": 100.5},
    }

    out = mod.build_window_audit(
        prefix="event15",
        sierra_samples=sierra_samples,
        databento_samples=databento_samples,
        tick_size=0.5,
    )

    assert out["classification"] == "SOURCE_OR_DEPTH_DEFINITION_DIFFERENCE_REMAINS"
    assert out["common_seconds"]["delta_summary"]["max_abs_delta"] > 0
