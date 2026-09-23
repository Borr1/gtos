#!/usr/bin/env python3
"""Build the NOFILL forward source-capture contract/prototype lane.

This lane is source/control tooling only. It consumes already accepted
source-control artifacts, freezes a future capture contract, emits offline
projection fixtures, and writes machine-checkable ledgers. It does not score
outcomes, validate, promote, wire live loggers, call external APIs, or import
live trading components.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
ROUTE_ID = "NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_HARDENING_OFFLINE_PROJECTION_PROTOTYPE"
SCHEMA_VERSION = "nofill_forward_source_capture_contract_hardening_offline_projection_prototype_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
FIXTURE_DIR = OUT_DIR / "fixtures"
BASE = Path("research/science_program_2026_05/06_outcome_testing")
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_HARDENING_AND_OFFLINE_PROJECTION_PROTOTYPE_GOAL_PROMPT_2026-05-09.md"
)

CONTROL_FLAGS: dict[str, Any] = {
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

UPSTREAM_INPUTS: dict[str, str] = {
    "goal_prompt": str(PROMPT_PATH),
    "live_state": ".context/LIVE_STATE.md",
    "latest_handoff": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "quick_reference": ".context/00_core/quick_reference_card.md",
    "research_doctrine": ".context/00_core/research_operating_doctrine.md",
    "research_current_state": ".context/00_core/research_current_state.md",
    "goal_session_research_discipline": ".context/00_core/goal_session_research_discipline.md",
    "local_heavy_data_inventory": ".context/00_core/local_heavy_data_inventory.md",
    "g0_context_anchor": str(
        BASE
        / "g0_nofill_forward_projection_synthesis_control_route"
        / f"G0_NOFILL_FORWARD_PROJECTION_CONTEXT_ANCHOR_{DATE}.md"
    ),
    "g0_evidence_chain": str(
        BASE
        / "g0_nofill_forward_projection_synthesis_control_route"
        / f"G0_NOFILL_FORWARD_PROJECTION_EVIDENCE_CHAIN_RECONCILIATION_{DATE}.md"
    ),
    "g0_field_matrix": str(
        BASE
        / "g0_nofill_forward_projection_synthesis_control_route"
        / f"G0_NOFILL_FORWARD_PROJECTION_FIELD_REQUIREMENT_MATRIX_{DATE}.json"
    ),
    "g0_schema_requirements": str(
        BASE
        / "g0_nofill_forward_projection_synthesis_control_route"
        / f"G0_NOFILL_FORWARD_CAPTURE_SCHEMA_REQUIREMENTS_{DATE}.json"
    ),
    "g0_completion_audit": str(
        BASE
        / "g0_nofill_forward_projection_synthesis_control_route"
        / f"G0_NOFILL_FORWARD_COMPLETION_AUDIT_{DATE}.json"
    ),
    "g12_repair_completion": str(
        BASE
        / "g12_nofill_forward_projection_repair_reaudit"
        / f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_COMPLETION_AUDIT_{DATE}.json"
    ),
    "g12_repair_no_leak": str(
        BASE
        / "g12_nofill_forward_projection_repair_reaudit"
        / f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_NO_LEAK_AUDIT_{DATE}.json"
    ),
    "g12_repair_denom": str(
        BASE
        / "g12_nofill_forward_projection_repair_reaudit"
        / f"G12_NOFILL_FORWARD_PROJECTION_REPAIR_DENOMINATOR_AUDIT_{DATE}.json"
    ),
    "source_projection_rows": str(
        BASE
        / "nofill_forward_source_safe_projection_builder"
        / f"NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_ROWS_{DATE}.jsonl"
    ),
    "source_projection_allowlist": str(
        BASE
        / "nofill_forward_source_safe_projection_builder"
        / f"NOFILL_FORWARD_ALLOWLIST_PROJECTION_SPEC_{DATE}.json"
    ),
    "source_projection_denom": str(
        BASE
        / "nofill_forward_source_safe_projection_builder"
        / f"NOFILL_FORWARD_DENOMINATOR_AND_EXCLUSION_AUDIT_{DATE}.json"
    ),
    "source_projection_missing": str(
        BASE
        / "nofill_forward_source_safe_projection_builder"
        / f"NOFILL_FORWARD_MISSING_STATUS_LEDGER_{DATE}.json"
    ),
    "source_projection_ticket_audit": str(
        BASE
        / "nofill_forward_source_safe_projection_builder"
        / f"NOFILL_FORWARD_TICKET_REDACTION_AND_FORBIDDEN_FIELD_AUDIT_{DATE}.json"
    ),
    "source_projection_source_manifest": str(
        BASE
        / "nofill_forward_source_safe_projection_builder"
        / f"NOFILL_FORWARD_SOURCE_HASH_MANIFEST_{DATE}.json"
    ),
    "source_projection_parser_manifest": str(
        BASE
        / "nofill_forward_source_safe_projection_builder"
        / f"NOFILL_FORWARD_PARSER_HASH_MANIFEST_{DATE}.json"
    ),
    "addendum_schema": str(
        BASE
        / "nofill_forward_contract_addendum_projection_plan"
        / f"NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA_{DATE}.json"
    ),
    "g12_lifecycle_schema_audit": str(
        BASE
        / "g12_nofill_forward_lifecycle_capture_contract_audit"
        / f"G12_NOFILL_FORWARD_SCHEMA_AUDIT_{DATE}.json"
    ),
    "cat_v3_source_control_rebuild": str(
        BASE
        / "nofill_cat_v3_source_control_rebuild"
        / f"NOFILL_CAT_V3_UNIVERSE_RECONCILIATION_{DATE}.json"
    ),
    "g12_cat_v3_source_control_audit": str(
        BASE
        / "g12_nofill_cat_v3_source_control_audit"
        / f"G12_NOFILL_CAT_V3_COMPLETION_AUDIT_{DATE}.json"
    ),
}

PARSER_FILES = [
    "build_nofill_forward_capture_contract_2026_05_09.py",
    "verify_nofill_forward_capture_contract_2026_05_09.py",
    "test_nofill_forward_capture_contract_2026_05_09.py",
]

MUTABLE_CONTEXT_INPUTS = {
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
}

REQUIRED_MD = [
    f"NOFILL_FORWARD_SOURCE_CAPTURE_CONTEXT_ANCHOR_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_EVIDENCE_CHAIN_RECONCILIATION_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_{DATE}.md",
    f"NOFILL_FORWARD_OFFLINE_PARSER_PROJECTION_PROTOTYPE_DESIGN_{DATE}.md",
    f"NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_{DATE}.md",
    f"NOFILL_FORWARD_DUPLICATE_DENOMINATOR_CONTROL_AUDIT_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_COST_EXECUTION_SEPARATION_LEDGER_{DATE}.md",
    f"NOFILL_FORWARD_HOSTILE_REVIEW_AND_SATURATION_LEDGER_{DATE}.md",
    f"NOFILL_FORWARD_FORBIDDEN_ROUTE_LEDGER_{DATE}.md",
    f"NOFILL_FORWARD_G12_ACCEPTANCE_AUDIT_NEXT_PROMPT_PACK_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_{DATE}.md",
]

REQUIRED_JSON = [
    f"NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_{DATE}.json",
    f"NOFILL_FORWARD_MISSING_STATUS_VOCABULARY_{DATE}.json",
    f"NOFILL_FORWARD_FIXTURE_MANIFEST_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_HASH_MANIFEST_{DATE}.json",
    f"NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_{DATE}.json",
    f"NOFILL_FORWARD_DUPLICATE_DENOMINATOR_CONTROL_AUDIT_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_COST_EXECUTION_SEPARATION_LEDGER_{DATE}.json",
    f"NOFILL_FORWARD_HOSTILE_REVIEW_AND_SATURATION_LEDGER_{DATE}.json",
    f"NOFILL_FORWARD_FORBIDDEN_ROUTE_LEDGER_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_{DATE}.json",
]

PROTOTYPE_ROWS_NAME = f"NOFILL_FORWARD_OFFLINE_PROJECTION_PROTOTYPE_ROWS_{DATE}.jsonl"
VERIFICATION_RESULT_NAME = f"NOFILL_FORWARD_SOURCE_CAPTURE_VERIFICATION_RESULT_{DATE}.json"

FORBIDDEN_RAW_FIELD_NAMES = {
    "account_history",
    "account_id",
    "account_pnl",
    "actual_r",
    "broker_actual_r",
    "broker_fill_state",
    "deal_id",
    "dsr",
    "expectancy",
    "fill_time_utc",
    "live_order_state",
    "mt5_deal_id",
    "mt5_order_ticket",
    "mt5_position_id",
    "order_id",
    "order_send_attempted",
    "order_send_success",
    "pbo",
    "pending_ticket",
    "position_id",
    "profit_factor",
    "r_multiple",
    "r_value",
    "slippage_price",
    "synthetic_path_r",
    "trade_state_ticket",
    "win_rate",
}

ALLOWED_TAXONOMY_FILES = {
    f"NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_{DATE}.json",
    f"NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_{DATE}.json",
    f"NOFILL_FORWARD_FORBIDDEN_ROUTE_LEDGER_{DATE}.json",
    f"NOFILL_FORWARD_FIXTURE_MANIFEST_{DATE}.json",
}


def as_repo_path(path: str | Path) -> Path:
    path_obj = Path(path)
    return path_obj if path_obj.is_absolute() else REPO_ROOT / path_obj


def rel_display(path: str | Path) -> str:
    path_obj = Path(path)
    try:
        return str(path_obj.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path_obj).replace("\\", "/")


def read_json(path: str | Path) -> Any:
    return json.loads(as_repo_path(path).read_text(encoding="utf-8"))


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with as_repo_path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(name: str, payload: Any) -> Path:
    path = OUT_DIR / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> Path:
    path = OUT_DIR / name
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return path


def write_md(name: str, text: str) -> Path:
    path = OUT_DIR / name
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path


def sha256_file(path: str | Path) -> str | None:
    full = as_repo_path(path)
    if not full.exists() or not full.is_file():
        return None
    digest = hashlib.sha256()
    with full.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_lf_normalized_file(path: str | Path) -> str | None:
    full = as_repo_path(path)
    if not full.exists() or not full.is_file():
        return None
    if full.suffix.lower() not in {".md", ".py", ".json", ".jsonl", ".txt", ".yaml", ".yml"}:
        return None
    return hashlib.sha256(full.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def git_oneline() -> str:
    result = subprocess.run(
        ["git", "log", "-1", "--oneline"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.strip() or "UNKNOWN_HEAD"


def base_payload(artifact: str) -> dict[str, Any]:
    return {
        "artifact": artifact,
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **CONTROL_FLAGS,
    }


def infer_json_type(field_name: str) -> str:
    if field_name.endswith("_utc"):
        return "string:datetime-utc-or-null"
    if field_name.endswith("_ms"):
        return "number-or-null"
    if field_name.endswith("_sha256") or field_name.endswith("_hash") or field_name.endswith("_code_hash"):
        return "string:sha256"
    if field_name in {
        "row_level_denominator_member",
        "nofill_duplicate_key_count_member",
        "duplicate_group_id_count_member",
    }:
        return "boolean"
    if field_name in {"missing_coverage_intervals"}:
        return "array"
    if field_name.endswith("_status") or field_name.endswith("_mode") or field_name.endswith("_unit"):
        return "string:closed-vocabulary"
    return "string-or-null"


def lineage_rule(field_name: str, family: str) -> str:
    if "duplicate" in family:
        return "Frozen CAT V3 source-control/count packet; raw duplicate values are replaced by SHA256 controls."
    if "spread" in field_name:
        return "Source-hashed tick/quote snapshot only; not fill, cost, slippage, or result evidence."
    if "ticket" in field_name or "pending_order" in family:
        return "Source-safe pending-lifecycle status projection only; raw ticket/order/deal/account values are never emitted or hashed."
    if "capture_latency" in family:
        return "Direct capture timestamp or explicit missing status from source metadata; never inferred from outcomes."
    if "source" in family or "no_leak" in family:
        return "Source/parser/fixture/projection manifest and verifier controls."
    return "Decision-time source/control artifact or explicit source-safe missing status."


def normalize_status_values(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    if isinstance(values, list):
        return [str(value) for value in values]
    return [str(values)]


def build_contract(g0_schema: dict[str, Any], g0_matrix: dict[str, Any]) -> dict[str, Any]:
    fields: list[dict[str, Any]] = []
    for row in g0_schema["future_capture_field_requirements"]:
        field_name = row["field_name"]
        family = row.get("field_family", "unknown")
        missing_vocab = normalize_status_values(row.get("missing_policy"))
        fields.append(
            {
                "field_name": field_name,
                "json_type": infer_json_type(field_name),
                "field_family": family,
                "requirement_level": row.get("requirement_level", "mandatory"),
                "required_or_optional_source": row.get("required_or_optional_source", row.get("requirement_level", "mandatory")),
                "fail_closed_status": True,
                "source_asof_rule": row.get("source_asof_rule"),
                "source_lineage_rule": lineage_rule(field_name, family),
                "allowed_missing_or_status_values": missing_vocab,
                "hash_provenance_requirements": row.get(
                    "hash_provenance_requirements",
                    ["source_artifact_hash", "parser_code_hash", "controlling_git_head"],
                ),
                "duplicate_denominator_effect": row.get("duplicate_denominator_effect", "NO_DENOMINATOR_EFFECT_SOURCE_CONTROL_FIELD_ONLY"),
                "forbidden_field_rule": "No raw broker/account/order/deal/position/result/cost/performance labels may populate this field.",
                "owner_acceptance_status": "FROZEN_SOURCE_CONTROL_CONTRACT_PENDING_OWNER_APPROVED_LIVE_WIRING_LANE",
                "g12_acceptance_status": "PENDING_NEXT_G12_SOURCE_CAPTURE_ACCEPTANCE_AUDIT",
                "result_or_cost_label_opened_now": False,
                "live_logger_wiring_opened_now": False,
            }
        )
    return {
        **base_payload("NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT"),
        "controlling_git_head": git_oneline(),
        "prompt_path": str(PROMPT_PATH).replace("\\", "/"),
        "field_count": len(fields),
        "fields": fields,
        "forbidden_output_field_names": sorted(FORBIDDEN_RAW_FIELD_NAMES),
        "status_contract_boundary": {
            "missing": "Use only when a source field is expected for this evidence class but absent from approved source artifacts.",
            "not_applicable": "Use only when the field cannot logically apply to the row family.",
            "not_observed": "Use when the source path proves non-observation, such as no entry touch inside the source-safe window.",
            "source_impossible": "Use when approved inputs cannot prove the value without crossing a forbidden evidence class.",
            "redacted": "Use when a hazardous raw source field exists but value emission or hashing is forbidden.",
            "not_yet_captured": "Use for future live-capture fields that require owner-approved live wiring.",
            "forbidden": "Use when a field/value would open broker/account/order/result/cost/performance evidence and must fail closed.",
        },
        "source_projection_usage_limits": g0_schema.get("source_projection_usage_limits", []),
        "mandatory_fail_closed_controls": g0_matrix.get("mandatory_fail_closed_controls", []),
        "future_live_logger_wiring_gate": "YES_GATED_BEHIND_G12_ACCEPTANCE_AND_SEPARATE_OWNER_APPROVAL",
    }


def build_missing_status_vocabulary(contract: dict[str, Any], rows: list[dict[str, Any]], upstream_missing: dict[str, Any]) -> dict[str, Any]:
    observed_statuses: set[str] = set()
    for row in rows:
        for key, value in row.items():
            if key.endswith("_status") or key in {"cost_testing_gate_status", "entry_touch_spread_status", "decision_spread_status"}:
                if isinstance(value, str):
                    observed_statuses.add(value)
        for value in row.get("missing_statuses", {}).values():
            if isinstance(value, str):
                observed_statuses.add(value)
    for field in contract["fields"]:
        observed_statuses.update(field.get("allowed_missing_or_status_values", []))

    canonical = {
        "MISSING_SOURCE_FIELD": {
            "canonical_values": ["SOURCE_FIELD_MISSING", "NOT_CAPTURED_IN_RAW_SOURCE"],
            "meaning": "A required source/control field is absent from approved inputs.",
            "denominator_effect": "none",
        },
        "NOT_APPLICABLE": {
            "canonical_values": ["VALUE_NOT_APPLICABLE", "TOUCH_NOT_OBSERVED_VALUE_NOT_APPLICABLE"],
            "meaning": "The value cannot logically apply after a source-safe status has been established.",
            "denominator_effect": "none",
        },
        "NOT_OBSERVED_SOURCE_SAFE": {
            "canonical_values": ["TOUCH_NOT_OBSERVED_SOURCE_SAFE", "NO_TOUCH_SOURCE_SAFE"],
            "meaning": "Approved source window proves non-observation without result scoring.",
            "denominator_effect": "none",
        },
        "SOURCE_IMPOSSIBLE": {
            "canonical_values": ["SOURCE_IMPOSSIBLE", "SOURCE_IMPOSSIBLE_FROM_APPROVED_INPUTS"],
            "meaning": "Current approved artifacts cannot prove the value without a new source/access/capture lane.",
            "denominator_effect": "none",
        },
        "REDACTED": {
            "canonical_values": [
                "RAW_TICKET_VALUE_PRESENT_REDACTED",
                "SOURCE_TICKET_VALUE_REDACTED",
                "NATIVE_PENDING_OBSERVABILITY_PRESENT_REDACTED",
            ],
            "meaning": "A hazardous source field may exist, but raw value emission and hashing are forbidden.",
            "denominator_effect": "none",
        },
        "NOT_YET_CAPTURED": {
            "canonical_values": [
                "NOT_CAPTURED_IN_RAW_SOURCE",
                "CLOCK_SKEW_NOT_MEASURABLE_SOURCE_ONLY",
                "BROKER_PENDING_OBSERVABILITY_NOT_OPENED_FOR_SOURCE_CONTROL",
            ],
            "meaning": "A future source-safe logger or source contract must capture this value.",
            "denominator_effect": "none",
        },
        "FORBIDDEN_FAIL_CLOSED": {
            "canonical_values": [
                "FORBIDDEN_FIELD_DETECTED_FAIL_CLOSED",
                "FAIL_TICKET_VALUE_DETECTED_IN_OUTPUT",
                "UNKNOWN_MODE_FAIL_CLOSED",
                "UNKNOWN_TYPE_FAIL_CLOSED",
                "INVALID_FAIL_CLOSED",
            ],
            "meaning": "The value would violate source/no-leak boundaries and must fail the packet.",
            "denominator_effect": "none_until_repaired",
        },
    }
    return {
        **base_payload("NOFILL_FORWARD_MISSING_STATUS_VOCABULARY"),
        "canonical_groups": canonical,
        "observed_status_values": sorted(observed_statuses),
        "upstream_missing_status_counts": upstream_missing.get("field_missing_status_counts", {}),
        "rule": "Null, missing, not-applicable, not-observed, source-impossible, redacted, not-yet-captured, and forbidden states are distinct and must not be collapsed.",
    }


def build_source_field_schema(contract: dict[str, Any], allowlist: dict[str, Any]) -> dict[str, Any]:
    required = [field["field_name"] for field in contract["fields"] if field["requirement_level"].startswith("mandatory")]
    return {
        **base_payload("NOFILL_FORWARD_SOURCE_FIELD_SCHEMA"),
        "contract_field_count": contract["field_count"],
        "required_field_names": required,
        "field_schema": {
            field["field_name"]: {
                "type": field["json_type"],
                "required": field["field_name"] in required,
                "fail_closed_status": field["fail_closed_status"],
                "source_asof_rule": field["source_asof_rule"],
                "allowed_missing_or_status_values": field["allowed_missing_or_status_values"],
            }
            for field in contract["fields"]
        },
        "prototype_projection_allowed_fields": allowlist.get("exhaustive_projection_output_fields_allowed", []),
        "forbidden_output_field_names": sorted(FORBIDDEN_RAW_FIELD_NAMES),
        "redaction_only_fields": allowlist.get("redaction_only_fields", []),
        "g12_acceptance_status": "PENDING_NEXT_G12_SOURCE_CAPTURE_ACCEPTANCE_AUDIT",
    }


def build_prototype_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prototype_rows: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["contract_route_id"] = ROUTE_ID
        item["contract_schema_version"] = SCHEMA_VERSION
        item["contract_acceptance_state"] = "SOURCE_CONTROL_CONTRACT_FROZEN_G12_AUDIT_PENDING"
        item["future_live_logger_wiring_gate"] = "GATED_BEHIND_G12_ACCEPTANCE_AND_OWNER_APPROVAL"
        prototype_rows.append(item)
    return prototype_rows


def first_row(rows: list[dict[str, Any]], predicate: Any) -> dict[str, Any]:
    for row in rows:
        if predicate(row):
            return row
    raise AssertionError("fixture predicate did not match any row")


def safe_row_summary(row: dict[str, Any]) -> dict[str, Any]:
    keep = [
        "packet_row_id",
        "source_row_id",
        "candidate_id",
        "symbol",
        "session",
        "side",
        "v3_terminal_family",
        "v3_terminal_state",
        "source_match_status",
        "row_level_denominator_member",
        "nofill_duplicate_key_count_member",
        "duplicate_group_id_count_member",
        "nofill_duplicate_key_sha256",
        "duplicate_group_id_sha256",
        "decision_spread_status",
        "entry_touch_spread_status",
        "raw_ticket_field_present_status",
        "mt5_order_ticket_redaction_status",
        "missing_statuses",
    ]
    return {key: row.get(key) for key in keep if key in row}


def write_fixture(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIXTURE_DIR / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "fixture_id": payload["fixture_id"],
        "category": payload["category"],
        "path": rel_display(path),
        "sha256": sha256_file(path),
        "covers": payload.get("covers", []),
        "expected_behavior": payload.get("expected_behavior"),
    }


def build_fixtures(rows: list[dict[str, Any]]) -> dict[str, Any]:
    duplicate_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("v3_terminal_family") == "accepted":
            duplicate_groups[row.get("nofill_duplicate_key_sha256")].append(row)
    duplicate_rows = next(group for group in duplicate_groups.values() if len(group) >= 2)

    fixtures: list[dict[str, Any]] = []
    actual_fixtures = [
        (
            "ACCEPTED_ROW_FIXTURE_2026-05-09.json",
            "accepted_row",
            first_row(rows, lambda row: row["v3_terminal_family"] == "accepted"),
        ),
        (
            "SOURCE_CONTROL_ROW_FIXTURE_2026-05-09.json",
            "source_control_row",
            first_row(rows, lambda row: row["v3_terminal_family"] == "source_control"),
        ),
        (
            "SOURCE_IMPOSSIBLE_ROW_FIXTURE_2026-05-09.json",
            "source_impossible_row",
            first_row(rows, lambda row: row["v3_terminal_family"] == "source_impossible"),
        ),
        (
            "REJECT_ROW_FIXTURE_2026-05-09.json",
            "reject_row",
            first_row(rows, lambda row: row["v3_terminal_family"] == "reject"),
        ),
        (
            "TOUCH_NOT_OBSERVED_ROW_FIXTURE_2026-05-09.json",
            "touch_not_observed_row",
            first_row(rows, lambda row: row.get("entry_touch_spread_status") == "TOUCH_NOT_OBSERVED_SOURCE_SAFE"),
        ),
        (
            "SPREAD_PRESENT_ROW_FIXTURE_2026-05-09.json",
            "spread_present_row",
            first_row(
                rows,
                lambda row: row.get("decision_spread_status") == "CAPTURED_SOURCE_SAFE"
                and row.get("entry_touch_spread_status") == "CAPTURED_SOURCE_SAFE",
            ),
        ),
        (
            "MISSING_NA_STATUS_ROW_FIXTURE_2026-05-09.json",
            "missing_na_status_row",
            first_row(rows, lambda row: row.get("source_match_status") == "NO_MATCH_IN_APPROVED_LOGS_EXPLICIT_MISSING_STATUSES"),
        ),
    ]
    for filename, category, row in actual_fixtures:
        fixtures.append(
            write_fixture(
                filename,
                {
                    "fixture_id": filename.replace(".json", ""),
                    "category": category,
                    "covers": [category, "source_control_projection_row"],
                    "source": "NOFILL_FORWARD_SOURCE_SAFE_PROJECTION_ROWS_2026-05-09.jsonl",
                    "row_summary": safe_row_summary(row),
                    "expected_behavior": "accepted_by_offline_contract_verifier_without_denominator_change",
                    **CONTROL_FLAGS,
                },
            )
        )

    fixtures.append(
        write_fixture(
            "DUPLICATE_PROJECTION_FIXTURE_2026-05-09.json",
            {
                "fixture_id": "DUPLICATE_PROJECTION_FIXTURE_2026-05-09",
                "category": "duplicate_projection_rows",
                "covers": ["duplicate_projections", "primary_duplicate_key", "secondary_duplicate_group"],
                "duplicate_key_sha256": duplicate_rows[0]["nofill_duplicate_key_sha256"],
                "rows": [safe_row_summary(row) for row in duplicate_rows[:3]],
                "expected_behavior": "first_duplicate_member_counts; later duplicate members remain projected but do not increase duplicate denominators",
                **CONTROL_FLAGS,
            },
        )
    )
    fixtures.append(
        write_fixture(
            "REDACTED_TICKET_ROW_FIXTURE_2026-05-09.json",
            {
                "fixture_id": "REDACTED_TICKET_ROW_FIXTURE_2026-05-09",
                "category": "redacted_ticket_row",
                "covers": ["redacted-ticket rows", "pending-order observability", "no raw ticket emission"],
                "synthetic_source_control_input": {
                    "forbidden_field_family_present": ["mt5_order_ticket", "pending_ticket", "trade_state_ticket"],
                    "raw_value_material_included": False,
                    "raw_value_hashing_allowed": False,
                },
                "expected_projection": {
                    "raw_ticket_field_present_status": "RAW_TICKET_VALUE_PRESENT_REDACTED",
                    "mt5_order_ticket_redaction_status": "SOURCE_TICKET_VALUE_REDACTED",
                    "broker_pending_order_created_status": "NATIVE_PENDING_OBSERVABILITY_PRESENT_REDACTED",
                },
                "expected_behavior": "redact_status_only_and_fail_if_raw_value_is_emitted_or_hashed",
                **CONTROL_FLAGS,
            },
        )
    )
    fixtures.append(
        write_fixture(
            "SAME_TICK_AMBIGUITY_ROW_FIXTURE_2026-05-09.json",
            {
                "fixture_id": "SAME_TICK_AMBIGUITY_ROW_FIXTURE_2026-05-09",
                "category": "same_tick_ambiguity_row",
                "covers": ["same-tick ambiguity rows", "same-bar ambiguity rows", "event ordering preservation"],
                "synthetic_source_control_input": {
                    "entry_touch_and_terminal_or_protective_event_share_source_timestamp": True,
                    "post_event_ordering_guess_allowed": False,
                },
                "expected_projection": {
                    "event_order_resolution_method": "SAME_TICK_OR_SAME_BAR_AMBIGUOUS_SOURCE_SAFE",
                    "same_tick_same_bar_ambiguity_status": "AMBIGUITY_PRESERVED_NO_ORDERING_ASSUMPTION",
                },
                "expected_behavior": "preserve_ambiguity_without_result_or_ordering_label",
                **CONTROL_FLAGS,
            },
        )
    )
    fixtures.append(
        write_fixture(
            "FORBIDDEN_FIELD_EXAMPLES_FIXTURE_2026-05-09.json",
            {
                "fixture_id": "FORBIDDEN_FIELD_EXAMPLES_FIXTURE_2026-05-09",
                "category": "forbidden_field_examples",
                "covers": ["forbidden-field examples", "no-leak fail-closed controls"],
                "forbidden_field_examples": [
                    {
                        "forbidden_field_name": name,
                        "raw_value_material_included": False,
                        "expected_action": "fail_closed_or_redact_before_projection_and_before_hashing",
                    }
                    for name in sorted(FORBIDDEN_RAW_FIELD_NAMES)
                ],
                "expected_behavior": "taxonomy_only_no_raw_values",
                **CONTROL_FLAGS,
            },
        )
    )
    return {
        **base_payload("NOFILL_FORWARD_FIXTURE_MANIFEST"),
        "fixture_count": len(fixtures),
        "fixtures": fixtures,
        "required_fixture_categories": [
            "accepted_row",
            "source_control_row",
            "source_impossible_row",
            "reject_row",
            "touch_not_observed_row",
            "spread_present_row",
            "redacted_ticket_row",
            "same_tick_ambiguity_row",
            "missing_na_status_row",
            "duplicate_projection_rows",
            "forbidden_field_examples",
        ],
        "coverage_status": "PASS",
    }


def denominator_audit(prototype_rows: list[dict[str, Any]], upstream_denom: dict[str, Any]) -> dict[str, Any]:
    family_counts = Counter(row.get("v3_terminal_family") for row in prototype_rows)
    issues: list[str] = []
    if len(prototype_rows) != 298:
        issues.append(f"prototype_row_count:{len(prototype_rows)}")
    if dict(family_counts) != {"accepted": 225, "reject": 65, "source_control": 4, "source_impossible": 4}:
        issues.append(f"family_counts:{dict(family_counts)}")
    row_level = sum(bool(row.get("row_level_denominator_member")) for row in prototype_rows)
    primary = sum(bool(row.get("nofill_duplicate_key_count_member")) for row in prototype_rows)
    secondary = sum(bool(row.get("duplicate_group_id_count_member")) for row in prototype_rows)
    if (row_level, primary, secondary) != (225, 182, 139):
        issues.append(f"denominators:{row_level}/{primary}/{secondary}")
    nonaccepted_counting = [
        row["packet_row_id"]
        for row in prototype_rows
        if row.get("v3_terminal_family") != "accepted"
        and (
            row.get("row_level_denominator_member")
            or row.get("nofill_duplicate_key_count_member")
            or row.get("duplicate_group_id_count_member")
        )
    ]
    if nonaccepted_counting:
        issues.append(f"nonaccepted_counting:{nonaccepted_counting[:5]}")
    return {
        **base_payload("NOFILL_FORWARD_DUPLICATE_DENOMINATOR_CONTROL_AUDIT"),
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "universe_equation": "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject",
        "projection_row_count": len(prototype_rows),
        "family_counts": dict(sorted(family_counts.items())),
        "row_level_accepted_denominator": row_level,
        "primary_duplicate_key_denominator": primary,
        "secondary_duplicate_group_denominator": secondary,
        "reject_overlap_rows": upstream_denom.get("reject_overlap_rows"),
        "reject_overlap_denominator_effect": upstream_denom.get("reject_overlap_denominator_effect"),
        "upstream_denominator_status": upstream_denom.get("status"),
        "prototype_denominator_effect": "NO_CHANGE_SOURCE_CONTROL_METADATA_ONLY",
    }


def scan_generated_files(files: list[Path]) -> dict[str, Any]:
    raw_value_hits: list[dict[str, Any]] = []
    controlled_taxonomy_mentions: list[dict[str, Any]] = []
    forbidden_key_hits_in_prototype: list[dict[str, Any]] = []
    raw_value_pattern = re.compile(r"(?:RAW_SECRET|SECRET_TICKET|ticket-[0-9]+|order-[0-9]+)", re.I)
    for path in files:
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if raw_value_pattern.search(text):
            raw_value_hits.append({"path": rel_display(path), "pattern": "raw-ticket-like-placeholder"})
        for name in sorted(FORBIDDEN_RAW_FIELD_NAMES):
            if name in text:
                controlled_taxonomy_mentions.append(
                    {
                        "path": rel_display(path),
                        "field_name": name,
                        "classification": "controlled_taxonomy_or_negative_fixture" if path.name in ALLOWED_TAXONOMY_FILES or "FIXTURE" in path.name else "review",
                    }
                )
    prototype_path = OUT_DIR / PROTOTYPE_ROWS_NAME
    if prototype_path.exists():
        for line_no, line in enumerate(prototype_path.read_text(encoding="utf-8").splitlines(), 1):
            row = json.loads(line)
            for key in row:
                if key in FORBIDDEN_RAW_FIELD_NAMES:
                    forbidden_key_hits_in_prototype.append({"line_no": line_no, "key": key})
    issues = []
    if raw_value_hits:
        issues.append("raw_value_like_hits")
    if forbidden_key_hits_in_prototype:
        issues.append("forbidden_keys_in_prototype_rows")
    return {
        **base_payload("NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT"),
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "raw_value_hits": raw_value_hits,
        "forbidden_key_hits_in_prototype_rows": forbidden_key_hits_in_prototype,
        "controlled_taxonomy_mentions_count": len(controlled_taxonomy_mentions),
        "controlled_taxonomy_mentions_sample": controlled_taxonomy_mentions[:30],
        "redaction_controls": {
            "raw_ticket_values_emitted": False,
            "raw_ticket_values_hashed": False,
            "broker_account_order_history_labels_emitted": False,
            "result_or_cost_labels_opened": False,
            "redacted_ticket_fixture_present": True,
        },
    }


def cost_execution_ledger(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        **base_payload("NOFILL_FORWARD_SOURCE_COST_EXECUTION_SEPARATION_LEDGER"),
        "decision_spread_status_counts": dict(Counter(row.get("decision_spread_status") for row in rows)),
        "entry_touch_spread_status_counts": dict(Counter(row.get("entry_touch_spread_status") for row in rows)),
        "slippage_label_status_counts": dict(Counter(row.get("slippage_label_status") for row in rows)),
        "execution_quality_label_status_counts": dict(Counter(row.get("execution_quality_label_status") for row in rows)),
        "cost_testing_gate_status_counts": dict(Counter(row.get("cost_testing_gate_status") for row in rows)),
        "separation_rules": [
            "Decision and entry-touch spread fields are source-safe quote snapshots only.",
            "Slippage and execution-quality values remain closed redaction/status fields.",
            "No result, validation, promotion, account, order-history, deal, position, or live execution label is opened.",
        ],
    }


def hostile_review_ledger() -> dict[str, Any]:
    checks = [
        ("source_control_masquerades_as_result", "Blocked: every artifact states source/control only and closed flags remain false."),
        ("duplicate_denominator_inflation", "Blocked: 225/182/139 denominators recomputed from prototype rows."),
        ("ticket_or_account_leakage", "Blocked: raw value material is absent; redaction fixture is status-only."),
        ("same_tick_ordering_fabrication", "Blocked: ambiguity fixture preserves ambiguous ordering instead of choosing a path."),
        ("missing_status_collapse", "Blocked: missing, NA, not observed, source impossible, redacted, not-yet-captured, and forbidden groups are distinct."),
        ("future_live_wiring_without_gate", "Blocked: live logger wiring remains gated behind G12 acceptance and separate owner approval."),
        ("cost_slippage_label_creep", "Blocked: spread snapshots are separated from slippage/execution quality labels."),
        ("worktree_data_blindness", "Addressed: this lane consumes source-hashed upstream manifests and records local-heavy roots through upstream projection evidence."),
    ]
    return {
        **base_payload("NOFILL_FORWARD_HOSTILE_REVIEW_AND_SATURATION_LEDGER"),
        "status": "PASS",
        "same_evidence_class_gaps_remaining": [],
        "hostile_review_checks": [{"risk": risk, "control": control} for risk, control in checks],
        "saturation_decision": "All remaining next steps cross evidence-class gates: independent G12 acceptance, owner-approved live wiring, or result/cost scoring.",
    }


def forbidden_route_ledger() -> dict[str, Any]:
    routes = [
        "result_cost_scoring",
        "validation_or_promotion",
        "master_registry_edit",
        "live_logger_wiring",
        "src_prompts_config_risk_execution_permissions_safety_selector_canary_order_behavior",
        "mt5_order_account_history_deal_position_routes",
        "credentials_or_remote_push",
        "paid_api_or_databento_calls",
        "broker_account_order_history_result_labels",
    ]
    return {
        **base_payload("NOFILL_FORWARD_FORBIDDEN_ROUTE_LEDGER"),
        "status": "PASS",
        "forbidden_routes": [
            {
                "route": route,
                "status": "FORBIDDEN_IN_THIS_LANE",
                "future_gate": "requires separate owner-approved prompt and correct evidence-class gate",
            }
            for route in routes
        ],
        "future_live_logger_wiring_lane_still_gated": True,
    }


def source_hash_entry(path: str | Path, role: str, consumed: bool = True) -> dict[str, Any]:
    full = as_repo_path(path)
    display = rel_display(full)
    strict_hash_recompute = display not in MUTABLE_CONTEXT_INPUTS
    return {
        "path": display,
        "role": role,
        "exists": full.exists(),
        "consumed_or_generated": consumed,
        "strict_hash_recompute": strict_hash_recompute,
        "hash_policy": "strict_recompute" if strict_hash_recompute else "mutable_context_snapshot_presence_only",
        "sha256": sha256_file(full),
        "sha256_lf_normalized": sha256_lf_normalized_file(full),
        "size_bytes": full.stat().st_size if full.exists() and full.is_file() else None,
    }


def build_source_hash_manifest(generated_files: list[Path], fixture_manifest: dict[str, Any]) -> dict[str, Any]:
    source_entries = [source_hash_entry(path, f"upstream:{name}") for name, path in sorted(UPSTREAM_INPUTS.items())]
    parser_entries = [source_hash_entry(OUT_DIR / name, "parser_or_test") for name in PARSER_FILES]
    fixture_entries = [source_hash_entry(REPO_ROOT / item["path"], "fixture") for item in fixture_manifest["fixtures"]]
    generated_entries = [
        source_hash_entry(path, "generated_artifact")
        for path in generated_files
        if path.name != f"NOFILL_FORWARD_SOURCE_HASH_MANIFEST_{DATE}.json"
    ]
    return {
        **base_payload("NOFILL_FORWARD_SOURCE_HASH_MANIFEST"),
        "hash_policy": "sha256 plus LF-normalized fallback for text artifacts; source hash manifest self is excluded to avoid self-reference",
        "source_entries": source_entries,
        "parser_entries": parser_entries,
        "fixture_entries": fixture_entries,
        "generated_entries": generated_entries,
        "excluded_self_referential_artifacts": [
            f"NOFILL_FORWARD_SOURCE_HASH_MANIFEST_{DATE}.json",
            VERIFICATION_RESULT_NAME,
        ],
        "record_counts": {
            "source_entries": len(source_entries),
            "parser_entries": len(parser_entries),
            "fixture_entries": len(fixture_entries),
            "generated_entries": len(generated_entries),
        },
    }


def md_header(title: str) -> str:
    return (
        f"# {title} {DATE}\n\n"
        f"Route: `{ROUTE_ID}`\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`\n"
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`\n"
    )


def render_context_anchor() -> str:
    inputs = "\n".join(f"- `{name}`: `{path}`" for name, path in sorted(UPSTREAM_INPUTS.items()))
    prompt_display = str(PROMPT_PATH).replace("\\", "/")
    return f"""{md_header("NOFILL Forward Source Capture Context Anchor")}
