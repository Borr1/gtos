from __future__ import annotations

from src.research_infra.decision_layer_diagnostics_join import (
    ACTION_REQUIRED,
    COMPLETE,
    PARTIAL,
    build_decision_layer_diagnostics_rows,
    build_rolling_status,
    select_nearest_diagnostic,
)


def _candidate(**overrides):
    row = {
        "schema_version": "strategy_follow_candidate_v1",
        "candidate_id": "NAS100_2026-05-04T17:00:00+00:00",
        "created_at_utc": "2026-05-04T17:00:26+00:00",
        "decision_time_utc": "2026-05-04T17:00:00+00:00",
        "symbol": "NAS100",
        "broker_symbol": "NDX100",
        "side": "LONG",
        "framework": "ob_retest",
        "session": "ny",
        "final_outcome_at_log": "REJECTED_GATE1_SAFETY",
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 27446.2,
            "stop_loss": 27387.1,
            "take_profit_1": 27534.8,
        },
        "h1_setup": {"poi_type": "OB"},
        "verification": {
            "passed": True,
            "blocked_by": None,
            "checks": [
                {"name": "m15_choch_exists", "status": "PASS", "detail": "ok"},
                {"name": "sl_beyond_ob", "status": "PASS", "detail": "ok"},
            ],
        },
    }
    row.update(overrides)
    return row


def _candidate_features(**overrides):
    row = {
        "timestamp_utc": "2026-05-04T17:00:05+00:00",
        "candle_close_utc": "2026-05-04T17:00:00+00:00",
        "symbol": "NAS100",
        "evaluation_id": "NAS100_2026-05-04T17_00_00_00_00",
        "decision": "CANDIDATE",
        "framework": "ob_retest",
        "setup_grade": "A+",
        "ai_decision": "CANDIDATE",
        "ai_direction_evaluated": "LONG",
        "daily_bias_direction": "bullish",
        "daily_bias_confidence": 80,
        "h4_aligned": True,
        "m15_choch_detected": True,
        "c_gate_result": {"c1_h1_bias_present": True},
        "pre_ai_gate_skipped": False,
        "pre_ai_gate_reason": None,
        "mso_h1_structure_direction": "bullish",
        "mso_m15_structure_direction": "bullish",
        "mso_d1_structure_direction": "bullish",
        "mso_h1_unmitigated_ob_count": 2,
        "mso_h1_ob_touch_counts": [1, 1],
        "mso_h1_atr_14": 89.5,
    }
    row.update(overrides)
    return row


def _d1(**overrides):
    row = {
        "timestamp": "2026-05-04T17:00:05+00:00",
        "symbol": "NAS100",
        "d1_bias": "bullish",
        "h4_bias": "bullish",
        "h1_direction": "bullish",
        "kill_zone": "ny",
        "h4_missing": False,
        "rolling_N_consecutive": 3,
    }
    row.update(overrides)
    return row


def _direction(**overrides):
    row = {
        "logged_at_utc": "2026-05-04T17:00:26+00:00",
        "candle_time_utc": "2026-05-04T17:00:05+00:00",
        "instrument": "NAS100",
        "proposed_direction": "LONG",
        "xau_d1_direction": "unavailable",
        "correlation_to_xau": 0.3572,
        "direction_aligned_with_xau": None,
        "kill_zone": "ny",
        "confidence_score": 72,
        "framework": "ob_retest",
    }
    row.update(overrides)
    return row


def _sl(**overrides):
    row = {
        "timestamp_utc": "2026-05-04T17:00:26+00:00",
        "candle_time": "2026-05-04T17:00:05+00:00",
        "symbol": "NAS100",
        "framework": "ob_retest",
        "l2_decision": "PASS",
        "l2_reason": "SL clears OB low",
        "direction": "LONG",
        "proposed_entry": 27446.2,
        "proposed_sl": 27387.1,
        "proposed_tp1": 27534.8,
        "ob_low": 27409.52,
        "ob_high": 27446.25,
        "zone_label": "OB",
        "h1_atr": 89.5,
        "confidence_score": 72,
    }
    row.update(overrides)
    return row


