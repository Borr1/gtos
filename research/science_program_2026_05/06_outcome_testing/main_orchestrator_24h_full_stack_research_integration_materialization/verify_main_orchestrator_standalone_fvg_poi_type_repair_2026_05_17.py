"""Verify standalone-FVG selected-POI-type action repair."""

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
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_SRC_ENTRY_M15_REPAIRS_LEDGER_2026-05-16.jsonl"
)
INPUT_STRATEGY_FOLLOW = Path("shadow_logs/strategy_follow_candidates.jsonl")
INPUT_FVG_OB = Path("shadow_logs/fvg_ob_confluence.jsonl")
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STANDALONE_FVG_POI_TYPE_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STANDALONE_FVG_POI_TYPE_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STANDALONE_FVG_POI_TYPE_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STANDALONE_FVG_POI_TYPE_REPAIR_VERIFICATION_RESULT_{DATE}.json"

TARGET_SOURCE_DECISION = "SOURCE_CAPTURE_REQUIRED_FOR_STANDALONE_FVG_SCORER"
REPAIRED_KILL_DECISION = (
    "KILL_STANDALONE_FVG_SCORER_FOR_NON_FVG_POI_ROWS_DECISION_TIME_POI_TYPE_REPAIR"
)


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


def parse_utc(value: Any) -> str:
    return str(value or "")


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        if parse_utc(row.get("created_at_utc")) >= parse_utc(latest.get(cid, {}).get("created_at_utc")):
            latest[cid] = row
    return latest


def selected_poi_type(
    candidate_id: str,
    strategy_follow: dict[str, dict[str, Any]],
    fvg_ob: dict[str, dict[str, Any]],
) -> tuple[str | None, str]:
    candidate = strategy_follow.get(candidate_id) or {}
    h1_setup = candidate.get("h1_setup")
    if isinstance(h1_setup, dict):
        value = str(h1_setup.get("poi_type") or "").upper()
        if value:
            return value, "shadow_logs/strategy_follow_candidates.jsonl:h1_setup.poi_type"
    row = fvg_ob.get(candidate_id) or {}
    fields = row.get("decision_time_fields")
    if isinstance(fields, dict):
        value = str(fields.get("h1_poi_type") or "").upper()
        if value:
            return value, "shadow_logs/fvg_ob_confluence.jsonl:decision_time_fields.h1_poi_type"
    return None, "NO_DECISION_TIME_SELECTED_POI_TYPE_SOURCE_FOUND"


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def proxy_stats(rows: list[dict[str, Any]]) -> tuple[int, float]:
    values = [safe_float(row.get("after_proxy_r")) for row in rows]
    numeric = [value for value in values if value is not None]
    return len(numeric), round(sum(numeric), 8)


