from __future__ import annotations

from src.research_infra.gate_filter_selector_evidence import (
    build_pre_ai_h1_poi_outcome_join_rows,
    build_sl_beyond_ob_outcome_join_rows,
    build_touch_count_gate_outcome_join_rows,
    normalize_candidate_id,
    summarize_pre_ai_h1_poi_outcome_join,
    summarize_sl_beyond_ob_outcome_join,
    summarize_touch_count_gate_outcome_join,
)


def _touch(**overrides):
    row = {
        "candidate_id": "XAGUSD_2026-05-04T10_00_05_012689_00_00",
        "symbol": "XAGUSD",
        "framework": "ob_retest",
        "gate_decision": "REJECT",
        "gate_target_ob_touch": 2,
        "gate_threshold_at_eval": 2,
        "gate_target_ob_id": "XAGUSD_bearish_2026-05-04T08_00_00_00_00",
        "ob_type": "bearish",
        "candle_time": "2026-05-04T10:00:05+00:00",
    }
    row.update(overrides)
    return row


def _outcome(**overrides):
    row = {
        "candidate_id": "XAGUSD_2026-05-04T10:00:00+00:00",
        "outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
        "path_label": "continued_without_entry_touch_to_tp_area",
        "candidate_final_outcome_at_log": "REJECTED_L2",
        "strategy_proxy_r": 0.0,
        "path_metrics": {
            "max_favorable_r_from_entry": 1.8,
            "max_adverse_r_from_entry": -1.2,
        },
    }
    row.update(overrides)
    return row


def _sl_beyond(**overrides):
    row = {
        "symbol": "NAS100",
        "framework": "ob_retest",
        "l2_decision": "PASS",
        "l2_reason": "ok",
        "direction": "LONG",
        "candle_time": "2026-05-04T07:15:05.489368+00:00",
        "proposed_entry": 18453.2,
        "proposed_sl": 18420.5,
        "proposed_tp1": 18502.3,
        "ob_low": 18400.0,
        "ob_high": 18450.0,
        "zone_label": "OB",
    }
    row.update(overrides)
    return row


def _pre_ai_feature(**overrides):
    row = {
        "evaluation_id": "GBPJPY_2026-05-04T07_30_05_000001_00_00",
        "symbol": "GBPJPY",
        "timestamp_utc": "2026-05-04T07:30:05+00:00",
        "candle_close_utc": "2026-05-04T07:30:00+00:00",
        "kill_zone": "london",
        "session_tag": "london",
        "pre_ai_gate_skipped": True,
        "pre_ai_gate_reason": "no_bullish_pois_for_ob_retest+fvg_fill+breaker_re_entry",
        "decision": None,
        "framework": "none",
        "setup_grade": None,
        "trade_parameters": None,
        "mso_h1_unmitigated_ob_count": 0,
        "mso_h1_ob_touch_counts": [],
        "mso_h1_fvg_count": 2,
        "mso_m15_fvg_count": 3,
        "mso_h1_structure_direction": "bullish",
        "mso_m15_structure_direction": "bullish",
        "mso_d1_structure_direction": "bullish",
    }
    row.update(overrides)
    return row


def test_normalize_legacy_candidate_id_preserves_symbol_and_m15_minute():
    assert normalize_candidate_id("XAGUSD_2026-05-04T10_15_05_144064_00_00") == (
        "XAGUSD_2026-05-04T10:15:00+00:00"
    )
    assert normalize_candidate_id("XAUUSD_2026-05-04T07:15:00+00:00") == "XAUUSD_2026-05-04T07:15:00+00:00"


def test_touch_count_reject_joined_no_fill_is_not_counted_as_missed_fillable_r():
    rows = build_touch_count_gate_outcome_join_rows(
        touch_count_rows=[(7, _touch())],
        outcome_rows=[(11, _outcome())],
        touch_source_path="touch.jsonl",
        touch_source_sha256="touch-sha",
        outcome_source_path="outcomes.jsonl",
        outcome_source_sha256="outcome-sha",
    )
    summary = summarize_touch_count_gate_outcome_join(rows)

    row = rows[0]
    assert row["join_status"] == "TOUCH_COUNT_GATE_OUTCOME_JOINED"
    assert row["outcome_source_line_no"] == 11
    assert row["touch_count_gate_outcome_action"] == "TOUCH_COUNT_REJECT_JOINED_NO_FILLABLE_MISSED_R_CURRENT_FORWARD"
    assert row["runtime_decision_effect"] is False
    assert row["gate_config_change_now"] is False
    assert summary["joined_reject_rows"] == 1
    assert summary["joined_reject_no_fillable_missed_r_rows"] == 1
    assert summary["joined_reject_positive_fillable_proxy_rows"] == 0


