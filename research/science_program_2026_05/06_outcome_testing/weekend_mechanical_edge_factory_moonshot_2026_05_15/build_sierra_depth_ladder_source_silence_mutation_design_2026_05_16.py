#!/usr/bin/env python3
"""Convert source-silence mutation context into explicit design updates."""

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

MUTATION_CONTEXT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_CONTEXT_LEDGER_{STAMP}.jsonl"
MUTATION_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_JOIN_LEDGER_{STAMP}.jsonl"
TARGET_SUMMARY_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_TARGET_SUMMARY_LEDGER_{STAMP}.jsonl"
MUTATION_LEDGER = ROUTE_DIR / f"TICK_M15_TRANSFER_HYPOTHESIS_MUTATION_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_DESIGN_RESULT_{STAMP}.json"
DESIGN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_DESIGN_LEDGER_{STAMP}.jsonl"
EVIDENCE_JOIN_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_EVIDENCE_JOIN_LEDGER_{STAMP}.jsonl"
QUEUE_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_QUEUE_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_DESIGN_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra ladder source-silence mutation design updates; source-control/design evidence only, "
    "with no strategy validation, trade outcome, R/PnL, expectancy, live-readiness, or live deployment"
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


def design_status(mutation_type: str, affected: bool, neighbor_counts: dict[str, int]) -> str:
    if not affected:
        return "MUTATION_DESIGN_UNAFFECTED_BY_SOURCE_SILENCE"
    has_strong = neighbor_counts.get("SOURCE_SILENCE_HAS_STRONG_SAME_SOURCE_FEATURE_ALIGNMENT_CONTEXT", 0) > 0
    has_underpowered = neighbor_counts.get("SOURCE_SILENCE_HAS_UNDERPOWERED_SAME_SOURCE_FEATURE_CONTEXT", 0) > 0
    has_no_context = neighbor_counts.get("SOURCE_SILENCE_NO_SAME_SOURCE_CONTEXT", 0) > 0
    if mutation_type == "avoid_filter_mutation":
        return "SOURCE_SILENCE_AVOID_FILTER_DESIGN_CANDIDATE"
    if mutation_type == "source_proxy_mutation":
        return "SOURCE_SILENCE_SOURCE_PROXY_ACQUISITION_DESIGN"
    if mutation_type == "cost_filter_mutation":
        return "SOURCE_SILENCE_COST_AND_SOURCE_QUALITY_DESIGN"
    if mutation_type == "horizon_router_mutation":
        return "SOURCE_SILENCE_HORIZON_ROUTER_SPLIT_DESIGN"
    if mutation_type == "entry_geometry_mutation":
        return "SOURCE_SILENCE_ENTRY_TIMING_GUARD_DESIGN"
    if mutation_type == "deconcentration_mutation":
        return "SOURCE_SILENCE_DECONCENTRATION_DESIGN"
    if has_no_context:
        return "SOURCE_SILENCE_ACQUISITION_ONLY_DESIGN"
    if has_strong and has_underpowered:
        return "SOURCE_SILENCE_MIXED_NEIGHBOR_SUPPORT_DESIGN"
    return "SOURCE_SILENCE_MUTATION_SPLIT_DESIGN"


def proposed_rule_for_status(status: str) -> str:
    rules = {
        "MUTATION_DESIGN_UNAFFECTED_BY_SOURCE_SILENCE": "No source-silence-specific rule; continue existing mutation evidence route.",
        "SOURCE_SILENCE_AVOID_FILTER_DESIGN_CANDIDATE": "If event-boundary source silence occurs, evaluate as avoid/source-quality filter against same-source neighbor controls before any entry logic use.",
        "SOURCE_SILENCE_SOURCE_PROXY_ACQUISITION_DESIGN": "Route source-silence rows to exact .depth acquisition and same-source proxy validation before treating missing ladder data as neutral.",
        "SOURCE_SILENCE_COST_AND_SOURCE_QUALITY_DESIGN": "Treat event-boundary source silence as a source-quality/cost-realism flag and test whether it coincides with sparse/liquidity-fragile execution contexts.",
        "SOURCE_SILENCE_HORIZON_ROUTER_SPLIT_DESIGN": "Split horizon-router hypotheses by source-silence family and neighbor support instead of mixing no-record windows with exact ladder windows.",
        "SOURCE_SILENCE_ENTRY_TIMING_GUARD_DESIGN": "Do not derive event-boundary entry ladder features from source-silent windows; require alternate timing descriptor or same-source proxy support.",
        "SOURCE_SILENCE_DECONCENTRATION_DESIGN": "Use source-silence family and neighbor support as a deconcentration axis for Route C residual queues.",
        "SOURCE_SILENCE_ACQUISITION_ONLY_DESIGN": "Preserve as exact source-acquisition requirement until same-source or alternate-root evidence exists.",
        "SOURCE_SILENCE_MIXED_NEIGHBOR_SUPPORT_DESIGN": "Split source-silence rows by strong versus underpowered same-source neighbor support before scoring any mutation.",
        "SOURCE_SILENCE_MUTATION_SPLIT_DESIGN": "Split mutation by source-silence family and same-source neighbor bucket before interpretation.",
    }
    return rules.get(status, "Manual source-silence mutation design review required.")


