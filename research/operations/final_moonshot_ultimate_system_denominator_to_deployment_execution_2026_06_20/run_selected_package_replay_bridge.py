#!/usr/bin/env python3
"""Run a route-local selected-package replay bridge from optimized source selections."""

from __future__ import annotations

import argparse
import bisect
import copy
import gc
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import date, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.components import data_ingestion as live_data_ingestion  # noqa: E402
from src.components import market_state as live_market_state  # noqa: E402
from src.components.candidate_geometry import canonicalize_candidate_geometry  # noqa: E402
from src.components.session_namespace import utc_hour_bucket_aliases  # noqa: E402
import src.research_infra.v4_timewarp_simulated_live_research_loop as timewarp_loop  # noqa: E402
from src.research.moonshot_scheduler_v4_best_trade_allocator import (  # noqa: E402
    PACKAGE_NEW_ENTRY_AUTHORITY_DECISION_INPUT_FIELDS,
    PACKAGE_NEW_ENTRY_AUTHORITY_EXECUTION_FILLABILITY_CLASS,
    execution_fillability_source_is_authoritative,
    predecision_execution_fillability_source_boundary_allowed,
    reduced_package_new_entry_authority_validation,
    resolve_execution_fillability_surfaces,
    selected_policy_expected_net_calibration_failure_reason,
    stamp_package_new_entry_authority,
)
from src.research.reduced_risk_action_reason_contract import (  # noqa: E402
    RISK_BEARING_SELECTOR_ACTIONS,
    REDUCED_RISK_SIGNED_NEW_ENTRY_ACTION_INTENTS,
    SCHEDULER_ACTION_INTENT_ALIASES,
    SELECTOR_OPEN_REDUCED_RISK_ALLOWED_ACTION_INTENTS,
    SELECTOR_REDUCE_RISK_ALLOWED_ACTION_INTENTS,
    SOURCE_COMPLETENESS_BLOCKED_STATUS_TOKENS,
    normalize_selector_action_for_reason,
)
from src.research.source_required_lifecycle_authority import (  # noqa: E402
    SOURCE_REQUIRED_REPLAY_OVERRIDE_REASONS,
    source_required_replay_override_applied,
    source_required_replay_override_kind,
    source_required_replay_override_reason,
)
from src.research_infra.v4_timewarp_simulated_live_research_loop import (  # noqa: E402
    CampaignConfig,
    HTF_MIN_TOTAL_ROWS,
    M15_LIVE_LOOKBACK_MIN_TOTAL_ROWS,
    M1_MIN_ROWS_PER_DAY,
    OUTCOME_EVIDENCE_CLASS,
    REPAIRED_PENDING_EXPIRY_MINUTES,
    SOURCE_BOUND_EVIDENCE_CLASS,
    SOURCE_TRUTH_SCOPE,
    ResolvedSource,
    SimulatedBroker,
    SourceSpec,
    file_sha256,
    file_sha256_cached,
    load_config,
    load_csv_rows,
    m1_symbol_day_source_authority,
    rows_by_day,
    run_campaign,
    stable_sha256,
    source_day_authority_with_updates,
    summarize_campaign,
    utc_now,
)

FULL_PACKAGE_SYMBOLS = tuple(timewarp_loop.INCLUDED_SYMBOLS)

ACCEPTANCE_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19"
FILLABILITY_ROUTE = ROOT / "research/operations/final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19"

MATERIALIZER_LEDGER = ROUTE / "REPLAY_EXTENSION_OPTIMIZED_SOURCE_MATERIALIZER_LEDGER.jsonl"
MEMBER_LEDGER = ACCEPTANCE_ROUTE / "FINAL_PACKAGE_SLEEVE_MEMBER_LEDGER.jsonl"
ULTIMATE_PACKAGE_REGISTRY_PATH = ROUTE / "ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl"
LABEL_LEDGER = FILLABILITY_ROUTE / "WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl"
BROKER_COST_PROFILE_PATH = ROOT / "config/profiles/operator_profile.yaml"
RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY_PATH = (
    ROUTE / "RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY.json"
)
RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY_SCHEMA = (
    "gtos.final_moonshot.denominator_to_deployment."
    "reconstructed_proxy_package_selection.summary.v1"
)
RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SOURCE_CONTRACT_SCHEMA = (
    "gtos.final_moonshot.selected_package_replay_bridge."
    "reconstructed_proxy_package_selection_source_contract.v1"
)
RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SEMANTIC_DIGEST_BOUNDARY = (
    "canonical_recursive_json_projection_excluding_generated_timestamps_"
    "and_derived_packet_or_row_hashes"
)
RECONSTRUCTED_PROXY_PACKAGE_SELECTION_VOLATILE_KEYS = frozenset(
    {
        "generated_at_utc",
        "generated_utc",
        "packet_hash_sha256",
        "row_hash_sha256",
    }
)
LIFECYCLE_LABEL_CONTEXT_FIELDS = (
    "pending_lifecycle_v4_state_group",
    "fillability_label_family",
    "fill_no_fill_label",
)
LIFECYCLE_LABEL_CONTEXT_LIST_FIELDS = {
    "pending_lifecycle_v4_state_group": "pending_lifecycle_v4_state_groups",
    "fillability_label_family": "fillability_label_families",
    "fill_no_fill_label": "fill_no_fill_labels",
}
ROUTE_PROVENANCE_FIELDS = (
    "framework",
    "current_framework",
    "origin_family",
    "candidate_origin_family",
    "route_family",
    "route_session",
    "session",
    "session_bucket",
    "setup_family",
    "dynamic_geometry_policy",
)


def reconstructed_proxy_package_selection_semantic_payload(value: Any) -> Any:
    """Remove generated metadata while preserving every economic/gate field."""

    if isinstance(value, Mapping):
        return {
            str(key): reconstructed_proxy_package_selection_semantic_payload(item)
            for key, item in value.items()
            if str(key) not in RECONSTRUCTED_PROXY_PACKAGE_SELECTION_VOLATILE_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [
            reconstructed_proxy_package_selection_semantic_payload(item)
            for item in value
        ]
    return value


def _display_reconstructed_proxy_package_selection_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


@lru_cache(maxsize=16)
def _cached_reconstructed_proxy_package_selection_source_contract(
    path_key: str,
    stat_mtime_ns: int,
    stat_size: int,
) -> dict[str, Any]:
    _ = (stat_mtime_ns, stat_size)
    path = Path(path_key)
    source_path = _display_reconstructed_proxy_package_selection_path(path)
    artifact_sha256 = file_sha256_cached(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {
            "schema": RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SOURCE_CONTRACT_SCHEMA,
            "valid": False,
            "status": "source_artifact_parse_failed",
            "source_path": source_path,
            "source_artifact_sha256": artifact_sha256,
            "source_semantic_sha256": None,
            "semantic_digest_boundary": (
                RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SEMANTIC_DIGEST_BOUNDARY
            ),
            "semantic_digest_excluded_keys": sorted(
                RECONSTRUCTED_PROXY_PACKAGE_SELECTION_VOLATILE_KEYS
            ),
            "failure_reasons": [f"source_artifact_parse_failed:{type(exc).__name__}"],
        }
    if not isinstance(payload, Mapping):
        return {
            "schema": RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SOURCE_CONTRACT_SCHEMA,
            "valid": False,
            "status": "source_artifact_root_not_mapping",
            "source_path": source_path,
            "source_artifact_sha256": artifact_sha256,
            "source_semantic_sha256": None,
            "semantic_digest_boundary": (
                RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SEMANTIC_DIGEST_BOUNDARY
            ),
            "semantic_digest_excluded_keys": sorted(
                RECONSTRUCTED_PROXY_PACKAGE_SELECTION_VOLATILE_KEYS
            ),
            "failure_reasons": ["source_artifact_root_not_mapping"],
        }

    semantic_payload = reconstructed_proxy_package_selection_semantic_payload(payload)
    semantic_sha256 = stable_sha256(semantic_payload)
    failures: list[str] = []
    required_values = {
        "proxy_package_selected_for_replay_evaluation": True,
        "owner_approved_proxy_package_selection": True,
        "local_replay_proxy_package_selection_allowed": True,
        "local_replay_proxy_package_selection_passed": True,
        "selected_package_scope": "full_82_sleeve_proxy_approved_replay_package",
        "live_trading_enabled": False,
        "broker_operation": False,
        "final_package_selected": False,
        "order_calls": 0,
    }
    if payload.get("schema") != RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY_SCHEMA:
        failures.append("source_summary_schema_invalid")
    for field, expected in required_values.items():
        if payload.get(field) != expected:
            failures.append(f"source_summary_{field}_invalid")
    valid = not failures
    return {
        "schema": RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SOURCE_CONTRACT_SCHEMA,
        "valid": valid,
        "status": (
            "semantic_calibration_source_bound"
            if valid
            else "semantic_calibration_source_invalid"
        ),
        "source_path": source_path,
        "source_artifact_sha256": artifact_sha256,
        "source_semantic_sha256": semantic_sha256,
        "source_summary_schema": payload.get("schema"),
        "source_summary_status": payload.get("status"),
        "selected_package_scope": payload.get("selected_package_scope"),
        "semantic_digest_boundary": (
            RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SEMANTIC_DIGEST_BOUNDARY
        ),
        "semantic_digest_excluded_keys": sorted(
            RECONSTRUCTED_PROXY_PACKAGE_SELECTION_VOLATILE_KEYS
        ),
        "failure_reasons": failures,
    }


def reconstructed_proxy_package_selection_source_contract(
    path: Path | str = RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY_PATH,
) -> dict[str, Any]:
    """Bind execution identity to semantic content and retain raw-file provenance."""

    source = Path(path)
    if not source.is_file():
        return {
            "schema": RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SOURCE_CONTRACT_SCHEMA,
            "valid": False,
            "status": "source_artifact_missing",
            "source_path": _display_reconstructed_proxy_package_selection_path(source),
            "source_artifact_sha256": None,
            "source_semantic_sha256": None,
            "semantic_digest_boundary": (
                RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SEMANTIC_DIGEST_BOUNDARY
            ),
            "semantic_digest_excluded_keys": sorted(
                RECONSTRUCTED_PROXY_PACKAGE_SELECTION_VOLATILE_KEYS
            ),
            "failure_reasons": ["source_artifact_missing"],
        }
    stat = source.stat()
    return copy.deepcopy(
        _cached_reconstructed_proxy_package_selection_source_contract(
            str(source.resolve()),
            int(stat.st_mtime_ns),
            int(stat.st_size),
        )
    )
CANONICAL_REPLAY_CONTEXT_ENVELOPE_FIELDS = (
    "timeframe",
    "market_timeframe",
    "decision_timeframe",
    "source_timeframe",
    "asof_utc",
    "scheduler_asof_utc",
    "current_price_asof_utc",
    "source_asof_utc",
    "candle_close_utc",
    "source_candle_time_utc",
    "source_hash",
    "source_sha256",
    "source_hashes_by_timeframe",
    "source_path",
    "source_paths_by_timeframe",
    "same_symbol_replay_exposure_context",
    "same_symbol_replay_exposure_context_source",
    "same_symbol_replay_exposure_context_status",
    "same_symbol_replay_exposure_context_synthesized_empty",
    "same_symbol_lifecycle_exposure_risk_pct",
    "same_side_pending_ids",
    "same_side_pending_order_ids",
    "opposite_pending_ids",
    "opposite_pending_order_ids",
    "same_side_pending_risk_pct",
    "opposite_pending_risk_pct",
    "canonical_replay_context_envelope",
    "canonical_replay_context_envelope_hash_sha256",
    "canonical_replay_context_envelope_shape_hash_sha256",
    "canonical_replay_context_source_boundary",
    "canonical_replay_context_projection_status",
    "replacement_reallocation_quality",
    "replacement_reallocation_quality_score",
    "replacement_reallocation_quality_eligible",
    "replacement_reallocation_quality_hard_gate_failures",
    "replacement_release_quality_score",
    "replacement_release_bonus",
    "replacement_reallocation_base_expected_transfer_score",
    "replacement_reallocation_stop_hazard_status",
    "replacement_reallocation_stop_hazard_quality_penalty",
    "replacement_reallocation_usable_release_candidate_count",
    "replacement_reallocation_selected_release_pending_id",
    "replacement_reallocation_selected_release_reason",
    "replacement_reallocation_used_pending_id_count",
    "replacement_reallocation_quality_source_boundary",
    "replacement_reallocation_quality_uses_outcome_fields",
    "replacement_reallocation_quality_projection_status",
)
EXECUTABLE_GEOMETRY_FIELDS = (
    "entry_price",
    "entry_reference",
    "stop_loss",
    "stop_or_invalidation",
    "take_profit_1",
    "take_profit",
    "target_reference",
    "risk_reward_ratio",
    "trade_parameters",
    "geometry_contract",
    "dynamic_geometry_policy",
    "dynamic_execution_policy_id",
    "canonical_geometry_status",
    "canonical_geometry_source",
    "canonical_geometry_target_recomputed",
)
PACKAGE_AUTHORITY_FIELDS = (
    "package_authority_has_order_geometry",
    "package_authority_order_geometry_status",
    "package_authority_executable_candidate_status",
    "package_new_entry_authority_required",
    "package_new_entry_authority_valid",
    "package_new_entry_authority_status",
    "package_new_entry_authority_failures",
    "package_new_entry_authority_hash_sha256",
    "expected_package_new_entry_authority_hash_sha256",
    "package_new_entry_authority_payload_schema",
    "package_new_entry_authority_scope",
    "package_new_entry_authority_target_action_intent",
    "package_new_entry_authority_authority_field",
    "package_new_entry_authority_authority_family",
    "package_new_entry_authority_source_boundary",
    "package_new_entry_authority_uses_outcome_fields",
    "package_new_entry_authority_candidate_id",
    "package_new_entry_authority_decision_time_utc",
    "package_new_entry_authority_canonical_replay_candidate_instance_key",
    "package_new_entry_authority_source_bound_replay_candidate_instance_key",
    "package_new_entry_authority_candidate_instance_identity_status",
    "package_new_entry_authority_selector_action",
    "package_new_entry_authority_selector_reason",
    "package_new_entry_authority_candidate_decision_quality",
    "package_new_entry_authority_candidate_decision_quality_field_sources",
    "package_new_entry_authority_candidate_decision_quality_source_boundary",
    "package_new_entry_authority_candidate_decision_quality_alias_status",
    "package_new_entry_authority_candidate_decision_quality_alias_mismatches",
    "package_new_entry_authority_candidate_decision_quality_provenance_failures",
    "package_new_entry_authority_candidate_decision_quality_bridge_materialized_fields",
    "package_new_entry_authority_candidate_decision_quality_bridge_materialized_boundary",
    "package_new_entry_authority_entry_quality_fill_probability",
    "package_new_entry_authority_fill_probability",
    "package_new_entry_authority_limit_fillability_probability",
    "package_new_entry_authority_predecision_limit_fillability_probability",
    "package_new_entry_authority_execution_fill_probability",
    "package_new_entry_authority_execution_fill_probability_source",
    "package_new_entry_authority_predecessor_payload_contract",
    "package_new_entry_authority_predecessor_payload",
    "package_new_entry_authority_predecessor_hash_sha256",
    "package_new_entry_authority_predecessor_action_intent",
    "package_new_entry_authority_predecessor_selector_action",
    "package_new_entry_authority_predecessor_selector_reason",
    "package_new_entry_authority_restamp_reason",
    *PACKAGE_NEW_ENTRY_AUTHORITY_DECISION_INPUT_FIELDS,
    *(
        projection_field
        for projection_field, _payload_field in (
            timewarp_loop.PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_PROJECTION_FIELDS
        )
    ),
)
PACKAGE_AUTHORITY_IDENTITY_ROOT_BACKFILLS = {
    "package_new_entry_authority_candidate_id": "candidate_id",
    "package_new_entry_authority_decision_time_utc": "decision_time_utc",
    "package_new_entry_authority_canonical_replay_candidate_instance_key": (
        "canonical_replay_candidate_instance_key"
    ),
    "package_new_entry_authority_source_bound_replay_candidate_instance_key": (
        "source_bound_replay_candidate_instance_key"
    ),
    "package_new_entry_authority_candidate_instance_identity_status": (
        "candidate_instance_identity_status"
    ),
}
PACKAGE_AUTHORITY_EMPTY_LIST_FIELDS = {
    "package_new_entry_authority_failures",
    "package_new_entry_authority_candidate_decision_quality_alias_mismatches",
    "package_new_entry_authority_candidate_decision_quality_provenance_failures",
    "package_new_entry_authority_candidate_decision_quality_bridge_materialized_fields",
}
PACKAGE_REPLAY_AUTHORITY_FIELDS = (
    "package_replay_authority_enabled",
    "source_bound_package_candidate_use_allowed_reason",
    "package_replay_authority_evidence_class",
    "package_replay_result_use_status",
    "package_replay_score",
    "package_replay_source_namespace",
)
PATH_PROVENANCE_FIELDS = (
    "path_source",
    "path_source_timeframe",
    "path_index_timeframe",
    "path_index_source_path",
    "path_index_source_sha256",
    "path_index_rows_returned",
    "path_row_count",
    "path_source_selected_status",
    "path_source_role",
    "path_source_truth_scope",
    "path_source_gaps",
    "source_gaps",
    "postdecision_path_proxy",
    "postdecision_path_proxy_timeframe",
    "postdecision_path_proxy_reason",
    "ordered_tick_truth_satisfied",
    "ordered_tick_truth_oracle_satisfied",
    "ordered_tick_truth_source_satisfied",
    "terminal_r_path_authority",
    "ordered_tick_final_r_authority",
    "m1_proxy_replay_authority",
    "headline_result_authority",
    "headline_result_authority_status",
    "final_r_authority",
    "legacy_final_r_authority_semantics",
)
PATH_PROVENANCE_FIELD_ALIASES = {
    "path_source": ("path_source", "source"),
    "path_source_timeframe": ("path_source_timeframe", "source_timeframe", "timeframe"),
    "path_index_timeframe": ("path_index_timeframe", "source_timeframe", "timeframe"),
    "path_index_source_path": ("path_index_source_path", "source_path"),
    "path_index_source_sha256": ("path_index_source_sha256", "source_sha256"),
    "path_row_count": ("path_row_count", "rows_returned", "source_row_count"),
    "ordered_tick_truth_satisfied": ("ordered_tick_truth_satisfied",),
}

PREFIX = "REPLAY_EXTENSION_SELECTED_PACKAGE_REPLAY_BRIDGE"
PENDING_CREATED_PREFIX = "REPLAY_EXTENSION_PENDING_CREATED_REPLAY_BRIDGE"
REPLAY_DAYS = tuple(f"2026-05-{day:02d}" for day in range(3, 13))
PENDING_CREATED_REPLAY_DAYS = ("2026-06-01", "2026-06-02", "2026-06-03")
PRIMARY_TIMEFRAMES = ("D1", "H4", "H1", "M15", "M1")
TIMEFRAME_FLOORS = {
    "D1": HTF_MIN_TOTAL_ROWS["D1"],
    "H4": HTF_MIN_TOTAL_ROWS["H4"],
    "H1": HTF_MIN_TOTAL_ROWS["H1"],
    "M15": M15_LIVE_LOOKBACK_MIN_TOTAL_ROWS,
    "M1": M1_MIN_ROWS_PER_DAY,
}
PENDING_CREATED_SOURCE_COVERAGE_LEDGER = ROUTE / "REPLAY_EXTENSION_PENDING_CREATED_SOURCE_COVERAGE_LEDGER.jsonl"
ULTIMATE_REPLAY_LOSS_BUCKET_POLICY_ID = "ultimate_candidate_causal_admission_guard_v2"
ULTIMATE_REPLAY_LOSS_BUCKET_GUARD_RULES = (
    {
        "enabled": False,
        "rule_id": "demote_selector_trade_full_admission_uncalibrated",
        "symbol": "*",
        "side": "*",
        "session": "*",
        "selector_action": "trade",
        "selector_reason": "broker_net_probability_confluence_lifecycle_admission_passed",
        "numeric_mixed_count": 0,
        "reason": "diagnostic_only_after_reallocation_regression",
        "demotion_reason": (
            "blocking this full-admission selector class removed a net-negative bucket "
            "but caused worse risk-finalizer replacement selection; keep diagnostic "
            "until reallocation can prove replacement quality does not displace better "
            "reduce-risk rows"
        ),
        "evidence_basis": (
            "BROAD_LIVE_AS_IF_REPLAY_REPLAY_LIFECYCLE_RESOLVER_REPAIR_HOLDOUT_5D_SMOKE "
            "repaired_package_conversion_v3 admitted seven selector trade rows with "
            "this predecision reason for -2.82216188R, but the active-rule smoke "
            "BROAD_LIVE_AS_IF_REPLAY_SELECTOR_FULL_ADMISSION_GUARD_REPAIR_REPAIRED_ONLY_HOLDOUT_5D_SMOKE "
            "fell from +1.40956687R to -1.47512711R because replacements displaced "
            "higher-value reduce-risk rows; do not activate before reallocation repair"
        ),
        "predecision_only_fields": [
            "selector_action",
            "selector_reason",
            "numeric_confluence.mixed_count",
        ],
    },
)


def apply_ultimate_replay_loss_bucket_policy(config: Mapping[str, Any]) -> dict[str, Any]:
    """Enable route-local causal admission repair without broker/live authority."""

    output = copy.deepcopy(config if isinstance(config, Mapping) else {})
    runtime = output.setdefault("gtos_vnext_runtime", {})
    if not isinstance(runtime, dict):
        runtime = {}
        output["gtos_vnext_runtime"] = runtime
    runtime.update(
        {
            "scheduler_v4_best_trade_allocator_live_activation_allowed": False,
            "scheduler_v4_best_trade_allocator_replay_loss_bucket_guard_enabled": True,
            "scheduler_v4_best_trade_allocator_replay_loss_bucket_guard_policy_id": (
                ULTIMATE_REPLAY_LOSS_BUCKET_POLICY_ID
            ),
            "scheduler_v4_best_trade_allocator_replay_loss_bucket_guard_rules": [
                dict(row) for row in ULTIMATE_REPLAY_LOSS_BUCKET_GUARD_RULES
            ],
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_enabled": True,
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_allow_zero_trade_conversion": True,
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_allow_reallocation": True,
            "scheduler_v4_best_trade_allocator_apply_to_execution": True,
            "broad_live_as_if_replay_enforce_broker_cost_packet_status": True,
            "ultimate_candidate_package_enabled": True,
            "ultimate_candidate_package_shadow_enabled": True,
            "ultimate_candidate_package_apply_to_execution": True,
            "ultimate_candidate_package_live_activation_allowed": False,
            "ultimate_candidate_package_final_package_selected": False,
            "ultimate_candidate_package_registry_path": str(ULTIMATE_PACKAGE_REGISTRY_PATH),
            "ultimate_candidate_package_require_shadow_match_for_selector_v4": True,
            "selector_v4_dynamic_router_refusal_action": "reject",
            "ultimate_candidate_package_soften_dynamic_router_refusal_enabled": True,
            "ultimate_candidate_package_soften_dynamic_router_refusal_requires_broker_cost_pass": True,
            "ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families": [
                "structural_distance_extreme",
                "session_open_range_break",
            ],
            "ultimate_candidate_package_dynamic_router_refusal_softening_origin_family_policy": (
                "BROAD_LIVE_AS_IF_REPLAY_LEDGER_TRUTH_REPAIR_SMOKE causal "
                "predecision origin-family repair; selected bridge follows "
                "the broader repaired replay authority instead of preserving "
                "selected-only router-refusal winners from losing families."
            ),
            "scheduler_v4_best_trade_allocator_selected_policy_expected_net_calibration_required_for_new_risk": True,
            "selector_v4_router_refusal_expected_net_policy_calibration_required": True,
            "selected_policy_expected_net_calibration_execution_policy": (
                "repaired_selected_bridge_requires_selected_policy_expected_r_"
                "calibration_for_new_risk_execution; uncalibrated source-bound "
                "expected_net_r remains scoreable/missed but is not filled as "
                "selected-policy executable authority."
            ),
            "ultimate_candidate_package_replay_execution_allowed_sides": [],
            "ultimate_candidate_package_replay_execution_side_policy": (
                "demoted_after_BROAD_LIVE_AS_IF_REPLAY_LEDGER_TRUTH_REPAIR_SMOKE; "
                "selected bridge follows broad repaired replay by keeping side "
                "authority diagnostic until a causal symbol/session/origin/side "
                "rule proves transfer."
            ),
            "selector_v4_calibrated_admission_floor_failure_action": "reject",
            "ultimate_candidate_package_positive_predecision_router_refusal_full_trade_allowed": False,
            "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": True,
            "ultimate_candidate_package_soften_selector_fill_floor_enabled": False,
            "ultimate_candidate_package_soften_selector_fill_floor_repair_reason": (
                "disabled_for_V114C_B3_risk_expression_truth: selected-package "
                "bridge follows broad repaired replay by keeping selector "
                "fill-floor softening scoreable/missed until explicit signed "
                "fillability route authority promotes it."
            ),
            "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled": False,
            "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_demotion_reason": (
                "default-off for V114C_B3: selected-package bridge keeps "
                "below-full-trade broker-net EV as reduce-risk unless a signed "
                "risk ladder explicitly promotes open-reduced replay authority."
            ),
            "ultimate_candidate_package_soften_selector_fill_floor_requires_broker_cost_pass": True,
            "ultimate_candidate_package_soften_selector_fill_floor_requires_positive_predecision_edge": True,
            "selector_v4_package_session_token_authority_enabled": True,
            "ultimate_candidate_package_positive_predecision_off_session_softening_enabled": True,
            "ultimate_candidate_package_positive_predecision_off_session_min_expected_net_r": 0.80,
            "ultimate_candidate_package_positive_predecision_off_session_min_probability": 0.75,
            "ultimate_candidate_package_positive_predecision_off_session_min_fill_probability": 0.70,
            "selector_v4_admission_quality_exact_block_rules_mode": "diagnostic",
            "selector_v4_repaired_profile_soft_fail_status": (
                "dynamic_router_refusal_softens_to_reduced_risk_for_package_admitted_broker_cost_passed_rows"
            ),
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_enabled": True,
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_require_admission": True,
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_score_weight": 0.65,
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_source_r_weight": 0.35,
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_admission_weight": 0.20,
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_max_boost": 2.50,
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_status": (
                "enabled_for_local_replay_authority_requires_package_admission_and_broker_cost_pass"
            ),
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_reserve_release_enabled": True,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_micro_allocation_enabled": True,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_micro_allocation_min_risk_pct": 0.02,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_opening_risk_cap_release_enabled": True,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_opening_risk_cap_release_max_risk_pct": 0.25,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_min_scheduler_score": 1.0,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_min_expected_net_r": 0.60,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_min_probability": 0.58,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_order_cap_release_enabled": True,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_daily_order_cap_release_enabled": True,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_decision_time_order_cap_release_enabled": True,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_immediate_marketable_opening_quality_floor_release_enabled": True,
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_enabled": True,
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_min_scheduler_score": 1.0,
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_min_expected_net_r": 0.80,
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_min_probability": 0.75,
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_min_fill_probability": 0.25,
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_min_source_completeness": 0.95,
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_lifecycle_reconcile_enabled": True,
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_lifecycle_reconcile_min_scheduler_score": 1.0,
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_lifecycle_reconcile_min_expected_net_r": 0.80,
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_lifecycle_reconcile_min_probability": 0.75,
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_lifecycle_reconcile_min_fill_probability": 0.25,
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_lifecycle_reconcile_min_source_completeness": 0.95,
            "scheduler_v4_best_trade_allocator_package_pending_replacement_lifecycle_reconcile_enabled": True,
            "scheduler_v4_best_trade_allocator_package_pending_replacement_lifecycle_reconcile_min_scheduler_score": 1.0,
            "scheduler_v4_best_trade_allocator_package_pending_replacement_lifecycle_reconcile_min_expected_net_r": 0.80,
            "scheduler_v4_best_trade_allocator_package_pending_replacement_lifecycle_reconcile_min_probability": 0.75,
            "scheduler_v4_best_trade_allocator_package_pending_replacement_lifecycle_reconcile_min_fill_probability": 0.25,
            "scheduler_v4_best_trade_allocator_package_pending_replacement_lifecycle_reconcile_min_source_completeness": 0.95,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_authority_enabled": True,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_expected_net_r": 0.70,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_probability": 0.70,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability": 0.45,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness": 0.65,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_router_refusal_package_new_entry_authority_enabled": True,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_release_risk_cap_enabled": True,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_release_max_risk_pct": 0.25,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_enabled": True,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_selector_trade_only": False,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_scheduler_score": 0.0,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_expected_net_r": 0.80,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_probability": 0.75,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_fill_probability": 0.45,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_source_completeness": 0.65,
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_namespace_status": (
                "authoritative_namespace_only_legacy_dynamic_budget_package_fill_floor_bypass_removed"
            ),
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_execution_drag_penalty_enabled": True,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_execution_drag_min_fill_probability": 0.45,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_execution_drag_gap_weight": 1.20,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_execution_drag_cost_weight": 0.80,
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_execution_drag_max_penalty": 0.75,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_enabled": True,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_allowed": True,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_allowed": True,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_router_refusal_immediate_marketable_limit_replay_authority_enabled": True,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_scheduler_score": 3.0,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_expected_net_r": 0.55,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_probability": 0.70,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_fill_probability": 0.80,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_source_completeness": 0.95,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_scheduler_score": 1.0,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_expected_net_r": 0.55,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_probability": 0.70,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_fill_probability": 0.80,
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_source_completeness": 0.95,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled": True,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_reason": (
                "Enable replay-only package authority for source_required_fail_closed "
                "scheduler lifecycle rows after the broad repaired profile proved the "
                "scheduler path requires explicit override materialization. Broker-cost "
                "pass, source-bound package admission, expected-net, probability, "
                "fillability, and source-completeness floors remain required; "
                "source_required_hold and no-same-side new-position conversion remain "
                "disabled until source repair."
            ),
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_expected_net_r": 0.80,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_probability": 0.75,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_fill_probability": 0.12,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_source_completeness": 0.95,
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_allow_new_position_without_same_side_context_enabled": False,
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_enabled": False,
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_expected_net_r": 0.60,
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_probability": 0.72,
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_fill_probability": 0.90,
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_source_completeness": 0.95,
            "scheduler_v4_best_trade_allocator_replay_lifecycle_action_resolver_enabled": True,
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_enabled": True,
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_expected_net_r": 0.80,
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_probability": 0.75,
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_fill_probability": 0.12,
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_source_completeness": 0.95,
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_same_geometry_guard_enabled": True,
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_same_geometry_price_precision": 5,
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_enabled": True,
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_min_scheduler_score": 2.50,
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_min_expected_net_r": 0.80,
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_min_probability": 0.75,
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_min_fill_probability": 0.12,
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_min_source_completeness": 0.95,
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_enabled": True,
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_min_scheduler_score": 0.0,
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_min_expected_net_r": 0.80,
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_min_probability": 0.75,
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_min_fill_probability": 0.12,
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_min_source_completeness": 0.95,
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_opportunity_cost_gate_enabled": True,
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_min_edge_delta": 0.05,
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allow_no_new_position_comparator_authority": False,
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allocation_comparator_enabled": True,
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allocation_transfer_ratio_floor": 0.90,
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allocation_comparator_policy_reason": (
                "Selected-package replay matches broad repaired replay: package "
                "scale-ins must preserve same-cluster allocation quality whenever "
                "an executable independent new-position comparator exists."
            ),
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_opportunity_cost_gate_reason": (
                "Lifecycle-derived package scale-ins are valid replay authority only "
                "when they beat the best executable independent new-position "
                "candidate by a causal predecision edge margin. The lifecycle "
                "authority remains scoreable/missed, but it cannot consume scarce "
                "scheduler headroom merely because package rank boost or same-side "
                "exposure made it executable."
            ),
            "scheduler_v4_best_trade_allocator_same_decision_cluster_burst_guard_enabled": True,
            "scheduler_v4_best_trade_allocator_same_decision_cluster_burst_guard_max_same_direction_new_positions_per_cluster": 1,
            "scheduler_v4_best_trade_allocator_same_decision_cluster_package_extra_slot_enabled": True,
            "scheduler_v4_best_trade_allocator_same_decision_cluster_package_extra_slot_max_same_direction_risk_bearing_orders_per_cluster": 2,
            "scheduler_v4_best_trade_allocator_same_decision_cluster_package_extra_slot_max_total_risk_pct": 0.25,
            "scheduler_v4_best_trade_allocator_same_decision_cluster_package_extra_slot_min_expected_transfer_score": 0.02,
            "scheduler_v4_best_trade_allocator_same_decision_cluster_package_extra_slot_policy_reason": (
                "Selected-package replay matches broad repaired replay: allow a "
                "second same-decision cluster/side package row only after "
                "source-bound package authority, broker-calibrated cost pass, risk "
                "admission, and capped combined cluster-side risk. Broker/live/final "
                "remain closed."
            ),
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled": True,
            "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed": True,
            "replay_order_fillability_policy_v1_enabled": True,
            "replay_order_fillability_policy_v1_require_package_execution_policy": True,
            "replay_order_fillability_policy_v1_fallback_delay_minutes": 30.0,
            "replay_order_fillability_policy_v1_min_candidate_probability": 0.58,
            "replay_order_fillability_policy_v1_min_candidate_ev_r": 0.20,
            "replay_order_fillability_policy_v1_min_candidate_expected_net_r_after_fallback": 0.40,
            "replay_order_fillability_policy_v1_min_fill_probability": 0.60,
            "replay_order_fillability_policy_v1_package_min_fill_probability": 0.25,
            "replay_order_fillability_policy_v1_max_limit_fill_probability_for_fallback": 0.85,
            "replay_order_fillability_policy_v1_allow_open_reduced_risk_guarded_market_fallback": True,
            "replay_order_fillability_policy_v1_allow_passive_limit_queue_for_package_replay": True,
            "replay_order_fillability_policy_v1_require_passive_limit_fallback_envelope": True,
            "scheduler_v4_best_trade_allocator_replay_order_fillability_policy_v1_require_passive_limit_fallback_envelope": True,
            "replay_order_fillability_policy_v1_passive_limit_queue_min_fill_probability": 0.20,
            "replay_order_fillability_policy_v1_allow_high_fill_probability_after_unfilled_probe": False,
            "replay_order_fillability_policy_v1_allow_off_configured_session_guarded_market_fallback": False,
            "replay_order_fillability_policy_v1_min_source_completeness": 0.75,
            "replay_order_fillability_policy_v1_max_expected_cost_r": 0.20,
            "replay_order_fillability_policy_v1_guarded_market_extra_cost_r": 0.05,
            "replay_order_fillability_policy_v1_max_adverse_entry_drift_r": 0.75,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_enabled": True,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout": False,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_package_quality": False,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_fill_floor_authority": True,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_router_refusal_authority": True,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_signed_executable_package_authority": True,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_min_scheduler_score": 3.0,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_min_expected_net_r": 0.70,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_min_probability": 0.70,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_min_fill_probability": 0.80,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_min_source_completeness": 0.95,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_fill_floor_authority_min_scheduler_score": 2.50,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_fill_floor_authority_min_expected_net_r": 0.80,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_fill_floor_authority_min_probability": 0.75,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_fill_floor_authority_min_fill_probability": 0.25,
            "scheduler_v4_best_trade_allocator_package_cooldown_release_fill_floor_authority_min_source_completeness": 0.95,
            "selected_cell_swap_cost_time_stop_bars": 32,
            "selected_cell_swap_cost_minutes_per_bar": 15,
            "profit_harvest_mfe_capture_v4_enabled": True,
            "profit_harvest_mfe_capture_v4_enabled_source": (
                "live_like_profit_preservation_from_ordered_path_mfe_not_live_broker"
            ),
            "profit_harvest_mfe_capture_v4_require_vnext_dynamic_policy": True,
            "profit_harvest_mfe_capture_v4_allow_m1_proxy_final_r_authority": True,
            "profit_harvest_mfe_capture_v4_m1_proxy_final_r_authority_source": (
                "owner_approved_reconstructed_proxy_replay_authority_m1_ordered_path_not_live"
            ),
            "profit_harvest_mfe_capture_v4_min_mfe_r": 0.50,
            "profit_harvest_mfe_capture_v4_stop_activation_mfe_r": 0.50,
            "profit_harvest_mfe_capture_v4_target_activation_fraction": 0.75,
            "profit_harvest_mfe_capture_v4_trail_gap_r": 0.35,
            "profit_harvest_mfe_capture_v4_protect_floor_r": 0.0,
            "profit_harvest_mfe_capture_v4_cost_aware_protect_floor_enabled": True,
            "profit_harvest_mfe_capture_v4_cost_aware_margin_r": 0.02,
            "profit_harvest_mfe_capture_v4_close_on_giveback_r": 0.50,
            "profit_harvest_mfe_capture_v4_armed_stale_close_enabled": True,
            "profit_harvest_mfe_capture_v4_armed_stale_minutes": 30,
            "profit_harvest_mfe_capture_v4_armed_stale_min_mfe_r": 0.50,
            "profit_harvest_mfe_capture_v4_armed_stale_close_below_r": 0.0,
            "profit_harvest_mfe_capture_v4_min_hold_minutes_before_stop_raise": 0,
            "profit_harvest_mfe_capture_v4_stale_minutes": 360,
            "profit_harvest_mfe_capture_v4_stale_min_mfe_r": 0.25,
            "profit_harvest_mfe_capture_v4_stale_close_below_r": 0.0,
        }
    )
    output["ultimate_replay_loss_bucket_policy"] = {
        "policy_id": ULTIMATE_REPLAY_LOSS_BUCKET_POLICY_ID,
        "enabled": True,
        "policy_family": "causal_predecision_admission_calibration_guard",
        "rules": [dict(row) for row in ULTIMATE_REPLAY_LOSS_BUCKET_GUARD_RULES],
        "profit_harvest_overlay": {
            "enabled": True,
            "repair_status": (
                "sub1r_protective_floor_replay_authority_enabled_no_broker_mutation_target_touch_source_gap_safe"
            ),
            "min_mfe_r": 0.50,
            "stop_activation_mfe_r": 0.50,
            "target_activation_fraction": 0.75,
            "trail_gap_r": 0.35,
            "cost_aware_protect_floor_enabled": True,
            "cost_aware_margin_r": 0.02,
            "close_on_giveback_r": 0.50,
            "armed_stale_close_enabled": True,
            "min_hold_minutes_before_stop_raise": 0,
        },
        "live_broker_authority": False,
        "order_calls": 0,
    }
    output["broad_live_as_if_replay_harness"] = {
        "profile": "selected_package_replay_bridge",
        "profile_family": "selected_package_replay_extension",
        "repaired_profile": True,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_authority_fallback_diagnostic": "timewarp_candidate_cost_r_proxy",
        "source_boundary": (
            "selected_package_bridge_no_broker_replay_authority_for_package_policy"
        ),
    }
    return output


def merge_broker_profile_cost_specs(
    base_config: Mapping[str, Any],
    broker_profile: Mapping[str, Any],
) -> dict[str, Any]:
    """Hydrate replay bridge cost authority with the same broker profile as broad replay."""

    output = copy.deepcopy(base_config if isinstance(base_config, Mapping) else {})
    profile_cfg = broker_profile if isinstance(broker_profile, Mapping) else {}
    for key in (
        "broker",
        "broker_profile",
        "broker_account",
        "account",
        "profile_name",
        "runtime",
        "dual_broker",
    ):
        if key in profile_cfg:
            if (
                key == "runtime"
                and isinstance(output.get(key), Mapping)
                and isinstance(profile_cfg.get(key), Mapping)
            ):
                merged_runtime = copy.deepcopy(profile_cfg[key])
                merged_runtime.update(copy.deepcopy(output[key]))
                output[key] = merged_runtime
            else:
                output[key] = copy.deepcopy(profile_cfg[key])
    merged_instruments = copy.deepcopy(profile_cfg.get("instruments") or {})
    base_instruments = (
        base_config.get("instruments")
        if isinstance(base_config.get("instruments"), Mapping)
        else {}
    )
    for symbol, base_row in base_instruments.items():
        if not isinstance(base_row, Mapping):
            continue
        merged_row = merged_instruments.setdefault(str(symbol), {})
        if not isinstance(merged_row, dict):
            merged_row = {}
            merged_instruments[str(symbol)] = merged_row
        for key, value in base_row.items():
            if key == "market" and isinstance(value, Mapping):
                market = copy.deepcopy(merged_row.get("market") or {})
                market.update(copy.deepcopy(value))
                merged_row["market"] = market
            elif key == "risk" and isinstance(value, Mapping):
                risk = copy.deepcopy(merged_row.get("risk") or {})
                for risk_key, risk_value in value.items():
                    risk.setdefault(risk_key, copy.deepcopy(risk_value))
                merged_row["risk"] = risk
            elif key not in merged_row:
                merged_row[key] = copy.deepcopy(value)
    if merged_instruments:
        output["instruments"] = merged_instruments
    output["selected_package_bridge_broker_cost_profile"] = {
        "profile_path": str(BROKER_COST_PROFILE_PATH.relative_to(ROOT)),
        "profile_name": profile_cfg.get("profile_name"),
        "instrument_count": len(merged_instruments),
        "runtime_gate_source": "config/agent_config.yaml",
        "broker_symbol_spec_source": str(BROKER_COST_PROFILE_PATH.relative_to(ROOT)),
        "source_boundary": "selected_package_bridge_uses_broad_replay_broker_calibrated_cost_namespace",
    }
    return output


def build_replay_config() -> dict[str, Any]:
    base_config = load_config(ROOT / "config/agent_config.yaml")
    broker_profile = load_config(BROKER_COST_PROFILE_PATH)
    return apply_ultimate_replay_loss_bucket_policy(
        merge_broker_profile_cost_specs(base_config, broker_profile)
    )


def ledger_files(prefix: str) -> dict[str, str]:
    return {
        "source_hydration": f"{prefix}_SOURCE_HYDRATION_LEDGER.jsonl",
        "progress": f"{prefix}_PROGRESS_LEDGER.jsonl",
        "candidate": f"{prefix}_CANDIDATE_LEDGER.jsonl",
        "compact_candidate": f"{prefix}_COMPACT_CANDIDATE_LEDGER.jsonl",
        "execution_disposition": f"{prefix}_EXECUTION_DISPOSITION_LEDGER.jsonl",
        "scorecard": f"{prefix}_SCORECARD_LEDGER.jsonl",
        "order": f"{prefix}_ORDER_LEDGER.jsonl",
        "trade": f"{prefix}_TRADE_LEDGER.jsonl",
        "filtered_non_executable_order": (
            f"{prefix}_FILTERED_NON_EXECUTABLE_ORDER_LEDGER.jsonl"
        ),
        "filtered_non_executable_trade": (
            f"{prefix}_FILTERED_NON_EXECUTABLE_TRADE_LEDGER.jsonl"
        ),
        "oracle": f"{prefix}_ORDERED_PATH_ORACLE_LEDGER.jsonl",
        "profit_harvest_authority_blocker": (
            f"{prefix}_PROFIT_HARVEST_AUTHORITY_BLOCKER_LEDGER.jsonl"
        ),
        "packet_sidecar": f"{prefix}_PACKET_SIDECAR_LEDGER.jsonl",
        "denominator_bridge": f"{prefix}_DENOMINATOR_BRIDGE_LEDGER.jsonl",
        "label_join": f"{prefix}_LABEL_JOIN_LEDGER.jsonl",
    }


def summary_file(prefix: str) -> str:
    return f"{prefix}_SUMMARY.json"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    tmp_path.write_text(
        json.dumps(data, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp_path, path)


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    tmp_path = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with tmp_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
            count += 1
    os.replace(tmp_path, path)
    return count


def append_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
            count += 1
    return count


def reset_outputs(prefix: str) -> None:
    for filename in ledger_files(prefix).values():
        tmp_path = ROUTE / f".{filename}.tmp-{os.getpid()}"
        if tmp_path.exists():
            tmp_path.unlink()
    summary_tmp = ROUTE / f".{summary_file(prefix)}.tmp-{os.getpid()}"
    if summary_tmp.exists():
        summary_tmp.unlink()


def norm_symbol(value: Any) -> str:
    text = str(value or "").strip()
    upper_text = text.upper()
    alias_map = {
        "NDX100": "NAS100",
        "US30": "US30_cash",
        "US30.CASH": "US30_cash",
        "US30_CASH": "US30_cash",
        "US30CASH": "US30_cash",
        "UKOIL_CASH": "UKOIL_cash",
        "UKOIL.CASH": "UKOIL_cash",
        "UKOILCASH": "UKOIL_cash",
        "USOIL_CASH": "USOIL_cash",
        "USOIL.CASH": "USOIL_cash",
        "USOILCASH": "USOIL_cash",
    }
    return alias_map.get(upper_text, upper_text or text)


def norm_side(value: Any) -> str:
    raw = str(value or "").strip().upper()
    if raw in {"BUY", "BULL", "BULLISH", "LONG", "UP"}:
        return "LONG"
    if raw in {"SELL", "BEAR", "BEARISH", "SHORT", "DOWN"}:
        return "SHORT"
    return raw


def session_variants(value: Any) -> set[str]:
    raw = str(value or "").strip()
    if not raw:
        return {""}
    out = {raw, raw.lower()}
    alias_map = {
        "tokyo": ("tokyo_broad",),
        "tokyo_broad": ("tokyo",),
        "london": ("london_broad",),
        "london_broad": ("london",),
        "ny": ("ny_broad", "new_york"),
        "new_york": ("ny", "ny_broad"),
        "ny_broad": ("ny", "new_york"),
        "off_configured": ("off_configured_session", "off_kz_broad"),
        "off_configured_session": ("off_configured", "off_kz_broad"),
        "off_kz_broad": ("off_configured", "off_configured_session"),
    }
    for candidate in list(out):
        out.update(utc_hour_bucket_aliases(candidate))
        if candidate.startswith("moonshot_h"):
            out.add(candidate.removeprefix("moonshot_"))
        out.update(alias_map.get(candidate, ()))
    if raw.endswith("_broad"):
        out.add(raw.removesuffix("_broad"))
    return out


def family_aliases(value: Any) -> set[str]:
    raw = str(value or "").strip().lower()
    if not raw:
        return {""}
    aliases = {raw}
    if raw.startswith("origin_"):
        aliases.add(raw.removeprefix("origin_"))
    else:
        aliases.add(f"origin_{raw}")
    if raw.startswith("current_"):
        aliases.add(raw.removeprefix("current_"))
    else:
        aliases.add(f"current_{raw}")
    for alias in tuple(aliases):
        if alias.startswith("origin_current_"):
            aliases.add(alias.replace("origin_current_", "current_", 1))
            aliases.add(alias.replace("origin_current_", "origin_", 1))
        if alias.startswith("current_origin_"):
            aliases.add(alias.replace("current_origin_", "origin_", 1))
            aliases.add(alias.replace("current_origin_", "current_", 1))
    return aliases


def framework_origin_variants(candidate: Mapping[str, Any]) -> set[tuple[str, str]]:
    framework = str(candidate.get("framework") or "")
    origin = str(candidate.get("origin_family") or candidate.get("candidate_origin_family") or "")
    framework_values = family_aliases(framework)
    origin_values = family_aliases(origin)
    values = {
        (framework_value, origin_value)
        for framework_value in framework_values
        for origin_value in origin_values
    }
    if framework.startswith("origin_") or origin:
        values.update(("broader_origin", origin_value) for origin_value in origin_values)
    return values


def member_keys(member: Mapping[str, Any]) -> set[tuple[str, str, str, str, str]]:
    framework_values = family_aliases(member.get("framework"))
    origin_values = family_aliases(member.get("origin_family"))
    return {
        (
            framework,
            origin,
            norm_symbol(member.get("symbol")),
            session,
            norm_side(member.get("side")),
        )
        for framework in framework_values
        for origin in origin_values
        for session in session_variants(member.get("session_bucket"))
    }


def candidate_keys(candidate: Mapping[str, Any]) -> set[tuple[str, str, str, str, str]]:
    symbol = norm_symbol(candidate.get("symbol"))
    side = norm_side(candidate.get("side") or candidate.get("direction"))
    sessions = session_variants(candidate.get("session_bucket") or candidate.get("route_session") or candidate.get("session"))
    return {
        (framework, origin, symbol, session, side)
        for framework, origin in framework_origin_variants(candidate)
        for session in sessions
    }


def stable_id(*parts: Any) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]


def member_axis_signature(member: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(member.get("framework") or "unknown_framework"),
        str(member.get("origin_family") or "unknown_origin_family"),
        norm_symbol(member.get("symbol")) or "UNKNOWN",
        str(member.get("session_bucket") or "unknown_session"),
        str(member.get("side") or "UNKNOWN"),
    )


def stable_member_axis_id(member: Mapping[str, Any]) -> str | None:
    existing = str(member.get("stable_member_axis_id") or "").strip()
    if existing:
        return existing
    if member.get("source_axis_row_index") is None:
        return None
    return (
        "member_axis:"
        + stable_id(
            member.get("source_axis_row_index"),
            member.get("sleeve_id"),
            member_axis_signature(member),
        )
    )


def decision_window_id(symbol: Any, side: Any, decision_time: Any) -> str | None:
    if not decision_time:
        return None
    parsed = timewarp_loop.parse_utc(str(decision_time or ""))
    if parsed is not None:
        decision_time = parsed.astimezone(timezone.utc).isoformat()
    return f"decision_window:{norm_symbol(symbol)}:{norm_side(side)}:{decision_time}"


def floor_to_m15_iso(value: Any) -> str | None:
    parsed = timewarp_loop.parse_utc(str(value or ""))
    if parsed is None:
        return None
    parsed = parsed.astimezone(timezone.utc)
    floored_minute = (parsed.minute // 15) * 15
    return parsed.replace(minute=floored_minute, second=0, microsecond=0).isoformat()


def proxy_window_id(symbol: Any, side: Any, pending_floor: Any) -> str | None:
    if not pending_floor:
        return None
    return f"pending_created_window:{norm_symbol(symbol)}:{norm_side(side)}:{pending_floor}"


def selected_file_index(materializer_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("source_path")): row
        for row in materializer_rows
        if row.get("row_type") == "selected_source_file"
    }


def build_source_spec(row: Mapping[str, Any], selected_files: Mapping[str, Mapping[str, Any]]) -> SourceSpec:
    path = Path(str(row.get("selected_source_path") or ""))
    file_row = selected_files.get(str(row.get("selected_source_path") or ""), {})
    return SourceSpec(
        symbol=str(row.get("symbol") or ""),
        mapped_symbol=str(row.get("mapped_symbol") or row.get("symbol") or ""),
        timeframe=str(row.get("timeframe") or "").upper(),
        path=path,
        source_family=Path(str(row.get("selected_manifest_path") or "")).parent.name,
        source_broker=str(file_row.get("source_broker") or "FTMO"),
        source_role=str(file_row.get("source_role") or "owner_authorized_research_hydration"),
        start_utc=str(row.get("required_window_start") or ""),
        end_utc=str(row.get("required_window_end_exclusive") or ""),
        row_count=int(row.get("selected_manifest_rows") or file_row.get("row_count") or 0),
        sha256=str(file_row.get("manifest_sha256") or ""),
        export_tool="scripts/export_mt5_research_ohlcv.py",
        manifest_path=str(row.get("selected_manifest_path") or file_row.get("manifest_path") or ""),
        source_server_hash=None,
        source_account_hash=None,
        source_truth_scope=SOURCE_TRUTH_SCOPE,
        not_redacted_account_native=True,
    )


def load_rows_cached(
    *,
    spec: SourceSpec,
    cache: dict[str, tuple[tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]], str]],
) -> tuple[tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]], str]:
    key = str(spec.path)
    if key not in cache:
        rows = load_csv_rows(spec.path, symbol=spec.symbol)
        cache[key] = (rows, rows_by_day(rows), file_sha256(spec.path))
    return cache[key]


def resolved_htf_source(
    *,
    symbol: str,
    timeframe: str,
    selection_rows: Mapping[tuple[str, str], Mapping[str, Any]],
    selected_files: Mapping[str, Mapping[str, Any]],
    cache: dict[str, tuple[tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]], str]],
) -> tuple[ResolvedSource | None, dict[str, Any]]:
    row = selection_rows.get((symbol, timeframe))
    if not row or row.get("selected") is not True:
        return None, {"symbol": symbol, "timeframe": timeframe, "status": "missing_materializer_selection"}
    spec = build_source_spec(row, selected_files)
    rows, grouped, actual_sha = load_rows_cached(spec=spec, cache=cache)
    min_rows = TIMEFRAME_FLOORS[timeframe]
    sha_ok = bool(spec.sha256 and actual_sha == spec.sha256)
    enough = len(rows) >= min_rows
    status = "selected_optimized_htf_source" if sha_ok and enough else "blocked_htf_source_contract_failed"
    source = None
    if sha_ok and enough:
        source = ResolvedSource(
            spec=spec,
            rows=rows,
            rows_by_day=grouped,
            sha256=actual_sha,
            day_counts={day: len(rows_for_day) for day, rows_for_day in grouped.items()},
            selected_status=status,
            min_required_rows_per_day=min_rows,
        )
    return source, {
        "symbol": symbol,
        "timeframe": timeframe,
        "source_path": str(spec.path),
        "manifest_path": spec.manifest_path,
        "rows": len(rows),
        "min_required_rows": min_rows,
        "sha256": actual_sha,
        "sha256_matches_manifest": sha_ok,
        "status": status,
        "exact_denominator_join_allowed": False,
        "training_use_allowed": False,
        "final_package_selection_allowed": False,
        "selected_package_denominator_use_allowed": False,
    }


def resolved_m1_source(
    *,
    symbol: str,
    replay_days: Iterable[str],
    day_rows: Mapping[tuple[str, str], Mapping[str, Any]],
    m15_source: ResolvedSource | None,
    selected_files: Mapping[str, Mapping[str, Any]],
    cache: dict[str, tuple[tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]], str]],
) -> tuple[ResolvedSource | None, list[dict[str, Any]], list[dict[str, Any]]]:
    merged_rows: list[dict[str, Any]] = []
    grouped_rows: dict[str, tuple[dict[str, Any], ...]] = {}
    component_labels: list[dict[str, Any]] = []
    hydration_rows: list[dict[str, Any]] = []
    day_counts: dict[str, int] = {}
    first_spec: SourceSpec | None = None
    components_for_sha: list[dict[str, Any]] = []
    day_source_authority: dict[str, dict[str, Any]] = {}
    for day in replay_days:
        row = day_rows.get((symbol, day))
        if not row or row.get("selected") is not True:
            m15_day_count = (
                len(m15_source.rows_by_day.get(day, ()))
                if m15_source is not None
                else 0
            )
            authority = source_day_authority_with_updates(
                m1_symbol_day_source_authority(
                    symbol=symbol,
                    trading_day=day,
                    m1_row_count=0,
                    m15_row_count=m15_day_count,
                ),
                status="m1_day_source_selection_missing",
                source_session_status="source_selection_missing",
                diagnostic_fallback_only=True,
                source_gaps=["m1_day_source_selection_missing"],
                path_replay_allowed=False,
                terminal_lifecycle_close_allowed=False,
            )
            day_source_authority[day] = authority
            grouped_rows[day] = ()
            day_counts[day] = 0
            hydration_rows.append(
                {
                    **authority,
                    "status": "missing_day_selection",
                }
            )
            components_for_sha.append(
                {
                    "day": day,
                    "source_day_authority_hash_sha256": authority[
                        "source_day_authority_hash_sha256"
                    ],
                }
            )
            continue
        spec = build_source_spec(row, selected_files)
        first_spec = first_spec or spec
        _rows, grouped, actual_sha = load_rows_cached(spec=spec, cache=cache)
        if spec.sha256 and actual_sha != spec.sha256:
            m15_day_count = (
                len(m15_source.rows_by_day.get(day, ()))
                if m15_source is not None
                else 0
            )
            authority = source_day_authority_with_updates(
                m1_symbol_day_source_authority(
                    symbol=symbol,
                    trading_day=day,
                    m1_row_count=0,
                    m15_row_count=m15_day_count,
                    source_path=str(spec.path),
                    source_family=spec.source_family,
                    source_file_sha256=actual_sha,
                ),
                status="m1_day_source_sha256_mismatch",
                source_session_status="source_integrity_failed",
                diagnostic_fallback_only=True,
                source_gaps=["m1_day_source_sha256_mismatch"],
                path_replay_allowed=False,
                terminal_lifecycle_close_allowed=False,
            )
            day_source_authority[day] = authority
            grouped_rows[day] = ()
            day_counts[day] = 0
            hydration_rows.append(
                {
                    "symbol": symbol,
                    "timeframe": "M1",
                    "trading_day": day,
                    "status": "sha256_mismatch",
                    "source_path": str(spec.path),
                    "manifest_sha256": spec.sha256,
                    "actual_sha256": actual_sha,
                }
            )
            components_for_sha.append(
                {
                    "day": day,
                    "source_day_authority_hash_sha256": authority[
                        "source_day_authority_hash_sha256"
                    ],
                }
            )
            continue
        rows_for_day = grouped.get(day, ())
        m15_day_count = (
            len(m15_source.rows_by_day.get(day, ()))
            if m15_source is not None
            else 0
        )
        authority = m1_symbol_day_source_authority(
            symbol=symbol,
            trading_day=day,
            m1_row_count=len(rows_for_day),
            m15_row_count=m15_day_count,
            source_day_sha256=stable_sha256(rows_for_day),
            source_path=str(spec.path),
            source_family=spec.source_family,
            source_file_sha256=actual_sha,
        )
        day_source_authority[day] = authority
        no_session = authority["status"] == "ftmo_verified_no_session_day"
        merged_rows.extend(rows_for_day)
        grouped_rows[day] = rows_for_day
        day_counts[day] = len(rows_for_day)
        selected_status = str(authority["status"])
        label = {
            "symbol": spec.symbol,
            "mapped_symbol": spec.mapped_symbol,
            "timeframe": spec.timeframe,
            "path": str(spec.path),
            "source_family": spec.source_family,
            "source_broker": spec.source_broker,
            "source_role": spec.source_role,
            "source_truth_scope": spec.source_truth_scope,
            "not_redacted_account_native": spec.not_redacted_account_native,
            "start_utc": spec.start_utc,
            "end_utc": spec.end_utc,
            "row_count": len(rows_for_day),
            "rows": len(rows_for_day),
            "sha256": actual_sha,
            "source_sha256": actual_sha,
            "export_tool": spec.export_tool,
            "manifest_path": spec.manifest_path,
            "selected_status": selected_status,
            "trading_day": day,
            "day_counts": {day: len(rows_for_day)},
            "min_required_rows_per_day": authority.get("effective_min_rows"),
            "source_session_status": authority.get("source_session_status"),
            "expected_rows_for_session_status": authority.get(
                "expected_m1_rows_from_m15_session"
            ),
            "diagnostic_fallback_only": authority.get(
                "diagnostic_fallback_only"
            ),
            "source_gaps": list(authority.get("source_gaps") or ()),
            "source_day_authority_id": authority.get(
                "source_day_authority_id"
            ),
            "source_day_authority_hash_sha256": authority.get(
                "source_day_authority_hash_sha256"
            ),
            "exact_denominator_join_allowed": False,
            "training_use_allowed": False,
            "final_package_selection_allowed": False,
            "selected_package_denominator_use_allowed": False,
        }
        component_labels.append(label)
        hydration_rows.append(
            {
                **label,
                "status": (
                    "accepted_for_replay_bridge"
                    if authority.get("diagnostic_fallback_only") is not True
                    else "diagnostic_only_for_replay_bridge"
                ),
            }
        )
        components_for_sha.append(
            {
                "day": day,
                "path": str(spec.path),
                "sha256": actual_sha,
                "rows": len(rows_for_day),
                "source_day_authority_hash_sha256": authority.get(
                    "source_day_authority_hash_sha256"
                ),
            }
        )
    if first_spec is None:
        return None, hydration_rows, component_labels
    source = ResolvedSource(
        spec=first_spec,
        rows=tuple(merged_rows),
        rows_by_day=grouped_rows,
        sha256=stable_sha256({"symbol": symbol, "timeframe": "M1", "components": components_for_sha}),
        day_counts=day_counts,
        selected_status=(
            "selected_optimized_m1_day_sources_with_symbol_day_scoped_gaps"
            if any(
                row.get("diagnostic_fallback_only") is True
                for row in day_source_authority.values()
            )
            else "selected_optimized_m1_day_sources"
        ),
        min_required_rows_per_day=M1_MIN_ROWS_PER_DAY,
        component_source_labels=tuple(component_labels),
        day_source_authority=day_source_authority,
    )
    return source, hydration_rows, component_labels


def build_sources(
    materializer_rows: list[dict[str, Any]],
    *,
    replay_days: Iterable[str],
) -> tuple[dict[str, dict[str, ResolvedSource]], list[dict[str, Any]], list[dict[str, Any]]]:
    selected_files = selected_file_index(materializer_rows)
    symbol_tf_rows = {
        (str(row.get("symbol")), str(row.get("timeframe"))): row
        for row in materializer_rows
        if row.get("row_type") == "symbol_timeframe_source_selection"
    }
    m1_day_rows = {
        (str(row.get("symbol")), str(row.get("day"))): row
        for row in materializer_rows
        if row.get("row_type") == "m1_day_source_selection"
    }
    symbols = sorted({symbol for symbol, _tf in symbol_tf_rows})
    cache: dict[str, tuple[tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]], str]] = {}
    sources: dict[str, dict[str, ResolvedSource]] = {}
    hydration_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    for symbol in symbols:
        resolved_by_tf: dict[str, ResolvedSource] = {}
        for timeframe in ("D1", "H4", "H1", "M15"):
            source, row = resolved_htf_source(
                symbol=symbol,
                timeframe=timeframe,
                selection_rows=symbol_tf_rows,
                selected_files=selected_files,
                cache=cache,
            )
            hydration_rows.append(row)
            if source is not None:
                resolved_by_tf[timeframe] = source
                manifest_rows.append(
                    {
                        **source.source_label(),
                        "rows_total": len(source.rows),
                        "day_counts": dict(source.day_counts),
                    }
                )
        m1, m1_hydration_rows, m1_manifest_rows = resolved_m1_source(
            symbol=symbol,
            replay_days=replay_days,
            day_rows=m1_day_rows,
            m15_source=resolved_by_tf.get("M15"),
            selected_files=selected_files,
            cache=cache,
        )
        hydration_rows.extend(m1_hydration_rows)
        manifest_rows.extend(m1_manifest_rows)
        if m1 is not None:
            resolved_by_tf["M1"] = m1
        if all(timeframe in resolved_by_tf for timeframe in PRIMARY_TIMEFRAMES):
            sources[symbol] = resolved_by_tf
    return sources, hydration_rows, manifest_rows


def pending_created_source_index(
    coverage_rows: Iterable[Mapping[str, Any]],
) -> dict[tuple[str, str], Mapping[str, Any]]:
    by_symbol_timeframe: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in coverage_rows:
        if row.get("row_type") != "symbol_timeframe_day_coverage":
            continue
        if row.get("coverage_status") != "source_rows_cover_pending_created_day":
            continue
        symbol = norm_symbol(row.get("symbol"))
        timeframe = str(row.get("timeframe") or "").upper()
        if not symbol or not timeframe or not row.get("source_path"):
            continue
        by_symbol_timeframe.setdefault((symbol, timeframe), row)
    return by_symbol_timeframe


def pending_created_source_spec(row: Mapping[str, Any]) -> SourceSpec:
    path = Path(str(row.get("source_path") or ""))
    return SourceSpec(
        symbol=norm_symbol(row.get("symbol")),
        mapped_symbol=norm_symbol(row.get("symbol")),
        timeframe=str(row.get("timeframe") or "").upper(),
        path=path,
        source_family=str(row.get("source_export_dir") or "pending_created_bridge_source"),
        source_broker="FTMO",
        source_role="owner_authorized_research_hydration",
        start_utc=str(row.get("first_timestamp") or ""),
        end_utc=str(row.get("last_timestamp") or ""),
        row_count=int(row.get("rows_scanned") or 0),
        export_tool="scripts/export_mt5_research_ohlcv.py",
        manifest_path=None,
        source_truth_scope=SOURCE_TRUTH_SCOPE,
        not_redacted_account_native=True,
    )


def resolve_pending_created_source(
    *,
    symbol: str,
    timeframe: str,
    coverage_index: Mapping[tuple[str, str], Mapping[str, Any]],
    replay_days: Iterable[str],
    cache: dict[str, tuple[tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]], str]],
    m15_source: ResolvedSource | None = None,
) -> tuple[ResolvedSource | None, list[dict[str, Any]], list[dict[str, Any]]]:
    row = coverage_index.get((symbol, timeframe))
    if not row:
        return None, [
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "status": "missing_pending_created_source_coverage",
                "exact_denominator_join_allowed": False,
                "training_use_allowed": False,
                "final_package_selection_allowed": False,
                "selected_package_denominator_use_allowed": False,
            }
        ], []

    spec = pending_created_source_spec(row)
    rows, grouped, actual_sha = load_rows_cached(spec=spec, cache=cache)
    min_rows = TIMEFRAME_FLOORS[timeframe]
    hydration_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    day_counts = {day: len(grouped.get(day, ())) for day in replay_days}
    missing_days = [day for day, count in day_counts.items() if count <= 0]
    day_source_authority: dict[str, dict[str, Any]] = {}
    if timeframe == "M1":
        for day in replay_days:
            rows_for_day = grouped.get(day, ())
            m15_day_rows = (
                len(m15_source.rows_by_day.get(day, ()))
                if m15_source is not None
                else 0
            )
            day_source_authority[day] = m1_symbol_day_source_authority(
                symbol=symbol,
                trading_day=day,
                m1_row_count=len(rows_for_day),
                m15_row_count=m15_day_rows,
                source_day_sha256=stable_sha256(rows_for_day),
                source_path=str(spec.path),
                source_family=spec.source_family,
                source_file_sha256=actual_sha,
            )
    below_day_floor = [
        day
        for day, authority in day_source_authority.items()
        if authority.get("diagnostic_fallback_only") is True
    ]
    strict_missing_days = missing_days if timeframe != "M1" else []
    if len(rows) < min_rows or strict_missing_days:
        if len(rows) < min_rows:
            status = "rows_below_floor"
        else:
            status = "missing_replay_day_rows"
        hydration_rows.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "source_path": str(spec.path),
                "rows": len(rows),
                "min_required_rows": min_rows,
                "day_counts": day_counts,
                "missing_days": strict_missing_days,
                "below_day_floor": below_day_floor,
                "status": status,
                "exact_denominator_join_allowed": False,
                "training_use_allowed": False,
                "final_package_selection_allowed": False,
                "selected_package_denominator_use_allowed": False,
            }
        )
        return None, hydration_rows, manifest_rows

    source = ResolvedSource(
        spec=spec,
        rows=rows,
        rows_by_day=grouped,
        sha256=actual_sha,
        day_counts=day_counts,
        selected_status=(
            "selected_pending_created_source_coverage_with_symbol_day_scoped_gaps"
            if below_day_floor
            else "selected_pending_created_source_coverage"
        ),
        min_required_rows_per_day=0 if timeframe != "M1" else M1_MIN_ROWS_PER_DAY,
        source_gaps=(),
        day_source_authority=day_source_authority,
    )
    label = {
        **source.source_label(),
        "rows_total": len(rows),
        "day_counts": day_counts,
        "m1_symbol_day_authority_count": len(day_source_authority),
        "m1_symbol_day_diagnostic_count": len(below_day_floor),
        "m1_symbol_day_authority": day_source_authority,
        "source_truth_scope": SOURCE_TRUTH_SCOPE,
        "pending_created_window_truth_status": (
            "source_bound_stable_window_proxy_only_not_recovered_original_decision_time"
        ),
        "exact_denominator_join_allowed": False,
        "training_use_allowed": False,
        "final_package_selection_allowed": False,
        "selected_package_denominator_use_allowed": False,
    }
    manifest_rows.append(label)
    hydration_rows.append(
        {
            **label,
            "status": (
                "accepted_for_pending_created_replay_bridge_with_symbol_day_scoped_gaps"
                if below_day_floor
                else "accepted_for_pending_created_replay_bridge"
            ),
        }
    )
    return source, hydration_rows, manifest_rows


def build_pending_created_sources(
    coverage_rows: list[dict[str, Any]],
    *,
    replay_days: Iterable[str],
    scoped_symbols: Iterable[str],
) -> tuple[dict[str, dict[str, ResolvedSource]], list[dict[str, Any]], list[dict[str, Any]]]:
    coverage_index = pending_created_source_index(coverage_rows)
    cache: dict[str, tuple[tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]], str]] = {}
    sources: dict[str, dict[str, ResolvedSource]] = {}
    hydration_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    for symbol in sorted({norm_symbol(item) for item in scoped_symbols if item}):
        resolved_by_tf: dict[str, ResolvedSource] = {}
        for timeframe in PRIMARY_TIMEFRAMES:
            source, source_hydration_rows, source_manifest_rows = resolve_pending_created_source(
                symbol=symbol,
                timeframe=timeframe,
                coverage_index=coverage_index,
                replay_days=replay_days,
                cache=cache,
                m15_source=resolved_by_tf.get("M15"),
            )
            hydration_rows.extend(source_hydration_rows)
            manifest_rows.extend(source_manifest_rows)
            if source is not None:
                resolved_by_tf[timeframe] = source
        if all(timeframe in resolved_by_tf for timeframe in PRIMARY_TIMEFRAMES):
            sources[symbol] = resolved_by_tf
    return sources, hydration_rows, manifest_rows


PACKAGE_STATUS_JOIN_FIELDS = (
    *PACKAGE_REPLAY_AUTHORITY_FIELDS,
    "ultimate_candidate_package_packet_hash_sha256",
    "ultimate_candidate_package_packet_shape_hash_sha256",
    "candidate_decision_quality",
    "candidate_decision_quality_field_sources",
    "candidate_decision_quality_alias_status",
    "candidate_decision_quality_source_boundary",
    "candidate_decision_quality_alias_mismatches",
    "candidate_decision_quality_provenance_failures",
    "package_new_entry_authority_candidate_decision_quality",
    "package_new_entry_authority_candidate_decision_quality_field_sources",
    "package_new_entry_authority_candidate_decision_quality_source_boundary",
    "package_new_entry_authority_candidate_decision_quality_alias_status",
    "package_new_entry_authority_candidate_decision_quality_alias_mismatches",
    "package_new_entry_authority_candidate_decision_quality_provenance_failures",
    "selected_policy_expected_net_calibration_status",
    "selected_policy_expected_net_r_calibration_status",
    "expected_net_r_selected_policy_calibration_status",
    "selected_policy_expected_net_calibrated",
    "selected_policy_expected_net_calibration_required",
    "selected_policy_expected_net_calibration_source",
    "selected_policy_expected_net_calibration_source_boundary",
    "selected_policy_expected_net_calibration_boundary",
    "selected_policy_expected_net_assumption_hash",
    "selected_policy_expected_net_r_assumption_hash",
    "selected_policy_expected_net_calibration_hash",
    "selected_policy_for_expected_net_r",
    "selected_policy_expected_net_r",
    "selected_policy_probability",
    "selected_policy_source_completeness",
    "selected_policy_quality_alias_status",
    "selected_policy_quality_source_boundary",
    "source_boundary",
    *ROUTE_PROVENANCE_FIELDS,
    *CANONICAL_REPLAY_CONTEXT_ENVELOPE_FIELDS,
    "canonical_replay_candidate_instance_key",
    "risk_finalizer_probe_instance_key",
    "source_bound_replay_candidate_instance_key",
    "candidate_instance_identity_status",
    "source_bound_package_candidate_use_allowed",
    "ultimate_package_source_bound_candidate_use_allowed",
    "ultimate_package_admission_candidate_use_allowed",
    "package_replay_source_bound_candidate_use_allowed",
    "package_replay_candidate_use_allowed",
    "package_replay_executable_candidate_use_allowed",
    "package_replay_executable_candidate_use_allowed_reason",
    "replay_candidate_use_allowed_now",
    "replay_candidate_use_allowed_now_reason",
    "selected_package_candidate_use_allowed_status",
    "ultimate_package_effective_matched_count",
    "ultimate_package_effective_admission_count",
    "ultimate_package_effective_source_bound_signal_r",
    "source_bound_r_additive_allowed",
    "source_bound_r_additive_unit",
    "source_bound_r_additive_scope",
    "ultimate_package_effective_source_bound_r_additive_allowed",
    "ultimate_package_effective_source_bound_r_additive_unit",
    "ultimate_package_effective_source_bound_candidate_use_allowed",
    "ultimate_package_effective_evidence_source",
    "ultimate_package_executable_admission_status",
    "ultimate_package_scheduler_consumed_status",
    "ultimate_package_decision_status",
    "ultimate_package_role_disposition",
    "role_disposition",
    "ultimate_package_matched_sleeve_ids",
    "matched_sleeve_ids",
    "ultimate_package_matched_sleeve_count",
    "matched_sleeve_count",
    "ultimate_package_admission_sleeve_match_count",
    "admission_sleeve_match_count",
    "ultimate_package_non_admission_sleeve_match_count",
    "non_admission_sleeve_match_count",
    "ultimate_package_selector_shadow_score",
    "ultimate_package_combined_source_bound_signal_r_sum",
    "ultimate_package_max_combined_source_bound_signal_r",
    "ultimate_package_source_bound_r_additive_allowed",
    "ultimate_package_source_bound_r_additive_unit",
    "ultimate_package_source_bound_r_additive_scope",
    "ultimate_package_scheduler_parity_evidence_class",
    "ultimate_package_matched_member_axis_count",
    "ultimate_package_admission_member_axis_match_count",
    "ultimate_package_matched_member_axis_ids",
    "selected_package_matched_member_axis_ids",
    "ultimate_package_matched_member_axis_role_counts",
    "ultimate_package_member_axis_source_bound_signal_r_sum",
    "ultimate_package_member_axis_max_source_bound_signal_r",
    "ultimate_package_member_axis_source_bound_r_additive_allowed",
    "ultimate_package_member_axis_source_bound_r_additive_unit",
    "ultimate_package_member_axis_source_bound_r_additive_scope",
    "ultimate_package_member_axis_evidence_class",
    "selected_package_bridge_source_bound_candidate_use_allowed",
    "selected_package_bridge_admission_candidate_use_allowed",
    "scheduler_materialization_action_intent",
    "scheduler_materialization_original_action_intent",
    "scheduler_materialization_selector_action",
    "scheduler_materialization_selector_reason",
    "scheduler_materialization_skip_reason",
    "selector_action",
    "selector_reason",
    "ultimate_candidate_package_open_reduced_risk_authority",
    "package_open_reduced_authority_allowed",
    "package_open_reduced_authority_family",
    "ultimate_package_open_reduced_authority_allowed",
    "pretrade_cost_packet_status",
    "pretrade_cost_refusal_reasons",
    "cost_source_gap_status",
    "cost_authority",
    "execution_cost_authority",
    "candidate_cost_r_fallback_is_authority",
    "source_gap_cost_fallback_blocked",
    "source_bound_signal_r",
    "expected_net_r",
    "candidate_expected_net_r",
    "probability",
    "candidate_probability",
    "confidence",
    "candidate_confidence",
    "fill_probability",
    "candidate_fill_probability",
    "model_limit_fill_probability_prior",
    "fill_probability_authority_class",
    "fill_probability_missing_degraded_default_applied",
    "broker_pretrade_cost_r",
    "broker_calibrated_expected_cost_r",
    "source_completeness",
    "source_completeness_status",
    "source_completeness_source",
    *PACKAGE_AUTHORITY_FIELDS,
    *EXECUTABLE_GEOMETRY_FIELDS,
)

PACKAGE_STATUS_QUALITY_JOIN_FIELDS = (
    "candidate_expected_net_r",
    "expected_net_r",
    "candidate_decision_quality",
    "probability",
    "candidate_probability",
    "confidence",
    "candidate_confidence",
    "fill_probability",
    "candidate_fill_probability",
    "model_limit_fill_probability_prior",
    "fill_probability_authority_class",
    "fill_probability_missing_degraded_default_applied",
)

SCORECARD_NO_FINAL_SELECTION_PREFIX_ONLY_FIELDS = tuple(
    dict.fromkeys(
        (
            *PACKAGE_REPLAY_AUTHORITY_FIELDS,
            *CANONICAL_REPLAY_CONTEXT_ENVELOPE_FIELDS,
            "canonical_replay_candidate_instance_key",
            "risk_finalizer_probe_instance_key",
            "source_bound_replay_candidate_instance_key",
            "candidate_instance_identity_status",
            "source_bound_package_candidate_use_allowed",
            "ultimate_package_source_bound_candidate_use_allowed",
            "ultimate_package_admission_candidate_use_allowed",
            "package_replay_source_bound_candidate_use_allowed",
            "package_replay_candidate_use_allowed",
            "package_replay_executable_candidate_use_allowed",
            "package_replay_executable_candidate_use_allowed_reason",
            "replay_candidate_use_allowed_now",
            "replay_candidate_use_allowed_now_reason",
            "selected_package_candidate_use_allowed_status",
            "selected_package_bridge_source_bound_candidate_use_allowed",
            "selected_package_bridge_admission_candidate_use_allowed",
            "scheduler_materialization_action_intent",
            "scheduler_materialization_original_action_intent",
            "scheduler_materialization_selector_action",
            "scheduler_materialization_selector_reason",
            "scheduler_materialization_skip_reason",
            "selector_action",
            "selector_reason",
            "pretrade_cost_packet_status",
            "pretrade_cost_refusal_reasons",
            "cost_source_gap_status",
            "cost_authority",
            "execution_cost_authority",
            "candidate_cost_r_fallback_is_authority",
            "source_gap_cost_fallback_blocked",
            "source_bound_signal_r",
            "source_bound_r_additive_allowed",
            "source_bound_r_additive_unit",
            "source_bound_r_additive_scope",
            *PACKAGE_AUTHORITY_FIELDS,
            *EXECUTABLE_GEOMETRY_FIELDS,
        )
    )
)

ORDER_TRADE_STATUS_CONFLICT_PRESERVE_FIELDS = (
    *PACKAGE_REPLAY_AUTHORITY_FIELDS,
    "source_bound_package_candidate_use_allowed",
    "ultimate_package_source_bound_candidate_use_allowed",
    "ultimate_package_admission_candidate_use_allowed",
    "package_replay_source_bound_candidate_use_allowed",
    "package_replay_executable_candidate_use_allowed",
    "package_replay_executable_candidate_use_allowed_reason",
    "replay_candidate_use_allowed_now",
    "replay_candidate_use_allowed_now_reason",
    "selected_package_candidate_use_allowed_status",
    "scheduler_materialization_action_intent",
    "scheduler_materialization_original_action_intent",
    "scheduler_materialization_selector_action",
    "scheduler_materialization_selector_reason",
    "scheduler_materialization_skip_reason",
    "selector_action",
    "selector_reason",
    "candidate_decision_quality",
    "selected_policy_expected_net_calibration_status",
    "selected_policy_expected_net_r_calibration_status",
    "expected_net_r_selected_policy_calibration_status",
    "selected_policy_expected_net_calibrated",
    "selected_policy_expected_net_calibration_required",
    "selected_policy_expected_net_calibration_source",
    "selected_policy_expected_net_calibration_source_boundary",
    "selected_policy_expected_net_calibration_boundary",
    "selected_policy_expected_net_assumption_hash",
    "selected_policy_expected_net_r_assumption_hash",
    "selected_policy_expected_net_calibration_hash",
    "selected_policy_for_expected_net_r",
    "selected_policy_expected_net_r",
    "selected_policy_probability",
    "selected_policy_source_completeness",
    "selected_policy_quality_alias_status",
    "selected_policy_quality_source_boundary",
    "pretrade_cost_packet_status",
    "pretrade_cost_refusal_reasons",
    "cost_source_gap_status",
    "cost_authority",
    "execution_cost_authority",
    "broker_pretrade_cost_r",
    "broker_calibrated_expected_cost_r",
    "candidate_cost_r_fallback_is_authority",
    "source_gap_cost_fallback_blocked",
    *PACKAGE_AUTHORITY_FIELDS,
    *EXECUTABLE_GEOMETRY_FIELDS,
    "ultimate_package_role_disposition",
    "role_disposition",
    "ultimate_package_matched_sleeve_ids",
    "matched_sleeve_ids",
    "ultimate_package_matched_sleeve_count",
    "matched_sleeve_count",
    "ultimate_package_admission_sleeve_match_count",
    "admission_sleeve_match_count",
    "ultimate_package_non_admission_sleeve_match_count",
    "non_admission_sleeve_match_count",
)
AUTHORITY_STATUS_CONFLICT_PRESERVE_ROW_TYPES = {"order", "trade", "oracle"}

ORDER_TRADE_STATUS_PROVENANCE_ONLY_FIELDS = {
    "ultimate_package_admission_candidate_use_allowed",
    "selected_policy_expected_net_calibration_status",
    "selected_policy_expected_net_r_calibration_status",
    "expected_net_r_selected_policy_calibration_status",
    "selected_policy_expected_net_calibrated",
    "selected_policy_expected_net_calibration_required",
    "selected_policy_expected_net_calibration_source",
    "selected_policy_expected_net_calibration_source_boundary",
    "selected_policy_expected_net_calibration_boundary",
    "selected_policy_expected_net_assumption_hash",
    "selected_policy_expected_net_r_assumption_hash",
    "selected_policy_expected_net_calibration_hash",
    "selected_policy_for_expected_net_r",
    "selected_policy_expected_net_r",
    "selected_policy_probability",
    "selected_policy_source_completeness",
    "selected_policy_quality_alias_status",
    "selected_policy_quality_source_boundary",
    "candidate_decision_quality",
    "package_new_entry_authority_candidate_decision_quality",
    "package_new_entry_authority_candidate_decision_quality_field_sources",
    "package_new_entry_authority_candidate_decision_quality_source_boundary",
    "package_new_entry_authority_candidate_decision_quality_alias_status",
    "package_new_entry_authority_candidate_decision_quality_alias_mismatches",
    "package_new_entry_authority_candidate_decision_quality_provenance_failures",
}

ORDER_TRADE_REDERIVED_EXECUTABLE_STATUS_FIELDS = {
    "package_replay_executable_candidate_use_allowed",
    "package_replay_executable_candidate_use_allowed_reason",
    "replay_candidate_use_allowed_now",
    "replay_candidate_use_allowed_now_reason",
    "selected_package_candidate_use_allowed_status",
}

ORDER_TRADE_EMPTY_LIST_AUTHORITY_FIELDS = {
    "pretrade_cost_refusal_reasons",
}

STATUS_JOIN_EXECUTABLE_REASON_ALIASES = {
    "broker_cost_and_scheduler_action_executable": "broker_cost_selector_scheduler_executable",
    "broker_cost_selector_and_scheduler_action_executable": "broker_cost_selector_scheduler_executable",
    "risk_bearing_selector_and_broker_cost_passed": "broker_cost_selector_scheduler_executable",
    "broker_pretrade_cost_only": "broker_calibrated_replay_cost_scope",
    "broker_pretrade_plus_guarded_market_fallback_surcharge": (
        "broker_calibrated_replay_cost_scope"
    ),
}

STATUS_JOIN_UNORDERED_LIST_FIELDS = {
    "matched_sleeve_ids",
    "ultimate_package_matched_sleeve_ids",
    "ultimate_package_matched_member_axis_ids",
    "selected_package_matched_member_axis_ids",
    "candidate_decision_quality_alias_mismatches",
    "candidate_decision_quality_provenance_failures",
    "package_new_entry_authority_candidate_decision_quality_alias_mismatches",
    "package_new_entry_authority_candidate_decision_quality_provenance_failures",
}

STATUS_JOIN_EXECUTION_ATTRIBUTION_UNION_FIELDS = {
    "matched_sleeve_ids",
    "ultimate_package_matched_sleeve_ids",
}


def _canonical_status_join_value(field: str, value: Any) -> Any:
    if isinstance(value, str):
        return STATUS_JOIN_EXECUTABLE_REASON_ALIASES.get(value, value)
    if field in STATUS_JOIN_UNORDERED_LIST_FIELDS and isinstance(value, list):
        return sorted(str(item) for item in value)
    return value


def _status_join_values_conflict(field: str, left: Any, right: Any) -> bool:
    return _canonical_status_join_value(field, left) != _canonical_status_join_value(
        field,
        right,
    )


def _order_trade_status_conflict_is_rederived_executable(
    row: Mapping[str, Any],
    status: Mapping[str, Any],
    *,
    field: str,
    current_value: Any,
    status_value: Any,
) -> bool:
    if field not in ORDER_TRADE_REDERIVED_EXECUTABLE_STATUS_FIELDS:
        return False
    if (
        row.get("package_replay_executable_candidate_use_allowed") is False
        or (
            field == "package_replay_executable_candidate_use_allowed"
            and current_value is False
        )
    ):
        return False
    current_executable = bool(
        _truthy(row.get("package_replay_executable_candidate_use_allowed"))
        or (
            row.get("package_replay_executable_candidate_use_allowed") is not False
            and _truthy(row.get("replay_candidate_use_allowed_now"))
        )
        or current_value is True
        or _canonical_status_join_value(field, current_value)
        == "broker_cost_selector_scheduler_executable"
    )
    if not current_executable:
        return False
    status_reason = str(
        status.get("package_replay_executable_candidate_use_allowed_reason")
        or status.get("replay_candidate_use_allowed_now_reason")
        or status.get("selected_package_candidate_use_allowed_status")
        or status_value
        or ""
    ).strip()
    status_text = str(status_value or "").strip()
    stale_status_false = bool(
        (
            status_value is False
            and status_reason
            in {
                "ultimate_package_effective_source_bound_not_allowed",
                "source_bound_package_replay_not_allowed",
            }
        )
        or status_text
        in {
            "ultimate_package_effective_source_bound_not_allowed",
            "source_bound_package_replay_not_allowed",
        }
    )
    if not stale_status_false:
        return False
    source_bound_allowed = any(
        _truthy(row.get(alias))
        for alias in (
            "source_bound_package_candidate_use_allowed",
            "ultimate_package_source_bound_candidate_use_allowed",
            "package_replay_source_bound_candidate_use_allowed",
            "package_source_bound_admission_diagnostic",
        )
    )
    return bool(source_bound_allowed)


def _merged_execution_attribution_list(field: str, left: Any, right: Any) -> list[str] | None:
    if field not in STATUS_JOIN_EXECUTION_ATTRIBUTION_UNION_FIELDS:
        return None
    left_items = stable_unique(list_values(left))
    right_items = stable_unique(list_values(right))
    if not left_items or not right_items:
        return None
    merged = stable_unique(left_items + right_items)
    if set(merged) == set(left_items) == set(right_items):
        return None
    return merged


def _normalized_status_join_key(instance_key: str, row: Mapping[str, Any]) -> str:
    candidate_id, sep, window = str(instance_key or "").partition("@@")
    if not sep or not candidate_id:
        return str(instance_key or "")
    if window.startswith("decision_window:"):
        parts = window.split(":", 3)
        if len(parts) == 4 and parts[3]:
            return f"{candidate_id}@@{parts[3]}"
    decision_time = row.get("decision_time_utc") or row.get("candle_close_utc")
    if decision_time:
        return f"{candidate_id}@@{decision_time}"
    return str(instance_key or "")


SELECTED_SCHEDULER_ALIAS_BACKFILLS = {
    "selected_scheduler_rank": ("scheduler_rank",),
    "selected_scheduler_score": ("scheduler_score",),
    "selected_scheduler_option_status": ("scheduler_option_status",),
    "selected_scheduler_option_reason": ("scheduler_option_reason",),
    "selected_scheduler_action_class": ("scheduler_action_class",),
    "selected_scheduler_symbol": ("symbol", "broker_symbol"),
    "selected_scheduler_side": ("side", "direction"),
    "selected_scheduler_framework": ("framework",),
    "selected_scheduler_current_framework": ("current_framework", "framework"),
    "selected_scheduler_origin_family": (
        "origin_family",
        "candidate_origin_family",
        "framework",
    ),
    "selected_scheduler_candidate_origin_family": (
        "candidate_origin_family",
        "origin_family",
        "framework",
    ),
    "selected_scheduler_route_family": ("route_family", "origin_family"),
    "selected_scheduler_route_session": (
        "route_session",
        "session_bucket",
        "session",
    ),
    "selected_scheduler_session": ("session", "session_bucket", "route_session"),
    "selected_scheduler_session_bucket": (
        "session_bucket",
        "route_session",
        "session",
    ),
    "selected_scheduler_setup_family": ("setup_family",),
    "selected_scheduler_dynamic_geometry_policy": ("dynamic_geometry_policy",),
    "selected_scheduler_requested_risk_pct": (
        "requested_risk_pct",
        "scheduler_requested_risk_pct",
        "selector_requested_risk_pct",
        "risk_per_trade_pct",
    ),
    "selected_scheduler_approved_risk_pct": (
        "approved_risk_pct",
        "scheduler_approved_risk_pct",
    ),
    "selected_scheduler_risk_delta_pct": ("risk_delta_pct", "scheduler_risk_delta_pct"),
    "selected_scheduler_expected_net_r": ("scheduler_expected_net_r", "expected_net_r"),
    "selected_scheduler_probability": ("scheduler_probability", "probability"),
    "selected_scheduler_confidence": ("scheduler_confidence", "confidence"),
    "selected_scheduler_fill_probability": ("scheduler_fill_probability", "fill_probability"),
    "selected_scheduler_source_completeness": (
        "scheduler_source_completeness",
        "source_completeness",
    ),
    "selected_scheduler_source_completeness_status": (
        "scheduler_source_completeness_status",
        "source_completeness_status",
    ),
    "selected_scheduler_selector_action": ("selector_action",),
    "selected_scheduler_selector_reason": ("selector_reason",),
    "selected_scheduler_broker_pretrade_cost_r": (
        "scheduler_broker_pretrade_cost_r",
        "broker_pretrade_cost_r",
        "cost_r",
    ),
    "selected_scheduler_broker_calibrated_expected_cost_r": (
        "scheduler_broker_calibrated_expected_cost_r",
        "broker_calibrated_expected_cost_r",
        "expected_cost_r",
        "cost_r",
    ),
    "selected_scheduler_pretrade_cost_packet_status": ("pretrade_cost_packet_status",),
    "selected_scheduler_pretrade_cost_refusal_reasons": ("pretrade_cost_refusal_reasons",),
    "selected_scheduler_cost_authority": ("cost_authority",),
    "selected_scheduler_cost_source_gap_status": ("cost_source_gap_status",),
    "selected_scheduler_source_bound_signal_r": ("source_bound_signal_r",),
    "selected_scheduler_source_bound_package_candidate_use_allowed": (
        "source_bound_package_candidate_use_allowed",
    ),
    "selected_scheduler_package_replay_source_bound_candidate_use_allowed": (
        "package_replay_source_bound_candidate_use_allowed",
    ),
    "selected_scheduler_package_replay_candidate_use_allowed": (
        "package_replay_candidate_use_allowed",
    ),
    "selected_scheduler_package_replay_authority_enabled": (
        "package_replay_authority_enabled",
    ),
    "selected_scheduler_source_bound_package_candidate_use_allowed_reason": (
        "source_bound_package_candidate_use_allowed_reason",
    ),
    "selected_scheduler_package_replay_authority_evidence_class": (
        "package_replay_authority_evidence_class",
    ),
    "selected_scheduler_package_replay_result_use_status": (
        "package_replay_result_use_status",
    ),
    "selected_scheduler_package_replay_score": ("package_replay_score",),
    "selected_scheduler_package_replay_executable_candidate_use_allowed": (
        "package_replay_executable_candidate_use_allowed",
    ),
    "selected_scheduler_package_replay_executable_candidate_use_allowed_reason": (
        "package_replay_executable_candidate_use_allowed_reason",
    ),
    "selected_scheduler_replay_candidate_use_allowed_now": (
        "replay_candidate_use_allowed_now",
    ),
    "selected_scheduler_replay_candidate_use_allowed_now_reason": (
        "replay_candidate_use_allowed_now_reason",
    ),
    "selected_scheduler_selected_package_candidate_use_allowed_status": (
        "selected_package_candidate_use_allowed_status",
    ),
    "selected_scheduler_ultimate_package_admission_candidate_use_allowed": (
        "ultimate_package_admission_candidate_use_allowed",
    ),
}


def _first_non_missing(row: Mapping[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = row.get(key)
        if not _missing_value(value):
            return value
    return None


def _first_non_missing_with_inputs(
    row: Mapping[str, Any],
    decision_inputs: Mapping[str, Any] | None,
    keys: Iterable[str],
) -> Any:
    decision_inputs = decision_inputs if isinstance(decision_inputs, Mapping) else {}
    for key in keys:
        value = row.get(key)
        if not _missing_value(value):
            return value
        value = decision_inputs.get(key)
        if not _missing_value(value):
            return value
    return None


PACKAGE_ROOT_ALIAS_BACKFILLS = {
    "role_disposition": ("ultimate_package_role_disposition",),
    "ultimate_package_role_disposition": ("role_disposition",),
    "matched_sleeve_ids": ("ultimate_package_matched_sleeve_ids",),
    "ultimate_package_matched_sleeve_ids": ("matched_sleeve_ids",),
    "matched_sleeve_count": ("ultimate_package_matched_sleeve_count",),
    "ultimate_package_matched_sleeve_count": ("matched_sleeve_count",),
    "admission_sleeve_match_count": (
        "ultimate_package_admission_sleeve_match_count",
    ),
    "ultimate_package_admission_sleeve_match_count": (
        "admission_sleeve_match_count",
    ),
    "non_admission_sleeve_match_count": (
        "ultimate_package_non_admission_sleeve_match_count",
    ),
    "ultimate_package_non_admission_sleeve_match_count": (
        "non_admission_sleeve_match_count",
    ),
}


def _backfill_package_root_aliases(row: dict[str, Any]) -> None:
    for target, sources in PACKAGE_ROOT_ALIAS_BACKFILLS.items():
        if not _missing_value(row.get(target)):
            continue
        value = _first_non_missing(row, sources)
        if not _missing_value(value):
            row[target] = value


def _backfill_selected_scheduler_aliases(row: dict[str, Any], *, row_type: str) -> None:
    if row_type not in {"order", "trade"}:
        return
    if _missing_value(row.get("selected_scheduler_primary_candidate_id")):
        candidate_id = _first_non_missing(
            row,
            (
                "selected_candidate_id",
                "candidate_id",
                "row_bound_candidate_id",
                "original_candidate_id",
            ),
        )
        if not _missing_value(candidate_id):
            row["selected_scheduler_primary_candidate_id"] = candidate_id
    if _missing_value(row.get("selected_scheduler_option_count")):
        row["selected_scheduler_option_count"] = (
            1 if not _missing_value(row.get("selected_scheduler_primary_candidate_id")) else 0
        )
    if _missing_value(row.get("selected_scheduler_input_status")):
        row["selected_scheduler_input_status"] = (
            "order_trade_scheduler_alias_backfill"
            if row.get("selected_scheduler_option_count")
            else "missing_selected_scheduler_inputs"
        )
    decision_inputs = row.get("scheduler_candidate_decision_inputs")
    if (
        _missing_value(row.get("selected_scheduler_decision_inputs"))
        and isinstance(decision_inputs, Mapping)
    ):
        row["selected_scheduler_decision_inputs"] = dict(decision_inputs)
    for target, sources in SELECTED_SCHEDULER_ALIAS_BACKFILLS.items():
        if not _missing_value(row.get(target)):
            continue
        value = _first_non_missing_with_inputs(row, decision_inputs, sources)
        if not _missing_value(value):
            row[target] = value


def _canonicalize_order_trade_open_reduced_status_join(
    row: dict[str, Any],
    *,
    row_type: str,
) -> None:
    """Promote exact joined open-reduced authority over stale reduce-risk aliases."""

    if row_type not in {"order", "trade"}:
        return
    action_intent = normalize_bridge_action_intent(
        row.get("scheduler_materialization_action_intent")
        or row.get("action_intent")
        or row.get("lifecycle_action")
        or "new_position"
    )
    normalized_selector_action = normalize_selector_action_for_reason(
        row.get("selector_action"),
        row.get("selector_reason"),
        action_intent,
    )
    joined_selector_action = str(
        row.get("selected_package_status_selector_action") or ""
    ).strip()
    raw_selector_action = str(row.get("selector_action") or "").strip()
    if (
        raw_selector_action != "open-reduced-risk"
        and
        joined_selector_action != "open-reduced-risk"
        and normalized_selector_action != "open-reduced-risk"
    ):
        return
    if not open_reduced_bridge_authority_allowed(row):
        return
    row.setdefault(f"{row_type}_reported_selector_action", row.get("selector_action"))
    row["selector_action_normalized_from_reduce_risk_new_entry"] = True
    row["selector_action_normalization_action_intent"] = action_intent
    if not _missing_value(row.get("selected_package_status_selector_reason")):
        row.setdefault(
            f"{row_type}_reported_selector_reason",
            row.get("selector_reason"),
        )
        row["selector_reason"] = row.get("selected_package_status_selector_reason")
    row["selector_action"] = "open-reduced-risk"
    row["selected_package_status_selector_action_canonicalized_from_exact_join"] = True
    conflicts = row.get("selected_package_candidate_status_join_conflicts")
    if isinstance(conflicts, list):
        stale_open_reduced_authority_conflict_fields = {
            "package_new_entry_authority_hash_sha256",
            "expected_package_new_entry_authority_hash_sha256",
            "package_new_entry_authority_authority_field",
            "package_new_entry_authority_selector_action",
            "package_new_entry_authority_selector_reason",
        }
        kept_conflicts = [
            conflict
            for conflict in conflicts
            if not (
                isinstance(conflict, Mapping)
                and (
                    conflict.get("field") in {"selector_action", "selector_reason"}
                    or (
                        conflict.get("field")
                        in stale_open_reduced_authority_conflict_fields
                        and trusted_signed_package_new_entry_authority_surface(row)
                    )
                )
            )
        ]
        if kept_conflicts:
            row["selected_package_candidate_status_join_conflicts"] = kept_conflicts
        else:
            row.pop("selected_package_candidate_status_join_conflicts", None)
            row.pop(
                "selected_package_candidate_status_join_execution_authority_conflict",
                None,
            )


NON_EXECUTABLE_TERMINAL_STATUS_FIELDS = (
    "order_status",
    "order_submission_status",
    "order_send_status",
    "send_status",
    "fill_status",
    "limit_first_fill_status",
    "execution_manager_replay_admission_status",
    "execution_manager_action",
    "risk_decision",
)
NON_EXECUTABLE_TERMINAL_STATUSES = frozenset(
    {
        "risk_rejected",
        "execution_manager_blocked",
        "guarded_market_fallback_contract_unmet",
        "held_existing_live_candidate_duplicate",
        "source_required_lifecycle_gap_diagnostic_only",
        "not_sent_missed_opportunity",
    }
)
NON_EXECUTABLE_TERMINAL_STATUS_PREFIXES = (
    "not_sent",
    "non_sent",
    "blocked",
    "rejected",
)
NON_EXECUTABLE_TERMINAL_STATUS_SUFFIXES = (
    "_blocked",
    "_rejected",
    "_contract_unmet",
    "_diagnostic_only",
)


def terminal_non_executable_execution_status_reason(
    row: Mapping[str, Any],
) -> str | None:
    """Reject terminal statuses that prove no executable order was sent."""

    for field in NON_EXECUTABLE_TERMINAL_STATUS_FIELDS:
        raw_status = str(row.get(field) or "").strip()
        if not raw_status:
            continue
        status = raw_status.lower().replace("-", "_").replace(" ", "_")
        if (
            status in NON_EXECUTABLE_TERMINAL_STATUSES
            or status.startswith(NON_EXECUTABLE_TERMINAL_STATUS_PREFIXES)
            or status.endswith(NON_EXECUTABLE_TERMINAL_STATUS_SUFFIXES)
        ):
            return f"terminal_non_executable_status:{field}:{status}"
    return None


def _order_trade_terminal_execution_block_reason(row: Mapping[str, Any]) -> str | None:
    terminal_status_reason = terminal_non_executable_execution_status_reason(row)
    if terminal_status_reason:
        return terminal_status_reason
    if row.get("package_replay_executable_candidate_use_allowed") is False:
        return str(
            row.get("package_replay_executable_candidate_use_allowed_reason")
            or "package_replay_executable_candidate_use_allowed_false"
        )
    if (
        bool(row.get("source_required_lifecycle_origin"))
        and row.get("broker_order_lifecycle_truth_satisfied") is not True
    ):
        return "source_required_lifecycle_origin_without_broker_order_lifecycle_truth"
    selector_action = str(row.get("selector_action") or "").strip()
    selector_reason = str(row.get("selector_reason") or "").strip()
    action_intent = str(
        row.get("scheduler_materialization_action_intent")
        or row.get("action_intent")
        or row.get("lifecycle_action")
        or ""
    ).strip()
    normalized_action_intent = normalize_bridge_action_intent(action_intent) or "new_position"
    signed_authority_block_reason = signed_reduced_package_bridge_authority_block_reason(
        row,
        selector_action=selector_action,
        selector_reason=selector_reason,
        action_intent=normalized_action_intent,
    )
    if signed_authority_block_reason:
        return signed_authority_block_reason
    return None


NON_EXECUTABLE_SOURCE_BOUND_R_FIELDS = (
    "ultimate_package_effective_source_bound_signal_r",
    "ultimate_package_combined_source_bound_signal_r_sum",
    "ultimate_package_max_combined_source_bound_signal_r",
    "ultimate_package_member_axis_source_bound_signal_r_sum",
    "ultimate_package_member_axis_max_source_bound_signal_r",
    "package_source_bound_r",
    "source_bound_r",
    "combined_source_bound_signal_r",
    "source_bound_proxy_r",
)


def _demote_non_executable_source_bound_r_fields(
    row: dict[str, Any],
    *,
    reason: str,
    clear_effective_candidate_use: bool = True,
) -> None:
    demoted = False
    for field in NON_EXECUTABLE_SOURCE_BOUND_R_FIELDS:
        source_r = _safe_float_or_none(row.get(field))
        if source_r is None or source_r <= 0.0:
            continue
        row.setdefault(f"diagnostic_{field}", row.get(field))
        row.setdefault(f"missed_opportunity_{field}", row.get(field))
        row[field] = 0.0
        demoted = True
    if not demoted:
        return
    row.setdefault(
        "diagnostic_ultimate_package_effective_source_bound_candidate_use_allowed",
        row.get("ultimate_package_effective_source_bound_candidate_use_allowed"),
    )
    if clear_effective_candidate_use:
        row["ultimate_package_effective_source_bound_candidate_use_allowed"] = False
    row["ultimate_package_effective_source_bound_non_executable"] = True
    row["ultimate_package_effective_source_bound_non_executable_reason"] = reason
    row["ultimate_package_effective_executable_authority_allowed"] = False
    row["ultimate_package_effective_executable_authority_reason"] = reason


def _source_bound_package_use_allowed(row: Mapping[str, Any]) -> bool:
    return any(
        _truthy(row.get(field))
        for field in (
            "source_bound_package_candidate_use_allowed",
            "ultimate_package_source_bound_candidate_use_allowed",
            "package_replay_source_bound_candidate_use_allowed",
            "ultimate_package_effective_source_bound_candidate_use_allowed",
        )
    )


def _executable_package_use_allowed_from_row(row: Mapping[str, Any]) -> bool:
    return any(
        _truthy(row.get(field))
        for field in (
            "package_replay_executable_candidate_use_allowed",
        )
    )


def _non_executable_source_bound_reason(row: Mapping[str, Any]) -> str:
    for field in (
        "package_replay_executable_candidate_use_allowed_reason",
        "replay_candidate_use_allowed_now_reason",
        "selected_package_candidate_use_allowed_status",
        "execution_disposition_reason",
        "scheduler_materialization_skip_reason",
        "order_materialization_authority_block_reason",
        "selected_package_non_executable_order_trade_reason",
    ):
        value = row.get(field)
        if not _missing_value(value):
            reason = str(value).strip()
            if reason:
                return reason
    return "package_replay_executable_candidate_use_allowed_false"


def _enforce_non_executable_source_bound_diagnostic(
    row: dict[str, Any],
    *,
    reason: str | None = None,
) -> None:
    if not _source_bound_package_use_allowed(row):
        return
    if _executable_package_use_allowed_from_row(row):
        return
    non_executable_reason = (
        str(reason).strip()
        if reason is not None and str(reason).strip()
        else _non_executable_source_bound_reason(row)
    )
    _demote_non_executable_source_bound_r_fields(
        row,
        reason=non_executable_reason,
        clear_effective_candidate_use=False,
    )
    row.setdefault(
        "diagnostic_ultimate_package_effective_source_bound_candidate_use_allowed",
        row.get("ultimate_package_effective_source_bound_candidate_use_allowed"),
    )
    row["ultimate_package_effective_source_bound_non_executable"] = True
    row["ultimate_package_effective_source_bound_non_executable_reason"] = (
        non_executable_reason
    )
    row["ultimate_package_effective_executable_authority_allowed"] = False
    row["ultimate_package_effective_executable_authority_reason"] = (
        non_executable_reason
    )


def _backfill_source_bound_diagnostic_contract(row: dict[str, Any]) -> None:
    if _missing_value(
        row.get("diagnostic_ultimate_package_effective_source_bound_signal_r")
    ):
        row["diagnostic_ultimate_package_effective_source_bound_signal_r"] = (
            _safe_float_or_none(
                row.get("ultimate_package_effective_source_bound_signal_r")
            )
            or 0.0
        )
    if _missing_value(
        row.get("diagnostic_ultimate_package_effective_source_bound_candidate_use_allowed")
    ):
        row[
            "diagnostic_ultimate_package_effective_source_bound_candidate_use_allowed"
        ] = bool(
            _truthy(
                row.get("ultimate_package_effective_source_bound_candidate_use_allowed")
            )
        )
    if _missing_value(row.get("ultimate_package_effective_source_bound_non_executable")):
        row["ultimate_package_effective_source_bound_non_executable"] = False
    if _missing_value(
        row.get("ultimate_package_effective_source_bound_non_executable_reason")
    ):
        row["ultimate_package_effective_source_bound_non_executable_reason"] = (
            "package_replay_executable_or_not_source_bound"
        )
    if _missing_value(row.get("ultimate_package_effective_executable_authority_allowed")):
        row["ultimate_package_effective_executable_authority_allowed"] = bool(
            _executable_package_use_allowed_from_row(row)
        )
    if _missing_value(row.get("ultimate_package_effective_executable_authority_reason")):
        if _executable_package_use_allowed_from_row(row):
            row["ultimate_package_effective_executable_authority_reason"] = (
                row.get("package_replay_executable_candidate_use_allowed_reason")
                or row.get("replay_candidate_use_allowed_now_reason")
                or "package_replay_executable_candidate_use_allowed_true"
            )
        else:
            row["ultimate_package_effective_executable_authority_reason"] = (
                _non_executable_source_bound_reason(row)
            )


def _demote_non_executable_effective_source_bound_signal(
    row: dict[str, Any],
    *,
    reason: str,
) -> None:
    _demote_non_executable_source_bound_r_fields(row, reason=reason)


def enforce_order_trade_terminal_execution_authority(
    row: dict[str, Any],
    *,
    row_type: str,
) -> None:
    if row_type not in {"order", "trade"}:
        return
    block_reason = _order_trade_terminal_execution_block_reason(row)
    if not block_reason:
        return
    row["package_replay_candidate_use_allowed"] = False
    row["package_replay_executable_candidate_use_allowed"] = False
    row["package_replay_executable_candidate_use_allowed_reason"] = block_reason
    row["replay_candidate_use_allowed_now"] = False
    row["replay_candidate_use_allowed_now_reason"] = block_reason
    row["selected_package_candidate_use_allowed_status"] = block_reason
    row["selected_package_non_executable_order_trade_diagnostic"] = True
    row["selected_package_non_executable_order_trade_reason"] = block_reason
    row["order_materialization_authority_blocked"] = True
    row["order_materialization_authority_block_reason"] = block_reason
    _demote_non_executable_effective_source_bound_signal(row, reason=block_reason)


def filter_executable_order_trade_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    row_type: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for row in rows:
        out = dict(row)
        enforce_order_trade_terminal_execution_authority(out, row_type=row_type)
        reason = _order_trade_terminal_execution_block_reason(out)
        if reason:
            out[f"{row_type}_filtered_from_executable_ledger"] = True
            out[f"{row_type}_filtered_from_executable_ledger_reason"] = reason
            dropped.append(out)
        else:
            kept.append(out)
    return kept, dropped


def _candidate_id_for_status_join(row: Mapping[str, Any]) -> str:
    return str(
        row.get("candidate_id")
        or row.get("selected_candidate_id")
        or row.get("selected_scheduler_primary_candidate_id")
        or ""
    ).strip()


def _scheduler_status_trace_rows(
    row: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    """Read selected trace plus one complete post/canonical trace surface."""

    rows: list[Mapping[str, Any]] = []
    selected_trace = row.get("selected_scheduler_option_trace")
    if isinstance(selected_trace, list):
        rows.extend(item for item in selected_trace if isinstance(item, Mapping))
    complete_trace = row.get("post_risk_finalizer_scheduler_option_trace")
    if not isinstance(complete_trace, list):
        complete_trace = row.get("scheduler_option_trace")
    if isinstance(complete_trace, list):
        rows.extend(item for item in complete_trace if isinstance(item, Mapping))
    return rows


def _candidate_ids_for_status_join(row: Mapping[str, Any]) -> list[str]:
    ids: list[str] = []
    primary_candidate_id = str(row.get("candidate_id") or "").strip()
    if primary_candidate_id:
        ids.append(primary_candidate_id)
    else:
        for value in (
            row.get("selected_candidate_id"),
            row.get("selected_scheduler_primary_candidate_id"),
        ):
            candidate_id = str(value or "").strip()
            if candidate_id and candidate_id not in ids:
                ids.append(candidate_id)
    for value in (row.get("row_bound_candidate_id"), row.get("original_candidate_id")):
        candidate_id = str(value or "").strip()
        if candidate_id and candidate_id not in ids:
            ids.append(candidate_id)
    for item in _scheduler_status_trace_rows(row):
        candidate_id = str(item.get("candidate_id") or "").strip()
        if candidate_id and candidate_id not in ids:
            ids.append(candidate_id)
    return ids


def _status_join_windows(row: Mapping[str, Any]) -> list[str]:
    windows: list[str] = []

    def add_window(value: Any) -> None:
        window = str(value or "").strip()
        if window and window not in windows:
            windows.append(window)

    add_window(row.get("stable_decision_window_id"))
    add_window(
        decision_window_id(
            row.get("symbol") or row.get("broker_symbol"),
            row.get("side") or row.get("direction"),
            row.get("decision_time_utc")
            or row.get("candle_close_utc")
            or row.get("source_candle_time_utc")
            or row.get("scheduler_asof_utc"),
        )
    )

    selected_ids = set(_candidate_ids_for_status_join(row))
    for item in _scheduler_status_trace_rows(row):
        candidate_id = str(item.get("candidate_id") or "").strip()
        if selected_ids and candidate_id and candidate_id not in selected_ids:
            continue
        add_window(item.get("stable_decision_window_id"))
        add_window(
            decision_window_id(
                item.get("symbol") or item.get("broker_symbol"),
                item.get("side") or item.get("direction"),
                item.get("decision_time_utc")
                or item.get("candle_close_utc")
                or item.get("source_candle_time_utc")
                or item.get("scheduler_asof_utc")
                or row.get("decision_time_utc"),
            )
        )
    return windows


def _candidate_status_instance_key(row: Mapping[str, Any]) -> str:
    candidate_id = _candidate_id_for_status_join(row)
    if not candidate_id:
        return ""
    windows = _status_join_windows(row)
    stable_window = windows[0] if windows else ""
    return f"{candidate_id}@@{stable_window}" if stable_window else ""


def _candidate_status_instance_keys(row: Mapping[str, Any]) -> list[str]:
    keys: list[str] = []
    for field in (
        "canonical_replay_candidate_instance_key",
        "risk_finalizer_probe_instance_key",
        "source_bound_replay_candidate_instance_key",
    ):
        key = str(row.get(field) or "").strip()
        if key and key not in keys:
            keys.append(key)
    for candidate_id in _candidate_ids_for_status_join(row):
        for decision_time in (
            row.get("decision_time_utc"),
            row.get("candle_close_utc"),
            row.get("source_candle_time_utc"),
            row.get("scheduler_asof_utc"),
        ):
            key = _candidate_time_instance_key(candidate_id, decision_time)
            if key and key not in keys:
                keys.append(key)
    for candidate_id in _candidate_ids_for_status_join(row):
        for window in _status_join_windows(row):
            key = f"{candidate_id}@@{window}"
            if key not in keys:
                keys.append(key)
    return keys


def _candidate_status_lookup_keys(row: Mapping[str, Any]) -> list[str]:
    candidate_id = str(row.get("candidate_id") or "").strip()
    if not candidate_id:
        return []
    keys: list[str] = []
    for field in (
        "canonical_replay_candidate_instance_key",
        "risk_finalizer_probe_instance_key",
        "source_bound_replay_candidate_instance_key",
    ):
        key = str(row.get(field) or "").strip()
        if key and key not in keys:
            keys.append(key)
    for decision_time in (
        row.get("decision_time_utc"),
        row.get("candle_close_utc"),
        row.get("source_candle_time_utc"),
        row.get("scheduler_asof_utc"),
    ):
        key = _candidate_time_instance_key(candidate_id, decision_time)
        if key and key not in keys:
            keys.append(key)
    for window in _status_join_windows(row):
        key = f"{candidate_id}@@{window}"
        if key not in keys:
            keys.append(key)
    return keys


def build_candidate_status_lookup(
    compact_rows: Iterable[Mapping[str, Any]],
) -> dict[str, list[Mapping[str, Any]]]:
    rows = [row for row in compact_rows if str(row.get("candidate_id") or "").strip()]
    lookup: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        for instance_key in _candidate_status_lookup_keys(row):
            lookup[instance_key].append(row)
    return lookup


def _status_num(row: Mapping[str, Any], *fields: str) -> float:
    for field in fields:
        value = row.get(field)
        if _missing_value(value):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return 0.0


def _first_present(*values: Any) -> Any:
    for value in values:
        if not _missing_value(value):
            return value
    return None


def candidate_decision_quality_envelope(fields: Mapping[str, Any]) -> dict[str, Any]:
    """Canonical nested quality object; flat fields remain compatibility API."""

    existing = _mapping(fields.get("candidate_decision_quality"))
    envelope = dict(existing)
    scalar_aliases = {
        "expected_net_r": ("expected_net_r", "candidate_expected_net_r"),
        "candidate_expected_net_r": ("candidate_expected_net_r", "expected_net_r"),
        "probability": ("probability", "candidate_probability"),
        "candidate_probability": ("candidate_probability", "probability"),
        "confidence": ("confidence", "candidate_confidence", "scheduler_confidence"),
        "candidate_confidence": (
            "candidate_confidence",
            "confidence",
            "scheduler_confidence",
        ),
        "fill_probability": ("fill_probability", "candidate_fill_probability"),
        "candidate_fill_probability": ("candidate_fill_probability", "fill_probability"),
        "source_completeness": (
            "source_completeness",
            "candidate_source_completeness",
        ),
        "source_completeness_status": (
            "source_completeness_status",
            "candidate_source_completeness_status",
        ),
        "expected_cost_r": (
            "expected_cost_r",
            "predecision_expected_cost_r",
            "cost_total_r",
            "cost_r",
        ),
        "cost_total_r": ("cost_total_r", "expected_cost_r", "cost_r"),
        "cost_r": ("cost_r", "expected_cost_r", "cost_total_r"),
        "source_boundary": (
            "source_boundary",
            "candidate_decision_quality_source_boundary",
        ),
        "selected_policy_for_expected_net_r": (
            "selected_policy_for_expected_net_r",
            "expected_net_r_selected_policy",
        ),
        "selected_policy_expected_net_r": (
            "selected_policy_expected_net_r",
            "expected_net_r",
            "candidate_expected_net_r",
        ),
        "selected_policy_probability": (
            "selected_policy_probability",
            "probability",
            "candidate_probability",
        ),
        "selected_policy_source_completeness": (
            "selected_policy_source_completeness",
            "source_completeness",
            "candidate_source_completeness",
        ),
        "selected_policy_quality_alias_status": (
            "selected_policy_quality_alias_status",
        ),
        "selected_policy_quality_source_boundary": (
            "selected_policy_quality_source_boundary",
            "candidate_decision_quality_source_boundary",
            "source_boundary",
        ),
        "selected_policy_expected_net_calibration_status": (
            "selected_policy_expected_net_calibration_status",
            "selected_policy_expected_net_r_calibration_status",
        ),
        "selected_policy_expected_net_calibrated": (
            "selected_policy_expected_net_calibrated",
        ),
        "selected_policy_expected_net_calibration_required": (
            "selected_policy_expected_net_calibration_required",
        ),
        "selected_policy_expected_net_calibration_source": (
            "selected_policy_expected_net_calibration_source",
            "selected_policy_expected_net_r_calibration_source",
        ),
        "selected_policy_expected_net_calibration_source_boundary": (
            "selected_policy_expected_net_calibration_source_boundary",
            "selected_policy_expected_net_calibration_boundary",
        ),
        "selected_policy_expected_net_assumption_hash": (
            "selected_policy_expected_net_assumption_hash",
            "selected_policy_expected_net_r_assumption_hash",
            "selected_policy_expected_net_calibration_hash",
        ),
    }
    for out_key, candidates in scalar_aliases.items():
        value = _first_present(*(fields.get(key) for key in candidates))
        if not _missing_value(value):
            envelope[out_key] = value
    field_sources = (
        _mapping(fields.get("candidate_decision_quality_field_sources"))
        or _mapping(fields.get("field_sources"))
        or _mapping(envelope.get("field_sources"))
    )
    if field_sources:
        envelope["field_sources"] = dict(field_sources)
        envelope["candidate_decision_quality_field_sources"] = dict(field_sources)
    for out_key, candidates in {
        "alias_status": ("candidate_decision_quality_alias_status", "alias_status"),
        "alias_mismatches": (
            "candidate_decision_quality_alias_mismatches",
            "alias_mismatches",
        ),
        "provenance_failures": (
            "candidate_decision_quality_provenance_failures",
            "provenance_failures",
        ),
        "source_boundary": (
            "candidate_decision_quality_source_boundary",
            "source_boundary",
        ),
    }.items():
        value = _first_present(*(fields.get(key) for key in candidates))
        if not _missing_value(value):
            envelope[out_key] = list(value) if isinstance(value, tuple) else value
            if out_key == "source_boundary":
                envelope["candidate_decision_quality_source_boundary"] = value
    return {
        key: value
        for key, value in envelope.items()
        if not _missing_value(value)
    }


def _candidate_status_window_sort_key(row: Mapping[str, Any]) -> tuple[float, ...]:
    executable = 1.0 if _truthy(row.get("package_replay_executable_candidate_use_allowed")) else 0.0
    replay_allowed = 1.0 if _truthy(row.get("package_replay_candidate_use_allowed")) else 0.0
    source_allowed = 1.0 if _truthy(row.get("source_bound_package_candidate_use_allowed")) else 0.0
    return (
        executable,
        replay_allowed,
        source_allowed,
        _status_num(
            row,
            "expected_net_r",
            "candidate_expected_net_r",
            "ev_r",
            "candidate_ev_r",
        ),
        _status_num(row, "probability", "candidate_probability"),
        _status_num(row, "fill_probability", "candidate_fill_probability"),
        _status_num(row, "source_completeness"),
        _status_num(
            row,
            "ultimate_package_effective_source_bound_signal_r",
            "ultimate_package_combined_source_bound_signal_r_sum",
            "source_bound_signal_r",
        ),
    )


def build_candidate_status_window_lookup(
    compact_rows: Iterable[Mapping[str, Any]],
) -> dict[str, list[Mapping[str, Any]]]:
    lookup: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in compact_rows:
        if not isinstance(row, Mapping):
            continue
        for window in _status_join_windows(row):
            lookup[window].append(row)
    for window, rows in list(lookup.items()):
        lookup[window] = sorted(rows, key=_candidate_status_window_sort_key, reverse=True)
    return lookup


def _join_window_candidate_status_diagnostic(
    row: dict[str, Any],
    *,
    row_type: str,
    row_windows: Sequence[str],
    candidate_status_by_window: Mapping[str, list[Mapping[str, Any]]] | None,
) -> bool:
    if row_type != "scorecard" or not row_windows or not candidate_status_by_window:
        return False
    if _scorecard_has_final_selected_candidate(row):
        return False
    window_matches: list[Mapping[str, Any]] = []
    for window in row_windows:
        for item in candidate_status_by_window.get(window) or []:
            if isinstance(item, Mapping):
                window_matches.append(item)
    if not window_matches:
        return False
    best = sorted(window_matches, key=_candidate_status_window_sort_key, reverse=True)[0]
    row["selected_package_window_candidate_status_joined"] = True
    row["selected_package_window_candidate_status_source_boundary"] = (
        "diagnostic_window_package_candidate_status_not_selected_execution_authority"
    )
    row["selected_package_window_candidate_count"] = len(window_matches)
    row["selected_package_window_candidate_windows"] = list(row_windows)
    row["selected_package_window_best_candidate_id"] = best.get("candidate_id")
    row["selected_package_window_best_expected_net_r"] = _first_present(
        best.get("expected_net_r"),
        best.get("candidate_expected_net_r"),
        best.get("ev_r"),
        best.get("candidate_ev_r"),
    )
    row["selected_package_window_best_probability"] = _first_present(
        best.get("probability"),
        best.get("candidate_probability"),
    )
    row["selected_package_window_best_fill_probability"] = _first_present(
        best.get("fill_probability"),
        best.get("candidate_fill_probability"),
    )
    row["selected_package_window_best_source_completeness"] = best.get(
        "source_completeness"
    )
    row["selected_package_window_best_package_replay_candidate_use_allowed"] = best.get(
        "package_replay_candidate_use_allowed"
    )
    row["selected_package_window_best_package_replay_executable_candidate_use_allowed"] = (
        best.get("package_replay_executable_candidate_use_allowed")
    )
    row["selected_package_window_best_package_replay_executable_candidate_use_allowed_reason"] = (
        best.get("package_replay_executable_candidate_use_allowed_reason")
    )
    row["selected_package_window_best_matched_sleeve_ids"] = stable_unique(
        list_values(best.get("ultimate_package_matched_sleeve_ids"))
        + list_values(best.get("matched_sleeve_ids"))
    )
    row["selected_package_window_best_matched_member_axis_ids"] = stable_unique(
        list_values(best.get("ultimate_package_matched_member_axis_ids"))
        + list_values(best.get("matched_stable_member_axis_ids"))
    )
    row["selected_package_window_best_packet_sidecar_id"] = best.get(
        "packet_sidecar_id"
    )
    row["selected_package_window_best_packet_sidecar_hash_sha256"] = best.get(
        "packet_sidecar_hash_sha256"
    )
    row["selected_package_window_best_ultimate_candidate_package_packet_hash_sha256"] = (
        best.get("ultimate_candidate_package_packet_hash_sha256")
    )
    row["selected_package_window_best_ultimate_candidate_package_packet_shape_hash_sha256"] = (
        best.get("ultimate_candidate_package_packet_shape_hash_sha256")
    )
    return True


def _join_candidate_status(
    row: dict[str, Any],
    *,
    row_type: str,
    candidate_status_by_id: Mapping[str, Any] | None,
    candidate_status_by_window: Mapping[str, list[Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    if not candidate_status_by_id:
        envelope = candidate_decision_quality_envelope(row)
        if envelope:
            row["candidate_decision_quality"] = envelope
        return row
    candidate_ids = _candidate_ids_for_status_join(row)
    row_windows = _status_join_windows(row)
    status: Mapping[str, Any] | None = None
    join_key = ""
    rejected_join_candidate_ids: list[str] = []
    duplicate_join_keys: list[str] = []
    for instance_key in _candidate_status_instance_keys(row):
        raw_matches = candidate_status_by_id.get(instance_key)
        if isinstance(raw_matches, Mapping):
            candidate_status_matches = [raw_matches]
        elif isinstance(raw_matches, list):
            candidate_status_matches = [
                item for item in raw_matches if isinstance(item, Mapping)
            ]
        else:
            candidate_status_matches = []
        if len(candidate_status_matches) > 1:
            duplicate_join_keys.append(instance_key)
            continue
        candidate_status = (
            candidate_status_matches[0] if candidate_status_matches else None
        )
        status_candidate_id = (
            _candidate_id_for_status_join(candidate_status)
            if isinstance(candidate_status, Mapping)
            else ""
        )
        if (
            isinstance(candidate_status, Mapping)
            and (not candidate_ids or status_candidate_id in candidate_ids)
        ):
            status = candidate_status
            join_key = instance_key
            break
        if status_candidate_id and status_candidate_id not in rejected_join_candidate_ids:
            rejected_join_candidate_ids.append(status_candidate_id)
    if not isinstance(status, Mapping):
        row["selected_package_candidate_status_joined"] = False
        window_diagnostic_joined = _join_window_candidate_status_diagnostic(
            row,
            row_type=row_type,
            row_windows=row_windows,
            candidate_status_by_window=candidate_status_by_window,
        )
        if duplicate_join_keys:
            row["selected_package_candidate_status_join_status"] = (
                "selected_package_candidate_status_join_duplicate_ambiguous"
            )
            row["selected_package_candidate_status_join_duplicate_keys"] = (
                duplicate_join_keys
            )
        elif row_windows:
            row["selected_package_candidate_status_join_status"] = (
                "selected_package_candidate_status_join_exact_missing_with_window_diagnostic"
                if window_diagnostic_joined
                else "selected_package_candidate_status_join_exact_missing"
            )
            row["selected_package_candidate_status_join_required_windows"] = row_windows
        elif candidate_ids:
            row["selected_package_candidate_status_join_status"] = (
                "selected_package_candidate_status_join_window_missing"
            )
        if rejected_join_candidate_ids:
            row["selected_package_candidate_status_join_rejected_candidate_ids"] = (
                rejected_join_candidate_ids
            )
        envelope = candidate_decision_quality_envelope(row)
        if envelope:
            row["candidate_decision_quality"] = envelope
        return row
    normalized_join_key = _normalized_status_join_key(join_key, row)
    row["selected_package_candidate_status_joined"] = True
    row["selected_package_candidate_status_lookup_key"] = join_key
    row["selected_package_candidate_status_join_key"] = normalized_join_key or join_key
    row["selected_package_candidate_status_join_status"] = "exact_candidate_window_join"
    row["selected_package_candidate_status_join_candidate_id"] = _candidate_id_for_status_join(status)
    if normalized_join_key and normalized_join_key != join_key:
        row["selected_package_candidate_status_join_key_canonical_equivalent"] = True
    scorecard_without_final_selection = (
        row_type == "scorecard"
        and not _scorecard_has_final_selected_candidate(row)
    )
    if row_type == "scorecard":
        status_window = status.get("stable_decision_window_id")
        current_window = row.get("stable_decision_window_id")
        if (
            not _missing_value(status_window)
            and str(status_window).startswith("decision_window:")
            and status_window != current_window
        ):
            row.setdefault("scheduler_stable_decision_window_id", current_window)
            row["stable_decision_window_id"] = status_window
    status_join_conflicts: list[dict[str, Any]] = []
    for field in PACKAGE_STATUS_JOIN_FIELDS:
        if field in PACKAGE_STATUS_QUALITY_JOIN_FIELDS:
            continue
        value = status.get(field)
        if not _missing_value(value):
            if (
                scorecard_without_final_selection
                and field in SCORECARD_NO_FINAL_SELECTION_PREFIX_ONLY_FIELDS
            ):
                row[f"selected_package_status_{field}"] = value
                continue
            current_value = row.get(field)
            current_value_authoritative = not _missing_value(current_value)
            if (
                row_type in AUTHORITY_STATUS_CONFLICT_PRESERVE_ROW_TYPES
                and field in ORDER_TRADE_EMPTY_LIST_AUTHORITY_FIELDS
                and current_value == []
            ):
                current_value_authoritative = True
            if (
                row_type in AUTHORITY_STATUS_CONFLICT_PRESERVE_ROW_TYPES
                and field in ORDER_TRADE_STATUS_CONFLICT_PRESERVE_FIELDS
                and current_value_authoritative
                and _status_join_values_conflict(field, current_value, value)
            ):
                if (
                    field
                    == "package_new_entry_authority_candidate_decision_quality_alias_status"
                    and str(current_value or "").strip() == "materialized"
                    and str(value or "").strip() == "exact_materialized"
                ):
                    row.setdefault(f"{row_type}_reported_{field}", current_value)
                    row[field] = value
                    row[
                        "package_new_entry_authority_candidate_decision_quality_alias_status_upgraded_from_exact_join"
                    ] = True
                    continue
                if (
                    field in ORDER_TRADE_STATUS_PROVENANCE_ONLY_FIELDS
                    or _order_trade_status_conflict_is_rederived_executable(
                        row,
                        status,
                        field=field,
                        current_value=current_value,
                        status_value=value,
                    )
                ):
                    row.setdefault(f"{row_type}_reported_{field}", current_value)
                    row[f"selected_package_status_{field}"] = value
                    row.setdefault(
                        "selected_package_candidate_status_join_provenance_differences",
                        [],
                    ).append(
                        {
                            "field": field,
                            "row_value": current_value,
                            "candidate_status_value": value,
                        }
                    )
                    continue
                merged_attribution = _merged_execution_attribution_list(
                    field,
                    current_value,
                    value,
                )
                if merged_attribution is not None:
                    row.setdefault(f"{row_type}_reported_{field}", current_value)
                    row[f"selected_package_status_{field}"] = value
                    row[f"selected_package_status_{field}_union_merged"] = True
                    row[field] = merged_attribution
                    continue
                row.setdefault(f"{row_type}_reported_{field}", current_value)
                row[f"selected_package_status_{field}"] = value
                status_join_conflicts.append(
                    {
                        "field": field,
                        "row_value": current_value,
                        "candidate_status_value": value,
                    }
                )
                continue
            if (
                row_type in AUTHORITY_STATUS_CONFLICT_PRESERVE_ROW_TYPES
                and field in ORDER_TRADE_STATUS_CONFLICT_PRESERVE_FIELDS
                and current_value_authoritative
                and current_value != value
            ):
                row.setdefault(f"{row_type}_reported_{field}", current_value)
                row[f"selected_package_status_{field}"] = value
                row[f"selected_package_status_{field}_canonical_equivalent"] = True
                continue
            row[field] = value
    if status_join_conflicts:
        row["selected_package_candidate_status_join_execution_authority_conflict"] = True
        row["selected_package_candidate_status_join_conflicts"] = status_join_conflicts
    for field in PACKAGE_STATUS_QUALITY_JOIN_FIELDS:
        status_value = status.get(field)
        if _missing_value(status_value):
            continue
        current_value = row.get(field)
        if (
            not _missing_value(current_value)
            and _status_join_values_conflict(field, current_value, status_value)
        ):
                row.setdefault(f"{row_type}_reported_{field}", current_value)
        row[field] = status_value
    _canonicalize_order_trade_open_reduced_status_join(row, row_type=row_type)
    if row_type == "scorecard":
        _scrub_scorecard_no_final_selection_candidate_authority(row)
    enforce_order_trade_terminal_execution_authority(row, row_type=row_type)
    _backfill_package_root_aliases(row)
    _backfill_selected_scheduler_aliases(row, row_type=row_type)
    envelope = candidate_decision_quality_envelope(row)
    if envelope:
        row["candidate_decision_quality"] = envelope
    return row


def decorate_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    row_type: str,
    candidate_status_by_id: Mapping[str, Any] | None = None,
    candidate_status_by_window: Mapping[str, list[Mapping[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    decorated: list[dict[str, Any]] = []
    for row in rows:
        out = {
            "schema": f"gtos.final_moonshot.denominator_to_deployment.selected_package_replay_bridge.{row_type}.v1",
            "route_id": "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20",
            "source_operation": "route_local_replay_from_optimized_source_materializer",
            "broker_mutation": False,
            "paid_api_call": False,
            "remote_push": False,
            **dict(row),
        }
        joined = _join_candidate_status(
            out,
            row_type=row_type,
            candidate_status_by_id=candidate_status_by_id,
            candidate_status_by_window=candidate_status_by_window,
        )
        if row_type == "scorecard":
            joined.update(timewarp_loop.scorecard_source_boundary_backfill_fields(joined))
            _scrub_scorecard_no_final_selection_candidate_authority(joined)
        if row_type == "candidate":
            source_bound_allowed = any(
                _truthy(joined.get(field)) for field in PACKAGE_USE_ALIAS_FIELDS
            )
            derived_authority_fields = package_authority_bridge_fields(
                joined,
                source_bound_allowed=source_bound_allowed,
            )
            _promote_trusted_package_authority_fields(
                joined,
                derived_authority_fields,
            )
            flatten_package_bridge_contract_fields(
                joined,
                source_bound_allowed=source_bound_allowed,
            )
            finalize_bridge_package_authority_contract(
                joined,
                source_bound_allowed=source_bound_allowed,
            )
            _enforce_non_executable_source_bound_diagnostic(joined)
        if row_type in {"order", "trade"}:
            if _missing_value(joined.get("candidate_decision_quality_source_boundary")):
                joined["candidate_decision_quality_source_boundary"] = (
                    joined.get("source_boundary")
                    or "selected_package_bridge_order_trade_predecision_quality"
                )
            if _missing_value(joined.get("source_boundary")):
                joined["source_boundary"] = (
                    joined.get("candidate_decision_quality_source_boundary")
                    or SOURCE_BOUND_EVIDENCE_CLASS
                )
            identity_fields = timewarp_loop.canonical_replay_candidate_instance_fields(
                joined,
                decision_time_utc=(
                    joined.get("decision_time_utc")
                    or joined.get("candle_close_utc")
                    or joined.get("source_candle_time_utc")
                ),
            )
            for identity_field, identity_value in identity_fields.items():
                if _missing_value(joined.get(identity_field)) and not _missing_value(
                    identity_value
                ):
                    joined[identity_field] = identity_value
            source_bound_allowed = any(
                _truthy(joined.get(field))
                for field in (
                    "source_bound_package_candidate_use_allowed",
                    "ultimate_package_source_bound_candidate_use_allowed",
                    "package_replay_source_bound_candidate_use_allowed",
                )
            )
            derived_authority_fields = package_authority_bridge_fields(
                joined,
                source_bound_allowed=source_bound_allowed,
            )
            _promote_trusted_package_authority_fields(
                joined,
                derived_authority_fields,
            )
            flatten_package_bridge_contract_fields(
                joined,
                source_bound_allowed=source_bound_allowed,
            )
            _canonicalize_order_trade_open_reduced_status_join(
                joined,
                row_type=row_type,
            )
            executable_allowed, executable_reason = executable_package_use_detail(
                joined,
                source_bound_allowed=source_bound_allowed,
            )
            if not executable_allowed:
                existing_reason = joined.get(
                    "package_replay_executable_candidate_use_allowed_reason"
                )
                block_reason = (
                    existing_reason
                    if not source_bound_allowed
                    and not _missing_value(existing_reason)
                    and joined.get("package_replay_executable_candidate_use_allowed")
                    is False
                    else executable_reason
                )
                joined["package_replay_candidate_use_allowed"] = False
                joined["package_replay_executable_candidate_use_allowed"] = False
                joined["package_replay_executable_candidate_use_allowed_reason"] = (
                    block_reason
                )
                joined["selected_package_non_executable_order_trade_diagnostic"] = True
                joined["selected_package_non_executable_order_trade_reason"] = (
                    block_reason
                )
                joined["order_materialization_authority_blocked"] = True
                joined["order_materialization_authority_block_reason"] = (
                    block_reason
                )
                _demote_non_executable_effective_source_bound_signal(
                    joined,
                    reason=block_reason,
                )
                _enforce_non_executable_source_bound_diagnostic(
                    joined,
                    reason=block_reason,
                )
        _backfill_source_bound_diagnostic_contract(joined)
        _backfill_selected_scheduler_aliases(joined, row_type=row_type)
        envelope = candidate_decision_quality_envelope(joined)
        if envelope:
            joined["candidate_decision_quality"] = envelope
        decorated.append(joined)
    return decorated


def execution_disposition_instance_key(row: Mapping[str, Any]) -> str:
    key = str(row.get("canonical_replay_candidate_instance_key") or "").strip()
    if key:
        return key
    candidate_id = str(row.get("candidate_id") or row.get("selected_candidate_id") or "").strip()
    decision_time = str(
        row.get("decision_time_utc")
        or row.get("candle_close_utc")
        or row.get("source_candle_time_utc")
        or ""
    ).strip()
    return f"{candidate_id}@@{decision_time}" if candidate_id and decision_time else ""


def _index_rows_by_instance(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = execution_disposition_instance_key(row)
        if not key:
            continue
        out.setdefault(key, []).append(dict(row))
    return out


def _first_non_missing_mapping_value(
    row: Mapping[str, Any],
    fields: Iterable[str],
) -> Any:
    for field in fields:
        value = row.get(field)
        if not _missing_value(value):
            return value
    return None


def path_provenance_payload(row: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in PATH_PROVENANCE_FIELDS:
        aliases = PATH_PROVENANCE_FIELD_ALIASES.get(field, (field,))
        value = _first_non_missing_mapping_value(row, aliases)
        if not _missing_value(value):
            payload[field] = value
    return payload


def _row_has_path_provenance(row: Mapping[str, Any]) -> bool:
    return bool(path_provenance_payload(row))


def _oracle_path_provenance_index_keys(row: Mapping[str, Any]) -> list[str]:
    keys: list[str] = []

    def add(kind: str, value: Any) -> None:
        text = str(value or "").strip()
        if not text:
            return
        key = f"{kind}:{text}"
        if key not in keys:
            keys.append(key)

    for field in (
        "simulated_order_id",
        "terminal_resolution_order_id",
        "replacement_simulated_order_id",
    ):
        add("order", row.get(field))
    for field in ("simulated_trade_id", "terminal_resolution_trade_id"):
        add("trade", row.get(field))
    instance_key = execution_disposition_instance_key(row)
    add("instance", instance_key)
    candidate_id = str(row.get("candidate_id") or row.get("selected_candidate_id") or "").strip()
    decision_time = str(
        row.get("decision_time_utc")
        or row.get("candle_close_utc")
        or row.get("source_candle_time_utc")
        or ""
    ).strip()
    expiry = str(row.get("expiry_utc") or row.get("order_expiry_utc") or "").strip()
    if candidate_id and decision_time and expiry:
        add("candidate_decision_expiry", f"{candidate_id}@@{decision_time}@@{expiry}")
    return keys


def _oracle_path_provenance_index(
    oracle_rows: Iterable[Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for row in oracle_rows:
        if not _row_has_path_provenance(row):
            continue
        oracle_row = dict(row)
        for key in _oracle_path_provenance_index_keys(oracle_row):
            index.setdefault(key, []).append(oracle_row)
    return index


def _unique_path_payloads(rows: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for row in rows:
        payload = path_provenance_payload(row)
        if not payload:
            continue
        payload_hash = stable_sha256(payload)
        unique[payload_hash] = payload
    return unique


def _matched_oracle_path_provenance(
    row: Mapping[str, Any],
    oracle_index: Mapping[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any], str, str] | None:
    for key in _oracle_path_provenance_index_keys(row):
        matches = oracle_index.get(key) or []
        if not matches:
            continue
        same_candidate_matches = [
            match
            for match in matches
            if str(match.get("candidate_id") or "") == str(row.get("candidate_id") or "")
            or not row.get("candidate_id")
        ]
        candidates = same_candidate_matches or matches
        unique_payloads = _unique_path_payloads(candidates)
        if len(unique_payloads) == 1:
            payload = next(iter(unique_payloads.values()))
            status = "exact_oracle_path_provenance_match"
            if len(candidates) > 1:
                status = "equivalent_duplicate_oracle_path_provenance_match"
            return payload, key, status
    return None


def backfill_order_trade_path_provenance_from_oracles(
    rows: Iterable[Mapping[str, Any]],
    oracle_rows: Iterable[Mapping[str, Any]],
    *,
    row_type: str,
) -> list[dict[str, Any]]:
    oracle_index = _oracle_path_provenance_index(oracle_rows)
    backfilled: list[dict[str, Any]] = []
    for row in rows:
        out = dict(row)
        match = _matched_oracle_path_provenance(out, oracle_index)
        if match is None:
            if not _row_has_path_provenance(out):
                out["path_provenance_backfilled_from_oracle"] = False
                out["path_provenance_backfill_status"] = "missing_oracle_path_provenance_match"
            backfilled.append(out)
            continue
        payload, key, status = match
        copied: list[str] = []
        for field, value in payload.items():
            if _missing_value(out.get(field)) and not _missing_value(value):
                out[field] = value
                copied.append(field)
        if copied:
            out["path_provenance_backfilled_from_oracle"] = True
            out["path_provenance_backfill_status"] = status
            out["path_provenance_backfill_key"] = key
            out["path_provenance_backfill_row_type"] = row_type
            out["path_provenance_backfilled_fields"] = copied
        else:
            out.setdefault("path_provenance_backfilled_from_oracle", False)
            out.setdefault(
                "path_provenance_backfill_status",
                "path_provenance_already_present",
            )
        backfilled.append(out)
    return backfilled


def _row_fill_status(row: Mapping[str, Any]) -> str:
    for field in ("order_status", "fill_status", "limit_first_fill_status"):
        value = str(row.get(field) or "").strip()
        if value:
            return value
    return ""


def _row_is_filled(row: Mapping[str, Any]) -> bool:
    status = _row_fill_status(row).lower()
    if status.startswith("not_filled") or status.startswith("unfilled"):
        return False
    return status == "filled" or status.startswith("filled_")


def _terminal_non_executable_reason(rows: Iterable[Mapping[str, Any]]) -> str:
    for row in rows:
        for field in (
            "selected_package_non_executable_order_trade_reason",
            "order_materialization_authority_block_reason",
            "package_replay_executable_candidate_use_allowed_reason",
            "replay_candidate_use_allowed_now_reason",
            "risk_decision_reason",
            "execution_manager_replay_admission_status",
            "execution_manager_action",
        ):
            value = row.get(field)
            if not _missing_value(value):
                return str(value)
    return "filtered_non_executable_terminal_row"


def _row_candidate_id(row: Mapping[str, Any]) -> str:
    return str(row.get("candidate_id") or row.get("selected_candidate_id") or "").strip()


def _row_id_set(row: Mapping[str, Any], fields: Iterable[str]) -> set[str]:
    values: set[str] = set()
    for field in fields:
        for item in list_values(row.get(field)):
            text = str(item or "").strip()
            if text:
                values.add(text)
    return values


def _compact_row_scheduler_final_selected(row: Mapping[str, Any]) -> bool:
    candidate_id = _row_candidate_id(row)
    if _truthy(row.get("scheduler_final_selected")):
        return True
    selected_id = str(row.get("selected_candidate_id") or "").strip()
    if candidate_id and selected_id and selected_id == candidate_id:
        return True
    selected_ids = _row_id_set(
        row,
        (
            "selected_candidate_ids",
            "scheduler_final_selected_candidate_ids",
            "risk_admitted_final_selected_candidate_ids",
            "final_selected_candidate_ids",
        ),
    )
    return bool(candidate_id and candidate_id in selected_ids)


def _compact_row_scheduler_pre_finalizer_selected(row: Mapping[str, Any]) -> bool:
    candidate_id = _row_candidate_id(row)
    if _truthy(row.get("scheduler_pre_finalizer_selected")):
        return True
    selected_ids = _row_id_set(
        row,
        (
            "pre_risk_finalizer_selected_candidate_ids",
            "scheduler_selected_candidate_ids_before_risk_finalizer",
            "original_selected_candidate_ids",
        ),
    )
    return bool(candidate_id and candidate_id in selected_ids)


def build_selected_package_execution_disposition_rows(
    *,
    compact_rows: Iterable[Mapping[str, Any]],
    order_rows: Iterable[Mapping[str, Any]],
    oracle_rows: Iterable[Mapping[str, Any]],
    trade_rows: Iterable[Mapping[str, Any]],
    filtered_non_executable_order_rows: Iterable[Mapping[str, Any]] = (),
    filtered_non_executable_trade_rows: Iterable[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    order_by_key = _index_rows_by_instance(order_rows)
    oracle_by_key = _index_rows_by_instance(oracle_rows)
    trade_by_key = _index_rows_by_instance(trade_rows)
    filtered_order_by_key = _index_rows_by_instance(filtered_non_executable_order_rows)
    filtered_trade_by_key = _index_rows_by_instance(filtered_non_executable_trade_rows)
    rows: list[dict[str, Any]] = []
    for compact in compact_rows:
        if compact.get("selected_package_replay_row") is not True:
            continue
        key = execution_disposition_instance_key(compact)
        orders = order_by_key.get(key, []) if key else []
        oracles = oracle_by_key.get(key, []) if key else []
        trades = trade_by_key.get(key, []) if key else []
        filtered_orders = filtered_order_by_key.get(key, []) if key else []
        filtered_trades = filtered_trade_by_key.get(key, []) if key else []
        filled_order = next((row for row in orders if _row_is_filled(row)), None)
        filled_oracle = next((row for row in oracles if _row_is_filled(row)), None)
        filled_filtered_order = next(
            (row for row in filtered_orders if _row_is_filled(row)),
            None,
        )
        scheduler_final_selected = _compact_row_scheduler_final_selected(compact)
        scheduler_pre_finalizer_selected = _compact_row_scheduler_pre_finalizer_selected(
            compact
        )
        disposition = "selected_package_execution_disposition_unclassified"
        reason = None
        execution_claim = False
        non_executable_reason = None
        if compact.get("package_replay_executable_candidate_use_allowed") is False:
            non_executable_reason = (
                compact.get("package_replay_executable_candidate_use_allowed_reason")
                or "package_replay_executable_candidate_use_allowed_false"
            )
        elif compact.get(
            "scheduler_materialization_skip_reason"
        ) and not scheduler_materialization_skip_is_soft_transfer(
            compact,
            str(compact.get("scheduler_materialization_skip_reason") or ""),
        ):
            non_executable_reason = compact.get("scheduler_materialization_skip_reason")
        if non_executable_reason:
            if trades or filled_order:
                disposition = "invalid_non_executable_bound_execution"
                reason = non_executable_reason
            elif filled_oracle or oracles:
                disposition = "non_executable_path_oracle_diagnostic"
                reason = non_executable_reason
            else:
                disposition = "non_executable_scheduler_skip"
                reason = non_executable_reason
        elif trades and filled_order and (filled_oracle or not oracles):
            disposition = "bound_filled_trade"
            reason = "trade_bound_to_filled_order_oracle"
            execution_claim = True
        elif trades and (not filled_order or (oracles and not filled_oracle)):
            disposition = "invalid_trade_without_filled_order_or_oracle"
            reason = "trade_row_without_filled_order_or_oracle"
        elif (filled_order or filled_oracle) and not trades:
            disposition = "filled_order_or_oracle_without_trade_row"
            reason = "filled_order_or_oracle_present_without_filled_trade"
        elif orders and oracles:
            disposition = "ordered_unfilled_no_trade"
            reason = "order_and_oracle_present_without_filled_trade"
        elif str(compact.get("order_policy_action") or "").strip() == "limit_first_delay_queue":
            disposition = "deferred_limit_first_delay_queue_not_ordered"
            reason = "limit_first_delay_queue_no_order_or_oracle"
        elif compact.get("replay_candidate_use_allowed_now") is False:
            disposition = "non_executable_replay_candidate_use_not_allowed"
            reason = (
                compact.get("replay_candidate_use_allowed_now_reason")
                or "replay_candidate_use_allowed_now_false"
            )
        elif scheduler_final_selected and (filtered_orders or filtered_trades):
            terminal_reason = _terminal_non_executable_reason(
                [*filtered_orders, *filtered_trades]
            )
            if filtered_trades or filled_filtered_order:
                disposition = "filtered_non_executable_terminal_filled_diagnostic"
                reason = terminal_reason
            else:
                disposition = "filtered_non_executable_terminal_blocked_no_trade"
                reason = terminal_reason
        elif not scheduler_final_selected and scheduler_pre_finalizer_selected:
            disposition = "executable_pre_finalizer_selected_not_risk_final_selected"
            reason = "package_executable_candidate_removed_by_risk_finalizer"
        elif not scheduler_final_selected:
            disposition = "executable_package_candidate_not_scheduler_selected"
            reason = "package_executable_candidate_not_scheduler_final_selected"
        else:
            disposition = "executable_scheduler_final_selected_missing_order_binding"
            reason = "scheduler_final_selected_candidate_has_no_order_oracle_trade_binding"
        row = {
            "schema": "gtos.final_moonshot.denominator_to_deployment.selected_package_replay_bridge.execution_disposition.v1",
            "route_id": "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20",
            "source_operation": "route_local_replay_from_optimized_source_materializer",
            "candidate_id": compact.get("candidate_id"),
            "selected_candidate_id": compact.get("selected_candidate_id"),
            "decision_time_utc": compact.get("decision_time_utc"),
            "symbol": compact.get("symbol"),
            "side": compact.get("side") or compact.get("direction"),
            "canonical_replay_candidate_instance_key": key or None,
            "selected_package_replay_row": True,
            "execution_disposition": disposition,
            "execution_disposition_reason": reason,
            "execution_claim": execution_claim,
            "bound_order_rows": len(orders),
            "bound_oracle_rows": len(oracles),
            "bound_trade_rows": len(trades),
            "bound_filtered_non_executable_order_rows": len(filtered_orders),
            "bound_filtered_non_executable_trade_rows": len(filtered_trades),
            "bound_filled_order_rows": sum(1 for row in orders if _row_is_filled(row)),
            "bound_filled_oracle_rows": sum(1 for row in oracles if _row_is_filled(row)),
            "bound_filled_filtered_non_executable_order_rows": sum(
                1 for row in filtered_orders if _row_is_filled(row)
            ),
            "order_statuses": [_row_fill_status(row) for row in orders if _row_fill_status(row)],
            "filtered_non_executable_order_statuses": [
                _row_fill_status(row)
                for row in filtered_orders
                if _row_fill_status(row)
            ],
            "oracle_statuses": [_row_fill_status(row) for row in oracles if _row_fill_status(row)],
            "trade_ids": [
                row.get("simulated_trade_id")
                for row in trades
                if row.get("simulated_trade_id") not in (None, "")
            ],
            "filtered_non_executable_trade_ids": [
                row.get("simulated_trade_id")
                for row in filtered_trades
                if row.get("simulated_trade_id") not in (None, "")
            ],
            "order_policy_action": compact.get("order_policy_action"),
            "scheduler_final_selected": scheduler_final_selected,
            "scheduler_pre_finalizer_selected": scheduler_pre_finalizer_selected,
            "scheduler_final_selected_candidate_ids": list_values(
                compact.get("scheduler_final_selected_candidate_ids")
            )
            or list_values(compact.get("selected_candidate_ids")),
            "pre_risk_finalizer_selected_candidate_ids": list_values(
                compact.get("pre_risk_finalizer_selected_candidate_ids")
            ),
            "scheduler_materialization_skip_reason": compact.get(
                "scheduler_materialization_skip_reason"
            ),
            "package_replay_executable_candidate_use_allowed": compact.get(
                "package_replay_executable_candidate_use_allowed"
            ),
            "package_replay_executable_candidate_use_allowed_reason": compact.get(
                "package_replay_executable_candidate_use_allowed_reason"
            ),
            "training_use_allowed": False,
            "final_package_selection_allowed": False,
            "live_broker_authority": False,
            "broker_mutation": False,
            "paid_api_call": False,
            "remote_push": False,
        }
        for field in EXECUTION_DISPOSITION_PROPAGATED_COMPACT_FIELDS:
            if field in row:
                continue
            value = compact.get(field)
            if not _missing_value(value):
                row[field] = value
        _enforce_non_executable_source_bound_diagnostic(
            row,
            reason=reason,
        )
        _backfill_source_bound_diagnostic_contract(row)
        row.setdefault("candidate_decision_quality_alias_mismatches", [])
        row.setdefault("candidate_decision_quality_provenance_failures", [])
        row.setdefault(
            "package_new_entry_authority_candidate_decision_quality_alias_mismatches",
            [],
        )
        row.setdefault(
            "package_new_entry_authority_candidate_decision_quality_provenance_failures",
            [],
        )
        rows.append(row)
    return rows


def summarize_selected_package_execution_dispositions(
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    rows = list(rows)
    counts = Counter(str(row.get("execution_disposition") or "missing") for row in rows)
    return {
        "selected_package_execution_disposition_rows": len(rows),
        "selected_package_execution_disposition_counts": dict(sorted(counts.items())),
        "selected_package_execution_disposition_bound_filled_trade_rows": counts.get(
            "bound_filled_trade",
            0,
        ),
        "selected_package_execution_disposition_ordered_unfilled_rows": counts.get(
            "ordered_unfilled_no_trade",
            0,
        ),
        "selected_package_execution_disposition_filtered_terminal_blocked_rows": (
            counts.get("filtered_non_executable_terminal_blocked_no_trade", 0)
        ),
        "selected_package_execution_disposition_filtered_terminal_filled_diagnostic_rows": (
            counts.get("filtered_non_executable_terminal_filled_diagnostic", 0)
        ),
        "selected_package_execution_disposition_deferred_rows": counts.get(
            "deferred_limit_first_delay_queue_not_ordered",
            0,
        ),
        "selected_package_execution_disposition_not_scheduler_selected_rows": (
            counts.get("executable_package_candidate_not_scheduler_selected", 0)
            + counts.get(
                "executable_pre_finalizer_selected_not_risk_final_selected",
                0,
            )
        ),
        "selected_package_execution_disposition_missing_order_binding_rows": counts.get(
            "executable_scheduler_final_selected_missing_order_binding",
            0,
        ),
        "selected_package_execution_disposition_non_executable_rows": (
            counts.get("non_executable_scheduler_skip", 0)
            + counts.get("non_executable_replay_candidate_use_not_allowed", 0)
            + counts.get("non_executable_path_oracle_diagnostic", 0)
            + counts.get("filtered_non_executable_terminal_blocked_no_trade", 0)
            + counts.get("filtered_non_executable_terminal_filled_diagnostic", 0)
            + counts.get("invalid_non_executable_bound_execution", 0)
        ),
        "selected_package_execution_disposition_missing_rows": counts.get(
            "selected_package_execution_disposition_unclassified",
            0,
        ),
        "selected_package_execution_disposition_invalid_rows": counts.get(
            "invalid_trade_without_filled_order_or_oracle",
            0,
        )
        + counts.get(
            "filled_order_or_oracle_without_trade_row",
            0,
        )
        + counts.get(
            "invalid_non_executable_bound_execution",
            0,
        )
        + counts.get(
            "executable_scheduler_final_selected_missing_order_binding",
            0,
        ),
    }


STOP_HAZARD_PROJECTION_FIELDS = (
    "predecision_stop_hazard_guard_status",
    "predecision_stop_hazard_guard_reason",
    "predecision_stop_hazard_guard_action",
    "predecision_stop_hazard_guard_risk_cap_applied",
    "predecision_stop_hazard_guard_risk_cap_pct",
    "predecision_stop_hazard_guard_score_penalty",
    "predecision_stop_hazard_guard_unit_risk_atr",
    "predecision_stop_hazard_guard_unit_risk",
    "predecision_stop_hazard_guard_atr14",
    "predecision_stop_hazard_guard_distance_to_limit_risk",
    "predecision_stop_hazard_guard_distance_to_limit_atr",
    "predecision_stop_hazard_guard_limit_fill_probability",
    "predecision_stop_hazard_guard_target_r",
    "predecision_stop_hazard_guard_target_r_source",
    "predecision_stop_hazard_guard_min_unit_risk_atr",
    "predecision_stop_hazard_guard_max_distance_to_limit_risk",
    "predecision_stop_hazard_guard_min_limit_fill_probability",
    "predecision_stop_hazard_guard_min_target_r",
    "predecision_stop_hazard_guard_pressure_enabled",
    "predecision_stop_hazard_guard_pressure_min_score",
    "predecision_stop_hazard_guard_pressure_score",
    "predecision_stop_hazard_guard_pressure_triggered",
    "predecision_stop_hazard_guard_pressure_components",
    "predecision_stop_hazard_guard_pressure_required_conditions",
    "predecision_stop_hazard_guard_pressure_triggered_conditions",
    "predecision_stop_hazard_guard_pressure_missing_fields",
    "predecision_stop_hazard_guard_require_all_thresholds",
    "predecision_stop_hazard_guard_triggered_conditions",
    "predecision_stop_hazard_guard_missing_fields",
    "predecision_stop_hazard_guard_source_boundary",
    "predecision_stop_hazard_guard_outcome_fields_used",
)


STOP_HAZARD_NESTED_INPUT_FIELDS = (
    "scheduler_candidate_decision_inputs",
    "selected_scheduler_decision_inputs",
    "pre_risk_finalizer_selected_scheduler_decision_inputs",
    "scheduler_option_candidate_decision_inputs",
)


PACKAGE_ORDER_EXECUTABLE_AUTHORITY_FIELDS = (
    "package_replay_order_executable_candidate_use_allowed",
    "package_replay_order_executable_candidate_use_allowed_reason",
    "package_replay_order_executable_authority_source",
)
SCHEDULER_MATERIALIZATION_SOFT_TRANSFER_SKIP_TOKENS = (
    "not_scheduler_selected",
    "scheduler_not_selected",
    "scheduler_selection",
    "selected_competing_candidate",
    "selector_materialization",
    "runtime_eligible_no_selected",
    "no_selected_id",
    "selector_not_risk_bearing",
)
SCHEDULER_MATERIALIZATION_TERMINAL_SKIP_TOKENS = (
    "cost",
    "refused",
    "source_gap",
    "source_required",
    "fillability",
    "fill_probability",
    "unfillable",
    "marketable",
    "geometry",
    "invalid",
    "terminal",
    "expiry",
    "expired",
    "fallback",
    "lifecycle",
    "off_configured",
    "authority_missing",
)
V220_HARD_CLEAN_CAPPED_SOFT_SKIP_TOKENS = (
    "reallocation_quality_score_below_floor",
    "selected_policy_reallocation_quality_score",
)
V220_CAPPED_REALLOCATION_SCORE_POLICY = (
    "risk_cap_adjusted_expected_transfer_for_capped_candidate;"
    "legacy_absolute_guard_penalty_is_diagnostic_only"
)


def _backfill_stop_hazard_projection(
    row: dict[str, Any],
    *sources: Mapping[str, Any],
) -> None:
    for source_row in sources:
        if not isinstance(source_row, Mapping):
            continue
        for key in STOP_HAZARD_PROJECTION_FIELDS:
            if _missing_value(row.get(key)):
                value = source_row.get(key)
                if not _missing_value(value):
                    row[key] = value
        for nested_field in STOP_HAZARD_NESTED_INPUT_FIELDS:
            nested = source_row.get(nested_field)
            if not isinstance(nested, Mapping):
                continue
            for key in STOP_HAZARD_PROJECTION_FIELDS:
                if _missing_value(row.get(key)):
                    value = nested.get(key)
                    if not _missing_value(value):
                        row[key] = value
    _normalize_stop_hazard_cap_truth(row)


def _normalize_stop_hazard_cap_truth(row: dict[str, Any]) -> None:
    status = str(row.get("predecision_stop_hazard_guard_status") or "").strip().lower()
    reason = str(row.get("predecision_stop_hazard_guard_reason") or "").strip().lower()
    action = str(row.get("predecision_stop_hazard_guard_action") or "").strip().lower()
    cap_pct = row.get("predecision_stop_hazard_guard_risk_cap_pct")
    cap_pct_present = not _missing_value(cap_pct)
    if not (status or reason or action or cap_pct_present):
        return
    non_cap_status = status in {"pass", "passed", "clear", "allowed"}
    capped_truth = (
        status == "capped"
        or "risk_capped" in reason
        or (action in {"cap", "capped"} and cap_pct_present and not non_cap_status)
    )
    if capped_truth:
        row["predecision_stop_hazard_guard_risk_cap_applied"] = True
    elif non_cap_status or (action and action not in {"cap", "capped"}):
        row["predecision_stop_hazard_guard_risk_cap_applied"] = False


def _backfill_package_order_executable_authority(
    row: dict[str, Any],
    *sources: Mapping[str, Any],
) -> None:
    copied_from: str | None = None
    for source_row in sources:
        if not isinstance(source_row, Mapping):
            continue
        source_name = "selected_package_bridge_surface"
        for key in PACKAGE_ORDER_EXECUTABLE_AUTHORITY_FIELDS:
            if _missing_value(row.get(key)):
                value = source_row.get(key)
                if not _missing_value(value):
                    row[key] = value
                    copied_from = copied_from or source_name
        for nested_field in STOP_HAZARD_NESTED_INPUT_FIELDS:
            nested = source_row.get(nested_field)
            if not isinstance(nested, Mapping):
                continue
            nested_name = nested_field
            for key in PACKAGE_ORDER_EXECUTABLE_AUTHORITY_FIELDS:
                if _missing_value(row.get(key)):
                    value = nested.get(key)
                    if not _missing_value(value):
                        row[key] = value
                        copied_from = copied_from or nested_name
    if copied_from and _missing_value(
        row.get("package_replay_order_executable_authority_flattened_from")
    ):
        row["package_replay_order_executable_authority_flattened_from"] = copied_from


COMPACT_CANDIDATE_FIELDS = (
    "route_id",
    "source_operation",
    *PACKAGE_REPLAY_AUTHORITY_FIELDS,
    *timewarp_loop.SIGNED_SOFT_TRANSFER_DISPLACEMENT_TRACE_KEYS,
    "broad_replay_profile",
    *CANONICAL_REPLAY_CONTEXT_ENVELOPE_FIELDS,
    "source_asof_utc",
    "candle_close_utc",
    "source_candle_time_utc",
    "source_hash",
    "source_sha256",
    "source_hashes_by_timeframe",
    "source_path",
    "source_paths_by_timeframe",
    "packet_sidecar_id",
    "packet_sidecar_hash_sha256",
    "selector_packet_hash_sha256",
    "ultimate_candidate_package_packet_hash_sha256",
    "ultimate_candidate_package_packet_shape_hash_sha256",
    "source_bound_fields",
    "source_fields",
    "candidate_decision_quality",
    "candidate_decision_quality_field_sources",
    "candidate_decision_quality_alias_status",
    "candidate_decision_quality_source_boundary",
    "candidate_decision_quality_alias_mismatches",
    "candidate_decision_quality_provenance_failures",
    "selected_policy_expected_net_calibration_status",
    "selected_policy_expected_net_r_calibration_status",
    "expected_net_r_selected_policy_calibration_status",
    "selected_policy_expected_net_calibrated",
    "selected_policy_expected_net_calibration_required",
    "selected_policy_expected_net_calibration_source",
    "selected_policy_expected_net_calibration_source_boundary",
    "selected_policy_expected_net_calibration_boundary",
    "selected_policy_expected_net_assumption_hash",
    "selected_policy_expected_net_r_assumption_hash",
    "selected_policy_expected_net_calibration_hash",
    "selected_policy_for_expected_net_r",
    "selected_policy_expected_net_r",
    "selected_policy_probability",
    "selected_policy_source_completeness",
    "selected_policy_quality_alias_status",
    "selected_policy_quality_source_boundary",
    "source_boundary",
    "canonical_replay_candidate_instance_key",
    "risk_finalizer_probe_instance_key",
    "source_bound_replay_candidate_instance_key",
    "candidate_instance_identity_status",
    "source_bound_signal_r",
    "source_bound_r_additive_allowed",
    "source_bound_r_additive_unit",
    "source_bound_r_additive_scope",
    "replay_identity_tuple_status",
    "source_bound_alias_status",
    "source_completeness_status",
    "source_window_complete",
    "candidate_id",
    "original_candidate_id",
    "row_bound_candidate_id",
    "candidate_set_id",
    "selected_candidate_id",
    "selected_candidate_ids",
    "decision_time_utc",
    "decision_window_id",
    "stable_decision_window_id",
    "symbol",
    "instrument",
    "side",
    "direction",
    "framework",
    "current_framework",
    "strategy_family",
    "origin_family",
    "candidate_origin_family",
    "route_family",
    "setup_family",
    "session_bucket",
    "session",
    "route_session",
    "utc_hour_bucket",
    "package_session_tokens",
    *PACKAGE_AUTHORITY_FIELDS,
    *EXECUTABLE_GEOMETRY_FIELDS,
    "candidate_ev_r",
    "ev_r",
    "expectancy_r",
    "expected_net_r",
    "candidate_expected_net_r",
    "candidate_probability",
    "probability",
    "candidate_confidence",
    "confidence",
    "expected_cost_r",
    "cost_r",
    "broker_calibrated_expected_cost_r",
    "broker_pretrade_cost_r",
    "candidate_cost_r_fallback_diagnostic",
    "candidate_cost_r_fallback_is_authority",
    "cost_authority",
    "execution_cost_authority",
    "pretrade_cost_packet_status",
    "pretrade_cost_refusal_reasons",
    "cost_source_gap_status",
    "close_side_all_in_cost_status",
    "source_completeness",
    "fill_probability",
    "entry_quality_fill_probability",
    "candidate_fill_probability",
    "heuristic_fill_probability",
    "predecision_limit_fillability",
    "limit_fillability_probability",
    "predecision_limit_fillability_probability",
    "execution_fill_probability",
    "execution_fill_probability_source",
    "execution_fill_probability_source_time_utc",
    "execution_fill_probability_source_boundary",
    "risk_pct",
    "selected_cell_risk_pct",
    "requested_risk_pct",
    "scheduler_approved_risk_pct",
    "risk_per_trade_pct",
    "selector_action_origin",
    "selector_action",
    "effective_selector_action",
    "selector_reason",
    "ultimate_candidate_package_open_reduced_risk_authority",
    "package_open_reduced_authority_allowed",
    "package_open_reduced_authority_family",
    "ultimate_package_open_reduced_authority_allowed",
    "source_bound_package_candidate_use_allowed",
    "ultimate_package_source_bound_candidate_use_allowed",
    "ultimate_package_admission_candidate_use_allowed",
    "package_replay_source_bound_candidate_use_allowed",
    "package_replay_candidate_use_allowed",
    "package_replay_executable_candidate_use_allowed",
    "package_replay_executable_candidate_use_allowed_reason",
    "replay_candidate_use_allowed_now",
    "replay_candidate_use_allowed_now_reason",
    "selected_package_candidate_use_allowed_status",
    *PACKAGE_ORDER_EXECUTABLE_AUTHORITY_FIELDS,
    "package_replay_order_executable_authority_flattened_from",
    *STOP_HAZARD_PROJECTION_FIELDS,
    "scheduler_final_selected",
    "scheduler_pre_finalizer_selected",
    "scheduler_final_selected_candidate_ids",
    "pre_risk_finalizer_selected_candidate_ids",
    "scheduler_materialization_action_intent",
    "scheduler_materialization_original_action_intent",
    "scheduler_materialization_selector_action",
    "scheduler_materialization_selector_reason",
    "scheduler_materialization_skip_reason",
    "ultimate_package_decision_status",
    "ultimate_package_role_disposition",
    "role_disposition",
    "ultimate_package_matched_sleeve_ids",
    "matched_sleeve_ids",
    "ultimate_package_matched_sleeve_count",
    "matched_sleeve_count",
    "ultimate_package_admission_sleeve_match_count",
    "admission_sleeve_match_count",
    "ultimate_package_non_admission_sleeve_match_count",
    "non_admission_sleeve_match_count",
    "ultimate_package_selector_shadow_score",
    "ultimate_package_combined_source_bound_signal_r_sum",
    "ultimate_package_max_combined_source_bound_signal_r",
    "ultimate_package_source_bound_r_additive_allowed",
    "ultimate_package_source_bound_r_additive_unit",
    "ultimate_package_source_bound_r_additive_scope",
    "ultimate_package_scheduler_parity_evidence_class",
    "ultimate_package_matched_member_axis_ids",
    "selected_package_matched_member_axis_ids",
    "ultimate_package_matched_member_axis_count",
    "ultimate_package_admission_member_axis_match_count",
    "ultimate_package_matched_member_axis_role_counts",
    "ultimate_package_member_axis_source_bound_signal_r_sum",
    "ultimate_package_member_axis_max_source_bound_signal_r",
    "ultimate_package_member_axis_source_bound_r_additive_allowed",
    "ultimate_package_member_axis_source_bound_r_additive_unit",
    "ultimate_package_member_axis_source_bound_r_additive_scope",
    "ultimate_package_member_axis_evidence_class",
    "ultimate_package_effective_matched_count",
    "ultimate_package_effective_admission_count",
    "ultimate_package_effective_source_bound_signal_r",
    "ultimate_package_effective_source_bound_r_additive_allowed",
    "ultimate_package_effective_source_bound_r_additive_unit",
    "ultimate_package_effective_source_bound_candidate_use_allowed",
    "ultimate_package_effective_executable_authority_allowed",
    "ultimate_package_effective_evidence_source",
    "ultimate_package_executable_admission_status",
    "ultimate_package_scheduler_consumed_status",
)


EXECUTION_DISPOSITION_PROPAGATED_COMPACT_FIELDS = (
    "expected_net_r",
    "candidate_expected_net_r",
    "probability",
    "candidate_probability",
    "fill_probability",
    "candidate_fill_probability",
    "source_completeness",
    "source_completeness_status",
    "candidate_decision_quality",
    "candidate_decision_quality_field_sources",
    "candidate_decision_quality_source_boundary",
    "candidate_decision_quality_alias_status",
    "candidate_decision_quality_alias_mismatches",
    "candidate_decision_quality_provenance_failures",
    "selector_action",
    "selector_reason",
    "scheduler_materialization_action_intent",
    "scheduler_materialization_original_action_intent",
    "scheduler_materialization_selector_action",
    "scheduler_materialization_selector_reason",
    "action_intent",
    "lifecycle_action",
    "risk_authority",
    "risk_authority_status",
    "risk_authority_packet_hash_sha256",
    "risk_config_source",
    "risk_per_trade_pct",
    "selected_cell_risk_pct",
    "scheduler_approved_risk_pct",
    "ultimate_candidate_package_packet_hash_sha256",
    "ultimate_candidate_package_packet_shape_hash_sha256",
    *CANONICAL_REPLAY_CONTEXT_ENVELOPE_FIELDS,
    *PACKAGE_AUTHORITY_FIELDS,
    "source_bound_package_candidate_use_allowed",
    "ultimate_package_source_bound_candidate_use_allowed",
    "package_replay_source_bound_candidate_use_allowed",
    "package_replay_candidate_use_allowed",
    "replay_candidate_use_allowed_now",
    "replay_candidate_use_allowed_now_reason",
    "selected_package_candidate_use_allowed_status",
    "ultimate_package_effective_source_bound_signal_r",
    "ultimate_package_effective_source_bound_candidate_use_allowed",
    "ultimate_package_effective_executable_authority_allowed",
    "ultimate_package_effective_admission_count",
    "ultimate_package_executable_admission_status",
    "ultimate_package_scheduler_consumed_status",
)


def stable_unique(values: Iterable[Any]) -> list[str]:
    if isinstance(values, (str, bytes, bytearray)):
        values = (values,)
    return sorted({str(value) for value in values if value not in (None, "")})


def list_values(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Iterable):
        return list(value)
    return [value]


def lifecycle_label_context_fields(
    labels: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    rows = [label for label in labels if isinstance(label, Mapping)]
    out: dict[str, Any] = {
        "lifecycle_label_context_row_count": len(rows),
        "lifecycle_label_context_present": False,
    }
    for field in LIFECYCLE_LABEL_CONTEXT_FIELDS:
        values = stable_unique(label.get(field) for label in rows)
        out[LIFECYCLE_LABEL_CONTEXT_LIST_FIELDS[field]] = values
        out[field] = values[0] if len(values) == 1 else None
        if values:
            out["lifecycle_label_context_present"] = True
    return out


def selected_package_denominator_use_reason(
    *,
    denominator_use_allowed: bool,
    canonical_alias_status: str,
    exact_candidate_id_match: bool,
    stable_window_unique_alias_allowed: bool,
    package_axis_unique_alias_allowed: bool,
    pending_proxy_match: bool,
    lifecycle_label_context_present: bool,
) -> str:
    if denominator_use_allowed:
        return canonical_alias_status
    if lifecycle_label_context_present and not pending_proxy_match:
        if (
            exact_candidate_id_match
            or stable_window_unique_alias_allowed
            or package_axis_unique_alias_allowed
        ):
            return "stable_window_lifecycle_context_present_denominator_authority_closed"
        return (
            "stable_window_lifecycle_context_present_"
            "candidate_id_namespace_mismatch_or_collision"
        )
    if lifecycle_label_context_present and pending_proxy_match:
        return "pending_created_lifecycle_context_present_denominator_authority_closed"
    if stable_window_unique_alias_allowed:
        return "stable_window_member_axis_unique_alias_context_only"
    if package_axis_unique_alias_allowed:
        return "package_axis_window_unique_alias_context_only"
    return "candidate_id_namespace_mismatch_or_collision"


def _safe_float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not (number == number) or number in (float("inf"), float("-inf")):
        return None
    return number


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "allowed", "pass"}
    return bool(value)


def _missing_value(value: Any) -> bool:
    return value in (None, "", [], {})


def _explicit_false(value: Any) -> bool:
    return value is False or str(value).strip().lower() in {"0", "false", "no", "off"}


def _v220_reallocation_contract_value(
    row: Mapping[str, Any],
    diagnostic: Mapping[str, Any],
    *fields: str,
) -> Any:
    for surface in (diagnostic, row):
        for field in fields:
            if field in surface and surface.get(field) not in (None, ""):
                return surface.get(field)
    return None


def _v220_reallocation_contract_list(
    row: Mapping[str, Any],
    diagnostic: Mapping[str, Any],
    *fields: str,
) -> tuple[bool, list[Any]]:
    for surface in (diagnostic, row):
        for field in fields:
            if field in surface:
                return True, list_values(surface.get(field))
    return False, []


def v220_hard_clean_capped_reduced_risk_contract_applies(
    row: Mapping[str, Any],
) -> bool:
    diagnostic = row.get("replacement_reallocation_quality")
    diagnostic = diagnostic if isinstance(diagnostic, Mapping) else {}
    marker = _truthy(
        _v220_reallocation_contract_value(
            row,
            diagnostic,
            "soft_risk_cap_transfer_eligible",
            "risk_admitted_scheduler_reallocation_soft_risk_cap_transfer_eligible",
            "replacement_reallocation_soft_risk_cap_transfer_eligible",
        )
    )
    stop_status = str(
        _v220_reallocation_contract_value(
            row,
            diagnostic,
            "stop_hazard_status",
            "replacement_reallocation_stop_hazard_status",
            "selected_policy_executable_quality_reallocation_stop_hazard_status",
        )
        or ""
    ).strip().lower()
    legacy_score = _safe_float_or_none(
        _v220_reallocation_contract_value(
            row,
            diagnostic,
            "legacy_mixed_reallocation_quality_score",
            "replacement_reallocation_legacy_mixed_quality_score",
        )
    )
    score_floor = _safe_float_or_none(
        _v220_reallocation_contract_value(
            row,
            diagnostic,
            "reallocation_quality_min_promotion_score",
            "selected_policy_executable_quality_min_reallocation_quality_score",
        )
    )
    return bool(
        marker
        or (
            stop_status == "capped"
            and legacy_score is not None
            and legacy_score < (score_floor if score_floor is not None else 0.0)
        )
    )


def v220_hard_clean_capped_reduced_risk_contract_allowed(
    row: Mapping[str, Any],
) -> bool:
    """Validate the exact V220 exception to a legacy below-floor mixed score."""

    diagnostic = row.get("replacement_reallocation_quality")
    diagnostic = diagnostic if isinstance(diagnostic, Mapping) else {}
    marker = _v220_reallocation_contract_value(
        row,
        diagnostic,
        "soft_risk_cap_transfer_eligible",
        "risk_admitted_scheduler_reallocation_soft_risk_cap_transfer_eligible",
        "replacement_reallocation_soft_risk_cap_transfer_eligible",
    )
    if marker is not True:
        return False
    raw_present, raw_hard_failures = _v220_reallocation_contract_list(
        row,
        diagnostic,
        "raw_hard_gate_failures",
        "replacement_reallocation_raw_hard_gate_failures",
        "selected_policy_executable_quality_reallocation_raw_hard_failures",
    )
    hard_present, hard_failures = _v220_reallocation_contract_list(
        row,
        diagnostic,
        "hard_gate_failures",
        "risk_admitted_scheduler_reallocation_hard_failures",
        "replacement_reallocation_quality_hard_gate_failures",
    )
    if not raw_present or raw_hard_failures or not hard_present or hard_failures:
        return False
    if _v220_reallocation_contract_value(
        row,
        diagnostic,
        "eligible_for_reallocation_promotion",
        "risk_admitted_scheduler_reallocation_eligible",
        "replacement_reallocation_quality_eligible",
    ) is not True:
        return False
    adjusted_transfer = _safe_float_or_none(
        _v220_reallocation_contract_value(
            row,
            diagnostic,
            "risk_cap_adjusted_expected_transfer_score",
            "replacement_reallocation_risk_cap_adjusted_expected_transfer_score",
            "selected_policy_executable_quality_reallocation_risk_cap_adjusted_expected_transfer_score",
        )
    )
    legacy_score = _safe_float_or_none(
        _v220_reallocation_contract_value(
            row,
            diagnostic,
            "legacy_mixed_reallocation_quality_score",
            "replacement_reallocation_legacy_mixed_quality_score",
        )
    )
    score_floor = _safe_float_or_none(
        _v220_reallocation_contract_value(
            row,
            diagnostic,
            "reallocation_quality_min_promotion_score",
            "selected_policy_executable_quality_min_reallocation_quality_score",
        )
    )
    score_floor = score_floor if score_floor is not None else 0.0
    if adjusted_transfer is None or adjusted_transfer <= 0.0:
        return False
    if legacy_score is None or legacy_score >= score_floor:
        return False
    if not _explicit_false(
        _v220_reallocation_contract_value(
            row,
            diagnostic,
            "legacy_mixed_reallocation_quality_score_authority",
        )
    ):
        return False
    if (
        _v220_reallocation_contract_value(
            row,
            diagnostic,
            "reallocation_quality_score_policy",
        )
        != V220_CAPPED_REALLOCATION_SCORE_POLICY
    ):
        return False
    boundary = str(
        _v220_reallocation_contract_value(
            row,
            diagnostic,
            "source_boundary",
            "replacement_reallocation_quality_source_boundary",
        )
        or ""
    ).lower().replace("-", "_").replace(" ", "_")
    if "predecision" not in boundary or "no_outcome" not in boundary:
        return False
    if not _explicit_false(
        _v220_reallocation_contract_value(
            row,
            diagnostic,
            "uses_outcome_fields",
            "replacement_reallocation_quality_uses_outcome_fields",
        )
    ):
        return False
    stop_status = str(
        _v220_reallocation_contract_value(
            row,
            diagnostic,
            "stop_hazard_status",
            "replacement_reallocation_stop_hazard_status",
        )
        or ""
    ).strip().lower()
    risk_cap_factor = _safe_float_or_none(
        _v220_reallocation_contract_value(
            row,
            diagnostic,
            "risk_cap_transfer_factor",
            "replacement_reallocation_risk_cap_transfer_factor",
        )
    )
    if stop_status != "capped" or risk_cap_factor is None or not 0.0 < risk_cap_factor <= 1.0:
        return False
    cap_applied = _first_present(
        row.get("predecision_stop_hazard_guard_risk_cap_applied"),
        row.get("selected_policy_executable_quality_risk_cap_applied"),
        row.get("risk_finalizer_predecision_stop_hazard_guard_risk_cap_applied"),
    )
    if not _truthy(cap_applied):
        return False
    stop_action = _first_present(
        row.get("predecision_stop_hazard_guard_action"),
        row.get("risk_finalizer_predecision_stop_hazard_guard_action"),
    )
    if str(stop_action or "").strip().lower() not in {
        "cap",
        "capped",
    }:
        return False
    risk_ladder = row.get("risk_expression_ladder")
    risk_ladder = risk_ladder if isinstance(risk_ladder, Mapping) else {}
    full_risk_allowed = _first_present(
        row.get("package_risk_expression_full_risk_allowed"),
        row.get("full_risk_allowed"),
        risk_ladder.get("full_risk_allowed"),
    )
    full_risk_applied = _first_present(
        row.get("package_risk_expression_full_risk_applied"),
        row.get("full_risk_applied"),
        risk_ladder.get("full_risk_applied"),
    )
    if not _explicit_false(full_risk_allowed):
        return False
    if not _explicit_false(full_risk_applied):
        return False
    if row.get("package_replay_order_executable_candidate_use_allowed") is not True:
        return False
    if not trusted_signed_package_new_entry_authority_surface(row):
        return False
    if str(row.get("pretrade_cost_packet_status") or "").strip().upper() != "PASSED":
        return False
    if str(row.get("cost_authority") or "").strip() != "broker_calibrated_replay_cost":
        return False
    if str(row.get("cost_source_gap_status") or "").strip() != "source_bound_cost_authority_present":
        return False
    if row.get("candidate_cost_r_fallback_is_authority") is not False:
        return False
    if _truthy(row.get("source_gap_cost_fallback_blocked")):
        return False
    source_completeness = _safe_float_or_none(row.get("source_completeness"))
    source_status = str(row.get("source_completeness_status") or "").strip().lower()
    if source_completeness is None or source_completeness < 0.95:
        return False
    if source_status not in {
        "complete",
        "source_completeness_present",
        "source_complete_for_timewarp_candidate",
    }:
        return False
    terminal_vetoes = stable_unique(
        list_values(row.get("terminal_vetoes"))
        + list_values(row.get("scheduler_terminal_vetoes"))
        + list_values(row.get("reallocation_soft_guard_pool_terminal_vetoes"))
    )
    if terminal_vetoes:
        return False
    if row.get("source_required_lifecycle_origin") is True and not any(
        row.get(field) is True
        for field in (
            "source_required_package_risk_lifecycle_reconcile_applied",
            "risk_lifecycle_action_reconciled_from_scheduler",
            "execution_manager_same_symbol_lifecycle_permission_reconcile_applied",
        )
    ):
        return False
    for field in (
        "broker_order_lifecycle_truth_satisfied",
        "same_symbol_lifecycle_permitted",
        "package_lifecycle_root_authority_allowed",
    ):
        if row.get(field) is False:
            return False
    if any(
        _truthy(row.get(field))
        for field in (
            "selected_policy_executable_quality_lifecycle_authority_blocked",
            "package_lifecycle_root_hard_blocked",
            "package_lifecycle_root_authority_not_allowed",
        )
    ):
        return False
    if row.get("package_authority_has_order_geometry") is False:
        return False
    blocker_class = str(
        row.get("package_replay_order_executable_final_blocker_class") or ""
    ).strip()
    return blocker_class in {"", "scheduler_selection", "selector_materialization"}


def scheduler_materialization_skip_is_soft_transfer(
    row: Mapping[str, Any],
    skip_reason: str,
) -> bool:
    """Allow only self-referential scheduler/materialization skips past B7 gates."""

    reason = str(skip_reason or "").strip().lower()
    if not reason:
        return False
    if row.get("package_replay_order_executable_candidate_use_allowed") is False:
        return False
    if any(token in reason for token in SCHEDULER_MATERIALIZATION_TERMINAL_SKIP_TOKENS):
        return False
    has_soft_skip_shape = any(
        token in reason for token in SCHEDULER_MATERIALIZATION_SOFT_TRANSFER_SKIP_TOKENS
    )
    capped_score_skip = any(
        token in reason for token in V220_HARD_CLEAN_CAPPED_SOFT_SKIP_TOKENS
    )
    capped_contract_applies = v220_hard_clean_capped_reduced_risk_contract_applies(
        row
    )
    if capped_score_skip or capped_contract_applies:
        if not (has_soft_skip_shape or capped_score_skip):
            return False
        return v220_hard_clean_capped_reduced_risk_contract_allowed(row)
    if not has_soft_skip_shape:
        return False
    blocker_class = str(
        row.get("package_replay_order_executable_final_blocker_class") or ""
    ).strip()
    if row.get("package_replay_order_executable_candidate_use_allowed") is True:
        return blocker_class in {"scheduler_selection", "selector_materialization"}
    soft_guard_contract = row.get("scheduler_terminal_vs_soft_guard")
    soft_guard_contract = (
        soft_guard_contract if isinstance(soft_guard_contract, Mapping) else {}
    )
    soft_vetoes = (
        list_values(row.get("reallocation_soft_guard_vetoes"))
        or list_values(row.get("scheduler_reallocation_soft_guard_vetoes"))
        or list_values(soft_guard_contract.get("soft_guard_vetoes"))
    )
    terminal_vetoes = (
        list_values(row.get("terminal_vetoes"))
        or list_values(row.get("scheduler_terminal_vetoes"))
        or list_values(row.get("reallocation_soft_guard_pool_terminal_vetoes"))
        or list_values(soft_guard_contract.get("terminal_vetoes"))
    )
    pool_status = str(
        row.get("reallocation_soft_guard_pool_status")
        or soft_guard_contract.get("pool_status")
        or ""
    ).strip().lower()
    pool_eligible = _truthy(
        _first_present(
            row.get("reallocation_soft_guard_pool_eligible"),
            soft_guard_contract.get("pool_eligible"),
        )
    )
    return bool(
        pool_eligible
        and soft_vetoes
        and not terminal_vetoes
        and pool_status in {"", "eligible"}
    )


def bridge_route_provenance_fields(*rows: Mapping[str, Any] | None) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for key in ROUTE_PROVENANCE_FIELDS:
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            value = row.get(key)
            if _missing_value(value):
                value = row.get(f"candidate_{key}")
            if _missing_value(value):
                value = row.get(f"selected_scheduler_{key}")
            if not _missing_value(value):
                fields[key] = value
                break
    if "current_framework" not in fields and not _missing_value(fields.get("framework")):
        fields["current_framework"] = fields["framework"]
    if "origin_family" not in fields and not _missing_value(
        fields.get("candidate_origin_family")
    ):
        fields["origin_family"] = fields["candidate_origin_family"]
    if "candidate_origin_family" not in fields and not _missing_value(
        fields.get("origin_family")
    ):
        fields["candidate_origin_family"] = fields["origin_family"]
    if "route_session" not in fields:
        route_session = next(
            (
                fields[key]
                for key in ("session_bucket", "session")
                if not _missing_value(fields.get(key))
            ),
            None,
        )
        if not _missing_value(route_session):
            fields["route_session"] = route_session
    if "session_bucket" not in fields:
        session_bucket = next(
            (
                fields[key]
                for key in ("route_session", "session")
                if not _missing_value(fields.get(key))
            ),
            None,
        )
        if not _missing_value(session_bucket):
            fields["session_bucket"] = session_bucket
    if "session" not in fields:
        session = next(
            (
                fields[key]
                for key in ("route_session", "session_bucket")
                if not _missing_value(fields.get(key))
            ),
            None,
        )
        if not _missing_value(session):
            fields["session"] = session
    return fields


def _scorecard_has_final_selected_candidate(row: Mapping[str, Any]) -> bool:
    if not _missing_value(row.get("selected_candidate_id")):
        return True
    selected_ids = row.get("selected_candidate_ids")
    if isinstance(selected_ids, (str, bytes, bytearray)):
        return bool(str(selected_ids or "").strip())
    if isinstance(selected_ids, Iterable):
        return any(not _missing_value(item) for item in selected_ids)
    return False


def _scrub_scorecard_no_final_selection_candidate_authority(
    row: dict[str, Any],
) -> None:
    if _scorecard_has_final_selected_candidate(row):
        return
    scrubbed: list[str] = []
    for field in SCORECARD_NO_FINAL_SELECTION_PREFIX_ONLY_FIELDS:
        value = row.get(field)
        if _missing_value(value):
            row.setdefault(field, None)
            continue
        row.setdefault(f"scorecard_reported_{field}", value)
        row.setdefault(f"selected_package_status_{field}", value)
        row[field] = None
        scrubbed.append(field)
    if scrubbed:
        row["scorecard_no_final_selection_candidate_authority_scrubbed"] = True
        row["scorecard_no_final_selection_scrubbed_fields"] = sorted(set(scrubbed))


def normalize_window_selected_candidate_identity(row: dict[str, Any]) -> None:
    candidate_id = str(row.get("candidate_id") or "").strip()
    if not candidate_id:
        return
    selected_candidate_id = str(row.get("selected_candidate_id") or "").strip()
    if selected_candidate_id and selected_candidate_id != candidate_id:
        row["window_selected_candidate_id"] = selected_candidate_id
        row["selected_candidate_id"] = None
        row["selected_candidate_identity_status"] = (
            "window_selected_candidate_not_row_candidate"
        )
    selected_ids = row.get("selected_candidate_ids")
    if isinstance(selected_ids, (str, bytes, bytearray)):
        selected_id_values = [
            item.strip()
            for item in str(selected_ids).split(",")
            if item.strip()
        ]
    elif isinstance(selected_ids, Iterable):
        selected_id_values = [
            str(item).strip() for item in selected_ids if str(item or "").strip()
        ]
    else:
        selected_id_values = []
    mismatched_ids = [
        selected_id for selected_id in selected_id_values if selected_id != candidate_id
    ]
    if mismatched_ids:
        row["window_selected_candidate_ids"] = sorted(set(mismatched_ids))
        row["selected_candidate_ids"] = (
            [candidate_id] if candidate_id in selected_id_values else []
        )
        row.setdefault(
            "selected_candidate_identity_status",
            "window_selected_candidates_not_row_candidate",
        )


def _canonical_utc_iso(value: Any) -> str | None:
    if _missing_value(value):
        return None
    parsed = timewarp_loop.parse_utc(str(value or ""))
    if parsed is None:
        return str(value or "").strip() or None
    return parsed.astimezone(timezone.utc).isoformat()


def _candidate_time_instance_key(candidate_id: Any, decision_time: Any) -> str | None:
    candidate_id_text = str(candidate_id or "").strip()
    decision_time_iso = _canonical_utc_iso(decision_time)
    if not candidate_id_text or not decision_time_iso:
        return None
    return f"{candidate_id_text}@@{decision_time_iso}"


def _profit_harvest_row_decision_time(row: Mapping[str, Any]) -> Any:
    return _first_non_missing(
        row,
        (
            "decision_time_utc",
            "selected_scheduler_decision_time_utc",
            "scheduler_decision_time_utc",
            "asof_utc",
            "source_candle_time_utc",
            "candle_close_utc",
        ),
    )


SIGNED_REDUCED_PACKAGE_NEW_ENTRY_ACTIONS = REDUCED_RISK_SIGNED_NEW_ENTRY_ACTION_INTENTS
SIGNED_REDUCED_PACKAGE_NEW_ENTRY_AUTHORITY_BLOCK_PREFIX = (
    "selector_reduced_package_new_entry_signed_authority_invalid"
)
SIGNED_PACKAGE_AUTHORITY_CURRENT_DECISION_FIELDS = (
    "expected_net_r",
    "probability",
    "confidence",
    "fill_probability",
    "source_completeness",
    "entry_quality_fill_probability",
    "limit_fillability_probability",
    "predecision_limit_fillability_probability",
    "execution_fill_probability",
    "execution_fill_probability_source",
    "candidate_decision_quality_field_sources",
    "candidate_decision_quality_source_boundary",
    "candidate_decision_quality_alias_status",
    "candidate_decision_quality_alias_mismatches",
    "candidate_decision_quality_provenance_failures",
    "pretrade_cost_packet_status",
    "cost_source_gap_status",
    "cost_authority",
    "candidate_cost_r_fallback_is_authority",
    "source_completeness_status",
    "source_bound_package_candidate_use_allowed",
    "source_bound_router_refusal_materialization_floors",
    "selected_policy_for_expected_net_r",
    "selected_policy_expected_net_calibration_status",
    "selected_policy_expected_net_calibrated",
    "selected_policy_expected_net_calibration_required",
    "selected_policy_expected_net_calibration_source",
    "selected_policy_expected_net_calibration_source_boundary",
    "selected_policy_expected_net_calibration_hash",
    "package_replay_order_executable_candidate_use_allowed",
    "package_replay_order_executable_candidate_use_allowed_reason",
    "package_replay_order_executable_authority_source",
)


def normalize_bridge_action_intent(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw.startswith("invalid_action_intent:"):
        raw = raw.split(":", 1)[1]
    return SCHEDULER_ACTION_INTENT_ALIASES.get(raw, raw)


def open_reduced_bridge_authority_allowed(row: Mapping[str, Any]) -> bool:
    authority = row.get("ultimate_candidate_package_open_reduced_risk_authority")
    authority = authority if isinstance(authority, Mapping) else {}
    return bool(
        row.get("package_open_reduced_authority_allowed") is True
        or row.get("selected_scheduler_package_open_reduced_authority_allowed") is True
        or authority.get("allowed") is True
    )


def _trusted_signed_package_new_entry_expected_action(
    row: Mapping[str, Any],
    action_intent: Any | None = None,
) -> str:
    raw_action = (
        action_intent
        if not _missing_value(action_intent)
        else _first_non_missing(
            row,
            (
                "scheduler_materialization_action_intent",
                "action_intent",
                "lifecycle_action",
                "same_symbol_lifecycle_action",
                "gtos_vnext_same_symbol_lifecycle_action",
            ),
        )
    )
    return normalize_bridge_action_intent(raw_action)


def trusted_signed_package_new_entry_authority_surface(
    row: Mapping[str, Any],
    *,
    action_intent: Any | None = None,
) -> bool:
    if row.get("package_new_entry_authority_required") is not True:
        return False
    if row.get("package_new_entry_authority_valid") is not True:
        return False
    status = str(row.get("package_new_entry_authority_status") or "").strip()
    if status and status != "valid_signed_predecision_new_entry_authority":
        return False
    failures = row.get("package_new_entry_authority_failures")
    if failures not in (None, "", [], (), {}):
        return False
    authority_hash = str(row.get("package_new_entry_authority_hash_sha256") or "").strip()
    expected_hash = str(
        row.get("expected_package_new_entry_authority_hash_sha256")
        or authority_hash
        or ""
    ).strip()
    if len(authority_hash) != 64 or len(expected_hash) != 64:
        return False
    if authority_hash != expected_hash:
        return False
    try:
        int(authority_hash, 16)
        int(expected_hash, 16)
    except ValueError:
        return False
    if row.get("package_new_entry_authority_uses_outcome_fields") is True:
        return False
    expected_action = _trusted_signed_package_new_entry_expected_action(
        row,
        action_intent,
    )
    normalized_selector_action = normalize_selector_action_for_reason(
        row.get("package_new_entry_authority_selector_action")
        or row.get("selector_action"),
        row.get("package_new_entry_authority_selector_reason")
        or row.get("selector_reason"),
        expected_action or "new_position",
    )
    if timewarp_loop.package_new_entry_authority_immutable_payload_failures(
        row,
        normalized_selector_action=normalized_selector_action,
        normalized_action=expected_action,
    ):
        return False
    if expected_action:
        signed_target_action = normalize_bridge_action_intent(
            row.get("package_new_entry_authority_target_action_intent")
        )
        if not signed_target_action or signed_target_action != expected_action:
            return False
    identity_checks = (
        (
            "package_new_entry_authority_candidate_id",
            "candidate_id",
        ),
        (
            "package_new_entry_authority_decision_time_utc",
            "decision_time_utc",
        ),
        (
            "package_new_entry_authority_canonical_replay_candidate_instance_key",
            "canonical_replay_candidate_instance_key",
        ),
        (
            "package_new_entry_authority_source_bound_replay_candidate_instance_key",
            "source_bound_replay_candidate_instance_key",
        ),
    )
    for signed_field, row_field in identity_checks:
        signed_value = str(row.get(signed_field) or "").strip()
        row_value = str(row.get(row_field) or "").strip()
        if not signed_value or not row_value or signed_value != row_value:
            return False
    signed_identity_status = str(
        row.get("package_new_entry_authority_candidate_instance_identity_status")
        or ""
    ).strip()
    if not signed_identity_status or signed_identity_status.startswith("missing"):
        return False
    boundary = str(row.get("package_new_entry_authority_source_boundary") or "").lower()
    boundary = boundary.replace("-", "_").replace(" ", "_")
    if not ("predecision" in boundary and "no_outcome" in boundary):
        return False
    quality_sources = row.get(
        "package_new_entry_authority_candidate_decision_quality_field_sources"
    )
    if not isinstance(quality_sources, Mapping):
        return False
    for field in (
        "expected_net_r",
        "probability",
        "fill_probability",
        "source_completeness",
    ):
        if _missing_value(quality_sources.get(field)):
            return False
    quality_boundary = str(
        row.get("package_new_entry_authority_candidate_decision_quality_source_boundary")
        or ""
    ).lower()
    quality_boundary = quality_boundary.replace("-", "_").replace(" ", "_")
    if not ("predecision" in quality_boundary and "no_outcome" in quality_boundary):
        return False
    if (
        row.get("package_new_entry_authority_candidate_decision_quality_alias_status")
        != "exact_materialized"
    ):
        return False
    if row.get("package_new_entry_authority_candidate_decision_quality_alias_mismatches") not in (
        None,
        "",
        [],
        (),
        {},
    ):
        return False
    if row.get("package_new_entry_authority_candidate_decision_quality_provenance_failures") not in (
        None,
        "",
        [],
        (),
        {},
    ):
        return False
    selected_policy_failure = selected_policy_expected_net_calibration_failure_reason(
        row
    )
    if selected_policy_failure:
        return False
    if _router_refusal_open_reduced_authority_applies(row):
        floors = _candidate_quality_floor_requirements(row)
        expected_net_r = _first_numeric(row, "expected_net_r", "candidate_expected_net_r")
        probability = _first_numeric(row, "probability", "candidate_probability")
        fill_probability, _fill_source = execution_fillability_authority(row)
        source_completeness = _first_numeric(
            row,
            "source_completeness",
            "candidate_source_completeness",
        )
        if expected_net_r is None or expected_net_r < floors["expected_net_r"]:
            return False
        if probability is None or probability < floors["probability"]:
            return False
        if fill_probability is None or fill_probability < floors["fill_probability"]:
            return False
        if (
            source_completeness is None
            or source_completeness < PACKAGE_BRIDGE_ROUTER_REFUSAL_MIN_SOURCE_COMPLETENESS
        ):
            return False
    return True


def signed_reduced_package_bridge_authority_block_reason(
    row: Mapping[str, Any],
    *,
    selector_action: str,
    selector_reason: str,
    action_intent: str,
) -> str | None:
    normalized_action_intent = normalize_bridge_action_intent(action_intent) or "new_position"
    if normalized_action_intent not in SIGNED_REDUCED_PACKAGE_NEW_ENTRY_ACTIONS:
        return None
    if selector_action not in {"reduce-risk", "open-reduced-risk"}:
        return None
    validation = bridge_reduced_package_new_entry_authority_validation(
        row,
        selector_action=selector_action,
        selector_reason=selector_reason,
        action_intent=normalized_action_intent,
    )
    lightweight_trusted = trusted_signed_package_new_entry_authority_surface(
        row,
        action_intent=normalized_action_intent,
    )
    open_reduced_authority = row.get("ultimate_candidate_package_open_reduced_risk_authority")
    open_reduced_authority = (
        open_reduced_authority if isinstance(open_reduced_authority, Mapping) else {}
    )
    reduce_authority = row.get("ultimate_candidate_package_reduce_risk_authority")
    reduce_authority = reduce_authority if isinstance(reduce_authority, Mapping) else {}
    signed_hash_present = bool(
        str(
            row.get("package_new_entry_authority_hash_sha256")
            or open_reduced_authority.get("package_new_entry_authority_hash_sha256")
            or open_reduced_authority.get("authority_hash_sha256")
            or reduce_authority.get("package_new_entry_authority_hash_sha256")
            or reduce_authority.get("authority_hash_sha256")
            or ""
        ).strip()
    )
    if (
        _router_refusal_open_reduced_authority_applies(row)
        and normalized_action_intent == "new_position"
        and signed_hash_present
    ):
        floors = _candidate_quality_floor_requirements(
            row,
            action_intent=normalized_action_intent,
        )
        expected_net_r = _first_numeric(row, "expected_net_r", "candidate_expected_net_r")
        probability = _first_numeric(row, "probability", "candidate_probability")
        fill_probability, _fill_source = execution_fillability_authority(row)
        source_completeness = _first_numeric(
            row,
            "source_completeness",
            "candidate_source_completeness",
        )
        router_failures: list[str] = []
        if expected_net_r is None or expected_net_r < floors["expected_net_r"]:
            router_failures.append("router_refusal_expected_net_r_below_floor")
        if probability is None or probability < floors["probability"]:
            router_failures.append("router_refusal_probability_below_floor")
        if fill_probability is None or fill_probability < floors["fill_probability"]:
            router_failures.append("router_refusal_fill_probability_below_floor")
        if (
            source_completeness is None
            or source_completeness < PACKAGE_BRIDGE_ROUTER_REFUSAL_MIN_SOURCE_COMPLETENESS
        ):
            router_failures.append("router_refusal_source_completeness_below_floor")
        if router_failures:
            return (
                f"{SIGNED_REDUCED_PACKAGE_NEW_ENTRY_AUTHORITY_BLOCK_PREFIX}:"
                + "|".join(router_failures)
            )
    if validation.get("required") is not True:
        return None
    if validation.get("valid") is not True:
        raw_failures = [
            str(item)
            for item in validation.get("failures") or ()
            if str(item or "").strip()
        ]
        if "authority_hash_missing" in raw_failures:
            raw_failures = ["authority_hash_missing"]
        failures = "|".join(raw_failures)
        return (
            f"{SIGNED_REDUCED_PACKAGE_NEW_ENTRY_AUTHORITY_BLOCK_PREFIX}:"
            f"{failures or validation.get('status') or 'invalid_or_missing_signed_new_entry_authority'}"
        )
    if not lightweight_trusted:
        return (
            f"{SIGNED_REDUCED_PACKAGE_NEW_ENTRY_AUTHORITY_BLOCK_PREFIX}:"
            "signed_authority_surface_contract_invalid"
        )
    return None


def _bridge_reduced_authority_candidates(
    row: Mapping[str, Any],
    *,
    selector_action: str,
    selector_reason: str,
) -> list[tuple[str, Mapping[str, Any]]]:
    action_intent = normalize_bridge_action_intent(
        row.get("scheduler_materialization_action_intent")
        or row.get("action_intent")
        or row.get("lifecycle_action")
        or "new_position"
    )
    normalized_selector_action = normalize_selector_action_for_reason(
        selector_action,
        selector_reason,
        action_intent,
    )
    raw_selector_action = str(selector_action or "").strip().lower()
    reduce_authority = _mapping(
        row.get("ultimate_candidate_package_reduce_risk_authority")
        or row.get("ultimate_candidate_package_reduced_risk_authority")
    )
    open_reduced_authority = _mapping(
        row.get("ultimate_candidate_package_open_reduced_risk_authority")
    )
    ordered_fields: list[tuple[str, Mapping[str, Any]]] = []
    if normalized_selector_action == "open-reduced-risk" and open_reduced_authority:
        ordered_fields.append(
            (
                "ultimate_candidate_package_open_reduced_risk_authority",
                open_reduced_authority,
            )
        )
    if (
        raw_selector_action == "reduce-risk"
        and normalized_selector_action != "open-reduced-risk"
        and reduce_authority
    ):
        ordered_fields.append(
            ("ultimate_candidate_package_reduce_risk_authority", reduce_authority)
        )
    if open_reduced_authority:
        ordered_fields.append(
            (
                "ultimate_candidate_package_open_reduced_risk_authority",
                open_reduced_authority,
            )
        )
    if reduce_authority:
        ordered_fields.append(
            ("ultimate_candidate_package_reduce_risk_authority", reduce_authority)
        )
    seen: set[str] = set()
    out: list[tuple[str, Mapping[str, Any]]] = []
    for field, authority in ordered_fields:
        key = f"{field}:{stable_sha256(authority)}"
        if key in seen:
            continue
        seen.add(key)
        out.append((field, authority))
    return out


def _bridge_materialize_signed_reduced_authority(
    row: Mapping[str, Any],
    *,
    selector_action: str,
    selector_reason: str,
    action_intent: str,
) -> dict[str, Any]:
    """Stamp existing package reduced/open-reduced authority before validation."""

    out = dict(row)
    normalized_action_intent = normalize_bridge_action_intent(action_intent) or "new_position"
    if trusted_signed_package_new_entry_authority_surface(
        out,
        action_intent=normalized_action_intent,
    ):
        full_validation = bridge_reduced_package_new_entry_authority_validation(
            out,
            selector_action=selector_action,
            selector_reason=selector_reason,
            action_intent=normalized_action_intent,
        )
        if (
            full_validation.get("required") is not True
            or full_validation.get("valid") is True
        ):
            _project_final_signed_fillability(out)
            return out
    stale_target_action = normalize_bridge_action_intent(
        out.get("package_new_entry_authority_target_action_intent")
    )
    if stale_target_action and stale_target_action != normalized_action_intent:
        out["package_new_entry_authority_bridge_stale_target_action_intent"] = (
            stale_target_action
        )
        out["package_new_entry_authority_bridge_restamp_required_reason"] = (
            "signed_authority_target_action_mismatch"
        )
    if normalized_action_intent not in SIGNED_REDUCED_PACKAGE_NEW_ENTRY_ACTIONS:
        return out
    for field, authority in _bridge_reduced_authority_candidates(
        out,
        selector_action=selector_action,
        selector_reason=selector_reason,
    ):
        if not authority:
            continue
        try:
            stamp_row = bridge_row_with_execution_fillability_for_stamp(out)
            predecessor_payload = authority.get(
                "package_new_entry_authority_payload"
            )
            predecessor_payload = (
                predecessor_payload
                if isinstance(predecessor_payload, Mapping)
                else {}
            )
            predecessor_action = normalize_bridge_action_intent(
                predecessor_payload.get("target_action_intent")
            )
            predecessor_selector_action = normalize_selector_action_for_reason(
                predecessor_payload.get("selector_action"),
                predecessor_payload.get("selector_reason"),
                predecessor_action or normalized_action_intent,
            )
            predecessor_surface = {**out, **authority}
            predecessor_valid = bool(
                predecessor_payload
                and predecessor_action
                and not timewarp_loop.package_new_entry_authority_immutable_payload_failures(
                    predecessor_surface,
                    normalized_selector_action=predecessor_selector_action,
                    normalized_action=predecessor_action,
                )
            )
            if predecessor_valid and predecessor_action != normalized_action_intent:
                stamp_row = dict(stamp_row)
                for action_field in (
                    "scheduler_materialization_action_intent",
                    "action_intent",
                    "lifecycle_action",
                    "same_symbol_lifecycle_action",
                    "gtos_vnext_same_symbol_lifecycle_action",
                ):
                    if action_field in stamp_row or action_field == (
                        "scheduler_materialization_action_intent"
                    ):
                        stamp_row[action_field] = predecessor_action
            stamp_authority = bridge_authority_with_execution_fillability_for_stamp(
                authority,
                stamp_row,
            )
            stamped = stamp_package_new_entry_authority(
                stamp_row,
                selector_action=selector_action,
                selector_reason=selector_reason,
                action_intent=normalized_action_intent,
                authority=stamp_authority,
            )
        except Exception:
            continue
        if not stamped:
            continue
        authority_field = (
            stamped.get("package_new_entry_authority_authority_field")
            or field
        )
        nested_authority = _bridge_finalized_signed_authority(
            stamp_authority,
            stamped,
        )
        if authority_field:
            out[str(authority_field)] = nested_authority
        for signed_field in PACKAGE_AUTHORITY_FIELDS:
            value = stamped.get(signed_field)
            if signed_field in PACKAGE_AUTHORITY_EMPTY_LIST_FIELDS:
                missing = value in (None, "", {})
            else:
                missing = _missing_value(value)
            if not missing:
                out[signed_field] = value
        _project_final_signed_fillability(out)
        trusted_materialized = trusted_signed_package_new_entry_authority_surface(
            out,
            action_intent=normalized_action_intent,
        )
        full_validation = bridge_reduced_package_new_entry_authority_validation(
            out,
            selector_action=selector_action,
            selector_reason=selector_reason,
            action_intent=normalized_action_intent,
        )
        if (
            trusted_materialized
            and full_validation.get("required") is True
            and full_validation.get("valid") is True
        ):
            out["package_new_entry_authority_bridge_materialized"] = True
            out["package_new_entry_authority_bridge_materialized_from_field"] = field
            if predecessor_valid and predecessor_action != normalized_action_intent:
                out["package_new_entry_authority_predecessor_payload"] = dict(
                    predecessor_payload
                )
                out["package_new_entry_authority_predecessor_hash_sha256"] = (
                    predecessor_surface.get(
                        "package_new_entry_authority_hash_sha256"
                    )
                )
                out["package_new_entry_authority_predecessor_action_intent"] = (
                    predecessor_action
                )
            return out
    return out


def _promote_trusted_package_authority_fields(
    row: dict[str, Any],
    authority_fields: Mapping[str, Any],
) -> None:
    """Make bridge-derived signed authority the verifier-facing surface."""

    if not authority_fields:
        return

    def authority_field_missing(field: str, value: Any) -> bool:
        if field in PACKAGE_AUTHORITY_EMPTY_LIST_FIELDS:
            return value in (None, "", {})
        return _missing_value(value)

    def backfill_root_identity_from_signed_authority(target: dict[str, Any]) -> None:
        for signed_field, root_field in PACKAGE_AUTHORITY_IDENTITY_ROOT_BACKFILLS.items():
            signed_value = target.get(signed_field)
            if authority_field_missing(signed_field, signed_value):
                continue
            if _missing_value(target.get(root_field)):
                target[root_field] = signed_value

    promoted = dict(row)
    for field in PACKAGE_AUTHORITY_FIELDS:
        value = authority_fields.get(field)
        if not authority_field_missing(field, value):
            promoted[field] = value
    backfill_root_identity_from_signed_authority(promoted)
    force_promote = trusted_signed_package_new_entry_authority_surface(promoted)
    derived_failures = [
        str(item)
        for item in authority_fields.get("package_new_entry_authority_failures") or ()
        if str(item or "").strip()
    ]
    force_root_missing_signature = "authority_hash_missing" in derived_failures
    for field in PACKAGE_AUTHORITY_FIELDS:
        value = authority_fields.get(field)
        if authority_field_missing(field, value):
            continue
        current = row.get(field)
        if authority_field_missing(field, current):
            row[field] = value
            continue
        if force_promote and current != value:
            row.setdefault(f"diagnostic_stale_{field}", current)
            row[field] = value
            continue
        if force_root_missing_signature and field in {
            "package_new_entry_authority_failures",
            "package_new_entry_authority_valid",
            "package_new_entry_authority_status",
            "package_new_entry_authority_hash_sha256",
            "expected_package_new_entry_authority_hash_sha256",
        } and current != value:
            row.setdefault(f"diagnostic_stale_{field}", current)
            row[field] = value
    backfill_root_identity_from_signed_authority(row)


_BRIDGE_PRIVATE_STAMP_FILL_FIELDS = {
    "candidate_decision_quality_field_sources",
    "entry_quality_fill_probability",
    "limit_fillability_probability",
    "predecision_limit_fillability_probability",
    "execution_fill_probability",
    "execution_fill_probability_source",
    "execution_fill_probability_source_time_utc",
    "execution_fill_probability_source_boundary",
    "execution_fill_probability_authority_class",
    "predecision_limit_fillability",
}


def _bridge_finalized_signed_authority(
    authority: Mapping[str, Any],
    stamped: Mapping[str, Any],
) -> dict[str, Any]:
    """Keep raw inputs private while retaining the signer's final projections."""

    finalized = {
        key: copy.deepcopy(value)
        for key, value in authority.items()
        if key not in _BRIDGE_PRIVATE_STAMP_FILL_FIELDS
    }
    finalized.update(copy.deepcopy(dict(stamped)))
    return finalized


def _signed_execution_payload_from_surface(
    row: Mapping[str, Any],
) -> Mapping[str, Any]:
    authority_fields = timewarp_loop.package_new_entry_authority_attribution_fields(
        row
    )
    if authority_fields.get("package_new_entry_authority_valid") is not True:
        return {}
    payload = authority_fields.get("package_new_entry_authority_payload")
    if isinstance(payload, Mapping):
        return payload
    return {}


def _validated_signed_member_axis_ids(row: Mapping[str, Any]) -> list[str]:
    """Carry exact member axes only from a fully valid current signature."""

    action_intent = normalize_bridge_action_intent(
        row.get("scheduler_materialization_action_intent")
        or row.get("action_intent")
        or row.get("lifecycle_action")
        or "new_position"
    ) or "new_position"
    selector_action = str(row.get("selector_action") or "").strip()
    selector_reason = str(row.get("selector_reason") or "").strip()
    if not trusted_signed_package_new_entry_authority_surface(
        row,
        action_intent=action_intent,
    ):
        return []
    validation = bridge_reduced_package_new_entry_authority_validation(
        row,
        selector_action=selector_action,
        selector_reason=selector_reason,
        action_intent=action_intent,
    )
    if validation.get("required") is True and validation.get("valid") is not True:
        return []
    payload = _signed_execution_payload_from_surface(row)
    signed_axes = stable_unique(payload.get("matched_member_axis_ids") or ())
    current_axes = stable_unique(
        row.get("ultimate_package_matched_member_axis_ids")
        or row.get("selected_package_matched_member_axis_ids")
        or ()
    )
    return signed_axes if signed_axes and current_axes == signed_axes else []


def _project_final_signed_fillability(row: dict[str, Any]) -> bool:
    """Project one validated signed fill envelope onto flat and nested aliases."""

    execution_fill, execution_source = execution_fillability_authority(row)
    if execution_fill is None:
        return False
    payload = _signed_execution_payload_from_surface(row)
    if not payload:
        return False
    payload_execution_fill = _safe_float_or_none(
        payload.get("execution_fill_probability")
    )
    payload_execution_source = str(
        payload.get("execution_fill_probability_source") or ""
    ).strip()
    payload_execution_source_time = str(
        payload.get("execution_fill_probability_source_time_utc") or ""
    ).strip()
    payload_execution_source_boundary = str(
        payload.get("execution_fill_probability_source_boundary") or ""
    ).strip()
    payload_execution_authority_class = str(
        payload.get("execution_fill_probability_authority_class") or ""
    ).strip()
    payload_source_dt = timewarp_loop.parse_utc(payload_execution_source_time)
    payload_decision_dt = timewarp_loop.parse_utc(
        payload.get("decision_time_utc")
    )
    if (
        payload_execution_fill is None
        or payload_execution_fill != execution_fill
        or payload_execution_source != execution_source
        or payload_source_dt is None
        or payload_decision_dt is None
        or payload_source_dt >= payload_decision_dt
        or not _bridge_predecision_fillability_boundary_allowed(
            payload_execution_source_boundary
        )
        or payload_execution_authority_class
        != PACKAGE_NEW_ENTRY_AUTHORITY_EXECUTION_FILLABILITY_CLASS
        or not execution_fillability_source_is_authoritative(
            payload_execution_source,
            payload_execution_authority_class,
        )
    ):
        return False

    entry_fill = _safe_float_or_none(
        _first_present(
            payload.get("entry_quality_fill_probability"),
            payload.get("fill_probability"),
        )
    )
    quality_sources = payload.get("candidate_decision_quality_field_sources")
    quality_sources = quality_sources if isinstance(quality_sources, Mapping) else {}
    entry_source = str(quality_sources.get("fill_probability") or "").strip()
    projected_sources = row.get("candidate_decision_quality_field_sources")
    projected_sources = (
        dict(projected_sources) if isinstance(projected_sources, Mapping) else {}
    )
    if entry_fill is not None:
        row["fill_probability"] = entry_fill
        row["candidate_fill_probability"] = entry_fill
        row["entry_quality_fill_probability"] = entry_fill
        if entry_source:
            projected_sources["fill_probability"] = entry_source
    row["execution_fill_probability"] = execution_fill
    row["execution_fill_probability_source"] = execution_source
    row["execution_fill_probability_source_time_utc"] = (
        payload_execution_source_time
    )
    row["execution_fill_probability_source_boundary"] = (
        payload_execution_source_boundary
    )
    row["execution_fill_probability_authority_class"] = (
        payload_execution_authority_class
    )
    signed_hash = str(
        row.get("package_new_entry_authority_hash_sha256")
        or row.get("expected_package_new_entry_authority_hash_sha256")
        or ""
    ).strip()
    row["execution_fill_probability_authority_hash_sha256"] = signed_hash or None
    row["limit_fillability_probability"] = execution_fill
    row["predecision_limit_fillability_probability"] = execution_fill
    fillability = row.get("predecision_limit_fillability")
    fillability = dict(fillability) if isinstance(fillability, Mapping) else {}
    fillability["fill_probability"] = execution_fill
    fillability["current_price_source_time_utc"] = payload_execution_source_time
    fillability["source_time_utc"] = payload_execution_source_time
    fillability["current_price_source_boundary"] = (
        payload_execution_source_boundary
    )
    fillability["source_boundary"] = payload_execution_source_boundary
    row["predecision_limit_fillability"] = fillability
    projected_sources["execution_fill_probability"] = execution_source
    projected_sources["limit_fillability_probability"] = execution_source
    row["candidate_decision_quality_field_sources"] = projected_sources

    nested = row.get("predecision_limit_fillability")
    nested = dict(nested) if isinstance(nested, Mapping) else {}
    nested.update(
        {
            "available": True,
            "fill_probability": execution_fill,
            "limit_fillability_probability": execution_fill,
            "fill_probability_source": execution_source,
            "source": execution_source,
            "source_time_utc": payload_execution_source_time,
            "current_price_source_time_utc": payload_execution_source_time,
            "source_boundary": payload_execution_source_boundary,
            "current_price_source_boundary": payload_execution_source_boundary,
            "authority_class": (
                payload_execution_authority_class
            ),
            "authority_hash_sha256": signed_hash or None,
            "uses_outcome_fields": False,
        }
    )
    row["predecision_limit_fillability"] = nested
    row["execution_fillability_projection_status"] = (
        "projected_from_valid_final_signed_authority"
    )
    return True


def _project_bridge_execution_fillability_tuple(
    target: dict[str, Any],
    detail: Mapping[str, Any],
) -> bool:
    value = _safe_float_or_none(detail.get("value"))
    source = str(detail.get("source") or "").strip()
    source_time = str(detail.get("source_time_utc") or "").strip()
    source_boundary = str(detail.get("source_boundary") or "").strip()
    authority_class = str(
        detail.get("authority_class")
        or "predecision_passive_limit_fillability_authority"
    ).strip()
    if (
        value is None
        or not source
        or not source_time
        or not source_boundary
        or not authority_class
    ):
        return False
    value = max(0.0, min(1.0, value))
    target.update(
        {
            "predecision_limit_fillability_probability": value,
            "limit_fillability_probability": value,
            "execution_fill_probability": value,
            "execution_fill_probability_source": source,
            "execution_fill_probability_source_time_utc": source_time,
            "execution_fill_probability_source_boundary": source_boundary,
            "execution_fill_probability_authority_class": authority_class,
            "package_new_entry_authority_predecision_limit_fillability_probability": value,
            "package_new_entry_authority_limit_fillability_probability": value,
            "package_new_entry_authority_execution_fill_probability": value,
            "package_new_entry_authority_execution_fill_probability_source": source,
            "package_new_entry_authority_execution_fill_probability_source_time_utc": source_time,
            "package_new_entry_authority_execution_fill_probability_source_boundary": source_boundary,
        }
    )
    nested = target.get("predecision_limit_fillability")
    nested = dict(nested) if isinstance(nested, Mapping) else {}
    nested.update(
        {
            "available": True,
            "fill_probability": value,
            "limit_fillability_probability": value,
            "fill_probability_source": source,
            "source": source,
            "source_time_utc": source_time,
            "current_price_source_time_utc": source_time,
            "source_boundary": source_boundary,
            "current_price_source_boundary": source_boundary,
            "authority_class": authority_class,
            "uses_outcome_fields": False,
        }
    )
    target["predecision_limit_fillability"] = nested
    return True


def bridge_row_with_execution_fillability_for_stamp(row: Mapping[str, Any]) -> dict[str, Any]:
    """Materialize bridge-resolved execution fillability for scheduler authority stamps."""

    out = dict(row)
    fill_detail = bridge_predecision_execution_fillability_detail_for_stamp(out)
    fill_probability = _safe_float_or_none(fill_detail.get("value"))
    fill_source = str(fill_detail.get("source") or "")
    if fill_probability is not None and _project_bridge_execution_fillability_tuple(
        out,
        fill_detail,
    ):
        entry_fill_probability = _safe_float_or_none(
            _first_present(
                out.get("entry_quality_fill_probability"),
                out.get("fill_probability"),
                out.get("candidate_fill_probability"),
            )
        )
        if entry_fill_probability is None:
            entry_fill_probability = fill_probability
        field_sources = out.get("candidate_decision_quality_field_sources")
        field_sources = dict(field_sources) if isinstance(field_sources, Mapping) else {}
        field_sources.setdefault("execution_fill_probability", fill_source)
        field_sources.setdefault("limit_fillability_probability", fill_source)
        field_sources.setdefault("predecision_limit_fillability_probability", fill_source)
        if not str(field_sources.get("fill_probability") or "").strip():
            field_sources["fill_probability"] = fill_source
        out["candidate_decision_quality_field_sources"] = field_sources
        for entry_field in (
            "fill_probability",
            "candidate_fill_probability",
            "entry_quality_fill_probability",
        ):
            if _missing_value(out.get(entry_field)):
                out[entry_field] = entry_fill_probability
        out["package_new_entry_authority_fill_probability"] = entry_fill_probability
        out["package_new_entry_authority_entry_quality_fill_probability"] = (
            entry_fill_probability
        )
    return out


def bridge_authority_with_execution_fillability_for_stamp(
    authority: Mapping[str, Any],
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind bridge-resolved execution fillability to the signed authority surface."""

    out = dict(authority)
    fill_detail = bridge_predecision_execution_fillability_detail_for_stamp(row)
    fill_probability = _safe_float_or_none(fill_detail.get("value"))
    fill_source = str(fill_detail.get("source") or "")
    if fill_probability is not None and _project_bridge_execution_fillability_tuple(
        out,
        fill_detail,
    ):
        entry_fill_probability = _safe_float_or_none(
            _first_present(
                out.get("entry_quality_fill_probability"),
                out.get("fill_probability"),
                row.get("entry_quality_fill_probability"),
                row.get("fill_probability"),
                row.get("candidate_fill_probability"),
            )
        )
        if entry_fill_probability is None:
            entry_fill_probability = fill_probability
        for entry_field in ("fill_probability", "entry_quality_fill_probability"):
            if _missing_value(out.get(entry_field)):
                out[entry_field] = entry_fill_probability
        out["package_new_entry_authority_fill_probability"] = entry_fill_probability
        out["package_new_entry_authority_entry_quality_fill_probability"] = (
            entry_fill_probability
        )
    return out


def _bridge_refresh_existing_signed_reduced_authority(
    row: dict[str, Any],
    *,
    selector_action: str,
    selector_reason: str,
    action_intent: str,
) -> None:
    """Rebind an existing signed reduced/open-reduced authority after bridge enrichment."""

    normalized_action_intent = normalize_bridge_action_intent(action_intent) or "new_position"
    if normalized_action_intent not in SIGNED_REDUCED_PACKAGE_NEW_ENTRY_ACTIONS:
        return
    for field, authority in _bridge_reduced_authority_candidates(
        row,
        selector_action=selector_action,
        selector_reason=selector_reason,
    ):
        original_surface = {**row, **authority}
        original_payload = original_surface.get(
            "package_new_entry_authority_payload"
        )
        if not isinstance(original_payload, Mapping):
            continue
        original_action = normalize_bridge_action_intent(
            original_payload.get("target_action_intent")
        )
        original_selector_action = normalize_selector_action_for_reason(
            original_payload.get("selector_action"),
            original_payload.get("selector_reason"),
            original_action or normalized_action_intent,
        )
        if timewarp_loop.package_new_entry_authority_immutable_payload_failures(
            original_surface,
            normalized_selector_action=original_selector_action,
            normalized_action=original_action,
        ):
            continue
        original_hash = str(
            original_surface.get("package_new_entry_authority_hash_sha256") or ""
        ).strip()
        try:
            stamp_row = bridge_row_with_execution_fillability_for_stamp(row)
            stamp_authority = bridge_authority_with_execution_fillability_for_stamp(
                authority,
                stamp_row,
            )
            stamped = stamp_package_new_entry_authority(
                stamp_row,
                selector_action=selector_action,
                selector_reason=selector_reason,
                action_intent=normalized_action_intent,
                authority=stamp_authority,
            )
        except Exception:
            continue
        if not stamped:
            continue
        authority_field = (
            stamped.get("package_new_entry_authority_authority_field")
            or field
        )
        nested_authority = _bridge_finalized_signed_authority(
            stamp_authority,
            stamped,
        )
        row[str(authority_field)] = nested_authority
        for signed_field in PACKAGE_AUTHORITY_FIELDS:
            if signed_field in {
                "package_new_entry_authority_required",
                "package_new_entry_authority_valid",
                "package_new_entry_authority_status",
            }:
                continue
            value = stamped.get(signed_field)
            if signed_field in PACKAGE_AUTHORITY_EMPTY_LIST_FIELDS:
                missing = value in (None, "", {})
            else:
                missing = _missing_value(value)
            if not missing:
                row[signed_field] = value
        _project_final_signed_fillability(row)
        row["package_new_entry_authority_bridge_restamped"] = True
        row["package_new_entry_authority_bridge_restamped_from_field"] = field
        row["package_new_entry_authority_bridge_restamp_reason"] = (
            "existing_signed_authority_rebound_after_predecision_bridge_enrichment"
        )
        row["package_new_entry_authority_predecessor_payload_contract"] = (
            original_surface.get("package_new_entry_authority_payload_contract")
            or original_payload.get("payload_contract")
        )
        row["package_new_entry_authority_predecessor_payload"] = dict(
            original_payload
        )
        row["package_new_entry_authority_predecessor_hash_sha256"] = original_hash
        row["package_new_entry_authority_predecessor_action_intent"] = original_action
        row["package_new_entry_authority_predecessor_selector_action"] = (
            original_selector_action
        )
        row["package_new_entry_authority_predecessor_selector_reason"] = (
            original_payload.get("selector_reason")
        )
        return


def bridge_reduced_package_new_entry_authority_validation(
    row: Mapping[str, Any],
    *,
    selector_action: str,
    selector_reason: str,
    action_intent: str,
) -> dict[str, Any]:
    """Validate signed reduced-risk authority with explicit bridge provenance fallback."""

    validation_row = dict(row)
    quality_sources = validation_row.get("candidate_decision_quality_field_sources")
    quality_sources = dict(quality_sources) if isinstance(quality_sources, Mapping) else {}
    bridge_materialized_fields: list[str] = []
    authority_fill_probability, authority_fill_source = execution_fillability_authority(
        validation_row
    )
    if authority_fill_probability is not None:
        validation_row["predecision_limit_fillability_probability"] = (
            authority_fill_probability
        )
        validation_row["limit_fillability_probability"] = authority_fill_probability
    for field, aliases in (
        ("expected_net_r", ("expected_net_r", "candidate_expected_net_r")),
        ("probability", ("probability", "candidate_probability")),
    ):
        if str(quality_sources.get(field) or "").strip():
            continue
        if _first_numeric(validation_row, *aliases) is not None:
            quality_sources[field] = f"selected_package_bridge.{field}"
            bridge_materialized_fields.append(field)
    if not str(quality_sources.get("fill_probability") or "").strip():
        if authority_fill_probability is not None:
            quality_sources["fill_probability"] = authority_fill_source
            bridge_materialized_fields.append("fill_probability")
        else:
            if _first_numeric(
                validation_row,
                "fill_probability",
                "candidate_fill_probability",
                "entry_quality_fill_probability",
            ) is not None:
                bridge_materialized_fields.append("fill_probability")
            provenance_failures = validation_row.get(
                "candidate_decision_quality_provenance_failures"
            )
            provenance_failure_list = (
                list(provenance_failures)
                if isinstance(provenance_failures, Sequence)
                and not isinstance(provenance_failures, (str, bytes, bytearray))
                else []
            )
            provenance_failure_list.append(EXECUTION_FILLABILITY_MISSING_SOURCE)
            validation_row["candidate_decision_quality_provenance_failures"] = (
                provenance_failure_list
            )
    if not str(quality_sources.get("source_completeness") or "").strip():
        if _first_numeric(
            validation_row,
            "source_completeness",
            "candidate_source_completeness",
        ) is not None:
            quality_sources["source_completeness"] = (
                "selected_package_bridge.source_completeness"
            )
            bridge_materialized_fields.append("source_completeness")
    if quality_sources:
        validation_row["candidate_decision_quality_field_sources"] = quality_sources
    bridge_materialized_boundary = False
    if _missing_value(validation_row.get("candidate_decision_quality_source_boundary")):
        validation_row["candidate_decision_quality_source_boundary"] = (
            "predecision_selected_package_bridge_quality_no_outcome_fields"
        )
        bridge_materialized_boundary = True
    quality_boundary = str(
        validation_row.get("candidate_decision_quality_source_boundary") or ""
    ).lower()
    quality_boundary = quality_boundary.replace("-", "_").replace(" ", "_")
    alias_mismatches = validation_row.get("candidate_decision_quality_alias_mismatches")
    provenance_failures = validation_row.get("candidate_decision_quality_provenance_failures")
    all_quality_sources_present = all(
        str(quality_sources.get(field) or "").strip()
        for field in (
            "expected_net_r",
            "probability",
            "fill_probability",
            "source_completeness",
        )
    )
    exact_quality_materialized = bool(
        all_quality_sources_present
        and "predecision" in quality_boundary
        and "no_outcome" in quality_boundary
        and alias_mismatches in (None, "", [], (), {})
        and provenance_failures in (None, "", [], (), {})
    )
    if exact_quality_materialized:
        validation_row["candidate_decision_quality_alias_status"] = "exact_materialized"
        validation_row.setdefault("candidate_decision_quality_alias_mismatches", [])
        validation_row.setdefault("candidate_decision_quality_provenance_failures", [])
    elif _missing_value(validation_row.get("candidate_decision_quality_alias_status")):
        validation_row["candidate_decision_quality_alias_status"] = "materialized"
    validation_row["candidate_decision_quality"] = candidate_decision_quality_envelope(
        validation_row
    )
    validation = reduced_package_new_entry_authority_validation(
        validation_row,
        selector_action=selector_action,
        selector_reason=selector_reason,
        action_intent=action_intent,
    )
    validation = dict(validation)
    if not _missing_value(validation_row.get("candidate_decision_quality")):
        validation["candidate_decision_quality"] = validation_row.get(
            "candidate_decision_quality"
        )
    if bridge_materialized_fields or bridge_materialized_boundary:
        validation["bridge_materialized_candidate_decision_quality_fields"] = tuple(
            bridge_materialized_fields
        )
        validation["bridge_materialized_candidate_decision_quality_source_boundary"] = (
            "predecision_selected_package_bridge_quality_no_outcome_fields"
            if bridge_materialized_boundary
            else ""
        )
    return validation


SOURCE_REQUIRED_REPLAY_OVERRIDE_ACTION_BY_REASON = {
    "source_required_fail_closed_package_source_reconciled_for_replay": (
        "same_direction_scale_in"
    ),
    "source_required_fail_closed_package_new_position_source_gap_reconciled_for_replay": (
        "new_position"
    ),
    "package_same_direction_scale_in_lifecycle_reconciled_for_replay": (
        "same_direction_scale_in"
    ),
    "source_required_fail_closed_package_close_reverse_reconciled_for_replay": (
        "close_and_reverse"
    ),
    "source_required_fail_closed_package_replace_pending_reconciled_for_replay": (
        "replace_pending"
    ),
    "replay_lifecycle_action_resolver_same_direction_scale_in": (
        "same_direction_scale_in"
    ),
    "replay_lifecycle_action_resolver_same_side_pending_replace_pending": (
        "replace_pending"
    ),
    "replay_lifecycle_action_resolver_close_and_reverse": "close_and_reverse",
    "replay_lifecycle_action_resolver_replace_pending": "replace_pending",
}


def _source_required_override_expected_kind(reason: str) -> str | None:
    if reason.startswith("replay_lifecycle_action_resolver_"):
        return "replay_lifecycle_action_resolver"
    if reason.startswith("source_required_fail_closed_"):
        return "fail_closed"
    if reason.startswith("source_required_selector_hold_"):
        return "selector_hold"
    return None


def source_required_bridge_override_block_reason(row: Mapping[str, Any]) -> str | None:
    applied = source_required_replay_override_applied(row)
    if not applied:
        return None
    failures = row.get("scheduler_materialization_source_required_fail_closed_override_failures")
    if failures not in (None, "", [], (), {}):
        return "source_required_override_failures_present"
    override_reason = source_required_replay_override_reason(row)
    if not override_reason or override_reason not in SOURCE_REQUIRED_REPLAY_OVERRIDE_REASONS:
        return "source_required_override_reason_missing_or_invalid"
    expected_action = SOURCE_REQUIRED_REPLAY_OVERRIDE_ACTION_BY_REASON.get(
        override_reason
    )
    if not expected_action:
        return "source_required_override_reason_has_no_executable_action"
    action_intent = normalize_bridge_action_intent(
        row.get("scheduler_materialization_action_intent")
        or row.get("action_intent")
        or row.get("lifecycle_action")
    )
    if action_intent != expected_action:
        return (
            "source_required_override_reason_action_mismatch:"
            f"{override_reason}:{action_intent or 'missing'}:{expected_action}"
        )
    expected_kind = _source_required_override_expected_kind(override_reason)
    actual_kind = source_required_replay_override_kind(row)
    if expected_kind and actual_kind != expected_kind:
        return (
            "source_required_override_reason_kind_mismatch:"
            f"{override_reason}:{actual_kind or 'missing'}:{expected_kind}"
        )
    for field, floor in (
        ("source_completeness", PACKAGE_BRIDGE_MIN_EXECUTABLE_SOURCE_COMPLETENESS),
        ("expected_net_r", 0.0),
        ("probability", 0.0),
    ):
        value = _first_numeric(row, field, f"candidate_{field}")
        if value is None:
            return f"source_required_quality_field_missing:{field}"
        if value < floor:
            return f"source_required_quality_field_below_floor:{field}"
    fill_probability, _fill_source = execution_fillability_authority(row)
    if fill_probability is None:
        return "source_required_quality_field_missing:execution_fillability"
    if fill_probability < 0.0:
        return "source_required_quality_field_below_floor:execution_fillability"
    source_status = str(row.get("source_completeness_status") or "").strip().lower()
    if any(
        token in source_status
        for token in SOURCE_COMPLETENESS_BLOCKED_STATUS_TOKENS
    ):
        return f"source_required_source_completeness_status_not_executable:{source_status}"
    return None


def _bridge_authority_mapping(
    row: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any]:
    surfaces: list[Mapping[str, Any]] = [row]
    for components_key in ("score_components", "scheduler_score_components"):
        components = row.get(components_key)
        if not isinstance(components, Mapping):
            continue
        surfaces.append(components)
        for nested_key in (
            "candidate_decision_inputs",
            "scheduler_candidate_decision_inputs",
            "decision_inputs",
        ):
            nested = components.get(nested_key)
            if isinstance(nested, Mapping):
                surfaces.append(nested)
    for nested_key in (
        "candidate_decision_inputs",
        "scheduler_candidate_decision_inputs",
        "decision_inputs",
    ):
        nested = row.get(nested_key)
        if isinstance(nested, Mapping):
            surfaces.append(nested)
    for surface in surfaces:
        value = surface.get(key)
        if isinstance(value, Mapping):
            return value
    return {}


def _bridge_canonical_ids(value: Any) -> list[str]:
    if isinstance(value, str):
        values: Iterable[Any] = value.split(",")
    elif isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        values = value
    else:
        values = ()
    return sorted({str(item).strip() for item in values if str(item or "").strip()})


def lifecycle_release_binding_block_reason(
    row: Mapping[str, Any],
    action_intent: str,
) -> str | None:
    """Require exact predecision release identity for lifecycle-mutating actions."""

    normalized_action = normalize_bridge_action_intent(action_intent)
    candidate_id = str(row.get("candidate_id") or "").strip()
    decision_time = str(row.get("decision_time_utc") or "").strip()
    instance_key = str(
        row.get("canonical_replay_candidate_instance_key") or ""
    ).strip()
    source_bound_instance_key = str(
        row.get("source_bound_replay_candidate_instance_key") or ""
    ).strip()
    identity_status = str(
        row.get("candidate_instance_identity_status") or ""
    ).strip()
    if normalized_action == "close_and_reverse":
        authority = _bridge_authority_mapping(
            row,
            "package_opposite_side_close_reverse_authority",
        )
        binding = authority.get("release_binding_payload")
        binding = binding if isinstance(binding, Mapping) else {}
        binding_hash = str(
            authority.get("release_binding_hash_sha256") or ""
        ).strip()
        release_ids = _bridge_canonical_ids(
            binding.get("opposite_open_position_ids")
        )
        authority_release_ids = _bridge_canonical_ids(
            authority.get("opposite_open_position_ids")
        )
        if (
            binding.get("schema_version")
            != "package_close_reverse_release_binding_v1"
            or not binding_hash
            or binding_hash != stable_sha256(binding)
            or str(binding.get("candidate_id") or "").strip() != candidate_id
            or str(binding.get("decision_time_utc") or "").strip()
            != decision_time
            or str(
                binding.get("canonical_replay_candidate_instance_key") or ""
            ).strip()
            != instance_key
            or str(
                binding.get("source_bound_replay_candidate_instance_key") or ""
            ).strip()
            != source_bound_instance_key
            or str(binding.get("candidate_instance_identity_status") or "").strip()
            != identity_status
            or normalize_bridge_action_intent(
                binding.get("effective_action_intent")
            )
            != "close_and_reverse"
            or not release_ids
            or release_ids != authority_release_ids
        ):
            return "close_reverse_release_binding_invalid"
        return None
    if normalized_action == "replace_pending":
        replacement = _bridge_authority_mapping(
            row,
            "replacement_reallocation_quality",
        )
        binding = replacement.get("replacement_release_binding_payload")
        binding = binding if isinstance(binding, Mapping) else {}
        binding_hash = str(
            replacement.get("replacement_release_binding_hash_sha256") or ""
        ).strip()
        selected_release_id = str(
            binding.get("selected_release_pending_id") or ""
        ).strip()
        pending_ids = set()
        for key in (
            "same_side_pending_ids",
            "same_side_pending_order_ids",
            "opposite_pending_ids",
            "opposite_pending_order_ids",
        ):
            pending_ids.update(_bridge_canonical_ids(binding.get(key)))
        if (
            binding.get("schema_version")
            != "package_pending_replacement_release_binding_v1"
            or not binding_hash
            or binding_hash != stable_sha256(binding)
            or str(binding.get("candidate_id") or "").strip() != candidate_id
            or str(binding.get("decision_time_utc") or "").strip()
            != decision_time
            or str(
                binding.get("canonical_replay_candidate_instance_key") or ""
            ).strip()
            != instance_key
            or str(
                binding.get("source_bound_replay_candidate_instance_key") or ""
            ).strip()
            != source_bound_instance_key
            or str(binding.get("candidate_instance_identity_status") or "").strip()
            != identity_status
            or normalize_bridge_action_intent(
                binding.get("effective_action_intent")
            )
            != "replace_pending"
            or not selected_release_id
            or selected_release_id not in pending_ids
            or str(replacement.get("selected_release_pending_id") or "").strip()
            != selected_release_id
        ):
            return "replace_pending_release_binding_invalid"
    return None


def selector_not_risk_bearing_bridge_reason(row: Mapping[str, Any]) -> str:
    selector_action = str(row.get("selector_action") or "").strip()
    selector_reason = str(row.get("selector_reason") or "").strip()
    if selector_action == "source-required":
        return "selector_not_risk_bearing_source_required_hold"
    if selector_reason == "admission_quality_off_configured_session_entry_blocked":
        return "selector_not_risk_bearing_off_configured_session_block"
    if selector_reason in {
        "no_shadow_sleeve_match",
        "ultimate_candidate_package_no_shadow_sleeve_match",
    }:
        return "selector_not_risk_bearing_no_shadow_sleeve_match"
    if selector_reason in {
        "non_admission_sleeve_only",
        "ultimate_candidate_package_non_admission_sleeve_only",
    }:
        return "selector_not_risk_bearing_non_admission_sleeve_only"
    if "router_refused" in selector_reason or "router_refusal" in selector_reason:
        return "selector_not_risk_bearing_router_refusal"
    if "fill_probability" in selector_reason:
        return "selector_not_risk_bearing_fill_probability_block"
    return "selector_not_risk_bearing"


def executable_package_use_detail(
    row: Mapping[str, Any],
    *,
    source_bound_allowed: bool,
) -> tuple[bool, str]:
    """Keep source-bound membership separate from executable replay authority."""

    if not source_bound_allowed:
        return False, "no_package_axis_or_candidate_use_alias"
    terminal_status_reason = terminal_non_executable_execution_status_reason(row)
    if terminal_status_reason:
        return False, terminal_status_reason
    effective_admission_count = row.get("ultimate_package_effective_admission_count")
    if (
        effective_admission_count not in (None, "")
        and (_safe_float_or_none(effective_admission_count) or 0.0) <= 0.0
    ):
        return False, "ultimate_package_effective_admission_count_zero"
    cost_status = str(row.get("pretrade_cost_packet_status") or "").strip().upper()
    if not cost_status:
        return False, "broker_cost_packet_status_missing"
    if cost_status == "REFUSED":
        refusal_reasons = row.get("pretrade_cost_refusal_reasons")
        if isinstance(refusal_reasons, str):
            refusal_reason = refusal_reasons.strip()
        elif isinstance(refusal_reasons, Sequence) and not isinstance(
            refusal_reasons,
            (bytes, bytearray, str),
        ):
            refusal_reason = "|".join(
                str(item).strip() for item in refusal_reasons if str(item).strip()
            )
        else:
            refusal_reason = ""
        return (
            False,
            f"broker_cost_packet_refused:{refusal_reason}"
            if refusal_reason
            else "broker_cost_packet_refused",
        )
    if cost_status not in {"PASSED", "PASS", "OK"}:
        return False, f"broker_cost_packet_not_passed:{cost_status}"
    effective_allowed = row.get("ultimate_package_effective_source_bound_candidate_use_allowed")
    if effective_allowed is False:
        return False, "ultimate_package_effective_source_bound_not_allowed"
    selector_action = str(row.get("selector_action") or "").strip()
    selector_reason = str(row.get("selector_reason") or "").strip()
    action_intent = str(
        row.get("scheduler_materialization_action_intent")
        or row.get("action_intent")
        or row.get("lifecycle_action")
        or ""
    ).strip()
    normalized_action_intent = normalize_bridge_action_intent(action_intent) or "new_position"
    normalized_selector_action = normalize_selector_action_for_reason(
        selector_action,
        selector_reason,
        normalized_action_intent,
    )
    replay_override_applied = source_required_replay_override_applied(row)
    replay_override_block_reason = source_required_bridge_override_block_reason(row)
    replay_override_valid = replay_override_applied and replay_override_block_reason is None
    if replay_override_block_reason:
        return False, f"source_required_replay_override_invalid:{replay_override_block_reason}"
    if (
        replay_override_valid
        and normalized_action_intent
        not in SIGNED_REDUCED_PACKAGE_NEW_ENTRY_ACTIONS
    ):
        return False, (
            "source_required_replay_override_invalid:"
            "source_required_override_action_not_signed_new_entry_action:"
            f"{normalized_action_intent or 'missing'}"
        )
    if (
        normalized_selector_action
        and normalized_selector_action not in RISK_BEARING_SELECTOR_ACTIONS
        and not replay_override_valid
        and cost_status != "REFUSED"
    ):
        return False, selector_not_risk_bearing_bridge_reason(row)
    cost_authority = str(
        row.get("cost_authority") or row.get("pretrade_cost_packet_authority") or ""
    ).strip()
    if not cost_authority:
        return False, "broker_cost_authority_missing"
    if cost_authority != "broker_calibrated_replay_cost":
        return False, f"broker_cost_authority_unexpected:{cost_authority}"
    cost_source_gap_status = str(row.get("cost_source_gap_status") or "").strip()
    if not cost_source_gap_status:
        return False, "broker_cost_source_gap_status_missing"
    if cost_source_gap_status != "source_bound_cost_authority_present":
        return False, f"broker_cost_source_gap_not_executable:{cost_source_gap_status}"
    if bool(row.get("source_gap_cost_fallback_blocked")):
        return False, "source_gap_cost_fallback_blocked"
    if bool(row.get("candidate_cost_r_fallback_is_authority")):
        return False, "candidate_cost_r_fallback_not_order_authority"
    source_completeness = _safe_float_or_none(row.get("source_completeness"))
    source_status = str(row.get("source_completeness_status") or "").strip().lower()
    if source_completeness is None:
        return False, "source_completeness_missing"
    source_completeness_floor = _bridge_source_completeness_floor(
        normalized_selector_action
    )
    if _router_refusal_open_reduced_authority_applies(row):
        source_completeness_floor = max(
            source_completeness_floor,
            PACKAGE_BRIDGE_ROUTER_REFUSAL_MIN_SOURCE_COMPLETENESS,
        )
    if source_completeness < source_completeness_floor:
        return False, f"source_completeness_below_floor:{source_completeness:.3f}"
    if any(
        token in source_status
        for token in SOURCE_COMPLETENESS_BLOCKED_STATUS_TOKENS
    ):
        return False, f"source_completeness_status_not_executable:{source_status}"
    quality_floors = _candidate_quality_floor_requirements(
        row,
        action_intent=normalized_action_intent,
    )
    expected_net_r = _first_numeric(row, "expected_net_r", "candidate_expected_net_r")
    probability = _first_numeric(row, "probability", "candidate_probability")
    fill_probability, fill_probability_source = execution_fillability_authority(row)
    if expected_net_r is None:
        return False, "expected_net_r_missing"
    if expected_net_r < quality_floors["expected_net_r"]:
        return False, f"expected_net_r_below_floor:{expected_net_r:.3f}"
    if probability is None:
        return False, "probability_missing"
    if probability < quality_floors["probability"]:
        return False, f"probability_below_floor:{probability:.3f}"
    signed_authority_block_reason = signed_reduced_package_bridge_authority_block_reason(
        row,
        selector_action=normalized_selector_action,
        selector_reason=selector_reason,
        action_intent=normalized_action_intent,
    )
    if signed_authority_block_reason:
        return False, signed_authority_block_reason
    lifecycle_release_block_reason = lifecycle_release_binding_block_reason(
        row,
        normalized_action_intent,
    )
    if lifecycle_release_block_reason:
        return False, lifecycle_release_block_reason
    if fill_probability is None:
        return False, EXECUTION_FILLABILITY_MISSING_SOURCE
    if fill_probability < quality_floors["fill_probability"]:
        return False, (
            f"execution_fillability_below_floor:{fill_probability:.3f}:"
            f"{fill_probability_source}"
        )
    selected_policy_failure = selected_policy_expected_net_calibration_failure_reason(
        row
    )
    if selected_policy_failure:
        return False, (
            "selected_policy_expected_net_calibration_invalid:"
            f"{selected_policy_failure}"
        )
    scheduler_skip_reason = str(row.get("scheduler_materialization_skip_reason") or "").strip()
    if scheduler_skip_reason and not scheduler_materialization_skip_is_soft_transfer(
        row,
        scheduler_skip_reason,
    ):
        return False, f"scheduler_materialization_skipped:{scheduler_skip_reason}"
    if action_intent.startswith("invalid_action_intent:") and not replay_override_valid:
        return False, f"scheduler_materialization_invalid_action:{action_intent}"
    if normalized_selector_action == "open-reduced-risk":
        if (
            normalized_action_intent
            not in SELECTOR_OPEN_REDUCED_RISK_ALLOWED_ACTION_INTENTS
            and not replay_override_valid
        ):
            return False, (
                "selector_open_reduced_risk_action_intent_not_order_authority:"
                f"{normalized_action_intent or 'missing'}"
            )
        if not open_reduced_bridge_authority_allowed(row) and not replay_override_valid:
            return False, "selector_open_reduced_risk_authority_missing"
    if (
        normalized_selector_action
        and normalized_selector_action not in RISK_BEARING_SELECTOR_ACTIONS
        and not replay_override_valid
    ):
        return False, selector_not_risk_bearing_bridge_reason(row)
    return True, "broker_cost_selector_and_scheduler_action_executable"


def package_authority_bridge_fields(
    row: Mapping[str, Any],
    *,
    source_bound_allowed: bool | None = None,
) -> dict[str, Any]:
    """Expose bridge package authority as a first-class executable contract."""

    entry_price = _first_numeric(row, "entry_price")
    stop_loss = _first_numeric(row, "stop_loss", "stop_or_invalidation")
    target_price = _first_numeric(
        row,
        "take_profit_1",
        "take_profit",
        "target_price",
        "target_reference",
    )
    has_order_geometry = bool(
        entry_price is not None and stop_loss is not None and target_price is not None
    )
    if source_bound_allowed is None:
        source_bound_allowed = any(
            _truthy(row.get(field)) for field in PACKAGE_USE_ALIAS_FIELDS
        )
    if not has_order_geometry:
        executable_allowed = False
        executable_reason = "package_authority_candidate_missing_entry_stop_target_geometry"
    else:
        executable_allowed, executable_reason = executable_package_use_detail(
            row,
            source_bound_allowed=bool(source_bound_allowed),
        )
    selector_action = str(row.get("selector_action") or "").strip()
    selector_reason = str(row.get("selector_reason") or "").strip()
    action_intent = normalize_bridge_action_intent(
        row.get("scheduler_materialization_action_intent")
        or row.get("action_intent")
        or row.get("lifecycle_action")
        or "new_position"
    ) or "new_position"
    if (
        selector_action in {"reduce-risk", "open-reduced-risk"}
        and action_intent in SIGNED_REDUCED_PACKAGE_NEW_ENTRY_ACTIONS
    ):
        signed_validation = bridge_reduced_package_new_entry_authority_validation(
            row,
            selector_action=selector_action,
            selector_reason=selector_reason,
            action_intent=action_intent,
        )
    else:
        signed_validation = {}
    signed_failures = [
        str(item)
        for item in signed_validation.get("failures") or ()
        if str(item or "").strip()
    ]
    order_executable_authority_source = (
        "selected_package_bridge_package_authority_bridge_fields"
    )
    if "authority_hash_missing" in signed_failures:
        signed_failures = ["authority_hash_missing"]
    if (
        signed_validation.get("required") is True
        and signed_validation.get("valid") is not True
    ):
        executable_allowed = False
        executable_reason = (
            "signed_package_new_entry_authority_invalid:"
            + (signed_failures[0] if signed_failures else "unknown_failure")
        )
    elif signed_validation.get("required") is True and executable_allowed:
        signed_payload = signed_validation.get("package_new_entry_authority_payload")
        signed_payload = (
            signed_payload if isinstance(signed_payload, Mapping) else {}
        )
        signed_order_allowed = signed_payload.get(
            "package_replay_order_executable_candidate_use_allowed"
        )
        signed_order_reason = str(
            signed_payload.get(
                "package_replay_order_executable_candidate_use_allowed_reason"
            )
            or ""
        ).strip()
        signed_order_source = str(
            signed_payload.get("package_replay_order_executable_authority_source")
            or ""
        ).strip()
        executable_allowed = signed_order_allowed is True
        executable_reason = (
            signed_order_reason
            if executable_allowed and signed_order_reason
            else "signed_package_new_entry_order_executable_triplet_invalid"
        )
        order_executable_authority_source = (
            signed_order_source or order_executable_authority_source
        )
    return {
        "package_authority_has_order_geometry": has_order_geometry,
        "package_authority_order_geometry_status": (
            "order_geometry_present"
            if has_order_geometry
            else "package_authority_candidate_missing_entry_stop_target_geometry"
        ),
        "package_authority_executable_candidate_status": (
            "package_authority_candidate_executable"
            if executable_allowed
            else f"package_authority_candidate_not_executable:{executable_reason}"
        ),
        "package_replay_order_executable_candidate_use_allowed": executable_allowed,
        "package_replay_order_executable_candidate_use_allowed_reason": (
            executable_reason
        ),
        "package_replay_order_executable_authority_source": (
            order_executable_authority_source
        ),
        "package_new_entry_authority_required": signed_validation.get("required"),
        "package_new_entry_authority_valid": signed_validation.get("valid"),
        "package_new_entry_authority_status": signed_validation.get("status"),
        "package_new_entry_authority_failures": signed_failures,
        "package_new_entry_authority_hash_sha256": signed_validation.get(
            "package_new_entry_authority_hash_sha256"
        ),
        "expected_package_new_entry_authority_hash_sha256": signed_validation.get(
            "expected_package_new_entry_authority_hash_sha256"
        ),
        "package_new_entry_authority_payload_schema": signed_validation.get(
            "payload_schema"
        ),
        "package_new_entry_authority_payload_contract": signed_validation.get(
            "payload_contract"
        ),
        "package_new_entry_authority_payload": signed_validation.get(
            "package_new_entry_authority_payload"
        ),
        "package_new_entry_authority_scope": signed_validation.get("scope"),
        "package_new_entry_authority_target_action_intent": signed_validation.get(
            "target_action_intent"
        ),
        "package_new_entry_authority_authority_field": signed_validation.get(
            "authority_field"
        ),
        "package_new_entry_authority_authority_family": signed_validation.get(
            "authority_family"
        ),
        "package_new_entry_authority_source_boundary": signed_validation.get(
            "source_boundary"
        ),
        "package_new_entry_authority_uses_outcome_fields": signed_validation.get(
            "uses_outcome_fields"
        ),
        "package_new_entry_authority_candidate_id": _first_present(
            signed_validation.get("package_new_entry_authority_candidate_id"),
            signed_validation.get("candidate_id"),
        ),
        "package_new_entry_authority_decision_time_utc": _first_present(
            signed_validation.get("package_new_entry_authority_decision_time_utc"),
            signed_validation.get("decision_time_utc"),
        ),
        "package_new_entry_authority_canonical_replay_candidate_instance_key": _first_present(
            signed_validation.get(
                "package_new_entry_authority_canonical_replay_candidate_instance_key"
            ),
            signed_validation.get("canonical_replay_candidate_instance_key"),
        ),
        "package_new_entry_authority_source_bound_replay_candidate_instance_key": _first_present(
            signed_validation.get(
                "package_new_entry_authority_source_bound_replay_candidate_instance_key"
            ),
            signed_validation.get("source_bound_replay_candidate_instance_key"),
        ),
        "package_new_entry_authority_candidate_instance_identity_status": _first_present(
            signed_validation.get(
                "package_new_entry_authority_candidate_instance_identity_status"
            ),
            signed_validation.get("candidate_instance_identity_status"),
        ),
        "package_new_entry_authority_selector_action": signed_validation.get(
            "selector_action"
        ),
        "package_new_entry_authority_selector_reason": signed_validation.get(
            "selector_reason"
        ),
        "package_new_entry_authority_candidate_decision_quality": (
            signed_validation.get("candidate_decision_quality")
        ),
        "package_new_entry_authority_candidate_decision_quality_field_sources": (
            signed_validation.get("candidate_decision_quality_field_sources")
        ),
        "package_new_entry_authority_candidate_decision_quality_source_boundary": (
            signed_validation.get("candidate_decision_quality_source_boundary")
        ),
        "package_new_entry_authority_candidate_decision_quality_alias_status": (
            signed_validation.get("candidate_decision_quality_alias_status")
        ),
        "package_new_entry_authority_candidate_decision_quality_alias_mismatches": list(
            signed_validation.get("candidate_decision_quality_alias_mismatches") or ()
        ),
        "package_new_entry_authority_candidate_decision_quality_provenance_failures": list(
            signed_validation.get("candidate_decision_quality_provenance_failures") or ()
        ),
        "package_new_entry_authority_candidate_decision_quality_bridge_materialized_fields": list(
            signed_validation.get(
                "bridge_materialized_candidate_decision_quality_fields"
            )
            or ()
        ),
        "package_new_entry_authority_candidate_decision_quality_bridge_materialized_boundary": (
            signed_validation.get(
                "bridge_materialized_candidate_decision_quality_source_boundary"
            )
        ),
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


UNSPECIFIED_SELECTED_POLICY_TOKENS = {
    "unspecified_expected_net_r_policy",
    "unspecified",
    "unknown_policy",
    "unknown",
    "none",
    "null",
    "not_required_no_selected_policy",
}


def _selected_policy_text_or_none(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.lower().replace("-", "_").replace(" ", "_")
    if normalized in UNSPECIFIED_SELECTED_POLICY_TOKENS:
        return None
    return text


def selected_policy_from_bridge_row(row: Mapping[str, Any]) -> str | None:
    geometry = _mapping(row.get("geometry_contract"))
    geometry_scalar_fields = _mapping(geometry.get("scalar_fields"))
    geometry_hash_material = _mapping(geometry.get("source_event_hash_material"))
    router = _mapping(row.get("moonshot_dynamic_execution_router_v4"))
    router_scalar_fields = _mapping(router.get("scalar_fields"))
    router_hash_material = _mapping(router.get("source_event_hash_material"))
    candidates = (
        row.get("expected_net_r_selected_policy"),
        row.get("selected_policy_expected_net_r_policy"),
        row.get("selected_policy_for_expected_net_r"),
        row.get("dynamic_geometry_policy"),
        row.get("gtos_vnext_selected_cell_risk_selected_policy"),
        row.get("selected_execution_policy"),
        row.get("selected_policy"),
        geometry.get("selected_policy"),
        geometry_scalar_fields.get("selected_policy"),
        geometry_hash_material.get("selected_policy"),
        router.get("selected_policy"),
        router_scalar_fields.get("selected_policy"),
        router_hash_material.get("selected_policy"),
        row.get("dynamic_execution_policy_id"),
        row.get("dynamic_execution_policy"),
        router.get("execution_policy_id"),
        router_scalar_fields.get("execution_policy_id"),
        router_hash_material.get("execution_policy_id"),
    )
    for value in candidates:
        policy = _selected_policy_text_or_none(value)
        if policy:
            return policy
    return None


def expected_net_r_from_bridge_row(row: Mapping[str, Any]) -> float | None:
    geometry = _mapping(row.get("geometry_contract"))
    geometry_scalar_fields = _mapping(geometry.get("scalar_fields"))
    geometry_hash_material = _mapping(geometry.get("source_event_hash_material"))
    return _first_numeric(
        {
            **dict(row),
            "geometry_expected_net_r": geometry.get("expected_net_r"),
            "geometry_candidate_expected_net_r": geometry.get("candidate_expected_net_r"),
            "geometry_scalar_expected_net_r": geometry_scalar_fields.get("expected_net_r"),
            "geometry_scalar_candidate_expected_net_r": geometry_scalar_fields.get(
                "candidate_expected_net_r"
            ),
            "geometry_hash_material_expected_net_r": geometry_hash_material.get(
                "expected_net_r"
            ),
            "geometry_hash_material_candidate_expected_net_r": geometry_hash_material.get(
                "candidate_expected_net_r"
            ),
        },
        "expected_net_r",
        "candidate_expected_net_r",
        "broker_net_expected_r",
        "scheduler_expected_net_r",
        "geometry_expected_net_r",
        "geometry_candidate_expected_net_r",
        "geometry_scalar_expected_net_r",
        "geometry_scalar_candidate_expected_net_r",
        "geometry_hash_material_expected_net_r",
        "geometry_hash_material_candidate_expected_net_r",
    )


def probability_from_bridge_row(row: Mapping[str, Any]) -> float | None:
    geometry = _mapping(row.get("geometry_contract"))
    geometry_scalar_fields = _mapping(geometry.get("scalar_fields"))
    geometry_hash_material = _mapping(geometry.get("source_event_hash_material"))
    return _first_numeric(
        {
            **dict(row),
            "geometry_probability": geometry.get("probability"),
            "geometry_candidate_probability": geometry.get("candidate_probability"),
            "geometry_scalar_probability": geometry_scalar_fields.get("probability"),
            "geometry_scalar_candidate_probability": geometry_scalar_fields.get(
                "candidate_probability"
            ),
            "geometry_hash_material_probability": geometry_hash_material.get(
                "probability"
            ),
            "geometry_hash_material_candidate_probability": geometry_hash_material.get(
                "candidate_probability"
            ),
        },
        "probability",
        "candidate_probability",
        "scheduler_probability",
        "selected_scheduler_probability",
        "geometry_probability",
        "geometry_candidate_probability",
        "geometry_scalar_probability",
        "geometry_scalar_candidate_probability",
        "geometry_hash_material_probability",
        "geometry_hash_material_candidate_probability",
    )


def source_completeness_from_bridge_row(row: Mapping[str, Any]) -> float | None:
    geometry = _mapping(row.get("geometry_contract"))
    geometry_scalar_fields = _mapping(geometry.get("scalar_fields"))
    geometry_hash_material = _mapping(geometry.get("source_event_hash_material"))
    return _first_numeric(
        {
            **dict(row),
            "geometry_source_completeness": geometry.get("source_completeness"),
            "geometry_candidate_source_completeness": geometry.get(
                "candidate_source_completeness"
            ),
            "geometry_scalar_source_completeness": geometry_scalar_fields.get(
                "source_completeness"
            ),
            "geometry_scalar_candidate_source_completeness": geometry_scalar_fields.get(
                "candidate_source_completeness"
            ),
            "geometry_hash_material_source_completeness": geometry_hash_material.get(
                "source_completeness"
            ),
            "geometry_hash_material_candidate_source_completeness": (
                geometry_hash_material.get("candidate_source_completeness")
            ),
        },
        "source_completeness",
        "candidate_source_completeness",
        "selected_scheduler_source_completeness",
        "geometry_source_completeness",
        "geometry_candidate_source_completeness",
        "geometry_scalar_source_completeness",
        "geometry_scalar_candidate_source_completeness",
        "geometry_hash_material_source_completeness",
        "geometry_hash_material_candidate_source_completeness",
    )


def selected_policy_expected_net_calibration_fields(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Materialize selected-policy expected-net truth for bridge artifacts.

    The bridge can carry reconstructed/proxy expected-net values, but it must
    not silently let them masquerade as selected-exit-policy calibrated values.
    """

    expected_net_r = expected_net_r_from_bridge_row(row)
    probability = probability_from_bridge_row(row)
    source_completeness = source_completeness_from_bridge_row(row)
    selected_policy = selected_policy_from_bridge_row(row)
    existing_status = _first_non_missing(
        row,
        (
            "selected_policy_expected_net_calibration_status",
            "selected_policy_expected_net_r_calibration_status",
            "expected_net_r_selected_policy_calibration_status",
            "selected_policy_exit_assumption_status",
            "expected_net_r_exit_assumption_status",
        ),
    )
    existing_source = _first_non_missing(
        row,
        (
            "selected_policy_expected_net_calibration_source",
            "selected_policy_expected_net_r_calibration_source",
            "expected_net_r_source",
            "candidate_expected_net_r_source",
        ),
    )
    field_sources = row.get("candidate_decision_quality_field_sources")
    field_sources = field_sources if isinstance(field_sources, Mapping) else {}
    expected_source = (
        str(existing_source or field_sources.get("expected_net_r") or "").strip()
        or None
    )
    existing_boundary = _first_non_missing(
        row,
        (
            "selected_policy_expected_net_calibration_source_boundary",
            "selected_policy_expected_net_calibration_boundary",
            "selected_policy_expected_net_r_calibration_boundary",
            "candidate_decision_quality_source_boundary",
            "source_boundary",
        ),
    )
    quality_boundary = _first_non_missing(
        row,
        (
            "candidate_decision_quality_source_boundary",
            "source_boundary",
        ),
    )
    existing_hash = _first_non_missing(
        row,
        (
            "selected_policy_expected_net_assumption_hash",
            "selected_policy_expected_net_calibration_hash",
            "selected_policy_expected_net_r_assumption_hash",
            "selected_policy_expected_net_r_calibration_hash",
            "selected_policy_exit_assumption_hash",
            "expected_net_r_exit_assumption_hash",
        ),
    )
    source_boundary = str(existing_boundary or "").strip()
    if (
        "uncalibrated" in source_boundary.lower().replace("-", "_").replace(" ", "_")
        and quality_boundary
    ):
        source_boundary = str(quality_boundary or "").strip()
    source_boundary = (
        source_boundary
        or "selected_package_bridge_predecision_quality_alias_repair"
    )
    source_boundary_norm = source_boundary.lower().replace("-", "_").replace(" ", "_")
    expected_source_norm = str(expected_source or "").lower().replace("-", "_").replace(" ", "_")
    bridge_proxy_expected_source = bool(
        expected_source_norm
        in {
            "packets.candidate_expected_net_r",
            "candidate_expected_net_r",
            "expected_net_r",
            "packets.expected_net_r",
            "selected_package_bridge_proxy_expected_net_r",
        }
        or "candidate_expected_net_r" in expected_source_norm
        or "bridge_proxy" in expected_source_norm
    )
    unsafe_boundary_tokens = (
        "terminal",
        "trade_result",
        "replay_order_result",
        "final_r",
        "actual_r",
        "live_fill",
        "broker_live",
        "postdecision",
        "post_decision",
        "realized",
        "inferred",
        "fallback_authority",
    )
    existing_status_norm = (
        str(existing_status or "").strip().lower().replace("-", "_").replace(" ", "_")
    )
    expected_net_source_safe = bool(
        expected_source
        and "predecision" in source_boundary_norm
        and (
            "no_outcome" in source_boundary_norm
            or "no_outcome_fields" in source_boundary_norm
        )
        and not any(
            marker in expected_source_norm
            for marker in (
                "outcome",
                "terminal",
                "trade_result",
                "replay_order_result",
                "final_r",
                "actual_r",
                "live_fill",
                "broker_live",
                "postdecision",
                "post_decision",
                "realized",
                "inferred",
                "fallback_authority",
            )
        )
        and not any(
            marker in source_boundary_norm
            for marker in unsafe_boundary_tokens
        )
        and not bridge_proxy_expected_source
    )
    existing_calibrated_status = bool(
        ("calibrated" in existing_status_norm or "aligned" in existing_status_norm)
        and expected_net_source_safe
        and not any(
            marker in existing_status_norm
            for marker in (
                "missing",
                "stale",
                "legacy",
                "uncalibrated",
                "mismatch",
                "not_required",
            )
        )
    )
    bridge_proxy_calibrated = bool(
        selected_policy
        and expected_net_r is not None
        and (
            bridge_proxy_expected_source
            or (
                expected_source
                and "predecision" in source_boundary_norm
                and (
                    "no_outcome" in source_boundary_norm
                    or "no_outcome_fields" in source_boundary_norm
                )
                and not any(
                    marker in source_boundary_norm
                    for marker in unsafe_boundary_tokens
                )
            )
        )
        and source_boundary
    )
    if expected_net_r is None:
        status = "expected_net_r_missing"
        calibrated = False
        required = bool(selected_policy)
    elif not selected_policy:
        status = "not_required_no_selected_policy"
        calibrated = True
        required = False
    else:
        if existing_status_norm == "not_required_no_selected_policy":
            existing_status_norm = ""
            existing_status = None
        calibrated = bool(existing_calibrated_status)
        status = (
            str(existing_status).strip()
            if existing_status and existing_calibrated_status
            else "selected_policy_expected_net_bridge_proxy_diagnostic_only"
            if bridge_proxy_calibrated
            else "selected_policy_expected_net_calibration_missing"
        )
        required = True
    if required and not calibrated:
        source_boundary = (
            "selected_policy_expected_net_uncalibrated_bridge_proxy_predecision_quality"
        )
    assumption_hash = str(existing_hash or "").strip() if existing_calibrated_status else ""
    if not assumption_hash and expected_net_r is not None and existing_calibrated_status:
        assumption_hash = stable_sha256(
            {
                "selected_policy": selected_policy,
                "expected_net_r": expected_net_r,
                "expected_net_r_source": expected_source,
                "source_boundary": source_boundary,
                "status": status,
                "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
                "calibration_source_class": (
                    "predecision_selected_policy_expected_net_bridge_proxy"
                    if bridge_proxy_calibrated
                    else "upstream_selected_policy_expected_net_calibration"
                    if existing_calibrated_status
                    else "uncalibrated_selected_policy_expected_net_proxy"
                ),
            }
        )
    return {
        "selected_policy_expected_net_r": expected_net_r,
        "selected_policy_probability": probability,
        "selected_policy_source_completeness": source_completeness,
        "selected_policy_quality_alias_status": (
            "selected_policy_proxy_quality_materialized"
            if (
                expected_net_r is not None
                and probability is not None
                and source_completeness is not None
            )
            else "selected_policy_proxy_quality_partial"
        ),
        "selected_policy_quality_source_boundary": source_boundary,
        "selected_policy_expected_net_calibration_status": status,
        "selected_policy_expected_net_r_calibration_status": status,
        "expected_net_r_selected_policy_calibration_status": status,
        "selected_policy_expected_net_calibrated": calibrated,
        "selected_policy_expected_net_calibration_required": required,
        "selected_policy_expected_net_calibration_source": (
            expected_source or "selected_package_bridge_proxy_expected_net_r"
        )
        if expected_net_r is not None
        else None,
        "selected_policy_expected_net_calibration_source_boundary": source_boundary,
        "selected_policy_expected_net_calibration_boundary": source_boundary,
        "selected_policy_expected_net_assumption_hash": assumption_hash or None,
        "selected_policy_expected_net_r_assumption_hash": assumption_hash or None,
        "selected_policy_expected_net_calibration_hash": assumption_hash or None,
        "selected_policy_for_expected_net_r": selected_policy,
    }


def owner_approved_reconstructed_proxy_selected_policy_expected_net_bridge_fields(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Selected-package bridge authority for owner-approved reconstructed replay only."""

    source_contract = reconstructed_proxy_package_selection_source_contract(
        RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY_PATH
    )
    return timewarp_loop.owner_approved_reconstructed_proxy_selected_policy_expected_net_fields(
        candidate=row,
        expected_net_r=expected_net_r_from_bridge_row(row),
        selected_policy=selected_policy_from_bridge_row(row),
        enabled=source_contract.get("valid") is True,
        source_boundary_note=(
            "selected_package_replay_bridge_owner_approved_reconstructed_proxy_"
            "local_replay_only_final_live_closed"
        ),
        source_path=source_contract.get("source_path"),
        source_sha256=source_contract.get("source_semantic_sha256"),
        source_semantic_sha256=source_contract.get("source_semantic_sha256"),
        source_artifact_sha256=source_contract.get("source_artifact_sha256"),
        source_digest_semantics=source_contract.get("semantic_digest_boundary"),
    )


def hydrate_candidate_quality_aliases(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Repair compact bridge aliases from predecision replay fields only."""

    row = canonicalize_candidate_geometry(
        candidate,
        source="selected_package_bridge_hydrate_quality_aliases",
    )

    normalize_bridge_predecision_fillability_source_time(row)

    def set_if_missing(key: str, value: Any) -> None:
        if _missing_value(row.get(key)) and not _missing_value(value):
            row[key] = value

    pretrade_cost_packet = timewarp_loop.normalized_pretrade_cost_packet_from_packets(row)
    if pretrade_cost_packet:
        set_if_missing("pretrade_cost_packet_status", pretrade_cost_packet.get("status"))
        cost_authority = _first_present(
            pretrade_cost_packet.get("cost_authority"),
            pretrade_cost_packet.get("authority"),
        )
        set_if_missing("cost_authority", cost_authority)
        set_if_missing("execution_cost_authority", cost_authority)
        set_if_missing(
            "cost_source_gap_status",
            pretrade_cost_packet.get("cost_source_gap_status"),
        )
        set_if_missing(
            "candidate_cost_r_fallback_is_authority",
            pretrade_cost_packet.get("candidate_cost_r_fallback_is_authority"),
        )
        set_if_missing(
            "source_gap_cost_fallback_blocked",
            pretrade_cost_packet.get("source_gap_cost_fallback_blocked"),
        )
        set_if_missing(
            "candidate_cost_r_fallback_diagnostic",
            pretrade_cost_packet.get("old_timewarp_candidate_cost_r_fallback_diagnostic"),
        )
        set_if_missing(
            "old_proxy_vs_broker_calibrated_delta_r",
            pretrade_cost_packet.get("old_proxy_vs_broker_calibrated_delta_r"),
        )
        refusal_reasons = pretrade_cost_packet.get("refusal_reasons")
        if isinstance(refusal_reasons, Sequence) and not isinstance(
            refusal_reasons,
            (bytes, bytearray, str),
        ):
            set_if_missing("pretrade_cost_refusal_reasons", list(refusal_reasons))
        else:
            set_if_missing("pretrade_cost_refusal_reasons", refusal_reasons)

    ev_r = _safe_float_or_none(
        row.get("candidate_ev_r") if row.get("candidate_ev_r") is not None else row.get("ev_r")
    )
    cost_r = _safe_float_or_none(
        row.get("broker_calibrated_expected_cost_r")
        if row.get("broker_calibrated_expected_cost_r") is not None
        else row.get("broker_pretrade_cost_r")
        if row.get("broker_pretrade_cost_r") is not None
        else row.get("expected_cost_r")
        if row.get("expected_cost_r") is not None
        else row.get("cost_r")
        if row.get("cost_r") is not None
        else _first_present(
            pretrade_cost_packet.get("total_cost_r"),
            pretrade_cost_packet.get("expected_total_cost_r"),
        )
    )
    if ev_r is not None:
        set_if_missing("candidate_ev_r", ev_r)
        set_if_missing("ev_r", ev_r)
        set_if_missing("expectancy_r", ev_r)
    if cost_r is not None:
        set_if_missing("expected_cost_r", cost_r)
        set_if_missing("cost_r", cost_r)
        set_if_missing("broker_calibrated_expected_cost_r", cost_r)
        set_if_missing("broker_pretrade_cost_r", cost_r)
    expected_net_r = expected_net_r_from_bridge_row(row)
    if expected_net_r is None and ev_r is not None and cost_r is not None:
        expected_net_r = round(ev_r - cost_r, 12)
    if expected_net_r is not None:
        set_if_missing("expected_net_r", expected_net_r)
        set_if_missing("candidate_expected_net_r", expected_net_r)
        row.update(
            owner_approved_reconstructed_proxy_selected_policy_expected_net_bridge_fields(
                row
            )
        )
        for key, value in selected_policy_expected_net_calibration_fields(row).items():
            set_if_missing(key, value)

    entry_quality_fill_probability = _safe_float_or_none(
        row.get("fill_probability")
        if row.get("fill_probability") is not None
        else row.get("candidate_fill_probability")
        if row.get("candidate_fill_probability") is not None
        else row.get("heuristic_fill_probability")
    )
    if entry_quality_fill_probability is not None:
        set_if_missing("entry_quality_fill_probability", entry_quality_fill_probability)
    _project_final_signed_fillability(row)
    fill_probability, _fill_probability_source = execution_fillability_authority(row)

    source_completeness = _safe_float_or_none(row.get("source_completeness"))
    source_status = str(row.get("source_completeness_status") or "")
    if source_completeness is None and source_status in {
        "complete",
        "source_completeness_present",
        "source_complete_for_timewarp_candidate",
    }:
        source_completeness = 1.0
    if source_completeness is not None:
        set_if_missing("source_completeness", source_completeness)
    if row.get("source_completeness") is not None and not row.get(
        "source_completeness_status"
    ):
        row["source_completeness_status"] = "source_completeness_present"

    selector_packet = row.get("selector_packet")
    scalar_selector = (
        selector_packet.get("scalar_fields")
        if isinstance(selector_packet, Mapping)
        and isinstance(selector_packet.get("scalar_fields"), Mapping)
        else {}
    )
    if not row.get("selector_action") and scalar_selector.get("action"):
        row["selector_action"] = scalar_selector.get("action")
    if not row.get("selector_reason") and scalar_selector.get("reason"):
        row["selector_reason"] = scalar_selector.get("reason")

    source_bound_allowed = canonical_package_source_bound_candidate_use_allowed(row)
    if source_bound_allowed:
        row.setdefault("package_source_bound_admission_diagnostic", True)
        if fill_probability is None:
            row["diagnostic_fill_probability_default"] = (
                PACKAGE_BRIDGE_DEFAULT_FILL_PROBABILITY
            )
            row["diagnostic_fill_probability_default_source"] = (
                "selected_package_bridge_package_min_fill_probability_floor"
            )
        if source_completeness is None:
            row["diagnostic_source_completeness_default"] = (
                PACKAGE_BRIDGE_DEFAULT_SOURCE_COMPLETENESS
            )
            row["diagnostic_source_completeness_default_source"] = (
                "selected_package_bridge_missing_source_completeness_degraded_default"
            )
        executable_package_allowed, executable_package_reason = executable_package_use_detail(
            row,
            source_bound_allowed=True,
        )
        row["source_bound_package_candidate_use_allowed"] = True
        row["ultimate_package_source_bound_candidate_use_allowed"] = True
        row["package_replay_source_bound_candidate_use_allowed"] = (
            True
        )
        row["package_replay_candidate_use_allowed"] = executable_package_allowed
        row["package_replay_executable_candidate_use_allowed"] = (
            executable_package_allowed
        )
        row["package_replay_executable_candidate_use_allowed_reason"] = (
            executable_package_reason
        )
        set_if_missing(
            "selected_package_candidate_use_allowed_status",
            executable_package_reason,
        )
        row.update(package_authority_bridge_fields(row, source_bound_allowed=True))
    else:
        row.setdefault("package_source_bound_admission_diagnostic", False)
        row.setdefault("source_bound_package_candidate_use_allowed", False)
        row.setdefault("ultimate_package_source_bound_candidate_use_allowed", False)
        row.setdefault("package_replay_source_bound_candidate_use_allowed", False)
        row.setdefault("package_replay_candidate_use_allowed", False)
        row.setdefault("package_replay_executable_candidate_use_allowed", False)
        row.setdefault(
            "package_replay_executable_candidate_use_allowed_reason",
            "no_package_axis_or_candidate_use_alias",
        )
        row.setdefault(
            "selected_package_candidate_use_allowed_status",
            "no_package_axis_or_candidate_use_alias",
        )
        row.update(timewarp_loop.ultimate_package_effective_signal_fields(row))
        row.update(package_authority_bridge_fields(row, source_bound_allowed=False))
    row["candidate_decision_quality"] = candidate_decision_quality_envelope(row)
    normalize_bridge_predecision_fillability_source_time(row)
    return row


PACKAGE_USE_ALIAS_FIELDS = (
    "source_bound_package_candidate_use_allowed",
    "ultimate_package_source_bound_candidate_use_allowed",
    "ultimate_package_effective_source_bound_candidate_use_allowed",
    "package_replay_source_bound_candidate_use_allowed",
    "package_replay_candidate_use_allowed",
)
CANONICAL_PACKAGE_SOURCE_BOUND_USE_ALIAS_FIELDS = (
    "source_bound_package_candidate_use_allowed",
    "ultimate_package_source_bound_candidate_use_allowed",
    "package_replay_source_bound_candidate_use_allowed",
)


def canonical_package_source_bound_candidate_use_allowed(
    row: Mapping[str, Any],
) -> bool:
    """Exclude member-axis/effective aliases from canonical candidate authority."""

    canonical_values = [
        row.get(field)
        for field in CANONICAL_PACKAGE_SOURCE_BOUND_USE_ALIAS_FIELDS
        if not _missing_value(row.get(field))
    ]
    signed_exact_instance = trusted_signed_package_new_entry_authority_surface(row)
    if any(value is False for value in canonical_values):
        return signed_exact_instance
    if any(_truthy(value) for value in canonical_values):
        return True
    return signed_exact_instance


PACKAGE_BRIDGE_DEFAULT_FILL_PROBABILITY = 0.25
PACKAGE_BRIDGE_DEFAULT_SOURCE_COMPLETENESS = 0.25
PACKAGE_BRIDGE_MIN_EXECUTABLE_SOURCE_COMPLETENESS = 0.95
PACKAGE_BRIDGE_MIN_EXECUTABLE_EXPECTED_NET_R = 0.40
PACKAGE_BRIDGE_MIN_EXECUTABLE_PROBABILITY = 0.58
PACKAGE_BRIDGE_MIN_EXECUTABLE_FILL_PROBABILITY = 0.25
PACKAGE_BRIDGE_SELECTOR_REDUCED_MIN_SOURCE_COMPLETENESS = 0.65
PACKAGE_BRIDGE_SELECTOR_REDUCED_MIN_EXPECTED_NET_R = 0.70
PACKAGE_BRIDGE_SELECTOR_REDUCED_MIN_PROBABILITY = 0.70
PACKAGE_BRIDGE_SELECTOR_REDUCED_MIN_FILL_PROBABILITY = 0.20
PACKAGE_BRIDGE_ROUTER_REFUSAL_MIN_EXPECTED_NET_R = 0.85
PACKAGE_BRIDGE_ROUTER_REFUSAL_MIN_PROBABILITY = 0.75
PACKAGE_BRIDGE_ROUTER_REFUSAL_MIN_FILL_PROBABILITY = 0.60
PACKAGE_BRIDGE_ROUTER_REFUSAL_MIN_SOURCE_COMPLETENESS = 0.95
PACKAGE_BRIDGE_SOURCE_BOUND_ROUTER_REFUSAL_MIN_EXPECTED_NET_R = 0.55
PACKAGE_BRIDGE_SOURCE_BOUND_ROUTER_REFUSAL_MIN_PROBABILITY = 0.70
PACKAGE_BRIDGE_SOURCE_BOUND_ROUTER_REFUSAL_MIN_FILL_PROBABILITY = 0.80
PACKAGE_BRIDGE_SOURCE_BOUND_ROUTER_REFUSAL_MIN_SOURCE_COMPLETENESS = 0.95
PACKAGE_BRIDGE_SOURCE_REQUIRED_MIN_EXPECTED_NET_R = 0.80
PACKAGE_BRIDGE_SOURCE_REQUIRED_MIN_PROBABILITY = 0.75
PACKAGE_BRIDGE_SOURCE_REQUIRED_MIN_FILL_PROBABILITY = 0.12


ASOF_CANDIDATE_FIELD_SOURCE_BOUNDARIES = {
    "asof_candidate_fields_only_no_postdecision_path",
    "closed_m15_predecision_asof_no_postdecision_path",
}


def bridge_predecision_source_time(row: Mapping[str, Any]) -> Any:
    return _first_present(
        row.get("predecision_current_price_source_time_utc"),
        row.get("current_price_source_time_utc"),
        row.get("current_price_asof_utc"),
        row.get("source_candle_time_utc"),
        row.get("candle_close_utc"),
    )


def normalize_bridge_predecision_fillability_source_time(row: dict[str, Any]) -> None:
    """Keep bridge fillability price provenance claim-bearing and time-stamped."""

    fillability = row.get("predecision_limit_fillability")
    if not isinstance(fillability, Mapping):
        return
    fillability = dict(fillability)
    boundary = str(
        fillability.get("current_price_source_boundary")
        or fillability.get("source_boundary")
        or row.get("predecision_current_price_source_boundary")
        or row.get("current_price_source_boundary")
        or ""
    ).strip()
    if boundary not in ASOF_CANDIDATE_FIELD_SOURCE_BOUNDARIES:
        row["predecision_limit_fillability"] = fillability
        return
    source_time = _first_present(
        fillability.get("current_price_source_time_utc"),
        fillability.get("source_time_utc"),
        bridge_predecision_source_time(row),
    )
    if _missing_value(source_time):
        row["predecision_limit_fillability_source_time_status"] = (
            "source_time_missing_non_executable"
        )
        row["predecision_limit_fillability"] = fillability
        return
    decision_time = _first_present(
        row.get("decision_time_utc"),
        row.get("asof_utc"),
    )
    source_dt = timewarp_loop.parse_utc(source_time)
    decision_dt = timewarp_loop.parse_utc(decision_time)
    if source_dt is None or decision_dt is None or source_dt >= decision_dt:
        row["predecision_limit_fillability_source_time_status"] = (
            "source_time_not_before_decision_non_executable"
        )
        row["diagnostic_unsafe_predecision_fillability_source_time_utc"] = (
            source_time
        )
        row["predecision_limit_fillability"] = fillability
        return
    fillability.setdefault("current_price_source_boundary", boundary)
    fillability.setdefault("source_boundary", boundary)
    fillability["current_price_source_time_utc"] = source_time
    fillability.setdefault("source_time_utc", source_time)
    row["predecision_limit_fillability"] = fillability
    if _missing_value(row.get("predecision_current_price_source_boundary")):
        row["predecision_current_price_source_boundary"] = boundary
    if _missing_value(row.get("current_price_source_boundary")):
        row["current_price_source_boundary"] = boundary
    if _missing_value(row.get("predecision_current_price_source_time_utc")):
        row["predecision_current_price_source_time_utc"] = source_time
    if _missing_value(row.get("current_price_source_time_utc")):
        row["current_price_source_time_utc"] = source_time
    if _missing_value(row.get("predecision_current_price")) and not _missing_value(
        fillability.get("current_price")
    ):
        row["predecision_current_price"] = fillability.get("current_price")
    if _missing_value(row.get("predecision_current_price_source")):
        row["predecision_current_price_source"] = (
            fillability.get("current_price_source")
            or "predecision_limit_fillability.current_price"
        )
    row["predecision_limit_fillability_source_time_status"] = (
        "asof_candidate_field_source_time_stamped"
    )


ROUTER_REFUSAL_AUTHORITY_FAMILIES = {
    "router_refusal_softening",
    "source_bound_router_refusal_materialization",
    "source_bound_router_refusal_replay_materialization",
}


def _explicit_package_authority_family(row: Mapping[str, Any]) -> str:
    authority = row.get("ultimate_candidate_package_open_reduced_risk_authority")
    authority = authority if isinstance(authority, Mapping) else {}
    return str(
        row.get("package_new_entry_authority_authority_family")
        or row.get("package_open_reduced_authority_family")
        or row.get("selected_scheduler_package_open_reduced_authority_family")
        or authority.get("package_new_entry_authority_authority_family")
        or authority.get("authority_family")
        or ""
    ).strip()


def _router_refusal_open_reduced_authority_applies(row: Mapping[str, Any]) -> bool:
    selector_reason = str(row.get("selector_reason") or "").strip()
    authority = row.get("ultimate_candidate_package_open_reduced_risk_authority")
    authority = authority if isinstance(authority, Mapping) else {}
    authority_family = _explicit_package_authority_family(row)
    if authority_family and authority_family not in ROUTER_REFUSAL_AUTHORITY_FAMILIES:
        return False
    authority_reason = str(
        authority.get("selector_reason")
        or authority.get("original_selector_reason")
        or authority.get("authority_reason")
        or ""
    ).strip()
    router_reasons = {
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
        "source_bound_router_refusal_open_reduced_materialized_for_replay",
    }
    return bool(
        authority_family in ROUTER_REFUSAL_AUTHORITY_FAMILIES
        or selector_reason in router_reasons
        or authority_reason in router_reasons
    )


def _source_bound_router_refusal_materialization_applies(row: Mapping[str, Any]) -> bool:
    authority_family = _explicit_package_authority_family(row)
    if authority_family and authority_family not in ROUTER_REFUSAL_AUTHORITY_FAMILIES:
        return False
    if authority_family in {
        "source_bound_router_refusal_materialization",
        "source_bound_router_refusal_replay_materialization",
    }:
        return True
    selector_reason = str(row.get("selector_reason") or "").strip()
    authority_reason = str(
        row.get("package_new_entry_authority_selector_reason") or ""
    ).strip()
    authority_source = str(
        row.get("authority_source")
        or row.get("package_new_entry_authority_authority_source")
        or ""
    ).strip()
    authority = row.get("ultimate_candidate_package_open_reduced_risk_authority")
    authority = authority if isinstance(authority, Mapping) else {}
    nested_reason = str(
        authority.get("selector_reason")
        or authority.get("original_selector_reason")
        or authority.get("authority_reason")
        or authority.get("package_new_entry_authority_selector_reason")
        or ""
    ).strip()
    nested_source = str(
        authority.get("authority_source")
        or authority.get("package_new_entry_authority_authority_source")
        or ""
    ).strip()
    return bool(
        "source_bound_router_refusal_open_reduced_materialized_for_replay"
        in {selector_reason, authority_reason, nested_reason}
        or "derived_from_source_bound_router_refusal_package_authority"
        in {authority_source, nested_source}
    )


def _candidate_quality_floor_requirements(
    row: Mapping[str, Any],
    *,
    action_intent: str | None = None,
) -> dict[str, float]:
    selector_action = str(row.get("selector_action") or "").strip()
    normalized_action_intent = normalize_bridge_action_intent(
        action_intent
        or row.get("scheduler_materialization_action_intent")
        or row.get("action_intent")
        or row.get("lifecycle_action")
        or "new_position"
    )
    if (
        _router_refusal_open_reduced_authority_applies(row)
        and normalized_action_intent == "new_position"
    ):
        if _source_bound_router_refusal_materialization_applies(row):
            return {
                "expected_net_r": PACKAGE_BRIDGE_SOURCE_BOUND_ROUTER_REFUSAL_MIN_EXPECTED_NET_R,
                "probability": PACKAGE_BRIDGE_SOURCE_BOUND_ROUTER_REFUSAL_MIN_PROBABILITY,
                "fill_probability": PACKAGE_BRIDGE_SOURCE_BOUND_ROUTER_REFUSAL_MIN_FILL_PROBABILITY,
            }
        return {
            "expected_net_r": PACKAGE_BRIDGE_ROUTER_REFUSAL_MIN_EXPECTED_NET_R,
            "probability": PACKAGE_BRIDGE_ROUTER_REFUSAL_MIN_PROBABILITY,
            "fill_probability": PACKAGE_BRIDGE_ROUTER_REFUSAL_MIN_FILL_PROBABILITY,
        }
    source_required_override = source_required_replay_override_applied(row)
    if source_required_override:
        return {
            "expected_net_r": PACKAGE_BRIDGE_SOURCE_REQUIRED_MIN_EXPECTED_NET_R,
            "probability": PACKAGE_BRIDGE_SOURCE_REQUIRED_MIN_PROBABILITY,
            "fill_probability": PACKAGE_BRIDGE_SOURCE_REQUIRED_MIN_FILL_PROBABILITY,
        }
    if selector_action in {"reduce-risk", "open-reduced-risk"}:
        return {
            "expected_net_r": PACKAGE_BRIDGE_SELECTOR_REDUCED_MIN_EXPECTED_NET_R,
            "probability": PACKAGE_BRIDGE_SELECTOR_REDUCED_MIN_PROBABILITY,
            "fill_probability": PACKAGE_BRIDGE_SELECTOR_REDUCED_MIN_FILL_PROBABILITY,
        }
    return {
        "expected_net_r": PACKAGE_BRIDGE_MIN_EXECUTABLE_EXPECTED_NET_R,
        "probability": PACKAGE_BRIDGE_MIN_EXECUTABLE_PROBABILITY,
        "fill_probability": PACKAGE_BRIDGE_MIN_EXECUTABLE_FILL_PROBABILITY,
    }


def _bridge_source_completeness_floor(selector_action: str) -> float:
    if selector_action in {"reduce-risk", "open-reduced-risk"}:
        return PACKAGE_BRIDGE_SELECTOR_REDUCED_MIN_SOURCE_COMPLETENESS
    return PACKAGE_BRIDGE_MIN_EXECUTABLE_SOURCE_COMPLETENESS


def _first_numeric(row: Mapping[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = _safe_float_or_none(row.get(key))
        if value is not None:
            return value
    return None


EXECUTION_FILLABILITY_MISSING_SOURCE = "execution_fillability_missing_source_bound_input"


_BRIDGE_PREDECISION_FILLABILITY_SCALAR_KEYS = (
    "pending_limit_fillability_probability",
    "pending_fill_probability",
    "predecision_limit_fillability_probability",
    "limit_fillability_probability",
    "limit_fill_probability",
)

_BRIDGE_PREDECISION_FILLABILITY_SOURCE_MARKERS = (
    "predecision_limit_fill",
    "predecision_pending_fill",
    "predecision_order_fill",
    "pending_limit_fill",
)

_BRIDGE_PREDECISION_FILLABILITY_UNSAFE_MARKERS = (
    "postdecision",
    "post_decision",
    "outcome",
    "realized",
    "broker_live",
    "live_fill",
    "future",
    "inferred",
    "fallback",
    "generic",
    "model",
    "unknown",
)


def _bridge_predecision_fillability_source_allowed(source: Any) -> bool:
    """Accept an explicit current predecision order/fillability source only."""
    return execution_fillability_source_is_authoritative(source)


def _bridge_predecision_fillability_boundary_allowed(boundary: Any) -> bool:
    return predecision_execution_fillability_source_boundary_allowed(
        boundary
    )


def _bridge_predecision_fillability_source_time(
    row: Mapping[str, Any],
    *,
    nested: Mapping[str, Any] | None = None,
    field: str = "",
) -> Any:
    nested = nested if isinstance(nested, Mapping) else {}
    return _first_present(
        nested.get("source_time_utc"),
        nested.get("current_price_source_time_utc"),
        nested.get("asof_utc"),
        row.get(f"{field}_source_time_utc") if field else None,
        row.get("execution_fill_probability_source_time_utc"),
        row.get("execution_fillability_source_time_utc"),
        row.get("predecision_limit_fillability_source_time_utc"),
        row.get("predecision_current_price_source_time_utc"),
        row.get("current_price_source_time_utc"),
    )


def _bridge_predecision_fillability_boundary(
    row: Mapping[str, Any],
    *,
    nested: Mapping[str, Any] | None = None,
    field: str = "",
) -> Any:
    nested = nested if isinstance(nested, Mapping) else {}
    return _first_present(
        nested.get("source_boundary"),
        nested.get("current_price_source_boundary"),
        row.get(f"{field}_source_boundary") if field else None,
        row.get("execution_fill_probability_source_boundary"),
        row.get("execution_fillability_source_boundary"),
        row.get("predecision_limit_fillability_source_boundary"),
        row.get("predecision_current_price_source_boundary"),
        row.get("current_price_source_boundary"),
        row.get("candidate_decision_quality_source_boundary"),
    )


def _bridge_predecision_fillability_provenance_allowed(
    row: Mapping[str, Any],
    *,
    source: Any,
    nested: Mapping[str, Any] | None = None,
    field: str = "",
) -> bool:
    nested = nested if isinstance(nested, Mapping) else {}
    if "available" in nested and _explicit_false(nested.get("available")):
        return False
    nested_status = str(nested.get("status") or "").strip().lower()
    if any(marker in nested_status for marker in ("unavailable", "invalid", "blocked")):
        return False
    if not _bridge_predecision_fillability_source_allowed(source):
        return False
    if not _bridge_predecision_fillability_boundary_allowed(
        _bridge_predecision_fillability_boundary(
            row,
            nested=nested,
            field=field,
        )
    ):
        return False
    source_time = timewarp_loop.parse_utc(
        str(
            _bridge_predecision_fillability_source_time(
                row,
                nested=nested,
                field=field,
            )
            or ""
        )
    )
    decision_time = timewarp_loop.parse_utc(str(row.get("decision_time_utc") or ""))
    return bool(
        source_time is not None
        and decision_time is not None
        and source_time < decision_time
    )


def bridge_predecision_execution_fillability_detail_for_stamp(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Resolve raw predecision fillability only while producing a fresh signature.

    This producer boundary intentionally ignores every
    ``package_new_entry_authority_*`` alias. Invalid, provisional, or stale signed
    claims remain fail-closed at ``execution_fillability_authority`` and all
    executable consumers; they cannot become authority merely because the bridge
    is preparing a replacement signature from current order evidence.
    """

    unsigned_surface = {
        key: copy.deepcopy(value)
        for key, value in row.items()
        if not key.startswith("package_new_entry_authority_")
        and key
        not in {
            "expected_package_new_entry_authority_hash_sha256",
            "ultimate_candidate_package_open_reduced_risk_authority",
            "ultimate_candidate_package_reduce_risk_authority",
            "ultimate_candidate_package_reduced_risk_authority",
            "signed_new_entry_authority",
        }
    }
    detail = resolve_execution_fillability_surfaces(unsigned_surface)
    value = _safe_float_or_none(detail.get("value"))
    if value is None:
        return {
            **detail,
            "value": None,
            "source": EXECUTION_FILLABILITY_MISSING_SOURCE,
        }
    return {
        **detail,
        "value": max(0.0, min(1.0, value)),
        "source": str(detail.get("source") or ""),
    }


def bridge_predecision_execution_fillability_for_stamp(
    row: Mapping[str, Any],
) -> tuple[float | None, str]:
    detail = bridge_predecision_execution_fillability_detail_for_stamp(row)
    return _safe_float_or_none(detail.get("value")), str(
        detail.get("source") or EXECUTION_FILLABILITY_MISSING_SOURCE
    )


def execution_fillability_authority(
    row: Mapping[str, Any],
) -> tuple[float | None, str]:
    """Delegate strict consumer resolution to the hardened runtime resolver."""

    value, source, authority_class = (
        timewarp_loop.source_bound_execution_fill_probability_with_source(row)
    )
    invalid_source = timewarp_loop.INVALID_SIGNED_EXECUTION_FILLABILITY_SOURCE
    if source == invalid_source or authority_class == invalid_source:
        return None, invalid_source
    if value is not None:
        return value, source
    return None, EXECUTION_FILLABILITY_MISSING_SOURCE


def selected_package_bridge_quality_fields(
    candidate: Mapping[str, Any],
    *,
    matched_stable_member_axis_ids: Iterable[Any] = (),
    matched_members: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Expose candidate quality and package-use aliases on every bridge row."""

    candidate = canonicalize_candidate_geometry(
        candidate,
        source="selected_package_bridge_quality_fields",
    )
    matched_axis_ids = stable_unique(matched_stable_member_axis_ids)
    if not matched_axis_ids:
        matched_axis_ids = _validated_signed_member_axis_ids(candidate)
    matched_member_rows = [
        row for row in matched_members if isinstance(row, Mapping)
    ]
    candidate_role_counts = candidate.get("ultimate_package_matched_member_axis_role_counts")
    candidate_role_counts = (
        candidate_role_counts if isinstance(candidate_role_counts, Mapping) else {}
    )
    upstream_package_alias_allowed = any(
        _truthy(candidate.get(field)) for field in PACKAGE_USE_ALIAS_FIELDS
    )
    upstream_package_alias_present = any(
        not _missing_value(candidate.get(field)) for field in PACKAGE_USE_ALIAS_FIELDS
    )
    bridge_member_axis_authority_bound = bool(matched_axis_ids)
    package_use_allowed = bridge_member_axis_authority_bound
    role_counts = Counter(
        str(
            row.get("package_role")
            or timewarp_loop.package_role_for_sleeve_type(row.get("sleeve_type"))
        )
        for row in matched_member_rows
    )
    if not role_counts and candidate_role_counts:
        role_counts = Counter(
            {
                str(role): _safe_float_or_none(count) or 0.0
                for role, count in candidate_role_counts.items()
                if str(role or "").strip()
            }
        )
    admission_count = role_counts.get("scheduler_lifecycle_core", 0) + role_counts.get(
        "promote_default_off_signal",
        0,
    )
    candidate_admission_count = _safe_float_or_none(
        candidate.get("ultimate_package_admission_member_axis_match_count")
    )
    if not admission_count and candidate_admission_count is not None:
        admission_count = candidate_admission_count
    source_r_values = [
        _safe_float_or_none(row.get("combined_source_bound_signal_r")) or 0.0
        for row in matched_member_rows
    ]
    source_r_sum = round(sum(source_r_values), 9) if source_r_values else None
    source_r_max = (
        round(max(source_r_values), 9)
        if source_r_values
        else None
    )
    if source_r_sum is None:
        source_r_sum = round(
            _safe_float_or_none(
                candidate.get("ultimate_package_member_axis_source_bound_signal_r_sum")
            )
            or 0.0,
            9,
        )
    if source_r_max is None:
        source_r_max = round(
            _safe_float_or_none(
                candidate.get("ultimate_package_member_axis_max_source_bound_signal_r")
            )
            or 0.0,
            9,
        )
    matched_sleeve_ids = stable_unique(
        row.get("sleeve_id") for row in matched_member_rows
    )
    if not matched_sleeve_ids:
        matched_sleeve_ids = stable_unique(
            _first_non_missing(
                candidate,
                (
                    "ultimate_package_matched_sleeve_ids",
                    "matched_sleeve_ids",
                ),
            )
            or []
        )
    matched_sleeve_count = _safe_float_or_none(
        _first_non_missing(
            candidate,
            (
                "ultimate_package_matched_sleeve_count",
                "matched_sleeve_count",
            ),
        )
    )
    if matched_sleeve_count is None and matched_sleeve_ids:
        matched_sleeve_count = float(len(matched_sleeve_ids))
    admission_sleeve_count = _safe_float_or_none(
        _first_non_missing(
            candidate,
            (
                "ultimate_package_admission_sleeve_match_count",
                "admission_sleeve_match_count",
            ),
        )
    )
    if admission_sleeve_count is None:
        admission_sleeve_count = float(
            role_counts.get("scheduler_lifecycle_core", 0)
            + role_counts.get("promote_default_off_signal", 0)
        )
    prior_effective_admission_count = _safe_float_or_none(
        candidate.get("ultimate_package_effective_admission_count")
    )
    effective_admission_count = max(
        _safe_float_or_none(admission_count) or 0.0,
        _safe_float_or_none(admission_sleeve_count) or 0.0,
        prior_effective_admission_count or 0.0,
    )
    non_admission_sleeve_count = _safe_float_or_none(
        _first_non_missing(
            candidate,
            (
                "ultimate_package_non_admission_sleeve_match_count",
                "non_admission_sleeve_match_count",
            ),
        )
    )
    if non_admission_sleeve_count is None and matched_sleeve_count is not None:
        non_admission_sleeve_count = max(
            0.0,
            matched_sleeve_count - (admission_sleeve_count or 0.0),
        )
    entry_quality_fill_probability = candidate.get("fill_probability")
    if entry_quality_fill_probability in (None, ""):
        entry_quality_fill_probability = candidate.get("candidate_fill_probability")
    if entry_quality_fill_probability in (None, ""):
        entry_quality_fill_probability = candidate.get("heuristic_fill_probability")
    execution_fill_probability, execution_fill_probability_source = (
        execution_fillability_authority(candidate)
    )
    expected_net_r = candidate.get("expected_net_r")
    if expected_net_r in (None, ""):
        expected_net_r = candidate.get("candidate_expected_net_r")
    probability = candidate.get("probability")
    if probability in (None, ""):
        probability = candidate.get("candidate_probability")
    confidence = candidate.get("confidence")
    if confidence in (None, ""):
        confidence = candidate.get("candidate_confidence")
    source_completeness = candidate.get("source_completeness")
    source_completeness_status = candidate.get("source_completeness_status")
    geometry_fields = {
        key: candidate.get(key)
        for key in EXECUTABLE_GEOMETRY_FIELDS
        if candidate.get(key) not in (None, "")
    }
    cost_fields = {
        "expected_cost_r": candidate.get("expected_cost_r"),
        "cost_r": candidate.get("cost_r"),
        "broker_calibrated_expected_cost_r": candidate.get(
            "broker_calibrated_expected_cost_r"
        ),
        "broker_pretrade_cost_r": candidate.get("broker_pretrade_cost_r"),
        "candidate_cost_r_fallback_diagnostic": candidate.get(
            "candidate_cost_r_fallback_diagnostic"
        ),
        "candidate_cost_r_fallback_is_authority": candidate.get(
            "candidate_cost_r_fallback_is_authority"
        ),
        "cost_authority": candidate.get("cost_authority"),
        "execution_cost_authority": candidate.get("execution_cost_authority"),
        "pretrade_cost_packet_status": candidate.get("pretrade_cost_packet_status"),
        "pretrade_cost_refusal_reasons": candidate.get(
            "pretrade_cost_refusal_reasons"
        ),
        "cost_source_gap_status": candidate.get("cost_source_gap_status"),
        "source_gap_cost_fallback_blocked": candidate.get(
            "source_gap_cost_fallback_blocked"
        ),
        "close_side_all_in_cost_status": candidate.get(
            "close_side_all_in_cost_status"
        ),
    }
    carried_effective_source_bound_preservable = bool(
        str(cost_fields.get("pretrade_cost_packet_status") or "").strip().upper()
        == "PASSED"
        and "broker_calibrated"
        in str(
            cost_fields.get("cost_authority")
            or cost_fields.get("execution_cost_authority")
            or ""
        ).lower()
        and "source_bound" in str(cost_fields.get("cost_source_gap_status") or "").lower()
        and not _truthy(cost_fields.get("candidate_cost_r_fallback_is_authority"))
    )
    authority_fields = {
        "package_replay_authority_enabled": candidate.get(
            "package_replay_authority_enabled"
        ),
        "ultimate_candidate_package_open_reduced_risk_authority": candidate.get(
            "ultimate_candidate_package_open_reduced_risk_authority"
        ),
        "package_open_reduced_authority_allowed": candidate.get(
            "package_open_reduced_authority_allowed"
        ),
        "package_open_reduced_authority_family": candidate.get(
            "package_open_reduced_authority_family"
        ),
        "ultimate_package_open_reduced_authority_allowed": candidate.get(
            "ultimate_package_open_reduced_authority_allowed"
        ),
        "selected_scheduler_package_open_reduced_authority_allowed": candidate.get(
            "selected_scheduler_package_open_reduced_authority_allowed"
        ),
        "package_open_reduced_authority_current_config_allowed": candidate.get(
            "package_open_reduced_authority_current_config_allowed"
        ),
        "package_open_reduced_authority_config_block_reason": candidate.get(
            "package_open_reduced_authority_config_block_reason"
        ),
        "open_reduced_authority_current_config_allowed": candidate.get(
            "open_reduced_authority_current_config_allowed"
        ),
        "open_reduced_authority_config_block_reason": candidate.get(
            "open_reduced_authority_config_block_reason"
        ),
        "package_open_reduced_authority_source_boundary": candidate.get(
            "package_open_reduced_authority_source_boundary"
        ),
        "open_reduced_authority_source_boundary": candidate.get(
            "open_reduced_authority_source_boundary"
        ),
        "source_bound_package_candidate_use_allowed_reason": candidate.get(
            "source_bound_package_candidate_use_allowed_reason"
        ),
        "package_replay_authority_evidence_class": (
            candidate.get("package_replay_authority_evidence_class")
            or candidate.get("evidence_class")
        ),
        "package_replay_result_use_status": (
            candidate.get("package_replay_result_use_status")
            or candidate.get("result_use_status")
        ),
        "package_replay_score": candidate.get("package_replay_score"),
        "package_replay_source_namespace": (
            candidate.get("package_replay_source_namespace")
            or candidate.get("source_namespace")
        ),
    }
    signed_open_reduced_authority = candidate.get(
        "ultimate_candidate_package_open_reduced_risk_authority"
    )
    signed_open_reduced_authority = (
        signed_open_reduced_authority
        if isinstance(signed_open_reduced_authority, Mapping)
        else {}
    )
    selector_action = _first_non_missing(
        candidate,
        (
            "selector_action",
            "package_new_entry_authority_selector_action",
            "scheduler_materialization_selector_action",
        ),
    ) or signed_open_reduced_authority.get(
        "selector_action"
    ) or signed_open_reduced_authority.get(
        "package_new_entry_authority_selector_action"
    )
    selector_reason = _first_non_missing(
        candidate,
        (
            "selector_reason",
            "package_new_entry_authority_selector_reason",
            "scheduler_materialization_selector_reason",
        ),
    ) or signed_open_reduced_authority.get(
        "selector_reason"
    ) or signed_open_reduced_authority.get(
        "package_new_entry_authority_selector_reason"
    )
    scheduler_materialization_fields = {
        field: candidate.get(field)
        for field in (
            "scheduler_materialization_action_intent",
            "scheduler_materialization_original_action_intent",
            "scheduler_materialization_selector_action",
            "scheduler_materialization_selector_reason",
            "scheduler_materialization_skip_reason",
            "scheduler_terminal_vs_soft_guard",
            "terminal_vetoes",
            "scheduler_terminal_vetoes",
            "reallocation_soft_guard_vetoes",
            "scheduler_reallocation_soft_guard_vetoes",
            "reallocation_soft_guard_pool_eligible",
            "reallocation_soft_guard_pool_reason",
            "reallocation_soft_guard_pool_status",
            "reallocation_soft_guard_pool_terminal_vetoes",
            "action_intent",
            "lifecycle_action",
            "same_symbol_lifecycle_action",
            "gtos_vnext_same_symbol_lifecycle_action",
        )
        if candidate.get(field) not in (None, "")
    }
    upstream_non_executable_reason = str(
        candidate.get("package_replay_executable_candidate_use_allowed_reason")
        or candidate.get("selected_package_candidate_use_allowed_status")
        or ""
    ).strip()
    explicit_upstream_source_bound_false = bool(
        upstream_package_alias_present
        and not upstream_package_alias_allowed
        and upstream_non_executable_reason
        and upstream_non_executable_reason != "no_package_axis_or_candidate_use_alias"
    )
    source_bound_use_allowed = canonical_package_source_bound_candidate_use_allowed(
        candidate
    )
    diagnostic_quality_defaults: dict[str, Any] = {}
    if source_bound_use_allowed and execution_fill_probability in (None, ""):
        diagnostic_quality_defaults["diagnostic_fill_probability_default"] = (
            PACKAGE_BRIDGE_DEFAULT_FILL_PROBABILITY
        )
        diagnostic_quality_defaults["diagnostic_fill_probability_default_source"] = (
            "selected_package_bridge_package_min_fill_probability_floor"
        )
    if source_bound_use_allowed and source_completeness in (None, ""):
        diagnostic_quality_defaults["diagnostic_source_completeness_default"] = (
            PACKAGE_BRIDGE_DEFAULT_SOURCE_COMPLETENESS
        )
        diagnostic_quality_defaults["diagnostic_source_completeness_default_source"] = (
            "selected_package_bridge_missing_source_completeness_degraded_default"
        )
    candidate_instance_fields = timewarp_loop.canonical_replay_candidate_instance_fields(
        candidate
    )
    for identity_field in (
        "canonical_replay_candidate_instance_key",
        "risk_finalizer_probe_instance_key",
        "source_bound_replay_candidate_instance_key",
        "candidate_instance_identity_status",
    ):
        explicit_value = candidate.get(identity_field)
        if not _missing_value(explicit_value):
            candidate_instance_fields[identity_field] = explicit_value
    candidate_decision_quality_source_boundary = candidate.get(
        "candidate_decision_quality_source_boundary"
    ) or "selected_package_bridge_predecision_quality_alias_repair"
    source_boundary = candidate.get("source_boundary") or SOURCE_BOUND_EVIDENCE_CLASS
    package_packet = candidate.get("ultimate_candidate_package_packet")
    package_packet_hash = _first_present(
        candidate.get("ultimate_candidate_package_packet_hash_sha256"),
        package_packet.get("packet_hash_sha256")
        if isinstance(package_packet, Mapping)
        else None,
        package_packet.get("payload_hash_sha256")
        if isinstance(package_packet, Mapping)
        else None,
        stable_sha256(package_packet)
        if isinstance(package_packet, Mapping)
        else None,
    )
    package_packet_shape_hash = _first_present(
        candidate.get("ultimate_candidate_package_packet_shape_hash_sha256"),
        package_packet.get("payload_shape_hash_sha256")
        if isinstance(package_packet, Mapping)
        else None,
        stable_sha256(_packet_shape(package_packet))
        if isinstance(package_packet, Mapping)
        else None,
    )
    selected_policy_input = {
        **dict(candidate),
        "expected_net_r": expected_net_r,
        "candidate_expected_net_r": candidate.get("candidate_expected_net_r")
        if candidate.get("candidate_expected_net_r") not in (None, "")
        else expected_net_r,
        "candidate_decision_quality_source_boundary": (
            candidate_decision_quality_source_boundary
        ),
        "source_boundary": source_boundary,
    }
    selected_policy_input.update(
        owner_approved_reconstructed_proxy_selected_policy_expected_net_bridge_fields(
            selected_policy_input
        )
    )
    selected_policy_calibration = selected_policy_expected_net_calibration_fields(
        selected_policy_input
    )
    context_fields = timewarp_loop.same_symbol_replay_exposure_ledger_fields(
        candidate,
    )
    replacement_quality_fields = (
        timewarp_loop.scheduler_replacement_reallocation_quality_ledger_fields(
            candidate,
        )
    )
    direct_context_fields = {
        field: candidate.get(field)
        for field in CANONICAL_REPLAY_CONTEXT_ENVELOPE_FIELDS
        if not _missing_value(candidate.get(field))
    }
    fields = {
        "candidate_id": candidate.get("candidate_id") or candidate.get("replay_candidate_id"),
        "symbol": candidate.get("symbol"),
        "side": candidate.get("side") or candidate.get("direction"),
        "decision_time_utc": candidate.get("decision_time_utc"),
        "ultimate_candidate_package_packet_hash_sha256": package_packet_hash,
        "ultimate_candidate_package_packet_shape_hash_sha256": package_packet_shape_hash,
        "expected_net_r": expected_net_r,
        "candidate_expected_net_r": candidate.get("candidate_expected_net_r")
        if candidate.get("candidate_expected_net_r") not in (None, "")
        else expected_net_r,
        "probability": probability,
        "candidate_probability": candidate.get("candidate_probability")
        if candidate.get("candidate_probability") not in (None, "")
        else probability,
        "confidence": confidence,
        "candidate_confidence": candidate.get("candidate_confidence")
        if candidate.get("candidate_confidence") not in (None, "")
        else confidence,
        "fill_probability": entry_quality_fill_probability,
        "entry_quality_fill_probability": entry_quality_fill_probability,
        "candidate_fill_probability": candidate.get("candidate_fill_probability")
        if candidate.get("candidate_fill_probability") not in (None, "")
        else entry_quality_fill_probability,
        "limit_fillability_probability": execution_fill_probability,
        "predecision_limit_fillability_probability": execution_fill_probability,
        "execution_fill_probability": execution_fill_probability,
        "execution_fill_probability_source": execution_fill_probability_source,
        "execution_fill_probability_source_time_utc": candidate.get(
            "execution_fill_probability_source_time_utc"
        ),
        "execution_fill_probability_source_boundary": candidate.get(
            "execution_fill_probability_source_boundary"
        ),
        "execution_fill_probability_authority_class": candidate.get(
            "execution_fill_probability_authority_class"
        ),
        "execution_fill_probability_authority_hash_sha256": candidate.get(
            "execution_fill_probability_authority_hash_sha256"
        ),
        "source_completeness": source_completeness,
        "source_completeness_status": source_completeness_status,
        "candidate_decision_quality_field_sources": candidate.get(
            "candidate_decision_quality_field_sources"
        ),
        "candidate_decision_quality_alias_status": candidate.get(
            "candidate_decision_quality_alias_status"
        ),
        "candidate_decision_quality_alias_mismatches": candidate.get(
            "candidate_decision_quality_alias_mismatches"
        ),
        "candidate_decision_quality_provenance_failures": candidate.get(
            "candidate_decision_quality_provenance_failures"
        ),
        "candidate_decision_quality_source_boundary": (
            candidate_decision_quality_source_boundary
        ),
        **selected_policy_calibration,
        "source_boundary": source_boundary,
        **candidate_instance_fields,
        **direct_context_fields,
        **{
            key: value
            for key, value in context_fields.items()
            if value not in (None, "")
        },
        **{
            key: value
            for key, value in replacement_quality_fields.items()
            if value not in (None, "")
        },
        "selector_action": selector_action,
        "selector_reason": selector_reason,
        **geometry_fields,
        **{
            key: value
            for key, value in authority_fields.items()
            if value not in (None, "")
        },
        **{key: value for key, value in cost_fields.items() if value not in (None, "")},
        **scheduler_materialization_fields,
        "upstream_package_source_bound_candidate_use_allowed": upstream_package_alias_allowed,
        "upstream_package_source_bound_candidate_use_alias_present": (
            upstream_package_alias_present
        ),
        "upstream_package_explicit_source_bound_false": (
            explicit_upstream_source_bound_false
        ),
        "selected_package_member_axis_authority_bound": bridge_member_axis_authority_bound,
        "selected_package_bridge_source_bound_candidate_use_allowed": bridge_member_axis_authority_bound,
        "selected_package_bridge_admission_candidate_use_allowed": (
            bridge_member_axis_authority_bound and effective_admission_count > 0
        ),
        "package_source_bound_admission_diagnostic": source_bound_use_allowed,
        "source_bound_package_candidate_use_allowed": source_bound_use_allowed,
        "ultimate_package_source_bound_candidate_use_allowed": source_bound_use_allowed,
        "ultimate_package_effective_source_bound_candidate_use_allowed": (
            source_bound_use_allowed
        ),
        "ultimate_package_admission_candidate_use_allowed": source_bound_use_allowed
        and effective_admission_count > 0,
        "ultimate_package_effective_admission_count": effective_admission_count,
        "ultimate_package_decision_status": candidate.get("ultimate_package_decision_status"),
        "ultimate_package_role_disposition": _first_non_missing(
            candidate,
            (
                "ultimate_package_role_disposition",
                "role_disposition",
            ),
        ),
        "role_disposition": _first_non_missing(
            candidate,
            (
                "ultimate_package_role_disposition",
                "role_disposition",
            ),
        ),
        "ultimate_package_matched_sleeve_ids": matched_sleeve_ids,
        "matched_sleeve_ids": matched_sleeve_ids,
        "ultimate_package_matched_sleeve_count": matched_sleeve_count,
        "matched_sleeve_count": matched_sleeve_count,
        "ultimate_package_admission_sleeve_match_count": admission_sleeve_count,
        "admission_sleeve_match_count": admission_sleeve_count,
        "ultimate_package_non_admission_sleeve_match_count": non_admission_sleeve_count,
        "non_admission_sleeve_match_count": non_admission_sleeve_count,
        "ultimate_package_selector_shadow_score": candidate.get(
            "ultimate_package_selector_shadow_score"
        ),
        "ultimate_package_combined_source_bound_signal_r_sum": candidate.get(
            "ultimate_package_combined_source_bound_signal_r_sum"
        ),
        "ultimate_package_max_combined_source_bound_signal_r": candidate.get(
            "ultimate_package_max_combined_source_bound_signal_r"
        ),
        "ultimate_package_source_bound_r_additive_allowed": False,
        "ultimate_package_source_bound_r_additive_unit": (
            "matched_sleeve_signal_not_candidate_trace"
        ),
        "ultimate_package_source_bound_r_additive_scope": (
            "unique_source_bound_surface_claim"
        ),
        "ultimate_package_scheduler_parity_evidence_class": candidate.get(
            "ultimate_package_scheduler_parity_evidence_class"
        ),
        **diagnostic_quality_defaults,
    }
    if matched_member_rows or matched_axis_ids:
        fields.update(
            {
                "ultimate_package_matched_member_axis_count": (
                    len(matched_member_rows)
                    if matched_member_rows
                    else _safe_float_or_none(
                        candidate.get("ultimate_package_matched_member_axis_count")
                    )
                    or len(matched_axis_ids)
                ),
                "ultimate_package_admission_member_axis_match_count": admission_count,
                "ultimate_package_matched_member_axis_role_counts": dict(
                    sorted(role_counts.items())
                ),
                "ultimate_package_member_axis_source_bound_signal_r_sum": source_r_sum,
                "ultimate_package_member_axis_max_source_bound_signal_r": source_r_max,
                "ultimate_package_member_axis_source_bound_r_additive_allowed": False,
                "ultimate_package_member_axis_source_bound_r_additive_unit": (
                    "source_member_axis_not_candidate_trace"
                ),
                "ultimate_package_member_axis_source_bound_r_additive_scope": (
                    "unique_stable_member_axis_id"
                ),
                "ultimate_package_matched_member_axis_ids": matched_axis_ids,
                "selected_package_matched_member_axis_ids": matched_axis_ids,
                "ultimate_package_member_axis_evidence_class": (
                    "source_member_axis_overlap_not_additive_exact_execution_r"
                    if matched_member_rows
                    else candidate.get("ultimate_package_member_axis_evidence_class")
                    or "candidate_carried_source_member_axis_overlap_fallback"
                ),
            }
        )
    else:
        fields.update(
            {
                "ultimate_package_matched_member_axis_count": 0,
                "ultimate_package_admission_member_axis_match_count": 0,
                "ultimate_package_matched_member_axis_role_counts": {},
                "ultimate_package_member_axis_source_bound_signal_r_sum": 0.0,
                "ultimate_package_member_axis_max_source_bound_signal_r": 0.0,
                "ultimate_package_member_axis_source_bound_r_additive_allowed": False,
                "ultimate_package_member_axis_source_bound_r_additive_unit": (
                    "source_member_axis_not_candidate_trace"
                ),
                "ultimate_package_member_axis_source_bound_r_additive_scope": (
                    "unique_stable_member_axis_id"
                ),
                "ultimate_package_matched_member_axis_ids": [],
                "selected_package_matched_member_axis_ids": [],
                "ultimate_package_member_axis_evidence_class": (
                    "no_current_bridge_member_axis_match"
                ),
            }
        )
    effective_fields = timewarp_loop.ultimate_package_effective_signal_fields(
        {**dict(candidate), **fields}
    )
    fields.update(effective_fields)
    if (
        _truthy(candidate.get("ultimate_package_effective_source_bound_candidate_use_allowed"))
        and source_bound_use_allowed
        and effective_admission_count > 0
        and carried_effective_source_bound_preservable
    ):
        prior_effective_matched_count = _safe_float_or_none(
            candidate.get("ultimate_package_effective_matched_count")
        )
        effective_matched_count = max(
            _safe_float_or_none(fields.get("ultimate_package_effective_matched_count"))
            or 0.0,
            prior_effective_matched_count or 0.0,
            _safe_float_or_none(matched_sleeve_count) or 0.0,
            effective_admission_count,
        )
        fields["ultimate_package_effective_matched_count"] = effective_matched_count
        fields["ultimate_package_effective_source_bound_candidate_use_allowed"] = True
        fields["ultimate_package_effective_evidence_source"] = (
            fields.get("ultimate_package_effective_evidence_source")
            or "candidate_carried_effective_source_bound_authority"
        )
    authority_action_intent = normalize_bridge_action_intent(
        candidate.get("scheduler_materialization_action_intent")
        or candidate.get("action_intent")
        or candidate.get("lifecycle_action")
        or "new_position"
    ) or "new_position"
    lightweight_trusted_existing_authority = (
        trusted_signed_package_new_entry_authority_surface(
            candidate,
            action_intent=authority_action_intent,
        )
    )
    existing_full_validation = bridge_reduced_package_new_entry_authority_validation(
        candidate,
        selector_action=str(selector_action or ""),
        selector_reason=str(selector_reason or ""),
        action_intent=authority_action_intent,
    )
    trusted_existing_authority = bool(
        lightweight_trusted_existing_authority
        and (
            existing_full_validation.get("required") is not True
            or existing_full_validation.get("valid") is True
        )
    )
    if trusted_existing_authority:
        signed_payload = candidate.get("package_new_entry_authority_payload")
        signed_payload = signed_payload if isinstance(signed_payload, Mapping) else {}
        for authority_field in PACKAGE_AUTHORITY_FIELDS:
            value = candidate.get(authority_field)
            if authority_field in PACKAGE_AUTHORITY_EMPTY_LIST_FIELDS:
                missing = value in (None, "", {})
            else:
                missing = _missing_value(value)
            if not missing:
                fields[authority_field] = copy.deepcopy(value)
        for current_field in SIGNED_PACKAGE_AUTHORITY_CURRENT_DECISION_FIELDS:
            if current_field not in signed_payload:
                continue
            value = signed_payload.get(current_field)
            if value is not None and value != "":
                fields[current_field] = copy.deepcopy(value)
        authority_materialization_row = {**dict(candidate), **fields}
        _project_final_signed_fillability(authority_materialization_row)
    else:
        private_materialization_input = {**dict(candidate), **fields}
        for private_field in (
            "fill_probability",
            "candidate_fill_probability",
            "predecision_limit_fillability",
            "pending_limit_fillability_probability",
            "pending_fill_probability",
            "predecision_limit_fillability_probability",
            "limit_fillability_probability",
            "limit_fill_probability",
            "execution_fill_probability",
            "execution_fill_probability_source",
            "execution_fill_probability_source_boundary",
            "execution_fill_probability_source_time_utc",
            "predecision_limit_fillability_source_boundary",
            "predecision_limit_fillability_source_time_utc",
            "predecision_current_price_source_boundary",
            "predecision_current_price_source_time_utc",
            "current_price_source_boundary",
            "current_price_source_time_utc",
        ):
            candidate_value = candidate.get(private_field)
            if not _missing_value(candidate_value):
                private_materialization_input[private_field] = copy.deepcopy(
                    candidate_value
                )
        authority_materialization_row = _bridge_materialize_signed_reduced_authority(
            private_materialization_input,
            selector_action=str(selector_action or ""),
            selector_reason=str(selector_reason or ""),
            action_intent=authority_action_intent,
        )
    for authority_field in (
        *PACKAGE_AUTHORITY_FIELDS,
        "ultimate_candidate_package_open_reduced_risk_authority",
        "ultimate_candidate_package_reduce_risk_authority",
        "ultimate_candidate_package_reduced_risk_authority",
    ):
        value = authority_materialization_row.get(authority_field)
        if authority_field in PACKAGE_AUTHORITY_EMPTY_LIST_FIELDS:
            missing = value in (None, "", {})
        else:
            missing = _missing_value(value)
        if not missing:
            fields[authority_field] = value
    final_projection_row = {**dict(candidate), **fields}
    if _project_final_signed_fillability(final_projection_row):
        for projection_field in (
            "fill_probability",
            "candidate_fill_probability",
            "entry_quality_fill_probability",
            "execution_fill_probability",
            "execution_fill_probability_source",
            "execution_fill_probability_source_time_utc",
            "execution_fill_probability_source_boundary",
            "execution_fill_probability_authority_class",
            "execution_fill_probability_authority_hash_sha256",
            "limit_fillability_probability",
            "predecision_limit_fillability_probability",
            "predecision_limit_fillability",
            "candidate_decision_quality_field_sources",
            "execution_fillability_projection_status",
        ):
            fields[projection_field] = copy.deepcopy(
                final_projection_row.get(projection_field)
            )
        entry_quality_fill_probability = fields.get(
            "entry_quality_fill_probability"
        )
        execution_fill_probability = fields.get("execution_fill_probability")
        execution_fill_probability_source = fields.get(
            "execution_fill_probability_source"
        )
    executable_package_allowed, executable_package_reason = executable_package_use_detail(
        {**dict(candidate), **fields},
        source_bound_allowed=source_bound_use_allowed,
    )
    executable_package_reason = (
        candidate.get("package_replay_executable_candidate_use_allowed_reason")
        if not source_bound_use_allowed
        and not _missing_value(
            candidate.get("package_replay_executable_candidate_use_allowed_reason")
        )
        else executable_package_reason
    )
    replay_candidate_use_allowed_now_reason = (
        candidate.get("replay_candidate_use_allowed_now_reason")
        if not source_bound_use_allowed
        and not _missing_value(candidate.get("replay_candidate_use_allowed_now_reason"))
        else executable_package_reason
    )
    selected_package_candidate_use_allowed_status = (
        candidate.get("selected_package_candidate_use_allowed_status")
        if not source_bound_use_allowed
        and not _missing_value(
            candidate.get("selected_package_candidate_use_allowed_status")
        )
        else executable_package_reason
    )
    fields.update(
        {
            "source_bound_package_candidate_use_allowed": source_bound_use_allowed,
            "ultimate_package_source_bound_candidate_use_allowed": (
                source_bound_use_allowed
            ),
            "ultimate_package_admission_candidate_use_allowed": (
                source_bound_use_allowed and effective_admission_count > 0
            ),
            "package_replay_source_bound_candidate_use_allowed": (
                source_bound_use_allowed
            ),
            "package_replay_candidate_use_allowed": executable_package_allowed,
            "package_replay_executable_candidate_use_allowed": (
                executable_package_allowed
            ),
            "package_replay_executable_candidate_use_allowed_reason": (
                executable_package_reason
            ),
            "replay_candidate_use_allowed_now": executable_package_allowed,
            "replay_candidate_use_allowed_now_reason": (
                replay_candidate_use_allowed_now_reason
            ),
            "selected_package_candidate_use_allowed_status": (
                selected_package_candidate_use_allowed_status
            ),
        }
    )
    fields.update(
        package_authority_bridge_fields(
            {**dict(candidate), **fields},
            source_bound_allowed=source_bound_use_allowed,
        )
    )
    effective_fields = timewarp_loop.ultimate_package_effective_signal_fields(
        {**dict(candidate), **fields}
    )
    fields.update(effective_fields)
    if (
        _truthy(candidate.get("ultimate_package_effective_source_bound_candidate_use_allowed"))
        and source_bound_use_allowed
        and effective_admission_count > 0
        and carried_effective_source_bound_preservable
    ):
        fields["ultimate_package_effective_matched_count"] = max(
            _safe_float_or_none(fields.get("ultimate_package_effective_matched_count"))
            or 0.0,
            _safe_float_or_none(candidate.get("ultimate_package_effective_matched_count"))
            or 0.0,
            _safe_float_or_none(matched_sleeve_count) or 0.0,
            effective_admission_count,
        )
        fields["ultimate_package_effective_source_bound_candidate_use_allowed"] = True
        fields["ultimate_package_effective_evidence_source"] = (
            fields.get("ultimate_package_effective_evidence_source")
            or "candidate_carried_effective_source_bound_authority"
        )
    if not executable_package_allowed:
        _demote_non_executable_source_bound_r_fields(
            fields,
            reason=executable_package_reason,
            clear_effective_candidate_use=False,
        )
        fields.setdefault(
            "diagnostic_ultimate_package_effective_source_bound_signal_r",
            fields.get("ultimate_package_effective_source_bound_signal_r")
        )
        fields.setdefault(
            "diagnostic_ultimate_package_effective_source_bound_candidate_use_allowed",
            fields.get("ultimate_package_effective_source_bound_candidate_use_allowed")
        )
        fields["ultimate_package_effective_source_bound_non_executable"] = True
        fields["ultimate_package_effective_source_bound_non_executable_reason"] = (
            executable_package_reason
        )
        fields["ultimate_package_effective_executable_authority_allowed"] = False
        fields["ultimate_package_effective_executable_authority_reason"] = (
            executable_package_reason
        )
        _enforce_non_executable_source_bound_diagnostic(
            fields,
            reason=executable_package_reason,
        )
    else:
        fields["ultimate_package_effective_source_bound_non_executable"] = False
        fields["ultimate_package_effective_executable_authority_allowed"] = True
        fields["ultimate_package_effective_executable_authority_reason"] = (
            executable_package_reason
        )
    _backfill_source_bound_diagnostic_contract(fields)
    quality_envelope = candidate_decision_quality_envelope({**dict(candidate), **fields})
    quality_envelope["fill_probability"] = entry_quality_fill_probability
    quality_envelope["candidate_fill_probability"] = entry_quality_fill_probability
    quality_envelope["execution_fill_probability"] = execution_fill_probability
    quality_envelope["execution_fill_probability_source"] = (
        execution_fill_probability_source
    )
    quality_envelope["execution_fill_probability_source_time_utc"] = fields.get(
        "execution_fill_probability_source_time_utc"
    )
    quality_envelope["execution_fill_probability_source_boundary"] = fields.get(
        "execution_fill_probability_source_boundary"
    )
    quality_envelope["execution_fill_probability_authority_class"] = fields.get(
        "execution_fill_probability_authority_class"
    )
    quality_envelope[
        "execution_fill_probability_authority_hash_sha256"
    ] = fields.get("execution_fill_probability_authority_hash_sha256")
    quality_envelope["entry_quality_fill_probability"] = entry_quality_fill_probability
    quality_envelope["limit_fillability_probability"] = execution_fill_probability
    quality_envelope["predecision_limit_fillability_probability"] = (
        execution_fill_probability
    )
    quality_envelope["candidate_decision_quality_field_sources"] = copy.deepcopy(
        fields.get("candidate_decision_quality_field_sources") or {}
    )
    fields["candidate_decision_quality"] = quality_envelope
    return fields


def _packet_shape(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _packet_shape(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_packet_shape(item) for item in value]
    if value is None:
        return None
    return type(value).__name__


def _package_packet_from_surfaces(*surfaces: Mapping[str, Any] | None) -> Any:
    for surface in surfaces:
        if not isinstance(surface, Mapping):
            continue
        packet = surface.get("ultimate_candidate_package_packet")
        if isinstance(packet, Mapping) or (
            isinstance(packet, Sequence)
            and not isinstance(packet, (str, bytes, bytearray))
        ):
            return packet
    return None


def _bridge_materialized_package_packet_contract(
    row: Mapping[str, Any],
    *,
    source_bound_allowed: bool | None,
) -> dict[str, Any]:
    authority_contract = {
        field: row.get(field)
        for field in PACKAGE_AUTHORITY_FIELDS
        if not _missing_value(row.get(field))
    }
    quality_contract = candidate_decision_quality_envelope(row)
    matched_axis_ids = stable_unique(
        list_values(row.get("ultimate_package_matched_member_axis_ids"))
        + list_values(row.get("matched_stable_member_axis_ids"))
    )
    matched_sleeve_ids = stable_unique(
        list_values(row.get("ultimate_package_matched_sleeve_ids"))
        + list_values(row.get("matched_sleeve_ids"))
    )
    context_contract = {
        field: row.get(field)
        for field in CANONICAL_REPLAY_CONTEXT_ENVELOPE_FIELDS
        if not _missing_value(row.get(field))
    }
    return {
        "schema": "gtos.final_moonshot.ultimate_candidate_package.bridge_materialized_packet.v1",
        "source_boundary": "predecision_selected_package_bridge_packet_materialization_no_outcome_fields",
        "source_bound_allowed": bool(source_bound_allowed),
        "candidate_id": row.get("candidate_id") or row.get("selected_candidate_id"),
        "decision_time_utc": row.get("decision_time_utc")
        or row.get("candle_close_utc")
        or row.get("source_candle_time_utc"),
        "canonical_replay_candidate_instance_key": row.get(
            "canonical_replay_candidate_instance_key"
        ),
        "risk_finalizer_probe_instance_key": row.get(
            "risk_finalizer_probe_instance_key"
        ),
        "source_bound_replay_candidate_instance_key": row.get(
            "source_bound_replay_candidate_instance_key"
        ),
        "candidate_instance_identity_status": row.get(
            "candidate_instance_identity_status"
        ),
        "symbol": row.get("symbol"),
        "side": row.get("side") or row.get("direction"),
        "timeframe": row.get("timeframe")
        or row.get("market_timeframe")
        or row.get("decision_timeframe"),
        "session_bucket": row.get("session_bucket")
        or row.get("session")
        or row.get("route_session"),
        "canonical_replay_context": context_contract,
        "selector_action": row.get("selector_action"),
        "selector_reason": row.get("selector_reason"),
        "scheduler_materialization_action_intent": row.get(
            "scheduler_materialization_action_intent"
        )
        or row.get("action_intent")
        or row.get("lifecycle_action"),
        "pretrade_cost_packet_status": row.get("pretrade_cost_packet_status"),
        "cost_authority": row.get("cost_authority")
        or row.get("execution_cost_authority"),
        "cost_source_gap_status": row.get("cost_source_gap_status"),
        "candidate_decision_quality": quality_contract,
        "package_authority": authority_contract,
        "matched_sleeve_ids": matched_sleeve_ids,
        "matched_member_axis_ids": matched_axis_ids,
        "ultimate_package_effective_admission_count": row.get(
            "ultimate_package_effective_admission_count"
        ),
        "ultimate_package_effective_source_bound_candidate_use_allowed": row.get(
            "ultimate_package_effective_source_bound_candidate_use_allowed"
        ),
        "package_replay_candidate_use_allowed": row.get(
            "package_replay_candidate_use_allowed"
        ),
        "package_replay_executable_candidate_use_allowed": row.get(
            "package_replay_executable_candidate_use_allowed"
        ),
        "package_replay_executable_candidate_use_allowed_reason": row.get(
            "package_replay_executable_candidate_use_allowed_reason"
        ),
    }


def flatten_package_bridge_contract_fields(
    row: dict[str, Any],
    *surfaces: Mapping[str, Any] | None,
    source_bound_allowed: bool | None = None,
) -> None:
    """Expose nested package packet and signed-authority contracts on bridge rows."""

    for field in (
        "ultimate_candidate_package_packet_hash_sha256",
        "ultimate_candidate_package_packet_shape_hash_sha256",
    ):
        if not _missing_value(row.get(field)):
            continue
        value = _first_present(
            *(surface.get(field) for surface in surfaces if isinstance(surface, Mapping))
        )
        if not _missing_value(value):
            row[field] = value
    package_packet = _package_packet_from_surfaces(row, *surfaces)
    if isinstance(package_packet, Mapping) or (
        isinstance(package_packet, Sequence)
        and not isinstance(package_packet, (str, bytes, bytearray))
    ):
        if _missing_value(row.get("ultimate_candidate_package_packet_hash_sha256")):
            row["ultimate_candidate_package_packet_hash_sha256"] = _first_present(
                package_packet.get("packet_hash_sha256")
                if isinstance(package_packet, Mapping)
                else None,
                package_packet.get("payload_hash_sha256")
                if isinstance(package_packet, Mapping)
                else None,
                stable_sha256(package_packet),
            )
        if _missing_value(row.get("ultimate_candidate_package_packet_shape_hash_sha256")):
            row["ultimate_candidate_package_packet_shape_hash_sha256"] = _first_present(
                package_packet.get("payload_shape_hash_sha256")
                if isinstance(package_packet, Mapping)
                else None,
                stable_sha256(_packet_shape(package_packet)),
            )
    if (
        _missing_value(row.get("ultimate_candidate_package_packet_hash_sha256"))
        or _missing_value(row.get("ultimate_candidate_package_packet_shape_hash_sha256"))
    ):
        materialized_packet = _bridge_materialized_package_packet_contract(
            row,
            source_bound_allowed=source_bound_allowed,
        )
        if _missing_value(row.get("ultimate_candidate_package_packet_hash_sha256")):
            row["ultimate_candidate_package_packet_hash_sha256"] = stable_sha256(
                materialized_packet
            )
        if _missing_value(row.get("ultimate_candidate_package_packet_shape_hash_sha256")):
            row["ultimate_candidate_package_packet_shape_hash_sha256"] = stable_sha256(
                _packet_shape(materialized_packet)
            )
        row["ultimate_candidate_package_packet_materialization_status"] = (
            "bridge_materialized_predecision_contract_packet"
        )
        row["ultimate_candidate_package_packet_materialization_source_boundary"] = (
            materialized_packet["source_boundary"]
        )
    authority_fields = package_authority_bridge_fields(
        row,
        source_bound_allowed=source_bound_allowed,
    )
    _promote_trusted_package_authority_fields(row, authority_fields)


def finalize_bridge_package_authority_contract(
    row: dict[str, Any],
    *,
    source_bound_allowed: bool | None,
) -> None:
    """Bind package authority fields to the canonical row instance before writing."""

    identity_fields = timewarp_loop.canonical_replay_candidate_instance_fields(
        row,
        decision_time_utc=(
            row.get("decision_time_utc")
            or row.get("candle_close_utc")
            or row.get("source_candle_time_utc")
        ),
    )
    for identity_field, identity_value in identity_fields.items():
        if _missing_value(row.get(identity_field)) and not _missing_value(identity_value):
            row[identity_field] = identity_value
    authority_fields = package_authority_bridge_fields(
        row,
        source_bound_allowed=source_bound_allowed,
    )
    for field in PACKAGE_AUTHORITY_FIELDS:
        value = authority_fields.get(field)
        if field in PACKAGE_AUTHORITY_EMPTY_LIST_FIELDS:
            missing = value in (None, "", {})
        else:
            missing = _missing_value(value)
        if not missing:
            row[field] = value
    _promote_trusted_package_authority_fields(row, authority_fields)
    flatten_package_bridge_contract_fields(
        row,
        source_bound_allowed=source_bound_allowed,
    )


def compact_candidate_rows(
    candidates: Iterable[Mapping[str, Any]],
    bridge_rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    bridge_by_identity: dict[tuple[str, str], Mapping[str, Any]] = {}
    bridge_by_candidate_id: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in bridge_rows:
        candidate_id = str(row.get("replay_candidate_id") or "")
        if not candidate_id:
            continue
        stable_window = str(row.get("stable_decision_window_id") or "")
        if stable_window:
            bridge_by_identity[(candidate_id, stable_window)] = row
        bridge_by_candidate_id[candidate_id].append(row)
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate = hydrate_candidate_quality_aliases(candidate)
        candidate_id = str(candidate.get("candidate_id") or "")
        stable_window = decision_window_id(
            candidate.get("symbol"),
            candidate.get("side") or candidate.get("direction"),
            candidate.get("decision_time_utc"),
        )
        bridge_join_key = ""
        bridge_join_status = "selected_package_bridge_not_joined"
        bridge = bridge_by_identity.get((candidate_id, stable_window or ""))
        if bridge is not None:
            bridge_join_key = f"{candidate_id}@@{stable_window}"
            bridge_join_status = "exact_candidate_window_join"
        elif not stable_window:
            bridge = {}
            bridge_join_status = "selected_package_bridge_window_missing"
        else:
            bridge = {}
            bridge_join_status = "selected_package_bridge_exact_missing"
        matched_axis_ids = stable_unique(
            list_values(candidate.get("ultimate_package_matched_member_axis_ids"))
            + list_values(bridge.get("matched_stable_member_axis_ids"))
        )
        row = {
            "schema": (
                "gtos.final_moonshot.denominator_to_deployment."
                "selected_package_replay_bridge.compact_candidate.v1"
            ),
            "compact_candidate_schema_version": 2,
            "route_id": "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20",
            "source_operation": "route_local_replay_from_optimized_source_materializer",
            "selected_package_bridge_join_status": bridge_join_status,
            "selected_package_bridge_join_key": bridge_join_key or None,
            "broker_mutation": False,
            "paid_api_call": False,
            "remote_push": False,
            "selected_package_replay_row": bool(
                bridge.get("selected_package_replay_row") or matched_axis_ids
            ),
            "selected_package_denominator_use_allowed": bool(
                bridge.get("selected_package_denominator_use_allowed")
            ),
            "stable_decision_window_label_match": bool(
                bridge.get("stable_decision_window_label_match")
            ),
            "exact_candidate_id_label_match": bool(
                bridge.get("exact_candidate_id_label_match")
            ),
            "label_window_match_count": int(bridge.get("label_window_match_count") or 0),
            "lifecycle_label_context_row_count": int(
                bridge.get("lifecycle_label_context_row_count") or 0
            ),
            "lifecycle_label_context_present": bool(
                bridge.get("lifecycle_label_context_present")
            ),
            "pending_lifecycle_v4_state_group": bridge.get(
                "pending_lifecycle_v4_state_group"
            ),
            "pending_lifecycle_v4_state_groups": list(
                bridge.get("pending_lifecycle_v4_state_groups") or []
            ),
            "fillability_label_family": bridge.get("fillability_label_family"),
            "fillability_label_families": list(
                bridge.get("fillability_label_families") or []
            ),
            "fill_no_fill_label": bridge.get("fill_no_fill_label"),
            "fill_no_fill_labels": list(bridge.get("fill_no_fill_labels") or []),
            "member_axis_match_count": int(bridge.get("member_axis_match_count") or 0),
            "matched_source_axis_row_indexes": list(
                bridge.get("matched_source_axis_row_indexes") or []
            ),
            "matched_stable_member_axis_ids": matched_axis_ids,
            "ultimate_package_matched_member_axis_ids": matched_axis_ids,
            "selected_package_matched_member_axis_ids": matched_axis_ids,
            "source_truth_scope": bridge.get("source_truth_scope") or SOURCE_TRUTH_SCOPE,
            "training_use_allowed": False,
            "final_package_selection_allowed": False,
        }
        recomputed_quality = selected_package_bridge_quality_fields(
            candidate,
            matched_stable_member_axis_ids=matched_axis_ids,
        )
        quality_candidates = (
            bridge,
            recomputed_quality,
            candidate,
        )
        for field in COMPACT_CANDIDATE_FIELDS:
            if field in row:
                continue
            for quality_source in quality_candidates:
                value = quality_source.get(field)
                if not _missing_value(value):
                    row[field] = value
                    break
        if _missing_value(row.get("candidate_fill_probability")):
            for quality_source in (
                candidate,
                recomputed_quality,
                bridge,
            ):
                diagnostic_fill_probability = _first_non_missing(
                    quality_source,
                    (
                        "entry_quality_fill_probability",
                        "candidate_fill_probability",
                        "fill_probability",
                        "heuristic_fill_probability",
                    ),
                )
                if not _missing_value(diagnostic_fill_probability):
                    row["candidate_fill_probability"] = diagnostic_fill_probability
                    break
        if _missing_value(row.get("selector_action_origin")):
            row["selector_action_origin"] = _first_non_missing(
                candidate,
                (
                    "selector_action_origin",
                    "scheduler_materialization_original_selector_action",
                    "original_position_selector_action",
                    "selector_action",
                ),
            ) or row.get("selector_action")
        if _missing_value(row.get("effective_selector_action")):
            row["effective_selector_action"] = _first_non_missing(
                candidate,
                (
                    "effective_selector_action",
                    "materialized_package_new_entry_authority_selector_action",
                    "scheduler_materialization_effective_selector_action",
                    "selector_action",
                ),
            ) or row.get("selector_action")
        _backfill_stop_hazard_projection(
            row,
            bridge,
            recomputed_quality,
            candidate,
        )
        _backfill_package_order_executable_authority(
            row,
            bridge,
            recomputed_quality,
            candidate,
        )
        identity_fields = timewarp_loop.canonical_replay_candidate_instance_fields(
            row,
            decision_time_utc=(
                row.get("decision_time_utc")
                or candidate.get("decision_time_utc")
                or row.get("candle_close_utc")
                or candidate.get("candle_close_utc")
                or row.get("source_candle_time_utc")
                or candidate.get("source_candle_time_utc")
            ),
        )
        for identity_field, identity_value in identity_fields.items():
            if _missing_value(row.get(identity_field)) and not _missing_value(
                identity_value
            ):
                row[identity_field] = identity_value
        source_bound_candidate_use_allowed = (
            canonical_package_source_bound_candidate_use_allowed(row)
        )
        row["selected_package_bridge_source_bound_candidate_use_allowed"] = bool(
            matched_axis_ids
        )
        if source_bound_candidate_use_allowed:
            row.setdefault("package_source_bound_admission_diagnostic", True)
            executable_package_allowed, executable_package_reason = (
                executable_package_use_detail(
                    row,
                    source_bound_allowed=True,
                )
            )
            row["source_bound_package_candidate_use_allowed"] = True
            row["ultimate_package_source_bound_candidate_use_allowed"] = True
            row["package_replay_source_bound_candidate_use_allowed"] = (
                True
            )
            row["package_replay_executable_candidate_use_allowed"] = executable_package_allowed
            row["package_replay_executable_candidate_use_allowed_reason"] = executable_package_reason
            row["replay_candidate_use_allowed_now"] = executable_package_allowed
            row["replay_candidate_use_allowed_now_reason"] = executable_package_reason
            if _missing_value(row.get("selected_package_candidate_use_allowed_status")):
                row["selected_package_candidate_use_allowed_status"] = executable_package_reason
            row.update(package_authority_bridge_fields(row, source_bound_allowed=True))
            flatten_package_bridge_contract_fields(
                row,
                candidate,
                bridge,
                source_bound_allowed=True,
            )
        else:
            if _missing_value(row.get("package_source_bound_admission_diagnostic")):
                row["package_source_bound_admission_diagnostic"] = False
            if _missing_value(row.get("source_bound_package_candidate_use_allowed")):
                row["source_bound_package_candidate_use_allowed"] = False
            if _missing_value(row.get("ultimate_package_source_bound_candidate_use_allowed")):
                row["ultimate_package_source_bound_candidate_use_allowed"] = False
            if _missing_value(row.get("package_replay_candidate_use_allowed")):
                row["package_replay_candidate_use_allowed"] = False
            if _missing_value(row.get("package_replay_source_bound_candidate_use_allowed")):
                row["package_replay_source_bound_candidate_use_allowed"] = False
            if _missing_value(row.get("package_replay_executable_candidate_use_allowed")):
                row["package_replay_executable_candidate_use_allowed"] = False
            if _missing_value(row.get("package_replay_executable_candidate_use_allowed_reason")):
                row["package_replay_executable_candidate_use_allowed_reason"] = (
                    "no_package_axis_or_candidate_use_alias"
                )
            if _missing_value(row.get("replay_candidate_use_allowed_now")):
                row["replay_candidate_use_allowed_now"] = False
            if _missing_value(row.get("replay_candidate_use_allowed_now_reason")):
                row["replay_candidate_use_allowed_now_reason"] = (
                    "no_package_axis_or_candidate_use_alias"
                )
            if _missing_value(row.get("selected_package_candidate_use_allowed_status")):
                row["selected_package_candidate_use_allowed_status"] = (
                    "no_package_axis_or_candidate_use_alias"
                )
            row.update(package_authority_bridge_fields(row, source_bound_allowed=False))
            flatten_package_bridge_contract_fields(
                row,
                candidate,
                bridge,
                source_bound_allowed=False,
            )
        if not row.get("candidate_id"):
            row["candidate_id"] = candidate_id
        if bridge.get("stable_decision_window_id"):
            row["stable_decision_window_id"] = bridge.get("stable_decision_window_id")
        elif stable_window:
            row["stable_decision_window_id"] = stable_window
        normalize_window_selected_candidate_identity(row)
        _backfill_package_root_aliases(row)
        row.setdefault("candidate_decision_quality_alias_mismatches", [])
        row.setdefault("candidate_decision_quality_provenance_failures", [])
        row.setdefault(
            "package_new_entry_authority_candidate_decision_quality_alias_mismatches",
            [],
        )
        row.setdefault(
            "package_new_entry_authority_candidate_decision_quality_provenance_failures",
            [],
        )
        row["candidate_decision_quality"] = candidate_decision_quality_envelope(row)
        finalize_bridge_package_authority_contract(
            row,
            source_bound_allowed=source_bound_candidate_use_allowed,
        )
        _enforce_non_executable_source_bound_diagnostic(row)
        _backfill_source_bound_diagnostic_contract(row)
        rows.append(row)
    return rows


def build_denominator_bridge(
    *,
    candidates: list[dict[str, Any]],
    members: list[dict[str, Any]],
    labels: list[dict[str, Any]],
    decision_time_source: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    member_by_key: defaultdict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    member_by_stable_axis_id: dict[str, dict[str, Any]] = {}
    for member in members:
        for key in member_keys(member):
            member_by_key[key].append(member)
        stable_axis_id = stable_member_axis_id(member)
        if stable_axis_id:
            member_by_stable_axis_id[stable_axis_id] = member
    labels_by_window: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for label in labels:
        if decision_time_source == "pending-created-labels":
            pending_floor = floor_to_m15_iso(label.get("pending_created_time_utc"))
            window = decision_window_id(label.get("symbol"), label.get("side"), pending_floor)
        else:
            window = decision_window_id(label.get("symbol"), label.get("side"), label.get("decision_time_utc"))
        if window:
            labels_by_window[window].append(label)
    label_candidate_ids = {str(label.get("candidate_id")) for label in labels if label.get("candidate_id")}
    candidate_window_counts: Counter[str] = Counter()
    for candidate in candidates:
        candidate_window = decision_window_id(
            candidate.get("symbol"),
            candidate.get("side"),
            candidate.get("decision_time_utc"),
        )
        if candidate_window:
            candidate_window_counts[candidate_window] += 1
    axis_window_candidate_ids: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    axis_window_executable_candidate_ids: defaultdict[tuple[str, str], set[str]] = (
        defaultdict(set)
    )
    prepared_candidates: list[
        tuple[
            dict[str, Any],
            str,
            str | None,
            dict[int, dict[str, Any]],
            list[str],
            dict[str, Any],
        ]
    ] = []
    selected_package_candidate_rows = 0
    for raw_candidate in candidates:
        candidate = hydrate_candidate_quality_aliases(raw_candidate)
        candidate_id = str(candidate.get("candidate_id") or "")
        window = decision_window_id(
            candidate.get("symbol"),
            candidate.get("side"),
            candidate.get("decision_time_utc"),
        )
        member_matches: list[dict[str, Any]] = []
        for key in candidate_keys(candidate):
            member_matches.extend(member_by_key.get(key, []))
        unique_members = {
            int(member["source_axis_row_index"]): member
            for member in member_matches
            if member.get("source_axis_row_index") is not None
        }
        for stable_axis_id in stable_unique(
            list_values(candidate.get("ultimate_package_matched_member_axis_ids"))
            + list_values(candidate.get("matched_stable_member_axis_ids"))
        ):
            member = member_by_stable_axis_id.get(stable_axis_id)
            if member and member.get("source_axis_row_index") is not None:
                unique_members.setdefault(int(member["source_axis_row_index"]), member)
        matched_stable_member_axis_ids = sorted(
            {
                stable_axis_id
                for idx in unique_members
                if (stable_axis_id := stable_member_axis_id(unique_members[idx]))
            }
        )
        if unique_members:
            selected_package_candidate_rows += 1
        quality_fields = selected_package_bridge_quality_fields(
            candidate,
            matched_stable_member_axis_ids=matched_stable_member_axis_ids,
            matched_members=unique_members.values(),
        )
        if window and candidate_id:
            for stable_axis_id in matched_stable_member_axis_ids:
                axis_key = (window, stable_axis_id)
                axis_window_candidate_ids[axis_key].add(candidate_id)
                if (
                    quality_fields.get("package_replay_executable_candidate_use_allowed")
                    is True
                ):
                    axis_window_executable_candidate_ids[axis_key].add(candidate_id)
        prepared_candidates.append(
            (
                candidate,
                candidate_id,
                window,
                unique_members,
                matched_stable_member_axis_ids,
                quality_fields,
            )
        )

    bridge_rows: list[dict[str, Any]] = []
    label_join_rows: list[dict[str, Any]] = []
    matched_label_ids: set[str] = set()
    candidate_id_label_hits = 0
    proxy_window_label_match_rows = 0
    for (
        candidate,
        candidate_id,
        window,
        unique_members,
        matched_stable_member_axis_ids,
        quality_fields,
    ) in prepared_candidates:
        labels_for_window = labels_by_window.get(window or "", [])
        replay_instance_key = _candidate_time_instance_key(
            candidate_id,
            candidate.get("decision_time_utc"),
        )
        if not replay_instance_key and candidate_id and window:
            replay_instance_key = f"{candidate_id}@@{window}"
        bridge_instance_join_key = (
            f"{candidate_id}@@{window}" if candidate_id and window else None
        )
        if candidate_id in label_candidate_ids:
            candidate_id_label_hits += 1
        for label in labels_for_window:
            matched_label_ids.add(str(label.get("label_id")))
            pending_floor = floor_to_m15_iso(label.get("pending_created_time_utc"))
            pending_proxy_match = decision_time_source == "pending-created-labels"
            if pending_proxy_match:
                proxy_window_label_match_rows += 1
            exact_candidate_id_match = candidate_id == str(label.get("candidate_id") or "")
            stable_window_unique_alias_allowed = bool(
                unique_members
                and not exact_candidate_id_match
                and not pending_proxy_match
                and window
                and len(labels_for_window) == 1
                and candidate_window_counts.get(window, 0) == 1
            )
            package_axis_alias_ids = [
                stable_axis_id
                for stable_axis_id in matched_stable_member_axis_ids
                if window
                and candidate_id
                and len(axis_window_executable_candidate_ids.get((window, stable_axis_id), set()))
                == 1
                and candidate_id
                in axis_window_executable_candidate_ids.get((window, stable_axis_id), set())
            ]
            canonical_package_axis_alias_id = (
                package_axis_alias_ids[0]
                if len(package_axis_alias_ids) == 1
                else None
            )
            package_axis_unique_alias_allowed = bool(
                canonical_package_axis_alias_id
                and not exact_candidate_id_match
                and not pending_proxy_match
            )
            package_axis_key = (
                (window, canonical_package_axis_alias_id)
                if window and canonical_package_axis_alias_id
                else None
            )
            package_axis_window_replay_candidate_count = (
                len(axis_window_candidate_ids.get(package_axis_key, set()))
                if package_axis_key
                else 0
            )
            package_axis_window_executable_candidate_count = (
                len(axis_window_executable_candidate_ids.get(package_axis_key, set()))
                if package_axis_key
                else 0
            )
            denominator_use_allowed = bool(
                unique_members
                and not pending_proxy_match
                and (
                    exact_candidate_id_match
                    or stable_window_unique_alias_allowed
                    or package_axis_unique_alias_allowed
                )
                and quality_fields.get("package_replay_executable_candidate_use_allowed")
                is True
            )
            canonical_candidate_id = (
                candidate_id
                if exact_candidate_id_match
                else window
                if stable_window_unique_alias_allowed
                else (
                    f"{window}:{canonical_package_axis_alias_id}"
                    if package_axis_unique_alias_allowed
                    else None
                )
            )
            canonical_alias_status = (
                "exact_candidate_id_match"
                if exact_candidate_id_match
                else "stable_window_member_axis_unique_alias"
                if stable_window_unique_alias_allowed
                else "package_axis_window_unique_executable_alias"
                if package_axis_unique_alias_allowed
                else "candidate_id_namespace_mismatch_or_stable_window_collision"
            )
            canonical_package_axis_alias_status = (
                "package_axis_window_unique_executable_alias"
                if package_axis_unique_alias_allowed
                else "package_axis_no_unique_executable_alias"
                if matched_stable_member_axis_ids and not pending_proxy_match
                else "pending_created_proxy_context_only"
                if pending_proxy_match
                else "no_package_axis_alias"
            )
            label_context_fields = lifecycle_label_context_fields([label])
            denominator_use_reason = selected_package_denominator_use_reason(
                denominator_use_allowed=denominator_use_allowed,
                canonical_alias_status=canonical_alias_status,
                exact_candidate_id_match=exact_candidate_id_match,
                stable_window_unique_alias_allowed=stable_window_unique_alias_allowed,
                package_axis_unique_alias_allowed=package_axis_unique_alias_allowed,
                pending_proxy_match=pending_proxy_match,
                lifecycle_label_context_present=bool(
                    label_context_fields.get("lifecycle_label_context_present")
                ),
            )
            label_join_rows.append(
                {
                    "schema": "gtos.final_moonshot.denominator_to_deployment.selected_package_replay_bridge.label_join.v1",
                    "decision_time_source": decision_time_source,
                    "label_id": label.get("label_id"),
                    "candidate_id": candidate_id,
                    "label_candidate_id": label.get("candidate_id"),
                    "replay_candidate_id": candidate_id,
                    "canonical_replay_candidate_instance_key": replay_instance_key,
                    "risk_finalizer_probe_instance_key": replay_instance_key,
                    "source_bound_replay_candidate_instance_key": replay_instance_key,
                    "selected_package_bridge_join_status": (
                        "exact_candidate_window_join"
                        if bridge_instance_join_key
                        else "selected_package_bridge_window_missing"
                    ),
                    "selected_package_bridge_join_key": bridge_instance_join_key,
                    "stable_decision_window_id": window,
                    "pending_created_time_utc": label.get("pending_created_time_utc"),
                    "pending_created_m15_floor_utc": pending_floor,
                    "pending_created_stable_window_proxy_id": proxy_window_id(
                        label.get("symbol"),
                        label.get("side"),
                        pending_floor,
                    ),
                    "symbol": candidate.get("symbol"),
                    "side": candidate.get("side"),
                    "decision_time_utc": candidate.get("decision_time_utc"),
                    **bridge_route_provenance_fields(candidate, quality_fields),
                    "member_axis_match_count": len(unique_members),
                    "matched_source_axis_row_indexes": sorted(unique_members),
                    "matched_stable_member_axis_ids": matched_stable_member_axis_ids,
                    "selected_package_matched_member_axis_ids": matched_stable_member_axis_ids,
                    **quality_fields,
                    "canonical_candidate_id": canonical_candidate_id,
                    "canonical_candidate_alias_status": canonical_alias_status,
                    "canonical_candidate_alias_source_boundary": (
                        "exact_candidate_id_or_unique_stable_window_member_axis_alias"
                        "_or_unique_executable_package_axis_alias;"
                        "pending_created_proxy_remains_context_only"
                    ),
                    "canonical_package_axis_alias_id": canonical_package_axis_alias_id,
                    "canonical_package_axis_alias_status": (
                        canonical_package_axis_alias_status
                    ),
                    "canonical_package_axis_alias_boundary": (
                        "stable_decision_window_id_plus_stable_member_axis_id;"
                        "requires_one_executable_replay_candidate_for_axis_window;"
                        "pending_created_proxy_remains_context_only"
                    ),
                    "package_axis_window_replay_candidate_count": (
                        package_axis_window_replay_candidate_count
                    ),
                    "package_axis_window_executable_candidate_count": (
                        package_axis_window_executable_candidate_count
                    ),
                    "package_axis_window_label_count": len(labels_for_window),
                    "package_axis_unique_alias_allowed": package_axis_unique_alias_allowed,
                    "stable_window_label_collision_count": len(labels_for_window),
                    "stable_window_replay_candidate_collision_count": (
                        candidate_window_counts.get(window or "", 0)
                    ),
                    "stable_window_unique_alias_allowed": (
                        stable_window_unique_alias_allowed
                    ),
                    "exact_candidate_id_match": exact_candidate_id_match,
                    "stable_decision_window_match": not pending_proxy_match,
                    "pending_created_proxy_window_match": pending_proxy_match,
                    **label_context_fields,
                    "source_truth_scope": SOURCE_TRUTH_SCOPE,
                    "pending_created_window_truth_status": (
                        "source_bound_stable_window_proxy_only_not_recovered_original_decision_time"
                        if pending_proxy_match
                        else None
                    ),
                    "selected_package_denominator_use_allowed": denominator_use_allowed,
                    "selected_package_denominator_use_reason": denominator_use_reason,
                    "training_use_allowed": False,
                    "final_package_selection_allowed": False,
                }
            )
        selected_label_join_rows_for_candidate = [
            row
            for row in label_join_rows
            if row.get("replay_candidate_id") == candidate_id
            and row.get("stable_decision_window_id") == window
            and row.get("selected_package_denominator_use_allowed") is True
        ]
        label_join_rows_for_candidate = [
            row
            for row in label_join_rows
            if row.get("replay_candidate_id") == candidate_id
            and row.get("stable_decision_window_id") == window
        ]
        bridge_denominator_use_allowed = bool(selected_label_join_rows_for_candidate)
        bridge_label_context_fields = lifecycle_label_context_fields(labels_for_window)
        bridge_denominator_use_reason = (
            str(selected_label_join_rows_for_candidate[0].get("selected_package_denominator_use_reason"))
            if selected_label_join_rows_for_candidate
            else str(
                label_join_rows_for_candidate[0].get(
                    "selected_package_denominator_use_reason"
                )
            )
            if label_join_rows_for_candidate
            else "stable_window_lifecycle_context_present_denominator_authority_closed"
            if bridge_label_context_fields.get("lifecycle_label_context_present")
            and decision_time_source != "pending-created-labels"
            else "pending_created_lifecycle_context_present_denominator_authority_closed"
            if bridge_label_context_fields.get("lifecycle_label_context_present")
            and decision_time_source == "pending-created-labels"
            else "candidate_id_namespace_mismatch_or_collision"
        )
        bridge_rows.append(
            {
                "schema": "gtos.final_moonshot.denominator_to_deployment.selected_package_replay_bridge.denominator.v1",
                "decision_time_source": decision_time_source,
                "candidate_id": candidate_id,
                "replay_candidate_id": candidate_id,
                "canonical_replay_candidate_instance_key": replay_instance_key,
                "risk_finalizer_probe_instance_key": replay_instance_key,
                "source_bound_replay_candidate_instance_key": replay_instance_key,
                "selected_package_bridge_join_status": (
                    "exact_candidate_window_join"
                    if bridge_instance_join_key
                    else "selected_package_bridge_window_missing"
                ),
                "selected_package_bridge_join_key": bridge_instance_join_key,
                "stable_decision_window_id": window,
                "symbol": candidate.get("symbol"),
                "side": candidate.get("side"),
                "decision_time_utc": candidate.get("decision_time_utc"),
                **bridge_route_provenance_fields(candidate, quality_fields),
                "member_axis_match_count": len(unique_members),
                "matched_source_axis_row_indexes": sorted(unique_members),
                "matched_stable_member_axis_ids": matched_stable_member_axis_ids,
                "selected_package_matched_member_axis_ids": matched_stable_member_axis_ids,
                **quality_fields,
                "package_axis_window_replay_candidate_count": sum(
                    len(axis_window_candidate_ids.get((window, stable_axis_id), set()))
                    for stable_axis_id in matched_stable_member_axis_ids
                    if window
                ),
                "package_axis_window_executable_candidate_count": sum(
                    len(
                        axis_window_executable_candidate_ids.get(
                            (window, stable_axis_id),
                            set(),
                        )
                    )
                    for stable_axis_id in matched_stable_member_axis_ids
                    if window
                ),
                "label_window_match_count": len(labels_for_window),
                "exact_candidate_id_label_match": candidate_id in label_candidate_ids,
                "stable_window_replay_candidate_collision_count": (
                    candidate_window_counts.get(window or "", 0)
                ),
                "stable_decision_window_label_match": bool(labels_for_window)
                and decision_time_source != "pending-created-labels",
                "pending_created_proxy_window_label_match": bool(labels_for_window)
                and decision_time_source == "pending-created-labels",
                **bridge_label_context_fields,
                "selected_package_replay_row": bool(unique_members),
                "source_truth_scope": SOURCE_TRUTH_SCOPE,
                "pending_created_window_truth_status": (
                    "source_bound_stable_window_proxy_only_not_recovered_original_decision_time"
                    if decision_time_source == "pending-created-labels"
                    else None
                ),
                "selected_package_denominator_use_allowed": bridge_denominator_use_allowed,
                "selected_package_denominator_use_reason": bridge_denominator_use_reason,
                "selected_package_denominator_canonical_package_axis_alias_ids": sorted(
                    {
                        str(row.get("canonical_package_axis_alias_id"))
                        for row in label_join_rows
                        if row.get("replay_candidate_id") == candidate_id
                        and row.get("stable_decision_window_id") == window
                        and row.get("selected_package_denominator_use_allowed") is True
                        and row.get("canonical_package_axis_alias_id")
                    }
                ),
                "training_use_allowed": False,
                "final_package_selection_allowed": False,
            }
        )

    matched_member_rows = {
        idx
        for row in bridge_rows
        for idx in row.get("matched_source_axis_row_indexes", [])
        if row.get("selected_package_replay_row")
    }
    selected_denominator_rows = [
        row for row in bridge_rows if row.get("selected_package_denominator_use_allowed") is True
    ]
    selected_denominator_label_join_rows = [
        row for row in label_join_rows if row.get("selected_package_denominator_use_allowed") is True
    ]
    summary = {
        "candidate_rows": len(candidates),
        "selected_package_candidate_rows": selected_package_candidate_rows,
        "stable_decision_window_label_match_rows": (
            0 if decision_time_source == "pending-created-labels" else len(label_join_rows)
        ),
        "proxy_window_label_match_rows": proxy_window_label_match_rows,
        "matched_lifecycle_label_rows": len(matched_label_ids),
        "candidate_id_label_hits": candidate_id_label_hits,
        "matched_member_axis_rows": len(matched_member_rows),
        "exact_denominator_join_rows": sum(
            1 for row in label_join_rows if row.get("exact_candidate_id_match") is True
            and row.get("selected_package_denominator_use_allowed") is True
        ),
        "canonical_denominator_join_rows": len(selected_denominator_rows),
        "canonical_denominator_label_join_rows": len(selected_denominator_label_join_rows),
        "stable_window_member_axis_unique_alias_rows": sum(
            1 for row in label_join_rows if row.get("stable_window_unique_alias_allowed") is True
        ),
        "package_axis_window_unique_executable_alias_rows": sum(
            1
            for row in label_join_rows
            if row.get("package_axis_unique_alias_allowed") is True
        ),
        "selected_package_denominator_use_allowed_rows": len(selected_denominator_rows),
        "selected_package_denominator_use_allowed_label_join_rows": len(
            selected_denominator_label_join_rows
        ),
    }
    return bridge_rows, label_join_rows, summary


def build_profit_harvest_authority_blocker_rows(
    *,
    oracles: Iterable[Mapping[str, Any]],
    trades: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Rows where profit-harvest replay has edge but lacks ordered tick authority."""

    trades_by_candidate_id: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    trades_by_instance_key: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for trade_row in trades:
        candidate_id = str(trade_row.get("candidate_id") or "").strip()
        if not candidate_id:
            continue
        trades_by_candidate_id[candidate_id].append(trade_row)
        instance_key = _candidate_time_instance_key(
            candidate_id,
            _profit_harvest_row_decision_time(trade_row),
        )
        if instance_key:
            trades_by_instance_key[instance_key].append(trade_row)

    rows: list[dict[str, Any]] = []
    for oracle in oracles:
        diagnostic = oracle.get("profit_harvest_mfe_capture_replay_exit_diagnostic")
        if not isinstance(diagnostic, Mapping):
            continue
        if oracle.get("profit_harvest_mfe_capture_replay_exit_final_r_authority") is True:
            continue
        candidate_id = str(oracle.get("candidate_id") or "")
        decision_time = _profit_harvest_row_decision_time(oracle)
        join_key = _candidate_time_instance_key(candidate_id, decision_time)
        trade_matches: list[Mapping[str, Any]] = []
        join_status = "profit_harvest_trade_join_candidate_id_missing"
        if join_key:
            trade_matches = list(trades_by_instance_key.get(join_key, ()))
            if len(trade_matches) == 1:
                join_status = "exact_candidate_time_trade_join"
            elif len(trade_matches) > 1:
                trade_matches = []
                join_status = "duplicate_candidate_time_trade_join_ambiguous"
            else:
                join_status = "profit_harvest_trade_join_exact_missing"
        elif candidate_id:
            join_status = "profit_harvest_trade_join_decision_time_missing_no_trade_join"
        trade = trade_matches[0] if trade_matches else {}
        actual_net_r = _safe_float_or_none(
            trade.get("net_proxy_r") if isinstance(trade, Mapping) else None
        )
        expected_cost_r = _safe_float_or_none(
            trade.get("expected_cost_r") if isinstance(trade, Mapping) else None
        )
        if expected_cost_r is None:
            expected_cost_r = _safe_float_or_none(oracle.get("expected_cost_r")) or 0.0
        diagnostic_gross_r = _safe_float_or_none(
            diagnostic.get("m1_proxy_policy_gross_r")
            if diagnostic.get("m1_proxy_policy_gross_r") is not None
            else diagnostic.get("diagnostic_policy_gross_r")
        )
        diagnostic_net_r = (
            round(diagnostic_gross_r - expected_cost_r, 8)
            if diagnostic_gross_r is not None
            else None
        )
        m1_proxy_replay_authority = bool(
            diagnostic.get("m1_proxy_replay_authority") is True
            or diagnostic.get("m1_proxy_profit_harvest_replay_authority") is True
            or oracle.get("profit_harvest_mfe_capture_replay_exit_m1_proxy_replay_authority")
            is True
            or str(
                oracle.get(
                    "profit_harvest_mfe_capture_replay_exit_final_r_authority_status"
                )
                or ""
            )
            in {
                "m1_ordered_path_proxy_replay_not_terminal_final_r_authority",
                "m1_ordered_path_proxy_final_r_diagnostic_not_authority",
                "m1_ordered_path_proxy_target_after_exit_diagnostic_not_authority",
            }
        )
        blocker_status = (
            "selected_loser_positive_profit_harvest_diagnostic_needs_ordered_tick"
            if actual_net_r is not None
            and actual_net_r <= 0.0
            and diagnostic_net_r is not None
            and diagnostic_net_r > 0.0
            else "profit_harvest_diagnostic_needs_ordered_tick"
        )
        rows.append(
            {
                "schema": (
                    "gtos.final_moonshot.denominator_to_deployment."
                    "selected_package_replay_bridge.profit_harvest_authority_blocker.v1"
                ),
                "candidate_id": candidate_id,
                "profit_harvest_trade_join_status": join_status,
                "profit_harvest_trade_join_key": join_key,
                "profit_harvest_trade_join_candidate_id_trade_count": len(
                    trades_by_candidate_id.get(candidate_id, ())
                )
                if candidate_id
                else 0,
                "symbol": oracle.get("symbol") or trade.get("symbol"),
                "side": oracle.get("side") or trade.get("side"),
                "decision_time_utc": decision_time,
                "fill_time_utc": oracle.get("fill_time_utc"),
                "close_time_utc": oracle.get("close_time_utc")
                or trade.get("exit_time_utc"),
                "expiry_utc": oracle.get("expiry_utc"),
                "actual_gross_r": trade.get("gross_r") if isinstance(trade, Mapping) else None,
                "actual_net_r": actual_net_r,
                "actual_cash_pnl": trade.get("pnl_cash") if isinstance(trade, Mapping) else None,
                "actual_risk_cash": trade.get("risk_cash") if isinstance(trade, Mapping) else None,
                "actual_risk_pct": trade.get("risk_pct") if isinstance(trade, Mapping) else None,
                "expected_cost_r": expected_cost_r,
                "mfe_r": oracle.get("mfe_r") or trade.get("mfe_r"),
                "mae_r": oracle.get("mae_r") or trade.get("mae_r"),
                "terminal_outcome": oracle.get("terminal_outcome"),
                "actual_close_reason": trade.get("close_reason")
                if isinstance(trade, Mapping)
                else oracle.get("close_reason"),
                "profit_harvest_diagnostic_gross_r": diagnostic_gross_r,
                "profit_harvest_diagnostic_net_r": diagnostic_net_r,
                "profit_harvest_diagnostic_close_reason": diagnostic.get(
                    "diagnostic_policy_close_reason"
                ),
                "profit_harvest_diagnostic_close_time_utc": diagnostic.get(
                    "diagnostic_policy_close_time_utc"
                ),
                "profit_harvest_diagnostic_status": diagnostic.get("status"),
                "profit_harvest_final_r_authority": False,
                "profit_harvest_final_r_authority_status": oracle.get(
                    "profit_harvest_mfe_capture_replay_exit_final_r_authority_status"
                ),
                "ordered_tick_final_r_authority": False,
                "m1_proxy_replay_authority": m1_proxy_replay_authority,
                "m1_proxy_replay_authority_status": (
                    "m1_ordered_path_proxy_replay_authority_ordered_tick_proof_required"
                    if m1_proxy_replay_authority
                    else None
                ),
                "m1_proxy_policy_gross_r": diagnostic.get("m1_proxy_policy_gross_r"),
                "m1_proxy_policy_net_r": (
                    diagnostic_net_r if m1_proxy_replay_authority else None
                ),
                "headline_result_authority": False,
                "headline_result_authority_status": (
                    "m1_proxy_replay_diagnostic_not_headline_authority"
                    if m1_proxy_replay_authority
                    else "profit_harvest_diagnostic_not_headline_authority"
                ),
                "legacy_final_r_authority": False,
                "legacy_final_r_authority_semantics": (
                    "final_r_authority_is_ordered_tick_terminal_authority_only"
                ),
                "profit_harvest_authority_blocker_status": blocker_status,
                "blocker_type": "m1_proxy_ordered_tick_proof_required"
                if m1_proxy_replay_authority
                else "profit_harvest_ordered_tick_proof_required",
                "ordered_tick_proof_required": True,
                "ordered_tick_proof_required_reason": (
                    "m1_proxy_replay_authority_not_terminal_headline_final_r"
                    if m1_proxy_replay_authority
                    else "profit_harvest_diagnostic_requires_ordered_tick"
                ),
                "diagnostic_net_delta_vs_actual_r": (
                    round(diagnostic_net_r - actual_net_r, 8)
                    if diagnostic_net_r is not None and actual_net_r is not None
                    else None
                ),
                "path_source": oracle.get("source"),
                "ordered_tick_truth_satisfied": oracle.get(
                    "ordered_tick_truth_satisfied"
                ),
                "required_tick_source_broker": "FTMO",
                "required_timeframe": "TICK",
                "required_tick_start_utc": decision_time,
                "required_tick_end_utc": oracle.get("expiry_utc")
                or oracle.get("close_time_utc")
                or trade.get("exit_time_utc"),
                "required_export_tool": "scripts/export_mt5_research_ticks.py",
                "required_source_truth_scope": SOURCE_TRUTH_SCOPE,
                "broker_mutation": False,
                "live_broker_authority": False,
                "final_package_selection_allowed": False,
                "evidence_class": OUTCOME_EVIDENCE_CLASS,
            }
        )
    rows.sort(
        key=lambda row: (
            str(row.get("decision_time_utc") or ""),
            str(row.get("symbol") or ""),
            str(row.get("candidate_id") or ""),
        )
    )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-only", action="store_true", help="Build sources and emit source summary without replay.")
    parser.add_argument("--smoke-subset", action="store_true", help="Use campaign smoke subset for local debugging only.")
    parser.add_argument("--max-days", type=int, default=0, help="Limit replay days for bounded diagnostics; 0 means all days.")
    parser.add_argument(
        "--enable-m15-tick-ohlc-repair",
        action="store_true",
        help="Keep live M15 tick OHLC repair enabled. Default disables it for source-bound CSV replay speed.",
    )
    parser.add_argument(
        "--enable-pipeline-state-writes",
        action="store_true",
        help="Allow live component pipeline_state writes. Default suppresses them for read-only route replay.",
    )
    parser.add_argument(
        "--disable-symbol-config-cache",
        action="store_true",
        help="Use the upstream per-snapshot JSON config copy. Default caches per-symbol replay config for route speed.",
    )
    parser.add_argument(
        "--disable-candle-index-cache",
        action="store_true",
        help="Use upstream linear closed-bar scans. Default indexes source timestamps for route replay speed.",
    )
    parser.add_argument(
        "--decision-time-source",
        choices=("lifecycle-labels", "m15-grid", "pending-created-labels"),
        default="lifecycle-labels",
        help="Replay lifecycle decision windows by default; pending-created-labels uses M15 proxy windows only.",
    )
    parser.add_argument(
        "--symbol-scope",
        choices=("lifecycle-labels", "pending-created-labels", "full-package", "all"),
        default="lifecycle-labels",
        help="Replay lifecycle-label symbols by default; full-package uses the full package symbol surface. 'all' is a backward-compatible alias for full-package.",
    )
    parser.add_argument(
        "--replay-days",
        default="",
        help="Comma-separated YYYY-MM-DD replay days. Defaults to May label days or June pending-created days by mode.",
    )
    parser.add_argument(
        "--replay-day-start",
        default="",
        help="Inclusive replay start day for bounded route-local diagnostics.",
    )
    parser.add_argument(
        "--replay-day-end",
        default="",
        help="Inclusive replay end day for bounded route-local diagnostics.",
    )
    parser.add_argument(
        "--output-prefix",
        default="",
        help="Artifact prefix. Defaults preserve the May bridge prefix or use the pending-created bridge prefix by mode.",
    )
    return parser.parse_args()


def install_source_bound_csv_replay_fast_paths(
    *,
    disable_m15_tick_repair: bool,
    suppress_pipeline_writes: bool,
    cache_symbol_config: bool,
    cache_candle_index: bool,
) -> None:
    def _disabled_m15_tick_repair(
        candles: list[dict],
        symbol: str,
        config: dict | None = None,
    ) -> tuple[list[dict], dict[str, Any]]:
        return list(candles), {
            "enabled": False,
            "reason": "route_local_source_bound_csv_replay_m15_tick_repair_disabled",
            "source": "source_bound_csv_replay_fast_path",
            "symbol": symbol,
            "timeframe": "M15",
            "input_candles": len(candles),
        }

    def _suppressed_pipeline_write(filename: str, data: dict) -> None:
        return None

    symbol_config_cache: dict[
        tuple[int, str], tuple[Mapping[str, Any], dict[str, Any]]
    ] = {}
    candle_index_cache: dict[
        tuple[int, str],
        tuple[
            Iterable[Mapping[str, Any]],
            tuple[dict[str, Any], ...],
            tuple[Any, ...],
        ],
    ] = {}

    def _cached_replay_symbol_config(config: Mapping[str, Any], symbol: str) -> dict[str, Any]:
        key = (id(config), symbol)
        cached = symbol_config_cache.get(key)
        if cached is None or cached[0] is not config:
            output = copy.deepcopy(config)
            market = output.setdefault("market", {})
            if not isinstance(market, dict):
                market = {}
                output["market"] = market
            market["symbol"] = symbol
            market["mt5_symbol"] = timewarp_loop.ftmo_symbol(symbol)
            tick_features = output.setdefault("tick_features", {})
            if not isinstance(tick_features, dict):
                tick_features = {}
                output["tick_features"] = tick_features
            tick_features["enabled"] = False
            tick_features[
                "disabled_reason"
            ] = "replay_source_separation_predecision_uses_d1_h4_h1_m15_closed_bars_only"
            cached = (config, output)
            symbol_config_cache[key] = cached
        return cached[1]

    def _indexed_rows(
        rows: Iterable[Mapping[str, Any]],
        *,
        timeframe: str,
        asof: Any,
        limit: int,
    ) -> tuple[dict[str, Any], ...]:
        tf_name = str(timeframe or "").upper()
        key = (id(rows), tf_name)
        cached = candle_index_cache.get(key)
        if cached is None or cached[0] is not rows:
            row_tuple = tuple(dict(row) for row in rows)
            indexed = [
                (parsed, row)
                for row in row_tuple
                if (parsed := timewarp_loop.parse_row_time(row)) is not None
            ]
            indexed.sort(key=lambda item: item[0])
            cached = (
                rows,
                tuple(row for _parsed, row in indexed),
                tuple(parsed for parsed, _row in indexed),
            )
            candle_index_cache[key] = cached
        _source_rows, row_tuple, times = cached
        asof_utc = asof.astimezone(timezone.utc) if getattr(asof, "tzinfo", None) else asof.replace(tzinfo=timezone.utc)
        close_delta = timedelta(minutes=timewarp_loop.TIMEFRAME_MINUTES.get(tf_name, 0))
        cutoff = asof_utc + timedelta(seconds=2) - close_delta
        end = bisect.bisect_right(times, cutoff)
        start = max(0, end - max(0, int(limit))) if limit else 0
        return row_tuple[start:end]

    def _fast_get_candles(self: Any, symbol: str, timeframe: int, count: int) -> list[dict[str, Any]]:
        canonical_symbol, asof = self._context()
        tf_name = self._timeframe_name(timeframe)
        source = self.sources[canonical_symbol][tf_name]
        selected = [dict(row) for row in _indexed_rows(source.rows, timeframe=tf_name, asof=asof, limit=int(count))]
        self._last_calls[tf_name] = {
            "requested_broker_symbol": symbol,
            "canonical_symbol": canonical_symbol,
            "mapped_symbol": timewarp_loop.ftmo_symbol(canonical_symbol),
            "timeframe": tf_name,
            "requested_count": int(count),
            "returned_count": len(selected),
            "latest_closed_time": selected[-1].get("time_utc") if selected else None,
            "source_path": str(source.spec.path),
            "source_hash": source.sha256,
            "source_broker": source.spec.source_broker,
            "source_role": source.spec.source_role,
            "manifest_path": source.spec.manifest_path,
            "export_tool": source.spec.export_tool,
        }
        return selected

    if disable_m15_tick_repair:
        live_data_ingestion.repair_malformed_m15_ohlc_from_ticks = _disabled_m15_tick_repair
    if suppress_pipeline_writes:
        live_market_state.write_pipeline = _suppressed_pipeline_write
    if cache_symbol_config:
        timewarp_loop.replay_symbol_config = _cached_replay_symbol_config
    if cache_candle_index:
        timewarp_loop.HistoricalMT5Adapter.get_candles = _fast_get_candles


def replay_days_from_args(args: argparse.Namespace, labels: Iterable[Mapping[str, Any]]) -> tuple[str, ...]:
    if args.replay_days:
        return tuple(day.strip() for day in str(args.replay_days).split(",") if day.strip())
    if args.replay_day_start or args.replay_day_end:
        start = date.fromisoformat(args.replay_day_start or args.replay_day_end)
        end = date.fromisoformat(args.replay_day_end or args.replay_day_start)
        if end < start:
            raise ValueError("--replay-day-end must be >= --replay-day-start")
        out = []
        current = start
        while current <= end:
            out.append(current.isoformat())
            current += timedelta(days=1)
        return tuple(out)
    if args.decision_time_source == "pending-created-labels":
        days = sorted(
            {
                str(floor)[:10]
                for row in labels
                if not row.get("decision_time_utc")
                if (floor := floor_to_m15_iso(row.get("pending_created_time_utc")))
            }
        )
        return tuple(days or PENDING_CREATED_REPLAY_DAYS)
    return REPLAY_DAYS


def install_lifecycle_label_replay_scope(
    labels: Iterable[Mapping[str, Any]],
    *,
    decision_time_source: str,
    symbol_scope: str,
    replay_days: Iterable[str],
) -> dict[str, Any]:
    normalized_symbol_scope = (
        "full-package" if symbol_scope in {"all", "full-package"} else symbol_scope
    )
    if decision_time_source == "pending-created-labels":
        replay_day_set = set(replay_days)
        labels_with_time = [
            {
                **dict(row),
                "decision_time_utc": pending_floor,
            }
            for row in labels
            if not row.get("decision_time_utc")
            if (pending_floor := floor_to_m15_iso(row.get("pending_created_time_utc")))
            and pending_floor[:10] in replay_day_set
        ]
    else:
        labels_with_time = [row for row in labels if row.get("decision_time_utc")]
    decision_times_by_day: dict[str, list[Any]] = defaultdict(list)
    seen_times: set[str] = set()
    for row in labels_with_time:
        decision_time = str(row.get("decision_time_utc") or "")
        parsed = timewarp_loop.parse_utc(decision_time)
        if parsed is None or decision_time in seen_times:
            continue
        seen_times.add(decision_time)
        decision_times_by_day[decision_time[:10]].append(parsed)
    for rows in decision_times_by_day.values():
        rows.sort()

    scoped_symbols = tuple(
        sorted(
            {
                norm_symbol(row.get("symbol"))
                for row in labels_with_time
                if row.get("symbol")
            }
        )
    )

    if decision_time_source in {"lifecycle-labels", "pending-created-labels"}:
        def _label_decision_times_for_day(self: Any, day: str, *, smoke_subset: bool = False) -> list[Any]:
            return list(decision_times_by_day.get(day, ()))

        timewarp_loop.ReplayClock.decision_times_for_day = _label_decision_times_for_day

    if normalized_symbol_scope in {"lifecycle-labels", "pending-created-labels"} and scoped_symbols:
        timewarp_loop.INCLUDED_SYMBOLS = scoped_symbols
        active_symbols = scoped_symbols
    else:
        timewarp_loop.INCLUDED_SYMBOLS = FULL_PACKAGE_SYMBOLS
        active_symbols = FULL_PACKAGE_SYMBOLS

    return {
        "decision_time_source": decision_time_source,
        "symbol_scope": normalized_symbol_scope,
        "requested_symbol_scope": symbol_scope,
        "lifecycle_label_rows_with_decision_time": len(labels_with_time),
        "scoped_unique_decision_times": len(seen_times),
        "scoped_symbols": list(active_symbols),
        "full_package_symbol_count": len(FULL_PACKAGE_SYMBOLS),
        "full_package_symbols": list(FULL_PACKAGE_SYMBOLS),
        "bounded_smoke": normalized_symbol_scope != "full-package",
        "pending_created_proxy_replay_windows": len(seen_times) if decision_time_source == "pending-created-labels" else 0,
        "pending_created_proxy_truth_scope": (
            "source_bound_stable_window_proxy_only_not_recovered_original_decision_time"
            if decision_time_source == "pending-created-labels"
            else None
        ),
    }


def main() -> int:
    args = parse_args()
    output_prefix = args.output_prefix.strip() or (
        PENDING_CREATED_PREFIX if args.decision_time_source == "pending-created-labels" else PREFIX
    )
    output_ledgers = ledger_files(output_prefix)
    reset_outputs(output_prefix)
    install_source_bound_csv_replay_fast_paths(
        disable_m15_tick_repair=not args.enable_m15_tick_ohlc_repair,
        suppress_pipeline_writes=not args.enable_pipeline_state_writes,
        cache_symbol_config=not args.disable_symbol_config_cache,
        cache_candle_index=not args.disable_candle_index_cache,
    )
    materializer_rows = read_jsonl(MATERIALIZER_LEDGER)
    pending_created_source_coverage_rows = read_jsonl(PENDING_CREATED_SOURCE_COVERAGE_LEDGER)
    members = read_jsonl(MEMBER_LEDGER)
    labels = read_jsonl(LABEL_LEDGER)
    replay_days = replay_days_from_args(args, labels)
    scope_summary = install_lifecycle_label_replay_scope(
        labels,
        decision_time_source=args.decision_time_source,
        symbol_scope=args.symbol_scope,
        replay_days=replay_days,
    )
    if args.decision_time_source == "pending-created-labels":
        sources, hydration_rows, manifest_rows = build_pending_created_sources(
            pending_created_source_coverage_rows,
            replay_days=replay_days,
            scoped_symbols=scope_summary["scoped_symbols"],
        )
        expected_source_symbols = set(scope_summary["scoped_symbols"])
        campaign_name = "pending_created_replay_bridge"
        campaign_phase = "pending_created_proxy_replay_bridge_june1_3"
        source_operation = "route_local_pending_created_proxy_replay_from_source_coverage"
    else:
        sources, hydration_rows, manifest_rows = build_sources(materializer_rows, replay_days=replay_days)
        expected_source_symbols = {str(row.get("symbol")) for row in materializer_rows if row.get("symbol")}
        campaign_name = "selected_package_replay_bridge"
        campaign_phase = "selected_package_replay_bridge_may3_12"
        source_operation = "route_local_replay_from_optimized_source_materializer"
    hydration_count = write_jsonl(ROUTE / output_ledgers["source_hydration"], hydrate_with_boundary(hydration_rows))
    progress_rows: list[dict[str, Any]] = []
    all_candidates: list[dict[str, Any]] = []
    all_scorecards: list[dict[str, Any]] = []
    all_orders: list[dict[str, Any]] = []
    all_trades: list[dict[str, Any]] = []
    all_oracles: list[dict[str, Any]] = []
    all_sidecars: list[dict[str, Any]] = []
    day_summaries: list[dict[str, Any]] = []
    broker = SimulatedBroker()
    order_sequence = 0
    config = build_replay_config()
    source_complete = bool(expected_source_symbols) and set(sources) == expected_source_symbols
    replay_days = replay_days[: args.max_days] if args.max_days and args.max_days > 0 else replay_days

    if source_complete and not args.source_only:
        for day in replay_days:
            campaign = CampaignConfig(
                name=campaign_name,
                phase=campaign_phase,
                days=(day,),
                pending_expiry_minutes=REPAIRED_PENDING_EXPIRY_MINUTES,
                use_repaired_pending_expiry=True,
                partial_be_runner=False,
                run_smoke_subset=args.smoke_subset,
            )
            old_cwd = os.getcwd()
            with tempfile.TemporaryDirectory(prefix="gtos_replay_bridge_") as tmpdir:
                os.chdir(tmpdir)
                try:
                    result = run_campaign(
                        campaign=campaign,
                        config=config,
                        sources=sources,
                        broker=broker,
                        starting_order_sequence=order_sequence,
                    )
                finally:
                    os.chdir(old_cwd)
            order_sequence = int(result.get("selected_order_sequence") or order_sequence)
            ledgers = result["ledgers"]
            all_candidates.extend(ledgers.get("candidate", []))
            all_scorecards.extend(ledgers.get("scorecard", []))
            all_orders.extend(ledgers.get("order", []))
            all_trades.extend(ledgers.get("trade", []))
            all_oracles.extend(ledgers.get("oracle", []))
            all_sidecars.extend(ledgers.get("packet_sidecar", []))
            day_summary = summarize_campaign(result, phase=campaign.phase)
            day_summary["trading_day"] = day
            day_summaries.append(day_summary)
            progress_rows.append(
                {
                    "schema": "gtos.final_moonshot.denominator_to_deployment.selected_package_replay_bridge.progress.v1",
                    "trading_day": day,
                    "status": "completed",
                    "source_complete": source_complete,
                    "candidate_rows": len(ledgers.get("candidate", [])),
                    "scorecard_rows": len(ledgers.get("scorecard", [])),
                    "order_rows": len(ledgers.get("order", [])),
                    "trade_rows": len(ledgers.get("trade", [])),
                    "oracle_rows": len(ledgers.get("oracle", [])),
                    "selected_order_sequence_after_day": order_sequence,
                    "broker_mutation": False,
                    "paid_api_call": False,
                    "remote_push": False,
                }
            )
    else:
        materializer_symbols = {str(row.get("symbol")) for row in materializer_rows if row.get("symbol")}
        progress_rows.append(
            {
                "schema": "gtos.final_moonshot.denominator_to_deployment.selected_package_replay_bridge.progress.v1",
                "status": "source_only" if args.source_only else "not_run_source_incomplete",
                "source_complete": source_complete,
                "symbols_with_source": sorted(sources),
                "missing_symbols": sorted((expected_source_symbols or materializer_symbols) - set(sources)),
                "broker_mutation": False,
                "paid_api_call": False,
                "remote_push": False,
            }
        )

    bridge_rows, label_join_rows, bridge_summary = build_denominator_bridge(
        candidates=all_candidates,
        members=members,
        labels=labels,
        decision_time_source=args.decision_time_source,
    )
    compact_rows = compact_candidate_rows(all_candidates, bridge_rows)
    candidate_status_by_id = build_candidate_status_lookup(compact_rows)
    candidate_status_by_window = build_candidate_status_window_lookup(compact_rows)
    decorated_candidates = decorate_rows(
        all_candidates,
        row_type="candidate",
        candidate_status_by_id=candidate_status_by_id,
        candidate_status_by_window=candidate_status_by_window,
    )
    decorated_scorecards = decorate_rows(
        all_scorecards,
        row_type="scorecard",
        candidate_status_by_id=candidate_status_by_id,
        candidate_status_by_window=candidate_status_by_window,
    )
    decorated_orders = decorate_rows(
        all_orders,
        row_type="order",
        candidate_status_by_id=candidate_status_by_id,
        candidate_status_by_window=candidate_status_by_window,
    )
    decorated_trades = decorate_rows(
        all_trades,
        row_type="trade",
        candidate_status_by_id=candidate_status_by_id,
        candidate_status_by_window=candidate_status_by_window,
    )
    decorated_oracles = decorate_rows(
        all_oracles,
        row_type="oracle",
        candidate_status_by_id=candidate_status_by_id,
        candidate_status_by_window=candidate_status_by_window,
    )
    decorated_orders = backfill_order_trade_path_provenance_from_oracles(
        decorated_orders,
        decorated_oracles,
        row_type="order",
    )
    decorated_trades = backfill_order_trade_path_provenance_from_oracles(
        decorated_trades,
        decorated_oracles,
        row_type="trade",
    )
    decorated_orders, filtered_non_executable_orders = filter_executable_order_trade_rows(
        decorated_orders,
        row_type="order",
    )
    decorated_trades, filtered_non_executable_trades = filter_executable_order_trade_rows(
        decorated_trades,
        row_type="trade",
    )
    profit_harvest_blocker_rows = build_profit_harvest_authority_blocker_rows(
        oracles=decorated_oracles,
        trades=decorated_trades,
    )
    execution_disposition_rows = build_selected_package_execution_disposition_rows(
        compact_rows=compact_rows,
        order_rows=decorated_orders,
        oracle_rows=decorated_oracles,
        trade_rows=decorated_trades,
        filtered_non_executable_order_rows=filtered_non_executable_orders,
        filtered_non_executable_trade_rows=filtered_non_executable_trades,
    )
    execution_disposition_summary = summarize_selected_package_execution_dispositions(
        execution_disposition_rows
    )
    ledger_write_row_counts = {
        "progress": write_jsonl(ROUTE / output_ledgers["progress"], progress_rows),
        "candidate": write_jsonl(ROUTE / output_ledgers["candidate"], decorated_candidates),
        "compact_candidate": write_jsonl(ROUTE / output_ledgers["compact_candidate"], compact_rows),
        "execution_disposition": write_jsonl(
            ROUTE / output_ledgers["execution_disposition"],
            execution_disposition_rows,
        ),
        "scorecard": write_jsonl(ROUTE / output_ledgers["scorecard"], decorated_scorecards),
        "order": write_jsonl(ROUTE / output_ledgers["order"], decorated_orders),
        "trade": write_jsonl(ROUTE / output_ledgers["trade"], decorated_trades),
    }
    ledger_write_row_counts["filtered_non_executable_order"] = write_jsonl(
        ROUTE / output_ledgers["filtered_non_executable_order"],
        filtered_non_executable_orders,
    )
    ledger_write_row_counts["filtered_non_executable_trade"] = write_jsonl(
        ROUTE / output_ledgers["filtered_non_executable_trade"],
        filtered_non_executable_trades,
    )
    ledger_write_row_counts["oracle"] = write_jsonl(ROUTE / output_ledgers["oracle"], decorated_oracles)
    ledger_write_row_counts["profit_harvest_authority_blocker"] = write_jsonl(
        ROUTE / output_ledgers["profit_harvest_authority_blocker"],
        profit_harvest_blocker_rows,
    )
    ledger_write_row_counts["packet_sidecar"] = write_jsonl(
        ROUTE / output_ledgers["packet_sidecar"],
        decorate_rows(all_sidecars, row_type="packet_sidecar"),
    )
    ledger_write_row_counts["denominator_bridge"] = write_jsonl(
        ROUTE / output_ledgers["denominator_bridge"],
        bridge_rows,
    )
    ledger_write_row_counts["label_join"] = write_jsonl(
        ROUTE / output_ledgers["label_join"],
        label_join_rows,
    )

    terminal_execution_materialized = bool(
        ledger_write_row_counts["order"]
        or ledger_write_row_counts["trade"]
        or ledger_write_row_counts["oracle"]
    )
    if source_complete and not args.source_only:
        summary_status = (
            "completed"
            if terminal_execution_materialized or not ledger_write_row_counts["candidate"]
            else "completed_candidate_replay_no_terminal_execution"
        )
    else:
        summary_status = progress_rows[0]["status"]

    summary = {
        "schema": "gtos.final_moonshot.denominator_to_deployment.selected_package_replay_bridge.summary.v1",
        "generated_utc": utc_now(),
        "status": summary_status,
        "output_prefix": output_prefix,
        "source_operation": source_operation,
        "source_complete": source_complete,
        "expected_source_symbols": sorted(expected_source_symbols),
        "symbols_with_source": sorted(sources),
        "source_hydration_rows": hydration_count,
        "source_manifest_rows": len(manifest_rows),
        "requested_replay_days": list(replay_days),
        "campaign_smoke_subset": bool(args.smoke_subset),
        "m15_tick_ohlc_repair_enabled": bool(args.enable_m15_tick_ohlc_repair),
        "pipeline_state_writes_enabled": bool(args.enable_pipeline_state_writes),
        "symbol_config_cache_enabled": not bool(args.disable_symbol_config_cache),
        "candle_index_cache_enabled": not bool(args.disable_candle_index_cache),
        "source_bound_csv_replay_fast_path": (
            not bool(args.enable_m15_tick_ohlc_repair)
            and not bool(args.enable_pipeline_state_writes)
            and not bool(args.disable_symbol_config_cache)
            and not bool(args.disable_candle_index_cache)
        ),
        **scope_summary,
        "bounded_smoke": bool(
            scope_summary.get("bounded_smoke")
            or args.smoke_subset
            or args.max_days
            or args.replay_days
            or args.replay_day_start
            or args.replay_day_end
        ),
        "broker_mutation": False,
        "paid_api_call": False,
        "remote_push": False,
        "ultimate_replay_loss_bucket_policy": config.get(
            "ultimate_replay_loss_bucket_policy"
        ),
        "ultimate_replay_loss_bucket_policy_id": ULTIMATE_REPLAY_LOSS_BUCKET_POLICY_ID,
        "ultimate_replay_loss_bucket_guard_rules": [
            dict(row) for row in ULTIMATE_REPLAY_LOSS_BUCKET_GUARD_RULES
        ],
        "live_broker_authority": False,
        "order_calls": 0,
        "candidate_rows": ledger_write_row_counts["candidate"],
        "compact_candidate_rows": ledger_write_row_counts["compact_candidate"],
        "scorecard_rows": ledger_write_row_counts["scorecard"],
        "raw_order_rows_before_executable_authority_filter": len(all_orders),
        "raw_trade_rows_before_executable_authority_filter": len(all_trades),
        "order_rows": ledger_write_row_counts["order"],
        "trade_rows": ledger_write_row_counts["trade"],
        "terminal_execution_materialized": terminal_execution_materialized,
        "terminal_execution_materialization_status": (
            "terminal_execution_ledgers_materialized"
            if terminal_execution_materialized
            else "candidate_replay_no_terminal_execution_materialized"
        ),
        "ledger_write_row_counts": dict(ledger_write_row_counts),
        "filtered_non_executable_order_rows": ledger_write_row_counts[
            "filtered_non_executable_order"
        ],
        "filtered_non_executable_trade_rows": ledger_write_row_counts[
            "filtered_non_executable_trade"
        ],
        "filtered_non_executable_order_ledger": output_ledgers[
            "filtered_non_executable_order"
        ],
        "filtered_non_executable_trade_ledger": output_ledgers[
            "filtered_non_executable_trade"
        ],
        "filtered_non_executable_order_reasons": dict(
            sorted(
                Counter(
                    str(
                        row.get("order_filtered_from_executable_ledger_reason")
                        or "missing"
                    )
                    for row in filtered_non_executable_orders
                ).items()
            )
        ),
        "filtered_non_executable_trade_reasons": dict(
            sorted(
                Counter(
                    str(
                        row.get("trade_filtered_from_executable_ledger_reason")
                        or "missing"
                    )
                    for row in filtered_non_executable_trades
                ).items()
            )
        ),
        "oracle_rows": ledger_write_row_counts["oracle"],
        "profit_harvest_authority_blocker_rows": ledger_write_row_counts[
            "profit_harvest_authority_blocker"
        ],
        "profit_harvest_selected_loser_positive_diagnostic_blocker_rows": sum(
            1
            for row in profit_harvest_blocker_rows
            if row.get("profit_harvest_authority_blocker_status")
            == "selected_loser_positive_profit_harvest_diagnostic_needs_ordered_tick"
        ),
        "m1_proxy_ordered_tick_proof_blocker_rows": sum(
            1
            for row in profit_harvest_blocker_rows
            if row.get("m1_proxy_replay_authority") is True
            and row.get("ordered_tick_proof_required") is True
        ),
        "profit_harvest_ordered_tick_truth_rows": sum(
            1
            for row in all_oracles
            if row.get("ordered_tick_truth_satisfied") is True
        ),
        **execution_disposition_summary,
        "packet_sidecar_rows": ledger_write_row_counts["packet_sidecar"],
        "progress_rows": ledger_write_row_counts["progress"],
        "denominator_bridge_rows": ledger_write_row_counts["denominator_bridge"],
        "label_join_rows": ledger_write_row_counts["label_join"],
        "day_summaries": day_summaries,
        **bridge_summary,
        "selected_package_replay_extension_materialized": bool(all_candidates),
        "selected_package_denominator_use_allowed": (
            bridge_summary.get("selected_package_denominator_use_allowed_rows", 0) > 0
            and args.decision_time_source != "pending-created-labels"
        ),
        "training_use_allowed": False,
        "final_package_selected": False,
        "final_package_selection_allowed": False,
        "live_trading_enabled": False,
        "no_live_broker_mutation": True,
        "summary_hash_sha256": stable_sha256(
            {
                "day_summaries": day_summaries,
                "bridge_summary": bridge_summary,
                "profit_harvest_authority_blocker_rows": ledger_write_row_counts[
                    "profit_harvest_authority_blocker"
                ],
                "source_complete": source_complete,
            }
        ),
    }
    if args.decision_time_source == "pending-created-labels":
        summary.update(
            {
                "exact_decision_time_recovery_allowed": False,
                "pending_created_proxy_replay_only": True,
                "pending_created_window_truth_status": (
                    "source_bound_stable_window_proxy_only_not_recovered_original_decision_time"
                ),
                "source_truth_scope": SOURCE_TRUTH_SCOPE,
            }
        )
    write_json(ROUTE / summary_file(output_prefix), summary)
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0 if source_complete else 1


def hydrate_with_boundary(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "schema": "gtos.final_moonshot.denominator_to_deployment.selected_package_replay_bridge.source_hydration.v1",
            "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
            "broker_mutation": False,
            "paid_api_call": False,
            "remote_push": False,
            **dict(row),
        }
        for row in rows
    ]


if __name__ == "__main__":
    if _truthy(os.environ.get("GTOS_REPLAY_BRIDGE_DISABLE_CYCLIC_GC", "1")):
        gc.disable()
    raise SystemExit(main())
