from __future__ import annotations

from pathlib import Path

from src.research_infra.continuation_no_retrace import (
    PROMOTION_VERDICT,
    build_continuation_candidate_row,
    build_continuation_resolution_row,
    build_continuation_rows,
    decision_price_proxy_from_trade_record,
    eligibility,
)


def _candidate(**overrides):
    row = {
        "candidate_id": "XAGUSD_2026-05-05T07:30:00+00:00",
        "symbol": "XAGUSD",
        "broker_symbol": "XAGUSD",
        "session": "london",
        "kill_zone": "london",
        "decision_time_utc": "2026-05-05T07:30:00+00:00",
        "analysis_decision": "CANDIDATE",
        "final_outcome_at_log": "REJECTED_L2",
        "side": "SHORT",
        "framework": "ob_retest",
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
                {"name": "m15_choch_exists", "status": "FAIL", "detail": "No M15 CHoCH/BOS"},
                {"name": "displacement_ratio", "status": "SKIP", "detail": "No qualifying M15 event"},
                {"name": "h1_poi_exists", "status": "PASS", "detail": "H1 OB found"},
                {"name": "entry_in_ob", "status": "PASS", "detail": "Entry in OB"},
                {"name": "sl_beyond_ob", "status": "PASS", "detail": "SL clears OB"},
            ],
        },
    }
    row.update(overrides)
    return row


def test_eligibility_requires_m15_failure_and_valid_geometry():
    result = eligibility(_candidate())

    assert result["eligibility_status"] == "ELIGIBLE_SHADOW_ONLY"
    assert result["original_geometry"]["geometry_valid"] is True


def test_eligibility_rejects_non_m15_hard_failure():
    result = eligibility(
        _candidate(
            verification={
                "passed": False,
                "blocked_by": "m15_choch_exists",
                "checks": [
                    {"name": "m15_choch_exists", "status": "FAIL", "detail": "No M15 CHoCH/BOS"},
                    {"name": "h1_poi_exists", "status": "FAIL", "detail": "No H1 POI"},
                ],
            }
        )
    )

    assert result["eligibility_status"] == "NOT_ELIGIBLE"
    assert "NON_M15_L2_HARD_FAILURE:h1_poi_exists" in result["eligibility_reasons"]


def test_decision_price_proxy_from_trade_record_is_marked_non_promotion():
    proxy = decision_price_proxy_from_trade_record(
        {
            "_source_path": "knowledge_base/trade_records/XAGUSD/test.json",
            "shadow": {"proximity": {"current_price": 73.3215}},
            "shadow_data": {"spread_at_entry": 6.6},
        }
    )

    assert proxy["price"] == 73.3215
    assert proxy["price_source_status"] == "DECISION_PRICE_PROXY_AVAILABLE_NOT_EXECUTABLE_QUOTE"
    assert proxy["promotion_eligible_price_source"] is False


def test_candidate_row_records_preregistered_entry_stop_target_models():
    row = build_continuation_candidate_row(
        12,
        _candidate(),
        generated_at_utc="2026-05-06T00:00:00+00:00",
        trade_record={"shadow": {"proximity": {"current_price": 73.3215}}},
    )

    assert row is not None
    assert row["schema_version"] == "continuation_no_retrace_candidate_v1"
    assert row["strategy_id"] == "CONTINUATION_NO_RETRACE_M15_FAIL_V1"
    assert row["promotion_verdict"] == PROMOTION_VERDICT
    assert row["entry_models"][0]["entry_model_id"] == "CNR_E0_DECISION_CLOSE_MARKET"
    assert row["entry_models"][0]["entry_price"] is None
    assert row["entry_models"][1]["entry_price"] == 73.3215
    assert row["distance_from_original_limit"]["status"] == "COMPUTED_FROM_DECISION_PRICE_PROXY"
    assert row["no_execution"] is True


def test_resolution_row_keeps_path_context_separate_from_r_scoring():
    candidate_row = build_continuation_candidate_row(
        12,
        _candidate(),
        generated_at_utc="2026-05-06T00:00:00+00:00",
        trade_record={"shadow": {"proximity": {"current_price": 73.3215}}},
    )
    row = build_continuation_resolution_row(
        candidate_row,
        generated_at_utc="2026-05-06T00:00:00+00:00",
        path_row={
            "candidate_id": "XAGUSD_2026-05-05T07:30:00+00:00",
            "asof_latest_candle_utc": "2026-05-05T17:00:00+00:00",
            "path_label": "continued_without_entry_touch_to_tp_area",
            "touched_entry": False,
            "hit_tp1": True,
            "hit_sl": False,
        },
        opportunity_row={
            "candidate_id": "XAGUSD_2026-05-05T07:30:00+00:00",
            "opportunity_counting_status": "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE",
            "opportunity_duplicate_status": "CONSECUTIVE_DUPLICATE_ACTIVE_SETUP",
            "opportunity_lifecycle_state": "DUPLICATE_ACTIVE_SETUP",
        },
    )

    assert row["continuation_resolution_status"] == "FAST_CONTINUATION_PATH_CONTEXT"
    assert row["aggregate_counting_status"] == "EXCLUDED_DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE"
    assert row["synthetic_r_status"] == "NOT_COMPUTED_SOURCE_BLOCKED"
    assert row["synthetic_r"] is None
    assert "EXACT_DECISION_ENTRY_PRICE_NOT_CAPTURED" in row["source_blockers"]
    assert row["no_leak_status"] == "POST_DECISION_CONTINUATION_NO_RETRACE_AUDIT_NO_DECISION_FEATURE"


def test_build_rows_filters_by_date_and_joins_latest_sources(tmp_path: Path):
    record_dir = tmp_path / "records" / "XAGUSD"
    record_dir.mkdir(parents=True)
    (record_dir / "2026-05-05_london_0730.json").write_text(
        '{"shadow":{"proximity":{"current_price":73.3215}}}',
        encoding="utf-8",
    )
    candidate_rows = [
        (1, _candidate()),
        (2, _candidate(candidate_id="old", decision_time_utc="2026-05-04T07:30:00+00:00")),
    ]
    path_rows = [
        (
            1,
            {
                "candidate_id": "XAGUSD_2026-05-05T07:30:00+00:00",
                "asof_latest_candle_utc": "2026-05-05T17:00:00+00:00",
                "path_label": "continued_without_entry_touch_to_tp_area",
                "touched_entry": False,
                "hit_tp1": True,
                "hit_sl": False,
            },
        )
    ]
    opportunity_rows = [
        (
            1,
            {
                "candidate_id": "XAGUSD_2026-05-05T07:30:00+00:00",
                "opportunity_counting_status": "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY",
            },
        )
    ]

    candidates, resolutions, skipped = build_continuation_rows(
        candidate_rows,
        generated_at_utc="2026-05-06T00:00:00+00:00",
        trade_records_root=tmp_path / "records",
        path_rows=path_rows,
        opportunity_rows=opportunity_rows,
        decision_date_prefix="2026-05-05",
    )

    assert len(candidates) == 1
    assert len(resolutions) == 1
    assert skipped["outside_decision_date_prefix"] == 1
    assert candidates[0]["decision_price_proxy"]["price"] == 73.3215
    assert resolutions[0]["aggregate_counting_status"] == "COUNTABLE_PRIMARY_ONLY"