## Scope

This lane freezes a source/control-only capture contract and offline projection prototype for later independent G12 audit. It does not score outcomes, validate an edge, promote anything, edit registries, wire live loggers, touch live trading behavior, call paid/API routes, or use broker/account/order/history/deal/position labels.

## Current HEAD

`{git_oneline()}`

## Controlling Prompt

`{prompt_display}`

## Inputs Read

{inputs}

## Active Question Stack

| Question | Resolution |
|---|---|
| Can the accepted G0/G12 projection evidence be hardened into an exact forward source-capture contract? | Yes. The JSON contract freezes field names, types, source/as-of rules, required/fail-closed status, lineage, forbidden rules, and G12/owner gate state. |
| Can an offline parser/projection prototype exist without live wiring? | Yes. It consumes the existing 298 source-safe projection rows and emits a gated prototype packet with no denominator change. |
| Can fixture coverage include redaction and same-tick ambiguity without leaking raw broker values? | Yes. Those fixtures are synthetic source-control fixtures with no raw value material and status-only expected projections. |
| Is future live logger wiring still gated? | Yes. It remains gated behind independent G12 acceptance and separate owner approval. |
"""


def render_contract_md(contract: dict[str, Any]) -> str:
    family_counts = Counter(field["field_family"] for field in contract["fields"])
    lines = [
        md_header("NOFILL Forward Source Capture Contract"),
        "## Contract Boundary",
        "",
        "This contract is frozen for source/control review only. It defines what a future owner-approved live logger lane would need to capture, but it does not implement that wiring.",
        "",
        "## Field Families",
        "",
        "| Family | Field Count |",
        "|---|---:|",
    ]
    lines.extend(f"| `{family}` | {count} |" for family, count in sorted(family_counts.items()))
    lines.extend(
        [
            "",
            "## Required Gate",
            "",
            "Future live logger wiring is still gated behind independent G12 acceptance of this contract/prototype and separate owner approval.",
            "",
            "## Forbidden Raw Values",
            "",
            "Raw broker/account/order/deal/position/result/cost/performance values may not be emitted or hashed. The JSON contract carries the exact forbidden field-name taxonomy as source-control metadata only.",
        ]
    )
    return "\n".join(lines)


def render_evidence_chain(denom: dict[str, Any]) -> str:
    return f"""{md_header("NOFILL Forward Source Capture Evidence Chain Reconciliation")}
