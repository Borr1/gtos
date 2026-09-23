"""Closed, order-agnostic inputs for the Wave 21 truth Selector boundary.

The legacy Selector accepts a large event mapping and contains compatibility
fallbacks for packages, routers, order policy, and later-stage state.  Those
fallbacks are not a valid pre-order truth boundary.  This module defines the
two packets that truth mode is allowed to inspect:

* an immutable, account-agnostic candidate decision projection; and
* a separate Selector context projection for broker-net cell, cost, lifecycle,
  and the finite pure-Selector policy configuration.

Both packets use closed schemas.  Truth callers must pass the sanitized event
and sanitized config returned by :func:`selector_truth_sanitized_inputs` to
Selector; hashing a projection while evaluating the original event is not a
contract.
"""

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_SCHEMA = (
    "gtos.selector_order_agnostic_candidate_input_projection.v2"
)
SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_SOURCE_BOUNDARY = (
    "immediately_preselector_closed_candidate_decision_inputs_no_order_policy"
)
SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_STATUS_MATERIALIZED = "materialized"

SELECTOR_CONTEXT_INPUT_PROJECTION_SCHEMA = (
    "gtos.selector_context_input_projection.v1"
)
SELECTOR_CONTEXT_INPUT_PROJECTION_SOURCE_BOUNDARY = (
    "immediately_preselector_closed_broker_cost_lifecycle_and_policy_context"
)
SELECTOR_CONTEXT_INPUT_PROJECTION_STATUS_MATERIALIZED = "materialized"


SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_FIELD_NAMES = (
    "selector_order_agnostic_input_projection_schema",
    "selector_order_agnostic_input_projection_sha256",
    "selector_order_agnostic_input_projection_status",
    "selector_order_agnostic_input_projection_source_boundary",
    "selector_order_agnostic_input_projection",
    "selector_order_agnostic_input_projection_removed_order_paths",
    "selector_order_agnostic_input_projection_removed_non_authoritative_paths",
    "selector_order_agnostic_input_projection_order_dependent_paths",
    "selector_order_agnostic_input_projection_forbidden_outcome_paths",
    "selector_order_agnostic_input_projection_missing_required_paths",
)

SELECTOR_CONTEXT_INPUT_PROJECTION_FIELD_NAMES = (
    "selector_context_input_projection_schema",
    "selector_context_input_projection_sha256",
    "selector_context_input_projection_status",
    "selector_context_input_projection_source_boundary",
    "selector_context_event_projection",
    "selector_context_resolved_runtime_config_projection",
    "selector_context_account_metadata_projection",
    "selector_context_removed_non_authoritative_paths",
    "selector_context_forbidden_or_unknown_paths",
    "selector_context_missing_required_paths",
)


_SHA256_FIELDS = frozenset(
    {
        "candidate_transform_chain_root_sha256",
        "emission_lineage_hash_sha256",
        "emission_source_authority_root_sha256",
        "emission_source_composition_root_sha256",
        "emission_mso_source_receipt_root_sha256",
        "emission_producer_code_root_sha256",
        "emission_producer_config_sha256",
    }
)

_REQUIRED_CANDIDATE_FIELDS = (
    "origin_family",
    "generator_family_strategy_version",
    "candidate_action_class",
    "decision_time_utc",
    "symbol",
    "side",
    "entry_reference_price",
    "entry_reference_price_provenance",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "candidate_transform_chain_root_sha256",
    "emission_lineage_hash_sha256",
    "emission_source_authority_root_sha256",
    "emission_source_composition_root_sha256",
    "emission_mso_source_receipt_root_sha256",
    "emission_producer_code_root_sha256",
    "emission_producer_config_sha256",
    "emission_source_timeframe",
    "emission_source_timestamp_timezone_status",
    "source_window_complete",
    "numeric_confluence",
    "probability_debate",
)

_CANDIDATE_ALIASES: dict[str, tuple[str, ...]] = {
    "origin_family": ("origin_family",),
    "generator_family_strategy_version": ("generator_family_strategy_version",),
    "candidate_action_class": ("candidate_action_class",),
    "decision_time_utc": ("decision_time_utc",),
    "symbol": ("symbol",),
    "side": ("side", "direction"),
    "entry_reference_price": ("entry_reference_price",),
    "entry_reference_price_provenance": ("entry_reference_price_provenance",),
    "entry_price": ("entry_price", "entry", "e"),
    "stop_loss": ("stop_loss", "stop", "sl"),
    "take_profit_1": ("take_profit_1", "target", "tp"),
    "risk_reward_ratio": ("risk_reward_ratio",),
    "candidate_transform_chain_root_sha256": (
        "candidate_transform_chain_root_sha256",
    ),
    "emission_lineage_hash_sha256": ("emission_lineage_hash_sha256",),
    "emission_source_authority_root_sha256": (
        "emission_source_authority_root_sha256",
    ),
    "emission_source_composition_root_sha256": (
        "emission_source_composition_root_sha256",
    ),
    "emission_mso_source_receipt_root_sha256": (
        "emission_mso_source_receipt_root_sha256",
    ),
    "emission_producer_code_root_sha256": (
        "emission_producer_code_root_sha256",
    ),
    "emission_producer_config_sha256": ("emission_producer_config_sha256",),
    "emission_source_timeframe": ("emission_source_timeframe",),
    "emission_source_timestamp_timezone_status": (
        "emission_source_timestamp_timezone_status",
    ),
    "source_window_complete": ("source_window_complete",),
    "source_candle_time_utc": ("source_candle_time_utc", "candle_close_utc"),
    "candle_open_utc": ("candle_open_utc",),
    "poi_id": ("poi_id",),
    "poi_state_hash_sha256": ("poi_state_hash_sha256",),
}

_CONFLUENCE_ROOT_ALIASES = (
    "numeric_confluence",
    "follow_avoid_mixed_numeric_confluence",
    "confluence",
)
_DEBATE_ROOT_ALIASES = (
    "probability_debate",
    "probability_debate_packet",
    "debate",
)

_CONFLUENCE_SOURCE_ALIASES: dict[str, tuple[str, ...]] = {
    "source_id": ("source_id",),
    "source_family": ("source_family", "family", "source_kind"),
    "schema_version": ("schema_version",),
    "label": ("label", "classification", "fam_label", "state", "categorical_label"),
    "direction": ("direction", "side", "bias_direction"),
    "strength": ("strength",),
    "confidence": ("confidence",),
    "reliability_history": ("reliability_history", "reliability"),
    "freshness": ("freshness",),
    "source_completeness": ("source_completeness",),
    "cost_sensitivity": ("cost_sensitivity",),
    "invalidation_type": ("invalidation_type", "avoid_invalidation_type"),
    "conflict_reason": ("conflict_reason",),
    "evidence_class": ("evidence_class",),
}

_SCORE_MAPPING_FIELDS = frozenset(
    {
        "score",
        "freshness_score",
        "reliability_score",
        "cost_sensitivity_score",
        "source_completeness_score",
        "confidence",
        "value",
        "status",
    }
)

