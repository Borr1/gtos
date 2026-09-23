"""Denominator forward-capture contract helpers.

The helpers in this module are observation and validation utilities only. They
do not call MT5, place orders, mutate account/order/deal/position state, reveal
credentials, or promote replay/proxy rows into historical broker truth.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "denominator_forward_capture_contract_v1"
COMPONENT = "denominator_forward_capture_contract"
EVIDENCE_CLASS = "production_code_integration_denominator_forward_capture_contract"
RESULT_USE_STATUS = "RESULT_MATERIALIZATION_REQUIRED"
EVENT_VALIDATION_SCHEMA = "gtos.final_moonshot.denominator_forward_capture.event_validation.v1"
LOG_INGESTION_SUMMARY_SCHEMA = "gtos.final_moonshot.denominator_forward_capture.log_ingestion_summary.v1"
EXPANSION_REVIEW_SCHEMA = "gtos.final_moonshot.denominator_forward_capture.expansion_review.v1"
ROW_REVIEW_SUMMARY_SCHEMA = "gtos.final_moonshot.denominator_forward_capture.row_review_summary.v1"
ROW_REVIEW_LEDGER_SCHEMA = "gtos.final_moonshot.denominator_forward_capture.row_review_ledger.v1"
DOWNSTREAM_JOIN_SUMMARY_SCHEMA = (
    "gtos.final_moonshot.denominator_forward_capture.downstream_join_summary.v1"
)
SELECTED_PACKAGE_JOIN_LEDGER_SCHEMA = (
    "gtos.final_moonshot.denominator_forward_capture.selected_package_join_ledger.v1"
)
LIFECYCLE_LABEL_JOIN_LEDGER_SCHEMA = (
    "gtos.final_moonshot.denominator_forward_capture.lifecycle_label_join_ledger.v1"
)
DEFAULT_LOG_PATH = "shadow_logs/denominator_forward_capture.jsonl"
ENABLED_CONFIG_KEY = "denominator_forward_capture_contract_enabled"
LOG_ENABLED_CONFIG_KEY = "denominator_forward_capture_contract_log_enabled"
LOG_PATH_CONFIG_KEY = "denominator_forward_capture_contract_log_path"

PENDING_CREATED_DECISION_TIME_FAMILY = "pending_created_exact_decision_time"
M15_GRID_ORDER_LIFECYCLE_FAMILY = "m15_grid_order_lifecycle"
ULTIMATE_CANDIDATE_PACKAGE_SUPPLEMENTAL_CONTEXT_FIELDS: tuple[str, ...] = (
    "ultimate_candidate_package_shadow_status",
    "ultimate_candidate_package_shadow_authority_closed",
    "ultimate_candidate_package_shadow_packet_present",
    "ultimate_candidate_package_shadow_packet_hash",
    "ultimate_candidate_package_shadow_decision_status",
    "ultimate_candidate_package_shadow_selected_candidate_id",
    "ultimate_candidate_package_selected_candidate_id",
    "ultimate_candidate_package_approved_risk_pct",
    "ultimate_candidate_package_runtime_effect_now",
    "ultimate_candidate_package_live_execution_activation_allowed",
    "ultimate_candidate_package_final_package_selection_allowed",
    "ultimate_candidate_package_order_calls",
    "ultimate_candidate_package_execution_policy_status",
    "ultimate_candidate_package_selected_order_type_architecture",
    "ultimate_candidate_package_execution_order_type_policy_selectable",
    "ultimate_candidate_package_gate_violations",
)

logger = logging.getLogger(__name__)

PENDING_CREATED_DECISION_TIME_REQUIRED_FIELDS: tuple[str, ...] = (
    "decision_time_utc",
    "row_bound_candidate_id",
    "pending_created_time_utc",
    "order_intent",
    "cancel_replace_or_time_in_force",
    "source_event_hash",
)

M15_GRID_ORDER_LIFECYCLE_REQUIRED_FIELDS: tuple[str, ...] = (
    "decision_time_utc",
    "original_candidate_id",
    "stable_decision_window_id",
    "row_bound_candidate_id",
    "order_intent",
    "order_type",
    "pending_ticket_or_order_ticket",
    "lifecycle_state",
    "fill_or_no_fill",
    "cancel_replace_or_time_in_force",
    "broker_profile_namespace",
    "source_event_hash",
)

PENDING_CREATED_DECISION_TIME_FIELD_CONTRACTS: tuple[dict[str, str], ...] = (
    {
        "field_name": "decision_time_utc",
        "required_source_class": "decision_packet",
        "capture_surface": "runtime_decision_packet_or_order_intent_event",
        "capture_timing": "pre_decision_or_at_order_intent",
        "asof_role": "predecision_join_key_no_outcome_leakage",
        "denominator_role": "required_before_pending_created_label_denominator_use",
    },
    {
        "field_name": "row_bound_candidate_id",
        "required_source_class": "candidate_registry",
        "capture_surface": "selected_package_candidate_packet",
        "capture_timing": "candidate_selection",
        "asof_role": "predecision_selected_candidate_identity",
        "denominator_role": "required_to_bind_pending_created_label_to_runtime_candidate",
    },
    {
        "field_name": "pending_created_time_utc",
        "required_source_class": "pending_lifecycle_event",
        "capture_surface": "pending_order_lifecycle_capture",
        "capture_timing": "pending_created_transition",
        "asof_role": "post_intent_lifecycle_label_not_predecision_feature",
        "denominator_role": "required_to_audit_proxy_window_vs_original_decision_time",
    },
    {
        "field_name": "order_intent",
        "required_source_class": "order_intent_event",
        "capture_surface": "execution_manager_order_intent_event",
        "capture_timing": "order_send_attempt",
        "asof_role": "decision_action_label_only_after_freeze",
        "denominator_role": "required_before_order_intent_label_use",
    },
    {
        "field_name": "cancel_replace_or_time_in_force",
        "required_source_class": "pending_lifecycle_event",
        "capture_surface": "cancel_replace_time_in_force_capture",
        "capture_timing": "cancel_replace_or_expiry_transition",
        "asof_role": "post_intent_management_label_not_predecision_feature",
        "denominator_role": "required_for_stale_thesis_and_execution_policy_labels",
    },
    {
        "field_name": "source_event_hash",
        "required_source_class": "source_event_hash",
        "capture_surface": "runtime_event_hash_and_notification_context",
        "capture_timing": "every_decision_order_lifecycle_event",
        "asof_role": "provenance_integrity_no_outcome_leakage_by_itself",
        "denominator_role": "required_for_replay_vs_runtime_event_dedup_and_audit",
    },
)

M15_GRID_ORDER_LIFECYCLE_FIELD_CONTRACTS: tuple[dict[str, str], ...] = (
    {
        "field_name": "decision_time_utc",
        "required_source_class": "decision_packet",
        "capture_surface": "runtime_decision_packet_or_order_intent_event",
        "capture_timing": "pre_decision_or_at_order_intent",
        "asof_role": "predecision_join_key_no_outcome_leakage",
        "denominator_role": "required_before_exact_denominator_expansion",
    },
    {
        "field_name": "original_candidate_id",
        "required_source_class": "candidate_registry",
        "capture_surface": "candidate_generation_packet",
        "capture_timing": "candidate_materialization",
        "asof_role": "predecision_identity_no_outcome_leakage",
        "denominator_role": "required_for_candidate_namespace_parity",
    },
    {
        "field_name": "stable_decision_window_id",
        "required_source_class": "decision_packet",
        "capture_surface": "runtime_decision_packet_or_replay_bridge_packet",
        "capture_timing": "pre_decision_or_at_order_intent",
        "asof_role": "predecision_window_join_key_no_outcome_leakage",
        "denominator_role": "required_fallback_when_original_candidate_id_namespaces_diverge",
    },
    {
        "field_name": "row_bound_candidate_id",
        "required_source_class": "candidate_registry",
        "capture_surface": "selected_package_candidate_packet",
        "capture_timing": "candidate_selection",
        "asof_role": "predecision_selected_candidate_identity",
        "denominator_role": "required_to_bind_sleeve_member_axis_to_runtime_candidate",
    },
    {
        "field_name": "order_intent",
        "required_source_class": "order_intent_event",
        "capture_surface": "execution_manager_order_intent_event",
        "capture_timing": "order_send_attempt",
        "asof_role": "decision_action_label_only_after_freeze",
        "denominator_role": "required_before_order_type_label_or_execution_architecture_use",
    },
    {
        "field_name": "order_type",
        "required_source_class": "order_intent_event",
        "capture_surface": "execution_manager_order_intent_event",
        "capture_timing": "order_send_attempt",
        "asof_role": "decision_action_label_only_after_freeze",
        "denominator_role": "required_for_limit_first_vs_guarded_market_denominator",
    },
    {
        "field_name": "pending_ticket_or_order_ticket",
        "required_source_class": "broker_order_event",
        "capture_surface": "broker_order_lifecycle_capture",
        "capture_timing": "broker_order_ack_or_pending_created",
        "asof_role": "broker_identity_label_not_predecision_feature",
        "denominator_role": "required_for_ticket_bound_lifecycle_join",
    },
    {
        "field_name": "lifecycle_state",
        "required_source_class": "pending_lifecycle_event",
        "capture_surface": "pending_order_lifecycle_capture",
        "capture_timing": "pending_lifecycle_transition",
        "asof_role": "post_intent_lifecycle_label_not_predecision_feature",
        "denominator_role": "required_for_fill_no_fill_and_stale_thesis_labels",
    },
    {
        "field_name": "fill_or_no_fill",
        "required_source_class": "pending_lifecycle_event",
        "capture_surface": "pending_order_lifecycle_capture",
        "capture_timing": "fill_no_fill_resolution",
        "asof_role": "post_decision_label_not_predecision_feature",
        "denominator_role": "required_for_fillability_cost_risk_labels",
    },
    {
        "field_name": "cancel_replace_or_time_in_force",
        "required_source_class": "pending_lifecycle_event",
        "capture_surface": "cancel_replace_time_in_force_capture",
        "capture_timing": "cancel_replace_or_expiry_transition",
        "asof_role": "post_intent_management_label_not_predecision_feature",
        "denominator_role": "required_for_execution_policy_and_stale_thesis_labels",
    },
    {
        "field_name": "broker_profile_namespace",
        "required_source_class": "broker_profile_event",
        "capture_surface": "broker_profile_runtime_context",
        "capture_timing": "pre_decision_or_at_order_intent",
        "asof_role": "broker_profile_context_no_outcome_leakage",
        "denominator_role": "required_for_redacted_account_ftmo_profile_specific_support",
    },
    {
        "field_name": "source_event_hash",
        "required_source_class": "source_event_hash",
        "capture_surface": "runtime_event_hash_and_notification_context",
        "capture_timing": "every_decision_order_lifecycle_event",
        "asof_role": "provenance_integrity_no_outcome_leakage_by_itself",
        "denominator_role": "required_for_replay_vs_runtime_event_dedup_and_audit",
    },
)

REQUIRED_FIELDS_BY_FAMILY: dict[str, tuple[str, ...]] = {
    PENDING_CREATED_DECISION_TIME_FAMILY: PENDING_CREATED_DECISION_TIME_REQUIRED_FIELDS,
    M15_GRID_ORDER_LIFECYCLE_FAMILY: M15_GRID_ORDER_LIFECYCLE_REQUIRED_FIELDS,
}

FIELD_CONTRACTS_BY_FAMILY: dict[str, tuple[dict[str, str], ...]] = {
    PENDING_CREATED_DECISION_TIME_FAMILY: PENDING_CREATED_DECISION_TIME_FIELD_CONTRACTS,
    M15_GRID_ORDER_LIFECYCLE_FAMILY: M15_GRID_ORDER_LIFECYCLE_FIELD_CONTRACTS,
}

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "row_bound_candidate_id": (
        "row_bound_candidate_id",
        "selected_candidate_id",
        "gtos_vnext_candidate_id",
        "candidate_id",
    ),
    "original_candidate_id": (
        "original_candidate_id",
        "candidate_id",
        "gtos_vnext_candidate_id",
    ),
    "stable_decision_window_id": (
        "stable_decision_window_id",
        "decision_window_id",
        "gtos_vnext_decision_window_id",
    ),
    "pending_ticket_or_order_ticket": (
        "pending_ticket_or_order_ticket",
        "pending_ticket",
        "order_ticket",
        "mt5_order_ticket",
        "mt5_entry_order_ticket",
    ),
    "lifecycle_state": (
        "lifecycle_state",
        "pending_lifecycle_v4_state",
        "intent_after_check",
    ),
    "fill_or_no_fill": (
        "fill_or_no_fill",
        "fill_no_fill_label",
        "broker_fill_state",
    ),
    "cancel_replace_or_time_in_force": (
        "cancel_replace_or_time_in_force",
        "time_in_force",
        "cancel_reason",
        "expiry_time_utc",
        "cancel_expiry_reason_status",
    ),
    "broker_profile_namespace": (
        "broker_profile_namespace",
        "risk_reservation_broker_namespace",
        "broker_account_namespace",
    ),
    "source_event_hash": (
        "source_event_hash",
        "source_hash",
        "source_event_hash_sha256",
        "gtos_vnext_source_event_hash",
        "gtos_vnext_source_event_hash_sha256",
    ),
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _noneish(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return str(value)


def _packet_hash(payload: Mapping[str, Any]) -> str:
    material = {
        key: value
        for key, value in payload.items()
        if key not in {"generated_utc", "contract_hash_sha256", "packet_hash_sha256"}
    }
    raw = json.dumps(
        _json_safe(material),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _aliases_for(field_name: str) -> tuple[str, ...]:
    aliases = FIELD_ALIASES.get(field_name, ())
    if field_name in aliases:
        return aliases
    return (field_name, *aliases)


def _field_value(event: Mapping[str, Any], field_name: str) -> Any:
    for alias in _aliases_for(field_name):
        value = event.get(alias)
        if not _noneish(value):
            return value
    return None


def _supplemental_package_context(event: Mapping[str, Any]) -> dict[str, Any]:
    context = {
        field_name: _json_safe(event.get(field_name))
        for field_name in ULTIMATE_CANDIDATE_PACKAGE_SUPPLEMENTAL_CONTEXT_FIELDS
        if not _noneish(event.get(field_name))
    }
    summary = event.get("ultimate_candidate_package_shadow_summary")
    if isinstance(summary, Mapping):
        context["ultimate_candidate_package_shadow_summary"] = _json_safe(summary)
    return context


def required_fields_for_family(requirement_family: str) -> tuple[str, ...]:
    try:
        return REQUIRED_FIELDS_BY_FAMILY[requirement_family]
    except KeyError as exc:
        raise ValueError(f"unknown denominator capture requirement family: {requirement_family}") from exc


def field_contracts_for_family(requirement_family: str) -> tuple[dict[str, str], ...]:
    required_fields_for_family(requirement_family)
    return tuple(dict(row) for row in FIELD_CONTRACTS_BY_FAMILY[requirement_family])


def build_denominator_forward_capture_code_contract(
    *,
    pending_created_capture_required_rows: int,
    m15_grid_capture_required_rows: int,
    generated_utc: str | None = None,
) -> dict[str, Any]:
    """Build a route-agnostic manifest for current denominator capture blockers."""
    generated = generated_utc or _now_iso()
    family_inputs = (
        (PENDING_CREATED_DECISION_TIME_FAMILY, int(pending_created_capture_required_rows)),
        (M15_GRID_ORDER_LIFECYCLE_FAMILY, int(m15_grid_capture_required_rows)),
    )
    family_contracts: list[dict[str, Any]] = []
    for family, row_count in family_inputs:
        required_fields = required_fields_for_family(family)
        family_contracts.append(
            {
                "requirement_family": family,
                "status": "prospective_capture_required",
                "capture_required_rows": row_count,
                "required_capture_fields": list(required_fields),
                "required_capture_field_count": len(required_fields),
                "required_capture_field_rows": row_count * len(required_fields),
                "field_contracts": list(field_contracts_for_family(family)),
                "historical_reconstruction_allowed": False,
                "selected_package_denominator_use_allowed": False,
                "training_use_allowed": False,
                "model_training_allowed": False,
                "final_package_selection_allowed": False,
            }
        )
    payload = {
        "schema": "gtos.final_moonshot.denominator_forward_capture.code_contract.v1",
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "generated_utc": generated,
        "status": "default_off_capture_writer_ready_for_runtime_wiring",
        "default_log_path": DEFAULT_LOG_PATH,
        "runtime_config_keys": {
            "enabled": ENABLED_CONFIG_KEY,
            "log_enabled": LOG_ENABLED_CONFIG_KEY,
            "log_path": LOG_PATH_CONFIG_KEY,
        },
        "family_contracts": family_contracts,
        "total_capture_required_units": sum(row["capture_required_rows"] for row in family_contracts),
        "total_required_capture_field_rows": sum(
            row["required_capture_field_rows"] for row in family_contracts
        ),
        "historical_reconstruction_allowed": False,
        "runtime_effect_now": False,
        "live_execution_activation_allowed": False,
        "broker_account_order_history_deal_position_mutation_allowed": False,
        "selected_package_denominator_use_allowed": False,
        "training_use_allowed": False,
        "model_training_allowed": False,
        "final_package_selection_allowed": False,
        "deployment_dossier_allowed": False,
        "vps_handoff_allowed": False,
        "no_leak_boundary": (
            "predecision identity/profile fields may be feature keys only if captured before action; "
            "order intent, tickets, lifecycle, fill/no-fill, cancel/replace, and time-in-force fields "
            "are label or audit fields and must not become as-of features"
        ),
    }
    payload["contract_hash_sha256"] = _packet_hash(payload)
    return payload


def validate_denominator_forward_capture_event(
    event: Mapping[str, Any],
    *,
    requirement_family: str,
    generated_utc: str | None = None,
) -> dict[str, Any]:
    """Validate that one prospective event carries the required source fields."""
    required_fields = required_fields_for_family(requirement_family)
    captured_fields = [
        field_name for field_name in required_fields if not _noneish(_field_value(event, field_name))
    ]
    missing_fields = [field_name for field_name in required_fields if field_name not in captured_fields]
    supplemental_package_context = _supplemental_package_context(event)
    payload = {
        "schema": EVENT_VALIDATION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "generated_utc": generated_utc or _now_iso(),
        "requirement_family": requirement_family,
        "status": "capture_event_complete" if not missing_fields else "capture_event_missing_required_fields",
        "required_capture_fields": list(required_fields),
        "captured_fields": captured_fields,
        "missing_capture_fields": missing_fields,
        "field_contracts": list(field_contracts_for_family(requirement_family)),
        "candidate_id": _field_value(event, "row_bound_candidate_id"),
        "decision_time_utc": _field_value(event, "decision_time_utc"),
        "stable_decision_window_id": _field_value(event, "stable_decision_window_id"),
        "source_event_hash": _field_value(event, "source_event_hash"),
        "ultimate_candidate_package_shadow_status": supplemental_package_context.get(
            "ultimate_candidate_package_shadow_status"
        ),
        "ultimate_candidate_package_shadow_authority_closed": supplemental_package_context.get(
            "ultimate_candidate_package_shadow_authority_closed"
        ),
        "ultimate_candidate_package_shadow_packet_hash": supplemental_package_context.get(
            "ultimate_candidate_package_shadow_packet_hash"
        ),
        "ultimate_candidate_package_shadow_selected_candidate_id": supplemental_package_context.get(
            "ultimate_candidate_package_shadow_selected_candidate_id"
        ),
        "ultimate_candidate_package_selected_candidate_id": supplemental_package_context.get(
            "ultimate_candidate_package_selected_candidate_id"
        ),
        "ultimate_candidate_package_runtime_effect_now": supplemental_package_context.get(
            "ultimate_candidate_package_runtime_effect_now"
        ),
        "ultimate_candidate_package_live_execution_activation_allowed": supplemental_package_context.get(
            "ultimate_candidate_package_live_execution_activation_allowed"
        ),
        "ultimate_candidate_package_final_package_selection_allowed": supplemental_package_context.get(
            "ultimate_candidate_package_final_package_selection_allowed"
        ),
        "ultimate_candidate_package_execution_policy_status": supplemental_package_context.get(
            "ultimate_candidate_package_execution_policy_status"
        ),
        "ultimate_candidate_package_selected_order_type_architecture": supplemental_package_context.get(
            "ultimate_candidate_package_selected_order_type_architecture"
        ),
        "ultimate_candidate_package_execution_order_type_policy_selectable": supplemental_package_context.get(
            "ultimate_candidate_package_execution_order_type_policy_selectable"
        ),
        "ultimate_candidate_package_supplemental_context": supplemental_package_context,
        "historical_reconstruction_allowed": False,
        "selected_package_denominator_use_allowed": False,
        "training_use_allowed": False,
        "model_training_allowed": False,
        "final_package_selection_allowed": False,
        "runtime_effect_now": False,
    }
    payload["packet_hash_sha256"] = _packet_hash(payload)
    return payload


def _counter_payload(counter: Counter[Any]) -> dict[str, int]:
    return {str(key) if key is not None else "null": value for key, value in sorted(counter.items())}


def summarize_denominator_forward_capture_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    generated_utc: str | None = None,
    source_path: str | Path | None = None,
) -> dict[str, Any]:
    """Summarize denominator forward-capture validation rows for review.

    This is a read-only ingestion verifier. Complete capture rows can become
    review candidates for a later denominator-expansion route, but this summary
    never opens denominator, training, final-selection, deployment, or VPS gates.
    """
    generated = generated_utc or _now_iso()
    total_rows = 0
    valid_event_rows = 0
    complete_event_rows = 0
    missing_required_field_event_rows = 0
    invalid_row_reasons: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    append_status_counts: Counter[str] = Counter()
    missing_field_counts: Counter[str] = Counter()
    complete_by_family: Counter[str] = Counter()
    candidate_ids: set[str] = set()
    stable_decision_windows: set[str] = set()
    decision_times: set[str] = set()
    source_hashes: set[str] = set()
    candidate_id_counts: Counter[str] = Counter()
    stable_decision_window_counts: Counter[str] = Counter()
    decision_time_counts: Counter[str] = Counter()
    source_hash_counts: Counter[str] = Counter()

    for row in rows:
        total_rows += 1
        if not isinstance(row, Mapping):
            invalid_row_reasons["row_not_mapping"] += 1
            continue

        schema = row.get("schema")
        if schema != EVENT_VALIDATION_SCHEMA:
            invalid_row_reasons["schema_mismatch"] += 1

        family = row.get("requirement_family")
        if family not in REQUIRED_FIELDS_BY_FAMILY:
            invalid_row_reasons["unknown_requirement_family"] += 1
            family_key = str(family) if family is not None else "null"
        else:
            family_key = str(family)
            expected_fields = list(required_fields_for_family(family_key))
            if row.get("required_capture_fields") != expected_fields:
                invalid_row_reasons["required_fields_mismatch"] += 1
        family_counts[family_key] += 1

        status = str(row.get("status") or "missing_status")
        status_counts[status] += 1
        append_status_counts[str(row.get("append_status") or "not_recorded")] += 1

        missing_fields = row.get("missing_capture_fields") or []
        if not isinstance(missing_fields, list):
            invalid_row_reasons["missing_capture_fields_not_list"] += 1
            missing_fields = []
        for field_name in missing_fields:
            missing_field_counts[str(field_name)] += 1

        if status == "capture_event_complete" and missing_fields:
            invalid_row_reasons["complete_status_with_missing_fields"] += 1
        if status == "capture_event_missing_required_fields" and not missing_fields:
            invalid_row_reasons["missing_status_without_missing_fields"] += 1

        if schema == EVENT_VALIDATION_SCHEMA and family in REQUIRED_FIELDS_BY_FAMILY:
            valid_event_rows += 1
            if status == "capture_event_complete" and not missing_fields:
                complete_event_rows += 1
                complete_by_family[family_key] += 1
            elif status == "capture_event_missing_required_fields":
                missing_required_field_event_rows += 1

        for field_name, target, counter in (
            ("candidate_id", candidate_ids, candidate_id_counts),
            ("stable_decision_window_id", stable_decision_windows, stable_decision_window_counts),
            ("decision_time_utc", decision_times, decision_time_counts),
            ("source_event_hash", source_hashes, source_hash_counts),
        ):
            value = row.get(field_name)
            if not _noneish(value):
                value_key = str(value)
                target.add(value_key)
                counter[value_key] += 1

    invalid_event_rows = total_rows - valid_event_rows
    duplicate_candidate_ids = {key: value for key, value in candidate_id_counts.items() if value > 1}
    duplicate_stable_windows = {
        key: value for key, value in stable_decision_window_counts.items() if value > 1
    }
    duplicate_decision_times = {key: value for key, value in decision_time_counts.items() if value > 1}
    duplicate_source_hashes = {key: value for key, value in source_hash_counts.items() if value > 1}
    payload = {
        "schema": LOG_INGESTION_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "generated_utc": generated,
        "source_path": str(source_path) if source_path is not None else None,
        "status": (
            "capture_log_ingestion_rows_observed_review_required"
            if total_rows
            else "capture_log_ingestion_ready_no_rows_currently_observed"
        ),
        "total_rows": total_rows,
        "valid_event_rows": valid_event_rows,
        "invalid_event_rows": invalid_event_rows,
        "complete_event_rows": complete_event_rows,
        "missing_required_field_event_rows": missing_required_field_event_rows,
        "family_counts": _counter_payload(family_counts),
        "status_counts": _counter_payload(status_counts),
        "append_status_counts": _counter_payload(append_status_counts),
        "missing_capture_field_counts": _counter_payload(missing_field_counts),
        "invalid_row_reason_counts": _counter_payload(invalid_row_reasons),
        "families_with_complete_rows": sorted(complete_by_family),
        "complete_rows_by_family": _counter_payload(complete_by_family),
        "candidate_id_count": len(candidate_ids),
        "stable_decision_window_id_count": len(stable_decision_windows),
        "decision_time_utc_count": len(decision_times),
        "source_event_hash_count": len(source_hashes),
        "duplicate_candidate_id_count": len(duplicate_candidate_ids),
        "duplicate_stable_decision_window_id_count": len(duplicate_stable_windows),
        "duplicate_decision_time_utc_count": len(duplicate_decision_times),
        "duplicate_source_event_hash_count": len(duplicate_source_hashes),
        "duplicate_candidate_id_sample": sorted(duplicate_candidate_ids)[:20],
        "duplicate_stable_decision_window_id_sample": sorted(duplicate_stable_windows)[:20],
        "duplicate_decision_time_utc_sample": sorted(duplicate_decision_times)[:20],
        "duplicate_source_event_hash_sample": sorted(duplicate_source_hashes)[:20],
        "capture_log_has_complete_rows": complete_event_rows > 0,
        "complete_rows_ready_for_denominator_expansion_review": complete_event_rows > 0,
        "review_required_before_any_downstream_use": total_rows > 0,
        "historical_reconstruction_allowed": False,
        "selected_package_denominator_use_allowed": False,
        "denominator_expansion_allowed": False,
        "training_use_allowed": False,
        "model_training_allowed": False,
        "final_package_selection_allowed": False,
        "deployment_dossier_allowed": False,
        "vps_handoff_allowed": False,
        "live_execution_activation_allowed": False,
        "broker_account_order_history_deal_position_mutation_allowed": False,
    }
    payload["packet_hash_sha256"] = _packet_hash(payload)
    return payload


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def build_denominator_forward_capture_expansion_review(
    ingestion_summary: Mapping[str, Any],
    *,
    required_capture_units: int = 0,
    required_capture_field_rows: int = 0,
    generated_utc: str | None = None,
    ingestion_summary_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build the fail-closed review contract before any denominator expansion.

    The review is intentionally conservative about permissions: complete rows
    can only become candidates for a later route-local denominator-expansion
    rerun. This function never opens denominator, training, final-selection,
    deployment, VPS, broker, or runtime gates.
    """
    generated = generated_utc or _now_iso()
    total_rows = _as_int(ingestion_summary.get("total_rows"))
    complete_rows = _as_int(ingestion_summary.get("complete_event_rows"))
    valid_rows = _as_int(ingestion_summary.get("valid_event_rows"))
    invalid_rows = _as_int(ingestion_summary.get("invalid_event_rows"))
    missing_rows = _as_int(ingestion_summary.get("missing_required_field_event_rows"))
    parse_errors = _as_int(ingestion_summary.get("jsonl_parse_error_count"))
    duplicate_source_hashes = _as_int(ingestion_summary.get("duplicate_source_event_hash_count"))
    duplicate_candidate_ids = _as_int(ingestion_summary.get("duplicate_candidate_id_count"))
    duplicate_stable_windows = _as_int(
        ingestion_summary.get("duplicate_stable_decision_window_id_count")
    )
    required_units = _as_int(required_capture_units)
    required_fields = _as_int(required_capture_field_rows)

    blockers: list[str] = []
    if ingestion_summary.get("log_exists") is False and total_rows == 0:
        blockers.append("capture_log_missing_no_rows")
    if parse_errors:
        blockers.append("capture_log_parse_errors")
    if invalid_rows:
        blockers.append("invalid_capture_event_rows")
    if missing_rows:
        blockers.append("missing_required_capture_fields")
    if complete_rows == 0:
        blockers.append("no_complete_capture_rows")
    if duplicate_source_hashes:
        blockers.append("duplicate_source_event_hashes")
    if duplicate_candidate_ids:
        blockers.append("duplicate_candidate_ids_require_row_level_review")
    if duplicate_stable_windows:
        blockers.append("duplicate_stable_decision_windows_require_row_level_review")

    row_quality_blockers = [
        blocker
        for blocker in blockers
        if blocker
        not in {
            "capture_log_missing_no_rows",
            "no_complete_capture_rows",
        }
    ]
    ready_for_rerun = complete_rows > 0 and not row_quality_blockers
    if ready_for_rerun:
        status = "complete_capture_rows_observed_denominator_expansion_rerun_required"
    elif total_rows == 0:
        status = "no_captured_rows_no_denominator_expansion"
    else:
        status = "capture_rows_blocked_before_denominator_expansion"

    payload = {
        "schema": EXPANSION_REVIEW_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "generated_utc": generated,
        "status": status,
        "ingestion_summary_schema": ingestion_summary.get("schema"),
        "ingestion_summary_status": ingestion_summary.get("status"),
        "ingestion_summary_path": str(ingestion_summary_path) if ingestion_summary_path else None,
        "capture_log_path": ingestion_summary.get("log_path") or ingestion_summary.get("source_path"),
        "capture_log_exists": bool(ingestion_summary.get("log_exists")),
        "capture_log_total_rows": total_rows,
        "capture_log_valid_event_rows": valid_rows,
        "capture_log_complete_event_rows": complete_rows,
        "capture_log_missing_required_field_event_rows": missing_rows,
        "capture_log_invalid_event_rows": invalid_rows,
        "capture_log_jsonl_parse_error_count": parse_errors,
        "complete_rows_observed": complete_rows > 0,
        "expansion_review_candidate_rows": complete_rows if ready_for_rerun else 0,
        "complete_rows_require_route_denominator_expansion_rerun": ready_for_rerun,
        "review_required_before_any_downstream_use": total_rows > 0,
        "required_capture_units": required_units,
        "required_capture_field_rows": required_fields,
        "remaining_required_capture_units_after_observed_complete_rows": max(
            required_units - complete_rows,
            0,
        ),
        "family_counts": dict(ingestion_summary.get("family_counts") or {}),
        "complete_rows_by_family": dict(ingestion_summary.get("complete_rows_by_family") or {}),
        "candidate_id_count": _as_int(ingestion_summary.get("candidate_id_count")),
        "stable_decision_window_id_count": _as_int(
            ingestion_summary.get("stable_decision_window_id_count")
        ),
        "decision_time_utc_count": _as_int(ingestion_summary.get("decision_time_utc_count")),
        "source_event_hash_count": _as_int(ingestion_summary.get("source_event_hash_count")),
        "duplicate_candidate_id_count": duplicate_candidate_ids,
        "duplicate_stable_decision_window_id_count": duplicate_stable_windows,
        "duplicate_source_event_hash_count": duplicate_source_hashes,
        "review_blockers": blockers,
        "required_next_artifacts": [
            "row_level_capture_log_review_ledger",
            "source_event_hash_dedup_ledger",
            "captured_row_to_selected_package_candidate_join_ledger",
            "captured_row_to_lifecycle_label_join_ledger",
            "denominator_expansion_replay_or_verifier_result",
            "split_floor_recalculation_after_verified_expansion",
        ],
        "historical_reconstruction_allowed": False,
        "selected_package_denominator_use_allowed": False,
        "denominator_expansion_allowed": False,
        "split_floor_countable": False,
        "clean_label_use_allowed": False,
        "training_use_allowed": False,
        "model_training_allowed": False,
        "final_package_selection_allowed": False,
        "deployment_dossier_allowed": False,
        "vps_handoff_allowed": False,
        "runtime_effect_now": False,
        "live_execution_activation_allowed": False,
        "broker_account_order_history_deal_position_mutation_allowed": False,
    }
    payload["packet_hash_sha256"] = _packet_hash(payload)
    return payload