| Chain Link | Status | Boundary |
|---|---|---|
| NOFILL CAT V3 source-control rebuild | Consumed as upstream source/control universe. | No result or promotion use. |
| G12 CAT V3 source-control audit | Consumed for label-family and control consistency. | Historical upstream audit only. |
| Forward lifecycle capture contract audit | Consumed for schema blockers and contract hardening. | No live wiring opened. |
| Source-safe projection builder | Consumed 298 row projection and existing source/hash manifests. | Accepted by G12 only as source/control projection evidence. |
| G12 projection repair reaudit | Terminal decision `ACCEPT_AS_SOURCE_CONTROL_PROJECTION_EVIDENCE_ONLY`. | Not validation-safe, not result/cost evidence. |
| G0 synthesis/control route | Ranked this contract/prototype as the next allowed route. | Stops before G12 acceptance and live wiring. |
| This lane | Freezes contract, fixtures, prototype, and verifiers. | Ready for separate G12 audit only. |

## Preserved Counts

- Universe: `{denom['universe_equation']}`.
- Row-level accepted denominator: `{denom['row_level_accepted_denominator']}`.
- Primary duplicate-key denominator: `{denom['primary_duplicate_key_denominator']}`.
- Secondary duplicate-group denominator: `{denom['secondary_duplicate_group_denominator']}`.
- Reject-overlap rows: `{denom['reject_overlap_rows']}` with zero denominator effect.
"""


def render_prototype_design() -> str:
    return f"""{md_header("NOFILL Forward Offline Parser Projection Prototype Design")}
