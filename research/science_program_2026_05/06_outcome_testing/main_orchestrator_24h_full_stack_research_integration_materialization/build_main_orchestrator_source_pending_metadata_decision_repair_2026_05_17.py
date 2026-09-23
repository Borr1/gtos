"""Repair SOURCE M15 and pending-lifecycle decision metadata.

This plate consumes the current far-miss retest-control action queue and
converts the remaining SOURCE/pending nonterminal metadata into concrete
implementation, kill, keep, or preserve decisions. It does not change proxy R,
exact R, live behavior, or shadow logs.
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

INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_FAR_MISS_RETEST_CONTROL_DECISION_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PREFILL_FAR_MISS_RETEST_CONTROL_DECISION_SUMMARY_{DATE}.json"
PENDING_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_PENDING_LIFECYCLE_SOURCE_DERIVATION_RECOMPUTE_SUMMARY_2026-05-16.json"
SOURCE_M15_SUMMARY = ROUTE_DIR / "MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_SUMMARY_2026-05-16.json"

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_PENDING_METADATA_DECISION_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_PENDING_METADATA_DECISION_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_PENDING_METADATA_DECISION_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


SOURCE_M15_DECISIONS: dict[str, dict[str, str]] = {
    "DOWNGRADE_OR_AVOID_ACCEPTED_SOURCE_BRANCH": {
        "action_class": "KILL",
        "branch_decision": "KILL_OR_AVOID_ACCEPTED_SOURCE_BRANCH_UNTIL_EXACT_SOURCE_REPAIR",
        "decision_evidence": "BAR_SPREAD_PROXY_DEGRADED_ACCEPTED_SOURCE_BRANCH_EXACT_TICK_GAP_PRESERVED",
        "scoring_boundary": "NO_SOURCE_BRANCH_IMPLEMENTATION_WHEN_BAR_SPREAD_PROXY_DEGRADES_ACCEPTED_ROW",
        "implementation_candidate": "NONE_KILL_OR_AVOID_UNTIL_EXACT_SOURCE_REPAIR",
        "coverage_status": "KILLED_WITH_CURRENT_PROXY_EVIDENCE",
    },
    "KEEP_REPAIR_OR_AVOID_DECISION": {
        "action_class": "IMPLEMENT_DEFAULT_OFF",
        "branch_decision": "IMPLEMENT_DEFAULT_OFF_SOURCE_REPAIR_CONFIRMED_BAR_SPREAD_PROXY",
        "decision_evidence": "BAR_SPREAD_PROXY_REPAIR_CONFIRMED_EXACT_TICK_GAP_PRESERVED",
        "scoring_boundary": "SOURCE_REPAIR_CONFIRMED_BAR_SPREAD_PROXY_NO_EXACT_TICK_OR_PROMOTION_CLAIM",
        "implementation_candidate": "IMPLEMENT_DEFAULT_OFF_SOURCE_REPAIR_BAR_SPREAD_PROXY_OBSERVABLE_CANDIDATE",
        "coverage_status": "OBSERVABLE_CANDIDATE_READY_DEFAULT_OFF",
    },
    "UPGRADE_REPAIR_TO_SOURCE_CHALLENGER_REVIEW": {
        "action_class": "IMPLEMENT_DEFAULT_OFF",
        "branch_decision": "IMPLEMENT_DEFAULT_OFF_SOURCE_REPAIR_UPGRADED_CHALLENGER",
        "decision_evidence": "BAR_SPREAD_PROXY_UPGRADED_REPAIR_BRANCH_TO_SOURCE_CHALLENGER",
        "scoring_boundary": "SOURCE_REPAIR_DEFAULT_OFF_CHALLENGER_WITHOUT_EXACT_CHRONOLOGY_OR_PROMOTION",
        "implementation_candidate": "IMPLEMENT_DEFAULT_OFF_SOURCE_REPAIR_CHALLENGER_REPLAY_SCORER",
        "coverage_status": "OBSERVABLE_CANDIDATE_READY_DEFAULT_OFF",
    },
    "KEEP_SOURCE_REPAIR_WITH_M15_ORDERING_INTERVAL_BOUND": {
        "action_class": "PRESERVE_REQUIREMENT",
        "branch_decision": "PRESERVE_SOURCE_REPAIR_INTERVAL_BOUND_EXACT_ORDERING_REQUIRED",
        "decision_evidence": "M15_ORDERING_REPAIR_INTERVAL_STRADDLES_ZERO",
        "scoring_boundary": "INTERVAL_STRADDLES_ZERO_NO_SCALAR_IMPLEMENTATION_DECISION",
        "implementation_candidate": "PRESERVE_REQUIRE_EXACT_TICK_ORDERING_OR_STRONGER_SOURCE_REPLAY",
        "coverage_status": "PRESERVED_SOURCE_REQUIREMENT_ONLY",
    },
    "KEEP_SOURCE_ACCEPTED_AFTER_M15_ORDERING_POSITIVE_PROXY": {
        "action_class": "KEEP",
        "branch_decision": "KEEP_SOURCE_ACCEPTED_AFTER_M15_ORDERING_POSITIVE_PROXY",
        "decision_evidence": "M15_ORDERING_REPAIR_COMPUTED_POSITIVE_BOUNDED_PROXY_MIDPOINT",
        "scoring_boundary": "BOUNDED_M15_ORDERING_PROXY_NO_EXACT_CHRONOLOGY_OR_PROMOTION",
        "implementation_candidate": "KEEP_SOURCE_ACCEPTED_REPLAY_QUEUE_WITH_BOUNDED_POSITIVE_M15_PROXY",
        "coverage_status": "KEPT_WITH_CURRENT_EVIDENCE",
    },
    "KEEP_SOURCE_ACCEPTED_CONFIRMED_CHALLENGER_REPLAY_QUEUE": {
        "action_class": "KEEP",
        "branch_decision": "KEEP_SOURCE_ACCEPTED_CONFIRMED_CHALLENGER_REPLAY_QUEUE",
        "decision_evidence": "SOURCE_ACCEPTED_CONFIRMED_BY_BAR_SPREAD_PROXY",
        "scoring_boundary": "SOURCE_ACCEPTED_BAR_SPREAD_PROXY_NO_EXACT_TICK_OR_PROMOTION_CLAIM",
        "implementation_candidate": "KEEP_SOURCE_ACCEPTED_CONFIRMED_DEFAULT_OFF_REPLAY_QUEUE",
        "coverage_status": "KEPT_WITH_CURRENT_EVIDENCE",
    },
    "KILL_SOURCE_REPAIR_UPGRADED_CHALLENGER_AFTER_ORDERING_NEGATIVE_PROXY": {
        "action_class": "KILL",
        "branch_decision": "KILL_SOURCE_REPAIR_UPGRADED_CHALLENGER_AFTER_ORDERING_NEGATIVE_PROXY",
        "decision_evidence": "M15_ORDERING_REPAIR_COMPUTED_NEGATIVE_BOUNDED_PROXY_MIDPOINT",
        "scoring_boundary": "NEGATIVE_BOUNDED_M15_PROXY_KILLS_SOURCE_CHALLENGER_NO_PROMOTION",
        "implementation_candidate": "NONE_KILL_SOURCE_CHALLENGER_AFTER_NEGATIVE_ORDERING_PROXY",
        "coverage_status": "KILLED_WITH_CURRENT_PROXY_EVIDENCE",
    },
    "PRESERVE_SOURCE_REPAIR_UPGRADED_INTERVAL_BOUND_NO_CHALLENGER": {
        "action_class": "PRESERVE_REQUIREMENT",
        "branch_decision": "PRESERVE_SOURCE_REPAIR_UPGRADED_INTERVAL_BOUND_NO_CHALLENGER",
        "decision_evidence": "M15_ORDERING_REPAIR_INTERVAL_STRADDLES_ZERO_NO_CHALLENGER_DECISION",
        "scoring_boundary": "INTERVAL_STRADDLES_ZERO_NO_CHALLENGER_IMPLEMENTATION",
        "implementation_candidate": "PRESERVE_INTERVAL_BOUND_REQUIRE_EXACT_TICK_ORDERING",
        "coverage_status": "PRESERVED_SOURCE_REQUIREMENT_ONLY",
    },
    "PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR": {
        "action_class": "PRESERVE_REQUIREMENT",
        "branch_decision": "PRESERVE_SOURCE_REQUIREMENT_NO_SCALAR",
        "decision_evidence": "SOURCE_REQUIREMENT_HAS_NO_SCALAR_CURRENT_DISK_PROXY",
        "scoring_boundary": "NO_SOURCE_SCALAR_PROXY_R_AVAILABLE_FROM_CURRENT_ARTIFACTS",
        "implementation_candidate": "PRESERVE_EXACT_SOURCE_REQUIREMENT_NO_SCALAR_DECISION",
        "coverage_status": "PRESERVED_SOURCE_REQUIREMENT_ONLY",
    },
}

PENDING_DECISIONS: dict[str, dict[str, str]] = {
    "KEEP_PENDING_LIFECYCLE_HYPOTHETICAL_PATH_SCORER": {
        "action_class": "KEEP",
        "decision_evidence": "NO_LIVE_PENDING_LIMIT_INTENT_SCORE_SHARED_CANDIDATE_PATH_ONLY",
        "scoring_boundary": "HYPOTHETICAL_PENDING_LIMIT_PATH_PROXY_NOT_LIVE_LIFECYCLE_TRUTH",
        "implementation_candidate": "KEEP_HYPOTHETICAL_PENDING_LIMIT_PATH_SCORER_NO_LIFECYCLE_SOURCE_REQUIRED",
        "coverage_status": "KEPT_WITH_CURRENT_EVIDENCE",
    },
    "KEEP_PENDING_LIFECYCLE_SCORER_WITH_DERIVED_SOURCE_FIELDS_CURRENT_ROWS_PARTIAL": {
        "action_class": "KEEP",
        "decision_evidence": "PENDING_LIFECYCLE_INTERNAL_TRUTH_WITH_SOURCE_SAFE_DERIVED_FIELDS",
        "scoring_boundary": "PENDING_LIFECYCLE_R_UNCHANGED_SOURCE_FIELDS_PARTIAL_NO_EXACT_BROKER_R",
        "implementation_candidate": (
            "KEEP_PENDING_LIFECYCLE_SCORER_WITH_DERIVED_FIELDS_AND_FORWARD_CAPTURE_MISSING_SPREAD_FIELDS"
        ),
        "coverage_status": "KEPT_WITH_CURRENT_EVIDENCE",
    },
    "KEEP_PENDING_LIFECYCLE_SCORER_FORWARD_CAPTURE_FIELDS_IMPLEMENTED_CURRENT_ROWS_PARTIAL": {
        "action_class": "KEEP",
        "decision_evidence": "PENDING_LIFECYCLE_FORWARD_CAPTURE_FIELDS_IMPLEMENTED_CURRENT_ROWS_PARTIAL",
        "scoring_boundary": "PENDING_LIFECYCLE_R_UNCHANGED_FORWARD_CAPTURE_FIELDS_PARTIAL",
        "implementation_candidate": "KEEP_PENDING_LIFECYCLE_SCORER_AND_FORWARD_CAPTURE_MISSING_SOURCE_FIELDS",
        "coverage_status": "KEPT_WITH_CURRENT_EVIDENCE",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            row = json.loads(stripped)
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


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "") for row in rows))


def has_metadata_gap(row: dict[str, Any]) -> bool:
    return (
        row.get("decision_evidence") in (None, "")
        or row.get("scoring_boundary") in (None, "")
        or row.get("implementation_candidate") in (None, "")
        or str(row.get("current_action")) in {"None", "False", ""}
        or str(row.get("next_action")) in {"None", "False", ""}
    )


def is_pending_derivation_row(row: dict[str, Any]) -> bool:
    return row.get("source_plate") == "pending_lifecycle_source_derivation_recompute"


def is_source_m15_row(row: dict[str, Any]) -> bool:
    return row.get("source_plate") == "source_m15_ordering_repair"


def apply_source_m15_decision(row: dict[str, Any]) -> bool:
    original_branch = str(row.get("branch_decision") or row.get("implementation_decision") or "")
    decision = SOURCE_M15_DECISIONS.get(original_branch)
    if not decision:
        return False
    row["before_metadata_repair_action_class"] = row.get("action_class")
    row["before_metadata_repair_branch_decision"] = original_branch
    row["before_metadata_repair_current_action"] = row.get("current_action")
    row["before_metadata_repair_implementation_candidate"] = row.get("implementation_candidate")
    row["source_pending_metadata_repair_status"] = "REPAIRED_SOURCE_M15_BRANCH_DECISION_METADATA"
    for key, value in decision.items():
        row[key] = value
    row["implementation_decision"] = decision["branch_decision"]
    row["current_action"] = decision["implementation_candidate"]
    row["next_action"] = decision["implementation_candidate"]
    return True


def apply_pending_decision(row: dict[str, Any]) -> bool:
    original_branch = str(row.get("branch_decision") or row.get("implementation_decision") or "")
    decision = PENDING_DECISIONS.get(original_branch)
    if not decision:
        return False
    row["before_metadata_repair_action_class"] = row.get("action_class")
    row["before_metadata_repair_branch_decision"] = original_branch
    row["before_metadata_repair_current_action"] = row.get("current_action")
    row["before_metadata_repair_implementation_candidate"] = row.get("implementation_candidate")
    row["source_pending_metadata_repair_status"] = "REPAIRED_PENDING_LIFECYCLE_DECISION_METADATA"
    for key, value in decision.items():
        row[key] = value
    row["branch_decision"] = original_branch
    row["implementation_decision"] = original_branch
    row["current_action"] = decision["implementation_candidate"]
    row["next_action"] = decision["implementation_candidate"]
    return True


def backfill_generic_implementation_candidate(row: dict[str, Any]) -> bool:
    if row.get("implementation_candidate") not in (None, ""):
        return False
    candidate = row.get("implementation_decision") or row.get("current_action") or row.get("branch_decision")
    if candidate in (None, "", "None", "False"):
        return False
    row["before_metadata_repair_implementation_candidate"] = row.get("implementation_candidate")
    row["implementation_candidate"] = str(candidate)
    row["source_pending_metadata_repair_status"] = "BACKFILLED_IMPLEMENTATION_CANDIDATE_FROM_EXISTING_DECISION"
    return True


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [
        value
        for row in rows
        if (value := safe_float(row.get("after_proxy_r"))) is not None
    ]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "proxy_r_mean": round(sum(values) / len(values), 8) if values else None,
    }


def repair_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    repaired: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    generated = utc_now()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        before_gap = has_metadata_gap(row)
        changed = False
        if is_source_m15_row(row):
            changed = apply_source_m15_decision(row)
            if changed:
                stats["source_m15_decision_rows_repaired"] += 1
        elif is_pending_derivation_row(row):
            changed = apply_pending_decision(row)
            if changed:
                stats["pending_lifecycle_decision_rows_repaired"] += 1
        if backfill_generic_implementation_candidate(row):
            stats["generic_implementation_candidate_backfills"] += 1
            changed = True
        if not row.get("source_pending_metadata_repair_status"):
            row["source_pending_metadata_repair_status"] = "NOT_TARGET_ROW"
        if before_gap:
            stats["metadata_gap_rows_before"] += 1
        if has_metadata_gap(row):
            stats["metadata_gap_rows_after"] += 1
        if changed:
            stats["rows_changed"] += 1
        repaired.append(row)
    return repaired, dict(stats)


def action_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    keys = sorted(set(before) | set(after))
    return {
        key: int(after.get(key, 0)) - int(before.get(key, 0))
        for key in keys
        if int(after.get(key, 0)) != int(before.get(key, 0))
    }


def build_manifest(output_paths: list[Path]) -> dict[str, Any]:
    inputs = [INPUT_LEDGER, INPUT_SUMMARY, PENDING_SUMMARY, SOURCE_M15_SUMMARY]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
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
    pending_summary = read_json(PENDING_SUMMARY)
    source_m15_summary = read_json(SOURCE_M15_SUMMARY)
    output_rows, repair_stats = repair_rows(input_rows)

    write_jsonl(OUTPUT_LEDGER, output_rows)

    before_actions = counter(input_rows, "action_class")
    after_actions = counter(output_rows, "action_class")
    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    source_rows = [row for row in output_rows if is_source_m15_row(row)]
    pending_rows = [row for row in output_rows if is_pending_derivation_row(row)]
    source_pending_rows = source_rows + pending_rows
    target_metadata_gaps_after = sum(1 for row in source_pending_rows if has_metadata_gap(row))
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_SOURCE_PENDING_METADATA_DECISION_REPAIR",
        "claim_boundary": (
            "Decision-metadata repair and branch-action conversion for SOURCE M15 ordering and "
            "pending-lifecycle source derivation rows. Proxy R and exact R are unchanged; no live "
            "behavior, shadow append, validation, promotion, broker operation, or AI/API call is opened."
        ),
        "rows": len(output_rows),
        "source_m15_rows": len(source_rows),
        "pending_lifecycle_source_derivation_rows": len(pending_rows),
        "source_pending_target_rows": len(source_pending_rows),
        "source_pending_metadata_gaps_after": target_metadata_gaps_after,
        "repair_stats": repair_stats,
        "action_class_counts_before": before_actions,
        "action_class_counts_after": after_actions,
        "action_class_delta_vs_previous": action_delta(before_actions, after_actions),
        "source_m15_action_class_counts_after": counter(source_rows, "action_class"),
        "pending_lifecycle_action_class_counts_after": counter(pending_rows, "action_class"),
        "branch_decision_counts_after": counter(output_rows, "branch_decision"),
        "source_pending_branch_decision_counts_after": counter(source_pending_rows, "branch_decision"),
        "metadata_repair_status_counts": counter(output_rows, "source_pending_metadata_repair_status"),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "source_m15_proxy_midpoint_sum": source_m15_summary.get("ordering_proxy_midpoint_sum"),
        "source_m15_repair_rows": source_m15_summary.get("rows"),
        "source_m15_ordering_repaired_rows": source_m15_summary.get("m15_ordering_repaired_rows"),
        "pending_lifecycle_after_derived_source_field_cells": pending_summary.get("after_derived_source_field_cells"),
        "pending_lifecycle_after_missing_source_field_cells": pending_summary.get("after_missing_source_field_cells"),
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": (
            "SOURCE_M15_AND_PENDING_LIFECYCLE_NONTERMINAL_METADATA_CONVERTED_TO_CONCRETE_DECISIONS"
        ),
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "source_pending_target_rows": len(source_pending_rows),
                "target_metadata_gaps_after": target_metadata_gaps_after,
                "summary": str(OUTPUT_SUMMARY),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
