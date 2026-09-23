from __future__ import annotations

from src.research_infra.fvg_ob_confluence_audit import (
    ACTION_REQUIRED,
    build_fvg_ob_confluence_audit_rows,
    build_rolling_status,
)


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


def _confluence(candidate_id: str = "c1", **overrides) -> dict:
    row = {
        "schema_version": "fvg_ob_confluence_forward_v1",
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
        "bucket": "ob_only",
        "touch_count": None,
        "poi_quality": "discount",
        "lower_timeframe_available": None,
        "candidate_outcome_lane": "UNRESOLVED_REQUIRES_FORWARD_JOIN",
        "decision_time_fields": {
            "analysis_decision": "CANDIDATE",
            "framework": "ob_retest",
            "entry_price": 100.0,
            "stop_loss": 98.0,
            "take_profit_1": 103.0,
            "h1_poi_type": "OB",
            "h1_poi_price_level": 100.25,
            "m15_displacement_quality": "strong",
        },
        "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _resolution(candidate_id: str = "c1") -> dict:
    return {
        "schema_version": "fvg_ob_confluence_resolution_v1",
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
        "path_metrics": {"base_r_price": 2.0},
        "strategy_outcomes": {
            "FVG_OB_CONFLUENCE_OB_AFTER_FVG": {
                "strategy_status": "NOT_COMPUTABLE_MISSING_FVG_ENTRY_OR_LOCK_METADATA",
                "score_status": "MISSING_REQUIRED_LIVE_METADATA",
                "outcome_status": "NOT_SCORED",
            },
            "V2_STRUCT_FVG_MID_EDGE": {
                "strategy_status": "NOT_COMPUTABLE_MISSING_FVG_ENTRY_OR_LOCK_METADATA",
                "score_status": "MISSING_REQUIRED_LIVE_METADATA",
                "outcome_status": "NOT_SCORED",
            },
        },
        "manual_backfill_status": "RECOVERED_DERIVED",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def _path(candidate_id: str = "c1") -> dict:
    return {
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
            "standalone_fvg_entry_geometry": "SOURCE_NOT_CAPTURED",
            "fvg_lock_state": "SOURCE_NOT_CAPTURED",
        },
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def _audit_rows(confluence: dict) -> list[dict]:
    return build_fvg_ob_confluence_audit_rows(
        [(1, confluence)],
        [(1, _resolution(confluence["candidate_id"]))],
        path_rows=[(1, _path(confluence["candidate_id"]))],
        opportunity_rows=[(1, _opportunity(confluence["candidate_id"]))],
        structural_rows=[(1, _structural(confluence["candidate_id"]))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )


def test_fvg_ob_audit_documents_ob_only_partial_bounds_without_scoring():
    row = _audit_rows(_confluence(bucket="ob_only"))[0]

    assert row["bucket_state"]["relation_state"] == "OB_ONLY"
    assert row["source_capture_statuses"]["ob_bounds"] == "PARTIAL_POI_POINT_CAPTURED_NOT_BOUNDS"
    assert row["source_capture_statuses"]["fvg_bounds"] == "SOURCE_NOT_CAPTURED"
    assert row["fvg_ob_confluence_outcome"]["scoreability_status"] == "NOT_SCORABLE_MISSING_FVG_ENTRY_OR_LOCK_METADATA"
    assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_fvg_ob_audit_accepts_exact_overlap_and_sequence_fields_when_present():
    row = _audit_rows(
        _confluence(
            bucket="both_fvg_and_ob_fire",
            fvg_bounds={"low": 99.5, "high": 100.5},
            ob_bounds={"low": 100.0, "high": 101.0},
            sequencing={"first": "FVG", "second": "OB"},
            composite_arbitration={"mode": "overlap"},
        )
    )[0]

    assert row["source_capture_statuses"]["fvg_bounds"] == "FVG_BOUNDS_CAPTURED"
    _assert_cp281_event_contract(row)
    assert row["source_capture_statuses"]["ob_bounds"] == "OB_BOUNDS_CAPTURED"
    assert row["geometry_state"]["overlap_computed"] is True
    assert row["source_capture_statuses"]["sequencing"] == "SEQUENCING_CAPTURED"
    assert row["fvg_ob_source_capture_status"] == "FVG_OB_EXACT_BOUNDS_CAPTURED"


def test_fvg_ob_audit_counts_bucket_specific_exact_bounds():
    rows = build_fvg_ob_confluence_audit_rows(
        [
            (1, _confluence("fvg", bucket="fvg_only", fvg_bounds={"low": 99.5, "high": 100.5})),
            (2, _confluence("ob", bucket="ob_only", ob_bounds={"low": 100.0, "high": 101.0})),
        ],
        [(1, _resolution("fvg")), (2, _resolution("ob"))],
        path_rows=[(1, _path("fvg")), (2, _path("ob"))],
        opportunity_rows=[(1, _opportunity("fvg")), (2, _opportunity("ob"))],
        structural_rows=[(1, _structural("fvg")), (2, _structural("ob"))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert rows[0]["fvg_ob_source_capture_status"] == "FVG_EXACT_BOUNDS_CAPTURED"
    assert rows[1]["fvg_ob_source_capture_status"] == "OB_EXACT_BOUNDS_CAPTURED"
    status = build_rolling_status(rows)
    assert status["exact_bounds_captured_rows"] == 2


def test_fvg_ob_audit_classifies_fvg_only_and_disagreement_buckets():
    rows = build_fvg_ob_confluence_audit_rows(
        [
            (1, _confluence("c1", bucket="fvg_only", decision_time_fields={"framework": "fvg_fill"})),
            (2, _confluence("c2", bucket="disagreement", decision_time_fields={"framework": "breaker_re_entry"})),
        ],
        [(1, _resolution("c1")), (2, _resolution("c2"))],
        path_rows=[(1, _path("c1")), (2, _path("c2"))],
        opportunity_rows=[(1, _opportunity("c1")), (2, _opportunity("c2"))],
        structural_rows=[(1, _structural("c1")), (2, _structural("c2"))],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    status = build_rolling_status(rows)
    assert status["bucket_counts"] == {"disagreement": 1, "fvg_only": 1}
    assert rows[0]["bucket_state"]["relation_state"] == "FVG_ONLY"
    assert rows[1]["source_capture_statuses"]["disagreement_reason"] == "DERIVED_FROM_BUCKET_AND_FRAMEWORK"


def test_fvg_ob_audit_preserves_waiting_path_without_fabricating_bounds():
    rows = build_fvg_ob_confluence_audit_rows(
        [(1, _confluence())],
        [],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert rows[0]["fvg_ob_confluence_audit_status"] == "FVG_OB_CONFLUENCE_WAITING_FOR_PATH"
    assert rows[0]["source_capture_statuses"]["fvg_bounds"] == "SOURCE_NOT_CAPTURED"
    assert "FVG_OB_RESOLUTION_ROW_NOT_AVAILABLE_YET" in rows[0]["documented_limitation_codes"]


def test_fvg_ob_audit_flags_decision_time_post_outcome_state():
    rows = build_fvg_ob_confluence_audit_rows(
        [(1, _confluence(candidate_outcome_lane="synthetic_path_r"))],
        [(1, _resolution())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert rows[0]["fvg_ob_confluence_audit_status"] == ACTION_REQUIRED
    assert any(code.startswith("FVG_OB_DECISION_ROW_POST_OUTCOME_STATE") for code in rows[0]["action_required_codes"])