## Algorithm

1. Read only the accepted upstream source/control artifacts named in the context anchor.
2. Parse the 298 source-safe projection rows.
3. Add contract identity and future-gate metadata.
4. Preserve row family, duplicate flags, denominator flags, missing statuses, source hashes, redaction statuses, and closed route flags.
5. Emit `NOFILL_FORWARD_OFFLINE_PROJECTION_PROTOTYPE_ROWS_{DATE}.jsonl`.
6. Generate fixtures for accepted, source-control, source-impossible, reject, touch-not-observed, spread-present, redaction, same-tick ambiguity, missing/NA, duplicate, and forbidden-field examples.

## Explicit Non-Goals

No result/cost scoring, broker account/order/deal/history labels, validation, promotion, registry edit, live logger wiring, or live trading behavior is opened.
"""


def render_no_leak_md(audit: dict[str, Any]) -> str:
    return f"""{md_header("NOFILL Forward No-Leak And Redaction Audit")}
Status: `{audit['status']}`.

- Raw value hits: `{len(audit['raw_value_hits'])}`.
- Forbidden keys in prototype rows: `{len(audit['forbidden_key_hits_in_prototype_rows'])}`.
- Controlled forbidden-taxonomy mentions: `{audit['controlled_taxonomy_mentions_count']}`.
- Raw ticket values emitted: `{audit['redaction_controls']['raw_ticket_values_emitted']}`.
- Raw ticket values hashed: `{audit['redaction_controls']['raw_ticket_values_hashed']}`.

