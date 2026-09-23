from __future__ import annotations

import json
from pathlib import Path

from src.research_infra.execution_telemetry_verifier import build_verification


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_index_verifier_flags_stale_index_and_lifecycle_gaps(tmp_path):
    index = tmp_path / "index" / "_trade_index.json"
    trade_root = tmp_path / "trade_records"
    live_root = tmp_path / "live_evaluations"
    write_json(
        index,
        {
            "version": 2,
            "source": "test",
            "trades": [{"date": "2026-01-01", "source": "batch_session"}],
            "trade_count": 1,
        },
    )
    write_json(
        trade_root / "XAUUSD" / "reject.json",
        {
            "metadata": {"trade_id": "reject", "symbol": "XAUUSD", "date": "2026-01-02"},
            "decision_pipeline": {
                "ai_decision": "CANDIDATE",
                "final_outcome": "REJECTED_L2",
                "level2_verification": {"passed": False, "blocked_by": "h1_poi_exists"},
            },
            "execution": None,
        },
    )
    write_json(
        trade_root / "XAUUSD" / "limit.json",
        {
            "metadata": {"trade_id": "limit", "symbol": "XAUUSD", "date": "2026-01-03"},
            "decision_pipeline": {
                "ai_decision": "CANDIDATE",
                "final_outcome": "LIMIT_PLACED",
                "level2_verification": {"passed": True},
                "gate3_result": {"passed": True},
            },
            "execution": None,
        },
    )
    write_jsonl(
        live_root / "XAUUSD" / "2026-01-03.jsonl",
        [{"decision": "CANDIDATE", "candle_time": "2026-01-03T08:15:00+00:00"}],
    )

    payload = build_verification(index_path=index, trade_records_root=trade_root, live_evaluations_root=live_root)

    assert payload["o1_index_verifier"]["status"] == "STALE_REBUILD_OR_CONSUMER_MIGRATION_REQUIRED"
    assert payload["o1_index_verifier"]["stale_by_days"] == 2
    lifecycle = payload["o8_lifecycle_completeness_verifier"]
    assert lifecycle["state_counts"]["REJECTED_L2"] == 1
    assert lifecycle["state_counts"]["LIMIT_PLACED"] == 1
    assert lifecycle["complete_counts"]["REJECTED_L2"] == 1
    assert lifecycle["missing_field_counts"]["execution"] == 1
    assert lifecycle["missing_field_counts"]["pending_lifecycle"] == 1
    assert payload["live_evaluation_summary"]["row_count"] == 1


def test_index_verifier_accepts_current_index_when_dates_and_counts_match(tmp_path):
    index = tmp_path / "index" / "_trade_index.json"
    trade_root = tmp_path / "trade_records"
    live_root = tmp_path / "live_evaluations"
    write_json(
        index,
        {
            "version": 2,
            "source": "test",
            "trades": [{"date": "2026-01-03", "source": "trade_records"}],
            "trade_count": 1,
        },
    )
    write_json(
        trade_root / "XAUUSD" / "reject.json",
        {
            "metadata": {"trade_id": "reject", "symbol": "XAUUSD", "date": "2026-01-03"},
            "decision_pipeline": {
                "ai_decision": "CANDIDATE",
                "final_outcome": "REJECTED_L2",
                "level2_verification": {"passed": False, "blocked_by": "h1_poi_exists"},
            },
        },
    )

    payload = build_verification(index_path=index, trade_records_root=trade_root, live_evaluations_root=live_root)

    assert payload["o1_index_verifier"]["status"] == "CURRENT_WITHIN_LAG"
    assert payload["o8_lifecycle_completeness_verifier"]["status"] == "COMPLETE"
