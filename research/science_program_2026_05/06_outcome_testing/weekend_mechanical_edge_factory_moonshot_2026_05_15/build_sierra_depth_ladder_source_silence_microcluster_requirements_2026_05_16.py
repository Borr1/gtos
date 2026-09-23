#!/usr/bin/env python3
"""Turn possible-avoid micro-clusters into requirements and mutation boundaries."""

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

DEEP_SPLIT_GROUP_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEEP_SPLIT_GROUP_LEDGER_{STAMP}.jsonl"
DEDUP_TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEDUP_TARGET_LEDGER_{STAMP}.jsonl"
SOURCE_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_ROUTE_C_JOIN_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_REQUIREMENT_RESULT_{STAMP}.json"
REQUIREMENT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_REQUIREMENT_LEDGER_{STAMP}.jsonl"
TARGET_MEMBERSHIP_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_TARGET_MEMBERSHIP_LEDGER_{STAMP}.jsonl"
SOURCE_REQUIREMENT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_REQUIREMENT_LEDGER_{STAMP}.jsonl"
MUTATION_BOUNDARY_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_MUTATION_BOUNDARY_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_REQUIREMENT_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Source-silence possible-avoid micro-cluster acquisition/proxy requirements and branch-local "
    "mutation boundaries only; no strategy validation, trade outcome, R/PnL, expectancy, "
    "live-readiness, or live deployment"
)

MICROCLUSTER_BUCKET = "DEEP_SPLIT_AVOID_DIRECTIONAL_BUT_UNDERPOWERED"


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


def counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def microcluster_requirement_type(group: dict[str, Any]) -> str:
    n = int(group["candidate_rows"]["n"])
    family = str(group.get("split_family"))
    if family in {"by_queue", "by_command_bucket", "by_source_date", "by_source_symbol"} and n >= 10:
        return "PARENT_AXIS_MICROCLUSTER_NEEDS_MORE_EXACT_ROWS"
    if n >= 10:
        return "PAIRWISE_MICROCLUSTER_NEEDS_PARENT_AGGREGATION"
    return "MICROCLUSTER_N_5_TO_9_NEEDS_ACQUISITION_OR_PARENT_AGGREGATION"


