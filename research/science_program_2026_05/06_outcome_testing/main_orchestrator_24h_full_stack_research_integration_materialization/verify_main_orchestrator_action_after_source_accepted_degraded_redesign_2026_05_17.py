"""Verify accepted SOURCE degraded redesign action materialization."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_DEGRADED_REDESIGN_VERIFICATION_RESULT_{DATE}.json"

TARGET_BRANCH = "PRESERVE_ACCEPTED_SOURCE_BRANCH_EXACT_TICK_REPAIR_OR_AVOID_REDESIGN"
REPAIRED_BRANCH = "REDESIGN_ACCEPTED_SOURCE_BRANCH_DEGRADED_PROXY_AVOID_OR_EXACT_REPAIR"


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
    require(before_counts.get("PRESERVE_REQUIREMENT") == 71, issues, f"unexpected input preserve count {before_counts.get('PRESERVE_REQUIREMENT')}")
    require(counts.get("PRESERVE_REQUIREMENT") == 24, issues, f"preserve requirement count should be 24, got {counts.get('PRESERVE_REQUIREMENT')}")
    require(counts.get("REDESIGN") == before_counts.get("REDESIGN", 0) + 47, issues, "redesign count did not increase by 47")
    require(counts.get("KILL") == before_counts.get("KILL"), issues, "kill count changed")
    require(counts.get("IMPLEMENT_DEFAULT_OFF") == before_counts.get("IMPLEMENT_DEFAULT_OFF"), issues, "implementation count changed")

    before_proxy = proxy_summary(before_rows)
    after_proxy = proxy_summary(rows)
    require(before_proxy == (723, 31.40613887), issues, f"unexpected input proxy state {before_proxy}")
    require(after_proxy == before_proxy, issues, f"proxy denominator changed: before={before_proxy} after={after_proxy}")

    repaired = [row for row in rows if row.get("branch_decision") == REPAIRED_BRANCH]
    require(len(repaired) == 47, issues, f"expected 47 repaired rows, got {len(repaired)}")
    require(not any(row.get("branch_decision") == TARGET_BRANCH for row in rows), issues, "old accepted SOURCE preserve branch remains")
    require(all(row.get("action_class") == "REDESIGN" for row in repaired), issues, "not all repaired rows are REDESIGN")
    require(all(row.get("after_proxy_r") is None for row in repaired), issues, "repaired rows should not count proxy R")
    require(all(row.get("source_requirement_preserved") is True for row in repaired), issues, "exact source repair path not preserved on all rows")
    require(all(row.get("underlying_intelligence_preserved") is True for row in repaired), issues, "underlying intelligence not preserved on all rows")
    require(all(row.get("missed_opportunity_audit") for row in repaired), issues, "missed-opportunity audit missing on repaired rows")
    require(
        Counter(row.get("symbol") for row in repaired) == Counter({"GBPJPY": 44, "XAUUSD": 3}),
        issues,
        f"unexpected repaired symbol split {Counter(row.get('symbol') for row in repaired)}",
    )

    missing_audit = sum(
        1
        for row in rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and not row.get("missed_opportunity_audit")
    )
    require(missing_audit == 0, issues, f"missing missed-opportunity audits after repair: {missing_audit}")
    require(summary.get("accepted_source_rows_redesigned") == 47, issues, "summary repaired count wrong")
    require(summary.get("accepted_source_rows_requiring_exact_repair_preserved") == 47, issues, "summary exact repair preservation count wrong")
    require(summary.get("remaining_preserve_requirement_rows") == 24, issues, "summary remaining preserve count wrong")
    require(summary.get("remaining_accepted_source_preserve_rows") == 0, issues, "summary remaining accepted-source preserve count wrong")
    require(summary.get("proxy_r_sum_delta") == 0.0, issues, "summary proxy delta should be zero")
    require(manifest.get("safe_flags", {}).get("NO_PROMOTION_VERDICT") is True, issues, "manifest safe flag missing")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "action_class_counts_after": dict(sorted(counts.items())),
        "numeric_proxy_rows_after": after_proxy[0],
        "proxy_r_sum_after": after_proxy[1],
        "accepted_source_rows_redesigned": summary.get("accepted_source_rows_redesigned"),
        "accepted_source_rows_requiring_exact_repair_preserved": summary.get("accepted_source_rows_requiring_exact_repair_preserved"),
        "remaining_preserve_requirement_rows": summary.get("remaining_preserve_requirement_rows"),
        "safe_flags": summary.get("safe_flags"),
    }
    write_json(OUTPUT_VERIFICATION, result)
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
