from __future__ import annotations

import json

from src.research_infra.ai_decision_trace_backfill import (
    SCHEMA_VERSION,
    build_trade_record_ai_trace_backfill_row,
    build_trade_record_ai_trace_backfill_rows,
    iter_trade_record_paths,
    summarize_trade_record_ai_trace_backfill,
)


def _trade_record():
    return {
        "metadata": {
            "trade_id": "XAUUSD_2026-05-18_london_0700",
            "symbol": "XAUUSD",
            "candle_close_utc": "2026-05-18T07:00:00+00:00",
        },
        "prompt": {
            "system_prompt": "secret system prompt",
            "user_message": "secret user message",
        },
        "ai_response": {
            "model_used": "claude-sonnet-4-6",
            "decision": "CANDIDATE",
        },
        "decision_pipeline": {
            "ai_decision": "CANDIDATE",
            "ai_grade": "A+",
            "ai_confidence": 82,
            "ai_direction": "LONG",
            "ai_framework": "ob_retest",
            "final_outcome": "LIMIT_PLACED",
        },
    }


def test_trade_record_backfill_row_is_hash_only(tmp_path):
    path = tmp_path / "knowledge_base" / "trade_records" / "XAUUSD" / "sample.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(_trade_record()), encoding="utf-8")

    row = build_trade_record_ai_trace_backfill_row(
        path,
        _trade_record(),
        source_root=tmp_path,
        generated_at_utc="2026-05-18T00:00:00+00:00",
    )

    encoded = json.dumps(row, sort_keys=True)
    assert row["schema_version"] == SCHEMA_VERSION
    assert row["capture_status"] == "TRADE_RECORD_AI_TRACE_HASH_BACKFILL_COMPLETE"
    assert row["trade_id"] == "XAUUSD_2026-05-18_london_0700"
    assert row["prompt_fingerprint"]["system_prompt_length"] == len("secret system prompt")
    assert row["ai_response_sha256"]
    assert row["stores_full_prompt_or_response_text"] is False
    assert row["research_boundary"]["runtime_trace_stream_write"] is False
    assert "secret system prompt" not in encoded
    assert "secret user message" not in encoded


def test_trade_record_backfill_rows_and_summary(tmp_path):
    path = tmp_path / "records" / "XAUUSD" / "sample.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(_trade_record()), encoding="utf-8")

    rows = build_trade_record_ai_trace_backfill_rows(
        [path],
        source_root=tmp_path,
        generated_at_utc="2026-05-18T00:00:00+00:00",
    )
    summary = summarize_trade_record_ai_trace_backfill(rows)

    assert len(rows) == 1
    assert summary["rows"] == 1
    assert summary["complete_rows"] == 1
    assert summary["stores_full_prompt_or_response_text_rows"] == 0
    assert summary["runtime_trace_stream_write_rows"] == 0
    assert summary["paid_api_or_vendor_call_rows"] == 0


def test_iter_trade_record_paths_excludes_pending_index_files(tmp_path):
    record_path = tmp_path / "records" / "XAUUSD" / "sample.json"
    index_path = tmp_path / "records" / "XAUUSD" / "_pending_records_index.json"
    record_path.parent.mkdir(parents=True)
    record_path.write_text(json.dumps(_trade_record()), encoding="utf-8")
    index_path.write_text(json.dumps({"pending": []}), encoding="utf-8")

    assert iter_trade_record_paths(tmp_path / "records") == [record_path]