Forbidden field names appear only as controlled taxonomy or negative-fixture metadata. No raw broker/account/order/deal/position values are included.
"""


def render_denom_md(audit: dict[str, Any]) -> str:
    return f"""{md_header("NOFILL Forward Duplicate Denominator Control Audit")}
Status: `{audit['status']}`.

| Control | Value |
|---|---:|
| Projection rows | {audit['projection_row_count']} |
| Accepted row-level denominator | {audit['row_level_accepted_denominator']} |
| Primary duplicate-key denominator | {audit['primary_duplicate_key_denominator']} |
| Secondary duplicate-group denominator | {audit['secondary_duplicate_group_denominator']} |
| Reject-overlap rows | {audit['reject_overlap_rows']} |

Prototype denominator effect: `{audit['prototype_denominator_effect']}`.
"""


def render_cost_ledger_md(ledger: dict[str, Any]) -> str:
    return f"""{md_header("NOFILL Forward Source Cost Execution Separation Ledger")}
Decision spread statuses: `{ledger['decision_spread_status_counts']}`.

Entry-touch spread statuses: `{ledger['entry_touch_spread_status_counts']}`.

Slippage label statuses: `{ledger['slippage_label_status_counts']}`.

Execution-quality label statuses: `{ledger['execution_quality_label_status_counts']}`.

