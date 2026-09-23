#!/usr/bin/env python3
"""Convert proxy-stressed microclusters into branch-local challenger specs."""

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
PROXY_TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_TARGET_LEDGER_{STAMP}.jsonl"
REQUIREMENT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_REQUIREMENT_LEDGER_{STAMP}.jsonl"
BOUNDARY_INTEGRATION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_BOUNDARY_INTEGRATION_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BOUNDARY_CHALLENGER_RESULT_{STAMP}.json"
EVENT15_STATE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EVENT15_EMPTY_STATE_LEDGER_{STAMP}.jsonl"
PARENT_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BOUNDARY_PARENT_CONTROL_LEDGER_{STAMP}.jsonl"
CHALLENGER_SPEC_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BOUNDARY_CHALLENGER_SPEC_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BOUNDARY_CHALLENGER_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BOUNDARY_CHALLENGER_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BOUNDARY_CHALLENGER_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Branch-local source-silence micro-cluster challenger specification only; "
    "source-control/design evidence with no strategy validation, trade outcome, "
    "R/PnL, expectancy, live-readiness, or live deployment"
)

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


def bool_value(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(out) or math.isinf(out) else out


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


def row_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    alignment_values = [value for row in rows if (value := bool_value(row.get("route_c_delta_aligned_with_future"))) is not None]
    future_values = [
        value for row in rows
        if (value := safe_float(row.get("route_c_future_change_per_current_range"))) is not None
    ]
    return {
        "n": len(rows),
        "unique_request_count": len({str(row.get("request_id")) for row in rows if row.get("request_id")}),
        "route_alignment_n": len(alignment_values),
        "route_alignment_share": share(alignment_values),
        "mean_route_c_future_change_per_current_range": mean(future_values),
        "candidate_replay_bucket_counts": counter_dict(row.get("candidate_replay_bucket") for row in rows),
        "proxy_target_status_counts": counter_dict(row.get("proxy_target_status") for row in rows),
        "source_symbol_counts": counter_dict(row.get("source_symbol") for row in rows),
        "source_date_counts": counter_dict(row.get("source_date") for row in rows),
        "route_queue_counts": counter_dict(row.get("route_c_queue_id") for row in rows),
        "command_feature_bucket_counts": counter_dict(row.get("command_feature_bucket") for row in rows),
    }


def target_rows_for_requirement(requirement: dict[str, Any], targets_by_request: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for request_id in requirement.get("request_ids", []):
        row = targets_by_request.get(str(request_id))
        if row:
            rows.append(row)
    return rows


def exact_control_pool(group_values: dict[str, Any], exact_rows: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    queue_id = group_values.get("queue_id") or group_values.get("route_c_queue_id")
    command = group_values.get("command_feature_bucket")
    source_symbol = group_values.get("source_symbol")
    source_date = group_values.get("source_date")
    matchers = [
        (
            "parent_exact_source_date_queue_command",
            lambda row: source_date
            and queue_id
            and command
            and row.get("source_date") == source_date
            and row.get("route_c_queue_id") == queue_id
            and row.get("command_feature_bucket") == command,
        ),
        (
            "parent_exact_source_symbol_queue_command",
            lambda row: source_symbol
            and queue_id
            and command
            and row.get("source_symbol") == source_symbol
            and row.get("route_c_queue_id") == queue_id
            and row.get("command_feature_bucket") == command,
        ),
        (
            "parent_exact_queue_command",
            lambda row: queue_id
            and command
            and row.get("route_c_queue_id") == queue_id
            and row.get("command_feature_bucket") == command,
        ),
        ("parent_exact_queue", lambda row: queue_id and row.get("route_c_queue_id") == queue_id),
        ("parent_exact_command", lambda row: command and row.get("command_feature_bucket") == command),
        ("parent_exact_source_symbol", lambda row: source_symbol and row.get("source_symbol") == source_symbol),
        ("parent_exact_source_date", lambda row: source_date and row.get("source_date") == source_date),
    ]
    for scope, predicate in matchers:
        pool = [row for row in exact_rows if predicate(row)]
        if pool:
            return scope, pool
    return "all_exact_feature_rows", exact_rows


def build_event15_state_rows(targets: list[dict[str, Any]], boundary_by_requirement: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        if target.get("candidate_replay_bucket") != "CANDIDATE_HAS_NO_EVENT15_RECORDS":
            continue
        linked_boundaries = [
            boundary_id
            for boundary_id, boundary in boundary_by_requirement.items()
            if target.get("request_id") in set(boundary.get("request_ids", []))
        ]
        rows.append(
            {
                "event15_state_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EVENT15-EMPTY-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "request_id": target.get("request_id"),
                "source_requirement_id": target.get("source_requirement_id"),
                "linked_requirement_ids": linked_boundaries,
                "source_symbol": target.get("source_symbol"),
                "source_date": target.get("source_date"),
                "route_c_queue_id": target.get("route_c_queue_id"),
                "command_feature_bucket": target.get("command_feature_bucket"),
                "event15_record_count": target.get("event15_record_count"),
                "event_boundary_record_count": target.get("event_boundary_record_count"),
                "source_quality_state": "EVENT15_EMPTY_SOURCE_ACTIVITY_PROXY_STATE",
                "branch_local_predicate": "candidate_replay_bucket == 'CANDIDATE_HAS_NO_EVENT15_RECORDS'",
                "next_same_resource_action": "keep separate from final-minute source silence and test as source-activity proxy state",
            }
        )
    return rows


def parent_control_verdict(target_stats: dict[str, Any], control_stats: dict[str, Any], has_event15_empty: bool) -> str:
    target_n = int(target_stats["n"])
    control_n = int(control_stats["n"])
    delta = numeric_delta(target_stats.get("route_alignment_share"), control_stats.get("route_alignment_share"))
    if has_event15_empty:
        return "BOUNDARY_PARENT_EVENT15_EMPTY_SPLIT_REQUIRED"
    if control_n < 20:
        return "BOUNDARY_PARENT_CONTROL_UNDERPOWERED_N_LT_20"
    if target_n < 5:
        return "BOUNDARY_PARENT_TARGET_UNDERPOWERED_N_LT_5"
    if target_n < 20:
        if delta is not None and delta <= -0.15:
            return "BOUNDARY_PARENT_AVOID_CANDIDATE_UNDERPOWERED"
        return "BOUNDARY_PARENT_UNDERPOWERED_CONTEXT_ONLY"
    if delta is not None and delta <= -0.15:
        return "BOUNDARY_PARENT_AVOID_CANDIDATE"
    return "BOUNDARY_PARENT_MIXED_OR_NEAR_CONTROL"


def build_parent_controls(
    requirements: list[dict[str, Any]],
    targets_by_request: dict[str, dict[str, Any]],
    exact_rows: list[dict[str, Any]],
    boundary_integrations_by_requirement: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for requirement in requirements:
        all_targets = target_rows_for_requirement(requirement, targets_by_request)
        subgroups = [
            ("all_proxy_targets", all_targets),
            (
                "final_minute_source_silence_only",
                [row for row in all_targets if row.get("candidate_replay_bucket") == "CANDIDATE_HAS_EVENT15_BUT_FINAL_MINUTE_SOURCE_SILENCE"],
            ),
            (
                "event15_empty_only",
                [row for row in all_targets if row.get("candidate_replay_bucket") == "CANDIDATE_HAS_NO_EVENT15_RECORDS"],
            ),
        ]
        for subgroup, target_rows in subgroups:
            if not target_rows:
                continue
            control_scope, controls = exact_control_pool(requirement.get("group_values", {}), exact_rows)
            target_stats = row_stats(target_rows)
            control_stats = row_stats(controls)
            verdict = parent_control_verdict(
                target_stats,
                control_stats,
                any(row.get("candidate_replay_bucket") == "CANDIDATE_HAS_NO_EVENT15_RECORDS" for row in target_rows),
            )
            integration = boundary_integrations_by_requirement.get(str(requirement["requirement_id"]), {})
            rows.append(
                {
                    "parent_control_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PARENT-CONTROL-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "requirement_id": requirement["requirement_id"],
                    "source_group_id": requirement.get("source_group_id"),
                    "split_family": requirement.get("split_family"),
                    "requirement_type": requirement.get("requirement_type"),
                    "group_values": requirement.get("group_values"),
                    "subgroup": subgroup,
                    "boundary_integration_status": integration.get("boundary_integration_status"),
                    "target_rows": target_stats,
                    "control_scope": control_scope,
                    "control_rows": control_stats,
                    "route_alignment_delta_vs_control": numeric_delta(
                        target_stats.get("route_alignment_share"),
                        control_stats.get("route_alignment_share"),
                    ),
                    "mean_future_change_delta_vs_control": numeric_delta(
                        target_stats.get("mean_route_c_future_change_per_current_range"),
                        control_stats.get("mean_route_c_future_change_per_current_range"),
                    ),
                    "parent_control_verdict": verdict,
                    "next_same_resource_action": next_action_for_parent_verdict(verdict),
                }
            )
    return rows


def next_action_for_parent_verdict(verdict: str) -> str:
    if verdict == "BOUNDARY_PARENT_AVOID_CANDIDATE":
        return "materialize branch-local challenger predicate and run sealed/proxy validation packet"
    if verdict == "BOUNDARY_PARENT_AVOID_CANDIDATE_UNDERPOWERED":
        return "retain as branch-local candidate only after parent-axis aggregation and concentration stress"
    if verdict == "BOUNDARY_PARENT_EVENT15_EMPTY_SPLIT_REQUIRED":
        return "route to event15-empty source-activity proxy state, not directional avoid logic"
    if verdict.startswith("BOUNDARY_PARENT_CONTROL_UNDERPOWERED") or verdict.startswith("BOUNDARY_PARENT_TARGET_UNDERPOWERED"):
        return "aggregate/acquire/proxy more same-axis rows before stronger interpretation"
    return "preserve as context and continue challenger comparison"


def build_challenger_specs(parent_controls: list[dict[str, Any]], event15_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for control in parent_controls:
        verdict = control["parent_control_verdict"]
        if verdict not in {
            "BOUNDARY_PARENT_AVOID_CANDIDATE",
            "BOUNDARY_PARENT_AVOID_CANDIDATE_UNDERPOWERED",
            "BOUNDARY_PARENT_EVENT15_EMPTY_SPLIT_REQUIRED",
        }:
            continue
        group_values = control.get("group_values") or {}
        predicate_parts = [
            "source_silence_status in {'BLOCKED_TRUE_EVENT_BOUNDARY_NO_RECORDS_AFTER_CLEAR', 'BLOCKED_NO_CLEAR_AND_NO_EVENT_BOUNDARY_RECORDS'}",
        ]
        for key, value in group_values.items():
            if key == "queue_id":
                predicate_parts.append(f"route_c_queue_id == {json.dumps(value)}")
            else:
                predicate_parts.append(f"{key} == {json.dumps(value)}")
        if verdict == "BOUNDARY_PARENT_EVENT15_EMPTY_SPLIT_REQUIRED":
            predicate_parts.append("candidate_replay_bucket == 'CANDIDATE_HAS_NO_EVENT15_RECORDS'")
            action = "source_quality_event15_empty_proxy_state"
        else:
            action = "source_quality_avoid_challenger_candidate"
        rows.append(
            {
                "challenger_spec_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-CHALLENGER-SPEC-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "requirement_id": control["requirement_id"],
                "subgroup": control["subgroup"],
                "parent_control_verdict": verdict,
                "branch_local_predicate": " AND ".join(predicate_parts),
                "branch_local_action": action,
                "target_rows": control["target_rows"],
                "control_scope": control["control_scope"],
                "control_rows": control["control_rows"],
                "required_before_any_live_or_promotion_use": [
                    "sealed source-safe validation denominator",
                    "deduplicated target/control identity",
                    "concentration stress by source/date/queue/command",
                    "separate promotion dossier",
                ],
                "next_same_resource_action": next_action_for_parent_verdict(verdict),
            }
        )
    if event15_rows and not any(row.get("branch_local_action") == "source_quality_event15_empty_proxy_state" for row in rows):
        rows.append(
            {
                "challenger_spec_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-CHALLENGER-SPEC-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "requirement_id": "EVENT15_EMPTY_SOURCE_ACTIVITY_GLOBAL",
                "subgroup": "event15_empty_only",
                "parent_control_verdict": "BOUNDARY_PARENT_EVENT15_EMPTY_SPLIT_REQUIRED",
                "branch_local_predicate": "candidate_replay_bucket == 'CANDIDATE_HAS_NO_EVENT15_RECORDS'",
                "branch_local_action": "source_quality_event15_empty_proxy_state",
                "target_rows": {"n": len(event15_rows), "unique_request_count": len({row['request_id'] for row in event15_rows})},
                "required_before_any_live_or_promotion_use": [
                    "separate source-activity validation denominator",
                    "source parser/source-coverage audit",
                    "separate promotion dossier",
                ],
                "next_same_resource_action": "test event15-empty source state across all exact-feature controls and broader source roots",
            }
        )
    return rows


def build_bucket_rows(parent_controls: list[dict[str, Any]], challenger_specs: list[dict[str, Any]], event15_rows: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sources = [
        ("parent_control_verdict", parent_controls, "parent_control_verdict"),
        ("challenger_action", challenger_specs, "branch_local_action"),
        ("event15_source_symbol", event15_rows, "source_symbol"),
    ]
    for family, source_rows, key in sources:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in source_rows:
            grouped[str(row.get(key))].append(row)
        for value, group in sorted(grouped.items()):
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-CHALLENGER-BUCKET-{len(rows) + 1:05d}",
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
    if family == "parent_control_verdict":
        return next_action_for_parent_verdict(value)
    if value == "source_quality_event15_empty_proxy_state":
        return "test event15-empty source activity as separate source-quality state"
    if value == "source_quality_avoid_challenger_candidate":
        return "deduplicate/stress before any implementation proposal"
    return "preserve bucket and continue same-resource controls"


def build_questions(bucket_rows: list[dict[str, Any]], challenger_specs: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket in bucket_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-CHALLENGER-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": bucket["bucket_family"],
                "question_key": bucket["bucket_value"],
                "row_count": bucket["row_count"],
                "question": "What same-resource stress, split, or branch-local implementation route follows for this challenger bucket?",
                "next_same_resource_action": bucket["next_same_resource_action"],
                "counts_context": counts,
            }
        )
    for spec in challenger_specs:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-CHALLENGER-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "challenger_spec",
                "question_key": spec["challenger_spec_id"],
                "row_count": spec.get("target_rows", {}).get("n"),
                "question": "Can this branch-local source-quality predicate survive broader parent-axis controls and sealed/proxy testing?",
                "next_same_resource_action": spec["next_same_resource_action"],
                "counts_context": counts,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_microcluster_boundary_challengers_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_microcluster_boundary_challenger_result", "created"),
        (EVENT15_STATE_LEDGER, "sierra_depth_ladder_source_silence_microcluster_event15_empty_state_ledger", "created"),
        (PARENT_CONTROL_LEDGER, "sierra_depth_ladder_source_silence_microcluster_boundary_parent_control_ledger", "created"),
        (CHALLENGER_SPEC_LEDGER, "sierra_depth_ladder_source_silence_microcluster_boundary_challenger_spec_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_boundary_challenger_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_boundary_challenger_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_microcluster_boundary_challenger_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], verdict_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_microcluster_boundary_challengers",
        "status": "done",
        "route": "source_silence_microcluster_branch_local_challenger_specs",
        "details": "Converted proxy-stressed boundaries into event15-empty source-quality state specs and parent-axis avoid challenger candidates.",
        "counts": counts,
        "parent_control_verdict_counts": verdict_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(EVENT15_STATE_LEDGER),
            relative(PARENT_CONTROL_LEDGER),
            relative(CHALLENGER_SPEC_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], verdict_counts: dict[str, int], action_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Source-Silence Microcluster Boundary Challengers",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: branch-local challenger specifications only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Parent Control Verdicts", ""])
    for key, value in sorted(verdict_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Challenger Actions", ""])
    for key, value in sorted(action_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Test event15-empty source state against broader source activity controls.",
            "- Run sealed/proxy validation packets only for challenger specs that survive dedup and parent-axis stress.",
            "- Keep every spec branch-local until separate promotion evidence exists.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    targets = read_jsonl(PROXY_TARGET_LEDGER)
    requirements = read_jsonl(REQUIREMENT_LEDGER)
    boundary_integrations = read_jsonl(BOUNDARY_INTEGRATION_LEDGER)
    targets_by_request = {str(row["request_id"]): row for row in targets}
    requirements_by_id = {str(row["requirement_id"]): row for row in requirements}
    boundary_by_requirement = {str(row["requirement_id"]): row for row in boundary_integrations}
    exact_rows = [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES and not row.get("source_silence_joined")
    ]
    event15_rows = build_event15_state_rows(targets, requirements_by_id)
    parent_controls = build_parent_controls(requirements, targets_by_request, exact_rows, boundary_by_requirement)
    challenger_specs = build_challenger_specs(parent_controls, event15_rows)
    verdict_counts = counter_dict(row.get("parent_control_verdict") for row in parent_controls)
    action_counts = counter_dict(row.get("branch_local_action") for row in challenger_specs)
    counts = {
        "source_join_input_rows": len(source_join),
        "exact_feature_control_rows": len(exact_rows),
        "proxy_target_input_rows": len(targets),
        "requirement_input_rows": len(requirements),
        "boundary_integration_input_rows": len(boundary_integrations),
        "event15_empty_state_rows": len(event15_rows),
        "parent_control_rows": len(parent_controls),
        "challenger_spec_rows": len(challenger_specs),
        "bucket_rows": 0,
        "question_rows": 0,
    }
    bucket_rows = build_bucket_rows(parent_controls, challenger_specs, event15_rows, counts)
    counts["bucket_rows"] = len(bucket_rows)
    question_rows = build_questions(bucket_rows, challenger_specs, counts)
    counts["question_rows"] = len(question_rows)
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_boundary_challenger_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_BOUNDARY_CHALLENGER_SPEC_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "parent_control_verdict_counts": verdict_counts,
        "challenger_action_counts": action_counts,
        "not_completion": "This challenger-spec packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "test event15-empty source state across broader source activity controls",
            "run dedup/concentration stress for avoid challenger specs",
            "build sealed/proxy validation packets for surviving branch-local specs only",
        ],
    }
    write_jsonl(EVENT15_STATE_LEDGER, event15_rows)
    write_jsonl(PARENT_CONTROL_LEDGER, parent_controls)
    write_jsonl(CHALLENGER_SPEC_LEDGER, challenger_specs)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, verdict_counts)
    write_summary(generated_utc, counts, verdict_counts, action_counts)
    print(json.dumps({"ok": True, "counts": counts, "verdict_counts": verdict_counts, "action_counts": action_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
