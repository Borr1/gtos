"""Consume pending tick-spread repair into the current action ledger."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(ROUTE_DIR)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from build_main_orchestrator_pending_lifecycle_decision_spread_repair_2026_05_17 import (  # noqa: E402
    PENDING_LIMIT_STRATEGY_ID,
    SAFE_FLAGS,
    counter,
    kill_audit_present,
    proxy_summary,
    read_json,
    read_jsonl,
    safe_float,
    sha256_file,
    utc_now,
    write_json,
    write_jsonl,
)


INPUT_ACTION_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_SELECTION_LEDGER_{DATE}.jsonl"
INPUT_ACTION_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_IMPLEMENTATION_SELECTION_SUMMARY_{DATE}.json"
PENDING_TICK_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_LEDGER_{DATE}.jsonl"
PENDING_TICK_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_SUMMARY_{DATE}.json"
PENDING_TICK_SOURCE_LEDGER = ROUTE_DIR / (
    f"MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_SOURCE_LEDGER_{DATE}.jsonl"
)
KILL_SCOPE_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_KILL_SCOPE_PRESERVATION_AUDIT_LEDGER_{DATE}.jsonl"
BUILDER_SOURCE = (
    ROUTE_DIR / "build_main_orchestrator_action_after_pending_tick_spread_repair_2026_05_17.py"
)

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / (
    f"MAIN_ORCH24_ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
)

PENDING_UPDATE_FIELDS = (
    "branch_decision",
    "decision_evidence",
    "scoring_boundary",
    "implementation_candidate",
    "implementation_decision",
    "current_action",
    "next_action",
    "after_proxy_r",
    "pending_lifecycle_decision_spread_value_source_safe",
    "pending_lifecycle_decision_spread_unit",
    "pending_lifecycle_decision_spread_reconstruction_source",
    "pending_lifecycle_decision_spread_reconstruction_source_created_at_utc",
    "pending_lifecycle_decision_spread_reconstruction_source_status",
    "pending_lifecycle_decision_spread_reconstruction_tick_ts_utc",
    "pending_lifecycle_decision_spread_reconstruction_tick_offset_seconds",
    "pending_lifecycle_decision_spread_reconstruction_tick_source_path",
    "pending_lifecycle_decision_spread_reconstruction_tick_source_sha256",
    "pending_lifecycle_source_capture_statuses",
    "pending_lifecycle_source_capture_derivations",
    "pending_lifecycle_source_capture_complete",
    "pending_lifecycle_tick_spread_reconstruction_status",
    "pending_lifecycle_tick_spread_reconstruction_attempt_status",
    "pending_lifecycle_tick_spread_reconstruction_attempt_source_path",
    "pending_lifecycle_tick_spread_reconstruction_attempt_source_requirement",
)

KILL_AUDIT_FIELDS = (
    "missed_opportunity_audit",
    "claim_decision_scope",
    "underlying_intelligence_preserved",
    "current_claim_proxy_counted",
    "data_requirement_state",
    "preserved_candidate_path_outcome_source",
    "preserved_candidate_path_outcome_status",
    "kill_scope_preservation_audit_status",
)


def pending_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("candidate_id") or ""): row
        for row in rows
        if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID and row.get("candidate_id")
    }


def row_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("candidate_id") or ""), str(row.get("strategy_id") or ""))


def kill_audit_map(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {row_key(row): row for row in rows if row.get("action_class") == "KILL" and kill_audit_present(row)}


def pending_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID]


def pending_decision_spread_status(row: dict[str, Any]) -> str:
    statuses = row.get("pending_lifecycle_source_capture_statuses")
    if not isinstance(statuses, dict):
        return "NO_PENDING_LIFECYCLE_STATUS_MAP"
    return str(statuses.get("decision_spread_value_source_safe") or "")


def mark_before(row: dict[str, Any]) -> None:
    for field in PENDING_UPDATE_FIELDS:
        row[f"before_pending_tick_action_{field}"] = row.get(field)


def materialize_rows(
    action_rows: list[dict[str, Any]],
    tick_rows_by_candidate: dict[str, dict[str, Any]],
    kill_audits: dict[tuple[str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    output = []
    stats: Counter[str] = Counter()
    generated = utc_now()
    for source in action_rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if row.get("action_class") == "KILL" and not kill_audit_present(row):
            audit_source = kill_audits.get(row_key(row))
            if audit_source:
                for field in KILL_AUDIT_FIELDS:
                    if field in audit_source:
                        row[field] = audit_source.get(field)
                row["action_after_pending_tick_kill_audit_status"] = "KILL_AUDIT_RESTORED_FROM_SCOPE_LEDGER"
                stats["kill_audit_restored"] += 1
            else:
                row["action_after_pending_tick_kill_audit_status"] = "KILL_AUDIT_SOURCE_NOT_FOUND"
                stats["kill_audit_missing"] += 1
        elif row.get("action_class") == "KILL":
            row["action_after_pending_tick_kill_audit_status"] = "KILL_AUDIT_ALREADY_PRESENT"
        if row.get("strategy_id") != PENDING_LIMIT_STRATEGY_ID:
            row["action_after_pending_tick_spread_repair_status"] = "NOT_PENDING_LIFECYCLE_ROW"
            output.append(row)
            continue
        stats["pending_rows"] += 1
        mark_before(row)
        scorer = tick_rows_by_candidate.get(str(row.get("candidate_id") or ""))
        if scorer is None:
            row["action_after_pending_tick_spread_repair_status"] = "PENDING_TICK_REPAIR_ROW_MISSING"
            stats["missing_pending_tick_row"] += 1
            output.append(row)
            continue
        for field in PENDING_UPDATE_FIELDS:
            if field in scorer:
                row[field] = scorer.get(field)
        if row.get("before_pending_tick_action_branch_decision") != row.get("branch_decision"):
            stats["branch_changed"] += 1
        if (
            row.get("before_pending_tick_action_pending_lifecycle_source_capture_complete")
            != row.get("pending_lifecycle_source_capture_complete")
        ):
            stats["source_capture_complete_changed"] += 1
        if (
            row.get("before_pending_tick_action_pending_lifecycle_decision_spread_reconstruction_source")
            != row.get("pending_lifecycle_decision_spread_reconstruction_source")
        ):
            stats["spread_reconstruction_source_changed"] += 1
        if safe_float(row.get("before_pending_tick_action_after_proxy_r")) != safe_float(row.get("after_proxy_r")):
            stats["proxy_changed"] += 1
        row["action_after_pending_tick_spread_repair_status"] = (
            row.get("pending_lifecycle_tick_spread_reconstruction_status")
            or "PENDING_LIFECYCLE_NO_TICK_REPAIR_STATUS"
        )
        stats[str(row["action_after_pending_tick_spread_repair_status"])] += 1
        output.append(row)
    return output, dict(stats)


def build_manifest(output_paths: list[Path]) -> dict[str, Any]:
    inputs = [
        INPUT_ACTION_LEDGER,
        INPUT_ACTION_SUMMARY,
        PENDING_TICK_LEDGER,
        PENDING_TICK_SUMMARY,
        PENDING_TICK_SOURCE_LEDGER,
        KILL_SCOPE_LEDGER,
        BUILDER_SOURCE,
    ]
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
    action_rows = read_jsonl(INPUT_ACTION_LEDGER)
    action_summary = read_json(INPUT_ACTION_SUMMARY)
    tick_rows = read_jsonl(PENDING_TICK_LEDGER)
    tick_summary = read_json(PENDING_TICK_SUMMARY)
    output_rows, stats = materialize_rows(
        action_rows,
        pending_map(tick_rows),
        kill_audit_map(read_jsonl(KILL_SCOPE_LEDGER)),
    )
    write_jsonl(OUTPUT_LEDGER, output_rows)

    before_pending = pending_rows(action_rows)
    after_pending = pending_rows(output_rows)
    before_proxy = proxy_summary(action_rows)
    after_proxy = proxy_summary(output_rows)
    kill_rows = [row for row in output_rows if row.get("action_class") == "KILL"]
    source_requirement_rows = [
        {
            "candidate_id": row.get("candidate_id"),
            "branch_decision": row.get("branch_decision"),
            "source_requirement": row.get(
                "pending_lifecycle_tick_spread_reconstruction_attempt_source_requirement"
            ),
            "attempt_status": row.get("pending_lifecycle_tick_spread_reconstruction_attempt_status"),
        }
        for row in after_pending
        if row.get("pending_lifecycle_tick_spread_reconstruction_attempt_source_requirement")
    ]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_PENDING_TICK_SPREAD_REPAIR",
        "claim_boundary": (
            "Current implementation-selection action ledger after consuming pending lifecycle tick-spread "
            "reconstruction. This changes pending source completeness and branch decisions inside the "
            "current 1,475 proxy-row action denominator; R values and action classes remain unchanged."
        ),
        "rows": len(output_rows),
        "pending_rows": len(after_pending),
        "decision_repair_stats": stats,
        "status_counts": counter(output_rows, "action_after_pending_tick_spread_repair_status"),
        "before_pending_branch_counts": counter(before_pending, "branch_decision"),
        "after_pending_branch_counts": counter(after_pending, "branch_decision"),
        "before_pending_source_complete_counts": counter(before_pending, "pending_lifecycle_source_capture_complete"),
        "after_pending_source_complete_counts": counter(after_pending, "pending_lifecycle_source_capture_complete"),
        "before_pending_decision_spread_status_counts": {
            status: count
            for status, count in Counter(pending_decision_spread_status(row) for row in before_pending).items()
        },
        "after_pending_decision_spread_status_counts": {
            status: count
            for status, count in Counter(pending_decision_spread_status(row) for row in after_pending).items()
        },
        "after_action_class_counts": counter(output_rows, "action_class"),
        "previous_action_class_counts": action_summary.get("action_class_counts_after"),
        "after_numeric_proxy_rows": after_proxy["numeric_proxy_rows"],
        "after_proxy_r_sum": after_proxy["proxy_r_sum"],
        "before_numeric_proxy_rows": before_proxy["numeric_proxy_rows"],
        "before_proxy_r_sum": before_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "all_metadata_gaps_after": sum(
            1 for row in output_rows if row.get("metadata_gap") or row.get("source_metadata_gap")
        ),
        "kill_scope_audited_rows_after": sum(1 for row in kill_rows if kill_audit_present(row)),
        "pending_tick_reconstruction_source_summary": {
            "tick_reconstruction_attempt_rows": tick_summary.get("tick_reconstruction_attempt_rows"),
            "tick_reconstruction_success_rows": tick_summary.get("tick_reconstruction_success_rows"),
            "tick_reconstruction_unsafe_rows": tick_summary.get("tick_reconstruction_unsafe_rows"),
            "remaining_pending_decision_spread_gaps": tick_summary.get(
                "remaining_pending_decision_spread_gaps"
            ),
        },
        "remaining_pending_tick_source_requirements": source_requirement_rows,
        "previous_plate_decision": action_summary.get("plate_decision"),
        "plate_decision": "CURRENT_ACTION_LEDGER_CONSUMED_PENDING_TICK_SPREAD_REPAIR",
        "safe_flags": SAFE_FLAGS,
    }
    summary["after_pending_decision_spread_status_counts"] = dict(
        sorted(summary["after_pending_decision_spread_status_counts"].items())
    )
    summary["before_pending_decision_spread_status_counts"] = dict(
        sorted(summary["before_pending_decision_spread_status_counts"].items())
    )
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows": len(output_rows),
                "pending_rows": len(after_pending),
                "after_numeric_proxy_rows": summary["after_numeric_proxy_rows"],
                "after_proxy_r_sum": summary["after_proxy_r_sum"],
                "pending_branch_counts": summary["after_pending_branch_counts"],
                "pending_decision_spread_status_counts": summary[
                    "after_pending_decision_spread_status_counts"
                ],
                "remaining_pending_tick_source_requirements": len(source_requirement_rows),
                "plate_decision": summary["plate_decision"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