def build_denominator_forward_capture_row_review(
    rows: Iterable[Mapping[str, Any]],
    *,
    ingestion_summary: Mapping[str, Any] | None = None,
    required_capture_units: int = 0,
    generated_utc: str | None = None,
    log_path: str | Path | None = None,
) -> dict[str, Any]:
    """Classify captured rows before any downstream denominator use.

    The row review is the first route-local artifact after log ingestion. It
    classifies complete capture events, source-event hash dedup status, and
    the still-required selected-package/lifecycle joins. It never opens
    denominator, split-floor, training, final-selection, deployment, or VPS
    gates by itself.
    """
    generated = generated_utc or _now_iso()
    ingestion = ingestion_summary or {}
    materialized_rows = list(rows)
    required_units = _as_int(required_capture_units)

    source_hash_counts: Counter[str] = Counter()
    candidate_id_counts: Counter[str] = Counter()
    stable_window_counts: Counter[str] = Counter()
    for row in materialized_rows:
        if not isinstance(row, Mapping):
            continue
        for field_name, counter in (
            ("source_event_hash", source_hash_counts),
            ("candidate_id", candidate_id_counts),
            ("stable_decision_window_id", stable_window_counts),
        ):
            value = row.get(field_name)
            if not _noneish(value):
                counter[str(value)] += 1

    ledger_rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    missing_field_counts: Counter[str] = Counter()
    duplicate_source_hash_rows = 0
    duplicate_candidate_id_rows = 0
    duplicate_stable_window_rows = 0
    complete_event_rows = 0
    row_review_candidate_rows = 0
    dedup_pass_rows = 0
    selected_package_join_ready_rows = 0

    for row_number, row in enumerate(materialized_rows, start=1):
        if not isinstance(row, Mapping):
            review_status = "invalid_capture_row_not_mapping"
            ledger_row = {
                "schema": ROW_REVIEW_LEDGER_SCHEMA,
                "schema_version": SCHEMA_VERSION,
                "component": COMPONENT,
                "evidence_class": EVIDENCE_CLASS,
                "result_use_status": RESULT_USE_STATUS,
                "generated_utc": generated,
                "row_number": row_number,
                "input_schema": None,
                "requirement_family": None,
                "input_status": "row_not_mapping",
                "review_status": review_status,
                "row_review_candidate": False,
                "capture_event_complete": False,
                "source_event_hash_dedup_passed": False,
                "selected_package_candidate_join_status": "not_attempted_row_invalid",
                "lifecycle_label_join_status": "not_attempted_row_invalid",
                "selected_package_denominator_use_allowed": False,
                "denominator_expansion_allowed": False,
                "split_floor_countable": False,
                "training_use_allowed": False,
                "model_training_allowed": False,
                "final_package_selection_allowed": False,
                "deployment_dossier_allowed": False,
                "vps_handoff_allowed": False,
                "runtime_effect_now": False,
                "live_execution_activation_allowed": False,
                "broker_account_order_history_deal_position_mutation_allowed": False,
            }
            ledger_row["review_row_hash_sha256"] = _packet_hash(ledger_row)
            ledger_rows.append(ledger_row)
            status_counts[review_status] += 1
            continue

        family = row.get("requirement_family")
        family_key = str(family) if family is not None else "null"
        family_counts[family_key] += 1
        schema_ok = row.get("schema") == EVENT_VALIDATION_SCHEMA
        known_family = family in REQUIRED_FIELDS_BY_FAMILY
        expected_fields = list(required_fields_for_family(str(family))) if known_family else []
        required_fields_match = row.get("required_capture_fields") == expected_fields if known_family else False
        missing_fields = row.get("missing_capture_fields") or []
        if not isinstance(missing_fields, list):
            missing_fields = []
        for field_name in missing_fields:
            missing_field_counts[str(field_name)] += 1

        input_status = str(row.get("status") or "missing_status")
        source_hash = row.get("source_event_hash")
        source_hash_key = None if _noneish(source_hash) else str(source_hash)
        candidate_id = row.get("candidate_id")
        candidate_key = None if _noneish(candidate_id) else str(candidate_id)
        stable_window = row.get("stable_decision_window_id")
        stable_window_key = None if _noneish(stable_window) else str(stable_window)
        duplicate_source_hash = bool(source_hash_key and source_hash_counts[source_hash_key] > 1)
        duplicate_candidate_id = bool(candidate_key and candidate_id_counts[candidate_key] > 1)
        duplicate_stable_window = bool(
            stable_window_key and stable_window_counts[stable_window_key] > 1
        )
        if duplicate_source_hash:
            duplicate_source_hash_rows += 1
        if duplicate_candidate_id:
            duplicate_candidate_id_rows += 1
        if duplicate_stable_window:
            duplicate_stable_window_rows += 1

        capture_event_complete = (
            schema_ok
            and known_family
            and required_fields_match
            and input_status == "capture_event_complete"
            and not missing_fields
        )
        if capture_event_complete:
            complete_event_rows += 1

        if not schema_ok:
            review_status = "invalid_capture_event_schema"
        elif not known_family:
            review_status = "invalid_capture_event_unknown_family"
        elif not required_fields_match:
            review_status = "invalid_capture_event_required_fields_mismatch"
        elif input_status == "capture_event_missing_required_fields":
            review_status = "missing_required_fields_not_countable"
        elif input_status != "capture_event_complete":
            review_status = "invalid_capture_event_status"
        elif missing_fields:
            review_status = "missing_required_fields_not_countable"
        elif duplicate_source_hash:
            review_status = "duplicate_source_event_hash_blocked"
        else:
            review_status = "captured_row_requires_selected_package_and_lifecycle_joins"
            row_review_candidate_rows += 1
            dedup_pass_rows += 1
            selected_package_join_ready_rows += 1

        ledger_row = {
            "schema": ROW_REVIEW_LEDGER_SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "component": COMPONENT,
            "evidence_class": EVIDENCE_CLASS,
            "result_use_status": RESULT_USE_STATUS,
            "generated_utc": generated,
            "row_number": row_number,
            "input_schema": row.get("schema"),
            "requirement_family": family,
            "input_status": input_status,
            "review_status": review_status,
            "row_review_candidate": review_status
            == "captured_row_requires_selected_package_and_lifecycle_joins",
            "capture_event_complete": capture_event_complete,
            "required_capture_fields": expected_fields,
            "missing_capture_fields": list(missing_fields),
            "candidate_id": candidate_id,
            "stable_decision_window_id": stable_window,
            "decision_time_utc": row.get("decision_time_utc"),
            "source_event_hash": source_hash,
            "source_event_hash_occurrence_count": source_hash_counts.get(source_hash_key, 0)
            if source_hash_key
            else 0,
            "source_event_hash_dedup_status": (
                "duplicate_source_event_hash_blocked"
                if duplicate_source_hash
                else "source_event_hash_unique"
                if source_hash_key
                else "source_event_hash_missing"
            ),
            "source_event_hash_dedup_passed": bool(capture_event_complete and source_hash_key and not duplicate_source_hash),
            "candidate_id_occurrence_count": candidate_id_counts.get(candidate_key, 0)
            if candidate_key
            else 0,
            "stable_decision_window_id_occurrence_count": stable_window_counts.get(
                stable_window_key,
                0,
            )
            if stable_window_key
            else 0,
            "candidate_id_duplicate_observed": duplicate_candidate_id,
            "stable_decision_window_id_duplicate_observed": duplicate_stable_window,
            "selected_package_candidate_join_status": (
                "not_attempted_downstream_artifact_required"
                if review_status == "captured_row_requires_selected_package_and_lifecycle_joins"
                else "not_attempted_row_not_join_ready"
            ),
            "lifecycle_label_join_status": (
                "not_attempted_downstream_artifact_required"
                if review_status == "captured_row_requires_selected_package_and_lifecycle_joins"
                else "not_attempted_row_not_join_ready"
            ),
            "selected_package_denominator_use_allowed": False,
            "denominator_expansion_allowed": False,
            "split_floor_countable": False,
            "clean_label_use_allowed": False,
            "training_use_allowed": False,
            "model_training_allowed": False,
            "final_package_selection_allowed": False,
            "deployment_dossier_allowed": False,
            "vps_handoff_allowed": False,
            "runtime_effect_now": False,
            "live_execution_activation_allowed": False,
            "broker_account_order_history_deal_position_mutation_allowed": False,
        }
        ledger_row["review_row_hash_sha256"] = _packet_hash(ledger_row)
        ledger_rows.append(ledger_row)
        status_counts[review_status] += 1

    parse_errors = _as_int(ingestion.get("jsonl_parse_error_count"))
    invalid_events = _as_int(ingestion.get("invalid_event_rows"))
    missing_events = _as_int(ingestion.get("missing_required_field_event_rows"))
    blockers: list[str] = []
    if not materialized_rows:
        blockers.append("no_capture_rows")
    if parse_errors:
        blockers.append("capture_log_parse_errors")
    if invalid_events or any(status.startswith("invalid_capture") for status in status_counts):
        blockers.append("invalid_capture_event_rows")
    if missing_events or status_counts.get("missing_required_fields_not_countable"):
        blockers.append("missing_required_capture_fields")
    if duplicate_source_hash_rows:
        blockers.append("duplicate_source_event_hashes")
    if selected_package_join_ready_rows:
        blockers.extend(
            [
                "selected_package_candidate_join_not_built",
                "lifecycle_label_join_not_built",
                "denominator_expansion_rerun_not_built",
                "split_floor_recalculation_not_built",
            ]
        )

    if not materialized_rows:
        status = "no_capture_rows_no_row_review_candidates"
    elif duplicate_source_hash_rows:
        status = "capture_rows_blocked_by_source_event_hash_duplicates"
    elif parse_errors or invalid_events or missing_events or any(
        row["review_status"].startswith("invalid_capture")
        or row["review_status"] == "missing_required_fields_not_countable"
        for row in ledger_rows
    ):
        status = "capture_rows_blocked_before_downstream_join_review"
    elif selected_package_join_ready_rows:
        status = "captured_rows_require_downstream_join_review"
    else:
        status = "capture_rows_reviewed_no_downstream_candidates"

    summary = {
        "schema": ROW_REVIEW_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "generated_utc": generated,
        "status": status,
        "log_path": str(log_path) if log_path is not None else ingestion.get("log_path"),
        "ingestion_summary_schema": ingestion.get("schema"),
        "ingestion_summary_status": ingestion.get("status"),
        "capture_log_total_rows": _as_int(ingestion.get("total_rows")),
        "capture_log_valid_event_rows": _as_int(ingestion.get("valid_event_rows")),
        "capture_log_complete_event_rows": _as_int(ingestion.get("complete_event_rows")),
        "capture_log_missing_required_field_event_rows": missing_events,
        "capture_log_invalid_event_rows": invalid_events,
        "capture_log_jsonl_parse_error_count": parse_errors,
        "row_review_ledger_rows": len(ledger_rows),
        "row_review_candidate_rows": row_review_candidate_rows,
        "complete_capture_event_rows_reviewed": complete_event_rows,
        "source_event_hash_unique_count": sum(1 for count in source_hash_counts.values() if count == 1),
        "source_event_hash_duplicate_key_count": sum(1 for count in source_hash_counts.values() if count > 1),
        "source_event_hash_duplicate_row_count": duplicate_source_hash_rows,
        "source_event_hash_dedup_pass_rows": dedup_pass_rows,
        "candidate_id_duplicate_row_count": duplicate_candidate_id_rows,
        "stable_decision_window_id_duplicate_row_count": duplicate_stable_window_rows,
        "captured_row_to_selected_package_candidate_join_ready_rows": selected_package_join_ready_rows,
        "captured_row_to_selected_package_candidate_join_rows": 0,
        "captured_row_to_lifecycle_label_join_ready_rows": 0,
        "captured_row_to_lifecycle_label_join_rows": 0,
        "denominator_expansion_candidate_rows": 0,
        "split_floor_recalculation_ready_rows": 0,
        "required_capture_units": required_units,
        "remaining_required_capture_units_after_row_review_passed": max(
            required_units - dedup_pass_rows,
            0,
        ),
        "family_counts": _counter_payload(family_counts),
        "review_status_counts": _counter_payload(status_counts),
        "missing_capture_field_counts": _counter_payload(missing_field_counts),
        "review_blockers": blockers,
        "required_next_artifacts": [
            "captured_row_to_selected_package_candidate_join_ledger",
            "captured_row_to_lifecycle_label_join_ledger",
            "denominator_expansion_replay_or_verifier_result",
            "split_floor_recalculation_after_verified_expansion",
        ],
        "historical_reconstruction_allowed": False,
        "selected_package_denominator_use_allowed": False,
        "denominator_expansion_allowed": False,
        "split_floor_countable": False,
        "clean_label_use_allowed": False,
        "training_use_allowed": False,
        "model_training_allowed": False,
        "final_package_selection_allowed": False,
        "deployment_dossier_allowed": False,
        "vps_handoff_allowed": False,
        "runtime_effect_now": False,
        "live_execution_activation_allowed": False,
        "broker_account_order_history_deal_position_mutation_allowed": False,
    }
    summary["packet_hash_sha256"] = _packet_hash(summary)
    return {
        "summary": summary,
        "ledger_rows": ledger_rows,
    }


