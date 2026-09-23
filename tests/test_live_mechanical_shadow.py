from __future__ import annotations

import json
from pathlib import Path

from src.research_infra.live_mechanical_shadow import (
    build_strategy_outcome_rows,
    entry_reference_metrics,
    latest_ltf_for_candidate_asof,
    latest_path_rows_by_candidate,
    path_outcome_status,
    run,
)


def _assert_full_opportunity_preservation(row: dict) -> None:
    required = (
        "opportunity_preservation_status",
        "opportunity_owner_row_id",
        "opportunity_owner_source_artifact",
        "opportunity_proxy_reference_status",
        "opportunity_not_independently_countable_reason",
        "opportunity_useful_mechanism",
        "opportunity_downstream_paths",
    )
    for field in required:
        assert row.get(field) not in (None, "", [])
    assert row["underlying_intelligence_preserved"] is True
    assert isinstance(row.get("missed_opportunity_audit"), dict)
    for field in (
        "kill_scope",
        "current_claim",
        "unsupported_reason",
        "what_was_tried",
        "what_could_make_it_work",
        "preserve_as",
        "next_route",
    ):
        assert row["missed_opportunity_audit"].get(field) not in (None, "", [])


def _assert_cp281_event_contract(row: dict) -> None:
    for field in (
        "symbol",
        "source_symbol",
        "symbol_family",
        "market_timeframe",
        "route_session",
        "horizon_id",
        "side",
        "source_path_sha256",
        "source_file_sha256",
    ):
        assert row.get(field) not in (None, ""), field


def _candidate() -> dict:
    return {
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "trade_id": "lim_2026-05-04_0715",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "session": "london",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "side": "SHORT",
        "framework": "ob_retest",
        "final_outcome_at_log": "LIMIT_PLACED",
        "strategy_snapshots": [
            {
                "strategy_id": "LIVE_AI_J46_J49_BASELINE_COMPARATOR",
                "family": "current_live_baseline",
                "evidence_role": "baseline_comparator",
                "applicability": "candidate_relevant",
                "result_use_status": "LIVE_PRODUCTION_PATH",
            },
            {
                "strategy_id": "V2_STRUCT_OB_BOUNDARY",
                "family": "v2_structural_selector",
                "evidence_role": "cleanest_v2b_candidate",
                "applicability": "candidate_relevant",
                "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
            },
            {
                "strategy_id": "V3_OB_LOCK_PULLBACK_RISK_BANK",
                "family": "v3_risk_bank",
                "evidence_role": "locked_progress_reentry_comparator",
                "applicability": "candidate_relevant",
                "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
            },
        ],
    }


def _candidate_with_moonshot_strategy(strategy_id: str) -> dict:
    candidate = json.loads(json.dumps(_candidate()))
    candidate["strategy_snapshots"].append(
        {
            "strategy_id": strategy_id,
            "family": "moonshot_nofill_redesign",
            "evidence_role": "default_off_selected_action",
            "applicability": "candidate_relevant",
            "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
            "branch_decision": "IMPLEMENT_DEFAULT_OFF_FAR_MISS_RETEST_REDESIGN_VARIANT",
            "decision_evidence": "unit-test selected action evidence",
            "implementation_candidate": "CAPTURE_AND_SCORE_DEFAULT_OFF_MOONSHOT_TEST",
            "source_capture_required_fields": (
                "moonshot_far_miss_retest_control_key",
                "moonshot_no_fill_distance_bucket",
            ),
        }
    )
    return candidate


def _candidate_with_nas100_depth_strategy() -> dict:
    candidate = json.loads(json.dumps(_candidate()))
    candidate.update(
        {
            "candidate_id": "NAS100_2026-05-04T13:15:00+00:00",
            "trade_id": None,
            "symbol": "NAS100",
            "broker_symbol": "NDX100",
            "decision_time_utc": "2026-05-04T13:15:00+00:00",
            "side": "LONG",
        }
    )
    candidate["strategy_snapshots"].append(
        {
            "strategy_id": "NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC",
            "family": "orderflow_depth",
            "evidence_role": "nas100_specific_forward_diagnostic",
            "applicability": "candidate_relevant",
            "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
        }
    )
    return candidate


def _path() -> dict:
    return {
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "trade_id": "lim_2026-05-04_0715",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "route_session": "fallback_london",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T07:45:00+00:00",
        "side": "SHORT",
        "framework": "ob_retest",
        "path_label": "continued_without_entry_touch_to_tp_area",
        "touched_entry": False,
        "hit_tp1": True,
        "hit_sl": False,
        "bars_elapsed": 3,
        "min_low": 4605.06,
        "max_high": 4613.11,
        "last_close": 4605.89,
        "nearest_abs_distance_to_entry": 55.34,
        "nearest_distance_to_entry_r": 4.686,
        "entry_touch_distance_status": "FAR_MISS_GT_0_25R",
        "m15_spread_source_status": "SPREAD_CAPTURED",
        "m15_spread_count": 3,
        "m15_spread_min": 8,
        "m15_spread_max": 12,
        "m15_spread_mean": 10,
        "m15_tick_volume_source_status": "TICK_VOLUME_CAPTURED",
        "m15_tick_volume_count": 3,
        "m15_tick_volume_min": 80,
        "m15_tick_volume_max": 120,
        "m15_tick_volume_mean": 100,
        "m15_real_volume_source_status": "REAL_VOLUME_CAPTURED",
        "m15_real_volume_count": 3,
        "m15_real_volume_min": 1,
        "m15_real_volume_max": 3,
        "m15_real_volume_mean": 2,
        "trade_parameters": {
            "direction": "SHORT",
            "entry_price": 4668.45,
            "stop_loss": 4680.26,
            "take_profit_1": 4650.73,
        },
    }


def _nas100_path() -> dict:
    path = json.loads(json.dumps(_path()))
    path.update(
        {
            "candidate_id": "NAS100_2026-05-04T13:15:00+00:00",
            "trade_id": None,
            "symbol": "NAS100",
            "broker_symbol": "NDX100",
            "decision_time_utc": "2026-05-04T13:15:00+00:00",
            "asof_latest_candle_utc": "2026-05-04T14:15:00+00:00",
            "side": "LONG",
        }
    )
    return path


def _ambiguous_path() -> dict:
    row = json.loads(json.dumps(_path()))
    row.update(
        {
            "path_label": "entry_touched_tp_and_sl_m15_ambiguous",
            "touched_entry": True,
            "hit_tp1": True,
            "hit_sl": True,
        }
    )
    return row


def _ltf(
    status: str,
    *,
    event: str | None = "2026-05-04T07:35:00+00:00",
    r_value: float | None = -1.0,
    tp1_first_touch_utc: str | None = None,
    sl_first_touch_utc: str | None = None,
) -> dict:
    row = {
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T07:45:00+00:00",
        "created_at_utc": "2026-05-04T07:45:05+00:00",
        "path_order_label": "entry_then_sl_before_tp1",
        "terminal_outcome_status": status,
        "terminal_event_utc": event,
        "terminal_event_r": r_value,
        "terminal_order_ambiguity": r_value is None,
    }
    if tp1_first_touch_utc is not None:
        row["tp1_first_touch_utc"] = tp1_first_touch_utc
    if sl_first_touch_utc is not None:
        row["sl_first_touch_utc"] = sl_first_touch_utc
    return row


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _candidate_with_pending_strategy() -> dict:
    candidate = json.loads(json.dumps(_candidate()))
    candidate["strategy_snapshots"].append(
        {
            "strategy_id": "PENDING_LIMIT_LIFECYCLE",
            "family": "pending_limit_lifecycle",
            "evidence_role": "internal_limit_lifecycle",
            "applicability": "candidate_relevant",
            "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
        }
    )
    return candidate


def _candidate_with_structural_sources() -> dict:
    candidate = json.loads(json.dumps(_candidate()))
    candidate["decision_time_structural_fields"] = {
        "fields": {
            "standalone_fvg_entry_geometry": {"source_status": "DECISION_TIME_SOURCE_CAPTURED"},
            "fvg_lock_state": {
                "source_status": "DECISION_TIME_SOURCE_CAPTURED_PATH_DERIVATION_PENDING"
            },
            "swing_protected_lock_level": {"source_status": "DECISION_TIME_SOURCE_CAPTURED"},
            "structural_lock_event_time_price": {
                "source_status": "FORWARD_PATH_EVENT_PENDING_DECISION_TIME_SEED_CAPTURED"
            },
            "post_lock_reentry_state": {
                "source_status": "FORWARD_PATH_EVENT_PENDING_DECISION_TIME_SEED_CAPTURED"
            },
            "cost_aware_min_r_fields": {"source_status": "DECISION_TIME_SOURCE_CAPTURED"},
        }
    }
    return candidate


def _candidate_with_fvg_ob_strategy(*, structural_sources: bool = True) -> dict:
    candidate = _candidate_with_structural_sources() if structural_sources else json.loads(json.dumps(_candidate()))
    candidate["strategy_snapshots"].append(
        {
            "strategy_id": "FVG_OB_CONFLUENCE_OB_AFTER_FVG",
            "family": "fvg_ob_confluence",
            "evidence_role": "forward_confluence_bucket",
            "applicability": "candidate_relevant",
            "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
        }
    )
    return candidate


def _candidate_with_fvg_strategy(*, structural_sources: bool = True) -> dict:
    candidate = _candidate_with_structural_sources() if structural_sources else json.loads(json.dumps(_candidate()))
    candidate["strategy_snapshots"].append(
        {
            "strategy_id": "V2_STRUCT_FVG_MID_EDGE",
            "family": "v2_structural_selector",
            "evidence_role": "discovery_comparator",
            "applicability": "candidate_relevant",
            "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
        }
    )
    return candidate


def _candidate_with_selected_fvg_strategy() -> dict:
    candidate = _candidate_with_fvg_strategy(structural_sources=True)
    fields = candidate["decision_time_structural_fields"]["fields"]
    fields["standalone_fvg_entry_geometry"] = {
        "source_status": "DECISION_TIME_SOURCE_CAPTURED",
        "candidate_h1_poi_type": "FVG",
        "candidate_h1_poi_price_level": 4668.45,
        "candidate_entry_price": 4668.45,
        "h1_fair_value_gaps": [
            {
                "bottom": 4667.0,
                "top": 4670.0,
                "midpoint": 4668.5,
                "type": "bearish",
                "formation_time": "2026-05-04T06:00:00+00:00",
            }
        ],
        "m15_fair_value_gaps": [],
    }
    return candidate


def _candidate_with_swing_protected_strategy(*, protects: bool = True) -> dict:
    candidate = _candidate_with_structural_sources()
    candidate["strategy_snapshots"].append(
        {
            "strategy_id": "V2_STRUCT_SWING_PROTECTED",
            "family": "v2_structural_selector",
            "evidence_role": "discovery_comparator_concentration_blocked",
            "applicability": "candidate_relevant",
            "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
        }
    )
    fields = candidate["decision_time_structural_fields"]["fields"]
    fields["cost_aware_min_r_fields"] = {
        "source_status": "DECISION_TIME_SOURCE_CAPTURED",
        "candidate_geometry": {
            "direction": "SHORT",
            "entry_price": 4668.45,
            "stop_loss": 4680.26,
            "take_profit_1": 4650.73,
        },
    }
    fields["swing_protected_lock_level"] = {
        "source_status": "DECISION_TIME_SOURCE_CAPTURED",
        "h1_protected_swing": {
            "price": 4679.0 if protects else 4682.0,
            "time": "2026-05-04T06:30:00+00:00",
            "type": "high",
        },
        "m15_protected_swing": None,
    }
    return candidate


def _candidate_with_prefill_strategy() -> dict:
    candidate = json.loads(json.dumps(_candidate()))
    candidate["strategy_snapshots"].append(
        {
            "strategy_id": "PREFILL_DELIVERY_REVERSAL_PATH",
            "family": "prefill_delivery",
            "evidence_role": "delivery_reversal_redesign_candidate",
            "applicability": "candidate_relevant",
            "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
        }
    )
    return candidate


def _as_gbpjpy_long(candidate: dict) -> dict:
    candidate = json.loads(json.dumps(candidate))
    candidate.update(
        {
            "candidate_id": "GBPJPY_2026-05-04T02:15:00+00:00",
            "trade_id": "lim_2026-05-04_0215",
            "symbol": "GBPJPY",
            "broker_symbol": "GBPJPY",
            "side": "LONG",
            "trade_parameters": {
                "direction": "LONG",
                "entry_price": 190.0,
                "stop_loss": 189.0,
                "take_profit_1": 191.5,
            },
        }
    )
    fields = candidate.get("decision_time_structural_fields", {}).get("fields", {})
    fields["cost_aware_min_r_fields"] = {
        "source_status": "DECISION_TIME_SOURCE_CAPTURED",
        "candidate_geometry": {
            "direction": "LONG",
            "entry_price": 190.0,
            "stop_loss": 189.0,
            "take_profit_1": 191.5,
        },
    }
    fields["swing_protected_lock_level"] = {
        "source_status": "DECISION_TIME_SOURCE_CAPTURED",
        "h1_protected_swing": {
            "price": 189.25,
            "time": "2026-05-04T01:30:00+00:00",
            "type": "low",
        },
        "m15_protected_swing": None,
    }
    return candidate


def _gbpjpy_long_path() -> dict:
    path = json.loads(json.dumps(_path()))
    path.update(
        {
            "candidate_id": "GBPJPY_2026-05-04T02:15:00+00:00",
            "trade_id": "lim_2026-05-04_0215",
            "symbol": "GBPJPY",
            "broker_symbol": "GBPJPY",
            "side": "LONG",
            "decision_time_utc": "2026-05-04T02:15:00+00:00",
            "asof_latest_candle_utc": "2026-05-04T02:45:00+00:00",
            "path_label": "entry_touched_then_sl",
            "touched_entry": True,
            "hit_tp1": False,
            "hit_sl": True,
            "trade_parameters": {
                "direction": "LONG",
                "entry_price": 190.0,
                "stop_loss": 189.0,
                "take_profit_1": 191.5,
            },
        }
    )
    return path