_DEBATE_ACTIONS = (
    "long",
    "short",
    "no-trade",
    "wait",
    "scale",
    "reduce",
    "close",
    "reverse",
)
_THESIS_ALIASES: dict[str, tuple[str, ...]] = {
    "probability": ("probability",),
    "EV": ("EV", "ev", "expected_value_r", "ev_r"),
    "uncertainty": ("uncertainty",),
    "missing_source_penalty": ("missing_source_penalty", "source_penalty"),
    "source_completeness": ("source_completeness",),
    "confidence_calibration": ("confidence_calibration", "calibration"),
    "evidence_class": ("evidence_class",),
    "vetoes": ("vetoes",),
    "disagreement_state": ("disagreement_state",),
    "rejected_alternatives": ("rejected_alternatives",),
}

_CONTEXT_ROOT_ALIASES = {
    "selected_cell": (
        "broker_net_selected_cell",
        "selected_cell",
        "selected_cell_admission",
        "broker_net",
    ),
    "cost": ("broker_cost", "cost", "cost_swap_slippage"),
    "lifecycle": ("lifecycle", "same_symbol_lifecycle", "position_lifecycle"),
}

_SELECTED_CELL_ALIASES: dict[str, tuple[str, ...]] = {
    "selected_cell_id": ("selected_cell_id", "cell_id"),
    "broker_net_expectancy_r": (
        "broker_net_expectancy_r",
        "broker_net_ev_r",
        "cost_adjusted_expectancy_r",
        "selected_cell_expectancy_r",
        "expectancy_r",
    ),
    "stress_expectancy_r": ("stress_expectancy_r", "broker_net_stress_ev_r"),
    "risk_pct": ("risk_pct", "selected_cell_risk_pct", "approved_risk_pct"),
    "source_completeness": ("source_completeness",),
    "evidence_class": ("evidence_class",),
    "rows": ("rows", "selected_cell_rows", "effective_n"),
    "source_status": ("source_status", "result_use_status"),
    "fill_probability": ("fill_probability",),
    "confidence": ("confidence", "candidate_confidence"),
}

_COST_ALIASES: dict[str, tuple[str, ...]] = {
    "expected_total_cost_r": (
        "expected_total_cost_r",
        "total_cost_r",
        "broker_net_cost_r",
    ),
    "spread_r": ("spread_r",),
    "commission_r": ("commission_r",),
    "swap_r": ("swap_r",),
    "slippage_stress_r": ("slippage_stress_r",),
    "source_completeness": ("source_completeness",),
    "evidence_class": ("evidence_class",),
    "pretrade_cost_packet_status": (
        "pretrade_cost_packet_status",
        "broker_net_cost_packet_status",
    ),
    "cost_source_gap_status": (
        "cost_source_gap_status",
        "broker_net_cost_source_gap_status",
    ),
    "cost_authority": ("cost_authority", "pretrade_cost_packet_authority"),
    "execution_cost_authority": (
        "execution_cost_authority",
        "execution_cost_scope",
    ),
    "candidate_cost_r_fallback_is_authority": (
        "candidate_cost_r_fallback_is_authority",
        "source_gap_cost_fallback_is_authority",
    ),
    "pretrade_cost_refusal_reasons": ("pretrade_cost_refusal_reasons",),
    "source_gap_cost_fallback_blocked": ("source_gap_cost_fallback_blocked",),
}

_COST_PACKET_ALIASES: dict[str, tuple[str, ...]] = {
    "status": ("status",),
    "expected_total_cost_r": (
        "expected_total_cost_r",
        "total_cost_r",
        "broker_net_cost_r",
    ),
    "cost_source_gap_status": ("cost_source_gap_status",),
    "authority": ("authority",),
    "candidate_cost_r_fallback_is_authority": (
        "candidate_cost_r_fallback_is_authority",
    ),
    "refusal_reasons": ("refusal_reasons",),
    "source_gap_cost_fallback_blocked": ("source_gap_cost_fallback_blocked",),
}

_LIFECYCLE_ALIASES: dict[str, tuple[str, ...]] = {
    "duplicate_exposure": ("duplicate_exposure", "duplicate_symbol_exposure"),
    "same_symbol_conflict": ("same_symbol_conflict", "same_instrument_conflict"),
    "open_trade_competition_status": (
        "open_trade_competition_status",
        "open_trade_competition",
    ),
    "source_completeness": ("source_completeness",),
    "evidence_class": ("evidence_class",),
    "ticket_bound_state": ("ticket_bound_state",),
    "pending_partial_be_trailing_stale_state": (
        "pending_partial_be_trailing_stale_state",
    ),
    "decision_packet_version": ("decision_packet_version",),
}

_LIFECYCLE_PACKET_FIELDS = frozenset(
    {"action", "reason", "permitted_order_intent", "evidence_class", "candidate"}
)
_LIFECYCLE_PACKET_CANDIDATE_ALIASES: dict[str, tuple[str, ...]] = {
    "candidate_id": ("candidate_id", "replay_candidate_id"),
    "symbol": ("symbol", "candidate_symbol", "instrument"),
    "side": ("side", "direction"),
    "decision_time_utc": (
        "decision_time_utc",
        "asof_utc",
        "candle_close_utc",
    ),
}

_FLAT_SELECTED_CELL_ALIASES: dict[str, tuple[str, ...]] = {
    "broker_net_expectancy_r": (
        "broker_net_expectancy_r",
        "cost_adjusted_expectancy_r",
    ),
    "stress_expectancy_r": ("stress_expectancy_r",),
    "risk_pct": ("selected_cell_risk_pct", "risk_pct"),
    "selected_cell_id": ("selected_cell_id",),
    "source_completeness": ("source_completeness",),
    "evidence_class": ("evidence_class",),
}

_FLAT_COST_ALIASES: dict[str, tuple[str, ...]] = {
    "expected_total_cost_r": (
        "expected_total_cost_r",
        "total_cost_r",
        "total_execution_cost_r",
        "broker_calibrated_expected_cost_r",
        "broker_pretrade_cost_r",
        "expected_cost_r",
        "cost_r",
    ),
    "pretrade_cost_packet_status": (
        "pretrade_cost_packet_status",
        "broker_net_cost_packet_status",
    ),
    "pretrade_cost_refusal_reasons": ("pretrade_cost_refusal_reasons",),
    "cost_source_gap_status": (
        "cost_source_gap_status",
        "broker_net_cost_source_gap_status",
    ),
    "cost_authority": ("cost_authority", "execution_cost_authority"),
    "candidate_cost_r_fallback_is_authority": (
        "candidate_cost_r_fallback_is_authority",
        "source_gap_cost_fallback_is_authority",
    ),
    "source_gap_cost_fallback_blocked": ("source_gap_cost_fallback_blocked",),
    "source_completeness": ("cost_source_completeness",),
    "evidence_class": ("cost_evidence_class",),
}

