from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
INPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_SOURCE_KILL_SCOPE_REDESIGN_LEDGER_2026-05-17.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_AVOID_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
SUMMARY = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_AVOID_MATERIALIZATION_SUMMARY_2026-05-17.json"
MANIFEST = ROUTE_DIR / "MAIN_ORCH24_GBPJPY_LONG_ADVERSE_AVOID_OUTPUT_MANIFEST_2026-05-17.json"
VERIFY_RESULT = ROUTE_DIR / "MAIN_ORCH24_GBPJPY_LONG_ADVERSE_AVOID_MATERIALIZATION_VERIFY_RESULT_2026-05-17.json"

OLD_BRANCH = "REDESIGN_GBPJPY_LONG_STRUCTURAL_FVG_OB_ADVERSE_CLUSTER_AVOID_FILTER_CANDIDATE"
IMPLEMENT_BRANCH = "IMPLEMENT_DEFAULT_OFF_GBPJPY_LONG_STRUCTURAL_FVG_OB_ADVERSE_AVOID_FILTER"
DUPLICATE_BRANCH = "MERGE_DUPLICATE_GBPJPY_LONG_ADVERSE_AVOID_EVIDENCE_TO_CANONICAL_OWNER"
SOURCE_BRANCH = "REDESIGN_GBPJPY_LONG_ADVERSE_AVOID_FILTER_SOURCE_REQUIRED"
TARGET_STATUS = "RECLASSIFIED_IMPLEMENT_TO_REDESIGN_AVOID_FILTER_CANDIDATE"


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


