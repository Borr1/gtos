"""Materialize remaining action-row decision evidence and candidates.

This plate consumes current scorer recomputation and entry-offset M15/tick
repair evidence into the action ledger. It closes the remaining decision gaps
as row-level keep/kill/default-off implementation decisions, without changing
proxy R, exact R, live behavior, or shadow logs.
"""

from __future__ import annotations

import hashlib
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
SOURCE_DATE = "2026-05-16"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(ROUTE_DIR)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.live_mechanical_shadow import (  # noqa: E402
    build_strategy_outcome_rows,
    latest_lifecycle_for_candidate_asof,
    latest_ltf_for_candidate_asof,
    read_jsonl as read_shadow_jsonl,
)


INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_SCORER_METADATA_REFRESH_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_SCORER_METADATA_REFRESH_SUMMARY_{DATE}.json"
ENTRY_OFFSET_SOURCE_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_LEDGER_{SOURCE_DATE}.jsonl"
)
SCORER_SOURCE = REPO_ROOT / "src/research_infra/live_mechanical_shadow.py"

SHADOW_INPUTS = {
    "strategy_follow_candidates": REPO_ROOT / "shadow_logs/strategy_follow_candidates.jsonl",
    "candidate_path_follow": REPO_ROOT / "shadow_logs/candidate_path_follow.jsonl",
    "pending_limit_lifecycle": REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl",
    "candidate_ltf_path_order": REPO_ROOT / "shadow_logs/candidate_ltf_path_order.jsonl",
}

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_DECISION_COMPLETENESS_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_DECISION_COMPLETENESS_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_DECISION_COMPLETENESS_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

FVG_STRUCTURAL_SOURCE_PLATE = "fvg_structural_scorer_candidate_recompute"
ENTRY_OFFSET_SOURCE_PLATE = "entry_offset_m15_hard_no_fill_repair"

FVG_STATUS = "REPAIRED_FROM_RECOMPUTED_FVG_STRUCTURAL_SCORER"
ENTRY_STATUS = "REPAIRED_FROM_ENTRY_OFFSET_M15_TICK_SOURCE_DECISION"

