from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
INPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_LEDGER_2026-05-17.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_PATH_PROXY_REPAIR_LEDGER_2026-05-17.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_PATH_PROXY_REPAIR_SUMMARY_2026-05-17.json"
VERIFY_RESULT = ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_PATH_PROXY_REPAIR_VERIFY_RESULT_2026-05-17.json"

REPAIR_BRANCH = "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_FILLED_PATH_PROXY_REPAIRED"
OLD_BRANCH = "REDESIGN_PENDING_LIFECYCLE_R_OUTCOME_SOURCE_REQUIRED"
EXPECTED_PROXY = {
    "GBPJPY_2026-05-11T07:30:00+00:00": 1.5,
    "XAGUSD_2026-05-14T13:15:00+00:00": -1.0,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def proxy_summary(rows: list[dict[str, Any]]) -> tuple[int, float]:
    count = 0
    total = 0.0
    for row in rows:
        value = row.get("after_proxy_r")
        if value is None:
            value = row.get("strategy_proxy_r")
        if value is None or isinstance(value, bool):
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        count += 1
        total += number
    return count, round(total, 8)


def main() -> None:
    issues: list[str] = []
    before = read_jsonl(INPUT_LEDGER)
    after = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)

    if len(before) != 3426 or len(after) != 3426:
        issues.append(f"row_count_mismatch before={len(before)} after={len(after)}")
    before_ids = [row.get("row_id") for row in before]
    after_ids = [row.get("row_id") for row in after]
    if before_ids != after_ids:
        issues.append("row_identity_or_order_changed")

    repaired = [
        row
        for row in after
        if row.get("strategy_id") == "PENDING_LIMIT_LIFECYCLE"
        and row.get("branch_decision") == REPAIR_BRANCH
    ]
    if len(repaired) != 2:
        issues.append(f"expected_2_repaired_rows_found_{len(repaired)}")

    for row in repaired:
        candidate_id = str(row.get("candidate_id") or "")
        expected = EXPECTED_PROXY.get(candidate_id)
        if expected is None:
            issues.append(f"unexpected_repaired_candidate_{candidate_id}")
            continue
        if row.get("action_class") != "IMPLEMENT_DEFAULT_OFF":
            issues.append(f"{candidate_id}_not_implement_default_off")
        if row.get("score_status") != "COMPUTED_FROM_PENDING_LIFECYCLE_PATH_PROXY_REPAIR":
            issues.append(f"{candidate_id}_wrong_score_status")
        if row.get("outcome_status") != "BROKER_FILLED_SYNTHETIC_PATH_R_REPAIRED":
            issues.append(f"{candidate_id}_wrong_outcome_status")
        try:
            proxy = float(row.get("strategy_proxy_r"))
        except (TypeError, ValueError):
            proxy = None
        if proxy != expected:
            issues.append(f"{candidate_id}_proxy_expected_{expected}_got_{proxy}")
        if row.get("pending_lifecycle_broker_actual_r_status") != "BROKER_ACTUAL_R_NOT_CAPTURED_PATH_PROXY_ONLY":
            issues.append(f"{candidate_id}_broker_actual_r_status_not_preserved")
        if row.get("pending_lifecycle_r_repair_status") != "FILLED_R_REPAIRED_FROM_CANDIDATE_PATH_PROXY":
            issues.append(f"{candidate_id}_repair_status_missing")

    remaining_old = [
        row
        for row in after
        if row.get("strategy_id") == "PENDING_LIMIT_LIFECYCLE"
        and row.get("branch_decision") == OLD_BRANCH
    ]
    if remaining_old:
        issues.append(f"old_pending_r_source_required_rows_remain_{len(remaining_old)}")

    before_proxy_rows, before_proxy_sum = proxy_summary(before)
    after_proxy_rows, after_proxy_sum = proxy_summary(after)
    if before_proxy_rows != 709 or after_proxy_rows != 711:
        issues.append(f"proxy_row_count_unexpected before={before_proxy_rows} after={after_proxy_rows}")
    if round(after_proxy_sum - before_proxy_sum, 8) != 0.5:
        issues.append(f"proxy_sum_delta_unexpected {round(after_proxy_sum - before_proxy_sum, 8)}")
    if summary.get("pending_lifecycle_path_proxy_repaired_rows") != 2:
        issues.append("summary_repaired_rows_not_2")
    if summary.get("rows_requiring_source_cost_fill_repair_after") != 110:
        issues.append("summary_source_cost_fill_repair_after_not_110")
    if summary.get("opportunity_preservation_missing_after") != 0:
        issues.append("opportunity_preservation_missing_after_not_zero")
    if summary.get("safe_flags", {}).get("NO_PROMOTION_VERDICT") is not True:
        issues.append("safe_flag_no_promotion_missing")
    if summary.get("safe_flags", {}).get("live_effect") is not False:
        issues.append("live_effect_flag_not_false")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(after),
        "pending_lifecycle_path_proxy_repaired_rows": len(repaired),
        "numeric_proxy_rows_before": before_proxy_rows,
        "numeric_proxy_rows_after": after_proxy_rows,
        "proxy_r_sum_before": before_proxy_sum,
        "proxy_r_sum_after": after_proxy_sum,
        "proxy_r_sum_delta": round(after_proxy_sum - before_proxy_sum, 8),
        "rows_requiring_source_cost_fill_repair_after": summary.get(
            "rows_requiring_source_cost_fill_repair_after"
        ),
        "opportunity_preservation_missing_after": summary.get(
            "opportunity_preservation_missing_after"
        ),
        "safe_flags": summary.get("safe_flags"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
