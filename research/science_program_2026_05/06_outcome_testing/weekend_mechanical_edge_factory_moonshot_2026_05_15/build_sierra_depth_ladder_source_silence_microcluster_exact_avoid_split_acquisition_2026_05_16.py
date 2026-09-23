#!/usr/bin/env python3
"""Turn exact avoid concentration stress into split/acquisition requirements."""

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

BRANCH_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_BRANCH_LEDGER_{STAMP}.jsonl"
GROUP_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_GROUP_STRESS_LEDGER_{STAMP}.jsonl"
NON_EXACT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_NON_EXACT_NEXT_ROUTE_LEDGER_{STAMP}.jsonl"
SPEC_PLAN_INPUT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPEC_PLAN_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPLIT_ACQUISITION_RESULT_{STAMP}.json"
BRANCH_SPLIT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPLIT_BRANCH_LEDGER_{STAMP}.jsonl"
GROUP_SPLIT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPLIT_GROUP_LEDGER_{STAMP}.jsonl"
ACQUISITION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPLIT_ACQUISITION_LEDGER_{STAMP}.jsonl"
SPEC_SPLIT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPLIT_SPEC_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPLIT_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPLIT_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPLIT_ACQUISITION_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Branch-local exact avoid concentration split/acquisition routing only; "
    "source-control/repair evidence with no validation, R/PnL, expectancy, "
    "live-readiness, promotion, or live deployment"
)

