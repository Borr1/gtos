#!/usr/bin/env python3
"""Build source-safe proxy controls for unrepaired source-silence micro-clusters."""

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
SOURCE_SEARCH_REQUEST_REPLAY_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_SEARCH_REQUEST_REPLAY_LEDGER_{STAMP}.jsonl"
SOURCE_SEARCH_DECISION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_SOURCE_SEARCH_DECISION_LEDGER_{STAMP}.jsonl"
MICROCLUSTER_REQUIREMENT_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_REQUIREMENT_LEDGER_{STAMP}.jsonl"

RESULT_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_CONTROL_RESULT_{STAMP}.json"
TARGET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_TARGET_LEDGER_{STAMP}.jsonl"
PAIR_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_PAIR_LEDGER_{STAMP}.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_CONTROL_LEDGER_{STAMP}.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_BUCKET_LEDGER_{STAMP}.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_QUESTION_LEDGER_{STAMP}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"SIERRA_DEPTH_LADDER_SOURCE_SILENCE_MICROCLUSTER_PROXY_CONTROL_SUMMARY_{STAMP}.md"
MANIFEST_PATH = ROUTE_DIR / f"OUTPUT_MANIFEST_{SOURCE_STAMP}.json"
SPRINT_LEDGER = ROUTE_DIR / f"SPRINT_OPERATING_LEDGER_{SOURCE_STAMP}.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

EVIDENCE_BOUNDARY = (
    "Sierra source-silence micro-cluster source-safe proxy controls only; "
    "descriptor/source-control evidence with no strategy validation, trade "
    "outcome, R/PnL, expectancy, live-readiness, or live deployment"
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


def route_alignment_share(rows: Iterable[dict[str, Any]]) -> tuple[float | None, int]:
    values = [value for row in rows if (value := bool_value(row.get("route_c_delta_aligned_with_future"))) is not None]
    return share(values), len(values)


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "request_id",
        "route_c_queue_id",
        "route_c_symbol",
        "route_c_primitive_flag",
        "route_c_mechanism_family",
        "horizon_id",
        "source_symbol",
        "source_proxy_family",
        "source_date",
        "proxy_relation",
        "command_feature_bucket",
        "source_silence_status",
        "source_silence_family",
        "route_c_delta_aligned_with_future",
        "route_c_future_change_per_current_range",
        "route_c_future_abs_change",
        "bar_start_utc",
        "event15_start_utc",
        "canonical_m15_close_utc",
    ]
    return {key: row.get(key) for key in keys}


def row_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    alignment, alignment_n = route_alignment_share(rows)
    future_change = [
        value for row in rows
        if (value := safe_float(row.get("route_c_future_change_per_current_range"))) is not None
    ]
    return {
        "n": len(rows),
        "unique_request_count": len({str(row.get("request_id")) for row in rows if row.get("request_id")}),
        "route_alignment_share": alignment,
        "route_alignment_n": alignment_n,
        "mean_route_c_future_change_per_current_range": mean(future_change),
        "source_symbol_counts": counter_dict(row.get("source_symbol") for row in rows),
        "source_date_count": len({str(row.get("source_date")) for row in rows if row.get("source_date")}),
        "route_queue_counts": counter_dict(row.get("route_c_queue_id") for row in rows),
        "command_feature_bucket_counts": counter_dict(row.get("command_feature_bucket") for row in rows),
        "candidate_replay_bucket_counts": counter_dict(row.get("candidate_replay_bucket") for row in rows),
        "source_search_decision_bucket_counts": counter_dict(row.get("source_search_decision_bucket") for row in rows),
    }


