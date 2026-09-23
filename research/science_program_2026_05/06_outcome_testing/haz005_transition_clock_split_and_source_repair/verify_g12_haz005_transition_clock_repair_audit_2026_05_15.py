#!/usr/bin/env python3
"""Verify G12 HAZ-005 transition-clock source-repair audit artifacts."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-15"
G12_ROUTE_ID = "G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT"
G12_EVIDENCE_CLASS = "G12_READY8_HAZ005_TRANSITION_CLOCK_SOURCE_REPAIR_AUDIT_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

SCRIPT_PATH = Path(__file__).resolve()
ROUTE_DIR = SCRIPT_PATH.parent
REPO = SCRIPT_PATH.parents[4]

SOURCE_RECOMPUTATION_PATH = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_SOURCE_REPAIR_RECOMPUTATION_LEDGER_{DATE}.jsonl"
DISCREPANCY_PATH = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_DISCREPANCY_REPAIR_LEDGER_{DATE}.jsonl"
RECOMPUTATION_PATH = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json"
DECISION_PATH = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_DECISION_LEDGER_{DATE}.json"
SATURATION_PATH = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_SATURATION_SELF_RED_TEAM_{DATE}.json"
COMPLETION_PATH = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_COMPLETION_AUDIT_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_OUTPUT_MANIFEST_{DATE}.json"
SUMMARY_PATH = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_SUMMARY_{DATE}.md"
VERIFICATION_RESULT_PATH = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_VERIFICATION_RESULT_{DATE}.json"
FOCUSED_TEST_RESULT_PATH = ROUTE_DIR / f"G12_HAZ005_TRANSITION_CLOCK_REPAIR_AUDIT_FOCUSED_TEST_RESULT_{DATE}.json"

ARTIFACTS = [
    ("source_repair_recomputation", SOURCE_RECOMPUTATION_PATH),
    ("discrepancy_repair", DISCREPANCY_PATH),
    ("recomputation", RECOMPUTATION_PATH),
    ("decision", DECISION_PATH),
    ("saturation", SATURATION_PATH),
    ("completion", COMPLETION_PATH),
    ("summary", SUMMARY_PATH),
    ("builder", ROUTE_DIR / f"build_g12_haz005_transition_clock_repair_audit_{DATE.replace('-', '_')}.py"),
    ("verifier", ROUTE_DIR / f"verify_g12_haz005_transition_clock_repair_audit_{DATE.replace('-', '_')}.py"),
    ("focused_tests", ROUTE_DIR / f"test_g12_haz005_transition_clock_repair_audit_{DATE.replace('-', '_')}.py"),
    ("verification_result", VERIFICATION_RESULT_PATH),
    ("focused_test_result", FOCUSED_TEST_RESULT_PATH),
]

FORBIDDEN_TRUE_FIELDS = {
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_live_trading_behavior",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "changes_trading_risk_safety_prompt_decision_behavior",
}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO.resolve())).replace("\\", "/")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                yield line_number, json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def route_fields() -> dict[str, Any]:
    return {
        "route_id": G12_ROUTE_ID,
        "evidence_class": G12_EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_live_trading_behavior": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "changes_trading_risk_safety_prompt_decision_behavior": False,
    }


def safe_failures(payload: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    if payload.get("route_id") != G12_ROUTE_ID:
        failures.append(f"{label}: route_id mismatch")
    if payload.get("evidence_class") != G12_EVIDENCE_CLASS:
        failures.append(f"{label}: evidence_class mismatch")
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        failures.append(f"{label}: promotion_verdict mismatch")
    for field in FORBIDDEN_TRUE_FIELDS:
        if payload.get(field) is not False:
            failures.append(f"{label}: {field} must be false")
    return failures


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: Any = None) -> None:
    checks.append({"name": name, "ok": bool(ok), "detail": detail})


def refresh_manifest() -> None:
    outputs = []
    for key, path in ARTIFACTS:
        outputs.append({
            "artifact_key": key,
            "path": rel(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256_file(path) if path.exists() else None,
        })
    payload = {
        **route_fields(),
        "schema_version": "g12_haz005_output_manifest_v1",
        "artifact_family": "output_manifest",
        "generated_at_utc": now_utc(),
        "manifest_self_hash_policy": "manifest excludes itself from hash closure; verifier refreshes final manifest after verification/test artifacts exist",
        "outputs": outputs,
        "output_counts": {
            "source_repair_recomputation_rows": sum(1 for _ in iter_jsonl(SOURCE_RECOMPUTATION_PATH)) if SOURCE_RECOMPUTATION_PATH.exists() else 0,
            "discrepancy_repair_rows": sum(1 for _ in iter_jsonl(DISCREPANCY_PATH)) if DISCREPANCY_PATH.exists() else 0,
        },
    }
    write_json(MANIFEST_PATH, payload)


def verify(write_result: bool = True) -> tuple[bool, dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    required_paths = [
        SOURCE_RECOMPUTATION_PATH,
        DISCREPANCY_PATH,
        RECOMPUTATION_PATH,
        DECISION_PATH,
        SATURATION_PATH,
        COMPLETION_PATH,
        MANIFEST_PATH,
        SUMMARY_PATH,
    ]
    missing = [rel(path) for path in required_paths if not path.exists()]
    add_check(checks, "required_g12_artifacts_exist", not missing, missing)
    failures.extend(f"missing {path}" for path in missing)
    if missing:
        result = {
            **route_fields(),
            "schema_version": "g12_haz005_verification_result_v1",
            "artifact_family": "verification_result",
            "generated_at_utc": now_utc(),
            "ok": False,
            "checks": checks,
            "failures": failures,
        }
        if write_result:
            write_json(VERIFICATION_RESULT_PATH, result)
            refresh_manifest()
        return False, result

    recomputation = read_json(RECOMPUTATION_PATH)
    decision = read_json(DECISION_PATH)
    saturation = read_json(SATURATION_PATH)
    completion = read_json(COMPLETION_PATH)
    manifest = read_json(MANIFEST_PATH)

    safe_flag_failures: list[str] = []
    for label, payload in [
        ("recomputation", recomputation),
        ("decision", decision),
        ("saturation", saturation),
        ("completion", completion),
        ("manifest", manifest),
    ]:
        safe_flag_failures.extend(safe_failures(payload, label))
    add_check(checks, "g12_safe_flags_closed", not safe_flag_failures, safe_flag_failures)
    failures.extend(safe_flag_failures)

    source_rows = [row for _, row in iter_jsonl(SOURCE_RECOMPUTATION_PATH)]
    source_acceptance_counts = Counter(row.get("g12_acceptance_status") for row in source_rows)
    source_status_counts = Counter(row.get("g12_recomputed_repair_status") for row in source_rows)
    source_mismatches = [
        row["candidate_input_row_id"]
        for row in source_rows
        if row.get("g12_acceptance_status") == "G12_REPAIR_RECOMPUTATION_MISMATCH"
        or not row.get("status_match")
        or (row.get("frozen_repair_status") == "REPAIRED_FROM_LOCAL_SIERRA_CANDIDATE_REQUIRES_G12" and not (
            row.get("source_bar_hashes_match")
            and row.get("source_record_count_match")
            and row.get("source_byte_range_match")
            and row.get("packet_row_matches_repair_ledger")
        ))
    ]
    source_ok = (
        len(source_rows) == 790
        and source_status_counts == Counter({
            "NOT_REPAIRABLE_FROM_SEARCHED_SAME_EVIDENCE_CLASS_SOURCES": 785,
            "REPAIRED_FROM_LOCAL_SIERRA_CANDIDATE_REQUIRES_G12": 5,
        })
        and source_acceptance_counts == Counter({
            "BOUNDED_NOT_REPAIRABLE_FROM_SEARCHED_SOURCES": 785,
            "ACCEPT_SOURCE_REPAIR_CANDIDATE_AS_G12_CONTROL_EVIDENCE_ONLY": 5,
        })
        and not source_mismatches
    )
    add_check(checks, "source_repair_rows_recomputed_and_match", source_ok, {
        "rows": len(source_rows),
        "status_counts": dict(source_status_counts),
        "acceptance_counts": dict(source_acceptance_counts),
        "mismatches": source_mismatches,
    })
    if not source_ok:
        failures.append("source repair recomputation did not match expected 5 repaired / 785 bounded split")

    discrepancy_rows = [row for _, row in iter_jsonl(DISCREPANCY_PATH)]
    discrepancy_ok = bool(discrepancy_rows) and all(row.get("remaining_same_g12_issue") is False for row in discrepancy_rows)
    add_check(checks, "discrepancy_repairs_closed", discrepancy_ok, {
        "rows": len(discrepancy_rows),
        "issue_ids": [row.get("issue_id") for row in discrepancy_rows],
    })
    if not discrepancy_ok:
        failures.append("discrepancy repair ledger has unclosed same-G12 issues")

    decision_ok = (
        decision.get("accepted") is True
        and decision.get("terminal_decision") == "ACCEPT_AS_G12_READY8_HAZ005_TRANSITION_CLOCK_SOURCE_REPAIR_AUDIT_NO_PROMOTION"
        and decision.get("summary", {}).get("same_g12_repairable_remaining") == 0
        and decision.get("summary", {}).get("accepted_source_repair_candidate_rows") == 5
        and decision.get("summary", {}).get("bounded_not_repairable_rows") == 785
    )
    add_check(checks, "terminal_decision_accepts_source_control_only", decision_ok, decision.get("summary"))
    if not decision_ok:
        failures.append("terminal decision is not the expected G12 source-control acceptance")

    recomputation_ok = (
        recomputation.get("same_g12_issues") == []
        and recomputation.get("accepted_input_anchor", {}).get("counts", {}).get("haz005_target_status_counts", {}).get("COMPUTABLE") == 20292
        and recomputation.get("accepted_input_anchor", {}).get("counts", {}).get("haz005_target_status_counts", {}).get("FAIL_CLOSED_NOT_COMPUTABLE") == 3820
        and recomputation.get("builder_artifact_inventory", {}).get("all_hashes_match") is True
        and recomputation.get("builder_artifact_inventory", {}).get("all_sizes_match") is True
    )
    add_check(checks, "accepted_anchor_and_builder_inventory_verified", recomputation_ok, {
        "same_g12_issues": recomputation.get("same_g12_issues"),
        "haz005_target_status_counts": recomputation.get("accepted_input_anchor", {}).get("counts", {}).get("haz005_target_status_counts"),
        "artifact_inventory_hashes": recomputation.get("builder_artifact_inventory", {}).get("all_hashes_match"),
    })
    if not recomputation_ok:
        failures.append("accepted input anchor or builder inventory check failed")

    saturation_ok = (
        saturation.get("remaining_same_g12_repairable_issues") == 0
        and saturation.get("remaining_same_evidence_class_intelligence") == 0
        and saturation.get("no_arbitrary_top_n_policy_observed") is True
    )
    add_check(checks, "saturation_exhaustion_recorded", saturation_ok, saturation.get("all_material_rows_preserved"))
    if not saturation_ok:
        failures.append("saturation ledger does not record same-G12 exhaustion")

    checklist = completion.get("prompt_to_artifact_checklist", [])
    bad_statuses = [row for row in checklist if row.get("status") not in {"DONE", "DONE_AFTER_VERIFIER_AND_TEST"}]
    completion_ok = (
        not bad_statuses
        and completion.get("same_evidence_class_exhaustion", {}).get("same_g12_repairable_remaining") == 0
        and completion.get("safe_flags", {}).get("validation_safe_false") is True
    )
    add_check(checks, "completion_audit_maps_prompt_to_artifacts", completion_ok, bad_statuses)
    if not completion_ok:
        failures.append("completion audit is incomplete")

    manifest_rows = {row.get("artifact_key"): row for row in manifest.get("outputs", [])}
    manifest_failures: list[str] = []
    for key, path in ARTIFACTS:
        if key == "verification_result":
            continue
        row = manifest_rows.get(key)
        if not row:
            manifest_failures.append(f"{key}: missing from manifest")
            continue
        if not path.exists():
            if key == "focused_test_result":
                continue
            manifest_failures.append(f"{key}: path missing on disk")
            continue
        if row.get("sha256") != sha256_file(path) or row.get("size_bytes") != path.stat().st_size:
            if key == "focused_test_result" and not path.exists():
                continue
            manifest_failures.append(f"{key}: hash/size mismatch")
    add_check(checks, "manifest_hashes_match_disk_nonself", not manifest_failures, manifest_failures)
    failures.extend(manifest_failures)

    focused_result_ok = True
    focused_detail: Any = "not yet written"
    if FOCUSED_TEST_RESULT_PATH.exists():
        focused = read_json(FOCUSED_TEST_RESULT_PATH)
        focused_detail = focused
        focused_result_ok = focused.get("ok") is True and focused.get("tests_passed") == 4
    add_check(checks, "focused_pytest_evidence_when_present", focused_result_ok, focused_detail)
    if not focused_result_ok:
        failures.append("focused pytest evidence exists but does not pass")

    ok = not failures
    result = {
        **route_fields(),
        "schema_version": "g12_haz005_verification_result_v1",
        "artifact_family": "verification_result",
        "generated_at_utc": now_utc(),
        "ok": ok,
        "checks": checks,
        "failures": failures,
        "closeout_readiness": {
            "can_mark_goal_complete_after_verifier_tests_and_commit": ok,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    if write_result:
        write_json(VERIFICATION_RESULT_PATH, result)
        refresh_manifest()
    return ok, result


def main() -> None:
    ok, result = verify(write_result=True)
    print(json.dumps({"ok": ok, "verification_result": rel(VERIFICATION_RESULT_PATH)}, indent=2, sort_keys=True))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
