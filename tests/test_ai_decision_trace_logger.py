from __future__ import annotations

import json
from types import SimpleNamespace

from src.components.ai_decision_trace_logger import (
    SCHEMA_VERSION,
    build_ai_decision_trace_row,
    record_ai_decision_trace,
)


def _result(decision: str = "NO_TRADE"):
    return SimpleNamespace(
        decision=decision,
        no_trade_reason="test_reason" if decision == "NO_TRADE" else None,
        framework="none",
        trade_parameters=None,
    )


def _config():
    return {
        "ai": {"primary_model": "claude-sonnet-4-6"},
        "ai_call_policy": {"max_research_ai_budget_usd": 5.0},
        "ai_supervisor": {"require_complete_trace_cache_identity": True},
        "budget": {"monthly_cap_usd": 50.0},
    }


def test_build_trace_row_is_hash_only():
    row = build_ai_decision_trace_row(
        system_prompt=[{"type": "text", "text": "secret system prompt"}],
        user_message="secret user message",
        raw_response='{"decision":"NO_TRADE"}',
        result=_result(),
        usage={
            "input_tokens": 10,
            "output_tokens": 5,
            "cache_read_tokens": 3,
            "cache_create_tokens": 2,
        },
        symbol="XAUUSD",
        candle_time="2026-05-18T00:00:00+00:00",
        kill_zone="london",
        model="claude-sonnet-4-6",
        backend_mode="api",
        response_status="parsed_first_attempt",
        parse_attempts=1,
        config=_config(),
    )

    encoded = json.dumps(row, sort_keys=True)
    assert row["schema_version"] == SCHEMA_VERSION
    assert row["decision"] == "NO_TRADE"
    assert row["raw_response_length"] == len('{"decision":"NO_TRADE"}')
    assert row["prompt_fingerprint"]["system_prompt_length"] > 0
    assert row["prompt_fingerprint"]["user_message_length"] == len("secret user message")
    assert row["usage"]["cache_read_tokens"] == 3
    cache_identity = row["content_addressed_cache_identity"]
    assert cache_identity["cache_key_status"] == "complete"
    assert cache_identity["content_addressed_cache_key"]
    assert row["ai_reliability_contract"]["schema_version"] == "ai_reliability_contract_v1"
    assert row["ai_reliability_contract"]["fallback_behavior_contract"][
        "fallback_active"
    ] is False
    assert row["research_boundary"]["stores_full_prompt_or_response_text"] is False
    assert "secret system prompt" not in encoded
    assert "secret user message" not in encoded
    assert '{"decision":"NO_TRADE"}' not in encoded


def test_record_trace_respects_enabled_config(tmp_path):
    log_path = tmp_path / "ai_decision_trace.jsonl"
    disabled = {"shadow_loggers": {"ai_decision_trace_logger": {"enabled": False, "path": str(log_path)}}}
    enabled = {
        **_config(),
        "shadow_loggers": {"ai_decision_trace_logger": {"enabled": True, "path": str(log_path)}},
    }

    assert record_ai_decision_trace(
        config=disabled,
        system_prompt="system",
        user_message="user",
        raw_response="response",
        result=_result(),
        usage={},
        symbol="GBPJPY",
        candle_time="2026-05-18T00:15:00+00:00",
        kill_zone="ny",
        model="claude-sonnet-4-6",
        backend_mode="api",
        response_status="parsed_first_attempt",
        parse_attempts=1,
    ) is None
    assert not log_path.exists()

    row = record_ai_decision_trace(
        config=enabled,
        system_prompt="system",
        user_message="user",
        raw_response="response",
        result=_result("CANDIDATE"),
        usage={},
        symbol="GBPJPY",
        candle_time="2026-05-18T00:15:00+00:00",
        kill_zone="ny",
        model="claude-sonnet-4-6",
        backend_mode="api",
        response_status="parsed_first_attempt",
        parse_attempts=1,
    )
    assert row is not None
    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["decision"] == "CANDIDATE"
    assert rows[0]["research_boundary"]["paid_api_or_vendor_call_added_by_logger"] is False
    assert rows[0]["content_addressed_cache_identity"]["cache_key_status"] == "complete"


def test_trace_row_records_deterministic_fallback_contract():
    row = build_ai_decision_trace_row(
        system_prompt="system",
        user_message="user",
        raw_response="not json",
        result=_result("NO_TRADE"),
        usage={},
        symbol="XAUUSD",
        candle_time="2026-05-18T00:00:00+00:00",
        kill_zone="london",
        model="claude-sonnet-4-6",
        backend_mode="api",
        response_status="malformed_demoted",
        parse_attempts=2,
        config=_config(),
    )

    fallback = row["ai_reliability_contract"]["fallback_behavior_contract"]
    baseline = row["ai_reliability_contract"]["deterministic_baseline_contract"]
    assert fallback["fallback_active"] is True
    assert fallback["fallback_action"] == "NO_TRADE"
    assert baseline["uses_paid_ai"] is False
    assert baseline["trade_permission"] is False
