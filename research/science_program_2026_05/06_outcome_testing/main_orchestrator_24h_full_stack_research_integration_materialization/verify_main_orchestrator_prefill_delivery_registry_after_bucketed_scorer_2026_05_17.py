"""Verify prefill delivery registry metadata after bucketed scorer output."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = (
    ROUTE_DIR
    / "MAIN_ORCH24_PREFILL_DELIVERY_REGISTRY_AFTER_BUCKETED_SCORER_LEDGER_2026-05-17.jsonl"
)
SUMMARY = (
    ROUTE_DIR
    / "MAIN_ORCH24_PREFILL_DELIVERY_REGISTRY_AFTER_BUCKETED_SCORER_SUMMARY_2026-05-17.json"
)
MANIFEST = (
    ROUTE_DIR
    / "MAIN_ORCH24_PREFILL_DELIVERY_REGISTRY_AFTER_BUCKETED_SCORER_OUTPUT_MANIFEST_2026-05-17.json"
)
RESULT = (
    ROUTE_DIR
    / "MAIN_ORCH24_PREFILL_DELIVERY_REGISTRY_AFTER_BUCKETED_SCORER_VERIFICATION_RESULT_2026-05-17.json"
)

EXPECTED_BRANCH_DECISION = (
    "PREFILL_DELIVERY_BUCKETED_SCORER_OUTPUT_WITH_ENTRY_OFFSET_PROXY_BOUNDARY"
)
EXPECTED_IMPLEMENTATION_CANDIDATE = (
    "KEEP_BUCKETED_PREFILL_DELIVERY_SCORER_AND_BUILD_FAR_MISS_RETEST_CONTROL_MODEL"
)
EXPECTED_BUCKET_COUNTS = {
    "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE": 94,
    "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE": 3,
    "NOT_A_NO_FILL_TP1_ENTRY_REDESIGN_ROW": 177,
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
    if row.get("strategy_id") != "PREFILL_DELIVERY_REVERSAL_PATH":
        failures.append(f"unexpected strategy id {row.get('strategy_id')}")
    if row.get("branch_decision") != EXPECTED_BRANCH_DECISION:
        failures.append(f"prefill registry branch decision stale: {row.get('branch_decision')}")
    if row.get("implementation_candidate") != EXPECTED_IMPLEMENTATION_CANDIDATE:
        failures.append("prefill registry implementation candidate missing or stale")
    if row.get("stale_metadata_tokens"):
        failures.append(f"stale prefill metadata tokens remain: {row.get('stale_metadata_tokens')}")
    evidence = str(row.get("decision_evidence") or "")
    if "MAIN_ORCH24_PREFILL_DELIVERY_BUCKETED_SCORER_OUTPUT" not in evidence:
        failures.append("decision evidence does not cite bucketed scorer output plate")
    if "generic no-scorer 274->0" not in evidence:
        failures.append("decision evidence does not preserve generic no-scorer delta")
    if "+8.66977687R" not in evidence:
        failures.append("decision evidence does not preserve linked entry-offset proxy sum")

    expected_counts = {
        "action_rows": 3426,
        "prefill_target_rows": 274,
        "generic_no_scorer_rows_before": 274,
        "generic_no_scorer_rows_after": 0,
        "metadata_proxy_row_delta": 0,
        "exact_r_rows": 0,
        "linked_entry_offset_no_fill_rows": 97,
        "linked_entry_offset_numeric_proxy_rows": 95,
    }
    for field, expected in expected_counts.items():
        if summary.get(field) != expected:
            failures.append(f"summary {field} expected {expected}, got {summary.get(field)}")
        if row.get(field) != expected:
            failures.append(f"ledger {field} expected {expected}, got {row.get(field)}")
    if summary.get("bucket_counts") != EXPECTED_BUCKET_COUNTS:
        failures.append(f"summary bucket counts mismatch: {summary.get('bucket_counts')}")
    if row.get("bucket_counts") != EXPECTED_BUCKET_COUNTS:
        failures.append(f"ledger bucket counts mismatch: {row.get('bucket_counts')}")
    if summary.get("metadata_rows_with_stale_tokens") != 0:
        failures.append("summary reports stale metadata tokens")
    if not close_enough(summary.get("metadata_proxy_r_sum_delta"), 0.0):
        failures.append("metadata proxy R delta is nonzero")
    if not close_enough(row.get("metadata_proxy_r_sum_delta"), 0.0):
        failures.append("ledger metadata proxy R delta is nonzero")
    if not close_enough(summary.get("linked_entry_offset_proxy_r_sum"), 8.66977687):
        failures.append("linked entry-offset proxy sum mismatch")
    if row.get("safe_flags", {}).get("live_effect") is not False:
        failures.append("ledger live_effect safe flag changed")

    manifest_counts = manifest.get("summary_counts", {})
    if manifest_counts.get("metadata_rows_with_stale_tokens") != 0:
        failures.append("manifest reports stale metadata tokens")
    if manifest_counts.get("generic_no_scorer_rows_after") != 0:
        failures.append("manifest reports generic prefill rows after repair")
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
        "prefill_target_rows": summary.get("prefill_target_rows"),
        "generic_no_scorer_rows_after": summary.get("generic_no_scorer_rows_after"),
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
