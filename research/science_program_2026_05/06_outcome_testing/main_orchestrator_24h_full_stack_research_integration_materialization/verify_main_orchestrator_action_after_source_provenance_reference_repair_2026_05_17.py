"""Verify source-provenance reference repair materialization."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_VERIFICATION_RESULT_{DATE}.json"

GENERIC_BRANCH = "PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR"
POSITIVE_BRANCH = "PRESERVE_SOURCE_PROVENANCE_EXCLUDE_SCALAR_POSITIVE_RSTYLE_REFERENCE"
NEGATIVE_BRANCH = "PRESERVE_SOURCE_PROVENANCE_EXCLUDE_SCALAR_NEGATIVE_RSTYLE_REFERENCE_AVOID_CONTEXT"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def without_status(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "source_provenance_reference_repair_status"}


def main() -> None:
    issues: list[str] = []
    before_rows = read_jsonl(INPUT_LEDGER)
    rows = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)

    require(len(rows) == 3426, issues, f"expected 3426 rows, got {len(rows)}")
    require([row.get("row_id") for row in before_rows] == [row.get("row_id") for row in rows], issues, "row identity/order changed")

    before_counts = Counter(row.get("action_class") for row in before_rows)
    counts = Counter(row.get("action_class") for row in rows)
    require(counts == before_counts, issues, f"action counts changed: before={before_counts}, after={counts}")

    before_proxy = proxy_summary(before_rows)
    after_proxy = proxy_summary(rows)
    require(before_proxy == (710, 33.19811387), issues, f"unexpected input proxy state {before_proxy}")
    require(after_proxy == before_proxy, issues, f"proxy denominator changed: {after_proxy}")

    before_branch_counts = Counter(row.get("branch_decision") for row in before_rows)
    branch_counts = Counter(row.get("branch_decision") for row in rows)
    require(before_branch_counts.get(GENERIC_BRANCH) == 9, issues, f"unexpected input generic preserve rows {before_branch_counts.get(GENERIC_BRANCH)}")
    require(branch_counts.get(GENERIC_BRANCH, 0) == 0, issues, f"generic no-scalar branch remains {branch_counts.get(GENERIC_BRANCH, 0)}")
    require(branch_counts.get(POSITIVE_BRANCH) == 7, issues, f"positive source-provenance rows wrong {branch_counts.get(POSITIVE_BRANCH)}")
    require(branch_counts.get(NEGATIVE_BRANCH) == 2, issues, f"negative source-provenance rows wrong {branch_counts.get(NEGATIVE_BRANCH)}")

    before_by_id = {row.get("row_id"): row for row in before_rows}
    changed = [
        row
        for row in rows
        if row.get("source_provenance_reference_repair_status")
        == "MOONSHOT_UNIFIED_SOURCE_PROVENANCE_CONSUMED_REFERENCE_ONLY"
    ]
    require(len(changed) == 9, issues, f"expected 9 source provenance rows, got {len(changed)}")
    require(
        all(before_by_id[row.get("row_id")].get("branch_decision") == GENERIC_BRANCH for row in changed),
        issues,
        "changed row did not originate from generic no-scalar branch",
    )
    require(all(row.get("action_class") == "PRESERVE_REQUIREMENT" for row in changed), issues, "changed rows must stay preserve requirements")
    require(all(row.get("after_proxy_r") is None for row in changed), issues, "changed rows should not count proxy R")
    require(all(row.get("current_claim_proxy_counted") is False for row in changed), issues, "changed rows should have proxy counted false")
    require(all(row.get("underlying_intelligence_preserved") is True for row in changed), issues, "changed rows missing preserved intelligence")
    require(all(row.get("missed_opportunity_audit") for row in changed), issues, "changed rows missing missed-opportunity audit")
    require(
        all(row.get("source_requirement_preserved") is True for row in changed),
        issues,
        "source requirement not preserved on changed rows",
    )
    require(
        all(row.get("source_provenance_reference_status") == "REFERENCE_ONLY_NOT_COUNTED_EXCLUDED_FROM_SCALAR_IMPLEMENTATION" for row in changed),
        issues,
        "source provenance reference status wrong",
    )
    require(
        all(row.get("source_provenance_reference_payload", {}).get("action_execution_class") == "BRANCH_PROVENANCE_PRESERVE_EXCLUDE_SCALAR" for row in changed),
        issues,
        "moonshot action execution class not preserved",
    )
    require(
        all(row.get("source_provenance_reference_payload", {}).get("unified_execution_decision") == "PRESERVE_PROVENANCE_REQUIREMENT" for row in changed),
        issues,
        "moonshot unified decision not preserved",
    )
    rstyle_midpoints = [float(row["source_provenance_rstyle_midpoint_reference"]) for row in changed]
    candidate_scores = [float(row["source_provenance_candidate_score_proxy_reference"]) for row in changed]
    require(round(sum(rstyle_midpoints), 8) == 1.64594, issues, f"rstyle midpoint reference sum changed {round(sum(rstyle_midpoints), 8)}")
    require(sum(value >= 0 for value in rstyle_midpoints) == 7, issues, "positive rstyle split wrong")
    require(sum(value < 0 for value in rstyle_midpoints) == 2, issues, "negative rstyle split wrong")
    require(round(sum(candidate_scores), 8) == -3.695919, issues, f"candidate score proxy sum changed {round(sum(candidate_scores), 8)}")

    non_target_diffs = [
        row.get("row_id")
        for row in rows
        if row.get("source_provenance_reference_repair_status") == "NOT_TARGET_ROW"
        and without_status(row) != without_status(before_by_id[row.get("row_id")])
    ]
    require(not non_target_diffs, issues, f"non-target rows changed: {non_target_diffs[:5]}")

    remaining_preserve = [row for row in rows if row.get("action_class") == "PRESERVE_REQUIREMENT"]
    require(len(remaining_preserve) == 9, issues, f"expected 9 remaining preserve rows, got {len(remaining_preserve)}")
    require(
        Counter(row.get("branch_decision") for row in remaining_preserve)
        == Counter({POSITIVE_BRANCH: 7, NEGATIVE_BRANCH: 2}),
        issues,
        f"unexpected remaining preserve branches {Counter(row.get('branch_decision') for row in remaining_preserve)}",
    )
    require(
        not any(safe_float(row.get("after_proxy_r")) is not None for row in remaining_preserve),
        issues,
        "remaining preserve rows should not carry counted numeric proxy R",
    )

    missing_audit = sum(
        1
        for row in rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and not row.get("missed_opportunity_audit")
    )
    missing_intel = sum(
        1
        for row in rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and row.get("underlying_intelligence_preserved") is not True
    )
    require(missing_audit == 0, issues, f"missing missed-opportunity audits after repair: {missing_audit}")
    require(missing_intel == 0, issues, f"missing underlying-intelligence preservation after repair: {missing_intel}")

    require(summary.get("source_provenance_reference_rows") == 9, issues, "summary reference row count wrong")
    require(summary.get("generic_no_scalar_preserve_rows_after") == 0, issues, "summary generic no-scalar count wrong")
    require(summary.get("source_provenance_rstyle_midpoint_sum_referenced_not_counted") == 1.64594, issues, "summary rstyle sum wrong")
    require(summary.get("source_provenance_candidate_score_proxy_sum_referenced_not_counted") == -3.695919, issues, "summary candidate score sum wrong")
    require(summary.get("numeric_proxy_rows_after") == 710, issues, "summary numeric proxy rows wrong")
    require(summary.get("proxy_r_sum_after") == 33.19811387, issues, "summary proxy sum wrong")
    require(summary.get("remaining_preserve_requirement_rows") == 9, issues, "summary remaining preserve count wrong")
    require(summary.get("remaining_numeric_preserve_requirement_rows") == 0, issues, "summary remaining numeric preserve count wrong")
    require(summary.get("moonshot_snapshot", {}).get("source_ledger_sha256"), issues, "moonshot source hash missing")
    require(summary.get("moonshot_snapshot", {}).get("source_ledger_size_bytes", 0) > 0, issues, "moonshot source size missing")
    require(manifest.get("safe_flags", {}).get("NO_PROMOTION_VERDICT") is True, issues, "manifest safe flag missing")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "action_class_counts_after": dict(sorted(counts.items())),
        "numeric_proxy_rows_after": after_proxy[0],
        "proxy_r_sum_after": after_proxy[1],
        "source_provenance_reference_rows": summary.get("source_provenance_reference_rows"),
        "generic_no_scalar_preserve_rows_after": summary.get("generic_no_scalar_preserve_rows_after"),
        "source_provenance_rstyle_midpoint_sum_referenced_not_counted": summary.get(
            "source_provenance_rstyle_midpoint_sum_referenced_not_counted"
        ),
        "source_provenance_candidate_score_proxy_sum_referenced_not_counted": summary.get(
            "source_provenance_candidate_score_proxy_sum_referenced_not_counted"
        ),
        "remaining_preserve_requirement_rows": summary.get("remaining_preserve_requirement_rows"),
        "remaining_preserve_requirement_branch_counts": summary.get("remaining_preserve_requirement_branch_counts"),
        "safe_flags": summary.get("safe_flags"),
    }
    write_json(OUTPUT_VERIFICATION, result)
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
