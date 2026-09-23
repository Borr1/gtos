"""Verify entry-offset registry metadata after M15 hard no-fill repair."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / "MAIN_ORCH24_ENTRY_OFFSET_REGISTRY_AFTER_M15_HARD_NO_FILL_LEDGER_2026-05-17.jsonl"
SUMMARY = ROUTE_DIR / "MAIN_ORCH24_ENTRY_OFFSET_REGISTRY_AFTER_M15_HARD_NO_FILL_SUMMARY_2026-05-17.json"
MANIFEST = (
    ROUTE_DIR / "MAIN_ORCH24_ENTRY_OFFSET_REGISTRY_AFTER_M15_HARD_NO_FILL_OUTPUT_MANIFEST_2026-05-17.json"
)
RESULT = (
    ROUTE_DIR
    / "MAIN_ORCH24_ENTRY_OFFSET_REGISTRY_AFTER_M15_HARD_NO_FILL_VERIFICATION_RESULT_2026-05-17.json"
)

EXPECTED_BRANCH_DECISION = (
    "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_TICK_REPLAY_AND_M15_HARD_NO_FILL_SCORER_WITH_SOURCE_GATES"
)
EXPECTED_IMPLEMENTATION_CANDIDATE = (
    "KEEP_DEFAULT_OFF_ENTRY_OFFSET_050R_SCORER_WITH_SPREAD_AWARE_TICK_REPLAY_AND_M15_HARD_NO_FILL_GUARD"
)
EXPECTED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 3,
    "KEEP": 177,
    "KILL": 84,
    "REDESIGN": 10,
}
EXPECTED_STATUS_COUNTS = {
    "KILLED_ENTRY_OFFSET_050R_M15_HARD_NO_FILL": 2,
    "KILLED_ENTRY_OFFSET_050R_NO_FILL": 82,
    "NOT_APPLICABLE_NOT_ENTRY_REDESIGN_DENOMINATOR": 177,
    "SCORED_ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_PROXY": 10,
    "SCORED_ENTRY_OFFSET_050R_TICK_REPLAY_PROXY_DEFAULT_OFF": 3,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{path}:{line_no} invalid JSONL: {exc}") from exc
    return rows


def close_enough(left: Any, right: float, tolerance: float = 1e-8) -> bool:
    try:
        return abs(float(left) - right) <= tolerance
    except (TypeError, ValueError):
        return False


def main() -> None:
    failures: list[str] = []
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)
    rows = read_jsonl(LEDGER)

    if summary.get("rows") != 1 or len(rows) != 1:
        failures.append(f"expected 1 registry row, got summary={summary.get('rows')} ledger={len(rows)}")
    row = rows[0] if rows else {}
    if row.get("strategy_id") != "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER":
        failures.append(f"unexpected strategy id {row.get('strategy_id')}")
    if row.get("branch_decision") != EXPECTED_BRANCH_DECISION:
        failures.append(f"entry-offset branch decision stale: {row.get('branch_decision')}")
    if row.get("implementation_candidate") != EXPECTED_IMPLEMENTATION_CANDIDATE:
        failures.append("entry-offset implementation candidate missing or stale")
    if row.get("stale_metadata_tokens"):
        failures.append(f"stale entry-offset metadata tokens remain: {row.get('stale_metadata_tokens')}")
    evidence = str(row.get("decision_evidence") or "")
    if "MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR" not in evidence:
        failures.append("decision evidence does not cite M15 hard no-fill repair")
    if "source-repair rows 2->0" not in evidence:
        failures.append("decision evidence does not preserve source-repair closure")
    if "+8.66977687R" not in evidence:
        failures.append("decision evidence does not preserve proxy R sum")

    expected_counts = {
        "candidate_rows": 274,
        "no_fill_denominator_rows": 97,
        "numeric_proxy_rows": 97,
        "numeric_proxy_row_delta_from_repair": 2,
        "m15_hard_no_fill_repaired_rows": 2,
        "source_repair_rows_after": 0,
        "metadata_proxy_row_delta": 0,
        "exact_r_rows": 0,
    }
    for field, expected in expected_counts.items():
        if summary.get(field) != expected:
            failures.append(f"summary {field} expected {expected}, got {summary.get(field)}")
        if row.get(field) != expected:
            failures.append(f"ledger {field} expected {expected}, got {row.get(field)}")
    if not close_enough(summary.get("proxy_r_sum"), 8.66977687):
        failures.append(f"summary proxy sum mismatch {summary.get('proxy_r_sum')}")
    if not close_enough(row.get("proxy_r_sum"), 8.66977687):
        failures.append(f"ledger proxy sum mismatch {row.get('proxy_r_sum')}")
    if not close_enough(summary.get("proxy_r_sum_delta_from_repair"), 0.0):
        failures.append("repair proxy R sum delta is nonzero")
    if summary.get("after_entry_action_class_counts") != EXPECTED_ACTION_COUNTS:
        failures.append(f"action counts mismatch: {summary.get('after_entry_action_class_counts')}")
    if summary.get("after_entry_scorer_status_counts") != EXPECTED_STATUS_COUNTS:
        failures.append(f"status counts mismatch: {summary.get('after_entry_scorer_status_counts')}")
    if summary.get("metadata_rows_with_stale_tokens") != 0:
        failures.append("summary reports stale metadata tokens")
    if not close_enough(summary.get("metadata_proxy_r_sum_delta"), 0.0):
        failures.append("metadata proxy R delta is nonzero")
    if row.get("safe_flags", {}).get("live_effect") is not False:
        failures.append("ledger live_effect safe flag changed")

    manifest_counts = manifest.get("summary_counts", {})
    if manifest_counts.get("metadata_rows_with_stale_tokens") != 0:
        failures.append("manifest reports stale metadata tokens")
    if manifest_counts.get("source_repair_rows_after") != 0:
        failures.append("manifest reports remaining source-repair rows")
    for name, payload in manifest.get("inputs", {}).items():
        if not payload.get("exists"):
            failures.append(f"manifest input missing: {name}")
    for name, payload in manifest.get("outputs", {}).items():
        if not Path(payload.get("path", "")).exists():
            failures.append(f"manifest output missing: {name}")

    result = {
        "ok": not failures,
        "failures": failures,
        "rows": len(rows),
        "metadata_rows_with_stale_tokens": summary.get("metadata_rows_with_stale_tokens"),
        "candidate_rows": summary.get("candidate_rows"),
        "numeric_proxy_rows": summary.get("numeric_proxy_rows"),
        "source_repair_rows_after": summary.get("source_repair_rows_after"),
        "metadata_proxy_row_delta": summary.get("metadata_proxy_row_delta"),
        "metadata_proxy_r_sum_delta": summary.get("metadata_proxy_r_sum_delta"),
        "exact_r_rows": summary.get("exact_r_rows"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
