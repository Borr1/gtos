"""Split and repair swing-protected default-off scorer labels."""

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

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_CAPTURED_METADATA_SCORER_SPLIT_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_CAPTURED_METADATA_SCORER_SPLIT_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_SCORER_SPLIT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_SCORER_SPLIT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SWING_PROTECTED_SCORER_SPLIT_OUTPUT_MANIFEST_{DATE}.json"

OLD_GENERIC_BRANCH = "IMPLEMENT_SHADOW_SCORER_SWING_PROTECTED_STOP_DEFAULT_OFF"
NEW_GENERIC_BRANCH = "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_STOP_CAPTURED_METADATA_SCORER"
SOURCE_REPAIRED_BRANCH = "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_SOURCE_REPAIRED_LTF_PROXY"
OLD_SOURCE_REPAIRED_CANDIDATE = "KEEP_DEFAULT_OFF_SWING_PROTECTED_STOP_PATH_SCORER_NOW_SOURCE_REPAIRED"
NEW_SOURCE_REPAIRED_CANDIDATE = "IMPLEMENT_DEFAULT_OFF_SWING_PROTECTED_STOP_PATH_SCORER_NOW_SOURCE_REPAIRED"

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


def convert_generic(row: dict[str, Any], *, generated_utc: str) -> None:
    row["before_swing_protected_scorer_split_branch_decision"] = row.get("branch_decision")
    row["branch_decision"] = NEW_GENERIC_BRANCH
    row["current_action"] = NEW_GENERIC_BRANCH
    row["strategy_status"] = NEW_GENERIC_BRANCH
    row["implementation_decision"] = NEW_GENERIC_BRANCH
    row["decision_evidence"] = "CANDIDATE_STOP_PROTECTS_CAPTURED_SIDE_COMPATIBLE_SWING"
    row["scoring_boundary"] = "SWING_PROTECTED_STOP_CAPTURED_METADATA_CANDIDATE_PATH_PROXY_NOT_LOCK_REENTRY"
    row["swing_protected_scorer_split_status"] = "GENERIC_BRANCH_SPLIT_TO_SWING_PROTECTED_STOP_SCORER"
    row["swing_protected_proxy_counted_as_r"] = True
    row["swing_protected_scorer_split_generated_utc"] = generated_utc
    row["safe_flags"] = SAFE_FLAGS
    row["no_live_behavior"] = True
    row["no_shadow_log_append"] = True


def repair_source_candidate(row: dict[str, Any], *, generated_utc: str) -> None:
    row["before_swing_protected_scorer_split_implementation_candidate"] = row.get("implementation_candidate")
    row["implementation_candidate"] = NEW_SOURCE_REPAIRED_CANDIDATE
    row["current_action"] = SOURCE_REPAIRED_BRANCH
    row["strategy_status"] = SOURCE_REPAIRED_BRANCH
    row["implementation_decision"] = SOURCE_REPAIRED_BRANCH
    row["decision_evidence"] = "SWING_PROTECTED_SOURCE_REPAIRED_LTF_PROXY_IMPLEMENTATION_LABEL_REPAIRED"
    row["swing_protected_scorer_split_status"] = "SOURCE_REPAIRED_IMPLEMENTATION_CANDIDATE_LABEL_REPAIRED"
    row["swing_protected_proxy_counted_as_r"] = True
    row["swing_protected_scorer_split_generated_utc"] = generated_utc
    row["safe_flags"] = SAFE_FLAGS
    row["no_live_behavior"] = True
    row["no_shadow_log_append"] = True


def build() -> dict[str, Any]:
    generated_utc = utc_now()
    input_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    before_counts = Counter(str(row.get("action_class") or "") for row in input_rows)
    before_proxy = proxy_summary(input_rows)
    output_rows: list[dict[str, Any]] = []
    generic_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []

    for source_row in input_rows:
        row = {key: value for key, value in source_row.items() if key != "_source_line_no"}
        if row.get("action_class") == "IMPLEMENT_DEFAULT_OFF" and row.get("branch_decision") == OLD_GENERIC_BRANCH:
            convert_generic(row, generated_utc=generated_utc)
            generic_rows.append(row)
        elif (
            row.get("action_class") == "IMPLEMENT_DEFAULT_OFF"
            and row.get("branch_decision") == SOURCE_REPAIRED_BRANCH
            and row.get("implementation_candidate") == OLD_SOURCE_REPAIRED_CANDIDATE
        ):
            repair_source_candidate(row, generated_utc=generated_utc)
            source_rows.append(row)
        else:
            row["swing_protected_scorer_split_status"] = "NOT_TARGET_ROW"
        output_rows.append(row)

    after_proxy = proxy_summary(output_rows)

    def values(rows: list[dict[str, Any]]) -> list[float]:
        return [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]

    generic_values = values(generic_rows)
    source_values = values(source_rows)
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
        "action_class_counts_after": dict(sorted(Counter(str(row.get("action_class") or "") for row in output_rows).items())),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "swing_protected_rows_touched": len(generic_rows) + len(source_rows),
        "generic_branch_rows_split": len(generic_rows),
        "source_repaired_candidate_label_rows": len(source_rows),
        "generic_branch_proxy_rows": len(generic_values),
        "generic_branch_proxy_sum": round(sum(generic_values), 8),
        "source_repaired_proxy_rows": len(source_values),
        "source_repaired_proxy_sum": round(sum(source_values), 8),
        "old_generic_branch_rows_remaining": sum(row.get("branch_decision") == OLD_GENERIC_BRANCH for row in output_rows),
        "old_source_repaired_candidate_rows_remaining": sum(
            row.get("branch_decision") == SOURCE_REPAIRED_BRANCH
            and row.get("implementation_candidate") == OLD_SOURCE_REPAIRED_CANDIDATE
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
        "description": "Swing-protected scorer branch split and source-repaired implementation label repair.",
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
            "swing_protected_rows_touched": summary["swing_protected_rows_touched"],
            "generic_branch_rows_split": summary["generic_branch_rows_split"],
            "source_repaired_candidate_label_rows": summary["source_repaired_candidate_label_rows"],
            "numeric_proxy_rows_after": summary["numeric_proxy_rows_after"],
            "proxy_r_sum_after": summary["proxy_r_sum_after"],
        },
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