def _string_set(values: Iterable[Any]) -> set[str]:
    return {str(value) for value in values if not _noneish(value)}


def build_denominator_forward_capture_downstream_join_review(
    row_review_rows: Iterable[Mapping[str, Any]],
    *,
    selected_package_candidate_ids: Iterable[Any] = (),
    selected_package_decision_window_ids: Iterable[Any] = (),
    lifecycle_label_candidate_ids: Iterable[Any] = (),
    lifecycle_label_decision_window_ids: Iterable[Any] = (),
    generated_utc: str | None = None,
) -> dict[str, Any]:
    """Join row-reviewed capture events to selected-package and lifecycle keys.

    This is the downstream fail-closed gate after row review/dedup. It records
    whether a captured row can be matched to selected-package candidate/window
    keys and lifecycle label keys. Even rows that match both sides remain only
    candidates for a later denominator-expansion rerun and split-floor
    recalculation.
    """
    generated = generated_utc or _now_iso()
    selected_candidate_keys = _string_set(selected_package_candidate_ids)
    selected_window_keys = _string_set(selected_package_decision_window_ids)
    lifecycle_candidate_keys = _string_set(lifecycle_label_candidate_ids)
    lifecycle_window_keys = _string_set(lifecycle_label_decision_window_ids)
    rows = list(row_review_rows)

    selected_rows: list[dict[str, Any]] = []
    lifecycle_rows: list[dict[str, Any]] = []
    selected_status_counts: Counter[str] = Counter()
    lifecycle_status_counts: Counter[str] = Counter()
    row_review_candidate_rows = 0
    dedup_pass_rows = 0
    selected_join_rows = 0
    lifecycle_join_rows = 0
    denominator_candidate_rows = 0

    for index, row in enumerate(rows, start=1):
        row_number = row.get("row_number", index) if isinstance(row, Mapping) else index
        candidate_id = row.get("candidate_id") if isinstance(row, Mapping) else None
        stable_window = row.get("stable_decision_window_id") if isinstance(row, Mapping) else None
        source_event_hash = row.get("source_event_hash") if isinstance(row, Mapping) else None
        candidate_key = None if _noneish(candidate_id) else str(candidate_id)
        stable_window_key = None if _noneish(stable_window) else str(stable_window)
        review_candidate = bool(isinstance(row, Mapping) and row.get("row_review_candidate") is True)
        dedup_pass = bool(
            isinstance(row, Mapping) and row.get("source_event_hash_dedup_passed") is True
        )
        if review_candidate:
            row_review_candidate_rows += 1
        if dedup_pass:
            dedup_pass_rows += 1

        selected_candidate_match = bool(candidate_key and candidate_key in selected_candidate_keys)
        selected_window_match = bool(stable_window_key and stable_window_key in selected_window_keys)
        lifecycle_candidate_match = bool(candidate_key and candidate_key in lifecycle_candidate_keys)
        lifecycle_window_match = bool(stable_window_key and stable_window_key in lifecycle_window_keys)
        selected_joined = review_candidate and dedup_pass and (
            selected_candidate_match or selected_window_match
        )
        lifecycle_joined = review_candidate and dedup_pass and (
            lifecycle_candidate_match or lifecycle_window_match
        )
        if selected_joined:
            selected_join_rows += 1
        if lifecycle_joined:
            lifecycle_join_rows += 1
        denominator_candidate = selected_joined and lifecycle_joined
        if denominator_candidate:
            denominator_candidate_rows += 1

        if not review_candidate:
            selected_status = "not_row_review_candidate"
            lifecycle_status = "not_row_review_candidate"
        elif not dedup_pass:
            selected_status = "source_event_hash_dedup_not_passed"
            lifecycle_status = "source_event_hash_dedup_not_passed"
        else:
            selected_status = (
                "selected_package_candidate_joined"
                if selected_joined
                else "selected_package_candidate_join_missing"
            )
            lifecycle_status = (
                "lifecycle_label_joined" if lifecycle_joined else "lifecycle_label_join_missing"
            )
        selected_status_counts[selected_status] += 1
        lifecycle_status_counts[lifecycle_status] += 1

        common = {
            "schema_version": SCHEMA_VERSION,
            "component": COMPONENT,
            "evidence_class": EVIDENCE_CLASS,
            "result_use_status": RESULT_USE_STATUS,
            "generated_utc": generated,
            "row_number": row_number,
            "row_review_status": row.get("review_status") if isinstance(row, Mapping) else None,
            "row_review_candidate": review_candidate,
            "source_event_hash_dedup_passed": dedup_pass,
            "candidate_id": candidate_id,
            "stable_decision_window_id": stable_window,
            "decision_time_utc": row.get("decision_time_utc") if isinstance(row, Mapping) else None,
            "source_event_hash": source_event_hash,
            "selected_package_denominator_use_allowed": False,
            "denominator_expansion_allowed": False,
            "split_floor_countable": False,
            "clean_label_use_allowed": False,
            "training_use_allowed": False,
            "model_training_allowed": False,
            "final_package_selection_allowed": False,
            "deployment_dossier_allowed": False,
            "vps_handoff_allowed": False,
            "runtime_effect_now": False,
            "live_execution_activation_allowed": False,
            "broker_account_order_history_deal_position_mutation_allowed": False,
        }
        selected_row = {
            **common,
            "schema": SELECTED_PACKAGE_JOIN_LEDGER_SCHEMA,
            "join_status": selected_status,
            "selected_package_candidate_joined": selected_joined,
            "matched_by_candidate_id": selected_candidate_match,
            "matched_by_stable_decision_window_id": selected_window_match,
            "selected_package_candidate_lookup_count": len(selected_candidate_keys),
            "selected_package_decision_window_lookup_count": len(selected_window_keys),
            "requires_lifecycle_label_join": selected_joined,
            "denominator_expansion_candidate": denominator_candidate,
        }
        selected_row["join_row_hash_sha256"] = _packet_hash(selected_row)
        selected_rows.append(selected_row)

        lifecycle_row = {
            **common,
            "schema": LIFECYCLE_LABEL_JOIN_LEDGER_SCHEMA,
            "join_status": lifecycle_status,
            "lifecycle_label_joined": lifecycle_joined,
            "matched_by_candidate_id": lifecycle_candidate_match,
            "matched_by_stable_decision_window_id": lifecycle_window_match,
            "lifecycle_label_candidate_lookup_count": len(lifecycle_candidate_keys),
            "lifecycle_label_decision_window_lookup_count": len(lifecycle_window_keys),
            "requires_selected_package_candidate_join": lifecycle_joined,
            "denominator_expansion_candidate": denominator_candidate,
        }
        lifecycle_row["join_row_hash_sha256"] = _packet_hash(lifecycle_row)
        lifecycle_rows.append(lifecycle_row)

    blockers: list[str] = []
    if not rows:
        blockers.append("no_row_review_rows")
    if row_review_candidate_rows == 0:
        blockers.append("no_row_review_candidates")
    if dedup_pass_rows == 0:
        blockers.append("no_source_event_hash_dedup_pass_rows")
    if row_review_candidate_rows and selected_join_rows == 0:
        blockers.append("selected_package_candidate_join_missing")
    if row_review_candidate_rows and lifecycle_join_rows == 0:
        blockers.append("lifecycle_label_join_missing")
    if denominator_candidate_rows:
        blockers.extend(
            [
                "denominator_expansion_rerun_not_built",
                "split_floor_recalculation_not_built",
            ]
        )

    if not rows:
        status = "no_row_review_rows_no_downstream_join_candidates"
    elif row_review_candidate_rows == 0:
        status = "row_review_has_no_downstream_join_candidates"
    elif selected_join_rows == 0 or lifecycle_join_rows == 0:
        status = "captured_rows_missing_downstream_joins"
    elif denominator_candidate_rows:
        status = "captured_rows_joined_denominator_expansion_rerun_required"
    else:
        status = "captured_rows_reviewed_no_denominator_candidates"

    summary = {
        "schema": DOWNSTREAM_JOIN_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "generated_utc": generated,
        "status": status,
        "row_review_ledger_rows": len(rows),
        "row_review_candidate_rows": row_review_candidate_rows,
        "source_event_hash_dedup_pass_rows": dedup_pass_rows,
        "selected_package_candidate_lookup_count": len(selected_candidate_keys),
        "selected_package_decision_window_lookup_count": len(selected_window_keys),
        "lifecycle_label_candidate_lookup_count": len(lifecycle_candidate_keys),
        "lifecycle_label_decision_window_lookup_count": len(lifecycle_window_keys),
        "captured_row_to_selected_package_candidate_join_ledger_rows": len(selected_rows),
        "captured_row_to_selected_package_candidate_join_rows": selected_join_rows,
        "captured_row_to_lifecycle_label_join_ledger_rows": len(lifecycle_rows),
        "captured_row_to_lifecycle_label_join_rows": lifecycle_join_rows,
        "denominator_expansion_candidate_rows": denominator_candidate_rows,
        "split_floor_recalculation_ready_rows": 0,
        "selected_package_join_status_counts": _counter_payload(selected_status_counts),
        "lifecycle_label_join_status_counts": _counter_payload(lifecycle_status_counts),
        "review_blockers": blockers,
        "required_next_artifacts": [
            "denominator_expansion_replay_or_verifier_result",
            "split_floor_recalculation_after_verified_expansion",
        ],
        "historical_reconstruction_allowed": False,
        "selected_package_denominator_use_allowed": False,
        "denominator_expansion_allowed": False,
        "split_floor_countable": False,
        "clean_label_use_allowed": False,
        "training_use_allowed": False,
        "model_training_allowed": False,
        "final_package_selection_allowed": False,
        "deployment_dossier_allowed": False,
        "vps_handoff_allowed": False,
        "runtime_effect_now": False,
        "live_execution_activation_allowed": False,
        "broker_account_order_history_deal_position_mutation_allowed": False,
    }
    summary["packet_hash_sha256"] = _packet_hash(summary)
    return {
        "summary": summary,
        "selected_package_join_rows": selected_rows,
        "lifecycle_label_join_rows": lifecycle_rows,
    }