def build_evidence_joins(
    mutation_joins: list[dict[str, Any]],
    target_summary_by_request: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for join in mutation_joins:
        summary = target_summary_by_request.get(str(join.get("request_id")), {})
        rows.append(
            {
                "evidence_join_id": f"SIERRA-LADDER-SOURCE-SILENCE-MUTATION-EVIDENCE-{len(rows) + 1:06d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                **join,
                "target_neighbor_bucket": summary.get("neighbor_bucket"),
                "same_source_neighbor_rows": summary.get("same_source_neighbor_rows"),
                "same_source_exact_feature_neighbor_rows": summary.get("same_source_exact_feature_neighbor_rows"),
                "feature_neighbor_route_alignment_share": summary.get("feature_neighbor_route_alignment_share"),
                "feature_neighbor_route_alignment_n": summary.get("feature_neighbor_route_alignment_n"),
            }
        )
    return rows


def build_design_rows(
    mutation_contexts: list[dict[str, Any]],
    mutations_by_id: dict[str, dict[str, Any]],
    evidence_by_mutation: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for context in mutation_contexts:
        mutation_id = str(context.get("mutation_id"))
        mutation = mutations_by_id.get(mutation_id, {})
        evidence = evidence_by_mutation.get(mutation_id, [])
        neighbor_counts = counter_dict([row.get("target_neighbor_bucket") for row in evidence])
        affected = context.get("mutation_source_silence_status") == "MUTATION_HAS_TRUE_SOURCE_SILENCE_CONTEXT"
        status = design_status(str(context.get("mutation_type")), affected, neighbor_counts)
        rows.append(
            {
                "design_id": f"SIERRA-LADDER-SOURCE-SILENCE-MUTATION-DESIGN-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "mutation_id": mutation_id,
                "mutation_type": context.get("mutation_type"),
                "queue_id": context.get("queue_id"),
                "symbol": mutation.get("symbol"),
                "session_bucket": mutation.get("session_bucket"),
                "primitive_flag": mutation.get("primitive_flag"),
                "original_action": mutation.get("action"),
                "source_silence_target_rows": context.get("source_silence_target_rows"),
                "source_silence_family_counts": context.get("source_silence_family_counts"),
                "neighbor_bucket_counts": neighbor_counts,
                "mutation_source_silence_status": context.get("mutation_source_silence_status"),
                "source_silence_design_status": status,
                "proposed_branch_local_rule": proposed_rule_for_status(status),
                "required_next_evidence": required_next_evidence(status),
                "live_effect": False,
                "next_same_resource_action": next_action_for_design(status),
            }
        )
    return rows


def required_next_evidence(status: str) -> str:
    if status == "MUTATION_DESIGN_UNAFFECTED_BY_SOURCE_SILENCE":
        return "none for source-silence branch; continue other mutation packets"
    if "ACQUISITION" in status:
        return "exact .depth source-date recovery, alternate-root search, or same-source proxy sufficiency proof"
    if "AVOID" in status:
        return "same-denominator source-silence versus exact-feature neighbor/control comparison before avoid-filter scoring"
    return "same-denominator mutation split with source-silence family and neighbor bucket controls"


def next_action_for_design(status: str) -> str:
    if status == "MUTATION_DESIGN_UNAFFECTED_BY_SOURCE_SILENCE":
        return "leave unchanged in source-silence branch"
    return "materialize mutation split/control packet using the design row as the branch-local rule sketch"


def build_queue_rows(design_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in design_rows:
        grouped[str(row.get("queue_id"))].append(row)
    rows: list[dict[str, Any]] = []
    for queue_id, group in sorted(grouped.items()):
        rows.append(
            {
                "queue_design_id": f"SIERRA-LADDER-SOURCE-SILENCE-QUEUE-DESIGN-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "queue_id": queue_id,
                "design_rows": len(group),
                "affected_design_rows": sum(1 for row in group if row.get("mutation_source_silence_status") == "MUTATION_HAS_TRUE_SOURCE_SILENCE_CONTEXT"),
                "source_silence_design_status_counts": counter_dict([row.get("source_silence_design_status") for row in group]),
                "mutation_type_counts": counter_dict([row.get("mutation_type") for row in group]),
                "next_same_resource_action": "run queue-level source-silence split/control or preserve unaffected queue branch",
            }
        )
    return rows


def build_bucket_rows(design_rows: list[dict[str, Any]], queue_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    families: list[tuple[str, list[dict[str, Any]], list[str]]] = [
        ("design_status", design_rows, ["source_silence_design_status"]),
        ("design_status_by_mutation_type", design_rows, ["mutation_type", "source_silence_design_status"]),
        ("design_status_by_queue", design_rows, ["queue_id", "source_silence_design_status"]),
        ("queue_affected_rows", queue_rows, ["affected_design_rows"]),
    ]
    for family, rows, keys in families:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[tuple(row.get(key) for key in keys)].append(row)
        for values, group in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
            outputs.append(
                {
                    "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MUTATION-BUCKET-{len(outputs) + 1:05d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "bucket_family": family,
                    "bucket_values": {key: value for key, value in zip(keys, values, strict=True)},
                    "row_count": len(group),
                    "queue_counts": counter_dict([row.get("queue_id") for row in group]),
                    "mutation_type_counts": counter_dict([row.get("mutation_type") for row in group if row.get("mutation_type")]),
                }
            )
    return outputs


def build_questions(bucket_rows: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket in bucket_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MUTATION-Q-{len(rows) + 1:03d}",
                "question_family": bucket["bucket_family"],
                "bucket_values": bucket["bucket_values"],
                "row_count": bucket["row_count"],
                "question": "What source-silence mutation split, control packet, or acquisition path follows from this full bucket?",
                "next_same_resource_action": "materialize the design row into a source-safe control/split packet; do not treat as forward-data waiting",
                "counts_context": counts,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_mutation_design_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_mutation_design_result", "created"),
        (DESIGN_LEDGER, "sierra_depth_ladder_source_silence_mutation_design_ledger", "created"),
        (EVIDENCE_JOIN_LEDGER, "sierra_depth_ladder_source_silence_mutation_evidence_join_ledger", "created"),
        (QUEUE_LEDGER, "sierra_depth_ladder_source_silence_mutation_queue_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_mutation_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_mutation_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_mutation_design_summary", "created"),
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
        "event_type": "sierra_depth_ladder_source_silence_mutation_design",
        "status": "done",
        "route": "source_silence_mutation_design_updates",
        "details": "Converted source-silence mutation contexts into explicit branch-local design statuses and rule sketches.",
        "counts": counts,
        "source_silence_design_status_counts": status_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(DESIGN_LEDGER),
            relative(EVIDENCE_JOIN_LEDGER),
            relative(QUEUE_LEDGER),
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
        "# Sierra Depth Ladder Source Silence Mutation Design",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: branch-local mutation design only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Design Status Counts", ""])
    for key, value in sorted(status_counts.items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Materialize affected design rows into source-silence split/control packets.",
            "- Keep unaffected mutation rows in the denominator instead of dropping them.",
            "- Treat the rules as branch-local proposals only until a separate validation/promotion dossier exists.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    mutation_contexts = read_jsonl(MUTATION_CONTEXT_LEDGER)
    mutation_joins = read_jsonl(MUTATION_JOIN_LEDGER)
    target_summaries = read_jsonl(TARGET_SUMMARY_LEDGER)
    mutations = read_jsonl(MUTATION_LEDGER)
    target_summary_by_request = {str(row["request_id"]): row for row in target_summaries}
    mutations_by_id = {str(row["mutation_id"]): row for row in mutations}

    evidence_rows = build_evidence_joins(mutation_joins, target_summary_by_request)
    evidence_by_mutation: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evidence_rows:
        evidence_by_mutation[str(row.get("mutation_id"))].append(row)
    design_rows = build_design_rows(mutation_contexts, mutations_by_id, evidence_by_mutation)
    queue_rows = build_queue_rows(design_rows)
    bucket_rows = build_bucket_rows(design_rows, queue_rows)
    status_counts = counter_dict([row.get("source_silence_design_status") for row in design_rows])
    counts = {
        "mutation_context_input_rows": len(mutation_contexts),
        "mutation_source_silence_join_input_rows": len(mutation_joins),
        "target_summary_input_rows": len(target_summaries),
        "design_rows": len(design_rows),
        "affected_design_rows": sum(1 for row in design_rows if row.get("mutation_source_silence_status") == "MUTATION_HAS_TRUE_SOURCE_SILENCE_CONTEXT"),
        "unaffected_design_rows": sum(1 for row in design_rows if row.get("mutation_source_silence_status") != "MUTATION_HAS_TRUE_SOURCE_SILENCE_CONTEXT"),
        "evidence_join_rows": len(evidence_rows),
        "queue_rows": len(queue_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": 0,
    }
    question_rows = build_questions(bucket_rows, counts)
    counts["question_rows"] = len(question_rows)

    write_jsonl(DESIGN_LEDGER, design_rows)
    write_jsonl(EVIDENCE_JOIN_LEDGER, evidence_rows)
    write_jsonl(QUEUE_LEDGER, queue_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    result = {
        "schema": "sierra_depth_ladder_source_silence_mutation_design_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MUTATION_DESIGN_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "source_silence_design_status_counts": status_counts,
        "not_completion": "This mutation design packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "materialize source-silence split/control packets from affected design rows",
            "test same-source neighbor support for source-silence families",
            "continue exact missing .depth acquisition and no-clear earlier-history search",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(generated_utc)
    append_sprint_ledger(generated_utc, counts, status_counts)
    write_summary(generated_utc, counts, status_counts)
    print(json.dumps({"ok": True, "counts": counts, "status_counts": status_counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
