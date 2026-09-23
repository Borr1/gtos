"""Verify residual SOURCE proxy redesign action materialization."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_SOURCE_PROXY_REDESIGN_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_SOURCE_PROXY_REDESIGN_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_SOURCE_PROXY_REDESIGN_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_RESIDUAL_SOURCE_PROXY_REDESIGN_VERIFICATION_RESULT_{DATE}.json"

TARGET_BRANCHES = {
    "PRESERVE_SOURCE_COST_REPAIR_STRADDLE_EXACT_SOURCE_REQUIRED",
    "PRESERVE_SOURCE_REPAIR_INTERVAL_BOUND_EXACT_ORDERING_REQUIRED",
    "PRESERVE_SOURCE_REPAIR_UPGRADED_INTERVAL_BOUND_NO_CHALLENGER",
}
NEW_BRANCHES = {
    "REDESIGN_SOURCE_COST_STRADDLE_PROXY_AS_AVOID_CONTEXT_EXACT_SOURCE_REQUIRED",
    "REDESIGN_SOURCE_INTERVAL_BOUND_PROXY_AS_AVOID_CONTEXT_EXACT_ORDERING_REQUIRED",
    "REDESIGN_SOURCE_UPGRADED_INTERVAL_BOUND_PROXY_AS_CONTEXT_NO_CHALLENGER_EXACT_ORDERING_REQUIRED",
}


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
    require(before_counts.get("PRESERVE_REQUIREMENT") == 24, issues, f"unexpected input preserve count {before_counts.get('PRESERVE_REQUIREMENT')}")
    require(counts.get("PRESERVE_REQUIREMENT") == 10, issues, f"preserve requirement count should be 10, got {counts.get('PRESERVE_REQUIREMENT')}")
    require(counts.get("REDESIGN") == before_counts.get("REDESIGN", 0) + 14, issues, "redesign count did not increase by 14")
    require(counts.get("KILL") == before_counts.get("KILL"), issues, "kill count changed")
    require(counts.get("IMPLEMENT_DEFAULT_OFF") == before_counts.get("IMPLEMENT_DEFAULT_OFF"), issues, "implementation count changed")
    require(counts.get("KEEP") == before_counts.get("KEEP"), issues, "keep count changed")

    before_proxy = proxy_summary(before_rows)
    after_proxy = proxy_summary(rows)
    require(before_proxy == (723, 31.40613887), issues, f"unexpected input proxy state {before_proxy}")
    require(after_proxy == (709, 32.19811387), issues, f"unexpected output proxy state {after_proxy}")

    redesigned = [row for row in rows if row.get("branch_decision") in NEW_BRANCHES]
    require(len(redesigned) == 14, issues, f"expected 14 redesigned rows, got {len(redesigned)}")
    require(
        not any(row.get("action_class") == "PRESERVE_REQUIREMENT" and row.get("branch_decision") in TARGET_BRANCHES for row in rows),
        issues,
        "old numeric residual SOURCE preserve branch remains",
    )
    require(all(row.get("action_class") == "REDESIGN" for row in redesigned), issues, "not all repaired rows are REDESIGN")
    require(all(row.get("after_proxy_r") is None for row in redesigned), issues, "redesigned rows should not count proxy R")
    require(
        all(safe_float(row.get("opportunity_proxy_r_reference")) is not None for row in redesigned),
        issues,
        "opportunity proxy references missing on redesigned rows",
    )
    require(
        all(safe_float(row.get("source_proxy_r_reference")) is not None for row in redesigned),
        issues,
        "source proxy references missing on redesigned rows",
    )
    require(
        round(sum(float(row["opportunity_proxy_r_reference"]) for row in redesigned), 8) == -0.791975,
        issues,
        "redesigned proxy reference sum changed",
    )
    require(
        all(row.get("source_requirement_preserved") is True for row in redesigned),
        issues,
        "exact source repair path not preserved on all redesigned rows",
    )
    require(
        all(row.get("underlying_intelligence_preserved") is True for row in redesigned),
        issues,
        "underlying intelligence not preserved on all redesigned rows",
    )
    require(all(row.get("missed_opportunity_audit") for row in redesigned), issues, "missed-opportunity audit missing on redesigned rows")
    require(
        Counter(row.get("before_residual_source_proxy_redesign_branch_decision") for row in redesigned)
        == Counter(
            {
                "PRESERVE_SOURCE_COST_REPAIR_STRADDLE_EXACT_SOURCE_REQUIRED": 7,
                "PRESERVE_SOURCE_REPAIR_UPGRADED_INTERVAL_BOUND_NO_CHALLENGER": 4,
                "PRESERVE_SOURCE_REPAIR_INTERVAL_BOUND_EXACT_ORDERING_REQUIRED": 3,
            }
        ),
        issues,
        "unexpected original branch split",
    )
    require(
        Counter(row.get("symbol") for row in redesigned) == Counter({"GBPJPY": 10, "XAUUSD": 4}),
        issues,
        f"unexpected symbol split {Counter(row.get('symbol') for row in redesigned)}",
    )

    remaining_preserve = [row for row in rows if row.get("action_class") == "PRESERVE_REQUIREMENT"]
    require(len(remaining_preserve) == 10, issues, f"expected 10 remaining preserve rows, got {len(remaining_preserve)}")
    require(
        Counter(row.get("branch_decision") for row in remaining_preserve)
        == Counter(
            {
                "PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR": 9,
                "PRESERVE_STRUCTURAL_METADATA_LTF_SAME_M1_TICK_ORDER_REQUIRED": 1,
            }
        ),
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
    require(summary.get("residual_source_proxy_rows_redesigned") == 14, issues, "summary redesigned count wrong")
    require(summary.get("residual_source_rows_exact_repair_preserved") == 14, issues, "summary exact repair preservation count wrong")
    require(summary.get("residual_source_proxy_r_sum_referenced_not_counted") == -0.791975, issues, "summary reference proxy sum wrong")
    require(summary.get("remaining_preserve_requirement_rows") == 10, issues, "summary remaining preserve count wrong")
    require(summary.get("remaining_numeric_preserve_requirement_rows") == 0, issues, "summary remaining numeric preserve count wrong")
    require(summary.get("numeric_proxy_rows_after") == 709, issues, "summary numeric proxy rows wrong")
    require(summary.get("proxy_r_sum_after") == 32.19811387, issues, "summary proxy sum wrong")
    require(manifest.get("safe_flags", {}).get("NO_PROMOTION_VERDICT") is True, issues, "manifest safe flag missing")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "action_class_counts_after": dict(sorted(counts.items())),
        "numeric_proxy_rows_after": after_proxy[0],
        "proxy_r_sum_after": after_proxy[1],
        "residual_source_proxy_rows_redesigned": summary.get("residual_source_proxy_rows_redesigned"),
        "residual_source_proxy_reference_rows": summary.get("residual_source_proxy_reference_rows"),
        "residual_source_proxy_r_sum_referenced_not_counted": summary.get(
            "residual_source_proxy_r_sum_referenced_not_counted"
        ),
        "remaining_preserve_requirement_rows": summary.get("remaining_preserve_requirement_rows"),
        "remaining_numeric_preserve_requirement_rows": summary.get("remaining_numeric_preserve_requirement_rows"),
        "safe_flags": summary.get("safe_flags"),
    }
    write_json(OUTPUT_VERIFICATION, result)
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
