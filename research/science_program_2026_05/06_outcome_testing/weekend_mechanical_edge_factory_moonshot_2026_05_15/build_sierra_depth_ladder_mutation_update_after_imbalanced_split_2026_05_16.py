#!/usr/bin/env python3
"""Update Route C mutation rows with imbalanced ladder split context."""

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

MUTATION_LEDGER = ROUTE_DIR / f"TICK_M15_TRANSFER_HYPOTHESIS_MUTATION_LEDGER_{STAMP}.jsonl"
IMBALANCED_SPLIT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_AFTER_FALLBACK_ROW_LEDGER_{STAMP}.jsonl"
IMBALANCED_RESULT = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_IMBALANCED_AFTER_FALLBACK_RESULT_{STAMP}.json"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_MUTATION_AFTER_IMBALANCED_RESULT_{STAMP}.json"
UPDATED_MUTATION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_MUTATION_AFTER_IMBALANCED_LEDGER_{STAMP}.jsonl"
MUTATION_IMBALANCED_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_MUTATION_AFTER_IMBALANCED_JOIN_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_MUTATION_AFTER_IMBALANCED_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_MUTATION_AFTER_IMBALANCED_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_MUTATION_AFTER_IMBALANCED_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Route C mutation rows updated with Sierra .depth imbalanced ladder split "
    "context; descriptor/control evidence only, with no strategy validation, "
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


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key)) for row in rows).items()))


def classify_mutation_update(mutation: dict[str, Any], split_rows: list[dict[str, Any]]) -> tuple[str, str, str]:
    if not split_rows:
        return (
            "NO_IMBALANCED_LADDER_CONTEXT_IN_CURRENT_SPLIT",
            "mutation remains open under its prior Route C transfer diagnostics",
            str(mutation.get("action")),
        )

    split_counts = Counter(str(row.get("combined_split_bucket")) for row in split_rows)
    mutation_type = str(mutation.get("mutation_type"))
    underpowered = sum(count for bucket, count in split_counts.items() if "UNDERPOWERED" in bucket)
    divergent = split_counts.get("DIVERGENT_COMMAND_LADDER_SPLIT_REQUIRED", 0)
    weakened = split_counts.get("AGREEING_COMMAND_LADDER_BUT_ROUTE_OR_CONTROL_WEAKENED", 0)
    isolated = split_counts.get("AGREEING_IMBALANCE_WITH_NO_NEIGHBOR_SUPPORT", 0)
    supported = split_counts.get("AGREEING_ROUTE_ALIGNED_IMBALANCE_WITH_NEIGHBOR_SUPPORT", 0)

    if mutation_type == "avoid_filter_mutation":
        status = "CURRENT_DATA_SUPPORTS_AVOID_OR_SPLIT_DESIGN_NOT_UNIFIED_SIGNAL"
        action = "design avoid/split rule candidates for divergent, weakened, isolated, and underpowered ladder contexts separately"
    elif mutation_type == "source_proxy_mutation":
        status = "SOURCE_PROXY_MUTATION_REFINED_BY_DEPTH_CONTEXT_REQUIREMENTS"
        action = "separate exact-source acquisition requirements from fallback/no-event and underpowered proxy contexts"
    elif mutation_type == "cost_filter_mutation":
        status = "COST_FILTER_MUTATION_REFINED_BY_LADDER_LIQUIDITY_CONTEXT"
        action = "test cost/friction filters only after separating underpowered and weakened ladder contexts"
    elif mutation_type == "broad_family_challenger_mutation":
        status = "BROAD_CHALLENGER_MUTATION_FRAGMENTED_BY_LADDER_SPLITS"
        action = "do not carry the queue as one broad challenger; split into ladder support, divergence, isolated, and underpowered subfamilies"
    elif mutation_type == "robustness_mutation":
        status = "ROBUSTNESS_MUTATION_REQUIRES_COMMAND_LADDER_SPLIT"
        action = "stress each command-ladder/fallback-neighbor split independently before any broader robustness claim"
    elif mutation_type == "risk_router_mutation":
        status = "RISK_ROUTER_MUTATION_REQUIRES_SOURCE_CONTEXT_SPLIT"
        action = "route risk only as a prospective design branch after exact source and underpower gaps are separated"
    else:
        status = "MUTATION_REQUIRES_IMBALANCED_SPLIT_CONTEXT"
        action = "carry imbalanced split context into the next current-data mutation packet"

    if supported == len(split_rows):
        interpretation = "all imbalanced context rows are route-aligned with neighbor support"
    elif divergent or weakened or isolated:
        interpretation = (
            f"fragmented context: divergent={divergent}, weakened={weakened}, "
            f"isolated={isolated}, underpowered={underpowered}, supported={supported}"
        )
    elif underpowered:
        interpretation = f"underpowered context dominates current imbalanced split rows ({underpowered}/{len(split_rows)})"
    else:
        interpretation = "mixed descriptor context requires split-preserving mutation design"
    return status, interpretation, action


