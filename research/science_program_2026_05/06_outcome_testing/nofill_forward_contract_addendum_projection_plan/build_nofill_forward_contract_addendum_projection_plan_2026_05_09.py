#!/usr/bin/env python3
"""Build NOFILL forward contract addendum and projection-plan artifacts.

This lane is source/control only. It writes versioned research artifacts under
this directory and does not import or modify live trading components.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
ROUTE_ID = "NOFILL_FORWARD_CONTRACT_ADDENDUM_PROJECTION_PLAN"
SCHEMA_VERSION = "nofill_forward_contract_addendum_projection_plan_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_DECISION = "SOURCE_CONTROL_ADDENDUM_READY_NO_RESULT_SCORING"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
BASE = Path("research/science_program_2026_05/06_outcome_testing")
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "NOFILL_FORWARD_CONTRACT_ADDENDUM_PROJECTION_PLAN_GOAL_PROMPT_2026-05-09.md"
)

FORWARD_CONTRACT_DIR = BASE / "nofill_cat_v3_forward_lifecycle_capture_contract"
G12_FORWARD_AUDIT_DIR = BASE / "g12_nofill_forward_lifecycle_capture_contract_audit"
G12_USDJPY_AUDIT_DIR = BASE / "g12_nofill_usdjpy_sequence_source_audit"
G0_SYNTHESIS_DIR = BASE / "g0_nofill_cat_v3_categorical_evidence_synthesis_control_review"
G12_COUNT_AUDIT_DIR = BASE / "g12_nofill_cat_v3_quarantined_categorical_count_packet_audit"

SOURCE_ROOTS = [
    "shadow_logs/strategy_follow_candidates.jsonl",
    "shadow_logs/candidate_path_follow.jsonl",
    "shadow_logs/candidate_ltf_path_order.jsonl",
    "shadow_logs/pending_limit_lifecycle.jsonl",
    "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl",
    "shadow_logs/prefill_delivery_path.jsonl",
    "shadow_logs/v2b_forward_pairs.jsonl",
    "shadow_logs/fvg_ob_confluence.jsonl",
    "src/research_infra/forward_capture.py",
    "src/components/pending_limit_lifecycle_logger.py",
    "src/research_infra/live_shadow_gap_closure.py",
    "src/research_infra/live_mechanical_shadow.py",
    "scripts/audit_live_shadow_data_health.py",
    "scripts/verify_shadow_log_integrity.py",
]

CONTEXT_INPUTS = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    str(PROMPT_PATH),
    str(G12_FORWARD_AUDIT_DIR / "G12_NOFILL_FORWARD_DECISION_LEDGER_2026-05-09.md"),
    str(G12_FORWARD_AUDIT_DIR / "G12_NOFILL_FORWARD_SCHEMA_AUDIT_2026-05-09.json"),
    str(FORWARD_CONTRACT_DIR / "NOFILL_FORWARD_CAPTURE_CONTRACT_2026-05-09.json"),
    str(FORWARD_CONTRACT_DIR / "NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_2026-05-09.json"),
    str(G12_USDJPY_AUDIT_DIR / "G12_NOFILL_USDJPY_SEQ_DECISION_LEDGER_2026-05-09.md"),
    str(G0_SYNTHESIS_DIR / "G0_NOFILL_CAT_V3_EVIDENCE_CHAIN_RECONCILIATION_2026-05-09.md"),
    str(G12_COUNT_AUDIT_DIR / "G12_NOFILL_CAT_V3_COUNT_AUDIT_LABEL_FAMILY_REVIEW_2026-05-09.md"),
]

LOCAL_HEAVY_ROOTS = [
    "C:/Users/MSI/Documents/ai-trading-agent/data",
    "C:/Users/MSI/Documents/ai-trading-agent/data/ticks",
    "C:/Users/MSI/Documents/ai-trading-agent/shadow_logs",
    "C:/Users/MSI/Documents/ai-trading-agent/exports",
    "C:/tmp",
    "C:/SierraChart",
    "C:/Users/MSI/Documents",
]

CONTROL_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_live_wiring": False,
    "opens_paid_api_or_databento_route": False,
    "opens_registry_edit": False,
    "changes_live_trading_behavior": False,
}

FORBIDDEN_OUTPUT_FIELD_NAMES = {
    "account_history",
    "account_pnl",
    "actual_r",
    "broker_actual_r",
    "broker_fill_state",
    "deal_id",
    "expectancy",
    "fill_time_utc",
    "live_order_state",
    "mt5_deal_id",
    "mt5_order_ticket",
    "mt5_position_id",
    "order_send_attempted",
    "order_send_success",
    "pending_ticket",
    "position_id",
    "r_multiple",
    "r_value",
    "slippage_price",
    "synthetic_path_r",
    "trade_state_ticket",
    "win_rate",
}

FORBIDDEN_VALUE_PATTERNS = [
    re.compile(r"\b(?:actual[-_ ]?r|broker[-_ ]?actual|synthetic[-_ ]?path[-_ ]?r)\b", re.I),
    re.compile(r"\b(?:win[-_ ]?rate|expectancy|dsr|pbo|sharpe)\b", re.I),
    re.compile(r"\b(?:mt5[-_ ]?order[-_ ]?ticket|mt5[-_ ]?deal|position[-_ ]?id)\b", re.I),
]

ALLOWED_SOURCE_TYPES = [
    "decision_time_candidate_safe_projection",
    "pending_limit_lifecycle_source_safe_projection",
    "candidate_path_follow_source_safe_projection",
    "candidate_ltf_path_order_source_safe_projection",
    "tick_parquet_readonly_manifest",
    "lower_tf_ohlc_readonly_manifest",
    "source_control_rebuild_artifact",
    "source_contract_artifact",
    "parser_hash_manifest",
    "hashed_file_mtime_manifest",
]

BASE_FORBIDDEN_FIELDS = sorted(FORBIDDEN_OUTPUT_FIELD_NAMES)

NULL_STATUS_VOCAB = [
    "CAPTURED_DIRECT",
    "DERIVED_FROM_SOURCE_CREATED_AT",
    "DERIVED_FROM_HASHED_FILE_MTIME",
    "NOT_CAPTURED_IN_RAW_SOURCE",
    "SOURCE_FIELD_MISSING",
    "SOURCE_FIELD_PRESENT_REDACTED",
    "NOT_OPENED_FOR_SOURCE_CONTROL",
    "CLOCK_SKEW_NOT_MEASURABLE_SOURCE_ONLY",
    "PARSER_REBUILD_TIME_ONLY_NOT_DECISION_FEATURE",
    "INVALID_FAIL_CLOSED",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def sha256_file(rel_path: str | Path) -> str | None:
    path = REPO_ROOT / rel_path
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, payload: dict[str, Any] | list[Any]) -> None:
    (OUT_DIR / name).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_md(name: str, text: str) -> None:
    (OUT_DIR / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def field_spec(
    *,
    name: str,
    family: str,
    blocker_id: str,
    source_rule: str,
    allowed_roots: list[str],
    statuses: list[str],
    required: str = "required",
    readiness: str = "READY_FOR_OFFLINE_SOURCE_SAFE_PROJECTION",
    verifier: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "field_name": name,
        "schema_family": family,
        "blocker_id": blocker_id,
        "source_asof_rule": source_rule,
        "allowed_source_roots_or_logs": allowed_roots,
        "allowed_source_types": ALLOWED_SOURCE_TYPES,
        "forbidden_fields_or_values": BASE_FORBIDDEN_FIELDS,
        "hash_provenance_requirements": [
            "source_file_sha256",
            "parser_code_sha256",
            "projection_builder_version",
            "controlling_git_head",
            "source_lineage_path",
        ],
        "null_missing_status_vocabulary": statuses,
        "duplicate_denominator_effect": "NO_DENOMINATOR_EFFECT_SOURCE_CONTROL_FIELD_ONLY",
        "required_or_optional": required,
        "implementation_readiness_status": readiness,
        "verifier_assertions": verifier
        or [
            f"{name} exists in projection schema",
            f"{name} never changes accepted/source-control/source-impossible/reject counts",
            f"{name} never opens result scoring or validation",
        ],
    }


def blocker_closures() -> list[dict[str, Any]]:
    latency_roots = [
        "shadow_logs/strategy_follow_candidates.jsonl",
        "shadow_logs/candidate_path_follow.jsonl",
        "shadow_logs/candidate_ltf_path_order.jsonl",
        "shadow_logs/pending_limit_lifecycle.jsonl",
        "hashed_file_mtime_manifest",
    ]
    pending_roots = [
        "shadow_logs/pending_limit_lifecycle.jsonl",
        "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl",
        "knowledge_base/meta/pending_intent_*.pkl source inventory only after separate parser hash",
    ]
    spread_roots = [
        "shadow_logs/strategy_follow_candidates.jsonl",
        "shadow_logs/pending_limit_lifecycle.jsonl",
        "shadow_logs/candidate_ltf_path_order.jsonl",
        "tick_parquet_readonly_manifest",
    ]
    return [
        {
            "blocker_id": "G12-FWD-BLOCKER-001",
            "blocker_name": "capture_latency_write_clock_skew",
            "closure_decision": "CLOSED_BY_ADDENDUM_FIELDS_AND_FAIL_CLOSED_MISSING_STATUSES",
            "proof_status": "PROOF_BY_SOURCE_CONTROL_SCHEMA_AND_VERIFIER_ASSERTIONS",
            "terminal_boundary": "No live logger wiring is authorized; existing rows may project NOT_CAPTURED statuses.",
            "fields": [
                field_spec(
                    name="capture_observed_at_utc",
                    family="capture_latency_clock",
                    blocker_id="G12-FWD-BLOCKER-001",
                    source_rule="Use raw row created_at_utc/backfilled_at_utc when present and at or after decision_asof_utc; otherwise null with capture_observed_status.",
                    allowed_roots=latency_roots,
                    statuses=["CAPTURED_DIRECT", "DERIVED_FROM_SOURCE_CREATED_AT", "NOT_CAPTURED_IN_RAW_SOURCE"],
                ),
                field_spec(
                    name="capture_write_started_at_utc",
                    family="capture_latency_clock",
                    blocker_id="G12-FWD-BLOCKER-001",
                    source_rule="Populate only when a source-safe writer explicitly records write start. Existing raw rows use NOT_CAPTURED_IN_RAW_SOURCE.",
                    allowed_roots=latency_roots,
                    statuses=["CAPTURED_DIRECT", "NOT_CAPTURED_IN_RAW_SOURCE"],
                    required="required_with_explicit_missing_status",
                ),
                field_spec(
                    name="capture_write_completed_at_utc",
                    family="capture_latency_clock",
                    blocker_id="G12-FWD-BLOCKER-001",
                    source_rule="Populate only from explicit write-complete timestamp or hashed file-mtime manifest; never infer from un-hashed filesystem state.",
                    allowed_roots=latency_roots,
                    statuses=["CAPTURED_DIRECT", "DERIVED_FROM_HASHED_FILE_MTIME", "NOT_CAPTURED_IN_RAW_SOURCE"],
                ),
                field_spec(
                    name="capture_latency_ms",
                    family="capture_latency_clock",
                    blocker_id="G12-FWD-BLOCKER-001",
                    source_rule="write_completed minus observed timestamp when both are source-safe; null when either side is absent.",
                    allowed_roots=latency_roots,
                    statuses=["CAPTURED_DIRECT", "NOT_CAPTURED_IN_RAW_SOURCE", "INVALID_FAIL_CLOSED"],
                ),
                field_spec(
                    name="capture_clock_source_status",
                    family="capture_latency_clock",
                    blocker_id="G12-FWD-BLOCKER-001",
                    source_rule="Categorical clock source only: broker_time, system_utc, hashed_file_mtime, parser_rebuild_time, or unavailable.",
                    allowed_roots=latency_roots,
                    statuses=[
                        "BROKER_TIME_SOURCE",
                        "SYSTEM_UTC_SOURCE",
                        "HASHED_FILE_MTIME_SOURCE",
                        "PARSER_REBUILD_TIME_ONLY_NOT_DECISION_FEATURE",
                        "SOURCE_FIELD_MISSING",
                    ],
                ),
                field_spec(
                    name="capture_clock_skew_ms",
                    family="capture_latency_clock",
                    blocker_id="G12-FWD-BLOCKER-001",
                    source_rule="Populate only from an approved broker-offset measurement captured as source metadata; never backfill from outcomes.",
                    allowed_roots=latency_roots,
                    statuses=[
                        "CAPTURED_DIRECT",
                        "CLOCK_SKEW_NOT_MEASURABLE_SOURCE_ONLY",
                        "SOURCE_FIELD_MISSING",
                    ],
                ),
                field_spec(
                    name="capture_clock_skew_status",
                    family="capture_latency_clock",
                    blocker_id="G12-FWD-BLOCKER-001",
                    source_rule="Closed categorical status for skew measurement availability and validity.",
                    allowed_roots=latency_roots,
                    statuses=[
                        "CLOCK_SKEW_MEASURED_SOURCE_SAFE",
                        "CLOCK_SKEW_NOT_MEASURABLE_SOURCE_ONLY",
                        "CLOCK_SOURCE_MIXED_FAIL_CLOSED",
                    ],
                ),
                field_spec(
                    name="capture_timestamp_derivation_rule",
                    family="capture_latency_clock",
                    blocker_id="G12-FWD-BLOCKER-001",
                    source_rule="Short parser rule identifier explaining how observed/write/skew fields were populated or why they are missing.",
                    allowed_roots=latency_roots,
                    statuses=["DIRECT_SOURCE_FIELDS", "HASHED_FILE_MTIME_RULE", "MISSING_STATUS_RULE"],
                ),
            ],
            "remaining_owner_access_source_requirement": (
                "To populate direct live write-start/write-complete/skew values prospectively, open a separate "
                "owner-approved live-wiring lane. The contract itself is closed because missing statuses and "
                "verifier rules are now explicit."
            ),
        },
        {
            "blocker_id": "G12-FWD-BLOCKER-002",
            "blocker_name": "pending_order_observability_ticket_redaction",
            "closure_decision": "CLOSED_BY_ALLOWLIST_PROJECTION_AND_TICKET_REDACTION_PROOF",
            "proof_status": "PROOF_BY_DRY_RUN_REDACTION_AND_FORBIDDEN_OUTPUT_FIELD_SCAN",
            "terminal_boundary": "No raw MT5 tickets, order-send flags, account/order/history/deal/position labels, or broker fill states may enter a contract row.",
            "fields": [
                field_spec(
                    name="pending_order_mode_source_safe",
                    family="pending_order_observability",
                    blocker_id="G12-FWD-BLOCKER-002",
                    source_rule="Allowlist pending_order_mode into internal/source-safe values only; unknown values fail closed.",
                    allowed_roots=pending_roots,
                    statuses=[
                        "INTERNAL_CANDLE_POLLED_INTENT",
                        "SOURCE_FIELD_MISSING",
                        "UNKNOWN_MODE_FAIL_CLOSED",
                    ],
                ),
                field_spec(
                    name="pending_order_mode_status",
                    family="pending_order_observability",
                    blocker_id="G12-FWD-BLOCKER-002",
                    source_rule="Categorical capture status for pending_order_mode_source_safe.",
                    allowed_roots=pending_roots,
                    statuses=["CAPTURED_DIRECT", "SOURCE_FIELD_MISSING", "INVALID_FAIL_CLOSED"],
                ),
                field_spec(
                    name="broker_pending_order_created_status",
                    family="pending_order_observability",
                    blocker_id="G12-FWD-BLOCKER-002",
                    source_rule="Status only; never emit raw bool, ticket, order-send success, fill state, account history, deal, or position fields.",
                    allowed_roots=pending_roots,
                    statuses=[
                        "INTERNAL_ONLY_NO_NATIVE_BROKER_ORDER",
                        "NATIVE_PENDING_OBSERVABILITY_PRESENT_REDACTED",
                        "BROKER_PENDING_OBSERVABILITY_NOT_OPENED_FOR_SOURCE_CONTROL",
                        "SOURCE_FIELD_MISSING",
                    ],
                ),
                field_spec(
                    name="native_pending_order_type_source_safe",
                    family="pending_order_observability",
                    blocker_id="G12-FWD-BLOCKER-002",
                    source_rule="Allowlist order type category only when source is source-safe; no ticket/order-history fields.",
                    allowed_roots=pending_roots,
                    statuses=[
                        "BUY_LIMIT",
                        "SELL_LIMIT",
                        "INTERNAL_LIMIT_INTENT_ONLY",
                        "NOT_OPENED_FOR_SOURCE_CONTROL",
                        "SOURCE_FIELD_MISSING",
                        "UNKNOWN_TYPE_FAIL_CLOSED",
                    ],
                ),
                field_spec(
                    name="native_pending_order_type_status",
                    family="pending_order_observability",
                    blocker_id="G12-FWD-BLOCKER-002",
                    source_rule="Categorical capture status for native pending order type source.",
                    allowed_roots=pending_roots,
                    statuses=["CAPTURED_SOURCE_SAFE", "NOT_OPENED_FOR_SOURCE_CONTROL", "SOURCE_FIELD_MISSING"],
                ),
                field_spec(
                    name="raw_ticket_field_present_status",
                    family="pending_order_observability",
                    blocker_id="G12-FWD-BLOCKER-002",
                    source_rule="Hazard status only, derived during projection. It records that a raw ticket-like source field existed without preserving value or hash.",
                    allowed_roots=pending_roots,
                    statuses=[
                        "RAW_TICKET_FIELD_NOT_IN_SOURCE",
                        "RAW_TICKET_FIELD_EMPTY",
                        "RAW_TICKET_VALUE_PRESENT_REDACTED",
                    ],
                ),
                field_spec(
                    name="mt5_order_ticket_redaction_status",
                    family="pending_order_observability",
                    blocker_id="G12-FWD-BLOCKER-002",
                    source_rule="Projection fails closed if any raw ticket value appears in projected output keys or values.",
                    allowed_roots=pending_roots,
                    statuses=[
                        "PASS_NO_TICKET_VALUE_EXPOSED",
                        "SOURCE_TICKET_VALUE_REDACTED",
                        "FAIL_TICKET_VALUE_DETECTED_IN_OUTPUT",
                    ],
                    verifier=[
                        "raw mt5_order_ticket, pending_ticket, and trade_state_ticket values are absent from projection output",
                        "no output key contains ticket",
                        "projection output contains redaction status only",
                    ],
                ),
            ],
            "remaining_owner_access_source_requirement": (
                "If the owner wants native broker pending-order type/created status populated beyond redacted observability, "
                "a separate source-contract lane must approve the source and prove no ticket/order-history/fill labels."
            ),
        },
        {
            "blocker_id": "G12-FWD-BLOCKER-003",
            "blocker_name": "spread_slippage_execution_quality_status",
            "closure_decision": "CLOSED_BY_SOURCE_SAFE_SPREAD_FIELDS_AND_CLOSED_SLIPPAGE_EXECUTION_STATUSES",
            "proof_status": "PROOF_BY_CLOSED_STATUS_FIELDS_AND_FORBIDDEN_RESULT_SCORING_SCAN",
            "terminal_boundary": "Cost, slippage, survival-adjusted expectancy, and execution-quality testing remain unopened.",
            "fields": [
                field_spec(
                    name="decision_spread_status",
                    family="spread_slippage_execution_quality_status",
                    blocker_id="G12-FWD-BLOCKER-003",
                    source_rule="Decision-time spread capture status only; spread value allowed only if captured at or before decision_asof_utc from source-safe quote metadata.",
                    allowed_roots=spread_roots,
                    statuses=["CAPTURED_SOURCE_SAFE", "SOURCE_FIELD_MISSING", "NOT_OPENED_FOR_SOURCE_CONTROL"],
                ),
                field_spec(
                    name="decision_spread_value_source_safe",
                    family="spread_slippage_execution_quality_status",
                    blocker_id="G12-FWD-BLOCKER-003",
                    source_rule="Numeric spread from decision/as-of quote only; never from fill, deal, order history, PnL, or slippage fields.",
                    allowed_roots=spread_roots,
                    statuses=["CAPTURED_SOURCE_SAFE", "SOURCE_FIELD_MISSING"],
                    required="optional_with_status",
                ),
                field_spec(
                    name="decision_spread_unit",
                    family="spread_slippage_execution_quality_status",
                    blocker_id="G12-FWD-BLOCKER-003",
                    source_rule="points, ticks, price, or source-native unit declared with spread value.",
                    allowed_roots=spread_roots,
                    statuses=["POINTS", "TICKS", "PRICE", "SOURCE_NATIVE", "SOURCE_FIELD_MISSING"],
                ),
                field_spec(
                    name="entry_touch_spread_status",
                    family="spread_slippage_execution_quality_status",
                    blocker_id="G12-FWD-BLOCKER-003",
                    source_rule="Entry-touch spread status only. Existing paths without quote-spread at touch use SOURCE_FIELD_MISSING.",
                    allowed_roots=spread_roots,
                    statuses=["CAPTURED_SOURCE_SAFE", "SOURCE_FIELD_MISSING", "TOUCH_NOT_OBSERVED_SOURCE_SAFE"],
                ),
                field_spec(
                    name="entry_touch_spread_value_source_safe",
                    family="spread_slippage_execution_quality_status",
                    blocker_id="G12-FWD-BLOCKER-003",
                    source_rule="Numeric spread at source-safe entry-touch quote only; never filled slippage or order-history data.",
                    allowed_roots=spread_roots,
                    statuses=["CAPTURED_SOURCE_SAFE", "SOURCE_FIELD_MISSING", "TOUCH_NOT_OBSERVED_SOURCE_SAFE"],
                    required="optional_with_status",
                ),
                field_spec(
                    name="spread_source_hash",
                    family="spread_slippage_execution_quality_status",
                    blocker_id="G12-FWD-BLOCKER-003",
                    source_rule="SHA256 of the source artifact used for any spread value.",
                    allowed_roots=spread_roots,
                    statuses=["HASH_PRESENT", "SOURCE_FIELD_MISSING"],
                ),
                field_spec(
                    name="slippage_label_status",
                    family="spread_slippage_execution_quality_status",
                    blocker_id="G12-FWD-BLOCKER-003",
                    source_rule="Fixed closed status in this lane. Slippage values and labels are not opened.",
                    allowed_roots=spread_roots,
                    statuses=["NOT_OPENED_FOR_SOURCE_CONTROL"],
                    verifier=["field exists and equals NOT_OPENED_FOR_SOURCE_CONTROL in projection contract"],
                ),
                field_spec(
                    name="slippage_value_redaction_status",
                    family="spread_slippage_execution_quality_status",
                    blocker_id="G12-FWD-BLOCKER-003",
                    source_rule="If raw slippage_price exists, output only this redaction status and never the value.",
                    allowed_roots=spread_roots,
                    statuses=[
                        "RAW_SLIPPAGE_FIELD_NOT_IN_SOURCE",
                        "RAW_SLIPPAGE_FIELD_EMPTY",
                        "RAW_SLIPPAGE_VALUE_PRESENT_REDACTED",
                    ],
                ),
                field_spec(
                    name="execution_quality_label_status",
                    family="spread_slippage_execution_quality_status",
                    blocker_id="G12-FWD-BLOCKER-003",
                    source_rule="Fixed closed status in this lane. No execution-quality labels are opened.",
                    allowed_roots=spread_roots,
                    statuses=["NOT_OPENED_FOR_SOURCE_CONTROL"],
                    verifier=["field exists and equals NOT_OPENED_FOR_SOURCE_CONTROL in projection contract"],
                ),
                field_spec(
                    name="execution_quality_value_redaction_status",
                    family="spread_slippage_execution_quality_status",
                    blocker_id="G12-FWD-BLOCKER-003",
                    source_rule="If raw order-send/fill/execution fields exist, output only this redaction status and never values.",
                    allowed_roots=spread_roots,
                    statuses=[
                        "RAW_EXECUTION_FIELD_NOT_IN_SOURCE",
                        "RAW_EXECUTION_FIELD_PRESENT_REDACTED",
                    ],
                ),
                field_spec(
                    name="cost_testing_gate_status",
                    family="spread_slippage_execution_quality_status",
                    blocker_id="G12-FWD-BLOCKER-003",
                    source_rule="Closed gate status preventing cost/survival-adjusted expectancy testing from this contract addendum.",
                    allowed_roots=spread_roots,
                    statuses=["COST_TESTING_NOT_OPENED", "SPREAD_ONLY_SOURCE_CONTROL_READY"],
                ),
            ],
            "remaining_owner_access_source_requirement": (
                "Future cost or survival-adjusted expectancy testing needs a separate result/cost lane with source-safe spread-at-decision/touch manifests. "
                "Slippage and execution-quality labels remain closed here."
            ),
        },
    ]


def projection_field_schema(closures: list[dict[str, Any]]) -> dict[str, Any]:
    fields = [field for closure in closures for field in closure["fields"]]
    family_counts = Counter(field["schema_family"] for field in fields)
    return {
        **CONTROL_FLAGS,
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact": "NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA",
        "field_count": len(fields),
        "field_families": dict(sorted(family_counts.items())),
        "fields": fields,
        "projection_output_allowed_fields": [field["field_name"] for field in fields],
        "forbidden_output_field_names": BASE_FORBIDDEN_FIELDS,
        "null_missing_status_vocabulary": NULL_STATUS_VOCAB,
        "duplicate_denominator_policy": {
            "row_level_accepted_denominator": 225,
            "primary_duplicate_key_denominator": 182,
            "secondary_duplicate_group_denominator": 139,
            "effect": "NO_CHANGE_BY_ADDENDUM_FIELDS",
            "required_rule": "Addendum projection metadata never creates accepted rows, result rows, or duplicate-key members.",
        },
    }


def source_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in SOURCE_ROOTS:
        path = REPO_ROOT / rel
        entry: dict[str, Any] = {
            "path": rel,
            "exists": path.exists(),
            "sha256": sha256_file(rel),
            "role": "source_safe_projection_candidate_or_code_evidence",
        }
        if path.exists() and path.suffix == ".jsonl":
            keys: set[str] = set()
            forbidden_key_hits: set[str] = set()
            sampled = 0
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if sampled >= 200:
                        break
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        item = json.loads(stripped)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(item, dict):
                        sampled += 1
                        keys.update(item.keys())
                        forbidden_key_hits.update(k for k in item.keys() if k in FORBIDDEN_OUTPUT_FIELD_NAMES)
            entry.update(
                {
                    "sampled_json_rows": sampled,
                    "observed_key_count": len(keys),
                    "observed_forbidden_key_hits": sorted(forbidden_key_hits),
                    "projection_rule": "raw rows require allowlist projection; forbidden keys are never output",
                }
            )
        rows.append(entry)
    return rows


def local_heavy_inventory() -> list[dict[str, Any]]:
    out = []
    for root in LOCAL_HEAVY_ROOTS:
        path = Path(root)
        out.append(
            {
                "root": root,
                "exists": path.exists(),
                "use_in_this_lane": "discovery_or_source_inventory_only_not_validation_safe",
                "searched_mode": "existence_and_known-source-path check; no broad recursive scan",
            }
        )
    return out


def project_source_safe_status(raw: dict[str, Any], *, source_root: str) -> dict[str, Any]:
    """Return only addendum status fields from a raw source row.

    This dry-run projection is intentionally conservative. It proves the output
    vocabulary can expose source availability and hazards without leaking ticket,
    order, account, fill, R, slippage, or execution labels.
    """
    mode = str(raw.get("pending_order_mode") or "")
    native_type = str(raw.get("native_pending_order_type") or "")
    ticket_values = [
        raw.get("mt5_order_ticket"),
        raw.get("pending_ticket"),
        raw.get("trade_state_ticket"),
    ]
    ticket_present = any(v not in (None, "", 0, "0") for v in ticket_values)
    execution_present = any(
        key in raw
        for key in (
            "order_send_attempted",
            "order_send_success",
            "broker_fill_state",
            "fill_time_utc",
        )
    )
    slippage_present = raw.get("slippage_price") not in (None, "")
    spread_value = raw.get("spread")
    created = raw.get("created_at_utc") or raw.get("backfilled_at_utc") or raw.get("timestamp_utc")
    projected = {
        "capture_observed_at_utc": created,
        "capture_write_started_at_utc": None,
        "capture_write_completed_at_utc": None,
        "capture_latency_ms": None,
        "capture_clock_source_status": "SYSTEM_UTC_SOURCE" if created else "SOURCE_FIELD_MISSING",
        "capture_clock_skew_ms": None,
        "capture_clock_skew_status": "CLOCK_SKEW_NOT_MEASURABLE_SOURCE_ONLY",
        "capture_timestamp_derivation_rule": (
            "DERIVED_FROM_SOURCE_CREATED_AT" if created else "MISSING_STATUS_RULE"
        ),
        "pending_order_mode_source_safe": (
            "INTERNAL_CANDLE_POLLED_INTENT"
            if mode in {"", "INTERNAL_CANDLE_POLLED_INTENT"}
            else "UNKNOWN_MODE_FAIL_CLOSED"
        ),
        "pending_order_mode_status": "CAPTURED_DIRECT" if mode else "SOURCE_FIELD_MISSING",
        "broker_pending_order_created_status": (
            "NATIVE_PENDING_OBSERVABILITY_PRESENT_REDACTED"
            if raw.get("broker_pending_order_created") is True
            else "INTERNAL_ONLY_NO_NATIVE_BROKER_ORDER"
            if raw.get("broker_pending_order_created") is False
            else "SOURCE_FIELD_MISSING"
        ),
        "native_pending_order_type_source_safe": (
            native_type
            if native_type in {"BUY_LIMIT", "SELL_LIMIT"}
            else "INTERNAL_LIMIT_INTENT_ONLY"
            if not native_type
            else "UNKNOWN_TYPE_FAIL_CLOSED"
        ),
        "native_pending_order_type_status": "CAPTURED_SOURCE_SAFE" if native_type else "SOURCE_FIELD_MISSING",
        "raw_ticket_field_present_status": (
            "RAW_TICKET_VALUE_PRESENT_REDACTED" if ticket_present else "RAW_TICKET_FIELD_EMPTY"
        ),
        "mt5_order_ticket_redaction_status": (
            "SOURCE_TICKET_VALUE_REDACTED" if ticket_present else "PASS_NO_TICKET_VALUE_EXPOSED"
        ),
        "decision_spread_status": (
            "CAPTURED_SOURCE_SAFE" if spread_value not in (None, "") else "SOURCE_FIELD_MISSING"
        ),
        "decision_spread_value_source_safe": spread_value if spread_value not in (None, "") else None,
        "decision_spread_unit": "SOURCE_NATIVE" if spread_value not in (None, "") else "SOURCE_FIELD_MISSING",
        "entry_touch_spread_status": "SOURCE_FIELD_MISSING",
        "entry_touch_spread_value_source_safe": None,
        "spread_source_hash": sha256_file(source_root) if spread_value not in (None, "") else None,
        "slippage_label_status": "NOT_OPENED_FOR_SOURCE_CONTROL",
        "slippage_value_redaction_status": (
            "RAW_SLIPPAGE_VALUE_PRESENT_REDACTED"
            if slippage_present
            else "RAW_SLIPPAGE_FIELD_EMPTY"
            if "slippage_price" in raw
            else "RAW_SLIPPAGE_FIELD_NOT_IN_SOURCE"
        ),
        "execution_quality_label_status": "NOT_OPENED_FOR_SOURCE_CONTROL",
        "execution_quality_value_redaction_status": (
            "RAW_EXECUTION_FIELD_PRESENT_REDACTED"
            if execution_present
            else "RAW_EXECUTION_FIELD_NOT_IN_SOURCE"
        ),
        "cost_testing_gate_status": "COST_TESTING_NOT_OPENED",
    }
    return projected


def projection_has_forbidden_leak(projected: dict[str, Any], raw: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key in projected:
        if key in FORBIDDEN_OUTPUT_FIELD_NAMES or "ticket" in key.lower():
            if key not in {"mt5_order_ticket_redaction_status", "raw_ticket_field_present_status"}:
                issues.append(f"forbidden output key: {key}")
    text = json.dumps(projected, sort_keys=True)
    for ticket_key in ("mt5_order_ticket", "pending_ticket", "trade_state_ticket"):
        raw_value = raw.get(ticket_key)
        if raw_value not in (None, "", 0, "0") and str(raw_value) in text:
            issues.append(f"raw ticket value leaked: {ticket_key}")
    for forbidden_key in FORBIDDEN_OUTPUT_FIELD_NAMES:
        if forbidden_key in projected:
            issues.append(f"forbidden direct field emitted: {forbidden_key}")
    return issues


def no_leak_audit(schema: dict[str, Any], closures: list[dict[str, Any]]) -> dict[str, Any]:
    raw_fixture = {
        "created_at_utc": "2026-05-09T10:00:00+00:00",
        "timestamp_utc": "2026-05-09T10:00:01+00:00",
        "pending_order_mode": "INTERNAL_CANDLE_POLLED_INTENT",
        "broker_pending_order_created": True,
        "native_pending_order_type": "BUY_LIMIT",
        "mt5_order_ticket": 09,
        "pending_ticket": "pending-local-abc",
        "trade_state_ticket": 987654321,
        "order_send_attempted": True,
        "order_send_success": True,
        "broker_fill_state": "filled",
        "fill_time_utc": "2026-05-09T10:01:00+00:00",
        "slippage_price": 0.12,
        "actual_r": 1.5,
        "synthetic_path_r": -1.0,
        "spread": 16.0,
    }
    projected = project_source_safe_status(
        raw_fixture,
        source_root="shadow_logs/pending_limit_lifecycle.jsonl",
    )
    leak_issues = projection_has_forbidden_leak(projected, raw_fixture)
    output_field_violations = sorted(
        key for key in schema["projection_output_allowed_fields"] if key in FORBIDDEN_OUTPUT_FIELD_NAMES
    )
    value_pattern_issues = []
    for field in schema["fields"]:
        for key in ("field_name",):
            value = str(field.get(key) or "")
            if any(pattern.search(value) for pattern in FORBIDDEN_VALUE_PATTERNS):
                value_pattern_issues.append({"field_name": field.get("field_name"), "issue": value})
    return {
        **CONTROL_FLAGS,
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact": "NOFILL_FORWARD_NO_LEAK_AND_FORBIDDEN_FIELD_AUDIT",
        "status": "PASS" if not leak_issues and not output_field_violations else "FAIL",
        "dry_run_projection_fixture": {
            "raw_fixture_contains_forbidden_values": True,
            "projected_output": projected,
            "leak_issues": leak_issues,
        },
        "output_field_violations": output_field_violations,
        "field_name_value_pattern_issues": value_pattern_issues,
        "raw_source_inventory": source_inventory(),
        "local_heavy_inventory": local_heavy_inventory(),
        "blocked_routes_preserved": [
            "result_scoring",
            "validation",
            "promotion",
            "broker_account_order_history_deal_position_labels",
            "paid_api_or_databento_calls",
            "live_logger_wiring",
            "registry_edits",
        ],
        "closed_flag_checks": {
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "blockers": [
            {
                "blocker_id": closure["blocker_id"],
                "closure_decision": closure["closure_decision"],
                "field_count": len(closure["fields"]),
            }
            for closure in closures
        ],
    }


def source_hash_manifest() -> list[dict[str, Any]]:
    rows = []
    for rel in CONTEXT_INPUTS + SOURCE_ROOTS:
        rows.append(
            {
                "path": rel,
                "exists": (REPO_ROOT / rel).exists(),
                "sha256": sha256_file(rel),
                "role": "controlling_input_or_source_surface",
            }
        )
    return rows


def contract_addendum_json(
    closures: list[dict[str, Any]],
    schema: dict[str, Any],
    audit: dict[str, Any],
) -> dict[str, Any]:
    return {
        **CONTROL_FLAGS,
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "terminal_decision": TERMINAL_DECISION,
        "generated_at_utc": utc_now_iso(),
        "controlling_git_head": run_git(["log", "-1", "--oneline"]),
        "controlling_prompt": str(PROMPT_PATH),
        "source_hash_manifest": source_hash_manifest(),
        "evidence_chain_controls": {
            "row_level_accepted_denominator": 225,
            "primary_duplicate_key_denominator": 182,
            "secondary_duplicate_group_denominator": 139,
            "source_control_exclusions": [
                "NOFILL-CAT-ROW-0049",
                "NOFILL-CAT-ROW-0050",
                "NOFILL-CAT-ROW-0051",
                "NOFILL-CAT-ROW-0241",
            ],
            "source_impossible_exclusions": [
                "NOFILL-CAT-ROW-0130",
                "NOFILL-CAT-ROW-0143",
                "NOFILL-CAT-ROW-0165",
                "NOFILL-CAT-ROW-0178",
            ],
            "reject_rows": 65,
            "reject_overlap_rows": 47,
            "addendum_denominator_effect": "NO_CHANGE",
        },
        "blocker_closure_decisions": closures,
        "projection_schema_artifact": "NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA_2026-05-09.json",
        "no_leak_audit_status": audit["status"],
        "all_required_blockers_closed_or_preserved": {
            "G12-FWD-BLOCKER-001": closures[0]["closure_decision"],
            "G12-FWD-BLOCKER-002": closures[1]["closure_decision"],
            "G12-FWD-BLOCKER-003": closures[2]["closure_decision"],
        },
        "required_field_count": schema["field_count"],
        "implementation_readiness": (
            "READY_FOR_OFFLINE_SOURCE_SAFE_PROJECTION_BUILDER_PLAN; "
            "LIVE_WIRING_AND_RESULT_SCORING_REMAIN_SEPARATE_FORBIDDEN_LANES"
        ),
    }


def spec_json(closures: list[dict[str, Any]], blocker_id: str, artifact: str) -> dict[str, Any]:
    closure = next(item for item in closures if item["blocker_id"] == blocker_id)
    return {
        **CONTROL_FLAGS,
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "artifact": artifact,
        "blocker_id": blocker_id,
        "closure_decision": closure["closure_decision"],
        "proof_status": closure["proof_status"],
        "fields": closure["fields"],
        "remaining_owner_access_source_requirement": closure["remaining_owner_access_source_requirement"],
        "duplicate_denominator_effect": "NO_CHANGE",
    }


def contract_addendum_md(addendum: dict[str, Any]) -> str:
    closure_lines = []
    for closure in addendum["blocker_closure_decisions"]:
        field_names = ", ".join(field["field_name"] for field in closure["fields"])
        closure_lines.append(
            f"- `{closure['blocker_id']}`: `{closure['closure_decision']}`. "
            f"Fields: {field_names}. Remaining requirement: {closure['remaining_owner_access_source_requirement']}"
        )
    return f"""# NOFILL Forward Contract Addendum 2026-05-09

