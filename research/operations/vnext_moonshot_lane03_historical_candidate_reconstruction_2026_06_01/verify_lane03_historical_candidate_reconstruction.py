#!/usr/bin/env python3
"""Verify Lane03 historical candidate reconstruction artifacts."""

from __future__ import annotations

import gzip
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

from build_lane03_historical_candidate_reconstruction import (
    BRANCH_DECISION_LEDGER,
    CANDIDATE_LEDGER,
    COMPLETION_AUDIT_PATH,
    CONTEXT_ANCHOR_PATH,
    DEPENDENCY_STATE_LEDGER,
    DUPLICATE_GROUP_LEDGER,
    DUPLICATE_POLICY_PATH,
    EVENT_LEDGER,
    MANIFEST_PATH,
    MECHANISM_COVERAGE_LEDGER,
    REQUIRED_MECHANISMS,
    REQUIRED_ROW_CLASSES,
    RESULT_USE_STATUS,
    ROUTE_ID,
    RUNTIME_EFFECT_BOUNDARY,
    SCHEMA_VERSION,
    SOURCE_GAP_LEDGER,
    SOURCE_INVENTORY_LEDGER,
    SUMMARY_PATH,
    build_manifest,
    json_dump_line,
    rel,
    utc_now,
)


VERIFICATION_RESULT = Path(__file__).resolve().parent / "LANE03_VERIFICATION_RESULT.json"


REQUIRED_OUTPUTS = [
    EVENT_LEDGER,
    CANDIDATE_LEDGER,
    DUPLICATE_GROUP_LEDGER,
    SOURCE_INVENTORY_LEDGER,
    SOURCE_GAP_LEDGER,
    MECHANISM_COVERAGE_LEDGER,
    DEPENDENCY_STATE_LEDGER,
    BRANCH_DECISION_LEDGER,
    SUMMARY_PATH,
    COMPLETION_AUDIT_PATH,
    CONTEXT_ANCHOR_PATH,
    DUPLICATE_POLICY_PATH,
]

REQUIRED_EVENT_FIELDS = [
    "canonical_event_id",
    "canonical_candidate_id",
    "canonical_duplicate_key",
    "source_id",
    "source_path",
    "source_line",
    "row_class",
    "source_use_state",
    "result_use_status",
    "runtime_effect_boundary",
]


def open_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if path.suffix == ".gz":
        handle_context = gzip.open(path, "rt", encoding="utf-8", errors="replace")
    else:
        handle_context = path.open("r", encoding="utf-8", errors="replace")
    with handle_context as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{rel(path)} line {line_number} is not valid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise AssertionError(f"{rel(path)} line {line_number} is not a JSON object")
            yield row


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise AssertionError(f"{rel(path)} is not a JSON object")
    return data


def source_family_counts() -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in open_jsonl(SOURCE_INVENTORY_LEDGER):
        category = row.get("category")
        family = row.get("row_family", "")
        source_path = row.get("source_path", "")
        parsed_rows = int(row.get("parsed_rows") or 0)
        if category == "full_replay" and row.get("process_events"):
            if "candidate_generation" in family:
                counts["full_replay_candidate_generation"] += parsed_rows
            if family == "denominator_disposition_ledger":
                counts["full_replay_denominator"] += parsed_rows
            if "path_outcome" in family:
                counts["full_replay_path_outcome_r"] += parsed_rows
        if source_path.endswith("LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_LEDGER.jsonl"):
            counts["may31_lane02_selected"] += parsed_rows
    return dict(counts)