def build_mutation_rows(
    mutations: list[dict[str, Any]],
    split_by_queue: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    updated: list[dict[str, Any]] = []
    joins: list[dict[str, Any]] = []
    for idx, mutation in enumerate(mutations, start=1):
        queue_id = str(mutation.get("queue_id"))
        split_rows = split_by_queue.get(queue_id, [])
        status, interpretation, updated_action = classify_mutation_update(mutation, split_rows)
        split_counts = count_by(split_rows, "combined_split_bucket")
        neighbor_counts = count_by(split_rows, "neighbor_split_bucket")
        fallback_counts = count_by(split_rows, "fallback_context_bucket")
        out = dict(mutation)
        out.update(
            {
                "mutation_update_id": f"SIERRA-DEPTH-LADDER-MUTATION-AFTER-IMBALANCED-{idx:05d}",
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "imbalanced_split_rows": len(split_rows),
                "imbalanced_request_ids": sorted(str(row.get("request_id")) for row in split_rows),
                "imbalanced_combined_split_bucket_counts": split_counts,
                "imbalanced_neighbor_split_bucket_counts": neighbor_counts,
                "imbalanced_fallback_context_bucket_counts": fallback_counts,
                "mutation_current_data_update_status": status,
                "mutation_current_data_interpretation": interpretation,
                "updated_same_resource_action": updated_action,
                "status": "open_same_resource_current_data_updated"
                if split_rows
                else "open_same_resource_or_next_packet",
            }
        )
        updated.append(out)
        for split in split_rows:
            joins.append(
                {
                    "mutation_imbalanced_join_id": f"SIERRA-DEPTH-LADDER-MUTATION-IMBALANCED-JOIN-{len(joins) + 1:06d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "mutation_id": mutation.get("mutation_id"),
                    "mutation_type": mutation.get("mutation_type"),
                    "mutation_queue_id": queue_id,
                    "mutation_update_status": status,
                    "split_row_id": split.get("split_row_id"),
                    "request_id": split.get("request_id"),
                    "source_symbol": split.get("source_symbol"),
                    "source_date": split.get("source_date"),
                    "route_c_symbol": split.get("route_c_symbol"),
                    "horizon_id": split.get("horizon_id"),
                    "route_c_primitive_flag": split.get("route_c_primitive_flag"),
                    "combined_split_bucket": split.get("combined_split_bucket"),
                    "command_ladder_sign_relation": split.get("command_ladder_sign_relation"),
                    "route_alignment_descriptor": split.get("route_alignment_descriptor"),
                    "neighbor_split_bucket": split.get("neighbor_split_bucket"),
                    "fallback_context_bucket": split.get("fallback_context_bucket"),
                    "requirement_context_bucket": split.get("requirement_context_bucket"),
                    "next_same_resource_action": split.get("next_same_resource_action"),
                }
            )
    return updated, joins


def build_bucket_rows(updated: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families: list[tuple[str, list[str]]] = [
        ("mutation_update_status", ["mutation_current_data_update_status"]),
        ("mutation_type", ["mutation_type"]),
        ("queue_id", ["queue_id"]),
        ("queue_update_status", ["queue_id", "mutation_current_data_update_status"]),
        ("mutation_type_update_status", ["mutation_type", "mutation_current_data_update_status"]),
    ]
    outputs: list[dict[str, Any]] = []
    for family, keys in families:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in updated:
            grouped[tuple(row.get(key) for key in keys)].append(row)
        for values, group in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
            outputs.append(
                {
                    "bucket_id": f"SIERRA-DEPTH-LADDER-MUTATION-AFTER-IMBALANCED-BUCKET-{len(outputs) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "group_family": family,
                    "group_keys": keys,
                    "group_values": {key: value for key, value in zip(keys, values, strict=True)},
                    "row_count": len(group),
                    "mutation_ids": sorted(str(row.get("mutation_id")) for row in group),
                    "queue_counts": count_by(group, "queue_id"),
                    "mutation_type_counts": count_by(group, "mutation_type"),
                    "updated_status_counts": count_by(group, "mutation_current_data_update_status"),
                    "imbalanced_split_rows_sum": sum(int(row.get("imbalanced_split_rows") or 0) for row in group),
                    "next_same_resource_action": group_action(group),
                }
            )
    return outputs


def group_action(group: list[dict[str, Any]]) -> str:
    statuses = Counter(str(row.get("mutation_current_data_update_status")) for row in group)
    if statuses.get("NO_IMBALANCED_LADDER_CONTEXT_IN_CURRENT_SPLIT") == len(group):
        return "preserve unchanged mutation rows and continue with other current-data packets"
    if any("FRAGMENTED" in status or "SPLIT" in status for status in statuses):
        return "split mutation design by imbalanced ladder context before any broader challenger interpretation"
    if any("UNDERPOWERED" in str(row.get("mutation_current_data_interpretation")) for row in group):
        return "seek additional same-source/source-date rows or preserve underpowered caveat"
    return "carry refined mutation status into next same-resource packet"


def build_question_rows(updated: list[dict[str, Any]], joins: list[dict[str, Any]]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    affected = [row for row in updated if row.get("imbalanced_split_rows")]
    for status, count in sorted(Counter(str(row.get("mutation_current_data_update_status")) for row in affected).items()):
        rows = [row for row in affected if row.get("mutation_current_data_update_status") == status]
        questions.append(
            {
                "question_id": f"SIERRA-DEPTH-LADDER-MUTATION-AFTER-IMBALANCED-Q-{len(questions) + 1:03d}",
                "question_family": "affected_mutation_status",
                "bucket": status,
                "row_count": count,
                "mutation_ids": sorted(str(row.get("mutation_id")) for row in rows),
                "queue_ids": sorted(set(str(row.get("queue_id")) for row in rows)),
                "question": f"What exact same-resource mutation design follows for all {count} rows now classified as {status}?",
                "next_same_resource_action": group_action(rows),
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    unaffected = [row for row in updated if not row.get("imbalanced_split_rows")]
    questions.append(
        {
            "question_id": f"SIERRA-DEPTH-LADDER-MUTATION-AFTER-IMBALANCED-Q-{len(questions) + 1:03d}",
            "question_family": "unaffected_mutation_rows",
            "bucket": "NO_IMBALANCED_LADDER_CONTEXT_IN_CURRENT_SPLIT",
            "row_count": len(unaffected),
            "mutation_ids": sorted(str(row.get("mutation_id")) for row in unaffected),
            "question": "Which unchanged mutation rows still need current-data packets outside the imbalanced ladder split?",
            "next_same_resource_action": "continue mutation rows answerable from current data after exact source acquisition and earlier-book repair/proxy work",
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "safe_flags": SAFE_FLAGS,
        }
    )
    if not joins:
        raise RuntimeError("expected imbalanced mutation join rows")
    return questions


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_mutation_after_imbalanced_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_mutation_after_imbalanced_result", "created"),
        (UPDATED_MUTATION_LEDGER, "sierra_depth_ladder_mutation_after_imbalanced_ledger", "created"),
        (MUTATION_IMBALANCED_JOIN_LEDGER, "sierra_depth_ladder_mutation_after_imbalanced_join_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_mutation_after_imbalanced_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_mutation_after_imbalanced_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_mutation_after_imbalanced_summary", "created"),
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
        "event_type": "sierra_depth_ladder_mutation_after_imbalanced_update",
        "status": "done",
        "route": "sierra_depth_ladder_mutation_after_imbalanced_update",
        "details": "Preserved all Route C mutation rows and joined the imbalanced ladder split to affected mutation families.",
        "counts": counts,
        "mutation_update_status_counts": status_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(UPDATED_MUTATION_LEDGER),
            relative(MUTATION_IMBALANCED_JOIN_LEDGER),
            relative(BUCKET_LEDGER),
            relative(QUESTION_LEDGER),
            relative(SUMMARY_PATH),
        ],
        "commands": [f"py -3 {relative(Path(__file__).resolve())}"],
        "safe_flags": SAFE_FLAGS,
    }
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=False) + "\n")


def write_summary(generated_utc: str, counts: dict[str, int], status_counts: dict[str, int]) -> None:
    lines = [
        "# Sierra Depth Ladder Mutation Update After Imbalanced Split",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: mutation-row refinement only. No validation, R/PnL, expectancy, live-readiness, promotion, or completion claim.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Mutation Update Status", ""])
    for key, value in sorted(status_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- The full `54`-row Route C mutation ledger is preserved.",
            "- The `27` join rows are descriptor/control joins from `9` imbalanced ladder rows across `3` mutation rows for each of two affected queue IDs.",
            "- This packet refines mutation design status only; it does not claim edge, performance, validation, or live readiness.",
            "",
            "## Next Same-Resource Work",
            "",
            "- Continue exact missing `.depth` source-date acquisition and earlier-book repair/proxy work.",
            "- Use split-aware mutation statuses only as design constraints for future source-safe packets.",
            "- Continue current-data mutation rows outside imbalanced ladder context.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    mutations = read_jsonl(MUTATION_LEDGER)
    split_rows = read_jsonl(IMBALANCED_SPLIT_LEDGER)
    split_result = json.loads(IMBALANCED_RESULT.read_text(encoding="utf-8"))
    split_by_queue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in split_rows:
        split_by_queue[str(row.get("route_c_queue_id"))].append(row)

    updated_rows, join_rows = build_mutation_rows(mutations, split_by_queue)
    bucket_rows = build_bucket_rows(updated_rows)
    question_rows = build_question_rows(updated_rows, join_rows)
    status_counts = count_by(updated_rows, "mutation_current_data_update_status")
    counts = {
        "input_mutation_rows": len(mutations),
        "updated_mutation_rows": len(updated_rows),
        "input_imbalanced_split_rows": len(split_rows),
        "input_imbalanced_result_split_bucket_total": sum(split_result["combined_split_bucket_counts"].values()),
        "affected_mutation_rows": sum(1 for row in updated_rows if row.get("imbalanced_split_rows")),
        "unaffected_mutation_rows": sum(1 for row in updated_rows if not row.get("imbalanced_split_rows")),
        "affected_queue_ids": len({row.get("queue_id") for row in updated_rows if row.get("imbalanced_split_rows")}),
        "mutation_imbalanced_join_rows": len(join_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
    }

    write_jsonl(UPDATED_MUTATION_LEDGER, updated_rows)
    write_jsonl(MUTATION_IMBALANCED_JOIN_LEDGER, join_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    result = {
        "schema": "sierra_depth_ladder_mutation_after_imbalanced_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "ROUTE_C_MUTATION_REFINEMENT_AFTER_IMBALANCED_LADDER_SPLIT_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "mutation_update_status_counts": status_counts,
        "affected_queue_ids": sorted({str(row.get("queue_id")) for row in updated_rows if row.get("imbalanced_split_rows")}),
        "next_same_resource_work": [
            "continue exact missing .depth source-date acquisition and earlier-book repair/proxy work",
            "preserve split-aware mutation statuses as design constraints only",
            "continue current-data mutation rows outside imbalanced ladder context",
        ],
        "not_completion": "This packet refines mutation rows and does not complete the 60-hour moonshot objective.",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, status_counts)
    write_summary(generated_utc, counts, status_counts)
    print(json.dumps({"ok": True, "counts": counts, "status_counts": status_counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
