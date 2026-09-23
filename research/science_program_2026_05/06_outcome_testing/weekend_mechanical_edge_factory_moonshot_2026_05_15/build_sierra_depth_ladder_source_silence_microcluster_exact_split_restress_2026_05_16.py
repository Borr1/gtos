#!/usr/bin/env python3
"""Rerun exact-feature split restress for fragile microcluster acquisition rows."""

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
ACQUISITION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_FRAGILE_STRESS_ACQUISITION_LEDGER_{STAMP}.jsonl"
SPEC_PLAN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_FRAGILE_STRESS_SPEC_PLAN_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_SPLIT_RESTRESS_RESULT_{STAMP}.json"
EXACT_RESTRESS_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_SPLIT_RESTRESS_LEDGER_{STAMP}.jsonl"
NON_EXACT_ROUTE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_SPLIT_NON_EXACT_ROUTE_LEDGER_{STAMP}.jsonl"
SPEC_EXACT_PLAN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_SPLIT_SPEC_PLAN_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_SPLIT_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_SPLIT_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_SPLIT_RESTRESS_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Branch-local exact split restress only; source-control/repair evidence with "
    "no strategy validation, trade outcome, R/PnL, expectancy, live-readiness, "
    "promotion, or live deployment"
)

EXACT_FEATURE_STATUSES = {
    "LADDER_FEATURE_JOINED",
    "LADDER_FEATURE_JOINED_AFTER_IN_WINDOW_CLEAR_REPAIR",
    "LADDER_FEATURE_AND_BLOCKER_BUCKET_JOINED",
}

EXACT_READY_STATUS = "CURRENT_EXACT_FEATURE_PROXY_ROWS_AVAILABLE_RESTRESS_NOW"


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
        "command_feature_bucket_counts": counter_dict(row.get("command_feature_bucket") for row in rows),
        "horizon_counts": counter_dict(row.get("horizon_id") for row in rows),
    }


def rows_matching(rows: list[dict[str, Any]], axis: str, value: str) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get(axis)) == value]


def verdict_vs_exact(target_stats: dict[str, Any], exact_stats: dict[str, Any]) -> str:
    target_n = int(target_stats.get("n") or 0)
    exact_n = int(exact_stats.get("n") or 0)
    target_align = target_stats.get("route_alignment_share")
    exact_align = exact_stats.get("route_alignment_share")
    if target_n < 5:
        sample_prefix = "EXACT_SPLIT_TARGET_UNDERPOWERED_N_LT_5"
    elif target_n < 20:
        sample_prefix = "EXACT_SPLIT_TARGET_UNDERPOWERED_N_LT_20"
    else:
        sample_prefix = "EXACT_SPLIT_TARGET_N_OK"
    if exact_n < 5:
        return f"{sample_prefix}_EXACT_CONTROL_UNDERPOWERED_N_LT_5"
    if exact_n < 20:
        return f"{sample_prefix}_EXACT_CONTROL_UNDERPOWERED_N_LT_20"
    if target_align is None or exact_align is None:
        return f"{sample_prefix}_DESCRIPTIVE_NO_ALIGNMENT"
    if target_align < exact_align - 0.15:
        return f"{sample_prefix}_AVOID_DIRECTION_VS_EXACT"
    if target_align > exact_align + 0.15:
        return f"{sample_prefix}_TARGET_ALIGNED_VS_EXACT"
    return f"{sample_prefix}_NEAR_EXACT"


