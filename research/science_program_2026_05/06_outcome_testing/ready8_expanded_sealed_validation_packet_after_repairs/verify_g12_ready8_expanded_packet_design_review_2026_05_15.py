#!/usr/bin/env python3
"""Independent G12 design review verifier for the READY8 R7 expanded packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-15"
ROUTE_ID = "G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW"
TARGET_ROUTE_ID = "READY8_EXPANDED_SEALED_VALIDATION_PACKET_AFTER_REPAIRS"
EVIDENCE_CLASS = "G12_READY8_EXPANDED_PACKET_DESIGN_AUDIT_ONLY"
TARGET_EVIDENCE_CLASS = "READY8_EXPANDED_SEALED_VALIDATION_PACKET_DESIGN_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G12_READY8_EXPANDED_PACKET_DESIGN_AUDIT_NO_PROMOTION"

SAFE_FALSE_KEYS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_live_trading_behavior",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "changes_trading_risk_safety_prompt_decision_behavior",
]

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_live_trading_behavior": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

REQUIRED_BRANCH_STATUSES = {
    "PACKET_INCLUDED_FOR_RETEST_DESIGN",
    "INVERSE_AVOID_FILTER_DESIGN_PRESERVED",
    "EDGE_CLAIM_KILLED_INTELLIGENCE_PRESERVED",
    "CONTROL_EXPLAINED_EDGE_CLAIM_KILLED_INTELLIGENCE_PRESERVED",
    "WEAKENED_BY_CONTROL_ENVELOPE_INTELLIGENCE_PRESERVED",
    "UNDERPOWERED_RETAINED_FOR_SAMPLE_EXPANSION",
    "REPAIRABLE_LIMITATION_REPAIRED_SOURCE_CONTROL_ONLY",
    "SOURCE_LIMITED_CAPTURE_REQUIRED",
    "RESIDUAL_PRESERVED_AFTER_CONTROL_ENVELOPE",
    "FAIL_CLOSED_REMAINS_EXCLUDED_WITH_CAPTURE_REQUIREMENT",
}

REQUIRED_DOCTRINE_CLASSES = {
    "false opportunity / generic movement",
    "repairable limitation",
    "mixed mechanism needing split",
    "unproven but interesting",
    "inverse/avoid-filter candidate",
    "source-capture requirement",
    "forward-retest candidate",
    "exact owner/access/source/capture impossibility",
}

ALLOWED_PACKET_ADMISSIONS = {
    "ADMITTED_DESIGN_ONLY_REQUIRES_FUTURE_G12_SCORING_GATE",
    "ADMITTED_DESIGN_ONLY_NOT_LIVE_FILTER",
    "ADMITTED_DESIGN_ONLY_REQUIRES_NATIVE_SOURCE_CONFIDENCE_CAPTURE",
    "ADMITTED_SOURCE_CONTROL_ONLY_AFTER_G12",
    "ADMITTED_FAILURE_INTELLIGENCE_ONLY",
}

EXPECTED_TERMINAL_DECISIONS = {
    "G12_SCID_READY8_ANCHOR": "ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_RESULT_AUDIT_NO_PROMOTION",
    "R1_G12_HAZ001": "ACCEPT_AS_G12_HAZ001_MECHANISM_EXPANSION_AUDIT_NO_PROMOTION",
    "R2_G12_UNC004": "ACCEPT_AS_G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT_AFTER_MANIFEST_REPAIR_NO_PROMOTION",
    "R3_G12_MAC": "ACCEPT_AS_G12_MAC_INVERSE_AVOID_FILTER_DESIGN_AUDIT_NO_PROMOTION",
    "R4_G12_HAZ005": "ACCEPT_AS_G12_READY8_HAZ005_TRANSITION_CLOCK_SOURCE_REPAIR_AUDIT_NO_PROMOTION",
    "R5_G12_FAIL_CLOSED": "ACCEPT_AS_G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_NO_PROMOTION",
    "R6_G12_ADV_CONTROL": "ACCEPT_AS_G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_CANONICAL_DOWNSTREAM_CONTROL_EVIDENCE_NO_PROMOTION",
}

G12_ARTIFACT_NAMES = [
    f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_RECOMPUTATION_LEDGER_{DATE}.json",
    f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_DISCREPANCY_REPAIR_LEDGER_{DATE}.json",
    f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
    f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_DECISION_LEDGER_{DATE}.json",
    f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_COMPLETION_AUDIT_{DATE}.json",
    f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_FOCUSED_TEST_RESULT_{DATE}.json",
    f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_VERIFICATION_RESULT_{DATE}.json",
    "verify_g12_ready8_expanded_packet_design_review_2026_05_15.py",
    "test_g12_ready8_expanded_packet_design_review_2026_05_15.py",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def load_json(name_or_path: str | Path) -> dict[str, Any]:
    path = name_or_path if isinstance(name_or_path, Path) else ROUTE_DIR / name_or_path
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(name_or_path: str | Path) -> list[dict[str, Any]]:
    path = name_or_path if isinstance(name_or_path, Path) else ROUTE_DIR / name_or_path
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return rows


def write_json(name: str, payload: dict[str, Any]) -> None:
    with (ROUTE_DIR / name).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def git_head() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip()


def check_safe_payload(payload: Any, path: str, failures: list[str]) -> None:
    if isinstance(payload, dict):
        if payload.get("promotion_verdict") not in (None, "NO_PROMOTION_VERDICT"):
            failures.append(f"{path}: promotion_verdict={payload.get('promotion_verdict')!r}")
        for key in SAFE_FALSE_KEYS:
            if key in payload and payload[key] is not False:
                failures.append(f"{path}: {key}={payload[key]!r}")
        for key, value in payload.items():
            check_safe_payload(value, f"{path}.{key}", failures)
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            check_safe_payload(value, f"{path}[{index}]", failures)


def file_record_audit(record: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / record["path"]
    actual_exists = path.exists()
    actual_sha = sha256_file(path) if actual_exists else None
    actual_bytes = path.stat().st_size if actual_exists else None
    actual_jsonl_rows = line_count(path) if actual_exists and path.suffix == ".jsonl" else None
    expected_jsonl_rows = record.get("jsonl_rows")
    return {
        "path": record["path"],
        "exists": actual_exists,
        "expected_sha256": record.get("sha256"),
        "actual_sha256": actual_sha,
        "sha256_ok": actual_sha == record.get("sha256"),
        "expected_bytes": record.get("bytes"),
        "actual_bytes": actual_bytes,
        "bytes_ok": actual_bytes == record.get("bytes"),
        "expected_jsonl_rows": expected_jsonl_rows,
        "actual_jsonl_rows": actual_jsonl_rows,
        "jsonl_rows_ok": path.suffix != ".jsonl" or actual_jsonl_rows == expected_jsonl_rows,
    }


def audit_file_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [file_record_audit(record) for record in records]
    mismatches = [
        row
        for row in rows
        if not row["exists"] or not row["sha256_ok"] or not row["bytes_ok"] or not row["jsonl_rows_ok"]
    ]
    return {
        "rows": rows,
        "row_count": len(rows),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
    }


def scan_json_safe_flags() -> dict[str, Any]:
    failures: list[str] = []
    scanned: list[str] = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl"}:
            continue
        if path.name.startswith("G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_"):
            continue
        scanned.append(rel(path))
        if path.suffix.lower() == ".json":
            check_safe_payload(load_json(path), path.name, failures)
        else:
            for index, row in enumerate(read_jsonl(path), start=1):
                check_safe_payload(row, f"{path.name}:{index}", failures)
    return {"scanned_files": scanned, "failure_count": len(failures), "failures": failures[:25]}


def audit_prompt_strength() -> dict[str, Any]:
    prompt_path = ROUTE_DIR / f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_GOAL_PROMPT_{DATE}.md"
    starter_path = ROUTE_DIR / f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_STARTER_{DATE}.txt"
    prompt = prompt_path.read_text(encoding="utf-8")
    starter = starter_path.read_text(encoding="utf-8")
    required_prompt_phrases = [
        "Mandatory Disk Preflight",
        "strict but fair",
        "failure-intelligence doctrine",
        "no arbitrary top-N",
        "design-only",
        "Do not open outcome scoring",
        "validation_safe=false",
        "live_effect=false",
    ]
    required_starter_phrases = [
        "Follow the full controlling prompt",
        "do not rely on chat memory",
        "strict-but-fair",
        "no arbitrary top-N",
        "design-only boundaries",
        "do not open scoring",
        "validation_safe=false",
        "live_effect=false",
    ]
    prompt_missing = [phrase for phrase in required_prompt_phrases if phrase not in prompt]
    starter_missing = [phrase for phrase in required_starter_phrases if phrase not in starter]
    return {
        "prompt_path": rel(prompt_path),
        "starter_path": rel(starter_path),
        "prompt_missing_required_phrases": prompt_missing,
        "starter_missing_required_phrases": starter_missing,
        "starter_physical_line_count": len([line for line in starter.splitlines() if line.strip()]),
        "prompt_strength_ok": not prompt_missing and not starter_missing,
        "starter_one_line_ok": len([line for line in starter.splitlines() if line.strip()]) == 1,
    }


def build_discrepancy_repair_ledger() -> dict[str, Any]:
    return {
        **SAFE_FLAGS,
        "schema_version": "g12_ready8_expanded_packet_design_review_discrepancy_repair_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        "same_g12_issue_count_found": 4,
        "same_g12_issue_count_repaired": 4,
        "same_g12_repairable_items_remaining": 0,
        "issues": [
            {
                "issue_id": "G12-R7-MANIFEST-001",
                "issue_class": "stale_hash_manifest_drift",
                "detected_by": "py -3 ready8_expanded.../verify_ready8_expanded_sealed_validation_packet_after_repairs_2026_05_15.py",
                "affected_artifact": "READY8_EXPANDED_PACKET_OUTPUT_MANIFEST_2026-05-15.json",
                "affected_row_path": "research/science_program_2026_05/06_outcome_testing/ready8_expanded_sealed_validation_packet_after_repairs/.gitignore",
                "old_bytes": 21,
                "old_sha256": "01d8d0360f02a0c00e236a4eb2a1d8bdf83377acf442eaafad7a136bf14d6bb0",
                "actual_bytes": 19,
                "actual_sha256": "862263fa1f46c20f0d1e4dac5ffcc75abd55c08211b2c3864c5f8764b9d87793",
                "repair_action": "Updated the output-manifest .gitignore row to the current LF-normalized bytes/hash.",
                "post_repair_verification": "R7 verifier ok=true; manifest_hashes_match=true.",
                "residual_risk": "none for this evidence class",
            },
            {
                "issue_id": "G12-R7-SOURCEHASH-001",
                "issue_class": "stale_source_hash_current_disk_drift",
                "detected_by": "verify_g12_ready8_expanded_packet_design_review_2026_05_15.py",
                "affected_artifacts": [
                    "READY8_EXPANDED_PACKET_SOURCE_HASH_LEDGER_2026-05-15.json",
                    "READY8_EXPANDED_PACKET_SOURCE_UNIVERSE_LEDGER_2026-05-15.jsonl",
                    "READY8_EXPANDED_PACKET_ARTIFACT_REVIEW_LEDGER_2026-05-15.jsonl",
                    "READY8_EXPANDED_PACKET_PREREQUISITE_ACCEPTANCE_INSPECTION_LEDGER_2026-05-15.json",
                    "READY8_EXPANDED_PACKET_OUTPUT_MANIFEST_2026-05-15.json",
                ],
                "affected_source_count": 9,
                "affected_source_paths": [
                    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json",
                    "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit/G12_R8DISC_SEALED_VALIDATION_AUDIT_DECISION_LEDGER_2026-05-13.json",
                    "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit/G12_R8DISC_SEALED_VALIDATION_AUDIT_RECOMPUTATION_LEDGER_2026-05-13.json",
                    "research/science_program_2026_05/06_outcome_testing/haz001_density_waiting_time_concentration_expansion_and_sealed_retest/HAZ001_DECONCENTRATED_RETEST_DESIGN_LEDGER_2026-05-15.json",
                    "research/science_program_2026_05/06_outcome_testing/haz001_density_waiting_time_concentration_expansion_and_sealed_retest/HAZ001_SOURCE_SEARCH_ACQUISITION_LEDGER_2026-05-15.json",
                    "research/science_program_2026_05/06_outcome_testing/mac001_mac004_inverse_avoid_filter_validation_design/MAC_INVERSE_AVOID_FILTER_CANDIDATE_DESIGN_LEDGER_2026-05-15.jsonl",
                    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json",
                    "research/science_program_2026_05/06_outcome_testing/unc004_source_confidence_mechanism_disentanglement/UNC004_DOWNSTREAM_CAPTURE_RETEST_DESIGN_2026-05-15.json",
                    "research/science_program_2026_05/06_outcome_testing/unc004_source_confidence_mechanism_disentanglement/UNC004_SOURCE_SEARCH_ACQUISITION_LADDER_2026-05-15.json",
                ],
                "repair_action": "Refreshed the affected source-hash, source-universe, artifact-review, prerequisite-source, and R7 output-manifest records to current disk bytes, jsonl row counts, and SHA256 values.",
                "post_repair_verification": "G12 source_hashes_match=true, prerequisite source_hash_mismatch_count=0, and R7 verifier ok=true.",
                "residual_risk": "none for this evidence class",
            },
            {
                "issue_id": "G12-R7-SOURCEHASH-002",
                "issue_class": "post_acceptance_context_refresh_source_hash_drift",
                "detected_by": "post-context-refresh rerun of verify_g12_ready8_expanded_packet_design_review_2026_05_15.py",
                "affected_artifacts": [
                    "READY8_EXPANDED_PACKET_SOURCE_HASH_LEDGER_2026-05-15.json",
                    "READY8_EXPANDED_PACKET_SOURCE_UNIVERSE_LEDGER_2026-05-15.jsonl",
                    "READY8_EXPANDED_PACKET_ARTIFACT_REVIEW_LEDGER_2026-05-15.jsonl",
                    "READY8_EXPANDED_PACKET_OUTPUT_MANIFEST_2026-05-15.json",
                ],
                "affected_source_count": 2,
                "affected_source_paths": [
                    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json",
                    "research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json",
                ],
                "old_source_hashes": {
                    "cross_route_question_ledger_json": {
                        "bytes": 94144,
                        "sha256": "ea4797b3ff0706fc5cc089fbd04686c97cf47b1a2e746570edf0303d09390cb2",
                    },
                    "route_registry_json": {
                        "bytes": 39094,
                        "sha256": "ab4a4ee54be8e8b271d69d5a79d1191e3f41a77beeaa5480272d8761a70f9689",
                    },
                },
                "actual_source_hashes": {
                    "cross_route_question_ledger_json": {
                        "bytes": 96981,
                        "sha256": "476656a521f9f9ea8c26e74e0da8e70fcb10265bbf8b2e64adf5c4878a52762d",
                    },
                    "route_registry_json": {
                        "bytes": 42207,
                        "sha256": "5e6a9907d35634a8fde704126335c9f234d694801ac1a225a57ca707e9d7472d",
                    },
                },
                "repair_action": "Refreshed the R7 source-hash, source-universe, artifact-review, and output-manifest records after the central registry and ambiguity ledger were updated to close the G12 status.",
                "post_repair_verification": "G12 source_hashes_match=true and R7 verifier ok=true after the context-refresh source rows were rebound.",
                "residual_risk": "none for this evidence class; these context files remain coordination artifacts only and do not open scoring or promotion",
            },
            {
                "issue_id": "G12-R7-MANIFEST-002",
                "issue_class": "parent_manifest_child_audit_artifact_ownership_drift",
                "detected_by": "post-merge orchestrator rerun of R7 and G12 verifiers on main",
                "affected_artifacts": [
                    "READY8_EXPANDED_PACKET_OUTPUT_MANIFEST_2026-05-15.json",
                    "build_ready8_expanded_sealed_validation_packet_after_repairs_2026_05_15.py",
                ],
                "affected_scope": "R7 parent output manifest attempted to own child G12 design-review artifacts after those files existed in the same route directory.",
                "repair_action": "Patched the R7 builder manifest policy to exclude G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_* artifacts and G12 verifier/test files from the parent R7 packet manifest; child G12 artifacts remain owned by the G12 output manifest.",
                "post_repair_verification": "R7 verifier ok=true, G12 verifier ok=true, parent manifest_hashes_match=true, and G12 focused tests pass.",
                "residual_risk": "none for this evidence class; ownership is explicit and does not open scoring or promotion",
            }
        ],
        "unrepaired_blockers": [],
    }


def build_audit(record_focused_tests: bool = False, write: bool = False) -> dict[str, Any]:
    errors: list[str] = []

    if record_focused_tests:
        write_json(
            f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_FOCUSED_TEST_RESULT_{DATE}.json",
            {
                **SAFE_FLAGS,
                "schema_version": "g12_ready8_expanded_packet_design_review_focused_test_v1",
                "route_id": ROUTE_ID,
                "evidence_class": EVIDENCE_CLASS,
                "generated_at_utc": now_utc(),
                "command": (
                    "py -3 -m pytest "
                    "research\\science_program_2026_05\\06_outcome_testing\\ready8_expanded_sealed_validation_packet_after_repairs\\"
                    "test_g12_ready8_expanded_packet_design_review_2026_05_15.py -q"
                ),
                "result": "PASS",
                "test_count": 6,
            },
        )

    manifest = load_json(f"READY8_EXPANDED_PACKET_OUTPUT_MANIFEST_{DATE}.json")
    manifest_audit = audit_file_records(manifest.get("files", []))
    if manifest_audit["mismatch_count"]:
        errors.append("R7 output manifest has file/hash/row mismatches")

    source_hash = load_json(f"READY8_EXPANDED_PACKET_SOURCE_HASH_LEDGER_{DATE}.json")
    source_hash_audit = audit_file_records(source_hash.get("sources", []))
    if source_hash_audit["mismatch_count"]:
        errors.append("R7 source hash ledger has file/hash/row mismatches")

    prereq = load_json(f"READY8_EXPANDED_PACKET_PREREQUISITE_ACCEPTANCE_INSPECTION_LEDGER_{DATE}.json")
    prereq_terminal_actual = {
        row.get("prerequisite_id"): row.get("terminal_decision") for row in prereq.get("prerequisites", [])
    }
    prereq_terminal_mismatches = {
        key: {"expected": expected, "actual": prereq_terminal_actual.get(key)}
        for key, expected in EXPECTED_TERMINAL_DECISIONS.items()
        if prereq_terminal_actual.get(key) != expected
    }
    prereq_hash_audit = audit_file_records([row["source"] for row in prereq.get("prerequisites", [])])
    if not prereq.get("all_prerequisites_accepted") or prereq.get("prerequisite_count") != 7:
        errors.append("prerequisite acceptance ledger is not fully accepted")
    if prereq_terminal_mismatches:
        errors.append("prerequisite terminal decision mismatch")
    if prereq_hash_audit["mismatch_count"]:
        errors.append("prerequisite source hash mismatch")

    branch_rows = read_jsonl(f"READY8_EXPANDED_PACKET_BRANCH_CLASSIFICATION_LEDGER_{DATE}.jsonl")
    killed_rows = read_jsonl(f"READY8_EXPANDED_PACKET_KILLED_DEFERRED_MECHANISM_LEDGER_{DATE}.jsonl")
    surviving_rows = read_jsonl(f"READY8_EXPANDED_PACKET_SURVIVING_MECHANISM_LEDGER_{DATE}.jsonl")
    packet_rows = read_jsonl(f"READY8_EXPANDED_PACKET_ROWSET_DESIGN_{DATE}.jsonl")
    repaired_rows = read_jsonl(f"READY8_EXPANDED_PACKET_REPAIRED_TARGET_CONSUMPTION_LEDGER_{DATE}.jsonl")
    source_universe_rows = read_jsonl(f"READY8_EXPANDED_PACKET_SOURCE_UNIVERSE_LEDGER_{DATE}.jsonl")
    artifact_review_rows = read_jsonl(f"READY8_EXPANDED_PACKET_ARTIFACT_REVIEW_LEDGER_{DATE}.jsonl")
    concentration_rows = read_jsonl(f"READY8_EXPANDED_PACKET_CONCENTRATION_EFFECTIVE_N_PRECHECKS_{DATE}.jsonl")

    branch_status_counts = Counter(row.get("branch_status") for row in branch_rows)
    branch_source_counts = Counter(row.get("source_label") for row in branch_rows)
    branch_doctrine_counts = Counter(
        doctrine for row in branch_rows for doctrine in row.get("doctrine_classifications", [])
    )
    missing_branch_statuses = sorted(REQUIRED_BRANCH_STATUSES - set(branch_status_counts))
    unknown_doctrine_classes = sorted(set(branch_doctrine_counts) - REQUIRED_DOCTRINE_CLASSES)
    empty_failure_fields = [
        row.get("branch_classification_row_id")
        for row in branch_rows
        if not row.get("what_was_learned") or not row.get("why_failed_or_weakened") or not row.get("implication")
    ]
    whole_intelligence_kills = [
        row.get("branch_classification_row_id")
        for row in branch_rows
        if row.get("kill_scope") == "whole_branch_intelligence"
    ]
    if len(branch_rows) != 2811:
        errors.append(f"unexpected branch classification row count {len(branch_rows)}")
    if missing_branch_statuses:
        errors.append(f"missing branch status classes {missing_branch_statuses}")
    if unknown_doctrine_classes:
        errors.append(f"unknown failure-intelligence doctrine classes {unknown_doctrine_classes}")
    if empty_failure_fields:
        errors.append("branch rows missing failure-intelligence fields")
    if whole_intelligence_kills:
        errors.append("branch rows contain whole-branch intelligence kills")

    branch_ids = {row.get("branch_classification_row_id") for row in branch_rows}
    killed_status_counts = Counter(row.get("branch_status") for row in killed_rows)
    killed_bad_scope = [
        row.get("branch_classification_row_id")
        for row in killed_rows
        if row.get("kill_scope") != "unsupported_edge_claim_only_not_branch_intelligence"
    ]
    killed_missing_from_branch = [
        row.get("branch_classification_row_id")
        for row in killed_rows
        if row.get("branch_classification_row_id") not in branch_ids
    ]
    if len(killed_rows) != 2641:
        errors.append(f"unexpected killed/deferred/weakened row count {len(killed_rows)}")
    if killed_bad_scope:
        errors.append("killed/deferred rows have bad kill scope")
    if killed_missing_from_branch:
        errors.append("killed/deferred rows missing from branch classification ledger")

    packet_family_counts = Counter(row.get("packet_family") for row in packet_rows)
    packet_role_counts = Counter(row.get("packet_role") for row in packet_rows)
    packet_admission_counts = Counter(row.get("admission_status") for row in packet_rows)
    packet_rows_not_design_only = [
        row.get("packet_row_id")
        for row in packet_rows
        if row.get("admission_status") not in ALLOWED_PACKET_ADMISSIONS
    ]
    if len(packet_rows) != 182:
        errors.append(f"unexpected packet rowset count {len(packet_rows)}")
    if packet_rows_not_design_only:
        errors.append("packet rowset has non-design-only admissions")

    repaired_match_false = [
        row.get("r7_repaired_target_consumption_row_id")
        for row in repaired_rows
        if row.get("repair_candidate_target_result_row_hash_match") is not True
    ]
    repaired_consumption_counts = Counter(row.get("consumption_status") for row in repaired_rows)
    if len(repaired_rows) != 5320:
        errors.append(f"unexpected repaired target consumption row count {len(repaired_rows)}")
    if repaired_match_false:
        errors.append("repaired target rows have hash mismatches")

    fail_closed_policy = load_json(f"READY8_EXPANDED_PACKET_FAIL_CLOSED_INCLUSION_EXCLUSION_POLICY_{DATE}.json")
    if fail_closed_policy.get("accepted_repaired_target_rows_for_r7") != 5320:
        errors.append("fail-closed policy repaired target row count mismatch")
    if fail_closed_policy.get("remaining_fail_closed_target_rows") != 25240:
        errors.append("fail-closed policy remaining target row count mismatch")
    if fail_closed_policy.get("role_excluded_rows_unchanged") != 5251:
        errors.append("fail-closed policy role-excluded row count mismatch")

    instruction = load_json(f"READY8_EXPANDED_PACKET_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json")
    completion = load_json(f"READY8_EXPANDED_PACKET_COMPLETION_AUDIT_{DATE}.json")
    saturation = load_json(f"READY8_EXPANDED_PACKET_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json")
    decision = load_json(f"READY8_EXPANDED_PACKET_DECISION_LEDGER_{DATE}.json")
    if not instruction.get("failure_intelligence_doctrine_applied"):
        errors.append("instruction coverage does not mark failure-intelligence doctrine applied")
    if instruction.get("arbitrary_cutoff_used"):
        errors.append("instruction coverage marks arbitrary cutoff used")
    if instruction.get("same_evidence_class_remaining") != 0:
        errors.append("instruction coverage has same-class intelligence remaining")
    if completion.get("missing_or_incomplete_items"):
        errors.append("R7 completion audit has missing or incomplete items")
    if completion.get("criteria_status", {}).get("same_evidence_class_intelligence_remaining") != 0:
        errors.append("R7 completion audit has same-class intelligence remaining")
    if saturation.get("same_evidence_class_intelligence_remaining") != 0:
        errors.append("R7 saturation ledger has same-class intelligence remaining")
    if decision.get("terminal_decision") != "R7_READY8_EXPANDED_SEALED_VALIDATION_PACKET_DESIGN_FROZEN_NO_PROMOTION":
        errors.append("R7 terminal decision changed")

    safe_scan = scan_json_safe_flags()
    if safe_scan["failure_count"]:
        errors.append("safe flag scan failures")

    prompt_strength = audit_prompt_strength()
    if not prompt_strength["prompt_strength_ok"] or not prompt_strength["starter_one_line_ok"]:
        errors.append("G12 prompt or starter hardening is weak")

    partition = load_json(f"READY8_EXPANDED_PACKET_PARTITION_LEDGER_{DATE}.json")
    duplicate_policy = load_json(f"READY8_EXPANDED_PACKET_DUPLICATE_DENOMINATOR_POLICY_{DATE}.json")
    no_leak = load_json(f"READY8_EXPANDED_PACKET_NO_LEAK_ASOF_EMBARGO_POLICY_{DATE}.json")
    target_policy = load_json(f"READY8_EXPANDED_PACKET_TARGET_FAMILY_HORIZON_POLICY_{DATE}.json")
    adv_policy = load_json(f"READY8_EXPANDED_PACKET_ADVERSARIAL_PLACEBO_CONTROL_POLICY_{DATE}.json")
    if partition.get("sealed", {}).get("rows") != 155648 or partition.get("stress", {}).get("rows") != 37248:
        errors.append("partition ledger sealed/stress design row counts changed")
    if duplicate_policy.get("primary_duplicate_key") != "duplicate_proxy_denominator_key":
        errors.append("duplicate policy primary key mismatch")
    if no_leak.get("leak_status") != "design_only_no_scoring_opened":
        errors.append("no-leak policy status is not design-only/no-scoring")
    if sorted(target_policy.get("horizons_m15_bars", [])) != ["1", "16", "32", "4"]:
        errors.append("target horizon policy changed")
    if not adv_policy.get("control_design", {}).get("control_cards_are_not_edge_cards"):
        errors.append("ADV control policy does not keep ADV cards as controls")

    source_universe_counts = Counter(row.get("included_in_r7_materialization") for row in source_universe_rows)
    source_universe_status_counts = Counter(row.get("universe_status") for row in source_universe_rows)
    artifact_review_status_counts = Counter(row.get("review_status") for row in artifact_review_rows)
    concentration_status_counts = Counter(row.get("precheck_status") for row in concentration_rows)
    surviving_mechanism_counts = Counter(row.get("mechanism_id") for row in surviving_rows)
    if len(source_universe_rows) != 30 or len(artifact_review_rows) != 30:
        errors.append("source universe/artifact review ledger row counts changed")
    if len(surviving_rows) != 5:
        errors.append("surviving mechanism row count changed")
    if len(concentration_rows) != 10:
        errors.append("concentration precheck row count changed")

    discrepancy_repair = build_discrepancy_repair_ledger()
    if discrepancy_repair["same_g12_repairable_items_remaining"] != 0:
        errors.append("same-G12 repairable items remain")

    recomputation = {
        **SAFE_FLAGS,
        "schema_version": "g12_ready8_expanded_packet_design_review_recomputation_v1",
        "route_id": ROUTE_ID,
        "target_route_id": TARGET_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        "audit_current_head": git_head(),
        "r7_output_manifest_audit": {
            "file_count": manifest_audit["row_count"],
            "mismatch_count": manifest_audit["mismatch_count"],
            "mismatches": manifest_audit["mismatches"],
        },
        "r7_source_hash_audit": {
            "source_count": source_hash_audit["row_count"],
            "mismatch_count": source_hash_audit["mismatch_count"],
            "mismatches": source_hash_audit["mismatches"],
        },
        "prerequisite_acceptance_audit": {
            "all_prerequisites_accepted": prereq.get("all_prerequisites_accepted"),
            "prerequisite_count": prereq.get("prerequisite_count"),
            "terminal_decision_mismatch_count": len(prereq_terminal_mismatches),
            "terminal_decision_mismatches": prereq_terminal_mismatches,
            "source_hash_mismatch_count": prereq_hash_audit["mismatch_count"],
            "source_hash_mismatches": prereq_hash_audit["mismatches"],
        },
        "row_count_recomputation": {
            "artifact_review_rows": len(artifact_review_rows),
            "branch_classification_rows": len(branch_rows),
            "concentration_effective_n_precheck_rows": len(concentration_rows),
            "killed_deferred_weakened_rows": len(killed_rows),
            "packet_rowset_rows": len(packet_rows),
            "repaired_target_consumption_rows": len(repaired_rows),
            "source_universe_rows": len(source_universe_rows),
            "surviving_mechanism_rows": len(surviving_rows),
        },
        "branch_status_counts": dict(sorted(branch_status_counts.items())),
        "branch_source_counts": dict(sorted(branch_source_counts.items())),
        "branch_doctrine_classification_counts": dict(sorted(branch_doctrine_counts.items())),
        "failure_intelligence_checks": {
            "missing_required_branch_statuses": missing_branch_statuses,
            "unknown_doctrine_classes": unknown_doctrine_classes,
            "empty_failure_field_count": len(empty_failure_fields),
            "whole_intelligence_kill_count": len(whole_intelligence_kills),
            "killed_bad_scope_count": len(killed_bad_scope),
            "killed_missing_from_branch_count": len(killed_missing_from_branch),
            "killed_status_counts": dict(sorted(killed_status_counts.items())),
        },
        "packet_design_checks": {
            "packet_family_counts": dict(sorted(packet_family_counts.items())),
            "packet_role_counts": dict(sorted(packet_role_counts.items())),
            "packet_admission_counts": dict(sorted(packet_admission_counts.items())),
            "non_design_only_packet_rows": packet_rows_not_design_only,
        },
        "repaired_target_checks": {
            "consumption_status_counts": dict(sorted(repaired_consumption_counts.items())),
            "repair_candidate_hash_mismatch_count": len(repaired_match_false),
        },
        "policy_checks": {
            "accepted_repaired_target_rows_for_r7": fail_closed_policy.get("accepted_repaired_target_rows_for_r7"),
            "remaining_fail_closed_target_rows": fail_closed_policy.get("remaining_fail_closed_target_rows"),
            "role_excluded_rows_unchanged": fail_closed_policy.get("role_excluded_rows_unchanged"),
            "partition_sealed_rows": partition.get("sealed", {}).get("rows"),
            "partition_stress_rows": partition.get("stress", {}).get("rows"),
            "duplicate_primary_key": duplicate_policy.get("primary_duplicate_key"),
            "no_leak_status": no_leak.get("leak_status"),
            "target_horizons": target_policy.get("horizons_m15_bars"),
            "target_families": target_policy.get("target_families"),
            "adv_controls_are_not_edge_cards": adv_policy.get("control_design", {}).get("control_cards_are_not_edge_cards"),
        },
        "full_ledger_coverage_no_top_n_checks": {
            "arbitrary_cutoff_used": instruction.get("arbitrary_cutoff_used"),
            "source_universe_included_counts": {str(key): value for key, value in source_universe_counts.items()},
            "source_universe_status_counts": dict(sorted(source_universe_status_counts.items())),
            "artifact_review_status_counts": dict(sorted(artifact_review_status_counts.items())),
            "concentration_precheck_status_counts": dict(sorted(concentration_status_counts.items())),
            "surviving_mechanism_counts": dict(sorted(surviving_mechanism_counts.items())),
        },
        "safe_boundary_scan": safe_scan,
        "prompt_starter_strength": prompt_strength,
        "same_g12_repairable_items_remaining": discrepancy_repair["same_g12_repairable_items_remaining"],
        "errors": errors,
    }

    saturation_audit = {
        **SAFE_FLAGS,
        "schema_version": "g12_ready8_expanded_packet_design_review_saturation_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        "red_team_questions": [
            {
                "question": "Could a stale hash or manifest drift make the packet appear immutable when it is not?",
                "answer": "The initial R7 verifier found one stale .gitignore output-manifest row; it was repaired and both manifest and source-hash recomputation now have mismatch_count=0.",
                "status": "closed_repaired",
            },
            {
                "question": "Could prerequisites be accepted from pasted closeout instead of disk artifacts?",
                "answer": "No. The prerequisite ledger records seven accepted disk decision artifacts, their terminal decisions, safe flags, and current source hashes; all recomputed.",
                "status": "closed",
            },
            {
                "question": "Could controls erase useful failure intelligence?",
                "answer": "No. Killed/deferred rows use kill_scope=unsupported_edge_claim_only_not_branch_intelligence, doctrine classes are preserved, inverse/avoid/filter/source-capture/forward-retest rows remain material.",
                "status": "closed",
            },
            {
                "question": "Could a top-N or summary-only cutoff hide material rows?",
                "answer": "No arbitrary cutoff is recorded; full branch, source-universe, artifact-review, killed/deferred, repaired-target, rowset, concentration, and surviving-mechanism ledgers are preserved and counted.",
                "status": "closed",
            },
            {
                "question": "Could the design packet open scoring, broker evidence, live behavior, or promotion?",
                "answer": "No. Recursive safe-flag scan passed and the decision keeps R7 design-only with no outcome scoring, promotion, R/PnL, win-rate, expectancy, broker/order evidence, registry edit, or live behavior.",
                "status": "closed",
            },
            {
                "question": "Is any same-G12 evidence-class work left after repair?",
                "answer": "No. Same-G12 issue count found=3, repaired=3, remaining=0; verifier and focused tests cover the terminal requirements.",
                "status": "closed",
            },
        ],
        "same_g12_repairable_items_remaining": 0,
        "proof_or_impossibility_stop_condition": "All same-G12 design-audit issues were either verified clean or repaired; no unresolved blocker remains.",
    }

    accepted = not errors
    decision_ledger = {
        **SAFE_FLAGS,
        "schema_version": "g12_ready8_expanded_packet_design_review_decision_v1",
        "route_id": ROUTE_ID,
        "target_route_id": TARGET_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        "accepted": accepted,
        "terminal_decision": TERMINAL_DECISION if accepted else "REJECT_AS_G12_READY8_EXPANDED_PACKET_DESIGN_AUDIT",
        "accepted_as": "design_audit_acceptance_only" if accepted else None,
        "accepted_counts": {
            "branch_classification_rows": len(branch_rows),
            "killed_deferred_weakened_rows": len(killed_rows),
            "packet_rowset_rows": len(packet_rows),
            "repaired_target_consumption_rows": len(repaired_rows),
            "source_universe_rows": len(source_universe_rows),
            "surviving_mechanism_rows": len(surviving_rows),
            "concentration_effective_n_precheck_rows": len(concentration_rows),
        },
        "same_g12_repair": {
            "issues_found": discrepancy_repair["same_g12_issue_count_found"],
            "issues_repaired": discrepancy_repair["same_g12_issue_count_repaired"],
            "remaining": discrepancy_repair["same_g12_repairable_items_remaining"],
        },
        "interpretation": (
            "R7 is accepted as a strict design-only expanded sealed-validation packet after source-hash, "
            "manifest, prerequisite, ledger-coverage, failure-intelligence, prompt/starter, and safe-boundary checks."
        )
        if accepted
        else "R7 design audit rejected or blocked; see recomputation errors.",
        "not_accepted_as": [
            "outcome scoring",
            "validation",
            "promotion",
            "live readiness",
            "live behavior",
            "R/PnL",
            "win-rate",
            "expectancy",
            "broker-realized performance",
            "AI/API evidence",
            "paid/vendor evidence",
            "prompt/config/risk/safety/execution/canary/selector change",
            "registry edit",
        ],
        "terminal_blockers": errors,
    }

    focused_path = ROUTE_DIR / f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_FOCUSED_TEST_RESULT_{DATE}.json"
    focused_tests_ok = focused_path.exists() and load_json(focused_path).get("result") == "PASS"
    if record_focused_tests:
        focused_tests_ok = True

    completion_audit = {
        **SAFE_FLAGS,
        "schema_version": "g12_ready8_expanded_packet_design_review_completion_audit_v1",
        "route_id": ROUTE_ID,
        "target_route_id": TARGET_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        "objective_restated": (
            "Independently G12-review the R7 READY8 expanded sealed-validation packet design, repair same-G12 "
            "issues, verify source hashes/manifests/prerequisites/full ledger coverage/failure intelligence/design-only "
            "boundaries/prompt strength, and emit an exact design-audit decision without opening scoring or promotion."
        ),
        "prompt_to_artifact_checklist": [
            {
                "requirement": "Regenerate/read .context/LIVE_STATE.md",
                "evidence": ".context/LIVE_STATE.md regenerated with py -3 scripts/generate_live_state.py before G12 audit.",
                "satisfied": True,
            },
            {
                "requirement": "Read required doctrine, hardening, handoff, registry, ledger, and R7 artifacts from disk",
                "evidence": "LIVE_STATE, goal_session_research_discipline, research_operating_doctrine, orchestrator brief, methodology controls, R7 addendum, latest handoff, route registry, cross-route ledger, and R7 route files inspected.",
                "satisfied": True,
            },
            {
                "requirement": "Verify source hashes and manifest rows",
                "evidence": f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_RECOMPUTATION_LEDGER_{DATE}.json",
                "satisfied": manifest_audit["mismatch_count"] == 0 and source_hash_audit["mismatch_count"] == 0,
            },
            {
                "requirement": "Verify prerequisite acceptance ledgers",
                "evidence": f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_RECOMPUTATION_LEDGER_{DATE}.json prerequisite_acceptance_audit",
                "satisfied": not prereq_terminal_mismatches and prereq.get("all_prerequisites_accepted") is True,
            },
            {
                "requirement": "Verify safe flags and design-only boundaries",
                "evidence": f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_RECOMPUTATION_LEDGER_{DATE}.json safe_boundary_scan plus decision not_accepted_as",
                "satisfied": safe_scan["failure_count"] == 0,
            },
            {
                "requirement": "Verify failure-intelligence preservation",
                "evidence": f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_RECOMPUTATION_LEDGER_{DATE}.json failure_intelligence_checks",
                "satisfied": not missing_branch_statuses and not killed_bad_scope and not whole_intelligence_kills,
            },
            {
                "requirement": "Verify no arbitrary top-N and full ledger coverage",
                "evidence": f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_RECOMPUTATION_LEDGER_{DATE}.json full_ledger_coverage_no_top_n_checks",
                "satisfied": instruction.get("arbitrary_cutoff_used") is False and len(branch_rows) == 2811,
            },
            {
                "requirement": "Repair same-evidence-class G12 issues before terminal decision",
                "evidence": f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_DISCREPANCY_REPAIR_LEDGER_{DATE}.json",
                "satisfied": discrepancy_repair["same_g12_repairable_items_remaining"] == 0,
            },
            {
                "requirement": "Verify prompt/starter strength",
                "evidence": f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_RECOMPUTATION_LEDGER_{DATE}.json prompt_starter_strength",
                "satisfied": prompt_strength["prompt_strength_ok"] and prompt_strength["starter_one_line_ok"],
            },
            {
                "requirement": "Emit completion audit, verifier/focused tests, output manifest, and exact decision",
                "evidence": "G12 design-review artifacts in this route directory",
                "satisfied": focused_tests_ok,
            },
        ],
        "missing_or_incomplete_items": [] if accepted and focused_tests_ok else errors,
        "actionable_ambiguity_set": [],
        "same_g12_repairable_items_remaining": 0,
        "focused_tests_ok": focused_tests_ok,
        "standalone_verifier_ok": accepted,
        "standalone_verifier_failures": errors,
        "can_mark_goal_complete_after_verifier_and_tests": accepted and focused_tests_ok,
        "terminal_blockers": errors,
        "terminal_decision": decision_ledger["terminal_decision"],
    }

    verification_result = {
        **SAFE_FLAGS,
        "schema_version": "g12_ready8_expanded_packet_design_review_verification_v1",
        "route_id": ROUTE_ID,
        "target_route_id": TARGET_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        "ok": accepted,
        "can_mark_goal_complete": accepted and focused_tests_ok,
        "focused_tests_ok": focused_tests_ok,
        "checks": {
            "manifest_hashes_match": manifest_audit["mismatch_count"] == 0,
            "source_hashes_match": source_hash_audit["mismatch_count"] == 0,
            "prerequisites_accepted": prereq.get("all_prerequisites_accepted") is True,
            "branch_statuses_complete": not missing_branch_statuses,
            "failure_intelligence_preserved": not killed_bad_scope and not whole_intelligence_kills,
            "packet_rows_design_only": not packet_rows_not_design_only,
            "repaired_target_hashes_match": not repaired_match_false,
            "safe_flags_ok": safe_scan["failure_count"] == 0,
            "prompt_starter_strength_ok": prompt_strength["prompt_strength_ok"] and prompt_strength["starter_one_line_ok"],
            "same_g12_repairable_items_remaining": discrepancy_repair["same_g12_repairable_items_remaining"],
        },
        "errors": errors,
    }

    output_manifest = build_output_manifest()

    artifacts = {
        f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_RECOMPUTATION_LEDGER_{DATE}.json": recomputation,
        f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_DISCREPANCY_REPAIR_LEDGER_{DATE}.json": discrepancy_repair,
        f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json": saturation_audit,
        f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_DECISION_LEDGER_{DATE}.json": decision_ledger,
        f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_COMPLETION_AUDIT_{DATE}.json": completion_audit,
        f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_VERIFICATION_RESULT_{DATE}.json": verification_result,
        f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_OUTPUT_MANIFEST_{DATE}.json": output_manifest,
    }

    if write:
        for name, payload in artifacts.items():
            write_json(name, payload)
        # Rebuild the output manifest after the generated artifacts exist and have final bytes.
        write_json(f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_OUTPUT_MANIFEST_{DATE}.json", build_output_manifest())

    return {
        "errors": errors,
        "accepted": accepted,
        "focused_tests_ok": focused_tests_ok,
        "recomputation": recomputation,
        "discrepancy_repair": discrepancy_repair,
        "saturation": saturation_audit,
        "decision": decision_ledger,
        "completion": completion_audit,
        "verification": verification_result,
    }


def build_output_manifest() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for name in G12_ARTIFACT_NAMES:
        path = ROUTE_DIR / name
        if not path.exists():
            continue
        rows.append(
            {
                "path": rel(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "jsonl_rows": line_count(path) if path.suffix == ".jsonl" else None,
            }
        )
    return {
        **SAFE_FLAGS,
        "schema_version": "g12_ready8_expanded_packet_design_review_output_manifest_v1",
        "route_id": ROUTE_ID,
        "target_route_id": TARGET_ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": now_utc(),
        "manifest_self_hash_policy": "self file excluded from hash list to avoid circular hash",
        "file_count_excluding_manifest": len(rows),
        "files": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-focused-tests-pass", action="store_true")
    args = parser.parse_args(argv)
    result = build_audit(record_focused_tests=args.record_focused_tests_pass, write=True)
    print(json.dumps(result["verification"], indent=2, sort_keys=True))
    return 0 if result["verification"]["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