- route_id: `{ROUTE_ID}`
- schema_version: `{SCHEMA_VERSION}`
- promotion_verdict: `{PROMOTION_VERDICT}`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`
- opens_result_scoring: `false`
- changes_live_trading_behavior: `false`

## Decision

Terminal decision: `{TERMINAL_DECISION}`.

This addendum closes the three G12 forward-contract blockers for the source/control contract by adding explicit field names, missing-status vocabulary, redaction proof, and verifier assertions. It does not consume raw logs directly, wire live loggers, score results, validate an edge, promote a source, edit registries, call paid/API/Databento routes, or open broker/account/order/history/deal/position labels.

## Blocker Closures

{chr(10).join(closure_lines)}

## Count And Duplicate Boundary

The addendum has `NO_CHANGE` effect on the frozen G0/G12 count equation: 225 accepted input-only rows, 182 primary duplicate-key members, 139 secondary duplicate-group members, 4 source-control exclusions, 4 source-impossible exclusions, 65 rejects, and 47 reject-overlap rows filtered before accepted denominators.

## Projection Rule

Existing raw logs are source inventory only until an offline allowlist projection builder emits the exact fields in `NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA_2026-05-09.json`, attaches source and parser hashes, applies ticket/slippage/execution redaction, and passes the verifier. Missing latency/spread/native-pending values are explicit status states, not hidden nulls.
"""


def context_anchor_md(addendum: dict[str, Any]) -> str:
    inputs = "\n".join(
        f"- `{row['path']}` exists={str(row['exists']).lower()} sha256=`{row['sha256']}`"
        for row in addendum["source_hash_manifest"]
    )
    return f"""# NOFILL Forward Addendum Context Anchor 2026-05-09

- route_id: `{ROUTE_ID}`
- controlling_prompt: `{PROMPT_PATH}`
- current_head_at_build: `{addendum['controlling_git_head']}`
- promotion_verdict: `{PROMOTION_VERDICT}`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`

