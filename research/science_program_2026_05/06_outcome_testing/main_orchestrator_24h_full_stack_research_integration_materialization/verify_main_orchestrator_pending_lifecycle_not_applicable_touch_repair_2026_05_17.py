"""Verify pending lifecycle not-applicable touch/source repair plate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_NOT_APPLICABLE_TOUCH_REPAIR_LEDGER_2026-05-17.jsonl"
SUMMARY = ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_NOT_APPLICABLE_TOUCH_REPAIR_SUMMARY_2026-05-17.json"
MANIFEST = ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_NOT_APPLICABLE_TOUCH_REPAIR_OUTPUT_MANIFEST_2026-05-17.json"
RESULT = ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_NOT_APPLICABLE_TOUCH_REPAIR_VERIFICATION_RESULT_2026-05-17.json"

EXPECTED_REPAIR_COUNTS = {
    "entry_touch_spread_value_source_safe": 39,
    "entry_touch_spread_unit": 39,
    "terminal_area_first_touch_utc": 3,
    "protective_area_first_touch_utc": 25,
}
EXPECTED_MISSING_COUNTS = {
    "decision_spread_value_source_safe": 39,
    "decision_spread_unit": 39,
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

    if summary.get("rows") != 274 or len(rows) != 274:
        failures.append(f"expected 274 rows, got summary={summary.get('rows')} ledger={len(rows)}")
    if summary.get("internal_pending_lifecycle_rows") != 39:
        failures.append("internal pending lifecycle row count changed")
    if summary.get("source_repair_rows") != 39:
        failures.append(f"expected 39 source repair rows, got {summary.get('source_repair_rows')}")
    if summary.get("after_missing_source_field_cells") != 78:
        failures.append(
            f"expected 78 missing source cells, got {summary.get('after_missing_source_field_cells')}"
        )
    if summary.get("missing_source_field_cell_delta") != -106:
        failures.append(
            f"expected missing cell delta -106, got {summary.get('missing_source_field_cell_delta')}"
        )
    if summary.get("numeric_proxy_row_delta") != 0:
        failures.append("proxy row count changed")
    if not close_enough(summary.get("proxy_r_sum_delta"), 0.0):
        failures.append("proxy R sum changed")
    if summary.get("exact_r_rows") != 0:
        failures.append("exact-R rows opened")
    if summary.get("after_capture_complete_rows") != 0:
        failures.append("capture-complete rows should remain zero until decision spread exists")

    repair_counts = summary.get("source_repair_field_counts") or {}
    for field, expected in EXPECTED_REPAIR_COUNTS.items():
        if repair_counts.get(field) != expected:
            failures.append(f"{field} repair count expected {expected}, got {repair_counts.get(field)}")
    missing_counts = summary.get("missing_field_counts") or {}
    if missing_counts != EXPECTED_MISSING_COUNTS:
        failures.append(f"missing field counts expected {EXPECTED_MISSING_COUNTS}, got {missing_counts}")

    repaired_rows = [row for row in rows if row.get("source_repair_count", 0) > 0]
    if len(repaired_rows) != 39:
        failures.append(f"expected 39 repaired rows, got {len(repaired_rows)}")
    for row in repaired_rows:
        statuses = row.get("after_source_capture_statuses") or {}
        if statuses.get("decision_spread_value_source_safe") != "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW":
            failures.append("decision spread value was incorrectly repaired")
            break
        if statuses.get("decision_spread_unit") != "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW":
            failures.append("decision spread unit was incorrectly repaired")
            break
    if not any(
        "NOT_APPLICABLE_NO_ENTRY_TOUCH_BY_ASOF"
        in (row.get("after_source_capture_statuses") or {}).values()
        for row in repaired_rows
    ):
        failures.append("no row carries the no-entry-touch not-applicable status")
    if not any(
        "NOT_APPLICABLE_PROTECTIVE_AREA_NOT_TOUCHED_BY_ASOF"
        in (row.get("after_source_capture_statuses") or {}).values()
        for row in repaired_rows
    ):
        failures.append("no row carries the protective-area not-applicable status")

    manifest_outputs = manifest.get("output_artifacts", {})
    for name, payload in manifest_outputs.items():
        path = ROUTE_DIR / name if not Path(name).is_absolute() else Path(name)
        if payload.get("size_bytes") is None:
            failures.append(f"manifest output missing size for {name}")
    if manifest.get("safe_flags", {}).get("live_effect") is not False:
        failures.append("manifest live_effect safe flag changed")

    result = {
        "ok": not failures,
        "failures": failures,
        "rows": len(rows),
        "source_repair_rows": summary.get("source_repair_rows"),
        "after_missing_source_field_cells": summary.get("after_missing_source_field_cells"),
        "missing_source_field_cell_delta": summary.get("missing_source_field_cell_delta"),
        "proxy_r_sum_delta": summary.get("proxy_r_sum_delta"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
