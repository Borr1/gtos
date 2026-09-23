"""Forward-capture research helpers.

These helpers define schema-stable append-only rows for forward shadow
collection. They are not imported by live trading decisions unless a caller
explicitly chooses to write a research row, and every writer is fail-open.
"""

from __future__ import annotations

import json
import hashlib
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.components.gtos_vnext_event_fields import (
    enrich_cp281_event_contract_fields,
)
from src.research_infra.sierra_proxy_registry import (
    registry_entry,
    sierra_proxy_by_symbol,
    sierra_source_status_by_symbol,
)
from src.research_infra.m15_choch_diagnostics import (
    m15_choch_decision_diagnostic,
)

try:  # pragma: no cover - exercised on Windows in production
    import msvcrt
except ImportError:  # pragma: no cover - non-Windows test/dev fallback
    msvcrt = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

RESULT_USE_STATUS = "RESULT_MATERIALIZATION_REQUIRED"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
INTERNAL_PENDING_ORDER_MODE = "INTERNAL_CANDLE_POLLED_INTENT"
_JSONL_LOCK_RETRIES = 200
_JSONL_LOCK_SLEEP_SECONDS = 0.025

EVIDENCE_LABELS = {
    "BROKER_ACTUAL_R",
    "INTERNAL_LIMIT_LIFECYCLE",
    "SYNTHETIC_PATH_R",
    "FUTURES_PROXY_TRANSFER",
    "SAME_MARKET_SOURCE_TRANSFER",
    "CROSS_INSTRUMENT_CONTEXT",
    "FORWARD_SHADOW",
    "DISCOVERY_ONLY",
    "CONTROL_ONLY",
}

COMMON_METADATA_FIELDS = (
    "schema_version",
    "created_at_utc",
    "symbol",
    "broker_symbol",
    "source_symbol",
    "symbol_family",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "source_path_sha256",
    "source_file_sha256",
    "source_component",
    "selected_side",
    "session",
    "kill_zone",
    "side",
    "regime",
    "candidate_id",
    "trade_id",
    "evidence_class",
    "decision_time_utc",
    "asof_cutoff_utc",
    "source_file",
    "source_hash",
    "no_leak_status",
    "result_use_status",
)

V2B_FORWARD_PAIR_PATH = "shadow_logs/v2b_forward_pairs.jsonl"
PREFILL_DELIVERY_PATH = "shadow_logs/prefill_delivery_path.jsonl"
FVG_OB_CONFLUENCE_PATH = "shadow_logs/fvg_ob_confluence.jsonl"
CONTEXT_CONTROL_PATH = "shadow_logs/context_control_ledger.jsonl"
STRATEGY_FOLLOW_PATH = "shadow_logs/strategy_follow_candidates.jsonl"
STRATEGY_FOLLOW_EVALUATION_PATH = "shadow_logs/strategy_follow_evaluations.jsonl"
NOFILL_FORWARD_SOURCE_CAPTURE_PATH = "shadow_logs/nofill_forward_source_capture.jsonl"
NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION = "nofill_forward_source_capture_v1"
MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE_PATH = "shadow_logs/moonshot_selected_action_source_capture.jsonl"
MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE_SCHEMA_VERSION = "moonshot_selected_action_source_capture_v1"
SCID_FORWARD_SOURCE_CAPTURE_PATH = "shadow_logs/scid_forward_source_capture.jsonl"
SCID_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION = "scid_forward_source_capture_v1"
SCID_FORWARD_SOURCE_CAPTURE_ROUTE_ID = "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE"
SCID_FORWARD_SOURCE_CAPTURE_EVIDENCE_CLASS = (
    "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY"
)

SCID_CAPTURE_GROUPS = (
    "baseline_control_fields",
    "framework_setup_family",
    "future_orderflow_depth_proxy_requirements",
    "intended_entry_reference",
    "intended_side_direction",
    "intended_stop_reference",
    "intended_target_reference",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "poi_type_bounds_source",
)

SCID_COMMON_FIELDS = (
    "schema_version",
    "route_id",
    "evidence_class",
    "promotion_verdict",
    "result_use_status",
    "validation_result_status",
    "outcome_result_rows_status",
    "broker_runtime_change_status",
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_raw_market_data_blob_commit",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "candidate_input_row_id",
    "duplicate_proxy_denominator_key",
    "field_group",
    "decision_asof_utc",
    "source_observed_asof_utc",
    "source_identifier",
    "source_hash",
    "source_symbol",
    "symbol",
    "symbol_family",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
    "source_path_sha256",
    "source_file_sha256",
    "source_hash_contract",
    "source_component",
    "source_hash_policy",
    "redaction_policy_id",
    "forbidden_value_policy_id",
    "missing_status_policy",
    "field_status",
    "downstream_g12_acceptance_rule",
)

SCID_GROUP_FIELDS = {
    "baseline_control_fields": (
        "partition_assignment",
        "symbol",
        "session_bucket",
        "time_of_day_bucket",
        "baseline_family_session_only_volatility_only_random_proxy_matched",
        "baseline_assignment_seed",
        "baseline_duplicate_policy_id",
    ),
    "framework_setup_family": (
        "frameworks_evaluated",
        "framework_qualified_flags",
        "selected_framework_or_none",
        "setup_family",
        "framework_tiebreak_rule_id",
        "framework_source_snapshot_hash",
    ),
    "future_orderflow_depth_proxy_requirements": (
        "proxy_instrument",
        "proxy_contract_month",
        "source_family_scid_depth_mbo_mbp_other",
        "source_file_pointer_or_vendor_cache_id",
        "proxy_mapping_version",
        "publication_or_capture_asof_utc",
        "derived_feature_schema_version",
        "orderflow_proxy_availability_status",
    ),
    "intended_entry_reference": (
        "entry_reference_type_market_limit_zone_midpoint_other",
        "entry_reference_price",
        "entry_reference_time_utc",
        "entry_source_timeframe",
        "entry_source_bar_hash_or_mso_snapshot_hash",
    ),
    "intended_side_direction": (
        "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY",
        "side_source_component",
        "side_source_rule_or_model_hash",
        "side_emission_reason_code",
    ),
    "intended_stop_reference": (
        "stop_reference_price",
        "stop_reference_type",
        "stop_buffer_rule_id",
        "stop_source_structure_id",
        "stop_source_snapshot_hash",
    ),
    "intended_target_reference": (
        "target_reference_price",
        "target_reference_type",
        "target_rule_id",
        "risk_reward_reference",
        "target_source_snapshot_hash",
    ),
    "lifecycle_fill_cancel_expiry_source_status": (
        "pending_intent_id",
        "source_event_type_created_updated_expired_cancelled_replaced_no_order",
        "source_event_utc",
        "source_event_clock_basis",
        "intent_state_before",
        "intent_state_after",
        "redacted_order_bridge_hash_optional",
    ),
    "lower_timeframe_asof_path_availability": (
        "ltf_timeframes_available",
        "ltf_source_file_pointer_or_cache_id",
        "ltf_source_hash",
        "decision_minus_window_start_utc",
        "bars_present_by_timeframe",
        "asof_path_descriptor_version",
        "ltf_availability_status",
    ),
    "poi_type_bounds_source": (
        "poi_type_enum_ob_fvg_breaker_swing_other_none",
        "poi_lower_bound",
        "poi_upper_bound",
        "poi_source_timeframe",
        "poi_source_bar_ids",
        "mso_snapshot_hash",
        "poi_detection_rule_version",
    ),
}

SCID_REQUIRED_FIELDS = {
    group: SCID_COMMON_FIELDS + SCID_GROUP_FIELDS[group] for group in SCID_CAPTURE_GROUPS
}
SCID_SCHEMA_FIELD_NAMES = set(SCID_COMMON_FIELDS) | {
    field for fields in SCID_GROUP_FIELDS.values() for field in fields
}

SCID_BOUNDARY_FALSE_FIELDS = (
    "validation_result_status",
    "outcome_result_rows_status",
    "broker_runtime_change_status",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_raw_market_data_blob_commit",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
)

SCID_SOURCE_HASH_STRICT = "STRICT_SHA256_REQUIRED"
SCID_SOURCE_HASH_DEFERRED = "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
SCID_REDACTION_POLICY_ID = "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"
SCID_FORBIDDEN_VALUE_POLICY_ID = "SCID_FORWARD_CAPTURE_FORBIDDEN_SURFACE_FAIL_CLOSED_V1"
SCID_MISSING_STATUS_POLICY = "SCID_FORWARD_CAPTURE_MISSING_FIELDS_FAIL_CLOSED_V1"
SCID_DOWNSTREAM_G12_ACCEPTANCE_RULE = "SOURCE_CAPTURE_ONLY_RESULT_ROWS_NOT_OPENED"
SCID_FIELD_CAPTURED = "CAPTURED_SOURCE_SAFE"
SCID_FIELD_UNAVAILABLE = "SOURCE_UNAVAILABLE_FAIL_CLOSED"
SCID_FIELD_PROSPECTIVE = "PROSPECTIVE_CAPTURE_REQUIRED"
SCID_FIELD_FORBIDDEN = "FORBIDDEN_FAIL_CLOSED"

SCID_ENUMS = {
    "field_status": {
        SCID_FIELD_CAPTURED,
        SCID_FIELD_UNAVAILABLE,
        SCID_FIELD_PROSPECTIVE,
        SCID_FIELD_FORBIDDEN,
    },
    "source_hash_policy": {
        SCID_SOURCE_HASH_STRICT,
        SCID_SOURCE_HASH_DEFERRED,
        "SELF_REFERENTIAL_MANIFEST_HASH_NON_BLOCKING",
    },
    "baseline_family_session_only_volatility_only_random_proxy_matched": {
        "session_only",
        "volatility_only",
        "random_proxy_matched",
    },
    "source_family_scid_depth_mbo_mbp_other": {
        "scid",
        "depth",
        "mbo",
        "mbp",
        "other",
        "unavailable",
    },
    "orderflow_proxy_availability_status": {
        "AVAILABLE",
        "UNAVAILABLE_FAIL_CLOSED",
    },
    "entry_reference_type_market_limit_zone_midpoint_other": {
        "market",
        "limit",
        "zone_midpoint",
        "other",
    },
    "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY": {
        "LONG",
        "SHORT",
        "NEUTRAL",
        "NO_STRATEGY",
    },
    "source_event_type_created_updated_expired_cancelled_replaced_no_order": {
        "created",
        "updated",
        "expired",
        "cancelled",
        "replaced",
        "no_order",
    },
    "ltf_availability_status": {
        "AVAILABLE",
        "UNAVAILABLE_FAIL_CLOSED",
    },
    "poi_type_enum_ob_fvg_breaker_swing_other_none": {
        "ob",
        "fvg",
        "breaker",
        "swing",
        "other",
        "none",
    },
}

SCID_NULLABLE_FIELDS = {
    "selected_framework_or_none",
    "proxy_instrument",
    "proxy_contract_month",
    "source_file_pointer_or_vendor_cache_id",
    "proxy_mapping_version",
    "derived_feature_schema_version",
    "source_hash",
    "ltf_source_file_pointer_or_cache_id",
    "ltf_source_hash",
    "intent_state_before",
    "redacted_order_bridge_hash_optional",
    "poi_lower_bound",
    "poi_upper_bound",
}

SCID_FORBIDDEN_RAW_FIELD_NAMES = {
    "account",
    "account_id",
    "account_number",
    "account_login",
    "account_name",
    "account_balance",
    "account_equity",
    "broker_account_id",
    "order",
    "order_id",
    "order_ticket",
    "mt5_order_ticket",
    "pending_ticket",
    "trade_state_ticket",
    "deal",
    "deal_id",
    "position",
    "position_id",
    "position_ticket",
    "history_deal",
    "history_order",
    "actual_r",
    "broker_actual_r",
    "synthetic_path_r",
    "realized_r",
    "realized_pnl",
    "pnl",
    "profit",
    "loss",
    "slippage",
    "slippage_price",
    "win_loss",
    "result_label",
    "trade_result",
    "expectancy",
    "win_rate",
}

SCID_FORBIDDEN_KEY_FRAGMENTS = (
    "account_id",
    "account_login",
    "account_number",
    "broker_account",
    "order_ticket",
    "mt5_order",
    "pending_ticket",
    "trade_state_ticket",
    "deal_id",
    "history_deal",
    "history_order",
    "position_id",
    "position_ticket",
    "actual_r",
    "synthetic_path_r",
    "realized_r",
    "realized_pnl",
    "slippage",
    "win_loss",
    "result_label",
    "trade_result",
    "expectancy",
    "win_rate",
)

SIERRA_DEPTH_ROOT = Path("C:/SierraChart/Data/MarketDepthData")
SIERRA_PROXY_BY_SYMBOL = sierra_proxy_by_symbol()
SIERRA_SOURCE_STATUS_BY_SYMBOL = sierra_source_status_by_symbol()
DATABENTO_TRIGGER_SYMBOLS = {
    "NAS100": {
        "trigger_family": "NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC",
        "raw_symbols": ["NQ.v.0"],
        "reason": "registered NAS100/NQ forward orderflow diagnostic",
    },
}
SOURCE_BLOCKED_DATABENTO_SYMBOLS = {
    "GBPJPY": "NO_VALIDATED_DIRECT_FUTURES_PROXY_GBPJPY_TWO_BOOK_DESIGN_REQUIRED",
    "XAGUSD": "SI_SOURCE_DEPTH_DEFINITION_BLOCKED",
}
DATABENTO_FORWARD_REQUEST_MANIFEST = (
    "research/databento_orderflow_capture_2026-05-02/"
    "databento_forward_requests_2026-05-04.jsonl"
)
DATABENTO_LIVE_SHADOW_PATH = "shadow_logs/databento_live_confluence.jsonl"

STRUCTURAL_SOURCE_CAPTURE_FIELDS = (
    "standalone_fvg_entry_geometry",
    "fvg_lock_state",
    "swing_protected_lock_level",
    "structural_lock_event_time_price",
    "post_lock_reentry_state",
    "cost_aware_min_r_fields",
)

MOONSHOT_SELECTED_ACTION_STRATEGY_REGISTRY = (
    {
        "strategy_id": "MOONSHOT_NOFILL_FAR_MISS_RETEST_REDESIGN",
        "family": "moonshot_nofill_redesign",
        "evidence_role": "default_off_far_miss_retest_redesign",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_DEFAULT_OFF_FAR_MISS_RETEST_REDESIGN_VARIANT",
        "decision_evidence": "MAIN_ORCH24_MOONSHOT_NOFILL_REDESIGN_SELECTION: 3992 implement-default-off rows, 3992 proxy references, +1389.944864R proxy reference sum, not counted as R.",
        "implementation_candidate": "CAPTURE_AND_SCORE_DEFAULT_OFF_MOONSHOT_FAR_MISS_RETEST_REDESIGN_WITH_SOURCE_GUARDS",
        "source_capture_required_fields": (
            "moonshot_far_miss_retest_control_key",
            "moonshot_no_fill_distance_bucket",
            "moonshot_spread_aware_path_source",
            "moonshot_retest_control_denominator",
        ),
    },
    {
        "strategy_id": "MOONSHOT_NOFILL_FAMILY_SPLIT",
        "family": "moonshot_nofill_redesign",
        "evidence_role": "default_off_nofill_family_split",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_DEFAULT_OFF_NOFILL_FAMILY_SPLIT_VARIANT",
        "decision_evidence": "MAIN_ORCH24_MOONSHOT_NOFILL_REDESIGN_SELECTION: 132 implement-default-off rows, 132 proxy references, +55.777784R proxy reference sum, not counted as R.",
        "implementation_candidate": "CAPTURE_AND_SCORE_DEFAULT_OFF_MOONSHOT_NOFILL_FAMILY_SPLIT_WITH_SOURCE_CONFIDENCE_GUARD",
        "source_capture_required_fields": (
            "moonshot_no_fill_family_key",
            "moonshot_symbol_session_horizon_scope",
            "moonshot_family_split_denominator",
        ),
    },
    {
        "strategy_id": "MOONSHOT_NOFILL_NEAR_MISS_MARKET_ENTRY",
        "family": "moonshot_nofill_redesign",
        "evidence_role": "default_off_near_miss_market_entry",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_DEFAULT_OFF_NEAR_MISS_MARKET_ENTRY_VARIANT",
        "decision_evidence": "MAIN_ORCH24_MOONSHOT_NOFILL_REDESIGN_SELECTION: 374 implement-default-off rows, 374 proxy references, +56.1R proxy reference sum, not counted as R.",
        "implementation_candidate": "CAPTURE_AND_SCORE_DEFAULT_OFF_MOONSHOT_NEAR_MISS_MARKET_ENTRY_VARIANT",
        "source_capture_required_fields": (
            "moonshot_near_miss_market_entry_control_key",
            "moonshot_near_miss_entry_distance_r",
            "moonshot_market_entry_cost_source",
            "moonshot_market_entry_control_denominator",
        ),
    },
    {
        "strategy_id": "MOONSHOT_NOFILL_NEAR_MISS_OFFSET_ENTRY",
        "family": "moonshot_nofill_redesign",
        "evidence_role": "default_off_near_miss_offset_entry",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_DEFAULT_OFF_NEAR_MISS_OFFSET_ENTRY_VARIANT",
        "decision_evidence": "MAIN_ORCH24_MOONSHOT_NOFILL_REDESIGN_SELECTION: 70 implement-default-off rows, 70 proxy references, +10.5R proxy reference sum, not counted as R.",
        "implementation_candidate": "CAPTURE_AND_SCORE_DEFAULT_OFF_MOONSHOT_NEAR_MISS_OFFSET_ENTRY_VARIANT",
        "source_capture_required_fields": (
            "moonshot_near_miss_offset_control_key",
            "moonshot_offset_entry_price_source",
            "moonshot_offset_entry_cost_source",
            "moonshot_offset_control_denominator",
        ),
    },
    {
        "strategy_id": "MOONSHOT_SOURCE_GUARD_SCOPE_CONTROL",
        "family": "moonshot_source_guard",
        "evidence_role": "default_off_source_guard_scope_proxy",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_DEFAULT_OFF_SOURCE_GUARD_SCOPE_PROXY_AND_CONTROL_SCORE",
        "decision_evidence": "MAIN_ORCH24_MOONSHOT_SOURCE_CONTROL_SELECTION plus CONTROL_SCORE_SELECTION: 119 implement-default-off source-guard rows, 119 proxy references, +9.092151R proxy reference sum, not counted as R.",
        "implementation_candidate": "CAPTURE_AND_SCORE_DEFAULT_OFF_MOONSHOT_SOURCE_GUARD_SCOPE_CONTROL",
        "source_capture_required_fields": (
            "moonshot_source_guard_scope_key",
            "moonshot_source_root_coverage_status",
            "moonshot_source_guard_control_denominator",
        ),
    },
    {
        "strategy_id": "MOONSHOT_MARKET_GAP_CONTROL",
        "family": "moonshot_market_gap",
        "evidence_role": "default_off_market_gap_control_proxy",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_DEFAULT_OFF_MARKET_GAP_CONTROL_PROXY_AND_CONTROL_SCORE",
        "decision_evidence": "MAIN_ORCH24_MOONSHOT_SOURCE_CONTROL_SELECTION plus CONTROL_SCORE_SELECTION: 20 implement-default-off market-gap rows, 20 proxy references, +1.013975R proxy reference sum, not counted as R.",
        "implementation_candidate": "CAPTURE_AND_SCORE_DEFAULT_OFF_MOONSHOT_MARKET_GAP_CONTROL",
        "source_capture_required_fields": (
            "moonshot_market_gap_control_key",
            "moonshot_market_gap_event_source",
            "moonshot_market_gap_control_denominator",
        ),
    },
    {
        "strategy_id": "MOONSHOT_DEFAULT_OFF_SCORER_APPLICATION_CONTROL",
        "family": "moonshot_scorer_application",
        "evidence_role": "default_off_scorer_application_control",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_DEFAULT_OFF_CONTROL_SCORE_SCORER_APPLICATION",
        "decision_evidence": "MAIN_ORCH24_MOONSHOT_CONTROL_SCORE_SELECTION: 10 implement-default-off scorer-application rows, 10 proxy references, +2.909544R proxy reference sum, not counted as R; exact-denominator source repairs remain separate.",
        "implementation_candidate": "CAPTURE_AND_SCORE_DEFAULT_OFF_MOONSHOT_SCORER_APPLICATION_CONTROL",
        "source_capture_required_fields": (
            "moonshot_scorer_application_id",
            "moonshot_scorer_application_source_hash",
            "moonshot_scorer_exact_control_denominator",
        ),
    },
)

