#!/usr/bin/env python3
"""Verify the READY8 R7 expanded sealed-validation packet design."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-15"
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
REQUIRED_STATUS_CLASSES = {
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


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(name: str) -> dict[str, Any]:
    with (ROUTE_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(name: str) -> list[dict[str, Any]]:
    rows = []
    with (ROUTE_DIR / name).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def check_safe_payload(payload: Any, path: str, errors: list[str]) -> None:
    if isinstance(payload, dict):
        if payload.get("promotion_verdict") not in (None, "NO_PROMOTION_VERDICT"):
            errors.append(f"{path}: promotion_verdict={payload.get('promotion_verdict')}")
        for key in SAFE_FALSE_KEYS:
            if key in payload and payload[key] is not False:
                errors.append(f"{path}: {key}={payload[key]}")
        for key, value in payload.items():
            check_safe_payload(value, f"{path}.{key}", errors)
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            check_safe_payload(value, f"{path}[{index}]", errors)


def line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def main() -> int:
    errors: list[str] = []
    expected_files = [
        f"READY8_EXPANDED_PACKET_CONTEXT_ANCHOR_{DATE}.json",
        f"READY8_EXPANDED_PACKET_PREREQUISITE_ACCEPTANCE_INSPECTION_LEDGER_{DATE}.json",
        f"READY8_EXPANDED_PACKET_ARTIFACT_REVIEW_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_PACKET_SURVIVING_MECHANISM_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_PACKET_BRANCH_CLASSIFICATION_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_PACKET_KILLED_DEFERRED_MECHANISM_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_PACKET_SOURCE_UNIVERSE_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_PACKET_PARTITION_LEDGER_{DATE}.json",
        f"READY8_EXPANDED_PACKET_NO_LEAK_ASOF_EMBARGO_POLICY_{DATE}.json",
        f"READY8_EXPANDED_PACKET_DUPLICATE_DENOMINATOR_POLICY_{DATE}.json",
        f"READY8_EXPANDED_PACKET_CONCENTRATION_EFFECTIVE_N_PRECHECKS_{DATE}.jsonl",
        f"READY8_EXPANDED_PACKET_TARGET_FAMILY_HORIZON_POLICY_{DATE}.json",
        f"READY8_EXPANDED_PACKET_FAIL_CLOSED_INCLUSION_EXCLUSION_POLICY_{DATE}.json",
        f"READY8_EXPANDED_PACKET_ADVERSARIAL_PLACEBO_CONTROL_POLICY_{DATE}.json",
        f"READY8_EXPANDED_PACKET_ROWSET_DESIGN_{DATE}.jsonl",
        f"READY8_EXPANDED_PACKET_REPAIRED_TARGET_CONSUMPTION_LEDGER_{DATE}.jsonl",
        f"READY8_EXPANDED_PACKET_SOURCE_HASH_LEDGER_{DATE}.json",
        f"READY8_EXPANDED_PACKET_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
        f"READY8_EXPANDED_PACKET_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        f"READY8_EXPANDED_PACKET_COMPLETION_AUDIT_{DATE}.json",
        f"READY8_EXPANDED_PACKET_DECISION_LEDGER_{DATE}.json",
        f"READY8_EXPANDED_PACKET_SYNTHESIS_{DATE}.md",
        f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_GOAL_PROMPT_{DATE}.md",
        f"G12_READY8_EXPANDED_PACKET_DESIGN_REVIEW_STARTER_{DATE}.txt",
        f"READY8_EXPANDED_PACKET_FOCUSED_TEST_RESULT_{DATE}.json",
        f"READY8_EXPANDED_PACKET_OUTPUT_MANIFEST_{DATE}.json",
    ]
    for name in expected_files:
        if not (ROUTE_DIR / name).exists():
            errors.append(f"missing {name}")

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2, sort_keys=True))
        return 1

    manifest = load_json(f"READY8_EXPANDED_PACKET_OUTPUT_MANIFEST_{DATE}.json")
    for record in manifest.get("files", []):
        path = ROOT / record["path"]
        if not path.exists():
            errors.append(f"manifest missing file {record['path']}")
            continue
        if sha256_file(path) != record["sha256"]:
            errors.append(f"manifest hash mismatch {record['path']}")
        if path.suffix == ".jsonl" and line_count(path) != record["jsonl_rows"]:
            errors.append(f"manifest jsonl row mismatch {record['path']}")

    prerequisites = load_json(f"READY8_EXPANDED_PACKET_PREREQUISITE_ACCEPTANCE_INSPECTION_LEDGER_{DATE}.json")
    if not prerequisites.get("all_prerequisites_accepted"):
        errors.append("not all prerequisites accepted")
    if prerequisites.get("prerequisite_count") != 7:
        errors.append(f"unexpected prerequisite_count {prerequisites.get('prerequisite_count')}")

    branch_rows = read_jsonl(f"READY8_EXPANDED_PACKET_BRANCH_CLASSIFICATION_LEDGER_{DATE}.jsonl")
    status_counts = Counter(row.get("branch_status") for row in branch_rows)
    missing_statuses = sorted(REQUIRED_STATUS_CLASSES - set(status_counts))
    if missing_statuses:
        errors.append(f"missing branch statuses {missing_statuses}")
    if any(row.get("kill_scope") == "whole_branch_intelligence" for row in branch_rows):
        errors.append("found whole-branch intelligence kill")
    if len(branch_rows) < 2800:
        errors.append(f"branch classification ledger too small {len(branch_rows)}")

    killed_rows = read_jsonl(f"READY8_EXPANDED_PACKET_KILLED_DEFERRED_MECHANISM_LEDGER_{DATE}.jsonl")
    if not killed_rows:
        errors.append("killed/deferred ledger empty")
    for row in killed_rows:
        if row.get("kill_scope") != "unsupported_edge_claim_only_not_branch_intelligence":
            errors.append(f"bad kill scope {row.get('branch_classification_row_id')}")
            break

    packet_rows = read_jsonl(f"READY8_EXPANDED_PACKET_ROWSET_DESIGN_{DATE}.jsonl")
    if len(packet_rows) != 182:
        errors.append(f"unexpected packet rowset count {len(packet_rows)}")

    repaired_rows = read_jsonl(f"READY8_EXPANDED_PACKET_REPAIRED_TARGET_CONSUMPTION_LEDGER_{DATE}.jsonl")
    if len(repaired_rows) != 5320:
        errors.append(f"unexpected repaired target row count {len(repaired_rows)}")

    fail_closed_policy = load_json(f"READY8_EXPANDED_PACKET_FAIL_CLOSED_INCLUSION_EXCLUSION_POLICY_{DATE}.json")
    if fail_closed_policy.get("remaining_fail_closed_target_rows") != 25240:
        errors.append("remaining fail-closed target rows changed")
    if fail_closed_policy.get("role_excluded_rows_unchanged") != 5251:
        errors.append("role-excluded rows changed")

    coverage = load_json(f"READY8_EXPANDED_PACKET_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json")
    if not coverage.get("failure_intelligence_doctrine_applied"):
        errors.append("failure intelligence doctrine not marked applied")
    if coverage.get("arbitrary_cutoff_used"):
        errors.append("arbitrary cutoff marked used")

    completion = load_json(f"READY8_EXPANDED_PACKET_COMPLETION_AUDIT_{DATE}.json")
    if completion.get("missing_or_incomplete_items"):
        errors.append("completion audit has missing items")

    for path in ROUTE_DIR.iterdir():
        if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl"}:
            continue
        if path.name == f"READY8_EXPANDED_PACKET_VERIFICATION_RESULT_{DATE}.json":
            continue
        if path.suffix.lower() == ".json":
            check_safe_payload(load_json(path.name), path.name, errors)
        else:
            for index, row in enumerate(read_jsonl(path.name), start=1):
                check_safe_payload(row, f"{path.name}:{index}", errors)

    result = {
        "ok": not errors,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "route_dir": rel(ROUTE_DIR),
        "checks": {
            "expected_files_present": not any(error.startswith("missing ") for error in errors),
            "manifest_hashes_match": not any("manifest hash mismatch" in error for error in errors),
            "safe_flags_ok": not any("validation_safe=" in error or "promotion_verdict=" in error or "live_effect=" in error for error in errors),
            "prerequisites_accepted": prerequisites.get("all_prerequisites_accepted"),
            "branch_status_counts": dict(status_counts),
            "killed_rows": len(killed_rows),
            "packet_rows": len(packet_rows),
            "repaired_target_rows": len(repaired_rows),
        },
        "errors": errors,
    }
    output = ROUTE_DIR / f"READY8_EXPANDED_PACKET_VERIFICATION_RESULT_{DATE}.json"
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
