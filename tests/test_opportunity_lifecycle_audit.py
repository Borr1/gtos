from __future__ import annotations

from src.research_infra.opportunity_lifecycle_audit import (
    ACTION_REQUIRED,
    COMPLETE_WITH_LIMITATIONS,
    build_opportunity_lifecycle_audit_rows,
)
from src.research_infra.live_opportunity_dedupe import build_opportunity_index


def _candidate(
    candidate_id: str,
    decision_time_utc: str,
    *,
    entry: float = 75.471,
    sl: float = 75.971,
    tp1: float = 74.721,
) -> dict:
    return {
        "candidate_id": candidate_id,
        "symbol": "XAGUSD",
        "broker_symbol": "XAGUSD",
        "session": "london",
        "side": "SHORT",
        "framework": "ob_retest",
        "decision_time_utc": decision_time_utc,
        "h1_setup": {"poi_type": "OB"},
        "trade_parameters": {
            "direction": "SHORT",
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit_1": tp1,
        },
    }


def _path(candidate: dict, *, asof: str = "2026-05-04T08:15:00+00:00") -> dict:
    return {
        "candidate_id": candidate["candidate_id"],
        "created_at_utc": asof,
        "decision_time_utc": candidate["decision_time_utc"],
        "asof_latest_candle_utc": asof,
        "symbol": candidate["symbol"],
        "broker_symbol": candidate["broker_symbol"],
        "side": candidate["side"],
        "framework": candidate["framework"],
        "path_label": "entry_touched_then_reached_tp1",
        "touched_entry": True,
        "hit_tp1": True,
        "hit_sl": False,
        "trade_parameters": candidate["trade_parameters"],
    }


def _ltf(candidate: dict, *, entry_touch: str, tp: str) -> dict:
    return {
        "candidate_id": candidate["candidate_id"],
        "created_at_utc": tp,
        "asof_latest_candle_utc": "2026-05-04T08:15:00+00:00",
        "entry_first_touch_utc": entry_touch,
        "tp1_first_touch_utc": tp,
        "sl_first_touch_utc": None,
        "terminal_outcome_status": "ENTRY_THEN_TP1",
        "terminal_event_utc": tp,
        "path_order_label": "entry_then_tp1_before_sl",
    }


def _blocked_ltf(candidate: dict, *, asof: str, created: str) -> dict:
    return {
        "candidate_id": candidate["candidate_id"],
        "created_at_utc": created,
        "backfilled_at_utc": created,
        "asof_latest_candle_utc": asof,
        "entry_first_touch_utc": None,
        "tp1_first_touch_utc": None,
        "sl_first_touch_utc": None,
        "terminal_outcome_status": "NO_ENTRY_TOUCH_BY_LTF_ASOF",
        "terminal_event_utc": None,
        "path_order_label": "ltf_source_blocked",
        "ltf_status": "SOURCE_BLOCKED",
        "manual_backfill_status": "SOURCE_BLOCKED",
        "mt5_read_error": "outside_max_hours",
    }


def _cluster_row(candidate: dict, computed: dict) -> dict:
    return {
        "candidate_id": candidate["candidate_id"],
        "created_at_utc": "2026-05-04T08:16:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:15:00+00:00",
        "opportunity_id": computed["opportunity_id"],
        "opportunity_first_candidate_id": computed["opportunity_first_candidate_id"],
        "opportunity_sequence_index": computed["opportunity_sequence_index"],
        "opportunity_candidate_count": computed["opportunity_candidate_count"],
        "opportunity_duplicate_status": computed["opportunity_duplicate_status"],
        "opportunity_reset_reason": computed["opportunity_reset_reason"],
        "opportunity_counting_status": computed["opportunity_counting_status"],
        "same_symbol_overlap_status": computed["same_symbol_overlap_status"],
    }