FOLLOW_STRATEGY_REGISTRY = (
    {
        "strategy_id": "LIVE_AI_J46_J49_BASELINE_COMPARATOR",
        "family": "current_live_baseline",
        "evidence_role": "baseline_comparator",
        "result_use_status": "LIVE_PRODUCTION_PATH",
    },
    {
        "strategy_id": "J46_J49_PORTFOLIO_POLICY",
        "family": "portfolio_policy",
        "evidence_role": "dsr_validated_research_comparator",
        "result_use_status": "RESEARCH_ONLY",
    },
    {
        "strategy_id": "S79_UNIFORM_FN_RISK_POLICY",
        "family": "risk_policy",
        "evidence_role": "dsr_validated_risk_comparator",
        "result_use_status": "SHIPPED_POLICY_CONTEXT",
    },
    {
        "strategy_id": "V2_STRUCT_SWING_PROTECTED",
        "family": "v2_structural_selector",
        "evidence_role": "discovery_comparator_concentration_blocked",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_SHADOW_SCORER_SWING_PROTECTED_STOP_DEFAULT_OFF_WITH_ROW_LEVEL_SOURCE_GATES",
        "decision_evidence": "MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR: swing-protected source-repair rows close 190->0; current repaired target rows split into 87 numeric proxy rows (+36.5R), 28 ambiguity-excluded default-off rows, and 75 unprotected-stop kills.",
        "implementation_candidate": "KEEP_DEFAULT_OFF_SWING_PROTECTED_STOP_PATH_SCORER_WITH_DECISION_TIME_STRUCTURAL_CAPTURE_OR_TICK_DERIVATION",
    },
    {
        "strategy_id": "V2_STRUCT_FVG_MID_EDGE",
        "family": "v2_structural_selector",
        "evidence_role": "discovery_comparator",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_SHADOW_SCORER_STANDALONE_FVG_POI_DEFAULT_OFF_WITH_ROW_LEVEL_SOURCE_GATES",
        "decision_evidence": "MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR: true standalone-FVG source-repair rows close 3->0 for this strategy; repaired target rows split into 1 numeric proxy row (-1.0R) and 2 ambiguity-excluded default-off rows while non-FVG POI kills stay excluded.",
        "implementation_candidate": "KEEP_DEFAULT_OFF_STANDALONE_FVG_POI_PATH_SCORER_WITH_DECISION_TIME_FVG_GEOMETRY_OR_TICK_DERIVATION",
    },
    {
        "strategy_id": "V2_STRUCT_OB_BOUNDARY",
        "family": "v2_structural_selector",
        "evidence_role": "cleanest_v2b_candidate",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "PRESERVE_DEFAULT_OFF_SHADOW_OB_BOUNDARY_PROXY_ONLY",
        "decision_evidence": "MAIN_ORCH24_V2_V2B_DUPLICATE_AWARE_REPLAY: n=253 per strategy, mean_proxy_r=0.0177865613; replay/shadow only.",
    },
    {
        "strategy_id": "V2_STRUCT_COMPOSITE_ANY",
        "family": "v2_structural_selector",
        "evidence_role": "overlock_warning_comparator",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_SHADOW_SCORER_STRUCTURAL_METADATA_SHARED_PATH_DEFAULT_OFF_WITH_AMBIGUITY_EXCLUSION",
        "decision_evidence": "MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR: structural-lock source-repair rows close 760->0; each non-swing structural strategy has 188 numeric proxy rows (+59.0R) and 86 ambiguity exclusions.",
        "implementation_candidate": "KEEP_DEFAULT_OFF_STRUCTURAL_METADATA_SHARED_PATH_PROXY_SCORER_AND_DESIGN_EXACT_LOCK_REENTRY_SCORER",
    },
    {
        "strategy_id": "V2B_OB_BOUNDARY_PROSPECTIVE",
        "family": "v2b_forward_validation",
        "evidence_role": "primary_forward_pair_target",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "PRESERVE_DEFAULT_OFF_SHADOW_OB_BOUNDARY_PROXY_ONLY",
        "decision_evidence": "MAIN_ORCH24_V2_V2B_DUPLICATE_AWARE_REPLAY: n=253 per strategy, mean_proxy_r=0.0177865613; replay/shadow only.",
    },
    {
        "strategy_id": "V3_FVG_ONLY_RESCUE_RISK_BANK",
        "family": "v3_risk_bank",
        "evidence_role": "positive_same_dataset_discovery_candidate",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_SHADOW_SCORER_STANDALONE_FVG_POI_DEFAULT_OFF_WITH_ROW_LEVEL_SOURCE_GATES",
        "decision_evidence": "MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR: true standalone-FVG source-repair rows close 3->0 for this strategy; repaired target rows split into 1 numeric proxy row (-1.0R) and 2 ambiguity-excluded default-off rows while non-FVG POI kills stay excluded.",
        "implementation_candidate": "KEEP_DEFAULT_OFF_STANDALONE_FVG_POI_PATH_SCORER_WITH_DECISION_TIME_FVG_GEOMETRY_OR_TICK_DERIVATION",
    },
    {
        "strategy_id": "V3_FVG_THEN_OB_TAIL_RISK_BANK",
        "family": "v3_risk_bank",
        "evidence_role": "structurally_clean_discovery_candidate",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_SHADOW_SCORER_STRUCTURAL_METADATA_SHARED_PATH_DEFAULT_OFF_WITH_AMBIGUITY_EXCLUSION",
        "decision_evidence": "MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR: structural-lock source-repair rows close 760->0; each non-swing structural strategy has 188 numeric proxy rows (+59.0R) and 86 ambiguity exclusions.",
        "implementation_candidate": "KEEP_DEFAULT_OFF_STRUCTURAL_METADATA_SHARED_PATH_PROXY_SCORER_AND_DESIGN_EXACT_LOCK_REENTRY_SCORER",
    },
    {
        "strategy_id": "V3_OB_LOCK_PULLBACK_RISK_BANK",
        "family": "v3_risk_bank",
        "evidence_role": "locked_progress_reentry_comparator",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_SHADOW_SCORER_STRUCTURAL_METADATA_SHARED_PATH_DEFAULT_OFF_WITH_AMBIGUITY_EXCLUSION",
        "decision_evidence": "MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR: structural-lock source-repair rows close 760->0; each non-swing structural strategy has 188 numeric proxy rows (+59.0R) and 86 ambiguity exclusions.",
        "implementation_candidate": "KEEP_DEFAULT_OFF_STRUCTURAL_METADATA_SHARED_PATH_PROXY_SCORER_AND_DESIGN_EXACT_LOCK_REENTRY_SCORER",
    },
    {
        "strategy_id": "V3_OB_LOCK_COST_AWARE_MIN_R",
        "family": "v3_risk_bank",
        "evidence_role": "cost_aware_reentry_comparator",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_SHADOW_SCORER_STRUCTURAL_METADATA_SHARED_PATH_DEFAULT_OFF_WITH_AMBIGUITY_EXCLUSION",
        "decision_evidence": "MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR: structural-lock source-repair rows close 760->0; each non-swing structural strategy has 188 numeric proxy rows (+59.0R) and 86 ambiguity exclusions.",
        "implementation_candidate": "KEEP_DEFAULT_OFF_STRUCTURAL_METADATA_SHARED_PATH_PROXY_SCORER_AND_DESIGN_EXACT_LOCK_REENTRY_SCORER",
    },
    {
        "strategy_id": "FVG_OB_CONFLUENCE_OB_AFTER_FVG",
        "family": "fvg_ob_confluence",
        "evidence_role": "forward_confluence_bucket",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "KEEP_DEFAULT_OFF_FVG_OB_BUCKET_SHARED_PATH_PROXY_SCORER_NO_EXACT_BOUNDS_CLAIM",
        "decision_evidence": "MAIN_ORCH24_ACTION_AFTER_FVG_OB_BUCKET_REPAIR: FVG/OB source-repair rows close 190->0; 189 single-family bucket rows killed, one both-fire row kept as -1.0R bucket-only shared-path proxy.",
        "implementation_candidate": "KEEP_SHARED_PATH_PROXY_SCORER_DEFAULT_OFF_NO_STANDALONE_FVG_ENTRY_CLAIM",
    },
    {
        "strategy_id": "PREFILL_DELIVERY_REVERSAL_PATH",
        "family": "pre_fill_path",
        "evidence_role": "owner_delivery_leg_reversal_hypothesis",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "MERGE_PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE",
        "decision_evidence": "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD: 3426 action rows preserved; 13 prefill TP-after-fill rows reference entry-offset owner proxy only, +8.66977687R referenced but not duplicated; 168 no-fill controls preserve wider-retest/source-cost-fill repair paths. Largest current positive cluster is US30_cash|2026-05-08 with 11/13 owner rows and +7.33544301R, so this remains cluster-capped until independent rows exist.",
        "implementation_candidate": "PREFILL_TP_AFTER_FILL_CONTEXT_MERGED_TO_ENTRY_OFFSET_CLUSTER_GUARD",
    },
    {
        "strategy_id": "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER",
        "family": "entry_geometry_fillability",
        "evidence_role": "default_off_entry_offset_challenger",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_CONCENTRATION_GUARDED_CANDIDATE",
        "decision_evidence": "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD: 13 entry-offset owner rows remain counted once, +8.66977687R; 3 effective symbol-date clusters; largest cluster US30_cash|2026-05-08 has 11 rows, +7.33544301R, row share 0.84615385 and proxy share 0.84609363. Keep default-off scorer with source gates and cluster cap.",
        "implementation_candidate": "ENTRY_OFFSET_050R_CLUSTER_GUARDED_DEFAULT_OFF_CHALLENGER",
    },
    {
        "strategy_id": "PENDING_LIMIT_LIFECYCLE",
        "family": "execution_lifecycle",
        "evidence_role": "live_flow_shadow_truth",
        "result_use_status": "IMPLEMENTED_SHADOW_ONLY",
        "branch_decision": "KEEP_PENDING_LIFECYCLE_SCORER_WITH_NOT_APPLICABLE_TOUCH_REPAIR_AND_DECISION_SPREAD_FORWARD_CAPTURE",
        "decision_evidence": "MAIN_ORCH24_PENDING_LIFECYCLE_NOT_APPLICABLE_TOUCH_REPAIR: 274 current rows, 39 internal pending lifecycle rows, 197 numeric proxy rows, +50.0R proxy sum, missing source cells 184->78; remaining historical source gap is decision_spread value/unit for 39 rows, already fixed prospectively by PendingLimitIntent decision-spread capture.",
        "implementation_candidate": "KEEP_SHADOW_ONLY_PENDING_LIFECYCLE_SCORER_WITH_DECISION_SPREAD_FORWARD_CAPTURE_AND_NOT_APPLICABLE_TOUCH_CLASSIFICATION",
    },
    {
        "strategy_id": "NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC",
        "family": "orderflow_depth",
        "evidence_role": "nas100_specific_forward_diagnostic",
        "result_use_status": RESULT_USE_STATUS,
        "branch_decision": "PRESERVE_DIAGNOSTIC_ONLY_WAIT_FOR_LICENSE_AND_SAMPLE_FLOORS",
        "decision_evidence": "MAIN_ORCH24_ORDERFLOW_SIERRA_DIAGNOSTIC_CAPABILITY: Databento live license blocked; Sierra depth context is diagnostic only.",
    },
    *MOONSHOT_SELECTED_ACTION_STRATEGY_REGISTRY,
)

CONFLUENCE_BUCKETS = {
    "both_fvg_and_ob_fire",
    "fvg_only",
    "ob_only",
    "neither",
    "ob_after_fvg",
    "fvg_after_ob",
    "composite_overlock",
    "disagreement",
    "no_poi",
}

AMBIGUITY_STATES = {
    "no_ltf_data",
    "same_bar_tp_sl_ambiguity",
    "no_fill",
    "fill_before_invalidation",
    "invalidation_before_fill",
    "tp_before_sl",
    "sl_before_tp",
    "unresolved",
}

POST_OUTCOME_FIELD_NAMES = {
    "actual_r",
    "broker_actual_r",
    "synthetic_path_r",
    "realized_r",
    "outcome_r",
    "tp_hit",
    "sl_hit",
    "winner",
    "loser",
}

NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUSES = {
    "CLOCK_SOURCE_MISSING_FAIL_CLOSED",
    "CONTROL_FIELD_MISSING_FAIL_CLOSED",
    "EVENT_ORDER_METHOD_MISSING_FAIL_CLOSED",
    "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
    "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
    "LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED",
    "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
    "SOURCE_FIELD_MISSING_FAIL_CLOSED",
    "WRITE_CLOCK_MISSING_FAIL_CLOSED",
}

NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES = {
    "account_history",
    "account_id",
    "actual_r",
    "broker_actual_r",
    "deal",
    "deal_id",
    "execution_quality",
    "mt5_order_ticket",
    "order_ticket",
    "pending_ticket",
    "position",
    "position_id",
    "result",
    "slippage_price",
    "trade_state_ticket",
}

NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS = (
    "capture_observed_at_utc",
    "capture_write_started_at_utc",
    "capture_write_completed_at_utc",
    "capture_latency_ms",
    "capture_clock_source_status",
    "capture_clock_skew_ms",
    "capture_clock_skew_status",
    "capture_timestamp_derivation_rule",
    "pending_order_mode_source_safe",
    "pending_order_mode_status",
    "broker_pending_order_created_status",
    "native_pending_order_type_source_safe",
    "native_pending_order_type_status",
    "raw_ticket_field_present_status",
    "mt5_order_ticket_redaction_status",
    "decision_spread_status",
    "decision_spread_value_source_safe",
    "decision_spread_unit",
    "entry_touch_spread_status",
    "entry_touch_spread_value_source_safe",
    "spread_source_hash",
    "slippage_label_status",
    "slippage_value_redaction_status",
    "execution_quality_label_status",
    "execution_quality_value_redaction_status",
    "cost_testing_gate_status",
    "pending_intent_created_utc",
    "pending_horizon_start_utc",
    "pending_horizon_end_utc",
    "cancel_expiry_utc",
    "cancel_expiry_reason_status",
    "entry_touch_first_utc",
    "side_aware_entry_touch_status",
    "terminal_area_touch_status",
    "terminal_area_first_touch_utc",
    "protective_area_touch_status",
    "protective_area_first_touch_utc",
    "event_order_resolution_method",
    "same_tick_same_bar_ambiguity_status",
    "lower_tf_coverage_window_start_utc",
    "lower_tf_coverage_window_end_utc",
    "missing_coverage_intervals",
    "row_level_denominator_member",
    "nofill_duplicate_key_count_member",
    "duplicate_group_id_count_member",
    "nofill_duplicate_key_sha256",
    "duplicate_group_id_sha256",
    "session_tag",
    "regime_context_status",
    "sample_floor_policy_id",
    "perturbation_ready_bucket",
    "kill_switch_observability_status",
    "source_artifact_hash",
    "parser_code_hash",
    "forbidden_field_scan_status",
)

NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS = (
    "capture_write_started_at_utc",
    "capture_write_completed_at_utc",
    "capture_latency_ms",
    "capture_clock_source_status",
    "capture_clock_skew_ms",
    "capture_clock_skew_status",
    "native_pending_order_type_source_safe",
    "native_pending_order_type_status",
    "decision_spread_status",
    "decision_spread_value_source_safe",
    "decision_spread_unit",
    "entry_touch_spread_status",
    "entry_touch_spread_value_source_safe",
    "spread_source_hash",
    "pending_horizon_start_utc",
    "pending_horizon_end_utc",
    "terminal_area_touch_status",
    "terminal_area_first_touch_utc",
    "protective_area_touch_status",
    "protective_area_first_touch_utc",
)