def test_touch_count_reject_joined_positive_fillable_proxy_requires_review():
    rows = build_touch_count_gate_outcome_join_rows(
        touch_count_rows=[_touch(candidate_id="XAUUSD_2026-05-04T08_00_05_000001_00_00", symbol="XAUUSD")],
        outcome_rows=[
            _outcome(
                candidate_id="XAUUSD_2026-05-04T08:00:00+00:00",
                outcome_status="ENTRY_TOUCHED_THEN_TP1",
                path_label="entry_touched_then_tp1",
                strategy_proxy_r=1.5,
            )
        ],
        touch_source_path="touch.jsonl",
        touch_source_sha256="touch-sha",
        outcome_source_path="outcomes.jsonl",
        outcome_source_sha256="outcome-sha",
    )

    assert rows[0]["touch_count_gate_outcome_action"] == (
        "TOUCH_COUNT_REJECT_JOINED_POSITIVE_FILLABLE_PROXY_REVIEW_REQUIRED"
    )
    assert rows[0]["replay_r_reference_counted_as_new_main_result"] is False


def test_touch_count_missing_outcome_keeps_source_capture_requirement():
    rows = build_touch_count_gate_outcome_join_rows(
        touch_count_rows=[_touch(candidate_id="GBPJPY_2026-05-13T01_00_05_008786_00_00", symbol="GBPJPY")],
        outcome_rows=[],
        touch_source_path="touch.jsonl",
        touch_source_sha256="touch-sha",
        outcome_source_path="outcomes.jsonl",
        outcome_source_sha256="outcome-sha",
    )

    assert rows[0]["join_status"] == "TOUCH_COUNT_GATE_OUTCOME_MISSING_BY_NORMALIZED_CANDIDATE_ID"
    assert rows[0]["touch_count_gate_outcome_action"] == (
        "TOUCH_COUNT_GATE_OUTCOME_JOIN_MISSING_SOURCE_CAPTURE_REQUIRED"
    )


def test_sl_beyond_ob_join_by_symbol_and_candle_minute_handles_aliases():
    rows = build_sl_beyond_ob_outcome_join_rows(
        sl_beyond_rows=[(5, _sl_beyond(symbol="NDX100"))],
        outcome_rows=[
            (
                9,
                _outcome(
                    candidate_id="NAS100_2026-05-04T07:15:00+00:00",
                    decision_time_utc="2026-05-04T07:15:00+00:00",
                    symbol="NAS100",
                ),
            )
        ],
        sl_beyond_source_path="sl.jsonl",
        sl_beyond_source_sha256="sl-sha",
        outcome_source_path="outcomes.jsonl",
        outcome_source_sha256="outcome-sha",
    )
    summary = summarize_sl_beyond_ob_outcome_join(rows)

    assert rows[0]["join_status"] == "SL_BEYOND_OB_OUTCOME_JOINED"
    assert rows[0]["canonical_symbol"] == "NAS100"
    assert rows[0]["outcome_source_line_no"] == 9
    assert rows[0]["sl_beyond_ob_outcome_action"] == "SL_BEYOND_OB_PASS_OUTCOME_REFERENCE_ONLY"
    assert summary["joined_rows"] == 1
    assert summary["runtime_decision_effect_rows"] == 0


def test_sl_beyond_ob_reject_without_outcome_keeps_capture_requirement():
    rows = build_sl_beyond_ob_outcome_join_rows(
        sl_beyond_rows=[_sl_beyond(l2_decision="REJECT", symbol="US30_cash")],
        outcome_rows=[],
        sl_beyond_source_path="sl.jsonl",
        sl_beyond_source_sha256="sl-sha",
        outcome_source_path="outcomes.jsonl",
        outcome_source_sha256="outcome-sha",
    )

    assert rows[0]["canonical_symbol"] == "US30"
    assert rows[0]["join_status"] == "SL_BEYOND_OB_OUTCOME_MISSING_BY_SYMBOL_MINUTE"
    assert rows[0]["sl_beyond_ob_outcome_action"] == "SL_BEYOND_OB_REJECT_OUTCOME_JOIN_MISSING_CAPTURE_REQUIRED"
    assert rows[0]["gate_config_change_now"] is False