def summarize_denominator_forward_capture_log(
    path: str | Path,
    *,
    generated_utc: str | None = None,
) -> dict[str, Any]:
    """Read and summarize a denominator forward-capture JSONL log if present."""
    target = Path(path)
    rows: list[Mapping[str, Any]] = []
    parse_error_rows: list[dict[str, Any]] = []
    line_count = 0
    nonblank_line_count = 0

    if target.exists():
        with target.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line_count += 1
                if not line.strip():
                    continue
                nonblank_line_count += 1
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    parse_error_rows.append(
                        {
                            "line_number": line_number,
                            "error": str(exc),
                        }
                    )

    summary = summarize_denominator_forward_capture_rows(
        rows,
        generated_utc=generated_utc,
        source_path=target,
    )
    summary.update(
        {
            "log_path": str(target),
            "log_exists": target.exists(),
            "line_count": line_count,
            "nonblank_line_count": nonblank_line_count,
            "jsonl_parse_error_count": len(parse_error_rows),
            "jsonl_parse_error_rows": parse_error_rows[:20],
        }
    )
    if not target.exists():
        summary["status"] = "capture_log_missing_no_rows_currently_observed"
    elif not rows and not parse_error_rows:
        summary["status"] = "capture_log_empty_no_rows_currently_observed"
    elif parse_error_rows:
        summary["status"] = "capture_log_parse_errors_review_required"
    summary["packet_hash_sha256"] = _packet_hash(summary)
    return summary


