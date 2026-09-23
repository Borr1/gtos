"""Materialize pending-lifecycle source-completeness action decisions.

The previous action ledger still left pending lifecycle rows as KEEP after
spread/source repairs. This plate consumes those repaired source fields:
source-complete rows with computable pending-lifecycle R become default-off
implementation candidates, source-complete rows with missing R become repair
redesigns, source-partial rows become source-repair redesigns, and duplicate
source-derivation rows are merged into their canonical pending scorer owner.
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

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_SUMMARY_{DATE}.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_SOURCE_DECISION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_SOURCE_DECISION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_LIFECYCLE_SOURCE_DECISION_OUTPUT_MANIFEST_{DATE}.json"

OLD_COMPLETE_RECONSTRUCTED = "KEEP_PENDING_LIFECYCLE_SCORER_WITH_RECONSTRUCTED_SOURCE_FIELDS_COMPLETE"
OLD_COMPLETE_CAPTURE = "KEEP_PENDING_LIFECYCLE_SCORER_WITH_CAPTURE_FIELDS_COMPLETE"
OLD_PARTIAL_DERIVED = "KEEP_PENDING_LIFECYCLE_SCORER_WITH_DERIVED_SOURCE_FIELDS_CURRENT_ROWS_PARTIAL"
OLD_PARTIAL_FORWARD = "KEEP_PENDING_LIFECYCLE_SCORER_FORWARD_CAPTURE_FIELDS_IMPLEMENTED_CURRENT_ROWS_PARTIAL"

IMPLEMENT_RECONSTRUCTED = "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_RECONSTRUCTED_SOURCE_SCORER"
IMPLEMENT_CAPTURE_COMPLETE = "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_CAPTURE_COMPLETE_SCORER"
REDESIGN_R_REQUIRED = "REDESIGN_PENDING_LIFECYCLE_R_OUTCOME_SOURCE_REQUIRED"
REDESIGN_SOURCE_PARTIAL = "REDESIGN_PENDING_LIFECYCLE_SOURCE_PARTIAL_REPAIR_REQUIRED"
REDESIGN_FORWARD_PARTIAL = "REDESIGN_PENDING_LIFECYCLE_FORWARD_CAPTURE_FIELDS_PARTIAL_REPAIR_REQUIRED"
MERGE_DUPLICATE_DERIVATION = "MERGE_DUPLICATE_PENDING_SOURCE_DERIVATION_ROW_INTO_CANONICAL_PENDING_SCORER"

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


def is_old_target(row: dict[str, Any]) -> bool:
    return row.get("branch_decision") in {
        OLD_COMPLETE_RECONSTRUCTED,
        OLD_COMPLETE_CAPTURE,
        OLD_PARTIAL_DERIVED,
        OLD_PARTIAL_FORWARD,
    }


def canonical_pending_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("strategy_id") == "PENDING_LIMIT_LIFECYCLE":
            candidate_id = str(row.get("candidate_id") or "")
            if candidate_id:
                mapping[candidate_id] = row
    return mapping


def audit_payload(
    row: dict[str, Any],
    *,
    decision_branch: str,
    preserve_as: str,
    next_route: str,
    unsupported_reason: str,
) -> dict[str, Any]:
    return {
        "kill_scope": "NOT_KILLED_PENDING_LIFECYCLE_SOURCE_DECISION",
        "current_claim": row.get("before_pending_lifecycle_source_branch_decision") or row.get("branch_decision"),
        "decision_branch": decision_branch,
        "unsupported_reason": unsupported_reason,
        "what_was_tried": (
            "Consumed pending lifecycle intent/fill/cancel telemetry, nofill-forward decision spread, "
            "tick-parquet spread reconstruction, legacy spread proxy, duplicate source-derivation ownership, "
            "and current pending lifecycle R/proxy status."
        ),
        "what_could_make_it_work": (
            "Source-complete rows need a default-off pending-lifecycle scorer; source-partial rows need exact "
            "decision spread/fill/R repair; duplicate derivation rows need the canonical pending scorer owner."
        ),
        "preserve_as": preserve_as,
        "next_route": next_route,
        "path_status": {
            "candidate_id": row.get("candidate_id"),
            "strategy_id": row.get("strategy_id"),
            "pending_lifecycle_source_capture_complete": row.get("pending_lifecycle_source_capture_complete"),
            "data_requirement_state": row.get("data_requirement_state"),
            "proxy_r_reference": row.get("opportunity_proxy_r_reference"),
            "decision_spread_source": row.get("pending_lifecycle_decision_spread_reconstruction_source"),
            "decision_spread_status": row.get("pending_lifecycle_decision_spread_reconstruction_source_status"),
        },
    }


def apply_common(row: dict[str, Any], *, generated_utc: str) -> None:
    row["before_pending_lifecycle_source_action_class"] = row.get("action_class")
    row["before_pending_lifecycle_source_branch_decision"] = row.get("branch_decision")
    row["before_pending_lifecycle_source_after_proxy_r"] = row.get("after_proxy_r")
    row["pending_lifecycle_source_decision_generated_utc"] = generated_utc
    row["safe_flags"] = SAFE_FLAGS
    row["no_live_behavior"] = True
    row["no_shadow_log_append"] = True
    row["underlying_intelligence_preserved"] = True


def convert_complete_numeric(row: dict[str, Any], *, generated_utc: str) -> None:
    apply_common(row, generated_utc=generated_utc)
    branch = IMPLEMENT_RECONSTRUCTED if row.get("branch_decision") == OLD_COMPLETE_RECONSTRUCTED else IMPLEMENT_CAPTURE_COMPLETE
    candidate = (
        "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_INTERNAL_TRUTH_SCORER_WITH_RECONSTRUCTED_SOURCE_FIELDS"
        if branch == IMPLEMENT_RECONSTRUCTED
        else "IMPLEMENT_DEFAULT_OFF_PENDING_LIFECYCLE_INTERNAL_TRUTH_SCORER_WITH_COMPLETE_SOURCE_FIELDS"
    )
    row["action_class"] = "IMPLEMENT_DEFAULT_OFF"
    row["branch_decision"] = branch
    row["current_action"] = candidate
    row["strategy_status"] = branch
    row["implementation_decision"] = branch
    row["implementation_candidate"] = candidate
    row["decision_evidence"] = (
        "PENDING_LIFECYCLE_SOURCE_COMPLETE_AND_R_COMPUTABLE_READY_FOR_DEFAULT_OFF_SCORER"
    )
    row["scoring_boundary"] = "PENDING_LIFECYCLE_DEFAULT_OFF_INTERNAL_TRUTH_SCORER_NO_PROMOTION_OR_LIVE_EFFECT"
    row["pending_lifecycle_source_decision_status"] = "SOURCE_COMPLETE_R_COMPUTABLE_IMPLEMENT_DEFAULT_OFF"
    row["pending_lifecycle_source_complete_r_counted"] = True


def convert_complete_r_missing(row: dict[str, Any], *, generated_utc: str) -> None:
    apply_common(row, generated_utc=generated_utc)
    row["action_class"] = "REDESIGN"
    row["branch_decision"] = REDESIGN_R_REQUIRED
    row["current_action"] = REDESIGN_R_REQUIRED
    row["strategy_status"] = REDESIGN_R_REQUIRED
    row["implementation_decision"] = REDESIGN_R_REQUIRED
    row["implementation_candidate"] = "REPAIR_PENDING_LIFECYCLE_FILLED_OR_RETRY_R_OUTCOME_SOURCE"
    row["decision_evidence"] = "PENDING_LIFECYCLE_SOURCE_COMPLETE_BUT_R_OUTCOME_NOT_COMPUTABLE"
    row["scoring_boundary"] = "PENDING_LIFECYCLE_SOURCE_COMPLETE_BUT_R_OUTCOME_REQUIRED_BEFORE_IMPLEMENTATION"
    row["pending_lifecycle_source_decision_status"] = "SOURCE_COMPLETE_R_MISSING_REDESIGN_REPAIR"
    row["opportunity_owner_row_id"] = row.get("row_id")
    row["opportunity_owner_source_artifact"] = row.get("source_artifact")
    row["opportunity_proxy_reference_status"] = "NO_PROXY_R_REFERENCE_SOURCE_COMPLETE_R_MISSING"
    row["opportunity_not_independently_countable_reason"] = (
        "Pending lifecycle source fields are complete, but the row lacks computable pending lifecycle R; "
        "do not implement until filled/retry/exit R source is repaired."
    )
    row["opportunity_useful_mechanism"] = (
        "The source-complete pending lifecycle telemetry remains useful for fill/cancel state scoring, but "
        "the R outcome source must be repaired before implementation."
    )
    row["opportunity_downstream_paths"] = ["source requirement", "redesign", "broader system component"]
    row["missed_opportunity_audit"] = audit_payload(
        row,
        decision_branch=REDESIGN_R_REQUIRED,
        preserve_as="PENDING_LIFECYCLE_R_OUTCOME_SOURCE_REPAIR",
        next_route="REPAIR_PENDING_LIFECYCLE_FILLED_RETRY_OR_EXIT_R_OUTCOME_SOURCE",
        unsupported_reason="SOURCE_FIELDS_COMPLETE_BUT_PENDING_LIFECYCLE_R_IS_NOT_COMPUTABLE",
    )


def convert_canonical_partial(row: dict[str, Any], *, generated_utc: str) -> None:
    apply_common(row, generated_utc=generated_utc)
    reference = safe_float(row.get("after_proxy_r"))
    row["opportunity_proxy_r_reference"] = reference
    row["after_proxy_r"] = None
    row["action_class"] = "REDESIGN"
    row["branch_decision"] = REDESIGN_SOURCE_PARTIAL
    row["current_action"] = REDESIGN_SOURCE_PARTIAL
    row["strategy_status"] = REDESIGN_SOURCE_PARTIAL
    row["implementation_decision"] = REDESIGN_SOURCE_PARTIAL
    row["implementation_candidate"] = "REPAIR_PENDING_LIFECYCLE_SCORER_SOURCE_FIELDS_OR_MERGE_WITH_ENTRY_GEOMETRY"
    row["decision_evidence"] = "PENDING_LIFECYCLE_INTERNAL_TRUTH_HAS_PARTIAL_SOURCE_FIELDS"
    row["scoring_boundary"] = "PENDING_LIFECYCLE_PARTIAL_SOURCE_ROW_REMOVED_FROM_IMPLEMENTATION_PROXY_DENOMINATOR"
    row["pending_lifecycle_source_decision_status"] = "CANONICAL_SOURCE_PARTIAL_REDESIGN_REPAIR_REQUIRED"
    row["pending_lifecycle_proxy_reference_counted_as_r"] = False
    row["opportunity_owner_row_id"] = row.get("row_id")
    row["opportunity_owner_source_artifact"] = row.get("source_artifact")
    row["opportunity_proxy_reference_status"] = "REFERENCE_ONLY_NOT_COUNTED_SOURCE_PARTIAL"
    row["opportunity_not_independently_countable_reason"] = (
        "The current row has internal pending lifecycle truth but still lacks complete source/cost fields; "
        "its zero-R proxy is preserved only as reference until source repair is complete."
    )
    row["opportunity_useful_mechanism"] = (
        "The row identifies the exact market-reopen/tick-source gap and remains useful for pending lifecycle "
        "source-capture repair and entry/fillability controls."
    )
    row["opportunity_downstream_paths"] = ["source requirement", "redesign", "context feature", "broader system component"]
    row["missed_opportunity_audit"] = audit_payload(
        row,
        decision_branch=REDESIGN_SOURCE_PARTIAL,
        preserve_as="PENDING_LIFECYCLE_SOURCE_REPAIR_REQUIREMENT",
        next_route="REPAIR_PENDING_LIFECYCLE_DECISION_SPREAD_SOURCE_FOR_MARKET_REOPEN_GAP",
        unsupported_reason="SOURCE_FIELDS_PARTIAL_AFTER_NOFILL_FORWARD_AND_TICK_RECONSTRUCTION_REPAIR",
    )


def convert_duplicate_partial(
    row: dict[str, Any],
    *,
    generated_utc: str,
    canonical_owner: dict[str, Any] | None,
) -> None:
    apply_common(row, generated_utc=generated_utc)
    row["action_class"] = "REDESIGN"
    row["branch_decision"] = MERGE_DUPLICATE_DERIVATION
    row["current_action"] = MERGE_DUPLICATE_DERIVATION
    row["strategy_status"] = MERGE_DUPLICATE_DERIVATION
    row["implementation_decision"] = MERGE_DUPLICATE_DERIVATION
    row["implementation_candidate"] = "MERGE_PENDING_SOURCE_DERIVATION_ROW_INTO_CANONICAL_PENDING_LIFECYCLE_SCORER"
    row["decision_evidence"] = (
        "PENDING_SOURCE_DERIVATION_ROW_DUPLICATES_CANONICAL_PENDING_LIFECYCLE_SCORER_OWNER"
    )
    row["scoring_boundary"] = "NO_DUPLICATE_R_FOR_PENDING_LIFECYCLE_SOURCE_DERIVATION_COPY"
    row["pending_lifecycle_source_decision_status"] = "DUPLICATE_SOURCE_DERIVATION_MERGED_TO_CANONICAL_OWNER"
    row["pending_lifecycle_proxy_reference_counted_as_r"] = False
    row["opportunity_owner_row_id"] = (canonical_owner or {}).get("row_id") or row.get("row_id")
    row["opportunity_owner_source_artifact"] = (canonical_owner or {}).get("source_artifact") or row.get("source_artifact")
    row["opportunity_proxy_r_reference"] = row.get("merged_duplicate_proxy_reference_r")
    row["opportunity_proxy_reference_status"] = "MERGED_DUPLICATE_REFERENCE_ONLY_NOT_COUNTED"
    row["opportunity_not_independently_countable_reason"] = (
        "This source-derivation row duplicates the canonical pending lifecycle scorer candidate; "
        "counting it independently would double-count the same opportunity."
    )
    row["opportunity_useful_mechanism"] = (
        "The duplicate row preserves source-derivation provenance and pending lifecycle metadata for the "
        "canonical scorer owner, source repair, and broader fillability diagnostics."
    )
    row["opportunity_downstream_paths"] = ["merge", "source requirement", "context feature", "broader system component"]
    row["missed_opportunity_audit"] = audit_payload(
        row,
        decision_branch=MERGE_DUPLICATE_DERIVATION,
        preserve_as="MERGED_PENDING_LIFECYCLE_SOURCE_DERIVATION_COMPONENT",
        next_route="USE_CANONICAL_PENDING_LIFECYCLE_SCORER_OWNER_FOR_IMPLEMENTATION_AND_SOURCE_REPAIR",
        unsupported_reason="DUPLICATE_SOURCE_DERIVATION_ROW_NOT_INDEPENDENTLY_COUNTABLE",
    )


def convert_row(
    row: dict[str, Any],
    *,
    generated_utc: str,
    canonical_map: dict[str, dict[str, Any]],
) -> None:
    branch = row.get("branch_decision")
    proxy = safe_float(row.get("after_proxy_r"))
    if branch in {OLD_COMPLETE_RECONSTRUCTED, OLD_COMPLETE_CAPTURE}:
        if proxy is None:
            convert_complete_r_missing(row, generated_utc=generated_utc)
        else:
            convert_complete_numeric(row, generated_utc=generated_utc)
        return
    if branch in {OLD_PARTIAL_DERIVED, OLD_PARTIAL_FORWARD}:
        if row.get("strategy_id") == "PENDING_LIMIT_LIFECYCLE":
            convert_canonical_partial(row, generated_utc=generated_utc)
        else:
            canonical_owner = canonical_map.get(str(row.get("candidate_id") or ""))
            convert_duplicate_partial(row, generated_utc=generated_utc, canonical_owner=canonical_owner)
        return
    raise ValueError(f"unexpected target branch: {branch}")


def build() -> dict[str, Any]:
    generated_utc = utc_now()
    input_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    canonical_map = canonical_pending_by_candidate(input_rows)
    before_counts = Counter(str(row.get("action_class") or "") for row in input_rows)
    before_proxy = proxy_summary(input_rows)
    output_rows: list[dict[str, Any]] = []
    converted: list[dict[str, Any]] = []

    for source_row in input_rows:
        row = {key: value for key, value in source_row.items() if key != "_source_line_no"}
        if is_old_target(row):
            convert_row(row, generated_utc=generated_utc, canonical_map=canonical_map)
            converted.append(row)
        else:
            row["pending_lifecycle_source_decision_status"] = "NOT_TARGET_ROW"
        output_rows.append(row)

    after_counts = Counter(str(row.get("action_class") or "") for row in output_rows)
    after_proxy = proxy_summary(output_rows)
    removed_proxy_refs = [
        value
        for row in converted
        if row.get("pending_lifecycle_source_decision_status") == "CANONICAL_SOURCE_PARTIAL_REDESIGN_REPAIR_REQUIRED"
        if (value := safe_float(row.get("opportunity_proxy_r_reference"))) is not None
    ]
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
        "pending_lifecycle_source_decision_rows": len(converted),
        "rows_removed_from_keep": sum(row.get("before_pending_lifecycle_source_action_class") == "KEEP" for row in converted),
        "source_complete_rows_reclassified": sum(
            row.get("before_pending_lifecycle_source_branch_decision")
            in {OLD_COMPLETE_RECONSTRUCTED, OLD_COMPLETE_CAPTURE}
            for row in converted
        ),
        "source_complete_numeric_implemented_rows": sum(
            row.get("pending_lifecycle_source_decision_status") == "SOURCE_COMPLETE_R_COMPUTABLE_IMPLEMENT_DEFAULT_OFF"
            for row in converted
        ),
        "source_complete_r_missing_redesign_rows": sum(
            row.get("pending_lifecycle_source_decision_status") == "SOURCE_COMPLETE_R_MISSING_REDESIGN_REPAIR"
            for row in converted
        ),
        "canonical_partial_source_repair_rows": sum(
            row.get("pending_lifecycle_source_decision_status") == "CANONICAL_SOURCE_PARTIAL_REDESIGN_REPAIR_REQUIRED"
            for row in converted
        ),
        "duplicate_source_derivation_merged_rows": sum(
            row.get("pending_lifecycle_source_decision_status") == "DUPLICATE_SOURCE_DERIVATION_MERGED_TO_CANONICAL_OWNER"
            for row in converted
        ),
        "rows_added_to_implementation": sum(row.get("action_class") == "IMPLEMENT_DEFAULT_OFF" for row in converted),
        "rows_added_to_redesign": sum(row.get("action_class") == "REDESIGN" for row in converted),
        "proxy_rows_removed_from_counted_denominator": len(removed_proxy_refs),
        "proxy_r_sum_removed_from_counted_denominator": round(sum(removed_proxy_refs), 8),
        "pending_lifecycle_proxy_reference_rows_not_counted": sum(
            safe_float(row.get("opportunity_proxy_r_reference")) is not None
            and row.get("pending_lifecycle_proxy_reference_counted_as_r") is False
            for row in converted
        ),
        "remaining_old_pending_keep_branch_rows": sum(
            row.get("branch_decision")
            in {OLD_COMPLETE_RECONSTRUCTED, OLD_COMPLETE_CAPTURE, OLD_PARTIAL_DERIVED, OLD_PARTIAL_FORWARD}
            for row in output_rows
        ),
        "pending_lifecycle_decision_branch_counts": dict(
            sorted(Counter(row.get("branch_decision") for row in converted).items())
        ),
        "redesign_missing_audit_after": sum(
            row.get("action_class") == "REDESIGN" and not isinstance(row.get("missed_opportunity_audit"), dict)
            for row in output_rows
        ),
        "redesign_missing_underlying_intel_after": sum(
            row.get("action_class") == "REDESIGN" and row.get("underlying_intelligence_preserved") is not True
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
        "description": "Pending lifecycle source-completeness action decision materialization.",
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
            "pending_lifecycle_source_decision_rows": len(converted),
            "source_complete_numeric_implemented_rows": summary["source_complete_numeric_implemented_rows"],
            "source_complete_r_missing_redesign_rows": summary["source_complete_r_missing_redesign_rows"],
            "canonical_partial_source_repair_rows": summary["canonical_partial_source_repair_rows"],
            "duplicate_source_derivation_merged_rows": summary["duplicate_source_derivation_merged_rows"],
            "numeric_proxy_rows_after": summary["numeric_proxy_rows_after"],
            "proxy_r_sum_after": summary["proxy_r_sum_after"],
        },
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
