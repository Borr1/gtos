#!/usr/bin/env python3
"""Build branch-local implementation candidate specs from the 386-branch action synthesis.

This packet is one layer deeper than proxy scoring: it turns each branch row
into concrete branch-local replay/spec/code-surface actions without changing the
386-branch denominator or claiming live performance.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

SYNTH_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_BRANCH_LEDGER_2026-05-16.jsonl"
SYNTH_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_ENTRY_GEOMETRY_RETEST_LEDGER_2026-05-16.jsonl"
SYNTH_ADVERSE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_ADVERSE_STOP_FIRST_AVOID_REDESIGN_LEDGER_2026-05-16.jsonl"
SYNTH_POSITIVE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_POSITIVE_CHALLENGER_COMPARISON_LEDGER_2026-05-16.jsonl"
SYNTH_SOURCE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_SOURCE_STRESS_ACTION_LEDGER_2026-05-16.jsonl"
SYNTH_ORDERING_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_ORDERING_COLLAPSE_ACTION_LEDGER_2026-05-16.jsonl"
SYNTH_SEQUENCE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_IMPLEMENTATION_ACTION_SYNTHESIS_IMPLEMENTATION_SEQUENCE_EXPLODED_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_RESULT_2026-05-16.json"
BRANCH_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
ENTRY_SPEC_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_ENTRY_REDESIGN_SPEC_LEDGER_2026-05-16.jsonl"
ADVERSE_SPEC_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_ADVERSE_AVOID_REDESIGN_SPEC_LEDGER_2026-05-16.jsonl"
POSITIVE_SPEC_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_POSITIVE_CHALLENGER_SPEC_LEDGER_2026-05-16.jsonl"
SOURCE_SPEC_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_SOURCE_REPAIR_SPEC_LEDGER_2026-05-16.jsonl"
ORDERING_SPEC_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_ORDERING_COLLAPSE_SPEC_LEDGER_2026-05-16.jsonl"
CODE_SURFACE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_CODE_SURFACE_EXPLODED_LEDGER_2026-05-16.jsonl"
RULE_CARD_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_RULE_CARD_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Branch-local implementation candidate specification only. The packet "
    "preserves all 386 historical OHLC/MT5/Sierra proxy branches and maps them "
    "to replay/spec/code-surface actions for source repair, ordering collapse, "
    "entry redesign, adverse avoid/redesign, and positive challenger comparison. "
    "It does not claim broker R/PnL, realized expectancy, win-rate, validation, "
    "live-readiness, promotion, or live behavior change."
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


def group_by_branch(input_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in input_rows}


def group_many_by_branch(input_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[str(row.get("branch_queue_id"))].append(row)
    return grouped


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def source_manifest_rows() -> tuple[list[dict[str, Any]], str]:
    source_paths = [
        SYNTH_BRANCH_PATH,
        SYNTH_ENTRY_PATH,
        SYNTH_ADVERSE_PATH,
        SYNTH_POSITIVE_PATH,
        SYNTH_SOURCE_PATH,
        SYNTH_ORDERING_PATH,
        SYNTH_SEQUENCE_PATH,
    ]
    manifest_rows = []
    for index, path in enumerate(source_paths, 1):
        manifest_rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-BRANCH-LOCAL-IMPL-SOURCE-{index:03d}",
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "status": "HASHED",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(
        json.dumps(manifest_rows, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return manifest_rows, manifest_hash


def entry_spec(entry: dict[str, Any]) -> tuple[str, str, str, str, list[str]]:
    entry_cls = str(entry.get("entry_geometry_retest_class"))
    if entry_cls == "NEAR_MISS_ENTRY_CHALLENGER":
        return (
            "ENTRY_MARKET_AND_OFFSET_CHALLENGER_REPLAY_READY",
            "scripts/replay_branch_entry_market_offset_challengers.py",
            "Replay every near-miss offset and market-entry branch with source requirements attached.",
            "CURRENT_NEAR_MISS_LEDGER_ROWS_AVAILABLE",
            ["near_offset_first_touch_proxy", "near_market_first_touch_proxy"],
        )
    if entry_cls == "FAR_MISS_AVOID_OR_MARKET_PROXY_REDESIGN":
        return (
            "ENTRY_FAR_MISS_AVOID_OR_MARKET_PROXY_SPEC_READY",
            "src/research_infra/branch_entry_geometry_router.py",
            "Translate far miss/no-fill distance into avoid-filter and market-entry proxy branches.",
            "CURRENT_FAR_MISS_AVOID_AND_RETEST_ROWS_AVAILABLE",
            ["far_avoid_status_counts", "far_retest_status_counts", "far_mean_miss_distance_to_zero_over_rolling_median_range"],
        )
    if entry_cls == "WITHIN_RANGE_RETEST_REDESIGN":
        return (
            "ENTRY_WITHIN_RANGE_RETEST_ZONE_REDESIGN_SPEC_READY",
            "src/research_infra/branch_entry_geometry_router.py",
            "Build retest-zone and entry-offset redesign branches for within-range no-fill contexts.",
            "CURRENT_RETEST_REDESIGN_ROWS_AVAILABLE",
            ["far_retest_status_counts", "far_retest_miss_class_counts"],
        )
    if entry_cls == "MIXED_FILLABILITY_SOURCE_SPLIT":
        return (
            "ENTRY_FILLABILITY_SOURCE_SPLIT_ROUTER_REQUIRED",
            "src/research_infra/branch_fillability_source_splitter.py",
            "Split mixed fillability rows before using them as entry redesign or avoid-filter evidence.",
            "MIXED_SOURCE_ROWS_PRESENT",
            ["fillability_action_class", "fillability_bucket"],
        )
    return (
        "ENTRY_NO_BRANCH_LOCAL_REDESIGN_SCOPE",
        "none",
        "No entry-geometry redesign action is implied for this branch class.",
        "NOT_ENTRY_SCOPE",
        [],
    )


def adverse_spec(adverse: dict[str, Any]) -> tuple[str, str, str, str, list[str]]:
    adverse_cls = str(adverse.get("adverse_stop_first_class"))
    if adverse_cls == "STOP_FIRST_AVOID_OR_REDESIGN_READY":
        return (
            "ADVERSE_STOP_FIRST_AVOID_OR_REDESIGN_REPLAY_READY",
            "src/research_infra/branch_adverse_path_router.py",
            "Build avoid-filter and redesigned-entry variants for stop-first branches with no upstream source/order blocker.",
            "STOP_FIRST_READY_FROM_CURRENT_PROXY",
            ["target_stop_result", "rstyle_midpoint_mean", "exact_failure_cause"],
        )
    if adverse_cls == "STOP_FIRST_SOURCE_REPAIR_FIRST":
        return (
            "ADVERSE_STOP_FIRST_SOURCE_REPAIR_PRECONDITION",
            "scripts/build_branch_source_repair_queue.py",
            "Repair or stress exact-spread source before treating the stop-first path as an avoid/redesign candidate.",
            "SOURCE_REPAIR_REQUIRED",
            ["source_stress_action_class", "exact_failure_cause"],
        )
    if adverse_cls == "STOP_FIRST_ORDERING_COLLAPSE_FIRST":
        return (
            "ADVERSE_STOP_FIRST_ORDERING_COLLAPSE_PRECONDITION",
            "scripts/build_branch_ordering_collapse_queue.py",
            "Collapse or preserve ordering intervals before using stop-first as an avoid/redesign rule.",
            "ORDERING_COLLAPSE_REQUIRED",
            ["ordering_collapse_action_class", "exact_failure_cause"],
        )
    if adverse_cls == "STOP_FIRST_MIXED_POSITIVE_PROXY_REVIEW":
        return (
            "ADVERSE_STOP_FIRST_MIXED_POSITIVE_SPLIT_REQUIRED",
            "src/research_infra/branch_positive_adverse_splitter.py",
            "Split positive midpoint branches that still carry stop-first descriptors into source/order/control subbranches.",
            "MIXED_POSITIVE_STOP_FIRST_CONTEXT",
            ["branch_result_class", "same_route_peer_delta", "target_stop_result"],
        )
    return (
        "ADVERSE_NO_STOP_FIRST_SCOPE",
        "none",
        "No stop-first avoid/redesign action is implied for this branch.",
        "NOT_ADVERSE_SCOPE",
        [],
    )


def positive_spec(positive: dict[str, Any]) -> tuple[str, str, str, str, list[str]]:
    positive_cls = str(positive.get("positive_challenger_class"))
    if positive_cls == "POSITIVE_AFTER_EXACT_REPAIR":
        return (
            "POSITIVE_EXACT_REPAIRED_CHALLENGER_COMPARISON_READY",
            "src/research_infra/branch_positive_challenger_router.py",
            "Compare exact-repaired positive proxy branches after carrying control and concentration modifiers.",
            "CURRENT_EXACT_OR_RECOMPUTED_SOURCE_READY",
            ["rstyle_midpoint_mean", "same_route_peer_delta", "positive_control_delta_modifier_class"],
        )
    if positive_cls == "POSITIVE_ZERO_TO_SPREAD_REPLAY_COMPARABLE":
        return (
            "POSITIVE_ZERO_TO_SPREAD_M1_REPLAY_CHALLENGER_READY",
            "src/research_infra/branch_positive_challenger_router.py",
            "Compare zero-to-spread descriptor-shift branches using M1 replay evidence as the replayable proxy.",
            "CURRENT_M1_REPLAY_AVAILABLE",
            ["positive_source_modifier_class", "positive_ordering_modifier_class", "rstyle_midpoint_mean"],
        )
    if positive_cls == "POSITIVE_STRESS_INTERVAL_ONLY":
        return (
            "POSITIVE_STRESS_ONLY_CHALLENGER_NOT_SCALAR_COLLAPSED",
            "scripts/build_branch_source_stress_bounds.py",
            "Keep positive proxy branch as low/high stress-bounded until exact source is repaired or acquisition route closes.",
            "EXACT_SOURCE_UNAVAILABLE",
            ["positive_source_modifier_class", "rstyle_lower_mean", "rstyle_upper_mean"],
        )
    return (
        "POSITIVE_NO_CHALLENGER_SCOPE",
        "none",
        "No positive challenger comparison action is implied for this branch.",
        "NOT_POSITIVE_SCOPE",
        [],
    )


def source_spec(source: dict[str, Any]) -> tuple[str, str, str, str, list[str]]:
    source_cls = str(source.get("source_stress_action_class"))
    if source_cls == "EXACT_SPREAD_RECOMPUTED_USE_REPAIRED_DESCRIPTOR":
        return (
            "SOURCE_EXACT_SPREAD_RECOMPUTED_DESCRIPTOR_READY",
            "src/research_infra/branch_source_descriptor_repair.py",
            "Use repaired exact-spread descriptor as the preferred source branch.",
            "EXACT_SPREAD_RECOMPUTED",
            ["exact_spread_descriptor_delta_rows", "exact_descriptor_delta_status_counts"],
        )
    if source_cls == "CURRENT_EXACT_SOURCE_CLEAN_COST_CLASS_PRESERVED":
        return (
            "SOURCE_CURRENT_EXACT_CLEAN_PRESERVE",
            "src/research_infra/branch_source_descriptor_repair.py",
            "Preserve current exact-source cost class; no source repair required.",
            "CURRENT_EXACT_SOURCE_CLEAN",
            ["source_confidence_status", "repair_feasibility_class"],
        )
    if source_cls == "ZERO_TO_SPREAD_DESCRIPTOR_SHIFT_USE_M1_REPLAY":
        return (
            "SOURCE_ZERO_TO_SPREAD_SHIFT_USE_M1_REPLAY",
            "scripts/replay_branch_zero_to_spread_m1.py",
            "Use M1 spread-adjusted fill replay to keep zero-to-spread descriptor shifts comparable.",
            "M1_REPLAY_PROXY_AVAILABLE",
            ["source_repair_route_class", "exact_spread_repairability_class"],
        )
    if source_cls == "EXACT_SPREAD_UNAVAILABLE_LOW_HIGH_STRESS_ONLY":
        return (
            "SOURCE_EXACT_SPREAD_UNAVAILABLE_ACQUIRE_OR_STRESS",
            "scripts/build_branch_source_acquisition_and_stress.py",
            "Search current/owned/free source routes; until repaired, preserve low/high spread stress bounds.",
            "EXACT_SPREAD_SOURCE_UNAVAILABLE",
            ["exact_unavailable_source_status_counts", "sierra_depth_manifest_context"],
        )
    return (
        "SOURCE_TARGETSTOP_NA_BINDING_ONLY",
        "scripts/build_targetstop_na_signature_binding.py",
        "Keep target/stop NA rows in binding/provenance scope and route only through bound signature rows.",
        "TARGETSTOP_NA_BINDING",
        ["target_stop_contract_id"],
    )


def ordering_spec(ordering: dict[str, Any]) -> tuple[str, str, str, str, list[str]]:
    ordering_cls = str(ordering.get("ordering_collapse_action_class"))
    if ordering_cls == "M1_CHRONOLOGICAL_COLLAPSE_AVAILABLE":
        return (
            "ORDERING_M1_CHRONOLOGICAL_COLLAPSE_READY",
            "src/research_infra/branch_ordering_collapse.py",
            "Use existing M1 chronological evidence to collapse target/stop ordering.",
            "M1_CHRONOLOGICAL_SOURCE_AVAILABLE",
            ["m1_replay_first_touch_status_counts", "interval_preservation_rstyle_midpoint_mean"],
        )
    if ordering_cls == "M1_FILL_BAR_STRESS_INTERVAL_PRESERVED":
        return (
            "ORDERING_M1_FILL_BAR_STRESS_INTERVAL_REQUIRED",
            "scripts/build_branch_m1_fill_bar_ordering_stress.py",
            "Preserve conservative/optimistic M1 fill-bar interval; do not coerce it to one scalar result.",
            "M1_FILL_BAR_INTERVAL_SOURCE_AVAILABLE",
            ["m1_fill_bar_interval_status_counts", "interval_preservation_rstyle_lower_mean", "interval_preservation_rstyle_upper_mean"],
        )
    if ordering_cls == "M15_INTERVAL_ONLY_NO_M1_SOURCE":
        return (
            "ORDERING_M15_INTERVAL_ONLY_SOURCE_ROUTE_REQUIRED",
            "scripts/build_branch_m15_interval_source_route.py",
            "Keep M15 interval-only branches as interval evidence and search/proxy LTF ordering source.",
            "NO_M1_SOURCE_FOR_BRANCH_KEY",
            ["m15_same_bar_rows_for_branch_key", "interval_preservation_class"],
        )
    if ordering_cls == "NO_COLLAPSE_REQUIRED":
        return (
            "ORDERING_NO_COLLAPSE_REQUIRED",
            "none",
            "Ordering is already point/ordered enough for the current branch-local proxy class.",
            "ORDERING_NOT_BLOCKING",
            ["interval_preservation_class"],
        )
    if ordering_cls == "RECOVERED_PROXY_ONLY_NO_M1_KEY":
        return (
            "ORDERING_RECOVERED_PROXY_NO_M1_KEY_REQUIREMENT",
            "scripts/build_recovered_proxy_ordering_key_repair.py",
            "Preserve recovered proxy only row and create exact key repair/source requirement.",
            "RECOVERED_PROXY_WITHOUT_M1_KEY",
            ["recovered_signature_path_rows_for_branch_key"],
        )
    return (
        "ORDERING_TARGETSTOP_NA_BINDING_ONLY",
        "scripts/build_targetstop_na_signature_binding.py",
        "Target/stop NA row is binding/provenance scope, not an ordering collapse candidate.",
        "TARGETSTOP_NA_BINDING",
        ["target_stop_contract_id"],
    )


def branch_stage(branch: dict[str, Any], specs: dict[str, str]) -> str:
    if branch.get("target_stop_contract_id") == "TARGETSTOP_NA_NA":
        return "BINDING_SCOPE_ONLY"
    if specs["source"].startswith("SOURCE_EXACT_SPREAD_UNAVAILABLE"):
        return "SOURCE_ACQUISITION_OR_STRESS_FIRST"
    if specs["ordering"] in {
        "ORDERING_M1_FILL_BAR_STRESS_INTERVAL_REQUIRED",
        "ORDERING_M15_INTERVAL_ONLY_SOURCE_ROUTE_REQUIRED",
        "ORDERING_RECOVERED_PROXY_NO_M1_KEY_REQUIREMENT",
    }:
        return "ORDERING_COLLAPSE_OR_INTERVAL_FIRST"
    if specs["entry"] != "ENTRY_NO_BRANCH_LOCAL_REDESIGN_SCOPE":
        return "ENTRY_REDESIGN_REPLAY_SPEC_READY"
    if specs["adverse"] in {
        "ADVERSE_STOP_FIRST_AVOID_OR_REDESIGN_REPLAY_READY",
        "ADVERSE_STOP_FIRST_MIXED_POSITIVE_SPLIT_REQUIRED",
    }:
        return "ADVERSE_AVOID_REDESIGN_SPEC_READY"
    if specs["positive"] in {
        "POSITIVE_EXACT_REPAIRED_CHALLENGER_COMPARISON_READY",
        "POSITIVE_ZERO_TO_SPREAD_M1_REPLAY_CHALLENGER_READY",
    }:
        return "POSITIVE_CHALLENGER_SPEC_READY"
    return "PRESERVE_AND_ROUTE_BY_BUCKET"


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    artifacts = [
        (Path(__file__).resolve(), "builder"),
        (RESULT_PATH, "result"),
        (BRANCH_LEDGER_PATH, "branch_ledger"),
        (ENTRY_SPEC_PATH, "entry_redesign_spec_ledger"),
        (ADVERSE_SPEC_PATH, "adverse_avoid_redesign_spec_ledger"),
        (POSITIVE_SPEC_PATH, "positive_challenger_spec_ledger"),
        (SOURCE_SPEC_PATH, "source_repair_spec_ledger"),
        (ORDERING_SPEC_PATH, "ordering_collapse_spec_ledger"),
        (CODE_SURFACE_PATH, "code_surface_exploded_ledger"),
        (RULE_CARD_PATH, "rule_card_ledger"),
        (BUCKET_PATH, "bucket_ledger"),
        (QUESTION_PATH, "question_ledger"),
        (SOURCE_MANIFEST_LEDGER_PATH, "source_manifest_ledger"),
        (SUMMARY_PATH, "summary"),
    ]
    artifact_names = {path.name for path, _ in artifacts}
    manifest["outputs"] = [row for row in manifest.get("outputs", []) if row.get("artifact") not in artifact_names]
    for path, artifact_type in artifacts[1:]:
        manifest["outputs"].append(
            {
                "artifact": path.name,
                "category": "historical_ohlc_gtos_replay_branch_local_implementation_candidate_packet",
                "artifact_type": artifact_type,
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    existing_paths = {str(path.relative_to(REPO)).replace("\\", "/") for path, _ in artifacts}
    existing_paths.add(
        "research/science_program_2026_05/06_outcome_testing/"
        "weekend_mechanical_edge_factory_moonshot_2026_05_15/"
        "build_historical_ohlc_gtos_replay_branch_local_implementation_candidate_packet_2026_05_16.py"
    )
    manifest["artifacts"] = [row for row in manifest.get("artifacts", []) if row.get("path") not in existing_paths]
    for path, artifact_type in artifacts:
        manifest["artifacts"].append(
            {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": artifact_type}
        )
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "event_type": "branch_local_implementation_candidate_packet_built",
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
        "# Historical OHLC GTOS Replay Branch Local Implementation Candidate Packet",
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
    for category in [
        "branch_local_candidate_stage",
        "entry_local_impl_class",
        "adverse_local_impl_class",
        "positive_local_impl_class",
        "source_local_impl_class",
        "ordering_local_impl_class",
    ]:
        lines.extend(["", f"## {category}", ""])
        for bucket, count in result["bucket_distributions"][category].items():
            lines.append(f"- {bucket}: {count}")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows()

    branch_rows_in = rows(SYNTH_BRANCH_PATH)
    entry_by_branch = group_by_branch(rows(SYNTH_ENTRY_PATH))
    adverse_by_branch = group_by_branch(rows(SYNTH_ADVERSE_PATH))
    positive_by_branch = group_by_branch(rows(SYNTH_POSITIVE_PATH))
    source_by_branch = group_by_branch(rows(SYNTH_SOURCE_PATH))
    ordering_by_branch = group_by_branch(rows(SYNTH_ORDERING_PATH))
    sequence_by_branch = group_many_by_branch(rows(SYNTH_SEQUENCE_PATH))

    output_branch_rows: list[dict[str, Any]] = []
    entry_rows: list[dict[str, Any]] = []
    adverse_rows: list[dict[str, Any]] = []
    positive_rows: list[dict[str, Any]] = []
    source_spec_rows: list[dict[str, Any]] = []
    ordering_rows: list[dict[str, Any]] = []
    code_surface_rows: list[dict[str, Any]] = []
    bucket_counters: dict[str, Counter[str]] = defaultdict(Counter)
    rule_counter: Counter[tuple[str, str, str]] = Counter()

    for index, branch in enumerate(branch_rows_in, 1):
        branch_id = str(branch.get("branch_queue_id"))
        entry = entry_by_branch.get(branch_id, {})
        adverse = adverse_by_branch.get(branch_id, {})
        positive = positive_by_branch.get(branch_id, {})
        source = source_by_branch.get(branch_id, {})
        ordering = ordering_by_branch.get(branch_id, {})

        entry_cls, entry_surface, entry_action, entry_data, entry_fields = entry_spec(entry)
        adverse_cls, adverse_surface, adverse_action, adverse_data, adverse_fields = adverse_spec(adverse)
        positive_cls, positive_surface, positive_action, positive_data, positive_fields = positive_spec(positive)
        source_cls, source_surface, source_action, source_data, source_fields = source_spec(source)
        ordering_cls, ordering_surface, ordering_action, ordering_data, ordering_fields = ordering_spec(ordering)
        specs = {
            "entry": entry_cls,
            "adverse": adverse_cls,
            "positive": positive_cls,
            "source": source_cls,
            "ordering": ordering_cls,
        }
        stage = branch_stage(branch, specs)
        code_surfaces = {
            "ENTRY": entry_surface,
            "ADVERSE": adverse_surface,
            "POSITIVE": positive_surface,
            "SOURCE": source_surface,
            "ORDERING": ordering_surface,
        }
        field_base = {
            "branch_queue_id": branch_id,
            "route_candidate_id": branch.get("route_candidate_id"),
            "symbol": branch.get("symbol"),
            "route_session": branch.get("route_session"),
            "side": branch.get("side"),
            "entry_variant": branch.get("entry_variant"),
            "target_stop_contract_id": branch.get("target_stop_contract_id"),
            "target_multiple": branch.get("target_multiple"),
            "stop_multiple": branch.get("stop_multiple"),
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "generated_utc": generated_at,
        }
        branch_record = {
            "branch_local_implementation_candidate_id": f"OHLC-GTOS-BRANCH-LOCAL-IMPL-{index:05d}",
            **field_base,
            "branch_result_class": branch.get("branch_result_class"),
            "target_stop_result": branch.get("target_stop_result"),
            "rstyle_lower_mean": branch.get("rstyle_lower_mean"),
            "rstyle_midpoint_mean": branch.get("rstyle_midpoint_mean"),
            "rstyle_upper_mean": branch.get("rstyle_upper_mean"),
            "expectancy_style_proxy_method": branch.get("expectancy_style_proxy_method"),
            "pass_control_delta_status": branch.get("pass_control_delta_status"),
            "same_route_peer_delta": branch.get("same_route_peer_delta"),
            "positive_control_delta_modifier_class": branch.get("positive_control_delta_modifier_class"),
            "positive_concentration_modifier_class": branch.get("positive_concentration_modifier_class"),
            "effective_n_concentration_class": branch.get("effective_n_concentration_class"),
            "source_confidence_status": branch.get("source_confidence_status"),
            "ambiguity_status": branch.get("ambiguity_status"),
            "entry_geometry_retest_class": branch.get("entry_geometry_retest_class"),
            "adverse_stop_first_class": branch.get("adverse_stop_first_class"),
            "positive_challenger_class": branch.get("positive_challenger_class"),
            "source_stress_action_class": branch.get("source_stress_action_class"),
            "ordering_collapse_action_class": branch.get("ordering_collapse_action_class"),
            "entry_local_impl_class": entry_cls,
            "adverse_local_impl_class": adverse_cls,
            "positive_local_impl_class": positive_cls,
            "source_local_impl_class": source_cls,
            "ordering_local_impl_class": ordering_cls,
            "branch_local_candidate_stage": stage,
            "branch_local_code_surfaces": code_surfaces,
            "branch_local_next_computations": {
                "entry": entry_action,
                "adverse": adverse_action,
                "positive": positive_action,
                "source": source_action,
                "ordering": ordering_action,
            },
            "branch_local_data_status": {
                "entry": entry_data,
                "adverse": adverse_data,
                "positive": positive_data,
                "source": source_data,
                "ordering": ordering_data,
            },
            "source_manifest_hash": manifest_hash,
            "exact_failure_cause": branch.get("exact_failure_cause"),
            "exact_success_cause": branch.get("exact_success_cause"),
            "exact_missing_geometry_or_source_reason": branch.get("exact_missing_geometry_or_source_reason"),
            "upstream_sequence_rows": len(sequence_by_branch.get(branch_id, [])),
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET",
        }
        output_branch_rows.append(branch_record)

        families = [
            ("ENTRY", entry_cls, entry_surface, entry_action, entry_data, entry_fields, entry, entry_rows),
            ("ADVERSE", adverse_cls, adverse_surface, adverse_action, adverse_data, adverse_fields, adverse, adverse_rows),
            ("POSITIVE", positive_cls, positive_surface, positive_action, positive_data, positive_fields, positive, positive_rows),
            ("SOURCE", source_cls, source_surface, source_action, source_data, source_fields, source, source_spec_rows),
            ("ORDERING", ordering_cls, ordering_surface, ordering_action, ordering_data, ordering_fields, ordering, ordering_rows),
        ]
        for family, impl_class, surface, action, data_status, evidence_fields, source_row, target_rows in families:
            row = {
                f"{family.lower()}_local_implementation_spec_id": f"OHLC-GTOS-BRANCH-LOCAL-{family}-{index:05d}",
                **field_base,
                "action_family": family,
                "local_impl_class": impl_class,
                "proposed_branch_local_code_surface": surface,
                "next_same_resource_computation": action,
                "data_status": data_status,
                "evidence_fields_to_preserve": evidence_fields,
                "upstream_class": (
                    source_row.get("entry_geometry_retest_class")
                    or source_row.get("adverse_stop_first_class")
                    or source_row.get("positive_challenger_class")
                    or source_row.get("source_stress_action_class")
                    or source_row.get("ordering_collapse_action_class")
                ),
                "source_manifest_hash": manifest_hash,
            }
            target_rows.append(row)
            if surface != "none":
                code_surface_rows.append(
                    {
                        "code_surface_candidate_id": f"OHLC-GTOS-BRANCH-LOCAL-CODE-{index:05d}-{family}",
                        **field_base,
                        "action_family": family,
                        "local_impl_class": impl_class,
                        "proposed_branch_local_code_surface": surface,
                        "next_same_resource_computation": action,
                        "data_status": data_status,
                        "source_manifest_hash": manifest_hash,
                    }
                )
            rule_counter[(family, impl_class, surface)] += 1

        for category, value in {
            "branch_local_candidate_stage": stage,
            "entry_local_impl_class": entry_cls,
            "adverse_local_impl_class": adverse_cls,
            "positive_local_impl_class": positive_cls,
            "source_local_impl_class": source_cls,
            "ordering_local_impl_class": ordering_cls,
            "branch_result_class": branch.get("branch_result_class"),
            "target_stop_result": branch.get("target_stop_result"),
        }.items():
            bucket_counters[category][str(value)] += 1

    rule_rows = []
    for rule_index, ((family, impl_class, surface), count) in enumerate(sorted(rule_counter.items()), 1):
        rule_rows.append(
            {
                "rule_card_id": f"OHLC-GTOS-BRANCH-LOCAL-RULE-{rule_index:03d}",
                "action_family": family,
                "local_impl_class": impl_class,
                "proposed_branch_local_code_surface": surface,
                "branch_count": int(count),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-BRANCH-LOCAL-BUCKET-{len(bucket_rows) + 1:05d}",
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
            "question_id": "OHLC-GTOS-BRANCH-LOCAL-IMPL-QUESTION-001",
            "question": "Which branches can become entry redesign or market-entry replay specs immediately?",
            "answer_route": "Use ENTRY_REDESIGN_SPEC_LEDGER and branch_local_candidate_stage across all 386 rows.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-LOCAL-IMPL-QUESTION-002",
            "question": "Which stop-first branches are avoid/redesign-ready versus source/order preconditioned?",
            "answer_route": "Use ADVERSE_AVOID_REDESIGN_SPEC_LEDGER with source/order local classes preserved.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-LOCAL-IMPL-QUESTION-003",
            "question": "Which positive proxy branches are exact-repair comparable, M1 replay comparable, or stress-only?",
            "answer_route": "Use POSITIVE_CHALLENGER_SPEC_LEDGER with control and concentration modifiers from the branch ledger.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-LOCAL-IMPL-QUESTION-004",
            "question": "Which source gaps require current-source acquisition versus replay/proxy usage?",
            "answer_route": "Use SOURCE_REPAIR_SPEC_LEDGER; exact-unavailable rows remain stress-bounded until repaired.",
        },
        {
            "question_id": "OHLC-GTOS-BRANCH-LOCAL-IMPL-QUESTION-005",
            "question": "Which ordering branches collapse with M1, remain M1 interval stress, or remain M15 interval-only?",
            "answer_route": "Use ORDERING_COLLAPSE_SPEC_LEDGER and never scalar-collapse interval-only rows.",
        },
    ]
    for row in question_rows:
        row.update(
            {
                "generated_utc": generated_at,
                "not_completion": True,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "bucket_snapshot": {
                    "branch_local_candidate_stage": compact_counter(bucket_counters["branch_local_candidate_stage"]),
                    "entry_local_impl_class": compact_counter(bucket_counters["entry_local_impl_class"]),
                    "source_local_impl_class": compact_counter(bucket_counters["source_local_impl_class"]),
                    "ordering_local_impl_class": compact_counter(bucket_counters["ordering_local_impl_class"]),
                },
            }
        )

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "counts": {
            "input_branch_synthesis_rows": len(branch_rows_in),
            "input_entry_synthesis_rows": len(entry_by_branch),
            "input_adverse_synthesis_rows": len(adverse_by_branch),
            "input_positive_synthesis_rows": len(positive_by_branch),
            "input_source_synthesis_rows": len(source_by_branch),
            "input_ordering_synthesis_rows": len(ordering_by_branch),
            "branch_candidate_rows": len(output_branch_rows),
            "entry_redesign_spec_rows": len(entry_rows),
            "adverse_avoid_redesign_spec_rows": len(adverse_rows),
            "positive_challenger_spec_rows": len(positive_rows),
            "source_repair_spec_rows": len(source_spec_rows),
            "ordering_collapse_spec_rows": len(ordering_rows),
            "code_surface_exploded_rows": len(code_surface_rows),
            "rule_card_rows": len(rule_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_rows),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "source_manifest_hash": manifest_hash,
    }

    write_jsonl(BRANCH_LEDGER_PATH, output_branch_rows)
    write_jsonl(ENTRY_SPEC_PATH, entry_rows)
    write_jsonl(ADVERSE_SPEC_PATH, adverse_rows)
    write_jsonl(POSITIVE_SPEC_PATH, positive_rows)
    write_jsonl(SOURCE_SPEC_PATH, source_spec_rows)
    write_jsonl(ORDERING_SPEC_PATH, ordering_rows)
    write_jsonl(CODE_SURFACE_PATH, code_surface_rows)
    write_jsonl(RULE_CARD_PATH, rule_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER_PATH, source_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)

    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
