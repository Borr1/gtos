from __future__ import annotations

import json
from datetime import datetime, timezone

from src.research_infra.databento_live_shadow import (
    BUDGET_LEDGER_SCHEMA_VERSION,
    SCHEMA_VERSION,
    append_live_row,
    build_budget_ledger_row,
    build_live_status_row,
    evaluate_live_trigger_policy,
    schema_feature_class,
)


def test_build_live_status_row_is_shadow_only():
    row = build_live_status_row(
        status="SUBSCRIBED",
        gtos_symbol="NAS100",
        raw_symbol="NQ.FUT",
        schema="trades",
    )

    assert row["schema_version"] == SCHEMA_VERSION
    assert row["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert row["evidence_class"] == "FUTURES_PROXY_TRANSFER"
    assert row["no_ai_calls"] is True
    assert row["no_canary_required"] is True
    assert row["no_execution"] is True
    assert row["order_calls"] == 0
    assert row["paid_fetch_attempted"] is False


def test_append_live_row_writes_jsonl(tmp_path):
    path = tmp_path / "databento_live.jsonl"
    append_live_row(build_live_status_row(status="DRY_RUN_OR_DISABLED"), path)

    row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert row["schema_version"] == SCHEMA_VERSION
    assert row["status"] == "DRY_RUN_OR_DISABLED"


def _enabled_env() -> dict[str, str]:
    return {
        "GTOS_DATABENTO_LIVE_SHADOW_ENABLED": "1",
        "DATABENTO_API_KEY": "test_key",
    }


def test_policy_requires_registered_symbol_schema_reason_and_env():
    row = evaluate_live_trigger_policy(
        symbols=["GBPJPY"],
        schemas=["mbo"],
        trigger_id=None,
        reason="short",
        estimated_cost_usd=None,
        timeout_seconds=None,
        max_records=None,
        env={},
        budget_rows=[],
    )

    assert row["decision"] == "DO_NOT_FETCH"
    assert "MISSING_TRIGGER_ID" in row["block_reasons"]
    assert "MISSING_REQUIRED_REASON" in row["block_reasons"]
    assert "SYMBOL_NOT_REGISTERED:GBPJPY" in row["block_reasons"]
    assert "MISSING_ESTIMATED_COST_USD" in row["block_reasons"]
    assert "DISABLED_BY_ENV" in row["block_reasons"]
    assert row["paid_fetch_attempted"] is False
    assert row["paid_data_calls"] == 0


def test_policy_allows_only_registered_nas100_trades_and_mbp10_when_enabled():
    row = evaluate_live_trigger_policy(
        symbols=["NAS100"],
        schemas=["trades", "mbp-10"],
        trigger_id="NAS100_20260505T1300_LTO010",
        reason="NAS100/NQ registered orderflow confluence around live candidate",
        estimated_cost_usd=0.10,
        timeout_seconds=60.0,
        max_records=5000,
        env=_enabled_env(),
        budget_rows=[],
        now_utc=datetime(2026, 5, 5, 13, 0, tzinfo=timezone.utc),
    )

    assert row["decision"] == "ALLOW_LIVE_FETCH"
    assert row["trigger_status"] == "TRIGGER_APPROVED_FOR_LIVE_FETCH"
    assert row["feature_classes"] == ["MBP_DEPTH", "TRADES_ONLY"]
    assert row["env_status"]["owner_approved"] is True


def test_policy_allows_direct_proxy_symbols_and_blocks_unregistered_proxy():
    allowed = evaluate_live_trigger_policy(
        symbols=["XAUUSD", "US30"],
        schemas=["trades", "mbp-10"],
        trigger_id="DIRECT_PROXY_LTO010",
        reason="direct futures proxy depth confluence around live candidate",
        estimated_cost_usd=0.50,
        timeout_seconds=120.0,
        max_records=10000,
        env=_enabled_env(),
        budget_rows=[],
        now_utc=datetime(2026, 5, 5, 13, 0, tzinfo=timezone.utc),
    )
    blocked = evaluate_live_trigger_policy(
        symbols=["GBPJPY"],
        schemas=["mbp-10"],
        trigger_id="GBPJPY_LTO010",
        reason="cross proxy needs separate registered source transfer policy",
        estimated_cost_usd=0.50,
        timeout_seconds=120.0,
        max_records=10000,
        env=_enabled_env(),
        budget_rows=[],
        now_utc=datetime(2026, 5, 5, 13, 0, tzinfo=timezone.utc),
    )

    assert allowed["decision"] == "ALLOW_LIVE_FETCH"
    assert "SYMBOL_NOT_REGISTERED:GBPJPY" in blocked["block_reasons"]


def test_policy_blocks_cost_cap_and_cooldown():
    first = evaluate_live_trigger_policy(
        symbols=["NAS100"],
        schemas=["trades"],
        trigger_id="NAS100_20260505T1300_LTO010",
        reason="NAS100/NQ registered orderflow confluence around live candidate",
        estimated_cost_usd=0.10,
        timeout_seconds=60.0,
        max_records=5000,
        env=_enabled_env(),
        budget_rows=[],
        now_utc=datetime(2026, 5, 5, 13, 0, tzinfo=timezone.utc),
    )
    budget_row = build_budget_ledger_row(budget_status="BUDGET_RESERVED", policy_decision=first)
    budget_row["created_at_utc"] = "2026-05-05T13:00:00+00:00"

    cooldown = evaluate_live_trigger_policy(
        symbols=["NAS100"],
        schemas=["trades"],
        trigger_id="NAS100_20260505T1301_LTO010",
        reason="NAS100/NQ registered orderflow confluence around live candidate",
        estimated_cost_usd=0.10,
        timeout_seconds=60.0,
        max_records=5000,
        env=_enabled_env(),
        budget_rows=[budget_row],
        now_utc=datetime(2026, 5, 5, 13, 0, 30, tzinfo=timezone.utc),
    )
    over_cap = evaluate_live_trigger_policy(
        symbols=["NAS100"],
        schemas=["trades"],
        trigger_id="NAS100_20260505T1330_LTO010",
        reason="NAS100/NQ registered orderflow confluence around live candidate",
        estimated_cost_usd=3.00,
        timeout_seconds=60.0,
        max_records=5000,
        env=_enabled_env(),
        budget_rows=[],
        now_utc=datetime(2026, 5, 5, 13, 30, tzinfo=timezone.utc),
    )

    assert "COOLDOWN_ACTIVE" in cooldown["block_reasons"]
    assert "TRIGGER_COST_CAP_EXCEEDED" in over_cap["block_reasons"]
    assert budget_row["schema_version"] == BUDGET_LEDGER_SCHEMA_VERSION
    assert budget_row["budget_day_utc"] == "2026-05-05"


def test_policy_separates_feature_classes():
    assert schema_feature_class("trades") == "TRADES_ONLY"
    assert schema_feature_class("mbp-10") == "MBP_DEPTH"
    assert schema_feature_class("mbo") == "MBO_ORDER_FLOW"
