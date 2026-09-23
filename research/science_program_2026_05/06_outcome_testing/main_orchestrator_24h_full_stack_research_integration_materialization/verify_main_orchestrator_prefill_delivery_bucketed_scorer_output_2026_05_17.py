"""Verify bucketed prefill delivery scorer/action output."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = ROUTE_DIR / "MAIN_ORCH24_PREFILL_DELIVERY_BUCKETED_SCORER_OUTPUT_LEDGER_2026-05-17.jsonl"
SUMMARY = ROUTE_DIR / "MAIN_ORCH24_PREFILL_DELIVERY_BUCKETED_SCORER_OUTPUT_SUMMARY_2026-05-17.json"
MANIFEST = (
    ROUTE_DIR / "MAIN_ORCH24_PREFILL_DELIVERY_BUCKETED_SCORER_OUTPUT_OUTPUT_MANIFEST_2026-05-17.json"
)
RESULT = (
    ROUTE_DIR / "MAIN_ORCH24_PREFILL_DELIVERY_BUCKETED_SCORER_OUTPUT_VERIFICATION_RESULT_2026-05-17.json"
)

EXPECTED_BUCKET_COUNTS = {
    "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE": 94,
    "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE": 3,
    "NOT_A_NO_FILL_TP1_ENTRY_REDESIGN_ROW": 177,
}
EXPECTED_BRANCH_COUNTS = {
    "KEEP_CURRENT_ENTRY_MODEL_NOT_IN_PREFILL_REDESIGN_DENOMINATOR": 177,
    "REDESIGN_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL": 94,
    "REDESIGN_WITH_ENTRY_OFFSET_050R_NEAR_MISS_CHALLENGER": 3,
}
EXPECTED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 3,
    "KEEP": 177,
    "REDESIGN": 94,
}
EXPECTED_IMPL_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF_PREFILL_NEAR_MISS_ENTRY_OFFSET_050R_CHALLENGER": 3,
    "KEEP_CURRENT_ENTRY_MODEL_NOT_IN_PREFILL_REDESIGN_DENOMINATOR": 177,
    "REDESIGN_PREFILL_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL": 94,
}
EXPECTED_LINKED_ACTION_COUNTS = {
    "IMPLEMENT_DEFAULT_OFF": 3,
    "KILL": 82,
    "REDESIGN": 10,
    "SOURCE_REPAIR": 2,
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
    rows = read_jsonl(LEDGER)
    summary = read_json(SUMMARY)
    manifest = read_json(MANIFEST)
    prefill_rows = [row for row in rows if row.get("strategy_id") == "PREFILL_DELIVERY_REVERSAL_PATH"]

    if summary.get("rows") != 3426 or len(rows) != 3426:
        failures.append(f"expected 3426 action rows, got summary={summary.get('rows')} ledger={len(rows)}")
    if summary.get("prefill_target_rows") != 274 or len(prefill_rows) != 274:
        failures.append(
            f"expected 274 prefill rows, got summary={summary.get('prefill_target_rows')} ledger={len(prefill_rows)}"
        )
    if summary.get("prefill_missing_candidate_or_path_inputs") != 0:
        failures.append("prefill scorer had missing candidate/path inputs")
    if summary.get("generic_no_scorer_rows_before") != 274:
        failures.append(
            f"generic rows before expected 274, got {summary.get('generic_no_scorer_rows_before')}"
        )
    if summary.get("generic_no_scorer_rows_after") != 0:
        failures.append(
            f"generic rows after expected 0, got {summary.get('generic_no_scorer_rows_after')}"
        )

    if summary.get("entry_retest_redesign_bucket_counts") != EXPECTED_BUCKET_COUNTS:
        failures.append(
            f"bucket counts mismatch: {summary.get('entry_retest_redesign_bucket_counts')}"
        )
    if summary.get("prefill_branch_decision_counts") != EXPECTED_BRANCH_COUNTS:
        failures.append(
            f"branch counts mismatch: {summary.get('prefill_branch_decision_counts')}"
        )
    if summary.get("prefill_target_action_class_counts") != EXPECTED_ACTION_COUNTS:
        failures.append(
            f"target action counts mismatch: {summary.get('prefill_target_action_class_counts')}"
        )
    if summary.get("prefill_target_implementation_decision_counts") != EXPECTED_IMPL_COUNTS:
        failures.append(
            f"implementation counts mismatch: {summary.get('prefill_target_implementation_decision_counts')}"
        )

    stale_prefill_rows = [
        row
        for row in prefill_rows
        if row.get("implementation_decision") == "REDESIGN_PREFILL_DELIVERY_REVERSAL_PATH_SCORER"
        or row.get("branch_decision") == "REDESIGN_REQUIRED_NO_SCORER"
        or row.get("scoring_boundary") == "NO_SHARED_ENTRY_PROXY_FOR_PREFILL_DELIVERY_REVERSAL_PATH"
    ]
    if stale_prefill_rows:
        failures.append(f"stale generic prefill rows remain: {len(stale_prefill_rows)}")
    if any(row.get("after_proxy_r") is not None for row in prefill_rows):
        failures.append("prefill metadata rows duplicated proxy R")
    if summary.get("prefill_metadata_numeric_proxy_rows") != 0:
        failures.append("summary reports prefill metadata proxy rows")
    if not close_enough(summary.get("prefill_metadata_proxy_r_sum"), 0.0):
        failures.append("summary reports nonzero prefill metadata proxy sum")
    if summary.get("numeric_proxy_row_delta") != 0:
        failures.append(f"proxy row delta expected 0, got {summary.get('numeric_proxy_row_delta')}")
    if not close_enough(summary.get("proxy_r_sum_delta"), 0.0):
        failures.append(f"proxy R delta expected 0, got {summary.get('proxy_r_sum_delta')}")
    if summary.get("exact_r_rows") != 0:
        failures.append("exact-R rows opened")
    if summary.get("action_class_delta_vs_previous") != {
        "IMPLEMENT_DEFAULT_OFF": 3,
        "KEEP": 177,
        "REDESIGN": -180,
    }:
        failures.append(
            f"unexpected action delta {summary.get('action_class_delta_vs_previous')}"
        )

    if summary.get("linked_entry_offset_no_fill_rows") != 97:
        failures.append("linked entry-offset no-fill row count is not 97")
    if summary.get("linked_entry_offset_numeric_proxy_rows") != 95:
        failures.append("linked entry-offset numeric proxy row count is not 95")
    if not close_enough(summary.get("linked_entry_offset_proxy_r_sum"), 8.66977687):
        failures.append(
            f"linked entry-offset proxy sum mismatch {summary.get('linked_entry_offset_proxy_r_sum')}"
        )
    if summary.get("linked_entry_offset_action_class_counts_on_no_fill") != EXPECTED_LINKED_ACTION_COUNTS:
        failures.append(
            "linked entry-offset no-fill action counts changed: "
            f"{summary.get('linked_entry_offset_action_class_counts_on_no_fill')}"
        )

    if not all(row.get("safe_flags", {}).get("live_effect") is False for row in prefill_rows):
        failures.append("prefill row live_effect safe flag changed")
    if not all(row.get("no_shadow_log_append") is True for row in prefill_rows):
        failures.append("prefill row shadow-log append flag changed")

    manifest_counts = manifest.get("summary_counts", {})
    if manifest_counts.get("generic_no_scorer_rows_after") != 0:
        failures.append("manifest reports stale generic rows")
    if manifest_counts.get("entry_retest_redesign_bucket_counts") != EXPECTED_BUCKET_COUNTS:
        failures.append("manifest bucket counts mismatch")
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
        "prefill_target_rows": len(prefill_rows),
        "generic_no_scorer_rows_after": summary.get("generic_no_scorer_rows_after"),
        "entry_retest_redesign_bucket_counts": summary.get(
            "entry_retest_redesign_bucket_counts"
        ),
        "numeric_proxy_row_delta": summary.get("numeric_proxy_row_delta"),
        "proxy_r_sum_delta": summary.get("proxy_r_sum_delta"),
        "exact_r_rows": summary.get("exact_r_rows"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