def test_opportunity_lifecycle_audit_matches_existing_cluster_with_legacy_limitations():
    first = _candidate("c1", "2026-05-04T07:15:00+00:00")
    duplicate = _candidate("c2", "2026-05-04T07:30:00+00:00")
    paths = {"c1": _path(first), "c2": _path(duplicate)}
    ltfs = {"c1": _ltf(first, entry_touch="2026-05-04T07:35:00+00:00", tp="2026-05-04T07:50:00+00:00")}
    computed = build_opportunity_index([first, duplicate], latest_paths=paths, latest_ltf=ltfs)

    rows = build_opportunity_lifecycle_audit_rows(
        [(1, first), (2, duplicate)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        path_rows=[(1, paths["c1"]), (2, paths["c2"])],
        ltf_rows=[(1, ltfs["c1"])],
        cluster_rows=[(1, _cluster_row(first, computed["c1"])), (2, _cluster_row(duplicate, computed["c2"]))],
    )

    duplicate_audit = next(row for row in rows if row["candidate_id"] == "c2")
    assert duplicate_audit["opportunity_lifecycle_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert duplicate_audit["action_required_codes"] == []
    assert duplicate_audit["opportunity_lifecycle_state"] == "DUPLICATE_ACTIVE_SETUP"
    assert duplicate_audit["cluster_comparison_status"] == "MATCHED_COMPUTED_OPPORTUNITY_INDEX"
    assert "LEGACY_CLUSTER_ROW_LIFECYCLE_STATE_NOT_CAPTURED" in duplicate_audit["documented_limitation_codes"]


def test_opportunity_lifecycle_audit_flags_cluster_mismatch():
    candidate = _candidate("c1", "2026-05-04T07:15:00+00:00")
    path = _path(candidate)
    computed = build_opportunity_index([candidate], latest_paths={"c1": path})
    cluster = _cluster_row(candidate, computed["c1"])
    cluster["opportunity_counting_status"] = "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE"

    rows = build_opportunity_lifecycle_audit_rows(
        [(1, candidate)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        path_rows=[(1, path)],
        cluster_rows=[(1, cluster)],
    )

    assert rows[0]["opportunity_lifecycle_audit_status"] == ACTION_REQUIRED
    assert "OPPORTUNITY_CLUSTER_MISMATCH" in rows[0]["action_required_codes"]
    assert rows[0]["cluster_comparison_mismatches"]["opportunity_counting_status"]["computed"] == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"


def test_opportunity_lifecycle_audit_accepts_ltf_recovered_path_without_candidate_path_follow():
    candidate = _candidate("c1", "2026-05-04T07:15:00+00:00")
    ltf = _ltf(
        candidate,
        entry_touch="2026-05-04T07:35:00+00:00",
        tp="2026-05-04T07:50:00+00:00",
    )
    computed = build_opportunity_index([candidate], latest_ltf={"c1": ltf})

    rows = build_opportunity_lifecycle_audit_rows(
        [(1, candidate)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        ltf_rows=[(1, ltf)],
        cluster_rows=[(1, _cluster_row(candidate, computed["c1"]))],
    )

    assert rows[0]["opportunity_lifecycle_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert "LATEST_CANDIDATE_PATH_ROW_MISSING" not in rows[0]["action_required_codes"]
    assert "CANDIDATE_PATH_ROW_MISSING_BUT_LTF_ORDER_RECOVERED" in rows[0]["documented_limitation_codes"]
    assert rows[0]["asof_latest_candle_utc"] == "2026-05-04T08:15:00+00:00"


def test_opportunity_lifecycle_prefers_recovered_ltf_over_later_blocked_placeholder():
    candidate = _candidate("c1", "2026-05-04T07:15:00+00:00")
    recovered = _ltf(
        candidate,
        entry_touch="2026-05-04T07:35:00+00:00",
        tp="2026-05-04T07:50:00+00:00",
    )
    blocked = _blocked_ltf(
        candidate,
        asof=recovered["asof_latest_candle_utc"],
        created="2026-05-04T08:20:00+00:00",
    )
    computed = build_opportunity_index([candidate], latest_ltf={"c1": recovered})

    rows = build_opportunity_lifecycle_audit_rows(
        [(1, candidate)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        ltf_rows=[(1, recovered), (2, blocked)],
        cluster_rows=[(1, _cluster_row(candidate, computed["c1"]))],
    )

    assert rows[0]["opportunity_lifecycle_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert rows[0]["action_required_codes"] == []
    assert rows[0]["candidate_terminal_event"]["terminal_event_status"] == "ENTRY_THEN_TP1_BEFORE_SL"


def test_opportunity_lifecycle_prefers_recovered_cluster_over_blocked_placeholder():
    candidate = _candidate("c1", "2026-05-04T07:15:00+00:00")
    path = _path(candidate)
    ltf = _ltf(
        candidate,
        entry_touch="2026-05-04T07:35:00+00:00",
        tp="2026-05-04T07:50:00+00:00",
    )
    computed = build_opportunity_index([candidate], latest_paths={"c1": path}, latest_ltf={"c1": ltf})
    recovered_cluster = _cluster_row(candidate, computed["c1"])
    recovered_cluster["manual_backfill_status"] = "RECOVERED_DERIVED"
    recovered_cluster["ltf_path_order_label"] = "entry_then_tp1_before_sl"
    blocked_cluster = {
        **recovered_cluster,
        "created_at_utc": "2026-05-04T08:20:00+00:00",
        "manual_backfill_status": "RECOVERED_DERIVED",
        "ltf_path_order_label": "ltf_source_blocked",
        "opportunity_counting_status": "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE",
        "same_symbol_overlap_status": "NO_ACTIVE_SYMBOL_OVERLAP",
    }

    rows = build_opportunity_lifecycle_audit_rows(
        [(1, candidate)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        path_rows=[(1, path)],
        ltf_rows=[(1, ltf)],
        cluster_rows=[(1, recovered_cluster), (2, blocked_cluster)],
    )

    assert rows[0]["opportunity_lifecycle_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert rows[0]["action_required_codes"] == []
    assert rows[0]["cluster_comparison_status"] == "MATCHED_COMPUTED_OPPORTUNITY_INDEX"


def test_opportunity_lifecycle_downgrades_lower_documented_count_to_limitation():
    first = _candidate("c1", "2026-05-04T07:15:00+00:00")
    duplicate = _candidate("c2", "2026-05-04T07:30:00+00:00")
    paths = {"c1": _path(first), "c2": _path(duplicate)}
    computed = build_opportunity_index([first, duplicate], latest_paths=paths)
    documented = _cluster_row(first, computed["c1"])
    documented["opportunity_candidate_count"] = 1

    rows = build_opportunity_lifecycle_audit_rows(
        [(1, first), (2, duplicate)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        path_rows=[(1, paths["c1"]), (2, paths["c2"])],
        cluster_rows=[(1, documented), (2, _cluster_row(duplicate, computed["c2"]))],
    )

    first_row = next(row for row in rows if row["candidate_id"] == "c1")
    assert first_row["opportunity_lifecycle_audit_status"] == COMPLETE_WITH_LIMITATIONS
    assert "OPPORTUNITY_CLUSTER_MISMATCH" not in first_row["action_required_codes"]
    assert "OPPORTUNITY_CANDIDATE_COUNT_POINT_IN_TIME_STALE" in first_row["documented_limitation_codes"]


def test_opportunity_lifecycle_row_key_changes_when_source_comparison_changes():
    candidate = _candidate("c1", "2026-05-04T07:15:00+00:00")
    path = _path(candidate)
    computed = build_opportunity_index([candidate], latest_paths={"c1": path})
    matched_cluster = _cluster_row(candidate, computed["c1"])
    mismatched_cluster = dict(matched_cluster)
    mismatched_cluster["opportunity_counting_status"] = "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE"

    matched = build_opportunity_lifecycle_audit_rows(
        [(1, candidate)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        path_rows=[(1, path)],
        cluster_rows=[(1, matched_cluster)],
    )[0]
    mismatched = build_opportunity_lifecycle_audit_rows(
        [(1, candidate)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        path_rows=[(1, path)],
        cluster_rows=[(1, mismatched_cluster)],
    )[0]

    assert matched["source_dependency_signature"] != mismatched["source_dependency_signature"]
    assert matched["row_key"] != mismatched["row_key"]


def test_opportunity_lifecycle_audit_flags_missing_cluster_row():
    candidate = _candidate("c1", "2026-05-04T07:15:00+00:00")
    path = _path(candidate)

    rows = build_opportunity_lifecycle_audit_rows(
        [(1, candidate)],
        generated_at_utc="2026-05-05T00:00:00+00:00",
        path_rows=[(1, path)],
    )

    assert rows[0]["opportunity_lifecycle_audit_status"] == ACTION_REQUIRED
    assert "LIVE_CLUSTER_ROW_MISSING" in rows[0]["action_required_codes"]
