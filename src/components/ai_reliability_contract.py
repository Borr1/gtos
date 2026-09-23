"""AI reliability contract helpers for measured, budgeted AI use.

This module is intentionally deterministic and side-effect free. Runtime
callers use it to attach the same versioned contract to AI call-policy rows,
AI decision traces, malformed-response fallbacks, and route verifiers without
turning the AI layer into a broad paid replay engine or an ML owner.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


AI_RELIABILITY_CONTRACT_SCHEMA_VERSION = "ai_reliability_contract_v1"
CACHE_IDENTITY_SCHEMA_VERSION = "ai_content_addressed_cache_identity_v1"
DETERMINISTIC_BASELINE_SCHEMA_VERSION = "ai_deterministic_baseline_v1"
FALLBACK_BEHAVIOR_SCHEMA_VERSION = "ai_fallback_behavior_v1"

_CONFIG_HASH_KEYS = (
    "ai",
    "ai_call_policy",
    "ai_supervisor",
    "budget",
    "gtos_vnext_runtime",
    "model_a",
    "risk",
)


def stable_json(value: Any) -> str:
    """Return deterministic JSON for hashing heterogeneous payloads."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def stable_sha256(value: Any) -> str:
    """Hash a value after deterministic JSON/text normalization."""

    if isinstance(value, str):
        payload = value
    else:
        payload = stable_json(value)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def config_fingerprint(config: dict[str, Any] | None) -> dict[str, Any]:
    """Hash the AI-relevant config subset used by call/cache decisions."""

    cfg = config or {}
    subset = {key: cfg.get(key) for key in _CONFIG_HASH_KEYS if key in cfg}
    return {
        "schema_version": "ai_reliability_config_fingerprint_v1",
        "included_keys": sorted(subset),
        "config_hash": stable_sha256(subset),
    }


def build_model_version_contract(
    *,
    requested_model: str | None,
    served_model: str | None = None,
    schema_name: str = "PrimaryAnalysisOutput",
) -> dict[str, Any]:
    """Build the model/schema version contract for one AI decision surface."""

    requested = str(requested_model or "").strip()
    served = str(served_model or "").strip()
    return {
        "schema_version": "ai_model_version_contract_v1",
        "requested_model": requested,
        "requested_model_hash": stable_sha256(requested) if requested else None,
        "served_model": served or None,
        "served_model_hash": stable_sha256(served) if served else None,
        "served_model_pin_required": True,
        "schema_name": schema_name,
        "schema_contract_version": AI_RELIABILITY_CONTRACT_SCHEMA_VERSION,
        "schema_validation_required": True,
    }


