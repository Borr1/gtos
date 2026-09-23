"""LiveDecisionPacketV4 source-truth capture.

This module builds a schema-stable packet from the existing vNext candidate
packet and runtime record. It is capture-only: it never calls broker APIs,
changes orders, mutates credentials, or affects routing decisions.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "LiveDecisionPacketV4"
PACKET_SCHEMA_VERSION = "live_decision_packet_v4_2026_06_04"
DEFAULT_LOG_PATH = "shadow_logs/live_decision_packets_v4.jsonl"
RESULT_USE_STATUS = "RESULT_MATERIALIZATION_REQUIRED"
EVIDENCE_CLASS = "production_code_integration_source_bound_capture_v4"
DEFERRED_PACKET_HASH_PREIMAGE_KEY = (
    "_replay_deferred_packet_hash_preimage_bytes"
)

FORBIDDEN_SURFACE_BOUNDARY = {
    "live_trading_deployment": False,
    "broker_account_order_history_deal_position_mutation": False,
    "credential_mutation_or_disclosure": False,
    "paid_api_vendor_call": False,
    "active_vps_process_change": False,
    "remote_push": False,
}

REQUIRED_FIELD_GROUPS = (
    "candidate_identity_and_source_namespace",
    "source_window_hash_and_no_leak_contract",
    "selector_allocator_final_say",
    "ultimate_candidate_package_selector_scheduler_surface",
    "execution_geometry_policy_and_order_readiness",
    "cost_slippage_swap_broker_constraints",
    "same_symbol_lifecycle_and_ticket_state",
    "probability_debate_numeric_theses",
    "follow_avoid_mixed_numeric_confluence",
    "broker_dual_broker_local_truth",
    "halt_authority_and_runtime_control",
    "ai_reliability_and_cost_control",
    "feature_label_forward_capture_contract",
)

SEMANTIC_OWNERSHIP_REQUIREMENTS = {
    "same_symbol_lifecycle": (
        "same_symbol_same_instrument_lifecycle_v4",
        (
            "scale/reduce/close/reverse/ticket-bound lifecycle fields are captured "
            "or marked prospective source gaps"
        ),
    ),
    "probability_debate": (
        "probability_debate_team_engine_v4",
        (
            "numeric theses for long/short/no_trade/wait/scale/reduce/close/"
            "reverse are captured or marked prospective source gaps"
        ),
    ),
    "follow_avoid_mixed_numeric_confluence": (
        "follow_avoid_mixed_numeric_confluence_v4",
        "FOLLOW/AVOID/MIXED is numeric evidence, not trade permission",
    ),
    "scheduler_allocator": (
        "scheduler_v4_best_trade_allocator",
        "candidate set, alternatives, open/pending competition, and zero-trade value",
    ),
    "ultimate_candidate_package": (
        "ultimate_candidate_package_shadow_selector_scheduler_surface",
        (
            "82-sleeve ultimate package registry, selector shadow packet, scheduler "
            "shadow packet, and closed final/live/broker-mutation gates"
        ),
    ),
    "execution": (
        "execution_manager_v4",
        "order readiness, entry mode, tickets, and source-local execution state",
    ),
    "cost_broker": (
        "cost_swap_slippage_broker_constraint_engine",
        "spread/slippage/commission/swap/session/spec/cash-conversion source state",
    ),
    "runtime_halt": (
        "runtime_control_atomic_halt_safety",
        "halt/process/final-say authority fields captured without mutating runtime",
    ),
    "ml_feature_label": (
        "wave4_wave5_ml_owner",
        "as-of feature capture and label requirements are declared, not backfilled",
    ),
}

POST_DECISION_ROOTS = {
    "execution",
    "final_order_decision",
    "lifecycle",
    "same_symbol_lifecycle_and_ticket_state",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def _json_hash_default(value: Any) -> Any:
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    if isinstance(value, set):
        return list(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def _json_material_bytes(value: Any) -> bytes:
    try:
        material = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            default=_json_hash_default,
        )
    except TypeError:
        # Compatibility fallback for non-string or otherwise non-canonical
        # mapping keys outside the packet builder's schema-stable hot path.
        material = json.dumps(
            _json_safe(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
    return material.encode("utf-8")


def _json_sha256(value: Any) -> str:
    return hashlib.sha256(_json_material_bytes(value)).hexdigest()


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _get_path(mapping: dict[str, Any], *path: str) -> Any:
    cur: Any = mapping
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _component_from_pipeline(pipeline: dict[str, Any], *names: str) -> dict[str, Any]:
    for name in names:
        value = pipeline.get(name)
        if isinstance(value, dict) and value:
            return value
    return {}


def _normalize_action_key(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip().lower().replace("-", "_")
    aliases = {
        "notrade": "no_trade",
        "none": "no_trade",
        "stand_aside": "no_trade",
        "hold": "wait",
        "buy": "long",
        "sell": "short",
        "scale_in": "scale",
        "reduce_existing": "reduce",
        "close_existing": "close",
        "close_and_reverse": "reverse",
    }
    return aliases.get(text, text)


def _first_status_source(sources: Any) -> dict[str, Any]:
    if isinstance(sources, list):
        for source in sources:
            if isinstance(source, dict) and source:
                return source
    return {}


def _field_status(value: Any, *, missing_reason: str) -> dict[str, Any]:
    return {
        "value": _json_safe(value),
        "source_status": "captured" if value not in (None, "", [], {}) else "source_gap",
        "missing_reason": None if value not in (None, "", [], {}) else missing_reason,
    }


def _numeric_theses_from_pipeline(pipeline: dict[str, Any]) -> dict[str, Any]:
    debate = _component_from_pipeline(
        pipeline,
        "probability_debate_v4",
        "probability_debate_team_engine_v4",
        "probability_debate",
        "gtos_vnext_probability_debate",
    )
    theses = _dict(debate.get("numeric_theses"))
    for thesis in debate.get("theses") or ():
        if not isinstance(thesis, dict):
            continue
        action_key = _normalize_action_key(thesis.get("action"))
        if action_key and action_key not in theses:
            theses[action_key] = thesis
    selected = debate.get("selected_thesis")
    if isinstance(selected, dict):
        action_key = _normalize_action_key(selected.get("action") or debate.get("selected_action"))
        if action_key and action_key not in theses:
            theses[action_key] = selected
    result: dict[str, Any] = {}
    for action in (
        "long",
        "short",
        "no_trade",
        "wait",
        "scale",
        "reduce",
        "close",
        "reverse",
    ):
        value = theses.get(action)
        result[action] = {
            "probability": _get_path(value, "probability") if isinstance(value, dict) else None,
            "ev": _first_present(
                _get_path(value, "ev"),
                _get_path(value, "EV"),
                _get_path(value, "ev_r"),
            )
            if isinstance(value, dict)
            else None,
            "uncertainty": (
                _get_path(value, "uncertainty") if isinstance(value, dict) else None
            ),
            "source_status": "captured" if isinstance(value, dict) else "prospective_capture_required",
            "missing_reason": (
                None
                if isinstance(value, dict)
                else "probability_debate_team_engine_v4_not_yet_emitting_this_thesis"
            ),
        }
    return result


def _confluence_from_pipeline(pipeline: dict[str, Any]) -> dict[str, Any]:
    confluence = _component_from_pipeline(
        pipeline,
        "follow_avoid_mixed_numeric_confluence_v4",
        "numeric_confluence_v4",
        "numeric_confluence",
        "follow_avoid_mixed_numeric_confluence",
        "gtos_vnext_follow_avoid_mixed",
    )
    source = _first_status_source(confluence.get("sources"))
    return {
        "classification": _field_status(
            _first_present(
                confluence.get("classification"),
                confluence.get("stance"),
                source.get("stance"),
                source.get("decision"),
            ),
            missing_reason="numeric_confluence_classification_not_yet_emitted",
        ),
        "direction": _field_status(
            _first_present(confluence.get("direction"), source.get("direction")),
            missing_reason="numeric_confluence_direction_not_yet_emitted",
        ),
        "strength": _field_status(
            _first_present(confluence.get("strength"), source.get("strength")),
            missing_reason="numeric_confluence_strength_not_yet_emitted",
        ),
        "confidence": _field_status(
            _first_present(confluence.get("confidence"), source.get("confidence")),
            missing_reason="numeric_confluence_confidence_not_yet_emitted",
        ),
        "reliability_history": _field_status(
            _first_present(
                confluence.get("reliability_history"),
                confluence.get("reliability"),
                source.get("reliability_history"),
                source.get("reliability"),
            ),
            missing_reason="numeric_confluence_reliability_history_not_yet_emitted",
        ),
        "evidence_class": _field_status(
            _first_present(confluence.get("evidence_class"), source.get("evidence_class")),
            missing_reason="numeric_confluence_evidence_class_not_yet_emitted",
        ),
        "freshness": _field_status(
            _first_present(confluence.get("freshness"), source.get("freshness")),
            missing_reason="numeric_confluence_freshness_not_yet_emitted",
        ),
        "cost_sensitivity": _field_status(
            _first_present(confluence.get("cost_sensitivity"), source.get("cost_sensitivity")),
            missing_reason="numeric_confluence_cost_sensitivity_not_yet_emitted",
        ),
        "conflict_reason": _field_status(
            _first_present(confluence.get("conflict_reason"), source.get("conflict_reason")),
            missing_reason="numeric_confluence_conflict_reason_not_yet_emitted",
        ),
        "source_completeness": _field_status(
            _first_present(
                confluence.get("source_completeness"),
                source.get("source_completeness"),
            ),
            missing_reason="numeric_confluence_source_completeness_not_yet_emitted",
        ),
        "permission_rule": (
            "FOLLOW_is_not_automatic_trade_permission_AVOID_requires_invalidation_type_"
            "MIXED_requires_structured_disagreement"
        ),
        "avoid_invalidation_type": _field_status(
            _first_present(
                confluence.get("avoid_invalidation_type"),
                source.get("avoid_invalidation_type"),
                source.get("invalidation_type"),
            ),
            missing_reason="avoid_invalidation_type_not_yet_emitted",
        ),
        "mixed_disagreement": _field_status(
            _first_present(
                confluence.get("mixed_disagreement"),
                source.get("mixed_disagreement"),
                source.get("disagreement_state"),
            ),
            missing_reason="mixed_structured_disagreement_not_yet_emitted",
        ),
    }


def _scheduler_from_pipeline(pipeline: dict[str, Any]) -> dict[str, Any]:
    return _component_from_pipeline(
        pipeline,
        "scheduler_v4_best_trade_allocator",
        "scheduler_v4",
        "gtos_vnext_scheduler_v4",
    )


def _ultimate_candidate_package_from_pipeline(
    pipeline: dict[str, Any],
    runtime_config: dict[str, Any],
) -> dict[str, Any]:
    selector = _component_from_pipeline(
        pipeline,
        "selector_v4",
        "gtos_vnext_selector_v4",
        "gtos_vnext_selector_v4_packet",
    )
    scheduler = _scheduler_from_pipeline(pipeline)
    selector_packet = _first_present(
        _get_path(selector, "component_scores", "ultimate_candidate_package"),
        selector.get("ultimate_candidate_package"),
        _get_path(pipeline, "gtos_vnext_selector_v4_packet", "component_scores", "ultimate_candidate_package"),
        _get_path(pipeline, "selector_v4_packet", "component_scores", "ultimate_candidate_package"),
    )
    scheduler_packet = _first_present(
        scheduler.get("ultimate_candidate_package_shadow"),
        _get_path(scheduler, "decision", "ultimate_candidate_package_shadow"),
        pipeline.get("ultimate_candidate_package_shadow"),
    )
    selector_packet = _dict(selector_packet)
    scheduler_packet = _dict(scheduler_packet)
    execution_policy_packet = _dict(
        _first_present(
            scheduler_packet.get("execution_policy_shadow"),
            _get_path(scheduler_packet, "decision", "execution_policy_shadow"),
            pipeline.get("ultimate_candidate_package_execution_policy_shadow"),
        )
    )

    gate_violations: list[str] = []
    for source_name, packet in (
        ("selector_packet", selector_packet),
        ("scheduler_packet", scheduler_packet),
        ("execution_policy_packet", execution_policy_packet),
    ):
        if not packet:
            continue
        for gate in (
            "runtime_effect_now",
            "candidate_use_allowed_now",
            "selected_package_denominator_use_allowed",
            "denominator_expansion_allowed",
            "clean_label_use_allowed",
            "training_use_allowed",
            "model_training_allowed",
            "final_package_selection_allowed",
            "deployment_dossier_allowed",
            "vps_handoff_allowed",
            "live_execution_activation_allowed",
            "broker_account_order_history_deal_position_mutation_allowed",
            "broker_operation",
            "paid_api_or_vendor_call",
        ):
            if packet.get(gate) is not False and gate in packet:
                gate_violations.append(f"{source_name}.{gate}")
        if packet.get("order_calls") not in (None, False, 0):
            gate_violations.append(f"{source_name}.order_calls")
    config_final_selected = runtime_config.get("ultimate_candidate_package_final_package_selected")
    config_apply = runtime_config.get("ultimate_candidate_package_apply_to_execution")
    config_live = runtime_config.get("ultimate_candidate_package_live_activation_allowed")
    for config_key, value in (
        ("ultimate_candidate_package_final_package_selected", config_final_selected),
        ("ultimate_candidate_package_apply_to_execution", config_apply),
        ("ultimate_candidate_package_live_activation_allowed", config_live),
    ):
        if value is True:
            gate_violations.append(f"runtime_config.{config_key}")

    missing_fields: list[str] = []
    if not selector_packet:
        missing_fields.append("selector_v4.component_scores.ultimate_candidate_package")
    if not scheduler_packet:
        missing_fields.append("scheduler_v4.ultimate_candidate_package_shadow")
    elif not execution_policy_packet:
        missing_fields.append(
            "scheduler_v4.ultimate_candidate_package_shadow.execution_policy_shadow"
        )
    group_status = (
        "captured_incomplete"
        if gate_violations
        else "captured_present"
        if selector_packet or scheduler_packet
        else "prospective_capture_required"
    )
    shadow_selected_candidate_id = scheduler_packet.get("shadow_selected_candidate_id")
    selected_candidate_id = scheduler_packet.get("selected_candidate_id")
    approved_risk_pct = scheduler_packet.get("approved_risk_pct")
    return {
        "owner": "ultimate_candidate_package_shadow_selector_scheduler_surface",
        "registry_path": _first_present(
            scheduler_packet.get("registry_path"),
            selector_packet.get("registry_path"),
            runtime_config.get("ultimate_candidate_package_registry_path"),
        ),
        "config_flags": {
            "enabled": runtime_config.get("ultimate_candidate_package_enabled"),
            "shadow_enabled": runtime_config.get("ultimate_candidate_package_shadow_enabled"),
            "apply_to_execution": config_apply,
            "live_activation_allowed": config_live,
            "final_package_selected": config_final_selected,
        },
        "selector_packet": selector_packet or None,
        "scheduler_packet": scheduler_packet or None,
        "execution_policy_packet": execution_policy_packet or None,
        "matched_sleeve_count": _first_present(selector_packet.get("matched_sleeve_count"), 0),
        "matched_scheduler_lifecycle_merge_sleeves": _first_present(
            selector_packet.get("matched_scheduler_lifecycle_merge_sleeves"),
            0,
        ),
        "matched_promote_default_off_sleeves": _first_present(
            selector_packet.get("matched_promote_default_off_sleeves"),
            0,
        ),
        "shadow_selected_candidate_id": shadow_selected_candidate_id,
        "selected_candidate_id": selected_candidate_id,
        "would_scheduler_action": scheduler_packet.get("would_scheduler_action"),
        "execution_policy_status": execution_policy_packet.get("policy_status"),
        "would_order_entry_policy": execution_policy_packet.get("would_order_entry_policy"),
        "would_primary_order_type": execution_policy_packet.get("would_primary_order_type"),
        "would_guarded_market_fallback": execution_policy_packet.get(
            "would_guarded_market_fallback"
        ),
        "selected_order_type_architecture": execution_policy_packet.get(
            "selected_order_type_architecture"
        ),
        "execution_order_type_policy_selectable": False,
        "missed_fill_opportunity_cost_allowed": False,
        "required_cost_source_fields": execution_policy_packet.get(
            "required_cost_source_fields",
            [],
        ),
        "required_fillability_source_fields": execution_policy_packet.get(
            "required_fillability_source_fields",
            [],
        ),
        "action": _first_present(
            scheduler_packet.get("action"),
            execution_policy_packet.get("action"),
            selector_packet.get("action"),
        ),
        "approved_risk_pct": approved_risk_pct,
        "runtime_effect_now": False,
        "candidate_use_allowed_now": False,
        "final_package_selection_allowed": False,
        "live_execution_activation_allowed": False,
        "broker_account_order_history_deal_position_mutation_allowed": False,
        "order_calls": 0,
        "default_off": True,
        "shadow_only": True,
        "proof_boundary": (
            "package_packets_are_shadow_architecture_only_until_denominator_clean_label_"
            "cost_validation_and_wave_h_proof_select_the_final_package"
        ),
        "gate_violations": sorted(dict.fromkeys(gate_violations)),
        "group_source_status": group_status,
        "missing_fields": sorted(dict.fromkeys(missing_fields)),
        "capture_requirement": (
            None
            if group_status == "captured_present"
            else (
                "Selector V4 and Scheduler V4 must carry ultimate candidate package "
                "shadow packets with final/live/broker mutation gates closed before "
                "LiveDecisionPacketV4 packet parity is complete"
            )
        ),
    }


def _status_from_bool(value: Any) -> str:
    if value is True:
        return "captured_complete"
    if value is False:
        return "captured_incomplete"
    return "unknown_or_not_emitted"


def _same_symbol_lifecycle_packet(
    pipeline: dict[str, Any],
    record: dict[str, Any],
) -> tuple[dict[str, Any], str | None]:
    for source_name, value in (
        ("decision_pipeline.same_symbol_lifecycle_v4", pipeline.get("same_symbol_lifecycle_v4")),
        (
            "decision_pipeline.same_symbol_same_instrument_lifecycle_v4",
            pipeline.get("same_symbol_same_instrument_lifecycle_v4"),
        ),
        ("decision_pipeline.same_symbol_lifecycle", pipeline.get("same_symbol_lifecycle")),
        (
            "decision_pipeline.scheduler_v4.source_context.same_symbol_lifecycle_packet",
            _get_path(pipeline, "scheduler_v4", "source_context", "same_symbol_lifecycle_packet"),
        ),
        (
            "decision_pipeline.scheduler_v4_best_trade_allocator.source_context.same_symbol_lifecycle_packet",
            _get_path(
                pipeline,
                "scheduler_v4_best_trade_allocator",
                "source_context",
                "same_symbol_lifecycle_packet",
            ),
        ),
        (
            "record.gtos_vnext_same_symbol_lifecycle_v4_packet",
            record.get("gtos_vnext_same_symbol_lifecycle_v4_packet"),
        ),
        (
            "record.trade_parameters.gtos_vnext_same_symbol_lifecycle_v4_packet",
            _get_path(record, "trade_parameters", "gtos_vnext_same_symbol_lifecycle_v4_packet"),
        ),
    ):
        if isinstance(value, dict) and value:
            return value, source_name
    return {}, None


def _same_symbol_lifecycle_group(
    *,
    pipeline: dict[str, Any],
    record: dict[str, Any],
    final_order_decision: dict[str, Any],
) -> dict[str, Any]:
    packet, source_name = _same_symbol_lifecycle_packet(pipeline, record)
    candidate = _dict(packet.get("candidate"))
    durable_capture = _dict(packet.get("durable_lifecycle_capture"))
    open_positions = (
        packet.get("open_position_snapshot")
        if isinstance(packet.get("open_position_snapshot"), list)
        else []
    )
    pending_orders = (
        packet.get("pending_order_snapshot")
        if isinstance(packet.get("pending_order_snapshot"), list)
        else []
    )
    action = _first_present(
        packet.get("action"),
        pipeline.get("same_symbol_lifecycle_action"),
        record.get("gtos_vnext_same_symbol_lifecycle_action"),
        _get_path(record, "trade_parameters", "gtos_vnext_same_symbol_lifecycle_action"),
    )
    permitted = packet.get("permitted_order_intent")
    durable_missing = durable_capture.get("missing_fields")
    missing_fields = list(durable_missing) if isinstance(durable_missing, list) else []
    for field, value in (
        ("same_symbol_lifecycle_v4_packet", packet),
        ("action", action),
        ("permitted_order_intent", permitted),
        ("candidate.candidate_id", candidate.get("candidate_id")),
        ("candidate.thesis_id", candidate.get("thesis_id")),
        ("candidate.probability", candidate.get("probability")),
        ("candidate.ev_r", candidate.get("ev_r")),
        ("durable_lifecycle_capture.capture_hash_sha256", durable_capture.get("capture_hash_sha256")),
        ("source_event_hash_sha256", packet.get("source_event_hash_sha256")),
        ("packet_hash_sha256", packet.get("packet_hash_sha256")),
    ):
        if value in (None, "", [], {}):
            missing_fields.append(field)
    missing_fields = sorted(dict.fromkeys(str(field) for field in missing_fields))

    management_state = [
        {
            "ticket": _dict(position).get("ticket"),
            "thesis_id": _dict(position).get("thesis_id"),
            "lifecycle_phase": _dict(position).get("lifecycle_phase"),
            "source_status": _dict(position).get("source_status"),
            "stale_thesis": _dict(position).get("stale_thesis"),
            "partial_state": _dict(position).get("partial_state"),
            "be_state": _dict(position).get("be_state"),
            "trailing_state": _dict(position).get("trailing_state"),
        }
        for position in open_positions
        if isinstance(position, dict)
    ]
    if not management_state and packet:
        management_state = [
            {
                "status": "captured_no_same_symbol_open_position",
                "source_status": "captured",
            }
        ]

    group_status = (
        "captured_complete"
        if packet
        and durable_capture.get("status") == "complete"
        and not missing_fields
        else "captured_incomplete"
    )
    return {
        "owner": "same_symbol_same_instrument_lifecycle_v4",
        "position_ticket": _first_present(final_order_decision.get("ticket"), packet.get("parent_ticket")),
        "trade_id": final_order_decision.get("trade_id"),
        "order_path": final_order_decision.get("order_path"),
        "pending_limit": record.get("limit_intent"),
        "execution": record.get("execution"),
        "same_symbol_lifecycle_packet_source": source_name,
        "same_symbol_lifecycle_packet_hash_sha256": packet.get("packet_hash_sha256"),
        "same_symbol_lifecycle_source_event_hash_sha256": packet.get("source_event_hash_sha256"),
        "durable_lifecycle_capture": durable_capture,
        "candidate_lifecycle_capture": {
            "candidate_id": candidate.get("candidate_id"),
            "thesis_id": candidate.get("thesis_id"),
            "risk_pct": candidate.get("risk_pct"),
            "probability_at_decision": candidate.get("probability"),
            "ev_r_at_decision": candidate.get("ev_r"),
            "source_completeness_status": candidate.get("source_completeness_status"),
            "freshness_status": candidate.get("freshness_status"),
        },
        "parent_ticket": packet.get("parent_ticket"),
        "parent_thesis_id": packet.get("parent_thesis_id"),
        "selected_tickets": packet.get("selected_tickets"),
        "close_ticket": packet.get("close_ticket"),
        "reverse_intent_id": packet.get("reverse_intent_id"),
        "scale_in_risk_delta_pct": packet.get("scale_in_risk_delta_pct"),
        "open_position_snapshot": open_positions,
        "pending_order_snapshot": pending_orders,
        "open_trade_vs_new_candidate_competition": _field_status(
            {
                "candidate": candidate,
                "open_position_snapshot": open_positions,
                "pending_order_snapshot": pending_orders,
                "source_completeness": packet.get("source_completeness"),
            }
            if packet
            else None,
            missing_reason="same_symbol_lifecycle_v4_packet_not_yet_emitted",
        ),
        "scale_reduce_close_reverse_state": _field_status(
            {
                "action": action,
                "permitted_order_intent": permitted,
                "reason": packet.get("reason"),
                "parent_ticket": packet.get("parent_ticket"),
                "parent_thesis_id": packet.get("parent_thesis_id"),
                "selected_tickets": packet.get("selected_tickets"),
                "close_ticket": packet.get("close_ticket"),
                "reverse_intent_id": packet.get("reverse_intent_id"),
                "scale_in_risk_delta_pct": packet.get("scale_in_risk_delta_pct"),
            }
            if packet
            else None,
            missing_reason="ticket_bound_scale_reduce_close_reverse_state_not_yet_emitted",
        ),
        "partial_be_trailing_stale_thesis_state": _field_status(
            management_state,
            missing_reason="partial_be_trailing_stale_thesis_state_not_yet_emitted",
        ),
        "no_duplicate_exposure_status": _field_status(
            {
                "action": action,
                "permitted_order_intent": permitted,
                "vetoes": packet.get("vetoes"),
                "rejected_alternatives": packet.get("rejected_alternatives"),
                "broker_local_risk_result": packet.get("broker_local_risk_result"),
            }
            if packet
            else None,
            missing_reason="no_duplicate_exposure_status_not_yet_emitted",
        ),
        "group_source_status": group_status,
        "missing_fields": missing_fields,
        "capture_requirement": (
            None
            if group_status == "captured_complete"
            else (
                "Same-symbol lifecycle lane must emit ticket-bound open/pending/"
                "scale/reduce/close/reverse/duplicate-exposure state with durable "
                "candidate thesis, probability, EV, and lifecycle hashes"
            )
        ),
    }


def _source_gap_rows(packet: dict[str, Any]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    groups = packet.get("field_groups") or {}
    for group_name, group_payload in groups.items():
        group_status = group_payload.get("group_source_status")
        if group_status not in {"captured_complete", "captured_present"}:
            gaps.append(
                {
                    "group": group_name,
                    "status": group_status,
                    "missing": group_payload.get("missing_fields") or [],
                    "owner": group_payload.get("owner"),
                    "capture_requirement": group_payload.get("capture_requirement"),
                }
            )
    return gaps


def build_live_decision_packet_v4(
    *,
    record: dict[str, Any],
    legacy_packet: dict[str, Any],
    candidate: dict[str, Any] | None = None,
    raw_data: dict[str, Any] | None = None,
    runtime_config: dict[str, Any] | None = None,
    log_path: str | None = None,
    defer_packet_hash: bool = False,
) -> dict[str, Any]:
    """Build LiveDecisionPacketV4 from current source/capture surfaces."""
    candidate = _dict(candidate)
    raw_data = _dict(raw_data)
    runtime_config = _dict(runtime_config)
    pipeline = _dict(record.get("decision_pipeline"))
    metadata = _dict(record.get("metadata"))
    legacy = _dict(legacy_packet)

    candidate_identity = _dict(legacy.get("candidate_identity"))
    source_m15 = _dict(legacy.get("source_m15"))
    source_completeness = _dict(legacy.get("source_completeness"))
    source_identity_material = {
        "candidate_identity": candidate_identity,
        "source_m15": {
            key: source_m15.get(key)
            for key in (
                "candle_open_utc",
                "candle_close_utc",
                "timeframe",
                "market_timeframe",
                "source_path_feature_status",
                "source_window_complete",
                "source_fields",
            )
        },
        "runtime_event": _get_path(legacy, "runtime_decision", "event"),
        "raw_data_identity": {
            "symbol": raw_data.get("symbol"),
            "candle_close_utc": raw_data.get("candle_close_utc"),
            "source_hash": raw_data.get("source_hash"),
            "source_file": raw_data.get("source_file"),
        },
    }
    source_event_hash = _json_sha256(source_identity_material)

    final_order_decision = _dict(legacy.get("final_order_decision"))
    order_readiness = _dict(legacy.get("order_readiness"))
    broker_snapshot = _dict(legacy.get("broker_spec_snapshot"))
    tick_snapshot = _dict(legacy.get("tick_spread_snapshot"))
    v3_authority = _dict(legacy.get("v3_live_authority"))
    final_risk_authority = _dict(legacy.get("final_risk_authority"))
    selected_cell = _dict(legacy.get("selected_cell_risk_proof"))
    scheduler = _scheduler_from_pipeline(pipeline)
    ultimate_package_group = _ultimate_candidate_package_from_pipeline(
        pipeline,
        runtime_config,
    )
    scheduler_decision = _dict(scheduler.get("decision"))
    scheduler_input_counts = _dict(scheduler.get("input_counts"))
    scheduler_selected_option = _dict(scheduler_decision.get("selected_option"))
    scheduler_alternative_count = _first_present(
        scheduler_input_counts.get("candidate_rows"),
        scheduler_input_counts.get("allocator_options"),
        len(scheduler.get("all_options_preserved") or [])
        if isinstance(scheduler.get("all_options_preserved"), list)
        else None,
    )
    scheduler_zero_trade_value = _first_present(
        scheduler.get("zero_trade_value"),
        scheduler_decision.get("zero_trade_value"),
        scheduler_selected_option.get("zero_trade_value"),
        scheduler_selected_option.get("score")
        if scheduler_decision.get("selected_action_class") == "zero_trade"
        else None,
    )
    scheduler_missing_fields = [
        field
        for field, value in (
            ("decision_window_id", _first_present(scheduler.get("decision_window_id"), pipeline.get("decision_window_id"))),
            ("candidate_set_id", _first_present(scheduler.get("candidate_set_id"), pipeline.get("candidate_set_id"))),
            ("alternative_candidate_count", scheduler_alternative_count),
            ("zero_trade_value", scheduler_zero_trade_value),
            ("selected_action_class", scheduler_decision.get("selected_action_class")),
        )
        if value in (None, "", [], {})
    ]
    probability_debate = _component_from_pipeline(
        pipeline,
        "probability_debate_v4",
        "probability_debate_team_engine_v4",
        "probability_debate",
        "gtos_vnext_probability_debate",
    )
    probability_numeric_theses = _numeric_theses_from_pipeline(pipeline)
    probability_final_action = _first_present(
        pipeline.get("probability_debate_final_action"),
        probability_debate.get("selected_action"),
    )
    probability_missing_fields = [
        f"numeric_theses.{action}"
        for action, thesis in probability_numeric_theses.items()
        if thesis.get("source_status") != "captured"
    ]
    if probability_final_action in (None, "", [], {}):
        probability_missing_fields.append("final_action_selection")
    if probability_debate.get("confidence_calibration") in (None, "", [], {}) and probability_debate.get(
        "selected_thesis"
    ) not in (None, "", [], {}):
        selected_thesis = _dict(probability_debate.get("selected_thesis"))
        if selected_thesis.get("confidence_calibration") in (None, "", [], {}):
            probability_missing_fields.append("calibration")
    elif probability_debate.get("confidence_calibration") in (None, "", [], {}):
        probability_missing_fields.append("calibration")
    confluence_payload = _confluence_from_pipeline(pipeline)
    confluence_missing_fields = [
        field
        for field in (
            "direction",
            "strength",
            "confidence",
            "reliability_history",
            "evidence_class",
            "freshness",
            "cost_sensitivity",
            "conflict_reason",
            "source_completeness",
            "avoid_invalidation_type",
            "mixed_disagreement",
        )
        if _get_path(confluence_payload, field, "source_status") != "captured"
    ]

    field_groups: dict[str, Any] = {
        "candidate_identity_and_source_namespace": {
            "owner": "data_capture_source_repair_final_and_livedecisionpacket_v4",
            "candidate_identity": candidate_identity,
            "source_namespace": {
                "symbol": candidate_identity.get("symbol"),
                "broker_symbol": candidate_identity.get("broker_symbol"),
                "source_symbol": _first_present(
                    raw_data.get("source_symbol"),
                    candidate.get("source_symbol"),
                    candidate_identity.get("broker_symbol"),
                ),
                "candidate_id": candidate_identity.get("candidate_id"),
                "trade_id": candidate_identity.get("trade_id"),
            },
            "group_source_status": (
                "captured_complete"
                if candidate_identity.get("candidate_id")
                and candidate_identity.get("broker_symbol")
                else "captured_incomplete"
            ),
            "missing_fields": [
                field
                for field in ("candidate_id", "broker_symbol")
                if candidate_identity.get(field) in (None, "")
            ],
            "capture_requirement": None,
        },
        "source_window_hash_and_no_leak_contract": {
            "owner": "data_capture_source_repair_final_and_livedecisionpacket_v4",
            "source_event_hash_sha256": source_event_hash,
            "packet_source_hash_contract": "pre_decision_source_identity_sha256_v1",
            "source_m15": source_m15,
            "m1_ltf_availability": legacy.get("m1_ltf_availability"),
            "tick_spread_snapshot_status": _status_from_bool(tick_snapshot.get("available")),
            "source_completeness": source_completeness,
            "no_leak_status": "PASS_PRE_DECISION_SOURCE_HASH_EXCLUDES_POST_DECISION_FIELDS",
            "post_decision_fields_allowed_only_as_lifecycle_truth": sorted(
                POST_DECISION_ROOTS
            ),
            "group_source_status": (
                "captured_complete"
                if source_completeness.get("source_window_complete") is True
                and source_event_hash
                else "captured_incomplete"
            ),
            "missing_fields": (
                []
                if source_completeness.get("source_window_complete") is True
                else ["source_window_complete"]
            ),
            "capture_requirement": None,
        },
        "selector_allocator_final_say": {
            "owner": "scheduler_v4_best_trade_allocator",
            "selector_bridge_proof": legacy.get("selector_bridge_proof"),
            "v3_live_authority": v3_authority,
            "selected_cell_risk_proof": selected_cell,
            "decision_window_id": _field_status(
                _first_present(scheduler.get("decision_window_id"), pipeline.get("decision_window_id")),
                missing_reason="allocator_decision_window_id_not_yet_emitted",
            ),
            "candidate_set_id": _field_status(
                _first_present(scheduler.get("candidate_set_id"), pipeline.get("candidate_set_id")),
                missing_reason="allocator_candidate_set_id_not_yet_emitted",
            ),
            "alternative_candidate_count": _field_status(
                scheduler_alternative_count,
                missing_reason="allocator_alternatives_not_yet_emitted",
            ),
            "zero_trade_value": _field_status(
                scheduler_zero_trade_value,
                missing_reason="zero_trade_value_not_yet_emitted",
            ),
            "selected_action_class": _field_status(
                scheduler_decision.get("selected_action_class"),
                missing_reason="allocator_selected_action_class_not_yet_emitted",
            ),
            "selected_candidate_id": _field_status(
                scheduler_decision.get("selected_candidate_id"),
                missing_reason="allocator_selected_candidate_id_not_yet_emitted",
            ),
            "final_say_authority": _first_present(
                scheduler.get("status"),
                _get_path(v3_authority, "status"),
                _get_path(legacy, "dynamic_policy", "selected_policy_source"),
                "legacy_candidate_packet_final_order_decision",
            ),
            "group_source_status": (
                "captured_complete" if not scheduler_missing_fields else "captured_incomplete"
            ),
            "missing_fields": scheduler_missing_fields,
            "capture_requirement": (
                None
                if not scheduler_missing_fields
                else (
                    "SchedulerV4 must emit decision_window_id, candidate_set_id, all "
                    "material alternatives, open/pending competition, selected action, "
                    "and zero-trade value"
                )
            ),
        },
        "ultimate_candidate_package_selector_scheduler_surface": ultimate_package_group,
        "execution_geometry_policy_and_order_readiness": {
            "owner": "execution_manager_v4",
            "geometry": legacy.get("geometry"),
            "dynamic_policy": legacy.get("dynamic_policy"),
            "pending_policy": legacy.get("pending_policy"),
            "order_readiness": order_readiness,
            "final_order_decision": final_order_decision,
            "final_risk_authority": final_risk_authority,
            "group_source_status": (
                "captured_complete"
                if order_readiness.get("order_path") not in (None, "")
                else "captured_incomplete"
            ),
            "missing_fields": (
                []
                if order_readiness.get("order_path") not in (None, "")
                else ["order_readiness.order_path"]
            ),
            "capture_requirement": None,
        },
        "cost_slippage_swap_broker_constraints": {
            "owner": "cost_swap_slippage_broker_constraint_engine",
            "broker_spec_snapshot": broker_snapshot,
            "tick_spread_snapshot": tick_snapshot,
            "spread_source_status": _status_from_bool(tick_snapshot.get("available")),
            "commission_source_status": _field_status(
                _first_present(
                    broker_snapshot.get("commission"),
                    broker_snapshot.get("commission_per_lot"),
                    pipeline.get("gtos_vnext_commission_model_status"),
                ),
                missing_reason="broker_commission_source_not_yet_emitted",
            ),
            "swap_source_status": _field_status(
                _first_present(broker_snapshot.get("swap_long"), broker_snapshot.get("swap_short")),
                missing_reason="broker_swap_source_not_yet_emitted",
            ),
            "slippage_source_status": _field_status(
                pipeline.get("slippage_source_status"),
                missing_reason="pre_send_or_fill_slippage_source_not_yet_emitted",
            ),
            "cash_conversion_source_status": _field_status(
                broker_snapshot.get("trade_tick_value"),
                missing_reason="broker_cash_conversion_tick_value_not_available",
            ),
            "group_source_status": (
                "captured_complete"
                if tick_snapshot.get("available")
                and broker_snapshot.get("symbol_info_available")
                else "captured_incomplete"
            ),
            "missing_fields": [
                field
                for field, value in (
                    ("tick_spread_snapshot.available", tick_snapshot.get("available")),
                    (
                        "broker_spec_snapshot.symbol_info_available",
                        broker_snapshot.get("symbol_info_available"),
                    ),
                    ("commission", broker_snapshot.get("commission")),
                    ("swap_long_or_short", _first_present(broker_snapshot.get("swap_long"), broker_snapshot.get("swap_short"))),
                )
                if value in (None, "", False)
            ],
            "capture_requirement": (
                "Cost engine must emit commission, swap, slippage, session/spec, and "
                "cash conversion fields as broker-local source truth"
            ),
        },
        "same_symbol_lifecycle_and_ticket_state": _same_symbol_lifecycle_group(
            pipeline=pipeline,
            record=record,
            final_order_decision=final_order_decision,
        ),
        "probability_debate_numeric_theses": {
            "owner": "probability_debate_team_engine_v4",
            "numeric_theses": probability_numeric_theses,
            "final_action_selection": _field_status(
                probability_final_action,
                missing_reason="probability_debate_final_action_not_yet_emitted",
            ),
            "missing_source_penalty": _field_status(
                _first_present(
                    pipeline.get("probability_missing_source_penalty"),
                    _get_path(probability_debate, "source_summary", "missing_source_penalty"),
                    _get_path(probability_debate, "selected_thesis", "missing_source_penalty"),
                ),
                missing_reason="probability_missing_source_penalty_not_yet_emitted",
            ),
            "calibration": _field_status(
                _first_present(
                    pipeline.get("probability_calibration"),
                    probability_debate.get("confidence_calibration"),
                    _get_path(probability_debate, "selected_thesis", "confidence_calibration"),
                ),
                missing_reason="probability_calibration_not_yet_emitted",
            ),
            "group_source_status": (
                "captured_present"
                if probability_debate and len(probability_missing_fields) < len(probability_numeric_theses) + 2
                else "prospective_capture_required"
            ),
            "missing_fields": sorted(dict.fromkeys(probability_missing_fields)),
            "capture_requirement": (
                "Probability debate lane must emit calibrated numeric alternatives "
                "for trade/no-trade/manage actions with EV, uncertainty, vetoes, "
                "disagreement, and missing-source penalties"
            ),
        },
        "follow_avoid_mixed_numeric_confluence": {
            "owner": "follow_avoid_mixed_numeric_confluence_v4",
            **confluence_payload,
            "group_source_status": (
                "captured_present"
                if len(confluence_missing_fields) < 11
                else "prospective_capture_required"
            ),
            "missing_fields": sorted(dict.fromkeys(confluence_missing_fields)),
            "capture_requirement": (
                "Confluence lane must emit numeric FOLLOW/AVOID/MIXED mapping; "
                "FOLLOW is not trade permission and MIXED must carry structured disagreement"
            ),
        },
        "broker_dual_broker_local_truth": {
            "owner": "dual_broker_runtime_contract",
            "source_broker_namespace": _first_present(
                runtime_config.get("broker_profile"),
                runtime_config.get("source_broker_namespace"),
                "current_runtime_broker_namespace_not_reported",
            ),
            "target_broker_namespace": _field_status(
                runtime_config.get("target_broker_namespace"),
                missing_reason="target_broker_namespace_not_emitted_in_current_runtime_config",
            ),
            "no_copy_rule": (
                "do_not_copy_redacted_account_lots_fills_cash_cost_specs_lifecycle_truth_to_FTMO"
            ),
            "broker_local_truth_status": "source_broker_only_unless_target_broker_fields_present",
            "redacted_account_fields_must_not_be_ftmo_truth": True,
            "group_source_status": "captured_present",
            "missing_fields": [],
            "capture_requirement": (
                "Dual broker lane must emit target-broker-local risk/cost/spec truth "
                "before any target-broker decision uses it"
            ),
        },
        "halt_authority_and_runtime_control": {
            "owner": "runtime_control_atomic_halt_safety",
            "gate0": _get_path(legacy, "gates", "gate0_deployment_profile_trading"),
            "runtime_decision": legacy.get("runtime_decision"),
            "hard_halt_boundary": {
                "broker_runtime_change_status": False,
                "packet_capture_is_observation_only": True,
            },
            "process_autostart_recovery": _field_status(
                pipeline.get("process_autostart_recovery"),
                missing_reason="runtime_control_process_autostart_recovery_not_yet_emitted",
            ),
            "atomic_halt_authority_chain": _field_status(
                pipeline.get("atomic_halt_authority_chain"),
                missing_reason="runtime_control_atomic_halt_authority_chain_not_yet_emitted",
            ),
            "group_source_status": "captured_incomplete",
            "missing_fields": [
                "process_autostart_recovery",
                "atomic_halt_authority_chain",
            ],
            "capture_requirement": (
                "Runtime control lane must emit halt flags, process authority, "
                "scheduler shutdown, and final-say chain without broker mutation"
            ),
        },
        "ai_reliability_and_cost_control": {
            "owner": "ai_reliability_cost_control",
            "ai_call_policy": pipeline.get("ai_call_policy"),
            "ai_supervisor": pipeline.get("ai_supervisor"),
            "confidence_filter": pipeline.get("confidence_filter"),
            "ai_decision_trace": pipeline.get("ai_decision_trace"),
            "llm_budget_policy": _field_status(
                pipeline.get("llm_budget_policy"),
                missing_reason="llm_budget_policy_not_yet_emitted_in_packet",
            ),
            "group_source_status": "captured_incomplete",
            "missing_fields": [
                field
                for field in (
                    "ai_call_policy",
                    "ai_supervisor",
                    "confidence_filter",
                    "ai_decision_trace",
                    "llm_budget_policy",
                )
                if pipeline.get(field) in (None, "", [], {})
            ],
            "capture_requirement": (
                "AI reliability lane must emit schema/budget/fallback decisions; ML "
                "feature/label/model registry ownership stays separate"
            ),
        },
        "feature_label_forward_capture_contract": {
            "owner": "wave4_wave5_ml_owner",
            "feature_store_status": "prospective_capture_requirement",
            "label_store_status": "prospective_capture_requirement",
            "digital_twin_status": "prospective_capture_requirement",
            "ml_baseline_status": "prospective_capture_requirement",
            "model_registry_status": "prospective_capture_requirement",
            "leakage_guard": (
                "features must be as-of; broker-real labels, exact-R, proxy-R, "
                "MFE, MAE, giveback, cost, stale thesis, and opportunity cost "
                "must be captured after outcome with partition-safe status"
            ),
            "group_source_status": "prospective_capture_required",
            "missing_fields": [
                "feature_store_row_id",
                "label_store_row_id",
                "digital_twin_replay_id",
                "model_registry_candidate_id",
            ],
            "capture_requirement": (
                "Wave4/Wave5 must own feature store, label store, digital twin, "
                "ML baselines, walk-forward, Brier/ECE/logloss, registry, and challengers"
            ),
        },
    }

    packet: dict[str, Any] = {
        "schema_name": SCHEMA_VERSION,
        "schema_version": PACKET_SCHEMA_VERSION,
        "created_at_utc": utc_now_iso(),
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "validation_result_status": False,
        "outcome_result_rows_status": False,
        "broker_runtime_change_status": False,
        "capture_mode": "native_live_writer_capture_only",
        "capture_reason": "wave3_live_decision_packet_v4_source_truth_capture",
        "runtime_effect_boundary": (
            "packet_capture_only_no_broker_order_account_deal_position_mutation"
        ),
        "forbidden_surface_boundary": dict(FORBIDDEN_SURFACE_BOUNDARY),
        "legacy_packet_schema_version": legacy.get("schema_version"),
        "candidate_identity": candidate_identity,
        "source_event_hash_sha256": source_event_hash,
        "source_event_hash_material": _json_safe(source_identity_material),
        "packet_log_path": log_path,
        "required_field_groups": list(REQUIRED_FIELD_GROUPS),
        "field_groups": field_groups,
        "semantic_ownership": {
            key: {
                "owner_lane": owner,
                "requirement": requirement,
                "packet_status": (
                    "captured_or_explicit_source_gap"
                    if key in {
                        "same_symbol_lifecycle",
                        "probability_debate",
                        "follow_avoid_mixed_numeric_confluence",
                        "scheduler_allocator",
                    }
                    else "captured_boundary_or_forward_capture_contract"
                ),
            }
            for key, (owner, requirement) in SEMANTIC_OWNERSHIP_REQUIREMENTS.items()
        },
        "production_code_disposition": {
            "live_decision_packet_v4": "active_capture_only",
            "orchestrator_candidate_packet_v1": "extended_active_v4_source_capture",
            "selector_v3_scheduler_v3_execution_v3": "captured_default_off_authority_only",
            "ultimate_candidate_package": "active_default_off_shadow_packet_capture",
        },
        "runtime_evidence_contract": {
            "source_completeness_policy": (
                "each field group carries captured, captured_incomplete, "
                "captured_present, prospective_capture_required, or source_gap status"
            ),
            "no_leak_asof_policy": (
                "pre-decision source_event_hash excludes post-decision fields; "
                "post-decision order/lifecycle fields are lifecycle truth only"
            ),
            "duplicate_policy": (
                "candidate_identity.candidate_id plus trade_id, broker_symbol, "
                "candle_close_utc, source_event_hash_sha256, and decision_window_id "
                "when present define canonical decision identity; duplicates must be "
                "merged before denominator, validation, or ML label use"
            ),
            "partition_holdout_requirements": (
                "this lane emits no validation rows; future validation must freeze "
                "discovery/development/sealed/stress/forward partitions before using "
                "packet labels or outcome fields"
            ),
            "cost_slippage_stress_requirements": (
                "cost engine must provide broker-local commission, swap, spread, "
                "slippage, session/spec, cash conversion, and stress fields before "
                "broker-net expectancy or promotion claims"
            ),
            "rollback_path": (
                "set gtos_vnext_runtime.live_decision_packet_v4_enabled=false to "
                "disable attachment, or clear live_decision_packet_v4_log_path to "
                "retain trade-record capture without JSONL append"
            ),
            "semantic_ownership_handoff": sorted(SEMANTIC_OWNERSHIP_REQUIREMENTS),
        },
    }
    packet["source_gap_rows"] = _source_gap_rows(packet)
    packet["packet_completeness"] = {
        "required_group_count": len(REQUIRED_FIELD_GROUPS),
        "present_group_count": len(field_groups),
        "source_gap_group_count": len(packet["source_gap_rows"]),
        "status": (
            "complete_with_explicit_source_gaps"
            if len(field_groups) == len(REQUIRED_FIELD_GROUPS)
            else "missing_required_groups"
        ),
    }
    packet_hash_material = {
        "schema_version": packet["schema_version"],
        "candidate_identity": packet["candidate_identity"],
        "source_event_hash_sha256": packet["source_event_hash_sha256"],
        "field_groups": packet["field_groups"],
        "semantic_ownership": packet["semantic_ownership"],
        "forbidden_surface_boundary": packet["forbidden_surface_boundary"],
    }
    if defer_packet_hash:
        packet["packet_hash_sha256"] = None
        packet[DEFERRED_PACKET_HASH_PREIMAGE_KEY] = _json_material_bytes(
            packet_hash_material
        )
    else:
        packet["packet_hash_sha256"] = _json_sha256(packet_hash_material)
    return packet


def validate_live_decision_packet_v4(packet: dict[str, Any]) -> list[dict[str, Any]]:
    """Return machine-checkable packet validation issues."""
    issues: list[dict[str, Any]] = []
    if packet.get("schema_name") != SCHEMA_VERSION:
        issues.append({"code": "schema_name_mismatch", "value": packet.get("schema_name")})
    if packet.get("schema_version") != PACKET_SCHEMA_VERSION:
        issues.append(
            {"code": "schema_version_mismatch", "value": packet.get("schema_version")}
        )
    if packet.get("broker_runtime_change_status") is not False:
        issues.append({"code": "broker_runtime_change_status_not_false"})
    if packet.get("validation_result_status") is not False:
        issues.append({"code": "validation_result_status_not_false"})
    if packet.get("outcome_result_rows_status") is not False:
        issues.append({"code": "outcome_result_rows_status_not_false"})
    forbidden = packet.get("forbidden_surface_boundary")
    if not isinstance(forbidden, dict):
        issues.append({"code": "forbidden_surface_boundary_missing"})
    else:
        for key, value in forbidden.items():
            if value is not False:
                issues.append(
                    {
                        "code": "forbidden_surface_boundary_not_false",
                        "surface": key,
                        "value": value,
                    }
                )
    groups = packet.get("field_groups")
    if not isinstance(groups, dict):
        issues.append({"code": "field_groups_missing"})
    else:
        for group in REQUIRED_FIELD_GROUPS:
            if group not in groups:
                issues.append({"code": "required_group_missing", "group": group})
    semantic = packet.get("semantic_ownership")
    if not isinstance(semantic, dict):
        issues.append({"code": "semantic_ownership_missing"})
    else:
        for key in SEMANTIC_OWNERSHIP_REQUIREMENTS:
            if key not in semantic:
                issues.append({"code": "semantic_ownership_missing_key", "key": key})
    if not packet.get("source_event_hash_sha256"):
        issues.append({"code": "source_event_hash_missing"})
    if not packet.get("packet_hash_sha256"):
        issues.append({"code": "packet_hash_missing"})
    source_hash_material = packet.get("source_event_hash_material")
    if isinstance(source_hash_material, dict):
        expected_source_hash = _json_sha256(source_hash_material)
        if packet.get("source_event_hash_sha256") != expected_source_hash:
            issues.append(
                {
                    "code": "source_event_hash_mismatch",
                    "expected": expected_source_hash,
                    "actual": packet.get("source_event_hash_sha256"),
                }
            )
    else:
        issues.append({"code": "source_event_hash_material_missing"})
    if isinstance(groups, dict) and isinstance(semantic, dict) and isinstance(forbidden, dict):
        expected_packet_hash = _json_sha256(
            {
                "schema_version": packet.get("schema_version"),
                "candidate_identity": packet.get("candidate_identity"),
                "source_event_hash_sha256": packet.get("source_event_hash_sha256"),
                "field_groups": groups,
                "semantic_ownership": semantic,
                "forbidden_surface_boundary": forbidden,
            }
        )
        if packet.get("packet_hash_sha256") != expected_packet_hash:
            issues.append(
                {
                    "code": "packet_hash_mismatch",
                    "expected": expected_packet_hash,
                    "actual": packet.get("packet_hash_sha256"),
                }
            )
    ultimate_group = _get_path(
        packet,
        "field_groups",
        "ultimate_candidate_package_selector_scheduler_surface",
    )
    if isinstance(ultimate_group, dict):
        for gate in (
            "runtime_effect_now",
            "candidate_use_allowed_now",
            "final_package_selection_allowed",
            "live_execution_activation_allowed",
            "broker_account_order_history_deal_position_mutation_allowed",
        ):
            if ultimate_group.get(gate) is not False:
                issues.append(
                    {
                        "code": "ultimate_candidate_package_gate_not_false",
                        "gate": gate,
                        "value": ultimate_group.get(gate),
                    }
                )
        if ultimate_group.get("order_calls") not in (False, 0):
            issues.append(
                {
                    "code": "ultimate_candidate_package_order_calls_not_zero",
                    "value": ultimate_group.get("order_calls"),
                }
            )
        if ultimate_group.get("selected_candidate_id") not in (None, ""):
            issues.append(
                {
                    "code": "ultimate_candidate_package_selected_candidate_not_closed",
                    "value": ultimate_group.get("selected_candidate_id"),
                }
            )
        if ultimate_group.get("approved_risk_pct") not in (None, 0, 0.0):
            issues.append(
                {
                    "code": "ultimate_candidate_package_approved_risk_not_zero",
                    "value": ultimate_group.get("approved_risk_pct"),
                }
            )
        if ultimate_group.get("selected_order_type_architecture") not in (None, ""):
            issues.append(
                {
                    "code": "ultimate_candidate_package_order_type_selection_not_closed",
                    "value": ultimate_group.get("selected_order_type_architecture"),
                }
            )
        if ultimate_group.get("execution_order_type_policy_selectable") is not False:
            issues.append(
                {
                    "code": "ultimate_candidate_package_execution_policy_selectable_not_false",
                    "value": ultimate_group.get("execution_order_type_policy_selectable"),
                }
            )
        if ultimate_group.get("missed_fill_opportunity_cost_allowed") is not False:
            issues.append(
                {
                    "code": "ultimate_candidate_package_missed_fill_cost_not_closed",
                    "value": ultimate_group.get("missed_fill_opportunity_cost_allowed"),
                }
            )
        if ultimate_group.get("gate_violations"):
            issues.append(
                {
                    "code": "ultimate_candidate_package_gate_violations_present",
                    "violations": ultimate_group.get("gate_violations"),
                }
            )
    no_leak = _get_path(
        packet,
        "field_groups",
        "source_window_hash_and_no_leak_contract",
        "no_leak_status",
    )
    if no_leak != "PASS_PRE_DECISION_SOURCE_HASH_EXCLUDES_POST_DECISION_FIELDS":
        issues.append({"code": "no_leak_status_missing_or_invalid", "value": no_leak})
    runtime_contract = packet.get("runtime_evidence_contract")
    required_runtime_contract_keys = {
        "source_completeness_policy",
        "no_leak_asof_policy",
        "duplicate_policy",
        "partition_holdout_requirements",
        "cost_slippage_stress_requirements",
        "rollback_path",
        "semantic_ownership_handoff",
    }
    if not isinstance(runtime_contract, dict):
        issues.append({"code": "runtime_evidence_contract_missing"})
    else:
        missing = sorted(required_runtime_contract_keys - set(runtime_contract))
        if missing:
            issues.append(
                {
                    "code": "runtime_evidence_contract_keys_missing",
                    "missing": missing,
                }
            )
    return issues


def append_live_decision_packet_v4(packet: dict[str, Any], path: str | Path) -> None:
    """Append packet as JSONL; failures are swallowed by the caller boundary."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(_json_safe(packet), sort_keys=True, separators=(",", ":")))
        fh.write("\n")


