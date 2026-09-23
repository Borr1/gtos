#!/usr/bin/env python3
"""Materialize source-date weakening splits into current-data acquisition/proxy work."""

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
GROUP_SPLIT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPLIT_GROUP_LEDGER_{STAMP}.jsonl"
BRANCH_SPLIT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPLIT_BRANCH_LEDGER_{STAMP}.jsonl"
SPLIT_ACQ_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_SPLIT_ACQUISITION_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_DATE_MATERIALIZATION_RESULT_{STAMP}.json"
SOURCE_DATE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_DATE_MATERIALIZATION_LEDGER_{STAMP}.jsonl"
DATE_POOL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_DATE_POOL_LEDGER_{STAMP}.jsonl"
DATE_ACQUISITION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_DATE_ACQUISITION_LEDGER_{STAMP}.jsonl"
SPEC_DATE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_DATE_SPEC_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_DATE_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_DATE_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_DATE_MATERIALIZATION_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Branch-local source-date materialization and acquisition routing only; "
    "source-control/repair evidence with no validation, R/PnL, expectancy, "
    "live-readiness, promotion, or live deployment"
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


def counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def exact_feature_rows(source_join: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES
        and not row.get("source_silence_joined")
    ]


def rows_for_date(rows: list[dict[str, Any]], source_date: str) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get("source_date")) == source_date]


def count_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    align = [row.get("route_c_delta_aligned_with_future") for row in rows if isinstance(row.get("route_c_delta_aligned_with_future"), bool)]
    return {
        "n": len(rows),
        "unique_request_count": len({str(row.get("request_id")) for row in rows if row.get("request_id")}),
        "alignment_n": len(align),
        "alignment_share": (sum(1 for value in align if value) / len(align)) if align else None,
        "source_symbol_counts": counter_dict(row.get("source_symbol") for row in rows),
        "source_proxy_family_counts": counter_dict(row.get("source_proxy_family") for row in rows),
        "command_feature_bucket_counts": counter_dict(row.get("command_feature_bucket") for row in rows),
        "horizon_counts": counter_dict(row.get("horizon_id") for row in rows),
        "ladder_join_status_counts": counter_dict(row.get("updated_ladder_join_status") for row in rows),
    }


