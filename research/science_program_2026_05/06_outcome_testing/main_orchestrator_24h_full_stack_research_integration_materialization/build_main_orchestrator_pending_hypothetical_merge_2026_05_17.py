"""Reclassify pending lifecycle hypothetical shared-path rows as redesign.

Rows with no live pending-limit intent were previously counted under the
PENDING_LIMIT_LIFECYCLE strategy by reusing the candidate path. That is useful
intelligence, but it is not distinct pending-lifecycle evidence and must not
inflate the implementation proxy denominator. This plate preserves the rows
and their proxy references while removing the shared-path proxy from counted R.
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
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_ACTION_RECLASS_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_ACTION_RECLASS_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_HYPOTHETICAL_MERGE_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_HYPOTHETICAL_MERGE_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_HYPOTHETICAL_MERGE_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

TARGET_PRIMITIVE = "pending_lifecycle_fill_cancel_expiry_source_capture"
TARGET_BRANCH = "KEEP_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_SCORER"
NEW_BRANCH = "REDESIGN_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_PROXY_NOT_DISTINCT"
CANONICAL_STATUS = "CANONICAL_PENDING_LIFECYCLE_ROW_PROXY_COUNTED"
DUPLICATE_STATUS = "MERGED_DUPLICATE_PENDING_SOURCE_DERIVATION_ROW"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(ROUTE_DIR)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
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


def is_hypothetical_pending(row: dict[str, Any]) -> bool:
    return row.get("primitive_family") == TARGET_PRIMITIVE and row.get("branch_decision") == TARGET_BRANCH


def materialize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    generated = utc_now()
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if not is_hypothetical_pending(row):
            row["pending_hypothetical_merge_status"] = "NOT_TARGET_ROW"
            output.append(row)
            continue

        before_proxy = safe_float(row.get("after_proxy_r"))
        duplicate_reference = safe_float(row.get("merged_duplicate_proxy_reference_r"))
        row["before_pending_hypothetical_merge_action_class"] = row.get("action_class")
        row["before_pending_hypothetical_merge_branch_decision"] = row.get("branch_decision")
        row["before_pending_hypothetical_merge_after_proxy_r"] = before_proxy
        row["branch_decision"] = NEW_BRANCH
        row["implementation_decision"] = NEW_BRANCH
        row["action_class"] = "REDESIGN"
        row["coverage_status"] = "REDESIGN_REQUIRED_SHARED_PATH_PROXY_NOT_DISTINCT"
        row["current_action"] = (
            "REDESIGN_PENDING_LIMIT_ENTRY_MODEL_WITH_SOURCE_BOUND_INTENT_OR_MERGE_WITH_ENTRY_GEOMETRY"
        )
        row["implementation_candidate"] = (
            "REDESIGN_PENDING_LIMIT_ENTRY_MODEL_WITH_SOURCE_BOUND_INTENT_OR_MERGE_WITH_ENTRY_GEOMETRY"
        )
        row["next_action"] = (
            "REDESIGN_PENDING_LIMIT_ENTRY_MODEL_WITH_SOURCE_BOUND_INTENT_OR_MERGE_WITH_ENTRY_GEOMETRY"
        )
        row["decision_evidence"] = (
            "NO_LIVE_PENDING_LIMIT_INTENT_SHARED_CANDIDATE_PATH_DUPLICATE_NOT_LIFECYCLE_TRUTH"
        )
        row["scoring_boundary"] = "HYPOTHETICAL_PENDING_LIMIT_PATH_PROXY_NOT_DISTINCT_IMPLEMENTATION_EVIDENCE"
        row["underlying_intelligence_preserved"] = True
        row["missed_opportunity_audit"] = {
            "kill_scope": "NOT_KILLED_REDESIGNED_SHARED_PATH_PROXY",
            "preserve_as": "PENDING_ENTRY_MODEL_REDESIGN_OR_ENTRY_GEOMETRY_MERGE",
            "unsupported_current_claim": "PENDING_LIMIT_LIFECYCLE_EDGE_FROM_NO_INTENT_SHARED_CANDIDATE_PATH",
            "what_was_tried": "COUNTED_HYPOTHETICAL_PENDING_PATH_WITH_EXISTING_CANDIDATE_PATH_PROXY",
            "what_could_make_it_work": (
                "SOURCE_BOUND_PENDING_INTENT_MODEL_OR_DISTINCT_ENTRY_GEOMETRY_REPLAY_WITH_FILL_CANCEL_COST_FIELDS"
            ),
            "next_route": "REDESIGN_PENDING_LIMIT_ENTRY_GEOMETRY_OR_MERGE_WITH_EXISTING_ENTRY_SCORERS",
        }

        if row.get("pending_duplicate_merge_status") == CANONICAL_STATUS:
            row["pending_hypothetical_merge_status"] = "CANONICAL_SHARED_PATH_PROXY_EXCLUDED_REDESIGN"
            row["pending_hypothetical_proxy_reference_r"] = before_proxy
            row["after_proxy_r"] = None
            row["current_claim_proxy_counted"] = False
            row["proxy_counting_decision"] = (
                "EXCLUDED_FROM_IMPLEMENTATION_PROXY_DENOMINATOR_SHARED_PATH_NOT_PENDING_LIFECYCLE"
            )
            stats["canonical_hypothetical_pending_rows_redesigned"] += 1
            if before_proxy is not None:
                stats["canonical_hypothetical_numeric_proxy_rows_excluded"] += 1
        elif row.get("pending_duplicate_merge_status") == DUPLICATE_STATUS:
            row["pending_hypothetical_merge_status"] = "DUPLICATE_SHARED_PATH_PROXY_REFERENCE_REDESIGN"
            row["pending_hypothetical_proxy_reference_r"] = duplicate_reference
            row["after_proxy_r"] = None
            row["current_claim_proxy_counted"] = False
            row["proxy_counting_decision"] = (
                "ALREADY_EXCLUDED_DUPLICATE_SHARED_PATH_NOT_PENDING_LIFECYCLE"
            )
            stats["duplicate_hypothetical_pending_rows_redesigned"] += 1
            if duplicate_reference is not None:
                stats["duplicate_hypothetical_proxy_reference_rows_preserved"] += 1
        else:
            row["pending_hypothetical_merge_status"] = "HYPOTHETICAL_PENDING_UNEXPECTED_MERGE_STATUS"
            stats["unexpected_hypothetical_pending_rows"] += 1
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
    canonical = [
        row
        for row in output_rows
        if row.get("pending_hypothetical_merge_status") == "CANONICAL_SHARED_PATH_PROXY_EXCLUDED_REDESIGN"
    ]
    duplicate = [
        row
        for row in output_rows
        if row.get("pending_hypothetical_merge_status") == "DUPLICATE_SHARED_PATH_PROXY_REFERENCE_REDESIGN"
    ]
    canonical_values = [
        value for row in canonical if (value := safe_float(row.get("pending_hypothetical_proxy_reference_r"))) is not None
    ]
    duplicate_values = [
        value for row in duplicate if (value := safe_float(row.get("pending_hypothetical_proxy_reference_r"))) is not None
    ]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_PENDING_HYPOTHETICAL_MERGE",
        "claim_boundary": (
            "Converts no-live-intent pending lifecycle shared-path rows from passive KEEP to REDESIGN and "
            "removes their candidate-path proxy from implementation R. The underlying intelligence remains "
            "available for a source-bound pending entry model or merge into entry geometry scorers."
        ),
        "rows": len(output_rows),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "action_class_counts_before": counter(input_rows, "action_class"),
        "action_class_counts_after": counter(output_rows, "action_class"),
        "action_class_delta_vs_previous": {
            key: counter(output_rows, "action_class").get(key, 0) - counter(input_rows, "action_class").get(key, 0)
            for key in sorted(set(counter(input_rows, "action_class")) | set(counter(output_rows, "action_class")))
            if counter(output_rows, "action_class").get(key, 0) != counter(input_rows, "action_class").get(key, 0)
        },
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_delta": after_proxy["numeric_proxy_rows"] - before_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "canonical_hypothetical_rows_redesigned": len(canonical),
        "canonical_hypothetical_numeric_proxy_rows_excluded": len(canonical_values),
        "canonical_hypothetical_proxy_reference_r_sum": round(sum(canonical_values), 8),
        "duplicate_hypothetical_rows_redesigned": len(duplicate),
        "duplicate_hypothetical_proxy_reference_rows_preserved": len(duplicate_values),
        "duplicate_hypothetical_proxy_reference_r_sum": round(sum(duplicate_values), 8),
        "pending_hypothetical_merge_status_counts": counter(output_rows, "pending_hypothetical_merge_status"),
        "repair_stats": stats,
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "PENDING_HYPOTHETICAL_SHARED_PATH_PROXY_REDESIGNED_AND_DEDUPED",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "canonical_hypothetical_rows_redesigned": len(canonical),
                "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
                "proxy_r_sum_after": after_proxy["proxy_r_sum"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