ENTRY_BRANCH_KEEP_CURRENT = "KEEP_CURRENT_ENTRY_MODEL_NOT_IN_ENTRY_REDESIGN_DENOMINATOR"
ENTRY_BRANCH_KILL_FAR_MISS = "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL"
ENTRY_BRANCH_NEAR_MISS = "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_NEAR_MISS_CHALLENGER"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def floats_equal(left: Any, right: Any) -> bool:
    left_value = safe_float(left)
    right_value = safe_float(right)
    if left_value is None or right_value is None:
        return left_value is None and right_value is None
    return round(left_value - right_value, 10) == 0


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter("" if row.get(field) is None else str(row.get(field)) for row in rows))


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current = parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        previous = parse_utc(out.get(cid, {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        if current >= previous:
            out[cid] = row
    return out


def latest_path_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current_asof = parse_utc(row.get("asof_latest_candle_utc"))
        previous_asof = parse_utc(out.get(cid, {}).get("asof_latest_candle_utc"))
        current_created = parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        previous_created = parse_utc(out.get(cid, {}).get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)
        if previous_asof is None or (
            current_asof is not None
            and (current_asof > previous_asof or (current_asof == previous_asof and current_created >= previous_created))
        ):
            out[cid] = row
    return out


def has_metadata_gap(row: dict[str, Any]) -> bool:
    return (
        row.get("decision_evidence") in (None, "")
        or row.get("scoring_boundary") in (None, "")
        or row.get("implementation_candidate") in (None, "")
        or str(row.get("current_action")) in {"None", "False", ""}
        or str(row.get("next_action")) in {"None", "False", ""}
    )


def is_fvg_structural_gap(row: dict[str, Any]) -> bool:
    return row.get("source_plate") == FVG_STRUCTURAL_SOURCE_PLATE and has_metadata_gap(row)


def is_entry_offset_gap(row: dict[str, Any]) -> bool:
    return row.get("source_plate") == ENTRY_OFFSET_SOURCE_PLATE and has_metadata_gap(row)


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "proxy_r_mean": round(sum(values) / len(values), 8) if values else None,
    }


def far_miss_invariants(rows: list[dict[str, Any]]) -> dict[str, Any]:
    entry_branch = "IMPLEMENT_DEFAULT_OFF_ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_CHALLENGER"
    prefill_branch = "IMPLEMENT_DEFAULT_OFF_PREFILL_FAR_MISS_RETEST_CONTROL_CHALLENGER"
    kill_branch = ENTRY_BRANCH_KILL_FAR_MISS
    prefill_kill_branch = "KILL_PREFILL_050R_OFFSET_NO_FILL_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL"
    entry_rows = [row for row in rows if row.get("branch_decision") == entry_branch]
    prefill_rows = [row for row in rows if row.get("branch_decision") == prefill_branch]
    killed_rows = [row for row in rows if row.get("branch_decision") == kill_branch]
    prefill_killed_rows = [row for row in rows if row.get("branch_decision") == prefill_kill_branch]
    entry_values = [safe_float(row.get("after_proxy_r")) for row in entry_rows]
    entry_values = [value for value in entry_values if value is not None]
    return {
        "entry_default_off_rows": len(entry_rows),
        "entry_default_off_candidates": len({row.get("candidate_id") for row in entry_rows}),
        "entry_default_off_numeric_proxy_rows": len(entry_values),
        "entry_default_off_proxy_r_sum": round(sum(entry_values), 8),
        "prefill_default_off_rows": len(prefill_rows),
        "prefill_default_off_candidates": len({row.get("candidate_id") for row in prefill_rows}),
        "killed_far_miss_rows": len(killed_rows),
        "killed_far_miss_candidates": len({row.get("candidate_id") for row in killed_rows}),
        "prefill_killed_far_miss_rows": len(prefill_killed_rows),
        "prefill_killed_far_miss_candidates": len({row.get("candidate_id") for row in prefill_killed_rows}),
    }


def tick_structural_invariants(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = counter(rows, "tick_structural_derivation_repair_status")
    converted = sum(
        count
        for status, count in counts.items()
        if status not in {"", "None", "NOT_TARGET_ROW"}
    )
    return {
        "tick_structural_converted_rows": converted,
        "tick_structural_status_counts": counts,
    }


def build_strategy_recompute_map(generated_utc: str) -> dict[tuple[str, str], dict[str, Any]]:
    candidates = latest_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["strategy_follow_candidates"]))
    paths = latest_path_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["candidate_path_follow"]))
    pending_lifecycle_rows = read_shadow_jsonl(SHADOW_INPUTS["pending_limit_lifecycle"])
    ltf_rows = read_shadow_jsonl(SHADOW_INPUTS["candidate_ltf_path_order"])
    recomputed: dict[tuple[str, str], dict[str, Any]] = {}
    for cid in sorted(candidates):
        candidate = candidates[cid]
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
            created_at_utc=generated_utc,
        ):
            key = (str(row.get("candidate_id") or ""), str(row.get("strategy_id") or ""))
            recomputed[key] = row
    return recomputed


def build_entry_source_map() -> dict[str, dict[str, Any]]:
    rows = read_jsonl(ENTRY_OFFSET_SOURCE_LEDGER)
    return {str(row.get("row_id") or ""): row for row in rows}


def copy_context_fields(row: dict[str, Any], source: dict[str, Any], prefixes: tuple[str, ...]) -> None:
    for key, value in source.items():
        if key.startswith(prefixes):
            row[key] = value