WEAKENING_STATUSES = {
    "EXACT_AVOID_CONCENTRATION_WEAKENS_TO_NEAR_EXACT",
    "EXACT_AVOID_WEAKENS_TO_NEAR_EXACT_AFTER_LEAVE_GROUP",
    "EXACT_AVOID_REVERSES_TO_TARGET_ALIGNED_AFTER_LEAVE_GROUP",
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


def counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def classify_group(row: dict[str, Any]) -> str:
    status = str(row.get("group_stress_status"))
    if status in WEAKENING_STATUSES:
        axis = str(row.get("concentration_axis"))
        if axis == "source_date":
            return "GROUP_SPLIT_WEAKENING_SOURCE_DATE"
        if axis == "source_symbol":
            return "GROUP_SPLIT_WEAKENING_SOURCE_SYMBOL"
        return "GROUP_SPLIT_WEAKENING_OTHER_AXIS"
    if status == "EXACT_AVOID_PERSISTS_AFTER_LEAVE_GROUP":
        return "GROUP_SPLIT_PERSISTENT_AFTER_LEAVE_GROUP"
    if status == "EXACT_AVOID_GROUP_REMOVAL_TARGET_UNDERPOWERED_N_LT_5":
        return "GROUP_SPLIT_TARGET_UNDERPOWERED_AFTER_REMOVAL"
    if status == "EXACT_AVOID_LEAVE_GROUP_CONTROL_UNDERPOWERED":
        return "GROUP_SPLIT_CONTROL_UNDERPOWERED_AFTER_REMOVAL"
    return "GROUP_SPLIT_OTHER_DESCRIPTIVE_STATUS"


def build_group_split_rows(group_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in group_rows:
        split_status = classify_group(row)
        rows.append(
            {
                "group_split_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-AVOID-SPLIT-GROUP-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_group_stress_id": row.get("group_stress_id"),
                "exact_split_restress_id": row.get("exact_split_restress_id"),
                "fragile_stress_split_id": row.get("fragile_stress_split_id"),
                "dedup_spec_id": row.get("dedup_spec_id"),
                "concentration_axis": row.get("concentration_axis"),
                "concentration_value": row.get("concentration_value"),
                "group_role": row.get("group_role"),
                "target_group_n": row.get("target_group_n"),
                "exact_group_n": row.get("exact_group_n"),
                "target_group_share": row.get("target_group_share"),
                "exact_group_share": row.get("exact_group_share"),
                "target_without_group_n": row.get("target_without_group", {}).get("n"),
                "exact_without_group_n": row.get("exact_without_group", {}).get("n"),
                "after_leave_group_status": row.get("after_leave_group_status"),
                "group_stress_status": row.get("group_stress_status"),
                "group_split_status": split_status,
                "next_same_resource_action": group_action(split_status),
                "not_completion": "Group split rows route current-data work; they are not a stop condition.",
            }
        )
    return rows


def group_action(status: str) -> str:
    if status == "GROUP_SPLIT_WEAKENING_SOURCE_DATE":
        return "split by this source date and acquire/replay broader same-date exact source context now"
    if status == "GROUP_SPLIT_WEAKENING_SOURCE_SYMBOL":
        return "split by this source symbol and acquire/replay broader exact source-symbol context now"
    if status == "GROUP_SPLIT_WEAKENING_OTHER_AXIS":
        return "split by this axis and test source/proxy expansion now"
    if status == "GROUP_SPLIT_PERSISTENT_AFTER_LEAVE_GROUP":
        return "preserve as persistent descriptive avoid context while broadening denominator"
    return "expand source/proxy rows because leave-group stress is underpowered or descriptive"


def build_branch_split_rows(
    branch_rows: list[dict[str, Any]],
    group_split_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups_by_branch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in group_split_rows:
        groups_by_branch[str(row.get("exact_split_restress_id"))].append(row)

    rows: list[dict[str, Any]] = []
    for branch in branch_rows:
        if not branch.get("is_exact_descriptive_avoid_branch"):
            continue
        restress_id = str(branch.get("exact_split_restress_id"))
        groups = groups_by_branch.get(restress_id, [])
        weakening = [row for row in groups if str(row.get("group_split_status")).startswith("GROUP_SPLIT_WEAKENING")]
        source_date_weakening = [row for row in weakening if row.get("concentration_axis") == "source_date"]
        source_symbol_weakening = [row for row in weakening if row.get("concentration_axis") == "source_symbol"]
        branch_split_status = classify_branch(branch, weakening, source_date_weakening, source_symbol_weakening)
        rows.append(
            {
                "branch_split_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-AVOID-SPLIT-BRANCH-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "exact_avoid_branch_id": branch.get("exact_avoid_branch_id"),
                "exact_split_restress_id": branch.get("exact_split_restress_id"),
                "fragile_stress_split_id": branch.get("fragile_stress_split_id"),
                "source_acquisition_requirement_id": branch.get("source_acquisition_requirement_id"),
                "dedup_spec_id": branch.get("dedup_spec_id"),
                "prior_branch_concentration_status": branch.get("branch_concentration_status"),
                "target_n": branch.get("target_n"),
                "exact_feature_n": branch.get("exact_feature_n"),
                "dominant_target_source_date": branch.get("dominant_target_source_date"),
                "dominant_target_source_date_share": branch.get("dominant_target_source_date_share"),
                "dominant_target_source_symbol": branch.get("dominant_target_source_symbol"),
                "dominant_target_source_symbol_share": branch.get("dominant_target_source_symbol_share"),
                "weakening_group_rows": len(weakening),
                "source_date_weakening_group_rows": len(source_date_weakening),
                "source_symbol_weakening_group_rows": len(source_symbol_weakening),
                "weakening_values_by_axis": values_by_axis(weakening),
                "branch_split_status": branch_split_status,
                "next_same_resource_action": branch_action(branch_split_status),
                "not_completion": "Branch split rows create immediate acquisition/replay requirements, not live logic.",
            }
        )
    return rows


def values_by_axis(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    values: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        values[str(row.get("concentration_axis"))].add(str(row.get("concentration_value")))
    return {axis: sorted(axis_values) for axis, axis_values in sorted(values.items())}


def classify_branch(
    branch: dict[str, Any],
    weakening: list[dict[str, Any]],
    source_date_weakening: list[dict[str, Any]],
    source_symbol_weakening: list[dict[str, Any]],
) -> str:
    prior = str(branch.get("branch_concentration_status"))
    if weakening and source_date_weakening and len(source_date_weakening) == len(weakening):
        return "BRANCH_SPLIT_CONCENTRATION_SENSITIVE_SOURCE_DATE_ONLY"
    if weakening and source_symbol_weakening and len(source_symbol_weakening) == len(weakening):
        return "BRANCH_SPLIT_CONCENTRATION_SENSITIVE_SOURCE_SYMBOL_ONLY"
    if weakening:
        return "BRANCH_SPLIT_CONCENTRATION_SENSITIVE_MIXED_AXIS"
    if prior == "EXACT_AVOID_BRANCH_PERSISTS_ALL_FEASIBLE_GROUP_STRESS":
        return "BRANCH_SPLIT_PERSISTENT_BROADER_DENOMINATOR_REQUIRED"
    if prior == "EXACT_AVOID_BRANCH_TARGET_N_LT_5_SOURCE_EXPANSION_REQUIRED":
        return "BRANCH_SPLIT_TARGET_N_LT_5_SOURCE_EXPANSION_REQUIRED"
    return "BRANCH_SPLIT_DESCRIPTIVE_SOURCE_EXPANSION_REQUIRED"


def branch_action(status: str) -> str:
    if status == "BRANCH_SPLIT_CONCENTRATION_SENSITIVE_SOURCE_DATE_ONLY":
        return "build source-date split packet and exact/broader date acquisition now"
    if status == "BRANCH_SPLIT_CONCENTRATION_SENSITIVE_SOURCE_SYMBOL_ONLY":
        return "build source-symbol split packet and exact/broader symbol acquisition now"
    if status == "BRANCH_SPLIT_CONCENTRATION_SENSITIVE_MIXED_AXIS":
        return "split by every weakening axis/value and acquire/proxy missing source context now"
    if status == "BRANCH_SPLIT_PERSISTENT_BROADER_DENOMINATOR_REQUIRED":
        return "broaden exact source/proxy denominator before implementation consideration"
    return "expand source denominator or local-depth proxy because the branch remains underpowered/descriptive"


def build_acquisition_rows(
    branch_split_rows: list[dict[str, Any]],
    group_split_rows: list[dict[str, Any]],
    non_exact_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for branch in branch_split_rows:
        rows.append(
            acquisition(
                len(rows) + 1,
                "branch_split",
                branch.get("branch_split_id"),
                branch.get("dedup_spec_id"),
                branch.get("branch_split_status"),
                branch.get("next_same_resource_action"),
                {
                    "exact_split_restress_id": branch.get("exact_split_restress_id"),
                    "target_n": branch.get("target_n"),
                    "exact_feature_n": branch.get("exact_feature_n"),
                    "weakening_values_by_axis": branch.get("weakening_values_by_axis"),
                },
            )
        )
    for group in group_split_rows:
        if not str(group.get("group_split_status")).startswith("GROUP_SPLIT_WEAKENING"):
            continue
        rows.append(
            acquisition(
                len(rows) + 1,
                "weakening_group",
                group.get("group_split_id"),
                group.get("dedup_spec_id"),
                group.get("group_split_status"),
                group.get("next_same_resource_action"),
                {
                    "exact_split_restress_id": group.get("exact_split_restress_id"),
                    "concentration_axis": group.get("concentration_axis"),
                    "concentration_value": group.get("concentration_value"),
                    "target_group_n": group.get("target_group_n"),
                    "target_group_share": group.get("target_group_share"),
                },
            )
        )
    for route in non_exact_rows:
        rows.append(
            acquisition(
                len(rows) + 1,
                "non_exact_route",
                route.get("non_exact_next_route_id"),
                route.get("dedup_spec_id"),
                route.get("non_exact_next_route_status"),
                route.get("next_same_resource_action"),
                {
                    "non_exact_route_id": route.get("non_exact_route_id"),
                    "current_local_depth_rows": route.get("current_local_depth_rows"),
                    "current_source_join_rows": route.get("current_source_join_rows"),
                    "current_target_proxy_rows": route.get("current_target_proxy_rows"),
                },
            )
        )
    return rows


def acquisition(
    index: int,
    scope: str,
    source_id: Any,
    spec_id: Any,
    status: Any,
    action: Any,
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "split_acquisition_requirement_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-AVOID-SPLIT-ACQ-{index:05d}",
        "route_id": ROUTE_ID,
        "safe_flags": SAFE_FLAGS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "requirement_scope": scope,
        "source_row_id": source_id,
        "dedup_spec_id": spec_id,
        "status": status,
        "details": details,
        "next_same_resource_action": action,
        "not_completion": "Acquisition requirements are immediate work items inside the moonshot, not waiting labels.",
    }


def build_spec_split_rows(
    spec_rows: list[dict[str, Any]],
    branch_split_rows: list[dict[str, Any]],
    acquisition_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    branches_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    acquisitions_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in branch_split_rows:
        branches_by_spec[str(row.get("dedup_spec_id"))].append(row)
    for row in acquisition_rows:
        acquisitions_by_spec[str(row.get("dedup_spec_id"))].append(row)
    rows: list[dict[str, Any]] = []
    for spec in spec_rows:
        spec_id = str(spec.get("dedup_spec_id"))
        branches = branches_by_spec.get(spec_id, [])
        acquisitions = acquisitions_by_spec.get(spec_id, [])
        branch_counts = counter_dict(row.get("branch_split_status") for row in branches)
        acquisition_counts = counter_dict(row.get("requirement_scope") for row in acquisitions)
        status = classify_spec(branches)
        rows.append(
            {
                "split_spec_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-AVOID-SPLIT-SPEC-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "dedup_spec_id": spec_id,
                "prior_exact_avoid_spec_plan_status": spec.get("exact_avoid_spec_plan_status"),
                "branch_split_rows": len(branches),
                "split_acquisition_requirement_rows": len(acquisitions),
                "branch_split_status_counts": branch_counts,
                "acquisition_scope_counts": acquisition_counts,
                "split_spec_status": status,
                "next_same_resource_action": spec_action(status),
                "not_completion": "Spec split plan routes the next packet only; it is not validation.",
            }
        )
    return rows


def classify_spec(branches: list[dict[str, Any]]) -> str:
    statuses = {str(row.get("branch_split_status")) for row in branches}
    if any("CONCENTRATION_SENSITIVE" in status for status in statuses):
        return "SPEC_SPLIT_HAS_CONCENTRATION_SENSITIVE_BRANCHES"
    if "BRANCH_SPLIT_PERSISTENT_BROADER_DENOMINATOR_REQUIRED" in statuses:
        return "SPEC_SPLIT_PERSISTENT_BRANCHES_REQUIRE_BROADER_DENOMINATOR"
    return "SPEC_SPLIT_SOURCE_EXPANSION_REQUIRED"


def spec_action(status: str) -> str:
    if status == "SPEC_SPLIT_HAS_CONCENTRATION_SENSITIVE_BRANCHES":
        return "materialize source-date/source-axis split packet from acquisition rows now"
    if status == "SPEC_SPLIT_PERSISTENT_BRANCHES_REQUIRE_BROADER_DENOMINATOR":
        return "broaden exact source/proxy denominator and test persistent branches against new controls now"
    return "expand source/proxy denominator and local-depth replay before any stronger interpretation"


def build_bucket_rows(
    group_split_rows: list[dict[str, Any]],
    branch_split_rows: list[dict[str, Any]],
    acquisition_rows: list[dict[str, Any]],
    spec_split_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    bucket_sets = [
        ("group_split_status", counter_dict(row.get("group_split_status") for row in group_split_rows)),
        ("group_split_axis", counter_dict(row.get("concentration_axis") for row in group_split_rows)),
        ("weakening_axis", counter_dict(row.get("concentration_axis") for row in group_split_rows if str(row.get("group_split_status")).startswith("GROUP_SPLIT_WEAKENING"))),
        ("branch_split_status", counter_dict(row.get("branch_split_status") for row in branch_split_rows)),
        ("acquisition_requirement_scope", counter_dict(row.get("requirement_scope") for row in acquisition_rows)),
        ("acquisition_requirement_status", counter_dict(row.get("status") for row in acquisition_rows)),
        ("split_spec_status", counter_dict(row.get("split_spec_status") for row in spec_split_rows)),
    ]
    for family, counts in bucket_sets:
        for value, count in counts.items():
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-AVOID-SPLIT-BUCKET-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": family,
                    "bucket_value": value,
                    "row_count": count,
                    "not_completion": "Bucket rows summarize full ledgers without replacing them.",
                }
            )
    return rows


def build_question_rows(
    branch_split_rows: list[dict[str, Any]],
    acquisition_rows: list[dict[str, Any]],
    spec_split_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in [*branch_split_rows, *acquisition_rows, *spec_split_rows]:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-AVOID-SPLIT-Q-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_row_id": row.get("branch_split_id")
                or row.get("split_acquisition_requirement_id")
                or row.get("split_spec_id"),
                "dedup_spec_id": row.get("dedup_spec_id"),
                "status": row.get("branch_split_status") or row.get("status") or row.get("split_spec_status"),
                "question": "Which same-resource computation/acquisition/replay follows from this split row now?",
                "next_same_resource_action": row.get("next_same_resource_action"),
                "not_completion": "Questions are immediate work generators, not a future-work sink.",
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    artifacts = manifest.setdefault("artifacts", [])
    existing = {artifact.get("path") for artifact in artifacts if isinstance(artifact, dict)}
    for path, description in [
        (Path(__file__).resolve(), "Builder for exact avoid split/acquisition requirements."),
        (RESULT_PATH, "Exact avoid split/acquisition result JSON."),
        (BRANCH_SPLIT_LEDGER, "Exact avoid branch split ledger."),
        (GROUP_SPLIT_LEDGER, "Exact avoid full group split ledger."),
        (ACQUISITION_LEDGER, "Exact avoid split acquisition/replay requirements."),
        (SPEC_SPLIT_LEDGER, "Exact avoid spec split plan ledger."),
        (BUCKET_LEDGER, "Exact avoid split bucket ledger."),
        (QUESTION_LEDGER, "Exact avoid split question/action ledger."),
        (SUMMARY_PATH, "Human summary for exact avoid split/acquisition packet."),
    ]:
        rel = relative(path)
        if rel not in existing:
            artifacts.append({"path": rel, "description": description})
            existing.add(rel)
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], spec_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_microcluster_exact_avoid_split_acquisition",
        "status": "done",
        "route": "source_silence_microcluster_exact_avoid_split_acquisition",
        "details": "Converted exact avoid concentration stress into split/acquisition/replay requirements.",
        "counts": counts,
        "spec_status_counts": spec_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(BRANCH_SPLIT_LEDGER),
            relative(GROUP_SPLIT_LEDGER),
            relative(ACQUISITION_LEDGER),
            relative(SPEC_SPLIT_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], spec_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Source-Silence Microcluster Exact Avoid Split Acquisition",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: branch-local split/acquisition routing only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Spec Split Status", ""])
    for key, value in sorted(spec_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Materialize source-date/source-axis split packet for concentration-sensitive rows.",
            "- Execute local-depth replay/proxy requirements.",
            "- Search/acquire exact `.depth` source-date rows and broaden source/proxy denominators for target-only rows.",
            "- Continue unrelated challenger-family expansion in parallel.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    branch_rows = read_jsonl(BRANCH_LEDGER)
    group_rows = read_jsonl(GROUP_LEDGER)
    non_exact_rows = read_jsonl(NON_EXACT_LEDGER)
    spec_rows = read_jsonl(SPEC_PLAN_INPUT_LEDGER)
    group_split_rows = build_group_split_rows(group_rows)
    branch_split_rows = build_branch_split_rows(branch_rows, group_split_rows)
    acquisition_rows = build_acquisition_rows(branch_split_rows, group_split_rows, non_exact_rows)
    spec_split_rows = build_spec_split_rows(spec_rows, branch_split_rows, acquisition_rows)
    bucket_rows = build_bucket_rows(group_split_rows, branch_split_rows, acquisition_rows, spec_split_rows)
    question_rows = build_question_rows(branch_split_rows, acquisition_rows, spec_split_rows)
    spec_counts = counter_dict(row.get("split_spec_status") for row in spec_split_rows)
    counts = {
        "branch_input_rows": len(branch_rows),
        "exact_avoid_branch_input_rows": sum(1 for row in branch_rows if row.get("is_exact_descriptive_avoid_branch")),
        "group_stress_input_rows": len(group_rows),
        "non_exact_input_rows": len(non_exact_rows),
        "spec_input_rows": len(spec_rows),
        "group_split_rows": len(group_split_rows),
        "weakening_group_rows": sum(1 for row in group_split_rows if str(row.get("group_split_status")).startswith("GROUP_SPLIT_WEAKENING")),
        "branch_split_rows": len(branch_split_rows),
        "split_acquisition_requirement_rows": len(acquisition_rows),
        "spec_split_rows": len(spec_split_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_exact_avoid_split_acquisition_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPLIT_ACQUISITION_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "group_split_status_counts": counter_dict(row.get("group_split_status") for row in group_split_rows),
        "weakening_axis_counts": counter_dict(row.get("concentration_axis") for row in group_split_rows if str(row.get("group_split_status")).startswith("GROUP_SPLIT_WEAKENING")),
        "branch_split_status_counts": counter_dict(row.get("branch_split_status") for row in branch_split_rows),
        "acquisition_requirement_scope_counts": counter_dict(row.get("requirement_scope") for row in acquisition_rows),
        "acquisition_requirement_status_counts": counter_dict(row.get("status") for row in acquisition_rows),
        "split_spec_status_counts": spec_counts,
        "not_completion": "This split/acquisition packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "materialize source-date/source-axis split packet for concentration-sensitive rows",
            "execute local-depth replay/proxy packet for local-depth non-exact rows",
            "search/acquire exact .depth source-date files for route-C proxy rows",
            "broaden source/proxy denominators for target-only rows and unrelated challenger families",
        ],
    }
    write_jsonl(GROUP_SPLIT_LEDGER, group_split_rows)
    write_jsonl(BRANCH_SPLIT_LEDGER, branch_split_rows)
    write_jsonl(ACQUISITION_LEDGER, acquisition_rows)
    write_jsonl(SPEC_SPLIT_LEDGER, spec_split_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, spec_counts)
    write_summary(generated_utc, counts, spec_counts)
    print(json.dumps({"ok": True, "counts": counts, "spec_counts": spec_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
