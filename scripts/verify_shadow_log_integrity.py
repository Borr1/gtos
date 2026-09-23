"""Verify shadow log integrity and value sanity.

This is a read-only monitoring/research verifier. It does not import or call
live trading components and does not make network, AI, or broker order
requests.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.mso_snapshot_join import (
    JOIN_MISSING,
    JOIN_SCHEMA_VERSION,
    JOINED_EXACT,
    build_candidate_mso_join_rows,
)
from src.research_infra.candidate_registry_audit import (
    ACTION_REQUIRED as CANDIDATE_REGISTRY_ACTION_REQUIRED,
    SCHEMA_VERSION as CANDIDATE_REGISTRY_AUDIT_SCHEMA_VERSION,
    build_candidate_registry_audit_rows,
)
from src.research_infra.candidate_path_contract import (
    ACTION_REQUIRED as PATH_CONTRACT_ACTION_REQUIRED,
    SCHEMA_VERSION as PATH_CONTRACT_AUDIT_SCHEMA_VERSION,
    build_candidate_path_contract_rows,
)
from src.research_infra.opportunity_lifecycle_audit import (
    ACTION_REQUIRED as OPPORTUNITY_LIFECYCLE_ACTION_REQUIRED,
    SCHEMA_VERSION as OPPORTUNITY_LIFECYCLE_AUDIT_SCHEMA_VERSION,
    build_opportunity_lifecycle_audit_rows,
)
from src.research_infra.pending_limit_lifecycle_audit import (
    ACTION_REQUIRED as PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED,
    SCHEMA_VERSION as PENDING_LIMIT_LIFECYCLE_AUDIT_SCHEMA_VERSION,
    build_pending_limit_lifecycle_audit_rows,
    read_persisted_pending_intents,
)
from src.research_infra.v2b_forward_pair_resolution_audit import (
    ACTION_REQUIRED as V2B_FORWARD_PAIR_ACTION_REQUIRED,
    SCHEMA_VERSION as V2B_FORWARD_PAIR_AUDIT_SCHEMA_VERSION,
    build_v2b_forward_pair_audit_rows,
)
from src.research_infra.prefill_delivery_path_audit import (
    ACTION_REQUIRED as PREFILL_DELIVERY_PATH_ACTION_REQUIRED,
    SCHEMA_VERSION as PREFILL_DELIVERY_PATH_AUDIT_SCHEMA_VERSION,
    build_prefill_delivery_path_audit_rows,
)
from src.research_infra.fvg_ob_confluence_audit import (
    ACTION_REQUIRED as FVG_OB_CONFLUENCE_ACTION_REQUIRED,
    EXACT_SOURCE_CAPTURE_STATUSES as FVG_OB_EXACT_SOURCE_CAPTURE_STATUSES,
    SCHEMA_VERSION as FVG_OB_CONFLUENCE_AUDIT_SCHEMA_VERSION,
    build_fvg_ob_confluence_audit_rows,
)
from src.research_infra.context_control_audit import (
    ACTION_REQUIRED as CONTEXT_CONTROL_ACTION_REQUIRED,
    SCHEMA_VERSION as CONTEXT_CONTROL_AUDIT_SCHEMA_VERSION,
    build_context_control_audit_rows,
    direct_validation_problems as context_direct_validation_problems,
)
from src.research_infra.broker_actual_r_audit import (
    ACTION_REQUIRED as BROKER_ACTUAL_R_ACTION_REQUIRED,
    SCHEMA_VERSION as BROKER_ACTUAL_R_AUDIT_SCHEMA_VERSION,
    build_broker_actual_r_audit_rows,
)
from src.research_infra.j46_j49_exit_comparator_audit import (
    ACTION_REQUIRED as J46_J49_EXIT_COMPARATOR_ACTION_REQUIRED,
    SCHEMA_VERSION as J46_J49_EXIT_COMPARATOR_SCHEMA_VERSION,
    build_j46_j49_exit_comparator_audit_rows,
)
from src.research_infra.s79_side_aware_risk_context import (
    ACTION_REQUIRED as S79_SIDE_AWARE_ACTION_REQUIRED,
    SCHEMA_VERSION as S79_SIDE_AWARE_SCHEMA_VERSION,
    build_s79_side_aware_context_rows,
)
from src.research_infra.regime_decay_outcome_join import (
    ACTION_REQUIRED as REGIME_DECAY_ACTION_REQUIRED,
    SCHEMA_VERSION as REGIME_DECAY_SCHEMA_VERSION,
    build_regime_decay_outcome_rows,
)
from src.research_infra.decision_layer_diagnostics_join import (
    ACTION_REQUIRED as DECISION_DIAGNOSTICS_ACTION_REQUIRED,
    SCHEMA_VERSION as DECISION_DIAGNOSTICS_SCHEMA_VERSION,
    build_decision_layer_diagnostics_rows,
)
from src.research_infra.mechanical_context_diagnostics_join import (
    ACTION_REQUIRED as MECHANICAL_CONTEXT_ACTION_REQUIRED,
    SCHEMA_VERSION as MECHANICAL_CONTEXT_SCHEMA_VERSION,
    build_mechanical_context_rows,
)
from src.research_infra.k55_ml_shadow import (
    ACTION_REQUIRED as ML_SHADOW_ACTION_REQUIRED,
    DEFAULT_MODEL_REGISTRY_PATH as ML_SHADOW_DEFAULT_MODEL_REGISTRY_PATH,
    SCHEMA_VERSION as ML_SHADOW_SCHEMA_VERSION,
    build_ml_shadow_rows,
)
from src.research_infra.v2_structural_selector_readiness import (
    ACTION_REQUIRED as V2_STRUCTURAL_SELECTOR_ACTION_REQUIRED,
    SCHEMA_VERSION as V2_STRUCTURAL_SELECTOR_READINESS_SCHEMA_VERSION,
    build_status_row as build_v2_structural_selector_status_row,
)
from src.research_infra.xauusd_same_market_extension import (
    ACTION_REQUIRED as XAUUSD_SAME_MARKET_ACTION_REQUIRED,
    DEFAULT_REGISTRY_PATH as XAUUSD_SAME_MARKET_REGISTRY_PATH,
    DEFAULT_SIERRA_INVENTORY_PATH as XAUUSD_SAME_MARKET_SIERRA_INVENTORY_PATH,
    DEFAULT_SOURCE_MAP_PATH as XAUUSD_SAME_MARKET_SOURCE_MAP_PATH,
    SCHEMA_VERSION as XAUUSD_SAME_MARKET_SCHEMA_VERSION,
    build_status_row as build_xauusd_same_market_status_row,
)
from src.research_infra.es_mes_preregistration import (
    ACTION_REQUIRED as ES_MES_PREREG_ACTION_REQUIRED,
    DEFAULT_CONVERSION_STATUS_PATH as ES_MES_CONVERSION_STATUS_PATH,
    DEFAULT_LABEL_STATUS_PATH as ES_MES_LABEL_STATUS_PATH,
    DEFAULT_PRIOR_PREREG_PATH as ES_MES_PRIOR_PREREG_PATH,
    DEFAULT_REGISTRY_PATH as ES_MES_REGISTRY_PATH,
    DEFAULT_SIERRA_INVENTORY_PATH as ES_MES_SIERRA_INVENTORY_PATH,
    SCHEMA_VERSION as ES_MES_PREREG_SCHEMA_VERSION,
    build_status_row as build_es_mes_prereg_status_row,
)
from src.research_infra.shadow_observer_hardening import (
    ACTION_REQUIRED as SHADOW_OBSERVER_HARDENING_ACTION_REQUIRED,
    DEFAULT_AGENT_CONFIG_PATH as SHADOW_OBSERVER_AGENT_CONFIG_PATH,
    DEFAULT_OBSERVER_REGISTRY_PATH as SHADOW_OBSERVER_REGISTRY_PATH,
    DEFAULT_STATE_PATH as SHADOW_OBSERVER_STATE_PATH,
    DEFAULT_STATUS_LOG_PATH as SHADOW_OBSERVER_STATUS_PATH,
    DEFAULT_STRATEGY_EVALUATIONS_PATH as SHADOW_OBSERVER_STRATEGY_EVALUATIONS_PATH,
    SCHEMA_VERSION as SHADOW_OBSERVER_HARDENING_SCHEMA_VERSION,
    build_status_row as build_shadow_observer_hardening_status_row,
)
from src.research_infra.account_pnl_truth_reconciler import (
    ACTION_REQUIRED as ACCOUNT_PNL_TRUTH_ACTION_REQUIRED,
    SCHEMA_VERSION as ACCOUNT_PNL_TRUTH_SCHEMA_VERSION,
    build_account_pnl_truth_rows,
)
from src.research_infra.trade_index_lifecycle_audit import (
    ACTION_REQUIRED as TRADE_INDEX_LIFECYCLE_ACTION_REQUIRED,
    INDEX_SCHEMA_VERSION as TRADE_RECORD_INVENTORY_INDEX_SCHEMA_VERSION,
    SCHEMA_VERSION as TRADE_INDEX_LIFECYCLE_SCHEMA_VERSION,
    build_inventory_index,
    build_trade_index_lifecycle_rows,
    read_trade_records,
)
from src.research_infra.exit_management_no_event_audit import (
    ACTION_REQUIRED as EXIT_MANAGEMENT_ACTION_REQUIRED,
    SCHEMA_VERSION as EXIT_MANAGEMENT_STATUS_SCHEMA_VERSION,
    build_exit_management_status_rows,
)
from src.research_infra.session_volatility_sweep_status import (
    ACTION_REQUIRED as SESSION_VOL_SWEEP_ACTION_REQUIRED,
    SCHEMA_VERSION as SESSION_VOL_SWEEP_STATUS_SCHEMA_VERSION,
    build_status_rows as build_session_vol_sweep_status_rows,
    target_previous_utc_date,
)
from src.research_infra.notification_queue_dead_zone_status import (
    ACTION_REQUIRED as NOTIFICATION_QUEUE_ACTION_REQUIRED,
    DEFAULT_LOCK_PATH as NOTIFICATION_QUEUE_LOCK_PATH,
    DEFAULT_QUEUE_PATH as NOTIFICATION_QUEUE_PATH,
    SCHEMA_VERSION as NOTIFICATION_QUEUE_DEAD_ZONE_SCHEMA_VERSION,
    build_status_row as build_notification_queue_status_row,
    status_fields_for_contract as notification_queue_status_fields_for_contract,
)
from src.research_infra.storage_retention_policy import (
    ACTION_REQUIRED as STORAGE_RETENTION_ACTION_REQUIRED,
    SCHEMA_VERSION as STORAGE_RETENTION_SCHEMA_VERSION,
)
from src.research_infra.trade_record_candidate_backfill import (
    DEFAULT_TRADE_RECORD_ROOT,
    iter_trade_record_candidates,
)
from src.components.ai_decision_trace_logger import SCHEMA_VERSION as AI_DECISION_TRACE_SCHEMA_VERSION


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

ALLOWED_PROMOTION_VERDICTS = {
    PROMOTION_VERDICT,
    "LIVE_PRODUCTION_PATH",
    "RESEARCH_ONLY",
    "SHIPPED_POLICY_CONTEXT",
    "IMPLEMENTED_SHADOW_ONLY",
}

ALLOWED_EVIDENCE_CLASSES = {
    "BROKER_ACTUAL_R",
    "ACCOUNT_HISTORY_REALIZED",
    "INTERNAL_LIMIT_LIFECYCLE",
    "SYNTHETIC_PATH_R",
    "FUTURES_PROXY_TRANSFER",
    "SAME_MARKET_SOURCE_TRANSFER",
    "SAME_MARKET_SOURCE_TRANSFER_REGISTRATION",
    "CROSS_INSTRUMENT_CONTEXT",
    "FORWARD_SHADOW",
    "FORWARD_SHADOW_PATH_CONTEXT",
    "FORWARD_SHADOW_PATH_FOLLOW",
    "J46_J49_FILLED_ACCOUNT_HISTORY_MISSING",
    "RECOVERY_AUDIT",
    "DISCOVERY_ONLY",
    "CONTROL_ONLY",
    "EXIT_MANAGEMENT_NO_EVENT_STATUS",
    "MONITOR_CADENCE_STATUS",
    "SHIPPED_POLICY_CONTEXT",
    "DECISION_TIME_REGIME_DECAY_CONTEXT",
    "DECISION_LAYER_DIAGNOSTICS_CONTEXT",
    "MECHANICAL_CONTEXT_DIAGNOSTICS",
    "ML_SHADOW_FEATURE_BUNDLE_STATUS",
}

POST_OUTCOME_KEYS = {
    "actual_r",
    "broker_actual_r",
    "pnl",
    "profit",
    "outcome_r",
    "realized_r",
    "winner",
    "loser",
}


@dataclass(frozen=True)
class JsonlSpec:
    expected_schema: str | None = None
    required_fields: tuple[str, ...] = ()
    nullable_required_fields: tuple[str, ...] = ()
    unique_key: tuple[str, ...] = ()
    freshness_minutes: int | None = None
    event_driven: bool = True
    freshness_mode: str = "wall_clock"


JSONL_SPECS: dict[str, JsonlSpec] = {
    "strategy_follow_evaluations.jsonl": JsonlSpec(
        expected_schema="strategy_follow_evaluation_v1",
        required_fields=(
            "schema_version",
            "created_at_utc",
            "symbol",
            "broker_symbol",
            "candidate_id",
            "decision_time_utc",
            "evidence_class",
            "no_leak_status",
            "promotion_verdict",
            "evaluation_stage",
            "ai_dependency",
            "ai_status",
            "strategy_snapshots",
        ),
        freshness_minutes=30,
        event_driven=False,
        freshness_mode="kill_zone_gated",
    ),
    "strategy_follow_candidates.jsonl": JsonlSpec(
        expected_schema="strategy_follow_candidate_v1",
        required_fields=(
            "schema_version",
            "created_at_utc",
            "symbol",
            "broker_symbol",
            "candidate_id",
            "decision_time_utc",
            "side",
            "framework",
            "analysis_decision",
            "final_outcome_at_log",
            "trade_parameters",
            "external_confluence",
            "strategy_snapshots",
            "no_leak_status",
            "promotion_verdict",
        ),
        unique_key=("candidate_id",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "ai_narrowing_policy_shadow_evaluations.jsonl": JsonlSpec(
        expected_schema="ai_narrowing_policy_shadow_evaluation_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "created_at_utc",
            "backfilled_at_utc",
            "candidate_id",
            "candidate_source_path",
            "candidate_source_line_no",
            "candidate_source_sha256",
            "policy_ledger_path",
            "policy_ledger_sha256",
            "event",
            "evaluation",
            "event_adapter_status",
            "missing_required_fields",
            "selector_scope_key",
            "ai_narrowing_registry_eval_status",
            "matched_policy_rows",
            "matched_policy_row_ids",
            "ai_narrowing_review_ready",
            "capacity_blocklist_required_before_ai_narrowing",
            "current_ai_runtime_behavior",
            "ai_call_skip_allowed_now",
            "production_change_opened_now",
            "live_ai_runtime_change_now",
            "live_selector_change_now",
            "paid_api_or_vendor_call",
            "runtime_candidate_use_permitted",
            "candidate_use_allowed_now",
            "replay_r_reference_counted_as_new_main_result",
            "promotion_verdict",
        ),
        nullable_required_fields=("missing_required_fields", "matched_policy_row_ids"),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "ai_decision_trace.jsonl": JsonlSpec(
        expected_schema=AI_DECISION_TRACE_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "timestamp_utc",
            "row_key",
            "symbol",
            "candle_time",
            "kill_zone",
            "model",
            "backend_mode",
            "response_status",
            "parse_attempts",
            "decision",
            "prompt_fingerprint",
            "raw_response_length",
            "result_sha256",
            "usage",
            "research_boundary",
        ),
        nullable_required_fields=("raw_response_sha256", "no_trade_reason", "framework", "trade_direction"),
        unique_key=("row_key",),
        freshness_mode="candidate_driven",
    ),
    "candidate_path_follow.jsonl": JsonlSpec(
        expected_schema="candidate_path_follow_v1",
        required_fields=(
            "schema_version",
            "created_at_utc",
            "symbol",
            "broker_symbol",
            "candidate_id",
            "decision_time_utc",
            "asof_latest_candle_utc",
            "side",
            "trade_parameters",
            "path_label",
            "touched_entry",
            "hit_tp1",
            "hit_sl",
            "no_leak_status",
            "promotion_verdict",
        ),
        unique_key=("candidate_id", "asof_latest_candle_utc"),
        freshness_minutes=90,
        freshness_mode="kill_zone_gated",
    ),
    "candidate_path_contract_audit.jsonl": JsonlSpec(
        expected_schema=PATH_CONTRACT_AUDIT_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "created_at_utc",
            "backfilled_at_utc",
            "candidate_id",
            "symbol",
            "broker_symbol",
            "decision_time_utc",
            "asof_latest_candle_utc",
            "path_label",
            "touched_entry",
            "hit_tp1",
            "hit_sl",
            "first_touch_times",
            "path_ambiguity_status",
            "tick_order_claim_status",
            "source_ohlc_range",
            "ltf_join_status",
            "path_contract_status",
            "documented_limitation_codes",
            "manual_backfill_status",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=("action_required_codes",),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "live_mechanical_strategy_shadow_outcomes.jsonl": JsonlSpec(
        expected_schema="live_mechanical_strategy_shadow_outcome_v1",
        required_fields=(
            "schema_version",
            "created_at_utc",
            "symbol",
            "broker_symbol",
            "candidate_id",
            "decision_time_utc",
            "asof_latest_candle_utc",
            "strategy_id",
            "strategy_status",
            "score_status",
            "outcome_status",
            "path_label",
            "path_metrics",
            "no_leak_status",
            "manual_backfill_status",
            "no_ai_calls",
            "no_canary_required",
            "paid_fetch_attempted",
            "promotion_verdict",
        ),
        unique_key=("candidate_id", "strategy_id", "asof_latest_candle_utc"),
        freshness_minutes=90,
        freshness_mode="kill_zone_gated",
    ),
    "d1_bias_lag.jsonl": JsonlSpec(
        required_fields=(
            "timestamp",
            "symbol",
            "d1_bias",
            "h4_bias",
            "h1_direction",
            "kill_zone",
            "h4_missing",
            "rolling_N_consecutive",
        ),
        unique_key=("timestamp", "symbol"),
    ),
    "d1_bias_lag_recovery.jsonl": JsonlSpec(
        expected_schema="d1_bias_lag_recovery_v1",
        required_fields=(
            "schema_version",
            "created_at_utc",
            "source_path",
            "original_line",
            "raw_fragment",
            "raw_fragment_sha256",
            "json_error",
            "recovery_status",
            "manual_backfill_status",
            "no_leak_status",
            "promotion_verdict",
        ),
        unique_key=("source_path", "original_line", "raw_fragment_sha256"),
    ),
    "shadow_observer_tick_enrichment.jsonl": JsonlSpec(
        expected_schema="shadow_observer_tick_enrichment_v1",
        required_fields=(
            "schema_version",
            "created_at_utc",
            "candidate_id",
            "decision_time_utc",
            "symbol",
            "broker_symbol",
            "status",
            "pre60_tick_summary",
            "event15_tick_summary",
            "no_leak_status",
            "manual_backfill_status",
            "no_ai_calls",
            "no_canary_required",
            "paid_fetch_attempted",
            "promotion_verdict",
        ),
        unique_key=("candidate_id", "decision_time_utc"),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "v2b_forward_pairs.jsonl": JsonlSpec(
        expected_schema="v2b_forward_pair_v1",
        required_fields=(
            "schema_version",
            "created_at_utc",
            "symbol",
            "broker_symbol",
            "candidate_id",
            "decision_time_utc",
            "side",
            "ob_boundary_outcome",
            "j46_baseline_outcome",
            "fixed_r_comparator",
            "fvg_comparator",
            "path_label_status",
            "actual_synthetic_label_lane",
            "no_leak_status",
            "promotion_verdict",
        ),
        unique_key=("candidate_id",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "prefill_delivery_path.jsonl": JsonlSpec(
        expected_schema="prefill_delivery_path_v1",
        required_fields=(
            "schema_version",
            "created_at_utc",
            "symbol",
            "broker_symbol",
            "candidate_id",
            "decision_time_utc",
            "side",
            "structural_setup_id",
            "original_poi_bounds",
            "entry_arming_time_utc",
            "delivery_leg_direction",
            "lower_timeframe_path_ordering",
            "cancel_expiry_abort_reason",
            "no_leak_status",
            "promotion_verdict",
        ),
        nullable_required_fields=("fill_happened",),
        unique_key=("candidate_id",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "fvg_ob_confluence.jsonl": JsonlSpec(
        expected_schema="fvg_ob_confluence_forward_v1",
        required_fields=(
            "schema_version",
            "created_at_utc",
            "symbol",
            "broker_symbol",
            "candidate_id",
            "decision_time_utc",
            "side",
            "bucket",
            "decision_time_fields",
            "candidate_outcome_lane",
            "no_leak_status",
            "promotion_verdict",
        ),
        unique_key=("candidate_id",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "context_control_ledger.jsonl": JsonlSpec(
        expected_schema="context_control_forward_v1",
        required_fields=(
            "schema_version",
            "created_at_utc",
            "symbol",
            "broker_symbol",
            "candidate_id",
            "decision_time_utc",
            "side",
            "context_question_id",
            "context_family",
            "context_values",
            "control_only",
            "no_leak_status",
            "promotion_verdict",
        ),
        unique_key=("candidate_id",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "context_control_audit.jsonl": JsonlSpec(
        expected_schema=CONTEXT_CONTROL_AUDIT_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "candidate_id",
            "symbol",
            "broker_symbol",
            "decision_time_utc",
            "context_question_id",
            "context_family",
            "registered_control_questions",
            "control_role",
            "control_only",
            "source_control_only",
            "evidence_class_at_source",
            "normalized_evidence_class",
            "direct_strategy_validation_status",
            "strategy_validation_status",
            "validation_scope",
            "context_family_source_statuses",
            "context_event_window_snapshot",
            "exploratory_outcome_context",
            "context_control_audit_status",
            "manual_backfill_status",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "action_required_codes",
            "documented_limitation_codes",
            "direct_validation_problem_paths",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "pending_limit_lifecycle.jsonl": JsonlSpec(
        expected_schema="pending_limit_lifecycle_v1",
        required_fields=(
            "schema_version",
            "created_at_utc",
            "timestamp_utc",
            "symbol",
            "broker_symbol",
            "trade_id",
            "side",
            "entry_price",
            "stop_loss",
            "take_profit_1",
            "check_context",
            "intent_after_check",
            "fill_no_fill_label",
            "broker_fill_state",
            "order_send_attempted",
            "order_send_success",
            "no_leak_status",
            "promotion_verdict",
        ),
        unique_key=("symbol", "trade_id", "timestamp_utc", "check_context", "intent_after_check"),
    ),
    "shadow_observer_status.jsonl": JsonlSpec(
        expected_schema="shadow_observer_status_v1",
        required_fields=(
            "schema_version",
            "created_at_utc",
            "symbol",
            "observer_id",
            "activation_state",
            "lifecycle_status",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "promotion_verdict",
        ),
        freshness_minutes=30,
        event_driven=False,
    ),
    "pending_limit_lifecycle_join_backfill.jsonl": JsonlSpec(
        expected_schema="pending_limit_lifecycle_join_backfill_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "created_at_utc",
            "backfilled_at_utc",
            "symbol",
            "trade_id",
            "join_status",
            "source_lifecycle_trade_id",
            "manual_backfill_status",
            "no_leak_status",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="source_driven",
    ),
    "pending_limit_lifecycle_audit.jsonl": JsonlSpec(
        expected_schema=PENDING_LIMIT_LIFECYCLE_AUDIT_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "created_at_utc",
            "backfilled_at_utc",
            "pending_intent_global_key",
            "raw_trade_id",
            "trade_id_global_uniqueness_status",
            "candidate_match_status",
            "trade_record_match_status",
            "symbol",
            "broker_symbol",
            "side",
            "entry_price",
            "stop_loss",
            "take_profit_1",
            "lifecycle_row_count",
            "final_state",
            "final_state_status",
            "missed_move_classification",
            "required_field_statuses",
            "documented_limitation_codes",
            "pending_limit_lifecycle_audit_status",
            "manual_backfill_status",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "candidate_id",
            "source_symbol",
            "decision_time_utc",
            "trade_record_candidate_id",
            "trade_record_path",
            "latest_lifecycle_timestamp_utc",
            "latest_lifecycle_checked_candle_time_utc",
            "latest_lifecycle_intent_after_check",
            "latest_lifecycle_fill_no_fill_label",
            "latest_lifecycle_broker_fill_state",
            "latest_lifecycle_order_send_attempted",
            "latest_lifecycle_order_send_success",
            "latest_lifecycle_cancel_reason",
            "path_label",
            "ltf_terminal_outcome_status",
            "persisted_pending_intent_path",
            "action_required_codes",
            "raw_trade_id_collision_symbols",
        ),
        freshness_minutes=90,
        freshness_mode="source_driven",
    ),
    "candidate_mso_snapshot_joins.jsonl": JsonlSpec(
        expected_schema=JOIN_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "created_at_utc",
            "backfilled_at_utc",
            "candidate_id",
            "symbol",
            "broker_symbol",
            "decision_time_utc",
            "join_status",
            "join_method",
            "context_comparison_status",
            "manual_backfill_status",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=("evaluation_line_no", "mso_snapshot", "nearest_mso_delta_seconds"),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "candidate_registry_audit.jsonl": JsonlSpec(
        expected_schema=CANDIDATE_REGISTRY_AUDIT_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "created_at_utc",
            "backfilled_at_utc",
            "candidate_id",
            "symbol",
            "broker_symbol",
            "decision_time_utc",
            "source_file",
            "source_hash_status",
            "framework",
            "analysis_decision",
            "l2_final_state",
            "l2_final_state_status",
            "trade_geometry_status",
            "sierra_confluence_status",
            "databento_confluence_status",
            "structural_metadata_status",
            "documented_limitation_codes",
            "registry_audit_status",
            "manual_backfill_status",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=("source_hash", "missing_required_candidate_fields", "action_required_codes"),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "live_structural_strategy_metadata.jsonl": JsonlSpec(
        expected_schema="live_structural_strategy_metadata_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "created_at_utc",
            "backfilled_at_utc",
            "candidate_id",
            "symbol",
            "decision_time_utc",
            "recovered_decision_time_fields",
            "missing_exact_required_fields",
            "affected_strategy_ids",
            "scoreability_status",
            "manual_backfill_status",
            "no_leak_status",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "v2b_forward_pair_resolutions.jsonl": JsonlSpec(
        expected_schema="v2b_forward_pair_resolution_v1",
        required_fields=("schema_version", "row_key", "candidate_id", "symbol", "resolution_status", "path_metrics", "strategy_outcomes", "manual_backfill_status", "promotion_verdict"),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="kill_zone_gated",
    ),
    "v2b_forward_pair_resolution_audit.jsonl": JsonlSpec(
        expected_schema=V2B_FORWARD_PAIR_AUDIT_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "candidate_id",
            "symbol",
            "broker_symbol",
            "decision_time_utc",
            "ob_boundary_outcome",
            "j46_baseline_outcome",
            "fixed_r_comparator",
            "fvg_comparator",
            "actual_synthetic_label_lane",
            "resolved_pair",
            "r_counted_pair",
            "duplicate_aware_counting_status",
            "decision_pair_no_leak_status",
            "v2b_forward_pair_resolution_audit_status",
            "documented_limitation_codes",
            "manual_backfill_status",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "action_required_codes",
            "latest_resolution_row_key",
            "latest_resolution_status",
            "latest_resolution_asof_utc",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "prefill_delivery_path_resolutions.jsonl": JsonlSpec(
        expected_schema="prefill_delivery_path_resolution_v1",
        required_fields=("schema_version", "row_key", "candidate_id", "symbol", "resolution_status", "path_metrics", "strategy_outcomes", "manual_backfill_status", "promotion_verdict"),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="kill_zone_gated",
    ),
    "prefill_delivery_path_audit.jsonl": JsonlSpec(
        expected_schema=PREFILL_DELIVERY_PATH_AUDIT_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "candidate_id",
            "symbol",
            "broker_symbol",
            "decision_time_utc",
            "source_capture_statuses",
            "prefill_source_capture_status",
            "decision_prefill_no_leak_status",
            "fill_state",
            "delivery_leg_state",
            "reversal_leg_state",
            "cancel_expiry_state",
            "post_lock_reentry_eligibility",
            "cost_aware_min_r",
            "prefill_delivery_reversal_outcome",
            "pending_limit_lifecycle_outcome",
            "duplicate_aware_counting_status",
            "derived_prefill_path_status",
            "prefill_delivery_path_audit_status",
            "manual_backfill_status",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "action_required_codes",
            "documented_limitation_codes",
            "latest_resolution_row_key",
            "latest_resolution_status",
            "latest_resolution_asof_utc",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "fvg_ob_confluence_resolutions.jsonl": JsonlSpec(
        expected_schema="fvg_ob_confluence_resolution_v1",
        required_fields=("schema_version", "row_key", "candidate_id", "symbol", "resolution_status", "path_metrics", "strategy_outcomes", "manual_backfill_status", "promotion_verdict"),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="kill_zone_gated",
    ),
    "fvg_ob_confluence_audit.jsonl": JsonlSpec(
        expected_schema=FVG_OB_CONFLUENCE_AUDIT_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "candidate_id",
            "symbol",
            "broker_symbol",
            "decision_time_utc",
            "bucket_state",
            "geometry_state",
            "source_capture_statuses",
            "fvg_ob_source_capture_status",
            "decision_fvg_ob_no_leak_status",
            "fvg_ob_confluence_outcome",
            "fvg_mid_edge_outcome",
            "duplicate_aware_counting_status",
            "fvg_ob_confluence_audit_status",
            "manual_backfill_status",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "action_required_codes",
            "documented_limitation_codes",
            "latest_resolution_row_key",
            "latest_resolution_status",
            "latest_resolution_asof_utc",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "missed_opportunity_shadow.jsonl": JsonlSpec(
        expected_schema="missed_opportunity_shadow_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "candidate_id",
            "symbol",
            "limit_entry_outcome_status",
            "market_at_decision_close_comparator",
            "proximity_entry_comparator",
            "near_miss_classification",
            "manual_backfill_status",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="kill_zone_gated",
    ),
    "candidate_ltf_path_order.jsonl": JsonlSpec(
        expected_schema="candidate_ltf_path_order_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "candidate_id",
            "symbol",
            "ltf_source",
            "ltf_status",
            "path_order_label",
            "manual_backfill_status",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="kill_zone_gated",
    ),
    "databento_live_trigger_decisions.jsonl": JsonlSpec(
        expected_schema="databento_live_trigger_decision_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "candidate_id",
            "symbol",
            "trigger_status",
            "decision",
            "cost_policy",
            "paid_fetch_attempted",
            "paid_data_calls",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "databento_live_confluence.jsonl": JsonlSpec(
        expected_schema="databento_live_confluence_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "created_at_utc",
            "status",
            "dataset",
            "policy_id",
            "policy_decision",
            "cost_policy",
            "feature_class",
            "source_candidate_id",
            "signal_use_case",
            "paid_fetch_attempted",
            "paid_data_calls",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "databento_live_budget_ledger.jsonl": JsonlSpec(
        expected_schema="databento_live_budget_ledger_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "created_at_utc",
            "policy_id",
            "trigger_id",
            "budget_status",
            "budget_day_utc",
            "symbols",
            "schemas",
            "estimated_cost_usd",
            "max_cost_per_trigger_usd",
            "daily_spend_cap_usd",
            "cooldown_seconds",
            "paid_fetch_attempted",
            "paid_data_calls",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "nas100_orderflow_adverse_selection_status.jsonl": JsonlSpec(
        expected_schema="nas100_orderflow_adverse_selection_status_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "status",
            "symbol",
            "broker_symbol",
            "databento_raw_symbol",
            "evidence_class",
            "trigger_criteria",
            "feature_family_forward_plan",
            "databento_live_status",
            "floors",
            "current_counts",
            "readiness_gates",
            "diagnostic_only",
            "no_leak_status",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="source_driven",
    ),
    "sierra_depth_enrichment_status.jsonl": JsonlSpec(
        expected_schema="sierra_depth_enrichment_status_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "status",
            "depth_feature_version",
            "feature_status_counts",
            "source_status_counts",
            "interpretation_status_counts",
            "current_counts",
            "background_queue_policy",
            "boundary",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="source_driven",
    ),
    "sierra_proxy_registry_status.jsonl": JsonlSpec(
        expected_schema="sierra_proxy_registry_status_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_ids",
            "candidate_id",
            "symbol",
            "broker_symbol",
            "decision_time_utc",
            "source_dependency_signature",
            "source_system",
            "proxy_class",
            "source_status",
            "parity_status",
            "interpretation_status",
            "allowed_use",
            "claim_boundary",
            "depth_interpretation_allowed",
            "scid_interpretation_allowed",
            "control_only",
            "registry_status",
            "backfill_policy",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
            "promotion_verdict",
        ),
        nullable_required_fields=("sierra_source_symbol", "sierra_futures_symbol", "sierra_tick_size"),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="source_driven",
    ),
    "gbpjpy_proxy_gap_status.jsonl": JsonlSpec(
        expected_schema="gbpjpy_orderflow_proxy_gap_status_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "status",
            "symbol",
            "broker_symbol",
            "candidate_id",
            "decision_time_utc",
            "registry_proxy_class",
            "registry_source_status",
            "registry_parity_status",
            "current_proxy_status",
            "direct_proxy_registered",
            "direct_confluence_allowed",
            "existing_confluence_inferred",
            "blocker_policy",
            "proxy_design_version",
            "proxy_design_status",
            "registered_proxy_designs",
            "pre_registered_tests",
            "validation_summary",
            "outcome_transfer_caveat_status",
            "no_leak_status",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="source_driven",
    ),
    "sierra_6b_si_depth_policy_status.jsonl": JsonlSpec(
        expected_schema="sierra_6b_si_depth_policy_status_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "status",
            "symbol",
            "broker_symbol",
            "source_symbol",
            "futures_symbol",
            "policy_type",
            "source_status",
            "parity_status",
            "interpretation_status",
            "current_rows_policy",
            "depth_interpretation_allowed_current",
            "depth_interpretation_allowed_after_policy",
            "sample_alignment_policy",
            "validation_summary",
            "requirements_before_interpretation",
            "no_leak_status",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="source_driven",
    ),
    "orderflow_primitives_status.jsonl": JsonlSpec(
        expected_schema="orderflow_primitives_status_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "status",
            "registry_version",
            "primitive_count",
            "primitive_ids",
            "feature_families",
            "roles_evaluated_separately",
            "candidate_trigger_policy",
            "cost_policy",
            "no_lookahead_check",
            "field_coverage",
            "cached_feature_stability",
            "source_readiness",
            "blocker_codes",
            "claim_boundary",
            "no_leak_status",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="source_driven",
    ),
    "sierra_confluence_source_status.jsonl": JsonlSpec(
        expected_schema="sierra_confluence_source_status_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "candidate_id",
            "symbol",
            "source_status",
            "parity_status",
            "interpretation_status",
            "features_present",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "sierra_depth_feature_snapshots.jsonl": JsonlSpec(
        expected_schema="sierra_depth_feature_snapshot_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "candidate_id",
            "symbol",
            "decision_time_utc",
            "source_system",
            "feature_status",
            "features_present",
            "paid_fetch_attempted",
            "paid_data_calls",
            "no_leak_status",
            "promotion_verdict",
        ),
        nullable_required_fields=("depth_path",),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "live_candidate_strategy_rollups.jsonl": JsonlSpec(
        expected_schema="live_candidate_strategy_rollup_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "candidate_id",
            "symbol",
            "candidate_path_status",
            "strategy_count",
            "unresolved_strategy_count",
            "strategy_statuses",
            "promotion_verdict",
        ),
        nullable_required_fields=("latest_follow_asof_utc",),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="kill_zone_gated",
    ),
    "live_candidate_opportunity_clusters.jsonl": JsonlSpec(
        expected_schema="live_candidate_opportunity_cluster_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "candidate_id",
            "symbol",
            "asof_latest_candle_utc",
            "opportunity_id",
            "opportunity_setup_signature",
            "candidate_level_key",
            "opportunity_first_candidate_id",
            "opportunity_duplicate_status",
            "opportunity_reset_reason",
            "opportunity_counting_status",
            "same_symbol_overlap_status",
            "opportunity_similarity",
            "instrument_concurrency_guidance",
            "opportunity_counting_guidance",
            "candidate_terminal_event",
            "same_setup_duplicate_rule",
            "manual_backfill_status",
            "promotion_verdict",
        ),
        nullable_required_fields=("asof_latest_candle_utc", "overlapping_active_symbol_opportunity_ids"),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="kill_zone_gated",
    ),
    "opportunity_lifecycle_audit.jsonl": JsonlSpec(
        expected_schema=OPPORTUNITY_LIFECYCLE_AUDIT_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "created_at_utc",
            "backfilled_at_utc",
            "candidate_id",
            "symbol",
            "broker_symbol",
            "session",
            "decision_time_utc",
            "opportunity_assignment_algorithm_version",
            "opportunity_lifecycle_state",
            "formal_lifecycle_states",
            "opportunity_lifecycle_signature",
            "same_level_tolerance_band",
            "computed_opportunity_id",
            "opportunity_counting_status",
            "opportunity_duplicate_status",
            "opportunity_reset_reason",
            "same_symbol_overlap_status",
            "candidate_terminal_event",
            "reset_policy_status",
            "opportunity_counting_rule_status",
            "cluster_comparison_status",
            "cluster_comparison_mismatches",
            "documented_limitation_codes",
            "manual_backfill_status",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "action_required_codes",
            "asof_latest_candle_utc",
            "documented_opportunity_id",
            "overlapping_active_symbol_opportunity_ids",
            "opportunity_first_candidate_id",
            "opportunity_sequence_index",
            "opportunity_candidate_count",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "account_truth_reconciliation_status.jsonl": JsonlSpec(
        expected_schema="account_truth_reconciliation_status_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "candidate_id",
            "symbol",
            "account_truth_status",
            "truth_lane",
            "actual_r_claim_allowed",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "broker_actual_r_audit.jsonl": JsonlSpec(
        expected_schema=BROKER_ACTUAL_R_AUDIT_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "audit_scope",
            "symbol",
            "broker_symbol",
            "accounting_evidence_class",
            "actual_r_claim_allowed",
            "account_truth_status",
            "truth_lane",
            "entry_slippage_status",
            "exit_accounting_status",
            "commission_status",
            "swap_status",
            "close_reason_status",
            "time_in_trade_status",
            "source_links",
            "broker_actual_r_audit_status",
            "manual_backfill_status",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "candidate_id",
            "fill_id",
            "decision_time_utc",
            "trade_id",
            "ticket",
            "broker_actual_r",
            "action_required_codes",
            "documented_limitation_codes",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "j46_j49_exit_comparator_audit.jsonl": JsonlSpec(
        expected_schema=J46_J49_EXIT_COMPARATOR_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "row_type",
            "j46_j49_exit_comparator_status",
            "symbol",
            "broker_symbol",
            "actual_r_claim_allowed",
            "broker_actual_r_claim_allowed",
            "path_context_status",
            "claim_boundary",
            "ml_feature_role",
            "ml_label_eligibility",
            "ml_no_leak_boundary",
            "evidence_class",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "candidate_id",
            "fill_id",
            "trade_id",
            "side",
            "framework",
            "decision_time_utc",
            "j46_actual_close_realized_r",
            "hypothetical_old_r",
            "delta_r",
            "shadow_better",
            "broker_actual_r",
            "broker_actual_r_delta_vs_j46",
            "broker_actual_r_audit_row_key",
            "broker_actual_r_evidence_class",
            "broker_actual_r_truth_lane",
            "path_label",
            "touched_entry",
            "hit_tp1",
            "hit_sl",
            "path_ambiguity_status",
            "documented_limitation_codes",
            "action_required_codes",
            "source_links",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "s79_side_aware_risk_context.jsonl": JsonlSpec(
        expected_schema=S79_SIDE_AWARE_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "row_type",
            "s79_side_aware_context_status",
            "symbol",
            "broker_symbol",
            "risk_context",
            "account_history_join_status",
            "actual_r_claim_allowed",
            "claim_boundary",
            "ml_feature_role",
            "ml_label_eligibility",
            "ml_no_leak_boundary",
            "evidence_class",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "candidate_id",
            "fill_id",
            "trade_id",
            "side",
            "framework",
            "session",
            "decision_time_utc",
            "candidate_final_outcome_at_log",
            "s79_strategy_snapshot_present",
            "broker_actual_r",
            "broker_actual_r_audit_row_key",
            "broker_actual_r_evidence_class",
            "broker_actual_r_truth_lane",
            "documented_limitation_codes",
            "action_required_codes",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "regime_decay_outcome_join.jsonl": JsonlSpec(
        expected_schema=REGIME_DECAY_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "row_type",
            "regime_decay_context_status",
            "symbol",
            "broker_symbol",
            "path_context_status",
            "account_history_join_status",
            "actual_r_claim_allowed",
            "regime_context",
            "ob_continuation_context",
            "monthly_decay_report_context",
            "claim_boundary",
            "ml_feature_role",
            "ml_label_eligibility",
            "ml_no_leak_boundary",
            "evidence_class",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "candidate_id",
            "fill_id",
            "trade_id",
            "side",
            "framework",
            "session",
            "decision_time_utc",
            "candidate_final_outcome_at_log",
            "path_label",
            "touched_entry",
            "hit_tp1",
            "hit_sl",
            "path_ambiguity_status",
            "broker_actual_r",
            "broker_actual_r_audit_row_key",
            "broker_actual_r_evidence_class",
            "broker_actual_r_truth_lane",
            "documented_limitation_codes",
            "action_required_codes",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "decision_layer_diagnostics_join.jsonl": JsonlSpec(
        expected_schema=DECISION_DIAGNOSTICS_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "row_type",
            "decision_diagnostics_status",
            "symbol",
            "broker_symbol",
            "verification_context",
            "candidate_features_join_status",
            "d1_bias_lag_join_status",
            "direction_emission_join_status",
            "sl_beyond_ob_join_status",
            "touch_count_join_status",
            "diagnostic_join_statuses",
            "candidate_features_context",
            "d1_bias_lag_context",
            "direction_emission_context",
            "sl_beyond_ob_context",
            "touch_count_context",
            "claim_boundary",
            "ml_feature_role",
            "ml_label_eligibility",
            "ml_no_leak_boundary",
            "evidence_class",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "candidate_id",
            "side",
            "framework",
            "session",
            "decision_time_utc",
            "candidate_final_outcome_at_log",
            "ai_decision",
            "ai_direction",
            "trade_parameter_direction",
            "verification_passed",
            "verification_blocked_by",
            "mismatch_codes",
            "documented_limitation_codes",
            "action_required_codes",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "mechanical_context_diagnostics_join.jsonl": JsonlSpec(
        expected_schema=MECHANICAL_CONTEXT_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "row_type",
            "mechanical_context_status",
            "symbol",
            "broker_symbol",
            "path_context",
            "account_history_join_status",
            "actual_r_claim_allowed",
            "mechanical_context_join_statuses",
            "dumb_baseline_context",
            "proximity_context",
            "liquidity_distance_context",
            "displacement_context",
            "structure_divergence_context",
            "claim_boundary",
            "ml_feature_role",
            "ml_label_eligibility",
            "ml_no_leak_boundary",
            "evidence_class",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "candidate_id",
            "side",
            "framework",
            "session",
            "decision_time_utc",
            "candidate_final_outcome_at_log",
            "broker_actual_r",
            "broker_actual_r_audit_row_key",
            "mismatch_codes",
            "documented_limitation_codes",
            "action_required_codes",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "ml_shadow_predictions.jsonl": JsonlSpec(
        expected_schema=ML_SHADOW_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "classifier_version",
            "lto_id",
            "follow_id",
            "row_type",
            "promotion_verdict",
            "evidence_class",
            "ml_shadow_status",
            "target_version",
            "feature_bundle_version",
            "inference_version",
            "candidate_id",
            "symbol",
            "broker_symbol",
            "side",
            "framework",
            "decision_time_utc",
            "analysis_decision",
            "trade_parameters",
            "prediction",
            "feature_bundle_status",
            "feature_availability",
            "feature_groups",
            "feature_vector",
            "label_contract",
            "ml_label_eligibility",
            "no_leak_status",
            "claim_boundary",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "trade_id",
            "asof_latest_candle_utc",
            "documented_limitation_codes",
            "action_required_codes",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "v2_structural_selector_readiness.jsonl": JsonlSpec(
        expected_schema=V2_STRUCTURAL_SELECTOR_READINESS_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_ids",
            "row_type",
            "promotion_verdict",
            "evidence_class",
            "readiness_status",
            "readiness_verdict",
            "sample_floor_target_broker_actual_pairs",
            "gate_summary",
            "readiness_gates",
            "source_counts",
            "evidence_counts",
            "concentration_diagnostics",
            "mt5_account_history_boundary",
            "claim_boundary",
            "ml_contribution",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=("documented_limitation_codes", "action_required_codes"),
        unique_key=("row_key",),
        freshness_minutes=1440,
        freshness_mode="source_driven",
    ),
    "xauusd_same_market_extension_status.jsonl": JsonlSpec(
        expected_schema=XAUUSD_SAME_MARKET_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "status",
            "evidence_class",
            "promotion_verdict",
            "registry_ref",
            "source_map_ref",
            "sierra_inventory_ref",
            "registered_question",
            "registered_families",
            "registered_evidence_classes",
            "opened_outcome_slices_at_registration",
            "outcome_opening_status",
            "source_status",
            "forward_snapshot",
            "validation_gates",
            "gate_summary",
            "claim_boundary",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "documented_limitation_codes",
            "action_required_codes",
            "opened_outcome_slices",
        ),
        unique_key=("row_key",),
        freshness_minutes=1440,
        freshness_mode="source_driven",
    ),
    "es_mes_preregistration_status.jsonl": JsonlSpec(
        expected_schema=ES_MES_PREREG_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "status",
            "evidence_class",
            "promotion_verdict",
            "registry_ref",
            "prior_preregistration_ref",
            "conversion_status_ref",
            "label_status_ref",
            "sierra_inventory_ref",
            "registered_question",
            "registered_question_type",
            "strategy_family",
            "source_mapping",
            "session_windows_utc",
            "evidence_classes",
            "no_lookahead_rules",
            "opened_outcome_slices_at_registration",
            "outcome_opening_status",
            "conversion_rows",
            "label_status",
            "sierra_source_status",
            "validation_gates",
            "gate_summary",
            "claim_boundary",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "documented_limitation_codes",
            "action_required_codes",
            "opened_outcome_slices",
            "opened_outcome_artifacts",
        ),
        unique_key=("row_key",),
        freshness_minutes=1440,
        freshness_mode="source_driven",
    ),
    "shadow_observer_hardening_status.jsonl": JsonlSpec(
        expected_schema=SHADOW_OBSERVER_HARDENING_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_ids",
            "status",
            "evidence_class",
            "promotion_verdict",
            "source_registry_schema_version",
            "source_registry",
            "registry_summary",
            "lifecycle_summary",
            "strategy_observer_counts",
            "stale_observer_detection",
            "final_closeout_detection",
            "restart_policy",
            "validation_gates",
            "gate_summary",
            "claim_boundary",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=("documented_limitation_codes", "action_required_codes"),
        unique_key=("row_key",),
        freshness_minutes=1440,
        freshness_mode="source_driven",
    ),
    "account_pnl_truth_reconciliation.jsonl": JsonlSpec(
        expected_schema=ACCOUNT_PNL_TRUTH_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "source_scope",
            "source_log",
            "dollar_evidence_class",
            "actual_r_claim_allowed",
            "actual_dollar_claim_allowed",
            "account_pnl_truth_status",
            "source_links",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "source_line",
            "trade_id",
            "symbol",
            "source_ts_utc",
            "result_r",
            "realized_usd",
            "risk_dollars",
            "broker_actual_r",
            "broker_profit",
            "mt5_deal_id",
            "mt5_order_id",
            "r_evidence_class",
            "documented_limitation_codes",
            "action_required_codes",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "trade_index_lifecycle_audit.jsonl": JsonlSpec(
        expected_schema=TRADE_INDEX_LIFECYCLE_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "source_log",
            "source_path",
            "record_hash",
            "symbol",
            "lifecycle_state",
            "lifecycle_completeness",
            "has_execution",
            "has_exit",
            "has_embedded_pending_lifecycle",
            "has_pending_lifecycle_audit",
            "broker_position_mismatch_status",
            "trade_index_lifecycle_status",
            "source_links",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "candidate_id",
            "trade_record_trade_id",
            "limit_intent_trade_id",
            "broker_symbol",
            "record_date",
            "decision_time_utc",
            "kill_zone",
            "ai_decision",
            "final_outcome",
            "pending_lifecycle_audit_row_key",
            "pending_lifecycle_final_state",
            "pending_lifecycle_final_state_status",
            "pending_lifecycle_missed_move_classification",
            "pending_lifecycle_trade_id_global_uniqueness_status",
            "raw_trade_id_collision_symbols",
            "entry_price",
            "stop_loss",
            "take_profit_1",
            "actual_r",
            "documented_limitation_codes",
            "action_required_codes",
        ),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "exit_management_shadow_status.jsonl": JsonlSpec(
        expected_schema=EXIT_MANAGEMENT_STATUS_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "candidate_id",
            "exit_management_status",
            "fill_state",
            "pending_lifecycle_fill_status",
            "account_truth_fill_status",
            "broker_actual_r_fill_status",
            "be_shadow_status",
            "partial_close_shadow_status",
            "time_in_trade_shadow_status",
            "actual_event_row_counts",
            "event_log_file_statuses",
            "event_rows_separate_from_status_rows",
            "claim_boundary",
            "evidence_class",
            "no_leak_status",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=(
            "documented_no_event_codes",
            "action_required_codes",
            "trade_id",
            "symbol",
            "broker_symbol",
            "side",
            "framework",
            "session",
            "decision_time_utc",
            "candidate_final_outcome_at_log",
        ),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="candidate_driven",
    ),
    "session_volatility_sweep_status.jsonl": JsonlSpec(
        expected_schema=SESSION_VOL_SWEEP_STATUS_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "lto_id",
            "follow_id",
            "source_name",
            "source_path",
            "source_file_status",
            "source_row_count",
            "target_date",
            "expected_symbol_sessions",
            "covered_symbol_sessions",
            "coverage_status",
            "event_row_count",
            "no_event_row_count",
            "cadence_policy",
            "watchdog_marker",
            "claim_boundary",
            "evidence_class",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=("latest_run_time_utc", "missing_symbol_sessions", "action_required_codes"),
        unique_key=("row_key",),
        freshness_minutes=1440,
        freshness_mode="source_driven",
    ),
    "notification_queue_dead_zone_status.jsonl": JsonlSpec(
        expected_schema=NOTIFICATION_QUEUE_DEAD_ZONE_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "classifier_version",
            "lto_id",
            "target_date",
            "checked_at_utc",
            "notification_queue_status",
            "worker_status",
            "queue_status",
            "dead_zone_active",
            "expected_worker_policy",
            "watchdog_local_time",
            "watchdog_local_day",
            "queue_path",
            "queue_file_status",
            "pending_alert_count",
            "terminal_marker_count",
            "malformed_row_count",
            "lock_path",
            "lock_status",
            "lock_pid_alive",
            "claim_boundary",
            "evidence_class",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=("lock_pid", "latest_enqueue_ts_utc", "action_required_codes"),
        unique_key=("row_key",),
        freshness_minutes=1440,
        freshness_mode="source_driven",
    ),
    "storage_retention_status.jsonl": JsonlSpec(
        expected_schema=STORAGE_RETENTION_SCHEMA_VERSION,
        required_fields=(
            "schema_version",
            "row_key",
            "source_dependency_signature",
            "created_at_utc",
            "backfilled_at_utc",
            "policy_version",
            "lto_id",
            "target_date",
            "checked_at_utc",
            "storage_status",
            "dry_run_only",
            "deletion_performed",
            "disk",
            "inventory",
            "retention_classes",
            "deletion_allowlist_policy",
            "claim_boundary",
            "evidence_class",
            "promotion_verdict",
            "no_ai_calls",
            "no_canary_required",
            "no_execution",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ),
        nullable_required_fields=("action_required_codes",),
        unique_key=("row_key",),
        freshness_minutes=1440,
        freshness_mode="source_driven",
    ),
    "proxy_blocker_status.jsonl": JsonlSpec(
        expected_schema="proxy_blocker_status_v1",
        required_fields=("schema_version", "row_key", "symbol", "blocker_status", "blocker", "required_before_use", "promotion_verdict"),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="kill_zone_gated",
    ),
    "ml_shadow_status.jsonl": JsonlSpec(
        expected_schema="ml_shadow_status_v1",
        required_fields=("schema_version", "row_key", "blocker_status", "model_family", "inference_enabled", "required_before_enable", "promotion_verdict"),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="kill_zone_gated",
    ),
    "external_source_blocker_status.jsonl": JsonlSpec(
        expected_schema="external_source_blocker_status_v1",
        required_fields=("schema_version", "row_key", "source_family", "blocker_status", "blocker", "live_capture_status", "promotion_verdict"),
        unique_key=("row_key",),
        freshness_minutes=90,
        freshness_mode="kill_zone_gated",
    ),
    "lto_blocked_lane_status.jsonl": JsonlSpec(
        expected_schema="lto_blocked_lane_status_v1",
        required_fields=(
            "schema_version",
            "row_key",
            "lto_id",
            "blocked_lane_status",
            "blocker_type",
            "summary",
            "promotion_verdict",
        ),
        unique_key=("row_key",),
        freshness_minutes=1440,
        freshness_mode="source_driven",
    ),
}

AI_NARROWING_FORBIDDEN_TRUE_FIELDS = (
    "ai_call_skip_allowed_now",
    "production_change_opened_now",
    "live_ai_runtime_change_now",
    "live_selector_change_now",
    "paid_api_or_vendor_call",
    "runtime_candidate_use_permitted",
    "candidate_use_allowed_now",
    "replay_r_reference_counted_as_new_main_result",
)

AI_DECISION_TRACE_ALLOWED_STATUSES = {
    "api_timeout",
    "api_server_error",
    "api_rate_limit",
    "unexpected_error",
    "parsed_first_attempt",
    "parsed_retry",
    "malformed_demoted",
}

AI_DECISION_TRACE_FORBIDDEN_TEXT_FIELDS = {
    "system_prompt",
    "user_message",
    "raw_response",
    "prompt_text",
    "response_text",
}

LEGACY_SCHEMA_ALLOWLIST: dict[str, set[str]] = {
    # Append-only audit logs may contain old schema rows after a semantic schema
    # bump. Current dependency signatures must have current rows; historical
    # v1 rows remain valid archive evidence and should not make the whole
    # verifier red.
    "fvg_ob_confluence_audit.jsonl": {"fvg_ob_confluence_audit_v1"},
}

CSV_SPECS = {
    "ob_continuation_daily.csv": {"event_driven": False, "freshness_minutes": 1440},
    "cusum_candidate_rate_daily.csv": {"event_driven": False, "freshness_minutes": 1440},
    "session_volatility_log.csv": {"event_driven": True},
    "sweep_divergence_log.csv": {"event_driven": True},
}

EXPECTED_WAITING_FILES = {
    "databento_live_confluence.jsonl": "owner-approved value-max collector is event/env/API gated; no registered live trigger has invoked the collector yet",
    "databento_live_budget_ledger.jsonl": "owner-approved value-max collector budget ledger; no registered live trigger has invoked the collector yet",
    "ai_decision_trace.jsonl": "hash-only AI decision trace rows are emitted only on post-patch PrimaryAnalyzer calls; no rows are expected while the research runtime halt is active",
    "be_shadow_log.jsonl": "actual BE event rows only; no-event proof lives in exit_management_shadow_status.jsonl",
    "partial_close_shadow_log.jsonl": "actual partial-close trigger rows only; no-event proof lives in exit_management_shadow_status.jsonl",
    "time_in_trade.jsonl": "actual close/time-in-trade rows only; no-event proof lives in exit_management_shadow_status.jsonl",
}


def parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_hhmm(value: Any) -> time | None:
    if not isinstance(value, str):
        return None
    parts = value.strip().split(":")
    if len(parts) != 2:
        return None
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        return time(hour=hour, minute=minute)
    except (TypeError, ValueError):
        return None


def window_contains(now_t: time, start: time, end: time) -> bool:
    if start <= end:
        return start <= now_t < end
    return now_t >= start or now_t < end


def active_symbols_from_start_script(project_root: Path) -> set[str]:
    start_script = project_root / "start_all.bat"
    if not start_script.exists():
        return set()
    text = start_script.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"run_agent\.py\s+--symbol\s+([A-Za-z0-9_]+)", text))


def iter_kill_zone_windows(config: dict[str, Any], active_symbols: set[str] | None = None) -> list[tuple[time, time]]:
    windows: list[tuple[time, time]] = []

    def collect_from_market(market: Any) -> None:
        if not isinstance(market, dict):
            return
        kill_zones = market.get("kill_zones")
        if not isinstance(kill_zones, dict):
            return
        for zone in kill_zones.values():
            if not isinstance(zone, dict):
                continue
            start = parse_hhmm(zone.get("start_utc"))
            end = parse_hhmm(zone.get("end_utc"))
            if start is not None and end is not None:
                windows.append((start, end))

    collect_from_market(config.get("market"))
    instruments = config.get("instruments")
    if isinstance(instruments, dict):
        for symbol, instrument_cfg in instruments.items():
            if active_symbols and str(symbol) not in active_symbols:
                continue
            if isinstance(instrument_cfg, dict):
                collect_from_market(instrument_cfg.get("market"))
    return windows


def any_configured_kill_zone_active(project_root: Path, now_utc: datetime) -> bool | None:
    config_path = project_root / "config" / "agent_config.yaml"
    if not config_path.exists():
        return None
    try:
        import yaml

        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    if not isinstance(config, dict):
        return None
    windows = iter_kill_zone_windows(config, active_symbols_from_start_script(project_root))
    if not windows:
        return None
    now_t = now_utc.astimezone(timezone.utc).time().replace(second=0, microsecond=0)
    return any(window_contains(now_t, start, end) for start, end in windows)


def recursive_nonfinite(value: Any, path: str = "$") -> list[str]:
    out: list[str] = []
    if isinstance(value, float) and not math.isfinite(value):
        out.append(path)
    elif isinstance(value, dict):
        for key, child in value.items():
            out.extend(recursive_nonfinite(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            out.extend(recursive_nonfinite(child, f"{path}[{index}]"))
    return out


def is_missing(value: Any) -> bool:
    return value is None or value == "" or value == []


def add_issue(
    issues: list[dict[str, Any]],
    *,
    path: str,
    severity: str,
    code: str,
    message: str,
    line: int | None = None,
) -> None:
    issues.append(
        {
            "path": path,
            "line": line,
            "severity": severity,
            "code": code,
            "message": message,
        }
    )


def read_jsonl(path: Path, issues: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError as exc:
                add_issue(
                    issues,
                    path=str(path),
                    severity="CRITICAL",
                    code="INVALID_JSON",
                    message=str(exc),
                    line=line_no,
                )
                continue
            if not isinstance(item, dict):
                add_issue(
                    issues,
                    path=str(path),
                    severity="CRITICAL",
                    code="NON_OBJECT_JSONL_ROW",
                    message="JSONL row is not an object",
                    line=line_no,
                )
                continue
            rows.append((line_no, item))
    return rows


def sha256_path(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_mt5_deal_exports(root: Path, issues: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    account_history_dir = root / "data" / "account_history"
    rows: list[tuple[int, dict[str, Any]]] = []
    if not account_history_dir.exists():
        return rows
    seen_deals: set[tuple[Any, ...]] = set()
    for path in sorted(account_history_dir.glob("mt5_deals_*.jsonl")):
        for line_no, row in read_jsonl(path, issues):
            if row.get("schema_version") == "mt5_account_history_deal_export_v1":
                deal_key = (
                    row.get("ticket"),
                    row.get("order"),
                    row.get("position_id"),
                    row.get("entry"),
                    row.get("time_utc"),
                )
                if deal_key in seen_deals:
                    continue
                seen_deals.add(deal_key)
            rows.append((line_no, row))
    return rows


def latest_row_time(rows: list[tuple[int, dict[str, Any]]]) -> datetime | None:
    keys = (
        "created_at_utc",
        "timestamp_utc",
        "decision_time_utc",
        "asof_latest_candle_utc",
        "candle_close_utc",
        "checked_candle_time_utc",
        "time_utc",
    )
    latest: datetime | None = None
    for _, row in rows:
        for key in keys:
            dt = parse_dt(row.get(key))
            if dt is None:
                continue
            if latest is None or dt > latest:
                latest = dt
    return latest


def validate_trade_geometry(
    row: dict[str, Any],
    *,
    side_field: str,
    entry_field: str,
    sl_field: str,
    tp_field: str,
) -> str | None:
    side = str(row.get(side_field) or "").upper()
    try:
        entry = float(row.get(entry_field))
        stop = float(row.get(sl_field))
        tp1 = float(row.get(tp_field))
    except (TypeError, ValueError):
        return "entry/stop/tp1 not numeric"
    if side == "LONG" and not (stop < entry < tp1):
        return f"LONG geometry expected stop < entry < tp1, got {stop}, {entry}, {tp1}"
    if side == "SHORT" and not (tp1 < entry < stop):
        return f"SHORT geometry expected tp1 < entry < stop, got {tp1}, {entry}, {stop}"
    if side not in {"LONG", "SHORT"}:
        return f"side is not LONG/SHORT: {side!r}"
    return None


def validate_schema_row(
    name: str,
    spec: JsonlSpec,
    line_no: int,
    row: dict[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    path = f"shadow_logs/{name}"
    schema = row.get("schema_version")
    if (
        spec.expected_schema
        and schema != spec.expected_schema
        and schema not in LEGACY_SCHEMA_ALLOWLIST.get(name, set())
    ):
        add_issue(
            issues,
            path=path,
            line=line_no,
            severity="SERIOUS",
            code="SCHEMA_VERSION_MISMATCH",
            message=f"expected {spec.expected_schema}, got {schema!r}",
        )

    nullable_required = set(spec.nullable_required_fields)
    for field in spec.required_fields:
        if field in nullable_required:
            if field not in row:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="MISSING_REQUIRED_FIELD",
                    message=f"missing required field {field}",
                )
            continue
        if field not in row or is_missing(row.get(field)):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="MISSING_REQUIRED_FIELD",
                message=f"missing or empty required field {field}",
            )
    for field in spec.nullable_required_fields:
        if field not in row:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="MISSING_REQUIRED_FIELD",
                message=f"missing required field {field}",
            )

    if row.get("promotion_verdict") and row.get("promotion_verdict") not in ALLOWED_PROMOTION_VERDICTS:
        add_issue(
            issues,
            path=path,
            line=line_no,
            severity="SERIOUS",
            code="UNEXPECTED_PROMOTION_VERDICT",
            message=f"unexpected promotion_verdict {row.get('promotion_verdict')!r}",
        )

    if row.get("evidence_class") and row.get("evidence_class") not in ALLOWED_EVIDENCE_CLASSES:
        add_issue(
            issues,
            path=path,
            line=line_no,
            severity="SERIOUS",
            code="UNEXPECTED_EVIDENCE_CLASS",
            message=f"unexpected evidence_class {row.get('evidence_class')!r}",
        )

    for field_path in recursive_nonfinite(row):
        add_issue(
            issues,
            path=path,
            line=line_no,
            severity="SERIOUS",
            code="NONFINITE_NUMBER",
            message=f"non-finite number at {field_path}",
        )

    if name == "strategy_follow_evaluations.jsonl":
        snapshots = row.get("strategy_snapshots")
        if not isinstance(snapshots, list) or not snapshots:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="EMPTY_STRATEGY_SNAPSHOTS",
                message="strategy_snapshots must be a non-empty list",
            )
        if str(row.get("ai_dependency") or "").startswith("NO_AI") and "CALLED" in str(
            row.get("ai_status") or ""
        ) and str(row.get("ai_status")) not in {
            "NOT_CALLED_AT_ROW_TIME",
            "NOT_CALLED_BY_SHADOW_OBSERVER",
        }:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_STATUS_CONFLICT",
                message=f"no-AI dependency conflicts with ai_status={row.get('ai_status')!r}",
            )

    if name == "strategy_follow_candidates.jsonl":
        confluence = row.get("external_confluence") or {}
        if not isinstance(confluence, dict) or "sierra" not in confluence or "databento" not in confluence:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="MISSING_EXTERNAL_CONFLUENCE",
                message="external_confluence must include sierra and databento",
            )
        if not isinstance(row.get("strategy_snapshots"), list) or not row.get("strategy_snapshots"):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="EMPTY_STRATEGY_SNAPSHOTS",
                message="candidate row has no strategy registry snapshots",
            )
        params = row.get("trade_parameters") or {}
        if isinstance(params, dict) and params:
            geom = validate_trade_geometry(
                {"side": row.get("side"), **params},
                side_field="side",
                entry_field="entry_price",
                sl_field="stop_loss",
                tp_field="take_profit_1",
            )
            if geom:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="TRADE_GEOMETRY_INVALID",
                    message=geom,
                )

    if name == "ai_narrowing_policy_shadow_evaluations.jsonl":
        event = row.get("event")
        evaluation = row.get("evaluation")
        if not isinstance(event, dict):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_NARROWING_EVENT_NOT_OBJECT",
                message="event must be a JSON object",
            )
            event = {}
        if not isinstance(evaluation, dict):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_NARROWING_EVALUATION_NOT_OBJECT",
                message="evaluation must be a JSON object",
            )
            evaluation = {}
        for container_name, container in (("row", row), ("event", event), ("evaluation", evaluation)):
            for field in AI_NARROWING_FORBIDDEN_TRUE_FIELDS:
                if field in container and container.get(field) is not False:
                    add_issue(
                        issues,
                        path=path,
                        line=line_no,
                        severity="SERIOUS",
                        code="AI_NARROWING_FORBIDDEN_RUNTIME_FLAG",
                        message=f"{container_name}.{field} must be false, got {container.get(field)!r}",
                    )
        if row.get("current_ai_runtime_behavior") != "UNCHANGED_DEFAULT_AI_DECISION_GATE":
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_NARROWING_RUNTIME_BEHAVIOR_CHANGED",
                message=f"unexpected current_ai_runtime_behavior={row.get('current_ai_runtime_behavior')!r}",
            )
        missing_fields = row.get("missing_required_fields")
        if not isinstance(missing_fields, list):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_NARROWING_MISSING_FIELDS_NOT_LIST",
                message="missing_required_fields must be a list",
            )
            missing_fields = []
        if row.get("event_adapter_status") == "AI_NARROWING_EVENT_CONTRACT_COMPLETE" and missing_fields:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_NARROWING_COMPLETE_EVENT_HAS_MISSING_FIELDS",
                message=f"complete event reports missing fields {missing_fields}",
            )
        if row.get("event_adapter_status") == "AI_NARROWING_EVENT_CONTRACT_INCOMPLETE" and not missing_fields:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_NARROWING_INCOMPLETE_EVENT_WITHOUT_MISSING_FIELDS",
                message="incomplete event must list missing_required_fields",
            )
        matched_ids = row.get("matched_policy_row_ids")
        if not isinstance(matched_ids, list):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_NARROWING_MATCHED_POLICY_IDS_NOT_LIST",
                message="matched_policy_row_ids must be a list",
            )
            matched_ids = []
        if int(row.get("matched_policy_rows") or 0) != len(matched_ids):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_NARROWING_MATCHED_POLICY_COUNT_MISMATCH",
                message=f"matched_policy_rows={row.get('matched_policy_rows')!r}, ids={len(matched_ids)}",
            )

    if name == "ai_decision_trace.jsonl":
        status = str(row.get("response_status") or "")
        if status not in AI_DECISION_TRACE_ALLOWED_STATUSES:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_DECISION_TRACE_STATUS_UNEXPECTED",
                message=f"unexpected response_status={status!r}",
            )
        try:
            attempts = int(row.get("parse_attempts"))
        except (TypeError, ValueError):
            attempts = -1
        if attempts < 0 or attempts > 2:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_DECISION_TRACE_PARSE_ATTEMPTS_INVALID",
                message=f"parse_attempts must be 0, 1, or 2; got {row.get('parse_attempts')!r}",
            )
        if status.startswith("api_") and attempts != 0:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_DECISION_TRACE_API_STATUS_ATTEMPTS_CONFLICT",
                message=f"{status} rows must have parse_attempts=0, got {attempts}",
            )
        prompt_fingerprint = row.get("prompt_fingerprint")
        if not isinstance(prompt_fingerprint, dict):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_DECISION_TRACE_PROMPT_FINGERPRINT_NOT_OBJECT",
                message="prompt_fingerprint must be a JSON object",
            )
            prompt_fingerprint = {}
        for field in ("system_prompt_sha256", "user_message_sha256", "prompt_bundle_sha256"):
            if not re.fullmatch(r"[0-9a-f]{64}", str(prompt_fingerprint.get(field) or "")):
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="AI_DECISION_TRACE_PROMPT_HASH_INVALID",
                    message=f"prompt_fingerprint.{field} must be a SHA256 hex digest",
                )
        for key in AI_DECISION_TRACE_FORBIDDEN_TEXT_FIELDS:
            if key in row:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="AI_DECISION_TRACE_FULL_TEXT_FIELD_PRESENT",
                    message=f"trace row must not store full-text field {key}",
                )
        boundary = row.get("research_boundary")
        if not isinstance(boundary, dict):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="AI_DECISION_TRACE_BOUNDARY_NOT_OBJECT",
                message="research_boundary must be a JSON object",
            )
            boundary = {}
        for field in (
            "runtime_trading_or_live_broker_effect",
            "broker_operation",
            "paid_api_or_vendor_call_added_by_logger",
            "runtime_candidate_use_permitted",
            "stores_full_prompt_or_response_text",
        ):
            if boundary.get(field) is not False:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="AI_DECISION_TRACE_FORBIDDEN_BOUNDARY_FLAG",
                    message=f"research_boundary.{field} must be false, got {boundary.get(field)!r}",
                )

    if name == "candidate_path_follow.jsonl":
        params = row.get("trade_parameters") or {}
        if isinstance(params, dict):
            geom = validate_trade_geometry(
                {"side": row.get("side"), **params},
                side_field="side",
                entry_field="entry_price",
                sl_field="stop_loss",
                tp_field="take_profit_1",
            )
            if geom:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="PATH_TRADE_GEOMETRY_INVALID",
                    message=geom,
                )
        label = str(row.get("path_label") or "")
        touched = row.get("touched_entry")
        if label.startswith("no_touch") and touched is not False:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="PATH_TOUCH_LABEL_CONFLICT",
                message=f"path_label={label!r} but touched_entry={touched!r}",
            )
        if "without_entry_touch" in label and touched is not False:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="PATH_TOUCH_LABEL_CONFLICT",
                message=f"path_label={label!r} but touched_entry={touched!r}",
            )
        if ("entry_touched" in label or "went_through_entry" in label) and touched is not True:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="PATH_TOUCH_LABEL_CONFLICT",
                message=f"path_label={label!r} but touched_entry={touched!r}",
            )

    if name == "live_mechanical_strategy_shadow_outcomes.jsonl":
        for field in ("no_ai_calls", "no_canary_required"):
            if row.get(field) is not True:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="MECHANICAL_SHADOW_SAFETY_FLAG_FALSE",
                    message=f"{field} must be true, got {row.get(field)!r}",
                )
        if row.get("paid_fetch_attempted") is not False:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="MECHANICAL_SHADOW_PAID_FETCH_ATTEMPTED",
                message="mechanical shadow rows must not trigger paid data fetches",
            )
        status = str(row.get("score_status") or "")
        if status.startswith("COMPUTED") and not isinstance(row.get("path_metrics"), dict):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="MECHANICAL_SHADOW_MISSING_PATH_METRICS",
                message="computed mechanical rows must carry path_metrics",
            )

    if name == "v2b_forward_pairs.jsonl":
        for field in ("ob_boundary_outcome", "j46_baseline_outcome", "fixed_r_comparator", "fvg_comparator"):
            value = row.get(field)
            if not isinstance(value, dict) or "label_status" not in value:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="V2B_COMPARATOR_MISSING_LABEL_STATUS",
                    message=f"{field} must be an object with label_status",
                )

    if name == "fvg_ob_confluence.jsonl":
        decision_time_fields = row.get("decision_time_fields") or {}
        if isinstance(decision_time_fields, dict):
            leaked = sorted(set(decision_time_fields) & POST_OUTCOME_KEYS)
            if leaked:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="POST_OUTCOME_FIELD_IN_DECISION_FIELDS",
                    message=f"decision_time_fields contains post-outcome keys: {leaked}",
                )
        if str(row.get("no_leak_status") or "").startswith("POST_OUTCOME"):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="NO_LEAK_STATUS_FAILED",
                message=f"no_leak_status={row.get('no_leak_status')!r}",
            )

    if name == "context_control_ledger.jsonl":
        if row.get("control_only") is not True:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="CONTEXT_NOT_CONTROL_ONLY",
                message="context control row must remain control_only=true",
            )
        if row.get("promotion_verdict") != PROMOTION_VERDICT:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="CONTEXT_CONTROL_PROMOTION_VERDICT_NOT_NO_PROMOTION",
                message=f"context row promotion_verdict={row.get('promotion_verdict')!r}",
            )
        direct_problems = context_direct_validation_problems(row)
        if direct_problems:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="CONTEXT_CONTROL_DIRECT_STRATEGY_VALIDATION_FORBIDDEN",
                message=f"context/control rows cannot carry direct strategy-validation claims: {direct_problems[:5]}",
            )

    if name == "account_truth_reconciliation_status.jsonl":
        if row.get("actual_r_claim_allowed") is True and row.get("broker_actual_r") is None:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="ACCOUNT_TRUTH_ALLOWS_ACTUAL_R_WITHOUT_VALUE",
                message="account truth row allows actual-R claim but has no broker_actual_r",
            )

    if name == "broker_actual_r_audit.jsonl":
        evidence_class = row.get("accounting_evidence_class")
        if row.get("actual_r_claim_allowed") is True and evidence_class != "ACCOUNT_HISTORY_REALIZED":
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="BROKER_ACTUAL_R_ALLOWED_WITHOUT_ACCOUNT_HISTORY",
                message=f"actual_r_claim_allowed requires ACCOUNT_HISTORY_REALIZED, got {evidence_class!r}",
            )
        if evidence_class != "ACCOUNT_HISTORY_REALIZED" and row.get("broker_actual_r") is not None:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="BROKER_ACTUAL_R_VALUE_ON_NON_ACCOUNT_HISTORY_ROW",
                message=f"broker_actual_r is present on {evidence_class!r} row",
            )

    if name == "j46_j49_exit_comparator_audit.jsonl":
        if row.get("actual_r_claim_allowed") is True and row.get("broker_actual_r_evidence_class") != "ACCOUNT_HISTORY_REALIZED":
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="J46_COMPARATOR_ACTUAL_R_ALLOWED_WITHOUT_ACCOUNT_HISTORY",
                message=(
                    "J46/J49 comparator actual-R claims require ACCOUNT_HISTORY_REALIZED "
                    f"evidence, got {row.get('broker_actual_r_evidence_class')!r}"
                ),
            )
        if row.get("row_type") == "candidate_context" and row.get("actual_r_claim_allowed") is True:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="J46_COMPARATOR_CANDIDATE_CONTEXT_ACTUAL_R_FORBIDDEN",
                message="candidate-context rows must never claim broker actual-R",
            )
        if row.get("row_type") == "candidate_context" and row.get("broker_actual_r") is not None:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="J46_COMPARATOR_CANDIDATE_CONTEXT_BROKER_R_FORBIDDEN",
                message="candidate-context rows must keep broker_actual_r null",
            )

    if name == "s79_side_aware_risk_context.jsonl":
        if row.get("actual_r_claim_allowed") is True and row.get("broker_actual_r_evidence_class") != "ACCOUNT_HISTORY_REALIZED":
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="S79_RISK_CONTEXT_ACTUAL_R_ALLOWED_WITHOUT_ACCOUNT_HISTORY",
                message=(
                    "S79/side-aware context actual-R claims require ACCOUNT_HISTORY_REALIZED "
                    f"evidence, got {row.get('broker_actual_r_evidence_class')!r}"
                ),
            )
        risk_context = row.get("risk_context")
        if not isinstance(risk_context, dict):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="S79_RISK_CONTEXT_NOT_OBJECT",
                message="risk_context must be an object",
            )
        elif risk_context.get("s79_policy_id") != "S79_UNIFORM_FN_RISK_POLICY":
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="S79_POLICY_ID_MISSING",
                message=f"risk_context.s79_policy_id={risk_context.get('s79_policy_id')!r}",
            )
        if row.get("promotion_verdict") != PROMOTION_VERDICT:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="S79_CONTEXT_PROMOTION_VERDICT_NOT_NO_PROMOTION",
                message=f"risk-context row promotion_verdict={row.get('promotion_verdict')!r}",
            )

    if name == "regime_decay_outcome_join.jsonl":
        if row.get("actual_r_claim_allowed") is True and row.get("broker_actual_r_evidence_class") != "ACCOUNT_HISTORY_REALIZED":
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="REGIME_DECAY_ACTUAL_R_ALLOWED_WITHOUT_ACCOUNT_HISTORY",
                message=(
                    "Regime/decay actual-R claims require ACCOUNT_HISTORY_REALIZED "
                    f"evidence, got {row.get('broker_actual_r_evidence_class')!r}"
                ),
            )
        regime_context = row.get("regime_context")
        if not isinstance(regime_context, dict):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="REGIME_DECAY_REGIME_CONTEXT_NOT_OBJECT",
                message="regime_context must be an object",
            )
        ob_context = row.get("ob_continuation_context")
        if not isinstance(ob_context, dict):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="REGIME_DECAY_OB_CONTEXT_NOT_OBJECT",
                message="ob_continuation_context must be an object",
            )
        elif ob_context.get("join_status") == "OB_CONTINUATION_JOINED" and not (
            ob_context.get("symbol_scope_snapshot") or ob_context.get("portfolio_scope_snapshot")
        ):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="REGIME_DECAY_OB_JOINED_WITHOUT_SNAPSHOT",
                message="OB-continuation join_status is joined but no scope snapshot is present",
            )
        if row.get("promotion_verdict") != PROMOTION_VERDICT:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="REGIME_DECAY_PROMOTION_VERDICT_NOT_NO_PROMOTION",
                message=f"regime/decay row promotion_verdict={row.get('promotion_verdict')!r}",
            )

    if name == "decision_layer_diagnostics_join.jsonl":
        if row.get("decision_diagnostics_status") == DECISION_DIAGNOSTICS_ACTION_REQUIRED or row.get("action_required_codes"):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="DECISION_DIAGNOSTICS_ACTION_REQUIRED",
                message=f"decision diagnostics row requires action: {row.get('action_required_codes')}",
            )
        for context_field in (
            "verification_context",
            "candidate_features_context",
            "d1_bias_lag_context",
            "direction_emission_context",
            "sl_beyond_ob_context",
            "touch_count_context",
        ):
            if not isinstance(row.get(context_field), dict):
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="DECISION_DIAGNOSTICS_CONTEXT_NOT_OBJECT",
                    message=f"{context_field} must be an object",
                )
        join_statuses = row.get("diagnostic_join_statuses")
        if not isinstance(join_statuses, dict) or "candidate_features" not in join_statuses:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="DECISION_DIAGNOSTICS_JOIN_STATUSES_MISSING",
                message="diagnostic_join_statuses must include candidate_features",
            )
        if row.get("promotion_verdict") != PROMOTION_VERDICT:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="DECISION_DIAGNOSTICS_PROMOTION_VERDICT_NOT_NO_PROMOTION",
                message=f"decision diagnostics row promotion_verdict={row.get('promotion_verdict')!r}",
            )

    if name == "mechanical_context_diagnostics_join.jsonl":
        if row.get("mechanical_context_status") == MECHANICAL_CONTEXT_ACTION_REQUIRED or row.get("action_required_codes"):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="MECHANICAL_CONTEXT_ACTION_REQUIRED",
                message=f"mechanical context row requires action: {row.get('action_required_codes')}",
            )
        for context_field in (
            "path_context",
            "dumb_baseline_context",
            "proximity_context",
            "liquidity_distance_context",
            "displacement_context",
            "structure_divergence_context",
        ):
            if not isinstance(row.get(context_field), dict):
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="MECHANICAL_CONTEXT_NOT_OBJECT",
                    message=f"{context_field} must be an object",
                )
        join_statuses = row.get("mechanical_context_join_statuses")
        if not isinstance(join_statuses, dict) or "proximity" not in join_statuses:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="MECHANICAL_CONTEXT_JOIN_STATUSES_MISSING",
                message="mechanical_context_join_statuses must include proximity",
            )
        dumb_context = row.get("dumb_baseline_context") if isinstance(row.get("dumb_baseline_context"), dict) else {}
        comparator_outcome = dumb_context.get("post_decision_comparator_outcome") if isinstance(dumb_context.get("post_decision_comparator_outcome"), dict) else {}
        if comparator_outcome and comparator_outcome.get("feature_safe") is not False:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="MECHANICAL_BASELINE_OUTCOME_FEATURE_SAFE_NOT_FALSE",
                message="dumb baseline outcome context must remain feature_safe=false",
            )
        if row.get("actual_r_claim_allowed") is True and row.get("broker_actual_r") is None:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="MECHANICAL_CONTEXT_ACTUAL_R_ALLOWED_WITHOUT_VALUE",
                message="mechanical context row allows actual-R but broker_actual_r is missing",
            )
        if row.get("promotion_verdict") != PROMOTION_VERDICT:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="MECHANICAL_CONTEXT_PROMOTION_VERDICT_NOT_NO_PROMOTION",
                message=f"mechanical context row promotion_verdict={row.get('promotion_verdict')!r}",
            )

    if name == "account_pnl_truth_reconciliation.jsonl":
        if row.get("result_r") is not None and not row.get("r_evidence_class"):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="R_CLAIM_MISSING_EVIDENCE_CLASS",
                message="result_r is present but r_evidence_class is missing",
            )
        if row.get("realized_usd") is not None and not row.get("dollar_evidence_class"):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="DOLLAR_CLAIM_MISSING_EVIDENCE_CLASS",
                message="realized_usd is present but dollar_evidence_class is missing",
            )
        if row.get("actual_dollar_claim_allowed") is True and row.get("dollar_evidence_class") != "ACCOUNT_HISTORY_PROFIT":
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="ACTUAL_DOLLAR_ALLOWED_WITHOUT_ACCOUNT_HISTORY_PROFIT",
                message=f"actual dollar claim requires ACCOUNT_HISTORY_PROFIT, got {row.get('dollar_evidence_class')!r}",
            )

    if name == "trade_index_lifecycle_audit.jsonl":
        if row.get("lifecycle_state") == "LIMIT_PLACED" and not (
            row.get("has_execution")
            or row.get("has_exit")
            or row.get("has_embedded_pending_lifecycle")
            or row.get("has_pending_lifecycle_audit")
        ):
            limitations = set(row.get("documented_limitation_codes") or [])
            if "LIMIT_PLACED_MISSING_EXECUTION_AND_PENDING_LIFECYCLE_STATE" not in limitations:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="LIMIT_PLACED_LIFECYCLE_GAP_UNDOCUMENTED",
                    message="LIMIT_PLACED row lacks execution/exit/pending lifecycle truth without documented limitation",
                )
    if name == "pending_limit_lifecycle.jsonl":
        geom = validate_trade_geometry(
            row,
            side_field="side",
            entry_field="entry_price",
            sl_field="stop_loss",
            tp_field="take_profit_1",
        )
        if geom:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="PENDING_TRADE_GEOMETRY_INVALID",
                message=geom,
            )
        before = row.get("candles_elapsed_before")
        after = row.get("candles_elapsed_after")
        if before is not None and after is not None:
            try:
                if int(after) < int(before):
                    add_issue(
                        issues,
                        path=path,
                        line=line_no,
                        severity="SERIOUS",
                        code="PENDING_CANDLE_COUNTER_REGRESSED",
                        message=f"candles_elapsed_after {after} < before {before}",
                    )
            except (TypeError, ValueError):
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="PENDING_CANDLE_COUNTER_NON_NUMERIC",
                    message="candles_elapsed_before/after must be numeric when present",
                )
        if row.get("order_send_success") is True and row.get("order_send_attempted") is not True:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="ORDER_SUCCESS_WITHOUT_ATTEMPT",
                message="order_send_success true while order_send_attempted is not true",
            )
        if row.get("wrong_side_abort") is True and not row.get("cancel_reason"):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="WRONG_SIDE_ABORT_WITHOUT_REASON",
                message="wrong_side_abort true without cancel_reason",
            )

    if name == "shadow_observer_status.jsonl":
        for field in ("no_ai_calls", "no_canary_required", "no_execution"):
            if row.get(field) is not True:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="SHADOW_OBSERVER_SAFETY_FLAG_FALSE",
                    message=f"{field} must be true, got {row.get(field)!r}",
                )

    if name == "shadow_observer_tick_enrichment.jsonl":
        for field in ("no_ai_calls", "no_canary_required"):
            if row.get(field) is not True:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="OBSERVER_TICK_ENRICHMENT_SAFETY_FLAG_FALSE",
                    message=f"{field} must be true, got {row.get(field)!r}",
                )
        if row.get("paid_fetch_attempted") is not False:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="OBSERVER_TICK_ENRICHMENT_PAID_FETCH_ATTEMPTED",
                message="observer tick enrichment must not trigger paid data fetches",
            )

    if name in {
        "pending_limit_lifecycle_join_backfill.jsonl",
        "live_structural_strategy_metadata.jsonl",
        "v2b_forward_pair_resolutions.jsonl",
        "prefill_delivery_path_resolutions.jsonl",
        "fvg_ob_confluence_resolutions.jsonl",
        "missed_opportunity_shadow.jsonl",
        "candidate_ltf_path_order.jsonl",
        "databento_live_trigger_decisions.jsonl",
        "sierra_confluence_source_status.jsonl",
        "live_candidate_strategy_rollups.jsonl",
        "live_candidate_opportunity_clusters.jsonl",
        "account_truth_reconciliation_status.jsonl",
        "proxy_blocker_status.jsonl",
        "ml_shadow_status.jsonl",
        "external_source_blocker_status.jsonl",
        "lto_blocked_lane_status.jsonl",
        "candidate_mso_snapshot_joins.jsonl",
        "candidate_registry_audit.jsonl",
        "candidate_path_contract_audit.jsonl",
        "opportunity_lifecycle_audit.jsonl",
        "pending_limit_lifecycle_audit.jsonl",
        "v2b_forward_pair_resolution_audit.jsonl",
        "prefill_delivery_path_audit.jsonl",
        "fvg_ob_confluence_audit.jsonl",
        "context_control_audit.jsonl",
        "broker_actual_r_audit.jsonl",
        "j46_j49_exit_comparator_audit.jsonl",
        "s79_side_aware_risk_context.jsonl",
        "regime_decay_outcome_join.jsonl",
        "decision_layer_diagnostics_join.jsonl",
        "mechanical_context_diagnostics_join.jsonl",
        "account_pnl_truth_reconciliation.jsonl",
        "trade_index_lifecycle_audit.jsonl",
        "nas100_orderflow_adverse_selection_status.jsonl",
        "sierra_depth_enrichment_status.jsonl",
        "sierra_proxy_registry_status.jsonl",
        "gbpjpy_proxy_gap_status.jsonl",
        "sierra_6b_si_depth_policy_status.jsonl",
        "orderflow_primitives_status.jsonl",
        "exit_management_shadow_status.jsonl",
        "session_volatility_sweep_status.jsonl",
        "notification_queue_dead_zone_status.jsonl",
        "storage_retention_status.jsonl",
        "v2_structural_selector_readiness.jsonl",
        "xauusd_same_market_extension_status.jsonl",
        "es_mes_preregistration_status.jsonl",
        "shadow_observer_hardening_status.jsonl",
    }:
        for field in ("no_ai_calls", "no_canary_required", "no_execution"):
            if row.get(field) is not True:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="GAP_CLOSURE_SAFETY_FLAG_FALSE",
                    message=f"{field} must be true, got {row.get(field)!r}",
                )
        for field in ("ai_calls", "canary_calls", "order_calls", "paid_data_calls"):
            if row.get(field) not in {0, 0.0}:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="GAP_CLOSURE_CALL_COUNTER_NONZERO",
                    message=f"{field} must be zero, got {row.get(field)!r}",
                )
        if row.get("paid_fetch_attempted") is not False:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="GAP_CLOSURE_PAID_FETCH_ATTEMPTED",
                message="gap closure rows must not trigger paid data fetches",
            )

    if name == "storage_retention_status.jsonl":
        if row.get("dry_run_only") is not True or row.get("deletion_performed") is not False:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="STORAGE_RETENTION_NOT_DRY_RUN",
                message="storage retention monitor must remain dry-run and perform no deletion",
            )
        policy = row.get("deletion_allowlist_policy") if isinstance(row.get("deletion_allowlist_policy"), dict) else {}
        for field in ("raw_source_delete_allowed", "evidence_log_delete_allowed", "reports_delete_allowed", "apply_mode_available"):
            if policy.get(field) is not False:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="STORAGE_RETENTION_PROTECTED_DELETE_ALLOWED",
                    message=f"{field} must be false, got {policy.get(field)!r}",
                )
        if row.get("storage_status") == STORAGE_RETENTION_ACTION_REQUIRED:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="STORAGE_RETENTION_ACTION_REQUIRED",
                message=f"storage retention row requires action: {row.get('action_required_codes')}",
            )

    if name in {"databento_live_confluence.jsonl", "databento_live_budget_ledger.jsonl"}:
        for field in ("no_ai_calls", "no_canary_required", "no_execution"):
            if row.get(field) is not True:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="DATABENTO_LIVE_SAFETY_FLAG_FALSE",
                    message=f"{field} must be true, got {row.get(field)!r}",
                )
        for field in ("ai_calls", "canary_calls", "order_calls"):
            if row.get(field) not in {0, 0.0}:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="DATABENTO_LIVE_FORBIDDEN_CALL_COUNTER_NONZERO",
                    message=f"{field} must be zero, got {row.get(field)!r}",
                )
        if row.get("paid_fetch_attempted") is True and not row.get("trigger_id"):
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="DATABENTO_LIVE_PAID_ATTEMPT_WITHOUT_TRIGGER",
                message="paid Databento attempts must carry a trigger_id",
            )
        if row.get("paid_fetch_attempted") is True and float(row.get("databento_calls") or 0) <= 0:
            add_issue(
                issues,
                path=path,
                line=line_no,
                severity="SERIOUS",
                code="DATABENTO_LIVE_PAID_ATTEMPT_WITHOUT_CALL_COUNTER",
                message="paid Databento attempts must carry databento_calls > 0",
            )
        if name == "databento_live_confluence.jsonl" and row.get("status") == "LIVE_RECORD":
            features = row.get("features")
            if not isinstance(features, dict) or not features:
                add_issue(
                    issues,
                    path=path,
                    line=line_no,
                    severity="SERIOUS",
                    code="DATABENTO_LIVE_RECORD_EMPTY_FEATURES",
                    message="LIVE_RECORD rows must carry normalized Databento features",
                )


def allowed_append_only_unique_key_supersession(name: str, row: dict[str, Any]) -> bool:
    """Allow explicit mechanical correction rows to supersede an older key.

    Mechanical strategy rows are append-only evidence. When a later source
    reconciliation corrects an older candidate/strategy/as-of interpretation,
    readers choose the latest created row; the verifier should still reject
    accidental duplicate keys that are not marked as corrections.
    """
    if name == "candidate_path_follow.jsonl":
        return (
            bool(row.get("correction_of_created_at_utc"))
            and str(row.get("correction_reason") or "") == "same_candidate_asof_path_recomputed_changed"
            and str(row.get("manual_backfill_status") or "").startswith("CORRECTED")
        )
    if name == "fvg_ob_confluence.jsonl":
        return (
            str(row.get("manual_backfill_status") or "")
            == "FVG_OB_EXACT_GEOMETRY_RECOVERED_FROM_STRATEGY_FOLLOW_DECISION_MSO"
            and str(row.get("geometry_recovery_no_leak_status") or "")
            == "DECISION_TIME_MSO_ONLY_NO_POST_OUTCOME_FIELDS"
            and bool(row.get("fvg_bounds") or row.get("ob_bounds"))
        )
    if name != "live_mechanical_strategy_shadow_outcomes.jsonl":
        return False
    return (
        bool(row.get("correction_of_created_at_utc"))
        and str(row.get("correction_reason") or "")
        == "latest_computed_shadow_outcome_changed_after_source_reconciliation"
        and str(row.get("manual_backfill_status") or "").startswith("CORRECTED")
    )


def verify_jsonl_file(
    root: Path,
    name: str,
    spec: JsonlSpec | None,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    path = root / name
    rows = read_jsonl(path, issues)
    schemas = Counter(row.get("schema_version") for _, row in rows if row.get("schema_version"))
    evidence = Counter(row.get("evidence_class") for _, row in rows if row.get("evidence_class"))
    verdicts = Counter(row.get("promotion_verdict") for _, row in rows if row.get("promotion_verdict"))

    if spec:
        for line_no, row in rows:
            validate_schema_row(name, spec, line_no, row, issues)
        if spec.unique_key:
            seen: dict[tuple[Any, ...], int] = {}
            for line_no, row in rows:
                key = tuple(row.get(field) for field in spec.unique_key)
                if any(item is None for item in key):
                    continue
                if key in seen:
                    if not allowed_append_only_unique_key_supersession(name, row):
                        add_issue(
                            issues,
                            path=str(path),
                            line=line_no,
                            severity="SERIOUS",
                            code="DUPLICATE_UNIQUE_KEY",
                            message=f"duplicate key {spec.unique_key}={key!r}; first seen at line {seen[key]}",
                        )
                else:
                    seen[key] = line_no
        if spec.expected_schema and rows and not schemas:
            add_issue(
                issues,
                path=str(path),
                severity="SERIOUS",
                code="MISSING_SCHEMA_VERSION_ALL_ROWS",
                message="no rows have schema_version",
            )

    if name == "shadow_observer_status.jsonl" and rows:
        for line_no, row in rows[-10:]:
            if row.get("observer_run_id") is None:
                add_issue(
                    issues,
                    path=str(path),
                    line=line_no,
                    severity="SERIOUS",
                    code="CURRENT_SHADOW_OBSERVER_RUN_ID_MISSING",
                    message="recent shadow observer status row is missing observer_run_id",
                )

    latest = latest_row_time(rows)
    skip_freshness = False
    if spec and spec.freshness_mode in {"candidate_driven", "source_driven"}:
        skip_freshness = True
    elif spec and spec.freshness_mode == "kill_zone_gated":
        active_kill_zone = any_configured_kill_zone_active(root.parent, now_utc)
        skip_freshness = active_kill_zone is False
    if (
        spec
        and spec.freshness_minutes is not None
        and latest is not None
        and not skip_freshness
    ):
        age_minutes = (now_utc - latest).total_seconds() / 60.0
        if age_minutes > spec.freshness_minutes:
            add_issue(
                issues,
                path=str(path),
                severity="MODERATE" if spec.event_driven else "SERIOUS",
                code="FRESHNESS_THRESHOLD_EXCEEDED",
                message=(
                    f"latest timestamp age {age_minutes:.1f}m exceeds "
                    f"{spec.freshness_minutes}m"
                ),
            )

    return {
        "path": str(path),
        "exists": path.exists(),
        "rows": len(rows),
        "latest_timestamp_utc": latest.isoformat() if latest else None,
        "schemas": dict(schemas),
        "evidence_classes": dict(evidence),
        "promotion_verdicts": dict(verdicts),
        "known_spec": spec is not None,
        "freshness_mode": spec.freshness_mode if spec else None,
    }


def verify_csv_file(root: Path, name: str, spec: dict[str, Any], now_utc: datetime) -> dict[str, Any]:
    path = root / name
    rows = 0
    headers: list[str] = []
    latest_mtime = None
    if path.exists():
        latest_mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            try:
                headers = next(reader)
            except StopIteration:
                headers = []
            rows = sum(1 for _ in reader)
    age_minutes = None
    if latest_mtime is not None:
        age_minutes = (now_utc - latest_mtime).total_seconds() / 60.0
    return {
        "path": str(path),
        "exists": path.exists(),
        "rows": rows,
        "headers": headers,
        "latest_mtime_utc": latest_mtime.isoformat() if latest_mtime else None,
        "age_minutes": age_minutes,
        "event_driven": bool(spec.get("event_driven", True)),
    }


def summarize_status(summary: dict[str, Any], issues: list[dict[str, Any]]) -> str:
    severe = [i for i in issues if i["severity"] in {"CRITICAL", "SERIOUS"}]
    moderate = [i for i in issues if i["severity"] == "MODERATE"]
    if severe:
        return "ACTION_REQUIRED"
    if moderate:
        return "CHECK_WARNINGS_PRESENT"
    waiting = summary.get("waiting_files", {})
    if waiting:
        return "OK_WITH_DOCUMENTED_WAITING_LANES"
    return "OK"


def write_markdown(report: dict[str, Any], output_md: Path) -> None:
    issues = report["issues"]
    severity_counts = Counter(issue["severity"] for issue in issues)
    mso_health = report.get("mso_candidate_join_health") or {}
    registry_health = report.get("candidate_registry_audit_health") or {}
    path_health = report.get("candidate_path_contract_health") or {}
    lifecycle_health = report.get("opportunity_lifecycle_audit_health") or {}
    pending_lifecycle_health = report.get("pending_limit_lifecycle_audit_health") or {}
    v2b_health = report.get("v2b_forward_pair_resolution_audit_health") or {}
    prefill_health = report.get("prefill_delivery_path_audit_health") or {}
    fvg_ob_health = report.get("fvg_ob_confluence_audit_health") or {}
    context_control_health = report.get("context_control_audit_health") or {}
    broker_actual_r_health = report.get("broker_actual_r_audit_health") or {}
    j46_j49_exit_comparator_health = report.get("j46_j49_exit_comparator_health") or {}
    s79_side_aware_context_health = report.get("s79_side_aware_context_health") or {}
    regime_decay_outcome_health = report.get("regime_decay_outcome_health") or {}
    decision_layer_diagnostics_health = report.get("decision_layer_diagnostics_health") or {}
    mechanical_context_health = report.get("mechanical_context_health") or {}
    ml_shadow_health = report.get("ml_shadow_health") or {}
    v2_selector_readiness_health = report.get("v2_structural_selector_readiness_health") or {}
    xauusd_same_market_health = report.get("xauusd_same_market_extension_health") or {}
    es_mes_prereg_health = report.get("es_mes_preregistration_health") or {}
    shadow_observer_hardening_health = report.get("shadow_observer_hardening_health") or {}
    account_pnl_truth_health = report.get("account_pnl_truth_health") or {}
    trade_index_lifecycle_health = report.get("trade_index_lifecycle_health") or {}
    exit_management_status_health = report.get("exit_management_status_health") or {}
    session_vol_sweep_status_health = report.get("session_vol_sweep_status_health") or {}
    notification_queue_dead_zone_health = report.get("notification_queue_dead_zone_health") or {}
    ai_narrowing_policy_shadow_evaluations_health = report.get("ai_narrowing_policy_shadow_evaluations_health") or {}
    lines = [
        "# Shadow Log Integrity Verification - 2026-05-04",
        "",
        f"**Schema:** `shadow_log_integrity_verification_v1`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Overall status:** `{report['overall_status']}`",
        f"**Promotion verdict:** `NO_PROMOTION_VERDICT`",
        "",
        "## Summary",
        "",
        f"- JSONL files inspected: `{report['counts']['jsonl_files']}`",
        f"- JSONL rows inspected: `{report['counts']['jsonl_rows']}`",
        f"- Known-schema JSONL files: `{report['counts']['known_schema_jsonl_files']}`",
        f"- CSV shadow files inspected: `{report['counts']['csv_files']}`",
        f"- Documented waiting lanes: `{len(report['waiting_files'])}`",
        f"- Candidate/MSO join health: `{mso_health.get('status', 'NOT_RUN')}`",
        f"- Candidate registry audit health: `{registry_health.get('status', 'NOT_RUN')}`",
        f"- Candidate path contract health: `{path_health.get('status', 'NOT_RUN')}`",
        f"- Opportunity lifecycle audit health: `{lifecycle_health.get('status', 'NOT_RUN')}`",
        f"- Pending-limit lifecycle audit health: `{pending_lifecycle_health.get('status', 'NOT_RUN')}`",
        f"- V2b forward-pair resolution audit health: `{v2b_health.get('status', 'NOT_RUN')}`",
        f"- Pre-fill delivery path audit health: `{prefill_health.get('status', 'NOT_RUN')}`",
        f"- FVG/OB confluence audit health: `{fvg_ob_health.get('status', 'NOT_RUN')}`",
        f"- Context/control audit health: `{context_control_health.get('status', 'NOT_RUN')}`",
        f"- Broker actual-R audit health: `{broker_actual_r_health.get('status', 'NOT_RUN')}`",
        f"- J46/J49 exit-comparator audit health: `{j46_j49_exit_comparator_health.get('status', 'NOT_RUN')}`",
        f"- S79/side-aware risk-context health: `{s79_side_aware_context_health.get('status', 'NOT_RUN')}`",
        f"- Regime/decay outcome-join health: `{regime_decay_outcome_health.get('status', 'NOT_RUN')}`",
        f"- Decision-layer diagnostics health: `{decision_layer_diagnostics_health.get('status', 'NOT_RUN')}`",
        f"- Mechanical/context diagnostics health: `{mechanical_context_health.get('status', 'NOT_RUN')}`",
        f"- K55/ML shadow health: `{ml_shadow_health.get('status', 'NOT_RUN')}`",
        f"- V2 structural selector readiness health: `{v2_selector_readiness_health.get('status', 'NOT_RUN')}`",
        f"- XAUUSD same-market extension health: `{xauusd_same_market_health.get('status', 'NOT_RUN')}`",
        f"- ES/MES preregistration health: `{es_mes_prereg_health.get('status', 'NOT_RUN')}`",
        f"- Shadow-observer hardening health: `{shadow_observer_hardening_health.get('status', 'NOT_RUN')}`",
        f"- Account/PnL truth health: `{account_pnl_truth_health.get('status', 'NOT_RUN')}`",
        f"- Trade-index lifecycle health: `{trade_index_lifecycle_health.get('status', 'NOT_RUN')}`",
        f"- Exit-management no-event/status health: `{exit_management_status_health.get('status', 'NOT_RUN')}`",
        f"- Session-volatility/sweep status health: `{session_vol_sweep_status_health.get('status', 'NOT_RUN')}`",
        f"- Notification queue dead-zone health: `{notification_queue_dead_zone_health.get('status', 'NOT_RUN')}`",
        f"- AI narrowing policy shadow-evaluation health: `{ai_narrowing_policy_shadow_evaluations_health.get('status', 'NOT_RUN')}`",
        f"- Issues: `{len(issues)}`",
        "",
        "## Issue Counts",
        "",
        "| Severity | Count |",
        "|---|---:|",
    ]
    for severity in ("CRITICAL", "SERIOUS", "MODERATE", "LOW"):
        lines.append(f"| `{severity}` | {severity_counts.get(severity, 0)} |")

    lines.extend(
        [
            "",
            "## Known Forward/Shadow Logs",
            "",
            "| Log | Rows | Latest UTC | Schemas | Status |",
            "|---|---:|---|---|---|",
        ]
    )
    issue_by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for issue in issues:
        issue_by_path[issue["path"]].append(issue)

    for item in report["jsonl_files"]:
        if not item["known_spec"]:
            continue
        path = item["path"]
        status = "ISSUES" if issue_by_path.get(path) else "OK"
        lines.append(
            "| `{}` | {} | `{}` | `{}` | `{}` |".format(
                Path(path).name,
                item["rows"],
                item["latest_timestamp_utc"],
                item["schemas"],
                status,
            )
        )

    lines.extend(
        [
            "",
            "## Documented Waiting Lanes",
            "",
            "| Log | Reason |",
            "|---|---|",
        ]
    )
    for name, reason in sorted(report["waiting_files"].items()):
        lines.append(f"| `{name}` | {reason} |")

    lines.extend(
        [
            "",
            "## Issues",
            "",
        ]
    )
    if not issues:
        lines.append("No structural/value issues found in inspected rows.")
    else:
        lines.extend(["| Severity | Code | Path | Line | Message |", "|---|---|---|---:|---|"])
        for issue in issues[:200]:
            message = str(issue["message"]).replace("|", "\\|")
            lines.append(
                f"| `{issue['severity']}` | `{issue['code']}` | `{issue['path']}` | "
                f"{issue.get('line') or ''} | {message} |"
            )
        if len(issues) > 200:
            lines.append(f"\nOnly first 200 issues shown; JSON contains all `{len(issues)}` issues.")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This verifier checks JSON/CSV structure, schema versions, required fields, duplicate keys, timestamp freshness where expected, no-leak markers, trade geometry, path-label consistency, pending-limit lifecycle sanity, candidate-to-MSO snapshot coverage, candidate-registry contract coverage, candidate path-contract coverage, opportunity lifecycle contract coverage, pending-limit lifecycle contract coverage, V2b forward-pair resolution audit coverage, J46/J49 exit-comparator audit coverage, S79/side-aware risk-context coverage, AI narrowing shadow-evaluation coverage, exit-management no-event/status coverage, session-volatility/sweep cadence coverage, shadow-observer safety flags.",
            "- It does not promote, reject, or alter any strategy. It does not score independent alternate V2/V3 entries; it only verifies the rows currently implemented.",
        ]
    )

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def audit_candidate_mso_snapshot_coverage(
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_rows = read_jsonl(shadow_root / "strategy_follow_candidates.jsonl", issues)
    evaluation_rows = read_jsonl(shadow_root / "strategy_follow_evaluations.jsonl", issues)
    join_rows = read_jsonl(shadow_root / "candidate_mso_snapshot_joins.jsonl", issues)
    join_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in join_rows
        if row.get("row_key")
    }
    computed = build_candidate_mso_join_rows(
        candidate_rows,
        evaluation_rows,
        generated_at_utc=now_utc.isoformat(),
    )

    status_counts = Counter(str(row.get("join_status") or "UNKNOWN") for row in computed)
    comparison_counts = Counter(str(row.get("context_comparison_status") or "UNKNOWN") for row in computed)
    undocumented_missing: list[str] = []
    documented_missing: list[str] = []
    context_mismatch: list[str] = []
    stale_documented_missing: list[str] = []

    for row in computed:
        row_key = str(row.get("row_key") or "")
        candidate_id = str(row.get("candidate_id") or "")
        documented = join_by_row_key.get(row_key)
        documented_row = documented[1] if documented else None
        if row.get("join_status") == JOIN_MISSING:
            if documented_row and documented_row.get("join_status") == JOIN_MISSING:
                documented_missing.append(candidate_id)
            else:
                undocumented_missing.append(candidate_id)
                add_issue(
                    issues,
                    path=str(shadow_root / "candidate_mso_snapshot_joins.jsonl"),
                    severity="SERIOUS",
                    code="MSO_JOIN_MISSING",
                    message=(
                        f"candidate {candidate_id} has no exact symbol/time MSO row "
                        "and no append-only MSO_JOIN_MISSING documentation row"
                    ),
                )
            continue

        if documented_row and documented_row.get("join_status") == JOIN_MISSING:
            stale_documented_missing.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "candidate_mso_snapshot_joins.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="STALE_MSO_JOIN_MISSING_ROW",
                message=f"candidate {candidate_id} now has an exact MSO row but join backfill still says missing",
            )
        if row.get("context_mismatches"):
            context_mismatch.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "strategy_follow_candidates.jsonl"),
                severity="SERIOUS",
                code="MSO_CONTEXT_MISMATCH",
                message=f"candidate {candidate_id} differs from exact MSO snapshot: {row.get('context_mismatches')}",
            )

    if candidate_rows and not evaluation_rows:
        add_issue(
            issues,
            path=str(shadow_root / "strategy_follow_evaluations.jsonl"),
            severity="SERIOUS",
            code="MSO_EVALUATION_ROWS_ABSENT",
            message="candidate rows exist but no AI-independent MSO evaluation rows are available",
        )

    if undocumented_missing or context_mismatch or stale_documented_missing or (candidate_rows and not evaluation_rows):
        status = "ACTION_REQUIRED"
    elif documented_missing:
        status = "OK_WITH_DOCUMENTED_MSO_JOIN_LIMITATIONS"
    elif candidate_rows:
        status = "OK"
    else:
        status = "NO_CANDIDATE_ROWS"

    return {
        "status": status,
        "candidate_rows_checked": len(candidate_rows),
        "evaluation_rows_available": len(evaluation_rows),
        "join_backfill_rows_available": len(join_rows),
        "join_status_counts": dict(status_counts),
        "context_comparison_status_counts": dict(comparison_counts),
        "documented_missing_candidates": documented_missing,
        "undocumented_missing_candidates": undocumented_missing,
        "context_mismatch_candidates": context_mismatch,
        "stale_documented_missing_candidates": stale_documented_missing,
        "exact_joined_candidates": status_counts.get(JOINED_EXACT, 0),
    }


def audit_candidate_registry_contract(
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_rows = read_jsonl(shadow_root / "strategy_follow_candidates.jsonl", issues)
    audit_rows = read_jsonl(shadow_root / "candidate_registry_audit.jsonl", issues)
    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    computed = build_candidate_registry_audit_rows(
        candidate_rows,
        generated_at_utc=now_utc.isoformat(),
    )
    computed_status_counts = Counter(str(row.get("registry_audit_status") or "UNKNOWN") for row in computed)
    missing_audit: list[str] = []
    action_required: list[str] = []
    stale_audit: list[str] = []

    for row in computed:
        row_key = str(row.get("row_key") or "")
        candidate_id = str(row.get("candidate_id") or "")
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "candidate_registry_audit.jsonl"),
                severity="SERIOUS",
                code="CANDIDATE_REGISTRY_AUDIT_MISSING",
                message=f"candidate {candidate_id} has no append-only candidate registry audit row",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("registry_audit_status") == CANDIDATE_REGISTRY_ACTION_REQUIRED:
            action_required.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "candidate_registry_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="CANDIDATE_REGISTRY_AUDIT_ACTION_REQUIRED",
                message=(
                    f"candidate {candidate_id} registry audit requires action: "
                    f"{documented_row.get('action_required_codes')}"
                ),
            )
        if documented_row.get("action_required_codes") != row.get("action_required_codes"):
            stale_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "candidate_registry_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="CANDIDATE_REGISTRY_AUDIT_STALE",
                message=(
                    f"candidate {candidate_id} audit action codes are stale: "
                    f"stored={documented_row.get('action_required_codes')} current={row.get('action_required_codes')}"
                ),
            )

    if missing_audit or action_required or stale_audit:
        status = "ACTION_REQUIRED"
    elif candidate_rows:
        status = "OK_WITH_DOCUMENTED_REGISTRY_LIMITATIONS"
    else:
        status = "NO_CANDIDATE_ROWS"

    return {
        "status": status,
        "candidate_rows_checked": len(candidate_rows),
        "audit_rows_available": len(audit_rows),
        "computed_registry_audit_status_counts": dict(computed_status_counts),
        "missing_audit_candidates": missing_audit,
        "action_required_candidates": action_required,
        "stale_audit_candidates": stale_audit,
    }


def audit_candidate_path_contract(
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    path_rows = read_jsonl(shadow_root / "candidate_path_follow.jsonl", issues)
    ltf_rows = read_jsonl(shadow_root / "candidate_ltf_path_order.jsonl", issues)
    audit_rows = read_jsonl(shadow_root / "candidate_path_contract_audit.jsonl", issues)
    ltf_by_candidate: dict[str, dict[str, Any]] = {}
    for _, row in ltf_rows:
        cid = str(row.get("candidate_id") or "")
        if cid:
            ltf_by_candidate[cid] = row
    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    computed = build_candidate_path_contract_rows(
        path_rows,
        generated_at_utc=now_utc.isoformat(),
        ltf_rows_by_candidate=ltf_by_candidate,
    )
    computed_status_counts = Counter(str(row.get("path_contract_status") or "UNKNOWN") for row in computed)
    missing_audit: list[str] = []
    action_required: list[str] = []
    stale_audit: list[str] = []

    for row in computed:
        row_key = str(row.get("row_key") or "")
        candidate_id = str(row.get("candidate_id") or "")
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "candidate_path_contract_audit.jsonl"),
                severity="SERIOUS",
                code="CANDIDATE_PATH_CONTRACT_AUDIT_MISSING",
                message=f"candidate {candidate_id} has no append-only path contract audit row",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("path_contract_status") == PATH_CONTRACT_ACTION_REQUIRED:
            action_required.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "candidate_path_contract_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="CANDIDATE_PATH_CONTRACT_ACTION_REQUIRED",
                message=(
                    f"candidate {candidate_id} path contract requires action: "
                    f"{documented_row.get('action_required_codes')}"
                ),
            )
        if documented_row.get("action_required_codes") != row.get("action_required_codes"):
            stale_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "candidate_path_contract_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="CANDIDATE_PATH_CONTRACT_AUDIT_STALE",
                message=(
                    f"candidate {candidate_id} path action codes are stale: "
                    f"stored={documented_row.get('action_required_codes')} current={row.get('action_required_codes')}"
                ),
            )

    if missing_audit or action_required or stale_audit:
        status = "ACTION_REQUIRED"
    elif path_rows:
        status = "OK_WITH_DOCUMENTED_PATH_LIMITATIONS"
    else:
        status = "NO_PATH_ROWS"

    return {
        "status": status,
        "path_rows_checked": len(path_rows),
        "audit_rows_available": len(audit_rows),
        "computed_path_contract_status_counts": dict(computed_status_counts),
        "missing_audit_candidates": missing_audit,
        "action_required_candidates": action_required,
        "stale_audit_candidates": stale_audit,
    }


def audit_opportunity_lifecycle_contract(
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_rows = read_jsonl(shadow_root / "strategy_follow_candidates.jsonl", issues)
    path_rows = read_jsonl(shadow_root / "candidate_path_follow.jsonl", issues)
    ltf_rows = read_jsonl(shadow_root / "candidate_ltf_path_order.jsonl", issues)
    cluster_rows = read_jsonl(shadow_root / "live_candidate_opportunity_clusters.jsonl", issues)
    audit_rows = read_jsonl(shadow_root / "opportunity_lifecycle_audit.jsonl", issues)
    if not cluster_rows and not audit_rows:
        return {
            "status": "NO_CLUSTER_ROWS",
            "candidate_rows_checked": len(candidate_rows),
            "audit_rows_available": 0,
            "computed_lifecycle_audit_status_counts": {},
            "computed_lifecycle_state_counts": {},
            "missing_audit_candidates": [],
            "action_required_candidates": [],
            "stale_audit_candidates": [],
        }
    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    computed = build_opportunity_lifecycle_audit_rows(
        candidate_rows,
        generated_at_utc=now_utc.isoformat(),
        path_rows=path_rows,
        ltf_rows=ltf_rows,
        cluster_rows=cluster_rows,
    )
    computed_status_counts = Counter(str(row.get("opportunity_lifecycle_audit_status") or "UNKNOWN") for row in computed)
    lifecycle_state_counts = Counter(str(row.get("opportunity_lifecycle_state") or "UNKNOWN") for row in computed)
    missing_audit: list[str] = []
    action_required: list[str] = []
    stale_audit: list[str] = []

    for row in computed:
        row_key = str(row.get("row_key") or "")
        candidate_id = str(row.get("candidate_id") or "")
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "opportunity_lifecycle_audit.jsonl"),
                severity="SERIOUS",
                code="OPPORTUNITY_LIFECYCLE_AUDIT_MISSING",
                message=f"candidate {candidate_id} has no append-only opportunity lifecycle audit row",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("opportunity_lifecycle_audit_status") == OPPORTUNITY_LIFECYCLE_ACTION_REQUIRED:
            action_required.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "opportunity_lifecycle_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="OPPORTUNITY_LIFECYCLE_AUDIT_ACTION_REQUIRED",
                message=(
                    f"candidate {candidate_id} opportunity lifecycle audit requires action: "
                    f"{documented_row.get('action_required_codes')}"
                ),
            )
        if documented_row.get("action_required_codes") != row.get("action_required_codes"):
            stale_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "opportunity_lifecycle_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="OPPORTUNITY_LIFECYCLE_AUDIT_STALE",
                message=(
                    f"candidate {candidate_id} lifecycle action codes are stale: "
                    f"stored={documented_row.get('action_required_codes')} current={row.get('action_required_codes')}"
                ),
            )

    if missing_audit or action_required or stale_audit:
        status = "ACTION_REQUIRED"
    elif candidate_rows:
        status = "OK_WITH_DOCUMENTED_LIFECYCLE_LIMITATIONS"
    else:
        status = "NO_CANDIDATE_ROWS"

    return {
        "status": status,
        "candidate_rows_checked": len(candidate_rows),
        "audit_rows_available": len(audit_rows),
        "computed_lifecycle_audit_status_counts": dict(computed_status_counts),
        "computed_lifecycle_state_counts": dict(lifecycle_state_counts),
        "missing_audit_candidates": missing_audit,
        "action_required_candidates": action_required,
        "stale_audit_candidates": stale_audit,
    }


def audit_pending_limit_lifecycle_contract(
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_rows = read_jsonl(shadow_root / "strategy_follow_candidates.jsonl", issues)
    lifecycle_rows = read_jsonl(shadow_root / "pending_limit_lifecycle.jsonl", issues)
    join_rows = read_jsonl(shadow_root / "pending_limit_lifecycle_join_backfill.jsonl", issues)
    path_rows = read_jsonl(shadow_root / "candidate_path_follow.jsonl", issues)
    ltf_rows = read_jsonl(shadow_root / "candidate_ltf_path_order.jsonl", issues)
    account_rows = read_jsonl(shadow_root / "account_truth_reconciliation_status.jsonl", issues)
    audit_rows = read_jsonl(shadow_root / "pending_limit_lifecycle_audit.jsonl", issues)
    if not lifecycle_rows and not audit_rows:
        return {
            "status": "NO_PENDING_LIFECYCLE_ROWS",
            "lifecycle_rows_checked": 0,
            "audit_rows_available": 0,
            "computed_lifecycle_audit_status_counts": {},
            "computed_final_state_counts": {},
            "missing_audit_pending_intent_keys": [],
            "action_required_pending_intent_keys": [],
            "stale_audit_pending_intent_keys": [],
        }
    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    trade_records, _skipped = iter_trade_record_candidates(shadow_root.parent / DEFAULT_TRADE_RECORD_ROOT)
    latest_prefixes = sorted(
        {
            str(row.get("decision_time_utc") or "")[:10]
            for _, row in candidate_rows
            if len(str(row.get("decision_time_utc") or "")) >= 10
        }
    )
    latest_decision_date_prefix = latest_prefixes[-1] if latest_prefixes else None
    computed = build_pending_limit_lifecycle_audit_rows(
        candidate_rows,
        lifecycle_rows,
        generated_at_utc=now_utc.isoformat(),
        join_rows=join_rows,
        path_rows=path_rows,
        ltf_rows=ltf_rows,
        trade_record_candidates=trade_records,
        account_truth_rows=account_rows,
        persisted_pending_intents=read_persisted_pending_intents(shadow_root.parent / "knowledge_base" / "meta"),
        decision_date_prefix=latest_decision_date_prefix,
    )
    computed_status_counts = Counter(str(row.get("pending_limit_lifecycle_audit_status") or "UNKNOWN") for row in computed)
    final_state_counts = Counter(str(row.get("final_state") or "UNKNOWN") for row in computed)
    missing_audit: list[str] = []
    action_required: list[str] = []
    stale_audit: list[str] = []

    for row in computed:
        row_key = str(row.get("row_key") or "")
        pending_key = str(row.get("pending_intent_global_key") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing_audit.append(pending_key)
            add_issue(
                issues,
                path=str(shadow_root / "pending_limit_lifecycle_audit.jsonl"),
                severity="SERIOUS",
                code="PENDING_LIMIT_LIFECYCLE_AUDIT_MISSING",
                message=f"pending lifecycle key {pending_key} has no append-only LTO-005 audit row",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("pending_limit_lifecycle_audit_status") == PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED:
            action_required.append(pending_key)
            add_issue(
                issues,
                path=str(shadow_root / "pending_limit_lifecycle_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="PENDING_LIMIT_LIFECYCLE_AUDIT_ACTION_REQUIRED",
                message=(
                    f"pending lifecycle key {pending_key} requires action: "
                    f"{documented_row.get('action_required_codes')}"
                ),
            )
        if documented_row.get("action_required_codes") != row.get("action_required_codes"):
            stale_audit.append(pending_key)
            add_issue(
                issues,
                path=str(shadow_root / "pending_limit_lifecycle_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="PENDING_LIMIT_LIFECYCLE_AUDIT_STALE",
                message=(
                    f"pending lifecycle key {pending_key} audit action codes are stale: "
                    f"stored={documented_row.get('action_required_codes')} current={row.get('action_required_codes')}"
                ),
            )

    if missing_audit or action_required or stale_audit:
        status = "ACTION_REQUIRED"
    elif lifecycle_rows:
        status = "OK_WITH_DOCUMENTED_PENDING_LIFECYCLE_LIMITATIONS"
    else:
        status = "NO_PENDING_LIFECYCLE_ROWS"

    return {
        "status": status,
        "lifecycle_rows_checked": len(lifecycle_rows),
        "audit_rows_available": len(audit_rows),
        "computed_lifecycle_audit_status_counts": dict(computed_status_counts),
        "computed_final_state_counts": dict(final_state_counts),
        "missing_audit_pending_intent_keys": missing_audit,
        "action_required_pending_intent_keys": action_required,
        "stale_audit_pending_intent_keys": stale_audit,
    }


def audit_v2b_forward_pair_resolution_contract(
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    pair_rows = read_jsonl(shadow_root / "v2b_forward_pairs.jsonl", issues)
    resolution_rows = read_jsonl(shadow_root / "v2b_forward_pair_resolutions.jsonl", issues)
    mechanical_rows = read_jsonl(shadow_root / "live_mechanical_strategy_shadow_outcomes.jsonl", issues)
    path_rows = read_jsonl(shadow_root / "candidate_path_follow.jsonl", issues)
    ltf_rows = read_jsonl(shadow_root / "candidate_ltf_path_order.jsonl", issues)
    account_rows = read_jsonl(shadow_root / "account_truth_reconciliation_status.jsonl", issues)
    opportunity_rows = read_jsonl(shadow_root / "live_candidate_opportunity_clusters.jsonl", issues)
    pending_lifecycle_audit_rows = read_jsonl(shadow_root / "pending_limit_lifecycle_audit.jsonl", issues)
    audit_rows = read_jsonl(shadow_root / "v2b_forward_pair_resolution_audit.jsonl", issues)
    if not pair_rows and not audit_rows:
        return {
            "status": "NO_V2B_FORWARD_PAIR_ROWS",
            "v2b_pair_rows_checked": 0,
            "audit_rows_available": 0,
            "computed_v2b_audit_status_counts": {},
            "computed_label_lane_counts": {},
            "missing_audit_candidates": [],
            "action_required_candidates": [],
            "stale_audit_candidates": [],
        }

    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    computed = build_v2b_forward_pair_audit_rows(
        pair_rows,
        resolution_rows,
        mechanical_rows=mechanical_rows,
        path_rows=path_rows,
        ltf_rows=ltf_rows,
        account_truth_rows=account_rows,
        opportunity_rows=opportunity_rows,
        pending_lifecycle_audit_rows=pending_lifecycle_audit_rows,
        generated_at_utc=now_utc.isoformat(),
        decision_date_prefix=None,
    )
    computed_status_counts = Counter(str(row.get("v2b_forward_pair_resolution_audit_status") or "UNKNOWN") for row in computed)
    label_lane_counts = Counter(str(row.get("actual_synthetic_label_lane") or "UNKNOWN") for row in computed)
    missing_audit: list[str] = []
    action_required: list[str] = []
    stale_audit: list[str] = []

    for row in computed:
        row_key = str(row.get("row_key") or "")
        candidate_id = str(row.get("candidate_id") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "v2b_forward_pair_resolution_audit.jsonl"),
                severity="SERIOUS",
                code="V2B_FORWARD_PAIR_RESOLUTION_AUDIT_MISSING",
                message=f"candidate {candidate_id} has no append-only LTO-006 audit row for current source dependency signature",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("v2b_forward_pair_resolution_audit_status") == V2B_FORWARD_PAIR_ACTION_REQUIRED:
            action_required.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "v2b_forward_pair_resolution_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="V2B_FORWARD_PAIR_RESOLUTION_AUDIT_ACTION_REQUIRED",
                message=(
                    f"candidate {candidate_id} V2b resolution audit requires action: "
                    f"{documented_row.get('action_required_codes')}"
                ),
            )
        stale_fields = [
            field
            for field in (
                "action_required_codes",
                "actual_synthetic_label_lane",
                "r_counted_pair",
                "latest_resolution_row_key",
                "duplicate_aware_counting_status",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "v2b_forward_pair_resolution_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="V2B_FORWARD_PAIR_RESOLUTION_AUDIT_STALE",
                message=f"candidate {candidate_id} V2b audit fields are stale: {stale_fields}",
            )

    if missing_audit or action_required or stale_audit:
        status = "ACTION_REQUIRED"
    elif pair_rows:
        status = "OK_WITH_DOCUMENTED_V2B_LIMITATIONS"
    else:
        status = "NO_V2B_FORWARD_PAIR_ROWS"

    return {
        "status": status,
        "v2b_pair_rows_checked": len(pair_rows),
        "audit_rows_available": len(audit_rows),
        "computed_v2b_audit_status_counts": dict(computed_status_counts),
        "computed_label_lane_counts": dict(label_lane_counts),
        "computed_resolved_pair_count": sum(1 for row in computed if row.get("resolved_pair")),
        "computed_r_counted_pair_count": sum(1 for row in computed if row.get("r_counted_pair")),
        "missing_audit_candidates": missing_audit,
        "action_required_candidates": action_required,
        "stale_audit_candidates": stale_audit,
    }


def audit_prefill_delivery_path_contract(
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    prefill_rows = read_jsonl(shadow_root / "prefill_delivery_path.jsonl", issues)
    resolution_rows = read_jsonl(shadow_root / "prefill_delivery_path_resolutions.jsonl", issues)
    mechanical_rows = read_jsonl(shadow_root / "live_mechanical_strategy_shadow_outcomes.jsonl", issues)
    path_rows = read_jsonl(shadow_root / "candidate_path_follow.jsonl", issues)
    ltf_rows = read_jsonl(shadow_root / "candidate_ltf_path_order.jsonl", issues)
    pending_lifecycle_audit_rows = read_jsonl(shadow_root / "pending_limit_lifecycle_audit.jsonl", issues)
    opportunity_rows = read_jsonl(shadow_root / "live_candidate_opportunity_clusters.jsonl", issues)
    structural_rows = read_jsonl(shadow_root / "live_structural_strategy_metadata.jsonl", issues)
    audit_rows = read_jsonl(shadow_root / "prefill_delivery_path_audit.jsonl", issues)
    if not prefill_rows and not audit_rows:
        return {
            "status": "NO_PREFILL_DELIVERY_PATH_ROWS",
            "prefill_rows_checked": 0,
            "audit_rows_available": 0,
            "computed_prefill_audit_status_counts": {},
            "computed_source_capture_status_counts": {},
            "missing_audit_candidates": [],
            "action_required_candidates": [],
            "stale_audit_candidates": [],
        }

    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    computed = build_prefill_delivery_path_audit_rows(
        prefill_rows,
        resolution_rows,
        mechanical_rows=mechanical_rows,
        path_rows=path_rows,
        ltf_rows=ltf_rows,
        pending_lifecycle_audit_rows=pending_lifecycle_audit_rows,
        opportunity_rows=opportunity_rows,
        structural_rows=structural_rows,
        generated_at_utc=now_utc.isoformat(),
        decision_date_prefix=None,
    )
    computed_status_counts = Counter(str(row.get("prefill_delivery_path_audit_status") or "UNKNOWN") for row in computed)
    source_capture_counts = Counter(str(row.get("prefill_source_capture_status") or "UNKNOWN") for row in computed)
    missing_audit: list[str] = []
    action_required: list[str] = []
    stale_audit: list[str] = []

    for row in computed:
        row_key = str(row.get("row_key") or "")
        candidate_id = str(row.get("candidate_id") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "prefill_delivery_path_audit.jsonl"),
                severity="SERIOUS",
                code="PREFILL_DELIVERY_PATH_AUDIT_MISSING",
                message=f"candidate {candidate_id} has no append-only LTO-007 audit row for current source dependency signature",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("prefill_delivery_path_audit_status") == PREFILL_DELIVERY_PATH_ACTION_REQUIRED:
            action_required.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "prefill_delivery_path_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="PREFILL_DELIVERY_PATH_AUDIT_ACTION_REQUIRED",
                message=(
                    f"candidate {candidate_id} pre-fill delivery path audit requires action: "
                    f"{documented_row.get('action_required_codes')}"
                ),
            )
        stale_fields = [
            field
            for field in (
                "action_required_codes",
                "prefill_source_capture_status",
                "derived_prefill_path_status",
                "latest_resolution_row_key",
                "duplicate_aware_counting_status",
                "fill_state",
                "delivery_leg_state",
                "reversal_leg_state",
                "post_lock_reentry_eligibility",
                "cost_aware_min_r",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "prefill_delivery_path_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="PREFILL_DELIVERY_PATH_AUDIT_STALE",
                message=f"candidate {candidate_id} pre-fill audit fields are stale: {stale_fields}",
            )

    if missing_audit or action_required or stale_audit:
        status = "ACTION_REQUIRED"
    elif prefill_rows:
        status = "OK_WITH_DOCUMENTED_PREFILL_LIMITATIONS"
    else:
        status = "NO_PREFILL_DELIVERY_PATH_ROWS"

    return {
        "status": status,
        "prefill_rows_checked": len(prefill_rows),
        "audit_rows_available": len(audit_rows),
        "computed_prefill_audit_status_counts": dict(computed_status_counts),
        "computed_source_capture_status_counts": dict(source_capture_counts),
        "computed_core_source_captured_rows": sum(1 for row in computed if row.get("prefill_source_capture_status") == "PREFILL_DECISION_CORE_SOURCE_CAPTURED"),
        "computed_derived_path_rows": sum(1 for row in computed if str(row.get("derived_prefill_path_status") or "").startswith("DERIVED_FROM")),
        "missing_audit_candidates": missing_audit,
        "action_required_candidates": action_required,
        "stale_audit_candidates": stale_audit,
    }


def audit_fvg_ob_confluence_contract(
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    confluence_rows = read_jsonl(shadow_root / "fvg_ob_confluence.jsonl", issues)
    resolution_rows = read_jsonl(shadow_root / "fvg_ob_confluence_resolutions.jsonl", issues)
    mechanical_rows = read_jsonl(shadow_root / "live_mechanical_strategy_shadow_outcomes.jsonl", issues)
    path_rows = read_jsonl(shadow_root / "candidate_path_follow.jsonl", issues)
    ltf_rows = read_jsonl(shadow_root / "candidate_ltf_path_order.jsonl", issues)
    opportunity_rows = read_jsonl(shadow_root / "live_candidate_opportunity_clusters.jsonl", issues)
    structural_rows = read_jsonl(shadow_root / "live_structural_strategy_metadata.jsonl", issues)
    audit_rows = read_jsonl(shadow_root / "fvg_ob_confluence_audit.jsonl", issues)
    if not confluence_rows and not audit_rows:
        return {
            "status": "NO_FVG_OB_CONFLUENCE_ROWS",
            "confluence_rows_checked": 0,
            "audit_rows_available": 0,
            "computed_fvg_ob_audit_status_counts": {},
            "computed_source_capture_status_counts": {},
            "missing_audit_candidates": [],
            "action_required_candidates": [],
            "stale_audit_candidates": [],
        }

    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    computed = build_fvg_ob_confluence_audit_rows(
        confluence_rows,
        resolution_rows,
        mechanical_rows=mechanical_rows,
        path_rows=path_rows,
        ltf_rows=ltf_rows,
        opportunity_rows=opportunity_rows,
        structural_rows=structural_rows,
        generated_at_utc=now_utc.isoformat(),
        decision_date_prefix=None,
    )
    computed_status_counts = Counter(str(row.get("fvg_ob_confluence_audit_status") or "UNKNOWN") for row in computed)
    source_capture_counts = Counter(str(row.get("fvg_ob_source_capture_status") or "UNKNOWN") for row in computed)
    missing_audit: list[str] = []
    action_required: list[str] = []
    stale_audit: list[str] = []

    for row in computed:
        row_key = str(row.get("row_key") or "")
        candidate_id = str(row.get("candidate_id") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "fvg_ob_confluence_audit.jsonl"),
                severity="SERIOUS",
                code="FVG_OB_CONFLUENCE_AUDIT_MISSING",
                message=f"candidate {candidate_id} has no append-only LTO-008 audit row for current source dependency signature",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("fvg_ob_confluence_audit_status") == FVG_OB_CONFLUENCE_ACTION_REQUIRED:
            action_required.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "fvg_ob_confluence_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="FVG_OB_CONFLUENCE_AUDIT_ACTION_REQUIRED",
                message=(
                    f"candidate {candidate_id} FVG/OB confluence audit requires action: "
                    f"{documented_row.get('action_required_codes')}"
                ),
            )
        stale_fields = [
            field
            for field in (
                "action_required_codes",
                "fvg_ob_source_capture_status",
                "latest_resolution_row_key",
                "duplicate_aware_counting_status",
                "bucket_state",
                "geometry_state",
                "source_capture_statuses",
                "fvg_ob_confluence_outcome",
                "fvg_mid_edge_outcome",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "fvg_ob_confluence_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="FVG_OB_CONFLUENCE_AUDIT_STALE",
                message=f"candidate {candidate_id} FVG/OB confluence audit fields are stale: {stale_fields}",
            )

    if missing_audit or action_required or stale_audit:
        status = "ACTION_REQUIRED"
    elif confluence_rows:
        status = "OK_WITH_DOCUMENTED_FVG_OB_LIMITATIONS"
    else:
        status = "NO_FVG_OB_CONFLUENCE_ROWS"

    return {
        "status": status,
        "confluence_rows_checked": len(confluence_rows),
        "audit_rows_available": len(audit_rows),
        "computed_fvg_ob_audit_status_counts": dict(computed_status_counts),
        "computed_source_capture_status_counts": dict(source_capture_counts),
        "computed_exact_bounds_captured_rows": sum(
            1 for row in computed if row.get("fvg_ob_source_capture_status") in FVG_OB_EXACT_SOURCE_CAPTURE_STATUSES
        ),
        "missing_audit_candidates": missing_audit,
        "action_required_candidates": action_required,
        "stale_audit_candidates": stale_audit,
    }


def audit_context_control_contract(
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    context_rows = read_jsonl(shadow_root / "context_control_ledger.jsonl", issues)
    path_rows = read_jsonl(shadow_root / "candidate_path_follow.jsonl", issues)
    audit_rows = read_jsonl(shadow_root / "context_control_audit.jsonl", issues)
    if not context_rows and not audit_rows:
        return {
            "status": "NO_CONTEXT_CONTROL_ROWS",
            "context_rows_checked": 0,
            "audit_rows_available": 0,
            "computed_context_audit_status_counts": {},
            "computed_family_source_status_counts": {},
            "missing_audit_candidates": [],
            "action_required_candidates": [],
            "stale_audit_candidates": [],
        }

    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    computed = build_context_control_audit_rows(
        context_rows,
        path_rows,
        generated_at_utc=now_utc.isoformat(),
        decision_date_prefix=None,
    )
    computed_status_counts = Counter(str(row.get("context_control_audit_status") or "UNKNOWN") for row in computed)
    family_source_counts: Counter[str] = Counter()
    for row in computed:
        for family, status in (row.get("context_family_source_statuses") or {}).items():
            family_source_counts[f"{family}:{status}"] += 1

    missing_audit: list[str] = []
    action_required: list[str] = []
    stale_audit: list[str] = []
    for row in computed:
        row_key = str(row.get("row_key") or "")
        candidate_id = str(row.get("candidate_id") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "context_control_audit.jsonl"),
                severity="SERIOUS",
                code="CONTEXT_CONTROL_AUDIT_MISSING",
                message=f"candidate {candidate_id} has no append-only LTO-009 audit row for current source dependency signature",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("context_control_audit_status") == CONTEXT_CONTROL_ACTION_REQUIRED:
            action_required.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "context_control_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="CONTEXT_CONTROL_AUDIT_ACTION_REQUIRED",
                message=(
                    f"candidate {candidate_id} context/control audit requires action: "
                    f"{documented_row.get('action_required_codes')}"
                ),
            )
        stale_fields = [
            field
            for field in (
                "action_required_codes",
                "documented_limitation_codes",
                "direct_strategy_validation_status",
                "strategy_validation_status",
                "validation_scope",
                "context_family_source_statuses",
                "context_event_window_snapshot",
                "exploratory_outcome_context",
                "context_control_audit_status",
                "no_leak_status",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale_audit.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "context_control_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="CONTEXT_CONTROL_AUDIT_STALE",
                message=f"candidate {candidate_id} context/control audit fields are stale: {stale_fields}",
            )

    if missing_audit or action_required or stale_audit:
        status = "ACTION_REQUIRED"
    elif context_rows:
        status = "OK_WITH_DOCUMENTED_CONTEXT_CONTROL_LIMITATIONS"
    else:
        status = "NO_CONTEXT_CONTROL_ROWS"

    return {
        "status": status,
        "context_rows_checked": len(context_rows),
        "audit_rows_available": len(audit_rows),
        "computed_context_audit_status_counts": dict(computed_status_counts),
        "computed_family_source_status_counts": dict(family_source_counts),
        "missing_audit_candidates": missing_audit,
        "action_required_candidates": action_required,
        "stale_audit_candidates": stale_audit,
    }


def audit_broker_actual_r_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    account_rows = read_jsonl(shadow_root / "account_truth_reconciliation_status.jsonl", issues)
    slippage_rows = read_jsonl(shadow_root / "slippage.jsonl", issues)
    j46_rows = read_jsonl(shadow_root / "j46_j49_shadow_outcomes.jsonl", issues)
    mt5_deal_rows = read_mt5_deal_exports(root, issues)
    audit_rows = read_jsonl(shadow_root / "broker_actual_r_audit.jsonl", issues)
    if not account_rows and not j46_rows and not audit_rows:
        return {
            "status": "NO_BROKER_ACTUAL_R_SOURCE_ROWS",
            "source_rows_checked": 0,
            "audit_rows_available": 0,
            "computed_broker_actual_r_audit_status_counts": {},
            "computed_accounting_evidence_class_counts": {},
            "missing_audit_keys": [],
            "action_required_keys": [],
            "stale_audit_keys": [],
        }

    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    computed = build_broker_actual_r_audit_rows(
        account_rows,
        slippage_rows,
        j46_rows,
        mt5_deal_rows,
        generated_at_utc=now_utc.isoformat(),
        account_decision_date_prefix=None,
    )
    computed_status_counts = Counter(str(row.get("broker_actual_r_audit_status") or "UNKNOWN") for row in computed)
    evidence_counts = Counter(str(row.get("accounting_evidence_class") or "UNKNOWN") for row in computed)

    missing_audit: list[str] = []
    action_required: list[str] = []
    stale_audit: list[str] = []
    for row in computed:
        row_key = str(row.get("row_key") or "")
        row_id = str(row.get("candidate_id") or row.get("fill_id") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing_audit.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "broker_actual_r_audit.jsonl"),
                severity="SERIOUS",
                code="BROKER_ACTUAL_R_AUDIT_MISSING",
                message=f"{row_id} has no append-only LTO-015 audit row for current source dependency signature",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("broker_actual_r_audit_status") == BROKER_ACTUAL_R_ACTION_REQUIRED:
            action_required.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "broker_actual_r_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="BROKER_ACTUAL_R_AUDIT_ACTION_REQUIRED",
                message=f"{row_id} broker actual-R audit requires action: {documented_row.get('action_required_codes')}",
            )
        stale_fields = [
            field
            for field in (
                "action_required_codes",
                "documented_limitation_codes",
                "accounting_evidence_class",
                "actual_r_claim_allowed",
                "broker_actual_r",
                "account_truth_status",
                "truth_lane",
                "entry_slippage_status",
                "exit_accounting_status",
                "commission_status",
                "swap_status",
                "close_reason_status",
                "time_in_trade_status",
                "source_links",
                "broker_actual_r_audit_status",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale_audit.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "broker_actual_r_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="BROKER_ACTUAL_R_AUDIT_STALE",
                message=f"{row_id} broker actual-R audit fields are stale: {stale_fields}",
            )

    if missing_audit or action_required or stale_audit:
        status = "ACTION_REQUIRED"
    elif account_rows or j46_rows:
        status = "OK_WITH_DOCUMENTED_ACCOUNTING_LIMITATIONS"
    else:
        status = "NO_BROKER_ACTUAL_R_SOURCE_ROWS"

    return {
        "status": status,
        "source_rows_checked": len(account_rows) + len(j46_rows),
        "mt5_deal_rows_available": len(mt5_deal_rows),
        "audit_rows_available": len(audit_rows),
        "computed_broker_actual_r_audit_status_counts": dict(computed_status_counts),
        "computed_accounting_evidence_class_counts": dict(evidence_counts),
        "computed_broker_actual_r_claim_allowed_rows": sum(1 for row in computed if row.get("actual_r_claim_allowed") is True),
        "missing_audit_keys": missing_audit,
        "action_required_keys": action_required,
        "stale_audit_keys": stale_audit,
    }


def audit_j46_j49_exit_comparator_contract(
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    j46_rows = read_jsonl(shadow_root / "j46_j49_shadow_outcomes.jsonl", issues)
    broker_rows = read_jsonl(shadow_root / "broker_actual_r_audit.jsonl", issues)
    candidate_rows = read_jsonl(shadow_root / "strategy_follow_candidates.jsonl", issues)
    path_rows = read_jsonl(shadow_root / "candidate_path_follow.jsonl", issues)
    audit_rows = read_jsonl(shadow_root / "j46_j49_exit_comparator_audit.jsonl", issues)
    if not j46_rows and not candidate_rows and not audit_rows:
        return {
            "status": "NO_J46_J49_COMPARATOR_SOURCE_ROWS",
            "source_rows_checked": 0,
            "audit_rows_available": 0,
            "computed_status_counts": {},
            "computed_ml_label_eligibility_counts": {},
            "missing_audit_keys": [],
            "action_required_keys": [],
            "stale_audit_keys": [],
        }

    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    computed = build_j46_j49_exit_comparator_audit_rows(
        j46_rows,
        broker_rows=broker_rows,
        candidate_rows=candidate_rows,
        path_rows=path_rows,
        generated_at_utc=now_utc.isoformat(),
    )
    status_counts = Counter(str(row.get("j46_j49_exit_comparator_status") or "UNKNOWN") for row in computed)
    ml_label_counts = Counter(str(row.get("ml_label_eligibility") or "UNKNOWN") for row in computed)
    missing_audit: list[str] = []
    action_required: list[str] = []
    stale_audit: list[str] = []
    for row in computed:
        row_key = str(row.get("row_key") or "")
        row_id = str(row.get("candidate_id") or row.get("fill_id") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing_audit.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "j46_j49_exit_comparator_audit.jsonl"),
                severity="SERIOUS",
                code="J46_J49_EXIT_COMPARATOR_AUDIT_MISSING",
                message=f"{row_id} has no append-only LTO-016 comparator audit row for current source dependency signature",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("j46_j49_exit_comparator_status") == J46_J49_EXIT_COMPARATOR_ACTION_REQUIRED or documented_row.get("action_required_codes"):
            action_required.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "j46_j49_exit_comparator_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="J46_J49_EXIT_COMPARATOR_AUDIT_ACTION_REQUIRED",
                message=f"{row_id} J46/J49 comparator audit requires action: {documented_row.get('action_required_codes')}",
            )
        stale_fields = [
            field
            for field in (
                "row_type",
                "j46_j49_exit_comparator_status",
                "actual_r_claim_allowed",
                "broker_actual_r_claim_allowed",
                "broker_actual_r",
                "broker_actual_r_delta_vs_j46",
                "broker_actual_r_audit_row_key",
                "broker_actual_r_evidence_class",
                "broker_actual_r_truth_lane",
                "path_context_status",
                "path_label",
                "touched_entry",
                "hit_tp1",
                "hit_sl",
                "path_ambiguity_status",
                "j46_actual_close_realized_r",
                "hypothetical_old_r",
                "delta_r",
                "shadow_better",
                "documented_limitation_codes",
                "action_required_codes",
                "ml_feature_role",
                "ml_label_eligibility",
                "evidence_class",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale_audit.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "j46_j49_exit_comparator_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="J46_J49_EXIT_COMPARATOR_AUDIT_STALE",
                message=f"{row_id} J46/J49 comparator audit fields are stale: {stale_fields}",
            )

    if missing_audit or action_required or stale_audit:
        status = "ACTION_REQUIRED"
    elif computed:
        status = "OK_WITH_DOCUMENTED_J46_J49_EXIT_COMPARATOR_AUDIT"
    else:
        status = "NO_J46_J49_COMPARATOR_SOURCE_ROWS"
    return {
        "status": status,
        "source_rows_checked": len(j46_rows) + len(candidate_rows),
        "j46_outcome_rows_checked": len(j46_rows),
        "candidate_rows_checked": len(candidate_rows),
        "path_rows_available": len(path_rows),
        "audit_rows_available": len(audit_rows),
        "computed_status_counts": dict(status_counts),
        "computed_ml_label_eligibility_counts": dict(ml_label_counts),
        "computed_actual_r_claim_allowed_rows": sum(1 for row in computed if row.get("actual_r_claim_allowed") is True),
        "missing_audit_keys": missing_audit,
        "action_required_keys": action_required,
        "stale_audit_keys": stale_audit,
    }


def _read_yaml_object(path: Path, issues: list[dict[str, Any]]) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml

        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        add_issue(
            issues,
            path=str(path),
            severity="SERIOUS",
            code="YAML_READ_FAILED",
            message=str(exc),
        )
        return {}
    return payload if isinstance(payload, dict) else {}


def audit_s79_side_aware_context_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_rows = read_jsonl(shadow_root / "strategy_follow_candidates.jsonl", issues)
    broker_rows = read_jsonl(shadow_root / "broker_actual_r_audit.jsonl", issues)
    j46_rows = read_jsonl(shadow_root / "j46_j49_shadow_outcomes.jsonl", issues)
    audit_rows = read_jsonl(shadow_root / "s79_side_aware_risk_context.jsonl", issues)
    if not candidate_rows and not broker_rows and not audit_rows:
        return {
            "status": "NO_S79_SIDE_AWARE_SOURCE_ROWS",
            "source_rows_checked": 0,
            "audit_rows_available": 0,
            "computed_status_counts": {},
            "missing_audit_keys": [],
            "action_required_keys": [],
            "stale_audit_keys": [],
        }

    sprt_state = _read_json_object(root / "pipeline_state" / "side_aware_sprt_state.json", issues) or {}
    computed = build_s79_side_aware_context_rows(
        candidate_rows,
        broker_rows=broker_rows,
        j46_rows=j46_rows,
        config=_read_yaml_object(root / "config" / "agent_config.yaml", issues),
        profile=_read_yaml_object(root / "config" / "profiles" / "redacted_account.yaml", issues),
        sprt_state=sprt_state,
        generated_at_utc=now_utc.isoformat(),
    )
    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    status_counts = Counter(str(row.get("s79_side_aware_context_status") or "UNKNOWN") for row in computed)
    missing: list[str] = []
    action_required: list[str] = []
    stale: list[str] = []
    for row in computed:
        row_key = str(row.get("row_key") or "")
        row_id = str(row.get("candidate_id") or row.get("fill_id") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "s79_side_aware_risk_context.jsonl"),
                severity="SERIOUS",
                code="S79_SIDE_AWARE_CONTEXT_MISSING",
                message=f"{row_id} has no append-only LTO-017 risk-context row for current source dependency signature",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("s79_side_aware_context_status") == S79_SIDE_AWARE_ACTION_REQUIRED or documented_row.get("action_required_codes"):
            action_required.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "s79_side_aware_risk_context.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="S79_SIDE_AWARE_CONTEXT_ACTION_REQUIRED",
                message=f"{row_id} S79/side-aware context requires action: {documented_row.get('action_required_codes')}",
            )
        stale_fields = [
            field
            for field in (
                "row_type",
                "s79_side_aware_context_status",
                "risk_context",
                "s79_strategy_snapshot_present",
                "account_history_join_status",
                "actual_r_claim_allowed",
                "broker_actual_r",
                "broker_actual_r_audit_row_key",
                "broker_actual_r_evidence_class",
                "broker_actual_r_truth_lane",
                "documented_limitation_codes",
                "action_required_codes",
                "ml_label_eligibility",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "s79_side_aware_risk_context.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="S79_SIDE_AWARE_CONTEXT_STALE",
                message=f"{row_id} S79/side-aware context fields are stale: {stale_fields}",
            )

    if missing or action_required or stale:
        status = "ACTION_REQUIRED"
    elif computed:
        status = "OK_WITH_DOCUMENTED_S79_SIDE_AWARE_CONTEXT"
    else:
        status = "NO_S79_SIDE_AWARE_SOURCE_ROWS"
    return {
        "status": status,
        "source_rows_checked": len(candidate_rows) + len(broker_rows),
        "candidate_rows_checked": len(candidate_rows),
        "broker_rows_checked": len(broker_rows),
        "audit_rows_available": len(audit_rows),
        "computed_status_counts": dict(status_counts),
        "computed_actual_r_claim_allowed_rows": sum(1 for row in computed if row.get("actual_r_claim_allowed") is True),
        "missing_audit_keys": missing,
        "action_required_keys": action_required,
        "stale_audit_keys": stale,
    }


def _read_csv_rows(path: Path, issues: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return []
    rows: list[tuple[int, dict[str, Any]]] = []
    try:
        with path.open("r", encoding="utf-8", newline="", errors="replace") as handle:
            reader = csv.DictReader(handle)
            for line_no, row in enumerate(reader, start=2):
                rows.append((line_no, dict(row)))
    except OSError as exc:
        add_issue(
            issues,
            path=str(path),
            severity="SERIOUS",
            code="CSV_READ_FAILED",
            message=str(exc),
        )
    return rows


def _latest_monthly_decay_report_metadata(path: Path, now_utc: datetime) -> dict[str, Any]:
    if not path.exists():
        return {
            "status": "MONTHLY_DECAY_REPORT_NOT_FOUND",
            "path": None,
            "mtime_utc": None,
            "age_days": None,
        }
    reports = sorted(path.glob("????-??_report*.md"), key=lambda item: item.stat().st_mtime if item.exists() else 0.0)
    if not reports:
        return {
            "status": "MONTHLY_DECAY_REPORT_NOT_FOUND",
            "path": None,
            "mtime_utc": None,
            "age_days": None,
        }
    latest = reports[-1]
    mtime = datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc)
    age_days = round((now_utc - mtime).total_seconds() / 86400, 3)
    try:
        report_path = str(latest.relative_to(ROOT))
    except ValueError:
        report_path = str(latest)
    return {
        "status": "MONTHLY_DECAY_REPORT_PRESENT" if age_days <= 35 else "MONTHLY_DECAY_REPORT_STALE_GT_35D",
        "path": report_path,
        "mtime_utc": mtime.isoformat(),
        "age_days": age_days,
    }


def audit_regime_decay_outcome_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_rows = read_jsonl(shadow_root / "strategy_follow_candidates.jsonl", issues)
    broker_rows = read_jsonl(shadow_root / "broker_actual_r_audit.jsonl", issues)
    path_rows = read_jsonl(shadow_root / "candidate_path_follow.jsonl", issues)
    regime_rows = read_jsonl(shadow_root / "regime_classifications.jsonl", issues)
    ob_rows = _read_csv_rows(shadow_root / "ob_continuation_daily.csv", issues)
    audit_rows = read_jsonl(shadow_root / "regime_decay_outcome_join.jsonl", issues)
    if not candidate_rows and not broker_rows and not audit_rows:
        return {
            "status": "NO_REGIME_DECAY_SOURCE_ROWS",
            "source_rows_checked": 0,
            "audit_rows_available": 0,
            "computed_status_counts": {},
            "missing_audit_keys": [],
            "action_required_keys": [],
            "stale_audit_keys": [],
        }

    computed = build_regime_decay_outcome_rows(
        candidate_rows,
        broker_rows=broker_rows,
        path_rows=path_rows,
        regime_rows=regime_rows,
        ob_rows=ob_rows,
        monthly_decay_report=_latest_monthly_decay_report_metadata(root / "research" / "monthly_decay_monitor", now_utc),
        generated_at_utc=now_utc.isoformat(),
    )
    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    status_counts = Counter(str(row.get("regime_decay_context_status") or "UNKNOWN") for row in computed)
    missing: list[str] = []
    action_required: list[str] = []
    stale: list[str] = []
    for row in computed:
        row_key = str(row.get("row_key") or "")
        row_id = str(row.get("candidate_id") or row.get("fill_id") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "regime_decay_outcome_join.jsonl"),
                severity="SERIOUS",
                code="REGIME_DECAY_CONTEXT_MISSING",
                message=f"{row_id} has no append-only LTO-018 regime/decay row for current source dependency signature",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("regime_decay_context_status") == REGIME_DECAY_ACTION_REQUIRED or documented_row.get("action_required_codes"):
            action_required.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "regime_decay_outcome_join.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="REGIME_DECAY_CONTEXT_ACTION_REQUIRED",
                message=f"{row_id} regime/decay context requires action: {documented_row.get('action_required_codes')}",
            )
        stale_fields = [
            field
            for field in (
                "row_type",
                "regime_decay_context_status",
                "path_context_status",
                "account_history_join_status",
                "actual_r_claim_allowed",
                "broker_actual_r",
                "broker_actual_r_audit_row_key",
                "broker_actual_r_evidence_class",
                "broker_actual_r_truth_lane",
                "regime_context",
                "ob_continuation_context",
                "monthly_decay_report_context",
                "documented_limitation_codes",
                "action_required_codes",
                "ml_label_eligibility",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "regime_decay_outcome_join.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="REGIME_DECAY_CONTEXT_STALE",
                message=f"{row_id} regime/decay context fields are stale: {stale_fields}",
            )

    if missing or action_required or stale:
        status = "ACTION_REQUIRED"
    elif computed:
        status = "OK_WITH_DOCUMENTED_REGIME_DECAY_CONTEXT"
    else:
        status = "NO_REGIME_DECAY_SOURCE_ROWS"
    return {
        "status": status,
        "source_rows_checked": len(candidate_rows) + len(broker_rows),
        "candidate_rows_checked": len(candidate_rows),
        "broker_rows_checked": len(broker_rows),
        "regime_rows_checked": len(regime_rows),
        "ob_continuation_rows_checked": len(ob_rows),
        "audit_rows_available": len(audit_rows),
        "computed_status_counts": dict(status_counts),
        "computed_actual_r_claim_allowed_rows": sum(1 for row in computed if row.get("actual_r_claim_allowed") is True),
        "missing_audit_keys": missing,
        "action_required_keys": action_required,
        "stale_audit_keys": stale,
    }


def audit_decision_layer_diagnostics_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_rows = read_jsonl(shadow_root / "strategy_follow_candidates.jsonl", issues)
    candidate_feature_rows = read_jsonl(shadow_root / "candidate_features_log.jsonl", issues)
    d1_bias_rows = read_jsonl(shadow_root / "d1_bias_lag.jsonl", issues)
    direction_rows = read_jsonl(shadow_root / "direction_emission_xau_audit.jsonl", issues)
    sl_rows = read_jsonl(shadow_root / "sl_beyond_ob_decisions.jsonl", issues)
    touch_rows = read_jsonl(shadow_root / "touch_count_gate_decisions.jsonl", issues)
    cross_corr_rows = read_jsonl(shadow_root / "cross_instrument_correlation_decisions.jsonl", issues)
    audit_rows = read_jsonl(shadow_root / "decision_layer_diagnostics_join.jsonl", issues)
    if not candidate_rows and not audit_rows:
        return {
            "status": "NO_DECISION_DIAGNOSTICS_SOURCE_ROWS",
            "source_rows_checked": 0,
            "audit_rows_available": 0,
            "computed_status_counts": {},
            "missing_audit_keys": [],
            "action_required_keys": [],
            "stale_audit_keys": [],
        }

    computed = build_decision_layer_diagnostics_rows(
        candidate_rows,
        candidate_feature_rows=candidate_feature_rows,
        d1_bias_rows=d1_bias_rows,
        direction_emission_rows=direction_rows,
        sl_beyond_ob_rows=sl_rows,
        touch_count_rows=touch_rows,
        cross_instrument_correlation_rows=cross_corr_rows,
        generated_at_utc=now_utc.isoformat(),
    )
    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    status_counts = Counter(str(row.get("decision_diagnostics_status") or "UNKNOWN") for row in computed)
    missing: list[str] = []
    action_required: list[str] = []
    stale: list[str] = []
    for row in computed:
        row_key = str(row.get("row_key") or "")
        row_id = str(row.get("candidate_id") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "decision_layer_diagnostics_join.jsonl"),
                severity="SERIOUS",
                code="DECISION_DIAGNOSTICS_CONTEXT_MISSING",
                message=f"{row_id} has no append-only LTO-019 decision diagnostics row for current source dependency signature",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("decision_diagnostics_status") == DECISION_DIAGNOSTICS_ACTION_REQUIRED or documented_row.get("action_required_codes"):
            action_required.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "decision_layer_diagnostics_join.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="DECISION_DIAGNOSTICS_CONTEXT_ACTION_REQUIRED",
                message=f"{row_id} decision diagnostics require action: {documented_row.get('action_required_codes')}",
            )
        stale_fields = [
            field
            for field in (
                "decision_diagnostics_status",
                "ai_decision",
                "ai_direction",
                "trade_parameter_direction",
                "verification_passed",
                "verification_blocked_by",
                "verification_context",
                "candidate_features_join_status",
                "d1_bias_lag_join_status",
                "direction_emission_join_status",
                "sl_beyond_ob_join_status",
                "touch_count_join_status",
                "cross_instrument_correlation_join_status",
                "diagnostic_join_statuses",
                "candidate_features_context",
                "d1_bias_lag_context",
                "direction_emission_context",
                "sl_beyond_ob_context",
                "touch_count_context",
                "cross_instrument_correlation_context",
                "mismatch_codes",
                "documented_limitation_codes",
                "action_required_codes",
                "ml_label_eligibility",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "decision_layer_diagnostics_join.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="DECISION_DIAGNOSTICS_CONTEXT_STALE",
                message=f"{row_id} decision diagnostics fields are stale: {stale_fields}",
            )

    if missing or action_required or stale:
        status = "ACTION_REQUIRED"
    elif computed:
        status = "OK_WITH_DOCUMENTED_DECISION_DIAGNOSTICS_CONTEXT"
    else:
        status = "NO_DECISION_DIAGNOSTICS_SOURCE_ROWS"
    return {
        "status": status,
        "source_rows_checked": len(candidate_rows),
        "candidate_rows_checked": len(candidate_rows),
        "candidate_feature_rows_checked": len(candidate_feature_rows),
        "d1_bias_rows_checked": len(d1_bias_rows),
        "direction_emission_rows_checked": len(direction_rows),
        "sl_beyond_ob_rows_checked": len(sl_rows),
        "touch_count_rows_checked": len(touch_rows),
        "cross_instrument_correlation_rows_checked": len(cross_corr_rows),
        "audit_rows_available": len(audit_rows),
        "computed_status_counts": dict(status_counts),
        "missing_audit_keys": missing,
        "action_required_keys": action_required,
        "stale_audit_keys": stale,
    }


def audit_mechanical_context_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_rows = read_jsonl(shadow_root / "strategy_follow_candidates.jsonl", issues)
    path_rows = read_jsonl(shadow_root / "candidate_path_follow.jsonl", issues)
    broker_rows = read_jsonl(shadow_root / "broker_actual_r_audit.jsonl", issues)
    dumb_rows = read_jsonl(shadow_root / "dumb_baseline_hypotheticals.jsonl", issues)
    proximity_rows = read_jsonl(shadow_root / "proximity_shadow_log.jsonl", issues)
    liquidity_rows = read_jsonl(shadow_root / "liquidity_distance_log.jsonl", issues)
    displacement_rows = read_jsonl(shadow_root / "displacement_events.jsonl", issues)
    structure_rows = read_jsonl(shadow_root / "structure_detector_divergences.jsonl", issues)
    audit_rows = read_jsonl(shadow_root / "mechanical_context_diagnostics_join.jsonl", issues)
    if not candidate_rows and not audit_rows:
        return {
            "status": "NO_MECHANICAL_CONTEXT_SOURCE_ROWS",
            "source_rows_checked": 0,
            "audit_rows_available": 0,
            "computed_status_counts": {},
            "missing_audit_keys": [],
            "action_required_keys": [],
            "stale_audit_keys": [],
        }

    computed = build_mechanical_context_rows(
        candidate_rows,
        path_rows=path_rows,
        broker_rows=broker_rows,
        dumb_rows=dumb_rows,
        proximity_rows=proximity_rows,
        liquidity_rows=liquidity_rows,
        displacement_rows=displacement_rows,
        structure_rows=structure_rows,
        generated_at_utc=now_utc.isoformat(),
    )
    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    status_counts = Counter(str(row.get("mechanical_context_status") or "UNKNOWN") for row in computed)
    missing: list[str] = []
    action_required: list[str] = []
    stale: list[str] = []
    for row in computed:
        row_key = str(row.get("row_key") or "")
        row_id = str(row.get("candidate_id") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "mechanical_context_diagnostics_join.jsonl"),
                severity="SERIOUS",
                code="MECHANICAL_CONTEXT_MISSING",
                message=f"{row_id} has no append-only LTO-020 mechanical context row for current source dependency signature",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("mechanical_context_status") == MECHANICAL_CONTEXT_ACTION_REQUIRED or documented_row.get("action_required_codes"):
            action_required.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "mechanical_context_diagnostics_join.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="MECHANICAL_CONTEXT_ACTION_REQUIRED",
                message=f"{row_id} mechanical context requires action: {documented_row.get('action_required_codes')}",
            )
        stale_fields = [
            field
            for field in (
                "mechanical_context_status",
                "path_context",
                "account_history_join_status",
                "actual_r_claim_allowed",
                "broker_actual_r",
                "broker_actual_r_audit_row_key",
                "mechanical_context_join_statuses",
                "dumb_baseline_context",
                "proximity_context",
                "liquidity_distance_context",
                "displacement_context",
                "structure_divergence_context",
                "mismatch_codes",
                "documented_limitation_codes",
                "action_required_codes",
                "ml_label_eligibility",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "mechanical_context_diagnostics_join.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="MECHANICAL_CONTEXT_STALE",
                message=f"{row_id} mechanical context fields are stale: {stale_fields}",
            )

    if missing or action_required or stale:
        status = "ACTION_REQUIRED"
    elif computed:
        status = "OK_WITH_DOCUMENTED_MECHANICAL_CONTEXT"
    else:
        status = "NO_MECHANICAL_CONTEXT_SOURCE_ROWS"
    return {
        "status": status,
        "source_rows_checked": len(candidate_rows),
        "candidate_rows_checked": len(candidate_rows),
        "path_rows_checked": len(path_rows),
        "broker_rows_checked": len(broker_rows),
        "dumb_baseline_rows_checked": len(dumb_rows),
        "proximity_rows_checked": len(proximity_rows),
        "liquidity_rows_checked": len(liquidity_rows),
        "displacement_rows_checked": len(displacement_rows),
        "structure_rows_checked": len(structure_rows),
        "audit_rows_available": len(audit_rows),
        "computed_status_counts": dict(status_counts),
        "missing_audit_keys": missing,
        "action_required_keys": action_required,
        "stale_audit_keys": stale,
    }


def _normalise_repo_relative_path_text(value: Any, root: Path) -> Any:
    if value in (None, ""):
        return value
    try:
        path = Path(str(value))
        resolved = path.resolve(strict=False)
        root_resolved = root.resolve(strict=False)
        return resolved.relative_to(root_resolved).as_posix()
    except (OSError, ValueError):
        return value


def _normalise_ml_prediction_for_compare(value: Any, root: Path) -> Any:
    if not isinstance(value, dict):
        return value
    normalised = dict(value)
    normalised["model_artifact_path"] = _normalise_repo_relative_path_text(
        normalised.get("model_artifact_path"),
        root,
    )
    return normalised


def audit_ml_shadow_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_rows = read_jsonl(shadow_root / "strategy_follow_candidates.jsonl", issues)
    log_path = shadow_root / "ml_shadow_predictions.jsonl"
    lto023_report = root / "research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.md"
    audit_rows = read_jsonl(log_path, issues)
    if not audit_rows and not lto023_report.exists():
        return {
            "status": "ML_SHADOW_NOT_IMPLEMENTED_OR_NO_LOG_YET",
            "candidate_rows_checked": len(candidate_rows),
            "audit_rows_available": 0,
            "computed_status_counts": {},
            "missing_audit_keys": [],
            "action_required_keys": [],
            "stale_audit_keys": [],
        }
    if not candidate_rows and not audit_rows:
        return {
            "status": "NO_ML_SHADOW_SOURCE_ROWS",
            "candidate_rows_checked": 0,
            "audit_rows_available": 0,
            "computed_status_counts": {},
            "missing_audit_keys": [],
            "action_required_keys": [],
            "stale_audit_keys": [],
        }

    computed = build_ml_shadow_rows(
        candidate_rows,
        mso_rows=read_jsonl(shadow_root / "candidate_mso_snapshot_joins.jsonl", issues),
        account_truth_rows=read_jsonl(shadow_root / "account_truth_reconciliation_status.jsonl", issues),
        broker_rows=read_jsonl(shadow_root / "broker_actual_r_audit.jsonl", issues),
        j46_rows=read_jsonl(shadow_root / "j46_j49_exit_comparator_audit.jsonl", issues),
        s79_rows=read_jsonl(shadow_root / "s79_side_aware_risk_context.jsonl", issues),
        regime_rows=read_jsonl(shadow_root / "regime_decay_outcome_join.jsonl", issues),
        decision_rows=read_jsonl(shadow_root / "decision_layer_diagnostics_join.jsonl", issues),
        mechanical_rows=read_jsonl(shadow_root / "mechanical_context_diagnostics_join.jsonl", issues),
        databento_trigger_rows=read_jsonl(shadow_root / "databento_live_trigger_decisions.jsonl", issues),
        sierra_proxy_rows=read_jsonl(shadow_root / "sierra_proxy_registry_status.jsonl", issues),
        sierra_depth_rows=read_jsonl(shadow_root / "sierra_depth_feature_snapshots.jsonl", issues),
        orderflow_status_rows=read_jsonl(shadow_root / "orderflow_primitives_status.jsonl", issues),
        sierra_status_rows=read_jsonl(shadow_root / "sierra_depth_enrichment_status.jsonl", issues),
        model_artifact_path=root / ML_SHADOW_DEFAULT_MODEL_REGISTRY_PATH,
        generated_at_utc=now_utc.isoformat(),
    )
    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    status_counts = Counter(str(row.get("ml_shadow_status") or "UNKNOWN") for row in computed)
    missing: list[str] = []
    action_required: list[str] = []
    stale: list[str] = []
    for row in computed:
        row_key = str(row.get("row_key") or "")
        row_id = str(row.get("candidate_id") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "ml_shadow_predictions.jsonl"),
                severity="SERIOUS",
                code="ML_SHADOW_ROW_MISSING",
                message=f"{row_id} has no append-only LTO-023 ML shadow row for current source dependency signature",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("ml_shadow_status") == ML_SHADOW_ACTION_REQUIRED or documented_row.get("action_required_codes"):
            action_required.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "ml_shadow_predictions.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="ML_SHADOW_ACTION_REQUIRED",
                message=f"{row_id} ML shadow row requires action: {documented_row.get('action_required_codes')}",
            )
        stale_fields = [
            field
            for field in (
                "ml_shadow_status",
                "prediction",
                "feature_bundle_status",
                "feature_availability",
                "source_freshness",
                "feature_groups",
                "feature_vector",
                "forbidden_feature_keys",
                "label_contract",
                "ml_label_eligibility",
                "documented_limitation_codes",
                "action_required_codes",
            )
            if (
                _normalise_ml_prediction_for_compare(documented_row.get(field), root)
                if field == "prediction"
                else documented_row.get(field)
            )
            != (
                _normalise_ml_prediction_for_compare(row.get(field), root)
                if field == "prediction"
                else row.get(field)
            )
        ]
        if stale_fields:
            stale.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "ml_shadow_predictions.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="ML_SHADOW_ROW_STALE",
                message=f"{row_id} ML shadow fields are stale: {stale_fields}",
            )

    if missing or action_required or stale:
        status = "ACTION_REQUIRED"
    elif computed:
        status = "OK_WITH_DOCUMENTED_K55_ML_SHADOW"
    else:
        status = "NO_ML_SHADOW_SOURCE_ROWS"
    return {
        "status": status,
        "candidate_rows_checked": len(candidate_rows),
        "audit_rows_available": len(audit_rows),
        "computed_status_counts": dict(status_counts),
        "missing_audit_keys": missing,
        "action_required_keys": action_required,
        "stale_audit_keys": stale,
    }


def audit_v2_structural_selector_readiness_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    log_path = shadow_root / "v2_structural_selector_readiness.jsonl"
    lto027_report = root / "research/program_control/LTO027_V2_STRUCTURAL_SELECTOR_READINESS_2026-05-05.md"
    documented_rows = read_jsonl(log_path, issues)
    if not documented_rows and not lto027_report.exists():
        return {
            "status": "V2_STRUCTURAL_SELECTOR_READINESS_NOT_IMPLEMENTED_OR_NO_LOG_YET",
            "audit_rows_available": 0,
            "computed_status": "NOT_RUN",
            "missing_status": False,
            "action_required": False,
            "stale_fields": [],
        }

    computed = build_v2_structural_selector_status_row(
        root=root,
        v2b_audit_rows=read_jsonl(shadow_root / "v2b_forward_pair_resolution_audit.jsonl", issues),
        v2b_pair_rows=read_jsonl(shadow_root / "v2b_forward_pairs.jsonl", issues),
        pending_lifecycle_rows=read_jsonl(shadow_root / "pending_limit_lifecycle_audit.jsonl", issues),
        broker_actual_rows=read_jsonl(shadow_root / "broker_actual_r_audit.jsonl", issues),
        generated_at_utc=now_utc.isoformat(),
    )
    row_key = str(computed.get("row_key") or "")
    documented = {
        str(row.get("row_key") or ""): (line_no, row)
        for line_no, row in documented_rows
        if row.get("row_key")
    }.get(row_key)
    missing = documented is None
    action_required = False
    stale_fields: list[str] = []

    if missing:
        add_issue(
            issues,
            path=str(log_path),
            severity="SERIOUS",
            code="V2_STRUCTURAL_SELECTOR_READINESS_ROW_MISSING",
            message="current LTO-027 V2 structural selector readiness row is missing",
        )
    else:
        line_no, documented_row = documented
        if (
            documented_row.get("readiness_status") == V2_STRUCTURAL_SELECTOR_ACTION_REQUIRED
            or documented_row.get("action_required_codes")
        ):
            action_required = True
            add_issue(
                issues,
                path=str(log_path),
                line=line_no,
                severity="SERIOUS",
                code="V2_STRUCTURAL_SELECTOR_READINESS_ACTION_REQUIRED",
                message=f"LTO-027 readiness row requires action: {documented_row.get('action_required_codes')}",
            )
        for field in (
            "readiness_status",
            "readiness_verdict",
            "gate_summary",
            "readiness_gates",
            "source_counts",
            "evidence_counts",
            "concentration_diagnostics",
            "mt5_account_history_boundary",
            "documented_limitation_codes",
            "action_required_codes",
            "promotion_verdict",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ):
            if documented_row.get(field) != computed.get(field):
                stale_fields.append(field)
        if stale_fields:
            add_issue(
                issues,
                path=str(log_path),
                line=line_no,
                severity="SERIOUS",
                code="V2_STRUCTURAL_SELECTOR_READINESS_ROW_STALE",
                message=f"LTO-027 readiness fields are stale: {stale_fields}",
            )

    if missing or action_required or stale_fields:
        status = "ACTION_REQUIRED"
    else:
        status = "OK_WITH_DOCUMENTED_V2_SELECTOR_NOT_READY"
    return {
        "status": status,
        "audit_rows_available": len(documented_rows),
        "computed_status": computed.get("readiness_status"),
        "computed_readiness_verdict": computed.get("readiness_verdict"),
        "computed_failed_gate_ids": computed.get("gate_summary", {}).get("failed_gate_ids", []),
        "computed_mt5_boundary": computed.get("mt5_account_history_boundary", {}),
        "missing_status": missing,
        "action_required": action_required,
        "stale_fields": stale_fields,
    }


def audit_xauusd_same_market_extension_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    log_path = shadow_root / "xauusd_same_market_extension_status.jsonl"
    lto028_report = root / "research/program_control/LTO028_XAUUSD_SAME_MARKET_EXTENSION_2026-05-05.md"
    documented_rows = read_jsonl(log_path, issues)
    if not documented_rows and not lto028_report.exists():
        return {
            "status": "XAUUSD_SAME_MARKET_EXTENSION_NOT_IMPLEMENTED_OR_NO_LOG_YET",
            "audit_rows_available": 0,
            "computed_status": "NOT_RUN",
            "missing_status": False,
            "action_required": False,
            "stale_fields": [],
        }

    registry_path = root / XAUUSD_SAME_MARKET_REGISTRY_PATH
    source_map_path = root / XAUUSD_SAME_MARKET_SOURCE_MAP_PATH
    sierra_inventory_path = root / XAUUSD_SAME_MARKET_SIERRA_INVENTORY_PATH
    computed = build_xauusd_same_market_status_row(
        registry=_read_json_object(registry_path, issues),
        source_map=_read_json_object(source_map_path, issues),
        sierra_inventory=_read_json_object(sierra_inventory_path, issues),
        candidate_rows=read_jsonl(shadow_root / "strategy_follow_candidates.jsonl", issues),
        evaluation_rows=read_jsonl(shadow_root / "strategy_follow_evaluations.jsonl", issues),
        registry_path=XAUUSD_SAME_MARKET_REGISTRY_PATH,
        source_map_path=XAUUSD_SAME_MARKET_SOURCE_MAP_PATH,
        sierra_inventory_path=XAUUSD_SAME_MARKET_SIERRA_INVENTORY_PATH,
        generated_at_utc=now_utc.isoformat(),
    )
    row_key = str(computed.get("row_key") or "")
    documented = {
        str(row.get("row_key") or ""): (line_no, row)
        for line_no, row in documented_rows
        if row.get("row_key")
    }.get(row_key)
    missing = documented is None
    action_required = False
    stale_fields: list[str] = []

    if missing:
        add_issue(
            issues,
            path=str(log_path),
            severity="SERIOUS",
            code="XAUUSD_SAME_MARKET_EXTENSION_ROW_MISSING",
            message="current LTO-028 XAUUSD same-market extension row is missing",
        )
    else:
        line_no, documented_row = documented
        if documented_row.get("status") == XAUUSD_SAME_MARKET_ACTION_REQUIRED or documented_row.get("action_required_codes"):
            action_required = True
            add_issue(
                issues,
                path=str(log_path),
                line=line_no,
                severity="SERIOUS",
                code="XAUUSD_SAME_MARKET_EXTENSION_ACTION_REQUIRED",
                message=f"LTO-028 row requires action: {documented_row.get('action_required_codes')}",
            )
        for field in (
            "status",
            "opened_outcome_slices_at_registration",
            "outcome_opening_status",
            "source_status",
            "documented_limitation_codes",
            "action_required_codes",
            "promotion_verdict",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ):
            if documented_row.get(field) != computed.get(field):
                stale_fields.append(field)
        if stale_fields:
            add_issue(
                issues,
                path=str(log_path),
                line=line_no,
                severity="SERIOUS",
                code="XAUUSD_SAME_MARKET_EXTENSION_ROW_STALE",
                message=f"LTO-028 fields are stale: {stale_fields}",
            )

    if missing or action_required or stale_fields:
        status = "ACTION_REQUIRED"
    else:
        status = "OK_WITH_DOCUMENTED_XAUUSD_SAME_MARKET_PREREGISTRATION"
    return {
        "status": status,
        "audit_rows_available": len(documented_rows),
        "computed_status": computed.get("status"),
        "opened_outcome_slices_at_registration": computed.get("opened_outcome_slices_at_registration"),
        "xauusd_live_candidate_rows": computed.get("forward_snapshot", {}).get("xauusd_live_candidate_rows"),
        "source_status": computed.get("source_status"),
        "missing_status": missing,
        "action_required": action_required,
        "stale_fields": stale_fields,
    }


def audit_es_mes_preregistration_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    log_path = shadow_root / "es_mes_preregistration_status.jsonl"
    lto029_report = root / "research/program_control/LTO029_ES_MES_STRATEGY_COHORT_PREREGISTRATION_2026-05-05.md"
    documented_rows = read_jsonl(log_path, issues)
    if not documented_rows and not lto029_report.exists():
        return {
            "status": "ES_MES_PREREGISTRATION_NOT_IMPLEMENTED_OR_NO_LOG_YET",
            "audit_rows_available": 0,
            "computed_status": "NOT_RUN",
            "missing_status": False,
            "action_required": False,
            "stale_fields": [],
        }

    computed = build_es_mes_prereg_status_row(
        root=root,
        registry=_read_json_object(root / ES_MES_REGISTRY_PATH, issues),
        prior_preregistration=_read_json_object(root / ES_MES_PRIOR_PREREG_PATH, issues),
        conversion_status=_read_json_object(root / ES_MES_CONVERSION_STATUS_PATH, issues),
        label_status=_read_json_object(root / ES_MES_LABEL_STATUS_PATH, issues),
        sierra_inventory=_read_json_object(root / ES_MES_SIERRA_INVENTORY_PATH, issues),
        registry_path=ES_MES_REGISTRY_PATH,
        prior_prereg_path=ES_MES_PRIOR_PREREG_PATH,
        conversion_status_path=ES_MES_CONVERSION_STATUS_PATH,
        label_status_path=ES_MES_LABEL_STATUS_PATH,
        sierra_inventory_path=ES_MES_SIERRA_INVENTORY_PATH,
        generated_at_utc=now_utc.isoformat(),
    )
    row_key = str(computed.get("row_key") or "")
    documented = {
        str(row.get("row_key") or ""): (line_no, row)
        for line_no, row in documented_rows
        if row.get("row_key")
    }.get(row_key)
    missing = documented is None
    action_required = False
    stale_fields: list[str] = []

    if missing:
        add_issue(
            issues,
            path=str(log_path),
            severity="SERIOUS",
            code="ES_MES_PREREGISTRATION_ROW_MISSING",
            message="current LTO-029 ES/MES preregistration row is missing",
        )
    else:
        line_no, documented_row = documented
        if documented_row.get("status") == ES_MES_PREREG_ACTION_REQUIRED or documented_row.get("action_required_codes"):
            action_required = True
            add_issue(
                issues,
                path=str(log_path),
                line=line_no,
                severity="SERIOUS",
                code="ES_MES_PREREGISTRATION_ACTION_REQUIRED",
                message=f"LTO-029 row requires action: {documented_row.get('action_required_codes')}",
            )
        for field in (
            "status",
            "registered_question",
            "strategy_family",
            "source_mapping",
            "session_windows_utc",
            "evidence_classes",
            "no_lookahead_rules",
            "opened_outcome_slices_at_registration",
            "opened_outcome_artifacts",
            "outcome_opening_status",
            "conversion_rows",
            "label_status",
            "sierra_source_status",
            "validation_gates",
            "gate_summary",
            "documented_limitation_codes",
            "action_required_codes",
            "promotion_verdict",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ):
            if documented_row.get(field) != computed.get(field):
                stale_fields.append(field)
        if stale_fields:
            add_issue(
                issues,
                path=str(log_path),
                line=line_no,
                severity="SERIOUS",
                code="ES_MES_PREREGISTRATION_ROW_STALE",
                message=f"LTO-029 fields are stale: {stale_fields}",
            )

    if missing or action_required or stale_fields:
        status = "ACTION_REQUIRED"
    else:
        status = "OK_WITH_DOCUMENTED_ES_MES_PREREGISTRATION"
    return {
        "status": status,
        "audit_rows_available": len(documented_rows),
        "computed_status": computed.get("status"),
        "opened_outcome_slices_at_registration": computed.get("opened_outcome_slices_at_registration"),
        "opened_outcome_artifacts": computed.get("opened_outcome_artifacts"),
        "strategy_family": computed.get("strategy_family"),
        "missing_status": missing,
        "action_required": action_required,
        "stale_fields": stale_fields,
    }


def _stable_shadow_observer_stale(stale: dict[str, Any] | None) -> dict[str, Any]:
    stale = stale or {}
    return {
        "status": stale.get("status"),
        "action_required_observer_ids": stale.get("action_required_observer_ids") or [],
        "row_statuses": {
            row.get("observer_id"): row.get("stale_status")
            for row in stale.get("rows") or []
        },
    }


def _stable_shadow_observer_gates(gates: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [
        {
            "gate_id": gate.get("gate_id"),
            "passed": gate.get("passed"),
            "blocker_code": gate.get("blocker_code"),
        }
        for gate in (gates or [])
    ]


def audit_shadow_observer_hardening_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    log_path = shadow_root / "shadow_observer_hardening_status.jsonl"
    report_path = root / "research/program_control/LTO035_SHADOW_OBSERVER_HARDENING_2026-05-05.md"
    documented_rows = read_jsonl(log_path, issues)
    if not documented_rows and not report_path.exists():
        return {
            "status": "SHADOW_OBSERVER_HARDENING_NOT_IMPLEMENTED_OR_NO_LOG_YET",
            "audit_rows_available": 0,
            "computed_status": "NOT_RUN",
            "missing_status": False,
            "action_required": False,
            "stale_fields": [],
        }

    computed = build_shadow_observer_hardening_status_row(
        observer_registry=_read_yaml_object(root / SHADOW_OBSERVER_REGISTRY_PATH, issues),
        agent_config=_read_yaml_object(root / SHADOW_OBSERVER_AGENT_CONFIG_PATH, issues),
        observer_state=_read_json_object(root / SHADOW_OBSERVER_STATE_PATH, issues),
        status_rows=read_jsonl(root / SHADOW_OBSERVER_STATUS_PATH, issues),
        strategy_rows=read_jsonl(root / SHADOW_OBSERVER_STRATEGY_EVALUATIONS_PATH, issues),
        generated_at_utc=now_utc.isoformat(),
    )
    row_key = str(computed.get("row_key") or "")
    documented = {
        str(row.get("row_key") or ""): (line_no, row)
        for line_no, row in documented_rows
        if row.get("row_key")
    }.get(row_key)
    missing = documented is None
    action_required = False
    stale_fields: list[str] = []

    if missing:
        add_issue(
            issues,
            path=str(log_path),
            severity="SERIOUS",
            code="SHADOW_OBSERVER_HARDENING_ROW_MISSING",
            message="current LTO-035 shadow-observer hardening row is missing",
        )
    else:
        line_no, documented_row = documented
        if (
            documented_row.get("status") == SHADOW_OBSERVER_HARDENING_ACTION_REQUIRED
            or documented_row.get("action_required_codes")
        ):
            action_required = True
            add_issue(
                issues,
                path=str(log_path),
                line=line_no,
                severity="SERIOUS",
                code="SHADOW_OBSERVER_HARDENING_ACTION_REQUIRED",
                message=f"LTO-035 row requires action: {documented_row.get('action_required_codes')}",
            )
        for field in (
            "status",
            "registry_summary",
            "strategy_observer_counts",
            "final_closeout_detection",
            "restart_policy",
            "gate_summary",
            "documented_limitation_codes",
            "action_required_codes",
            "promotion_verdict",
            "ai_calls",
            "canary_calls",
            "order_calls",
            "paid_data_calls",
            "paid_fetch_attempted",
        ):
            if documented_row.get(field) != computed.get(field):
                stale_fields.append(field)
        if _stable_shadow_observer_stale(
            documented_row.get("stale_observer_detection")
        ) != _stable_shadow_observer_stale(computed.get("stale_observer_detection")):
            stale_fields.append("stale_observer_detection")
        if _stable_shadow_observer_gates(
            documented_row.get("validation_gates")
        ) != _stable_shadow_observer_gates(computed.get("validation_gates")):
            stale_fields.append("validation_gates")
        if stale_fields:
            add_issue(
                issues,
                path=str(log_path),
                line=line_no,
                severity="SERIOUS",
                code="SHADOW_OBSERVER_HARDENING_ROW_STALE",
                message=f"LTO-035 fields are stale: {stale_fields}",
            )

    if missing or action_required or stale_fields:
        status = "ACTION_REQUIRED"
    else:
        status = "OK_WITH_DOCUMENTED_SHADOW_OBSERVER_HARDENING"
    return {
        "status": status,
        "audit_rows_available": len(documented_rows),
        "computed_status": computed.get("status"),
        "active_observers": computed.get("registry_summary", {}).get("active_entries"),
        "source_registry_entries": computed.get("registry_summary", {}).get("total_entries"),
        "stale_action_required": computed.get("stale_observer_detection", {}).get("action_required_observer_ids"),
        "ger40_closeout_confirmed": "ger40_tier2_mso_shadow_v1"
        in computed.get("final_closeout_detection", {}).get("confirmed_observer_ids", []),
        "missing_status": missing,
        "action_required": action_required,
        "stale_fields": stale_fields,
    }


def _read_json_object(path: Path, issues: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        add_issue(
            issues,
            path=str(path),
            severity="CRITICAL",
            code="INVALID_JSON",
            message=str(exc),
        )
        return None
    return payload if isinstance(payload, dict) else None


def audit_account_pnl_truth_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    daily_pnl_state = _read_json_object(shadow_root / "daily_pnl.json", issues)
    daily_pnl_history = read_jsonl(shadow_root / "daily_pnl_history.jsonl", issues)
    broker_rows = read_jsonl(shadow_root / "broker_actual_r_audit.jsonl", issues)
    mt5_deal_rows = read_mt5_deal_exports(root, issues)
    reconciliation_rows = read_jsonl(shadow_root / "account_pnl_truth_reconciliation.jsonl", issues)
    if not daily_pnl_state and not daily_pnl_history and not mt5_deal_rows and not reconciliation_rows:
        return {
            "status": "NO_ACCOUNT_PNL_SOURCE_ROWS",
            "source_rows_checked": 0,
            "reconciliation_rows_available": 0,
            "missing_reconciliation_keys": [],
            "action_required_keys": [],
            "stale_reconciliation_keys": [],
        }

    documented_by_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in reconciliation_rows
        if row.get("row_key")
    }
    computed = build_account_pnl_truth_rows(
        daily_pnl_state=daily_pnl_state,
        daily_pnl_history_rows=daily_pnl_history,
        broker_actual_r_rows=broker_rows,
        mt5_deal_rows=mt5_deal_rows,
        generated_at_utc=now_utc.isoformat(),
    )
    missing: list[str] = []
    action_required: list[str] = []
    stale: list[str] = []
    for row in computed:
        row_key = str(row.get("row_key") or "")
        row_id = str(row.get("trade_id") or row.get("mt5_deal_id") or row_key)
        documented = documented_by_key.get(row_key)
        if not documented:
            missing.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "account_pnl_truth_reconciliation.jsonl"),
                severity="SERIOUS",
                code="ACCOUNT_PNL_TRUTH_RECONCILIATION_MISSING",
                message=f"{row_id} has no LTO-025 account/PnL truth reconciliation row",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("account_pnl_truth_status") == ACCOUNT_PNL_TRUTH_ACTION_REQUIRED:
            action_required.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "account_pnl_truth_reconciliation.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="ACCOUNT_PNL_TRUTH_ACTION_REQUIRED",
                message=f"{row_id} account/PnL truth reconciliation requires action: {documented_row.get('action_required_codes')}",
            )
        stale_fields = [
            field
            for field in (
                "r_evidence_class",
                "dollar_evidence_class",
                "actual_r_claim_allowed",
                "actual_dollar_claim_allowed",
                "broker_actual_r",
                "broker_profit",
                "account_pnl_truth_status",
                "documented_limitation_codes",
                "action_required_codes",
                "source_links",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "account_pnl_truth_reconciliation.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="ACCOUNT_PNL_TRUTH_RECONCILIATION_STALE",
                message=f"{row_id} account/PnL truth fields are stale: {stale_fields}",
            )

    if missing or action_required or stale:
        status = "ACTION_REQUIRED"
    else:
        status = "OK_WITH_DOCUMENTED_PNL_TRUTH_LIMITATIONS"
    return {
        "status": status,
        "source_rows_checked": len(daily_pnl_history) + len(mt5_deal_rows) + (1 if daily_pnl_state else 0),
        "reconciliation_rows_available": len(reconciliation_rows),
        "missing_reconciliation_keys": missing,
        "action_required_keys": action_required,
        "stale_reconciliation_keys": stale,
    }


def audit_trade_index_lifecycle_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    trade_records_root = root / "knowledge_base" / "trade_records"
    inventory_index_path = root / "knowledge_base" / "index" / "trade_record_inventory_index_2026-05-05.json"
    pending_audit_rows = read_jsonl(shadow_root / "pending_limit_lifecycle_audit.jsonl", issues)
    audit_rows = read_jsonl(shadow_root / "trade_index_lifecycle_audit.jsonl", issues)
    trade_records = read_trade_records(trade_records_root)
    if not trade_records and not audit_rows:
        return {
            "status": "NO_TRADE_RECORD_SOURCE_ROWS",
            "trade_records_checked": 0,
            "audit_rows_available": 0,
            "missing_audit_keys": [],
            "action_required_keys": [],
            "stale_audit_keys": [],
            "inventory_index_status": "NOT_REQUIRED",
        }

    documented_by_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in audit_rows
        if row.get("row_key")
    }
    computed = build_trade_index_lifecycle_rows(
        trade_records=trade_records,
        trade_records_root=trade_records_root,
        pending_lifecycle_audit_rows=pending_audit_rows,
        generated_at_utc=now_utc.isoformat(),
    )
    missing: list[str] = []
    action_required: list[str] = []
    stale: list[str] = []
    for row in computed:
        row_key = str(row.get("row_key") or "")
        row_id = str(row.get("candidate_id") or row.get("source_path") or row_key)
        documented = documented_by_key.get(row_key)
        if not documented:
            missing.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "trade_index_lifecycle_audit.jsonl"),
                severity="SERIOUS",
                code="TRADE_INDEX_LIFECYCLE_AUDIT_MISSING",
                message=f"{row_id} has no LTO-026 trade-index lifecycle audit row",
            )
            continue
        documented_row = documented[1]
        if documented_row.get("trade_index_lifecycle_status") == TRADE_INDEX_LIFECYCLE_ACTION_REQUIRED:
            action_required.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "trade_index_lifecycle_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="TRADE_INDEX_LIFECYCLE_AUDIT_ACTION_REQUIRED",
                message=f"{row_id} trade-index lifecycle audit requires action: {documented_row.get('action_required_codes')}",
            )
        stale_fields = [
            field
            for field in (
                "record_hash",
                "lifecycle_state",
                "lifecycle_completeness",
                "has_execution",
                "has_exit",
                "has_embedded_pending_lifecycle",
                "has_pending_lifecycle_audit",
                "pending_lifecycle_audit_row_key",
                "pending_lifecycle_final_state",
                "pending_lifecycle_final_state_status",
                "pending_lifecycle_missed_move_classification",
                "pending_lifecycle_trade_id_global_uniqueness_status",
                "raw_trade_id_collision_symbols",
                "broker_position_mismatch_status",
                "trade_index_lifecycle_status",
                "documented_limitation_codes",
                "action_required_codes",
                "source_links",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale.append(row_id)
            add_issue(
                issues,
                path=str(shadow_root / "trade_index_lifecycle_audit.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="TRADE_INDEX_LIFECYCLE_AUDIT_STALE",
                message=f"{row_id} trade-index lifecycle fields are stale: {stale_fields}",
            )

    inventory_status = "OK"
    inventory = _read_json_object(inventory_index_path, issues)
    if not inventory:
        inventory_status = "MISSING"
        add_issue(
            issues,
            path=str(inventory_index_path),
            severity="SERIOUS",
            code="TRADE_RECORD_INVENTORY_INDEX_MISSING",
            message="LTO-026 current trade-record inventory index is missing",
        )
    else:
        expected_index = build_inventory_index(computed, generated_at_utc=now_utc.isoformat())
        fields = (
            "schema_version",
            "trade_record_count",
            "index_count",
            "index_count_equals_trade_record_count",
            "latest_record_date",
            "by_symbol",
            "by_final_outcome",
            "by_lifecycle_completeness",
            "by_trade_index_lifecycle_status",
        )
        stale_index_fields = [field for field in fields if inventory.get(field) != expected_index.get(field)]
        source_paths = [entry.get("source_path") for entry in inventory.get("entries") or []]
        expected_paths = [entry.get("source_path") for entry in expected_index.get("entries") or []]
        if source_paths != expected_paths:
            stale_index_fields.append("entries.source_path")
        if inventory.get("schema_version") != TRADE_RECORD_INVENTORY_INDEX_SCHEMA_VERSION:
            stale_index_fields.append("schema_version")
        if stale_index_fields:
            inventory_status = "STALE"
            add_issue(
                issues,
                path=str(inventory_index_path),
                severity="SERIOUS",
                code="TRADE_RECORD_INVENTORY_INDEX_STALE",
                message=f"inventory index fields are stale: {sorted(set(stale_index_fields))}",
            )

    if missing or action_required or stale or inventory_status != "OK":
        status = "ACTION_REQUIRED"
    else:
        status = "OK_WITH_DOCUMENTED_LIFECYCLE_BLOCKERS"
    return {
        "status": status,
        "trade_records_checked": len(trade_records),
        "audit_rows_available": len(audit_rows),
        "missing_audit_keys": missing,
        "action_required_keys": action_required,
        "stale_audit_keys": stale,
        "inventory_index_status": inventory_status,
    }


def _event_log_file_status(path: Path) -> str:
    if not path.exists():
        return "EVENT_LOG_FILE_MISSING_NO_EVENT_STATUS_REQUIRED"
    if path.stat().st_size == 0:
        return "EVENT_LOG_FILE_EMPTY_NO_EVENT_STATUS_REQUIRED"
    return "EVENT_LOG_FILE_HAS_EVENT_ROWS"


def audit_exit_management_status_contract(
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_rows = read_jsonl(shadow_root / "strategy_follow_candidates.jsonl", issues)
    status_rows = read_jsonl(shadow_root / "exit_management_shadow_status.jsonl", issues)
    event_statuses = {
        "be": _event_log_file_status(shadow_root / "be_shadow_log.jsonl"),
        "partial_close": _event_log_file_status(shadow_root / "partial_close_shadow_log.jsonl"),
        "time_in_trade": _event_log_file_status(shadow_root / "time_in_trade.jsonl"),
    }
    computed = build_exit_management_status_rows(
        candidate_rows,
        pending_rows=read_jsonl(shadow_root / "pending_limit_lifecycle_join_backfill.jsonl", issues),
        account_rows=read_jsonl(shadow_root / "account_truth_reconciliation_status.jsonl", issues),
        broker_rows=read_jsonl(shadow_root / "broker_actual_r_audit.jsonl", issues),
        be_event_rows=read_jsonl(shadow_root / "be_shadow_log.jsonl", issues),
        partial_event_rows=read_jsonl(shadow_root / "partial_close_shadow_log.jsonl", issues),
        time_in_trade_rows=read_jsonl(shadow_root / "time_in_trade.jsonl", issues),
        event_log_file_statuses=event_statuses,
        generated_at_utc=now_utc.isoformat(),
    )
    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in status_rows
        if row.get("row_key")
    }
    computed_status_counts = Counter(str(row.get("exit_management_status") or "UNKNOWN") for row in computed)
    missing: list[str] = []
    action_required: list[str] = []
    stale: list[str] = []
    for row in computed:
        row_key = str(row.get("row_key") or "")
        candidate_id = str(row.get("candidate_id") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "exit_management_shadow_status.jsonl"),
                severity="SERIOUS",
                code="EXIT_MANAGEMENT_STATUS_MISSING",
                message=(
                    f"candidate {candidate_id} has no append-only LTO-021 no-event/status row; "
                    "missing/empty event logs cannot be distinguished from no trigger"
                ),
            )
            continue
        documented_row = documented[1]
        if documented_row.get("exit_management_status") == EXIT_MANAGEMENT_ACTION_REQUIRED:
            action_required.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "exit_management_shadow_status.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="EXIT_MANAGEMENT_STATUS_ACTION_REQUIRED",
                message=(
                    f"candidate {candidate_id} exit-management status requires action: "
                    f"{documented_row.get('action_required_codes')}"
                ),
            )
        stale_fields = [
            field
            for field in (
                "fill_state",
                "pending_lifecycle_fill_status",
                "account_truth_fill_status",
                "broker_actual_r_fill_status",
                "be_shadow_status",
                "partial_close_shadow_status",
                "time_in_trade_shadow_status",
                "documented_no_event_codes",
                "action_required_codes",
                "actual_event_row_counts",
                "event_log_file_statuses",
                "exit_management_status",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale.append(candidate_id)
            add_issue(
                issues,
                path=str(shadow_root / "exit_management_shadow_status.jsonl"),
                line=documented[0],
                severity="SERIOUS",
                code="EXIT_MANAGEMENT_STATUS_STALE",
                message=f"candidate {candidate_id} exit-management status fields are stale: {stale_fields}",
            )

    if missing or action_required or stale:
        status = "ACTION_REQUIRED"
    elif computed:
        status = "OK_WITH_DOCUMENTED_EXIT_MANAGEMENT_NO_EVENTS"
    else:
        status = "NO_CANDIDATE_ROWS"
    return {
        "status": status,
        "candidate_rows_checked": len(candidate_rows),
        "status_rows_available": len(status_rows),
        "computed_exit_management_status_counts": dict(computed_status_counts),
        "event_log_file_statuses": event_statuses,
        "missing_status_candidates": missing,
        "action_required_candidates": action_required,
        "stale_status_candidates": stale,
    }


def audit_session_vol_sweep_status_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    status_path = shadow_root / "session_volatility_sweep_status.jsonl"
    status_rows = read_jsonl(status_path, issues)
    source_files_exist = any(
        (shadow_root / name).exists()
        for name in ("session_volatility_log.csv", "sweep_divergence_log.csv")
    )
    if not status_rows and not source_files_exist:
        return {
            "status": "NO_SOURCE_ROWS",
            "target_date": target_previous_utc_date(now_utc).isoformat(),
            "status_rows_available": 0,
            "missing_status_sources": [],
            "action_required_sources": [],
            "stale_status_sources": [],
        }

    target_date = target_previous_utc_date(now_utc)
    computed = build_session_vol_sweep_status_rows(
        root=root,
        target_date=target_date,
        generated_at_utc=now_utc.isoformat(),
    )
    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in status_rows
        if row.get("row_key")
    }
    missing: list[str] = []
    action_required: list[str] = []
    stale: list[str] = []
    for row in computed:
        row_key = str(row.get("row_key") or "")
        source_name = str(row.get("source_name") or row_key)
        documented = audit_by_row_key.get(row_key)
        if not documented:
            missing.append(source_name)
            add_issue(
                issues,
                path=str(status_path),
                severity="SERIOUS",
                code="SESSION_VOL_SWEEP_STATUS_MISSING",
                message=(
                    f"{source_name} has no LTO-022 cadence/status row for {target_date}; "
                    "CSV absence and explicit no-event rows cannot be distinguished"
                ),
            )
            continue
        documented_row = documented[1]
        if documented_row.get("coverage_status") == SESSION_VOL_SWEEP_ACTION_REQUIRED:
            action_required.append(source_name)
            add_issue(
                issues,
                path=str(status_path),
                line=documented[0],
                severity="SERIOUS",
                code="SESSION_VOL_SWEEP_STATUS_ACTION_REQUIRED",
                message=(
                    f"{source_name} LTO-022 status requires action: "
                    f"{documented_row.get('action_required_codes')}"
                ),
            )
        stale_fields = [
            field
            for field in (
                "source_file_status",
                "source_row_count",
                "latest_run_time_utc",
                "expected_symbol_sessions",
                "covered_symbol_sessions",
                "missing_symbol_sessions",
                "coverage_status",
                "event_row_count",
                "no_event_row_count",
                "action_required_codes",
            )
            if documented_row.get(field) != row.get(field)
        ]
        if stale_fields:
            stale.append(source_name)
            add_issue(
                issues,
                path=str(status_path),
                line=documented[0],
                severity="SERIOUS",
                code="SESSION_VOL_SWEEP_STATUS_STALE",
                message=f"{source_name} LTO-022 status fields are stale: {stale_fields}",
            )

    status_counts = Counter(str(row.get("coverage_status") or "UNKNOWN") for row in computed)
    if missing or action_required or stale:
        status = "ACTION_REQUIRED"
    elif computed:
        status = "OK_WITH_DOCUMENTED_SESSION_VOL_SWEEP_STATUS"
    else:
        status = "NO_SOURCE_ROWS"
    return {
        "status": status,
        "target_date": target_date.isoformat(),
        "status_rows_available": len(status_rows),
        "computed_coverage_status_counts": dict(status_counts),
        "missing_status_sources": missing,
        "action_required_sources": action_required,
        "stale_status_sources": stale,
    }


def audit_notification_queue_dead_zone_contract(
    root: Path,
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    status_path = shadow_root / "notification_queue_dead_zone_status.jsonl"
    status_rows = read_jsonl(status_path, issues)
    queue_path = root / NOTIFICATION_QUEUE_PATH
    lock_path = root / NOTIFICATION_QUEUE_LOCK_PATH
    if not status_rows and not queue_path.exists() and not lock_path.exists():
        return {
            "status": "NOT_APPLICABLE_NO_NOTIFICATION_QUEUE_SOURCE",
            "status_rows_available": 0,
            "computed_worker_status": None,
            "computed_queue_status": None,
            "missing_status": False,
            "action_required": False,
            "stale_fields": [],
        }
    computed = build_notification_queue_status_row(
        root=root,
        now_utc=now_utc,
        target_date=now_utc.date(),
        generated_at_utc=now_utc.isoformat(),
    )
    audit_by_row_key: dict[str, tuple[int, dict[str, Any]]] = {
        str(row.get("row_key")): (line_no, row)
        for line_no, row in status_rows
        if row.get("row_key")
    }
    missing = False
    action_required = False
    stale_fields: list[str] = []
    documented = audit_by_row_key.get(str(computed.get("row_key") or ""))
    if not documented:
        missing = True
        add_issue(
            issues,
            path=str(status_path),
            severity="SERIOUS",
            code="NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_MISSING",
            message="LTO-037 notification queue dead-zone status row is missing or stale",
        )
    else:
        documented_row = documented[1]
        if documented_row.get("notification_queue_status") == NOTIFICATION_QUEUE_ACTION_REQUIRED:
            action_required = True
            add_issue(
                issues,
                path=str(status_path),
                line=documented[0],
                severity="SERIOUS",
                code="NOTIFICATION_QUEUE_DEAD_ZONE_ACTION_REQUIRED",
                message=f"LTO-037 notification queue requires action: {documented_row.get('action_required_codes')}",
            )
        stale_fields = [
            field
            for field in notification_queue_status_fields_for_contract()
            if documented_row.get(field) != computed.get(field)
        ]
        if stale_fields:
            add_issue(
                issues,
                path=str(status_path),
                line=documented[0],
                severity="SERIOUS",
                code="NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_STALE",
                message=f"LTO-037 notification queue status fields are stale: {stale_fields}",
            )

    if missing or action_required or stale_fields:
        status = "ACTION_REQUIRED"
    else:
        status = "OK_WITH_DOCUMENTED_NOTIFICATION_QUEUE_DEAD_ZONE"
    return {
        "status": status,
        "status_rows_available": len(status_rows),
        "computed_worker_status": computed.get("worker_status"),
        "computed_queue_status": computed.get("queue_status"),
        "computed_dead_zone_active": computed.get("dead_zone_active"),
        "missing_status": missing,
        "action_required": action_required,
        "stale_fields": stale_fields,
    }


def audit_ai_narrowing_policy_shadow_evaluations_contract(
    shadow_root: Path,
    now_utc: datetime,
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_path = shadow_root / "strategy_follow_candidates.jsonl"
    evaluation_path = shadow_root / "ai_narrowing_policy_shadow_evaluations.jsonl"
    candidate_rows = read_jsonl(candidate_path, issues)
    evaluation_rows = read_jsonl(evaluation_path, issues)
    current_candidate_sha = sha256_path(candidate_path)

    candidate_ids = {
        str(row.get("candidate_id"))
        for _, row in candidate_rows
        if row.get("candidate_id")
    }
    current_evaluation_rows = [
        (line_no, row)
        for line_no, row in evaluation_rows
        if current_candidate_sha and row.get("candidate_source_sha256") == current_candidate_sha
    ]
    current_eval_candidate_ids = {
        str(row.get("candidate_id"))
        for _, row in current_evaluation_rows
        if row.get("candidate_id")
    }
    missing_candidate_ids = sorted(candidate_ids - current_eval_candidate_ids)
    stale_source_rows = len(evaluation_rows) - len(current_evaluation_rows)
    forbidden_flag_rows = 0

    for _, row in current_evaluation_rows:
        containers = [row]
        for key in ("event", "evaluation"):
            if isinstance(row.get(key), dict):
                containers.append(row[key])
        if any(container.get(field) is not False for container in containers for field in AI_NARROWING_FORBIDDEN_TRUE_FIELDS if field in container):
            forbidden_flag_rows += 1

    if missing_candidate_ids:
        add_issue(
            issues,
            path=str(evaluation_path),
            severity="SERIOUS",
            code="AI_NARROWING_SHADOW_EVAL_MISSING_CURRENT_CANDIDATES",
            message=(
                f"missing current-source AI narrowing evaluations for {len(missing_candidate_ids)} "
                f"candidate ids; first={missing_candidate_ids[:5]}"
            ),
        )
    if forbidden_flag_rows:
        add_issue(
            issues,
            path=str(evaluation_path),
            severity="SERIOUS",
            code="AI_NARROWING_SHADOW_EVAL_FORBIDDEN_FLAGS",
            message=f"{forbidden_flag_rows} current-source AI narrowing evaluation rows carry forbidden runtime flags",
        )

    status = (
        "ACTION_REQUIRED"
        if missing_candidate_ids or forbidden_flag_rows
        else "OK_WITH_DEFAULT_OFF_AI_NARROWING_SHADOW_EVALUATIONS"
    )
    return {
        "status": status,
        "candidate_rows": len(candidate_rows),
        "evaluation_rows": len(evaluation_rows),
        "current_source_evaluation_rows": len(current_evaluation_rows),
        "stale_source_evaluation_rows": stale_source_rows,
        "current_candidate_sha256": current_candidate_sha,
        "candidate_ids": len(candidate_ids),
        "covered_current_candidate_ids": len(current_eval_candidate_ids),
        "missing_current_candidate_ids": len(missing_candidate_ids),
        "forbidden_flag_rows": forbidden_flag_rows,
        "event_adapter_status_counts": dict(
            sorted(Counter(str(row.get("event_adapter_status") or "UNKNOWN") for _, row in current_evaluation_rows).items())
        ),
        "registry_eval_status_counts": dict(
            sorted(
                Counter(str(row.get("ai_narrowing_registry_eval_status") or "UNKNOWN") for _, row in current_evaluation_rows).items()
            )
        ),
        "generated_at_utc": now_utc.isoformat(),
    }


def build_report(root: Path, now_utc: datetime) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    shadow_root = root / "shadow_logs"
    jsonl_files: list[dict[str, Any]] = []
    jsonl_paths = sorted(shadow_root.glob("*.jsonl")) if shadow_root.exists() else []
    for path in jsonl_paths:
        jsonl_files.append(
            verify_jsonl_file(
                shadow_root,
                path.name,
                JSONL_SPECS.get(path.name),
                now_utc,
                issues,
            )
        )

    for name in EXPECTED_WAITING_FILES:
        path = shadow_root / name
        if path.exists() and path.stat().st_size > 0 and path.suffix == ".jsonl":
            # If the lane wakes up, it should be represented in the inspected list.
            if not any(item["path"] == str(path) for item in jsonl_files):
                jsonl_files.append(
                    verify_jsonl_file(shadow_root, name, JSONL_SPECS.get(name), now_utc, issues)
                )

    csv_files = [
        verify_csv_file(shadow_root, name, spec, now_utc)
        for name, spec in sorted(CSV_SPECS.items())
    ]

    waiting_files = {
        name: reason
        for name, reason in EXPECTED_WAITING_FILES.items()
        if not (shadow_root / name).exists() or (shadow_root / name).stat().st_size == 0
    }
    mso_candidate_join_health = audit_candidate_mso_snapshot_coverage(shadow_root, now_utc, issues)
    candidate_registry_audit_health = audit_candidate_registry_contract(shadow_root, now_utc, issues)
    candidate_path_contract_health = audit_candidate_path_contract(shadow_root, now_utc, issues)
    opportunity_lifecycle_audit_health = audit_opportunity_lifecycle_contract(shadow_root, now_utc, issues)
    pending_limit_lifecycle_audit_health = audit_pending_limit_lifecycle_contract(shadow_root, now_utc, issues)
    v2b_forward_pair_resolution_audit_health = audit_v2b_forward_pair_resolution_contract(shadow_root, now_utc, issues)
    prefill_delivery_path_audit_health = audit_prefill_delivery_path_contract(shadow_root, now_utc, issues)
    fvg_ob_confluence_audit_health = audit_fvg_ob_confluence_contract(shadow_root, now_utc, issues)
    context_control_audit_health = audit_context_control_contract(shadow_root, now_utc, issues)
    broker_actual_r_audit_health = audit_broker_actual_r_contract(root, shadow_root, now_utc, issues)
    j46_j49_exit_comparator_health = audit_j46_j49_exit_comparator_contract(shadow_root, now_utc, issues)
    s79_side_aware_context_health = audit_s79_side_aware_context_contract(root, shadow_root, now_utc, issues)
    regime_decay_outcome_health = audit_regime_decay_outcome_contract(root, shadow_root, now_utc, issues)
    decision_layer_diagnostics_health = audit_decision_layer_diagnostics_contract(root, shadow_root, now_utc, issues)
    mechanical_context_health = audit_mechanical_context_contract(root, shadow_root, now_utc, issues)
    ml_shadow_health = audit_ml_shadow_contract(root, shadow_root, now_utc, issues)
    v2_structural_selector_readiness_health = audit_v2_structural_selector_readiness_contract(root, shadow_root, now_utc, issues)
    xauusd_same_market_extension_health = audit_xauusd_same_market_extension_contract(root, shadow_root, now_utc, issues)
    es_mes_preregistration_health = audit_es_mes_preregistration_contract(root, shadow_root, now_utc, issues)
    shadow_observer_hardening_health = audit_shadow_observer_hardening_contract(root, shadow_root, now_utc, issues)
    account_pnl_truth_health = audit_account_pnl_truth_contract(root, shadow_root, now_utc, issues)
    trade_index_lifecycle_health = audit_trade_index_lifecycle_contract(root, shadow_root, now_utc, issues)
    exit_management_status_health = audit_exit_management_status_contract(shadow_root, now_utc, issues)
    session_vol_sweep_status_health = audit_session_vol_sweep_status_contract(root, shadow_root, now_utc, issues)
    notification_queue_dead_zone_health = audit_notification_queue_dead_zone_contract(root, shadow_root, now_utc, issues)
    ai_narrowing_policy_shadow_evaluations_health = audit_ai_narrowing_policy_shadow_evaluations_contract(
        shadow_root,
        now_utc,
        issues,
    )

    counts = {
        "jsonl_files": len(jsonl_files),
        "jsonl_rows": sum(item["rows"] for item in jsonl_files),
        "known_schema_jsonl_files": sum(1 for item in jsonl_files if item["known_spec"]),
        "csv_files": len(csv_files),
    }

    report = {
        "schema_version": "shadow_log_integrity_verification_v1",
        "generated_at_utc": now_utc.isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "counts": counts,
        "jsonl_files": jsonl_files,
        "csv_files": csv_files,
        "waiting_files": waiting_files,
        "mso_candidate_join_health": mso_candidate_join_health,
        "candidate_registry_audit_health": candidate_registry_audit_health,
        "candidate_path_contract_health": candidate_path_contract_health,
        "opportunity_lifecycle_audit_health": opportunity_lifecycle_audit_health,
        "pending_limit_lifecycle_audit_health": pending_limit_lifecycle_audit_health,
        "v2b_forward_pair_resolution_audit_health": v2b_forward_pair_resolution_audit_health,
        "prefill_delivery_path_audit_health": prefill_delivery_path_audit_health,
        "fvg_ob_confluence_audit_health": fvg_ob_confluence_audit_health,
        "context_control_audit_health": context_control_audit_health,
        "broker_actual_r_audit_health": broker_actual_r_audit_health,
        "j46_j49_exit_comparator_health": j46_j49_exit_comparator_health,
        "s79_side_aware_context_health": s79_side_aware_context_health,
        "regime_decay_outcome_health": regime_decay_outcome_health,
        "decision_layer_diagnostics_health": decision_layer_diagnostics_health,
        "mechanical_context_health": mechanical_context_health,
        "ml_shadow_health": ml_shadow_health,
        "v2_structural_selector_readiness_health": v2_structural_selector_readiness_health,
        "xauusd_same_market_extension_health": xauusd_same_market_extension_health,
        "es_mes_preregistration_health": es_mes_preregistration_health,
        "shadow_observer_hardening_health": shadow_observer_hardening_health,
        "account_pnl_truth_health": account_pnl_truth_health,
        "trade_index_lifecycle_health": trade_index_lifecycle_health,
        "exit_management_status_health": exit_management_status_health,
        "session_vol_sweep_status_health": session_vol_sweep_status_health,
        "notification_queue_dead_zone_health": notification_queue_dead_zone_health,
        "ai_narrowing_policy_shadow_evaluations_health": ai_narrowing_policy_shadow_evaluations_health,
        "issues": issues,
    }
    report["overall_status"] = summarize_status(report, issues)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("research/program_control/SHADOW_LOG_INTEGRITY_VERIFICATION_2026-05-04.md"),
    )
    args = parser.parse_args()

    root = Path.cwd()
    now_utc = datetime.now(timezone.utc)
    report = build_report(root, now_utc)

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, args.output_md)

    print(
        json.dumps(
            {
                "overall_status": report["overall_status"],
                "counts": report["counts"],
                "issues": Counter(issue["severity"] for issue in report["issues"]),
                "waiting_files": report["waiting_files"],
                "output_json": str(args.output_json),
                "output_md": str(args.output_md),
            },
            default=dict,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
