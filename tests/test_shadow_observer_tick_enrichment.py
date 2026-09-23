from __future__ import annotations

import json
from pathlib import Path

from src.research_infra.shadow_observer_tick_enrichment import (
    build_enrichment_row,
    run,
    summarize_ticks,
)


def _observer_row() -> dict:
    return {
        "schema_version": "strategy_follow_evaluation_v1",
        "source_file": "shadow_observer_mso_no_ai",
        "candidate_id": "EURUSD_2026-05-04T07:45:00+00:00_shadow_observer",
        "decision_time_utc": "2026-05-04T07:45:00+00:00",
        "symbol": "EURUSD",
        "broker_symbol": "EURUSD",
        "source_symbol": "EURUSD/6E",
        "source_run_id": "shadow_observer_test",
        "observer_metadata": {"observer_id": "eurusd_6e_mso_shadow_v1"},
    }


def _ticks() -> list[dict]:
    return [
        {"time_msc": 1777880100000, "bid": 1.1000, "ask": 1.1001, "last": 0.0, "volume": 1.0, "flags": 2},
        {"time_msc": 1777880400000, "bid": 1.1002, "ask": 1.1003, "last": 0.0, "volume": 1.0, "flags": 2},
        {"time_msc": 1777880700000, "bid": 1.1001, "ask": 1.1002, "last": 0.0, "volume": 1.0, "flags": 2},
    ]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def test_summarize_ticks_extracts_basic_flow_features():
    summary = summarize_ticks(_ticks())

    assert summary["status"] == "FEATURES_EXTRACTED"
    assert summary["tick_count"] == 3
    assert summary["buy_count"] == 1
    assert summary["sell_count"] == 1


def test_build_enrichment_row_logs_safety_flags_and_no_paid_fetch():
    row = build_enrichment_row(
        _observer_row(),
        pull_ticks=lambda symbol, start, end: (_ticks(), None),
        created_at_utc="2026-05-04T08:00:00+00:00",
    )

    assert row is not None
    assert row["schema_version"] == "shadow_observer_tick_enrichment_v1"
    assert row["status"] == "FEATURES_EXTRACTED"
    assert row["no_ai_calls"] is True
    assert row["paid_fetch_attempted"] is False
    assert row["pre60_tick_summary"]["tick_count"] == 3


def test_run_dedupes_observer_enrichment_rows(tmp_path, monkeypatch):
    source = tmp_path / "evals.jsonl"
    output = tmp_path / "out.jsonl"
    _write_jsonl(source, [_observer_row()])
    monkeypatch.setattr(
        "src.research_infra.shadow_observer_tick_enrichment.build_enrichment_row",
        lambda row: {
            "schema_version": "shadow_observer_tick_enrichment_v1",
            "candidate_id": row["candidate_id"],
            "decision_time_utc": row["decision_time_utc"],
            "symbol": row["symbol"],
            "broker_symbol": row["broker_symbol"],
            "created_at_utc": "2026-05-04T08:00:00+00:00",
            "status": "NO_TICKS_OR_READ_ERROR",
            "pre60_tick_summary": {"status": "NO_TICKS_IN_WINDOW", "tick_count": 0},
            "event15_tick_summary": {"status": "NO_TICKS_IN_WINDOW", "tick_count": 0},
            "no_leak_status": "POST_DECISION_OBSERVER_ENRICHMENT_NOT_DECISION_FEATURE",
            "manual_backfill_status": "BACKFILLED_FROM_MT5_RECENT_TICKS_OR_EXPLICIT_BLOCKER",
            "no_ai_calls": True,
            "no_canary_required": True,
            "paid_fetch_attempted": False,
            "promotion_verdict": "NO_PROMOTION_VERDICT",
        },
    )

    first = run(source_path=source, output_path=output, symbol_filter={"EURUSD"})
    second = run(source_path=source, output_path=output, symbol_filter={"EURUSD"})

    assert first["rows_written"] == 1
    assert second["rows_written"] == 0
    assert second["skipped"]["duplicate_candidate_time"] == 1
