"""Materialize pending lifecycle LTF first-touch source repair deltas.

This plate compares the previous pending lifecycle source-derivation checkpoint
against the current scorer output after adding LTF first-touch fallback fields.
It is read-only for shadow logs and does not change proxy R, broker truth, or
live behavior.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_main_orchestrator_pending_lifecycle_source_derivation_recompute_2026_05_16 import (
    DATE,
    INPUTS,
    OUTPUT_LEDGER as PREVIOUS_LEDGER,
    OUTPUT_SUMMARY as PREVIOUS_SUMMARY,
    PENDING_LIFECYCLE_CAPTURE_FIELDS,
    ROUTE_DIR,
    ROUTE_ID,
    SAFE_FLAGS,
    build_rows,
    safe_float,
)


OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_LTF_FIRST_TOUCH_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_LTF_FIRST_TOUCH_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_LTF_FIRST_TOUCH_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

FIRST_TOUCH_FIELDS = {
    "terminal_area_touch_status",
    "terminal_area_first_touch_utc",
    "protective_area_touch_status",
    "protective_area_first_touch_utc",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def is_missing(status: str | None) -> bool:
    return status in {None, "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW"}


def capture_statuses(row: dict[str, Any]) -> dict[str, str]:
    statuses = row.get("after_source_capture_statuses")
    return statuses if isinstance(statuses, dict) else {}


def capture_derivations(row: dict[str, Any]) -> dict[str, str]:
    derivations = row.get("after_source_capture_derivations")
    return derivations if isinstance(derivations, dict) else {}


def source_field_value(row: dict[str, Any], field: str) -> Any:
    return row.get(f"pending_lifecycle_{field}")


def diff_fields(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    previous_statuses = capture_statuses(previous)
    current_statuses = capture_statuses(current)
    previous_derivations = capture_derivations(previous)
    current_derivations = capture_derivations(current)

    repaired_fields: list[str] = []
    changed_fields: dict[str, dict[str, Any]] = {}
    for field in PENDING_LIFECYCLE_CAPTURE_FIELDS:
        before_status = previous_statuses.get(field)
        after_status = current_statuses.get(field)
        before_value = source_field_value(previous, field)
        after_value = source_field_value(current, field)
        if is_missing(before_status) and not is_missing(after_status):
            repaired_fields.append(field)
        if before_status != after_status or before_value != after_value:
            changed_fields[field] = {
                "before_status": before_status,
                "after_status": after_status,
                "before_derivation": previous_derivations.get(field),
                "after_derivation": current_derivations.get(field),
                "before_value": before_value,
                "after_value": after_value,
            }
    first_touch_repair_fields = [field for field in repaired_fields if field in FIRST_TOUCH_FIELDS]
    return {
        "repaired_fields": repaired_fields,
        "first_touch_repair_fields": first_touch_repair_fields,
        "changed_fields": changed_fields,
    }


def branch_decision(current: dict[str, Any], first_touch_fields: list[str]) -> str:
    if first_touch_fields:
        return "IMPLEMENT_PENDING_LIFECYCLE_LTF_FIRST_TOUCH_SOURCE_REPAIR"
    if capture_statuses(current):
        return "KEEP_PENDING_LIFECYCLE_SOURCE_DERIVATION_PROXY_R_UNCHANGED"
    return "KEEP_NON_PENDING_LIFECYCLE_ROW_OUTSIDE_SOURCE_REPAIR_DENOMINATOR"


def build_delta_rows() -> list[dict[str, Any]]:
    previous_rows = {row["candidate_id"]: row for row in read_jsonl(PREVIOUS_LEDGER)}
    current_rows = {row["candidate_id"]: row for row in build_rows()}
    generated = utc_now()
    rows: list[dict[str, Any]] = []

    for cid in sorted(current_rows):
        current = current_rows[cid]
        previous = previous_rows.get(cid, {})
        diff = diff_fields(previous, current)
        before_r = previous.get("after_proxy_r")
        after_r = current.get("after_proxy_r")
        rows.append(
            {
                "row_id": f"MAIN-ORCH24-PENDING-LIFECYCLE-LTF-FIRST-TOUCH-REPAIR-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "generated_utc": generated,
                "candidate_id": cid,
                "symbol": current.get("symbol"),
                "side": current.get("side"),
                "asof_latest_candle_utc": current.get("asof_latest_candle_utc"),
                "before_proxy_r": before_r,
                "after_proxy_r": after_r,
                "proxy_r_delta": None
                if safe_float(before_r) is None or safe_float(after_r) is None
                else round(float(after_r) - float(before_r), 8),
                "before_score_status": previous.get("after_score_status"),
                "after_score_status": current.get("after_score_status"),
                "before_strategy_status": previous.get("after_strategy_status"),
                "after_strategy_status": current.get("after_strategy_status"),
                "before_outcome_status": previous.get("after_outcome_status"),
                "after_outcome_status": current.get("after_outcome_status"),
                "before_source_capture_statuses": capture_statuses(previous),
                "after_source_capture_statuses": capture_statuses(current),
                "before_source_capture_derivations": capture_derivations(previous),
                "after_source_capture_derivations": capture_derivations(current),
                "repaired_fields": diff["repaired_fields"],
                "first_touch_repair_fields": diff["first_touch_repair_fields"],
                "changed_source_fields": diff["changed_fields"],
                "source_repair_count": len(diff["repaired_fields"]),
                "first_touch_source_repair_count": len(diff["first_touch_repair_fields"]),
                "source_capture_complete": current.get("after_source_capture_complete"),
                "branch_decision": branch_decision(current, diff["first_touch_repair_fields"]),
                "implementation_decision": current.get("implementation_decision"),
                "exact_r": None,
                "safe_flags": SAFE_FLAGS,
                "no_live_behavior": True,
                "no_shadow_log_append": True,
            }
        )
    return rows


def mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def field_counts(rows: list[dict[str, Any]], key: str) -> Counter[str]:
    return Counter(field for row in rows for field in row.get(key, []))


def derived_missing_counts(rows: list[dict[str, Any]]) -> tuple[Counter[str], Counter[str], int, int]:
    derived: Counter[str] = Counter()
    missing: Counter[str] = Counter()
    derived_cells = 0
    missing_cells = 0
    for row in rows:
        statuses = row.get("after_source_capture_statuses")
        if not isinstance(statuses, dict) or not statuses:
            continue
        for field in PENDING_LIFECYCLE_CAPTURE_FIELDS:
            status = statuses.get(field)
            if isinstance(status, str) and status.startswith("DERIVED_"):
                derived[field] += 1
                derived_cells += 1
            if is_missing(status):
                missing[field] += 1
                missing_cells += 1
    return derived, missing, derived_cells, missing_cells


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    previous_summary = read_json(PREVIOUS_SUMMARY)
    before_values = [value for row in rows if (value := safe_float(row.get("before_proxy_r"))) is not None]
    after_values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    internal_rows = [row for row in rows if capture_statuses(row)]
    derived, missing, derived_cells, missing_cells = derived_missing_counts(rows)
    first_touch_repair_rows = [
        row for row in rows if row.get("first_touch_source_repair_count", 0) > 0
    ]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_PENDING_LIFECYCLE_LTF_FIRST_TOUCH_REPAIR",
        "claim_boundary": (
            "Current latest-row source-capture repair for pending lifecycle first-touch fields. "
            "Exact broker R is not opened, proxy R is unchanged, and no shadow log append is performed."
        ),
        "rows": len(rows),
        "candidate_rows": len({row.get("candidate_id") for row in rows}),
        "internal_pending_lifecycle_rows": len(internal_rows),
        "exact_r_rows": 0,
        "before_numeric_proxy_rows": len(before_values),
        "after_numeric_proxy_rows": len(after_values),
        "numeric_proxy_row_delta": len(after_values) - len(before_values),
        "before_proxy_r_mean": mean(before_values),
        "after_proxy_r_mean": mean(after_values),
        "before_proxy_r_sum": sum(before_values),
        "after_proxy_r_sum": sum(after_values),
        "proxy_r_sum_delta": sum(after_values) - sum(before_values),
        "previous_derived_source_field_cells": previous_summary.get("after_derived_source_field_cells"),
        "after_derived_source_field_cells": derived_cells,
        "derived_source_field_cell_delta": derived_cells
        - int(previous_summary.get("after_derived_source_field_cells", 0)),
        "previous_missing_source_field_cells": previous_summary.get("after_missing_source_field_cells"),
        "after_missing_source_field_cells": missing_cells,
        "missing_source_field_cell_delta": missing_cells
        - int(previous_summary.get("after_missing_source_field_cells", 0)),
        "after_capture_complete_rows": sum(
            1 for row in internal_rows if row.get("source_capture_complete") is True
        ),
        "source_repair_rows": sum(1 for row in rows if row.get("source_repair_count", 0) > 0),
        "first_touch_source_repair_rows": len(first_touch_repair_rows),
        "source_repair_field_counts": dict(field_counts(rows, "repaired_fields")),
        "first_touch_source_repair_field_counts": dict(
            field_counts(rows, "first_touch_repair_fields")
        ),
        "derived_field_counts": dict(derived),
        "missing_field_counts": dict(missing),
        "branch_decision_counts": dict(Counter(row.get("branch_decision") for row in rows)),
        "implementation_decision_counts": dict(
            Counter(row.get("implementation_decision") for row in rows)
        ),
        "plate_decision": (
            "PENDING_LIFECYCLE_LTF_FIRST_TOUCH_SOURCE_REPAIR_IMPLEMENTED_PROXY_R_UNCHANGED"
            if first_touch_repair_rows
            else "PENDING_LIFECYCLE_LTF_FIRST_TOUCH_SOURCE_REPAIR_NO_CURRENT_ROW_DELTA"
        ),
        "safe_flags": SAFE_FLAGS,
    }


def build_manifest() -> dict[str, Any]:
    inputs: dict[str, Path] = {
        **INPUTS,
        "previous_pending_lifecycle_source_derivation_ledger": PREVIOUS_LEDGER,
        "previous_pending_lifecycle_source_derivation_summary": PREVIOUS_SUMMARY,
        "live_mechanical_shadow_source": Path("src/research_infra/live_mechanical_shadow.py"),
        "live_mechanical_shadow_tests": Path("tests/test_live_mechanical_shadow.py"),
    }
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            str(path): {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in inputs.values()
        },
        "output_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in [OUTPUT_LEDGER, OUTPUT_SUMMARY]
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    rows = build_delta_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summarize(rows))
    write_json(OUTPUT_MANIFEST, build_manifest())
    print(json.dumps({"rows": len(rows), "summary": str(OUTPUT_SUMMARY)}, sort_keys=True))


if __name__ == "__main__":
    main()
