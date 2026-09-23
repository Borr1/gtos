from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from src.models.analysis_models import (
    DailyBiasAnalysis,
    H1SetupAnalysis,
    H4AlignmentAnalysis,
    LiquiditySweepAnalysis,
    M15ConfirmationAnalysis,
    PrimaryAnalysisOutput,
    PrimaryAnalysisReasoning,
    TradeParameters,
)
from src.research_infra.forward_capture import (
    COMMON_METADATA_FIELDS,
    NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUSES,
    NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS,
    NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES,
    NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS,
    NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION,
    RESULT_USE_STATUS,
    build_moonshot_selected_action_source_capture_row,
    build_nofill_forward_source_capture_row,
    build_strategy_follow_candidate_row,
    build_context_control_row,
    build_fvg_ob_confluence_row,
    build_prefill_delivery_path_row,
    build_v2b_forward_pair_row,
    record_nofill_forward_source_capture,
    record_moonshot_selected_action_source_capture,
    record_live_candidate_forward_shadow,
    record_live_mso_forward_shadow,
    record_strategy_follow_candidate,
    record_context_control,
    record_fvg_ob_confluence,
    record_prefill_delivery_path,
    record_v2b_forward_pair,
    validate_nofill_forward_source_capture_row,
)


def _read_one(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8").splitlines()[0])


def _base_fields() -> dict:
    return {
        "symbol": "NAS100",
        "broker_symbol": "NAS100",
        "source_symbol": "NQ.v.0",
        "market_timeframe": "M15",
        "route_session": "ny",
        "horizon_id": "live_candidate_decision",
        "source_component": "primary_analyzer_live_candidate",
        "selected_side": "LONG",
        "session": "ny",
        "kill_zone": "ny",
        "side": "LONG",
        "regime": "trending_bull",
        "candidate_id": "NAS100_20260504T1330_candidate_1",
        "trade_id": "lim_2026-05-04_1330",
        "decision_time_utc": "2026-05-04T13:30:00+00:00",
        "source_file": "shadow_logs/candidate_features_log.jsonl",
        "source_hash": "abc123",
    }


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


def _nofill_source_fields() -> dict:
    return {
        **_base_fields(),
        "created_at_utc": "2026-05-04T13:30:02+00:00",
        "capture_write_started_at_utc": "2026-05-04T13:30:02.100000+00:00",
        "capture_write_completed_at_utc": "2026-05-04T13:30:02.140000+00:00",
        "capture_clock_skew_ms": 25,
        "capture_clock_skew_status": "BROKER_CLOCK_WITHIN_CAPTURE_TOLERANCE",
        "pending_order_mode": "INTERNAL_CANDLE_POLLED_INTENT",
        "broker_pending_order_created": False,
        "native_pending_order_type": "INTERNAL_CANDLE_POLLED_INTENT",
        "decision_spread_value_source_safe": 12.0,
        "decision_spread_unit": "spread_cents",
        "entry_touch_spread_value_source_safe": 14.0,
        "entry_touch_spread_unit": "spread_cents",
        "pending_created_time_utc": "2026-05-04T13:30:03+00:00",
        "pending_horizon_end_utc": "2026-05-06T13:30:03+00:00",
        "expiry_time_utc": "2026-05-06T13:30:03+00:00",
        "cancel_reason": "48h clock expiry",
        "entry_touch_first_utc": "2026-05-04T13:45:00+00:00",
        "trigger_condition_met": True,
        "terminal_area_touch_status": "TERMINAL_AREA_NOT_TOUCHED_SOURCE_SAFE",
        "terminal_area_first_touch_utc": None,
        "protective_area_touch_status": "PROTECTIVE_AREA_NOT_TOUCHED_SOURCE_SAFE",
        "protective_area_first_touch_utc": None,
        "event_order_resolution_method": "M1_PATH_ORDERED_NO_SAME_TICK_AMBIGUITY",
        "same_tick_same_bar_ambiguity_status": "NO_SAME_TICK_OR_SAME_BAR_AMBIGUITY",
        "lower_tf_coverage_window_start_utc": "2026-05-04T13:30:00+00:00",
        "lower_tf_coverage_window_end_utc": "2026-05-06T13:30:00+00:00",
        "missing_coverage_intervals": [],
        "sample_floor_policy_id": "NOFILL_SOURCE_CAPTURE_CONTROL_ONLY_SAMPLE_FLOOR_NOT_VALIDATION",
    }


def test_v2b_forward_pair_row_has_required_lanes():
    row = build_v2b_forward_pair_row(
        **_base_fields(),
        ob_boundary_outcome={"label_status": "unresolved"},
        j46_baseline_outcome={"label_status": "unresolved"},
        fixed_r_comparator={"label_status": "unresolved"},
        fvg_comparator={"label_status": "unresolved"},
        lower_timeframe_available=True,
        same_bar_ambiguity_state="unresolved",
        cost_sensitivity={"0.05R": None},
        source_period="forward_2026",
        path_label_status="WAITING_FOR_FORWARD_ROWS",
        actual_synthetic_label_lane="synthetic_path_pending",
    )

    for field in COMMON_METADATA_FIELDS:
        assert field in row
    _assert_cp281_event_contract(row)
    assert row["schema_version"] == "v2b_forward_pair_v1"
    assert row["result_use_status"] == RESULT_USE_STATUS
    assert row["resolved_pair"] is True
    assert row["ob_boundary_outcome"]["label_status"] == "unresolved"


def test_nofill_source_capture_row_covers_accepted_55_field_contract():
    row = build_nofill_forward_source_capture_row(**_nofill_source_fields())
    validation = validate_nofill_forward_source_capture_row(row)

    assert row["schema_version"] == NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION
    assert validation["ok"] is True
    assert validation["present_field_count"] == 55
    assert set(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS).issubset(row)
    assert row["result_use_status"] == RESULT_USE_STATUS
    assert row["validation_result_status"] is False
    assert row["outcome_result_rows_status"] is False
    assert row["broker_runtime_change_status"] is False
    assert row["opens_result_scoring"] is False
    assert row["opens_live_trading_behavior"] is False
    assert row["capture_latency_ms"] == 40
    assert row["decision_spread_value_source_safe"] == 12.0
    assert row["entry_touch_spread_value_source_safe"] == 14.0


def test_nofill_source_capture_future_fields_emit_or_fail_closed():
    row = build_nofill_forward_source_capture_row(**_base_fields())

    assert set(NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS).issubset(row)
    for field in NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS:
        assert row[field] is not None
        if field in {
            "capture_write_started_at_utc",
            "capture_write_completed_at_utc",
            "capture_latency_ms",
            "capture_clock_skew_ms",
            "capture_clock_skew_status",
            "native_pending_order_type_source_safe",
            "native_pending_order_type_status",
            "decision_spread_status",
            "decision_spread_value_source_safe",
            "decision_spread_unit",
            "entry_touch_spread_status",
            "entry_touch_spread_value_source_safe",
            "spread_source_hash",
            "pending_horizon_start_utc",
            "pending_horizon_end_utc",
            "terminal_area_touch_status",
            "terminal_area_first_touch_utc",
            "protective_area_touch_status",
            "protective_area_first_touch_utc",
        }:
            assert row[field] in NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUSES


def test_nofill_source_capture_redacts_forbidden_raw_values():
    row = build_nofill_forward_source_capture_row(
        **_nofill_source_fields(),
        mt5_order_ticket="SECRET_TICKET_123",
        pending_ticket="SECRET_PENDING_456",
        slippage_price="SECRET_SLIPPAGE",
        execution_quality="SECRET_EXECUTION",
        actual_r="SECRET_RESULT_R",
    )
    payload = json.dumps(row, sort_keys=True)

    assert "SECRET_" not in payload
    assert not (set(row) & NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES)
    assert row["raw_ticket_field_present_status"] == "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
    assert row["mt5_order_ticket_redaction_status"] == "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
    assert row["slippage_value_redaction_status"] == "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
    assert row["execution_quality_value_redaction_status"] == "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
    assert row["cost_testing_gate_status"] == "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
    assert row["forbidden_field_scan_status"] == "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"


def test_nofill_source_capture_writer_appends_and_returns_none(tmp_path):
    path = tmp_path / "nofill_forward_source_capture.jsonl"

    result = record_nofill_forward_source_capture(_nofill_source_fields(), log_path=path)

    row = _read_one(path)
    assert result is None
    assert row["schema_version"] == NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION
    assert validate_nofill_forward_source_capture_row(row)["ok"] is True


def test_nofill_source_capture_writer_failure_is_fail_open(monkeypatch):
    import src.research_infra.forward_capture as forward_capture_mod

    def _boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(forward_capture_mod, "append_jsonl", _boom)

    result = record_nofill_forward_source_capture(_nofill_source_fields())

    assert result is None


def test_moonshot_selected_action_source_capture_row_tracks_required_fields():
    row = build_moonshot_selected_action_source_capture_row(
        **_base_fields(),
        strategy_id="MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN",
        source_capture_required_fields=[
            "moonshot_far_miss_retest_control_key",
            "moonshot_no_fill_distance_bucket",
        ],
        source_capture_fields={
            "moonshot_far_miss_retest_control_key": "control-1",
        },
    )

    assert row["schema_version"] == "moonshot_selected_action_source_capture_v1"
    assert row["source_capture_status"] == "SOURCE_CAPTURE_INCOMPLETE"
    assert row["source_capture_missing_fields"] == ["moonshot_no_fill_distance_bucket"]
    assert row["candidate_use_allowed_now"] is False
    assert row["runtime_score_allowed"] is False
    assert row["proxy_delta_reference_counted_as_r"] is False


def test_record_moonshot_selected_action_source_capture_appends_row(tmp_path):
    path = tmp_path / "moonshot_selected_action_source_capture.jsonl"

    result = record_moonshot_selected_action_source_capture(
        {
            **_base_fields(),
            "strategy_id": "MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN",
            "source_capture_required_fields": [
                "moonshot_far_miss_retest_control_key",
            ],
            "source_capture_fields": {
                "moonshot_far_miss_retest_control_key": "control-1",
            },
        },
        log_path=path,
    )

    row = _read_one(path)
    assert result is None
    assert row["source_capture_status"] == "SOURCE_CAPTURE_COMPLETE"
    assert row["scorer_ready_status"] == "SOURCE_READY_SCORER_NOT_IMPLEMENTED"


def test_v2b_forward_pair_appends_jsonl(tmp_path):
    path = tmp_path / "v2b.jsonl"
    record_v2b_forward_pair({**_base_fields()}, log_path=path)

    row = _read_one(path)
    assert row["schema_version"] == "v2b_forward_pair_v1"
    assert row["candidate_id"] == "NAS100_20260504T1330_candidate_1"


def test_prefill_delivery_path_row_preserves_no_leak_fields(tmp_path):
    path = tmp_path / "prefill.jsonl"
    record_prefill_delivery_path(
        {
            **_base_fields(),
            "structural_setup_id": "setup_1",
            "original_poi_bounds": {"low": 100.0, "high": 101.0},
            "entry_arming_time_utc": "2026-05-04T13:31:00+00:00",
            "pre_fill_candles": [{"time": "2026-05-04T13:30:00+00:00"}],
            "delivery_leg_direction": "down_to_poi",
            "reversal_leg_timing": None,
            "fill_happened": False,
            "cancel_expiry_abort_reason": "still_pending",
            "lower_timeframe_path_ordering": "unresolved",
            "fvg_ob_swing_state_at_arm": {"ob": "armed"},
        },
        log_path=path,
    )

    row = _read_one(path)
    assert row["schema_version"] == "prefill_delivery_path_v1"
    assert row["original_poi_bounds"] == {"low": 100.0, "high": 101.0}
    assert row["result_use_status"] == RESULT_USE_STATUS


def test_fvg_ob_confluence_row_flags_post_outcome_leak():
    clean = build_fvg_ob_confluence_row(
        **_base_fields(),
        bucket="both_fvg_and_ob_fire",
        decision_time_fields={"ob_touch_count": 1, "fvg_gap_ticks": 12},
    )
    leaked = build_fvg_ob_confluence_row(
        **_base_fields(),
        bucket="both_fvg_and_ob_fire",
        decision_time_fields={"actual_r": 1.0, "fvg_gap_ticks": 12},
    )

    assert clean["no_leak_status"] == "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT"
    assert leaked["no_leak_status"] == "POST_OUTCOME_FIELD_PRESENT:actual_r"


def test_fvg_ob_confluence_appends_jsonl(tmp_path):
    path = tmp_path / "confluence.jsonl"
    record_fvg_ob_confluence(
        {
            **_base_fields(),
            "bucket": "fvg_only",
            "touch_count": 1,
            "poi_quality": "research_only",
            "lower_timeframe_available": True,
            "candidate_outcome_lane": "synthetic_path_pending",
            "decision_time_fields": {"ob_present": False, "fvg_present": True},
            "fvg_bounds": {"low": 100.0, "high": 101.0, "source_status": "TEST_CAPTURED"},
        },
        log_path=path,
    )

    row = _read_one(path)
    assert row["bucket"] == "fvg_only"
    assert row["schema_version"] == "fvg_ob_confluence_forward_v1"
    assert row["fvg_bounds"] == {"low": 100.0, "high": 101.0, "source_status": "TEST_CAPTURED"}


def test_context_control_row_is_control_only(tmp_path):
    path = tmp_path / "context.jsonl"
    record_context_control(
        {
            **_base_fields(),
            "context_question_id": "VIX_VXM_VOL_REGIME_CONTEXT_V1",
            "context_family": "VIX/VXM",
            "asof_timestamp_convention": "latest_observation_at_or_before_decision_time",
            "join_rule": "left_join_by_decision_time_no_forward_fill_after_event",
            "context_values": {"vxm_available": False},
        },
        log_path=path,
    )

    row = _read_one(path)
    assert row["schema_version"] == "context_control_forward_v1"
    assert row["control_only"] is True
    assert row["evidence_class"] == "CONTROL_ONLY"
    assert row["control_role"] == "CONTROL_ONLY"
    assert row["direct_strategy_validation_status"] == "NOT_DIRECT_STRATEGY_VALIDATION"
    assert row["strategy_validation_status"] == "CONTROL_CONTEXT_ONLY_NOT_STRATEGY_VALIDATION"
    assert row["validation_scope"] == "EXPLORATORY_CONTEXT_ONLY"


def test_prefill_builder_defaults_to_result_use_status():
    row = build_prefill_delivery_path_row(**_base_fields())
    assert row["result_use_status"] == RESULT_USE_STATUS
    assert row["pre_fill_candles"] == []


def test_strategy_follow_candidate_row_carries_registry_and_external_confluence():
    row = build_strategy_follow_candidate_row(
        **_base_fields(),
        analysis_decision="CANDIDATE",
        framework="ob_retest",
        final_outcome="LIMIT_PLACED",
        external_confluence={
            "sierra": {"status": "FEATURES_EXTRACTED"},
            "databento": {"status": "NOT_FETCHED_OR_NO_CACHE_FOR_LIVE_CANDIDATE"},
        },
    )

    strategy_ids = {item["strategy_id"] for item in row["strategy_snapshots"]}
    snapshots = {item["strategy_id"]: item for item in row["strategy_snapshots"]}
    assert row["schema_version"] == "strategy_follow_candidate_v1"
    assert "V2_STRUCT_OB_BOUNDARY" in strategy_ids
    assert "V3_FVG_ONLY_RESCUE_RISK_BANK" in strategy_ids
    assert (
        snapshots["V2_STRUCT_OB_BOUNDARY"]["branch_decision"]
        == "PRESERVE_DEFAULT_OFF_SHADOW_OB_BOUNDARY_PROXY_ONLY"
    )
    assert (
        snapshots["V2_STRUCT_FVG_MID_EDGE"]["branch_decision"]
        == "IMPLEMENT_SHADOW_SCORER_STANDALONE_FVG_POI_DEFAULT_OFF_WITH_ROW_LEVEL_SOURCE_GATES"
    )
    assert (
        snapshots["V2_STRUCT_SWING_PROTECTED"]["branch_decision"]
        == "IMPLEMENT_SHADOW_SCORER_SWING_PROTECTED_STOP_DEFAULT_OFF_WITH_ROW_LEVEL_SOURCE_GATES"
    )
    assert (
        snapshots["V3_OB_LOCK_PULLBACK_RISK_BANK"]["branch_decision"]
        == "IMPLEMENT_SHADOW_SCORER_STRUCTURAL_METADATA_SHARED_PATH_DEFAULT_OFF_WITH_AMBIGUITY_EXCLUSION"
    )
    assert (
        snapshots["FVG_OB_CONFLUENCE_OB_AFTER_FVG"]["branch_decision"]
        == "KEEP_DEFAULT_OFF_FVG_OB_BUCKET_SHARED_PATH_PROXY_SCORER_NO_EXACT_BOUNDS_CLAIM"
    )
    assert (
        snapshots["PREFILL_DELIVERY_REVERSAL_PATH"]["branch_decision"]
        == "MERGE_PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE"
    )
    assert (
        snapshots["PREFILL_DELIVERY_REVERSAL_PATH"]["implementation_candidate"]
        == "PREFILL_TP_AFTER_FILL_CONTEXT_MERGED_TO_ENTRY_OFFSET_CLUSTER_GUARD"
    )
    assert (
        snapshots["V3_OB_LOCK_PULLBACK_RISK_BANK"]["implementation_candidate"]
        == "KEEP_DEFAULT_OFF_STRUCTURAL_METADATA_SHARED_PATH_PROXY_SCORER_AND_DESIGN_EXACT_LOCK_REENTRY_SCORER"
    )
    assert (
        snapshots["FVG_OB_CONFLUENCE_OB_AFTER_FVG"]["implementation_candidate"]
        == "KEEP_SHARED_PATH_PROXY_SCORER_DEFAULT_OFF_NO_STANDALONE_FVG_ENTRY_CLAIM"
    )
    assert (
        snapshots["PENDING_LIMIT_LIFECYCLE"]["branch_decision"]
        == "KEEP_PENDING_LIFECYCLE_SCORER_WITH_NOT_APPLICABLE_TOUCH_REPAIR_AND_DECISION_SPREAD_FORWARD_CAPTURE"
    )
    assert (
        snapshots["PENDING_LIMIT_LIFECYCLE"]["implementation_candidate"]
        == "KEEP_SHADOW_ONLY_PENDING_LIFECYCLE_SCORER_WITH_DECISION_SPREAD_FORWARD_CAPTURE_AND_NOT_APPLICABLE_TOUCH_CLASSIFICATION"
    )
    assert "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER" in strategy_ids
    assert (
        snapshots["ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"]["branch_decision"]
        == "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_CONCENTRATION_GUARDED_CANDIDATE"
    )
    assert (
        snapshots["ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"]["implementation_candidate"]
        == "ENTRY_OFFSET_050R_CLUSTER_GUARDED_DEFAULT_OFF_CHALLENGER"
    )
    assert "MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN" in strategy_ids
    assert (
        snapshots["MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN"]["branch_decision"]
        == "IMPLEMENT_DEFAULT_OFF_FAR_MISS_RETEST_REDESIGN_VARIANT"
    )
    assert (
        snapshots["MOONSHOT_SOURCE_GUARD_SCOPE_CONTROL"]["implementation_candidate"]
        == "CAPTURE_AND_SCORE_DEFAULT_OFF_MOONSHOT_SOURCE_GUARD_SCOPE_CONTROL"
    )
    assert (
        snapshots["MOONSHOT_DEFAULT_OFF_SCORER_APPLICATION_CONTROL"]["source_capture_required_fields"]
        == (
            "moonshot_scorer_application_id",
            "moonshot_scorer_application_source_hash",
            "moonshot_scorer_exact_control_denominator",
        )
    )
    assert row["external_confluence"]["sierra"]["status"] == "FEATURES_EXTRACTED"
    assert row["pending_order_mode"] == "INTERNAL_CANDLE_POLLED_INTENT"
    assert row["broker_pending_order_created"] is False
    assert row["mt5_order_ticket"] is None
    assert row["native_pending_order_type"] is None


def test_strategy_follow_candidate_row_carries_m15_choch_diagnostic():
    row = build_strategy_follow_candidate_row(
        **_base_fields(),
        analysis_decision="CANDIDATE",
        framework="ob_retest",
        final_outcome="REJECTED_L2",
        verification={
            "passed": False,
            "blocked_by": "m15_choch_exists",
            "checks": [
                {
                    "name": "m15_choch_exists",
                    "status": "FAIL",
                    "detail": "No M15 CHoCH/BOS with displacement for bearish",
                    "mso_value": [],
                    "ai_value": True,
                },
                {
                    "name": "displacement_ratio",
                    "status": "SKIP",
                    "detail": "No qualifying M15 event found (depends on Check 1)",
                },
            ],
        },
    )

    diagnostic = row["m15_choch_diagnostic"]
    assert diagnostic["diagnostic_status"] == "M15_CHOCH_GATE_FAILED"
    assert diagnostic["blocked_by"] == "m15_choch_exists"
    assert diagnostic["m15_choch_mso_value"] == []
    assert diagnostic["displacement_ratio_check_status"] == "SKIP"


def _analysis() -> PrimaryAnalysisOutput:
    return PrimaryAnalysisOutput(
        timestamp_utc="2026-05-04T03:00:00+00:00",
        model_used="test",
        decision="CANDIDATE",
        confidence_score=80,
        framework="ob_retest",
        kill_zone="london",
        reasoning=PrimaryAnalysisReasoning(
            daily_bias=DailyBiasAnalysis(direction="bullish", confidence="high"),
            h4_alignment=H4AlignmentAnalysis(aligned=True),
            h1_setup=H1SetupAnalysis(
                poi_identified=True,
                poi_type="OB",
                poi_price_level=213.26,
                zone="discount",
            ),
            liquidity_sweep=LiquiditySweepAnalysis(detected=False),
            m15_confirmation=M15ConfirmationAnalysis(
                choch_detected=True,
                displacement_quality="strong",
                displacement_candle_body_vs_avg_ratio=1.8,
            ),
            setup_grade="A+",
        ),
        trade_parameters=TradeParameters(
            direction="LONG",
            entry_price=213.257,
            stop_loss=212.640,
            take_profit_1=214.183,
            risk_reward_ratio=1.5,
        ),
    )


def test_live_candidate_forward_shadow_writes_all_follow_logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    verification = SimpleNamespace(
        passed=False,
        blocked_by="h1_poi_exists",
        checks=[
            SimpleNamespace(
                name="h1_poi_exists",
                status="FAIL",
                detail="no matching H1 POI",
            )
        ],
    )

    record_live_candidate_forward_shadow(
        symbol="GBPJPY",
        broker_symbol="GBPJPY",
        source_symbol="GBPJPY",
        kill_zone="tokyo",
        analysis=_analysis(),
        mso={
            "timestamp_utc": "2026-05-04T03:00:00+00:00",
            "spread_cents": 1.2,
            "timeframes": {
                "H1": {
                    "structure": {
                        "direction": "bullish",
                        "protected_swing": {
                            "type": "low",
                            "price": 212.64,
                            "time": "2026-05-04T02:00:00+00:00",
                        },
                    },
                    "fair_value_gaps": [
                        {
                            "type": "bullish",
                            "top": 213.40,
                            "bottom": 213.10,
                            "midpoint": 213.25,
                            "formation_time": "2026-05-04T02:00:00+00:00",
                        }
                    ],
                    "swings": [],
                    "order_blocks": [
                        {
                            "type": "bullish",
                            "high": 213.40,
                            "low": 213.10,
                            "open": 213.18,
                            "close": 213.35,
                            "formation_index": 12,
                            "formation_time": "2026-05-04T02:00:00+00:00",
                            "causing_bos_index": 14,
                            "mitigated": False,
                            "causing_event_type": "BOS",
                            "touch_count": 1,
                        }
                    ],
                    "breaker_blocks": [],
                    "structure_events": [],
                },
                "M15": {
                    "structure": {"direction": "bullish"},
                    "fair_value_gaps": [],
                    "swings": [],
                    "order_blocks": [],
                    "breaker_blocks": [],
                    "structure_events": [],
                },
            },
        },
        record={
            "trade_id": "GBPJPY_20260504T0300",
            "metadata": {"candle_close_utc": "2026-05-04T03:00:00+00:00"},
            "instrumentation": {"detector_version_at_eval": "v2"},
        },
        verification=verification,
        final_outcome="REJECTED_L2",
    )

    expected = {
        "strategy_follow_candidates.jsonl": "strategy_follow_candidate_v1",
        "v2b_forward_pairs.jsonl": "v2b_forward_pair_v1",
        "prefill_delivery_path.jsonl": "prefill_delivery_path_v1",
        "fvg_ob_confluence.jsonl": "fvg_ob_confluence_forward_v1",
        "context_control_ledger.jsonl": "context_control_forward_v1",
        "nofill_forward_source_capture.jsonl": NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION,
    }
    for name, schema in expected.items():
        row = _read_one(tmp_path / "shadow_logs" / name)
        assert row["schema_version"] == schema
        assert row["candidate_id"] == "GBPJPY_20260504T0300"

    follow = _read_one(tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl")
    _assert_cp281_event_contract(follow)
    assert follow["final_outcome_at_log"] == "REJECTED_L2"
    assert follow["source_symbol"] == "GBPJPY"
    assert follow["market_timeframe"] == "M15"
    assert follow["route_session"] == "tokyo"
    assert follow["horizon_id"] == "live_candidate_decision"
    assert follow["source_component"] == "primary_analyzer_live_candidate"
    assert follow["selected_side"] == "LONG"
    assert follow["external_confluence"]["sierra"]["status"] == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"
    assert follow["external_confluence"]["databento"]["paid_fetch_attempted"] is False
    assert "live_shadow" in follow["external_confluence"]["databento"]
    structural_fields = follow["decision_time_structural_fields"]["fields"]
    assert structural_fields["standalone_fvg_entry_geometry"]["source_status"] == "DECISION_TIME_SOURCE_CAPTURED"
    assert structural_fields["swing_protected_lock_level"]["h1_protected_swing"]["price"] == 212.64
    assert 1.49 < structural_fields["cost_aware_min_r_fields"]["candidate_geometry"]["gross_tp1_r"] < 1.51
    assert follow["structural_selector_metadata"]["cost_aware_min_r_present"] is True

    nofill = _read_one(tmp_path / "shadow_logs" / "nofill_forward_source_capture.jsonl")
    _assert_cp281_event_contract(nofill)
    assert validate_nofill_forward_source_capture_row(nofill)["ok"] is True
    assert nofill["field_count"] == 55
    assert nofill["forbidden_field_scan_status"] == "NO_FORBIDDEN_RAW_FIELDS_PRESENT"

    fvg_ob = _read_one(tmp_path / "shadow_logs" / "fvg_ob_confluence.jsonl")
    _assert_cp281_event_contract(fvg_ob)
    assert fvg_ob["ob_bounds"]["source_status"] == "MATCHED_H1_ORDER_BLOCK_FROM_DECISION_MSO"
    assert fvg_ob["ob_bounds"]["low"] == 213.10
    assert fvg_ob["ob_bounds"]["high"] == 213.40
    assert fvg_ob["exact_geometry_source_status"] == "OB_EXACT_BOUNDS_MATCHED_FROM_DECISION_MSO"

    scid_rows = [
        json.loads(line)
        for line in (tmp_path / "shadow_logs" / "scid_forward_source_capture.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert scid_rows
    assert all(row["symbol_family"] == "GBPJPY" for row in scid_rows)
    assert all(row["source_path_sha256"] for row in scid_rows)
    assert all(row["source_file_sha256"] for row in scid_rows)


def test_live_candidate_forward_shadow_captures_fvg_bounds_from_decision_mso(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    analysis = _analysis()
    analysis.framework = "fvg_fill"
    analysis.reasoning.h1_setup.poi_type = "FVG"
    analysis.reasoning.h1_setup.poi_price_level = 213.25
    analysis.trade_parameters.entry_price = 213.25

    record_live_candidate_forward_shadow(
        symbol="GBPJPY",
        broker_symbol="GBPJPY",
        kill_zone="tokyo",
        analysis=analysis,
        mso={
            "timestamp_utc": "2026-05-04T03:00:00+00:00",
            "timeframes": {
                "H1": {
                    "structure": {"direction": "bullish"},
                    "fair_value_gaps": [],
                    "swings": [],
                    "order_blocks": [],
                    "breaker_blocks": [],
                    "structure_events": [],
                },
                "M15": {
                    "structure": {"direction": "bullish"},
                    "fair_value_gaps": [
                        {
                            "type": "bullish",
                            "top": 213.40,
                            "bottom": 213.10,
                            "midpoint": 213.25,
                            "formation_time": "2026-05-04T02:45:00+00:00",
                            "candle_indices": [9, 10, 11],
                            "filled": False,
                        }
                    ],
                    "swings": [],
                    "order_blocks": [],
                    "breaker_blocks": [],
                    "structure_events": [],
                },
            },
        },
        record={
            "trade_id": "GBPJPY_20260504T0300_FVG",
            "metadata": {"candle_close_utc": "2026-05-04T03:00:00+00:00"},
        },
        verification=SimpleNamespace(passed=True, blocked_by=None, checks=[]),
        final_outcome="LIMIT_PLACED",
    )

    row = _read_one(tmp_path / "shadow_logs" / "fvg_ob_confluence.jsonl")
    assert row["bucket"] == "fvg_only"
    assert row["fvg_bounds"]["source_status"] == "MATCHED_M15_FVG_FROM_DECISION_MSO"
    assert row["fvg_bounds"]["low"] == 213.10
    assert row["fvg_bounds"]["high"] == 213.40
    assert row["exact_geometry_source_status"] == "FVG_EXACT_BOUNDS_MATCHED_FROM_DECISION_MSO"


def test_live_candidate_forward_shadow_marks_limit_placed_as_internal_intent(
    tmp_path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)

    record_live_candidate_forward_shadow(
        symbol="NAS100",
        broker_symbol="NDX100",
        kill_zone="ny",
        analysis=_analysis(),
        mso=SimpleNamespace(timestamp_utc="2026-05-04T13:30:00+00:00"),
        record={
            "trade_id": "NAS100_20260504T1330",
            "metadata": {"candle_close_utc": "2026-05-04T13:30:00+00:00"},
            "limit_intent": {
                "trade_id": "lim_NAS100_2026-05-04_133000",
                "limit_price": 27736.8,
                "stop_loss": 27673.5,
                "take_profit_1": 27831.7,
                "pending_order_mode": "INTERNAL_CANDLE_POLLED_INTENT",
                "broker_pending_order_created": False,
                "mt5_order_ticket": None,
                "native_pending_order_type": None,
            },
        },
        final_outcome="LIMIT_PLACED",
        trade_id="lim_NAS100_2026-05-04_133000",
    )

    follow = _read_one(tmp_path / "shadow_logs" / "strategy_follow_candidates.jsonl")
    assert follow["final_outcome_at_log"] == "LIMIT_PLACED"
    assert follow["trade_id"] == "lim_NAS100_2026-05-04_133000"
    assert follow["pending_order_mode"] == "INTERNAL_CANDLE_POLLED_INTENT"
    assert follow["broker_pending_order_created"] is False
    assert follow["mt5_order_ticket"] is None
    assert follow["native_pending_order_type"] is None


def test_live_mso_forward_shadow_is_ai_independent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    record_live_mso_forward_shadow(
        symbol="GBPJPY",
        broker_symbol="GBPJPY",
        kill_zone="tokyo",
        mso=SimpleNamespace(
            timestamp_utc="2026-05-04T03:15:00+00:00",
            timeframes={},
        ),
        raw_data={"candle_close_utc": "2026-05-04T03:15:00+00:00"},
        evaluation_stage="MSO_COMPUTED_PRE_AI",
    )

    row = _read_one(tmp_path / "shadow_logs" / "strategy_follow_evaluations.jsonl")
    _assert_cp281_event_contract(row)
    assert row["schema_version"] == "strategy_follow_evaluation_v1"
    assert row["ai_dependency"] == "NO_AI_REQUIRED_FOR_ROW"
    assert row["ai_status"] == "NOT_CALLED_AT_ROW_TIME"
    assert row["strategy_snapshots"]