def target_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("gbpjpy_long_adverse_reclass_status") == TARGET_STATUS
        or row.get("before_gbpjpy_long_adverse_avoid_branch_decision") == OLD_BRANCH
        or row.get("branch_decision") in {OLD_BRANCH, IMPLEMENT_BRANCH, DUPLICATE_BRANCH, SOURCE_BRANCH}
    ]


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

    before_targets = [
        row
        for row in before
        if row.get("gbpjpy_long_adverse_reclass_status") == TARGET_STATUS
        or row.get("branch_decision") == OLD_BRANCH
    ]
    after_targets = target_rows(after)
    if len(before_targets) != 62 or len(after_targets) != 62:
        issues.append(f"expected_62_adverse_rows before={len(before_targets)} after={len(after_targets)}")

    implement_rows = [row for row in after_targets if row.get("branch_decision") == IMPLEMENT_BRANCH]
    duplicate_rows = [row for row in after_targets if row.get("branch_decision") == DUPLICATE_BRANCH]
    source_rows = [row for row in after_targets if row.get("branch_decision") == SOURCE_BRANCH]
    if len(implement_rows) != 9:
        issues.append(f"expected_9_implement_avoid_owner_rows_found_{len(implement_rows)}")
    if len(duplicate_rows) != 13:
        issues.append(f"expected_13_duplicate_reference_rows_found_{len(duplicate_rows)}")
    if len(source_rows) != 40:
        issues.append(f"expected_40_source_required_rows_found_{len(source_rows)}")

    old_remaining = [row for row in after_targets if row.get("branch_decision") == OLD_BRANCH]
    if old_remaining:
        issues.append(f"old_adverse_redesign_branch_rows_remain_{len(old_remaining)}")

    for row in implement_rows:
        saved = safe_float(row.get("gbpjpy_long_adverse_avoid_saved_proxy_r"))
        current_ref = safe_float(row.get("gbpjpy_long_adverse_current_claim_proxy_r_reference"))
        if row.get("action_class") != "IMPLEMENT_DEFAULT_OFF":
            issues.append(f"{row.get('row_id')}_implement_owner_action_class_not_default_off")
        if row.get("gbpjpy_long_adverse_avoid_materialization_status") != "CANONICAL_AVOID_FILTER_SAVED_R_OWNER":
            issues.append(f"{row.get('row_id')}_canonical_status_missing")
        if saved != 1.0 or current_ref != -1.0:
            issues.append(f"{row.get('row_id')}_saved_or_reference_proxy_wrong saved={saved} ref={current_ref}")
        if row.get("gbpjpy_long_adverse_avoid_saved_proxy_counted") is not True:
            issues.append(f"{row.get('row_id')}_saved_proxy_not_counted")
        if row.get("underlying_intelligence_preserved") is not True:
            issues.append(f"{row.get('row_id')}_underlying_intelligence_not_preserved")

    for row in duplicate_rows:
        if row.get("action_class") != "REDESIGN":
            issues.append(f"{row.get('row_id')}_duplicate_not_redesign")
        if row.get("gbpjpy_long_adverse_avoid_saved_proxy_counted") is not False:
            issues.append(f"{row.get('row_id')}_duplicate_saved_proxy_counted")
        if not row.get("gbpjpy_long_adverse_avoid_owner_row_id"):
            issues.append(f"{row.get('row_id')}_duplicate_owner_missing")

    for row in source_rows:
        if safe_float(row.get("gbpjpy_long_adverse_avoid_saved_proxy_r")) is not None:
            issues.append(f"{row.get('row_id')}_source_required_has_saved_proxy")
        if row.get("gbpjpy_long_adverse_current_claim_proxy_reference_status") != "NO_NUMERIC_PROXY_CURRENT_ROW_SOURCE_OR_LTF_REQUIRED":
            issues.append(f"{row.get('row_id')}_source_required_reference_status_wrong")

    before_proxy_rows, before_proxy_sum = proxy_summary(before)
    after_proxy_rows, after_proxy_sum = proxy_summary(after)
    if before_proxy_rows != after_proxy_rows or after_proxy_rows != 711:
        issues.append(f"proxy_row_count_changed before={before_proxy_rows} after={after_proxy_rows}")
    if before_proxy_sum != after_proxy_sum or after_proxy_sum != 33.69811387:
        issues.append(f"proxy_sum_changed before={before_proxy_sum} after={after_proxy_sum}")

    saved_sum = round(sum(safe_float(row.get("gbpjpy_long_adverse_avoid_saved_proxy_r")) or 0.0 for row in implement_rows), 8)
    if saved_sum != 9.0:
        issues.append(f"saved_proxy_sum_expected_9_got_{saved_sum}")
    if summary.get("avoid_saved_r_owner_rows") != 9 or summary.get("avoid_saved_proxy_r_sum") != 9.0:
        issues.append("summary_saved_rows_or_sum_wrong")
    if summary.get("rows_moved_from_redesign_to_implement_default_off") != 9:
        issues.append("summary_rows_moved_not_9")
    if summary.get("current_negative_proxy_reference_rows") != 22:
        issues.append("summary_current_negative_proxy_reference_rows_not_22")
    if summary.get("current_negative_proxy_reference_sum") != -22.0:
        issues.append("summary_current_negative_proxy_reference_sum_not_minus_22")
    if summary.get("opportunity_preservation_missing_after") != 0:
        issues.append("opportunity_preservation_missing_after_not_zero")
    if manifest.get("safe_flags", {}).get("live_effect") is not False:
        issues.append("manifest_live_effect_not_false")

    result = {
        "verified": not issues,
        "issues": issues,
        "rows": len(after),
        "adverse_rows_materialized": len(after_targets),
        "avoid_saved_r_owner_rows": len(implement_rows),
        "avoid_saved_proxy_r_sum": saved_sum,
        "duplicate_proxy_reference_rows": len(duplicate_rows),
        "source_required_rows": len(source_rows),
        "numeric_proxy_rows": after_proxy_rows,
        "proxy_r_sum": after_proxy_sum,
        "opportunity_preservation_missing_after": summary.get("opportunity_preservation_missing_after"),
        "safe_flags": summary.get("safe_flags"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