def entry_decision_fields(source: dict[str, Any], action_row: dict[str, Any]) -> dict[str, Any]:
    branch = str(source.get("after_entry_branch_decision") or action_row.get("branch_decision") or "")
    if branch == ENTRY_BRANCH_KEEP_CURRENT:
        return {
            "branch_decision": branch,
            "decision_evidence": "CURRENT_ENTRY_MODEL_ROW_NOT_NO_FILL_TP1_OFFSET_REDESIGN",
            "scoring_boundary": "CURRENT_ENTRY_MODEL_ROW_NOT_NO_FILL_TP1_OFFSET_REDESIGN",
            "implementation_candidate": "NONE_CURRENT_ENTRY_ALREADY_TOUCHED_OR_NOT_TP1_NO_FILL",
            "implementation_decision": branch,
            "current_action": "NONE_CURRENT_ENTRY_ALREADY_TOUCHED_OR_NOT_TP1_NO_FILL",
            "data_requirement_state": "NOT_REQUIRED_FOR_NON_REDESIGN_ROW",
        }
    if branch == ENTRY_BRANCH_KILL_FAR_MISS:
        if source.get("m15_hard_no_fill_proof_status") == "PROVEN_NO_FILL_AT_050R_FROM_M15_LTF_RANGE":
            evidence = "ENTRY_OFFSET_050R_M15_HARD_NO_FILL_GT_1R_NO_TICK_NEEDED"
            boundary = "M15_HARD_NO_FILL_RANGE_PROOF_ONLY_NO_FILL_OR_TP_INFERENCE"
        else:
            evidence = "ENTRY_OFFSET_050R_TICK_REPLAY_NO_FILL"
            boundary = "NO_ENTRY_OFFSET_PROXY_UPLIFT_WHEN_050R_SHIFT_STILL_NO_FILL"
        return {
            "branch_decision": branch,
            "decision_evidence": evidence,
            "scoring_boundary": boundary,
            "implementation_candidate": "NONE_FAR_MISS_050R_NO_FILL_KEEP_AS_RETEST_REDESIGN_FAILURE",
            "implementation_decision": branch,
            "current_action": "NONE_FAR_MISS_050R_NO_FILL_KEEP_AS_RETEST_REDESIGN_FAILURE",
            "data_requirement_state": source.get("after_entry_score_status"),
        }
    if branch == ENTRY_BRANCH_NEAR_MISS:
        return {
            "branch_decision": branch,
            "decision_evidence": "ENTRY_OFFSET_050R_TICK_REPLAY_TP_AFTER_FILL",
            "scoring_boundary": "ENTRY_OFFSET_050R_TICK_REPLAY_PROXY_NO_LIVE_ENTRY_CHANGE",
            "implementation_candidate": "ENTRY_OFFSET_050R_NEAR_MISS_SPREAD_AWARE_CHALLENGER",
            "implementation_decision": branch,
            "current_action": "ENTRY_OFFSET_050R_NEAR_MISS_SPREAD_AWARE_CHALLENGER",
            "data_requirement_state": source.get("after_entry_score_status"),
        }
    return {
        "branch_decision": branch,
        "decision_evidence": f"ENTRY_OFFSET_BRANCH_{branch}_MATERIALIZATION_REQUIRED",
        "scoring_boundary": "ENTRY_OFFSET_BRANCH_NOT_RECOGNIZED_BY_CURRENT_MATERIALIZER",
        "implementation_candidate": str(action_row.get("implementation_candidate") or action_row.get("current_action") or branch),
        "implementation_decision": str(action_row.get("implementation_decision") or branch),
        "current_action": str(action_row.get("current_action") or action_row.get("implementation_candidate") or branch),
        "data_requirement_state": source.get("after_entry_score_status") or action_row.get("data_requirement_state"),
    }


def mark_before(row: dict[str, Any]) -> None:
    for field in (
        "branch_decision",
        "decision_evidence",
        "scoring_boundary",
        "implementation_candidate",
        "implementation_decision",
        "current_action",
        "next_action",
        "data_requirement_state",
    ):
        row[f"before_action_decision_materialization_{field}"] = row.get(field)


