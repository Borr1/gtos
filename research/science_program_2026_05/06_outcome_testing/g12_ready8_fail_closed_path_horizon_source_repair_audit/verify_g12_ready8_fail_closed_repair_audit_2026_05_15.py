#!/usr/bin/env python3
"""Verify the G12 READY8 fail-closed source-repair audit artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-15"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def safe_flag_issues(payload: dict[str, Any], path: Path) -> list[str]:
    issues: list[str] = []
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        issues.append(f"{path.name}: promotion_verdict={payload.get('promotion_verdict')}")
    for key in ("validation_safe", "outcome_review_opened", "live_effect"):
        if payload.get(key) is not False:
            issues.append(f"{path.name}: {key}={payload.get(key)}")
    for key in (
        "opens_ai_api",
        "opens_paid_or_vendor_access",
        "opens_broker_account_order_history_deal_position_evidence",
        "opens_live_trading_behavior",
        "opens_prompt_config_risk_safety_execution_canary_selector_edit",
        "opens_raw_market_data_blob_commit",
        "opens_registry_edit",
        "opens_remote_push",
        "changes_trading_risk_safety_prompt_decision_behavior",
    ):
        if key in payload and payload.get(key) is not False:
            issues.append(f"{path.name}: {key}={payload.get(key)}")
    return issues


def count_statuses(path: Path) -> tuple[int, Counter, list[str]]:
    rows = 0
    counter: Counter = Counter()
    issues: list[str] = []
    for row in iter_jsonl(path):
        rows += 1
        if rows <= 100:
            issues.extend(safe_flag_issues(row, path))
        counter[row.get("audit_status")] += 1
        if row.get("audit_status") != "PASS":
            issues.append(f"{path.name}: non-PASS row {rows}")
    return rows, counter, issues


def verify(*, require_completion_tests: bool = True) -> dict[str, Any]:
    paths = {
        "recompute": ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json",
        "inventory": ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_INVENTORY_RECOMPUTATION_LEDGER_{DATE}.jsonl",
        "source_hash": ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SOURCE_RECORD_HASH_RECOMPUTATION_LEDGER_{DATE}.jsonl",
        "target": ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_REPAIRED_TARGET_RECOMPUTATION_LEDGER_{DATE}.jsonl",
        "discrepancy": ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_DISCREPANCY_LEDGER_{DATE}.json",
        "repair": ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SAME_G12_REPAIR_LEDGER_{DATE}.json",
        "safe": ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SAFE_SURFACE_LEDGER_{DATE}.json",
        "saturation": ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        "r7": ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_R7_CONSUMPTION_RULE_{DATE}.json",
        "decision": ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_DECISION_LEDGER_{DATE}.json",
        "completion": ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_COMPLETION_AUDIT_{DATE}.json",
        "manifest": ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_OUTPUT_MANIFEST_{DATE}.json",
        "summary": ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_SUMMARY_{DATE}.md",
    }
    issues: list[str] = []
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        issues.append(f"missing artifacts: {missing}")

    loaded = {name: load_json(path) for name, path in paths.items() if path.exists() and path.suffix == ".json"}
    for name, payload in loaded.items():
        issues.extend(safe_flag_issues(payload, paths[name]))

    inventory_rows, inventory_counter, inv_issues = count_statuses(paths["inventory"])
    source_rows, source_counter, source_issues = count_statuses(paths["source_hash"])
    target_rows, target_counter, target_issues = count_statuses(paths["target"])
    issues.extend(inv_issues + source_issues + target_issues)

    recompute = loaded.get("recompute", {})
    decision = loaded.get("decision", {})
    discrepancy = loaded.get("discrepancy", {})
    completion = loaded.get("completion", {})
    r7 = loaded.get("r7", {})
    checks = {
        "inventory_rows_exact": inventory_rows == 35_811,
        "source_repaired_bar_rows_exact": source_rows == 220,
        "target_repaired_rows_exact": target_rows == 5_320,
        "all_inventory_rows_pass": inventory_counter.get("PASS") == 35_811,
        "all_source_rows_pass": source_counter.get("PASS") == 220,
        "all_target_rows_pass": target_counter.get("PASS") == 5_320,
        "critical_issue_count_zero": discrepancy.get("critical_issue_count") == 0,
        "decision_accepts": decision.get("accepted") is True
        and decision.get("terminal_decision")
        == "ACCEPT_AS_G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_NO_PROMOTION",
        "r7_may_consume_5320": r7.get("r7_may_consume_repaired_rows") is True
        and r7.get("accepted_repaired_target_rows") == 5_320,
        "remaining_fail_closed_exact": r7.get("remaining_fail_closed_target_rows") == 25_240,
        "role_excluded_unchanged": r7.get("role_excluded_rows_unchanged") == 5_251,
        "sensitivity_checks_all_true": all(recompute.get("sensitivity_checks", {}).values()),
        "searched_root_checks_all_true": all(recompute.get("searched_root_checks", {}).values()),
        "completion_complete_after_tests": (
            completion.get("can_mark_goal_complete_after_verifier_tests_commit") is True
            if require_completion_tests
            else True
        ),
    }
    for name, ok in checks.items():
        if not ok:
            issues.append(f"check failed: {name}")

    result = {
        "ok": not issues,
        "issues": issues,
        "checks": checks,
        "counts": {
            "inventory_rows": inventory_rows,
            "source_repaired_bar_rows": source_rows,
            "target_repaired_rows": target_rows,
            "inventory_counter": dict(inventory_counter),
            "source_counter": dict(source_counter),
            "target_counter": dict(target_counter),
        },
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    out = ROUTE_DIR / f"G12_READY8_FAIL_CLOSED_REPAIR_AUDIT_VERIFICATION_RESULT_{DATE}.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    result = verify(require_completion_tests=True)
    print(json.dumps({"ok": result["ok"], "issues": result["issues"]}, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
