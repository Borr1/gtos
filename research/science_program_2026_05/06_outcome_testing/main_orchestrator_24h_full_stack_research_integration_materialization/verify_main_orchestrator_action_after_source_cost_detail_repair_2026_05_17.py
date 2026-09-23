"""Verify SOURCE cost-detail repair consumption."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_COST_DETAIL_REPAIR_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_COST_DETAIL_REPAIR_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_COST_DETAIL_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
VERIFY_OUT = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_COST_DETAIL_REPAIR_VERIFICATION_RESULT_{DATE}.json"

EXPECTED_SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

IMPLEMENT_BRANCH = "IMPLEMENT_DEFAULT_OFF_SOURCE_ACCEPTED_SOURCE_COST_PROXY_REPAIRED"
REDESIGN_BRANCH = "REDESIGN_SOURCE_COST_REPAIR_ALL_NEGATIVE_AVOID_OR_EXACT_SOURCE_REPAIR"
PRESERVE_BRANCH = "PRESERVE_SOURCE_COST_REPAIR_STRADDLE_EXACT_SOURCE_REQUIRED"


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


def approx(left: float | None, right: float | None, tolerance: float = 1e-9) -> bool:
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
    touched = [row for row in rows if row.get("source_cost_detail_repair_status") != "NOT_TARGET_ROW"]
    values = [safe_float(row.get("after_proxy_r")) for row in touched]
    values = [value for value in values if value is not None]
    accepted = [row for row in touched if row.get("branch_decision") == IMPLEMENT_BRANCH]
    redesign = [row for row in touched if row.get("branch_decision") == REDESIGN_BRANCH]
    preserve = [row for row in touched if row.get("branch_decision") == PRESERVE_BRANCH]
    numeric_count, proxy_sum = proxy_summary(rows)
    issues: list[str] = []

    if len(rows) != summary.get("rows"):
        issues.append("summary row count does not match ledger")
    if len(rows) != 3426:
        issues.append(f"expected 3426 rows, got {len(rows)}")
    if summary.get("safe_flags") != EXPECTED_SAFE_FLAGS:
        issues.append("summary safe flags changed")
    if manifest.get("safe_flags") != EXPECTED_SAFE_FLAGS:
        issues.append("manifest safe flags changed")
    if summary.get("exact_r_rows") != 0:
        issues.append("exact R rows opened unexpectedly")
    if len(touched) != 52:
        issues.append(f"expected 52 touched source-cost rows, got {len(touched)}")
    if len(values) != 52:
        issues.append(f"expected 52 source-cost proxy rows, got {len(values)}")
    if len(accepted) != 19:
        issues.append(f"expected 19 accepted source-cost implementation rows, got {len(accepted)}")
    if len(redesign) != 26:
        issues.append(f"expected 26 all-negative redesign rows, got {len(redesign)}")
    if len(preserve) != 7:
        issues.append(f"expected 7 straddle preserve rows, got {len(preserve)}")
    if not approx(round(sum(values), 8), -0.565877):
        issues.append("source-cost proxy sum mismatch")
    if numeric_count != summary.get("numeric_proxy_rows_after") or numeric_count != 697:
        issues.append("numeric proxy row total after repair mismatch")
    if not approx(proxy_sum, summary.get("proxy_r_sum_after")) or not approx(proxy_sum, 57.40613887):
        issues.append("proxy R sum after repair mismatch")
    expected_delta = {"IMPLEMENT_DEFAULT_OFF": -33, "PRESERVE_REQUIREMENT": 7, "REDESIGN": 26}
    if summary.get("action_class_delta_vs_previous") != expected_delta:
        issues.append("action class delta mismatch")
    after_counts = summary.get("action_class_counts_after", {})
    if after_counts.get("IMPLEMENT_DEFAULT_OFF") != 431:
        issues.append("IMPLEMENT_DEFAULT_OFF count after repair mismatch")
    if after_counts.get("REDESIGN") != 1498:
        issues.append("REDESIGN count after repair mismatch")
    if after_counts.get("PRESERVE_REQUIREMENT") != 98:
        issues.append("PRESERVE_REQUIREMENT count after repair mismatch")
    if after_counts.get("KILL") != 967:
        issues.append("KILL count changed unexpectedly")

    for row in accepted:
        if row.get("action_class") != "IMPLEMENT_DEFAULT_OFF":
            issues.append("accepted source-cost row is not implementation default-off")
            break
        if row.get("source_cost_detail_proxy_source_status") != "ACCEPTED_PROXY_DETAIL_ALLOWED":
            issues.append("accepted source-cost row missing accepted scalar permission")
            break
        if safe_float(row.get("after_proxy_r")) is None or safe_float(row.get("after_proxy_r")) <= 0:
            issues.append("accepted source-cost row is not positive proxy")
            break
    for row in redesign:
        if row.get("action_class") != "REDESIGN":
            issues.append("all-negative source-cost row is not redesign")
            break
        if row.get("source_cost_interval_sign_class") != "SOURCE_COST_INTERVAL_ALL_NEGATIVE":
            issues.append("redesign row is not all-negative source-cost interval")
            break
        audit = row.get("missed_opportunity_audit")
        if not isinstance(audit, dict) or not str(audit.get("kill_scope") or "").startswith("NOT_KILLED"):
            issues.append("redesign row missing not-killed missed-opportunity audit")
            break
        if row.get("underlying_intelligence_preserved") is not True:
            issues.append("redesign row did not preserve underlying intelligence")
            break
    for row in preserve:
        if row.get("action_class") != "PRESERVE_REQUIREMENT":
            issues.append("straddle source-cost row is not preserve requirement")
            break
        if row.get("source_cost_interval_sign_class") != "SOURCE_COST_INTERVAL_STRADDLES_ZERO":
            issues.append("preserve row is not straddled source-cost interval")
            break
        audit = row.get("missed_opportunity_audit")
        if not isinstance(audit, dict) or not str(audit.get("kill_scope") or "").startswith("NOT_KILLED"):
            issues.append("preserve row missing not-killed missed-opportunity audit")
            break
    for row in touched:
        source = row.get("source_cost_detail_source")
        if not isinstance(source, dict) or not source.get("source_cost_detail_line_no"):
            issues.append("touched row missing source-cost detail provenance")
            break
        if not row.get("entry_variant") or not row.get("route_session"):
            issues.append("touched row missing entry/session provenance")
            break

    remaining_no_proxy_source_impl = [
        row
        for row in rows
        if row.get("source_capture_surface") == "source_m15_ordering_repair"
        and row.get("action_class") == "IMPLEMENT_DEFAULT_OFF"
        and row.get("after_proxy_r") is None
    ]
    if remaining_no_proxy_source_impl:
        issues.append(f"remaining source_m15 default-off rows without proxy: {len(remaining_no_proxy_source_impl)}")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(rows),
        "touched_rows": len(touched),
        "source_cost_numeric_proxy_rows": len(values),
        "source_cost_proxy_r_sum": round(sum(values), 8),
        "numeric_proxy_rows_after": numeric_count,
        "proxy_r_sum_after": proxy_sum,
        "accepted_implementation_rows": len(accepted),
        "redesign_rows": len(redesign),
        "preserve_requirement_rows": len(preserve),
        "action_class_counts_after": dict(Counter(row.get("action_class") for row in rows)),
        "source_cost_branch_counts": dict(Counter(row.get("branch_decision") for row in touched)),
        "safe_flags": EXPECTED_SAFE_FLAGS,
    }
    VERIFY_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