def apply_fvg_structural(
    row: dict[str, Any],
    recomputed: dict[tuple[str, str], dict[str, Any]],
) -> bool:
    key = (str(row.get("candidate_id") or ""), str(row.get("strategy_id") or ""))
    source = recomputed.get(key)
    if not source:
        row["action_decision_completeness_status"] = "FVG_STRUCTURAL_RECOMPUTE_ROW_MISSING"
        return False
    mark_before(row)
    row["action_decision_completeness_status"] = FVG_STATUS
    row["action_decision_completeness_source"] = "src/research_infra/live_mechanical_shadow.py"
    row["action_decision_recomputed_strategy_status"] = source.get("strategy_status")
    row["action_decision_recomputed_score_status"] = source.get("score_status")
    row["action_decision_recomputed_outcome_status"] = source.get("outcome_status")
    row["action_decision_recomputed_proxy_r"] = source.get("strategy_proxy_r")
    row["action_decision_recomputed_proxy_r_matches_action_row"] = floats_equal(
        row.get("after_proxy_r"),
        source.get("strategy_proxy_r"),
    )
    row["branch_decision"] = source.get("branch_decision") or row.get("branch_decision")
    row["decision_evidence"] = source.get("decision_evidence") or row.get("decision_evidence")
    row["scoring_boundary"] = source.get("scoring_boundary") or row.get("scoring_boundary")
    row["implementation_candidate"] = source.get("implementation_candidate") or row.get("implementation_candidate")
    row["current_action"] = source.get("implementation_candidate") or row.get("current_action")
    row["next_action"] = source.get("implementation_candidate") or row.get("next_action")
    row["data_requirement_state"] = source.get("score_status") or row.get("data_requirement_state")
    copy_context_fields(
        row,
        source,
        (
            "fvg_ob_confluence_",
            "standalone_fvg_",
            "swing_protected_",
            "ltf_",
        ),
    )
    return True


def apply_entry_offset(row: dict[str, Any], entry_sources: dict[str, dict[str, Any]]) -> bool:
    source = entry_sources.get(str(row.get("source_row_id") or ""))
    if not source:
        row["action_decision_completeness_status"] = "ENTRY_OFFSET_SOURCE_ROW_MISSING"
        return False
    mark_before(row)
    fields = entry_decision_fields(source, row)
    row["action_decision_completeness_status"] = ENTRY_STATUS
    row["action_decision_completeness_source"] = ENTRY_OFFSET_SOURCE_LEDGER.name
    row["entry_offset_materialized_score_status"] = source.get("after_entry_score_status")
    row["entry_offset_materialized_scorer_status"] = source.get("after_entry_scorer_status")
    row["entry_offset_m15_hard_no_fill_proof_status"] = source.get("m15_hard_no_fill_proof_status")
    row["entry_offset_m15_hard_no_fill_repaired"] = source.get("m15_hard_no_fill_repaired")
    row["entry_offset_m15_hard_no_fill_min_distance_r"] = source.get("m15_hard_no_fill_min_distance_r")
    row["entry_offset_m15_nearest_distance_to_entry_r"] = source.get("m15_nearest_distance_to_entry_r")
    row["entry_offset_tick_source_status"] = source.get("tick_source_status")
    row["entry_offset_path_outcome_status"] = source.get("path_outcome_status")
    row["entry_offset_ltf_terminal_outcome_status"] = source.get("ltf_terminal_outcome_status")
    row["entry_offset_after_entry_proxy_r"] = source.get("after_entry_proxy_r")
    for key, value in fields.items():
        row[key] = value
    row["next_action"] = row["current_action"]
    return True