def build_targets(
    replay_rows: list[dict[str, Any]],
    decisions_by_requirement: dict[str, dict[str, Any]],
    source_join_by_request: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for replay in replay_rows:
        request_id = str(replay["request_id"])
        source_row = source_join_by_request.get(request_id, {})
        decision = decisions_by_requirement.get(str(replay["source_requirement_id"]), {})
        rows.append(
            {
                "proxy_target_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-TARGET-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                **compact_row(source_row or replay),
                "source_requirement_id": replay.get("source_requirement_id"),
                "request_replay_id": replay.get("request_replay_id"),
                "candidate_replay_bucket": replay.get("candidate_replay_bucket"),
                "source_search_decision_bucket": decision.get("source_search_decision_bucket"),
                "event15_record_count": replay.get("event15_record_count"),
                "event_boundary_record_count": replay.get("event_boundary_record_count"),
                "file_first_record_utc": replay.get("file_first_record_utc"),
                "file_last_record_utc": replay.get("file_last_record_utc"),
                "updated_ladder_join_status": source_row.get("updated_ladder_join_status"),
                "updated_ladder_snapshot_bucket": source_row.get("updated_ladder_snapshot_bucket"),
                "depth_path": source_row.get("depth_path") or replay.get("candidate_path"),
                "proxy_target_status": proxy_target_status(replay, decision),
                "not_waiting": "This target is routed to source-safe proxy controls, not future/live shadow waiting.",
            }
        )
    return rows


def proxy_target_status(replay: dict[str, Any], decision: dict[str, Any]) -> str:
    replay_bucket = replay.get("candidate_replay_bucket")
    decision_bucket = decision.get("source_search_decision_bucket")
    if replay_bucket == "CANDIDATE_HAS_NO_EVENT15_RECORDS":
        return "PROXY_TARGET_EVENT15_EMPTY_SOURCE_FILE"
    if decision_bucket == "CURRENT_FILE_TRUE_FINAL_MINUTE_SOURCE_SILENCE_NO_ALTERNATE":
        return "PROXY_TARGET_TRUE_FINAL_MINUTE_SOURCE_SILENCE"
    return "PROXY_TARGET_UNREPAIRED_SOURCE_SILENCE"


def control_pool_for_group(group_values: dict[str, Any], exact_rows: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    queue_id = group_values.get("route_c_queue_id")
    command = group_values.get("command_feature_bucket")
    source_symbol = group_values.get("source_symbol")
    source_proxy_family = group_values.get("source_proxy_family")
    source_date = group_values.get("source_date")

    matchers = [
        (
            "same_source_date_queue_command_exact_feature",
            lambda row: source_symbol
            and source_date
            and queue_id
            and command
            and row.get("source_symbol") == source_symbol
            and row.get("source_date") == source_date
            and row.get("route_c_queue_id") == queue_id
            and row.get("command_feature_bucket") == command,
        ),
        (
            "same_source_symbol_queue_command_exact_feature",
            lambda row: source_symbol
            and queue_id
            and command
            and row.get("source_symbol") == source_symbol
            and row.get("route_c_queue_id") == queue_id
            and row.get("command_feature_bucket") == command,
        ),
        (
            "same_queue_command_exact_feature",
            lambda row: queue_id
            and command
            and row.get("route_c_queue_id") == queue_id
            and row.get("command_feature_bucket") == command,
        ),
        (
            "same_source_symbol_command_exact_feature",
            lambda row: source_symbol
            and command
            and row.get("source_symbol") == source_symbol
            and row.get("command_feature_bucket") == command,
        ),
        (
            "same_queue_exact_feature",
            lambda row: queue_id and row.get("route_c_queue_id") == queue_id,
        ),
        (
            "same_command_exact_feature",
            lambda row: command and row.get("command_feature_bucket") == command,
        ),
        (
            "same_source_symbol_exact_feature",
            lambda row: source_symbol and row.get("source_symbol") == source_symbol,
        ),
        (
            "same_source_proxy_family_exact_feature",
            lambda row: source_proxy_family and row.get("source_proxy_family") == source_proxy_family,
        ),
    ]
    for scope, predicate in matchers:
        pool = [row for row in exact_rows if predicate(row)]
        if pool:
            return scope, pool
    return "all_exact_feature_rows", exact_rows


def classify_proxy_verdict(group_stats: dict[str, Any], control_stats: dict[str, Any], group_values: dict[str, Any]) -> str:
    group_n = int(group_stats["n"])
    control_n = int(control_stats["n"])
    delta = numeric_delta(group_stats.get("route_alignment_share"), control_stats.get("route_alignment_share"))
    if control_n == 0:
        return "PROXY_CONTROL_EMPTY_CONTROL_POOL"
    if group_n < 5:
        return "PROXY_CONTROL_UNDERPOWERED_N_LT_5"
    if group_n < 20:
        return "PROXY_CONTROL_UNDERPOWERED_N_LT_20"
    if group_values.get("candidate_replay_bucket") == "CANDIDATE_HAS_NO_EVENT15_RECORDS":
        return "PROXY_CONTROL_EVENT15_EMPTY_SOURCE_STATE"
    if delta is not None and delta <= -0.05:
        return "PROXY_CONTROL_AVOID_DIRECTIONAL_DESCRIPTOR"
    if delta is not None and abs(delta) <= 0.05:
        return "PROXY_CONTROL_NEAR_EXACT_FEATURE_CONTROL"
    return "PROXY_CONTROL_MIXED_OR_DESCRIPTIVE"


def next_action_for_verdict(verdict: str) -> str:
    if verdict == "PROXY_CONTROL_AVOID_DIRECTIONAL_DESCRIPTOR":
        return "convert to branch-local avoid challenger only after dedup/concentration stress"
    if verdict == "PROXY_CONTROL_EVENT15_EMPTY_SOURCE_STATE":
        return "split as source-capture/market-activity state and compare against exact-feature no-event controls"
    if verdict.startswith("PROXY_CONTROL_UNDERPOWERED"):
        return "aggregate through parent axes or acquire/proxy more exact rows before stronger interpretation"
    if verdict == "PROXY_CONTROL_EMPTY_CONTROL_POOL":
        return "build broader exact-feature control pool or source-acquisition route"
    return "preserve descriptor context and continue mutation-boundary challenger design"


def build_pair_rows(targets: list[dict[str, Any]], exact_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        for control in exact_rows:
            relation_parts: list[str] = []
            if target.get("source_symbol") == control.get("source_symbol"):
                relation_parts.append("same_source_symbol")
            if target.get("source_date") == control.get("source_date"):
                relation_parts.append("same_source_date")
            if target.get("route_c_queue_id") == control.get("route_c_queue_id"):
                relation_parts.append("same_queue")
            if target.get("command_feature_bucket") == control.get("command_feature_bucket"):
                relation_parts.append("same_command")
            if target.get("source_proxy_family") == control.get("source_proxy_family"):
                relation_parts.append("same_source_proxy_family")
            if not relation_parts:
                continue
            target_align = bool_value(target.get("route_c_delta_aligned_with_future"))
            control_align = bool_value(control.get("route_c_delta_aligned_with_future"))
            rows.append(
                {
                    "pair_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-PAIR-{len(rows) + 1:06d}",
                    "route_id": ROUTE_ID,
                    "safe_flags": SAFE_FLAGS,
                    "evidence_boundary": EVIDENCE_BOUNDARY,
                    "target_request_id": target.get("request_id"),
                    "control_request_id": control.get("request_id"),
                    "source_requirement_id": target.get("source_requirement_id"),
                    "candidate_replay_bucket": target.get("candidate_replay_bucket"),
                    "proxy_target_status": target.get("proxy_target_status"),
                    "pair_relations": relation_parts,
                    "target_source_symbol": target.get("source_symbol"),
                    "control_source_symbol": control.get("source_symbol"),
                    "target_source_date": target.get("source_date"),
                    "control_source_date": control.get("source_date"),
                    "target_queue_id": target.get("route_c_queue_id"),
                    "control_queue_id": control.get("route_c_queue_id"),
                    "target_command_feature_bucket": target.get("command_feature_bucket"),
                    "control_command_feature_bucket": control.get("command_feature_bucket"),
                    "target_alignment": target_align,
                    "control_alignment": control_align,
                    "alignment_delta_target_minus_control": numeric_delta(
                        None if target_align is None else float(target_align),
                        None if control_align is None else float(control_align),
                    ),
                }
            )
    return rows


def build_control_rows(targets: list[dict[str, Any]], exact_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families: list[tuple[str, list[str]]] = [
        ("proxy_target_status", ["proxy_target_status"]),
        ("candidate_replay_bucket", ["candidate_replay_bucket"]),
        ("source_search_decision_bucket", ["source_search_decision_bucket"]),
        ("source_symbol_replay_bucket", ["source_symbol", "candidate_replay_bucket"]),
        ("source_proxy_family_replay_bucket", ["source_proxy_family", "candidate_replay_bucket"]),
        ("route_queue_replay_bucket", ["route_c_queue_id", "candidate_replay_bucket"]),
        ("command_bucket_replay_bucket", ["command_feature_bucket", "candidate_replay_bucket"]),
        ("route_queue_command_replay_bucket", ["route_c_queue_id", "command_feature_bucket", "candidate_replay_bucket"]),
        ("source_symbol_queue_command", ["source_symbol", "route_c_queue_id", "command_feature_bucket"]),
    ]
    rows: list[dict[str, Any]] = []
    for family, keys in families:
        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for target in targets:
            grouped[tuple(target.get(key) for key in keys)].append(target)
        for values, group in sorted(grouped.items(), key=lambda item: tuple(str(value) for value in item[0])):
            group_values = {key: value for key, value in zip(keys, values, strict=True)}
            control_scope, pool = control_pool_for_group(group_values, exact_rows)
            group_stats = row_stats(group)
            control_stats = row_stats(pool)
            verdict = classify_proxy_verdict(group_stats, control_stats, group_values)
            rows.append(
                {
                    "control_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-CONTROL-{len(rows) + 1:05d}",
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
                    "proxy_control_verdict": verdict,
                    "next_same_resource_action": next_action_for_verdict(verdict),
                }
            )
    return rows


def build_bucket_rows(control_rows: list[dict[str, Any]], pair_rows: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for control in control_rows:
        grouped[str(control["proxy_control_verdict"])].append(control)
    for verdict, group in sorted(grouped.items()):
        rows.append(
            {
                "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-BUCKET-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "bucket_family": "proxy_control_verdict",
                "bucket_value": verdict,
                "row_count": len(group),
                "underlying_target_rows": sum(int(item["source_rows"]["n"]) for item in group),
                "control_scopes": counter_dict(item.get("control_scope") for item in group),
                "next_same_resource_action": next_action_for_verdict(verdict),
                "counts_context": counts,
            }
        )
    relation_counter = Counter()
    for pair in pair_rows:
        for relation in pair.get("pair_relations", []):
            relation_counter[str(relation)] += 1
    for relation, count in sorted(relation_counter.items()):
        rows.append(
            {
                "bucket_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-BUCKET-{len(rows) + 1:05d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "bucket_family": "pair_relation",
                "bucket_value": relation,
                "row_count": count,
                "next_same_resource_action": "use relation-level pair controls to build deduplicated challenger stress tests",
                "counts_context": counts,
            }
        )
    return rows


def build_questions(bucket_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]], counts: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket in bucket_rows:
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": bucket["bucket_family"],
                "question_key": bucket["bucket_value"],
                "row_count": bucket["row_count"],
                "question": "What split, stress, acquisition, or challenger-boundary action follows from this proxy-control bucket?",
                "next_same_resource_action": bucket["next_same_resource_action"],
                "counts_context": counts,
            }
        )
    grouped: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for target in target_rows:
        grouped[(target.get("source_requirement_id"), target.get("candidate_replay_bucket"))].append(target)
    for (requirement_id, replay_bucket), group in sorted(grouped.items(), key=lambda item: tuple(str(v) for v in item[0])):
        rows.append(
            {
                "question_id": f"SIERRA-LADDER-SOURCE-SILENCE-MICROCLUSTER-PROXY-Q-{len(rows) + 1:03d}",
                "route_id": ROUTE_ID,
                "safe_flags": SAFE_FLAGS,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "question_family": "requirement_replay_bucket",
                "question_key": {"source_requirement_id": requirement_id, "candidate_replay_bucket": replay_bucket},
                "row_count": len(group),
                "question": "Should this requirement bucket become a source-quality avoid boundary, an event-activity proxy, or a killed descriptor after controls?",
                "next_same_resource_action": "feed controlled proxy verdict into branch-local mutation boundary design",
                "counts_context": counts,
            }
        )
    return rows


def update_manifest(generated_utc: str) -> None:
    artifacts = [
        (Path(__file__).resolve(), "sierra_depth_ladder_source_silence_microcluster_proxy_controls_builder", "created"),
        (RESULT_PATH, "sierra_depth_ladder_source_silence_microcluster_proxy_control_result", "created"),
        (TARGET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_proxy_target_ledger", "created"),
        (PAIR_LEDGER, "sierra_depth_ladder_source_silence_microcluster_proxy_pair_ledger", "created"),
        (CONTROL_LEDGER, "sierra_depth_ladder_source_silence_microcluster_proxy_control_ledger", "created"),
        (BUCKET_LEDGER, "sierra_depth_ladder_source_silence_microcluster_proxy_bucket_ledger", "created"),
        (QUESTION_LEDGER, "sierra_depth_ladder_source_silence_microcluster_proxy_question_ledger", "created"),
        (SUMMARY_PATH, "sierra_depth_ladder_source_silence_microcluster_proxy_control_summary", "created"),
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
        "event_type": "sierra_depth_ladder_source_silence_microcluster_proxy_controls",
        "status": "done",
        "route": "source_silence_microcluster_proxy_controls",
        "details": "Converted unrepaired microcluster source-search rows into source-safe exact-feature/pair proxy controls.",
        "counts": counts,
        "proxy_control_verdict_counts": verdict_counts,
        "artifacts": [
            relative(Path(__file__).resolve()),
            relative(RESULT_PATH),
            relative(TARGET_LEDGER),
            relative(PAIR_LEDGER),
            relative(CONTROL_LEDGER),
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
        "# Sierra Source-Silence Microcluster Proxy Controls",
        "",
        f"Generated UTC: `{generated_utc}`",
        "",
        "Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`",
        "",
        "Evidence class: source-safe proxy controls only. No validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.",
        "",
        "## Counts",
        "",
    ]
    for key, value in counts.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Proxy Control Verdicts", ""])
    for verdict, count in sorted(verdict_counts.items()):
        lines.append(f"- `{verdict}`: `{count}`")
    lines.extend(
        [
            "",
            "## Same-Resource Continuation",
            "",
            "- Deduplicate and stress any proxy avoid-descriptor verdict before branch-local challenger use.",
            "- Keep event15-empty source states separate from final-minute-silence states.",
            "- Use pair-relation ledgers to build next challenger-boundary packets without waiting for forward rows.",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    generated_utc = utc_now()
    source_join = read_jsonl(SOURCE_JOIN_LEDGER)
    replay_rows = read_jsonl(SOURCE_SEARCH_REQUEST_REPLAY_LEDGER)
    decision_rows = read_jsonl(SOURCE_SEARCH_DECISION_LEDGER)
    requirement_rows = read_jsonl(MICROCLUSTER_REQUIREMENT_LEDGER)

    source_join_by_request = {str(row["request_id"]): row for row in source_join}
    decisions_by_requirement = {str(row["source_requirement_id"]): row for row in decision_rows}
    exact_feature_rows = [
        row for row in source_join
        if row.get("updated_ladder_join_status") in EXACT_FEATURE_STATUSES and not row.get("source_silence_joined")
    ]
    target_rows = build_targets(replay_rows, decisions_by_requirement, source_join_by_request)
    pair_rows = build_pair_rows(target_rows, exact_feature_rows)
    control_rows = build_control_rows(target_rows, exact_feature_rows)
    verdict_counts = counter_dict(row.get("proxy_control_verdict") for row in control_rows)
    counts = {
        "source_join_input_rows": len(source_join),
        "source_search_replay_input_rows": len(replay_rows),
        "source_search_decision_input_rows": len(decision_rows),
        "microcluster_requirement_input_rows": len(requirement_rows),
        "exact_feature_control_rows": len(exact_feature_rows),
        "proxy_target_rows": len(target_rows),
        "pair_rows": len(pair_rows),
        "control_rows": len(control_rows),
        "bucket_rows": 0,
        "question_rows": 0,
    }
    bucket_rows = build_bucket_rows(control_rows, pair_rows, counts)
    counts["bucket_rows"] = len(bucket_rows)
    question_rows = build_questions(bucket_rows, target_rows, counts)
    counts["question_rows"] = len(question_rows)

    write_jsonl(TARGET_LEDGER, target_rows)
    write_jsonl(PAIR_LEDGER, pair_rows)
    write_jsonl(CONTROL_LEDGER, control_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    result = {
        "schema": "sierra_depth_ladder_source_silence_microcluster_proxy_control_result_v1",
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "safe_flags": SAFE_FLAGS,
        "evidence_class": "SIERRA_SOURCE_SILENCE_MICROCLUSTER_PROXY_CONTROL_ONLY",
        "claim_boundary": EVIDENCE_BOUNDARY,
        "counts": counts,
        "proxy_control_verdict_counts": verdict_counts,
        "not_completion": "This proxy-control packet does not complete the 60-hour moonshot objective.",
        "next_same_resource_work": [
            "deduplicate and stress proxy avoid-descriptor verdicts",
            "split event15-empty source states from final-minute-silence states in branch-local challenger design",
            "feed controlled proxy verdicts into source-quality mutation boundary packet",
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