def main() -> None:
    failures: list[str] = []
    for path in [INPUT_ACTION_LEDGER, INPUT_STRATEGY_FOLLOW, INPUT_FVG_OB, OUTPUT_LEDGER, OUTPUT_SUMMARY, OUTPUT_MANIFEST]:
        if not path.exists():
            failures.append(f"missing_path:{path}")

    if failures:
        result = {"ok": False, "failures": failures}
        OUTPUT_VERIFICATION.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
        return

    source_rows = read_jsonl(INPUT_ACTION_LEDGER)
    output_rows = read_jsonl(OUTPUT_LEDGER)
    summary = read_json(OUTPUT_SUMMARY)
    manifest = read_json(OUTPUT_MANIFEST)
    strategy_follow = latest_by_candidate(read_jsonl(INPUT_STRATEGY_FOLLOW))
    fvg_ob = latest_by_candidate(read_jsonl(INPUT_FVG_OB))

    if len(output_rows) != len(source_rows):
        failures.append(f"row_count_mismatch:{len(source_rows)}!={len(output_rows)}")

    source_by_row_id = {str(row.get("row_id") or ""): row for row in source_rows}
    output_by_row_id = {str(row.get("row_id") or ""): row for row in output_rows}
    if set(source_by_row_id) != set(output_by_row_id):
        failures.append("row_id_set_changed")

    expected_repaired_row_ids: set[str] = set()
    expected_true_fvg_row_ids: set[str] = set()
    expected_missing_row_ids: set[str] = set()
    expected_source_counts: Counter[str] = Counter()
    expected_poi_counts: Counter[str] = Counter()
    for row in source_rows:
        if row.get("implementation_decision") != TARGET_SOURCE_DECISION:
            continue
        poi_type, source = selected_poi_type(str(row.get("candidate_id") or ""), strategy_follow, fvg_ob)
        expected_poi_counts[poi_type or "MISSING"] += 1
        row_id = str(row.get("row_id") or "")
        if poi_type and poi_type != "FVG":
            expected_repaired_row_ids.add(row_id)
            expected_source_counts[source] += 1
        elif poi_type == "FVG":
            expected_true_fvg_row_ids.add(row_id)
        else:
            expected_missing_row_ids.add(row_id)

    actual_repaired = {
        str(row.get("row_id") or "")
        for row in output_rows
        if row.get("standalone_fvg_poi_type_repair_status") == "REPAIRED_KILL_NON_FVG_SELECTED_POI"
    }
    if actual_repaired != expected_repaired_row_ids:
        failures.append(
            f"repaired_row_id_mismatch:expected={len(expected_repaired_row_ids)} actual={len(actual_repaired)}"
        )

    for row_id in expected_repaired_row_ids:
        row = output_by_row_id[row_id]
        if row.get("action_class") != "KILL":
            failures.append(f"repaired_not_kill:{row_id}")
        if row.get("implementation_decision") != REPAIRED_KILL_DECISION:
            failures.append(f"repaired_decision_mismatch:{row_id}")
        if row.get("branch_decision") != "KILL_ROW_NOT_STANDALONE_FVG_POI":
            failures.append(f"repaired_branch_mismatch:{row_id}")
        if row.get("after_proxy_r") is not None:
            failures.append(f"repaired_row_opened_proxy_r:{row_id}")

    for row_id in expected_true_fvg_row_ids:
        row = output_by_row_id[row_id]
        if row.get("implementation_decision") != TARGET_SOURCE_DECISION:
            failures.append(f"true_fvg_row_not_source_bound:{row_id}")

    before_proxy_rows, before_proxy_sum = proxy_stats(source_rows)
    after_proxy_rows, after_proxy_sum = proxy_stats(output_rows)
    if (before_proxy_rows, before_proxy_sum) != (after_proxy_rows, after_proxy_sum):
        failures.append(
            f"proxy_changed:before=({before_proxy_rows},{before_proxy_sum}) after=({after_proxy_rows},{after_proxy_sum})"
        )

    output_decisions = Counter(row.get("implementation_decision") for row in output_rows)
    if output_decisions.get(TARGET_SOURCE_DECISION, 0) != len(expected_true_fvg_row_ids) + len(expected_missing_row_ids):
        failures.append("remaining_standalone_fvg_source_repair_count_mismatch")
    if output_decisions.get(REPAIRED_KILL_DECISION, 0) != len(expected_repaired_row_ids):
        failures.append("repaired_kill_decision_count_mismatch")

    if summary.get("rows") != len(output_rows):
        failures.append("summary_rows_mismatch")
    if summary.get("repaired_action_rows") != len(expected_repaired_row_ids):
        failures.append("summary_repaired_rows_mismatch")
    if summary.get("standalone_fvg_source_repair_rows_after") != output_decisions.get(TARGET_SOURCE_DECISION, 0):
        failures.append("summary_remaining_source_repair_mismatch")
    if summary.get("selected_poi_type_counts_on_target_rows") != dict(sorted(expected_poi_counts.items())):
        failures.append("summary_poi_counts_mismatch")
    if summary.get("repair_source_counts") != dict(sorted(expected_source_counts.items())):
        failures.append("summary_repair_source_counts_mismatch")
    if summary.get("numeric_proxy_row_delta") != 0 or summary.get("proxy_r_sum_delta") != 0.0:
        failures.append("summary_proxy_delta_not_zero")
    if summary.get("safe_flags") != SAFE_FLAGS:
        failures.append("summary_safe_flags_mismatch")

    for name, meta in manifest.get("outputs", {}).items():
        path = Path(meta.get("path", ""))
        if not path.exists():
            failures.append(f"manifest_output_missing:{name}")
        elif sha256_file(path) != meta.get("sha256"):
            failures.append(f"manifest_output_hash_mismatch:{name}")
    if manifest.get("summary_counts", {}).get("repaired_action_rows") != len(expected_repaired_row_ids):
        failures.append("manifest_repaired_rows_mismatch")

    result = {
        "ok": not failures,
        "failures": failures,
        "source_rows": len(source_rows),
        "output_rows": len(output_rows),
        "expected_repaired_rows": len(expected_repaired_row_ids),
        "remaining_standalone_fvg_source_repair_rows": output_decisions.get(TARGET_SOURCE_DECISION, 0),
        "numeric_proxy_rows": after_proxy_rows,
        "proxy_r_sum": after_proxy_sum,
        "safe_flags": SAFE_FLAGS,
    }
    OUTPUT_VERIFICATION.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
