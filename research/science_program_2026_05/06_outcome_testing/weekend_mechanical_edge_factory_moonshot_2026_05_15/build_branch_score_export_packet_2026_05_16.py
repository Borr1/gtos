#!/usr/bin/env python3
"""Materialize next-compute score rows into concrete export queues.

This packet is the bridge from score vectors to the next same-resource builders:
source-risk router/acquisition, M15 interval challenger/avoid/bounds, M1 support
conflict splits, positive replay candidates, and entry/adverse redesign rows.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

NEXT_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_RESULT_2026-05-16.json"
NEXT_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_BRANCH_LEDGER_2026-05-16.jsonl"
NEXT_ACTION = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_ACTION_FAMILY_LEDGER_2026-05-16.jsonl"
NEXT_SOURCE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_SOURCE_RISK_ROUTER_LEDGER_2026-05-16.jsonl"
NEXT_M15 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_M15_INTERVAL_LEDGER_2026-05-16.jsonl"
NEXT_M1 = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_M1_CONFLICT_LEDGER_2026-05-16.jsonl"
NEXT_POSITIVE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_POSITIVE_REPLAY_LEDGER_2026-05-16.jsonl"
NEXT_ENTRY_ADVERSE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_RESULT_2026-05-16.json"
BRANCH_EXPORT_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
EXPORT_ACTION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_EXPORT_ACTION_LEDGER_2026-05-16.jsonl"
SOURCE_EXPORT_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_SOURCE_ROUTER_LEDGER_2026-05-16.jsonl"
M15_EXPORT_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_M15_INTERVAL_LEDGER_2026-05-16.jsonl"
M1_EXPORT_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_M1_CONFLICT_LEDGER_2026-05-16.jsonl"
POSITIVE_EXPORT_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_POSITIVE_REPLAY_LEDGER_2026-05-16.jsonl"
ENTRY_ADVERSE_EXPORT_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Branch score export packet only. It materializes next-compute proxy scores "
    "into branch-local research export queues and implementation-scoring specs. "
    "It does not change live behavior and does not claim broker R/PnL, realized "
    "expectancy, win-rate, validation, live-readiness, promotion, or live effect."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"_parse_error": True, "_line_no": line_no, "_source_path": str(path)})
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def by_branch(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in rows if row.get("branch_queue_id") is not None}


def group_by_branch(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("branch_queue_id") is not None:
            grouped[str(row.get("branch_queue_id"))].append(row)
    return grouped


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def branch_sort_key(branch_id: str) -> tuple[str, int]:
    try:
        return (branch_id.rsplit("-", 1)[0], int(branch_id.rsplit("-", 1)[1]))
    except (ValueError, IndexError):
        return (branch_id, 0)


def round_or_none(value: Any, digits: int = 6) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def source_export_class(row: dict[str, Any]) -> str:
    cls = row.get("source_risk_score_class")
    if cls == "SOURCE_STRESS_FLIP_BUT_CONSERVATIVE_POSITIVE":
        return "SOURCE_ROUTER_POSITIVE_LOW_SPREAD_BUT_HIGH_SPREAD_FLIP"
    if cls == "SOURCE_STRESS_FLIP_CONSERVATIVE_NEGATIVE":
        return "SOURCE_ROUTER_NEGATIVE_AVOID_OR_ACQUIRE_EXACT_SOURCE"
    return "SOURCE_ROUTER_STRADDLE_BOUNDS_ACQUIRE_OR_COST_SPLIT"


def m15_export_class(row: dict[str, Any]) -> str:
    cls = row.get("m15_interval_score_class")
    if cls == "M15_TARGET_FIRST_CHALLENGER_SCORE":
        return "M15_EXPORT_TARGET_FIRST_CHALLENGER"
    if cls == "M15_STOP_FIRST_AVOID_SCORE":
        return "M15_EXPORT_STOP_FIRST_AVOID_OR_REDESIGN"
    return "M15_EXPORT_INTERVAL_BOUNDS_ROUTER"


def m1_export_class(row: dict[str, Any]) -> str:
    if row.get("m1_conflict_score_class") == "M1_SUPPORT_POSITIVE_BRANCH_AGGREGATE_CONFLICT":
        return "M1_EXPORT_SUPPORT_POSITIVE_BRANCH_CONFLICT_SPLIT"
    return "M1_EXPORT_SUPPORT_AND_BRANCH_TARGET_STABLE"


def positive_export_class(row: dict[str, Any]) -> str:
    if row.get("positive_replay_score_class") == "POSITIVE_REPLAYABLE_CONSERVATIVE_POSITIVE_PROXY":
        return "POSITIVE_EXPORT_REPLAYABLE_CONSERVATIVE_POSITIVE"
    return "POSITIVE_EXPORT_SOURCE_REPAIR_OR_STRESS_FIRST"


def entry_adverse_export_class(row: dict[str, Any]) -> str:
    cls = row.get("entry_adverse_score_class")
    if cls == "ENTRY_AND_ADVERSE_REDESIGN_BOTH_ACTIVE":
        return "ENTRY_ADVERSE_EXPORT_BOTH_REDESIGN_SCORE"
    if cls == "ENTRY_REDESIGN_ACTIVE":
        return "ENTRY_ADVERSE_EXPORT_ENTRY_REDESIGN_SCORE"
    return "ENTRY_ADVERSE_EXPORT_NO_REDESIGN_SCOPE_PRESERVE"


def source_manifest_rows(paths: list[Path]) -> tuple[list[dict[str, Any]], str]:
    rows = []
    for index, path in enumerate(paths, 1):
        rel = path.relative_to(REPO).as_posix()
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-SCORE-EXPORT-SRC-{index:04d}",
                "path": rel,
                "sha256": sha256_file(path) if path.exists() else None,
                "status": "HASHED" if path.exists() else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def export_base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_queue_id": row.get("branch_queue_id"),
        "route_candidate_id": row.get("route_candidate_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "side": row.get("side"),
        "entry_variant": row.get("entry_variant"),
        "target_stop_contract_id": row.get("target_stop_contract_id"),
    }


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Historical OHLC GTOS Replay Branch Score Export Packet",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Export Distributions", ""])
    for category in [
        "primary_export_class",
        "source_export_class",
        "m15_export_class",
        "m1_export_class",
        "positive_export_class",
        "entry_adverse_export_class",
    ]:
        lines.append(f"### {category}")
        for bucket, count in result["bucket_distributions"].get(category, {}).items():
            lines.append(f"- `{bucket}`: `{count}`")
        lines.append("")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST) if OUTPUT_MANIFEST.exists() else {
        "schema": "weekend_mechanical_edge_factory_output_manifest_v1",
        "artifacts": [],
    }
    output_paths = [
        RESULT_PATH,
        BRANCH_EXPORT_LEDGER,
        EXPORT_ACTION_LEDGER,
        SOURCE_EXPORT_LEDGER,
        M15_EXPORT_LEDGER,
        M1_EXPORT_LEDGER,
        POSITIVE_EXPORT_LEDGER,
        ENTRY_ADVERSE_EXPORT_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        SUMMARY_PATH,
    ]
    output_path_strings = {path.relative_to(REPO).as_posix() for path in output_paths}
    artifacts = [item for item in manifest.get("artifacts", []) if item.get("path") not in output_path_strings]
    for path in output_paths:
        artifacts.append(
            {
                "path": path.relative_to(REPO).as_posix(),
                "status": "created",
                "type": "branch_score_export_packet",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["artifacts"] = artifacts
    manifest["safe_flags"] = SAFE_FLAGS
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "branch_score_export_packet_built",
                    "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
                    "artifact": RESULT_PATH.relative_to(REPO).as_posix(),
                    "counts": result["counts"],
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "not_completion": True,
                },
                sort_keys=True,
            )
            + "\n"
        )


def main() -> int:
    generated_at = now_utc()
    next_result = read_json(NEXT_RESULT)
    branch_rows_in = read_jsonl(NEXT_BRANCH)
    action_rows_in = read_jsonl(NEXT_ACTION)
    source_rows_in = read_jsonl(NEXT_SOURCE)
    m15_rows_in = read_jsonl(NEXT_M15)
    m1_rows_in = read_jsonl(NEXT_M1)
    positive_rows_in = read_jsonl(NEXT_POSITIVE)
    entry_adverse_rows_in = read_jsonl(NEXT_ENTRY_ADVERSE)

    branch_by_id = by_branch(branch_rows_in)
    action_by_id = group_by_branch(action_rows_in)
    source_by_id = by_branch(source_rows_in)
    m15_by_id = by_branch(m15_rows_in)
    m1_by_id = by_branch(m1_rows_in)
    positive_by_id = by_branch(positive_rows_in)
    entry_adverse_by_id = by_branch(entry_adverse_rows_in)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            NEXT_RESULT,
            NEXT_BRANCH,
            NEXT_ACTION,
            NEXT_SOURCE,
            NEXT_M15,
            NEXT_M1,
            NEXT_POSITIVE,
            NEXT_ENTRY_ADVERSE,
            Path(__file__).resolve(),
        ]
    )

    branch_export_rows: list[dict[str, Any]] = []
    export_action_rows: list[dict[str, Any]] = []
    source_export_rows: list[dict[str, Any]] = []
    m15_export_rows: list[dict[str, Any]] = []
    m1_export_rows: list[dict[str, Any]] = []
    positive_export_rows: list[dict[str, Any]] = []
    entry_adverse_export_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[Any]] = defaultdict(Counter)

    for index, branch_id in enumerate(sorted(branch_by_id, key=branch_sort_key), 1):
        branch = branch_by_id[branch_id]
        source = source_by_id.get(branch_id)
        m15 = m15_by_id.get(branch_id)
        m1 = m1_by_id.get(branch_id)
        positive = positive_by_id.get(branch_id)
        entry_adverse = entry_adverse_by_id.get(branch_id)
        score_vector = branch.get("mechanical_score_vector") or {}

        if source and branch.get("branch_next_score_class") == "SOURCE_STRESS_ROUTER_SCORE_REQUIRED":
            primary_export_class = source_export_class(source)
            primary_family = "SOURCE"
        elif branch.get("branch_next_score_class") == "M15_INTERVAL_SCORE_REQUIRED":
            primary_export_class = m15_export_class(m15 or {})
            primary_family = "M15"
        elif branch.get("branch_next_score_class") == "M1_SUPPORT_CONFLICT_OR_TARGET_SCORE_REQUIRED":
            primary_export_class = m1_export_class(m1 or {})
            primary_family = "M1"
        elif branch.get("branch_next_score_class") == "POSITIVE_CHALLENGER_REPLAY_SCORE_REQUIRED":
            primary_export_class = positive_export_class(positive or {})
            primary_family = "POSITIVE"
        elif branch.get("branch_next_score_class") == "ENTRY_ADVERSE_REDESIGN_SCORE_REQUIRED":
            primary_export_class = entry_adverse_export_class(entry_adverse or {})
            primary_family = "ENTRY_ADVERSE"
        else:
            primary_export_class = "BINDING_OR_PRESERVE_NO_SCALAR_EXPORT"
            primary_family = "BINDING"

        branch_export_rows.append(
            {
                "score_export_branch_id": f"OHLC-GTOS-SCORE-EXPORT-BRANCH-{index:05d}",
                **export_base(branch),
                "primary_export_family": primary_family,
                "primary_export_class": primary_export_class,
                "next_computation_class": branch.get("next_computation_class"),
                "branch_next_score_class": branch.get("branch_next_score_class"),
                "mechanical_triage_score_proxy": score_vector.get("mechanical_triage_score_proxy"),
                "score_direction_class": score_vector.get("score_direction_class"),
                "target_stop_result": branch.get("target_stop_result"),
                "source_execution_class": branch.get("source_execution_class"),
                "ordering_execution_class": branch.get("ordering_execution_class"),
                "source_export_present": source is not None,
                "m15_export_present": m15 is not None,
                "m1_export_present": m1 is not None,
                "positive_export_present": positive is not None,
                "entry_adverse_export_present": entry_adverse is not None,
                "export_action_count": len(action_by_id.get(branch_id, [])),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        for action_index, action in enumerate(action_by_id.get(branch_id, []), 1):
            export_action_rows.append(
                {
                    "score_export_action_id": f"OHLC-GTOS-SCORE-EXPORT-ACTION-{index:05d}-{action_index:02d}",
                    **export_base(branch),
                    "action_family": action.get("action_family"),
                    "family_score_class": action.get("family_score_class"),
                    "family_score_proxy": action.get("family_score_proxy"),
                    "export_action_status": "EXPORTED_FOR_FAMILY_SPEC_OR_CONTROL_CONTEXT",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if source:
            source_export_rows.append(
                {
                    "source_router_export_id": f"OHLC-GTOS-SCORE-EXPORT-SOURCE-{len(source_export_rows) + 1:05d}",
                    **export_base(source),
                    "source_export_class": source_export_class(source),
                    "source_risk_score_class": source.get("source_risk_score_class"),
                    "branch_stress_class": source.get("branch_stress_class"),
                    "stress_lower_mean": source.get("stress_lower_mean"),
                    "stress_midpoint_mean": source.get("stress_midpoint_mean"),
                    "stress_upper_mean": source.get("stress_upper_mean"),
                    "stress_interval_width": source.get("stress_interval_width"),
                    "source_support_rows": source.get("source_support_rows"),
                    "next_packet_route": "BUILD_SOURCE_STRESS_ROUTER_OR_ACQUISITION_SPLIT",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if m15:
            m15_export_rows.append(
                {
                    "m15_interval_export_id": f"OHLC-GTOS-SCORE-EXPORT-M15-{len(m15_export_rows) + 1:05d}",
                    **export_base(m15),
                    "m15_export_class": m15_export_class(m15),
                    "m15_interval_score_class": m15.get("m15_interval_score_class"),
                    "interval_lower_mean": m15.get("interval_lower_mean"),
                    "interval_midpoint_mean": m15.get("interval_midpoint_mean"),
                    "interval_upper_mean": m15.get("interval_upper_mean"),
                    "interval_width": m15.get("interval_width"),
                    "proxy_variant_count": m15.get("proxy_variant_count"),
                    "exact_chronology_claim": False,
                    "next_packet_route": "BUILD_M15_CHALLENGER_AVOID_BOUNDS_EXPORT",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if m1:
            m1_export_rows.append(
                {
                    "m1_conflict_export_id": f"OHLC-GTOS-SCORE-EXPORT-M1-{len(m1_export_rows) + 1:05d}",
                    **export_base(m1),
                    "m1_export_class": m1_export_class(m1),
                    "m1_conflict_score_class": m1.get("m1_conflict_score_class"),
                    "branch_midpoint_mean": m1.get("branch_midpoint_mean"),
                    "m1_support_midpoint_mean": m1.get("m1_support_midpoint_mean"),
                    "m1_support_minus_branch_midpoint": m1.get("m1_support_minus_branch_midpoint"),
                    "m1_support_resolution_class": m1.get("m1_support_resolution_class"),
                    "proxy_variant_count": m1.get("proxy_variant_count"),
                    "exact_chronology_claim": False,
                    "tick_ordering_exact": False,
                    "next_packet_route": "BUILD_M1_SUPPORT_CONFLICT_SPLIT_EXPORT",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if positive:
            positive_export_rows.append(
                {
                    "positive_replay_export_id": f"OHLC-GTOS-SCORE-EXPORT-POSITIVE-{len(positive_export_rows) + 1:05d}",
                    **export_base(positive),
                    "positive_export_class": positive_export_class(positive),
                    "positive_replay_score_class": positive.get("positive_replay_score_class"),
                    "positive_challenger_class": positive.get("positive_challenger_class"),
                    "positive_replay_status": positive.get("positive_replay_status"),
                    "positive_replayable_now": positive.get("positive_replayable_now"),
                    "positive_lower_mean": positive.get("positive_lower_mean"),
                    "positive_midpoint_mean": positive.get("positive_midpoint_mean"),
                    "positive_upper_mean": positive.get("positive_upper_mean"),
                    "positive_control_delta_modifier_class": positive.get("positive_control_delta_modifier_class"),
                    "positive_concentration_modifier_class": positive.get("positive_concentration_modifier_class"),
                    "proposed_branch_local_code_surface": positive.get("proposed_branch_local_code_surface"),
                    "next_packet_route": "BUILD_POSITIVE_REPLAY_CANDIDATE_EXPORT",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        if entry_adverse:
            entry_adverse_export_rows.append(
                {
                    "entry_adverse_export_id": f"OHLC-GTOS-SCORE-EXPORT-ENTRY-ADVERSE-{index:05d}",
                    **export_base(entry_adverse),
                    "entry_adverse_export_class": entry_adverse_export_class(entry_adverse),
                    "entry_adverse_score_class": entry_adverse.get("entry_adverse_score_class"),
                    "entry_geometry_retest_class": entry_adverse.get("entry_geometry_retest_class"),
                    "entry_redesign_action_class": entry_adverse.get("entry_redesign_action_class"),
                    "adverse_stop_first_class": entry_adverse.get("adverse_stop_first_class"),
                    "adverse_redesign_action_class": entry_adverse.get("adverse_redesign_action_class"),
                    "no_fill_or_unfilled_rows": entry_adverse.get("no_fill_or_unfilled_rows"),
                    "target_first_rows": entry_adverse.get("target_first_rows"),
                    "stop_first_rows": entry_adverse.get("stop_first_rows"),
                    "next_packet_route": "BUILD_ENTRY_ADVERSE_REDESIGN_SCORE_EXPORT",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

        for category, value in [
            ("primary_export_class", primary_export_class),
            ("primary_export_family", primary_family),
            ("branch_next_score_class", branch.get("branch_next_score_class")),
            ("next_computation_class", branch.get("next_computation_class")),
            ("score_direction_class", score_vector.get("score_direction_class")),
            ("target_stop_result", branch.get("target_stop_result")),
        ]:
            bucket_counters[category][str(value)] += 1

    for row in source_export_rows:
        bucket_counters["source_export_class"][row.get("source_export_class")] += 1
    for row in m15_export_rows:
        bucket_counters["m15_export_class"][row.get("m15_export_class")] += 1
    for row in m1_export_rows:
        bucket_counters["m1_export_class"][row.get("m1_export_class")] += 1
    for row in positive_export_rows:
        bucket_counters["positive_export_class"][row.get("positive_export_class")] += 1
    for row in entry_adverse_export_rows:
        bucket_counters["entry_adverse_export_class"][row.get("entry_adverse_export_class")] += 1
    for row in export_action_rows:
        bucket_counters["action_family"][row.get("action_family")] += 1
        bucket_counters["family_score_class"][row.get("family_score_class")] += 1

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-SCORE-EXPORT-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "row_count": int(count),
                    "share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-SCORE-EXPORT-QUESTION-001",
            "question": "Which source-stress branches become risk-router candidates versus acquire-or-avoid rows?",
            "answer_route": "Use source_router_export_class and stress interval fields.",
        },
        {
            "question_id": "OHLC-GTOS-SCORE-EXPORT-QUESTION-002",
            "question": "Which M15 interval branches export as challengers, avoids, or bounds routers?",
            "answer_route": "Use m15_export_class with interval bounds; exact chronology remains false.",
        },
        {
            "question_id": "OHLC-GTOS-SCORE-EXPORT-QUESTION-003",
            "question": "Which M1 support rows conflict with the branch aggregate and require split scoring?",
            "answer_route": "Use m1_export_class and support-minus-branch midpoint.",
        },
        {
            "question_id": "OHLC-GTOS-SCORE-EXPORT-QUESTION-004",
            "question": "Which positive candidates are replayable now versus source repair/stress first?",
            "answer_route": "Use positive_export_class and modifier fields.",
        },
        {
            "question_id": "OHLC-GTOS-SCORE-EXPORT-QUESTION-005",
            "question": "Which entry/adverse rows require redesign score exports?",
            "answer_route": "Use entry_adverse_export_class across the full branch denominator.",
        },
    ]
    for row in question_rows:
        row.update(
            {
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "not_completion": True,
                "source_manifest_hash": manifest_hash,
            }
        )

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SCORE_EXPORT_PACKET",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_branch_score_rows": len(branch_rows_in),
            "input_action_family_score_rows": len(action_rows_in),
            "input_source_risk_router_rows": len(source_rows_in),
            "input_m15_interval_score_rows": len(m15_rows_in),
            "input_m1_conflict_score_rows": len(m1_rows_in),
            "input_positive_replay_score_rows": len(positive_rows_in),
            "input_entry_adverse_score_rows": len(entry_adverse_rows_in),
            "branch_export_rows": len(branch_export_rows),
            "export_action_rows": len(export_action_rows),
            "source_router_export_rows": len(source_export_rows),
            "m15_interval_export_rows": len(m15_export_rows),
            "m1_conflict_export_rows": len(m1_export_rows),
            "positive_replay_export_rows": len(positive_export_rows),
            "entry_adverse_export_rows": len(entry_adverse_export_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_next_compute_counts": next_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "coverage": {
            "branch_export_denominator_preserved": len(branch_export_rows) == 386,
            "export_action_count_per_branch": 5,
            "source_router_scope": len(source_export_rows),
            "m15_interval_scope": len(m15_export_rows),
            "m1_conflict_scope": len(m1_export_rows),
            "positive_replay_scope": len(positive_export_rows),
            "entry_adverse_scope": len(entry_adverse_export_rows),
        },
        "source_manifest_hash": manifest_hash,
    }

    for path, rows in [
        (BRANCH_EXPORT_LEDGER, branch_export_rows),
        (EXPORT_ACTION_LEDGER, export_action_rows),
        (SOURCE_EXPORT_LEDGER, source_export_rows),
        (M15_EXPORT_LEDGER, m15_export_rows),
        (M1_EXPORT_LEDGER, m1_export_rows),
        (POSITIVE_EXPORT_LEDGER, positive_export_rows),
        (ENTRY_ADVERSE_EXPORT_LEDGER, entry_adverse_export_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]:
        write_jsonl(path, rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