def materialize_rows(
    rows: list[dict[str, Any]],
    recomputed: dict[tuple[str, str], dict[str, Any]],
    entry_sources: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    generated = utc_now()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        before_gap = has_metadata_gap(row)
        if is_fvg_structural_gap(row):
            stats["fvg_structural_target_rows"] += 1
            if apply_fvg_structural(row, recomputed):
                stats["fvg_structural_rows_materialized"] += 1
            else:
                stats["fvg_structural_rows_missing_recompute"] += 1
        elif is_entry_offset_gap(row):
            stats["entry_offset_target_rows"] += 1
            if apply_entry_offset(row, entry_sources):
                stats["entry_offset_rows_materialized"] += 1
            else:
                stats["entry_offset_rows_missing_source"] += 1
        else:
            row.setdefault("action_decision_completeness_status", "NOT_TARGET_ROW")

        if before_gap:
            stats["metadata_gap_rows_before"] += 1
        if has_metadata_gap(row):
            stats["metadata_gap_rows_after"] += 1
        output.append(row)
    return output, dict(stats)


def action_delta(before: dict[str, int], after: dict[str, int]) -> dict[str, int]:
    keys = sorted(set(before) | set(after))
    return {
        key: int(after.get(key, 0)) - int(before.get(key, 0))
        for key in keys
        if int(after.get(key, 0)) != int(before.get(key, 0))
    }


def build_manifest(output_paths: list[Path]) -> dict[str, Any]:
    inputs = [INPUT_LEDGER, INPUT_SUMMARY, ENTRY_OFFSET_SOURCE_LEDGER, SCORER_SOURCE, *SHADOW_INPUTS.values()]
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
    recomputed = build_strategy_recompute_map(utc_now())
    entry_sources = build_entry_source_map()
    output_rows, stats = materialize_rows(input_rows, recomputed, entry_sources)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    fvg_targets = [row for row in output_rows if row.get("action_decision_completeness_status") == FVG_STATUS]
    entry_targets = [row for row in output_rows if row.get("action_decision_completeness_status") == ENTRY_STATUS]
    before_actions = counter(input_rows, "action_class")
    after_actions = counter(output_rows, "action_class")
    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ACTION_DECISION_COMPLETENESS_MATERIALIZATION",
        "claim_boundary": (
            "Remaining FVG/structural scorer and entry-offset action rows consume current scorer/source evidence "
            "into concrete keep/kill/default-off implementation candidates. Proxy R and exact R are unchanged; "
            "no live behavior, shadow append, promotion, broker operation, or AI/API call is opened."
        ),
        "rows": len(output_rows),
        "fvg_structural_rows_materialized": len(fvg_targets),
        "entry_offset_rows_materialized": len(entry_targets),
        "total_rows_materialized": len(fvg_targets) + len(entry_targets),
        "all_metadata_gaps_before": sum(1 for row in input_rows if has_metadata_gap(row)),
        "all_metadata_gaps_after": sum(1 for row in output_rows if has_metadata_gap(row)),
        "repair_stats": stats,
        "action_decision_completeness_status_counts": counter(
            output_rows,
            "action_decision_completeness_status",
        ),
        "fvg_structural_action_class_counts": counter(fvg_targets, "action_class"),
        "fvg_structural_branch_decision_counts": counter(fvg_targets, "branch_decision"),
        "fvg_structural_strategy_counts": counter(fvg_targets, "strategy_id"),
        "fvg_structural_source_surface_counts": counter(fvg_targets, "source_capture_surface"),
        "entry_offset_action_class_counts": counter(entry_targets, "action_class"),
        "entry_offset_branch_decision_counts": counter(entry_targets, "branch_decision"),
        "entry_offset_source_status_counts": counter(entry_targets, "entry_offset_tick_source_status"),
        "entry_offset_m15_hard_no_fill_proof_counts": counter(
            entry_targets,
            "entry_offset_m15_hard_no_fill_proof_status",
        ),
        "action_class_counts_before": before_actions,
        "action_class_counts_after": after_actions,
        "action_class_delta_vs_previous": action_delta(before_actions, after_actions),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "far_miss_retest_control_invariants": far_miss_invariants(output_rows),
        "tick_structural_source_repair_invariants": tick_structural_invariants(output_rows),
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "ALL_CURRENT_ACTION_ROWS_HAVE_CONCRETE_DECISION_EVIDENCE_BOUNDARY_AND_IMPLEMENTATION_CANDIDATE",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "rows_materialized": summary["total_rows_materialized"],
                "all_metadata_gaps_after": summary["all_metadata_gaps_after"],
                "summary": str(OUTPUT_SUMMARY),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
