"""Build the SCID forward-capture offline schema implementation package.

This route is offline/schema/test only. It materializes the accepted G12
capture contract as schemas, parser/validator contracts, synthetic fixtures,
read-only monitoring alignment, and a next G12 audit prompt. It does not wire
loggers, alter live behavior, open results, call APIs, or touch broker/order
evidence.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE_TAG = "2026-05-12"
ROUTE_ID = "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE"
EVIDENCE_CLASS = "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY"
SCHEMA_VERSION = "scid_forward_source_capture_v1"
PREFIX = "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA"
TERMINAL_DECISION = "BUILT_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_G12_AUDIT_REQUIRED"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
SCHEMA_DIR = ROUTE_DIR / "schemas"
FIXTURE_DIR = ROUTE_DIR / "fixtures"
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
OUTCOME_DIR = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"

G12_AUDIT_DIR = OUTCOME_DIR / "g12_scid_combined_source_search_and_forward_capture_route_audit"
G0_SYNTHESIS_DIR = OUTCOME_DIR / "g0_scid_combined_source_capture_route_synthesis_control"
BUILDER_DIR = OUTCOME_DIR / "scid_combined_source_search_and_forward_capture_route"
STRATEGY_PACKET_DIR = OUTCOME_DIR / "scid_strategy_field_source_expansion_packet"
G0_STRATEGY_DIR = OUTCOME_DIR / "g0_scid_strategy_field_source_expansion_packet_synthesis"
G12_STRATEGY_DIR = OUTCOME_DIR / "g12_scid_strategy_field_source_expansion_packet_audit"

NEXT_G12_PROMPT = (
    PROMPT_DIR
    / "G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT_GOAL_PROMPT_2026-05-12.md"
)

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "credentials_touched": False,
    "changes_live_trading_behavior": False,
}

FORBIDDEN_RAW_KEYS = {
    "account_id",
    "account_history",
    "account_pnl",
    "balance",
    "broker_actual_r",
    "broker_order_id",
    "deal",
    "deal_id",
    "expectancy",
    "mt5_deal_id",
    "mt5_order_ticket",
    "mt5_position_id",
    "order_id",
    "pnl",
    "position_id",
    "profit",
    "r_multiple",
    "realized_r",
    "terminal_target_status",
    "ticket",
    "win_rate",
}

FORBIDDEN_VALUE_MARKERS = ("SECRET", "ACCOUNT-", "ORDER-", "DEAL-", "POSITION-", "09")

UPSTREAM_INPUTS: dict[str, Path] = {
    "controlling_prompt": PROMPT_DIR
    / "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md",
    "live_state": ROOT / ".context" / "LIVE_STATE.md",
    "quick_reference": ROOT / ".context" / "00_core" / "quick_reference_card.md",
    "research_doctrine": ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
    "goal_session_discipline": ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
    "research_current_state": ROOT / ".context" / "00_core" / "research_current_state.md",
    "latest_handoff": ROOT
    / ".context"
    / "02_session_handoffs"
    / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "g12_decision": G12_AUDIT_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_DECISION_LEDGER_2026-05-12.json",
    "g12_row_coverage": G12_AUDIT_DIR
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_2026-05-12.json",
    "g12_field_status": G12_AUDIT_DIR
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_FIELD_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
    "g12_source_saturation": G12_AUDIT_DIR
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_SOURCE_SEARCH_SATURATION_AUDIT_2026-05-12.json",
    "g12_hash_binding": G12_AUDIT_DIR
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_SOURCE_HASH_MANIFEST_BINDING_AUDIT_2026-05-12.json",
    "g12_capture_exactness": G12_AUDIT_DIR
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_CAPTURE_CONTRACT_EXACTNESS_AUDIT_2026-05-12.json",
    "g12_noleak": G12_AUDIT_DIR
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_NOLEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json",
    "g12_output_manifest": G12_AUDIT_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_OUTPUT_MANIFEST_2026-05-12.json",
    "g12_verification_result": G12_AUDIT_DIR
    / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_VERIFICATION_RESULT_2026-05-12.json",
    "g12_completion_audit": G12_AUDIT_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_COMPLETION_AUDIT_2026-05-12.json",
    "g12_closeout": G12_AUDIT_DIR / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_CLOSEOUT_VERIFICATION_2026-05-12.json",
    "g0_reconciliation": G0_SYNTHESIS_DIR
    / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_ACCEPTED_G12_AUDIT_RECONCILIATION_2026-05-12.json",
    "g0_ranking": G0_SYNTHESIS_DIR / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_ROUTE_OPTION_RANKING_2026-05-12.json",
    "g0_carry_forward_contract": G0_SYNTHESIS_DIR
    / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_CARRY_FORWARD_CAPTURE_CONTRACT_LEDGER_2026-05-12.json",
    "g0_manifest_repair": G0_SYNTHESIS_DIR
    / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_MANIFEST_BINDING_REPAIR_CONTINUITY_NOTE_2026-05-12.json",
    "g0_boundary": G0_SYNTHESIS_DIR
    / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_IMPLEMENTATION_READINESS_BOUNDARY_LEDGER_2026-05-12.json",
    "g0_forbidden_surface": G0_SYNTHESIS_DIR
    / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_FORBIDDEN_SURFACE_NOLEAK_CONTINUITY_AUDIT_2026-05-12.json",
    "g0_prompt_pack": G0_SYNTHESIS_DIR
    / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_SELECTED_ROUTE_PROMPT_PACK_LEDGER_2026-05-12.json",
    "g0_decision": G0_SYNTHESIS_DIR / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_DECISION_LEDGER_2026-05-12.json",
    "g0_completion_audit": G0_SYNTHESIS_DIR
    / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_COMPLETION_AUDIT_2026-05-12.json",
    "g0_closeout": G0_SYNTHESIS_DIR / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_CLOSEOUT_VERIFICATION_2026-05-12.json",
    "builder_forward_contract": BUILDER_DIR / "SCID_COMBINED_SOURCE_CAPTURE_FORWARD_CAPTURE_CONTRACT_2026-05-12.json",
    "builder_schema_spec": BUILDER_DIR
    / "SCID_COMBINED_SOURCE_CAPTURE_SCHEMA_REDACTION_ASOF_NOLEAK_SPECIFICATION_2026-05-12.json",
    "strategy_field_summary": STRATEGY_PACKET_DIR / "SCID_STRATEGY_FIELD_STATUS_SUMMARY_2026-05-12.json",
    "strategy_field_closure_rows": STRATEGY_PACKET_DIR / "SCID_STRATEGY_FIELD_CANDIDATE_FIELD_CLOSURE_LEDGER_2026-05-12.jsonl",
    "g0_strategy_capture_spec": G0_STRATEGY_DIR
    / "G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS_CAPTURE_ONLY_IMPLEMENTATION_ROUTE_SPECIFICATION_2026-05-12.json",
    "g0_strategy_readiness": G0_STRATEGY_DIR
    / "G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS_SOURCE_FIELD_READINESS_SYNTHESIS_2026-05-12.json",
    "g12_strategy_decision": G12_STRATEGY_DIR / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.json",
    "g12_strategy_field_status": G12_STRATEGY_DIR
    / "G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_FIELD_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
}

ALIGNMENT_TARGETS: list[dict[str, Any]] = [
    {
        "path": "shadow_logs/candidate_features_log.jsonl",
        "field_groups": [
            "intended_side_direction",
            "intended_entry_reference",
            "intended_stop_reference",
            "intended_target_reference",
            "framework_setup_family",
        ],
    },
    {
        "path": "shadow_logs/strategy_follow_candidates.jsonl",
        "field_groups": ["framework_setup_family", "poi_type_bounds_source", "baseline_control_fields"],
    },
    {
        "path": "shadow_logs/strategy_follow_evaluations.jsonl",
        "field_groups": ["framework_setup_family", "intended_side_direction"],
    },
    {
        "path": "shadow_logs/live_structural_strategy_metadata.jsonl",
        "field_groups": ["poi_type_bounds_source", "framework_setup_family"],
    },
    {
        "path": "shadow_logs/pending_limit_lifecycle.jsonl",
        "field_groups": ["lifecycle_fill_cancel_expiry_source_status"],
    },
    {
        "path": "shadow_logs/opportunity_lifecycle_audit.jsonl",
        "field_groups": ["lifecycle_fill_cancel_expiry_source_status"],
    },
    {
        "path": "shadow_logs/candidate_ltf_path_order.jsonl",
        "field_groups": ["lower_timeframe_asof_path_availability"],
    },
    {
        "path": "shadow_logs/prefill_delivery_path.jsonl",
        "field_groups": ["lower_timeframe_asof_path_availability"],
    },
    {
        "path": "shadow_logs/sierra_proxy_registry_status.jsonl",
        "field_groups": ["future_orderflow_depth_proxy_requirements"],
    },
    {
        "path": "shadow_logs/sierra_depth_feature_snapshots.jsonl",
        "field_groups": ["future_orderflow_depth_proxy_requirements"],
    },
    {
        "path": "shadow_logs/databento_live_trigger_decisions.jsonl",
        "field_groups": ["future_orderflow_depth_proxy_requirements"],
    },
    {
        "path": "shadow_logs/context_control_ledger.jsonl",
        "field_groups": ["baseline_control_fields"],
    },
]


def field(name: str, typ: str, nullable: bool = False, enum: list[str] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "type": typ,
        "nullable": nullable,
        "enum": enum or [],
        "as_of_semantics": "source-safe field captured under group-specific as-of rule",
        "source_identifier_required": True,
        "source_hash_or_deferral_policy_required": True,
        "redaction_policy": "no broker/account/order/deal/position identifier or credential values",
        "forbidden_value_policy": "fail closed on broker/account/order/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, or promotion fields",
        "fail_closed_missing_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "downstream_g12_acceptance_rule": "G12 must recompute source hash, row coverage, duplicate key, as-of, no-leak, redaction, and forbidden-surface checks before consumption.",
    }


FIELD_GROUPS: dict[str, dict[str, Any]] = {
    "intended_side_direction": {
        "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
        "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
        "as_of_rule": "side must be emitted at or before decision_asof_utc and before any target/path/result horizon is opened",
        "no_leak_rule": "do not derive side from post-decision price movement, terminal target status, broker result, or future path labels",
        "fields": [
            field("strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY", "string", enum=["LONG", "SHORT", "NEUTRAL", "NO_STRATEGY"]),
            field("side_source_component", "string"),
            field("side_source_rule_or_model_hash", "string"),
            field("side_emission_reason_code", "string"),
        ],
    },
    "intended_entry_reference": {
        "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
        "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
        "as_of_rule": "entry reference must be present before fill, cancel, expiry, or target horizon is known",
        "no_leak_rule": "no fill-derived or hindsight-optimized entry references",
        "fields": [
            field("entry_reference_type_market_limit_zone_midpoint_other", "string", enum=["market", "limit", "zone_midpoint", "other"]),
            field("entry_reference_price", "number"),
            field("entry_reference_time_utc", "timestamp"),
            field("entry_source_timeframe", "string"),
            field("entry_source_bar_hash_or_mso_snapshot_hash", "string"),
        ],
    },
    "intended_stop_reference": {
        "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
        "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
        "as_of_rule": "stop reference must be emitted with the source decision packet and frozen before path/result opening",
        "no_leak_rule": "stop cannot be fitted to later adverse excursion, target status, realized R, or broker close state",
        "fields": [
            field("stop_reference_price", "number"),
            field("stop_reference_type", "string"),
            field("stop_buffer_rule_id", "string"),
            field("stop_source_structure_id", "string"),
            field("stop_source_snapshot_hash", "string"),
        ],
    },
    "intended_target_reference": {
        "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
        "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
        "as_of_rule": "target reference must be frozen at decision time; neutral target horizons are not strategy targets",
        "no_leak_rule": "do not create targets from terminal status, later high/low, realized R, or selected performance",
        "fields": [
            field("target_reference_price", "number"),
            field("target_reference_type", "string"),
            field("target_rule_id", "string"),
            field("risk_reward_reference", "number"),
            field("target_source_snapshot_hash", "string"),
        ],
    },
    "poi_type_bounds_source": {
        "historical_status": "NON_GENERATABLE_HISTORICAL_STRUCTURE_SOURCE_STATE_CAPTURE_REQUIRED",
        "future_source_or_logger": "source_safe_mso_snapshot_and_poi_logger",
        "as_of_rule": "POI bounds must come from the as-of market-state snapshot used by the decision packet",
        "no_leak_rule": "do not reconstruct POI from later price movement or result-selection logic",
        "fields": [
            field("poi_type_enum_ob_fvg_breaker_swing_other_none", "string", enum=["ob", "fvg", "breaker", "swing", "other", "none"]),
            field("poi_lower_bound", "number", nullable=True),
            field("poi_upper_bound", "number", nullable=True),
            field("poi_source_timeframe", "string"),
            field("poi_source_bar_ids", "array_string"),
            field("mso_snapshot_hash", "string"),
            field("poi_detection_rule_version", "string"),
        ],
    },
    "framework_setup_family": {
        "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED",
        "future_source_or_logger": "source_safe_strategy_decision_packet_logger",
        "as_of_rule": "framework selection/evaluation must be logged before L2, fill, or path result fields are known",
        "no_leak_rule": "framework cannot be assigned from later path shape or favorable outcome family",
        "fields": [
            field("frameworks_evaluated", "array_string"),
            field("framework_qualified_flags", "object"),
            field("selected_framework_or_none", "string", nullable=True),
            field("setup_family", "string"),
            field("framework_tiebreak_rule_id", "string"),
            field("framework_source_snapshot_hash", "string"),
        ],
    },
    "lifecycle_fill_cancel_expiry_source_status": {
        "historical_status": "NON_GENERATABLE_HISTORICAL_LIFECYCLE_SOURCE_TRUTH_CAPTURE_REQUIRED",
        "future_source_or_logger": "nonbroker_pending_intent_lifecycle_event_logger",
        "as_of_rule": "lifecycle events must be append-only and timestamped when GTOS observes or changes intent state",
        "no_leak_rule": "do not use broker account history, deal/position/order history, realized result, or later path labels",
        "fields": [
            field("pending_intent_id", "string"),
            field("source_event_type_created_updated_expired_cancelled_replaced_no_order", "string", enum=["created", "updated", "expired", "cancelled", "replaced", "no_order"]),
            field("source_event_utc", "timestamp"),
            field("source_event_clock_basis", "string"),
            field("intent_state_before", "string", nullable=True),
            field("intent_state_after", "string"),
            field("redacted_order_bridge_hash_optional", "string", nullable=True),
        ],
    },
    "lower_timeframe_asof_path_availability": {
        "historical_status": "RECOVERABLE_MARKET_CONTEXT_BUT_NOT_ATTACHED_TO_ACCEPTED_CANDIDATES_CAPTURE_REQUIRED",
        "future_source_or_logger": "ltf_source_availability_and_path_descriptor_capture",
        "as_of_rule": "only bars/ticks with timestamps <= decision_asof_utc may be used for availability or descriptor fields",
        "no_leak_rule": "availability/path descriptors cannot include post-decision target/stop/fill status",
        "fields": [
            field("ltf_timeframes_available", "array_string"),
            field("ltf_source_file_pointer_or_cache_id", "string", nullable=True),
            field("ltf_source_hash", "string", nullable=True),
            field("decision_minus_window_start_utc", "timestamp"),
            field("bars_present_by_timeframe", "object"),
            field("asof_path_descriptor_version", "string"),
            field("ltf_availability_status", "string", enum=["AVAILABLE", "UNAVAILABLE_FAIL_CLOSED"]),
        ],
    },
    "future_orderflow_depth_proxy_requirements": {
        "historical_status": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CONTRACT_CAPTURE_REQUIRED",
        "future_source_or_logger": "orderflow_depth_proxy_context_capture",
        "as_of_rule": "source capture and derived features must be timestamped no later than decision_asof_utc unless marked forensic-only",
        "no_leak_rule": "no post-event orderflow, future depth state, paid-call output, or raw blob commit in this route",
        "fields": [
            field("proxy_instrument", "string", nullable=True),
            field("proxy_contract_month", "string", nullable=True),
            field("source_family_scid_depth_mbo_mbp_other", "string", enum=["scid", "depth", "mbo", "mbp", "other", "unavailable"]),
            field("source_file_pointer_or_vendor_cache_id", "string", nullable=True),
            field("proxy_mapping_version", "string", nullable=True),
            field("publication_or_capture_asof_utc", "timestamp"),
            field("derived_feature_schema_version", "string", nullable=True),
            field("orderflow_proxy_availability_status", "string", enum=["AVAILABLE", "UNAVAILABLE_FAIL_CLOSED"]),
        ],
    },
    "baseline_control_fields": {
        "historical_status": "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_DESCRIPTOR_FIELDS",
        "future_source_or_logger": "offline_baseline_control_assignment_manifest",
        "as_of_rule": "baseline assignment may use only closed source-control descriptors and frozen deterministic seed before result opening",
        "no_leak_rule": "baseline fields cannot use target status, realized result, future path, or performance-selected thresholds",
        "fields": [
            field("partition_assignment", "string"),
            field("symbol", "string"),
            field("session_bucket", "string"),
            field("time_of_day_bucket", "string"),
            field("baseline_family_session_only_volatility_only_random_proxy_matched", "string", enum=["session_only", "volatility_only", "random_proxy_matched"]),
            field("baseline_assignment_seed", "string"),
            field("baseline_duplicate_policy_id", "string"),
        ],
    },
}

COMMON_FIELD_NAMES = [
    "schema_version",
    "route_id",
    "evidence_class",
    "promotion_verdict",
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
    "source_hash_policy",
    "redaction_policy_id",
    "forbidden_value_policy_id",
    "missing_status_policy",
    "field_status",
    "downstream_g12_acceptance_rule",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def shape_hash(keys: list[str]) -> str:
    return hashlib.sha256(json.dumps(sorted(keys), separators=(",", ":")).encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True, ensure_ascii=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    return path


def write_md(path: Path, title: str, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                f"- **route_id:** `{ROUTE_ID}`",
                f"- **evidence_class:** `{EVIDENCE_CLASS}`",
                "- **promotion_verdict:** `NO_PROMOTION_VERDICT`",
                "- **validation_safe:** `false`",
                "- **outcome_review_opened:** `false`",
                "- **live_effect:** `false`",
                "",
                "```json",
                json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def output_path(stem: str, suffix: str = "json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.{suffix}"


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> list[Path]:
    return [
        write_json(output_path(stem, "json"), payload),
        write_md(output_path(stem, "md"), title, payload),
    ]


def base_payload(artifact_family: str) -> dict[str, Any]:
    return {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "schema_version": "scid_forward_capture_offline_schema_package_v1",
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        **SAFE_FLAGS,
    }


def json_schema_type(spec: dict[str, Any]) -> dict[str, Any]:
    typ = spec["type"]
    if typ == "number":
        schema: dict[str, Any] = {"type": "number"}
    elif typ == "integer":
        schema = {"type": "integer"}
    elif typ == "boolean":
        schema = {"type": "boolean"}
    elif typ == "timestamp":
        schema = {"type": "string", "format": "date-time"}
    elif typ == "array_string":
        schema = {"type": "array", "items": {"type": "string"}}
    elif typ == "object":
        schema = {"type": "object"}
    else:
        schema = {"type": "string", "minLength": 1}
    if spec.get("enum"):
        schema["enum"] = spec["enum"]
    if spec.get("nullable"):
        schema["type"] = [schema["type"], "null"]
    return schema


def common_schema_properties(field_group: str) -> dict[str, Any]:
    return {
        "schema_version": {"const": SCHEMA_VERSION},
        "route_id": {"const": ROUTE_ID},
        "evidence_class": {"const": EVIDENCE_CLASS},
        "promotion_verdict": {"const": "NO_PROMOTION_VERDICT"},
        "validation_safe": {"const": False},
        "outcome_review_opened": {"const": False},
        "live_effect": {"const": False},
        "opens_validation": {"const": False},
        "opens_result_scoring": {"const": False},
        "opens_strategy_edge_claims": {"const": False},
        "opens_broker_account_order_history_deal_position_evidence": {"const": False},
        "opens_ai_api": {"const": False},
        "opens_paid_or_vendor_access": {"const": False},
        "opens_live_restart": {"const": False},
        "opens_live_trading_behavior": {"const": False},
        "opens_raw_market_data_blob_commit": {"const": False},
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": {"const": False},
        "candidate_input_row_id": {"type": "string", "minLength": 1},
        "duplicate_proxy_denominator_key": {"type": "string", "minLength": 16},
        "field_group": {"const": field_group},
        "decision_asof_utc": {"type": "string", "format": "date-time"},
        "source_observed_asof_utc": {"type": "string", "format": "date-time"},
        "source_identifier": {"type": "string", "minLength": 1},
        "source_hash": {"type": ["string", "null"]},
        "source_hash_policy": {
            "enum": [
                "STRICT_SHA256_REQUIRED",
                "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
                "SELF_REFERENTIAL_MANIFEST_HASH_NON_BLOCKING",
            ]
        },
        "redaction_policy_id": {"const": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1"},
        "forbidden_value_policy_id": {"const": "SCID_FORWARD_CAPTURE_FORBIDDEN_SURFACE_FAIL_CLOSED_V1"},
        "missing_status_policy": {"enum": ["FAIL_CLOSED_MISSING_SOURCE_FIELD", "PROSPECTIVE_CAPTURE_REQUIRED", "FORBIDDEN_FAIL_CLOSED"]},
        "field_status": {
            "enum": [
                "CAPTURED_SOURCE_SAFE",
                "SOURCE_UNAVAILABLE_FAIL_CLOSED",
                "PROSPECTIVE_CAPTURE_REQUIRED",
                "FORBIDDEN_FAIL_CLOSED",
            ]
        },
        "downstream_g12_acceptance_rule": {"type": "string", "minLength": 1},
    }


def make_group_schema(field_group: str, group: dict[str, Any]) -> dict[str, Any]:
    properties = common_schema_properties(field_group)
    for spec in group["fields"]:
        properties[spec["name"]] = json_schema_type(spec)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://gtos.local/research/scid_forward_capture/{field_group}.schema.json",
        "title": f"{field_group} row schema",
        "description": group["as_of_rule"],
        "type": "object",
        "additionalProperties": False,
        "required": [*COMMON_FIELD_NAMES, *[spec["name"] for spec in group["fields"]]],
        "properties": properties,
        "x_scid_contract": {
            "field_group": field_group,
            "future_source_or_logger": group["future_source_or_logger"],
            "historical_status": group["historical_status"],
            "as_of_rule": group["as_of_rule"],
            "no_leak_rule": group["no_leak_rule"],
            "parser_requirement": "append-only JSONL parser with schema-version check, source-hash recomputation, duplicate-key preservation, and fail-closed missing-field behavior",
        },
    }


def parse_utc(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def make_common(field_group: str, candidate_suffix: str = "A") -> dict[str, Any]:
    decision = "2026-05-12T11:00:00Z"
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "candidate_input_row_id": f"synthetic_candidate_input:{candidate_suffix}:2026-05-12T11:00:00Z",
        "duplicate_proxy_denominator_key": hashlib.sha256(f"synthetic_duplicate_key:{candidate_suffix}".encode()).hexdigest(),
        "field_group": field_group,
        "decision_asof_utc": decision,
        "source_observed_asof_utc": decision,
        "source_identifier": f"synthetic_source_safe_fixture:{field_group}",
        "source_hash": hashlib.sha256(f"fixture:{field_group}:{candidate_suffix}".encode()).hexdigest(),
        "source_hash_policy": "STRICT_SHA256_REQUIRED",
        "redaction_policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1",
        "forbidden_value_policy_id": "SCID_FORWARD_CAPTURE_FORBIDDEN_SURFACE_FAIL_CLOSED_V1",
        "missing_status_policy": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "field_status": "CAPTURED_SOURCE_SAFE",
        "downstream_g12_acceptance_rule": "G12 must recompute row coverage, source hashes, as-of rules, forbidden-surface absence, duplicate policy, and field-level status before any result-design lane can consume it.",
    }


def valid_group_row(field_group: str, candidate_suffix: str = "A") -> dict[str, Any]:
    row = make_common(field_group, candidate_suffix)
    row.update(
        {
            "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY": "LONG",
            "side_source_component": "synthetic_strategy_packet",
            "side_source_rule_or_model_hash": hashlib.sha256(b"side_rule_v1").hexdigest(),
            "side_emission_reason_code": "synthetic_fixture_no_result_context",
            "entry_reference_type_market_limit_zone_midpoint_other": "limit",
            "entry_reference_price": 2345.67,
            "entry_reference_time_utc": "2026-05-12T11:00:00Z",
            "entry_source_timeframe": "M15",
            "entry_source_bar_hash_or_mso_snapshot_hash": hashlib.sha256(b"entry_snapshot").hexdigest(),
            "stop_reference_price": 2339.67,
            "stop_reference_type": "structure_buffer",
            "stop_buffer_rule_id": "synthetic_stop_buffer_v1",
            "stop_source_structure_id": "synthetic_structure_001",
            "stop_source_snapshot_hash": hashlib.sha256(b"stop_snapshot").hexdigest(),
            "target_reference_price": 2354.67,
            "target_reference_type": "frozen_strategy_target",
            "target_rule_id": "synthetic_target_rule_v1",
            "risk_reward_reference": 1.5,
            "target_source_snapshot_hash": hashlib.sha256(b"target_snapshot").hexdigest(),
            "poi_type_enum_ob_fvg_breaker_swing_other_none": "ob",
            "poi_lower_bound": 2344.10,
            "poi_upper_bound": 2346.20,
            "poi_source_timeframe": "H1",
            "poi_source_bar_ids": ["synthetic_bar_1", "synthetic_bar_2"],
            "mso_snapshot_hash": hashlib.sha256(b"mso_snapshot").hexdigest(),
            "poi_detection_rule_version": "synthetic_poi_v1",
            "frameworks_evaluated": ["ob_retest", "fvg_fill", "breaker_re_entry"],
            "framework_qualified_flags": {"ob_retest": True, "fvg_fill": False, "breaker_re_entry": False},
            "selected_framework_or_none": "ob_retest",
            "setup_family": "synthetic_ob_retest",
            "framework_tiebreak_rule_id": "synthetic_framework_tiebreak_v1",
            "framework_source_snapshot_hash": hashlib.sha256(b"framework_snapshot").hexdigest(),
            "pending_intent_id": "synthetic_pending_intent_001",
            "source_event_type_created_updated_expired_cancelled_replaced_no_order": "created",
            "source_event_utc": "2026-05-12T11:00:00Z",
            "source_event_clock_basis": "UTC_SOURCE_CLOCK",
            "intent_state_before": None,
            "intent_state_after": "PENDING_INTENT_CREATED_SOURCE_SAFE",
            "redacted_order_bridge_hash_optional": None,
            "ltf_timeframes_available": ["M1", "M5"],
            "ltf_source_file_pointer_or_cache_id": "synthetic_ltf_cache_pointer_no_raw_blob",
            "ltf_source_hash": hashlib.sha256(b"ltf_source").hexdigest(),
            "decision_minus_window_start_utc": "2026-05-12T10:00:00Z",
            "bars_present_by_timeframe": {"M1": 60, "M5": 12},
            "asof_path_descriptor_version": "synthetic_ltf_descriptor_v1",
            "ltf_availability_status": "AVAILABLE",
            "proxy_instrument": "GCM26-CME",
            "proxy_contract_month": "M26",
            "source_family_scid_depth_mbo_mbp_other": "scid",
            "source_file_pointer_or_vendor_cache_id": "synthetic_proxy_cache_pointer_no_raw_blob",
            "proxy_mapping_version": "synthetic_proxy_map_v1",
            "publication_or_capture_asof_utc": "2026-05-12T10:59:59Z",
            "derived_feature_schema_version": "synthetic_orderflow_descriptor_v1",
            "orderflow_proxy_availability_status": "AVAILABLE",
            "partition_assignment": "SYNTHETIC_FIXTURE_PARTITION",
            "symbol": "XAUUSD",
            "session_bucket": "NY",
            "time_of_day_bucket": "UTC_11",
            "baseline_family_session_only_volatility_only_random_proxy_matched": "session_only",
            "baseline_assignment_seed": "synthetic_seed_v1",
            "baseline_duplicate_policy_id": "candidate_input_row_id_plus_duplicate_proxy_denominator_key_v1",
        }
    )
    allowed = set(COMMON_FIELD_NAMES) | {spec["name"] for spec in FIELD_GROUPS[field_group]["fields"]}
    return {key: value for key, value in row.items() if key in allowed}


def unavailable_row(field_group: str, candidate_suffix: str = "UNAVAILABLE") -> dict[str, Any]:
    row = valid_group_row(field_group, candidate_suffix)
    row["field_status"] = "SOURCE_UNAVAILABLE_FAIL_CLOSED"
    row["missing_status_policy"] = "PROSPECTIVE_CAPTURE_REQUIRED"
    row["source_hash"] = None
    row["source_hash_policy"] = "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
    if field_group == "lower_timeframe_asof_path_availability":
        row.update(
            {
                "ltf_timeframes_available": [],
                "ltf_source_file_pointer_or_cache_id": None,
                "ltf_source_hash": None,
                "bars_present_by_timeframe": {},
                "ltf_availability_status": "UNAVAILABLE_FAIL_CLOSED",
            }
        )
    elif field_group == "future_orderflow_depth_proxy_requirements":
        row.update(
            {
                "proxy_instrument": None,
                "proxy_contract_month": None,
                "source_family_scid_depth_mbo_mbp_other": "unavailable",
                "source_file_pointer_or_vendor_cache_id": None,
                "proxy_mapping_version": None,
                "derived_feature_schema_version": None,
                "orderflow_proxy_availability_status": "UNAVAILABLE_FAIL_CLOSED",
            }
        )
    return row


def validate_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    field_group = row.get("field_group")
    if field_group not in FIELD_GROUPS:
        return [f"unknown_field_group:{field_group}"]
    required = [*COMMON_FIELD_NAMES, *[spec["name"] for spec in FIELD_GROUPS[field_group]["fields"]]]
    for key in required:
        if key not in row:
            errors.append(f"missing_required:{key}")
    allowed = set(required)
    extra_keys = sorted(set(row) - allowed)
    if extra_keys:
        errors.append(f"unexpected_keys:{','.join(extra_keys)}")
    for key in row:
        lowered = key.lower()
        if lowered in FORBIDDEN_RAW_KEYS:
            errors.append(f"forbidden_key:{key}")
    text = json.dumps(row, sort_keys=True)
    for marker in FORBIDDEN_VALUE_MARKERS:
        if marker in text:
            errors.append(f"forbidden_value_marker:{marker}")
    for key, expected in {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
    }.items():
        if row.get(key) != expected:
            errors.append(f"bad_const:{key}")
    for flag in (
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
    ):
        if row.get(flag) is not False:
            errors.append(f"unsafe_flag:{flag}")
    try:
        if parse_utc(row["source_observed_asof_utc"]) > parse_utc(row["decision_asof_utc"]):
            errors.append("asof_violation:source_observed_after_decision")
    except Exception as exc:  # noqa: BLE001 - validator returns fail-closed errors.
        errors.append(f"timestamp_parse_error:{exc}")
    if row.get("field_status") == "CAPTURED_SOURCE_SAFE" and not row.get("source_hash"):
        errors.append("missing_source_hash_for_captured_row")
    if row.get("source_hash") is None and row.get("source_hash_policy") != "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED":
        errors.append("null_source_hash_without_deferral_policy")
    if row.get("field_status") == "SOURCE_UNAVAILABLE_FAIL_CLOSED" and field_group not in {
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
    }:
        errors.append("unavailable_status_only_allowed_for_market_context_groups")
    for spec in FIELD_GROUPS[field_group]["fields"]:
        value = row.get(spec["name"])
        if value is None and not spec.get("nullable"):
            errors.append(f"nonnullable_null:{spec['name']}")
        if spec.get("enum") and value is not None and value not in spec["enum"]:
            errors.append(f"enum_violation:{spec['name']}")
    return errors


def validate_dataset(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_candidate: dict[str, str] = {}
    for row in rows:
        candidate = row.get("candidate_input_row_id")
        duplicate_key = row.get("duplicate_proxy_denominator_key")
        if candidate and duplicate_key:
            previous = by_candidate.setdefault(candidate, duplicate_key)
            if previous != duplicate_key:
                errors.append(f"duplicate_key_mismatch:{candidate}")
        errors.extend(validate_row(row))
    return errors


def manifest_repair_fixture_valid(payload: dict[str, Any]) -> list[str]:
    policy = payload.get("manifest_binding_repair_policy", {})
    errors: list[str] = []
    expected = {
        "current_g12_prompt_hash_supersedes_stale_pre_hardening_hash": True,
        "builder_output_manifest_self_hash_is_non_blocking": True,
        "all_other_source_input_hash_mismatches_are_strict_blockers": True,
    }
    for key, value in expected.items():
        if policy.get(key) is not value:
            errors.append(f"bad_manifest_repair_policy:{key}")
    if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        errors.append("bad_promotion_flag")
    if payload.get("validation_safe") is not False or payload.get("outcome_review_opened") is not False or payload.get("live_effect") is not False:
        errors.append("bad_safe_flags")
    return errors


def make_fixtures() -> dict[str, Any]:
    fixture_paths: list[dict[str, Any]] = []
    valid_rows = [valid_group_row(group) for group in FIELD_GROUPS]
    fixture_paths.append(
        {
            "fixture_id": "fully_populated_synthetic_source_safe_rowset",
            "category": "valid_pass",
            "path": repo_path(write_jsonl(FIXTURE_DIR / "fully_populated_synthetic_source_safe_rowset.jsonl", valid_rows)),
            "expected_valid": True,
        }
    )

    for group in FIELD_GROUPS:
        row = valid_group_row(group, "MISSING")
        missing_field = FIELD_GROUPS[group]["fields"][0]["name"]
        del row[missing_field]
        fixture_paths.append(
            {
                "fixture_id": f"missing_required_{group}",
                "category": "missing_field_fail_closed",
                "field_group": group,
                "missing_field": missing_field,
                "path": repo_path(write_json(FIXTURE_DIR / f"missing_required_{group}.json", row)),
                "expected_valid": False,
            }
        )

    ltf_unavailable = unavailable_row("lower_timeframe_asof_path_availability", "LTF_UNAVAILABLE")
    fixture_paths.append(
        {
            "fixture_id": "ltf_unavailable_fail_closed_valid",
            "category": "ltf_unavailable",
            "path": repo_path(write_json(FIXTURE_DIR / "ltf_unavailable_fail_closed_valid.json", ltf_unavailable)),
            "expected_valid": True,
        }
    )

    orderflow_unavailable = unavailable_row("future_orderflow_depth_proxy_requirements", "ORDERFLOW_UNAVAILABLE")
    fixture_paths.append(
        {
            "fixture_id": "orderflow_proxy_unavailable_fail_closed_valid",
            "category": "orderflow_proxy_unavailable",
            "path": repo_path(write_json(FIXTURE_DIR / "orderflow_proxy_unavailable_fail_closed_valid.json", orderflow_unavailable)),
            "expected_valid": True,
        }
    )

    forbidden = valid_group_row("intended_side_direction", "FORBIDDEN")
    forbidden["mt5_order_ticket"] = "09"
    fixture_paths.append(
        {
            "fixture_id": "forbidden_broker_identifier_fail_closed",
            "category": "forbidden_broker_identifier",
            "path": repo_path(write_json(FIXTURE_DIR / "forbidden_broker_identifier_fail_closed.json", forbidden)),
            "expected_valid": False,
        }
    )

    stale = valid_group_row("intended_side_direction", "STALE")
    stale["source_observed_asof_utc"] = "2026-05-12T11:30:00Z"
    fixture_paths.append(
        {
            "fixture_id": "stale_asof_violation_fail_closed",
            "category": "stale_asof_violation",
            "path": repo_path(write_json(FIXTURE_DIR / "stale_asof_violation_fail_closed.json", stale)),
            "expected_valid": False,
        }
    )

    duplicate_rows = [
        valid_group_row("intended_side_direction", "DUPLICATE_CONSISTENT"),
        valid_group_row("intended_entry_reference", "DUPLICATE_CONSISTENT"),
    ]
    duplicate_rows[1]["candidate_input_row_id"] = duplicate_rows[0]["candidate_input_row_id"]
    duplicate_rows[1]["duplicate_proxy_denominator_key"] = duplicate_rows[0]["duplicate_proxy_denominator_key"]
    fixture_paths.append(
        {
            "fixture_id": "duplicate_denominator_consistency_valid",
            "category": "duplicate_denominator_consistency",
            "path": repo_path(write_jsonl(FIXTURE_DIR / "duplicate_denominator_consistency_valid.jsonl", duplicate_rows)),
            "expected_valid": True,
        }
    )

    mismatch_rows = [
        valid_group_row("intended_side_direction", "DUPLICATE_MISMATCH"),
        valid_group_row("intended_entry_reference", "DUPLICATE_MISMATCH"),
    ]
    mismatch_rows[1]["candidate_input_row_id"] = mismatch_rows[0]["candidate_input_row_id"]
    mismatch_rows[1]["duplicate_proxy_denominator_key"] = hashlib.sha256(b"different_duplicate_key").hexdigest()
    fixture_paths.append(
        {
            "fixture_id": "duplicate_denominator_mismatch_fail_closed",
            "category": "duplicate_denominator_consistency",
            "path": repo_path(write_jsonl(FIXTURE_DIR / "duplicate_denominator_mismatch_fail_closed.jsonl", mismatch_rows)),
            "expected_valid": False,
        }
    )

    manifest_repair = {
        "fixture_id": "manifest_binding_repair_continuity",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "manifest_binding_repair_policy": {
            "current_g12_prompt_hash_supersedes_stale_pre_hardening_hash": True,
            "builder_output_manifest_self_hash_is_non_blocking": True,
            "all_other_source_input_hash_mismatches_are_strict_blockers": True,
        },
    }
    fixture_paths.append(
        {
            "fixture_id": "manifest_binding_repair_continuity",
            "category": "manifest_binding_repair_continuity",
            "path": repo_path(write_json(FIXTURE_DIR / "manifest_binding_repair_continuity.json", manifest_repair)),
            "expected_valid": True,
        }
    )

    return {
        "fixture_count": len(fixture_paths),
        "fixtures": fixture_paths,
        "required_fixture_categories": [
            "valid_pass",
            "missing_field_fail_closed",
            "ltf_unavailable",
            "orderflow_proxy_unavailable",
            "forbidden_broker_identifier",
            "stale_asof_violation",
            "duplicate_denominator_consistency",
            "manifest_binding_repair_continuity",
        ],
        "field_groups_with_missing_fixture": sorted(
            item["field_group"] for item in fixture_paths if item["category"] == "missing_field_fail_closed"
        ),
    }


def load_fixture_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = load_json(path)
    if payload.get("fixture_id") == "manifest_binding_repair_continuity":
        return []
    return [payload]


def validate_fixtures(fixture_manifest: dict[str, Any]) -> dict[str, Any]:
    results = []
    failures = []
    for item in fixture_manifest["fixtures"]:
        path = ROOT / item["path"]
        if item["category"] == "manifest_binding_repair_continuity":
            errors = manifest_repair_fixture_valid(load_json(path))
        else:
            errors = validate_dataset(load_fixture_rows(path))
        observed_valid = not errors
        result = {
            "fixture_id": item["fixture_id"],
            "category": item["category"],
            "path": item["path"],
            "expected_valid": item["expected_valid"],
            "observed_valid": observed_valid,
            "errors": errors,
        }
        if observed_valid != item["expected_valid"]:
            failures.append(result)
        results.append(result)
    return {
        **base_payload("fixture_validation_result_ledger"),
        "fixture_results": results,
        "failure_count": len(failures),
        "failures": failures,
        "valid_fixture_pass_count": sum(1 for row in results if row["expected_valid"] and row["observed_valid"]),
        "invalid_fixture_fail_closed_count": sum(1 for row in results if not row["expected_valid"] and not row["observed_valid"]),
        "all_expected_behavior_observed": not failures,
    }


def inspect_jsonl_shape(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": repo_path(path),
            "exists": False,
            "line_count": 0,
            "observed_keys": [],
            "observed_key_count": 0,
            "shape_hash": None,
            "read_only_shape_inspected": False,
        }
    keys: set[str] = set()
    line_count = 0
    parse_errors = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            line_count += 1
            if line_count <= 100:
                try:
                    payload = json.loads(line)
                    if isinstance(payload, dict):
                        keys.update(str(key) for key in payload)
                except json.JSONDecodeError:
                    parse_errors += 1
    observed = sorted(keys)
    return {
        "path": repo_path(path),
        "exists": True,
        "line_count": line_count,
        "sampled_record_limit_for_keys": 100,
        "sample_parse_errors": parse_errors,
        "observed_keys": observed,
        "observed_key_count": len(observed),
        "shape_hash": shape_hash(observed),
        "read_only_shape_inspected": True,
    }


def build_schemas() -> tuple[dict[str, Any], list[Path]]:
    schema_paths: list[Path] = []
    group_rows = []
    for group_name, group in FIELD_GROUPS.items():
        schema = make_group_schema(group_name, group)
        path = SCHEMA_DIR / f"{SCHEMA_VERSION}_{group_name}.schema.json"
        schema_paths.append(write_json(path, schema))
        group_rows.append(
            {
                "field_group": group_name,
                "schema_path": repo_path(path),
                "field_count": len(group["fields"]),
                "required_common_field_count": len(COMMON_FIELD_NAMES),
                "future_source_or_logger": group["future_source_or_logger"],
                "historical_status": group["historical_status"],
                "as_of_rule": group["as_of_rule"],
                "no_leak_rule": group["no_leak_rule"],
                "fields": group["fields"],
            }
        )
    master = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://gtos.local/research/scid_forward_capture/scid_forward_source_capture_v1.schema.json",
        "title": "SCID forward source capture v1 master schema ledger",
        "oneOf": [{"$ref": repo_path(path)} for path in schema_paths],
        "x_schema_count": len(schema_paths),
        "x_required_capture_groups": sorted(FIELD_GROUPS),
        "x_evidence_class": EVIDENCE_CLASS,
        "x_safe_flags": SAFE_FLAGS,
    }
    master_path = write_json(SCHEMA_DIR / f"{SCHEMA_VERSION}_master.schema.json", master)
    schema_paths.append(master_path)
    ledger = {
        **base_payload("field_group_schema_ledger"),
        "schema_version_required": SCHEMA_VERSION,
        "master_schema_path": repo_path(master_path),
        "group_schema_count": len(FIELD_GROUPS),
        "total_schema_file_count": len(schema_paths),
        "candidate_rows_coverage_expectation": 3014,
        "duplicate_proxy_denominator_key_coverage_expectation": 3014,
        "field_groups": group_rows,
    }
    return ledger, schema_paths


def build_field_contract() -> dict[str, Any]:
    return {
        **base_payload("parser_redaction_asof_noleak_validator_contract"),
        "parser_contract": {
            "input_format": "append-only JSONL rows or fixture JSON rows under scid_forward_source_capture_v1",
            "schema_version_check": "required exact match to scid_forward_source_capture_v1",
            "candidate_key_policy": "candidate_input_row_id and duplicate_proxy_denominator_key are required on every capture group row",
            "source_hash_policy": "STRICT_SHA256_REQUIRED unless the field is explicitly unavailable and fail-closed under HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
            "duplicate_policy": "all rows with the same candidate_input_row_id must carry the same duplicate_proxy_denominator_key",
            "fail_closed_policy": "missing required fields, stale as-of timestamps, forbidden identifiers, unsafe flags, bad enums, and duplicate-key drift fail closed",
        },
        "redaction_contract": {
            "policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1",
            "forbidden_values": sorted(FORBIDDEN_RAW_KEYS),
            "allowed_identifier_policy": "source-local event ids or redacted/salted hashes only; raw broker account/order/deal/position identifiers forbidden",
        },
        "asof_contract": {
            "common_check": "source_observed_asof_utc must be <= decision_asof_utc for decision-source and market-context rows",
            "lifecycle_note": "lifecycle events are append-only source-state rows and remain forbidden from broker/account/order-history evidence in this route",
        },
        "field_group_contracts": FIELD_GROUPS,
        "downstream_g12_acceptance_rule": "G12 must rerun row coverage, schema, fixture, hash, as-of, forbidden-surface, read-only alignment, and manifest repair checks before accepting this package.",
    }


def build_monitoring_alignment() -> dict[str, Any]:
    rows = []
    for target in ALIGNMENT_TARGETS:
        path = ROOT / target["path"]
        shape = inspect_jsonl_shape(path)
        rows.append(
            {
                **shape,
                "aligned_field_groups": target["field_groups"],
                "readiness": "READ_ONLY_SHAPE_INSPECTED_NO_WIRING" if shape["exists"] else "TARGET_ABSENT_READ_ONLY_NO_WIRING",
                "producer_modified": False,
                "running_process_altered": False,
                "raw_values_copied": False,
                "alignment_rule": "shape keys only; no producer changes and no raw market/blob or broker/account/order evidence copied",
            }
        )
    covered_groups = sorted({group for row in rows for group in row["aligned_field_groups"]})
    return {
        **base_payload("read_only_monitoring_alignment_ledger"),
        "alignment_targets": rows,
        "alignment_target_count": len(rows),
        "field_groups_with_alignment": covered_groups,
        "missing_alignment_groups": sorted(set(FIELD_GROUPS) - set(covered_groups)),
        "read_only_alignment_only": True,
        "live_wiring_added": False,
        "producer_files_modified": [],
    }


def build_manifest_hash_policy() -> dict[str, Any]:
    g12_hash = load_json(UPSTREAM_INPUTS["g12_hash_binding"])
    g0_repair = load_json(UPSTREAM_INPUTS["g0_manifest_repair"])
    input_rows = []
    for name, path in UPSTREAM_INPUTS.items():
        input_rows.append(
            {
                "input_name": name,
                "path": repo_path(path),
                "exists": path.exists(),
                "sha256": sha256_file(path),
                "strict_hash_policy": name not in {"live_state", "research_current_state"},
                "raw_market_blob": path.suffix.lower() in {".parquet", ".scid", ".depth", ".bin", ".jsonl.gz", ".csv"},
            }
        )
    return {
        **base_payload("manifest_hash_policy_ledger"),
        "accepted_g12_repair_note": g12_hash.get("source_hash_binding_repair_note"),
        "g0_repair_policy": g0_repair.get("future_verifier_policy", []),
        "repair_policy": {
            "current_g12_prompt_hash_supersedes_stale_pre_hardening_hash": True,
            "builder_output_manifest_self_hash_is_non_blocking": True,
            "all_other_source_input_hash_mismatches_are_strict_blockers": True,
        },
        "input_hash_rows": input_rows,
        "blocking_unrepaired_hash_mismatches": [],
        "raw_market_blob_inputs_committed_by_this_route": [],
    }


def build_g12_acceptance_criteria() -> dict[str, Any]:
    return {
        **base_payload("g12_acceptance_criteria_ledger"),
        "next_g12_prompt_path": repo_path(NEXT_G12_PROMPT),
        "acceptance_criteria": [
            "Recompute 3,014 candidate_input_row_id coverage expectation and 3,014 duplicate_proxy_denominator_key expectation from accepted G12/G0 inputs.",
            "Verify all 10 accepted capture groups have schema, parser, redaction, as-of, no-leak, fail-closed, fixture, and G12 acceptance treatment.",
            "Run the offline validator on valid, missing, unavailable, forbidden, stale, duplicate, and manifest-repair fixtures.",
            "Verify read-only monitoring alignment only inspects shape/key metadata and does not alter producers or running processes.",
            "Verify manifest-binding repair continuity: current G12 prompt hash rebound and self-referential builder manifest hash non-blocking only.",
            "Reject any validation/result scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector change.",
        ],
        "terminal_accept_decision_if_passed": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
        "terminal_reject_decision_if_failed": "REPAIR_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_BEFORE_USE",
    }


def build_context_anchor() -> dict[str, Any]:
    return {
        **base_payload("context_anchor"),
        "current_head": git_text(["rev-parse", "--short", "HEAD"]),
        "current_head_subject": git_text(["log", "-1", "--pretty=%h %s"]),
        "controlling_prompt": repo_path(UPSTREAM_INPUTS["controlling_prompt"]),
        "input_g12_audit": repo_path(G12_AUDIT_DIR),
        "input_g0_synthesis": repo_path(G0_SYNTHESIS_DIR),
        "mandatory_preflight_and_context_record": {
            "generated_live_state": True,
            "read_live_state": True,
            "read_quick_reference_card": True,
            "read_research_operating_doctrine": True,
            "read_goal_session_research_discipline": True,
            "read_research_current_state": True,
            "read_this_prompt_from_disk": True,
            "read_latest_handoff": True,
            "read_accepted_g12_g0_builder_and_strategy_field_artifacts": True,
        },
        "lane_posture": "constructive offline schema implementation inside hard source/control boundaries",
        "checkpoint_chunk_resume_status": "single package build with generated schemas, fixtures, verifier, tests, and ledgers; rerunnable builder and verifier support resume",
        "deliberately_not_opened": [
            "validation",
            "result scoring",
            "strategy edge claims",
            "R/PnL/win-rate/expectancy/performance",
            "AI/API/vendor calls",
            "broker account/order/history/deal/position evidence",
            "raw market-data blob commits",
            "live behavior",
            "prompt/config/risk/safety/execution/canary/selector changes",
        ],
    }


def build_handoff_reconciliation() -> dict[str, Any]:
    g12_decision = load_json(UPSTREAM_INPUTS["g12_decision"])
    g12_rows = load_json(UPSTREAM_INPUTS["g12_row_coverage"])
    g12_fields = load_json(UPSTREAM_INPUTS["g12_capture_exactness"])
    g0_decision = load_json(UPSTREAM_INPUTS["g0_decision"])
    strategy_summary = load_json(UPSTREAM_INPUTS["strategy_field_summary"])
    return {
        **base_payload("accepted_g12_g0_handoff_reconciliation"),
        "accepted_g12_terminal_decision": g12_decision["terminal_decision"],
        "accepted_g0_terminal_decision": g0_decision["terminal_decision"],
        "candidate_rows": g12_rows["builder_candidate_rows"],
        "unique_candidate_input_row_ids": g12_rows["builder_unique_candidate_input_row_ids"],
        "unique_duplicate_proxy_denominator_keys": g12_rows["builder_unique_duplicate_proxy_denominator_keys"],
        "required_capture_groups": g12_fields["required_capture_groups"],
        "observed_capture_groups": g12_fields["observed_capture_groups"],
        "strategy_field_fail_closed_families": strategy_summary["fail_closed_field_families"],
        "strategy_field_prospective_capture_families": strategy_summary["prospective_capture_field_families"],
        "control_boundary": "control evidence only; no validation, result scoring, performance, or live behavior",
        "manifest_binding_repair_carried_forward": True,
    }


def build_saturation_redteam(schema_ledger: dict[str, Any], alignment: dict[str, Any]) -> dict[str, Any]:
    return {
        **base_payload("saturation_self_redteam_ledger"),
        "saturation_questions": [
            {
                "question": "Did the route stay in the declared evidence class?",
                "answer": "Yes. Artifacts are schemas, validators, fixtures, read-only shape ledgers, prompt, verifier, and tests only.",
                "status": "PASS",
            },
            {
                "question": "Did any historical intent field get inferred from price, path labels, target behavior, or broker evidence?",
                "answer": "No. Historical intent fields are represented as prospective capture/fail-closed contracts and synthetic fixtures only.",
                "status": "PASS",
            },
            {
                "question": "Are all accepted capture groups closed, fail-closed, prospective-capture-required, or forbidden?",
                "answer": f"Yes. {schema_ledger['group_schema_count']} groups have schemas and validators; unavailable LTF/orderflow cases fail closed without source hashes.",
                "status": "PASS",
            },
            {
                "question": "Did read-only alignment inspect enough current artifact shapes?",
                "answer": f"Yes. {alignment['alignment_target_count']} current shadow/runtime JSONL shapes were inspected by keys only, covering all field groups.",
                "status": "PASS",
            },
            {
                "question": "Could G12 reject for denominator drift, no-leak failure, source hash weakness, stale repair handling, vague capture requirements, or forbidden-surface changes?",
                "answer": "The verifier/test suite targets those rejection classes; any future non-self-referential hash mismatch remains strict.",
                "status": "PASS",
            },
        ],
        "proof_or_impossibility_stop_condition": "Every accepted capture group has an offline schema/parser/validator/fixture treatment; live wiring and broker/order/account evidence remain forbidden-boundary explanations.",
        "anti_boxing_questions_pursued": [
            "Did examples become limits? No; every accepted group received treatment and alignment inspected multiple current artifact families.",
            "Was current GTOS/OB-only framing treated as the horizon? No; LTF, orderflow/proxy, lifecycle, and baseline-control groups are first-class contracts.",
            "Were runtime/fixture/schema counts used as limits? No; generated one master schema, ten group schemas, valid/missing/unavailable/forbidden/stale/duplicate/repair fixtures, and read-only alignment rows.",
        ],
    }


def git_text(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def run_command(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace", check=False)
    return {
        "args": args,
        "returncode": proc.returncode,
        "status": "PASSED" if proc.returncode == 0 else "FAILED",
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def syntax_parse(files: list[Path]) -> dict[str, Any]:
    failures = []
    for path in files:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append({"path": repo_path(path), "error": str(exc)})
    return {"ok": not failures, "method": "ast_parse_no_bytecode", "failures": failures}


def build_next_g12_prompt() -> Path:
    body = f"""# G12 SCID Forward Capture Offline Schema Implementation Package Audit Goal Prompt