def _touch(**overrides):
    row = {
        "timestamp_utc": "2026-05-04T17:00:26+00:00",
        "symbol": "NDX100",
        "candle_time": "2026-05-04T17:00:05+00:00",
        "framework": "ob_retest",
        "gate_target_ob_touch": 1,
        "gate_threshold_at_eval": 2,
        "gate_decision": "PASS",
        "gate_target_ob_id": "NDX100_bullish_2026-05-01T11_00_00_00_00",
        "candidate_id": "NDX100_2026-05-04T17_00_05_000000_00_00",
        "ob_low": 27409.52,
        "ob_high": 27446.25,
        "ob_type": "bullish",
    }
    row.update(overrides)
    return row


def _cross_corr(**overrides):
    row = {
        "timestamp_utc": "2026-05-04T17:00:27+00:00",
        "candidate_symbol": "NAS100",
        "candidate_direction": "LONG",
        "evaluation_context": "orchestrator_sizing_risk_adjustment",
        "gate_action": "NONE",
        "risk_multiplier": 1.0,
        "cluster_size": 0,
        "correlated_positions": [],
        "threshold": 0.4,
        "min_positions": 2,
        "reason": "below_cluster_threshold",
    }
    row.update(overrides)
    return row


def test_select_nearest_diagnostic_normalizes_broker_alias():
    joined = select_nearest_diagnostic(
        symbol="NAS100",
        decision_time_utc="2026-05-04T17:00:00+00:00",
        rows=[(1, _touch())],
        time_fields=("candle_time",),
    )

    assert joined["join_status"] == "DIAGNOSTIC_NEAR_TIME_JOINED"
    assert joined["source_line"] == 1
    assert joined["offset_seconds"] == 5


