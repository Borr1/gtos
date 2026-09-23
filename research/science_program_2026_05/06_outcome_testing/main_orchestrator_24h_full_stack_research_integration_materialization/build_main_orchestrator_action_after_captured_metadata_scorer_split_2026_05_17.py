"""Split generic captured-metadata scorer labels into concrete branches."""

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

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_NEAR_MISS_OWNER_MERGE_DECISION_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PREFILL_NEAR_MISS_OWNER_MERGE_DECISION_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_CAPTURED_METADATA_SCORER_SPLIT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_CAPTURED_METADATA_SCORER_SPLIT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_CAPTURED_METADATA_SCORER_SPLIT_OUTPUT_MANIFEST_{DATE}.json"

OLD_BRANCH = "IMPLEMENT_SHADOW_SCORER_CAPTURED_METADATA_DEFAULT_OFF"
STRUCTURAL_STRATEGY = "V2_STRUCT_COMPOSITE_ANY"
FVG_OB_STRATEGY = "FVG_OB_CONFLUENCE_OB_AFTER_FVG"
STRUCTURAL_BRANCH = "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_COMPOSITE_CAPTURED_METADATA_SHARED_PATH_SCORER"
FVG_OB_BRANCH = "IMPLEMENT_DEFAULT_OFF_FVG_OB_CONFLUENCE_CAPTURED_METADATA_SHARED_PATH_SCORER"

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


def target_row(row: dict[str, Any]) -> bool:
    return row.get("action_class") == "IMPLEMENT_DEFAULT_OFF" and row.get("branch_decision") == OLD_BRANCH


def convert_target(row: dict[str, Any], *, generated_utc: str) -> None:
    strategy_id = row.get("strategy_id")
    row["before_captured_metadata_scorer_split_branch_decision"] = row.get("branch_decision")
    row["captured_metadata_scorer_split_generated_utc"] = generated_utc
    row["captured_metadata_proxy_counted_as_r"] = True
    row["safe_flags"] = SAFE_FLAGS
    row["no_live_behavior"] = True
    row["no_shadow_log_append"] = True
    if strategy_id == STRUCTURAL_STRATEGY:
        row["branch_decision"] = STRUCTURAL_BRANCH
        row["current_action"] = STRUCTURAL_BRANCH
        row["strategy_status"] = STRUCTURAL_BRANCH
        row["implementation_decision"] = STRUCTURAL_BRANCH
        row["implementation_candidate"] = (
            "IMPLEMENT_DEFAULT_OFF_STRUCTURAL_METADATA_SHARED_PATH_SCORER_AND_DESIGN_LOCK_REENTRY_SCORER"
        )
        row["decision_evidence"] = "CAPTURED_STRUCTURAL_COMPOSITE_METADATA_SCORED_WITH_SHARED_CANDIDATE_PATH_PROXY"
        row["scoring_boundary"] = "STRUCTURAL_COMPOSITE_CAPTURED_METADATA_SHARED_PATH_PROXY_NO_LOCK_REENTRY_CLAIM"
        row["captured_metadata_scorer_split_status"] = "STRUCTURAL_COMPOSITE_DEFAULT_OFF_SCORER_SPLIT"
    elif strategy_id == FVG_OB_STRATEGY:
        row["branch_decision"] = FVG_OB_BRANCH
        row["current_action"] = FVG_OB_BRANCH
        row["strategy_status"] = FVG_OB_BRANCH
        row["implementation_decision"] = FVG_OB_BRANCH
        row["implementation_candidate"] = "IMPLEMENT_DEFAULT_OFF_FVG_OB_CONFLUENCE_SHARED_PATH_PROXY_SCORER"
        row["decision_evidence"] = "CAPTURED_FVG_OB_CONFLUENCE_METADATA_SCORED_WITH_SHARED_CANDIDATE_PATH_PROXY"
        row["scoring_boundary"] = "FVG_OB_CONFLUENCE_CAPTURED_METADATA_SHARED_PATH_PROXY_NO_STANDALONE_FVG_ENTRY"
        row["captured_metadata_scorer_split_status"] = "FVG_OB_CONFLUENCE_DEFAULT_OFF_SCORER_SPLIT"
    else:
        raise ValueError(f"unsupported captured metadata strategy: {strategy_id}")


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
            row["captured_metadata_scorer_split_status"] = "NOT_TARGET_ROW"
        output_rows.append(row)

    after_proxy = proxy_summary(output_rows)
    strategy_counts = Counter(row.get("strategy_id") for row in converted)
    proxy_by_strategy: dict[str, dict[str, Any]] = {}
    for strategy_id in [STRUCTURAL_STRATEGY, FVG_OB_STRATEGY]:
        values = [
            value
            for row in converted
            if row.get("strategy_id") == strategy_id
            if (value := safe_float(row.get("after_proxy_r"))) is not None
        ]
        proxy_by_strategy[strategy_id] = {
            "rows": len(values),
            "sum": round(sum(values), 8),
            "positive": sum(value > 0 for value in values),
            "zero": sum(value == 0 for value in values),
            "negative": sum(value < 0 for value in values),
        }
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
        "captured_metadata_rows_split": len(converted),
        "structural_composite_rows_split": strategy_counts.get(STRUCTURAL_STRATEGY, 0),
        "fvg_ob_confluence_rows_split": strategy_counts.get(FVG_OB_STRATEGY, 0),
        "proxy_by_strategy": proxy_by_strategy,
        "old_generic_branch_rows_remaining": sum(target_row(row) for row in output_rows),
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
        "description": "Concrete split of generic captured-metadata default-off scorer branches.",
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
            "captured_metadata_rows_split": len(converted),
            "structural_composite_rows_split": summary["structural_composite_rows_split"],
            "fvg_ob_confluence_rows_split": summary["fvg_ob_confluence_rows_split"],
            "numeric_proxy_rows_after": summary["numeric_proxy_rows_after"],
            "proxy_r_sum_after": summary["proxy_r_sum_after"],
        },
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
