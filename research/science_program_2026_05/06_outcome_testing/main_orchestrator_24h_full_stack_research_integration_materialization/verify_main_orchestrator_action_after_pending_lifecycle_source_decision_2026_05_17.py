"""Verify pending-lifecycle source decision materialization."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_SOURCE_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_SOURCE_DECISION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_SOURCE_DECISION_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_SOURCE_DECISION_VERIFICATION_RESULT_{DATE}.json"

OLD_COMPLETE_RECONSTRUCTED = "KEEP_PENDING_LIFECYCLE_SCORER_WITH_RECONSTRUCTED_SOURCE_FIELDS_COMPLETE"
OLD_COMPLETE_CAPTURE = "KEEP_PENDING_LIFECYCLE_SCORER_WITH_CAPTURE_FIELDS_COMPLETE"
OLD_PARTIAL_DERIVED = "KEEP_PENDING_LIFECYCLE_SCORER_WITH_DERIVED_SOURCE_FIELDS_CURRENT_ROWS_PARTIAL"
OLD_PARTIAL_FORWARD = "KEEP_PENDING_LIFECYCLE_SCORER_FORWARD_CAPTURE_FIELDS_IMPLEMENTED_CURRENT_ROWS_PARTIAL"
IMPLEMENT_RECONSTRUCTED = "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_RECONSTRUCTED_SOURCE_SCORER"
REDESIGN_R_REQUIRED = "REDESIGN_PENDING_LIFECYCLE_R_OUTCOME_SOURCE_REQUIRED"
REDESIGN_SOURCE_PARTIAL = "REDESIGN_PENDING_LIFECYCLE_SOURCE_PARTIAL_REPAIR_REQUIRED"
MERGE_DUPLICATE_DERIVATION = "MERGE_DUPLICATE_PENDING_SOURCE_DERIVATION_ROW_INTO_CANONICAL_PENDING_SCORER"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def proxy_summary(rows: list[dict[str, Any]]) -> tuple[int, float]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return len(values), round(sum(values), 8)


def require(condition: bool, issues: list[str], message: str) -> None:
    if not condition:
        issues.append(message)


def stripped(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "pending_lifecycle_source_decision_status"}


def preservation_ok(row: dict[str, Any]) -> bool:
    required = (
        "opportunity_owner_row_id",
        "opportunity_owner_source_artifact",
        "opportunity_proxy_reference_status",
        "opportunity_not_independently_countable_reason",
        "opportunity_useful_mechanism",
        "opportunity_downstream_paths",
    )
    return (
        all(row.get(key) not in (None, "", []) for key in required)
        and isinstance(row.get("missed_opportunity_audit"), dict)
        and row.get("underlying_intelligence_preserved") is True
    )


def main() -> None:
    issues: list[str] = []
    before_rows = read_jsonl(INPUT_LEDGER)
    rows = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)

    require(len(rows) == 3426, issues, f"expected 3426 rows got {len(rows)}")
    require([row.get("row_id") for row in before_rows] == [row.get("row_id") for row in rows], issues, "row identity/order changed")
    before_by_id = {row.get("row_id"): row for row in before_rows}

    before_counts = Counter(str(row.get("action_class") or "") for row in before_rows)
    counts = Counter(str(row.get("action_class") or "") for row in rows)
    require(
        before_counts == Counter({"REDESIGN": 1572, "KILL": 967, "IMPLEMENT_DEFAULT_OFF": 452, "KEEP": 435}),
        issues,
        f"unexpected input action counts {before_counts}",
    )
    require(
        counts == Counter({"REDESIGN": 1614, "KILL": 967, "IMPLEMENT_DEFAULT_OFF": 488, "KEEP": 357}),
        issues,
        f"unexpected output action counts {counts}",
    )
    require(proxy_summary(before_rows) == (710, 33.19811387), issues, f"input proxy mismatch {proxy_summary(before_rows)}")
    require(proxy_summary(rows) == (709, 33.19811387), issues, f"output proxy mismatch {proxy_summary(rows)}")

    converted = [
        row
        for row in rows
        if row.get("pending_lifecycle_source_decision_status") not in (None, "NOT_TARGET_ROW")
    ]
    require(len(converted) == 78, issues, f"expected 78 converted rows got {len(converted)}")
    require(
        all(before_by_id[row.get("row_id")].get("action_class") == "KEEP" for row in converted),
        issues,
        "converted row did not originate as keep",
    )
    require(
        Counter(row.get("branch_decision") for row in converted)
        == Counter(
            {
                IMPLEMENT_RECONSTRUCTED: 36,
                REDESIGN_R_REQUIRED: 2,
                REDESIGN_SOURCE_PARTIAL: 1,
                MERGE_DUPLICATE_DERIVATION: 39,
            }
        ),
        issues,
        f"converted branch split mismatch {Counter(row.get('branch_decision') for row in converted)}",
    )
    require(
        Counter(row.get("action_class") for row in converted)
        == Counter({"IMPLEMENT_DEFAULT_OFF": 36, "REDESIGN": 42}),
        issues,
        f"converted action split mismatch {Counter(row.get('action_class') for row in converted)}",
    )

    impl_rows = [row for row in converted if row.get("branch_decision") == IMPLEMENT_RECONSTRUCTED]
    r_missing_rows = [row for row in converted if row.get("branch_decision") == REDESIGN_R_REQUIRED]
    partial_rows = [row for row in converted if row.get("branch_decision") == REDESIGN_SOURCE_PARTIAL]
    duplicate_rows = [row for row in converted if row.get("branch_decision") == MERGE_DUPLICATE_DERIVATION]

    require(sum(safe_float(row.get("after_proxy_r")) is not None for row in impl_rows) == 36, issues, "implemented rows must keep numeric R")
    require(round(sum(safe_float(row.get("after_proxy_r")) or 0.0 for row in impl_rows), 8) == 0.0, issues, "implemented pending R sum changed")
    require(all(safe_float(row.get("after_proxy_r")) is None for row in r_missing_rows), issues, "R-missing rows counted proxy")
    require(all(safe_float(row.get("after_proxy_r")) is None for row in partial_rows), issues, "partial source row counted proxy")
    require(all(safe_float(row.get("after_proxy_r")) is None for row in duplicate_rows), issues, "duplicate derivation row counted proxy")
    require(len(partial_rows) == 1 and safe_float(partial_rows[0].get("opportunity_proxy_r_reference")) == 0.0, issues, "canonical partial row proxy reference mismatch")
    require(all(row.get("pending_lifecycle_proxy_reference_counted_as_r") is False for row in partial_rows + duplicate_rows), issues, "reference-only flag missing")
    require(all(preservation_ok(row) for row in r_missing_rows + partial_rows + duplicate_rows), issues, "redesign/merge row missing opportunity preservation")
    require(all(row.get("safe_flags") == SAFE_FLAGS for row in converted), issues, "converted safe flags mismatch")

    non_target_diffs = [
        row.get("row_id")
        for row in rows
        if row.get("pending_lifecycle_source_decision_status") == "NOT_TARGET_ROW"
        and stripped(row) != stripped(before_by_id[row.get("row_id")])
    ]
    require(not non_target_diffs, issues, f"non-target rows changed {non_target_diffs[:5]}")
    branch_counts = Counter(row.get("branch_decision") for row in rows)
    for old_branch in {OLD_COMPLETE_RECONSTRUCTED, OLD_COMPLETE_CAPTURE, OLD_PARTIAL_DERIVED, OLD_PARTIAL_FORWARD}:
        require(branch_counts.get(old_branch, 0) == 0, issues, f"old pending branch remains {old_branch}")

    require(summary.get("pending_lifecycle_source_decision_rows") == 78, issues, "summary converted rows mismatch")
    require(summary.get("source_complete_numeric_implemented_rows") == 36, issues, "summary implemented rows mismatch")
    require(summary.get("source_complete_r_missing_redesign_rows") == 2, issues, "summary R-missing rows mismatch")
    require(summary.get("canonical_partial_source_repair_rows") == 1, issues, "summary canonical partial mismatch")
    require(summary.get("duplicate_source_derivation_merged_rows") == 39, issues, "summary duplicate merge mismatch")
    require(summary.get("rows_removed_from_keep") == 78, issues, "summary keep removal mismatch")
    require(summary.get("rows_added_to_implementation") == 36, issues, "summary implementation rows mismatch")
    require(summary.get("rows_added_to_redesign") == 42, issues, "summary redesign rows mismatch")
    require(summary.get("numeric_proxy_rows_after") == 709, issues, "summary proxy row mismatch")
    require(summary.get("proxy_r_sum_after") == 33.19811387, issues, "summary proxy sum mismatch")
    require(summary.get("proxy_rows_removed_from_counted_denominator") == 1, issues, "summary removed proxy rows mismatch")
    require(summary.get("proxy_r_sum_removed_from_counted_denominator") == 0.0, issues, "summary removed proxy sum mismatch")
    require(summary.get("remaining_old_pending_keep_branch_rows") == 0, issues, "summary old branches remain")
    require(summary.get("redesign_missing_audit_after") == 0, issues, "summary redesign audit gaps")
    require(summary.get("redesign_missing_underlying_intel_after") == 0, issues, "summary redesign intel gaps")
    require(manifest.get("safe_flags") == SAFE_FLAGS, issues, "manifest safe flags mismatch")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "action_class_counts_after": dict(sorted(counts.items())),
        "numeric_proxy_rows_after": proxy_summary(rows)[0],
        "proxy_r_sum_after": proxy_summary(rows)[1],
        "pending_lifecycle_source_decision_rows": summary.get("pending_lifecycle_source_decision_rows"),
        "source_complete_numeric_implemented_rows": summary.get("source_complete_numeric_implemented_rows"),
        "source_complete_r_missing_redesign_rows": summary.get("source_complete_r_missing_redesign_rows"),
        "canonical_partial_source_repair_rows": summary.get("canonical_partial_source_repair_rows"),
        "duplicate_source_derivation_merged_rows": summary.get("duplicate_source_derivation_merged_rows"),
        "proxy_rows_removed_from_counted_denominator": summary.get("proxy_rows_removed_from_counted_denominator"),
        "proxy_r_sum_removed_from_counted_denominator": summary.get("proxy_r_sum_removed_from_counted_denominator"),
        "safe_flags": summary.get("safe_flags"),
    }
    write_json(OUTPUT_VERIFICATION, result)
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