_SAFE_RUNTIME_CONFIG_FIELDS = frozenset(
    {
        "wave21_full_flow_truth_mode_enabled",
        "selector_v4_enabled",
        "selector_v4_apply_to_execution",
        "selector_v4_live_activation_allowed",
        "selector_v4_require_confluence_source_families",
        "selector_v4_required_confluence_source_families",
        "selector_v4_min_confluence_source_completeness",
        "selector_v4_hard_avoid_strength",
        "selector_v4_max_missing_source_penalty",
        "selector_v4_min_selected_cell_source_completeness",
        "selector_v4_require_pretrade_cost_model",
        "selector_v4_enforce_broker_net_cost_packet_refusal",
        "selector_v4_max_expected_cost_r",
        "selector_v4_min_broker_net_trade_ev_r",
        "selector_v4_min_no_trade_ev_r",
        "selector_v4_min_confluence_score",
        "selector_v4_max_uncertainty_for_full_risk",
        "selector_v4_reduce_risk_multiplier",
        "selector_v4_admission_quality_guard_enabled",
        "selector_v4_admission_quality_exact_block_rules_mode",
        "selector_v4_admission_quality_rule_enforcement_mode",
        "selector_v4_admission_quality_guard_source",
        "selector_v4_admission_quality_blocked_session_origin_families",
        "selector_v4_admission_quality_blocked_session_origin_symbols",
        "selector_v4_admission_quality_blocked_utc_hour_buckets",
        "selector_v4_block_off_configured_session_entries",
        "selector_v4_block_off_configured_session_partial_be_runner",
        "selector_v4_block_partial_be_runner",
        "selector_v4_off_configured_session_entry_action",
        "selector_v4_off_configured_session_max_cost_r",
        "selector_v4_calibrated_admission_enabled",
        "selector_v4_calibrated_admission_floor_failure_action",
        "selector_v4_calibrated_admission_require_fill_probability",
        "selector_v4_calibrated_admission_source",
        "selector_v4_calibrated_min_expected_net_r",
        "selector_v4_calibrated_min_fill_probability",
        "selector_v4_calibrated_min_probability",
        "selector_v4_calibrated_min_source_completeness",
    }
)

_UNSAFE_RUNTIME_ENABLE_FIELDS = frozenset(
    {
        "selector_v4_enforce_dynamic_router_refusal",
        "selector_v4_learned_edge_enabled",
        "selector_v4_learned_edge_required",
        "selector_v4_learned_risk_sizing_enabled",
        "selector_v4_package_session_token_authority_enabled",
        "ultimate_candidate_package_apply_to_execution",
        "ultimate_candidate_package_enabled",
        "ultimate_candidate_package_replay_admission_enabled",
        "ultimate_candidate_package_shadow_enabled",
        "ultimate_candidate_package_soften_dynamic_router_refusal_enabled",
        "ultimate_candidate_package_soften_selector_fill_floor_enabled",
        "ultimate_candidate_package_strong_fill_floor_bypass_enabled",
        "ultimate_candidate_package_session_token_authority_enabled",
        "scheduler_v4_best_trade_allocator_selector_reduce_risk_numeric_disagreement_package_new_entry_authority_enabled",
        "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_authority_enabled",
        "scheduler_v4_best_trade_allocator_selector_reduce_risk_router_refusal_package_new_entry_authority_enabled",
    }
)

_NON_AUTHORITATIVE_TOP_LEVEL_FIELDS = frozenset(
    {
        "candidate_id",
        "replay_candidate_id",
        "candidate_order_type",
        "candidate_order_type_hint",
        "final_order_type",
        "order_type",
        "time_in_force",
        "tif",
        "expiry",
        "expiry_time_utc",
        "native_pending_order_type",
        "packet_hash_sha256",
        "source_event_hash_sha256",
        "candidate_transform_chain",
        "poi_state",
        "emission_lineage_schema",
        "emission_lineage_id",
        "emission_lineage_status",
        "emission_lineage_source_boundary",
        "emission_lineage_atoms",
        "emission_lineage_missing_atoms",
        "emission_lineage_origin_family",
        "emission_lineage_symbol",
        "emission_lineage_generation_side",
        "emission_lineage_timeframe",
        "emission_lineage_source_anchor",
        "emission_lineage_source_authority",
        "emission_lineage_source_authority_root_sha256",
        "emission_lineage_source_composition",
        "emission_lineage_source_composition_root_sha256",
        "emission_lineage_mso_source_receipt_root_sha256",
        "emission_lineage_producer_code_root_sha256",
        "emission_lineage_producer_config_sha256",
        "emission_lineage_cross_asset_source_authorities",
        "emission_source_authority",
        "emission_source_authority_by_timeframe",
        "emission_source_composition",
        "emission_mso_source_receipt",
        "emission_cross_asset_source_authorities",
        "executable_instance_schema",
        "executable_instance_id",
        "executable_instance_hash_sha256",
        "executable_instance_status",
        "executable_instance_source_boundary",
        "executable_instance_decision_time_utc",
        "executable_instance_order_type",
        "executable_instance_time_in_force",
        "executable_instance_expiry_time_utc",
        "executable_instance_atoms",
        "executable_instance_missing_atoms",
        "account_id",
        "profile",
        "broker",
        "server",
        "account_currency",
        "balance",
        "equity",
        "open_positions",
    }
)

_ORDER_DEPENDENT_TOP_LEVEL_FIELDS = frozenset(
    {
        "predecision_limit_fillability",
        "limit_fillability_probability",
        "predecision_limit_fillability_probability",
        "order_executable",
        "marketable_entry",
        "min_fill_probability",
        "fill_floor",
    }
)

_UNSAFE_TOP_LEVEL_FIELDS = frozenset(
    {
        "ultimate_candidate_package",
        "ultimate_package",
        "candidate_ultimate_package",
        "package_new_entry_authority",
        "moonshot_dynamic_execution_router_v4",
        "dynamic_execution_policy",
        "dynamic_policy",
        "learned_edge",
        "learned_edge_packet",
        "fillability",
        "score_components",
    }
)

_LATER_OUTPUT_FIELDS = frozenset(
    {
        "component_scores",
        "effective_selector_action",
        "effective_selector_reason",
        "hard_reject_reasons",
        "materialized_selector_action",
        "materialized_selector_reason",
        "raw_selector_action",
        "raw_selector_reason",
        "reduced_risk_reasons",
        "risk_budget",
        "risk_pct",
        "selected_risk_pct",
        "selector_action",
        "selector_action_origin",
        "selector_reason",
        "selector_reason_origin",
        "source_required_fields",
    }
)

_LATER_OR_RECEIPT_PREFIXES = (
    "allocation_",
    "allocator_",
    "candidate_decision_fingerprint_",
    "candidate_identity_contract_",
    "effective_selector_",
    "executable_instance_",
    "materialized_selector_",
    "order_construction_",
    "raw_selector_",
    "risk_sizing_",
    "scheduler_",
    "selector_context_input_projection_",
    "selector_input_geometry_",
    "selector_order_agnostic_input_projection_",
    "selector_v4_verdict_",
)

_ACCOUNT_METADATA_FIELDS = frozenset(
    {"account_id", "profile", "broker", "server", "account_currency"}
)


def _canonical_primitive(value: Any) -> Any:
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Selector projection cannot encode NaN or infinity")
        return value
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Selector projection cannot encode naive datetimes")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("Selector projection mapping keys must be strings")
            result[key] = _canonical_primitive(item)
        return result
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_canonical_primitive(item) for item in value]
    raise TypeError(
        "Selector projection supports deterministic JSON primitives only: "
        f"{type(value).__module__}.{type(value).__qualname__}"
    )