def attach_live_decision_packet_v4(
    record: dict[str, Any],
    *,
    legacy_packet: dict[str, Any],
    candidate: dict[str, Any] | None = None,
    raw_data: dict[str, Any] | None = None,
    runtime_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach and optionally append LiveDecisionPacketV4 to the runtime record."""
    runtime_config = _dict(runtime_config)
    enabled = runtime_config.get("live_decision_packet_v4_enabled", True)
    log_path = runtime_config.get("live_decision_packet_v4_log_path")
    if enabled is False:
        packet = {
            "schema_name": SCHEMA_VERSION,
            "schema_version": PACKET_SCHEMA_VERSION,
            "capture_mode": "disabled_by_runtime_config",
            "broker_runtime_change_status": False,
            "disabled_reason": "live_decision_packet_v4_enabled_false",
        }
        record.setdefault("decision_pipeline", {})["live_decision_packet_v4"] = packet
        return packet

    packet = build_live_decision_packet_v4(
        record=record,
        legacy_packet=legacy_packet,
        candidate=candidate,
        raw_data=raw_data,
        runtime_config=runtime_config,
        log_path=log_path,
    )
    record.setdefault("decision_pipeline", {})["live_decision_packet_v4"] = packet
    if log_path:
        try:
            append_live_decision_packet_v4(packet, log_path)
        except Exception as exc:  # noqa: BLE001 - capture must not affect trading flow.
            logger.warning("LiveDecisionPacketV4 append failed: %s", exc, exc_info=True)
            packet["append_status"] = {
                "status": "append_failed_capture_retained_in_trade_record",
                "error": str(exc),
            }
    return packet


__all__ = [
    "DEFAULT_LOG_PATH",
    "EVIDENCE_CLASS",
    "FORBIDDEN_SURFACE_BOUNDARY",
    "PACKET_SCHEMA_VERSION",
    "REQUIRED_FIELD_GROUPS",
    "RESULT_USE_STATUS",
    "SCHEMA_VERSION",
    "SEMANTIC_OWNERSHIP_REQUIREMENTS",
    "append_live_decision_packet_v4",
    "attach_live_decision_packet_v4",
    "build_live_decision_packet_v4",
    "validate_live_decision_packet_v4",
]
