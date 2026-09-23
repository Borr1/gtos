#!/usr/bin/env python3
"""Build a de-duplicated possible-avoid challenger packet for source silence."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

SOURCE_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_ROUTE_C_JOIN_LEDGER_{STAMP}.jsonl"
NO_API_DESIGN_TEST_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_NO_API_DESIGN_TEST_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEDUP_RESULT_{STAMP}.json"
TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEDUP_TARGET_LEDGER_{STAMP}.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEDUP_CONTROL_LEDGER_{STAMP}.jsonl"
STRESS_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEDUP_STRESS_LEDGER_{STAMP}.jsonl"
DECISION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEDUP_DECISION_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEDUP_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEDUP_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "De-duplicated source-silence possible-avoid challenger packet; source-control/design "
    "evidence only, with no strategy validation, trade outcome, R/PnL, expectancy, "
    "live-readiness, or live deployment"
)

POSSIBLE_AVOID_STATUS = "NO_API_TEST_DESIGN_POSSIBLE_AVOID_UNDERPOWERED_CONTROL"
EXACT_FEATURE_STATUSES = {
    "LADDER_FEATURE_JOINED",
    "LADDER_FEATURE_JOINED_AFTER_IN_WINDOW_CLEAR_REPAIR",
    "LADDER_FEATURE_AND_BLOCKER_BUCKET_JOINED",
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relative(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def bool_value(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def share(values: list[bool]) -> float | None:
    return sum(1 for value in values if value) / len(values) if values else None


def numeric_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def hhi(values: list[Any]) -> float | None:
    if not values:
        return None
    counts = Counter(str(value) for value in values)
    total = sum(counts.values())
    return sum((count / total) ** 2 for count in counts.values())


def row_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    alignments = [value for row in rows if (value := bool_value(row.get("route_c_delta_aligned_with_future"))) is not None]
    future_change = [
        value for row in rows
        if (value := safe_float(row.get("route_c_future_change_per_current_range"))) is not None
    ]
    return {
        "n": len(rows),
        "route_alignment_share": share(alignments),
        "route_alignment_n": len(alignments),
        "mean_route_c_future_change_per_current_range": mean(future_change),
        "source_date_count": len({str(row.get("source_date")) for row in rows if row.get("source_date")}),
        "source_date_hhi": hhi([row.get("source_date") for row in rows if row.get("source_date")]),
        "source_symbol_counts": counter_dict(row.get("source_symbol") for row in rows),
        "source_symbol_hhi": hhi([row.get("source_symbol") for row in rows if row.get("source_symbol")]),
        "queue_counts": counter_dict(row.get("queue_id") or row.get("route_c_queue_id") for row in rows),
        "command_feature_bucket_counts": counter_dict(row.get("command_feature_bucket") for row in rows),
    }


def build_dedup_targets(design_rows: list[dict[str, Any]], source_join_by_request: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in design_rows:
        if row.get("design_no_api_test_status") == POSSIBLE_AVOID_STATUS:
            grouped[str(row.get("request_id"))].append(row)

    outputs: list[dict[str, Any]] = []
    for request_id, rows in sorted(grouped.items()):
        first = rows[0]
        source = source_join_by_request.get(request_id, {})
        outputs.append(
            {
                "target_id": f"SIERRA-LADDER-SOURCE-SILENCE-POSSIBLE-AVOID-DEDUP-TARGET-{len(outputs) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "request_id": request_id,
                "source_symbol": first.get("source_symbol"),
                "source_date": first.get("source_date"),
                "queue_id": first.get("queue_id"),
                "route_c_symbol": source.get("route_c_symbol"),
                "source_silence_family": first.get("source_silence_family"),
                "source_silence_status": first.get("source_silence_status"),
                "neighbor_bucket": first.get("neighbor_bucket"),
                "command_feature_bucket": first.get("command_feature_bucket"),
                "route_c_delta_aligned_with_future": first.get("route_c_delta_aligned_with_future"),
                "route_c_future_change_per_current_range": first.get("route_c_future_change_per_current_range"),
                "feature_neighbor_route_alignment_share": first.get("feature_neighbor_route_alignment_share"),
                "feature_neighbor_route_alignment_n": first.get("feature_neighbor_route_alignment_n"),
                "design_row_count": len(rows),
                "design_statuses": sorted({str(row.get("source_silence_design_status")) for row in rows}),
                "mutation_types": sorted({str(row.get("mutation_type")) for row in rows}),
                "mutation_ids": sorted({str(row.get("mutation_id")) for row in rows}),
                "depth_path": source.get("depth_path"),
                "depth_file_exists": source.get("depth_file_exists"),
                "candidate_interpretation": "possible_avoid_underpowered_source_silence_context_after_dedup",
            }
        )
    return outputs


def exact_feature_rows(source_join: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES and not row.get("source_silence_joined")
    ]


def control_rows_for_scope(targets: list[dict[str, Any]], exact_rows: list[dict[str, Any]], scope: str) -> list[dict[str, Any]]:
    queues = {row.get("queue_id") for row in targets if row.get("queue_id")}
    commands = {row.get("command_feature_bucket") for row in targets if row.get("command_feature_bucket")}
    symbols = {row.get("source_symbol") for row in targets if row.get("source_symbol")}
    pairs = {(row.get("queue_id"), row.get("command_feature_bucket")) for row in targets}
    if scope == "matched_queue_command_exact_feature":
        return [
            row for row in exact_rows
            if (row.get("route_c_queue_id"), row.get("command_feature_bucket")) in pairs
        ]
    if scope == "matched_queue_exact_feature":
        return [row for row in exact_rows if row.get("route_c_queue_id") in queues]
    if scope == "matched_command_exact_feature":
        return [row for row in exact_rows if row.get("command_feature_bucket") in commands]
    if scope == "matched_source_symbol_exact_feature":
        return [row for row in exact_rows if row.get("source_symbol") in symbols]
    if scope == "all_exact_feature":
        return list(exact_rows)
    raise ValueError(scope)


def build_control_rows(targets: list[dict[str, Any]], exact_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidate_stats = row_stats(targets)
    for scope in [
        "matched_queue_command_exact_feature",
        "matched_queue_exact_feature",
        "matched_command_exact_feature",
        "matched_source_symbol_exact_feature",
        "all_exact_feature",
    ]:
        control = control_rows_for_scope(targets, exact_rows, scope)
        control_stats = row_stats(control)
        rows.append(
            {
                "control_id": f"SIERRA-LADDER-SOURCE-SILENCE-POSSIBLE-AVOID-DEDUP-CONTROL-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "control_scope": scope,
                "candidate_rows": candidate_stats,
                "control_rows": control_stats,
                "route_alignment_delta_vs_control": numeric_delta(
                    candidate_stats.get("route_alignment_share"),
                    control_stats.get("route_alignment_share"),
                ),
                "mean_future_change_delta_vs_control": numeric_delta(
                    candidate_stats.get("mean_route_c_future_change_per_current_range"),
                    control_stats.get("mean_route_c_future_change_per_current_range"),
                ),
                "control_interpretation": interpret_control(candidate_stats, control_stats),
            }
        )
    return rows


def interpret_control(candidate_stats: dict[str, Any], control_stats: dict[str, Any]) -> str:
    candidate_n = int(candidate_stats["n"])
    control_n = int(control_stats["n"])
    delta = numeric_delta(candidate_stats.get("route_alignment_share"), control_stats.get("route_alignment_share"))
    if control_n == 0:
        return "CONTROL_EMPTY_ACQUIRE_OR_PROXY"
    if candidate_n < 20:
        return "CANDIDATE_UNDERPOWERED_UNIQUE_N_LT_20"
    if delta is not None and delta <= -0.05:
        return "DEDUP_POSSIBLE_AVOID_LOWER_ALIGNMENT_THAN_CONTROL"
    if delta is not None and abs(delta) <= 0.05:
        return "DEDUP_NEAR_CONTROL"
    return "DEDUP_MIXED_OR_NOT_AVOID"


def build_stress_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    full_stats = row_stats(targets)
    axes = [
        ("source_date", "source_date"),
        ("source_symbol", "source_symbol"),
        ("queue_id", "queue_id"),
        ("command_feature_bucket", "command_feature_bucket"),
    ]
    for axis_name, field in axes:
        values = sorted({str(row.get(field)) for row in targets if row.get(field) is not None})
        for value in values:
            kept = [row for row in targets if str(row.get(field)) != value]
            removed = [row for row in targets if str(row.get(field)) == value]
            kept_stats = row_stats(kept)
            removed_stats = row_stats(removed)
            rows.append(
                {
                    "stress_id": f"SIERRA-LADDER-SOURCE-SILENCE-POSSIBLE-AVOID-DEDUP-STRESS-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "stress_axis": axis_name,
                    "removed_value": value,
                    "full_rows": full_stats,
                    "kept_rows": kept_stats,
                    "removed_rows": removed_stats,
                    "alignment_delta_after_removal": numeric_delta(
                        kept_stats.get("route_alignment_share"),
                        full_stats.get("route_alignment_share"),
                    ),
                    "stress_interpretation": interpret_stress(full_stats, kept_stats),
                }
            )
    return rows


def interpret_stress(full_stats: dict[str, Any], kept_stats: dict[str, Any]) -> str:
    if int(kept_stats["n"]) < 20:
        return "LEAVE_ONE_UNDERPOWERED_AFTER_REMOVAL"
    delta = numeric_delta(kept_stats.get("route_alignment_share"), full_stats.get("route_alignment_share"))
    if delta is not None and abs(delta) <= 0.05:
        return "LEAVE_ONE_ALIGNMENT_STABLE"
    return "LEAVE_ONE_ALIGNMENT_SHIFTS"


def build_decision_rows(targets: list[dict[str, Any]], controls: list[dict[str, Any]], stresses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_stats = row_stats(targets)
    control_counts = Counter(row["control_interpretation"] for row in controls)
    stress_counts = Counter(row["stress_interpretation"] for row in stresses)
    lower_alignment_controls = control_counts.get("DEDUP_POSSIBLE_AVOID_LOWER_ALIGNMENT_THAN_CONTROL", 0)
    stable_stresses = stress_counts.get("LEAVE_ONE_ALIGNMENT_STABLE", 0)
    if candidate_stats["n"] < 20:
        decision = "POSSIBLE_AVOID_DEDUP_UNDERPOWERED_KEEP_AS_CHALLENGER_QUEUE"
    elif lower_alignment_controls >= 3 and stable_stresses >= 3:
        decision = "POSSIBLE_AVOID_DEDUP_CHALLENGER_PACKET_SURVIVES_INITIAL_CONTROLS"
    elif lower_alignment_controls >= 1:
        decision = "POSSIBLE_AVOID_DEDUP_PARTIAL_CONTROL_SUPPORT_NEEDS_DEEPER_SPLIT"
    else:
        decision = "POSSIBLE_AVOID_DEDUP_WEAK_OR_CONTROL_EXPLAINED"
    return [
        {
            "decision_id": "SIERRA-LADDER-SOURCE-SILENCE-POSSIBLE-AVOID-DEDUP-DECISION-00001",
            "route_id": ROUTE_ID,
            "safe_flags": SAFE_FLAGS,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "candidate_rows": candidate_stats,
            "control_interpretation_counts": dict(sorted(control_counts.items())),
            "stress_interpretation_counts": dict(sorted(stress_counts.items())),
            "decision_status": decision,
            "not_promotion": "Decision is branch-local challenger/source-control design only.",
            "next_same_resource_action": next_action_for_decision(decision),
        }
    ]


def next_action_for_decision(decision: str) -> str:
    if decision == "POSSIBLE_AVOID_DEDUP_CHALLENGER_PACKET_SURVIVES_INITIAL_CONTROLS":
        return "build sealed no-API challenger spec with source/date/queue stress and exact-feature controls"
    if decision == "POSSIBLE_AVOID_DEDUP_PARTIAL_CONTROL_SUPPORT_NEEDS_DEEPER_SPLIT":
        return "split by queue, command bucket, source date, and source symbol; then rerun matched controls"
    if decision == "POSSIBLE_AVOID_DEDUP_UNDERPOWERED_KEEP_AS_CHALLENGER_QUEUE":
        return "preserve as challenger queue and acquire/proxy more exact same-source rows"
    return "preserve failure/control explanation and convert useful parts into acquisition or avoid-test mutations"


def build_questions(decisions: list[dict[str, Any]], controls: list[dict[str, Any]], stresses: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for decision in decisions:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-POSSIBLE-AVOID-DEDUP-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "decision",
                "question_key": decision["decision_status"],
                "question": "What challenger, split, or kill action follows from the de-duplicated possible-avoid packet?",
                "next_same_resource_action": decision["next_same_resource_action"],
                "counts_context": counts,
            }
        )
    for control in controls:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-POSSIBLE-AVOID-DEDUP-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "control_scope",
                "question_key": control["control_scope"],
                "question": "Does this matched exact-feature control explain or preserve the possible-avoid branch?",
                "next_same_resource_action": "use this control scope in the next split or challenger packet",
                "counts_context": counts,
            }
        )
    stress_counter = Counter(row["stress_interpretation"] for row in stresses)
    for status, count in sorted(stress_counter.items()):
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-POSSIBLE-AVOID-DEDUP-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "leave_one_stress",
                "question_key": status,
                "row_count": count,
                "question": "Which concentration axis should be split or expanded next for this stress result?",
                "next_same_resource_action": "split by the unstable axis or acquire/proxy exact rows for underpowered axes",
                "counts_context": counts,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_possible_avoid_dedup_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_possible_avoid_dedup_result", "created"),
        (TARGET_LEDGER, "sierra_depth_ladder_source_silence_possible_avoid_dedup_target_ledger", "created"),
        (CONTROL_LEDGER, "sierra_depth_ladder_source_silence_possible_avoid_dedup_control_ledger", "created"),
        (STRESS_LEDGER, "sierra_depth_ladder_source_silence_possible_avoid_dedup_stress_ledger", "created"),
        (DECISION_LEDGER, "sierra_depth_ladder_source_silence_possible_avoid_dedup_decision_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_possible_avoid_dedup_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_possible_avoid_dedup_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], decision_status: str) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_possible_avoid_dedup",
        "status": "done",
        "route": "source_silence_possible_avoid_deduplicated_challenger_packet",
        "details": "De-duplicated the possible-avoid source-silence branch by request_id and compared it against exact-feature controls and leave-one concentration stresses.",
        "counts": counts,
        "decision_status": decision_status,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(TARGET_LEDGER),
            relative(CONTROL_LEDGER),
            relative(STRESS_LEDGER),
            relative(DECISION_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], decisions: list[dict[str, Any]]) -> None:
    decision = decisions[0]
    lines = [
        "# Sierra Depth Ladder Source Silence Possible-Avoid Dedup Packet",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: de-duplicated source-control/challenger design only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- `decision_status`: `{decision['decision_status']}`",
            f"- `next_same_resource_action`: {decision['next_same_resource_action']}",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    design_tests = read_jsonl(NO_API_DESIGN_TEST_LEDGER)
    source_join_by_request = {str(row.get("request_id")): row for row in source_join}
    exact_rows = exact_feature_rows(source_join)
    possible_design_rows = [
        row for row in design_tests
        if row.get("design_no_api_test_status") == POSSIBLE_AVOID_STATUS
    ]
    targets = build_dedup_targets(possible_design_rows, source_join_by_request)
    controls = build_control_rows(targets, exact_rows)
    stresses = build_stress_rows(targets)
    decisions = build_decision_rows(targets, controls, stresses)
    counts = {
        "source_join_input_rows": len(source_join),
        "exact_feature_control_rows": len(exact_rows),
        "possible_avoid_design_rows": len(possible_design_rows),
        "dedup_target_rows": len(targets),
        "duplicate_design_rows_removed": len(possible_design_rows) - len(targets),
        "control_rows": len(controls),
        "stress_rows": len(stresses),
        "decision_rows": len(decisions),
        "question_rows": 0,
    }
    questions = build_questions(decisions, controls, stresses, counts)
    counts["question_rows"] = len(questions)

    write_jsonl(TARGET_LEDGER, targets)
    write_jsonl(CONTROL_LEDGER, controls)
    write_jsonl(STRESS_LEDGER, stresses)
    write_jsonl(DECISION_LEDGER, decisions)
    write_jsonl(QUESTION_LEDGER, questions)
    result = {
        "schema": "sierra_depth_ladder_source_silence_possible_avoid_dedup_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEDUP_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "decision_status": decisions[0]["decision_status"],
        "not_completion": "This de-duplicated possible-avoid packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [decisions[0]["next_same_resource_action"]],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, decisions[0]["decision_status"])
    write_summary(generated_utc, counts, decisions)
    print(json.dumps({"ok": True, "counts": counts, "decision_status": decisions[0]["decision_status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
