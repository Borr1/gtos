from __future__ import annotations

from src.research_infra.v2b_forward_pair_resolution_audit import (
    ACTION_REQUIRED,
    build_rolling_status,
    build_v2b_forward_pair_audit_rows,
)


def _pair(candidate_id: str = "c1", **overrides) -> dict:
    row = {
        "schema_version": "v2b_forward_pair_v1",
        "created_at_utc": "2026-05-04T07:15:05+00:00",
        "candidate_id": candidate_id,
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "source_symbol": None,
        "session": "london",
        "kill_zone": "london",
        "side": "LONG",
        "framework": "ob_retest",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "trade_id": None,
        "source_hash": None,
        "ob_boundary_outcome": {"label_status": "unresolved_live_forward"},
        "j46_baseline_outcome": {"label_status": "unresolved_live_forward"},
        "fixed_r_comparator": {"label_status": "unresolved_live_forward"},
        "fvg_comparator": {"label_status": "unresolved_live_forward"},
        "path_label_status": "UNRESOLVED_REQUIRES_FORWARD_JOIN",
        "actual_synthetic_label_lane": "no_outcome_at_decision_time",
        "resolved_pair": True,
        "sample_floor_target_resolved_pairs": 30,
        "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }
    row.update(overrides)
    return row


def _resolution(candidate_id: str = "c1", *, status: str = "ENTRY_TOUCHED_THEN_TP1") -> dict:
    return {
        "schema_version": "v2b_forward_pair_resolution_v1",
        "row_key": f"resolution_{candidate_id}",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": candidate_id,
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "session": "london",
        "side": "LONG",
        "framework": "ob_retest",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "resolution_status": "RESOLVED_FROM_LIVE_PATH_ROW",
        "path_label": "entry_touched_then_reached_tp1",
        "path_outcome_status": status,
        "touched_entry": True,
        "hit_tp1": True,
        "hit_sl": False,
        "bars_elapsed": 3,
        "path_metrics": {"base_r_price": 2.0},
        "strategy_outcomes": {
            "V2B_OB_BOUNDARY_PROSPECTIVE": {
                "strategy_status": "SCORED_OB_BOUNDARY_PROXY_SHARED_CANDIDATE_PATH",
                "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
                "outcome_status": status,
            },
            "LIVE_AI_J46_J49_BASELINE_COMPARATOR": {
                "strategy_status": "SCORED_SHARED_CANDIDATE_PATH",
                "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
                "outcome_status": status,
            },
        },
        "manual_backfill_status": "RECOVERED_DERIVED",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def _mechanical(candidate_id: str, strategy_id: str, *, score: str = "COMPUTED_FROM_CANDIDATE_PATH", outcome: str = "ENTRY_TOUCHED_THEN_TP1", proxy_r=1.5) -> dict:
    return {
        "schema_version": "live_mechanical_strategy_shadow_outcome_v1",
        "created_at_utc": "2026-05-04T08:00:01+00:00",
        "candidate_id": candidate_id,
        "strategy_id": strategy_id,
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
        "strategy_status": "SCORED_OB_BOUNDARY_PROXY_SHARED_CANDIDATE_PATH" if "V2B" in strategy_id else "SCORED_SHARED_CANDIDATE_PATH",
        "score_status": score,
        "outcome_status": outcome,
        "outcome_source": "candidate_path_follow",
        "strategy_proxy_r": proxy_r,
        "manual_backfill_status": "BACKFILLED_OR_REFRESHED_FROM_LIVE_SHADOW_ROWS",
        "no_leak_status": "POST_DECISION_FORWARD_OBSERVATION_NOT_DECISION_FEATURE",
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
        "path_label": "entry_touched_then_reached_tp1",
        "touched_entry": True,
        "hit_tp1": True,
        "hit_sl": False,
        "trade_parameters": {"direction": "LONG", "entry_price": 100, "stop_loss": 98, "take_profit_1": 103},
        "no_leak_status": "POST_DECISION_FORWARD_OBSERVATION_NOT_DECISION_FEATURE",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def _account(candidate_id: str = "c1") -> dict:
    return {
        "schema_version": "account_truth_reconciliation_status_v1",
        "row_key": f"account_{candidate_id}",
        "created_at_utc": "2026-05-04T08:00:00+00:00",
        "candidate_id": candidate_id,
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "decision_time_utc": "2026-05-04T07:15:00+00:00",
        "account_truth_status": "NO_REALIZED_ACCOUNT_HISTORY_FOR_CANDIDATE_OR_NOT_QUERIED_IN_CLOSURE",
        "actual_r_claim_allowed": False,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def _opportunity(candidate_id: str = "c1", *, status: str = "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY") -> dict:
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
        "opportunity_counting_status": status,
        "opportunity_duplicate_status": "PRIMARY_UNIQUE_OPPORTUNITY",
        "opportunity_assignment_algorithm_version": "active_setup_lifecycle_tolerance_v1",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }


def test_v2b_audit_splits_synthetic_path_r_from_blocked_broker_actual_r():
    rows = build_v2b_forward_pair_audit_rows(
        [(1, _pair())],
        [(1, _resolution())],
        mechanical_rows=[
            (1, _mechanical("c1", "V2B_OB_BOUNDARY_PROSPECTIVE")),
            (2, _mechanical("c1", "LIVE_AI_J46_J49_BASELINE_COMPARATOR")),
        ],
        path_rows=[(1, _path())],
        account_truth_rows=[(1, _account())],
        opportunity_rows=[(1, _opportunity())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    row = rows[0]
    assert row["resolved_pair"] is True
    assert row["r_counted_pair"] is True
    assert row["actual_synthetic_label_lane"] == "SYNTHETIC_PATH_R"
    assert row["synthetic_path_r_pair_counted"] is True
    assert row["broker_actual_r_pair_counted"] is False
    assert row["ob_boundary_outcome"]["synthetic_path_r"] == 1.5
    assert row["ob_boundary_outcome"]["actual_r_lane_status"] == "ACCOUNT_TRUTH_SOURCE_BLOCKED_NO_BROKER_ACTUAL_R"
    assert row["decision_pair_no_leak_status"] == "NO_POST_OUTCOME_LABEL_IN_DECISION_PAIR"
    assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"


def test_v2b_audit_excludes_ambiguous_ltf_order_from_r():
    ambiguous = _mechanical(
        "c1",
        "V2B_OB_BOUNDARY_PROSPECTIVE",
        score="AMBIGUOUS_LTF_ORDER",
        outcome="ENTRY_THEN_SL_SAME_M1_AMBIGUOUS",
        proxy_r=None,
    )
    baseline = _mechanical(
        "c1",
        "LIVE_AI_J46_J49_BASELINE_COMPARATOR",
        score="AMBIGUOUS_LTF_ORDER",
        outcome="ENTRY_THEN_SL_SAME_M1_AMBIGUOUS",
        proxy_r=None,
    )
    rows = build_v2b_forward_pair_audit_rows(
        [(1, _pair())],
        [(1, _resolution(status="ENTRY_THEN_SL_SAME_M1_AMBIGUOUS"))],
        mechanical_rows=[(1, ambiguous), (2, baseline)],
        path_rows=[(1, _path())],
        account_truth_rows=[(1, _account())],
        opportunity_rows=[(1, _opportunity())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert rows[0]["r_counted_pair"] is False
    assert rows[0]["actual_synthetic_label_lane"] == "UNRESOLVED_PATH"
    assert rows[0]["ob_boundary_outcome"]["r_counting_status"] == "AMBIGUOUS_EXCLUDED_FROM_R"
    assert build_rolling_status(rows)["ambiguity_count"] == 1


def test_v2b_audit_flags_decision_time_post_outcome_label_leak():
    leaky_pair = _pair(
        actual_synthetic_label_lane="synthetic_path_r",
        ob_boundary_outcome={"label_status": "ENTRY_TOUCHED_THEN_TP1"},
    )
    rows = build_v2b_forward_pair_audit_rows(
        [(1, leaky_pair)],
        [(1, _resolution())],
        mechanical_rows=[
            (1, _mechanical("c1", "V2B_OB_BOUNDARY_PROSPECTIVE")),
            (2, _mechanical("c1", "LIVE_AI_J46_J49_BASELINE_COMPARATOR")),
        ],
        path_rows=[(1, _path())],
        account_truth_rows=[(1, _account())],
        opportunity_rows=[(1, _opportunity())],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    assert rows[0]["v2b_forward_pair_resolution_audit_status"] == ACTION_REQUIRED
    assert "DECISION_PAIR_POST_OUTCOME_LANE_NOT_PLACEHOLDER" in rows[0]["action_required_codes"]


def test_v2b_rolling_status_reports_duplicate_aware_sample_progress():
    rows = build_v2b_forward_pair_audit_rows(
        [
            (1, _pair("c1", symbol="XAUUSD", broker_symbol="XAUUSD")),
            (2, _pair("c2", symbol="NAS100", broker_symbol="NDX100", session="ny", kill_zone="ny", decision_time_utc="2026-05-04T13:15:00+00:00")),
        ],
        [(1, _resolution("c1")), (2, _resolution("c2"))],
        mechanical_rows=[
            (1, _mechanical("c1", "V2B_OB_BOUNDARY_PROSPECTIVE")),
            (2, _mechanical("c1", "LIVE_AI_J46_J49_BASELINE_COMPARATOR")),
            (3, _mechanical("c2", "V2B_OB_BOUNDARY_PROSPECTIVE")),
            (4, _mechanical("c2", "LIVE_AI_J46_J49_BASELINE_COMPARATOR")),
        ],
        path_rows=[(1, _path("c1")), (2, _path("c2"))],
        account_truth_rows=[(1, _account("c1")), (2, _account("c2"))],
        opportunity_rows=[
            (1, _opportunity("c1", status="COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY")),
            (2, _opportunity("c2", status="DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE")),
        ],
        generated_at_utc="2026-05-05T00:00:00+00:00",
    )

    status = build_rolling_status(rows)
    assert status["resolved_pair_count"] == 2
    assert status["r_counted_pair_count"] == 2
    assert status["duplicate_aware_countable_r_pair_count"] == 1
    assert status["symbol_counts"] == {"NAS100": 1, "XAUUSD": 1}
    assert status["label_lane_counts"] == {"SYNTHETIC_PATH_R": 2}