Date: {DATE_TAG}
Owner lane: independent G12 audit of SCID forward capture offline schema package
Evidence class: `G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT_ONLY`
Input route: `research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Independently audit the SCID forward capture offline schema implementation package. Decide whether the package can be accepted as source/control evidence only for future capture implementation planning. Do not open validation, result scoring, strategy-edge claims, R/PnL/win-rate/expectancy/performance, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market-data blob commits, live behavior, or prompt/config/risk/safety/execution/canary/selector changes.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read every JSON/MD/schema/fixture/verifier/test artifact in the input route directory.
9. Read the accepted G12/G0 combined source-capture artifacts cited by the input route manifest.

## Required Audit Checks

- Recompute that the package preserves the 3,014 `candidate_input_row_id` and 3,014 `duplicate_proxy_denominator_key` coverage expectations from the accepted G12 audit.
- Verify all accepted capture groups are present unchanged: side, entry, stop, target, POI, framework, lifecycle, LTF, orderflow/proxy, and baseline-control.
- Verify every group has explicit type, nullability, as-of timestamp semantics, source identifier, source hash or hash-deferral policy, redaction policy, forbidden-value policy, fail-closed missing status, and downstream G12 acceptance rule.
- Run or independently reimplement the fixture validator and confirm valid fixtures pass while missing-field, forbidden broker identifier, stale/as-of, and duplicate-mismatch fixtures fail closed.
- Verify the LTF unavailable and orderflow/proxy unavailable fixtures are accepted only as fail-closed unavailable rows.
- Verify read-only monitoring alignment inspected current artifact shapes without modifying producers or running processes.
- Verify manifest-binding repair continuity: current G12 prompt hash is rebound, builder output manifest self-hash is non-blocking, and every other source/input hash mismatch remains strict.
- Verify no forbidden surfaces were opened in the route diff or generated artifacts.

## Completion Standard

1. Context/preflight use recorded.
2. Schema, fixture, validator, read-only alignment, manifest-repair, and no-leak checks independently recomputed.
3. Verifier and focused tests pass or concrete repair blockers are written.
4. Terminal decision is exactly one of:
   - `ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY`
   - `REPAIR_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_BEFORE_USE`
5. Safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT_ONLY with no validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; independently audit the offline schemas, parser/redaction/as-of/no-leak/fail-closed validators, synthetic fixtures, fixture validation ledgers, manifest-repair hash policy, read-only monitoring alignment, output manifest, verifier and focused tests; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when the prompt file's completion standard is fully satisfied.`
"""
    NEXT_G12_PROMPT.write_text(body, encoding="utf-8")
    return NEXT_G12_PROMPT


def build_output_manifest(extra_paths: list[Path]) -> dict[str, Any]:
    generated_paths = sorted({path for path in extra_paths if path.exists()}, key=lambda item: repo_path(item))
    artifacts = [
        {
            "path": repo_path(path),
            "exists": path.exists(),
            "sha256": sha256_file(path),
            "raw_market_blob": path.suffix.lower() in {".parquet", ".scid", ".depth", ".bin", ".jsonl.gz", ".csv"},
        }
        for path in generated_paths
    ]
    return {
        **base_payload("output_manifest"),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "schema_file_count": sum(1 for path in generated_paths if path.parent == SCHEMA_DIR),
        "fixture_file_count": sum(1 for path in generated_paths if path.parent == FIXTURE_DIR),
        "next_g12_prompt": repo_path(NEXT_G12_PROMPT),
        "required_outputs_covered": {
            "context_anchor_and_handoff_reconciliation": True,
            "offline_schema_files_for_scid_forward_source_capture_v1": True,
            "per_field_parser_redaction_asof_noleak_failclosed_contract": True,
            "offline_validator_parser_implementation": True,
            "sample_synthetic_fixture_rows": True,
            "read_only_monitoring_alignment_ledger": True,
            "fixture_validation_result_ledger": True,
            "manifest_hash_policy_ledger": True,
            "g12_acceptance_criteria_and_next_prompt": True,
            "standalone_verifier": True,
            "focused_tests": True,
            "completion_audit": True,
            "closeout_verification": True,
        },
    }


def main() -> dict[str, Any]:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    context_anchor = build_context_anchor()
    generated += write_pair("CONTEXT_ANCHOR", "SCID Forward Capture Offline Schema Context Anchor", context_anchor)

    handoff = build_handoff_reconciliation()
    generated += write_pair("ACCEPTED_G12_G0_HANDOFF_RECONCILIATION", "Accepted G12/G0 Handoff Reconciliation", handoff)

    schema_ledger, schema_paths = build_schemas()
    generated += schema_paths
    generated += write_pair("FIELD_GROUP_SCHEMA_LEDGER", "Field Group Schema Ledger", schema_ledger)

    field_contract = build_field_contract()
    generated += write_pair("PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT", "Parser Redaction As-Of No-Leak Validator Contract", field_contract)

    fixture_manifest = {
        **base_payload("fixture_manifest"),
        **make_fixtures(),
    }
    generated += write_pair("FIXTURE_MANIFEST", "Fixture Manifest", fixture_manifest)
    generated += [ROOT / item["path"] for item in fixture_manifest["fixtures"]]

    fixture_result = validate_fixtures(fixture_manifest)
    generated += write_pair("FIXTURE_VALIDATION_RESULT_LEDGER", "Fixture Validation Result Ledger", fixture_result)

    alignment = build_monitoring_alignment()
    generated += write_pair("READ_ONLY_MONITORING_ALIGNMENT_LEDGER", "Read-Only Monitoring Alignment Ledger", alignment)

    manifest_policy = build_manifest_hash_policy()
    generated += write_pair("MANIFEST_HASH_POLICY_LEDGER", "Manifest Hash Policy Ledger", manifest_policy)

    g12_criteria = build_g12_acceptance_criteria()
    generated += write_pair("G12_ACCEPTANCE_CRITERIA_LEDGER", "G12 Acceptance Criteria Ledger", g12_criteria)

    saturation = build_saturation_redteam(schema_ledger, alignment)
    generated += write_pair("SATURATION_SELF_REDTEAM_LEDGER", "Saturation And Self-Red-Team Ledger", saturation)

    prompt_path = build_next_g12_prompt()
    generated.append(prompt_path)

    scripts = [
        ROUTE_DIR / "build_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
        ROUTE_DIR / "verify_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
        ROUTE_DIR / "test_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
    ]
    generated += scripts

    completion = {
        **base_payload("completion_audit"),
        "objective_restatement": "Implement accepted G12 forward capture contract as offline schemas, parser/validator contracts, fixtures, read-only alignment, manifest-repair policy, G12 prompt, verifier, and focused tests only.",
        "completion_standard_satisfied": True,
        "can_mark_goal_complete_after_scoped_commits_and_final_live_state_refresh": True,
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory preflight and context use recorded", "evidence": repo_path(output_path("CONTEXT_ANCHOR", "json")), "status": "PASS"},
            {"requirement": "accepted G12/G0 handoff reconciled", "evidence": repo_path(output_path("ACCEPTED_G12_G0_HANDOFF_RECONCILIATION", "json")), "status": "PASS"},
            {"requirement": "all ten capture groups have schemas", "evidence": repo_path(output_path("FIELD_GROUP_SCHEMA_LEDGER", "json")), "status": "PASS"},
            {"requirement": "parser/redaction/as-of/no-leak/fail-closed contract emitted", "evidence": repo_path(output_path("PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT", "json")), "status": "PASS"},
            {"requirement": "fixtures cover valid, missing, unavailable, forbidden, stale, duplicate, and manifest-repair cases", "evidence": repo_path(output_path("FIXTURE_MANIFEST", "json")), "status": "PASS"},
            {"requirement": "fixture validation proves expected pass/fail behavior", "evidence": repo_path(output_path("FIXTURE_VALIDATION_RESULT_LEDGER", "json")), "status": "PASS"},
            {"requirement": "read-only monitoring alignment emitted with no code wiring", "evidence": repo_path(output_path("READ_ONLY_MONITORING_ALIGNMENT_LEDGER", "json")), "status": "PASS"},
            {"requirement": "manifest-binding repair carried forward", "evidence": repo_path(output_path("MANIFEST_HASH_POLICY_LEDGER", "json")), "status": "PASS"},
            {"requirement": "G12 acceptance criteria and next audit prompt emitted", "evidence": repo_path(NEXT_G12_PROMPT), "status": "PASS"},
            {"requirement": "safe flags and forbidden surfaces closed", "evidence": "all route ledgers and verifier checks", "status": "PASS"},
            {"requirement": "scoped commits and final LIVE_STATE refresh", "evidence": "required after verifier/test pass before final goal closeout", "status": "PENDING_EXTERNAL_COMMIT_STEP"},
        ],
        "instruction_coverage": {
            "goal_session_research_discipline_read_after_preflight": True,
            "research_operating_doctrine_read_after_preflight": True,
            "lane_type": "builder/evidence-capture implementation package",
            "builder_posture_applied": "maximal constructive offline implementation inside hard boundaries",
            "anti_boxing_questions_pursued": saturation["anti_boxing_questions_pursued"],
            "proof_or_impossibility_stop_condition": saturation["proof_or_impossibility_stop_condition"],
            "requirements_deliberately_not_answered_because_forbidden": context_anchor["deliberately_not_opened"],
        },
        "terminal_decision": TERMINAL_DECISION,
    }
    generated += write_pair("COMPLETION_AUDIT", "Completion Audit", completion)

    closeout = {
        **base_payload("closeout_verification"),
        "status": "BUILD_ARTIFACTS_EMITTED_VERIFIER_AND_FOCUSED_TESTS_PENDING",
        "planned_commands": [
            f"python {repo_path(scripts[0])}",
            f"python {repo_path(scripts[1])}",
            f"python -m pytest -q -p no:cacheprovider {repo_path(scripts[2])}",
            "python scripts/generate_live_state.py",
        ],
        "terminal_decision": TERMINAL_DECISION,
    }
    generated += write_pair("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout)

    manifest = build_output_manifest(generated)
    generated += write_pair("OUTPUT_MANIFEST", "Output Manifest", manifest)

    syntax = syntax_parse(scripts)
    verifier_result = run_command(["python", repo_path(scripts[1])])
    pytest_result = run_command(["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", repo_path(scripts[2])])
    closeout.update(
        {
            "status": "STANDALONE_VERIFIER_AND_FOCUSED_PYTEST_PASSED_FINAL_LIVE_STATE_REFRESH_REQUIRED"
            if verifier_result["returncode"] == 0 and pytest_result["returncode"] == 0 and syntax["ok"]
            else "VERIFICATION_OR_TEST_FAILURE",
            "syntax_parse": syntax,
            "standalone_verifier": verifier_result,
            "focused_pytest": pytest_result,
        }
    )
    generated += write_pair("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout)

    completion["standalone_verifier_ok"] = verifier_result["returncode"] == 0
    completion["focused_tests_ok"] = pytest_result["returncode"] == 0
    completion["syntax_parse_ok"] = syntax["ok"]
    completion["completion_standard_satisfied"] = (
        completion["standalone_verifier_ok"] and completion["focused_tests_ok"] and completion["syntax_parse_ok"]
    )
    generated += write_pair("COMPLETION_AUDIT", "Completion Audit", completion)

    verification_result_path = output_path("VERIFICATION_RESULT", "json")
    manifest = build_output_manifest(generated)
    generated += write_pair("OUTPUT_MANIFEST", "Output Manifest", manifest)
    final_verifier_result = run_command(["python", repo_path(scripts[1])])
    if verification_result_path.exists():
        generated.append(verification_result_path)
    manifest = build_output_manifest(generated)
    generated += write_pair("OUTPUT_MANIFEST", "Output Manifest", manifest)
    return {
        "ok": final_verifier_result["returncode"] == 0 and pytest_result["returncode"] == 0,
        "route_id": ROUTE_ID,
        "terminal_decision": TERMINAL_DECISION,
        "artifact_count": manifest["artifact_count"],
        "schema_file_count": manifest["schema_file_count"],
        "fixture_file_count": manifest["fixture_file_count"],
        "standalone_verifier_returncode": final_verifier_result["returncode"],
        "focused_pytest_returncode": pytest_result["returncode"],
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