def build_requirements(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in groups:
        n = int(group["candidate_rows"]["n"])
        control_n = int(group["control_rows"]["n"])
        requirement_type = microcluster_requirement_type(group)
        rows.append(
            {
                "requirement_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-REQ-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_group_id": group["group_id"],
                "split_family": group["split_family"],
                "group_values": group["group_values"],
                "candidate_n": n,
                "candidate_alignment_share": group["candidate_rows"].get("route_alignment_share"),
                "control_scope": group["control_scope"],
                "control_n": control_n,
                "control_alignment_share": group["control_rows"].get("route_alignment_share"),
                "route_alignment_delta_vs_control": group.get("route_alignment_delta_vs_control"),
                "mean_future_change_delta_vs_control": group.get("mean_future_change_delta_vs_control"),
                "request_ids": group["request_ids"],
                "requirement_type": requirement_type,
                "additional_unique_rows_needed_for_n20": max(0, 20 - n),
                "exact_source_requirement": "recover more exact same-axis source-silence or source-safe rows from owned/current/free depth history",
                "proxy_requirement": "if exact rows are unavailable, build same-axis proxy controls from exact-feature rows and source-silence neighbors",
                "mutation_boundary_requirement": "branch-local source-quality or avoid-microcluster boundary only; no live behavior change",
                "next_same_resource_action": next_action_for_requirement(requirement_type),
            }
        )
    return rows


def next_action_for_requirement(requirement_type: str) -> str:
    if requirement_type == "PARENT_AXIS_MICROCLUSTER_NEEDS_MORE_EXACT_ROWS":
        return "search/acquire same-axis exact rows first, then rerun parent-axis matched controls"
    if requirement_type == "PAIRWISE_MICROCLUSTER_NEEDS_PARENT_AGGREGATION":
        return "aggregate through parent axis and retain pairwise boundary as source-quality modifier"
    return "preserve as micro-cluster; acquire/proxy more rows before stronger interpretation"


def build_memberships(requirements: list[dict[str, Any]], targets_by_request: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for requirement in requirements:
        for request_id in requirement["request_ids"]:
            target = targets_by_request.get(str(request_id), {})
            rows.append(
                {
                    "membership_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-MEMBER-{len(rows) + 1:06d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "requirement_id": requirement["requirement_id"],
                    "source_group_id": requirement["source_group_id"],
                    "split_family": requirement["split_family"],
                    "group_values": requirement["group_values"],
                    "request_id": request_id,
                    "source_symbol": target.get("source_symbol"),
                    "source_date": target.get("source_date"),
                    "queue_id": target.get("queue_id"),
                    "command_feature_bucket": target.get("command_feature_bucket"),
                    "route_c_delta_aligned_with_future": target.get("route_c_delta_aligned_with_future"),
                    "route_c_future_change_per_current_range": target.get("route_c_future_change_per_current_range"),
                    "depth_path": target.get("depth_path"),
                    "depth_file_exists": target.get("depth_file_exists"),
                    "design_statuses": target.get("design_statuses"),
                    "mutation_types": target.get("mutation_types"),
                }
            )
    return rows


def build_source_requirements(memberships: list[dict[str, Any]], source_join_by_request: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in memberships:
        grouped[(row.get("source_symbol"), row.get("source_date"), row.get("depth_path"))].append(row)
    outputs: list[dict[str, Any]] = []
    for (symbol, source_date, depth_path), rows in sorted(grouped.items(), key=lambda item: tuple(str(v) for v in item[0])):
        request_ids = sorted({str(row["request_id"]) for row in rows})
        source_rows = [source_join_by_request.get(request_id, {}) for request_id in request_ids]
        outputs.append(
            {
                "source_requirement_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-REQ-{len(outputs) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_symbol": symbol,
                "source_date": source_date,
                "depth_path": depth_path,
                "depth_file_exists": any(bool(row.get("depth_file_exists")) for row in source_rows),
                "unique_request_count": len(request_ids),
                "request_ids": request_ids,
                "split_families": sorted({str(row["split_family"]) for row in rows}),
                "requirement_ids": sorted({str(row["requirement_id"]) for row in rows}),
                "exact_acquisition_action": "search alternate local roots and source-safe exports for same source symbol/date with deeper earlier-book history",
                "proxy_action": "build same source-symbol/date exact-feature and neighbor controls if exact repair remains unavailable",
                "not_waiting": "This source requirement is an immediate acquisition/proxy route, not a forward-data wait condition.",
            }
        )
    return outputs


def build_mutation_boundaries(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for requirement in requirements:
        predicate_parts = [
            "source_silence_status in {BLOCKED_TRUE_EVENT_BOUNDARY_NO_RECORDS_AFTER_CLEAR, BLOCKED_NO_CLEAR_AND_NO_EVENT_BOUNDARY_RECORDS}",
        ]
        for key, value in requirement["group_values"].items():
            predicate_parts.append(f"{key} == {json.dumps(value)}")
        rows.append(
            {
                "mutation_boundary_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-BOUNDARY-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "requirement_id": requirement["requirement_id"],
                "source_group_id": requirement["source_group_id"],
                "boundary_family": requirement["requirement_type"],
                "branch_local_predicate": " AND ".join(predicate_parts),
                "branch_local_action": "source_quality_microcluster_flag_for_research_challenger_only",
                "required_before_any_promotion": [
                    "deduplicated source-safe validation denominator",
                    "same-axis exact-feature controls",
                    "concentration stress by date/symbol/queue/command",
                    "separate promotion dossier",
                ],
                "next_same_resource_action": requirement["next_same_resource_action"],
            }
        )
    return rows


def build_bucket_rows(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in requirements:
        grouped[(row["split_family"], row["requirement_type"])].append(row)
    for (family, requirement_type), group in sorted(grouped.items()):
        rows.append(
            {
                "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-BUCKET-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "split_family": family,
                "requirement_type": requirement_type,
                "requirement_rows": len(group),
                "underlying_membership_rows": sum(len(row["request_ids"]) for row in group),
                "additional_unique_rows_needed_for_n20": sum(int(row["additional_unique_rows_needed_for_n20"]) for row in group),
                "next_same_resource_action": next_action_for_requirement(requirement_type),
            }
        )
    return rows


def build_questions(bucket_rows: list[dict[str, Any]], source_requirements: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket in bucket_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": bucket["split_family"],
                "question_key": bucket["requirement_type"],
                "row_count": bucket["requirement_rows"],
                "underlying_rows": bucket["underlying_membership_rows"],
                "question": "Which acquisition/proxy/mutation-boundary action follows for this micro-cluster requirement bucket?",
                "next_same_resource_action": bucket["next_same_resource_action"],
                "counts_context": counts,
            }
        )
    for source_req in source_requirements:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "source_requirement",
                "question_key": {
                    "source_symbol": source_req["source_symbol"],
                    "source_date": source_req["source_date"],
                },
                "row_count": source_req["unique_request_count"],
                "question": "Can this source-date micro-cluster be repaired by exact acquisition or a stronger source-safe proxy?",
                "next_same_resource_action": source_req["exact_acquisition_action"],
                "counts_context": counts,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_microcluster_requirements_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_microcluster_requirement_result", "created"),
        (REQUIREMENT_LEDGER, "sierra_depth_ladder_source_silence_microcluster_requirement_ledger", "created"),
        (TARGET_MEMBERSHIP_LEDGER, "sierra_depth_ladder_source_silence_microcluster_target_membership_ledger", "created"),
        (SOURCE_REQUIREMENT_LEDGER, "sierra_depth_ladder_source_silence_microcluster_source_requirement_ledger", "created"),
        (MUTATION_BOUNDARY_LEDGER, "sierra_depth_ladder_source_silence_microcluster_mutation_boundary_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_microcluster_requirement_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], requirement_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_microcluster_requirements",
        "status": "done",
        "route": "source_silence_possible_avoid_microcluster_requirements",
        "details": "Converted directional-but-underpowered possible-avoid micro-clusters into acquisition/proxy requirements and branch-local mutation boundaries.",
        "counts": counts,
        "requirement_type_counts": requirement_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(REQUIREMENT_LEDGER),
            relative(TARGET_MEMBERSHIP_LEDGER),
            relative(SOURCE_REQUIREMENT_LEDGER),
            relative(MUTATION_BOUNDARY_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], requirement_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Depth Ladder Source Silence Micro-Cluster Requirements",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: acquisition/proxy requirements and branch-local mutation boundaries only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Requirement Types", ""])
    for key, value in sorted(requirement_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Search exact source-date/depth roots for micro-cluster source requirements.",
            "- Build source-safe proxy controls for unrecovered micro-clusters.",
            "- Use mutation boundaries only in branch-local challenger design, not live behavior.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    groups = read_jsonl(DEEP_SPLIT_GROUP_LEDGER)
    targets = read_jsonl(DEDUP_TARGET_LEDGER)
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    targets_by_request = {str(row["request_id"]): row for row in targets}
    source_join_by_request = {str(row["request_id"]): row for row in source_join}
    micro_groups = [row for row in groups if row.get("deep_split_bucket") == MICROCLUSTER_BUCKET]

    requirements = build_requirements(micro_groups)
    memberships = build_memberships(requirements, targets_by_request)
    source_requirements = build_source_requirements(memberships, source_join_by_request)
    mutation_boundaries = build_mutation_boundaries(requirements)
    bucket_rows = build_bucket_rows(requirements)
    counts = {
        "deep_split_group_input_rows": len(groups),
        "microcluster_group_rows": len(micro_groups),
        "dedup_target_input_rows": len(targets),
        "requirement_rows": len(requirements),
        "target_membership_rows": len(memberships),
        "source_requirement_rows": len(source_requirements),
        "mutation_boundary_rows": len(mutation_boundaries),
        "bucket_rows": len(bucket_rows),
        "question_rows": 0,
    }
    question_rows = build_questions(bucket_rows, source_requirements, counts)
    counts["question_rows"] = len(question_rows)
    requirement_counts = counter_dict(row["requirement_type"] for row in requirements)

    write_jsonl(REQUIREMENT_LEDGER, requirements)
    write_jsonl(TARGET_MEMBERSHIP_LEDGER, memberships)
    write_jsonl(SOURCE_REQUIREMENT_LEDGER, source_requirements)
    write_jsonl(MUTATION_BOUNDARY_LEDGER, mutation_boundaries)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_requirement_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_REQUIREMENT_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "requirement_type_counts": requirement_counts,
        "not_completion": "This micro-cluster requirement packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "search exact source-date/depth roots for micro-cluster source requirements",
            "build source-safe proxy controls for unrecovered micro-clusters",
            "feed mutation boundaries into branch-local challenger design only",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, requirement_counts)
    write_summary(generated_utc, counts, requirement_counts)
    print(json.dumps({"ok": True, "counts": counts, "requirement_type_counts": requirement_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
