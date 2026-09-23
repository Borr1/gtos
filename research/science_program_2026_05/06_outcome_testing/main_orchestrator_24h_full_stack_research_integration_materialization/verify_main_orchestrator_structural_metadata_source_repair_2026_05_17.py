"""Verify structural metadata source repair materialization."""

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

INPUT_ACTION_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_FVG_OB_BUCKET_REPAIR_LEDGER_2026-05-17.jsonl"
)
INPUT_STRUCTURAL_METADATA = Path("shadow_logs/live_structural_strategy_metadata.jsonl")
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = (
    ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_METADATA_REPAIR_VERIFICATION_RESULT_{DATE}.json"
)

TARGET_SOURCE_DECISION = "SOURCE_CAPTURE_REQUIRED_FOR_STRUCTURAL_LOCK_SCORER"
IMPLEMENT_NUMERIC_DECISION = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_SHARED_PATH_PROXY_SCORER_NOW"
IMPLEMENT_AMBIGUITY_DECISION = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_SCORER_WITH_AMBIGUITY_EXCLUSION"
SCORED_STATUS = "SCORED_STRUCTURAL_LOCK_METADATA_PROXY_SHARED_CANDIDATE_PATH"

EXPECTED_ROWS = 3426
EXPECTED_BEFORE_PROXY_ROWS = 862
EXPECTED_BEFORE_PROXY_SUM = 193.97201587
EXPECTED_TARGET_ROWS = 760
EXPECTED_REPAIRED_CANDIDATES = 190
EXPECTED_NUMERIC_TARGET_ROWS = 524
EXPECTED_TARGET_PROXY_SUM = 180.0
EXPECTED_AFTER_PROXY_ROWS = 1386
EXPECTED_AFTER_PROXY_SUM = 373.97201587
EXPECTED_REMAINING_SOURCE_REPAIR_DECISIONS = {
    "SOURCE_CAPTURE_REQUIRED_FOR_STANDALONE_FVG_SCORER": 6,
    "SOURCE_CAPTURE_REQUIRED_FOR_SWING_PROTECTED_STOP_SCORER": 190,
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
    for path in [
        INPUT_ACTION_LEDGER,
        INPUT_STRUCTURAL_METADATA,
        OUTPUT_LEDGER,
        OUTPUT_SUMMARY,
        OUTPUT_MANIFEST,
    ]:
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
        failures.append(f"row_count_mismatch:{len(source_rows)}!={len(output_rows)}")

    source_ids = {str(row.get("row_id") or "") for row in source_rows}
    output_by_id = {str(row.get("row_id") or ""): row for row in output_rows}
    if source_ids != set(output_by_id):
        failures.append("row_id_set_changed")

    target_source = [
        row for row in source_rows if row.get("implementation_decision") == TARGET_SOURCE_DECISION
    ]
    if len(target_source) != EXPECTED_TARGET_ROWS:
        failures.append(f"unexpected_target_source_rows:{len(target_source)}")
    target_ids = {str(row.get("row_id") or "") for row in target_source}
    target_output = [output_by_id[row_id] for row_id in target_ids if row_id in output_by_id]
    target_candidates = {str(row.get("candidate_id") or "") for row in target_output}
    if len(target_candidates) != EXPECTED_REPAIRED_CANDIDATES:
        failures.append(f"unexpected_target_candidate_count:{len(target_candidates)}")

    for row in target_output:
        row_id = str(row.get("row_id") or "")
        if row.get("action_class") != "IMPLEMENT_DEFAULT_OFF":
            failures.append(f"target_action_not_implement_default_off:{row_id}")
        if row.get("after_strategy_status") != SCORED_STATUS:
            failures.append(f"target_not_scored:{row_id}")
        if row.get("structural_metadata_repair_status") not in {
            "REPAIRED_STRUCTURAL_METADATA_SHARED_PATH_PROXY",
            "REPAIRED_STRUCTURAL_METADATA_SHARED_PATH_AMBIGUITY_EXCLUDED",
        }:
            failures.append(f"target_bad_repair_status:{row_id}")
        if not row.get("structural_metadata_created_at_utc"):
            failures.append(f"target_missing_metadata_created_at:{row_id}")
        if not row.get("cost_geometry_source_status"):
            failures.append(f"target_missing_cost_geometry_status:{row_id}")
        numeric = safe_float(row.get("after_proxy_r")) is not None
        expected_decision = IMPLEMENT_NUMERIC_DECISION if numeric else IMPLEMENT_AMBIGUITY_DECISION
        if row.get("implementation_decision") != expected_decision:
            failures.append(f"target_decision_mismatch:{row_id}")

    target_numeric_values = [
        safe_float(row.get("after_proxy_r"))
        for row in target_output
        if safe_float(row.get("after_proxy_r")) is not None
    ]
    target_proxy_sum = round(sum(value for value in target_numeric_values if value is not None), 8)
    if len(target_numeric_values) != EXPECTED_NUMERIC_TARGET_ROWS:
        failures.append(f"unexpected_numeric_target_rows:{len(target_numeric_values)}")
    if target_proxy_sum != EXPECTED_TARGET_PROXY_SUM:
        failures.append(f"unexpected_target_proxy_sum:{target_proxy_sum}")

    source_decisions = Counter(row.get("implementation_decision") for row in source_rows)
    output_decisions = Counter(row.get("implementation_decision") for row in output_rows)
    source_actions = Counter(row.get("action_class") for row in source_rows)
    output_actions = Counter(row.get("action_class") for row in output_rows)
    if output_decisions.get(TARGET_SOURCE_DECISION, 0) != 0:
        failures.append("structural_source_repair_rows_remaining")
    target_decisions = Counter(row.get("implementation_decision") for row in target_output)
    if target_decisions.get(IMPLEMENT_NUMERIC_DECISION, 0) != EXPECTED_NUMERIC_TARGET_ROWS:
        failures.append("numeric_target_implementation_count_mismatch")
    if (
        target_decisions.get(IMPLEMENT_AMBIGUITY_DECISION, 0)
        != EXPECTED_TARGET_ROWS - EXPECTED_NUMERIC_TARGET_ROWS
    ):
        failures.append("ambiguity_target_implementation_count_mismatch")

    remaining_source_repair = {
        str(decision): count
        for decision, count in sorted(output_decisions.items())
        if str(decision).startswith("SOURCE_CAPTURE_REQUIRED")
        or str(decision).startswith("SOURCE_REPAIR_REQUIRED")
    }
    if remaining_source_repair != EXPECTED_REMAINING_SOURCE_REPAIR_DECISIONS:
        failures.append(f"remaining_source_repair_mismatch:{remaining_source_repair}")

    if output_actions.get("SOURCE_REPAIR", 0) != 196:
        failures.append(f"unexpected_source_repair_action_count:{output_actions.get('SOURCE_REPAIR', 0)}")
    if output_actions.get("IMPLEMENT_DEFAULT_OFF", 0) - source_actions.get("IMPLEMENT_DEFAULT_OFF", 0) != 760:
        failures.append("implement_default_off_action_delta_mismatch")
    if output_actions.get("SOURCE_REPAIR", 0) - source_actions.get("SOURCE_REPAIR", 0) != -760:
        failures.append("source_repair_action_delta_mismatch")

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

    if summary.get("rows") != len(output_rows):
        failures.append("summary_rows_mismatch")
    if summary.get("structural_source_repair_rows_before") != EXPECTED_TARGET_ROWS:
        failures.append("summary_structural_before_mismatch")
    if summary.get("structural_source_repair_rows_after") != 0:
        failures.append("summary_structural_after_not_zero")
    if summary.get("remaining_source_repair_rows_after") != 196:
        failures.append("summary_remaining_source_repair_mismatch")
    if summary.get("remaining_source_repair_decision_counts") != EXPECTED_REMAINING_SOURCE_REPAIR_DECISIONS:
        failures.append("summary_remaining_source_repair_decisions_mismatch")
    if summary.get("repaired_action_rows") != EXPECTED_TARGET_ROWS:
        failures.append("summary_repaired_rows_mismatch")
    if summary.get("repair_decision_counts") != {
        IMPLEMENT_AMBIGUITY_DECISION: EXPECTED_TARGET_ROWS - EXPECTED_NUMERIC_TARGET_ROWS,
        IMPLEMENT_NUMERIC_DECISION: EXPECTED_NUMERIC_TARGET_ROWS,
    }:
        failures.append("summary_repair_decision_counts_mismatch")
    if summary.get("repaired_candidate_ids") != EXPECTED_REPAIRED_CANDIDATES:
        failures.append("summary_repaired_candidate_ids_mismatch")
    if summary.get("numeric_proxy_row_delta") != EXPECTED_NUMERIC_TARGET_ROWS:
        failures.append("summary_numeric_proxy_delta_mismatch")
    if summary.get("proxy_r_sum_delta") != EXPECTED_TARGET_PROXY_SUM:
        failures.append("summary_proxy_sum_delta_mismatch")
    if summary.get("proxy_before", {}).get("numeric_proxy_rows") != EXPECTED_BEFORE_PROXY_ROWS:
        failures.append("summary_before_proxy_rows_mismatch")
    if summary.get("proxy_before", {}).get("proxy_r_sum") != EXPECTED_BEFORE_PROXY_SUM:
        failures.append("summary_before_proxy_sum_mismatch")
    if summary.get("proxy_after", {}).get("numeric_proxy_rows") != EXPECTED_AFTER_PROXY_ROWS:
        failures.append("summary_after_proxy_rows_mismatch")
    if summary.get("proxy_after", {}).get("proxy_r_sum") != EXPECTED_AFTER_PROXY_SUM:
        failures.append("summary_after_proxy_sum_mismatch")
    if summary.get("safe_flags") != SAFE_FLAGS:
        failures.append("summary_safe_flags_mismatch")

    if source_decisions.get(TARGET_SOURCE_DECISION, 0) != EXPECTED_TARGET_ROWS:
        failures.append("source_target_decision_count_mismatch")

    for name, meta in manifest.get("outputs", {}).items():
        path = Path(meta.get("path", ""))
        if not path.exists():
            failures.append(f"manifest_output_missing:{name}")
        elif sha256_file(path) != meta.get("sha256"):
            failures.append(f"manifest_output_hash_mismatch:{name}")

    result = {
        "ok": not failures,
        "failures": failures,
        "source_rows": len(source_rows),
        "output_rows": len(output_rows),
        "structural_source_repair_rows_before": len(target_source),
        "structural_source_repair_rows_after": output_decisions.get(TARGET_SOURCE_DECISION, 0),
        "remaining_source_repair_rows_after": output_actions.get("SOURCE_REPAIR", 0),
        "repaired_candidate_ids": len(target_candidates),
        "numeric_proxy_row_delta": after_proxy_rows - before_proxy_rows,
        "proxy_r_sum_delta": round(after_proxy_sum - before_proxy_sum, 8),
        "safe_flags": SAFE_FLAGS,
    }
    OUTPUT_VERIFICATION.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
