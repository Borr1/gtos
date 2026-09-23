#!/usr/bin/env python3
"""Build no-API source-silence control tests from split-control buckets."""

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

SOURCE_SILENCE_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_ROUTE_C_JOIN_LEDGER_{STAMP}.jsonl"
TARGET_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_SPLIT_TARGET_CONTROL_LEDGER_{STAMP}.jsonl"
DESIGN_TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_SPLIT_DESIGN_TARGET_LEDGER_{STAMP}.jsonl"
SPLIT_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_SPLIT_CONTROL_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_NO_API_CONTROL_TEST_RESULT_{STAMP}.json"
TARGET_TEST_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_NO_API_TARGET_TEST_LEDGER_{STAMP}.jsonl"
DESIGN_TEST_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_NO_API_DESIGN_TEST_LEDGER_{STAMP}.jsonl"
CONTROL_COMPARISON_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_NO_API_CONTROL_COMPARISON_LEDGER_{STAMP}.jsonl"
ACQUISITION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_NO_API_ACQUISITION_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_NO_API_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_NO_API_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_NO_API_CONTROL_TEST_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra source-silence no-API control tests against same-denominator exact-feature controls; "
    "source-control/design evidence only, with no strategy validation, trade outcome, R/PnL, "
    "expectancy, live-readiness, or live deployment"
)

EXACT_FEATURE_STATUSES = {
    "LADDER_FEATURE_JOINED",
    "LADDER_FEATURE_JOINED_AFTER_IN_WINDOW_CLEAR_REPAIR",
    "LADDER_FEATURE_AND_BLOCKER_BUCKET_JOINED",
}

