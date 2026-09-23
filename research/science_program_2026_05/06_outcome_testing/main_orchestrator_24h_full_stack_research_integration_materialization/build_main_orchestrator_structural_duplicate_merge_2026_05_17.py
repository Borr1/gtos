"""Merge duplicate structural-lock scorer rows into one counted scorer.

The current action ledger carries three V3 structural-lock rows per candidate
that share exactly the same candidate-path proxy as the canonical
V2_STRUCT_COMPOSITE_ANY scorer. This plate preserves every duplicate row and its
proxy reference, but removes duplicate shared-path R from the implementation
proxy denominator so positive evidence is merged rather than double-counted.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(ROUTE_DIR)
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_KILL_LABEL_SCOPE_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_KILL_LABEL_SCOPE_REPAIR_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_DUPLICATE_MERGE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_DUPLICATE_MERGE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_DUPLICATE_MERGE_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

STRUCTURAL_PRIMITIVE = "structural_lock_reentry_cost_metadata"
CANONICAL_STRATEGY_ID = "V2_STRUCT_COMPOSITE_ANY"
DUPLICATE_BRANCH = "REDESIGN_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY_NOT_DISTINCT_IMPLEMENTATION"
MERGE_BRANCH = "MERGE_DUPLICATE_STRUCTURAL_LOCK_SHARED_PATH_PROXY_INTO_V2_STRUCT_COMPOSITE_ANY"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "proxy_r_mean": round(sum(values) / len(values), 8) if values else None,
    }


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "") for row in rows))


def is_duplicate_structural_row(row: dict[str, Any]) -> bool:
    return (
        row.get("primitive_family") == STRUCTURAL_PRIMITIVE
        and row.get("strategy_id") != CANONICAL_STRATEGY_ID
        and row.get("action_class") == "REDESIGN"
        and row.get("branch_decision") == DUPLICATE_BRANCH
    )


def is_canonical_structural_row(row: dict[str, Any]) -> bool:
    return row.get("primitive_family") == STRUCTURAL_PRIMITIVE and row.get("strategy_id") == CANONICAL_STRATEGY_ID


def merge_row(source: dict[str, Any], generated_utc: str) -> tuple[dict[str, Any], bool]:
    row = {key: value for key, value in source.items() if key != "_source_line_no"}
    row["generated_utc"] = generated_utc
    if is_canonical_structural_row(row):
        row["structural_duplicate_merge_status"] = "CANONICAL_STRUCTURAL_LOCK_PROXY_COUNTED"
        row["canonical_strategy_id"] = CANONICAL_STRATEGY_ID
        row["proxy_counting_decision"] = "COUNT_CANONICAL_STRUCTURAL_LOCK_SHARED_PATH_PROXY_ONCE"
        return row, False
    if not is_duplicate_structural_row(row):
        row["structural_duplicate_merge_status"] = "NOT_TARGET_ROW"
        return row, False

    before_proxy = safe_float(row.get("after_proxy_r"))
    row["before_structural_duplicate_merge_branch_decision"] = row.get("branch_decision")
    row["before_structural_duplicate_merge_implementation_decision"] = row.get("implementation_decision")
    row["before_structural_duplicate_merge_after_proxy_r"] = before_proxy
    row["before_structural_duplicate_merge_proxy_counted"] = before_proxy is not None
    row["branch_decision"] = MERGE_BRANCH
    row["implementation_decision"] = MERGE_BRANCH
    row["implementation_candidate"] = "MERGE_INTO_CANONICAL_V2_STRUCT_COMPOSITE_ANY_SCORER_NO_DUPLICATE_R"
    row["current_action"] = "MERGE_DUPLICATE_STRUCTURAL_LOCK_ROW_INTO_CANONICAL_SCORER"
    row["next_action"] = "MERGE_DUPLICATE_STRUCTURAL_LOCK_ROW_INTO_CANONICAL_SCORER"
    row["coverage_status"] = "MERGED_DUPLICATE_POSITIVE_PROXY_EVIDENCE"
    row["decision_evidence"] = (
        "V3 structural-lock rows share the same candidate-path proxy and candidate_id as "
        "V2_STRUCT_COMPOSITE_ANY, so their proxy evidence is preserved but not counted again."
    )
    row["scoring_boundary"] = (
        "NO_DISTINCT_R_COUNT_FOR_V3_LOCK_VARIANTS_UNTIL_UNIQUE_LOCK_REENTRY_GEOMETRY_EXISTS"
    )
    row["canonical_strategy_id"] = CANONICAL_STRATEGY_ID
    row["merged_duplicate_proxy_reference_r"] = before_proxy
    row["after_proxy_r"] = None
    row["current_claim_proxy_counted"] = False
    row["proxy_counting_decision"] = "EXCLUDED_FROM_IMPLEMENTATION_PROXY_DENOMINATOR_DUPLICATE_SHARED_PATH"
    row["structural_duplicate_merge_status"] = "MERGED_DUPLICATE_SHARED_PATH_PROXY_INTO_CANONICAL_SCORER"
    row["structural_duplicate_merge_proxy_r_delta"] = round(-before_proxy, 8) if before_proxy is not None else 0.0
    row["missed_opportunity_audit"] = {
        "kill_scope": "NOT_KILLED_MERGED_DUPLICATE_POSITIVE_PROXY_EVIDENCE",
        "what_was_tried": "COMPARED_V3_STRUCTURAL_LOCK_ROWS_TO_CANONICAL_SHARED_CANDIDATE_PATH_PROXY",
        "what_could_make_it_work": (
            "UNIQUE_LOCK_REENTRY_GEOMETRY_OR_COST_MODEL_THAT_DIFFERS_FROM_V2_STRUCT_COMPOSITE_ANY"
        ),
        "preserve_as": "MERGED_COMPONENT_AND_FUTURE_UNIQUE_LOCK_REENTRY_SCORER_DESIGN",
        "next_route": "STRUCTURAL_LOCK_REENTRY_UNIQUE_GEOMETRY_AND_COST_MODEL_DESIGN",
    }
    row["underlying_intelligence_preserved"] = True
    return row, True


def materialize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    generated = utc_now()
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    for source in rows:
        row, changed = merge_row(source, generated)
        if changed:
            stats["duplicate_structural_rows_merged"] += 1
            if safe_float(row.get("merged_duplicate_proxy_reference_r")) is not None:
                stats["duplicate_structural_numeric_proxy_rows_excluded"] += 1
        output.append(row)
    return output, dict(stats)


def build_manifest(output_paths: list[Path]) -> dict[str, Any]:
    inputs = [INPUT_LEDGER, INPUT_SUMMARY]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            str(path.relative_to(REPO_ROOT)): {
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in inputs
        },
        "output_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in output_paths
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    input_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    output_rows, stats = materialize(input_rows)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    duplicate_rows = [
        row
        for row in output_rows
        if row.get("structural_duplicate_merge_status")
        == "MERGED_DUPLICATE_SHARED_PATH_PROXY_INTO_CANONICAL_SCORER"
    ]
    duplicate_reference_values = [
        value
        for row in duplicate_rows
        if (value := safe_float(row.get("merged_duplicate_proxy_reference_r"))) is not None
    ]
    canonical_rows = [
        row
        for row in output_rows
        if row.get("structural_duplicate_merge_status") == "CANONICAL_STRUCTURAL_LOCK_PROXY_COUNTED"
    ]
    canonical_values = [
        value for row in canonical_rows if (value := safe_float(row.get("after_proxy_r"))) is not None
    ]
    action_counts = counter(output_rows, "action_class")
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_STRUCTURAL_DUPLICATE_MERGE",
        "claim_boundary": (
            "Deduplicates structural-lock implementation proxy R by merging three V3 shared-path rows per "
            "candidate into the canonical V2_STRUCT_COMPOSITE_ANY scorer. Duplicate rows and proxy references "
            "are preserved as redesign intelligence; no live behavior, validation, promotion, broker operation, "
            "AI/API call, or shadow append is opened."
        ),
        "rows": len(output_rows),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "action_class_counts_after": action_counts,
        "action_class_counts_changed": action_counts != counter(input_rows, "action_class"),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_delta": after_proxy["numeric_proxy_rows"] - before_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "structural_rows": sum(1 for row in output_rows if row.get("primitive_family") == STRUCTURAL_PRIMITIVE),
        "canonical_structural_rows_counted": len(canonical_rows),
        "canonical_structural_numeric_proxy_rows": len(canonical_values),
        "canonical_structural_proxy_r_sum": round(sum(canonical_values), 8),
        "duplicate_structural_rows_merged": len(duplicate_rows),
        "duplicate_structural_numeric_proxy_rows_excluded": len(duplicate_reference_values),
        "duplicate_structural_proxy_reference_r_sum": round(sum(duplicate_reference_values), 8),
        "duplicate_structural_branch_counts_after": counter(duplicate_rows, "branch_decision"),
        "merge_status_counts": counter(output_rows, "structural_duplicate_merge_status"),
        "repair_stats": stats,
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "STRUCTURAL_DUPLICATE_SHARED_PATH_PROXY_R_MERGED_INTO_CANONICAL_SCORER",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "duplicate_rows_merged": len(duplicate_rows),
                "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
                "proxy_r_sum_after": after_proxy["proxy_r_sum"],
                "summary": str(OUTPUT_SUMMARY),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
