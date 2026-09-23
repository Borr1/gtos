"""No-API helpers for auditing GTOS AI decision architecture evidence."""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any


BOUNDARY_SCHEMA = "main_orch48_ai_decision_architecture_audit_v1"


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "artifact_scope": "main_side_research_compiler",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def _bool_text(value: str) -> bool | None:
    text = value.strip().lower()
    if text == "true":
        return True
    if text == "false":
        return False
    return None


def _config_value(config_text: str, key: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(key)}:\s*\"?([^\"\n#]+)\"?", config_text)
    return match.group(1).strip() if match else ""


def _nested_bool(config_text: str, section: str, key: str) -> bool | None:
    match = re.search(rf"(?ms)^\s*{re.escape(section)}:\s*\n(?P<body>(?:^\s+.+\n?)+)", config_text)
    if not match:
        return None
    value_match = re.search(rf"(?m)^\s+{re.escape(key)}:\s*(true|false)\b", match.group("body"))
    return _bool_text(value_match.group(1)) if value_match else None


def classify_malformed_ai_response(row: dict[str, Any]) -> str:
    raw_response = normalized(row.get("raw_response")).strip().lower()
    error = normalized(row.get("error")).lower()
    raw_len = int(row.get("raw_response_length") or 0)
    if error.startswith("expecting value:") and raw_len < 100:
        return "FLAT_REFUSAL_OR_SHORT_NON_JSON"
    if raw_response.startswith("```json") or "extra data" in error:
        return "JSON_FENCE_OR_TRAILING_TEXT_PARSE_FAILURE"
    if raw_response and not raw_response.startswith("{"):
        return "NON_JSON_RESPONSE_PARSE_FAILURE"
    return "OTHER_MALFORMED_AI_RESPONSE"


def summarize_malformed_ai_responses(rows: list[dict[str, Any]]) -> dict[str, Any]:
    classifications = Counter(classify_malformed_ai_response(row) for row in rows)
    attempts = Counter(normalized(row.get("attempt")) for row in rows)
    timestamps = [normalized(row.get("timestamp")) for row in rows if normalized(row.get("timestamp"))]
    return {
        "malformed_response_rows": len(rows),
        "malformed_response_classification_counts": dict(sorted(classifications.items())),
        "malformed_response_attempt_counts": dict(sorted(attempts.items())),
        "first_malformed_response_timestamp": min(timestamps) if timestamps else "",
        "latest_malformed_response_timestamp": max(timestamps) if timestamps else "",
    }


def ai_architecture_config_audit_row(
    config_text: str,
    *,
    audit_row_id: str,
    source_artifact: str,
    source_sha256: str,
) -> dict[str, Any]:
    session_memory = _bool_text(_config_value(config_text, "session_memory_enabled"))
    timeout_retry = _bool_text(_config_value(config_text, "timeout_retry_enabled"))
    return {
        "ai_architecture_audit_row_id": audit_row_id,
        "audit_surface": "ai_runtime_config",
        "schema_version": BOUNDARY_SCHEMA,
        "source_artifact": source_artifact,
        "source_sha256": source_sha256,
        "ai_billing_mode": _config_value(config_text, "billing_mode"),
        "ai_primary_model": _config_value(config_text, "primary_model"),
        "ai_primary_effort": _config_value(config_text, "primary_effort"),
        "ai_timeout_retry_enabled": timeout_retry,
        "session_memory_enabled": session_memory,
        "confidence_filter_mode": _config_value(config_text, "confidence_filter_mode"),
        "ai_architecture_action": "KEEP_API_DECISION_LAYER_WITH_EXISTING_COST_CONTROLS_PENDING_BRANCH_REVIEW",
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "production_change_opened_now": False,
        "research_boundary": research_boundary(),
    }