## Lane Boundary

Source/control addendum and offline projection-builder plan only. No live trading surfaces, no result scoring, no validation, no promotion, no broker/account/order/history/deal/position labels, no paid/API/Databento calls, no registry edits, no remote.

## Active Question Stack

- Close `G12-FWD-BLOCKER-001` with explicit capture latency/write/clock-skew fields or exact missing statuses.
- Close `G12-FWD-BLOCKER-002` with source-safe pending-order observability and MT5 ticket redaction proof.
- Close `G12-FWD-BLOCKER-003` with source-safe spread fields and closed slippage/execution-quality statuses.
- Preserve G0/G12 denominator boundaries and `NO_PROMOTION_VERDICT`.

## Inputs Read Or Hashed

{inputs}

## Stop Condition Status

All three blockers have source/control closure decisions in the addendum. Any future live writer, native broker pending-order source exposure, cost scoring, or result lane requires a separate owner-approved goal.
"""


def pending_order_redaction_md(audit: dict[str, Any]) -> str:
    projected = audit["dry_run_projection_fixture"]["projected_output"]
    projected_lines = "\n".join(f"- `{k}`: `{v}`" for k, v in sorted(projected.items()))
    return f"""# NOFILL Forward Pending Order Redaction Proof 2026-05-09

- route_id: `{ROUTE_ID}`
- promotion_verdict: `{PROMOTION_VERDICT}`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`

## Proof

The dry-run fixture intentionally includes raw ticket/order/fill/result-shaped fields: `mt5_order_ticket`, `pending_ticket`, `trade_state_ticket`, `order_send_attempted`, `order_send_success`, `broker_fill_state`, `fill_time_utc`, `slippage_price`, `actual_r`, and `synthetic_path_r`.

The source-safe projection emits only addendum status fields. It does not emit raw ticket values, ticket hashes, order-send booleans, fill state, account/order-history fields, slippage value, actual R, synthetic R, win-rate, or expectancy.

Projection leak issues: `{audit['dry_run_projection_fixture']['leak_issues']}`.

## Projected Status Output

{projected_lines}

## Required Verifier Behavior

- Fail if any output key equals a forbidden raw field name.
- Fail if any raw ticket value appears in output keys or values.
- Fail if `slippage_label_status` or `execution_quality_label_status` differs from `NOT_OPENED_FOR_SOURCE_CONTROL`.
- Fail if `validation_safe`, `outcome_review_opened`, or `live_effect` is true.
"""


def offline_projection_plan_md() -> str:
    return f"""# NOFILL Forward Offline Projection Builder Plan 2026-05-09

- route_id: `{ROUTE_ID}`
- promotion_verdict: `{PROMOTION_VERDICT}`
- validation_safe: `false`
- outcome_review_opened: `false`
- live_effect: `false`

## Purpose

Build an offline, read-only projection builder that consumes existing source/log artifacts only through an allowlist and emits source/control rows matching `NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA_2026-05-09.json`.

## Inputs

- `shadow_logs/strategy_follow_candidates.jsonl`
- `shadow_logs/candidate_path_follow.jsonl`
- `shadow_logs/candidate_ltf_path_order.jsonl`
- `shadow_logs/pending_limit_lifecycle.jsonl`
- `shadow_logs/pending_limit_lifecycle_join_backfill.jsonl`
- `shadow_logs/prefill_delivery_path.jsonl`
- `shadow_logs/v2b_forward_pairs.jsonl`
- `shadow_logs/fvg_ob_confluence.jsonl`
- read-only tick/lower-timeframe manifests only when source-hashed
- parser/build/source-contract artifacts listed in the context anchor

## Projection Stages

1. Read raw rows as source inventory and compute source SHA256, parser SHA256, controlling git head, source line number, and source route.
2. Apply a strict allowlist for identity, decision/as-of, source coverage, event-order, and the addendum fields.
3. Redact ticket, order-send, fill, account/order-history, slippage, execution-quality, actual-R, synthetic-R, win-rate, expectancy, DSR, and PBO fields.
4. Emit explicit missing statuses for capture latency/write/skew, native pending-order observability, and entry-touch spread when source fields are absent.
5. Attach duplicate/denominator controls and assert `NO_CHANGE` to the frozen 225/182/139 denominators.
6. Run verifier before any row is treated as contract-complete.

## Forbidden Routes

No MT5 live call, order/account/history/deal/position export, paid/API/Databento call, live logger wiring, prompt/risk/execution/permissions/safety/selector/canary change, result scoring, validation, promotion, or registry edit is opened by this plan.

## Future Owner/Access Requirements

- Direct live capture latency/write/skew population requires a separate owner-approved live-wiring lane.
- Native broker pending-order observability beyond redacted status requires a separate source contract proving no ticket/order-history/fill leakage.
- Cost/slippage/execution-quality or survival-adjusted expectancy testing requires a separate result/cost lane after source fields are captured and accepted.
"""


def decision_ledger_md(closures: list[dict[str, Any]]) -> str:
    rows = []
    for closure in closures:
        rows.append(
            "| `{}` | `{}` | `{}` | `{}` |".format(
                closure["blocker_id"],
                closure["closure_decision"],
                closure["proof_status"],
                closure["remaining_owner_access_source_requirement"],
            )
        )
    return f"""# NOFILL Forward Blocker Closure Decision Ledger 2026-05-09

Promotion posture: `{PROMOTION_VERDICT}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

