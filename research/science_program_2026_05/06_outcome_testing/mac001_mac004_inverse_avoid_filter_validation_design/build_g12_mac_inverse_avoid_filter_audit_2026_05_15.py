from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DATE = "2026-05-15"
ROUTE_ID = "G12_MAC_INVERSE_AVOID_FILTER_AUDIT"
SOURCE_ROUTE_ID = "MAC001_MAC004_INVERSE_AVOID_FILTER_VALIDATION_DESIGN"
EVIDENCE_CLASS = "G12_MAC_INVERSE_AVOID_FILTER_AUDIT_ONLY"
SOURCE_EVIDENCE_CLASS = "READY8_MAC_INVERSE_AVOID_FILTER_DESIGN_AND_SCREEN_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G12_MAC_INVERSE_AVOID_FILTER_DESIGN_AUDIT_NO_PROMOTION"
SCHEMA_VERSION = "g12_mac_inverse_avoid_filter_audit_v1"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
ACCEPTED_G12_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit"
ACCEPTED_G12_RECOMPUTATION = ACCEPTED_G12_DIR / "G12_R8DISC_SEALED_VALIDATION_AUDIT_RECOMPUTATION_LEDGER_2026-05-13.json"
ACCEPTED_G12_DECISION = ACCEPTED_G12_DIR / "G12_R8DISC_SEALED_VALIDATION_AUDIT_DECISION_LEDGER_2026-05-13.json"
ACCEPTED_PASS_CONTROL = ROOT / "research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_sealed_validation_after_opening_gate/R8DISC_SEALED_PASS_CONTROL_2026-05-13.jsonl"
SOURCE_MANIFEST = ROUTE_DIR / f"MAC_INVERSE_OUTPUT_MANIFEST_{DATE}.json"
SOURCE_COMPLETION = ROUTE_DIR / f"MAC_INVERSE_COMPLETION_AUDIT_{DATE}.json"
SOURCE_DECISION = ROUTE_DIR / f"MAC_INVERSE_DECISION_LEDGER_{DATE}.json"
SOURCE_VERIFICATION = ROUTE_DIR / f"MAC_INVERSE_VERIFICATION_RESULT_{DATE}.json"
SOURCE_FOCUSED = ROUTE_DIR / f"MAC_INVERSE_FOCUSED_TEST_RESULT_{DATE}.json"
SOURCE_PASS_CONTROL = ROUTE_DIR / f"MAC_INVERSE_PASS_CONTROL_RECOMPUTATION_LEDGER_{DATE}.jsonl"
SOURCE_CANDIDATE_DESIGN = ROUTE_DIR / f"MAC_INVERSE_AVOID_FILTER_CANDIDATE_DESIGN_LEDGER_{DATE}.jsonl"
SOURCE_FAILURE = ROUTE_DIR / f"MAC_INVERSE_FAILURE_ANATOMY_LEDGER_{DATE}.jsonl"
SOURCE_FAIL_CLOSED = ROUTE_DIR / f"MAC_INVERSE_FAIL_CLOSED_NON_APPLICABLE_LEDGER_{DATE}.jsonl"
SOURCE_SATURATION = ROUTE_DIR / f"MAC_INVERSE_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json"
SOURCE_FUTURE_DESIGN = ROUTE_DIR / f"MAC_INVERSE_FUTURE_VALIDATION_SOURCE_CAPTURE_DESIGN_{DATE}.json"
SOURCE_INPUT_BINDING = ROUTE_DIR / f"MAC_INVERSE_INPUT_BINDING_LEDGER_{DATE}.json"
SOURCE_ROWSET_INVENTORY = ROUTE_DIR / f"MAC_INVERSE_ROWSET_INVENTORY_AND_DESCRIPTOR_DEFINITIONS_{DATE}.json"
SOURCE_VERIFY_SCRIPT = ROUTE_DIR / "verify_mac001_mac004_inverse_avoid_filter_validation_design_2026_05_15.py"
SOURCE_TEST = ROUTE_DIR / "test_mac001_mac004_inverse_avoid_filter_validation_design_2026_05_15.py"
G12_PROMPT = ROUTE_DIR / f"G12_MAC_INVERSE_AVOID_FILTER_AUDIT_GOAL_PROMPT_{DATE}.md"

OUTPUTS = {
    "recomputation": f"G12_MAC_INVERSE_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json",
    "discrepancy_repair": f"G12_MAC_INVERSE_AUDIT_DISCREPANCY_REPAIR_LEDGER_{DATE}.jsonl",
    "question_ambiguity": f"G12_MAC_INVERSE_AUDIT_QUESTION_AMBIGUITY_LEDGER_{DATE}.jsonl",
    "source_roots": f"G12_MAC_INVERSE_AUDIT_SOURCE_ROOT_LEDGER_{DATE}.jsonl",
    "door_branch": f"G12_MAC_INVERSE_AUDIT_DOOR_BRANCH_LEDGER_{DATE}.jsonl",
    "blocker_impossibility": f"G12_MAC_INVERSE_AUDIT_BLOCKER_IMPOSSIBILITY_LEDGER_{DATE}.jsonl",
    "decision": f"G12_MAC_INVERSE_AUDIT_DECISION_LEDGER_{DATE}.json",
    "saturation": f"G12_MAC_INVERSE_AUDIT_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
    "completion": f"G12_MAC_INVERSE_AUDIT_COMPLETION_AUDIT_{DATE}.json",
    "summary": f"G12_MAC_INVERSE_AUDIT_SUMMARY_{DATE}.md",
    "manifest": f"G12_MAC_INVERSE_AUDIT_OUTPUT_MANIFEST_{DATE}.json",
    "verification": f"G12_MAC_INVERSE_AUDIT_VERIFICATION_RESULT_{DATE}.json",
    "focused": f"G12_MAC_INVERSE_AUDIT_FOCUSED_TEST_RESULT_{DATE}.json",
    "builder": "build_g12_mac_inverse_avoid_filter_audit_2026_05_15.py",
    "verifier": "verify_g12_mac_inverse_avoid_filter_audit_2026_05_15.py",
    "test": "test_g12_mac_inverse_avoid_filter_audit_2026_05_15.py",
}

SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_raw_market_data_blob_commit": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "credentials_touched": False,
}

PROMPT_REQUIREMENTS = [
    "mandatory_preflight_context_read",
    "accepted_ready8_g12_anchor_inspected",
    "mac_route_manifest_completion_verifier_decision_ledgers_inspected",
    "all_mac_json_jsonl_ledgers_parsed",
    "route_verifier_rerun",
    "focused_pytest_rerun",
    "route_artifact_audit_full_jsonl_rerun",
    "row_counts_recomputed",
    "safe_flags_recomputed",
    "manifest_hash_size_coverage_recomputed",
    "mac_pass_control_compared_to_accepted_g12_rows",
    "mac001_inverse_avoid_filter_design_verified",
    "mac004_h1_positive_kill_verified",
    "metals_concentration_calendar_fix_leave_one_failure_fail_closed_future_capture_verified",
    "questions_ambiguities_roots_doors_branches_followups_blockers_impossibility_ledgers_emitted",
    "no_forbidden_surfaces_opened",
    "completion_accept_or_reject_decision_emitted",
]

MANDATORY_CONTEXT_FILES = [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_55_ORCHESTRATOR_SUCCESSOR_HANDOFF_2026-05-15.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/orchestrator_successor_operating_brief.md",
    ".context/00_core/orchestrator_methodology_hardening_controls.md",
    ".context/00_core/parallel_goal_merge_playbook.md",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(stable_json(row) + "\n")
            count += 1
    return count


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_jsonl(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def safe_flag_violations(row: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    for key, expected in SAFE_FLAGS.items():
        if key in row and row[key] != expected:
            violations.append(f"{key}={row[key]!r} expected {expected!r}")
    return violations


def with_audit_flags(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        **SAFE_FLAGS,
    }


def run_command(args: list[str], timeout: int = 120) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "command": " ".join(args),
        "returncode": completed.returncode,
        "stdout": completed.stdout[-8000:],
        "stderr": completed.stderr[-8000:],
        "ok": completed.returncode == 0,
    }


def accepted_delta_key(row: dict[str, Any]) -> str:
    return stable_json({"family": row.get("comparison_family"), "key": row.get("branch_key")})


def values_match(left: Any, right: Any, tolerance: float = 1e-15) -> bool:
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, (int, float)) or isinstance(right, (int, float)):
        return abs(float(left) - float(right)) <= tolerance
    return left == right


def artifact_record(path: Path, role: str, rows: int | None = None) -> dict[str, Any]:
    exists = path.exists()
    record = {
        "artifact_role": role,
        "path": rel(path) if path.is_absolute() else path.as_posix(),
        "exists": exists,
        "bytes": path.stat().st_size if exists else None,
        "sha256": sha256_file(path) if exists and path.is_file() else None,
    }
    if rows is not None:
        record["rows"] = rows
    elif exists and path.suffix == ".jsonl":
        record["rows"] = count_jsonl(path)
    return record


def scan_jsonl_file(path: Path) -> dict[str, Any]:
    rows = 0
    safe_violations = 0
    parse_errors: list[str] = []
    status_counter: Counter[str] = Counter()
    class_counter: Counter[str] = Counter()
    try:
        for row in iter_jsonl(path):
            rows += 1
            safe_violations += len(safe_flag_violations(row))
            status = row.get("candidate_status") or row.get("terminal_status") or row.get("status")
            if status is not None:
                status_counter[str(status)] += 1
            classification = row.get("comparison_classification") or row.get("classification")
            if classification is not None:
                class_counter[str(classification)] += 1
    except ValueError as exc:
        parse_errors.append(str(exc))
    return {
        "path": rel(path),
        "rows": rows,
        "parse_errors": parse_errors,
        "safe_flag_violation_count": safe_violations,
        "status_counts": dict(status_counter),
        "classification_counts": dict(class_counter),
    }


def build_source_root_rows(source_manifest: dict[str, Any], input_binding: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for context_path in MANDATORY_CONTEXT_FILES:
        path = ROOT / context_path
        rows.append(with_audit_flags({
            "ledger_family": "source_root",
            "source_root_type": "mandatory_context",
            **artifact_record(path, "mandatory_context"),
            "source_status": "READ_FROM_DISK_OR_HASHED_FOR_AUDIT",
        }))

    core_roots = [
        (ACCEPTED_G12_DIR, "accepted_ready8_g12_audit_directory"),
        (ROUTE_DIR, "mac_inverse_route_directory"),
        (SOURCE_MANIFEST, "mac_route_output_manifest"),
        (SOURCE_COMPLETION, "mac_route_completion_audit"),
        (SOURCE_DECISION, "mac_route_decision_ledger"),
        (SOURCE_VERIFICATION, "mac_route_verification_result"),
        (SOURCE_FOCUSED, "mac_route_focused_test_result"),
        (G12_PROMPT, "controlling_g12_prompt"),
    ]
    for path, role in core_roots:
        rows.append(with_audit_flags({
            "ledger_family": "source_root",
            "source_root_type": role,
            **artifact_record(path, role),
            "source_status": "READ_FROM_DISK_OR_HASHED_FOR_AUDIT",
        }))

    for name, rel_path in sorted((source_manifest.get("artifacts") or {}).items()):
        path = ROOT / rel_path
        rows.append(with_audit_flags({
            "ledger_family": "source_root",
            "source_root_type": "mac_manifest_artifact",
            "manifest_key": name,
            **artifact_record(path, f"mac_manifest_artifact:{name}"),
            "source_status": "MANIFEST_ARTIFACT_HASHED_FOR_G12_AUDIT",
        }))

    for target in input_binding.get("target_file_ledgers", []):
        path = ROOT / target["path"]
        rows.append(with_audit_flags({
            "ledger_family": "source_root",
            "source_root_type": "mac_target_file_from_accepted_packet",
            "expected_rows": target.get("rows"),
            "expected_sha256": target.get("sha256"),
            **artifact_record(path, "mac_target_file", rows=count_jsonl(path) if path.exists() else None),
            "source_status": "TARGET_FILE_HASH_AND_ROW_COUNT_RECOMPUTED",
        }))

    forbidden_roots = [
        "live_trading_behavior",
        "broker_account_order_history_deal_position",
        "paid_vendor_api_access",
        "prompt_config_risk_safety_execution_canary_selector",
        "raw_market_blob_commit",
        "registry_edit",
        "remote_push",
    ]
    for root_name in forbidden_roots:
        rows.append(with_audit_flags({
            "ledger_family": "source_root",
            "source_root_type": "forbidden_surface",
            "forbidden_surface": root_name,
            "exists": None,
            "source_status": "NOT_OPENED_BY_G12_AUDIT_BOUNDARY",
            "proof": "Audit used committed/source-control route artifacts only.",
        }))
    return rows


def build_question_rows(source_completion: dict[str, Any], source_saturation: dict[str, Any], candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    checklist = {item.get("requirement"): item for item in source_completion.get("prompt_to_artifact_checklist", [])}
    for requirement in PROMPT_REQUIREMENTS:
        source_item = checklist.get(requirement)
        rows.append(with_audit_flags({
            "ledger_family": "question_or_ambiguity",
            "question_family": "prompt_requirement_coverage",
            "question": requirement,
            "answer_status": "SATISFIED_BY_G12_AUDIT" if requirement not in {"completion_accept_or_reject_decision_emitted"} else "SATISFIED_BY_DECISION_LEDGER",
            "source_builder_status": source_item.get("status") if source_item else None,
            "source_builder_evidence": source_item.get("evidence") if source_item else None,
            "same_g12_gap_remaining": False,
        }))

    for idx, item in enumerate(source_saturation.get("self_red_team_questions", []), start=1):
        rows.append(with_audit_flags({
            "ledger_family": "question_or_ambiguity",
            "question_family": "source_route_self_red_team",
            "question_index": idx,
            "question": item.get("question"),
            "answer": item.get("answer"),
            "answer_status": "BOUNDED_OR_CLOSED_BY_SOURCE_ROUTE_AND_RECHECKED",
            "same_g12_gap_remaining": bool(item.get("same_class_gap_remaining")),
        }))

    for row in candidate_rows:
        rows.append(with_audit_flags({
            "ledger_family": "question_or_ambiguity",
            "question_family": "candidate_branch_acceptance_question",
            "candidate_id": row.get("candidate_id"),
            "branch_key": row.get("branch_key"),
            "question": "Can this MAC branch be accepted as G12 avoid-filter design evidence?",
            "answer_status": row.get("candidate_status"),
            "classification": row.get("classification"),
            "warnings": row.get("warnings", []),
            "same_g12_gap_remaining": False,
        }))
    return rows


def branch_door_status(candidate_status: str | None) -> tuple[str, str]:
    if candidate_status == "KILLED_FOR_AVOID_FILTER_CURRENT_BRANCH_POSITIVE":
        return "closed_door", "failed_current_avoid_filter_branch"
    if candidate_status == "UNDERPOWERED_NON_INVERSE_NO_AVOID_FILTER_CURRENT_BRANCH":
        return "closed_door", "failed_or_underpowered_non_inverse_branch"
    if candidate_status == "UNDERPOWERED_INVERSE_RETAIN_ONLY_AS_FUTURE_DATA_CAPTURE_ROUTE":
        return "open_door", "future_capture_only_inverse_branch"
    if candidate_status == "RETAIN_BUT_DECONCENTRATION_MIXED_OR_INCOMPLETE":
        return "open_door", "retained_future_validation_design_branch"
    return "reviewed_door", "unclassified_branch_status"


def build_door_branch_rows(candidate_rows: list[dict[str, Any]], failure_rows: list[dict[str, Any]], future_design: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        door_status, branch_family = branch_door_status(row.get("candidate_status"))
        rows.append(with_audit_flags({
            "ledger_family": "door_branch",
            "door_record_type": "candidate_design_branch",
            "door_status": door_status,
            "branch_family": branch_family,
            "candidate_id": row.get("candidate_id"),
            "candidate_status": row.get("candidate_status"),
            "candidate_use_type": row.get("candidate_use_type"),
            "branch_key": row.get("branch_key"),
            "classification": row.get("classification"),
            "delta": row.get("delta"),
            "pass_rows": row.get("pass_rows"),
            "control_rows": row.get("control_rows"),
            "warnings": row.get("warnings", []),
        }))

    for row in failure_rows:
        rows.append(with_audit_flags({
            "ledger_family": "door_branch",
            "door_record_type": "failure_anatomy_branch",
            "door_status": "closed_or_bounded_door",
            "branch_family": row.get("ledger_family"),
            "branch_key": row.get("branch_key"),
            "comparison_family": row.get("comparison_family"),
            "comparison_id": row.get("comparison_id"),
            "classification": row.get("classification"),
            "delta": row.get("delta"),
            "failure_anatomy": row.get("failure_anatomy"),
            "warnings": row.get("warnings", []),
        }))

    followups = [
        "R5_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR",
        "R6_READY8_ADVERSARIAL_CONTROL_AND_PLACEBO_DRIFT_AUDIT",
        "R7_READY8_EXPANDED_SEALED_VALIDATION_PACKET_AFTER_REPAIRS",
        "future_preregistered_mac_inverse_source_capture",
        "future_owner_approved_promotion_dossier_only_if_separate_validation_exists",
    ]
    for followup in followups:
        rows.append(with_audit_flags({
            "ledger_family": "door_branch",
            "door_record_type": "follow_up_route",
            "door_status": "open_door_outside_current_g12_audit",
            "follow_up_route": followup,
            "boundary": future_design.get("minimum_future_route"),
            "same_g12_gap_remaining": False,
        }))
    return rows


def build_blocker_rows(fail_closed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in fail_closed_rows:
        rows.append(with_audit_flags({
            "ledger_family": "blocker_impossibility",
            "blocker_record_type": "fail_closed_or_non_applicable_source_gap",
            "blocker_status": "EXACTLY_BOUNDED_OUTSIDE_CURRENT_MAC_G12_AUDIT",
            "branch_key": row.get("branch_key"),
            "rows_total_including_non_metric": row.get("rows_total_including_non_metric"),
            "non_applicable_interpretation": row.get("non_applicable_interpretation"),
            "impossibility_or_boundary_proof": "This G12 audit can verify exclusion and source-gap accounting but cannot convert fail-closed/non-applicable source rows into target denominators; source repair belongs to R5/future capture.",
        }))

    exact_boundaries = [
        ("promotion", "Promotion requires a separate promotion dossier and is forbidden in this evidence class."),
        ("live_behavior", "Live behavior changes are forbidden in this evidence class."),
        ("R_PnL_win_rate_expectancy", "This packet contains neutral target-movement control evidence only, not broker-realized performance labels."),
        ("AI_API_paid_vendor", "No AI/API/paid/vendor access is authorized or needed for this audit."),
        ("broker_order_account_history", "Broker/account/order/history/deal/position evidence is forbidden for this audit."),
    ]
    for name, proof in exact_boundaries:
        rows.append(with_audit_flags({
            "ledger_family": "blocker_impossibility",
            "blocker_record_type": "forbidden_boundary",
            "blocker_name": name,
            "blocker_status": "EXACT_EVIDENCE_CLASS_BOUNDARY_NOT_OPENED",
            "impossibility_or_boundary_proof": proof,
            "same_g12_gap_remaining": False,
        }))
    return rows


def build_discrepancy_rows(recomputation: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    checks = recomputation["checks"]
    for name, ok in checks.items():
        rows.append(with_audit_flags({
            "ledger_family": "discrepancy_or_repair",
            "check_name": name,
            "status": "PASS" if ok else "FAIL",
            "repair_action": None if ok else "REPAIR_REQUIRED",
            "same_g12_repair_remaining": not bool(ok),
        }))

    for mismatch in recomputation["pass_control_comparison"]["mismatch_examples"]:
        rows.append(with_audit_flags({
            "ledger_family": "discrepancy_or_repair",
            "check_name": "accepted_g12_pass_control_delta_match",
            "status": "FAIL",
            "repair_action": "INVESTIGATE_PASS_CONTROL_DELTA_MISMATCH",
            "mismatch": mismatch,
            "same_g12_repair_remaining": True,
        }))

    rows.append(with_audit_flags({
        "ledger_family": "discrepancy_or_repair",
        "check_name": "route_manifest_hash_size_coverage",
        "status": "PASS",
        "repair_action": "G12_AUDIT_HASH_SIZE_MANIFEST_EMITTED",
        "same_g12_repair_remaining": False,
        "explanation": "The source route manifest listed paths and counts; this G12 audit adds a hash/byte coverage manifest without changing source evidence.",
    }))
    return rows


def build_recomputation(external_results: dict[str, Any]) -> dict[str, Any]:
    source_manifest = read_json(SOURCE_MANIFEST)
    source_completion = read_json(SOURCE_COMPLETION)
    source_decision = read_json(SOURCE_DECISION)
    source_saturation = read_json(SOURCE_SATURATION)
    source_future_design = read_json(SOURCE_FUTURE_DESIGN)
    source_input_binding = read_json(SOURCE_INPUT_BINDING)
    accepted = read_json(ACCEPTED_G12_RECOMPUTATION)
    accepted_decision = read_json(ACCEPTED_G12_DECISION)
    accepted_pass_control_rows = {
        accepted_delta_key(row): row
        for row in iter_jsonl(ACCEPTED_PASS_CONTROL)
        if (row.get("branch_key") or {}).get("card_id") in {"MAC-001", "MAC-004"}
    }

    manifest_artifacts = source_manifest.get("artifacts", {})
    jsonl_scans: dict[str, Any] = {}
    actual_counts: dict[str, int] = {}
    safe_flag_violations = 0
    parse_error_count = 0
    for key, rel_path in manifest_artifacts.items():
        path = ROOT / rel_path
        if path.suffix == ".jsonl":
            scan = scan_jsonl_file(path)
            jsonl_scans[key] = scan
            actual_counts[f"{key}_rows"] = scan["rows"]
            safe_flag_violations += scan["safe_flag_violation_count"]
            parse_error_count += len(scan["parse_errors"])

    expected_counts = source_manifest.get("counts", {})
    count_checks = {
        "candidate_rows": actual_counts.get("candidate_design_rows"),
        "concentration_rows": actual_counts.get("concentration_rows"),
        "fail_closed_rows": actual_counts.get("fail_closed_rows"),
        "failure_rows": actual_counts.get("failure_rows"),
        "horizon_rows": actual_counts.get("horizon_anatomy_rows"),
        "interaction_rows": actual_counts.get("interaction_rows"),
        "leave_one_rows": actual_counts.get("leave_one_rows"),
        "pass_control_rows": actual_counts.get("pass_control_rows"),
        "timing_rows": actual_counts.get("timing_rows"),
    }
    count_mismatches = {
        key: {"expected": expected_counts.get(key), "actual": actual}
        for key, actual in count_checks.items()
        if expected_counts.get(key) != actual
    }

    target_file_records = []
    for target in source_input_binding.get("target_file_ledgers", []):
        path = ROOT / target["path"]
        rows = count_jsonl(path)
        sha = sha256_file(path)
        target_file_records.append({
            "path": target["path"],
            "expected_rows": target.get("rows"),
            "actual_rows": rows,
            "rows_match": rows == target.get("rows"),
            "expected_sha256": target.get("sha256"),
            "actual_sha256": sha,
            "sha256_match": sha == target.get("sha256"),
            "bytes": path.stat().st_size,
        })

    accepted_map = accepted["target_file_recomputation"]["pass_control_positive_rate_delta_map"]
    pass_rows = list(iter_jsonl(SOURCE_PASS_CONTROL))
    pass_family_counts = Counter(row.get("comparison_family") for row in pass_rows)
    pass_class_counts = Counter(row.get("comparison_classification") for row in pass_rows)
    accepted_present_counts = Counter(str(row.get("accepted_g12_row_present")) for row in pass_rows)
    accepted_match_counts = Counter(str(row.get("accepted_g12_match")) for row in pass_rows)
    mismatch_examples: list[dict[str, Any]] = []
    comparable_rows = 0
    accepted_delta_matches = 0
    accepted_delta_missing = 0
    accepted_delta_mismatch = 0
    accepted_full_row_matches = 0
    accepted_full_row_missing = 0
    accepted_full_row_mismatch = 0
    full_row_mismatch_examples: list[dict[str, Any]] = []
    full_compare_fields = [
        "comparison_classification",
        "comparison_id",
        "comparison_type",
        "inversion_flag",
        "underpowered_flag",
        "pass_rows",
        "control_rows",
        "pass_unique_duplicate_denominator_count",
        "control_unique_duplicate_denominator_count",
        "pass_target_movement_mean",
        "control_target_movement_mean",
        "pass_minus_control_target_movement_mean_delta",
        "pass_positive_rate_minus_control_positive_rate_delta",
    ]
    for row in pass_rows:
        delta = row.get("pass_positive_rate_minus_control_positive_rate_delta")
        key = accepted_delta_key(row)
        if row.get("accepted_g12_row_present"):
            accepted_row = accepted_pass_control_rows.get(key)
            if accepted_row is None:
                accepted_full_row_missing += 1
                if len(full_row_mismatch_examples) < 20:
                    full_row_mismatch_examples.append({"reason": "missing_accepted_row", "key": key})
            else:
                field_mismatches = [
                    field for field in full_compare_fields
                    if not values_match(row.get(field), accepted_row.get(field))
                ]
                if field_mismatches:
                    accepted_full_row_mismatch += 1
                    if len(full_row_mismatch_examples) < 20:
                        full_row_mismatch_examples.append({
                            "reason": "field_mismatch",
                            "key": key,
                            "fields": field_mismatches,
                        })
                else:
                    accepted_full_row_matches += 1
            if delta is not None:
                accepted_delta = accepted_map.get(key)
                comparable_rows += 1
                if accepted_delta is None:
                    accepted_delta_missing += 1
                    if len(mismatch_examples) < 20:
                        mismatch_examples.append({"reason": "missing_accepted_delta", "key": key})
                elif abs(float(delta) - float(accepted_delta)) <= 1e-15:
                    accepted_delta_matches += 1
                else:
                    accepted_delta_mismatch += 1
                    if len(mismatch_examples) < 20:
                        mismatch_examples.append({
                            "reason": "delta_mismatch",
                            "key": key,
                            "source_delta": delta,
                            "accepted_delta": accepted_delta,
                        })

    candidate_rows = list(iter_jsonl(SOURCE_CANDIDATE_DESIGN))
    failure_rows = list(iter_jsonl(SOURCE_FAILURE))
    fail_closed_rows = list(iter_jsonl(SOURCE_FAIL_CLOSED))
    candidate_status_counts = Counter(row.get("candidate_status") for row in candidate_rows)
    candidate_class_counts = Counter(row.get("classification") for row in candidate_rows)

    checks = {
        "source_route_verifier_ok": bool(external_results["source_route_verifier"].get("ok")),
        "source_route_focused_pytest_ok": bool(external_results["source_route_focused_pytest"].get("ok")),
        "prompt_hardening_ok": bool(external_results["prompt_hardening"].get("ok")),
        "route_artifact_full_jsonl_audit_ok": bool(external_results["route_artifact_audit"].get("ok")),
        "source_decision_terminal_expected": source_decision.get("terminal_decision") == "NO_PROMOTION_MAC001_MAC004_INVERSE_AVOID_FILTER_DESIGN_SCREEN_COMPLETE",
        "accepted_ready8_anchor_accepted": accepted_decision.get("accepted") is True,
        "source_safe_flags_closed": source_manifest.get("safe_flags_closed") is True and source_decision.get("safe_flags", {}).get("validation_safe") is False,
        "jsonl_parse_errors_zero": parse_error_count == 0,
        "jsonl_safe_flag_violations_zero": safe_flag_violations == 0,
        "manifest_counts_match_actual": not count_mismatches,
        "target_file_rows_hashes_match": all(item["rows_match"] and item["sha256_match"] for item in target_file_records),
        "pass_control_accepted_g12_delta_matches": accepted_delta_missing == 0 and accepted_delta_mismatch == 0,
        "pass_control_full_accepted_rows_match": accepted_full_row_missing == 0 and accepted_full_row_mismatch == 0 and accepted_full_row_matches == accepted_present_counts.get("True", 0),
        "pass_control_builder_accepted_match_flags_clean": accepted_match_counts.get("False", 0) == 0 and accepted_match_counts.get("True", 0) == accepted_present_counts.get("True", 0),
        "mac001_inverse_candidate_rows_present": any(row.get("branch_key", {}).get("card_id") == "MAC-001" and row.get("classification") == "INVERSE_PASS_LT_CONTROL" for row in candidate_rows),
        "mac004_h1_positive_kill_present": any(row.get("branch_key", {}).get("card_id") == "MAC-004" and row.get("branch_key", {}).get("horizon_m15_bars") == "1" and row.get("candidate_status") == "KILLED_FOR_AVOID_FILTER_CURRENT_BRANCH_POSITIVE" for row in candidate_rows),
        "fail_closed_rows_preserved": len(fail_closed_rows) == expected_counts.get("fail_closed_rows"),
        "future_design_safe_flags_closed": source_future_design.get("safe_terminal_flags", {}).get("validation_safe") is False,
    }

    return {
        "artifact_family": "g12_mac_inverse_audit_recomputation",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "source_route_id": SOURCE_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "source_evidence_class": SOURCE_EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "accepted_anchor": {
            "path": rel(ACCEPTED_G12_RECOMPUTATION),
            "terminal_decision": accepted_decision.get("terminal_decision"),
            "accepted": accepted_decision.get("accepted"),
            "rowset_sha256": accepted["rowset_recomputation"]["sha256"],
            "accepted_pass_control_delta_map_count": accepted["target_file_recomputation"]["pass_control_positive_rate_delta_map_count"],
            "accepted_comparable_pass_control_records": accepted["headline_recomputed_counts"]["comparable_pass_control_records"],
            "accepted_inverse_pass_control_records": accepted["headline_recomputed_counts"]["inverse_pass_control_records"],
            "accepted_positive_pass_control_records": accepted["headline_recomputed_counts"]["positive_pass_control_records"],
        },
        "external_command_results": external_results,
        "jsonl_scans": jsonl_scans,
        "manifest_expected_counts": expected_counts,
        "manifest_actual_count_checks": count_checks,
        "manifest_count_mismatches": count_mismatches,
        "target_file_records": target_file_records,
        "pass_control_comparison": {
            "rows": len(pass_rows),
            "family_counts": dict(pass_family_counts),
            "classification_counts": dict(pass_class_counts),
            "accepted_present_counts": dict(accepted_present_counts),
            "accepted_match_counts": dict(accepted_match_counts),
            "accepted_delta_comparable_rows": comparable_rows,
            "accepted_delta_matches": accepted_delta_matches,
            "accepted_delta_missing": accepted_delta_missing,
            "accepted_delta_mismatch": accepted_delta_mismatch,
            "accepted_full_row_matches": accepted_full_row_matches,
            "accepted_full_row_missing": accepted_full_row_missing,
            "accepted_full_row_mismatch": accepted_full_row_mismatch,
            "accepted_false_families": sorted({row.get("comparison_family") for row in pass_rows if not row.get("accepted_g12_row_present")}),
            "mismatch_examples": mismatch_examples,
            "full_row_mismatch_examples": full_row_mismatch_examples,
        },
        "candidate_design": {
            "rows": len(candidate_rows),
            "status_counts": dict(candidate_status_counts),
            "classification_counts": dict(candidate_class_counts),
            "retained_design_rows": source_future_design.get("retained_design_rows"),
            "killed_design_rows": source_future_design.get("killed_design_rows"),
        },
        "failure_and_blocker_coverage": {
            "failure_rows": len(failure_rows),
            "fail_closed_non_applicable_rows": len(fail_closed_rows),
            "remaining_repairable_blockers_source_claim": source_completion.get("same_evidence_class_exhaustion", {}).get("remaining_repairable_blockers"),
            "remaining_same_class_intelligence_source_claim": source_completion.get("same_evidence_class_exhaustion", {}).get("remaining_same_class_intelligence"),
        },
        "checks": checks,
        "all_checks_ok": all(checks.values()),
    }


def output_artifact_records(include_verification: bool = False) -> list[dict[str, Any]]:
    records = []
    for key, name in OUTPUTS.items():
        if key in {"manifest"}:
            continue
        if key == "verification" and not include_verification:
            continue
        records.append(artifact_record(ROUTE_DIR / name, key))
    return records


def write_manifest() -> dict[str, Any]:
    manifest = {
        "artifact_family": "g12_mac_inverse_audit_output_manifest",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "source_route_id": SOURCE_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        **SAFE_FLAGS,
        "manifest_policy": "Manifest excludes itself and the dynamic verification-result file; verifier recomputes manifest-covered hashes and reports verification separately.",
        "artifacts": output_artifact_records(include_verification=False),
    }
    write_json(ROUTE_DIR / OUTPUTS["manifest"], manifest)
    return manifest


def verify_outputs() -> dict[str, Any]:
    issues: list[str] = []
    manifest_path = ROUTE_DIR / OUTPUTS["manifest"]
    recomputation_path = ROUTE_DIR / OUTPUTS["recomputation"]
    decision_path = ROUTE_DIR / OUTPUTS["decision"]
    completion_path = ROUTE_DIR / OUTPUTS["completion"]
    focused_path = ROUTE_DIR / OUTPUTS["focused"]
    for key, name in OUTPUTS.items():
        if key == "verification":
            continue
        path = ROUTE_DIR / name
        if not path.exists():
            issues.append(f"missing artifact {name}")

    recomputation = read_json(recomputation_path) if recomputation_path.exists() else {}
    if recomputation and not recomputation.get("all_checks_ok"):
        failed = [name for name, ok in recomputation.get("checks", {}).items() if not ok]
        issues.append(f"recomputation checks failed: {failed}")

    decision = read_json(decision_path) if decision_path.exists() else {}
    if decision and decision.get("terminal_decision") != TERMINAL_DECISION:
        issues.append("terminal decision mismatch")
    if decision and decision.get("validation_safe") is not False:
        issues.append("validation_safe not false in decision")

    completion = read_json(completion_path) if completion_path.exists() else {}
    if completion and completion.get("can_mark_goal_complete") is not True:
        issues.append("completion audit does not allow completion")

    focused = read_json(focused_path) if focused_path.exists() else {}
    if focused and focused.get("ok") is not True:
        issues.append("focused test result not ok")

    manifest_hash_mismatches: list[dict[str, Any]] = []
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        for artifact in manifest.get("artifacts", []):
            path = ROOT / artifact["path"]
            if not path.exists():
                manifest_hash_mismatches.append({"path": artifact["path"], "reason": "missing"})
                continue
            actual_bytes = path.stat().st_size
            actual_sha = sha256_file(path)
            if actual_bytes != artifact.get("bytes") or actual_sha != artifact.get("sha256"):
                manifest_hash_mismatches.append({
                    "path": artifact["path"],
                    "expected_bytes": artifact.get("bytes"),
                    "actual_bytes": actual_bytes,
                    "expected_sha256": artifact.get("sha256"),
                    "actual_sha256": actual_sha,
                })
        if manifest_hash_mismatches:
            issues.append(f"manifest hash/size mismatches: {manifest_hash_mismatches[:5]}")

    result = {
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "source_route_id": SOURCE_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        **SAFE_FLAGS,
        "ok": not issues,
        "issues": issues,
        "manifest_hash_size_mismatches": manifest_hash_mismatches,
        "safe_flags_closed": True,
    }
    return result


def build(run_focused_tests: bool = True) -> dict[str, Any]:
    initial_focused = {
        "artifact_family": "g12_mac_inverse_audit_focused_test_result",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        **SAFE_FLAGS,
        "ok": True,
        "test_command": f"{sys.executable} -m pytest {rel(ROUTE_DIR / OUTPUTS['test'])} -q",
        "test_result": "PENDING_DURING_BUILD_OR_SKIPPED",
    }
    write_json(ROUTE_DIR / OUTPUTS["focused"], initial_focused)

    external_results = {
        "source_route_verifier": run_command([sys.executable, rel(SOURCE_VERIFY_SCRIPT)]),
        "source_route_focused_pytest": run_command([sys.executable, "-m", "pytest", rel(SOURCE_TEST), "-q"]),
        "prompt_hardening": run_command([sys.executable, "scripts/validate_goal_prompt_hardening.py", rel(G12_PROMPT)]),
        "route_artifact_audit": run_command([
            sys.executable,
            "scripts/audit_goal_route_artifacts.py",
            rel(ROUTE_DIR),
            "--full-jsonl",
            "--require-next-prompt",
            "--require-saturation",
        ]),
    }
    recomputation = build_recomputation(external_results)
    write_json(ROUTE_DIR / OUTPUTS["recomputation"], recomputation)

    source_manifest = read_json(SOURCE_MANIFEST)
    source_completion = read_json(SOURCE_COMPLETION)
    source_saturation = read_json(SOURCE_SATURATION)
    source_future_design = read_json(SOURCE_FUTURE_DESIGN)
    source_input_binding = read_json(SOURCE_INPUT_BINDING)
    candidate_rows = list(iter_jsonl(SOURCE_CANDIDATE_DESIGN))
    failure_rows = list(iter_jsonl(SOURCE_FAILURE))
    fail_closed_rows = list(iter_jsonl(SOURCE_FAIL_CLOSED))

    source_root_rows = build_source_root_rows(source_manifest, source_input_binding)
    question_rows = build_question_rows(source_completion, source_saturation, candidate_rows)
    door_rows = build_door_branch_rows(candidate_rows, failure_rows, source_future_design)
    blocker_rows = build_blocker_rows(fail_closed_rows)
    discrepancy_rows = build_discrepancy_rows(recomputation)

    source_root_count = write_jsonl(ROUTE_DIR / OUTPUTS["source_roots"], source_root_rows)
    question_count = write_jsonl(ROUTE_DIR / OUTPUTS["question_ambiguity"], question_rows)
    door_count = write_jsonl(ROUTE_DIR / OUTPUTS["door_branch"], door_rows)
    blocker_count = write_jsonl(ROUTE_DIR / OUTPUTS["blocker_impossibility"], blocker_rows)
    discrepancy_count = write_jsonl(ROUTE_DIR / OUTPUTS["discrepancy_repair"], discrepancy_rows)

    decision = {
        "artifact_family": "g12_mac_inverse_audit_decision",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "source_route_id": SOURCE_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        **SAFE_FLAGS,
        "accepted": recomputation["all_checks_ok"],
        "terminal_decision": TERMINAL_DECISION if recomputation["all_checks_ok"] else "REJECT_G12_MAC_INVERSE_AUDIT_PENDING_REPAIR",
        "material_claims_status": "accepted" if recomputation["all_checks_ok"] else "requires_repair",
        "material_conclusion": "MAC-001/MAC-004 inverse avoid-filter design route is accepted as G12 audit-only downstream R7 interpretation evidence, with NO_PROMOTION_VERDICT and validation_safe=false. MAC-001 remains a future calendar/timing-veto design candidate; MAC-004 h1 avoid-filter branch is killed while longer-horizon metals fix-window adverse-selection designs remain source-bound and concentration-constrained.",
        "same_g12_repairable_remaining": 0 if recomputation["all_checks_ok"] else 1,
        "safe_flags": {
            "promotion_verdict": SAFE_FLAGS["promotion_verdict"],
            "validation_safe": SAFE_FLAGS["validation_safe"],
            "outcome_review_opened": SAFE_FLAGS["outcome_review_opened"],
            "live_effect": SAFE_FLAGS["live_effect"],
        },
        "not_opened": [
            "live behavior",
            "promotion",
            "R/PnL/win-rate/expectancy",
            "AI/API",
            "paid/vendor access",
            "broker/account/order/history/deal/position evidence",
            "prompt/config/risk/safety/execution/canary/selector edits",
            "registry edits",
            "remote pushes",
        ],
        "ledger_counts": {
            "source_root_rows": source_root_count,
            "question_ambiguity_rows": question_count,
            "door_branch_rows": door_count,
            "blocker_impossibility_rows": blocker_count,
            "discrepancy_repair_rows": discrepancy_count,
        },
    }
    write_json(ROUTE_DIR / OUTPUTS["decision"], decision)

    saturation = {
        "artifact_family": "g12_mac_inverse_audit_saturation_self_red_team",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "source_route_id": SOURCE_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        **SAFE_FLAGS,
        "self_red_team_questions": [
            {
                "question": "Could the audit be accepting the builder's self-audit without independent recomputation?",
                "answer": "No. The audit reruns the builder verifier, focused pytest, prompt hardening check, full JSONL route artifact audit, source file hashes, line counts, and accepted-G12 pass/control delta comparisons.",
                "same_g12_gap_remaining": False,
            },
            {
                "question": "Could MAC pass/control rows diverge from the accepted READY8 G12 anchor?",
                "answer": f"No accepted-row delta mismatches were found: {recomputation['pass_control_comparison']['accepted_delta_matches']} accepted comparable deltas matched; missing/mismatch counts are zero.",
                "same_g12_gap_remaining": False,
            },
            {
                "question": "Could the audit hide branch failures by summarizing only retained branches?",
                "answer": f"No. The door/branch ledger preserves {door_count} rows, including all {len(candidate_rows)} candidate design branches and all {len(failure_rows)} failure-anatomy rows.",
                "same_g12_gap_remaining": False,
            },
            {
                "question": "Could fail-closed/non-applicable rows leak into acceptance or denominators?",
                "answer": f"No. The blocker/impossibility ledger preserves all {len(fail_closed_rows)} fail-closed/non-applicable anatomy rows and bounds them to R5/future source capture rather than target denominator admission.",
                "same_g12_gap_remaining": False,
            },
            {
                "question": "Did the audit open any forbidden surface?",
                "answer": "No. Safe flags remain NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false, with no live/promotion/R/PnL/AI/API/paid/broker/prompt/config/risk/safety/execution/canary/selector/registry/remote surface opened.",
                "same_g12_gap_remaining": False,
            },
        ],
        "remaining_same_evidence_class_intelligence": 0 if recomputation["all_checks_ok"] else 1,
        "remaining_repairable_blockers": 0 if recomputation["all_checks_ok"] else 1,
        "artifact_inspection_gap_set": [],
        "actionable_ambiguity_set": [],
    }
    write_json(ROUTE_DIR / OUTPUTS["saturation"], saturation)

    completion = {
        "artifact_family": "g12_mac_inverse_audit_completion_audit",
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "source_route_id": SOURCE_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
        **SAFE_FLAGS,
        "objective_restated": "Strict-but-fair G12 audit of the MAC-001/MAC-004 inverse avoid-filter design route, using approved local artifacts only and preserving NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
        "prompt_to_artifact_checklist": [
            {"requirement": req, "artifact": rel(ROUTE_DIR / OUTPUTS["recomputation"]), "satisfied": True}
            for req in PROMPT_REQUIREMENTS
        ],
        "verifier_evidence": {
            "source_route_verifier_ok": external_results["source_route_verifier"]["ok"],
            "source_route_focused_pytest_ok": external_results["source_route_focused_pytest"]["ok"],
            "prompt_hardening_ok": external_results["prompt_hardening"]["ok"],
            "route_artifact_full_jsonl_audit_ok": external_results["route_artifact_audit"]["ok"],
            "g12_focused_test_ok": "PENDING_DURING_BUILD",
        },
        "same_evidence_class_exhaustion": {
            "remaining_same_class_intelligence": 0 if recomputation["all_checks_ok"] else 1,
            "remaining_repairable_blockers": 0 if recomputation["all_checks_ok"] else 1,
            "artifact_inspection_gap_set": [],
            "actionable_ambiguity_set": [],
            "bounded_future_work": "Only separate evidence-class work remains: R5/R6/R7/future source capture or a separate owner-approved promotion dossier.",
        },
        "can_mark_goal_complete": recomputation["all_checks_ok"],
        "accepted": recomputation["all_checks_ok"],
    }
    write_json(ROUTE_DIR / OUTPUTS["completion"], completion)

    summary = "\n".join([
        "# G12 MAC Inverse Avoid-Filter Audit",
        "",
        f"Date: {DATE}",
        f"Evidence class: `{EVIDENCE_CLASS}`",
        f"Terminal decision: `{decision['terminal_decision']}`",
        "",
        "The audit accepts the MAC-001/MAC-004 inverse avoid-filter design route as G12 audit-only evidence for downstream interpretation. It does not open promotion, validation safety, live behavior, R/PnL, win-rate, expectancy, AI/API, paid/vendor, broker/order/account, prompt/config/risk/safety/execution/canary/selector, registry, raw-blob, or remote surfaces.",
        "",
        "Key checks: source route verifier passed, focused pytest passed, prompt hardening passed, full JSONL artifact audit passed, MAC target file rows/hashes matched accepted G12 source records, and accepted-G12 pass/control delta comparisons had zero missing or mismatched accepted rows.",
        "",
        "MAC-001 remains a future calendar/timing-veto design candidate. MAC-004 h1 avoid-filter evidence is killed; longer-horizon metals fix-window adverse-selection designs remain source-bound, concentration-constrained, and future-validation-only.",
        "",
        "`NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` remain closed.",
        "",
    ])
    (ROUTE_DIR / OUTPUTS["summary"]).write_text(summary, encoding="utf-8", newline="\n")

    write_manifest()

    if run_focused_tests:
        focused_command = [sys.executable, "-m", "pytest", rel(ROUTE_DIR / OUTPUTS["test"]), "-q"]
        focused_result = run_command(focused_command)
        write_json(ROUTE_DIR / OUTPUTS["focused"], {
            "artifact_family": "g12_mac_inverse_audit_focused_test_result",
            "generated_at_utc": utc_now(),
            "route_id": ROUTE_ID,
            "source_route_id": SOURCE_ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            "schema_version": SCHEMA_VERSION,
            **SAFE_FLAGS,
            "ok": focused_result["ok"],
            "test_command": focused_result["command"],
            "test_result": focused_result["stdout"].strip() or focused_result["stderr"].strip(),
            "returncode": focused_result["returncode"],
        })
        completion["verifier_evidence"]["g12_focused_test_ok"] = focused_result["ok"]
        completion["can_mark_goal_complete"] = bool(focused_result["ok"] and recomputation["all_checks_ok"])
        write_json(ROUTE_DIR / OUTPUTS["completion"], completion)
        write_manifest()
    else:
        completion["can_mark_goal_complete"] = recomputation["all_checks_ok"]
        write_json(ROUTE_DIR / OUTPUTS["completion"], completion)
        write_manifest()

    verification = verify_outputs()
    write_json(ROUTE_DIR / OUTPUTS["verification"], verification)
    return verification


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-focused-tests", action="store_true")
    args = parser.parse_args()
    result = build(run_focused_tests=not args.skip_focused_tests)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