def ai_architecture_malformed_response_audit_row(
    malformed_rows: list[dict[str, Any]],
    *,
    audit_row_id: str,
    source_artifact: str,
    source_sha256: str,
) -> dict[str, Any]:
    summary = summarize_malformed_ai_responses(malformed_rows)
    return {
        "ai_architecture_audit_row_id": audit_row_id,
        "audit_surface": "malformed_response_monitoring",
        "schema_version": BOUNDARY_SCHEMA,
        "source_artifact": source_artifact,
        "source_sha256": source_sha256,
        **summary,
        "ai_architecture_action": "HARDEN_SCHEMA_PARSER_AND_KEEP_REFUSAL_MONITORING_BEFORE_EXPANDING_AI_ROLE"
        if malformed_rows
        else "NO_MALFORMED_RESPONSE_ROWS_FOUND",
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "production_change_opened_now": False,
        "research_boundary": research_boundary(),
    }


def ai_architecture_selector_dossier_audit_row(
    dossier_summary: dict[str, Any],
    *,
    audit_row_id: str,
    source_artifact: str,
    source_sha256: str,
) -> dict[str, Any]:
    return {
        "ai_architecture_audit_row_id": audit_row_id,
        "audit_surface": "mechanical_selector_ai_narrowing_dossier",
        "schema_version": BOUNDARY_SCHEMA,
        "source_artifact": source_artifact,
        "source_sha256": source_sha256,
        "selector_dossier_rows": int(dossier_summary.get("rows") or 0),
        "mechanical_selector_scope_draft_ready_for_separate_review_rows": int(
            dossier_summary.get("mechanical_selector_scope_draft_ready_for_separate_review_rows") or 0
        ),
        "capacity_blocked_selector_blocklist_required_rows": int(
            dossier_summary.get("capacity_blocked_selector_blocklist_required_rows") or 0
        ),
        "implementation_ready_candidate_rows": int(dossier_summary.get("implementation_ready_candidate_rows") or 0),
        "capacity_blocked_candidate_rows": int(dossier_summary.get("capacity_blocked_candidate_rows") or 0),
        "production_change_opened_now_rows": int(dossier_summary.get("production_change_opened_now_rows") or 0),
        "runtime_candidate_use_permitted_rows": int(dossier_summary.get("runtime_candidate_use_permitted_rows") or 0),
        "ai_architecture_recommendation_counts": dossier_summary.get("ai_architecture_recommendation_counts") or {},
        "ai_architecture_action": "USE_DEFAULT_OFF_MECHANICAL_SELECTOR_DOSSIER_TO_NARROW_AI_ONLY_AFTER_PRODUCTION_REVIEW",
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "production_change_opened_now": False,
        "research_boundary": research_boundary(),
    }


def summarize_b12_confidence_autopsy(autopsy: dict[str, Any]) -> dict[str, Any]:
    distribution = autopsy.get("distribution") or {}
    predictive = autopsy.get("predictive") or []
    all_results = autopsy.get("all_results") or []
    tested = [row for row in all_results if normalized(row.get("flag")) not in ("INSUFFICIENT_N", "DEGENERATE")]
    return {
        "b12_confidence_trades_loaded": int(autopsy.get("n_trades_loaded") or 0),
        "b12_confidence_trades_evaluated": int(
            autopsy.get("n_trades_after_dedupe") or distribution.get("n") or 0
        ),
        "b12_confidence_mean": distribution.get("mean"),
        "b12_confidence_mode": distribution.get("mode"),
        "b12_confidence_mode_fraction": distribution.get("mode_fraction"),
        "b12_confidence_fraction_at_80": distribution.get("fraction_at_80"),
        "b12_confidence_family_size": int(autopsy.get("family_size") or len(tested)),
        "b12_confidence_total_strata_observed": len(all_results),
        "b12_confidence_tested_strata": len(tested),
        "b12_confidence_predictive_strata": len(predictive),
        "b12_confidence_min_n": int(autopsy.get("min_n") or 0),
        "b12_confidence_alpha": autopsy.get("alpha"),
        "b12_confidence_rho_threshold": autopsy.get("rho_threshold"),
        "b12_confidence_n_perms": int(autopsy.get("n_perms") or 0),
        "b12_confidence_seed": autopsy.get("seed"),
        "b12_confidence_strata_axes": autopsy.get("strata_axes") or [],
    }