def build_exact_restress_rows(acquisition_rows: list[dict[str, Any]], source_join: list[dict[str, Any]], proxy_targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    exact_rows = [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES and not row.get("source_silence_joined")
    ]
    rows: list[dict[str, Any]] = []
    for acquisition in acquisition_rows:
        if acquisition.get("acquisition_status") != EXACT_READY_STATUS:
            continue
        axis = str(acquisition["stress_axis"])
        value = str(acquisition["left_out_value"])
        targets = rows_matching(proxy_targets, axis, value)
        exact_controls = rows_matching(exact_rows, axis, value)
        target_stats = row_stats(targets)
        exact_stats = row_stats(exact_controls)
        status = verdict_vs_exact(target_stats, exact_stats)
        rows.append(
            {
                "exact_split_restress_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-SPLIT-RESTRESS-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_acquisition_requirement_id": acquisition.get("acquisition_requirement_id"),
                "fragile_stress_split_id": acquisition.get("fragile_stress_split_id"),
                "dedup_spec_id": acquisition.get("dedup_spec_id"),
                "stress_axis": axis,
                "left_out_value": value,
                "target_rows": target_stats,
                "exact_feature_rows": exact_stats,
                "target_alignment_delta_vs_exact": numeric_delta(
                    target_stats.get("route_alignment_share"),
                    exact_stats.get("route_alignment_share"),
                ),
                "exact_split_restress_status": status,
                "next_same_resource_action": next_action_for_exact_status(status),
            }
        )
    return rows


def next_action_for_exact_status(status: str) -> str:
    if "AVOID_DIRECTION_VS_EXACT" in status:
        return "preserve as exact descriptive avoid branch and run concentration/source-date stress"
    if "TARGET_ALIGNED_VS_EXACT" in status:
        return "preserve as inverse/failure branch and test alternate horizons"
    if "UNDERPOWERED" in status:
        return "route to local-depth replay/proxy or source acquisition; do not wait"
    return "preserve as near-control/weak branch and continue stronger routes"


def build_non_exact_rows(acquisition_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for acquisition in acquisition_rows:
        if acquisition.get("acquisition_status") == EXACT_READY_STATUS:
            continue
        rows.append(
            {
                "non_exact_route_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-SPLIT-NON-EXACT-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_acquisition_requirement_id": acquisition.get("acquisition_requirement_id"),
                "fragile_stress_split_id": acquisition.get("fragile_stress_split_id"),
                "dedup_spec_id": acquisition.get("dedup_spec_id"),
                "stress_axis": acquisition.get("stress_axis"),
                "left_out_value": acquisition.get("left_out_value"),
                "acquisition_status": acquisition.get("acquisition_status"),
                "current_exact_feature_rows": acquisition.get("current_exact_feature_rows"),
                "current_local_depth_rows": acquisition.get("current_local_depth_rows"),
                "current_source_join_rows": acquisition.get("current_source_join_rows"),
                "current_target_proxy_rows": acquisition.get("current_target_proxy_rows"),
                "next_same_resource_action": acquisition.get("next_same_resource_action"),
            }
        )
    return rows


def build_spec_plan_rows(spec_plans: list[dict[str, Any]], restress_rows: list[dict[str, Any]], non_exact_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    restress_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    non_exact_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in restress_rows:
        restress_by_spec[str(row["dedup_spec_id"])].append(row)
    for row in non_exact_rows:
        non_exact_by_spec[str(row["dedup_spec_id"])].append(row)
    rows: list[dict[str, Any]] = []
    for plan in spec_plans:
        spec_id = str(plan["dedup_spec_id"])
        restress = restress_by_spec[spec_id]
        non_exact = non_exact_by_spec[spec_id]
        status_counts = counter_dict(row.get("exact_split_restress_status") for row in restress)
        avoid_count = sum(count for status, count in status_counts.items() if "AVOID_DIRECTION_VS_EXACT" in status)
        if avoid_count:
            status = "SPEC_EXACT_SPLIT_HAS_DESCRIPTIVE_AVOID_BRANCH"
        elif restress:
            status = "SPEC_EXACT_SPLIT_NO_AVOID_BRANCH_AFTER_RESTRESS"
        else:
            status = "SPEC_EXACT_SPLIT_NO_EXACT_READY_ROWS"
        rows.append(
            {
                "spec_exact_plan_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-SPLIT-SPEC-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "dedup_spec_id": spec_id,
                "prior_fragile_split_plan_status": plan.get("spec_fragile_split_plan_status"),
                "exact_restress_rows": len(restress),
                "non_exact_route_rows": len(non_exact),
                "exact_split_restress_status_counts": status_counts,
                "spec_exact_split_status": status,
                "next_same_resource_action": next_action_for_spec_exact_status(status),
            }
        )
    return rows


def next_action_for_spec_exact_status(status: str) -> str:
    if status == "SPEC_EXACT_SPLIT_HAS_DESCRIPTIVE_AVOID_BRANCH":
        return "run concentration/source-date stress and source-acquisition check before any implementation candidate"
    if status == "SPEC_EXACT_SPLIT_NO_AVOID_BRANCH_AFTER_RESTRESS":
        return "preserve failure intelligence and route non-exact rows to local-depth/source acquisition"
    return "run local-depth replay/proxy or exact source acquisition now"


def build_bucket_rows(restress_rows: list[dict[str, Any]], non_exact_rows: list[dict[str, Any]], spec_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets = [
        ("exact_split_restress_status", counter_dict(row.get("exact_split_restress_status") for row in restress_rows)),
        ("exact_stress_axis", counter_dict(row.get("stress_axis") for row in restress_rows)),
        ("non_exact_acquisition_status", counter_dict(row.get("acquisition_status") for row in non_exact_rows)),
        ("spec_exact_split_status", counter_dict(row.get("spec_exact_split_status") for row in spec_rows)),
    ]
    rows: list[dict[str, Any]] = []
    for family, counts in buckets:
        for bucket, count in counts.items():
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-SPLIT-BUCKET-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": family,
                    "bucket": bucket,
                    "row_count": count,
                }
            )
    return rows


def build_question_rows(restress_rows: list[dict[str, Any]], non_exact_rows: list[dict[str, Any]], spec_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in spec_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-SPLIT-Q-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "spec_exact_split_next_action",
                "dedup_spec_id": spec.get("dedup_spec_id"),
                "status": spec.get("spec_exact_split_status"),
                "question": "Does exact split restress leave a branch worth concentration/source-date stress?",
                "next_action": spec.get("next_same_resource_action"),
            }
        )
    for restress in restress_rows:
        if "AVOID_DIRECTION_VS_EXACT" in str(restress.get("exact_split_restress_status")):
            rows.append(
                {
                    "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-SPLIT-Q-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "question_family": "exact_avoid_branch_stress",
                    "dedup_spec_id": restress.get("dedup_spec_id"),
                    "stress_axis": restress.get("stress_axis"),
                    "left_out_value": restress.get("left_out_value"),
                    "question": "Does this exact avoid split survive concentration, date, source-symbol, and command stress?",
                    "next_action": restress.get("next_same_resource_action"),
                }
            )
    for row in non_exact_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-EXACT-SPLIT-Q-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "non_exact_split_route",
                "dedup_spec_id": row.get("dedup_spec_id"),
                "stress_axis": row.get("stress_axis"),
                "left_out_value": row.get("left_out_value"),
                "question": "Which local-depth replay, source acquisition, or proxy route repairs this non-exact split?",
                "next_action": row.get("next_same_resource_action"),
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_microcluster_exact_split_restress_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_microcluster_exact_split_restress_result", "created"),
        (EXACT_RESTRESS_LEDGER, "sierra_depth_ladder_source_silence_microcluster_exact_split_restress_ledger", "created"),
        (NON_EXACT_ROUTE_LEDGER, "sierra_depth_ladder_source_silence_microcluster_exact_split_non_exact_route_ledger", "created"),
        (SPEC_EXACT_PLAN_LEDGER, "sierra_depth_ladder_source_silence_microcluster_exact_split_spec_plan_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_exact_split_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_exact_split_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_microcluster_exact_split_restress_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], spec_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_microcluster_exact_split_restress",
        "status": "done",
        "route": "source_silence_microcluster_exact_split_restress",
        "details": "Reran exact-feature split restress for all exact-ready fragile-stress acquisition rows.",
        "counts": counts,
        "spec_exact_split_status_counts": spec_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(EXACT_RESTRESS_LEDGER),
            relative(NON_EXACT_ROUTE_LEDGER),
            relative(SPEC_EXACT_PLAN_LEDGER),
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
        "# Sierra Source-Silence Microcluster Exact Split Restress",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: branch-local exact split restress only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Spec Exact Split Status", ""])
    for key, value in sorted(spec_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Run concentration/source-date stress on exact descriptive avoid branches.",
            "- Route non-exact rows to local-depth replay/proxy and exact source acquisition.",
            "- Keep every result as source-control evidence only until a separate promotion dossier exists.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    proxy_targets = read_jsonl(PROXY_TARGET_LEDGER)
    acquisition_rows = read_jsonl(ACQUISITION_LEDGER)
    spec_plans = read_jsonl(SPEC_PLAN_LEDGER)
    exact_restress_rows = build_exact_restress_rows(acquisition_rows, source_join, proxy_targets)
    non_exact_rows = build_non_exact_rows(acquisition_rows)
    spec_exact_rows = build_spec_plan_rows(spec_plans, exact_restress_rows, non_exact_rows)
    bucket_rows = build_bucket_rows(exact_restress_rows, non_exact_rows, spec_exact_rows)
    question_rows = build_question_rows(exact_restress_rows, non_exact_rows, spec_exact_rows)
    spec_counts = counter_dict(row.get("spec_exact_split_status") for row in spec_exact_rows)
    counts = {
        "source_join_input_rows": len(source_join),
        "proxy_target_input_rows": len(proxy_targets),
        "acquisition_input_rows": len(acquisition_rows),
        "spec_plan_input_rows": len(spec_plans),
        "exact_ready_acquisition_rows": sum(1 for row in acquisition_rows if row.get("acquisition_status") == EXACT_READY_STATUS),
        "exact_split_restress_rows": len(exact_restress_rows),
        "non_exact_route_rows": len(non_exact_rows),
        "spec_exact_plan_rows": len(spec_exact_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_exact_split_restress_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_EXACT_SPLIT_RESTRESS_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "exact_split_restress_status_counts": counter_dict(row.get("exact_split_restress_status") for row in exact_restress_rows),
        "exact_stress_axis_counts": counter_dict(row.get("stress_axis") for row in exact_restress_rows),
        "non_exact_acquisition_status_counts": counter_dict(row.get("acquisition_status") for row in non_exact_rows),
        "spec_exact_split_status_counts": spec_counts,
        "not_completion": "This exact split restress packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "run concentration/source-date stress on exact descriptive avoid branches",
            "build local-depth replay/proxy packet for non-exact local-depth rows",
            "continue exact .depth source-date acquisition and unrelated challenger expansion",
        ],
    }
    write_jsonl(EXACT_RESTRESS_LEDGER, exact_restress_rows)
    write_jsonl(NON_EXACT_ROUTE_LEDGER, non_exact_rows)
    write_jsonl(SPEC_EXACT_PLAN_LEDGER, spec_exact_rows)
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
