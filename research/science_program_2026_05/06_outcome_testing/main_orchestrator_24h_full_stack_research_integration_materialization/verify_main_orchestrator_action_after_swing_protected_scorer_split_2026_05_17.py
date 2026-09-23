"""Verify swing-protected scorer branch split."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_CAPTURED_METADATA_SCORER_SPLIT_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_SCORER_SPLIT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_SCORER_SPLIT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_SCORER_SPLIT_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = ROUTE_DIR / f"MAIN_ORCH24_SWING_PROTECTED_SCORER_SPLIT_VERIFICATION_RESULT_{DATE}.json"

OLD_GENERIC_BRANCH = "IMPLEMENT_SHADOW_SCORER_SWING_PROTECTED_STOP_DEFAULT_OFF"
NEW_GENERIC_BRANCH = "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_STOP_CAPTURED_METADATA_SCORER"
SOURCE_REPAIRED_BRANCH = "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_SOURCE_REPAIRED_LTF_PROXY"
OLD_SOURCE_REPAIRED_CANDIDATE = "KEEP_DEFAULT_OFF_SWING_PROTECTED_STOP_PATH_SCORER_NOW_SOURCE_REPAIRED"
NEW_SOURCE_REPAIRED_CANDIDATE = "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_STOP_PATH_SCORER_NOW_SOURCE_REPAIRED"
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
    return {key: value for key, value in row.items() if key != "swing_protected_scorer_split_status"}


def main() -> None:
    issues: list[str] = []
    before_rows = read_jsonl(INPUT_LEDGER)
    rows = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)

    require(len(rows) == 3426, issues, f"expected 3426 rows got {len(rows)}")
    require([row.get("row_id") for row in before_rows] == [row.get("row_id") for row in rows], issues, "row identity/order changed")
    before_by_id = {row.get("row_id"): row for row in before_rows}
    expected_counts = Counter({"REDESIGN": 1617, "KILL": 967, "IMPLEMENT_DEFAULT_OFF": 488, "KEEP": 354})
    before_counts = Counter(str(row.get("action_class") or "") for row in before_rows)
    counts = Counter(str(row.get("action_class") or "") for row in rows)
    require(before_counts == expected_counts, issues, f"unexpected input action counts {before_counts}")
    require(counts == expected_counts, issues, f"unexpected output action counts {counts}")
    require(proxy_summary(before_rows) == (709, 33.19811387), issues, f"input proxy mismatch {proxy_summary(before_rows)}")
    require(proxy_summary(rows) == (709, 33.19811387), issues, f"output proxy mismatch {proxy_summary(rows)}")

    generic = [row for row in rows if row.get("swing_protected_scorer_split_status") == "GENERIC_BRANCH_SPLIT_TO_SWING_PROTECTED_STOP_SCORER"]
    source = [row for row in rows if row.get("swing_protected_scorer_split_status") == "SOURCE_REPAIRED_IMPLEMENTATION_CANDIDATE_LABEL_REPAIRED"]
    require(len(generic) == 128, issues, f"expected 128 generic split rows got {len(generic)}")
    require(len(source) == 26, issues, f"expected 26 source candidate repairs got {len(source)}")
    require(
        all(before_by_id[row.get("row_id")].get("branch_decision") == OLD_GENERIC_BRANCH for row in generic),
        issues,
        "generic split row did not originate from old branch",
    )
    require(
        all(before_by_id[row.get("row_id")].get("implementation_candidate") == OLD_SOURCE_REPAIRED_CANDIDATE for row in source),
        issues,
        "source repaired row did not originate from stale candidate label",
    )
    require(all(row.get("branch_decision") == NEW_GENERIC_BRANCH for row in generic), issues, "new generic branch mismatch")
    require(all(row.get("branch_decision") == SOURCE_REPAIRED_BRANCH for row in source), issues, "source branch changed")
    require(all(row.get("implementation_candidate") == NEW_SOURCE_REPAIRED_CANDIDATE for row in source), issues, "source candidate label not repaired")
    require(all(row.get("action_class") == "IMPLEMENT_DEFAULT_OFF" for row in generic + source), issues, "action class changed")
    require(all(row.get("swing_protected_proxy_counted_as_r") is True for row in generic + source), issues, "proxy counted flag missing")
    require(all(row.get("safe_flags") == SAFE_FLAGS for row in generic + source), issues, "safe flags mismatch")

    generic_values = [safe_float(row.get("after_proxy_r")) for row in generic]
    source_values = [safe_float(row.get("after_proxy_r")) for row in source]
    generic_values = [value for value in generic_values if value is not None]
    source_values = [value for value in source_values if value is not None]
    require(len(generic_values) == 128 and round(sum(generic_values), 8) == 63.5, issues, "generic proxy split mismatch")
    require(len(source_values) == 26 and round(sum(source_values), 8) == -26.0, issues, "source-repaired proxy split mismatch")
    require(sum(row.get("branch_decision") == OLD_GENERIC_BRANCH for row in rows) == 0, issues, "old generic branch remains")
    require(
        sum(
            row.get("branch_decision") == SOURCE_REPAIRED_BRANCH
            and row.get("implementation_candidate") == OLD_SOURCE_REPAIRED_CANDIDATE
            for row in rows
        )
        == 0,
        issues,
        "old source-repaired candidate label remains",
    )

    non_target_diffs = [
        row.get("row_id")
        for row in rows
        if row.get("swing_protected_scorer_split_status") == "NOT_TARGET_ROW"
        and stripped(row) != stripped(before_by_id[row.get("row_id")])
    ]
    require(not non_target_diffs, issues, f"non-target rows changed {non_target_diffs[:5]}")

    require(summary.get("swing_protected_rows_touched") == 154, issues, "summary touched rows mismatch")
    require(summary.get("generic_branch_rows_split") == 128, issues, "summary generic rows mismatch")
    require(summary.get("source_repaired_candidate_label_rows") == 26, issues, "summary source rows mismatch")
    require(summary.get("generic_branch_proxy_sum") == 63.5, issues, "summary generic proxy sum mismatch")
    require(summary.get("source_repaired_proxy_sum") == -26.0, issues, "summary source proxy sum mismatch")
    require(summary.get("numeric_proxy_rows_after") == 709, issues, "summary proxy rows changed")
    require(summary.get("proxy_r_sum_after") == 33.19811387, issues, "summary proxy sum changed")
    require(summary.get("old_generic_branch_rows_remaining") == 0, issues, "summary old branch remains")
    require(summary.get("old_source_repaired_candidate_rows_remaining") == 0, issues, "summary old source candidate remains")
    require(manifest.get("safe_flags") == SAFE_FLAGS, issues, "manifest safe flags mismatch")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "action_class_counts_after": dict(sorted(counts.items())),
        "numeric_proxy_rows_after": proxy_summary(rows)[0],
        "proxy_r_sum_after": proxy_summary(rows)[1],
        "swing_protected_rows_touched": summary.get("swing_protected_rows_touched"),
        "generic_branch_rows_split": summary.get("generic_branch_rows_split"),
        "source_repaired_candidate_label_rows": summary.get("source_repaired_candidate_label_rows"),
        "generic_branch_proxy_sum": summary.get("generic_branch_proxy_sum"),
        "source_repaired_proxy_sum": summary.get("source_repaired_proxy_sum"),
        "safe_flags": summary.get("safe_flags"),
    }
    write_json(OUTPUT_VERIFICATION, result)
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
