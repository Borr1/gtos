from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
INPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_AVOID_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_2026-05-17.jsonl"
SUMMARY = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_SUMMARY_2026-05-17.json"
MANIFEST = ROUTE_DIR / "MAIN_ORCH24_ENTRY_OFFSET_CONCENTRATION_GUARD_OUTPUT_MANIFEST_2026-05-17.json"
VERIFY_RESULT = ROUTE_DIR / "MAIN_ORCH24_ENTRY_OFFSET_CONCENTRATION_GUARD_VERIFY_RESULT_2026-05-17.json"

OWNER_BRANCHES = {
    "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_CHALLENGER",
    "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_NEAR_MISS_CHALLENGER",
}
PREFILL_REFERENCE_BRANCHES = {
    "REDESIGN_PREFILL_FAR_MISS_RETEST_CONTROL_MERGED_INTO_ENTRY_OFFSET_050R",
    "MERGE_PREFILL_NEAR_MISS_INTO_ENTRY_OFFSET_050R_IMPLEMENTATION",
}
NO_FILL_CONTROL_BRANCHES = {
    "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL",
    "KILL_PREFILL_050R_OFFSET_NO_FILL_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL",
}
GUARDED_OWNER_BRANCH = "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_CONCENTRATION_GUARDED_CANDIDATE"
GUARDED_PREFILL_BRANCH = "MERGE_PREFILL_ENTRY_OFFSET_CONCENTRATION_GUARD_REFERENCE"
LARGEST_CLUSTER_KEY = "US30_cash|2026-05-08"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def proxy_summary(rows: list[dict[str, Any]]) -> tuple[int, float]:
    count = 0
    total = 0.0
    for row in rows:
        value = row.get("after_proxy_r")
        if value is None:
            value = row.get("strategy_proxy_r")
        number = safe_float(value)
        if number is None:
            continue
        count += 1
        total += number
    return count, round(total, 8)


