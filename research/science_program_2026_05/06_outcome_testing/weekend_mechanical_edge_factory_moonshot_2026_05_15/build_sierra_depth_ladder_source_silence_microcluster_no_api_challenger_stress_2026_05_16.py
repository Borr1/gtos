#!/usr/bin/env python3
"""Stress broader source/proxy specs as branch-local no-API challenger candidates."""

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
BROADER_SPEC_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_SPEC_LEDGER_{STAMP}.jsonl"
BROADER_SCOPE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_SCOPE_LEDGER_{STAMP}.jsonl"
BROADER_SPEC_DECISION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_BROADER_SOURCE_PROXY_SPEC_DECISION_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_NO_API_CHALLENGER_STRESS_RESULT_{STAMP}.json"
SCOPE_CANDIDATE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_NO_API_CHALLENGER_STRESS_SCOPE_CANDIDATE_LEDGER_{STAMP}.jsonl"
LEAVE_GROUP_STRESS_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_NO_API_CHALLENGER_STRESS_LEAVE_GROUP_LEDGER_{STAMP}.jsonl"
SPEC_STRESS_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_NO_API_CHALLENGER_STRESS_SPEC_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_NO_API_CHALLENGER_STRESS_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_NO_API_CHALLENGER_STRESS_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_NO_API_CHALLENGER_STRESS_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Branch-local no-API challenger stress only; source-control/design evidence "
    "with no strategy validation, trade outcome, R/PnL, expectancy, live-readiness, "
    "promotion, or live deployment"
)

EXACT_FEATURE_STATUSES = {
    "LADDER_FEATURE_JOINED",
    "LADDER_FEATURE_JOINED_AFTER_IN_WINDOW_CLEAR_REPAIR",
    "LADDER_FEATURE_AND_BLOCKER_BUCKET_JOINED",
}

STRESS_GROUP_AXES = [
    "request_id",
    "source_date",
    "source_symbol",
    "source_proxy_family",
    "horizon_id",
    "command_feature_bucket",
]


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
    return None if math.isnan(out) or math.isinf(out) else out


def bool_value(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def share(values: list[bool]) -> float | None:
    return sum(1 for value in values if value) / len(values) if values else None


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def numeric_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def row_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    alignment_values = [
        value for row in rows
        if (value := bool_value(row.get("route_c_delta_aligned_with_future"))) is not None
    ]
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
        "source_date_counts": counter_dict(row.get("source_date") for row in rows),
        "source_symbol_counts": counter_dict(row.get("source_symbol") for row in rows),
        "source_proxy_family_counts": counter_dict(row.get("source_proxy_family") for row in rows),
        "route_queue_counts": counter_dict(row.get("route_c_queue_id") for row in rows),
        "command_feature_bucket_counts": counter_dict(row.get("command_feature_bucket") for row in rows),
        "horizon_counts": counter_dict(row.get("horizon_id") for row in rows),
    }


def rows_from_request_ids(rows_by_request: dict[str, dict[str, Any]], request_ids: list[str]) -> list[dict[str, Any]]:
    return [rows_by_request[request_id] for request_id in request_ids if request_id in rows_by_request]


def denominator_families(source_join: list[dict[str, Any]], exact_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "exact_feature_controls": exact_rows,
        "local_depth_available_source_proxy": [row for row in source_join if bool_value(row.get("depth_file_exists")) is True],
        "source_silence_context_proxy": [row for row in source_join if bool_value(row.get("source_silence_joined")) is True],
        "missing_depth_source_gap_route_proxy": [row for row in source_join if bool_value(row.get("depth_file_exists")) is False],
        "all_route_c_source_join_proxy": source_join,
    }


def axis_values(rows: list[dict[str, Any]], axis: str) -> set[Any]:
    return {row.get(axis) for row in rows if row.get(axis) is not None}


def matching_rows(
    denominator_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
    axes: list[str],
    exclude_request_ids: set[str],
) -> list[dict[str, Any]]:
    if not axes:
        return [row for row in denominator_rows if str(row.get("request_id")) not in exclude_request_ids]
    values_by_axis = {axis: axis_values(target_rows, axis) for axis in axes}
    rows: list[dict[str, Any]] = []
    for row in denominator_rows:
        if str(row.get("request_id")) in exclude_request_ids:
            continue
        if all(row.get(axis) in values_by_axis[axis] for axis in axes):
            rows.append(row)
    return rows


