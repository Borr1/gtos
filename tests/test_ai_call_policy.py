import json
from types import SimpleNamespace

import yaml

from src.components.ai_call_policy import (
    attach_ai_call_policy_to_record,
    evaluate_ai_call_policy,
    record_ai_call_policy_decision,
)
from src.components.orchestrator import SessionOrchestrator


def _cfg(tmp_path):
    return {
        "market": {"symbol": "XAUUSD"},
        "ai": {"primary_model": "claude-sonnet-4-6"},
        "ai_call_policy": {
            "enabled": True,
            "apply_to_ai_call": True,
            "decision_log_enabled": True,
            "decision_log_path": str(tmp_path / "ai_call_policy.jsonl"),
            "max_research_ai_budget_usd": 5.0,
        },
    }


def test_ai_call_policy_allows_live_production_decision(tmp_path):
    decision = evaluate_ai_call_policy(
        config=_cfg(tmp_path),
        context={"purpose": "production_trade_decision", "runtime_context": "live_orchestrator"},
        symbol="XAUUSD",
        kill_zone="london",
        model="claude-sonnet-4-6",
    )

    assert decision.allowed is True
    assert decision.action == "ALLOW_AI"
    assert decision.reason == "ai_cost_control_production_decision_allowed"
    assert decision.evidence["source_artifact_path"] == (
        ".context/00_core/ai_in_loop_cost_control_research_plan.md"
    )


def test_ai_call_policy_blocks_historical_market_edge_replay(tmp_path):
    decision = evaluate_ai_call_policy(
        config=_cfg(tmp_path),
        context={
            "purpose": "market_edge_replay",
            "runtime_context": "historical_replay",
            "source_universe_kind": "mechanical_replay",
        },
        symbol="GBPJPY",
        kill_zone="tokyo",
        model="claude-sonnet-4-6",
    )

    assert decision.allowed is False
    assert decision.action == "SKIP_AI_NO_API_REPLAY"
    assert decision.reason == "ai_cost_control_no_api_market_replay"
    assert decision.evidence["is_no_api_context"] is True


def test_ai_call_policy_research_ai_requires_manifest_budget_owner_and_cache(tmp_path):
    base = {
        "purpose": "ai_delta_audit",
        "runtime_context": "historical_replay",
        "requires_paid_ai_for_research": True,
    }
    missing_manifest = evaluate_ai_call_policy(config=_cfg(tmp_path), context=base)
    assert missing_manifest.action == "SKIP_AI_MANIFEST_REQUIRED"

    missing_budget = evaluate_ai_call_policy(
        config=_cfg(tmp_path),
        context={**base, "sample_manifest_path": "samples.jsonl"},
    )
    assert missing_budget.action == "SKIP_AI_BUDGET_REQUIRED"

    missing_owner = evaluate_ai_call_policy(
        config=_cfg(tmp_path),
        context={**base, "sample_manifest_path": "samples.jsonl", "api_budget_usd": 1.25},
    )
    assert missing_owner.action == "SKIP_AI_OWNER_BUDGET_REQUIRED"

    over_cap = evaluate_ai_call_policy(
        config=_cfg(tmp_path),
        context={
            **base,
            "sample_manifest_path": "samples.jsonl",
            "api_budget_usd": 6.0,
        },
    )
    assert over_cap.action == "SKIP_AI_BUDGET_CAP_EXCEEDED"
    assert over_cap.evidence["budget_contract"]["research_budget_cap_usd"] == 5.0

    missing_cache = evaluate_ai_call_policy(
        config=_cfg(tmp_path),
        context={
            **base,
            "sample_manifest_path": "samples.jsonl",
            "api_budget_usd": 1.25,
            "owner_approved_budget": True,
        },
    )
    assert missing_cache.action == "SKIP_AI_CACHE_IDENTITY_REQUIRED"

    allowed = evaluate_ai_call_policy(
        config=_cfg(tmp_path),
        context={
            **base,
            "sample_manifest_path": "samples.jsonl",
            "api_budget_usd": 1.25,
            "owner_approved_budget": True,
            "model_hash": "m",
            "prompt_hash": "p",
            "input_hash": "i",
            "config_hash": "c",
            "source_data_hash": "s",
        },
    )
    assert allowed.allowed is True
    assert allowed.reason == "ai_cost_control_research_ai_sample_allowed"
    assert allowed.evidence["cache_identity_present"] is True
    assert allowed.evidence["budget_contract"]["budget_within_cap"] is True
    assert allowed.evidence["model_version_contract"]["schema_validation_required"] is True


def test_ai_call_policy_record_and_trade_attachment(tmp_path):
    cfg = _cfg(tmp_path)
    decision = evaluate_ai_call_policy(
        config=cfg,
        context={"purpose": "market_edge_replay", "runtime_context": "historical_replay"},
    )
    record_ai_call_policy_decision(
        decision=decision,
        config=cfg,
        phase="unit_test_pre_call",
    )
    rows = (tmp_path / "ai_call_policy.jsonl").read_text(encoding="utf-8").splitlines()
    logged = json.loads(rows[0])
    assert logged["phase"] == "unit_test_pre_call"
    assert logged["decision"]["action"] == "SKIP_AI_NO_API_REPLAY"

    record = {"decision_pipeline": {}, "instrumentation": {}}
    attach_ai_call_policy_to_record(record, decision)
    assert record["decision_pipeline"]["ai_call_policy"]["reason"] == (
        "ai_cost_control_no_api_market_replay"
    )
    assert record["instrumentation"]["ai_call_policy_allowed"] is False


def test_orchestrator_ai_call_policy_hook_runs_before_primary_analyzer(tmp_path):
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = _cfg(tmp_path)
    orch._symbol = "US30_cash"
    orch._mt5_symbol = "US30.cash"

    decision = orch._evaluate_ai_call_policy(
        raw_data={
            "candle_close_utc": "2026-05-18T13:45:00+00:00",
            "ai_call_context": {
                "purpose": "market_edge_replay",
                "runtime_context": "historical_replay",
            },
        },
        kill_zone="ny",
        bias_result={"bias": "bullish"},
        vnext_pre_ai=SimpleNamespace(action="ALLOW_AI", reason="matched_pre_ai_vnext_scope"),
    )

    assert decision.allowed is False
    assert decision.context["source_symbol"] == "US30.cash"
    rows = (tmp_path / "ai_call_policy.jsonl").read_text(encoding="utf-8").splitlines()
    logged = json.loads(rows[0])
    assert logged["phase"] == "orchestrator_pre_primary_analyzer"
    assert logged["decision"]["reason"] == "ai_cost_control_no_api_market_replay"


def test_agent_config_wires_ai_call_policy_runtime_guard():
    cfg = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
    policy = cfg["ai_call_policy"]

    assert policy["enabled"] is True
    assert policy["apply_to_ai_call"] is True
    assert policy["decision_log_path"] == "shadow_logs/ai_call_policy_decisions.jsonl"
    assert "production_trade_decision" in policy["production_purposes"]
    assert "ai_delta_audit" in policy["research_ai_purposes"]
    assert "historical_replay" in policy["no_api_contexts"]
    assert policy["require_manifest_for_research_ai"] is True
    assert policy["require_budget_cap_for_research_ai"] is True
    assert policy["max_research_ai_budget_usd"] == 5.0
    assert policy["require_owner_approval_for_research_ai"] is True
    assert policy["require_cache_key_for_research_ai"] is True