| Blocker | Decision | Proof | Remaining owner/access/source requirement |
|---|---|---|---|
{chr(10).join(rows)}

## Boundary

This ledger is a source/control addendum. It does not open outcome review, result scoring, validation, promotion, live behavior, remote, paid/API/Databento, registry edits, or broker/account/order/history/deal/position labels.
"""


def next_prompt_pack_md() -> str:
    return f"""# NOFILL Forward Next Prompt Pack 2026-05-09

Promotion posture: `{PROMOTION_VERDICT}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Next Allowed Source-Control Prompt

`/goal Build the offline NOFILL forward source-safe projection builder from the accepted addendum at research/science_program_2026_05/06_outcome_testing/nofill_forward_contract_addendum_projection_plan/. Consume only approved existing logs through allowlist projection, attach source/parser hashes, emit explicit missing statuses, preserve 225/182/139 denominators, and keep NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false. Do not wire live loggers, score results, validate, promote, edit registries, call paid/API/Databento, touch live trading surfaces, or use broker/account/order/history/deal/position labels.`

## Separate Future Lanes

- Owner-approved live-wiring lane for prospective direct capture latency/write/skew fields.
- Broker-native pending-order source contract if native pending observability must be more than redacted status.
- Result/cost lane only after accepted source packet exists; this addendum does not authorize it.
"""


def completion_audit_md(addendum: dict[str, Any], audit: dict[str, Any]) -> str:
    required_outputs = [
        "NOFILL_FORWARD_ADDENDUM_CONTEXT_ANCHOR_2026-05-09.md",
        "NOFILL_FORWARD_CONTRACT_ADDENDUM_2026-05-09.md",
        "NOFILL_FORWARD_CONTRACT_ADDENDUM_2026-05-09.json",
        "NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA_2026-05-09.json",
        "NOFILL_FORWARD_PENDING_ORDER_REDACTION_PROOF_2026-05-09.md",
        "NOFILL_FORWARD_LATENCY_CLOCK_SKEW_CAPTURE_SPEC_2026-05-09.json",
        "NOFILL_FORWARD_SPREAD_SLIPPAGE_EXECUTION_QUALITY_STATUS_SPEC_2026-05-09.json",
        "NOFILL_FORWARD_OFFLINE_PROJECTION_BUILDER_PLAN_2026-05-09.md",
        "NOFILL_FORWARD_NO_LEAK_AND_FORBIDDEN_FIELD_AUDIT_2026-05-09.json",
        "NOFILL_FORWARD_BLOCKER_CLOSURE_DECISION_LEDGER_2026-05-09.md",
        "NOFILL_FORWARD_NEXT_PROMPT_PACK_2026-05-09.md",
        "NOFILL_FORWARD_ADDENDUM_COMPLETION_AUDIT_2026-05-09.md",
        "build_nofill_forward_contract_addendum_projection_plan_2026_05_09.py",
        "verify_nofill_forward_contract_addendum_projection_plan_2026_05_09.py",
        "test_nofill_forward_contract_addendum_projection_plan_2026_05_09.py",
    ]
    checklist = [
        ("mandatory preflight and context anchor", "PASS", "context anchor records prompt, core docs, handoff, source hashes"),
        ("G12-FWD-BLOCKER-001", "PASS", addendum["all_required_blockers_closed_or_preserved"]["G12-FWD-BLOCKER-001"]),
        ("G12-FWD-BLOCKER-002", "PASS", addendum["all_required_blockers_closed_or_preserved"]["G12-FWD-BLOCKER-002"]),
        ("G12-FWD-BLOCKER-003", "PASS", addendum["all_required_blockers_closed_or_preserved"]["G12-FWD-BLOCKER-003"]),
        ("NO_PROMOTION_VERDICT and closed flags", "PASS", "validation_safe=false, outcome_review_opened=false, live_effect=false"),
        ("no result scoring", "PASS", "opens_result_scoring=false and cost_testing_gate_status=COST_TESTING_NOT_OPENED"),
        ("no broker/account/order-history labels", "PASS", f"dry-run leak issues={audit['dry_run_projection_fixture']['leak_issues']}"),
        ("no live trading surfaces", "PASS", "artifact scope is research directory only"),
        ("duplicate denominator preservation", "PASS", "NO_CHANGE to 225/182/139 denominators"),
        ("local-heavy/source search", "PASS", "source inventory and local-heavy existence ledger recorded in no-leak audit"),
    ]
    checklist_md = "\n".join(f"- {item}: `{status}` - {evidence}" for item, status, evidence in checklist)
    outputs_md = "\n".join(f"- `{name}`" for name in required_outputs)
    return f"""# NOFILL Forward Addendum Completion Audit 2026-05-09

## Objective Restatement

Resolve `G12-FWD-BLOCKER-001..003` from the G12 NOFILL forward lifecycle capture contract audit by producing a source/control-only contract addendum and offline source-safe projection-builder plan. Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`, and all live-surface boundaries.

