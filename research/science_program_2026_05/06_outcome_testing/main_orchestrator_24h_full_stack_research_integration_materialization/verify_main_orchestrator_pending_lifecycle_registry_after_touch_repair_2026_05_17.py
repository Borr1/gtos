"""Verify pending lifecycle registry metadata after not-applicable touch repair."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_REGISTRY_AFTER_TOUCH_REPAIR_LEDGER_2026-05-17.jsonl"
SUMMARY = ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_REGISTRY_AFTER_TOUCH_REPAIR_SUMMARY_2026-05-17.json"
MANIFEST = (
    ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_REGISTRY_AFTER_TOUCH_REPAIR_OUTPUT_MANIFEST_2026-05-17.json"
)
RESULT = (
    ROUTE_DIR
    / "MAIN_ORCH24_PENDING_LIFECYCLE_REGISTRY_AFTER_TOUCH_REPAIR_VERIFICATION_RESULT_2026-05-17.json"
)

EXPECTED_BRANCH_DECISION = (
    "KEEP_PENDING_LIFECYCLE_SCORER_WITH_NOT_APPLICABLE_TOUCH_REPAIR_AND_DECISION_SPREAD_FORWARD_CAPTURE"
)
EXPECTED_IMPLEMENTATION_CANDIDATE = (
    "KEEP_SHADOW_ONLY_PENDING_LIFECYCLE_SCORER_WITH_DECISION_SPREAD_FORWARD_CAPTURE_AND_NOT_APPLICABLE_TOUCH_CLASSIFICATION"
)
EXPECTED_MISSING_COUNTS = {
    "decision_spread_unit": 39,
    "decision_spread_value_source_safe": 39,
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
        return abs(float(left) - float(right)) <= tolerance
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
    if row.get("strategy_id") != "PENDING_LIMIT_LIFECYCLE":
        failures.append(f"unexpected strategy id {row.get('strategy_id')}")
    if row.get("branch_decision") != EXPECTED_BRANCH_DECISION:
        failures.append(f"pending lifecycle branch decision stale: {row.get('branch_decision')}")
    if row.get("implementation_candidate") != EXPECTED_IMPLEMENTATION_CANDIDATE:
        failures.append("pending lifecycle implementation candidate missing or stale")
    if row.get("stale_metadata_tokens"):
        failures.append(f"stale metadata tokens remain: {row.get('stale_metadata_tokens')}")
    decision_evidence = str(row.get("decision_evidence") or "")
    if "MAIN_ORCH24_PENDING_LIFECYCLE_NOT_APPLICABLE_TOUCH_REPAIR" not in decision_evidence:
        failures.append("decision evidence does not cite not-applicable touch repair")
    if "184->78" not in decision_evidence:
        failures.append("decision evidence does not preserve missing-cell delta 184->78")
    if "decision_spread" not in decision_evidence:
        failures.append("decision evidence does not preserve remaining decision-spread boundary")

    expected_counts = {
        "current_rows": 274,
        "current_internal_pending_lifecycle_rows": 39,
        "current_numeric_proxy_rows": 197,
        "previous_missing_source_field_cells": 184,
        "current_missing_source_field_cells": 78,
        "missing_source_field_cell_delta": -106,
        "source_repair_rows": 39,
        "not_applicable_source_repair_rows": 38,
    }
    for field, expected in expected_counts.items():
        if summary.get(field) != expected:
            failures.append(f"summary {field} expected {expected}, got {summary.get(field)}")
        if row.get(field) != expected:
            failures.append(f"ledger {field} expected {expected}, got {row.get(field)}")
    if not close_enough(summary.get("current_proxy_r_sum"), 50.0):
        failures.append(f"summary proxy sum expected 50.0, got {summary.get('current_proxy_r_sum')}")
    if not close_enough(row.get("current_proxy_r_sum"), 50.0):
        failures.append(f"ledger proxy sum expected 50.0, got {row.get('current_proxy_r_sum')}")
    if summary.get("remaining_missing_field_counts") != EXPECTED_MISSING_COUNTS:
        failures.append(
            f"summary missing counts expected {EXPECTED_MISSING_COUNTS}, got {summary.get('remaining_missing_field_counts')}"
        )
    if row.get("remaining_missing_field_counts") != EXPECTED_MISSING_COUNTS:
        failures.append(
            f"ledger missing counts expected {EXPECTED_MISSING_COUNTS}, got {row.get('remaining_missing_field_counts')}"
        )
    if summary.get("metadata_rows_with_stale_tokens") != 0:
        failures.append("summary reports stale metadata tokens")
    if summary.get("metadata_refresh_proxy_row_delta") != 0:
        failures.append("metadata refresh changed proxy row count")
    if not close_enough(summary.get("metadata_refresh_proxy_r_sum_delta"), 0.0):
        failures.append("metadata refresh changed proxy R sum")
    if summary.get("exact_r_rows") != 0 or row.get("exact_r_rows") != 0:
        failures.append("metadata refresh opened exact-R rows")
    if row.get("safe_flags", {}).get("live_effect") is not False:
        failures.append("ledger live_effect safe flag changed")

    manifest_counts = manifest.get("summary_counts", {})
    if manifest_counts.get("current_missing_source_field_cells") != 78:
        failures.append("manifest missing-cell count is not refreshed to 78")
    if manifest_counts.get("metadata_rows_with_stale_tokens") != 0:
        failures.append("manifest stale-token count is nonzero")
    for name, payload in manifest.get("inputs", {}).items():
        if not payload.get("exists"):
            failures.append(f"manifest input missing: {name}")
    for name, payload in manifest.get("outputs", {}).items():
        path = Path(payload.get("path", ""))
        if not path.exists():
            failures.append(f"manifest output missing: {name}")

    result = {
        "ok": not failures,
        "failures": failures,
        "rows": len(rows),
        "metadata_rows_with_stale_tokens": summary.get("metadata_rows_with_stale_tokens"),
        "current_missing_source_field_cells": summary.get("current_missing_source_field_cells"),
        "metadata_refresh_proxy_row_delta": summary.get("metadata_refresh_proxy_row_delta"),
        "metadata_refresh_proxy_r_sum_delta": summary.get("metadata_refresh_proxy_r_sum_delta"),
        "exact_r_rows": summary.get("exact_r_rows"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