def main() -> None:
    issues: list[str] = []
    before = read_jsonl(INPUT_LEDGER)
    after = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)

    if len(before) != 3426 or len(after) != 3426:
        issues.append(f"row_count_mismatch before={len(before)} after={len(after)}")
    if [row.get("row_id") for row in before] != [row.get("row_id") for row in after]:
        issues.append("row_identity_or_order_changed")

    before_owner = [row for row in before if row.get("branch_decision") in OWNER_BRANCHES]
    before_prefill = [row for row in before if row.get("branch_decision") in PREFILL_REFERENCE_BRANCHES]
    before_no_fill = [row for row in before if row.get("branch_decision") in NO_FILL_CONTROL_BRANCHES]
    owner_rows = [row for row in after if row.get("branch_decision") == GUARDED_OWNER_BRANCH]
    prefill_rows = [row for row in after if row.get("branch_decision") == GUARDED_PREFILL_BRANCH]
    no_fill_rows = [
        row
        for row in after
        if row.get("entry_offset_no_fill_control_status")
        == "CURRENT_050R_FILL_CLAIM_UNSUPPORTED_REDESIGN_PATH_PRESERVED"
    ]

    if len(before_owner) != 13 or len(owner_rows) != 13:
        issues.append(f"expected_13_owner_rows before={len(before_owner)} after={len(owner_rows)}")
    if len(before_prefill) != 13 or len(prefill_rows) != 13:
        issues.append(f"expected_13_prefill_reference_rows before={len(before_prefill)} after={len(prefill_rows)}")
    if len(before_no_fill) != 168 or len(no_fill_rows) != 168:
        issues.append(f"expected_168_no_fill_rows before={len(before_no_fill)} after={len(no_fill_rows)}")

    old_owner_remaining = [row for row in after if row.get("branch_decision") in OWNER_BRANCHES]
    old_prefill_remaining = [row for row in after if row.get("branch_decision") in PREFILL_REFERENCE_BRANCHES]
    if old_owner_remaining:
        issues.append(f"old_owner_branches_remain_{len(old_owner_remaining)}")
    if old_prefill_remaining:
        issues.append(f"old_prefill_reference_branches_remain_{len(old_prefill_remaining)}")

    before_proxy_rows, before_proxy_sum = proxy_summary(before)
    after_proxy_rows, after_proxy_sum = proxy_summary(after)
    if before_proxy_rows != after_proxy_rows or after_proxy_rows != 711:
        issues.append(f"proxy_row_count_changed before={before_proxy_rows} after={after_proxy_rows}")
    if before_proxy_sum != after_proxy_sum or after_proxy_sum != 33.69811387:
        issues.append(f"proxy_sum_changed before={before_proxy_sum} after={after_proxy_sum}")

    owner_sum = round(sum(safe_float(row.get("after_proxy_r")) or 0.0 for row in owner_rows), 8)
    prefill_ref_sum = round(sum(safe_float(row.get("opportunity_proxy_r_reference")) or 0.0 for row in prefill_rows), 8)
    if owner_sum != 8.66977687:
        issues.append(f"owner_proxy_sum_expected_8.66977687_got_{owner_sum}")
    if prefill_ref_sum != 8.66977687:
        issues.append(f"prefill_reference_sum_expected_8.66977687_got_{prefill_ref_sum}")

    owner_refs = {str(row.get("row_id")) for row in owner_rows}
    for row in owner_rows:
        if row.get("action_class") != "IMPLEMENT_DEFAULT_OFF":
            issues.append(f"{row.get('row_id')}_owner_action_class_changed")
        if row.get("entry_offset_proxy_reference_status") != "COUNTED_ON_ENTRY_OFFSET_OWNER_ROW_ONLY":
            issues.append(f"{row.get('row_id')}_owner_proxy_reference_status_wrong")
        if row.get("entry_offset_proxy_owner_row_id") != row.get("row_id"):
            issues.append(f"{row.get('row_id')}_owner_row_id_not_self")
        if row.get("underlying_intelligence_preserved") is not True:
            issues.append(f"{row.get('row_id')}_owner_underlying_intelligence_not_preserved")
        if not isinstance(row.get("missed_opportunity_audit"), dict):
            issues.append(f"{row.get('row_id')}_owner_audit_missing")

    for row in prefill_rows:
        if row.get("action_class") != "REDESIGN":
            issues.append(f"{row.get('row_id')}_prefill_not_redesign")
        if row.get("entry_offset_proxy_reference_status") != "REFERENCE_ONLY_NOT_DUPLICATED":
            issues.append(f"{row.get('row_id')}_prefill_reference_status_wrong")
        if row.get("entry_offset_proxy_owner_row_id") not in owner_refs:
            issues.append(f"{row.get('row_id')}_prefill_owner_not_guarded_owner")
        if safe_float(row.get("after_proxy_r")) is not None:
            issues.append(f"{row.get('row_id')}_prefill_after_proxy_should_remain_null")
        if row.get("underlying_intelligence_preserved") is not True:
            issues.append(f"{row.get('row_id')}_prefill_underlying_intelligence_not_preserved")

    for row in no_fill_rows:
        if row.get("action_class") != "KILL":
            issues.append(f"{row.get('row_id')}_no_fill_action_class_not_current_claim_kill")
        if row.get("entry_offset_no_fill_repair_branch_candidate") != "REDESIGN_ENTRY_OFFSET_NO_FILL_RETEST_SOURCE_COST_FILL_REPAIR_REQUIRED":
            issues.append(f"{row.get('row_id')}_no_fill_repair_branch_missing")
        if row.get("underlying_intelligence_preserved") is not True:
            issues.append(f"{row.get('row_id')}_no_fill_underlying_intelligence_not_preserved")

    largest_owner = [
        row for row in owner_rows if row.get("entry_offset_concentration_cluster_key") == LARGEST_CLUSTER_KEY
    ]
    largest_sum = round(sum(safe_float(row.get("after_proxy_r")) or 0.0 for row in largest_owner), 8)
    if len(largest_owner) != 11:
        issues.append(f"largest_cluster_owner_count_expected_11_got_{len(largest_owner)}")
    if largest_sum != 7.33544301:
        issues.append(f"largest_cluster_sum_expected_7.33544301_got_{largest_sum}")
    if summary.get("effective_cluster_count") != 3:
        issues.append("summary_effective_cluster_count_not_3")
    if summary.get("largest_cluster_key") != LARGEST_CLUSTER_KEY:
        issues.append("summary_largest_cluster_key_wrong")
    if summary.get("largest_cluster_row_count") != 11:
        issues.append("summary_largest_cluster_row_count_not_11")
    if summary.get("largest_cluster_proxy_r_sum") != 7.33544301:
        issues.append("summary_largest_cluster_proxy_sum_wrong")
    if summary.get("largest_cluster_row_share") != 0.84615385:
        issues.append("summary_largest_cluster_row_share_wrong")
    if summary.get("prefill_reference_proxy_rows_referenced") != 13:
        issues.append("summary_prefill_reference_proxy_rows_not_13")
    if summary.get("prefill_reference_proxy_r_sum_referenced") != 8.66977687:
        issues.append("summary_prefill_reference_sum_wrong")
    if summary.get("proxy_r_reference_mentions_not_duplicated") is not True:
        issues.append("summary_proxy_duplication_flag_wrong")
    if summary.get("opportunity_preservation_missing_after") != 0:
        issues.append("opportunity_preservation_missing_after_not_zero")
    if manifest.get("safe_flags", {}).get("live_effect") is not False:
        issues.append("manifest_live_effect_not_false")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(after),
        "entry_offset_owner_rows_guarded": len(owner_rows),
        "entry_offset_owner_proxy_r_sum_counted": owner_sum,
        "prefill_reference_rows_guarded": len(prefill_rows),
        "prefill_reference_proxy_r_sum_referenced": prefill_ref_sum,
        "no_fill_control_rows_preserved": len(no_fill_rows),
        "largest_cluster_key": LARGEST_CLUSTER_KEY,
        "largest_cluster_owner_rows": len(largest_owner),
        "largest_cluster_proxy_r_sum": largest_sum,
        "numeric_proxy_rows": after_proxy_rows,
        "proxy_r_sum": after_proxy_sum,
        "rows_requiring_source_cost_fill_repair": summary.get("rows_requiring_source_cost_fill_repair"),
        "rows_with_missed_opportunity_audit": summary.get("rows_with_missed_opportunity_audit"),
        "opportunity_preservation_missing_after": summary.get("opportunity_preservation_missing_after"),
        "safe_flags": summary.get("safe_flags"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
