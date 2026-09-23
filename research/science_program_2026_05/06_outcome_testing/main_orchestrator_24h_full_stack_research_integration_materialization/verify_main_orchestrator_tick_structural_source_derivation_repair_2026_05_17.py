"""Verify tick-derived structural source repair materialization."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

INPUT_ACTION_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR_LEDGER_2026-05-17.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = (
    ROUTE_DIR / f"MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR_VERIFICATION_RESULT_{DATE}.json"
)

TARGET_SOURCE_DECISIONS = {
    "SOURCE_CAPTURE_REQUIRED_FOR_SWING_PROTECTED_STOP_SCORER",
    "SOURCE_CAPTURE_REQUIRED_FOR_STANDALONE_FVG_SCORER",
}

EXPECTED_ROWS = 3426
EXPECTED_TARGET_ROWS = 196
EXPECTED_BEFORE_PROXY_ROWS = 1386
EXPECTED_BEFORE_PROXY_SUM = 373.97201587
EXPECTED_AFTER_PROXY_ROWS = 1475
EXPECTED_AFTER_PROXY_SUM = 408.47201587
EXPECTED_PROXY_ROWS_DELTA = 89
EXPECTED_PROXY_SUM_DELTA = 34.5
EXPECTED_TARGET_STATUSES = {
    "KILLED_SWING_PROTECTED_STOP_NOT_CONFIRMED": 75,
    "SCORED_STANDALONE_FVG_POI_PROXY_CANDIDATE_PATH": 6,
    "SCORED_SWING_PROTECTED_STOP_PROXY_SHARED_CANDIDATE_PATH": 115,
}
EXPECTED_TARGET_DECISIONS = {
    "IMPLEMENT_DEFAULT_OFF_STANDALONE_FVG_POI_PATH_SCORER_NOW": 2,
    "IMPLEMENT_DEFAULT_OFF_STANDALONE_FVG_POI_SCORER_WITH_AMBIGUITY_EXCLUSION": 4,
    "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_STOP_PATH_SCORER_NOW": 87,
    "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_STOP_SCORER_WITH_AMBIGUITY_EXCLUSION": 28,
    "KILL_ROW_NOT_SWING_PROTECTED_STOP": 75,
}
EXPECTED_TARGET_ACTIONS = {"IMPLEMENT_DEFAULT_OFF": 121, "KILL": 75}
EXPECTED_TARGET_STRATEGIES = {
    "V2_STRUCT_FVG_MID_EDGE": 3,
    "V2_STRUCT_SWING_PROTECTED": 190,
    "V3_FVG_ONLY_RESCUE_RISK_BANK": 3,
}
EXPECTED_TARGET_SYMBOLS = {
    "GBPJPY": 10,
    "GBPUSD": 57,
    "NAS100": 42,
    "US30_cash": 12,
    "USDJPY": 3,
    "XAGUSD": 61,
    "XAUUSD": 11,
}
EXPECTED_CONSUMED_TICK_FILES = 113


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def proxy_stats(rows: list[dict[str, Any]]) -> tuple[int, float]:
    values = [safe_float(row.get("after_proxy_r")) for row in rows]
    numeric = [value for value in values if value is not None]
    return len(numeric), round(sum(numeric), 8)


def fail_result(failures: list[str]) -> dict[str, Any]:
    result = {"ok": False, "failures": failures}
    OUTPUT_VERIFICATION.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    failures: list[str] = []
    for path in [INPUT_ACTION_LEDGER, OUTPUT_LEDGER, OUTPUT_SUMMARY, OUTPUT_MANIFEST]:
        if not path.exists():
            failures.append(f"missing_path:{path}")
    if failures:
        print(json.dumps(fail_result(failures), sort_keys=True))
        return

    source_rows = read_jsonl(INPUT_ACTION_LEDGER)
    output_rows = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)

    if len(source_rows) != EXPECTED_ROWS:
        failures.append(f"unexpected_source_rows:{len(source_rows)}")
    if len(output_rows) != EXPECTED_ROWS:
        failures.append(f"unexpected_output_rows:{len(output_rows)}")
    if len(source_rows) != len(output_rows):
        failures.append("source_output_row_count_mismatch")

    source_ids = {str(row.get("row_id") or "") for row in source_rows}
    output_by_id = {str(row.get("row_id") or ""): row for row in output_rows}
    if source_ids != set(output_by_id):
        failures.append("row_id_set_changed")

    target_source = [
        row for row in source_rows if row.get("implementation_decision") in TARGET_SOURCE_DECISIONS
    ]
    if len(target_source) != EXPECTED_TARGET_ROWS:
        failures.append(f"unexpected_target_source_rows:{len(target_source)}")
    target_ids = {str(row.get("row_id") or "") for row in target_source}
    target_output = [output_by_id[row_id] for row_id in target_ids if row_id in output_by_id]

    target_statuses = Counter(row.get("after_strategy_status") for row in target_output)
    target_decisions = Counter(row.get("implementation_decision") for row in target_output)
    target_actions = Counter(row.get("action_class") for row in target_output)
    target_strategies = Counter(row.get("strategy_id") for row in target_output)
    target_symbols = Counter(row.get("symbol") for row in target_output)
    if dict(sorted(target_statuses.items())) != EXPECTED_TARGET_STATUSES:
        failures.append(f"target_status_mismatch:{dict(sorted(target_statuses.items()))}")
    if dict(sorted(target_decisions.items())) != EXPECTED_TARGET_DECISIONS:
        failures.append(f"target_decision_mismatch:{dict(sorted(target_decisions.items()))}")
    if dict(sorted(target_actions.items())) != EXPECTED_TARGET_ACTIONS:
        failures.append(f"target_action_mismatch:{dict(sorted(target_actions.items()))}")
    if dict(sorted(target_strategies.items())) != EXPECTED_TARGET_STRATEGIES:
        failures.append(f"target_strategy_mismatch:{dict(sorted(target_strategies.items()))}")
    if dict(sorted(target_symbols.items())) != EXPECTED_TARGET_SYMBOLS:
        failures.append(f"target_symbol_mismatch:{dict(sorted(target_symbols.items()))}")

    for row in target_output:
        row_id = str(row.get("row_id") or "")
        if row.get("safe_flags") != SAFE_FLAGS:
            failures.append(f"safe_flags_mismatch:{row_id}")
        if row.get("exact_r") is not None:
            failures.append(f"target_exact_r_not_null:{row_id}")
        if row.get("tick_structural_derivation_repair_status") in {None, "", "NOT_TARGET_ROW"}:
            failures.append(f"target_missing_repair_status:{row_id}")
        if not row.get("tick_structural_source_derivation_provenance"):
            failures.append(f"target_missing_tick_provenance:{row_id}")
        if row.get("action_class") == "IMPLEMENT_DEFAULT_OFF" and row.get("after_strategy_status", "").startswith("KILLED"):
            failures.append(f"killed_row_marked_implement:{row_id}")
        if row.get("action_class") == "KILL" and not row.get("after_strategy_status", "").startswith("KILLED"):
            failures.append(f"non_killed_row_marked_kill:{row_id}")

    output_source_repairs = [
        row for row in output_rows if str(row.get("implementation_decision") or "").startswith("SOURCE_CAPTURE_REQUIRED")
    ]
    if output_source_repairs:
        failures.append(f"source_capture_required_rows_remaining:{len(output_source_repairs)}")

    before_proxy_rows, before_proxy_sum = proxy_stats(source_rows)
    after_proxy_rows, after_proxy_sum = proxy_stats(output_rows)
    if before_proxy_rows != EXPECTED_BEFORE_PROXY_ROWS:
        failures.append(f"unexpected_before_proxy_rows:{before_proxy_rows}")
    if before_proxy_sum != EXPECTED_BEFORE_PROXY_SUM:
        failures.append(f"unexpected_before_proxy_sum:{before_proxy_sum}")
    if after_proxy_rows != EXPECTED_AFTER_PROXY_ROWS:
        failures.append(f"unexpected_after_proxy_rows:{after_proxy_rows}")
    if after_proxy_sum != EXPECTED_AFTER_PROXY_SUM:
        failures.append(f"unexpected_after_proxy_sum:{after_proxy_sum}")
    if after_proxy_rows - before_proxy_rows != EXPECTED_PROXY_ROWS_DELTA:
        failures.append(f"unexpected_proxy_rows_delta:{after_proxy_rows - before_proxy_rows}")
    if round(after_proxy_sum - before_proxy_sum, 8) != EXPECTED_PROXY_SUM_DELTA:
        failures.append(f"unexpected_proxy_sum_delta:{round(after_proxy_sum - before_proxy_sum, 8)}")

    if summary.get("rows") != EXPECTED_ROWS:
        failures.append("summary_rows_mismatch")
    if summary.get("target_rows_before") != EXPECTED_TARGET_ROWS:
        failures.append("summary_target_before_mismatch")
    if summary.get("target_rows_converted_out_of_source_repair") != EXPECTED_TARGET_ROWS:
        failures.append("summary_converted_target_mismatch")
    if summary.get("target_rows_remaining_source_repair") != 0:
        failures.append("summary_remaining_source_not_zero")
    if summary.get("source_repair_decisions_after") != {}:
        failures.append(f"summary_source_repair_after_not_empty:{summary.get('source_repair_decisions_after')}")
    if summary.get("consumed_tick_file_count") != EXPECTED_CONSUMED_TICK_FILES:
        failures.append(f"summary_tick_file_count_mismatch:{summary.get('consumed_tick_file_count')}")
    if summary.get("exact_r_rows") != 0:
        failures.append("summary_exact_r_not_zero")
    if summary.get("proxy_delta", {}).get("numeric_proxy_rows_delta") != EXPECTED_PROXY_ROWS_DELTA:
        failures.append("summary_proxy_rows_delta_mismatch")
    if summary.get("proxy_delta", {}).get("proxy_r_sum_delta") != EXPECTED_PROXY_SUM_DELTA:
        failures.append("summary_proxy_sum_delta_mismatch")
    if summary.get("target_statuses") != EXPECTED_TARGET_STATUSES:
        failures.append("summary_target_status_mismatch")
    if summary.get("target_implementation_decisions") != EXPECTED_TARGET_DECISIONS:
        failures.append("summary_target_decision_mismatch")

    manifest_outputs = {item.get("path"): item for item in manifest.get("outputs", [])}
    for output_path in [OUTPUT_LEDGER, OUTPUT_SUMMARY]:
        item = manifest_outputs.get(str(output_path))
        if not item:
            failures.append(f"manifest_missing_output:{output_path}")
            continue
        if item.get("sha256") != sha256_file(output_path):
            failures.append(f"manifest_hash_mismatch:{output_path}")

    result = {
        "ok": not failures,
        "failures": failures,
        "checked_rows": len(output_rows),
        "target_rows": len(target_output),
        "before_proxy_rows": before_proxy_rows,
        "before_proxy_sum": before_proxy_sum,
        "after_proxy_rows": after_proxy_rows,
        "after_proxy_sum": after_proxy_sum,
        "proxy_rows_delta": after_proxy_rows - before_proxy_rows,
        "proxy_sum_delta": round(after_proxy_sum - before_proxy_sum, 8),
        "consumed_tick_file_count": summary.get("consumed_tick_file_count"),
    }
    OUTPUT_VERIFICATION.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
