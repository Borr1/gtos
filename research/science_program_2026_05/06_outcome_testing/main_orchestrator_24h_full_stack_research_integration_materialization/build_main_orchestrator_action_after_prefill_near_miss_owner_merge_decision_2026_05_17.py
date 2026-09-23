"""Convert near-miss prefill owner-merged rows out of KEEP.

Near-miss prefill TP-after-fill rows are not standalone implementation rows:
their proxy R is owned by ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER. This
plate keeps the opportunity and proxy reference, but moves the metadata rows
from KEEP to an explicit merge/redesign action class so the action ledger no
longer treats owner-merged context as passive carryforward.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_SOURCE_DECISION_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_SOURCE_DECISION_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_NEAR_MISS_OWNER_MERGE_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_NEAR_MISS_OWNER_MERGE_DECISION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_NEAR_MISS_OWNER_MERGE_DECISION_OUTPUT_MANIFEST_{DATE}.json"

TARGET_BRANCH = "MERGE_PREFILL_NEAR_MISS_INTO_ENTRY_OFFSET_050R_IMPLEMENTATION"
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_no"] = line_no
                rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "positive_rows": sum(value > 0 for value in values),
        "zero_rows": sum(value == 0 for value in values),
        "negative_rows": sum(value < 0 for value in values),
    }


def action_delta(before: Counter[str], after: Counter[str]) -> dict[str, int]:
    keys = sorted(set(before) | set(after))
    return {
        key: int(after.get(key, 0)) - int(before.get(key, 0))
        for key in keys
        if int(after.get(key, 0)) != int(before.get(key, 0))
    }


def target_row(row: dict[str, Any]) -> bool:
    return row.get("action_class") == "KEEP" and row.get("branch_decision") == TARGET_BRANCH


def convert_target(row: dict[str, Any], *, generated_utc: str) -> None:
    row["before_prefill_near_miss_owner_merge_action_class"] = row.get("action_class")
    row["before_prefill_near_miss_owner_merge_branch_decision"] = row.get("branch_decision")
    row["action_class"] = "REDESIGN"
    row["current_action"] = TARGET_BRANCH
    row["strategy_status"] = TARGET_BRANCH
    row["implementation_decision"] = TARGET_BRANCH
    row["implementation_candidate"] = "MERGE_PREFILL_NEAR_MISS_CONTEXT_INTO_ENTRY_OFFSET_050R_SCORER"
    row["decision_evidence"] = "PREFILL_NEAR_MISS_OWNER_MERGE_CONSUMED_NO_STANDALONE_IMPLEMENTATION"
    row["scoring_boundary"] = "PREFILL_NEAR_MISS_PROXY_REFERENCE_OWNED_BY_ENTRY_OFFSET_SCORER_NO_DUPLICATE_R"
    row["prefill_near_miss_owner_merge_decision_status"] = "MOVED_FROM_KEEP_TO_OWNER_MERGE_REDESIGN"
    row["prefill_proxy_reference_counted_as_r"] = False
    row["prefill_proxy_reference_owner"] = "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER"
    row["prefill_near_miss_owner_merge_generated_utc"] = generated_utc
    row["opportunity_proxy_reference_status"] = "REFERENCE_ONLY_OWNER_MERGED_NOT_COUNTED"
    row["opportunity_not_independently_countable_reason"] = (
        "Near-miss prefill metadata has no independent fill/terminal contract; proxy R is owned by the "
        "entry-offset 0.50R scorer row and must not be duplicated."
    )
    row["opportunity_useful_mechanism"] = (
        "Near-miss prefill delivery remains useful as an entry-offset context feature, merge component, "
        "and broader fillability signal."
    )
    row["opportunity_downstream_paths"] = ["entry-offset merge", "context feature", "broader system component"]
    row["underlying_intelligence_preserved"] = True
    row["safe_flags"] = SAFE_FLAGS
    row["no_live_behavior"] = True
    row["no_shadow_log_append"] = True
    audit = row.get("missed_opportunity_audit")
    if isinstance(audit, dict):
        audit["decision_branch"] = TARGET_BRANCH
        audit["unsupported_reason"] = "OWNER_MERGED_NOT_INDEPENDENTLY_COUNTABLE"
        audit["preserve_as"] = "ENTRY_OFFSET_CONTEXT_FEATURE_AND_OWNER_MERGED_COMPONENT"
        row["missed_opportunity_audit"] = audit


def build() -> dict[str, Any]:
    generated_utc = utc_now()
    input_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    before_counts = Counter(str(row.get("action_class") or "") for row in input_rows)
    before_proxy = proxy_summary(input_rows)
    output_rows: list[dict[str, Any]] = []
    converted: list[dict[str, Any]] = []

    for source_row in input_rows:
        row = {key: value for key, value in source_row.items() if key != "_source_line_no"}
        if target_row(row):
            convert_target(row, generated_utc=generated_utc)
            converted.append(row)
        else:
            row["prefill_near_miss_owner_merge_decision_status"] = "NOT_TARGET_ROW"
        output_rows.append(row)

    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    after_proxy = proxy_summary(output_rows)
    refs = [safe_float(row.get("opportunity_proxy_r_reference")) for row in converted]
    refs = [value for value in refs if value is not None]
    summary = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "input_ledger": str(INPUT_LEDGER),
        "input_summary": str(INPUT_SUMMARY),
        "input_rows": len(input_rows),
        "rows": len(output_rows),
        "exact_r_rows": 0,
        "action_class_counts_before": dict(sorted(before_counts.items())),
        "action_class_counts_after": dict(sorted(after_counts.items())),
        "action_class_delta_vs_previous": action_delta(before_counts, after_counts),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "prefill_near_miss_owner_merged_rows": len(converted),
        "rows_removed_from_keep": sum(row.get("before_prefill_near_miss_owner_merge_action_class") == "KEEP" for row in converted),
        "rows_added_to_redesign": sum(row.get("action_class") == "REDESIGN" for row in converted),
        "proxy_r_reference_rows": len(refs),
        "proxy_r_reference_sum_not_counted": round(sum(refs), 8),
        "counted_proxy_r_rows_added": 0,
        "counted_proxy_r_sum_added": 0.0,
        "remaining_prefill_near_miss_keep_rows": sum(target_row(row) for row in output_rows),
        "owner_merge_rows_missing_audit": sum(
            row.get("prefill_near_miss_owner_merge_decision_status")
            == "MOVED_FROM_KEEP_TO_OWNER_MERGE_REDESIGN"
            and not isinstance(row.get("missed_opportunity_audit"), dict)
            for row in output_rows
        ),
        "owner_merge_rows_missing_underlying_intel": sum(
            row.get("prefill_near_miss_owner_merge_decision_status")
            == "MOVED_FROM_KEEP_TO_OWNER_MERGE_REDESIGN"
            and row.get("underlying_intelligence_preserved") is not True
            for row in output_rows
        ),
        "research_safety": {
            "opens_exact_r": False,
            "opens_counted_proxy_r": False,
            "changes_shadow_log_history": False,
            "changes_live_behavior": False,
            "changes_prompt_risk_selector_execution": False,
        },
        "input_snapshot": {
            "input_ledger_sha256": sha256_file(INPUT_LEDGER),
            "input_ledger_size_bytes": INPUT_LEDGER.stat().st_size,
            "input_summary_sha256": sha256_file(INPUT_SUMMARY),
            "input_summary_captured_proxy_rows": input_summary.get("numeric_proxy_rows_after"),
            "input_summary_captured_proxy_sum": input_summary.get("proxy_r_sum_after"),
        },
    }
    write_jsonl(OUTPUT_LEDGER, output_rows)
    write_json(OUTPUT_SUMMARY, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": generated_utc,
        "description": "Near-miss prefill owner-merge action class materialization.",
        "safe_flags": SAFE_FLAGS,
        "input_files": {
            "input_ledger": {
                "path": str(INPUT_LEDGER),
                "sha256": sha256_file(INPUT_LEDGER),
                "size_bytes": INPUT_LEDGER.stat().st_size,
                "rows": len(input_rows),
            },
            "input_summary": {
                "path": str(INPUT_SUMMARY),
                "sha256": sha256_file(INPUT_SUMMARY),
                "size_bytes": INPUT_SUMMARY.stat().st_size,
            },
        },
        "output_files": {
            "ledger": {
                "path": str(OUTPUT_LEDGER),
                "sha256": sha256_file(OUTPUT_LEDGER),
                "size_bytes": OUTPUT_LEDGER.stat().st_size,
                "rows": len(output_rows),
            },
            "summary": {
                "path": str(OUTPUT_SUMMARY),
                "sha256": sha256_file(OUTPUT_SUMMARY),
                "size_bytes": OUTPUT_SUMMARY.stat().st_size,
            },
        },
        "counts": {
            "rows": len(output_rows),
            "prefill_near_miss_owner_merged_rows": len(converted),
            "proxy_r_reference_rows": summary["proxy_r_reference_rows"],
            "proxy_r_reference_sum_not_counted": summary["proxy_r_reference_sum_not_counted"],
            "numeric_proxy_rows_after": summary["numeric_proxy_rows_after"],
            "proxy_r_sum_after": summary["proxy_r_sum_after"],
        },
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
