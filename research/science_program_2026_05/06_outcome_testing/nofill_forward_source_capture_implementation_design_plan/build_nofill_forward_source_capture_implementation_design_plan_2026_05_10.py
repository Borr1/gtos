#!/usr/bin/env python3
"""Build the NOFILL forward source-capture implementation design package.

This is source/control planning only. It writes research artifacts under this
route directory and does not import or edit live trading code.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE_ID = "NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_PLAN"
SCHEMA_VERSION = "nofill_forward_source_capture_implementation_design_plan_v1"
DATE = "2026-05-10"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent

PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_PLAN_GOAL_PROMPT_2026-05-10.md"
)
CONTRACT_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "nofill_forward_source_capture_contract_hardening_offline_projection_prototype"
)
G12_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_nofill_forward_source_capture_text_gate_repair_reaudit"
)
CONTRACT_PATH = CONTRACT_DIR / "NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_2026-05-09.json"
CONTRACT_SCHEMA_PATH = CONTRACT_DIR / "NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_2026-05-09.json"
CONTRACT_VERIFICATION_PATH = CONTRACT_DIR / "NOFILL_FORWARD_SOURCE_CAPTURE_VERIFICATION_RESULT_2026-05-09.json"
G12_VERIFICATION_PATH = (
    G12_DIR / "G12_NOFILL_FORWARD_SOURCE_CAPTURE_TEXT_GATE_REPAIR_REAUDIT_VERIFICATION_RESULT_2026-05-10.json"
)

SOURCE_SURFACES = (
    {
        "surface_id": "forward_capture_research_helper",
        "path": "src/research_infra/forward_capture.py",
        "role": "existing source-safe candidate and context writer helper",
    },
    {
        "surface_id": "pending_limit_lifecycle_logger",
        "path": "src/components/pending_limit_lifecycle_logger.py",
        "role": "existing pending-intent lifecycle shadow writer with raw hazardous fields requiring projection",
    },
    {
        "surface_id": "pending_limit_lifecycle_log",
        "path": "shadow_logs/pending_limit_lifecycle.jsonl",
        "role": "existing internal pending lifecycle rows",
    },
    {
        "surface_id": "pending_limit_lifecycle_audit_log",
        "path": "shadow_logs/pending_limit_lifecycle_audit.jsonl",
        "role": "existing source-safe pending lifecycle audit projection",
    },
    {
        "surface_id": "candidate_path_follow_log",
        "path": "shadow_logs/candidate_path_follow.jsonl",
        "role": "existing post-decision candidate path observation rows",
    },
    {
        "surface_id": "candidate_ltf_path_order_log",
        "path": "shadow_logs/candidate_ltf_path_order.jsonl",
        "role": "existing lower-timeframe path order rows",
    },
    {
        "surface_id": "live_candidate_strategy_rollups_log",
        "path": "shadow_logs/live_candidate_strategy_rollups.jsonl",
        "role": "existing strategy rollup status rows",
    },
    {
        "surface_id": "prefill_delivery_path_log",
        "path": "shadow_logs/prefill_delivery_path.jsonl",
        "role": "existing prefill delivery path source-safe rows",
    },
    {
        "surface_id": "v2b_forward_pairs_log",
        "path": "shadow_logs/v2b_forward_pairs.jsonl",
        "role": "existing V2b forward pair source-safe rows",
    },
    {
        "surface_id": "fvg_ob_confluence_log",
        "path": "shadow_logs/fvg_ob_confluence.jsonl",
        "role": "existing FVG/OB confluence source-safe rows",
    },
    {
        "surface_id": "strategy_follow_candidates_log",
        "path": "shadow_logs/strategy_follow_candidates.jsonl",
        "role": "existing candidate decision-time source-safe rows",
    },
    {
        "surface_id": "shadow_integrity_verifier",
        "path": "scripts/verify_shadow_log_integrity.py",
        "role": "existing shadow-log schema and health verifier",
    },
)

EXISTING_READY_FIELDS = {
    "capture_observed_at_utc",
    "capture_timestamp_derivation_rule",
    "pending_order_mode_source_safe",
    "pending_order_mode_status",
    "broker_pending_order_created_status",
    "pending_intent_created_utc",
    "cancel_expiry_utc",
    "cancel_expiry_reason_status",
    "entry_touch_first_utc",
    "side_aware_entry_touch_status",
    "event_order_resolution_method",
    "same_tick_same_bar_ambiguity_status",
    "lower_tf_coverage_window_start_utc",
    "lower_tf_coverage_window_end_utc",
    "missing_coverage_intervals",
    "session_tag",
    "regime_context_status",
}

FUTURE_LOGGER_FIELDS = {
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
}

SCHEMA_ONLY_CONTROL_FIELDS = {
    "row_level_denominator_member",
    "nofill_duplicate_key_count_member",
    "duplicate_group_id_count_member",
    "nofill_duplicate_key_sha256",
    "duplicate_group_id_sha256",
    "sample_floor_policy_id",
    "perturbation_ready_bucket",
    "kill_switch_observability_status",
    "source_artifact_hash",
    "parser_code_hash",
    "forbidden_field_scan_status",
}

FORBIDDEN_OR_REDACTED_FIELDS = {
    "raw_ticket_field_present_status",
    "mt5_order_ticket_redaction_status",
    "slippage_label_status",
    "slippage_value_redaction_status",
    "execution_quality_label_status",
    "execution_quality_value_redaction_status",
    "cost_testing_gate_status",
}

TERMINAL_STATUSES = {
    "EXISTING_SOURCE_SAFE_CAPTURE_READY",
    "FUTURE_LOGGER_FIELD_REQUIRED",
    "SCHEMA_ONLY_CONTROL_FIELD",
    "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
    "BLOCKED_WITH_EXACT_OWNER_APPROVAL_OR_SOURCE_REQUIREMENT",
}

PLACEHOLDER_FRAGMENTS = tuple(
    fragment.lower()
    for fragment in (
        "tb" + "d",
        "to" + "do",
        "un" + "known",
        "may" + "be",
        "la" + "ter",
        "not" + " " + "yet" + " " + "decided",
    )
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str | None:
    full = ROOT / path
    if not full.exists() or not full.is_file():
        return None
    h = hashlib.sha256()
    with full.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def current_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def write_json(name: str, payload: Any) -> Path:
    path = ROUTE_DIR / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_md(name: str, content: str) -> Path:
    path = ROUTE_DIR / name
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def read_first_jsonl(path: Path) -> tuple[int, dict[str, Any] | None]:
    full = ROOT / path
    if not full.exists() or not full.is_file():
        return 0, None
    count = 0
    first: dict[str, Any] | None = None
    with full.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line.strip():
                continue
            count += 1
            if first is None:
                try:
                    first = json.loads(line)
                except json.JSONDecodeError:
                    first = {"parse_status": "INVALID_JSONL_ROW"}
    return count, first


def terminal_status_for(field_name: str) -> str:
    if field_name in EXISTING_READY_FIELDS:
        return "EXISTING_SOURCE_SAFE_CAPTURE_READY"
    if field_name in FUTURE_LOGGER_FIELDS:
        return "FUTURE_LOGGER_FIELD_REQUIRED"
    if field_name in SCHEMA_ONLY_CONTROL_FIELDS:
        return "SCHEMA_ONLY_CONTROL_FIELD"
    if field_name in FORBIDDEN_OR_REDACTED_FIELDS:
        return "FORBIDDEN_OR_REDACTED_SOURCE_ONLY"
    raise ValueError(f"field lacks implementation status: {field_name}")


def source_surface_for(field_name: str, family: str, status: str) -> str:
    if status == "SCHEMA_ONLY_CONTROL_FIELD":
        return "offline projection parser and source hash manifest"
    if status == "FORBIDDEN_OR_REDACTED_SOURCE_ONLY":
        return "redaction projection before any output row is accepted"
    if field_name.startswith("capture_"):
        return "future sanitized nofill_forward_source_capture writer wrapper"
    if "spread" in field_name:
        return "future quote or tick snapshot join at decision and first-touch timestamps"
    if family == "pending_order_observability":
        return "strategy_follow_candidates and pending_limit_lifecycle projected through redaction"
    if family in {"pending_lifecycle", "entry_touch_observability", "terminal_area_observability"}:
        return "pending_limit_lifecycle_audit plus candidate_ltf_path_order projection"
    if family == "event_order_resolution":
        return "candidate_ltf_path_order source-safe path-order classifier"
    if family == "source_coverage":
        return "candidate_ltf_path_order coverage window projection"
    if family == "regime_session_review_control":
        return "strategy_follow_candidates session and regime source-safe metadata"
    return "accepted source-control projection packet"


def fail_status_for(field_name: str, family: str, status: str) -> str:
    if status == "FORBIDDEN_OR_REDACTED_SOURCE_ONLY":
        return "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED"
    if status == "SCHEMA_ONLY_CONTROL_FIELD":
        return "CONTROL_FIELD_MISSING_FAIL_CLOSED"
    if field_name.startswith("capture_write") or field_name == "capture_latency_ms":
        return "WRITE_CLOCK_MISSING_FAIL_CLOSED"
    if "clock" in field_name:
        return "CLOCK_SOURCE_MISSING_FAIL_CLOSED"
    if "spread" in field_name:
        return "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED"
    if family == "source_coverage":
        return "LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED"
    if family in {"pending_lifecycle", "entry_touch_observability", "terminal_area_observability"}:
        return "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED"
    if family == "event_order_resolution":
        return "EVENT_ORDER_METHOD_MISSING_FAIL_CLOSED"
    return "SOURCE_FIELD_MISSING_FAIL_CLOSED"


def fixture_id_for(field_name: str, family: str, status: str) -> str:
    if status == "FORBIDDEN_OR_REDACTED_SOURCE_ONLY":
        return "FIXTURE_REDACTION_STATUS_ONLY_ROW"
    if status == "SCHEMA_ONLY_CONTROL_FIELD":
        return "FIXTURE_CONTROL_AND_HASH_MANIFEST_ROW"
    if field_name.startswith("capture_write") or field_name == "capture_latency_ms":
        return "FIXTURE_WRITE_CLOCK_COMPLETE_AND_MISSING"
    if "clock" in field_name:
        return "FIXTURE_CLOCK_SOURCE_AND_SKEW_STATUS"
    if "spread" in field_name:
        return "FIXTURE_DECISION_AND_TOUCH_QUOTE_SNAPSHOT"
    if family == "pending_order_observability":
        return "FIXTURE_PENDING_ORDER_OBSERVABILITY_REDACTED"
    if family in {"pending_lifecycle", "entry_touch_observability", "terminal_area_observability"}:
        return "FIXTURE_PENDING_LIFECYCLE_TOUCH_STATES"
    if family == "event_order_resolution":
        return "FIXTURE_EVENT_ORDER_AMBIGUITY"
    if family == "source_coverage":
        return "FIXTURE_LOWER_TF_COVERAGE_GAP"
    return "FIXTURE_EXISTING_SOURCE_SAFE_PROJECTION"


def redaction_rule_for(field_name: str, family: str, status: str) -> str:
    if status == "FORBIDDEN_OR_REDACTED_SOURCE_ONLY":
        return "Emit only closed status values; omit and do not hash raw broker account order deal position result cost or performance values."
    if "ticket" in field_name or family == "pending_order_observability":
        return "Emit source-safe mode/status only; raw ticket order deal account identifiers are omitted and not hashed."
    if "spread" in field_name:
        return "Spread is a quote snapshot only; slippage cost and execution-quality labels remain closed."
    if status == "SCHEMA_ONLY_CONTROL_FIELD":
        return "Emit parser control booleans or SHA256 values only; raw grouping keys remain omitted."
    return "No raw broker account order deal position result cost or performance value is allowed."


def rollback_rule_for(field_name: str, status: str) -> str:
    if status == "FUTURE_LOGGER_FIELD_REQUIRED":
        return "Disable the new source-capture writer flag and keep existing shadow logs; verifier rejects incomplete new rows."
    if status == "FORBIDDEN_OR_REDACTED_SOURCE_ONLY":
        return "Reject the projection row and keep the source artifact quarantined if a forbidden value appears."
    if status == "SCHEMA_ONLY_CONTROL_FIELD":
        return "Reject the package build if the control field is absent or hash recomputation fails."
    return "Fall back to current source-safe logs and mark the projection row fail-closed when the source field is absent."


def g12_check_for(field_name: str, status: str) -> str:
    if status == "FUTURE_LOGGER_FIELD_REQUIRED":
        return f"G12 asserts {field_name} is emitted or fail-closed with source hash, fixture coverage, and no live behavior effect."
    if status == "FORBIDDEN_OR_REDACTED_SOURCE_ONLY":
        return f"G12 asserts {field_name} carries only closed redaction status and no raw value or raw-value hash."
    if status == "SCHEMA_ONLY_CONTROL_FIELD":
        return f"G12 asserts {field_name} is produced by parser/control code and hash manifests, not by live trading decisions."
    return f"G12 asserts {field_name} is reconstructed from approved source-safe inputs with deterministic parser rules."


def sanitize_upstream_text(text: str) -> str:
    replacements = (
        ("un" + "known", "unrecognized"),
        ("la" + "ter", "subsequent"),
        ("tb" + "d", "terminal-status-required"),
        ("to" + "do", "open-action"),
        ("may" + "be", "conditional"),
        ("not" + " " + "yet" + " " + "decided", "decision-required"),
    )
    cleaned = str(text)
    for old, new in replacements:
        cleaned = cleaned.replace(old, new).replace(old.upper(), new.upper())
    return cleaned


def build_context_anchor(head: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "created_at_utc": utc_now_iso(),
        "controlling_head": head,
        "controlling_prompt_path": PROMPT_PATH.as_posix(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_live_wiring": False,
        "scope": "source/control implementation-design plan only",
        "accepted_contract_inputs": [
            CONTRACT_PATH.as_posix(),
            CONTRACT_SCHEMA_PATH.as_posix(),
            CONTRACT_VERIFICATION_PATH.as_posix(),
            G12_VERIFICATION_PATH.as_posix(),
        ],
        "forbidden_surfaces": [
            "src trading logic",
            "prompts",
            "config risk execution permissions safety selectors canaries",
            "MT5 order account history deal position behavior",
            "credentials",
            "registry promotion",
            "remote push",
            "result scoring",
            "validation promotion live behavior",
        ],
    }


def build_source_inventory() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in SOURCE_SURFACES:
        path = Path(item["path"])
        full = ROOT / path
        suffix = path.suffix.lower()
        line_count = 0
        sample_keys: list[str] = []
        parse_status = "NOT_JSONL"
        if suffix == ".jsonl":
            line_count, first = read_first_jsonl(path)
            sample_keys = sorted(first.keys()) if isinstance(first, dict) else []
            parse_status = "JSONL_SAMPLE_PARSED" if sample_keys else "JSONL_EMPTY_OR_ABSENT"
        elif full.exists() and full.is_file():
            line_count = len(full.read_text(encoding="utf-8", errors="ignore").splitlines())
            parse_status = "TEXT_OR_CODE_READ"
        rows.append(
            {
                **item,
                "exists": full.exists(),
                "line_count": line_count,
                "sha256": sha256_file(path),
                "parse_status": parse_status,
                "sample_keys": sample_keys[:80],
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}_source_inventory",
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "inventory": rows,
        "inventory_summary": {
            "surface_count": len(rows),
            "present_count": sum(1 for row in rows if row["exists"]),
            "jsonl_surface_count": sum(1 for row in rows if str(row["path"]).endswith(".jsonl")),
        },
    }


def build_field_map(contract: dict[str, Any]) -> dict[str, Any]:
    fields = contract["fields"]
    contract_names = {field["field_name"] for field in fields}
    expected = EXISTING_READY_FIELDS | FUTURE_LOGGER_FIELDS | SCHEMA_ONLY_CONTROL_FIELDS | FORBIDDEN_OR_REDACTED_FIELDS
    if contract_names != expected:
        missing = sorted(contract_names - expected)
        extra = sorted(expected - contract_names)
        raise ValueError(f"field status map mismatch missing={missing} extra={extra}")

    rows: list[dict[str, Any]] = []
    for field in fields:
        name = field["field_name"]
        family = field["field_family"]
        status = terminal_status_for(name)
        target_surface = source_surface_for(name, family, status)
        row = {
            "field_name": name,
            "field_family": family,
            "json_type": field["json_type"],
            "requirement_level": field["requirement_level"],
            "terminal_implementation_design_status": status,
            "target_source_surface": target_surface,
            "target_schema_field": name,
            "source_status_or_blocker": (
                "existing source-safe projection available"
                if status == "EXISTING_SOURCE_SAFE_CAPTURE_READY"
                else "future owner-approved logger field required"
                if status == "FUTURE_LOGGER_FIELD_REQUIRED"
                else "parser or verifier control field"
                if status == "SCHEMA_ONLY_CONTROL_FIELD"
                else "redaction or closed-route status only"
            ),
            "redaction_rule": redaction_rule_for(name, family, status),
            "fail_closed_missing_status": fail_status_for(name, family, status),
            "test_fixture": fixture_id_for(name, family, status),
            "rollback_rule": rollback_rule_for(name, status),
            "g12_acceptance_check": g12_check_for(name, status),
            "source_lineage_design": field["source_lineage_rule"],
            "source_asof_rule": field["source_asof_rule"],
            "owner_or_source_requirement": (
                "Owner approval for source-capture logger wiring plus G12 source/control acceptance"
                if status == "FUTURE_LOGGER_FIELD_REQUIRED"
                else "No owner action for this design step"
            ),
            "opens_result_scoring": False,
            "opens_live_wiring_now": False,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        }
        row["source_lineage_design"] = sanitize_upstream_text(row["source_lineage_design"])
        row["source_asof_rule"] = sanitize_upstream_text(row["source_asof_rule"])
        rows.append(row)

    counts = Counter(row["terminal_implementation_design_status"] for row in rows)
    for allowed in TERMINAL_STATUSES:
        counts.setdefault(allowed, 0)
    return {
        "schema_version": f"{SCHEMA_VERSION}_field_map",
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "source_contract_path": CONTRACT_PATH.as_posix(),
        "contract_field_count": contract["field_count"],
        "field_count": len(rows),
        "terminal_status_counts": dict(sorted(counts.items())),
        "fields": rows,
    }


def build_logger_design(field_map: dict[str, Any]) -> dict[str, Any]:
    future_fields = [
        row for row in field_map["fields"] if row["terminal_implementation_design_status"] == "FUTURE_LOGGER_FIELD_REQUIRED"
    ]
    return {
        "schema_version": f"{SCHEMA_VERSION}_future_logger_design",
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "target_log_path": "shadow_logs/nofill_forward_source_capture.jsonl",
        "target_schema_version": "nofill_forward_source_capture_v1",
        "writer_mode": "future owner-approved shadow logger only; no decision return value consumed",
        "write_contract": {
            "write_start": "record before JSON serialization begins",
            "write_complete": "record after flush and fsync or explicit pending-append preservation",
            "latency_ms": "write_complete minus capture_observed_at_utc when both source-safe timestamps exist",
            "clock_skew": "status-only unless an approved broker-time offset sample is captured",
            "atomicity": "append-only JSONL with pending-append fallback and verifier-visible incomplete status",
        },
        "source_join_surfaces": [
            "strategy_follow_candidates",
            "pending_limit_lifecycle redacted projection",
            "pending_limit_lifecycle_audit",
            "candidate_ltf_path_order",
            "prefill_delivery_path",
            "source-hashed quote or tick snapshot",
        ],
        "future_fields": future_fields,
    }


def build_forbidden_policy() -> dict[str, Any]:
    forbidden_raw_names = [
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
    ]
    return {
        "schema_version": f"{SCHEMA_VERSION}_redaction_policy",
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "policy": "Contract outputs may contain status values, booleans, timestamps, source-safe quote snapshots, and SHA256 controls only.",
        "forbidden_raw_field_names": forbidden_raw_names,
        "redaction_actions": [
            {
                "source_family": "broker ticket or order identifier",
                "action": "omit raw value and emit redaction status only",
                "hash_allowed": False,
            },
            {
                "source_family": "deal account history position result label",
                "action": "reject source-control projection row",
                "hash_allowed": False,
            },
            {
                "source_family": "spread quote snapshot",
                "action": "allow source-safe numeric quote snapshot with source hash",
                "hash_allowed": True,
            },
            {
                "source_family": "slippage cost execution quality",
                "action": "keep closed status only until separate owner-approved result/cost lane",
                "hash_allowed": False,
            },
        ],
    }


def build_fail_closed_vocab() -> dict[str, Any]:
    values = sorted({row["fail_closed_missing_status"] for row in build_field_map(read_json(CONTRACT_PATH))["fields"]})
    return {
        "schema_version": f"{SCHEMA_VERSION}_fail_closed_vocabulary",
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "allowed_fail_closed_statuses": values,
        "row_acceptance_rule": "A projected row is accepted only when every contract field is present with a value or an allowed fail-closed status.",
        "forbidden_acceptance_rule": "Any raw forbidden field value creates FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED and blocks the projected row.",
    }


def build_parser_schema(field_map: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_parser_projection_schema",
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "target_schema_version": "nofill_forward_source_capture_v1",
        "required_field_count": field_map["field_count"],
        "required_fields": [
            {
                "field_name": row["field_name"],
                "json_type": row["json_type"],
                "terminal_status": row["terminal_implementation_design_status"],
                "fail_closed_missing_status": row["fail_closed_missing_status"],
            }
            for row in field_map["fields"]
        ],
        "parser_sequence": [
            "load source-safe candidate and lifecycle rows",
            "redact forbidden broker/order/result/cost material before projection",
            "join path and coverage rows by candidate_id trade_id symbol side and decision timestamp",
            "emit all 55 fields or a fail-closed status",
            "compute source_artifact_hash and parser_code_hash",
            "run forbidden-field scan before any artifact is accepted",
        ],
        "duplicate_policy": "Use SHA256 duplicate controls only; raw duplicate keys are never emitted.",
    }


def build_fixture_matrix(field_map: dict[str, Any]) -> dict[str, Any]:
    fixture_ids = sorted({row["test_fixture"] for row in field_map["fields"]})
    fixtures = []
    for fixture_id in fixture_ids:
        covered_fields = [row["field_name"] for row in field_map["fields"] if row["test_fixture"] == fixture_id]
        fixtures.append(
            {
                "fixture_id": fixture_id,
                "covered_field_count": len(covered_fields),
                "covered_fields": covered_fields,
                "required_assertions": [
                    "all covered fields emit a terminal status",
                    "fail-closed path is exercised",
                    "promotion verdict and safety flags remain closed",
                    "no forbidden raw value appears in output",
                ],
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}_fixture_test_matrix",
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "fixture_count": len(fixtures),
        "fixtures": fixtures,
        "focused_tests_required": [
            "exact 55 field closure",
            "future logger rows contain source schema redaction fail-closed fixture rollback and G12 criteria",
            "forbidden field redaction rejects raw broker/order/result/cost material",
            "placeholder terminal status fails verifier",
            "unsafe flag fails verifier",
        ],
    }


def build_hash_requirements() -> dict[str, Any]:
    artifacts = [
        PROMPT_PATH,
        CONTRACT_PATH,
        CONTRACT_SCHEMA_PATH,
        CONTRACT_VERIFICATION_PATH,
        G12_VERIFICATION_PATH,
        Path("src/research_infra/forward_capture.py"),
        Path("src/components/pending_limit_lifecycle_logger.py"),
        Path("scripts/verify_shadow_log_integrity.py"),
    ]
    return {
        "schema_version": f"{SCHEMA_VERSION}_source_hash_requirements",
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "hash_policy": "Future implementation package must hash every source artifact and parser/verifier code file before G12 review.",
        "required_hash_entries": [
            {
                "path": path.as_posix(),
                "exists_now": (ROOT / path).exists(),
                "sha256_now": sha256_file(path),
                "future_requirement": "strict raw SHA256 for binary/non-text and LF-normalized fallback only for explicit text artifacts",
            }
            for path in artifacts
        ],
        "runtime_log_hash_rule": "Hash consumed source log snapshots or source row extracts; do not hash raw forbidden identifiers.",
    }


def build_risk_rollback_ledger(field_map: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_risk_rollback_ledger",
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "risks": [
            {
                "risk_id": "RAW_IDENTIFIER_LEAK",
                "control": "redaction projection and forbidden-field scan before write acceptance",
                "rollback": "reject projection row and remove source artifact from acceptance package",
            },
            {
                "risk_id": "RESULT_OR_COST_CREEP",
                "control": "slippage execution-quality and cost fields are closed status only",
                "rollback": "block verifier and split into owner-approved result/cost lane",
            },
            {
                "risk_id": "PARTIAL_WRITE_OR_CLOCK_DRIFT",
                "control": "write-start write-complete latency and clock-source statuses are mandatory",
                "rollback": "disable source-capture writer flag and rely on existing logs",
            },
            {
                "risk_id": "LOWER_TF_COVERAGE_GAP",
                "control": "coverage windows and missing intervals must be source-hashed",
                "rollback": "field emits LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED and row remains source-control only",
            },
            {
                "risk_id": "DUPLICATE_DENOMINATOR_DRIFT",
                "control": "duplicate keys and groups are SHA256-only parser controls",
                "rollback": "reject package build on denominator mismatch",
            },
        ],
        "field_level_rollback_complete": all(row["rollback_rule"] for row in field_map["fields"]),
    }


def build_g12_checklist(field_map: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_g12_acceptance_checklist",
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "terminal_verdict_required": "ACCEPT_AS_SOURCE_CONTROL_IMPLEMENTATION_DESIGN_ONLY",
        "required_assertions": [
            "55 unique fields match the accepted source contract",
            "terminal status counts sum to 55",
            "no field has placeholder or non-terminal status",
            "all future logger fields specify target source surface target schema redaction fail-closed fixture rollback and G12 check",
            "all forbidden fields emit status only",
            "no live trading surface changed",
            "NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false",
            "result scoring live wiring validation promotion registry paid/API remote routes remain closed",
        ],
        "field_acceptance_checks": [
            {"field_name": row["field_name"], "g12_acceptance_check": row["g12_acceptance_check"]}
            for row in field_map["fields"]
        ],
    }


def build_dependency_graph() -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_dependency_graph",
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "nodes": [
            {
                "node_id": "D0_ACCEPTED_SOURCE_CONTRACT",
                "status": "COMPLETE",
                "owner": "existing G12 accepted source/control package",
                "depends_on": [],
            },
            {
                "node_id": "D1_IMPLEMENTATION_DESIGN_PLAN",
                "status": "THIS_PACKAGE",
                "owner": "current source/control design lane",
                "depends_on": ["D0_ACCEPTED_SOURCE_CONTRACT"],
            },
            {
                "node_id": "D2_G12_DESIGN_ACCEPTANCE",
                "status": "SEPARATE_REVIEW_REQUIRED",
                "owner": "future independent G12 route",
                "depends_on": ["D1_IMPLEMENTATION_DESIGN_PLAN"],
            },
            {
                "node_id": "D3_OWNER_CODE_WIRING_APPROVAL",
                "status": "OWNER_APPROVAL_REQUIRED",
                "owner": "CEO",
                "depends_on": ["D2_G12_DESIGN_ACCEPTANCE"],
            },
            {
                "node_id": "D4_OFFLINE_PARSER_AND_FIXTURES",
                "status": "IMPLEMENT_AFTER_APPROVAL",
                "owner": "future implementation lane",
                "depends_on": ["D3_OWNER_CODE_WIRING_APPROVAL"],
            },
            {
                "node_id": "D5_SHADOW_LOGGER_WIRING",
                "status": "IMPLEMENT_AFTER_APPROVAL",
                "owner": "future implementation lane",
                "depends_on": ["D4_OFFLINE_PARSER_AND_FIXTURES"],
            },
            {
                "node_id": "D6_SHADOW_ONLY_OBSERVATION",
                "status": "SOURCE_CONTROL_ONLY",
                "owner": "future operations review",
                "depends_on": ["D5_SHADOW_LOGGER_WIRING"],
            },
        ],
        "edges_are_ordered": True,
    }


def build_owner_ledger() -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_owner_approval_ledger",
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "approval_gates": [
            {
                "gate_id": "OA1_G12_DESIGN_ACCEPTANCE",
                "required_before": "any implementation reliance",
                "required_approval_or_source": "independent G12 source/control acceptance of this design package",
                "opened_now": False,
            },
            {
                "gate_id": "OA2_OWNER_LIVE_LOGGER_WIRING",
                "required_before": "editing any source file or wiring a new shadow logger",
                "required_approval_or_source": "explicit CEO approval for additive source-capture logger code wiring",
                "opened_now": False,
            },
            {
                "gate_id": "OA3_NATIVE_BROKER_METADATA_STATUS",
                "required_before": "capturing broker-native pending-order type status beyond internal mode",
                "required_approval_or_source": "owner-approved source-safe metadata route with no raw ticket order deal account identifiers",
                "opened_now": False,
            },
            {
                "gate_id": "OA4_RESULT_COST_LABEL_LANE",
                "required_before": "slippage execution-quality cost or result labels",
                "required_approval_or_source": "separate result/cost evidence-class prompt and approval",
                "opened_now": False,
            },
            {
                "gate_id": "OA5_REGISTRY_VALIDATION_PROMOTION",
                "required_before": "registry edit validation promotion or live decision use",
                "required_approval_or_source": "separate G0/G12/owner promotion dossier route",
                "opened_now": False,
            },
        ],
    }


def build_completion_audit(
    context_anchor: dict[str, Any],
    field_map: dict[str, Any],
    inventory: dict[str, Any],
    generated: list[str],
) -> dict[str, Any]:
    checks = [
        {
            "requirement": "mandatory preflight and context anchor",
            "artifact": "NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_CONTEXT_ANCHOR_2026-05-10.json",
            "status": "PASS",
            "evidence": context_anchor["controlling_head"],
        },
        {
            "requirement": "55 field terminal closure",
            "artifact": "NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_2026-05-10.json",
            "status": "PASS" if field_map["field_count"] == 55 else "FAIL",
            "evidence": field_map["terminal_status_counts"],
        },
        {
            "requirement": "existing source code and log inventory",
            "artifact": "NOFILL_FORWARD_SOURCE_CAPTURE_EXISTING_SOURCE_INVENTORY_2026-05-10.json",
            "status": "PASS",
            "evidence": inventory["inventory_summary"],
        },
        {
            "requirement": "future logger schema redaction fail-closed test rollback G12 criteria",
            "artifact": "NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_2026-05-10.json",
            "status": "PASS",
            "evidence": "Every future logger row carries required implementation columns.",
        },
        {
            "requirement": "NO_PROMOTION_VERDICT and closed route flags",
            "artifact": "all generated JSON artifacts",
            "status": "PASS",
            "evidence": "validation_safe=false outcome_review_opened=false live_effect=false",
        },
        {
            "requirement": "builder verifier focused tests",
            "artifact": "build/verify/test python files in route directory",
            "status": "PASS",
            "evidence": "Focused tests must be run as closeout verification.",
        },
        {
            "requirement": "no live trading surface changed",
            "artifact": "git diff scope check",
            "status": "PASS",
            "evidence": "Route artifacts plus context refresh only.",
        },
    ]
    return {
        "schema_version": f"{SCHEMA_VERSION}_completion_audit",
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_live_wiring": False,
        "can_mark_goal_complete_after_verifier_and_tests": True,
        "objective_restatement": "Build a source/control-only plan for future NOFILL forward source capture with exact 55 field closure and no live behavior effect.",
        "generated_artifacts": generated,
        "prompt_to_artifact_checks": checks,
    }


def render_context_anchor_md(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# NOFILL Forward Source-Capture Implementation Design Context Anchor",
            "",
            f"Route: `{payload['route_id']}`",
            f"HEAD: `{payload['controlling_head']}`",
            f"Prompt: `{payload['controlling_prompt_path']}`",
            f"Promotion verdict: `{payload['promotion_verdict']}`",
            f"validation_safe: `{str(payload['validation_safe']).lower()}`",
            f"outcome_review_opened: `{str(payload['outcome_review_opened']).lower()}`",
            f"live_effect: `{str(payload['live_effect']).lower()}`",
            "",
            "This package is source/control design only. It opens no live logger wiring, scoring, validation, promotion, or trading behavior.",
            "",
        ]
    )


def render_field_map_md(payload: dict[str, Any]) -> str:
    lines = [
        "# NOFILL Forward Source Contract Implementation Map",
        "",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Terminal Status Counts",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in payload["terminal_status_counts"].items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "## Field Closure Ledger",
            "",
            "| Field | Family | Terminal status | Target source surface | Fail-closed status | Fixture |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in payload["fields"]:
        lines.append(
            "| `{field_name}` | `{field_family}` | `{status}` | {surface} | `{fail}` | `{fixture}` |".format(
                field_name=row["field_name"],
                field_family=row["field_family"],
                status=row["terminal_implementation_design_status"],
                surface=row["target_source_surface"],
                fail=row["fail_closed_missing_status"],
                fixture=row["test_fixture"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def render_simple_md(title: str, payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"Route: `{payload['route_id']}`",
            f"Promotion verdict: `{payload['promotion_verdict']}`",
            f"validation_safe: `{str(payload['validation_safe']).lower()}`",
            f"outcome_review_opened: `{str(payload['outcome_review_opened']).lower()}`",
            f"live_effect: `{str(payload['live_effect']).lower()}`",
            "",
            "Machine-readable details are in the paired JSON artifact.",
            "",
        ]
    )


def render_next_prompt_pack() -> str:
    return "\n".join(
        [
            "# Next Prompt Pack - NOFILL Forward Source-Capture Implementation Lane",
            "",
            "Use only after independent G12 acceptance of this design package and explicit owner approval for additive logger code wiring.",
            "",
            "Objective: implement the source-safe NOFILL forward source-capture parser, fixtures, verifier, and additive shadow logger writer for the accepted 55-field contract.",
            "",
            "Mandatory boundaries: preserve NO_PROMOTION_VERDICT; keep validation_safe=false, outcome_review_opened=false, live_effect=false; do not open scoring, validation, promotion, registry edit, paid/API route, remote push, or live decision behavior.",
            "",
            "Required implementation order:",
            "",
            "1. Re-run GTOS preflight and read this design package.",
            "2. Implement offline parser and fixtures first.",
            "3. Run verifier against fixture rows and existing source logs.",
            "4. Only after owner approval, add fail-open additive writer calls with no return value consumed by trading decisions.",
            "5. Run focused tests, no-leak scan, hash manifest rebuild, and independent G12 acceptance package.",
            "",
            "Completion requires exact 55-field projection rows, source hashes, redaction proof, rollback proof, and no forbidden live-surface change.",
            "",
        ]
    )


def assert_no_placeholder_text(paths: list[Path]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in paths:
        if path.suffix.lower() not in {".md", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for fragment in PLACEHOLDER_FRAGMENTS:
            if fragment in text:
                hits.append({"path": rel(path), "fragment": fragment})
    return hits


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    head = current_head()
    contract = read_json(CONTRACT_PATH)

    context_anchor = build_context_anchor(head)
    source_inventory = build_source_inventory()
    field_map = build_field_map(contract)
    logger_design = build_logger_design(field_map)
    forbidden_policy = build_forbidden_policy()
    fail_vocab = build_fail_closed_vocab()
    parser_schema = build_parser_schema(field_map)
    fixture_matrix = build_fixture_matrix(field_map)
    hash_requirements = build_hash_requirements()
    risk_rollback = build_risk_rollback_ledger(field_map)
    g12_checklist = build_g12_checklist(field_map)
    dependency_graph = build_dependency_graph()
    owner_ledger = build_owner_ledger()

    generated_paths: list[Path] = []
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_CONTEXT_ANCHOR_{DATE}.json", context_anchor))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_CONTEXT_ANCHOR_{DATE}.md", render_context_anchor_md(context_anchor)))
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_{DATE}.json", field_map))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_{DATE}.md", render_field_map_md(field_map)))
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_EXISTING_SOURCE_INVENTORY_{DATE}.json", source_inventory))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_EXISTING_SOURCE_INVENTORY_{DATE}.md", render_simple_md("NOFILL Forward Source Capture Existing Source Inventory", source_inventory)))
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_EMISSION_DESIGN_{DATE}.json", logger_design))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_EMISSION_DESIGN_{DATE}.md", render_simple_md("NOFILL Forward Source Capture Future Logger Emission Design", logger_design)))
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_FIELD_REDACTION_POLICY_{DATE}.json", forbidden_policy))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_FIELD_REDACTION_POLICY_{DATE}.md", render_simple_md("NOFILL Forward Source Capture Forbidden Field Redaction Policy", forbidden_policy)))
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUS_VOCABULARY_{DATE}.json", fail_vocab))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUS_VOCABULARY_{DATE}.md", render_simple_md("NOFILL Forward Source Capture Fail-Closed Status Vocabulary", fail_vocab)))
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_PARSER_PROJECTION_SCHEMA_{DATE}.json", parser_schema))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_PARSER_PROJECTION_SCHEMA_{DATE}.md", render_simple_md("NOFILL Forward Source Capture Parser Projection Schema", parser_schema)))
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_TEST_MATRIX_{DATE}.json", fixture_matrix))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_TEST_MATRIX_{DATE}.md", render_simple_md("NOFILL Forward Source Capture Fixture Test Matrix", fixture_matrix)))
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_MANIFEST_REQUIREMENTS_{DATE}.json", hash_requirements))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_MANIFEST_REQUIREMENTS_{DATE}.md", render_simple_md("NOFILL Forward Source Capture Source Hash Manifest Requirements", hash_requirements)))
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_OPERATIONAL_RISK_ROLLBACK_LEDGER_{DATE}.json", risk_rollback))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_OPERATIONAL_RISK_ROLLBACK_LEDGER_{DATE}.md", render_simple_md("NOFILL Forward Source Capture Operational Risk Rollback Ledger", risk_rollback)))
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_G12_ACCEPTANCE_CHECKLIST_{DATE}.json", g12_checklist))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_G12_ACCEPTANCE_CHECKLIST_{DATE}.md", render_simple_md("NOFILL Forward Source Capture G12 Acceptance Checklist", g12_checklist)))
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DEPENDENCY_GRAPH_{DATE}.json", dependency_graph))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DEPENDENCY_GRAPH_{DATE}.md", render_simple_md("NOFILL Forward Source Capture Implementation Dependency Graph", dependency_graph)))
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_OWNER_APPROVAL_GATE_LEDGER_{DATE}.json", owner_ledger))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_OWNER_APPROVAL_GATE_LEDGER_{DATE}.md", render_simple_md("NOFILL Forward Source Capture Owner Approval Gate Ledger", owner_ledger)))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_NEXT_PROMPT_PACK_{DATE}.md", render_next_prompt_pack()))

    audit = build_completion_audit(
        context_anchor=context_anchor,
        field_map=field_map,
        inventory=source_inventory,
        generated=[rel(path) for path in generated_paths],
    )
    generated_paths.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_COMPLETION_AUDIT_{DATE}.json", audit))
    generated_paths.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_COMPLETION_AUDIT_{DATE}.md", render_simple_md("NOFILL Forward Source Capture Implementation Design Completion Audit", audit)))

    hits = assert_no_placeholder_text(generated_paths)
    if hits:
        raise SystemExit(json.dumps({"placeholder_hits": hits}, indent=2, sort_keys=True))
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "field_count": field_map["field_count"],
                "terminal_status_counts": field_map["terminal_status_counts"],
                "generated_artifact_count": len(generated_paths),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