def test_decision_layer_join_builds_complete_ml_feature_context():
    rows = build_decision_layer_diagnostics_rows(
        [(1, _candidate())],
        candidate_feature_rows=[(1, _candidate_features())],
        d1_bias_rows=[(1, _d1())],
        direction_emission_rows=[(1, _direction())],
        sl_beyond_ob_rows=[(1, _sl())],
        touch_count_rows=[(1, _touch())],
        cross_instrument_correlation_rows=[(1, _cross_corr())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["decision_diagnostics_status"] == COMPLETE
    assert row["touch_count_context"]["symbol"] == "NAS100"
    assert row["verification_context"]["l2_check_summary"]["sl_beyond_ob"] == "PASS"
    assert row["candidate_features_context"]["mso"]["h1_unmitigated_ob_count"] == 2
    assert row["cross_instrument_correlation_context"]["gate_action"] == "NONE"
    assert row["ml_feature_role"] == "ML_DECISION_LAYER_DIAGNOSTICS_AND_GATE_CONTEXT"
    assert row["action_required_codes"] == []


def test_missing_cross_instrument_correlation_context_is_optional():
    rows = build_decision_layer_diagnostics_rows(
        [(1, _candidate())],
        candidate_feature_rows=[(1, _candidate_features())],
        d1_bias_rows=[(1, _d1())],
        direction_emission_rows=[(1, _direction())],
        sl_beyond_ob_rows=[(1, _sl())],
        touch_count_rows=[(1, _touch())],
        cross_instrument_correlation_rows=[],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["decision_diagnostics_status"] == COMPLETE
    assert row["cross_instrument_correlation_join_status"] == "DIAGNOSTIC_JOIN_MISSING_WITHIN_TIME_WINDOW"
    assert (
        "CROSS_INSTRUMENT_CORRELATION_DIAGNOSTIC_OPTIONAL_MISSING_WITHIN_TIME_WINDOW"
        in row["documented_limitation_codes"]
    )
    assert row["action_required_codes"] == []


def test_candidate_feature_join_prefers_matching_framework_over_later_same_candle_no_trade():
    rows = build_decision_layer_diagnostics_rows(
        [(1, _candidate())],
        candidate_feature_rows=[
            (1, _candidate_features()),
            (
                2,
                _candidate_features(
                    timestamp_utc="2026-05-04T17:00:05+00:00",
                    decision="NO_TRADE",
                    framework="none",
                    setup_grade="C",
                    ai_decision="NO_TRADE",
                    ai_direction_evaluated=None,
                    ai_no_trade_reason="no_qualifying_h1_poi",
                ),
            ),
        ],
        d1_bias_rows=[(1, _d1())],
        direction_emission_rows=[(1, _direction())],
        sl_beyond_ob_rows=[(1, _sl())],
        touch_count_rows=[(1, _touch())],
        cross_instrument_correlation_rows=[(1, _cross_corr())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["decision_diagnostics_status"] == COMPLETE
    assert row["candidate_features_context"]["decision"] == "CANDIDATE"
    assert row["candidate_features_context"]["source_line"] == 1
    assert row["action_required_codes"] == []


def test_direction_mismatch_is_action_required():
    rows = build_decision_layer_diagnostics_rows(
        [(1, _candidate())],
        candidate_feature_rows=[(1, _candidate_features(ai_direction_evaluated="SHORT"))],
        direction_emission_rows=[(1, _direction(proposed_direction="LONG"))],
        sl_beyond_ob_rows=[(1, _sl())],
        touch_count_rows=[(1, _touch())],
        cross_instrument_correlation_rows=[(1, _cross_corr())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["decision_diagnostics_status"] == ACTION_REQUIRED
    assert "AI_DIRECTION_MISMATCH_SIDE" in row["action_required_codes"]
    assert "AI_DIRECTION_MISMATCH_SIDE" in row["mismatch_codes"]


def test_missing_optional_diagnostics_are_documented_not_action_required():
    rows = build_decision_layer_diagnostics_rows(
        [(1, _candidate(framework="breaker_re_entry", h1_setup={"poi_type": "breaker"}))],
        candidate_feature_rows=[(1, _candidate_features(framework="breaker_re_entry"))],
        d1_bias_rows=[],
        direction_emission_rows=[],
        sl_beyond_ob_rows=[],
        touch_count_rows=[],
        cross_instrument_correlation_rows=[],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["decision_diagnostics_status"] == PARTIAL
    assert row["action_required_codes"] == []
    assert "D1_BIAS_LAG_DIAGNOSTIC_MISSING_WITHIN_TIME_WINDOW" in row["documented_limitation_codes"]
    assert "TOUCH_COUNT_GATE_DIAGNOSTIC_MISSING_FOR_OB_RETEST" not in row["documented_limitation_codes"]


def test_row_key_stable_and_rolling_status_counts():
    kwargs = {
        "candidate_rows": [(1, _candidate())],
        "candidate_feature_rows": [(1, _candidate_features())],
        "d1_bias_rows": [(1, _d1())],
        "direction_emission_rows": [(1, _direction())],
        "sl_beyond_ob_rows": [(1, _sl())],
        "touch_count_rows": [(1, _touch())],
        "cross_instrument_correlation_rows": [(1, _cross_corr())],
    }
    rows_a = build_decision_layer_diagnostics_rows(**kwargs, generated_at_utc="2026-05-05T00:00:00+00:00")
    rows_b = build_decision_layer_diagnostics_rows(**kwargs, generated_at_utc="2026-05-05T01:00:00+00:00")

    assert [row["row_key"] for row in rows_a] == [row["row_key"] for row in rows_b]
    rolling = build_rolling_status(rows_a)
    assert rolling["status_counts"][COMPLETE] == 1
    assert rolling["diagnostic_join_counts"]["touch_count"]["DIAGNOSTIC_NEAR_TIME_JOINED"] == 1
    cross_corr_counts = rolling["diagnostic_join_counts"]["cross_instrument_correlation"]
    assert cross_corr_counts["DIAGNOSTIC_NEAR_TIME_JOINED"] == 1
    assert rolling["cross_instrument_correlation_joined_rows"] == 1
    assert rolling["daily_status_mix"]["2026-05-04"][COMPLETE] == 1
