#!/usr/bin/env python3
"""Verify READY8 fail-closed path/horizon source-repair artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-15"
ROUTE_ID = "READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR"
EVIDENCE_CLASS = "READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def safe_flag_issues(payload: dict[str, Any], path: Path) -> list[str]:
    issues: list[str] = []
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        issues.append(f"{rel(path)} promotion_verdict={payload.get('promotion_verdict')}")
    for key in ("validation_safe", "outcome_review_opened", "live_effect"):
        if payload.get(key) is not False:
            issues.append(f"{rel(path)} {key}={payload.get(key)}")
    for key in (
        "opens_ai_api",
        "opens_paid_or_vendor_access",
        "opens_broker_account_order_history_deal_position_evidence",
        "opens_live_trading_behavior",
        "opens_prompt_config_risk_safety_execution_canary_selector",
        "opens_raw_market_data_blob_commit",
        "opens_registry_edit",
        "opens_remote_push",
        "changes_trading_risk_safety_prompt_decision_behavior",
    ):
        if key in payload and payload.get(key) is not False:
            issues.append(f"{rel(path)} {key}={payload.get(key)}")
    return issues


def count_jsonl(path: Path) -> tuple[int, Counter, list[str]]:
    count = 0
    counter: Counter = Counter()
    issues: list[str] = []
    for row in iter_jsonl(path):
        count += 1
        if count <= 100:
            issues.extend(safe_flag_issues(row, path))
        if path.name.startswith("READY8_FAIL_CLOSED_ROW_INVENTORY"):
            counter[row.get("inventory_type")] += 1
            counter[row.get("repair_status")] += 1
        elif path.name.startswith("READY8_FAIL_CLOSED_REPAIRED_TARGET"):
            counter[row.get("repair_status")] += 1
            counter[row.get("card_id")] += 1
        elif path.name.startswith("READY8_FAIL_CLOSED_REPAIRED_BAR"):
            counter[row.get("symbol")] += 1
    return count, counter, issues


def verify() -> dict[str, Any]:
    paths = {
        "binding": ROUTE_DIR / f"READY8_FAIL_CLOSED_ACCEPTED_BINDING_LEDGER_{DATE}.json",
        "inventory": ROUTE_DIR / f"READY8_FAIL_CLOSED_ROW_INVENTORY_{DATE}.jsonl",
        "distribution": ROUTE_DIR / f"READY8_FAIL_CLOSED_DISTRIBUTION_LEDGER_{DATE}.json",
        "search": ROUTE_DIR / f"READY8_FAIL_CLOSED_SEARCHED_ROOT_ACQUISITION_LEDGER_{DATE}.json",
        "recovered": ROUTE_DIR / f"READY8_FAIL_CLOSED_RECOVERED_SOURCE_HASH_LEDGER_{DATE}.json",
        "bars": ROUTE_DIR / f"READY8_FAIL_CLOSED_REPAIRED_BAR_PACKET_{DATE}.jsonl",
        "targets": ROUTE_DIR / f"READY8_FAIL_CLOSED_REPAIRED_TARGET_ROW_PACKET_{DATE}.jsonl",
        "unrecoverable": ROUTE_DIR / f"READY8_FAIL_CLOSED_UNRECOVERABLE_PROOF_LEDGER_{DATE}.json",
        "sensitivity": ROUTE_DIR / f"READY8_FAIL_CLOSED_SENSITIVITY_LEDGER_{DATE}.json",
        "no_leak": ROUTE_DIR / f"READY8_FAIL_CLOSED_NO_LEAK_ASOF_DUPLICATE_POLICY_LEDGER_{DATE}.json",
        "saturation": ROUTE_DIR / f"READY8_FAIL_CLOSED_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
        "completion": ROUTE_DIR / f"READY8_FAIL_CLOSED_COMPLETION_AUDIT_{DATE}.json",
        "manifest": ROUTE_DIR / f"READY8_FAIL_CLOSED_OUTPUT_MANIFEST_{DATE}.json",
        "synthesis": ROUTE_DIR / f"READY8_FAIL_CLOSED_SYNTHESIS_{DATE}.md",
        "next_g12_prompt": ROOT
        / "research"
        / "science_program_2026_05"
        / "04_goal_prompts"
        / f"G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_GOAL_PROMPT_{DATE}.md",
    }
    issues: list[str] = []
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        issues.append(f"missing artifacts: {missing}")

    loaded: dict[str, dict[str, Any]] = {}
    for name, path in paths.items():
        if path.exists() and path.suffix == ".json":
            loaded[name] = load_json(path)
            issues.extend(safe_flag_issues(loaded[name], path))

    inventory_count, inventory_counter, inv_issues = count_jsonl(paths["inventory"])
    bar_count, bar_counter, bar_issues = count_jsonl(paths["bars"])
    target_count, target_counter, target_issues = count_jsonl(paths["targets"])
    issues.extend(inv_issues + bar_issues + target_issues)

    checks = {
        "inventory_count_exact": inventory_count == 35_811,
        "target_fail_rows_exact": inventory_counter["TARGET_FAIL_CLOSED_NOT_COMPUTABLE"] == 30_560,
        "role_excluded_rows_exact": inventory_counter["ROLE_FAIL_CLOSED_COMPUTABLE_EXCLUDED"] == 5_251,
        "repair_candidate_inventory_rows_exact": inventory_counter[
            "REPAIR_CANDIDATE_COMPUTABLE_REQUIRES_G12_ACCEPTANCE"
        ]
        == 5_320,
        "still_fail_closed_inventory_rows_exact": inventory_counter[
            "STILL_FAIL_CLOSED_AFTER_CURRENT_LOCAL_SOURCE_SEARCH"
        ]
        == 25_240,
        "recovered_bar_rows_exact": bar_count == 220,
        "repaired_target_rows_exact": target_count == 5_320,
        "repaired_target_rows_all_repair_candidates": target_counter[
            "REPAIR_CANDIDATE_COMPUTABLE_REQUIRES_G12_ACCEPTANCE"
        ]
        == 5_320,
        "sensitivity_arithmetic_ok": loaded.get("sensitivity", {}).get(
            "counterfactual_fail_closed_not_computable_rows_if_g12_accepts_recovered_sources"
        )
        == 25_240
        and loaded.get("sensitivity", {}).get("counterfactual_computable_rows_if_g12_accepts_recovered_sources")
        == 167_656,
        "unique_missing_bar_arithmetic_ok": loaded.get("recovered", {}).get("unique_missing_bars")
        == loaded.get("recovered", {}).get("recovered_unique_bars")
        + loaded.get("recovered", {}).get("still_missing_unique_bars"),
        "remaining_unique_missing_bars_exact": loaded.get("unrecoverable", {}).get(
            "remaining_unique_missing_bar_windows"
        )
        == 536,
        "safe_flags_ok": not issues,
        "next_g12_prompt_exists": paths["next_g12_prompt"].exists(),
        "no_top_n_claimed": loaded.get("saturation", {}).get("no_arbitrary_top_n") is True,
        "completion_claims_can_mark_after_commit": loaded.get("completion", {}).get(
            "can_mark_goal_complete_after_verifier_and_scoped_commit"
        )
        is True,
    }
    for name, ok in checks.items():
        if not ok:
            issues.append(f"check failed: {name}")

    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "checks": checks,
        "counts": {
            "inventory_rows": inventory_count,
            "repaired_bar_rows": bar_count,
            "repaired_target_rows": target_count,
            "inventory_counter": dict(inventory_counter),
            "repaired_bar_counter": dict(bar_counter),
            "repaired_target_counter": dict(target_counter),
        },
        "issues": issues,
        "ok": not issues,
    }
    return result


def main() -> None:
    result = verify()
    out = ROUTE_DIR / f"READY8_FAIL_CLOSED_VERIFICATION_RESULT_{DATE}.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "issues": result["issues"]}, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
