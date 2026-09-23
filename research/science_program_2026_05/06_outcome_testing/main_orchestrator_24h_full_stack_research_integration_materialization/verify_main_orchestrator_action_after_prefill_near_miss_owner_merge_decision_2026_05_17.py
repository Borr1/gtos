"""Verify near-miss prefill owner-merge decision materialization."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_SOURCE_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_NEAR_MISS_OWNER_MERGE_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_NEAR_MISS_OWNER_MERGE_DECISION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_NEAR_MISS_OWNER_MERGE_DECISION_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_NEAR_MISS_OWNER_MERGE_VERIFICATION_RESULT_{DATE}.json"

TARGET_BRANCH = "MERGE_PREFILL_NEAR_MISS_INTO_ENTRY_OFFSET_050R_IMPLEMENTATION"
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
    return {key: value for key, value in row.items() if key != "prefill_near_miss_owner_merge_decision_status"}


def preservation_ok(row: dict[str, Any]) -> bool:
    required = (
        "opportunity_owner_row_id",
        "opportunity_owner_source_artifact",
        "opportunity_proxy_r_reference",
        "opportunity_proxy_reference_status",
        "opportunity_not_independently_countable_reason",
        "opportunity_useful_mechanism",
        "opportunity_downstream_paths",
    )
    return (
        all(row.get(key) not in (None, "", []) for key in required)
        and row.get("prefill_proxy_reference_counted_as_r") is False
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
        before_counts == Counter({"REDESIGN": 1614, "KILL": 967, "IMPLEMENT_DEFAULT_OFF": 488, "KEEP": 357}),
        issues,
        f"unexpected input action counts {before_counts}",
    )
    require(
        counts == Counter({"REDESIGN": 1617, "KILL": 967, "IMPLEMENT_DEFAULT_OFF": 488, "KEEP": 354}),
        issues,
        f"unexpected output action counts {counts}",
    )
    require(proxy_summary(before_rows) == (709, 33.19811387), issues, f"input proxy mismatch {proxy_summary(before_rows)}")
    require(proxy_summary(rows) == (709, 33.19811387), issues, f"output proxy mismatch {proxy_summary(rows)}")

    converted = [
        row
        for row in rows
        if row.get("prefill_near_miss_owner_merge_decision_status") == "MOVED_FROM_KEEP_TO_OWNER_MERGE_REDESIGN"
    ]
    require(len(converted) == 3, issues, f"expected 3 converted rows got {len(converted)}")
    require(
        all(before_by_id[row.get("row_id")].get("action_class") == "KEEP" for row in converted),
        issues,
        "converted row did not originate as keep",
    )
    require(all(row.get("action_class") == "REDESIGN" for row in converted), issues, "converted row not redesign")
    require(all(row.get("branch_decision") == TARGET_BRANCH for row in converted), issues, "converted branch mismatch")
    require(all(safe_float(row.get("after_proxy_r")) is None for row in converted), issues, "converted row counted proxy R")
    require(all(row.get("prefill_proxy_reference_owner") == "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER" for row in converted), issues, "owner mismatch")
    require(all(preservation_ok(row) for row in converted), issues, "converted row missing opportunity preservation")
    refs = [safe_float(row.get("opportunity_proxy_r_reference")) for row in converted]
    refs = [value for value in refs if value is not None]
    require(len(refs) == 3, issues, "proxy references missing")
    require(round(sum(refs), 8) == 1.99702603, issues, f"proxy reference sum mismatch {round(sum(refs), 8)}")
    require(all(row.get("safe_flags") == SAFE_FLAGS for row in converted), issues, "converted safe flags mismatch")

    non_target_diffs = [
        row.get("row_id")
        for row in rows
        if row.get("prefill_near_miss_owner_merge_decision_status") == "NOT_TARGET_ROW"
        and stripped(row) != stripped(before_by_id[row.get("row_id")])
    ]
    require(not non_target_diffs, issues, f"non-target rows changed {non_target_diffs[:5]}")
    require(
        sum(row.get("action_class") == "KEEP" and row.get("branch_decision") == TARGET_BRANCH for row in rows) == 0,
        issues,
        "near-miss owner merge keep rows remain",
    )

    require(summary.get("prefill_near_miss_owner_merged_rows") == 3, issues, "summary converted rows mismatch")
    require(summary.get("rows_removed_from_keep") == 3, issues, "summary keep removal mismatch")
    require(summary.get("rows_added_to_redesign") == 3, issues, "summary redesign rows mismatch")
    require(summary.get("proxy_r_reference_rows") == 3, issues, "summary proxy reference rows mismatch")
    require(summary.get("proxy_r_reference_sum_not_counted") == 1.99702603, issues, "summary proxy reference sum mismatch")
    require(summary.get("numeric_proxy_rows_after") == 709, issues, "summary proxy rows changed")
    require(summary.get("proxy_r_sum_after") == 33.19811387, issues, "summary proxy sum changed")
    require(summary.get("counted_proxy_r_rows_added") == 0, issues, "summary counted proxy rows added")
    require(summary.get("counted_proxy_r_sum_added") == 0.0, issues, "summary counted proxy sum added")
    require(summary.get("remaining_prefill_near_miss_keep_rows") == 0, issues, "summary keep rows remain")
    require(summary.get("owner_merge_rows_missing_audit") == 0, issues, "summary audit gaps")
    require(summary.get("owner_merge_rows_missing_underlying_intel") == 0, issues, "summary intel gaps")
    require(manifest.get("safe_flags") == SAFE_FLAGS, issues, "manifest safe flags mismatch")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "action_class_counts_after": dict(sorted(counts.items())),
        "numeric_proxy_rows_after": proxy_summary(rows)[0],
        "proxy_r_sum_after": proxy_summary(rows)[1],
        "prefill_near_miss_owner_merged_rows": summary.get("prefill_near_miss_owner_merged_rows"),
        "rows_removed_from_keep": summary.get("rows_removed_from_keep"),
        "rows_added_to_redesign": summary.get("rows_added_to_redesign"),
        "proxy_r_reference_rows": summary.get("proxy_r_reference_rows"),
        "proxy_r_reference_sum_not_counted": summary.get("proxy_r_reference_sum_not_counted"),
        "safe_flags": summary.get("safe_flags"),
    }
    write_json(OUTPUT_VERIFICATION, result)
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
