"""Consume nofill-forward decision-spread source into pending lifecycle rows."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
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
if str(ROUTE_DIR) not in sys.path:
    sys.path.insert(0, str(ROUTE_DIR))

from build_main_orchestrator_pending_lifecycle_decision_spread_repair_2026_05_17 import (  # noqa: E402
    PENDING_LIMIT_STRATEGY_ID,
    SAFE_FLAGS,
    apply_pending_scorer as base_apply_pending_scorer,
    counter,
    has_metadata_gap,
    kill_audit_present,
    latest_by_candidate,
    latest_path_by_candidate,
    nested_status_counter,
    pending_proxy_summary,
    proxy_summary,
    read_json,
    read_jsonl,
    safe_float,
    sha256_file,
    utc_now,
    write_json,
    write_jsonl,
)
from src.research_infra.live_mechanical_shadow import (  # noqa: E402
    PENDING_LIFECYCLE_CAPTURE_FIELDS,
    build_strategy_outcome_rows,
    latest_lifecycle_for_candidate_asof,
    latest_ltf_for_candidate_asof,
    latest_nofill_forward_capture_by_candidate,
    latest_structural_metadata_by_candidate,
    merge_structural_metadata_candidate,
    read_jsonl as read_shadow_jsonl,
)


INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_DECISION_SPREAD_REPAIR_SUMMARY_{DATE}.json"
SCORER_SOURCE = REPO_ROOT / "src/research_infra/live_mechanical_shadow.py"
TEST_SOURCE = REPO_ROOT / "tests/test_live_mechanical_shadow.py"
PREVIOUS_BUILDER = (
    ROUTE_DIR / "build_main_orchestrator_pending_lifecycle_decision_spread_repair_2026_05_17.py"
)

SHADOW_INPUTS = {
    "strategy_follow_candidates": REPO_ROOT / "shadow_logs/strategy_follow_candidates.jsonl",
    "candidate_path_follow": REPO_ROOT / "shadow_logs/candidate_path_follow.jsonl",
    "pending_limit_lifecycle": REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl",
    "candidate_ltf_path_order": REPO_ROOT / "shadow_logs/candidate_ltf_path_order.jsonl",
    "live_structural_strategy_metadata": REPO_ROOT / "shadow_logs/live_structural_strategy_metadata.jsonl",
    "nofill_forward_source_capture": REPO_ROOT / "shadow_logs/nofill_forward_source_capture.jsonl",
}

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / (
    f"MAIN_ORCH24_PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
)

NOFILL_DERIVATION = "DERIVED_FROM_NOFILL_FORWARD_SOURCE_CAPTURE_DECISION_SPREAD"
LEGACY_DERIVATION = "DERIVED_FROM_PENDING_LIFECYCLE_LEGACY_SPREAD_AS_DECISION_SPREAD_PROXY"
RECONSTRUCTED_BRANCH = "KEEP_PENDING_LIFECYCLE_SCORER_WITH_RECONSTRUCTED_SOURCE_FIELDS_COMPLETE"


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_pending_recompute_map(generated_utc: str) -> dict[str, dict[str, Any]]:
    candidates = latest_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["strategy_follow_candidates"]))
    paths = latest_path_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["candidate_path_follow"]))
    pending_lifecycle_rows = read_shadow_jsonl(SHADOW_INPUTS["pending_limit_lifecycle"])
    ltf_rows = read_shadow_jsonl(SHADOW_INPUTS["candidate_ltf_path_order"])
    structural_metadata = latest_structural_metadata_by_candidate(
        read_shadow_jsonl(SHADOW_INPUTS["live_structural_strategy_metadata"])
    )
    nofill_forward = latest_nofill_forward_capture_by_candidate(
        read_shadow_jsonl(SHADOW_INPUTS["nofill_forward_source_capture"])
    )
    recomputed: dict[str, dict[str, Any]] = {}
    for cid in sorted(candidates):
        candidate = merge_structural_metadata_candidate(candidates[cid], structural_metadata.get(cid))
        path = paths.get(cid)
        if not path:
            continue
        pending = latest_lifecycle_for_candidate_asof(candidate, path, pending_lifecycle_rows)
        ltf = latest_ltf_for_candidate_asof(candidate, path, ltf_rows)
        for row in build_strategy_outcome_rows(
            candidate,
            path,
            pending_lifecycle_row=pending,
            ltf_row=ltf,
            nofill_forward_capture_row=nofill_forward.get(cid),
            created_at_utc=generated_utc,
        ):
            if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID:
                recomputed[str(row.get("candidate_id") or "")] = row
    return recomputed


def mark_before(row: dict[str, Any]) -> None:
    for field in (
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
        "pending_lifecycle_source_capture_statuses",
        "pending_lifecycle_source_capture_derivations",
        "pending_lifecycle_source_capture_complete",
    ):
        row[f"before_pending_nofill_forward_spread_repair_{field}"] = row.get(field)


def apply_pending_scorer(row: dict[str, Any], scorer_row: dict[str, Any]) -> None:
    base_apply_pending_scorer(row, scorer_row)
    for field in (
        "pending_lifecycle_decision_spread_reconstruction_source",
        "pending_lifecycle_decision_spread_reconstruction_source_created_at_utc",
        "pending_lifecycle_decision_spread_reconstruction_source_status",
    ):
        if field in scorer_row:
            row[field] = scorer_row.get(field)


def repair_status(row: dict[str, Any]) -> str:
    if row.get("strategy_id") != PENDING_LIMIT_STRATEGY_ID:
        return "NOT_PENDING_LIFECYCLE_ROW"
    statuses = row.get("pending_lifecycle_source_capture_statuses")
    if not isinstance(statuses, dict):
        return "PENDING_LIFECYCLE_RECOMPUTE_APPLIED_NO_INTERNAL_LIFECYCLE"
    derivation = statuses.get("decision_spread_value_source_safe")
    if derivation == NOFILL_DERIVATION:
        return "PENDING_LIFECYCLE_DECISION_SPREAD_REPAIRED_FROM_NOFILL_FORWARD_CAPTURE"
    if derivation == LEGACY_DERIVATION:
        return "PENDING_LIFECYCLE_LEGACY_SPREAD_REPAIR_PRESERVED"
    return "PENDING_LIFECYCLE_RECOMPUTE_APPLIED_NO_DECISION_SPREAD_REPAIR"


def materialize_rows(
    rows: list[dict[str, Any]],
    recomputed: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    generated = utc_now()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if row.get("strategy_id") != PENDING_LIMIT_STRATEGY_ID:
            row["pending_lifecycle_nofill_forward_spread_repair_status"] = "NOT_PENDING_LIFECYCLE_ROW"
            output.append(row)
            continue
        stats["pending_rows"] += 1
        mark_before(row)
        scorer_row = recomputed.get(str(row.get("candidate_id") or ""))
        if scorer_row is None:
            row["pending_lifecycle_nofill_forward_spread_repair_status"] = (
                "PENDING_LIFECYCLE_RECOMPUTE_MISSING"
            )
            stats["recompute_missing"] += 1
            output.append(row)
            continue
        apply_pending_scorer(row, scorer_row)
        status = repair_status(row)
        row["pending_lifecycle_nofill_forward_spread_repair_status"] = status
        stats[status] += 1
        if row.get("before_pending_nofill_forward_spread_repair_branch_decision") != row.get("branch_decision"):
            stats["branch_changed"] += 1
        if safe_float(row.get("before_pending_nofill_forward_spread_repair_after_proxy_r")) != safe_float(
            row.get("after_proxy_r")
        ):
            stats["proxy_changed"] += 1
        if (
            row.get("before_pending_nofill_forward_spread_repair_pending_lifecycle_source_capture_complete")
            != row.get("pending_lifecycle_source_capture_complete")
        ):
            stats["source_capture_complete_changed"] += 1
        if (
            row.get("before_pending_nofill_forward_spread_repair_pending_lifecycle_decision_spread_reconstruction_source")
            != row.get("pending_lifecycle_decision_spread_reconstruction_source")
        ):
            stats["spread_reconstruction_source_changed"] += 1
        output.append(row)
    return output, dict(stats)


def build_manifest(output_paths: list[Path]) -> dict[str, Any]:
    inputs = [INPUT_LEDGER, INPUT_SUMMARY, SCORER_SOURCE, TEST_SOURCE, PREVIOUS_BUILDER, *SHADOW_INPUTS.values()]
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
    recomputed = build_pending_recompute_map(utc_now())
    output_rows, stats = materialize_rows(input_rows, recomputed)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    pending_rows = [row for row in output_rows if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID]
    input_pending = [row for row in input_rows if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID]
    kill_rows = [row for row in output_rows if row.get("action_class") == "KILL"]
    nofill_rows = [
        row
        for row in pending_rows
        if row.get("pending_lifecycle_nofill_forward_spread_repair_status")
        == "PENDING_LIFECYCLE_DECISION_SPREAD_REPAIRED_FROM_NOFILL_FORWARD_CAPTURE"
    ]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR",
        "claim_boundary": (
            "Pending lifecycle decision-spread source completeness after consuming exact decision quote "
            "snapshots from nofill_forward_source_capture. This changes source completeness and branch "
            "decisions only; R values, exact-R claims, validation safety, and live behavior remain closed."
        ),
        "rows": len(output_rows),
        "pending_rows": len(pending_rows),
        "decision_repair_stats": stats,
        "status_counts": counter(output_rows, "pending_lifecycle_nofill_forward_spread_repair_status"),
        "before_pending_branch_counts": counter(input_pending, "branch_decision"),
        "after_pending_branch_counts": counter(pending_rows, "branch_decision"),
        "before_pending_source_complete_counts": counter(input_pending, "pending_lifecycle_source_capture_complete"),
        "after_pending_source_complete_counts": counter(pending_rows, "pending_lifecycle_source_capture_complete"),
        "before_pending_decision_spread_status_counts": nested_status_counter(
            input_pending,
            "decision_spread_value_source_safe",
        ),
        "after_pending_decision_spread_status_counts": nested_status_counter(
            pending_rows,
            "decision_spread_value_source_safe",
        ),
        "nofill_forward_decision_spread_rows": len(nofill_rows),
        "nofill_forward_decision_spread_candidates": sorted(str(row.get("candidate_id") or "") for row in nofill_rows),
        "legacy_decision_spread_rows_after": sum(
            1
            for row in pending_rows
            if (row.get("pending_lifecycle_source_capture_statuses") or {}).get(
                "decision_spread_value_source_safe"
            )
            == LEGACY_DERIVATION
        ),
        "remaining_pending_decision_spread_gaps": sum(
            1
            for row in pending_rows
            if (row.get("pending_lifecycle_source_capture_statuses") or {}).get(
                "decision_spread_value_source_safe"
            )
            == "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW"
        ),
        "before_action_class_counts": input_summary.get("after_action_class_counts"),
        "after_action_class_counts": counter(output_rows, "action_class"),
        "all_metadata_gaps_after": sum(1 for row in output_rows if has_metadata_gap(row)),
        "kill_scope_audited_rows_after": sum(1 for row in kill_rows if kill_audit_present(row)),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "before_pending_proxy_summary": pending_proxy_summary(input_rows),
        "after_pending_proxy_summary": pending_proxy_summary(output_rows),
        "pending_proxy_r_sum_delta": round(
            pending_proxy_summary(output_rows)["pending_proxy_r_sum"]
            - pending_proxy_summary(input_rows)["pending_proxy_r_sum"],
            8,
        ),
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_ACCEPTED_NO_R_CHANGE",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "pending_rows": len(pending_rows),
                "nofill_forward_decision_spread_rows": len(nofill_rows),
                "remaining_pending_decision_spread_gaps": summary["remaining_pending_decision_spread_gaps"],
                "pending_branch_counts": summary["after_pending_branch_counts"],
                "pending_decision_spread_status_counts": summary[
                    "after_pending_decision_spread_status_counts"
                ],
                "proxy_r_sum_after": summary["proxy_r_sum_after"],
                "pending_proxy_r_sum": summary["after_pending_proxy_summary"]["pending_proxy_r_sum"],
                "plate_decision": summary["plate_decision"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
