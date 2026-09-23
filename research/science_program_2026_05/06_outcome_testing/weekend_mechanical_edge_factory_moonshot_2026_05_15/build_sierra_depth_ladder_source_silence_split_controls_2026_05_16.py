#!/usr/bin/env python3
"""Build same-denominator split controls for source-silence mutation designs."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SOURCE_STAMP = "2026-05-15"
STAMP = "2026-05-16"
ROUTE_ID = "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H"

TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_TARGET_LEDGER_{STAMP}.jsonl"
TARGET_SUMMARY_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_TARGET_SUMMARY_LEDGER_{STAMP}.jsonl"
MUTATION_DESIGN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_DESIGN_LEDGER_{STAMP}.jsonl"
MUTATION_EVIDENCE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_EVIDENCE_JOIN_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_SPLIT_CONTROL_RESULT_{STAMP}.json"
TARGET_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_SPLIT_TARGET_CONTROL_LEDGER_{STAMP}.jsonl"
DESIGN_TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_SPLIT_DESIGN_TARGET_LEDGER_{STAMP}.jsonl"
SPLIT_CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_SPLIT_CONTROL_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_SPLIT_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_SPLIT_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_SPLIT_CONTROL_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra ladder source-silence same-denominator split controls; source-control/design "
    "evidence only, with no strategy validation, trade outcome, R/PnL, expectancy, "
    "live-readiness, or live deployment"
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


def counter_dict(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def build_target_control_rows(targets: list[dict[str, Any]], summaries_by_request: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        summary = summaries_by_request.get(str(target.get("request_id")), {})
        rows.append(
            {
                "target_control_id": f"SIERRA-LADDER-SOURCE-SILENCE-SPLIT-TARGET-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                **target,
                "neighbor_bucket": summary.get("neighbor_bucket"),
                "same_source_neighbor_rows": summary.get("same_source_neighbor_rows"),
                "same_source_exact_feature_neighbor_rows": summary.get("same_source_exact_feature_neighbor_rows"),
                "same_source_source_silence_neighbor_rows": summary.get("same_source_source_silence_neighbor_rows"),
                "feature_neighbor_route_alignment_share": summary.get("feature_neighbor_route_alignment_share"),
                "feature_neighbor_route_alignment_n": summary.get("feature_neighbor_route_alignment_n"),
            }
        )
    return rows


def build_design_target_rows(
    evidence_rows: list[dict[str, Any]],
    design_by_mutation: dict[str, dict[str, Any]],
    target_by_request: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for evidence in evidence_rows:
        design = design_by_mutation.get(str(evidence.get("mutation_id")), {})
        target = target_by_request.get(str(evidence.get("request_id")), {})
        rows.append(
            {
                "design_target_id": f"SIERRA-LADDER-SOURCE-SILENCE-SPLIT-DESIGN-TARGET-{len(rows) + 1:06d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "mutation_id": evidence.get("mutation_id"),
                "mutation_type": evidence.get("mutation_type"),
                "queue_id": evidence.get("queue_id"),
                "request_id": evidence.get("request_id"),
                "source_silence_family": evidence.get("source_silence_family"),
                "source_silence_status": evidence.get("source_silence_status"),
                "source_silence_design_status": design.get("source_silence_design_status"),
                "proposed_branch_local_rule": design.get("proposed_branch_local_rule"),
                "required_next_evidence": design.get("required_next_evidence"),
                "source_symbol": evidence.get("source_symbol"),
                "source_date": evidence.get("source_date"),
                "neighbor_bucket": evidence.get("target_neighbor_bucket"),
                "same_source_exact_feature_neighbor_rows": evidence.get("same_source_exact_feature_neighbor_rows"),
                "feature_neighbor_route_alignment_share": evidence.get("feature_neighbor_route_alignment_share"),
                "feature_neighbor_route_alignment_n": evidence.get("feature_neighbor_route_alignment_n"),
                "route_c_delta_aligned_with_future": target.get("route_c_delta_aligned_with_future"),
                "route_c_future_change_per_current_range": target.get("route_c_future_change_per_current_range"),
                "command_feature_bucket": target.get("command_feature_bucket"),
            }
        )
    return rows


def row_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    alignments = [value for row in rows if (value := bool_value(row.get("route_c_delta_aligned_with_future"))) is not None]
    future_change = [
        value for row in rows
        if (value := safe_float(row.get("route_c_future_change_per_current_range"))) is not None
    ]
    feature_neighbor_alignment = [
        value for row in rows
        if (value := safe_float(row.get("feature_neighbor_route_alignment_share"))) is not None
    ]
    return {
        "n": len(rows),
        "route_alignment_share": share(alignments),
        "route_alignment_n": len(alignments),
        "mean_route_c_future_change_per_current_range": mean(future_change),
        "mean_feature_neighbor_route_alignment_share": mean(feature_neighbor_alignment),
        "source_symbol_counts": counter_dict([row.get("source_symbol") for row in rows]),
        "source_date_count": len({str(row.get("source_date")) for row in rows if row.get("source_date")}),
        "route_queue_counts": counter_dict([row.get("route_c_queue_id") or row.get("queue_id") for row in rows]),
        "neighbor_bucket_counts": counter_dict([row.get("neighbor_bucket") for row in rows]),
        "source_silence_family_counts": counter_dict([row.get("source_silence_family") for row in rows]),
    }


def classify_split(stats: dict[str, Any], group_values: dict[str, Any]) -> str:
    if stats["n"] < 5:
        return "SOURCE_SILENCE_SPLIT_UNDERPOWERED_N_LT_5"
    if "SOURCE_SILENCE_NO_SAME_SOURCE_CONTEXT" in stats["neighbor_bucket_counts"]:
        return "SOURCE_SILENCE_SPLIT_ACQUISITION_ONLY_CONTEXT"
    if "SOURCE_SILENCE_HAS_STRONG_SAME_SOURCE_FEATURE_ALIGNMENT_CONTEXT" in stats["neighbor_bucket_counts"]:
        return "SOURCE_SILENCE_SPLIT_HAS_STRONG_NEIGHBOR_ALIGNMENT_CONTEXT"
    if stats.get("route_alignment_share") is not None and stats["route_alignment_share"] <= 0.45:
        return "SOURCE_SILENCE_SPLIT_POSSIBLE_AVOID_CONTEXT"
    if stats.get("route_alignment_share") is not None and stats["route_alignment_share"] >= 0.60:
        return "SOURCE_SILENCE_SPLIT_ROUTE_ALIGNED_CONTEXT"
    if group_values.get("source_silence_design_status") == "SOURCE_SILENCE_AVOID_FILTER_DESIGN_CANDIDATE":
        return "SOURCE_SILENCE_SPLIT_AVOID_DESIGN_NEEDS_CONTROL"
    return "SOURCE_SILENCE_SPLIT_DESCRIPTIVE_CONTEXT"


def build_split_controls(target_rows: list[dict[str, Any]], design_target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families: list[tuple[str, list[dict[str, Any]], list[str]]] = [
        ("target_by_source_silence_family", target_rows, ["source_silence_family"]),
        ("target_by_neighbor_bucket", target_rows, ["neighbor_bucket"]),
        ("target_by_source_family_neighbor_bucket", target_rows, ["source_silence_family", "neighbor_bucket"]),
        ("target_by_command_bucket", target_rows, ["command_feature_bucket", "source_silence_family"]),
        ("target_by_route_queue", target_rows, ["route_c_queue_id", "source_silence_family"]),
        ("design_by_status", design_target_rows, ["source_silence_design_status"]),
        ("design_by_status_neighbor_bucket", design_target_rows, ["source_silence_design_status", "neighbor_bucket"]),
        ("design_by_mutation_type_source_family", design_target_rows, ["mutation_type", "source_silence_family"]),
    ]
    outputs: list[dict[str, Any]] = []
    for family, rows, keys in families:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[tuple(row.get(key) for key in keys)].append(row)
        for values, group in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
            group_values = {key: value for key, value in zip(keys, values, strict=True)}
            stats = row_stats(group)
            bucket = classify_split(stats, group_values)
            outputs.append(
                {
                    "split_control_id": f"SIERRA-LADDER-SOURCE-SILENCE-SPLIT-CONTROL-{len(outputs) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "control_family": family,
                    "group_values": group_values,
                    "stats": stats,
                    "split_control_bucket": bucket,
                    "next_same_resource_action": next_action_for_bucket(bucket),
                }
            )
    return outputs


def next_action_for_bucket(bucket: str) -> str:
    if bucket == "SOURCE_SILENCE_SPLIT_HAS_STRONG_NEIGHBOR_ALIGNMENT_CONTEXT":
        return "test whether true source silence can be treated as neutral/timing context where same-source feature neighbors align"
    if bucket == "SOURCE_SILENCE_SPLIT_POSSIBLE_AVOID_CONTEXT":
        return "materialize avoid-filter control using same-denominator exact-feature and source-silence rows"
    if bucket == "SOURCE_SILENCE_SPLIT_ACQUISITION_ONLY_CONTEXT":
        return "keep as exact source acquisition requirement and search alternate roots/source-date files"
    if bucket == "SOURCE_SILENCE_SPLIT_UNDERPOWERED_N_LT_5":
        return "aggregate only via declared source family/session/queue controls or acquire more exact source rows"
    return "preserve in mutation split packet and continue same-resource controls"


def build_bucket_rows(split_controls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in split_controls:
        grouped[(str(row.get("control_family")), str(row.get("split_control_bucket")))].append(row)
    for (family, bucket), group in sorted(grouped.items()):
        rows.append(
            {
                "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-SPLIT-BUCKET-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "control_family": family,
                "split_control_bucket": bucket,
                "control_rows": len(group),
                "total_underlying_rows": sum(int(row["stats"]["n"]) for row in group),
                "next_same_resource_action": next_action_for_bucket(bucket),
            }
        )
    return rows


def build_questions(bucket_rows: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket in bucket_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-SPLIT-Q-{len(rows) + 1:03d}",
                "question_family": bucket["control_family"],
                "split_control_bucket": bucket["split_control_bucket"],
                "row_count": bucket["control_rows"],
                "underlying_rows": bucket["total_underlying_rows"],
                "question": "Which concrete source-silence split/control/acquisition action follows for this full bucket?",
                "next_same_resource_action": bucket["next_same_resource_action"],
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_split_controls_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_split_control_result", "created"),
        (TARGET_CONTROL_LEDGER, "sierra_depth_ladder_source_silence_split_target_control_ledger", "created"),
        (DESIGN_TARGET_LEDGER, "sierra_depth_ladder_source_silence_split_design_target_ledger", "created"),
        (SPLIT_CONTROL_LEDGER, "sierra_depth_ladder_source_silence_split_control_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_split_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_split_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_split_control_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], bucket_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_split_controls",
        "status": "done",
        "route": "source_silence_same_denominator_split_controls",
        "details": "Built same-denominator target and design split controls from source-silence mutation design rows.",
        "counts": counts,
        "split_control_bucket_counts": bucket_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(TARGET_CONTROL_LEDGER),
            relative(DESIGN_TARGET_LEDGER),
            relative(SPLIT_CONTROL_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], bucket_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Depth Ladder Source Silence Split Controls",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: same-denominator source-silence split controls only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Split Control Buckets", ""])
    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"- `{bucket}`: `{count}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Promote no live behavior; use this as branch-local split/control design evidence.",
            "- Convert avoid/acquisition/strong-neighbor buckets into explicit no-API control tests.",
            "- Continue exact missing `.depth` source-date acquisition and no-clear earlier-history search.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    targets = read_jsonl(TARGET_LEDGER)
    target_summaries = read_jsonl(TARGET_SUMMARY_LEDGER)
    design_rows = read_jsonl(MUTATION_DESIGN_LEDGER)
    evidence_rows = read_jsonl(MUTATION_EVIDENCE_LEDGER)
    summaries_by_request = {str(row["request_id"]): row for row in target_summaries}
    designs_by_mutation = {str(row["mutation_id"]): row for row in design_rows}

    target_controls = build_target_control_rows(targets, summaries_by_request)
    target_by_request = {str(row["request_id"]): row for row in target_controls}
    design_targets = build_design_target_rows(evidence_rows, designs_by_mutation, target_by_request)
    split_controls = build_split_controls(target_controls, design_targets)
    bucket_rows = build_bucket_rows(split_controls)
    bucket_counts = counter_dict([row.get("split_control_bucket") for row in split_controls])
    counts = {
        "target_input_rows": len(targets),
        "target_summary_input_rows": len(target_summaries),
        "mutation_design_input_rows": len(design_rows),
        "mutation_evidence_input_rows": len(evidence_rows),
        "target_control_rows": len(target_controls),
        "design_target_rows": len(design_targets),
        "split_control_rows": len(split_controls),
        "bucket_rows": len(bucket_rows),
        "question_rows": 0,
    }
    question_rows = build_questions(bucket_rows, counts)
    counts["question_rows"] = len(question_rows)

    write_jsonl(TARGET_CONTROL_LEDGER, target_controls)
    write_jsonl(DESIGN_TARGET_LEDGER, design_targets)
    write_jsonl(SPLIT_CONTROL_LEDGER, split_controls)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    result = {
        "schema": "sierra_depth_ladder_source_silence_split_control_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_SOURCE_SILENCE_SPLIT_CONTROL_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "split_control_bucket_counts": bucket_counts,
        "not_completion": "This split-control packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "convert avoid/acquisition/strong-neighbor split buckets into no-API control tests",
            "continue exact missing .depth acquisition and no-clear earlier-history search",
            "feed source-silence split buckets into Route C mutation prioritization",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, bucket_counts)
    write_summary(generated_utc, counts, bucket_counts)
    print(json.dumps({"ok": True, "counts": counts, "bucket_counts": bucket_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