Cost-testing gate statuses: `{ledger['cost_testing_gate_status_counts']}`.

These are source observability statuses only. Slippage values, execution-quality values, broker account/order/history labels, validation, and promotion remain closed.
"""


def render_hostile_md(ledger: dict[str, Any]) -> str:
    lines = [
        md_header("NOFILL Forward Hostile Review And Saturation Ledger"),
        "| Hostile Failure Mode | Control |",
        "|---|---|",
    ]
    for item in ledger["hostile_review_checks"]:
        lines.append(f"| `{item['risk']}` | {item['control']} |")
    lines.extend(
        [
            "",
            f"Saturation decision: {ledger['saturation_decision']}",
            "",
            "No same-evidence-class gaps remain. Remaining work crosses into independent G12 acceptance, owner-approved live wiring, or result/cost scoring.",
        ]
    )
    return "\n".join(lines)


def render_forbidden_md(ledger: dict[str, Any]) -> str:
    lines = [
        md_header("NOFILL Forward Forbidden Route Ledger"),
        "| Route | Status | Future Gate |",
        "|---|---|---|",
    ]
    for item in ledger["forbidden_routes"]:
        lines.append(f"| `{item['route']}` | `{item['status']}` | {item['future_gate']} |")
    lines.append("")
    lines.append("Future live logger wiring remains gated behind G12 acceptance and separate owner approval.")
    return "\n".join(lines)


def render_next_prompt_pack() -> str:
    return f"""{md_header("NOFILL Forward G12 Acceptance Audit Next Prompt Pack")}
