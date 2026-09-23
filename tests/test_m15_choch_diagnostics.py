from __future__ import annotations

from src.research_infra.m15_choch_diagnostics import (
    PROMOTION_VERDICT,
    build_m15_choch_diagnostic_row,
    build_m15_choch_diagnostic_rows,
    m15_choch_decision_diagnostic,
)


def _candidate(**overrides):
    row = {
        "candidate_id": "XAGUSD_2026-05-05T19:45:00+00:00",
        "symbol": "XAGUSD",
        "broker_symbol": "XAGUSD",
        "decision_time_utc": "2026-05-05T19:45:00+00:00",
        "side": "SHORT",
        "framework": "ob_retest",
        "analysis_decision": "CANDIDATE",
        "final_outcome_at_log": "REJECTED_L2",
        "trade_parameters": {
            "direction": "SHORT",
            "entry_price": 75.471,
            "stop_loss": 75.928,
            "take_profit_1": 74.786,
        },
        "verification": {
            "passed": False,
            "blocked_by": "m15_choch_exists",
            "checks": [
                {
                    "name": "m15_choch_exists",
                    "status": "FAIL",
                    "detail": "No M15 CHoCH/BOS with displacement for bearish. Available events: none",
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
    }
    row.update(overrides)
    return row


def test_decision_diagnostic_explains_m15_failure():
    diagnostic = m15_choch_decision_diagnostic(_candidate()["verification"])

    assert diagnostic["diagnostic_status"] == "M15_CHOCH_GATE_FAILED"
    assert diagnostic["blocked_by"] == "m15_choch_exists"
    assert diagnostic["m15_choch_check_status"] == "FAIL"
    assert "No M15 CHoCH" in diagnostic["m15_choch_check_detail"]
    assert diagnostic["displacement_ratio_check_status"] == "SKIP"
    assert diagnostic["decision_time_only"] is True


def test_m15_audit_row_joins_later_continuation_path_and_opportunity():
    row = build_m15_choch_diagnostic_row(
        7,
        _candidate(),
        generated_at_utc="2026-05-06T00:00:00+00:00",
        path_row={
            "candidate_id": "XAGUSD_2026-05-05T19:45:00+00:00",
            "asof_latest_candle_utc": "2026-05-05T21:00:00+00:00",
            "path_label": "continued_without_entry_touch_to_tp_area",
            "touched_entry": False,
            "hit_tp1": True,
            "hit_sl": False,
            "tp1_first_touch_utc": "2026-05-05T20:15:00+00:00",
            "path_ambiguity_status": "NO_ENTRY_TOUCH_TP_AREA_NOT_A_FILL",
            "tick_order_claim_status": "NO_TICK_ORDER_CLAIM_M15_OHLC_ONLY",
        },
        opportunity_row={
            "candidate_id": "XAGUSD_2026-05-05T19:45:00+00:00",
            "opportunity_id": "opp-1",
            "opportunity_lifecycle_state": "ACTIVE_DUPLICATE_SETUP",
            "opportunity_counting_status": "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE",
            "opportunity_duplicate_status": "CONSECUTIVE_DUPLICATE_ACTIVE_SETUP",
            "opportunity_candidate_count": 4,
        },
    )

    assert row["schema_version"] == "m15_choch_diagnostic_audit_v1"
    assert row["promotion_verdict"] == PROMOTION_VERDICT
    assert row["post_decision_join_status"] == "JOINED_LATEST_CANDIDATE_PATH"
    assert row["later_path_outcome_status"] == "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH"
    assert row["gate_interpretation_status"] == "FAST_CONTINUATION_RESEARCH_DOOR_NOT_GATE_CHANGE"
    assert row["opportunity_join_status"] == "JOINED_LIVE_OPPORTUNITY_CLUSTER"
    assert row["opportunity_counting_status"] == "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE"
    assert row["no_execution"] is True
    assert row["order_calls"] == 0


def test_builder_filters_non_m15_failures_and_uses_latest_path():
    candidate_rows = [
        (1, _candidate(candidate_id="keep")),
        (
            2,
            _candidate(
                candidate_id="skip",
                verification={
                    "passed": False,
                    "blocked_by": "h1_poi_exists",
                    "checks": [{"name": "h1_poi_exists", "status": "FAIL", "detail": "no poi"}],
                },
            ),
        ),
    ]
    path_rows = [
        (1, {"candidate_id": "keep", "asof_latest_candle_utc": "2026-05-05T20:00:00+00:00", "path_label": "entry_touched_unresolved"}),
        (
            2,
            {
                "candidate_id": "keep",
                "asof_latest_candle_utc": "2026-05-05T21:00:00+00:00",
                "path_label": "entry_touched_then_reached_tp1",
                "touched_entry": True,
                "hit_tp1": True,
                "hit_sl": False,
            },
        ),
    ]

    rows = build_m15_choch_diagnostic_rows(
        candidate_rows,
        generated_at_utc="2026-05-06T00:00:00+00:00",
        path_rows=path_rows,
    )

    assert [row["candidate_id"] for row in rows] == ["keep"]
    assert rows[0]["later_path_outcome_status"] == "ENTRY_TOUCHED_THEN_TP1"
