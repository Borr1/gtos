#!/usr/bin/env python3
"""Update ladder source/capture requirements after no-event fallback proof."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

REQUIREMENT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REQUIREMENT_LEDGER_{STAMP}.jsonl"
FALLBACK_FEATURE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_FALLBACK_FEATURE_LEDGER_{STAMP}.jsonl"
NEIGHBOR_TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_NO_EVENT_NEIGHBOR_TARGET_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REQUIREMENT_AFTER_FALLBACK_RESULT_{STAMP}.json"
UPDATED_REQUIREMENT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REQUIREMENT_AFTER_FALLBACK_LEDGER_{STAMP}.jsonl"
EVENT_RESOLUTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_EVENT_WINDOW_AFTER_FALLBACK_LEDGER_{STAMP}.jsonl"
GROUP_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REQUIREMENT_AFTER_FALLBACK_GROUP_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REQUIREMENT_AFTER_FALLBACK_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REQUIREMENT_AFTER_FALLBACK_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra .depth ladder source/capture requirement update after record-level "
    "no-event proof and same-source neighbor controls; no strategy validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or promotion"
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def fallback_resolution_status(fallback: dict[str, Any] | None, neighbor: dict[str, Any] | None) -> str:
    if fallback is None:
        return "EVENT_WINDOW_REQUIREMENT_NO_FALLBACK_ROW"
    if fallback.get("fallback_ladder_snapshot_bucket") != "FALLBACK_RECORD_LEVEL_NO_EVENT_SAMPLES":
        return "EVENT_WINDOW_BOUNDARY60_RECORD_LEVEL_REPAIRED"
    proxy_bucket = str(fallback.get("fallback_event15_proxy_bucket"))
    control_bucket = str((neighbor or {}).get("target_neighbor_control_bucket"))
    if proxy_bucket == "FALLBACK_RECORD_LEVEL_EVENT15_NO_SAMPLES":
        return "BOUNDARY60_TRUE_EMPTY_AND_EVENT15_EMPTY_SOURCE_GAP_REMAINS"
    if proxy_bucket.endswith("MISSING"):
        return "BOUNDARY60_TRUE_EMPTY_EVENT15_BOOK_IMBALANCE_MISSING"
    if control_bucket == "SAME_SOURCE_NEIGHBOR_ALIGNMENT_WEAKENING_CONTEXT":
        return "BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_NEIGHBOR_WEAKENED"
    if control_bucket == "UNDERPOWERED_TARGET_NEIGHBOR_N_LT_20":
        return "BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_UNDERPOWERED_NEIGHBOR"
    return "BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_DESCRIPTOR_AVAILABLE"


def next_action(status: str) -> str:
    if status == "BOUNDARY60_TRUE_EMPTY_AND_EVENT15_EMPTY_SOURCE_GAP_REMAINS":
        return "preserve exact boundary60/event15 no-sample source-capture requirement; search earlier or alternate source if available"
    if status == "BOUNDARY60_TRUE_EMPTY_EVENT15_BOOK_IMBALANCE_MISSING":
        return "inspect book completeness/top-depth construction before using full-M15 proxy"
    if status == "BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_NEIGHBOR_WEAKENED":
        return "treat as weakening/avoid descriptor candidate and split by source-date and route primitive"
    if status == "BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_UNDERPOWERED_NEIGHBOR":
        return "retain proxy descriptor but require more same-source context before stronger interpretation"
    if status == "BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_DESCRIPTOR_AVAILABLE":
        return "carry full-M15 proxy as descriptor-only context into imbalanced/fallback split work"
    if status == "EVENT_WINDOW_BOUNDARY60_RECORD_LEVEL_REPAIRED":
        return "carry exact boundary60 descriptor into controls"
    return "manual requirement review required"


def build_updated_rows(
    requirements: list[dict[str, Any]],
    fallback_by_request: dict[str, dict[str, Any]],
    neighbor_by_request: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    updated: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []
    for row in requirements:
        out = dict(row)
        out["safe_flags"] = SAFE_FLAGS
        out["evidence_boundary"] = EVIDENCE_BOUNDARY
        out["post_fallback_update_scope"] = "unchanged_requirement"
        out["post_fallback_requirement_status"] = row.get("requirement_status")
        out["post_fallback_next_same_resource_action"] = row.get("next_same_resource_action")
        if row.get("requirement_type") == "EVENT_WINDOW_DEPTH_SAMPLE_ALIGNMENT_REQUIREMENT":
            request_id = str(row.get("request_id"))
            fallback = fallback_by_request.get(request_id)
            neighbor = neighbor_by_request.get(request_id)
            status = fallback_resolution_status(fallback, neighbor)
            out.update(
                {
                    "post_fallback_update_scope": "event_window_requirement_refined",
                    "post_fallback_requirement_status": status,
                    "post_fallback_next_same_resource_action": next_action(status),
                    "fallback_ladder_snapshot_bucket": (fallback or {}).get("fallback_ladder_snapshot_bucket"),
                    "fallback_event15_proxy_bucket": (fallback or {}).get("fallback_event15_proxy_bucket"),
                    "fallback_event15_record_count": (fallback or {}).get("fallback_event15_record_count"),
                    "fallback_event15_imbalance_sign": (fallback or {}).get("fallback_event15_imbalance_sign"),
                    "fallback_event15_median_depth10_imbalance": (fallback or {}).get("fallback_event15_record_median_depth10_imbalance"),
                    "fallback_event15_median_total_depth10": (fallback or {}).get("fallback_event15_record_median_total_depth10"),
                    "neighbor_control_bucket": (neighbor or {}).get("target_neighbor_control_bucket"),
                    "neighbor_pair_rows": (neighbor or {}).get("neighbor_pair_rows"),
                    "same_route_alignment_share": (neighbor or {}).get("same_route_alignment_share"),
                    "proxy_neighbor_relation_counts": (neighbor or {}).get("proxy_neighbor_relation_counts"),
                }
            )
            event = {
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "requirement_id": row.get("requirement_id"),
                "request_id": request_id,
                "source_symbol": row.get("source_symbol"),
                "source_date": row.get("source_date"),
                "route_c_queue_id": row.get("route_c_queue_id"),
                "route_c_symbol": row.get("route_c_symbol"),
                "route_c_primitive_flag": row.get("route_c_primitive_flag"),
                "route_c_full_control_bucket": row.get("route_c_full_control_bucket"),
                "original_requirement_status": row.get("requirement_status"),
                "post_fallback_requirement_status": status,
                "post_fallback_next_same_resource_action": next_action(status),
                "fallback_event15_proxy_bucket": (fallback or {}).get("fallback_event15_proxy_bucket"),
                "neighbor_control_bucket": (neighbor or {}).get("target_neighbor_control_bucket"),
                "neighbor_pair_rows": (neighbor or {}).get("neighbor_pair_rows"),
            }
            event_rows.append(event)
        updated.append(out)
    return updated, event_rows


def build_group_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: Counter[tuple[str, str, str, str | None]] = Counter()
    for row in rows:
        grouped[
            (
                str(row.get("requirement_type")),
                str(row.get("post_fallback_requirement_status")),
                str(row.get("fallback_event15_proxy_bucket")),
                str(row.get("neighbor_control_bucket")),
            )
        ] += 1
    out: list[dict[str, Any]] = []
    for ordinal, (key, count) in enumerate(sorted(grouped.items()), start=1):
        requirement_type, status, proxy_bucket, neighbor_bucket = key
        out.append(
            {
                "group_id": f"SIERRA-DEPTH-LADDER-REQ-AFTER-FALLBACK-GROUP-{ordinal:04d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "requirement_type": requirement_type,
                "post_fallback_requirement_status": status,
                "fallback_event15_proxy_bucket": proxy_bucket,
                "neighbor_control_bucket": neighbor_bucket,
                "row_count": count,
            }
        )
    return out


def build_question_rows(event_rows: list[dict[str, Any]], group_rows: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    status_counts = Counter(str(row.get("post_fallback_requirement_status")) for row in event_rows)
    for status, count in sorted(status_counts.items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-REQ-AFTER-FALLBACK-Q-{len(rows) + 1:03d}",
                "question_family": "event_window_refined_status",
                "bucket": status,
                "row_count": count,
                "question": f"What exact same-resource closure follows for all {count} event-window requirements now classified as {status}?",
                "next_same_resource_action": next_action(status),
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    non_event_groups = [
        row for row in group_rows
        if row.get("requirement_type") != "EVENT_WINDOW_DEPTH_SAMPLE_ALIGNMENT_REQUIREMENT"
    ]
    rows.append(
        {
            "question_id": f"SIERRA-DEPTH-LADDER-REQ-AFTER-FALLBACK-Q-{len(rows) + 1:03d}",
            "question_family": "remaining_requirement_denominator",
            "bucket": "NON_EVENT_WINDOW_REQUIREMENTS_UNCHANGED",
            "row_count": sum(int(row.get("row_count") or 0) for row in non_event_groups),
            "question": "Which remaining non-event requirements can still be repaired from owned/current/free source routes?",
            "next_same_resource_action": "continue exact missing .depth source-date acquisition and earlier-book-history repair/proxy search",
            "counts_context": counts,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
    )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_requirement_after_fallback_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_requirement_after_fallback_result", "created"),
        (UPDATED_REQUIREMENT_LEDGER, "sierra_depth_ladder_requirement_after_fallback_ledger", "created"),
        (EVENT_RESOLUTION_LEDGER, "sierra_depth_ladder_event_window_after_fallback_ledger", "created"),
        (GROUP_LEDGER, "sierra_depth_ladder_requirement_after_fallback_group_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_requirement_after_fallback_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_requirement_after_fallback_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], status_counts: Counter[str]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_requirement_after_fallback_update",
        "status": "done",
        "route": "sierra_depth_ladder_requirement_refinement",
        "details": "Preserved all ladder requirements and refined the 26 event-window requirements with record-level boundary proof, full-M15 proxy buckets, and neighbor controls.",
        "counts": counts,
        "event_window_refined_status_counts": dict(sorted(status_counts.items())),
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(UPDATED_REQUIREMENT_LEDGER),
            relative(EVENT_RESOLUTION_LEDGER),
            relative(GROUP_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], status_counts: Counter[str]) -> None:
    lines = [
        "# Sierra Depth Ladder Requirement Update After Fallback",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: source/capture requirement refinement only. No validation, R/PnL, expectancy, live-readiness, promotion, or completion claim.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Event Window Refined Status", ""])
    for key, value in sorted(status_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- The full `9,919`-row ladder requirement denominator is preserved.",
            "- Only the `26` event-window sample-alignment rows are refined; missing exact `.depth` files and earlier-book-history requirements remain separate source/capture requirements.",
            "- Full-M15 event-window proxy rows are descriptor-only proxies and do not replace exact final-minute boundary60 truth.",
            "",
            "## Next Same-Resource Work",
            "",
            "- Continue exact missing `.depth` source-date acquisition and earlier-book-history repair/proxy search.",
            "- Split remaining imbalanced descriptors by command-ladder/fallback-neighbor relation.",
            "- Feed refined requirement statuses into the Route C question ledger and frontier map.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    requirements = read_jsonl(REQUIREMENT_LEDGER)
    fallback_rows = read_jsonl(FALLBACK_FEATURE_LEDGER)
    neighbor_rows = read_jsonl(NEIGHBOR_TARGET_LEDGER)
    fallback_by_request = {str(row.get("request_id")): row for row in fallback_rows}
    neighbor_by_request = {str(row.get("target_request_id")): row for row in neighbor_rows}
    updated_rows, event_rows = build_updated_rows(requirements, fallback_by_request, neighbor_by_request)
    group_rows = build_group_rows(updated_rows)
    status_counts = Counter(str(row.get("post_fallback_requirement_status")) for row in event_rows)
    counts = {
        "input_requirement_rows": len(requirements),
        "updated_requirement_rows": len(updated_rows),
        "event_window_requirement_rows": len(event_rows),
        "fallback_feature_input_rows": len(fallback_rows),
        "neighbor_target_input_rows": len(neighbor_rows),
        "group_rows": len(group_rows),
        "question_rows": 0,
        "boundary60_true_empty_rows": status_counts.get("BOUNDARY60_TRUE_EMPTY_AND_EVENT15_EMPTY_SOURCE_GAP_REMAINS", 0)
        + status_counts.get("BOUNDARY60_TRUE_EMPTY_EVENT15_BOOK_IMBALANCE_MISSING", 0)
        + status_counts.get("BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_NEIGHBOR_WEAKENED", 0)
        + status_counts.get("BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_UNDERPOWERED_NEIGHBOR", 0)
        + status_counts.get("BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_DESCRIPTOR_AVAILABLE", 0),
        "event15_proxy_descriptor_rows": status_counts.get("BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_NEIGHBOR_WEAKENED", 0)
        + status_counts.get("BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_UNDERPOWERED_NEIGHBOR", 0)
        + status_counts.get("BOUNDARY60_TRUE_EMPTY_EVENT15_PROXY_DESCRIPTOR_AVAILABLE", 0),
        "event15_source_gap_or_missing_rows": status_counts.get("BOUNDARY60_TRUE_EMPTY_AND_EVENT15_EMPTY_SOURCE_GAP_REMAINS", 0)
        + status_counts.get("BOUNDARY60_TRUE_EMPTY_EVENT15_BOOK_IMBALANCE_MISSING", 0),
    }
    question_rows = build_question_rows(event_rows, group_rows, counts)
    counts["question_rows"] = len(question_rows)
    write_jsonl(UPDATED_REQUIREMENT_LEDGER, updated_rows)
    write_jsonl(EVENT_RESOLUTION_LEDGER, event_rows)
    write_jsonl(GROUP_LEDGER, group_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    result = {
        "schema": "sierra_depth_ladder_requirement_after_fallback_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_REQUIREMENT_REFINEMENT_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "event_window_refined_status_counts": dict(sorted(status_counts.items())),
        "next_same_resource_work": [
            "continue exact missing .depth source-date acquisition and earlier-book-history repair/proxy search",
            "split imbalanced descriptors by command-ladder/fallback-neighbor relation",
            "feed refined requirement statuses into the question/frontier ledgers",
        ],
        "not_completion": "This requirement refinement packet closes one blocker ambiguity but does not complete the 60-hour moonshot objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, status_counts)
    write_summary(generated_utc, counts, status_counts)
    print(json.dumps({"ok": True, "counts": counts, "status_counts": dict(status_counts), "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