def _candidate_with_entry_offset_strategy() -> dict:
    candidate = json.loads(json.dumps(_candidate()))
    candidate["strategy_snapshots"].append(
        {
            "strategy_id": "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER",
            "family": "entry_geometry_fillability",
            "evidence_role": "default_off_entry_offset_challenger",
            "applicability": "candidate_relevant",
            "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
        }
    )
    return candidate


def _pending_lifecycle(**overrides) -> dict:
    row = {
        "schema_version": "pending_limit_lifecycle_v1",
        "created_at_utc": "2026-05-04T08:01:00+00:00",
        "timestamp_utc": "2026-05-04T08:01:00+00:00",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "candidate_id": None,
        "trade_id": "lim_2026-05-04_0715",
        "side": "SHORT",
        "entry_price": 4668.45,
        "stop_loss": 4680.26,
        "take_profit_1": 4650.73,
        "intent_after_check": "cancelled_wrong_side",
        "fill_no_fill_label": "no_fill_cancelled_wrong_side",
        "checked_candle_time_utc": "2026-05-04T07:45:00+00:00",
        "asof_cutoff_utc": "2026-05-04T07:45:00+00:00",
        "wrong_side_abort": True,
        "broker_fill_state": "not_filled",
    }
    row.update(overrides)
    return row


def _nofill_forward_capture(**overrides) -> dict:
    row = {
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "created_at_utc": "2026-05-04T07:15:30+00:00",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "decision_spread_status": "QUOTE_SNAPSHOT_CAPTURED_SOURCE_SAFE",
        "decision_spread_value_source_safe": 1.25,
        "decision_spread_unit": "spread_cents",
        "schema_version": "nofill_forward_source_capture_v1",
    }
    row.update(overrides)
    return row


def _tick_spread_reconstruction(**overrides) -> dict:
    row = {
        "candidate_id": "XAUUSD_2026-05-04T07:15:00+00:00",
        "created_at_utc": "2026-05-17T00:00:00+00:00",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "decision_spread_status": "TICK_PARQUET_AT_OR_BEFORE_DECISION_WITHIN_2S_SOURCE_SAFE",
        "decision_spread_value_source_safe": 0.55,
        "decision_spread_unit": "spread_cents",
        "tick_ts_utc": "2026-05-04T07:14:59.948000+00:00",
        "tick_offset_seconds": -0.052,
        "tick_source_path": "data/ticks/XAUUSD/2026-05-04.parquet",
        "tick_source_sha256": "abc123",
        "schema_version": "pending_lifecycle_tick_spread_reconstruction_v1",
    }
    row.update(overrides)
    return row


def test_path_outcome_marks_tp_area_without_fill():
    assert path_outcome_status(_path()) == "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH"


def test_entry_reference_metrics_for_short():
    metrics = entry_reference_metrics(_path())

    assert metrics["base_r_price"] == 11.81
    assert metrics["max_favorable_price_from_entry"] == 63.39
    assert metrics["max_adverse_price_from_entry"] == -55.34
    assert metrics["r_metrics_reference"] == "ENTRY_REFERENCE_NOT_REALIZED_UNLESS_ENTRY_TOUCHED"


def test_build_rows_scores_shared_and_marks_missing_v3_metadata():
    rows = build_strategy_outcome_rows(_candidate(), _path(), created_at_utc="2026-05-04T08:00:00+00:00")
    by_id = {row["strategy_id"]: row for row in rows}

    assert by_id["LIVE_AI_J46_J49_BASELINE_COMPARATOR"]["score_status"] == "COMPUTED_FROM_CANDIDATE_PATH"
    assert by_id["V2_STRUCT_OB_BOUNDARY"]["strategy_status"] == "SCORED_OB_BOUNDARY_PROXY_SHARED_CANDIDATE_PATH"
    assert by_id["V3_OB_LOCK_PULLBACK_RISK_BANK"]["score_status"] == "MISSING_REQUIRED_LIVE_METADATA"
    baseline = by_id["LIVE_AI_J46_J49_BASELINE_COMPARATOR"]
    assert baseline["entry_touch_distance_status"] == "FAR_MISS_GT_0_25R"
    assert baseline["route_session"] == "london"
    assert baseline["nearest_distance_to_entry_r"] == 4.686
    assert baseline["entry_retest_redesign_bucket"] == "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE"
    assert baseline["entry_retest_redesign_bucket_basis"] == "M15_RANGE_DISTANCE_TO_ORIGINAL_ENTRY"
    assert (
        baseline["entry_retest_redesign_fill_claim_status"]
        == "NO_FILL_CLAIM_WITHOUT_SPREAD_AWARE_LTF_OR_TICK_REPLAY"
    )
    assert baseline["entry_retest_redesign_tick_replay_requirement"] == "REQUIRED_BEFORE_OFFSET_SCORER_R"
    assert baseline["max_adverse_r_from_entry"] == -4.68585944
    assert baseline["m15_path_provenance_status"] == "M15_SPREAD_SOURCE_CAPTURED"
    assert baseline["m15_spread_mean"] == 10
    assert baseline["m15_tick_volume_mean"] == 100
    assert baseline["m15_real_volume_mean"] == 2
    _assert_cp281_event_contract(baseline)
    structural_missing = by_id["V3_OB_LOCK_PULLBACK_RISK_BANK"]
    assert structural_missing["branch_decision"] == "SOURCE_CAPTURE_REQUIRED_FOR_STRUCTURAL_LOCK_SCORER"
    assert (
        structural_missing["implementation_candidate"]
        == "CAPTURE_STRUCTURAL_LOCK_REENTRY_AND_COST_AWARE_MIN_R_FIELDS"
    )
    assert all(row["no_ai_calls"] is True for row in rows)
    assert all(row["paid_fetch_attempted"] is False for row in rows)


