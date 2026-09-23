from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "research/science_program_2026_05/06_outcome_testing/"
    "vnext_full_historical_candidate_generation_replay_2026_05_24/"
    "build_vnext_full_replay_stage03_runtime_trace_2026_05_24.py"
)


def load_stage03_module():
    spec = importlib.util.spec_from_file_location("vnext_full_stage03", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _candidate() -> dict:
    return {
        "candidate_id": "cand_test",
        "source_universe_row_id": "denom_test",
        "market_state_packet_id": "msp_test",
        "source_origin": "market_bar_enumeration",
        "source_path": "data/test/XAUUSD_M15.csv",
        "source_sha256": "abc123",
        "source_mode": "OHLC_M15_CSV",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "timeframe": "M15",
        "market_timeframe": "M15",
        "session_bucket": "ny_broad",
        "date_utc": "2026-05-01",
        "candle_time_utc": "2026-05-01 13:30:00",
        "side": "LONG",
        "framework": "ob_retest",
        "entry_reference": 2300.0,
        "stop_or_invalidation": 2290.0,
        "target_reference": 2315.0,
        "rr": 1.5,
        "entry_variant": "zone_midpoint",
        "target_stop_class": "min_rr_projection",
        "poi_type": "ob_retest",
        "setup_type": "order_block_retest",
        "zone_id": "ob_test",
    }


def _cache_row(stage03, mode: str) -> dict:
    return {
        "runtime_event_cache_id": "rtevt_test",
        "runtime_surface_call_status": "ok",
        "runtime_truth_class": "actual_current_runtime_surfaces_on_replay_constructed_candidate_event",
        "direct_decision": {
            "decision": "FOLLOW",
            "matched": True,
            "reason": "matched_vnext_scope",
            "evidence": {
                "matched_rows": 1,
                "matched_row_id_count": 1,
                "matched_row_ids": ["row_direct"],
                "matched_row_ids_truncated": False,
            },
        },
        "route_decision": {
            "decision": "MIXED",
            "matched": True,
            "reason": "matched_vnext_route_scope",
            "evidence": {
                "matched_rows": 2,
                "matched_row_id_count": 2,
                "matched_row_ids": ["row_a", "row_b"],
                "matched_row_ids_truncated": False,
                "decision_counts": {"FOLLOW": 1, "AVOID": 1},
                "decision_resolution": {"policy": "evidence_weighted"},
                "metrics": {"effective_n": {"sum": 12}},
            },
        },
        "pre_ai_decision": {
            "action": "ALLOW_AI",
            "would_action": "NARROW_AI_TO_ROUTE",
            "decision": "FOLLOW",
            "reason": "matched_pre_ai_vnext_scope",
            "recommended_side": "LONG",
            "recommended_frameworks": ["ob_retest"],
            "blocked_sides": [],
            "blocked_frameworks": [],
        },
        "risk_adjustment": {
            "reason": f"{mode}_risk_reason",
            "would_multiplier": 1.25,
            "applied": mode == "hypothetical_activated_vnext",
        },
        "pending_policy": {
            "action": "PLACE_LIMIT",
            "would_action": "PLACE_LIMIT",
            "reason": "legacy_pending_policy",
        },
    }


def test_runtime_event_from_candidate_maps_session_and_framework_scope():
    stage03 = load_stage03_module()
    event = stage03.runtime_event_from_candidate(_candidate())

    assert event["route_session"] == "ny"
    assert event["kill_zone"] == "ny"
    assert event["side"] == "LONG"
    assert event["direction"] == "LONG"
    assert event["framework"] == "ob_retest"
    assert event["route_family"] == "ob_retest"
    assert event["entry_variant"] == "zone_midpoint"
    assert event["target_stop_order_class"] == "min_rr_projection"


def test_event_cache_key_excludes_candle_time_but_preserves_decision_scope():
    stage03 = load_stage03_module()
    candidate = _candidate()
    event = stage03.runtime_event_from_candidate(candidate)
    raw_data = stage03.raw_data_from_candidate(candidate, event)
    key = stage03.event_cache_key(event, raw_data)

    assert key["cache_excludes_candle_time"] is True
    assert "candle_close_utc" not in key["raw_data_decision_scope"]
    assert key["event"]["symbol"] == "XAUUSD"


def test_trace_row_preserves_runtime_trace_boundary_and_next_actions():
    stage03 = load_stage03_module()
    candidate = _candidate()
    event = stage03.runtime_event_from_candidate(candidate)
    raw_data = stage03.raw_data_from_candidate(candidate, event)
    raw_data["pre_ai_bias_proxy"] = stage03.bias_from_side(candidate["side"])
    row = stage03.trace_row_for_candidate(
        candidate=candidate,
        mode="current_config_shadow",
        event=event,
        raw_data=raw_data,
        cache_row=_cache_row(stage03, "current_config_shadow"),
    )

    assert row["source_origin"] == "market_bar_enumeration"
    assert row["runtime_surface_call_status"] == "ok"
    assert row["path_truth_status"] == "pending_stage04_path_r_simulation"
    assert row["m15_blindness_status"] == "pending_stage04_lower_timeframe_disagreement_measurement"
    assert row["repair_state"]["remaining_source_mode_actions"].startswith("execute_or_repair")
    assert row["no_live_trading_or_broker_mutation"] is True
    assert [step["stage_name"] for step in row["causal_decision_steps"]] == [
        "stage03_runtime_event_construction",
        "pre_ai_vnext_runtime_surface",
        "post_l2_route_vnext_runtime_surface",
        "risk_vnext_runtime_surface",
        "pending_policy_vnext_runtime_surface",
    ]
