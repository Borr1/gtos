from __future__ import annotations

import json
from pathlib import Path

from scripts.summarize_live_shadow_opportunities import build_summary


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_summary_counts_only_countable_opportunities_and_entry_model_r(tmp_path):
    shadow = tmp_path / "shadow_logs"
    _write_jsonl(
        shadow / "live_candidate_opportunity_clusters.jsonl",
        [
            {
                "candidate_id": "c1",
                "opportunity_id": "opp1",
                "opportunity_assignment_algorithm_version": "active_setup_lifecycle_tolerance_v1",
                "opportunity_counting_status": "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY",
                "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
                "created_at_utc": "2026-05-04T08:01:00+00:00",
            },
            {
                "candidate_id": "c2",
                "opportunity_id": "opp1",
                "opportunity_assignment_algorithm_version": "active_setup_lifecycle_tolerance_v1",
                "opportunity_counting_status": "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE",
                "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
                "created_at_utc": "2026-05-04T08:01:00+00:00",
            },
            {
                "candidate_id": "c3",
                "opportunity_id": "opp2",
                "opportunity_assignment_algorithm_version": "active_setup_lifecycle_tolerance_v1",
                "opportunity_counting_status": "BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP",
                "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
                "created_at_utc": "2026-05-04T08:01:00+00:00",
            },
        ],
    )
    _write_jsonl(
        shadow / "candidate_path_follow.jsonl",
        [
            {
                "candidate_id": "c1",
                "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
                "created_at_utc": "2026-05-04T08:01:00+00:00",
                "path_label": "entry_touched_then_reached_tp1",
            },
            {
                "candidate_id": "c2",
                "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
                "created_at_utc": "2026-05-04T08:01:00+00:00",
                "path_label": "entry_touched_then_reached_tp1",
            },
            {
                "candidate_id": "c3",
                "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
                "created_at_utc": "2026-05-04T08:01:00+00:00",
                "path_label": "entry_touched_then_reached_tp1",
            },
        ],
    )
    _write_jsonl(
        shadow / "live_mechanical_strategy_shadow_outcomes.jsonl",
        [
            {
                "candidate_id": "c1",
                "strategy_id": "LIVE_AI_J46_J49_BASELINE_COMPARATOR",
                "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
                "created_at_utc": "2026-05-04T08:01:00+00:00",
                "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
                "outcome_status": "ENTRY_TOUCHED_THEN_TP1",
            },
            {
                "candidate_id": "c1",
                "strategy_id": "J46_J49_PORTFOLIO_POLICY",
                "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
                "created_at_utc": "2026-05-04T08:01:00+00:00",
                "score_status": "NOT_AN_ENTRY_STRATEGY",
                "outcome_status": "ENTRY_TOUCHED_THEN_TP1",
            },
            {
                "candidate_id": "c1",
                "strategy_id": "PENDING_LIMIT_LIFECYCLE",
                "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
                "created_at_utc": "2026-05-04T08:02:00+00:00",
                "score_status": "COMPUTED_FROM_PENDING_LIFECYCLE",
                "outcome_status": "NO_FILL_CANCELLED_WRONG_SIDE",
                "strategy_proxy_r": 0.0,
            },
            {
                "candidate_id": "c1",
                "strategy_id": "AMBIGUOUS_MODEL",
                "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
                "created_at_utc": "2026-05-04T08:03:00+00:00",
                "score_status": "AMBIGUOUS_LTF_ORDER",
                "outcome_status": "ENTRY_THEN_SL_SAME_M1_AMBIGUOUS",
                "strategy_proxy_r": None,
            },
            {
                "candidate_id": "c1",
                "strategy_id": "LTF_RESOLVED_MODEL",
                "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
                "created_at_utc": "2026-05-04T08:04:00+00:00",
                "score_status": "COMPUTED_FROM_LTF_PATH_ORDER",
                "outcome_status": "ENTRY_TOUCHED_THEN_SL",
                "strategy_proxy_r": -1.0,
            },
            {
                "candidate_id": "c2",
                "strategy_id": "LIVE_AI_J46_J49_BASELINE_COMPARATOR",
                "asof_latest_candle_utc": "2026-05-04T08:00:00+00:00",
                "created_at_utc": "2026-05-04T08:01:00+00:00",
                "score_status": "COMPUTED_FROM_CANDIDATE_PATH",
                "outcome_status": "ENTRY_TOUCHED_THEN_TP1",
            },
        ],
    )

    summary = build_summary(tmp_path)
    strategies = summary["strategy_summary_countable_only"]

    assert summary["raw_candidate_count_with_latest_cluster"] == 3
    assert summary["countable_primary_opportunities"] == 1
    assert summary["not_countable_by_reason"] == {
        "BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP": 1,
        "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE": 1,
    }
    assert summary["opportunity_assignment_algorithm_versions"] == {"active_setup_lifecycle_tolerance_v1": 3}
    assert strategies["LIVE_AI_J46_J49_BASELINE_COMPARATOR"]["proxy_r"] == 1.5
    assert strategies["LIVE_AI_J46_J49_BASELINE_COMPARATOR"]["r_counted_rows"] == 1
    assert strategies["PENDING_LIMIT_LIFECYCLE"]["proxy_r"] == 0.0
    assert strategies["PENDING_LIMIT_LIFECYCLE"]["r_counted_rows"] == 1
    assert strategies["PENDING_LIMIT_LIFECYCLE"]["outcomes"] == {"NO_FILL_CANCELLED_WRONG_SIDE": 1}
    assert strategies["AMBIGUOUS_MODEL"]["r_counted_rows"] == 0
    assert strategies["LTF_RESOLVED_MODEL"]["proxy_r"] == -1.0
    assert strategies["LTF_RESOLVED_MODEL"]["r_counted_rows"] == 1
    assert strategies["J46_J49_PORTFOLIO_POLICY"]["proxy_r"] == 0.0
    assert strategies["J46_J49_PORTFOLIO_POLICY"]["r_counted_rows"] == 0