def ai_architecture_confidence_filter_quarantine_row(
    config_text: str,
    b12_autopsy: dict[str, Any],
    *,
    orchestrator_text: str,
    confidence_scorer_text: str,
    audit_row_id: str,
    source_artifact: str,
    source_sha256: str,
    b12_source_artifact: str,
    b12_source_sha256: str,
) -> dict[str, Any]:
    autopsy = summarize_b12_confidence_autopsy(b12_autopsy)
    confidence_filter_mode = _config_value(config_text, "confidence_filter_mode")
    active_branch_present = (
        'conf_mode == "active"' in orchestrator_text and "SKIPPED_LOW_CONFIDENCE" in orchestrator_text
    )
    shadow_mode_configured = confidence_filter_mode == "shadow"
    predictive_strata = int(autopsy["b12_confidence_predictive_strata"])
    keep_shadow = shadow_mode_configured and predictive_strata == 0
    return {
        "ai_architecture_audit_row_id": audit_row_id,
        "audit_surface": "confidence_filter_quarantine",
        "schema_version": BOUNDARY_SCHEMA,
        "source_artifact": source_artifact,
        "source_sha256": source_sha256,
        "b12_source_artifact": b12_source_artifact,
        "b12_source_sha256": b12_source_sha256,
        "confidence_filter_mode": confidence_filter_mode,
        "confidence_filter_shadow_mode_configured": shadow_mode_configured,
        "confidence_filter_active_branch_present": active_branch_present,
        "confidence_scorer_gold_price_config_present": (
            "price_range: [1500.0, 6000.0]" in config_text
            and "_PRICE_RANGE = (1500.0, 6000.0)" in confidence_scorer_text
        ),
        **autopsy,
        "ai_architecture_action": (
            "KEEP_CONFIDENCE_FILTER_SHADOW_AND_BLOCK_ACTIVE_PROMOTION_WITHOUT_FRESH_VALIDATION"
            if keep_shadow
            else "CONFIDENCE_FILTER_REQUIRES_SEPARATE_REVIEW_BEFORE_ANY_RUNTIME_USE"
        ),
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "production_change_opened_now": False,
        "live_ai_runtime_change_now": False,
        "research_boundary": research_boundary(),
    }


def summarize_ai_architecture_audit_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "audit_surface_counts": dict(sorted(Counter(normalized(row.get("audit_surface")) for row in rows).items())),
        "ai_architecture_action_counts": dict(
            sorted(Counter(normalized(row.get("ai_architecture_action")) for row in rows).items())
        ),
        "malformed_response_rows": sum(int(row.get("malformed_response_rows") or 0) for row in rows),
        "selector_dossier_rows": sum(int(row.get("selector_dossier_rows") or 0) for row in rows),
        "mechanical_selector_scope_draft_ready_for_separate_review_rows": sum(
            int(row.get("mechanical_selector_scope_draft_ready_for_separate_review_rows") or 0) for row in rows
        ),
        "capacity_blocked_selector_blocklist_required_rows": sum(
            int(row.get("capacity_blocked_selector_blocklist_required_rows") or 0) for row in rows
        ),
        "confidence_filter_quarantine_rows": sum(
            normalized(row.get("audit_surface")) == "confidence_filter_quarantine" for row in rows
        ),
        "b12_confidence_predictive_strata": sum(
            int(row.get("b12_confidence_predictive_strata") or 0) for row in rows
        ),
        "confidence_filter_active_branch_present_rows": sum(
            bool(row.get("confidence_filter_active_branch_present")) for row in rows
        ),
        "paid_api_or_vendor_call_rows": sum(bool(row.get("paid_api_or_vendor_call")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "production_change_opened_now_rows": sum(bool(row.get("production_change_opened_now")) for row in rows),
    }


def parse_jsonl(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
