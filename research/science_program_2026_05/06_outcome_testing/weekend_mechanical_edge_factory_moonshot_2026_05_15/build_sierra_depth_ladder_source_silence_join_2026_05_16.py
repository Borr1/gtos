#!/usr/bin/env python3
"""Join true source-silence ladder blockers into Route C and mutations."""

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

EFFECTIVE_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_ROUTE_C_CONTROL_AFTER_IN_WINDOW_CLEAR_JOIN_LEDGER_{STAMP}.jsonl"
SOURCE_SILENCE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_REMAINING_BLOCKER_REPAIR_ROW_LEDGER_{STAMP}.jsonl"
MUTATION_LEDGER = ROUTE_DIR / f"TICK_M15_TRANSFER_HYPOTHESIS_MUTATION_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_JOIN_RESULT_{STAMP}.json"
UPDATED_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_ROUTE_C_JOIN_LEDGER_{STAMP}.jsonl"
TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_TARGET_LEDGER_{STAMP}.jsonl"
NEIGHBOR_PAIR_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_NEIGHBOR_PAIR_LEDGER_{STAMP}.jsonl"
TARGET_SUMMARY_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_TARGET_SUMMARY_LEDGER_{STAMP}.jsonl"
MUTATION_CONTEXT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_CONTEXT_LEDGER_{STAMP}.jsonl"
MUTATION_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_JOIN_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_JOIN_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra ladder true source-silence status joined to Route C controls and mutation context; "
    "source-control and design evidence only, with no strategy validation, trade outcome, "
    "R/PnL, expectancy, live-readiness, or live deployment"
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


