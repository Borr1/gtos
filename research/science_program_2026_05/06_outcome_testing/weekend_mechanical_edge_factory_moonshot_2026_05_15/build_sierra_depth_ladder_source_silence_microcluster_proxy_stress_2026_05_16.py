#!/usr/bin/env python3
"""Deduplicate/stress microcluster proxy pairs and integrate boundaries."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

PROXY_TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_TARGET_LEDGER_{STAMP}.jsonl"
PROXY_PAIR_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_PAIR_LEDGER_{STAMP}.jsonl"
PROXY_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_CONTROL_LEDGER_{STAMP}.jsonl"
MUTATION_BOUNDARY_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_MUTATION_BOUNDARY_LEDGER_{STAMP}.jsonl"
SOURCE_REQUIREMENT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_REQUIREMENT_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_STRESS_RESULT_{STAMP}.json"
TARGET_SUMMARY_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_TARGET_SUMMARY_LEDGER_{STAMP}.jsonl"
RELATION_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_RELATION_CONTROL_LEDGER_{STAMP}.jsonl"
LEAVE_ONE_STRESS_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_LEAVE_ONE_STRESS_LEDGER_{STAMP}.jsonl"
BOUNDARY_INTEGRATION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_BOUNDARY_INTEGRATION_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_STRESS_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_STRESS_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_STRESS_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra source-silence micro-cluster proxy pair stress and branch-local "
    "mutation-boundary integration only; descriptor/source-control evidence with "
    "no strategy validation, trade outcome, R/PnL, expectancy, live-readiness, "
    "or live deployment"
)


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


def bool_value(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def share(values: list[bool]) -> float | None:
    return sum(1 for value in values if value) / len(values) if values else None


def numeric_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def alignment_stats_from_rows(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = [value for row in rows if (value := bool_value(row.get(field))) is not None]
    return {
        "n": len(rows),
        "alignment_n": len(values),
        "alignment_share": share(values),
    }


def alignment_stats_from_pairs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    target_values = [value for row in rows if (value := bool_value(row.get("target_alignment"))) is not None]
    control_values = [value for row in rows if (value := bool_value(row.get("control_alignment"))) is not None]
    unique_controls = {str(row.get("control_request_id")) for row in rows if row.get("control_request_id")}
    unique_targets = {str(row.get("target_request_id")) for row in rows if row.get("target_request_id")}
    target_share = share(target_values)
    control_share = share(control_values)
    return {
        "pair_rows": len(rows),
        "unique_target_count": len(unique_targets),
        "unique_control_count": len(unique_controls),
        "target_alignment_n": len(target_values),
        "target_alignment_share": target_share,
        "control_alignment_n": len(control_values),
        "control_alignment_share": control_share,
        "target_minus_control_alignment_share": numeric_delta(target_share, control_share),
        "source_requirement_counts": counter_dict(row.get("source_requirement_id") for row in rows),
        "target_source_symbol_counts": counter_dict(row.get("target_source_symbol") for row in rows),
        "control_source_symbol_counts": counter_dict(row.get("control_source_symbol") for row in rows),
        "target_queue_counts": counter_dict(row.get("target_queue_id") for row in rows),
        "control_queue_counts": counter_dict(row.get("control_queue_id") for row in rows),
        "target_command_bucket_counts": counter_dict(row.get("target_command_feature_bucket") for row in rows),
        "control_command_bucket_counts": counter_dict(row.get("control_command_feature_bucket") for row in rows),
    }


def build_target_summaries(targets: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pairs:
        pairs_by_target[str(pair.get("target_request_id"))].append(pair)
    rows: list[dict[str, Any]] = []
    for target in targets:
        request_id = str(target["request_id"])
        target_pairs = pairs_by_target.get(request_id, [])
        stats = alignment_stats_from_pairs(target_pairs)
        relation_counts = Counter()
        for pair in target_pairs:
            for relation in pair.get("pair_relations", []):
                relation_counts[str(relation)] += 1
        rows.append(
            {
                "target_summary_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-TARGET-SUM-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "request_id": request_id,
                "source_requirement_id": target.get("source_requirement_id"),
                "proxy_target_status": target.get("proxy_target_status"),
                "candidate_replay_bucket": target.get("candidate_replay_bucket"),
                "source_search_decision_bucket": target.get("source_search_decision_bucket"),
                "target_alignment": target.get("route_c_delta_aligned_with_future"),
                "source_symbol": target.get("source_symbol"),
                "source_date": target.get("source_date"),
                "route_c_queue_id": target.get("route_c_queue_id"),
                "command_feature_bucket": target.get("command_feature_bucket"),
                "pair_stats": stats,
                "pair_relation_counts": dict(sorted(relation_counts.items())),
                "target_pair_stress_status": target_pair_stress_status(target, stats),
                "next_same_resource_action": next_action_for_target_stress(target, stats),
            }
        )
    return rows


def target_pair_stress_status(target: dict[str, Any], stats: dict[str, Any]) -> str:
    control_n = int(stats.get("unique_control_count") or 0)
    target_alignment = bool_value(target.get("route_c_delta_aligned_with_future"))
    control_share = stats.get("control_alignment_share")
    if control_n < 5:
        return "TARGET_PAIR_STRESS_UNDERPOWERED_CONTROLS_N_LT_5"
    if target.get("candidate_replay_bucket") == "CANDIDATE_HAS_NO_EVENT15_RECORDS":
        return "TARGET_PAIR_STRESS_EVENT15_EMPTY_SOURCE_STATE"
    if target_alignment is False and control_share is not None and control_share >= 0.60:
        return "TARGET_PAIR_STRESS_AVOID_DIRECTION_AGAINST_ALIGNED_CONTROLS"
    if target_alignment is True and control_share is not None and control_share >= 0.60:
        return "TARGET_PAIR_STRESS_TARGET_ALIGNED_WITH_ALIGNED_CONTROLS"
    return "TARGET_PAIR_STRESS_MIXED_OR_DESCRIPTIVE"


def next_action_for_target_stress(target: dict[str, Any], stats: dict[str, Any]) -> str:
    status = target_pair_stress_status(target, stats)
    if status == "TARGET_PAIR_STRESS_AVOID_DIRECTION_AGAINST_ALIGNED_CONTROLS":
        return "feed as branch-local avoid-boundary candidate and run leave-one concentration stress"
    if status == "TARGET_PAIR_STRESS_EVENT15_EMPTY_SOURCE_STATE":
        return "split as event-activity/source-quality proxy, not directional signal"
    if status.startswith("TARGET_PAIR_STRESS_UNDERPOWERED"):
        return "aggregate through source/queue/command parent axes or acquire more exact rows"
    return "preserve for mutation-boundary context and continue stress"


def build_relation_controls(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families: list[tuple[str, list[str]]] = [
        ("relation", ["relation"]),
        ("relation_candidate_replay_bucket", ["relation", "candidate_replay_bucket"]),
        ("relation_proxy_target_status", ["relation", "proxy_target_status"]),
        ("relation_target_source_symbol", ["relation", "target_source_symbol"]),
        ("relation_target_queue", ["relation", "target_queue_id"]),
        ("relation_target_command", ["relation", "target_command_feature_bucket"]),
    ]
    exploded: list[dict[str, Any]] = []
    for pair in pairs:
        for relation in pair.get("pair_relations", []):
            exploded.append({**pair, "relation": relation})
    rows: list[dict[str, Any]] = []
    for family, keys in families:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in exploded:
            grouped[tuple(row.get(key) for key in keys)].append(row)
        for values, group in sorted(grouped.items(), key=lambda item: tuple(str(v) for v in item[0])):
            group_values = {key: value for key, value in zip(keys, values, strict=True)}
            stats = alignment_stats_from_pairs(group)
            verdict = relation_control_verdict(stats)
            rows.append(
                {
                    "relation_control_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-REL-CONTROL-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "control_family": family,
                    "group_values": group_values,
                    "relation_stats": stats,
                    "relation_control_verdict": verdict,
                    "next_same_resource_action": next_action_for_relation_verdict(verdict),
                }
            )
    return rows


def relation_control_verdict(stats: dict[str, Any]) -> str:
    unique_targets = int(stats.get("unique_target_count") or 0)
    unique_controls = int(stats.get("unique_control_count") or 0)
    delta = stats.get("target_minus_control_alignment_share")
    if unique_targets < 5:
        return "RELATION_CONTROL_UNDERPOWERED_TARGETS_N_LT_5"
    if unique_controls < 20:
        return "RELATION_CONTROL_UNDERPOWERED_CONTROLS_N_LT_20"
    if delta is not None and delta <= -0.15:
        return "RELATION_CONTROL_AVOID_DIRECTIONAL_STRESS_CANDIDATE"
    if delta is not None and abs(delta) <= 0.05:
        return "RELATION_CONTROL_NEAR_CONTROL"
    return "RELATION_CONTROL_MIXED_OR_DESCRIPTIVE"


def next_action_for_relation_verdict(verdict: str) -> str:
    if verdict == "RELATION_CONTROL_AVOID_DIRECTIONAL_STRESS_CANDIDATE":
        return "run leave-one stress and convert only stable rows into branch-local boundary candidates"
    if verdict.startswith("RELATION_CONTROL_UNDERPOWERED"):
        return "aggregate through parent axes or acquire/proxy more rows before stronger interpretation"
    return "preserve relation context and continue branch-local boundary design"


def build_leave_one_stress(relation_controls: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_controls = [
        row for row in relation_controls
        if row.get("relation_control_verdict") == "RELATION_CONTROL_AVOID_DIRECTIONAL_STRESS_CANDIDATE"
        or int(row.get("relation_stats", {}).get("unique_target_count") or 0) >= 5
    ]
    rows: list[dict[str, Any]] = []
    for control in candidate_controls:
        group_values = control["group_values"]
        filtered = pairs_for_group_values(pairs, group_values)
        base_delta = control["relation_stats"].get("target_minus_control_alignment_share")
        axes = [
            ("source_requirement_id", "source_requirement_id"),
            ("target_source_symbol", "target_source_symbol"),
            ("target_source_date", "target_source_date"),
            ("target_queue_id", "target_queue_id"),
            ("target_command_feature_bucket", "target_command_feature_bucket"),
        ]
        for axis_name, field in axes:
            values = sorted({str(row.get(field)) for row in filtered if row.get(field) is not None})
            for value in values:
                remaining = [row for row in filtered if str(row.get(field)) != value]
                stats = alignment_stats_from_pairs(remaining)
                stress_status = leave_one_status(base_delta, stats)
                rows.append(
                    {
                        "leave_one_stress_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-LEAVEONE-{len(rows) + 1:06d}",
                        "route_id": ROUTE_ID,
                        "safe_flags": SAFE_FLAGS,
                        "evidence_boundary": EVIDENCE_BOUNDARY,
                        "source_relation_control_id": control["relation_control_id"],
                        "control_family": control["control_family"],
                        "group_values": group_values,
                        "leave_one_axis": axis_name,
                        "leave_one_value": value,
                        "base_target_minus_control_alignment_share": base_delta,
                        "post_leave_one_stats": stats,
                        "post_leave_one_delta": stats.get("target_minus_control_alignment_share"),
                        "leave_one_stress_status": stress_status,
                        "next_same_resource_action": next_action_for_leave_one(stress_status),
                    }
                )
    return rows


def pairs_for_group_values(pairs: list[dict[str, Any]], group_values: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for pair in pairs:
        relation_match = True
        for key, value in group_values.items():
            if key == "relation":
                if value not in pair.get("pair_relations", []):
                    relation_match = False
                    break
            elif pair.get(key) != value:
                relation_match = False
                break
        if relation_match:
            out.append(pair)
    return out


def leave_one_status(base_delta: float | None, stats: dict[str, Any]) -> str:
    if int(stats.get("unique_target_count") or 0) < 5:
        return "LEAVE_ONE_UNDERPOWERED_AFTER_REMOVAL"
    post_delta = stats.get("target_minus_control_alignment_share")
    if base_delta is None or post_delta is None:
        return "LEAVE_ONE_NO_DELTA_AVAILABLE"
    if base_delta <= -0.15 and post_delta <= -0.15:
        return "LEAVE_ONE_AVOID_DIRECTION_STABLE"
    if abs(post_delta - base_delta) <= 0.05:
        return "LEAVE_ONE_DELTA_STABLE"
    return "LEAVE_ONE_DELTA_SHIFTS"


def next_action_for_leave_one(status: str) -> str:
    if status == "LEAVE_ONE_AVOID_DIRECTION_STABLE":
        return "retain as branch-local challenger-boundary candidate pending dedup and broader controls"
    if status == "LEAVE_ONE_DELTA_SHIFTS":
        return "split by the removed axis before any boundary use"
    if status.startswith("LEAVE_ONE_UNDERPOWERED"):
        return "aggregate parent axis or acquire/proxy more exact rows"
    return "preserve stress context"


def build_boundary_integration(
    boundaries: list[dict[str, Any]],
    source_requirements: list[dict[str, Any]],
    targets: list[dict[str, Any]],
    target_summaries: list[dict[str, Any]],
    relation_controls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source_requirements_by_micro: dict[str, list[dict[str, Any]]] = defaultdict(list)
    targets_by_source_requirement: dict[str, list[dict[str, Any]]] = defaultdict(list)
    summaries_by_source_requirement: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source_requirement in source_requirements:
        for requirement_id in source_requirement.get("requirement_ids", []):
            source_requirements_by_micro[str(requirement_id)].append(source_requirement)
    for target in targets:
        targets_by_source_requirement[str(target.get("source_requirement_id"))].append(target)
    for summary in target_summaries:
        summaries_by_source_requirement[str(summary.get("source_requirement_id"))].append(summary)
    stable_relation_candidates = [
        row for row in relation_controls
        if row.get("relation_control_verdict") == "RELATION_CONTROL_AVOID_DIRECTIONAL_STRESS_CANDIDATE"
    ]
    rows: list[dict[str, Any]] = []
    for boundary in boundaries:
        requirement_id = str(boundary["requirement_id"])
        linked_source_requirements = source_requirements_by_micro.get(requirement_id, [])
        linked_source_requirement_ids = sorted(
            {str(row.get("source_requirement_id")) for row in linked_source_requirements}
        )
        req_targets = [
            target
            for source_requirement_id in linked_source_requirement_ids
            for target in targets_by_source_requirement.get(source_requirement_id, [])
        ]
        req_summaries = [
            summary
            for source_requirement_id in linked_source_requirement_ids
            for summary in summaries_by_source_requirement.get(source_requirement_id, [])
        ]
        target_status_counts = counter_dict(target.get("proxy_target_status") for target in req_targets)
        stress_status_counts = counter_dict(summary.get("target_pair_stress_status") for summary in req_summaries)
        integration_status = boundary_integration_status(req_targets, req_summaries, stable_relation_candidates)
        rows.append(
            {
                "boundary_integration_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-BOUNDARY-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "requirement_id": requirement_id,
                "source_group_id": boundary.get("source_group_id"),
                "boundary_family": boundary.get("boundary_family"),
                "original_branch_local_predicate": boundary.get("branch_local_predicate"),
                "linked_source_requirement_ids": linked_source_requirement_ids,
                "proxy_target_rows": len(req_targets),
                "target_status_counts": target_status_counts,
                "target_pair_stress_status_counts": stress_status_counts,
                "relation_avoid_candidate_count_global": len(stable_relation_candidates),
                "boundary_integration_status": integration_status,
                "branch_local_boundary_update": branch_local_boundary_update(integration_status),
                "required_before_any_live_or_promotion_use": [
                    "deduplicated source-safe validation denominator",
                    "stable leave-one stress by source/date/queue/command",
                    "same-axis exact-feature control support",
                    "separate promotion dossier",
                ],
                "next_same_resource_action": next_action_for_boundary_status(integration_status),
            }
        )
    return rows


def boundary_integration_status(
    targets: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    stable_relation_candidates: list[dict[str, Any]],
) -> str:
    if not targets:
        return "BOUNDARY_NO_TARGET_MEMBERSHIP_IN_PROXY_PACKET"
    if any(target.get("candidate_replay_bucket") == "CANDIDATE_HAS_NO_EVENT15_RECORDS" for target in targets):
        return "BOUNDARY_SOURCE_ACTIVITY_EMPTY_SPLIT_REQUIRED"
    if any(summary.get("target_pair_stress_status") == "TARGET_PAIR_STRESS_AVOID_DIRECTION_AGAINST_ALIGNED_CONTROLS" for summary in summaries):
        return "BOUNDARY_AVOID_STRESS_CANDIDATE_UNDER_DEDUP_REVIEW"
    if stable_relation_candidates:
        return "BOUNDARY_RELATION_LEVEL_AVOID_CANDIDATE_GLOBAL_NOT_REQUIREMENT_SPECIFIC"
    return "BOUNDARY_UNDERPOWERED_PROXY_CONTEXT_ONLY"


def branch_local_boundary_update(status: str) -> str:
    if status == "BOUNDARY_SOURCE_ACTIVITY_EMPTY_SPLIT_REQUIRED":
        return "add event15_empty_source_state predicate as source-quality proxy, not directional avoid rule"
    if status == "BOUNDARY_AVOID_STRESS_CANDIDATE_UNDER_DEDUP_REVIEW":
        return "retain original predicate only as branch-local avoid challenger pending stress"
    if status == "BOUNDARY_RELATION_LEVEL_AVOID_CANDIDATE_GLOBAL_NOT_REQUIREMENT_SPECIFIC":
        return "use global relation candidate to prioritize further stress, not as requirement-level rule"
    return "keep as underpowered source-quality context"


def next_action_for_boundary_status(status: str) -> str:
    if status == "BOUNDARY_SOURCE_ACTIVITY_EMPTY_SPLIT_REQUIRED":
        return "split event15-empty source activity from final-minute source silence in branch-local challenger design"
    if status == "BOUNDARY_AVOID_STRESS_CANDIDATE_UNDER_DEDUP_REVIEW":
        return "deduplicate and run concentration stress before any branch-local challenger implementation"
    if status == "BOUNDARY_RELATION_LEVEL_AVOID_CANDIDATE_GLOBAL_NOT_REQUIREMENT_SPECIFIC":
        return "build broader parent-axis relation stress packet"
    return "aggregate or acquire/proxy more rows before stronger interpretation"


def build_bucket_rows(
    target_summaries: list[dict[str, Any]],
    relation_controls: list[dict[str, Any]],
    leave_one_rows: list[dict[str, Any]],
    boundary_rows: list[dict[str, Any]],
    counts: dict[str, int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    bucket_sources = [
        ("target_pair_stress_status", target_summaries, "target_pair_stress_status"),
        ("relation_control_verdict", relation_controls, "relation_control_verdict"),
        ("leave_one_stress_status", leave_one_rows, "leave_one_stress_status"),
        ("boundary_integration_status", boundary_rows, "boundary_integration_status"),
    ]
    for family, source_rows, key in bucket_sources:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in source_rows:
            grouped[str(row.get(key))].append(row)
        for value, group in sorted(grouped.items()):
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-STRESS-BUCKET-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": family,
                    "bucket_value": value,
                    "row_count": len(group),
                    "next_same_resource_action": next_action_for_bucket(family, value),
                    "counts_context": counts,
                }
            )
    return rows


def next_action_for_bucket(family: str, value: str) -> str:
    if family == "boundary_integration_status":
        return next_action_for_boundary_status(value)
    if family == "leave_one_stress_status":
        return next_action_for_leave_one(value)
    if family == "relation_control_verdict":
        return next_action_for_relation_verdict(value)
    if value == "TARGET_PAIR_STRESS_AVOID_DIRECTION_AGAINST_ALIGNED_CONTROLS":
        return "run leave-one/concentration stress and convert only stable boundaries"
    if value == "TARGET_PAIR_STRESS_EVENT15_EMPTY_SOURCE_STATE":
        return "split as source-activity proxy state"
    return "preserve stress context and continue parent-axis aggregation"


def build_questions(bucket_rows: list[dict[str, Any]], boundary_rows: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket in bucket_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-STRESS-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": bucket["bucket_family"],
                "question_key": bucket["bucket_value"],
                "row_count": bucket["row_count"],
                "question": "What stress, split, or branch-local boundary action follows for this bucket?",
                "next_same_resource_action": bucket["next_same_resource_action"],
                "counts_context": counts,
            }
        )
    for boundary in boundary_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-STRESS-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "boundary_integration",
                "question_key": boundary["requirement_id"],
                "row_count": boundary["proxy_target_rows"],
                "question": "How should this requirement boundary be represented in a branch-local challenger without promotion claims?",
                "next_same_resource_action": boundary["next_same_resource_action"],
                "counts_context": counts,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_microcluster_proxy_stress_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_microcluster_proxy_stress_result", "created"),
        (TARGET_SUMMARY_LEDGER, "sierra_depth_ladder_source_silence_microcluster_proxy_target_summary_ledger", "created"),
        (RELATION_CONTROL_LEDGER, "sierra_depth_ladder_source_silence_microcluster_proxy_relation_control_ledger", "created"),
        (LEAVE_ONE_STRESS_LEDGER, "sierra_depth_ladder_source_silence_microcluster_proxy_leave_one_stress_ledger", "created"),
        (BOUNDARY_INTEGRATION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_proxy_boundary_integration_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_proxy_stress_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_proxy_stress_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_microcluster_proxy_stress_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], bucket_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_microcluster_proxy_stress",
        "status": "done",
        "route": "source_silence_microcluster_proxy_pair_stress_and_boundary_integration",
        "details": "Deduplicated/stressed proxy pair relations and integrated microcluster mutation boundaries as branch-local source-quality predicates.",
        "counts": counts,
        "boundary_bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(TARGET_SUMMARY_LEDGER),
            relative(RELATION_CONTROL_LEDGER),
            relative(LEAVE_ONE_STRESS_LEDGER),
            relative(BOUNDARY_INTEGRATION_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], bucket_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Source-Silence Microcluster Proxy Stress",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: proxy pair stress and branch-local boundary integration only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Boundary Buckets", ""])
    for key, value in sorted(bucket_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Convert event15-empty source activity into a separate source-quality proxy state.",
            "- Stress any avoid-looking target rows by source/date/queue/command before branch-local challenger implementation.",
            "- Build parent-axis relation controls for underpowered requirement-level boundaries.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    targets = read_jsonl(PROXY_TARGET_LEDGER)
    pairs = read_jsonl(PROXY_PAIR_LEDGER)
    proxy_controls = read_jsonl(PROXY_CONTROL_LEDGER)
    boundaries = read_jsonl(MUTATION_BOUNDARY_LEDGER)
    source_requirements = read_jsonl(SOURCE_REQUIREMENT_LEDGER)
    target_summaries = build_target_summaries(targets, pairs)
    relation_controls = build_relation_controls(pairs)
    leave_one_rows = build_leave_one_stress(relation_controls, pairs)
    boundary_rows = build_boundary_integration(boundaries, source_requirements, targets, target_summaries, relation_controls)
    boundary_bucket_counts = counter_dict(row.get("boundary_integration_status") for row in boundary_rows)
    counts = {
        "proxy_target_input_rows": len(targets),
        "proxy_pair_input_rows": len(pairs),
        "proxy_control_input_rows": len(proxy_controls),
        "mutation_boundary_input_rows": len(boundaries),
        "source_requirement_input_rows": len(source_requirements),
        "target_summary_rows": len(target_summaries),
        "relation_control_rows": len(relation_controls),
        "leave_one_stress_rows": len(leave_one_rows),
        "boundary_integration_rows": len(boundary_rows),
        "bucket_rows": 0,
        "question_rows": 0,
    }
    bucket_rows = build_bucket_rows(target_summaries, relation_controls, leave_one_rows, boundary_rows, counts)
    counts["bucket_rows"] = len(bucket_rows)
    question_rows = build_questions(bucket_rows, boundary_rows, counts)
    counts["question_rows"] = len(question_rows)
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_proxy_stress_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_PROXY_STRESS_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "boundary_integration_status_counts": boundary_bucket_counts,
        "target_pair_stress_status_counts": counter_dict(row.get("target_pair_stress_status") for row in target_summaries),
        "relation_control_verdict_counts": counter_dict(row.get("relation_control_verdict") for row in relation_controls),
        "leave_one_stress_status_counts": counter_dict(row.get("leave_one_stress_status") for row in leave_one_rows),
        "not_completion": "This proxy-stress packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "split event15-empty source activity from final-minute source silence in branch-local challenger design",
            "build parent-axis relation controls for underpowered requirement-level boundaries",
            "only retain avoid-looking boundaries after stable leave-one stress",
        ],
    }
    write_jsonl(TARGET_SUMMARY_LEDGER, target_summaries)
    write_jsonl(RELATION_CONTROL_LEDGER, relation_controls)
    write_jsonl(LEAVE_ONE_STRESS_LEDGER, leave_one_rows)
    write_jsonl(BOUNDARY_INTEGRATION_LEDGER, boundary_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, boundary_bucket_counts)
    write_summary(generated_utc, counts, boundary_bucket_counts)
    print(json.dumps({"ok": True, "counts": counts, "boundary_counts": boundary_bucket_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
