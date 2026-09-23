#!/usr/bin/env python3
"""Materialize non-exact local-depth rows into exact/proxy replay requirements."""

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
SOURCE_DATE_ACQ_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_DATE_ACQUISITION_LEDGER_{STAMP}.jsonl"
NON_EXACT_NEXT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_EXACT_AVOID_NON_EXACT_NEXT_ROUTE_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_LOCAL_DEPTH_PROXY_RESULT_{STAMP}.json"
ROUTE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_LOCAL_DEPTH_PROXY_ROUTE_LEDGER_{STAMP}.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_LOCAL_DEPTH_PROXY_MEMBER_LEDGER_{STAMP}.jsonl"
REQUIREMENT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_LOCAL_DEPTH_PROXY_REQUIREMENT_LEDGER_{STAMP}.jsonl"
SPEC_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_LOCAL_DEPTH_PROXY_SPEC_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_LOCAL_DEPTH_PROXY_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_LOCAL_DEPTH_PROXY_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_LOCAL_DEPTH_PROXY_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Branch-local local-depth replay/proxy materialization only; source-control "
    "and repair evidence with no validation, R/PnL, expectancy, live-readiness, "
    "promotion, or live deployment"
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


def rows_matching(rows: list[dict[str, Any]], axis: str, value: str) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get(axis)) == value]


def exact_feature_available(row: dict[str, Any]) -> bool:
    return row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES and not row.get("source_silence_joined")


def local_depth_available(row: dict[str, Any]) -> bool:
    return bool_value(row.get("depth_file_exists")) is True


def row_class(row: dict[str, Any]) -> str:
    if exact_feature_available(row):
        return "LOCAL_DEPTH_MEMBER_EXACT_FEATURE_AVAILABLE"
    if row.get("source_silence_joined"):
        return "LOCAL_DEPTH_MEMBER_SOURCE_SILENCE_CONTEXT"
    if local_depth_available(row):
        return "LOCAL_DEPTH_MEMBER_LOCAL_DEPTH_PRESENT_NEEDS_REPLAY_OR_PROXY"
    return "LOCAL_DEPTH_MEMBER_NO_LOCAL_DEPTH"


def stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    align = [row.get("route_c_delta_aligned_with_future") for row in rows if isinstance(row.get("route_c_delta_aligned_with_future"), bool)]
    return {
        "n": len(rows),
        "unique_request_count": len({str(row.get("request_id")) for row in rows if row.get("request_id")}),
        "alignment_n": len(align),
        "alignment_share": (sum(1 for value in align if value) / len(align)) if align else None,
        "member_class_counts": counter_dict(row_class(row) for row in rows),
        "source_date_counts": counter_dict(row.get("source_date") for row in rows),
        "source_symbol_counts": counter_dict(row.get("source_symbol") for row in rows),
        "source_proxy_family_counts": counter_dict(row.get("source_proxy_family") for row in rows),
        "command_feature_bucket_counts": counter_dict(row.get("command_feature_bucket") for row in rows),
        "horizon_counts": counter_dict(row.get("horizon_id") for row in rows),
        "ladder_join_status_counts": counter_dict(row.get("updated_ladder_join_status") for row in rows),
    }


def classify_route(local_rows: list[dict[str, Any]], exact_rows: list[dict[str, Any]], proxy_rows: list[dict[str, Any]]) -> str:
    if len(exact_rows) >= 20 and len(proxy_rows) >= 5:
        return "LOCAL_DEPTH_PROXY_EXACT_CONTEXT_READY_FOR_BROADER_STRESS"
    if len(local_rows) >= 20 and len(exact_rows) < 20:
        return "LOCAL_DEPTH_PROXY_LOCAL_ROWS_AVAILABLE_EXACT_UNDERPOWERED_REPLAY_REQUIRED"
    if len(local_rows) > 0:
        return "LOCAL_DEPTH_PROXY_LOCAL_ROWS_AVAILABLE_SMALL_DENOMINATOR_EXPAND"
    return "LOCAL_DEPTH_PROXY_NO_LOCAL_ROWS_UNEXPECTED_RECHECK_SOURCE"


def route_action(status: str) -> str:
    if status == "LOCAL_DEPTH_PROXY_EXACT_CONTEXT_READY_FOR_BROADER_STRESS":
        return "stress exact/proxy local-depth context against broader denominators now"
    if status == "LOCAL_DEPTH_PROXY_LOCAL_ROWS_AVAILABLE_EXACT_UNDERPOWERED_REPLAY_REQUIRED":
        return "replay local-depth rows or broaden exact proxy rows now"
    if status == "LOCAL_DEPTH_PROXY_LOCAL_ROWS_AVAILABLE_SMALL_DENOMINATOR_EXPAND":
        return "expand source denominator and proxy rows now"
    return "recheck source join because local-depth route expected local rows"