def selector_order_agnostic_projection_sha256(value: Any) -> str:
    material = json.dumps(
        _canonical_primitive(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _same_value(left: Any, right: Any) -> bool:
    try:
        return selector_order_agnostic_projection_sha256(left) == (
            selector_order_agnostic_projection_sha256(right)
        )
    except (TypeError, ValueError):
        return False


def _alias_value(
    source: Mapping[str, Any],
    aliases: Sequence[str],
    *,
    canonical_path: str,
    forbidden: list[str],
) -> Any:
    present = [(name, source.get(name)) for name in aliases if _present(source.get(name))]
    if not present:
        return None
    first_name, first_value = present[0]
    for name, value in present[1:]:
        if not _same_value(first_value, value):
            forbidden.append(
                f"{canonical_path}:conflicting_aliases:{first_name}:{name}"
            )
    return first_value


def _allowed_alias_keys(aliases: Mapping[str, Sequence[str]]) -> frozenset[str]:
    return frozenset(alias for names in aliases.values() for alias in names)


def _unknown_mapping_keys(
    source: Mapping[str, Any],
    allowed: frozenset[str],
    *,
    path: str,
    forbidden: list[str],
) -> None:
    for key in source:
        if not isinstance(key, str):
            forbidden.append(f"{path}:non_string_key")
        elif key not in allowed:
            forbidden.append(f"{path}.{key}")


def _aware_utc(value: Any, *, path: str, missing: list[str]) -> str | None:
    try:
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, str) and value.strip():
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        else:
            raise ValueError
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
        return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, OverflowError):
        missing.append(f"{path}:aware_utc_required")
        return None


def _finite_number(value: Any, *, path: str, missing: list[str]) -> float | None:
    if isinstance(value, bool):
        missing.append(f"{path}:finite_number_required")
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        missing.append(f"{path}:finite_number_required")
        return None
    if not math.isfinite(number):
        missing.append(f"{path}:finite_number_required")
        return None
    return number


