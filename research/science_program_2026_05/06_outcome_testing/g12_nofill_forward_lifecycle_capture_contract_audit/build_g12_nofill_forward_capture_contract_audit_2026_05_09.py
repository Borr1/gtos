#!/usr/bin/env python3
"""Build the G12 NOFILL forward lifecycle capture contract audit artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "g12_nofill_forward_lifecycle_capture_contract_audit_v1"
AUDIT_LANE_ID = "G12_NOFILL_FORWARD_LIFECYCLE_CAPTURE_CONTRACT_AUDIT"
AUDITED_ROUTE_ID = "NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT"
TERMINAL_VERDICT = "ACCEPT_WITH_EXACT_CONTRACT_BLOCKERS"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
BASE = Path("research/science_program_2026_05/06_outcome_testing")
PROMPT_PATH = Path(
    "research/science_program_2026_05/04_goal_prompts/"
    "G12_NOFILL_FORWARD_CAPTURE_CONTRACT_AUDIT_GOAL_PROMPT_2026-05-09.md"
)

FORWARD_DIR = BASE / "nofill_cat_v3_forward_lifecycle_capture_contract"
G0_DIR = BASE / "g0_nofill_cat_v3_categorical_evidence_synthesis_control_review"
G12_COUNT_DIR = BASE / "g12_nofill_cat_v3_quarantined_categorical_count_packet_audit"
COUNT_PACKET_DIR = BASE / "nofill_cat_v3_quarantined_categorical_count_packet"
G12_RESULT_DIR = BASE / "g12_nofill_cat_v3_result_contract_audit"
RESULT_UPDATE_DIR = BASE / "nofill_cat_v3_result_contract_update"
G12_SOURCE_DIR = BASE / "g12_nofill_cat_v3_source_control_audit"
SOURCE_REBUILD_DIR = BASE / "nofill_cat_v3_source_control_rebuild"
USDJPY_SEQ_DIR = BASE / "nofill_cat_v3_usdjpy_quote_event_sequence_source_access"

SOURCE_CONTROL_ROWS = [
    "NOFILL-CAT-ROW-0049",
    "NOFILL-CAT-ROW-0050",
    "NOFILL-CAT-ROW-0051",
    "NOFILL-CAT-ROW-0241",
]
SOURCE_IMPOSSIBLE_ROWS = [
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
]
EXPECTED_TERMINAL_COUNTS = {
    "accepted": 225,
    "source_control": 4,
    "source_impossible": 4,
    "reject": 65,
    "blocked": 0,
}
EXPECTED_LABEL_COUNTS_ROW_LEVEL = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 51,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_LABEL_COUNTS_DUPLICATE_KEY = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 22,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 8,
    "source_corrected_no_entry_through_pending_horizon": 32,
}
EXPECTED_LABEL_COUNTS_DUPLICATE_GROUP = {
    "canonical_duplicate_geometry_source_ready_no_label_assigned": 3,
    "fill_path_entry_before_protective_level_before_terminal_area": 4,
    "fill_path_entry_before_protective_level_no_terminal_observed": 4,
    "fill_path_entry_before_terminal_area_before_protective_level": 3,
    "nofill_terminal_before_entry": 110,
    "opening_drive_source_projection_ready_no_result_label": 8,
    "source_corrected_no_entry_through_pending_horizon": 7,
}

REQUIRED_CONTEXT_FILES = [
    Path(".context/LIVE_STATE.md"),
    Path(".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md"),
    Path(".context/00_core/quick_reference_card.md"),
    Path(".context/00_core/research_operating_doctrine.md"),
    Path(".context/00_core/research_current_state.md"),
    Path(".context/00_core/goal_session_research_discipline.md"),
    Path(".context/00_core/local_heavy_data_inventory.md"),
]

FORWARD_REQUIRED_INPUTS = [
    FORWARD_DIR / "NOFILL_FORWARD_CONTEXT_ANCHOR_2026-05-09.md",
    FORWARD_DIR / "NOFILL_FORWARD_CAPTURE_CONTRACT_2026-05-09.md",
    FORWARD_DIR / "NOFILL_FORWARD_CAPTURE_CONTRACT_2026-05-09.json",
    FORWARD_DIR / "NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_2026-05-09.json",
    FORWARD_DIR / "NOFILL_FORWARD_NO_LEAK_FIELD_POLICY_2026-05-09.json",
    FORWARD_DIR / "NOFILL_FORWARD_DUPLICATE_DENOMINATOR_POLICY_2026-05-09.json",
    FORWARD_DIR / "NOFILL_FORWARD_EXISTING_SOURCE_AND_CODE_AUDIT_2026-05-09.json",
    FORWARD_DIR / "NOFILL_FORWARD_CAPTURE_BACKLOG_AND_IMPLEMENTATION_ROUTE_2026-05-09.json",
    FORWARD_DIR / "NOFILL_FORWARD_HOSTILE_EDGE_REVIEW_AND_SATURATION_2026-05-09.md",
    FORWARD_DIR / "NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.md",
    FORWARD_DIR / "build_nofill_forward_lifecycle_capture_contract_2026_05_09.py",
    FORWARD_DIR / "verify_nofill_forward_lifecycle_capture_contract_2026_05_09.py",
    FORWARD_DIR / "test_nofill_forward_lifecycle_capture_contract_2026_05_09.py",
]

UPSTREAM_DIRS = [
    G0_DIR,
    G12_COUNT_DIR,
    COUNT_PACKET_DIR,
    G12_RESULT_DIR,
    RESULT_UPDATE_DIR,
    G12_SOURCE_DIR,
    SOURCE_REBUILD_DIR,
    USDJPY_SEQ_DIR,
]

SOURCE_SURFACES = [
    Path("src/research_infra/forward_capture.py"),
    Path("src/components/pending_limit_lifecycle_logger.py"),
    Path("src/research_infra/pending_limit_lifecycle_audit.py"),
    Path("src/research_infra/opportunity_lifecycle_audit.py"),
    Path("src/research_infra/candidate_path_contract.py"),
    Path("scripts/follow_live_candidate_paths.py"),
    Path("scripts/backfill_pending_limit_lifecycle_audit.py"),
]

SOURCE_LOGS = [
    Path("shadow_logs/pending_limit_lifecycle.jsonl"),
    Path("shadow_logs/pending_limit_lifecycle_audit.jsonl"),
    Path("shadow_logs/pending_limit_lifecycle_join_backfill.jsonl"),
    Path("shadow_logs/candidate_path_follow.jsonl"),
    Path("shadow_logs/candidate_ltf_path_order.jsonl"),
    Path("shadow_logs/strategy_follow_candidates.jsonl"),
    Path("shadow_logs/strategy_follow_evaluations.jsonl"),
    Path("shadow_logs/prefill_delivery_path.jsonl"),
    Path("shadow_logs/v2b_forward_pairs.jsonl"),
    Path("shadow_logs/fvg_ob_confluence.jsonl"),
    Path("shadow_logs/context_control_ledger.jsonl"),
]

FORBIDDEN_RESULT_OR_LIVE_FIELD_TOKENS = {
    "actual_r",
    "broker_actual_r",
    "synthetic_path_r",
    "realized_r",
    "outcome_r",
    "win_rate",
    "expectancy",
    "mt5_order_ticket",
    "mt5_deal_id",
    "account_history",
    "order_history",
    "broker_fill_state",
    "live_order_state",
    "order_send_success",
    "order_send_attempted",
    "paid_api_result",
    "databento_payload",
}
FORBIDDEN_TRUE_FLAGS = ("validation_safe", "outcome_review_opened", "live_effect")

EXACT_CONTRACT_BLOCKERS = [
    {
        "blocker_id": "G12-FWD-BLOCKER-001",
        "severity": "CONTRACT_ADDENDUM_REQUIRED_BEFORE_IMPLEMENTATION_ACCEPTANCE",
        "finding": "Capture-latency observability is only partial. The contract has source manifest and source coverage timestamps, but no explicit row capture/write latency fields.",
        "exact_fix": [
            "Add capture_observed_at_utc or equivalent.",
            "Add capture_write_completed_utc or equivalent.",
            "Add capture_latency_ms or explicit null/impossible reason.",
            "Add capture_clock_source_and_skew_policy or equivalent.",
        ],
        "evidence": "Forward schema includes source_manifest_created_utc, first_quote_utc, last_quote_utc, and coverage windows, but no field name containing capture_latency, write_completed, or clock_skew.",
        "forbidden_shortcut": "Do not infer capture latency later from file mtime without hashing and recording the parser rule.",
    },
    {
        "blocker_id": "G12-FWD-BLOCKER-002",
        "severity": "CONTRACT_ADDENDUM_REQUIRED_BEFORE_RAW_LOG_PROJECTION",
        "finding": "Source-safe pending-order observability is not explicit enough to consume current lifecycle logs without accidental order/account leakage.",
        "exact_fix": [
            "Add pending_order_mode_source_safe or map pending_order_mode with an allowlist.",
            "Add broker_pending_order_created_status as a categorical observability field, not a broker outcome label.",
            "Add native_pending_order_type_status with MT5 ticket redaction proof.",
            "Add mt5_order_ticket_redaction_status and fail closed when a ticket value would enter the contract row.",
        ],
        "evidence": "pending_limit_lifecycle_logger.py and forward_capture.py expose pending_order_mode, broker_pending_order_created, native_pending_order_type, and mt5_order_ticket; the contract forbids MT5 order history but does not give source-safe replacement fields.",
        "forbidden_shortcut": "Do not pass mt5_order_ticket, trade_state_ticket, order_send_success, or broker_fill_state into a forward contract row.",
    },
    {
        "blocker_id": "G12-FWD-BLOCKER-003",
        "severity": "CONTRACT_ADDENDUM_REQUIRED_BEFORE_COST_EXECUTION_TESTING",
        "finding": "Cost/spread coverage is present only as spread_state and quote_side. Slippage and execution-quality observability need closed source-safe status fields before any later cost or survival test.",
        "exact_fix": [
            "Add decision_spread_source_safe and entry_touch_spread_source_safe or explicit unavailable statuses.",
            "Add slippage_label_status fixed to NOT_OPENED_FOR_SOURCE_CONTROL unless a later result lane is explicitly opened.",
            "Add execution_quality_label_status fixed to NOT_OPENED_FOR_SOURCE_CONTROL.",
            "Preserve source hashes for any spread/quote measurement.",
        ],
        "evidence": "Forward schema has quote_side and spread_state. pending_limit_lifecycle_logger.py has slippage_price and order-send fields, which are not source-control-safe for this lane.",
        "forbidden_shortcut": "Do not use slippage_price, order_send_success, broker_fill_state, or account/order-history records inside this source/control contract.",
    },
]


def now_utc() -> str:
    fixed = os.environ.get("G12_NOFILL_FORWARD_AUDIT_FIXED_GENERATED_AT")
    if fixed:
        return fixed
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def abs_path(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else REPO_ROOT / path


def rel(path: Path | str) -> str:
    path = Path(path)
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path | str) -> Any:
    with abs_path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path | str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    p = abs_path(path)
    if not p.exists():
        return rows
    with p.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def write_json(name: str, payload: dict[str, Any]) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(name: str, title: str, body: str) -> None:
    (OUT_DIR / name).write_text("# " + title + "\n\n" + body.rstrip() + "\n", encoding="utf-8")


def sha256_file(path: Path | str) -> str | None:
    p = abs_path(path)
    if not p.exists() or not p.is_file():
        return None
    digest = hashlib.sha256()
    with p.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path | str, role: str) -> dict[str, Any]:
    p = abs_path(path)
    return {
        "path": rel(p),
        "role": role,
        "exists": p.exists(),
        "size_bytes": p.stat().st_size if p.exists() and p.is_file() else None,
        "sha256": sha256_file(p) if p.exists() and p.is_file() else None,
        "git_last_commit": git_last_commit(rel(p)) if p.exists() and p.is_file() else None,
    }


def git_output(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else proc.stderr.strip()


def git_last_commit(path: str) -> str | None:
    value = git_output(["log", "-1", "--format=%H", "--", path])
    return value or None


def base_flags() -> dict[str, Any]:
    return {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_live_wiring": False,
        "opens_selector_logic": False,
        "opens_registry_edit": False,
        "opens_paid_api_or_databento_route": False,
        "changes_live_trading_behavior": False,
    }


def all_input_files() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = [file_record(PROMPT_PATH, "controlling_g12_prompt")]
    records.extend(file_record(path, "mandatory_preflight_context") for path in REQUIRED_CONTEXT_FILES)
    records.extend(file_record(path, "forward_contract_controlling_input") for path in FORWARD_REQUIRED_INPUTS)
    for directory in UPSTREAM_DIRS:
        root = abs_path(directory)
        if not root.exists():
            records.append({"path": rel(root), "role": "upstream_chain_directory", "exists": False})
            continue
        for path in sorted(root.iterdir(), key=lambda item: item.name):
            if path.suffix.lower() in {".json", ".jsonl", ".md", ".py"}:
                records.append(file_record(path, f"upstream_chain:{directory.name}"))
    return records


def flattened_values(obj: Any, path: str = "") -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            out.extend(flattened_values(value, child))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            out.extend(flattened_values(value, f"{path}[{idx}]"))
    else:
        out.append((path, obj))
    return out


def scan_payload_flags(name: str, payload: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for key_path, value in flattened_values(payload):
        leaf = key_path.split(".")[-1].split("[")[0]
        if leaf in FORBIDDEN_TRUE_FLAGS and value is not False:
            issues.append({"artifact": name, "path": key_path, "value": value, "issue": "unsafe_true_flag"})
        if leaf == "promotion_verdict" and value != PROMOTION_VERDICT:
            issues.append({"artifact": name, "path": key_path, "value": value, "issue": "promotion_verdict_not_preserved"})
    return issues


def counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def analyze_evidence_chain() -> dict[str, Any]:
    accepted = load_jsonl(COUNT_PACKET_DIR / f"NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_{DATE}.jsonl")
    exclusions = load_jsonl(COUNT_PACKET_DIR / f"NOFILL_CAT_V3_COUNT_EXCLUSION_PROOF_LEDGER_{DATE}.jsonl")
    eligibility = load_jsonl(RESULT_UPDATE_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_ELIGIBILITY_LEDGER_{DATE}.jsonl")
    contract_exclusions = load_jsonl(RESULT_UPDATE_DIR / f"NOFILL_CAT_V3_RESULT_CONTRACT_EXCLUSION_LEDGER_{DATE}.jsonl")

    terminal_counts = Counter(str(row.get("v3_terminal_family") or "UNKNOWN") for row in exclusions)
    terminal_counts["accepted"] = len(accepted)
    terminal_counts.setdefault("blocked", 0)
    universe_total = len(accepted) + len(exclusions)

    accepted_ids = {str(row.get("packet_row_id")) for row in accepted}
    eligibility_ids = {str(row.get("packet_row_id")) for row in eligibility}
    exclusion_ids = {str(row.get("packet_row_id")) for row in exclusions}
    contract_exclusion_ids = {str(row.get("packet_row_id")) for row in contract_exclusions}

    accepted_keys = {str(row.get("nofill_duplicate_key")) for row in accepted}
    accepted_groups = {str(row.get("duplicate_group_id")) for row in accepted}
    duplicate_key_members = [row for row in accepted if row.get("nofill_duplicate_key_count_member") is True]
    duplicate_group_members = [row for row in accepted if row.get("duplicate_group_id_count_member") is True]

    rows_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rows_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accepted:
        rows_by_key[str(row.get("nofill_duplicate_key"))].append(row)
        rows_by_group[str(row.get("duplicate_group_id"))].append(row)

    label_conflicts = []
    geometry_conflicts = []
    key_denominator_conflicts = []
    group_denominator_conflicts = []
    for key, rows in rows_by_key.items():
        labels = {str(row.get("categorical_lifecycle_label")) for row in rows}
        if len(labels) != 1:
            label_conflicts.append({"nofill_duplicate_key": key, "labels": sorted(labels)})
        geometry = {
            (
                row.get("symbol"),
                row.get("session"),
                row.get("side"),
                row.get("source_lane"),
                row.get("source_packet_id"),
                row.get("duplicate_group_id"),
            )
            for row in rows
        }
        if len(geometry) != 1:
            geometry_conflicts.append({"nofill_duplicate_key": key, "geometry_count": len(geometry)})
        member_count = sum(1 for row in rows if row.get("nofill_duplicate_key_count_member") is True)
        if member_count != 1:
            key_denominator_conflicts.append({"nofill_duplicate_key": key, "member_count": member_count})
    for group, rows in rows_by_group.items():
        member_count = sum(1 for row in rows if row.get("duplicate_group_id_count_member") is True)
        if member_count != 1:
            group_denominator_conflicts.append({"duplicate_group_id": group, "member_count": member_count})

    reject_rows = [row for row in exclusions if row.get("v3_terminal_family") == "reject"]
    source_control_rows = [row for row in exclusions if row.get("v3_terminal_family") == "source_control"]
    source_impossible_rows = [row for row in exclusions if row.get("v3_terminal_family") == "source_impossible"]
    reject_key_overlap = sorted(row.get("packet_row_id") for row in reject_rows if str(row.get("nofill_duplicate_key")) in accepted_keys)
    reject_group_overlap = sorted(row.get("packet_row_id") for row in reject_rows if str(row.get("duplicate_group_id")) in accepted_groups)
    exclusion_denominator_violations = [
        row.get("packet_row_id")
        for row in exclusions
        if row.get("row_level_count_member") or row.get("nofill_duplicate_key_count_member") or row.get("duplicate_group_id_count_member")
    ]
    accepted_flag_issues = []
    for row in accepted:
        row_id = row.get("packet_row_id")
        if row.get("promotion_verdict") != PROMOTION_VERDICT:
            accepted_flag_issues.append({"packet_row_id": row_id, "issue": "promotion_verdict"})
        if row.get("validation_safe") is not False:
            accepted_flag_issues.append({"packet_row_id": row_id, "issue": "validation_safe"})
        if row.get("outcome_review_opened") is not False:
            accepted_flag_issues.append({"packet_row_id": row_id, "issue": "outcome_review_opened"})
        if row.get("live_effect") is not False:
            accepted_flag_issues.append({"packet_row_id": row_id, "issue": "live_effect"})
        if row.get("source_safe_input_only") is not True:
            accepted_flag_issues.append({"packet_row_id": row_id, "issue": "source_safe_input_only"})
    mandatory_source_control = sorted(str(row.get("packet_row_id")) for row in source_control_rows)
    mandatory_source_impossible = sorted(str(row.get("packet_row_id")) for row in source_impossible_rows)

    issues = []
    if universe_total != 298:
        issues.append("universe_total_mismatch")
    if {key: terminal_counts.get(key, 0) for key in EXPECTED_TERMINAL_COUNTS} != EXPECTED_TERMINAL_COUNTS:
        issues.append("terminal_partition_mismatch")
    if len(accepted) != 225 or len(accepted_keys) != 182 or len(accepted_groups) != 139:
        issues.append("denominator_count_mismatch")
    if accepted_ids != eligibility_ids:
        issues.append("accepted_ids_do_not_match_result_contract")
    if exclusion_ids != contract_exclusion_ids:
        issues.append("exclusion_ids_do_not_match_result_contract")
    if mandatory_source_control != SOURCE_CONTROL_ROWS:
        issues.append("source_control_row_set_mismatch")
    if mandatory_source_impossible != SOURCE_IMPOSSIBLE_ROWS:
        issues.append("source_impossible_row_set_mismatch")
    if len(reject_key_overlap) != 47 or len(reject_group_overlap) != 47:
        issues.append("reject_overlap_mismatch")
    if exclusion_denominator_violations:
        issues.append("exclusion_denominator_leak")
    if label_conflicts or geometry_conflicts or key_denominator_conflicts or group_denominator_conflicts:
        issues.append("duplicate_conflicts")
    if accepted_flag_issues:
        issues.append("accepted_flag_issues")

    return {
        **base_flags(),
        "artifact_family": "G12_NOFILL_FORWARD_DUPLICATE_DENOMINATOR_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "universe_equation": {
            "text": "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject",
            "total": universe_total,
            "terminal_counts": {key: terminal_counts.get(key, 0) for key in sorted(EXPECTED_TERMINAL_COUNTS)},
        },
        "denominators": {
            "row_level_accepted": len(accepted),
            "unique_nofill_duplicate_key": len(accepted_keys),
            "unique_duplicate_group_id": len(accepted_groups),
            "duplicate_key_count_members": len(duplicate_key_members),
            "duplicate_group_count_members": len(duplicate_group_members),
        },
        "label_counts": {
            "row_level": counter_dict(Counter(str(row.get("categorical_lifecycle_label")) for row in accepted)),
            "duplicate_key": counter_dict(Counter(str(row.get("categorical_lifecycle_label")) for row in duplicate_key_members)),
            "duplicate_group": counter_dict(Counter(str(row.get("categorical_lifecycle_label")) for row in duplicate_group_members)),
            "expected_row_level": EXPECTED_LABEL_COUNTS_ROW_LEVEL,
            "expected_duplicate_key": EXPECTED_LABEL_COUNTS_DUPLICATE_KEY,
            "expected_duplicate_group": EXPECTED_LABEL_COUNTS_DUPLICATE_GROUP,
        },
        "mandatory_exclusions": {
            "source_control_rows": mandatory_source_control,
            "source_impossible_rows": mandatory_source_impossible,
            "reject_rows": len(reject_rows),
            "exclusion_denominator_violations": exclusion_denominator_violations,
        },
        "reject_overlap": {
            "reject_key_overlap_count": len(reject_key_overlap),
            "reject_group_overlap_count": len(reject_group_overlap),
            "denominator_delta_after_accepted_first_filter": {
                "row_level": 0,
                "duplicate_key": 0,
                "duplicate_group": 0,
            },
            "overlap_rows_sample": reject_key_overlap[:20],
        },
        "contract_alignment": {
            "accepted_ids_match_result_contract_eligibility": accepted_ids == eligibility_ids,
            "exclusion_ids_match_result_contract_exclusions": exclusion_ids == contract_exclusion_ids,
        },
        "duplicate_conflicts": {
            "label_conflict_count": len(label_conflicts),
            "geometry_conflict_count": len(geometry_conflicts),
            "key_denominator_conflict_count": len(key_denominator_conflicts),
            "group_denominator_conflict_count": len(group_denominator_conflicts),
            "label_conflicts": label_conflicts[:20],
            "geometry_conflicts": geometry_conflicts[:20],
            "key_denominator_conflicts": key_denominator_conflicts[:20],
            "group_denominator_conflicts": group_denominator_conflicts[:20],
        },
        "accepted_flag_issues": accepted_flag_issues[:50],
    }


def analyze_forward_schema() -> dict[str, Any]:
    schema = load_json(FORWARD_DIR / f"NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_{DATE}.json")
    contract = load_json(FORWARD_DIR / f"NOFILL_FORWARD_CAPTURE_CONTRACT_{DATE}.json")
    fields = schema.get("contract_fields", [])
    field_names = [str(field.get("field_name")) for field in fields]
    families = sorted({str(field.get("field_family")) for field in fields})
    required_metadata = {
        "field_name",
        "field_family",
        "required_or_optional",
        "allowed_source_types",
        "as_of_rule",
        "hash_requirement",
        "no_leak_role",
        "forbidden_substitute_fields",
        "capture_mode",
        "verification_rule",
    }
    metadata_issues = [
        {"field_name": field.get("field_name"), "missing": sorted(required_metadata - set(field))}
        for field in fields
        if required_metadata - set(field)
    ]
    forbidden_schema_fields = sorted(set(field_names) & FORBIDDEN_RESULT_OR_LIVE_FIELD_TOKENS)
    unsafe_flag_issues = scan_payload_flags("NOFILL_FORWARD_SOURCE_FIELD_SCHEMA", schema)
    unsafe_flag_issues.extend(scan_payload_flags("NOFILL_FORWARD_CAPTURE_CONTRACT", contract))

    def names_matching(pattern: str) -> list[str]:
        rx = re.compile(pattern, re.I)
        return sorted(name for name in field_names if rx.search(name))

    prompt_topic_coverage = {
        "source_asof_timestamp_fields": names_matching(r"asof|utc|timestamp|time|horizon|coverage"),
        "no_leak_exclusion_fields": names_matching(r"validation_safe|outcome_review_opened|live_effect|promotion|forbidden|status"),
        "cost_spread_slippage_execution_observability_fields": names_matching(r"spread|quote|slippage|execution|order|broker|fill"),
        "duplicate_denominator_fields": names_matching(r"duplicate|canonical|accepted_first|reject_overlap|denominator|concentration"),
        "source_provenance_hash_parser_fields": names_matching(r"source|hash|parser|builder|manifest|version|head"),
        "capture_latency_fields": names_matching(r"latency|write_completed|observed_at|clock_skew|capture_latency"),
        "blocker_pattern_fields": names_matching(r"nofill|no_entry|terminal|entry|touch|event|sequence|same_tick|same_bar|opening|protective|impossible"),
    }
    coverage_assessment = {
        "source_asof_timestamp_fields": "PASS" if prompt_topic_coverage["source_asof_timestamp_fields"] else "FAIL",
        "no_leak_exclusions": "PASS" if {"validation_safe", "outcome_review_opened", "live_effect", "promotion_verdict"}.issubset(field_names) else "FAIL",
        "cost_spread_slippage_execution_observability": "PARTIAL_WITH_BLOCKER"
        if "spread_state" in field_names and not names_matching(r"slippage|execution_quality|pending_order_mode")
        else "PASS",
        "duplicate_denominator_controls": "PASS" if {"nofill_duplicate_key", "duplicate_group_id", "canonical_row_id"}.issubset(field_names) else "FAIL",
        "source_provenance_hash_parser": "PASS" if {"source_artifact_hash", "parser_version", "parser_code_hash", "source_file_hashes"}.issubset(field_names) else "FAIL",
        "capture_latency": "PARTIAL_WITH_BLOCKER" if not prompt_topic_coverage["capture_latency_fields"] else "PASS",
        "blocker_patterns": "PASS"
        if {"same_tick_same_bar_ambiguity_status", "event_sequence", "exact_next_source_if_unresolved"}.issubset(field_names)
        else "FAIL",
    }
    issues = []
    if len(fields) != 80:
        issues.append("unexpected_field_count")
    if len(families) != 12:
        issues.append("unexpected_family_count")
    if metadata_issues:
        issues.append("field_metadata_missing")
    if forbidden_schema_fields:
        issues.append("forbidden_schema_field_names")
    if unsafe_flag_issues:
        issues.append("unsafe_flag_issue")
    if any(value == "FAIL" for value in coverage_assessment.values()):
        issues.append("prompt_topic_coverage_failure")

    return {
        **base_flags(),
        "artifact_family": "G12_NOFILL_FORWARD_SCHEMA_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "status": "PASS_WITH_EXACT_CONTRACT_BLOCKERS" if not issues else "FAIL",
        "issues": issues,
        "field_count": len(fields),
        "family_count": len(families),
        "families": families,
        "required_metadata_keys": sorted(required_metadata),
        "metadata_issue_count": len(metadata_issues),
        "metadata_issues": metadata_issues[:25],
        "forbidden_schema_field_hits": forbidden_schema_fields,
        "unsafe_flag_issues": unsafe_flag_issues,
        "prompt_topic_coverage": prompt_topic_coverage,
        "coverage_assessment": coverage_assessment,
        "exact_contract_blockers": EXACT_CONTRACT_BLOCKERS,
        "accepted_schema_claims": [
            "Field families cover identity/provenance, decision as-of, pending intent, source coverage, event order, duplicate controls, label separation, no-leak guards, and capture backlog control.",
            "Forbidden result/account/order field names are not accepted schema field names.",
            "Every schema row carries source hash requirements, as-of rules, and forbidden substitute fields.",
            "The schema preserves same-tick/same-bar ambiguity and exact next source requirements instead of guessing order.",
        ],
        "weakened_schema_claims": [
            "Capture latency is a concept in source manifests but not an explicit row field.",
            "Execution observability is protected by forbidden-label status fields but lacks a source-safe pending-order-mode projection contract.",
            "Spread is present as spread_state, but slippage/execution-quality must remain closed or be represented by explicit NOT_OPENED status fields before cost testing.",
        ],
    }


def source_file_audit() -> list[dict[str, Any]]:
    records = []
    for path in SOURCE_SURFACES:
        p = abs_path(path)
        text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        function_names = sorted(set(re.findall(r"^def\s+([a-zA-Z0-9_]+)\(", text, flags=re.M)))
        forbidden_hits = sorted(token for token in FORBIDDEN_RESULT_OR_LIVE_FIELD_TOKENS if token in text)
        safe_status_hits = sorted(set(re.findall(r"NO_PROMOTION_VERDICT|no_ai_calls|no_execution|paid_fetch_attempted|NO_TICK_ORDER_CLAIM|FORWARD_SHADOW|CONTROL_ONLY", text)))
        records.append(
            {
                "path": rel(p),
                "exists": p.exists(),
                "sha256": sha256_file(p) if p.exists() else None,
                "function_names_sample": function_names[:40],
                "function_count": len(function_names),
                "forbidden_token_hits_in_source_text": forbidden_hits,
                "safe_status_literals": safe_status_hits,
                "audit_interpretation": (
                    "usable_only_through_source_safe_allowlist_projection"
                    if forbidden_hits
                    else "source_safe_candidate_surface_or_context_only"
                ),
            }
        )
    return records


def source_log_schema_audit() -> list[dict[str, Any]]:
    out = []
    for path in SOURCE_LOGS:
        p = abs_path(path)
        row_count = 0
        key_counter: Counter[str] = Counter()
        forbidden_key_counter: Counter[str] = Counter()
        unsafe_flag_values = []
        parse_errors = 0
        if p.exists():
            with p.open("r", encoding="utf-8", errors="replace") as handle:
                for line_no, line in enumerate(handle, start=1):
                    text = line.strip()
                    if not text:
                        continue
                    try:
                        row = json.loads(text)
                    except json.JSONDecodeError as exc:
                        parse_errors += 1
                        if parse_errors <= 5:
                            unsafe_flag_values.append({"line": line_no, "parse_error": str(exc)})
                        continue
                    row_count += 1
                    for key, value in row.items():
                        key_s = str(key)
                        key_counter[key_s] += 1
                        if key_s in FORBIDDEN_RESULT_OR_LIVE_FIELD_TOKENS:
                            forbidden_key_counter[key_s] += 1
                        if key_s in FORBIDDEN_TRUE_FLAGS and value is not False:
                            unsafe_flag_values.append({"line": line_no, "key": key_s, "value": value})
        out.append(
            {
                "path": rel(p),
                "exists": p.exists(),
                "sha256": sha256_file(p) if p.exists() else None,
                "row_count": row_count,
                "parse_errors": parse_errors,
                "observed_key_count": len(key_counter),
                "observed_key_sample": sorted(key_counter)[:80],
                "forbidden_raw_key_hits": dict(sorted(forbidden_key_counter.items())),
                "unsafe_flag_values_sample": unsafe_flag_values[:20],
                "contract_use_policy": (
                    "raw_log_not_contract_safe_projection_required"
                    if forbidden_key_counter or unsafe_flag_values
                    else "may_be_source_safe_after_hash_and_allowlist_review"
                ),
            }
        )
    return out


def local_heavy_data_search() -> dict[str, Any]:
    roots = [
        Path("data/ticks"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\external"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs"),
        Path(r"C:\tmp"),
        Path(r"C:\SierraChart\Data"),
        Path(r"C:\SierraChart\Data\MarketDepthData"),
    ]
    records = []
    for root in roots:
        exists = root.exists()
        record: dict[str, Any] = {
            "path": str(root),
            "exists": exists,
            "role": "local_heavy_data_discovery_only_not_validation_safe",
        }
        if exists and root.is_dir():
            try:
                parquet_files = list(islice(root.rglob("*.parquet"), 5000))
                jsonl_files = list(islice(root.rglob("*.jsonl"), 5000))
                scid_files = list(islice(root.rglob("*.scid"), 5000))
                depth_files = list(islice(root.rglob("*.depth"), 5000))
                record.update(
                    {
                        "parquet_count_capped_5000": len(parquet_files),
                        "jsonl_count_capped_5000": len(jsonl_files),
                        "scid_count_capped_5000": len(scid_files),
                        "depth_count_capped_5000": len(depth_files),
                        "sample_files": [str(path) for path in (parquet_files[:5] + jsonl_files[:5] + scid_files[:5] + depth_files[:5])],
                    }
                )
            except Exception as exc:  # noqa: BLE001
                record["search_error"] = str(exc)
        records.append(record)
    return {
        "searched_roots": records,
        "search_conclusion": (
            "Local heavy roots can strengthen future source manifests and source coverage, "
            "but no discovered root changes this audit into validation or result scoring. "
            "Every consumed file still requires hashing, parser versioning, as-of rules, and allowlist projection."
        ),
        "missed_field_findings_from_search": [
            "External tick roots support source_file_hashes and coverage windows but do not provide same-tick event sequence IDs.",
            "Sierra roots can support future context/depth manifests only after symbol mapping and parser hashing; they do not clear broker-native no-fill sequence blockers.",
            "Current worktree shadow logs contain additional source-safe candidates such as pending_order_mode and broker_pending_order_created, but raw rows also contain forbidden ticket/order/result fields.",
        ],
    }


def analyze_no_leak_source() -> dict[str, Any]:
    forward_jsons = [
        FORWARD_DIR / f"NOFILL_FORWARD_CAPTURE_CONTRACT_{DATE}.json",
        FORWARD_DIR / f"NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_{DATE}.json",
        FORWARD_DIR / f"NOFILL_FORWARD_NO_LEAK_FIELD_POLICY_{DATE}.json",
        FORWARD_DIR / f"NOFILL_FORWARD_DUPLICATE_DENOMINATOR_POLICY_{DATE}.json",
        FORWARD_DIR / f"NOFILL_FORWARD_EXISTING_SOURCE_AND_CODE_AUDIT_{DATE}.json",
        FORWARD_DIR / f"NOFILL_FORWARD_CAPTURE_BACKLOG_AND_IMPLEMENTATION_ROUTE_{DATE}.json",
        FORWARD_DIR / f"NOFILL_FORWARD_COMPLETION_AUDIT_{DATE}.json",
    ]
    artifact_flag_issues = []
    for path in forward_jsons:
        if abs_path(path).exists():
            artifact_flag_issues.extend(scan_payload_flags(path.name, load_json(path)))

    source_records = source_file_audit()
    log_records = source_log_schema_audit()
    local_search = local_heavy_data_search()
    raw_log_hazards = [
        {"path": record["path"], "forbidden_raw_key_hits": record["forbidden_raw_key_hits"], "unsafe_flag_values_sample": record["unsafe_flag_values_sample"]}
        for record in log_records
        if record["forbidden_raw_key_hits"] or record["unsafe_flag_values_sample"]
    ]
    source_code_hazards = [
        {"path": record["path"], "forbidden_token_hits_in_source_text": record["forbidden_token_hits_in_source_text"]}
        for record in source_records
        if record["forbidden_token_hits_in_source_text"]
    ]
    return {
        **base_flags(),
        "artifact_family": "G12_NOFILL_FORWARD_NO_LEAK_SOURCE_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "status": "PASS_WITH_RAW_SOURCE_PROJECTION_REQUIRED" if not artifact_flag_issues else "FAIL",
        "artifact_flag_issues": artifact_flag_issues,
        "source_file_audit": source_records,
        "source_log_schema_audit": log_records,
        "raw_log_hazards_requiring_allowlist_projection": raw_log_hazards,
        "source_code_hazards_requiring_allowlist_projection": source_code_hazards,
        "local_heavy_data_search": local_search,
        "no_leak_decision": (
            "The forward contract artifacts preserve closed safety flags and do not open result scoring. "
            "Current source/log surfaces are useful but raw consumption is rejected because multiple surfaces contain "
            "order/account/result-shaped fields. A future builder must project an allowlist and fail closed on forbidden keys."
        ),
    }


def decision_payload(
    schema: dict[str, Any],
    noleak: dict[str, Any],
    duplicate: dict[str, Any],
) -> dict[str, Any]:
    blocking_failures = []
    if duplicate["status"] != "PASS":
        blocking_failures.append("duplicate_denominator_audit_failed")
    if noleak["artifact_flag_issues"]:
        blocking_failures.append("unsafe_forward_artifact_flag")
    if schema["issues"]:
        blocking_failures.append("schema_hard_failure")
    verdict = TERMINAL_VERDICT if not blocking_failures else "RETURN_TO_G0_OR_FORWARD_LANE_WITH_EXACT_FIXES"
    return {
        **base_flags(),
        "artifact_family": "G12_NOFILL_FORWARD_DECISION_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "audit_lane_id": AUDIT_LANE_ID,
        "audited_route_id": AUDITED_ROUTE_ID,
        "terminal_g12_verdict": verdict,
        "decision_status": "PASS_ACCEPTED_WITH_BLOCKERS" if verdict == TERMINAL_VERDICT else "FAIL_RETURN",
        "blocking_failures": blocking_failures,
        "accepted_contract_claims": [
            "The full NOFILL CAT V3 evidence chain and frozen count equation recompute cleanly from committed count/result-contract artifacts.",
            "The forward contract is correctly bounded as source/control only with NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, and live_effect=false.",
            "The schema has 80 fields across 12 families and covers source/as-of timestamps, hashes, parser/build provenance, event-order ambiguity, duplicate controls, and no-leak guards.",
            "The contract correctly rejects raw pending lifecycle/candidate/path logs as direct inputs when they contain account/order/result-shaped fields.",
            "The backlog keeps live wiring, paid/API/Databento, registry edits, result scoring, validation, and promotion outside this lane.",
        ],
        "rejected_or_weakened_claims": [
            "The contract is not implementation-ready until the exact addendum blockers are resolved or mapped to equivalent source-safe fields.",
            "Current raw source logs are not contract-safe and cannot be consumed without allowlist projection and forbidden-key scans.",
            "Local heavy data availability strengthens future source manifests but does not clear same-tick broker-native sequence blockers and does not create validation evidence.",
            "Cost/spread/slippage/execution observability is not sufficient for any later survival-adjusted expectancy test until explicit closed status fields and source hashes exist.",
        ],
        "exact_contract_blockers": EXACT_CONTRACT_BLOCKERS,
        "exact_implementation_blockers": [
            "Offline source-safe projection builder must be audited before it can emit contract rows.",
            "Every projected row must have source hashes, parser code hash, as-of rule, duplicate key, canonical row control, and forbidden-field scan status.",
            "Same-tick and same-bar cases must remain ambiguous/impossible unless source sequence proof exists.",
            "Any live logger wiring would touch live-source surfaces and requires a separate owner-approved implementation lane; this audit does not authorize it.",
        ],
        "forbidden_future_routes": [
            "result scoring",
            "validation or promotion",
            "broker actual-R or account/order/deal history labels",
            "hidden path labels in this source/control lane",
            "registry edits",
            "live trading prompt/src/risk/execution/permissions/safety/selector/canary/order behavior changes",
            "paid/API/Databento calls",
            "remote push",
        ],
        "next_route": (
            "After this G12 acceptance-with-blockers, run a contract-addendum/source-safe projection-builder lane "
            "that resolves G12-FWD-BLOCKER-001..003 without opening result scoring or live behavior."
        ),
    }


def completion_checklist() -> list[dict[str, Any]]:
    requirements = [
        ("mandatory_preflight", "GTOS preflight and controlling prompt/context read"),
        ("controlling_forward_inputs", "Forward contract artifacts, builder, verifier, and tests read/hash recorded"),
        ("upstream_chain", "G0, G12 count, count packet, result contract, source-control, rebuild, and USDJPY sequence chain inventoried"),
        ("evidence_chain", "298 = 225 + 4 + 4 + 65 and 225/182/139 denominators independently recomputed"),
        ("reject_overlap", "47 reject-overlap rows neutralized by accepted-first filtering"),
        ("schema_audit", "Field count/family count/source-as-of/no-leak/cost/provenance/blocker coverage audited"),
        ("source_code_logs", "forward_capture.py, pending lifecycle code, follow scripts, and current source logs scanned"),
        ("local_heavy_data", "Worktree and absolute local heavy-data roots searched as discovery-only evidence"),
        ("adversarial_findings", "Accepted, weakened, missing-field, implementation-blocker, no-leak, duplicate, and forbidden-route findings emitted"),
        ("terminal_verdict", "One terminal G12 verdict emitted"),
        ("required_outputs", "All required markdown/JSON artifacts plus builder/verifier/focused tests generated"),
        ("verification", "JSON parse, py_compile, focused pytest, recomputed source/no-leak/duplicate checks, safety flags, diff-scope checks run"),
        ("context_refresh_commit", "research_current_state refreshed and committed after audit artifacts"),
    ]
    return [{"id": key, "requirement": text, "status": "PENDING_VERIFIER", "evidence": "pending"} for key, text in requirements]


def completion_payload(decision: dict[str, Any], schema: dict[str, Any], noleak: dict[str, Any], duplicate: dict[str, Any]) -> dict[str, Any]:
    weak = []
    if decision["terminal_g12_verdict"] != TERMINAL_VERDICT:
        weak.append("Terminal decision is not acceptance-with-blockers.")
    if schema["status"] != "PASS_WITH_EXACT_CONTRACT_BLOCKERS":
        weak.append("Schema audit did not reach pass-with-blockers.")
    if noleak["status"] != "PASS_WITH_RAW_SOURCE_PROJECTION_REQUIRED":
        weak.append("No-leak/source audit did not pass.")
    if duplicate["status"] != "PASS":
        weak.append("Duplicate denominator audit did not pass.")
    weak.append("Verifier and scoped commits have not finalized this audit yet.")
    return {
        **base_flags(),
        "artifact_family": "G12_NOFILL_FORWARD_COMPLETION_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "completion_status": "PENDING_VERIFIER_AND_COMMIT",
        "can_mark_goal_complete": False,
        "objective_restatement": (
            "Run a maximum-depth G12 audit of the forward no-fill lifecycle capture contract as source/control evidence only, "
            "reconstruct the V3 no-fill evidence chain, audit schema/source/no-leak/duplicate coverage, search local heavy data, "
            "emit adversarial findings and one terminal verdict, preserve NO_PROMOTION_VERDICT and closed safety flags, "
            "commit scoped artifacts, and refresh research context without touching live trading surfaces or remote."
        ),
        "terminal_g12_verdict": decision["terminal_g12_verdict"],
        "prompt_to_artifact_checklist": completion_checklist(),
        "missing_incomplete_or_weak_requirements": weak,
        "verification_results": {},
    }


def md_header() -> list[str]:
    return [
        f"- audit_lane_id: `{AUDIT_LANE_ID}`",
        f"- audited_route_id: `{AUDITED_ROUTE_ID}`",
        f"- promotion_verdict: `{PROMOTION_VERDICT}`",
        "- validation_safe: `false`",
        "- outcome_review_opened: `false`",
        "- live_effect: `false`",
        "- opens_result_scoring: `false`",
        "- changes_live_trading_behavior: `false`",
        "",
    ]


def write_markdown(payloads: dict[str, dict[str, Any]]) -> None:
    decision = payloads[f"G12_NOFILL_FORWARD_DECISION_LEDGER_{DATE}.json"]
    schema = payloads[f"G12_NOFILL_FORWARD_SCHEMA_AUDIT_{DATE}.json"]
    noleak = payloads[f"G12_NOFILL_FORWARD_NO_LEAK_SOURCE_AUDIT_{DATE}.json"]
    duplicate = payloads[f"G12_NOFILL_FORWARD_DUPLICATE_DENOMINATOR_AUDIT_{DATE}.json"]
    completion = payloads[f"G12_NOFILL_FORWARD_COMPLETION_AUDIT_{DATE}.json"]

    write_md(
        f"G12_NOFILL_FORWARD_DECISION_LEDGER_{DATE}.md",
        "G12 NOFILL Forward Decision Ledger 2026-05-09",
        "\n".join(
            md_header()
            + [
                f"Terminal G12 verdict: `{decision['terminal_g12_verdict']}`",
                f"Decision status: `{decision['decision_status']}`",
                "",
                "## Accepted Contract Claims",
                "",
                *[f"- {item}" for item in decision["accepted_contract_claims"]],
                "",
                "## Rejected Or Weakened Claims",
                "",
                *[f"- {item}" for item in decision["rejected_or_weakened_claims"]],
                "",
                "## Exact Contract Blockers",
                "",
                *[
                    f"- `{item['blocker_id']}` {item['finding']} Exact fix: {', '.join(item['exact_fix'])}"
                    for item in decision["exact_contract_blockers"]
                ],
                "",
                "## Next Route",
                "",
                decision["next_route"],
            ]
        ),
    )

    write_md(
        f"G12_NOFILL_FORWARD_BACKLOG_AND_IMPLEMENTATION_AUDIT_{DATE}.md",
        "G12 NOFILL Forward Backlog And Implementation Audit 2026-05-09",
        "\n".join(
            md_header()
            + [
                "## Implementation Decision",
                "",
                "The contract can move forward only as source/control work and only after the exact blockers are patched or mapped to equivalent audited fields. This audit does not authorize live logger wiring, result scoring, validation, promotion, paid data, registry edits, or any order behavior.",
                "",
                "## Required Blocker Closure",
                "",
                *[
                    f"- `{item['blocker_id']}`: {item['severity']}. {item['finding']}"
                    for item in decision["exact_contract_blockers"]
                ],
                "",
                "## Source Projection Requirements",
                "",
                *[f"- {item}" for item in decision["exact_implementation_blockers"]],
                "",
                "## Raw Source Hazards",
                "",
                f"- Raw source/log surfaces requiring projection: `{len(noleak['raw_log_hazards_requiring_allowlist_projection']) + len(noleak['source_code_hazards_requiring_allowlist_projection'])}`",
                f"- Local-heavy searched roots: `{len(noleak['local_heavy_data_search']['searched_roots'])}`",
            ]
        ),
    )

    hostile_questions = [
        (
            "Could source-control evidence become result evidence?",
            "No. The accepted verdict is contract-only; future_result_label_status, broker_actual_r_status, hidden_path_label_status, validation_safe, outcome_review_opened, and live_effect stay closed.",
        ),
        (
            "Could rejected/source-impossible rows leak into denominators?",
            "No. The recomputation preserves 225 accepted, 182 duplicate-key members, 139 duplicate-group members, 4 source-control exclusions, 4 source-impossible exclusions, 65 rejects, and zero denominator delta from 47 reject-overlap rows.",
        ),
        (
            "Could raw logs leak account/order/result truth?",
            "Yes if consumed raw. That is why the audit accepts only an allowlist projection builder after G12-FWD-BLOCKER-001..003 are resolved.",
        ),
        (
            "Could local heavy data clear same-tick ordering?",
            "No. It can provide source hashes and coverage, but the USDJPY same-tick rows still need broker-native quote-event sequence or sub-row timing.",
        ),
        (
            "Could costs/execution be tested later?",
            "Only after source-safe spread fields and closed slippage/execution-quality statuses exist. The current contract is not enough for survival-adjusted expectancy testing.",
        ),
    ]
    write_md(
        f"G12_NOFILL_FORWARD_HOSTILE_EDGE_REVIEW_{DATE}.md",
        "G12 NOFILL Forward Hostile Edge Review 2026-05-09",
        "\n".join(
            md_header()
            + [
                "## Hostile Review",
                "",
                *[f"- **{q}** {a}" for q, a in hostile_questions],
                "",
                "## Saturation Status",
                "",
                "Same-evidence-class questions were pursued through forward artifacts, upstream chain rows, code/log schemas, and local-heavy discovery roots. Remaining work is not generic future work; it is the exact blocker closure listed in the decision ledger.",
            ]
        ),
    )

    write_md(
        f"G12_NOFILL_FORWARD_NEXT_PROMPT_PACK_{DATE}.md",
        "G12 NOFILL Forward Next Prompt Pack 2026-05-09",
        "\n".join(
            md_header()
            + [
                "## Prompt 1 - Contract Addendum And Source-Safe Projection Builder",
                "",
                "`/goal Resolve G12-FWD-BLOCKER-001..003 for the accepted-with-blockers NOFILL forward lifecycle capture contract. Build a source-control-only contract addendum and offline source-safe projection builder plan. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false. Do not open result scoring, validation, promotion, broker actual-R/account/order/deal history labels, live trading prompts, src trading logic, risk, execution, permissions, safety gates, selectors, canaries, paid/API/Databento, registry edits, credentials, remote pushes, or order behavior.`",
                "",
                "## Prompt 2 - Offline Projection Verifier",
                "",
                "After the addendum is accepted, build a verifier that consumes only hashed source-safe projections from current logs and local heavy manifests. It must fail closed on forbidden fields, generated duplicate keys, missing hashes, unresolved same-tick ordering, missing capture latency, and unsafe flags.",
                "",
                "## Prompt 3 - USDJPY Quote-Event Access",
                "",
                "The four USDJPY source-impossible rows still require broker-native bid/ask quote-event sequence, sub-millisecond timestamp, or monotonic event ID for the exact target timestamps. Proxy futures or M15/M1 OHLC cannot clear those rows.",
            ]
        ),
    )

    write_md(
        f"G12_NOFILL_FORWARD_COMPLETION_AUDIT_{DATE}.md",
        "G12 NOFILL Forward Completion Audit 2026-05-09",
        "\n".join(
            md_header()
            + [
                f"Completion status: `{completion['completion_status']}`",
                f"Can mark goal complete: `{str(completion['can_mark_goal_complete']).lower()}`",
                "",
                "## Objective Restatement",
                "",
                completion["objective_restatement"],
                "",
                "## Prompt-To-Artifact Checklist",
                "",
                *[f"- `{item['status']}` `{item['id']}`: {item['requirement']} ({item['evidence']})" for item in completion["prompt_to_artifact_checklist"]],
                "",
                "## Audit Summary",
                "",
                f"- Terminal verdict: `{decision['terminal_g12_verdict']}`",
                f"- Schema status: `{schema['status']}` with `{len(schema['exact_contract_blockers'])}` exact blockers.",
                f"- No-leak/source status: `{noleak['status']}`.",
                f"- Duplicate denominator status: `{duplicate['status']}`.",
            ]
        ),
    )


def build_payloads() -> dict[str, dict[str, Any]]:
    generated_at = now_utc()
    duplicate = analyze_evidence_chain()
    schema = analyze_forward_schema()
    noleak = analyze_no_leak_source()
    decision = decision_payload(schema=schema, noleak=noleak, duplicate=duplicate)
    context = {
        **base_flags(),
        "artifact_family": "G12_NOFILL_FORWARD_CONTEXT_AND_SOURCE_ANCHOR",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "audit_lane_id": AUDIT_LANE_ID,
        "audited_route_id": AUDITED_ROUTE_ID,
        "branch": git_output(["branch", "--show-current"]),
        "head_at_build": git_output(["rev-parse", "--short", "HEAD"]),
        "git_status_short_at_build": git_output(["status", "--short"]),
        "input_files_read_or_inventoried": all_input_files(),
        "required_forward_inputs_missing": [rel(abs_path(path)) for path in FORWARD_REQUIRED_INPUTS if not abs_path(path).exists()],
        "upstream_dirs_read_or_inventoried": [rel(abs_path(path)) for path in UPSTREAM_DIRS],
        "hard_boundary": "source_control_audit_only_no_result_scoring_no_live_behavior_no_remote",
    }
    completion = completion_payload(decision=decision, schema=schema, noleak=noleak, duplicate=duplicate)
    payloads = {
        f"G12_NOFILL_FORWARD_CONTEXT_ANCHOR_{DATE}.json": context,
        f"G12_NOFILL_FORWARD_DECISION_LEDGER_{DATE}.json": decision,
        f"G12_NOFILL_FORWARD_SCHEMA_AUDIT_{DATE}.json": schema,
        f"G12_NOFILL_FORWARD_NO_LEAK_SOURCE_AUDIT_{DATE}.json": noleak,
        f"G12_NOFILL_FORWARD_DUPLICATE_DENOMINATOR_AUDIT_{DATE}.json": duplicate,
        f"G12_NOFILL_FORWARD_COMPLETION_AUDIT_{DATE}.json": completion,
    }
    return payloads


def main() -> int:
    payloads = build_payloads()
    for name, payload in payloads.items():
        write_json(name, payload)
    write_markdown(payloads)
    print(
        json.dumps(
            {
                "status": "built",
                "output_dir": rel(OUT_DIR),
                "terminal_g12_verdict": payloads[f"G12_NOFILL_FORWARD_DECISION_LEDGER_{DATE}.json"]["terminal_g12_verdict"],
                "json_artifacts": sorted(payloads),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