def verdict_vs_proxy(target_stats: dict[str, Any], proxy_stats: dict[str, Any], prefix: str) -> str:
    target_n = int(target_stats.get("n") or 0)
    proxy_n = int(proxy_stats.get("n") or 0)
    target_align = target_stats.get("route_alignment_share")
    proxy_align = proxy_stats.get("route_alignment_share")
    if target_n < 5:
        sample_prefix = f"{prefix}_TARGET_UNDERPOWERED_N_LT_5"
    elif target_n < 20:
        sample_prefix = f"{prefix}_TARGET_UNDERPOWERED_N_LT_20"
    else:
        sample_prefix = f"{prefix}_TARGET_N_OK"
    if proxy_n < 5:
        return f"{sample_prefix}_PROXY_UNDERPOWERED_N_LT_5"
    if proxy_n < 20:
        return f"{sample_prefix}_PROXY_UNDERPOWERED_N_LT_20"
    if target_align is None or proxy_align is None:
        return f"{sample_prefix}_DESCRIPTIVE_NO_ALIGNMENT"
    if target_align < proxy_align - 0.15:
        return f"{sample_prefix}_AVOID_DIRECTION_VS_PROXY"
    if target_align > proxy_align + 0.15:
        return f"{sample_prefix}_TARGET_ALIGNED_VS_PROXY"
    return f"{sample_prefix}_NEAR_PROXY"


def challenger_action_for_scope(status: str) -> str:
    if "AVOID_DIRECTION_VS_BROADER_PROXY" in status:
        return "NO_API_AVOID_CHALLENGER_STRESS_CANDIDATE"
    if "TARGET_ALIGNED_VS_BROADER_PROXY" in status:
        return "NO_API_INVERSE_OR_FAILURE_CONTEXT"
    if "NEAR_BROADER_PROXY" in status:
        return "NO_API_NEAR_CONTROL_CONTEXT"
    if "PROXY_UNDERPOWERED" in status:
        return "NO_API_PROXY_UNDERPOWERED_CONTEXT"
    return "NO_API_DESCRIPTIVE_CONTEXT"