NOFILL_FORWARD_SOURCE_CAPTURE_MISSING_STATUS_BY_FIELD = {
    "capture_observed_at_utc": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
    "capture_write_started_at_utc": "WRITE_CLOCK_MISSING_FAIL_CLOSED",
    "capture_write_completed_at_utc": "WRITE_CLOCK_MISSING_FAIL_CLOSED",
    "capture_latency_ms": "WRITE_CLOCK_MISSING_FAIL_CLOSED",
    "capture_clock_source_status": "CLOCK_SOURCE_MISSING_FAIL_CLOSED",
    "capture_clock_skew_ms": "CLOCK_SOURCE_MISSING_FAIL_CLOSED",
    "capture_clock_skew_status": "CLOCK_SOURCE_MISSING_FAIL_CLOSED",
    "capture_timestamp_derivation_rule": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
    "pending_order_mode_source_safe": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
    "pending_order_mode_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
    "broker_pending_order_created_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
    "native_pending_order_type_source_safe": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
    "native_pending_order_type_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
    "raw_ticket_field_present_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
    "mt5_order_ticket_redaction_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
    "decision_spread_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
    "decision_spread_value_source_safe": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
    "decision_spread_unit": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
    "entry_touch_spread_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
    "entry_touch_spread_value_source_safe": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
    "spread_source_hash": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
    "slippage_label_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
    "slippage_value_redaction_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
    "execution_quality_label_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
    "execution_quality_value_redaction_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
    "cost_testing_gate_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
    "pending_intent_created_utc": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
    "pending_horizon_start_utc": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
    "pending_horizon_end_utc": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
    "cancel_expiry_utc": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
    "cancel_expiry_reason_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
    "entry_touch_first_utc": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
    "side_aware_entry_touch_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
    "terminal_area_touch_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
    "terminal_area_first_touch_utc": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
    "protective_area_touch_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
    "protective_area_first_touch_utc": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
    "event_order_resolution_method": "EVENT_ORDER_METHOD_MISSING_FAIL_CLOSED",
    "same_tick_same_bar_ambiguity_status": "EVENT_ORDER_METHOD_MISSING_FAIL_CLOSED",
    "lower_tf_coverage_window_start_utc": "LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED",
    "lower_tf_coverage_window_end_utc": "LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED",
    "missing_coverage_intervals": "LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED",
    "row_level_denominator_member": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
    "nofill_duplicate_key_count_member": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
    "duplicate_group_id_count_member": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
    "nofill_duplicate_key_sha256": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
    "duplicate_group_id_sha256": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
    "session_tag": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
    "regime_context_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
    "sample_floor_policy_id": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
    "perturbation_ready_bucket": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
    "kill_switch_observability_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
    "source_artifact_hash": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
    "parser_code_hash": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
    "forbidden_field_scan_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
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
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(val) for val in value]
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def _sequence_dump(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return []
    try:
        items = list(value)
    except TypeError:
        return []
    return [_json_safe(_safe_model_dump(item) or item) for item in items]


def _timeframe_state_snapshot(mso: Any, tf_name: str) -> dict[str, Any]:
    tfs = _safe_get(mso, "timeframes", {}) or {}
    try:
        tf = tfs.get(tf_name) if hasattr(tfs, "get") else tfs[tf_name]
    except Exception:
        tf = None
    if tf is None:
        return {"timeframe": tf_name, "source_status": "TIMEFRAME_NOT_PRESENT_IN_MSO"}

    structure = _safe_get(tf, "structure")
    protected_swing = _safe_get(structure, "protected_swing") if structure is not None else None
    return {
        "timeframe": tf_name,
        "source_status": "DECISION_TIME_MSO_TIMEFRAME_CAPTURED",
        "structure": _json_safe(_safe_model_dump(structure) or structure) if structure is not None else {},
        "protected_swing": _json_safe(_safe_model_dump(protected_swing) or protected_swing)
        if protected_swing is not None
        else None,
        "structure_events": _sequence_dump(_safe_get(tf, "structure_events", []) or []),
        "swings": _sequence_dump(_safe_get(tf, "swings", []) or []),
        "order_blocks": _sequence_dump(_safe_get(tf, "order_blocks", []) or []),
        "breaker_blocks": _sequence_dump(_safe_get(tf, "breaker_blocks", []) or []),
        "fair_value_gaps": _sequence_dump(_safe_get(tf, "fair_value_gaps", []) or []),
        "atr_14": _safe_get(tf, "atr_14"),
        "avg_candle_body": _safe_get(tf, "avg_candle_body"),
    }


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _price_inside_bounds(price: float | None, low: float | None, high: float | None) -> bool:
    if price is None or low is None or high is None:
        return False
    lo = min(low, high)
    hi = max(low, high)
    tolerance = max(abs(price) * 1e-6, 1e-8)
    return lo - tolerance <= price <= hi + tolerance


def _trade_side_zone_type(side: Any) -> str | None:
    side_text = str(side or "").upper()
    if side_text == "LONG":
        return "bullish"
    if side_text == "SHORT":
        return "bearish"
    return None


def _candidate_price_refs(fields: dict[str, Any]) -> list[tuple[str, float]]:
    h1_setup = fields.get("h1_setup") or {}
    tp = fields.get("trade_parameters") or {}
    refs: list[tuple[str, float]] = []
    for label, value in (
        ("h1_poi_price_level", h1_setup.get("poi_price_level")),
        ("entry_price", tp.get("entry_price")),
    ):
        parsed = _safe_float(value)
        if parsed is not None:
            refs.append((label, parsed))
    return refs


def _zone_time_value(value: Any) -> tuple[int, str]:
    if value is None:
        return (1, "")
    return (0, str(value))


def _order_block_payload(ob: dict[str, Any], *, matched_by: str) -> dict[str, Any] | None:
    low = _safe_float(ob.get("low"))
    high = _safe_float(ob.get("high"))
    if low is None or high is None:
        return None
    return {
        "low": min(low, high),
        "high": max(low, high),
        "type": ob.get("type"),
        "formation_time": ob.get("formation_time"),
        "causing_bos_index": ob.get("causing_bos_index"),
        "causing_event_type": ob.get("causing_event_type"),
        "touch_count": ob.get("touch_count"),
        "mitigated": bool(ob.get("mitigated", False)),
        "timeframe": "H1",
        "matched_by": matched_by,
        "source_status": "MATCHED_H1_ORDER_BLOCK_FROM_DECISION_MSO",
    }


def _fvg_payload(fvg: dict[str, Any], *, timeframe: str, matched_by: str) -> dict[str, Any] | None:
    bottom = _safe_float(fvg.get("bottom"))
    top = _safe_float(fvg.get("top"))
    if bottom is None or top is None:
        return None
    return {
        "low": min(bottom, top),
        "high": max(bottom, top),
        "bottom": bottom,
        "top": top,
        "midpoint": _safe_float(fvg.get("midpoint")),
        "type": fvg.get("type"),
        "formation_time": fvg.get("formation_time"),
        "candle_indices": fvg.get("candle_indices") or [],
        "filled": bool(fvg.get("filled", False)),
        "timeframe": timeframe,
        "matched_by": matched_by,
        "source_status": f"MATCHED_{timeframe}_FVG_FROM_DECISION_MSO",
    }


def _match_order_block_from_decision_mso(fields: dict[str, Any]) -> dict[str, Any] | None:
    structural = fields.get("decision_time_structural_fields") or {}
    h1 = structural.get("h1_snapshot") or {}
    order_blocks = h1.get("order_blocks") or []
    if not isinstance(order_blocks, list):
        return None
    expected_type = _trade_side_zone_type(fields.get("side"))
    for label, price in _candidate_price_refs(fields):
        matches: list[dict[str, Any]] = []
        for ob in order_blocks:
            if not isinstance(ob, dict):
                continue
            if bool(ob.get("mitigated", False)):
                continue
            if expected_type and ob.get("type") != expected_type:
                continue
            low = _safe_float(ob.get("low"))
            high = _safe_float(ob.get("high"))
            if _price_inside_bounds(price, low, high):
                payload = _order_block_payload(ob, matched_by=label)
                if payload:
                    matches.append(payload)
        if matches:
            return min(
                matches,
                key=lambda item: abs(
                    price - (((_safe_float(item.get("low")) or 0.0) + (_safe_float(item.get("high")) or 0.0)) / 2.0)
                ),
            )
    return None


def _match_fvg_from_decision_mso(fields: dict[str, Any]) -> dict[str, Any] | None:
    structural = fields.get("decision_time_structural_fields") or {}
    expected_type = _trade_side_zone_type(fields.get("side"))
    # Production fvg_fill validates against M15 FVGs, so search M15 first.
    for timeframe in ("M15", "H1"):
        snapshot = structural.get(f"{timeframe.lower()}_snapshot") or {}
        fvgs = snapshot.get("fair_value_gaps") or []
        if not isinstance(fvgs, list):
            continue
        for label, price in _candidate_price_refs(fields):
            matches: list[dict[str, Any]] = []
            for fvg in fvgs:
                if not isinstance(fvg, dict):
                    continue
                if bool(fvg.get("filled", False)):
                    continue
                if expected_type and fvg.get("type") != expected_type:
                    continue
                bottom = _safe_float(fvg.get("bottom"))
                top = _safe_float(fvg.get("top"))
                if _price_inside_bounds(price, bottom, top):
                    payload = _fvg_payload(fvg, timeframe=timeframe, matched_by=label)
                    if payload:
                        matches.append(payload)
            if matches:
                return min(
                    matches,
                    key=lambda item: abs(
                        price
                        - (
                            _safe_float(item.get("midpoint"))
                            if _safe_float(item.get("midpoint")) is not None
                            else (((_safe_float(item.get("low")) or 0.0) + (_safe_float(item.get("high")) or 0.0)) / 2.0)
                        )
                    ),
                )
    return None


def _fvg_ob_geometry_from_decision_mso(fields: dict[str, Any]) -> dict[str, Any]:
    h1_setup = fields.get("h1_setup") or {}
    framework = str(fields.get("framework") or "").lower()
    poi_type = str(h1_setup.get("poi_type") or "").lower()
    evaluated = fields.get("frameworks_evaluated") or {}
    try:
        fvg_qualified = bool((evaluated.get("fvg_fill") or {}).get("qualified"))
        ob_qualified = bool((evaluated.get("ob_retest") or {}).get("qualified"))
    except Exception:
        fvg_qualified = False
        ob_qualified = False

    should_match_fvg = fvg_qualified or framework == "fvg_fill" or poi_type == "fvg"
    should_match_ob = ob_qualified or framework == "ob_retest" or poi_type == "ob"
    fvg_bounds = _match_fvg_from_decision_mso(fields) if should_match_fvg else None
    ob_bounds = _match_order_block_from_decision_mso(fields) if should_match_ob else None
    sequencing = None
    if fvg_bounds and ob_bounds:
        fvg_time = _zone_time_value(fvg_bounds.get("formation_time"))
        ob_time = _zone_time_value(ob_bounds.get("formation_time"))
        if fvg_time < ob_time:
            sequencing = {
                "first": "FVG",
                "second": "OB",
                "method": "formation_time_order_from_decision_mso",
                "fvg_formation_time": fvg_bounds.get("formation_time"),
                "ob_formation_time": ob_bounds.get("formation_time"),
            }
        elif ob_time < fvg_time:
            sequencing = {
                "first": "OB",
                "second": "FVG",
                "method": "formation_time_order_from_decision_mso",
                "fvg_formation_time": fvg_bounds.get("formation_time"),
                "ob_formation_time": ob_bounds.get("formation_time"),
            }

    if fvg_bounds and ob_bounds:
        status = "FVG_AND_OB_EXACT_BOUNDS_MATCHED_FROM_DECISION_MSO"
    elif fvg_bounds:
        status = "FVG_EXACT_BOUNDS_MATCHED_FROM_DECISION_MSO"
    elif ob_bounds:
        status = "OB_EXACT_BOUNDS_MATCHED_FROM_DECISION_MSO"
    elif should_match_fvg or should_match_ob:
        status = "REQUESTED_FVG_OR_OB_BOUNDS_NOT_MATCHED_IN_DECISION_MSO"
    else:
        status = "NO_FVG_OR_OB_MATCH_REQUESTED"

    return {
        "fvg_bounds": fvg_bounds,
        "ob_bounds": ob_bounds,
        "sequencing": sequencing,
        "exact_geometry_source_status": status,
    }


def fvg_ob_geometry_from_candidate_row(candidate_row: dict[str, Any]) -> dict[str, Any]:
    """Recover decision-time FVG/OB bounds from a strategy-follow candidate row.

    This is research-only source recovery. It uses the already-captured
    decision-time MSO snapshots embedded in ``strategy_follow_candidates`` and
    does not inspect future path/outcome rows.
    """
    return _fvg_ob_geometry_from_decision_mso(candidate_row)


def _risk_geometry(tp: dict[str, Any]) -> dict[str, Any]:
    entry = _safe_float(tp.get("entry_price"))
    stop = _safe_float(tp.get("stop_loss"))
    target = _safe_float(tp.get("take_profit_1"))
    side = str(tp.get("direction") or "").upper()
    risk = abs(entry - stop) if entry is not None and stop is not None else None
    gross_r = None
    if risk and risk > 0 and entry is not None and target is not None:
        gross_r = (target - entry) / risk if side == "LONG" else (entry - target) / risk
    return {
        "direction": side or None,
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit_1": target,
        "risk_price": risk,
        "gross_tp1_r": round(gross_r, 8) if gross_r is not None else None,
        "reported_risk_reward_ratio": tp.get("risk_reward_ratio"),
        "sl_buffer_applied": tp.get("sl_buffer_applied"),
    }


def _decision_time_structural_fields(
    *,
    fields: dict[str, Any],
    mso: Any,
) -> dict[str, Any]:
    h1 = _timeframe_state_snapshot(mso, "H1")
    m15 = _timeframe_state_snapshot(mso, "M15")
    h1_setup = fields.get("h1_setup") or {}
    tp = fields.get("trade_parameters") or {}
    risk = _risk_geometry(tp)
    mso_present = bool(mso)
    fvg_sources_present = bool(h1.get("fair_value_gaps") or m15.get("fair_value_gaps"))
    protected_swing = h1.get("protected_swing") or m15.get("protected_swing")

    if not mso_present:
        source_status = "SOURCE_NOT_CAPTURED"
    else:
        source_status = "DECISION_TIME_SOURCE_CAPTURED"

    structural_fields = {
        "standalone_fvg_entry_geometry": {
            "source_status": (
                "DECISION_TIME_SOURCE_CAPTURED"
                if fvg_sources_present
                else "NO_FVG_GEOMETRY_PRESENT_IN_DECISION_MSO"
                if mso_present
                else "SOURCE_NOT_CAPTURED"
            ),
            "candidate_h1_poi_type": h1_setup.get("poi_type"),
            "candidate_h1_poi_price_level": h1_setup.get("poi_price_level"),
            "candidate_entry_price": risk.get("entry_price"),
            "h1_fair_value_gaps": h1.get("fair_value_gaps") or [],
            "m15_fair_value_gaps": m15.get("fair_value_gaps") or [],
        },
        "fvg_lock_state": {
            "source_status": (
                "DECISION_TIME_SOURCE_CAPTURED_PATH_DERIVATION_PENDING"
                if fvg_sources_present
                else "NO_FVG_GEOMETRY_PRESENT_IN_DECISION_MSO"
                if mso_present
                else "SOURCE_NOT_CAPTURED"
            ),
            "lock_algorithm_status": "NOT_EVALUATED_IN_LIVE_DECISION_PATH",
            "path_follow_required": True,
            "h1_fvg_count": len(h1.get("fair_value_gaps") or []),
            "m15_fvg_count": len(m15.get("fair_value_gaps") or []),
        },
        "swing_protected_lock_level": {
            "source_status": (
                "DECISION_TIME_SOURCE_CAPTURED" if protected_swing else "NO_PROTECTED_SWING_PRESENT_IN_DECISION_MSO"
            )
            if mso_present
            else "SOURCE_NOT_CAPTURED",
            "h1_protected_swing": h1.get("protected_swing"),
            "m15_protected_swing": m15.get("protected_swing"),
        },
        "structural_lock_event_time_price": {
            "source_status": (
                "FORWARD_PATH_EVENT_PENDING_DECISION_TIME_SEED_CAPTURED"
                if mso_present
                else "SOURCE_NOT_CAPTURED"
            ),
            "decision_time_utc": fields.get("decision_time_utc"),
            "candidate_entry_price": risk.get("entry_price"),
            "candidate_tp1": risk.get("take_profit_1"),
            "candidate_stop_loss": risk.get("stop_loss"),
            "path_follow_required": True,
        },
        "post_lock_reentry_state": {
            "source_status": (
                "FORWARD_PATH_EVENT_PENDING_DECISION_TIME_SEED_CAPTURED"
                if mso_present
                else "SOURCE_NOT_CAPTURED"
            ),
            "reentry_algorithm_status": "NOT_EVALUATED_IN_LIVE_DECISION_PATH",
            "path_follow_required": True,
            "candidate_geometry": risk,
        },
        "cost_aware_min_r_fields": {
            "source_status": "DECISION_TIME_SOURCE_CAPTURED" if tp else "SOURCE_NOT_CAPTURED",
            "candidate_geometry": risk,
            "spread_cents": _safe_get(mso, "spread_cents"),
            "cost_model_status": "RAW_DECISION_GEOMETRY_CAPTURED_COST_MODEL_NOT_APPLIED",
        },
    }
    return {
        "schema_version": "decision_time_structural_fields_v1",
        "capture_status": (
            "DECISION_TIME_STRUCTURAL_SOURCE_CAPTURED"
            if any(
                (payload.get("source_status") if isinstance(payload, dict) else None)
                != "SOURCE_NOT_CAPTURED"
                for payload in structural_fields.values()
            )
            else "SOURCE_NOT_CAPTURED"
        ),
        "source": "live_mso_at_candidate_time",
        "mso_timestamp_utc": _safe_get(mso, "timestamp_utc"),
        "h1_snapshot": h1,
        "m15_snapshot": m15,
        "fields": structural_fields,
        "field_statuses": {
            key: value.get("source_status") if isinstance(value, dict) else "UNKNOWN"
            for key, value in structural_fields.items()
        },
        "no_leak_status": "DECISION_TIME_MSO_ONLY_NO_POST_OUTCOME_FIELDS",
        "source_status": source_status,
    }


def _structural_selector_metadata_from_fields(structural_fields: dict[str, Any]) -> dict[str, Any]:
    field_map = structural_fields.get("fields") if isinstance(structural_fields, dict) else {}
    if not isinstance(field_map, dict):
        field_map = {}
    if not field_map:
        return {}

    def status(name: str) -> str:
        value = field_map.get(name)
        return str(value.get("source_status") if isinstance(value, dict) else "")

    return {
        "capture_status": structural_fields.get("capture_status") or "SOURCE_NOT_CAPTURED",
        "h1_setup_present": True,
        "m15_confirmation_present": True,
        "frameworks_evaluated_present": True,
        "mso_summary_present": True,
        "standalone_fvg_geometry_present": status("standalone_fvg_entry_geometry") != "SOURCE_NOT_CAPTURED",
        "structural_lock_event_present": status("structural_lock_event_time_price") != "SOURCE_NOT_CAPTURED",
        "reentry_state_present": status("post_lock_reentry_state") != "SOURCE_NOT_CAPTURED",
        "cost_aware_min_r_present": status("cost_aware_min_r_fields") != "SOURCE_NOT_CAPTURED",
        "field_statuses": structural_fields.get("field_statuses") or {},
        "note": (
            "Decision-time MSO structural sources are preserved for forward research. "
            "Rows may still report scorer_not_implemented where the alternate strategy "
            "algorithm is not wired."
        ),
    }


def common_metadata(**fields: Any) -> dict[str, Any]:
    now = utc_now_iso()
    evidence_class = fields.get("evidence_class") or "FORWARD_SHADOW"
    if evidence_class not in EVIDENCE_LABELS:
        evidence_class = "DISCOVERY_ONLY"
    row = {
        "schema_version": fields.get("schema_version"),
        "created_at_utc": fields.get("created_at_utc") or now,
        "symbol": fields.get("symbol"),
        "broker_symbol": fields.get("broker_symbol"),
        "source_symbol": fields.get("source_symbol"),
        "market_timeframe": fields.get("market_timeframe"),
        "route_session": (
            fields.get("route_session")
            or fields.get("session")
            or fields.get("kill_zone")
        ),
        "horizon_id": fields.get("horizon_id"),
        "source_component": fields.get("source_component"),
        "selected_side": fields.get("selected_side") or fields.get("side"),
        "session": fields.get("session"),
        "kill_zone": fields.get("kill_zone"),
        "side": fields.get("side"),
        "regime": fields.get("regime"),
        "candidate_id": fields.get("candidate_id"),
        "trade_id": fields.get("trade_id"),
        "evidence_class": evidence_class,
        "decision_time_utc": fields.get("decision_time_utc"),
        "asof_cutoff_utc": fields.get("asof_cutoff_utc") or fields.get("decision_time_utc"),
        "source_file": fields.get("source_file"),
        "source_hash": fields.get("source_hash"),
        "no_leak_status": fields.get("no_leak_status") or "AS_OF_FIELDS_ONLY",
        "result_use_status": fields.get("result_use_status") or RESULT_USE_STATUS,
    }
    return enrich_cp281_event_contract_fields(row, source_path=fields.get("source_path"))


def _write_pending_append(target: Path, payload: str) -> None:
    pending_dir = target.parent / "_pending_appends"
    pending_dir.mkdir(parents=True, exist_ok=True)
    pending_path = pending_dir / f"{target.name}.{os.getpid()}.{time.time_ns()}.json"
    with open(pending_path, "x", encoding="utf-8", newline="") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())