def test_build_rows_redesigns_duplicate_structural_metadata_shared_path_proxy():
    candidate = _candidate_with_structural_sources()
    candidate["strategy_snapshots"].append(
        {
            "strategy_id": "V2_STRUCT_COMPOSITE_ANY",
            "family": "v2_structural_selector",
            "evidence_role": "canonical_structural_shared_path",
            "applicability": "candidate_relevant",
            "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
        }
    )
    rows = build_strategy_outcome_rows(
        candidate,
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    by_id = {row["strategy_id"]: row for row in rows}

    assert by_id["V2_STRUCT_COMPOSITE_ANY"]["strategy_status"] == (
        "SCORED_STRUCTURAL_LOCK_METADATA_PROXY_SHARED_CANDIDATE_PATH"
    )
    assert by_id["V2_STRUCT_COMPOSITE_ANY"]["branch_decision"] == (
        "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_COMPOSITE_CAPTURED_METADATA_SHARED_PATH_SCORER"
    )
    assert by_id["V3_OB_LOCK_PULLBACK_RISK_BANK"]["score_status"] == "COMPUTED_FROM_CANDIDATE_PATH"
    assert by_id["V3_OB_LOCK_PULLBACK_RISK_BANK"]["outcome_status"] == "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH"
    assert by_id["V3_OB_LOCK_PULLBACK_RISK_BANK"]["strategy_proxy_r"] is None
    assert by_id["V3_OB_LOCK_PULLBACK_RISK_BANK"]["structural_duplicate_proxy_reference_r"] == 0.0
    assert (
        by_id["V3_OB_LOCK_PULLBACK_RISK_BANK"]["strategy_status"]
        == "REDESIGN_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY"
    )
    assert (
        by_id["V3_OB_LOCK_PULLBACK_RISK_BANK"]["branch_decision"]
        == "MERGE_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY_INTO_V2_STRUCT_COMPOSITE_ANY"
    )
    assert (
        by_id["V3_OB_LOCK_PULLBACK_RISK_BANK"]["scoring_boundary"]
        == "NO_SEPARATE_V3_STRUCTURAL_LOCK_IMPLEMENTATION_FROM_DUPLICATED_SHARED_CANDIDATE_PATH_PROXY"
    )
    assert (
        by_id["V3_OB_LOCK_PULLBACK_RISK_BANK"]["implementation_candidate"]
        == "MERGE_INTO_CANONICAL_V2_STRUCT_COMPOSITE_ANY_SCORER_NO_DUPLICATE_R"
    )
    assert (
        by_id["V3_OB_LOCK_PULLBACK_RISK_BANK"]["opportunity_proxy_reference_status"]
        == "REFERENCE_ONLY_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_NOT_COUNTED"
    )
    _assert_full_opportunity_preservation(by_id["V3_OB_LOCK_PULLBACK_RISK_BANK"])


def test_fvg_scorer_captured_metadata_becomes_default_off_implementation_candidate():
    rows = build_strategy_outcome_rows(
        _candidate_with_selected_fvg_strategy(),
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    fvg = {row["strategy_id"]: row for row in rows}["V2_STRUCT_FVG_MID_EDGE"]

    assert fvg["strategy_status"] == "SCORED_STANDALONE_FVG_POI_PROXY_CANDIDATE_PATH"
    assert fvg["score_status"] == "COMPUTED_FROM_CANDIDATE_PATH"
    assert fvg["outcome_status"] == "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH"
    assert fvg["strategy_proxy_r"] == 0.0
    assert fvg["branch_decision"] == "IMPLEMENT_SHADOW_SCORER_STANDALONE_FVG_POI_DEFAULT_OFF"
    assert fvg["scoring_boundary"] == "FVG_POI_CANDIDATE_PATH_PROXY_NO_ALTERNATE_ENTRY_SYNTHESIS"
    assert fvg["standalone_fvg_poi_status"] == "SELECTED_FVG_POI_ENTRY_GEOMETRY_CAPTURED"
    assert fvg["standalone_fvg_entry_inside_gap"] is True
    assert (
        fvg["implementation_candidate"]
        == "IMPLEMENT_DEFAULT_OFF_STANDALONE_FVG_POI_PATH_SCORER_NOW"
    )


def test_fvg_scorer_kills_non_fvg_selected_poi_rows():
    rows = build_strategy_outcome_rows(
        _candidate_with_fvg_strategy(structural_sources=True),
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    fvg = {row["strategy_id"]: row for row in rows}["V2_STRUCT_FVG_MID_EDGE"]

    assert fvg["strategy_status"] == "KILLED_STANDALONE_FVG_POI_NOT_SELECTED"
    assert fvg["score_status"] == "NOT_APPLICABLE_TO_ROW"
    assert fvg.get("strategy_proxy_r") is None
    assert fvg["branch_decision"] == "KILL_ROW_NOT_STANDALONE_FVG_POI"
    assert fvg["scoring_boundary"] == "NO_STANDALONE_FVG_PROXY_R_FOR_NON_FVG_SELECTED_POI"
    assert (
        fvg["claim_decision_scope"]
        == "CURRENT_STRATEGY_CLAIM_ONLY_UNDERLYING_INTELLIGENCE_PRESERVED"
    )
    assert fvg["underlying_intelligence_preserved"] is True
    assert fvg["missed_opportunity_audit"]["kill_scope"] == "CURRENT_CLAIM_ONLY"
    assert fvg["missed_opportunity_audit"]["preserve_as"] == (
        "NON_FVG_POI_CONTEXT_FEATURE_OR_REDESIGN_SOURCE_FOR_OB_FVG_SWITCHING"
    )
    _assert_full_opportunity_preservation(fvg)


def test_fvg_scorer_missing_metadata_becomes_source_capture_candidate():
    rows = build_strategy_outcome_rows(
        _candidate_with_fvg_strategy(structural_sources=False),
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    fvg = {row["strategy_id"]: row for row in rows}["V2_STRUCT_FVG_MID_EDGE"]

    assert fvg["strategy_status"] == "NOT_COMPUTABLE_MISSING_FVG_ENTRY_OR_LOCK_METADATA"
    assert fvg["score_status"] == "MISSING_REQUIRED_LIVE_METADATA"
    assert fvg["branch_decision"] == "SOURCE_CAPTURE_REQUIRED_FOR_FVG_SCORER"
    assert (
        fvg["implementation_candidate"]
        == "CAPTURE_STANDALONE_FVG_ENTRY_LOCK_AND_POST_LOCK_REENTRY_FIELDS"
    )
    _assert_full_opportunity_preservation(fvg)


def test_fvg_scorer_kills_non_fvg_poi_from_h1_setup_without_full_fvg_lock_metadata():
    candidate = _candidate_with_fvg_strategy(structural_sources=False)
    candidate["h1_setup"] = {
        "poi_identified": True,
        "poi_type": "OB",
        "poi_price_level": 4672.09,
        "zone": "premium",
    }

    rows = build_strategy_outcome_rows(
        candidate,
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    fvg = {row["strategy_id"]: row for row in rows}["V2_STRUCT_FVG_MID_EDGE"]

    assert fvg["strategy_status"] == "KILLED_STANDALONE_FVG_POI_NOT_SELECTED"
    assert fvg["score_status"] == "NOT_APPLICABLE_TO_ROW"
    assert fvg.get("strategy_proxy_r") is None
    assert fvg["branch_decision"] == "KILL_ROW_NOT_STANDALONE_FVG_POI"
    assert fvg["standalone_fvg_poi_status"] == "NON_FVG_POI_METADATA_CAPTURED"
    assert fvg["standalone_fvg_poi_type"] == "OB"
    assert fvg["missed_opportunity_audit"]["current_claim"] == "STANDALONE_FVG_SELECTED_POI_ENTRY"
    assert (
        fvg["standalone_fvg_selected_poi_type_source_status"]
        == "DECISION_TIME_H1_SETUP_POI_TYPE_CAPTURED_ONLY"
    )


def test_fvg_scorer_keeps_fvg_poi_source_bound_when_gap_and_lock_metadata_missing():
    candidate = _candidate_with_fvg_strategy(structural_sources=False)
    candidate["h1_setup"] = {
        "poi_identified": True,
        "poi_type": "FVG",
        "poi_price_level": 4668.45,
        "zone": "premium",
    }

    rows = build_strategy_outcome_rows(
        candidate,
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    fvg = {row["strategy_id"]: row for row in rows}["V2_STRUCT_FVG_MID_EDGE"]

    assert fvg["strategy_status"] == "NOT_COMPUTABLE_MISSING_FVG_ENTRY_OR_LOCK_METADATA"
    assert fvg["score_status"] == "MISSING_REQUIRED_LIVE_METADATA"
    assert fvg["branch_decision"] == "SOURCE_CAPTURE_REQUIRED_FOR_FVG_SCORER"
    assert fvg["standalone_fvg_poi_status"] == "STANDALONE_FVG_POI_SOURCE_NOT_CAPTURED"
    assert fvg["standalone_fvg_poi_type"] == "FVG"


def test_fvg_scorer_consumes_repaired_current_claim_decision_reference_only():
    candidate = _candidate_with_fvg_strategy(structural_sources=False)
    candidate["h1_setup"] = {
        "poi_identified": True,
        "poi_type": "FVG",
        "poi_price_level": 4668.45,
        "zone": "premium",
    }
    strategy_id = "V2_STRUCT_FVG_MID_EDGE"
    repair = {
        "row_id": "MAIN-ORCH24-ACTION-SRCM15-00025",
        "candidate_id": candidate["candidate_id"],
        "strategy_id": strategy_id,
        "source_decision_status": "ACTION_LEDGER_REPAIRED_CURRENT_CLAIM_DECISION",
        "branch_decision": "REDESIGN_STANDALONE_FVG_POI_SCORER_CURRENT_PROXY_NEGATIVE_SMALL_N",
        "decision_evidence": "STANDALONE_FVG_POI_DEFAULT_OFF_NUMERIC_PROXY_ROWS_SUM_NEGATIVE",
        "scoring_boundary": "NO_STANDALONE_FVG_DEFAULT_OFF_IMPLEMENTATION_WITH_CURRENT_NEGATIVE_SMALL_N_SHARED_PATH_PROXY",
        "implementation_candidate": "REDESIGN_STANDALONE_FVG_ENTRY_SELECTOR_BEFORE_DEFAULT_OFF_IMPLEMENTATION",
        "after_proxy_r": -1.0,
        "source_ledger": "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_2026-05-17.jsonl",
        "opportunity_proxy_reference_status": "REFERENCE_ONLY_CURRENT_STANDALONE_FVG_CLAIM_NOT_COUNTED",
        "opportunity_not_independently_countable_reason": "The current standalone-FVG POI claim has negative small-N shared-path proxy evidence and still lacks a distinct FVG entry-lock/reentry/fill-cost contract.",
        "opportunity_useful_mechanism": "Standalone FVG POI intelligence remains useful as entry selector redesign, context feature, source requirement, tighter target, shorter horizon, or broader system component.",
        "opportunity_downstream_paths": [
            "redesign",
            "context feature",
            "source requirement",
            "tighter target",
            "shorter horizon",
            "broader system component",
        ],
        "missed_opportunity_audit": {
            "kill_scope": "NOT_KILLED_CURRENT_STANDALONE_FVG_CLAIM_REDESIGN",
            "current_claim": "REDESIGN_STANDALONE_FVG_POI_SCORER_CURRENT_PROXY_NEGATIVE_SMALL_N",
            "unsupported_reason": "CURRENT_STANDALONE_FVG_POI_SHARED_PATH_PROXY_NEGATIVE_SMALL_N",
            "what_was_tried": "Selected FVG POI geometry was repaired and scored with current shared candidate-path proxy.",
            "what_could_make_it_work": "Exact standalone FVG entry-lock/reentry path, source-safe fill ordering, cost/spread accounting, and condition splits.",
            "preserve_as": "STANDALONE_FVG_ENTRY_SELECTOR_REDESIGN_CONTEXT_FEATURE_OR_SPECIALIZED_COMPONENT",
            "next_route": "DESIGN_STANDALONE_FVG_ENTRY_LOCK_REENTRY_SCORER_WITH_TIGHTER_TARGET_SHORTER_HORIZON_AND_CONTEXT_SPLITS",
        },
    }

    rows = build_strategy_outcome_rows(
        candidate,
        _path(),
        standalone_fvg_repair_decisions={(candidate["candidate_id"], strategy_id): repair},
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    fvg = {row["strategy_id"]: row for row in rows}[strategy_id]

    assert fvg["strategy_status"] == "REDESIGN_STANDALONE_FVG_POI_CURRENT_CLAIM_REPAIRED_REFERENCE"
    assert (
        fvg["branch_decision"]
        == "REDESIGN_STANDALONE_FVG_POI_SCORER_CURRENT_PROXY_NEGATIVE_SMALL_N"
    )
    assert fvg.get("strategy_proxy_r") is None
    assert fvg["standalone_fvg_current_claim_proxy_r_reference"] == -1.0
    assert fvg["opportunity_proxy_r_reference"] == -1.0
    assert (
        fvg["opportunity_proxy_reference_status"]
        == "REFERENCE_ONLY_CURRENT_STANDALONE_FVG_CLAIM_NOT_COUNTED"
    )
    assert (
        fvg["standalone_fvg_current_claim_repair_status"]
        == "CONSUMED_REPAIRED_ACTION_DECISION_REFERENCE_ONLY"
    )
    _assert_full_opportunity_preservation(fvg)


def test_swing_protected_scorer_scores_only_confirmed_protected_stops():
    rows = build_strategy_outcome_rows(
        _candidate_with_swing_protected_strategy(protects=True),
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    swing = {row["strategy_id"]: row for row in rows}["V2_STRUCT_SWING_PROTECTED"]

    assert swing["strategy_status"] == "SCORED_SWING_PROTECTED_STOP_PROXY_SHARED_CANDIDATE_PATH"
    assert swing["score_status"] == "COMPUTED_FROM_CANDIDATE_PATH"
    assert swing["strategy_proxy_r"] == 0.0
    assert swing["branch_decision"] == "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_STOP_CAPTURED_METADATA_SCORER"
    assert swing["swing_protected_stop_status"] == "SWING_PROTECTED_STOP_CONFIRMED"
    assert swing["swing_protected_match_timeframe"] == "H1"


def test_swing_protected_repair_decisions_count_only_default_off_proxy():
    candidate = _candidate_with_swing_protected_strategy(protects=False)
    strategy_id = "V2_STRUCT_SWING_PROTECTED"
    counted_repair = {
        "source_decision_status": "ACTION_LEDGER_REPAIRED_SWING_PROTECTED_CURRENT_CLAIM_DECISION",
        "candidate_id": candidate["candidate_id"],
        "strategy_id": strategy_id,
        "action_class": "IMPLEMENT_DEFAULT_OFF",
        "branch_decision": "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_SOURCE_REPAIRED_LTF_PROXY",
        "after_proxy_r": 1.0,
        "after_strategy_status": "SCORED_SWING_PROTECTED_STOP_PROXY_SHARED_CANDIDATE_PATH",
        "after_score_status": "COMPUTED_FROM_LTF_PATH_ORDER",
        "after_outcome_status": "ENTRY_TOUCHED_THEN_TP1",
        "row_id": "SWING-COUNTED-001",
        "source_ledger": "action-ledger.jsonl",
        "swing_protected_stop_status": "SWING_PROTECTED_STOP_CONFIRMED",
    }

    counted_rows = build_strategy_outcome_rows(
        candidate,
        _path(),
        swing_protected_repair_decisions={(candidate["candidate_id"], strategy_id): counted_repair},
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    counted = {row["strategy_id"]: row for row in counted_rows}[strategy_id]

    assert counted["strategy_proxy_r"] == 1.0
    assert (
        counted["swing_protected_current_claim_repair_status"]
        == "CONSUMED_REPAIRED_ACTION_DECISION_COUNTED_DEFAULT_OFF_PROXY"
    )
    assert counted["opportunity_proxy_reference_status"] == (
        "COUNTED_AS_DEFAULT_OFF_SWING_PROTECTED_PROXY_R"
    )

    reference_repair = {
        **counted_repair,
        "action_class": "REDESIGN",
        "branch_decision": "MERGE_DUPLICATE_GBPJPY_LONG_ADVERSE_AVOID_EVIDENCE_TO_CANONICAL_OWNER",
        "after_proxy_r": -1.0,
        "opportunity_proxy_reference_status": "REFERENCE_ONLY_NEGATIVE_CURRENT_CLAIM_PROXY",
        "missed_opportunity_audit": {
            "kill_scope": "NOT_KILLED_CURRENT_CLAIM_REDESIGN",
            "current_claim": "SWING_PROTECTED_STOP_SCORER",
            "unsupported_reason": "DUPLICATE_ADVERSE_EVIDENCE",
            "what_was_tried": "CONSUMED_ACTION_LEDGER_REPAIR",
            "what_could_make_it_work": "UNIQUE_NON_DUPLICATE_AVOID_FILTER_OWNER",
            "preserve_as": "AVOID_FILTER_OR_CONTEXT_FEATURE",
            "next_route": "MERGE_TO_CANONICAL_AVOID_FILTER_OWNER",
        },
        "underlying_intelligence_preserved": True,
    }
    reference_rows = build_strategy_outcome_rows(
        candidate,
        _path(),
        swing_protected_repair_decisions={(candidate["candidate_id"], strategy_id): reference_repair},
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    reference = {row["strategy_id"]: row for row in reference_rows}[strategy_id]

    assert reference.get("strategy_proxy_r") is None
    assert reference["swing_protected_current_claim_proxy_r_reference"] == -1.0
    assert reference["opportunity_proxy_reference_status"] == (
        "REFERENCE_ONLY_NEGATIVE_CURRENT_CLAIM_PROXY"
    )
    assert (
        reference["swing_protected_current_claim_repair_status"]
        == "CONSUMED_REPAIRED_ACTION_DECISION_REFERENCE_ONLY"
    )
    _assert_full_opportunity_preservation(reference)


def test_gbpjpy_long_structural_and_fvg_ob_rows_emit_adverse_redesign_branch():
    candidate = _as_gbpjpy_long(_candidate_with_swing_protected_strategy(protects=True))
    candidate["strategy_snapshots"].extend(
        [
            {
                "strategy_id": "V2_STRUCT_COMPOSITE_ANY",
                "family": "v2_structural_selector",
                "evidence_role": "canonical_structural_shared_path",
                "applicability": "candidate_relevant",
                "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
            },
            {
                "strategy_id": "FVG_OB_CONFLUENCE_OB_AFTER_FVG",
                "family": "fvg_ob_confluence",
                "evidence_role": "forward_confluence_bucket",
                "applicability": "candidate_relevant",
                "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
            },
        ]
    )

    rows = build_strategy_outcome_rows(
        candidate,
        _gbpjpy_long_path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    by_id = {row["strategy_id"]: row for row in rows}
    target_ids = [
        "V2_STRUCT_SWING_PROTECTED",
        "V2_STRUCT_COMPOSITE_ANY",
        "FVG_OB_CONFLUENCE_OB_AFTER_FVG",
    ]

    for strategy_id in target_ids:
        row = by_id[strategy_id]
        assert row["branch_decision"] == (
            "REDESIGN_GBPJPY_LONG_STRUCTURAL_FVG_OB_ADVERSE_CLUSTER_AVOID_FILTER_CANDIDATE"
        )
        assert row["implementation_candidate"] == (
            "REDESIGN_GBPJPY_LONG_STRUCTURAL_FVG_OB_AVOID_OR_CONTEXT_FILTER"
        )
        assert row["underlying_intelligence_preserved"] is True
        assert row["missed_opportunity_audit"]["kill_scope"] == "NOT_KILLED_REDESIGN_ADVERSE_CLUSTER"
        assert row["symbol"] == "GBPJPY"
        assert row["side"] == "LONG"
        _assert_full_opportunity_preservation(row)

    canonical = by_id["V2_STRUCT_COMPOSITE_ANY"]
    assert canonical["gbpjpy_long_adverse_avoid_materialization_status"] == (
        "CANONICAL_AVOID_FILTER_SAVED_R_OWNER"
    )
    assert canonical["gbpjpy_long_adverse_avoid_candidate_decision"] == (
        "IMPLEMENT_DEFAULT_OFF_GBPJPY_LONG_STRUCTURAL_FVG_OB_ADVERSE_AVOID_FILTER"
    )
    assert canonical["gbpjpy_long_adverse_current_claim_proxy_r_reference"] == -1.0
    assert canonical["gbpjpy_long_adverse_avoid_saved_proxy_r"] == 1.0
    assert canonical["gbpjpy_long_adverse_avoid_saved_proxy_counted"] is True

    for strategy_id in ("V2_STRUCT_SWING_PROTECTED", "FVG_OB_CONFLUENCE_OB_AFTER_FVG"):
        duplicate = by_id[strategy_id]
        assert duplicate["gbpjpy_long_adverse_avoid_materialization_status"] == (
            "DUPLICATE_AVOID_FILTER_PROXY_REFERENCE_NOT_COUNTED"
        )
        assert duplicate["gbpjpy_long_adverse_avoid_candidate_decision"] == (
            "MERGE_DUPLICATE_GBPJPY_LONG_ADVERSE_AVOID_EVIDENCE_TO_CANONICAL_OWNER"
        )
        assert duplicate["gbpjpy_long_adverse_current_claim_proxy_r_reference"] == -1.0
        assert duplicate.get("gbpjpy_long_adverse_avoid_saved_proxy_r") is None
        assert duplicate["gbpjpy_long_adverse_avoid_saved_proxy_counted"] is False

    assert by_id["V2_STRUCT_SWING_PROTECTED"]["strategy_status"] == (
        "REDESIGN_GBPJPY_LONG_SWING_PROTECTED_ADVERSE_CLUSTER"
    )
    assert by_id["V2_STRUCT_COMPOSITE_ANY"]["strategy_status"] == (
        "REDESIGN_GBPJPY_LONG_STRUCTURAL_LOCK_ADVERSE_CLUSTER"
    )
    assert by_id["FVG_OB_CONFLUENCE_OB_AFTER_FVG"]["strategy_status"] == (
        "REDESIGN_GBPJPY_LONG_FVG_OB_ADVERSE_CLUSTER"
    )


def test_gbpjpy_long_adverse_avoid_bounds_ambiguous_ltf_saved_r_interval():
    candidate = _as_gbpjpy_long(_candidate_with_structural_sources())
    candidate["strategy_snapshots"].append(
        {
            "strategy_id": "V2_STRUCT_COMPOSITE_ANY",
            "family": "v2_structural_selector",
            "evidence_role": "canonical_structural_shared_path",
            "applicability": "candidate_relevant",
            "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
        }
    )
    path = _gbpjpy_long_path()
    path.update(
        {
            "path_label": "entry_touched_tp_and_sl_m15_ambiguous",
            "hit_tp1": True,
            "hit_sl": True,
        }
    )
    ltf = _ltf(
        "ENTRY_THEN_TP1_SL_SAME_M1_AMBIGUOUS",
        event="2026-05-04T02:35:00+00:00",
        r_value=None,
        tp1_first_touch_utc="2026-05-04T02:35:00+00:00",
        sl_first_touch_utc="2026-05-04T02:35:00+00:00",
    )
    ltf.update(
        {
            "candidate_id": "GBPJPY_2026-05-04T02:15:00+00:00",
            "asof_latest_candle_utc": "2026-05-04T02:45:00+00:00",
            "created_at_utc": "2026-05-04T02:45:05+00:00",
            "path_order_label": "entry_then_tp1_sl_same_m1_ambiguous",
        }
    )

    rows = build_strategy_outcome_rows(
        candidate,
        path,
        ltf_row=ltf,
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    canonical = {row["strategy_id"]: row for row in rows}["V2_STRUCT_COMPOSITE_ANY"]

    assert canonical["score_status"] == "AMBIGUOUS_LTF_ORDER"
    assert canonical["outcome_status"] == "ENTRY_THEN_TP1_SL_SAME_M1_AMBIGUOUS"
    assert canonical.get("strategy_proxy_r") is None
    assert canonical["gbpjpy_long_adverse_avoid_materialization_status"] == (
        "BOUNDED_AVOID_FILTER_SAVED_R_INTERVAL_NOT_COUNTED"
    )
    assert canonical["gbpjpy_long_adverse_avoid_candidate_decision"] == (
        "REDESIGN_GBPJPY_LONG_ADVERSE_AVOID_FILTER_BOUNDED_PROXY_REPAIR"
    )
    assert canonical["gbpjpy_long_adverse_current_claim_proxy_reference_status"] == (
        "BOUNDED_AMBIGUOUS_PROXY_INTERVAL_REFERENCE_NOT_COUNTED"
    )
    assert canonical["gbpjpy_long_adverse_avoid_saved_proxy_r_interval_low"] == -1.5
    assert canonical["gbpjpy_long_adverse_avoid_saved_proxy_r_interval_high"] == 1.0
    assert canonical["gbpjpy_long_adverse_avoid_saved_proxy_interval_status"] == (
        "TP1_OR_SL_SAME_M1_AVOID_SAVED_R_INTERVAL"
    )
    assert canonical["gbpjpy_long_adverse_avoid_saved_proxy_interval_counted"] is False
    assert canonical["gbpjpy_long_adverse_avoid_saved_proxy_counted"] is False
    _assert_full_opportunity_preservation(canonical)


def test_gbpjpy_long_adverse_avoid_marks_non_adverse_proxy_false_positive():
    candidate = _as_gbpjpy_long(_candidate_with_structural_sources())
    candidate["strategy_snapshots"].append(
        {
            "strategy_id": "V2_STRUCT_COMPOSITE_ANY",
            "family": "v2_structural_selector",
            "evidence_role": "canonical_structural_shared_path",
            "applicability": "candidate_relevant",
            "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
        }
    )
    path = _gbpjpy_long_path()
    path.update(
        {
            "path_label": "entry_touched_tp_and_sl_m15_ambiguous",
            "hit_tp1": True,
            "hit_sl": True,
        }
    )
    ltf = _ltf(
        "ENTRY_THEN_TP1",
        event="2026-05-04T02:35:00+00:00",
        r_value=1.5,
        tp1_first_touch_utc="2026-05-04T02:35:00+00:00",
    )
    ltf.update(
        {
            "candidate_id": "GBPJPY_2026-05-04T02:15:00+00:00",
            "asof_latest_candle_utc": "2026-05-04T02:45:00+00:00",
            "created_at_utc": "2026-05-04T02:45:05+00:00",
            "path_order_label": "entry_then_tp1_before_sl",
        }
    )

    rows = build_strategy_outcome_rows(
        candidate,
        path,
        ltf_row=ltf,
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    canonical = {row["strategy_id"]: row for row in rows}["V2_STRUCT_COMPOSITE_ANY"]

    assert canonical["score_status"] == "COMPUTED_FROM_LTF_PATH_ORDER"
    assert canonical["outcome_status"] == "ENTRY_TOUCHED_THEN_TP1"
    assert canonical["strategy_proxy_r"] == 1.5
    assert canonical["gbpjpy_long_adverse_avoid_materialization_status"] == (
        "REDESIGN_AVOID_FILTER_FALSE_POSITIVE_PROXY_REFERENCE"
    )
    assert canonical["gbpjpy_long_adverse_avoid_candidate_decision"] == (
        "REDESIGN_GBPJPY_LONG_ADVERSE_AVOID_FILTER_FALSE_POSITIVE_CONTEXT_REQUIRED"
    )
    assert canonical["gbpjpy_long_adverse_current_claim_proxy_reference_status"] == (
        "NUMERIC_NON_ADVERSE_PROXY_REFERENCE_REDESIGN_FALSE_POSITIVE"
    )
    assert canonical["gbpjpy_long_adverse_avoid_non_saved_proxy_r_reference"] == -1.5
    assert canonical["gbpjpy_long_adverse_avoid_saved_proxy_counted"] is False
    assert canonical["gbpjpy_long_adverse_avoid_saved_proxy_r"] is None
    _assert_full_opportunity_preservation(canonical)


def test_gbpjpy_long_adverse_avoid_marks_unresolved_horizon_with_mfe_mae_reference():
    candidate = _as_gbpjpy_long(_candidate_with_structural_sources())
    candidate["strategy_snapshots"].append(
        {
            "strategy_id": "V2_STRUCT_COMPOSITE_ANY",
            "family": "v2_structural_selector",
            "evidence_role": "canonical_structural_shared_path",
            "applicability": "candidate_relevant",
            "result_use_status": "RESULT_MATERIALIZATION_REQUIRED",
        }
    )
    path = _gbpjpy_long_path()
    path.update(
        {
            "path_label": "entry_touched_unresolved",
            "hit_tp1": False,
            "hit_sl": False,
            "min_low": 189.75,
            "max_high": 191.0,
            "last_close": 190.5,
        }
    )

    rows = build_strategy_outcome_rows(
        candidate,
        path,
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    canonical = {row["strategy_id"]: row for row in rows}["V2_STRUCT_COMPOSITE_ANY"]

    assert canonical["score_status"] == "COMPUTED_FROM_CANDIDATE_PATH"
    assert canonical["outcome_status"] == "ENTRY_TOUCHED_UNRESOLVED"
    assert canonical.get("strategy_proxy_r") is None
    assert canonical["gbpjpy_long_adverse_avoid_materialization_status"] == (
        "UNRESOLVED_HORIZON_AVOID_FILTER_REFERENCE_NOT_COUNTED"
    )
    assert canonical["gbpjpy_long_adverse_avoid_candidate_decision"] == (
        "REDESIGN_GBPJPY_LONG_ADVERSE_AVOID_FILTER_UNRESOLVED_HORIZON_CONTEXT_REQUIRED"
    )
    assert canonical["gbpjpy_long_adverse_current_claim_proxy_reference_status"] == (
        "UNRESOLVED_HORIZON_MFE_MAE_REFERENCE_NOT_COUNTED"
    )
    assert canonical["gbpjpy_long_adverse_unresolved_horizon_mfe_r_reference"] == 1.0
    assert canonical["gbpjpy_long_adverse_unresolved_horizon_mae_r_reference"] == -0.25
    assert canonical["gbpjpy_long_adverse_avoid_saved_proxy_counted"] is False
    _assert_full_opportunity_preservation(canonical)


def test_latest_ltf_prefers_recovered_m1_over_later_source_blocked_row():
    recovered = _ltf("ENTRY_THEN_SL")
    recovered.update(
        {
            "ltf_status": "M1_PATH_RECOVERED",
            "m1_bar_count": 120,
            "created_at_utc": "2026-05-04T07:46:00+00:00",
            "mt5_read_error": None,
        }
    )
    blocked = _ltf("NO_ENTRY_TOUCH_BY_LTF_ASOF", event=None, r_value=None)
    blocked.update(
        {
            "ltf_status": "SOURCE_BLOCKED",
            "m1_bar_count": 0,
            "created_at_utc": "2026-05-04T07:50:00+00:00",
            "mt5_read_error": "outside_max_hours",
            "path_order_label": "ltf_source_blocked",
        }
    )

    selected = latest_ltf_for_candidate_asof(_candidate(), _path(), [recovered, blocked])

    assert selected is recovered
    assert selected["terminal_outcome_status"] == "ENTRY_THEN_SL"
    assert selected["ltf_status"] == "M1_PATH_RECOVERED"


def test_swing_protected_scorer_kills_unprotected_stops():
    rows = build_strategy_outcome_rows(
        _candidate_with_swing_protected_strategy(protects=False),
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    swing = {row["strategy_id"]: row for row in rows}["V2_STRUCT_SWING_PROTECTED"]

    assert swing["strategy_status"] == "KILLED_SWING_PROTECTED_STOP_NOT_CONFIRMED"
    assert swing["score_status"] == "NOT_APPLICABLE_TO_ROW"
    assert swing.get("strategy_proxy_r") is None
    assert swing["branch_decision"] == "KILL_ROW_NOT_SWING_PROTECTED_STOP"
    assert swing["swing_protected_stop_status"] == "STOP_DOES_NOT_PROTECT_COMPATIBLE_SWING"
    assert (
        swing["claim_decision_scope"]
        == "CURRENT_STRATEGY_CLAIM_ONLY_UNDERLYING_INTELLIGENCE_PRESERVED"
    )
    assert swing["missed_opportunity_audit"]["kill_scope"] == "CURRENT_CLAIM_ONLY"
    assert swing["missed_opportunity_audit"]["preserve_as"] == (
        "SWING_DISTANCE_STOP_PLACEMENT_CONTEXT_OR_AVOID_FILTER"
    )
    _assert_full_opportunity_preservation(swing)


def test_run_merges_live_structural_metadata_for_structural_lock_scorer(tmp_path: Path):
    candidate = _candidate()
    candidate["trade_parameters"] = _path()["trade_parameters"]
    path = _path()
    metadata = {
        "candidate_id": candidate["candidate_id"],
        "created_at_utc": "2026-05-04T08:00:01+00:00",
        "backfilled_at_utc": "2026-05-04T08:00:02+00:00",
        "decision_time_structural_capture_status": "LEGACY_CANDIDATE_ROW_WITH_RECOVERED_STRUCTURAL_SOURCE",
        "manual_backfill_status": "RECOVERED_AVAILABLE_FIELDS_WITH_EXPLICIT_SOURCE_GAPS",
        "no_leak_status": "POST_DECISION_RECOVERY_ROW_NOT_DECISION_FEATURE",
        "structural_source_field_statuses": {
            "structural_lock_event_time_price": "FORWARD_PATH_EVENT_CAPTURED",
            "post_lock_reentry_state": "FORWARD_PATH_SOURCE_CAPTURED_REENTRY_NOT_EVALUATED",
            "cost_aware_min_r_fields": "SOURCE_NOT_CAPTURED",
            "swing_protected_lock_level": "SOURCE_NOT_CAPTURED",
        },
        "captured_structural_source_fields": {
            "structural_lock_event_time_price": {
                "source_status": "FORWARD_PATH_EVENT_CAPTURED",
                "event_time_utc": "2026-05-04T07:35:00+00:00",
                "event_price": 4668.45,
            },
            "post_lock_reentry_state": {
                "source_status": "FORWARD_PATH_SOURCE_CAPTURED_REENTRY_NOT_EVALUATED",
                "entry_first_touch_utc": None,
                "tp1_first_touch_utc": "2026-05-04T07:45:00+00:00",
            },
        },
    }
    candidates_path = tmp_path / "candidates.jsonl"
    paths_path = tmp_path / "paths.jsonl"
    pending_path = tmp_path / "pending.jsonl"
    ltf_path = tmp_path / "ltf.jsonl"
    fvg_ob_path = tmp_path / "fvg_ob.jsonl"
    structural_metadata_path = tmp_path / "structural_metadata.jsonl"
    output_path = tmp_path / "out.jsonl"
    dry_run_output_path = tmp_path / "dry_run.jsonl"
    _write_jsonl(candidates_path, [candidate])
    _write_jsonl(paths_path, [path])
    pending_path.write_text("", encoding="utf-8")
    ltf_path.write_text("", encoding="utf-8")
    fvg_ob_path.write_text("", encoding="utf-8")
    _write_jsonl(structural_metadata_path, [metadata])

    summary = run(
        candidates_path=candidates_path,
        paths_path=paths_path,
        pending_lifecycle_path=pending_path,
        ltf_path_order_path=ltf_path,
        fvg_ob_confluence_path=fvg_ob_path,
        structural_metadata_path=structural_metadata_path,
        output_path=output_path,
        dry_run=True,
        dry_run_output_path=dry_run_output_path,
        latest_paths_only=True,
    )
    rows = [
        json.loads(line)
        for line in dry_run_output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    structural = {row["strategy_id"]: row for row in rows}["V3_OB_LOCK_PULLBACK_RISK_BANK"]

    assert summary["structural_metadata_candidates_seen"] == 1
    assert structural["strategy_status"] == "REDESIGN_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY"
    assert structural["score_status"] == "COMPUTED_FROM_CANDIDATE_PATH"
    assert structural["strategy_proxy_r"] is None
    assert structural["structural_duplicate_proxy_reference_r"] == 0.0
    assert (
        structural["branch_decision"]
        == "MERGE_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY_INTO_V2_STRUCT_COMPOSITE_ANY"
    )


def test_fvg_ob_confluence_scores_captured_metadata_with_shared_path_proxy():
    rows = build_strategy_outcome_rows(
        _candidate_with_fvg_ob_strategy(structural_sources=True),
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    fvg_ob = {row["strategy_id"]: row for row in rows}["FVG_OB_CONFLUENCE_OB_AFTER_FVG"]

    assert fvg_ob["strategy_status"] == "SCORED_FVG_OB_CONFLUENCE_PROXY_SHARED_CANDIDATE_PATH"
    assert fvg_ob["score_status"] == "COMPUTED_FROM_CANDIDATE_PATH"
    assert fvg_ob["outcome_status"] == "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH"
    assert fvg_ob["strategy_proxy_r"] == 0.0
    assert (
        fvg_ob["scoring_boundary"]
        == "FVG_OB_CONFLUENCE_SHARED_CANDIDATE_PATH_PROXY_NOT_STANDALONE_FVG_ENTRY"
    )
    assert (
        fvg_ob["branch_decision"]
        == "IMPLEMENT_DEFAULT_OFF_FVG_OB_CONFLUENCE_CAPTURED_METADATA_SHARED_PATH_SCORER"
    )
    assert (
        fvg_ob["implementation_candidate"]
        == "IMPLEMENT_DEFAULT_OFF_FVG_OB_CONFLUENCE_SHARED_PATH_PROXY_SCORER"
    )


def test_fvg_ob_confluence_stays_blocked_without_captured_metadata():
    rows = build_strategy_outcome_rows(
        _candidate_with_fvg_ob_strategy(structural_sources=False),
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    fvg_ob = {row["strategy_id"]: row for row in rows}["FVG_OB_CONFLUENCE_OB_AFTER_FVG"]

    assert fvg_ob["strategy_status"] == "NOT_COMPUTABLE_MISSING_FVG_ENTRY_OR_LOCK_METADATA"
    assert fvg_ob["score_status"] == "MISSING_REQUIRED_LIVE_METADATA"
    assert fvg_ob["branch_decision"] == "SOURCE_CAPTURE_REQUIRED_FOR_FVG_SCORER"
    assert fvg_ob.get("strategy_proxy_r") is None


def test_fvg_ob_confluence_kills_single_family_bucket_without_exact_bounds():
    candidate = _candidate_with_fvg_ob_strategy(structural_sources=False)
    candidate["fvg_ob_confluence_context"] = {
        "bucket": "ob_only",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "source_file": "shadow_logs/fvg_ob_confluence.jsonl",
    }

    rows = build_strategy_outcome_rows(
        candidate,
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    fvg_ob = {row["strategy_id"]: row for row in rows}["FVG_OB_CONFLUENCE_OB_AFTER_FVG"]

    assert fvg_ob["strategy_status"] == "KILLED_FVG_OB_CONFLUENCE_NOT_PRESENT"
    assert fvg_ob["score_status"] == "NOT_APPLICABLE_TO_ROW"
    assert fvg_ob["branch_decision"] == "KILL_ROW_NOT_FVG_OB_CONFLUENCE"
    assert fvg_ob["fvg_ob_confluence_bucket"] == "ob_only"
    assert fvg_ob.get("strategy_proxy_r") is None
    assert (
        fvg_ob["claim_decision_scope"]
        == "CURRENT_STRATEGY_CLAIM_ONLY_UNDERLYING_INTELLIGENCE_PRESERVED"
    )
    assert fvg_ob["underlying_intelligence_preserved"] is True
    assert fvg_ob["missed_opportunity_audit"]["kill_scope"] == "CURRENT_CLAIM_ONLY"
    assert fvg_ob["missed_opportunity_audit"]["preserve_as"] == (
        "SINGLE_FAMILY_OB_OR_FVG_CONTEXT_FEATURE_AVOID_FILTER_OR_MARKET_SESSION_CANDIDATE"
    )
    _assert_full_opportunity_preservation(fvg_ob)


def test_fvg_ob_confluence_preserves_both_fire_bucket_until_exact_bounds_exist():
    candidate = _candidate_with_fvg_ob_strategy(structural_sources=False)
    candidate["fvg_ob_confluence_context"] = {
        "bucket": "both_fvg_and_ob_fire",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "source_file": "shadow_logs/fvg_ob_confluence.jsonl",
    }

    rows = build_strategy_outcome_rows(
        candidate,
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    fvg_ob = {row["strategy_id"]: row for row in rows}["FVG_OB_CONFLUENCE_OB_AFTER_FVG"]

    assert fvg_ob["strategy_status"] == "SOURCE_REQUIRED_FVG_OB_CONFLUENCE_EXACT_BOUNDS_MISSING"
    assert fvg_ob["score_status"] == "SOURCE_CAPTURE_REQUIRED"
    assert fvg_ob["outcome_status"] == "NOT_SCORED"
    assert fvg_ob["strategy_proxy_r"] is None
    assert fvg_ob["fvg_ob_confluence_bucket"] == "both_fvg_and_ob_fire"
    assert fvg_ob["branch_decision"] == "PRESERVE_FVG_OB_BUCKET_BOTH_FIRE_EXACT_BOUNDS_REQUIRED"
    assert (
        fvg_ob["scoring_boundary"]
        == "FVG_OB_CONFLUENCE_BUCKET_SOURCE_REQUIREMENT_EXACT_BOUNDS_MISSING"
    )
    assert (
        fvg_ob["implementation_candidate"]
        == "PRESERVE_FVG_OB_EXACT_BOUNDS_AND_ENTRY_LOCK_SOURCE_REQUIREMENT"
    )


def test_fvg_ob_confluence_consumes_trade_record_bounds_repair_as_fvg_only_redesign():
    candidate = _candidate_with_fvg_ob_strategy(structural_sources=False)
    candidate["fvg_ob_confluence_context"] = {
        "bucket": "both_fvg_and_ob_fire",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "source_file": "knowledge_base/trade_records/GBPJPY/2026-05-04_tokyo_0300.json",
    }
    repair = {
        "source_decision_status": "ACTION_LEDGER_REPAIRED_FVG_OB_TRADE_RECORD_BOUNDS_DECISION",
        "candidate_id": candidate["candidate_id"],
        "strategy_id": "FVG_OB_CONFLUENCE_OB_AFTER_FVG",
        "row_id": "MAIN-ORCH24-ACTION-SRCM15-00021",
        "branch_decision": "REDESIGN_FVG_OB_BUCKET_REPAIRED_AS_FVG_ONLY_NO_OB_CONFLUENCE",
        "decision_evidence": "TRADE_RECORD_L2_ENTRY_IN_FVG_PASS_WITH_OB_CHECKS_SKIPPED",
        "scoring_boundary": "FVG_ONLY_EXACT_BOUNDS_REPAIRED_NOT_FVG_OB_OB_AFTER_FVG_IMPLEMENTATION",
        "implementation_candidate": "REDESIGN_AS_FVG_ONLY_ENTRY_LOCK_OR_REQUIRE_OB_BOUNDS",
        "opportunity_proxy_r_reference": -1.0,
        "opportunity_proxy_reference_status": "REFERENCE_ONLY_SHARED_PATH_PROXY_NOT_FVG_OB_IMPLEMENTATION",
        "opportunity_useful_mechanism": "Exact FVG entry geometry remains useful.",
        "opportunity_downstream_paths": ["redesign", "source requirement", "context feature"],
        "underlying_intelligence_preserved": True,
        "fvg_exact_bounds": {
            "bottom": 213.286,
            "top": 213.313,
            "type": "bullish",
            "formation_time": "2026-05-04T01:45:00+00:00",
        },
        "ob_leg_status": "NO_OB_BOUNDS_IN_TRADE_RECORD_L2_OB_CHECKS_SKIPPED_FVG_FILL_PATH",
        "missed_opportunity_audit": {
            "kill_scope": "NOT_KILLED_CURRENT_FVG_OB_CLAIM_REDESIGNED_ONLY",
            "current_claim": "PRESERVE_FVG_OB_BUCKET_BOTH_FIRE_EXACT_BOUNDS_REQUIRED",
            "unsupported_reason": "EXACT_FVG_BOUNDS_REPAIRED_BUT_OB_LEG_NOT_PRESENT_FOR_FVG_OB_CONFLUENCE",
            "what_was_tried": "Parsed trade record L2 entry_in_fvg PASS.",
            "what_could_make_it_work": "Capture OB bounds before FVG/OB confluence scoring.",
            "preserve_as": "FVG_ONLY_EXACT_BOUNDS_REDESIGN_AND_SOURCE_CAPTURE_REQUIREMENT",
            "next_route": "MERGE_INTO_STANDALONE_FVG_ENTRY_LOCK_REDESIGN",
        },
    }

    rows = build_strategy_outcome_rows(
        candidate,
        _path(),
        fvg_ob_trade_record_bounds_repairs={
            (candidate["candidate_id"], "FVG_OB_CONFLUENCE_OB_AFTER_FVG"): repair
        },
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    fvg_ob = {row["strategy_id"]: row for row in rows}["FVG_OB_CONFLUENCE_OB_AFTER_FVG"]

    assert fvg_ob["strategy_status"] == (
        "REDESIGN_FVG_OB_CONFLUENCE_REPAIRED_AS_FVG_ONLY_NO_OB_LEG"
    )
    assert fvg_ob["score_status"] == (
        "NOT_COUNTED_FVG_ONLY_SOURCE_REPAIR_NOT_FVG_OB_CONFLUENCE"
    )
    assert fvg_ob["branch_decision"] == (
        "REDESIGN_FVG_OB_BUCKET_REPAIRED_AS_FVG_ONLY_NO_OB_CONFLUENCE"
    )
    assert fvg_ob["strategy_proxy_r"] is None
    assert fvg_ob["fvg_ob_current_claim_proxy_r_reference"] == -1.0
    assert (
        fvg_ob["fvg_ob_current_claim_proxy_reference_status"]
        == "REFERENCE_ONLY_SHARED_PATH_PROXY_NOT_FVG_OB_IMPLEMENTATION"
    )
    assert fvg_ob["fvg_exact_bounds"]["bottom"] == 213.286
    assert fvg_ob["fvg_ob_ob_leg_status"] == (
        "NO_OB_BOUNDS_IN_TRADE_RECORD_L2_OB_CHECKS_SKIPPED_FVG_FILL_PATH"
    )
    _assert_full_opportunity_preservation(fvg_ob)


def test_prefill_delivery_kills_far_miss_with_m15_hard_no_fill_proof():
    rows = build_strategy_outcome_rows(
        _candidate_with_prefill_strategy(),
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    prefill = {row["strategy_id"]: row for row in rows}["PREFILL_DELIVERY_REVERSAL_PATH"]

    assert prefill["strategy_status"] == "KILL_PREFILL_FAR_MISS_050R_M15_HARD_NO_FILL"
    assert prefill["score_status"] == "COMPUTED_FROM_M15_HARD_NO_FILL_RANGE_PROOF"
    assert prefill["branch_decision"] == (
        "KILL_PREFILL_FAR_MISS_050R_OFFSET_NO_FILL_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL"
    )
    assert prefill["entry_retest_redesign_bucket"] == "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE"
    assert (
        prefill["scoring_boundary"]
        == "M15_HARD_NO_FILL_RANGE_PROOF_ONLY_NO_FILL_OR_TP_INFERENCE"
    )
    assert (
        prefill["implementation_candidate"]
        == "NONE_PREFILL_FAR_MISS_050R_NO_FILL_KEEP_AS_RETEST_REDESIGN_FAILURE"
    )
    assert (
        prefill["claim_decision_scope"]
        == "CURRENT_STRATEGY_CLAIM_ONLY_UNDERLYING_INTELLIGENCE_PRESERVED"
    )
    assert prefill["missed_opportunity_audit"]["kill_scope"] == "CURRENT_CLAIM_ONLY"
    assert prefill["missed_opportunity_audit"]["preserve_as"] == (
        "FAR_MISS_RETEST_CONTROL_REDESIGN_OR_AVOID_CONTEXT"
    )
    _assert_full_opportunity_preservation(prefill)


def test_prefill_delivery_far_miss_merges_into_entry_offset_retest_control_redesign():
    path = _path()
    path.update(
        {
            "entry_offset_050r_tick_replay_status": "TICK_REPLAY_SOURCE_COMPLETE",
            "entry_offset_050r_outcome_status": "TP1_AFTER_SHIFT_FILL",
            "entry_offset_050r_proxy_r": 0.66716406,
        }
    )
    rows = build_strategy_outcome_rows(
        _candidate_with_prefill_strategy(),
        path,
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    prefill = {row["strategy_id"]: row for row in rows}["PREFILL_DELIVERY_REVERSAL_PATH"]

    assert (
        prefill["strategy_status"]
        == "MERGED_PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE"
    )
    assert prefill["score_status"] == "METADATA_MERGED_TO_ENTRY_OFFSET_SCORER"
    assert prefill["outcome_status"] == "LINKED_ENTRY_OFFSET_TP1_AFTER_SHIFT_FILL"
    assert (
        prefill["branch_decision"]
        == "MERGE_PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE"
    )
    assert prefill["linked_entry_offset_050r_proxy_r"] == 0.66716406
    assert (
        prefill["linked_entry_offset_proxy_r_owner"]
        == "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"
    )
    assert prefill.get("strategy_proxy_r") is None
    assert (
        prefill["scoring_boundary"]
        == "REFERENCE_ONLY_PREFILL_PROXY_R_NOT_COUNTED_STANDALONE"
    )
    assert (
        prefill["implementation_candidate"]
        == "PREFILL_TP_AFTER_FILL_CONTEXT_MERGED_TO_ENTRY_OFFSET_CLUSTER_GUARD"
    )
    assert (
        prefill["prefill_proxy_counting_decision"]
        == "PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_NOT_DUPLICATED"
    )
    assert prefill["opportunity_proxy_r_reference"] == 0.66716406
    assert prefill["opportunity_proxy_reference_status"] == (
        "REFERENCE_ONLY_NOT_COUNTED_DUPLICATE_ENTRY_OFFSET_OWNER"
    )
    assert prefill["entry_offset_concentration_guard_status"] == "PREFILL_REFERENCE_CLUSTER_GUARDED"
    assert prefill["entry_offset_original_subtype"] == "FAR_MISS"
    assert prefill["entry_offset_current_evidence_owner_rows"] == 13
    assert "entry-offset merge" in prefill["opportunity_downstream_paths"]
    _assert_full_opportunity_preservation(prefill)


def test_prefill_delivery_near_miss_merges_into_entry_offset_implementation():
    path = _path()
    path.update(
        {
            "entry_touch_distance_status": "NEAR_MISS_LE_0_25R",
            "nearest_distance_to_entry_r": 0.12,
            "entry_offset_050r_tick_replay_status": "TICK_REPLAY_SOURCE_COMPLETE",
            "entry_offset_050r_outcome_status": "TP1_AFTER_SHIFT_FILL",
            "entry_offset_050r_proxy_r": 0.66567534,
        }
    )
    rows = build_strategy_outcome_rows(
        _candidate_with_prefill_strategy(),
        path,
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    prefill = {row["strategy_id"]: row for row in rows}["PREFILL_DELIVERY_REVERSAL_PATH"]

    assert prefill["strategy_status"] == "MERGED_PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE"
    assert prefill["score_status"] == "METADATA_MERGED_TO_ENTRY_OFFSET_SCORER"
    assert prefill["outcome_status"] == "LINKED_ENTRY_OFFSET_TP1_AFTER_SHIFT_FILL"
    assert prefill["branch_decision"] == "MERGE_PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE"
    assert prefill["linked_entry_offset_050r_proxy_r"] == 0.66567534
    assert prefill.get("strategy_proxy_r") is None
    assert (
        prefill["prefill_proxy_counting_decision"]
        == "PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_NOT_DUPLICATED"
    )
    assert prefill["opportunity_proxy_r_reference"] == 0.66567534
    assert prefill["opportunity_proxy_reference_status"] == (
        "REFERENCE_ONLY_NOT_COUNTED_DUPLICATE_ENTRY_OFFSET_OWNER"
    )
    assert prefill["entry_offset_concentration_guard_status"] == "PREFILL_REFERENCE_CLUSTER_GUARDED"
    assert prefill["entry_offset_original_subtype"] == "NEAR_MISS"
    assert "entry-offset merge" in prefill["opportunity_downstream_paths"]
    _assert_full_opportunity_preservation(prefill)


def test_prefill_delivery_keeps_rows_outside_no_fill_tp1_redesign_denominator():
    rows = build_strategy_outcome_rows(
        _candidate_with_prefill_strategy(),
        _ambiguous_path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    prefill = {row["strategy_id"]: row for row in rows}["PREFILL_DELIVERY_REVERSAL_PATH"]

    assert prefill["strategy_status"] == "NOT_APPLICABLE_NOT_PREFILL_REDESIGN_DENOMINATOR"
    assert prefill["score_status"] == "NOT_APPLICABLE"
    assert (
        prefill["branch_decision"]
        == "KEEP_CURRENT_ENTRY_MODEL_NOT_IN_PREFILL_REDESIGN_DENOMINATOR"
    )
    assert (
        prefill["scoring_boundary"]
        == "PREFILL_REDESIGN_NOT_APPLICABLE_OUTSIDE_NO_FILL_TP1_DENOMINATOR"
    )


def test_entry_offset_050r_waits_for_tick_replay_not_m15_distance():
    path = _path()
    path["nearest_distance_to_entry_r"] = 0.6
    rows = build_strategy_outcome_rows(
        _candidate_with_entry_offset_strategy(),
        path,
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    entry_offset = {row["strategy_id"]: row for row in rows}["ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"]

    assert entry_offset["strategy_status"] == "WAITING_FOR_ENTRY_OFFSET_050R_TICK_REPLAY_SOURCE"
    assert entry_offset["score_status"] == "WAITING_SOURCE"
    assert (
        entry_offset["scoring_boundary"]
        == "NO_ENTRY_OFFSET_PROXY_R_WITHOUT_SPREAD_AWARE_TICK_REPLAY"
    )
    assert (
        entry_offset["implementation_candidate"]
        == "BUILD_DEFAULT_OFF_ENTRY_OFFSET_050R_TICK_REPLAY_SCORER_WITH_SPREAD_AWARE_FILL_CONTRACT"
    )
    assert entry_offset.get("strategy_proxy_r") is None
    assert entry_offset["entry_offset_050r_source_capture_complete"] is False


def test_entry_offset_050r_kills_m15_hard_no_fill_without_tick_replay():
    rows = build_strategy_outcome_rows(
        _candidate_with_entry_offset_strategy(),
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    entry_offset = {row["strategy_id"]: row for row in rows}["ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"]

    assert entry_offset["strategy_status"] == "KILLED_ENTRY_OFFSET_050R_M15_HARD_NO_FILL"
    assert entry_offset["score_status"] == "COMPUTED_FROM_M15_HARD_NO_FILL_RANGE_PROOF"
    assert entry_offset["outcome_status"] == "NO_FILL_AT_SHIFT"
    assert entry_offset["strategy_proxy_r"] == 0.0
    assert (
        entry_offset["scoring_boundary"]
        == "M15_HARD_NO_FILL_RANGE_PROOF_ONLY_NO_FILL_OR_TP_INFERENCE"
    )
    assert (
        entry_offset["decision_evidence"]
        == "ENTRY_OFFSET_050R_M15_HARD_NO_FILL_GT_1R_NO_TICK_NEEDED"
    )
    assert (
        entry_offset["claim_decision_scope"]
        == "CURRENT_STRATEGY_CLAIM_ONLY_UNDERLYING_INTELLIGENCE_PRESERVED"
    )
    assert entry_offset["missed_opportunity_audit"]["kill_scope"] == "CURRENT_CLAIM_ONLY"
    assert entry_offset["missed_opportunity_audit"]["preserve_as"] == (
        "FAR_MISS_RETEST_CONTROL_REDESIGN_OR_AVOID_CONTEXT"
    )
    assert (
        entry_offset["entry_offset_no_fill_repair_branch_candidate"]
        == "REDESIGN_ENTRY_OFFSET_NO_FILL_RETEST_SOURCE_COST_FILL_REPAIR_REQUIRED"
    )
    _assert_full_opportunity_preservation(entry_offset)


def test_entry_offset_050r_scores_when_tick_replay_fields_are_captured():
    path = _path()
    path.update(
        {
            "entry_touch_distance_status": "NEAR_MISS_LE_0_25R",
            "nearest_distance_to_entry_r": 0.12,
            "entry_offset_050r_tick_replay_status": "TICK_REPLAY_SOURCE_COMPLETE",
            "entry_offset_050r_outcome_status": "TP1_AFTER_SHIFT_FILL",
            "entry_offset_050r_proxy_r": 0.66567534,
            "entry_offset_050r_shifted_entry_price": 4662.545,
            "entry_offset_050r_shifted_target_r": 0.66666667,
            "entry_offset_050r_fill_first_touch_utc": "2026-05-04T07:22:00+00:00",
            "entry_offset_050r_terminal_event_utc": "2026-05-04T07:31:00+00:00",
            "entry_offset_050r_source_files": ["data/ticks/XAUUSD/2026-05-04.parquet"],
        }
    )
    rows = build_strategy_outcome_rows(
        _candidate_with_entry_offset_strategy(),
        path,
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    entry_offset = {row["strategy_id"]: row for row in rows}["ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"]

    assert entry_offset["strategy_status"] == "SCORED_ENTRY_OFFSET_050R_CONCENTRATION_GUARDED_DEFAULT_OFF"
    assert entry_offset["score_status"] == "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY"
    assert entry_offset["outcome_status"] == "TP1_AFTER_SHIFT_FILL"
    assert entry_offset["strategy_proxy_r"] == 0.66567534
    assert (
        entry_offset["branch_decision"]
        == "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_CONCENTRATION_GUARDED_CANDIDATE"
    )
    assert (
        entry_offset["scoring_boundary"]
        == "PROXY_R_COUNTED_ON_OWNER_ROW_DEFAULT_OFF_CLUSTER_CAP_REQUIRED"
    )
    assert (
        entry_offset["implementation_candidate"]
        == "ENTRY_OFFSET_050R_CLUSTER_GUARDED_DEFAULT_OFF_CHALLENGER"
    )
    assert entry_offset["entry_offset_concentration_guard_status"] == "ENTRY_OFFSET_OWNER_CLUSTER_GUARDED"
    assert entry_offset["entry_offset_original_subtype"] == "NEAR_MISS"
    assert entry_offset["entry_offset_current_evidence_owner_rows"] == 13
    assert entry_offset["opportunity_proxy_reference_status"] == "COUNTED_ON_ENTRY_OFFSET_OWNER_ROW_ONLY"
    assert entry_offset["entry_offset_050r_source_capture_complete"] is True


def test_entry_offset_050r_far_miss_becomes_default_off_retest_control_candidate():
    path = _path()
    path.update(
        {
            "entry_offset_050r_tick_replay_status": "TICK_REPLAY_SOURCE_COMPLETE",
            "entry_offset_050r_outcome_status": "TP1_AFTER_SHIFT_FILL",
            "entry_offset_050r_proxy_r": 0.66716406,
            "entry_offset_050r_shifted_entry_price": 4662.545,
            "entry_offset_050r_shifted_target_r": 0.66666667,
            "entry_offset_050r_fill_first_touch_utc": "2026-05-04T07:22:00+00:00",
            "entry_offset_050r_terminal_event_utc": "2026-05-04T07:31:00+00:00",
            "entry_offset_050r_source_files": ["data/ticks/XAUUSD/2026-05-04.parquet"],
        }
    )
    rows = build_strategy_outcome_rows(
        _candidate_with_entry_offset_strategy(),
        path,
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    entry_offset = {row["strategy_id"]: row for row in rows}["ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"]

    assert (
        entry_offset["strategy_status"]
        == "SCORED_ENTRY_OFFSET_050R_FAR_MISS_CONCENTRATION_GUARDED_DEFAULT_OFF"
    )
    assert entry_offset["score_status"] == "COMPUTED_FROM_SPREAD_AWARE_TICK_REPLAY"
    assert entry_offset["outcome_status"] == "TP1_AFTER_SHIFT_FILL"
    assert entry_offset["strategy_proxy_r"] == 0.66716406
    assert (
        entry_offset["branch_decision"]
        == "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_CONCENTRATION_GUARDED_CANDIDATE"
    )
    assert (
        entry_offset["scoring_boundary"]
        == "PROXY_R_COUNTED_ON_OWNER_ROW_DEFAULT_OFF_CLUSTER_CAP_REQUIRED"
    )
    assert (
        entry_offset["implementation_candidate"]
        == "ENTRY_OFFSET_050R_CLUSTER_GUARDED_DEFAULT_OFF_CHALLENGER"
    )
    assert entry_offset["entry_offset_concentration_guard_status"] == "ENTRY_OFFSET_OWNER_CLUSTER_GUARDED"
    assert entry_offset["entry_offset_original_subtype"] == "FAR_MISS"


def test_moonshot_selected_action_waits_for_required_source_capture():
    rows = build_strategy_outcome_rows(
        _candidate_with_moonshot_strategy("MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN"),
        _path(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    moonshot = {row["strategy_id"]: row for row in rows}["MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN"]

    assert moonshot["strategy_status"] == "WAITING_FOR_MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE"
    assert moonshot["score_status"] == "WAITING_SOURCE"
    assert (
        moonshot["scoring_boundary"]
        == "NO_MOONSHOT_SELECTED_ACTION_PROXY_R_WITHOUT_REQUIRED_SOURCE_CAPTURE"
    )
    assert moonshot["source_capture_missing_fields"] == [
        "moonshot_far_miss_retest_control_key",
        "moonshot_no_fill_distance_bucket",
    ]
    assert moonshot["underlying_intelligence_preserved"] is True
    assert moonshot.get("strategy_proxy_r") is None
    _assert_full_opportunity_preservation(moonshot)


def test_moonshot_selected_action_marks_source_ready_without_counting_proxy():
    path = _path()
    path["moonshot_far_miss_retest_control_key"] = "unit-control"
    path["moonshot_no_fill_distance_bucket"] = "far_miss"
    rows = build_strategy_outcome_rows(
        _candidate_with_moonshot_strategy("MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN"),
        path,
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    moonshot = {row["strategy_id"]: row for row in rows}["MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN"]

    assert moonshot["strategy_status"] == "MOONSHOT_SELECTED_ACTION_SOURCE_READY_SCORER_NOT_IMPLEMENTED"
    assert moonshot["score_status"] == "SOURCE_READY_DEFAULT_OFF_SCORER_NOT_IMPLEMENTED"
    assert moonshot["source_capture_missing_fields"] == []
    assert moonshot["source_capture_ready"] is True
    assert (
        moonshot["scoring_boundary"]
        == "MOONSHOT_SELECTED_ACTION_SOURCE_READY_NEEDS_DEFAULT_OFF_SCORER_IMPLEMENTATION"
    )
    assert moonshot["current_claim_proxy_counted"] is False
    assert moonshot.get("strategy_proxy_r") is None


def test_moonshot_selected_action_consumes_source_capture_row():
    candidate = _candidate_with_moonshot_strategy("MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN")
    source_row = {
        "source_capture_status": "SOURCE_CAPTURE_COMPLETE",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "source_capture_fields": {
            "moonshot_far_miss_retest_control_key": "unit-control",
            "moonshot_no_fill_distance_bucket": "far_miss",
        },
    }
    rows = build_strategy_outcome_rows(
        candidate,
        _path(),
        moonshot_selected_action_source_capture={
            (candidate["candidate_id"], "MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN"): source_row
        },
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    moonshot = {row["strategy_id"]: row for row in rows}["MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN"]

    assert moonshot["strategy_status"] == "MOONSHOT_SELECTED_ACTION_SOURCE_READY_SCORER_NOT_IMPLEMENTED"
    assert moonshot["source_capture_ready"] is True
    assert moonshot["source_capture_missing_fields"] == []
    assert moonshot["moonshot_selected_action_source_capture_status"] == "SOURCE_CAPTURE_COMPLETE"
    assert moonshot["moonshot_selected_action_source_capture_created_at_utc"] == "2026-05-04T08:00:00+00:00"


def test_pending_limit_lifecycle_uses_internal_no_fill_truth():
    path = _path()
    path["tp1_first_touch_utc"] = "2026-05-04T07:31:00+00:00"
    rows = build_strategy_outcome_rows(
        _candidate_with_pending_strategy(),
        path,
        pending_lifecycle_row=_pending_lifecycle(),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    pending = {row["strategy_id"]: row for row in rows}["PENDING_LIMIT_LIFECYCLE"]

    assert pending["strategy_status"] == "SCORED_PENDING_LIFECYCLE_INTERNAL_TRUTH"
    assert pending["score_status"] == "COMPUTED_FROM_PENDING_LIFECYCLE"
    assert pending["outcome_status"] == "NO_FILL_CANCELLED_WRONG_SIDE"
    assert pending["strategy_proxy_r"] == 0.0
    assert pending["pending_lifecycle_match_method"] == "symbol_side_exact_price_geometry"
    assert (
        pending["pending_lifecycle_source_capture_contract"]
        == "pending_limit_lifecycle_v1_source_capture_fields"
    )
    assert pending["pending_lifecycle_source_capture_complete"] is True
    assert (
        pending["pending_lifecycle_source_capture_statuses"]["pending_horizon_start_utc"]
        == "DERIVED_FROM_PENDING_LIFECYCLE_OR_PATH_TIME"
    )
    assert (
        pending["pending_lifecycle_source_capture_statuses"]["terminal_area_touch_status"]
        == "DERIVED_FROM_CANDIDATE_PATH_FOLLOW"
    )
    assert pending["pending_lifecycle_terminal_area_touch_status"] == "TOUCHED"
    assert (
        pending["pending_lifecycle_source_capture_statuses"]["decision_spread_value_source_safe"]
        == "NOT_APPLICABLE_NO_ENTRY_TOUCH_NO_SPREAD_COST"
    )
    assert (
        pending["branch_decision"]
        == "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_RECONSTRUCTED_SOURCE_SCORER"
    )
    assert (
        pending["scoring_boundary"]
        == "PENDING_LIFECYCLE_RECONSTRUCTED_SOURCE_FIELDS_DEFAULT_OFF_NO_EXACT_BROKER_R_RESULT_BOUNDARY"
    )
    assert (
        pending["implementation_candidate"]
        == "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_INTERNAL_TRUTH_SCORER_WITH_RECONSTRUCTED_SOURCE_FIELDS"
    )


def test_pending_limit_lifecycle_reconstructs_decision_spread_from_legacy_spread():
    rows = build_strategy_outcome_rows(
        _candidate_with_pending_strategy(),
        _path(),
        pending_lifecycle_row=_pending_lifecycle(spread=2.5),
        ltf_row=_ltf(
            "ENTRY_THEN_TP1",
            event="2026-05-04T07:31:00+00:00",
            r_value=1.0,
            tp1_first_touch_utc="2026-05-04T07:31:00+00:00",
        ),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    pending = {row["strategy_id"]: row for row in rows}["PENDING_LIMIT_LIFECYCLE"]

    assert pending["pending_lifecycle_source_capture_complete"] is True
    assert pending["pending_lifecycle_decision_spread_value_source_safe"] == 2.5
    assert pending["pending_lifecycle_decision_spread_unit"] == "spread_cents"
    assert (
        pending["pending_lifecycle_source_capture_statuses"]["decision_spread_value_source_safe"]
        == "DERIVED_FROM_PENDING_LIFECYCLE_LEGACY_SPREAD_AS_DECISION_SPREAD_PROXY"
    )
    assert (
        pending["pending_lifecycle_source_capture_derivations"]["decision_spread_value_source_safe"]
        == "DERIVED_FROM_PENDING_LIFECYCLE_LEGACY_SPREAD_AS_DECISION_SPREAD_PROXY"
    )
    assert (
        pending["branch_decision"]
        == "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_RECONSTRUCTED_SOURCE_SCORER"
    )
    assert (
        pending["scoring_boundary"]
        == "PENDING_LIFECYCLE_RECONSTRUCTED_SOURCE_FIELDS_DEFAULT_OFF_NO_EXACT_BROKER_R_RESULT_BOUNDARY"
    )


def test_pending_limit_lifecycle_prefers_nofill_forward_decision_spread_source():
    rows = build_strategy_outcome_rows(
        _candidate_with_pending_strategy(),
        _path(),
        pending_lifecycle_row=_pending_lifecycle(spread=2.5),
        ltf_row=_ltf(
            "ENTRY_THEN_TP1",
            event="2026-05-04T07:31:00+00:00",
            r_value=1.0,
            tp1_first_touch_utc="2026-05-04T07:31:00+00:00",
        ),
        nofill_forward_capture_row=_nofill_forward_capture(
            decision_spread_value_source_safe=1.25,
            created_at_utc="2026-05-04T07:15:31+00:00",
        ),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    pending = {row["strategy_id"]: row for row in rows}["PENDING_LIMIT_LIFECYCLE"]

    assert pending["pending_lifecycle_source_capture_complete"] is True
    assert pending["pending_lifecycle_decision_spread_value_source_safe"] == 1.25
    assert (
        pending["pending_lifecycle_source_capture_statuses"]["decision_spread_value_source_safe"]
        == "DERIVED_FROM_NOFILL_FORWARD_SOURCE_CAPTURE_DECISION_SPREAD"
    )
    assert (
        pending["pending_lifecycle_decision_spread_reconstruction_source"]
        == "nofill_forward_source_capture"
    )
    assert (
        pending["pending_lifecycle_decision_spread_reconstruction_source_status"]
        == "QUOTE_SNAPSHOT_CAPTURED_SOURCE_SAFE"
    )
    assert (
        pending["branch_decision"]
        == "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_RECONSTRUCTED_SOURCE_SCORER"
    )


def test_pending_limit_lifecycle_uses_tick_spread_reconstruction_before_legacy_spread():
    rows = build_strategy_outcome_rows(
        _candidate_with_pending_strategy(),
        _path(),
        pending_lifecycle_row=_pending_lifecycle(spread=2.5),
        ltf_row=_ltf(
            "ENTRY_THEN_TP1",
            event="2026-05-04T07:31:00+00:00",
            r_value=1.0,
            tp1_first_touch_utc="2026-05-04T07:31:00+00:00",
        ),
        tick_spread_reconstruction_row=_tick_spread_reconstruction(
            decision_spread_value_source_safe=0.55,
            tick_offset_seconds=-0.052,
        ),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    pending = {row["strategy_id"]: row for row in rows}["PENDING_LIMIT_LIFECYCLE"]

    assert pending["pending_lifecycle_source_capture_complete"] is True
    assert pending["pending_lifecycle_decision_spread_value_source_safe"] == 0.55
    assert (
        pending["pending_lifecycle_source_capture_statuses"]["decision_spread_value_source_safe"]
        == "DERIVED_FROM_TICK_PARQUET_AT_OR_BEFORE_DECISION_SPREAD"
    )
    assert (
        pending["pending_lifecycle_decision_spread_reconstruction_source"]
        == "tick_parquet_decision_time"
    )
    assert (
        pending["pending_lifecycle_decision_spread_reconstruction_source_status"]
        == "TICK_PARQUET_AT_OR_BEFORE_DECISION_WITHIN_2S_SOURCE_SAFE"
    )
    assert (
        pending["pending_lifecycle_decision_spread_reconstruction_tick_ts_utc"]
        == "2026-05-04T07:14:59.948000+00:00"
    )
    assert pending["pending_lifecycle_decision_spread_reconstruction_tick_offset_seconds"] == -0.052
    assert (
        pending["branch_decision"]
        == "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_RECONSTRUCTED_SOURCE_SCORER"
    )


def test_pending_limit_lifecycle_source_complete_but_r_missing_requires_repair():
    rows = build_strategy_outcome_rows(
        _candidate_with_pending_strategy(),
        _path(),
        pending_lifecycle_row=_pending_lifecycle(
            intent_after_check="order_send_success_filled",
            fill_no_fill_label="filled",
            spread=2.5,
        ),
        ltf_row=_ltf(
            "ENTRY_THEN_TP1",
            event="2026-05-04T07:31:00+00:00",
            r_value=1.0,
            tp1_first_touch_utc="2026-05-04T07:31:00+00:00",
        ),
        tick_spread_reconstruction_row=_tick_spread_reconstruction(
            decision_spread_value_source_safe=0.55,
            tick_offset_seconds=-0.052,
        ),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    pending = {row["strategy_id"]: row for row in rows}["PENDING_LIMIT_LIFECYCLE"]

    assert pending["pending_lifecycle_source_capture_complete"] is True
    assert pending["score_status"] == "WAITING_FOR_PENDING_LIFECYCLE_R"
    assert (
        pending["branch_decision"]
        == "REDESIGN_PENDING_LIFECYCLE_R_OUTCOME_SOURCE_REQUIRED"
    )
    assert (
        pending["implementation_candidate"]
        == "REPAIR_PENDING_LIFECYCLE_FILLED_OR_RETRY_R_OUTCOME_SOURCE"
    )


def test_pending_limit_lifecycle_filled_r_repairs_from_entry_path_proxy():
    rows = build_strategy_outcome_rows(
        _candidate_with_pending_strategy(),
        _ambiguous_path(),
        pending_lifecycle_row=_pending_lifecycle(
            intent_after_check="order_send_success_filled",
            fill_no_fill_label="filled",
            spread=2.5,
        ),
        ltf_row=_ltf(
            "ENTRY_THEN_TP1",
            event="2026-05-04T07:31:00+00:00",
            r_value=1.5,
            tp1_first_touch_utc="2026-05-04T07:31:00+00:00",
            sl_first_touch_utc="2026-05-04T07:45:00+00:00",
        ),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    pending = {row["strategy_id"]: row for row in rows}["PENDING_LIMIT_LIFECYCLE"]

    assert pending["pending_lifecycle_source_capture_complete"] is True
    assert pending["score_status"] == "COMPUTED_FROM_PENDING_LIFECYCLE_PATH_PROXY_REPAIR"
    assert pending["outcome_status"] == "BROKER_FILLED_SYNTHETIC_PATH_R_REPAIRED"
    assert pending["outcome_source"] == "candidate_ltf_path_order"
    assert pending["strategy_proxy_r"] == 1.5
    assert (
        pending["branch_decision"]
        == "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_FILLED_PATH_PROXY_REPAIRED"
    )
    assert (
        pending["scoring_boundary"]
        == "PENDING_LIFECYCLE_FILLED_PATH_PROXY_DEFAULT_OFF_NO_BROKER_ACTUAL_R_RESULT_BOUNDARY"
    )
    assert (
        pending["pending_lifecycle_r_repair_status"]
        == "FILLED_R_REPAIRED_FROM_CANDIDATE_PATH_PROXY"
    )
    assert pending["pending_lifecycle_proxy_r_reference"] == 1.5
    assert (
        pending["pending_lifecycle_broker_actual_r_status"]
        == "BROKER_ACTUAL_R_NOT_CAPTURED_PATH_PROXY_ONLY"
    )


def test_pending_limit_lifecycle_hypothetical_path_has_decision_metadata():
    candidate = _candidate_with_pending_strategy()
    candidate["final_outcome_at_log"] = "CANDIDATE"
    rows = build_strategy_outcome_rows(
        candidate,
        _path(),
        pending_lifecycle_row=None,
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    pending = {row["strategy_id"]: row for row in rows}["PENDING_LIMIT_LIFECYCLE"]

    assert pending["strategy_status"] == "MERGED_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_PROXY_REFERENCE"
    assert pending["strategy_proxy_r"] is None
    assert pending["pending_hypothetical_proxy_reference_r"] == 0.0
    assert (
        pending["branch_decision"]
        == "MERGE_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_PROXY_TO_ENTRY_GEOMETRY_OWNER"
    )
    assert (
        pending["decision_evidence"]
        == "NO_LIVE_PENDING_LIMIT_INTENT_SHARED_CANDIDATE_PATH_DUPLICATE_NOT_LIFECYCLE_TRUTH"
    )
    assert (
        pending["scoring_boundary"]
        == "REFERENCE_ONLY_HYPOTHETICAL_PENDING_LIMIT_PATH_PROXY_NOT_LIFECYCLE_TRUTH"
    )
    assert (
        pending["implementation_candidate"]
        == "MERGE_HYPOTHETICAL_PENDING_LIMIT_PATH_EVIDENCE_TO_ENTRY_GEOMETRY_OWNER"
    )
    assert (
        pending["opportunity_proxy_reference_status"]
        == "REFERENCE_ONLY_NO_LIVE_PENDING_LIMIT_INTENT_NOT_COUNTED"
    )
    _assert_full_opportunity_preservation(pending)


def test_pending_limit_lifecycle_derives_first_touch_from_ltf_path_order():
    path = _path()
    path["hit_tp1"] = None
    path["hit_sl"] = None
    ltf = _ltf(
        "ENTRY_THEN_SL",
        tp1_first_touch_utc="2026-05-04T07:31:00+00:00",
        sl_first_touch_utc="2026-05-04T07:35:00+00:00",
    )
    rows = build_strategy_outcome_rows(
        _candidate_with_pending_strategy(),
        path,
        pending_lifecycle_row=_pending_lifecycle(),
        ltf_row=ltf,
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    pending = {row["strategy_id"]: row for row in rows}["PENDING_LIMIT_LIFECYCLE"]

    assert pending["pending_lifecycle_terminal_area_touch_status"] == "TOUCHED"
    assert pending["pending_lifecycle_terminal_area_first_touch_utc"] == "2026-05-04T07:31:00+00:00"
    assert pending["pending_lifecycle_protective_area_touch_status"] == "TOUCHED"
    assert pending["pending_lifecycle_protective_area_first_touch_utc"] == "2026-05-04T07:35:00+00:00"
    assert (
        pending["pending_lifecycle_source_capture_statuses"]["terminal_area_touch_status"]
        == "DERIVED_FROM_CANDIDATE_LTF_PATH_ORDER"
    )
    assert (
        pending["pending_lifecycle_source_capture_statuses"]["terminal_area_first_touch_utc"]
        == "DERIVED_FROM_CANDIDATE_LTF_PATH_ORDER"
    )
    assert (
        pending["pending_lifecycle_source_capture_statuses"]["protective_area_touch_status"]
        == "DERIVED_FROM_CANDIDATE_LTF_PATH_ORDER"
    )
    assert (
        pending["pending_lifecycle_source_capture_statuses"]["protective_area_first_touch_utc"]
        == "DERIVED_FROM_CANDIDATE_LTF_PATH_ORDER"
    )


def test_ambiguous_m15_path_uses_ltf_terminal_sl_for_entry_models():
    rows = build_strategy_outcome_rows(
        _candidate(),
        _ambiguous_path(),
        ltf_row=_ltf("ENTRY_THEN_SL"),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    by_id = {row["strategy_id"]: row for row in rows}

    baseline = by_id["LIVE_AI_J46_J49_BASELINE_COMPARATOR"]
    assert baseline["score_status"] == "COMPUTED_FROM_LTF_PATH_ORDER"
    assert baseline["outcome_status"] == "ENTRY_TOUCHED_THEN_SL"
    assert baseline["strategy_proxy_r"] == -1.0
    assert baseline["outcome_source"] == "candidate_ltf_path_order"


def test_ambiguous_same_m1_ltf_order_is_not_r_counted():
    rows = build_strategy_outcome_rows(
        _candidate(),
        _ambiguous_path(),
        ltf_row=_ltf("ENTRY_THEN_SL_SAME_M1_AMBIGUOUS", r_value=None),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )
    baseline = {row["strategy_id"]: row for row in rows}["LIVE_AI_J46_J49_BASELINE_COMPARATOR"]

    assert baseline["score_status"] == "AMBIGUOUS_LTF_ORDER"
    assert baseline["outcome_status"] == "ENTRY_THEN_SL_SAME_M1_AMBIGUOUS"
    assert baseline["strategy_proxy_r"] is None


def test_nas100_depth_source_repair_attaches_extracted_context_without_proxy_r():
    candidate = _candidate_with_nas100_depth_strategy()
    repair_key = (candidate["candidate_id"], "NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC")
    rows = build_strategy_outcome_rows(
        candidate,
        _nas100_path(),
        nas100_depth_source_repairs={
            repair_key: {
                "candidate_id": candidate["candidate_id"],
                "strategy_id": "NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC",
                "source_decision_status": "SIERRA_DEPTH_FEATURES_EXTRACTED_SOURCE_COMPLETE",
                "feature_status": "FEATURES_EXTRACTED",
                "features_present": True,
                "branch_decision": "KEEP_NAS100_DEPTH_THINNESS_CONTEXT_SOURCE_COMPLETE_DIAGNOSTIC",
                "source_artifact": "shadow_logs/nas100_depth_thinness_current_source_repair_decisions.jsonl",
                "feature_row_key": "unit-feature-row",
                "depth_path": "C:/SierraChart/Data/MarketDepthData/NQM26-CME.2026-05-04.depth",
                "features": {
                    "pre60_median_total_depth10": 52.0,
                    "event15_median_total_depth10": 51.0,
                    "event15_thin_depth10_rate": 0.3292410714,
                    "event15_sample_count": 896,
                },
            }
        },
        created_at_utc="2026-05-04T14:15:10+00:00",
    )
    depth = {row["strategy_id"]: row for row in rows}["NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC"]

    assert depth["strategy_status"] == "SCORED_DEPTH_THINNESS_CONTEXT_SOURCE_COMPLETE"
    assert depth["score_status"] == "CONTEXT_ATTACHED"
    assert depth["branch_decision"] == "KEEP_NAS100_DEPTH_THINNESS_CONTEXT_SOURCE_COMPLETE_DIAGNOSTIC"
    assert depth["strategy_proxy_r"] is None
    assert depth["depth_thinness_feature_status"] == "FEATURES_EXTRACTED"
    assert depth["depth_thinness_event15_median_total_depth10"] == 51.0
    assert depth["depth_thinness_event15_sample_count"] == 896


def test_nas100_depth_source_repair_converts_no_samples_to_redesign_with_audit():
    candidate = _candidate_with_nas100_depth_strategy()
    repair_key = (candidate["candidate_id"], "NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC")
    rows = build_strategy_outcome_rows(
        candidate,
        _nas100_path(),
        nas100_depth_source_repairs={
            repair_key: {
                "candidate_id": candidate["candidate_id"],
                "strategy_id": "NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC",
                "source_decision_status": "SIERRA_DEPTH_ATTEMPTED_NO_SAMPLES_SOURCE_COMPLETE_NO_CONTEXT",
                "feature_status": "FEATURES_ATTEMPTED_NO_SAMPLES",
                "features_present": False,
                "branch_decision": "REDESIGN_NAS100_DEPTH_THINNESS_NO_SAMPLES_SOURCE_BOUNDARY",
                "depth_path": "C:/SierraChart/Data/MarketDepthData/NQM26-CME.2026-05-04.depth",
                "missing_field": "predecision_sierra_depth_samples",
            }
        },
        created_at_utc="2026-05-04T14:15:10+00:00",
    )
    depth = {row["strategy_id"]: row for row in rows}["NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC"]

    assert depth["strategy_status"] == "REDESIGN_DEPTH_THINNESS_CONTEXT_NO_SAMPLES"
    assert depth["score_status"] == "SOURCE_COMPLETE_NO_SAMPLES"
    assert depth["strategy_proxy_r"] is None
    assert depth["underlying_intelligence_preserved"] is True
    assert depth["missed_opportunity_audit"]["current_claim"] == (
        "REDESIGN_NAS100_DEPTH_THINNESS_NO_SAMPLES_SOURCE_BOUNDARY"
    )


def test_run_dedupes_candidate_strategy_asof(tmp_path):
    candidates = tmp_path / "candidates.jsonl"
    paths = tmp_path / "paths.jsonl"
    output = tmp_path / "out.jsonl"
    _write_jsonl(candidates, [_candidate()])
    _write_jsonl(paths, [_path()])

    first = run(candidates_path=candidates, paths_path=paths, ltf_path_order_path=tmp_path / "missing_ltf.jsonl", output_path=output)
    second = run(candidates_path=candidates, paths_path=paths, ltf_path_order_path=tmp_path / "missing_ltf.jsonl", output_path=output)

    assert first["rows_written"] == 3
    assert second["rows_written"] == 0
    assert second["skipped"]["duplicate_candidate_strategy_asof"] == 3
    assert len(output.read_text(encoding="utf-8").splitlines()) == 3


def test_latest_path_rows_by_candidate_keeps_latest_asof():
    early = _path()
    late = json.loads(json.dumps(_path()))
    late["asof_latest_candle_utc"] = "2026-05-04T08:15:00+00:00"
    late["path_label"] = "entry_touched_unresolved"

    rows = latest_path_rows_by_candidate([late, early])

    assert len(rows) == 1
    assert rows[0]["asof_latest_candle_utc"] == "2026-05-04T08:15:00+00:00"
    assert rows[0]["path_label"] == "entry_touched_unresolved"


def test_run_latest_paths_dry_run_materializes_without_appending(tmp_path):
    candidates = tmp_path / "candidates.jsonl"
    paths = tmp_path / "paths.jsonl"
    output = tmp_path / "out.jsonl"
    dry_rows = tmp_path / "dry_rows.jsonl"
    late = json.loads(json.dumps(_path()))
    late["asof_latest_candle_utc"] = "2026-05-04T08:15:00+00:00"
    late["path_label"] = "entry_touched_unresolved"
    late["hit_tp1"] = False
    _write_jsonl(candidates, [_candidate()])
    _write_jsonl(paths, [_path(), late])

    summary = run(
        candidates_path=candidates,
        paths_path=paths,
        ltf_path_order_path=tmp_path / "missing_ltf.jsonl",
        output_path=output,
        latest_paths_only=True,
        dry_run=True,
        dry_run_output_path=dry_rows,
    )
    rows = [json.loads(line) for line in dry_rows.read_text(encoding="utf-8").splitlines()]

    assert summary["dry_run"] is True
    assert summary["latest_paths_only"] is True
    assert summary["path_rows_seen"] == 2
    assert summary["path_rows_evaluated"] == 1
    assert summary["rows_written"] == 0
    assert summary["rows_would_write"] == 3
    assert output.exists() is False
    assert len(rows) == 3
    assert {row["asof_latest_candle_utc"] for row in rows} == {"2026-05-04T08:15:00+00:00"}
    assert {row["dry_run_append_status"] for row in rows} == {"WOULD_APPEND_NEW"}


def test_run_appends_source_provenance_correction_when_path_source_upgrades(tmp_path):
    candidates = tmp_path / "candidates.jsonl"
    paths = tmp_path / "paths.jsonl"
    output = tmp_path / "out.jsonl"
    _write_jsonl(candidates, [_candidate()])
    _write_jsonl(paths, [_path()])
    existing = build_strategy_outcome_rows(
        _candidate(),
        _path(),
        created_at_utc="2026-05-04T07:50:00+00:00",
    )
    for row in existing:
        if row["strategy_id"] == "LIVE_AI_J46_J49_BASELINE_COMPARATOR":
            row.pop("m15_path_provenance_status", None)
            row.pop("m15_spread_source_status", None)
            row.pop("m15_spread_mean", None)
    _write_jsonl(output, existing)

    summary = run(
        candidates_path=candidates,
        paths_path=paths,
        ltf_path_order_path=tmp_path / "missing_ltf.jsonl",
        output_path=output,
    )
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    latest_baseline = [
        row for row in rows if row["strategy_id"] == "LIVE_AI_J46_J49_BASELINE_COMPARATOR"
    ][-1]

    assert summary["rows_written"] == 1
    assert latest_baseline["m15_path_provenance_status"] == "M15_SPREAD_SOURCE_CAPTURED"
    assert latest_baseline["m15_spread_mean"] == 10
    assert latest_baseline["correction_reason"] == "latest_computed_shadow_outcome_changed_after_source_reconciliation"


def test_run_appends_scorer_boundary_correction_when_existing_row_lacks_it(tmp_path):
    candidates = tmp_path / "candidates.jsonl"
    paths = tmp_path / "paths.jsonl"
    output = tmp_path / "out.jsonl"
    candidate = _candidate_with_structural_sources()
    _write_jsonl(candidates, [candidate])
    _write_jsonl(paths, [_path()])
    existing = build_strategy_outcome_rows(
        candidate,
        _path(),
        created_at_utc="2026-05-04T07:50:00+00:00",
    )
    for row in existing:
        if row["strategy_id"] == "V3_OB_LOCK_PULLBACK_RISK_BANK":
            row.pop("scoring_boundary", None)
            row.pop("implementation_candidate", None)
    _write_jsonl(output, existing)

    summary = run(
        candidates_path=candidates,
        paths_path=paths,
        ltf_path_order_path=tmp_path / "missing_ltf.jsonl",
        output_path=output,
    )
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    latest_structural = [row for row in rows if row["strategy_id"] == "V3_OB_LOCK_PULLBACK_RISK_BANK"][-1]

    assert summary["rows_written"] == 1
    assert (
        latest_structural["scoring_boundary"]
        == "NO_SEPARATE_V3_STRUCTURAL_LOCK_IMPLEMENTATION_FROM_DUPLICATED_SHARED_CANDIDATE_PATH_PROXY"
    )
    assert (
        latest_structural["implementation_candidate"]
        == "MERGE_INTO_CANONICAL_V2_STRUCT_COMPOSITE_ANY_SCORER_NO_DUPLICATE_R"
    )
    assert latest_structural["structural_duplicate_proxy_reference_r"] == 0.0
    assert latest_structural["correction_reason"] == "latest_computed_shadow_outcome_changed_after_source_reconciliation"


def test_run_appends_pending_lifecycle_correction_when_source_changes(tmp_path):
    candidates = tmp_path / "candidates.jsonl"
    paths = tmp_path / "paths.jsonl"
    lifecycle = tmp_path / "pending.jsonl"
    output = tmp_path / "out.jsonl"
    candidate = _candidate_with_pending_strategy()
    _write_jsonl(candidates, [candidate])
    _write_jsonl(paths, [_path()])
    _write_jsonl(lifecycle, [_pending_lifecycle()])
    _write_jsonl(
        output,
        [
            {
                "schema_version": "live_mechanical_strategy_shadow_outcome_v1",
                "created_at_utc": "2026-05-04T07:50:00+00:00",
                "candidate_id": candidate["candidate_id"],
                "strategy_id": "PENDING_LIMIT_LIFECYCLE",
                "asof_latest_candle_utc": "2026-05-04T07:45:00+00:00",
                "strategy_status": "SCORED_SHARED_CANDIDATE_PATH",
                "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
                "outcome_status": "ENTRY_TOUCHED_THEN_SL",
                "status_reason": "old generic path row",
            }
        ],
    )

    summary = run(
        candidates_path=candidates,
        paths_path=paths,
        pending_lifecycle_path=lifecycle,
        ltf_path_order_path=tmp_path / "missing_ltf.jsonl",
        output_path=output,
    )
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    latest_pending = [row for row in rows if row["strategy_id"] == "PENDING_LIMIT_LIFECYCLE"][-1]

    assert summary["rows_written"] == 4
    assert latest_pending["outcome_status"] == "NO_FILL_CANCELLED_WRONG_SIDE"
    assert latest_pending["score_status"] == "COMPUTED_FROM_PENDING_LIFECYCLE"
    assert latest_pending["correction_reason"] == "latest_computed_shadow_outcome_changed_after_source_reconciliation"