def _text(value: Any, *, path: str, missing: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        missing.append(f"{path}:nonempty_string_required")
        return None
    return value.strip()


def _sha256(value: Any, *, path: str, missing: list[str]) -> str | None:
    text = _text(value, path=path, missing=missing)
    if text is None:
        return None
    lowered = text.lower()
    if len(lowered) != 64 or any(char not in "009abcdef" for char in lowered):
        missing.append(f"{path}:sha256_required")
        return None
    return lowered


def _side(value: Any, *, path: str, missing: list[str]) -> str | None:
    text = _text(value, path=path, missing=missing)
    if text is None:
        return None
    normalized = text.upper()
    aliases = {
        "BUY": "LONG",
        "BULL": "LONG",
        "BULLISH": "LONG",
        "SELL": "SHORT",
        "BEAR": "SHORT",
        "BEARISH": "SHORT",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"LONG", "SHORT"}:
        missing.append(f"{path}:long_or_short_required")
        return None
    return normalized


def _string_list(value: Any, *, path: str, forbidden: list[str]) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        forbidden.append(f"{path}:string_sequence_required")
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            forbidden.append(f"{path}[{index}]:string_required")
        else:
            result.append(item)
    return sorted(set(result))


def _score_value(value: Any, *, path: str, forbidden: list[str]) -> Any:
    if isinstance(value, Mapping):
        _unknown_mapping_keys(
            value,
            _SCORE_MAPPING_FIELDS,
            path=path,
            forbidden=forbidden,
        )
        return _canonical_primitive(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return _canonical_primitive(value)
    forbidden.append(f"{path}:scalar_or_closed_score_packet_required")
    return None


def _canonical_confluence(
    raw: Any,
    *,
    forbidden: list[str],
    missing: list[str],
) -> dict[str, Any] | None:
    required_families: list[str] = []
    rows: Any
    if isinstance(raw, Mapping):
        if raw.get("source_id") is not None:
            rows = [raw]
        else:
            allowed = frozenset({"sources", "source_scores", "required_source_families"})
            _unknown_mapping_keys(
                raw,
                allowed,
                path="numeric_confluence",
                forbidden=forbidden,
            )
            rows = _alias_value(
                raw,
                ("sources", "source_scores"),
                canonical_path="numeric_confluence.sources",
                forbidden=forbidden,
            )
            required_families = _string_list(
                raw.get("required_source_families"),
                path="numeric_confluence.required_source_families",
                forbidden=forbidden,
            )
    else:
        rows = raw
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        missing.append("numeric_confluence.sources:sequence_required")
        return None
    if not rows:
        missing.append("numeric_confluence.sources:nonempty_required")
        return None
    canonical_rows: list[dict[str, Any]] = []
    seen_source_ids: set[str] = set()
    allowed_source_keys = _allowed_alias_keys(_CONFLUENCE_SOURCE_ALIASES)
    for index, row in enumerate(rows):
        path = f"numeric_confluence.sources[{index}]"
        if not isinstance(row, Mapping):
            forbidden.append(f"{path}:mapping_required")
            continue
        _unknown_mapping_keys(row, allowed_source_keys, path=path, forbidden=forbidden)
        canonical: dict[str, Any] = {}
        for name, aliases in _CONFLUENCE_SOURCE_ALIASES.items():
            value = _alias_value(
                row,
                aliases,
                canonical_path=f"{path}.{name}",
                forbidden=forbidden,
            )
            if value is not None:
                canonical[name] = (
                    _score_value(value, path=f"{path}.{name}", forbidden=forbidden)
                    if name
                    in {
                        "strength",
                        "confidence",
                        "reliability_history",
                        "freshness",
                        "source_completeness",
                        "cost_sensitivity",
                    }
                    else _canonical_primitive(value)
                )
        for required in (
            "source_id",
            "label",
            "direction",
            "strength",
            "confidence",
            "reliability_history",
            "freshness",
            "source_completeness",
            "cost_sensitivity",
            "evidence_class",
        ):
            if not _present(canonical.get(required)):
                missing.append(f"{path}.{required}")
        source_id = canonical.get("source_id")
        if isinstance(source_id, str) and source_id.strip():
            if source_id in seen_source_ids:
                forbidden.append(f"{path}.source_id:duplicate:{source_id}")
            seen_source_ids.add(source_id)
        canonical_rows.append(canonical)
    canonical_rows.sort(key=lambda row: str(row.get("source_id") or ""))
    return {
        "sources": canonical_rows,
        **(
            {"required_source_families": required_families}
            if required_families
            else {}
        ),
    }


def _normalize_action(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", "-")
    aliases = {
        "buy": "long",
        "bull": "long",
        "bullish": "long",
        "sell": "short",
        "bear": "short",
        "bearish": "short",
        "flat": "no-trade",
        "skip": "no-trade",
        "skip-trade": "no-trade",
        "notrade": "no-trade",
    }
    return aliases.get(text, text)


def _canonical_thesis(
    row: Mapping[str, Any],
    *,
    path: str,
    forbidden: list[str],
    missing: list[str],
    list_row: bool = False,
) -> dict[str, Any]:
    allowed = set(_allowed_alias_keys(_THESIS_ALIASES))
    if list_row:
        allowed.update({"action", "thesis_action", "selected_action"})
    _unknown_mapping_keys(row, frozenset(allowed), path=path, forbidden=forbidden)
    canonical: dict[str, Any] = {}
    for name, aliases in _THESIS_ALIASES.items():
        value = _alias_value(
            row,
            aliases,
            canonical_path=f"{path}.{name}",
            forbidden=forbidden,
        )
        if value is None:
            continue
        if name in {"vetoes", "rejected_alternatives"}:
            canonical[name] = _string_list(
                value,
                path=f"{path}.{name}",
                forbidden=forbidden,
            )
        else:
            canonical[name] = _canonical_primitive(value)
    for required in (
        "probability",
        "EV",
        "uncertainty",
        "missing_source_penalty",
        "source_completeness",
        "confidence_calibration",
        "evidence_class",
    ):
        if not _present(canonical.get(required)):
            missing.append(f"{path}.{required}")
    return canonical


def _canonical_debate(
    raw: Any,
    *,
    forbidden: list[str],
    missing: list[str],
) -> dict[str, Any] | None:
    if not isinstance(raw, Mapping):
        missing.append("probability_debate:mapping_required")
        return None
    allowed = frozenset(
        {
            "selected_action",
            "final_action",
            "action",
            "theses",
            "action_theses",
            "actions",
            "vetoes",
        }
    )
    _unknown_mapping_keys(raw, allowed, path="probability_debate", forbidden=forbidden)
    selected = _normalize_action(
        _alias_value(
            raw,
            ("selected_action", "final_action", "action"),
            canonical_path="probability_debate.selected_action",
            forbidden=forbidden,
        )
    )
    if selected not in _DEBATE_ACTIONS:
        missing.append("probability_debate.selected_action:known_action_required")
    thesis_rows = _alias_value(
        raw,
        ("theses", "action_theses", "actions"),
        canonical_path="probability_debate.theses",
        forbidden=forbidden,
    )
    canonical_theses: dict[str, dict[str, Any]] = {}
    if isinstance(thesis_rows, Mapping):
        for action, row in thesis_rows.items():
            normalized = _normalize_action(action)
            path = f"probability_debate.theses.{normalized or action}"
            if normalized not in _DEBATE_ACTIONS:
                forbidden.append(f"{path}:unknown_action")
                continue
            if not isinstance(row, Mapping):
                forbidden.append(f"{path}:mapping_required")
                continue
            canonical_theses[normalized] = _canonical_thesis(
                row,
                path=path,
                forbidden=forbidden,
                missing=missing,
            )
    elif isinstance(thesis_rows, Sequence) and not isinstance(
        thesis_rows, (str, bytes, bytearray)
    ):
        for index, row in enumerate(thesis_rows):
            path = f"probability_debate.theses[{index}]"
            if not isinstance(row, Mapping):
                forbidden.append(f"{path}:mapping_required")
                continue
            action = _normalize_action(
                _alias_value(
                    row,
                    ("action", "thesis_action", "selected_action"),
                    canonical_path=f"{path}.action",
                    forbidden=forbidden,
                )
            )
            if action not in _DEBATE_ACTIONS:
                forbidden.append(f"{path}.action:unknown_action")
                continue
            if action in canonical_theses:
                forbidden.append(f"{path}.action:duplicate_action:{action}")
                continue
            canonical_theses[action] = _canonical_thesis(
                row,
                path=path,
                forbidden=forbidden,
                missing=missing,
                list_row=True,
            )
    else:
        missing.append("probability_debate.theses:mapping_or_sequence_required")
    for action in _DEBATE_ACTIONS:
        if action not in canonical_theses:
            missing.append(f"probability_debate.theses.{action}")
    return {
        "selected_action": selected,
        "theses": canonical_theses,
        "vetoes": _string_list(
            raw.get("vetoes"),
            path="probability_debate.vetoes",
            forbidden=forbidden,
        ),
    }


def _candidate_projection(
    event: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str], list[str], list[str], list[str]]:
    removed: list[str] = []
    dependent: list[str] = []
    forbidden: list[str] = []
    missing: list[str] = []
    if not isinstance(event, Mapping):
        return {}, removed, dependent, ["event:mapping_required"], list(
            _REQUIRED_CANDIDATE_FIELDS
        )

    candidate_allowed = {
        alias for aliases in _CANDIDATE_ALIASES.values() for alias in aliases
    }
    candidate_allowed.update(_CONFLUENCE_ROOT_ALIASES)
    candidate_allowed.update(_DEBATE_ROOT_ALIASES)
    candidate_allowed.add("candidate_decision_inputs")
    context_fields = {
        alias for aliases in _CONTEXT_ROOT_ALIASES.values() for alias in aliases
    }
    context_fields.update(
        alias for aliases in _FLAT_SELECTED_CELL_ALIASES.values() for alias in aliases
    )
    context_fields.update(alias for aliases in _FLAT_COST_ALIASES.values() for alias in aliases)
    context_fields.update({"pretrade_broker_net_cost_packet", "broker_net_cost_packet"})
    for key in event:
        if not isinstance(key, str):
            forbidden.append("event:non_string_key")
        elif key in candidate_allowed:
            continue
        elif key in context_fields:
            removed.append(f"selector_context:{key}")
        elif key in _NON_AUTHORITATIVE_TOP_LEVEL_FIELDS:
            removed.append(key)
        elif key in _ORDER_DEPENDENT_TOP_LEVEL_FIELDS:
            dependent.append(key)
            forbidden.append(key)
        elif key in _UNSAFE_TOP_LEVEL_FIELDS or key.startswith(
            ("ultimate_candidate_package", "package_session", "route_session")
        ):
            forbidden.append(key)
        elif key in _LATER_OUTPUT_FIELDS or key.startswith(_LATER_OR_RECEIPT_PREFIXES):
            removed.append(f"later_or_receipt:{key}")
        else:
            forbidden.append(f"unrecognized_top_level:{key}")

    projection: dict[str, Any] = {}
    for name, aliases in _CANDIDATE_ALIASES.items():
        value = _alias_value(
            event,
            aliases,
            canonical_path=name,
            forbidden=forbidden,
        )
        if value is None:
            continue
        if name == "decision_time_utc" or name in {"source_candle_time_utc", "candle_open_utc"}:
            canonical = _aware_utc(value, path=name, missing=missing)
        elif name == "side":
            canonical = _side(value, path=name, missing=missing)
        elif name == "symbol":
            text = _text(value, path=name, missing=missing)
            canonical = text.upper() if text else None
        elif name in {
            "entry_reference_price",
            "entry_price",
            "stop_loss",
            "take_profit_1",
            "risk_reward_ratio",
        }:
            canonical = _finite_number(value, path=name, missing=missing)
        elif name in _SHA256_FIELDS or name == "poi_state_hash_sha256":
            canonical = _sha256(value, path=name, missing=missing)
        elif name == "source_window_complete":
            canonical = value if isinstance(value, bool) else None
            if canonical is not True:
                missing.append("source_window_complete:true_required")
        else:
            canonical = _text(value, path=name, missing=missing)
        if canonical is not None:
            projection[name] = canonical

    if projection.get("candidate_action_class") != "NEW_EXPOSURE_CANDIDATE":
        missing.append("candidate_action_class:NEW_EXPOSURE_CANDIDATE_required")
    if projection.get("emission_source_timestamp_timezone_status") != "timezone_aware":
        missing.append("emission_source_timestamp_timezone_status:timezone_aware_required")

    confluence_raw = _alias_value(
        event,
        _CONFLUENCE_ROOT_ALIASES,
        canonical_path="numeric_confluence",
        forbidden=forbidden,
    )
    if confluence_raw is None:
        missing.append("numeric_confluence")
    else:
        confluence = _canonical_confluence(
            confluence_raw,
            forbidden=forbidden,
            missing=missing,
        )
        if confluence is not None:
            projection["numeric_confluence"] = confluence

    decision_inputs = event.get("candidate_decision_inputs")
    decision_debate = None
    if decision_inputs is not None:
        if not isinstance(decision_inputs, Mapping):
            forbidden.append("candidate_decision_inputs:mapping_required")
        else:
            _unknown_mapping_keys(
                decision_inputs,
                frozenset(_DEBATE_ROOT_ALIASES),
                path="candidate_decision_inputs",
                forbidden=forbidden,
            )
            decision_debate = _alias_value(
                decision_inputs,
                _DEBATE_ROOT_ALIASES,
                canonical_path="candidate_decision_inputs.probability_debate",
                forbidden=forbidden,
            )
    top_debate = _alias_value(
        event,
        _DEBATE_ROOT_ALIASES,
        canonical_path="probability_debate",
        forbidden=forbidden,
    )
    if top_debate is not None and decision_debate is not None and not _same_value(
        top_debate, decision_debate
    ):
        forbidden.append("probability_debate:top_level_candidate_decision_inputs_conflict")
    debate_raw = top_debate if top_debate is not None else decision_debate
    if debate_raw is None:
        missing.append("probability_debate")
    else:
        debate = _canonical_debate(debate_raw, forbidden=forbidden, missing=missing)
        if debate is not None:
            projection["probability_debate"] = debate

    for field in _REQUIRED_CANDIDATE_FIELDS:
        if not _present(projection.get(field)) and field not in {
            "entry_reference_price",
            "entry_price",
            "stop_loss",
            "take_profit_1",
        }:
            missing.append(field)
        elif field in {
            "entry_reference_price",
            "entry_price",
            "stop_loss",
            "take_profit_1",
        } and field not in projection:
            missing.append(field)
    return projection, removed, dependent, forbidden, missing


def project_selector_order_agnostic_inputs(
    value: Any,
    *,
    path: str = "",
    exclude_receipts: bool = True,
) -> tuple[Any, list[str], list[str], list[str]]:
    """Compatibility API returning the closed candidate projection.

    ``path`` and ``exclude_receipts`` are retained for callers of the rejected
    v1 draft.  Projection is now defined only at the event root.
    """

    if path:
        raise ValueError("closed Selector candidate projection must start at event root")
    del exclude_receipts
    projection, removed, dependent, forbidden, _missing = _candidate_projection(value)
    return projection, sorted(set(removed)), sorted(set(dependent)), sorted(set(forbidden))


def selector_order_agnostic_input_projection(value: Any) -> Any:
    projection, _, _, _, _ = _candidate_projection(value)
    return projection


def build_selector_order_agnostic_input_projection_fields(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        projection, removed, dependent, forbidden, missing = _candidate_projection(event)
        digest = selector_order_agnostic_projection_sha256(
            {
                "schema": SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_SCHEMA,
                "projection": projection,
            }
        )
    except (TypeError, ValueError):
        projection = {}
        removed = []
        dependent = []
        forbidden = ["event:not_canonical_json_primitives"]
        missing = ["selector_order_agnostic_input_projection_not_canonical"]
        digest = ""
    valid = bool(digest and not dependent and not forbidden and not missing)
    return {
        "selector_order_agnostic_input_projection_schema": (
            SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_SCHEMA
        ),
        "selector_order_agnostic_input_projection_sha256": digest if valid else None,
        "selector_order_agnostic_input_projection_status": (
            SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_STATUS_MATERIALIZED
            if valid
            else "invalid_or_missing_required_inputs"
        ),
        "selector_order_agnostic_input_projection_source_boundary": (
            SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_SOURCE_BOUNDARY
        ),
        "selector_order_agnostic_input_projection": projection,
        "selector_order_agnostic_input_projection_removed_order_paths": sorted(
            path
            for path in set(removed)
            if path in _NON_AUTHORITATIVE_TOP_LEVEL_FIELDS and (
                "order" in path or "tif" in path or "expiry" in path
            )
        ),
        "selector_order_agnostic_input_projection_removed_non_authoritative_paths": sorted(
            set(removed)
        ),
        "selector_order_agnostic_input_projection_order_dependent_paths": sorted(
            set(dependent)
        ),
        "selector_order_agnostic_input_projection_forbidden_outcome_paths": sorted(
            set(forbidden)
        ),
        "selector_order_agnostic_input_projection_missing_required_paths": sorted(
            set(missing)
        ),
    }


def selector_order_agnostic_input_projection_failures(
    event: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> tuple[str, ...]:
    if not isinstance(event, Mapping):
        return ("selector_order_agnostic_input_event_invalid",)
    if not isinstance(receipt, Mapping):
        return ("selector_order_agnostic_input_projection_receipt_missing",)
    expected = build_selector_order_agnostic_input_projection_fields(event)
    failures = [
        f"{field}_current_projection_mismatch"
        for field in SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_FIELD_NAMES
        if receipt.get(field) != expected.get(field)
    ]
    if expected.get("selector_order_agnostic_input_projection_status") != (
        SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_STATUS_MATERIALIZED
    ):
        failures.append("selector_order_agnostic_input_projection_current_invalid")
    return tuple(dict.fromkeys(failures))


def _closed_alias_projection(
    source: Mapping[str, Any],
    aliases: Mapping[str, Sequence[str]],
    *,
    path: str,
    forbidden: list[str],
) -> dict[str, Any]:
    _unknown_mapping_keys(
        source,
        _allowed_alias_keys(aliases),
        path=path,
        forbidden=forbidden,
    )
    result: dict[str, Any] = {}
    for canonical, names in aliases.items():
        value = _alias_value(
            source,
            names,
            canonical_path=f"{path}.{canonical}",
            forbidden=forbidden,
        )
        if value is not None:
            result[canonical] = _canonical_primitive(value)
    return result


def _canonical_selected_cell(
    event: Mapping[str, Any],
    *,
    forbidden: list[str],
    missing: list[str],
) -> dict[str, Any] | None:
    roots = [
        (name, event.get(name))
        for name in _CONTEXT_ROOT_ALIASES["selected_cell"]
        if isinstance(event.get(name), Mapping) and event.get(name)
    ]
    if roots:
        first_name, first = roots[0]
        for name, value in roots[1:]:
            if not _same_value(first, value):
                forbidden.append(f"selected_cell:conflicting_roots:{first_name}:{name}")
        result = _closed_alias_projection(
            first,
            _SELECTED_CELL_ALIASES,
            path="selected_cell",
            forbidden=forbidden,
        )
    else:
        result = {}
        for canonical, aliases in _FLAT_SELECTED_CELL_ALIASES.items():
            value = _alias_value(
                event,
                aliases,
                canonical_path=f"selected_cell.{canonical}",
                forbidden=forbidden,
            )
            if value is not None:
                result[canonical] = _canonical_primitive(value)
    if not result:
        missing.append("selected_cell")
        return None
    for field in (
        "broker_net_expectancy_r",
        "risk_pct",
        "source_completeness",
        "evidence_class",
    ):
        if not _present(result.get(field)) and not (
            field in {"broker_net_expectancy_r", "risk_pct", "source_completeness"}
            and result.get(field) == 0
        ):
            missing.append(f"selected_cell.{field}")
    return result


def _canonical_cost(
    event: Mapping[str, Any],
    *,
    forbidden: list[str],
    missing: list[str],
) -> dict[str, Any] | None:
    roots = [
        (name, event.get(name))
        for name in _CONTEXT_ROOT_ALIASES["cost"]
        if isinstance(event.get(name), Mapping) and event.get(name)
    ]
    if roots:
        first_name, first = roots[0]
        for name, value in roots[1:]:
            if not _same_value(first, value):
                forbidden.append(f"cost:conflicting_roots:{first_name}:{name}")
        allowed = set(_allowed_alias_keys(_COST_ALIASES))
        allowed.update({"pretrade_broker_net_cost_packet", "broker_net_cost_packet"})
        _unknown_mapping_keys(first, frozenset(allowed), path="cost", forbidden=forbidden)
        result: dict[str, Any] = {}
        for canonical, aliases in _COST_ALIASES.items():
            value = _alias_value(
                first,
                aliases,
                canonical_path=f"cost.{canonical}",
                forbidden=forbidden,
            )
            if value is not None:
                result[canonical] = _canonical_primitive(value)
        packet = _alias_value(
            first,
            ("pretrade_broker_net_cost_packet", "broker_net_cost_packet"),
            canonical_path="cost.pretrade_broker_net_cost_packet",
            forbidden=forbidden,
        )
    else:
        result = {}
        for canonical, aliases in _FLAT_COST_ALIASES.items():
            value = _alias_value(
                event,
                aliases,
                canonical_path=f"cost.{canonical}",
                forbidden=forbidden,
            )
            if value is not None:
                result[canonical] = _canonical_primitive(value)
        packet = _alias_value(
            event,
            ("pretrade_broker_net_cost_packet", "broker_net_cost_packet"),
            canonical_path="cost.pretrade_broker_net_cost_packet",
            forbidden=forbidden,
        )
    if packet is not None:
        if not isinstance(packet, Mapping):
            forbidden.append("cost.pretrade_broker_net_cost_packet:mapping_required")
        else:
            result["pretrade_broker_net_cost_packet"] = _closed_alias_projection(
                packet,
                _COST_PACKET_ALIASES,
                path="cost.pretrade_broker_net_cost_packet",
                forbidden=forbidden,
            )
    if not result:
        missing.append("cost")
        return None
    for field in ("expected_total_cost_r", "source_completeness", "evidence_class"):
        if not _present(result.get(field)) and not (
            field in {"expected_total_cost_r", "source_completeness"}
            and result.get(field) == 0
        ):
            missing.append(f"cost.{field}")
    return result


def _canonical_lifecycle(
    event: Mapping[str, Any],
    *,
    forbidden: list[str],
    missing: list[str],
) -> dict[str, Any] | None:
    roots = [
        (name, event.get(name))
        for name in _CONTEXT_ROOT_ALIASES["lifecycle"]
        if isinstance(event.get(name), Mapping) and event.get(name)
    ]
    if not roots:
        missing.append("lifecycle")
        return None
    first_name, first = roots[0]
    for name, value in roots[1:]:
        if not _same_value(first, value):
            forbidden.append(f"lifecycle:conflicting_roots:{first_name}:{name}")
    allowed = set(_allowed_alias_keys(_LIFECYCLE_ALIASES))
    allowed.update({"same_symbol_lifecycle_v4_packet", "packet"})
    _unknown_mapping_keys(first, frozenset(allowed), path="lifecycle", forbidden=forbidden)
    result: dict[str, Any] = {}
    for canonical, aliases in _LIFECYCLE_ALIASES.items():
        value = _alias_value(
            first,
            aliases,
            canonical_path=f"lifecycle.{canonical}",
            forbidden=forbidden,
        )
        if value is not None:
            result[canonical] = _canonical_primitive(value)
    packet = _alias_value(
        first,
        ("same_symbol_lifecycle_v4_packet", "packet"),
        canonical_path="lifecycle.same_symbol_lifecycle_v4_packet",
        forbidden=forbidden,
    )
    if packet is None and first.get("decision_packet_version") is not None:
        packet = first
    if packet is not None:
        if not isinstance(packet, Mapping):
            forbidden.append("lifecycle.same_symbol_lifecycle_v4_packet:mapping_required")
        else:
            packet_allowed = set(_LIFECYCLE_PACKET_FIELDS)
            if packet is first:
                packet_allowed.update(allowed)
            _unknown_mapping_keys(
                packet,
                frozenset(packet_allowed),
                path="lifecycle.same_symbol_lifecycle_v4_packet",
                forbidden=forbidden,
            )
            canonical_packet = {
                key: _canonical_primitive(packet[key])
                for key in ("action", "reason", "permitted_order_intent", "evidence_class")
                if _present(packet.get(key))
            }
            candidate = packet.get("candidate")
            if candidate is not None:
                if not isinstance(candidate, Mapping):
                    forbidden.append(
                        "lifecycle.same_symbol_lifecycle_v4_packet.candidate:mapping_required"
                    )
                else:
                    canonical_packet["candidate"] = _closed_alias_projection(
                        candidate,
                        _LIFECYCLE_PACKET_CANDIDATE_ALIASES,
                        path="lifecycle.same_symbol_lifecycle_v4_packet.candidate",
                        forbidden=forbidden,
                    )
            result["same_symbol_lifecycle_v4_packet"] = canonical_packet
    for field in (
        "duplicate_exposure",
        "same_symbol_conflict",
        "open_trade_competition_status",
        "source_completeness",
        "evidence_class",
    ):
        if field not in result or result.get(field) in (None, ""):
            missing.append(f"lifecycle.{field}")
    return result


def _runtime_config_projection(
    config: Mapping[str, Any] | None,
    *,
    forbidden: list[str],
    missing: list[str],
) -> dict[str, Any]:
    root = config if isinstance(config, Mapping) else {}
    runtime = root.get("gtos_vnext_runtime")
    if runtime is None:
        runtime = root
    if not isinstance(runtime, Mapping):
        missing.append("config.gtos_vnext_runtime:mapping_required")
        return {}
    projected: dict[str, Any] = {}
    for key, value in runtime.items():
        if not isinstance(key, str):
            forbidden.append("config.gtos_vnext_runtime:non_string_key")
        elif key in _SAFE_RUNTIME_CONFIG_FIELDS:
            projected[key] = _canonical_primitive(value)
        elif key in _UNSAFE_RUNTIME_ENABLE_FIELDS:
            if value is True or (
                isinstance(value, str)
                and value.strip().lower() in {"1", "true", "yes", "enabled", "on"}
            ):
                forbidden.append(f"config.gtos_vnext_runtime.{key}:unsafe_active_policy")
        elif key.startswith("selector_v4_"):
            forbidden.append(f"config.gtos_vnext_runtime.{key}:unrecognized_selector_policy")
        elif key.startswith("ultimate_candidate_package_") or key.startswith(
            "scheduler_v4_best_trade_allocator_selector_"
        ):
            # Inactive legacy policy settings are not part of the truth context.
            continue
    if projected.get("wave21_full_flow_truth_mode_enabled") is not True:
        missing.append("config.gtos_vnext_runtime.wave21_full_flow_truth_mode_enabled:true_required")
    for key in (
        "selector_v4_enabled",
        "selector_v4_apply_to_execution",
        "selector_v4_live_activation_allowed",
    ):
        if key not in projected:
            missing.append(f"config.gtos_vnext_runtime.{key}")
    return projected


def _account_metadata_projection(
    account_metadata: Mapping[str, Any] | None,
    *,
    forbidden: list[str],
) -> dict[str, Any]:
    if account_metadata is None:
        return {}
    if not isinstance(account_metadata, Mapping):
        forbidden.append("account_metadata:mapping_required")
        return {}
    _unknown_mapping_keys(
        account_metadata,
        _ACCOUNT_METADATA_FIELDS,
        path="account_metadata",
        forbidden=forbidden,
    )
    return {
        key: _canonical_primitive(value)
        for key, value in account_metadata.items()
        if key in _ACCOUNT_METADATA_FIELDS
    }


def _context_projection(
    event: Mapping[str, Any],
    config: Mapping[str, Any] | None,
    account_metadata: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str], list[str], list[str]]:
    forbidden: list[str] = []
    missing: list[str] = []
    removed: list[str] = []
    selected = _canonical_selected_cell(event, forbidden=forbidden, missing=missing)
    cost = _canonical_cost(event, forbidden=forbidden, missing=missing)
    lifecycle = _canonical_lifecycle(event, forbidden=forbidden, missing=missing)
    event_projection = {
        **({"selected_cell": selected} if selected is not None else {}),
        **({"cost": cost} if cost is not None else {}),
        **({"lifecycle": lifecycle} if lifecycle is not None else {}),
    }
    config_projection = _runtime_config_projection(
        config,
        forbidden=forbidden,
        missing=missing,
    )
    account_projection = _account_metadata_projection(
        account_metadata,
        forbidden=forbidden,
    )
    for key in event:
        if key in _ACCOUNT_METADATA_FIELDS or key in {
            "balance",
            "equity",
            "open_positions",
        }:
            removed.append(f"event_non_selector_account_state:{key}")
    return (
        event_projection,
        config_projection,
        account_projection,
        removed,
        forbidden,
        missing,
    )


def build_selector_context_input_projection_fields(
    event: Mapping[str, Any],
    config: Mapping[str, Any] | None,
    *,
    account_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        (
            event_projection,
            config_projection,
            account_projection,
            removed,
            forbidden,
            missing,
        ) = _context_projection(event, config, account_metadata)
        digest = selector_order_agnostic_projection_sha256(
            {
                "schema": SELECTOR_CONTEXT_INPUT_PROJECTION_SCHEMA,
                "event_context": event_projection,
                "resolved_runtime_config": config_projection,
                "account_metadata": account_projection,
            }
        )
    except (TypeError, ValueError):
        event_projection = {}
        config_projection = {}
        account_projection = {}
        removed = []
        forbidden = ["selector_context:not_canonical_json_primitives"]
        missing = ["selector_context_input_projection_not_canonical"]
        digest = ""
    valid = bool(digest and not forbidden and not missing)
    return {
        "selector_context_input_projection_schema": SELECTOR_CONTEXT_INPUT_PROJECTION_SCHEMA,
        "selector_context_input_projection_sha256": digest if valid else None,
        "selector_context_input_projection_status": (
            SELECTOR_CONTEXT_INPUT_PROJECTION_STATUS_MATERIALIZED
            if valid
            else "invalid_or_missing_required_inputs"
        ),
        "selector_context_input_projection_source_boundary": (
            SELECTOR_CONTEXT_INPUT_PROJECTION_SOURCE_BOUNDARY
        ),
        "selector_context_event_projection": event_projection,
        "selector_context_resolved_runtime_config_projection": config_projection,
        "selector_context_account_metadata_projection": account_projection,
        "selector_context_removed_non_authoritative_paths": sorted(set(removed)),
        "selector_context_forbidden_or_unknown_paths": sorted(set(forbidden)),
        "selector_context_missing_required_paths": sorted(set(missing)),
    }


def selector_context_input_projection_failures(
    event: Mapping[str, Any],
    config: Mapping[str, Any] | None,
    receipt: Mapping[str, Any],
    *,
    account_metadata: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    if not isinstance(receipt, Mapping):
        return ("selector_context_input_projection_receipt_missing",)
    expected = build_selector_context_input_projection_fields(
        event,
        config,
        account_metadata=account_metadata,
    )
    failures = [
        f"{field}_current_projection_mismatch"
        for field in SELECTOR_CONTEXT_INPUT_PROJECTION_FIELD_NAMES
        if receipt.get(field) != expected.get(field)
    ]
    if expected.get("selector_context_input_projection_status") != (
        SELECTOR_CONTEXT_INPUT_PROJECTION_STATUS_MATERIALIZED
    ):
        failures.append("selector_context_input_projection_current_invalid")
    return tuple(dict.fromkeys(failures))


def selector_truth_sanitized_inputs(
    event: Mapping[str, Any],
    config: Mapping[str, Any] | None,
    *,
    account_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the only event/config pair truth Selector may evaluate."""

    candidate_receipt = build_selector_order_agnostic_input_projection_fields(event)
    context_receipt = build_selector_context_input_projection_fields(
        event,
        config,
        account_metadata=account_metadata,
    )
    valid = bool(
        candidate_receipt["selector_order_agnostic_input_projection_status"]
        == SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_STATUS_MATERIALIZED
        and context_receipt["selector_context_input_projection_status"]
        == SELECTOR_CONTEXT_INPUT_PROJECTION_STATUS_MATERIALIZED
    )
    sanitized_event = None
    sanitized_config = None
    if valid:
        sanitized_event = {
            **deepcopy(
                candidate_receipt["selector_order_agnostic_input_projection"]
            ),
            **deepcopy(context_receipt["selector_context_event_projection"]),
        }
        sanitized_config = {
            "gtos_vnext_runtime": deepcopy(
                context_receipt[
                    "selector_context_resolved_runtime_config_projection"
                ]
            )
        }
    return {
        "status": "materialized" if valid else "not_evaluable",
        "sanitized_event": sanitized_event,
        "sanitized_config": sanitized_config,
        "candidate_projection_receipt": candidate_receipt,
        "context_projection_receipt": context_receipt,
    }


def split_selector_truth_inputs(
    event: Mapping[str, Any],
    resolved_config: Mapping[str, Any] | None,
    *,
    account_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return selector_truth_sanitized_inputs(
        event,
        resolved_config,
        account_metadata=account_metadata,
    )


__all__ = [
    "SELECTOR_CONTEXT_INPUT_PROJECTION_FIELD_NAMES",
    "SELECTOR_CONTEXT_INPUT_PROJECTION_SCHEMA",
    "SELECTOR_CONTEXT_INPUT_PROJECTION_SOURCE_BOUNDARY",
    "SELECTOR_CONTEXT_INPUT_PROJECTION_STATUS_MATERIALIZED",
    "SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_FIELD_NAMES",
    "SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_SCHEMA",
    "SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_SOURCE_BOUNDARY",
    "SELECTOR_ORDER_AGNOSTIC_INPUT_PROJECTION_STATUS_MATERIALIZED",
    "build_selector_context_input_projection_fields",
    "build_selector_order_agnostic_input_projection_fields",
    "project_selector_order_agnostic_inputs",
    "selector_context_input_projection_failures",
    "selector_order_agnostic_input_projection",
    "selector_order_agnostic_input_projection_failures",
    "selector_order_agnostic_projection_sha256",
    "selector_truth_sanitized_inputs",
    "split_selector_truth_inputs",
]
