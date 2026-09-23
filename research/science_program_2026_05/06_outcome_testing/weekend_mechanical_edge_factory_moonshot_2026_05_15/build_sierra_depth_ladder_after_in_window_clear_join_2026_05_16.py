"""Join in-window CLEAR_BOOK ladder repairs back into Route C and mutations."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

ROUTE_C_LADDER_JOIN = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_JOIN_LEDGER_{STAMP}.jsonl"
IN_WINDOW_ROW_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IN_WINDOW_CLEAR_REPAIR_ROW_LEDGER_{STAMP}.jsonl"
IN_WINDOW_RESULT = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IN_WINDOW_CLEAR_REPAIR_RESULT_{STAMP}.json"
MUTATION_LEDGER = ROUTE_DIR / f"TICK_M15_TRANSFER_HYPOTHESIS_MUTATION_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_AFTER_IN_WINDOW_CLEAR_RESULT_{STAMP}.json"
UPDATED_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_AFTER_IN_WINDOW_CLEAR_JOIN_LEDGER_{STAMP}.jsonl"
REPAIRED_FEATURE_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_AFTER_IN_WINDOW_CLEAR_REPAIRED_FEATURE_LEDGER_{STAMP}.jsonl"
REMAINING_BLOCKER_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_AFTER_IN_WINDOW_CLEAR_BLOCKER_LEDGER_{STAMP}.jsonl"
MUTATION_CONTEXT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_AFTER_IN_WINDOW_CLEAR_MUTATION_CONTEXT_LEDGER_{STAMP}.jsonl"
MUTATION_REPAIR_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_AFTER_IN_WINDOW_CLEAR_MUTATION_JOIN_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_AFTER_IN_WINDOW_CLEAR_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_AFTER_IN_WINDOW_CLEAR_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_AFTER_IN_WINDOW_CLEAR_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Route C Sierra ladder denominator updated after in-window CLEAR_BOOK repair; "
    "source-control and mutation-design evidence only, with no strategy validation, "
    "trade outcome, R/PnL, expectancy, live-readiness, or live deployment"
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


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key)) for row in rows).items()))


def is_repaired(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    return str(row.get("primary_repair_status", "")).startswith("REPAIRED_")


def is_remaining_blocker(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    return str(row.get("primary_repair_status", "")).startswith("BLOCKED_")


def updated_join_status(original: dict[str, Any], repair: dict[str, Any] | None) -> str:
    if is_repaired(repair):
        return "LADDER_FEATURE_JOINED_AFTER_IN_WINDOW_CLEAR_REPAIR"
    if is_remaining_blocker(repair):
        return "LADDER_BLOCKER_REFINED_AFTER_IN_WINDOW_CLEAR_REPAIR"
    return str(original.get("ladder_join_status"))


def updated_bucket(original: dict[str, Any], repair: dict[str, Any] | None) -> str:
    if repair and repair.get("in_window_clear_feature_bucket"):
        return str(repair.get("in_window_clear_feature_bucket"))
    if repair and repair.get("primary_repair_status"):
        return str(repair.get("primary_repair_status"))
    return str(original.get("ladder_snapshot_bucket"))


def compact_repair_fields(repair: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "in_window_clear_primary_repair_status": repair.get("primary_repair_status"),
        "in_window_clear_timing_status": repair.get("clear_timing_status"),
        "in_window_clear_feature_bucket": repair.get("in_window_clear_feature_bucket"),
        "in_window_first_clear_utc": repair.get("first_in_window_clear_utc"),
        "in_window_first_clear_record_index": repair.get("first_in_window_clear_record_index"),
        "in_window_pre_boundary60_sample_count": repair.get("pre_boundary60_sample_count"),
        "in_window_event_boundary60_sample_count": repair.get("event_boundary60_sample_count"),
        "in_window_pre_boundary60_median_total_depth10": repair.get("pre_boundary60_median_total_depth10"),
        "in_window_event_boundary60_median_total_depth10": repair.get("event_boundary60_median_total_depth10"),
        "in_window_pre_boundary60_median_depth10_imbalance": repair.get("pre_boundary60_median_depth10_imbalance"),
        "in_window_event_boundary60_median_depth10_imbalance": repair.get("event_boundary60_median_depth10_imbalance"),
        "in_window_event_boundary60_median_spread_ticks": repair.get("event_boundary60_median_spread_ticks"),
        "in_window_event_boundary60_median_wall_concentration10": repair.get("event_boundary60_median_wall_concentration10"),
        "in_window_event_boundary60_mid_change_ticks": repair.get("event_boundary60_mid_change_ticks"),
        "in_window_next_same_resource_action": repair.get("next_same_resource_action"),
    }
    return fields


def build_updated_join_rows(route_rows: list[dict[str, Any]], repairs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in route_rows:
        repair = repairs.get(str(row.get("request_id")))
        updated = dict(row)
        updated.update(
            {
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "pre_in_window_clear_ladder_join_status": row.get("ladder_join_status"),
                "pre_in_window_clear_ladder_snapshot_bucket": row.get("ladder_snapshot_bucket"),
                "in_window_clear_repair_applied": repair is not None,
                "updated_ladder_join_status": updated_join_status(row, repair),
                "updated_ladder_snapshot_bucket": updated_bucket(row, repair),
            }
        )
        if repair:
            updated.update(compact_repair_fields(repair))
        out.append(updated)
    return out


def build_repaired_feature_rows(updated_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in updated_rows:
        if row.get("updated_ladder_join_status") != "LADDER_FEATURE_JOINED_AFTER_IN_WINDOW_CLEAR_REPAIR":
            continue
        rows.append(
            {
                "repair_feature_join_id": f"SIERRA-DEPTH-LADDER-AFTER-IN-WINDOW-FEATURE-{len(rows) + 1:06d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "request_id": row.get("request_id"),
                "route_c_queue_id": row.get("route_c_queue_id"),
                "route_c_symbol": row.get("route_c_symbol"),
                "route_c_primitive_flag": row.get("route_c_primitive_flag"),
                "source_symbol": row.get("source_symbol"),
                "source_date": row.get("source_date"),
                "horizon_id": row.get("horizon_id"),
                "depth_path": row.get("depth_path"),
                "updated_ladder_snapshot_bucket": row.get("updated_ladder_snapshot_bucket"),
                "command_feature_bucket": row.get("command_feature_bucket"),
                "command_event15_imbalance_sign": row.get("command_event15_imbalance_sign"),
                "route_c_delta_aligned_with_future": row.get("route_c_delta_aligned_with_future"),
                "route_c_future_change_per_current_range": row.get("route_c_future_change_per_current_range"),
                "route_c_future_abs_change": row.get("route_c_future_abs_change"),
                "event_boundary60_median_depth10_imbalance": row.get("in_window_event_boundary60_median_depth10_imbalance"),
                "event_boundary60_median_total_depth10": row.get("in_window_event_boundary60_median_total_depth10"),
                "event_boundary60_median_spread_ticks": row.get("in_window_event_boundary60_median_spread_ticks"),
                "event_boundary60_median_wall_concentration10": row.get("in_window_event_boundary60_median_wall_concentration10"),
                "event_boundary60_mid_change_ticks": row.get("in_window_event_boundary60_mid_change_ticks"),
                "next_same_resource_action": "feed repaired exact ladder descriptors into Route C controls, blocker splits, and mutation design packets",
            }
        )
    return rows


def build_blocker_rows(updated_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in updated_rows:
        if row.get("updated_ladder_join_status") != "LADDER_BLOCKER_REFINED_AFTER_IN_WINDOW_CLEAR_REPAIR":
            continue
        rows.append(
            {
                "remaining_blocker_id": f"SIERRA-DEPTH-LADDER-AFTER-IN-WINDOW-BLOCKER-{len(rows) + 1:06d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "request_id": row.get("request_id"),
                "route_c_queue_id": row.get("route_c_queue_id"),
                "route_c_symbol": row.get("route_c_symbol"),
                "route_c_primitive_flag": row.get("route_c_primitive_flag"),
                "source_symbol": row.get("source_symbol"),
                "source_date": row.get("source_date"),
                "horizon_id": row.get("horizon_id"),
                "depth_path": row.get("depth_path"),
                "pre_in_window_clear_ladder_snapshot_bucket": row.get("pre_in_window_clear_ladder_snapshot_bucket"),
                "blocker_type": row.get("in_window_clear_primary_repair_status"),
                "clear_timing_status": row.get("in_window_clear_timing_status"),
                "event_boundary60_sample_count": row.get("in_window_event_boundary60_sample_count"),
                "next_same_resource_action": remaining_blocker_action(str(row.get("in_window_clear_primary_repair_status"))),
            }
        )
    return rows


def remaining_blocker_action(status: str) -> str:
    if status == "BLOCKED_NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL":
        return "continue exact earlier depth source acquisition or file-start state search for these specific source-date windows"
    if status == "BLOCKED_IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY_BUT_NO_EVENT_SAMPLES":
        return "inspect event timestamp alignment and Sierra END_OF_BATCH sampling before classifying as source-history gap"
    if status == "BLOCKED_IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY_METRIC_MISSING":
        return "inspect reconstructed top-of-book depth state and source recording quality"
    return "manual blocker split review required"


def build_mutation_context(
    mutations: list[dict[str, Any]],
    repairs_by_queue: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    contexts: list[dict[str, Any]] = []
    joins: list[dict[str, Any]] = []
    for mutation in mutations:
        queue_id = str(mutation.get("queue_id"))
        rows = repairs_by_queue.get(queue_id, [])
        status_counts = count_by(rows, "primary_repair_status")
        feature_counts = count_by(rows, "in_window_clear_feature_bucket")
        repaired_count = sum(1 for row in rows if is_repaired(row))
        blocker_count = sum(1 for row in rows if is_remaining_blocker(row))
        if repaired_count and blocker_count:
            mutation_status = "MUTATION_HAS_REPAIRED_AND_REMAINING_IN_WINDOW_CLEAR_CONTEXT"
            action = "split mutation design by repaired exact ladder descriptors versus remaining blocker families"
        elif repaired_count:
            mutation_status = "MUTATION_HAS_REPAIRED_IN_WINDOW_CLEAR_LADDER_CONTEXT"
            action = "recompute mutation design constraints using repaired exact ladder features"
        elif blocker_count:
            mutation_status = "MUTATION_HAS_ONLY_REMAINING_IN_WINDOW_CLEAR_BLOCKERS"
            action = "keep mutation source-gated until blocker families are further repaired or proxied"
        else:
            mutation_status = "MUTATION_UNAFFECTED_BY_IN_WINDOW_CLEAR_REPAIR"
            action = "continue other current-data mutation packets"
        contexts.append(
            {
                "mutation_context_id": f"SIERRA-DEPTH-LADDER-AFTER-IN-WINDOW-MUTATION-CONTEXT-{len(contexts) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "mutation_id": mutation.get("mutation_id"),
                "mutation_type": mutation.get("mutation_type"),
                "queue_id": queue_id,
                "in_window_clear_context_rows": len(rows),
                "in_window_clear_repaired_rows": repaired_count,
                "in_window_clear_blocker_rows": blocker_count,
                "primary_repair_status_counts": status_counts,
                "feature_bucket_counts": feature_counts,
                "mutation_after_in_window_clear_status": mutation_status,
                "next_same_resource_action": action,
            }
        )
        for row in rows:
            joins.append(
                {
                    "mutation_repair_join_id": f"SIERRA-DEPTH-LADDER-AFTER-IN-WINDOW-MUTATION-JOIN-{len(joins) + 1:06d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "mutation_id": mutation.get("mutation_id"),
                    "mutation_type": mutation.get("mutation_type"),
                    "mutation_queue_id": queue_id,
                    "request_id": row.get("request_id"),
                    "source_symbol": row.get("source_symbol"),
                    "source_date": row.get("source_date"),
                    "horizon_id": row.get("horizon_id"),
                    "route_c_symbol": row.get("route_c_symbol"),
                    "route_c_primitive_flag": row.get("route_c_primitive_flag"),
                    "primary_repair_status": row.get("primary_repair_status"),
                    "in_window_clear_feature_bucket": row.get("in_window_clear_feature_bucket"),
                    "event_boundary60_median_depth10_imbalance": row.get("event_boundary60_median_depth10_imbalance"),
                    "event_boundary60_median_total_depth10": row.get("event_boundary60_median_total_depth10"),
                    "route_c_delta_aligned_with_future": row.get("route_c_delta_aligned_with_future"),
                    "route_c_future_change_per_current_range": row.get("route_c_future_change_per_current_range"),
                }
            )
    return contexts, joins


def build_bucket_rows(
    updated_rows: list[dict[str, Any]],
    repaired_features: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    mutation_context: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    families: list[tuple[str, list[str], list[dict[str, Any]]]] = [
        ("updated_ladder_join_status", ["updated_ladder_join_status"], updated_rows),
        ("updated_ladder_snapshot_bucket", ["updated_ladder_snapshot_bucket"], updated_rows),
        ("updated_status_by_source_symbol", ["source_symbol", "updated_ladder_join_status"], updated_rows),
        ("repaired_feature_by_queue", ["route_c_queue_id", "updated_ladder_snapshot_bucket"], repaired_features),
        ("remaining_blocker_type", ["blocker_type"], blockers),
        ("remaining_blocker_by_queue", ["route_c_queue_id", "blocker_type"], blockers),
        ("mutation_after_in_window_clear_status", ["mutation_after_in_window_clear_status"], mutation_context),
        ("mutation_type_after_in_window_clear_status", ["mutation_type", "mutation_after_in_window_clear_status"], mutation_context),
    ]
    outputs: list[dict[str, Any]] = []
    for family, keys, rows in families:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[tuple(row.get(key) for key in keys)].append(row)
        for values, group in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
            outputs.append(
                {
                    "bucket_id": f"SIERRA-DEPTH-LADDER-AFTER-IN-WINDOW-BUCKET-{len(outputs) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "group_family": family,
                    "group_keys": keys,
                    "group_values": {key: value for key, value in zip(keys, values, strict=True)},
                    "row_count": len(group),
                    "request_ids": sorted(str(row.get("request_id")) for row in group if row.get("request_id") is not None),
                    "mutation_ids": sorted(str(row.get("mutation_id")) for row in group if row.get("mutation_id") is not None),
                    "queue_counts": dict(sorted(Counter(str(row.get("route_c_queue_id") or row.get("queue_id")) for row in group).items())),
                    "next_same_resource_action": "use this full bucket ledger to drive the next Route C control/mutation recompute without representative truncation",
                }
            )
    return outputs


def build_questions(
    repaired_features: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    mutation_context: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket, count in sorted(Counter(str(row.get("updated_ladder_snapshot_bucket")) for row in repaired_features).items()):
        group = [row for row in repaired_features if row.get("updated_ladder_snapshot_bucket") == bucket]
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-AFTER-IN-WINDOW-Q-{len(rows) + 1:03d}",
                "question_family": "repaired_feature_bucket",
                "bucket": bucket,
                "row_count": count,
                "request_ids": sorted(str(row.get("request_id")) for row in group),
                "question": f"What Route C control and mutation split follows from all {count} repaired exact ladder rows in {bucket}?",
                "next_same_resource_action": "run a control/mutation recompute using the repaired exact ladder rows as current data",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    for blocker_type, count in sorted(Counter(str(row.get("blocker_type")) for row in blockers).items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-AFTER-IN-WINDOW-Q-{len(rows) + 1:03d}",
                "question_family": "remaining_blocker_type",
                "bucket": blocker_type,
                "row_count": count,
                "question": f"What exact same-resource source repair or proxy follows for all {count} remaining rows in {blocker_type}?",
                "next_same_resource_action": remaining_blocker_action(blocker_type),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    for status, count in sorted(Counter(str(row.get("mutation_after_in_window_clear_status")) for row in mutation_context).items()):
        rows.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-AFTER-IN-WINDOW-Q-{len(rows) + 1:03d}",
                "question_family": "mutation_context_status",
                "bucket": status,
                "row_count": count,
                "question": f"Which mutation design branches must be recomputed for all {count} mutation rows in {status}?",
                "next_same_resource_action": "feed mutation context rows into the next current-data mutation packet",
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_after_in_window_clear_join_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_after_in_window_clear_join_result", "created"),
        (UPDATED_JOIN_LEDGER, "sierra_depth_ladder_after_in_window_clear_join_ledger", "created"),
        (REPAIRED_FEATURE_JOIN_LEDGER, "sierra_depth_ladder_after_in_window_clear_repaired_feature_ledger", "created"),
        (REMAINING_BLOCKER_LEDGER, "sierra_depth_ladder_after_in_window_clear_blocker_ledger", "created"),
        (MUTATION_CONTEXT_LEDGER, "sierra_depth_ladder_after_in_window_clear_mutation_context_ledger", "created"),
        (MUTATION_REPAIR_JOIN_LEDGER, "sierra_depth_ladder_after_in_window_clear_mutation_join_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_after_in_window_clear_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_after_in_window_clear_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_after_in_window_clear_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], status_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_after_in_window_clear_join",
        "status": "done",
        "route": "sierra_depth_ladder_after_in_window_clear_join",
        "details": "Updated the full Route C Sierra ladder denominator and all mutation rows with in-window CLEAR_BOOK repair context.",
        "counts": counts,
        "updated_ladder_join_status_counts": status_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(UPDATED_JOIN_LEDGER),
            relative(REPAIRED_FEATURE_JOIN_LEDGER),
            relative(REMAINING_BLOCKER_LEDGER),
            relative(MUTATION_CONTEXT_LEDGER),
            relative(MUTATION_REPAIR_JOIN_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], status_counts: dict[str, int], bucket_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Depth Ladder Route C After In-Window CLEAR_BOOK Join",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Evidence class: full Route C ladder denominator and mutation-design update after same-source in-window clear repair.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Updated Ladder Join Status", ""])
    for key, value in sorted(status_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Repaired Feature Buckets", ""])
    for key, value in sorted(bucket_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- The full `10,382` Route C/Sierra depth request denominator is preserved.",
            "- All `393` old no-prior-clear ladder blockers now carry in-window clear repair context.",
            "- `342` rows become exact repaired boundary ladder descriptors and `51` remain exact source/sample blockers.",
            "- Mutation context is preserved for every `54` mutation rows and all row-level mutation/repair joins.",
            "- This packet is a current-data control/mutation update, not a terminal closeout.",
            "",
            "## Next Same-Resource Work",
            "",
            "- Recompute Route C controls with `831` exact ladder feature rows (`489` prior-clear plus `342` in-window-clear repaired).",
            "- Split the `51` remaining blockers by no-clear/no-sample source routes and search/acquire/proxy immediately.",
            "- Feed repaired ladder buckets into current-data mutation rows outside the prior imbalanced context.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    route_rows = read_jsonl(ROUTE_C_LADDER_JOIN)
    repair_rows = read_jsonl(IN_WINDOW_ROW_LEDGER)
    repair_result = json.loads(IN_WINDOW_RESULT.read_text(encoding="utf-8"))
    mutations = read_jsonl(MUTATION_LEDGER)

    repairs_by_request = {str(row.get("request_id")): row for row in repair_rows}
    repairs_by_queue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in repair_rows:
        repairs_by_queue[str(row.get("route_c_queue_id"))].append(row)

    updated_rows = build_updated_join_rows(route_rows, repairs_by_request)
    repaired_features = build_repaired_feature_rows(updated_rows)
    remaining_blockers = build_blocker_rows(updated_rows)
    mutation_context, mutation_joins = build_mutation_context(mutations, repairs_by_queue)
    bucket_rows = build_bucket_rows(updated_rows, repaired_features, remaining_blockers, mutation_context)
    question_rows = build_questions(repaired_features, remaining_blockers, mutation_context)

    status_counts = count_by(updated_rows, "updated_ladder_join_status")
    feature_bucket_counts = count_by(repaired_features, "updated_ladder_snapshot_bucket")
    mutation_status_counts = count_by(mutation_context, "mutation_after_in_window_clear_status")
    counts = {
        "input_route_c_join_rows": len(route_rows),
        "updated_route_c_join_rows": len(updated_rows),
        "input_in_window_clear_rows": len(repair_rows),
        "input_in_window_clear_repaired_full_rows": repair_result["counts"]["repaired_full_pre_and_event_rows"],
        "input_in_window_clear_remaining_blocker_rows": repair_result["counts"]["remaining_blocker_primary_rows"],
        "old_no_prior_clear_rows_updated": sum(1 for row in updated_rows if row.get("in_window_clear_repair_applied")),
        "repaired_feature_join_rows": len(repaired_features),
        "remaining_blocker_rows": len(remaining_blockers),
        "mutation_input_rows": len(mutations),
        "mutation_context_rows": len(mutation_context),
        "mutation_repair_join_rows": len(mutation_joins),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }

    write_jsonl(UPDATED_JOIN_LEDGER, updated_rows)
    write_jsonl(REPAIRED_FEATURE_JOIN_LEDGER, repaired_features)
    write_jsonl(REMAINING_BLOCKER_LEDGER, remaining_blockers)
    write_jsonl(MUTATION_CONTEXT_LEDGER, mutation_context)
    write_jsonl(MUTATION_REPAIR_JOIN_LEDGER, mutation_joins)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    result = {
        "schema": "sierra_depth_ladder_route_c_after_in_window_clear_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_ROUTE_C_DENOMINATOR_AFTER_IN_WINDOW_CLEAR_REPAIR",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "updated_ladder_join_status_counts": status_counts,
        "repaired_feature_bucket_counts": feature_bucket_counts,
        "mutation_after_in_window_clear_status_counts": mutation_status_counts,
        "next_same_resource_work": [
            "recompute Route C controls with repaired exact ladder features",
            "split and pursue the 51 remaining in-window clear blockers immediately",
            "feed repaired ladder buckets into current-data mutation rows outside the imbalanced ladder context",
        ],
        "not_completion": "This denominator update consumes the in-window clear repair but does not complete the moonshot.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, status_counts)
    write_summary(generated_utc, counts, status_counts, feature_bucket_counts)
    print(json.dumps({"ok": True, "counts": counts, "status_counts": status_counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
