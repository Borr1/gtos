"""Verify source-provenance context decision materialization."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_VERIFICATION_RESULT_{DATE}.json"

POSITIVE_REFERENCE_BRANCH = "PRESERVE_SOURCE_PROVENANCE_EXCLUDE_SCALAR_POSITIVE_RSTYLE_REFERENCE"
NEGATIVE_REFERENCE_BRANCH = "PRESERVE_SOURCE_PROVENANCE_EXCLUDE_SCALAR_NEGATIVE_RSTYLE_REFERENCE_AVOID_CONTEXT"
POSITIVE_DECISION_BRANCH = "IMPLEMENT_DEFAULT_OFF_SOURCE_PROVENANCE_CONTEXT_FEATURE_REFERENCE"
NEGATIVE_DECISION_BRANCH = "REDESIGN_SOURCE_PROVENANCE_AVOID_CONTEXT_FEATURE_REFERENCE"
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
    return {key: value for key, value in row.items() if key != "source_provenance_context_decision_status"}


def has_preservation(row: dict[str, Any]) -> bool:
    required = (
        "opportunity_preservation_status",
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
        before_counts == Counter({"KILL": 967, "REDESIGN": 1570, "KEEP": 435, "IMPLEMENT_DEFAULT_OFF": 445, "PRESERVE_REQUIREMENT": 9}),
        issues,
        f"unexpected input action counts {before_counts}",
    )
    require(
        counts == Counter({"KILL": 967, "REDESIGN": 1572, "KEEP": 435, "IMPLEMENT_DEFAULT_OFF": 452}),
        issues,
        f"unexpected output action counts {counts}",
    )
    require(proxy_summary(before_rows) == (710, 33.19811387), issues, f"input proxy mismatch {proxy_summary(before_rows)}")
    require(proxy_summary(rows) == (710, 33.19811387), issues, f"output proxy mismatch {proxy_summary(rows)}")

    converted = [
        row
        for row in rows
        if row.get("source_provenance_removed_from_preserve_requirement") is True
    ]
    require(len(converted) == 9, issues, f"expected 9 converted rows got {len(converted)}")
    require(
        all(before_by_id[row.get("row_id")].get("action_class") == "PRESERVE_REQUIREMENT" for row in converted),
        issues,
        "converted row did not originate as preserve requirement",
    )
    require(
        Counter(row.get("branch_decision") for row in converted)
        == Counter({POSITIVE_DECISION_BRANCH: 7, NEGATIVE_DECISION_BRANCH: 2}),
        issues,
        f"converted branch split mismatch {Counter(row.get('branch_decision') for row in converted)}",
    )
    require(
        Counter(row.get("action_class") for row in converted)
        == Counter({"IMPLEMENT_DEFAULT_OFF": 7, "REDESIGN": 2}),
        issues,
        f"converted action split mismatch {Counter(row.get('action_class') for row in converted)}",
    )
    refs = [safe_float(row.get("opportunity_proxy_r_reference")) for row in converted]
    refs = [value for value in refs if value is not None]
    require(len(refs) == 9, issues, "converted rows missing proxy references")
    require(round(sum(refs), 8) == 1.64594, issues, f"reference sum mismatch {round(sum(refs), 8)}")
    require(sum(value >= 0 for value in refs) == 7, issues, "positive ref split mismatch")
    require(sum(value < 0 for value in refs) == 2, issues, "negative ref split mismatch")
    candidate_scores = [
        safe_float(row.get("source_provenance_candidate_score_proxy_reference"))
        for row in converted
    ]
    candidate_scores = [value for value in candidate_scores if value is not None]
    require(round(sum(candidate_scores), 8) == -3.695919, issues, f"candidate score sum mismatch {round(sum(candidate_scores), 8)}")
    require(all(row.get("after_proxy_r") is None for row in converted), issues, "converted row counted after_proxy_r")
    require(all(row.get("source_provenance_proxy_reference_counted_as_r") is False for row in converted), issues, "converted row counted proxy ref")
    require(all(row.get("safe_flags") == SAFE_FLAGS for row in converted), issues, "converted row safe flags mismatch")
    require(all(has_preservation(row) for row in converted), issues, "converted row missing opportunity preservation")
    require(
        all((row.get("missed_opportunity_audit") or {}).get("kill_scope") == "NOT_KILLED_SOURCE_PROVENANCE_CONTEXT_DECISION" for row in converted),
        issues,
        "converted row audit scope mismatch",
    )

    non_target_diffs = [
        row.get("row_id")
        for row in rows
        if row.get("source_provenance_context_decision_status") == "NOT_TARGET_ROW"
        and stripped(row) != stripped(before_by_id[row.get("row_id")])
    ]
    require(not non_target_diffs, issues, f"non-target rows changed {non_target_diffs[:5]}")
    require(
        Counter(row.get("branch_decision") for row in rows).get(POSITIVE_REFERENCE_BRANCH, 0) == 0,
        issues,
        "positive preserve branch remains",
    )
    require(
        Counter(row.get("branch_decision") for row in rows).get(NEGATIVE_REFERENCE_BRANCH, 0) == 0,
        issues,
        "negative preserve branch remains",
    )
    require(sum(row.get("action_class") == "PRESERVE_REQUIREMENT" for row in rows) == 0, issues, "preserve requirement rows remain")

    missing_audit = sum(
        row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and not isinstance(row.get("missed_opportunity_audit"), dict)
        for row in rows
    )
    missing_intel = sum(
        row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and row.get("underlying_intelligence_preserved") is not True
        for row in rows
    )
    require(missing_audit == 0, issues, f"missing audits after decision {missing_audit}")
    require(missing_intel == 0, issues, f"missing intelligence preservation after decision {missing_intel}")

    require(summary.get("source_provenance_context_decision_rows") == 9, issues, "summary converted rows mismatch")
    require(summary.get("rows_removed_from_preserve_requirement") == 9, issues, "summary removed rows mismatch")
    require(summary.get("context_feature_implement_rows") == 7, issues, "summary implement rows mismatch")
    require(summary.get("avoid_inverse_redesign_rows") == 2, issues, "summary redesign rows mismatch")
    require(summary.get("remaining_preserve_requirement_rows") == 0, issues, "summary preserve remains")
    require(summary.get("reference_proxy_r_rows") == 9, issues, "summary reference rows mismatch")
    require(summary.get("reference_proxy_r_sum_not_counted") == 1.64594, issues, "summary ref sum mismatch")
    require(summary.get("proxy_r_sum_delta") == 0.0, issues, "counted proxy R changed")
    require(manifest.get("safe_flags") == SAFE_FLAGS, issues, "manifest safe flags mismatch")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "action_class_counts_after": dict(sorted(counts.items())),
        "numeric_proxy_rows_after": proxy_summary(rows)[0],
        "proxy_r_sum_after": proxy_summary(rows)[1],
        "source_provenance_context_decision_rows": summary.get("source_provenance_context_decision_rows"),
        "rows_removed_from_preserve_requirement": summary.get("rows_removed_from_preserve_requirement"),
        "context_feature_implement_rows": summary.get("context_feature_implement_rows"),
        "avoid_inverse_redesign_rows": summary.get("avoid_inverse_redesign_rows"),
        "reference_proxy_r_rows": summary.get("reference_proxy_r_rows"),
        "reference_proxy_r_sum_not_counted": summary.get("reference_proxy_r_sum_not_counted"),
        "remaining_preserve_requirement_rows": summary.get("remaining_preserve_requirement_rows"),
        "safe_flags": summary.get("safe_flags"),
    }
    write_json(OUTPUT_VERIFICATION, result)
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