def verify() -> dict[str, Any]:
    failures: list[str] = []
    for output in REQUIRED_OUTPUTS:
        if not output.exists():
            failures.append(f"missing required output: {rel(output)}")
        elif output.stat().st_size == 0:
            failures.append(f"empty required output: {rel(output)}")

    if failures:
        result = write_result(False, failures, {})
        return result

    summary = load_json(SUMMARY_PATH)
    source_inventory_rows = list(open_jsonl(SOURCE_INVENTORY_LEDGER))
    source_event_total = sum(int(row.get("event_rows") or 0) for row in source_inventory_rows)
    source_parsed_total = sum(int(row.get("parsed_rows") or 0) for row in source_inventory_rows)

    event_count = 0
    row_class_counts: Counter[str] = Counter()
    mechanism_counts: Counter[str] = Counter()
    runtime_boundaries: Counter[str] = Counter()
    result_use_statuses: Counter[str] = Counter()
    source_ids_seen: Counter[str] = Counter()
    for event in open_jsonl(EVENT_LEDGER):
        event_count += 1
        for field in REQUIRED_EVENT_FIELDS:
            if event.get(field) in (None, ""):
                failures.append(f"event row {event_count} missing {field}")
                break
        for row_class in event.get("row_classes", [event.get("row_class")]):
            if row_class:
                row_class_counts[str(row_class)] += 1
        mechanism_counts[str(event.get("mechanism_family", ""))] += 1
        runtime_boundaries[str(event.get("runtime_effect_boundary", ""))] += 1
        result_use_statuses[str(event.get("result_use_status", ""))] += 1
        source_ids_seen[str(event.get("source_id", ""))] += 1

    candidate_count = sum(1 for _ in open_jsonl(CANDIDATE_LEDGER))
    duplicate_count = sum(1 for _ in open_jsonl(DUPLICATE_GROUP_LEDGER))
    gap_rows = list(open_jsonl(SOURCE_GAP_LEDGER))
    dependency_rows = list(open_jsonl(DEPENDENCY_STATE_LEDGER))
    mechanism_rows = list(open_jsonl(MECHANISM_COVERAGE_LEDGER))

    if event_count != int(summary.get("total_event_rows") or -1):
        failures.append(f"event ledger count {event_count} != summary total_event_rows {summary.get('total_event_rows')}")
    if source_event_total != event_count:
        failures.append(f"source inventory event total {source_event_total} != event ledger count {event_count}")
    if source_parsed_total != int(summary.get("total_parsed_source_rows") or -1):
        failures.append(
            f"source inventory parsed total {source_parsed_total} != summary total_parsed_source_rows {summary.get('total_parsed_source_rows')}"
        )
    if candidate_count != int(summary.get("candidate_rows") or -1):
        failures.append(f"candidate ledger count {candidate_count} != summary candidate_rows {summary.get('candidate_rows')}")
    if duplicate_count != candidate_count:
        failures.append(f"duplicate group ledger count {duplicate_count} != candidate ledger count {candidate_count}")

    if set(runtime_boundaries) != {RUNTIME_EFFECT_BOUNDARY}:
        failures.append(f"unexpected runtime boundaries in event ledger: {dict(runtime_boundaries)}")
    if set(result_use_statuses) != {RESULT_USE_STATUS}:
        failures.append(f"unexpected result_use_status values in event ledger: {dict(result_use_statuses)}")

    missing_row_classes = REQUIRED_ROW_CLASSES - set(row_class_counts)
    missing_mechanisms = REQUIRED_MECHANISMS - set(mechanism_counts)
    gap_text = "\n".join(json.dumps(row, sort_keys=True) for row in gap_rows)
    for row_class in sorted(missing_row_classes):
        if row_class.replace(" ", "_") not in gap_text and row_class not in gap_text:
            failures.append(f"missing required row class without source gap row: {row_class}")
    for mechanism in sorted(missing_mechanisms):
        if mechanism not in gap_text:
            failures.append(f"missing required mechanism without source gap row: {mechanism}")

    dep_by_id = {row.get("dependency_id"): row for row in dependency_rows}
    for dep_id in ["june01_master_route", "june01_lane01_route", "june01_lane02_route"]:
        if dep_id not in dep_by_id:
            failures.append(f"dependency-state row missing for {dep_id}")
    lane01 = dep_by_id.get("june01_lane01_route")
    if lane01 and lane01.get("exists") and lane01.get("state") != "present":
        failures.append("june01_lane01_route has inconsistent dependency state")
    if lane01 and not lane01.get("exists") and "june01_lane01_route" not in gap_text:
        failures.append("absent June01 Lane01 route has no source gap row")

    mechanism_by_name = {row.get("mechanism_family"): row for row in mechanism_rows}
    for mechanism in REQUIRED_MECHANISMS:
        if mechanism not in mechanism_by_name:
            failures.append(f"mechanism coverage row missing for {mechanism}")

    family_counts = source_family_counts()
    expected_counts = {
        "full_replay_candidate_generation": 253234,
        "full_replay_denominator": 903163,
        "full_replay_path_outcome_r": 1978947,
        "may31_lane02_selected": 289600,
    }
    for key, expected in expected_counts.items():
        actual = family_counts.get(key)
        if actual is not None and actual != expected:
            failures.append(f"{key} parsed rows {actual} != expected {expected}")
        if actual is None and key != "may31_lane02_selected":
            failures.append(f"{key} source count missing from inventory")

    checks = {
        "event_count": event_count,
        "candidate_count": candidate_count,
        "duplicate_count": duplicate_count,
        "source_event_total": source_event_total,
        "source_parsed_total": source_parsed_total,
        "row_class_counts": dict(sorted(row_class_counts.items())),
        "mechanism_counts": dict(sorted(mechanism_counts.items())),
        "source_family_counts": family_counts,
        "gap_rows": len(gap_rows),
        "dependency_rows": len(dependency_rows),
    }
    result = write_result(not failures, failures, checks)
    if not failures:
        update_completion_audit(result)
        update_manifest()
    return result


def write_result(passed: bool, failures: list[str], checks: dict[str, Any]) -> dict[str, Any]:
    result = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "verified_at_utc": utc_now(),
        "passed": passed,
        "failure_count": len(failures),
        "failures": failures,
        "checks": checks,
        "runtime_effect_boundary": RUNTIME_EFFECT_BOUNDARY,
        "result_use_status": RESULT_USE_STATUS,
    }
    VERIFICATION_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def update_completion_audit(result: dict[str, Any]) -> None:
    audit = load_json(COMPLETION_AUDIT_PATH)
    audit["status"] = "complete_verified"
    audit["verification_result"] = {
        "path": rel(VERIFICATION_RESULT),
        "passed": result["passed"],
        "verified_at_utc": result["verified_at_utc"],
    }
    COMPLETION_AUDIT_PATH.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def update_manifest() -> None:
    manifest_paths = REQUIRED_OUTPUTS + [VERIFICATION_RESULT]
    manifest = build_manifest(manifest_paths)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