def append_jsonl(path: str | Path, row: dict[str, Any]) -> None:
    """Append one JSONL row. Never raises."""
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(_json_safe(row), sort_keys=True) + "\n"
        lock_path = target.with_suffix(target.suffix + ".lock")
        with open(lock_path, "a+b") as lock_f:
            locked = False
            if msvcrt is not None:
                for _ in range(_JSONL_LOCK_RETRIES):
                    try:
                        lock_f.seek(0)
                        msvcrt.locking(lock_f.fileno(), msvcrt.LK_NBLCK, 1)
                        locked = True
                        break
                    except OSError:
                        time.sleep(_JSONL_LOCK_SLEEP_SECONDS)
                if not locked:
                    _write_pending_append(target, payload)
                    logger.warning("forward-capture JSONL lock busy; preserved row in pending appends for %s", target)
                    return
            try:
                with open(target, "a", encoding="utf-8", newline="") as f:
                    f.write(payload)
                    f.flush()
                    os.fsync(f.fileno())
            finally:
                if msvcrt is not None and locked:
                    try:
                        lock_f.seek(0)
                        msvcrt.locking(lock_f.fileno(), msvcrt.LK_UNLCK, 1)
                    except OSError as exc:
                        logger.warning("forward-capture JSONL unlock failed (%s)", exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("forward-capture JSONL append failed (non-blocking): %s", exc)


def build_v2b_forward_pair_row(**fields: Any) -> dict[str, Any]:
    row = common_metadata(
        **{
            **fields,
            "schema_version": "v2b_forward_pair_v1",
            "evidence_class": fields.get("evidence_class") or "FORWARD_SHADOW",
        }
    )
    row.update(
        {
            "ob_boundary_outcome": fields.get("ob_boundary_outcome"),
            "j46_baseline_outcome": fields.get("j46_baseline_outcome"),
            "fixed_r_comparator": fields.get("fixed_r_comparator"),
            "fvg_comparator": fields.get("fvg_comparator"),
            "lower_timeframe_available": fields.get("lower_timeframe_available"),
            "same_bar_ambiguity_state": fields.get("same_bar_ambiguity_state"),
            "cost_sensitivity": fields.get("cost_sensitivity"),
            "source_period": fields.get("source_period"),
            "path_label_status": fields.get("path_label_status"),
            "actual_synthetic_label_lane": fields.get("actual_synthetic_label_lane"),
            "resolved_pair": bool(fields.get("ob_boundary_outcome"))
            and bool(fields.get("j46_baseline_outcome")),
            "sample_floor_target_resolved_pairs": fields.get(
                "sample_floor_target_resolved_pairs", 30
            ),
        }
    )
    return row


def record_v2b_forward_pair(row: dict[str, Any], log_path: str | Path = V2B_FORWARD_PAIR_PATH) -> None:
    append_jsonl(log_path, build_v2b_forward_pair_row(**row))


def build_prefill_delivery_path_row(**fields: Any) -> dict[str, Any]:
    row = common_metadata(
        **{
            **fields,
            "schema_version": "prefill_delivery_path_v1",
            "evidence_class": fields.get("evidence_class") or "FORWARD_SHADOW",
        }
    )
    row.update(
        {
            "structural_setup_id": fields.get("structural_setup_id"),
            "original_poi_bounds": fields.get("original_poi_bounds"),
            "entry_arming_time_utc": fields.get("entry_arming_time_utc"),
            "pre_fill_candles": fields.get("pre_fill_candles") or [],
            "pre_fill_ticks_summary": fields.get("pre_fill_ticks_summary"),
            "delivery_leg_direction": fields.get("delivery_leg_direction"),
            "reversal_leg_timing": fields.get("reversal_leg_timing"),
            "fill_happened": fields.get("fill_happened"),
            "fill_delay_seconds": fields.get("fill_delay_seconds"),
            "cancel_expiry_abort_reason": fields.get("cancel_expiry_abort_reason"),
            "lower_timeframe_path_ordering": fields.get("lower_timeframe_path_ordering"),
            "fvg_ob_swing_state_at_arm": fields.get("fvg_ob_swing_state_at_arm"),
            "fvg_ob_swing_state_at_fill": fields.get("fvg_ob_swing_state_at_fill"),
            "fvg_ob_swing_state_at_cancel": fields.get("fvg_ob_swing_state_at_cancel"),
        }
    )
    return row


def record_prefill_delivery_path(row: dict[str, Any], log_path: str | Path = PREFILL_DELIVERY_PATH) -> None:
    append_jsonl(log_path, build_prefill_delivery_path_row(**row))


def no_leak_status_for_decision_fields(decision_time_fields: dict[str, Any] | None) -> str:
    if not decision_time_fields:
        return "NO_DECISION_FIELDS_SUPPLIED"
    leaked = sorted(set(decision_time_fields) & POST_OUTCOME_FIELD_NAMES)
    if leaked:
        return "POST_OUTCOME_FIELD_PRESENT:" + ",".join(leaked)
    return "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT"


def build_fvg_ob_confluence_row(**fields: Any) -> dict[str, Any]:
    bucket = fields.get("bucket") or "no_poi"
    if bucket not in CONFLUENCE_BUCKETS:
        bucket = "disagreement"
    decision_time_fields = fields.get("decision_time_fields") or {}
    row = common_metadata(
        **{
            **fields,
            "schema_version": "fvg_ob_confluence_forward_v1",
            "evidence_class": fields.get("evidence_class") or "FORWARD_SHADOW",
            "no_leak_status": no_leak_status_for_decision_fields(decision_time_fields),
        }
    )
    row.update(
        {
            "bucket": bucket,
            "touch_count": fields.get("touch_count"),
            "poi_quality": fields.get("poi_quality"),
            "lower_timeframe_available": fields.get("lower_timeframe_available"),
            "candidate_outcome_lane": fields.get("candidate_outcome_lane"),
            "decision_time_fields": decision_time_fields,
            "fvg_bounds": fields.get("fvg_bounds"),
            "ob_bounds": fields.get("ob_bounds"),
            "sequencing": fields.get("sequencing"),
            "composite_arbitration": fields.get("composite_arbitration"),
            "disagreement_reason": fields.get("disagreement_reason"),
            "exact_geometry_source_status": fields.get("exact_geometry_source_status"),
        }
    )
    return row


def record_fvg_ob_confluence(row: dict[str, Any], log_path: str | Path = FVG_OB_CONFLUENCE_PATH) -> None:
    append_jsonl(log_path, build_fvg_ob_confluence_row(**row))


def build_context_control_row(**fields: Any) -> dict[str, Any]:
    row = common_metadata(
        **{
            **fields,
            "schema_version": "context_control_forward_v1",
            "evidence_class": fields.get("evidence_class") or "CONTROL_ONLY",
        }
    )
    row.update(
        {
            "context_question_id": fields.get("context_question_id"),
            "context_family": fields.get("context_family"),
            "asof_timestamp_convention": fields.get("asof_timestamp_convention"),
            "join_rule": fields.get("join_rule"),
            "context_values": fields.get("context_values") or {},
            "control_only": bool(fields.get("control_only", True)),
            "control_role": fields.get("control_role") or "CONTROL_ONLY",
            "direct_strategy_validation_status": fields.get("direct_strategy_validation_status")
            or "NOT_DIRECT_STRATEGY_VALIDATION",
            "strategy_validation_status": fields.get("strategy_validation_status")
            or "CONTROL_CONTEXT_ONLY_NOT_STRATEGY_VALIDATION",
            "validation_scope": fields.get("validation_scope") or "EXPLORATORY_CONTEXT_ONLY",
        }
    )
    return row


def record_context_control(row: dict[str, Any], log_path: str | Path = CONTEXT_CONTROL_PATH) -> None:
    append_jsonl(log_path, build_context_control_row(**row))


def _capture_value_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value != ""
    return True


def build_moonshot_selected_action_source_capture_row(**fields: Any) -> dict[str, Any]:
    required_fields = [str(field) for field in fields.get("source_capture_required_fields") or []]
    source_capture_fields = fields.get("source_capture_fields")
    if not isinstance(source_capture_fields, dict):
        source_capture_fields = {}
    missing_fields = [
        field for field in required_fields if not _capture_value_present(source_capture_fields.get(field))
    ]
    row = common_metadata(
        **{
            **fields,
            "schema_version": MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE_SCHEMA_VERSION,
            "evidence_class": fields.get("evidence_class") or "FORWARD_SHADOW",
            "result_use_status": fields.get("result_use_status") or RESULT_USE_STATUS,
        }
    )
    row.update(
        {
            "strategy_id": fields.get("strategy_id"),
            "source_capture_status": "SOURCE_CAPTURE_COMPLETE" if not missing_fields else "SOURCE_CAPTURE_INCOMPLETE",
            "source_capture_fields": _json_safe(source_capture_fields),
            "source_capture_required_fields": required_fields,
            "source_capture_missing_fields": missing_fields,
            "source_artifacts": fields.get("source_artifacts") or [],
            "source_hashes": fields.get("source_hashes") or [],
            "exact_control_denominator_status": fields.get("exact_control_denominator_status")
            or ("AVAILABLE" if not missing_fields else "MISSING_REQUIRED_FIELDS"),
            "scorer_ready_status": fields.get("scorer_ready_status")
            or ("SOURCE_READY_SCORER_NOT_IMPLEMENTED" if not missing_fields else "WAITING_SOURCE_CAPTURE"),
            "candidate_use_allowed_now": False,
            "runtime_score_allowed": False,
            "broker_runtime_change_status": False,
            "validation_result_status": False,
            "outcome_result_rows_status": False,
            "proxy_delta_reference_counted_as_r": False,
        }
    )
    return row


def record_moonshot_selected_action_source_capture(
    row: dict[str, Any],
    log_path: str | Path = MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE_PATH,
) -> None:
    append_jsonl(log_path, build_moonshot_selected_action_source_capture_row(**row))


def _source_rows_from_fields(fields: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [fields]
    for name in (
        "candidate_row",
        "lifecycle_row",
        "path_order_row",
        "quote_row",
        "control_row",
        "source_row",
    ):
        value = fields.get(name)
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _first_source_value(source_rows: list[dict[str, Any]], *names: str) -> Any:
    for name in names:
        for row in source_rows:
            if name in row and _capture_value_present(row.get(name)):
                return row.get(name)
    return None


def _field_or_missing(field_name: str, value: Any) -> Any:
    if _capture_value_present(value):
        return _json_safe(value)
    return NOFILL_FORWARD_SOURCE_CAPTURE_MISSING_STATUS_BY_FIELD[field_name]


def _parse_capture_datetime(value: Any) -> datetime | None:
    if not _capture_value_present(value):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _capture_latency_ms(started_at: Any, completed_at: Any) -> int | None:
    started = _parse_capture_datetime(started_at)
    completed = _parse_capture_datetime(completed_at)
    if started is None or completed is None:
        return None
    return max(0, int(round((completed - started).total_seconds() * 1000)))


def _sha256_json(value: Any) -> str:
    payload = json.dumps(
        _json_safe(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _parser_code_hash() -> str:
    try:
        return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except Exception:  # noqa: BLE001
        return _sha256_json(
            {
                "schema": NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION,
                "fields": NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS,
            }
        )


def _collect_present_forbidden_names(value: Any) -> set[str]:
    present: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            key_str = str(key)
            if key_str in NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES and _capture_value_present(item):
                present.add(key_str)
            present.update(_collect_present_forbidden_names(item))
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            present.update(_collect_present_forbidden_names(item))
    return present


def _bool_status(value: Any, *, true_status: str, false_status: str, missing_status: str) -> str:
    if value is None or value == "":
        return missing_status
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return true_status
        if normalized in {"false", "0", "no"}:
            return false_status
    return true_status if bool(value) else false_status


def _safe_capture_hash_seed(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": row.get("candidate_id"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "decision_time_utc": row.get("capture_observed_at_utc"),
        "pending_intent_created_utc": row.get("pending_intent_created_utc"),
        "session_tag": row.get("session_tag"),
        "event_order_resolution_method": row.get("event_order_resolution_method"),
        "schema_version": NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION,
    }


def build_nofill_forward_source_capture_row(**fields: Any) -> dict[str, Any]:
    """Build the accepted NOFILL source-capture projection row.

    The row is source/control-only. It emits the 55 accepted contract fields,
    converts missing source families to accepted fail-closed statuses, and
    redacts broker/order/deal/account/position/result/cost fields to status
    values only.
    """
    source_rows = _source_rows_from_fields(fields)
    forbidden_present = set()
    for row in source_rows:
        forbidden_present.update(_collect_present_forbidden_names(row))

    started_at = _first_source_value(source_rows, "capture_write_started_at_utc", "write_started_at_utc")
    completed_at = _first_source_value(source_rows, "capture_write_completed_at_utc", "write_completed_at_utc")
    latency_ms = _first_source_value(source_rows, "capture_latency_ms")
    if latency_ms is None:
        latency_ms = _capture_latency_ms(started_at, completed_at)

    pending_order_mode = _first_source_value(
        source_rows,
        "pending_order_mode_source_safe",
        "pending_order_mode",
    )
    native_pending_order_type = _first_source_value(
        source_rows,
        "native_pending_order_type_source_safe",
        "native_pending_order_type",
    )
    broker_pending_order_created = _first_source_value(
        source_rows,
        "broker_pending_order_created",
        "broker_pending_order_created_status_bool",
    )

    decision_spread = _first_source_value(
        source_rows,
        "decision_spread_value_source_safe",
        "decision_spread",
        "spread",
        "spread_cents",
        "tick_spread_cents",
    )
    decision_spread_unit = _first_source_value(source_rows, "decision_spread_unit", "spread_unit")
    if decision_spread_unit is None and decision_spread is not None:
        decision_spread_unit = "spread_cents"
    entry_touch_spread = _first_source_value(
        source_rows,
        "entry_touch_spread_value_source_safe",
        "entry_touch_spread",
    )
    entry_touch_spread_unit = _first_source_value(source_rows, "entry_touch_spread_unit")
    spread_hash = _first_source_value(source_rows, "spread_source_hash")
    if spread_hash is None and (decision_spread is not None or entry_touch_spread is not None):
        spread_hash = _sha256_json(
            {
                "decision_spread": decision_spread,
                "decision_spread_unit": decision_spread_unit,
                "entry_touch_spread": entry_touch_spread,
                "entry_touch_spread_unit": entry_touch_spread_unit,
            }
        )

    pending_created = _first_source_value(
        source_rows,
        "pending_intent_created_utc",
        "pending_created_time_utc",
        "placed_time",
    )
    cancel_expiry_utc = _first_source_value(
        source_rows,
        "cancel_expiry_utc",
        "expiry_time_utc",
        "cancel_time_utc",
    )
    cancel_reason = _first_source_value(
        source_rows,
        "cancel_expiry_reason_status",
        "cancel_reason",
        "reason",
    )
    entry_touch_first = _first_source_value(
        source_rows,
        "entry_touch_first_utc",
        "first_entry_touch_utc",
    )
    trigger_condition_met = _first_source_value(source_rows, "trigger_condition_met")
    side_touch_status = _first_source_value(source_rows, "side_aware_entry_touch_status")
    if side_touch_status is None and trigger_condition_met is not None:
        side_touch_status = _bool_status(
            trigger_condition_met,
            true_status="ENTRY_TOUCH_CONDITION_MET_SOURCE_SAFE",
            false_status="ENTRY_TOUCH_NOT_OBSERVED_SOURCE_SAFE",
            missing_status=NOFILL_FORWARD_SOURCE_CAPTURE_MISSING_STATUS_BY_FIELD[
                "side_aware_entry_touch_status"
            ],
        )

    observed_at = _first_source_value(
        source_rows,
        "capture_observed_at_utc",
        "created_at_utc",
        "timestamp_utc",
        "checked_candle_time_utc",
        "decision_time_utc",
    )
    session_tag = _first_source_value(source_rows, "session_tag", "session", "kill_zone")
    regime = _first_source_value(source_rows, "regime_context_status", "regime")
    event_order = _first_source_value(
        source_rows,
        "event_order_resolution_method",
        "lower_timeframe_path_ordering",
        "event_order_method",
    )
    same_tick_status = _first_source_value(
        source_rows,
        "same_tick_same_bar_ambiguity_status",
        "same_bar_ambiguity_state",
    )
    missing_coverage = _first_source_value(source_rows, "missing_coverage_intervals")

    ticket_names = {
        "mt5_order_ticket",
        "order_ticket",
        "pending_ticket",
        "trade_state_ticket",
        "deal",
        "deal_id",
        "position",
        "position_id",
        "account_id",
        "account_history",
    }
    ticket_present = bool(forbidden_present & ticket_names)
    slippage_present = "slippage_price" in forbidden_present
    execution_quality_present = "execution_quality" in forbidden_present
    result_cost_names = {
        "actual_r",
        "broker_actual_r",
        "result",
        "slippage_price",
        "execution_quality",
    }
    result_cost_present = bool(forbidden_present & result_cost_names)

    row: dict[str, Any] = {
        "schema_version": NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION,
        "created_at_utc": completed_at or utc_now_iso(),
        "route_id": "NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION",
        "result_use_status": RESULT_USE_STATUS,
        "validation_result_status": False,
        "outcome_result_rows_status": False,
        "broker_runtime_change_status": False,
        "opens_result_scoring": False,
        "opens_validation": False,
        "opens_production_change_review": False,
        "opens_live_trading_behavior": False,
        "no_leak_status": (
            "FORBIDDEN_INPUT_FIELDS_REDACTED_STATUS_ONLY"
            if forbidden_present
            else "NO_FORBIDDEN_RAW_FIELDS_PRESENT"
        ),
        "symbol": _first_source_value(source_rows, "symbol"),
        "broker_symbol": _first_source_value(source_rows, "broker_symbol"),
        "source_symbol": _first_source_value(source_rows, "source_symbol"),
        "candidate_id": _first_source_value(source_rows, "candidate_id"),
        "decision_time_utc": _first_source_value(source_rows, "decision_time_utc"),
        "field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
        "future_logger_field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS),
        "capture_observed_at_utc": _field_or_missing("capture_observed_at_utc", observed_at),
        "capture_write_started_at_utc": _field_or_missing("capture_write_started_at_utc", started_at),
        "capture_write_completed_at_utc": _field_or_missing("capture_write_completed_at_utc", completed_at),
        "capture_latency_ms": _field_or_missing("capture_latency_ms", latency_ms),
        "capture_clock_source_status": _field_or_missing(
            "capture_clock_source_status",
            _first_source_value(source_rows, "capture_clock_source_status", "clock_source_status")
            or ("SYSTEM_UTC_CLOCK_CAPTURED" if completed_at else None),
        ),
        "capture_clock_skew_ms": _field_or_missing(
            "capture_clock_skew_ms",
            _first_source_value(source_rows, "capture_clock_skew_ms", "clock_skew_ms"),
        ),
        "capture_clock_skew_status": _field_or_missing(
            "capture_clock_skew_status",
            _first_source_value(source_rows, "capture_clock_skew_status", "clock_skew_status"),
        ),
        "capture_timestamp_derivation_rule": _field_or_missing(
            "capture_timestamp_derivation_rule",
            _first_source_value(source_rows, "capture_timestamp_derivation_rule")
            or "writer_utc_clock_wrapped_around_sanitized_projection",
        ),
        "pending_order_mode_source_safe": _field_or_missing(
            "pending_order_mode_source_safe",
            pending_order_mode,
        ),
        "pending_order_mode_status": _field_or_missing(
            "pending_order_mode_status",
            _first_source_value(source_rows, "pending_order_mode_status")
            or ("PENDING_ORDER_MODE_CAPTURED_SOURCE_SAFE" if pending_order_mode else None),
        ),
        "broker_pending_order_created_status": _field_or_missing(
            "broker_pending_order_created_status",
            _first_source_value(source_rows, "broker_pending_order_created_status")
            or _bool_status(
                broker_pending_order_created,
                true_status="BROKER_PENDING_ORDER_CREATED_TRUE_STATUS_ONLY",
                false_status="BROKER_PENDING_ORDER_CREATED_FALSE_STATUS_ONLY",
                missing_status="",
            ),
        ),
        "native_pending_order_type_source_safe": _field_or_missing(
            "native_pending_order_type_source_safe",
            native_pending_order_type,
        ),
        "native_pending_order_type_status": _field_or_missing(
            "native_pending_order_type_status",
            _first_source_value(source_rows, "native_pending_order_type_status")
            or ("NATIVE_PENDING_ORDER_TYPE_CAPTURED_SOURCE_SAFE" if native_pending_order_type else None),
        ),
        "raw_ticket_field_present_status": (
            "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
            if ticket_present
            else "RAW_TICKET_FIELDS_ABSENT_OR_REDACTED"
        ),
        "mt5_order_ticket_redaction_status": (
            "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
            if "mt5_order_ticket" in forbidden_present
            else "MT5_ORDER_TICKET_OMITTED_NOT_HASHED"
        ),
        "decision_spread_status": _field_or_missing(
            "decision_spread_status",
            _first_source_value(source_rows, "decision_spread_status")
            or ("QUOTE_SNAPSHOT_CAPTURED_SOURCE_SAFE" if decision_spread is not None else None),
        ),
        "decision_spread_value_source_safe": _field_or_missing(
            "decision_spread_value_source_safe",
            decision_spread,
        ),
        "decision_spread_unit": _field_or_missing("decision_spread_unit", decision_spread_unit),
        "entry_touch_spread_status": _field_or_missing(
            "entry_touch_spread_status",
            _first_source_value(source_rows, "entry_touch_spread_status")
            or ("QUOTE_SNAPSHOT_CAPTURED_SOURCE_SAFE" if entry_touch_spread is not None else None),
        ),
        "entry_touch_spread_value_source_safe": _field_or_missing(
            "entry_touch_spread_value_source_safe",
            entry_touch_spread,
        ),
        "spread_source_hash": _field_or_missing("spread_source_hash", spread_hash),
        "slippage_label_status": (
            "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
            if slippage_present
            else "SLIPPAGE_LABEL_CLOSED_NOT_EMITTED"
        ),
        "slippage_value_redaction_status": (
            "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
            if slippage_present
            else "SLIPPAGE_VALUE_OMITTED_NOT_HASHED"
        ),
        "execution_quality_label_status": (
            "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
            if execution_quality_present
            else "EXECUTION_QUALITY_LABEL_CLOSED_NOT_EMITTED"
        ),
        "execution_quality_value_redaction_status": (
            "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
            if execution_quality_present
            else "EXECUTION_QUALITY_VALUE_OMITTED_NOT_HASHED"
        ),
        "cost_testing_gate_status": (
            "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
            if result_cost_present
            else "RESULT_COST_SCORING_CLOSED_NO_COST_LABELS"
        ),
        "pending_intent_created_utc": _field_or_missing("pending_intent_created_utc", pending_created),
        "pending_horizon_start_utc": _field_or_missing(
            "pending_horizon_start_utc",
            _first_source_value(source_rows, "pending_horizon_start_utc") or pending_created,
        ),
        "pending_horizon_end_utc": _field_or_missing(
            "pending_horizon_end_utc",
            _first_source_value(source_rows, "pending_horizon_end_utc") or cancel_expiry_utc,
        ),
        "cancel_expiry_utc": _field_or_missing("cancel_expiry_utc", cancel_expiry_utc),
        "cancel_expiry_reason_status": _field_or_missing(
            "cancel_expiry_reason_status",
            cancel_reason
            if str(cancel_reason or "").isupper()
            else ("CANCEL_OR_EXPIRY_REASON_CAPTURED_SOURCE_SAFE" if cancel_reason else None),
        ),
        "entry_touch_first_utc": _field_or_missing("entry_touch_first_utc", entry_touch_first),
        "side_aware_entry_touch_status": _field_or_missing(
            "side_aware_entry_touch_status",
            side_touch_status,
        ),
        "terminal_area_touch_status": _field_or_missing(
            "terminal_area_touch_status",
            _first_source_value(source_rows, "terminal_area_touch_status"),
        ),
        "terminal_area_first_touch_utc": _field_or_missing(
            "terminal_area_first_touch_utc",
            _first_source_value(source_rows, "terminal_area_first_touch_utc"),
        ),
        "protective_area_touch_status": _field_or_missing(
            "protective_area_touch_status",
            _first_source_value(source_rows, "protective_area_touch_status"),
        ),
        "protective_area_first_touch_utc": _field_or_missing(
            "protective_area_first_touch_utc",
            _first_source_value(source_rows, "protective_area_first_touch_utc"),
        ),
        "event_order_resolution_method": _field_or_missing(
            "event_order_resolution_method",
            event_order,
        ),
        "same_tick_same_bar_ambiguity_status": _field_or_missing(
            "same_tick_same_bar_ambiguity_status",
            same_tick_status,
        ),
        "lower_tf_coverage_window_start_utc": _field_or_missing(
            "lower_tf_coverage_window_start_utc",
            _first_source_value(source_rows, "lower_tf_coverage_window_start_utc", "coverage_window_start_utc"),
        ),
        "lower_tf_coverage_window_end_utc": _field_or_missing(
            "lower_tf_coverage_window_end_utc",
            _first_source_value(source_rows, "lower_tf_coverage_window_end_utc", "coverage_window_end_utc"),
        ),
        "missing_coverage_intervals": _field_or_missing(
            "missing_coverage_intervals",
            missing_coverage,
        ),
        "row_level_denominator_member": _field_or_missing(
            "row_level_denominator_member",
            _first_source_value(source_rows, "row_level_denominator_member") if "row_level_denominator_member" in fields else True,
        ),
        "nofill_duplicate_key_count_member": _field_or_missing(
            "nofill_duplicate_key_count_member",
            _first_source_value(source_rows, "nofill_duplicate_key_count_member")
            if "nofill_duplicate_key_count_member" in fields
            else True,
        ),
        "duplicate_group_id_count_member": _field_or_missing(
            "duplicate_group_id_count_member",
            _first_source_value(source_rows, "duplicate_group_id_count_member")
            if "duplicate_group_id_count_member" in fields
            else True,
        ),
        "session_tag": _field_or_missing("session_tag", session_tag),
        "regime_context_status": _field_or_missing(
            "regime_context_status",
            _first_source_value(source_rows, "regime_context_status")
            or ("REGIME_CONTEXT_CAPTURED_SOURCE_SAFE" if regime else None),
        ),
        "sample_floor_policy_id": _field_or_missing(
            "sample_floor_policy_id",
            _first_source_value(source_rows, "sample_floor_policy_id")
            or "NOFILL_SOURCE_CAPTURE_CONTROL_ONLY_SAMPLE_FLOOR_NOT_VALIDATION",
        ),
        "perturbation_ready_bucket": _field_or_missing(
            "perturbation_ready_bucket",
            _first_source_value(source_rows, "perturbation_ready_bucket")
            or "SOURCE_CAPTURE_ONLY_NO_RESULT_PERTURBATION",
        ),
        "kill_switch_observability_status": _field_or_missing(
            "kill_switch_observability_status",
            _first_source_value(source_rows, "kill_switch_observability_status")
            or "SOURCE_CAPTURE_ONLY_NO_KILL_SWITCH_ACTION",
        ),
        "parser_code_hash": _parser_code_hash(),
        "forbidden_field_scan_status": (
            "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
            if forbidden_present
            else "NO_FORBIDDEN_RAW_FIELDS_PRESENT"
        ),
    }

    row["nofill_duplicate_key_sha256"] = _sha256_json(
        {
            **_safe_capture_hash_seed(row),
            "key_family": "nofill_duplicate_key",
        }
    )
    row["duplicate_group_id_sha256"] = _sha256_json(
        {
            **_safe_capture_hash_seed(row),
            "key_family": "duplicate_group_id",
        }
    )
    row["source_artifact_hash"] = _sha256_json(
        {
            "route_id": row["route_id"],
            "schema_version": row["schema_version"],
            "safe_seed": _safe_capture_hash_seed(row),
            "field_statuses": {
                field: row[field]
                for field in NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS
                if isinstance(row.get(field), str)
                and row.get(field) in NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUSES
            },
        }
    )
    enrich_cp281_event_contract_fields(row, source_path=NOFILL_FORWARD_SOURCE_CAPTURE_PATH)
    return {key: _json_safe(value) for key, value in row.items()}


def validate_nofill_forward_source_capture_row(row: dict[str, Any]) -> dict[str, Any]:
    """Validate the source-capture contract without opening result scoring."""
    missing_fields = [field for field in NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS if field not in row]
    forbidden_output_keys = sorted(
        set(row) & NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_RAW_FIELD_NAMES
    )
    unexpected_true_boundary_fields = [
        flag
        for flag in (
            "validation_result_status",
            "outcome_result_rows_status",
            "broker_runtime_change_status",
            "opens_result_scoring",
            "opens_validation",
            "opens_production_change_review",
            "opens_live_trading_behavior",
        )
        if row.get(flag) is True
    ]
    bad_hash_fields = []
    for field in (
        "spread_source_hash",
        "nofill_duplicate_key_sha256",
        "duplicate_group_id_sha256",
        "source_artifact_hash",
        "parser_code_hash",
    ):
        value = row.get(field)
        if value in NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUSES:
            continue
        if not isinstance(value, str) or len(value) != 64 or any(ch not in "009abcdef" for ch in value):
            bad_hash_fields.append(field)
    future_fields_missing = [
        field for field in NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS if field not in row
    ]
    issues = []
    if missing_fields:
        issues.append("missing_contract_fields")
    if forbidden_output_keys:
        issues.append("forbidden_raw_output_keys")
    if unexpected_true_boundary_fields:
        issues.append("unboundary_fields_true")
    if bad_hash_fields:
        issues.append("bad_hash_fields")
    if future_fields_missing:
        issues.append("missing_future_logger_fields")
    return {
        "ok": not issues,
        "issues": issues,
        "missing_fields": missing_fields,
        "forbidden_output_keys": forbidden_output_keys,
        "unexpected_true_boundary_fields": unexpected_true_boundary_fields,
        "bad_hash_fields": bad_hash_fields,
        "future_fields_missing": future_fields_missing,
        "field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS),
        "present_field_count": sum(1 for field in NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS if field in row),
        "future_logger_field_count": len(NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS),
        "result_use_status": row.get("result_use_status"),
        "validation_result_status": row.get("validation_result_status"),
        "outcome_result_rows_status": row.get("outcome_result_rows_status"),
        "broker_runtime_change_status": row.get("broker_runtime_change_status"),
    }


def project_nofill_forward_source_capture_row(**fields: Any) -> dict[str, Any]:
    return build_nofill_forward_source_capture_row(**fields)


def record_nofill_forward_source_capture(
    row: dict[str, Any],
    log_path: str | Path = NOFILL_FORWARD_SOURCE_CAPTURE_PATH,
) -> None:
    """Append a sanitized NOFILL source-capture row. Never raises."""
    try:
        started_at = utc_now_iso()
        completed_at = utc_now_iso()
        payload_fields = dict(row)
        payload_fields.setdefault("capture_write_started_at_utc", started_at)
        payload_fields.setdefault("capture_write_completed_at_utc", completed_at)
        payload = build_nofill_forward_source_capture_row(**payload_fields)
        append_jsonl(log_path, payload)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to write NOFILL forward source-capture row (non-blocking): %s",
            exc,
        )
    return None


def _scid_hash(value: Any) -> str:
    return _sha256_json(
        {
            "schema": SCID_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION,
            "value": _json_safe(value),
        }
    )


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "009abcdef" for ch in value)
    )


def _scid_iso(value: Any, fallback: Any | None = None) -> str:
    candidate = value if _capture_value_present(value) else fallback
    parsed = _parse_capture_datetime(candidate)
    if parsed is None:
        return utc_now_iso()
    return parsed.isoformat()


def _scid_decision_asof(fields: dict[str, Any]) -> str:
    return _scid_iso(
        fields.get("decision_asof_utc")
        or fields.get("decision_time_utc")
        or fields.get("capture_observed_at_utc")
        or fields.get("source_event_utc")
        or fields.get("timestamp_utc")
        or fields.get("created_at_utc")
    )


def _scid_source_asof(fields: dict[str, Any], decision_asof_utc: str) -> str:
    return _scid_iso(
        fields.get("source_observed_asof_utc")
        or fields.get("publication_or_capture_asof_utc")
        or fields.get("source_event_utc")
        or fields.get("entry_reference_time_utc")
        or fields.get("decision_time_utc"),
        decision_asof_utc,
    )


def _scid_candidate_input_row_id(fields: dict[str, Any]) -> str:
    for name in ("candidate_input_row_id", "candidate_id", "trade_id", "pending_intent_id"):
        value = fields.get(name)
        if _capture_value_present(value):
            return str(value)
    return "runtime_candidate:" + _scid_hash(
        {
            "symbol": fields.get("symbol"),
            "decision_time_utc": fields.get("decision_time_utc"),
            "source_event_utc": fields.get("source_event_utc"),
        }
    )[:24]


def _scid_duplicate_key(fields: dict[str, Any], field_group: str, candidate_id: str) -> str:
    value = fields.get("duplicate_proxy_denominator_key")
    if _capture_value_present(value):
        return str(value)
    return _scid_hash(
        {
            "candidate_input_row_id": candidate_id,
            "field_group": field_group,
            "symbol": fields.get("symbol"),
            "decision_time_utc": fields.get("decision_time_utc"),
        }
    )


def _scid_source_identifier(fields: dict[str, Any], field_group: str, candidate_id: str) -> str:
    value = fields.get("source_identifier")
    if _capture_value_present(value):
        return str(value)
    return f"runtime://gtos/scid_forward_capture/{field_group}/{candidate_id}"


def _scid_snapshot_hash(*values: Any) -> str:
    return _scid_hash({"values": values})


def _normalize_side(value: Any) -> str:
    normalized = str(value or "").strip().upper()
    if normalized in {"BUY", "BULL", "BULLISH", "LONG"}:
        return "LONG"
    if normalized in {"SELL", "BEAR", "BEARISH", "SHORT"}:
        return "SHORT"
    if normalized in {"NEUTRAL", "FLAT"}:
        return "NEUTRAL"
    return "NO_STRATEGY"


def _normalize_poi_type(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if "breaker" in normalized:
        return "breaker"
    if normalized in {"ob", "order_block", "orderblock"} or "order" in normalized:
        return "ob"
    if normalized in {"fvg", "fair_value_gap"} or "fvg" in normalized:
        return "fvg"
    if "swing" in normalized:
        return "swing"
    if normalized in {"", "none", "null"}:
        return "none"
    return "other"


def _scid_common_row(
    field_group: str,
    fields: dict[str, Any],
    *,
    unavailable: bool = False,
    source_payload: Any | None = None,
) -> dict[str, Any]:
    decision_asof = _scid_decision_asof(fields)
    source_asof = _scid_source_asof(fields, decision_asof)
    candidate_id = _scid_candidate_input_row_id(fields)
    source_hash_policy = (
        SCID_SOURCE_HASH_DEFERRED if unavailable else SCID_SOURCE_HASH_STRICT
    )
    source_hash = None if unavailable else _scid_hash(source_payload or fields)
    row: dict[str, Any] = {
        "schema_version": SCID_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION,
        "route_id": SCID_FORWARD_SOURCE_CAPTURE_ROUTE_ID,
        "evidence_class": SCID_FORWARD_SOURCE_CAPTURE_EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        "result_use_status": RESULT_USE_STATUS,
        "validation_result_status": False,
        "outcome_result_rows_status": False,
        "broker_runtime_change_status": False,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_strategy_edge_claims": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_live_restart": False,
        "opens_live_trading_behavior": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "candidate_input_row_id": candidate_id,
        "duplicate_proxy_denominator_key": _scid_duplicate_key(fields, field_group, candidate_id),
        "field_group": field_group,
        "decision_asof_utc": decision_asof,
        "source_observed_asof_utc": source_asof,
        "source_identifier": _scid_source_identifier(fields, field_group, candidate_id),
        "source_hash": source_hash,
        "source_symbol": fields.get("source_symbol"),
        "symbol": fields.get("symbol"),
        "route_session": (
            fields.get("route_session")
            or fields.get("session")
            or fields.get("session_tag")
            or fields.get("kill_zone")
            or "unknown_session"
        ),
        "side": fields.get("side") or (fields.get("trade_parameters") or {}).get("direction"),
        "source_hash_policy": source_hash_policy,
        "redaction_policy_id": SCID_REDACTION_POLICY_ID,
        "forbidden_value_policy_id": SCID_FORBIDDEN_VALUE_POLICY_ID,
        "missing_status_policy": SCID_MISSING_STATUS_POLICY,
        "field_status": SCID_FIELD_UNAVAILABLE if unavailable else SCID_FIELD_CAPTURED,
        "downstream_g12_acceptance_rule": SCID_DOWNSTREAM_G12_ACCEPTANCE_RULE,
    }
    enrich_cp281_event_contract_fields(row, source_path=SCID_FORWARD_SOURCE_CAPTURE_PATH)
    return row


def build_scid_baseline_control_fields(**fields: Any) -> dict[str, Any]:
    decision = _parse_capture_datetime(_scid_decision_asof(fields))
    hour = decision.hour if decision else 0
    if 0 <= hour < 7:
        time_bucket = "asian_pre_london"
    elif 7 <= hour < 12:
        time_bucket = "london"
    elif 12 <= hour < 17:
        time_bucket = "new_york"
    else:
        time_bucket = "post_ny"
    group = "baseline_control_fields"
    row = _scid_common_row(group, fields, source_payload=fields)
    row.update(
        {
            "partition_assignment": fields.get("partition_assignment")
            or "FORWARD_CAPTURE_CONTROL_ONLY_UNPARTITIONED",
            "symbol": fields.get("symbol"),
            "session_bucket": fields.get("session_bucket")
            or fields.get("kill_zone")
            or fields.get("session")
            or "unknown_session",
            "time_of_day_bucket": fields.get("time_of_day_bucket") or time_bucket,
            "baseline_family_session_only_volatility_only_random_proxy_matched": fields.get(
                "baseline_family_session_only_volatility_only_random_proxy_matched"
            )
            or "session_only",
            "baseline_assignment_seed": fields.get("baseline_assignment_seed")
            or _scid_hash(
                {
                    "candidate": row["candidate_input_row_id"],
                    "symbol": fields.get("symbol"),
                    "session": fields.get("session") or fields.get("kill_zone"),
                }
            )[:32],
            "baseline_duplicate_policy_id": fields.get("baseline_duplicate_policy_id")
            or "SCID_FORWARD_CAPTURE_DUPLICATE_KEY_BY_CANDIDATE_AND_GROUP_V1",
        }
    )
    return {key: _json_safe(value) for key, value in row.items()}


def build_scid_framework_setup_family(**fields: Any) -> dict[str, Any]:
    group = "framework_setup_family"
    frameworks = fields.get("frameworks_evaluated") or {}
    if isinstance(frameworks, dict):
        framework_names = sorted(str(key) for key in frameworks)
        qualified = {}
        for key, value in frameworks.items():
            if isinstance(value, dict):
                qualified[str(key)] = bool(value.get("qualified"))
            else:
                qualified[str(key)] = bool(value)
    elif isinstance(frameworks, (list, tuple, set)):
        framework_names = sorted(str(item) for item in frameworks)
        qualified = {name: True for name in framework_names}
    else:
        framework_names = []
        qualified = {}
    selected = fields.get("selected_framework_or_none") or fields.get("framework")
    if selected and str(selected) not in framework_names:
        framework_names.append(str(selected))
    payload = {
        "frameworks_evaluated": frameworks,
        "selected_framework": selected,
        "h1_setup": fields.get("h1_setup"),
    }
    row = _scid_common_row(group, fields, source_payload=payload)
    row.update(
        {
            "frameworks_evaluated": framework_names,
            "framework_qualified_flags": qualified,
            "selected_framework_or_none": str(selected) if _capture_value_present(selected) else None,
            "setup_family": fields.get("setup_family")
            or str(selected or fields.get("analysis_decision") or "unknown_setup_family"),
            "framework_tiebreak_rule_id": fields.get("framework_tiebreak_rule_id")
            or "ADR006_PARALLEL_EVALUATION_FRAMEWORK_NEUTRAL_TIEBREAK_V1",
            "framework_source_snapshot_hash": fields.get("framework_source_snapshot_hash")
            or _scid_snapshot_hash(payload),
        }
    )
    return {key: _json_safe(value) for key, value in row.items()}


def build_scid_future_orderflow_depth_proxy_requirements(**fields: Any) -> dict[str, Any]:
    group = "future_orderflow_depth_proxy_requirements"
    external = fields.get("external_confluence") or {}
    sierra = external.get("sierra") if isinstance(external, dict) else {}
    if not isinstance(sierra, dict):
        sierra = {}
    status = str(sierra.get("status") or "")
    depth_path = sierra.get("depth_path")
    available = bool(depth_path) and "MISSING" not in status and "FAILED" not in status
    unavailable = not available
    source_family = "depth" if available else "unavailable"
    source_pointer = str(depth_path) if available else None
    source_asof = (
        sierra.get("file_mtime_utc")
        or fields.get("publication_or_capture_asof_utc")
        or fields.get("decision_time_utc")
    )
    derived_schema = "sierra_depth_feature_schema_deferred_v1" if available else None
    source_payload = {
        "symbol": fields.get("symbol"),
        "source_system": sierra.get("source_system"),
        "status": status,
        "depth_path": source_pointer,
        "source_symbol": sierra.get("source_symbol"),
        "file_mtime_utc": sierra.get("file_mtime_utc"),
    }
    row = _scid_common_row(
        group,
        {**fields, "publication_or_capture_asof_utc": source_asof},
        unavailable=unavailable,
        source_payload=source_payload,
    )
    row.update(
        {
            "proxy_instrument": sierra.get("source_symbol") or sierra.get("futures_symbol"),
            "proxy_contract_month": fields.get("proxy_contract_month"),
            "source_family_scid_depth_mbo_mbp_other": source_family,
            "source_file_pointer_or_vendor_cache_id": source_pointer,
            "proxy_mapping_version": sierra.get("proxy_class") or fields.get("proxy_mapping_version"),
            "publication_or_capture_asof_utc": _scid_iso(source_asof, row["decision_asof_utc"]),
            "derived_feature_schema_version": derived_schema,
            "orderflow_proxy_availability_status": (
                "AVAILABLE" if available else "UNAVAILABLE_FAIL_CLOSED"
            ),
        }
    )
    return {key: _json_safe(value) for key, value in row.items()}


def build_scid_intended_entry_reference(**fields: Any) -> dict[str, Any]:
    group = "intended_entry_reference"
    tp = fields.get("trade_parameters") or {}
    price = fields.get("entry_reference_price")
    if price is None:
        price = tp.get("entry_price") if isinstance(tp, dict) else None
    entry_type = fields.get("entry_reference_type_market_limit_zone_midpoint_other")
    if not entry_type:
        final_outcome = str(fields.get("final_outcome") or "").upper()
        pending_mode = fields.get("pending_order_mode")
        entry_type = "limit" if pending_mode or "LIMIT" in final_outcome else "market"
    source_timeframe = fields.get("entry_source_timeframe") or "decision_packet"
    payload = {"entry_price": price, "entry_type": entry_type, "trade_parameters": tp}
    row = _scid_common_row(group, fields, source_payload=payload)
    row.update(
        {
            "entry_reference_type_market_limit_zone_midpoint_other": str(entry_type).lower()
            if str(entry_type).lower() in SCID_ENUMS["entry_reference_type_market_limit_zone_midpoint_other"]
            else "other",
            "entry_reference_price": price,
            "entry_reference_time_utc": _scid_iso(
                fields.get("entry_reference_time_utc") or fields.get("decision_time_utc"),
                row["decision_asof_utc"],
            ),
            "entry_source_timeframe": source_timeframe,
            "entry_source_bar_hash_or_mso_snapshot_hash": fields.get(
                "entry_source_bar_hash_or_mso_snapshot_hash"
            )
            or _scid_snapshot_hash(fields.get("mso_summary"), fields.get("h1_setup"), tp),
        }
    )
    return {key: _json_safe(value) for key, value in row.items()}


def build_scid_intended_side_direction(**fields: Any) -> dict[str, Any]:
    group = "intended_side_direction"
    tp = fields.get("trade_parameters") or {}
    side = fields.get("strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY")
    if not side:
        side = fields.get("side") or fields.get("direction")
    if not side and isinstance(tp, dict):
        side = tp.get("direction")
    normalized = _normalize_side(side)
    payload = {
        "side": side,
        "analysis_decision": fields.get("analysis_decision"),
        "framework": fields.get("framework"),
        "trade_parameters": tp,
    }
    row = _scid_common_row(group, fields, source_payload=payload)
    row.update(
        {
            "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY": normalized,
            "side_source_component": fields.get("side_source_component")
            or "primary_analyzer_candidate_packet",
            "side_source_rule_or_model_hash": fields.get("side_source_rule_or_model_hash")
            or _scid_snapshot_hash(payload),
            "side_emission_reason_code": fields.get("side_emission_reason_code")
            or str(fields.get("analysis_decision") or "candidate_packet_side_field"),
        }
    )
    return {key: _json_safe(value) for key, value in row.items()}


def build_scid_intended_stop_reference(**fields: Any) -> dict[str, Any]:
    group = "intended_stop_reference"
    tp = fields.get("trade_parameters") or {}
    stop_price = fields.get("stop_reference_price")
    if stop_price is None and isinstance(tp, dict):
        stop_price = tp.get("stop_loss")
    payload = {"stop_reference_price": stop_price, "trade_parameters": tp}
    row = _scid_common_row(group, fields, source_payload=payload)
    row.update(
        {
            "stop_reference_price": stop_price,
            "stop_reference_type": fields.get("stop_reference_type")
            or "candidate_trade_parameters_stop_loss",
            "stop_buffer_rule_id": fields.get("stop_buffer_rule_id")
            or "CONFIGURED_SL_BUFFER_RULE_CAPTURED_BY_DECISION_PACKET",
            "stop_source_structure_id": fields.get("stop_source_structure_id")
            or str((fields.get("h1_setup") or {}).get("poi_type") or "unknown_structure"),
            "stop_source_snapshot_hash": fields.get("stop_source_snapshot_hash")
            or _scid_snapshot_hash(fields.get("h1_setup"), tp),
        }
    )
    return {key: _json_safe(value) for key, value in row.items()}


def build_scid_intended_target_reference(**fields: Any) -> dict[str, Any]:
    group = "intended_target_reference"
    tp = fields.get("trade_parameters") or {}
    target_price = fields.get("target_reference_price")
    if target_price is None and isinstance(tp, dict):
        target_price = tp.get("take_profit_1")
    rr = fields.get("risk_reward_reference")
    if rr is None and isinstance(tp, dict):
        rr = tp.get("risk_reward") or tp.get("risk_reward_ratio")
    payload = {"target_reference_price": target_price, "risk_reward_reference": rr, "trade_parameters": tp}
    row = _scid_common_row(group, fields, source_payload=payload)
    row.update(
        {
            "target_reference_price": target_price,
            "target_reference_type": fields.get("target_reference_type")
            or "candidate_trade_parameters_take_profit_1",
            "target_rule_id": fields.get("target_rule_id")
            or "MODEL_A_CONFIGURED_RR_TARGET_CAPTURED_BY_DECISION_PACKET",
            "risk_reward_reference": rr,
            "target_source_snapshot_hash": fields.get("target_source_snapshot_hash")
            or _scid_snapshot_hash(fields.get("h1_setup"), tp),
        }
    )
    return {key: _json_safe(value) for key, value in row.items()}


def _scid_lifecycle_event_type(fields: dict[str, Any]) -> str:
    explicit = str(
        fields.get("source_event_type_created_updated_expired_cancelled_replaced_no_order")
        or ""
    ).strip().lower()
    if explicit in SCID_ENUMS["source_event_type_created_updated_expired_cancelled_replaced_no_order"]:
        return explicit
    state = str(fields.get("intent_state_after") or fields.get("intent_after_check") or "").lower()
    reason = str(fields.get("reason") or fields.get("cancel_reason") or "").lower()
    if "expired" in state or "expired" in reason:
        return "expired"
    if "cancel" in state or "wrong_side" in state or "too_close" in state:
        return "cancelled"
    if "created" in state:
        return "created"
    if "replace" in state:
        return "replaced"
    if "no_order" in state:
        return "no_order"
    return "updated"


def build_scid_lifecycle_fill_cancel_expiry_source_status(**fields: Any) -> dict[str, Any]:
    group = "lifecycle_fill_cancel_expiry_source_status"
    event_time = (
        fields.get("source_event_utc")
        or fields.get("checked_candle_time_utc")
        or fields.get("timestamp_utc")
        or fields.get("created_at_utc")
        or fields.get("decision_time_utc")
    )
    payload = {
        "candidate_id": fields.get("candidate_id"),
        "trade_id": fields.get("trade_id"),
        "intent_after_check": fields.get("intent_after_check"),
        "reason": fields.get("reason"),
        "checked_candle_time_utc": fields.get("checked_candle_time_utc"),
    }
    row = _scid_common_row(
        group,
        {**fields, "source_event_utc": event_time, "decision_asof_utc": event_time},
        source_payload=payload,
    )
    pending_intent_id = (
        fields.get("pending_intent_id")
        or fields.get("candidate_id")
        or fields.get("trade_id")
        or _scid_hash(payload)[:32]
    )
    row.update(
        {
            "pending_intent_id": str(pending_intent_id),
            "source_event_type_created_updated_expired_cancelled_replaced_no_order": _scid_lifecycle_event_type(fields),
            "source_event_utc": _scid_iso(event_time, row["decision_asof_utc"]),
            "source_event_clock_basis": fields.get("source_event_clock_basis")
            or "SYSTEM_UTC_OR_CANDLE_CLOSE_UTC_SOURCE_SAFE",
            "intent_state_before": fields.get("intent_state_before")
            or fields.get("last_limit_check_candle_time_before"),
            "intent_state_after": fields.get("intent_state_after")
            or fields.get("intent_after_check")
            or "unknown_state",
            "redacted_order_bridge_hash_optional": None,
        }
    )
    return {key: _json_safe(value) for key, value in row.items()}


def build_scid_lower_timeframe_asof_path_availability(**fields: Any) -> dict[str, Any]:
    group = "lower_timeframe_asof_path_availability"
    timeframes = fields.get("ltf_timeframes_available")
    if timeframes is None:
        timeframes = fields.get("lower_timeframes_available")
    if timeframes is None:
        timeframes = []
    available = bool(timeframes) and bool(fields.get("ltf_source_hash") or fields.get("ltf_source_file_pointer_or_cache_id"))
    payload = {
        "ltf_timeframes_available": timeframes,
        "ltf_source_file_pointer_or_cache_id": fields.get("ltf_source_file_pointer_or_cache_id"),
        "bars_present_by_timeframe": fields.get("bars_present_by_timeframe") or {},
    }
    row = _scid_common_row(group, fields, unavailable=not available, source_payload=payload)
    decision_dt = _parse_capture_datetime(row["decision_asof_utc"])
    if decision_dt is None:
        window_start = row["decision_asof_utc"]
    else:
        window_start = (decision_dt - timedelta(minutes=60)).isoformat()
    row.update(
        {
            "ltf_timeframes_available": [str(item) for item in timeframes],
            "ltf_source_file_pointer_or_cache_id": fields.get("ltf_source_file_pointer_or_cache_id"),
            "ltf_source_hash": fields.get("ltf_source_hash") if available else None,
            "decision_minus_window_start_utc": fields.get("decision_minus_window_start_utc")
            or window_start,
            "bars_present_by_timeframe": fields.get("bars_present_by_timeframe") or {},
            "asof_path_descriptor_version": fields.get("asof_path_descriptor_version")
            or "SCID_LTF_ASOF_PATH_DESCRIPTOR_V1",
            "ltf_availability_status": "AVAILABLE" if available else "UNAVAILABLE_FAIL_CLOSED",
        }
    )
    return {key: _json_safe(value) for key, value in row.items()}


def build_scid_poi_type_bounds_source(**fields: Any) -> dict[str, Any]:
    group = "poi_type_bounds_source"
    h1_setup = fields.get("h1_setup") or {}
    geometry = fields.get("fvg_ob_geometry") or {}
    poi_type = fields.get("poi_type_enum_ob_fvg_breaker_swing_other_none")
    if not poi_type and isinstance(h1_setup, dict):
        poi_type = h1_setup.get("poi_type")
    normalized = _normalize_poi_type(poi_type)
    bounds_source = {}
    if isinstance(geometry, dict):
        if normalized == "fvg":
            bounds_source = geometry.get("fvg_bounds") or {}
        elif normalized == "ob":
            bounds_source = geometry.get("ob_bounds") or {}
    lower = fields.get("poi_lower_bound")
    upper = fields.get("poi_upper_bound")
    if lower is None:
        lower = bounds_source.get("lower") or bounds_source.get("low")
    if upper is None:
        upper = bounds_source.get("upper") or bounds_source.get("high")
    if lower is None and isinstance(h1_setup, dict):
        lower = h1_setup.get("poi_price_level")
    if upper is None and lower is not None:
        upper = lower
    payload = {
        "h1_setup": h1_setup,
        "geometry": geometry,
        "poi_type": normalized,
        "lower": lower,
        "upper": upper,
    }
    row = _scid_common_row(group, fields, source_payload=payload)
    row.update(
        {
            "poi_type_enum_ob_fvg_breaker_swing_other_none": normalized,
            "poi_lower_bound": lower,
            "poi_upper_bound": upper,
            "poi_source_timeframe": fields.get("poi_source_timeframe") or "H1",
            "poi_source_bar_ids": fields.get("poi_source_bar_ids") or [],
            "mso_snapshot_hash": fields.get("mso_snapshot_hash")
            or _scid_snapshot_hash(fields.get("mso_summary"), h1_setup, geometry),
            "poi_detection_rule_version": fields.get("poi_detection_rule_version")
            or "GTOS_MARKET_STATE_POI_DETECTION_RUNTIME_V1",
        }
    )
    return {key: _json_safe(value) for key, value in row.items()}


SCID_GROUP_BUILDERS = {
    "baseline_control_fields": build_scid_baseline_control_fields,
    "framework_setup_family": build_scid_framework_setup_family,
    "future_orderflow_depth_proxy_requirements": build_scid_future_orderflow_depth_proxy_requirements,
    "intended_entry_reference": build_scid_intended_entry_reference,
    "intended_side_direction": build_scid_intended_side_direction,
    "intended_stop_reference": build_scid_intended_stop_reference,
    "intended_target_reference": build_scid_intended_target_reference,
    "lifecycle_fill_cancel_expiry_source_status": build_scid_lifecycle_fill_cancel_expiry_source_status,
    "lower_timeframe_asof_path_availability": build_scid_lower_timeframe_asof_path_availability,
    "poi_type_bounds_source": build_scid_poi_type_bounds_source,
}


def build_scid_forward_source_capture_row(
    candidate_packet: dict[str, Any] | None = None,
    group_context: dict[str, Any] | None = None,
    **fields: Any,
) -> dict[str, Any]:
    """Build one SCID source-safe row for an accepted capture group."""
    payload: dict[str, Any] = {}
    if candidate_packet:
        payload.update(candidate_packet)
    if group_context:
        payload.update(group_context)
    payload.update(fields)
    field_group = str(payload.get("field_group") or "")
    if field_group not in SCID_GROUP_BUILDERS:
        raise ValueError(f"unknown SCID capture group: {field_group}")
    return SCID_GROUP_BUILDERS[field_group](**payload)


def _scid_forbidden_keys(value: Any, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_str = str(key)
            lowered = key_str.lower()
            full = f"{prefix}.{key_str}" if prefix else key_str
            if key_str not in SCID_SCHEMA_FIELD_NAMES and (
                lowered in SCID_FORBIDDEN_RAW_FIELD_NAMES or any(
                    fragment in lowered for fragment in SCID_FORBIDDEN_KEY_FRAGMENTS
                )
            ):
                keys.append(full)
            keys.extend(_scid_forbidden_keys(item, full))
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            keys.extend(_scid_forbidden_keys(item, f"{prefix}[{index}]"))
    return keys


def _scid_allowed_null(field: str, row: dict[str, Any]) -> bool:
    if field in SCID_NULLABLE_FIELDS:
        return True
    if field == "source_hash" and row.get("source_hash_policy") == SCID_SOURCE_HASH_DEFERRED:
        return True
    return False


def validate_scid_forward_source_capture_row(
    row: dict[str, Any],
    duplicate_key_registry: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Validate one SCID source-capture row without opening outcome scoring."""
    field_group = row.get("field_group")
    allowed_fields = set(SCID_COMMON_FIELDS)
    if field_group in SCID_GROUP_FIELDS:
        allowed_fields.update(SCID_GROUP_FIELDS[str(field_group)])
    missing_fields = [
        field for field in SCID_REQUIRED_FIELDS.get(str(field_group), SCID_COMMON_FIELDS) if field not in row
    ]
    null_required_fields = [
        field
        for field in SCID_REQUIRED_FIELDS.get(str(field_group), SCID_COMMON_FIELDS)
        if field in row and row.get(field) is None and not _scid_allowed_null(field, row)
    ]
    extra_fields = sorted(set(row) - allowed_fields)
    forbidden_keys = sorted(set(_scid_forbidden_keys(row)))
    unexpected_true_boundary_fields = [
        flag for flag in SCID_BOUNDARY_FALSE_FIELDS if row.get(flag) is not False
    ]
    bad_constants = []
    if row.get("schema_version") != SCID_FORWARD_SOURCE_CAPTURE_SCHEMA_VERSION:
        bad_constants.append("schema_version")
    if row.get("route_id") != SCID_FORWARD_SOURCE_CAPTURE_ROUTE_ID:
        bad_constants.append("route_id")
    if row.get("evidence_class") != SCID_FORWARD_SOURCE_CAPTURE_EVIDENCE_CLASS:
        bad_constants.append("evidence_class")
    if row.get("result_use_status") != RESULT_USE_STATUS:
        bad_constants.append("result_use_status")
    if row.get("redaction_policy_id") != SCID_REDACTION_POLICY_ID:
        bad_constants.append("redaction_policy_id")
    if row.get("forbidden_value_policy_id") != SCID_FORBIDDEN_VALUE_POLICY_ID:
        bad_constants.append("forbidden_value_policy_id")

    bad_enums = []
    for field, allowed in SCID_ENUMS.items():
        if field in row and row.get(field) not in allowed:
            bad_enums.append(field)

    bad_hash_fields = []
    if row.get("source_hash_policy") == SCID_SOURCE_HASH_STRICT:
        if not _is_sha256(row.get("source_hash")):
            bad_hash_fields.append("source_hash")
    elif row.get("source_hash_policy") == SCID_SOURCE_HASH_DEFERRED:
        if field_group not in {
            "future_orderflow_depth_proxy_requirements",
            "lower_timeframe_asof_path_availability",
        }:
            bad_hash_fields.append("source_hash_policy")
        if row.get("source_hash") is not None:
            bad_hash_fields.append("source_hash")
    for field in (
        "framework_source_snapshot_hash",
        "entry_source_bar_hash_or_mso_snapshot_hash",
        "side_source_rule_or_model_hash",
        "stop_source_snapshot_hash",
        "target_source_snapshot_hash",
        "ltf_source_hash",
        "mso_snapshot_hash",
    ):
        value = row.get(field)
        if value is not None and not _is_sha256(value):
            bad_hash_fields.append(field)

    stale_asof = False
    decision_dt = _parse_capture_datetime(row.get("decision_asof_utc"))
    source_dt = _parse_capture_datetime(row.get("source_observed_asof_utc"))
    if decision_dt is None or source_dt is None or source_dt > decision_dt:
        stale_asof = True
    publication_dt = _parse_capture_datetime(row.get("publication_or_capture_asof_utc"))
    if publication_dt is not None and decision_dt is not None and publication_dt > decision_dt:
        stale_asof = True
    source_event_dt = _parse_capture_datetime(row.get("source_event_utc"))
    if source_event_dt is not None and decision_dt is not None and source_event_dt > decision_dt:
        stale_asof = True

    duplicate_drift = False
    duplicate_key = row.get("duplicate_proxy_denominator_key")
    source_hash = row.get("source_hash")
    if duplicate_key_registry is not None and _capture_value_present(duplicate_key):
        existing = duplicate_key_registry.get(str(duplicate_key))
        candidate = str(source_hash)
        if existing is None:
            duplicate_key_registry[str(duplicate_key)] = candidate
        elif existing != candidate:
            duplicate_drift = True

    issues = []
    if field_group not in SCID_CAPTURE_GROUPS:
        issues.append("unknown_field_group")
    if missing_fields:
        issues.append("missing_required_fields")
    if null_required_fields:
        issues.append("null_required_fields")
    if extra_fields:
        issues.append("unexpected_fields")
    if forbidden_keys:
        issues.append("forbidden_raw_fields")
    if unexpected_true_boundary_fields:
        issues.append("unboundary_fields_true")
    if bad_constants:
        issues.append("bad_schema_constants")
    if bad_enums:
        issues.append("bad_enum_values")
    if bad_hash_fields:
        issues.append("bad_hash_fields")
    if stale_asof:
        issues.append("stale_or_invalid_asof")
    if duplicate_drift:
        issues.append("duplicate_key_drift")

    return {
        "ok": not issues,
        "issues": issues,
        "field_group": field_group,
        "missing_fields": missing_fields,
        "null_required_fields": null_required_fields,
        "extra_fields": extra_fields,
        "forbidden_keys": forbidden_keys,
        "unexpected_true_boundary_fields": unexpected_true_boundary_fields,
        "bad_constants": bad_constants,
        "bad_enums": bad_enums,
        "bad_hash_fields": sorted(set(bad_hash_fields)),
        "stale_asof": stale_asof,
        "duplicate_key_drift": duplicate_drift,
        "present_field_count": len(row),
        "required_field_count": len(SCID_REQUIRED_FIELDS.get(str(field_group), SCID_COMMON_FIELDS)),
        "result_use_status": row.get("result_use_status"),
        "validation_result_status": row.get("validation_result_status"),
        "outcome_result_rows_status": row.get("outcome_result_rows_status"),
        "broker_runtime_change_status": row.get("broker_runtime_change_status"),
    }


def record_scid_forward_capture_group(
    row: dict[str, Any],
    log_path: str | Path = SCID_FORWARD_SOURCE_CAPTURE_PATH,
) -> bool:
    """Append one validated SCID capture row. Fail-open for live callers."""
    try:
        validation = validate_scid_forward_source_capture_row(row)
        if not validation["ok"]:
            logger.warning(
                "Rejected SCID forward source-capture row for %s: %s",
                row.get("field_group"),
                validation["issues"],
            )
            return False
        append_jsonl(log_path, row)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to write SCID forward source-capture row (non-blocking): %s",
            exc,
        )
        return False


def record_scid_forward_capture_candidate_groups(
    fields: dict[str, Any],
    *,
    fvg_ob_geometry: dict[str, Any] | None = None,
    log_path: str | Path = SCID_FORWARD_SOURCE_CAPTURE_PATH,
) -> dict[str, bool]:
    """Emit the candidate-time SCID capture group rows. Never raises."""
    statuses: dict[str, bool] = {}
    try:
        payload = {**fields, "fvg_ob_geometry": fvg_ob_geometry or {}}
        for group in (
            "baseline_control_fields",
            "framework_setup_family",
            "future_orderflow_depth_proxy_requirements",
            "intended_entry_reference",
            "intended_side_direction",
            "intended_stop_reference",
            "intended_target_reference",
            "lower_timeframe_asof_path_availability",
            "poi_type_bounds_source",
        ):
            row = build_scid_forward_source_capture_row(
                payload,
                {"field_group": group},
            )
            statuses[group] = record_scid_forward_capture_group(row, log_path=log_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to write SCID candidate capture groups (non-blocking): %s",
            exc,
        )
    return statuses


def record_scid_forward_capture_lifecycle_event(
    lifecycle_event: dict[str, Any],
    candidate_context: dict[str, Any] | None = None,
    log_path: str | Path = SCID_FORWARD_SOURCE_CAPTURE_PATH,
) -> bool:
    """Append a redacted lifecycle SCID capture row. Never raises."""
    try:
        payload = {**(candidate_context or {}), **(lifecycle_event or {})}
        row = build_scid_forward_source_capture_row(
            payload,
            {"field_group": "lifecycle_fill_cancel_expiry_source_status"},
        )
        return record_scid_forward_capture_group(row, log_path=log_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to write SCID lifecycle capture row (non-blocking): %s",
            exc,
        )
        return False


def _safe_get(obj: Any, name: str, default: Any = None) -> Any:
    try:
        value = getattr(obj, name)
        return default if value is None else value
    except Exception:
        pass
    try:
        value = obj[name]  # type: ignore[index]
        return default if value is None else value
    except Exception:
        return default


def _safe_model_dump(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    try:
        return obj.model_dump(mode="json")
    except Exception:
        pass
    if isinstance(obj, dict):
        return obj
    return {}


def _verification_summary(verification: Any) -> dict[str, Any]:
    if verification is None:
        return {"passed": None, "blocked_by": None, "checks": []}
    checks = []
    for check in _safe_get(verification, "checks", []) or []:
        row = {
            "name": _safe_get(check, "name"),
            "status": _safe_get(check, "status"),
            "detail": _safe_get(check, "detail"),
        }
        mso_value = _safe_get(check, "mso_value")
        ai_value = _safe_get(check, "ai_value")
        if mso_value is not None:
            row["mso_value"] = _json_safe(mso_value)
        if ai_value is not None:
            row["ai_value"] = _json_safe(ai_value)
        checks.append(row)
    return {
        "passed": _safe_get(verification, "passed"),
        "blocked_by": _safe_get(verification, "blocked_by"),
        "checks": checks,
    }


def _candidate_id_from_fields(fields: dict[str, Any]) -> str:
    candidate_id = fields.get("candidate_id")
    if candidate_id:
        return str(candidate_id)
    symbol = fields.get("symbol") or "UNKNOWN"
    decision_time = str(fields.get("decision_time_utc") or "unknown")
    return f"{symbol}_{decision_time}"


def _pending_limit_intent_snapshot(
    *,
    final_outcome: str | None,
    record: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return explicit native-vs-internal pending-order telemetry fields."""
    limit_intent = (
        (record or {}).get("limit_intent") if isinstance(record, dict) else None
    ) or {}
    is_limit_placed = final_outcome == "LIMIT_PLACED" or bool(limit_intent)
    if not is_limit_placed:
        return {
            "pending_order_mode": None,
            "broker_pending_order_created": None,
            "mt5_order_ticket": None,
            "native_pending_order_type": None,
        }
    return {
        "pending_order_mode": limit_intent.get("pending_order_mode")
        or INTERNAL_PENDING_ORDER_MODE,
        "broker_pending_order_created": bool(
            limit_intent.get("broker_pending_order_created", False)
        ),
        "mt5_order_ticket": limit_intent.get("mt5_order_ticket"),
        "native_pending_order_type": limit_intent.get("native_pending_order_type"),
    }


def build_live_candidate_identity(
    *,
    symbol: str,
    broker_symbol: str | None,
    source_symbol: str | None = None,
    kill_zone: str | None = None,
    analysis: Any,
    mso: Any = None,
    record: dict[str, Any] | None = None,
    verification: Any = None,
    final_outcome: str | None = None,
    trade_id: str | None = None,
) -> dict[str, Any]:
    """Return the stable candidate identity fields used by live shadow logs.

    This lets execution telemetry and candidate snapshot rows share the same
    deterministic candidate key without importing trading code into the research
    logger or re-running any AI/canary path.
    """
    fields = _extract_candidate_fields(
        symbol=symbol,
        broker_symbol=broker_symbol,
        source_symbol=source_symbol,
        kill_zone=kill_zone,
        analysis=analysis,
        mso=mso,
        record=record,
        verification=verification,
        final_outcome=final_outcome,
        trade_id=trade_id,
    )
    fields["candidate_id"] = _candidate_id_from_fields(fields)
    return {
        "candidate_id": fields.get("candidate_id"),
        "decision_time_utc": fields.get("decision_time_utc"),
        "source_file": fields.get("source_file"),
        "source_hash": fields.get("source_hash"),
        "source_symbol": fields.get("source_symbol"),
        "market_timeframe": fields.get("market_timeframe"),
        "route_session": fields.get("route_session"),
        "horizon_id": fields.get("horizon_id"),
        "source_component": fields.get("source_component"),
        "selected_side": fields.get("selected_side"),
        "session": fields.get("session"),
        "kill_zone": fields.get("kill_zone"),
        "side": fields.get("side"),
        "regime": fields.get("regime"),
    }


def _extract_candidate_fields(
    *,
    symbol: str,
    broker_symbol: str | None,
    source_symbol: str | None,
    kill_zone: str | None,
    analysis: Any,
    mso: Any = None,
    record: dict[str, Any] | None = None,
    verification: Any = None,
    final_outcome: str | None = None,
    trade_id: str | None = None,
) -> dict[str, Any]:
    analysis_dict = _safe_model_dump(analysis)
    reasoning = _safe_get(analysis, "reasoning")
    reasoning_dict = _safe_model_dump(reasoning)
    trade_params = _safe_get(analysis, "trade_parameters")
    tp_dict = _safe_model_dump(trade_params)
    h1_setup = _safe_get(reasoning, "h1_setup")
    h1_dict = _safe_model_dump(h1_setup)
    m15_confirmation = _safe_get(reasoning, "m15_confirmation")
    m15_dict = _safe_model_dump(m15_confirmation)
    frameworks_evaluated = _safe_get(analysis, "frameworks_evaluated")
    if frameworks_evaluated:
        frameworks_evaluated = _json_safe(_safe_model_dump(frameworks_evaluated) or frameworks_evaluated)

    record_meta = (record or {}).get("metadata", {}) if isinstance(record, dict) else {}
    instrumentation = (record or {}).get("instrumentation", {}) if isinstance(record, dict) else {}
    decision_time = (
        record_meta.get("candle_close_utc")
        or _safe_get(mso, "timestamp_utc")
        or _safe_get(analysis, "timestamp_utc")
        or utc_now_iso()
    )
    candidate_id = (
        (record or {}).get("trade_id") if isinstance(record, dict) else None
    ) or f"{symbol}_{decision_time}"
    resolved_trade_id = trade_id or (
        (record or {}).get("trade_id") if isinstance(record, dict) else None
    )
    if not resolved_trade_id and isinstance(record, dict):
        resolved_trade_id = ((record.get("limit_intent") or {}).get("trade_id"))
    pending_intent_snapshot = _pending_limit_intent_snapshot(
        final_outcome=final_outcome,
        record=record,
    )
    verification_summary = _verification_summary(verification)
    side = tp_dict.get("direction") or _safe_get(trade_params, "direction")
    base_fields = {
        "symbol": symbol,
        "broker_symbol": broker_symbol or symbol,
        "source_symbol": source_symbol,
        "market_timeframe": "M15",
        "route_session": kill_zone,
        "horizon_id": "live_candidate_decision",
        "source_component": "primary_analyzer_live_candidate",
        "selected_side": side,
        "session": kill_zone,
        "kill_zone": kill_zone,
        "side": side,
        "regime": instrumentation.get("regime_at_eval") or record_meta.get("regime"),
        "candidate_id": candidate_id,
        "trade_id": resolved_trade_id,
        "decision_time_utc": str(decision_time),
        "source_file": (record or {}).get("_source_file", "live_orchestrator_candidate_path")
        if isinstance(record, dict)
        else "live_orchestrator_candidate_path",
        "source_hash": (record or {}).get("_source_hash") if isinstance(record, dict) else None,
        "no_leak_status": "NO_POST_OUTCOME_FIELDS_IN_DECISION_CONTEXT",
        "analysis_decision": analysis_dict.get("decision"),
        "framework": analysis_dict.get("framework"),
        "frameworks_evaluated": frameworks_evaluated,
        "trade_parameters": tp_dict,
        "h1_setup": h1_dict,
        "m15_confirmation": m15_dict,
        "mso_summary": _mso_summary(mso),
        "verification": verification_summary,
        "m15_choch_diagnostic": m15_choch_decision_diagnostic(verification_summary),
        "final_outcome": final_outcome,
        "detector_version_at_eval": instrumentation.get("detector_version_at_eval"),
        **pending_intent_snapshot,
    }
    structural_fields = _decision_time_structural_fields(fields=base_fields, mso=mso)
    base_fields["decision_time_structural_fields"] = structural_fields
    base_fields["structural_selector_metadata"] = _structural_selector_metadata_from_fields(structural_fields)
    return base_fields


def _confluence_bucket(fields: dict[str, Any]) -> str:
    framework = str(fields.get("framework") or "").lower()
    poi_type = str((fields.get("h1_setup") or {}).get("poi_type") or "").lower()
    evaluated = fields.get("frameworks_evaluated") or {}
    try:
        fvg_q = bool((evaluated.get("fvg_fill") or {}).get("qualified"))
        ob_q = bool((evaluated.get("ob_retest") or {}).get("qualified"))
    except Exception:
        fvg_q = False
        ob_q = False
    if fvg_q and ob_q:
        return "both_fvg_and_ob_fire"
    if fvg_q or framework == "fvg_fill" or poi_type == "fvg":
        return "fvg_only"
    if ob_q or framework == "ob_retest" or poi_type == "ob":
        return "ob_only"
    if framework in {"breaker_re_entry", "breaker_retest"} or poi_type == "breaker_block":
        return "disagreement"
    return "no_poi"


def _strategy_snapshots(fields: dict[str, Any]) -> list[dict[str, Any]]:
    symbol = str(fields.get("symbol") or "")
    snapshots = []
    for item in FOLLOW_STRATEGY_REGISTRY:
        applicability = "candidate_relevant"
        if item["strategy_id"] == "NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC":
            applicability = "candidate_relevant" if symbol == "NAS100" else "symbol_specific_not_applicable"
        if item["family"] in {"portfolio_policy", "risk_policy"}:
            applicability = "risk_or_portfolio_context"
        snapshots.append(
            {
                **item,
                "applicability": applicability,
                "decision_time_status": "OBSERVED_AT_LIVE_CANDIDATE_TIME",
                "outcome_status": "UNRESOLVED_REQUIRES_FORWARD_JOIN",
            }
        )
    return snapshots


def _mso_summary(mso: Any) -> dict[str, Any]:
    tfs = _safe_get(mso, "timeframes", {}) or {}
    out: dict[str, Any] = {
        "timestamp_utc": _safe_get(mso, "timestamp_utc"),
        "timeframes": {},
    }
    for tf_name in ("D1", "H4", "H1", "M15"):
        try:
            tf = tfs.get(tf_name) if hasattr(tfs, "get") else tfs[tf_name]
        except Exception:
            tf = None
        if tf is None:
            continue
        structure = _safe_get(tf, "structure")
        order_blocks = _safe_get(tf, "order_blocks", []) or []
        fvgs = _safe_get(tf, "fair_value_gaps", []) or []
        breaker_blocks = _safe_get(tf, "breaker_blocks", []) or []
        out["timeframes"][tf_name] = {
            "structure_direction": _safe_get(structure, "direction"),
            "bos_detected": _safe_get(structure, "bos_detected"),
            "choch_detected": _safe_get(structure, "choch_detected"),
            "order_block_count": len(order_blocks) if hasattr(order_blocks, "__len__") else None,
            "unmitigated_order_block_count": sum(
                1 for item in order_blocks if not bool(_safe_get(item, "mitigated", False))
            )
            if isinstance(order_blocks, list)
            else None,
            "fvg_count": len(fvgs) if hasattr(fvgs, "__len__") else None,
            "breaker_block_count": len(breaker_blocks) if hasattr(breaker_blocks, "__len__") else None,
        }
    return out


def mso_summary_snapshot(mso: Any) -> dict[str, Any]:
    """Public wrapper for callers that append MSO shadow rows directly."""
    return _mso_summary(mso)


def build_strategy_follow_evaluation_row(**fields: Any) -> dict[str, Any]:
    row = common_metadata(
        **{
            **fields,
            "schema_version": "strategy_follow_evaluation_v1",
            "evidence_class": fields.get("evidence_class") or "FORWARD_SHADOW",
        }
    )
    row.update(
        {
            "evaluation_stage": fields.get("evaluation_stage") or "MSO_COMPUTED_PRE_AI",
            "ai_dependency": fields.get("ai_dependency") or "NO_AI_REQUIRED_FOR_ROW",
            "ai_status": fields.get("ai_status") or "NOT_CALLED_AT_ROW_TIME",
            "prescreen_status": fields.get("prescreen_status"),
            "deterministic_bias": fields.get("deterministic_bias"),
            "source_run_id": fields.get("source_run_id"),
            "dedupe_key": fields.get("dedupe_key"),
            "mso_summary": fields.get("mso_summary") or {},
            "strategy_snapshots": fields.get("strategy_snapshots")
            or _strategy_snapshots(fields),
            "external_confluence_policy": fields.get("external_confluence_policy")
            or {
                "sierra": "ATTACH_ON_AI_CANDIDATE_OR_PATH_FOLLOW_REFRESH",
                "databento": "USE_LIVE_STREAM_OR_TARGETED_REQUEST_ONLY_ON_REGISTERED_TRIGGER",
                "no_paid_fetch_from_this_pre_ai_row": True,
            },
            "observer_metadata": fields.get("observer_metadata") or {},
        }
    )
    return enrich_cp281_event_contract_fields(row, source_path=STRATEGY_FOLLOW_EVALUATION_PATH)


def record_strategy_follow_evaluation(
    row: dict[str, Any],
    log_path: str | Path = STRATEGY_FOLLOW_EVALUATION_PATH,
) -> None:
    append_jsonl(log_path, build_strategy_follow_evaluation_row(**row))


def record_live_mso_forward_shadow(
    *,
    symbol: str,
    broker_symbol: str | None = None,
    kill_zone: str | None = None,
    mso: Any = None,
    raw_data: dict[str, Any] | None = None,
    evaluation_stage: str = "MSO_COMPUTED_PRE_AI",
    prescreen_status: str | None = None,
    deterministic_bias: str | None = None,
    ai_status: str | None = None,
    ai_dependency: str | None = None,
    reason: str | None = None,
) -> None:
    decision_time = (
        (raw_data or {}).get("candle_close_utc")
        or _safe_get(mso, "timestamp_utc")
        or utc_now_iso()
    )
    candidate_id = f"{symbol}_{decision_time}_pre_ai"
    record_strategy_follow_evaluation(
        {
            "symbol": symbol,
            "broker_symbol": broker_symbol or symbol,
            "session": kill_zone,
            "kill_zone": kill_zone,
            "candidate_id": candidate_id,
            "trade_id": None,
            "decision_time_utc": str(decision_time),
            "source_file": "live_orchestrator_mso_pre_ai",
            "source_hash": None,
            "no_leak_status": "NO_AI_OR_POST_OUTCOME_FIELDS_IN_ROW",
            "evaluation_stage": evaluation_stage,
            "ai_dependency": ai_dependency or "NO_AI_REQUIRED_FOR_ROW",
            "ai_status": ai_status or "NOT_CALLED_AT_ROW_TIME",
            "prescreen_status": prescreen_status,
            "deterministic_bias": deterministic_bias,
            "reason": reason,
            "mso_summary": _mso_summary(mso),
        }
    )


def _parse_iso(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    except Exception:
        return None


def _file_mtime_utc(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return None


def _sierra_depth_confluence(
    fields: dict[str, Any],
    *,
    feature_mode: str = "deferred",
) -> dict[str, Any]:
    symbol = str(fields.get("symbol") or "")
    registry = registry_entry(symbol, str(fields.get("broker_symbol") or symbol))
    proxy = SIERRA_PROXY_BY_SYMBOL.get(symbol)
    source_status = SIERRA_SOURCE_STATUS_BY_SYMBOL.get(symbol) or {
        "source_status": registry.source_status,
        "parity_status": registry.parity_status,
        "interpretation_status": registry.interpretation_status,
        "proxy_class": registry.proxy_class,
        "allowed_use": registry.allowed_use,
        "claim_boundary": registry.claim_boundary,
        "depth_interpretation_allowed": registry.depth_interpretation_allowed,
        "scid_interpretation_allowed": registry.scid_interpretation_allowed,
        "control_only": registry.control_only,
    }
    decision_time = _parse_iso(fields.get("decision_time_utc"))
    if not proxy:
        return {
            "status": "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
            "symbol": symbol,
            "source_system": "sierra_depth",
            **source_status,
            "paid_fetch_attempted": False,
        }
    if decision_time is None:
        return {
            "status": "MISSING_DECISION_TIME",
            "symbol": symbol,
            "source_system": "sierra_depth",
            **source_status,
            "paid_fetch_attempted": False,
        }
    depth_path = SIERRA_DEPTH_ROOT / f"{proxy['root']}.{decision_time:%Y-%m-%d}.depth"
    if not depth_path.exists():
        return {
            "status": "LOCAL_DEPTH_FILE_MISSING",
            "symbol": symbol,
            "source_system": "sierra_depth",
            "depth_path": str(depth_path),
            "source_symbol": str(proxy["root"]),
            "futures_symbol": str(proxy["futures_symbol"]),
            **source_status,
            "paid_fetch_attempted": False,
        }
    file_size = None
    try:
        file_size = depth_path.stat().st_size
    except OSError:
        pass
    common = {
        "symbol": symbol,
        "source_system": "sierra_depth",
        "depth_path": str(depth_path),
        "source_symbol": str(proxy["root"]),
        "futures_symbol": str(proxy["futures_symbol"]),
        **source_status,
        "feed_delay_expected_seconds": 610,
        "paid_fetch_attempted": False,
        "file_size_bytes": file_size,
        "file_mtime_utc": _file_mtime_utc(depth_path),
    }
    if feature_mode != "full":
        return {
            **common,
            "status": "LOCAL_DEPTH_FILE_PRESENT_FEATURE_EXTRACTION_DEFERRED",
            "feature_extraction_mode": feature_mode,
            "feature_extraction_policy": (
                "Candidate capture records the exact Sierra source file immediately; "
                "full heatmap/depth features are enriched outside the live candidate write path "
                "so a large .depth scan cannot create a shadow-capture gap."
            ),
            "features": {},
        }
    try:
        from scripts.extract_sierra_depth_features import extract_event_features

        event = {
            "event_id": fields.get("candidate_id"),
            "symbol": symbol,
            "event_class": "LIVE_CANDIDATE_SHADOW",
            "decision": fields.get("analysis_decision"),
            "framework": fields.get("framework"),
            "direction": fields.get("side"),
            "canonical_m15_close_utc": decision_time.isoformat(),
            "window_start_utc": (decision_time - timedelta(minutes=60)).isoformat(),
            "window_end_utc": (decision_time + timedelta(minutes=15)).isoformat(),
        }
        payload = extract_event_features(
            depth_path=depth_path,
            event=event,
            source_symbol=str(proxy["root"]),
            futures_symbol=str(proxy["futures_symbol"]),
            tick_size=float(proxy["tick_size"]),
        )
        feature_row = payload.get("feature_row") or {}
        selected = {
            key: feature_row.get(key)
            for key in (
                "data_status",
                "pre60_median_total_depth10",
                "pre60_median_depth10_imbalance",
                "pre60_thin_depth10_threshold",
                "event15_median_total_depth10",
                "event15_median_depth10_imbalance",
                "event15_thin_depth10_rate",
                "event15_median_max_bid_wall",
                "event15_median_max_ask_wall",
                "event15_median_near_far_ratio",
                "event15_mid_change_ticks",
                "event15_sample_count",
            )
        }
        return {
            **common,
            "status": "FEATURES_EXTRACTED" if selected.get("data_status") == "ok" else "FEATURES_ATTEMPTED_NO_SAMPLES",
            "feature_extraction_mode": "full",
            "features": selected,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            **common,
            "status": "FEATURE_EXTRACTION_FAILED",
            "feature_extraction_mode": "full",
            "error": str(exc),
        }


def _databento_trigger_policy(fields: dict[str, Any], *, live_enabled: bool, key_present: bool) -> dict[str, Any]:
    symbol = str(fields.get("symbol") or "")
    base = {
        "policy_version": "databento_live_trigger_policy_v1",
        "symbol": symbol,
        "candidate_id": fields.get("candidate_id"),
        "decision_time_utc": fields.get("decision_time_utc"),
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
        "api_key_present": key_present,
        "live_shadow_enabled": live_enabled,
    }
    if symbol in SOURCE_BLOCKED_DATABENTO_SYMBOLS:
        return {
            **base,
            "trigger_status": "SOURCE_BLOCKED",
            "reason": SOURCE_BLOCKED_DATABENTO_SYMBOLS[symbol],
            "raw_symbols": [],
        }
    trigger = DATABENTO_TRIGGER_SYMBOLS.get(symbol)
    if not trigger:
        return {
            **base,
            "trigger_status": "NO_TRIGGER_FOR_SYMBOL_OR_STRATEGY",
            "reason": "No registered live Databento trigger applies to this candidate.",
            "raw_symbols": [],
        }
    if not live_enabled:
        status = "TRIGGER_ELIGIBLE_BUT_DISABLED_BY_ENV"
    elif not key_present:
        status = "TRIGGER_ELIGIBLE_BUT_API_KEY_MISSING"
    else:
        status = "TRIGGER_ELIGIBLE_COLLECTOR_REQUIRED"
    return {
        **base,
        "trigger_status": status,
        **trigger,
    }


def _databento_confluence(fields: dict[str, Any]) -> dict[str, Any]:
    symbol = str(fields.get("symbol") or "")
    manifest = Path(DATABENTO_FORWARD_REQUEST_MANIFEST)
    rows = []
    if manifest.exists():
        try:
            for line in manifest.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if symbol == "NAS100" or row.get("source_event_id") == fields.get("candidate_id"):
                    rows.append(
                        {
                            "request_id": row.get("request_id"),
                            "schema": row.get("schema"),
                            "raw_symbol": row.get("raw_symbol"),
                            "status": row.get("status"),
                            "cache_path": row.get("cache_path"),
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "REQUEST_MANIFEST_READ_FAILED",
                "source_system": "databento",
                "request_manifest": str(manifest),
                "error": str(exc),
                "paid_fetch_attempted": False,
            }
    cached_rows = [row for row in rows if row.get("cache_path") and Path(str(row["cache_path"])).exists()]
    live_path = Path(DATABENTO_LIVE_SHADOW_PATH)
    live_rows = []
    if live_path.exists():
        try:
            for line in live_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-500:]:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("symbol") == symbol or row.get("gtos_symbol") == symbol:
                    live_rows.append(
                        {
                            "created_at_utc": row.get("created_at_utc"),
                            "schema": row.get("schema"),
                            "raw_symbol": row.get("raw_symbol"),
                            "status": row.get("status"),
                            "features": row.get("features"),
                        }
                    )
        except Exception:
            live_rows = []
    try:
        import databento as db  # noqa: F401

        package_status = "INSTALLED"
    except Exception:
        package_status = "NOT_INSTALLED"
    import os

    live_enabled = os.environ.get("GTOS_DATABENTO_LIVE_SHADOW_ENABLED") == "1"
    key_present = bool(os.environ.get("DATABENTO_API_KEY"))
    trigger_policy = _databento_trigger_policy(
        fields,
        live_enabled=live_enabled,
        key_present=key_present,
    )
    return {
        "status": (
            "LIVE_SHADOW_ROWS_PRESENT"
            if live_rows
            else "CACHE_PRESENT"
            if cached_rows
            else "NOT_FETCHED_OR_NO_CACHE_FOR_LIVE_CANDIDATE"
        ),
        "source_system": "databento",
        "request_manifest": str(manifest),
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
        "cost_policy": "NO_PAID_FETCH_FROM_LIVE_SHADOW_LOGGER",
        "trigger_policy": trigger_policy,
        "matching_declared_requests": rows,
        "cached_request_count": len(cached_rows),
        "live_shadow": {
            "status": "ENABLED" if live_enabled else "DISABLED_BY_ENV",
            "package_status": package_status,
            "api_key_present": key_present,
            "log_path": DATABENTO_LIVE_SHADOW_PATH,
            "matching_recent_rows": live_rows[-5:],
            "note": "Set GTOS_DATABENTO_LIVE_SHADOW_ENABLED=1 and run the live collector to populate this lane.",
        },
    }


def _external_confluence(fields: dict[str, Any], *, sierra_feature_mode: str = "deferred") -> dict[str, Any]:
    return {
        "sierra": _sierra_depth_confluence(fields, feature_mode=sierra_feature_mode),
        "databento": _databento_confluence(fields),
    }


def external_confluence_snapshot(fields: dict[str, Any], *, sierra_feature_mode: str = "deferred") -> dict[str, Any]:
    """Return local/cache-only external confluence for a live candidate row."""
    return _external_confluence(fields, sierra_feature_mode=sierra_feature_mode)


def build_strategy_follow_candidate_row(**fields: Any) -> dict[str, Any]:
    final_outcome = fields.get("final_outcome")
    is_limit_placed = final_outcome == "LIMIT_PLACED"
    pending_order_mode = fields.get("pending_order_mode")
    if pending_order_mode is None and is_limit_placed:
        pending_order_mode = INTERNAL_PENDING_ORDER_MODE
    broker_pending_order_created = fields.get("broker_pending_order_created")
    if broker_pending_order_created is None and is_limit_placed:
        broker_pending_order_created = False
    structural_fields = fields.get("decision_time_structural_fields") or {}
    row = common_metadata(
        **{
            **fields,
            "schema_version": "strategy_follow_candidate_v1",
            "evidence_class": fields.get("evidence_class") or "FORWARD_SHADOW",
        }
    )
    row.update(
        {
            "analysis_decision": fields.get("analysis_decision"),
            "framework": fields.get("framework"),
            "final_outcome_at_log": final_outcome,
            "pending_order_mode": pending_order_mode,
            "broker_pending_order_created": broker_pending_order_created,
            "mt5_order_ticket": fields.get("mt5_order_ticket"),
            "native_pending_order_type": fields.get("native_pending_order_type"),
            "detector_version_at_eval": fields.get("detector_version_at_eval"),
            "trade_parameters": fields.get("trade_parameters") or {},
            "h1_setup": fields.get("h1_setup") or {},
            "m15_confirmation": fields.get("m15_confirmation") or {},
            "frameworks_evaluated": fields.get("frameworks_evaluated") or {},
            "mso_summary": fields.get("mso_summary") or {},
            "decision_time_structural_fields": structural_fields,
            "structural_selector_metadata": fields.get("structural_selector_metadata")
            or _structural_selector_metadata_from_fields(structural_fields)
            or {
                "capture_status": "DECISION_TIME_AVAILABLE_FIELDS_PRESERVED",
                "h1_setup_present": bool(fields.get("h1_setup")),
                "m15_confirmation_present": bool(fields.get("m15_confirmation")),
                "frameworks_evaluated_present": bool(fields.get("frameworks_evaluated")),
                "mso_summary_present": bool(fields.get("mso_summary")),
                "standalone_fvg_geometry_present": False,
                "structural_lock_event_present": False,
                "reentry_state_present": False,
                "cost_aware_min_r_present": False,
                "note": (
                    "Future capture preserves the available decision-time MSO/AI "
                    "selector fields. Exact standalone FVG/lock/reentry fields "
                    "remain explicit source requirements unless present in MSO."
                ),
            },
            "verification": fields.get("verification") or {},
            "m15_choch_diagnostic": fields.get("m15_choch_diagnostic")
            or m15_choch_decision_diagnostic(fields.get("verification") or {}),
            "external_confluence": fields.get("external_confluence") or {},
            "strategy_snapshots": fields.get("strategy_snapshots")
            or _strategy_snapshots(fields),
        }
    )
    return enrich_cp281_event_contract_fields(row, source_path=STRATEGY_FOLLOW_PATH)


def record_strategy_follow_candidate(
    row: dict[str, Any],
    log_path: str | Path = STRATEGY_FOLLOW_PATH,
) -> None:
    append_jsonl(log_path, build_strategy_follow_candidate_row(**row))


def record_live_candidate_forward_shadow(
    *,
    symbol: str,
    broker_symbol: str | None = None,
    source_symbol: str | None = None,
    kill_zone: str | None = None,
    analysis: Any,
    mso: Any = None,
    record: dict[str, Any] | None = None,
    verification: Any = None,
    final_outcome: str | None = None,
    trade_id: str | None = None,
    log_root: str | Path | None = None,
    sierra_feature_mode: str = "deferred",
) -> None:
    """Emit live-time follow-data rows for one AI CANDIDATE.

    This is intentionally decision-time only. It does not compute synthetic R,
    does not inspect future bars, and does not change live trading decisions.
    """
    fields = _extract_candidate_fields(
        symbol=symbol,
        broker_symbol=broker_symbol,
        source_symbol=source_symbol,
        kill_zone=kill_zone,
        analysis=analysis,
        mso=mso,
        record=record,
        verification=verification,
        final_outcome=final_outcome,
        trade_id=trade_id,
    )
    fields["candidate_id"] = _candidate_id_from_fields(fields)
    fields["external_confluence"] = _external_confluence(fields, sierra_feature_mode=sierra_feature_mode)
    fvg_ob_geometry = _fvg_ob_geometry_from_decision_mso(fields)

    tp = fields.get("trade_parameters") or {}
    h1_setup = fields.get("h1_setup") or {}
    m15 = fields.get("m15_confirmation") or {}
    base = {
        key: fields.get(key)
        for key in (
            "symbol",
            "broker_symbol",
            "source_symbol",
            "session",
            "kill_zone",
            "side",
            "regime",
            "candidate_id",
            "trade_id",
            "decision_time_utc",
            "source_file",
            "source_hash",
            "no_leak_status",
        )
    }

    def _log_path(path: str | Path) -> Path:
        target = Path(path)
        if log_root is None or target.is_absolute():
            return target
        return Path(log_root) / target

    record_strategy_follow_candidate({**base, **fields}, log_path=_log_path(STRATEGY_FOLLOW_PATH))
    record_v2b_forward_pair(
        {
            **base,
            "ob_boundary_outcome": {"label_status": "unresolved_live_forward"},
            "j46_baseline_outcome": {"label_status": "unresolved_live_forward"},
            "fixed_r_comparator": {"label_status": "unresolved_live_forward"},
            "fvg_comparator": {"label_status": "unresolved_live_forward"},
            "lower_timeframe_available": None,
            "same_bar_ambiguity_state": "unresolved",
            "cost_sensitivity": {"status": "not_joined_at_decision_time"},
            "source_period": "forward_live",
            "path_label_status": "UNRESOLVED_REQUIRES_FORWARD_JOIN",
            "actual_synthetic_label_lane": "no_outcome_at_decision_time",
        },
        log_path=_log_path(V2B_FORWARD_PAIR_PATH),
    )
    record_prefill_delivery_path(
        {
            **base,
            "structural_setup_id": fields["candidate_id"],
            "original_poi_bounds": {
                "poi_type": h1_setup.get("poi_type"),
                "poi_price_level": h1_setup.get("poi_price_level"),
                "zone": h1_setup.get("zone"),
            },
            "entry_arming_time_utc": fields.get("decision_time_utc"),
            "pre_fill_candles": [],
            "pre_fill_ticks_summary": None,
            "delivery_leg_direction": "unresolved_live_forward",
            "reversal_leg_timing": None,
            "fill_happened": None,
            "fill_delay_seconds": None,
            "cancel_expiry_abort_reason": fields.get("final_outcome"),
            "lower_timeframe_path_ordering": "unresolved",
            "fvg_ob_swing_state_at_arm": {
                "framework": fields.get("framework"),
                "h1_poi_type": h1_setup.get("poi_type"),
                "m15_displacement_quality": m15.get("displacement_quality"),
            },
        },
        log_path=_log_path(PREFILL_DELIVERY_PATH),
    )
    record_fvg_ob_confluence(
        {
            **base,
            "bucket": _confluence_bucket(fields),
            **fvg_ob_geometry,
            "touch_count": None,
            "poi_quality": h1_setup.get("zone"),
            "lower_timeframe_available": None,
            "candidate_outcome_lane": "UNRESOLVED_REQUIRES_FORWARD_JOIN",
            "decision_time_fields": {
                "analysis_decision": fields.get("analysis_decision"),
                "framework": fields.get("framework"),
                "entry_price": tp.get("entry_price"),
                "stop_loss": tp.get("stop_loss"),
                "take_profit_1": tp.get("take_profit_1"),
                "h1_poi_type": h1_setup.get("poi_type"),
                "h1_poi_price_level": h1_setup.get("poi_price_level"),
                "m15_displacement_quality": m15.get("displacement_quality"),
                "verification_passed": (fields.get("verification") or {}).get("passed"),
                "verification_blocked_by": (fields.get("verification") or {}).get("blocked_by"),
                "final_outcome_at_log": fields.get("final_outcome"),
                "sierra_confluence_status": (
                    (fields.get("external_confluence") or {}).get("sierra") or {}
                ).get("status"),
                "databento_confluence_status": (
                    (fields.get("external_confluence") or {}).get("databento") or {}
                ).get("status"),
            },
        },
        log_path=_log_path(FVG_OB_CONFLUENCE_PATH),
    )
    record_context_control(
        {
            **base,
            "context_question_id": "LIVE_CANDIDATE_CONTEXT_CONTROLS_V1",
            "context_family": "CL_ZN_VIX_CONTROL_CONTEXT",
            "asof_timestamp_convention": "latest_observation_at_or_before_decision_time",
            "join_rule": "not_joined_in_live_candidate_hook",
            "context_values": {
                "status": "CONTROL_CONTEXT_NOT_JOINED_AT_DECISION_TIME",
                "symbol": fields.get("symbol"),
                "final_outcome_at_log": fields.get("final_outcome"),
                "sierra_confluence": (fields.get("external_confluence") or {}).get("sierra"),
                "databento_confluence": (fields.get("external_confluence") or {}).get("databento"),
            },
            "control_only": True,
            "control_role": "CONTROL_ONLY",
            "direct_strategy_validation_status": "NOT_DIRECT_STRATEGY_VALIDATION",
            "strategy_validation_status": "CONTROL_CONTEXT_ONLY_NOT_STRATEGY_VALIDATION",
            "validation_scope": "EXPLORATORY_CONTEXT_ONLY",
        },
        log_path=_log_path(CONTEXT_CONTROL_PATH),
    )
    decision_spread = _safe_get(mso, "spread_cents")
    record_nofill_forward_source_capture(
        {
            **base,
            **fields,
            "capture_observed_at_utc": fields.get("decision_time_utc"),
            "capture_timestamp_derivation_rule": "live_candidate_decision_time_utc_plus_writer_clock",
            "decision_spread_value_source_safe": decision_spread,
            "decision_spread_unit": "spread_cents" if decision_spread is not None else None,
            "pending_horizon_start_utc": fields.get("decision_time_utc")
            if fields.get("final_outcome") == "LIMIT_PLACED"
            else None,
            "event_order_resolution_method": "DECISION_TIME_ONLY_FORWARD_PATH_UNRESOLVED",
            "same_tick_same_bar_ambiguity_status": "UNRESOLVED_REQUIRES_FORWARD_PATH_JOIN",
            "missing_coverage_intervals": [],
        },
        log_path=_log_path(NOFILL_FORWARD_SOURCE_CAPTURE_PATH),
    )
    record_scid_forward_capture_candidate_groups(
        {**base, **fields},
        fvg_ob_geometry=fvg_ob_geometry,
        log_path=_log_path(SCID_FORWARD_SOURCE_CAPTURE_PATH),
    )


def classify_ltf_ambiguity(
    *,
    lower_tf_available: bool,
    fill_happened: bool | None = None,
    tp_hit: bool | None = None,
    sl_hit: bool | None = None,
    tp_time_utc: str | None = None,
    sl_time_utc: str | None = None,
    fill_before_invalidation: bool | None = None,
    invalidation_before_fill: bool | None = None,
    unresolved: bool = False,
) -> str:
    """Classify lower-timeframe path/fill ambiguity without guessing."""
    if not lower_tf_available:
        return "no_ltf_data"
    if unresolved:
        return "unresolved"
    if fill_happened is False:
        return "no_fill"
    if fill_before_invalidation is True:
        return "fill_before_invalidation"
    if invalidation_before_fill is True:
        return "invalidation_before_fill"
    if tp_hit and sl_hit and tp_time_utc and sl_time_utc:
        if tp_time_utc == sl_time_utc:
            return "same_bar_tp_sl_ambiguity"
        return "tp_before_sl" if tp_time_utc < sl_time_utc else "sl_before_tp"
    if tp_hit and sl_hit:
        return "same_bar_tp_sl_ambiguity"
    return "unresolved"
