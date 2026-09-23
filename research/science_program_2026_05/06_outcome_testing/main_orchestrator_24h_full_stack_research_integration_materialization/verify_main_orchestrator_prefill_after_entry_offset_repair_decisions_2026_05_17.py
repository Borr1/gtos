"""Verify prefill delivery decisions after entry-offset repair."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = (
    ROUTE_DIR
    / f"MAIN_ORCH24_PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION_LEDGER_{DATE}.jsonl"
)
SUMMARY = (
    ROUTE_DIR
    / f"MAIN_ORCH24_PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION_SUMMARY_{DATE}.json"
)
MANIFEST = (
    ROUTE_DIR
    / f"MAIN_ORCH24_PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION_OUTPUT_MANIFEST_{DATE}.json"
)
RESULT = (
    ROUTE_DIR
    / f"MAIN_ORCH24_PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION_VERIFICATION_RESULT_{DATE}.json"
)

PREFILL_STRATEGY_ID = "PREFILL_DELIVERY_REVERSAL_PATH"
EXPECTED_TARGET_ACTIONS = {
    "IMPLEMENT_DEFAULT_OFF": 3,
    "KEEP": 177,
    "KILL": 84,
    "REDESIGN": 10,
}
EXPECTED_ACTION_DELTA = {
    "KILL": 84,
    "REDESIGN": -84,
}
EXPECTED_REPAIRED_IDS = {
    "NAS100_2026-05-15T08:30:00+00:00",
    "NAS100_2026-05-15T15:00:00+00:00",
}
EXPECTED_LINKED_PROXY_SUM = 8.66977687


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def approx_equal(left: float, right: float, tol: float = 1e-8) -> bool:
    return math.isclose(left, right, abs_tol=tol, rel_tol=0.0)


def main() -> None:
    issues: list[str] = []
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    target = [row for row in rows if row.get("strategy_id") == PREFILL_STRATEGY_ID]
    target_actions = dict(Counter(str(row.get("action_class")) for row in target))
    target_impl = Counter(str(row.get("implementation_decision")) for row in target)
    repaired = [row for row in target if row.get("m15_hard_no_fill_repaired") is True]
    repaired_ids = {str(row.get("candidate_id")) for row in repaired}
    linked_values = [
        value
        for row in target
        if (value := safe_float(row.get("linked_prefill_after_proxy_r"))) is not None
    ]

    if len(rows) != 3426:
        issues.append(f"ledger_row_count_expected_3426_got_{len(rows)}")
    if len(target) != 274:
        issues.append(f"target_row_count_expected_274_got_{len(target)}")
    if len({row.get("candidate_id") for row in target}) != 274:
        issues.append("target_candidate_id_count_not_274")
    if target_actions != EXPECTED_TARGET_ACTIONS:
        issues.append(f"target_action_counts_mismatch:{target_actions}")
    if summary.get("action_class_delta_vs_previous") != EXPECTED_ACTION_DELTA:
        issues.append(
            f"action_delta_mismatch:{summary.get('action_class_delta_vs_previous')}"
        )
    if target_impl.get(
        "KILL_PREFILL_FAR_MISS_050R_OFFSET_NO_FILL_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL"
    ) != 84:
        issues.append("prefill_far_miss_kill_impl_count_not_84")
    if target_impl.get("REDESIGN_PREFILL_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL") != 10:
        issues.append("prefill_far_miss_redesign_impl_count_not_10")
    if repaired_ids != EXPECTED_REPAIRED_IDS:
        issues.append(f"m15_repaired_ids_mismatch:{sorted(repaired_ids)}")
    for row in repaired:
        if row.get("action_class") != "KILL":
            issues.append(f"m15_repaired_row_not_kill:{row.get('candidate_id')}")
        if row.get("linked_entry_offset_after_score_status") != "COMPUTED_FROM_M15_HARD_NO_FILL_RANGE_PROOF":
            issues.append(f"m15_repaired_row_bad_score:{row.get('candidate_id')}")
        if row.get("linked_prefill_after_proxy_r") != 0.0:
            issues.append(f"m15_repaired_row_not_zero_proxy:{row.get('candidate_id')}")
    if any(row.get("action_class") == "SOURCE_REPAIR" for row in target):
        issues.append("target_source_repair_rows_remain")
    if summary.get("linked_entry_offset_before_numeric_proxy_rows") != 95:
        issues.append("linked_before_proxy_rows_not_95")
    if summary.get("linked_entry_offset_after_numeric_proxy_rows") != 97:
        issues.append("linked_after_proxy_rows_not_97")
    if summary.get("linked_entry_offset_numeric_proxy_row_delta") != 2:
        issues.append("linked_proxy_row_delta_not_2")
    if not approx_equal(
        float(summary.get("linked_entry_offset_after_proxy_r_sum", 999)),
        EXPECTED_LINKED_PROXY_SUM,
    ):
        issues.append("linked_after_proxy_sum_mismatch")
    if not approx_equal(float(summary.get("linked_entry_offset_proxy_r_sum_delta", 999)), 0.0):
        issues.append("linked_proxy_sum_delta_not_zero")
    if summary.get("numeric_proxy_row_delta") != 0 or not approx_equal(
        float(summary.get("proxy_r_sum_delta", 999)), 0.0
    ):
        issues.append("prefill_metadata_proxy_delta_not_zero")
    if summary.get("exact_r_rows") != 0:
        issues.append("exact_r_rows_not_zero")
    if not all(
        row.get("safe_flags", {}).get("NO_PROMOTION_VERDICT") is True
        and row.get("safe_flags", {}).get("validation_safe") is False
        and row.get("safe_flags", {}).get("outcome_review_opened") is False
        and row.get("safe_flags", {}).get("live_effect") is False
        and row.get("no_live_behavior") is True
        and row.get("no_shadow_log_append") is True
        for row in target
    ):
        issues.append("target_safe_flags_not_closed")

    checks = {
        "summary_rows": summary.get("rows") == 3426,
        "summary_target_rows": summary.get("prefill_target_rows") == 274,
        "summary_target_actions": summary.get("prefill_target_action_class_counts_after")
        == EXPECTED_TARGET_ACTIONS,
        "summary_missing_join_zero": summary.get("missing_repair_join_rows") == 0,
        "summary_linked_proxy_delta": summary.get("linked_entry_offset_numeric_proxy_row_delta") == 2,
        "manifest_hash_ledger": bool(
            manifest.get("outputs", {}).get("ledger", {}).get("sha256") == sha256_file(LEDGER)
            if LEDGER.exists()
            else False
        ),
        "manifest_hash_summary": bool(
            manifest.get("outputs", {}).get("summary", {}).get("sha256")
            == sha256_file(SUMMARY)
            if SUMMARY.exists()
            else False
        ),
    }
    for name, passed in checks.items():
        if not passed:
            issues.append(f"check_failed:{name}")

    result = {
        "ok": not issues,
        "issues": issues,
        "checks": checks,
        "row_count": len(rows),
        "prefill_target_rows": len(target),
        "target_action_counts": target_actions,
        "target_implementation_counts": dict(target_impl),
        "m15_hard_no_fill_repaired_ids": sorted(repaired_ids),
        "linked_after_numeric_proxy_rows": len(linked_values),
        "linked_after_proxy_r_sum": round(sum(linked_values), 8),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