def counter_dict(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def bool_value(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def share(values: list[bool]) -> float | None:
    return sum(1 for value in values if value) / len(values) if values else None


def source_silence_family(status: str | None) -> str | None:
    if status == "BLOCKED_TRUE_EVENT_BOUNDARY_NO_RECORDS_AFTER_CLEAR":
        return "TRUE_EVENT_BOUNDARY_SOURCE_SILENCE_AFTER_CLEAR"
    if status == "BLOCKED_NO_CLEAR_AND_NO_EVENT_BOUNDARY_RECORDS":
        return "NO_CLEAR_AND_EVENT_BOUNDARY_SOURCE_SILENCE"
    return None


def build_updated_join_rows(
    effective_rows: list[dict[str, Any]],
    silence_by_request: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in effective_rows:
        silence = silence_by_request.get(str(row.get("request_id")))
        updated = dict(row)
        updated.update(
            {
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "source_silence_joined": silence is not None,
                "source_silence_status": None,
                "source_silence_family": None,
                "source_silence_event_boundary_record_count": None,
                "source_silence_next_same_resource_action": None,
            }
        )
        if silence:
            updated.update(
                {
                    "source_silence_status": silence.get("remaining_repair_status"),
                    "source_silence_family": source_silence_family(silence.get("remaining_repair_status")),
                    "source_silence_input_blocker_type": silence.get("input_blocker_type"),
                    "source_silence_event_boundary_record_count": silence.get("event_boundary_record_count"),
                    "source_silence_next_same_resource_action": silence.get("next_same_resource_action"),
                    "updated_ladder_snapshot_bucket": source_silence_family(silence.get("remaining_repair_status")),
                }
            )
        out.append(updated)
    return out


def build_target_rows(updated_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in updated_rows:
        if not row.get("source_silence_joined"):
            continue
        rows.append(
            {
                "target_id": f"SIERRA-LADDER-SOURCE-SILENCE-TARGET-{len(rows) + 1:05d}",
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
                "command_feature_bucket": row.get("command_feature_bucket"),
                "route_c_delta_aligned_with_future": row.get("route_c_delta_aligned_with_future"),
                "route_c_future_change_per_current_range": row.get("route_c_future_change_per_current_range"),
                "source_silence_status": row.get("source_silence_status"),
                "source_silence_family": row.get("source_silence_family"),
                "source_silence_input_blocker_type": row.get("source_silence_input_blocker_type"),
                "source_silence_event_boundary_record_count": row.get("source_silence_event_boundary_record_count"),
                "next_same_resource_action": "use same-source neighbors and mutation joins to decide whether source silence is avoid, neutral, or acquisition-only context",
            }
        )
    return rows


def is_feature_row(row: dict[str, Any]) -> bool:
    return "FEATURE" in str(row.get("ladder_join_status"))


def build_neighbor_pairs(updated_rows: list[dict[str, Any]], targets: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_source_date: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in updated_rows:
        if is_feature_row(row) or row.get("source_silence_joined"):
            by_source_date[(str(row.get("source_symbol")), str(row.get("source_date")))].append(row)

    pairs: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for target in targets:
        key = (str(target.get("source_symbol")), str(target.get("source_date")))
        candidates = by_source_date.get(key, [])
        neighbors = [row for row in candidates if str(row.get("request_id")) != str(target.get("request_id"))]
        feature_neighbors = [row for row in neighbors if is_feature_row(row)]
        silence_neighbors = [row for row in neighbors if row.get("source_silence_joined")]
        alignments = [
            value for row in feature_neighbors
            if (value := bool_value(row.get("route_c_delta_aligned_with_future"))) is not None
        ]
        summary_status = classify_target_context(len(feature_neighbors), len(silence_neighbors), share(alignments))
        summaries.append(
            {
                "target_summary_id": f"SIERRA-LADDER-SOURCE-SILENCE-TARGET-SUMMARY-{len(summaries) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "request_id": target.get("request_id"),
                "route_c_queue_id": target.get("route_c_queue_id"),
                "source_symbol": target.get("source_symbol"),
                "source_date": target.get("source_date"),
                "source_silence_family": target.get("source_silence_family"),
                "same_source_neighbor_rows": len(neighbors),
                "same_source_exact_feature_neighbor_rows": len(feature_neighbors),
                "same_source_source_silence_neighbor_rows": len(silence_neighbors),
                "feature_neighbor_route_alignment_share": share(alignments),
                "feature_neighbor_route_alignment_n": len(alignments),
                "neighbor_bucket": summary_status,
                "next_same_resource_action": next_action_for_neighbor_bucket(summary_status),
            }
        )
        for neighbor in neighbors:
            pairs.append(
                {
                    "pair_id": f"SIERRA-LADDER-SOURCE-SILENCE-PAIR-{len(pairs) + 1:06d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "target_request_id": target.get("request_id"),
                    "neighbor_request_id": neighbor.get("request_id"),
                    "source_symbol": target.get("source_symbol"),
                    "source_date": target.get("source_date"),
                    "target_source_silence_family": target.get("source_silence_family"),
                    "neighbor_ladder_join_status": neighbor.get("ladder_join_status"),
                    "neighbor_ladder_snapshot_bucket": neighbor.get("ladder_snapshot_bucket"),
                    "neighbor_source_silence_family": neighbor.get("source_silence_family"),
                    "neighbor_is_exact_feature": is_feature_row(neighbor),
                    "neighbor_is_source_silence": bool(neighbor.get("source_silence_joined")),
                    "neighbor_route_c_queue_id": neighbor.get("route_c_queue_id"),
                    "neighbor_route_c_delta_aligned_with_future": neighbor.get("route_c_delta_aligned_with_future"),
                    "neighbor_command_feature_bucket": neighbor.get("command_feature_bucket"),
                }
            )
    return pairs, summaries


def classify_target_context(feature_neighbors: int, silence_neighbors: int, alignment_share: float | None) -> str:
    if feature_neighbors >= 20 and alignment_share is not None and alignment_share >= 0.60:
        return "SOURCE_SILENCE_HAS_STRONG_SAME_SOURCE_FEATURE_ALIGNMENT_CONTEXT"
    if feature_neighbors >= 20 and alignment_share is not None and alignment_share <= 0.45:
        return "SOURCE_SILENCE_HAS_WEAK_SAME_SOURCE_FEATURE_ALIGNMENT_CONTEXT"
    if feature_neighbors >= 20:
        return "SOURCE_SILENCE_HAS_BROAD_SAME_SOURCE_FEATURE_CONTEXT"
    if feature_neighbors > 0:
        return "SOURCE_SILENCE_HAS_UNDERPOWERED_SAME_SOURCE_FEATURE_CONTEXT"
    if silence_neighbors > 0:
        return "SOURCE_SILENCE_ONLY_HAS_OTHER_SOURCE_SILENCE_NEIGHBORS"
    return "SOURCE_SILENCE_NO_SAME_SOURCE_CONTEXT"


def next_action_for_neighbor_bucket(bucket: str) -> str:
    if bucket == "SOURCE_SILENCE_HAS_STRONG_SAME_SOURCE_FEATURE_ALIGNMENT_CONTEXT":
        return "test source silence as timing/source-quality context against aligned same-source feature neighbors"
    if bucket == "SOURCE_SILENCE_HAS_WEAK_SAME_SOURCE_FEATURE_ALIGNMENT_CONTEXT":
        return "test source silence as avoid/source-quality warning against weak same-source feature neighbors"
    if bucket == "SOURCE_SILENCE_HAS_UNDERPOWERED_SAME_SOURCE_FEATURE_CONTEXT":
        return "aggregate by source family/date regime or acquire more same-source depth rows"
    if bucket == "SOURCE_SILENCE_NO_SAME_SOURCE_CONTEXT":
        return "preserve as exact source-acquisition requirement and search alternate source roots"
    return "preserve neighbor context and feed into mutation/source-acquisition design"


def build_mutation_context(
    mutations: list[dict[str, Any]],
    target_by_queue: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    contexts: list[dict[str, Any]] = []
    joins: list[dict[str, Any]] = []
    for mutation in mutations:
        queue_id = str(mutation.get("queue_id"))
        targets = target_by_queue.get(queue_id, [])
        family_counts = counter_dict([target.get("source_silence_family") for target in targets])
        if targets:
            status = "MUTATION_HAS_TRUE_SOURCE_SILENCE_CONTEXT"
            action = "split mutation design by true source-silence family and same-source neighbor support"
        else:
            status = "MUTATION_UNAFFECTED_BY_SOURCE_SILENCE_JOIN"
            action = "continue non-source-silence mutation evidence routes"
        contexts.append(
            {
                "mutation_context_id": f"SIERRA-LADDER-SOURCE-SILENCE-MUTATION-CONTEXT-{len(contexts) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "mutation_id": mutation.get("mutation_id"),
                "mutation_type": mutation.get("mutation_type"),
                "queue_id": queue_id,
                "source_silence_target_rows": len(targets),
                "source_silence_family_counts": family_counts,
                "mutation_source_silence_status": status,
                "next_same_resource_action": action,
            }
        )
        for target in targets:
            joins.append(
                {
                    "mutation_join_id": f"SIERRA-LADDER-SOURCE-SILENCE-MUTATION-JOIN-{len(joins) + 1:06d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "mutation_id": mutation.get("mutation_id"),
                    "mutation_type": mutation.get("mutation_type"),
                    "queue_id": queue_id,
                    "request_id": target.get("request_id"),
                    "source_silence_family": target.get("source_silence_family"),
                    "source_silence_status": target.get("source_silence_status"),
                    "source_symbol": target.get("source_symbol"),
                    "source_date": target.get("source_date"),
                }
            )
    return contexts, joins


def build_bucket_rows(targets: list[dict[str, Any]], summaries: list[dict[str, Any]], contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    families: list[tuple[str, list[dict[str, Any]], list[str]]] = [
        ("target_source_silence_family", targets, ["source_silence_family"]),
        ("target_by_route_queue", targets, ["route_c_queue_id", "source_silence_family"]),
        ("target_by_source_symbol", targets, ["source_symbol", "source_silence_family"]),
        ("target_neighbor_bucket", summaries, ["neighbor_bucket"]),
        ("mutation_source_silence_status", contexts, ["mutation_source_silence_status"]),
    ]
    for family, rows, keys in families:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[tuple(row.get(key) for key in keys)].append(row)
        for values, group in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
            outputs.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-BUCKET-{len(outputs) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": family,
                    "bucket_values": {key: value for key, value in zip(keys, values, strict=True)},
                    "row_count": len(group),
                    "source_symbol_counts": counter_dict([row.get("source_symbol") for row in group if row.get("source_symbol")]),
                    "route_queue_counts": counter_dict([row.get("route_c_queue_id") or row.get("queue_id") for row in group]),
                }
            )
    return outputs


def build_questions(bucket_rows: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket in bucket_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-Q-{len(rows) + 1:03d}",
                "question_family": bucket["bucket_family"],
                "bucket_values": bucket["bucket_values"],
                "row_count": bucket["row_count"],
                "question": "What same-resource source-silence, neighbor, mutation, or acquisition action follows for this full bucket?",
                "next_same_resource_action": "use target, neighbor, and mutation ledgers; do not collapse true source silence into vague future-data waiting",
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_join_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_join_result", "created"),
        (UPDATED_JOIN_LEDGER, "sierra_depth_ladder_source_silence_route_c_join_ledger", "created"),
        (TARGET_LEDGER, "sierra_depth_ladder_source_silence_target_ledger", "created"),
        (NEIGHBOR_PAIR_LEDGER, "sierra_depth_ladder_source_silence_neighbor_pair_ledger", "created"),
        (TARGET_SUMMARY_LEDGER, "sierra_depth_ladder_source_silence_target_summary_ledger", "created"),
        (MUTATION_CONTEXT_LEDGER, "sierra_depth_ladder_source_silence_mutation_context_ledger", "created"),
        (MUTATION_JOIN_LEDGER, "sierra_depth_ladder_source_silence_mutation_join_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_join_summary", "created"),
    ]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    known = {relative(path) for path, _, _ in artifacts}
    manifest["artifacts"] = [item for item in manifest["artifacts"] if item.get("path") not in known]
    for path, artifact_type, status in artifacts:
        manifest["artifacts"].append({"path": relative(path), "type": artifact_type, "status": status})
    manifest["last_updated_utc"] = generated_utc
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def append_sprint_ledger(generated_utc: str, counts: dict[str, int], family_counts: dict[str, int]) -> None:
    event = {
        "ts_utc": generated_utc,
        "event_type": "sierra_depth_ladder_source_silence_join",
        "status": "done",
        "route": "source_silence_route_c_mutation_neighbor_join",
        "details": "Joined true source-silence statuses into Route C denominator, same-source neighbor context, and mutation rows.",
        "counts": counts,
        "source_silence_family_counts": family_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(UPDATED_JOIN_LEDGER),
            relative(TARGET_LEDGER),
            relative(NEIGHBOR_PAIR_LEDGER),
            relative(TARGET_SUMMARY_LEDGER),
            relative(MUTATION_CONTEXT_LEDGER),
            relative(MUTATION_JOIN_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], family_counts: dict[str, int], neighbor_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Depth Ladder Source Silence Join",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: source-silence Route C/mutation/neighbor context only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Source Silence Families", ""])
    for key, value in sorted(family_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Neighbor Buckets", ""])
    for key, value in sorted(neighbor_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Use true source-silence status in mutation design instead of stale no-sample labels.",
            "- Source-silence rows with weak/underpowered neighbor context should feed acquisition and avoid-context tests.",
            "- Continue exact missing `.depth` source-date search; source silence is a current-source fact, not a future-data excuse.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    effective_rows = read_jsonl(EFFECTIVE_JOIN_LEDGER)
    silence_rows = read_jsonl(SOURCE_SILENCE_LEDGER)
    mutations = read_jsonl(MUTATION_LEDGER)
    silence_by_request = {str(row["request_id"]): row for row in silence_rows}

    updated_rows = build_updated_join_rows(effective_rows, silence_by_request)
    targets = build_target_rows(updated_rows)
    neighbor_pairs, target_summaries = build_neighbor_pairs(updated_rows, targets)
    target_by_queue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for target in targets:
        target_by_queue[str(target.get("route_c_queue_id"))].append(target)
    mutation_contexts, mutation_joins = build_mutation_context(mutations, target_by_queue)
    bucket_rows = build_bucket_rows(targets, target_summaries, mutation_contexts)
    family_counts = counter_dict([target.get("source_silence_family") for target in targets])
    neighbor_counts = counter_dict([row.get("neighbor_bucket") for row in target_summaries])

    counts = {
        "input_effective_join_rows": len(effective_rows),
        "input_source_silence_rows": len(silence_rows),
        "updated_join_rows": len(updated_rows),
        "target_rows": len(targets),
        "neighbor_pair_rows": len(neighbor_pairs),
        "target_summary_rows": len(target_summaries),
        "mutation_input_rows": len(mutations),
        "mutation_context_rows": len(mutation_contexts),
        "mutation_source_silence_join_rows": len(mutation_joins),
        "bucket_rows": len(bucket_rows),
        "question_rows": 0,
    }
    question_rows = build_questions(bucket_rows, counts)
    counts["question_rows"] = len(question_rows)

    write_jsonl(UPDATED_JOIN_LEDGER, updated_rows)
    write_jsonl(TARGET_LEDGER, targets)
    write_jsonl(NEIGHBOR_PAIR_LEDGER, neighbor_pairs)
    write_jsonl(TARGET_SUMMARY_LEDGER, target_summaries)
    write_jsonl(MUTATION_CONTEXT_LEDGER, mutation_contexts)
    write_jsonl(MUTATION_JOIN_LEDGER, mutation_joins)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    result = {
        "schema": "sierra_depth_ladder_source_silence_join_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_SOURCE_SILENCE_ROUTE_C_MUTATION_JOIN",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "source_silence_family_counts": family_counts,
        "neighbor_bucket_counts": neighbor_counts,
        "mutation_source_silence_status_counts": counter_dict(
            [row.get("mutation_source_silence_status") for row in mutation_contexts]
        ),
        "not_completion": "This joins source-silence context but does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "turn source-silence mutation statuses into exact mutation design updates",
            "test same-source neighbor support for true source-silence contexts",
            "continue exact missing .depth source-date acquisition and source-silence proxy construction",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, family_counts)
    write_summary(generated_utc, counts, family_counts, neighbor_counts)
    print(json.dumps({"ok": True, "counts": counts, "family_counts": family_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