def _config_value(config: Mapping[str, Any], key: str, default: Any) -> Any:
    if not config:
        return default
    return config.get(key, default)


def _append_jsonl(path: str | Path, row: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(_json_safe(row), sort_keys=True, separators=(",", ":")))
        handle.write("\n")


def record_denominator_forward_capture_event(
    event: Mapping[str, Any],
    *,
    requirement_family: str,
    runtime_config: Mapping[str, Any] | None = None,
    log_path: str | Path | None = None,
    generated_utc: str | None = None,
) -> dict[str, Any]:
    """Validate and optionally append one denominator forward-capture event.

    The writer is default-off and observation-only. Append failures are recorded
    in the returned validation packet and logged, but never raised.
    """
    config = runtime_config or {}
    validation = validate_denominator_forward_capture_event(
        event,
        requirement_family=requirement_family,
        generated_utc=generated_utc,
    )
    validation["capture_writer"] = {
        "enabled_config_key": ENABLED_CONFIG_KEY,
        "log_enabled_config_key": LOG_ENABLED_CONFIG_KEY,
        "log_path_config_key": LOG_PATH_CONFIG_KEY,
        "default_log_path": DEFAULT_LOG_PATH,
        "runtime_effect_now": False,
        "broker_account_order_history_deal_position_mutation_allowed": False,
    }
    enabled = bool(_config_value(config, ENABLED_CONFIG_KEY, False))
    log_enabled = bool(_config_value(config, LOG_ENABLED_CONFIG_KEY, False))
    if not enabled:
        validation["append_status"] = "disabled_by_runtime_config"
        return validation
    if not log_enabled:
        validation["append_status"] = "log_disabled_by_runtime_config"
        return validation

    target_path = log_path or _config_value(config, LOG_PATH_CONFIG_KEY, DEFAULT_LOG_PATH)
    validation["capture_log_path"] = str(target_path)
    try:
        validation["append_status"] = "appended"
        _append_jsonl(target_path, validation)
    except Exception as exc:  # noqa: BLE001 - capture must not affect runtime flow.
        validation["append_status"] = "append_failed_capture_retained_in_return_packet"
        validation["append_error"] = str(exc)
        logger.warning("Denominator forward-capture append failed: %s", exc, exc_info=True)
    return validation
