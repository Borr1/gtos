"""Refresh pending-lifecycle scorer metadata in the current action ledger.

This consumes the patched pending-limit lifecycle scorer fields from
``live_mechanical_shadow`` into the active 3,426-row action ledger. It does not
change proxy R, exact R, live behavior, or shadow logs.
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
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(ROUTE_DIR)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.live_mechanical_shadow import (  # noqa: E402
    PENDING_LIMIT_STRATEGY_ID,
    build_strategy_outcome_rows,
    latest_lifecycle_for_candidate_asof,
    latest_ltf_for_candidate_asof,
    read_jsonl as read_shadow_jsonl,
)


INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_PENDING_METADATA_DECISION_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_SOURCE_PENDING_METADATA_DECISION_REPAIR_SUMMARY_{DATE}.json"
SCORER_SOURCE = REPO_ROOT / "src/research_infra/live_mechanical_shadow.py"

SHADOW_INPUTS = {
    "strategy_follow_candidates": REPO_ROOT / "shadow_logs/strategy_follow_candidates.jsonl",
    "candidate_path_follow": REPO_ROOT / "shadow_logs/candidate_path_follow.jsonl",
    "pending_limit_lifecycle": REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl",
    "candidate_ltf_path_order": REPO_ROOT / "shadow_logs/candidate_ltf_path_order.jsonl",
}

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_SCORER_METADATA_REFRESH_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_SCORER_METADATA_REFRESH_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_PENDING_SCORER_METADATA_REFRESH_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

PENDING_SOURCE_FIELD_PREFIX = "pending_lifecycle_"
PENDING_REFRESH_STATUS = "REPAIRED_FROM_PATCHED_PENDING_LIFECYCLE_SCORER"


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


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter("" if row.get(field) is None else str(row.get(field)) for row in rows))


def has_metadata_gap(row: dict[str, Any]) -> bool:
    return (
        row.get("decision_evidence") in (None, "")
        or row.get("scoring_boundary") in (None, "")
        or row.get("implementation_candidate") in (None, "")
        or str(row.get("current_action")) in {"None", "False", ""}
        or str(row.get("next_action")) in {"None", "False", ""}
    )


def is_pending_scorer_action_row(row: dict[str, Any]) -> bool:
    return (
        row.get("source_plate") == "fvg_structural_scorer_candidate_recompute"
        and row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID
        and row.get("source_capture_surface") == "pending_limit_lifecycle_source_capture"
    )


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
    kill_branch = "KILL_FAR_MISS_050R_OFFSET_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL"
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


def source_field_cell_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    status_cells = 0
    derived_cells = 0
    missing_cells = 0
    captured_cells = 0
    for row in rows:
        statuses = row.get("pending_lifecycle_source_capture_statuses")
        if not isinstance(statuses, dict):
            continue
        status_cells += len(statuses)
        for status in statuses.values():
            text = str(status)
            if text.startswith("DERIVED_"):
                derived_cells += 1
            elif text == "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW":
                missing_cells += 1
            else:
                captured_cells += 1
    return {
        "pending_source_status_cells": status_cells,
        "pending_source_derived_field_cells": derived_cells,
        "pending_source_missing_field_cells": missing_cells,
        "pending_source_captured_field_cells": captured_cells,
    }


def build_pending_recompute_map(generated_utc: str) -> dict[str, dict[str, Any]]:
    candidates = latest_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["strategy_follow_candidates"]))
    paths = latest_path_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["candidate_path_follow"]))
    pending_lifecycle_rows = read_shadow_jsonl(SHADOW_INPUTS["pending_limit_lifecycle"])
    ltf_rows = read_shadow_jsonl(SHADOW_INPUTS["candidate_ltf_path_order"])
    recomputed: dict[str, dict[str, Any]] = {}
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
            if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID:
                recomputed[cid] = row
                break
    return recomputed


def copy_pending_source_fields(row: dict[str, Any], recomputed: dict[str, Any]) -> None:
    for key, value in recomputed.items():
        if key.startswith(PENDING_SOURCE_FIELD_PREFIX) or key in {
            "ltf_path_order_label",
            "ltf_terminal_outcome_status",
            "ltf_terminal_event_utc",
            "ltf_terminal_order_ambiguity",
            "pending_lifecycle_intent_after_check",
            "pending_lifecycle_fill_no_fill_label",
            "pending_lifecycle_trade_id",
            "pending_lifecycle_candidate_id",
            "pending_lifecycle_match_method",
            "pending_lifecycle_source_timestamp_utc",
            "pending_lifecycle_checked_candle_time_utc",
        }:
            row[key] = value


def refresh_rows(
    rows: list[dict[str, Any]],
    pending_recompute: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    generated = utc_now()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if not is_pending_scorer_action_row(row):
            row.setdefault("pending_scorer_metadata_refresh_status", "NOT_TARGET_ROW")
            output.append(row)
            continue

        stats["target_rows"] += 1
        if has_metadata_gap(row):
            stats["target_metadata_gaps_before"] += 1
        recomputed = pending_recompute.get(str(row.get("candidate_id") or ""))
        if not recomputed:
            row["pending_scorer_metadata_refresh_status"] = "RECOMPUTE_ROW_MISSING"
            stats["target_recompute_missing"] += 1
            output.append(row)
            continue

        row["before_pending_scorer_metadata_refresh_branch_decision"] = row.get("branch_decision")
        row["before_pending_scorer_metadata_refresh_decision_evidence"] = row.get("decision_evidence")
        row["before_pending_scorer_metadata_refresh_scoring_boundary"] = row.get("scoring_boundary")
        row["before_pending_scorer_metadata_refresh_implementation_candidate"] = row.get(
            "implementation_candidate"
        )
        row["before_pending_scorer_metadata_refresh_current_action"] = row.get("current_action")
        row["before_pending_scorer_metadata_refresh_next_action"] = row.get("next_action")
        row["before_pending_scorer_metadata_refresh_data_requirement_state"] = row.get("data_requirement_state")
        row["pending_scorer_metadata_refresh_status"] = PENDING_REFRESH_STATUS
        row["pending_scorer_metadata_refresh_source"] = "src/research_infra/live_mechanical_shadow.py"
        row["pending_scorer_metadata_refresh_recomputed_strategy_status"] = recomputed.get("strategy_status")
        row["pending_scorer_metadata_refresh_recomputed_score_status"] = recomputed.get("score_status")
        row["pending_scorer_metadata_refresh_recomputed_outcome_status"] = recomputed.get("outcome_status")
        row["pending_scorer_metadata_refresh_recomputed_outcome_source"] = recomputed.get("outcome_source")
        row["pending_scorer_metadata_refresh_recomputed_proxy_r"] = recomputed.get("strategy_proxy_r")
        row["pending_scorer_metadata_refresh_proxy_r_matches_action_row"] = floats_equal(
            row.get("after_proxy_r"),
            recomputed.get("strategy_proxy_r"),
        )
        row["action_class"] = "KEEP"
        row["coverage_status"] = "KEPT_WITH_CURRENT_EVIDENCE"
        row["branch_decision"] = recomputed.get("branch_decision")
        row["decision_evidence"] = recomputed.get("decision_evidence")
        row["scoring_boundary"] = recomputed.get("scoring_boundary")
        row["implementation_candidate"] = recomputed.get("implementation_candidate")
        row["implementation_decision"] = recomputed.get("branch_decision")
        row["current_action"] = recomputed.get("implementation_candidate")
        row["next_action"] = recomputed.get("implementation_candidate")
        row["data_requirement_state"] = recomputed.get("score_status")
        copy_pending_source_fields(row, recomputed)
        if has_metadata_gap(row):
            stats["target_metadata_gaps_after"] += 1
        if row.get("current_action") != row.get("before_pending_scorer_metadata_refresh_current_action"):
            stats["target_current_action_changed"] += 1
        stats["target_rows_repaired"] += 1
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
    inputs = [INPUT_LEDGER, INPUT_SUMMARY, SCORER_SOURCE, *SHADOW_INPUTS.values()]
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
    pending_recompute = build_pending_recompute_map(utc_now())
    output_rows, stats = refresh_rows(input_rows, pending_recompute)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    input_target_rows = [row for row in input_rows if is_pending_scorer_action_row(row)]
    output_target_rows = [row for row in output_rows if is_pending_scorer_action_row(row)]
    before_actions = counter(input_rows, "action_class")
    after_actions = counter(output_rows, "action_class")
    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_PENDING_SCORER_METADATA_REFRESH",
        "claim_boundary": (
            "Patches pending-limit lifecycle scorer/source-capture decision metadata into current action rows. "
            "No proxy R, exact R, live behavior, shadow append, promotion, broker operation, or AI/API call is opened."
        ),
        "rows": len(output_rows),
        "target_rows": len(output_target_rows),
        "target_rows_repaired": stats.get("target_rows_repaired", 0),
        "target_recompute_missing": stats.get("target_recompute_missing", 0),
        "target_metadata_gaps_before": sum(1 for row in input_target_rows if has_metadata_gap(row)),
        "target_metadata_gaps_after": sum(1 for row in output_target_rows if has_metadata_gap(row)),
        "all_metadata_gaps_before": sum(1 for row in input_rows if has_metadata_gap(row)),
        "all_metadata_gaps_after": sum(1 for row in output_rows if has_metadata_gap(row)),
        "repair_stats": stats,
        "target_branch_decision_counts_after": counter(output_target_rows, "branch_decision"),
        "target_implementation_candidate_counts_after": counter(output_target_rows, "implementation_candidate"),
        "target_current_action_counts_after": counter(output_target_rows, "current_action"),
        "target_data_requirement_state_counts_after": counter(output_target_rows, "data_requirement_state"),
        "target_capture_complete_counts_after": counter(
            output_target_rows,
            "pending_lifecycle_source_capture_complete",
        ),
        "target_source_field_cell_counts_after": source_field_cell_counts(output_target_rows),
        "target_proxy_match_counts": counter(
            output_target_rows,
            "pending_scorer_metadata_refresh_proxy_r_matches_action_row",
        ),
        "metadata_refresh_status_counts": counter(output_rows, "pending_scorer_metadata_refresh_status"),
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
        "plate_decision": "PENDING_LIFECYCLE_SCORER_METADATA_MATERIALIZED_IN_CURRENT_ACTION_ROWS",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "target_rows": len(output_target_rows),
                "target_metadata_gaps_after": summary["target_metadata_gaps_after"],
                "all_metadata_gaps_after": summary["all_metadata_gaps_after"],
                "summary": str(OUTPUT_SUMMARY),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
