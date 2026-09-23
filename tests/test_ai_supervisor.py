from __future__ import annotations

import json
from types import SimpleNamespace

import yaml

from src.components.ai_decision_trace_logger import build_ai_decision_trace_row
from src.components.ai_supervisor import (
    apply_ai_supervisor_runtime_overrides,
    evaluate_ai_supervisor,
    record_ai_supervisor_decision,
    repair_ai_response_format_preserving_semantics,
)
from src.components.orchestrator import SessionOrchestrator


def _cfg(tmp_path):
    return {
        "ai_supervisor": {
            "enabled": True,
            "apply_runtime_overrides": True,
            "decision_log_enabled": True,
            "decision_log_path": str(tmp_path / "ai_supervisor.jsonl"),
            "ai_decision_trace_path": str(tmp_path / "ai_decision_trace.jsonl"),
            "malformed_response_path": str(tmp_path / "malformed_responses.jsonl"),
            "vnext_decision_log_path": str(tmp_path / "gtos_vnext_runtime_decisions.jsonl"),
            "max_malformed_rows": 2,
            "max_malformed_demoted_rows": 1,
            "max_missing_source_bound_rows": 1,
            "max_candidate_cluster_rows": 2,
        },
        "gtos_vnext_runtime": {
            "pre_ai_apply_to_ai_call": True,
            "ai_policy_apply_to_ai_call": True,
        },
    }


def _trace_row(*, status="parsed_first_attempt", decision="NO_TRADE", symbol="XAUUSD"):
    result = SimpleNamespace(
        decision=decision,
        no_trade_reason="fixture" if decision == "NO_TRADE" else None,
        framework="none",
        trade_parameters=None,
        model_dump=lambda mode="json": {"decision": decision},
    )
    return build_ai_decision_trace_row(
        system_prompt="system",
        user_message="user",
        raw_response='{"decision":"NO_TRADE"}',
        result=result,
        usage={"input_tokens": 100, "output_tokens": 20},
        symbol=symbol,
        candle_time="2026-05-25T00:00:00Z",
        kill_zone="london",
        model="claude-sonnet-4-6",
        backend_mode="api",
        response_status=status,
        parse_attempts=2 if status == "parsed_retry" else 1,
        config={
            "ai": {"primary_model": "claude-sonnet-4-6"},
            "ai_call_policy": {"max_research_ai_budget_usd": 5.0},
            "ai_supervisor": {"require_complete_trace_cache_identity": True},
            "budget": {"monthly_cap_usd": 50.0},
        },
    )


def test_ai_supervisor_healthy_records_hash_and_cost_checks(tmp_path):
    decision = evaluate_ai_supervisor(
        config=_cfg(tmp_path),
        trace_rows=[_trace_row()],
        malformed_rows=[],
        vnext_rows=[],
    )

    assert decision.action == "HEALTHY"
    assert decision.disable_ai_narrowing is False
    assert decision.checks["ai_decision_trace"]["missing_prompt_hash_rows"] == 0
    assert decision.checks["ai_decision_trace"]["missing_cache_identity_rows"] == 0
    assert decision.checks["cost_monitoring"]["token_usage"]["input_tokens"] == 100


def test_ai_supervisor_disables_ai_narrowing_on_malformed_threshold(tmp_path):
    malformed_rows = [{"attempt": 1}, {"attempt": 2}]
    decision = evaluate_ai_supervisor(
        config=_cfg(tmp_path),
        trace_rows=[_trace_row(status="malformed_demoted")],
        malformed_rows=malformed_rows,
        vnext_rows=[],
    )
    effective = apply_ai_supervisor_runtime_overrides(_cfg(tmp_path), decision)

    assert decision.action == "DISABLE_AI_NARROWING"
    assert decision.disable_ai_narrowing is True
    assert effective["gtos_vnext_runtime"]["pre_ai_apply_to_ai_call"] is False
    assert effective["gtos_vnext_runtime"]["ai_policy_apply_to_ai_call"] is False


def test_ai_supervisor_detects_missing_source_bound_route_scope(tmp_path):
    vnext_rows = [
        {
            "phase": "ai_policy_pre_call",
            "decision": {
                "action": "CALL_AI_NARROWED_ROUTE",
                "would_action": "CALL_AI_NARROWED_ROUTE",
                "prompt_scope": {"source_bound": False},
            },
        }
    ]

    decision = evaluate_ai_supervisor(
        config=_cfg(tmp_path),
        trace_rows=[_trace_row()],
        malformed_rows=[],
        vnext_rows=vnext_rows,
    )

    assert decision.action == "DISABLE_AI_NARROWING"
    assert "missing_source_bound_prompt_scope" in decision.reason


def test_ai_supervisor_detects_missing_trace_cache_identity(tmp_path):
    legacy_row = _trace_row()
    legacy_row.pop("content_addressed_cache_identity")

    decision = evaluate_ai_supervisor(
        config=_cfg(tmp_path),
        trace_rows=[legacy_row],
        malformed_rows=[],
        vnext_rows=[],
    )

    assert decision.action == "DISABLE_AI_NARROWING"
    assert "missing_trace_cache_identity" in decision.reason


def test_ai_supervisor_repair_extracts_only_valid_json_object():
    raw = "Use this JSON:\n```json\n{\"decision\":\"NO_TRADE\"}\n```\nextra"
    repaired = repair_ai_response_format_preserving_semantics(raw)
    invalid = repair_ai_response_format_preserving_semantics("not json")

    assert repaired.repaired is True
    assert json.loads(repaired.repaired_text) == {"decision": "NO_TRADE"}
    assert repaired.reason == "json_object_extracted_without_field_mutation"
    assert invalid.repaired is False


def test_ai_supervisor_record_writes_decision_log(tmp_path):
    cfg = _cfg(tmp_path)
    decision = evaluate_ai_supervisor(
        config=cfg,
        trace_rows=[_trace_row()],
        malformed_rows=[],
        vnext_rows=[],
    )

    record_ai_supervisor_decision(
        decision=decision,
        config=cfg,
        phase="unit_test",
        symbol="XAUUSD",
        kill_zone="london",
    )

    rows = (tmp_path / "ai_supervisor.jsonl").read_text(encoding="utf-8").splitlines()
    logged = json.loads(rows[0])
    assert logged["schema_version"] == "ai_supervisor_decision_v1"
    assert logged["decision"]["action"] == "HEALTHY"


def test_orchestrator_ai_supervisor_hook_writes_effective_config(tmp_path):
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = _cfg(tmp_path)
    orch._symbol = "XAUUSD"
    raw_data = {}

    decision = orch._evaluate_ai_supervisor(raw_data=raw_data, kill_zone="london")

    assert decision.action == "HEALTHY"
    assert raw_data["ai_supervisor_decision"]["action"] == "HEALTHY"
    assert orch._config_after_ai_supervisor()["gtos_vnext_runtime"][
        "pre_ai_apply_to_ai_call"
    ] is True


def test_agent_config_wires_ai_supervisor():
    cfg = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
    supervisor = cfg["ai_supervisor"]

    assert supervisor["enabled"] is True
    assert supervisor["apply_runtime_overrides"] is True
    assert supervisor["decision_log_path"] == "shadow_logs/ai_supervisor_decisions.jsonl"
    assert supervisor["format_repair_enabled"] is True
    assert supervisor["require_complete_trace_cache_identity"] is True
    assert supervisor["max_missing_source_bound_rows"] == 1
