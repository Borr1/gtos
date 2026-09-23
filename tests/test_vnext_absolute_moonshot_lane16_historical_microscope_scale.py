from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = (
    ROOT
    / "research"
    / "operations"
    / "vnext_absolute_moonshot_lane16_historical_microscope_scale_2026_06_01"
    / "build_vnext_absolute_moonshot_lane16_historical_microscope_scale.py"
)

spec = importlib.util.spec_from_file_location("lane16_builder", BUILDER_PATH)
lane16 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = lane16
spec.loader.exec_module(lane16)


def test_lane16_event_row_preserves_timeline_and_gap_proof():
    timeline = {
        "row_id": "stage04_order_test",
        "selected_row_id": "stage04_order_test",
        "candidate_id": "cand_test",
        "symbol": "XAUUSD",
        "side": "LONG",
        "framework": "ob_retest",
        "origin_family": "current_ob_retest",
        "session_bucket": "london",
        "source_time_utc": "2026-01-02T09:00:00+00:00",
        "entry_time_utc": "2026-01-02T09:01:00+00:00",
        "exit_time_utc": "2026-01-02T10:00:00+00:00",
        "date": "2026-01-02",
        "month": "2026-01",
        "year": "2026",
        "timeline_source_family": "lane04_test",
        "path_class": "loss_sl_or_stop_policy_exit",
        "source_use_state": "m15_ordered_path_proxy_with_m1_availability_state",
        "final_r": -1.0,
        "mfe_r": 0.25,
        "mae_r": -1.1,
        "ordered_events": [{"event_type": "entry_touch", "time_utc": "2026-01-02T09:01:00+00:00"}],
        "missing_field_proof": [
            {
                "field_family": "ordered_bid_ask_tick_timeline",
                "reason": "test_gap",
                "repair_requirement": "test_repair",
            }
        ],
    }
    sidecars = {name: None for name in ("feature", "label", "replay", "selector", "scheduler", "reconciliation", "conflict", "policy")}

    row = lane16.build_microscope_event(timeline, sidecars)

    assert row["row_id"] == "stage04_order_test"
    assert row["source_gap_count"] >= 1
    assert "ordered_bid_ask_tick_timeline" in row["source_gap_families"]
    assert row["cross_lane_materialization_state"] == "partial_cross_lane_microscope_join_with_source_gaps"
    assert any(event["event_type"] == "execution_policy_simulation_materialized" for event in row["ordered_events"])


def test_lane16_policy_mapper_extracts_current_and_best_policy():
    mapped = lane16.policy_mapper(
        {
            "row_id": "policy_row",
            "current_router_policy": "momentum_exhaustion",
            "policy_results": {
                "current_router_policy": {
                    "gross_r": 0.8,
                    "cost_adjusted_median_r": 0.7,
                    "cost_adjusted_high_stress_r": 0.5,
                    "price_path_model": "m15_ordered_path_proxy",
                    "bid_ask_ordering_state": "m15_proxy_no_tick_bid_ask_order",
                },
                "momentum_exhaustion": {"gross_r": 0.8, "cost_adjusted_median_r": 0.7},
                "partial_be_runner": {"gross_r": 1.2, "cost_adjusted_median_r": 1.1},
            },
        }
    )

    assert mapped["current_router_policy"] == "momentum_exhaustion"
    assert mapped["current_policy_cost_adjusted_median_r"] == 0.7
    assert mapped["best_policy_id"] == "partial_be_runner"
    assert mapped["best_policy_cost_adjusted_median_r"] == 1.1


def test_lane16_written_route_outputs_verify_without_rebuild():
    result = lane16.verify_outputs(write=False)

    assert result["ok"] is True
    assert result["event_rows"] == result["path_anatomy_rows"]
    assert result["source_gap_rows"] > result["event_gap_rows"]
    assert result["coverage_symbol_count"] >= 24