DESIGN_STATUSES_TO_CONTROL = {
    "SOURCE_SILENCE_AVOID_FILTER_DESIGN_CANDIDATE",
    "SOURCE_SILENCE_COST_AND_SOURCE_QUALITY_DESIGN",
    "SOURCE_SILENCE_SOURCE_PROXY_ACQUISITION_DESIGN",
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


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def bool_value(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def share(values: list[bool]) -> float | None:
    return sum(1 for value in values if value) / len(values) if values else None


def counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def numeric_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def route_alignment_share(rows: Iterable[dict[str, Any]]) -> tuple[float | None, int]:
    values = [value for row in rows if (value := bool_value(row.get("route_c_delta_aligned_with_future"))) is not None]
    return share(values), len(values)


def row_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    alignment, alignment_n = route_alignment_share(rows)
    future_change = [
        value for row in rows
        if (value := safe_float(row.get("route_c_future_change_per_current_range"))) is not None
    ]
    neighbor_alignment = [
        value for row in rows
        if (value := safe_float(row.get("feature_neighbor_route_alignment_share"))) is not None
    ]
    return {
        "n": len(rows),
        "unique_request_count": len({str(row.get("request_id")) for row in rows if row.get("request_id")}),
        "duplicate_row_count": max(0, len(rows) - len({str(row.get("request_id")) for row in rows if row.get("request_id")})),
        "route_alignment_share": alignment,
        "route_alignment_n": alignment_n,
        "mean_route_c_future_change_per_current_range": mean(future_change),
        "mean_feature_neighbor_route_alignment_share": mean(neighbor_alignment),
        "source_symbol_counts": counter_dict(row.get("source_symbol") for row in rows),
        "source_date_count": len({str(row.get("source_date")) for row in rows if row.get("source_date")}),
        "route_queue_counts": counter_dict(row.get("route_c_queue_id") or row.get("queue_id") for row in rows),
        "command_feature_bucket_counts": counter_dict(row.get("command_feature_bucket") for row in rows),
        "neighbor_bucket_counts": counter_dict(row.get("neighbor_bucket") for row in rows),
        "source_silence_family_counts": counter_dict(row.get("source_silence_family") for row in rows),
    }


def target_test_status(row: dict[str, Any]) -> str:
    family = row.get("source_silence_family")
    neighbor_bucket = row.get("neighbor_bucket")
    if family == "NO_CLEAR_AND_EVENT_BOUNDARY_SOURCE_SILENCE":
        return "NO_API_TEST_SOURCE_ACQUISITION_ONLY_NO_CLEAR"
    if neighbor_bucket == "SOURCE_SILENCE_HAS_STRONG_SAME_SOURCE_FEATURE_ALIGNMENT_CONTEXT":
        return "NO_API_TEST_STRONG_NEIGHBOR_ALIGNMENT_CONTEXT"
    if neighbor_bucket == "SOURCE_SILENCE_NO_SAME_SOURCE_CONTEXT":
        return "NO_API_TEST_SOURCE_ACQUISITION_ONLY_NO_SAME_SOURCE_CONTEXT"
    if neighbor_bucket == "SOURCE_SILENCE_HAS_UNDERPOWERED_SAME_SOURCE_FEATURE_CONTEXT":
        return "NO_API_TEST_UNDERPOWERED_NEEDS_AGGREGATE_CONTROL"
    if neighbor_bucket == "SOURCE_SILENCE_ONLY_HAS_OTHER_SOURCE_SILENCE_NEIGHBORS":
        return "NO_API_TEST_SOURCE_SILENCE_ONLY_NEIGHBOR_CONTEXT"
    return "NO_API_TEST_DESCRIPTIVE_SOURCE_SILENCE_CONTEXT"


def design_test_status(row: dict[str, Any]) -> str:
    status = row.get("source_silence_design_status")
    neighbor_bucket = row.get("neighbor_bucket")
    family = row.get("source_silence_family")
    if family == "NO_CLEAR_AND_EVENT_BOUNDARY_SOURCE_SILENCE":
        return "NO_API_TEST_DESIGN_SOURCE_ACQUISITION_ONLY_NO_CLEAR"
    if status in DESIGN_STATUSES_TO_CONTROL and neighbor_bucket == "SOURCE_SILENCE_HAS_UNDERPOWERED_SAME_SOURCE_FEATURE_CONTEXT":
        return "NO_API_TEST_DESIGN_POSSIBLE_AVOID_UNDERPOWERED_CONTROL"
    if status in DESIGN_STATUSES_TO_CONTROL and neighbor_bucket == "SOURCE_SILENCE_HAS_STRONG_SAME_SOURCE_FEATURE_ALIGNMENT_CONTEXT":
        return "NO_API_TEST_DESIGN_AVOID_WEAKENED_BY_STRONG_NEIGHBOR"
    if neighbor_bucket == "SOURCE_SILENCE_HAS_STRONG_SAME_SOURCE_FEATURE_ALIGNMENT_CONTEXT":
        return "NO_API_TEST_DESIGN_STRONG_NEIGHBOR_CONTEXT"
    if neighbor_bucket == "SOURCE_SILENCE_HAS_UNDERPOWERED_SAME_SOURCE_FEATURE_CONTEXT":
        return "NO_API_TEST_DESIGN_UNDERPOWERED_AGGREGATE_ONLY"
    return "NO_API_TEST_DESIGN_DESCRIPTIVE_OR_SOURCE_SILENCE_ONLY"


def control_pool_for_group(group_values: dict[str, Any], exact_rows: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    queue_id = group_values.get("route_c_queue_id") or group_values.get("queue_id")
    command_bucket = group_values.get("command_feature_bucket")
    source_symbol = group_values.get("source_symbol")
    if queue_id and command_bucket:
        pool = [
            row for row in exact_rows
            if row.get("route_c_queue_id") == queue_id and row.get("command_feature_bucket") == command_bucket
        ]
        if pool:
            return "same_queue_and_command_exact_feature", pool
    if queue_id:
        pool = [row for row in exact_rows if row.get("route_c_queue_id") == queue_id]
        if pool:
            return "same_queue_exact_feature", pool
    if command_bucket:
        pool = [row for row in exact_rows if row.get("command_feature_bucket") == command_bucket]
        if pool:
            return "same_command_exact_feature", pool
    if source_symbol and command_bucket:
        pool = [
            row for row in exact_rows
            if row.get("source_symbol") == source_symbol and row.get("command_feature_bucket") == command_bucket
        ]
        if pool:
            return "same_source_symbol_and_command_exact_feature", pool
    return "all_exact_feature_rows", exact_rows


def classify_control_verdict(test_label: str, group_stats: dict[str, Any], control_stats: dict[str, Any]) -> str:
    group_n = int(group_stats["n"])
    control_n = int(control_stats["n"])
    unique_group_n = int(group_stats.get("unique_request_count") or group_n)
    group_align = group_stats.get("route_alignment_share")
    control_align = control_stats.get("route_alignment_share")
    delta = numeric_delta(group_align, control_align)
    if control_n == 0:
        return "NO_API_CONTROL_EMPTY_ACQUISITION_ROUTE"
    if "ACQUISITION_ONLY" in test_label:
        return "NO_API_CONTROL_SOURCE_ACQUISITION_NOT_SIGNAL"
    if group_n < 5:
        return "NO_API_CONTROL_UNDERPOWERED_N_LT_5"
    if group_n < 20:
        return "NO_API_CONTROL_UNDERPOWERED_N_LT_20"
    if "POSSIBLE_AVOID" in test_label and delta is not None and delta <= -0.05:
        if unique_group_n < group_n:
            return "NO_API_CONTROL_POSSIBLE_AVOID_DUPLICATE_AWARE_RETEST_REQUIRED"
        return "NO_API_CONTROL_POSSIBLE_AVOID_SURVIVES_DESCRIPTOR_TEST"
    if "STRONG_NEIGHBOR" in test_label and delta is not None and delta >= -0.05:
        return "NO_API_CONTROL_STRONG_NEIGHBOR_NOT_WEAKENED_BY_EXACT_CONTROL"
    if delta is not None and abs(delta) <= 0.05:
        return "NO_API_CONTROL_NEAR_EXACT_FEATURE_CONTROL"
    return "NO_API_CONTROL_MIXED_OR_DESCRIPTIVE_CONTEXT"


def add_control_context(row: dict[str, Any], exact_rows: list[dict[str, Any]], source_join_by_request: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_row = source_join_by_request.get(str(row.get("request_id")), {})
    enriched = {**row}
    enriched["depth_path"] = source_row.get("depth_path")
    enriched["depth_file_exists"] = source_row.get("depth_file_exists")
    enriched["updated_ladder_join_status"] = source_row.get("updated_ladder_join_status")
    enriched["updated_ladder_snapshot_bucket"] = source_row.get("updated_ladder_snapshot_bucket")
    enriched["same_queue_control_scope"], same_queue = control_pool_for_group(
        {"route_c_queue_id": row.get("route_c_queue_id") or row.get("queue_id")},
        exact_rows,
    )
    enriched["same_command_control_scope"], same_command = control_pool_for_group(
        {"command_feature_bucket": row.get("command_feature_bucket")},
        exact_rows,
    )
    queue_stats = row_stats(same_queue)
    command_stats = row_stats(same_command)
    target_alignment = bool_value(row.get("route_c_delta_aligned_with_future"))
    target_alignment_float = None if target_alignment is None else float(target_alignment)
    enriched["same_queue_exact_feature_control_n"] = queue_stats["n"]
    enriched["same_queue_exact_feature_alignment_share"] = queue_stats["route_alignment_share"]
    enriched["same_queue_exact_feature_alignment_delta"] = numeric_delta(
        target_alignment_float, queue_stats["route_alignment_share"]
    )
    enriched["same_command_exact_feature_control_n"] = command_stats["n"]
    enriched["same_command_exact_feature_alignment_share"] = command_stats["route_alignment_share"]
    enriched["same_command_exact_feature_alignment_delta"] = numeric_delta(
        target_alignment_float, command_stats["route_alignment_share"]
    )
    return enriched


def build_group_controls(
    rows: list[dict[str, Any]],
    exact_rows: list[dict[str, Any]],
    families: list[tuple[str, list[str]]],
    label_field: str,
) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for family, keys in families:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[tuple(row.get(key) for key in keys)].append(row)
        for values, group in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
            group_values = {key: value for key, value in zip(keys, values, strict=True)}
            control_scope, control_pool = control_pool_for_group(group_values, exact_rows)
            group_stats = row_stats(group)
            control_stats = row_stats(control_pool)
            label = str(group_values.get(label_field) or family)
            outputs.append(
                {
                    "comparison_id": f"SIERRA-LADDER-SOURCE-SILENCE-NOAPI-COMP-{len(outputs) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "control_family": family,
                    "group_values": group_values,
                    "source_rows": group_stats,
                    "control_scope": control_scope,
                    "control_rows": control_stats,
                    "route_alignment_delta_vs_control": numeric_delta(
                        group_stats.get("route_alignment_share"),
                        control_stats.get("route_alignment_share"),
                    ),
                    "mean_future_change_delta_vs_control": numeric_delta(
                        group_stats.get("mean_route_c_future_change_per_current_range"),
                        control_stats.get("mean_route_c_future_change_per_current_range"),
                    ),
                    "no_api_control_verdict": classify_control_verdict(label, group_stats, control_stats),
                    "next_same_resource_action": next_action_for_verdict(
                        classify_control_verdict(label, group_stats, control_stats)
                    ),
                }
            )
    return outputs


def next_action_for_verdict(verdict: str) -> str:
    if verdict == "NO_API_CONTROL_POSSIBLE_AVOID_SURVIVES_DESCRIPTOR_TEST":
        return "convert into explicit avoid-filter challenger packet with source-silence and exact-feature controls"
    if verdict == "NO_API_CONTROL_POSSIBLE_AVOID_DUPLICATE_AWARE_RETEST_REQUIRED":
        return "deduplicate request IDs and build a possible-avoid challenger packet before any stronger interpretation"
    if verdict == "NO_API_CONTROL_STRONG_NEIGHBOR_NOT_WEAKENED_BY_EXACT_CONTROL":
        return "treat as neutral/timing context candidate and test against queue-level exact-feature controls"
    if verdict == "NO_API_CONTROL_SOURCE_ACQUISITION_NOT_SIGNAL":
        return "preserve as source acquisition and no-clear history repair requirement, not a signal"
    if verdict.startswith("NO_API_CONTROL_UNDERPOWERED"):
        return "aggregate through declared queue/source/design controls or acquire exact source rows before stronger claim"
    if verdict == "NO_API_CONTROL_EMPTY_ACQUISITION_ROUTE":
        return "search/acquire exact source rows or build source-safe proxy controls"
    return "preserve descriptor/control evidence and continue same-resource mutation tests"


def build_acquisition_rows(target_rows: list[dict[str, Any]], source_join_by_request: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in target_rows:
        if row.get("source_silence_family") != "NO_CLEAR_AND_EVENT_BOUNDARY_SOURCE_SILENCE":
            continue
        source_row = source_join_by_request.get(str(row.get("request_id")), {})
        rows.append(
            {
                "acquisition_id": f"SIERRA-LADDER-SOURCE-SILENCE-NOAPI-ACQ-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "request_id": row.get("request_id"),
                "source_symbol": row.get("source_symbol"),
                "source_date": row.get("source_date"),
                "depth_path": source_row.get("depth_path"),
                "depth_file_exists": source_row.get("depth_file_exists"),
                "source_silence_status": row.get("source_silence_status"),
                "command_feature_bucket": row.get("command_feature_bucket"),
                "neighbor_bucket": row.get("neighbor_bucket"),
                "route_c_queue_id": row.get("route_c_queue_id"),
                "route_c_symbol": row.get("route_c_symbol"),
                "exact_source_requirement": "recover earlier in-window book history or an exact same source-date depth file with records before canonical event boundary",
                "proxy_allowed": "only after exact owned/free/current source search is exhausted; proxy must stay source-control evidence",
                "next_same_resource_action": "search exact depth source-date roots and build same-source proxy controls while preserving no-wait posture",
            }
        )
    return rows


def build_bucket_rows(comparisons: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in comparisons:
        grouped[str(row["no_api_control_verdict"])].append(row)
    for verdict, group in sorted(grouped.items()):
        rows.append(
            {
                "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-NOAPI-BUCKET-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "no_api_control_verdict": verdict,
                "comparison_rows": len(group),
                "total_source_rows": sum(int(item["source_rows"]["n"]) for item in group),
                "control_scopes": counter_dict(item.get("control_scope") for item in group),
                "next_same_resource_action": next_action_for_verdict(verdict),
                "counts_context": counts,
            }
        )
    return rows


def build_questions(bucket_rows: list[dict[str, Any]], acquisition_rows: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket in bucket_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-NOAPI-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "no_api_control_verdict",
                "question_key": bucket["no_api_control_verdict"],
                "row_count": bucket["comparison_rows"],
                "underlying_rows": bucket["total_source_rows"],
                "question": "What exact no-API control, acquisition, or mutation action follows for this verdict bucket?",
                "next_same_resource_action": bucket["next_same_resource_action"],
                "counts_context": counts,
            }
        )
    acquisition_groups: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in acquisition_rows:
        acquisition_groups[(row.get("source_symbol"), row.get("source_date"))].append(row)
    for (symbol, source_date), group in sorted(acquisition_groups.items()):
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-NOAPI-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "source_acquisition",
                "question_key": {"source_symbol": symbol, "source_date": source_date},
                "row_count": len(group),
                "underlying_rows": len(group),
                "question": "Can exact earlier-book/no-clear source history be recovered from owned/current/free roots for this source-date?",
                "next_same_resource_action": "search exact depth source-date roots, then build proxy controls if exact recovery is impossible",
                "counts_context": counts,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_no_api_controls_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_no_api_control_test_result", "created"),
        (TARGET_TEST_LEDGER, "sierra_depth_ladder_source_silence_no_api_target_test_ledger", "created"),
        (DESIGN_TEST_LEDGER, "sierra_depth_ladder_source_silence_no_api_design_test_ledger", "created"),
        (CONTROL_COMPARISON_LEDGER, "sierra_depth_ladder_source_silence_no_api_control_comparison_ledger", "created"),
        (ACQUISITION_LEDGER, "sierra_depth_ladder_source_silence_no_api_acquisition_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_no_api_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_no_api_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_no_api_control_test_summary", "created"),
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
        "event_type": "sierra_depth_ladder_source_silence_no_api_controls",
        "status": "done",
        "route": "source_silence_avoid_acquisition_strong_neighbor_no_api_controls",
        "details": "Converted source-silence split buckets into row-level target tests, design tests, exact-feature control comparisons, and acquisition requirements.",
        "counts": counts,
        "no_api_control_verdict_counts": verdict_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(TARGET_TEST_LEDGER),
            relative(DESIGN_TEST_LEDGER),
            relative(CONTROL_COMPARISON_LEDGER),
            relative(ACQUISITION_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], verdict_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Depth Ladder Source Silence No-API Control Tests",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: source-control and mutation-design tests only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## No-API Control Verdicts", ""])
    for verdict, count in sorted(verdict_counts.items()):
        lines.append(f"- `{verdict}`: `{count}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Convert surviving possible-avoid descriptor tests into a dedicated challenger packet before any promotion claim.",
            "- Treat no-clear source-silence rows as exact acquisition/earlier-history repair requirements, not future-data waiting.",
            "- Treat strong-neighbor source-silence rows as neutral/timing-context candidates and continue queue-level controls.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_SILENCE_JOIN_LEDGER)
    target_controls = read_jsonl(TARGET_CONTROL_LEDGER)
    design_targets = read_jsonl(DESIGN_TARGET_LEDGER)
    split_controls = read_jsonl(SPLIT_CONTROL_LEDGER)

    source_join_by_request = {str(row.get("request_id")): row for row in source_join}
    exact_feature_rows = [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES and not row.get("source_silence_joined")
    ]

    target_tests: list[dict[str, Any]] = []
    for row in target_controls:
        enriched = add_control_context(row, exact_feature_rows, source_join_by_request)
        enriched["target_no_api_test_status"] = target_test_status(row)
        enriched["next_same_resource_action"] = next_action_for_verdict(
            classify_control_verdict(enriched["target_no_api_test_status"], row_stats([row]), row_stats(exact_feature_rows))
        )
        target_tests.append(enriched)

    design_tests: list[dict[str, Any]] = []
    for row in design_targets:
        enriched = add_control_context(row, exact_feature_rows, source_join_by_request)
        enriched["design_no_api_test_status"] = design_test_status(row)
        enriched["next_same_resource_action"] = next_action_for_verdict(
            classify_control_verdict(enriched["design_no_api_test_status"], row_stats([row]), row_stats(exact_feature_rows))
        )
        design_tests.append(enriched)

    target_families = [
        ("target_by_no_api_status", ["target_no_api_test_status"]),
        ("target_by_status_and_neighbor", ["target_no_api_test_status", "neighbor_bucket"]),
        ("target_by_source_family", ["source_silence_family"]),
        ("target_by_command_bucket", ["command_feature_bucket"]),
        ("target_by_route_queue", ["route_c_queue_id"]),
        ("target_by_queue_command", ["route_c_queue_id", "command_feature_bucket"]),
    ]
    design_families = [
        ("design_by_no_api_status", ["design_no_api_test_status"]),
        ("design_by_design_status", ["source_silence_design_status"]),
        ("design_by_status_neighbor", ["source_silence_design_status", "neighbor_bucket"]),
        ("design_by_mutation_source_family", ["mutation_type", "source_silence_family"]),
        ("design_by_queue_design_status", ["queue_id", "source_silence_design_status"]),
    ]
    comparisons = build_group_controls(target_tests, exact_feature_rows, target_families, "target_no_api_test_status")
    design_comparisons = build_group_controls(design_tests, exact_feature_rows, design_families, "design_no_api_test_status")
    for row in design_comparisons:
        row["comparison_id"] = f"SIERRA-LADDER-SOURCE-SILENCE-NOAPI-COMP-{len(comparisons) + 1:05d}"
        comparisons.append(row)

    acquisition_rows = build_acquisition_rows(target_tests, source_join_by_request)
    verdict_counts = counter_dict(row.get("no_api_control_verdict") for row in comparisons)
    counts = {
        "source_join_input_rows": len(source_join),
        "exact_feature_control_rows": len(exact_feature_rows),
        "target_control_input_rows": len(target_controls),
        "design_target_input_rows": len(design_targets),
        "split_control_input_rows": len(split_controls),
        "target_test_rows": len(target_tests),
        "design_test_rows": len(design_tests),
        "control_comparison_rows": len(comparisons),
        "acquisition_rows": len(acquisition_rows),
        "bucket_rows": 0,
        "question_rows": 0,
    }
    bucket_rows = build_bucket_rows(comparisons, counts)
    counts["bucket_rows"] = len(bucket_rows)
    question_rows = build_questions(bucket_rows, acquisition_rows, counts)
    counts["question_rows"] = len(question_rows)

    write_jsonl(TARGET_TEST_LEDGER, target_tests)
    write_jsonl(DESIGN_TEST_LEDGER, design_tests)
    write_jsonl(CONTROL_COMPARISON_LEDGER, comparisons)
    write_jsonl(ACQUISITION_LEDGER, acquisition_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    result = {
        "schema": "sierra_depth_ladder_source_silence_no_api_control_test_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_SOURCE_SILENCE_NO_API_CONTROL_TEST_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "no_api_control_verdict_counts": verdict_counts,
        "not_completion": "This no-API control-test packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "dedicate a possible-avoid challenger packet to the descriptor tests that survive exact-feature controls",
            "search exact .depth source-date roots for no-clear acquisition rows",
            "continue strong-neighbor timing-context queue controls without live/promotion claims",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, verdict_counts)
    write_summary(generated_utc, counts, verdict_counts)
    print(json.dumps({"ok": True, "counts": counts, "verdict_counts": verdict_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
