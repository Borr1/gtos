#!/usr/bin/env python3
"""Build full-denominator entry/adverse proxy-redesign packet."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

SYNTH_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_RESULT_2026-05-16.json"
SYNTH_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_BRANCH_LEDGER_2026-05-16.jsonl"
SYNTH_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_ENTRY_GEOMETRY_RETEST_LEDGER_2026-05-16.jsonl"
SYNTH_ADVERSE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_ADVERSE_STOP_FIRST_AVOID_REDESIGN_LEDGER_2026-05-16.jsonl"
SYNTH_SOURCE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_SOURCE_STRESS_ACTION_LEDGER_2026-05-16.jsonl"
SYNTH_ORDERING_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_ORDERING_COLLAPSE_ACTION_LEDGER_2026-05-16.jsonl"
SYNTH_POSITIVE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_POSITIVE_CHALLENGER_COMPARISON_LEDGER_2026-05-16.jsonl"

EXACT_SPREAD_DELTA_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_DESCRIPTOR_DELTA_LEDGER_2026-05-16.jsonl"
EXACT_SPREAD_UNAVAILABLE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_UNAVAILABLE_STRESS_LEDGER_2026-05-16.jsonl"
M1_SPREAD_REPLAY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SIGNATURE_LEDGER_2026-05-16.jsonl"
M1_FILL_BAR_STRESS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_FILL_BAR_ORDERING_STRESS_SIGNATURE_LEDGER_2026-05-16.jsonl"
PATH_AMBIGUITY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_AMBIGUITY_LEDGER_2026-05-16.jsonl"
RECOVERED_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_SIGNATURE_PATH_LEDGER_2026-05-16.jsonl"
FAR_AVOID_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_AVOID_FILTER_BRANCH_LEDGER_2026-05-16.jsonl"
FAR_RETEST_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_FAR_MISS_AVOID_REDESIGN_RETEST_REDESIGN_BRANCH_LEDGER_2026-05-16.jsonl"
NEAR_OFFSET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_OFFSET_BRANCH_LEDGER_2026-05-16.jsonl"
NEAR_MARKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_NEAR_MISS_ENTRY_CONTROLS_MARKET_ENTRY_BRANCH_LEDGER_2026-05-16.jsonl"
SIERRA_SOURCE_MANIFEST_PATH = ROUTE_DIR / "SIERRA_DEPTH_EXACT_SOURCE_DATE_ACQUISITION_MANIFEST_2026-05-16.json"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_PROXY_REDESIGN_RESULT_2026-05-16.json"
ENTRY_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_GEOMETRY_BRANCH_REDESIGN_LEDGER_2026-05-16.jsonl"
ENTRY_VARIANT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_GEOMETRY_VARIANT_EXPLODED_LEDGER_2026-05-16.jsonl"
ADVERSE_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ADVERSE_STOP_FIRST_BRANCH_REDESIGN_LEDGER_2026-05-16.jsonl"
ADVERSE_ACTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ADVERSE_STOP_FIRST_ACTION_EXPLODED_LEDGER_2026-05-16.jsonl"
UNIFIED_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_UNIFIED_BRANCH_LOCAL_IMPLEMENTATION_LEDGER_2026-05-16.jsonl"
CROSSTAB_BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_CROSSTAB_BUCKET_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_PROXY_REDESIGN_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Entry/adverse branch-local proxy redesign packet only. It preserves all "
    "386 branch_queue_id rows and converts entry-geometry plus stop-first "
    "adverse path classes into same-resource replay/proxy/source/ordering "
    "actions. It does not claim broker R/PnL, realized expectancy, win-rate, "
    "validation, live-readiness, promotion, or live behavior change."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no, "_source_path": str(path)}


def rows(path: Path) -> list[dict[str, Any]]:
    return list(read_jsonl(path) or [])


def write_jsonl(path: Path, output_rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in output_rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def norm(value: Any) -> str:
    if value is None:
        return "None"
    try:
        return f"{float(value):.10g}"
    except (TypeError, ValueError):
        return str(value)


def branch_key(row: dict[str, Any], entry_field: str = "entry_variant") -> tuple[str, ...]:
    return (
        norm(row.get("route_candidate_id")),
        norm(row.get(entry_field)),
        norm(row.get("target_stop_contract_id")),
        norm(row.get("symbol")),
        norm(row.get("side")),
        norm(row.get("target_multiple")),
        norm(row.get("stop_multiple")),
    )


def compact_key(row: dict[str, Any], entry_field: str = "entry_variant") -> tuple[str, ...]:
    return (norm(row.get("route_candidate_id")), norm(row.get(entry_field)), norm(row.get("target_stop_contract_id")))


def group_by_branch(input_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in input_rows}


def group_by_key(input_rows: list[dict[str, Any]], entry_field: str = "entry_variant") -> dict[tuple[str, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[branch_key(row, entry_field)].append(row)
    return grouped


def group_by_compact_key(input_rows: list[dict[str, Any]], entry_field: str = "entry_variant") -> dict[tuple[str, ...], list[dict[str, Any]]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[compact_key(row, entry_field)].append(row)
    return grouped


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def source_manifest_rows() -> tuple[list[dict[str, Any]], str]:
    source_paths = [
        SYNTH_RESULT_PATH,
        SYNTH_BRANCH_PATH,
        SYNTH_ENTRY_PATH,
        SYNTH_ADVERSE_PATH,
        SYNTH_SOURCE_PATH,
        SYNTH_ORDERING_PATH,
        SYNTH_POSITIVE_PATH,
        EXACT_SPREAD_DELTA_PATH,
        EXACT_SPREAD_UNAVAILABLE_PATH,
        M1_SPREAD_REPLAY_PATH,
        M1_FILL_BAR_STRESS_PATH,
        PATH_AMBIGUITY_PATH,
        RECOVERED_PATH,
        FAR_AVOID_PATH,
        FAR_RETEST_PATH,
        NEAR_OFFSET_PATH,
        NEAR_MARKET_PATH,
        SIERRA_SOURCE_MANIFEST_PATH,
    ]
    manifest_rows = []
    for index, path in enumerate(source_paths, 1):
        manifest_rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-ENTRY-ADVERSE-SOURCE-{index:03d}",
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "status": "HASHED",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(manifest_rows, sort_keys=True).encode("utf-8")).hexdigest()
    return manifest_rows, manifest_hash


def entry_action(entry_cls: str) -> tuple[str, list[str], list[str]]:
    if entry_cls == "FAR_MISS_AVOID_OR_MARKET_PROXY_REDESIGN":
        return (
            "ENTRY_FAR_MISS_AVOID_AND_MARKET_PROXY_REDESIGN",
            ["AVOID_FILTER_BRANCH", "MARKET_ENTRY_PROXY_BRANCH", "RETEST_REDESIGN_BRANCH"],
            ["Use far-miss distance and existing avoid/retest rows; do not preserve original limit entry unchanged."],
        )
    if entry_cls == "WITHIN_RANGE_RETEST_REDESIGN":
        return (
            "ENTRY_WITHIN_RANGE_RETEST_ZONE_AND_OFFSET_REDESIGN",
            ["RETEST_ZONE_REDESIGN_BRANCH", "ENTRY_OFFSET_REDESIGN_BRANCH"],
            ["Build retest-zone and offset variants using current far-retest support rows."],
        )
    if entry_cls == "NEAR_MISS_ENTRY_CHALLENGER":
        return (
            "ENTRY_NEAR_MISS_OFFSET_AND_MARKET_ENTRY_CHALLENGER",
            ["NEAR_OFFSET_PROXY_BRANCH", "NEAR_MARKET_ENTRY_PROXY_BRANCH"],
            ["Replay both offset and market-entry challenger branches; preserve source requirements."],
        )
    if entry_cls == "MIXED_FILLABILITY_SOURCE_SPLIT":
        return (
            "ENTRY_MIXED_FILLABILITY_SOURCE_SPLIT_FIRST",
            ["SOURCE_SPLIT_BRANCH", "DESCRIPTOR_PRESERVE_BRANCH"],
            ["Split fillability source/descriptor status before redesign interpretation."],
        )
    return (
        "ENTRY_PRESERVE_NO_REDESIGN_SCOPE",
        ["PRESERVE_NO_ENTRY_GEOMETRY_SCOPE"],
        ["Preserve denominator row; no entry redesign action in this packet."],
    )


def adverse_action(adverse_cls: str) -> tuple[str, list[str], list[str]]:
    if adverse_cls == "STOP_FIRST_AVOID_OR_REDESIGN_READY":
        return (
            "ADVERSE_STOP_FIRST_IMMEDIATE_AVOID_OR_REDESIGN",
            ["STOP_FIRST_AVOID_FILTER_BRANCH", "STOP_FIRST_ENTRY_REDESIGN_BRANCH"],
            ["Only this stop-first class is immediate avoid/redesign candidate, still research-only."],
        )
    if adverse_cls == "STOP_FIRST_SOURCE_REPAIR_FIRST":
        return (
            "ADVERSE_STOP_FIRST_SOURCE_STRESS_FIRST",
            ["SOURCE_REPAIR_PRECONDITION_BRANCH", "LOW_HIGH_STRESS_BRANCH"],
            ["Repair/source-stress exact spread before avoid/redesign interpretation."],
        )
    if adverse_cls == "STOP_FIRST_ORDERING_COLLAPSE_FIRST":
        return (
            "ADVERSE_STOP_FIRST_ORDERING_COLLAPSE_FIRST",
            ["ORDERING_COLLAPSE_PRECONDITION_BRANCH", "INTERVAL_PRESERVATION_BRANCH"],
            ["Collapse ordering where M1/tick exists; otherwise preserve interval."],
        )
    if adverse_cls == "STOP_FIRST_MIXED_POSITIVE_PROXY_REVIEW":
        return (
            "ADVERSE_STOP_FIRST_MIXED_POSITIVE_CONFLICT_REVIEW",
            ["POSITIVE_CONFLICT_REVIEW_BRANCH", "CONTROL_CONCENTRATION_REVIEW_BRANCH"],
            ["Do not convert mixed-positive stop-first rows into avoid filters before conflict review."],
        )
    return (
        "ADVERSE_PRESERVE_NO_STOP_FIRST_SCOPE",
        ["PRESERVE_NO_ADVERSE_STOP_FIRST_SCOPE"],
        ["Preserve denominator row; no stop-first adverse redesign action in this packet."],
    )


def support_join_diagnostics(base_rows: list[dict[str, Any]], grouped_specs: dict[str, tuple[set[tuple[str, ...]], dict[tuple[str, ...], list[dict[str, Any]]], str]]) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    for name, (base_keys, grouped, policy) in grouped_specs.items():
        input_rows = sum(len(v) for v in grouped.values())
        matched_rows = sum(len(values) for key, values in grouped.items() if key in base_keys)
        diagnostics[name] = {
            "join_key_policy": policy,
            "input_rows": input_rows,
            "matched_rows_to_386_branch_keys": matched_rows,
            "unmatched_rows_to_386_branch_keys": input_rows - matched_rows,
            "matched_branch_keys": sum(1 for row in base_rows if (compact_key(row) if policy == "compact_route_entry_targetstop" else branch_key(row)) in grouped),
        }
    return diagnostics


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    artifacts = [
        (Path(__file__).resolve(), "builder"),
        (RESULT_PATH, "result"),
        (ENTRY_BRANCH_PATH, "entry_geometry_branch_redesign_ledger"),
        (ENTRY_VARIANT_PATH, "entry_geometry_variant_exploded_ledger"),
        (ADVERSE_BRANCH_PATH, "adverse_stop_first_branch_redesign_ledger"),
        (ADVERSE_ACTION_PATH, "adverse_stop_first_action_exploded_ledger"),
        (UNIFIED_PATH, "unified_branch_local_implementation_ledger"),
        (CROSSTAB_BUCKET_PATH, "crosstab_bucket_ledger"),
        (SOURCE_MANIFEST_LEDGER_PATH, "source_manifest_ledger"),
        (QUESTION_PATH, "question_ledger"),
        (SUMMARY_PATH, "summary"),
    ]
    artifact_names = {path.name for path, _ in artifacts}
    manifest["outputs"] = [row for row in manifest.get("outputs", []) if row.get("artifact") not in artifact_names]
    for path, artifact_type in artifacts[1:]:
        manifest["outputs"].append(
            {
                "artifact": path.name,
                "category": "historical_ohlc_gtos_replay_branch_entry_adverse_proxy_redesign",
                "artifact_type": artifact_type,
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    existing_paths = {str(path.relative_to(REPO)).replace("\\", "/") for path, _ in artifacts}
    manifest["artifacts"] = [row for row in manifest.get("artifacts", []) if row.get("path") not in existing_paths]
    for path, artifact_type in artifacts:
        manifest["artifacts"].append({"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": artifact_type})
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "event_type": "branch_entry_adverse_proxy_redesign_packet_built",
        "artifact": RESULT_PATH.name,
        "counts": result["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = [
        "# Historical OHLC GTOS Replay Branch Entry/Adverse Proxy Redesign",
        "",
        f"Generated UTC: `{result['generated_utc']}`",
        "",
        "## Boundary",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
    ]
    for key, value in result["counts"].items():
        lines.append(f"- {key}: {value}")
    for category in ["entry_geometry_retest_class", "entry_redesign_action_class", "adverse_stop_first_class", "adverse_redesign_action_class"]:
        lines.extend(["", f"## {category}", ""])
        for bucket, count in result["bucket_distributions"][category].items():
            lines.append(f"- {bucket}: {count}")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows()
    synth_result = read_json(SYNTH_RESULT_PATH)

    branch_rows = rows(SYNTH_BRANCH_PATH)
    base_full_keys = {branch_key(row) for row in branch_rows}
    base_compact_keys = {compact_key(row) for row in branch_rows}
    entry_by_branch = group_by_branch(rows(SYNTH_ENTRY_PATH))
    adverse_by_branch = group_by_branch(rows(SYNTH_ADVERSE_PATH))
    source_by_branch = group_by_branch(rows(SYNTH_SOURCE_PATH))
    ordering_by_branch = group_by_branch(rows(SYNTH_ORDERING_PATH))
    positive_by_branch = group_by_branch(rows(SYNTH_POSITIVE_PATH))

    support_groups = {
        "exact_spread_delta": (base_compact_keys, group_by_compact_key(rows(EXACT_SPREAD_DELTA_PATH)), "compact_route_entry_targetstop"),
        "path_ambiguity": (base_compact_keys, group_by_compact_key(rows(PATH_AMBIGUITY_PATH)), "compact_route_entry_targetstop"),
        "exact_spread_unavailable": (base_full_keys, group_by_key(rows(EXACT_SPREAD_UNAVAILABLE_PATH)), "full_route_entry_targetstop_symbol_side_target_stop"),
        "m1_spread_replay": (base_full_keys, group_by_key(rows(M1_SPREAD_REPLAY_PATH)), "full_route_entry_targetstop_symbol_side_target_stop"),
        "m1_fill_bar_stress": (base_full_keys, group_by_key(rows(M1_FILL_BAR_STRESS_PATH)), "full_route_entry_targetstop_symbol_side_target_stop"),
        "recovered_unfilled": (base_full_keys, group_by_key(rows(RECOVERED_PATH)), "full_route_entry_targetstop_symbol_side_target_stop"),
        "far_avoid": (base_full_keys, group_by_key(rows(FAR_AVOID_PATH)), "full_route_entry_targetstop_symbol_side_target_stop"),
        "far_retest": (base_full_keys, group_by_key(rows(FAR_RETEST_PATH)), "full_route_entry_targetstop_symbol_side_target_stop"),
        "near_offset": (base_full_keys, group_by_key(rows(NEAR_OFFSET_PATH), "source_entry_variant"), "full_route_source_entry_targetstop_symbol_side_target_stop"),
        "near_market": (base_full_keys, group_by_key(rows(NEAR_MARKET_PATH), "source_entry_variant"), "full_route_source_entry_targetstop_symbol_side_target_stop"),
    }
    join_diagnostics = support_join_diagnostics(branch_rows, support_groups)

    entry_branch_rows: list[dict[str, Any]] = []
    entry_variant_rows: list[dict[str, Any]] = []
    adverse_branch_rows: list[dict[str, Any]] = []
    adverse_action_rows: list[dict[str, Any]] = []
    unified_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[str]] = defaultdict(Counter)
    crosstab_counter: Counter[tuple[str, str]] = Counter()

    for index, branch in enumerate(branch_rows, 1):
        branch_id = str(branch.get("branch_queue_id"))
        entry = entry_by_branch.get(branch_id, {})
        adverse = adverse_by_branch.get(branch_id, {})
        source = source_by_branch.get(branch_id, {})
        ordering = ordering_by_branch.get(branch_id, {})
        positive = positive_by_branch.get(branch_id, {})
        entry_cls = str(branch.get("entry_geometry_retest_class"))
        adverse_cls = str(branch.get("adverse_stop_first_class"))
        entry_action_cls, entry_variants, entry_actions = entry_action(entry_cls)
        adverse_action_cls, adverse_variants, adverse_actions = adverse_action(adverse_cls)
        common = {
            "branch_queue_id": branch_id,
            "route_candidate_id": branch.get("route_candidate_id"),
            "symbol": branch.get("symbol"),
            "route_session": branch.get("route_session"),
            "side": branch.get("side"),
            "entry_variant": branch.get("entry_variant"),
            "target_stop_contract_id": branch.get("target_stop_contract_id"),
            "target_multiple": branch.get("target_multiple"),
            "stop_multiple": branch.get("stop_multiple"),
            "target_stop_reward_to_risk_ratio": branch.get("target_stop_reward_to_risk_ratio"),
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_PROXY_REDESIGN",
            "source_manifest_hash": manifest_hash,
            "generated_utc": generated_at,
        }
        outcome_fields = {
            "branch_result_class": branch.get("branch_result_class"),
            "target_stop_result": branch.get("target_stop_result"),
            "rstyle_lower_mean": branch.get("rstyle_lower_mean"),
            "rstyle_midpoint_mean": branch.get("rstyle_midpoint_mean"),
            "rstyle_upper_mean": branch.get("rstyle_upper_mean"),
            "rstyle_interval_rows": branch.get("rstyle_interval_rows"),
            "target_first_rows": branch.get("target_first_rows"),
            "stop_first_rows": branch.get("stop_first_rows"),
            "ambiguous_ordering_rows": branch.get("ambiguous_ordering_rows"),
            "no_fill_or_unfilled_rows": branch.get("no_fill_or_unfilled_rows"),
            "same_route_peer_delta": branch.get("same_route_peer_delta"),
            "same_route_peer_count": branch.get("same_route_peer_count"),
            "pass_control_delta_status": branch.get("pass_control_delta_status"),
        }
        source_order_fields = {
            "source_stress_action_class": branch.get("source_stress_action_class"),
            "source_confidence_status": branch.get("source_confidence_status"),
            "source_repairability_class": branch.get("source_repairability_class"),
            "exact_spread_repairability_class": branch.get("exact_spread_repairability_class"),
            "repair_feasibility_class": source.get("repair_feasibility_class") or branch.get("repair_feasibility_class"),
            "ordering_collapse_action_class": branch.get("ordering_collapse_action_class"),
            "ambiguity_collapse_class": branch.get("ambiguity_collapse_class"),
            "interval_preservation_class": branch.get("interval_preservation_class"),
            "effective_n_concentration_class": branch.get("effective_n_concentration_class"),
            "duplicate_inflation_ratio_material_rows_over_event_ids": branch.get("duplicate_inflation_ratio_material_rows_over_event_ids"),
            "unique_event_or_route_ids": branch.get("unique_event_or_route_ids"),
        }
        entry_record = {
            "entry_geometry_branch_redesign_id": f"OHLC-GTOS-ENTRY-ADVERSE-ENTRY-{index:05d}",
            **common,
            **outcome_fields,
            **source_order_fields,
            "entry_geometry_retest_class": entry_cls,
            "entry_redesign_action_class": entry_action_cls,
            "fillability_action_class": entry.get("fillability_action_class"),
            "fillability_bucket": entry.get("fillability_bucket"),
            "far_avoid_rows": entry.get("far_avoid_rows"),
            "far_avoid_status_counts": entry.get("far_avoid_status_counts"),
            "far_retest_rows": entry.get("far_retest_rows"),
            "far_retest_status_counts": entry.get("far_retest_status_counts"),
            "far_retest_miss_class_counts": entry.get("far_retest_miss_class_counts"),
            "far_mean_miss_distance_to_zero_over_rolling_median_range": entry.get("far_mean_miss_distance_to_zero_over_rolling_median_range"),
            "near_offset_rows": entry.get("near_offset_rows"),
            "near_offset_first_touch_proxy": entry.get("near_offset_first_touch_proxy"),
            "near_market_rows": entry.get("near_market_rows"),
            "near_market_first_touch_proxy": entry.get("near_market_first_touch_proxy"),
            "entry_proxy_variants": entry_variants,
            "entry_next_same_resource_actions": entry_actions,
        }
        entry_branch_rows.append(entry_record)
        for variant_index, variant in enumerate(entry_variants, 1):
            entry_variant_rows.append(
                {
                    "entry_geometry_variant_id": f"OHLC-GTOS-ENTRY-ADVERSE-ENTRY-VARIANT-{index:05d}-{variant_index:03d}",
                    **common,
                    "entry_geometry_retest_class": entry_cls,
                    "entry_redesign_action_class": entry_action_cls,
                    "entry_variant_action": variant,
                    "entry_next_same_resource_actions": entry_actions,
                    "source_requirement_status": entry.get("source_requirement_status"),
                }
            )
        adverse_record = {
            "adverse_stop_first_branch_redesign_id": f"OHLC-GTOS-ENTRY-ADVERSE-ADVERSE-{index:05d}",
            **common,
            **outcome_fields,
            **source_order_fields,
            "adverse_stop_first_class": adverse_cls,
            "adverse_redesign_action_class": adverse_action_cls,
            "exact_failure_cause": branch.get("exact_failure_cause") or adverse.get("exact_failure_cause"),
            "source_stress_action_class": branch.get("source_stress_action_class"),
            "ordering_collapse_action_class": branch.get("ordering_collapse_action_class"),
            "entry_geometry_retest_class": entry_cls,
            "rstyle_midpoint_mean": branch.get("rstyle_midpoint_mean"),
            "same_route_peer_delta": branch.get("same_route_peer_delta"),
            "far_avoid_status_counts": adverse.get("far_avoid_status_counts") or entry.get("far_avoid_status_counts"),
            "far_retest_status_counts": adverse.get("far_retest_status_counts") or entry.get("far_retest_status_counts"),
            "adverse_next_same_resource_actions": adverse_actions,
        }
        adverse_branch_rows.append(adverse_record)
        for variant_index, action_variant in enumerate(adverse_variants, 1):
            adverse_action_rows.append(
                {
                    "adverse_stop_first_action_id": f"OHLC-GTOS-ENTRY-ADVERSE-ACTION-{index:05d}-{variant_index:03d}",
                    **common,
                    "adverse_stop_first_class": adverse_cls,
                    "adverse_redesign_action_class": adverse_action_cls,
                    "adverse_action_variant": action_variant,
                    "adverse_next_same_resource_actions": adverse_actions,
                    "exact_failure_cause": branch.get("exact_failure_cause") or adverse.get("exact_failure_cause"),
                }
            )
        unified_rows.append(
            {
                "entry_adverse_unified_branch_local_implementation_id": f"OHLC-GTOS-ENTRY-ADVERSE-UNIFIED-{index:05d}",
                **common,
                **outcome_fields,
                **source_order_fields,
                "entry_geometry_retest_class": entry_cls,
                "entry_redesign_action_class": entry_action_cls,
                "adverse_stop_first_class": adverse_cls,
                "adverse_redesign_action_class": adverse_action_cls,
                "positive_challenger_class": branch.get("positive_challenger_class"),
                "positive_control_delta_modifier_class": positive.get("positive_control_delta_modifier_class"),
                "positive_concentration_modifier_class": positive.get("positive_concentration_modifier_class"),
                "entry_proxy_variants": entry_variants,
                "adverse_action_variants": adverse_variants,
                "exact_failure_cause": branch.get("exact_failure_cause"),
                "exact_success_cause": branch.get("exact_success_cause"),
                "targetstop_na_binding_class": branch.get("targetstop_na_binding_class"),
            }
        )
        for category, value in {
            "entry_geometry_retest_class": entry_cls,
            "entry_redesign_action_class": entry_action_cls,
            "adverse_stop_first_class": adverse_cls,
            "adverse_redesign_action_class": adverse_action_cls,
            "source_stress_action_class": branch.get("source_stress_action_class"),
            "ordering_collapse_action_class": branch.get("ordering_collapse_action_class"),
            "branch_result_class": branch.get("branch_result_class"),
            "target_stop_result": branch.get("target_stop_result"),
            "effective_n_concentration_class": branch.get("effective_n_concentration_class"),
        }.items():
            bucket_counters[category][str(value)] += 1
        crosstab_counter[(entry_cls, adverse_cls)] += 1

    crosstab_rows = []
    for (entry_cls, adverse_cls), count in sorted(crosstab_counter.items(), key=lambda item: (item[0][0], item[0][1])):
        crosstab_rows.append(
            {
                "entry_adverse_crosstab_bucket_id": f"OHLC-GTOS-ENTRY-ADVERSE-CROSSTAB-{len(crosstab_rows) + 1:04d}",
                "entry_geometry_retest_class": entry_cls,
                "adverse_stop_first_class": adverse_cls,
                "branch_count": int(count),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            crosstab_rows.append(
                {
                    "entry_adverse_crosstab_bucket_id": f"OHLC-GTOS-ENTRY-ADVERSE-CROSSTAB-{len(crosstab_rows) + 1:04d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "branch_count": int(count),
                    "branch_share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                }
            )
    question_rows = [
        {
            "question_id": "OHLC-GTOS-ENTRY-ADVERSE-QUESTION-001",
            "question": "Which entry-geometry branches become avoid, market-entry, offset, retest-zone, source-split, or preserve variants?",
            "answer_route": "Use ENTRY_GEOMETRY_VARIANT_EXPLODED_LEDGER with every branch preserved.",
        },
        {
            "question_id": "OHLC-GTOS-ENTRY-ADVERSE-QUESTION-002",
            "question": "Which stop-first adverse branches are immediate avoid/redesign versus source/order/mixed-positive preconditioned?",
            "answer_route": "Use ADVERSE_STOP_FIRST_ACTION_EXPLODED_LEDGER and ADVERSE_STOP_FIRST_BRANCH_REDESIGN_LEDGER.",
        },
        {
            "question_id": "OHLC-GTOS-ENTRY-ADVERSE-QUESTION-003",
            "question": "How do entry redesign classes intersect adverse stop-first classes?",
            "answer_route": "Use ENTRY_ADVERSE_CROSSTAB_BUCKET_LEDGER; no top-N crosstab truncation.",
        },
        {
            "question_id": "OHLC-GTOS-ENTRY-ADVERSE-QUESTION-004",
            "question": "Which support joins require compact keys and which retain full geometry keys?",
            "answer_route": "Use result join_diagnostics; exact_spread_delta and path_ambiguity use compact keys.",
        },
    ]
    for row in question_rows:
        row.update({"safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "generated_utc": generated_at, "not_completion": True})

    edge_checks = synth_result.get("edge_checks", {})
    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_PROXY_REDESIGN",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_branch_synthesis_rows": len(branch_rows),
            "input_entry_synthesis_rows": len(entry_by_branch),
            "input_adverse_synthesis_rows": len(adverse_by_branch),
            "entry_geometry_branch_redesign_rows": len(entry_branch_rows),
            "entry_geometry_variant_exploded_rows": len(entry_variant_rows),
            "adverse_stop_first_branch_redesign_rows": len(adverse_branch_rows),
            "adverse_stop_first_action_exploded_rows": len(adverse_action_rows),
            "entry_adverse_unified_branch_rows": len(unified_rows),
            "crosstab_bucket_rows": len(crosstab_rows),
            "source_manifest_rows": len(source_rows),
            "question_rows": len(question_rows),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "entry_adverse_crosstab": {f"{entry}__{adverse}": int(count) for (entry, adverse), count in sorted(crosstab_counter.items())},
        "join_diagnostics": join_diagnostics,
        "edge_checks": edge_checks,
        "source_manifest_hash": manifest_hash,
    }

    write_jsonl(ENTRY_BRANCH_PATH, entry_branch_rows)
    write_jsonl(ENTRY_VARIANT_PATH, entry_variant_rows)
    write_jsonl(ADVERSE_BRANCH_PATH, adverse_branch_rows)
    write_jsonl(ADVERSE_ACTION_PATH, adverse_action_rows)
    write_jsonl(UNIFIED_PATH, unified_rows)
    write_jsonl(CROSSTAB_BUCKET_PATH, crosstab_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER_PATH, source_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
