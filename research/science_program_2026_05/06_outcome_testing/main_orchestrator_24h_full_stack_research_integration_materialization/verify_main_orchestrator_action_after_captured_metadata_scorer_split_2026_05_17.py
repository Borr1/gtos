"""Verify captured-metadata scorer branch split."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_NEAR_MISS_OWNER_MERGE_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_CAPTURED_METADATA_SCORER_SPLIT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_CAPTURED_METADATA_SCORER_SPLIT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_CAPTURED_METADATA_SCORER_SPLIT_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = ROUTE_DIR / f"MAIN_ORCH24_CAPTURED_METADATA_SCORER_SPLIT_VERIFICATION_RESULT_{DATE}.json"

OLD_BRANCH = "IMPLEMENT_SHADOW_SCORER_CAPTURED_METADATA_DEFAULT_OFF"
STRUCTURAL_STRATEGY = "V2_STRUCT_COMPOSITE_ANY"
FVG_OB_STRATEGY = "FVG_OB_CONFLUENCE_OB_AFTER_FVG"
STRUCTURAL_BRANCH = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_COMPOSITE_CAPTURED_METADATA_SHARED_PATH_SCORER"
FVG_OB_BRANCH = "IMPLEMENT_DEFAULT_OFF_FVG_OB_CONFLUENCE_CAPTURED_METADATA_SHARED_PATH_SCORER"
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
    return {key: value for key, value in row.items() if key != "captured_metadata_scorer_split_status"}


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
    expected_counts = Counter({"REDESIGN": 1617, "KILL": 967, "IMPLEMENT_DEFAULT_OFF": 488, "KEEP": 354})
    require(before_counts == expected_counts, issues, f"unexpected input action counts {before_counts}")
    require(counts == expected_counts, issues, f"unexpected output action counts {counts}")
    require(proxy_summary(before_rows) == (709, 33.19811387), issues, f"input proxy mismatch {proxy_summary(before_rows)}")
    require(proxy_summary(rows) == (709, 33.19811387), issues, f"output proxy mismatch {proxy_summary(rows)}")

    converted = [
        row
        for row in rows
        if row.get("captured_metadata_scorer_split_status") in {
            "STRUCTURAL_COMPOSITE_DEFAULT_OFF_SCORER_SPLIT",
            "FVG_OB_CONFLUENCE_DEFAULT_OFF_SCORER_SPLIT",
        }
    ]
    require(len(converted) == 231, issues, f"expected 231 converted rows got {len(converted)}")
    require(
        all(before_by_id[row.get("row_id")].get("branch_decision") == OLD_BRANCH for row in converted),
        issues,
        "converted row did not originate from generic branch",
    )
    require(all(row.get("action_class") == "IMPLEMENT_DEFAULT_OFF" for row in converted), issues, "converted row action changed")
    require(all(row.get("captured_metadata_proxy_counted_as_r") is True for row in converted), issues, "counted proxy flag missing")
    require(all(row.get("safe_flags") == SAFE_FLAGS for row in converted), issues, "safe flag mismatch")
    require(all(safe_float(row.get("after_proxy_r")) is not None for row in converted), issues, "converted row lost proxy")

    branch_counts = Counter(row.get("branch_decision") for row in converted)
    require(
        branch_counts == Counter({STRUCTURAL_BRANCH: 179, FVG_OB_BRANCH: 52}),
        issues,
        f"branch split mismatch {branch_counts}",
    )
    strategy_counts = Counter(row.get("strategy_id") for row in converted)
    require(
        strategy_counts == Counter({STRUCTURAL_STRATEGY: 179, FVG_OB_STRATEGY: 52}),
        issues,
        f"strategy split mismatch {strategy_counts}",
    )
    structural_values = [safe_float(row.get("after_proxy_r")) for row in converted if row.get("strategy_id") == STRUCTURAL_STRATEGY]
    fvg_values = [safe_float(row.get("after_proxy_r")) for row in converted if row.get("strategy_id") == FVG_OB_STRATEGY]
    structural_values = [value for value in structural_values if value is not None]
    fvg_values = [value for value in fvg_values if value is not None]
    require(len(structural_values) == 179 and round(sum(structural_values), 8) == 68.0, issues, "structural proxy split mismatch")
    require(len(fvg_values) == 52 and round(sum(fvg_values), 8) == 19.0, issues, "FVG/OB proxy split mismatch")
    require(
        sum(row.get("branch_decision") == OLD_BRANCH for row in rows) == 0,
        issues,
        "generic captured metadata branch remains",
    )

    non_target_diffs = [
        row.get("row_id")
        for row in rows
        if row.get("captured_metadata_scorer_split_status") == "NOT_TARGET_ROW"
        and stripped(row) != stripped(before_by_id[row.get("row_id")])
    ]
    require(not non_target_diffs, issues, f"non-target rows changed {non_target_diffs[:5]}")

    require(summary.get("captured_metadata_rows_split") == 231, issues, "summary converted rows mismatch")
    require(summary.get("structural_composite_rows_split") == 179, issues, "summary structural rows mismatch")
    require(summary.get("fvg_ob_confluence_rows_split") == 52, issues, "summary FVG/OB rows mismatch")
    require(summary.get("numeric_proxy_rows_after") == 709, issues, "summary proxy rows changed")
    require(summary.get("proxy_r_sum_after") == 33.19811387, issues, "summary proxy sum changed")
    require(summary.get("old_generic_branch_rows_remaining") == 0, issues, "summary old generic remains")
    require(summary.get("proxy_by_strategy", {}).get(STRUCTURAL_STRATEGY, {}).get("sum") == 68.0, issues, "summary structural proxy sum mismatch")
    require(summary.get("proxy_by_strategy", {}).get(FVG_OB_STRATEGY, {}).get("sum") == 19.0, issues, "summary FVG/OB proxy sum mismatch")
    require(manifest.get("safe_flags") == SAFE_FLAGS, issues, "manifest safe flags mismatch")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "action_class_counts_after": dict(sorted(counts.items())),
        "numeric_proxy_rows_after": proxy_summary(rows)[0],
        "proxy_r_sum_after": proxy_summary(rows)[1],
        "captured_metadata_rows_split": summary.get("captured_metadata_rows_split"),
        "structural_composite_rows_split": summary.get("structural_composite_rows_split"),
        "fvg_ob_confluence_rows_split": summary.get("fvg_ob_confluence_rows_split"),
        "structural_proxy_r_sum": summary.get("proxy_by_strategy", {}).get(STRUCTURAL_STRATEGY, {}).get("sum"),
        "fvg_ob_proxy_r_sum": summary.get("proxy_by_strategy", {}).get(FVG_OB_STRATEGY, {}).get("sum"),
        "safe_flags": summary.get("safe_flags"),
    }
    write_json(OUTPUT_VERIFICATION, result)
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
