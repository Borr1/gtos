"""GTOS vNext runtime decision surface.

This module is the callable bridge from verified vNext evidence artifacts into
the live/replay runtime path. It does not place orders, call external services,
or mutate broker state. It maps the current candidate event to the strongest
matching vNext artifact scope and returns FOLLOW, AVOID, MIXED, or LEGACY with
the R/proxy/stress/effective-N evidence attached.
"""

from __future__ import annotations

import json
import hashlib
import logging
import os
import re
import threading
from collections.abc import Iterable as IterableABC
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from itertools import combinations, product
from pathlib import Path
from typing import Any, Iterable, Literal

from src.components.selector_v4 import (
    SelectorV4AdmissionDecision,
    evaluate_selector_v4_admission,
)
from src.components.dynamic_target_stop_geometry_v4 import (
    build_target_stop_geometry_v4_contract,
)
from src.research_infra.wave3_follow_avoid_mixed_numeric_confluence import (
    build_numeric_confluence_source,
    final_numeric_confluence_mapping,
    summarize_numeric_confluence_sources,
)
from src.components.ai_reliability_contract import (
    AI_RELIABILITY_CONTRACT_SCHEMA_VERSION,
    build_deterministic_baseline_contract,
    build_disagreement_calibration_contract,
    build_model_version_contract,
    build_semantic_ownership_handoff,
)


def _stable_sha256(payload: Any) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()

try:  # pragma: no cover - Windows production path
    import msvcrt
except ImportError:  # pragma: no cover
    msvcrt = None  # type: ignore[assignment]

try:  # pragma: no cover - POSIX fallback for local/dev runners
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)
_JSONL_THREAD_LOCKS: dict[str, threading.Lock] = {}
_JSONL_THREAD_LOCKS_GUARD = threading.Lock()

DecisionLabel = Literal["FOLLOW", "AVOID", "MIXED", "LEGACY"]
PreAIAction = Literal[
    "ALLOW_AI",
    "SKIP_AI_AVOID_ONLY",
    "NARROW_AI_TO_SIDE",
    "NARROW_AI_TO_ROUTE",
    "NARROW_AI_EXCLUDE_FRAMEWORKS",
]
PendingPolicyAction = Literal["PLACE_LIMIT", "SKIP_PENDING_NOFILL_AVOID", "MARKET_ENTRY_NOW"]
LTFPathExecutionAction = Literal[
    "PLACE_LIMIT",
    "MONITOR_LTF_PATH",
    "MARKET_ENTRY_NOW",
    "ADJUST_LIMIT_ENTRY",
    "SKIP_LTF_NOFILL_AVOID",
]
PropSafeSelectorAction = Literal["ALLOW", "REDUCE_RISK", "DEFER_UNTIL_RESET", "BLOCK"]
AIPolicyAction = Literal[
    "CALL_AI_CURRENT_PATH",
    "SKIP_AI_MECHANICAL_AVOID",
    "MECHANICAL_FOLLOW_NO_AI",
    "CALL_AI_CONSTRAINED_VALIDATOR",
    "CALL_AI_NARROWED_ROUTE",
    "CALL_AI_FRAMEWORK_SCREENER",
    "CALL_AI_MIXED_RESOLUTION",
    "CALL_AI_LEGACY_REPLAYED",
    "BLOCK_LEGACY_BROAD_FALLBACK",
]
ExitPolicyAction = Literal[
    "LEGACY_EXIT_POLICY",
    "SHADOW_EXIT_POLICY_CONTEXT",
    "KEEP_ACTIVE_EXIT_POLICY_PENDING_SIGNIFICANT_PARTIAL_SPLIT_EVIDENCE",
    "REQUIRE_ENTRY_EXIT_TIMESTAMPS_BEFORE_SESSION_EXIT_POLICY",
    "PRESERVE_NO_EVENT_EXIT_STATUS_AS_COMPLETE",
    "USE_H29_AWARE_EXIT_REPLAY_CONTEXT",
]


def _windows_extended_path(path: Path) -> Path:
    if os.name != "nt":
        return path
    raw = str(path)
    if raw.startswith("\\\\?\\") or raw.startswith("\\\\.\\"):
        return path
    absolute = path if path.is_absolute() else Path.cwd() / path
    return Path("\\\\?\\" + str(absolute))


def _jsonl_thread_lock(lock_path: Path) -> threading.Lock:
    key = str(lock_path.absolute())
    with _JSONL_THREAD_LOCKS_GUARD:
        lock = _JSONL_THREAD_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _JSONL_THREAD_LOCKS[key] = lock
        return lock


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    return str(value)


def _append_jsonl_locked(target: Path | str, row: dict[str, Any]) -> None:
    """Append one JSONL object under a sidecar process lock."""
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(row, sort_keys=True, default=_json_default) + "\n").encode("utf-8")
    lock_path = target_path.with_suffix(target_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with _jsonl_thread_lock(lock_path):
        locked = False
        with lock_path.open("a+b") as lock_handle:
            try:
                lock_handle.seek(0)
                if msvcrt is not None:
                    msvcrt.locking(lock_handle.fileno(), msvcrt.LK_LOCK, 1)
                    locked = True
                elif fcntl is not None:
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
                    locked = True
                with target_path.open("ab") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
            finally:
                if locked:
                    lock_handle.seek(0)
                    if msvcrt is not None:
                        msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
                    elif fcntl is not None:
                        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def _local_path_exists(path: Path) -> bool:
    if path.exists():
        return True
    if os.name != "nt":
        return False
    try:
        return _windows_extended_path(path).exists()
    except OSError:
        return False


def _local_path_for_io(path: Path) -> Path:
    if os.name == "nt" and not path.exists():
        extended = _windows_extended_path(path)
        if extended.exists():
            return extended
    return path
Ready8ControlPolicyAction = Literal[
    "READY8_LEGACY_CONTROL_POLICY",
    "SHADOW_READY8_CONTROL_CONTEXT",
    "BLOCK_READY8_CARD_RANK_CONTEXT",
    "REQUIRE_READY8_SOURCE_CONTROL_REPAIR",
    "REQUIRE_READY8_EXACT_GEOMETRY_SOURCE",
    "KEEP_READY8_WEAK_OVERLAP_SHADOW_ONLY",
    "BLOCK_READY8_PROMOTION_OR_LIVE_USE",
]

DEFAULT_REVIEW_ARTIFACT_PATH = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCORER_FILTER_ROUTER_REVIEW_LEDGER_2026-05-18.jsonl"
)
DEFAULT_IMPLEMENTATION_ARTIFACT_PATH = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCORER_FILTER_ROUTER_IMPLEMENTATION_LEDGER_2026-05-18.jsonl"
)
DEFAULT_EVIDENCE_MATRIX_ARTIFACT_PATH = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EVIDENCE_TO_SYSTEM_BUILD_MATRIX_2026-05-18.jsonl"
)
DEFAULT_BRIDGE_DIAGNOSTIC_ARTIFACT_PATH = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_BRIDGE_RESIDUE_RUNTIME_ROWS_2026-05-18.jsonl"
)
DEFAULT_AI_NARROWING_CAPACITY_BLOCKLIST_ARTIFACT_PATH = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization/"
    "MAIN_ORCH48_AI_NARROWING_CAPACITY_BLOCKLIST_LEDGER_2026-05-18.jsonl"
)
DEFAULT_CP281_RULE_REPLAY_RESULT_TABLE_ARTIFACT_PATH = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization/"
    "MAIN_ORCH48_CP281_RULE_REPLAY_EXECUTION_MATERIALIZATION_RESULT_TABLE_LEDGER_2026-05-18.jsonl"
)
DEFAULT_CP281_RULE_REPLAY_EVENT_ARTIFACT_PATH = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization/"
    "MAIN_ORCH48_CP281_RULE_REPLAY_EXECUTION_MATERIALIZATION_EVENT_LEDGER_2026-05-18.jsonl"
)
DEFAULT_CP281_BRANCH_DECISIONS_ARTIFACT_PATH = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization/"
    "MAIN_ORCH48_CP281_BRANCH_DECISIONS_LEDGER_2026-05-18.jsonl"
)
DEFAULT_CP281_READY_RUNTIME_AGGREGATE_ARTIFACT_PATH = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization/"
    "MAIN_ORCH48_CP281_READY_RUNTIME_MAPPING_AGGREGATE_LEDGER_2026-05-18.jsonl"
)
DEFAULT_CP281_READY_RUNTIME_RULE_ARTIFACT_PATH = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization/"
    "MAIN_ORCH48_CP281_READY_RUNTIME_MAPPING_RULE_LEDGER_2026-05-18.jsonl"
)
DEFAULT_FALLBACK_ARTIFACT_PATH = DEFAULT_IMPLEMENTATION_ARTIFACT_PATH
DEFAULT_LLM_SPECIALIZATION_BACKLOG_PATH = Path(
    ".context/00_core/llm_specialization_research_backlog.md"
)
DEFAULT_LOCAL_HEAVY_DATA_ROOTS = (
    Path(r"C:\Users\MSI\Documents\ai-trading-agent"),
    Path(r"C:\tmp"),
)

MATCH_FIELDS = (
    "symbol",
    "source_symbol",
    "symbol_family",
    "market",
    "timeframe",
    "framework",
    "route_family",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "primitive",
    "side",
    "source_component",
    "source_path_sha256",
    "source_file_sha256",
    "action_family",
    "action_class",
    "entry_variant",
    "proxy_r_class",
    "target_stop_order_class",
)

EVENT_FILTER_FIELDS = (
    "r_evidence_class",
    "implementation_action",
    "evidence_family",
    "source_name",
    "source_group",
    "source_role",
    "system_surface",
)

EVENT_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "symbol": ("symbol", "broker_symbol", "candidate_symbol"),
    "source_symbol": ("source_symbol", "symbol", "broker_symbol", "candidate_symbol"),
    "symbol_family": ("symbol_family", "family"),
    "market": ("market", "symbol", "broker_symbol", "candidate_symbol"),
    "timeframe": ("timeframe", "entry_timeframe", "market_timeframe"),
    "framework": ("framework", "selected_framework", "effective_framework", "route_framework"),
    "route_family": ("route_family", "mechanical_route_family", "route", "strategy_family"),
    "market_timeframe": ("market_timeframe", "timeframe", "entry_timeframe"),
    "route_session": ("route_session", "session", "kill_zone"),
    "horizon_id": ("horizon_id", "horizon"),
    "side": ("side", "selected_side", "direction", "candidate_side"),
    "source_component": ("source_component", "component", "source_component_name"),
    "source_path_sha256": ("source_path_sha256",),
    "source_file_sha256": ("source_file_sha256",),
    "action_family": ("action_family", "matched_action_family"),
    "action_class": ("action_class", "matched_action_class", "main_compiler_action_class"),
    "entry_variant": ("entry_variant",),
    "proxy_r_class": ("proxy_r_class",),
    "target_stop_order_class": ("target_stop_order_class",),
    "r_evidence_class": ("r_evidence_class",),
    "implementation_action": ("implementation_action",),
    "evidence_family": ("evidence_family",),
    "source_name": ("source_name",),
    "source_group": ("source_group",),
    "source_role": ("source_role",),
    "system_surface": ("system_surface",),
    "primitive": ("primitive", "market_primitive", "source_primitive", "evidence_primitive"),
}

METRIC_NAMES = (
    "cost_adjusted_simulated_r",
    "proxy_score",
    "stress_simulated_r",
    "effective_n",
)
DEFAULT_DECISION_LOG_PATH = Path("shadow_logs/gtos_vnext_runtime_decisions.jsonl")
DEFAULT_REPLACEMENT_MONITORING_LOG_PATH = Path(
    "shadow_logs/gtos_vnext_replacement_monitoring.jsonl"
)
DEFAULT_EVIDENCE_ROW_DETAIL_LIMIT = 250
DEFAULT_EVIDENCE_ID_LIST_LIMIT = 2000
EVIDENCE_DIMENSION_FIELDS = (
    "symbol",
    "source_symbol",
    "symbol_family",
    "market",
    "timeframe",
    "framework",
    "route_family",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
    "source_component",
    "source_path_sha256",
    "source_file_sha256",
    "action_family",
    "action_class",
    "entry_variant",
    "positive_result_class",
    "source_result_class",
    "rejected_repair_class",
    "market_gap_action_class",
    "market_gap_code_status",
    "market_gap_proxy_interval_gate",
    "proxy_r_class",
    "target_stop_order_class",
    "source_ai_action",
    "activation_state",
    "ai_decision",
    "capture_status",
    "final_outcome",
    "lifecycle_state",
    "lifecycle_completeness",
    "trade_index_lifecycle_status",
    "actual_r_class",
    "pending_lifecycle_final_state",
    "broker_position_mismatch_status",
    "model_used",
    "r_evidence_class",
    "implementation_action",
    "evidence_family",
    "source_name",
    "source_group",
    "source_role",
    "system_surface",
    "route_family_inferred_from",
    "primitive",
    "frontier_status",
    "action_family",
)

SESSION_ALIASES = {
    "london": "london_core",
    "london_core": "london_core",
    "ldn": "london_core",
    "ny": "ny_core",
    "new_york": "ny_core",
    "new_york_core": "ny_core",
    "ny_core": "ny_core",
    "tokyo": "tokyo_kz",
    "tokyo_kz": "tokyo_kz",
    "asia": "tokyo_kz",
    "off_core": "off_core_session",
    "off_core_session": "off_core_session",
    "off_kz": "off_core_session",
    "all_sessions": "ALL_SESSIONS",
}
SESSION_WILDCARD = "ALL_SESSIONS"
SESSION_CANONICAL_VALUES = ("london_core", "ny_core", "tokyo_kz", "off_core_session")

SYMBOL_FAMILY_BY_SYMBOL = {
    "AUDJPY": "AUDJPY_FAMILY",
    "AUDUSD": "AUDUSD_FAMILY",
    "BTCUSD": "BTCUSD_FAMILY",
    "BTCUSD_CASH": "BTCUSD_FAMILY",
    "CADJPY": "CADJPY_FAMILY",
    "CHFJPY": "CHFJPY_FAMILY",
    "ETHUSD": "ETHUSD_FAMILY",
    "ETHUSD_CASH": "ETHUSD_FAMILY",
    "EURGBP": "EURGBP_FAMILY",
    "EURJPY": "EURJPY_FAMILY",
    "EURUSD": "EURUSD_6E_FAMILY",
    "EURUSD_6E": "EURUSD_6E_FAMILY",
    "6E": "EURUSD_6E_FAMILY",
    "M6E": "EURUSD_6E_FAMILY",
    "ES": "SPX500_ES_FAMILY",
    "MES": "SPX500_ES_FAMILY",
    "GBPUSD": "GBPUSD_6B_FAMILY",
    "GBPUSD_6B": "GBPUSD_6B_FAMILY",
    "6B": "GBPUSD_6B_FAMILY",
    "GER30": "GER40_FAMILY",
    "GER40": "GER40_FAMILY",
    "GER40_CASH": "GER40_FAMILY",
    "DE40": "GER40_FAMILY",
    "NAS100": "NAS100_NQ_FAMILY",
    "NAS100_CASH": "NAS100_NQ_FAMILY",
    "US100": "NAS100_NQ_FAMILY",
    "US100_CASH": "NAS100_NQ_FAMILY",
    "NDX100": "NAS100_NQ_FAMILY",
    "NAS100_MNQ": "NAS100_NQ_FAMILY",
    "NAS100_NQ": "NAS100_NQ_FAMILY",
    "NQ": "NAS100_NQ_FAMILY",
    "MNQ": "NAS100_NQ_FAMILY",
    "SPX500": "SPX500_ES_FAMILY",
    "US500": "SPX500_ES_FAMILY",
    "US500_CASH": "SPX500_ES_FAMILY",
    "US30": "US30_YM_FAMILY",
    "US30_CASH": "US30_YM_FAMILY",
    "US30_MYM": "US30_YM_FAMILY",
    "US30_YM": "US30_YM_FAMILY",
    "YM": "US30_YM_FAMILY",
    "MYM": "US30_YM_FAMILY",
    "JP225": "JP225_FAMILY",
    "JP225_CASH": "JP225_FAMILY",
    "JPN225": "JP225_FAMILY",
    "NIKKEI225": "JP225_FAMILY",
    "NZDJPY": "NZDJPY_FAMILY",
    "NZDUSD": "NZDUSD_FAMILY",
    "UK100": "UK100_FAMILY",
    "FTSE100": "UK100_FAMILY",
    "UKOIL": "UKOIL_FAMILY",
    "UKOIL_CASH": "UKOIL_FAMILY",
    "UKOUSD": "UKOIL_FAMILY",
    "BRENT": "UKOIL_FAMILY",
    "USDCAD": "USDCAD_FAMILY",
    "USDCHF": "USDCHF_FAMILY",
    "USDJPY": "USDJPY_6J_FAMILY",
    "USDJPY_6J": "USDJPY_6J_FAMILY",
    "6J": "USDJPY_6J_FAMILY",
    "USOIL": "USOIL_FAMILY",
    "USOIL_CASH": "USOIL_FAMILY",
    "USOUSD": "USOIL_FAMILY",
    "WTI": "USOIL_FAMILY",
    "XAUUSD": "XAUUSD_GC_FAMILY",
    "XAUUSD_GC": "XAUUSD_GC_FAMILY",
    "XAUUSD_MGC": "XAUUSD_GC_FAMILY",
    "GC": "XAUUSD_GC_FAMILY",
    "MGC": "XAUUSD_GC_FAMILY",
    "XAGUSD": "XAGUSD_SILVER_FAMILY",
    "XAGUSD_SILVER": "XAGUSD_SILVER_FAMILY",
    "XAGUSD_SI": "XAGUSD_SILVER_FAMILY",
    "XAGUSD_SIL": "XAGUSD_SILVER_FAMILY",
    "SI": "XAGUSD_SILVER_FAMILY",
    "SIL": "XAGUSD_SILVER_FAMILY",
}
FUTURES_MONTH_CODES = "FGHJKMNQUVXZ"
RUNTIME_SOURCE_COMPONENT_RE = re.compile(r"^[A-Za-z0-9_]+$")
ADVISORY_SCOPE_FIELDS = {
    "action_family",
    "action_class",
    "entry_variant",
    "proxy_r_class",
    "target_stop_order_class",
}
ROUTE_FAMILY_BY_FRAMEWORK = {
    "ob_retest": "ob_retest",
    "fvg_fill": "fvg_fill",
    "breaker_re_entry": "breaker_re_entry",
    "breaker_retest": "breaker_re_entry",
    "breaker_block_retest": "breaker_re_entry",
    "breaker_block": "breaker_re_entry",
    "breaker": "breaker_re_entry",
}
ROUTE_FAMILY_BY_EVIDENCE_TOKEN = (
    ("moonshot_mechanical", ("moonshot", "expanded_market_reduced_surface")),
    ("cp281_native_rule", ("cp281",)),
    ("mechanical_ai_selector", ("ai_narrowing_policy", "ai_decision_architecture")),
    ("numeric_router", ("numeric_router",)),
    ("nofill_mechanical", ("nofill_", "no_fill")),
    ("default_off_scorer", ("default_off", "scorer_registry_surface")),
)
DEFAULT_RISK_ZERO_BYPASS_EFFECTIVE_N_REASONS = (
    "vnext_risk_route_family_avoid_veto",
    "vnext_risk_source_component_avoid_veto",
    "vnext_risk_source_component_summary_adverse_prior",
    "vnext_risk_action_class_avoid_veto",
    "vnext_risk_evidence_family_avoid_veto",
    "vnext_risk_source_name_avoid_veto",
    "vnext_risk_source_role_avoid_veto",
    "vnext_risk_target_stop_not_source_bound",
    "vnext_risk_stop_first_proxy",
    "vnext_risk_source_acquisition_required",
    "vnext_risk_source_repair_required",
    "vnext_risk_recommendation_family_rollup_adverse_prior",
    "vnext_risk_recommendation_unified_candidate_adverse_prior",
    "vnext_risk_recommendation_scope_rollup_adverse_prior",
    "vnext_risk_strong_negative_proxy_class",
)
CP281_RESULT_TABLE_DIMENSION_FIELD_MAP = {
    "symbol": "symbol",
    "source_symbol": "source_symbol",
    "symbol_family": "symbol_family",
    "market": "market",
    "timeframe": "timeframe",
    "market_timeframe": "market_timeframe",
    "route_session": "route_session",
    "horizon_id": "horizon_id",
    "side": "side",
    "source_path_sha256": "source_path_sha256",
    "source_file_sha256": "source_file_sha256",
    "framework": "framework",
    "route_family": "route_family",
    "matched_action_class": "action_class",
    "action_class": "action_class",
}
CP281_RESULT_TABLE_COUNT_FIELD_MAP = {
    "source_symbol_counts": "source_symbol",
    "symbol_family_counts": "symbol_family",
    "market_timeframe_counts": "market_timeframe",
    "route_session_counts": "route_session",
    "horizon_counts": "horizon_id",
    "side_counts": "side",
    "action_class_counts": "action_class",
}
CP281_BRANCH_SCOPE_FIELD_MAP = {
    "symbol": "symbol",
    "source_symbol": "source_symbol",
    "symbol_family": "symbol_family",
    "market": "market",
    "timeframe": "timeframe",
    "market_timeframe": "market_timeframe",
    "route_session": "route_session",
    "horizon_id": "horizon_id",
    "side": "side",
    "source_path_sha256": "source_path_sha256",
    "source_file_sha256": "source_file_sha256",
    "framework": "framework",
    "route_family": "route_family",
    "action_class": "action_class",
}
FAILURE_INTELLIGENCE_SCAN_FIELDS = (
    "review_action",
    "action_class",
    "implementation_action",
    "evidence_family",
    "source_name",
    "source_group",
    "source_role",
    "system_surface",
    "r_evidence_class",
    "runtime_effect_now",
    "candidate_use_allowed_now",
    "runtime_candidate_use_permitted",
    "branch_decision",
    "decision_evidence",
    "strategy_status",
    "score_status",
    "source_decision_status",
    "result_use_status",
    "not_directly_convertible_reason",
    "missing_field_source",
    "next_code_config_test_action",
    "source_path",
    "source_artifact",
    "declared_origin_artifact",
    "drill_through_path",
    "missed_opportunity_audit",
)
DEFAULT_NON_EXECUTABLE_FAILURE_INTELLIGENCE_TOKENS = (
    "SOURCE_REPAIR",
    "SOURCE_CAPTURE_REQUIRED",
    "SOURCE_CAPTURE_REQUIREMENT",
    "SOURCE_JOIN_REPAIR_REQUIRED",
    "SOURCE_LIMITED",
    "SOURCE_BLOCKED",
    "MISSING_REQUIRED",
    "BROKER_EXECUTION_GEOMETRY_REQUIRED",
    "BROKER_GEOMETRY_ATTACHMENT_REQUIRED",
    "EXECUTE_SOURCE_GEOMETRY_REPAIR_SCOPE",
    "SOURCE_PACKET_CONTEXT_SELECTOR_EXECUTION_IDENTITY_ABSENT",
    "FAIL_CLOSED",
    "FAIL_CLOSED_OR_DOWNWEIGHT",
    "UNDERPOWERED",
    "UNPROVEN",
    "CONTROL_EXPLAINED",
    "DUPLICATE_AVOID_FILTER_PROXY_REFERENCE_NOT_COUNTED",
    "REFERENCE_ONLY",
    "NOT_COUNTED",
    "BOUNDED_AMBIGUOUS",
    "RESULT_MATERIALIZATION_REQUIRED",
    "REDESIGN_ONLY",
    "REPAIR_NEEDED",
)
DEFAULT_EXECUTABLE_FAILURE_AVOID_TOKENS = (
    "AVOID_FILTER",
    "INVERSE_FILTER",
    "FAILURE_FILTER",
    "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE",
    "REGISTER_DEFAULT_OFF_CP281_AVOID_FILTER_RULE",
    "CANONICAL_AVOID_FILTER_SAVED_R_OWNER",
)
DEFAULT_FAILURE_SOURCE_COMPLETE_FIELDS = (
    "source_complete",
    "source_bound",
)
DEFAULT_ORDERFLOW_DIAGNOSTIC_TOKENS = (
    "ORDERFLOW",
    "ORDER_FLOW",
    "FOOTPRINT",
    "DEPTH",
    "LADDER",
    "MBO",
    "MBP",
    "DATABENTO",
    "SCID",
    "FUTURES_PROXY_TRANSFER",
    "FUTURES_TO_CFD",
    "PROXY_TRANSFER",
    "QUEUE_POSITION",
    "ABSORPTION",
)
DEFAULT_ORDERFLOW_RUNTIME_VALIDATED_FIELDS = (
    "orderflow_runtime_validated",
    "proxy_transfer_validated",
    "futures_to_cfd_transfer_validated",
    "source_transfer_validated",
)
DEFAULT_ORDERFLOW_RUNTIME_READY_TOKENS = (
    "ORDERFLOW_RUNTIME_VALIDATED",
    "VALIDATED_FUTURES_PROXY_TRANSFER",
    "SYMBOL_PROXY_TRANSFER_VALIDATED",
)

CHALLENGER_FRONTIER_ACTION_DECISION_BY_STATUS = {
    "OHLC_FRONTIER_KILLED_BY_NEIGHBOR_OR_PERMUTED_PLACEBO": "AVOID",
    "OHLC_FRONTIER_GTOS_REPLAY_CONTRACT_READY_SOURCE_REPLAY_AND_COST_FILL": "MIXED",
    "OHLC_FRONTIER_SOURCE_TRANSFER_MECHANISM_IMPORT_READY": "MIXED",
    "OHLC_FRONTIER_CONTROL_COVERAGE_EXPANSION_REQUIRED": "MIXED",
    "OHLC_FRONTIER_RESILIENT_CROSS_MARKET_DIAGNOSTIC_OR_TRANSFER_REQUIRED": "MIXED",
    "OHLC_FRONTIER_TIME_SPLIT_SIGN_FRAGILE_REGIME_SPLIT_REQUIRED": "MIXED",
    "OHLC_FRONTIER_CLUSTER_WEIGHTED_SIGN_FRAGILE_SPLIT_REQUIRED": "MIXED",
    "OHLC_FRONTIER_DUPLICATE_CLUSTER_HEAVY_DEDUP_REQUIRED": "MIXED",
}

CONTROL_SCREEN_BUCKET_DECISION = {
    "MATERIAL_POSITIVE_DIRECTIONAL_CONTROL_DELTA": "FOLLOW",
    "MATERIAL_NEGATIVE_DIRECTIONAL_CONTROL_DELTA": "AVOID",
    "MATERIAL_MIXED_DIRECTIONAL_CONTROL_DELTA": "MIXED",
    "MATERIAL_CONTRACTION_AFTER_NEUTRAL_PRIMITIVE": "MIXED",
    "MATERIAL_EXPANSION_AFTER_NEUTRAL_PRIMITIVE": "MIXED",
    "SMALL_OR_CONCENTRATED_SAMPLE": "MIXED",
}

CONTROL_SCREEN_PRIMITIVE_SIDE = {
    "CLOSE_BREAKOUT_UP_16": "LONG",
    "CLOSE_BREAKOUT_DOWN_16": "SHORT",
    "SWEEP_LOW_CLOSE_BACK_INSIDE_16": "LONG",
    "SWEEP_HIGH_CLOSE_BACK_INSIDE_16": "SHORT",
    "RANGE_EXPANSION_UP": "LONG",
    "RANGE_EXPANSION_DOWN": "SHORT",
    "LOWER_WICK_EXHAUSTION": "LONG",
    "UPPER_WICK_EXHAUSTION": "SHORT",
    "RANGE_COMPRESSION": "",
}

GTOS_REPLAY_BLOCKER_IMPLEMENTATION_ACTIONS = {
    "future_or_sealed_holdout_required_after_discovery_window": (
        "SEALED_HOLDOUT_REPLAY_REQUIRED_BEFORE_PROMOTION"
    ),
    "entry_geometry_not_defined_by_ohlc_primitive": (
        "ENTRY_GEOMETRY_SOURCE_REPAIR_REQUIRED"
    ),
    "spread_slippage_commission_not_applied": (
        "COST_SLIPPAGE_COMMISSION_SOURCE_REPAIR_REQUIRED"
    ),
    "pending_lifecycle_fillability_not_modeled": (
        "PENDING_LIFECYCLE_FILLABILITY_SOURCE_REPAIR_REQUIRED"
    ),
    "no_live_behavior_change_without_owner_approval": (
        "LIVE_BEHAVIOR_OWNER_COMMAND_REQUIRED"
    ),
}

ACCEPTED_BUILDER_MIXED_CLASS_TOKENS = (
    "CONFLICT_SPLIT",
    "BOUNDS_SPLIT",
    "ENTRY_ADVERSE_REDESIGN",
    "EXACT_SOURCE_REPAIR",
)


def _normalized(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _match_key(value: Any) -> str:
    return _normalized(value).casefold()


def _canonical_session(value: Any) -> str:
    key = _match_key(value).replace("-", "_").replace(" ", "_")
    return SESSION_ALIASES.get(key, _normalized(value))


def _canonical_symbol_family(value: Any) -> str:
    raw = _normalized(value).upper()
    if not raw:
        return ""
    mapped = _symbol_family_for(raw) or raw
    return mapped.removesuffix("_FAMILY")


def _symbol_lookup_keys(value: Any) -> tuple[str, ...]:
    raw = _normalized(value).upper()
    if not raw:
        return ()
    underscored = raw.replace(".", "_").replace("-", "_").replace(" ", "_")
    compact = underscored.replace("_", "")
    return tuple(dict.fromkeys((raw, underscored, compact, *_futures_contract_roots(raw))))


def _futures_contract_roots(value: Any) -> tuple[str, ...]:
    raw = _normalized(value).upper()
    if not raw:
        return ()
    contract = re.split(r"[-_.\s]", raw, maxsplit=1)[0]
    match = re.match(rf"^([A-Z0-9]+?)([{FUTURES_MONTH_CODES}])(\d{{1,2}})$", contract)
    if not match:
        return ()
    return (match.group(1),)


def _symbol_family_for(symbol: Any) -> str:
    for key in _symbol_lookup_keys(symbol):
        if key in SYMBOL_FAMILY_BY_SYMBOL:
            return SYMBOL_FAMILY_BY_SYMBOL[key]
    return ""


def _event_symbol_family(event: dict[str, str]) -> str:
    for field in ("symbol_family", "source_symbol", "symbol", "market"):
        if family := _symbol_family_for(event.get(field)):
            return family
    return ""


def _compatible_event_market_symbol(
    *,
    symbol: str,
    source_symbol: str | None,
    configured_market: Any,
) -> str:
    """Keep runtime market scope on the evaluated instrument, not stale config."""
    if configured_market in (None, ""):
        return symbol
    for candidate in (symbol, source_symbol):
        if candidate and _field_values_match("market", configured_market, candidate):
            return _normalized(configured_market)
    return symbol


def resolve_vnext_symbol_family(symbol: Any) -> str:
    """Return the vNext symbol-family label implied by a broker/source symbol."""
    return _symbol_family_for(symbol)


def normalize_vnext_symbol_key(symbol: Any) -> str:
    """Return the canonical runtime symbol key used for vNext alias matching."""
    keys = _symbol_lookup_keys(symbol)
    for key in keys:
        if "_" in key:
            return key
    return keys[0] if keys else ""


def symbol_family_candidates_for_vnext(symbol: Any, *alternates: Any) -> tuple[str, ...]:
    """Return all vNext family candidates implied by current event symbols."""
    candidates: list[str] = []
    for value in (symbol, *alternates):
        family = _symbol_family_for(value)
        if family and family not in candidates:
            candidates.append(family)
    return tuple(candidates)


def _canonical_symbol_like_value(value: Any) -> str:
    family = _symbol_family_for(value)
    if family:
        return family.removesuffix("_FAMILY")
    return normalize_vnext_symbol_key(value)


def _route_family_for_framework(framework: Any) -> str:
    normalized = _normalized(framework).casefold()
    return ROUTE_FAMILY_BY_FRAMEWORK.get(normalized, _normalized(framework))


def _route_family_for_source_component(source_component: Any) -> str:
    component = _normalized(source_component).casefold()
    if component.startswith("nofill_"):
        return "nofill_mechanical"
    return "numeric_router"


def resolve_vnext_route_family(framework: Any) -> str:
    """Return the vNext route-family label implied by a framework name."""
    return _route_family_for_framework(framework)


def is_vnext_ai_enforceable_route_family(route_family: Any) -> bool:
    """Return whether an AI framework can emit this route-family directly."""
    return _normalized(route_family) in set(ROUTE_FAMILY_BY_FRAMEWORK.values())


def _canonical_field_value(field: str, value: Any) -> str:
    if field == "route_session":
        return _canonical_session(value)
    if field == "symbol_family":
        return _canonical_symbol_family(value)
    if field in {"symbol", "source_symbol", "market"}:
        return _canonical_symbol_like_value(value)
    if field in {"side", "market", "timeframe", "market_timeframe", "horizon_id", "framework", "route_family"}:
        return _normalized(value).upper()
    return _match_key(value)


def _field_values_match(field: str, expected: Any, actual: Any) -> bool:
    if expected in (None, ""):
        return False
    if field == "route_session" and _canonical_session(expected) == SESSION_WILDCARD:
        return actual not in (None, "")
    if actual in (None, ""):
        return False
    return _canonical_field_value(field, expected) == _canonical_field_value(field, actual)


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_numeric(*values: Any) -> float | None:
    for value in values:
        numeric = _to_float(value)
        if numeric is not None:
            return numeric
    return None


def _single_positive_count_key(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    positive_keys: list[str] = []
    for key, value in payload.items():
        if key in (None, ""):
            continue
        numeric = _to_float(value)
        if numeric is None:
            continue
        if numeric > 0:
            positive_keys.append(str(key))
    return positive_keys[0] if len(positive_keys) == 1 else ""


def _metric_from_scalar(value: Any, *, source_field: str) -> dict[str, Any] | None:
    numeric = _to_float(value)
    if numeric is None:
        return None
    return {
        "sum": numeric,
        "mean": numeric,
        "count": 1,
        "match_rows_with_metric": 1,
        "positive_rows": 1 if numeric > 0 else 0,
        "negative_rows": 1 if numeric < 0 else 0,
        "zero_rows": 1 if numeric == 0 else 0,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _metric_from_mean_count(
    mean_value: Any,
    count_value: Any,
    *,
    source_field: str,
) -> dict[str, Any] | None:
    mean = _to_float(mean_value)
    count = _to_float(count_value)
    if mean is None or count is None or count <= 0:
        return None
    metric_sum = mean * count
    return {
        "sum": metric_sum,
        "mean": mean,
        "count": count,
        "match_rows_with_metric": count,
        "positive_rows": count if mean > 0 else 0,
        "negative_rows": count if mean < 0 else 0,
        "zero_rows": count if mean == 0 else 0,
        "source_field": source_field,
        "source_shape": "mean_count",
    }


def _enrich_cp281_result_table_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert CP281 replay result-table rows into runtime-matchable evidence.

    CP281 result tables are aggregate replay rows: their scope lives in
    result_table_dimensions plus singleton count columns rather than top-level
    event_scope fields. Promoting those fields here lets the runtime consume
    the frozen replay rows directly without creating a new artifact layer.
    """
    if _normalized(row.get("row_type")) != "cp281_rule_replay_result_table":
        return row

    enriched = dict(row)
    enriched.setdefault("source_name", "cp281_rule_replay_result_table")
    enriched.setdefault("evidence_family", "cp281_native_rule_replay")
    enriched.setdefault("route_family", "cp281_native_rule")
    enriched.setdefault("source_role", "historical_replay_result_table")
    enriched.setdefault("source_row_id", enriched.get("row_key"))

    metrics = dict(enriched.get("r_metrics") or {})
    for metric in METRIC_NAMES:
        payload = enriched.get(metric)
        if isinstance(payload, dict):
            metrics.setdefault(metric, payload)
    if metrics:
        enriched["r_metrics"] = metrics

    scope: dict[str, Any] = {}
    dimensions = enriched.get("result_table_dimensions")
    if isinstance(dimensions, dict):
        for source_field, target_field in CP281_RESULT_TABLE_DIMENSION_FIELD_MAP.items():
            value = dimensions.get(source_field)
            if value not in (None, ""):
                scope[target_field] = value

    for count_field, target_field in CP281_RESULT_TABLE_COUNT_FIELD_MAP.items():
        if scope.get(target_field):
            continue
        value = _single_positive_count_key(enriched.get(count_field))
        if value:
            scope[target_field] = value

    if scope:
        existing_scope = enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
        enriched["event_scope"] = {**existing_scope, **scope}
        for field, value in scope.items():
            enriched.setdefault(field, value)

    surface = _single_positive_count_key(enriched.get("main_system_surface_counts"))
    if surface:
        enriched.setdefault("system_surface", surface)
    return enriched


def _enrich_cp281_ready_runtime_rule_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert CP281 member rule rows into runtime-matchable evidence."""
    if _normalized(row.get("row_type")) != "cp281_ready_runtime_rule_to_main_system_surface":
        return row

    enriched = dict(row)
    enriched.setdefault("source_name", "cp281_ready_runtime_rules")
    enriched.setdefault("evidence_family", "cp281_ready_runtime_rule")
    enriched.setdefault("route_family", "cp281_native_rule")
    enriched.setdefault("source_role", "cp281_ready_runtime_rule_registry")
    enriched.setdefault(
        "source_row_id",
        enriched.get("cp281_rule_row_id") or enriched.get("row_key"),
    )
    if enriched.get("implementation_decision") and not enriched.get("implementation_action"):
        enriched["implementation_action"] = enriched.get("implementation_decision")
    if enriched.get("main_system_surface") and not enriched.get("system_surface"):
        enriched["system_surface"] = enriched.get("main_system_surface")

    source_ownership = enriched.get("source_ownership")
    if isinstance(source_ownership, dict):
        enriched.setdefault("source_path", source_ownership.get("source_path"))
        enriched.setdefault("declared_origin_artifact", source_ownership.get("source_rule_artifact"))
        enriched.setdefault("declared_origin_line_no", source_ownership.get("source_rule_line_no"))

    metrics = dict(enriched.get("r_metrics") or {})
    for metric in METRIC_NAMES:
        payload = _metric_from_scalar(enriched.get(metric), source_field=metric)
        if payload:
            metrics.setdefault(metric, payload)
    if metrics:
        enriched["r_metrics"] = metrics

    scope: dict[str, Any] = {}
    match_scope = enriched.get("match_scope") if isinstance(enriched.get("match_scope"), dict) else {}
    for source_field, target_field in CP281_BRANCH_SCOPE_FIELD_MAP.items():
        value = match_scope.get(source_field, enriched.get(source_field))
        if value not in (None, ""):
            scope[target_field] = value
    if enriched.get("action_class") and not scope.get("action_class"):
        scope["action_class"] = enriched.get("action_class")
    scope.setdefault("route_family", enriched.get("route_family"))

    if scope:
        existing_scope = enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
        enriched["event_scope"] = {**existing_scope, **scope}
        for field, value in scope.items():
            enriched.setdefault(field, value)
    return enriched


def _enrich_cp281_branch_decision_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert CP281 branch-decision rows into runtime-matchable evidence."""
    if _normalized(row.get("row_type")) != "cp281_ready_runtime_branch_decision":
        return row

    enriched = dict(row)
    enriched.setdefault("source_name", "cp281_branch_decisions")
    enriched.setdefault("evidence_family", "cp281_ready_runtime_branch_decision")
    enriched.setdefault("route_family", "cp281_native_rule")
    enriched.setdefault("source_role", "cp281_branch_decision_registry")
    enriched.setdefault(
        "source_row_id",
        enriched.get("row_key") or enriched.get("cp281_aggregate_row_id"),
    )
    if enriched.get("branch_decision_action") and not enriched.get("implementation_action"):
        enriched["implementation_action"] = enriched.get("branch_decision_action")
    if enriched.get("main_system_surface") and not enriched.get("system_surface"):
        enriched["system_surface"] = enriched.get("main_system_surface")

    metrics = dict(enriched.get("r_metrics") or {})
    for metric in METRIC_NAMES:
        payload = enriched.get(metric)
        if isinstance(payload, dict):
            metrics.setdefault(metric, payload)
    if metrics:
        enriched["r_metrics"] = metrics

    scope: dict[str, Any] = {}
    aggregate_scope = enriched.get("aggregate_scope")
    if isinstance(aggregate_scope, dict):
        for source_field, target_field in CP281_BRANCH_SCOPE_FIELD_MAP.items():
            value = aggregate_scope.get(source_field)
            if value not in (None, ""):
                scope[target_field] = value
    if enriched.get("action_class") and not scope.get("action_class"):
        scope["action_class"] = enriched.get("action_class")
    scope.setdefault("route_family", enriched.get("route_family"))

    if scope:
        existing_scope = enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
        enriched["event_scope"] = {**existing_scope, **scope}
        for field, value in scope.items():
            enriched.setdefault(field, value)
    return enriched


def _enrich_cp281_ready_runtime_aggregate_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert CP281 aggregate rows into matchable fallback/provenance evidence."""
    if _normalized(row.get("row_type")) != "cp281_ready_runtime_aggregate_to_main_system_surface":
        return row

    enriched = dict(row)
    enriched.setdefault("source_name", "cp281_ready_runtime_aggregates")
    enriched.setdefault("evidence_family", "cp281_ready_runtime_aggregate")
    enriched.setdefault("route_family", "cp281_native_rule")
    enriched.setdefault("source_role", "cp281_aggregate_registry")
    enriched.setdefault(
        "source_row_id",
        enriched.get("row_key") or enriched.get("cp281_aggregate_row_id"),
    )
    if enriched.get("main_surface_action") and not enriched.get("implementation_action"):
        enriched["implementation_action"] = enriched.get("main_surface_action")
    if enriched.get("main_system_surface") and not enriched.get("system_surface"):
        enriched["system_surface"] = enriched.get("main_system_surface")
    enriched.setdefault("cp281_aggregate_provenance", _cp281_aggregate_provenance(enriched))
    enriched.setdefault("cp281_aggregate_source_row_count", enriched.get("source_row_count"))
    enriched.setdefault("cp281_aggregate_loaded_from", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("cp281_aggregate_row_key", enriched.get("row_key"))

    source_ownership = enriched.get("source_ownership")
    if isinstance(source_ownership, dict):
        enriched.setdefault("source_path", source_ownership.get("source_aggregate_artifact"))
        enriched.setdefault(
            "declared_origin_artifact",
            source_ownership.get("source_aggregate_artifact"),
        )
        enriched.setdefault(
            "declared_origin_sha256",
            source_ownership.get("source_aggregate_artifact_sha256"),
        )
        enriched.setdefault(
            "declared_origin_line_no",
            source_ownership.get("source_aggregate_line_no"),
        )

    metrics = dict(enriched.get("r_metrics") or {})
    metric_sources = {
        "cost_adjusted_simulated_r": "average_cost_adjusted_simulated_r",
        "stress_simulated_r": "average_stress_simulated_r",
        "effective_n": "effective_n_sum",
    }
    for metric, source_field in metric_sources.items():
        payload = _metric_from_scalar(enriched.get(source_field), source_field=source_field)
        if payload:
            metrics.setdefault(metric, payload)
    if metrics:
        enriched["r_metrics"] = metrics

    scope: dict[str, Any] = {}
    aggregate_scope = enriched.get("aggregate_scope")
    if isinstance(aggregate_scope, dict):
        for source_field, target_field in CP281_BRANCH_SCOPE_FIELD_MAP.items():
            value = aggregate_scope.get(source_field)
            if value not in (None, ""):
                scope[target_field] = value
    if enriched.get("action_class") and not scope.get("action_class"):
        scope["action_class"] = enriched.get("action_class")
    scope.setdefault("route_family", enriched.get("route_family"))

    if scope:
        existing_scope = enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
        enriched["event_scope"] = {**existing_scope, **scope}
        for field, value in scope.items():
            enriched.setdefault(field, value)
    return enriched


def _event_value(event: dict[str, Any], field: str) -> str:
    for alias in EVENT_FIELD_ALIASES.get(field, (field,)):
        if alias in event and event.get(alias) not in (None, ""):
            return _normalized(event.get(alias))
    return ""


def normalize_event(event: dict[str, Any]) -> dict[str, str]:
    """Return the canonical vNext event fields present in *event*."""
    normalized = {
        field: value
        for field in MATCH_FIELDS
        if (value := _event_value(event, field))
    }
    for field in EVENT_FILTER_FIELDS:
        if value := _event_value(event, field):
            normalized[field] = value
    if value := _event_value(event, "primitive"):
        normalized["primitive"] = value
    if "symbol_family" not in normalized:
        family = _event_symbol_family(normalized)
        if family:
            normalized["symbol_family"] = family
    if "route_family" not in normalized and normalized.get("framework"):
        route_family = _route_family_for_framework(normalized.get("framework"))
        if route_family:
            normalized["route_family"] = route_family
    return normalized


def _row_matches_event_filters(row: dict[str, Any], event: dict[str, str]) -> bool:
    for field in EVENT_FILTER_FIELDS:
        actual = event.get(field)
        if actual in (None, ""):
            continue
        expected = _row_dimension_value(row, field)
        if expected in (None, ""):
            return False
        if not _field_values_match(field, expected, actual):
            return False
    return True


def _row_scope(row: dict[str, Any]) -> dict[str, str]:
    scope = row.get("event_scope")
    if isinstance(scope, dict):
        return {
            field: _normalized(scope.get(field))
            for field in MATCH_FIELDS
            if _normalized(scope.get(field))
        }
    return {
        field: _normalized(row.get(field))
        for field in MATCH_FIELDS
        if _normalized(row.get(field))
    }


def _infer_route_family_from_row(row: dict[str, Any]) -> tuple[str, str]:
    """Infer route family only when artifacts omit an explicit route_family."""
    scope = row.get("event_scope") if isinstance(row.get("event_scope"), dict) else {}
    existing = _normalized(row.get("route_family") or scope.get("route_family"))
    if existing:
        return existing, "explicit"
    if _normalized(row.get("row_type")) != "gtos_vnext_evidence_to_system_matrix_row":
        return "", ""

    evidence_text = " ".join(
        _normalized(row.get(field) or scope.get(field))
        for field in (
            "source_name",
            "evidence_family",
            "source_component",
            "implementation_action",
            "system_surface",
            "source_group",
            "source_role",
            "declared_origin_artifact",
            "source_path",
        )
    ).casefold()
    for route_family, tokens in ROUTE_FAMILY_BY_EVIDENCE_TOKEN:
        if any(token in evidence_text for token in tokens):
            return route_family, "evidence_token"
    return "", ""


MOONSHOT_TARGET_STOP_ORDER_CLASS_BY_RESULT = {
    "STOP_FIRST_PROXY_DOMINANT": "STOP_FIRST_PROXY_DOMINANT",
    "TARGET_FIRST_PROXY_DOMINANT": "TARGET_FIRST_PROXY_DOMINANT",
    "ORDERING_AMBIGUITY_DOMINANT": "TARGET_STOP_AMBIGUOUS_OR_MIXED",
    "NO_FILL_OR_UNFILLED_DOMINANT": "TARGET_STOP_AMBIGUOUS_OR_MIXED",
    "NO_TARGET_STOP_TOUCH_DESCRIPTOR_DOMINANT": "TARGET_STOP_ORDER_NOT_SOURCE_BOUND",
    "NO_TARGET_STOP_RESULT_ENTRY_PROVENANCE_ONLY": "TARGET_STOP_ORDER_NOT_SOURCE_BOUND",
}
ACCEPTED_BUILDER_ENTRY_ADVERSE_TARGET_STOP_CLASS_BY_BALANCE = {
    "STOP_FIRST_COUNT_DOMINANT": "STOP_FIRST_PROXY_DOMINANT",
    "TARGET_FIRST_COUNT_DOMINANT": "TARGET_FIRST_PROXY_DOMINANT",
    "NO_FILL_COUNT_DOMINANT": "TARGET_STOP_AMBIGUOUS_OR_MIXED",
    "BALANCED_OR_TIED_COUNTS": "TARGET_STOP_AMBIGUOUS_OR_MIXED",
}
ACCEPTED_BUILDER_M15_TARGET_STOP_CLASS_BY_STATUS = {
    "M15_TARGET_FIRST_ACCEPTED_CONSERVATIVE_BOUND": "TARGET_FIRST_PROXY_DOMINANT",
    "M15_BOUNDS_SPLIT_ACCEPTED_POSITIVE_MIDPOINT": "TARGET_STOP_AMBIGUOUS_OR_MIXED",
    "M15_REJECTED_AVOID_OR_REDESIGN_REQUIRED": "STOP_FIRST_PROXY_DOMINANT",
    "M15_SIDE_CAR_CONTEXT_PRESERVED": "TARGET_STOP_AMBIGUOUS_OR_MIXED",
}
ACCEPTED_BUILDER_M1_SUPPORT_CLASS_BY_STATUS = {
    "M1_SUPPORT_STABLE_ACCEPTED": "M1_SUPPORT_STABLE_POSITIVE",
    "M1_SUPPORT_CONFLICT_SPLIT_ACCEPTED": "M1_SUPPORT_CONFLICT_SPLIT_POSITIVE",
    "M1_SIDE_CAR_CONTEXT_PRESERVED": "M1_SUPPORT_SIDECAR_CONTEXT",
}

ACCEPTED_BUILDER_POSITIVE_CLASS_BY_STATUS = {
    "POSITIVE_REPLAY_ACCEPTED_AFTER_MODIFIERS": "POSITIVE_REPLAY_ACCEPTED",
    "POSITIVE_REPAIR_OR_STRESS_REQUIRED_BEFORE_REPLAY": "POSITIVE_REPAIR_STRESS_REQUIRED",
    "POSITIVE_SIDE_CAR_CONTEXT_PRESERVED": "POSITIVE_SIDECAR_CONTEXT",
    "POSITIVE_REJECTED_OR_NONPOSITIVE": "POSITIVE_REJECTED_NONPOSITIVE",
}

ACCEPTED_BUILDER_SOURCE_CLASS_BY_STATUS = {
    "SOURCE_COST_CAP_ACCEPTED_EXACT_ACQUISITION_OPEN": "SOURCE_COST_CAP_ACCEPTED",
    "SOURCE_LOW_HIGH_BOUNDS_ACCEPTED_EXACT_ACQUISITION_OPEN": "SOURCE_LOW_HIGH_BOUNDS_ACCEPTED",
    "SOURCE_REJECTED_EXACT_SOURCE_REPAIR_REQUIRED": "SOURCE_REJECTED_REPAIR_REQUIRED",
    "SOURCE_LOW_HIGH_BOUNDS_REPAIR_REQUIRED": "SOURCE_BOUNDS_REPAIR_REQUIRED",
}

ACCEPTED_BUILDER_REJECTED_REPAIR_CLASS_BY_ACTION = {
    "AVOID_SOURCE_BRANCH_UNTIL_EXACT_SOURCE_REPAIR_OR_COST_MODEL_CHANGE": "REJECTED_REPAIR_SOURCE_AVOID",
    "BUILD_M15_AVOID_OR_REDESIGN_FILTER": "REJECTED_REPAIR_M15_AVOID",
    "REPAIR_SOURCE_OR_STRESS_POSITIVE_BRANCH_BEFORE_REPLAY": "REJECTED_REPAIR_POSITIVE_STRESS_CONTEXT",
    "PRESERVE_BINDING_PROVENANCE_ONLY": "REJECTED_REPAIR_BINDING_PROVENANCE",
    "PRESERVE_BINDING_NO_SCALAR_FILL": "REJECTED_REPAIR_BINDING_PROVENANCE",
    "PRESERVE_OR_KILL_ENTRY_ADVERSE_BRANCH": "REJECTED_REPAIR_ENTRY_ADVERSE_CONTEXT",
}

MARKET_GAP_SOURCE_EXPANSION_ACTIONS = {
    "BUILD_SOURCE_EXPANSION_FOR_SMALL_N_MARKET_GAP",
    "EXPAND_SOURCE_DENOMINATOR_BEFORE_BRANCH_DECISION",
    "MARKET_GAP_SOURCE_EXPANSION_SPEC",
    "MARKET_GAP_CODE_SOURCE_MATERIALIZATION_REQUIRED",
    "REDESIGN_SOURCE_ACQUISITION_BEFORE_IMPLEMENT",
}
MARKET_GAP_ENTRY_FOLLOW_ACTIONS = {
    "BUILD_ENTRY_GEOMETRY_FOR_SUPPORTIVE_MARKET_GAP",
    "MARKET_GAP_ENTRY_GEOMETRY_SCORE_NOW",
    "MARKET_GAP_CODE_IMPLEMENT_ENTRY_GEOMETRY_SPEC",
    "IMPLEMENT_ENTRY_GEOMETRY_CHALLENGER_CANDIDATE",
}
MARKET_GAP_ENTRY_CONTEXT_ACTIONS = {
    "BUILD_ENTRY_GEOMETRY_WITH_MIXED_ROUTER_FLAG",
    "MARKET_GAP_ENTRY_GEOMETRY_MIXED_ALIGNMENT_SCORE_WITH_CONTROL",
    "MARKET_GAP_CODE_SCORE_ENTRY_WITH_CONTROL",
    "SCORE_ENTRY_GEOMETRY_WITH_CONTROL_BEFORE_IMPLEMENT",
}
MARKET_GAP_AVOID_ACTIONS = {
    "BUILD_AVOID_INVERSE_CONTROL_FOR_WEAK_MARKET_GAP",
    "IMPLEMENT_MARKET_GAP_AVOID_INVERSE_CONTROL",
    "MARKET_GAP_AVOID_INVERSE_SPEC",
    "MARKET_GAP_AVOID_INVERSE_SCORE_NOW",
    "MARKET_GAP_CODE_IMPLEMENT_AVOID_FILTER_SPEC",
    "MARKET_GAP_CODE_SCORE_AVOID_INVERSE_WITH_CONTROL",
    "IMPLEMENT_AVOID_FILTER_CANDIDATE",
    "SCORE_AVOID_INVERSE_POLICY_WITH_CONTROL",
}

MOONSHOT_NUMERIC_FOLLOW_ACTIONS = {
    "KEEP_NOFILL_CHALLENGER_COMPARATOR_STRONG_POSITIVE",
    "KEEP_STRONG_POSITIVE_PROXY_R_WITH_CONTROL",
    "KEEP_POSITIVE_PROXY_R_WITH_CONTROL",
    "IMPLEMENT_DEFAULT_OFF_SCORER_RESEARCH_MODULE",
}
MOONSHOT_NUMERIC_AVOID_ACTIONS = {
    "CONVERT_STRONG_NEGATIVE_TO_AVOID_INVERSE_OR_FAILURE_FILTER",
}
MOONSHOT_NUMERIC_CONTEXT_ACTIONS = {
    "SOURCE_GEOMETRY_REPAIR_OR_GUARD_BINDING_REQUIRED",
    "MERGE_AS_CONTROL_CONTEXT_PENDING_EXACT_GEOMETRY",
    "KEEP_NEUTRAL_PROXY_AS_CONTEXT_OR_STRESS_CONTROL",
    "REDESIGN_NEGATIVE_PROXY_OR_MERGE_AS_CONTEXT_FEATURE",
    "REDESIGN_OR_REPLAY_REPAIR_REQUIRED_NO_NUMERIC_PROXY",
}
MOONSHOT_NUMERIC_PROXY_FIELDS = (
    "proxy_r_value",
    "decision_proxy_value",
    "expectancy_proxy_value",
    "pass_control_delta_proxy",
    "computed_proxy_delta",
)
MOONSHOT_EXACT_R_MISSING_PROOF_ACTION_BY_STATUS = {
    "EXACT_R_NOT_COMPUTABLE_MISSING_BROKER_EXECUTION_GEOMETRY": (
        "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R"
    ),
    "EXACT_R_NOT_COMPUTABLE_SOURCE_JOIN_ABSENT": "SOURCE_JOIN_REPAIR_REQUIRED",
    "EXACT_SPREAD_REPAIRED_PROXY_AVAILABLE_NOT_BROKER_EXACT_R": (
        "BROKER_GEOMETRY_ATTACHMENT_REQUIRED_FOR_EXACT_SPREAD_PROXY"
    ),
}


def _parse_mechanical_scope_key(value: Any) -> dict[str, str]:
    scope: dict[str, str] = {}
    for part in _normalized(value).split("|"):
        if "=" not in part:
            continue
        key, raw_value = part.split("=", 1)
        key = key.strip().casefold()
        normalized = raw_value.strip()
        if not normalized or normalized.casefold() in {"none", "null"}:
            continue
        if key == "session":
            key = "route_session"
        elif key == "horizon":
            key = "horizon_id"
        elif key == "primitive":
            key = "primitive_flag"
        if key in {"symbol", "route_session", "horizon_id", "primitive_flag"}:
            scope[key] = normalized
    return scope


def _metric_from_count_dict(payload: Any, *, source_field: str) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    values = [
        numeric
        for value in payload.values()
        if (numeric := _to_float(value)) is not None and numeric > 0
    ]
    if not values:
        return None
    effective_n = max(values)
    return {
        "sum": effective_n,
        "mean": effective_n,
        "count": 1,
        "match_rows_with_metric": 1,
        "positive_rows": 1,
        "negative_rows": 0,
        "zero_rows": 0,
        "source_field": source_field,
        "source_shape": "count_dict_max",
    }


def _moonshot_route_scope_from_route_candidate(
    row: dict[str, Any],
    *,
    source_component: str,
) -> dict[str, str]:
    route_candidate_id = _normalized(row.get("route_candidate_id"))
    parts = [part.strip() for part in route_candidate_id.split("|") if part.strip()]
    if len(parts) < 4:
        return {}

    route_symbol, route_session, route_pattern, horizon_id = parts[:4]
    symbol = _normalized(row.get("symbol")) or route_symbol
    session = _normalized(row.get("route_session")) or route_session
    pattern = route_pattern.casefold()
    side = _normalized(row.get("side")).upper()
    if side not in {"LONG", "SHORT"}:
        side = ""
    if "sweep_low" in pattern or "lower_wick" in pattern:
        side = "LONG"
    elif "sweep_high" in pattern or "upper_wick" in pattern:
        side = "SHORT"

    scope = {
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "route_session": session,
        "horizon_id": horizon_id,
        "route_family": "moonshot_mechanical",
        "source_component": source_component,
    }
    if family := _symbol_family_for(symbol):
        scope["symbol_family"] = family
    if side:
        scope["side"] = side
    return scope


def _challenger_frontier_scope_from_route_candidate(
    row: dict[str, Any],
    *,
    source_component: str = "ohlc_challenger_frontier_action",
) -> dict[str, str]:
    route_candidate_id = _normalized(row.get("route_candidate_id"))
    parts = [part.strip() for part in route_candidate_id.split("|") if part.strip()]
    if len(parts) < 4:
        return {}

    symbol, route_session, primitive, horizon_id = parts[:4]
    primitive_lower = primitive.casefold()
    side = ""
    if (
        "sweep_low" in primitive_lower
        or "lower_wick" in primitive_lower
        or "close_breakout_up" in primitive_lower
        or "range_expansion_up" in primitive_lower
    ):
        side = "LONG"
    elif (
        "sweep_high" in primitive_lower
        or "upper_wick" in primitive_lower
        or "close_breakout_down" in primitive_lower
        or "range_expansion_down" in primitive_lower
    ):
        side = "SHORT"

    scope = {
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "route_session": route_session,
        "horizon_id": horizon_id,
        "primitive": primitive,
        "route_family": "moonshot_mechanical",
        "source_component": source_component,
    }
    if family := _symbol_family_for(symbol):
        scope["symbol_family"] = family
    if side:
        scope["side"] = side
    return scope


def _challenger_frontier_action_decision(row: dict[str, Any]) -> DecisionLabel:
    status = _normalized(row.get("frontier_status")).upper()
    action_family = _normalized(row.get("action_family")).casefold()
    if action_family == "placebo_fail":
        return "AVOID"
    decision = CHALLENGER_FRONTIER_ACTION_DECISION_BY_STATUS.get(status)
    if decision in {"FOLLOW", "AVOID", "MIXED"}:
        return decision  # type: ignore[return-value]
    return "MIXED"


def _control_screen_side(row: dict[str, Any]) -> str:
    sign = _to_float(row.get("expected_sign"))
    if sign is not None:
        if sign > 0:
            return "LONG"
        if sign < 0:
            return "SHORT"
        return ""
    primitive = _normalized(row.get("primitive_id")).upper()
    return CONTROL_SCREEN_PRIMITIVE_SIDE.get(primitive, "")


def _control_screen_expected_sign(row: dict[str, Any]) -> int:
    sign = _to_float(row.get("expected_sign"))
    if sign is not None:
        if sign > 0:
            return 1
        if sign < 0:
            return -1
        return 0
    side = _control_screen_side(row)
    if side == "LONG":
        return 1
    if side == "SHORT":
        return -1
    return 0


def _control_screen_horizon_id(row: dict[str, Any]) -> str:
    horizon = _to_float(row.get("horizon_bars"))
    if horizon is None:
        return ""
    if float(horizon).is_integer():
        return f"h{int(horizon)}"
    return f"h{horizon:g}"


def _control_screen_decision(row: dict[str, Any]) -> DecisionLabel:
    bucket = _normalized(row.get("screen_bucket")).upper()
    decision = CONTROL_SCREEN_BUCKET_DECISION.get(bucket)
    if decision in {"FOLLOW", "AVOID", "MIXED"}:
        return decision  # type: ignore[return-value]
    return "MIXED"


def _control_screen_route_queue_decision(row: dict[str, Any]) -> DecisionLabel:
    bucket = _normalized(row.get("screen_bucket")).upper()
    if bucket == "MATERIAL_POSITIVE_DIRECTIONAL_CONTROL_DELTA":
        return "FOLLOW"
    return "MIXED"


def _enrich_moonshot_control_screen_route_queue_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert CP280 control-screen route-queue rows into exact route evidence."""
    if _normalized(row.get("evidence_class")).upper() != "HISTORICAL_OHLC_CONTROL_SCREEN_ROUTE_QUEUE":
        return row
    if not row.get("symbol") or not row.get("session") or not row.get("primitive_id"):
        return row

    enriched = dict(row)
    decision = _control_screen_route_queue_decision(enriched)
    bucket = _normalized(enriched.get("screen_bucket")).upper()
    if decision == "FOLLOW":
        action_class = "follow_scorer"
        r_evidence_class = "CONTROL_SCREEN_ROUTE_QUEUE_POSITIVE_DIRECTIONAL_PROXY"
        implementation_action = "OHLC_CONTROL_SCREEN_ROUTE_QUEUE_POSITIVE_DIRECTIONAL_FOLLOW_SCORER"
        runtime_effect = "route_queue_follow_scorer"
        source_role = "same_context_route_queue_positive_directional"
    else:
        action_class = "market_timeframe_router"
        r_evidence_class = "CONTROL_SCREEN_ROUTE_QUEUE_NEUTRAL_EXPANSION_PROXY"
        implementation_action = "OHLC_CONTROL_SCREEN_ROUTE_QUEUE_NEUTRAL_EXPANSION_CONTEXT_ROUTER"
        runtime_effect = "route_queue_context_router"
        source_role = "same_context_route_queue_neutral_expansion"

    scope_payload = {
        "symbol": enriched.get("symbol"),
        "source_symbol": enriched.get("symbol"),
        "route_session": enriched.get("session"),
        "horizon_id": _control_screen_horizon_id(enriched),
        "primitive": enriched.get("primitive_id"),
        "route_family": "moonshot_control_screen_route_queue",
        "source_component": "ohlc_control_screen_route_queue",
        "action_class": action_class,
    }
    if family := _symbol_family_for(enriched.get("symbol")):
        scope_payload["symbol_family"] = family
    if side := _control_screen_side(enriched):
        scope_payload["side"] = side
    scope_payload = {
        key: value for key, value in scope_payload.items()
        if value not in (None, "")
    }
    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope_payload}
    for field, value in scope_payload.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("route_candidate_id") or (
        f"{enriched.get('symbol')}|{enriched.get('session')}|"
        f"{enriched.get('primitive_id')}|{_control_screen_horizon_id(enriched)}"
    )
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_control_screen_route_queue"
    enriched["evidence_family"] = "moonshot_control_screen_route_queue"
    enriched["source_group"] = "historical_ohlc_control_screen_route_queue"
    enriched["source_role"] = source_role
    enriched["system_surface"] = "vnext_control_screen_route_queue_router"
    enriched["source_component"] = "ohlc_control_screen_route_queue"
    enriched["route_family"] = "moonshot_control_screen_route_queue"
    enriched["review_action"] = decision
    enriched["action_class"] = action_class
    enriched["implementation_action"] = implementation_action
    enriched["r_evidence_class"] = r_evidence_class
    enriched["runtime_effect_now"] = runtime_effect
    enriched["candidate_use_allowed_now"] = decision == "FOLLOW"
    enriched["runtime_candidate_use_permitted"] = decision == "FOLLOW"
    enriched["source_bound"] = True
    enriched["source_complete"] = True
    enriched["expected_sign_inferred"] = _control_screen_expected_sign(enriched)
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    proxy_source = (
        "delta_mean_directional_close_units"
        if enriched.get("delta_mean_directional_close_units") is not None
        else "delta_total_excursion_units"
    )
    proxy = _metric_from_scalar(enriched.get(proxy_source), source_field=proxy_source)
    if proxy:
        metrics.setdefault("proxy_score", proxy)
    effective_n = _metric_from_scalar(
        enriched.get("unique_dates") or enriched.get("event_count"),
        source_field="control_screen_route_queue_unique_dates",
    )
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _enrich_moonshot_gtos_replay_blocker_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert route-level replay blockers into exact source-repair risk guards."""
    if _normalized(row.get("evidence_class")).upper() != "HISTORICAL_OHLC_GTOS_REPLAY_BLOCKER":
        return row
    if not row.get("route_candidate_id") or not row.get("blocker_id"):
        return row

    enriched = dict(row)
    scope = _challenger_frontier_scope_from_route_candidate(
        enriched,
        source_component="gtos_replay_blocker",
    )
    if not scope:
        return enriched
    scope["route_family"] = "moonshot_gtos_replay_blocker"

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    blocker_id = _normalized(enriched.get("blocker_id")).casefold()
    row_id = f"{enriched.get('route_candidate_id')}|{blocker_id}"
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_gtos_replay_blocker"
    enriched["evidence_family"] = "moonshot_gtos_replay_blocker"
    enriched["source_group"] = "source_repair_proof"
    enriched["source_role"] = "exact_r_source_repair_proof"
    enriched["system_surface"] = "source_repair_proof"
    enriched["source_component"] = "gtos_replay_blocker"
    enriched["route_family"] = "moonshot_gtos_replay_blocker"
    enriched["review_action"] = "MIXED"
    enriched["action_class"] = "source_repair_guard"
    enriched["implementation_action"] = GTOS_REPLAY_BLOCKER_IMPLEMENTATION_ACTIONS.get(
        blocker_id,
        "REPLAY_BLOCKER_SOURCE_REPAIR_REQUIRED",
    )
    enriched["r_evidence_class"] = "SOURCE_REPAIR_FOR_EXACT_R"
    enriched["runtime_effect_now"] = "risk_block_until_replay_blockers_repaired"
    enriched["candidate_use_allowed_now"] = False
    enriched["runtime_candidate_use_permitted"] = False
    enriched["source_bound"] = True
    enriched["source_complete"] = False
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    effective_n = _metric_from_scalar(1, source_field="gtos_replay_blocker_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _accepted_builder_decision(row: dict[str, Any]) -> DecisionLabel:
    branch_class = _normalized(row.get("branch_decision_class")).upper()
    selector_action = _normalized(row.get("primary_selector_action")).upper()
    if any(token in branch_class for token in ACCEPTED_BUILDER_MIXED_CLASS_TOKENS):
        return "MIXED"
    if "REDESIGN" in selector_action or "SOURCE_REPAIR" in selector_action:
        return "MIXED"
    if _truthy(row.get("accepted_for_next_executable_builder")):
        return "FOLLOW"
    return "MIXED"


def _accepted_builder_action_class(row: dict[str, Any], decision: DecisionLabel) -> str:
    branch_class = _normalized(row.get("branch_decision_class")).upper()
    export_family = _normalized(row.get("primary_export_family")).upper()
    selector_action = _normalized(row.get("primary_selector_action")).upper()
    if "ENTRY_ADVERSE" in branch_class or "REDESIGN" in selector_action:
        return "execution_geometry_redesign"
    if "SOURCE" in export_family or "EXACT_SOURCE" in branch_class:
        return "source_acquisition_router"
    if export_family in {"M1", "M15"}:
        return "market_timeframe_router"
    if decision == "FOLLOW":
        return "follow_scorer"
    return "accepted_builder_context"


def _accepted_builder_proxy_r_class(score: Any, decision: DecisionLabel) -> str:
    numeric = _to_float(score)
    if decision == "MIXED":
        return "BOUNDED_AMBIGUOUS_PROXY_R"
    if numeric is None:
        return ""
    if numeric >= 0.5:
        return "STRONG_POSITIVE_PROXY_R"
    if numeric > 0:
        return "POSITIVE_PROXY_R"
    if numeric <= -0.5:
        return "STRONG_NEGATIVE_PROXY_R"
    if numeric < 0:
        return "NEGATIVE_PROXY_R"
    return "FLAT_PROXY_R"


def _enrich_moonshot_accepted_builder_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert accepted next-layer builder rows into runtime selector evidence."""
    if not row.get("accepted_builder_result_id") or not row.get("branch_queue_id"):
        return row
    if _normalized(row.get("branch_result_binary")).upper() != "ACCEPTED":
        return row
    if not row.get("route_candidate_id"):
        return row

    enriched = dict(row)
    scope = _challenger_frontier_scope_from_route_candidate(
        enriched,
        source_component="gtos_accepted_builder",
    )
    if not scope:
        return enriched
    scope["route_family"] = "moonshot_accepted_builder"
    if side := _normalized(enriched.get("side")).upper():
        if side in {"LONG", "SHORT"}:
            scope["side"] = side

    decision = _accepted_builder_decision(enriched)
    action_class = _accepted_builder_action_class(enriched, decision)
    target_stop_result = _normalized(enriched.get("target_stop_result")).upper()
    target_stop_order_class = MOONSHOT_TARGET_STOP_ORDER_CLASS_BY_RESULT.get(
        target_stop_result,
        "TARGET_STOP_AMBIGUOUS_OR_MIXED",
    )
    proxy_r_class = _accepted_builder_proxy_r_class(
        enriched.get("next_layer_composite_score"),
        decision,
    )

    scope["action_class"] = action_class
    if target_stop_order_class:
        scope["target_stop_order_class"] = target_stop_order_class
    if proxy_r_class:
        scope["proxy_r_class"] = proxy_r_class

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("accepted_builder_result_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_accepted_builder"
    enriched["evidence_family"] = "moonshot_accepted_builder"
    enriched["source_group"] = (
        "accepted_builder_positive_proxy"
        if decision == "FOLLOW"
        else "accepted_builder_split_or_redesign_context"
    )
    enriched["source_role"] = "accepted_next_layer_builder_selector"
    enriched["system_surface"] = "accepted_builder_runtime_selector"
    enriched["source_component"] = "gtos_accepted_builder"
    enriched["route_family"] = "moonshot_accepted_builder"
    enriched["review_action"] = decision
    enriched["action_class"] = action_class
    enriched["proxy_r_class"] = proxy_r_class
    enriched["target_stop_order_class"] = target_stop_order_class
    enriched["implementation_action"] = (
        enriched.get("next_layer_branch_action")
        or enriched.get("branch_system_recommendation")
        or "RUN_ACCEPTED_NEXT_LAYER_BUILDER"
    )
    enriched["r_evidence_class"] = (
        "ACCEPTED_BUILDER_POSITIVE_PROXY"
        if decision == "FOLLOW"
        else "ACCEPTED_BUILDER_SPLIT_OR_REDESIGN_CONTEXT"
    )
    enriched["runtime_effect_now"] = (
        "accepted_builder_follow_selector"
        if decision == "FOLLOW"
        else "accepted_builder_split_or_redesign_router"
    )
    enriched["candidate_use_allowed_now"] = decision == "FOLLOW"
    enriched["runtime_candidate_use_permitted"] = decision == "FOLLOW"
    enriched["source_bound"] = True
    enriched["source_complete"] = decision == "FOLLOW"
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    proxy = _metric_from_scalar(
        enriched.get("next_layer_composite_score"),
        source_field="next_layer_composite_score",
    )
    if proxy:
        metrics.setdefault("proxy_score", proxy)
    stress = _metric_from_scalar(
        enriched.get("proxy_score_delta_vs_actionability"),
        source_field="proxy_score_delta_vs_actionability",
    )
    if stress:
        metrics.setdefault("stress_simulated_r", stress)
    effective_n = _metric_from_scalar(1, source_field="accepted_builder_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _enrich_moonshot_accepted_builder_binding_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert accepted-builder binding/no-scalar rows into exact route guards."""
    if not row.get("binding_builder_result_id") or not row.get("route_candidate_id"):
        return row
    if not _truthy(row.get("no_scalar_fill")):
        return row

    enriched = dict(row)
    scope = _challenger_frontier_scope_from_route_candidate(
        enriched,
        source_component="gtos_accepted_builder_binding",
    )
    if not scope:
        return enriched
    scope["route_family"] = "moonshot_accepted_builder_binding"
    if side := _normalized(enriched.get("side")).upper():
        if side in {"LONG", "SHORT"}:
            scope["side"] = side
    scope["action_class"] = "context_guard"
    scope["target_stop_order_class"] = "TARGET_STOP_ORDER_NOT_SOURCE_BOUND"

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("binding_builder_result_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_accepted_builder_binding"
    enriched["evidence_family"] = "moonshot_accepted_builder_binding"
    enriched["source_group"] = "accepted_builder_binding_no_scalar"
    enriched["source_role"] = "binding_provenance_no_scalar_fill"
    enriched["system_surface"] = "accepted_builder_binding_no_scalar_guard"
    enriched["source_component"] = "gtos_accepted_builder_binding"
    enriched["route_family"] = "moonshot_accepted_builder_binding"
    enriched["review_action"] = "MIXED"
    enriched["action_class"] = "context_guard"
    enriched["target_stop_order_class"] = "TARGET_STOP_ORDER_NOT_SOURCE_BOUND"
    enriched["implementation_action"] = (
        enriched.get("binding_builder_next_action")
        or "PRESERVE_BINDING_NO_SCALAR_FILL"
    )
    enriched["r_evidence_class"] = "ACCEPTED_BUILDER_BINDING_NO_SCALAR_FILL"
    enriched["runtime_effect_now"] = "accepted_builder_binding_no_scalar_guard"
    enriched["candidate_use_allowed_now"] = False
    enriched["runtime_candidate_use_permitted"] = False
    enriched["source_bound"] = True
    enriched["source_complete"] = False
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    effective_n = _metric_from_scalar(1, source_field="accepted_builder_binding_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _accepted_builder_branch_decision(row: dict[str, Any]) -> DecisionLabel:
    status = _normalized(row.get("branch_result_binary")).upper()
    branch_class = _normalized(row.get("branch_decision_class")).upper()
    recommendation = _normalized(row.get("branch_system_recommendation")).upper()
    if status == "REJECTED":
        if "BINDING_PROVENANCE_ONLY" in branch_class:
            return "MIXED"
        if "REPAIR_SOURCE_OR_STRESS" in recommendation:
            return "MIXED"
        return "AVOID"
    return "MIXED"


def _enrich_moonshot_accepted_builder_branch_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert branch-ledger rejected rows into route-scoped avoid evidence."""
    if not row.get("accepted_builder_branch_result_id") or not row.get("route_candidate_id"):
        return row
    if row.get("accepted_builder_result_id") or row.get("binding_builder_result_id"):
        return row

    enriched = dict(row)
    branch_status = _normalized(enriched.get("branch_result_binary")).upper()
    if branch_status != "REJECTED":
        enriched["event_scope"] = {}
        enriched["source_name"] = "moonshot_accepted_builder_branch"
        enriched["evidence_family"] = "moonshot_accepted_builder_branch"
        enriched["source_group"] = "accepted_branch_absorbed_by_accepted_builder_selector"
        enriched["source_role"] = "accepted_branch_duplicate_context"
        enriched["system_surface"] = "accepted_builder_branch_duplicate_absorbed"
        enriched["review_action"] = "MIXED"
        enriched["runtime_effect_now"] = "absorbed_by_unit568_accepted_builder_selector"
        enriched["candidate_use_allowed_now"] = False
        enriched["runtime_candidate_use_permitted"] = False
        enriched["source_bound"] = True
        enriched["source_complete"] = False
        return enriched
    branch_class = _normalized(enriched.get("branch_decision_class")).upper()
    if "BINDING_PROVENANCE_ONLY" in branch_class:
        enriched["event_scope"] = {}
        enriched["source_name"] = "moonshot_accepted_builder_branch"
        enriched["evidence_family"] = "moonshot_accepted_builder_branch"
        enriched["source_group"] = "binding_branch_absorbed_by_binding_guard"
        enriched["source_role"] = "binding_branch_duplicate_context"
        enriched["system_surface"] = "accepted_builder_branch_duplicate_absorbed"
        enriched["review_action"] = "MIXED"
        enriched["runtime_effect_now"] = "absorbed_by_unit569_binding_no_scalar_guard"
        enriched["candidate_use_allowed_now"] = False
        enriched["runtime_candidate_use_permitted"] = False
        enriched["source_bound"] = True
        enriched["source_complete"] = False
        return enriched

    scope = _challenger_frontier_scope_from_route_candidate(
        enriched,
        source_component="gtos_accepted_builder_branch",
    )
    if not scope:
        return enriched
    scope["route_family"] = "moonshot_accepted_builder_branch"
    if side := _normalized(enriched.get("side")).upper():
        if side in {"LONG", "SHORT"}:
            scope["side"] = side

    decision = _accepted_builder_branch_decision(enriched)
    target_stop_result = _normalized(enriched.get("target_stop_result")).upper()
    target_stop_order_class = MOONSHOT_TARGET_STOP_ORDER_CLASS_BY_RESULT.get(
        target_stop_result,
        "TARGET_STOP_AMBIGUOUS_OR_MIXED",
    )
    action_class = "avoid_filter" if decision == "AVOID" else "context_guard"
    scope["action_class"] = action_class
    scope["target_stop_order_class"] = target_stop_order_class

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("accepted_builder_branch_result_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_accepted_builder_branch"
    enriched["evidence_family"] = "moonshot_accepted_builder_branch"
    enriched["source_group"] = (
        "accepted_builder_branch_rejected_avoid"
        if decision == "AVOID"
        else "accepted_builder_branch_repair_context"
    )
    enriched["source_role"] = "rejected_branch_selector_filter"
    enriched["system_surface"] = "accepted_builder_branch_runtime_filter"
    enriched["source_component"] = "gtos_accepted_builder_branch"
    enriched["route_family"] = "moonshot_accepted_builder_branch"
    enriched["review_action"] = decision
    enriched["action_class"] = action_class
    enriched["target_stop_order_class"] = target_stop_order_class
    enriched["implementation_action"] = (
        enriched.get("next_layer_branch_action")
        or enriched.get("branch_system_recommendation")
        or "REJECT_ACCEPTED_BUILDER_BRANCH"
    )
    enriched["r_evidence_class"] = (
        "ACCEPTED_BUILDER_BRANCH_REJECTED_AVOID"
        if decision == "AVOID"
        else "ACCEPTED_BUILDER_BRANCH_REPAIR_CONTEXT"
    )
    enriched["runtime_effect_now"] = (
        "accepted_builder_branch_avoid_filter"
        if decision == "AVOID"
        else "accepted_builder_branch_repair_context"
    )
    enriched["candidate_use_allowed_now"] = decision == "AVOID"
    enriched["runtime_candidate_use_permitted"] = decision == "AVOID"
    enriched["source_bound"] = True
    enriched["source_complete"] = decision == "AVOID"
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    proxy = _metric_from_scalar(
        enriched.get("primary_selector_score"),
        source_field="primary_selector_score",
    )
    if proxy:
        metrics.setdefault("proxy_score", proxy)
    stress = _metric_from_scalar(
        enriched.get("next_layer_composite_score"),
        source_field="next_layer_composite_score",
    )
    if stress:
        metrics.setdefault("stress_simulated_r", stress)
    effective_n = _metric_from_scalar(1, source_field="accepted_builder_branch_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _accepted_builder_entry_adverse_decision(row: dict[str, Any]) -> DecisionLabel:
    status = _normalized(row.get("entry_adverse_builder_result_status")).upper()
    balance = _normalized(row.get("entry_target_stop_balance_class")).upper()
    if status == "ENTRY_ADVERSE_REJECTED_NONPOSITIVE":
        return "AVOID"
    if balance == "TARGET_FIRST_COUNT_DOMINANT":
        return "FOLLOW"
    if balance in {"STOP_FIRST_COUNT_DOMINANT", "NO_FILL_COUNT_DOMINANT"}:
        return "AVOID"
    return "MIXED"


def _accepted_builder_entry_adverse_action_class(row: dict[str, Any]) -> str:
    balance = _normalized(row.get("entry_target_stop_balance_class")).upper()
    status = _normalized(row.get("entry_adverse_builder_result_status")).upper()
    if status == "ENTRY_ADVERSE_REJECTED_NONPOSITIVE":
        return "entry_adverse_rejected_avoid"
    if balance == "TARGET_FIRST_COUNT_DOMINANT":
        return "follow_scorer"
    if balance == "NO_FILL_COUNT_DOMINANT":
        return "entry_adverse_nofill_avoid"
    if balance == "STOP_FIRST_COUNT_DOMINANT":
        return "entry_adverse_stop_first_avoid"
    return "context_guard"


def _accepted_builder_entry_adverse_source_group(row: dict[str, Any]) -> str:
    balance = _normalized(row.get("entry_target_stop_balance_class")).upper()
    status = _normalized(row.get("entry_adverse_builder_result_status")).upper()
    if status == "ENTRY_ADVERSE_REJECTED_NONPOSITIVE":
        return "accepted_builder_entry_adverse_rejected_avoid"
    if balance == "TARGET_FIRST_COUNT_DOMINANT":
        return "accepted_builder_entry_adverse_target_first_follow"
    if balance == "STOP_FIRST_COUNT_DOMINANT":
        return "accepted_builder_entry_adverse_stop_first_avoid"
    if balance == "NO_FILL_COUNT_DOMINANT":
        return "accepted_builder_entry_adverse_nofill_avoid"
    return "accepted_builder_entry_adverse_balanced_context"


def _accepted_builder_entry_adverse_r_evidence_class(row: dict[str, Any]) -> str:
    balance = _normalized(row.get("entry_target_stop_balance_class")).upper()
    status = _normalized(row.get("entry_adverse_builder_result_status")).upper()
    if status == "ENTRY_ADVERSE_REJECTED_NONPOSITIVE":
        return "ACCEPTED_BUILDER_ENTRY_ADVERSE_REJECTED_NONPOSITIVE"
    if balance == "TARGET_FIRST_COUNT_DOMINANT":
        return "ACCEPTED_BUILDER_ENTRY_ADVERSE_TARGET_FIRST_PROXY"
    if balance == "STOP_FIRST_COUNT_DOMINANT":
        return "ACCEPTED_BUILDER_ENTRY_ADVERSE_STOP_FIRST_PROXY"
    if balance == "NO_FILL_COUNT_DOMINANT":
        return "ACCEPTED_BUILDER_ENTRY_ADVERSE_NOFILL_PROXY"
    return "ACCEPTED_BUILDER_ENTRY_ADVERSE_BALANCED_CONTEXT"


def _enrich_moonshot_accepted_builder_entry_adverse_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert entry/adverse accepted-builder rows into path-quality runtime evidence."""
    if not row.get("entry_adverse_builder_result_id") or not row.get("route_candidate_id"):
        return row

    enriched = dict(row)
    scope = _challenger_frontier_scope_from_route_candidate(
        enriched,
        source_component="gtos_accepted_builder_entry_adverse",
    )
    if not scope:
        return enriched
    scope["route_family"] = "moonshot_accepted_builder_entry_adverse"
    if side := _normalized(enriched.get("side")).upper():
        if side in {"LONG", "SHORT"}:
            scope["side"] = side

    decision = _accepted_builder_entry_adverse_decision(enriched)
    action_class = _accepted_builder_entry_adverse_action_class(enriched)
    balance = _normalized(enriched.get("entry_target_stop_balance_class")).upper()
    target_stop_order_class = ACCEPTED_BUILDER_ENTRY_ADVERSE_TARGET_STOP_CLASS_BY_BALANCE.get(
        balance,
        "TARGET_STOP_AMBIGUOUS_OR_MIXED",
    )
    score = _to_float(enriched.get("entry_adverse_builder_score"))
    if decision == "FOLLOW":
        proxy_r_class = (
            "POSITIVE_PROXY_R" if score is None or score < 0.5 else "STRONG_POSITIVE_PROXY_R"
        )
    elif decision == "AVOID":
        proxy_r_class = (
            "NEGATIVE_PROXY_R" if score is None or score > -0.5 else "STRONG_NEGATIVE_PROXY_R"
        )
    else:
        proxy_r_class = "BOUNDED_AMBIGUOUS_PROXY_R"

    scope["action_class"] = action_class
    scope["target_stop_order_class"] = target_stop_order_class
    scope["proxy_r_class"] = proxy_r_class

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("entry_adverse_builder_result_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_accepted_builder_entry_adverse"
    enriched["evidence_family"] = "moonshot_accepted_builder_entry_adverse"
    enriched["source_group"] = _accepted_builder_entry_adverse_source_group(enriched)
    enriched["source_role"] = "entry_adverse_path_quality_runtime_surface"
    enriched["system_surface"] = "accepted_builder_entry_adverse_geometry_runtime"
    enriched["source_component"] = "gtos_accepted_builder_entry_adverse"
    enriched["route_family"] = "moonshot_accepted_builder_entry_adverse"
    enriched["review_action"] = decision
    enriched["action_class"] = action_class
    enriched["proxy_r_class"] = proxy_r_class
    enriched["target_stop_order_class"] = target_stop_order_class
    enriched["implementation_action"] = (
        enriched.get("entry_adverse_builder_next_action")
        or "PRESERVE_ENTRY_ADVERSE_PATH_QUALITY_CONTEXT"
    )
    enriched["r_evidence_class"] = _accepted_builder_entry_adverse_r_evidence_class(enriched)
    enriched["runtime_effect_now"] = (
        "accepted_builder_entry_adverse_target_first_follow"
        if decision == "FOLLOW"
        else "accepted_builder_entry_adverse_stop_nofill_avoid"
        if decision == "AVOID"
        else "accepted_builder_entry_adverse_balanced_context"
    )
    enriched["candidate_use_allowed_now"] = decision == "FOLLOW"
    enriched["runtime_candidate_use_permitted"] = decision == "FOLLOW"
    enriched["source_bound"] = True
    enriched["source_complete"] = decision in {"FOLLOW", "AVOID"}
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    target_first_rate = _to_float(enriched.get("target_first_rate")) or 0.0
    stop_first_rate = _to_float(enriched.get("stop_first_rate")) or 0.0
    no_fill_rate = _to_float(enriched.get("no_fill_or_unfilled_rate")) or 0.0
    path_quality_proxy = target_first_rate - stop_first_rate - no_fill_rate
    enriched["entry_adverse_path_quality_proxy"] = round(path_quality_proxy, 12)

    metrics = dict(enriched.get("r_metrics") or {})
    proxy = _metric_from_scalar(
        path_quality_proxy,
        source_field="target_first_rate_minus_stop_first_and_no_fill",
    )
    if proxy:
        metrics.setdefault("proxy_score", proxy)
    stress = _metric_from_scalar(
        enriched.get("entry_adverse_builder_score"),
        source_field="entry_adverse_builder_score",
    )
    if stress:
        metrics.setdefault("stress_simulated_r", stress)
    effective_n = _metric_from_scalar(1, source_field="accepted_builder_entry_adverse_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _accepted_builder_family_decision(row: dict[str, Any]) -> DecisionLabel:
    status = _normalized(row.get("family_builder_result_status")).upper()
    score_class = _normalized(row.get("family_builder_score_class")).upper()
    if status == "FAMILY_POSITIVE_NEXT_LAYER_CONTEXT" or score_class == "RESULT_SCORE_POSITIVE":
        return "FOLLOW"
    if status == "FAMILY_REPAIR_OR_NEGATIVE_CONTEXT" or score_class == "RESULT_SCORE_NEGATIVE":
        return "AVOID"
    return "MIXED"


def _accepted_builder_family_action_class(row: dict[str, Any], decision: DecisionLabel) -> str:
    action_family = _normalized(row.get("action_family")).casefold()
    if decision == "FOLLOW":
        return f"{action_family}_family_follow_scorer" if action_family else "follow_scorer"
    if decision == "AVOID":
        return f"{action_family}_family_avoid" if action_family else "family_negative_avoid"
    return f"{action_family}_family_context_guard" if action_family else "context_guard"


def _accepted_builder_family_source_group(row: dict[str, Any], decision: DecisionLabel) -> str:
    status = _normalized(row.get("family_builder_result_status")).upper()
    if decision == "FOLLOW":
        return "accepted_builder_family_positive_follow"
    if decision == "AVOID":
        return "accepted_builder_family_negative_or_repair_avoid"
    if status == "FAMILY_NO_SCALAR_OR_BINDING_CONTEXT":
        return "accepted_builder_family_no_scalar_context"
    return "accepted_builder_family_sidecar_context"


def _enrich_moonshot_accepted_builder_family_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert family-level accepted-builder rows into route-scoped scorer evidence."""
    if not row.get("family_builder_result_id") or not row.get("route_candidate_id"):
        return row

    enriched = dict(row)
    scope = _challenger_frontier_scope_from_route_candidate(
        enriched,
        source_component="gtos_accepted_builder_family",
    )
    if not scope:
        return enriched
    scope["route_family"] = "moonshot_accepted_builder_family"
    if side := _normalized(enriched.get("side")).upper():
        if side in {"LONG", "SHORT"}:
            scope["side"] = side
    if action_family := _normalized(enriched.get("action_family")).upper():
        scope["action_family"] = action_family

    decision = _accepted_builder_family_decision(enriched)
    action_class = _accepted_builder_family_action_class(enriched, decision)
    score = _to_float(enriched.get("family_builder_score"))
    if score is None:
        proxy_r_class = "BOUNDED_AMBIGUOUS_PROXY_R"
    elif score >= 0.5:
        proxy_r_class = "STRONG_POSITIVE_PROXY_R"
    elif score > 0:
        proxy_r_class = "POSITIVE_PROXY_R"
    elif score <= -0.5:
        proxy_r_class = "STRONG_NEGATIVE_PROXY_R"
    elif score < 0:
        proxy_r_class = "NEGATIVE_PROXY_R"
    else:
        proxy_r_class = "FLAT_PROXY_R"

    status = _normalized(enriched.get("family_builder_result_status")).upper()
    target_stop_order_class = (
        "TARGET_STOP_AMBIGUOUS_OR_MIXED"
        if decision == "MIXED" or status == "FAMILY_NO_SCALAR_OR_BINDING_CONTEXT"
        else ""
    )

    scope["action_class"] = action_class
    scope["proxy_r_class"] = proxy_r_class
    if target_stop_order_class:
        scope["target_stop_order_class"] = target_stop_order_class

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("family_builder_result_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_accepted_builder_family"
    enriched["evidence_family"] = "moonshot_accepted_builder_family"
    enriched["source_group"] = _accepted_builder_family_source_group(enriched, decision)
    enriched["source_role"] = "accepted_builder_family_runtime_surface"
    enriched["system_surface"] = "accepted_builder_family_scorer_filter_runtime"
    enriched["source_component"] = "gtos_accepted_builder_family"
    enriched["route_family"] = "moonshot_accepted_builder_family"
    enriched["review_action"] = decision
    enriched["action_class"] = action_class
    enriched["proxy_r_class"] = proxy_r_class
    if target_stop_order_class:
        enriched["target_stop_order_class"] = target_stop_order_class
    enriched["implementation_action"] = (
        enriched.get("family_builder_policy")
        or enriched.get("family_selector_execution_status")
        or "PRESERVE_FAMILY_BUILDER_CONTEXT"
    )
    enriched["r_evidence_class"] = (
        "ACCEPTED_BUILDER_FAMILY_POSITIVE_PROXY"
        if decision == "FOLLOW"
        else "ACCEPTED_BUILDER_FAMILY_NEGATIVE_OR_REPAIR_PROXY"
        if decision == "AVOID"
        else "ACCEPTED_BUILDER_FAMILY_CONTEXT_PROXY"
    )
    enriched["runtime_effect_now"] = (
        "accepted_builder_family_follow_scorer"
        if decision == "FOLLOW"
        else "accepted_builder_family_avoid_filter"
        if decision == "AVOID"
        else "accepted_builder_family_context_guard"
    )
    enriched["candidate_use_allowed_now"] = decision == "FOLLOW"
    enriched["runtime_candidate_use_permitted"] = decision == "FOLLOW"
    enriched["source_bound"] = True
    enriched["source_complete"] = decision in {"FOLLOW", "AVOID"}
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    proxy = _metric_from_scalar(
        enriched.get("family_builder_score"),
        source_field="family_builder_score",
    )
    if proxy:
        metrics.setdefault("proxy_score", proxy)
    effective_n = _metric_from_scalar(1, source_field="accepted_builder_family_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _accepted_builder_m15_decision(row: dict[str, Any]) -> DecisionLabel:
    status = _normalized(row.get("m15_builder_result_status")).upper()
    if status in {
        "M15_TARGET_FIRST_ACCEPTED_CONSERVATIVE_BOUND",
        "M15_BOUNDS_SPLIT_ACCEPTED_POSITIVE_MIDPOINT",
    }:
        return "FOLLOW"
    if status == "M15_REJECTED_AVOID_OR_REDESIGN_REQUIRED":
        return "AVOID"
    return "MIXED"


def _accepted_builder_m15_action_class(row: dict[str, Any], decision: DecisionLabel) -> str:
    status = _normalized(row.get("m15_builder_result_status")).upper()
    if decision == "FOLLOW":
        if status == "M15_BOUNDS_SPLIT_ACCEPTED_POSITIVE_MIDPOINT":
            return "m15_bounds_split_follow_scorer"
        return "m15_target_first_follow_scorer"
    if decision == "AVOID":
        return "m15_rejected_avoid_filter"
    return "m15_sidecar_context_guard"


def _accepted_builder_m15_source_group(row: dict[str, Any], decision: DecisionLabel) -> str:
    status = _normalized(row.get("m15_builder_result_status")).upper()
    if status == "M15_TARGET_FIRST_ACCEPTED_CONSERVATIVE_BOUND":
        return "accepted_builder_m15_target_first_follow"
    if status == "M15_BOUNDS_SPLIT_ACCEPTED_POSITIVE_MIDPOINT":
        return "accepted_builder_m15_bounds_split_positive_follow"
    if decision == "AVOID":
        return "accepted_builder_m15_rejected_avoid"
    return "accepted_builder_m15_sidecar_context"


def _accepted_builder_m15_r_evidence_class(row: dict[str, Any], decision: DecisionLabel) -> str:
    status = _normalized(row.get("m15_builder_result_status")).upper()
    if status == "M15_TARGET_FIRST_ACCEPTED_CONSERVATIVE_BOUND":
        return "ACCEPTED_BUILDER_M15_TARGET_FIRST_CONSERVATIVE_PROXY"
    if status == "M15_BOUNDS_SPLIT_ACCEPTED_POSITIVE_MIDPOINT":
        return "ACCEPTED_BUILDER_M15_BOUNDS_SPLIT_POSITIVE_PROXY"
    if decision == "AVOID":
        return "ACCEPTED_BUILDER_M15_REJECTED_AVOID_OR_REDESIGN"
    return "ACCEPTED_BUILDER_M15_SIDECAR_CONTEXT"


def _enrich_moonshot_accepted_builder_m15_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert M15 accepted-builder result rows into timeframe-scoped runtime evidence."""
    if not row.get("m15_builder_result_id") or not row.get("route_candidate_id"):
        return row

    enriched = dict(row)
    scope = _challenger_frontier_scope_from_route_candidate(
        enriched,
        source_component="gtos_accepted_builder_m15",
    )
    if not scope:
        return enriched
    scope["route_family"] = "moonshot_accepted_builder_m15"
    scope["market_timeframe"] = "M15"
    if side := _normalized(enriched.get("side")).upper():
        if side in {"LONG", "SHORT"}:
            scope["side"] = side

    decision = _accepted_builder_m15_decision(enriched)
    action_class = _accepted_builder_m15_action_class(enriched, decision)
    status = _normalized(enriched.get("m15_builder_result_status")).upper()
    target_stop_order_class = ACCEPTED_BUILDER_M15_TARGET_STOP_CLASS_BY_STATUS.get(
        status,
        "TARGET_STOP_AMBIGUOUS_OR_MIXED",
    )
    proxy_r_class = _accepted_builder_proxy_r_class(
        enriched.get("m15_builder_score"),
        decision,
    )

    scope["action_class"] = action_class
    scope["target_stop_order_class"] = target_stop_order_class
    if proxy_r_class:
        scope["proxy_r_class"] = proxy_r_class

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("m15_builder_result_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_accepted_builder_m15"
    enriched["evidence_family"] = "moonshot_accepted_builder_m15"
    enriched["source_group"] = _accepted_builder_m15_source_group(enriched, decision)
    enriched["source_role"] = "accepted_builder_m15_runtime_surface"
    enriched["system_surface"] = "accepted_builder_m15_scorer_filter_runtime"
    enriched["source_component"] = "gtos_accepted_builder_m15"
    enriched["route_family"] = "moonshot_accepted_builder_m15"
    enriched["market_timeframe"] = "M15"
    enriched["review_action"] = decision
    enriched["action_class"] = action_class
    enriched["proxy_r_class"] = proxy_r_class
    enriched["target_stop_order_class"] = target_stop_order_class
    enriched["implementation_action"] = (
        enriched.get("m15_builder_next_action")
        or enriched.get("m15_selector_execution_status")
        or "PRESERVE_M15_BUILDER_CONTEXT"
    )
    enriched["r_evidence_class"] = _accepted_builder_m15_r_evidence_class(
        enriched,
        decision,
    )
    enriched["runtime_effect_now"] = (
        "accepted_builder_m15_follow_scorer"
        if decision == "FOLLOW"
        else "accepted_builder_m15_avoid_filter"
        if decision == "AVOID"
        else "accepted_builder_m15_context_guard"
    )
    enriched["candidate_use_allowed_now"] = decision == "FOLLOW"
    enriched["runtime_candidate_use_permitted"] = decision == "FOLLOW"
    enriched["source_bound"] = True
    enriched["source_complete"] = decision in {"FOLLOW", "AVOID"}
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    proxy = _metric_from_scalar(
        enriched.get("m15_builder_score"),
        source_field="m15_builder_score",
    )
    if proxy:
        metrics.setdefault("proxy_score", proxy)
    stress = _metric_from_scalar(
        enriched.get("m15_interval_lower_mean"),
        source_field="m15_interval_lower_mean",
    )
    if stress:
        metrics.setdefault("stress_simulated_r", stress)
    effective_n = _metric_from_scalar(1, source_field="accepted_builder_m15_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _accepted_builder_m1_decision(row: dict[str, Any]) -> DecisionLabel:
    status = _normalized(row.get("m1_builder_result_status")).upper()
    if status in {
        "M1_SUPPORT_STABLE_ACCEPTED",
        "M1_SUPPORT_CONFLICT_SPLIT_ACCEPTED",
    }:
        return "FOLLOW"
    return "MIXED"


def _accepted_builder_m1_action_class(row: dict[str, Any], decision: DecisionLabel) -> str:
    status = _normalized(row.get("m1_builder_result_status")).upper()
    if decision == "FOLLOW":
        if status == "M1_SUPPORT_CONFLICT_SPLIT_ACCEPTED":
            return "m1_support_conflict_split_follow_scorer"
        return "m1_support_stable_follow_scorer"
    return "m1_sidecar_context_guard"


def _accepted_builder_m1_source_group(row: dict[str, Any], decision: DecisionLabel) -> str:
    status = _normalized(row.get("m1_builder_result_status")).upper()
    if status == "M1_SUPPORT_STABLE_ACCEPTED":
        return "accepted_builder_m1_support_stable_follow"
    if status == "M1_SUPPORT_CONFLICT_SPLIT_ACCEPTED":
        return "accepted_builder_m1_support_conflict_split_follow"
    return "accepted_builder_m1_sidecar_context"


def _accepted_builder_m1_r_evidence_class(row: dict[str, Any], decision: DecisionLabel) -> str:
    status = _normalized(row.get("m1_builder_result_status")).upper()
    if status == "M1_SUPPORT_STABLE_ACCEPTED":
        return "ACCEPTED_BUILDER_M1_SUPPORT_STABLE_POSITIVE_PROXY"
    if status == "M1_SUPPORT_CONFLICT_SPLIT_ACCEPTED":
        return "ACCEPTED_BUILDER_M1_SUPPORT_CONFLICT_SPLIT_PROXY"
    return "ACCEPTED_BUILDER_M1_SIDECAR_CONTEXT"


def _enrich_moonshot_accepted_builder_m1_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert M1 accepted-builder support rows into timeframe-scoped runtime evidence."""
    if not row.get("m1_builder_result_id") or not row.get("route_candidate_id"):
        return row

    enriched = dict(row)
    scope = _challenger_frontier_scope_from_route_candidate(
        enriched,
        source_component="gtos_accepted_builder_m1",
    )
    if not scope:
        return enriched
    scope["route_family"] = "moonshot_accepted_builder_m1"
    scope["market_timeframe"] = "M1"
    if side := _normalized(enriched.get("side")).upper():
        if side in {"LONG", "SHORT"}:
            scope["side"] = side

    decision = _accepted_builder_m1_decision(enriched)
    action_class = _accepted_builder_m1_action_class(enriched, decision)
    status = _normalized(enriched.get("m1_builder_result_status")).upper()
    support_class = ACCEPTED_BUILDER_M1_SUPPORT_CLASS_BY_STATUS.get(
        status,
        "M1_SUPPORT_SIDECAR_CONTEXT",
    )
    proxy_r_class = _accepted_builder_proxy_r_class(
        enriched.get("m1_builder_score"),
        decision,
    )

    scope["action_class"] = action_class
    scope["m1_support_class"] = support_class
    if proxy_r_class:
        scope["proxy_r_class"] = proxy_r_class

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("m1_builder_result_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_accepted_builder_m1"
    enriched["evidence_family"] = "moonshot_accepted_builder_m1"
    enriched["source_group"] = _accepted_builder_m1_source_group(enriched, decision)
    enriched["source_role"] = "accepted_builder_m1_runtime_surface"
    enriched["system_surface"] = "accepted_builder_m1_support_scorer_runtime"
    enriched["source_component"] = "gtos_accepted_builder_m1"
    enriched["route_family"] = "moonshot_accepted_builder_m1"
    enriched["market_timeframe"] = "M1"
    enriched["review_action"] = decision
    enriched["action_class"] = action_class
    enriched["m1_support_class"] = support_class
    enriched["proxy_r_class"] = proxy_r_class
    enriched["implementation_action"] = (
        enriched.get("m1_builder_next_action")
        or enriched.get("m1_selector_execution_status")
        or "PRESERVE_M1_BUILDER_CONTEXT"
    )
    enriched["r_evidence_class"] = _accepted_builder_m1_r_evidence_class(
        enriched,
        decision,
    )
    enriched["runtime_effect_now"] = (
        "accepted_builder_m1_follow_scorer"
        if decision == "FOLLOW"
        else "accepted_builder_m1_context_guard"
    )
    enriched["candidate_use_allowed_now"] = decision == "FOLLOW"
    enriched["runtime_candidate_use_permitted"] = decision == "FOLLOW"
    enriched["source_bound"] = True
    enriched["source_complete"] = decision == "FOLLOW"
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    proxy = _metric_from_scalar(
        enriched.get("m1_builder_score"),
        source_field="m1_builder_score",
    )
    if proxy:
        metrics.setdefault("proxy_score", proxy)
    support = _metric_from_scalar(
        enriched.get("m1_support_adjusted_midpoint"),
        source_field="m1_support_adjusted_midpoint",
    )
    if support:
        metrics.setdefault("stress_simulated_r", support)
    effective_n = _metric_from_scalar(1, source_field="accepted_builder_m1_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _accepted_builder_positive_decision(row: dict[str, Any]) -> DecisionLabel:
    status = _normalized(row.get("positive_builder_result_status")).upper()
    if status == "POSITIVE_REPLAY_ACCEPTED_AFTER_MODIFIERS":
        return "FOLLOW"
    if status == "POSITIVE_REJECTED_OR_NONPOSITIVE":
        return "AVOID"
    return "MIXED"


def _accepted_builder_positive_action_class(
    row: dict[str, Any],
    decision: DecisionLabel,
) -> str:
    status = _normalized(row.get("positive_builder_result_status")).upper()
    if decision == "FOLLOW":
        return "positive_replay_after_modifiers_follow_scorer"
    if decision == "AVOID":
        return "positive_rejected_nonpositive_avoid_filter"
    if status == "POSITIVE_REPAIR_OR_STRESS_REQUIRED_BEFORE_REPLAY":
        return "positive_repair_stress_context_guard"
    return "positive_sidecar_context_guard"


def _accepted_builder_positive_source_group(
    row: dict[str, Any],
    decision: DecisionLabel,
) -> str:
    status = _normalized(row.get("positive_builder_result_status")).upper()
    if decision == "FOLLOW":
        return "accepted_builder_positive_replay_follow"
    if decision == "AVOID":
        return "accepted_builder_positive_rejected_avoid"
    if status == "POSITIVE_REPAIR_OR_STRESS_REQUIRED_BEFORE_REPLAY":
        return "accepted_builder_positive_repair_stress_context"
    return "accepted_builder_positive_sidecar_context"


def _accepted_builder_positive_r_evidence_class(
    row: dict[str, Any],
    decision: DecisionLabel,
) -> str:
    status = _normalized(row.get("positive_builder_result_status")).upper()
    if decision == "FOLLOW":
        return "ACCEPTED_BUILDER_POSITIVE_REPLAY_PROXY"
    if decision == "AVOID":
        return "ACCEPTED_BUILDER_POSITIVE_REJECTED_NONPOSITIVE"
    if status == "POSITIVE_REPAIR_OR_STRESS_REQUIRED_BEFORE_REPLAY":
        return "ACCEPTED_BUILDER_POSITIVE_REPAIR_STRESS_CONTEXT"
    return "ACCEPTED_BUILDER_POSITIVE_SIDECAR_CONTEXT"


def _enrich_moonshot_accepted_builder_positive_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert accepted-builder positive result rows into route-scoped runtime evidence."""
    if not row.get("positive_builder_result_id") or not row.get("route_candidate_id"):
        return row

    enriched = dict(row)
    scope = _challenger_frontier_scope_from_route_candidate(
        enriched,
        source_component="gtos_accepted_builder_positive",
    )
    if not scope:
        return enriched
    scope["route_family"] = "moonshot_accepted_builder_positive"
    if side := _normalized(enriched.get("side")).upper():
        if side in {"LONG", "SHORT"}:
            scope["side"] = side
    if entry_variant := _normalized(enriched.get("entry_variant")).upper():
        scope["entry_variant"] = entry_variant

    decision = _accepted_builder_positive_decision(enriched)
    action_class = _accepted_builder_positive_action_class(enriched, decision)
    status = _normalized(enriched.get("positive_builder_result_status")).upper()
    positive_result_class = ACCEPTED_BUILDER_POSITIVE_CLASS_BY_STATUS.get(
        status,
        "POSITIVE_CONTEXT",
    )
    proxy_r_class = _accepted_builder_proxy_r_class(
        enriched.get("positive_builder_score"),
        decision,
    )

    scope["action_class"] = action_class
    scope["positive_result_class"] = positive_result_class
    if proxy_r_class:
        scope["proxy_r_class"] = proxy_r_class

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("positive_builder_result_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_accepted_builder_positive"
    enriched["evidence_family"] = "moonshot_accepted_builder_positive"
    enriched["source_group"] = _accepted_builder_positive_source_group(enriched, decision)
    enriched["source_role"] = "accepted_builder_positive_runtime_surface"
    enriched["system_surface"] = "accepted_builder_positive_scorer_filter_runtime"
    enriched["source_component"] = "gtos_accepted_builder_positive"
    enriched["route_family"] = "moonshot_accepted_builder_positive"
    enriched["review_action"] = decision
    enriched["action_class"] = action_class
    enriched["entry_variant"] = scope.get("entry_variant")
    enriched["positive_result_class"] = positive_result_class
    enriched["proxy_r_class"] = proxy_r_class
    enriched["implementation_action"] = (
        enriched.get("positive_builder_next_action")
        or enriched.get("positive_selector_execution_status")
        or "PRESERVE_POSITIVE_BUILDER_CONTEXT"
    )
    enriched["r_evidence_class"] = _accepted_builder_positive_r_evidence_class(
        enriched,
        decision,
    )
    enriched["runtime_effect_now"] = (
        "accepted_builder_positive_follow_scorer"
        if decision == "FOLLOW"
        else "accepted_builder_positive_avoid_filter"
        if decision == "AVOID"
        else "accepted_builder_positive_context_guard"
    )
    enriched["candidate_use_allowed_now"] = decision == "FOLLOW"
    enriched["runtime_candidate_use_permitted"] = decision == "FOLLOW"
    enriched["source_bound"] = True
    enriched["source_complete"] = decision in {"FOLLOW", "AVOID"}
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    proxy = _metric_from_scalar(
        enriched.get("positive_builder_score"),
        source_field="positive_builder_score",
    )
    if proxy:
        metrics.setdefault("proxy_score", proxy)
    midpoint = _metric_from_scalar(
        enriched.get("positive_adjusted_midpoint"),
        source_field="positive_adjusted_midpoint",
    )
    if midpoint:
        metrics.setdefault("cost_adjusted_simulated_r", midpoint)
    lower = _metric_from_scalar(
        enriched.get("positive_adjusted_lower"),
        source_field="positive_adjusted_lower",
    )
    if lower:
        metrics.setdefault("stress_simulated_r", lower)
    effective_n = _metric_from_scalar(1, source_field="accepted_builder_positive_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _accepted_builder_source_decision(row: dict[str, Any]) -> DecisionLabel:
    status = _normalized(row.get("source_builder_result_status")).upper()
    if "REJECTED" in status:
        return "AVOID"
    if "ACCEPTED" in status:
        return "FOLLOW"
    return "MIXED"


def _accepted_builder_source_action_class(
    row: dict[str, Any],
    decision: DecisionLabel,
) -> str:
    status = _normalized(row.get("source_builder_result_status")).upper()
    if decision == "FOLLOW":
        if "LOW_HIGH_BOUNDS" in status:
            return "source_low_high_bounds_follow_scorer"
        return "source_cost_cap_follow_scorer"
    if decision == "AVOID":
        return "source_exact_repair_avoid_filter"
    return "source_bounds_repair_context_guard"


def _accepted_builder_source_group(
    row: dict[str, Any],
    decision: DecisionLabel,
) -> str:
    status = _normalized(row.get("source_builder_result_status")).upper()
    if decision == "FOLLOW":
        if "LOW_HIGH_BOUNDS" in status:
            return "accepted_builder_source_low_high_follow"
        return "accepted_builder_source_cost_cap_follow"
    if decision == "AVOID":
        return "accepted_builder_source_rejected_avoid"
    return "accepted_builder_source_bounds_repair_context"


def _accepted_builder_source_r_evidence_class(
    row: dict[str, Any],
    decision: DecisionLabel,
) -> str:
    status = _normalized(row.get("source_builder_result_status")).upper()
    if decision == "FOLLOW":
        if "LOW_HIGH_BOUNDS" in status:
            return "ACCEPTED_BUILDER_SOURCE_LOW_HIGH_BOUNDS_PROXY"
        return "ACCEPTED_BUILDER_SOURCE_COST_CAP_PROXY"
    if decision == "AVOID":
        return "ACCEPTED_BUILDER_SOURCE_REJECTED_REPAIR_AVOID"
    return "ACCEPTED_BUILDER_SOURCE_BOUNDS_REPAIR_CONTEXT"


def _enrich_moonshot_accepted_builder_source_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert accepted-builder source rows into route-scoped cost/source evidence."""
    if not row.get("source_builder_result_id") or not row.get("route_candidate_id"):
        return row

    enriched = dict(row)
    scope = _challenger_frontier_scope_from_route_candidate(
        enriched,
        source_component="gtos_accepted_builder_source",
    )
    if not scope:
        return enriched
    scope["route_family"] = "moonshot_accepted_builder_source"
    if side := _normalized(enriched.get("side")).upper():
        if side in {"LONG", "SHORT"}:
            scope["side"] = side
    if entry_variant := _normalized(enriched.get("entry_variant")).upper():
        scope["entry_variant"] = entry_variant

    decision = _accepted_builder_source_decision(enriched)
    action_class = _accepted_builder_source_action_class(enriched, decision)
    status = _normalized(enriched.get("source_builder_result_status")).upper()
    source_result_class = ACCEPTED_BUILDER_SOURCE_CLASS_BY_STATUS.get(
        status,
        "SOURCE_CONTEXT",
    )
    proxy_r_class = _accepted_builder_proxy_r_class(
        enriched.get("source_builder_score"),
        decision,
    )

    scope["action_class"] = action_class
    scope["source_result_class"] = source_result_class
    if proxy_r_class:
        scope["proxy_r_class"] = proxy_r_class

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("source_builder_result_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_accepted_builder_source"
    enriched["evidence_family"] = "moonshot_accepted_builder_source"
    enriched["source_group"] = _accepted_builder_source_group(enriched, decision)
    enriched["source_role"] = "accepted_builder_source_cost_repair_runtime_surface"
    enriched["system_surface"] = "accepted_builder_source_cost_repair_scorer_filter_runtime"
    enriched["source_component"] = "gtos_accepted_builder_source"
    enriched["route_family"] = "moonshot_accepted_builder_source"
    enriched["review_action"] = decision
    enriched["action_class"] = action_class
    enriched["entry_variant"] = scope.get("entry_variant")
    enriched["source_result_class"] = source_result_class
    enriched["proxy_r_class"] = proxy_r_class
    enriched["implementation_action"] = (
        enriched.get("source_builder_next_action")
        or enriched.get("source_selector_execution_status")
        or "PRESERVE_SOURCE_BUILDER_CONTEXT"
    )
    enriched["r_evidence_class"] = _accepted_builder_source_r_evidence_class(
        enriched,
        decision,
    )
    enriched["runtime_effect_now"] = (
        "accepted_builder_source_follow_scorer"
        if decision == "FOLLOW"
        else "accepted_builder_source_avoid_filter"
        if decision == "AVOID"
        else "accepted_builder_source_repair_context_guard"
    )
    enriched["candidate_use_allowed_now"] = decision == "FOLLOW"
    enriched["runtime_candidate_use_permitted"] = decision == "FOLLOW"
    enriched["source_bound"] = True
    enriched["source_complete"] = decision in {"FOLLOW", "AVOID"}
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    proxy = _metric_from_scalar(
        enriched.get("source_builder_score"),
        source_field="source_builder_score",
    )
    if proxy:
        metrics.setdefault("proxy_score", proxy)
        metrics.setdefault("cost_adjusted_simulated_r", proxy)
    span_value = _to_float(enriched.get("source_cost_sensitivity_span"))
    if span_value is not None:
        stress_value = -abs(span_value) if decision != "FOLLOW" else span_value
        stress = _metric_from_scalar(
            stress_value,
            source_field="source_cost_sensitivity_span",
        )
        if stress:
            metrics.setdefault("stress_simulated_r", stress)
    effective_n = _metric_from_scalar(1, source_field="accepted_builder_source_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _accepted_builder_rejected_repair_decision(row: dict[str, Any]) -> DecisionLabel:
    action = _normalized(
        row.get("next_layer_branch_action") or row.get("branch_system_recommendation")
    ).upper()
    if action in {
        "AVOID_SOURCE_BRANCH_UNTIL_EXACT_SOURCE_REPAIR_OR_COST_MODEL_CHANGE",
        "BUILD_M15_AVOID_OR_REDESIGN_FILTER",
    }:
        return "AVOID"
    return "MIXED"


def _accepted_builder_rejected_repair_action_class(
    row: dict[str, Any],
    decision: DecisionLabel,
) -> str:
    action = _normalized(
        row.get("next_layer_branch_action") or row.get("branch_system_recommendation")
    ).upper()
    if decision == "AVOID":
        if action == "BUILD_M15_AVOID_OR_REDESIGN_FILTER":
            return "rejected_repair_m15_avoid_filter"
        return "rejected_repair_source_avoid_filter"
    if action == "REPAIR_SOURCE_OR_STRESS_POSITIVE_BRANCH_BEFORE_REPLAY":
        return "rejected_repair_positive_stress_context_guard"
    if "BINDING" in action:
        return "rejected_repair_binding_context_guard"
    return "rejected_repair_entry_adverse_context_guard"


def _accepted_builder_rejected_repair_source_group(
    row: dict[str, Any],
    decision: DecisionLabel,
) -> str:
    action = _normalized(
        row.get("next_layer_branch_action") or row.get("branch_system_recommendation")
    ).upper()
    if decision == "AVOID":
        if action == "BUILD_M15_AVOID_OR_REDESIGN_FILTER":
            return "accepted_builder_rejected_repair_m15_avoid"
        return "accepted_builder_rejected_repair_source_avoid"
    if action == "REPAIR_SOURCE_OR_STRESS_POSITIVE_BRANCH_BEFORE_REPLAY":
        return "accepted_builder_rejected_repair_positive_context"
    if "BINDING" in action:
        return "accepted_builder_rejected_repair_binding_context"
    return "accepted_builder_rejected_repair_entry_context"


def _accepted_builder_rejected_repair_r_evidence_class(
    row: dict[str, Any],
    decision: DecisionLabel,
) -> str:
    action = _normalized(
        row.get("next_layer_branch_action") or row.get("branch_system_recommendation")
    ).upper()
    if decision == "AVOID":
        if action == "BUILD_M15_AVOID_OR_REDESIGN_FILTER":
            return "ACCEPTED_BUILDER_REJECTED_REPAIR_M15_AVOID"
        return "ACCEPTED_BUILDER_REJECTED_REPAIR_SOURCE_AVOID"
    if action == "REPAIR_SOURCE_OR_STRESS_POSITIVE_BRANCH_BEFORE_REPLAY":
        return "ACCEPTED_BUILDER_REJECTED_REPAIR_POSITIVE_CONTEXT"
    if "BINDING" in action:
        return "ACCEPTED_BUILDER_REJECTED_REPAIR_BINDING_CONTEXT"
    return "ACCEPTED_BUILDER_REJECTED_REPAIR_ENTRY_CONTEXT"


def _enrich_moonshot_accepted_builder_rejected_repair_row(
    row: dict[str, Any],
) -> dict[str, Any]:
    """Convert accepted-builder rejected-repair rows into route-scoped avoid/context evidence."""
    if not row.get("rejected_repair_result_id") or not row.get("route_candidate_id"):
        return row

    enriched = dict(row)
    scope = _challenger_frontier_scope_from_route_candidate(
        enriched,
        source_component="gtos_accepted_builder_rejected_repair",
    )
    if not scope:
        return enriched
    scope["route_family"] = "moonshot_accepted_builder_rejected_repair"
    if side := _normalized(enriched.get("side")).upper():
        if side in {"LONG", "SHORT"}:
            scope["side"] = side
    if entry_variant := _normalized(enriched.get("entry_variant")).upper():
        scope["entry_variant"] = entry_variant

    decision = _accepted_builder_rejected_repair_decision(enriched)
    action_class = _accepted_builder_rejected_repair_action_class(enriched, decision)
    action = _normalized(
        enriched.get("next_layer_branch_action") or enriched.get("branch_system_recommendation")
    ).upper()
    rejected_repair_class = ACCEPTED_BUILDER_REJECTED_REPAIR_CLASS_BY_ACTION.get(
        action,
        "REJECTED_REPAIR_CONTEXT",
    )
    proxy_r_class = _accepted_builder_proxy_r_class(
        enriched.get("primary_selector_score"),
        decision,
    )

    scope["action_class"] = action_class
    scope["rejected_repair_class"] = rejected_repair_class
    if proxy_r_class:
        scope["proxy_r_class"] = proxy_r_class

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("rejected_repair_result_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_accepted_builder_rejected_repair"
    enriched["evidence_family"] = "moonshot_accepted_builder_rejected_repair"
    enriched["source_group"] = _accepted_builder_rejected_repair_source_group(
        enriched,
        decision,
    )
    enriched["source_role"] = "accepted_builder_rejected_repair_runtime_surface"
    enriched["system_surface"] = "accepted_builder_rejected_repair_avoid_context_runtime"
    enriched["source_component"] = "gtos_accepted_builder_rejected_repair"
    enriched["route_family"] = "moonshot_accepted_builder_rejected_repair"
    enriched["review_action"] = decision
    enriched["action_class"] = action_class
    enriched["entry_variant"] = scope.get("entry_variant")
    enriched["rejected_repair_class"] = rejected_repair_class
    enriched["proxy_r_class"] = proxy_r_class
    enriched["implementation_action"] = (
        enriched.get("next_layer_branch_action")
        or enriched.get("branch_system_recommendation")
        or "PRESERVE_REJECTED_REPAIR_CONTEXT"
    )
    enriched["r_evidence_class"] = _accepted_builder_rejected_repair_r_evidence_class(
        enriched,
        decision,
    )
    enriched["runtime_effect_now"] = (
        "accepted_builder_rejected_repair_avoid_filter"
        if decision == "AVOID"
        else "accepted_builder_rejected_repair_context_guard"
    )
    enriched["candidate_use_allowed_now"] = decision == "AVOID"
    enriched["runtime_candidate_use_permitted"] = decision == "AVOID"
    enriched["source_bound"] = True
    enriched["source_complete"] = decision == "AVOID"
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    proxy = _metric_from_scalar(
        enriched.get("primary_selector_score"),
        source_field="primary_selector_score",
    )
    if proxy:
        metrics.setdefault("proxy_score", proxy)
    composite = _metric_from_scalar(
        enriched.get("next_layer_composite_score"),
        source_field="next_layer_composite_score",
    )
    if composite:
        metrics.setdefault("stress_simulated_r", composite)
    effective_n = _metric_from_scalar(1, source_field="accepted_builder_rejected_repair_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _enrich_moonshot_control_screen_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert CP280 same-context control rows into primitive context evidence."""
    if _normalized(row.get("evidence_class")).upper() not in {
        "HISTORICAL_OHLC_SAME_CONTEXT_CONTROL_SCREEN",
    }:
        return row
    if not row.get("symbol") or not row.get("session") or not row.get("primitive_id"):
        return row

    enriched = dict(row)
    decision = _control_screen_decision(enriched)
    bucket = _normalized(enriched.get("screen_bucket")).upper()
    if decision == "FOLLOW":
        action_class = "follow_scorer"
        r_evidence_class = "CONTROL_SCREEN_POSITIVE_DIRECTIONAL_PROXY"
        implementation_action = "OHLC_CONTROL_SCREEN_POSITIVE_DIRECTIONAL_FOLLOW_SCORER"
        runtime_effect = "primitive_context_follow_pressure"
    elif decision == "AVOID":
        action_class = "avoid_filter"
        r_evidence_class = "CONTROL_SCREEN_NEGATIVE_DIRECTIONAL_PROXY"
        implementation_action = "OHLC_CONTROL_SCREEN_NEGATIVE_DIRECTIONAL_AVOID_FILTER"
        runtime_effect = "primitive_context_avoid_filter"
    else:
        action_class = "context_guard"
        r_evidence_class = "CONTROL_SCREEN_CONTEXT_OR_REPAIR_PROXY"
        implementation_action = f"OHLC_CONTROL_SCREEN_CONTEXT_GUARD_{bucket or 'UNKNOWN'}"
        runtime_effect = "primitive_context_guard"

    scope_payload = {
        "symbol": enriched.get("symbol"),
        "source_symbol": enriched.get("symbol"),
        "route_session": enriched.get("session"),
        "horizon_id": _control_screen_horizon_id(enriched),
        "primitive": enriched.get("primitive_id"),
        "route_family": "moonshot_control_screen",
        "source_component": "ohlc_control_screen",
        "action_class": action_class,
    }
    if family := _symbol_family_for(enriched.get("symbol")):
        scope_payload["symbol_family"] = family
    if side := _control_screen_side(enriched):
        scope_payload["side"] = side
    scope_payload = {
        key: value for key, value in scope_payload.items()
        if value not in (None, "")
    }
    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope_payload}
    for field, value in scope_payload.items():
        enriched.setdefault(field, value)

    row_id = (
        f"{enriched.get('symbol')}|{enriched.get('session')}|"
        f"{enriched.get('primitive_id')}|{_control_screen_horizon_id(enriched)}"
    )
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_control_screen"
    enriched["evidence_family"] = "moonshot_control_screen"
    enriched["source_group"] = "historical_ohlc_same_context_control_screen"
    enriched["source_role"] = (
        "same_context_directional_control"
        if decision in {"FOLLOW", "AVOID"}
        else "same_context_control_guard"
    )
    enriched["system_surface"] = "vnext_control_screen_context_guard"
    enriched["source_component"] = "ohlc_control_screen"
    enriched["route_family"] = "moonshot_control_screen"
    enriched["review_action"] = decision
    enriched["action_class"] = action_class
    enriched["implementation_action"] = implementation_action
    enriched["r_evidence_class"] = r_evidence_class
    enriched["runtime_effect_now"] = runtime_effect
    enriched["candidate_use_allowed_now"] = decision in {"FOLLOW", "AVOID"}
    enriched["runtime_candidate_use_permitted"] = decision in {"FOLLOW", "AVOID"}
    enriched["source_bound"] = True
    enriched["source_complete"] = bool(enriched.get("material_sample"))
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    proxy_source = (
        "delta_mean_directional_close_units"
        if enriched.get("delta_mean_directional_close_units") is not None
        else "delta_total_excursion_units"
    )
    proxy = _metric_from_scalar(enriched.get(proxy_source), source_field=proxy_source)
    if proxy:
        metrics.setdefault("proxy_score", proxy)
    effective_n = _metric_from_scalar(
        enriched.get("unique_dates") or enriched.get("event_count"),
        source_field="control_screen_unique_dates",
    )
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _enrich_moonshot_challenger_frontier_action_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert CP280 challenger frontier actions into executable route evidence.

    This artifact is not R/PnL validation. Its strongest direct runtime use is
    exact route filtering: placebo-killed primitive/session/horizon routes cast
    AVOID pressure, while replay/transfer/coverage/fragility actions attach as
    MIXED source-repair/context evidence so they cannot masquerade as FOLLOW.
    """
    if not row.get("frontier_action_id") or not row.get("route_candidate_id"):
        return row
    if _normalized(row.get("evidence_class")).upper() not in {
        "HISTORICAL_OHLC_CHALLENGER_FRONTIER_ACTION",
        "",
    }:
        return row

    scope = _challenger_frontier_scope_from_route_candidate(row)
    if not scope:
        return row

    enriched = dict(row)
    decision = _challenger_frontier_action_decision(enriched)
    if decision == "AVOID":
        action_class = "failure_filter"
        r_evidence_class = "CHALLENGER_FRONTIER_PLACEBO_KILLED_AVOID"
        runtime_effect = "primitive_route_avoid_filter"
        implementation_action = "OHLC_CHALLENGER_FRONTIER_PLACEBO_KILLED_AVOID_FILTER"
    else:
        action_class = "context_guard"
        r_evidence_class = "CHALLENGER_FRONTIER_SOURCE_REPAIR_OR_CONTEXT"
        runtime_effect = "primitive_route_source_repair_context"
        implementation_action = (
            "OHLC_CHALLENGER_FRONTIER_SOURCE_REPAIR_OR_CONTEXT_"
            f"{_normalized(enriched.get('frontier_status')).upper()}"
        )

    scope_payload = {
        **scope,
        "action_class": action_class,
    }
    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope_payload}
    for field, value in scope_payload.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("frontier_action_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_challenger_frontier_action"
    enriched["evidence_family"] = "moonshot_challenger_frontier_action"
    enriched["source_group"] = "historical_ohlc_challenger_frontier_action"
    enriched["source_role"] = (
        "placebo_killed_avoid_filter"
        if decision == "AVOID"
        else "source_replay_repair_or_context_action"
    )
    enriched["system_surface"] = "vnext_challenger_frontier_route_filter"
    enriched["source_component"] = "ohlc_challenger_frontier_action"
    enriched["route_family"] = "moonshot_mechanical"
    enriched["action_class"] = action_class
    enriched["implementation_action"] = implementation_action
    enriched["r_evidence_class"] = r_evidence_class
    enriched["runtime_effect_now"] = runtime_effect
    enriched["candidate_use_allowed_now"] = decision == "AVOID"
    enriched["runtime_candidate_use_permitted"] = decision == "AVOID"
    enriched["source_bound"] = True
    enriched["source_complete"] = decision == "AVOID"
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    effective_n = _metric_from_scalar(1, source_field="challenger_frontier_action_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _enrich_moonshot_challenger_frontier_route_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert CP280 challenger frontier route rows into executable evidence.

    Route rows aggregate the same screened primitive routes as the action ledger
    but at one row per route. They still are not validation/R rows, so only
    placebo-killed rows get avoid-filter behavior; survivor/repair route rows
    remain MIXED context with source-bound drill-through evidence.
    """
    if not row.get("route_frontier_id") or not row.get("route_candidate_id"):
        return row
    if row.get("frontier_action_id"):
        return row
    if _normalized(row.get("evidence_class")).upper() not in {
        "HISTORICAL_OHLC_CHALLENGER_FRONTIER_ONLY",
        "",
    }:
        return row

    scope = _challenger_frontier_scope_from_route_candidate(
        row,
        source_component="ohlc_challenger_frontier_route",
    )
    if not scope:
        return row

    enriched = dict(row)
    decision = _challenger_frontier_action_decision(enriched)
    if decision == "AVOID":
        action_class = "failure_filter"
        r_evidence_class = "CHALLENGER_FRONTIER_ROUTE_PLACEBO_KILLED_AVOID"
        runtime_effect = "primitive_route_avoid_filter"
        implementation_action = "OHLC_CHALLENGER_FRONTIER_ROUTE_PLACEBO_KILLED_AVOID_FILTER"
    else:
        action_class = "context_guard"
        r_evidence_class = "CHALLENGER_FRONTIER_ROUTE_SOURCE_REPAIR_OR_CONTEXT"
        runtime_effect = "primitive_route_source_repair_context"
        implementation_action = (
            "OHLC_CHALLENGER_FRONTIER_ROUTE_SOURCE_REPAIR_OR_CONTEXT_"
            f"{_normalized(enriched.get('frontier_status')).upper()}"
        )

    scope_payload = {
        **scope,
        "action_class": action_class,
    }
    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope_payload}
    for field, value in scope_payload.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("route_frontier_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_challenger_frontier_route"
    enriched["evidence_family"] = "moonshot_challenger_frontier_route"
    enriched["source_group"] = "historical_ohlc_challenger_frontier_route"
    enriched["source_role"] = (
        "placebo_killed_route_avoid_filter"
        if decision == "AVOID"
        else "source_replay_repair_or_context_route"
    )
    enriched["system_surface"] = "vnext_challenger_frontier_route_filter"
    enriched["source_component"] = "ohlc_challenger_frontier_route"
    enriched["route_family"] = "moonshot_mechanical"
    enriched["action_class"] = action_class
    enriched["implementation_action"] = implementation_action
    enriched["r_evidence_class"] = r_evidence_class
    enriched["runtime_effect_now"] = runtime_effect
    enriched["candidate_use_allowed_now"] = decision == "AVOID"
    enriched["runtime_candidate_use_permitted"] = decision == "AVOID"
    enriched["source_bound"] = True
    enriched["source_complete"] = decision == "AVOID"
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    effective_n = _metric_from_scalar(
        enriched.get("unique_dates") or enriched.get("event_count"),
        source_field="challenger_frontier_route_unique_dates",
    )
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _moonshot_source_repair_scope_from_route_candidate(row: dict[str, Any]) -> dict[str, str]:
    return _moonshot_route_scope_from_route_candidate(
        row,
        source_component="source_repair_proof",
    )


def _enrich_moonshot_source_repair_row(row: dict[str, Any]) -> dict[str, Any]:
    """Make row-bearing moonshot source-repair ledgers executable as risk blockers."""
    if not row.get("source_repair_id") and not row.get("source_repair_class"):
        return row
    if not row.get("route_candidate_id"):
        return row

    enriched = dict(row)
    scope = _moonshot_source_repair_scope_from_route_candidate(enriched)
    if not scope:
        return enriched

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    source_repair_id = enriched.get("source_repair_id")
    enriched.setdefault("row_key", source_repair_id)
    enriched.setdefault("source_row_id", source_repair_id)
    enriched.setdefault("source_name", "moonshot_source_repair")
    enriched.setdefault("evidence_family", "numeric_router_source_repair")
    enriched.setdefault("r_evidence_class", "SOURCE_REPAIR_FOR_EXACT_R")
    enriched.setdefault("source_group", "source_repair_proof")
    enriched.setdefault("source_role", "exact_r_source_repair_proof")
    enriched.setdefault("system_surface", "source_repair_proof")
    enriched.setdefault("source_component", "source_repair_proof")
    enriched.setdefault("route_family", "moonshot_mechanical")
    enriched.setdefault("implementation_action", "SOURCE_JOIN_REPAIR_REQUIRED")
    enriched.setdefault("runtime_effect_now", "risk_block_until_exact_broker_geometry")
    enriched.setdefault("candidate_use_allowed_now", False)
    enriched.setdefault("runtime_candidate_use_permitted", False)
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    payload = _metric_from_scalar(1, source_field="source_repair_row")
    if payload:
        metrics.setdefault("effective_n", payload)
        enriched["r_metrics"] = metrics
    return enriched


def _enrich_moonshot_target_stop_ordering_row(row: dict[str, Any]) -> dict[str, Any]:
    """Make moonshot ambiguity-collapse target/stop rows executable as risk guards."""
    if not row.get("route_candidate_id") or not row.get("target_stop_result"):
        return row
    if not (
        row.get("ambiguity_collapse_action_id")
        or row.get("ordering_route_id")
        or row.get("target_stop_contract_id")
    ):
        return row

    enriched = dict(row)
    scope = _moonshot_route_scope_from_route_candidate(
        enriched,
        source_component="target_stop_ordering",
    )
    if not scope:
        return enriched

    target_stop_result = _normalized(enriched.get("target_stop_result")).upper()
    target_stop_order_class = MOONSHOT_TARGET_STOP_ORDER_CLASS_BY_RESULT.get(
        target_stop_result,
        "TARGET_STOP_AMBIGUOUS_OR_MIXED",
    )

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {
        **existing_scope,
        **scope,
        "target_stop_order_class": target_stop_order_class,
    }
    for field, value in scope.items():
        enriched.setdefault(field, value)

    row_id = (
        enriched.get("ambiguity_collapse_action_id")
        or enriched.get("ordering_route_id")
        or enriched.get("target_stop_contract_id")
    )
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched.setdefault("source_name", "moonshot_target_stop_ordering")
    enriched.setdefault("evidence_family", "moonshot_target_stop_ordering")
    enriched.setdefault("r_evidence_class", "TARGET_STOP_ORDERING_PROXY_EVIDENCE")
    enriched.setdefault("source_group", "target_stop_ordering_proxy")
    enriched.setdefault("source_role", "m1_fill_bar_stress_ordering")
    enriched.setdefault("system_surface", "target_stop_geometry_runtime_risk")
    enriched.setdefault("source_component", "target_stop_ordering")
    enriched.setdefault("route_family", "moonshot_mechanical")
    enriched.setdefault(
        "implementation_action",
        "ORDERING_OR_INTERVAL_COLLAPSE_BEFORE_DIRECTIONAL_USE",
    )
    enriched.setdefault("target_stop_order_class", target_stop_order_class)
    enriched.setdefault("runtime_effect_now", "target_stop_geometry_risk_guard")
    enriched.setdefault("candidate_use_allowed_now", True)
    enriched.setdefault("runtime_candidate_use_permitted", True)
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    branch_result_class = _normalized(enriched.get("branch_result_class")).upper()
    if branch_result_class.startswith("NEGATIVE_RSTYLE_PROXY"):
        enriched.setdefault("proxy_r_class", "NEGATIVE_PROXY_R")
    elif branch_result_class.startswith("POSITIVE_RSTYLE_PROXY"):
        enriched.setdefault("proxy_r_class", "POSITIVE_PROXY_R")

    metrics = dict(enriched.get("r_metrics") or {})
    payload = _metric_from_scalar(1, source_field="target_stop_ordering_row")
    if payload:
        metrics.setdefault("effective_n", payload)
        enriched["r_metrics"] = metrics
    return enriched


def _enrich_moonshot_entry_adverse_stop_first_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert stop-first adverse redesign details into runtime avoid filters."""
    if not row.get("route_candidate_id"):
        return row
    if not (
        row.get("entry_adverse_adverse_variant_detail_id")
        or row.get("adverse_stop_first_action_id")
    ):
        return row
    if (
        _normalized(row.get("adverse_stop_first_class")).upper()
        != "STOP_FIRST_AVOID_OR_REDESIGN_READY"
    ):
        return row

    enriched = dict(row)
    scope = _moonshot_route_scope_from_route_candidate(
        enriched,
        source_component="entry_adverse_stop_first",
    )
    if not scope:
        return enriched

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {
        **existing_scope,
        **scope,
        "action_class": "avoid_filter",
        "proxy_r_class": "NEGATIVE_PROXY_R",
        "target_stop_order_class": "STOP_FIRST_PROXY_DOMINANT",
    }
    for field, value in scope.items():
        enriched.setdefault(field, value)

    row_id = (
        enriched.get("entry_adverse_adverse_variant_detail_id")
        or enriched.get("adverse_stop_first_action_id")
    )
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched.setdefault("source_name", "moonshot_entry_adverse_redesign")
    enriched.setdefault("evidence_family", "moonshot_entry_adverse_stop_first")
    enriched.setdefault("r_evidence_class", "STOP_FIRST_ADVERSE_PROXY")
    enriched.setdefault("source_group", "entry_adverse_stop_first")
    enriched.setdefault("source_role", "stop_first_avoid_or_redesign_detail")
    enriched.setdefault("system_surface", "entry_adverse_avoid_filter_runtime")
    enriched.setdefault("source_component", "entry_adverse_stop_first")
    enriched.setdefault("route_family", "moonshot_mechanical")
    enriched.setdefault(
        "implementation_action",
        "ADVERSE_STOP_FIRST_IMMEDIATE_AVOID_OR_REDESIGN",
    )
    enriched.setdefault("action_class", "avoid_filter")
    enriched.setdefault("proxy_r_class", "NEGATIVE_PROXY_R")
    enriched.setdefault("target_stop_order_class", "STOP_FIRST_PROXY_DOMINANT")
    enriched.setdefault("runtime_effect_now", "entry_adverse_stop_first_avoid_filter")
    enriched.setdefault("candidate_use_allowed_now", False)
    enriched.setdefault("runtime_candidate_use_permitted", False)
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    if (stop_first_rate := _to_float(enriched.get("stop_first_rate"))) is not None:
        payload = _metric_from_scalar(-abs(stop_first_rate), source_field="stop_first_rate")
        if payload:
            metrics.setdefault("proxy_score", payload)
    effective_n = _metric_from_scalar(1, source_field="entry_adverse_stop_first_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _enrich_moonshot_broker_repaired_proxy_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert broker-repaired proxy rows into executable no-fill route evidence."""
    if not row.get("broker_source_repair_result_row_id"):
        return row
    if not row.get("route_candidate_id") or not row.get("source_component"):
        return row

    source_component = _normalized(row.get("source_component"))
    enriched = dict(row)
    scope = _moonshot_route_scope_from_route_candidate(
        enriched,
        source_component=source_component,
    )
    if not scope:
        return enriched
    if source_component.startswith("nofill_"):
        scope["route_family"] = "nofill_mechanical"

    hard_decision = _normalized(enriched.get("hard_repair_decision")).upper()
    proxy_value = None
    for field_name in (
        "source_repaired_proxy_value",
        "numeric_proxy_value",
        "branch_proxy_value",
    ):
        proxy_value = _to_float(enriched.get(field_name))
        if proxy_value is not None:
            break

    is_negative_avoid = "KEEP_SOURCE_REPAIRED_NEGATIVE_PROXY_AS_AVOID_OR_REDESIGN_INPUT" in hard_decision
    is_positive_guard = "KEEP_SOURCE_REPAIRED_PROXY_AS_DEFAULT_OFF_SCORER_OR_GUARD_INPUT" in hard_decision
    is_flat_context = "MERGE_SOURCE_REPAIRED_FLAT_PROXY_AS_CONTEXT" in hard_decision
    repair_required = "BROKER_GEOMETRY_REPAIR_REQUIRES_DIRECT_TRADE_IDENTIFIER" in hard_decision

    action_class = ""
    if is_negative_avoid:
        action_class = "avoid_filter"
    elif is_positive_guard:
        action_class = "follow_scorer"
    elif is_flat_context:
        action_class = "context_guard"

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    scope_payload = dict(scope)
    if action_class:
        scope_payload["action_class"] = action_class
    if proxy_value is not None:
        if proxy_value < 0:
            scope_payload["proxy_r_class"] = "NEGATIVE_PROXY_R"
        elif proxy_value > 0:
            scope_payload["proxy_r_class"] = "POSITIVE_PROXY_R"
    if enriched.get("target_stop_order_class"):
        scope_payload["target_stop_order_class"] = enriched.get("target_stop_order_class")
    enriched["event_scope"] = {**existing_scope, **scope_payload}
    for field, value in scope_payload.items():
        enriched.setdefault(field, value)

    row_id = enriched.get("broker_source_repair_result_row_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched.setdefault("source_name", "moonshot_broker_repaired_proxy")
    enriched.setdefault("evidence_family", "moonshot_broker_repaired_proxy")
    enriched.setdefault("source_group", "broker_repaired_proxy")
    enriched.setdefault("source_role", "broker_repaired_proxy_input")
    enriched.setdefault(
        "system_surface",
        "nofill_pending_policy_runtime"
        if source_component.startswith("nofill_")
        else "broker_repaired_proxy_runtime",
    )
    enriched.setdefault("source_component", source_component)
    enriched.setdefault("route_family", scope_payload.get("route_family"))
    enriched.setdefault("implementation_action", hard_decision)
    if action_class:
        enriched.setdefault("action_class", action_class)
    if repair_required:
        enriched.setdefault("r_evidence_class", "SOURCE_REPAIR_FOR_EXACT_R")
    elif is_negative_avoid:
        enriched.setdefault("r_evidence_class", "SOURCE_REPAIRED_NEGATIVE_PROXY")
    elif is_positive_guard:
        enriched.setdefault("r_evidence_class", "SOURCE_REPAIRED_PROXY")
    else:
        enriched.setdefault("r_evidence_class", "SOURCE_REPAIRED_CONTEXT_PROXY")
    enriched.setdefault("runtime_effect_now", "broker_repaired_proxy_runtime_evidence")
    enriched.setdefault("candidate_use_allowed_now", False)
    enriched.setdefault("runtime_candidate_use_permitted", False)
    if is_negative_avoid:
        enriched.setdefault("source_bound", True)
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    if proxy_value is not None:
        payload = _metric_from_scalar(proxy_value, source_field="source_repaired_proxy_value")
        if payload:
            metrics.setdefault("proxy_score", payload)
    exact_r = _metric_from_scalar(
        enriched.get("exact_broker_r_value"),
        source_field="exact_broker_r_value",
    )
    if exact_r:
        metrics.setdefault("cost_adjusted_simulated_r", exact_r)
    effective_n = _metric_from_scalar(1, source_field="broker_repaired_proxy_row")
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _enrich_moonshot_unified_numeric_result_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert unified numeric result rows into runtime no-fill/scorer evidence."""
    if not row.get("numeric_result_row_id"):
        return row
    if not row.get("source_component"):
        return row

    enriched = dict(row)
    source_component = _normalized(enriched.get("source_component"))
    mechanical_scope = _parse_mechanical_scope_key(enriched.get("mechanical_scope_key"))
    symbol = _normalized(enriched.get("symbol")) or mechanical_scope.get("symbol", "")
    route_session = _normalized(enriched.get("route_session")) or mechanical_scope.get("route_session", "")
    horizon_id = _normalized(enriched.get("horizon_id")) or mechanical_scope.get("horizon_id", "")
    route_family = "nofill_mechanical" if source_component.startswith("nofill_") else "numeric_router"

    scope = {
        key: value
        for key, value in {
            "symbol": symbol,
            "source_symbol": symbol,
            "market": symbol,
            "route_session": route_session,
            "horizon_id": horizon_id,
            "route_family": route_family,
            "source_component": source_component,
            "proxy_r_class": enriched.get("proxy_r_class"),
            "target_stop_order_class": enriched.get("target_stop_order_class"),
        }.items()
        if value not in (None, "")
    }
    if family := _symbol_family_for(symbol):
        scope["symbol_family"] = family
    if primitive := _normalized(enriched.get("primitive_flag") or mechanical_scope.get("primitive_flag")):
        enriched.setdefault("primitive_flag", primitive)

    keep_decision = _normalized(enriched.get("keep_kill_redesign_implement_decision")).upper()
    computed_decision = _normalized(enriched.get("computed_decision")).upper()
    proxy_class = _normalized(enriched.get("proxy_r_class")).upper()
    action_class = ""
    if keep_decision in MOONSHOT_NUMERIC_AVOID_ACTIONS:
        action_class = "avoid_filter"
    elif keep_decision in MOONSHOT_NUMERIC_FOLLOW_ACTIONS:
        action_class = "follow_scorer"
    elif keep_decision in MOONSHOT_NUMERIC_CONTEXT_ACTIONS:
        action_class = "context_guard"
    elif "STRONG_NEGATIVE" in proxy_class:
        action_class = "avoid_filter"
    elif "POSITIVE" in proxy_class:
        action_class = "follow_scorer"
    if action_class:
        scope["action_class"] = action_class

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    if scope:
        enriched["event_scope"] = {**existing_scope, **scope}
        for field, value in scope.items():
            enriched.setdefault(field, value)

    row_id = enriched.get("numeric_result_row_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched.setdefault("source_name", "moonshot_unified_numeric_result_table")
    enriched.setdefault("evidence_family", "moonshot_unified_numeric_result")
    enriched.setdefault("source_group", "unified_numeric_result_table")
    enriched.setdefault(
        "source_role",
        "nofill_numeric_path_quality"
        if source_component.startswith("nofill_")
        else "numeric_result_table_context",
    )
    enriched.setdefault(
        "system_surface",
        "nofill_pending_policy_runtime"
        if source_component.startswith("nofill_")
        else "moonshot_unified_numeric_result_runtime",
    )
    enriched.setdefault("source_component", source_component)
    enriched.setdefault("route_family", route_family)
    enriched.setdefault("implementation_action", keep_decision or computed_decision)
    if action_class:
        enriched.setdefault("action_class", action_class)
    if "NEGATIVE" in proxy_class:
        enriched.setdefault("r_evidence_class", "UNIFIED_NUMERIC_NEGATIVE_PROXY")
    elif "POSITIVE" in proxy_class:
        enriched.setdefault("r_evidence_class", "UNIFIED_NUMERIC_POSITIVE_PROXY")
    elif "NO_NUMERIC_PROXY" in proxy_class:
        enriched.setdefault("r_evidence_class", "UNIFIED_NUMERIC_SOURCE_GEOMETRY_CONTEXT")
    else:
        enriched.setdefault("r_evidence_class", "UNIFIED_NUMERIC_CONTEXT_PROXY")
    enriched.setdefault("runtime_effect_now", "moonshot_unified_numeric_result_runtime_evidence")
    enriched.setdefault("runtime_candidate_use_permitted", False)
    enriched.setdefault("source_bound", bool(symbol and source_component))
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    for field_name in MOONSHOT_NUMERIC_PROXY_FIELDS:
        if (proxy_value := _to_float(enriched.get(field_name))) is not None:
            payload = _metric_from_scalar(proxy_value, source_field=field_name)
            if payload:
                metrics.setdefault("proxy_score", payload)
            break
    exact_r = _metric_from_scalar(
        enriched.get("exact_r_value"),
        source_field="exact_r_value",
    )
    if exact_r:
        metrics.setdefault("cost_adjusted_simulated_r", exact_r)
    effective_n = (
        _metric_from_count_dict(
            enriched.get("target_stop_status_counts"),
            source_field="target_stop_status_counts",
        )
        or _metric_from_count_dict(
            enriched.get("cost_sensitivity_counts"),
            source_field="cost_sensitivity_counts",
        )
        or _metric_from_scalar(1, source_field="unified_numeric_result_row")
    )
    if effective_n:
        metrics.setdefault("effective_n", effective_n)
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _enrich_moonshot_exact_r_missing_proof_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert exact-R impossibility/proof rows into runtime source-repair guards."""
    if not row.get("numeric_result_row_id") or not row.get("exact_r_status"):
        return row
    missing_fields = row.get("exact_missing_field_proof")
    if not isinstance(missing_fields, list):
        return row
    loaded_from = _normalized(row.get("_gtos_vnext_loaded_from") or row.get("source_path"))
    if (
        "exact_r_or_missing_proof_ledger" not in loaded_from.casefold()
        and "exact_r_or_missing_proof" not in loaded_from.casefold()
    ):
        return row

    enriched = dict(row)
    exact_status = _normalized(enriched.get("exact_r_status")).upper()
    implementation_action = MOONSHOT_EXACT_R_MISSING_PROOF_ACTION_BY_STATUS.get(
        exact_status,
        "SOURCE_JOIN_REPAIR_REQUIRED",
    )
    source_component = _normalized(enriched.get("source_component"))
    symbol = _normalized(enriched.get("symbol"))
    route_session = _normalized(enriched.get("route_session"))
    horizon_id = _normalized(enriched.get("horizon_id"))
    route_family = (
        "nofill_mechanical"
        if source_component.startswith("nofill_")
        else "numeric_router"
    )

    scope = {
        key: value
        for key, value in {
            "symbol": symbol,
            "source_symbol": symbol,
            "market": symbol,
            "route_session": route_session,
            "horizon_id": horizon_id,
            "route_family": route_family,
            "source_component": source_component,
            "action_class": "context_guard",
        }.items()
        if value not in (None, "")
    }
    if family := _symbol_family_for(symbol):
        scope["symbol_family"] = family

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    if scope:
        enriched["event_scope"] = {**existing_scope, **scope}
        for field, value in scope.items():
            enriched.setdefault(field, value)

    row_id = enriched.get("numeric_result_row_id")
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_exact_r_missing_proof"
    enriched["evidence_family"] = "moonshot_exact_r_missing_proof"
    enriched["source_group"] = "exact_r_missing_proof"
    enriched["source_role"] = "exact_r_source_repair_proof"
    enriched["system_surface"] = "exact_r_source_repair_runtime_guard"
    enriched["source_component"] = source_component
    enriched["route_family"] = route_family
    enriched["implementation_action"] = implementation_action
    enriched["action_class"] = "context_guard"
    enriched["r_evidence_class"] = "SOURCE_REPAIR_FOR_EXACT_R"
    enriched["runtime_effect_now"] = "exact_r_source_repair_risk_guard"
    enriched["candidate_use_allowed_now"] = False
    enriched["runtime_candidate_use_permitted"] = False
    enriched["source_complete"] = False
    enriched["source_bound"] = bool(symbol and source_component and route_session)
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    effective_n = _metric_from_scalar(1, source_field="exact_r_missing_proof_row")
    if effective_n:
        metrics["effective_n"] = effective_n
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _source_geometry_repair_implementation_action(raw_action: Any) -> str:
    action = _normalized(raw_action).casefold()
    if "source_sidecar" in action or "branch_replay" in action or "source_join" in action:
        return "SOURCE_JOIN_REPAIR_REQUIRED"
    return "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R"


def _enrich_moonshot_source_geometry_repair_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert source-geometry repair proof rows into runtime source-repair guards."""
    if not row.get("source_geometry_repair_row_id"):
        return row

    enriched = dict(row)
    proof = (
        enriched.get("missing_source_or_geometry_proof")
        if isinstance(enriched.get("missing_source_or_geometry_proof"), dict)
        else {}
    )
    source_component = _normalized(enriched.get("source_component"))
    symbol = _normalized(enriched.get("symbol"))
    route_session = _normalized(enriched.get("route_session"))
    horizon_id = _normalized(enriched.get("horizon_id"))
    route_family = _route_family_for_source_component(source_component)
    implementation_action = _source_geometry_repair_implementation_action(
        enriched.get("repair_implementation_action")
    )

    for field in (
        "branch_match_status",
        "cost_stress_status",
        "target_stop_order_class",
        "exact_missing_field_proof",
    ):
        if field in proof:
            enriched[field] = proof[field]

    scope = {
        key: value
        for key, value in {
            "symbol": symbol,
            "source_symbol": symbol,
            "market": symbol,
            "route_session": route_session,
            "horizon_id": horizon_id,
            "route_family": route_family,
            "source_component": source_component,
            "target_stop_order_class": enriched.get("target_stop_order_class"),
        }.items()
        if value not in (None, "")
    }
    if family := _symbol_family_for(symbol):
        scope["symbol_family"] = family

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    if scope:
        enriched["event_scope"] = {**existing_scope, **scope}
        for field, value in scope.items():
            enriched.setdefault(field, value)

    row_id = enriched.get("source_geometry_repair_row_id")
    enriched["row_key"] = row_id
    enriched.setdefault("numeric_result_row_id", enriched.get("input_numeric_result_row_id"))
    enriched["source_name"] = "moonshot_source_geometry_repair"
    enriched["evidence_family"] = "moonshot_source_geometry_repair"
    enriched["source_group"] = "source_repair_proof"
    enriched["source_role"] = "exact_r_source_geometry_repair_proof"
    enriched["system_surface"] = "source_geometry_repair_runtime_guard"
    enriched["source_component"] = source_component
    enriched["route_family"] = route_family
    enriched["implementation_action"] = implementation_action
    enriched["r_evidence_class"] = "SOURCE_REPAIR_FOR_EXACT_R"
    enriched["runtime_effect_now"] = "source_geometry_repair_risk_guard"
    enriched["candidate_use_allowed_now"] = False
    enriched["runtime_candidate_use_permitted"] = False
    enriched["source_complete"] = False
    enriched["source_bound"] = bool(symbol and source_component and route_session)
    enriched["source_geometry_repair_runtime_ready"] = True
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    effective_n = _metric_from_scalar(1, source_field="source_geometry_repair_row")
    if effective_n:
        metrics["effective_n"] = effective_n
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _recommendation_bucket_action_class(
    *,
    bucket_family: str,
    bucket_value: str,
    decision_group: str,
) -> str:
    text = " ".join((bucket_family, bucket_value, decision_group)).upper()
    if "AVOID" in text or "FAILURE" in text or "STRONG_NEGATIVE" in text:
        return "avoid_filter"
    if (
        "SOURCE_OR_CONTROL_REPAIR" in text
        or "GUARD" in text
        or "REDESIGN" in text
        or "RECHECK" in text
    ):
        return "context_guard"
    if "IMPLEMENT" in text or "SCORE_WITH_CONTROL" in text or "POSITIVE" in text:
        return "follow_scorer"
    return "context_guard"


def _enrich_moonshot_recommendation_bucket_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert recommendation merge bucket rows into source-bound runtime priors.

    These rows are rollups over source-component/action recommendation buckets,
    not standalone trade evidence. Keep their matching scope empty so they only
    attach after a selected row has already anchored the same source_component.
    """
    if not row.get("bucket_id"):
        return row

    bucket_family = _normalized(row.get("bucket_family"))
    bucket_value = _normalized(row.get("bucket_value"))
    if not bucket_family or not bucket_value:
        return row

    component = ""
    decision_group = ""
    if bucket_family == "source_component":
        component = bucket_value
    elif bucket_family == "source_component_decision_group":
        component, _sep, decision_group = bucket_value.partition("|")
        component = _normalized(component)
        decision_group = _normalized(decision_group)
    elif bucket_family == "unified_decision_group":
        decision_group = bucket_value

    route_family = _route_family_for_source_component(component) if component else ""
    action_class = _recommendation_bucket_action_class(
        bucket_family=bucket_family,
        bucket_value=bucket_value,
        decision_group=decision_group,
    )
    implementation_action = (
        f"RECOMMENDATION_BUCKET_{decision_group}"
        if decision_group
        else f"RECOMMENDATION_BUCKET_{bucket_family.upper()}"
    )

    enriched = dict(row)
    row_id = enriched.get("bucket_id")
    enriched["row_key"] = row_id
    enriched["source_row_id"] = row_id
    enriched["source_name"] = "moonshot_recommendation_merge_bucket"
    enriched["evidence_family"] = "moonshot_recommendation_merge_bucket"
    enriched["source_group"] = "recommendation_merge_bucket_rollup"
    enriched["source_role"] = (
        "source_component_recommendation_bucket_prior"
        if component
        else "global_recommendation_bucket_context"
    )
    enriched["system_surface"] = "recommendation_bucket_prior_context"
    enriched["runtime_effect_now"] = "source_component_recommendation_bucket_risk_prior"
    enriched["candidate_use_allowed_now"] = False
    enriched["runtime_candidate_use_permitted"] = False
    enriched["source_complete"] = False
    enriched["source_bound"] = bool(component)
    enriched["recommendation_bucket_family"] = bucket_family
    enriched["recommendation_bucket_value"] = bucket_value
    enriched["recommendation_decision_group"] = decision_group
    enriched["action_class"] = action_class
    enriched["implementation_action"] = implementation_action
    enriched["r_evidence_class"] = "RECOMMENDATION_BUCKET_PRIOR"
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))
    if component:
        enriched["source_component"] = component
        enriched["route_family"] = route_family
    # Empty scope prevents broad bucket-only rows from matching live events.
    enriched["event_scope"] = {}

    metrics = dict(enriched.get("r_metrics") or {})
    effective_n = _metric_from_scalar(
        enriched.get("row_count"),
        source_field="recommendation_bucket_row_count",
    )
    if effective_n:
        metrics["effective_n"] = effective_n
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _enrich_moonshot_recommendation_family_rollup_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert recommendation family rollup rows into anchored risk priors.

    The family rollup has useful row-count pressure by source_component and
    decision_group, but it is not trade evidence. Keep scope empty so it only
    attaches after another row has already anchored the same source_component.
    """
    row_id = row.get("unified_system_rollup_row_id")
    rollup_key = _normalized(row.get("rollup_key"))
    rollup_type = _normalized(row.get("rollup_type"))
    if not row_id or rollup_type != "source_component_decision_group":
        return row
    component, sep, decision_group = rollup_key.partition("|")
    component = _normalized(component)
    decision_group = _normalized(decision_group)
    if sep != "|" or not component or not decision_group:
        return row

    candidate_rows = _to_float(row.get("candidate_rows"))
    row_count: float | None = candidate_rows
    if row_count is None:
        row_count = sum(
            _to_float(row.get(field)) or 0.0
            for field in (
                "implement_rows",
                "score_with_control_rows",
                "source_or_control_repair_rows",
                "guard_rows",
                "redesign_rows",
                "preserve_audit_rows",
            )
        )
    route_family = _route_family_for_source_component(component)
    action_class = _recommendation_bucket_action_class(
        bucket_family=rollup_type,
        bucket_value=component,
        decision_group=decision_group,
    )

    enriched = dict(row)
    enriched["row_key"] = row_id
    enriched["source_row_id"] = row_id
    enriched["source_name"] = "moonshot_recommendation_family_rollup"
    enriched["evidence_family"] = "moonshot_recommendation_family_rollup"
    enriched["source_group"] = "recommendation_merge_family_rollup"
    enriched["source_role"] = "source_component_recommendation_family_prior"
    enriched["system_surface"] = "recommendation_family_rollup_prior_context"
    enriched["runtime_effect_now"] = "source_component_recommendation_family_rollup_risk_prior"
    enriched["candidate_use_allowed_now"] = False
    enriched["runtime_candidate_use_permitted"] = False
    enriched["source_complete"] = False
    enriched["source_bound"] = True
    enriched["source_component"] = component
    enriched["route_family"] = route_family
    enriched["recommendation_family_rollup_id"] = row_id
    enriched["recommendation_family_rollup_type"] = rollup_type
    enriched["recommendation_family_rollup_key"] = rollup_key
    enriched["recommendation_family_rollup_candidate_rows"] = row.get("candidate_rows")
    enriched["recommendation_decision_group"] = decision_group
    enriched["action_class"] = action_class
    enriched["implementation_action"] = f"RECOMMENDATION_FAMILY_ROLLUP_{decision_group}"
    enriched["r_evidence_class"] = "RECOMMENDATION_FAMILY_ROLLUP_PRIOR"
    if row_count is not None:
        enriched["row_count"] = int(row_count) if float(row_count).is_integer() else row_count
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched["event_scope"] = {}

    metrics = dict(enriched.get("r_metrics") or {})
    effective_n = _metric_from_scalar(
        enriched.get("row_count"),
        source_field="recommendation_family_rollup_row_count",
    )
    if effective_n:
        metrics["effective_n"] = effective_n
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _recommendation_candidate_dimension(value: Any) -> str:
    normalized = _normalized(value)
    if not normalized or normalized.casefold() == "none":
        return ""
    return normalized


def _enrich_moonshot_recommendation_unified_candidate_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert full recommendation candidate rows into anchored runtime priors.

    The unified candidate artifact is the full 17,916-row denominator behind
    the recommendation rollups. Its rows explicitly disable runtime scoring and
    live effect, so they must not match standalone. They do carry exact source
    row ids, symbol/session/horizon/primitive dimensions, decision groups, and
    proxy/module scores; attach them only after a source-bound row anchors the
    same source_component and matching scope.
    """
    row_id = row.get("unified_system_candidate_row_id")
    if not row_id:
        return row

    component = _recommendation_candidate_dimension(row.get("source_component"))
    component_valid = bool(component and RUNTIME_SOURCE_COMPONENT_RE.fullmatch(component))
    decision_group = _recommendation_candidate_dimension(row.get("unified_decision_group"))
    unified_action = _recommendation_candidate_dimension(
        row.get("unified_action_class") or row.get("implementation_implication")
    )
    action_class = _recommendation_bucket_action_class(
        bucket_family="unified_candidate",
        bucket_value=" ".join(
            item
            for item in (
                component,
                unified_action,
                _recommendation_candidate_dimension(row.get("source_status")),
            )
            if item
        ),
        decision_group=decision_group,
    )

    enriched = dict(row)
    enriched["row_key"] = row_id
    enriched["source_name"] = "moonshot_recommendation_unified_candidate"
    enriched["evidence_family"] = "moonshot_recommendation_unified_candidate"
    enriched["source_group"] = "recommendation_merge_unified_candidate"
    enriched["source_role"] = "source_component_recommendation_candidate_prior"
    enriched["system_surface"] = "recommendation_unified_candidate_prior_context"
    enriched["runtime_effect_now"] = "source_component_recommendation_unified_candidate_risk_prior"
    enriched["candidate_use_allowed_now"] = False
    enriched["runtime_candidate_use_permitted"] = False
    enriched["source_complete"] = False
    enriched["source_bound"] = component_valid
    enriched["row_count"] = 1
    enriched["recommendation_unified_candidate_id"] = row_id
    enriched["recommendation_unified_candidate_source_row_id"] = row.get("source_row_id")
    enriched["recommendation_unified_candidate_surface"] = row.get(
        "unified_system_recommendation_surface"
    )
    enriched["recommendation_unified_candidate_decision"] = row.get(
        "unified_system_decision"
    )
    enriched["recommendation_unified_candidate_action_class"] = row.get(
        "unified_action_class"
    )
    enriched["recommendation_decision_group"] = decision_group
    enriched["action_class"] = action_class
    enriched["implementation_action"] = (
        row.get("implementation_implication") or row.get("unified_action_class")
    )
    enriched["r_evidence_class"] = "RECOMMENDATION_UNIFIED_CANDIDATE_PRIOR"

    symbol = _recommendation_candidate_dimension(row.get("symbol"))
    session = _recommendation_candidate_dimension(row.get("route_session"))
    horizon = _recommendation_candidate_dimension(row.get("horizon_id"))
    primitive = _recommendation_candidate_dimension(row.get("primitive_flag"))
    if symbol:
        enriched["symbol"] = symbol
        enriched["source_symbol"] = symbol
        family = _symbol_family_for(symbol)
        if family:
            enriched["symbol_family"] = family
            enriched["market"] = family
    if session:
        enriched["route_session"] = session
    if horizon:
        enriched["horizon_id"] = horizon
    if primitive:
        enriched["primitive"] = primitive
        enriched["recommendation_unified_candidate_primitive"] = primitive
    if component_valid:
        enriched["source_component"] = component
        enriched["route_family"] = _route_family_for_source_component(component)

    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched["event_scope"] = {}

    metrics = dict(enriched.get("r_metrics") or {})
    proxy_metric = _metric_from_scalar(
        enriched.get("proxy_or_module_score"),
        source_field="recommendation_unified_candidate_proxy_or_module_score",
    )
    if proxy_metric:
        metrics["proxy_score"] = proxy_metric
    effective_n = _metric_from_scalar(
        1,
        source_field="recommendation_unified_candidate_row",
    )
    if effective_n:
        metrics["effective_n"] = effective_n
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _parse_recommendation_scope_rollup_key(rollup_key: Any) -> dict[str, str]:
    parsed: dict[str, str] = {}
    component_parts: list[str] = []
    for part in str(rollup_key or "").split("|"):
        if "=" in part:
            key, value = part.split("=", 1)
            normalized_value = _normalized(value)
            parsed[_normalized(key)] = "" if normalized_value == "None" else normalized_value
        elif part:
            component_parts.append(part)
    parsed["source_component"] = "|".join(component_parts)
    return parsed


def _recommendation_decision_group_row_counts(row: dict[str, Any]) -> dict[str, float | int]:
    counts: dict[str, float] = {}
    source_fields = {
        "IMPLEMENT": "implement_rows",
        "SCORE_WITH_CONTROL": "score_with_control_rows",
        "SOURCE_OR_CONTROL_REPAIR": "source_or_control_repair_rows",
        "GUARD": "guard_rows",
        "REDESIGN": "redesign_rows",
        "PRESERVE_AUDIT": "preserve_audit_rows",
    }
    for group, field in source_fields.items():
        value = _to_float(row.get(field)) or 0.0
        if value > 0:
            counts[group] = value

    represented = sum(counts.values())
    candidate_rows = _to_float(row.get("candidate_rows")) or 0.0
    unrepresented = max(0.0, candidate_rows - represented)
    for group in row.get("decision_groups") or ():
        normalized = _normalized(group)
        if normalized and normalized not in counts and unrepresented > 0:
            counts[normalized] = unrepresented
            break

    return {
        group: int(value) if float(value).is_integer() else value
        for group, value in sorted(counts.items())
    }


def _dominant_recommendation_decision_group(counts: dict[str, float | int]) -> str:
    ranked: list[tuple[float, str]] = []
    for group, value in counts.items():
        numeric = _to_float(value)
        if group and numeric is not None:
            ranked.append((numeric, group))
    if not ranked:
        return ""
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][1]


def _enrich_moonshot_recommendation_scope_rollup_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert recommendation scope rollups into scoped anchored priors.

    Scope rollups carry useful row-count pressure by symbol/session/horizon/
    primitive/source_component, but the artifact explicitly disables runtime
    score use. Keep event_scope empty so these rows cannot vote standalone;
    they only attach after a selected row anchors the same source_component and
    the scope dimensions match the current event.
    """
    row_id = row.get("unified_system_rollup_row_id")
    rollup_key = _normalized(row.get("rollup_key"))
    rollup_type = _normalized(row.get("rollup_type"))
    if not row_id or rollup_type != "scope_component" or not rollup_key:
        return row

    parsed = _parse_recommendation_scope_rollup_key(rollup_key)
    component = _normalized(parsed.get("source_component"))
    component_valid = bool(component and RUNTIME_SOURCE_COMPONENT_RE.fullmatch(component))
    decision_group_counts = _recommendation_decision_group_row_counts(row)
    decision_group = _dominant_recommendation_decision_group(decision_group_counts)
    candidate_rows = _to_float(row.get("candidate_rows"))
    row_count: float | None = candidate_rows
    if row_count is None and decision_group_counts:
        row_count = sum(_to_float(value) or 0.0 for value in decision_group_counts.values())
    action_class = _recommendation_bucket_action_class(
        bucket_family=rollup_type,
        bucket_value=component,
        decision_group=decision_group,
    )

    enriched = dict(row)
    enriched["row_key"] = row_id
    enriched["source_row_id"] = row_id
    enriched["source_name"] = "moonshot_recommendation_scope_rollup"
    enriched["evidence_family"] = "moonshot_recommendation_scope_rollup"
    enriched["source_group"] = "recommendation_merge_scope_rollup"
    enriched["source_role"] = "scoped_recommendation_component_prior"
    enriched["system_surface"] = "recommendation_scope_rollup_prior_context"
    enriched["runtime_effect_now"] = "scoped_recommendation_scope_rollup_risk_prior"
    enriched["candidate_use_allowed_now"] = False
    enriched["runtime_candidate_use_permitted"] = False
    enriched["source_complete"] = False
    enriched["source_bound"] = component_valid
    enriched["recommendation_scope_rollup_id"] = row_id
    enriched["recommendation_scope_rollup_type"] = rollup_type
    enriched["recommendation_scope_rollup_key"] = rollup_key
    enriched["recommendation_scope_rollup_candidate_rows"] = row.get("candidate_rows")
    enriched["recommendation_scope_rollup_decision_group_row_counts"] = decision_group_counts
    enriched["recommendation_decision_group"] = decision_group
    enriched["action_class"] = action_class
    enriched["implementation_action"] = (
        f"RECOMMENDATION_SCOPE_ROLLUP_{decision_group}"
        if decision_group
        else "RECOMMENDATION_SCOPE_ROLLUP"
    )
    enriched["r_evidence_class"] = "RECOMMENDATION_SCOPE_ROLLUP_PRIOR"
    if row_count is not None:
        enriched["row_count"] = int(row_count) if float(row_count).is_integer() else row_count

    symbol = _normalized(parsed.get("symbol"))
    session = _normalized(parsed.get("session"))
    horizon = _normalized(parsed.get("horizon"))
    primitive = _normalized(parsed.get("primitive"))
    if symbol:
        enriched["symbol"] = symbol
        enriched["source_symbol"] = symbol
        family = _symbol_family_for(symbol)
        if family:
            enriched["symbol_family"] = family
            enriched["market"] = family
    if session:
        enriched["route_session"] = session
    if horizon:
        enriched["horizon_id"] = horizon
    if primitive:
        enriched["primitive"] = primitive
        enriched["recommendation_scope_rollup_primitive"] = primitive
    if component_valid:
        enriched["source_component"] = component
        enriched["route_family"] = _route_family_for_source_component(component)
    else:
        enriched["recommendation_scope_rollup_unanchored_component"] = component

    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched["event_scope"] = {}

    metrics = dict(enriched.get("r_metrics") or {})
    effective_n = _metric_from_scalar(
        enriched.get("row_count"),
        source_field="recommendation_scope_rollup_row_count",
    )
    if effective_n:
        metrics["effective_n"] = effective_n
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _dominant_count_key(payload: Any) -> str:
    if not isinstance(payload, dict) or not payload:
        return ""
    ranked: list[tuple[float, str]] = []
    for key, value in payload.items():
        numeric = _to_float(value)
        if key in (None, "") or numeric is None:
            continue
        ranked.append((numeric, str(key)))
    if not ranked:
        return ""
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][1]


def _dominant_proxy_class(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    positive = sum(
        _to_float(payload.get(key)) or 0.0
        for key in ("STRONG_POSITIVE_PROXY_R", "POSITIVE_PROXY_R")
    )
    negative = sum(
        _to_float(payload.get(key)) or 0.0
        for key in ("STRONG_NEGATIVE_PROXY_R", "NEGATIVE_PROXY_R")
    )
    if negative > positive:
        return "STRONG_NEGATIVE_PROXY_R" if payload.get("STRONG_NEGATIVE_PROXY_R") else "NEGATIVE_PROXY_R"
    if positive > negative:
        return "STRONG_POSITIVE_PROXY_R" if payload.get("STRONG_POSITIVE_PROXY_R") else "POSITIVE_PROXY_R"
    return _dominant_count_key(payload)


def _enrich_moonshot_source_component_summary_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert source-component rollups into component-level risk priors."""
    if _normalized(row.get("rollup_type")) != "source_component_expectancy":
        return row
    component = _normalized(row.get("rollup_key"))
    if not component:
        return row

    enriched = dict(row)
    row_id = enriched.get("numeric_rollup_row_id") or component
    decision_action = _dominant_count_key(enriched.get("decision_counts"))
    proxy_class = _dominant_proxy_class(enriched.get("proxy_r_class_counts"))
    target_stop_class = _dominant_count_key(enriched.get("target_stop_order_counts"))
    route_family = "nofill_mechanical" if component.startswith("nofill_") else "numeric_router"

    action_class = "context_guard"
    if "AVOID" in decision_action or "NEGATIVE_PROXY" in proxy_class:
        action_class = "avoid_filter"
    elif (
        "KEEP_" in decision_action
        or "IMPLEMENT_DEFAULT_OFF_SCORER" in decision_action
        or "POSITIVE_PROXY" in proxy_class
    ):
        action_class = "follow_scorer"

    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = "moonshot_source_component_summary"
    enriched["evidence_family"] = "moonshot_source_component_summary"
    enriched["source_group"] = "source_component_summary_rollup"
    enriched["source_role"] = "component_expectancy_prior"
    enriched["system_surface"] = "source_component_summary_risk_prior"
    enriched["source_component"] = component
    enriched["route_family"] = route_family
    enriched["implementation_action"] = decision_action
    enriched["action_class"] = action_class
    enriched["proxy_r_class"] = proxy_class
    enriched["target_stop_order_class"] = target_stop_class
    enriched["r_evidence_class"] = "SOURCE_COMPONENT_SUMMARY_PROXY_R"
    enriched["runtime_effect_now"] = "source_component_summary_risk_prior"
    enriched["candidate_use_allowed_now"] = False
    enriched["runtime_candidate_use_permitted"] = False
    enriched["source_complete"] = False
    enriched["source_bound"] = bool(component)
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    scope = {
        "source_component": component,
        "route_family": route_family,
        "action_class": action_class,
    }
    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}

    metrics = dict(enriched.get("r_metrics") or {})
    proxy_metric = _metric_from_mean_count(
        enriched.get("proxy_r_mean"),
        enriched.get("numeric_proxy_r_count"),
        source_field="source_component_summary_proxy_r_mean",
    )
    if proxy_metric:
        metrics["proxy_score"] = proxy_metric
    effective_n = _metric_from_scalar(
        enriched.get("row_count"),
        source_field="source_component_summary_row_count",
    )
    if effective_n:
        metrics["effective_n"] = effective_n
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _market_gap_primitive_source_name(row: dict[str, Any]) -> str:
    if row.get("market_gap_code_id"):
        return "moonshot_market_gap_code_candidate"
    if row.get("market_gap_candidate_score_id"):
        return "moonshot_market_gap_candidate_score"
    if row.get("market_gap_transfer_context_id"):
        return "moonshot_market_gap_transfer_context"
    if row.get("market_gap_action_id"):
        return "moonshot_market_gap_primitive_action"
    if row.get("market_gap_combo_id"):
        return "moonshot_market_gap_primitive_combo"
    return ""


def _market_gap_primitive_row_id(row: dict[str, Any]) -> str:
    for key in (
        "market_gap_code_id",
        "market_gap_candidate_score_id",
        "market_gap_transfer_context_id",
        "market_gap_action_id",
        "market_gap_combo_id",
    ):
        value = _normalized(row.get(key))
        if value:
            return value
    return ""


def _market_gap_primitive_action_tokens(row: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for key in (
        "next_same_resource_action",
        "unified_execution_decision",
        "implementation_candidate_type",
        "candidate_score_class",
        "code_candidate_status",
        "market_gap_replay_decision",
    ):
        value = _normalized(row.get(key))
        if value:
            tokens.add(value)
    return tokens


def _market_gap_primitive_decision(row: dict[str, Any]) -> DecisionLabel:
    tokens = _market_gap_primitive_action_tokens(row)
    if tokens & MARKET_GAP_AVOID_ACTIONS:
        return "AVOID"
    if tokens & MARKET_GAP_ENTRY_FOLLOW_ACTIONS:
        return "FOLLOW"
    return "MIXED"


def _market_gap_primitive_action_class(row: dict[str, Any], decision: DecisionLabel) -> str:
    if decision == "AVOID":
        return "avoid_filter"
    if decision == "FOLLOW":
        return "follow_scorer"
    tokens = _market_gap_primitive_action_tokens(row)
    if tokens & MARKET_GAP_SOURCE_EXPANSION_ACTIONS:
        return "source_expansion_required"
    if tokens & MARKET_GAP_ENTRY_CONTEXT_ACTIONS:
        return "entry_geometry_context_guard"
    return "context_guard"


def _market_gap_primitive_r_evidence_class(
    row: dict[str, Any],
    decision: DecisionLabel,
) -> str:
    if decision == "AVOID":
        return "MARKET_GAP_AVOID_INVERSE_PROXY"
    if decision == "FOLLOW":
        return "MARKET_GAP_ENTRY_GEOMETRY_PROXY"
    tokens = _market_gap_primitive_action_tokens(row)
    if tokens & MARKET_GAP_SOURCE_EXPANSION_ACTIONS:
        return "MARKET_GAP_SOURCE_ACQUISITION_REQUIRED"
    return "MARKET_GAP_MIXED_ALIGNMENT_CONTEXT"


def _market_gap_primitive_implementation_action(row: dict[str, Any]) -> str:
    for key in (
        "code_candidate_status",
        "market_gap_replay_decision",
        "unified_execution_decision",
        "next_same_resource_action",
        "candidate_score_class",
        "implementation_candidate_type",
    ):
        value = _normalized(row.get(key))
        if value:
            return value
    return "MARKET_GAP_PRIMITIVE_CONTEXT"


def _enrich_moonshot_market_gap_primitive_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert market-gap primitive expansion rows into scoped router evidence."""
    if (
        _normalized(row.get("evidence_family")).casefold().startswith("gtos_vnext_")
        and isinstance(row.get("event_scope"), dict)
    ):
        return row
    source_name = _market_gap_primitive_source_name(row)
    if not source_name:
        return row
    symbol = _normalized(row.get("symbol"))
    primitive = _normalized(row.get("primitive_flag") or row.get("primitive"))
    route_session = _normalized(row.get("route_session") or row.get("mapped_route_session"))
    horizon_id = _normalized(row.get("horizon_id"))
    if not (symbol and primitive and route_session and horizon_id):
        return row

    enriched = dict(row)
    row_id = _market_gap_primitive_row_id(enriched)
    decision = _market_gap_primitive_decision(enriched)
    action_class = _market_gap_primitive_action_class(enriched, decision)
    implementation_action = _market_gap_primitive_implementation_action(enriched)

    scope = {
        "symbol": symbol,
        "source_symbol": symbol,
        "route_session": route_session,
        "horizon_id": horizon_id,
        "primitive": primitive,
        "route_family": "numeric_router",
        "source_component": "market_gap_code",
    }
    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    enriched.setdefault("row_key", row_id)
    enriched.setdefault("source_row_id", row_id)
    enriched["source_name"] = source_name
    enriched["evidence_family"] = "moonshot_market_gap_primitive_expansion"
    enriched["source_group"] = action_class
    enriched["source_role"] = "market_gap_primitive_router_evidence"
    enriched["system_surface"] = "market_gap_primitive_expansion_router"
    enriched["source_component"] = "market_gap_code"
    enriched["route_family"] = "numeric_router"
    enriched["primitive"] = primitive
    enriched["market_gap_action_class"] = _normalized(enriched.get("action_class"))
    enriched["action_class"] = action_class
    enriched["market_gap_code_status"] = _normalized(enriched.get("code_candidate_status"))
    enriched["market_gap_proxy_interval_gate"] = _normalized(enriched.get("proxy_interval_gate"))
    enriched["implementation_action"] = implementation_action
    enriched["decision"] = decision
    enriched["r_evidence_class"] = _market_gap_primitive_r_evidence_class(enriched, decision)
    enriched["runtime_effect_now"] = (
        "market_gap_primitive_avoid_filter"
        if decision == "AVOID"
        else "market_gap_primitive_entry_geometry_follow"
        if decision == "FOLLOW"
        else "market_gap_primitive_source_or_control_context"
    )
    enriched["runtime_candidate_use_permitted"] = decision in {"FOLLOW", "AVOID"}
    enriched["candidate_use_allowed_now"] = decision in {"FOLLOW", "AVOID"}
    enriched["source_bound"] = True
    enriched["source_complete"] = decision in {"FOLLOW", "AVOID"}
    enriched["orderflow_runtime_validated"] = True
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    proxy_value = _first_numeric(
        enriched.get("proxy_score"),
        enriched.get("candidate_score_proxy"),
        enriched.get("delta_mean_abs_future_change"),
        enriched.get("delta_alignment_rate"),
    )
    proxy_metric = _metric_from_scalar(
        proxy_value,
        source_field=(
            "proxy_score"
            if enriched.get("proxy_score") is not None
            else "candidate_score_proxy"
            if enriched.get("candidate_score_proxy") is not None
            else "delta_mean_abs_future_change"
            if enriched.get("delta_mean_abs_future_change") is not None
            else "delta_alignment_rate"
        ),
    )
    if proxy_metric:
        metrics["proxy_score"] = proxy_metric
    stress_metric = _metric_from_scalar(
        enriched.get("delta_alignment_rate"),
        source_field="delta_alignment_rate",
    )
    if stress_metric:
        metrics["stress_simulated_r"] = stress_metric
    effective_n = _metric_from_scalar(
        _first_numeric(enriched.get("flagged_n"), 1),
        source_field="flagged_n_or_row",
    )
    if effective_n:
        metrics["effective_n"] = effective_n
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _nearmiss_join_source_name(row: dict[str, Any]) -> str:
    loaded_from = _normalized(row.get("_gtos_vnext_loaded_from") or row.get("source_path")).casefold()
    if "nearmiss_market_entry_join_market_entry_join_ledger" in loaded_from:
        return "moonshot_nearmiss_market_entry"
    if "nearmiss_market_entry_join_offset_join_ledger" in loaded_from:
        return "moonshot_nearmiss_offset"
    if "nearmiss_market_entry_join_source_requirement_join_ledger" in loaded_from:
        return "moonshot_nearmiss_source_requirement"
    if "nearmiss_market_entry_join_branch_summary_ledger" in loaded_from:
        return "moonshot_nearmiss_branch_summary"
    return ""


def _nearmiss_join_source_component(source_name: str) -> str:
    return {
        "moonshot_nearmiss_market_entry": "nofill_near_miss_market_entry",
        "moonshot_nearmiss_offset": "nofill_near_miss_offset",
        "moonshot_nearmiss_source_requirement": "nofill_near_miss_source_requirement",
        "moonshot_nearmiss_branch_summary": "nofill_nearmiss_branch_summary",
    }.get(source_name, "")


def _nearmiss_join_row_id(row: dict[str, Any]) -> str:
    for field_name in (
        "near_miss_entry_control_market_branch_id",
        "near_miss_entry_control_offset_branch_id",
        "near_miss_entry_control_source_requirement_id",
        "nearmiss_transfer_branch_summary_id",
        "system_transfer_branch_id",
        "branch_queue_id",
    ):
        if value := _normalized(row.get(field_name)):
            return value
    return _row_identity(row)


def _nearmiss_join_touch_class(row: dict[str, Any]) -> str:
    return _normalized(row.get("market_touch_class") or row.get("offset_touch_class")).upper()


def _nearmiss_join_decision(row: dict[str, Any]) -> DecisionLabel:
    touch_class = _nearmiss_join_touch_class(row)
    decision_direction = _normalized(row.get("decision_direction")).upper()
    branch_result = _normalized(row.get("branch_result_binary")).upper()
    target_stop_result = _normalized(row.get("target_stop_result")).upper()
    if (
        touch_class == "TARGET_FIRST_OR_ONLY"
        and decision_direction == "KEEP_CHALLENGER"
        and branch_result == "ACCEPTED"
    ):
        return "FOLLOW"
    if (
        touch_class == "STOP_FIRST_OR_ONLY"
        or decision_direction in {"KILL_OR_REDESIGN", "KEEP_REPAIR_OR_AVOID"}
        or branch_result == "REJECTED"
    ):
        return "AVOID"
    if target_stop_result == "STOP_FIRST_PROXY_DOMINANT" and decision_direction not in {
        "KEEP_CHALLENGER",
        "",
    }:
        return "AVOID"
    return "MIXED"


def _nearmiss_join_target_stop_order_class(row: dict[str, Any]) -> str:
    touch_class = _nearmiss_join_touch_class(row)
    if touch_class == "TARGET_FIRST_OR_ONLY":
        return "TARGET_FIRST_PROXY_DOMINANT"
    if touch_class == "STOP_FIRST_OR_ONLY":
        return "STOP_FIRST_PROXY_DOMINANT"
    if touch_class == "TARGET_STOP_SAME_M15_AMBIGUOUS":
        return "ORDERING_AMBIGUITY_DOMINANT"
    if touch_class == "NO_TARGET_OR_STOP_TOUCH":
        return "NO_TARGET_STOP_TOUCH_DESCRIPTOR_DOMINANT"
    return _normalized(row.get("target_stop_result")).upper()


def _nearmiss_join_action_class(source_component: str, decision: DecisionLabel) -> str:
    if source_component == "nofill_near_miss_market_entry":
        if decision == "FOLLOW":
            return "nearmiss_market_entry_follow"
        if decision == "AVOID":
            return "nearmiss_market_entry_avoid_filter"
        return "nearmiss_market_entry_context_guard"
    if source_component == "nofill_near_miss_offset":
        if decision == "FOLLOW":
            return "nearmiss_offset_follow"
        if decision == "AVOID":
            return "nearmiss_offset_avoid_filter"
        return "nearmiss_offset_context_guard"
    if source_component == "nofill_near_miss_source_requirement":
        if decision == "AVOID":
            return "nearmiss_source_requirement_avoid_filter"
        return "nearmiss_source_requirement_guard"
    if decision == "AVOID":
        return "nearmiss_branch_avoid_filter"
    return "nearmiss_branch_context_guard"


def _nearmiss_join_r_evidence_class(source_component: str, decision: DecisionLabel) -> str:
    if decision == "FOLLOW" and source_component == "nofill_near_miss_market_entry":
        return "NEARMISS_MARKET_ENTRY_TARGET_FIRST_PROXY"
    if decision == "FOLLOW" and source_component == "nofill_near_miss_offset":
        return "NEARMISS_OFFSET_TARGET_FIRST_PROXY"
    if decision == "AVOID":
        return "NEARMISS_STOP_FIRST_OR_KILL_REDESIGN"
    if source_component == "nofill_near_miss_source_requirement":
        return "NEARMISS_SOURCE_REQUIREMENT_CONTEXT"
    return "NEARMISS_JOIN_CONTEXT"


def _nearmiss_join_runtime_effect(source_component: str, decision: DecisionLabel) -> str:
    if decision == "FOLLOW" and source_component == "nofill_near_miss_market_entry":
        return "nearmiss_pending_market_entry_now_candidate"
    if decision == "FOLLOW":
        return "nearmiss_pending_offset_follow_context"
    if decision == "AVOID":
        return "nearmiss_pending_avoid_or_redesign"
    if source_component == "nofill_near_miss_source_requirement":
        return "nearmiss_pending_source_requirement_context"
    return "nearmiss_pending_join_context"


def _nearmiss_join_implementation_action(source_component: str, decision: DecisionLabel) -> str:
    if decision == "FOLLOW" and source_component == "nofill_near_miss_market_entry":
        return "NEARMISS_MARKET_ENTRY_CHALLENGER_REVIEW"
    if decision == "FOLLOW":
        return "NEARMISS_OFFSET_SUPPORT_CHALLENGER_REVIEW"
    if decision == "AVOID":
        return "NEARMISS_MARKET_ENTRY_AVOID_OR_REDESIGN"
    if source_component == "nofill_near_miss_source_requirement":
        return "NEARMISS_SOURCE_REQUIREMENT_REPAIR_CONTEXT"
    return "NEARMISS_BRANCH_CONTEXT"


def _nearmiss_join_signed_proxy(row: dict[str, Any], decision: DecisionLabel) -> float | None:
    raw_value = _first_numeric(
        row.get("market_entry_signed_delta_over_rolling_range"),
        row.get("market_entry_signed_delta_vs_near_limit"),
        row.get("directional_close_units"),
        row.get("directional_favorable_excursion_units"),
        row.get("directional_adverse_excursion_units"),
        row.get("market_target_minus_stop_share"),
        row.get("offset_target_minus_stop_share"),
    )
    if decision == "MIXED":
        return None
    magnitude = abs(float(raw_value)) if raw_value not in (None, 0) else 1.0
    return magnitude if decision == "FOLLOW" else -magnitude


def _enrich_moonshot_nearmiss_market_entry_join_row(row: dict[str, Any]) -> dict[str, Any]:
    source_name = _nearmiss_join_source_name(row)
    if not source_name:
        return row
    source_component = _nearmiss_join_source_component(source_name)
    if not source_component:
        return row

    enriched = dict(row)
    decision = _nearmiss_join_decision(enriched)
    row_id = _nearmiss_join_row_id(enriched)
    scope = _moonshot_route_scope_from_route_candidate(
        enriched,
        source_component=source_component,
    )
    if scope:
        scope["route_family"] = "nofill_mechanical"
        if entry_variant := _normalized(
            enriched.get("source_entry_variant")
            or enriched.get("system_entry_variant")
            or enriched.get("entry_variant")
        ):
            scope["entry_variant"] = entry_variant
        scope["action_family"] = "nearmiss_market_entry_join"
        scope["action_class"] = _nearmiss_join_action_class(source_component, decision)
        if target_stop_order_class := _nearmiss_join_target_stop_order_class(enriched):
            scope["target_stop_order_class"] = target_stop_order_class
        existing_scope = (
            enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
        )
        enriched["event_scope"] = {**existing_scope, **scope}
        for field_name, value in scope.items():
            enriched.setdefault(field_name, value)

    enriched["row_key"] = row_id
    enriched["source_row_id"] = row_id
    enriched["source_name"] = source_name
    enriched["evidence_family"] = "moonshot_nearmiss_market_entry_join"
    enriched["source_role"] = "nearmiss_market_entry_join_evidence"
    enriched["system_surface"] = "nearmiss_market_entry_join_router"
    enriched["source_component"] = source_component
    enriched["route_family"] = "nofill_mechanical"
    enriched["action_family"] = "nearmiss_market_entry_join"
    enriched["action_class"] = _nearmiss_join_action_class(source_component, decision)
    enriched["entry_variant"] = (
        _normalized(enriched.get("source_entry_variant") or enriched.get("system_entry_variant"))
        or enriched.get("entry_variant")
    )
    enriched["target_stop_order_class"] = _nearmiss_join_target_stop_order_class(enriched)
    enriched["proxy_r_class"] = (
        "POSITIVE_PROXY_R"
        if decision == "FOLLOW"
        else "NEGATIVE_PROXY_R"
        if decision == "AVOID"
        else "NEARMISS_MIXED_PROXY_CONTEXT"
    )
    enriched["implementation_action"] = _nearmiss_join_implementation_action(
        source_component,
        decision,
    )
    enriched["decision"] = decision
    enriched["r_evidence_class"] = _nearmiss_join_r_evidence_class(source_component, decision)
    enriched["runtime_effect_now"] = _nearmiss_join_runtime_effect(source_component, decision)
    enriched["runtime_candidate_use_permitted"] = decision in {"FOLLOW", "AVOID"}
    enriched["candidate_use_allowed_now"] = decision in {"FOLLOW", "AVOID"}
    enriched["source_bound"] = True
    enriched["source_complete"] = decision in {"FOLLOW", "AVOID"}
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    proxy_metric = _metric_from_scalar(
        _nearmiss_join_signed_proxy(enriched, decision),
        source_field="nearmiss_join_decision_proxy",
    )
    if proxy_metric:
        metrics["proxy_score"] = proxy_metric
        metrics["stress_simulated_r"] = proxy_metric
    effective_n = _metric_from_scalar(1, source_field="nearmiss_join_row")
    if effective_n:
        metrics["effective_n"] = effective_n
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


EXPANDED_MARKET_IMPLEMENTATION_PATH_TOKENS = (
    "expanded_market_code_candidate",
    "expanded_market_code_candidates",
    "expanded_market_consensus_deconcentration",
    "expanded_market_decon_scorer",
    "expanded_market_deconcentrated_implementation_selection",
    "expanded_market_deconcentrated_scorer_surfaces",
    "expanded_market_deconcentration_execution",
    "expanded_market_final_implementation_decisions",
    "expanded_market_implementation_selection",
    "expanded_market_reduced_implementation_candidates",
    "expanded_market_repair_implementation_acceptance",
    "expanded_market_repair_implementation_handoff",
    "expanded_market_source_expansion_deconcentration",
    "expanded_market_source_expansion_ready_action_implementation",
    "expanded_market_unified_implementation_actions",
    "expanded_market_unified_strict_implementation_readiness",
)


def _expanded_market_implementation_loaded_path(row: dict[str, Any]) -> str:
    return _normalized(row.get("_gtos_vnext_loaded_from") or row.get("source_path")).casefold()


def _is_expanded_market_implementation_row(row: dict[str, Any]) -> bool:
    loaded_from = _expanded_market_implementation_loaded_path(row)
    if not loaded_from or not any(token in loaded_from for token in EXPANDED_MARKET_IMPLEMENTATION_PATH_TOKENS):
        return False
    if row.get("keep_kill_redesign_implement_decision") or row.get("follow_inverse_default_off_avoid_class"):
        return True
    return any(str(key).startswith("expanded_market_") for key in row)


def _expanded_market_row_id(row: dict[str, Any]) -> str:
    for field in (
        "expanded_market_unified_strict_implementation_readiness_row_id",
        "strict_implementation_readiness_row_id",
        "expanded_market_source_expansion_ready_action_implementation_candidate_row_id",
        "final_implementation_decision_row_id",
        "implementation_candidate_row_id",
        "code_candidate_execution_row_id",
        "code_candidate_row_id",
        "implementation_selection_row_id",
        "expanded_market_repair_implementation_handoff_row_id",
        "expanded_market_repair_implementation_handoff_execution_row_id",
        "expanded_market_repair_application_row_id",
        "expanded_market_repair_application_execution_row_id",
        "expanded_market_impl_candidate_execution_row_id",
        "expanded_market_impl_candidate_evidence_row_id",
        "expanded_market_deconcentrated_scorer_surface_row_id",
        "expanded_market_source_expansion_deconcentration_row_id",
    ):
        if value := _normalized(row.get(field)):
            return value
    for field, value in row.items():
        if str(field).endswith("_row_id") and (normalized := _normalized(value)):
            return normalized
    return _normalized(row.get("row_key"))


def _expanded_market_surface(row: dict[str, Any]) -> str:
    for field, value in row.items():
        if str(field).endswith("_surface") and (normalized := _normalized(value)):
            return normalized
    return "expanded_market_implementation_scorer_surface"


def _expanded_market_source_component(row: dict[str, Any]) -> str:
    if component := _normalized(row.get("source_component")):
        return component
    loaded_from = _expanded_market_implementation_loaded_path(row)
    if "source_expansion" in loaded_from:
        return "expanded_market_source_expansion"
    if "deconcentrated_scorer" in loaded_from or "decon_scorer" in loaded_from:
        return "registry_scorer_module"
    if "strict_implementation_readiness" in loaded_from:
        return "registry_scorer_module"
    return "default_off_scorer_application"


def _expanded_market_decision(row: dict[str, Any]) -> DecisionLabel:
    class_text = _normalized(row.get("follow_inverse_default_off_avoid_class")).casefold()
    action_text = _normalized(row.get("keep_kill_redesign_implement_decision")).upper()
    status_text = " ".join(
        _normalized(row.get(field)).upper()
        for field in (
            "execution_status",
            "implementation_candidate_status",
            "implementation_readiness_status",
            "ready_action_implementation_status",
            "branch_local_action_status",
            "final_implementation_decision_status",
        )
    )
    if class_text == "avoid" or "AVOID" in action_text:
        return "AVOID"
    if (
        class_text == "redesign"
        or "REDESIGN" in action_text
        or "REPAIR" in action_text
        or "UNDERPOWERED" in status_text
        or "SCOPE_LEAKAGE" in action_text
        or "TERMINAL_CAPACITY" in action_text
    ):
        return "MIXED"
    if class_text == "follow" or "IMPLEMENT" in action_text or "READY" in status_text:
        return "FOLLOW"
    return "MIXED"


def _expanded_market_implementation_action(row: dict[str, Any], decision: DecisionLabel) -> str:
    loaded_from = _expanded_market_implementation_loaded_path(row)
    action_text = _normalized(row.get("keep_kill_redesign_implement_decision")).upper()
    if decision == "AVOID":
        return "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE"
    if decision == "FOLLOW":
        if "repair_implementation" in loaded_from or "REPAIR" in action_text:
            return "KEEP_SOURCE_REPAIRED_PROXY_AS_DEFAULT_OFF_SCORER_OR_GUARD_INPUT"
        return "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS"
    if "SOURCE_EXPANSION" in action_text or "REPAIR" in action_text:
        return "SOURCE_GEOMETRY_REPAIR_OR_GUARD_BINDING_REQUIRED"
    return "REDESIGN_ONLY"


def _expanded_market_action_class(decision: DecisionLabel) -> str:
    if decision == "FOLLOW":
        return "expanded_market_follow_scorer"
    if decision == "AVOID":
        return "expanded_market_avoid_filter"
    return "expanded_market_context_guard"


def _expanded_market_metric_from_fields(
    row: dict[str, Any],
    *fields: str,
    source_field: str,
) -> dict[str, Any] | None:
    for field in fields:
        metric = _metric_from_scalar(row.get(field), source_field=field)
        if metric:
            return metric
    return None


def _enrich_expanded_market_implementation_row(row: dict[str, Any]) -> dict[str, Any]:
    if not _is_expanded_market_implementation_row(row):
        return row

    enriched = dict(row)
    row_id = _expanded_market_row_id(enriched)
    decision = _expanded_market_decision(enriched)
    source_component = _expanded_market_source_component(enriched)
    side = _normalized(enriched.get("side") or enriched.get("selected_side")).upper()
    symbol = _normalized(enriched.get("symbol"))
    source_symbol = _normalized(enriched.get("source_symbol")) or symbol
    symbol_family = (
        _normalized(enriched.get("symbol_family"))
        or _symbol_family_for(symbol)
        or _symbol_family_for(source_symbol)
    )
    route_session = _normalized(enriched.get("route_session"))
    market_timeframe = _normalized(enriched.get("market_timeframe"))
    horizon_id = _normalized(enriched.get("horizon_id"))
    route_family = _route_family_for_source_component(source_component)
    action_class = _expanded_market_action_class(decision)
    implementation_action = _expanded_market_implementation_action(enriched, decision)

    scope = {
        key: value
        for key, value in {
            "symbol": symbol,
            "source_symbol": source_symbol,
            "symbol_family": symbol_family,
            "market": symbol or source_symbol,
            "market_timeframe": market_timeframe,
            "route_session": route_session,
            "horizon_id": horizon_id,
            "side": side,
            "source_component": source_component,
            "route_family": route_family,
            "action_class": action_class,
        }.items()
        if value not in (None, "")
    }
    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    enriched["row_key"] = row_id or _normalized(enriched.get("row_key"))
    enriched["source_row_id"] = enriched["row_key"]
    enriched["source_name"] = "moonshot_expanded_market_implementation_surface"
    enriched["evidence_family"] = "expanded_market_reduced_surface"
    enriched["source_component"] = source_component
    enriched["route_family"] = route_family
    enriched["action_class"] = action_class
    enriched["implementation_action"] = implementation_action
    enriched["source_group"] = (
        "expanded_market_avoid_filter"
        if decision == "AVOID"
        else "scorer_registry_surface"
        if decision == "FOLLOW"
        else "expanded_market_repair_or_redesign_context"
    )
    enriched["source_role"] = (
        "branch_local_default_off_candidate"
        if decision == "FOLLOW"
        else "expanded_market_avoid_filter_candidate"
        if decision == "AVOID"
        else "expanded_market_repair_or_redesign_context"
    )
    enriched["system_surface"] = _expanded_market_surface(enriched)
    enriched["runtime_effect_now"] = (
        "expanded_market_default_off_follow_scorer"
        if decision == "FOLLOW"
        else "expanded_market_default_off_avoid_filter"
        if decision == "AVOID"
        else "expanded_market_context_repair_or_redesign"
    )
    enriched["r_evidence_class"] = (
        "EXPANDED_MARKET_POSITIVE_PROXY"
        if decision == "FOLLOW"
        else "EXPANDED_MARKET_NEGATIVE_PROXY"
        if decision == "AVOID"
        else "EXPANDED_MARKET_REPAIR_OR_REDESIGN_CONTEXT"
    )
    enriched["runtime_candidate_use_permitted"] = False
    enriched["candidate_use_allowed_now"] = False
    enriched["source_bound"] = bool((symbol or symbol_family) and route_session and side)
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    metrics = dict(enriched.get("r_metrics") or {})
    cost_metric = _expanded_market_metric_from_fields(
        enriched,
        "cost_adjusted_simulated_r",
        "selected_intrabar_cost_adjusted_simulated_r",
        "average_selected_intrabar_cost_adjusted_simulated_r",
        "average_deconcentrated_cost_adjusted_simulated_r",
        "accepted_cost_adjusted_simulated_r",
        "candidate_cost_adjusted_simulated_r",
        "final_repair_artifact_cost_adjusted_simulated_r",
        "alternate_source_proxy_cost_adjusted_simulated_r",
        "execution_cost_adjusted_simulated_r",
        "execution_observed_cost_adjusted_simulated_r",
        "source_expansion_cost_adjusted_simulated_r",
        source_field="expanded_market_cost",
    )
    stress_metric = _expanded_market_metric_from_fields(
        enriched,
        "stress_simulated_r",
        "average_stress_simulated_r",
        "average_deconcentrated_stress_simulated_r",
        "accepted_stress_simulated_r",
        "candidate_stress_simulated_r",
        "final_repair_artifact_stress_simulated_r",
        "execution_observed_stress_simulated_r",
        "source_expansion_stress_simulated_r",
        source_field="expanded_market_stress",
    )
    proxy_metric = _expanded_market_metric_from_fields(
        enriched,
        "selected_minus_rejected_intrabar_cost_adjusted_r",
        "average_selected_minus_rejected_intrabar_cost_adjusted_r",
        "average_numeric_priority_score",
        "max_final_review_score",
        "implementation_priority_score",
        "target_stop_edge_share",
        source_field="expanded_market_proxy",
    )
    effective_n_metric = _expanded_market_metric_from_fields(
        enriched,
        "effective_n",
        "effective_n_sum",
        "evidence_effective_n_sum",
        "accepted_effective_n",
        "candidate_effective_n",
        "final_repair_artifact_effective_n",
        "deconcentrated_effective_n",
        "deconcentrated_effective_n_sum",
        "matched_effective_n_sum",
        "observed_match_rows",
        "strict_execution_match_rows",
        "surface_member_rows",
        "member_rows_decided",
        source_field="expanded_market_effective_n",
    )
    if cost_metric:
        metrics["cost_adjusted_simulated_r"] = cost_metric
    if stress_metric:
        metrics["stress_simulated_r"] = stress_metric
    if proxy_metric:
        metrics["proxy_score"] = proxy_metric
    if effective_n_metric:
        metrics["effective_n"] = effective_n_metric
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


REPAIRED_PROXY_SYMBOL_SURFACE_PATH_TOKENS = (
    "branch_local_repaired_proxy_scope_scorer_application_default_off_score",
    "branch_local_repaired_proxy_scope_scorer_application_avoid_redesign",
    "branch_local_repaired_proxy_scope_scorer_application_repair_required",
    "branch_local_repaired_proxy_scope_scorer_application_registry",
    "branch_local_repaired_proxy_symbol_action_packet_symbol_proxy_surface",
    "branch_local_repaired_proxy_symbol_action_packet_symbol_action_packet",
    "branch_local_repaired_proxy_symbol_action_packet_comparator_registration",
    "branch_local_repaired_proxy_runtime_replay_performance_row",
    "branch_local_repaired_proxy_runtime_candidate_bundle_runtime_candidate",
    "branch_local_repaired_proxy_runtime_candidate_bundle_guard_check",
    "branch_local_repaired_proxy_runtime_candidate_registry_event_probe",
    "branch_local_repaired_proxy_runtime_candidate_registry_registry_module",
    "branch_local_repaired_proxy_registration_specs_registration_spec",
    "branch_local_repaired_proxy_registration_specs_runtime_guard",
    "branch_local_repaired_proxy_registration_specs_symbol_registration_summary",
    "branch_local_repaired_proxy_score_bridge_action_packet_action_scope",
    "branch_local_repaired_proxy_score_bridge_rebuild_score_scope_summary",
    "branch_local_repaired_proxy_score_bridge_rebuild_repair_context_bridge",
    "branch_local_repaired_proxy_score_bridge_rebuild_symbol_summary",
    "branch_local_repaired_proxy_execution_registry_symbol_action",
    "branch_local_repaired_proxy_execution_specs_cost_symbol",
)


def _repaired_proxy_symbol_surface_loaded_path(row: dict[str, Any]) -> str:
    return _normalized(row.get("_gtos_vnext_loaded_from") or row.get("source_path")).casefold()


def _is_repaired_proxy_symbol_surface_row(row: dict[str, Any]) -> bool:
    loaded_from = _repaired_proxy_symbol_surface_loaded_path(row)
    return bool(
        loaded_from
        and "branch_local_repaired_proxy" in loaded_from
        and any(token in loaded_from for token in REPAIRED_PROXY_SYMBOL_SURFACE_PATH_TOKENS)
    )


def _repaired_proxy_symbol_surface_row_id(row: dict[str, Any]) -> str:
    for field in (
        "repaired_proxy_event_application_row_id",
        "symbol_proxy_surface_row_id",
        "symbol_action_packet_row_id",
        "performance_row_id",
        "runtime_candidate_row_id",
        "registration_spec_row_id",
        "runtime_guard_row_id",
        "guard_check_row_id",
        "runtime_candidate_registry_event_probe_row_id",
        "registry_module_row_id",
        "scope_registry_row_id",
        "action_scope_row_id",
        "score_scope_summary_row_id",
        "repair_context_bridge_row_id",
        "symbol_summary_row_id",
        "symbol_action_row_id",
        "cost_symbol_row_id",
        "comparator_registration_row_id",
    ):
        if value := _normalized(row.get(field)):
            return value
    for field, value in row.items():
        field_name = str(field)
        if (field_name.endswith("_row_id") or field_name.endswith("_id")) and (
            normalized := _normalized(value)
        ):
            return normalized
    return _normalized(row.get("row_key"))


def _repaired_proxy_symbol_surface_component(row: dict[str, Any]) -> str:
    if component := _normalized(row.get("source_component")):
        return component
    loaded_from = _repaired_proxy_symbol_surface_loaded_path(row)
    if "symbol_action_packet" in loaded_from:
        return "repaired_proxy_symbol_surface"
    if "registration_specs" in loaded_from or "runtime_candidate_registry" in loaded_from:
        return "registry_scorer_module"
    if "score_bridge" in loaded_from:
        return "repaired_proxy_score_bridge"
    if "execution_registry_symbol_action" in loaded_from:
        return "repaired_proxy_symbol_action"
    if "execution_specs_cost_symbol" in loaded_from:
        return "repaired_proxy_cost_symbol"
    return "repaired_proxy_symbol_surface"


def _repaired_proxy_symbol_surface_side(row: dict[str, Any]) -> str:
    raw = _normalized(row.get("side") or row.get("selected_side") or row.get("direction")).upper()
    if "LONG" in raw:
        return "LONG"
    if "SHORT" in raw:
        return "SHORT"
    return raw


def _repaired_proxy_symbol_surface_score(row: dict[str, Any]) -> float | None:
    return _first_numeric(
        row.get("cost_adjusted_simulated_r"),
        row.get("net_proxy_r_weighted_mean"),
        row.get("net_proxy_r_mean"),
        row.get("repair_proxy_mean_for_event"),
        row.get("repaired_proxy_event_score"),
        row.get("score_value"),
        row.get("net_proxy_r"),
        row.get("stress_proxy_r"),
        row.get("replay_rerun_score"),
        row.get("score_context_index_weighted_mean"),
        row.get("score_context_index_mean"),
        row.get("score_minus_same_scope_default"),
        row.get("source_return_minus_control"),
    )


def _repaired_proxy_symbol_surface_decision(row: dict[str, Any]) -> DecisionLabel:
    class_text = " ".join(
        _normalized(row.get(field)).upper()
        for field in (
            "follow_inverse_default_off_avoid_class",
            "default_off_avoid_class",
            "repaired_proxy_event_action",
            "symbol_action_packet_next_action",
            "symbol_action_packet_status",
            "runtime_candidate_kind",
            "runtime_candidate_status",
            "registration_action",
            "scorer_registration_action",
            "comparator_registration_action",
            "score_scope_summary_status",
            "repair_context_bridge_status",
            "runtime_guard_action",
            "guard_check_status",
        )
    )
    if _truthy(row.get("emits_avoid_or_redesign")) or "AVOID" in class_text:
        return "AVOID"
    if _truthy(row.get("emits_source_repair_required")) or "REPAIR_REQUIRED" in class_text:
        return "MIXED"
    if (
        _truthy(row.get("emits_default_off_score"))
        or _truthy(row.get("runtime_score_allowed"))
        or "DEFAULT_OFF" in class_text
        or "FOLLOW" in class_text
    ):
        return "FOLLOW"
    if "FAIL_CLOSED" in class_text or "SOURCE_REPAIR" in class_text:
        return "MIXED"
    score = _repaired_proxy_symbol_surface_score(row)
    if score is not None:
        if score < 0:
            return "AVOID"
        if score > 0:
            return "FOLLOW"
    return "MIXED"


def _repaired_proxy_symbol_surface_action_class(decision: DecisionLabel) -> str:
    if decision == "FOLLOW":
        return "repaired_proxy_default_off_scorer"
    if decision == "AVOID":
        return "repaired_proxy_avoid_filter"
    return "repaired_proxy_context_guard"


def _repaired_proxy_symbol_surface_implementation_action(
    row: dict[str, Any],
    decision: DecisionLabel,
) -> str:
    if decision == "FOLLOW":
        return "REPAIRED_PROXY_DEFAULT_OFF_SCORER_WITH_GUARDS"
    if decision == "AVOID":
        return "KEEP_SOURCE_REPAIRED_NEGATIVE_PROXY_AS_AVOID_OR_REDESIGN_INPUT"
    if _truthy(row.get("emits_source_repair_required")):
        return "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R"
    return "MERGE_AS_CONTEXT_STRESS_GUARD_INPUT"


def _repaired_proxy_symbol_surface_r_class(
    row: dict[str, Any],
    decision: DecisionLabel,
) -> str:
    if decision == "FOLLOW":
        return "REPAIRED_POSITIVE_PROXY"
    if decision == "AVOID":
        return "REPAIRED_NEGATIVE_PROXY"
    if _truthy(row.get("emits_source_repair_required")):
        return "SOURCE_REPAIR_FOR_EXACT_R"
    return "SOURCE_REPAIRED_CONTEXT_PROXY"


def _repaired_proxy_metric_from_fields(row: dict[str, Any], *fields: str) -> dict[str, Any] | None:
    for field in fields:
        metric = _metric_from_scalar(row.get(field), source_field=field)
        if metric:
            return metric
    return None


def _repaired_proxy_effective_n_metric(row: dict[str, Any]) -> dict[str, Any] | None:
    for field in (
        "bridge_rows",
        "registration_candidate_rows",
        "nonregistration_rows",
        "source_repair_rows_for_event",
        "runtime_candidate_rows",
        "comparator_execution_rows",
        "represented_surface_rows",
        "scope_rows",
        "row_count",
    ):
        metric = _metric_from_scalar(row.get(field), source_field=field)
        if metric:
            return metric
    count_sum = sum(
        _to_float(row.get(field)) or 0.0
        for field in (
            "win_count",
            "loss_count",
            "no_fill_count",
            "flat_count",
            "target_first_count",
            "stop_first_count",
        )
    )
    if count_sum > 0:
        return _metric_from_scalar(count_sum, source_field="repaired_proxy_outcome_counts")
    return _metric_from_scalar(1, source_field="repaired_proxy_symbol_surface_row")


def _enrich_repaired_proxy_symbol_surface_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert repaired-proxy symbol/session rows into scoped runtime evidence."""
    if not _is_repaired_proxy_symbol_surface_row(row):
        return row

    enriched = dict(row)
    row_id = _repaired_proxy_symbol_surface_row_id(enriched)
    decision = _repaired_proxy_symbol_surface_decision(enriched)
    source_component = _repaired_proxy_symbol_surface_component(enriched)
    symbol = _normalized(enriched.get("symbol"))
    source_symbol = _normalized(enriched.get("source_symbol")) or symbol
    symbol_family = (
        _normalized(enriched.get("symbol_family"))
        or _symbol_family_for(symbol)
        or _symbol_family_for(source_symbol)
    )
    route_session = _normalized(enriched.get("route_session"))
    horizon_id = _normalized(enriched.get("horizon_id"))
    market_timeframe = _normalized(enriched.get("market_timeframe"))
    side = _repaired_proxy_symbol_surface_side(enriched)
    route_family = _route_family_for_source_component(source_component)
    action_class = _repaired_proxy_symbol_surface_action_class(decision)
    implementation_action = _repaired_proxy_symbol_surface_implementation_action(
        enriched,
        decision,
    )
    r_evidence_class = _repaired_proxy_symbol_surface_r_class(enriched, decision)

    scope = {
        key: value
        for key, value in {
            "symbol": symbol,
            "source_symbol": source_symbol,
            "symbol_family": symbol_family,
            "market": symbol or source_symbol,
            "market_timeframe": market_timeframe,
            "route_session": route_session,
            "horizon_id": horizon_id,
            "side": side,
            "source_component": source_component,
            "route_family": route_family,
            "action_class": action_class,
        }.items()
        if value not in (None, "")
    }
    if not symbol and not source_symbol and not symbol_family:
        scope = {}

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    enriched["row_key"] = row_id or _normalized(enriched.get("row_key"))
    enriched["source_row_id"] = enriched["row_key"]
    enriched["source_name"] = "moonshot_repaired_proxy_symbol_surface"
    enriched["evidence_family"] = "moonshot_repaired_proxy_symbol_surface"
    enriched["source_group"] = (
        "repaired_proxy_avoid_filter"
        if decision == "AVOID"
        else "repaired_proxy_default_off_scorer"
        if decision == "FOLLOW"
        else "repaired_proxy_repair_or_context_guard"
    )
    enriched["source_role"] = (
        "repaired_negative_proxy_filter"
        if decision == "AVOID"
        else "repaired_default_off_proxy_scorer"
        if decision == "FOLLOW"
        else "repaired_proxy_context_or_repair_guard"
    )
    enriched["system_surface"] = "repaired_proxy_symbol_surface_runtime"
    enriched["runtime_effect_now"] = (
        "repaired_proxy_symbol_default_off_follow_scorer"
        if decision == "FOLLOW"
        else "repaired_proxy_symbol_avoid_filter"
        if decision == "AVOID"
        else "repaired_proxy_symbol_context_or_repair_guard"
    )
    enriched["source_component"] = source_component
    enriched["route_family"] = route_family
    enriched["action_class"] = action_class
    enriched["implementation_action"] = implementation_action
    enriched["r_evidence_class"] = r_evidence_class
    enriched["runtime_candidate_use_permitted"] = False
    enriched["candidate_use_allowed_now"] = False
    source_bound = bool(scope and source_component and (symbol or source_symbol or symbol_family))
    enriched["source_bound"] = source_bound
    enriched["source_complete"] = bool(source_bound and decision in {"FOLLOW", "AVOID"})
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    score = _repaired_proxy_symbol_surface_score(enriched)
    if score is not None:
        if score < 0:
            enriched.setdefault("proxy_r_class", "NEGATIVE_PROXY_R")
            enriched["event_scope"] = {
                **enriched.get("event_scope", {}),
                "proxy_r_class": "NEGATIVE_PROXY_R",
            }
        elif score > 0:
            enriched.setdefault("proxy_r_class", "POSITIVE_PROXY_R")
            enriched["event_scope"] = {
                **enriched.get("event_scope", {}),
                "proxy_r_class": "POSITIVE_PROXY_R",
            }

    metrics = dict(enriched.get("r_metrics") or {})
    cost_metric = _repaired_proxy_metric_from_fields(
        enriched,
        "cost_adjusted_simulated_r",
    )
    stress_metric = _repaired_proxy_metric_from_fields(
        enriched,
        "stress_simulated_r",
        "stress_proxy_r",
    )
    proxy_metric = _repaired_proxy_metric_from_fields(
        enriched,
        "net_proxy_r_weighted_mean",
        "net_proxy_r_mean",
        "repair_proxy_mean_for_event",
        "repaired_proxy_event_score",
        "score_value",
        "net_proxy_r",
        "comparator_score",
        "replay_rerun_score",
        "score_context_index_weighted_mean",
        "score_context_index_mean",
        "score_minus_same_scope_default",
        "source_return_minus_control",
    )
    effective_n_metric = _repaired_proxy_effective_n_metric(enriched)
    if cost_metric:
        metrics["cost_adjusted_simulated_r"] = cost_metric
    if stress_metric:
        metrics["stress_simulated_r"] = stress_metric
    if proxy_metric:
        metrics["proxy_score"] = proxy_metric
    if effective_n_metric:
        metrics["effective_n"] = effective_n_metric
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


UNIFIED_CANDIDATE_MARKET_ROLLUP_PATH_TOKENS = (
    "BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_",
    "BRANCH_LOCAL_UNIFIED_SYSTEM_EXECUTABLE_ARTIFACTS_",
    "BRANCH_LOCAL_UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_",
    "BRANCH_LOCAL_UNIFIED_SYSTEM_RUNTIME_SURFACES_",
)
UNIFIED_CANDIDATE_MARKET_ROLLUP_ROW_ID_FIELDS = (
    "component_dispatch_plan_row_id",
    "candidate_execution_row_id",
    "market_component_row_id",
    "guard_component_row_id",
    "nofill_component_row_id",
    "scorer_component_row_id",
    "source_component_row_id",
    "recheck_component_row_id",
    "candidate_dispatch_rollup_row_id",
    "candidate_implementation_rollup_row_id",
    "candidate_materialization_rollup_row_id",
    "candidate_runtime_rollup_row_id",
    "candidate_system_rollup_row_id",
    "executable_artifact_rollup_row_id",
    "implementation_execution_rollup_row_id",
    "runtime_surface_rollup_row_id",
)
UNIFIED_CANDIDATE_MARKET_COMPONENT_SOURCE = "unified_candidate_market_rollup"


def _is_unified_candidate_market_rollup_row(row: dict[str, Any]) -> bool:
    path = _normalized(row.get("_gtos_vnext_loaded_from")).upper().replace("\\", "/")
    if not path or not any(token in path for token in UNIFIED_CANDIDATE_MARKET_ROLLUP_PATH_TOKENS):
        return False
    if any(row.get(field) for field in UNIFIED_CANDIDATE_MARKET_ROLLUP_ROW_ID_FIELDS):
        return True
    return bool(
        row.get("source_component")
        and (
            row.get("candidate_component_role")
            or row.get("candidate_component_status")
            or row.get("component_dispatch_action")
        )
    )


def _unified_candidate_market_rollup_row_id(row: dict[str, Any]) -> str:
    for field in UNIFIED_CANDIDATE_MARKET_ROLLUP_ROW_ID_FIELDS:
        if value := _normalized(row.get(field)):
            return value
    if value := _normalized(row.get("source_row_id")):
        return value
    return _normalized(row.get("row_key"))


def _unified_candidate_market_rollup_bundle(row: dict[str, Any]) -> str:
    path = _normalized(row.get("_gtos_vnext_loaded_from")).upper()
    if "CANDIDATE_DISPATCH_BUNDLE" in path:
        return "candidate_dispatch"
    if "CANDIDATE_IMPLEMENTATION_BUNDLE" in path:
        return "candidate_implementation"
    if "CANDIDATE_MATERIALIZATION_BUNDLE" in path:
        return "candidate_materialization"
    if "CANDIDATE_RUNTIME_BUNDLE" in path:
        return "candidate_runtime"
    if "CANDIDATE_SYNTHESIS_BUNDLE" in path:
        return "candidate_synthesis"
    if "EXECUTABLE_ARTIFACTS_BUNDLE" in path:
        return "executable_artifacts"
    if "IMPLEMENTATION_EXECUTION_BUNDLE" in path:
        return "implementation_execution"
    if "RUNTIME_SURFACES_BUNDLE" in path:
        return "runtime_surfaces"
    return "unified_candidate_market_rollup"


def _unified_candidate_source_component(row: dict[str, Any]) -> str:
    if component := _normalized(row.get("source_component")):
        return component
    if row.get("market_component_row_id") or "market" in _normalized(row.get("rollup_type")).casefold():
        return UNIFIED_CANDIDATE_MARKET_COMPONENT_SOURCE
    if row.get("candidate_execution_row_id"):
        role = _normalized(row.get("candidate_system_role")).casefold()
        if "nofill" in role:
            return "nofill_unified_candidate_execution"
        if "market" in role:
            return UNIFIED_CANDIDATE_MARKET_COMPONENT_SOURCE
        if "guard" in role:
            return "unified_candidate_guard"
        if "source" in role or "control" in role:
            return "unified_candidate_source_repair"
        return "unified_candidate_default_off_scorer"
    return UNIFIED_CANDIDATE_MARKET_COMPONENT_SOURCE


def _unified_candidate_proxy_class(row: dict[str, Any]) -> str:
    klass = _normalized(row.get("computed_proxy_delta_class")).upper()
    if "STRONG_POSITIVE" in klass:
        return "STRONG_POSITIVE_PROXY_R"
    if "POSITIVE" in klass:
        return "POSITIVE_PROXY_R"
    if "STRONG_NEGATIVE" in klass:
        return "STRONG_NEGATIVE_PROXY_R"
    if "WEAK_NEGATIVE" in klass or "NEGATIVE" in klass:
        return "NEGATIVE_PROXY_R"
    if "NEUTRAL" in klass:
        return "FLAT_PROXY_R"
    return ""


def _unified_candidate_text(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in (
        "candidate_component_role",
        "candidate_component_status",
        "candidate_system_role",
        "candidate_execution_status",
        "candidate_execution_policy",
        "component_dispatch_action",
        "component_dispatch_plan_status",
        "component_type",
        "runtime_surface_family",
        "runtime_surface_status",
        "self_test_emission",
        "rollup_type",
        "rollup_key",
        "computed_proxy_delta_class",
        "fillability_no_fill_status",
        "tradability_status",
    ):
        if value := row.get(field):
            parts.append(str(value))
    for field in ("status_counts", "decision_counts"):
        value = row.get(field)
        if isinstance(value, dict):
            parts.extend(str(key) for key in value)
    return " ".join(parts).upper()


def _unified_candidate_decision(row: dict[str, Any]) -> DecisionLabel:
    text = _unified_candidate_text(row)
    role = _normalized(row.get("candidate_component_role")).casefold()
    component = _unified_candidate_source_component(row)
    proxy_class = _unified_candidate_proxy_class(row)
    if (
        "SOURCE_OR_CONTROL" in text
        or "SOURCE_REPAIR" in text
        or "REPAIR_OR_CONTROL_REQUIRED" in text
        or "SOURCE_REQUIREMENT" in component.upper()
        or "RECHECK" in text
        or "FAIL_CLOSED_GUARD" in text
        or role in {
            "fail_closed_guard_binding",
            "stress_test_cost_source_target_stop_controls",
            "source_repair_or_target_stop_replay_input",
            "source_or_control_replay_builder",
            "source_horizon_targetability_recheck",
            "source_acquisition_or_proxy_control",
            "proxy_control_feature",
            "replay_only_or_comparator_scope",
            "system_context_input",
        }
    ):
        return "MIXED"
    if (
        "AVOID_INVERSE" in text
        or "FAILURE_FILTER" in text
        or role == "avoid_inverse_filter_or_failure_feature"
        or proxy_class == "STRONG_NEGATIVE_PROXY_R"
    ):
        return "AVOID"
    if (
        "POSITIVE_CHALLENGER" in text
        or "DEFAULT_OFF_POSITIVE" in text
        or "SCORER_RUNTIME_REGISTERED_DEFAULT_OFF" in text
        or role == "default_off_scorer_registry"
        or proxy_class in {"STRONG_POSITIVE_PROXY_R", "POSITIVE_PROXY_R"}
    ):
        return "FOLLOW"
    if "MARKET_" in text or "RUNTIME_SURFACE" in text:
        return "MIXED"
    if proxy_class == "NEGATIVE_PROXY_R":
        return "AVOID"
    return "MIXED"


def _unified_candidate_action_class(row: dict[str, Any], decision: DecisionLabel) -> str:
    text = _unified_candidate_text(row)
    role = _normalized(row.get("candidate_component_role")).casefold()
    if decision == "FOLLOW":
        return "unified_candidate_default_off_scorer"
    if decision == "AVOID":
        return "unified_candidate_avoid_filter"
    if "GUARD" in text or role == "fail_closed_guard_binding":
        return "unified_candidate_context_guard"
    if "SOURCE" in text or "CONTROL" in text or "REPAIR" in text or "RECHECK" in text:
        return "unified_candidate_source_repair_guard"
    if "NOFILL" in text:
        return "unified_candidate_nofill_stress_guard"
    return "unified_candidate_market_router"


def _unified_candidate_implementation_action(row: dict[str, Any], decision: DecisionLabel) -> str:
    text = _unified_candidate_text(row)
    if decision == "FOLLOW":
        return "UNIFIED_CANDIDATE_DEFAULT_OFF_SCORER_WITH_SOURCE_GUARDS"
    if decision == "AVOID":
        return "UNIFIED_CANDIDATE_AVOID_OR_FAILURE_FILTER"
    if "SOURCE" in text or "CONTROL" in text or "REPAIR" in text or "RECHECK" in text:
        return "SOURCE_JOIN_REPAIR_REQUIRED"
    return "MERGE_CONTEXT_STRESS_SCOPE_AS_GUARD_INPUT"


def _unified_candidate_r_evidence_class(row: dict[str, Any], decision: DecisionLabel) -> str:
    text = _unified_candidate_text(row)
    if decision == "FOLLOW":
        return "UNIFIED_CANDIDATE_POSITIVE_PROXY"
    if decision == "AVOID":
        return "UNIFIED_CANDIDATE_NEGATIVE_PROXY"
    if "SOURCE" in text or "CONTROL" in text or "REPAIR" in text or "RECHECK" in text:
        return "UNIFIED_CANDIDATE_SOURCE_REPAIR_OR_CONTROL"
    if "GUARD" in text:
        return "UNIFIED_CANDIDATE_GUARD_BINDING"
    return "UNIFIED_CANDIDATE_MARKET_ROUTER_CONTEXT"


def _unified_candidate_session(row: dict[str, Any]) -> str:
    if session := _normalized(row.get("route_session")):
        return session
    coverage = row.get("session_kz_offkz_coverage")
    if isinstance(coverage, list) and any(_canonical_session(item) == SESSION_WILDCARD for item in coverage):
        return SESSION_WILDCARD
    return ""


def _unified_candidate_effective_n_metric(row: dict[str, Any]) -> dict[str, Any] | None:
    for field in (
        "row_count",
        "computed_action_rows",
        "computed_delta_rows",
        "source_rows_needed_to_n20_proxy",
    ):
        metric = _metric_from_scalar(row.get(field), source_field=field)
        if metric:
            return metric
    for field in ("status_counts", "decision_counts"):
        payload = row.get(field)
        if isinstance(payload, dict):
            total = sum(_to_float(value) or 0.0 for value in payload.values())
            if total > 0:
                return _metric_from_scalar(total, source_field=field)
    return _metric_from_scalar(1, source_field="unified_candidate_market_rollup_row")


def _enrich_unified_candidate_market_rollup_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert branch-local unified candidate bundles into scoped runtime evidence."""
    if not _is_unified_candidate_market_rollup_row(row):
        return row

    enriched = dict(row)
    row_id = _unified_candidate_market_rollup_row_id(enriched)
    decision = _unified_candidate_decision(enriched)
    source_component = _unified_candidate_source_component(enriched)
    symbol = _normalized(enriched.get("symbol"))
    source_symbol = _normalized(enriched.get("source_symbol")) or symbol
    symbol_family = (
        _normalized(enriched.get("symbol_family"))
        or _symbol_family_for(symbol)
        or _symbol_family_for(source_symbol)
    )
    route_session = _unified_candidate_session(enriched)
    horizon_id = _normalized(enriched.get("horizon_id"))
    primitive = _normalized(enriched.get("primitive") or enriched.get("primitive_flag"))
    route_family = _route_family_for_source_component(source_component)
    action_class = _unified_candidate_action_class(enriched, decision)
    proxy_r_class = _unified_candidate_proxy_class(enriched)

    scope = {
        key: value
        for key, value in {
            "symbol": symbol,
            "source_symbol": source_symbol,
            "symbol_family": symbol_family,
            "market": symbol or source_symbol,
            "route_session": route_session,
            "horizon_id": horizon_id,
            "primitive": primitive,
            "source_component": source_component,
            "route_family": route_family,
            "action_class": action_class,
            "proxy_r_class": proxy_r_class,
        }.items()
        if value not in (None, "")
    }
    if not symbol and not source_symbol and not symbol_family:
        scope = {}

    existing_scope = (
        enriched.get("event_scope") if isinstance(enriched.get("event_scope"), dict) else {}
    )
    enriched["event_scope"] = {**existing_scope, **scope}
    for field, value in scope.items():
        enriched.setdefault(field, value)

    enriched["row_key"] = row_id
    enriched["source_row_id"] = _normalized(enriched.get("source_row_id")) or row_id
    enriched["source_name"] = "moonshot_unified_candidate_market_rollup"
    enriched["evidence_family"] = "moonshot_unified_candidate_market_rollup"
    enriched["source_group"] = f"unified_candidate_{_unified_candidate_market_rollup_bundle(enriched)}"
    enriched["source_role"] = (
        "unified_candidate_avoid_filter"
        if decision == "AVOID"
        else "unified_candidate_default_off_scorer"
        if decision == "FOLLOW"
        else action_class
    )
    enriched["system_surface"] = "unified_candidate_market_component_router"
    enriched["runtime_effect_now"] = (
        "unified_candidate_component_follow_scorer"
        if decision == "FOLLOW"
        else "unified_candidate_component_avoid_filter"
        if decision == "AVOID"
        else "unified_candidate_component_market_or_guard_context"
    )
    enriched["source_component"] = source_component
    enriched["route_family"] = route_family
    enriched["action_class"] = action_class
    enriched["implementation_action"] = _unified_candidate_implementation_action(
        enriched,
        decision,
    )
    enriched["r_evidence_class"] = _unified_candidate_r_evidence_class(enriched, decision)
    enriched["unified_candidate_market_rollup_id"] = row_id
    enriched["unified_candidate_market_rollup_bundle"] = _unified_candidate_market_rollup_bundle(
        enriched
    )
    enriched["unified_candidate_market_rollup_role"] = (
        enriched.get("candidate_component_role")
        or enriched.get("candidate_system_role")
        or enriched.get("rollup_type")
    )
    enriched["unified_candidate_market_rollup_status"] = (
        enriched.get("candidate_component_status")
        or enriched.get("candidate_execution_status")
        or enriched.get("component_dispatch_plan_status")
        or _dominant_count_key(enriched.get("status_counts"))
    )
    enriched["unified_candidate_market_rollup_live_effect"] = enriched.get("live_effect")
    enriched["unified_candidate_market_rollup_not_completion"] = enriched.get("not_completion")
    enriched["runtime_candidate_use_permitted"] = False
    enriched["candidate_use_allowed_now"] = bool(enriched.get("candidate_use_allowed_now")) and False
    source_bound = bool(scope and source_component and (symbol or source_symbol or symbol_family))
    enriched["source_bound"] = source_bound
    enriched["source_complete"] = bool(source_bound and decision in {"FOLLOW", "AVOID"})
    enriched.setdefault("source_path", enriched.get("_gtos_vnext_loaded_from"))
    enriched.setdefault("drill_through_path", enriched.get("_gtos_vnext_loaded_from"))

    if proxy_r_class:
        enriched["proxy_r_class"] = proxy_r_class
    if row_count := _to_float(enriched.get("row_count")):
        enriched["row_count"] = int(row_count) if row_count.is_integer() else row_count
    else:
        enriched["row_count"] = 1
    if source_events := _to_float(enriched.get("computed_action_rows")):
        enriched["source_event_rows"] = int(source_events) if source_events.is_integer() else source_events
    if weighted_rows := _to_float(enriched.get("computed_delta_rows")):
        enriched["source_weighted_registry_match_rows"] = (
            int(weighted_rows) if weighted_rows.is_integer() else weighted_rows
        )

    metrics = dict(enriched.get("r_metrics") or {})
    proxy_metric = _metric_from_scalar(
        enriched.get("computed_proxy_delta")
        if enriched.get("computed_proxy_delta") is not None
        else enriched.get("default_off_observation_score"),
        source_field="unified_candidate_computed_proxy_delta",
    )
    if proxy_metric:
        metrics["proxy_score"] = proxy_metric
    effective_n = _unified_candidate_effective_n_metric(enriched)
    if effective_n:
        metrics["effective_n"] = effective_n
    if metrics:
        enriched["r_metrics"] = metrics
    return enriched


def _enrich_runtime_row(row: dict[str, Any]) -> dict[str, Any]:
    """Preserve runtime matching dimensions compiled from full evidence rows."""
    enriched = _enrich_expanded_market_implementation_row(
    _enrich_moonshot_nearmiss_market_entry_join_row(
        _enrich_moonshot_market_gap_primitive_row(
        _enrich_moonshot_source_component_summary_row(
        _enrich_moonshot_recommendation_scope_rollup_row(
            _enrich_moonshot_recommendation_unified_candidate_row(
                _enrich_moonshot_recommendation_family_rollup_row(
                    _enrich_moonshot_recommendation_bucket_row(
                        _enrich_moonshot_source_geometry_repair_row(
                            _enrich_moonshot_exact_r_missing_proof_row(
                                _enrich_moonshot_unified_numeric_result_row(
                                    _enrich_moonshot_broker_repaired_proxy_row(
                                        _enrich_moonshot_entry_adverse_stop_first_row(
                                            _enrich_moonshot_target_stop_ordering_row(
                                                _enrich_moonshot_source_repair_row(
                                                    _enrich_cp281_branch_decision_row(
                                                        _enrich_cp281_ready_runtime_rule_row(
                                                            _enrich_cp281_ready_runtime_aggregate_row(
                                                                _enrich_moonshot_challenger_frontier_route_row(
                                                                    _enrich_moonshot_challenger_frontier_action_row(
                                                                        _enrich_moonshot_control_screen_route_queue_row(
                                                                            _enrich_moonshot_gtos_replay_blocker_row(
                                                                                _enrich_moonshot_control_screen_row(
                                                                                    _enrich_cp281_result_table_row(dict(row))
                                                                                )
                                                                            )
                                                                        )
                                                                    )
                                                                )
                                                            )
                                                        )
                                                    )
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )
    )
    )
    )
    enriched = _enrich_unified_candidate_market_rollup_row(enriched)
    enriched = _enrich_repaired_proxy_symbol_surface_row(enriched)
    enriched = _enrich_moonshot_accepted_builder_row(enriched)
    enriched = _enrich_moonshot_accepted_builder_binding_row(enriched)
    enriched = _enrich_moonshot_accepted_builder_branch_row(enriched)
    enriched = _enrich_moonshot_accepted_builder_entry_adverse_row(enriched)
    enriched = _enrich_moonshot_accepted_builder_family_row(enriched)
    enriched = _enrich_moonshot_accepted_builder_m15_row(enriched)
    enriched = _enrich_moonshot_accepted_builder_m1_row(enriched)
    enriched = _enrich_moonshot_accepted_builder_positive_row(enriched)
    enriched = _enrich_moonshot_accepted_builder_source_row(enriched)
    enriched = _enrich_moonshot_accepted_builder_rejected_repair_row(enriched)
    effective_n = _to_float(enriched.get("implementation_ready_candidate_rows"))
    effective_n_source = "implementation_ready_candidate_rows"
    if effective_n is None and isinstance(enriched.get("implementation_ready_candidate_row_ids"), list):
        effective_n = float(len(enriched.get("implementation_ready_candidate_row_ids") or []))
        effective_n_source = "implementation_ready_candidate_row_ids"
    if effective_n is not None and effective_n > 0:
        metrics = dict(enriched.get("r_metrics") or {})
        metrics.setdefault(
            "effective_n",
            {
                "sum": effective_n,
                "count": 1,
                "mean": effective_n,
                "positive_rows": 1,
                "negative_rows": 0,
                "zero_rows": 0,
                "source_field": effective_n_source,
                "source_shape": "row_count",
            },
        )
        enriched["r_metrics"] = metrics
    if enriched.get("selected_side") and not enriched.get("side"):
        enriched["side"] = enriched.get("selected_side")
    if enriched.get("ai_narrowing_policy_status") and not enriched.get("implementation_action"):
        enriched["implementation_action"] = enriched.get("ai_narrowing_policy_status")
    if enriched.get("ai_narrowing_capacity_blocklist_status"):
        enriched.setdefault("source_name", "ai_narrowing_capacity_blocklist")
        enriched.setdefault("evidence_family", "ai_decision_architecture")
        enriched.setdefault("implementation_action", enriched.get("ai_narrowing_capacity_blocklist_status"))
        enriched.setdefault("route_family", "mechanical_ai_selector")
        enriched.setdefault(
            "source_row_id",
            enriched.get("ai_narrowing_capacity_blocklist_row_id"),
        )
    route_family, inferred_from = _infer_route_family_from_row(enriched)
    if route_family and inferred_from != "explicit":
        scope = enriched.get("event_scope")
        if isinstance(scope, dict):
            enriched["event_scope"] = {**scope, "route_family": route_family}
        else:
            enriched["route_family"] = route_family
        enriched["route_family_inferred_from"] = inferred_from
    return enriched


def _scope_matches(scope: dict[str, str], event: dict[str, str]) -> bool:
    if not scope:
        return False
    for field, expected in scope.items():
        actual = event.get(field)
        if field in ADVISORY_SCOPE_FIELDS and actual in (None, ""):
            continue
        if not _field_values_match(field, expected, actual):
            return False
    return True


def _preserve_less_specific_row(row: dict[str, Any], cfg: dict[str, Any]) -> bool:
    source_names = {
        _normalized(item)
        for item in _configured_list(cfg, "preserve_source_names_when_less_specific", ["ai_narrowing_policy"])
    }
    evidence_families = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "preserve_evidence_families_when_less_specific",
            ["ai_decision_architecture"],
        )
    }
    return (
        _normalized(row.get("source_name")) in source_names
        or _normalized(row.get("evidence_family")) in evidence_families
    )


def _scope_selection_policy(cfg: dict[str, Any] | None) -> str:
    raw = _normalized((cfg or {}).get("scope_selection_policy") or "max_specificity").replace("-", "_")
    if raw in {"all_matching_anchored", "anchored_all_matching", "full_matching_anchored"}:
        return "all_matching_anchored"
    if raw in {"all", "all_matching", "all_matching_scopes", "full_matching_denominator"}:
        return "all_matching"
    return "max_specificity"


def _scope_required_anchor_groups(cfg: dict[str, Any] | None) -> tuple[tuple[str, ...], ...]:
    raw = (cfg or {}).get("scope_required_anchor_groups")
    if raw is None:
        return ()
    groups: list[tuple[str, ...]] = []
    if isinstance(raw, IterableABC) and not isinstance(raw, str):
        for item in raw:
            if isinstance(item, str):
                group = tuple(part.strip() for part in item.split("|") if part.strip())
            elif isinstance(item, IterableABC):
                group = tuple(str(part).strip() for part in item if str(part).strip())
            else:
                group = ()
            if group:
                groups.append(group)
    return tuple(groups)


def _row_allows_missing_side_anchor(row: dict[str, Any], cfg: dict[str, Any]) -> bool:
    evidence_families = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "scope_side_anchor_optional_evidence_families",
            (),
        )
    }
    source_components = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "scope_side_anchor_optional_source_components",
            (),
        )
    }
    if not evidence_families or not source_components:
        return False
    return (
        _normalized(row.get("evidence_family")) in evidence_families
        and _row_dimension_value(row, "source_component") in source_components
        and bool(_row_dimension_value(row, "symbol") or _row_dimension_value(row, "symbol_family"))
        and bool(_row_dimension_value(row, "route_session"))
    )


def _row_has_required_scope_anchors(row: dict[str, Any], cfg: dict[str, Any]) -> bool:
    groups = _scope_required_anchor_groups(cfg)
    if not groups:
        return True
    for group in groups:
        if any(_row_dimension_value(row, field) for field in group):
            continue
        if tuple(group) == ("side",) and _row_allows_missing_side_anchor(row, cfg):
            continue
        return False
    return True


def _select_runtime_rows(
    matches: list[dict[str, Any]],
    *,
    cfg: dict[str, Any],
    min_scope_fields: int,
    normalized_event: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    if not matches:
        return []
    eligible = [
        row for row in matches
        if len(_row_scope(row)) >= min_scope_fields
    ]
    policy = _scope_selection_policy(cfg)
    if policy == "all_matching_anchored":
        anchored = [
            row for row in eligible
            if _row_has_required_scope_anchors(row, cfg)
        ]
        return _prefer_event_specific_rows(anchored, normalized_event, cfg)
    if policy == "all_matching":
        return _prefer_event_specific_rows(eligible, normalized_event, cfg)
    max_scope_fields = max(len(_row_scope(row)) for row in matches)
    selected = [
        row for row in eligible
        if (
            len(_row_scope(row)) == max_scope_fields
            or _preserve_less_specific_row(row, cfg)
        )
    ]
    return _prefer_event_specific_rows(selected, normalized_event, cfg)


def _prefer_event_specific_rows(
    rows: list[dict[str, Any]],
    normalized_event: dict[str, str] | None,
    cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    """Let exact current-event dimensions dominate broad rows when available."""
    if not rows or not normalized_event:
        return rows
    if not bool(cfg.get("scope_prefer_event_specific_fields_enabled", False)):
        return rows
    fields = _configured_list(
        cfg,
        "scope_prefer_event_specific_fields",
        ["route_session", "framework", "route_family", "market_timeframe", "horizon_id", "source_component"],
    )
    narrowed = rows
    for field in fields:
        actual = normalized_event.get(field)
        if actual in (None, ""):
            continue
        exact_rows = [
            row for row in narrowed
            if (expected := _row_dimension_value(row, field))
            and not (field == "route_session" and _canonical_session(expected) == SESSION_WILDCARD)
            and _field_values_match(field, expected, actual)
        ]
        if exact_rows:
            narrowed = exact_rows
    return narrowed


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    read_path = _resolve_local_git_lfs_pointer(path) or _local_path_for_io(path)
    with read_path.open("r", encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                rows.append(parsed)
    return rows


def _repo_git_dir_for(path: Path) -> Path | None:
    for parent in (path.resolve().parent, *path.resolve().parents):
        git_path = parent / ".git"
        if git_path.is_dir():
            return git_path
        if git_path.is_file():
            try:
                content = git_path.read_text(encoding="utf-8").strip()
            except OSError:
                return None
            prefix = "gitdir:"
            if content.casefold().startswith(prefix):
                raw = content[len(prefix):].strip()
                target = Path(raw)
                if not target.is_absolute():
                    target = parent / target
                return target
    return None


def _resolve_local_git_lfs_pointer(path: Path) -> Path | None:
    """Return the local LFS object backing a JSONL pointer, when available."""
    try:
        with _local_path_for_io(path).open("r", encoding="utf-8-sig") as fh:
            first = fh.readline().strip()
            if first != "version https://git-lfs.github.com/spec/v1":
                return None
            oid_line = fh.readline().strip()
    except OSError:
        return None

    prefix = "oid sha256:"
    if not oid_line.startswith(prefix):
        return None
    oid = oid_line[len(prefix):].strip()
    if len(oid) != 64 or any(ch not in "009abcdefABCDEF" for ch in oid):
        return None

    git_dir = _repo_git_dir_for(path)
    if git_dir is None:
        return None
    obj = git_dir / "lfs" / "objects" / oid[:2] / oid[2:4] / oid
    return obj if _local_path_exists(obj) else None


def _cp281_aggregate_provenance(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "cp281_aggregate_row_id": row.get("cp281_aggregate_row_id"),
            "row_key": row.get("row_key"),
            "source_row_count": row.get("source_row_count"),
            "rule_count": row.get("rule_count"),
            "source_ownership": row.get("source_ownership"),
            "loaded_from": row.get("_gtos_vnext_loaded_from"),
            "average_cost_adjusted_simulated_r": row.get("average_cost_adjusted_simulated_r"),
            "average_stress_simulated_r": row.get("average_stress_simulated_r"),
            "effective_n_sum": row.get("effective_n_sum"),
        }.items()
        if value not in (None, "", {}, [])
    }


def _cp281_rule_replay_event_provenance(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "cp281_rule_replay_event_id": row.get("cp281_rule_replay_event_id"),
            "row_key": row.get("row_key"),
            "source_cp281_rule_row_id": row.get("source_cp281_rule_row_id"),
            "event_materialization_status": row.get("event_materialization_status"),
            "event_payload": row.get("event_payload"),
            "event_required_fields": row.get("event_required_fields"),
            "event_required_field_count": row.get("event_required_field_count"),
            "source_mapping_row_key": row.get("source_mapping_row_key"),
            "source_operation": row.get("source_operation"),
            "source_evidence_role": row.get("source_evidence_role"),
            "source_ownership": row.get("source_ownership"),
            "loaded_from": row.get("_gtos_vnext_loaded_from"),
            "gross_simulated_r": row.get("gross_simulated_r"),
            "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
            "stress_simulated_r": row.get("stress_simulated_r"),
            "effective_n": row.get("effective_n"),
        }.items()
        if value not in (None, "", {}, [])
    }


def _merge_cp281_rule_replay_event_provenance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach CP281 replay event materialization to member rules without votes."""
    events_by_rule: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if _normalized(row.get("row_type")) != "cp281_rule_replay_event":
            continue
        rule_id = _normalized(row.get("source_cp281_rule_row_id"))
        if rule_id:
            events_by_rule[rule_id].append(row)
    if not events_by_rule:
        return rows

    merged: list[dict[str, Any]] = []
    for row in rows:
        row_type = _normalized(row.get("row_type"))
        if row_type == "cp281_rule_replay_event":
            continue
        rule_id = _normalized(row.get("cp281_rule_row_id"))
        if row_type == "cp281_ready_runtime_rule_to_main_system_surface" and rule_id in events_by_rule:
            copied = dict(row)
            event_provenance = [
                _cp281_rule_replay_event_provenance(event)
                for event in sorted(
                    events_by_rule[rule_id],
                    key=lambda item: _normalized(item.get("cp281_rule_replay_event_id")),
                )
            ]
            copied.setdefault("cp281_rule_replay_event_provenance", event_provenance)
            copied.setdefault("cp281_rule_replay_event_count", len(event_provenance))
            if len(event_provenance) == 1:
                single = event_provenance[0]
                copied.setdefault(
                    "cp281_rule_replay_event_id",
                    single.get("cp281_rule_replay_event_id"),
                )
                copied.setdefault("cp281_rule_replay_event_row_key", single.get("row_key"))
                copied.setdefault(
                    "cp281_rule_replay_event_payload",
                    single.get("event_payload"),
                )
                copied.setdefault(
                    "cp281_rule_replay_event_required_fields",
                    single.get("event_required_fields"),
                )
                copied.setdefault(
                    "cp281_rule_replay_event_required_field_count",
                    single.get("event_required_field_count"),
                )
                copied.setdefault(
                    "cp281_rule_replay_event_loaded_from",
                    single.get("loaded_from"),
                )
            merged.append(copied)
            continue
        merged.append(row)
    return merged


def _merge_cp281_aggregate_provenance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach CP281 aggregate provenance to branch rows without double-counting scopes."""
    aggregates = {
        row.get("cp281_aggregate_row_id"): row
        for row in rows
        if _normalized(row.get("row_type")) == "cp281_ready_runtime_aggregate_to_main_system_surface"
        and row.get("cp281_aggregate_row_id")
    }
    if not aggregates:
        return rows

    branch_ids = {
        row.get("cp281_aggregate_row_id")
        for row in rows
        if _normalized(row.get("row_type")) == "cp281_ready_runtime_branch_decision"
        and row.get("cp281_aggregate_row_id")
    }
    if not branch_ids:
        return rows

    merged: list[dict[str, Any]] = []
    for row in rows:
        row_type = _normalized(row.get("row_type"))
        aggregate_id = row.get("cp281_aggregate_row_id")
        if row_type == "cp281_ready_runtime_aggregate_to_main_system_surface" and aggregate_id in branch_ids:
            continue
        if row_type == "cp281_ready_runtime_branch_decision" and aggregate_id in aggregates:
            aggregate = aggregates[aggregate_id]
            copied = dict(row)
            provenance = _cp281_aggregate_provenance(aggregate)
            copied.setdefault("cp281_aggregate_provenance", provenance)
            copied.setdefault("cp281_aggregate_source_row_count", aggregate.get("source_row_count"))
            copied.setdefault("cp281_aggregate_loaded_from", aggregate.get("_gtos_vnext_loaded_from"))
            copied.setdefault("cp281_aggregate_row_key", aggregate.get("row_key"))
            copied.setdefault("cp281_aggregate_source_ownership", aggregate.get("source_ownership"))
            merged.append(copied)
            continue
        merged.append(row)
    return merged


def _row_identity(row: dict[str, Any]) -> str:
    row_id = (
        row.get("review_row_id")
        or row.get("vnext_matrix_row_id")
        or row.get("event_scope_rollup_row_id")
        or row.get("registry_catalog_row_id")
        or row.get("ai_narrowing_policy_row_id")
        or row.get("ai_narrowing_capacity_blocklist_row_id")
        or row.get("ai_narrowing_default_off_runtime_row_id")
        or row.get("ai_decision_trace_routing_guard_runtime_row_id")
        or row.get("pre_ai_post_l2_routing_policy_runtime_row_id")
        or row.get("rejected_candidate_l2_value_mining_runtime_row_id")
        or row.get("accepted_candidate_m1_fill_source_repair_runtime_row_id")
        or row.get("trade_record_execution_lifecycle_runtime_row_id")
        or row.get("numeric_router_catalog_runtime_row_id")
        or row.get("survivor_failure_runtime_row_id")
        or row.get("cp280_scorer_filter_router_runtime_row_id")
        or row.get("branch_implementation_replay_runtime_row_id")
        or row.get("branch_ambiguity_collapse_runtime_row_id")
        or row.get("branch_followup_computation_runtime_row_id")
        or row.get("adverse_stop_first_execution_runtime_row_id")
        or row.get("gate_selector_session_timeframe_runtime_row_id")
        or row.get("risk_proxy_stress_cost_runtime_row_id")
        or row.get("sierra_depth_source_acquisition_runtime_row_id")
        or row.get("source_repair_missing_denominator_runtime_row_id")
        or row.get("nr_source_repair_execution_identity_runtime_row_id")
        or row.get("legacy_ai_cascade_model_runtime_row_id")
        or row.get("legacy_v2_v3_paper_live_friction_runtime_row_id")
        or row.get("sl_beyond_ob_outcome_join_source_repair_runtime_row_id")
        or row.get("fvg_trade_record_bounds_execution_runtime_row_id")
        or row.get("scid_target_horizon_control_runtime_row_id")
        or row.get("main_orch24_structural_repair_action_runtime_row_id")
        or row.get("main_orch24_action_completeness_residual_r_runtime_row_id")
        or row.get("main_orch24_implementation_selection_runtime_row_id")
        or row.get("main_orch24_snapshot_dependency_repair_runtime_row_id")
        or row.get("main_orch48_final_review_selector_runtime_row_id")
        or row.get("ltf_path_geometry_source_runtime_row_id")
        or row.get("instrument_expansion_market_session_runtime_row_id")
        or row.get("scid_combined_source_capture_poi_bounds_runtime_row_id")
        or row.get("recommendation_unified_candidate_id")
        or row.get("recommendation_scope_rollup_id")
        or row.get("numeric_result_row_id")
        or row.get("row_key")
        or row.get("source_row_id")
        or ""
    )
    loaded_from = row.get("_gtos_vnext_loaded_from") or row.get("source_artifact") or row.get("source_path") or ""
    line_no = row.get("source_line_no") or row.get("declared_origin_line_no") or ""
    return f"{loaded_from}|{row_id}|{line_no}"


def _scope_key_variants(scope: dict[str, str]) -> list[tuple[tuple[str, str], ...]]:
    if not scope:
        return []

    options: list[list[tuple[str, str]]] = []
    for field, value in scope.items():
        if field == "route_session" and _canonical_session(value) == SESSION_WILDCARD:
            variants = [(field, SESSION_WILDCARD), *[(field, session) for session in SESSION_CANONICAL_VALUES]]
            options.append([None, *variants] if field in ADVISORY_SCOPE_FIELDS else variants)
            continue
        canonical = _canonical_field_value(field, value)
        if canonical:
            options.append([None, (field, canonical)] if field in ADVISORY_SCOPE_FIELDS else [(field, canonical)])

    variants = []
    for parts in product(*options):
        key = tuple(sorted(part for part in parts if part is not None))
        if key:
            variants.append(key)
    return variants


def _event_criteria_key(normalized_event: dict[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted(
            (field, _canonical_field_value(field, value))
            for field, value in normalized_event.items()
            if field in MATCH_FIELDS
            if _canonical_field_value(field, value)
        )
    )


@dataclass(frozen=True)
class GTOSVNextEvidenceIndex:
    """Compact in-memory index compiled from full vNext evidence ledgers."""

    rows: tuple[dict[str, Any], ...]
    scopes: tuple[dict[str, str], ...]
    artifact_paths: tuple[str, ...]
    rows_loaded_by_path: dict[str, int] = field(default_factory=dict)
    missing_paths: tuple[str, ...] = field(default_factory=tuple)
    _scope_key_index: dict[tuple[tuple[str, str], ...], tuple[int, ...]] = field(
        default_factory=dict,
        repr=False,
    )

    @classmethod
    def from_rows(
        cls,
        rows: list[dict[str, Any]],
        *,
        artifact_paths: tuple[str, ...],
        rows_loaded_by_path: dict[str, int],
        missing_paths: tuple[str, ...] = (),
    ) -> "GTOSVNextEvidenceIndex":
        enriched_rows = tuple(_enrich_runtime_row(row) for row in rows)
        scopes = tuple(_row_scope(row) for row in enriched_rows)
        buckets: dict[tuple[tuple[str, str], ...], list[int]] = defaultdict(list)
        for index, scope in enumerate(scopes):
            for key in _scope_key_variants(scope):
                buckets[key].append(index)
        compact = {key: tuple(indices) for key, indices in buckets.items()}
        return cls(
            rows=enriched_rows,
            scopes=scopes,
            artifact_paths=artifact_paths,
            rows_loaded_by_path=dict(rows_loaded_by_path),
            missing_paths=missing_paths,
            _scope_key_index=compact,
        )

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def match_event(
        self,
        event: dict[str, Any],
        *,
        min_scope_fields: int = 1,
        source_names: set[str] | None = None,
        evidence_families: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        normalized_event = normalize_event(event)
        criteria_key = _event_criteria_key(normalized_event)
        if not criteria_key:
            return []

        candidate_indices: set[int] = set()
        for size in range(1, len(criteria_key) + 1):
            for subset in combinations(criteria_key, size):
                candidate_indices.update(self._scope_key_index.get(tuple(subset), ()))

        matches: list[dict[str, Any]] = []
        for index in sorted(candidate_indices):
            scope = self.scopes[index]
            if len(scope) < min_scope_fields:
                continue
            row = self.rows[index]
            if source_names and str(row.get("source_name") or "") not in source_names:
                continue
            if evidence_families and str(row.get("evidence_family") or "") not in evidence_families:
                continue
            if _scope_matches(scope, normalized_event) and _row_matches_event_filters(
                row,
                normalized_event,
            ):
                matches.append(dict(row))
        return matches


@dataclass(frozen=True)
class GTOSVNextBridgeDiagnostics:
    """Non-scoring vNext bridge registry and event-validation diagnostics."""

    rows: tuple[dict[str, Any], ...]
    artifact_paths: tuple[str, ...]
    rows_loaded_by_path: dict[str, int] = field(default_factory=dict)
    missing_paths: tuple[str, ...] = field(default_factory=tuple)

    @property
    def row_count(self) -> int:
        return len(self.rows)


def _configured_local_heavy_data_roots(config: dict[str, Any] | None) -> tuple[Path, ...]:
    config = config or {}
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    if not bool(cfg.get("local_heavy_data_search_enabled", True)):
        return ()

    raw_roots: list[Any] = []
    configured = cfg.get("local_heavy_data_search_roots")
    if isinstance(configured, list):
        raw_roots.extend(configured)
    elif configured:
        raw_roots.append(configured)

    top_level = config.get("local_heavy_data", {}) or {}
    top_roots = top_level.get("search_roots")
    if isinstance(top_roots, list):
        raw_roots.extend(top_roots)
    elif top_roots:
        raw_roots.append(top_roots)

    if not raw_roots and bool(cfg.get("local_heavy_data_use_default_roots", False)):
        raw_roots.extend(DEFAULT_LOCAL_HEAVY_DATA_ROOTS)

    roots: list[Path] = []
    seen: set[str] = set()
    for raw in raw_roots:
        if raw in (None, ""):
            continue
        root = Path(str(raw))
        key = str(root).casefold()
        if key in seen:
            continue
        seen.add(key)
        roots.append(root)
    return tuple(roots)


def _resolve_local_heavy_data_path(path: Path, search_roots: Iterable[Path]) -> Path:
    if _local_path_exists(path):
        return path
    if path.is_absolute():
        return path
    for root in search_roots:
        candidate = root / path
        if _local_path_exists(candidate):
            return candidate
    return path


def _configured_artifact_paths(config: dict[str, Any] | None) -> tuple[Path, ...]:
    config = config or {}
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    ai_cfg = config.get("ai_narrowing", {}) or {}
    search_roots = _configured_local_heavy_data_roots(config)
    paths: list[Path] = []
    configured_paths = cfg.get("artifact_paths")
    if isinstance(configured_paths, list):
        for raw in configured_paths:
            if raw:
                paths.append(Path(str(raw)))
    else:
        for key in (
            "implementation_artifact_path",
            "evidence_matrix_artifact_path",
            "review_artifact_path",
            "artifact_path",
            "fallback_artifact_path",
        ):
            raw = cfg.get(key)
            if raw:
                paths.append(Path(str(raw)))
    if not paths:
        paths.extend([
            DEFAULT_IMPLEMENTATION_ARTIFACT_PATH,
            DEFAULT_EVIDENCE_MATRIX_ARTIFACT_PATH,
            DEFAULT_REVIEW_ARTIFACT_PATH,
        ])
    if bool(cfg.get("pre_ai_ai_narrowing_load_capacity_blocklist_artifact", False)):
        raw_blocklist_path = (
            cfg.get("pre_ai_ai_narrowing_capacity_blocklist_artifact_path")
            or ai_cfg.get("capacity_blocklist_path")
            or DEFAULT_AI_NARROWING_CAPACITY_BLOCKLIST_ARTIFACT_PATH
        )
        if raw_blocklist_path:
            paths.append(Path(str(raw_blocklist_path)))
    if bool(cfg.get("load_cp281_rule_replay_result_table_artifact", False)):
        raw_cp281_result_path = (
            cfg.get("cp281_rule_replay_result_table_artifact_path")
            or DEFAULT_CP281_RULE_REPLAY_RESULT_TABLE_ARTIFACT_PATH
        )
        if raw_cp281_result_path:
            paths.append(Path(str(raw_cp281_result_path)))
    if bool(cfg.get("load_cp281_rule_replay_event_artifact", False)):
        raw_cp281_event_path = (
            cfg.get("cp281_rule_replay_event_artifact_path")
            or DEFAULT_CP281_RULE_REPLAY_EVENT_ARTIFACT_PATH
        )
        if raw_cp281_event_path:
            paths.append(Path(str(raw_cp281_event_path)))
    if bool(cfg.get("load_cp281_branch_decisions_artifact", False)):
        raw_cp281_branch_path = (
            cfg.get("cp281_branch_decisions_artifact_path")
            or DEFAULT_CP281_BRANCH_DECISIONS_ARTIFACT_PATH
        )
        if raw_cp281_branch_path:
            paths.append(Path(str(raw_cp281_branch_path)))
    if bool(cfg.get("load_cp281_ready_runtime_aggregate_artifact", False)):
        raw_cp281_aggregate_path = (
            cfg.get("cp281_ready_runtime_aggregate_artifact_path")
            or DEFAULT_CP281_READY_RUNTIME_AGGREGATE_ARTIFACT_PATH
        )
        if raw_cp281_aggregate_path:
            paths.append(Path(str(raw_cp281_aggregate_path)))
    if bool(cfg.get("load_cp281_ready_runtime_rule_artifact", False)):
        raw_cp281_rule_path = (
            cfg.get("cp281_ready_runtime_rule_artifact_path")
            or DEFAULT_CP281_READY_RUNTIME_RULE_ARTIFACT_PATH
        )
        if raw_cp281_rule_path:
            paths.append(Path(str(raw_cp281_rule_path)))
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = _resolve_local_heavy_data_path(path, search_roots)
        key = str(resolved)
        if key not in seen:
            deduped.append(resolved)
            seen.add(key)
    return tuple(deduped)


@lru_cache(maxsize=16)
def _load_evidence_index_cached(paths_key: tuple[str, ...]) -> GTOSVNextEvidenceIndex:
    rows: list[dict[str, Any]] = []
    loaded_paths: list[str] = []
    missing_paths: list[str] = []
    rows_loaded_by_path: dict[str, int] = {}
    for raw_path in paths_key:
        path = Path(raw_path)
        if not _local_path_exists(path):
            missing_paths.append(raw_path)
            continue
        try:
            loaded = _read_jsonl(path)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("GTOS vNext runtime artifact unreadable: %s (%s)", path, exc)
            continue
        if loaded:
            loaded_paths.append(raw_path)
            rows_loaded_by_path[raw_path] = len(loaded)
            for row in loaded:
                copied = dict(row)
                copied["_gtos_vnext_loaded_from"] = raw_path
                rows.append(copied)
    rows = _merge_cp281_rule_replay_event_provenance(rows)
    rows = _merge_cp281_aggregate_provenance(rows)
    for row in rows:
        row["_gtos_vnext_loaded_paths"] = loaded_paths
        row["_gtos_vnext_missing_paths"] = missing_paths
    return GTOSVNextEvidenceIndex.from_rows(
        rows,
        artifact_paths=tuple(loaded_paths),
        rows_loaded_by_path=rows_loaded_by_path,
        missing_paths=tuple(missing_paths),
    )


def load_vnext_evidence_index(paths: Iterable[Path | str]) -> GTOSVNextEvidenceIndex:
    key = tuple(str(path) for path in paths)
    return _load_evidence_index_cached(key)


def load_artifact_rows(paths: Iterable[Path | str]) -> list[dict[str, Any]]:
    return [dict(row) for row in load_vnext_evidence_index(paths).rows]


def _min_loaded_evidence_rows(cfg: dict[str, Any]) -> int:
    return max(0, int(_configured_float(cfg, "min_loaded_evidence_rows", 0.0)))


def _evidence_index_below_min_rows(
    index: GTOSVNextEvidenceIndex,
    cfg: dict[str, Any],
) -> bool:
    min_rows = _min_loaded_evidence_rows(cfg)
    return bool(min_rows and index.row_count < min_rows)


def _evidence_index_denominator_evidence(
    index: GTOSVNextEvidenceIndex,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    return {
        "runtime_index": {
            "row_count": index.row_count,
            "rows_loaded_by_path": index.rows_loaded_by_path,
            "missing_paths": list(index.missing_paths),
            "min_loaded_evidence_rows": _min_loaded_evidence_rows(cfg),
            "compiled_from_full_evidence": any(
                str(path).endswith("GTOS_VNEXT_EVIDENCE_TO_SYSTEM_BUILD_MATRIX_2026-05-18.jsonl")
                for path in index.artifact_paths
            ),
        }
    }


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().casefold()
    return text in {"1", "true", "yes", "y", "on"}


def _configured_bridge_diagnostic_paths(cfg: dict[str, Any] | None) -> tuple[Path, ...]:
    cfg = cfg or {}
    if not bool(cfg.get("bridge_diagnostics_enabled", False)):
        return ()
    configured_paths = cfg.get("bridge_diagnostic_artifact_paths")
    paths: list[Path] = []
    if isinstance(configured_paths, list):
        paths.extend(Path(str(raw)) for raw in configured_paths if raw)
    elif configured_paths:
        paths.append(Path(str(configured_paths)))
    if not paths:
        paths.append(DEFAULT_BRIDGE_DIAGNOSTIC_ARTIFACT_PATH)
    return tuple(paths)


@lru_cache(maxsize=16)
def _load_bridge_diagnostics_cached(paths_key: tuple[str, ...]) -> GTOSVNextBridgeDiagnostics:
    rows: list[dict[str, Any]] = []
    loaded_paths: list[str] = []
    missing_paths: list[str] = []
    rows_loaded_by_path: dict[str, int] = {}
    for raw_path in paths_key:
        path = Path(raw_path)
        if not _local_path_exists(path):
            missing_paths.append(raw_path)
            continue
        try:
            loaded = _read_jsonl(path)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("GTOS vNext bridge diagnostic artifact unreadable: %s (%s)", path, exc)
            missing_paths.append(raw_path)
            continue
        if loaded:
            loaded_paths.append(raw_path)
            rows_loaded_by_path[raw_path] = len(loaded)
            for row in loaded:
                copied = dict(row)
                copied["_gtos_vnext_bridge_loaded_from"] = raw_path
                rows.append(copied)
    return GTOSVNextBridgeDiagnostics(
        rows=tuple(rows),
        artifact_paths=tuple(loaded_paths),
        rows_loaded_by_path=rows_loaded_by_path,
        missing_paths=tuple(missing_paths),
    )


def load_vnext_bridge_diagnostics(
    config: dict[str, Any] | None,
) -> GTOSVNextBridgeDiagnostics:
    """Load non-scoring bridge diagnostic rows from vNext config."""
    cfg = (config or {}).get("gtos_vnext_runtime", config or {}) or {}
    paths = _configured_bridge_diagnostic_paths(cfg)
    return _load_bridge_diagnostics_cached(tuple(str(path) for path in paths))


def _limited_counter(values: Iterable[Any], *, limit: int = 24) -> dict[str, int]:
    counter = Counter(str(value) for value in values if value not in (None, ""))
    return dict(counter.most_common(limit))


def _bridge_diagnostics_for_event(
    normalized_event: dict[str, str],
    cfg: dict[str, Any] | None,
) -> dict[str, Any]:
    diagnostics = load_vnext_bridge_diagnostics(cfg or {})
    if not diagnostics.row_count and not diagnostics.missing_paths:
        return {}
    rows = diagnostics.rows
    event_rollup_rows = [
        row
        for row in rows
        if row.get("source_component") == "bridge_event_scope_rollup"
    ]
    registry_catalog_rows = [
        row for row in rows if row.get("source_component") == "bridge_registry_catalog"
    ]
    current_rollup_matches = [
        row
        for row in event_rollup_rows
        if _scope_matches(_row_scope(row), normalized_event)
    ]
    current_registry_matches = [
        row
        for row in registry_catalog_rows
        if _scope_matches(_row_scope(row), normalized_event)
    ]
    event_source_summary_rows = [
        row
        for row in rows
        if row.get("source_component") == "bridge_event_source_summary"
    ]
    return {
        "enabled": bool((cfg or {}).get("bridge_diagnostics_enabled", False)),
        "diagnostic_only": True,
        "row_count": diagnostics.row_count,
        "artifact_paths": list(diagnostics.artifact_paths),
        "rows_loaded_by_path": diagnostics.rows_loaded_by_path,
        "missing_paths": list(diagnostics.missing_paths),
        "source_component_counts": _limited_counter(
            row.get("source_component") for row in rows
        ),
        "bridge_source_kind_counts": _limited_counter(
            row.get("bridge_source_kind") for row in rows
        ),
        "original_evidence_family_counts": _limited_counter(
            row.get("bridge_original_evidence_family") for row in rows
        ),
        "original_system_surface_counts": _limited_counter(
            row.get("bridge_original_system_surface") for row in rows
        ),
        "original_implementation_action_counts": _limited_counter(
            row.get("bridge_original_implementation_action") for row in rows
        ),
        "self_check_status_counts": _limited_counter(
            row.get("self_check_status") for row in rows
        ),
        "callable_event_match_enabled_rows": sum(
            1 for row in rows if _truthy(row.get("callable_event_match_enabled"))
        ),
        "runtime_score_allowed_rows": sum(
            1 for row in rows if _truthy(row.get("runtime_score_allowed"))
        ),
        "candidate_use_allowed_now_rows": sum(
            1 for row in rows if _truthy(row.get("candidate_use_allowed_now"))
        ),
        "broker_operation_rows": sum(
            1 for row in rows if _truthy(row.get("broker_operation"))
        ),
        "paid_api_or_vendor_call_rows": sum(
            1 for row in rows if _truthy(row.get("paid_api_or_vendor_call"))
        ),
        "event_validation": {
            "scope_rollup_rows": len(event_rollup_rows),
            "source_summary_rows": len(event_source_summary_rows),
            "source_rows": sum(int(row.get("source_rows") or 0) for row in event_source_summary_rows),
            "matched_event_rows": sum(int(row.get("matched_event_rows") or 0) for row in event_rollup_rows),
            "unmatched_event_rows": sum(int(row.get("unmatched_event_rows") or 0) for row in event_rollup_rows),
            "registry_match_rows": sum(int(row.get("registry_match_rows") or 0) for row in event_rollup_rows),
            "parse_error_rows": sum(int(row.get("parse_error_rows") or 0) for row in event_source_summary_rows),
        },
        "current_event": {
            "matched_scope_rollup_rows": len(current_rollup_matches),
            "matched_registry_catalog_rows": len(current_registry_matches),
            "matched_event_rows": sum(int(row.get("matched_event_rows") or 0) for row in current_rollup_matches),
            "unmatched_event_rows": sum(int(row.get("unmatched_event_rows") or 0) for row in current_rollup_matches),
            "registry_match_rows": sum(int(row.get("registry_match_rows") or 0) for row in current_rollup_matches),
            "symbols": sorted({str(row.get("symbol")) for row in current_rollup_matches if row.get("symbol")}),
            "route_sessions": sorted({str(row.get("route_session")) for row in current_rollup_matches if row.get("route_session")}),
            "sides": sorted({str(row.get("side")) for row in current_rollup_matches if row.get("side")}),
        },
    }


def _bridge_diagnostics_evidence(
    normalized_event: dict[str, str],
    cfg: dict[str, Any] | None,
) -> dict[str, Any]:
    diagnostics = _bridge_diagnostics_for_event(normalized_event, cfg)
    return {"bridge_diagnostics": diagnostics} if diagnostics else {}


def _ai_narrowing_blocklist_scope_enabled(cfg: dict[str, Any]) -> bool:
    return bool(cfg.get("pre_ai_ai_narrowing_capacity_blocklist_active", False)) and bool(
        cfg.get("pre_ai_ai_narrowing_allow_blocklist_required_scopes", False)
    )


def _ai_narrowing_capacity_blocklist_decision(
    row: dict[str, Any],
    cfg: dict[str, Any] | None,
) -> DecisionLabel | None:
    """Translate capacity-blocklist rows into pre-AI selector route evidence."""
    cfg = cfg or {}
    if not bool(cfg.get("pre_ai_ai_narrowing_capacity_blocklist_decision_enabled", True)):
        return None

    status = _normalized(row.get("ai_narrowing_capacity_blocklist_status")).upper()
    if not status:
        return None
    if "PRESERVED_REDESIGN_ONLY_KEEP_AI_UNCHANGED" in status:
        return "MIXED"
    if "REQUIRED_FOR_PRE_AI_SELECTOR_REVIEW" in status:
        return "FOLLOW" if _ai_narrowing_blocklist_scope_enabled(cfg) else "MIXED"
    return None


def _ai_narrowing_policy_decision(row: dict[str, Any], cfg: dict[str, Any] | None) -> DecisionLabel | None:
    """Translate default-off AI selector policy rows into runtime route evidence."""
    cfg = cfg or {}
    if not bool(cfg.get("pre_ai_ai_narrowing_policy_decision_enabled", True)):
        return None

    if (
        _normalized(row.get("source_name")) != "ai_narrowing_policy"
        and _normalized(row.get("evidence_family")) != "ai_decision_architecture"
    ):
        return None

    status = _normalized(
        row.get("ai_narrowing_policy_status") or row.get("implementation_action")
    ).upper()
    if "KEEP_AI_UNCHANGED" in status or "REDESIGN_ONLY" in status:
        return "MIXED"
    if "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY" not in status:
        return None

    blocklist_required = (
        _truthy(row.get("capacity_blocklist_required_before_ai_narrowing"))
        or "WITH_CAPACITY_BLOCKLIST" in status
    )
    if blocklist_required and not (
        _ai_narrowing_blocklist_scope_enabled(cfg)
    ):
        return "MIXED"
    return "FOLLOW"


def _row_failure_intelligence_search_text(row: dict[str, Any]) -> str:
    parts: list[str] = []
    scope = row.get("event_scope")
    if isinstance(scope, dict):
        for value in scope.values():
            if value not in (None, ""):
                parts.append(_normalized(value))
    for field_name in FAILURE_INTELLIGENCE_SCAN_FIELDS:
        value = row.get(field_name)
        if value in (None, ""):
            continue
        if isinstance(value, (dict, list, tuple)):
            try:
                parts.append(json.dumps(value, sort_keys=True))
            except TypeError:
                parts.append(str(value))
        else:
            parts.append(_normalized(value))
    return " ".join(parts).casefold()


def _row_matching_configured_tokens(
    row: dict[str, Any],
    cfg: dict[str, Any] | None,
    key: str,
    defaults: Iterable[str],
    *,
    token_boundary: bool = False,
) -> list[str]:
    runtime_cfg = cfg or {}
    text = _row_failure_intelligence_search_text(row)
    tokens = _configured_list(runtime_cfg, key, defaults)
    matched: list[str] = []
    for token in tokens:
        token_text = token.casefold()
        if not token_text:
            continue
        if token_boundary:
            pattern = rf"(?<![a-z0-9]){re.escape(token_text)}(?![a-z0-9])"
            if re.search(pattern, text):
                matched.append(token)
        elif token_text in text:
            matched.append(token)
    return matched


def _row_has_false_source_complete_flag(row: dict[str, Any], cfg: dict[str, Any] | None) -> bool:
    fields = _configured_list(
        cfg or {},
        "failure_intelligence_source_complete_fields",
        DEFAULT_FAILURE_SOURCE_COMPLETE_FIELDS,
    )
    for field_name in fields:
        if field_name in row and row.get(field_name) not in (None, ""):
            return not _truthy(row.get(field_name))
    return False


def _row_has_truthy_configured_field(
    row: dict[str, Any],
    cfg: dict[str, Any] | None,
    key: str,
    defaults: Iterable[str],
) -> bool:
    for field_name in _configured_list(cfg or {}, key, defaults):
        if field_name in row and row.get(field_name) not in (None, "") and _truthy(row.get(field_name)):
            return True
    return False


def _failure_intelligence_guard_info(
    row: dict[str, Any],
    cfg: dict[str, Any] | None,
) -> dict[str, Any]:
    runtime_cfg = cfg or {}
    enabled = bool(runtime_cfg.get("failure_intelligence_guard_enabled", True))
    if not enabled:
        return {
            "enabled": False,
            "guarded": False,
            "runtime_evidence_executable": True,
            "non_executable_tokens": [],
            "executable_avoid_tokens": [],
            "source_complete": True,
        }

    non_executable_tokens = _row_matching_configured_tokens(
        row,
        runtime_cfg,
        "failure_intelligence_non_executable_tokens",
        DEFAULT_NON_EXECUTABLE_FAILURE_INTELLIGENCE_TOKENS,
    )
    executable_avoid_tokens = _row_matching_configured_tokens(
        row,
        runtime_cfg,
        "failure_intelligence_executable_avoid_tokens",
        DEFAULT_EXECUTABLE_FAILURE_AVOID_TOKENS,
    )
    source_complete_flag_false = _row_has_false_source_complete_flag(row, runtime_cfg)
    source_complete_flag_true = _row_has_truthy_configured_field(
        row,
        runtime_cfg,
        "failure_intelligence_source_complete_fields",
        DEFAULT_FAILURE_SOURCE_COMPLETE_FIELDS,
    )
    source_complete = (
        (bool(non_executable_tokens == []) or source_complete_flag_true)
        and not source_complete_flag_false
    )
    guarded = (bool(non_executable_tokens) or source_complete_flag_false) and not (
        bool(executable_avoid_tokens) and source_complete
    )
    return {
        "enabled": True,
        "guarded": guarded,
        "runtime_evidence_executable": not guarded,
        "non_executable_tokens": non_executable_tokens,
        "executable_avoid_tokens": executable_avoid_tokens,
        "source_complete": source_complete,
        "source_complete_flag_true": source_complete_flag_true,
        "source_complete_flag_false": source_complete_flag_false,
        "reason": (
            "non_executable_failure_intelligence"
            if guarded
            else (
                "explicit_executable_avoid_filter_candidate"
                if executable_avoid_tokens
                else ""
            )
        ),
    }


def _orderflow_diagnostic_guard_info(
    row: dict[str, Any],
    cfg: dict[str, Any] | None,
) -> dict[str, Any]:
    runtime_cfg = cfg or {}
    enabled = bool(runtime_cfg.get("orderflow_diagnostic_guard_enabled", True))
    if not enabled:
        return {
            "enabled": False,
            "guarded": False,
            "runtime_evidence_executable": True,
            "orderflow_tokens": [],
            "runtime_validated": True,
        }

    orderflow_tokens = _row_matching_configured_tokens(
        row,
        runtime_cfg,
        "orderflow_diagnostic_tokens",
        DEFAULT_ORDERFLOW_DIAGNOSTIC_TOKENS,
        token_boundary=True,
    )
    ready_tokens = _row_matching_configured_tokens(
        row,
        runtime_cfg,
        "orderflow_runtime_ready_tokens",
        DEFAULT_ORDERFLOW_RUNTIME_READY_TOKENS,
        token_boundary=True,
    )
    runtime_validated = bool(ready_tokens) or _row_has_truthy_configured_field(
        row,
        runtime_cfg,
        "orderflow_runtime_validated_fields",
        DEFAULT_ORDERFLOW_RUNTIME_VALIDATED_FIELDS,
    )
    guarded = bool(orderflow_tokens) and not runtime_validated
    return {
        "enabled": True,
        "guarded": guarded,
        "runtime_evidence_executable": not guarded,
        "orderflow_tokens": orderflow_tokens,
        "ready_tokens": ready_tokens,
        "runtime_validated": runtime_validated,
        "reason": "orderflow_diagnostic_only_until_transfer_validated" if guarded else "",
    }


def _implementation_action_decision(
    row: dict[str, Any],
    cfg: dict[str, Any] | None,
) -> DecisionLabel | None:
    """Classify full-ledger implementation actions before metric fallback.

    The implementation/evidence matrix carries action semantics for many rows
    whose R metrics are source-repair or proxy-only. Keeping those rows as
    generic MIXED erases follow/avoid instructions the runtime can safely use
    in default-off route evidence.
    """
    cfg = cfg or {}
    if not bool(cfg.get("implementation_action_decision_enabled", True)):
        return None
    action = _normalized(row.get("implementation_action")).upper()
    if not action:
        return None

    mixed_tokens = _configured_list(
        cfg,
        "implementation_action_mixed_tokens",
        [
            "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R",
            "BROKER_GEOMETRY_ATTACHMENT_REQUIRED_FOR_EXACT_SPREAD_PROXY",
            "EXECUTE_SOURCE_GEOMETRY_REPAIR_SCOPE",
            "SOURCE_JOIN_REPAIR_REQUIRED",
            "READY_DEFAULT_OFF_SOURCE_REPAIR",
            "SOURCE_PACKET_CONTEXT_SELECTOR_EXECUTION_IDENTITY_ABSENT",
            "MERGE_AS_CONTEXT_STRESS_GUARD_INPUT",
            "MERGE_CONTEXT_STRESS_SCOPE_AS_GUARD_INPUT",
            "KEEP_AI_UNCHANGED",
            "REDESIGN_ONLY",
            "PRESERVE_NUMERIC_ROUTER_SYSTEM_RECOMMENDATION_AS_NON_TERMINAL_INPUT",
        ],
    )
    if any(token.upper() in action for token in mixed_tokens):
        return "MIXED"

    avoid_tokens = _configured_list(
        cfg,
        "implementation_action_avoid_tokens",
        [
            "REGISTER_NEGATIVE_PROXY_FAILURE_FEATURE",
            "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE",
            "AVOID_CURRENT_ENTRY_STOP_FIRST_PROXY",
            "FAIL_CLOSED_OR_DOWNWEIGHT_AMBIGUOUS_NEGATIVE_PROXY",
            "REGISTER_DEFAULT_OFF_CP281_AVOID_FILTER_RULE",
        ],
    )
    if any(token.upper() in action for token in avoid_tokens):
        return "AVOID"

    follow_tokens = _configured_list(
        cfg,
        "implementation_action_follow_tokens",
        [
            "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
            "IMPLEMENT_DEFAULT_OFF_SCORER_SCOPE_WITH_GUARDS",
            "REGISTER_DEFAULT_OFF_CP281_FOLLOW_SCORER_RULE",
            "REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE",
            "REGISTER_DEFAULT_OFF_BRANCH_LOCAL_PRESERVED_REDUCED_SURFACE_CANDIDATE",
        ],
    )
    if any(token.upper() in action for token in follow_tokens):
        return "FOLLOW"
    return None


def _decision_from_row(row: dict[str, Any], cfg: dict[str, Any] | None = None) -> DecisionLabel:
    failure_guard = _failure_intelligence_guard_info(row, cfg)
    if failure_guard["guarded"]:
        return "MIXED"
    orderflow_guard = _orderflow_diagnostic_guard_info(row, cfg)
    if orderflow_guard["guarded"]:
        return "MIXED"

    ai_blocklist_decision = _ai_narrowing_capacity_blocklist_decision(row, cfg)
    if ai_blocklist_decision:
        return ai_blocklist_decision

    ai_policy_decision = _ai_narrowing_policy_decision(row, cfg)
    if ai_policy_decision:
        return ai_policy_decision

    review_action = _normalized(row.get("review_action")).upper()
    if "FOLLOW" in review_action:
        return "FOLLOW"
    if "AVOID" in review_action:
        return "AVOID"
    if "MIXED" in review_action or "CATALOG" in review_action:
        return "MIXED"

    action_class = _normalized(row.get("action_class")).casefold()
    if "follow" in action_class:
        return "FOLLOW"
    if "avoid" in action_class or "filter" in action_class:
        return "AVOID"

    implementation_decision = _implementation_action_decision(row, cfg)
    if implementation_decision:
        return implementation_decision

    cost = _metric_sum(row, "cost_adjusted_simulated_r")
    stress = _metric_sum(row, "stress_simulated_r")
    proxy = _metric_sum(row, "proxy_score")
    positive = [value for value in (cost, stress, proxy) if value is not None and value > 0]
    negative = [value for value in (cost, stress, proxy) if value is not None and value < 0]
    if negative and not positive:
        return "AVOID"
    if positive and not negative:
        return "FOLLOW"
    if positive or negative:
        return "MIXED"
    return "MIXED"


def _metric_trace(row: dict[str, Any], metric: str) -> dict[str, Any] | None:
    traces = row.get("r_metric_traces")
    if isinstance(traces, dict) and isinstance(traces.get(metric), dict):
        return traces[metric]
    metrics = row.get("r_metrics")
    if isinstance(metrics, dict) and isinstance(metrics.get(metric), dict):
        return metrics[metric]
    return None


def _metric_sum(row: dict[str, Any], metric: str) -> float | None:
    trace = _metric_trace(row, metric)
    if not trace:
        return None
    return _to_float(trace.get("sum"))


def _aggregate_metric(rows: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    total_sum = 0.0
    total_count = 0.0
    positive_rows = 0
    negative_rows = 0
    zero_rows = 0
    rows_with_metric = 0

    for row in rows:
        trace = _metric_trace(row, metric)
        if not trace:
            continue
        metric_sum = _to_float(trace.get("sum"))
        metric_count = _to_float(trace.get("match_rows_with_metric"))
        if metric_count is None:
            metric_count = _to_float(trace.get("count"))
        if metric_sum is None:
            mean = _to_float(trace.get("mean"))
            if mean is not None and metric_count is not None:
                metric_sum = mean * metric_count
        if metric_sum is None:
            continue

        rows_with_metric += 1
        total_sum += metric_sum
        total_count += metric_count or 1.0
        positive_rows += int(trace.get("positive_rows") or (1 if metric_sum > 0 else 0))
        negative_rows += int(trace.get("negative_rows") or (1 if metric_sum < 0 else 0))
        zero_rows += int(trace.get("zero_rows") or (1 if metric_sum == 0 else 0))

    mean = total_sum / total_count if total_count else None
    return {
        "rows_with_metric": rows_with_metric,
        "sum": round(total_sum, 12) if rows_with_metric else None,
        "count": total_count if rows_with_metric else 0,
        "mean": round(mean, 12) if mean is not None else None,
        "positive_rows": positive_rows,
        "negative_rows": negative_rows,
        "zero_rows": zero_rows,
    }


def _evidence_row(row: dict[str, Any], cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    scope = _row_scope(row)
    failure_guard = _failure_intelligence_guard_info(row, cfg)
    orderflow_guard = _orderflow_diagnostic_guard_info(row, cfg)
    return {
        "row_id": (
            row.get("review_row_id")
            or row.get("vnext_matrix_row_id")
            or row.get("event_scope_rollup_row_id")
            or row.get("registry_catalog_row_id")
            or row.get("ai_narrowing_policy_row_id")
        or row.get("ai_narrowing_capacity_blocklist_row_id")
        or row.get("ai_narrowing_default_off_runtime_row_id")
        or row.get("ai_decision_trace_routing_guard_runtime_row_id")
        or row.get("pre_ai_post_l2_routing_policy_runtime_row_id")
        or row.get("rejected_candidate_l2_value_mining_runtime_row_id")
        or row.get("accepted_candidate_m1_fill_source_repair_runtime_row_id")
        or row.get("trade_record_execution_lifecycle_runtime_row_id")
        or row.get("numeric_router_catalog_runtime_row_id")
            or row.get("survivor_failure_runtime_row_id")
            or row.get("cp280_scorer_filter_router_runtime_row_id")
            or row.get("branch_implementation_replay_runtime_row_id")
            or row.get("branch_ambiguity_collapse_runtime_row_id")
            or row.get("branch_followup_computation_runtime_row_id")
            or row.get("adverse_stop_first_execution_runtime_row_id")
            or row.get("gate_selector_session_timeframe_runtime_row_id")
            or row.get("risk_proxy_stress_cost_runtime_row_id")
            or row.get("sierra_depth_source_acquisition_runtime_row_id")
            or row.get("source_repair_missing_denominator_runtime_row_id")
            or row.get("nr_source_repair_execution_identity_runtime_row_id")
            or row.get("nofill_pending_lifecycle_runtime_row_id")
            or row.get("source_geometry_runtime_row_id")
            or row.get("source_geometry_repair_row_id")
            or row.get("legacy_ai_cascade_model_runtime_row_id")
            or row.get("legacy_v2_v3_paper_live_friction_runtime_row_id")
            or row.get("sl_beyond_ob_outcome_join_source_repair_runtime_row_id")
            or row.get("fvg_trade_record_bounds_execution_runtime_row_id")
            or row.get("scid_target_horizon_control_runtime_row_id")
            or row.get("main_orch24_structural_repair_action_runtime_row_id")
            or row.get("main_orch24_action_completeness_residual_r_runtime_row_id")
            or row.get("main_orch24_implementation_selection_runtime_row_id")
            or row.get("main_orch24_snapshot_dependency_repair_runtime_row_id")
            or row.get("main_orch48_final_review_selector_runtime_row_id")
            or row.get("ltf_path_geometry_source_runtime_row_id")
            or row.get("instrument_expansion_market_session_runtime_row_id")
            or row.get("scid_combined_source_capture_poi_bounds_runtime_row_id")
            or row.get("frontier_action_id")
            or row.get("recommendation_unified_candidate_id")
            or row.get("bucket_id")
            or row.get("numeric_result_row_id")
            or row.get("row_key")
            or ""
        ),
        "decision": _decision_from_row(row, cfg),
        "event_scope": scope,
        "symbol": row.get("symbol") or scope.get("symbol"),
        "source_symbol": row.get("source_symbol") or scope.get("source_symbol"),
        "symbol_family": row.get("symbol_family") or scope.get("symbol_family"),
        "market": row.get("market") or scope.get("market"),
        "timeframe": row.get("timeframe") or scope.get("timeframe"),
        "framework": row.get("framework") or scope.get("framework"),
        "route_family": (
            row.get("route_family")
            or scope.get("route_family")
            or _route_family_for_framework(row.get("framework") or scope.get("framework"))
        ),
        "market_timeframe": row.get("market_timeframe") or scope.get("market_timeframe"),
        "route_session": row.get("route_session") or scope.get("route_session"),
        "horizon_id": row.get("horizon_id") or scope.get("horizon_id"),
        "side": row.get("side") or scope.get("side"),
        "expected_sign_inferred": row.get("expected_sign_inferred"),
        "source_component": row.get("source_component") or scope.get("source_component"),
        "source_path_sha256": row.get("source_path_sha256") or scope.get("source_path_sha256"),
        "source_file_sha256": row.get("source_file_sha256") or scope.get("source_file_sha256"),
        "action_class": row.get("action_class") or scope.get("action_class"),
        "entry_variant": row.get("entry_variant") or scope.get("entry_variant"),
        "proxy_r_class": row.get("proxy_r_class") or scope.get("proxy_r_class"),
        "target_stop_order_class": row.get("target_stop_order_class") or scope.get("target_stop_order_class"),
        "row_route_decision": row.get("row_route_decision") or scope.get("row_route_decision"),
        "source_rows_represented": row.get("source_rows_represented"),
        "m1_support_class": row.get("m1_support_class"),
        "positive_result_class": row.get("positive_result_class"),
        "source_result_class": row.get("source_result_class"),
        "rejected_repair_class": row.get("rejected_repair_class"),
        "r_evidence_class": row.get("r_evidence_class"),
        "r_metrics": row.get("r_metrics"),
        "implementation_action": row.get("implementation_action"),
        "source_group": row.get("source_group"),
        "source_role": row.get("source_role"),
        "system_surface": row.get("system_surface"),
        "runtime_candidate_use_permitted": row.get("runtime_candidate_use_permitted"),
        "candidate_use_allowed_now": row.get("candidate_use_allowed_now"),
        "legacy_cannot_override_fresher_cp280_cp281_cp282": row.get(
            "legacy_cannot_override_fresher_cp280_cp281_cp282"
        ),
        "fresh_moonshot_cp_evidence_override_allowed": row.get(
            "fresh_moonshot_cp_evidence_override_allowed"
        ),
        "live_effect": row.get("live_effect"),
        "runtime_effect_now": row.get("runtime_effect_now"),
        "source_path": row.get("source_path") or row.get("source_artifact"),
        "drill_through_path": (
            row.get("drill_through_path")
            or row.get("declared_origin_artifact")
            or row.get("source_path")
            or row.get("source_artifact")
        ),
        "declared_origin_artifact": row.get("declared_origin_artifact"),
        "declared_origin_line_no": row.get("declared_origin_line_no"),
        "source_name": row.get("source_name"),
        "evidence_family": row.get("evidence_family"),
        "runtime_evidence_executable": (
            failure_guard["runtime_evidence_executable"]
            and orderflow_guard["runtime_evidence_executable"]
        ),
        "failure_intelligence_guard": {
            key: value
            for key, value in failure_guard.items()
            if key
            in {
                "enabled",
                "guarded",
                "non_executable_tokens",
                "executable_avoid_tokens",
                "source_complete",
                "source_complete_flag_false",
                "reason",
            }
            if value not in ([], "", None)
        },
        "orderflow_diagnostic_guard": {
            key: value
            for key, value in orderflow_guard.items()
            if key
            in {
                "enabled",
                "guarded",
                "orderflow_tokens",
                "ready_tokens",
                "runtime_validated",
                "reason",
            }
            if value not in ([], "", None)
        },
        "route_family_inferred_from": row.get("route_family_inferred_from"),
        "primitive": row.get("primitive"),
        "frontier_action_id": row.get("frontier_action_id"),
        "route_frontier_id": row.get("route_frontier_id"),
        "route_candidate_id": row.get("route_candidate_id"),
        "frontier_status": row.get("frontier_status"),
        "action_family": row.get("action_family"),
        "blocker_id": row.get("blocker_id"),
        "frozen_rule_id": row.get("frozen_rule_id"),
        "required_resolution_before_promotion": row.get("required_resolution_before_promotion"),
        "status": row.get("status"),
        "event_count": row.get("event_count"),
        "unique_dates": row.get("unique_dates"),
        "baseline_bar_count": row.get("baseline_bar_count"),
        "max_single_date_share": row.get("max_single_date_share"),
        "primitive_family": row.get("primitive_family"),
        "placebo_status": row.get("placebo_status"),
        "audit_bucket": row.get("audit_bucket"),
        "screen_bucket": row.get("screen_bucket"),
        "next_route": row.get("next_route"),
        "scope_bucket": row.get("scope_bucket"),
        "next_same_resource_action": row.get("next_same_resource_action"),
        "safe_flags": row.get("safe_flags"),
        "source_row_id": row.get("source_row_id"),
        "row_key": row.get("row_key"),
        "source_line_no": row.get("source_line_no") or row.get("declared_origin_line_no"),
        "source_artifact_sha256": row.get("source_artifact_sha256") or row.get("declared_origin_sha256"),
        "loaded_from": row.get("_gtos_vnext_loaded_from"),
        "cp281_aggregate_row_id": row.get("cp281_aggregate_row_id"),
        "cp281_aggregate_provenance": row.get("cp281_aggregate_provenance"),
        "cp281_aggregate_source_row_count": row.get("cp281_aggregate_source_row_count"),
        "cp281_aggregate_loaded_from": row.get("cp281_aggregate_loaded_from"),
        "cp281_rule_replay_event_id": row.get("cp281_rule_replay_event_id"),
        "cp281_rule_replay_event_row_key": row.get("cp281_rule_replay_event_row_key"),
        "cp281_rule_replay_event_payload": row.get("cp281_rule_replay_event_payload"),
        "cp281_rule_replay_event_required_fields": row.get("cp281_rule_replay_event_required_fields"),
        "cp281_rule_replay_event_required_field_count": row.get(
            "cp281_rule_replay_event_required_field_count"
        ),
        "cp281_rule_replay_event_count": row.get("cp281_rule_replay_event_count"),
        "cp281_rule_replay_event_loaded_from": row.get("cp281_rule_replay_event_loaded_from"),
        "cp281_rule_replay_event_provenance": row.get("cp281_rule_replay_event_provenance"),
        "matched_matrix_row_ids_sha256": row.get("matched_matrix_row_ids_sha256"),
        "numeric_result_row_id": row.get("numeric_result_row_id"),
        "numeric_router_catalog_runtime_row_id": row.get(
            "numeric_router_catalog_runtime_row_id"
        ),
        "survivor_failure_runtime_row_id": row.get(
            "survivor_failure_runtime_row_id"
        ),
        "nofill_pending_lifecycle_runtime_row_id": row.get(
            "nofill_pending_lifecycle_runtime_row_id"
        ),
        "sierra_depth_source_acquisition_runtime_row_id": row.get(
            "sierra_depth_source_acquisition_runtime_row_id"
        ),
        "source_repair_missing_denominator_runtime_row_id": row.get(
            "source_repair_missing_denominator_runtime_row_id"
        ),
        "nr_source_repair_execution_identity_runtime_row_id": row.get(
            "nr_source_repair_execution_identity_runtime_row_id"
        ),
        "legacy_ai_cascade_model_runtime_row_id": row.get(
            "legacy_ai_cascade_model_runtime_row_id"
        ),
        "legacy_v2_v3_paper_live_friction_runtime_row_id": row.get(
            "legacy_v2_v3_paper_live_friction_runtime_row_id"
        ),
        "sl_beyond_ob_outcome_join_source_repair_runtime_row_id": row.get(
            "sl_beyond_ob_outcome_join_source_repair_runtime_row_id"
        ),
        "fvg_trade_record_bounds_execution_runtime_row_id": row.get(
            "fvg_trade_record_bounds_execution_runtime_row_id"
        ),
        "scid_target_horizon_control_runtime_row_id": row.get(
            "scid_target_horizon_control_runtime_row_id"
        ),
        "main_orch24_structural_repair_action_runtime_row_id": row.get(
            "main_orch24_structural_repair_action_runtime_row_id"
        ),
        "main_orch24_action_completeness_residual_r_runtime_row_id": row.get(
            "main_orch24_action_completeness_residual_r_runtime_row_id"
        ),
        "main_orch24_implementation_selection_runtime_row_id": row.get(
            "main_orch24_implementation_selection_runtime_row_id"
        ),
        "main_orch24_snapshot_dependency_repair_runtime_row_id": row.get(
            "main_orch24_snapshot_dependency_repair_runtime_row_id"
        ),
        "main_orch48_final_review_selector_runtime_row_id": row.get(
            "main_orch48_final_review_selector_runtime_row_id"
        ),
        "ltf_path_geometry_source_runtime_row_id": row.get(
            "ltf_path_geometry_source_runtime_row_id"
        ),
        "instrument_expansion_market_session_runtime_row_id": row.get(
            "instrument_expansion_market_session_runtime_row_id"
        ),
        "scid_combined_source_capture_poi_bounds_runtime_row_id": row.get(
            "scid_combined_source_capture_poi_bounds_runtime_row_id"
        ),
        "ai_narrowing_default_off_runtime_row_id": row.get(
            "ai_narrowing_default_off_runtime_row_id"
        ),
        "ai_decision_trace_routing_guard_runtime_row_id": row.get(
            "ai_decision_trace_routing_guard_runtime_row_id"
        ),
        "pre_ai_post_l2_routing_policy_runtime_row_id": row.get(
            "pre_ai_post_l2_routing_policy_runtime_row_id"
        ),
        "rejected_candidate_l2_value_mining_runtime_row_id": row.get(
            "rejected_candidate_l2_value_mining_runtime_row_id"
        ),
        "accepted_candidate_m1_fill_source_repair_runtime_row_id": row.get(
            "accepted_candidate_m1_fill_source_repair_runtime_row_id"
        ),
        "trade_record_execution_lifecycle_runtime_row_id": row.get(
            "trade_record_execution_lifecycle_runtime_row_id"
        ),
        "source_ai_narrowing_policy_status": row.get(
            "source_ai_narrowing_policy_status"
        ),
        "source_ai_narrowing_registry_eval_status": row.get(
            "source_ai_narrowing_registry_eval_status"
        ),
        "source_repair_required": row.get("source_repair_required"),
        "runtime_guard_decision_status": row.get("runtime_guard_decision_status"),
        "runtime_enablement_gate_failures": row.get(
            "runtime_enablement_gate_failures"
        ),
        "runtime_halt_active": row.get("runtime_halt_active"),
        "ai_call_skip_allowed_now": row.get("ai_call_skip_allowed_now"),
        "live_ai_runtime_change_now": row.get("live_ai_runtime_change_now"),
        "live_selector_change_now": row.get("live_selector_change_now"),
        "runtime_eligible_after_all_gates": row.get(
            "runtime_eligible_after_all_gates"
        ),
        "source_ai_action": row.get("source_ai_action"),
        "activation_state": row.get("activation_state"),
        "ai_decision": row.get("ai_decision"),
        "ai_grade": row.get("ai_grade"),
        "ai_confidence": row.get("ai_confidence"),
        "ai_response_length": row.get("ai_response_length"),
        "ai_response_sha256": row.get("ai_response_sha256"),
        "model_used": row.get("model_used"),
        "capture_status": row.get("capture_status"),
        "final_outcome": row.get("final_outcome"),
        "lifecycle_state": row.get("lifecycle_state"),
        "lifecycle_completeness": row.get("lifecycle_completeness"),
        "trade_index_lifecycle_status": row.get("trade_index_lifecycle_status"),
        "documented_limitation_codes": row.get("documented_limitation_codes"),
        "action_required_codes": row.get("action_required_codes"),
        "has_execution": row.get("has_execution"),
        "has_exit": row.get("has_exit"),
        "has_embedded_pending_lifecycle": row.get("has_embedded_pending_lifecycle"),
        "has_pending_lifecycle_audit": row.get("has_pending_lifecycle_audit"),
        "pending_lifecycle_final_state": row.get("pending_lifecycle_final_state"),
        "pending_lifecycle_final_state_status": row.get(
            "pending_lifecycle_final_state_status"
        ),
        "pending_lifecycle_missed_move_classification": row.get(
            "pending_lifecycle_missed_move_classification"
        ),
        "pending_lifecycle_trade_id_global_uniqueness_status": row.get(
            "pending_lifecycle_trade_id_global_uniqueness_status"
        ),
        "broker_position_mismatch_status": row.get("broker_position_mismatch_status"),
        "raw_trade_id_collision_symbols": row.get("raw_trade_id_collision_symbols"),
        "trade_record_trade_id": row.get("trade_record_trade_id"),
        "limit_intent_trade_id": row.get("limit_intent_trade_id"),
        "candidate_id": row.get("candidate_id"),
        "decision_time_utc": row.get("decision_time_utc"),
        "record_date": row.get("record_date"),
        "entry_price": row.get("entry_price"),
        "stop_loss": row.get("stop_loss"),
        "take_profit_1": row.get("take_profit_1"),
        "actual_r": row.get("actual_r"),
        "actual_r_class": row.get("actual_r_class"),
        "exit_type": row.get("exit_type"),
        "exit_reason": row.get("exit_reason"),
        "exit_time": row.get("exit_time"),
        "trade_id": row.get("trade_id"),
        "trade_record_source_path": row.get("trade_record_source_path"),
        "prompt_bundle_sha256": row.get("prompt_bundle_sha256"),
        "system_prompt_sha256": row.get("system_prompt_sha256"),
        "user_message_sha256": row.get("user_message_sha256"),
        "stores_full_prompt_or_response_text": row.get(
            "stores_full_prompt_or_response_text"
        ),
        "broker_operation": row.get("broker_operation"),
        "paid_api_or_vendor_call": row.get("paid_api_or_vendor_call"),
        "runtime_trading_or_live_broker_effect": row.get(
            "runtime_trading_or_live_broker_effect"
        ),
        "runtime_observability_effect_if_runtime_reenabled": row.get(
            "runtime_observability_effect_if_runtime_reenabled"
        ),
        "config_enabled": row.get("config_enabled"),
        "primary_analyzer_records_trace": row.get(
            "primary_analyzer_records_trace"
        ),
        "hash_only_schema_present": row.get("hash_only_schema_present"),
        "hash_only_self_check_passed": row.get("hash_only_self_check_passed"),
        "expected_response_status_present_rows": row.get(
            "expected_response_status_present_rows"
        ),
        "required_shadow_labels": row.get("required_shadow_labels"),
        "readiness_status": row.get("readiness_status"),
        "promotion_verdict": row.get("promotion_verdict"),
        "blocker_trigger": row.get("blocker_trigger"),
        "required_event_field": row.get("required_event_field"),
        "adapter_resolution": row.get("adapter_resolution"),
        "adapter_action": row.get("adapter_action"),
        "risk_proxy_stress_cost_runtime_row_id": row.get(
            "risk_proxy_stress_cost_runtime_row_id"
        ),
        "cp280_scorer_filter_router_runtime_row_id": row.get(
            "cp280_scorer_filter_router_runtime_row_id"
        ),
        "branch_ambiguity_collapse_runtime_row_id": row.get(
            "branch_ambiguity_collapse_runtime_row_id"
        ),
        "branch_implementation_replay_runtime_row_id": row.get(
            "branch_implementation_replay_runtime_row_id"
        ),
        "branch_followup_computation_runtime_row_id": row.get(
            "branch_followup_computation_runtime_row_id"
        ),
        "adverse_stop_first_execution_runtime_row_id": row.get(
            "adverse_stop_first_execution_runtime_row_id"
        ),
        "gate_selector_session_timeframe_runtime_row_id": row.get(
            "gate_selector_session_timeframe_runtime_row_id"
        ),
        "source_acquisition_required": row.get("source_acquisition_required"),
        "source_acquisition_kind": row.get("source_acquisition_kind"),
        "source_transfer_validated": row.get("source_transfer_validated"),
        "source_geometry_repair_row_id": row.get("source_geometry_repair_row_id"),
        "source_geometry_runtime_row_id": row.get("source_geometry_runtime_row_id"),
        "recommendation_bucket_id": row.get("bucket_id"),
        "recommendation_unified_candidate_id": row.get(
            "recommendation_unified_candidate_id"
        ),
        "recommendation_unified_candidate_source_row_id": row.get(
            "recommendation_unified_candidate_source_row_id"
        ),
        "recommendation_unified_candidate_surface": row.get(
            "recommendation_unified_candidate_surface"
        ),
        "recommendation_unified_candidate_decision": row.get(
            "recommendation_unified_candidate_decision"
        ),
        "recommendation_unified_candidate_action_class": row.get(
            "recommendation_unified_candidate_action_class"
        ),
        "recommendation_unified_candidate_primitive": row.get(
            "recommendation_unified_candidate_primitive"
        ),
        "recommendation_family_rollup_id": row.get("recommendation_family_rollup_id"),
        "recommendation_family_rollup_type": row.get("recommendation_family_rollup_type"),
        "recommendation_family_rollup_key": row.get("recommendation_family_rollup_key"),
        "recommendation_family_rollup_candidate_rows": row.get(
            "recommendation_family_rollup_candidate_rows"
        ),
        "recommendation_scope_rollup_id": row.get("recommendation_scope_rollup_id"),
        "recommendation_scope_rollup_type": row.get("recommendation_scope_rollup_type"),
        "recommendation_scope_rollup_key": row.get("recommendation_scope_rollup_key"),
        "recommendation_scope_rollup_candidate_rows": row.get(
            "recommendation_scope_rollup_candidate_rows"
        ),
        "recommendation_scope_rollup_primitive": row.get(
            "recommendation_scope_rollup_primitive"
        ),
        "recommendation_scope_rollup_decision_group_row_counts": row.get(
            "recommendation_scope_rollup_decision_group_row_counts"
        ),
        "recommendation_bucket_family": row.get("recommendation_bucket_family"),
        "recommendation_bucket_value": row.get("recommendation_bucket_value"),
        "recommendation_decision_group": row.get("recommendation_decision_group"),
        "recommendation_bucket_live_effect": row.get("live_effect"),
        "recommendation_bucket_not_completion": row.get("not_completion"),
        "recommendation_bucket_claim_boundary": row.get("claim_boundary"),
        "recommendation_bucket_safe_flags": row.get("safe_flags"),
        "recommendation_bucket_source_manifest_hash": row.get("source_manifest_hash"),
        "numeric_rollup_row_id": row.get("numeric_rollup_row_id"),
        "numeric_rollup_surface": row.get("numeric_rollup_surface"),
        "rollup_key": row.get("rollup_key"),
        "rollup_type": row.get("rollup_type"),
        "row_count": row.get("row_count"),
        "proxy_r_mean": row.get("proxy_r_mean"),
        "proxy_r_min": row.get("proxy_r_min"),
        "proxy_r_max": row.get("proxy_r_max"),
        "numeric_proxy_r_count": row.get("numeric_proxy_r_count"),
        "expectancy_proxy_count": row.get("expectancy_proxy_count"),
        "source_decision_counts": row.get("decision_counts"),
        "source_proxy_r_class_counts": row.get("proxy_r_class_counts"),
        "source_target_stop_order_counts": row.get("target_stop_order_counts"),
        "source_exact_r_status_counts": row.get("exact_r_status_counts"),
        "input_integrated_result_execution_row_id": row.get(
            "input_integrated_result_execution_row_id"
        ),
        "exact_missing_field_proof": row.get("exact_missing_field_proof"),
        "branch_match_status": row.get("branch_match_status"),
        "sidecar_source_row_joined": row.get("sidecar_source_row_joined"),
        "matched_branch_queue_id": row.get("matched_branch_queue_id"),
        "computed_decision": row.get("computed_decision"),
        "keep_kill_redesign_implement_decision": row.get(
            "keep_kill_redesign_implement_decision"
        ),
        "exact_r_status": row.get("exact_r_status"),
        "proxy_r_status": row.get("proxy_r_status"),
        "cost_stress_status": row.get("cost_stress_status"),
        "repair_implementation_action": row.get("repair_implementation_action"),
        "source_geometry_repair_runtime_ready": row.get("source_geometry_repair_runtime_ready"),
        "mechanical_scope_key": row.get("mechanical_scope_key"),
        "metrics": {
            metric: _metric_trace(row, metric)
            for metric in METRIC_NAMES
            if _metric_trace(row, metric)
        },
    }


def _row_dimension_value(row: dict[str, Any], field: str) -> str:
    scope = _row_scope(row)
    if field == "route_family":
        route_family = (
            row.get("route_family")
            or scope.get("route_family")
            or _route_family_for_framework(row.get("framework") or scope.get("framework"))
        )
        return _normalized(route_family)
    if field in MATCH_FIELDS:
        return _normalized(row.get(field) or scope.get(field))
    return _normalized(row.get(field))


def _dimension_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    values = sorted({_row_dimension_value(row, field) for row in rows if _row_dimension_value(row, field)})
    return {
        value: sum(1 for row in rows if _row_dimension_value(row, field) == value)
        for value in values
    }


def _dimension_row_count_sums(rows: list[dict[str, Any]], field: str) -> dict[str, float | int]:
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        value = _row_dimension_value(row, field)
        if not value:
            continue
        count = _to_float(row.get("row_count"))
        totals[value] += count if count is not None else 1.0
    result: dict[str, float | int] = {}
    for key, value in sorted(totals.items()):
        result[key] = int(value) if float(value).is_integer() else round(value, 12)
    return result


def _recommendation_component_decision_group_row_counts(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, float | int]]:
    grouped: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in rows:
        component = _row_dimension_value(row, "source_component")
        if not component:
            continue
        row_group_counts = row.get("recommendation_scope_rollup_decision_group_row_counts")
        if isinstance(row_group_counts, dict) and row_group_counts:
            for decision_group, count in row_group_counts.items():
                decision_group = _normalized(decision_group)
                numeric = _to_float(count)
                if decision_group and numeric is not None:
                    grouped[component][decision_group] += numeric
            continue
        decision_group = _normalized(row.get("recommendation_decision_group"))
        if not decision_group:
            continue
        count = _to_float(row.get("row_count"))
        grouped[component][decision_group] += count if count is not None else 1.0
    result: dict[str, dict[str, float | int]] = {}
    for component, counts in sorted(grouped.items()):
        result[component] = {
            group: int(value) if float(value).is_integer() else round(value, 12)
            for group, value in sorted(counts.items())
        }
    return result


def _dimension_decision_counts(
    rows: list[dict[str, Any]],
    field: str,
    cfg: dict[str, Any] | None,
) -> dict[str, dict[str, int]]:
    values = sorted({_row_dimension_value(row, field) for row in rows if _row_dimension_value(row, field)})
    result: dict[str, dict[str, int]] = {}
    for value in values:
        counts = {"FOLLOW": 0, "AVOID": 0, "MIXED": 0}
        for row in rows:
            if _row_dimension_value(row, field) != value:
                continue
            counts[_decision_from_row(row, cfg)] += 1
        result[value] = {label: count for label, count in counts.items() if count}
    return result


def _dimension_decision_metric_summaries(
    rows: list[dict[str, Any]],
    field: str,
    cfg: dict[str, Any] | None,
) -> dict[str, dict[str, dict[str, float]]]:
    values = sorted({_row_dimension_value(row, field) for row in rows if _row_dimension_value(row, field)})
    result: dict[str, dict[str, dict[str, float]]] = {}
    for value in values:
        by_decision: dict[str, dict[str, float]] = {}
        for row in rows:
            if _row_dimension_value(row, field) != value:
                continue
            decision = _decision_from_row(row, cfg)
            summary = by_decision.setdefault(decision, {"rows": 0.0})
            summary["rows"] += 1.0
            for metric in METRIC_NAMES:
                metric_value = _metric_sum(row, metric)
                if metric_value is None:
                    continue
                summary[metric] = summary.get(metric, 0.0) + metric_value
        result[value] = by_decision
    return result


def _row_drill_through_path(row: dict[str, Any]) -> str:
    return _normalized(
        row.get("drill_through_path")
        or row.get("declared_origin_artifact")
        or row.get("source_path")
        or row.get("source_artifact")
    )


def _limit_sequence(items: list[Any], limit: int) -> tuple[list[Any], bool]:
    if limit < 0:
        return items, False
    return items[:limit], len(items) > limit


def _failure_intelligence_guard_summary(
    rows: list[dict[str, Any]],
    cfg: dict[str, Any] | None,
) -> dict[str, Any]:
    infos = [_failure_intelligence_guard_info(row, cfg) for row in rows]
    guarded_infos = [info for info in infos if info["guarded"]]
    non_executable_tokens = Counter(
        token
        for info in guarded_infos
        for token in info.get("non_executable_tokens", [])
    )
    executable_avoid_tokens = Counter(
        token
        for info in infos
        for token in info.get("executable_avoid_tokens", [])
    )
    return {
        "enabled": bool((cfg or {}).get("failure_intelligence_guard_enabled", True)),
        "non_executable_rows": len(guarded_infos),
        "runtime_executable_rows": len(rows) - len(guarded_infos),
        "source_incomplete_flag_rows": sum(
            1 for info in infos if info.get("source_complete_flag_false")
        ),
        "non_executable_token_counts": dict(sorted(non_executable_tokens.items())),
        "executable_avoid_token_counts": dict(sorted(executable_avoid_tokens.items())),
    }


def _orderflow_diagnostic_guard_summary(
    rows: list[dict[str, Any]],
    cfg: dict[str, Any] | None,
) -> dict[str, Any]:
    infos = [_orderflow_diagnostic_guard_info(row, cfg) for row in rows]
    guarded_infos = [info for info in infos if info["guarded"]]
    orderflow_tokens = Counter(
        token
        for info in infos
        for token in info.get("orderflow_tokens", [])
    )
    ready_tokens = Counter(
        token
        for info in infos
        for token in info.get("ready_tokens", [])
    )
    return {
        "enabled": bool((cfg or {}).get("orderflow_diagnostic_guard_enabled", True)),
        "diagnostic_only_rows": len(guarded_infos),
        "runtime_executable_rows": len(rows) - len(guarded_infos),
        "orderflow_token_counts": dict(sorted(orderflow_tokens.items())),
        "ready_token_counts": dict(sorted(ready_tokens.items())),
        "runtime_validated_rows": sum(
            1 for info in infos if info.get("runtime_validated") and info.get("orderflow_tokens")
        ),
    }


def _aggregate_evidence(
    rows: list[dict[str, Any]],
    *,
    row_detail_limit: int = DEFAULT_EVIDENCE_ROW_DETAIL_LIMIT,
    id_list_limit: int = DEFAULT_EVIDENCE_ID_LIST_LIMIT,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decisions = [_decision_from_row(row, cfg) for row in rows]
    decision_counts = {label: decisions.count(label) for label in ("FOLLOW", "AVOID", "MIXED")}
    dimension_counts = {
        field: counts
        for field in EVIDENCE_DIMENSION_FIELDS
        if (counts := _dimension_counts(rows, field))
    }
    matched_row_ids = [
        row.get("review_row_id")
        or row.get("vnext_matrix_row_id")
        or row.get("event_scope_rollup_row_id")
        or row.get("registry_catalog_row_id")
        or row.get("ai_narrowing_policy_row_id")
        or row.get("ai_narrowing_capacity_blocklist_row_id")
        or row.get("numeric_router_catalog_runtime_row_id")
        or row.get("survivor_failure_runtime_row_id")
        or row.get("branch_ambiguity_collapse_runtime_row_id")
        or row.get("branch_followup_computation_runtime_row_id")
        or row.get("adverse_stop_first_execution_runtime_row_id")
        or row.get("gate_selector_session_timeframe_runtime_row_id")
        or row.get("sierra_depth_source_acquisition_runtime_row_id")
        or row.get("source_repair_missing_denominator_runtime_row_id")
        or row.get("nr_source_repair_execution_identity_runtime_row_id")
        or row.get("ai_narrowing_default_off_runtime_row_id")
        or row.get("ai_decision_trace_routing_guard_runtime_row_id")
        or row.get("pre_ai_post_l2_routing_policy_runtime_row_id")
        or row.get("rejected_candidate_l2_value_mining_runtime_row_id")
        or row.get("accepted_candidate_m1_fill_source_repair_runtime_row_id")
        or row.get("trade_record_execution_lifecycle_runtime_row_id")
        or row.get("nofill_pending_lifecycle_runtime_row_id")
        or row.get("scid_forward_source_capture_runtime_row_id")
        or row.get("source_geometry_runtime_row_id")
        or row.get("source_geometry_repair_row_id")
        or row.get("legacy_ai_cascade_model_runtime_row_id")
        or row.get("legacy_v2_v3_paper_live_friction_runtime_row_id")
        or row.get("sl_beyond_ob_outcome_join_source_repair_runtime_row_id")
        or row.get("fvg_trade_record_bounds_execution_runtime_row_id")
        or row.get("scid_target_horizon_control_runtime_row_id")
        or row.get("main_orch24_structural_repair_action_runtime_row_id")
        or row.get("main_orch24_action_completeness_residual_r_runtime_row_id")
        or row.get("main_orch24_implementation_selection_runtime_row_id")
        or row.get("main_orch24_snapshot_dependency_repair_runtime_row_id")
        or row.get("main_orch48_final_review_selector_runtime_row_id")
        or row.get("ltf_path_geometry_source_runtime_row_id")
        or row.get("instrument_expansion_market_session_runtime_row_id")
        or row.get("scid_combined_source_capture_poi_bounds_runtime_row_id")
        or row.get("frontier_action_id")
        or row.get("recommendation_unified_candidate_id")
        or row.get("recommendation_scope_rollup_id")
        or row.get("recommendation_family_rollup_id")
        or row.get("bucket_id")
        or row.get("numeric_result_row_id")
        or row.get("row_key")
        or ""
        for row in rows
    ]
    source_row_ids = [
        row.get("source_row_id") or ""
        for row in rows
        if row.get("source_row_id")
    ]
    numeric_confluence_enabled = bool(cfg.get("numeric_confluence_enabled", True))
    numeric_confluence_schema_version = str(
        cfg.get("numeric_confluence_schema_version") or ""
    )
    numeric_confluence_sources = []
    if numeric_confluence_enabled:
        numeric_confluence_sources = [
            build_numeric_confluence_source(
                row,
                decision=_decision_from_row(row, cfg),
                cfg=cfg,
            )
            for row in rows
        ]
    limited_matched_row_ids, matched_row_ids_truncated = _limit_sequence(matched_row_ids, id_list_limit)
    limited_source_row_ids, source_row_ids_truncated = _limit_sequence(source_row_ids, id_list_limit)
    evidence_rows = [_evidence_row(row, cfg) for row in rows]
    limited_rows, row_details_truncated = _limit_sequence(evidence_rows, row_detail_limit)
    return {
        "matched_rows": len(rows),
        "decision_counts": {key: value for key, value in decision_counts.items() if value},
        "numeric_confluence": {
            **summarize_numeric_confluence_sources(numeric_confluence_sources),
            "enabled": numeric_confluence_enabled,
            "configured_schema_version": numeric_confluence_schema_version,
        },
        "failure_intelligence_guard": _failure_intelligence_guard_summary(rows, cfg),
        "orderflow_diagnostic_guard": _orderflow_diagnostic_guard_summary(rows, cfg),
        "max_scope_fields": max((len(_row_scope(row)) for row in rows), default=0),
        "scope_selection_policy": _scope_selection_policy(cfg),
        "scope_required_anchor_groups": [
            list(group) for group in _scope_required_anchor_groups(cfg)
        ],
        "source_event_rows": sum(int(row.get("source_event_rows") or 0) for row in rows),
        "source_weighted_registry_match_rows": sum(
            int(row.get("source_weighted_registry_match_rows") or row.get("registry_match_rows") or 0)
            for row in rows
        ),
        "unique_scope_registry_match_rows": sum(
            int(row.get("unique_scope_registry_match_rows") or 1) for row in rows
        ),
        "review_pressure": round(
            sum(_to_float(row.get("review_pressure")) or 0.0 for row in rows),
            12,
        ),
        "metrics": {
            metric: _aggregate_metric(rows, metric)
            for metric in METRIC_NAMES
        },
        "source_paths": sorted(
            {
                str(row.get("source_path") or row.get("source_artifact") or "")
                for row in rows
                if row.get("source_path") or row.get("source_artifact")
            }
        ),
        "drill_through_paths": sorted(
            {
                path
                for row in rows
                if (path := _row_drill_through_path(row))
            }
        ),
        "matched_row_ids": limited_matched_row_ids,
        "matched_row_id_count": len(matched_row_ids),
        "matched_row_ids_truncated": matched_row_ids_truncated,
        "source_row_ids": limited_source_row_ids,
        "source_row_id_count": len(source_row_ids),
        "source_row_ids_truncated": source_row_ids_truncated,
        "row_detail_limit": row_detail_limit,
        "row_detail_count": len(limited_rows),
        "row_details_truncated": row_details_truncated,
        "dimension_counts": dimension_counts,
        "symbol_counts": dimension_counts.get("symbol", {}),
        "source_symbol_counts": dimension_counts.get("source_symbol", {}),
        "symbol_family_counts": dimension_counts.get("symbol_family", {}),
        "market_counts": dimension_counts.get("market", {}),
        "timeframe_counts": dimension_counts.get("timeframe", {}),
        "framework_counts": dimension_counts.get("framework", {}),
        "route_family_counts": dimension_counts.get("route_family", {}),
        "market_timeframe_counts": dimension_counts.get("market_timeframe", {}),
        "route_session_counts": dimension_counts.get("route_session", {}),
        "horizon_id_counts": dimension_counts.get("horizon_id", {}),
        "side_counts": dimension_counts.get("side", {}),
        "entry_variant_counts": dimension_counts.get("entry_variant", {}),
        "positive_result_class_counts": dimension_counts.get("positive_result_class", {}),
        "source_result_class_counts": dimension_counts.get("source_result_class", {}),
        "rejected_repair_class_counts": dimension_counts.get("rejected_repair_class", {}),
        "source_name_counts": {
            name: sum(1 for row in rows if row.get("source_name") == name)
            for name in sorted({row.get("source_name") for row in rows if row.get("source_name")})
        },
        "evidence_family_counts": {
            name: sum(1 for row in rows if row.get("evidence_family") == name)
            for name in sorted({row.get("evidence_family") for row in rows if row.get("evidence_family")})
        },
        "source_component_counts": dimension_counts.get("source_component", {}),
        "action_family_counts": dimension_counts.get("action_family", {}),
        "action_class_counts": dimension_counts.get("action_class", {}),
        "proxy_r_class_counts": dimension_counts.get("proxy_r_class", {}),
        "target_stop_order_class_counts": dimension_counts.get("target_stop_order_class", {}),
        "r_evidence_class_counts": dimension_counts.get("r_evidence_class", {}),
        "implementation_action_counts": dimension_counts.get("implementation_action", {}),
        "source_group_counts": dimension_counts.get("source_group", {}),
        "source_role_counts": dimension_counts.get("source_role", {}),
        "system_surface_counts": dimension_counts.get("system_surface", {}),
        "recommendation_bucket_family_counts": _dimension_counts(
            rows,
            "recommendation_bucket_family",
        ),
        "recommendation_family_rollup_type_counts": _dimension_counts(
            rows,
            "recommendation_family_rollup_type",
        ),
        "recommendation_unified_candidate_primitive_counts": _dimension_counts(
            rows,
            "recommendation_unified_candidate_primitive",
        ),
        "recommendation_scope_rollup_type_counts": _dimension_counts(
            rows,
            "recommendation_scope_rollup_type",
        ),
        "recommendation_scope_rollup_primitive_counts": _dimension_counts(
            rows,
            "recommendation_scope_rollup_primitive",
        ),
        "recommendation_decision_group_counts": _dimension_counts(
            rows,
            "recommendation_decision_group",
        ),
        "recommendation_bucket_family_row_counts": _dimension_row_count_sums(
            rows,
            "recommendation_bucket_family",
        ),
        "recommendation_decision_group_row_counts": _dimension_row_count_sums(
            rows,
            "recommendation_decision_group",
        ),
        "recommendation_family_rollup_type_row_counts": _dimension_row_count_sums(
            rows,
            "recommendation_family_rollup_type",
        ),
        "recommendation_scope_rollup_type_row_counts": _dimension_row_count_sums(
            rows,
            "recommendation_scope_rollup_type",
        ),
        "recommendation_scope_rollup_primitive_row_counts": _dimension_row_count_sums(
            rows,
            "recommendation_scope_rollup_primitive",
        ),
        "recommendation_component_decision_group_row_counts": (
            _recommendation_component_decision_group_row_counts(rows)
        ),
        "route_family_inferred_from_counts": dimension_counts.get("route_family_inferred_from", {}),
        "route_family_decision_counts": _dimension_decision_counts(rows, "route_family", cfg),
        "source_component_decision_counts": _dimension_decision_counts(rows, "source_component", cfg),
        "action_class_decision_counts": _dimension_decision_counts(rows, "action_class", cfg),
        "evidence_family_decision_counts": _dimension_decision_counts(rows, "evidence_family", cfg),
        "source_name_decision_counts": _dimension_decision_counts(rows, "source_name", cfg),
        "source_role_decision_counts": _dimension_decision_counts(rows, "source_role", cfg),
        "framework_decision_metric_summaries": _dimension_decision_metric_summaries(
            rows,
            "framework",
            cfg,
        ),
        "rows": limited_rows,
    }


@dataclass(frozen=True)
class GTOSVNextRuntimeDecision:
    """Runtime vNext decision plus evidence payload."""

    decision: DecisionLabel
    event: dict[str, str]
    enabled: bool
    apply_to_execution: bool
    matched: bool
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)
    artifact_paths: tuple[str, ...] = field(default_factory=tuple)

    def to_record(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "enabled": self.enabled,
            "apply_to_execution": self.apply_to_execution,
            "matched": self.matched,
            "reason": self.reason,
            "event": dict(self.event),
            "artifact_paths": list(self.artifact_paths),
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class GTOSVNextMoonshotDynamicExecutionDecision:
    """Moonshot dynamic-execution router decision attached to runtime records."""

    enabled: bool
    apply_to_execution: bool
    applied: bool
    decision_status: str
    candidate_action: str
    selected_branch: str
    selected_policy: str | None
    replaced_policy: str
    fixed_target_role: str
    prop_action: str
    ai_role: str
    source_quality_action: str
    exit_management_action: str
    refusal_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_notes: tuple[str, ...] = field(default_factory=tuple)
    runtime_effect_now: bool = False
    candidate_use_allowed_now: bool = False
    source_event: dict[str, Any] = field(default_factory=dict)
    router_record: dict[str, Any] = field(default_factory=dict)
    target_stop_geometry_v4: dict[str, Any] = field(default_factory=dict)
    execution_policy_id: str | None = None

    def to_record(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "apply_to_execution": self.apply_to_execution,
            "applied": self.applied,
            "decision_status": self.decision_status,
            "candidate_action": self.candidate_action,
            "selected_branch": self.selected_branch,
            "selected_policy": self.selected_policy,
            "execution_policy_id": self.execution_policy_id,
            "replaced_policy": self.replaced_policy,
            "fixed_target_role": self.fixed_target_role,
            "prop_action": self.prop_action,
            "ai_role": self.ai_role,
            "source_quality_action": self.source_quality_action,
            "exit_management_action": self.exit_management_action,
            "refusal_reasons": list(self.refusal_reasons),
            "evidence_notes": list(self.evidence_notes),
            "runtime_effect_now": self.runtime_effect_now,
            "candidate_use_allowed_now": self.candidate_use_allowed_now,
            "source_event": dict(self.source_event),
            "router_record": dict(self.router_record),
            "target_stop_geometry_v4": dict(self.target_stop_geometry_v4),
        }


@dataclass(frozen=True)
class GTOSVNextReplacementMonitoringSnapshot:
    """Log-only replacement activation monitor snapshot.

    The snapshot is intentionally observational. It records the state that the
    semantic verifier and operations checklist need without changing routing,
    sizing, order placement, or AI-call behavior.
    """

    phase: str
    symbol: str
    kill_zone: str
    candle_time_utc: str | None
    vnext_apply_status: dict[str, Any]
    router_decision: dict[str, Any]
    label_effects: dict[str, Any]
    execution_effects: dict[str, Any]
    dynamic_exit_transition: dict[str, Any]
    ltf_pending_monitor_health: dict[str, Any]
    prop_budget_projection: dict[str, Any]
    source_capture_completeness: dict[str, Any]
    old_live_fallback_leakage: dict[str, Any]
    ai_malformed_monitoring: dict[str, Any]
    ml_assistant_roles: dict[str, Any]
    warnings: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = "gtos_vnext_replacement_monitoring_v1"

    def to_record(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "phase": self.phase,
            "symbol": self.symbol,
            "kill_zone": self.kill_zone,
            "candle_time_utc": self.candle_time_utc,
            "vnext_apply_status": dict(self.vnext_apply_status),
            "router_decision": dict(self.router_decision),
            "label_effects": dict(self.label_effects),
            "execution_effects": dict(self.execution_effects),
            "dynamic_exit_transition": dict(self.dynamic_exit_transition),
            "ltf_pending_monitor_health": dict(self.ltf_pending_monitor_health),
            "prop_budget_projection": dict(self.prop_budget_projection),
            "source_capture_completeness": dict(self.source_capture_completeness),
            "old_live_fallback_leakage": dict(self.old_live_fallback_leakage),
            "ai_malformed_monitoring": dict(self.ai_malformed_monitoring),
            "ml_assistant_roles": dict(self.ml_assistant_roles),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class GTOSVNextPreAIRoutingDecision:
    """Pre-AI vNext route decision built from non-AI event fields."""

    action: PreAIAction
    decision: DecisionLabel
    enabled: bool
    apply_to_ai_call: bool
    reason: str
    event: dict[str, str]
    recommended_side: str | None = None
    recommended_frameworks: tuple[str, ...] = field(default_factory=tuple)
    recommended_route_families: tuple[str, ...] = field(default_factory=tuple)
    blocked_sides: tuple[str, ...] = field(default_factory=tuple)
    blocked_frameworks: tuple[str, ...] = field(default_factory=tuple)
    blocked_route_families: tuple[str, ...] = field(default_factory=tuple)
    risk_vetoed_sides: tuple[str, ...] = field(default_factory=tuple)
    side_risk_reasons: dict[str, str] = field(default_factory=dict)
    evaluated_sides: tuple[str, ...] = field(default_factory=tuple)
    would_action: PreAIAction = "ALLOW_AI"
    side_decisions: tuple[GTOSVNextRuntimeDecision, ...] = field(default_factory=tuple)
    ai_role_context: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "decision": self.decision,
            "enabled": self.enabled,
            "apply_to_ai_call": self.apply_to_ai_call,
            "reason": self.reason,
            "event": dict(self.event),
            "recommended_side": self.recommended_side,
            "recommended_frameworks": list(self.recommended_frameworks),
            "recommended_route_families": list(self.recommended_route_families),
            "blocked_sides": list(self.blocked_sides),
            "blocked_frameworks": list(self.blocked_frameworks),
            "blocked_route_families": list(self.blocked_route_families),
            "risk_vetoed_sides": list(self.risk_vetoed_sides),
            "side_risk_reasons": dict(self.side_risk_reasons),
            "evaluated_sides": list(self.evaluated_sides),
            "would_action": self.would_action,
            "side_decisions": [decision.to_record() for decision in self.side_decisions],
            "ai_role_context": dict(self.ai_role_context),
        }


@dataclass(frozen=True)
class GTOSVNextAIPolicyDecision:
    """Mechanical-first policy for whether and how vNext uses the AI layer."""

    action: AIPolicyAction
    would_action: AIPolicyAction
    allowed: bool
    would_allow_ai_call: bool
    enabled: bool
    apply_to_ai_call: bool
    reason: str
    ai_role: str
    prompt_scope: dict[str, Any] = field(default_factory=dict)
    schema_contract: dict[str, Any] = field(default_factory=dict)
    cache_contract: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "would_action": self.would_action,
            "allowed": self.allowed,
            "would_allow_ai_call": self.would_allow_ai_call,
            "enabled": self.enabled,
            "apply_to_ai_call": self.apply_to_ai_call,
            "reason": self.reason,
            "ai_role": self.ai_role,
            "prompt_scope": dict(self.prompt_scope),
            "schema_contract": dict(self.schema_contract),
            "cache_contract": dict(self.cache_contract),
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class GTOSVNextRiskAdjustment:
    """Evidence-backed vNext risk multiplier decision."""

    enabled: bool
    apply_to_execution: bool
    applied: bool
    decision: DecisionLabel
    before_risk_pct: float
    after_risk_pct: float
    multiplier: float
    would_multiplier: float
    reason: str
    evidence_summary: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "apply_to_execution": self.apply_to_execution,
            "applied": self.applied,
            "decision": self.decision,
            "before_risk_pct": self.before_risk_pct,
            "after_risk_pct": self.after_risk_pct,
            "multiplier": self.multiplier,
            "would_multiplier": self.would_multiplier,
            "reason": self.reason,
            "evidence_summary": self.evidence_summary,
        }


@dataclass(frozen=True)
class GTOSVNextGateOverride:
    """Evidence-backed vNext override for an existing runtime gate."""

    gate: str
    enabled: bool
    apply_to_execution: bool
    applied: bool
    would_apply: bool
    decision: DecisionLabel
    reason: str
    evidence_summary: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "gate": self.gate,
            "enabled": self.enabled,
            "apply_to_execution": self.apply_to_execution,
            "applied": self.applied,
            "would_apply": self.would_apply,
            "decision": self.decision,
            "reason": self.reason,
            "evidence_summary": self.evidence_summary,
        }


@dataclass(frozen=True)
class GTOSVNextPendingPolicy:
    """Evidence-backed vNext pending-limit policy decision."""

    action: PendingPolicyAction
    would_action: PendingPolicyAction
    enabled: bool
    apply_to_execution: bool
    applied: bool
    decision: DecisionLabel
    reason: str
    evidence_summary: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "would_action": self.would_action,
            "enabled": self.enabled,
            "apply_to_execution": self.apply_to_execution,
            "applied": self.applied,
            "decision": self.decision,
            "reason": self.reason,
            "evidence_summary": self.evidence_summary,
        }


@dataclass(frozen=True)
class GTOSVNextLTFPathExecutionDecision:
    """Replay-backed lower-timeframe path execution decision.

    The decision is a scheduler/entry control surface. It does not place orders
    by itself; orchestrator/execution code consumes it only when both the global
    vNext execution gate and the Stage06 apply flag are enabled.
    """

    action: LTFPathExecutionAction
    would_action: LTFPathExecutionAction
    enabled: bool
    apply_to_execution: bool
    applied: bool
    decision: DecisionLabel
    reason: str
    monitor_timeframe: str | None = None
    replay_mode: str | None = None
    adjusted_entry_price: float | None = None
    evidence_summary: dict[str, Any] = field(default_factory=dict)
    path_state: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "would_action": self.would_action,
            "enabled": self.enabled,
            "apply_to_execution": self.apply_to_execution,
            "applied": self.applied,
            "decision": self.decision,
            "reason": self.reason,
            "monitor_timeframe": self.monitor_timeframe,
            "replay_mode": self.replay_mode,
            "adjusted_entry_price": self.adjusted_entry_price,
            "evidence_summary": self.evidence_summary,
            "path_state": self.path_state,
        }


@dataclass(frozen=True)
class GTOSVNextPropSafeSelectorDecision:
    """redacted_account-style prop budget selector decision.

    The selector is budget governance only. It never places orders and only
    changes execution when both the global vNext execution gate and the selector
    apply flag are enabled.
    """

    action: PropSafeSelectorAction
    would_action: PropSafeSelectorAction
    enabled: bool
    apply_to_execution: bool
    applied: bool
    decision: DecisionLabel
    before_risk_pct: float
    after_risk_pct: float
    max_allowed_new_trade_risk_pct: float
    reason: str
    reset_window: dict[str, Any] = field(default_factory=dict)
    external_rule_projection: dict[str, Any] = field(default_factory=dict)
    internal_overlay_projection: dict[str, Any] = field(default_factory=dict)
    exposure_breakdown: dict[str, Any] = field(default_factory=dict)
    concentration: dict[str, Any] = field(default_factory=dict)
    route_quality: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        missing_fields: list[str] = []
        if self.reason == "prop_safe_selector_missing_account_state":
            missing_fields.extend(["initial_balance_or_config", "current_equity"])
        if self.reason == "prop_safe_selector_missing_day_start_baseline":
            missing_fields.extend(
                [
                    "day_start_equity_or_balance_baseline",
                    "day_start_equity",
                    "day_start_balance",
                ]
            )
        if self.reason == "prop_safe_selector_unverified_open_position_risk":
            missing_fields.append("broker_order_calc_profit_cash_risk_for_all_open_positions")
        source_status = "source_bound_risk_packet_complete"
        if missing_fields:
            source_status = "source_gap_fail_closed"
        elif self.would_action in {"BLOCK", "DEFER_UNTIL_RESET", "REDUCE_RISK"}:
            source_status = "source_bound_risk_packet_binding_budget"
        record = {
            "action": self.action,
            "would_action": self.would_action,
            "enabled": self.enabled,
            "apply_to_execution": self.apply_to_execution,
            "applied": self.applied,
            "decision": self.decision,
            "before_risk_pct": self.before_risk_pct,
            "after_risk_pct": self.after_risk_pct,
            "max_allowed_new_trade_risk_pct": self.max_allowed_new_trade_risk_pct,
            "reason": self.reason,
            "reset_window": self.reset_window,
            "external_rule_projection": self.external_rule_projection,
            "internal_overlay_projection": self.internal_overlay_projection,
            "exposure_breakdown": self.exposure_breakdown,
            "concentration": self.concentration,
            "route_quality": self.route_quality,
        }
        record["risk_packet_source_status"] = source_status
        record["risk_packet_missing_fields"] = missing_fields
        record["risk_packet_field_groups"] = {
            "account_state": {
                "status": "source_gap" if missing_fields else "source_bound",
                "external_rule_projection_keys": sorted(self.external_rule_projection),
            },
            "exposure_headroom": {
                "status": "source_bound",
                "exposure_keys": sorted(self.exposure_breakdown),
            },
            "daily_and_overall_budget": {
                "status": "source_bound",
                "binding_budget_name": self.external_rule_projection.get(
                    "binding_budget_name"
                ),
                "max_allowed_new_trade_risk_pct": (
                    self.max_allowed_new_trade_risk_pct
                ),
            },
        }
        record["risk_packet_hash_sha256"] = _stable_sha256(record)
        return record


@dataclass(frozen=True)
class GTOSVNextExitPolicyDecision:
    """Evidence-backed vNext exit-management policy context."""

    action: ExitPolicyAction
    would_action: ExitPolicyAction
    enabled: bool
    apply_to_execution: bool
    applied: bool
    decision: DecisionLabel
    reason: str
    event: dict[str, str]
    evidence_summary: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "would_action": self.would_action,
            "enabled": self.enabled,
            "apply_to_execution": self.apply_to_execution,
            "applied": self.applied,
            "decision": self.decision,
            "reason": self.reason,
            "event": dict(self.event),
            "evidence_summary": self.evidence_summary,
        }


@dataclass(frozen=True)
class GTOSVNextReady8ControlPolicyDecision:
    """Evidence-backed READY8 failure/control residue policy context."""

    action: Ready8ControlPolicyAction
    would_action: Ready8ControlPolicyAction
    enabled: bool
    apply_to_execution: bool
    applied: bool
    decision: DecisionLabel
    reason: str
    event: dict[str, str]
    evidence_summary: dict[str, Any] = field(default_factory=dict)

    def to_record(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "would_action": self.would_action,
            "enabled": self.enabled,
            "apply_to_execution": self.apply_to_execution,
            "applied": self.applied,
            "decision": self.decision,
            "reason": self.reason,
            "event": dict(self.event),
            "evidence_summary": self.evidence_summary,
        }


def _final_decision(rows: list[dict[str, Any]], cfg: dict[str, Any] | None = None) -> DecisionLabel:
    if not rows:
        return "LEGACY"
    labels = {_decision_from_row(row, cfg) for row in rows}
    if labels == {"FOLLOW"}:
        return "FOLLOW"
    if labels == {"AVOID"}:
        return "AVOID"
    return "MIXED"


def _decision_counts(rows: list[dict[str, Any]], cfg: dict[str, Any] | None = None) -> dict[str, int]:
    decisions = [_decision_from_row(row, cfg) for row in rows]
    return {
        label: decisions.count(label)
        for label in ("FOLLOW", "AVOID", "MIXED")
        if decisions.count(label)
    }


def _weighted_pressure_components(row: dict[str, Any], cfg: dict[str, Any]) -> dict[str, float]:
    if _failure_intelligence_guard_info(row, cfg)["guarded"]:
        return {}
    if _orderflow_diagnostic_guard_info(row, cfg)["guarded"]:
        return {}

    weights = {
        "cost_adjusted_simulated_r": _configured_float(cfg, "conflict_cost_adjusted_r_weight", 1.0),
        "stress_simulated_r": _configured_float(cfg, "conflict_stress_r_weight", 0.25),
        "proxy_score": _configured_float(cfg, "conflict_proxy_score_weight", 1.0),
    }
    components: dict[str, float] = {}
    for metric, weight in weights.items():
        value = _metric_sum(row, metric)
        if value is not None:
            components[metric] = float(value) * weight
    return components


def _evidence_weighted_conflict_resolution(
    rows: list[dict[str, Any]],
    cfg: dict[str, Any],
    fallback: DecisionLabel,
) -> tuple[DecisionLabel, dict[str, Any]]:
    follow_pressure = 0.0
    avoid_pressure = 0.0
    scored_rows = 0
    row_scores: list[dict[str, Any]] = []
    effective_n_sum = 0.0

    for row in rows:
        components = _weighted_pressure_components(row, cfg)
        score = sum(components.values())
        effective_n = _metric_sum(row, "effective_n")
        if effective_n is not None:
            effective_n_sum += effective_n
        if components:
            scored_rows += 1
            if score > 0:
                follow_pressure += score
            elif score < 0:
                avoid_pressure += abs(score)
        row_scores.append({
            "row_id": (
                row.get("review_row_id")
                or row.get("vnext_matrix_row_id")
                or row.get("event_scope_rollup_row_id")
                or row.get("sierra_depth_source_acquisition_runtime_row_id")
                or row.get("source_repair_missing_denominator_runtime_row_id")
                or row.get("nr_source_repair_execution_identity_runtime_row_id")
                or row.get("legacy_ai_cascade_model_runtime_row_id")
                or row.get("legacy_v2_v3_paper_live_friction_runtime_row_id")
                or row.get("sl_beyond_ob_outcome_join_source_repair_runtime_row_id")
                or row.get("fvg_trade_record_bounds_execution_runtime_row_id")
                or row.get("main_orch24_structural_repair_action_runtime_row_id")
                or row.get("main_orch24_action_completeness_residual_r_runtime_row_id")
                or row.get("main_orch24_implementation_selection_runtime_row_id")
                or row.get("main_orch24_snapshot_dependency_repair_runtime_row_id")
                or row.get("main_orch48_final_review_selector_runtime_row_id")
                or row.get("ltf_path_geometry_source_runtime_row_id")
                or row.get("instrument_expansion_market_session_runtime_row_id")
                or row.get("ai_narrowing_default_off_runtime_row_id")
                or row.get("ai_decision_trace_routing_guard_runtime_row_id")
                or row.get("pre_ai_post_l2_routing_policy_runtime_row_id")
                or row.get("rejected_candidate_l2_value_mining_runtime_row_id")
                or row.get("accepted_candidate_m1_fill_source_repair_runtime_row_id")
                or row.get("trade_record_execution_lifecycle_runtime_row_id")
                or row.get("nofill_pending_lifecycle_runtime_row_id")
                or row.get("source_geometry_runtime_row_id")
                or row.get("numeric_result_row_id")
                or row.get("frontier_action_id")
                or row.get("row_key")
                or ""
            ),
            "row_decision": _decision_from_row(row, cfg),
            "score": round(score, 12),
            "components": {key: round(value, 12) for key, value in components.items()},
            "effective_n": effective_n,
        })

    dominance_ratio = _configured_float(cfg, "conflict_pressure_dominance_ratio", 1.25)
    min_abs_pressure = _configured_float(cfg, "conflict_min_abs_pressure", 0.0)
    selected = fallback
    if scored_rows:
        if follow_pressure >= min_abs_pressure and follow_pressure >= avoid_pressure * dominance_ratio:
            selected = "FOLLOW"
        elif avoid_pressure >= min_abs_pressure and avoid_pressure >= follow_pressure * dominance_ratio:
            selected = "AVOID"

    evidence = {
        "mode": "evidence_weighted",
        "raw_decision_counts": _decision_counts(rows, cfg),
        "fallback_decision": fallback,
        "selected_decision": selected,
        "rows_scored": scored_rows,
        "follow_pressure": round(follow_pressure, 12),
        "avoid_pressure": round(avoid_pressure, 12),
        "dominance_ratio": dominance_ratio,
        "min_abs_pressure": min_abs_pressure,
        "effective_n_sum": round(effective_n_sum, 12),
        "row_scores": row_scores,
    }
    return selected, evidence


def _resolve_final_decision(
    rows: list[dict[str, Any]],
    cfg: dict[str, Any] | None = None,
) -> tuple[DecisionLabel, dict[str, Any]]:
    fallback = _final_decision(rows, cfg)
    mode = _normalized((cfg or {}).get("conflict_resolution") or "strict").casefold()
    if fallback != "MIXED" or mode not in {"evidence_weighted", "weighted"}:
        return fallback, {
            "mode": mode or "strict",
            "raw_decision_counts": _decision_counts(rows, cfg),
            "selected_decision": fallback,
        }
    return _evidence_weighted_conflict_resolution(rows, cfg or {}, fallback)


def evaluate_vnext_event(
    event: dict[str, Any],
    config: dict[str, Any] | None = None,
    *,
    artifact_rows: list[dict[str, Any]] | None = None,
    artifact_index: GTOSVNextEvidenceIndex | None = None,
) -> GTOSVNextRuntimeDecision:
    """Evaluate a normalized or raw candidate event against vNext artifacts."""
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    enabled = bool(cfg.get("enabled", False))
    apply_to_execution = bool(cfg.get("apply_to_execution", False))
    normalized_event = normalize_event(event)
    paths = _configured_artifact_paths(config)
    artifact_paths = tuple(str(path) for path in paths)
    bridge_evidence = _bridge_diagnostics_evidence(normalized_event, cfg)

    if not enabled:
        return GTOSVNextRuntimeDecision(
            decision="LEGACY",
            event=normalized_event,
            enabled=False,
            apply_to_execution=False,
            matched=False,
            reason="gtos_vnext_runtime_disabled",
            artifact_paths=artifact_paths,
            evidence=bridge_evidence,
        )

    if artifact_rows is not None:
        rows = artifact_rows
        scoped_matches = [
            row for row in rows
            if _scope_matches(_row_scope(row), normalized_event)
            and _row_matches_event_filters(row, normalized_event)
        ]
        runtime_index = None
    else:
        index = artifact_index or load_vnext_evidence_index(paths)
        artifact_paths = index.artifact_paths or artifact_paths
        runtime_index = index
        if _evidence_index_below_min_rows(index, cfg):
            return GTOSVNextRuntimeDecision(
                decision="LEGACY",
                event=normalized_event,
                enabled=True,
                apply_to_execution=apply_to_execution,
                matched=False,
                reason="vnext_evidence_index_below_min_loaded_rows",
                artifact_paths=artifact_paths,
                evidence={
                    **_evidence_index_denominator_evidence(index, cfg),
                    **bridge_evidence,
                },
            )
        scoped_matches = index.match_event(normalized_event, min_scope_fields=1)
    if not scoped_matches:
        return GTOSVNextRuntimeDecision(
            decision="LEGACY",
            event=normalized_event,
            enabled=True,
            apply_to_execution=apply_to_execution,
            matched=False,
            reason="no_matching_vnext_scope",
            artifact_paths=artifact_paths,
            evidence=bridge_evidence,
        )

    min_scope_fields = int(cfg.get("min_scope_fields", 1) or 1)
    selected = _select_runtime_rows(
        scoped_matches,
        cfg=cfg,
        min_scope_fields=min_scope_fields,
        normalized_event=normalized_event,
    )
    if not selected:
        return GTOSVNextRuntimeDecision(
            decision="LEGACY",
            event=normalized_event,
            enabled=True,
            apply_to_execution=apply_to_execution,
            matched=False,
            reason="matching_scope_below_min_scope_fields",
            artifact_paths=artifact_paths,
            evidence=bridge_evidence,
        )

    return _decision_from_selected_rows(
        selected_rows=selected,
        normalized_event=normalized_event,
        enabled=True,
        apply_to_execution=apply_to_execution,
        reason="matched_vnext_scope",
        artifact_paths=artifact_paths,
        runtime_index=runtime_index,
        cfg=cfg,
        bridge_diagnostics=bridge_evidence.get("bridge_diagnostics"),
    )


def evaluate_vnext_route_event(
    event: dict[str, Any],
    config: dict[str, Any] | None = None,
    *,
    artifact_rows: list[dict[str, Any]] | None = None,
    artifact_index: GTOSVNextEvidenceIndex | None = None,
) -> GTOSVNextRuntimeDecision:
    """Evaluate a post-L2 candidate across configured route variants."""
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    if not bool(cfg.get("post_l2_evaluate_route_variants", True)):
        return evaluate_vnext_event(
            event,
            config,
            artifact_rows=artifact_rows,
            artifact_index=artifact_index,
        )

    enabled = bool(cfg.get("enabled", False))
    apply_to_execution = bool(cfg.get("apply_to_execution", False))
    normalized_event = normalize_event(event)
    paths = _configured_artifact_paths(config)
    bridge_evidence = _bridge_diagnostics_evidence(normalized_event, cfg)
    if not enabled:
        return GTOSVNextRuntimeDecision(
            decision="LEGACY",
            event=normalized_event,
            enabled=False,
            apply_to_execution=False,
            matched=False,
            reason="gtos_vnext_runtime_disabled",
            artifact_paths=tuple(str(path) for path in paths),
            evidence=bridge_evidence,
        )

    runtime_index = _runtime_index_for_evaluation(
        config=config,
        artifact_rows=artifact_rows,
        artifact_index=artifact_index,
    )
    if _evidence_index_below_min_rows(runtime_index, cfg):
        return GTOSVNextRuntimeDecision(
            decision="LEGACY",
            event=normalized_event,
            enabled=True,
            apply_to_execution=apply_to_execution,
            matched=False,
            reason="vnext_evidence_index_below_min_loaded_rows",
            artifact_paths=runtime_index.artifact_paths,
            evidence={
                **_evidence_index_denominator_evidence(runtime_index, cfg),
                **bridge_evidence,
            },
        )
    min_scope_fields = int(cfg.get("min_scope_fields", 1) or 1)
    selected_rows: list[dict[str, Any]] = []
    candidate_framework = _normalized(
        event.get("effective_framework") or event.get("framework")
    )
    route_cfg = cfg
    if bool(cfg.get("post_l2_route_use_candidate_framework_only", True)) and candidate_framework:
        route_cfg = {**cfg, "post_l2_route_frameworks": [candidate_framework]}
    if (
        bool(cfg.get("post_l2_prune_route_variants_to_artifact_scopes", True))
        and bool(cfg.get("post_l2_match_artifact_scopes_directly", True))
    ):
        selected_rows, route_event_count = _artifact_scoped_route_selected_rows(
            event,
            cfg=route_cfg,
            prefix="post_l2",
            artifact_index=runtime_index,
            min_scope_fields=min_scope_fields,
        )
    else:
        route_events = _candidate_route_events(event, cfg=cfg, artifact_index=runtime_index)
        route_event_count = len(route_events)
        for route_event in route_events:
            normalized_route_event = normalize_event(route_event)
            matches = runtime_index.match_event(
                normalized_route_event,
                min_scope_fields=min_scope_fields,
            )
            if not matches:
                continue
            selected_rows.extend(
                _select_runtime_rows(
                    matches,
                    cfg=cfg,
                    min_scope_fields=min_scope_fields,
                    normalized_event=normalized_route_event,
                )
            )
    selected_rows = _dedupe_rows(selected_rows)
    if not selected_rows:
        return GTOSVNextRuntimeDecision(
            decision="LEGACY",
            event=normalized_event,
            enabled=True,
            apply_to_execution=apply_to_execution,
            matched=False,
            reason="no_matching_vnext_route_scope",
            artifact_paths=runtime_index.artifact_paths,
            evidence=bridge_evidence,
        )
    return _decision_from_selected_rows(
        selected_rows=selected_rows,
        normalized_event=normalized_event,
        enabled=True,
        apply_to_execution=apply_to_execution,
        reason="matched_vnext_route_scope",
        artifact_paths=runtime_index.artifact_paths,
        runtime_index=runtime_index,
        route_event_count=route_event_count,
        cfg=cfg,
        bridge_diagnostics=bridge_evidence.get("bridge_diagnostics"),
    )


def resolve_vnext_effective_framework(analysis: Any) -> tuple[str | None, bool, dict[str, Any]]:
    """Return the framework L2 would route for this AI output.

    The AI wrapper field can disagree with ``frameworks_evaluated`` under
    parallel framework evaluation. L2 verification already follows the
    qualified/effective route; vNext must consume the same framework or route
    evidence can attach to the wrong OB/FVG/breaker family.
    """
    wrapper = getattr(analysis, "framework", None)
    try:
        from src.components.verification import _compute_effective_framework

        effective, was_overridden, routing_decision = _compute_effective_framework(analysis)
        return effective or wrapper, bool(was_overridden), dict(routing_decision or {})
    except Exception as exc:  # noqa: BLE001 - runtime evidence must fail open
        logger.debug("GTOS vNext effective framework fallback: %s", exc)
        return wrapper, False, {
            "wrapper_framework": wrapper,
            "effective_framework": wrapper,
            "was_overridden": False,
            "reason": "effective_framework_resolution_failed",
        }


def build_vnext_event_from_candidate(
    *,
    analysis: Any,
    raw_data: dict[str, Any] | None,
    kill_zone: str,
    symbol: str,
    source_symbol: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the compact runtime event contract from a GTOS candidate."""
    trade_params = getattr(analysis, "trade_parameters", None)
    direction = getattr(trade_params, "direction", None)
    if direction is None and isinstance(trade_params, dict):
        direction = trade_params.get("direction")

    model_cfg = (config or {}).get("model_a", {}) or {}
    market_cfg = (config or {}).get("market", {}) or {}
    market_symbol = _compatible_event_market_symbol(
        symbol=symbol,
        source_symbol=source_symbol,
        configured_market=market_cfg.get("symbol"),
    )
    family = _event_symbol_family(
        {
            "source_symbol": source_symbol or symbol,
            "symbol": symbol,
            "market": market_symbol,
        }
    )
    wrapper_framework = getattr(analysis, "framework", None)
    effective_framework, framework_overridden, framework_routing = (
        resolve_vnext_effective_framework(analysis)
    )
    entry_timeframe = model_cfg.get("entry_timeframe", "")
    route_family = _route_family_for_framework(effective_framework)
    event = {
        "symbol": symbol,
        "source_symbol": source_symbol or symbol,
        "symbol_family": family,
        "market": market_symbol,
        "route_session": kill_zone,
        "session": kill_zone,
        "kill_zone": kill_zone,
        "side": direction,
        "direction": direction,
        "framework": effective_framework,
        "effective_framework": effective_framework,
        "route_family": route_family,
        "wrapper_framework": wrapper_framework,
        "framework_route_overridden": framework_overridden,
        "framework_route_reason": framework_routing.get("reason"),
        "market_timeframe": entry_timeframe,
        "timeframe": entry_timeframe,
        "entry_timeframe": entry_timeframe,
    }
    if raw_data:
        event["candle_close_utc"] = raw_data.get("candle_close_utc")
        event["market"] = raw_data.get("market") or event.get("market")
        event["timeframe"] = raw_data.get("timeframe") or event.get("timeframe")
        event["route_family"] = raw_data.get("route_family") or event.get("route_family")
        event["source_component"] = raw_data.get("source_component") or raw_data.get("component")
        for field in (
            *ADVISORY_SCOPE_FIELDS,
            *EVENT_FILTER_FIELDS,
            "primitive",
            "market_primitive",
            "source_primitive",
            "evidence_primitive",
        ):
            if raw_data.get(field) not in (None, ""):
                event[field] = raw_data.get(field)
    return {key: value for key, value in event.items() if value not in (None, "")}


def _side_from_bias(bias: str | None) -> str:
    normalized = _normalized(bias).casefold()
    if normalized == "bullish":
        return "LONG"
    if normalized == "bearish":
        return "SHORT"
    return ""


def build_vnext_pre_ai_event(
    *,
    symbol: str,
    source_symbol: str | None,
    kill_zone: str,
    config: dict[str, Any] | None,
    bias: str | None = None,
    side: str | None = None,
    raw_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the compact vNext event available before the AI call."""
    model_cfg = (config or {}).get("model_a", {}) or {}
    market_cfg = (config or {}).get("market", {}) or {}
    resolved_side = side or _side_from_bias(bias)
    market_symbol = _compatible_event_market_symbol(
        symbol=symbol,
        source_symbol=source_symbol,
        configured_market=market_cfg.get("symbol"),
    )
    family = _event_symbol_family(
        {
            "source_symbol": source_symbol or symbol,
            "symbol": symbol,
            "market": market_symbol,
        }
    )
    entry_timeframe = model_cfg.get("entry_timeframe", "")
    event = {
        "symbol": symbol,
        "source_symbol": source_symbol or symbol,
        "symbol_family": family,
        "market": market_symbol,
        "route_session": kill_zone,
        "session": kill_zone,
        "kill_zone": kill_zone,
        "side": resolved_side,
        "direction": resolved_side,
        "market_timeframe": entry_timeframe,
        "timeframe": entry_timeframe,
        "entry_timeframe": entry_timeframe,
    }
    if raw_data:
        event["candle_close_utc"] = raw_data.get("candle_close_utc")
        event["market"] = raw_data.get("market") or event.get("market")
        event["timeframe"] = raw_data.get("timeframe") or event.get("timeframe")
        event["route_family"] = raw_data.get("route_family") or event.get("route_family")
        event["source_component"] = raw_data.get("source_component") or raw_data.get("component")
        for field in (
            *ADVISORY_SCOPE_FIELDS,
            *EVENT_FILTER_FIELDS,
            "primitive",
            "market_primitive",
            "source_primitive",
            "evidence_primitive",
        ):
            if raw_data.get(field) not in (None, ""):
                event[field] = raw_data.get(field)
    return {key: value for key, value in event.items() if value not in (None, "")}


def _collapse_pre_ai_side_decisions(
    side_decisions: list[GTOSVNextRuntimeDecision],
) -> DecisionLabel:
    matched = [decision.decision for decision in side_decisions if decision.matched]
    if not matched:
        return "LEGACY"
    labels = set(matched)
    if labels == {"FOLLOW"}:
        return "FOLLOW"
    if labels == {"AVOID"}:
        return "AVOID"
    return "MIXED"


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        identity = _row_identity(row)
        if identity in seen:
            continue
        seen.add(identity)
        deduped.append(row)
    return deduped


def _configured_list(cfg: dict[str, Any], key: str, default: Iterable[str]) -> list[str]:
    raw = cfg.get(key)
    if raw is None:
        return [str(item) for item in default]
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, IterableABC):
        items = [str(item) for item in raw if str(item)]
        return items or [str(item) for item in default]
    return [str(item) for item in default]


def _merge_configured_and_artifact_values(
    configured: Iterable[str],
    discovered: Iterable[str],
) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for value in (*configured, *discovered):
        normalized = _normalized(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        values.append(normalized)
    return values


def _artifact_route_source_components(
    artifact_index: GTOSVNextEvidenceIndex | None,
    cfg: dict[str, Any],
) -> tuple[str, ...]:
    if artifact_index is None:
        return ()
    allowed_families = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "artifact_source_component_evidence_families",
            [
                "numeric_router_system_recommendations",
                "numeric_router_source_repair",
                "expanded_market_reduced_surface",
                "ai_decision_architecture",
            ],
        )
    }
    excluded = {
        _normalized(item)
        for item in _configured_list(cfg, "artifact_source_component_exclusions", [])
    }
    components: set[str] = set()
    for row in artifact_index.rows:
        component = _row_dimension_value(row, "source_component")
        if not component or component in excluded:
            continue
        if not RUNTIME_SOURCE_COMPONENT_RE.match(component):
            continue
        if allowed_families and _normalized(row.get("evidence_family")) not in allowed_families:
            continue
        components.add(component)
    return tuple(sorted(components))


def _pre_ai_route_events(
    base_event: dict[str, Any],
    *,
    side: str,
    cfg: dict[str, Any],
    artifact_index: GTOSVNextEvidenceIndex | None = None,
) -> list[dict[str, Any]]:
    event = dict(base_event)
    event["side"] = side
    event["direction"] = side
    if not bool(cfg.get("pre_ai_evaluate_route_variants", True)):
        return [event]

    if bool(cfg.get("pre_ai_prune_route_variants_to_artifact_scopes", True)) and artifact_index is not None:
        return _artifact_scoped_route_events(
            event,
            cfg=cfg,
            prefix="pre_ai",
            artifact_index=artifact_index,
        )

    base_tf = _normalized(event.get("market_timeframe")) or "M15"
    timeframes, horizons, frameworks, route_families, source_components = _route_event_values(
        cfg,
        prefix="pre_ai",
        base_timeframe=base_tf,
        artifact_index=artifact_index,
    )

    events: list[dict[str, Any]] = [event]
    seen: set[tuple[tuple[str, Any], ...]] = {tuple(sorted(event.items()))}
    for timeframe, horizon, framework, route_family, source_component in product(
        timeframes,
        horizons,
        frameworks,
        route_families,
        source_components,
    ):
        variant = dict(event)
        if timeframe:
            variant["market_timeframe"] = timeframe
            variant["timeframe"] = timeframe
            variant["entry_timeframe"] = timeframe
        if horizon:
            variant["horizon_id"] = horizon
        if framework:
            variant["framework"] = framework
            variant.setdefault("route_family", _route_family_for_framework(framework))
        if route_family:
            variant["route_family"] = route_family
        if source_component:
            variant["source_component"] = source_component
        key = tuple(sorted(variant.items()))
        if key not in seen:
            seen.add(key)
            events.append(variant)
    return events


def _route_events_enabled_for_phase(cfg: dict[str, Any], phase: str) -> bool:
    if phase == "post_l2":
        return bool(cfg.get("post_l2_evaluate_route_variants", True))
    return bool(cfg.get("pre_ai_evaluate_route_variants", True))


def _route_event_values(
    cfg: dict[str, Any],
    *,
    prefix: str,
    base_timeframe: str,
    artifact_index: GTOSVNextEvidenceIndex | None = None,
) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    timeframes = _configured_list(
        cfg,
        f"{prefix}_route_timeframes",
        [base_timeframe, "H1", "H4", "D1"],
    )
    horizons = _configured_list(cfg, f"{prefix}_route_horizons", ["", "h4", "h16", "h32"])
    frameworks = _configured_list(cfg, f"{prefix}_route_frameworks", [""])
    route_families = _configured_list(cfg, f"{prefix}_route_families", [""])
    source_components = _configured_list(cfg, f"{prefix}_route_source_components", [""])
    include_artifact_components = bool(
        cfg.get(
            f"{prefix}_include_artifact_source_components",
            cfg.get("include_artifact_source_components", False),
        )
    )
    if include_artifact_components:
        source_components = _merge_configured_and_artifact_values(
            source_components,
            _artifact_route_source_components(artifact_index, cfg),
        )
    return timeframes, horizons, frameworks, route_families, source_components


def _route_value_allowed(field: str, value: str, allowed_values: list[str]) -> bool:
    if not value:
        return True
    configured = [item for item in allowed_values if _normalized(item)]
    if not configured:
        return True
    return any(_field_values_match(field, allowed, value) for allowed in configured)


def _route_scope_matches_base(scope: dict[str, str], base_event: dict[str, str]) -> bool:
    for field in ("symbol", "source_symbol", "symbol_family", "market", "route_session", "side"):
        expected = scope.get(field)
        if not expected:
            continue
        actual = base_event.get(field)
        if not actual or not _field_values_match(field, expected, actual):
            return False
    return True


def _route_event_excluded_evidence_families(cfg: dict[str, Any]) -> set[str]:
    return {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "route_event_excluded_evidence_families",
            (
                "moonshot_source_component_summary",
                "moonshot_recommendation_merge_bucket",
                "moonshot_recommendation_family_rollup",
                "moonshot_recommendation_unified_candidate",
                "moonshot_recommendation_scope_rollup",
            ),
        )
    }


def _append_route_event(
    events: list[dict[str, Any]],
    seen: set[tuple[tuple[str, Any], ...]],
    base_event: dict[str, Any],
    *,
    timeframe: str,
    horizon: str,
    framework: str,
    route_family: str,
    source_component: str,
) -> None:
    variant = dict(base_event)
    if timeframe:
        variant["market_timeframe"] = timeframe
        variant["timeframe"] = timeframe
        variant["entry_timeframe"] = timeframe
    if horizon:
        variant["horizon_id"] = horizon
    if framework:
        variant["framework"] = framework
        variant.setdefault("route_family", _route_family_for_framework(framework))
    if route_family:
        variant["route_family"] = route_family
    if source_component:
        variant["source_component"] = source_component
    key = tuple(sorted(variant.items()))
    if key not in seen:
        seen.add(key)
        events.append(variant)


def _artifact_scoped_route_events(
    base_event: dict[str, Any],
    *,
    cfg: dict[str, Any],
    prefix: str,
    artifact_index: GTOSVNextEvidenceIndex,
) -> list[dict[str, Any]]:
    """Build route variants only from artifact scopes compatible with the event."""
    base_tf = _normalized(base_event.get("market_timeframe")) or "M15"
    timeframes, horizons, frameworks, route_families, source_components = _route_event_values(
        cfg,
        prefix=prefix,
        base_timeframe=base_tf,
        artifact_index=artifact_index,
    )
    normalized_base = normalize_event(base_event)
    events: list[dict[str, Any]] = [base_event]
    seen: set[tuple[tuple[str, Any], ...]] = {tuple(sorted(base_event.items()))}
    excluded_families = _route_event_excluded_evidence_families(cfg)
    for row, scope in zip(artifact_index.rows, artifact_index.scopes):
        if _normalized(row.get("evidence_family")) in excluded_families:
            continue
        if not _route_scope_matches_base(scope, normalized_base):
            continue
        timeframe = _row_dimension_value(row, "market_timeframe") or _row_dimension_value(row, "timeframe")
        horizon = _row_dimension_value(row, "horizon_id")
        framework = _row_dimension_value(row, "framework")
        route_family = _row_dimension_value(row, "route_family")
        source_component = _row_dimension_value(row, "source_component")
        if source_component and not RUNTIME_SOURCE_COMPONENT_RE.match(source_component):
            continue
        if not _route_value_allowed("market_timeframe", timeframe, timeframes):
            continue
        if not _route_value_allowed("horizon_id", horizon, horizons):
            continue
        if not _route_value_allowed("framework", framework, frameworks):
            continue
        if not _route_value_allowed("route_family", route_family, route_families):
            continue
        if not _route_value_allowed("source_component", source_component, source_components):
            continue
        _append_route_event(
            events,
            seen,
            base_event,
            timeframe=timeframe,
            horizon=horizon,
            framework=framework,
            route_family=route_family,
            source_component=source_component,
        )
    return events


def _artifact_scoped_route_selected_rows(
    base_event: dict[str, Any],
    *,
    cfg: dict[str, Any],
    prefix: str,
    artifact_index: GTOSVNextEvidenceIndex,
    min_scope_fields: int,
) -> tuple[list[dict[str, Any]], int]:
    """Select rows directly from compatible artifact scopes for route evaluation."""
    events = _artifact_scoped_route_events(
        base_event,
        cfg=cfg,
        prefix=prefix,
        artifact_index=artifact_index,
    )
    selected_rows: list[dict[str, Any]] = []
    subset_index_cache: dict[tuple[tuple[str, str], ...], tuple[int, ...]] = {}
    excluded_families = _route_event_excluded_evidence_families(cfg)
    for route_event in events:
        normalized_event = normalize_event(route_event)
        criteria_key = _event_criteria_key(normalized_event)
        candidate_indices: set[int] = set()
        for size in range(1, len(criteria_key) + 1):
            for subset in combinations(criteria_key, size):
                key = tuple(subset)
                if key not in subset_index_cache:
                    subset_index_cache[key] = artifact_index._scope_key_index.get(key, ())
                candidate_indices.update(subset_index_cache[key])
        matches: list[dict[str, Any]] = []
        for index in sorted(candidate_indices):
            scope = artifact_index.scopes[index]
            if len(scope) < min_scope_fields:
                continue
            row = artifact_index.rows[index]
            if _normalized(row.get("evidence_family")) in excluded_families:
                continue
            if _scope_matches(scope, normalized_event) and _row_matches_event_filters(
                row,
                normalized_event,
            ):
                matches.append(dict(row))
        selected_rows.extend(
            _select_runtime_rows(
                matches,
                cfg=cfg,
                min_scope_fields=min_scope_fields,
                normalized_event=normalized_event,
            )
        )
    return selected_rows, len(events)


def _candidate_route_events(
    base_event: dict[str, Any],
    *,
    cfg: dict[str, Any],
    artifact_index: GTOSVNextEvidenceIndex | None = None,
) -> list[dict[str, Any]]:
    event = dict(base_event)
    if not _route_events_enabled_for_phase(cfg, "post_l2"):
        return [event]

    candidate_framework = _normalized(event.get("effective_framework") or event.get("framework"))
    route_cfg = cfg
    if bool(cfg.get("post_l2_route_use_candidate_framework_only", True)) and candidate_framework:
        route_cfg = {**cfg, "post_l2_route_frameworks": [candidate_framework]}

    if bool(cfg.get("post_l2_prune_route_variants_to_artifact_scopes", True)) and artifact_index is not None:
        return _artifact_scoped_route_events(
            event,
            cfg=route_cfg,
            prefix="post_l2",
            artifact_index=artifact_index,
        )

    base_tf = _normalized(event.get("market_timeframe")) or "M15"
    timeframes, horizons, frameworks, route_families, source_components = _route_event_values(
        route_cfg,
        prefix="post_l2",
        base_timeframe=base_tf,
        artifact_index=artifact_index,
    )
    if bool(cfg.get("post_l2_route_use_candidate_framework_only", True)) and candidate_framework:
        frameworks = [candidate_framework]
    elif candidate_framework and not frameworks:
        frameworks = [candidate_framework]

    events: list[dict[str, Any]] = [event]
    seen: set[tuple[tuple[str, Any], ...]] = {tuple(sorted(event.items()))}
    for timeframe, horizon, framework, route_family, source_component in product(
        timeframes,
        horizons,
        frameworks,
        route_families,
        source_components,
    ):
        variant = dict(event)
        if timeframe:
            variant["market_timeframe"] = timeframe
            variant["timeframe"] = timeframe
            variant["entry_timeframe"] = timeframe
        if horizon:
            variant["horizon_id"] = horizon
        if framework:
            variant["framework"] = framework
            variant.setdefault("route_family", _route_family_for_framework(framework))
        if route_family:
            variant["route_family"] = route_family
        if source_component:
            variant["source_component"] = source_component
        key = tuple(sorted(variant.items()))
        if key not in seen:
            seen.add(key)
            events.append(variant)
    return events


def _runtime_index_for_evaluation(
    *,
    config: dict[str, Any] | None,
    artifact_rows: list[dict[str, Any]] | None,
    artifact_index: GTOSVNextEvidenceIndex | None,
) -> GTOSVNextEvidenceIndex:
    paths = _configured_artifact_paths(config)
    if artifact_rows is not None:
        first_path = str(paths[0]) if paths else "in_memory"
        return GTOSVNextEvidenceIndex.from_rows(
            [dict(row) for row in artifact_rows],
            artifact_paths=tuple(str(path) for path in paths),
            rows_loaded_by_path={first_path: len(artifact_rows)},
        )
    return artifact_index or load_vnext_evidence_index(paths)


def _source_component_summary_prior_rows(
    *,
    selected_rows: list[dict[str, Any]],
    normalized_event: dict[str, str],
    runtime_index: GTOSVNextEvidenceIndex | None,
    cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    if runtime_index is None or not bool(cfg.get("source_component_summary_prior_enabled", True)):
        return []
    components = {
        _row_dimension_value(row, "source_component")
        for row in selected_rows
        if _row_dimension_value(row, "source_component")
    }
    if normalized_event.get("source_component"):
        components.add(normalized_event["source_component"])
    if not components:
        return []

    families = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "source_component_summary_prior_evidence_families",
            ("moonshot_source_component_summary",),
        )
    }
    configured_components = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "source_component_summary_prior_components",
            (),
        )
    }
    min_rollup_rows = int(
        _configured_float(cfg, "source_component_summary_prior_min_rollup_rows", 20.0)
    )
    selected: list[dict[str, Any]] = []
    for row in runtime_index.rows:
        if families and _normalized(row.get("evidence_family")) not in families:
            continue
        component = _row_dimension_value(row, "source_component")
        if not component or component not in components:
            continue
        if configured_components and component not in configured_components:
            continue
        row_count = _to_float(row.get("row_count"))
        if row_count is not None and row_count < min_rollup_rows:
            continue
        route_family = _row_dimension_value(row, "route_family")
        event_route_family = normalized_event.get("route_family")
        if (
            route_family
            and event_route_family
            and not _field_values_match("route_family", route_family, event_route_family)
        ):
            continue
        selected.append(dict(row))
    return _dedupe_rows(selected)


def _recommendation_bucket_prior_rows(
    *,
    selected_rows: list[dict[str, Any]],
    normalized_event: dict[str, str],
    runtime_index: GTOSVNextEvidenceIndex | None,
    cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    if runtime_index is None or not bool(cfg.get("recommendation_bucket_prior_enabled", True)):
        return []
    components = {
        _row_dimension_value(row, "source_component")
        for row in selected_rows
        if _row_dimension_value(row, "source_component")
    }
    if normalized_event.get("source_component"):
        components.add(normalized_event["source_component"])
    if not components:
        return []

    families = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_bucket_prior_evidence_families",
            ("moonshot_recommendation_merge_bucket",),
        )
    }
    configured_components = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_bucket_prior_components",
            (),
        )
    }
    configured_bucket_families = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_bucket_prior_bucket_families",
            ("source_component", "source_component_decision_group"),
        )
    }
    min_bucket_rows = int(
        _configured_float(cfg, "recommendation_bucket_prior_min_bucket_rows", 20.0)
    )
    selected: list[dict[str, Any]] = []
    for row in runtime_index.rows:
        if families and _normalized(row.get("evidence_family")) not in families:
            continue
        component = _row_dimension_value(row, "source_component")
        if not component or component not in components:
            continue
        if configured_components and component not in configured_components:
            continue
        bucket_family = _normalized(row.get("recommendation_bucket_family"))
        if configured_bucket_families and bucket_family not in configured_bucket_families:
            continue
        row_count = _to_float(row.get("row_count"))
        if row_count is not None and row_count < min_bucket_rows:
            continue
        route_family = _row_dimension_value(row, "route_family")
        event_route_family = normalized_event.get("route_family")
        if (
            route_family
            and event_route_family
            and not _field_values_match("route_family", route_family, event_route_family)
        ):
            continue
        selected.append(dict(row))
    return _dedupe_rows(selected)


def _recommendation_family_rollup_prior_rows(
    *,
    selected_rows: list[dict[str, Any]],
    normalized_event: dict[str, str],
    runtime_index: GTOSVNextEvidenceIndex | None,
    cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    if runtime_index is None or not bool(cfg.get("recommendation_family_rollup_prior_enabled", True)):
        return []
    components = {
        _row_dimension_value(row, "source_component")
        for row in selected_rows
        if _row_dimension_value(row, "source_component")
    }
    if normalized_event.get("source_component"):
        components.add(normalized_event["source_component"])
    if not components:
        return []

    families = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_family_rollup_prior_evidence_families",
            ("moonshot_recommendation_family_rollup",),
        )
    }
    configured_components = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_family_rollup_prior_components",
            (),
        )
    }
    configured_rollup_types = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_family_rollup_prior_rollup_types",
            ("source_component_decision_group",),
        )
    }
    min_rows = int(
        _configured_float(cfg, "recommendation_family_rollup_prior_min_rows", 20.0)
    )
    selected: list[dict[str, Any]] = []
    for row in runtime_index.rows:
        if families and _normalized(row.get("evidence_family")) not in families:
            continue
        component = _row_dimension_value(row, "source_component")
        if not component or component not in components:
            continue
        if configured_components and component not in configured_components:
            continue
        rollup_type = _normalized(row.get("recommendation_family_rollup_type"))
        if configured_rollup_types and rollup_type not in configured_rollup_types:
            continue
        row_count = _to_float(row.get("row_count"))
        if row_count is not None and row_count < min_rows:
            continue
        route_family = _row_dimension_value(row, "route_family")
        event_route_family = normalized_event.get("route_family")
        if (
            route_family
            and event_route_family
            and not _field_values_match("route_family", route_family, event_route_family)
        ):
            continue
        selected.append(dict(row))
    return _dedupe_rows(selected)


def _event_matches_prior_dimension(
    row: dict[str, Any],
    normalized_event: dict[str, str],
    field: str,
) -> bool:
    expected = _row_dimension_value(row, field)
    if not expected:
        return True
    candidates: list[str] = []
    if field == "symbol":
        candidates.extend(
            value
            for value in (
                normalized_event.get("symbol"),
                normalized_event.get("source_symbol"),
                normalized_event.get("market"),
            )
            if value
        )
    elif field == "source_symbol":
        candidates.extend(
            value
            for value in (
                normalized_event.get("source_symbol"),
                normalized_event.get("symbol"),
                normalized_event.get("market"),
            )
            if value
        )
    elif field == "symbol_family":
        candidates.extend(
            value
            for value in (
                normalized_event.get("symbol_family"),
                _event_symbol_family(normalized_event),
            )
            if value
        )
    else:
        if value := normalized_event.get(field):
            candidates.append(value)
    return any(_field_values_match(field, expected, actual) for actual in candidates)


def _recommendation_unified_candidate_prior_rows(
    *,
    selected_rows: list[dict[str, Any]],
    normalized_event: dict[str, str],
    runtime_index: GTOSVNextEvidenceIndex | None,
    cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    if runtime_index is None or not bool(
        cfg.get("recommendation_unified_candidate_prior_enabled", True)
    ):
        return []
    components = {
        _row_dimension_value(row, "source_component")
        for row in selected_rows
        if _row_dimension_value(row, "source_component")
    }
    if normalized_event.get("source_component"):
        components.add(normalized_event["source_component"])
    if not components:
        return []

    families = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_unified_candidate_prior_evidence_families",
            ("moonshot_recommendation_unified_candidate",),
        )
    }
    configured_components = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_unified_candidate_prior_components",
            (),
        )
    }
    scoped_match_fields = _configured_list(
        cfg,
        "recommendation_unified_candidate_prior_match_fields",
        ("symbol", "route_session", "horizon_id", "primitive"),
    )
    min_rows = int(
        _configured_float(cfg, "recommendation_unified_candidate_prior_min_rows", 20.0)
    )
    selected: list[dict[str, Any]] = []
    for row in runtime_index.rows:
        if families and _normalized(row.get("evidence_family")) not in families:
            continue
        component = _row_dimension_value(row, "source_component")
        if not component or component not in components:
            continue
        if configured_components and component not in configured_components:
            continue
        route_family = _row_dimension_value(row, "route_family")
        event_route_family = normalized_event.get("route_family")
        if (
            route_family
            and event_route_family
            and not _field_values_match("route_family", route_family, event_route_family)
        ):
            continue
        if not all(
            _event_matches_prior_dimension(row, normalized_event, _normalized(field))
            for field in scoped_match_fields
            if _normalized(field)
        ):
            continue
        selected.append(dict(row))

    deduped = _dedupe_rows(selected)
    if len(deduped) < max(1, min_rows):
        return []
    return deduped


def _recommendation_scope_rollup_prior_rows(
    *,
    selected_rows: list[dict[str, Any]],
    normalized_event: dict[str, str],
    runtime_index: GTOSVNextEvidenceIndex | None,
    cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    if runtime_index is None or not bool(cfg.get("recommendation_scope_rollup_prior_enabled", True)):
        return []
    components = {
        _row_dimension_value(row, "source_component")
        for row in selected_rows
        if _row_dimension_value(row, "source_component")
    }
    if normalized_event.get("source_component"):
        components.add(normalized_event["source_component"])
    if not components:
        return []

    families = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_scope_rollup_prior_evidence_families",
            ("moonshot_recommendation_scope_rollup",),
        )
    }
    configured_components = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_scope_rollup_prior_components",
            (),
        )
    }
    configured_rollup_types = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_scope_rollup_prior_rollup_types",
            ("scope_component",),
        )
    }
    min_rows = int(
        _configured_float(cfg, "recommendation_scope_rollup_prior_min_rows", 20.0)
    )
    scoped_match_fields = _configured_list(
        cfg,
        "recommendation_scope_rollup_prior_match_fields",
        ("symbol", "route_session", "horizon_id", "primitive"),
    )
    selected: list[dict[str, Any]] = []
    for row in runtime_index.rows:
        if families and _normalized(row.get("evidence_family")) not in families:
            continue
        component = _row_dimension_value(row, "source_component")
        if not component or component not in components:
            continue
        if configured_components and component not in configured_components:
            continue
        rollup_type = _normalized(row.get("recommendation_scope_rollup_type"))
        if configured_rollup_types and rollup_type not in configured_rollup_types:
            continue
        row_count = _to_float(row.get("row_count"))
        if row_count is not None and row_count < min_rows:
            continue
        route_family = _row_dimension_value(row, "route_family")
        event_route_family = normalized_event.get("route_family")
        if (
            route_family
            and event_route_family
            and not _field_values_match("route_family", route_family, event_route_family)
        ):
            continue
        if not all(
            _event_matches_prior_dimension(row, normalized_event, _normalized(field))
            for field in scoped_match_fields
            if _normalized(field)
        ):
            continue
        selected.append(dict(row))
    return _dedupe_rows(selected)


def _decision_from_selected_rows(
    *,
    selected_rows: list[dict[str, Any]],
    normalized_event: dict[str, str],
    enabled: bool,
    apply_to_execution: bool,
    reason: str,
    artifact_paths: tuple[str, ...],
    runtime_index: GTOSVNextEvidenceIndex | None = None,
    route_event_count: int | None = None,
    cfg: dict[str, Any] | None = None,
    bridge_diagnostics: dict[str, Any] | None = None,
) -> GTOSVNextRuntimeDecision:
    decision, resolution_evidence = _resolve_final_decision(selected_rows, cfg)
    cfg = cfg or {}
    row_detail_limit = int(
        _configured_float(cfg, "evidence_row_detail_limit", float(DEFAULT_EVIDENCE_ROW_DETAIL_LIMIT))
    )
    id_list_limit = int(
        _configured_float(cfg, "evidence_id_list_limit", float(DEFAULT_EVIDENCE_ID_LIST_LIMIT))
    )
    evidence = _aggregate_evidence(
        selected_rows,
        row_detail_limit=row_detail_limit,
        id_list_limit=id_list_limit,
        cfg=cfg,
    )
    source_component_prior_rows = _source_component_summary_prior_rows(
        selected_rows=selected_rows,
        normalized_event=normalized_event,
        runtime_index=runtime_index,
        cfg=cfg,
    )
    if source_component_prior_rows:
        evidence["source_component_summary_prior"] = _aggregate_evidence(
            source_component_prior_rows,
            row_detail_limit=row_detail_limit,
            id_list_limit=id_list_limit,
            cfg=cfg,
        )
    recommendation_bucket_prior_rows = _recommendation_bucket_prior_rows(
        selected_rows=selected_rows,
        normalized_event=normalized_event,
        runtime_index=runtime_index,
        cfg=cfg,
    )
    if recommendation_bucket_prior_rows:
        evidence["recommendation_bucket_prior"] = _aggregate_evidence(
            recommendation_bucket_prior_rows,
            row_detail_limit=row_detail_limit,
            id_list_limit=id_list_limit,
            cfg=cfg,
        )
    recommendation_family_rollup_prior_rows = _recommendation_family_rollup_prior_rows(
        selected_rows=selected_rows,
        normalized_event=normalized_event,
        runtime_index=runtime_index,
        cfg=cfg,
    )
    if recommendation_family_rollup_prior_rows:
        evidence["recommendation_family_rollup_prior"] = _aggregate_evidence(
            recommendation_family_rollup_prior_rows,
            row_detail_limit=row_detail_limit,
            id_list_limit=id_list_limit,
            cfg=cfg,
        )
    recommendation_unified_candidate_prior_rows = _recommendation_unified_candidate_prior_rows(
        selected_rows=selected_rows,
        normalized_event=normalized_event,
        runtime_index=runtime_index,
        cfg=cfg,
    )
    if recommendation_unified_candidate_prior_rows:
        evidence["recommendation_unified_candidate_prior"] = _aggregate_evidence(
            recommendation_unified_candidate_prior_rows,
            row_detail_limit=row_detail_limit,
            id_list_limit=id_list_limit,
            cfg=cfg,
        )
    recommendation_scope_rollup_prior_rows = _recommendation_scope_rollup_prior_rows(
        selected_rows=selected_rows,
        normalized_event=normalized_event,
        runtime_index=runtime_index,
        cfg=cfg,
    )
    if recommendation_scope_rollup_prior_rows:
        evidence["recommendation_scope_rollup_prior"] = _aggregate_evidence(
            recommendation_scope_rollup_prior_rows,
            row_detail_limit=row_detail_limit,
            id_list_limit=id_list_limit,
            cfg=cfg,
        )
    evidence["decision_resolution"] = resolution_evidence
    confluence_summary = evidence.get("numeric_confluence")
    if isinstance(confluence_summary, dict):
        confluence_summary["final_mapping"] = final_numeric_confluence_mapping(
            selected_decision=decision,
            resolution_evidence=resolution_evidence,
            confluence_summary=confluence_summary,
        )
    if route_event_count is not None:
        evidence["route_event_count"] = route_event_count
    if runtime_index is not None:
        evidence["runtime_index"] = {
            "row_count": runtime_index.row_count,
            "rows_loaded_by_path": runtime_index.rows_loaded_by_path,
            "missing_paths": list(runtime_index.missing_paths),
            "compiled_from_full_evidence": any(
                str(path).endswith("GTOS_VNEXT_EVIDENCE_TO_SYSTEM_BUILD_MATRIX_2026-05-18.jsonl")
                for path in runtime_index.artifact_paths
            ),
        }
    if bridge_diagnostics is None:
        bridge_diagnostics = _bridge_diagnostics_for_event(normalized_event, cfg)
    if bridge_diagnostics:
        evidence["bridge_diagnostics"] = bridge_diagnostics
    return GTOSVNextRuntimeDecision(
        decision=decision,
        event=normalized_event,
        enabled=enabled,
        apply_to_execution=apply_to_execution,
        matched=True,
        reason=reason,
        evidence=evidence,
        artifact_paths=artifact_paths,
    )


def _side_decision_from_route_events(
    *,
    side: str,
    base_event: dict[str, Any],
    config: dict[str, Any] | None,
    cfg: dict[str, Any],
    artifact_index: GTOSVNextEvidenceIndex,
) -> GTOSVNextRuntimeDecision:
    min_scope_fields = int(cfg.get("min_scope_fields", 1) or 1)
    selected_rows: list[dict[str, Any]] = []
    if (
        bool(cfg.get("pre_ai_prune_route_variants_to_artifact_scopes", True))
        and bool(cfg.get("pre_ai_match_artifact_scopes_directly", True))
    ):
        selected_rows, route_event_count = _artifact_scoped_route_selected_rows(
            base_event,
            cfg=cfg,
            prefix="pre_ai",
            artifact_index=artifact_index,
            min_scope_fields=min_scope_fields,
        )
    else:
        route_events = _pre_ai_route_events(
            base_event,
            side=side,
            cfg=cfg,
            artifact_index=artifact_index,
        )
        route_event_count = len(route_events)
        for route_event in route_events:
            normalized = normalize_event(route_event)
            matches = artifact_index.match_event(normalized, min_scope_fields=min_scope_fields)
            if not matches:
                continue
            selected_rows.extend(
                _select_runtime_rows(
                    matches,
                    cfg=cfg,
                    min_scope_fields=min_scope_fields,
                    normalized_event=normalized,
                )
            )

    selected_rows = _dedupe_rows(selected_rows)
    normalized_event = normalize_event({**base_event, "side": side, "direction": side})
    apply_to_execution = bool(cfg.get("apply_to_execution", False))
    if not selected_rows:
        return GTOSVNextRuntimeDecision(
            decision="LEGACY",
            event=normalized_event,
            enabled=True,
            apply_to_execution=apply_to_execution,
            matched=False,
            reason="no_matching_vnext_scope",
            artifact_paths=artifact_index.artifact_paths,
        )

    return _decision_from_selected_rows(
        selected_rows=selected_rows,
        normalized_event=normalized_event,
        enabled=True,
        apply_to_execution=apply_to_execution,
        reason="matched_vnext_route_scope",
        artifact_paths=artifact_index.artifact_paths,
        runtime_index=artifact_index,
        route_event_count=route_event_count,
        cfg=cfg,
    )


def _frameworks_from_decision_rows(
    decision: GTOSVNextRuntimeDecision,
    row_decision: DecisionLabel,
) -> tuple[str, ...]:
    evidence = decision.evidence or {}
    rows = evidence.get("rows") if isinstance(evidence, dict) else None
    if not isinstance(rows, list):
        return ()
    frameworks: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("decision") != row_decision:
            continue
        scope = row.get("event_scope") if isinstance(row.get("event_scope"), dict) else {}
        framework = row.get("framework") or scope.get("framework")
        if framework:
            frameworks.add(str(framework))
            continue
        route_family = row.get("route_family") or scope.get("route_family")
        if _normalized(route_family) in ROUTE_FAMILY_BY_FRAMEWORK:
            frameworks.add(_normalized(route_family))
    return tuple(sorted(frameworks))


def _route_families_from_decision_rows(
    decision: GTOSVNextRuntimeDecision,
    row_decision: DecisionLabel,
) -> tuple[str, ...]:
    evidence = decision.evidence or {}
    rows = evidence.get("rows") if isinstance(evidence, dict) else None
    if not isinstance(rows, list):
        return ()
    route_families: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("decision") != row_decision:
            continue
        scope = row.get("event_scope") if isinstance(row.get("event_scope"), dict) else {}
        route_family = (
            row.get("route_family")
            or scope.get("route_family")
            or _route_family_for_framework(row.get("framework") or scope.get("framework"))
        )
        if route_family:
            route_families.add(str(route_family))
    return tuple(sorted(route_families))


def _dominant_avoid_route_families(
    decision: GTOSVNextRuntimeDecision,
    cfg: dict[str, Any],
) -> tuple[str, ...]:
    evidence = decision.evidence or {}
    counts_by_family = (
        evidence.get("route_family_decision_counts", {})
        if isinstance(evidence, dict)
        else {}
    )
    if not isinstance(counts_by_family, dict):
        return ()
    min_rows = int(_configured_float(cfg, "route_family_avoid_veto_min_rows", 1.0))
    dominance_ratio = _configured_float(cfg, "route_family_avoid_veto_dominance_ratio", 1.0)
    blocked: set[str] = set()
    for family, counts in counts_by_family.items():
        if not isinstance(counts, dict):
            continue
        avoid_rows = int(counts.get("AVOID") or 0)
        follow_rows = int(counts.get("FOLLOW") or 0)
        if avoid_rows >= max(1, min_rows) and avoid_rows >= max(1, follow_rows) * dominance_ratio:
            blocked.add(str(family))
    return tuple(sorted(blocked))


def _pre_ai_framework_exclusion_candidates(cfg: dict[str, Any]) -> tuple[str, ...]:
    configured = _configured_list(cfg, "pre_ai_framework_exclusion_candidates", [])
    if not configured:
        configured = _configured_list(cfg, "pre_ai_route_frameworks", [])
    candidates: list[str] = []
    seen: set[str] = set()
    for framework in configured:
        if not framework or framework not in ROUTE_FAMILY_BY_FRAMEWORK:
            continue
        if framework in seen:
            continue
        seen.add(framework)
        candidates.append(framework)
    return tuple(candidates)


def _pre_ai_follow_side_pressure(
    decision: GTOSVNextRuntimeDecision,
    cfg: dict[str, Any],
) -> float:
    summary = _risk_evidence_summary(decision)
    components = {
        "cost_adjusted_simulated_r": summary["cost_adjusted_simulated_r_sum"],
        "stress_simulated_r": summary["stress_simulated_r_sum"],
        "proxy_score": summary["proxy_score_sum"],
    }
    weights = {
        "cost_adjusted_simulated_r": _configured_float(cfg, "conflict_cost_adjusted_r_weight", 1.0),
        "stress_simulated_r": _configured_float(cfg, "conflict_stress_r_weight", 0.25),
        "proxy_score": _configured_float(cfg, "conflict_proxy_score_weight", 1.0),
    }
    pressure = 0.0
    for key, value in components.items():
        if value is None:
            continue
        pressure += float(value) * weights[key]
    return pressure


def _pressure_from_metric_summary(summary: dict[str, Any], cfg: dict[str, Any]) -> float:
    components = {
        "cost_adjusted_simulated_r": _to_float(summary.get("cost_adjusted_simulated_r")),
        "stress_simulated_r": _to_float(summary.get("stress_simulated_r")),
        "proxy_score": _to_float(summary.get("proxy_score")),
    }
    weights = {
        "cost_adjusted_simulated_r": _configured_float(cfg, "conflict_cost_adjusted_r_weight", 1.0),
        "stress_simulated_r": _configured_float(cfg, "conflict_stress_r_weight", 0.25),
        "proxy_score": _configured_float(cfg, "conflict_proxy_score_weight", 1.0),
    }
    return sum(
        float(value) * weights[key]
        for key, value in components.items()
        if value is not None
    )


def _pre_ai_framework_follow_pressures(
    decision: GTOSVNextRuntimeDecision,
    cfg: dict[str, Any],
) -> dict[str, float]:
    evidence = decision.evidence or {}
    summaries = evidence.get("framework_decision_metric_summaries", {})
    if not isinstance(summaries, dict):
        return {}
    pressures: dict[str, float] = {}
    for framework, by_decision in summaries.items():
        if not isinstance(by_decision, dict):
            continue
        follow_summary = by_decision.get("FOLLOW")
        if not isinstance(follow_summary, dict):
            continue
        normalized = _normalized(framework)
        if not normalized:
            continue
        pressures[normalized] = _pressure_from_metric_summary(follow_summary, cfg)
    return pressures


def _pre_ai_select_ob_core_frameworks(
    decision: GTOSVNextRuntimeDecision,
    frameworks: tuple[str, ...],
    cfg: dict[str, Any],
) -> tuple[str, ...]:
    frameworks = tuple(_normalized(framework) for framework in frameworks if _normalized(framework))
    if (
        len(frameworks) <= 1
        or not bool(cfg.get("pre_ai_ob_core_framework_preference_enabled", True))
    ):
        return frameworks
    ob_framework = _normalized(cfg.get("pre_ai_ob_core_framework") or "ob_retest")
    if not ob_framework or ob_framework not in frameworks:
        return frameworks

    pressures = _pre_ai_framework_follow_pressures(decision, cfg)
    ob_pressure = pressures.get(ob_framework)
    if ob_pressure is None:
        return frameworks

    min_ob_pressure = _configured_float(cfg, "pre_ai_ob_core_min_abs_pressure", 1.0)
    competitor_ratio = _configured_float(
        cfg,
        "pre_ai_ob_core_competing_framework_dominance_ratio",
        1.5,
    )
    competitors = {
        framework: pressure
        for framework, pressure in pressures.items()
        if framework in frameworks and framework != ob_framework
    }
    if competitors:
        best_competitor, best_competitor_pressure = max(
            competitors.items(),
            key=lambda item: item[1],
        )
        if (
            best_competitor_pressure >= min_ob_pressure
            and best_competitor_pressure >= max(ob_pressure, min_ob_pressure) * competitor_ratio
        ):
            return (best_competitor,)
    if ob_pressure >= min_ob_pressure:
        return (ob_framework,)
    return frameworks


def _filter_route_families_for_framework_selection(
    route_families: tuple[str, ...],
    original_frameworks: tuple[str, ...],
    selected_frameworks: tuple[str, ...],
) -> tuple[str, ...]:
    if not route_families or selected_frameworks == original_frameworks:
        return route_families
    framework_route_families = set(ROUTE_FAMILY_BY_FRAMEWORK.values())
    selected_route_families = {
        _route_family_for_framework(framework)
        for framework in selected_frameworks
        if _route_family_for_framework(framework)
    }
    return tuple(
        family
        for family in route_families
        if family not in framework_route_families or family in selected_route_families
    )


def _dominant_follow_side(
    follow_sides: list[str],
    matched_by_side: dict[str, GTOSVNextRuntimeDecision],
    cfg: dict[str, Any],
) -> str | None:
    if len(follow_sides) <= 1 or not bool(cfg.get("pre_ai_select_stronger_follow_side_enabled", True)):
        return None
    min_pressure = _configured_float(cfg, "pre_ai_stronger_follow_min_abs_pressure", 1.0)
    dominance_ratio = _configured_float(cfg, "pre_ai_stronger_follow_dominance_ratio", 1.5)
    scores = {
        side: _pre_ai_follow_side_pressure(matched_by_side[side], cfg)
        for side in follow_sides
        if side in matched_by_side
    }
    if not scores:
        return None
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_side, best_score = ranked[0]
    if best_score < min_pressure:
        return None
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    if second_score <= 0 or best_score >= second_score * dominance_ratio:
        return best_side
    return None


def _pre_ai_recommendation(
    side_decisions: list[GTOSVNextRuntimeDecision],
    *,
    bias_side: str,
    skip_bias_avoid: bool,
    cfg: dict[str, Any],
) -> tuple[
    PreAIAction,
    str | None,
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    dict[str, str],
]:
    matched_by_side = {
        decision.event.get("side"): decision
        for decision in side_decisions
        if decision.event.get("side") and decision.matched
    }
    side_risk_reasons: dict[str, str] = {}
    risk_vetoed_sides: set[str] = set()
    min_route_multiplier = _configured_float(cfg, "pre_ai_min_route_risk_multiplier", 0.000001)
    min_follow_effective_n = _configured_float(cfg, "pre_ai_min_follow_effective_n", 3.0)
    risk_veto_enabled = bool(cfg.get("pre_ai_exclude_zero_risk_routes", True))
    for side, decision in matched_by_side.items():
        would_multiplier, risk_reason, _summary = _vnext_risk_multiplier(decision, cfg)
        side_risk_reasons[side] = risk_reason
        if (
            risk_veto_enabled
            and decision.decision == "FOLLOW"
        ):
            effective_n = _metric_value(decision.evidence or {}, "effective_n")
            if min_follow_effective_n > 0 and (
                effective_n is None or effective_n < min_follow_effective_n
            ):
                if _pre_ai_follow_effective_n_bypass_reason(risk_reason, cfg):
                    side_risk_reasons[side] = risk_reason
                else:
                    risk_vetoed_sides.add(side)
                    side_risk_reasons[side] = "vnext_pre_ai_follow_effective_n_below_min"
            elif would_multiplier <= min_route_multiplier:
                risk_vetoed_sides.add(side)

    follow_sides = sorted(
        side for side, decision in matched_by_side.items()
        if decision.decision == "FOLLOW" and side not in risk_vetoed_sides
    )
    avoided_or_vetoed_sides = sorted(
        side for side, decision in matched_by_side.items()
        if decision.decision == "AVOID" or side in risk_vetoed_sides
    )
    avoid_sides = sorted(
        side for side, decision in matched_by_side.items()
        if decision.decision == "AVOID"
    )
    blocked_frameworks = tuple(sorted({
        framework
        for decision in matched_by_side.values()
        for framework in _frameworks_from_decision_rows(decision, "AVOID")
    } | {
        framework
        for side in risk_vetoed_sides
        for framework in _frameworks_from_decision_rows(matched_by_side[side], "FOLLOW")
    }))
    blocked_route_families = tuple(sorted({
        route_family
        for decision in matched_by_side.values()
        for route_family in _dominant_avoid_route_families(decision, cfg)
    } | {
        route_family
        for side in risk_vetoed_sides
        for route_family in _route_families_from_decision_rows(matched_by_side[side], "FOLLOW")
    }))
    dominant_side = _dominant_follow_side(follow_sides, matched_by_side, cfg)
    if follow_sides and (len(follow_sides) == 1 or dominant_side):
        selected_side = dominant_side or follow_sides[0]
        selected_blocked_frameworks = _frameworks_from_decision_rows(
            matched_by_side[selected_side],
            "AVOID",
        )
        selected_blocked_route_families = _dominant_avoid_route_families(
            matched_by_side[selected_side],
            cfg,
        )
        recommended_frameworks = tuple(
            framework
            for framework in _frameworks_from_decision_rows(
                matched_by_side[selected_side],
                "FOLLOW",
            )
            if framework not in selected_blocked_frameworks
        )
        recommended_route_families = tuple(
            family
            for family in _route_families_from_decision_rows(
                matched_by_side[selected_side],
                "FOLLOW",
            )
            if family not in selected_blocked_route_families
        )
        original_recommended_frameworks = recommended_frameworks
        recommended_frameworks = _pre_ai_select_ob_core_frameworks(
            matched_by_side[selected_side],
            recommended_frameworks,
            cfg,
        )
        recommended_route_families = _filter_route_families_for_framework_selection(
            recommended_route_families,
            original_recommended_frameworks,
            recommended_frameworks,
        )
        action: PreAIAction = (
            "NARROW_AI_TO_ROUTE"
            if recommended_frameworks or recommended_route_families
            else "NARROW_AI_TO_SIDE"
        )
        return (
            action,
            selected_side,
            tuple(avoided_or_vetoed_sides),
            recommended_frameworks,
            recommended_route_families,
            selected_blocked_frameworks,
            selected_blocked_route_families,
            tuple(sorted(risk_vetoed_sides)),
            side_risk_reasons,
        )
    if blocked_frameworks and bool(cfg.get("pre_ai_exclude_blocked_frameworks_enabled", True)):
        framework_candidates = _pre_ai_framework_exclusion_candidates(cfg)
        remaining_frameworks = tuple(
            framework for framework in framework_candidates if framework not in blocked_frameworks
        )
        if remaining_frameworks and remaining_frameworks != framework_candidates:
            return (
                "NARROW_AI_EXCLUDE_FRAMEWORKS",
                None,
                tuple(avoided_or_vetoed_sides),
                remaining_frameworks,
                (),
                blocked_frameworks,
                blocked_route_families,
                tuple(sorted(risk_vetoed_sides)),
                side_risk_reasons,
            )
    if bias_side and bias_side in avoided_or_vetoed_sides and skip_bias_avoid and not follow_sides:
        return (
            "SKIP_AI_AVOID_ONLY",
            None,
            tuple(avoided_or_vetoed_sides),
            (),
            (),
            blocked_frameworks,
            blocked_route_families,
            tuple(sorted(risk_vetoed_sides)),
            side_risk_reasons,
        )
    if matched_by_side and set(matched_by_side) == set(avoided_or_vetoed_sides):
        return (
            "SKIP_AI_AVOID_ONLY",
            None,
            tuple(avoided_or_vetoed_sides),
            (),
            (),
            blocked_frameworks,
            blocked_route_families,
            tuple(sorted(risk_vetoed_sides)),
            side_risk_reasons,
        )
    recommended_side = follow_sides[0] if len(follow_sides) == 1 else None
    recommended_frameworks = (
        _frameworks_from_decision_rows(matched_by_side[recommended_side], "FOLLOW")
        if recommended_side
        else ()
    )
    recommended_route_families = (
        tuple(
            family
            for family in _route_families_from_decision_rows(
                matched_by_side[recommended_side],
                "FOLLOW",
            )
            if family not in blocked_route_families
        )
        if recommended_side
        else ()
    )
    original_recommended_frameworks = recommended_frameworks
    if recommended_side:
        recommended_frameworks = _pre_ai_select_ob_core_frameworks(
            matched_by_side[recommended_side],
            recommended_frameworks,
            cfg,
        )
        recommended_route_families = _filter_route_families_for_framework_selection(
            recommended_route_families,
            original_recommended_frameworks,
            recommended_frameworks,
        )
    return (
        "ALLOW_AI",
        recommended_side,
        tuple(avoided_or_vetoed_sides),
        recommended_frameworks,
        recommended_route_families,
        blocked_frameworks,
        blocked_route_families,
        tuple(sorted(risk_vetoed_sides)),
        side_risk_reasons,
    )


def _merge_numeric_counts(target: Counter[str], payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    for key, value in payload.items():
        if key in (None, ""):
            continue
        numeric = _to_float(value)
        if numeric is None:
            continue
        target[str(key)] += numeric


def _pre_ai_role_for_action(action: str, decision: DecisionLabel) -> str:
    if action == "NARROW_AI_TO_ROUTE":
        return "vnext_route_validator"
    if action == "NARROW_AI_TO_SIDE":
        return "vnext_side_validator"
    if action == "NARROW_AI_EXCLUDE_FRAMEWORKS":
        return "vnext_framework_screener"
    if action == "SKIP_AI_AVOID_ONLY":
        return "vnext_avoid_blocker_classifier"
    if decision != "LEGACY":
        return "vnext_evidence_triage"
    return "general_trade_decision"


def _pre_ai_role_instruction(ai_role: str) -> str:
    if ai_role == "vnext_route_validator":
        return (
            "Validate the evidence-routed side/framework/route only; reject with "
            "an exact blocker if current MSO geometry or source fields contradict it."
        )
    if ai_role == "vnext_side_validator":
        return (
            "Validate the evidence-routed side only; do not search the opposite "
            "side unless the current source fields invalidate the route."
        )
    if ai_role == "vnext_framework_screener":
        return (
            "Evaluate only the remaining frameworks after evidence-backed "
            "framework exclusions; do not revive blocked frameworks."
        )
    if ai_role == "vnext_avoid_blocker_classifier":
        return (
            "Treat the evidence as an avoid-class blocker and classify the exact "
            "reason; do not promote a candidate from this context."
        )
    if ai_role == "vnext_evidence_triage":
        return (
            "Use the attached vNext evidence as source-bound triage context and "
            "prefer exact blockers over broad trade selection."
        )
    return "Use the normal production trade-decision role."


def _pre_ai_ai_role_context(
    *,
    cfg: dict[str, Any],
    action: PreAIAction,
    would_action: PreAIAction,
    decision: DecisionLabel,
    recommended_side: str | None,
    recommended_frameworks: tuple[str, ...],
    recommended_route_families: tuple[str, ...],
    blocked_sides: tuple[str, ...],
    blocked_frameworks: tuple[str, ...],
    blocked_route_families: tuple[str, ...],
    risk_vetoed_sides: tuple[str, ...],
    side_risk_reasons: dict[str, str],
    side_decisions: list[GTOSVNextRuntimeDecision],
) -> dict[str, Any]:
    """Build the compact runtime role contract for the pre-AI LLM call.

    This is the runtime conversion of the LLM-specialization backlog's hybrid
    architecture: deterministic vNext evidence owns side/route/blocker
    selection, while the LLM is narrowed to source-safe validation and blocker
    classification.
    """
    enabled = bool(cfg.get("pre_ai_ai_role_context_enabled", True))
    role_action = (
        would_action
        if bool(cfg.get("pre_ai_ai_role_context_uses_would_action", True))
        else action
    )
    ai_role = _pre_ai_role_for_action(role_action, decision)
    metric_sums: dict[str, float] = {}
    decision_counts: Counter[str] = Counter()
    source_component_counts: Counter[str] = Counter()
    evidence_family_counts: Counter[str] = Counter()
    source_name_counts: Counter[str] = Counter()
    framework_counts: Counter[str] = Counter()
    route_family_counts: Counter[str] = Counter()
    matched_rows = 0
    matched_side_summaries: list[dict[str, Any]] = []
    max_side_summaries = int(_configured_float(cfg, "pre_ai_ai_role_context_side_limit", 4.0))
    first_event: dict[str, Any] = {}

    for side_decision in side_decisions:
        if side_decision.event and not first_event:
            first_event = dict(side_decision.event)
        evidence = side_decision.evidence or {}
        if isinstance(evidence, dict):
            matched_rows += int(evidence.get("matched_rows") or 0)
            _merge_numeric_counts(decision_counts, evidence.get("decision_counts"))
            _merge_numeric_counts(source_component_counts, evidence.get("source_component_counts"))
            _merge_numeric_counts(evidence_family_counts, evidence.get("evidence_family_counts"))
            _merge_numeric_counts(source_name_counts, evidence.get("source_name_counts"))
            _merge_numeric_counts(framework_counts, evidence.get("framework_counts"))
            _merge_numeric_counts(route_family_counts, evidence.get("route_family_counts"))
            for metric in METRIC_NAMES:
                value = _metric_value(evidence, metric)
                if value is not None:
                    metric_sums[metric] = metric_sums.get(metric, 0.0) + float(value)
        if side_decision.matched and len(matched_side_summaries) < max_side_summaries:
            side_summary = _risk_evidence_summary(side_decision)
            matched_side_summaries.append(
                {
                    "side": side_decision.event.get("side"),
                    "decision": side_decision.decision,
                    "matched_rows": side_summary["matched_rows"],
                    "cost_adjusted_simulated_r_sum": side_summary[
                        "cost_adjusted_simulated_r_sum"
                    ],
                    "proxy_score_sum": side_summary["proxy_score_sum"],
                    "stress_simulated_r_sum": side_summary["stress_simulated_r_sum"],
                    "effective_n_sum": side_summary["effective_n_sum"],
                    "framework_counts": side_summary["framework_counts"],
                    "route_family_counts": side_summary["route_family_counts"],
                    "source_component_counts": side_summary["source_component_counts"],
                }
            )

    source_path = str(
        cfg.get("pre_ai_ai_role_context_source_artifact_path")
        or DEFAULT_LLM_SPECIALIZATION_BACKLOG_PATH
    ).replace("\\", "/")
    pressure_test_enabled = bool(cfg.get("pre_ai_ai_role_pressure_test_enabled", True))
    pressure_test_steps = _configured_list(
        cfg,
        "pre_ai_ai_role_pressure_test_steps",
        ["critic_mode", "list_issues", "fix_or_reject", "state_what_was_fixed"],
    )
    scope_guard_enabled = bool(
        cfg.get("pre_ai_ai_role_per_instrument_scope_guard_enabled", True)
    )
    scope_guard = {
        "enabled": scope_guard_enabled,
        "per_instrument_required": True,
        "null_result_is_valid": bool(cfg.get("pre_ai_ai_role_null_result_is_valid", True)),
        "symbol": first_event.get("symbol"),
        "source_symbol": first_event.get("source_symbol"),
        "symbol_family": first_event.get("symbol_family"),
        "route_session": first_event.get("route_session"),
        "recommended_side": recommended_side,
        "recommended_frameworks": list(recommended_frameworks),
        "recommended_route_families": list(recommended_route_families),
        "source_artifact_path": ".context/01_knowledge_base/kb_prompt_engineering_patterns.md",
    }
    pressure_test = {
        "enabled": pressure_test_enabled,
        "steps": pressure_test_steps if pressure_test_enabled else [],
        "source_artifact_path": ".context/01_knowledge_base/kb_prompt_engineering_patterns.md",
    }
    return {
        "enabled": enabled,
        "ai_role": ai_role,
        "active_action": action,
        "selection_action": role_action,
        "would_action": would_action,
        "decision": decision,
        "recommended_side": recommended_side,
        "recommended_frameworks": list(recommended_frameworks),
        "recommended_route_families": list(recommended_route_families),
        "blocked_sides": list(blocked_sides),
        "blocked_frameworks": list(blocked_frameworks),
        "blocked_route_families": list(blocked_route_families),
        "risk_vetoed_sides": list(risk_vetoed_sides),
        "side_risk_reasons": dict(side_risk_reasons),
        "matched_rows": matched_rows,
        "metric_sums": metric_sums,
        "decision_counts": dict(decision_counts),
        "source_component_counts": dict(source_component_counts),
        "evidence_family_counts": dict(evidence_family_counts),
        "source_name_counts": dict(source_name_counts),
        "framework_counts": dict(framework_counts),
        "route_family_counts": dict(route_family_counts),
        "matched_side_summaries": matched_side_summaries,
        "source_artifact_path": source_path,
        "scope_guard": {
            key: value for key, value in scope_guard.items() if value not in (None, "")
        },
        "pressure_test": pressure_test,
        "source_directives": [
            "schema-valid GTOS-native decision formatting",
            "source/as-of obedience",
            "consistent blocker classification",
            "hybrid deterministic-selector plus LLM-validator architecture",
            "per-instrument scope only; do not generalize gold-only evidence",
            "null result is valid when source fields do not support the route",
        ],
        "role_instruction": _pre_ai_role_instruction(ai_role),
    }


def _format_count_dict(payload: dict[str, Any], *, limit: int = 5) -> str:
    if not payload:
        return "none"
    items = sorted(payload.items(), key=lambda item: (-float(item[1] or 0), str(item[0])))
    return ", ".join(f"{key}={value:g}" for key, value in items[:limit])


def _format_string_list(items: Iterable[Any]) -> str:
    values = [_normalized(item) for item in items if _normalized(item)]
    return ", ".join(values) if values else "none"


def format_vnext_ai_role_context_for_prompt(role_context: dict[str, Any] | None) -> str:
    """Render the compact vNext AI-role context injected before PrimaryAnalyzer."""
    if not isinstance(role_context, dict) or not role_context.get("enabled", False):
        return ""
    ai_role = _normalized(role_context.get("ai_role"))
    if not ai_role or ai_role == "general_trade_decision":
        return ""
    metric_sums = role_context.get("metric_sums", {})
    lines = [
        "## GTOS vNext Mechanical AI Role Context",
        f"Role: {ai_role}",
        f"Directive source: {role_context.get('source_artifact_path')}",
        (
            "Decision/action: "
            f"{role_context.get('decision')} / {role_context.get('selection_action')} "
            f"(active={role_context.get('active_action')}, "
            f"would={role_context.get('would_action')})"
        ),
        (
            "Route: "
            f"side={role_context.get('recommended_side') or 'none'}, "
            f"frameworks={_format_string_list(role_context.get('recommended_frameworks', []))}, "
            f"route_families={_format_string_list(role_context.get('recommended_route_families', []))}"
        ),
        (
            "Blocked: "
            f"sides={_format_string_list(role_context.get('blocked_sides', []))}, "
            f"frameworks={_format_string_list(role_context.get('blocked_frameworks', []))}, "
            f"route_families={_format_string_list(role_context.get('blocked_route_families', []))}"
        ),
        (
            "Evidence: "
            f"matched_rows={role_context.get('matched_rows', 0)}, "
            f"decision_counts={_format_count_dict(role_context.get('decision_counts', {}))}, "
            f"cost_adjusted_r_sum={metric_sums.get('cost_adjusted_simulated_r')}, "
            f"proxy_score_sum={metric_sums.get('proxy_score')}, "
            f"stress_r_sum={metric_sums.get('stress_simulated_r')}, "
            f"effective_n_sum={metric_sums.get('effective_n')}"
        ),
        (
            "Dominant dimensions: "
            f"frameworks={_format_count_dict(role_context.get('framework_counts', {}))}; "
            f"route_families={_format_count_dict(role_context.get('route_family_counts', {}))}; "
            f"source_components={_format_count_dict(role_context.get('source_component_counts', {}))}"
        ),
    ]
    scope_guard = role_context.get("scope_guard", {})
    if isinstance(scope_guard, dict) and scope_guard.get("enabled"):
        lines.append(
            "Scope guard: "
            "per-instrument evidence only; "
            f"symbol={scope_guard.get('symbol') or 'none'}, "
            f"source_symbol={scope_guard.get('source_symbol') or 'none'}, "
            f"family={scope_guard.get('symbol_family') or 'none'}, "
            f"session={scope_guard.get('route_session') or 'none'}, "
            f"null_result_is_valid={scope_guard.get('null_result_is_valid')}"
        )
    pressure_test = role_context.get("pressure_test", {})
    if isinstance(pressure_test, dict) and pressure_test.get("enabled"):
        lines.append(
            "Pressure test: "
            f"{' -> '.join(_configured_list(pressure_test, 'steps', []))}"
        )
    lines.append(f"Instruction: {role_context.get('role_instruction')}")
    return "\n".join(lines)


def _vnext_ai_policy_prompt_scope(
    *,
    pre_ai_decision: GTOSVNextPreAIRoutingDecision,
    role_context: dict[str, Any],
) -> dict[str, Any]:
    source_counts = role_context.get("source_component_counts", {})
    source_bound = bool(
        role_context.get("matched_rows")
        and (
            source_counts
            or role_context.get("source_artifact_path")
            or role_context.get("source_name_counts")
        )
    )
    return {
        "source_bound": source_bound,
        "recommended_side": pre_ai_decision.recommended_side,
        "recommended_frameworks": list(pre_ai_decision.recommended_frameworks),
        "recommended_route_families": list(pre_ai_decision.recommended_route_families),
        "blocked_sides": list(pre_ai_decision.blocked_sides),
        "blocked_frameworks": list(pre_ai_decision.blocked_frameworks),
        "blocked_route_families": list(pre_ai_decision.blocked_route_families),
        "matched_rows": role_context.get("matched_rows", 0),
        "source_component_counts": dict(source_counts) if isinstance(source_counts, dict) else {},
        "decision_counts": dict(role_context.get("decision_counts", {}))
        if isinstance(role_context.get("decision_counts"), dict)
        else {},
        "scope_guard": dict(role_context.get("scope_guard", {}))
        if isinstance(role_context.get("scope_guard"), dict)
        else {},
    }


def _vnext_ai_policy_schema_contract(
    *,
    action: AIPolicyAction,
    pre_ai_decision: GTOSVNextPreAIRoutingDecision,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    candidate_directions: list[str] = []
    if pre_ai_decision.recommended_side:
        candidate_directions = [pre_ai_decision.recommended_side]
    allowed_frameworks = list(pre_ai_decision.recommended_frameworks)
    if action == "CALL_AI_FRAMEWORK_SCREENER":
        allowed_frameworks = list(pre_ai_decision.recommended_frameworks)
    return {
        "schema_version": AI_RELIABILITY_CONTRACT_SCHEMA_VERSION,
        "schema_name": "PrimaryAnalysisOutput",
        "schema_validation_required": bool(cfg.get("ai_policy_schema_validation_required", True)),
        "model_version_contract": build_model_version_contract(
            requested_model=cfg.get("primary_model") or cfg.get("ai_policy_model")
        ),
        "allowed_decisions": ["NO_TRADE", "CANDIDATE", "WAIT"]
        if action.startswith("CALL_AI")
        else ["NO_TRADE"],
        "candidate_directions": candidate_directions,
        "candidate_frameworks": allowed_frameworks,
        "candidate_must_obey_prompt_scope": action
        in {
            "CALL_AI_CONSTRAINED_VALIDATOR",
            "CALL_AI_NARROWED_ROUTE",
            "CALL_AI_FRAMEWORK_SCREENER",
            "CALL_AI_MIXED_RESOLUTION",
        },
        "deterministic_baseline_contract": build_deterministic_baseline_contract(
            reason="vnext_ai_policy_mechanical_first_baseline"
        ),
        "disagreement_calibration_contract": build_disagreement_calibration_contract(),
        "semantic_ownership_handoff": build_semantic_ownership_handoff(),
        "malformed_response_demotes_to_no_trade": True,
        "semantic_repair_must_preserve_trade_fields": True,
    }


def _vnext_ai_policy_cache_contract(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "vnext_ai_policy_cache_contract_v2",
        "prompt_packet_hash_required": bool(
            cfg.get("ai_policy_prompt_hash_logging_required", True)
        ),
        "ai_decision_trace_hash_required": True,
        "content_addressed_cache_required": bool(
            cfg.get("ai_policy_content_addressed_cache_required", True)
        ),
        "paid_calls_require_ai_call_policy": True,
        "no_paid_call_harness_only_until_owner_approval": True,
    }


def _vnext_ai_policy_would_action(
    *,
    pre_ai_decision: GTOSVNextPreAIRoutingDecision,
    cfg: dict[str, Any],
    risk_tier: str,
    prompt_scope: dict[str, Any],
) -> tuple[AIPolicyAction, str]:
    pre_action = pre_ai_decision.action
    would_pre_action = pre_ai_decision.would_action
    decision = pre_ai_decision.decision
    if pre_action == "SKIP_AI_AVOID_ONLY" or would_pre_action == "SKIP_AI_AVOID_ONLY":
        return "SKIP_AI_MECHANICAL_AVOID", "mechanical_avoid_skips_ai"

    if pre_action == "NARROW_AI_EXCLUDE_FRAMEWORKS" or would_pre_action == "NARROW_AI_EXCLUDE_FRAMEWORKS":
        return "CALL_AI_FRAMEWORK_SCREENER", "mechanical_framework_exclusion_screens_ai_scope"

    if pre_action in {"NARROW_AI_TO_SIDE", "NARROW_AI_TO_ROUTE"} or would_pre_action in {
        "NARROW_AI_TO_SIDE",
        "NARROW_AI_TO_ROUTE",
    }:
        return "CALL_AI_NARROWED_ROUTE", "mechanical_route_narrows_ai_scope"

    if decision == "FOLLOW":
        no_ai_enabled = bool(cfg.get("ai_policy_follow_no_ai_enabled", False))
        validator_tiers = {
            _normalized(item).casefold()
            for item in _configured_list(
                cfg,
                "ai_policy_follow_validator_risk_tiers",
                ["standard", "elevated", "high", "funded_prop"],
            )
        }
        if no_ai_enabled and risk_tier.casefold() not in validator_tiers:
            return "MECHANICAL_FOLLOW_NO_AI", "mechanical_follow_low_risk_no_ai"
        return "CALL_AI_CONSTRAINED_VALIDATOR", "mechanical_follow_uses_constrained_validator"

    if decision == "MIXED":
        allow_mixed = bool(cfg.get("ai_policy_allow_mixed_ai_resolution", True))
        source_required = bool(
            cfg.get("ai_policy_mixed_resolution_requires_source_bound_fields", True)
        )
        if allow_mixed and (prompt_scope.get("source_bound") or not source_required):
            return "CALL_AI_MIXED_RESOLUTION", "source_bound_mixed_context_uses_ai_resolution"
        return "BLOCK_LEGACY_BROAD_FALLBACK", "mixed_context_missing_source_bound_fields"

    if decision == "LEGACY":
        allow_legacy = bool(cfg.get("ai_policy_allow_legacy_broad_fallback", False))
        replayed_required = bool(cfg.get("ai_policy_legacy_requires_replayed_scope", True))
        replayed = bool(prompt_scope.get("legacy_replayed_scope"))
        if allow_legacy and (replayed or not replayed_required):
            return "CALL_AI_LEGACY_REPLAYED", "legacy_ai_scope_explicitly_replayed"
        return "BLOCK_LEGACY_BROAD_FALLBACK", "legacy_broad_ai_fallback_not_replayed"

    return "CALL_AI_CONSTRAINED_VALIDATOR", "default_constrained_validator"


def evaluate_vnext_ai_policy(
    *,
    pre_ai_decision: GTOSVNextPreAIRoutingDecision,
    config: dict[str, Any] | None,
    raw_data: dict[str, Any] | None = None,
    risk_tier: str | None = None,
) -> GTOSVNextAIPolicyDecision:
    """Return the mechanical-first vNext AI policy decision for one event.

    The returned ``would_action`` is the production-change policy. The active
    ``action`` preserves the current path while ``ai_policy_apply_to_ai_call``
    remains false, so Stage07 can be replayed and audited before any broker-
    facing or paid-call behavior changes are activated.
    """
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    enabled = bool(cfg.get("ai_policy_enabled", cfg.get("pre_ai_enabled", False)))
    apply_to_ai_call = bool(cfg.get("ai_policy_apply_to_ai_call", False))
    role_context = dict(pre_ai_decision.ai_role_context or {})
    prompt_scope = _vnext_ai_policy_prompt_scope(
        pre_ai_decision=pre_ai_decision,
        role_context=role_context,
    )
    if isinstance(raw_data, dict):
        for key in (
            "legacy_replayed_scope",
            "replay_scope_id",
            "source_packet_id",
            "candidate_id",
        ):
            if raw_data.get(key) not in (None, ""):
                prompt_scope[key] = raw_data.get(key)
    resolved_risk_tier = _normalized(
        risk_tier
        or (raw_data or {}).get("risk_tier")
        or (raw_data or {}).get("prop_risk_tier")
        or "standard"
    ).casefold()

    if not enabled:
        return GTOSVNextAIPolicyDecision(
            action="CALL_AI_CURRENT_PATH",
            would_action="CALL_AI_CURRENT_PATH",
            allowed=True,
            would_allow_ai_call=True,
            enabled=False,
            apply_to_ai_call=False,
            reason="vnext_ai_policy_disabled",
            ai_role="general_trade_decision",
            prompt_scope=prompt_scope,
            schema_contract=_vnext_ai_policy_schema_contract(
                action="CALL_AI_CURRENT_PATH",
                pre_ai_decision=pre_ai_decision,
                cfg=cfg,
            ),
            cache_contract=_vnext_ai_policy_cache_contract(cfg),
            evidence={"policy_enabled": False},
        )

    would_action, reason = _vnext_ai_policy_would_action(
        pre_ai_decision=pre_ai_decision,
        cfg=cfg,
        risk_tier=resolved_risk_tier,
        prompt_scope=prompt_scope,
    )
    would_allow = would_action.startswith("CALL_AI")
    active_action = would_action if (apply_to_ai_call or would_allow) else "CALL_AI_CURRENT_PATH"
    allowed = would_allow or not apply_to_ai_call
    ai_role = _normalized(role_context.get("ai_role")) or _pre_ai_role_for_action(
        pre_ai_decision.would_action,
        pre_ai_decision.decision,
    )
    if would_action == "CALL_AI_CONSTRAINED_VALIDATOR" and ai_role == "general_trade_decision":
        ai_role = "vnext_evidence_triage"
    elif would_action == "CALL_AI_MIXED_RESOLUTION":
        ai_role = "vnext_mixed_resolution_validator"
    elif would_action == "MECHANICAL_FOLLOW_NO_AI":
        ai_role = "mechanical_follow_no_ai"

    return GTOSVNextAIPolicyDecision(
        action=active_action,
        would_action=would_action,
        allowed=allowed,
        would_allow_ai_call=would_allow,
        enabled=True,
        apply_to_ai_call=apply_to_ai_call,
        reason=reason,
        ai_role=ai_role,
        prompt_scope=prompt_scope,
        schema_contract=_vnext_ai_policy_schema_contract(
            action=would_action,
            pre_ai_decision=pre_ai_decision,
            cfg=cfg,
        ),
        cache_contract=_vnext_ai_policy_cache_contract(cfg),
        evidence={
            "pre_ai_action": pre_ai_decision.action,
            "pre_ai_would_action": pre_ai_decision.would_action,
            "pre_ai_decision": pre_ai_decision.decision,
            "risk_tier": resolved_risk_tier,
            "source_artifact_path": "research/science_program_2026_05/04_goal_prompts/"
            "VNEXT_PRODUCTION_CHANGE_DOSSIER_AND_PROP_SAFE_RUNTIME_GOAL_PROMPT_2026-05-25.md",
            "mechanical_first_policy": True,
        },
    )


def _vnext_ai_policy_record(
    policy_context: GTOSVNextAIPolicyDecision | dict[str, Any] | None,
) -> dict[str, Any]:
    if policy_context is None:
        return {}
    if isinstance(policy_context, GTOSVNextAIPolicyDecision):
        return policy_context.to_record()
    if isinstance(policy_context, dict):
        return dict(policy_context)
    return {}


def vnext_ai_policy_allows_no_paid_mechanical_follow(
    policy_context: GTOSVNextAIPolicyDecision | dict[str, Any] | None,
) -> bool:
    """Return true only when the policy explicitly resolves FOLLOW without AI."""
    record = _vnext_ai_policy_record(policy_context)
    actions = {
        str(record.get("action") or ""),
        str(record.get("would_action") or ""),
    }
    return bool(actions & {"MECHANICAL_FOLLOW_NO_AI", "FOLLOW_WITHOUT_AI"})


def vnext_ai_policy_requires_paid_call(
    policy_context: GTOSVNextAIPolicyDecision | dict[str, Any] | None,
) -> bool:
    """Return true for policy branches that need a real AI call to decide."""
    record = _vnext_ai_policy_record(policy_context)
    if bool(record.get("would_allow_ai_call")):
        return True
    would_action = str(record.get("would_action") or record.get("action") or "")
    return would_action.startswith("CALL_AI")


def vnext_ai_policy_no_paid_call_replay_decision(
    policy_context: GTOSVNextAIPolicyDecision | dict[str, Any] | None,
    *,
    production_selected: bool,
) -> dict[str, Any]:
    """Classify a no-paid-call replay row without turning diagnostics into trades."""
    record = _vnext_ai_policy_record(policy_context)
    would_action = str(record.get("would_action") or record.get("action") or "UNKNOWN")
    if not production_selected:
        return {
            "selected": False,
            "reason": "no_paid_ai_not_in_production_selected_stream",
            "status": "diagnostic_not_production_selected",
            "diagnostic_only": True,
        }
    if vnext_ai_policy_allows_no_paid_mechanical_follow(record):
        return {
            "selected": True,
            "reason": "selected_mechanical_follow_no_ai",
            "status": "mechanical_follow_no_paid_selected",
            "diagnostic_only": False,
        }
    if vnext_ai_policy_requires_paid_call(record):
        return {
            "selected": False,
            "reason": "no_paid_ai_required_diagnostic_only",
            "status": "diagnostic_ai_required_not_selected",
            "diagnostic_only": True,
        }
    return {
        "selected": False,
        "reason": f"no_paid_ai_{would_action.lower()}",
        "status": "diagnostic_mechanical_no_trade_not_selected",
        "diagnostic_only": True,
    }


def format_vnext_ai_policy_context_for_prompt(
    policy_context: GTOSVNextAIPolicyDecision | dict[str, Any] | None,
) -> str:
    """Render a compact AI-policy contract for the PrimaryAnalyzer prompt."""
    if policy_context is None:
        return ""
    record = _vnext_ai_policy_record(policy_context)
    if not record or not record.get("enabled", False):
        return ""
    prompt_scope = record.get("prompt_scope", {})
    schema_contract = record.get("schema_contract", {})
    cache_contract = record.get("cache_contract", {})
    lines = [
        "## GTOS vNext AI Policy Contract",
        (
            "AI policy action: "
            f"{record.get('would_action')} "
            f"(active={record.get('action')}, allowed={record.get('allowed')})"
        ),
        f"AI role: {record.get('ai_role')}",
        f"Reason: {record.get('reason')}",
        (
            "Prompt scope: "
            f"side={prompt_scope.get('recommended_side') or 'none'}, "
            f"frameworks={_format_string_list(prompt_scope.get('recommended_frameworks', []))}, "
            f"route_families={_format_string_list(prompt_scope.get('recommended_route_families', []))}, "
            f"blocked_frameworks={_format_string_list(prompt_scope.get('blocked_frameworks', []))}, "
            f"source_bound={prompt_scope.get('source_bound')}"
        ),
        (
            "Schema contract: "
            f"{schema_contract.get('schema_name')}; "
            f"allowed_decisions={_format_string_list(schema_contract.get('allowed_decisions', []))}; "
            f"candidate_directions={_format_string_list(schema_contract.get('candidate_directions', []))}; "
            f"candidate_frameworks={_format_string_list(schema_contract.get('candidate_frameworks', []))}"
        ),
        (
            "Hash/cache contract: "
            f"prompt_packet_hash_required={cache_contract.get('prompt_packet_hash_required')}, "
            f"ai_trace_hash_required={cache_contract.get('ai_decision_trace_hash_required')}, "
            f"paid_calls_require_ai_call_policy={cache_contract.get('paid_calls_require_ai_call_policy')}"
        ),
        "Instruction: stay inside the prompt scope; reject or wait rather than inventing an unscoped trade.",
    ]
    return "\n".join(lines)


def evaluate_pre_ai_vnext(
    *,
    symbol: str,
    source_symbol: str | None,
    kill_zone: str,
    config: dict[str, Any] | None,
    bias: str | None = None,
    raw_data: dict[str, Any] | None = None,
    artifact_rows: list[dict[str, Any]] | None = None,
    artifact_index: GTOSVNextEvidenceIndex | None = None,
) -> GTOSVNextPreAIRoutingDecision:
    """Evaluate vNext before the AI call using only current event fields."""
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    enabled = bool(cfg.get("pre_ai_enabled", cfg.get("enabled", False)))
    apply_to_ai_call = bool(cfg.get("pre_ai_apply_to_ai_call", False))
    base_event = build_vnext_pre_ai_event(
        symbol=symbol,
        source_symbol=source_symbol,
        kill_zone=kill_zone,
        config=config,
        bias=bias,
        raw_data=raw_data,
    )
    asian_sweep_context = _xau_asian_sweep_continuation_context(base_event, raw_data, cfg)

    if not enabled:
        return GTOSVNextPreAIRoutingDecision(
            action="ALLOW_AI",
            decision="LEGACY",
            enabled=False,
            apply_to_ai_call=False,
            reason="gtos_vnext_pre_ai_disabled",
            event=normalize_event(base_event),
        )

    bias_side = _side_from_bias(bias)
    sides = [bias_side] if bias_side else []
    if bool(cfg.get("pre_ai_evaluate_all_sides", False)):
        sides = ["LONG", "SHORT"]
    if (
        asian_sweep_context
        and bool(cfg.get("pre_ai_xau_asian_sweep_evaluate_continuation_side", True))
    ):
        continuation_side = _normalized(asian_sweep_context.get("continuation_side"))
        if continuation_side and continuation_side not in sides:
            sides.append(continuation_side)
    if not sides:
        return GTOSVNextPreAIRoutingDecision(
            action="ALLOW_AI",
            decision="LEGACY",
            enabled=True,
            apply_to_ai_call=apply_to_ai_call,
            reason="no_pre_ai_side_available",
            event=normalize_event(base_event),
        )

    paths = _configured_artifact_paths(config)
    if artifact_rows is not None:
        first_path = str(paths[0]) if paths else "in_memory"
        active_index = GTOSVNextEvidenceIndex.from_rows(
            [dict(row) for row in artifact_rows],
            artifact_paths=tuple(str(path) for path in paths),
            rows_loaded_by_path={first_path: len(artifact_rows)},
        )
    else:
        active_index = artifact_index or load_vnext_evidence_index(paths)

    if _evidence_index_below_min_rows(active_index, cfg):
        return GTOSVNextPreAIRoutingDecision(
            action="ALLOW_AI",
            decision="LEGACY",
            enabled=True,
            apply_to_ai_call=apply_to_ai_call,
            reason="vnext_evidence_index_below_min_loaded_rows",
            event=normalize_event(base_event),
            would_action="ALLOW_AI",
        )

    side_decisions = [
        _side_decision_from_route_events(
            side=side,
            base_event=build_vnext_pre_ai_event(
                symbol=symbol,
                source_symbol=source_symbol,
                kill_zone=kill_zone,
                config=config,
                bias=bias,
                side=side,
                raw_data=raw_data,
            ),
            config=config,
            cfg=cfg,
            artifact_index=active_index,
        )
        for side in sides
    ]
    decision = _collapse_pre_ai_side_decisions(side_decisions)
    (
        would_action,
        recommended_side,
        blocked_sides,
        recommended_frameworks,
        recommended_route_families,
        blocked_frameworks,
        blocked_route_families,
        risk_vetoed_sides,
        side_risk_reasons,
    ) = _pre_ai_recommendation(
        side_decisions,
        bias_side=bias_side,
        skip_bias_avoid=bool(cfg.get("pre_ai_skip_when_bias_side_avoid", True)),
        cfg=cfg,
    )
    (
        decision,
        would_action,
        recommended_side,
        blocked_sides,
        recommended_frameworks,
        recommended_route_families,
        side_risk_reasons,
    ) = _apply_xau_asian_sweep_continuation_rule(
        sweep_context=asian_sweep_context,
        decision=decision,
        would_action=would_action,
        recommended_side=recommended_side,
        blocked_sides=tuple(blocked_sides),
        recommended_frameworks=tuple(recommended_frameworks),
        recommended_route_families=tuple(recommended_route_families),
        blocked_frameworks=tuple(blocked_frameworks),
        blocked_route_families=tuple(blocked_route_families),
        risk_vetoed_sides=tuple(risk_vetoed_sides),
        side_risk_reasons=side_risk_reasons,
    )
    action = would_action if apply_to_ai_call else "ALLOW_AI"
    reason = "matched_pre_ai_vnext_scope" if decision != "LEGACY" else "no_matching_pre_ai_vnext_scope"
    if action == "SKIP_AI_AVOID_ONLY":
        reason = "pre_ai_vnext_avoid_only"
    elif action == "NARROW_AI_TO_SIDE":
        reason = f"pre_ai_vnext_route_to_{recommended_side}"
    elif action == "NARROW_AI_TO_ROUTE":
        route_text = (
            "+".join(recommended_frameworks)
            if recommended_frameworks
            else "+".join(recommended_route_families)
            if recommended_route_families
            else "any_route"
        )
        reason = f"pre_ai_vnext_route_to_{recommended_side}_{route_text}"
    elif action == "NARROW_AI_EXCLUDE_FRAMEWORKS":
        framework_text = "+".join(blocked_frameworks) if blocked_frameworks else "none"
        reason = f"pre_ai_vnext_exclude_frameworks_{framework_text}"

    ai_role_context = _pre_ai_ai_role_context(
        cfg=cfg,
        action=action,
        would_action=would_action,
        decision=decision,
        recommended_side=recommended_side,
        recommended_frameworks=tuple(recommended_frameworks),
        recommended_route_families=tuple(recommended_route_families),
        blocked_sides=tuple(blocked_sides),
        blocked_frameworks=tuple(blocked_frameworks),
        blocked_route_families=tuple(blocked_route_families),
        risk_vetoed_sides=tuple(sorted(risk_vetoed_sides)),
        side_risk_reasons=side_risk_reasons,
        side_decisions=side_decisions,
    )
    if asian_sweep_context:
        ai_role_context.setdefault("runtime_rules", {})[
            "xau_asian_sweep_continuation"
        ] = dict(asian_sweep_context)

    return GTOSVNextPreAIRoutingDecision(
        action=action,
        decision=decision,
        enabled=True,
        apply_to_ai_call=apply_to_ai_call,
        reason=reason,
        event=normalize_event(base_event),
        recommended_side=recommended_side,
        recommended_frameworks=tuple(recommended_frameworks),
        recommended_route_families=tuple(recommended_route_families),
        blocked_sides=tuple(blocked_sides),
        blocked_frameworks=tuple(blocked_frameworks),
        blocked_route_families=tuple(blocked_route_families),
        risk_vetoed_sides=tuple(risk_vetoed_sides),
        side_risk_reasons=side_risk_reasons,
        evaluated_sides=tuple(sides),
        would_action=would_action,
        side_decisions=tuple(side_decisions),
        ai_role_context=ai_role_context,
    )


def evaluate_candidate_vnext(
    *,
    analysis: Any,
    raw_data: dict[str, Any] | None,
    kill_zone: str,
    config: dict[str, Any] | None,
    symbol: str,
    source_symbol: str | None = None,
) -> GTOSVNextRuntimeDecision:
    event = build_vnext_event_from_candidate(
        analysis=analysis,
        raw_data=raw_data,
        kill_zone=kill_zone,
        symbol=symbol,
        source_symbol=source_symbol,
        config=config,
    )
    return evaluate_vnext_route_event(event, config)


def _decision_log_path(config: dict[str, Any] | None) -> Path:
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    return Path(str(cfg.get("decision_log_path") or DEFAULT_DECISION_LOG_PATH))


def _vnext_bridge_packet_summary(decision: Any) -> dict[str, Any]:
    if not isinstance(decision, GTOSVNextMoonshotDynamicExecutionDecision):
        return {}
    source_event = decision.source_event if isinstance(decision.source_event, dict) else {}
    candidate_quality = source_event.get("candidate_quality_selector")
    if not isinstance(candidate_quality, dict):
        candidate_quality = {}
    selected_cell_risk = {
        key: source_event.get(key)
        for key in (
            "selected_cell_risk_required",
            "selected_cell_risk_allowed",
            "selected_cell_risk_pct",
            "selected_cell_risk_cell_id",
            "selected_cell_risk_decision_basis",
            "selected_cell_risk_match_reason",
            "selected_cell_risk_refusal_cause",
            "selected_cell_risk_failed_dimensions",
            "selected_cell_risk_nearest_candidate",
            "selected_cell_risk_unresolved_reasons",
            "selected_cell_risk_execution_critical_unresolved_reasons",
            "selected_cell_risk_source_ledger_path",
            "selected_cell_risk_source_row_identity",
            "selected_cell_risk_capture_contract",
            "selected_cell_risk_selected_policy",
            "selected_cell_risk_source_policy",
            "selected_cell_risk_execution_policy_id",
            "selected_cell_risk_policy_identity_status",
            "selected_cell_risk_ledger_rows",
            "selected_cell_risk_ledger_load_status",
        )
        if source_event.get(key) is not None
    }
    return {
        "schema_version": "gtos_vnext_runtime_bridge_packet_summary_v1",
        "selected_policy": decision.selected_policy,
        "execution_policy_id": decision.execution_policy_id,
        "candidate_action": decision.candidate_action,
        "candidate_use_allowed_now": decision.candidate_use_allowed_now,
        "candidate_id": source_event.get("candidate_id"),
        "symbol": source_event.get("symbol") or source_event.get("source_symbol"),
        "broker_symbol": source_event.get("broker_symbol"),
        "side": source_event.get("side") or source_event.get("direction"),
        "session": source_event.get("session"),
        "kill_zone": source_event.get("kill_zone"),
        "route_session": source_event.get("route_session"),
        "origin_family": source_event.get("origin_family"),
        "candidate_origin_family": source_event.get("candidate_origin_family"),
        "framework": source_event.get("framework")
        or source_event.get("effective_framework"),
        "route_family": source_event.get("route_family"),
        "source_quality_action": decision.source_quality_action,
        "prop_action": decision.prop_action,
        "exit_management_action": decision.exit_management_action,
        "target_stop_geometry_v4": dict(decision.target_stop_geometry_v4),
        "broader_origin_allowed": source_event.get("broader_origin_allowed"),
        "broader_origin_match_reason": source_event.get("broader_origin_match_reason"),
        "broader_origin_source_row_identity": source_event.get(
            "broader_origin_source_row_identity"
        ),
        "selected_cell_risk_allowed": source_event.get("selected_cell_risk_allowed"),
        "selected_cell_risk_pct": source_event.get("selected_cell_risk_pct"),
        "selected_cell_risk_cell_id": source_event.get("selected_cell_risk_cell_id"),
        "selected_cell_risk_match_reason": source_event.get(
            "selected_cell_risk_match_reason"
        ),
        "selected_cell_risk_refusal_cause": source_event.get(
            "selected_cell_risk_refusal_cause"
        ),
        "selected_cell_risk_source_row_identity": source_event.get(
            "selected_cell_risk_source_row_identity"
        ),
        "selected_cell_risk_capture_contract": source_event.get(
            "selected_cell_risk_capture_contract"
        ),
        "selected_cell_risk": selected_cell_risk,
        "candidate_quality_classification": candidate_quality.get("classification"),
        "candidate_quality_refusal_reason": candidate_quality.get("refusal_reason"),
        "candidate_quality_matched_rule_id": (
            (candidate_quality.get("matched_rule") or {}).get("rule_id")
            if isinstance(candidate_quality.get("matched_rule"), dict)
            else None
        ),
        "spread_r_at_candidate": source_event.get("spread_r_at_candidate"),
        "raw_geometry": source_event.get("raw_geometry"),
        "trade_parameters": source_event.get("trade_parameters"),
        "m15_source_fields": source_event.get("m15_source_fields"),
        "mso_context": source_event.get("mso_context"),
        "tick_snapshot": source_event.get("tick_snapshot"),
        "broker_snapshot": source_event.get("broker_snapshot"),
        "source_completeness_state": {
            "source_mode": source_event.get("source_mode"),
            "source_path_feature_status": source_event.get("source_path_feature_status"),
            "source_window_complete": source_event.get("source_window_complete"),
            "ordered_path_status": source_event.get("ordered_path_status"),
            "selected_policy_ordered_path_status": source_event.get(
                "selected_policy_ordered_path_status"
            ),
        },
        "refusal_reasons": list(decision.refusal_reasons),
    }


def record_vnext_runtime_decision(
    *,
    decision: (
        GTOSVNextRuntimeDecision
        | GTOSVNextPreAIRoutingDecision
        | GTOSVNextMoonshotDynamicExecutionDecision
    ),
    config: dict[str, Any] | None,
    phase: str,
    symbol: str,
    kill_zone: str,
    candle_time_utc: str | None = None,
    log_path: Path | str | None = None,
) -> None:
    """Append one structured vNext runtime decision row."""
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    if not bool(cfg.get("decision_log_enabled", True)):
        return
    target = Path(log_path) if log_path is not None else _decision_log_path(config)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "schema_version": "gtos_vnext_runtime_decision_v1",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "phase": phase,
            "symbol": symbol,
            "kill_zone": kill_zone,
            "candle_time_utc": candle_time_utc,
            "decision": decision.to_record(),
        }
        bridge_summary = _vnext_bridge_packet_summary(decision)
        if bridge_summary:
            row["bridge_packet_summary"] = bridge_summary
        _append_jsonl_locked(target, row)
    except Exception as exc:  # noqa: BLE001 - logging must not break trading.
        logger.warning("GTOS vNext decision log failed: %s", exc)


def attach_vnext_decision_to_record(
    record: dict[str, Any],
    decision: GTOSVNextRuntimeDecision,
) -> dict[str, Any]:
    """Attach the vNext runtime decision to an existing trade record."""
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["gtos_vnext_runtime"] = decision.to_record()
    inst = record.setdefault("instrumentation", {})
    inst["gtos_vnext_decision"] = decision.decision
    inst["gtos_vnext_matched"] = decision.matched
    inst["gtos_vnext_apply_to_execution"] = decision.apply_to_execution
    return record


def attach_vnext_pre_ai_to_record(
    record: dict[str, Any],
    decision: GTOSVNextPreAIRoutingDecision,
) -> dict[str, Any]:
    """Attach the pre-AI vNext route decision to a candidate trade record."""
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["gtos_vnext_pre_ai"] = decision.to_record()
    inst = record.setdefault("instrumentation", {})
    inst["gtos_vnext_pre_ai_action"] = decision.action
    inst["gtos_vnext_pre_ai_decision"] = decision.decision
    inst["gtos_vnext_pre_ai_apply_to_ai_call"] = decision.apply_to_ai_call
    inst["gtos_vnext_pre_ai_would_action"] = decision.would_action
    inst["gtos_vnext_pre_ai_recommended_side"] = decision.recommended_side
    inst["gtos_vnext_pre_ai_recommended_frameworks"] = list(decision.recommended_frameworks)
    inst["gtos_vnext_pre_ai_recommended_route_families"] = list(
        decision.recommended_route_families
    )
    inst["gtos_vnext_pre_ai_blocked_sides"] = list(decision.blocked_sides)
    inst["gtos_vnext_pre_ai_blocked_frameworks"] = list(decision.blocked_frameworks)
    inst["gtos_vnext_pre_ai_blocked_route_families"] = list(decision.blocked_route_families)
    inst["gtos_vnext_pre_ai_risk_vetoed_sides"] = list(decision.risk_vetoed_sides)
    inst["gtos_vnext_pre_ai_side_risk_reasons"] = dict(decision.side_risk_reasons)
    role_context = dict(decision.ai_role_context or {})
    inst["gtos_vnext_pre_ai_ai_role"] = role_context.get("ai_role")
    inst["gtos_vnext_pre_ai_ai_role_source"] = role_context.get("source_artifact_path")
    inst["gtos_vnext_pre_ai_ai_role_matched_rows"] = role_context.get("matched_rows")
    return record


def attach_vnext_ai_policy_to_record(
    record: dict[str, Any],
    decision: GTOSVNextAIPolicyDecision,
) -> dict[str, Any]:
    """Attach the Stage07 vNext AI policy decision to a trade record."""
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["gtos_vnext_ai_policy"] = decision.to_record()
    inst = record.setdefault("instrumentation", {})
    inst["gtos_vnext_ai_policy_action"] = decision.action
    inst["gtos_vnext_ai_policy_would_action"] = decision.would_action
    inst["gtos_vnext_ai_policy_allowed"] = decision.allowed
    inst["gtos_vnext_ai_policy_would_allow_ai_call"] = decision.would_allow_ai_call
    inst["gtos_vnext_ai_policy_apply_to_ai_call"] = decision.apply_to_ai_call
    inst["gtos_vnext_ai_policy_reason"] = decision.reason
    inst["gtos_vnext_ai_policy_role"] = decision.ai_role
    inst["gtos_vnext_ai_policy_prompt_scope"] = dict(decision.prompt_scope)
    return record


def _metric_value(evidence: dict[str, Any], metric: str, field: str = "sum") -> float | None:
    metrics = evidence.get("metrics", {}) if isinstance(evidence, dict) else {}
    metric_payload = metrics.get(metric) if isinstance(metrics, dict) else None
    if isinstance(metric_payload, dict):
        return _to_float(metric_payload.get(field))
    return None


def _source_component_summary_prior_payload(evidence: dict[str, Any]) -> dict[str, Any]:
    prior = evidence.get("source_component_summary_prior") if isinstance(evidence, dict) else None
    return prior if isinstance(prior, dict) else {}


def _recommendation_bucket_prior_payload(evidence: dict[str, Any]) -> dict[str, Any]:
    prior = evidence.get("recommendation_bucket_prior") if isinstance(evidence, dict) else None
    return prior if isinstance(prior, dict) else {}


def _recommendation_family_rollup_prior_payload(evidence: dict[str, Any]) -> dict[str, Any]:
    prior = evidence.get("recommendation_family_rollup_prior") if isinstance(evidence, dict) else None
    return prior if isinstance(prior, dict) else {}


def _recommendation_unified_candidate_prior_payload(evidence: dict[str, Any]) -> dict[str, Any]:
    prior = evidence.get("recommendation_unified_candidate_prior") if isinstance(evidence, dict) else None
    return prior if isinstance(prior, dict) else {}


def _recommendation_scope_rollup_prior_payload(evidence: dict[str, Any]) -> dict[str, Any]:
    prior = evidence.get("recommendation_scope_rollup_prior") if isinstance(evidence, dict) else None
    return prior if isinstance(prior, dict) else {}


def _risk_evidence_summary(decision: GTOSVNextRuntimeDecision) -> dict[str, Any]:
    evidence = decision.evidence or {}
    component_prior = _source_component_summary_prior_payload(evidence)
    recommendation_prior = _recommendation_bucket_prior_payload(evidence)
    family_rollup_prior = _recommendation_family_rollup_prior_payload(evidence)
    unified_candidate_prior = _recommendation_unified_candidate_prior_payload(evidence)
    scope_rollup_prior = _recommendation_scope_rollup_prior_payload(evidence)
    summary = {
        "matched": decision.matched,
        "matched_rows": evidence.get("matched_rows", 0) if isinstance(evidence, dict) else 0,
        "decision_counts": evidence.get("decision_counts", {}) if isinstance(evidence, dict) else {},
        "cost_adjusted_simulated_r_sum": _metric_value(evidence, "cost_adjusted_simulated_r"),
        "cost_adjusted_simulated_r_mean": _metric_value(evidence, "cost_adjusted_simulated_r", "mean"),
        "stress_simulated_r_sum": _metric_value(evidence, "stress_simulated_r"),
        "stress_simulated_r_mean": _metric_value(evidence, "stress_simulated_r", "mean"),
        "proxy_score_sum": _metric_value(evidence, "proxy_score"),
        "proxy_score_mean": _metric_value(evidence, "proxy_score", "mean"),
        "effective_n_sum": _metric_value(evidence, "effective_n"),
        "source_name_counts": evidence.get("source_name_counts", {}) if isinstance(evidence, dict) else {},
        "evidence_family_counts": evidence.get("evidence_family_counts", {}) if isinstance(evidence, dict) else {},
        "source_component_counts": evidence.get("source_component_counts", {}) if isinstance(evidence, dict) else {},
        "source_role_decision_counts": (
            evidence.get("source_role_decision_counts", {}) if isinstance(evidence, dict) else {}
        ),
        "market_timeframe_counts": evidence.get("market_timeframe_counts", {}) if isinstance(evidence, dict) else {},
        "route_session_counts": evidence.get("route_session_counts", {}) if isinstance(evidence, dict) else {},
        "horizon_id_counts": evidence.get("horizon_id_counts", {}) if isinstance(evidence, dict) else {},
        "side_counts": evidence.get("side_counts", {}) if isinstance(evidence, dict) else {},
        "framework_counts": evidence.get("framework_counts", {}) if isinstance(evidence, dict) else {},
        "route_family_counts": evidence.get("route_family_counts", {}) if isinstance(evidence, dict) else {},
        "route_family_decision_counts": (
            evidence.get("route_family_decision_counts", {}) if isinstance(evidence, dict) else {}
        ),
        "proxy_r_class_counts": evidence.get("proxy_r_class_counts", {}) if isinstance(evidence, dict) else {},
        "r_evidence_class_counts": evidence.get("r_evidence_class_counts", {}) if isinstance(evidence, dict) else {},
        "source_group_counts": evidence.get("source_group_counts", {}) if isinstance(evidence, dict) else {},
        "source_role_counts": evidence.get("source_role_counts", {}) if isinstance(evidence, dict) else {},
        "system_surface_counts": evidence.get("system_surface_counts", {}) if isinstance(evidence, dict) else {},
        "implementation_action_counts": (
            evidence.get("implementation_action_counts", {}) if isinstance(evidence, dict) else {}
        ),
        "target_stop_order_class_counts": (
            evidence.get("target_stop_order_class_counts", {}) if isinstance(evidence, dict) else {}
        ),
        "source_component_summary_prior_rows": (
            component_prior.get("matched_rows", 0) if component_prior else 0
        ),
        "source_component_summary_prior_decision_counts": (
            component_prior.get("decision_counts", {}) if component_prior else {}
        ),
        "source_component_summary_prior_source_component_counts": (
            component_prior.get("source_component_counts", {}) if component_prior else {}
        ),
        "source_component_summary_prior_source_component_decision_counts": (
            component_prior.get("source_component_decision_counts", {}) if component_prior else {}
        ),
        "source_component_summary_prior_proxy_score_sum": (
            _metric_value(component_prior, "proxy_score") if component_prior else None
        ),
        "source_component_summary_prior_proxy_score_mean": (
            _metric_value(component_prior, "proxy_score", "mean") if component_prior else None
        ),
        "source_component_summary_prior_effective_n_sum": (
            _metric_value(component_prior, "effective_n") if component_prior else None
        ),
        "recommendation_bucket_prior_rows": (
            recommendation_prior.get("matched_rows", 0) if recommendation_prior else 0
        ),
        "recommendation_bucket_prior_source_component_counts": (
            recommendation_prior.get("source_component_counts", {}) if recommendation_prior else {}
        ),
        "recommendation_bucket_prior_decision_group_counts": (
            recommendation_prior.get("recommendation_decision_group_counts", {})
            if recommendation_prior
            else {}
        ),
        "recommendation_bucket_prior_decision_group_row_counts": (
            recommendation_prior.get("recommendation_decision_group_row_counts", {})
            if recommendation_prior
            else {}
        ),
        "recommendation_bucket_prior_component_decision_group_row_counts": (
            recommendation_prior.get("recommendation_component_decision_group_row_counts", {})
            if recommendation_prior
            else {}
        ),
        "recommendation_bucket_prior_effective_n_sum": (
            _metric_value(recommendation_prior, "effective_n") if recommendation_prior else None
        ),
        "recommendation_family_rollup_prior_rows": (
            family_rollup_prior.get("matched_rows", 0) if family_rollup_prior else 0
        ),
        "recommendation_family_rollup_prior_source_component_counts": (
            family_rollup_prior.get("source_component_counts", {}) if family_rollup_prior else {}
        ),
        "recommendation_family_rollup_prior_decision_group_counts": (
            family_rollup_prior.get("recommendation_decision_group_counts", {})
            if family_rollup_prior
            else {}
        ),
        "recommendation_family_rollup_prior_decision_group_row_counts": (
            family_rollup_prior.get("recommendation_decision_group_row_counts", {})
            if family_rollup_prior
            else {}
        ),
        "recommendation_family_rollup_prior_component_decision_group_row_counts": (
            family_rollup_prior.get("recommendation_component_decision_group_row_counts", {})
            if family_rollup_prior
            else {}
        ),
        "recommendation_family_rollup_prior_effective_n_sum": (
            _metric_value(family_rollup_prior, "effective_n") if family_rollup_prior else None
        ),
        "recommendation_unified_candidate_prior_rows": (
            unified_candidate_prior.get("matched_rows", 0) if unified_candidate_prior else 0
        ),
        "recommendation_unified_candidate_prior_source_component_counts": (
            unified_candidate_prior.get("source_component_counts", {})
            if unified_candidate_prior
            else {}
        ),
        "recommendation_unified_candidate_prior_decision_group_counts": (
            unified_candidate_prior.get("recommendation_decision_group_counts", {})
            if unified_candidate_prior
            else {}
        ),
        "recommendation_unified_candidate_prior_decision_group_row_counts": (
            unified_candidate_prior.get("recommendation_decision_group_row_counts", {})
            if unified_candidate_prior
            else {}
        ),
        "recommendation_unified_candidate_prior_component_decision_group_row_counts": (
            unified_candidate_prior.get("recommendation_component_decision_group_row_counts", {})
            if unified_candidate_prior
            else {}
        ),
        "recommendation_unified_candidate_prior_route_session_counts": (
            unified_candidate_prior.get("route_session_counts", {})
            if unified_candidate_prior
            else {}
        ),
        "recommendation_unified_candidate_prior_horizon_id_counts": (
            unified_candidate_prior.get("horizon_id_counts", {})
            if unified_candidate_prior
            else {}
        ),
        "recommendation_unified_candidate_prior_primitive_counts": (
            unified_candidate_prior.get("recommendation_unified_candidate_primitive_counts", {})
            if unified_candidate_prior
            else {}
        ),
        "recommendation_unified_candidate_prior_proxy_score_mean": (
            _metric_value(unified_candidate_prior, "proxy_score", "mean")
            if unified_candidate_prior
            else None
        ),
        "recommendation_unified_candidate_prior_effective_n_sum": (
            _metric_value(unified_candidate_prior, "effective_n")
            if unified_candidate_prior
            else None
        ),
        "recommendation_scope_rollup_prior_rows": (
            scope_rollup_prior.get("matched_rows", 0) if scope_rollup_prior else 0
        ),
        "recommendation_scope_rollup_prior_source_component_counts": (
            scope_rollup_prior.get("source_component_counts", {}) if scope_rollup_prior else {}
        ),
        "recommendation_scope_rollup_prior_decision_group_counts": (
            scope_rollup_prior.get("recommendation_decision_group_counts", {})
            if scope_rollup_prior
            else {}
        ),
        "recommendation_scope_rollup_prior_decision_group_row_counts": (
            scope_rollup_prior.get("recommendation_decision_group_row_counts", {})
            if scope_rollup_prior
            else {}
        ),
        "recommendation_scope_rollup_prior_component_decision_group_row_counts": (
            scope_rollup_prior.get("recommendation_component_decision_group_row_counts", {})
            if scope_rollup_prior
            else {}
        ),
        "recommendation_scope_rollup_prior_route_session_counts": (
            scope_rollup_prior.get("route_session_counts", {}) if scope_rollup_prior else {}
        ),
        "recommendation_scope_rollup_prior_horizon_id_counts": (
            scope_rollup_prior.get("horizon_id_counts", {}) if scope_rollup_prior else {}
        ),
        "recommendation_scope_rollup_prior_primitive_counts": (
            scope_rollup_prior.get("recommendation_scope_rollup_primitive_counts", {})
            if scope_rollup_prior
            else {}
        ),
        "recommendation_scope_rollup_prior_effective_n_sum": (
            _metric_value(scope_rollup_prior, "effective_n") if scope_rollup_prior else None
        ),
    }
    summary["strong_negative_proxy_r_rows"] = _count_evidence_values(
        evidence,
        "proxy_r_class_counts",
        ("STRONG_NEGATIVE_PROXY_R",),
    )
    summary["strong_positive_proxy_r_rows"] = _count_evidence_values(
        evidence,
        "proxy_r_class_counts",
        ("STRONG_POSITIVE_PROXY_R",),
    )
    summary["negative_proxy_r_rows"] = _count_evidence_values(
        evidence,
        "proxy_r_class_counts",
        ("STRONG_NEGATIVE_PROXY_R", "NEGATIVE_PROXY_R"),
    )
    summary["positive_proxy_r_rows"] = _count_evidence_values(
        evidence,
        "proxy_r_class_counts",
        ("STRONG_POSITIVE_PROXY_R", "POSITIVE_PROXY_R"),
    )
    return summary


def _configured_float(cfg: dict[str, Any], key: str, default: float) -> float:
    value = _to_float(cfg.get(key))
    return default if value is None else float(value)


def _risk_reason_bypasses_effective_n_floor(risk_reason: str, cfg: dict[str, Any]) -> bool:
    reasons = {
        _match_key(reason)
        for reason in _configured_list(
            cfg,
            "risk_zero_bypass_effective_n_reasons",
            DEFAULT_RISK_ZERO_BYPASS_EFFECTIVE_N_REASONS,
        )
    }
    return _match_key(risk_reason) in reasons


def _pre_ai_follow_effective_n_bypass_reason(risk_reason: str, cfg: dict[str, Any]) -> bool:
    reasons = {
        _match_key(reason)
        for reason in _configured_list(
            cfg,
            "pre_ai_follow_effective_n_bypass_risk_reasons",
            ("vnext_risk_strong_positive_proxy_class",),
        )
    }
    return _match_key(risk_reason) in reasons


def _payload_get(payload: Any, key: str, default: Any = None) -> Any:
    if isinstance(payload, dict):
        return payload.get(key, default)
    return getattr(payload, key, default)


def _side_from_asian_sweep_token(value: Any) -> str:
    token = _normalized(value).casefold()
    if token in {"long", "bullish", "buy", "up", "high", "asian_high", "above_asian_high"}:
        return "LONG"
    if token in {"short", "bearish", "sell", "down", "low", "asian_low", "below_asian_low"}:
        return "SHORT"
    return ""


def _xau_asian_sweep_continuation_context(
    base_event: dict[str, Any],
    raw_data: dict[str, Any] | None,
    cfg: dict[str, Any],
) -> dict[str, Any] | None:
    if not bool(cfg.get("pre_ai_xau_asian_sweep_continuation_enabled", True)):
        return None
    if not isinstance(raw_data, dict):
        return None
    family = (
        _normalized(base_event.get("symbol_family"))
        or _event_symbol_family({key: str(value) for key, value in base_event.items()})
    )
    enabled_families = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "pre_ai_xau_asian_sweep_symbol_families",
            ["XAUUSD_GC_FAMILY"],
        )
    }
    if enabled_families and family not in enabled_families:
        return None

    for key in (
        "asian_sweep_continuation_side",
        "asian_range_sweep_continuation_side",
        "asian_sweep_direction",
        "asian_range_sweep_direction",
    ):
        side = _side_from_asian_sweep_token(raw_data.get(key))
        if side:
            return {
                "enabled": True,
                "source": key,
                "pool_type": "asian_high" if side == "LONG" else "asian_low",
                "sweep_type": _normalized(raw_data.get("asian_sweep_type") or "explicit"),
                "continuation_side": side,
                "opposite_side": "SHORT" if side == "LONG" else "LONG",
                "framework": _normalized(
                    cfg.get("pre_ai_xau_asian_sweep_framework") or "ob_retest"
                ),
                "evidence_family": "gold_market_deep_knowledge_asian_sweep_continuation",
                "source_artifact_path": ".context/01_knowledge_base/kb_gold_market_deep_knowledge.md",
            }

    detected_sweeps = raw_data.get("detected_sweeps")
    if isinstance(detected_sweeps, IterableABC) and not isinstance(detected_sweeps, (str, bytes, dict)):
        candidates: list[dict[str, Any]] = []
        for sweep in detected_sweeps:
            pool = _payload_get(sweep, "pool", {}) or {}
            pool_type = (
                _payload_get(pool, "type")
                or _payload_get(sweep, "pool_type")
                or _payload_get(sweep, "type")
            )
            side = _side_from_asian_sweep_token(pool_type)
            if not side:
                continue
            candidates.append(
                {
                    "enabled": True,
                    "source": "detected_sweeps",
                    "pool_type": _normalized(pool_type),
                    "sweep_type": _normalized(_payload_get(sweep, "sweep_type") or "sweep"),
                    "continuation_side": side,
                    "opposite_side": "SHORT" if side == "LONG" else "LONG",
                    "framework": _normalized(
                        cfg.get("pre_ai_xau_asian_sweep_framework") or "ob_retest"
                    ),
                    "candle_index": _to_float(_payload_get(sweep, "candle_index")),
                    "time": _normalized(_payload_get(sweep, "time")),
                    "evidence_family": "gold_market_deep_knowledge_asian_sweep_continuation",
                    "source_artifact_path": ".context/01_knowledge_base/kb_gold_market_deep_knowledge.md",
                }
            )
        if candidates:
            return sorted(
                candidates,
                key=lambda item: (
                    item.get("candle_index") if item.get("candle_index") is not None else -1,
                    item.get("time") or "",
                ),
            )[-1]

    session_levels = raw_data.get("session_levels")
    candles = raw_data.get("candles")
    if not isinstance(session_levels, dict) or not isinstance(candles, dict):
        return None
    m15_candles = candles.get("M15")
    if not isinstance(m15_candles, list) or not m15_candles:
        return None
    latest = m15_candles[-1]
    if not isinstance(latest, dict):
        return None
    asian_high = _to_float(session_levels.get("asian_high"))
    asian_low = _to_float(session_levels.get("asian_low"))
    high = _to_float(latest.get("high"))
    low = _to_float(latest.get("low"))
    open_price = _to_float(latest.get("open"))
    close = _to_float(latest.get("close"))
    if open_price is None or close is None:
        return None
    body_top = max(open_price, close)
    body_bottom = min(open_price, close)
    latest_time = _normalized(latest.get("time") or latest.get("timestamp") or latest.get("timestamp_utc"))

    if asian_high is not None and asian_high > 0 and high is not None:
        if close > asian_high:
            sweep_type = "run"
        elif high > asian_high and body_top < asian_high:
            sweep_type = "sweep"
        else:
            sweep_type = ""
        if sweep_type:
            return {
                "enabled": True,
                "source": "latest_m15_candle_vs_session_levels",
                "pool_type": "asian_high",
                "sweep_type": sweep_type,
                "continuation_side": "LONG",
                "opposite_side": "SHORT",
                "framework": _normalized(cfg.get("pre_ai_xau_asian_sweep_framework") or "ob_retest"),
                "level": asian_high,
                "wick_extreme": high,
                "body_close": close,
                "time": latest_time,
                "evidence_family": "gold_market_deep_knowledge_asian_sweep_continuation",
                "source_artifact_path": ".context/01_knowledge_base/kb_gold_market_deep_knowledge.md",
            }

    if asian_low is not None and asian_low > 0 and low is not None:
        if close < asian_low:
            sweep_type = "run"
        elif low < asian_low and body_bottom > asian_low:
            sweep_type = "sweep"
        else:
            sweep_type = ""
        if sweep_type:
            return {
                "enabled": True,
                "source": "latest_m15_candle_vs_session_levels",
                "pool_type": "asian_low",
                "sweep_type": sweep_type,
                "continuation_side": "SHORT",
                "opposite_side": "LONG",
                "framework": _normalized(cfg.get("pre_ai_xau_asian_sweep_framework") or "ob_retest"),
                "level": asian_low,
                "wick_extreme": low,
                "body_close": close,
                "time": latest_time,
                "evidence_family": "gold_market_deep_knowledge_asian_sweep_continuation",
                "source_artifact_path": ".context/01_knowledge_base/kb_gold_market_deep_knowledge.md",
            }
    return None


def _with_unique_value(values: tuple[str, ...], value: str) -> tuple[str, ...]:
    value = _normalized(value)
    if not value or value in values:
        return values
    return tuple(sorted((*values, value)))


def _apply_xau_asian_sweep_continuation_rule(
    *,
    sweep_context: dict[str, Any] | None,
    decision: DecisionLabel,
    would_action: PreAIAction,
    recommended_side: str | None,
    blocked_sides: tuple[str, ...],
    recommended_frameworks: tuple[str, ...],
    recommended_route_families: tuple[str, ...],
    blocked_frameworks: tuple[str, ...],
    blocked_route_families: tuple[str, ...],
    risk_vetoed_sides: tuple[str, ...],
    side_risk_reasons: dict[str, str],
) -> tuple[
    DecisionLabel,
    PreAIAction,
    str | None,
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    dict[str, str],
]:
    if not sweep_context:
        return (
            decision,
            would_action,
            recommended_side,
            blocked_sides,
            recommended_frameworks,
            recommended_route_families,
            side_risk_reasons,
        )
    continuation_side = _normalized(sweep_context.get("continuation_side"))
    opposite_side = _normalized(sweep_context.get("opposite_side"))
    framework = _normalized(sweep_context.get("framework"))
    if not continuation_side:
        return (
            decision,
            would_action,
            recommended_side,
            blocked_sides,
            recommended_frameworks,
            recommended_route_families,
            side_risk_reasons,
        )
    side_risk_reasons = dict(side_risk_reasons)
    if opposite_side:
        blocked_sides = _with_unique_value(blocked_sides, opposite_side)
        side_risk_reasons.setdefault(opposite_side, "xau_asian_sweep_continuation_against_side")
    if continuation_side in blocked_sides or continuation_side in risk_vetoed_sides:
        return (
            "MIXED" if decision == "LEGACY" else decision,
            would_action,
            recommended_side,
            blocked_sides,
            recommended_frameworks,
            recommended_route_families,
            side_risk_reasons,
        )

    recommended_side = continuation_side
    if framework and framework not in blocked_frameworks:
        recommended_frameworks = (framework,)
        route_family = _route_family_for_framework(framework)
        recommended_route_families = (
            (route_family,)
            if route_family and route_family not in blocked_route_families
            else ()
        )
    would_action = (
        "NARROW_AI_TO_ROUTE"
        if recommended_frameworks or recommended_route_families
        else "NARROW_AI_TO_SIDE"
    )
    return (
        "FOLLOW",
        would_action,
        recommended_side,
        blocked_sides,
        recommended_frameworks,
        recommended_route_families,
        side_risk_reasons,
    )


def _route_family_avoid_veto(
    evidence: dict[str, Any],
    cfg: dict[str, Any],
) -> tuple[str, int, int] | None:
    if not bool(cfg.get("route_family_avoid_veto_enabled", True)):
        return None
    family_counts = evidence.get("route_family_decision_counts", {})
    if not isinstance(family_counts, dict):
        return None
    veto_families = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "route_family_avoid_veto_families",
            ["numeric_router", "nofill_mechanical"],
        )
    }
    min_rows = int(_configured_float(cfg, "route_family_avoid_veto_min_rows", 1.0))
    dominance_ratio = _configured_float(cfg, "route_family_avoid_veto_dominance_ratio", 1.0)
    for family, counts in sorted(family_counts.items()):
        if veto_families and _normalized(family) not in veto_families:
            continue
        if not isinstance(counts, dict):
            continue
        avoid_rows = int(counts.get("AVOID") or 0)
        follow_rows = int(counts.get("FOLLOW") or 0)
        if avoid_rows >= max(1, min_rows) and avoid_rows >= max(1, follow_rows) * dominance_ratio:
            return _normalized(family), avoid_rows, follow_rows
    return None


def _source_component_avoid_veto(
    evidence: dict[str, Any],
    cfg: dict[str, Any],
) -> tuple[str, int, int] | None:
    if not bool(cfg.get("source_component_avoid_veto_enabled", True)):
        return None
    component_counts = evidence.get("source_component_decision_counts", {})
    if not isinstance(component_counts, dict):
        return None
    veto_components = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "source_component_avoid_veto_components",
            [
                "market_gap_code",
                "nofill_far_miss_avoid",
                "nofill_far_miss_source_confidence",
                "shadow_source_guard",
            ],
        )
    }
    min_rows = int(_configured_float(cfg, "source_component_avoid_veto_min_rows", 1.0))
    dominance_ratio = _configured_float(cfg, "source_component_avoid_veto_dominance_ratio", 1.0)
    for component, counts in sorted(component_counts.items()):
        if veto_components and _normalized(component) not in veto_components:
            continue
        if not isinstance(counts, dict):
            continue
        avoid_rows = int(counts.get("AVOID") or 0)
        follow_rows = int(counts.get("FOLLOW") or 0)
        if avoid_rows >= max(1, min_rows) and avoid_rows >= max(1, follow_rows) * dominance_ratio:
            return _normalized(component), avoid_rows, follow_rows
    return None


def _source_component_summary_adverse_prior(
    evidence: dict[str, Any],
    cfg: dict[str, Any],
) -> tuple[str, int, int, float | None, float | None] | None:
    if not bool(cfg.get("source_component_summary_prior_risk_enabled", True)):
        return None
    prior = _source_component_summary_prior_payload(evidence)
    if not prior:
        return None
    component_presence_counts = prior.get("source_component_counts", {})
    if not isinstance(component_presence_counts, dict):
        component_presence_counts = {}
    allowed_components = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "source_component_summary_prior_risk_components",
            (),
        )
    }
    min_rows = int(
        _configured_float(cfg, "source_component_summary_prior_risk_min_rollup_rows", 20.0)
    )
    max_proxy_mean = _configured_float(
        cfg,
        "source_component_summary_prior_adverse_proxy_mean_max",
        -0.05,
    )
    proxy_mean = _metric_value(prior, "proxy_score", "mean")
    effective_n = _metric_value(prior, "effective_n")
    if proxy_mean is None:
        return None
    if proxy_mean > max_proxy_mean:
        return None
    if effective_n is None or effective_n < max(1, min_rows):
        return None

    for component in sorted(component_presence_counts):
        component = _normalized(component)
        if allowed_components and component not in allowed_components:
            continue
        adverse_rows = int(round(effective_n))
        if adverse_rows >= max(1, min_rows):
            return component, adverse_rows, 0, proxy_mean, effective_n
    return None


def _recommendation_bucket_repair_prior(
    evidence: dict[str, Any],
    cfg: dict[str, Any],
) -> tuple[str, float, float, dict[str, float | int]] | None:
    if not bool(cfg.get("recommendation_bucket_prior_risk_enabled", True)):
        return None
    prior = _recommendation_bucket_prior_payload(evidence)
    if not prior:
        return None
    component_group_counts = prior.get("recommendation_component_decision_group_row_counts", {})
    if not isinstance(component_group_counts, dict) or not component_group_counts:
        return None
    adverse_groups = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_bucket_prior_repair_groups",
            ("SOURCE_OR_CONTROL_REPAIR",),
        )
    }
    supportive_groups = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_bucket_prior_supportive_groups",
            ("IMPLEMENT", "SCORE_WITH_CONTROL"),
        )
    }
    min_rows = _configured_float(cfg, "recommendation_bucket_prior_risk_min_rows", 20.0)
    dominance_ratio = _configured_float(
        cfg,
        "recommendation_bucket_prior_repair_dominance_ratio",
        1.0,
    )
    for component, counts in sorted(component_group_counts.items()):
        if not isinstance(counts, dict):
            continue
        component = _normalized(component)
        adverse_rows = sum(
            _to_float(value) or 0.0
            for group, value in counts.items()
            if _normalized(group) in adverse_groups
        )
        supportive_rows = sum(
            _to_float(value) or 0.0
            for group, value in counts.items()
            if _normalized(group) in supportive_groups
        )
        if (
            adverse_rows >= max(1.0, min_rows)
            and adverse_rows >= max(1.0, supportive_rows) * dominance_ratio
        ):
            return component, adverse_rows, supportive_rows, counts
    return None


def _recommendation_family_rollup_adverse_prior(
    evidence: dict[str, Any],
    cfg: dict[str, Any],
) -> tuple[str, float, float, dict[str, float | int]] | None:
    if not bool(cfg.get("recommendation_family_rollup_prior_risk_enabled", True)):
        return None
    prior = _recommendation_family_rollup_prior_payload(evidence)
    if not prior:
        return None
    component_group_counts = prior.get("recommendation_component_decision_group_row_counts", {})
    if not isinstance(component_group_counts, dict) or not component_group_counts:
        return None
    adverse_groups = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_family_rollup_prior_adverse_groups",
            ("SOURCE_OR_CONTROL_REPAIR", "REDESIGN", "GUARD"),
        )
    }
    supportive_groups = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_family_rollup_prior_supportive_groups",
            ("IMPLEMENT", "SCORE_WITH_CONTROL"),
        )
    }
    min_rows = _configured_float(cfg, "recommendation_family_rollup_prior_risk_min_rows", 20.0)
    dominance_ratio = _configured_float(
        cfg,
        "recommendation_family_rollup_prior_adverse_dominance_ratio",
        1.0,
    )
    for component, counts in sorted(component_group_counts.items()):
        if not isinstance(counts, dict):
            continue
        component = _normalized(component)
        adverse_rows = sum(
            _to_float(value) or 0.0
            for group, value in counts.items()
            if _normalized(group) in adverse_groups
        )
        supportive_rows = sum(
            _to_float(value) or 0.0
            for group, value in counts.items()
            if _normalized(group) in supportive_groups
        )
        if (
            adverse_rows >= max(1.0, min_rows)
            and adverse_rows >= max(1.0, supportive_rows) * dominance_ratio
        ):
            return component, adverse_rows, supportive_rows, counts
    return None


def _recommendation_unified_candidate_adverse_prior(
    evidence: dict[str, Any],
    cfg: dict[str, Any],
) -> tuple[str, float, float, dict[str, float | int]] | None:
    if not bool(cfg.get("recommendation_unified_candidate_prior_risk_enabled", True)):
        return None
    prior = _recommendation_unified_candidate_prior_payload(evidence)
    if not prior:
        return None
    component_group_counts = prior.get("recommendation_component_decision_group_row_counts", {})
    if not isinstance(component_group_counts, dict) or not component_group_counts:
        return None
    adverse_groups = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_unified_candidate_prior_adverse_groups",
            ("SOURCE_OR_CONTROL_REPAIR", "REDESIGN", "GUARD"),
        )
    }
    supportive_groups = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_unified_candidate_prior_supportive_groups",
            ("IMPLEMENT", "SCORE_WITH_CONTROL"),
        )
    }
    min_rows = _configured_float(
        cfg,
        "recommendation_unified_candidate_prior_risk_min_rows",
        20.0,
    )
    dominance_ratio = _configured_float(
        cfg,
        "recommendation_unified_candidate_prior_adverse_dominance_ratio",
        1.0,
    )
    for component, counts in sorted(component_group_counts.items()):
        if not isinstance(counts, dict):
            continue
        component = _normalized(component)
        adverse_rows = sum(
            _to_float(value) or 0.0
            for group, value in counts.items()
            if _normalized(group) in adverse_groups
        )
        supportive_rows = sum(
            _to_float(value) or 0.0
            for group, value in counts.items()
            if _normalized(group) in supportive_groups
        )
        if (
            adverse_rows >= max(1.0, min_rows)
            and adverse_rows >= max(1.0, supportive_rows) * dominance_ratio
        ):
            return component, adverse_rows, supportive_rows, counts
    return None


def _recommendation_scope_rollup_adverse_prior(
    evidence: dict[str, Any],
    cfg: dict[str, Any],
) -> tuple[str, float, float, dict[str, float | int]] | None:
    if not bool(cfg.get("recommendation_scope_rollup_prior_risk_enabled", True)):
        return None
    prior = _recommendation_scope_rollup_prior_payload(evidence)
    if not prior:
        return None
    component_group_counts = prior.get("recommendation_component_decision_group_row_counts", {})
    if not isinstance(component_group_counts, dict) or not component_group_counts:
        return None
    adverse_groups = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_scope_rollup_prior_adverse_groups",
            ("SOURCE_OR_CONTROL_REPAIR", "REDESIGN", "GUARD"),
        )
    }
    supportive_groups = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "recommendation_scope_rollup_prior_supportive_groups",
            ("IMPLEMENT", "SCORE_WITH_CONTROL"),
        )
    }
    min_rows = _configured_float(cfg, "recommendation_scope_rollup_prior_risk_min_rows", 20.0)
    dominance_ratio = _configured_float(
        cfg,
        "recommendation_scope_rollup_prior_adverse_dominance_ratio",
        1.0,
    )
    for component, counts in sorted(component_group_counts.items()):
        if not isinstance(counts, dict):
            continue
        component = _normalized(component)
        adverse_rows = sum(
            _to_float(value) or 0.0
            for group, value in counts.items()
            if _normalized(group) in adverse_groups
        )
        supportive_rows = sum(
            _to_float(value) or 0.0
            for group, value in counts.items()
            if _normalized(group) in supportive_groups
        )
        if (
            adverse_rows >= max(1.0, min_rows)
            and adverse_rows >= max(1.0, supportive_rows) * dominance_ratio
        ):
            return component, adverse_rows, supportive_rows, counts
    return None


def _action_class_avoid_veto(
    evidence: dict[str, Any],
    cfg: dict[str, Any],
) -> tuple[str, int, int] | None:
    if not bool(cfg.get("action_class_avoid_veto_enabled", True)):
        return None
    action_counts = evidence.get("action_class_decision_counts", {})
    if not isinstance(action_counts, dict):
        return None
    veto_classes = {
        _normalized(item)
        for item in _configured_list(
            cfg,
            "action_class_avoid_veto_classes",
            ["avoid_filter", "inverse_filter", "failure_filter"],
        )
    }
    min_rows = int(_configured_float(cfg, "action_class_avoid_veto_min_rows", 1.0))
    dominance_ratio = _configured_float(cfg, "action_class_avoid_veto_dominance_ratio", 1.0)
    for action_class, counts in sorted(action_counts.items()):
        if veto_classes and _normalized(action_class) not in veto_classes:
            continue
        if not isinstance(counts, dict):
            continue
        avoid_rows = int(counts.get("AVOID") or 0)
        follow_rows = int(counts.get("FOLLOW") or 0)
        if avoid_rows >= max(1, min_rows) and avoid_rows >= max(1, follow_rows) * dominance_ratio:
            return _normalized(action_class), avoid_rows, follow_rows
    return None


def _decision_count_veto(
    evidence: dict[str, Any],
    *,
    count_key: str,
    enabled_key: str,
    names_key: str,
    min_rows_key: str,
    dominance_key: str,
    default_names: Iterable[str],
    cfg: dict[str, Any],
) -> tuple[str, int, int] | None:
    if not bool(cfg.get(enabled_key, True)):
        return None
    decision_counts = evidence.get(count_key, {})
    if not isinstance(decision_counts, dict):
        return None
    veto_names = {
        _normalized(item)
        for item in _configured_list(cfg, names_key, default_names)
    }
    min_rows = int(_configured_float(cfg, min_rows_key, 1.0))
    dominance_ratio = _configured_float(cfg, dominance_key, 1.0)
    for name, counts in sorted(decision_counts.items()):
        if veto_names and _normalized(name) not in veto_names:
            continue
        if not isinstance(counts, dict):
            continue
        avoid_rows = int(counts.get("AVOID") or 0)
        follow_rows = int(counts.get("FOLLOW") or 0)
        if avoid_rows >= max(1, min_rows) and avoid_rows >= max(1, follow_rows) * dominance_ratio:
            return _normalized(name), avoid_rows, follow_rows
    return None


def _summary_pressure(summary: dict[str, Any], cfg: dict[str, Any]) -> tuple[float, float]:
    weights = {
        "cost_adjusted_simulated_r_sum": _configured_float(
            cfg,
            "conflict_cost_adjusted_r_weight",
            1.0,
        ),
        "stress_simulated_r_sum": _configured_float(
            cfg,
            "conflict_stress_r_weight",
            0.25,
        ),
        "proxy_score_sum": _configured_float(cfg, "conflict_proxy_score_weight", 1.0),
    }
    follow_pressure = 0.0
    avoid_pressure = 0.0
    for key, weight in weights.items():
        value = _to_float(summary.get(key))
        if value is None:
            continue
        weighted = value * weight
        if weighted > 0:
            follow_pressure += weighted
        elif weighted < 0:
            avoid_pressure += abs(weighted)
    return follow_pressure, avoid_pressure


def _positive_follow_pressure_guard(
    decision: GTOSVNextRuntimeDecision,
    summary: dict[str, Any],
    cfg: dict[str, Any],
) -> bool:
    """Return True when source-bound positive R should outrank proxy vetoes."""
    if not bool(cfg.get("positive_follow_pressure_guard_enabled", True)):
        return False
    if decision.decision != "FOLLOW":
        return False

    effective_n = _to_float(summary.get("effective_n_sum")) or 0.0
    min_effective_n = _configured_float(
        cfg,
        "positive_follow_pressure_guard_min_effective_n",
        100.0,
    )
    follow_pressure, avoid_pressure = _summary_pressure(summary, cfg)
    min_abs_pressure = _configured_float(
        cfg,
        "positive_follow_pressure_guard_min_abs_pressure",
        1.0,
    )
    dominance_ratio = _configured_float(
        cfg,
        "positive_follow_pressure_guard_dominance_ratio",
        1.25,
    )
    summary["positive_follow_pressure_guard_follow_pressure"] = round(follow_pressure, 12)
    summary["positive_follow_pressure_guard_avoid_pressure"] = round(avoid_pressure, 12)
    summary["positive_follow_pressure_guard_effective_n"] = effective_n
    summary["positive_follow_pressure_guard_dominance_ratio"] = dominance_ratio
    summary["positive_follow_pressure_guard_min_effective_n"] = min_effective_n
    guard = (
        effective_n >= min_effective_n
        and follow_pressure >= min_abs_pressure
        and follow_pressure >= avoid_pressure * dominance_ratio
    )
    summary["positive_follow_pressure_guard_active"] = guard
    return guard


def _source_guarded_positive_proxy_guard(
    decision: GTOSVNextRuntimeDecision,
    summary: dict[str, Any],
    cfg: dict[str, Any],
) -> bool:
    """Return True when ready scorer-surface proxy evidence can carry routing.

    The full vNext matrix has source-guarded positive proxy scorer rows that do
    not have exact R/effective-N yet. Treating all non-source-bound target/stop
    rows as zero-risk before proxy scoring erases those implementation-ready
    surfaces. This guard keeps them usable only when positive proxy evidence is
    dominant and the matched rows come from configured source-guarded surfaces.
    """
    if not bool(cfg.get("source_guarded_positive_proxy_enabled", True)):
        return False
    if decision.decision != "FOLLOW":
        return False

    strong_positive_rows = int(summary.get("strong_positive_proxy_r_rows") or 0)
    positive_rows = int(summary.get("positive_proxy_r_rows") or 0)
    negative_rows = int(summary.get("negative_proxy_r_rows") or 0)
    min_rows = int(_configured_float(cfg, "source_guarded_positive_proxy_min_rows", 20.0))
    dominance_ratio = _configured_float(
        cfg,
        "source_guarded_positive_proxy_dominance_ratio",
        2.0,
    )
    role_rows = _count_evidence_values(
        {"source_role_counts": summary.get("source_role_counts", {})},
        "source_role_counts",
        _configured_list(
            cfg,
            "source_guarded_positive_proxy_source_roles",
            (
                "scorer_registry_surface",
                "branch_local_default_off_candidate",
                "scope_system_decision",
            ),
        ),
    )
    group_rows = _count_evidence_values(
        {"source_group_counts": summary.get("source_group_counts", {})},
        "source_group_counts",
        _configured_list(
            cfg,
            "source_guarded_positive_proxy_source_groups",
            ("scorer_registry_surface",),
        ),
    )
    surface_rows = _count_evidence_values(
        {"system_surface_counts": summary.get("system_surface_counts", {})},
        "system_surface_counts",
        _configured_list(
            cfg,
            "source_guarded_positive_proxy_system_surfaces",
            (
                "default_off_research_scorer_registry_catalog",
                "numeric_router_default_off_scope_decision_catalog",
                "scorer_registry_surface",
                "src/research_infra/moonshot_expanded_market_reduced_surface_execution.py",
            ),
        ),
    )
    action_rows = _count_evidence_values(
        {"implementation_action_counts": summary.get("implementation_action_counts", {})},
        "implementation_action_counts",
        _configured_list(
            cfg,
            "source_guarded_positive_proxy_implementation_actions",
            (
                "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
                "IMPLEMENT_DEFAULT_OFF_SCORER_SCOPE_WITH_GUARDS",
                "REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE",
                "REGISTER_DEFAULT_OFF_BRANCH_LOCAL_PRESERVED_REDUCED_SURFACE_CANDIDATE",
            ),
        ),
    )
    guarded_rows = max(role_rows, group_rows, surface_rows, action_rows)
    min_guard_rows = int(
        _configured_float(cfg, "source_guarded_positive_proxy_min_guard_rows", 1.0)
    )
    guard = (
        strong_positive_rows >= max(1, min_rows)
        and positive_rows >= max(1, negative_rows) * dominance_ratio
        and guarded_rows >= max(1, min_guard_rows)
    )
    summary["source_guarded_positive_proxy_guard_active"] = guard
    summary["source_guarded_positive_proxy_guard_rows"] = guarded_rows
    summary["source_guarded_positive_proxy_guard_role_rows"] = role_rows
    summary["source_guarded_positive_proxy_guard_group_rows"] = group_rows
    summary["source_guarded_positive_proxy_guard_surface_rows"] = surface_rows
    summary["source_guarded_positive_proxy_guard_action_rows"] = action_rows
    summary["source_guarded_positive_proxy_guard_min_rows"] = min_rows
    summary["source_guarded_positive_proxy_guard_dominance_ratio"] = dominance_ratio
    return guard


def _bypass_positive_follow_guard(
    summary: dict[str, Any],
    reason: str,
    *,
    enabled: bool,
) -> bool:
    if not enabled:
        return False
    summary.setdefault("positive_follow_pressure_bypassed_reasons", []).append(reason)
    return True


def _vnext_risk_multiplier(
    decision: GTOSVNextRuntimeDecision,
    cfg: dict[str, Any],
) -> tuple[float, str, dict[str, Any]]:
    summary = _risk_evidence_summary(decision)
    if not decision.matched:
        return 1.0, "vnext_risk_no_match", summary
    positive_follow_guard = _positive_follow_pressure_guard(decision, summary, cfg)
    source_guarded_positive_proxy_guard = _source_guarded_positive_proxy_guard(
        decision,
        summary,
        cfg,
    )
    bypass_avoid_veto = positive_follow_guard and bool(
        cfg.get("positive_follow_pressure_bypasses_avoid_veto", True)
    )
    route_family_veto = _route_family_avoid_veto(decision.evidence or {}, cfg)
    if route_family_veto:
        family, avoid_rows, follow_rows = route_family_veto
        summary["route_family_avoid_veto_family"] = family
        summary["route_family_avoid_veto_avoid_rows"] = avoid_rows
        summary["route_family_avoid_veto_follow_rows"] = follow_rows
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_route_family_avoid_veto",
            enabled=bypass_avoid_veto,
        ):
            summary["route_family_avoid_veto_bypassed"] = True
        else:
            return (
                _configured_float(cfg, "route_family_avoid_veto_risk_multiplier", 0.0),
                "vnext_risk_route_family_avoid_veto",
                summary,
            )
    source_component_veto = _source_component_avoid_veto(decision.evidence or {}, cfg)
    if source_component_veto:
        component, avoid_rows, follow_rows = source_component_veto
        summary["source_component_avoid_veto_component"] = component
        summary["source_component_avoid_veto_avoid_rows"] = avoid_rows
        summary["source_component_avoid_veto_follow_rows"] = follow_rows
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_source_component_avoid_veto",
            enabled=bypass_avoid_veto,
        ):
            summary["source_component_avoid_veto_bypassed"] = True
        else:
            return (
                _configured_float(cfg, "source_component_avoid_veto_risk_multiplier", 0.0),
                "vnext_risk_source_component_avoid_veto",
                summary,
            )
    component_summary_prior = _source_component_summary_adverse_prior(
        decision.evidence or {},
        cfg,
    )
    if component_summary_prior:
        component, avoid_rows, follow_rows, proxy_mean, effective_n = component_summary_prior
        summary["source_component_summary_prior_component"] = component
        summary["source_component_summary_prior_avoid_rows"] = avoid_rows
        summary["source_component_summary_prior_follow_rows"] = follow_rows
        summary["source_component_summary_prior_proxy_score_mean"] = proxy_mean
        summary["source_component_summary_prior_effective_n_sum"] = effective_n
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_source_component_summary_adverse_prior",
            enabled=bypass_avoid_veto,
        ):
            summary["source_component_summary_prior_bypassed"] = True
        else:
            return (
                _configured_float(
                    cfg,
                    "source_component_summary_prior_risk_multiplier",
                    0.0,
                ),
                "vnext_risk_source_component_summary_adverse_prior",
                summary,
            )
    recommendation_bucket_prior = _recommendation_bucket_repair_prior(
        decision.evidence or {},
        cfg,
    )
    if recommendation_bucket_prior:
        component, repair_rows, supportive_rows, group_counts = recommendation_bucket_prior
        summary["recommendation_bucket_prior_component"] = component
        summary["recommendation_bucket_prior_repair_rows"] = repair_rows
        summary["recommendation_bucket_prior_supportive_rows"] = supportive_rows
        summary["recommendation_bucket_prior_group_row_counts"] = dict(group_counts)
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_recommendation_bucket_repair_prior",
            enabled=positive_follow_guard
            and bool(
                cfg.get(
                    "positive_follow_pressure_bypasses_recommendation_bucket_repair",
                    False,
                )
            ),
        ):
            summary["recommendation_bucket_prior_bypassed"] = True
        else:
            return (
                _configured_float(
                    cfg,
                    "recommendation_bucket_prior_risk_multiplier",
                    0.0,
                ),
                "vnext_risk_recommendation_bucket_repair_prior",
                summary,
            )
    family_rollup_prior = _recommendation_family_rollup_adverse_prior(
        decision.evidence or {},
        cfg,
    )
    if family_rollup_prior:
        component, adverse_rows, supportive_rows, group_counts = family_rollup_prior
        summary["recommendation_family_rollup_prior_component"] = component
        summary["recommendation_family_rollup_prior_adverse_rows"] = adverse_rows
        summary["recommendation_family_rollup_prior_supportive_rows"] = supportive_rows
        summary["recommendation_family_rollup_prior_group_row_counts"] = dict(group_counts)
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_recommendation_family_rollup_adverse_prior",
            enabled=positive_follow_guard
            and bool(
                cfg.get(
                    "positive_follow_pressure_bypasses_recommendation_family_rollup_adverse",
                    False,
                )
            ),
        ):
            summary["recommendation_family_rollup_prior_bypassed"] = True
        else:
            return (
                _configured_float(
                    cfg,
                    "recommendation_family_rollup_prior_risk_multiplier",
                    0.0,
                ),
                "vnext_risk_recommendation_family_rollup_adverse_prior",
                summary,
            )
    unified_candidate_prior = _recommendation_unified_candidate_adverse_prior(
        decision.evidence or {},
        cfg,
    )
    if unified_candidate_prior:
        component, adverse_rows, supportive_rows, group_counts = unified_candidate_prior
        summary["recommendation_unified_candidate_prior_component"] = component
        summary["recommendation_unified_candidate_prior_adverse_rows"] = adverse_rows
        summary["recommendation_unified_candidate_prior_supportive_rows"] = supportive_rows
        summary["recommendation_unified_candidate_prior_group_row_counts"] = dict(group_counts)
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_recommendation_unified_candidate_adverse_prior",
            enabled=positive_follow_guard
            and bool(
                cfg.get(
                    "positive_follow_pressure_bypasses_recommendation_unified_candidate_adverse",
                    False,
                )
            ),
        ):
            summary["recommendation_unified_candidate_prior_bypassed"] = True
        else:
            return (
                _configured_float(
                    cfg,
                    "recommendation_unified_candidate_prior_risk_multiplier",
                    0.0,
                ),
                "vnext_risk_recommendation_unified_candidate_adverse_prior",
                summary,
            )
    scope_rollup_prior = _recommendation_scope_rollup_adverse_prior(
        decision.evidence or {},
        cfg,
    )
    if scope_rollup_prior:
        component, adverse_rows, supportive_rows, group_counts = scope_rollup_prior
        summary["recommendation_scope_rollup_prior_component"] = component
        summary["recommendation_scope_rollup_prior_adverse_rows"] = adverse_rows
        summary["recommendation_scope_rollup_prior_supportive_rows"] = supportive_rows
        summary["recommendation_scope_rollup_prior_group_row_counts"] = dict(group_counts)
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_recommendation_scope_rollup_adverse_prior",
            enabled=positive_follow_guard
            and bool(
                cfg.get(
                    "positive_follow_pressure_bypasses_recommendation_scope_rollup_adverse",
                    False,
                )
            ),
        ):
            summary["recommendation_scope_rollup_prior_bypassed"] = True
        else:
            return (
                _configured_float(
                    cfg,
                    "recommendation_scope_rollup_prior_risk_multiplier",
                    0.0,
                ),
                "vnext_risk_recommendation_scope_rollup_adverse_prior",
                summary,
            )
    action_class_veto = _action_class_avoid_veto(decision.evidence or {}, cfg)
    if action_class_veto:
        action_class, avoid_rows, follow_rows = action_class_veto
        summary["action_class_avoid_veto_class"] = action_class
        summary["action_class_avoid_veto_avoid_rows"] = avoid_rows
        summary["action_class_avoid_veto_follow_rows"] = follow_rows
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_action_class_avoid_veto",
            enabled=bypass_avoid_veto,
        ):
            summary["action_class_avoid_veto_bypassed"] = True
        else:
            return (
                _configured_float(cfg, "action_class_avoid_veto_risk_multiplier", 0.0),
                "vnext_risk_action_class_avoid_veto",
                summary,
            )
    evidence_family_veto = _decision_count_veto(
        decision.evidence or {},
        count_key="evidence_family_decision_counts",
        enabled_key="evidence_family_avoid_veto_enabled",
        names_key="evidence_family_avoid_veto_families",
        min_rows_key="evidence_family_avoid_veto_min_rows",
        dominance_key="evidence_family_avoid_veto_dominance_ratio",
        default_names=(
            "numeric_router_system_recommendations",
            "gate_filter_selector_evidence",
        ),
        cfg=cfg,
    )
    if evidence_family_veto:
        family, avoid_rows, follow_rows = evidence_family_veto
        summary["evidence_family_avoid_veto_family"] = family
        summary["evidence_family_avoid_veto_avoid_rows"] = avoid_rows
        summary["evidence_family_avoid_veto_follow_rows"] = follow_rows
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_evidence_family_avoid_veto",
            enabled=bypass_avoid_veto,
        ):
            summary["evidence_family_avoid_veto_bypassed"] = True
        else:
            return (
                _configured_float(cfg, "evidence_family_avoid_veto_risk_multiplier", 0.0),
                "vnext_risk_evidence_family_avoid_veto",
                summary,
            )
    source_name_veto = _decision_count_veto(
        decision.evidence or {},
        count_key="source_name_decision_counts",
        enabled_key="source_name_avoid_veto_enabled",
        names_key="source_name_avoid_veto_names",
        min_rows_key="source_name_avoid_veto_min_rows",
        dominance_key="source_name_avoid_veto_dominance_ratio",
        default_names=(
            "numeric_router_avoid_score",
            "gate_filter_selector_runtime_mapping",
        ),
        cfg=cfg,
    )
    if source_name_veto:
        source_name, avoid_rows, follow_rows = source_name_veto
        summary["source_name_avoid_veto_name"] = source_name
        summary["source_name_avoid_veto_avoid_rows"] = avoid_rows
        summary["source_name_avoid_veto_follow_rows"] = follow_rows
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_source_name_avoid_veto",
            enabled=bypass_avoid_veto,
        ):
            summary["source_name_avoid_veto_bypassed"] = True
        else:
            return (
                _configured_float(cfg, "source_name_avoid_veto_risk_multiplier", 0.0),
                "vnext_risk_source_name_avoid_veto",
                summary,
            )
    source_role_veto = _decision_count_veto(
        decision.evidence or {},
        count_key="source_role_decision_counts",
        enabled_key="source_role_avoid_veto_enabled",
        names_key="source_role_avoid_veto_roles",
        min_rows_key="source_role_avoid_veto_min_rows",
        dominance_key="source_role_avoid_veto_dominance_ratio",
        default_names=(
            "historical_replay_result_table",
            "default_off_branch_decision",
        ),
        cfg=cfg,
    )
    if source_role_veto:
        source_role, avoid_rows, follow_rows = source_role_veto
        summary["source_role_avoid_veto_role"] = source_role
        summary["source_role_avoid_veto_avoid_rows"] = avoid_rows
        summary["source_role_avoid_veto_follow_rows"] = follow_rows
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_source_role_avoid_veto",
            enabled=bypass_avoid_veto,
        ):
            summary["source_role_avoid_veto_bypassed"] = True
        else:
            return (
                _configured_float(cfg, "source_role_avoid_veto_risk_multiplier", 0.0),
                "vnext_risk_source_role_avoid_veto",
                summary,
            )
    stop_first_rows = _count_evidence_values(
        decision.evidence or {},
        "target_stop_order_class_counts",
        ("STOP_FIRST_PROXY_DOMINANT",),
    )
    target_first_rows = _count_evidence_values(
        decision.evidence or {},
        "target_stop_order_class_counts",
        ("TARGET_FIRST_PROXY_DOMINANT",),
    )
    target_stop_not_source_bound_rows = _count_evidence_values(
        decision.evidence or {},
        "target_stop_order_class_counts",
        ("TARGET_STOP_ORDER_NOT_SOURCE_BOUND",),
    )
    target_stop_ambiguous_rows = _count_evidence_values(
        decision.evidence or {},
        "target_stop_order_class_counts",
        ("TARGET_STOP_AMBIGUOUS_OR_MIXED",),
    )
    summary["stop_first_proxy_rows"] = stop_first_rows
    summary["target_first_proxy_rows"] = target_first_rows
    summary["target_stop_not_source_bound_rows"] = target_stop_not_source_bound_rows
    summary["target_stop_ambiguous_rows"] = target_stop_ambiguous_rows
    min_not_source_bound_rows = int(
        _configured_float(cfg, "target_stop_not_source_bound_risk_min_rows", 1.0)
    )
    if (
        bool(cfg.get("target_stop_not_source_bound_risk_adjustment_enabled", True))
        and target_stop_not_source_bound_rows >= max(1, min_not_source_bound_rows)
        and target_stop_not_source_bound_rows > target_first_rows
        and target_stop_not_source_bound_rows >= stop_first_rows
    ):
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_target_stop_not_source_bound",
            enabled=positive_follow_guard
            and bool(cfg.get("positive_follow_pressure_bypasses_target_stop_geometry", True))
            or source_guarded_positive_proxy_guard
            and bool(cfg.get("source_guarded_positive_proxy_bypasses_target_stop_geometry", True)),
        ):
            summary["target_stop_not_source_bound_bypassed"] = True
        else:
            return (
                _configured_float(cfg, "target_stop_not_source_bound_risk_multiplier", 0.0),
                "vnext_risk_target_stop_not_source_bound",
                summary,
            )
    min_stop_first_rows = int(_configured_float(cfg, "stop_first_risk_min_rows", 1.0))
    if (
        bool(cfg.get("stop_first_risk_adjustment_enabled", True))
        and stop_first_rows >= max(1, min_stop_first_rows)
        and stop_first_rows > target_first_rows
    ):
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_stop_first_proxy",
            enabled=positive_follow_guard
            and bool(cfg.get("positive_follow_pressure_bypasses_target_stop_geometry", True)),
        ):
            summary["stop_first_proxy_bypassed"] = True
        else:
            return (
                _configured_float(cfg, "stop_first_risk_multiplier", 0.0),
                "vnext_risk_stop_first_proxy",
                summary,
            )
    strong_negative_proxy_rows = _count_evidence_values(
        decision.evidence or {},
        "proxy_r_class_counts",
        ("STRONG_NEGATIVE_PROXY_R",),
    )
    strong_positive_proxy_rows = _count_evidence_values(
        decision.evidence or {},
        "proxy_r_class_counts",
        ("STRONG_POSITIVE_PROXY_R",),
    )
    negative_proxy_rows = _count_evidence_values(
        decision.evidence or {},
        "proxy_r_class_counts",
        ("STRONG_NEGATIVE_PROXY_R", "NEGATIVE_PROXY_R"),
    )
    positive_proxy_rows = _count_evidence_values(
        decision.evidence or {},
        "proxy_r_class_counts",
        ("STRONG_POSITIVE_PROXY_R", "POSITIVE_PROXY_R"),
    )
    source_repair_rows = max(
        _count_evidence_values(
            decision.evidence or {},
            "evidence_family_counts",
            ("numeric_router_source_repair",),
        ),
        _count_evidence_values(
            decision.evidence or {},
            "r_evidence_class_counts",
            (
                "SOURCE_REPAIR_FOR_EXACT_R",
                "MAIN_ORCH24_UNIFIED_M1_FILL_ORDERING_SOURCE_REPAIR_REQUIRED",
                "MAIN_ORCH24_UNIFIED_BRANCH_PROXY_SOURCE_REPAIR_REQUIRED",
            ),
        ),
        _count_evidence_values(
            decision.evidence or {},
            "source_group_counts",
            ("source_repair_proof",),
        ),
        _count_evidence_values(
            decision.evidence or {},
            "source_role_counts",
            (
                "exact_r_source_repair_proof",
                "source_repair_execution_plan",
                "source_repair_selector_surface",
                "main_orch24_unified_m1_fill_ordering_source_repair_guard",
                "main_orch24_unified_branch_proxy_source_repair_guard",
            ),
        ),
        _count_evidence_values(
            decision.evidence or {},
            "system_surface_counts",
            (
                "source_repair_proof",
                "source_repair_queue_catalog",
                "numeric_router_source_repair_selector_surface",
                "execution_adjacent_unified_m1_fill_ordering_source_repair",
                "execution_adjacent_unified_branch_proxy_source_repair",
            ),
        ),
    )
    source_acquisition_rows = max(
        _count_evidence_values(
            decision.evidence or {},
            "r_evidence_class_counts",
            (
                "SOURCE_ACQUISITION_FOR_DEPTH_TRANSFER",
                "BRANCH_FOLLOWUP_SOURCE_ACQUISITION_REQUIRED",
                "UNIFIED_CANDIDATE_ACTION_SOURCE_ACQUISITION_REQUIRED",
                "UNIFIED_CANDIDATE_VARIANT_SOURCE_ACQUISITION_REQUIRED",
                "UNIFIED_SHADOW_SCORER_SOURCE_ACQUISITION_REQUIRED",
                "UNIFIED_SOURCE_MATERIALIZATION_SOURCE_ACQUISITION_REQUIRED",
                "SCID_FORWARD_CAPTURE_SOURCE_ACQUISITION_REQUIRED",
                "SCID_FUTURE_CAPTURE_SOURCE_STATE_MATERIALIZATION_REQUIRED",
                "SCID_COMBINED_SOURCE_CAPTURE_REQUIRED",
                "SCID_POI_BOUNDS_SOURCE_CAPTURE_REQUIRED",
                "SCID_NOAPI_SOURCE_ACQUISITION_REQUIRED",
                "SCID_NOAPI_FORBIDDEN_SURFACE_GUARD",
                "PRE_AI_H1_POI_DIRECTIONAL_SOURCE_CAPTURE_REQUIRED",
                "SHADOW_SOURCE_LOG_MATERIALIZATION_REQUIRED",
                "TICK_M15_EXECUTION_FRICTION_ENTRY_GEOMETRY_SOURCE_ACQUISITION_REQUIRED",
                "TICK_M15_TARGET_CONTROL_PLACEBO_READY_SOURCE_ACQUISITION_REQUIRED",
                "MAIN_ORCH24_TICK_SOURCE_ACQUISITION_REQUIRED",
                "MAIN_ORCH24_ENTRY_OFFSET_TICK_SOURCE_ACQUISITION_REQUIRED",
                "MAIN_ORCH24_SOURCE_ACCEPTED_DEGRADED_REDESIGN_EXACT_REPAIR_REQUIRED",
                "MAIN_ORCH24_SWING_PROTECTED_SOURCE_ACQUISITION_REQUIRED",
                "MAIN_ORCH24_SOURCE_M15_SOURCE_ACQUISITION_REQUIRED",
                "MAIN_ORCH24_LIVE_MECHANICAL_SOURCE_ACQUISITION_REQUIRED",
                "MAIN_ORCH24_LIVE_MECHANICAL_AMBIGUOUS_M15_SOURCE_REQUIRED",
                "MAIN_ORCH24_LIVE_MECHANICAL_PENDING_LIFECYCLE_SOURCE_REQUIRED",
                "TICK_SOURCE_RECOVERY_ORDERED_PATH_SOURCE_ACQUISITION_REQUIRED",
                "TICK_SOURCE_RECOVERY_SEPARATE_FILL_PATH_SOURCE_ACQUISITION_REQUIRED",
                "TICK_SOURCE_RECOVERY_OPENING_DRIVE_SOURCE_ACQUISITION_REQUIRED",
                "TICK_SOURCE_RECOVERY_NO_ENTRY_TOUCH_SOURCE_ACQUISITION_REQUIRED",
                "TICK_SOURCE_RECOVERY_NO_TERMINAL_PENDING_SOURCE_ACQUISITION_REQUIRED",
                "TICK_SOURCE_RECOVERY_PARTIAL_COVERAGE_SOURCE_ACQUISITION_REQUIRED",
                "LEGACY_LIVE_SHADOW_V2B_FORWARD_SOURCE_ACQUISITION_REQUIRED",
                "LEGACY_LIVE_SHADOW_FVG_OB_SOURCE_ACQUISITION_REQUIRED",
                "LEGACY_LIVE_SHADOW_NOFILL_CAPTURE_SOURCE_ACQUISITION_REQUIRED",
                "LEGACY_LIVE_SHADOW_XAGUSD_ACCOUNT_HISTORY_SOURCE_ACQUISITION_REQUIRED",
                "MAIN_ORCH24_STRUCTURAL_SOURCE_REPAIR_REQUIRED",
                "MAIN_ORCH24_ACTION_COMPLETENESS_SOURCE_REPAIR_REQUIRED",
                "MAIN_ORCH24_SNAPSHOT_DEPENDENCY_SOURCE_REPAIR_REQUIRED",
                "LIFECYCLE_EXECUTION_SOURCE_ACQUISITION_REQUIRED",
            ),
        ),
        _count_evidence_values(
            decision.evidence or {},
            "source_role_counts",
            (
                "depth_source_acquisition_gate",
                "branch_followup_source_acquisition_guard",
                "unified_candidate_action_source_acquisition_guard",
                "unified_candidate_variant_source_expansion_guard",
                "unified_shadow_scorer_source_materialization_guard",
                "unified_source_materialization_execution_guard",
                "scid_forward_source_capture_lifecycle_guard",
                "scid_future_capture_source_state_guard",
                "scid_combined_source_capture_guard",
                "scid_poi_bounds_source_capture_guard",
                "scid_noapi_source_acquisition_guard",
                "pre_ai_h1_poi_source_gap_guard",
                "shadow_source_log_materialization_guard",
                "tick_m15_entry_geometry_source_acquisition_guard",
                "tick_m15_target_control_placebo_source_acquisition_guard",
                "main_orch24_tick_source_acquisition_guard",
                "main_orch24_entry_offset_tick_source_acquisition_guard",
                "main_orch24_source_accepted_exact_repair_required",
                "main_orch24_swing_protected_source_acquisition_guard",
                "main_orch24_source_m15_source_acquisition_guard",
                "main_orch24_live_mechanical_source_acquisition_guard",
                "main_orch24_live_mechanical_ambiguous_path_guard",
                "main_orch24_live_mechanical_pending_lifecycle_guard",
                "tick_source_recovery_ordered_path_source_acquisition_guard",
                "tick_source_recovery_separate_fill_path_source_acquisition_guard",
                "tick_source_recovery_opening_drive_source_acquisition_guard",
                "tick_source_recovery_no_entry_touch_source_acquisition_guard",
                "tick_source_recovery_no_terminal_pending_guard",
                "tick_source_recovery_partial_coverage_source_acquisition_guard",
                "legacy_live_shadow_v2b_forward_source_acquisition_guard",
                "legacy_live_shadow_fvg_ob_source_acquisition_guard",
                "legacy_live_shadow_nofill_capture_source_acquisition_guard",
                "legacy_live_shadow_xagusd_account_history_source_acquisition_guard",
                "main_orch24_structural_source_repair_requirement_guard",
                "main_orch24_action_completeness_source_repair_requirement_guard",
                "main_orch24_snapshot_dependency_source_repair_guard",
                "lifecycle_execution_source_acquisition_guard",
            ),
        ),
        _count_evidence_values(
            decision.evidence or {},
            "source_component_counts",
            (
                "sierra_depth_source_gap",
                "sierra_depth_window_sample_block",
                "sierra_depth_source_acquisition",
                "gtos_branch_followup_source",
                "unified_candidate_action_source_expansion",
                "unified_candidate_action_concentration_restress",
                "unified_candidate_variant_source_expansion",
                "unified_shadow_scorer_source_materialization",
                "unified_source_materialization_execution",
                "scid_forward_source_capture_lifecycle",
                "scid_future_capture_baseline_control",
                "scid_future_capture_framework_setup",
                "scid_future_capture_entry_reference",
                "scid_future_capture_side_direction",
                "scid_future_capture_stop_reference",
                "scid_future_capture_target_reference",
                "scid_future_capture_lifecycle_status",
                "scid_combined_framework_setup_source_gap",
                "scid_combined_orderflow_depth_source_gap",
                "scid_combined_entry_reference_source_gap",
                "scid_combined_side_direction_source_gap",
                "scid_combined_stop_reference_source_gap",
                "scid_combined_target_reference_source_gap",
                "scid_combined_lifecycle_source_gap",
                "scid_combined_ltf_path_source_gap",
                "scid_combined_poi_bounds_source_gap",
                "scid_noapi_forbidden_surface_guard",
                "scid_noapi_future_capture_source_acquisition",
                "scid_noapi_ltf_orderflow_source_acquisition",
                "scid_noapi_missing_source_acquisition",
                "scid_strategy_field_ltf_orderflow_source_acquisition",
                "scid_strategy_field_missing_source_acquisition",
                "scid_forward_readonly_alignment_source_acquisition",
                "pre_ai_h1_poi_bullish_source_gap",
                "pre_ai_h1_poi_bearish_source_gap",
                "shadow_action_required_source_gap",
                "shadow_candidate_poi_source_gap",
                "shadow_external_source_blocker",
                "shadow_framework_qualification_source_gap",
                "shadow_generic_source_materialization_gap",
                "shadow_join_status_source_gap",
                "shadow_missing_exact_required_fields",
                "shadow_path_contract_source_gap",
                "tick_m15_execution_friction_movement_dominates",
                "tick_m15_target_control_placebo_ready_positive",
                "main_orch24_tick_preserve_source_acquisition",
                "main_orch24_entry_offset_tick_source_acquisition",
                "main_orch24_source_accepted_degraded_redesign_source_acquisition",
                "main_orch24_swing_protected_source_acquisition",
                "main_orch24_source_m15_source_acquisition",
                "main_orch24_live_mechanical_source_acquisition",
                "main_orch24_live_mechanical_ambiguous_path_guard",
                "main_orch24_live_mechanical_pending_lifecycle_guard",
                "tick_source_recovery_ordered_path_source_acquisition",
                "tick_source_recovery_separate_fill_path_source_acquisition",
                "tick_source_recovery_opening_drive_source_acquisition",
                "tick_source_recovery_no_entry_touch_source_acquisition",
                "tick_source_recovery_no_terminal_pending_guard",
                "tick_source_recovery_partial_coverage_source_acquisition",
                "legacy_live_shadow_v2b_forward_source_acquisition",
                "legacy_live_shadow_fvg_ob_source_acquisition",
                "legacy_live_shadow_nofill_capture_source_acquisition",
                "legacy_live_shadow_xagusd_account_history_source_acquisition",
                "main_orch24_structural_source_repair_requirement",
                "main_orch24_action_completeness_source_repair_requirement",
                "main_orch24_snapshot_dependency_source_repair_requirement",
                "lifecycle_still_pending_no_fill_source_guard",
                "lifecycle_wrong_side_no_fill_source_guard",
                "trade_index_lifecycle_action_required_source_repair",
                "opportunity_lifecycle_reset_policy_source_guard",
            ),
        ),
    )
    risk_proxy_stress_cost_repair_rows = max(
        _count_evidence_values(
            decision.evidence or {},
            "r_evidence_class_counts",
            ("RISK_PROXY_STRESS_COST_REPAIR",),
        ),
        _count_evidence_values(
            decision.evidence or {},
            "source_role_counts",
            ("risk_proxy_stress_cost_repair_guard",),
        ),
        _count_evidence_values(
            decision.evidence or {},
            "source_component_counts",
            (
                "risk_source_cost_cap",
                "risk_source_stress_acquisition",
                "risk_cost_fill_proxy",
            ),
        ),
    )
    summary["strong_negative_proxy_r_rows"] = strong_negative_proxy_rows
    summary["strong_positive_proxy_r_rows"] = strong_positive_proxy_rows
    summary["negative_proxy_r_rows"] = negative_proxy_rows
    summary["positive_proxy_r_rows"] = positive_proxy_rows
    summary["risk_proxy_stress_cost_repair_rows"] = risk_proxy_stress_cost_repair_rows
    summary["source_acquisition_required_rows"] = source_acquisition_rows
    summary["source_repair_required_rows"] = source_repair_rows
    min_strong_negative_proxy_rows = int(
        _configured_float(cfg, "strong_negative_proxy_risk_min_rows", 20.0)
    )
    negative_proxy_dominance_ratio = _configured_float(
        cfg,
        "strong_negative_proxy_risk_dominance_ratio",
        2.0,
    )
    if (
        bool(cfg.get("strong_negative_proxy_risk_adjustment_enabled", True))
        and strong_negative_proxy_rows >= max(1, min_strong_negative_proxy_rows)
        and negative_proxy_rows >= positive_proxy_rows * negative_proxy_dominance_ratio
    ):
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_strong_negative_proxy_class",
            enabled=positive_follow_guard
            and bool(cfg.get("positive_follow_pressure_bypasses_negative_proxy_class", True)),
        ):
            summary["strong_negative_proxy_risk_bypassed"] = True
        else:
            return (
                _configured_float(cfg, "strong_negative_proxy_risk_multiplier", 0.0),
                "vnext_risk_strong_negative_proxy_class",
                summary,
            )
    min_ambiguous_rows = int(
        _configured_float(cfg, "target_stop_ambiguous_risk_min_rows", 1.0)
    )
    ambiguous_negative_proxy_dominance_ratio = _configured_float(
        cfg,
        "target_stop_ambiguous_negative_proxy_dominance_ratio",
        1.0,
    )
    if (
        bool(cfg.get("target_stop_ambiguous_risk_adjustment_enabled", True))
        and target_stop_ambiguous_rows >= max(1, min_ambiguous_rows)
        and (
            decision.decision != "FOLLOW"
            or negative_proxy_rows
            >= max(1, positive_proxy_rows) * ambiguous_negative_proxy_dominance_ratio
        )
    ):
        return (
            _configured_float(cfg, "target_stop_ambiguous_risk_multiplier", 0.5),
            "vnext_risk_target_stop_ambiguous_proxy",
            summary,
        )
    min_source_acquisition_rows = int(
        _configured_float(cfg, "source_acquisition_risk_min_rows", 1.0)
    )
    if (
        bool(cfg.get("risk_proxy_stress_cost_repair_adjustment_enabled", True))
        and risk_proxy_stress_cost_repair_rows
        >= max(
            1,
            int(_configured_float(cfg, "risk_proxy_stress_cost_repair_min_rows", 1.0)),
        )
    ):
        return (
            _configured_float(cfg, "risk_proxy_stress_cost_repair_multiplier", 0.0),
            "vnext_risk_proxy_stress_cost_repair",
            summary,
        )
    if (
        bool(cfg.get("source_acquisition_risk_adjustment_enabled", True))
        and source_acquisition_rows >= max(1, min_source_acquisition_rows)
    ):
        return (
            _configured_float(cfg, "source_acquisition_risk_multiplier", 0.0),
            "vnext_risk_source_acquisition_required",
            summary,
        )
    min_source_repair_rows = int(_configured_float(cfg, "source_repair_risk_min_rows", 1.0))
    if (
        bool(cfg.get("source_repair_risk_adjustment_enabled", True))
        and source_repair_rows >= max(1, min_source_repair_rows)
        and source_repair_rows > target_first_rows
    ):
        if _bypass_positive_follow_guard(
            summary,
            "vnext_risk_source_repair_required",
            enabled=positive_follow_guard
            and bool(cfg.get("positive_follow_pressure_bypasses_source_repair", True))
            or source_guarded_positive_proxy_guard
            and bool(cfg.get("source_guarded_positive_proxy_bypasses_source_repair", True)),
        ):
            summary["source_repair_required_bypassed"] = True
        else:
            return (
                _configured_float(cfg, "source_repair_risk_multiplier", 0.0),
                "vnext_risk_source_repair_required",
                summary,
            )
    if decision.decision == "AVOID":
        return _configured_float(cfg, "avoid_risk_multiplier", 0.0), "vnext_risk_avoid", summary
    if decision.decision == "MIXED":
        return _configured_float(cfg, "mixed_risk_multiplier", 0.5), "vnext_risk_mixed", summary
    if decision.decision != "FOLLOW":
        return _configured_float(cfg, "legacy_risk_multiplier", 1.0), "vnext_risk_legacy", summary

    context_guard_rows = max(
        _count_evidence_values(decision.evidence or {}, "source_group_counts", ("context_guard_input",)),
        _count_evidence_values(decision.evidence or {}, "source_role_counts", ("context_guard_input",)),
        _count_evidence_values(decision.evidence or {}, "system_surface_counts", ("context_guard_input",)),
    )
    summary["context_guard_input_rows"] = context_guard_rows
    min_context_guard_rows = int(_configured_float(cfg, "context_guard_risk_min_rows", 1.0))
    if (
        bool(cfg.get("context_guard_risk_adjustment_enabled", True))
        and context_guard_rows >= max(1, min_context_guard_rows)
    ):
        return (
            _configured_float(cfg, "context_guard_risk_multiplier", 0.5),
            "vnext_risk_context_guard_input",
            summary,
        )

    min_strong_positive_proxy_rows = int(
        _configured_float(cfg, "strong_positive_proxy_risk_min_rows", 20.0)
    )
    positive_proxy_dominance_ratio = _configured_float(
        cfg,
        "strong_positive_proxy_risk_dominance_ratio",
        2.0,
    )
    if (
        bool(cfg.get("strong_positive_proxy_risk_adjustment_enabled", True))
        and strong_positive_proxy_rows >= max(1, min_strong_positive_proxy_rows)
        and positive_proxy_rows >= max(1, negative_proxy_rows) * positive_proxy_dominance_ratio
    ):
        return (
            _configured_float(cfg, "strong_positive_proxy_risk_multiplier", 1.25),
            "vnext_risk_strong_positive_proxy_class",
            summary,
        )

    cost_sum = summary["cost_adjusted_simulated_r_sum"]
    stress_sum = summary["stress_simulated_r_sum"]
    proxy_sum = summary["proxy_score_sum"]
    effective_n = summary["effective_n_sum"] or 0.0
    has_negative_pressure = any(
        value is not None and value < 0
        for value in (cost_sum, stress_sum, proxy_sum)
    )
    has_positive_pressure = any(
        value is not None and value > 0
        for value in (cost_sum, stress_sum, proxy_sum)
    )
    if has_negative_pressure:
        return (
            _configured_float(cfg, "follow_conflicted_risk_multiplier", 0.5),
            "vnext_risk_follow_conflicted",
            summary,
        )
    min_strong_n = _configured_float(cfg, "strong_follow_min_effective_n", 100.0)
    if has_positive_pressure and effective_n >= min_strong_n:
        return (
            _configured_float(cfg, "strong_follow_risk_multiplier", 1.25),
            "vnext_risk_strong_follow",
            summary,
        )
    return _configured_float(cfg, "follow_risk_multiplier", 1.0), "vnext_risk_follow", summary


def apply_vnext_risk_adjustment(
    *,
    current_risk_pct: float,
    decision: GTOSVNextRuntimeDecision,
    config: dict[str, Any] | None,
) -> GTOSVNextRiskAdjustment:
    """Return the vNext risk multiplier decision for the current candidate."""
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    enabled = bool(cfg.get("risk_adjustment_enabled", False))
    apply_to_execution = bool(decision.apply_to_execution and enabled)
    if not enabled:
        return GTOSVNextRiskAdjustment(
            enabled=False,
            apply_to_execution=False,
            applied=False,
            decision=decision.decision,
            before_risk_pct=float(current_risk_pct),
            after_risk_pct=float(current_risk_pct),
            multiplier=1.0,
            would_multiplier=1.0,
            reason="vnext_risk_adjustment_disabled",
            evidence_summary=_risk_evidence_summary(decision),
        )

    would_multiplier, reason, summary = _vnext_risk_multiplier(decision, cfg)
    min_multiplier = _configured_float(cfg, "min_risk_multiplier", 0.0)
    max_multiplier = _configured_float(cfg, "max_risk_multiplier", 1.25)
    would_multiplier = max(min_multiplier, min(max_multiplier, would_multiplier))
    multiplier = would_multiplier if apply_to_execution else 1.0
    after_risk_pct = round(float(current_risk_pct) * multiplier, 12)
    return GTOSVNextRiskAdjustment(
        enabled=True,
        apply_to_execution=apply_to_execution,
        applied=apply_to_execution and multiplier != 1.0,
        decision=decision.decision,
        before_risk_pct=float(current_risk_pct),
        after_risk_pct=after_risk_pct,
        multiplier=multiplier,
        would_multiplier=would_multiplier,
        reason=reason if apply_to_execution else f"shadow_{reason}",
        evidence_summary=summary,
    )


def attach_vnext_risk_adjustment_to_record(
    record: dict[str, Any],
    adjustment: GTOSVNextRiskAdjustment,
) -> dict[str, Any]:
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["gtos_vnext_risk_adjustment"] = adjustment.to_record()
    inst = record.setdefault("instrumentation", {})
    inst["gtos_vnext_risk_applied"] = adjustment.applied
    inst["gtos_vnext_risk_multiplier"] = adjustment.multiplier
    inst["gtos_vnext_risk_would_multiplier"] = adjustment.would_multiplier
    inst["gtos_vnext_risk_reason"] = adjustment.reason
    return record


def evaluate_vnext_confidence_override(
    *,
    decision: GTOSVNextRuntimeDecision,
    confidence_grade: str | None,
    config: dict[str, Any] | None,
) -> GTOSVNextGateOverride:
    """Return whether vNext evidence should override active LOW confidence.

    The confidence scorer is intentionally quarantined in config because prior
    evidence showed it was weak. If the operator later activates it anyway, a
    strong vNext FOLLOW can keep the trade route alive, but only under the same
    positive-pressure/effective-N standard used by vNext risk sizing.
    """
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    enabled = bool(cfg.get("confidence_override_enabled", True))
    apply_to_execution = bool(decision.apply_to_execution and enabled)
    summary = _risk_evidence_summary(decision)
    grade = _normalized(confidence_grade).upper()

    def _result(would_apply: bool, reason: str) -> GTOSVNextGateOverride:
        applied = bool(would_apply and apply_to_execution)
        return GTOSVNextGateOverride(
            gate="confidence_low",
            enabled=enabled,
            apply_to_execution=apply_to_execution,
            applied=applied,
            would_apply=bool(would_apply),
            decision=decision.decision,
            reason=reason if applied else f"shadow_{reason}" if would_apply else reason,
            evidence_summary=summary,
        )

    if not enabled:
        return _result(False, "vnext_confidence_override_disabled")
    if grade != "LOW":
        return _result(False, "vnext_confidence_override_not_low_confidence")
    if not decision.enabled or not decision.matched:
        return _result(False, "vnext_confidence_override_no_match")
    if decision.decision != "FOLLOW":
        return _result(False, "vnext_confidence_override_requires_follow")

    _multiplier, risk_reason, _summary = _vnext_risk_multiplier(decision, cfg)
    allowed_risk_reasons = {
        _match_key(reason)
        for reason in _configured_list(
            cfg,
            "confidence_override_risk_reasons",
            ["vnext_risk_strong_follow", "vnext_risk_strong_positive_proxy_class"],
        )
    }
    if _match_key(risk_reason) not in allowed_risk_reasons:
        return _result(False, "vnext_confidence_override_requires_strong_follow")
    if risk_reason == "vnext_risk_strong_positive_proxy_class":
        return _result(True, "vnext_confidence_override_strong_positive_proxy")
    return _result(True, "vnext_confidence_override_strong_follow")


def attach_vnext_confidence_override_to_record(
    record: dict[str, Any],
    override: GTOSVNextGateOverride,
) -> dict[str, Any]:
    """Attach the vNext confidence-gate override decision to a trade record."""
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["gtos_vnext_confidence_override"] = override.to_record()
    inst = record.setdefault("instrumentation", {})
    inst["gtos_vnext_confidence_override_applied"] = override.applied
    inst["gtos_vnext_confidence_override_would_apply"] = override.would_apply
    inst["gtos_vnext_confidence_override_reason"] = override.reason
    return record


def _count_evidence_values(evidence: dict[str, Any], key: str, names: Iterable[str]) -> int:
    counts = evidence.get(key, {}) if isinstance(evidence, dict) else {}
    if not isinstance(counts, dict):
        return 0
    wanted = {_match_key(name) for name in names}
    total = 0
    for name, count in counts.items():
        if _match_key(name) in wanted:
            try:
                total += int(count)
            except (TypeError, ValueError):
                continue
    return total


def _component_decision_count(
    evidence: dict[str, Any],
    components: Iterable[str],
    decision_label: DecisionLabel,
) -> int:
    counts = evidence.get("source_component_decision_counts", {}) if isinstance(evidence, dict) else {}
    if not isinstance(counts, dict):
        return 0
    wanted = {_match_key(component) for component in components}
    total = 0
    for component, decision_counts in counts.items():
        if _match_key(component) not in wanted or not isinstance(decision_counts, dict):
            continue
        try:
            total += int(decision_counts.get(decision_label) or 0)
        except (TypeError, ValueError):
            continue
    return total


def _exit_policy_summary(decision: GTOSVNextRuntimeDecision) -> dict[str, Any]:
    evidence = decision.evidence or {}
    return {
        "matched": decision.matched,
        "decision": decision.decision,
        "reason": decision.reason,
        "decision_counts": evidence.get("decision_counts", {}) if isinstance(evidence, dict) else {},
        "source_component_counts": (
            evidence.get("source_component_counts", {}) if isinstance(evidence, dict) else {}
        ),
        "source_component_decision_counts": (
            evidence.get("source_component_decision_counts", {}) if isinstance(evidence, dict) else {}
        ),
        "r_evidence_class_counts": (
            evidence.get("r_evidence_class_counts", {}) if isinstance(evidence, dict) else {}
        ),
        "route_session_counts": (
            evidence.get("route_session_counts", {}) if isinstance(evidence, dict) else {}
        ),
        "symbol_counts": evidence.get("symbol_counts", {}) if isinstance(evidence, dict) else {},
        "metrics": evidence.get("metrics", {}) if isinstance(evidence, dict) else {},
    }


def evaluate_vnext_exit_management_policy(
    event: dict[str, Any],
    config: dict[str, Any] | None = None,
    *,
    artifact_rows: list[dict[str, Any]] | None = None,
    artifact_index: GTOSVNextEvidenceIndex | None = None,
) -> GTOSVNextExitPolicyDecision:
    """Return vNext exit-policy context from exit-management residue evidence."""
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    enabled = bool(cfg.get("exit_management_residue_policy_enabled", True))
    runtime_enabled = bool(cfg.get("enabled", False))
    normalized_event = normalize_event(event)
    if not enabled or not runtime_enabled:
        return GTOSVNextExitPolicyDecision(
            action="LEGACY_EXIT_POLICY",
            would_action="LEGACY_EXIT_POLICY",
            enabled=False,
            apply_to_execution=False,
            applied=False,
            decision="LEGACY",
            reason="vnext_exit_management_residue_disabled",
            event=normalized_event,
        )

    decision = evaluate_vnext_event(
        event,
        config,
        artifact_rows=artifact_rows,
        artifact_index=artifact_index,
    )
    evidence = decision.evidence or {}
    source_counts = (
        evidence.get("source_component_counts", {}) if isinstance(evidence, dict) else {}
    )

    def has(component: str) -> bool:
        if not isinstance(source_counts, dict):
            return False
        return any(_match_key(name) == _match_key(component) for name in source_counts)

    if not decision.matched:
        would_action: ExitPolicyAction = "LEGACY_EXIT_POLICY"
        reason = "no_matching_exit_management_residue"
    elif has("exit_session_timestamp_source_requirement"):
        would_action = "REQUIRE_ENTRY_EXIT_TIMESTAMPS_BEFORE_SESSION_EXIT_POLICY"
        reason = "exit_session_policy_requires_entry_exit_timestamps"
    elif has("exit_partial_split_policy_guard"):
        would_action = "KEEP_ACTIVE_EXIT_POLICY_PENDING_SIGNIFICANT_PARTIAL_SPLIT_EVIDENCE"
        reason = "partial_split_delta_not_significant"
    elif has("exit_no_event_status_observability"):
        would_action = "PRESERVE_NO_EVENT_EXIT_STATUS_AS_COMPLETE"
        reason = "exit_management_no_event_status_documented"
    elif has("exit_policy_h29_risk_context"):
        would_action = "USE_H29_AWARE_EXIT_REPLAY_CONTEXT"
        reason = "h29_aware_exit_replay_context_matched"
    else:
        would_action = "SHADOW_EXIT_POLICY_CONTEXT"
        reason = "exit_management_residue_context_matched"

    apply_to_execution = bool(
        decision.apply_to_execution
        and cfg.get("exit_management_residue_apply_to_execution", False)
    )
    applied = bool(apply_to_execution and would_action != "LEGACY_EXIT_POLICY")
    action: ExitPolicyAction = (
        would_action if applied else "SHADOW_EXIT_POLICY_CONTEXT"
        if would_action != "LEGACY_EXIT_POLICY"
        else "LEGACY_EXIT_POLICY"
    )
    summary = _exit_policy_summary(decision)
    summary["would_action"] = would_action
    summary["configured_apply_to_execution"] = apply_to_execution
    summary["required_event_fields"] = _configured_list(
        cfg,
        "exit_management_residue_required_timestamp_fields",
        ["entry_time_utc", "exit_time_utc"],
    )
    return GTOSVNextExitPolicyDecision(
        action=action,
        would_action=would_action,
        enabled=True,
        apply_to_execution=apply_to_execution,
        applied=applied,
        decision=decision.decision,
        reason=reason,
        event=normalized_event,
        evidence_summary=summary,
    )


def evaluate_vnext_ready8_failure_control_policy(
    event: dict[str, Any],
    config: dict[str, Any] | None = None,
    *,
    artifact_rows: list[dict[str, Any]] | None = None,
    artifact_index: GTOSVNextEvidenceIndex | None = None,
) -> GTOSVNextReady8ControlPolicyDecision:
    """Return READY8 control/source/geometry policy from residue evidence."""
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    enabled = bool(cfg.get("ready8_failure_control_residue_policy_enabled", True))
    runtime_enabled = bool(cfg.get("enabled", False))
    normalized_event = normalize_event(event)
    if not enabled or not runtime_enabled:
        return GTOSVNextReady8ControlPolicyDecision(
            action="READY8_LEGACY_CONTROL_POLICY",
            would_action="READY8_LEGACY_CONTROL_POLICY",
            enabled=False,
            apply_to_execution=False,
            applied=False,
            decision="LEGACY",
            reason="ready8_failure_control_residue_disabled",
            event=normalized_event,
        )

    policy_config = dict(config or {})
    policy_cfg = dict(cfg)
    policy_cfg["scope_selection_policy"] = str(
        cfg.get(
            "ready8_failure_control_residue_scope_selection_policy",
            "all_matching_anchored",
        )
    )
    policy_cfg["scope_required_anchor_groups"] = cfg.get(
        "ready8_failure_control_residue_scope_required_anchor_groups",
        [["source_component"]],
    )
    policy_config["gtos_vnext_runtime"] = policy_cfg

    decision = evaluate_vnext_event(
        event,
        policy_config,
        artifact_rows=artifact_rows,
        artifact_index=artifact_index,
    )
    evidence = decision.evidence or {}
    source_counts = (
        evidence.get("source_component_counts", {}) if isinstance(evidence, dict) else {}
    )

    def has(component: str) -> bool:
        if not isinstance(source_counts, dict):
            return False
        return any(_match_key(name) == _match_key(component) for name in source_counts)

    if not decision.matched:
        would_action: Ready8ControlPolicyAction = "READY8_LEGACY_CONTROL_POLICY"
        reason = "no_matching_ready8_failure_control_residue"
    elif has("ready8_exact_geometry_source_requirement"):
        would_action = "REQUIRE_READY8_EXACT_GEOMETRY_SOURCE"
        reason = "ready8_requires_source_bound_exact_r_and_target_stop_geometry"
    elif has("ready8_source_control_repair_requirement") or has(
        "ready8_denominator_overlap_requirement"
    ) or has("ready8_fail_closed_source_policy"):
        would_action = "REQUIRE_READY8_SOURCE_CONTROL_REPAIR"
        reason = "ready8_requires_source_control_denominator_or_fail_closed_repair"
    elif has("ready8_card_rank_redundancy_kill") or has("ready8_control_only_quarantine"):
        would_action = "BLOCK_READY8_CARD_RANK_CONTEXT"
        reason = "ready8_card_rank_or_control_only_evidence_is_not_promotional"
    elif has("ready8_promotion_validation_block"):
        would_action = "BLOCK_READY8_PROMOTION_OR_LIVE_USE"
        reason = "ready8_residue_blocks_promotion_validation_or_live_use"
    elif has("ready8_weak_overlap_shadow_only"):
        would_action = "KEEP_READY8_WEAK_OVERLAP_SHADOW_ONLY"
        reason = "ready8_weak_symbol_time_overlap_is_shadow_only"
    else:
        would_action = "SHADOW_READY8_CONTROL_CONTEXT"
        reason = "ready8_failure_control_residue_context_matched"

    apply_to_execution = bool(
        decision.apply_to_execution
        and cfg.get("ready8_failure_control_residue_apply_to_execution", False)
    )
    applied = bool(apply_to_execution and would_action != "READY8_LEGACY_CONTROL_POLICY")
    action: Ready8ControlPolicyAction = (
        would_action
        if applied
        else (
            "SHADOW_READY8_CONTROL_CONTEXT"
            if would_action != "READY8_LEGACY_CONTROL_POLICY"
            else "READY8_LEGACY_CONTROL_POLICY"
        )
    )
    summary = _exit_policy_summary(decision)
    summary["would_action"] = would_action
    summary["configured_apply_to_execution"] = apply_to_execution
    summary["required_source_control_repairs"] = _configured_list(
        cfg,
        "ready8_failure_control_required_repairs",
        [
            "card_specific_predicates",
            "descriptor_contrast_and_overlap_policy",
            "denominator_rules",
            "fail_closed_policy",
            "duplicate_concentration_controls",
            "sealed_stress_partition_preregistration",
            "source_bound_exact_r_geometry",
            "source_bound_target_stop_hit_miss",
        ],
    )
    summary["target_stop_order_class_counts"] = (
        evidence.get("target_stop_order_class_counts", {}) if isinstance(evidence, dict) else {}
    )
    summary["proxy_r_class_counts"] = (
        evidence.get("proxy_r_class_counts", {}) if isinstance(evidence, dict) else {}
    )
    return GTOSVNextReady8ControlPolicyDecision(
        action=action,
        would_action=would_action,
        enabled=True,
        apply_to_execution=apply_to_execution,
        applied=applied,
        decision=decision.decision,
        reason=reason,
        event=normalized_event,
        evidence_summary=summary,
    )


def evaluate_vnext_pending_policy(
    *,
    decision: GTOSVNextRuntimeDecision,
    config: dict[str, Any] | None,
) -> GTOSVNextPendingPolicy:
    """Return whether vNext no-fill evidence should alter pending placement."""
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    enabled = bool(cfg.get("pending_policy_enabled", True))
    pending_apply = bool(cfg.get("pending_policy_apply_to_execution", True))
    apply_to_execution = bool(decision.apply_to_execution and enabled and pending_apply)
    evidence = decision.evidence or {}
    summary = _risk_evidence_summary(decision)
    summary["source_component_counts"] = (
        evidence.get("source_component_counts", {}) if isinstance(evidence, dict) else {}
    )
    summary["target_stop_order_class_counts"] = (
        evidence.get("target_stop_order_class_counts", {}) if isinstance(evidence, dict) else {}
    )
    summary["proxy_r_class_counts"] = (
        evidence.get("proxy_r_class_counts", {}) if isinstance(evidence, dict) else {}
    )
    summary["source_component_decision_counts"] = (
        evidence.get("source_component_decision_counts", {}) if isinstance(evidence, dict) else {}
    )
    nofill_avoid_rows = _count_evidence_values(
        evidence,
        "source_component_counts",
        ("nofill_far_miss_avoid",),
    )
    nofill_market_entry_rows = _count_evidence_values(
        evidence,
        "source_component_counts",
        ("nofill_near_miss_market_entry",),
    )
    nofill_offset_rows = _count_evidence_values(
        evidence,
        "source_component_counts",
        ("nofill_near_miss_offset",),
    )
    nofill_source_requirement_rows = _count_evidence_values(
        evidence,
        "source_component_counts",
        ("nofill_near_miss_source_requirement",),
    )
    static_limit_market_entry_rows = _count_evidence_values(
        evidence,
        "source_component_counts",
        ("static_limit_adaptive_entry_challenger",),
    )
    static_limit_source_requirement_rows = _count_evidence_values(
        evidence,
        "source_component_counts",
        ("static_limit_adaptive_entry_source_requirement",),
    )
    nofill_retest_rows = _count_evidence_values(
        evidence,
        "source_component_counts",
        ("nofill_far_miss_retest", "nofill_far_miss_family"),
    )
    target_first_rows = _count_evidence_values(
        evidence,
        "target_stop_order_class_counts",
        ("TARGET_FIRST_PROXY_DOMINANT",),
    )
    stop_first_rows = _count_evidence_values(
        evidence,
        "target_stop_order_class_counts",
        ("STOP_FIRST_PROXY_DOMINANT",),
    )
    positive_proxy_rows = _count_evidence_values(
        evidence,
        "proxy_r_class_counts",
        ("STRONG_POSITIVE_PROXY_R", "POSITIVE_PROXY_R"),
    )
    negative_proxy_rows = _count_evidence_values(
        evidence,
        "proxy_r_class_counts",
        ("STRONG_NEGATIVE_PROXY_R", "NEGATIVE_PROXY_R"),
    )
    nofill_avoid_component_follow_rows = _component_decision_count(
        evidence,
        ("nofill_far_miss_avoid",),
        "FOLLOW",
    )
    nofill_avoid_component_avoid_rows = _component_decision_count(
        evidence,
        ("nofill_far_miss_avoid",),
        "AVOID",
    )
    nofill_market_entry_component_follow_rows = _component_decision_count(
        evidence,
        ("nofill_near_miss_market_entry",),
        "FOLLOW",
    )
    nofill_market_entry_component_avoid_rows = _component_decision_count(
        evidence,
        ("nofill_near_miss_market_entry",),
        "AVOID",
    )
    nofill_offset_component_follow_rows = _component_decision_count(
        evidence,
        ("nofill_near_miss_offset",),
        "FOLLOW",
    )
    nofill_offset_component_avoid_rows = _component_decision_count(
        evidence,
        ("nofill_near_miss_offset",),
        "AVOID",
    )
    nofill_source_requirement_component_mixed_rows = _component_decision_count(
        evidence,
        ("nofill_near_miss_source_requirement",),
        "MIXED",
    )
    static_limit_market_entry_component_follow_rows = _component_decision_count(
        evidence,
        ("static_limit_adaptive_entry_challenger",),
        "FOLLOW",
    )
    static_limit_market_entry_component_avoid_rows = _component_decision_count(
        evidence,
        ("static_limit_adaptive_entry_challenger",),
        "AVOID",
    )
    static_limit_source_requirement_component_mixed_rows = _component_decision_count(
        evidence,
        ("static_limit_adaptive_entry_source_requirement",),
        "MIXED",
    )
    market_entry_total_rows = nofill_market_entry_rows + static_limit_market_entry_rows
    source_requirement_total_rows = (
        nofill_source_requirement_rows + static_limit_source_requirement_rows
    )
    market_entry_component_follow_rows = (
        nofill_market_entry_component_follow_rows
        + static_limit_market_entry_component_follow_rows
    )
    market_entry_component_avoid_rows = (
        nofill_market_entry_component_avoid_rows
        + static_limit_market_entry_component_avoid_rows
    )
    source_requirement_component_mixed_rows = (
        nofill_source_requirement_component_mixed_rows
        + static_limit_source_requirement_component_mixed_rows
    )
    summary.update(
        {
            "nofill_avoid_rows": nofill_avoid_rows,
            "nofill_market_entry_rows": nofill_market_entry_rows,
            "nofill_offset_rows": nofill_offset_rows,
            "nofill_source_requirement_rows": nofill_source_requirement_rows,
            "static_limit_adaptive_entry_rows": static_limit_market_entry_rows,
            "static_limit_source_requirement_rows": static_limit_source_requirement_rows,
            "market_entry_total_rows": market_entry_total_rows,
            "source_requirement_total_rows": source_requirement_total_rows,
            "nofill_retest_rows": nofill_retest_rows,
            "target_first_proxy_rows": target_first_rows,
            "stop_first_proxy_rows": stop_first_rows,
            "positive_proxy_rows": positive_proxy_rows,
            "negative_proxy_rows": negative_proxy_rows,
            "nofill_avoid_component_follow_rows": nofill_avoid_component_follow_rows,
            "nofill_avoid_component_avoid_rows": nofill_avoid_component_avoid_rows,
            "nofill_market_entry_component_follow_rows": (
                nofill_market_entry_component_follow_rows
            ),
            "nofill_market_entry_component_avoid_rows": (
                nofill_market_entry_component_avoid_rows
            ),
            "nofill_offset_component_follow_rows": nofill_offset_component_follow_rows,
            "nofill_offset_component_avoid_rows": nofill_offset_component_avoid_rows,
            "nofill_source_requirement_component_mixed_rows": (
                nofill_source_requirement_component_mixed_rows
            ),
            "static_limit_market_entry_component_follow_rows": (
                static_limit_market_entry_component_follow_rows
            ),
            "static_limit_market_entry_component_avoid_rows": (
                static_limit_market_entry_component_avoid_rows
            ),
            "static_limit_source_requirement_component_mixed_rows": (
                static_limit_source_requirement_component_mixed_rows
            ),
            "market_entry_component_follow_rows": market_entry_component_follow_rows,
            "market_entry_component_avoid_rows": market_entry_component_avoid_rows,
            "source_requirement_component_mixed_rows": (
                source_requirement_component_mixed_rows
            ),
        }
    )
    min_rows = int(_configured_float(cfg, "pending_policy_min_component_rows", 1.0))
    market_min_rows = int(
        _configured_float(cfg, "pending_policy_market_entry_min_component_rows", float(min_rows))
    )
    offset_min_rows = int(
        _configured_float(cfg, "pending_policy_offset_min_component_rows", float(min_rows))
    )
    source_requirement_min_rows = int(
        _configured_float(
            cfg,
            "pending_policy_source_requirement_min_component_rows",
            float(min_rows),
        )
    )
    market_entry_enabled = bool(cfg.get("pending_policy_market_entry_enabled", True))
    static_limit_market_entry_enabled = bool(
        cfg.get("pending_policy_static_limit_adaptive_entry_enabled", True)
    )
    static_limit_market_min_rows = int(
        _configured_float(
            cfg,
            "pending_policy_static_limit_adaptive_entry_min_component_rows",
            float(market_min_rows),
        )
    )
    offset_avoid_enabled = bool(cfg.get("pending_policy_offset_avoid_enabled", True))
    market_entry_blocks_on_source_requirement = bool(
        cfg.get("pending_policy_market_entry_blocks_on_source_requirement", True)
    )
    market_entry_requires_follow = bool(
        cfg.get("pending_policy_market_entry_requires_follow", True)
    )
    market_entry_requires_positive_proxy = bool(
        cfg.get("pending_policy_market_entry_requires_positive_proxy", True)
    )
    positive_proxy_dominance_ratio = _configured_float(
        cfg,
        "pending_policy_market_entry_positive_proxy_dominance_ratio",
        1.0,
    )
    use_component_decisions = bool(
        cfg.get("pending_policy_use_source_component_decisions", True)
    )
    avoid_requires_component_avoid = bool(
        cfg.get("pending_policy_nofill_avoid_requires_component_avoid", True)
    )
    offset_avoid_requires_component_avoid = bool(
        cfg.get("pending_policy_offset_avoid_requires_component_avoid", True)
    )
    offset_avoid_requires_negative_proxy = bool(
        cfg.get("pending_policy_offset_avoid_requires_negative_proxy", True)
    )
    offset_negative_proxy_dominance_ratio = _configured_float(
        cfg,
        "pending_policy_offset_avoid_negative_proxy_dominance_ratio",
        1.0,
    )
    market_entry_requires_component_follow = bool(
        cfg.get("pending_policy_market_entry_requires_component_follow", True)
    )
    source_requirement_requires_mixed = bool(
        cfg.get("pending_policy_source_requirement_requires_mixed", True)
    )
    component_decision_dominance_ratio = _configured_float(
        cfg,
        "pending_policy_component_decision_dominance_ratio",
        1.0,
    )
    has_component_decision_counts = bool(summary["source_component_decision_counts"])
    proxy_rows_present = positive_proxy_rows > 0 or negative_proxy_rows > 0
    market_entry_follow_ok = not market_entry_requires_follow or decision.decision == "FOLLOW"
    market_entry_proxy_ok = (
        not market_entry_requires_positive_proxy
        or not proxy_rows_present
        or (
            positive_proxy_rows > 0
            and positive_proxy_rows > (negative_proxy_rows * positive_proxy_dominance_ratio)
        )
    )
    market_entry_candidate = (
        market_entry_enabled
        and nofill_market_entry_rows >= max(1, market_min_rows)
        and nofill_market_entry_rows > nofill_avoid_rows
        and nofill_market_entry_rows >= nofill_retest_rows
        and stop_first_rows <= target_first_rows
    )
    static_limit_market_entry_candidate = (
        market_entry_enabled
        and static_limit_market_entry_enabled
        and static_limit_market_entry_rows >= max(1, static_limit_market_min_rows)
        and static_limit_market_entry_rows > nofill_avoid_rows
        and stop_first_rows <= target_first_rows
    )
    market_entry_candidate = market_entry_candidate or static_limit_market_entry_candidate
    nofill_avoid_candidate = (
        nofill_avoid_rows >= max(1, min_rows) and nofill_avoid_rows >= nofill_retest_rows
    )
    nofill_offset_candidate = (
        offset_avoid_enabled
        and nofill_offset_rows >= max(1, offset_min_rows)
        and nofill_offset_rows >= market_entry_total_rows
    )
    nofill_avoid_component_ok = (
        not use_component_decisions
        or not avoid_requires_component_avoid
        or not has_component_decision_counts
        or (
            nofill_avoid_component_avoid_rows >= max(1, min_rows)
            and nofill_avoid_component_avoid_rows
            >= nofill_avoid_component_follow_rows * component_decision_dominance_ratio
        )
    )
    nofill_offset_component_ok = (
        not use_component_decisions
        or not offset_avoid_requires_component_avoid
        or not has_component_decision_counts
        or (
            nofill_offset_component_avoid_rows >= max(1, offset_min_rows)
            and nofill_offset_component_avoid_rows
            >= nofill_offset_component_follow_rows * component_decision_dominance_ratio
        )
    )
    nofill_offset_proxy_ok = (
        not offset_avoid_requires_negative_proxy
        or (
            negative_proxy_rows > 0
            and negative_proxy_rows
            >= max(1, positive_proxy_rows) * offset_negative_proxy_dominance_ratio
        )
    )
    market_entry_component_ok = (
        not use_component_decisions
        or not market_entry_requires_component_follow
        or not has_component_decision_counts
        or (
            nofill_market_entry_component_follow_rows >= max(1, market_min_rows)
            and nofill_market_entry_component_follow_rows
            > nofill_market_entry_component_avoid_rows * component_decision_dominance_ratio
        )
        or (
            static_limit_market_entry_candidate
            and static_limit_market_entry_component_follow_rows
            >= max(1, static_limit_market_min_rows)
            and static_limit_market_entry_component_follow_rows
            > static_limit_market_entry_component_avoid_rows
            * component_decision_dominance_ratio
        )
    )
    static_limit_component_follow_ok = (
        use_component_decisions
        and has_component_decision_counts
        and static_limit_market_entry_candidate
        and static_limit_market_entry_component_follow_rows
        >= max(1, static_limit_market_min_rows)
        and static_limit_market_entry_component_follow_rows
        > static_limit_market_entry_component_avoid_rows
        * component_decision_dominance_ratio
    )
    market_entry_follow_ok = market_entry_follow_ok or static_limit_component_follow_ok
    source_requirement_component_ok = (
        not use_component_decisions
        or not source_requirement_requires_mixed
        or not has_component_decision_counts
        or source_requirement_component_mixed_rows >= max(1, source_requirement_min_rows)
    )
    source_requirement_blocks_market_entry = (
        market_entry_blocks_on_source_requirement
        and source_requirement_total_rows >= max(1, source_requirement_min_rows)
        and source_requirement_component_ok
    )

    would_action: PendingPolicyAction = "PLACE_LIMIT"
    reason = "vnext_pending_policy_place_limit"
    if not enabled:
        reason = "vnext_pending_policy_disabled"
    elif not decision.enabled or not decision.matched:
        reason = "vnext_pending_policy_no_match"
    elif nofill_avoid_candidate and nofill_avoid_component_ok:
        would_action = "SKIP_PENDING_NOFILL_AVOID"
        reason = "vnext_pending_policy_nofill_avoid"
    elif nofill_offset_candidate and nofill_offset_component_ok and nofill_offset_proxy_ok:
        would_action = "SKIP_PENDING_NOFILL_AVOID"
        reason = "vnext_pending_policy_nofill_offset_avoid"
    elif stop_first_rows > target_first_rows and decision.decision == "AVOID":
        would_action = "SKIP_PENDING_NOFILL_AVOID"
        reason = "vnext_pending_policy_stop_first_avoid"
    elif market_entry_candidate and not market_entry_follow_ok:
        reason = "vnext_pending_policy_market_entry_requires_follow"
    elif market_entry_candidate and not market_entry_proxy_ok:
        reason = "vnext_pending_policy_market_entry_proxy_conflict"
    elif market_entry_candidate and not market_entry_component_ok:
        reason = "vnext_pending_policy_market_entry_component_conflict"
    elif market_entry_candidate and source_requirement_blocks_market_entry:
        reason = (
            "vnext_pending_policy_static_limit_adaptive_entry_source_requirement"
            if static_limit_market_entry_candidate
            else "vnext_pending_policy_market_entry_source_requirement"
        )
    elif market_entry_candidate:
        would_action = "MARKET_ENTRY_NOW"
        reason = (
            "vnext_pending_policy_static_limit_adaptive_entry_now"
            if static_limit_market_entry_candidate
            else "vnext_pending_policy_market_entry_now"
        )
    elif nofill_avoid_candidate and not nofill_avoid_component_ok:
        reason = "vnext_pending_policy_nofill_avoid_component_conflict"
    elif nofill_offset_candidate and not nofill_offset_component_ok:
        reason = "vnext_pending_policy_nofill_offset_component_conflict"
    elif nofill_offset_candidate and not nofill_offset_proxy_ok:
        reason = "vnext_pending_policy_nofill_offset_proxy_conflict"

    applied = bool(apply_to_execution and would_action != "PLACE_LIMIT")
    action: PendingPolicyAction = would_action if applied else "PLACE_LIMIT"
    if would_action != "PLACE_LIMIT" and not applied:
        reason = f"shadow_{reason}"
    return GTOSVNextPendingPolicy(
        action=action,
        would_action=would_action,
        enabled=enabled,
        apply_to_execution=apply_to_execution,
        applied=applied,
        decision=decision.decision,
        reason=reason,
        evidence_summary=summary,
    )


def attach_vnext_pending_policy_to_record(
    record: dict[str, Any],
    policy: GTOSVNextPendingPolicy,
) -> dict[str, Any]:
    """Attach the vNext pending-limit policy to a trade record."""
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["gtos_vnext_pending_policy"] = policy.to_record()
    inst = record.setdefault("instrumentation", {})
    inst["gtos_vnext_pending_policy_action"] = policy.action
    inst["gtos_vnext_pending_policy_would_action"] = policy.would_action
    inst["gtos_vnext_pending_policy_applied"] = policy.applied
    inst["gtos_vnext_pending_policy_reason"] = policy.reason
    return record


def _truthy_path_state(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "touch", "touched", "hit"}


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _path_adjusted_entry_price(
    *,
    trade_params: dict[str, Any] | None,
    fallback_direction: str | None,
    offset_r: float,
) -> float | None:
    if not trade_params:
        return None
    direction = str(
        trade_params.get("direction")
        or trade_params.get("side")
        or fallback_direction
        or ""
    ).upper()
    entry = _float_or_none(
        trade_params.get("entry_price")
        if "entry_price" in trade_params
        else trade_params.get("entry")
    )
    stop = _float_or_none(
        trade_params.get("stop_loss")
        if "stop_loss" in trade_params
        else trade_params.get("stop_or_invalidation")
    )
    if entry is None or stop is None or direction not in {"LONG", "SHORT"}:
        return None
    sl_distance = abs(entry - stop)
    if sl_distance <= 0:
        return None
    offset = max(0.0, float(offset_r or 0.0)) * sl_distance
    if direction == "LONG":
        return entry + offset
    return entry - offset


def evaluate_vnext_ltf_path_execution(
    *,
    decision: GTOSVNextRuntimeDecision,
    config: dict[str, Any] | None,
    trade_params: dict[str, Any] | None = None,
    path_state: dict[str, Any] | None = None,
) -> GTOSVNextLTFPathExecutionDecision:
    """Return the Stage06 path-aware entry/no-fill control decision.

    This uses current/as-of path state only. Replay outcome labels stay in the
    evidence summary for auditability; they do not become live decision inputs.
    """
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    enabled = bool(cfg.get("ltf_path_execution_enabled", True))
    apply_flag = bool(cfg.get("ltf_path_execution_apply_to_execution", False))
    apply_to_execution = bool(decision.apply_to_execution and enabled and apply_flag)
    evidence = decision.evidence or {}
    path_state = dict(path_state or {})
    source_counts = (
        evidence.get("source_component_counts", {}) if isinstance(evidence, dict) else {}
    )
    component_decisions = (
        evidence.get("source_component_decision_counts", {})
        if isinstance(evidence, dict)
        else {}
    )
    summary = _risk_evidence_summary(decision)
    summary["source_component_counts"] = source_counts
    summary["source_component_decision_counts"] = component_decisions
    summary["target_stop_order_class_counts"] = (
        evidence.get("target_stop_order_class_counts", {}) if isinstance(evidence, dict) else {}
    )
    summary["proxy_r_class_counts"] = (
        evidence.get("proxy_r_class_counts", {}) if isinstance(evidence, dict) else {}
    )

    min_rows = int(_configured_float(cfg, "ltf_path_execution_min_component_rows", 1.0))
    component_dominance_ratio = _configured_float(
        cfg,
        "ltf_path_execution_component_decision_dominance_ratio",
        1.0,
    )
    market_requires_touch = bool(
        cfg.get("ltf_path_market_entry_requires_path_touch", True)
    )
    monitor_timeframe = str(cfg.get("ltf_path_monitor_timeframe", "M1") or "M1").upper()
    replay_mode = f"{monitor_timeframe.lower()}_path_aware"
    offset_r = _configured_float(cfg, "ltf_path_adjusted_entry_offset_r", 0.5)

    nofill_avoid_rows = _count_evidence_values(
        evidence,
        "source_component_counts",
        ("nofill_far_miss_avoid", "main_orch24_live_mechanical_stop_or_nofill_avoid"),
    )
    market_entry_rows = _count_evidence_values(
        evidence,
        "source_component_counts",
        ("nofill_near_miss_market_entry", "static_limit_adaptive_entry_challenger"),
    )
    offset_rows = _count_evidence_values(
        evidence,
        "source_component_counts",
        ("nofill_near_miss_offset",),
    )
    source_requirement_rows = _count_evidence_values(
        evidence,
        "source_component_counts",
        (
            "nofill_near_miss_source_requirement",
            "static_limit_adaptive_entry_source_requirement",
            "ltf_path_source_blocked_guard",
            "scid_combined_ltf_path_source_gap",
        ),
    )
    ltf_positive_rows = _count_evidence_values(
        evidence,
        "source_component_counts",
        (
            "main_orch24_structural_ltf_positive_follow",
            "main_orch24_unified_tick_m15_path_follow",
            "ltf_path_contract_complete_context",
        ),
    )
    stop_or_nofill_rows = _count_evidence_values(
        evidence,
        "source_component_counts",
        (
            "main_orch24_unified_m1_spread_fill_stop_or_nofill_avoid",
            "tick_source_recovery_quote_tick_nofill_avoid",
        ),
    )
    nofill_avoid_component_avoid_rows = _component_decision_count(
        evidence,
        ("nofill_far_miss_avoid", "main_orch24_live_mechanical_stop_or_nofill_avoid"),
        "AVOID",
    )
    nofill_avoid_component_follow_rows = _component_decision_count(
        evidence,
        ("nofill_far_miss_avoid", "main_orch24_live_mechanical_stop_or_nofill_avoid"),
        "FOLLOW",
    )
    market_entry_component_follow_rows = _component_decision_count(
        evidence,
        ("nofill_near_miss_market_entry", "static_limit_adaptive_entry_challenger"),
        "FOLLOW",
    )
    market_entry_component_avoid_rows = _component_decision_count(
        evidence,
        ("nofill_near_miss_market_entry", "static_limit_adaptive_entry_challenger"),
        "AVOID",
    )
    offset_component_avoid_rows = _component_decision_count(
        evidence,
        ("nofill_near_miss_offset",),
        "AVOID",
    )
    offset_component_follow_rows = _component_decision_count(
        evidence,
        ("nofill_near_miss_offset",),
        "FOLLOW",
    )
    positive_proxy_rows = _count_evidence_values(
        evidence,
        "proxy_r_class_counts",
        ("STRONG_POSITIVE_PROXY_R", "POSITIVE_PROXY_R"),
    )
    negative_proxy_rows = _count_evidence_values(
        evidence,
        "proxy_r_class_counts",
        ("STRONG_NEGATIVE_PROXY_R", "NEGATIVE_PROXY_R"),
    )
    target_first_rows = _count_evidence_values(
        evidence,
        "target_stop_order_class_counts",
        ("TARGET_FIRST_PROXY_DOMINANT",),
    )
    stop_first_rows = _count_evidence_values(
        evidence,
        "target_stop_order_class_counts",
        ("STOP_FIRST_PROXY_DOMINANT",),
    )

    entry_touched = _truthy_path_state(path_state.get("entry_touched"))
    approach_state = str(path_state.get("approach_state") or "").lower()
    near_entry = approach_state in {"near_entry", "entry_touched", "inside_entry_zone"}
    target_before_entry = _truthy_path_state(path_state.get("target_touched_without_entry"))
    protective_before_entry = _truthy_path_state(
        path_state.get("protective_touched_before_entry")
    )
    same_bar_ambiguous = _truthy_path_state(path_state.get("same_bar_ambiguous"))
    source_complete = bool(path_state.get("source_complete", bool(path_state)))

    nofill_avoid_component_ok = (
        nofill_avoid_component_avoid_rows >= max(1, min_rows)
        and nofill_avoid_component_avoid_rows
        >= nofill_avoid_component_follow_rows * component_dominance_ratio
    )
    market_entry_component_ok = (
        market_entry_component_follow_rows >= max(1, min_rows)
        and market_entry_component_follow_rows
        > market_entry_component_avoid_rows * component_dominance_ratio
    )
    offset_component_ok = (
        offset_component_avoid_rows >= max(1, min_rows)
        and offset_component_avoid_rows
        >= offset_component_follow_rows * component_dominance_ratio
    )
    market_entry_evidence_ok = (
        market_entry_rows >= max(1, min_rows)
        and decision.decision == "FOLLOW"
        and (market_entry_component_ok or not component_decisions)
        and positive_proxy_rows >= negative_proxy_rows
        and stop_first_rows <= target_first_rows
    )
    offset_evidence_ok = (
        bool(cfg.get("ltf_path_adjusted_entry_enabled", True))
        and offset_rows >= max(1, min_rows)
        and (offset_component_ok or not component_decisions)
        and negative_proxy_rows >= positive_proxy_rows
    )
    nofill_avoid_evidence_ok = (
        nofill_avoid_rows >= max(1, min_rows)
        and (nofill_avoid_component_ok or not component_decisions)
    )
    source_repair_or_monitor_required = (
        source_requirement_rows >= max(1, min_rows)
        or not source_complete
        or same_bar_ambiguous
    )
    ltf_monitor_evidence = (
        ltf_positive_rows
        + stop_or_nofill_rows
        + nofill_avoid_rows
        + market_entry_rows
        + offset_rows
        + source_requirement_rows
    )
    adjusted_entry_price = _path_adjusted_entry_price(
        trade_params=trade_params,
        fallback_direction=path_state.get("side")
        or path_state.get("direction")
        or (decision.event or {}).get("side"),
        offset_r=offset_r,
    )

    summary.update(
        {
            "nofill_avoid_rows": nofill_avoid_rows,
            "market_entry_rows": market_entry_rows,
            "offset_rows": offset_rows,
            "source_requirement_rows": source_requirement_rows,
            "ltf_positive_rows": ltf_positive_rows,
            "stop_or_nofill_rows": stop_or_nofill_rows,
            "nofill_avoid_component_avoid_rows": nofill_avoid_component_avoid_rows,
            "nofill_avoid_component_follow_rows": nofill_avoid_component_follow_rows,
            "market_entry_component_follow_rows": market_entry_component_follow_rows,
            "market_entry_component_avoid_rows": market_entry_component_avoid_rows,
            "offset_component_avoid_rows": offset_component_avoid_rows,
            "offset_component_follow_rows": offset_component_follow_rows,
            "positive_proxy_rows": positive_proxy_rows,
            "negative_proxy_rows": negative_proxy_rows,
            "target_first_proxy_rows": target_first_rows,
            "stop_first_proxy_rows": stop_first_rows,
            "entry_touched": entry_touched,
            "near_entry": near_entry,
            "target_touched_without_entry": target_before_entry,
            "protective_touched_before_entry": protective_before_entry,
            "same_bar_ambiguous": same_bar_ambiguous,
            "source_complete": source_complete,
            "ltf_monitor_evidence_rows": ltf_monitor_evidence,
            "adjusted_entry_offset_r": offset_r,
        }
    )

    would_action: LTFPathExecutionAction = "PLACE_LIMIT"
    reason = "vnext_ltf_path_place_limit"
    if not enabled:
        reason = "vnext_ltf_path_disabled"
    elif not decision.enabled or not decision.matched:
        reason = "vnext_ltf_path_no_match"
    elif target_before_entry:
        would_action = "MONITOR_LTF_PATH"
        reason = "vnext_ltf_path_target_reached_without_entry_monitor"
    elif protective_before_entry:
        would_action = "MONITOR_LTF_PATH"
        reason = "vnext_ltf_path_protective_area_before_entry_monitor"
    elif nofill_avoid_evidence_ok:
        would_action = "SKIP_LTF_NOFILL_AVOID"
        reason = "vnext_ltf_path_nofill_avoid"
    elif market_entry_evidence_ok and (
        not market_requires_touch or entry_touched or near_entry
    ):
        would_action = "MARKET_ENTRY_NOW"
        reason = "vnext_ltf_path_market_entry_now"
    elif offset_evidence_ok and adjusted_entry_price is not None:
        would_action = "ADJUST_LIMIT_ENTRY"
        reason = "vnext_ltf_path_adjust_limit_entry"
    elif market_entry_evidence_ok or source_repair_or_monitor_required or ltf_monitor_evidence:
        would_action = "MONITOR_LTF_PATH"
        reason = "vnext_ltf_path_monitor_until_touch_or_invalidation"

    applied = bool(apply_to_execution and would_action != "PLACE_LIMIT")
    action: LTFPathExecutionAction = would_action if applied else "PLACE_LIMIT"
    if would_action != "PLACE_LIMIT" and not applied:
        reason = f"shadow_{reason}"
    return GTOSVNextLTFPathExecutionDecision(
        action=action,
        would_action=would_action,
        enabled=enabled,
        apply_to_execution=apply_to_execution,
        applied=applied,
        decision=decision.decision,
        reason=reason,
        monitor_timeframe=monitor_timeframe,
        replay_mode=replay_mode,
        adjusted_entry_price=adjusted_entry_price
        if would_action == "ADJUST_LIMIT_ENTRY"
        else None,
        evidence_summary=summary,
        path_state=path_state,
    )


def attach_vnext_ltf_path_execution_to_record(
    record: dict[str, Any],
    path_decision: GTOSVNextLTFPathExecutionDecision,
) -> dict[str, Any]:
    """Attach the Stage06 LTF path execution decision to a trade record."""
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["gtos_vnext_ltf_path_execution"] = path_decision.to_record()
    inst = record.setdefault("instrumentation", {})
    inst["gtos_vnext_ltf_path_action"] = path_decision.action
    inst["gtos_vnext_ltf_path_would_action"] = path_decision.would_action
    inst["gtos_vnext_ltf_path_applied"] = path_decision.applied
    inst["gtos_vnext_ltf_path_reason"] = path_decision.reason
    inst["gtos_vnext_ltf_path_monitor_timeframe"] = path_decision.monitor_timeframe
    inst["gtos_vnext_ltf_path_adjusted_entry_price"] = (
        path_decision.adjusted_entry_price
    )
    return record


def _coerce_utc_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str) and value.strip():
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _prop_safe_reset_window(
    *,
    current_time_utc: Any,
    reset_offset_hours: float,
    malaysia_offset_hours: float,
) -> dict[str, Any]:
    now_utc = _coerce_utc_datetime(current_time_utc)
    reset_tz = timezone(timedelta(hours=reset_offset_hours))
    malaysia_tz = timezone(timedelta(hours=malaysia_offset_hours))
    reset_local = now_utc.astimezone(reset_tz)
    window_start_local = reset_local.replace(hour=0, minute=0, second=0, microsecond=0)
    window_start_utc = window_start_local.astimezone(timezone.utc)
    next_reset_utc = window_start_utc + timedelta(days=1)
    return {
        "current_time_utc": now_utc.isoformat(),
        "reset_timezone_offset_hours": reset_offset_hours,
        "malaysia_timezone_offset_hours": malaysia_offset_hours,
        "reset_window_start_utc": window_start_utc.isoformat(),
        "next_reset_utc": next_reset_utc.isoformat(),
        "current_reset_local_time": reset_local.isoformat(),
        "next_reset_malaysia_time": next_reset_utc.astimezone(malaysia_tz).isoformat(),
        "daily_loss_reset_model": "00:00_GMT_PLUS_3",
    }


def _money_from_state(
    account_state: dict[str, Any],
    *,
    amount_key: str,
    pct_key: str,
    base_amount: float,
    default: float = 0.0,
) -> float:
    amount = _to_float(account_state.get(amount_key))
    if amount is not None:
        return max(0.0, float(amount))
    pct = _to_float(account_state.get(pct_key))
    if pct is not None:
        return max(0.0, base_amount * float(pct) / 100.0)
    return max(0.0, float(default))


def _pct_from_amount(amount: float, base_amount: float) -> float:
    if base_amount <= 0:
        return 0.0
    return (float(amount) / float(base_amount)) * 100.0


def _route_quality_summary(decision: GTOSVNextRuntimeDecision) -> dict[str, Any]:
    summary = _risk_evidence_summary(decision)
    score = 0.0
    for key in (
        "cost_adjusted_simulated_r_mean",
        "stress_simulated_r_mean",
        "proxy_score_mean",
    ):
        value = _to_float(summary.get(key))
        if value is not None:
            score += float(value)
    return {
        "decision": decision.decision,
        "matched": decision.matched,
        "matched_rows": summary.get("matched_rows", 0),
        "effective_n_sum": summary.get("effective_n_sum"),
        "cost_adjusted_simulated_r_mean": summary.get("cost_adjusted_simulated_r_mean"),
        "stress_simulated_r_mean": summary.get("stress_simulated_r_mean"),
        "proxy_score_mean": summary.get("proxy_score_mean"),
        "route_quality_score": round(score, 12),
        "source_mode_counts": summary.get("source_name_counts", {}),
        "replay_robustness_note": "ranking_context_only_not_a_budget_block",
    }


def evaluate_vnext_selector_v4_admission(
    *,
    config: dict[str, Any] | None,
    candidate_context: dict[str, Any] | None = None,
) -> SelectorV4AdmissionDecision:
    """Evaluate Selector V4 through the vNext runtime bridge.

    This wrapper deliberately performs no broker/account/order work. It binds
    runtime config to the pure Selector V4 authority so the config keys are
    production-code-owned instead of inert route metadata.
    """

    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    return evaluate_selector_v4_admission(
        candidate_context or {},
        config,
        enabled=bool(cfg.get("selector_v4_enabled", False)),
        apply_to_execution=bool(cfg.get("selector_v4_apply_to_execution", False)),
    )


def evaluate_vnext_prop_safe_selector(
    *,
    decision: GTOSVNextRuntimeDecision,
    config: dict[str, Any] | None,
    current_risk_pct: float,
    account_state: dict[str, Any] | None = None,
    current_time_utc: Any = None,
    candidate_context: dict[str, Any] | None = None,
) -> GTOSVNextPropSafeSelectorDecision:
    """Evaluate redacted_account-style budget governance before execution activation.

    redacted_account external math is kept distinct from GTOS' internal 4% emergency
    overlay. The external daily floor is reset-window based and uses:
    day_start_baseline - initial_balance * 5%. The overall floor is static:
    initial_balance * 90%. No trailing drawdown is modeled here.
    """
    root_config = config or {}
    cfg = root_config.get("gtos_vnext_runtime", {}) or {}
    risk_cfg = root_config.get("risk", {}) or {}
    account_state = account_state or {}
    candidate_context = candidate_context or {}
    enabled = bool(cfg.get("prop_safe_selector_enabled", False))
    selector_apply = bool(cfg.get("prop_safe_selector_apply_to_execution", False))
    apply_to_execution = bool(decision.apply_to_execution and enabled and selector_apply)
    before_risk_pct = float(_to_float(current_risk_pct) or 0.0)

    def _result(
        *,
        would_action: PropSafeSelectorAction,
        reason: str,
        after_risk_pct: float,
        max_allowed_pct: float = 0.0,
        reset_window: dict[str, Any] | None = None,
        external: dict[str, Any] | None = None,
        internal: dict[str, Any] | None = None,
        exposure: dict[str, Any] | None = None,
        concentration: dict[str, Any] | None = None,
        route_quality: dict[str, Any] | None = None,
    ) -> GTOSVNextPropSafeSelectorDecision:
        applied = bool(apply_to_execution and would_action != "ALLOW")
        action: PropSafeSelectorAction = would_action if applied else "ALLOW"
        resolved_after = float(after_risk_pct) if applied else before_risk_pct
        resolved_reason = reason if applied or would_action == "ALLOW" else f"shadow_{reason}"
        return GTOSVNextPropSafeSelectorDecision(
            action=action,
            would_action=would_action,
            enabled=enabled,
            apply_to_execution=apply_to_execution,
            applied=applied,
            decision=decision.decision,
            before_risk_pct=before_risk_pct,
            after_risk_pct=round(resolved_after, 12),
            max_allowed_new_trade_risk_pct=round(max(0.0, max_allowed_pct), 12),
            reason=resolved_reason,
            reset_window=reset_window or {},
            external_rule_projection=external or {},
            internal_overlay_projection=internal or {},
            exposure_breakdown=exposure or {},
            concentration=concentration or {},
            route_quality=route_quality or _route_quality_summary(decision),
        )

    if not enabled:
        return _result(
            would_action="ALLOW",
            reason="prop_safe_selector_disabled",
            after_risk_pct=before_risk_pct,
        )

    initial_balance = _to_float(account_state.get("initial_balance"))
    if initial_balance is None:
        initial_balance = _configured_float(cfg, "prop_safe_selector_initial_balance", 100000.0)
    current_equity = _to_float(account_state.get("current_equity"))
    if current_equity is None:
        current_equity = _to_float(account_state.get("equity"))
    if initial_balance is None or initial_balance <= 0 or current_equity is None or current_equity <= 0:
        return _result(
            would_action="BLOCK",
            reason="prop_safe_selector_missing_account_state",
            after_risk_pct=0.0,
            max_allowed_pct=0.0,
        )

    risk_base_amount = _to_float(account_state.get("risk_base_amount"))
    if risk_base_amount is None or risk_base_amount <= 0:
        risk_base_amount = _to_float(account_state.get("current_balance"))
    if risk_base_amount is None or risk_base_amount <= 0:
        risk_base_amount = current_equity

    day_start_baseline = _to_float(account_state.get("day_start_equity_or_balance_baseline"))
    baseline_source = "account_state.day_start_equity_or_balance_baseline"
    if day_start_baseline is None or day_start_baseline <= 0:
        day_start_baseline = _to_float(account_state.get("day_start_equity"))
        baseline_source = "account_state.day_start_equity"
    if day_start_baseline is None or day_start_baseline <= 0:
        day_start_baseline = _to_float(account_state.get("day_start_balance"))
        baseline_source = "account_state.day_start_balance"
    if day_start_baseline is None or day_start_baseline <= 0:
        return _result(
            would_action="BLOCK",
            reason="prop_safe_selector_missing_day_start_baseline",
            after_risk_pct=0.0,
            max_allowed_pct=0.0,
            external={
                "account_model": "redacted_account_100k_static_overall_loss",
                "initial_balance": initial_balance,
                "current_equity": current_equity,
                "day_start_baseline_source": "missing_fail_closed",
                "required_sources": [
                    "account_state.day_start_equity_or_balance_baseline",
                    "account_state.day_start_equity",
                    "account_state.day_start_balance",
                ],
            },
            exposure={
                "current_equity": current_equity,
                "risk_base_amount": risk_base_amount,
            },
            route_quality=_route_quality_summary(decision),
        )

    reset_window = _prop_safe_reset_window(
        current_time_utc=current_time_utc or account_state.get("current_time_utc"),
        reset_offset_hours=_configured_float(
            cfg,
            "prop_safe_selector_daily_reset_timezone_offset_hours",
            3.0,
        ),
        malaysia_offset_hours=_configured_float(
            cfg,
            "prop_safe_selector_malaysia_timezone_offset_hours",
            8.0,
        ),
    )

    open_risk = _money_from_state(
        account_state,
        amount_key="open_position_risk_amount",
        pct_key="open_position_risk_pct",
        base_amount=risk_base_amount,
    )
    pending_risk = _money_from_state(
        account_state,
        amount_key="pending_order_risk_amount",
        pct_key="pending_order_risk_pct",
        base_amount=risk_base_amount,
    )
    new_trade_risk = _money_from_state(
        account_state,
        amount_key="new_trade_sl_risk_amount",
        pct_key="new_trade_sl_risk_pct",
        base_amount=risk_base_amount,
        default=risk_base_amount * before_risk_pct / 100.0,
    )
    spread_buffer = _money_from_state(
        account_state,
        amount_key="spread_slippage_commission_buffer_amount",
        pct_key="spread_slippage_commission_buffer_pct",
        base_amount=risk_base_amount,
        default=risk_base_amount
        * _configured_float(cfg, "prop_safe_selector_spread_slippage_commission_buffer_pct", 0.10)
        / 100.0,
    )
    correlated_buffer = _money_from_state(
        account_state,
        amount_key="correlated_exposure_buffer_amount",
        pct_key="correlated_exposure_buffer_pct",
        base_amount=risk_base_amount,
    )
    concentration_buffer = _money_from_state(
        account_state,
        amount_key="concentration_buffer_amount",
        pct_key="concentration_buffer_pct",
        base_amount=risk_base_amount,
    )
    simultaneous_count = int(_to_float(account_state.get("simultaneous_candidate_count")) or 1)
    simultaneous_reserved = _money_from_state(
        account_state,
        amount_key="simultaneous_candidate_reserved_risk_amount",
        pct_key="simultaneous_candidate_reserved_risk_pct",
        base_amount=risk_base_amount,
    )
    if (
        simultaneous_reserved <= 0
        and simultaneous_count > 1
        and bool(cfg.get("prop_safe_selector_reserve_simultaneous_candidates", True))
    ):
        simultaneous_reserved = max(0, simultaneous_count - 1) * new_trade_risk

    existing_and_buffer_risk = (
        open_risk
        + pending_risk
        + spread_buffer
        + correlated_buffer
        + concentration_buffer
        + simultaneous_reserved
    )
    full_projected_risk = existing_and_buffer_risk + new_trade_risk
    projected_equity = current_equity - full_projected_risk
    projected_equity_before_new_trade = current_equity - existing_and_buffer_risk

    external_daily_pct = _configured_float(
        cfg,
        "prop_safe_selector_external_daily_loss_limit_pct",
        5.0,
    )
    external_overall_pct = _configured_float(
        cfg,
        "prop_safe_selector_external_overall_max_loss_pct",
        10.0,
    )
    daily_loss_amount = initial_balance * external_daily_pct / 100.0
    daily_floor = day_start_baseline - daily_loss_amount
    max_loss_floor = initial_balance * (1.0 - external_overall_pct / 100.0)
    external = {
        "account_model": "redacted_account_100k_static_overall_loss",
        "initial_balance": initial_balance,
        "phase1_target_pct": _configured_float(cfg, "prop_safe_selector_phase1_target_pct", 8.0),
        "phase2_target_pct": _configured_float(cfg, "prop_safe_selector_phase2_target_pct", 5.0),
        "daily_loss_limit_pct": external_daily_pct,
        "daily_loss_amount": daily_loss_amount,
        "day_start_equity_or_balance_baseline": day_start_baseline,
        "day_start_baseline_source": baseline_source,
        "daily_floor": daily_floor,
        "remaining_daily_cushion": current_equity - daily_floor,
        "projected_daily_cushion_before_new_trade": (
            projected_equity_before_new_trade - daily_floor
        ),
        "projected_daily_cushion_after_full_risk": projected_equity - daily_floor,
        "overall_max_loss_pct": external_overall_pct,
        "max_loss_floor": max_loss_floor,
        "remaining_overall_cushion": current_equity - max_loss_floor,
        "projected_overall_cushion_before_new_trade": (
            projected_equity_before_new_trade - max_loss_floor
        ),
        "projected_overall_cushion_after_full_risk": projected_equity - max_loss_floor,
        "trailing_drawdown_modeled": False,
    }

    internal_enabled = bool(cfg.get("prop_safe_selector_internal_daily_overlay_enabled", False))
    internal_source = "gtos_vnext_runtime.prop_safe_selector_internal_daily_overlay_pct"
    internal_pct = _to_float(cfg.get("prop_safe_selector_internal_daily_overlay_pct"))
    if internal_pct is None:
        internal_source = "risk.max_daily_loss_pct"
        internal_pct = _to_float(risk_cfg.get("max_daily_loss_pct"))
    internal_applies = bool(
        internal_enabled
        and internal_pct is not None
        and cfg.get("prop_safe_selector_internal_overlay_applies_to_budget", True)
    )
    internal_floor = None
    internal = {
        "enabled": internal_enabled,
        "applies_to_selector_budget": internal_applies,
        "source": internal_source,
        "daily_loss_limit_pct": internal_pct,
        "distinct_from_redacted_account_external_daily_limit": True,
    }
    if internal_enabled and internal_pct is not None:
        internal_loss_amount = initial_balance * float(internal_pct) / 100.0
        internal_floor = day_start_baseline - internal_loss_amount
        internal.update(
            {
                "daily_loss_amount": internal_loss_amount,
                "daily_floor": internal_floor,
                "remaining_daily_cushion": current_equity - internal_floor,
                "projected_daily_cushion_before_new_trade": (
                    projected_equity_before_new_trade - internal_floor
                ),
                "projected_daily_cushion_after_full_risk": projected_equity - internal_floor,
            }
        )

    exposure = {
        "current_equity": current_equity,
        "risk_base_amount": risk_base_amount,
        "open_position_risk_amount": open_risk,
        "pending_order_risk_amount": pending_risk,
        "new_trade_sl_risk_amount": new_trade_risk,
        "spread_slippage_commission_buffer_amount": spread_buffer,
        "correlated_exposure_buffer_amount": correlated_buffer,
        "concentration_buffer_amount": concentration_buffer,
        "simultaneous_candidate_reserved_risk_amount": simultaneous_reserved,
        "existing_and_buffer_risk_amount": existing_and_buffer_risk,
        "full_projected_risk_amount": full_projected_risk,
        "projected_equity_before_new_trade": projected_equity_before_new_trade,
        "projected_equity_after_full_risk": projected_equity,
    }
    for optional_key in (
        "open_position_count",
        "open_position_risk_valued_count",
        "open_position_risk_pct_fallback_count",
        "open_position_risk_missing_count",
        "open_position_risk_details",
        "open_position_risk_missing_positions",
    ):
        if optional_key in account_state:
            exposure[optional_key] = account_state.get(optional_key)

    open_position_count = int(_to_float(account_state.get("open_position_count")) or 0)
    open_risk_fallback_count = int(
        _to_float(account_state.get("open_position_risk_pct_fallback_count")) or 0
    )
    open_risk_missing_count = int(
        _to_float(account_state.get("open_position_risk_missing_count")) or 0
    )
    if open_position_count > 0 and (open_risk_fallback_count > 0 or open_risk_missing_count > 0):
        exposure["unverified_open_position_risk_block"] = {
            "open_position_count": open_position_count,
            "open_position_risk_pct_fallback_count": open_risk_fallback_count,
            "open_position_risk_missing_count": open_risk_missing_count,
            "requirement": "broker_order_calc_profit_cash_risk_for_all_open_positions",
        }
        return _result(
            would_action="BLOCK",
            reason="prop_safe_selector_unverified_open_position_risk",
            after_risk_pct=0.0,
            max_allowed_pct=0.0,
            reset_window=reset_window,
            external=external,
            internal=internal,
            exposure=exposure,
            route_quality=_route_quality_summary(decision),
        )

    concentration = {
        "symbol": candidate_context.get("symbol") or account_state.get("symbol"),
        "route_session": candidate_context.get("route_session") or account_state.get("route_session"),
        "day_trade_count": int(_to_float(account_state.get("day_trade_count")) or 0),
        "session_trade_count": int(_to_float(account_state.get("session_trade_count")) or 0),
        "symbol_day_trade_count": int(_to_float(account_state.get("symbol_day_trade_count")) or 0),
        "symbol_session_trade_count": int(
            _to_float(account_state.get("symbol_session_trade_count")) or 0
        ),
        "simultaneous_candidate_count": simultaneous_count,
        "concentration_is_budget_buffer_only": True,
    }
    route_quality = _route_quality_summary(decision)

    current_external_overall_breach = external["remaining_overall_cushion"] <= 0
    current_external_daily_breach = external["remaining_daily_cushion"] <= 0
    current_internal_breach = (
        internal_applies
        and internal_floor is not None
        and internal.get("remaining_daily_cushion", 1.0) <= 0
    )

    budget_limits: list[tuple[str, float]] = [
        ("redacted_account_external_daily_5pct", external["remaining_daily_cushion"]),
        ("redacted_account_external_overall_10pct_static", external["remaining_overall_cushion"]),
    ]
    if internal_applies and internal_floor is not None:
        budget_limits.append(("gtos_internal_daily_overlay", internal["remaining_daily_cushion"]))
    available_after_existing = [
        (name, cushion - existing_and_buffer_risk)
        for name, cushion in budget_limits
    ]
    binding_name, max_allowed_new_trade_amount = min(
        available_after_existing,
        key=lambda item: item[1],
    )
    max_allowed_new_trade_risk_pct = _pct_from_amount(
        max_allowed_new_trade_amount,
        risk_base_amount,
    )
    external["binding_budget_after_existing_risk"] = {
        name: amount for name, amount in available_after_existing
    }
    external["binding_budget_name"] = binding_name
    external["max_allowed_new_trade_risk_amount"] = max_allowed_new_trade_amount
    external["max_allowed_new_trade_risk_pct"] = max_allowed_new_trade_risk_pct

    min_reduced_risk_pct = _configured_float(
        cfg,
        "prop_safe_selector_min_reduced_risk_pct",
        0.25,
    )
    overall_allows_after_reset = (
        external["remaining_overall_cushion"] - existing_and_buffer_risk
    ) >= (risk_base_amount * min_reduced_risk_pct / 100.0)
    daily_binding = "daily" in binding_name

    if current_external_overall_breach:
        return _result(
            would_action="BLOCK",
            reason="prop_safe_selector_current_overall_max_loss_breach",
            after_risk_pct=0.0,
            max_allowed_pct=max_allowed_new_trade_risk_pct,
            reset_window=reset_window,
            external=external,
            internal=internal,
            exposure=exposure,
            concentration=concentration,
            route_quality=route_quality,
        )
    if current_external_daily_breach or current_internal_breach:
        would = "DEFER_UNTIL_RESET" if overall_allows_after_reset else "BLOCK"
        reason = (
            "prop_safe_selector_current_daily_loss_window_breach"
            if would == "DEFER_UNTIL_RESET"
            else "prop_safe_selector_current_daily_and_overall_budget_breach"
        )
        return _result(
            would_action=would,
            reason=reason,
            after_risk_pct=0.0,
            max_allowed_pct=max_allowed_new_trade_risk_pct,
            reset_window=reset_window,
            external=external,
            internal=internal,
            exposure=exposure,
            concentration=concentration,
            route_quality=route_quality,
        )

    if max_allowed_new_trade_amount >= new_trade_risk:
        return _result(
            would_action="ALLOW",
            reason="prop_safe_selector_budget_allows_full_risk",
            after_risk_pct=before_risk_pct,
            max_allowed_pct=max_allowed_new_trade_risk_pct,
            reset_window=reset_window,
            external=external,
            internal=internal,
            exposure=exposure,
            concentration=concentration,
            route_quality=route_quality,
        )

    if max_allowed_new_trade_risk_pct >= min_reduced_risk_pct:
        reduced = max(0.0, min(before_risk_pct, max_allowed_new_trade_risk_pct))
        return _result(
            would_action="REDUCE_RISK",
            reason=f"prop_safe_selector_reduce_risk_to_{binding_name}_budget",
            after_risk_pct=reduced,
            max_allowed_pct=max_allowed_new_trade_risk_pct,
            reset_window=reset_window,
            external=external,
            internal=internal,
            exposure=exposure,
            concentration=concentration,
            route_quality=route_quality,
        )

    would = "DEFER_UNTIL_RESET" if daily_binding and overall_allows_after_reset else "BLOCK"
    reason = (
        f"prop_safe_selector_defer_until_reset_{binding_name}_budget"
        if would == "DEFER_UNTIL_RESET"
        else f"prop_safe_selector_block_{binding_name}_budget"
    )
    return _result(
        would_action=would,
        reason=reason,
        after_risk_pct=0.0,
        max_allowed_pct=max_allowed_new_trade_risk_pct,
        reset_window=reset_window,
        external=external,
        internal=internal,
        exposure=exposure,
        concentration=concentration,
        route_quality=route_quality,
    )


def attach_vnext_prop_safe_selector_to_record(
    record: dict[str, Any],
    selector: GTOSVNextPropSafeSelectorDecision,
) -> dict[str, Any]:
    """Attach the vNext prop-safe selector decision to a trade record."""
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["gtos_vnext_prop_safe_selector"] = selector.to_record()
    inst = record.setdefault("instrumentation", {})
    inst["gtos_vnext_prop_safe_selector_action"] = selector.action
    inst["gtos_vnext_prop_safe_selector_would_action"] = selector.would_action
    inst["gtos_vnext_prop_safe_selector_applied"] = selector.applied
    inst["gtos_vnext_prop_safe_selector_reason"] = selector.reason
    inst["gtos_vnext_prop_safe_selector_after_risk_pct"] = selector.after_risk_pct
    inst["gtos_vnext_prop_safe_selector_max_allowed_risk_pct"] = (
        selector.max_allowed_new_trade_risk_pct
    )
    return record


def _moonshot_session_bucket(value: Any) -> str:
    key = _match_key(value).replace("-", "_").replace(" ", "_")
    if not key:
        return "off_kz_broad"
    if key.endswith("_broad"):
        return key
    if key.startswith("moonshot_h"):
        hour_parts = key.removeprefix("moonshot_h").split("_")
        if len(hour_parts) == 2 and all(part.isdigit() for part in hour_parts):
            return "off_kz_broad"
    if "tokyo" in key:
        return "tokyo_broad"
    if key in {"ny", "new_york", "newyork"} or "ny" in key:
        return "ny_broad"
    if "london" in key or key in {"ldn", "lon"}:
        return "london_broad"
    if "off" in key or "dead" in key:
        return "off_kz_broad"
    return f"{key}_broad"


_MOONSHOT_STAGE06_KILL_ZONES_MINUTES = {
    "XAUUSD": (("london", 7 * 60, 10 * 60 + 30), ("ny", 13 * 60, 17 * 60)),
    "XAGUSD": (("london", 7 * 60, 10 * 60 + 30), ("ny", 13 * 60, 17 * 60)),
    "US30": (("london", 8 * 60, 10 * 60 + 30), ("ny", 13 * 60 + 30, 16 * 60)),
    "US30_CASH": (("london", 8 * 60, 10 * 60 + 30), ("ny", 13 * 60 + 30, 16 * 60)),
    "NAS100": (("ny", 13 * 60, 17 * 60),),
    "USDJPY": (("tokyo", 0, 3 * 60), ("london", 7 * 60, 9 * 60 + 30), ("ny", 13 * 60, 15 * 60 + 30)),
    "GBPJPY": (("tokyo", 0, 3 * 60), ("london", 7 * 60, 9 * 60 + 30), ("ny", 13 * 60, 15 * 60 + 30)),
    "GBPUSD": (("london", 7 * 60, 12 * 60), ("ny", 13 * 60, 15 * 60 + 30)),
}


def _moonshot_parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _moonshot_hhmm_to_minutes(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        hour_text, minute_text = str(value).strip().split(":", 1)
        return int(hour_text) * 60 + int(minute_text[:2])
    except (TypeError, ValueError):
        return None


def _moonshot_minute_in_window(minute: int, start: int, end: int) -> bool:
    if start <= end:
        return start <= minute < end
    return minute >= start or minute < end


def _moonshot_stage06_kill_zone_position(symbol: Any, dt: datetime | None) -> str | None:
    if dt is None:
        return None
    symbol_key = _normalized(symbol).upper().replace(".", "_")
    windows = _MOONSHOT_STAGE06_KILL_ZONES_MINUTES.get(symbol_key)
    if not windows:
        return None
    minute = dt.hour * 60 + dt.minute
    for name, start, end in windows:
        if _moonshot_minute_in_window(minute, start, end):
            midpoint = (start + end) / 2
            phase = "early" if minute < midpoint else "late"
            return f"in_{name}_{phase}"
    return "off_configured_kill_zone_or_unconfigured_symbol"


def _moonshot_route_session_name(value: Any) -> str:
    key = _match_key(value).replace("-", "_").replace(" ", "_")
    if "tokyo" in key or "asia" in key:
        return "tokyo"
    if "london" in key or key in {"ldn", "lon"}:
        return "london"
    if "ny" in key or "new_york" in key or "newyork" in key:
        return "ny"
    return key


def _moonshot_utc_hour_bucket(value: Any = None, dt: datetime | None = None) -> str | None:
    explicit = _match_key(value)
    if explicit.startswith("h") and len(explicit) == 6 and explicit[1:3].isdigit() and explicit[4:6].isdigit():
        return explicit
    if dt is None:
        return None
    return f"h{dt.hour:02d}_{(dt.hour + 1) % 24:02d}"


def _moonshot_config_schedule_position(
    *,
    root_cfg: dict[str, Any],
    symbol: Any,
    route_session: Any,
    dt: datetime | None,
) -> str | None:
    if dt is None:
        return None
    symbol_key = _normalized(symbol)
    session_name = _moonshot_route_session_name(route_session)
    if not symbol_key or not session_name:
        return None
    instruments = root_cfg.get("instruments") or {}
    block = instruments.get(symbol_key)
    if block is None:
        normalized_symbols = {
            _normalized(key).upper().replace(".", "_"): key for key in instruments.keys()
        }
        block = instruments.get(
            normalized_symbols.get(symbol_key.upper().replace(".", "_"), "")
        )
    if block is None:
        market_cfg = root_cfg.get("market") if isinstance(root_cfg, dict) else None
        if isinstance(market_cfg, dict):
            root_symbol = _normalized(market_cfg.get("symbol"))
            requested_symbol = _normalized(market_cfg.get("requested_symbol"))
            mt5_symbol = _normalized(market_cfg.get("mt5_symbol"))
            symbol_keys = {
                root_symbol.upper().replace(".", "_"),
                requested_symbol.upper().replace(".", "_"),
                mt5_symbol.upper().replace(".", "_"),
            }
            if symbol_key.upper().replace(".", "_") in symbol_keys:
                block = {"market": market_cfg}
    kill_zones = ((block or {}).get("market") or {}).get("kill_zones") or {}
    normal_kill_zones = {
        name: value
        for name, value in kill_zones.items()
        if name not in {"off_configured_session", "missing_session"}
    }
    if session_name == "missing_session":
        minute = dt.hour * 60 + dt.minute
        for name, schedule in normal_kill_zones.items():
            if not isinstance(schedule, dict):
                continue
            start = _moonshot_hhmm_to_minutes(schedule.get("start_utc"))
            end = _moonshot_hhmm_to_minutes(schedule.get("end_utc"))
            if start is not None and end is not None and _moonshot_minute_in_window(minute, start, end):
                return f"in_{name}_repo_schedule_repaired"
        session_name = "off_configured_session"
    if session_name == "off_configured_session":
        minute = dt.hour * 60 + dt.minute
        for schedule in normal_kill_zones.values():
            if not isinstance(schedule, dict):
                continue
            start = _moonshot_hhmm_to_minutes(schedule.get("start_utc"))
            end = _moonshot_hhmm_to_minutes(schedule.get("end_utc"))
            if start is not None and end is not None and _moonshot_minute_in_window(minute, start, end):
                return "outside_off_configured_session"
        return "in_off_configured_session_repo_schedule_repaired"
    schedule = kill_zones.get(session_name)
    if not isinstance(schedule, dict):
        return None
    start = _moonshot_hhmm_to_minutes(schedule.get("start_utc"))
    end = _moonshot_hhmm_to_minutes(schedule.get("end_utc"))
    if start is None or end is None:
        return None
    minute = dt.hour * 60 + dt.minute
    if _moonshot_minute_in_window(minute, start, end):
        return f"in_{session_name}_repo_schedule_repaired"
    return "outside_repo_configured_kill_zone"


def _moonshot_runtime_kill_zone_position(
    *,
    root_cfg: dict[str, Any],
    symbol: Any,
    route_session: Any,
    dt: datetime | None,
) -> str | None:
    stage06_position = _moonshot_stage06_kill_zone_position(symbol, dt)
    if stage06_position not in (
        None,
        "off_configured_kill_zone_or_unconfigured_symbol",
    ):
        return stage06_position
    config_position = _moonshot_config_schedule_position(
        root_cfg=root_cfg,
        symbol=symbol,
        route_session=route_session,
        dt=dt,
    )
    if config_position is not None:
        return config_position
    return stage06_position


def _moonshot_runtime_instrument_configured(
    *,
    root_cfg: dict[str, Any],
    symbol: Any,
) -> bool | None:
    symbol_key = _normalized(symbol).upper().replace(".", "_")
    if not symbol_key:
        return None

    instruments = root_cfg.get("instruments")
    if isinstance(instruments, dict) and instruments:
        normalized_keys = {
            _normalized(key).upper().replace(".", "_"): key for key in instruments.keys()
        }
        block = instruments.get(normalized_keys.get(symbol_key, ""))
        if isinstance(block, dict):
            market_cfg = block.get("market") if isinstance(block.get("market"), dict) else {}
            return bool(market_cfg.get("mt5_symbol") or market_cfg.get("symbol")) and bool(
                market_cfg.get("kill_zones")
            )
        return False

    market_cfg = root_cfg.get("market") if isinstance(root_cfg, dict) else None
    if not isinstance(market_cfg, dict):
        return None
    market_symbols = {
        _normalized(market_cfg.get("symbol")).upper().replace(".", "_"),
        _normalized(market_cfg.get("requested_symbol")).upper().replace(".", "_"),
        _normalized(market_cfg.get("mt5_symbol")).upper().replace(".", "_"),
    }
    if symbol_key not in market_symbols:
        return False
    return bool(market_cfg.get("mt5_symbol") or market_cfg.get("symbol")) and bool(
        market_cfg.get("kill_zones")
    )


@lru_cache(maxsize=16)
def _moonshot_repaired_branch_allowlist_entries(path_text: str) -> tuple[dict[str, Any], ...]:
    if not path_text:
        return ()
    path = Path(path_text)
    try:
        payload = json.loads(_local_path_for_io(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    entries = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return ()
    return tuple(entry for entry in entries if isinstance(entry, dict))


def _moonshot_branch_allowlist_match(
    cfg: dict[str, Any],
    event: dict[str, Any],
) -> dict[str, Any]:
    raw_path = cfg.get("moonshot_dynamic_execution_router_repaired_branch_allowlist_path")
    entries = _moonshot_repaired_branch_allowlist_entries(str(raw_path or ""))
    branch_label = _normalized(event.get("branch_label")).upper()
    if not branch_label:
        return {
            "repaired_branch_allowed": False,
            "repaired_branch_allowlist_rows": len(entries),
            "repaired_branch_match_reason": "missing_branch_label",
        }
    symbol = _normalized(event.get("symbol")).upper().replace(".", "_")
    framework = _match_key(event.get("framework"))
    origin = _match_key(
        event.get("candidate_origin_family") or f"origin_current_{framework or 'unknown'}"
    )
    session_bucket = _match_key(event.get("session_bucket"))
    kill_zone_position = _match_key(event.get("kill_zone_position"))
    min_rows = int(
        cfg.get("moonshot_dynamic_execution_router_repaired_branch_min_rows")
        or cfg.get("moonshot_dynamic_execution_router_broader_origin_min_group_rows")
        or 20
    )
    for entry in entries:
        allowed_labels = {
            _normalized(label).upper()
            for label in (entry.get("allowed_prior_branch_labels") or ())
        }
        if branch_label not in allowed_labels:
            continue
        if _normalized(entry.get("symbol")).upper().replace(".", "_") != symbol:
            continue
        if _match_key(entry.get("framework")) != framework:
            continue
        if _match_key(entry.get("candidate_origin_family")) != origin:
            continue
        if _match_key(entry.get("session_bucket")) != session_bucket:
            continue
        entry_kill_zone = _match_key(entry.get("kill_zone_bucket"))
        if not kill_zone_position or entry_kill_zone != kill_zone_position:
            continue
        if _match_key(entry.get("repaired_branch_action")) not in {
            "",
            "moonshot_repaired_follow",
        }:
            continue
        if _match_key(entry.get("proof_class")) != "positive_executable_repaired_branch_semantics":
            continue
        metrics = entry.get("repaired_branch_metrics") or entry.get("metrics")
        if not _moonshot_positive_selector_metrics_valid(metrics, min_rows=min_rows):
            continue
        return {
            "repaired_branch_allowed": True,
            "repaired_branch_action": entry.get("repaired_branch_action")
            or "MOONSHOT_REPAIRED_FOLLOW",
            "repaired_branch_proof_class": entry.get("proof_class"),
            "repaired_branch_match_reason": "stage13_allowlist_exact_symbol_framework_origin_session_kz_branch_match",
            "repaired_branch_allowlist_rows": len(entries),
            "repaired_branch_metrics": metrics,
        }
    return {
        "repaired_branch_allowed": False,
        "repaired_branch_allowlist_rows": len(entries),
        "repaired_branch_match_reason": "no_exact_stage13_allowlist_match",
    }


def _moonshot_metric_value(metrics: Any, key: str) -> float | None:
    if not isinstance(metrics, dict):
        return None
    value = metrics.get(key)
    if isinstance(value, dict):
        value = value.get("value") if "value" in value else value.get("sum")
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _moonshot_positive_selector_metrics_valid(
    metrics: Any,
    *,
    min_rows: int,
) -> bool:
    rows = _moonshot_metric_value(metrics, "performance_rows")
    if rows is None:
        rows = _moonshot_metric_value(metrics, "selected_count")
    expectancy = _moonshot_metric_value(metrics, "expectancy_r")
    profit_factor = _moonshot_metric_value(metrics, "profit_factor")
    return bool(
        rows is not None
        and rows >= min_rows
        and expectancy is not None
        and expectancy > 0
        and profit_factor is not None
        and profit_factor > 1
    )


def _moonshot_origin_family_from_event(event: dict[str, Any]) -> str:
    origin = _match_key(event.get("candidate_origin_family"))
    if origin.startswith("origin_"):
        return origin.removeprefix("origin_")
    framework = _match_key(event.get("framework"))
    return framework.removeprefix("origin_")


def _moonshot_selected_cell_risk_source_identity(
    row: dict[str, Any],
    *,
    selected_policy: str | None = None,
    source_policy: str | None = None,
    identity_status: str | None = None,
) -> dict[str, Any]:
    return {
        "risk_cell_id": row.get("risk_cell_id"),
        "symbol": row.get("symbol"),
        "broker_alias": row.get("broker_alias"),
        "broker_spec_id": row.get("broker_spec_id"),
        "selector_component": row.get("selector_component"),
        "family": row.get("family") or row.get("candidate_origin_family"),
        "framework": row.get("framework"),
        "side": row.get("side"),
        "route_session": row.get("route_session"),
        "session_bucket": row.get("session_bucket"),
        "utc_hour_bucket": row.get("utc_hour_bucket"),
        "runtime_selected_policy": selected_policy,
        "source_selected_policy": source_policy or row.get("selected_policy"),
        "policy_identity_status": identity_status,
        "effective_risk_per_trade_pct": row.get("effective_risk_per_trade_pct"),
        "risk_decision_basis": row.get("risk_decision_basis"),
        "source_selector_path": row.get("source_selector_path"),
        "source_selector_entry_sha256": row.get("source_selector_entry_sha256"),
        "source_effective_config_status": row.get("source_effective_config_status"),
        "cell_evidence_granularity": row.get("cell_evidence_granularity"),
        "metric_selected_count": row.get("metric_selected_count"),
        "metric_total_r": row.get("metric_total_r"),
        "metric_profit_factor": row.get("metric_profit_factor"),
        "metric_win_rate": row.get("metric_win_rate"),
        "effective_price_rounding_increment": row.get("effective_price_rounding_increment"),
        "effective_lot_rounding_step": row.get("effective_lot_rounding_step"),
        "exact_unresolved_or_excluded_reasons": (
            row.get("exact_unresolved_or_excluded_reasons") or []
        ),
    }


def _moonshot_selected_cell_capture_contract(
    *,
    status: str,
    source_ledger_path: Any,
    refusal_cause: str | None = None,
    failed_dimensions: list[dict[str, Any]] | None = None,
    nearest_candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "source_ledger_path": source_ledger_path,
        "refusal_cause": refusal_cause,
        "failed_dimensions": failed_dimensions or [],
        "nearest_candidate": nearest_candidate,
        "required_join_keys": [
            "symbol",
            "side",
            "candidate_origin_family_or_framework",
            "route_session_or_session_bucket",
            "utc_hour_bucket_when_dimensioned",
            "selected_policy",
        ],
        "forward_runtime_requirement": (
            "packet must preserve exact failed dimensions, nearest selected-cell "
            "risk candidate, and source ledger row identity when a positive or "
            "zero/unresolved selected-cell row exists"
        ),
    }


@lru_cache(maxsize=16)
def _moonshot_broader_origin_allowlist_entries(path_text: str) -> tuple[dict[str, Any], ...]:
    if not path_text:
        return ()
    path = Path(path_text)
    try:
        payload = json.loads(_local_path_for_io(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    entries = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return ()
    return tuple(entry for entry in entries if isinstance(entry, dict))


@lru_cache(maxsize=16)
def _moonshot_candidate_quality_selector_package(path_text: str) -> dict[str, Any]:
    if not path_text:
        return {}
    path = Path(path_text)
    try:
        payload = json.loads(_local_path_for_io(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _moonshot_candidate_quality_selector_rules(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    package_path = str(cfg.get("moonshot_candidate_quality_selector_package_path") or "")
    package = _moonshot_candidate_quality_selector_package(package_path)
    rules: list[dict[str, Any]] = []
    for key in (
        "avoid_rules",
        "reduce_rules",
        "tradeable_rules",
        "capture_repair_rules",
    ):
        value = package.get(key)
        if isinstance(value, list):
            rules.extend(dict(rule) for rule in value if isinstance(rule, dict))

    inline_rules = cfg.get("moonshot_candidate_quality_selector_tradeable_rules")
    if isinstance(inline_rules, list):
        rules.extend(dict(rule) for rule in inline_rules if isinstance(rule, dict))
    return rules


_GIT_LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"


def _moonshot_selected_cell_risk_signature(
    path_text: str,
) -> tuple[str, int | None, int | None]:
    if not path_text:
        return "", None, None
    path = _local_path_for_io(Path(path_text))
    try:
        stat = path.stat()
    except OSError:
        return str(path), None, None
    return str(path), int(stat.st_mtime_ns), int(stat.st_size)


@lru_cache(maxsize=16)
def _moonshot_selected_cell_risk_load_for_signature(
    path_key: str,
    mtime_ns: int | None,
    size_bytes: int | None,
) -> tuple[tuple[dict[str, Any], ...], dict[str, Any]]:
    status = {
        "path": path_key or None,
        "mtime_ns": mtime_ns,
        "size_bytes": size_bytes,
    }
    if not path_key:
        return (), {
            **status,
            "status": "path_missing_from_runtime_config",
            "status_reason": "selected_cell_risk_ledger_path_not_configured",
        }
    if mtime_ns is None or size_bytes is None:
        return (), {
            **status,
            "status": "file_missing_or_unreadable",
            "status_reason": "selected_cell_risk_ledger_path_missing_or_unreadable",
        }

    path = Path(path_key)
    try:
        first = path.open("rb").read(128)
    except OSError as exc:
        return (), {
            **status,
            "status": "file_missing_or_unreadable",
            "status_reason": f"{exc.__class__.__name__}:{exc}",
        }
    if first.startswith(_GIT_LFS_POINTER_PREFIX):
        return (), {
            **status,
            "status": "raw_lfs_pointer",
            "status_reason": "selected_cell_risk_ledger_is_git_lfs_pointer_not_materialized",
        }

    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    return (), {
                        **status,
                        "status": "parse_failed",
                        "status_reason": f"line_{line_no}:jsonl_row_not_object",
                    }
                rows.append(row)
    except (OSError, json.JSONDecodeError) as exc:
        return (), {
            **status,
            "status": "parse_failed",
            "status_reason": f"{exc.__class__.__name__}:{exc}",
        }

    if not rows:
        return (), {
            **status,
            "status": "zero_rows",
            "status_reason": "selected_cell_risk_ledger_contains_no_jsonl_rows",
            "row_count": 0,
        }
    return tuple(rows), {
        **status,
        "status": "loaded",
        "status_reason": "selected_cell_risk_ledger_loaded_from_current_file_signature",
        "row_count": len(rows),
    }


def _moonshot_selected_cell_risk_load(
    path_text: str,
) -> tuple[tuple[dict[str, Any], ...], dict[str, Any]]:
    signature = _moonshot_selected_cell_risk_signature(path_text)
    return _moonshot_selected_cell_risk_load_for_signature(*signature)


def _moonshot_selected_cell_risk_entries(path_text: str) -> tuple[dict[str, Any], ...]:
    rows, _status = _moonshot_selected_cell_risk_load(path_text)
    return rows


@lru_cache(maxsize=8)
def _moonshot_policy_promotion_evidence(path_text: str) -> dict[str, Any]:
    if not path_text:
        return {}
    path = Path(path_text)
    try:
        payload = json.loads(_local_path_for_io(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    policy_counts = payload.get("policy_counts") if isinstance(payload.get("policy_counts"), dict) else {}
    return {
        "status": payload.get("status"),
        "issue_count": payload.get("issue_count"),
        "checked_rows": payload.get("checked_rows"),
        "policy_counts": policy_counts,
        "summary_path": payload.get("summary_path"),
        "verifier_result_path": payload.get("verifier_result_path"),
        "verified": (
            payload.get("status") == "verified"
            and payload.get("issue_count") == 0
            and int(payload.get("checked_rows") or 0) > 0
            and int(policy_counts.get("momentum_exhaustion") or 0) > 0
            and int(policy_counts.get("partial_be_runner") or 0) > 0
        ),
    }


def _moonshot_selected_cell_risk_match(
    cfg: dict[str, Any],
    event: dict[str, Any],
) -> dict[str, Any]:
    from src.research.moonshot_default_off_policy_router import (
        DEFAULT_POLICY as MOONSHOT_DEFAULT_EXECUTION_POLICY,
        EXECUTION_POLICY_IDS as MOONSHOT_EXECUTION_POLICY_IDS,
        select_asof_displacement_policy,
    )

    critical_prefixes = (
        "digits_",
        "filling_mode_",
        "order_mode_",
        "price_rounding_",
        "lot_rounding_",
        "spread_p95_",
    )
    critical_exact = {
        "eligible_symbol_has_missing_broker_geometry_field_no_default_substitution_allowed",
        "old_three_repaired_branch_allowlist_side_not_dimensioned",
        "selected_cell_sl_distance_distribution_missing_or_incomplete",
    }
    non_blocking_source_facts = {
        "commission_fields_not_exposed_in_current_symbol_info_snapshot",
    }

    def source_blocking_reasons(row: dict[str, Any]) -> list[str]:
        return [
            str(item)
            for item in (row.get("exact_unresolved_or_excluded_reasons") or [])
            if item and str(item) not in non_blocking_source_facts
        ]

    def critical_reasons(row: dict[str, Any]) -> list[str]:
        reasons = source_blocking_reasons(row)
        return sorted(
            {
                reason
                for reason in reasons
                if reason in critical_exact
                or any(reason.startswith(prefix) for prefix in critical_prefixes)
            }
        )

    def row_policy(row: dict[str, Any]) -> str:
        policy = _match_key(row.get("selected_policy"))
        if policy:
            return policy
        sizing_policy = row.get("dynamic_execution_sizing_policy")
        if isinstance(sizing_policy, dict):
            return _match_key(sizing_policy.get("selected_policy"))
        return ""

    def configured_selected_policy() -> str:
        event_for_policy = dict(event)
        event_for_policy.setdefault(
            "primary_policy",
            cfg.get("moonshot_dynamic_execution_router_policy")
            or MOONSHOT_DEFAULT_EXECUTION_POLICY,
        )
        event_for_policy.setdefault(
            "partial_exception_origin_families",
            cfg.get(
                "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner"
            ),
        )
        event_for_policy.setdefault(
            "partial_exception_policy",
            cfg.get("moonshot_dynamic_execution_router_momentum_exception_policy"),
        )
        condition_enabled = bool(
            cfg.get("moonshot_dynamic_execution_router_condition_challenger_enabled", False)
        )
        mode = _match_key(cfg.get("moonshot_dynamic_execution_router_condition_challenger_policy"))
        event_mode = _match_key(event.get("policy_router_mode"))
        if condition_enabled and (mode or event_mode):
            policy, _bucket = select_asof_displacement_policy(event_for_policy)
            return _match_key(policy)
        return _match_key(event_for_policy.get("primary_policy") or MOONSHOT_DEFAULT_EXECUTION_POLICY)

    def policy_invariant_broker_geometry(row: dict[str, Any], selected_policy: str) -> bool:
        if selected_policy not in MOONSHOT_EXECUTION_POLICY_IDS:
            return False
        price_policy = row.get("price_rounding_policy")
        volume_policy = row.get("volume_rounding_policy")
        if not isinstance(price_policy, dict) or not isinstance(volume_policy, dict):
            return False
        try:
            price_increment = float(row.get("effective_price_rounding_increment"))
            lot_step = float(row.get("effective_lot_rounding_step"))
        except (TypeError, ValueError):
            return False
        return bool(
            cfg.get(
                "moonshot_dynamic_execution_router_allow_policy_invariant_selected_cell_risk_geometry",
                False,
            )
            and row.get("source_effective_config_status") == "broker_native_geometry_bound"
            and price_policy.get("status") == "verified_from_broker_spec"
            and volume_policy.get("status") == "verified_from_broker_spec"
            and price_increment > 0
            and lot_step > 0
            and not bool(row.get("uses_unverified_default"))
            and not bool(row.get("stale_old_profile_risk_without_cell_evidence"))
        )

    def attach_policy_identity(
        payload: dict[str, Any],
        *,
        selected_policy: str,
        source_policy: str,
        identity_status: str,
    ) -> dict[str, Any]:
        payload.update(
            {
                "selected_cell_risk_selected_policy": selected_policy,
                "selected_cell_risk_source_policy": source_policy or None,
                "selected_cell_risk_execution_policy_id": MOONSHOT_EXECUTION_POLICY_IDS.get(
                    selected_policy
                ),
                "selected_cell_risk_policy_identity_status": identity_status,
            }
        )
        return payload

    require = bool(cfg.get("moonshot_dynamic_execution_router_require_selected_cell_risk_ledger", False))
    raw_path = cfg.get("moonshot_dynamic_execution_router_selected_cell_risk_ledger_path")
    rows, ledger_load_status = _moonshot_selected_cell_risk_load(str(raw_path or ""))
    if not require:
        return {
            "selected_cell_risk_required": False,
            "selected_cell_risk_allowed": True,
            "selected_cell_risk_match_reason": "risk_ledger_not_required_by_runtime_config",
            "selected_cell_risk_ledger_rows": len(rows),
        }
    if not rows:
        load_status = str(ledger_load_status.get("status") or "empty_or_unreadable")
        if load_status == "raw_lfs_pointer":
            match_reason = "selected_cell_risk_ledger_raw_lfs_pointer"
            refusal_cause = "selected_cell_risk_ledger_raw_lfs_pointer"
        elif load_status == "parse_failed":
            match_reason = "selected_cell_risk_ledger_parse_failed"
            refusal_cause = "selected_cell_risk_ledger_parse_failed"
        else:
            match_reason = "selected_cell_risk_ledger_missing_or_empty"
            refusal_cause = "selected_cell_risk_ledger_missing_or_empty"
        return {
            "selected_cell_risk_required": True,
            "selected_cell_risk_allowed": False,
            "selected_cell_risk_match_reason": match_reason,
            "selected_cell_risk_ledger_rows": 0,
            "selected_cell_risk_source_ledger_path": raw_path,
            "selected_cell_risk_ledger_load_status": ledger_load_status,
            "selected_cell_risk_refusal_cause": refusal_cause,
            "selected_cell_risk_capture_contract": _moonshot_selected_cell_capture_contract(
                status=match_reason,
                source_ledger_path=raw_path,
                refusal_cause=refusal_cause,
            ),
        }
    symbol = _normalized(event.get("symbol")).upper().replace(".", "_")
    side = _normalized(event.get("side")).upper()
    family = _moonshot_origin_family_from_event(event)
    framework = _match_key(event.get("framework"))
    selected_policy = configured_selected_policy()
    route_session = _match_key(event.get("route_session"))
    session_bucket = _match_key(event.get("session_bucket")).removesuffix("_broad")
    session_candidates = {route_session, session_bucket}
    event_hour_bucket = _match_key(event.get("utc_hour_bucket"))
    best_zero: dict[str, Any] | None = None

    def failed_dimensions_for_risk_row(row: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], int]:
        failed: list[dict[str, Any]] = []
        matched: list[str] = []

        def add_match(name: str) -> None:
            matched.append(name)

        row_symbol = _normalized(row.get("symbol")).upper().replace(".", "_")
        if row_symbol == symbol:
            add_match("symbol")
        else:
            failed.append({"field": "symbol", "live": symbol, "risk_row": row_symbol})

        row_component = _match_key(row.get("selector_component"))
        row_family = _match_key(row.get("family") or row.get("candidate_origin_family")).removeprefix("origin_")
        row_framework = _match_key(row.get("framework"))
        if row_component == "broader_origin":
            add_match("selector_component")
            if row_family == family:
                add_match("candidate_origin_family")
            else:
                failed.append(
                    {
                        "field": "candidate_origin_family",
                        "live": family,
                        "risk_row": row_family,
                    }
                )
        elif row_component == "old_three_repaired_branch":
            add_match("selector_component")
            if row_framework == framework:
                add_match("framework")
            else:
                failed.append({"field": "framework", "live": framework, "risk_row": row_framework})
        else:
            failed.append(
                {
                    "field": "selector_component",
                    "live": "broader_origin_or_old_three_repaired_branch",
                    "risk_row": row_component,
                }
            )

        row_side = _normalized(row.get("side")).upper()
        if not row_side or row_side == side:
            add_match("side")
        else:
            failed.append({"field": "side", "live": side, "risk_row": row_side})

        row_session = _match_key(row.get("route_session") or row.get("session_bucket")).removesuffix("_broad")
        if row_session in session_candidates:
            add_match("route_session")
        else:
            failed.append(
                {
                    "field": "route_session",
                    "live": sorted(session_candidates),
                    "risk_row": row_session,
                }
            )

        row_hour = _match_key(row.get("utc_hour_bucket"))
        if row_hour:
            if row_hour == event_hour_bucket:
                add_match("utc_hour_bucket")
            else:
                failed.append(
                    {
                        "field": "utc_hour_bucket",
                        "live": event_hour_bucket,
                        "risk_row": row_hour,
                    }
                )
        else:
            add_match("utc_hour_bucket_not_dimensioned")

        row_selected_policy = row_policy(row)
        if not row_selected_policy or row_selected_policy == selected_policy:
            add_match("selected_policy")
        elif policy_invariant_broker_geometry(row, selected_policy):
            add_match("policy_invariant_selected_cell_risk_geometry")
        else:
            failed.append(
                {
                    "field": "selected_policy",
                    "live": selected_policy,
                    "risk_row": row_selected_policy,
                }
            )

        return failed, matched, len(matched)

    def row_symbol_key(row: dict[str, Any]) -> str:
        return _normalized(row.get("symbol")).upper().replace(".", "_")

    same_symbol_rows = [row for row in rows if row_symbol_key(row) == symbol]

    def nearest_risk_candidate() -> dict[str, Any] | None:
        best: dict[str, Any] | None = None
        candidate_rows = same_symbol_rows if same_symbol_rows else rows
        for row in candidate_rows:
            failed, matched, score = failed_dimensions_for_risk_row(row)
            candidate = {
                "risk_cell_id": row.get("risk_cell_id"),
                "symbol": row.get("symbol"),
                "broker_alias": row.get("broker_alias"),
                "selector_component": row.get("selector_component"),
                "family": row.get("family") or row.get("candidate_origin_family"),
                "side": row.get("side"),
                "route_session": row.get("route_session") or row.get("session_bucket"),
                "utc_hour_bucket": row.get("utc_hour_bucket"),
                "selected_policy": row.get("selected_policy") or row_policy(row),
                "effective_risk_per_trade_pct": row.get("effective_risk_per_trade_pct"),
                "risk_decision_basis": row.get("risk_decision_basis"),
                "exact_unresolved_or_excluded_reasons": row.get("exact_unresolved_or_excluded_reasons") or [],
                "score": score,
                "matched_dimensions": matched,
                "failed_dimensions": failed,
            }
            if best is None or score > int(best.get("score") or -1) or (
                score == int(best.get("score") or -1)
                and len(failed) < len(best.get("failed_dimensions") or [])
            ):
                best = candidate
        return best

    def no_exact_refusal_cause(nearest: dict[str, Any] | None) -> str:
        if not same_symbol_rows:
            return "selected_cell_risk_symbol_absent_from_ledger"
        failed_fields = {
            str(item.get("field"))
            for item in (nearest or {}).get("failed_dimensions") or []
        }
        if "selected_policy" in failed_fields:
            return "policy_identity_mismatch_after_momentum_partial_promotion"
        if "route_session" in failed_fields or "utc_hour_bucket" in failed_fields:
            return "session_or_hour_key_mismatch"
        if "symbol" in failed_fields:
            return "symbol_alias_or_symbol_key_mismatch"
        if "candidate_origin_family" in failed_fields or "framework" in failed_fields:
            return "no_exact_selected_cell_match"
        return "missing_ledger_row"

    for row in rows:
        if _normalized(row.get("symbol")).upper().replace(".", "_") != symbol:
            continue
        row_component = _match_key(row.get("selector_component"))
        row_family = _match_key(row.get("family") or row.get("candidate_origin_family")).removeprefix("origin_")
        row_framework = _match_key(row.get("framework"))
        if row_component == "broader_origin":
            if row_family != family:
                continue
            if _normalized(row.get("side")).upper() != side:
                continue
            if _match_key(row.get("route_session") or row.get("session_bucket")) not in session_candidates:
                continue
            row_hour = _match_key(row.get("utc_hour_bucket"))
            if row_hour and row_hour != event_hour_bucket:
                continue
        elif row_component == "old_three_repaired_branch":
            if row_framework != framework:
                continue
            if row.get("side") not in (None, "") and _normalized(row.get("side")).upper() != side:
                continue
            if _match_key(row.get("session_bucket")).removesuffix("_broad") not in session_candidates:
                continue
        else:
            continue
        row_selected_policy = row_policy(row)
        policy_identity_status = "exact_selected_policy_risk_match"
        if row_selected_policy != selected_policy:
            if not policy_invariant_broker_geometry(row, selected_policy):
                continue
            policy_identity_status = (
                "policy_invariant_broker_geometry_for_selected_execution_policy"
            )
        risk_pct = _moonshot_metric_value(row, "effective_risk_per_trade_pct")
        if risk_pct is not None and risk_pct > 0:
            critical = critical_reasons(row)
            if critical:
                return attach_policy_identity({
                    "selected_cell_risk_required": True,
                    "selected_cell_risk_allowed": False,
                    "selected_cell_risk_pct": 0.0,
                    "selected_cell_risk_cell_id": row.get("risk_cell_id"),
                    "selected_cell_risk_decision_basis": row.get("risk_decision_basis"),
                    "selected_cell_risk_match_reason": "matching_selected_cell_risk_unresolved_execution_critical",
                    "selected_cell_risk_ledger_rows": len(rows),
                    "selected_cell_risk_unresolved_reasons": source_blocking_reasons(row),
                    "selected_cell_risk_execution_critical_unresolved_reasons": critical,
                    "selected_cell_risk_source_ledger_path": raw_path,
                    "selected_cell_risk_source_row_identity": _moonshot_selected_cell_risk_source_identity(
                        row,
                        selected_policy=selected_policy,
                        source_policy=row_selected_policy,
                        identity_status=policy_identity_status,
                    ),
                    "selected_cell_risk_capture_contract": _moonshot_selected_cell_capture_contract(
                        status="unresolved_execution_critical_source_fields",
                        source_ledger_path=raw_path,
                        refusal_cause="unresolved_broker_geometry_or_commission_spread",
                    ),
                }, selected_policy=selected_policy, source_policy=row_selected_policy, identity_status=policy_identity_status)
            match_reason = "exact_selected_cell_risk_positive_match"
            if policy_identity_status.startswith("policy_invariant"):
                match_reason = (
                    "policy_invariant_selected_cell_broker_geometry_positive_match"
                )
            return attach_policy_identity({
                "selected_cell_risk_required": True,
                "selected_cell_risk_allowed": True,
                "selected_cell_risk_pct": risk_pct,
                "selected_cell_risk_cell_id": row.get("risk_cell_id"),
                "selected_cell_risk_decision_basis": row.get("risk_decision_basis"),
                "selected_cell_risk_match_reason": match_reason,
                "selected_cell_risk_ledger_rows": len(rows),
                "selected_cell_risk_unresolved_reasons": source_blocking_reasons(row),
                "selected_cell_risk_source_ledger_path": raw_path,
                "selected_cell_risk_source_row_identity": _moonshot_selected_cell_risk_source_identity(
                    row,
                    selected_policy=selected_policy,
                    source_policy=row_selected_policy,
                    identity_status=policy_identity_status,
                ),
                "selected_cell_risk_capture_contract": _moonshot_selected_cell_capture_contract(
                    status="source_row_bound_no_capture_gap",
                    source_ledger_path=raw_path,
                ),
            }, selected_policy=selected_policy, source_policy=row_selected_policy, identity_status=policy_identity_status)
        best_zero = row

    if best_zero is not None:
        zero_reasons = best_zero.get("exact_unresolved_or_excluded_reasons") or []
        best_zero_policy = row_policy(best_zero)
        return attach_policy_identity({
            "selected_cell_risk_required": True,
            "selected_cell_risk_allowed": False,
            "selected_cell_risk_cell_id": best_zero.get("risk_cell_id"),
            "selected_cell_risk_decision_basis": best_zero.get("risk_decision_basis"),
            "selected_cell_risk_match_reason": "matching_selected_cell_risk_zero_or_unresolved",
            "selected_cell_risk_ledger_rows": len(rows),
            "selected_cell_risk_unresolved_reasons": zero_reasons,
            "selected_cell_risk_refusal_cause": (
                "zero_risk_row"
                if any("risk_zero" in str(item) for item in zero_reasons)
                else "zero_risk_row_or_unresolved_selected_cell"
            ),
            "selected_cell_risk_source_ledger_path": raw_path,
            "selected_cell_risk_source_row_identity": _moonshot_selected_cell_risk_source_identity(
                best_zero,
                selected_policy=selected_policy,
                source_policy=best_zero_policy,
                identity_status="zero_or_unresolved_selected_policy_risk_match",
            ),
            "selected_cell_risk_capture_contract": _moonshot_selected_cell_capture_contract(
                status="risk_zero_or_unresolved_source_row_bound",
                source_ledger_path=raw_path,
                refusal_cause=(
                    "zero_risk_row"
                    if any("risk_zero" in str(item) for item in zero_reasons)
                    else "zero_risk_row_or_unresolved_selected_cell"
                ),
            ),
        }, selected_policy=selected_policy, source_policy=best_zero_policy, identity_status="zero_or_unresolved_selected_policy_risk_match")
    if not same_symbol_rows:
        failed_dimensions = [
            {
                "field": "symbol",
                "live": symbol,
                "risk_row": None,
                "reason": "symbol_not_present_in_selected_cell_risk_ledger",
            }
        ]
        refusal_cause = "selected_cell_risk_symbol_absent_from_ledger"
        nearest_candidate = {
            "status": "not_available",
            "reason": "no_same_symbol_selected_cell_risk_rows",
            "symbol": symbol,
        }
        return {
            "selected_cell_risk_required": True,
            "selected_cell_risk_allowed": False,
            "selected_cell_risk_decision_basis": f"no_exact_selected_cell_risk_match:{refusal_cause}",
            "selected_cell_risk_match_reason": "no_exact_selected_cell_risk_match",
            "selected_cell_risk_ledger_rows": len(rows),
            "selected_cell_risk_selected_policy": selected_policy,
            "selected_cell_risk_execution_policy_id": MOONSHOT_EXECUTION_POLICY_IDS.get(selected_policy),
            "selected_cell_risk_refusal_cause": refusal_cause,
            "selected_cell_risk_failed_dimensions": failed_dimensions,
            "selected_cell_risk_nearest_candidate": nearest_candidate,
            "selected_cell_risk_unresolved_reasons": [refusal_cause],
            "selected_cell_risk_source_ledger_path": raw_path,
            "selected_cell_risk_capture_contract": _moonshot_selected_cell_capture_contract(
                status="exact_selected_cell_source_row_capture_required",
                source_ledger_path=raw_path,
                refusal_cause=refusal_cause,
                failed_dimensions=failed_dimensions,
                nearest_candidate=nearest_candidate,
            ),
        }

    nearest = nearest_risk_candidate()
    failed_dimensions = (nearest or {}).get("failed_dimensions") or []
    refusal_cause = no_exact_refusal_cause(nearest)
    return {
        "selected_cell_risk_required": True,
        "selected_cell_risk_allowed": False,
        "selected_cell_risk_decision_basis": f"no_exact_selected_cell_risk_match:{refusal_cause}",
        "selected_cell_risk_match_reason": "no_exact_selected_cell_risk_match",
        "selected_cell_risk_ledger_rows": len(rows),
        "selected_cell_risk_selected_policy": selected_policy,
        "selected_cell_risk_execution_policy_id": MOONSHOT_EXECUTION_POLICY_IDS.get(selected_policy),
        "selected_cell_risk_refusal_cause": refusal_cause,
        "selected_cell_risk_failed_dimensions": failed_dimensions,
        "selected_cell_risk_nearest_candidate": nearest,
        "selected_cell_risk_unresolved_reasons": [refusal_cause],
        "selected_cell_risk_source_ledger_path": raw_path,
        "selected_cell_risk_capture_contract": _moonshot_selected_cell_capture_contract(
            status="exact_selected_cell_source_row_capture_required",
            source_ledger_path=raw_path,
            refusal_cause=refusal_cause,
            failed_dimensions=failed_dimensions,
            nearest_candidate=nearest,
        ),
    }


def _moonshot_broader_origin_allowlist_match(
    cfg: dict[str, Any],
    event: dict[str, Any],
) -> dict[str, Any]:
    raw_path = cfg.get("moonshot_dynamic_execution_router_broader_origin_allowlist_path")
    entries = _moonshot_broader_origin_allowlist_entries(str(raw_path or ""))
    origin_family = _moonshot_origin_family_from_event(event)
    if not origin_family:
        return {
            "broader_origin_allowed": False,
            "broader_origin_allowlist_rows": len(entries),
            "broader_origin_match_reason": "missing_origin_family",
        }
    symbol = _normalized(event.get("symbol")).upper().replace(".", "_")
    side = _normalized(event.get("side")).upper()
    route_session = _match_key(event.get("route_session"))
    session_bucket = _match_key(event.get("session_bucket")).removesuffix("_broad")
    session_candidates = {route_session, session_bucket}
    if route_session == "off_kz_broad":
        session_candidates.add("off_configured_session")
    primary_policy = _match_key(
        cfg.get("moonshot_dynamic_execution_router_policy") or "momentum_exhaustion"
    )
    allowed_selected_policies = {primary_policy}
    exception_families = {
        _match_key(item)
        for item in _configured_list(
            cfg,
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner",
            (),
        )
    }
    exception_policy = _match_key(
        cfg.get("moonshot_dynamic_execution_router_momentum_exception_policy")
    )
    if origin_family in exception_families and exception_policy:
        allowed_selected_policies.add(exception_policy)
    promotion_evidence = _moonshot_policy_promotion_evidence(
        str(cfg.get("moonshot_dynamic_execution_router_policy_promotion_evidence_path") or "")
    )
    allow_stage13_be_policy_bridge = bool(
        cfg.get("moonshot_dynamic_execution_router_allow_stage13_be_selector_policy_bridge", False)
        and promotion_evidence.get("verified") is True
    )

    def policy_entry_allowed(entry_policy: Any) -> tuple[bool, str, str | None]:
        entry_key = _match_key(entry_policy)
        if entry_key in allowed_selected_policies:
            return True, "exact_selected_policy_selector_match", None
        if (
            allow_stage13_be_policy_bridge
            and entry_key == "be_after_trigger"
            and allowed_selected_policies & {"momentum_exhaustion", "partial_be_runner"}
        ):
            return (
                True,
                "stage13_be_after_trigger_selector_policy_bridge_to_promoted_momentum_partial",
                entry_key,
            )
        return False, "selected_policy_not_in_current_promoted_policy_set", entry_key or None

    min_rows = int(
        cfg.get("moonshot_dynamic_execution_router_broader_origin_min_group_rows")
        or 20
    )
    for entry in entries:
        entry_symbol = _normalized(entry.get("symbol")).upper().replace(".", "_")
        if entry_symbol != symbol:
            continue
        if _match_key(entry.get("origin_family")) != origin_family:
            continue
        if _normalized(entry.get("side")).upper() != side:
            continue
        if _match_key(entry.get("route_session")) not in session_candidates:
            continue
        entry_hour_bucket = _match_key(entry.get("utc_hour_bucket"))
        if entry_hour_bucket:
            event_hour_bucket = _match_key(event.get("utc_hour_bucket"))
            if event_hour_bucket != entry_hour_bucket:
                continue
        policy_allowed, policy_identity_status, source_policy = policy_entry_allowed(
            entry.get("selected_policy")
        )
        if not policy_allowed:
            continue
        if _match_key(entry.get("proof_class")) not in {
            "positive_origin_native_dynamic_replay_row_level_proof",
            "positive_outside_session_origin_native_dynamic_replay_row_level_proof",
        }:
            continue
        if _match_key(entry.get("activation_action")) != "trade_vnext_broader_origin_candidate":
            continue
        if not _moonshot_positive_selector_metrics_valid(
            entry.get("metrics"),
            min_rows=min_rows,
        ):
            continue
        return {
            "broader_origin_allowed": True,
            "broader_origin_activation_action": entry.get("activation_action")
            or "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
            "broader_origin_proof_class": entry.get("proof_class"),
            "broader_origin_match_reason": (
                "stage13_broader_origin_exact_symbol_family_session_side_hour_match"
                if entry.get("utc_hour_bucket")
                else "stage13_broader_origin_exact_symbol_family_session_side_match"
            ),
            "broader_origin_policy_identity_status": policy_identity_status,
            "broader_origin_source_policy": source_policy,
            "broader_origin_current_policy_set": sorted(allowed_selected_policies),
            "broader_origin_policy_promotion_evidence_status": promotion_evidence.get("status"),
            "broader_origin_policy_promotion_checked_rows": promotion_evidence.get("checked_rows"),
            "broader_origin_allowlist_rows": len(entries),
            "broader_origin_metrics": entry.get("metrics"),
            "broader_origin_utc_hour_bucket": entry.get("utc_hour_bucket"),
            "broader_origin_source_row_identity": {
                "symbol": entry.get("symbol"),
                "origin_family": entry.get("origin_family"),
                "candidate_origin_family": entry.get("candidate_origin_family"),
                "side": entry.get("side"),
                "route_session": entry.get("route_session"),
                "utc_hour_bucket": entry.get("utc_hour_bucket"),
                "selected_policy": entry.get("selected_policy"),
                "proof_class": entry.get("proof_class"),
                "activation_action": entry.get("activation_action"),
                "min_group_rows": entry.get("min_group_rows"),
                "metrics": entry.get("metrics"),
            },
        }
    return {
        "broader_origin_allowed": False,
        "broader_origin_allowlist_rows": len(entries),
        "broader_origin_match_reason": "no_exact_stage13_broader_origin_allowlist_match",
        "broader_origin_capture_contract": {
            "status": "exact_stage13_broader_origin_allowlist_row_required",
            "source_allowlist_path": raw_path,
            "required_join_keys": [
                "symbol",
                "origin_family",
                "side",
                "route_session",
                "utc_hour_bucket_when_dimensioned",
                "selected_policy_or_policy_bridge",
            ],
        },
    }


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _context_value(
    *,
    field: str,
    cfg: dict[str, Any],
    candidate_context: dict[str, Any],
    event: dict[str, Any],
    default_config_key: str | None = None,
    default: Any = None,
) -> Any:
    value = _first_present(candidate_context.get(field), event.get(field))
    if value not in (None, ""):
        return value
    if default_config_key:
        return cfg.get(default_config_key, default)
    return default


def build_vnext_moonshot_dynamic_execution_event(
    *,
    decision: GTOSVNextRuntimeDecision,
    config: dict[str, Any] | None,
    candidate_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the as-of event consumed by the moonshot dynamic router."""
    root_cfg = config or {}
    cfg = root_cfg.get("gtos_vnext_runtime", {}) or {}
    context = dict(candidate_context or {})
    event = dict(decision.event or {})
    symbol = _first_present(context.get("symbol"), event.get("symbol"))
    framework = _first_present(
        context.get("framework"),
        event.get("effective_framework"),
        event.get("framework"),
        event.get("route_family"),
    )
    route_session = _first_present(
        context.get("session_bucket"),
        context.get("route_session"),
        context.get("kill_zone"),
        context.get("session"),
        event.get("route_session"),
        event.get("kill_zone"),
        event.get("session"),
    )
    candle_time_utc = _first_present(
        context.get("candle_time_utc"),
        context.get("time_utc"),
        context.get("timestamp_utc"),
        context.get("time"),
        event.get("candle_time_utc"),
        event.get("time_utc"),
        event.get("timestamp_utc"),
        event.get("time"),
    )
    parsed_candle_dt = _moonshot_parse_dt(candle_time_utc)
    utc_hour_bucket = _first_present(
        context.get("utc_hour_bucket"),
        event.get("utc_hour_bucket"),
        _moonshot_utc_hour_bucket(dt=parsed_candle_dt),
    )
    raw_route_session_name = _moonshot_route_session_name(route_session)
    if raw_route_session_name == "missing_session" and parsed_candle_dt is not None:
        repaired_session_position = _moonshot_config_schedule_position(
            root_cfg=root_cfg,
            symbol=symbol,
            route_session="missing_session",
            dt=parsed_candle_dt,
        )
        if isinstance(repaired_session_position, str):
            if repaired_session_position.startswith("in_off_configured_session"):
                route_session = "off_configured_session"
            elif repaired_session_position.startswith("in_"):
                route_session = repaired_session_position.split("_repo_schedule_repaired", 1)[0].removeprefix("in_")
    computed_kill_zone_position = _moonshot_runtime_kill_zone_position(
        root_cfg=root_cfg,
        symbol=symbol,
        route_session=route_session,
        dt=parsed_candle_dt,
    )
    kill_zone_position = _first_present(
        context.get("kill_zone_position"),
        event.get("kill_zone_position"),
    )
    if (
        computed_kill_zone_position not in (None, "")
        and str(kill_zone_position or "").endswith("_runtime_configured_kill_zone")
    ):
        kill_zone_position = computed_kill_zone_position
    if kill_zone_position in (None, ""):
        kill_zone_position = computed_kill_zone_position
    require_configured_kill_zone = bool(
        cfg.get("moonshot_dynamic_execution_router_require_configured_kill_zone", True)
    )
    if kill_zone_position in (None, "") and not require_configured_kill_zone:
        raw_kill_zone = _first_present(context.get("kill_zone"), event.get("kill_zone"))
        if raw_kill_zone not in (None, ""):
            kill_zone_position = f"in_{str(raw_kill_zone).strip().lower()}_runtime_configured_kill_zone"

    source_window_complete = _first_present(
        context.get("source_window_complete"),
        event.get("source_window_complete"),
    )
    if source_window_complete in (None, "") and "source_complete" in context:
        source_window_complete = context.get("source_complete")
    if source_window_complete in (None, ""):
        production_replacement_active = (
            _match_key(cfg.get("mode")) == "production_replacement_vnext_moonshot"
            and bool(cfg.get("apply_to_execution", False))
        )
        source_window_complete = (
            False
            if production_replacement_active
            else cfg.get("moonshot_dynamic_execution_router_default_source_window_complete", True)
        )

    ordered_path_status = _context_value(
        field="ordered_path_status",
        cfg=cfg,
        candidate_context=context,
        event=event,
        default_config_key="moonshot_dynamic_execution_router_default_ordered_path_status",
        default="ordered_path_not_ambiguous_in_m15_replay",
    )
    if _truthy(context.get("same_bar_ambiguous")):
        ordered_path_status = "same_bar_ambiguous_requires_ltf_or_tick_ordering"
    selected_policy_same_bar_ambiguous = _first_present(
        context.get("selected_policy_same_bar_ambiguous"),
        event.get("selected_policy_same_bar_ambiguous"),
    )
    selected_policy_ordered_path_status = _context_value(
        field="selected_policy_ordered_path_status",
        cfg=cfg,
        candidate_context=context,
        event=event,
    )
    if selected_policy_ordered_path_status in (None, ""):
        selected_policy_ordered_path_status = ordered_path_status
    if selected_policy_same_bar_ambiguous in (None, ""):
        selected_policy_same_bar_ambiguous = context.get("same_bar_ambiguous")
    if _truthy(selected_policy_same_bar_ambiguous):
        selected_policy_ordered_path_status = "same_bar_ambiguous_requires_ltf_or_tick_ordering"

    policy_router_mode = _context_value(
        field="policy_router_mode",
        cfg=cfg,
        candidate_context=context,
        event=event,
    )
    condition_challenger_enabled = bool(
        cfg.get("moonshot_dynamic_execution_router_condition_challenger_enabled", False)
    )
    if condition_challenger_enabled:
        policy_router_mode = cfg.get(
            "moonshot_dynamic_execution_router_condition_challenger_policy",
            "condition_asof_displacement_v1",
        )
    else:
        policy_router_mode = None

    activated_frameworks = _configured_list(
        cfg,
        "moonshot_dynamic_execution_router_activated_frameworks",
        ("breaker_re_entry", "fvg_fill", "ob_retest"),
    )
    activated_origin_families = _configured_list(
        cfg,
        "moonshot_dynamic_execution_router_activated_origin_families",
        (),
    )
    required_branch_labels = _configured_list(
        cfg,
        "moonshot_dynamic_execution_router_required_branch_labels",
        ("FOLLOW",),
    )
    eligible_symbols = _configured_list(
        cfg,
        "moonshot_dynamic_execution_router_broker_native_eligible_symbols",
        (),
    )
    excluded_symbols = _configured_list(
        cfg,
        "moonshot_dynamic_execution_router_broker_native_exact_excluded_symbols",
        (),
    )
    symbol_key = _normalized(symbol).upper().replace(".", "_")
    eligible_keys = {
        _normalized(item).upper().replace(".", "_") for item in eligible_symbols
    }
    excluded_keys = {
        _normalized(item).upper().replace(".", "_") for item in excluded_symbols
    }
    runtime_instrument_configured = _moonshot_runtime_instrument_configured(
        root_cfg=root_cfg,
        symbol=symbol,
    )

    router_event = {
        "symbol": symbol,
        "broker_symbol": _first_present(context.get("broker_symbol"), event.get("broker_symbol")),
        "candidate_id": _first_present(context.get("candidate_id"), event.get("candidate_id")),
        "side": _first_present(context.get("side"), event.get("side"), event.get("direction")),
        "framework": framework,
        "candidate_origin_family": _first_present(
            context.get("candidate_origin_family"),
            event.get("candidate_origin_family"),
            f"origin_current_{str(framework or 'unknown').strip()}",
        ),
        "route_family": _first_present(context.get("route_family"), event.get("route_family")),
        "route_session": route_session,
        "session_bucket": _moonshot_session_bucket(route_session),
        "kill_zone_position": kill_zone_position,
        "candle_time_utc": candle_time_utc,
        "utc_hour_bucket": utc_hour_bucket,
        "branch_label": _first_present(
            context.get("branch_label"),
            event.get("branch_label"),
            decision.decision,
        ),
        "branch_reason": _first_present(
            context.get("branch_reason"),
            event.get("branch_reason"),
            decision.reason,
        ),
        "activated_frameworks": activated_frameworks,
        "activated_origin_families": activated_origin_families,
        "required_branch_labels": required_branch_labels,
        "broker_native_eligible_symbols": eligible_symbols,
        "broker_native_exact_excluded_symbols": excluded_symbols,
        "broker_native_eligible": (
            symbol_key in eligible_keys if symbol_key and eligible_keys else None
        ),
        "broker_native_exact_excluded": (
            symbol_key in excluded_keys if symbol_key and excluded_keys else False
        ),
        "runtime_instrument_configured": runtime_instrument_configured,
        "require_configured_kill_zone": require_configured_kill_zone,
        "stage13_repaired_overlay_selector": cfg.get(
            "moonshot_dynamic_execution_router_repaired_overlay_selector"
        ),
        "stage13_repair_summary_path": cfg.get(
            "moonshot_dynamic_execution_router_stage13_repair_summary_path"
        ),
        "source_mode": _context_value(
            field="source_mode",
            cfg=cfg,
            candidate_context=context,
            event=event,
            default_config_key="moonshot_dynamic_execution_router_default_source_mode",
            default="OHLC_M15_CSV",
        ),
        "source_path_feature_status": _context_value(
            field="source_path_feature_status",
            cfg=cfg,
            candidate_context=context,
            event=event,
            default_config_key=(
                "moonshot_dynamic_execution_router_default_source_path_feature_status"
            ),
            default="computed_from_source_ohlc_asof",
        ),
        "live_generation_status": _context_value(
            field="live_generation_status",
            cfg=cfg,
            candidate_context=context,
            event=event,
        ),
        "source_window_complete": source_window_complete,
        "ordered_path_status": ordered_path_status,
        "selected_policy_ordered_path_status": selected_policy_ordered_path_status,
        "selected_policy_same_bar_ambiguous": selected_policy_same_bar_ambiguous,
        "spread_r_at_candidate": _context_value(
            field="spread_r_at_candidate",
            cfg=cfg,
            candidate_context=context,
            event=event,
        ),
        "candidate_quality_selector_enabled": cfg.get(
            "moonshot_candidate_quality_selector_enabled"
        ),
        "candidate_quality_selector_apply_to_execution": cfg.get(
            "moonshot_candidate_quality_selector_apply_to_execution"
        ),
        "candidate_quality_selector_max_spread_r": cfg.get(
            "moonshot_candidate_quality_selector_max_spread_r"
        ),
        "candidate_quality_selector_tradeable_rules": (
            _moonshot_candidate_quality_selector_rules(cfg)
        ),
        "candidate_quality_selector_evidence_path": cfg.get(
            "moonshot_candidate_quality_selector_evidence_path"
        ),
        "candidate_quality_selector_package_path": cfg.get(
            "moonshot_candidate_quality_selector_package_path"
        ),
        "candidate_quality_selector_package_id": cfg.get(
            "moonshot_candidate_quality_selector_package_id"
        ),
        "liquidity_sweep_proxy_state": _context_value(
            field="liquidity_sweep_proxy_state",
            cfg=cfg,
            candidate_context=context,
            event=event,
            default="no_prior_20_sweep",
        ),
        "volatility_state_14_vs_50": _context_value(
            field="volatility_state_14_vs_50",
            cfg=cfg,
            candidate_context=context,
            event=event,
            default="unknown_volatility_state",
        ),
        "trend_state_20": _context_value(
            field="trend_state_20",
            cfg=cfg,
            candidate_context=context,
            event=event,
            default="unknown_trend_state",
        ),
        "current_bar_displacement_atr14": _context_value(
            field="current_bar_displacement_atr14",
            cfg=cfg,
            candidate_context=context,
            event=event,
        ),
        "policy_router_mode": policy_router_mode,
        "condition_challenger_enabled": condition_challenger_enabled,
        "primary_policy": cfg.get("moonshot_dynamic_execution_router_policy"),
        "partial_exception_origin_families": cfg.get(
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner"
        ),
        "partial_exception_policy": cfg.get(
            "moonshot_dynamic_execution_router_momentum_exception_policy"
        ),
        "prop_governor_action": _context_value(
            field="prop_governor_action",
            cfg=cfg,
            candidate_context=context,
            event=event,
        ),
        "remaining_daily_cushion_r": context.get("remaining_daily_cushion_r"),
        "remaining_overall_cushion_r": context.get("remaining_overall_cushion_r"),
        "phase_profit_remaining_r": context.get("phase_profit_remaining_r"),
        "account_recovery_expectancy_r": context.get("account_recovery_expectancy_r"),
        "raw_geometry": _first_present(context.get("raw_geometry"), event.get("raw_geometry")),
        "trade_parameters": _first_present(
            context.get("trade_parameters"),
            event.get("trade_parameters"),
        ),
        "m15_source_fields": _first_present(
            context.get("m15_source_fields"),
            event.get("m15_source_fields"),
        ),
        "mso_context": _first_present(context.get("mso_context"), event.get("mso_context")),
        "tick_snapshot": _first_present(
            context.get("tick_snapshot"),
            event.get("tick_snapshot"),
        ),
        "broker_snapshot": _first_present(
            context.get("broker_snapshot"),
            event.get("broker_snapshot"),
        ),
    }
    router_event = {key: value for key, value in router_event.items() if value not in (None, "")}
    router_event.update(_moonshot_broader_origin_allowlist_match(cfg, router_event))
    router_event.update(_moonshot_branch_allowlist_match(cfg, router_event))
    router_event.update(_moonshot_selected_cell_risk_match(cfg, router_event))
    return {key: value for key, value in router_event.items() if value not in (None, "")}


def evaluate_vnext_moonshot_dynamic_execution(
    *,
    decision: GTOSVNextRuntimeDecision,
    config: dict[str, Any] | None,
    candidate_context: dict[str, Any] | None = None,
) -> GTOSVNextMoonshotDynamicExecutionDecision:
    """Evaluate the production moonshot dynamic execution router."""
    from src.research.moonshot_default_off_policy_router import (
        route_moonshot_dynamic_execution,
    )

    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    enabled = bool(cfg.get("moonshot_dynamic_execution_router_enabled", False))
    apply_flag = bool(cfg.get("moonshot_dynamic_execution_router_apply_to_execution", False))
    apply_to_execution = bool(decision.apply_to_execution and apply_flag)
    source_event = build_vnext_moonshot_dynamic_execution_event(
        decision=decision,
        config=config,
        candidate_context=candidate_context,
    )
    router_decision: MoonshotPolicyRouterDecision = route_moonshot_dynamic_execution(
        source_event,
        enabled=enabled,
        apply_to_execution=apply_to_execution,
    )
    router_record = router_decision.to_record()
    event_trade_params = source_event.get("trade_parameters")
    if not isinstance(event_trade_params, dict):
        event_trade_params = {}
    target_stop_geometry_v4 = build_target_stop_geometry_v4_contract(
        config=config,
        selected_policy=router_decision.selected_policy,
        execution_policy_id=router_decision.execution_policy_id,
        source_event=source_event,
        router_record=router_record,
        trade_params=event_trade_params,
        stage="router_decision",
    )
    return GTOSVNextMoonshotDynamicExecutionDecision(
        enabled=router_decision.enabled,
        apply_to_execution=router_decision.apply_to_execution,
        applied=bool(router_decision.runtime_effect_now),
        decision_status=router_decision.decision_status,
        candidate_action=router_decision.candidate_action,
        selected_branch=router_decision.selected_branch,
        selected_policy=router_decision.selected_policy,
        execution_policy_id=router_decision.execution_policy_id,
        replaced_policy=router_decision.replaced_policy,
        fixed_target_role=router_decision.fixed_target_role,
        prop_action=router_decision.prop_action,
        ai_role=router_decision.ai_role,
        source_quality_action=router_decision.source_quality_action,
        exit_management_action=router_decision.exit_management_action,
        refusal_reasons=tuple(router_decision.refusal_reasons),
        evidence_notes=tuple(router_decision.evidence_notes),
        runtime_effect_now=router_decision.runtime_effect_now,
        candidate_use_allowed_now=router_decision.candidate_use_allowed_now,
        source_event=source_event,
        router_record=router_record,
        target_stop_geometry_v4=target_stop_geometry_v4,
    )


def attach_vnext_moonshot_dynamic_execution_to_record(
    record: dict[str, Any],
    decision: GTOSVNextMoonshotDynamicExecutionDecision,
) -> dict[str, Any]:
    """Attach the moonshot dynamic execution decision to a trade record."""
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["gtos_vnext_moonshot_dynamic_execution"] = decision.to_record()
    inst = record.setdefault("instrumentation", {})
    inst["gtos_vnext_dynamic_policy_selected"] = decision.selected_policy
    inst["gtos_vnext_execution_policy_id"] = decision.execution_policy_id
    inst["gtos_vnext_dynamic_policy_applied"] = decision.applied
    inst["gtos_vnext_dynamic_policy_replaced_policy"] = decision.replaced_policy
    inst["gtos_vnext_dynamic_policy_candidate_action"] = decision.candidate_action
    inst["gtos_vnext_dynamic_policy_decision_status"] = decision.decision_status
    inst["gtos_vnext_dynamic_policy_source_quality_action"] = decision.source_quality_action
    inst["gtos_vnext_dynamic_policy_prop_action"] = decision.prop_action
    inst["gtos_vnext_dynamic_policy_exit_management_action"] = (
        decision.exit_management_action
    )
    inst["gtos_vnext_dynamic_policy_refusal_reasons"] = list(decision.refusal_reasons)
    inst["gtos_vnext_target_stop_geometry_v4"] = dict(decision.target_stop_geometry_v4)
    inst["gtos_vnext_target_stop_geometry_v4_status"] = (
        decision.target_stop_geometry_v4 or {}
    ).get("status")
    return record


_MOONSHOT_REPLACED_POLICY_UNSET = object()


def _retired_static_baseline_comparator() -> str:
    from src.research.moonshot_default_off_policy_router import (
        RETIRED_STATIC_BASELINE_COMPARATOR,
    )

    return RETIRED_STATIC_BASELINE_COMPARATOR


def vnext_moonshot_dynamic_replaces_policy(
    decision: GTOSVNextMoonshotDynamicExecutionDecision,
    replaced_policy: object = _MOONSHOT_REPLACED_POLICY_UNSET,
) -> bool:
    """Return whether the activated moonshot router replaces a named policy."""
    if replaced_policy is _MOONSHOT_REPLACED_POLICY_UNSET:
        replaced_policy = _retired_static_baseline_comparator()
    return bool(
        decision.applied
        and _match_key(decision.replaced_policy) == _match_key(replaced_policy)
        and decision.selected_policy
    )


def _vnext_moonshot_dynamic_contains_old_fallback(
    decision: GTOSVNextMoonshotDynamicExecutionDecision | None,
    replaced_policy: object = _MOONSHOT_REPLACED_POLICY_UNSET,
) -> bool:
    """Return whether the dynamic router prevents old-policy fallthrough.

    A non-applied router decision is still a containment decision in the live
    path: the orchestrator records a vNext dynamic skip and returns before
    market or limit order placement. Only a missing dynamic decision leaves the
    replacement monitor without proof that old fixed-target handling was
    bypassed.
    """
    if decision is None:
        return False
    if replaced_policy is _MOONSHOT_REPLACED_POLICY_UNSET:
        replaced_policy = _retired_static_baseline_comparator()
    if _match_key(decision.replaced_policy) != _match_key(replaced_policy):
        return False
    return bool(
        decision.applied
        or decision.selected_policy
        or decision.execution_policy_id
        or decision.refusal_reasons
        or decision.decision_status
    )


def vnext_blocks_execution(
    decision: GTOSVNextRuntimeDecision,
    config: dict[str, Any] | None,
) -> bool:
    """Return whether this vNext decision should block the candidate now."""
    return vnext_execution_block_reason(decision, config) is not None


def vnext_execution_block_reason(
    decision: GTOSVNextRuntimeDecision,
    config: dict[str, Any] | None,
) -> str | None:
    """Return the active vNext block reason, if any.

    This includes explicit AVOID/MIXED/LEGACY blocking and zero-risk evidence
    that would otherwise be enforced later in the sizing stage.
    """
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    if not decision.enabled or not decision.apply_to_execution:
        return None
    risk_block_reason: str | None = None
    if (
        bool(cfg.get("risk_adjustment_enabled", False))
        and bool(cfg.get("risk_zero_blocks_execution", True))
    ):
        would_multiplier, risk_reason, _summary = _vnext_risk_multiplier(decision, cfg)
        block_threshold = _configured_float(cfg, "execution_block_min_risk_multiplier", 0.000001)
        if would_multiplier <= block_threshold:
            risk_block_reason = risk_reason
            if _risk_reason_bypasses_effective_n_floor(risk_reason, cfg):
                return risk_reason

    min_effective_n = _configured_float(cfg, "block_min_effective_n", 3.0)
    effective_n = _metric_value(decision.evidence or {}, "effective_n")
    if min_effective_n > 0 and (effective_n is None or effective_n < min_effective_n):
        return None
    if decision.decision == "AVOID":
        return "vnext_decision_avoid" if bool(cfg.get("avoid_blocks_execution", True)) else None
    if decision.decision == "MIXED":
        return "vnext_decision_mixed" if bool(cfg.get("mixed_blocks_execution", False)) else None
    if decision.decision == "LEGACY":
        return "vnext_decision_legacy" if bool(cfg.get("legacy_blocks_execution", False)) else None
    if risk_block_reason:
        return risk_block_reason
    return None


def _replacement_monitoring_log_path(config: dict[str, Any] | None) -> Path:
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    return Path(
        str(
            cfg.get("replacement_monitoring_log_path")
            or DEFAULT_REPLACEMENT_MONITORING_LOG_PATH
        )
    )


def _decision_record(decision: Any) -> dict[str, Any]:
    if decision is None:
        return {}
    to_record = getattr(decision, "to_record", None)
    if callable(to_record):
        return to_record()
    if isinstance(decision, dict):
        return dict(decision)
    return {}


def _evidence_metric_sum(decision: Any, metric_name: str) -> float | None:
    evidence = getattr(decision, "evidence", {}) or {}
    metrics = evidence.get("metrics", {}) if isinstance(evidence, dict) else {}
    payload = metrics.get(metric_name) if isinstance(metrics, dict) else None
    return _to_float(payload.get("sum")) if isinstance(payload, dict) else None


def _replacement_ml_role_status(cfg: dict[str, Any], role_key: str) -> dict[str, Any]:
    enabled_key = f"replacement_ml_{role_key}_enabled"
    role_name = role_key.replace("_", "-")
    return {
        "role_key": role_key,
        "enabled": bool(cfg.get(enabled_key, True)),
        "apply_to_execution": bool(cfg.get("replacement_ml_apply_to_execution", False)),
        "runtime_effect": "monitor_only",
        "role_source_manifest": cfg.get("replacement_ml_role_source_manifest"),
        "sealed_validation_required": True,
        "no_leak_tests_required": True,
        "reason": (
            "stage10_monitor_assistant_only_until_sealed_validation_and_owner_approval"
        ),
        "display_name": role_name,
    }


def build_vnext_replacement_monitoring_snapshot(
    *,
    config: dict[str, Any] | None,
    phase: str,
    symbol: str,
    kill_zone: str,
    candle_time_utc: str | None = None,
    vnext_decision: GTOSVNextRuntimeDecision | None = None,
    vnext_pre_ai: GTOSVNextPreAIRoutingDecision | None = None,
    vnext_ai_policy: GTOSVNextAIPolicyDecision | None = None,
    vnext_risk_adjustment: GTOSVNextRiskAdjustment | None = None,
    vnext_pending_policy: GTOSVNextPendingPolicy | None = None,
    vnext_ltf_path_execution: GTOSVNextLTFPathExecutionDecision | None = None,
    vnext_prop_safe_selector: GTOSVNextPropSafeSelectorDecision | None = None,
    vnext_moonshot_dynamic_execution: (
        GTOSVNextMoonshotDynamicExecutionDecision | None
    ) = None,
    ai_supervisor_decision: Any | None = None,
    malformed_ai_summary: dict[str, Any] | None = None,
    source_capture_state: dict[str, Any] | None = None,
) -> GTOSVNextReplacementMonitoringSnapshot:
    """Build the Stage10 replacement-monitoring snapshot without side effects."""
    root_cfg = config or {}
    cfg = root_cfg.get("gtos_vnext_runtime", {}) or {}
    source_capture_state = dict(source_capture_state or {})
    evidence = getattr(vnext_decision, "evidence", {}) or {}
    evidence = evidence if isinstance(evidence, dict) else {}
    source_event = (
        getattr(vnext_moonshot_dynamic_execution, "source_event", None) or {}
    )
    source_event = source_event if isinstance(source_event, dict) else {}
    source_packet = evidence.get("source_packet") if isinstance(evidence, dict) else {}
    source_packet = source_packet if isinstance(source_packet, dict) else {}
    path_state = getattr(vnext_ltf_path_execution, "path_state", None) or {}
    path_state = path_state if isinstance(path_state, dict) else {}

    block_reason = (
        vnext_execution_block_reason(vnext_decision, config)
        if vnext_decision is not None
        else None
    )
    source_window_complete = _first_present(
        source_capture_state.get("source_window_complete"),
        source_event.get("source_window_complete"),
        source_packet.get("source_window_complete"),
        path_state.get("source_complete"),
    )
    same_bar_ambiguous = _first_present(
        source_capture_state.get("same_bar_ambiguous"),
        source_event.get("selected_policy_ordered_path_status")
        == "same_bar_ambiguous_requires_ltf_or_tick_ordering",
        path_state.get("same_bar_ambiguous"),
    )
    source_mode = _first_present(
        source_capture_state.get("source_mode"),
        source_event.get("source_mode"),
        source_packet.get("source_mode"),
        evidence.get("source_mode"),
    )
    source_path_feature_status = _first_present(
        source_capture_state.get("source_path_feature_status"),
        source_event.get("source_path_feature_status"),
        source_packet.get("source_path_feature_status"),
        evidence.get("source_path_feature_status"),
    )

    dynamic_replaces_old_live = (
        vnext_moonshot_dynamic_replaces_policy(vnext_moonshot_dynamic_execution)
        if vnext_moonshot_dynamic_execution is not None
        else False
    )
    dynamic_contains_old_fallback = _vnext_moonshot_dynamic_contains_old_fallback(
        vnext_moonshot_dynamic_execution
    )
    dynamic_apply_requested = bool(
        cfg.get("moonshot_dynamic_execution_router_enabled", False)
        and cfg.get("moonshot_dynamic_execution_router_apply_to_execution", False)
    )
    old_live_leakage_detected = bool(
        dynamic_apply_requested
        and getattr(vnext_decision, "decision", None) == "FOLLOW"
        and not dynamic_contains_old_fallback
    )

    ai_supervisor_record = _decision_record(ai_supervisor_decision)
    supervisor_checks = ai_supervisor_record.get("checks", {})
    malformed_summary = dict(malformed_ai_summary or {})
    if not malformed_summary and isinstance(supervisor_checks, dict):
        malformed_summary = dict(supervisor_checks.get("malformed_responses", {}) or {})

    ml_role_keys = _configured_list(
        cfg,
        "replacement_ml_role_keys",
        (
            "ai_call_reducer",
            "source_confidence_scorer",
            "partition_robustness_scorer",
            "timeout_ambiguous_monitor",
            "drift_detector",
        ),
    )
    ml_roles = {
        role_key: _replacement_ml_role_status(cfg, role_key)
        for role_key in ml_role_keys
    }

    warnings: list[str] = []
    if old_live_leakage_detected:
        warnings.append("old_live_fallback_leakage_when_dynamic_overlay_requested")
    if source_window_complete is False:
        warnings.append("source_window_incomplete_forward_capture_required")
    if same_bar_ambiguous is True:
        warnings.append("same_bar_ambiguous_ordered_ltf_or_tick_required")
    if bool(cfg.get("replacement_ml_apply_to_execution", False)):
        warnings.append("ml_apply_to_execution_must_remain_false_until_sealed_validation")
    malformed_count = malformed_summary.get("row_count")
    try:
        if malformed_count is not None and int(malformed_count) > 0:
            warnings.append("malformed_ai_response_rows_present")
    except (TypeError, ValueError):
        warnings.append("malformed_ai_response_rows_unparseable")

    vnext_apply_status = {
        "replacement_monitoring_enabled": bool(
            cfg.get("replacement_monitoring_enabled", True)
        ),
        "runtime_enabled": bool(cfg.get("enabled", False)),
        "runtime_mode": cfg.get("mode"),
        "global_apply_to_execution": bool(cfg.get("apply_to_execution", False)),
        "pre_ai_apply_to_ai_call": bool(cfg.get("pre_ai_apply_to_ai_call", False)),
        "ai_policy_apply_to_ai_call": bool(cfg.get("ai_policy_apply_to_ai_call", False)),
        "ltf_path_execution_apply_to_execution": bool(
            cfg.get("ltf_path_execution_apply_to_execution", False)
        ),
        "prop_safe_selector_apply_to_execution": bool(
            cfg.get("prop_safe_selector_apply_to_execution", False)
        ),
        "moonshot_dynamic_execution_router_apply_to_execution": bool(
            cfg.get("moonshot_dynamic_execution_router_apply_to_execution", False)
        ),
        "ml_apply_to_execution": bool(cfg.get("replacement_ml_apply_to_execution", False)),
    }
    router_decision = {
        "post_l2_decision": getattr(vnext_decision, "decision", None),
        "post_l2_reason": getattr(vnext_decision, "reason", None),
        "post_l2_matched": getattr(vnext_decision, "matched", None),
        "matched_rows": evidence.get("matched_rows"),
        "pre_ai_action": getattr(vnext_pre_ai, "action", None),
        "pre_ai_would_action": getattr(vnext_pre_ai, "would_action", None),
        "pre_ai_decision": getattr(vnext_pre_ai, "decision", None),
        "ai_policy_action": getattr(vnext_ai_policy, "action", None),
        "ai_policy_would_action": getattr(vnext_ai_policy, "would_action", None),
        "ai_policy_allowed": getattr(vnext_ai_policy, "allowed", None),
        "dynamic_candidate_action": getattr(
            vnext_moonshot_dynamic_execution, "candidate_action", None
        ),
        "dynamic_decision_status": getattr(
            vnext_moonshot_dynamic_execution, "decision_status", None
        ),
        "dynamic_selected_policy": getattr(
            vnext_moonshot_dynamic_execution, "selected_policy", None
        ),
        "dynamic_execution_policy_id": getattr(
            vnext_moonshot_dynamic_execution, "execution_policy_id", None
        ),
        "dynamic_source_quality_action": getattr(
            vnext_moonshot_dynamic_execution, "source_quality_action", None
        ),
    }
    label_effects = {
        "label": getattr(vnext_decision, "decision", None),
        "block_reason": block_reason,
        "avoid_blocks_execution": bool(cfg.get("avoid_blocks_execution", True)),
        "mixed_blocks_execution": bool(cfg.get("mixed_blocks_execution", False)),
        "legacy_blocks_execution": bool(cfg.get("legacy_blocks_execution", False)),
        "decision_group_counts": evidence.get("decision_group_counts", {}),
        "decision_group_row_counts": evidence.get("decision_group_row_counts", {}),
        "source_component_decision_counts": evidence.get(
            "source_component_decision_counts",
            {},
        ),
    }
    execution_effects = {
        "risk_multiplier": getattr(vnext_risk_adjustment, "multiplier", None),
        "risk_would_multiplier": getattr(vnext_risk_adjustment, "would_multiplier", None),
        "risk_applied": getattr(vnext_risk_adjustment, "applied", None),
        "pending_policy_action": getattr(vnext_pending_policy, "action", None),
        "pending_policy_would_action": getattr(vnext_pending_policy, "would_action", None),
        "pending_policy_applied": getattr(vnext_pending_policy, "applied", None),
        "ltf_path_action": getattr(vnext_ltf_path_execution, "action", None),
        "ltf_path_would_action": getattr(vnext_ltf_path_execution, "would_action", None),
        "ltf_path_applied": getattr(vnext_ltf_path_execution, "applied", None),
        "prop_action": getattr(vnext_prop_safe_selector, "action", None),
        "prop_would_action": getattr(vnext_prop_safe_selector, "would_action", None),
        "prop_applied": getattr(vnext_prop_safe_selector, "applied", None),
        "dynamic_policy_applied": getattr(
            vnext_moonshot_dynamic_execution, "applied", None
        ),
        "cost_adjusted_simulated_r_sum": _evidence_metric_sum(
            vnext_decision,
            "cost_adjusted_simulated_r",
        ),
        "proxy_score_sum": _evidence_metric_sum(vnext_decision, "proxy_score"),
        "stress_simulated_r_sum": _evidence_metric_sum(
            vnext_decision,
            "stress_simulated_r",
        ),
        "effective_n_sum": _evidence_metric_sum(vnext_decision, "effective_n"),
    }
    dynamic_exit_transition = {
        "selected_policy": getattr(vnext_moonshot_dynamic_execution, "selected_policy", None),
        "execution_policy_id": getattr(
            vnext_moonshot_dynamic_execution,
            "execution_policy_id",
            None,
        ),
        "replaced_policy": getattr(vnext_moonshot_dynamic_execution, "replaced_policy", None),
        "fixed_target_role": getattr(
            vnext_moonshot_dynamic_execution,
            "fixed_target_role",
            None,
        ),
        "exit_management_action": getattr(
            vnext_moonshot_dynamic_execution,
            "exit_management_action",
            None,
        ),
        "applied": getattr(vnext_moonshot_dynamic_execution, "applied", None),
        "replaces_retired_static_baseline": dynamic_replaces_old_live,
    }
    ltf_pending_monitor_health = {
        "ltf_path_execution_enabled": bool(cfg.get("ltf_path_execution_enabled", True)),
        "ltf_path_monitor_pending_intent_enabled": bool(
            cfg.get("ltf_path_monitor_pending_intent_enabled", True)
        ),
        "monitor_timeframe": getattr(vnext_ltf_path_execution, "monitor_timeframe", None)
        or cfg.get("ltf_path_monitor_timeframe"),
        "action": getattr(vnext_ltf_path_execution, "action", None),
        "would_action": getattr(vnext_ltf_path_execution, "would_action", None),
        "reason": getattr(vnext_ltf_path_execution, "reason", None),
        "source_complete": path_state.get("source_complete"),
        "same_bar_ambiguous": path_state.get("same_bar_ambiguous"),
    }
    prop_budget_projection = {
        "action": getattr(vnext_prop_safe_selector, "action", None),
        "would_action": getattr(vnext_prop_safe_selector, "would_action", None),
        "applied": getattr(vnext_prop_safe_selector, "applied", None),
        "before_risk_pct": getattr(vnext_prop_safe_selector, "before_risk_pct", None),
        "after_risk_pct": getattr(vnext_prop_safe_selector, "after_risk_pct", None),
        "max_allowed_new_trade_risk_pct": getattr(
            vnext_prop_safe_selector,
            "max_allowed_new_trade_risk_pct",
            None,
        ),
        "reason": getattr(vnext_prop_safe_selector, "reason", None),
        "reset_window": dict(getattr(vnext_prop_safe_selector, "reset_window", {}) or {}),
        "external_rule_projection": dict(
            getattr(vnext_prop_safe_selector, "external_rule_projection", {}) or {}
        ),
        "internal_overlay_projection": dict(
            getattr(vnext_prop_safe_selector, "internal_overlay_projection", {}) or {}
        ),
    }
    source_capture_completeness = {
        "source_mode": source_mode,
        "source_window_complete": source_window_complete,
        "source_complete": _first_present(
            source_capture_state.get("source_complete"),
            path_state.get("source_complete"),
            source_packet.get("source_window_complete"),
            evidence.get("source_complete"),
        ),
        "same_bar_ambiguous": same_bar_ambiguous,
        "ordered_path_status": source_event.get("ordered_path_status"),
        "selected_policy_ordered_path_status": source_event.get(
            "selected_policy_ordered_path_status"
        ),
        "selected_policy_same_bar_ambiguous": source_event.get(
            "selected_policy_same_bar_ambiguous"
        ),
        "source_path_feature_status": source_path_feature_status,
        "source_quality_action": _first_present(
            getattr(vnext_moonshot_dynamic_execution, "source_quality_action", None),
            source_capture_state.get("source_quality_action"),
            source_packet.get("source_quality_action"),
        ),
        "refusal_reasons": list(
            getattr(vnext_moonshot_dynamic_execution, "refusal_reasons", ()) or ()
        ),
        "candidate_use_allowed_now": getattr(
            vnext_moonshot_dynamic_execution,
            "candidate_use_allowed_now",
            None,
        ),
    }
    for extra_key in (
        "candidate_count",
        "candidate_id",
        "candidate_summaries",
        "broker_symbol",
        "no_candidate_reason",
        "safety_gate_outcome",
        "safety_gate_reason",
        "null_zero_reasons",
        "m1",
        "m15",
        "tick",
        "source_path_feature_status",
        "ordered_path_status",
        "selected_policy_ordered_path_status",
        "selected_policy_same_bar_ambiguous",
        "raw_geometry",
        "trade_parameters",
        "m15_source_fields",
        "mso_context",
        "tick_snapshot",
        "broker_snapshot",
    ):
        if extra_key in source_capture_state:
            source_capture_completeness[extra_key] = source_capture_state[extra_key]
    selected_cell_risk = {
        key: source_event.get(key)
        for key in (
            "selected_cell_risk_required",
            "selected_cell_risk_allowed",
            "selected_cell_risk_pct",
            "selected_cell_risk_cell_id",
            "selected_cell_risk_decision_basis",
            "selected_cell_risk_match_reason",
            "selected_cell_risk_refusal_cause",
            "selected_cell_risk_failed_dimensions",
            "selected_cell_risk_nearest_candidate",
            "selected_cell_risk_unresolved_reasons",
            "selected_cell_risk_execution_critical_unresolved_reasons",
            "selected_cell_risk_source_ledger_path",
            "selected_cell_risk_source_row_identity",
            "selected_cell_risk_capture_contract",
            "selected_cell_risk_selected_policy",
            "selected_cell_risk_source_policy",
            "selected_cell_risk_execution_policy_id",
            "selected_cell_risk_policy_identity_status",
            "selected_cell_risk_ledger_rows",
            "selected_cell_risk_ledger_load_status",
        )
        if source_event.get(key) is not None
    }
    if selected_cell_risk:
        source_capture_completeness["selected_cell_risk"] = selected_cell_risk
    for event_key in (
        "candidate_id",
        "broker_symbol",
        "broader_origin_source_row_identity",
        "candidate_quality_selector",
        "raw_geometry",
        "trade_parameters",
        "m15_source_fields",
        "mso_context",
        "tick_snapshot",
        "broker_snapshot",
        "spread_r_at_candidate",
    ):
        if event_key in source_event and event_key not in source_capture_completeness:
            source_capture_completeness[event_key] = source_event[event_key]
    old_live_fallback_leakage = {
        "leakage_detected": old_live_leakage_detected,
        "dynamic_apply_requested": dynamic_apply_requested,
        "dynamic_replaces_retired_static_baseline": dynamic_replaces_old_live,
        "dynamic_contains_old_live_fallback": dynamic_contains_old_fallback,
        "dynamic_decision_present": vnext_moonshot_dynamic_execution is not None,
        "dynamic_policy_applied": getattr(
            vnext_moonshot_dynamic_execution,
            "applied",
            None,
        ),
        "selected_policy": getattr(vnext_moonshot_dynamic_execution, "selected_policy", None),
        "execution_policy_id": getattr(
            vnext_moonshot_dynamic_execution,
            "execution_policy_id",
            None,
        ),
        "replaced_policy": getattr(vnext_moonshot_dynamic_execution, "replaced_policy", None),
        "block_reason": block_reason,
    }
    ai_malformed_monitoring = {
        "ai_policy_action": getattr(vnext_ai_policy, "action", None),
        "ai_policy_would_action": getattr(vnext_ai_policy, "would_action", None),
        "ai_policy_allowed": getattr(vnext_ai_policy, "allowed", None),
        "ai_policy_reason": getattr(vnext_ai_policy, "reason", None),
        "ai_supervisor_action": ai_supervisor_record.get("action"),
        "ai_supervisor_severity": ai_supervisor_record.get("severity"),
        "malformed_response_summary": malformed_summary,
        "repair_function": (
            "src.components.ai_supervisor.repair_ai_response_format_preserving_semantics"
        ),
    }
    ml_assistant_roles = {
        "apply_to_execution": bool(cfg.get("replacement_ml_apply_to_execution", False)),
        "model_role_source_manifest": cfg.get("replacement_ml_role_source_manifest"),
        "roles": ml_roles,
        "drift_detector_warn_threshold": _configured_float(
            cfg,
            "replacement_ml_drift_psi_warn_threshold",
            0.25,
        ),
    }
    return GTOSVNextReplacementMonitoringSnapshot(
        phase=phase,
        symbol=symbol,
        kill_zone=kill_zone,
        candle_time_utc=candle_time_utc,
        vnext_apply_status=vnext_apply_status,
        router_decision=router_decision,
        label_effects=label_effects,
        execution_effects=execution_effects,
        dynamic_exit_transition=dynamic_exit_transition,
        ltf_pending_monitor_health=ltf_pending_monitor_health,
        prop_budget_projection=prop_budget_projection,
        source_capture_completeness=source_capture_completeness,
        old_live_fallback_leakage=old_live_fallback_leakage,
        ai_malformed_monitoring=ai_malformed_monitoring,
        ml_assistant_roles=ml_assistant_roles,
        warnings=tuple(sorted(set(warnings))),
    )


def attach_vnext_replacement_monitoring_to_record(
    record: dict[str, Any],
    snapshot: GTOSVNextReplacementMonitoringSnapshot,
) -> dict[str, Any]:
    """Attach the replacement monitoring snapshot to a trade record."""
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["gtos_vnext_replacement_monitoring"] = snapshot.to_record()
    inst = record.setdefault("instrumentation", {})
    inst["gtos_vnext_replacement_monitoring_schema"] = snapshot.schema_version
    inst["gtos_vnext_replacement_old_live_leakage"] = bool(
        snapshot.old_live_fallback_leakage.get("leakage_detected")
    )
    inst["gtos_vnext_replacement_source_window_complete"] = (
        snapshot.source_capture_completeness.get("source_window_complete")
    )
    inst["gtos_vnext_replacement_dynamic_policy"] = (
        snapshot.dynamic_exit_transition.get("selected_policy")
    )
    inst["gtos_vnext_replacement_execution_policy_id"] = (
        snapshot.dynamic_exit_transition.get("execution_policy_id")
    )
    inst["gtos_vnext_replacement_ml_apply_to_execution"] = (
        snapshot.ml_assistant_roles.get("apply_to_execution")
    )
    inst["gtos_vnext_replacement_warning_count"] = len(snapshot.warnings)
    return record


def record_vnext_replacement_monitoring_snapshot(
    *,
    snapshot: GTOSVNextReplacementMonitoringSnapshot,
    config: dict[str, Any] | None,
    log_path: Path | str | None = None,
) -> None:
    """Append one Stage10 replacement-monitoring JSONL row."""
    cfg = (config or {}).get("gtos_vnext_runtime", {}) or {}
    if not bool(cfg.get("replacement_monitoring_enabled", True)):
        return
    if not bool(cfg.get("replacement_monitoring_log_enabled", True)):
        return
    target = Path(log_path) if log_path is not None else _replacement_monitoring_log_path(config)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "schema_version": "gtos_vnext_replacement_monitoring_log_v1",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "snapshot": snapshot.to_record(),
        }
        _append_jsonl_locked(target, row)
    except Exception as exc:  # noqa: BLE001 - monitoring must not break trading.
        logger.warning("GTOS vNext replacement monitoring log failed: %s", exc)


__all__ = [
    "DEFAULT_REPLACEMENT_MONITORING_LOG_PATH",
    "DEFAULT_CP281_BRANCH_DECISIONS_ARTIFACT_PATH",
    "DEFAULT_CP281_READY_RUNTIME_AGGREGATE_ARTIFACT_PATH",
    "DEFAULT_CP281_READY_RUNTIME_RULE_ARTIFACT_PATH",
    "DEFAULT_CP281_RULE_REPLAY_EVENT_ARTIFACT_PATH",
    "DEFAULT_CP281_RULE_REPLAY_RESULT_TABLE_ARTIFACT_PATH",
    "DEFAULT_BRIDGE_DIAGNOSTIC_ARTIFACT_PATH",
    "DEFAULT_EVIDENCE_MATRIX_ARTIFACT_PATH",
    "DEFAULT_IMPLEMENTATION_ARTIFACT_PATH",
    "GTOSVNextAIPolicyDecision",
    "GTOSVNextBridgeDiagnostics",
    "GTOSVNextGateOverride",
    "GTOSVNextLTFPathExecutionDecision",
    "GTOSVNextPendingPolicy",
    "GTOSVNextPropSafeSelectorDecision",
    "GTOSVNextReplacementMonitoringSnapshot",
    "GTOSVNextExitPolicyDecision",
    "GTOSVNextMoonshotDynamicExecutionDecision",
    "GTOSVNextReady8ControlPolicyDecision",
    "GTOSVNextRuntimeDecision",
    "GTOSVNextEvidenceIndex",
    "GTOSVNextPreAIRoutingDecision",
    "GTOSVNextRiskAdjustment",
    "attach_vnext_confidence_override_to_record",
    "attach_vnext_ai_policy_to_record",
    "attach_vnext_decision_to_record",
    "attach_vnext_ltf_path_execution_to_record",
    "attach_vnext_moonshot_dynamic_execution_to_record",
    "attach_vnext_pending_policy_to_record",
    "attach_vnext_pre_ai_to_record",
    "attach_vnext_prop_safe_selector_to_record",
    "attach_vnext_replacement_monitoring_to_record",
    "attach_vnext_risk_adjustment_to_record",
    "apply_vnext_risk_adjustment",
    "build_vnext_pre_ai_event",
    "build_vnext_moonshot_dynamic_execution_event",
    "build_vnext_replacement_monitoring_snapshot",
    "build_vnext_event_from_candidate",
    "evaluate_candidate_vnext",
    "evaluate_vnext_ai_policy",
    "evaluate_vnext_exit_management_policy",
    "evaluate_vnext_ltf_path_execution",
    "evaluate_vnext_moonshot_dynamic_execution",
    "evaluate_vnext_ready8_failure_control_policy",
    "evaluate_vnext_pending_policy",
    "evaluate_vnext_prop_safe_selector",
    "evaluate_vnext_selector_v4_admission",
    "evaluate_vnext_confidence_override",
    "evaluate_pre_ai_vnext",
    "evaluate_vnext_route_event",
    "evaluate_vnext_event",
    "format_vnext_ai_policy_context_for_prompt",
    "format_vnext_ai_role_context_for_prompt",
    "is_vnext_ai_enforceable_route_family",
    "load_artifact_rows",
    "load_vnext_bridge_diagnostics",
    "load_vnext_evidence_index",
    "normalize_event",
    "normalize_vnext_symbol_key",
    "record_vnext_replacement_monitoring_snapshot",
    "record_vnext_runtime_decision",
    "resolve_vnext_effective_framework",
    "resolve_vnext_symbol_family",
    "symbol_family_candidates_for_vnext",
    "vnext_blocks_execution",
    "vnext_moonshot_dynamic_replaces_policy",
    "vnext_ai_policy_allows_no_paid_mechanical_follow",
    "vnext_ai_policy_no_paid_call_replay_decision",
    "vnext_ai_policy_requires_paid_call",
    "vnext_execution_block_reason",
]
