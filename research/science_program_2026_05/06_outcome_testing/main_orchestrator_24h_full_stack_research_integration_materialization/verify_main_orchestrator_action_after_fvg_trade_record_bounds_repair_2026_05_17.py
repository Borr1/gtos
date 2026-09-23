"""Verify the FVG trade-record bounds repair action ledger."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_REQUIREMENT_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_TRADE_RECORD_BOUNDS_REPAIR_VERIFICATION_RESULT_{DATE}.json"

TARGET_ROW_ID = "MAIN-ORCH24-ACTION-SRCM15-00021"
TARGET_BRANCH = "PRESERVE_FVG_OB_BUCKET_BOTH_FIRE_EXACT_BOUNDS_REQUIRED"
REPAIRED_BRANCH = "REDESIGN_FVG_OB_BUCKET_REPAIRED_AS_FVG_ONLY_NO_OB_CONFLUENCE"
TARGET_CANDIDATE_ID = "GBPJPY_2026-05-04T03:00:00+00:00"
RELATED_STANDALONE_STRATEGIES = {"V2_STRUCT_FVG_MID_EDGE", "V3_FVG_ONLY_RESCUE_RISK_BANK"}


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
    require(len(before_rows) == len(rows), issues, "row count changed vs input ledger")
    require([row.get("row_id") for row in before_rows] == [row.get("row_id") for row in rows], issues, "row identity/order changed")

    before_counts = Counter(row.get("action_class") for row in before_rows)
    counts = Counter(row.get("action_class") for row in rows)
    require(counts.get("PRESERVE_REQUIREMENT") == before_counts.get("PRESERVE_REQUIREMENT", 0) - 1, issues, "preserve requirement count did not drop by 1")
    require(counts.get("REDESIGN") == before_counts.get("REDESIGN", 0) + 1, issues, "redesign count did not increase by 1")
    require(counts.get("KILL") == before_counts.get("KILL"), issues, "kill count changed")

    before_proxy = proxy_summary(before_rows)
    after_proxy = proxy_summary(rows)
    require(after_proxy == before_proxy, issues, f"proxy denominator changed: before={before_proxy} after={after_proxy}")
    require(before_proxy == (723, 31.40613887), issues, f"unexpected input proxy state {before_proxy}")

    target_rows = [row for row in rows if row.get("row_id") == TARGET_ROW_ID]
    require(len(target_rows) == 1, issues, "target row missing or duplicated")
    target = target_rows[0] if target_rows else {}
    require(target.get("branch_decision") == REPAIRED_BRANCH, issues, "target branch decision not repaired")
    require(target.get("action_class") == "REDESIGN", issues, "target action class not REDESIGN")
    require(target.get("after_proxy_r") is None, issues, "target after_proxy_r should remain uncounted")
    require(safe_float(target.get("opportunity_proxy_r_reference")) == -1.0, issues, "target proxy reference should be -1.0")
    require(target.get("opportunity_proxy_reference_status") == "REFERENCE_ONLY_SHARED_PATH_PROXY_NOT_FVG_OB_IMPLEMENTATION", issues, "target proxy reference status wrong")
    require(target.get("underlying_intelligence_preserved") is True, issues, "target did not preserve underlying intelligence")

    repair = target.get("fvg_trade_record_bounds_repair_source") or {}
    bounds = repair.get("fvg_bounds") or {}
    require(repair.get("entry_in_fvg_check_status") == "PASS", issues, "entry_in_fvg source check not PASS")
    require(bounds.get("source_status") == "MATCHED_M15_FVG_FROM_TRADE_RECORD_L2_ENTRY_IN_FVG", issues, "FVG bounds source status wrong")
    require(safe_float(bounds.get("bottom")) == 213.286, issues, "FVG bottom mismatch")
    require(safe_float(bounds.get("top")) == 213.313, issues, "FVG top mismatch")
    require(safe_float(bounds.get("midpoint")) == 213.2995, issues, "FVG midpoint mismatch")
    require(repair.get("ob_leg_status") == "NO_OB_BOUNDS_IN_TRADE_RECORD_L2_OB_CHECKS_SKIPPED_FVG_FILL_PATH", issues, "OB leg status wrong")
    require(bool(target.get("missed_opportunity_audit")), issues, "target missing missed-opportunity audit")

    require(not any(row.get("branch_decision") == TARGET_BRANCH for row in rows), issues, "old FVG/OB source requirement branch remains")
    related = [
        row
        for row in rows
        if row.get("candidate_id") == TARGET_CANDIDATE_ID
        and row.get("strategy_id") in RELATED_STANDALONE_STRATEGIES
    ]
    require(len(related) == 2, issues, f"expected 2 related standalone rows, got {len(related)}")
    require(
        all(row.get("standalone_fvg_trade_record_bounds_repair_status") for row in related),
        issues,
        "related standalone rows were not enriched with FVG bounds repair status",
    )
    require(
        all(row.get("action_class") == "REDESIGN" for row in related),
        issues,
        "related standalone rows should remain redesign rows",
    )

    missing_audit = sum(
        1
        for row in rows
        if row.get("action_class") in {"KILL", "REDESIGN", "PRESERVE_REQUIREMENT"}
        and not row.get("missed_opportunity_audit")
    )
    require(missing_audit == 0, issues, f"missing missed-opportunity audits after repair: {missing_audit}")
    require(summary.get("target_fvg_ob_requirement_rows_repaired") == 1, issues, "summary target repair count wrong")
    require(summary.get("related_standalone_fvg_rows_enriched") == 2, issues, "summary related enrichment count wrong")
    require(summary.get("remaining_fvg_ob_exact_bounds_requirement_rows") == 0, issues, "summary remaining FVG/OB requirement count wrong")
    require(summary.get("rows_requiring_source_cost_fill_repair_after") == 71, issues, "summary source requirement count wrong")
    require(summary.get("proxy_r_rows_referenced_not_counted") == 1, issues, "summary referenced proxy row count wrong")
    require(summary.get("proxy_r_sum_referenced_not_counted") == -1.0, issues, "summary referenced proxy sum wrong")
    require(manifest.get("safe_flags", {}).get("NO_PROMOTION_VERDICT") is True, issues, "manifest safe flag missing")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "action_class_counts_after": dict(sorted(counts.items())),
        "numeric_proxy_rows_after": after_proxy[0],
        "proxy_r_sum_after": after_proxy[1],
        "target_fvg_ob_requirement_rows_repaired": summary.get("target_fvg_ob_requirement_rows_repaired"),
        "related_standalone_fvg_rows_enriched": summary.get("related_standalone_fvg_rows_enriched"),
        "proxy_r_rows_referenced_not_counted": summary.get("proxy_r_rows_referenced_not_counted"),
        "proxy_r_sum_referenced_not_counted": summary.get("proxy_r_sum_referenced_not_counted"),
        "rows_requiring_source_cost_fill_repair_after": summary.get("rows_requiring_source_cost_fill_repair_after"),
        "safe_flags": summary.get("safe_flags"),
    }
    write_json(OUTPUT_VERIFICATION, result)
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