def test_pre_ai_h1_poi_skip_without_outcome_records_capture_requirement_and_saved_call():
    rows = build_pre_ai_h1_poi_outcome_join_rows(
        candidate_feature_rows=[(3, _pre_ai_feature())],
        outcome_rows=[],
        candidate_features_source_path="candidate_features.jsonl",
        candidate_features_source_sha256="features-sha",
        outcome_source_path="outcomes.jsonl",
        outcome_source_sha256="outcomes-sha",
    )
    summary = summarize_pre_ai_h1_poi_outcome_join(rows)

    assert rows[0]["pre_ai_gate_decision"] == "SKIP_AI_CALL"
    assert rows[0]["join_status"] == "PRE_AI_H1_POI_OUTCOME_MISSING_BY_NORMALIZED_EVALUATION_ID"
    assert rows[0]["pre_ai_gate_skip_bias"] == "bullish"
    assert rows[0]["saved_ai_call_reference"] is True
    assert rows[0]["directional_poi_detail_capture_state"] == (
        "MISSING_FRAMEWORK_DIRECTIONAL_POI_COUNTS_FOR_SKIP_REVIEW"
    )
    assert rows[0]["pre_ai_h1_poi_outcome_action"] == (
        "PRE_AI_H1_POI_SKIP_NO_OUTCOME_JOIN_SOURCE_CAPTURE_REQUIRED"
    )
    assert summary["skip_rows"] == 1
    assert summary["missing_skip_rows"] == 1
    assert summary["saved_ai_call_reference_rows"] == 1
    assert summary["runtime_decision_effect_rows"] == 0


def test_pre_ai_h1_poi_skip_joined_positive_fillable_proxy_requires_review():
    rows = build_pre_ai_h1_poi_outcome_join_rows(
        candidate_feature_rows=[
            _pre_ai_feature(symbol="XAUUSD", evaluation_id="XAUUSD_2026-05-04T08_15_05_1_00_00")
        ],
        outcome_rows=[
            _outcome(
                candidate_id="XAUUSD_2026-05-04T08:15:00+00:00",
                outcome_status="ENTRY_TOUCHED_THEN_TP1",
                path_label="entry_touched_then_tp1",
                strategy_proxy_r=1.0,
                strategy_id="LIVE_AI_J46_J49_BASELINE_COMPARATOR",
            )
        ],
        candidate_features_source_path="candidate_features.jsonl",
        candidate_features_source_sha256="features-sha",
        outcome_source_path="outcomes.jsonl",
        outcome_source_sha256="outcomes-sha",
    )

    assert rows[0]["join_status"] == "PRE_AI_H1_POI_OUTCOME_JOINED"
    assert rows[0]["pre_ai_h1_poi_outcome_action"] == (
        "PRE_AI_H1_POI_SKIP_JOINED_POSITIVE_FILLABLE_PROXY_REVIEW_REQUIRED"
    )
    assert rows[0]["replay_r_reference_counted_as_new_main_result"] is False


def test_pre_ai_h1_poi_pass_rows_use_baseline_outcome_reference_when_available():
    rows = build_pre_ai_h1_poi_outcome_join_rows(
        candidate_feature_rows=[
            _pre_ai_feature(
                pre_ai_gate_skipped=False,
                pre_ai_gate_reason=None,
                decision="CANDIDATE",
                framework="ob_retest",
                trade_parameters={"direction": "LONG"},
            )
        ],
        outcome_rows=[
            _outcome(
                candidate_id="GBPJPY_2026-05-04T07:30:00+00:00",
                outcome_status="NOT_SCORED",
                strategy_id="V2_STRUCT_SWING_PROTECTED",
            ),
            _outcome(
                candidate_id="GBPJPY_2026-05-04T07:30:00+00:00",
                outcome_status="ENTRY_TOUCHED_THEN_TP1",
                strategy_id="LIVE_AI_J46_J49_BASELINE_COMPARATOR",
                strategy_proxy_r=1.5,
            ),
        ],
        candidate_features_source_path="candidate_features.jsonl",
        candidate_features_source_sha256="features-sha",
        outcome_source_path="outcomes.jsonl",
        outcome_source_sha256="outcome-sha",
    )

    assert rows[0]["pre_ai_gate_decision"] == "PASS_TO_AI_OR_DOWNSTREAM"
    assert rows[0]["outcome_strategy_id"] == "LIVE_AI_J46_J49_BASELINE_COMPARATOR"
    assert rows[0]["pre_ai_h1_poi_outcome_action"] == "PRE_AI_H1_POI_PASS_OUTCOME_REFERENCE_ONLY"
    assert rows[0]["saved_ai_call_reference"] is False
