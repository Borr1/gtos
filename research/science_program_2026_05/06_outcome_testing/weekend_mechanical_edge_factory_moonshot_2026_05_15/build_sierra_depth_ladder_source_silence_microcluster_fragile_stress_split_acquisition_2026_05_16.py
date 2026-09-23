#!/usr/bin/env python3
"""Split fragile no-API challenger stress into source acquisition/proxy repair work."""

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

SOURCE_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_ROUTE_C_JOIN_LEDGER_{STAMP}.jsonl"
PROXY_TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_TARGET_LEDGER_{STAMP}.jsonl"
NO_API_SPEC_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_NO_API_CHALLENGER_STRESS_SPEC_LEDGER_{STAMP}.jsonl"
NO_API_LEAVE_GROUP_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_NO_API_CHALLENGER_STRESS_LEAVE_GROUP_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_FRAGILE_STRESS_SPLIT_ACQUISITION_RESULT_{STAMP}.json"
SPLIT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_FRAGILE_STRESS_SPLIT_LEDGER_{STAMP}.jsonl"
ACQUISITION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_FRAGILE_STRESS_ACQUISITION_LEDGER_{STAMP}.jsonl"
SPEC_PLAN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_FRAGILE_STRESS_SPEC_PLAN_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_FRAGILE_STRESS_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_FRAGILE_STRESS_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_FRAGILE_STRESS_SPLIT_ACQUISITION_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Branch-local fragile-stress split/acquisition packet only; source-control and "
    "repair evidence with no strategy validation, trade outcome, R/PnL, expectancy, "
    "live-readiness, promotion, or live deployment"
)

EXACT_FEATURE_STATUSES = {
    "LADDER_FEATURE_JOINED",
    "LADDER_FEATURE_JOINED_AFTER_IN_WINDOW_CLEAR_REPAIR",
    "LADDER_FEATURE_AND_BLOCKER_BUCKET_JOINED",
}

STRESS_AXES = [
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


def bool_value(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def request_ids_for_group(targets: list[dict[str, Any]], axis: str, value: str) -> list[str]:
    return sorted(
        str(row["request_id"])
        for row in targets
        if str(row.get(axis)) == value
    )


def rows_matching(rows: list[dict[str, Any]], axis: str, value: str) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get(axis)) == value]


def target_source_context(targets: list[dict[str, Any]], axis: str, value: str) -> dict[str, Any]:
    members = [row for row in targets if str(row.get(axis)) == value]
    return {
        "target_member_count": len(members),
        "target_request_ids": sorted(str(row["request_id"]) for row in members),
        "target_depth_paths": sorted({str(row.get("depth_path")) for row in members if row.get("depth_path")}),
        "target_source_dates": counter_dict(row.get("source_date") for row in members),
        "target_source_symbols": counter_dict(row.get("source_symbol") for row in members),
        "target_source_proxy_families": counter_dict(row.get("source_proxy_family") for row in members),
        "target_command_feature_buckets": counter_dict(row.get("command_feature_bucket") for row in members),
        "target_horizons": counter_dict(row.get("horizon_id") for row in members),
    }


def acquisition_status(exact_n: int, local_depth_n: int, source_join_n: int, proxy_target_n: int) -> str:
    if exact_n >= 20:
        return "CURRENT_EXACT_FEATURE_PROXY_ROWS_AVAILABLE_RESTRESS_NOW"
    if local_depth_n >= 20:
        return "LOCAL_DEPTH_ROWS_AVAILABLE_EXACT_FEATURE_UNDERPOWERED_REPLAY_OR_PROXY_NOW"
    if source_join_n >= 20:
        return "ROUTE_C_SOURCE_JOIN_PROXY_AVAILABLE_EXACT_DEPTH_ACQUISITION_NEEDED"
    if proxy_target_n:
        return "ONLY_TARGET_PROXY_ROWS_AVAILABLE_NEEDS_BROADER_SOURCE_ACQUISITION"
    return "CURRENT_PROXY_UNDERPOWERED_NEEDS_SOURCE_SEARCH_OR_ALTERNATE_MARKET_PROXY"


def split_status(status_counts: dict[str, int]) -> str:
    avoid = sum(count for status, count in status_counts.items() if "AVOID_DIRECTION_VS_PROXY" in status)
    underpowered = sum(count for status, count in status_counts.items() if "UNDERPOWERED" in status)
    aligned = sum(count for status, count in status_counts.items() if "TARGET_ALIGNED_VS_PROXY" in status)
    near = sum(count for status, count in status_counts.items() if "NEAR_PROXY" in status)
    if avoid and avoid >= underpowered:
        return "FRAGILE_SPLIT_AVOID_REMAINS_BUT_UNDERPOWERED"
    if avoid:
        return "FRAGILE_SPLIT_AVOID_EXISTS_INSIDE_UNDERPOWERED_CONTEXT"
    if aligned:
        return "FRAGILE_SPLIT_INVERSE_OR_TARGET_ALIGNED"
    if near:
        return "FRAGILE_SPLIT_NEAR_CONTROL"
    return "FRAGILE_SPLIT_PROXY_UNDERPOWERED_OR_NO_ALIGNMENT"