def build_route_and_member_rows(
    source_join: list[dict[str, Any]],
    proxy_targets: list[dict[str, Any]],
    acquisition_rows: list[dict[str, Any]],
    non_exact_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    non_exact_by_id = {str(row.get("non_exact_next_route_id")): row for row in non_exact_rows}
    non_exact_by_original = {str(row.get("non_exact_route_id")): row for row in non_exact_rows}
    local_acqs = [
        row for row in acquisition_rows
        if row.get("status") == "NON_EXACT_LOCAL_DEPTH_REPLAY_OR_PROXY_NOW"
    ]
    route_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    for acq in local_acqs:
        details = acq.get("details") or {}
        non_exact_id = str(details.get("non_exact_route_id"))
        non_exact = non_exact_by_original.get(non_exact_id) or non_exact_by_id.get(non_exact_id)
        if not non_exact:
            axis = "missing_non_exact_route"
            value = non_exact_id
            matching_rows: list[dict[str, Any]] = []
            proxy_rows: list[dict[str, Any]] = []
        else:
            axis = str(non_exact.get("stress_axis"))
            value = str(non_exact.get("left_out_value"))
            matching_rows = rows_matching(source_join, axis, value)
            proxy_rows = rows_matching(proxy_targets, axis, value)
        local_rows = [row for row in matching_rows if local_depth_available(row)]
        exact_rows = [row for row in local_rows if exact_feature_available(row)]
        source_silence_rows = [row for row in local_rows if row.get("source_silence_joined")]
        needs_replay_rows = [
            row for row in local_rows
            if not exact_feature_available(row) and not row.get("source_silence_joined")
        ]
        status = classify_route(local_rows, exact_rows, proxy_rows)
        route_id = f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-LOCAL-DEPTH-PROXY-ROUTE-{len(route_rows) + 1:05d}"
        route_rows.append(
            {
                "local_depth_proxy_route_id": route_id,
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_date_acquisition_id": acq.get("source_date_acquisition_id"),
                "source_split_acquisition_requirement_id": acq.get("source_split_acquisition_requirement_id"),
                "non_exact_route_id": non_exact_id,
                "dedup_spec_id": acq.get("dedup_spec_id"),
                "stress_axis": axis,
                "left_out_value": value,
                "matching_source_join_rows": len(matching_rows),
                "local_depth_member_rows": len(local_rows),
                "exact_feature_member_rows": len(exact_rows),
                "source_silence_member_rows": len(source_silence_rows),
                "needs_replay_or_proxy_member_rows": len(needs_replay_rows),
                "proxy_target_rows": len(proxy_rows),
                "local_depth_member_stats": stats(local_rows),
                "exact_feature_member_stats": stats(exact_rows),
                "proxy_target_stats": stats(proxy_rows),
                "local_depth_proxy_status": status,
                "next_same_resource_action": route_action(status),
                "not_completion": "Local-depth proxy route is source-control materialization only.",
            }
        )
        for member in local_rows:
            member_rows.append(
                {
                    "local_depth_proxy_member_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-LOCAL-DEPTH-PROXY-MEMBER-{len(member_rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "local_depth_proxy_route_id": route_id,
                    "source_date_acquisition_id": acq.get("source_date_acquisition_id"),
                    "dedup_spec_id": acq.get("dedup_spec_id"),
                    "request_id": member.get("request_id"),
                    "source_date": member.get("source_date"),
                    "source_symbol": member.get("source_symbol"),
                    "source_proxy_family": member.get("source_proxy_family"),
                    "horizon_id": member.get("horizon_id"),
                    "command_feature_bucket": member.get("command_feature_bucket"),
                    "updated_ladder_join_status": member.get("updated_ladder_join_status"),
                    "updated_ladder_snapshot_bucket": member.get("updated_ladder_snapshot_bucket"),
                    "source_silence_joined": member.get("source_silence_joined"),
                    "depth_path": member.get("depth_path"),
                    "member_class": row_class(member),
                    "route_c_delta_aligned_with_future": member.get("route_c_delta_aligned_with_future"),
                    "route_c_future_change_per_current_range": member.get("route_c_future_change_per_current_range"),
                    "not_completion": "Member rows preserve the full local-depth denominator for this route.",
                }
            )
    return route_rows, member_rows


def build_requirement_rows(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for route in route_rows:
        for scope, count in [
            ("exact_feature_members", route.get("exact_feature_member_rows")),
            ("source_silence_members", route.get("source_silence_member_rows")),
            ("needs_replay_or_proxy_members", route.get("needs_replay_or_proxy_member_rows")),
        ]:
            rows.append(
                {
                    "local_depth_proxy_requirement_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-LOCAL-DEPTH-PROXY-REQ-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "local_depth_proxy_route_id": route.get("local_depth_proxy_route_id"),
                    "dedup_spec_id": route.get("dedup_spec_id"),
                    "requirement_scope": scope,
                    "row_count": count,
                    "route_status": route.get("local_depth_proxy_status"),
                    "next_same_resource_action": requirement_action(scope, int(count or 0)),
                    "not_completion": "Requirement rows are immediate replay/proxy work.",
                }
            )
    return rows


def requirement_action(scope: str, count: int) -> str:
    if scope == "needs_replay_or_proxy_members" and count > 0:
        return "replay or proxy these local-depth rows now"
    if scope == "exact_feature_members" and count > 0:
        return "stress exact-feature members against broader controls now"
    if scope == "source_silence_members" and count > 0:
        return "join source-silence member context into broader proxy denominator now"
    return "preserve zero-count requirement and continue nonzero routes"


def build_spec_rows(route_rows: list[dict[str, Any]], requirement_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    routes_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    req_by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in route_rows:
        routes_by_spec[str(row.get("dedup_spec_id"))].append(row)
    for row in requirement_rows:
        req_by_spec[str(row.get("dedup_spec_id"))].append(row)
    rows: list[dict[str, Any]] = []
    for spec_id in sorted(routes_by_spec):
        routes = routes_by_spec[spec_id]
        reqs = req_by_spec.get(spec_id, [])
        status = "SPEC_LOCAL_DEPTH_PROXY_REPLAY_REQUIRED"
        if any(row.get("local_depth_proxy_status") == "LOCAL_DEPTH_PROXY_EXACT_CONTEXT_READY_FOR_BROADER_STRESS" for row in routes):
            status = "SPEC_LOCAL_DEPTH_PROXY_HAS_EXACT_CONTEXT_STRESS_ROUTE"
        rows.append(
            {
                "local_depth_proxy_spec_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-LOCAL-DEPTH-PROXY-SPEC-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "dedup_spec_id": spec_id,
                "local_depth_proxy_route_rows": len(routes),
                "local_depth_proxy_requirement_rows": len(reqs),
                "route_status_counts": counter_dict(row.get("local_depth_proxy_status") for row in routes),
                "requirement_scope_counts": counter_dict(row.get("requirement_scope") for row in reqs),
                "local_depth_proxy_spec_status": status,
                "next_same_resource_action": "execute local-depth replay/proxy requirements and broaden exact controls now",
                "not_completion": "Spec row routes local-depth work only; it is not validation.",
            }
        )
    return rows


def build_bucket_rows(route_rows: list[dict[str, Any]], member_rows: list[dict[str, Any]], requirement_rows: list[dict[str, Any]], spec_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    bucket_sets = [
        ("local_depth_proxy_status", counter_dict(row.get("local_depth_proxy_status") for row in route_rows)),
        ("member_class", counter_dict(row.get("member_class") for row in member_rows)),
        ("member_source_date", counter_dict(row.get("source_date") for row in member_rows)),
        ("member_source_symbol", counter_dict(row.get("source_symbol") for row in member_rows)),
        ("requirement_scope", counter_dict(row.get("requirement_scope") for row in requirement_rows)),
        ("local_depth_proxy_spec_status", counter_dict(row.get("local_depth_proxy_spec_status") for row in spec_rows)),
    ]
    for family, counts in bucket_sets:
        for value, count in counts.items():
            rows.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-LOCAL-DEPTH-PROXY-BUCKET-{len(rows) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": family,
                    "bucket_value": value,
                    "row_count": count,
                    "not_completion": "Bucket row summarizes full ledgers without replacing them.",
                }
            )
    return rows


def build_question_rows(route_rows: list[dict[str, Any]], requirement_rows: list[dict[str, Any]], spec_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in [*route_rows, *requirement_rows, *spec_rows]:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-LOCAL-DEPTH-PROXY-Q-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_row_id": row.get("local_depth_proxy_route_id")
                or row.get("local_depth_proxy_requirement_id")
                or row.get("local_depth_proxy_spec_id"),
                "dedup_spec_id": row.get("dedup_spec_id"),
                "status": row.get("local_depth_proxy_status")
                or row.get("route_status")
                or row.get("local_depth_proxy_spec_status"),
                "question": "What local-depth replay/proxy computation follows from this row now?",
                "next_same_resource_action": row.get("next_same_resource_action"),
                "not_completion": "Question rows generate current work, not future waiting.",
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    artifacts = manifest.setdefault("artifacts", [])
    existing = {artifact.get("path") for artifact in artifacts if isinstance(artifact, dict)}
    for path, description in [
        (Path(__file__).resolve(), "Builder for local-depth replay/proxy materialization."),
        (RESULT_PATH, "Local-depth proxy result JSON."),
        (ROUTE_LEDGER, "Local-depth proxy route ledger."),
        (MEMBER_LEDGER, "Local-depth proxy full member ledger."),
        (REQUIREMENT_LEDGER, "Local-depth proxy requirement ledger."),
        (SPEC_LEDGER, "Local-depth proxy spec ledger."),
        (BUCKET_LEDGER, "Local-depth proxy bucket ledger."),
        (QUESTION_LEDGER, "Local-depth proxy question/action ledger."),
        (SUMMARY_PATH, "Human summary for local-depth proxy packet."),
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
        "event_type": "sierra_depth_ladder_source_silence_microcluster_local_depth_proxy",
        "status": "done",
        "route": "source_silence_microcluster_local_depth_proxy",
        "details": "Materialized non-exact local-depth routes into member/requirement/spec ledgers.",
        "counts": counts,
        "spec_status_counts": spec_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(ROUTE_LEDGER),
            relative(MEMBER_LEDGER),
            relative(REQUIREMENT_LEDGER),
            relative(SPEC_LEDGER),
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
        "# Sierra Source-Silence Microcluster Local-Depth Proxy",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: local-depth replay/proxy materialization only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
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
            "- Replay/proxy local-depth members that lack exact features.",
            "- Stress exact-feature members against broader controls.",
            "- Carry source-silence members into the broader source/proxy denominator.",
            "- Continue exact `.depth` source-date acquisition and broader challenger-family packets.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    proxy_targets = read_jsonl(PROXY_TARGET_LEDGER)
    acquisition_rows = read_jsonl(SOURCE_DATE_ACQ_LEDGER)
    non_exact_rows = read_jsonl(NON_EXACT_NEXT_LEDGER)
    route_rows, member_rows = build_route_and_member_rows(source_join, proxy_targets, acquisition_rows, non_exact_rows)
    requirement_rows = build_requirement_rows(route_rows)
    spec_rows = build_spec_rows(route_rows, requirement_rows)
    bucket_rows = build_bucket_rows(route_rows, member_rows, requirement_rows, spec_rows)
    question_rows = build_question_rows(route_rows, requirement_rows, spec_rows)
    spec_counts = counter_dict(row.get("local_depth_proxy_spec_status") for row in spec_rows)
    counts = {
        "source_join_input_rows": len(source_join),
        "proxy_target_input_rows": len(proxy_targets),
        "source_date_acquisition_input_rows": len(acquisition_rows),
        "non_exact_next_route_input_rows": len(non_exact_rows),
        "local_depth_route_input_rows": sum(1 for row in acquisition_rows if row.get("status") == "NON_EXACT_LOCAL_DEPTH_REPLAY_OR_PROXY_NOW"),
        "local_depth_proxy_route_rows": len(route_rows),
        "local_depth_proxy_member_rows": len(member_rows),
        "local_depth_proxy_requirement_rows": len(requirement_rows),
        "local_depth_proxy_spec_rows": len(spec_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_local_depth_proxy_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_LOCAL_DEPTH_PROXY_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "local_depth_proxy_status_counts": counter_dict(row.get("local_depth_proxy_status") for row in route_rows),
        "member_class_counts": counter_dict(row.get("member_class") for row in member_rows),
        "requirement_scope_counts": counter_dict(row.get("requirement_scope") for row in requirement_rows),
        "spec_status_counts": spec_counts,
        "not_completion": "This local-depth proxy packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "replay/proxy local-depth members that lack exact features",
            "stress exact-feature members against broader controls",
            "continue exact .depth source-date acquisition and target-only broader source expansion",
            "open unrelated challenger-family packets from the explorer map",
        ],
    }
    write_jsonl(ROUTE_LEDGER, route_rows)
    write_jsonl(MEMBER_LEDGER, member_rows)
    write_jsonl(REQUIREMENT_LEDGER, requirement_rows)
    write_jsonl(SPEC_LEDGER, spec_rows)
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