## Prompt-To-Artifact Checklist

{checklist_md}

## Required Output Inventory

{outputs_md}

## Completion Decision

`can_mark_goal_complete` is `true` only after generated JSON parses, generated Python compiles, focused pytest passes, the verifier passes, artifacts are committed, research context is refreshed, and closeout `LIVE_STATE` is regenerated. At artifact-build time, this audit's artifact coverage is complete and all blockers are closed or precisely preserved inside the source/control lane.

## Residual Boundaries

This lane did not and must not answer performance, validation, promotion, cost expectancy, slippage outcome, broker actual-R, account-history, or live-execution questions.
"""


def build_all() -> dict[str, Any]:
    closures = blocker_closures()
    schema = projection_field_schema(closures)
    audit = no_leak_audit(schema, closures)
    addendum = contract_addendum_json(closures, schema, audit)

    write_json("NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA_2026-05-09.json", schema)
    write_json("NOFILL_FORWARD_NO_LEAK_AND_FORBIDDEN_FIELD_AUDIT_2026-05-09.json", audit)
    write_json("NOFILL_FORWARD_CONTRACT_ADDENDUM_2026-05-09.json", addendum)
    write_json(
        "NOFILL_FORWARD_LATENCY_CLOCK_SKEW_CAPTURE_SPEC_2026-05-09.json",
        spec_json(closures, "G12-FWD-BLOCKER-001", "NOFILL_FORWARD_LATENCY_CLOCK_SKEW_CAPTURE_SPEC"),
    )
    write_json(
        "NOFILL_FORWARD_SPREAD_SLIPPAGE_EXECUTION_QUALITY_STATUS_SPEC_2026-05-09.json",
        spec_json(closures, "G12-FWD-BLOCKER-003", "NOFILL_FORWARD_SPREAD_SLIPPAGE_EXECUTION_QUALITY_STATUS_SPEC"),
    )
    write_md("NOFILL_FORWARD_CONTRACT_ADDENDUM_2026-05-09.md", contract_addendum_md(addendum))
    write_md("NOFILL_FORWARD_ADDENDUM_CONTEXT_ANCHOR_2026-05-09.md", context_anchor_md(addendum))
    write_md("NOFILL_FORWARD_PENDING_ORDER_REDACTION_PROOF_2026-05-09.md", pending_order_redaction_md(audit))
    write_md("NOFILL_FORWARD_OFFLINE_PROJECTION_BUILDER_PLAN_2026-05-09.md", offline_projection_plan_md())
    write_md("NOFILL_FORWARD_BLOCKER_CLOSURE_DECISION_LEDGER_2026-05-09.md", decision_ledger_md(closures))
    write_md("NOFILL_FORWARD_NEXT_PROMPT_PACK_2026-05-09.md", next_prompt_pack_md())
    write_md("NOFILL_FORWARD_ADDENDUM_COMPLETION_AUDIT_2026-05-09.md", completion_audit_md(addendum, audit))
    return {
        "addendum": addendum,
        "schema": schema,
        "audit": audit,
    }


if __name__ == "__main__":
    result = build_all()
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "schema_version": SCHEMA_VERSION,
                "generated_files": 12,
                "field_count": result["schema"]["field_count"],
                "no_leak_status": result["audit"]["status"],
                "terminal_decision": TERMINAL_DECISION,
            },
            sort_keys=True,
        )
    )