def classify_date(row: dict[str, Any], proxy_rows: list[dict[str, Any]], exact_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> str:
    target_n = int(row.get("target_group_n") or 0)
    exact_n = len(exact_rows)
    source_n = len(source_rows)
    if target_n < 5:
        return "SOURCE_DATE_WEAKENING_TARGET_UNDERPOWERED_EXPAND_DATE_DENOMINATOR"
    if exact_n < 20 and source_n >= 20:
        return "SOURCE_DATE_WEAKENING_EXACT_UNDERPOWERED_BUT_SOURCE_ROWS_AVAILABLE_REPLAY"
    if exact_n < 20:
        return "SOURCE_DATE_WEAKENING_EXACT_AND_SOURCE_UNDERPOWERED_ACQUIRE_BROADER_PROXY"
    if len(proxy_rows) >= 5:
        return "SOURCE_DATE_WEAKENING_MATERIALIZED_WITH_CURRENT_PROXY_AND_EXACT_CONTEXT"
    return "SOURCE_DATE_WEAKENING_PROXY_TARGET_UNDERPOWERED_ACQUIRE_BROADER_SOURCE"


def acquisition_action(status: str) -> str:
    if status == "SOURCE_DATE_WEAKENING_EXACT_UNDERPOWERED_BUT_SOURCE_ROWS_AVAILABLE_REPLAY":
        return "replay available source-date rows into exact ladder features now"
    if status == "SOURCE_DATE_WEAKENING_EXACT_AND_SOURCE_UNDERPOWERED_ACQUIRE_BROADER_PROXY":
        return "search/acquire broader source-date proxy rows from owned/free/current roots now"
    if status == "SOURCE_DATE_WEAKENING_MATERIALIZED_WITH_CURRENT_PROXY_AND_EXACT_CONTEXT":
        return "preserve as materialized source-date split and stress against broader denominators"
    if status == "SOURCE_DATE_WEAKENING_TARGET_UNDERPOWERED_EXPAND_DATE_DENOMINATOR":
        return "expand date denominator and do not use small-N as a stop"
    return "broaden source/proxy denominator now"


def build_source_date_rows(
    group_split_rows: list[dict[str, Any]],
    proxy_targets: list[dict[str, Any]],
    source_join: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    exact_rows = exact_feature_rows(source_join)
    rows: list[dict[str, Any]] = []
    weakening = [
        row for row in group_split_rows
        if row.get("group_split_status") == "GROUP_SPLIT_WEAKENING_SOURCE_DATE"
    ]
    for row in weakening:
        source_date = str(row.get("concentration_value"))
        proxy_date_rows = rows_for_date(proxy_targets, source_date)
        exact_date_rows = rows_for_date(exact_rows, source_date)
        source_date_rows = rows_for_date(source_join, source_date)
        missing_depth_rows = [r for r in source_date_rows if bool_value(r.get("depth_file_exists")) is False]
        local_depth_rows = [r for r in source_date_rows if bool_value(r.get("depth_file_exists")) is True]
        status = classify_date(row, proxy_date_rows, exact_date_rows, source_date_rows)
        rows.append(
            {
                "source_date_materialization_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-DATE-MAT-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_group_split_id": row.get("group_split_id"),
                "source_group_stress_id": row.get("source_group_stress_id"),
                "exact_split_restress_id": row.get("exact_split_restress_id"),
                "dedup_spec_id": row.get("dedup_spec_id"),
                "source_date": source_date,
                "target_group_n": row.get("target_group_n"),
                "target_group_share": row.get("target_group_share"),
                "target_without_group_n": row.get("target_without_group_n"),
                "exact_without_group_n": row.get("exact_without_group_n"),
                "proxy_target_date_stats": count_rows(proxy_date_rows),
                "exact_feature_date_stats": count_rows(exact_date_rows),
                "source_join_date_stats": count_rows(source_date_rows),
                "local_depth_source_rows": len(local_depth_rows),
                "missing_depth_source_rows": len(missing_depth_rows),
                "source_date_materialization_status": status,
                "next_same_resource_action": acquisition_action(status),
                "not_completion": "Source-date materialization is a source-control split, not validation or completion.",
            }
        )
    return rows


def build_date_pool_rows(
    source_join: list[dict[str, Any]],
    proxy_targets: list[dict[str, Any]],
    materialization_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    exact_rows = exact_feature_rows(source_join)
    weakening_dates = {str(row.get("source_date")) for row in materialization_rows}
    all_dates = sorted({str(row.get("source_date")) for row in source_join if row.get("source_date")})
    rows: list[dict[str, Any]] = []
    for source_date in all_dates:
        source_date_rows = rows_for_date(source_join, source_date)
        exact_date_rows = rows_for_date(exact_rows, source_date)
        proxy_date_rows = rows_for_date(proxy_targets, source_date)
        rows.append(
            {
                "source_date_pool_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-DATE-POOL-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_date": source_date,
                "is_weakening_source_date": source_date in weakening_dates,
                "source_join_date_stats": count_rows(source_date_rows),
                "exact_feature_date_stats": count_rows(exact_date_rows),
                "proxy_target_date_stats": count_rows(proxy_date_rows),
                "depth_file_exists_counts": counter_dict(row.get("depth_file_exists") for row in source_date_rows),
                "source_symbols": sorted({str(row.get("source_symbol")) for row in source_date_rows if row.get("source_symbol")}),
                "not_completion": "Date pool row preserves the full source-date denominator.",
            }
        )
    return rows


def build_acquisition_rows(
    materialization_rows: list[dict[str, Any]],
    split_acq_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in materialization_rows:
        rows.append(
            {
                "source_date_acquisition_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-DATE-ACQ-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "requirement_scope": "weakening_source_date_materialization",
                "source_date_materialization_id": row.get("source_date_materialization_id"),
                "dedup_spec_id": row.get("dedup_spec_id"),
                "source_date": row.get("source_date"),
                "status": row.get("source_date_materialization_status"),
                "next_same_resource_action": row.get("next_same_resource_action"),
                "not_completion": "Source-date acquisition row is immediate work, not a wait label.",
            }
        )
    for row in split_acq_rows:
        status = str(row.get("status"))
        if status in {
            "NON_EXACT_LOCAL_DEPTH_REPLAY_OR_PROXY_NOW",
            "NON_EXACT_ROUTE_C_PROXY_EXACT_DEPTH_SOURCE_DATE_ACQUISITION",
            "NON_EXACT_TARGET_ONLY_BROADER_SOURCE_ACQUISITION",
        }:
            rows.append(
                {
                    "source_date_acquisition_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-DATE-ACQ-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "requirement_scope": "carried_non_exact_route",
                    "source_split_acquisition_requirement_id": row.get("split_acquisition_requirement_id"),
                    "dedup_spec_id": row.get("dedup_spec_id"),
                    "source_date": None,
                    "status": status,
                    "next_same_resource_action": row.get("next_same_resource_action"),
                    "details": row.get("details"),
                    "not_completion": "Carried non-exact route must be pursued inside the goal.",
                }
            )
    return rows


def build_spec_rows(materialization_rows: list[dict[str, Any]], acquisition_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mat_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    acq_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in materialization_rows:
        mat_by_spec[str(row.get("dedup_spec_id"))].append(row)
    for row in acquisition_rows:
        acq_by_spec[str(row.get("dedup_spec_id"))].append(row)
    spec_ids = sorted(set(mat_by_spec) | set(acq_by_spec))
    rows: list[dict[str, Any]] = []
    for spec_id in spec_ids:
        mat_rows = mat_by_spec.get(spec_id, [])
        acq_rows = acq_by_spec.get(spec_id, [])
        mat_counts = counter_dict(row.get("source_date_materialization_status") for row in mat_rows)
        acq_counts = counter_dict(row.get("status") for row in acq_rows)
        status = "SPEC_SOURCE_DATE_HAS_WEAKENING_MATERIALIZATION"
        if not mat_rows:
            status = "SPEC_SOURCE_DATE_ONLY_CARRIED_NON_EXACT_ACQUISITION"
        rows.append(
            {
                "source_date_spec_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-DATE-SPEC-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "dedup_spec_id": spec_id,
                "source_date_materialization_rows": len(mat_rows),
                "source_date_acquisition_rows": len(acq_rows),
                "materialization_status_counts": mat_counts,
                "acquisition_status_counts": acq_counts,
                "source_date_spec_status": status,
                "next_same_resource_action": "execute date/source acquisition and local-depth replay requirements now",
                "not_completion": "Spec row routes current work and does not imply validation.",
            }
        )
    return rows


def build_bucket_rows(
    materialization_rows: list[dict[str, Any]],
    date_pool_rows: list[dict[str, Any]],
    acquisition_rows: list[dict[str, Any]],
    spec_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    bucket_sets = [
        ("source_date_materialization_status", counter_dict(row.get("source_date_materialization_status") for row in materialization_rows)),
        ("weakening_source_date", counter_dict(row.get("source_date") for row in materialization_rows)),
        ("date_pool_is_weakening", counter_dict(row.get("is_weakening_source_date") for row in date_pool_rows)),
        ("source_date_acquisition_scope", counter_dict(row.get("requirement_scope") for row in acquisition_rows)),
        ("source_date_acquisition_status", counter_dict(row.get("status") for row in acquisition_rows)),
        ("source_date_spec_status", counter_dict(row.get("source_date_spec_status") for row in spec_rows)),
    ]
    for family, counts in bucket_sets:
        for value, count in counts.items():
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-DATE-BUCKET-{len(rows) + 1:05d}",
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
    materialization_rows: list[dict[str, Any]],
    acquisition_rows: list[dict[str, Any]],
    spec_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in [*materialization_rows, *acquisition_rows, *spec_rows]:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-SOURCE-DATE-Q-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_row_id": row.get("source_date_materialization_id")
                or row.get("source_date_acquisition_id")
                or row.get("source_date_spec_id"),
                "dedup_spec_id": row.get("dedup_spec_id"),
                "status": row.get("source_date_materialization_status")
                or row.get("status")
                or row.get("source_date_spec_status"),
                "question": "Which same-resource source-date acquisition/replay/proxy computation follows now?",
                "next_same_resource_action": row.get("next_same_resource_action"),
                "not_completion": "Question rows generate immediate work; they are not future-work notes.",
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    artifacts = manifest.setdefault("artifacts", [])
    existing = {artifact.get("path") for artifact in artifacts if isinstance(artifact, dict)}
    for path, description in [
        (Path(__file__).resolve(), "Builder for source-date materialization/acquisition."),
        (RESULT_PATH, "Source-date materialization result JSON."),
        (SOURCE_DATE_LEDGER, "Source-date weakening materialization ledger."),
        (DATE_POOL_LEDGER, "Full source-date pool denominator ledger."),
        (DATE_ACQUISITION_LEDGER, "Source-date acquisition/replay requirement ledger."),
        (SPEC_DATE_LEDGER, "Source-date spec routing ledger."),
        (BUCKET_LEDGER, "Source-date bucket ledger."),
        (QUESTION_LEDGER, "Source-date question/action ledger."),
        (SUMMARY_PATH, "Human summary for source-date materialization packet."),
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
        "event_type": "sierra_depth_ladder_source_silence_microcluster_source_date_materialization",
        "status": "done",
        "route": "source_silence_microcluster_source_date_materialization",
        "details": "Materialized source-date weakening splits and carried non-exact acquisition routes.",
        "counts": counts,
        "spec_status_counts": spec_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(SOURCE_DATE_LEDGER),
            relative(DATE_POOL_LEDGER),
            relative(DATE_ACQUISITION_LEDGER),
            relative(SPEC_DATE_LEDGER),
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
        "# Sierra Source-Silence Microcluster Source-Date Materialization",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: source-date materialization/acquisition routing only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Spec Status", ""])
    for key, value in sorted(spec_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Execute local-depth replay/proxy for carried non-exact local-depth rows.",
            "- Search/acquire exact `.depth` source-date files for carried route-C proxy rows.",
            "- Broaden source/proxy denominators for target-only and source-underpowered rows.",
            "- Carry source-date materialized rows into the next split/proxy packet without waiting.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    proxy_targets = read_jsonl(PROXY_TARGET_LEDGER)
    group_split_rows = read_jsonl(GROUP_SPLIT_LEDGER)
    split_acq_rows = read_jsonl(SPLIT_ACQ_LEDGER)
    materialization_rows = build_source_date_rows(group_split_rows, proxy_targets, source_join)
    date_pool_rows = build_date_pool_rows(source_join, proxy_targets, materialization_rows)
    acquisition_rows = build_acquisition_rows(materialization_rows, split_acq_rows)
    spec_rows = build_spec_rows(materialization_rows, acquisition_rows)
    bucket_rows = build_bucket_rows(materialization_rows, date_pool_rows, acquisition_rows, spec_rows)
    question_rows = build_question_rows(materialization_rows, acquisition_rows, spec_rows)
    spec_counts = counter_dict(row.get("source_date_spec_status") for row in spec_rows)
    counts = {
        "source_join_input_rows": len(source_join),
        "proxy_target_input_rows": len(proxy_targets),
        "exact_feature_control_rows": len(exact_feature_rows(source_join)),
        "group_split_input_rows": len(group_split_rows),
        "split_acquisition_input_rows": len(split_acq_rows),
        "weakening_source_date_input_rows": sum(1 for row in group_split_rows if row.get("group_split_status") == "GROUP_SPLIT_WEAKENING_SOURCE_DATE"),
        "source_date_materialization_rows": len(materialization_rows),
        "source_date_pool_rows": len(date_pool_rows),
        "source_date_acquisition_rows": len(acquisition_rows),
        "source_date_spec_rows": len(spec_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_source_date_materialization_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_SOURCE_DATE_MATERIALIZATION_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "source_date_materialization_status_counts": counter_dict(row.get("source_date_materialization_status") for row in materialization_rows),
        "weakening_source_date_counts": counter_dict(row.get("source_date") for row in materialization_rows),
        "source_date_acquisition_scope_counts": counter_dict(row.get("requirement_scope") for row in acquisition_rows),
        "source_date_acquisition_status_counts": counter_dict(row.get("status") for row in acquisition_rows),
        "source_date_spec_status_counts": spec_counts,
        "not_completion": "This source-date materialization packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "execute local-depth replay/proxy for local-depth non-exact rows",
            "search/acquire exact .depth source-date files for route-C proxy rows",
            "broaden source/proxy denominators for target-only and underpowered rows",
            "open unrelated challenger-family routes from the explorer map",
        ],
    }
    write_jsonl(SOURCE_DATE_LEDGER, materialization_rows)
    write_jsonl(DATE_POOL_LEDGER, date_pool_rows)
    write_jsonl(DATE_ACQUISITION_LEDGER, acquisition_rows)
    write_jsonl(SPEC_DATE_LEDGER, spec_rows)
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
