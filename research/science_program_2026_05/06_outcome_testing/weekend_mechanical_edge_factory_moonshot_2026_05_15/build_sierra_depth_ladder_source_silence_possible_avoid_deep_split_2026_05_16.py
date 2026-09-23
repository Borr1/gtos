#!/usr/bin/env python3
"""Deep-split the de-duplicated source-silence possible-avoid branch."""

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
DEDUP_TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEDUP_TARGET_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEEP_SPLIT_RESULT_{STAMP}.json"
GROUP_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEEP_SPLIT_GROUP_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEEP_SPLIT_BUCKET_LEDGER_{STAMP}.jsonl"
DECISION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEEP_SPLIT_DECISION_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEEP_SPLIT_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEEP_SPLIT_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Deep split of de-duplicated source-silence possible-avoid branch; source-control/design "
    "evidence only, with no strategy validation, trade outcome, R/PnL, expectancy, "
    "live-readiness, or live deployment"
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


def numeric_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def counter_dict(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def row_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    alignments = [value for row in rows if (value := bool_value(row.get("route_c_delta_aligned_with_future"))) is not None]
    future_change = [
        value for row in rows
        if (value := safe_float(row.get("route_c_future_change_per_current_range"))) is not None
    ]
    return {
        "n": len(rows),
        "route_alignment_share": share(alignments),
        "route_alignment_n": len(alignments),
        "mean_route_c_future_change_per_current_range": mean(future_change),
        "source_date_count": len({str(row.get("source_date")) for row in rows if row.get("source_date")}),
        "source_symbol_counts": counter_dict(row.get("source_symbol") for row in rows),
        "queue_counts": counter_dict(row.get("queue_id") or row.get("route_c_queue_id") for row in rows),
        "command_feature_bucket_counts": counter_dict(row.get("command_feature_bucket") for row in rows),
    }


def exact_feature_rows(source_join: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES and not row.get("source_silence_joined")
    ]


def normalize_control_field(field: str) -> str:
    if field == "queue_id":
        return "route_c_queue_id"
    return field


def matched_controls(group_values: dict[str, Any], exact_rows: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    control_fields = {
        normalize_control_field(key): value
        for key, value in group_values.items()
        if value is not None
    }
    control = [
        row for row in exact_rows
        if all(row.get(field) == value for field, value in control_fields.items())
    ]
    if control:
        return "exact_feature_matched_on_" + "_".join(sorted(control_fields.keys())), control

    # Preserve a deterministic fallback ladder without dropping the group.
    for fallback_keys in [
        ["route_c_queue_id", "command_feature_bucket"],
        ["route_c_queue_id"],
        ["command_feature_bucket"],
        ["source_symbol"],
        ["source_date"],
    ]:
        available = {key: control_fields[key] for key in fallback_keys if key in control_fields}
        if not available:
            continue
        control = [
            row for row in exact_rows
            if all(row.get(field) == value for field, value in available.items())
        ]
        if control:
            return "exact_feature_fallback_on_" + "_".join(sorted(available.keys())), control
    return "all_exact_feature_fallback", exact_rows


def classify_group(group_stats: dict[str, Any], control_stats: dict[str, Any]) -> str:
    n = int(group_stats["n"])
    control_n = int(control_stats["n"])
    delta = numeric_delta(group_stats.get("route_alignment_share"), control_stats.get("route_alignment_share"))
    if control_n == 0:
        return "DEEP_SPLIT_CONTROL_EMPTY"
    if n < 5:
        return "DEEP_SPLIT_UNDERPOWERED_N_LT_5"
    if delta is not None and delta <= -0.05:
        if n >= 20:
            return "DEEP_SPLIT_AVOID_SURVIVES_MATCHED_CONTROL_N_GE_20"
        return "DEEP_SPLIT_AVOID_DIRECTIONAL_BUT_UNDERPOWERED"
    if delta is not None and abs(delta) <= 0.05:
        return "DEEP_SPLIT_NEAR_CONTROL"
    return "DEEP_SPLIT_NOT_AVOID_OR_MIXED"


def next_action_for_bucket(bucket: str) -> str:
    if bucket == "DEEP_SPLIT_AVOID_SURVIVES_MATCHED_CONTROL_N_GE_20":
        return "promote to branch-local challenger spec packet with additional concentration/placebo controls"
    if bucket == "DEEP_SPLIT_AVOID_DIRECTIONAL_BUT_UNDERPOWERED":
        return "preserve as micro-challenger; acquire/proxy more exact rows or aggregate through declared parent axis"
    if bucket == "DEEP_SPLIT_CONTROL_EMPTY":
        return "search exact source controls or build source-safe proxy controls"
    if bucket.startswith("DEEP_SPLIT_UNDERPOWERED"):
        return "do not discard; aggregate with parent axis or acquire/proxy additional rows"
    if bucket == "DEEP_SPLIT_NEAR_CONTROL":
        return "treat as control-explained unless another axis preserves residual"
    return "preserve failure intelligence and use as avoid-branch boundary"


def build_group_rows(targets: list[dict[str, Any]], exact_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axes: list[tuple[str, list[str]]] = [
        ("by_queue", ["queue_id"]),
        ("by_command_bucket", ["command_feature_bucket"]),
        ("by_source_symbol", ["source_symbol"]),
        ("by_source_date", ["source_date"]),
        ("by_queue_command", ["queue_id", "command_feature_bucket"]),
        ("by_queue_source_symbol", ["queue_id", "source_symbol"]),
        ("by_command_source_symbol", ["command_feature_bucket", "source_symbol"]),
        ("by_source_date_symbol", ["source_date", "source_symbol"]),
        ("by_source_date_queue", ["source_date", "queue_id"]),
    ]
    outputs: list[dict[str, Any]] = []
    for family, keys in axes:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in targets:
            grouped[tuple(row.get(key) for key in keys)].append(row)
        for values, group in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
            group_values = {key: value for key, value in zip(keys, values, strict=True)}
            control_scope, control = matched_controls(group_values, exact_rows)
            group_stats = row_stats(group)
            control_stats = row_stats(control)
            bucket = classify_group(group_stats, control_stats)
            outputs.append(
                {
                    "group_id": f"SIERRA-LADDER-SOURCE-SILENCE-POSSIBLE-AVOID-DEEP-SPLIT-GROUP-{len(outputs) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "split_family": family,
                    "group_values": group_values,
                    "request_ids": sorted(str(row.get("request_id")) for row in group),
                    "candidate_rows": group_stats,
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
                    "deep_split_bucket": bucket,
                    "next_same_resource_action": next_action_for_bucket(bucket),
                }
            )
    return outputs


def build_bucket_rows(group_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in group_rows:
        grouped[(row["split_family"], row["deep_split_bucket"])].append(row)
    for (family, bucket), group in sorted(grouped.items()):
        rows.append(
            {
                "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-POSSIBLE-AVOID-DEEP-SPLIT-BUCKET-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "split_family": family,
                "deep_split_bucket": bucket,
                "group_rows": len(group),
                "underlying_candidate_rows": sum(int(row["candidate_rows"]["n"]) for row in group),
                "control_scopes": counter_dict(row["control_scope"] for row in group),
                "next_same_resource_action": next_action_for_bucket(bucket),
            }
        )
    return rows


def build_decision_rows(group_rows: list[dict[str, Any]], targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bucket_counts = Counter(row["deep_split_bucket"] for row in group_rows)
    family_counts = Counter(row["split_family"] for row in group_rows)
    if bucket_counts.get("DEEP_SPLIT_AVOID_SURVIVES_MATCHED_CONTROL_N_GE_20", 0):
        decision = "DEEP_SPLIT_HAS_N_GE_20_AVOID_CHALLENGER"
    elif bucket_counts.get("DEEP_SPLIT_AVOID_DIRECTIONAL_BUT_UNDERPOWERED", 0):
        decision = "DEEP_SPLIT_ONLY_UNDERPOWERED_AVOID_MICRO_CLUSTERS"
    elif bucket_counts.get("DEEP_SPLIT_NEAR_CONTROL", 0):
        decision = "DEEP_SPLIT_PARTLY_CONTROL_EXPLAINED"
    else:
        decision = "DEEP_SPLIT_NO_AVOID_RESIDUAL"
    return [
        {
            "decision_id": "SIERRA-LADDER-SOURCE-SILENCE-POSSIBLE-AVOID-DEEP-SPLIT-DECISION-00001",
            "route_id": ROUTE_ID,
            "safe_flags": SAFE_FLAGS,
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "candidate_rows": row_stats(targets),
            "bucket_counts": dict(sorted(bucket_counts.items())),
            "split_family_counts": dict(sorted(family_counts.items())),
            "decision_status": decision,
            "next_same_resource_action": next_action_for_decision(decision),
            "not_promotion": "Branch-local source-control/challenger design only.",
        }
    ]


def next_action_for_decision(decision: str) -> str:
    if decision == "DEEP_SPLIT_HAS_N_GE_20_AVOID_CHALLENGER":
        return "build a branch-local challenger spec and add placebo/concentration controls before any validation lane"
    if decision == "DEEP_SPLIT_ONLY_UNDERPOWERED_AVOID_MICRO_CLUSTERS":
        return "preserve micro-clusters, aggregate through parent axes, and acquire/proxy more exact rows"
    if decision == "DEEP_SPLIT_PARTLY_CONTROL_EXPLAINED":
        return "kill or constrain control-explained axes, preserve residual axes as acquisition/challenger queue"
    return "convert the branch into failure intelligence and acquisition/source-quality constraints"


def build_questions(bucket_rows: list[dict[str, Any]], decisions: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket in bucket_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-POSSIBLE-AVOID-DEEP-SPLIT-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": bucket["split_family"],
                "question_key": bucket["deep_split_bucket"],
                "row_count": bucket["group_rows"],
                "underlying_rows": bucket["underlying_candidate_rows"],
                "question": "What source-control, acquisition, challenger, or kill action follows for this deep split bucket?",
                "next_same_resource_action": bucket["next_same_resource_action"],
                "counts_context": counts,
            }
        )
    for decision in decisions:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-POSSIBLE-AVOID-DEEP-SPLIT-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "decision",
                "question_key": decision["decision_status"],
                "question": "What is the next concrete action after the possible-avoid deep split?",
                "next_same_resource_action": decision["next_same_resource_action"],
                "counts_context": counts,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_possible_avoid_deep_split_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_possible_avoid_deep_split_result", "created"),
        (GROUP_LEDGER, "sierra_depth_ladder_source_silence_possible_avoid_deep_split_group_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_possible_avoid_deep_split_bucket_ledger", "created"),
        (DECISION_LEDGER, "sierra_depth_ladder_source_silence_possible_avoid_deep_split_decision_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_possible_avoid_deep_split_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_possible_avoid_deep_split_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], decision_status: str) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_possible_avoid_deep_split",
        "status": "done",
        "route": "source_silence_possible_avoid_queue_command_source_deep_split",
        "details": "Split the de-duplicated possible-avoid branch by queue, command bucket, source date, source symbol, and pairwise axes against matched exact-feature controls.",
        "counts": counts,
        "decision_status": decision_status,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(GROUP_LEDGER),
            relative(BUCKET_LEDGER),
            relative(DECISION_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], decisions: list[dict[str, Any]]) -> None:
    decision = decisions[0]
    lines = [
        "# Sierra Depth Ladder Source Silence Possible-Avoid Deep Split",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: deep source-control/challenger split only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- `decision_status`: `{decision['decision_status']}`",
            f"- `next_same_resource_action`: {decision['next_same_resource_action']}",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    targets = read_jsonl(DEDUP_TARGET_LEDGER)
    exact_rows = exact_feature_rows(source_join)
    group_rows = build_group_rows(targets, exact_rows)
    bucket_rows = build_bucket_rows(group_rows)
    decisions = build_decision_rows(group_rows, targets)
    counts = {
        "source_join_input_rows": len(source_join),
        "exact_feature_control_rows": len(exact_rows),
        "dedup_target_rows": len(targets),
        "group_rows": len(group_rows),
        "bucket_rows": len(bucket_rows),
        "decision_rows": len(decisions),
        "question_rows": 0,
    }
    questions = build_questions(bucket_rows, decisions, counts)
    counts["question_rows"] = len(questions)

    write_jsonl(GROUP_LEDGER, group_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(DECISION_LEDGER, decisions)
    write_jsonl(QUESTION_LEDGER, questions)
    result = {
        "schema": "sierra_depth_ladder_source_silence_possible_avoid_deep_split_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_SOURCE_SILENCE_POSSIBLE_AVOID_DEEP_SPLIT_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "deep_split_bucket_counts": counter_dict(row["deep_split_bucket"] for row in group_rows),
        "decision_status": decisions[0]["decision_status"],
        "not_completion": "This deep-split packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [decisions[0]["next_same_resource_action"]],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, decisions[0]["decision_status"])
    write_summary(generated_utc, counts, decisions)
    print(json.dumps({"ok": True, "counts": counts, "decision_status": decisions[0]["decision_status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
