"""Refresh prefill delivery decisions after entry-offset repair.

This research-only builder consumes the latest prefill bucketed action queue and
the repaired entry-offset/M15 hard-no-fill ledger. It turns the prefill far-miss
bucket from a generic redesign bucket into current row-level branch decisions:
no-fill kills, retained far-miss retest redesign controls, and near-miss
default-off entry-offset challengers. Proxy R remains owned by the entry-offset
scorer and is carried as linked evidence, not duplicated onto prefill metadata
rows.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

INPUT_PREFILL_BUCKET_LEDGER = (
    ROUTE_DIR / f"MAIN_ORCH24_PREFILL_DELIVERY_BUCKETED_SCORER_OUTPUT_LEDGER_{DATE}.jsonl"
)
INPUT_ENTRY_REPAIR_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_LEDGER_2026-05-16.jsonl"
)
INPUT_ENTRY_REPAIR_SUMMARY = (
    ROUTE_DIR / "MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR_SUMMARY_2026-05-16.json"
)

OUTPUT_LEDGER = (
    ROUTE_DIR
    / f"MAIN_ORCH24_PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION_LEDGER_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"MAIN_ORCH24_PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION_SUMMARY_{DATE}.json"
)
OUTPUT_MANIFEST = (
    ROUTE_DIR
    / f"MAIN_ORCH24_PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION_OUTPUT_MANIFEST_{DATE}.json"
)

PREFILL_STRATEGY_ID = "PREFILL_DELIVERY_REVERSAL_PATH"

PREFILL_KEEP_IMPL = "KEEP_CURRENT_ENTRY_MODEL_NOT_IN_PREFILL_REDESIGN_DENOMINATOR"
PREFILL_NEAR_IMPL = "IMPLEMENT_DEFAULT_OFF_PREFILL_NEAR_MISS_ENTRY_OFFSET_050R_CHALLENGER"
PREFILL_FAR_REDESIGN_IMPL = "REDESIGN_PREFILL_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL"
PREFILL_FAR_KILL_IMPL = (
    "KILL_PREFILL_FAR_MISS_050R_OFFSET_NO_FILL_REQUIRES_WIDER_RETEST_OR_MARKET_CONTROL"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def proxy_stats(rows: list[dict[str, Any]], key: str = "after_proxy_r") -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get(key))) is not None]
    total = round(sum(values), 8)
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": total,
        "proxy_r_mean": round(total / len(values), 8) if values else None,
        "positive_rows": sum(value > 0 for value in values),
        "zero_rows": sum(value == 0 for value in values),
        "negative_rows": sum(value < 0 for value in values),
    }


def repair_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if cid:
            out[cid] = row
    return out


def prefill_decision_from_repair(repair: dict[str, Any]) -> tuple[str, str, str, str, str]:
    action = str(repair.get("after_prefill_action_class") or "")
    branch = str(repair.get("after_prefill_branch_decision") or "")
    scorer_status = str(repair.get("after_entry_scorer_status") or "")
    if action == "KEEP":
        return (
            "KEEP",
            PREFILL_KEEP_IMPL,
            "KEPT_OUTSIDE_PREFILL_REDESIGN_DENOMINATOR",
            "NOT_APPLICABLE_OUTSIDE_NO_FILL_TP1_PREFILL_REDESIGN_DENOMINATOR",
            "NONE_CURRENT_ENTRY_ALREADY_TOUCHED_OR_NOT_TP1_NO_FILL",
        )
    if action == "IMPLEMENT_DEFAULT_OFF":
        return (
            "IMPLEMENT_DEFAULT_OFF",
            PREFILL_NEAR_IMPL,
            "IMPLEMENTATION_CANDIDATE_LINKED_ENTRY_OFFSET_SCORER_NO_DUPLICATE_PREFILL_R",
            "METADATA_ONLY_PROXY_R_OWNED_BY_ENTRY_OFFSET_050R_SCORER",
            "ENTRY_OFFSET_050R_NEAR_MISS_SPREAD_AWARE_CHALLENGER",
        )
    if action == "KILL" and scorer_status == "KILLED_ENTRY_OFFSET_050R_M15_HARD_NO_FILL":
        return (
            "KILL",
            PREFILL_FAR_KILL_IMPL,
            "KILLED_BY_M15_HARD_NO_FILL_ENTRY_OFFSET_REPAIR",
            "M15_HARD_NO_FILL_REPAIR_PROVES_050R_PREFILL_FAR_MISS_CONTROL_NO_FILL",
            "NONE_FAR_MISS_050R_NO_FILL_KEEP_AS_RETEST_REDESIGN_FAILURE",
        )
    if action == "KILL":
        return (
            "KILL",
            PREFILL_FAR_KILL_IMPL,
            "KILLED_BY_SPREAD_AWARE_ENTRY_OFFSET_REPLAY",
            "SPREAD_AWARE_TICK_REPLAY_PROVES_050R_PREFILL_FAR_MISS_CONTROL_NO_FILL",
            "NONE_FAR_MISS_050R_NO_FILL_KEEP_AS_RETEST_REDESIGN_FAILURE",
        )
    if action == "REDESIGN" and branch == "REDESIGN_PREFILL_FAR_MISS_RETEST_WITH_050R_OFFSET_CONTROL":
        return (
            "REDESIGN",
            PREFILL_FAR_REDESIGN_IMPL,
            "RETAIN_FAR_MISS_RETEST_REDESIGN_CONTROL_WITH_POSITIVE_050R_PROXY",
            "FAR_MISS_050R_RETEST_CONTROL_PROXY_OWNED_BY_ENTRY_OFFSET_SCORER",
            "ENTRY_OFFSET_050R_FAR_MISS_RETEST_CONTROL_NOT_DEFAULT_ENTRY",
        )
    return (
        "SOURCE_REPAIR",
        "SOURCE_REPAIR_REQUIRED_PREFILL_ENTRY_OFFSET_REPAIR_JOIN",
        "SOURCE_REPAIR_REQUIRED_FOR_PREFILL_ENTRY_OFFSET_REPAIR_JOIN",
        "NO_PREFILL_BRANCH_DECISION_WITHOUT_REPAIRED_ENTRY_OFFSET_ROW",
        "REPAIR_PREFILL_TO_ENTRY_OFFSET_CANDIDATE_JOIN",
    )


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    source_rows = read_jsonl(INPUT_PREFILL_BUCKET_LEDGER)
    repair_rows = read_jsonl(INPUT_ENTRY_REPAIR_LEDGER)
    repair_summary = read_json(INPUT_ENTRY_REPAIR_SUMMARY)
    repairs = repair_by_candidate(repair_rows)

    out: list[dict[str, Any]] = []
    target_rows = 0
    missing_repair_rows = 0
    linked_before_values: list[float] = []
    linked_after_values: list[float] = []
    repaired_candidate_ids: list[str] = []

    for idx, row in enumerate(source_rows, start=1):
        new = dict(row)
        new.pop("_source_line_no", None)
        if row.get("strategy_id") != PREFILL_STRATEGY_ID:
            new["prefill_after_entry_offset_repair_status"] = "NOT_TARGET_ROW"
            out.append(new)
            continue

        target_rows += 1
        cid = str(row.get("candidate_id") or "")
        repair = repairs.get(cid)
        new["source_line_no"] = row.get("source_line_no") or idx
        new["before_after_entry_offset_repair_action_class"] = row.get("action_class")
        new["before_after_entry_offset_repair_implementation_decision"] = row.get(
            "implementation_decision"
        )
        new["before_after_entry_offset_repair_branch_decision"] = row.get("branch_decision")
        new["before_after_entry_offset_repair_scoring_boundary"] = row.get("scoring_boundary")
        new["before_after_entry_offset_repair_proxy_r"] = row.get("after_proxy_r")
        new["generated_utc"] = generated
        new["safe_flags"] = SAFE_FLAGS
        new["no_promotion"] = True
        new["no_live_behavior"] = True
        new["no_shadow_log_append"] = True
        new["exact_r"] = None
        new["after_proxy_r"] = None
        new["proxy_r_delta"] = None
        new["prefill_after_entry_offset_repair_status"] = "REPAIRED_ENTRY_OFFSET_BRANCH_JOIN"
        new["source_capture_surface"] = "prefill_delivery_after_entry_offset_repair_decision"
        new["primitive_family"] = "prefill_delivery_adverse_reversal_path"
        new["source_artifact"] = str(INPUT_ENTRY_REPAIR_LEDGER)

        before_linked_proxy = safe_float(row.get("linked_entry_offset_selected_proxy_r"))
        if before_linked_proxy is not None:
            linked_before_values.append(before_linked_proxy)

        if repair is None:
            missing_repair_rows += 1
            new.update(
                {
                    "action_class": "SOURCE_REPAIR",
                    "implementation_decision": "SOURCE_REPAIR_REQUIRED_PREFILL_ENTRY_OFFSET_REPAIR_JOIN",
                    "branch_decision": "SOURCE_REPAIR_REQUIRED_FOR_PREFILL_ENTRY_OFFSET_REPAIR_JOIN",
                    "decision_evidence": "MISSING_ENTRY_OFFSET_REPAIR_ROW_FOR_PREFILL_CANDIDATE",
                    "scoring_boundary": "NO_PREFILL_BRANCH_DECISION_WITHOUT_REPAIRED_ENTRY_OFFSET_ROW",
                    "implementation_candidate": "REPAIR_PREFILL_TO_ENTRY_OFFSET_CANDIDATE_JOIN",
                    "coverage_status": "SOURCE_REPAIR_REQUIRED_FOR_PREFILL_ENTRY_OFFSET_REPAIR_JOIN",
                    "current_action": "SOURCE_REPAIR_REQUIRED_PREFILL_ENTRY_OFFSET_REPAIR_JOIN",
                    "next_action": "REPAIR_PREFILL_TO_ENTRY_OFFSET_CANDIDATE_JOIN",
                    "data_requirement_state": "SOURCE_REPAIR_REQUIRED_PREFILL_ENTRY_OFFSET_REPAIR_JOIN",
                }
            )
            out.append(new)
            continue

        action, impl, coverage, data_state, next_action = prefill_decision_from_repair(repair)
        after_linked_proxy = safe_float(repair.get("after_prefill_proxy_r"))
        if after_linked_proxy is not None:
            linked_after_values.append(after_linked_proxy)
        if repair.get("m15_hard_no_fill_repaired") is True:
            repaired_candidate_ids.append(cid)

        new.update(
            {
                "action_class": action,
                "implementation_decision": impl,
                "coverage_status": coverage,
                "current_action": impl,
                "next_action": next_action,
                "data_requirement_state": data_state,
                "branch_decision": repair.get("after_prefill_branch_decision"),
                "decision_evidence": (
                    "MAIN_ORCH24_ENTRY_OFFSET_M15_HARD_NO_FILL_REPAIR joined to prefill "
                    "far-miss/near-miss rows; prefill metadata rows inherit kill/redesign "
                    "decisions while linked proxy R remains owned by entry-offset scorer."
                ),
                "scoring_boundary": data_state,
                "implementation_candidate": next_action,
                "linked_entry_offset_before_action_class": repair.get("before_entry_action_class"),
                "linked_entry_offset_after_action_class": repair.get("after_entry_action_class"),
                "linked_entry_offset_before_branch_decision": repair.get(
                    "before_entry_branch_decision"
                ),
                "linked_entry_offset_after_branch_decision": repair.get(
                    "after_entry_branch_decision"
                ),
                "linked_entry_offset_before_score_status": repair.get("before_entry_score_status"),
                "linked_entry_offset_after_score_status": repair.get("after_entry_score_status"),
                "linked_entry_offset_before_scorer_status": repair.get(
                    "before_entry_scorer_status"
                ),
                "linked_entry_offset_after_scorer_status": repair.get("after_entry_scorer_status"),
                "linked_entry_offset_before_proxy_r": repair.get("before_entry_proxy_r"),
                "linked_entry_offset_after_proxy_r": repair.get("after_entry_proxy_r"),
                "linked_prefill_before_action_class": repair.get("before_prefill_action_class"),
                "linked_prefill_after_action_class": repair.get("after_prefill_action_class"),
                "linked_prefill_before_branch_decision": repair.get(
                    "before_prefill_branch_decision"
                ),
                "linked_prefill_after_branch_decision": repair.get("after_prefill_branch_decision"),
                "linked_prefill_before_proxy_r": repair.get("before_prefill_proxy_r"),
                "linked_prefill_after_proxy_r": repair.get("after_prefill_proxy_r"),
                "linked_prefill_proxy_r_owner": "ENTRY_OFFSET_050R_SPREAD_AWARE_CHALLENGER",
                "m15_hard_no_fill_repaired": repair.get("m15_hard_no_fill_repaired"),
                "m15_hard_no_fill_proof_status": repair.get("m15_hard_no_fill_proof_status"),
                "m15_nearest_distance_to_entry_r": repair.get("m15_nearest_distance_to_entry_r"),
                "path_outcome_status": repair.get("path_outcome_status"),
                "ltf_terminal_outcome_status": repair.get("ltf_terminal_outcome_status"),
                "latest_ltf_entry_first_touch_utc": repair.get("latest_ltf_entry_first_touch_utc"),
                "tick_source_status": repair.get("tick_source_status"),
                "tick_source_files": repair.get("tick_source_files"),
                "tick_source_read_error_files": repair.get("tick_source_read_error_files"),
                "manual_backfill_status": "PREFILL_BRANCH_DECISION_REFRESHED_AFTER_ENTRY_OFFSET_REPAIR",
            }
        )
        out.append(new)

    before_actions = Counter(row.get("action_class") for row in source_rows)
    after_actions = Counter(row.get("action_class") for row in out)
    before_impl = Counter(row.get("implementation_decision") for row in source_rows)
    after_impl = Counter(row.get("implementation_decision") for row in out)
    target_after = [row for row in out if row.get("strategy_id") == PREFILL_STRATEGY_ID]
    target_before = [row for row in source_rows if row.get("strategy_id") == PREFILL_STRATEGY_ID]
    target_actions_before = Counter(row.get("action_class") for row in target_before)
    target_actions_after = Counter(row.get("action_class") for row in target_after)
    target_impl_after = Counter(row.get("implementation_decision") for row in target_after)
    target_branch_after = Counter(row.get("branch_decision") for row in target_after)
    linked_before_total = round(sum(linked_before_values), 8)
    linked_after_total = round(sum(linked_after_values), 8)

    before_proxy = proxy_stats(source_rows)
    after_proxy = proxy_stats(out)
    summary = {
        "route_id": ROUTE_ID,
        "evidence_class": "MAIN_ORCH24_PREFILL_AFTER_ENTRY_OFFSET_REPAIR_DECISION",
        "generated_utc": generated,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": (
            "Versioned action queue after joining repaired entry-offset/M15 hard-no-fill "
            "decisions back into prefill delivery rows. Prefill rows carry branch decisions "
            "only; linked proxy R remains owned by the entry-offset scorer."
        ),
        "rows": len(out),
        "input_action_rows": len(source_rows),
        "prefill_target_rows": target_rows,
        "missing_repair_join_rows": missing_repair_rows,
        "prefill_target_action_class_counts_before": dict(sorted(target_actions_before.items())),
        "prefill_target_action_class_counts_after": dict(sorted(target_actions_after.items())),
        "prefill_target_implementation_decision_counts_after": dict(
            sorted(target_impl_after.items())
        ),
        "prefill_target_branch_decision_counts_after": dict(sorted(target_branch_after.items())),
        "action_class_counts_before": dict(sorted(before_actions.items())),
        "action_class_counts_after": dict(sorted(after_actions.items())),
        "action_class_delta_vs_previous": {
            key: after_actions.get(key, 0) - before_actions.get(key, 0)
            for key in sorted(set(before_actions) | set(after_actions))
            if after_actions.get(key, 0) - before_actions.get(key, 0)
        },
        "implementation_decision_counts_before": dict(sorted(before_impl.items())),
        "implementation_decision_counts_after": dict(sorted(after_impl.items())),
        "proxy_before": before_proxy,
        "proxy_after": after_proxy,
        "prefill_metadata_numeric_proxy_rows": 0,
        "prefill_metadata_proxy_r_sum": 0.0,
        "numeric_proxy_row_delta": after_proxy["numeric_proxy_rows"] - before_proxy["numeric_proxy_rows"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "linked_entry_offset_before_numeric_proxy_rows": len(linked_before_values),
        "linked_entry_offset_after_numeric_proxy_rows": len(linked_after_values),
        "linked_entry_offset_numeric_proxy_row_delta": len(linked_after_values)
        - len(linked_before_values),
        "linked_entry_offset_before_proxy_r_sum": linked_before_total,
        "linked_entry_offset_after_proxy_r_sum": linked_after_total,
        "linked_entry_offset_proxy_r_sum_delta": round(
            linked_after_total - linked_before_total, 8
        ),
        "m15_hard_no_fill_repaired_rows": len(repaired_candidate_ids),
        "m15_hard_no_fill_repaired_candidate_ids": sorted(repaired_candidate_ids),
        "entry_repair_summary_after_prefill_action_class_counts": repair_summary.get(
            "after_prefill_action_class_counts"
        ),
        "exact_r_rows": 0,
        "safe_flag_boundary": (
            "NO_PROMOTION_VERDICT; validation_safe=false; outcome_review_opened=false; "
            "live_effect=false; no shadow log append."
        ),
        "plate_decision": "PREFILL_FAR_MISS_ROWS_REFRESHED_FROM_REPAIRED_ENTRY_OFFSET_BRANCH_DECISIONS",
    }
    return out, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    inputs = {
        "prefill_bucket_ledger": INPUT_PREFILL_BUCKET_LEDGER,
        "entry_offset_m15_hard_no_fill_repair_ledger": INPUT_ENTRY_REPAIR_LEDGER,
        "entry_offset_m15_hard_no_fill_repair_summary": INPUT_ENTRY_REPAIR_SUMMARY,
    }
    outputs = {
        "ledger": OUTPUT_LEDGER,
        "summary": OUTPUT_SUMMARY,
    }
    return {
        "route_id": ROUTE_ID,
        "evidence_class": summary["evidence_class"],
        "generated_utc": summary["generated_utc"],
        "safe_flags": SAFE_FLAGS,
        "inputs": {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "bytes": path.stat().st_size if path.exists() else None,
            }
            for name, path in inputs.items()
        },
        "outputs": {
            name: {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
            for name, path in outputs.items()
        },
        "summary_counts": {
            "rows": summary["rows"],
            "prefill_target_rows": summary["prefill_target_rows"],
            "prefill_target_action_class_counts_after": summary[
                "prefill_target_action_class_counts_after"
            ],
            "action_class_delta_vs_previous": summary["action_class_delta_vs_previous"],
            "linked_entry_offset_numeric_proxy_row_delta": summary[
                "linked_entry_offset_numeric_proxy_row_delta"
            ],
            "linked_entry_offset_proxy_r_sum_delta": summary[
                "linked_entry_offset_proxy_r_sum_delta"
            ],
            "exact_r_rows": summary["exact_r_rows"],
        },
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary))
    print(
        json.dumps(
            {
                "ok": True,
                "rows": summary["rows"],
                "prefill_target_rows": summary["prefill_target_rows"],
                "target_actions_after": summary["prefill_target_action_class_counts_after"],
                "action_delta": summary["action_class_delta_vs_previous"],
                "linked_proxy_rows_delta": summary["linked_entry_offset_numeric_proxy_row_delta"],
                "linked_proxy_r_delta": summary["linked_entry_offset_proxy_r_sum_delta"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