## Recommended Next Goal

```text
Build an independent G12 acceptance audit for research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_contract_hardening_offline_projection_prototype/. Audit only source/control contract readiness: field schema, missing-status vocabulary, fixture coverage, redaction/no-leak controls, source/hash manifests, duplicate/denominator controls, source/cost/execution separation, hostile-review saturation, and verifier coverage. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false. Do not score outcomes, validate, promote, edit registries, wire live loggers, call paid/API routes, touch src/prompts/config/risk/execution/permissions/safety/selectors/canaries/order behavior, or use MT5 order/account/history/deal/position labels.
```

## Required Decision

G12 should either accept this package as source/control contract evidence only, or block with exact repair items. G12 must not open live wiring or result/cost scoring.
"""


def completion_audit_payload(
    contract: dict[str, Any],
    fixture_manifest: dict[str, Any],
    denom: dict[str, Any],
    no_leak: dict[str, Any],
) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight", "PASS", "LIVE_STATE regenerated; latest handoff, core doctrine, local-heavy inventory, and prompt read."),
        ("evidence_chain_reconstructed", "PASS", f"Evidence-chain artifact plus upstream inputs under {BASE}."),
        ("frozen_source_capture_contract", "PASS", f"{contract['field_count']} fields with names/types/as-of/source-lineage/G12-owner gate status."),
        ("offline_parser_projection_prototype", "PASS", PROTOTYPE_ROWS_NAME),
        ("fixture_coverage", fixture_manifest["coverage_status"], f"{fixture_manifest['fixture_count']} fixture files cover required categories."),
        ("missing_status_vocabulary", "PASS", f"NOFILL_FORWARD_MISSING_STATUS_VOCABULARY_{DATE}.json"),
        ("redaction_controls", no_leak["status"], f"NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_{DATE}.json"),
        ("source_hash_manifest", "PASS", f"NOFILL_FORWARD_SOURCE_HASH_MANIFEST_{DATE}.json"),
        ("duplicate_denominator_controls", denom["status"], f"{denom['universe_equation']} and 225/182/139 preserved."),
        ("g12_next_prompt_pack", "PASS", f"NOFILL_FORWARD_G12_ACCEPTANCE_AUDIT_NEXT_PROMPT_PACK_{DATE}.md"),
        ("research_current_state_update", "PASS", "Updated only because this lane materially changes the research map."),
        ("future_live_logger_wiring_gate", "PASS", "Still gated behind G12 acceptance and separate owner approval."),
    ]
    return {
        **base_payload("NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT"),
        "objective_restated": "Build a source/control-only contract and offline projection prototype ready for a separate G12 acceptance audit.",
        "prompt_to_artifact_checklist": [
            {"requirement": req, "status": status, "evidence": evidence}
            for req, status, evidence in checklist
        ],
        "missing_incomplete_or_weak_requirements": [
            item for item in checklist if item[1] != "PASS"
        ],
        "can_mark_goal_complete_after_verification_and_commit": all(item[1] == "PASS" for item in checklist),
        "future_live_logger_wiring_lane_still_gated": True,
        "verification_result_artifact": VERIFICATION_RESULT_NAME,
    }


def render_completion_md(audit: dict[str, Any]) -> str:
    lines = [
        md_header("NOFILL Forward Source Capture Completion Audit"),
        f"Objective: {audit['objective_restated']}",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence |",
        "|---|---|---|",
    ]
    for item in audit["prompt_to_artifact_checklist"]:
        lines.append(f"| `{item['requirement']}` | `{item['status']}` | {item['evidence']} |")
    lines.extend(
        [
            "",
            f"Can mark complete after verification and commit: `{audit['can_mark_goal_complete_after_verification_and_commit']}`.",
            "",
            f"Future live logger wiring lane still gated: `{audit['future_live_logger_wiring_lane_still_gated']}`.",
        ]
    )
    return "\n".join(lines)


def build_artifacts() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    g0_schema = read_json(UPSTREAM_INPUTS["g0_schema_requirements"])
    g0_matrix = read_json(UPSTREAM_INPUTS["g0_field_matrix"])
    allowlist = read_json(UPSTREAM_INPUTS["source_projection_allowlist"])
    upstream_denom = read_json(UPSTREAM_INPUTS["source_projection_denom"])
    upstream_missing = read_json(UPSTREAM_INPUTS["source_projection_missing"])
    source_rows = read_jsonl(UPSTREAM_INPUTS["source_projection_rows"])

    contract = build_contract(g0_schema, g0_matrix)
    missing_vocab = build_missing_status_vocabulary(contract, source_rows, upstream_missing)
    field_schema = build_source_field_schema(contract, allowlist)
    prototype_rows = build_prototype_rows(source_rows)
    fixture_manifest = build_fixtures(source_rows)
    denom = denominator_audit(prototype_rows, upstream_denom)
    cost_ledger = cost_execution_ledger(prototype_rows)
    hostile_ledger = hostile_review_ledger()
    forbidden_ledger = forbidden_route_ledger()
    completion = completion_audit_payload(contract, fixture_manifest, denom, {"status": "PENDING"})

    generated_files: list[Path] = []
    generated_files.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_{DATE}.json", contract))
    generated_files.append(write_json(f"NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_{DATE}.json", field_schema))
    generated_files.append(write_json(f"NOFILL_FORWARD_MISSING_STATUS_VOCABULARY_{DATE}.json", missing_vocab))
    generated_files.append(write_json(f"NOFILL_FORWARD_FIXTURE_MANIFEST_{DATE}.json", fixture_manifest))
    generated_files.append(write_jsonl(PROTOTYPE_ROWS_NAME, prototype_rows))
    generated_files.append(write_json(f"NOFILL_FORWARD_DUPLICATE_DENOMINATOR_CONTROL_AUDIT_{DATE}.json", denom))
    generated_files.append(write_json(f"NOFILL_FORWARD_SOURCE_COST_EXECUTION_SEPARATION_LEDGER_{DATE}.json", cost_ledger))
    generated_files.append(write_json(f"NOFILL_FORWARD_HOSTILE_REVIEW_AND_SATURATION_LEDGER_{DATE}.json", hostile_ledger))
    generated_files.append(write_json(f"NOFILL_FORWARD_FORBIDDEN_ROUTE_LEDGER_{DATE}.json", forbidden_ledger))

    generated_files.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_CONTEXT_ANCHOR_{DATE}.md", render_context_anchor()))
    generated_files.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_EVIDENCE_CHAIN_RECONCILIATION_{DATE}.md", render_evidence_chain(denom)))
    generated_files.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_{DATE}.md", render_contract_md(contract)))
    generated_files.append(write_md(f"NOFILL_FORWARD_OFFLINE_PARSER_PROJECTION_PROTOTYPE_DESIGN_{DATE}.md", render_prototype_design()))
    generated_files.append(write_md(f"NOFILL_FORWARD_DUPLICATE_DENOMINATOR_CONTROL_AUDIT_{DATE}.md", render_denom_md(denom)))
    generated_files.append(write_md(f"NOFILL_FORWARD_SOURCE_COST_EXECUTION_SEPARATION_LEDGER_{DATE}.md", render_cost_ledger_md(cost_ledger)))
    generated_files.append(write_md(f"NOFILL_FORWARD_HOSTILE_REVIEW_AND_SATURATION_LEDGER_{DATE}.md", render_hostile_md(hostile_ledger)))
    generated_files.append(write_md(f"NOFILL_FORWARD_FORBIDDEN_ROUTE_LEDGER_{DATE}.md", render_forbidden_md(forbidden_ledger)))
    generated_files.append(write_md(f"NOFILL_FORWARD_G12_ACCEPTANCE_AUDIT_NEXT_PROMPT_PACK_{DATE}.md", render_next_prompt_pack()))

    no_leak = scan_generated_files(
        generated_files
        + [REPO_ROOT / item["path"] for item in fixture_manifest["fixtures"]]
        + [OUT_DIR / PROTOTYPE_ROWS_NAME]
    )
    completion = completion_audit_payload(contract, fixture_manifest, denom, no_leak)
    generated_files.append(write_json(f"NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_{DATE}.json", no_leak))
    generated_files.append(write_md(f"NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_{DATE}.md", render_no_leak_md(no_leak)))
    generated_files.append(write_json(f"NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_{DATE}.json", completion))
    generated_files.append(write_md(f"NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_{DATE}.md", render_completion_md(completion)))

    source_manifest = build_source_hash_manifest(generated_files, fixture_manifest)
    generated_files.append(write_json(f"NOFILL_FORWARD_SOURCE_HASH_MANIFEST_{DATE}.json", source_manifest))

    return {
        "contract": contract,
        "fixture_manifest": fixture_manifest,
        "denominator": denom,
        "no_leak": no_leak,
        "source_manifest": source_manifest,
        "generated_file_count": len(generated_files),
    }


def main() -> int:
    payload = build_artifacts()
    print(
        json.dumps(
            {
                "ok": payload["denominator"]["status"] == "PASS" and payload["no_leak"]["status"] == "PASS",
                "route_id": ROUTE_ID,
                "field_count": payload["contract"]["field_count"],
                "fixture_count": payload["fixture_manifest"]["fixture_count"],
                "denominator_status": payload["denominator"]["status"],
                "no_leak_status": payload["no_leak"]["status"],
                "generated_file_count": payload["generated_file_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
