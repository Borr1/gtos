"""Verify structural metadata plus LTF repair materialization."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_LTF_REPAIR_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_LTF_REPAIR_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_LTF_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_OUT = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_LTF_REPAIR_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
NEGATIVE_BRANCH = "REDESIGN_STRUCTURAL_METADATA_LTF_RESOLVED_ADVERSE_CLUSTER_AVOID_FILTER_CANDIDATE"
POSITIVE_BRANCH = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_LTF_REPAIRED_POSITIVE_PROXY"
SWING_SOURCE_BRANCH = "PRESERVE_SWING_PROTECTED_SOURCE_REQUIREMENT_AFTER_STRUCTURAL_METADATA_REPAIR"
TICK_ORDER_BRANCH = "PRESERVE_STRUCTURAL_METADATA_LTF_SAME_M1_TICK_ORDER_REQUIRED"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def approx_equal(left: float | None, right: float | None, tolerance: float = 1e-9) -> bool:
    if left is None or right is None:
        return left is right
    return abs(left - right) <= tolerance


def proxy_summary(rows: list[dict[str, Any]]) -> tuple[int, float]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return len(values), round(sum(values), 8)


def main() -> None:
    rows = read_jsonl(LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)
    touched = [
        row for row in rows if row.get("structural_ltf_repair_status") != "NOT_TARGET_ROW"
    ]
    numeric = [row for row in touched if safe_float(row.get("after_proxy_r")) is not None]
    negative = [row for row in numeric if safe_float(row.get("after_proxy_r")) < 0]
    positive = [row for row in numeric if safe_float(row.get("after_proxy_r")) > 0]
    preserve = [row for row in touched if row.get("action_class") == "PRESERVE_REQUIREMENT"]
    numeric_count, proxy_sum = proxy_summary(rows)
    issues: list[str] = []

    if len(rows) != summary.get("rows"):
        issues.append("summary row count does not match ledger")
    if summary.get("safe_flags") != EXPECTED_SAFE_FLAGS:
        issues.append("summary safe flags changed")
    if manifest.get("safe_flags") != EXPECTED_SAFE_FLAGS:
        issues.append("manifest safe flags changed")
    if summary.get("exact_r_rows") != 0:
        issues.append("exact R rows opened unexpectedly")
    if numeric_count != summary.get("numeric_proxy_rows_after"):
        issues.append("numeric proxy row count mismatch")
    if not approx_equal(proxy_sum, summary.get("proxy_r_sum_after")):
        issues.append("proxy R sum mismatch")
    if len(touched) != 83:
        issues.append(f"expected 83 touched rows, got {len(touched)}")
    if len(numeric) != 56:
        issues.append(f"expected 56 newly numeric rows, got {len(numeric)}")
    if len(negative) != 55:
        issues.append(f"expected 55 adverse rows, got {len(negative)}")
    if len(positive) != 1:
        issues.append(f"expected 1 positive row, got {len(positive)}")
    if len(preserve) != 27:
        issues.append(f"expected 27 source requirements, got {len(preserve)}")
    if not approx_equal(sum(float(row["after_proxy_r"]) for row in numeric), -53.5):
        issues.append("repaired proxy R sum is not -53.5")
    if summary.get("numeric_proxy_rows_after") != 645:
        issues.append("numeric proxy row total after repair is not 645")
    if not approx_equal(summary.get("proxy_r_sum_after"), 57.97201587):
        issues.append("proxy R sum after repair is not 57.97201587")
    if summary.get("action_class_counts_after", {}).get("IMPLEMENT_DEFAULT_OFF") != 464:
        issues.append("IMPLEMENT_DEFAULT_OFF count after repair is not 464")
    if summary.get("action_class_counts_after", {}).get("REDESIGN") != 1472:
        issues.append("REDESIGN count after repair is not 1472")
    if summary.get("action_class_counts_after", {}).get("PRESERVE_REQUIREMENT") != 91:
        issues.append("PRESERVE_REQUIREMENT count after repair is not 91")
    expected_delta = {"IMPLEMENT_DEFAULT_OFF": -82, "PRESERVE_REQUIREMENT": 27, "REDESIGN": 55}
    if summary.get("action_class_delta_vs_previous") != expected_delta:
        issues.append("action class delta is not the expected -82/+27/+55 split")

    for row in negative:
        if row.get("action_class") != "REDESIGN" or row.get("branch_decision") != NEGATIVE_BRANCH:
            issues.append("negative repaired row has wrong redesign decision")
            break
        audit = row.get("missed_opportunity_audit")
        if not isinstance(audit, dict) or not str(audit.get("kill_scope") or "").startswith("NOT_KILLED"):
            issues.append("negative repaired row missing not-killed missed-opportunity audit")
            break
        if row.get("underlying_intelligence_preserved") is not True:
            issues.append("negative repaired row did not preserve underlying intelligence")
            break
    for row in positive:
        if row.get("action_class") != "IMPLEMENT_DEFAULT_OFF" or row.get("branch_decision") != POSITIVE_BRANCH:
            issues.append("positive repaired row has wrong implementation decision")
            break
    preserve_branches = Counter(row.get("branch_decision") for row in preserve)
    if preserve_branches.get(SWING_SOURCE_BRANCH) != 26:
        issues.append("expected 26 swing source requirement rows")
    if preserve_branches.get(TICK_ORDER_BRANCH) != 1:
        issues.append("expected 1 same-M1 tick-order requirement row")
    for row in touched:
        source = row.get("structural_ltf_repair_source")
        if not isinstance(source, dict):
            issues.append("touched row missing structural/LTF source metadata")
            break

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "numeric_proxy_rows_after": numeric_count,
        "proxy_r_sum_after": proxy_sum,
        "touched_rows": len(touched),
        "numeric_repaired_rows": len(numeric),
        "negative_repaired_rows": len(negative),
        "positive_repaired_rows": len(positive),
        "preserve_requirement_rows": len(preserve),
        "action_class_counts_after": dict(Counter(row.get("action_class") for row in rows)),
        "branch_counts_touched": dict(Counter(row.get("branch_decision") for row in touched)),
        "safe_flags": EXPECTED_SAFE_FLAGS,
    }
    VERIFY_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