def build_scope_candidate_rows(scope_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scope in scope_rows:
        action = challenger_action_for_scope(str(scope.get("broader_scope_status")))
        rows.append(
            {
                "scope_candidate_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-NO-API-CHALLENGER-SCOPE-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_broader_scope_id": scope.get("broader_source_proxy_scope_id"),
                "dedup_spec_id": scope.get("dedup_spec_id"),
                "branch_local_action": scope.get("branch_local_action"),
                "denominator_family": scope.get("denominator_family"),
                "control_scope": scope.get("control_scope"),
                "control_axes": scope.get("control_axes"),
                "broader_scope_status": scope.get("broader_scope_status"),
                "challenger_scope_action": action,
                "target_rows": scope.get("target_rows"),
                "broader_proxy_rows": scope.get("broader_proxy_rows"),
                "target_alignment_delta_vs_broader_proxy": scope.get("target_alignment_delta_vs_broader_proxy"),
                "next_same_resource_action": next_action_for_scope_candidate(action),
            }
        )
    return rows


def next_action_for_scope_candidate(action: str) -> str:
    if action == "NO_API_AVOID_CHALLENGER_STRESS_CANDIDATE":
        return "run leave-group stress and source-acquisition checks before any branch-local implementation candidate"
    if action == "NO_API_INVERSE_OR_FAILURE_CONTEXT":
        return "preserve as inverse/failure intelligence and test alternate axes/horizons"
    if action == "NO_API_PROXY_UNDERPOWERED_CONTEXT":
        return "broaden source/proxy denominators or exact source roots; do not wait"
    return "preserve context and continue stronger challenger routes"


def build_leave_group_stress_rows(
    scope_candidates: list[dict[str, Any]],
    spec_by_id: dict[str, dict[str, Any]],
    targets_by_request: dict[str, dict[str, Any]],
    denominators: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    avoid_candidates = [
        row for row in scope_candidates
        if row.get("challenger_scope_action") == "NO_API_AVOID_CHALLENGER_STRESS_CANDIDATE"
    ]
    for candidate in avoid_candidates:
        spec = spec_by_id[str(candidate["dedup_spec_id"])]
        original_targets = rows_from_request_ids(targets_by_request, spec.get("dedup_request_ids", []))
        control_axes = list(candidate.get("control_axes") or [])
        denominator_rows = denominators[str(candidate["denominator_family"])]
        for stress_axis in STRESS_GROUP_AXES:
            values = sorted(str(value) for value in axis_values(original_targets, stress_axis))
            for value in values:
                stressed_targets = [
                    row for row in original_targets
                    if str(row.get(stress_axis)) != value
                ]
                target_ids = {str(row.get("request_id")) for row in stressed_targets}
                proxy_rows = matching_rows(denominator_rows, stressed_targets, control_axes, target_ids)
                target_stats = row_stats(stressed_targets)
                proxy_stats = row_stats(proxy_rows)
                status = verdict_vs_proxy(target_stats, proxy_stats, "NO_API_LEAVE_GROUP_STRESS")
                rows.append(
                    {
                        "leave_group_stress_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-NO-API-CHALLENGER-LEAVE-{len(rows) + 1:06d}",
                        "route_id": ROUTE_ID,
                        "safe_flags": SAFE_FLAGS,
                        "evidence_boundary": EVIDENCE_BOUNDARY,
                        "scope_candidate_id": candidate.get("scope_candidate_id"),
                        "dedup_spec_id": candidate.get("dedup_spec_id"),
                        "denominator_family": candidate.get("denominator_family"),
                        "control_scope": candidate.get("control_scope"),
                        "control_axes": control_axes,
                        "stress_axis": stress_axis,
                        "left_out_value": value,
                        "remaining_target_rows": target_stats,
                        "recomputed_proxy_rows": proxy_stats,
                        "target_alignment_delta_vs_recomputed_proxy": numeric_delta(
                            target_stats.get("route_alignment_share"),
                            proxy_stats.get("route_alignment_share"),
                        ),
                        "leave_group_stress_status": status,
                    }
                )
    return rows


def build_spec_stress_rows(
    specs: list[dict[str, Any]],
    scope_candidates: list[dict[str, Any]],
    stress_rows: list[dict[str, Any]],
    spec_decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    stress_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    decision_by_spec = {str(row["dedup_spec_id"]): row for row in spec_decisions}
    for row in scope_candidates:
        candidates_by_spec[str(row["dedup_spec_id"])].append(row)
    for row in stress_rows:
        stress_by_spec[str(row["dedup_spec_id"])].append(row)
    rows: list[dict[str, Any]] = []
    for spec in specs:
        spec_id = str(spec["dedup_spec_id"])
        candidates = candidates_by_spec[spec_id]
        stresses = stress_by_spec[spec_id]
        action_counts = counter_dict(row.get("challenger_scope_action") for row in candidates)
        stress_counts = counter_dict(row.get("leave_group_stress_status") for row in stresses)
        avoid_candidates = action_counts.get("NO_API_AVOID_CHALLENGER_STRESS_CANDIDATE", 0)
        avoid_stresses = sum(
            count for status, count in stress_counts.items()
            if "AVOID_DIRECTION_VS_PROXY" in status
        )
        underpowered_stresses = sum(
            count for status, count in stress_counts.items()
            if "UNDERPOWERED" in status
        )
        if avoid_candidates and avoid_stresses and avoid_stresses >= underpowered_stresses:
            status = "NO_API_CHALLENGER_STRESS_AVOID_DIRECTION_PERSISTS_DESCRIPTIVE"
        elif avoid_candidates:
            status = "NO_API_CHALLENGER_STRESS_AVOID_DIRECTION_FRAGILE_OR_UNDERPOWERED"
        else:
            status = "NO_API_CHALLENGER_STRESS_NO_AVOID_SCOPE"
        rows.append(
            {
                "spec_stress_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-NO-API-CHALLENGER-SPEC-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "dedup_spec_id": spec_id,
                "branch_local_action": spec.get("branch_local_action"),
                "axis_repair_spec_status": spec.get("axis_repair_spec_status"),
                "broader_proxy_decision_status": decision_by_spec[spec_id].get("spec_broader_proxy_decision_status"),
                "scope_candidate_rows": len(candidates),
                "leave_group_stress_rows": len(stresses),
                "challenger_scope_action_counts": action_counts,
                "leave_group_stress_status_counts": stress_counts,
                "avoid_scope_candidate_count": avoid_candidates,
                "avoid_stress_count": avoid_stresses,
                "underpowered_stress_count": underpowered_stresses,
                "no_api_challenger_stress_status": status,
                "next_same_resource_action": next_action_for_spec_stress(status),
            }
        )
    return rows


def next_action_for_spec_stress(status: str) -> str:
    if status == "NO_API_CHALLENGER_STRESS_AVOID_DIRECTION_PERSISTS_DESCRIPTIVE":
        return "build source-acquisition and implementation-candidate packet with same-denominator controls only"
    if status == "NO_API_CHALLENGER_STRESS_AVOID_DIRECTION_FRAGILE_OR_UNDERPOWERED":
        return "split by stress axis, acquire/proxy more source rows, and preserve as fragile source-control intelligence"
    return "preserve as rejected/weak challenger context and continue alternate route families"


def build_bucket_rows(scope_candidates: list[dict[str, Any]], stress_rows: list[dict[str, Any]], spec_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets = [
        ("challenger_scope_action", counter_dict(row.get("challenger_scope_action") for row in scope_candidates)),
        ("scope_denominator_family", counter_dict(row.get("denominator_family") for row in scope_candidates)),
        ("leave_group_stress_status", counter_dict(row.get("leave_group_stress_status") for row in stress_rows)),
        ("leave_group_stress_axis", counter_dict(row.get("stress_axis") for row in stress_rows)),
        ("no_api_challenger_stress_status", counter_dict(row.get("no_api_challenger_stress_status") for row in spec_rows)),
    ]
    rows: list[dict[str, Any]] = []
    for family, counts in buckets:
        for bucket, count in counts.items():
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-NO-API-CHALLENGER-BUCKET-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": family,
                    "bucket": bucket,
                    "row_count": count,
                }
            )
    return rows


def build_question_rows(spec_rows: list[dict[str, Any]], stress_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in spec_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-NO-API-CHALLENGER-Q-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "spec_stress_next_action",
                "dedup_spec_id": spec.get("dedup_spec_id"),
                "stress_status": spec.get("no_api_challenger_stress_status"),
                "question": "Does this source-quality avoid challenger survive enough stress to justify source-acquisition and implementation-candidate packaging?",
                "next_action": spec.get("next_same_resource_action"),
            }
        )
    for stress in stress_rows:
        if "FRAGILE" in str(stress.get("leave_group_stress_status")) or "UNDERPOWERED" in str(stress.get("leave_group_stress_status")):
            rows.append(
                {
                    "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-NO-API-CHALLENGER-Q-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "question_family": "leave_group_stress_gap",
                    "dedup_spec_id": stress.get("dedup_spec_id"),
                    "stress_axis": stress.get("stress_axis"),
                    "left_out_value": stress.get("left_out_value"),
                    "question": "Which source/root/proxy split repairs this stressed group now?",
                    "next_action": "split, acquire exact source rows, or build strongest current proxy; do not wait",
                }
            )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_microcluster_no_api_challenger_stress_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_microcluster_no_api_challenger_stress_result", "created"),
        (SCOPE_CANDIDATE_LEDGER, "sierra_depth_ladder_source_silence_microcluster_no_api_challenger_scope_candidate_ledger", "created"),
        (LEAVE_GROUP_STRESS_LEDGER, "sierra_depth_ladder_source_silence_microcluster_no_api_challenger_leave_group_stress_ledger", "created"),
        (SPEC_STRESS_LEDGER, "sierra_depth_ladder_source_silence_microcluster_no_api_challenger_spec_stress_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_no_api_challenger_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_no_api_challenger_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_microcluster_no_api_challenger_stress_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], stress_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_microcluster_no_api_challenger_stress",
        "status": "done",
        "route": "source_silence_microcluster_no_api_challenger_stress",
        "details": "Stress-tested every broader avoid-direction source-control scope as branch-local no-API challenger context.",
        "counts": counts,
        "no_api_challenger_stress_status_counts": stress_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(SCOPE_CANDIDATE_LEDGER),
            relative(LEAVE_GROUP_STRESS_LEDGER),
            relative(SPEC_STRESS_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], stress_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Source-Silence Microcluster No-API Challenger Stress",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: branch-local no-API source-control challenger stress only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Spec Stress Status", ""])
    for key, value in sorted(stress_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Build source-acquisition and implementation-candidate packets only for stress-persistent descriptive avoid branches.",
            "- Split fragile/underpowered stress groups by stress axis and acquire/proxy current source rows now.",
            "- This is not a live rule, validation result, promotion dossier, or completion checkpoint.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    proxy_targets = read_jsonl(PROXY_TARGET_LEDGER)
    broader_specs = read_jsonl(BROADER_SPEC_LEDGER)
    broader_scopes = read_jsonl(BROADER_SCOPE_LEDGER)
    broader_spec_decisions = read_jsonl(BROADER_SPEC_DECISION_LEDGER)
    targets_by_request = {str(row["request_id"]): row for row in proxy_targets}
    spec_by_id = {str(row["dedup_spec_id"]): row for row in broader_specs}
    exact_rows = [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES and not row.get("source_silence_joined")
    ]
    denominators = denominator_families(source_join, exact_rows)
    scope_candidates = build_scope_candidate_rows(broader_scopes)
    leave_group_stress_rows = build_leave_group_stress_rows(scope_candidates, spec_by_id, targets_by_request, denominators)
    spec_stress_rows = build_spec_stress_rows(broader_specs, scope_candidates, leave_group_stress_rows, broader_spec_decisions)
    bucket_rows = build_bucket_rows(scope_candidates, leave_group_stress_rows, spec_stress_rows)
    question_rows = build_question_rows(spec_stress_rows, leave_group_stress_rows)
    stress_status_counts = counter_dict(row.get("no_api_challenger_stress_status") for row in spec_stress_rows)
    counts = {
        "source_join_input_rows": len(source_join),
        "proxy_target_input_rows": len(proxy_targets),
        "broader_spec_input_rows": len(broader_specs),
        "broader_scope_input_rows": len(broader_scopes),
        "broader_spec_decision_input_rows": len(broader_spec_decisions),
        "denominator_family_count": len(denominators),
        "stress_group_axis_count": len(STRESS_GROUP_AXES),
        "scope_candidate_rows": len(scope_candidates),
        "avoid_scope_candidate_rows": sum(1 for row in scope_candidates if row.get("challenger_scope_action") == "NO_API_AVOID_CHALLENGER_STRESS_CANDIDATE"),
        "leave_group_stress_rows": len(leave_group_stress_rows),
        "spec_stress_rows": len(spec_stress_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_no_api_challenger_stress_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_NO_API_CHALLENGER_STRESS_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "challenger_scope_action_counts": counter_dict(row.get("challenger_scope_action") for row in scope_candidates),
        "scope_denominator_family_counts": counter_dict(row.get("denominator_family") for row in scope_candidates),
        "leave_group_stress_status_counts": counter_dict(row.get("leave_group_stress_status") for row in leave_group_stress_rows),
        "leave_group_stress_axis_counts": counter_dict(row.get("stress_axis") for row in leave_group_stress_rows),
        "no_api_challenger_stress_status_counts": stress_status_counts,
        "not_completion": "This no-API challenger stress packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "build source-acquisition and implementation-candidate packets for stress-persistent descriptive avoid branches",
            "split fragile stress groups by source/date/symbol/horizon/command and acquire/proxy current source rows",
            "continue unrelated challenger families and exact .depth source-date acquisition",
        ],
    }
    write_jsonl(SCOPE_CANDIDATE_LEDGER, scope_candidates)
    write_jsonl(LEAVE_GROUP_STRESS_LEDGER, leave_group_stress_rows)
    write_jsonl(SPEC_STRESS_LEDGER, spec_stress_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, stress_status_counts)
    write_summary(generated_utc, counts, stress_status_counts)
    print(json.dumps({"ok": True, "counts": counts, "stress_status_counts": stress_status_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
