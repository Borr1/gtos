"""Runtime policy for when GTOS is allowed to spend an AI call.

This is the code conversion of the AI-in-the-loop cost-control doctrine:
historical market-edge work should run no-API by default, while paid AI calls
are reserved for production decisions, canaries, and explicitly budgeted AI
decision/reliability samples.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.components.ai_reliability_contract import (
    AI_RELIABILITY_CONTRACT_SCHEMA_VERSION,
    build_budget_contract,
    build_deterministic_baseline_contract,
    build_disagreement_calibration_contract,
    build_model_version_contract,
    build_semantic_ownership_handoff,
)


DEFAULT_AI_CALL_POLICY_LOG_PATH = Path("shadow_logs/ai_call_policy_decisions.jsonl")


@dataclass(frozen=True)
class AICallPolicyDecision:
    """Decision returned before a PrimaryAnalyzer call is allowed to execute."""

    action: str
    allowed: bool
    enabled: bool
    apply_to_ai_call: bool
    reason: str
    context: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "allowed": self.allowed,
            "enabled": self.enabled,
            "apply_to_ai_call": self.apply_to_ai_call,
            "reason": self.reason,
            "context": self.context,
            "evidence": self.evidence,
        }


def _policy_cfg(config: dict[str, Any] | None) -> dict[str, Any]:
    return ((config or {}).get("ai_call_policy") or {})


def _configured_list(cfg: dict[str, Any], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = cfg.get(key)
    if raw is None:
        return default
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, (list, tuple, set)):
        items = tuple(str(item) for item in raw if str(item))
        return items or default
    return default


def _normalized(value: Any) -> str:
    return str(value or "").strip()


def _normalized_case(value: Any) -> str:
    return _normalized(value).casefold()


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "y", "on", "approved"}
    return bool(value)


def _positive_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _has_manifest(context: dict[str, Any]) -> bool:
    return any(
        _normalized(context.get(key))
        for key in (
            "api_call_manifest_path",
            "pre_call_manifest_path",
            "sample_manifest_path",
            "manifest_path",
            "manifest_id",
        )
    )


def _budget_usd(context: dict[str, Any]) -> float | None:
    for key in (
        "api_budget_usd",
        "max_api_budget_usd",
        "budget_usd",
        "owner_approved_budget_usd",
    ):
        parsed = _positive_float(context.get(key))
        if parsed is not None:
            return parsed
    return None


def _has_cache_identity(context: dict[str, Any]) -> bool:
    if any(
        _normalized(context.get(key))
        for key in (
            "content_addressed_cache_key",
            "prompt_input_cache_key",
            "cache_key",
            "response_cache_key",
        )
    ):
        return True
    required_hashes = ("model_hash", "prompt_hash", "input_hash", "config_hash", "source_data_hash")
    return all(_normalized(context.get(key)) for key in required_hashes)


def _policy_context(
    *,
    config: dict[str, Any] | None,
    context: dict[str, Any] | None,
    symbol: str | None,
    kill_zone: str | None,
    candle_time_utc: str | None,
    model: str | None,
) -> dict[str, Any]:
    merged = dict(context or {})
    market_cfg = (config or {}).get("market", {}) or {}
    ai_cfg = (config or {}).get("ai", {}) or {}
    merged.setdefault("purpose", "production_trade_decision")
    merged.setdefault("runtime_context", "live_orchestrator")
    if symbol:
        merged.setdefault("symbol", symbol)
    elif market_cfg.get("symbol"):
        merged.setdefault("symbol", market_cfg.get("symbol"))
    if kill_zone:
        merged.setdefault("kill_zone", kill_zone)
    if candle_time_utc:
        merged.setdefault("candle_time_utc", candle_time_utc)
    if model:
        merged.setdefault("model", model)
    elif ai_cfg.get("primary_model"):
        merged.setdefault("model", ai_cfg.get("primary_model"))
    return merged


def _context_tokens(context: dict[str, Any]) -> set[str]:
    keys = (
        "purpose",
        "runtime_context",
        "run_mode",
        "evaluation_mode",
        "source_universe_kind",
        "claim_type",
    )
    return {_normalized_case(context.get(key)) for key in keys if _normalized(context.get(key))}


def evaluate_ai_call_policy(
    *,
    config: dict[str, Any] | None,
    context: dict[str, Any] | None = None,
    symbol: str | None = None,
    kill_zone: str | None = None,
    candle_time_utc: str | None = None,
    model: str | None = None,
) -> AICallPolicyDecision:
    """Return whether the current runtime path may call the paid AI layer."""

    cfg = _policy_cfg(config)
    enabled = bool(cfg.get("enabled", True))
    apply_to_ai_call = bool(cfg.get("apply_to_ai_call", True))
    merged = _policy_context(
        config=config,
        context=context,
        symbol=symbol,
        kill_zone=kill_zone,
        candle_time_utc=candle_time_utc,
        model=model,
    )
    tokens = _context_tokens(merged)

    if not enabled:
        return AICallPolicyDecision(
            action="ALLOW_AI",
            allowed=True,
            enabled=False,
            apply_to_ai_call=False,
            reason="ai_call_policy_disabled",
            context=merged,
            evidence={"policy_enabled": False},
        )

    production_purposes = {
        item.casefold()
        for item in _configured_list(
            cfg,
            "production_purposes",
            (
                "production_trade_decision",
                "ai_reliability_smoke",
            ),
        )
    }
    research_ai_purposes = {
        item.casefold()
        for item in _configured_list(
            cfg,
            "research_ai_purposes",
            (
                "ai_decision_value_audit",
                "ai_delta_audit",
                "ai_reliability_audit",
                "prompt_model_regression",
            ),
        )
    }
    no_api_contexts = {
        item.casefold()
        for item in _configured_list(
            cfg,
            "no_api_contexts",
            (
                "historical_replay",
                "market_edge_replay",
                "mechanical_replay",
                "goal_session_projection",
                "research_market_edge",
                "missed_opportunity_inventory",
            ),
        )
    }
    purpose = _normalized_case(merged.get("purpose"))
    is_no_api_context = bool(tokens & no_api_contexts) or _truthy(merged.get("historical_replay"))
    is_research_ai = (
        purpose in research_ai_purposes
        or _truthy(merged.get("requires_paid_ai_for_research"))
        or _truthy(merged.get("ai_decision_layer_question"))
    )
    manifest_present = _has_manifest(merged)
    budget = _budget_usd(merged)
    cache_identity_present = _has_cache_identity(merged)
    owner_approved = _truthy(merged.get("owner_approved_budget")) or _truthy(
        merged.get("owner_approval_confirmed")
    )
    budget_contract = build_budget_contract(
        config=config,
        requested_budget_usd=budget,
        policy_cfg=cfg,
    )
    evidence = {
        "schema_version": AI_RELIABILITY_CONTRACT_SCHEMA_VERSION,
        "purpose": purpose,
        "context_tokens": sorted(tokens),
        "is_no_api_context": is_no_api_context,
        "is_research_ai": is_research_ai,
        "manifest_present": manifest_present,
        "budget_usd": budget,
        "budget_contract": budget_contract,
        "cache_identity_present": cache_identity_present,
        "cache_contract": {
            "schema_version": "ai_call_policy_cache_contract_v1",
            "cache_identity_present": cache_identity_present,
            "content_addressed_cache_required": bool(
                cfg.get("require_cache_key_for_research_ai", True)
            ),
        },
        "owner_approved_budget": owner_approved,
        "model_version_contract": build_model_version_contract(
            requested_model=merged.get("model")
        ),
        "deterministic_baseline_contract": build_deterministic_baseline_contract(
            reason="policy_pre_call_no_api_baseline"
        ),
        "disagreement_calibration_contract": build_disagreement_calibration_contract(),
        "semantic_ownership_handoff": build_semantic_ownership_handoff(),
        "source_artifact_path": ".context/00_core/ai_in_loop_cost_control_research_plan.md",
    }

    if purpose in production_purposes and not is_no_api_context:
        return AICallPolicyDecision(
            action="ALLOW_AI",
            allowed=True,
            enabled=True,
            apply_to_ai_call=apply_to_ai_call,
            reason="ai_cost_control_production_decision_allowed",
            context=merged,
            evidence=evidence,
        )

    if is_research_ai:
        if bool(cfg.get("require_manifest_for_research_ai", True)) and not manifest_present:
            return _deny("SKIP_AI_MANIFEST_REQUIRED", "ai_cost_control_manifest_required", apply_to_ai_call, merged, evidence)
        if bool(cfg.get("require_budget_cap_for_research_ai", True)) and budget is None:
            return _deny("SKIP_AI_BUDGET_REQUIRED", "ai_cost_control_budget_required", apply_to_ai_call, merged, evidence)
        if (
            bool(cfg.get("require_budget_cap_for_research_ai", True))
            and budget is not None
            and budget_contract["research_budget_cap_usd"] is not None
            and not budget_contract["budget_within_cap"]
        ):
            return _deny("SKIP_AI_BUDGET_CAP_EXCEEDED", "ai_cost_control_budget_cap_exceeded", apply_to_ai_call, merged, evidence)
        if bool(cfg.get("require_owner_approval_for_research_ai", True)) and not owner_approved:
            return _deny("SKIP_AI_OWNER_BUDGET_REQUIRED", "ai_cost_control_owner_budget_required", apply_to_ai_call, merged, evidence)
        if bool(cfg.get("require_cache_key_for_research_ai", True)) and not cache_identity_present:
            return _deny("SKIP_AI_CACHE_IDENTITY_REQUIRED", "ai_cost_control_cache_identity_required", apply_to_ai_call, merged, evidence)
        return AICallPolicyDecision(
            action="ALLOW_AI",
            allowed=True,
            enabled=True,
            apply_to_ai_call=apply_to_ai_call,
            reason="ai_cost_control_research_ai_sample_allowed",
            context=merged,
            evidence=evidence,
        )

    if is_no_api_context:
        return _deny("SKIP_AI_NO_API_REPLAY", "ai_cost_control_no_api_market_replay", apply_to_ai_call, merged, evidence)

    return AICallPolicyDecision(
        action="ALLOW_AI",
        allowed=True,
        enabled=True,
        apply_to_ai_call=apply_to_ai_call,
        reason="ai_cost_control_default_allowed",
        context=merged,
        evidence=evidence,
    )


def _deny(
    action: str,
    reason: str,
    apply_to_ai_call: bool,
    context: dict[str, Any],
    evidence: dict[str, Any],
) -> AICallPolicyDecision:
    return AICallPolicyDecision(
        action=action,
        allowed=not apply_to_ai_call,
        enabled=True,
        apply_to_ai_call=apply_to_ai_call,
        reason=reason,
        context=context,
        evidence=evidence,
    )


def record_ai_call_policy_decision(
    *,
    decision: AICallPolicyDecision,
    config: dict[str, Any] | None,
    phase: str,
) -> None:
    cfg = _policy_cfg(config)
    if not cfg:
        return
    if not bool(cfg.get("decision_log_enabled", True)):
        return
    path = Path(cfg.get("decision_log_path") or DEFAULT_AI_CALL_POLICY_LOG_PATH)
    entry = {
        "schema_version": "ai_call_policy_decision_v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "decision": decision.to_record(),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
    except OSError:
        return


def attach_ai_call_policy_to_record(record: dict[str, Any], decision: AICallPolicyDecision) -> None:
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["ai_call_policy"] = decision.to_record()
    inst = record.setdefault("instrumentation", {})
    inst["ai_call_policy_action"] = decision.action
    inst["ai_call_policy_allowed"] = decision.allowed
    inst["ai_call_policy_apply_to_ai_call"] = decision.apply_to_ai_call
    inst["ai_call_policy_reason"] = decision.reason


__all__ = [
    "AICallPolicyDecision",
    "attach_ai_call_policy_to_record",
    "evaluate_ai_call_policy",
    "record_ai_call_policy_decision",
]
