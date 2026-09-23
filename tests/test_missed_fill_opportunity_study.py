from __future__ import annotations

import json
from pathlib import Path

from src.research_infra.missed_fill_opportunity_study import build_study


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _candidate(candidate_id: str, *, final_outcome: str = "REJECTED_L2") -> dict:
    return {
        "candidate_id": candidate_id,
        "symbol": "GBPJPY",
        "broker_symbol": "GBPJPY",
        "session": "tokyo",
        "framework": "ob_retest",
        "side": "LONG",
        "decision_time_utc": "2026-05-12T01:15:00+00:00",
        "final_outcome_at_log": final_outcome,
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 100.0,
            "stop_loss": 90.0,
            "take_profit_1": 115.0,
        },
    }


def _cluster(candidate_id: str, status: str = "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY") -> dict:
    return {
        "candidate_id": candidate_id,
        "created_at_utc": "2026-05-12T02:00:00+00:00",
        "asof_latest_candle_utc": "2026-05-12T02:00:00+00:00",
        "opportunity_id": candidate_id,
        "opportunity_counting_status": status,
    }


def _path(candidate_id: str, *, label: str, min_low: float = 102.0) -> dict:
    return {
        "candidate_id": candidate_id,
        "created_at_utc": "2026-05-12T02:00:00+00:00",
        "asof_latest_candle_utc": "2026-05-12T02:00:00+00:00",
        "path_label": label,
        "touched_entry": label != "continued_without_entry_touch_to_tp_area",
        "hit_tp1": label != "went_through_entry_and_continued_to_sl",
        "hit_sl": label == "went_through_entry_and_continued_to_sl",
        "min_low": min_low,
        "max_high": 116.0,
    }


def _ltf(candidate_id: str, *, status: str) -> dict:
    return {
        "candidate_id": candidate_id,
        "created_at_utc": "2026-05-12T02:00:01+00:00",
        "asof_latest_candle_utc": "2026-05-12T02:00:00+00:00",
        "terminal_outcome_status": status,
        "terminal_event_utc": "2026-05-12T01:15:00+00:00",
        "tp1_first_touch_utc": "2026-05-12T01:15:00+00:00",
    }


def _blocked_ltf(candidate_id: str) -> dict:
    return {
        "candidate_id": candidate_id,
        "created_at_utc": "2026-05-12T02:05:00+00:00",
        "asof_latest_candle_utc": "2026-05-12T02:00:00+00:00",
        "manual_backfill_status": "SOURCE_BLOCKED",
        "ltf_status": "SOURCE_BLOCKED",
        "path_order_label": "ltf_source_blocked",
        "mt5_read_error": "outside_max_hours",
    }


def test_missed_fill_study_counts_countable_misses_and_shift_sensitivity(tmp_path):
    shadow = tmp_path / "shadow_logs"
    candidates = [
        _candidate("c1", final_outcome="LIMIT_PLACED"),
        _candidate("c2"),
        _candidate("c3"),
        _candidate("c4"),
    ]
    _write_jsonl(shadow / "strategy_follow_candidates.jsonl", candidates)
    _write_jsonl(
        shadow / "live_candidate_opportunity_clusters.jsonl",
        [
            _cluster("c1"),
            _cluster("c2", status="DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE"),
            _cluster("c3"),
            _cluster("c4"),
        ],
    )
    _write_jsonl(
        shadow / "candidate_path_follow.jsonl",
        [
            _path("c1", label="continued_without_entry_touch_to_tp_area", min_low=102.0),
            _path("c2", label="continued_without_entry_touch_to_tp_area", min_low=102.0),
            _path("c3", label="entry_touched_then_reached_tp1", min_low=99.0),
            _path("c4", label="continued_without_entry_touch_to_tp_area", min_low=112.0),
        ],
    )
    _write_jsonl(
        shadow / "candidate_ltf_path_order.jsonl",
        [
            _ltf("c1", status="NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH"),
            _ltf("c2", status="NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH"),
            _ltf("c3", status="ENTRY_THEN_TP1"),
            _ltf("c4", status="NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH"),
        ],
    )

    study = build_study(tmp_path)

    assert study["counts"]["raw_candidates_with_latest_cluster"] == 4
    assert study["counts"]["countable_primary_opportunities"] == 3
    assert study["counts"]["raw_missed_fill_to_tp_area"] == 3
    assert study["counts"]["countable_missed_fill_to_tp_area"] == 2
    assert study["counts"]["countable_missed_fill_rate"] == 0.666667
    assert study["counts"]["countable_missed_more_than_1r_inside_required"] == 1
    assert study["shifted_entry_range_touch_summary"]["0.25R_inside_limit"]["count"] == 1
    assert study["shifted_entry_range_touch_summary"]["1.00R_inside_limit"]["count"] == 1
    assert study["group_breakdowns"]["by_final_outcome"]["LIMIT_PLACED"]["countable_missed_fill_to_tp_area"] == 1
    assert study["follow_up_recommendation"] == "CONTINUE_MONITORING_UNTIL_PRIMARY_TRIGGER"
    assert study["trigger_policy"]["trigger_met"] is False
    assert study["no_execution"] is True


def test_missed_fill_study_prefers_recovered_evidence_over_later_blocked_rows(tmp_path):
    shadow = tmp_path / "shadow_logs"
    _write_jsonl(shadow / "strategy_follow_candidates.jsonl", [_candidate("c1", final_outcome="LIMIT_PLACED")])
    _write_jsonl(
        shadow / "live_candidate_opportunity_clusters.jsonl",
        [
            {**_cluster("c1"), "ltf_path_order_label": "tp1_area_reached_without_entry_touch"},
            {
                **_cluster("c1", status="DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE"),
                "created_at_utc": "2026-05-12T02:05:00+00:00",
                "ltf_path_order_label": "ltf_source_blocked",
                "manual_backfill_status": "RECOVERED_DERIVED",
            },
        ],
    )
    _write_jsonl(
        shadow / "candidate_path_follow.jsonl",
        [_path("c1", label="continued_without_entry_touch_to_tp_area", min_low=102.0)],
    )
    _write_jsonl(
        shadow / "candidate_ltf_path_order.jsonl",
        [
            {
                **_ltf("c1", status="NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH"),
                "path_order_label": "tp1_area_reached_without_entry_touch",
                "ltf_status": "M1_PATH_RECOVERED",
            },
            _blocked_ltf("c1"),
        ],
    )

    study = build_study(tmp_path)

    assert study["counts"]["countable_primary_opportunities"] == 1
    assert study["counts"]["countable_missed_fill_to_tp_area"] == 1
