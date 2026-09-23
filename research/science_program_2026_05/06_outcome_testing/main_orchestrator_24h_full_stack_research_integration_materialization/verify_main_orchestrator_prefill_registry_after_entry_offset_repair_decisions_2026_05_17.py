"""Verify prefill registry metadata after entry-offset repair decisions."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_ENTRY_REPAIR_LEDGER_{DATE}.jsonl"
)
SUMMARY = (
    ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_ENTRY_REPAIR_SUMMARY_{DATE}.json"
)
MANIFEST = (
    ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_ENTRY_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
)
RESULT = (
    ROUTE_DIR / f"MAIN_ORCH24_PREFILL_REGISTRY_ENTRY_REPAIR_VERIFY_RESULT_{DATE}.json"
)

EXPECTED_BRANCH_DECISION = "PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION_WITH_KILL_REDESIGN_SPLIT"
EXPECTED_IMPLEMENTATION = (
    "KEEP_PREFILL_KILL_REDESIGN_SPLIT_AND_DESIGN_FAR_MISS_RETEST_CONTROL_FOR_10_ROWS"
)
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


def close_enough(left: Any, right: float, tolerance: float = 1e-8) -> bool:
    try:
        return math.isclose(float(left), right, abs_tol=tolerance, rel_tol=0.0)
    except (TypeError, ValueError):
        return False


def main() -> None:
    failures: list[str] = []
    for path in (LEDGER, SUMMARY, MANIFEST):
        if not path.exists():
            failures.append(f"missing_output:{path.name}")

    rows = read_jsonl(LEDGER) if LEDGER.exists() else []
    summary = read_json(SUMMARY) if SUMMARY.exists() else {}
    manifest = read_json(MANIFEST) if MANIFEST.exists() else {}
    row = rows[0] if rows else {}

    if len(rows) != 1 or summary.get("rows") != 1:
        failures.append(f"expected_one_row_got_ledger_{len(rows)}_summary_{summary.get('rows')}")
    if row.get("strategy_id") != "PREFILL_DELIVERY_REVERSAL_PATH":
        failures.append(f"unexpected_strategy_id:{row.get('strategy_id')}")
    if row.get("branch_decision") != EXPECTED_BRANCH_DECISION:
        failures.append(f"branch_decision_stale:{row.get('branch_decision')}")
    if row.get("implementation_candidate") != EXPECTED_IMPLEMENTATION:
        failures.append("implementation_candidate_stale")
    if row.get("stale_metadata_tokens"):
        failures.append(f"stale_tokens_remain:{row.get('stale_metadata_tokens')}")

    evidence = str(row.get("decision_evidence") or "")
    required_evidence = [
        "MAIN_ORCH24_PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION",
        "84 kill / 10 redesign",
        "95->97",
        "+8.66977687R",
        "exact-R 0",
    ]
    for token in required_evidence:
        if token not in evidence:
            failures.append(f"missing_evidence_token:{token}")

    expected_counts = {
        "action_rows": 3426,
        "prefill_target_rows": 274,
        "linked_entry_offset_before_numeric_proxy_rows": 95,
        "linked_entry_offset_after_numeric_proxy_rows": 97,
        "linked_entry_offset_numeric_proxy_row_delta": 2,
        "prefill_metadata_numeric_proxy_rows": 0,
        "prefill_metadata_proxy_r_sum": 0.0,
        "exact_r_rows": 0,
    }
    for field, expected in expected_counts.items():
        if row.get(field) != expected:
            failures.append(f"ledger_{field}_expected_{expected}_got_{row.get(field)}")
        if summary.get(field) != expected:
            failures.append(f"summary_{field}_expected_{expected}_got_{summary.get(field)}")
    if row.get("target_action_class_counts_after") != EXPECTED_TARGET_ACTIONS:
        failures.append(f"ledger_target_actions_mismatch:{row.get('target_action_class_counts_after')}")
    if summary.get("target_action_class_counts_after") != EXPECTED_TARGET_ACTIONS:
        failures.append(f"summary_target_actions_mismatch:{summary.get('target_action_class_counts_after')}")
    if row.get("action_class_delta_vs_previous") != EXPECTED_ACTION_DELTA:
        failures.append(f"ledger_action_delta_mismatch:{row.get('action_class_delta_vs_previous')}")
    if summary.get("action_class_delta_vs_previous") != EXPECTED_ACTION_DELTA:
        failures.append(f"summary_action_delta_mismatch:{summary.get('action_class_delta_vs_previous')}")
    if not close_enough(row.get("linked_entry_offset_after_proxy_r_sum"), 8.66977687):
        failures.append("ledger_linked_proxy_sum_mismatch")
    if not close_enough(summary.get("linked_entry_offset_after_proxy_r_sum"), 8.66977687):
        failures.append("summary_linked_proxy_sum_mismatch")
    if not close_enough(row.get("linked_entry_offset_proxy_r_sum_delta"), 0.0):
        failures.append("ledger_linked_proxy_delta_nonzero")
    if not close_enough(summary.get("linked_entry_offset_proxy_r_sum_delta"), 0.0):
        failures.append("summary_linked_proxy_delta_nonzero")
    if summary.get("metadata_rows_with_stale_tokens") != 0:
        failures.append("summary_reports_stale_tokens")
    if row.get("boundary_fields", {}).get("broker_runtime_change_status") is not False:
        failures.append("ledger_broker_runtime_change_status_flag_changed")

    output_hashes = manifest.get("outputs", {})
    if output_hashes.get("ledger", {}).get("sha256") != sha256_file(LEDGER):
        failures.append("manifest_ledger_hash_mismatch")
    if output_hashes.get("summary", {}).get("sha256") != sha256_file(SUMMARY):
        failures.append("manifest_summary_hash_mismatch")
    for name, payload in manifest.get("inputs", {}).items():
        if not payload.get("exists"):
            failures.append(f"manifest_input_missing:{name}")

    result = {
        "ok": not failures,
        "failures": failures,
        "rows": len(rows),
        "metadata_rows_with_stale_tokens": summary.get("metadata_rows_with_stale_tokens"),
        "prefill_target_rows": summary.get("prefill_target_rows"),
        "target_action_class_counts_after": summary.get("target_action_class_counts_after"),
        "action_class_delta_vs_previous": summary.get("action_class_delta_vs_previous"),
        "linked_entry_offset_after_numeric_proxy_rows": summary.get(
            "linked_entry_offset_after_numeric_proxy_rows"
        ),
        "linked_entry_offset_after_proxy_r_sum": summary.get(
            "linked_entry_offset_after_proxy_r_sum"
        ),
        "exact_r_rows": summary.get("exact_r_rows"),
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