def build_split_rows(stress_rows: list[dict[str, Any]], proxy_targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    targets_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in proxy_targets:
        # Membership is inferred later through target request ids in the stress rows.
        targets_by_spec["ALL"].append(row)
    for row in stress_rows:
        grouped[(str(row["dedup_spec_id"]), str(row["stress_axis"]), str(row["left_out_value"]))].append(row)
    rows: list[dict[str, Any]] = []
    for (spec_id, axis, value), group in sorted(grouped.items()):
        target_context = target_source_context(proxy_targets, axis, value)
        status_counts = counter_dict(row.get("leave_group_stress_status") for row in group)
        rows.append(
            {
                "fragile_stress_split_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-FRAGILE-STRESS-SPLIT-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "dedup_spec_id": spec_id,
                "stress_axis": axis,
                "left_out_value": value,
                "leave_group_stress_rows": len(group),
                "leave_group_stress_status_counts": status_counts,
                "fragile_split_status": split_status(status_counts),
                "target_source_context": target_context,
                "next_same_resource_action": "map this split to current proxy counts and exact source acquisition now",
            }
        )
    return rows


def build_acquisition_rows(
    split_rows: list[dict[str, Any]],
    source_join: list[dict[str, Any]],
    proxy_targets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    exact_rows = [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES and not row.get("source_silence_joined")
    ]
    local_depth_rows = [row for row in source_join if bool_value(row.get("depth_file_exists")) is True]
    rows: list[dict[str, Any]] = []
    for split in split_rows:
        axis = str(split["stress_axis"])
        value = str(split["left_out_value"])
        exact_matches = rows_matching(exact_rows, axis, value)
        local_depth_matches = rows_matching(local_depth_rows, axis, value)
        source_join_matches = rows_matching(source_join, axis, value)
        target_matches = rows_matching(proxy_targets, axis, value)
        status = acquisition_status(len(exact_matches), len(local_depth_matches), len(source_join_matches), len(target_matches))
        rows.append(
            {
                "acquisition_requirement_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-FRAGILE-STRESS-ACQ-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "fragile_stress_split_id": split.get("fragile_stress_split_id"),
                "dedup_spec_id": split.get("dedup_spec_id"),
                "stress_axis": axis,
                "left_out_value": value,
                "fragile_split_status": split.get("fragile_split_status"),
                "current_exact_feature_rows": len(exact_matches),
                "current_local_depth_rows": len(local_depth_matches),
                "current_source_join_rows": len(source_join_matches),
                "current_target_proxy_rows": len(target_matches),
                "target_source_context": split.get("target_source_context"),
                "acquisition_status": status,
                "next_same_resource_action": next_action_for_acquisition(status),
            }
        )
    return rows


def next_action_for_acquisition(status: str) -> str:
    if status == "CURRENT_EXACT_FEATURE_PROXY_ROWS_AVAILABLE_RESTRESS_NOW":
        return "rerun exact-feature stress at this split without needing new source"
    if status == "LOCAL_DEPTH_ROWS_AVAILABLE_EXACT_FEATURE_UNDERPOWERED_REPLAY_OR_PROXY_NOW":
        return "replay local depth/source rows or build source-safe proxy now"
    if status == "ROUTE_C_SOURCE_JOIN_PROXY_AVAILABLE_EXACT_DEPTH_ACQUISITION_NEEDED":
        return "use route-c proxy now and search/acquire exact depth source-date rows"
    if status == "ONLY_TARGET_PROXY_ROWS_AVAILABLE_NEEDS_BROADER_SOURCE_ACQUISITION":
        return "search broader source roots and alternate market proxies now"
    return "search local/free/current roots and construct nearest honest proxy now"


def build_spec_plan_rows(spec_rows: list[dict[str, Any]], split_rows: list[dict[str, Any]], acquisition_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    split_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    acquisition_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in split_rows:
        split_by_spec[str(row["dedup_spec_id"])].append(row)
    for row in acquisition_rows:
        acquisition_by_spec[str(row["dedup_spec_id"])].append(row)
    rows: list[dict[str, Any]] = []
    for spec in spec_rows:
        spec_id = str(spec["dedup_spec_id"])
        spec_splits = split_by_spec[spec_id]
        spec_acq = acquisition_by_spec[spec_id]
        exact_ready = sum(1 for row in spec_acq if row["acquisition_status"] == "CURRENT_EXACT_FEATURE_PROXY_ROWS_AVAILABLE_RESTRESS_NOW")
        local_ready = sum(1 for row in spec_acq if row["acquisition_status"] == "LOCAL_DEPTH_ROWS_AVAILABLE_EXACT_FEATURE_UNDERPOWERED_REPLAY_OR_PROXY_NOW")
        source_proxy = sum(1 for row in spec_acq if row["acquisition_status"] == "ROUTE_C_SOURCE_JOIN_PROXY_AVAILABLE_EXACT_DEPTH_ACQUISITION_NEEDED")
        if exact_ready:
            status = "SPEC_FRAGILE_SPLIT_HAS_EXACT_RESTRESS_ROUTE"
        elif local_ready:
            status = "SPEC_FRAGILE_SPLIT_HAS_LOCAL_DEPTH_REPLAY_ROUTE"
        elif source_proxy:
            status = "SPEC_FRAGILE_SPLIT_HAS_ROUTE_C_PROXY_AND_DEPTH_ACQUISITION_ROUTE"
        else:
            status = "SPEC_FRAGILE_SPLIT_NEEDS_BROADER_SOURCE_OR_ALTERNATE_PROXY"
        rows.append(
            {
                "spec_plan_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-FRAGILE-STRESS-SPEC-PLAN-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "dedup_spec_id": spec_id,
                "branch_local_action": spec.get("branch_local_action"),
                "prior_no_api_stress_status": spec.get("no_api_challenger_stress_status"),
                "split_rows": len(spec_splits),
                "acquisition_rows": len(spec_acq),
                "fragile_split_status_counts": counter_dict(row.get("fragile_split_status") for row in spec_splits),
                "acquisition_status_counts": counter_dict(row.get("acquisition_status") for row in spec_acq),
                "spec_fragile_split_plan_status": status,
                "next_same_resource_action": next_action_for_spec_plan(status),
            }
        )
    return rows


def next_action_for_spec_plan(status: str) -> str:
    if status == "SPEC_FRAGILE_SPLIT_HAS_EXACT_RESTRESS_ROUTE":
        return "rerun exact split stress and preserve only stress-surviving exact branches"
    if status == "SPEC_FRAGILE_SPLIT_HAS_LOCAL_DEPTH_REPLAY_ROUTE":
        return "build local-depth replay/proxy packet for these splits"
    if status == "SPEC_FRAGILE_SPLIT_HAS_ROUTE_C_PROXY_AND_DEPTH_ACQUISITION_ROUTE":
        return "search/acquire exact depth rows while using route-c proxy stress now"
    return "expand source roots, alternate market proxies, or unrelated challenger routes now"


def build_bucket_rows(split_rows: list[dict[str, Any]], acquisition_rows: list[dict[str, Any]], spec_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets = [
        ("fragile_split_status", counter_dict(row.get("fragile_split_status") for row in split_rows)),
        ("stress_axis", counter_dict(row.get("stress_axis") for row in split_rows)),
        ("acquisition_status", counter_dict(row.get("acquisition_status") for row in acquisition_rows)),
        ("spec_fragile_split_plan_status", counter_dict(row.get("spec_fragile_split_plan_status") for row in spec_rows)),
    ]
    rows: list[dict[str, Any]] = []
    for family, counts in buckets:
        for bucket, count in counts.items():
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-FRAGILE-STRESS-BUCKET-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": family,
                    "bucket": bucket,
                    "row_count": count,
                }
            )
    return rows


def build_question_rows(split_rows: list[dict[str, Any]], acquisition_rows: list[dict[str, Any]], spec_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in spec_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-FRAGILE-STRESS-Q-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "spec_fragile_split_plan",
                "dedup_spec_id": spec.get("dedup_spec_id"),
                "status": spec.get("spec_fragile_split_plan_status"),
                "question": "Which exact current-source route repairs this fragile spec next?",
                "next_action": spec.get("next_same_resource_action"),
            }
        )
    for acquisition in acquisition_rows:
        if acquisition.get("acquisition_status") != "CURRENT_EXACT_FEATURE_PROXY_ROWS_AVAILABLE_RESTRESS_NOW":
            rows.append(
                {
                    "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-FRAGILE-STRESS-Q-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "question_family": "split_acquisition_or_proxy",
                    "dedup_spec_id": acquisition.get("dedup_spec_id"),
                    "stress_axis": acquisition.get("stress_axis"),
                    "left_out_value": acquisition.get("left_out_value"),
                    "status": acquisition.get("acquisition_status"),
                    "question": "Which same-resource source search, local-depth replay, or proxy computation should run for this split?",
                    "next_action": acquisition.get("next_same_resource_action"),
                }
            )
    for split in split_rows:
        if "UNDERPOWERED" in str(split.get("fragile_split_status")):
            rows.append(
                {
                    "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-FRAGILE-STRESS-Q-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "question_family": "underpowered_split_repair",
                    "dedup_spec_id": split.get("dedup_spec_id"),
                    "stress_axis": split.get("stress_axis"),
                    "left_out_value": split.get("left_out_value"),
                    "question": "Can this underpowered split be repaired by exact source acquisition, broader proxy, or axis inversion now?",
                    "next_action": "use acquisition ledger and run next split/replay packet; do not wait",
                }
            )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_microcluster_fragile_stress_split_acquisition_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_microcluster_fragile_stress_split_acquisition_result", "created"),
        (SPLIT_LEDGER, "sierra_depth_ladder_source_silence_microcluster_fragile_stress_split_ledger", "created"),
        (ACQUISITION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_fragile_stress_acquisition_ledger", "created"),
        (SPEC_PLAN_LEDGER, "sierra_depth_ladder_source_silence_microcluster_fragile_stress_spec_plan_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_fragile_stress_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_fragile_stress_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_microcluster_fragile_stress_split_acquisition_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], plan_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_microcluster_fragile_stress_split_acquisition",
        "status": "done",
        "route": "source_silence_microcluster_fragile_stress_split_acquisition",
        "details": "Split fragile no-API challenger stress groups into exact current source-acquisition and proxy-repair requirements.",
        "counts": counts,
        "spec_fragile_split_plan_status_counts": plan_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(SPLIT_LEDGER),
            relative(ACQUISITION_LEDGER),
            relative(SPEC_PLAN_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], plan_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Source-Silence Microcluster Fragile Stress Split Acquisition",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: branch-local fragile-stress split/source-acquisition only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Spec Plan Status", ""])
    for key, value in sorted(plan_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Rerun exact split stress where exact-feature rows already exist.",
            "- Build local-depth replay/proxy packets where local depth rows exist but exact features are underpowered.",
            "- Search/acquire exact `.depth` source-date rows where only route-c proxy rows exist.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    proxy_targets = read_jsonl(PROXY_TARGET_LEDGER)
    no_api_specs = read_jsonl(NO_API_SPEC_LEDGER)
    stress_rows = read_jsonl(NO_API_LEAVE_GROUP_LEDGER)
    split_rows = build_split_rows(stress_rows, proxy_targets)
    acquisition_rows = build_acquisition_rows(split_rows, source_join, proxy_targets)
    spec_plan_rows = build_spec_plan_rows(no_api_specs, split_rows, acquisition_rows)
    bucket_rows = build_bucket_rows(split_rows, acquisition_rows, spec_plan_rows)
    question_rows = build_question_rows(split_rows, acquisition_rows, spec_plan_rows)
    plan_counts = counter_dict(row.get("spec_fragile_split_plan_status") for row in spec_plan_rows)
    counts = {
        "source_join_input_rows": len(source_join),
        "proxy_target_input_rows": len(proxy_targets),
        "no_api_spec_input_rows": len(no_api_specs),
        "leave_group_stress_input_rows": len(stress_rows),
        "stress_axis_count": len(STRESS_AXES),
        "fragile_stress_split_rows": len(split_rows),
        "acquisition_requirement_rows": len(acquisition_rows),
        "spec_plan_rows": len(spec_plan_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_fragile_stress_split_acquisition_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_FRAGILE_STRESS_SPLIT_ACQUISITION_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "fragile_split_status_counts": counter_dict(row.get("fragile_split_status") for row in split_rows),
        "stress_axis_counts": counter_dict(row.get("stress_axis") for row in split_rows),
        "acquisition_status_counts": counter_dict(row.get("acquisition_status") for row in acquisition_rows),
        "spec_fragile_split_plan_status_counts": plan_counts,
        "not_completion": "This fragile-stress split/acquisition packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "rerun exact split stress where exact-feature rows already exist",
            "build local-depth replay/proxy packet where local depth exists but exact features are underpowered",
            "search/acquire exact .depth source-date rows where only route-c proxy rows exist",
        ],
    }
    write_jsonl(SPLIT_LEDGER, split_rows)
    write_jsonl(ACQUISITION_LEDGER, acquisition_rows)
    write_jsonl(SPEC_PLAN_LEDGER, spec_plan_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, plan_counts)
    write_summary(generated_utc, counts, plan_counts)
    print(json.dumps({"ok": True, "counts": counts, "plan_counts": plan_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
