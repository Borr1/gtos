from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
INPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_PATH_PROXY_REPAIR_LEDGER_2026-05-17.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_SOURCE_KILL_SCOPE_REDESIGN_LEDGER_2026-05-17.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_SOURCE_KILL_SCOPE_REDESIGN_SUMMARY_2026-05-17.json"
VERIFY_RESULT = ROUTE_DIR / "MAIN_ORCH24_SOURCE_KILL_SCOPE_REDESIGN_VERIFY_RESULT_2026-05-17.json"

OLD_BRANCH = "KILL_SOURCE_REPAIR_UPGRADED_CHALLENGER_AFTER_ORDERING_NEGATIVE_PROXY"
NEW_BRANCH = "REDESIGN_SOURCE_REPAIR_UPGRADED_CHALLENGER_NEGATIVE_PROXY_AVOID_OR_EXACT_ORDERING"
EXPECTED_ROWS = {
    "MAIN-ORCH24-ACTION-SRCM15-03290": -0.239737,
    "MAIN-ORCH24-ACTION-SRCM15-03320": -0.161624,
    "MAIN-ORCH24-ACTION-SRCM15-03421": -0.02531,
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
    if [row.get("row_id") for row in before] != [row.get("row_id") for row in after]:
        issues.append("row_identity_or_order_changed")

    old_rows = [row for row in after if row.get("branch_decision") == OLD_BRANCH]
    if old_rows:
        issues.append(f"old_kill_branch_rows_remain_{len(old_rows)}")

    converted = [row for row in after if row.get("branch_decision") == NEW_BRANCH]
    if len(converted) != 3:
        issues.append(f"expected_3_redesigned_rows_found_{len(converted)}")
    for row in converted:
        row_id = str(row.get("row_id") or "")
        expected_proxy = EXPECTED_ROWS.get(row_id)
        if expected_proxy is None:
            issues.append(f"unexpected_redesigned_row_{row_id}")
            continue
        if row.get("action_class") != "REDESIGN":
            issues.append(f"{row_id}_not_redesign")
        if row.get("source_kill_scope_redesign_status") != "KILL_LABEL_REPLACED_WITH_REDESIGN_UNDER_CURRENT_CLAIM_SCOPE_RULE":
            issues.append(f"{row_id}_missing_redesign_status")
        if row.get("underlying_intelligence_preserved") is not True:
            issues.append(f"{row_id}_underlying_intelligence_not_preserved")
        audit = row.get("missed_opportunity_audit") or {}
        if audit.get("kill_scope") != "CURRENT_CLAIM_REDESIGNED_NOT_KILLED":
            issues.append(f"{row_id}_audit_scope_not_redesigned")
        try:
            proxy = float(row.get("after_proxy_r"))
        except (TypeError, ValueError):
            proxy = None
        if proxy != expected_proxy:
            issues.append(f"{row_id}_proxy_expected_{expected_proxy}_got_{proxy}")

    before_proxy_rows, before_proxy_sum = proxy_summary(before)
    after_proxy_rows, after_proxy_sum = proxy_summary(after)
    if before_proxy_rows != after_proxy_rows or before_proxy_rows != 711:
        issues.append(f"proxy_row_count_changed before={before_proxy_rows} after={after_proxy_rows}")
    if before_proxy_sum != after_proxy_sum or after_proxy_sum != 33.69811387:
        issues.append(f"proxy_sum_changed before={before_proxy_sum} after={after_proxy_sum}")
    if summary.get("source_kill_scope_rows_redesigned") != 3:
        issues.append("summary_redesigned_rows_not_3")
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
        "source_kill_scope_rows_redesigned": len(converted),
        "numeric_proxy_rows": after_proxy_rows,
        "proxy_r_sum": after_proxy_sum,
        "proxy_r_sum_delta": round(after_proxy_sum - before_proxy_sum, 8),
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
