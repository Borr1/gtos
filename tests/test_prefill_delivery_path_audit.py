from __future__ import annotations

from src.research_infra.prefill_delivery_path_audit import (
    ACTION_REQUIRED,
    build_prefill_delivery_path_audit_rows,
    build_rolling_status,
)


def _prefill(candidate_id: str = "c1", **overrides) -> dict:
    row = {
        "schema_version": "prefill_delivery_path_v1",
        "created_at_utc": "2026-05-04T07:15:05+00:00",
        "candidate_id": candidate_id,
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "source_symbol": None,
        "session": "london",
        "kill_zone": "london",
        "side": "LONG",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "trade_id": None,
        "source_hash": None,
        "structural_setup_id": candidate_id,
        "original_poi_bounds": {"poi_type": "OB", "poi_price_level": 100.0, "zone": "discount"},
        "entry_arming_time_utc": "2026-05-04T07:15:00+00:00",
        "pre_fill_candles": [],
        "pre_fill_ticks_summary": None,
        "delivery_leg_direction": "unresolved_live_forward",
        "reversal_leg_timing": None,
        "fill_happened": None,
        "fill_delay_seconds": None,
        "cancel_expiry_abort_reason": "REJECTED_L2",
        "lower_timeframe_path_ordering": "unresolved",
        "fvg_ob_swing_state_at_arm": {
            "framework": "ob_retest",
            "h1_poi_type": "OB",
            "m15_displacement_quality": "strong",
        },
        "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _resolution(candidate_id: str = "c1", **overrides) -> dict:
    row = {
        "schema_version": "prefill_delivery_path_resolution_v1",
        "row_key": f"resolution_{candidate_id}",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": candidate_id,
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "side": "LONG",
        "framework": "ob_retest",
        "resolution_status": "RESOLVED_FROM_LIVE_PATH_ROW",
        "path_label": "continued_without_entry_touch_to_tp_area",
        "path_outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
        "touched_entry": False,
        "hit_tp1": True,
        "hit_sl": False,
        "path_metrics": {"base_r_price": 2.0},
        "strategy_outcomes": {
            "PREFILL_DELIVERY_REVERSAL_PATH": {
                "strategy_status": "REGISTERED_NO_SCORER_IMPLEMENTED",
                "score_status": "NOT_COMPUTABLE",
                "outcome_status": "NOT_SCORED",
            },
            "PENDING_LIMIT_LIFECYCLE": {
                "strategy_status": "SCORED_SHARED_CANDIDATE_PATH",
                "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
                "outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
            },
        },
        "manual_backfill_status": "RECOVERED_DERIVED",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _path(candidate_id: str = "c1", **overrides) -> dict:
    row = {
        "schema_version": "candidate_path_follow_v1",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": candidate_id,
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "side": "LONG",
        "path_label": "continued_without_entry_touch_to_tp_area",
        "touched_entry": False,
        "hit_tp1": True,
        "hit_sl": False,
        "trade_parameters": {"direction": "LONG", "entry_price": 100, "stop_loss": 98, "take_profit_1": 103},
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _ltf(candidate_id: str = "c1", **overrides) -> dict:
    row = {
        "schema_version": "candidate_ltf_path_order_v1",
        "row_key": f"ltf_{candidate_id}",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": candidate_id,
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "side": "LONG",
        "ltf_status": "M1_PATH_RECOVERED",
        "entry_first_touch_utc": None,
        "tp1_first_touch_utc": "2026-05-04T07:30:00+00:00",
        "sl_first_touch_utc": None,
        "terminal_outcome_status": "NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH",
        "terminal_event_utc": "2026-05-04T07:30:00+00:00",
        "terminal_event_r": 0.0,
        "terminal_order_ambiguity": False,
        "path_order_label": "tp1_area_reached_without_entry_touch",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _opportunity(candidate_id: str = "c1") -> dict:
    return {
        "schema_version": "live_candidate_opportunity_cluster_v1",
        "row_key": f"opp_{candidate_id}",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": candidate_id,
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "opportunity_id": f"opp_{candidate_id}",
        "opportunity_counting_status": "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY",
        "opportunity_duplicate_status": "PRIMARY_UNIQUE_OPPORTUNITY",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def _structural(candidate_id: str = "c1") -> dict:
    return {
        "schema_version": "live_structural_strategy_metadata_v1",
        "row_key": f"struct_{candidate_id}",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": candidate_id,
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "missing_exact_required_fields": {
            "post_lock_reentry_state": "SOURCE_NOT_CAPTURED",
            "cost_aware_min_r_fields": "SOURCE_NOT_CAPTURED",
        },
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def test_prefill_audit_splits_captured_core_from_asof_derived_no_fill_path():
    rows = build_prefill_delivery_path_audit_rows(
        [(1, _prefill())],
        [(1, _resolution())],
        path_rows=[(1, _path())],
        ltf_rows=[(1, _ltf())],
        opportunity_rows=[(1, _opportunity())],
        structural_rows=[(1, _structural())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["prefill_source_capture_status"] == "PREFILL_DECISION_CORE_SOURCE_CAPTURED"
    assert row["fill_state"]["source_status"] == "DERIVED_FROM_LTF_PATH_ORDER_ASOF"
    assert row["fill_state"]["fill_happened_derived"] is False
    assert row["delivery_leg_state"]["delivery_leg_direction_derived"] == "MOVED_AWAY_FROM_ENTRY_TOWARD_TP_AREA_WITHOUT_FILL"
    assert row["reversal_leg_state"]["reversal_leg_state_derived"] == "NO_REVERSAL_LEG_NO_FILL"
    assert row["post_lock_reentry_eligibility"]["source_status"] == "SOURCE_NOT_CAPTURED"
    assert row["cost_aware_min_r"]["source_status"] == "SOURCE_NOT_CAPTURED"
    assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_prefill_audit_uses_fill_touch_time_for_delay_and_reversal_state():
    rows = build_prefill_delivery_path_audit_rows(
        [(1, _prefill())],
        [
            (
                1,
                _resolution(
                    path_label="entry_touched_then_reached_tp1",
                    path_outcome_status="ENTRY_TOUCHED_THEN_TP1",
                    touched_entry=True,
                    hit_tp1=True,
                ),
            )
        ],
        path_rows=[(1, _path(path_label="entry_touched_then_reached_tp1", touched_entry=True, hit_tp1=True))],
        ltf_rows=[
            (
                1,
                _ltf(
                    entry_first_touch_utc="2026-05-04T07:20:00+00:00",
                    terminal_outcome_status="ENTRY_THEN_TP1",
                    terminal_event_utc="2026-05-04T07:30:00+00:00",
                    terminal_event_r=1.5,
                    path_order_label="entry_then_tp1_before_sl",
                ),
            )
        ],
        opportunity_rows=[(1, _opportunity())],
        structural_rows=[(1, _structural())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["fill_state"]["fill_happened_derived"] is True
    assert row["fill_state"]["fill_delay_seconds_derived"] == 300
    assert row["reversal_leg_state"]["reversal_leg_state_derived"] == "FILLED_THEN_TP1"


def test_prefill_audit_preserves_waiting_path_without_fabricating_fields():
    rows = build_prefill_delivery_path_audit_rows(
        [(1, _prefill())],
        [],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["prefill_delivery_path_audit_status"] == "PREFILL_DELIVERY_PATH_WAITING_FOR_PATH"
    assert row["fill_state"]["source_status"] == "UNRESOLVED_PATH"
    assert "PREFILL_RESOLUTION_ROW_NOT_AVAILABLE_YET" in row["documented_limitation_codes"]


def test_prefill_audit_flags_decision_time_post_outcome_state():
    rows = build_prefill_delivery_path_audit_rows(
        [
            (
                1,
                _prefill(
                    fill_happened=False,
                    delivery_leg_direction="down_to_tp_after_decision",
                ),
            )
        ],
        [(1, _resolution())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert rows[0]["prefill_delivery_path_audit_status"] == ACTION_REQUIRED
    assert any(code.startswith("PREFILL_DECISION_ROW_POST_OUTCOME_STATE") for code in rows[0]["action_required_codes"])


def test_prefill_rolling_status_reports_v3_source_blockers():
    rows = build_prefill_delivery_path_audit_rows(
        [(1, _prefill("c1")), (2, _prefill("c2", decision_time_utc="2026-05-04T07:30:00+00:00"))],
        [(1, _resolution("c1")), (2, _resolution("c2"))],
        path_rows=[(1, _path("c1")), (2, _path("c2"))],
        ltf_rows=[(1, _ltf("c1")), (2, _ltf("c2"))],
        opportunity_rows=[(1, _opportunity("c1")), (2, _opportunity("c2"))],
        structural_rows=[(1, _structural("c1")), (2, _structural("c2"))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    status = build_rolling_status(rows)
    assert status["prefill_rows"] == 2
    assert status["core_source_captured_rows"] == 2
    assert status["duplicate_aware_countable_path_rows"] == 2
    assert status["post_lock_reentry_eligibility_status_counts"] == {"SOURCE_NOT_CAPTURED": 2}
    assert status["cost_aware_min_r_status_counts"] == {"SOURCE_NOT_CAPTURED": 2}
