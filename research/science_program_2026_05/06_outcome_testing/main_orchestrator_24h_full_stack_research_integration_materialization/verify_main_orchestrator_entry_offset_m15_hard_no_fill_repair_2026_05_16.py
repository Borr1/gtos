"""Verify the entry-offset M15 hard no-fill repair plate."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_LEDGER_{DATE}.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
RESULT = ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_VERIFICATION_RESULT_{DATE}.json"
EXPECTED_REPAIRED_IDS = {
    "NAS100_2026-05-15T08:30:00+00:00",
    "NAS100_2026-05-15T15:00:00+00:00",
}


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


def approx_equal(left: float, right: float, tol: float = 1e-9) -> bool:
    return math.isclose(left, right, abs_tol=tol, rel_tol=0.0)


def main() -> None:
    issues: list[str] = []
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            issues.append(f"missing_output:{path.name}")
    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}

    if len(rows) != 274:
        issues.append(f"ledger_row_count_expected_274_got_{len(rows)}")
    if len({row.get("candidate_id") for row in rows}) != 274:
        issues.append("candidate_id_count_not_274")
    repaired = [row for row in rows if row.get("m15_hard_no_fill_repaired") is True]
    repaired_ids = {str(row.get("candidate_id")) for row in repaired}
    if repaired_ids != EXPECTED_REPAIRED_IDS:
        issues.append(f"repaired_ids_mismatch:{sorted(repaired_ids)}")
    for row in repaired:
        nearest = safe_float(row.get("m15_nearest_distance_to_entry_r"))
        if nearest is None or nearest < 1.0:
            issues.append(f"repaired_row_without_gt1r_distance:{row.get('candidate_id')}")
        if row.get("path_outcome_status") != "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH":
            issues.append(f"repaired_row_bad_path_status:{row.get('candidate_id')}")
        if row.get("latest_ltf_entry_first_touch_utc") not in (None, ""):
            issues.append(f"repaired_row_has_ltf_entry_touch:{row.get('candidate_id')}")
        if row.get("after_entry_proxy_r") != 0.0 or row.get("after_prefill_proxy_r") != 0.0:
            issues.append(f"repaired_row_not_zero_proxy:{row.get('candidate_id')}")
        if row.get("after_entry_score_status") != "COMPUTED_FROM_M15_HARD_NO_FILL_RANGE_PROOF":
            issues.append(f"repaired_row_bad_score_status:{row.get('candidate_id')}")

    checks = {
        "summary_rows": summary.get("rows") == 274,
        "summary_repaired_rows": summary.get("m15_hard_no_fill_repaired_rows") == 2,
        "before_numeric_proxy_rows": summary.get("before_numeric_proxy_rows") == 95,
        "after_numeric_proxy_rows": summary.get("after_numeric_proxy_rows") == 97,
        "numeric_proxy_row_delta": summary.get("numeric_proxy_row_delta") == 2,
        "proxy_sum_unchanged": approx_equal(float(summary.get("proxy_r_sum_delta", 999)), 0.0),
        "prefill_numeric_delta": summary.get("prefill_numeric_proxy_row_delta") == 2,
        "prefill_proxy_sum_unchanged": approx_equal(float(summary.get("prefill_proxy_r_sum_delta", 999)), 0.0),
        "entry_source_repair_closed": summary.get("after_entry_action_class_counts", {}).get("SOURCE_REPAIR", 0) == 0,
        "prefill_source_repair_closed": summary.get("after_prefill_action_class_counts", {}).get("SOURCE_REPAIR", 0) == 0,
        "entry_kill_count_84": summary.get("after_entry_action_class_counts", {}).get("KILL") == 84,
        "prefill_kill_count_84": summary.get("after_prefill_action_class_counts", {}).get("KILL") == 84,
        "safe_flags_closed": all(
            row.get("safe_flags", {}).get("NO_PROMOTION_VERDICT") is True
            and row.get("safe_flags", {}).get("validation_safe") is False
            and row.get("safe_flags", {}).get("outcome_review_opened") is False
            and row.get("safe_flags", {}).get("live_effect") is False
            and row.get("no_live_behavior") is True
            for row in rows
        ),
        "manifest_hash_ledger": bool(
            manifest.get("outputs", {}).get(LEDGER.name, {}).get("sha256") == sha256_file(LEDGER)
            if LEDGER.exists()
            else False
        ),
        "manifest_hash_summary": bool(
            manifest.get("outputs", {}).get(SUMMARY.name, {}).get("sha256") == sha256_file(SUMMARY)
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
        "repaired_ids": sorted(repaired_ids),
        "after_entry_action_class_counts": dict(Counter(str(row.get("after_entry_action_class")) for row in rows)),
        "after_prefill_action_class_counts": dict(Counter(str(row.get("after_prefill_action_class")) for row in rows)),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
