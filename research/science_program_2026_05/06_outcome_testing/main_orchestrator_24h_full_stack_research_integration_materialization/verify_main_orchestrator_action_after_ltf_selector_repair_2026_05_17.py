"""Verify LTF selector repair materialization."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_LTF_SELECTOR_REPAIR_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_LTF_SELECTOR_REPAIR_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_LTF_SELECTOR_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_OUT = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_LTF_SELECTOR_REPAIR_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
NEGATIVE_BRANCH = "REDESIGN_LTF_RESOLVED_STRUCTURAL_FVG_OB_ADVERSE_CLUSTER_AVOID_FILTER_CANDIDATE"
POSITIVE_BRANCH = "IMPLEMENT_DEFAULT_OFF_LTF_SELECTOR_REPAIRED_POSITIVE_PROXY"


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


def proxy_summary(rows: list[dict[str, Any]]) -> tuple[int, float]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return len(values), round(sum(values), 8)


def approx_equal(left: float | None, right: float | None, tolerance: float = 1e-9) -> bool:
    if left is None or right is None:
        return left is right
    return abs(left - right) <= tolerance


def main() -> None:
    rows = read_jsonl(LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)
    repaired = [
        row
        for row in rows
        if row.get("ltf_selector_repair_status") == "REPAIRED_FROM_RECOVERED_M1_LTF_SELECTOR"
    ]
    negative = [row for row in repaired if safe_float(row.get("after_proxy_r")) is not None and safe_float(row.get("after_proxy_r")) < 0]
    positive = [row for row in repaired if safe_float(row.get("after_proxy_r")) is not None and safe_float(row.get("after_proxy_r")) > 0]
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
    if len(repaired) != summary.get("repaired_rows"):
        issues.append("repaired row count mismatch")
    if len(repaired) != 39:
        issues.append(f"expected 39 repaired rows, got {len(repaired)}")
    if len(negative) != 33:
        issues.append(f"expected 33 repaired negative rows, got {len(negative)}")
    if len(positive) != 6:
        issues.append(f"expected 6 repaired positive rows, got {len(positive)}")
    if not approx_equal(sum(float(row["after_proxy_r"]) for row in repaired), -24.0):
        issues.append("repaired proxy R sum is not -24.0")
    if summary.get("numeric_proxy_rows_after") != 589:
        issues.append("numeric proxy row total after repair is not 589")
    if not approx_equal(summary.get("proxy_r_sum_after"), 111.47201587):
        issues.append("proxy R sum after repair is not 111.47201587")
    if summary.get("action_class_counts_after", {}).get("IMPLEMENT_DEFAULT_OFF") != 546:
        issues.append("IMPLEMENT_DEFAULT_OFF count after repair is not 546")
    if summary.get("action_class_counts_after", {}).get("REDESIGN") != 1417:
        issues.append("REDESIGN count after repair is not 1417")
    if summary.get("action_class_delta_vs_previous") != {"IMPLEMENT_DEFAULT_OFF": -33, "REDESIGN": 33}:
        issues.append("action class delta is not the expected -33/+33 split")

    for row in negative:
        if row.get("action_class") != "REDESIGN":
            issues.append("negative repaired row did not move to REDESIGN")
            break
        if row.get("branch_decision") != NEGATIVE_BRANCH:
            issues.append("negative repaired row has wrong branch decision")
            break
        audit = row.get("missed_opportunity_audit")
        if not isinstance(audit, dict) or not str(audit.get("kill_scope") or "").startswith("NOT_KILLED"):
            issues.append("negative repaired row missing not-killed missed-opportunity audit")
            break
        if row.get("underlying_intelligence_preserved") is not True:
            issues.append("negative repaired row did not preserve underlying intelligence")
            break
    for row in positive:
        if row.get("action_class") != "IMPLEMENT_DEFAULT_OFF":
            issues.append("positive repaired row did not remain IMPLEMENT_DEFAULT_OFF")
            break
        if row.get("branch_decision") != POSITIVE_BRANCH:
            issues.append("positive repaired row has wrong branch decision")
            break

    for row in repaired:
        source = row.get("ltf_selector_repair_source")
        if not isinstance(source, dict) or source.get("ltf_status") != "M1_PATH_RECOVERED":
            issues.append("repaired row lacks recovered M1 LTF source metadata")
            break
        if row.get("after_score_status") != "COMPUTED_FROM_LTF_PATH_ORDER":
            issues.append("repaired row was not scored from LTF path order")
            break
        if row.get("outcome_source") != "candidate_ltf_path_order":
            issues.append("repaired row outcome source is not candidate_ltf_path_order")
            break

    status_counts = Counter(row.get("ltf_selector_repair_status") for row in rows)
    if status_counts.get("NOT_REPAIRED_SOURCE_METADATA_RECOMPUTE_REQUIRED") != 83:
        issues.append("expected 83 source-metadata target rows to remain unrepaired by LTF selector")
    if status_counts.get("NOT_TARGET_ROW") != len(rows) - 39 - 83:
        issues.append("NOT_TARGET_ROW count does not match expected complement")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "numeric_proxy_rows_after": numeric_count,
        "proxy_r_sum_after": proxy_sum,
        "repaired_rows": len(repaired),
        "negative_repaired_rows": len(negative),
        "positive_repaired_rows": len(positive),
        "action_class_counts_after": dict(Counter(row.get("action_class") for row in rows)),
        "branch_counts_repaired": dict(Counter(row.get("branch_decision") for row in repaired)),
        "safe_flags": EXPECTED_SAFE_FLAGS,
    }
    VERIFY_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
