"""Verify FVG/OB confluence bucket action repair."""

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
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_STANDALONE_FVG_POI_TYPE_REPAIR_LEDGER_2026-05-17.jsonl"
)
INPUT_FVG_OB = Path("shadow_logs/fvg_ob_confluence.jsonl")
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_BUCKET_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_BUCKET_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_BUCKET_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
OUTPUT_VERIFICATION = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_BUCKET_REPAIR_VERIFICATION_RESULT_{DATE}.json"

TARGET_SOURCE_DECISION = "SOURCE_CAPTURE_REQUIRED_FOR_FVG_OB_CONFLUENCE_SCORER"
KILL_DECISION = "KILL_FVG_OB_CONFLUENCE_SCORER_FOR_SINGLE_FAMILY_BUCKET_ROWS"
KEEP_DECISION = "KEEP_DEFAULT_OFF_FVG_OB_BUCKET_SHARED_PATH_PROXY_SCORER"


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


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        if str(row.get("created_at_utc") or "") >= str(latest.get(cid, {}).get("created_at_utc") or ""):
            latest[cid] = row
    return latest


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
    for path in [INPUT_ACTION_LEDGER, INPUT_FVG_OB, OUTPUT_LEDGER, OUTPUT_SUMMARY, OUTPUT_MANIFEST]:
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
    fvg_ob = latest_by_candidate(read_jsonl(INPUT_FVG_OB))

    if len(source_rows) != len(output_rows):
        failures.append(f"row_count_mismatch:{len(source_rows)}!={len(output_rows)}")

    source_ids = {str(row.get("row_id") or "") for row in source_rows}
    output_by_id = {str(row.get("row_id") or ""): row for row in output_rows}
    if source_ids != set(output_by_id):
        failures.append("row_id_set_changed")

    expected_kill: set[str] = set()
    expected_keep: set[str] = set()
    expected_bucket_counts: Counter[str] = Counter()
    for row in source_rows:
        if row.get("implementation_decision") != TARGET_SOURCE_DECISION:
            continue
        cid = str(row.get("candidate_id") or "")
        bucket = str((fvg_ob.get(cid) or {}).get("bucket") or "MISSING").lower()
        expected_bucket_counts[bucket] += 1
        row_id = str(row.get("row_id") or "")
        if bucket == "both_fvg_and_ob_fire":
            expected_keep.add(row_id)
        elif bucket in {"ob_only", "fvg_only", "no_poi", "disagreement"}:
            expected_kill.add(row_id)

    actual_kill = {
        str(row.get("row_id") or "")
        for row in output_rows
        if row.get("implementation_decision") == KILL_DECISION
    }
    actual_keep = {
        str(row.get("row_id") or "")
        for row in output_rows
        if row.get("implementation_decision") == KEEP_DECISION
    }
    if actual_kill != expected_kill:
        failures.append(f"kill_row_id_mismatch:expected={len(expected_kill)} actual={len(actual_kill)}")
    if actual_keep != expected_keep:
        failures.append(f"keep_row_id_mismatch:expected={len(expected_keep)} actual={len(actual_keep)}")

    for row_id in expected_kill:
        row = output_by_id[row_id]
        if row.get("action_class") != "KILL":
            failures.append(f"kill_action_class_mismatch:{row_id}")
        if row.get("after_proxy_r") is not None:
            failures.append(f"kill_row_opened_proxy:{row_id}")
    for row_id in expected_keep:
        row = output_by_id[row_id]
        if row.get("action_class") != "KEEP":
            failures.append(f"keep_action_class_mismatch:{row_id}")
        if safe_float(row.get("after_proxy_r")) is None:
            failures.append(f"keep_row_missing_proxy:{row_id}")

    output_decisions = Counter(row.get("implementation_decision") for row in output_rows)
    if output_decisions.get(TARGET_SOURCE_DECISION, 0) != 0:
        failures.append("fvg_ob_source_repair_rows_remaining")
    if output_decisions.get(KILL_DECISION, 0) != len(expected_kill):
        failures.append("kill_decision_count_mismatch")
    if output_decisions.get(KEEP_DECISION, 0) != len(expected_keep):
        failures.append("keep_decision_count_mismatch")

    before_proxy_rows, before_proxy_sum = proxy_stats(source_rows)
    after_proxy_rows, after_proxy_sum = proxy_stats(output_rows)
    if summary.get("rows") != len(output_rows):
        failures.append("summary_rows_mismatch")
    if summary.get("fvg_ob_source_repair_rows_after") != 0:
        failures.append("summary_source_repair_after_not_zero")
    if summary.get("repaired_action_rows") != len(expected_kill) + len(expected_keep):
        failures.append("summary_repaired_rows_mismatch")
    if summary.get("bucket_counts_on_target_rows") != dict(sorted(expected_bucket_counts.items())):
        failures.append("summary_bucket_counts_mismatch")
    if summary.get("numeric_proxy_row_delta") != after_proxy_rows - before_proxy_rows:
        failures.append("summary_proxy_row_delta_mismatch")
    if summary.get("proxy_r_sum_delta") != round(after_proxy_sum - before_proxy_sum, 8):
        failures.append("summary_proxy_sum_delta_mismatch")
    if summary.get("safe_flags") != SAFE_FLAGS:
        failures.append("summary_safe_flags_mismatch")

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
        "expected_kill_rows": len(expected_kill),
        "expected_keep_rows": len(expected_keep),
        "remaining_fvg_ob_source_repair_rows": output_decisions.get(TARGET_SOURCE_DECISION, 0),
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