def build_cache_identity(
    *,
    model: str | None,
    prompt_bundle_sha256: str | None,
    user_message_sha256: str | None,
    config: dict[str, Any] | None,
    source_context: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return a content-addressed cache identity for a paid AI input tuple."""

    cfg_fp = config_fingerprint(config) if config is not None else None
    model_hash = stable_sha256(str(model or "")) if model else None
    source_hash = stable_sha256(source_context or {})
    fields = {
        "model_hash": model_hash,
        "prompt_hash": prompt_bundle_sha256,
        "input_hash": user_message_sha256,
        "config_hash": cfg_fp["config_hash"] if cfg_fp else None,
        "source_data_hash": source_hash,
    }
    missing = sorted(key for key, value in fields.items() if not value)
    cache_key = stable_sha256(fields) if not missing else None
    return {
        "schema_version": CACHE_IDENTITY_SCHEMA_VERSION,
        "content_addressed_cache_key": cache_key,
        "cache_key_status": "complete" if cache_key else "incomplete",
        "missing_fields": missing,
        "model_hash": fields["model_hash"],
        "prompt_hash": fields["prompt_hash"],
        "input_hash": fields["input_hash"],
        "config_hash": fields["config_hash"],
        "source_data_hash": fields["source_data_hash"],
        "config_fingerprint": cfg_fp,
    }


def research_budget_cap_usd(
    config: dict[str, Any] | None,
    policy_cfg: dict[str, Any] | None = None,
) -> float | None:
    """Resolve the strict per-run research AI cap from policy or budget config."""

    policy = policy_cfg or {}
    candidates = (
        policy.get("max_research_ai_budget_usd"),
        policy.get("research_ai_budget_cap_usd"),
        ((config or {}).get("budget") or {}).get("research_ai_budget_cap_usd"),
        ((config or {}).get("budget") or {}).get("monthly_cap_usd"),
    )
    for value in candidates:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            return parsed
    return None


def build_budget_contract(
    *,
    config: dict[str, Any] | None,
    requested_budget_usd: float | None,
    policy_cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the budget guard contract for research AI sampling."""

    cap = research_budget_cap_usd(config, policy_cfg)
    within_cap = (
        requested_budget_usd is not None
        and cap is not None
        and requested_budget_usd <= cap
    )
    return {
        "schema_version": "ai_budget_contract_v1",
        "requested_budget_usd": requested_budget_usd,
        "research_budget_cap_usd": cap,
        "budget_within_cap": within_cap,
        "paid_broad_historical_replay_allowed": False,
        "requires_pre_call_manifest": True,
        "requires_owner_budget_approval": True,
        "requires_content_addressed_cache": True,
    }


def build_deterministic_baseline_contract(
    *,
    reason: str,
    baseline_action: str = "NO_TRADE",
    source_status: str = "as_of_runtime_context_only",
) -> dict[str, Any]:
    """Describe the no-API deterministic baseline/fallback action."""

    return {
        "schema_version": DETERMINISTIC_BASELINE_SCHEMA_VERSION,
        "baseline_id": "deterministic_no_api_policy_baseline_v1",
        "baseline_action": baseline_action,
        "reason": reason,
        "uses_paid_ai": False,
        "trade_permission": False,
        "broker_runtime_change": False,
        "source_status": source_status,
        "promotion_status": "not_a_production_change_or_ml_label",
    }


def build_fallback_behavior_contract(
    *,
    reason: str | None,
    response_status: str | None,
    parse_attempts: int | None,
) -> dict[str, Any]:
    """Describe fail-soft behavior when the AI layer is unavailable/unusable."""

    fallback_reason = str(reason or response_status or "none").strip()
    status = str(response_status or "").strip()
    active = bool(
        fallback_reason
        and fallback_reason != "none"
        and (
            fallback_reason.startswith("ai_call_policy:")
            or fallback_reason.startswith("api_")
            or fallback_reason.startswith("unexpected_error")
            or fallback_reason == "ai_output_malformed"
            or status
            in {
                "api_timeout",
                "api_server_error",
                "api_rate_limit",
                "unexpected_error",
                "malformed_demoted",
            }
        )
    )
    return {
        "schema_version": FALLBACK_BEHAVIOR_SCHEMA_VERSION,
        "fallback_active": active,
        "fallback_reason": fallback_reason if active else None,
        "response_status": status or None,
        "parse_attempts": int(parse_attempts or 0),
        "fallback_action": "NO_TRADE" if active else None,
        "confidence_score": 0 if active else None,
        "retry_policy": "one_format_retry_then_no_trade" if active else "not_applicable",
        "semantic_repair_policy": "preserve_fields_or_fail_closed",
        "broker_runtime_change": False,
    }


def build_disagreement_calibration_contract() -> dict[str, Any]:
    """Route-owned handoff for disagreement calibration without absorbing ML."""

    return {
        "schema_version": "ai_disagreement_calibration_contract_v1",
        "ai_lane_owns": [
            "schema validity",
            "prompt/model version traceability",
            "paid-call budget/cache guard",
            "malformed-response fallback",
            "AI-narrowing health override",
        ],
        "first_class_probability_owner": "probability_debate_team_engine_v4",
        "first_class_confluence_owner": "follow_avoid_mixed_numeric_confluence_v4",
        "required_runtime_inputs": [
            "recommended action alternatives",
            "AI role",
            "source completeness",
            "prompt scope",
            "cache identity",
            "response status",
        ],
        "calibration_metrics_deferred_to_ml_or_probability_owner": [
            "Brier",
            "ECE",
            "reliability bins",
            "logloss",
        ],
        "ai_reliability_runtime_decision": "measure_and_fail_closed_not_trade_permission",
    }


def build_semantic_ownership_handoff() -> dict[str, Any]:
    """Preserve Wave3 semantic ownership boundaries for the AI lane."""

    return {
        "schema_version": "ai_semantic_ownership_handoff_v1",
        "ai_reliability_cost_control_owns": [
            "LLM schema/model versioning",
            "AI call cache and budget guards",
            "malformed-response fallback behavior",
            "AI trace reliability and supervisor health checks",
        ],
        "same_symbol_same_instrument_lifecycle_v4_owns": [
            "same-symbol lifecycle",
            "scale/reduce/close/reverse",
            "ticket-bound open-trade competition",
            "duplicate exposure",
        ],
        "probability_debate_team_engine_v4_owns": [
            "calibrated probability",
            "EV",
            "uncertainty",
            "numeric theses",
            "final action selection",
        ],
        "follow_avoid_mixed_numeric_confluence_v4_owns": [
            "FOLLOW/AVOID/MIXED numeric mapping",
            "source freshness",
            "source completeness",
            "structured disagreement",
        ],
        "wave4_wave5_ml_owns": [
            "Feature Store",
            "Label Store",
            "Digital Twin",
            "ML baselines",
            "model registry",
            "challengers",
            "walk-forward validation",
        ],
        "no_copy_rule": "do_not_copy_redacted_account_broker_truth_to_ftmo",
    }


__all__ = [
    "AI_RELIABILITY_CONTRACT_SCHEMA_VERSION",
    "CACHE_IDENTITY_SCHEMA_VERSION",
    "DETERMINISTIC_BASELINE_SCHEMA_VERSION",
    "FALLBACK_BEHAVIOR_SCHEMA_VERSION",
    "build_budget_contract",
    "build_cache_identity",
    "build_deterministic_baseline_contract",
    "build_disagreement_calibration_contract",
    "build_fallback_behavior_contract",
    "build_model_version_contract",
    "build_semantic_ownership_handoff",
    "config_fingerprint",
    "research_budget_cap_usd",
    "stable_sha256",
]
