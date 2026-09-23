#!/usr/bin/env python3
"""Build branch-local code/replay proposal packet from full branch implementation specs."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

LOCAL_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_RESULT_2026-05-16.json"
LOCAL_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
LOCAL_CODE_SURFACE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_CODE_SURFACE_EXPLODED_LEDGER_2026-05-16.jsonl"
LOCAL_RULE_CARD_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_IMPLEMENTATION_CANDIDATE_PACKET_RULE_CARD_LEDGER_2026-05-16.jsonl"
ENTRY_ADVERSE_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_PROXY_REDESIGN_RESULT_2026-05-16.json"
ENTRY_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_GEOMETRY_BRANCH_REDESIGN_LEDGER_2026-05-16.jsonl"
ADVERSE_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ADVERSE_STOP_FIRST_BRANCH_REDESIGN_LEDGER_2026-05-16.jsonl"
SOURCE_ORDER_POSITIVE_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_ORDERING_POSITIVE_DEEP_RESULT_2026-05-16.json"
SOURCE_DEEP_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_DEEP_BRANCH_LEDGER_2026-05-16.jsonl"
ORDERING_DEEP_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ORDERING_COLLAPSE_DEEP_BRANCH_LEDGER_2026-05-16.jsonl"
POSITIVE_IMPL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_REPLAY_PROPOSAL_PACKET_RESULT_2026-05-16.json"
BRANCH_PACKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_REPLAY_PROPOSAL_BRANCH_LEDGER_2026-05-16.jsonl"
SURFACE_RESOLUTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_SURFACE_RESOLUTION_LEDGER_2026-05-16.jsonl"
POSITIVE_REPLAY_SPEC_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_REPLAY_SPEC_LEDGER_2026-05-16.jsonl"
SOURCE_ORDERING_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_ORDERING_REPLAY_QUEUE_LEDGER_2026-05-16.jsonl"
SURFACE_INVENTORY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_SURFACE_INVENTORY_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_REPLAY_PROPOSAL_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_REPLAY_PROPOSAL_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_REPLAY_PROPOSAL_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_REPLAY_PROPOSAL_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch-local code/replay proposal packet only. It maps every branch-local "
    "implementation candidate and positive challenger to research-tooling code "
    "surfaces, replay prerequisites, source/order blockers, and exact next "
    "computations. It does not change live behavior and does not claim broker "
    "R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
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


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def group_by_branch(input_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in input_rows}


def group_many_by_branch(input_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[str(row.get("branch_queue_id"))].append(row)
    return grouped


def source_manifest_rows() -> tuple[list[dict[str, Any]], str]:
    source_paths = [
        LOCAL_RESULT_PATH,
        LOCAL_BRANCH_PATH,
        LOCAL_CODE_SURFACE_PATH,
        LOCAL_RULE_CARD_PATH,
        ENTRY_ADVERSE_RESULT_PATH,
        ENTRY_BRANCH_PATH,
        ADVERSE_BRANCH_PATH,
        SOURCE_ORDER_POSITIVE_RESULT_PATH,
        SOURCE_DEEP_BRANCH_PATH,
        ORDERING_DEEP_BRANCH_PATH,
        POSITIVE_IMPL_PATH,
    ]
    manifest_rows = []
    for index, path in enumerate(source_paths, 1):
        manifest_rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-CODE-REPLAY-SOURCE-{index:03d}",
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "status": "HASHED",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(manifest_rows, sort_keys=True).encode("utf-8")).hexdigest()
    return manifest_rows, manifest_hash


def surface_mode(surface: str) -> str:
    if surface == "none":
        return "NO_CODE_SURFACE"
    if surface.startswith("src/research_infra/"):
        return "RESEARCH_HELPER_MODULE"
    if surface.startswith("scripts/"):
        return "REPLAY_OR_PACKET_BUILDER_SCRIPT"
    if surface.startswith("src/components/") or surface.startswith("prompts/") or surface.startswith("config/"):
        return "LIVE_SURFACE_REQUIRES_SEPARATE_APPROVAL"
    return "OTHER_BRANCH_LOCAL_RESEARCH_SURFACE"


def readiness_from_status(data_status: str, local_class: str) -> str:
    joined = f"{data_status} {local_class}"
    if ("NOT_" in joined and "NOT_POSITIVE_SCOPE" in joined) or ("NO_" in joined and "NO_STOP_FIRST_SCOPE" in joined):
        return "NOT_SCOPE_CONTROL_ROW"
    if "UNAVAILABLE" in joined or "SOURCE_REPAIR" in joined or "ACQUIRE" in joined:
        return "SOURCE_ACQUISITION_OR_STRESS_REQUIRED"
    if "M15_INTERVAL" in joined or "M15_ONLY" in joined:
        return "M15_INTERVAL_NON_EXACT_REPLAY_REQUIRED"
    if "FILL_BAR" in joined or "STRESS_INTERVAL" in joined:
        return "M1_FILL_BAR_INTERVAL_REPLAY_REQUIRED"
    if "EXACT" in joined or "M1" in joined or "CURRENT" in joined or "READY" in joined or "AVAILABLE" in joined:
        return "CURRENT_REPLAY_OR_PROXY_READY"
    if "BINDING" in joined:
        return "SIGNATURE_BINDING_ONLY"
    return "REVIEW_REQUIRED"


def branch_priority(branch: dict[str, Any]) -> str:
    stage = str(branch.get("branch_local_candidate_stage"))
    if stage == "POSITIVE_CHALLENGER_SPEC_READY":
        return "POSITIVE_CHALLENGER_REPLAY_FIRST"
    if stage == "ENTRY_REDESIGN_REPLAY_SPEC_READY":
        return "ENTRY_REDESIGN_REPLAY_FIRST"
    if stage == "SOURCE_ACQUISITION_OR_STRESS_FIRST":
        return "SOURCE_ACQUISITION_OR_STRESS_FIRST"
    if stage == "ORDERING_COLLAPSE_OR_INTERVAL_FIRST":
        return "ORDERING_COLLAPSE_OR_INTERVAL_FIRST"
    return "BINDING_OR_CONTROL_SCOPE"


def positive_replay_status(row: dict[str, Any]) -> tuple[str, bool, str]:
    action = str(row.get("positive_deep_action_class"))
    source_class = str(row.get("source_stress_action_class"))
    ordering_class = str(row.get("ordering_collapse_action_class"))
    if action == "POSITIVE_EXACT_REPAIR_COMPARISON":
        if ordering_class == "M1_FILL_BAR_STRESS_INTERVAL_PRESERVED":
            return ("REPLAYABLE_WITH_EXACT_REPAIR_AND_M1_FILL_BAR_INTERVAL", True, "Use exact-spread repaired descriptor and preserve conservative/optimistic fill-bar bounds.")
        return ("REPLAYABLE_WITH_EXACT_REPAIR", True, "Use exact-spread repaired descriptor and current target/stop path proxy.")
    if action == "POSITIVE_ZERO_TO_SPREAD_M1_REPLAY_COMPARISON":
        return ("REPLAYABLE_WITH_M1_SPREAD_ADJUSTED_PROXY", True, "Use M1 spread-adjusted fill replay; do not compare against zero-cost descriptors.")
    if action == "POSITIVE_STRESS_ONLY_NOT_SCALAR_COLLAPSED":
        return ("STRESS_INTERVAL_ONLY_NOT_SCALAR_REPLAY", False, "Keep low/high stress interval as bounds; exact scalar comparison requires source acquisition.")
    if source_class == "EXACT_SPREAD_UNAVAILABLE_LOW_HIGH_STRESS_ONLY":
        return ("SOURCE_STRESS_FIRST", False, "Acquire exact source or keep stress-pair interval before positive comparison.")
    return ("POSITIVE_SCOPE_REVIEW_REQUIRED", False, "Review positive challenger scope and prerequisites.")


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    artifact_paths = [
        RESULT_PATH,
        BRANCH_PACKET_PATH,
        SURFACE_RESOLUTION_PATH,
        POSITIVE_REPLAY_SPEC_PATH,
        SOURCE_ORDERING_QUEUE_PATH,
        SURFACE_INVENTORY_PATH,
        BUCKET_PATH,
        QUESTION_PATH,
        SOURCE_MANIFEST_LEDGER_PATH,
        SUMMARY_PATH,
        Path(__file__).resolve(),
    ]
    records = []
    for path in artifact_paths:
        records.append(
            {
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "category": "historical_ohlc_gtos_replay_branch_code_replay_proposal",
            }
        )
    manifest["historical_ohlc_branch_code_replay_proposal_packet_2026_05_16"] = {
        "generated_utc": generated_at,
        "result": records[0],
        "artifacts": records,
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
    }
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(result: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "event_type": "branch_code_replay_proposal_packet_built",
        "artifact": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = ["# Branch Code Replay Proposal Packet", "", f"Generated UTC: `{result['generated_utc']}`", "", "## Boundary", "", CLAIM_BOUNDARY, "", "## Counts", ""]
    for key, value in result["counts"].items():
        lines.append(f"- {key}: {value}")
    for category in ["surface_mode", "surface_file_status", "branch_priority", "positive_replay_status"]:
        lines.extend(["", f"## {category}", ""])
        for bucket, count in result["bucket_distributions"].get(category, {}).items():
            lines.append(f"- {bucket}: {count}")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows()
    local_result = read_json(LOCAL_RESULT_PATH)
    source_order_positive_result = read_json(SOURCE_ORDER_POSITIVE_RESULT_PATH)
    branch_rows = rows(LOCAL_BRANCH_PATH)
    code_rows = rows(LOCAL_CODE_SURFACE_PATH)
    positive_rows = rows(POSITIVE_IMPL_PATH)
    entry_by_branch = group_by_branch(rows(ENTRY_BRANCH_PATH))
    adverse_by_branch = group_by_branch(rows(ADVERSE_BRANCH_PATH))
    source_by_branch = group_by_branch(rows(SOURCE_DEEP_BRANCH_PATH))
    ordering_by_branch = group_by_branch(rows(ORDERING_DEEP_BRANCH_PATH))
    code_by_branch = group_many_by_branch(code_rows)
    positive_by_branch = group_by_branch(positive_rows)

    bucket_counters: dict[str, Counter[str]] = defaultdict(Counter)
    branch_packet_rows: list[dict[str, Any]] = []
    surface_resolution_rows: list[dict[str, Any]] = []
    positive_replay_rows: list[dict[str, Any]] = []
    source_ordering_queue_rows: list[dict[str, Any]] = []
    surface_inventory_counter: dict[str, Counter[str]] = defaultdict(Counter)

    for index, branch in enumerate(branch_rows, 1):
        branch_id = str(branch.get("branch_queue_id"))
        branch_surfaces = code_by_branch.get(branch_id, [])
        positive = positive_by_branch.get(branch_id, {})
        source = source_by_branch.get(branch_id, {})
        ordering = ordering_by_branch.get(branch_id, {})
        entry = entry_by_branch.get(branch_id, {})
        adverse = adverse_by_branch.get(branch_id, {})
        priority = branch_priority(branch)
        positive_status = "NOT_POSITIVE_CHALLENGER_SCOPE"
        positive_replayable = False
        if positive:
            positive_status, positive_replayable, _ = positive_replay_status(positive)
        current_surface_count = 0
        new_surface_count = 0
        ready_surface_count = 0
        source_required_count = 0
        m15_interval_count = 0
        m1_interval_count = 0
        for surface_row in branch_surfaces:
            surface = str(surface_row.get("proposed_branch_local_code_surface"))
            mode = surface_mode(surface)
            abs_surface = REPO / surface if surface != "none" else None
            exists = bool(abs_surface and abs_surface.exists())
            file_status = "EXISTING_FILE" if exists else "BRANCH_LOCAL_NEW_FILE_REQUIRED"
            if mode == "NO_CODE_SURFACE":
                file_status = "NO_FILE_REQUIRED"
            if exists:
                current_surface_count += 1
            elif mode != "NO_CODE_SURFACE":
                new_surface_count += 1
            readiness = readiness_from_status(str(surface_row.get("data_status")), str(surface_row.get("local_impl_class")))
            if readiness == "CURRENT_REPLAY_OR_PROXY_READY":
                ready_surface_count += 1
            if readiness == "SOURCE_ACQUISITION_OR_STRESS_REQUIRED":
                source_required_count += 1
            if readiness == "M15_INTERVAL_NON_EXACT_REPLAY_REQUIRED":
                m15_interval_count += 1
            if readiness == "M1_FILL_BAR_INTERVAL_REPLAY_REQUIRED":
                m1_interval_count += 1
            surface_inventory_counter[surface]["surface_rows"] += 1
            surface_inventory_counter[surface][mode] += 1
            surface_inventory_counter[surface][file_status] += 1
            surface_resolution_rows.append(
                {
                    "surface_resolution_id": f"OHLC-GTOS-CODE-REPLAY-SURFACE-{len(surface_resolution_rows) + 1:05d}",
                    **{key: branch.get(key) for key in ["branch_queue_id", "route_candidate_id", "symbol", "route_session", "side", "entry_variant", "target_stop_contract_id", "target_multiple", "stop_multiple"]},
                    "action_family": surface_row.get("action_family"),
                    "proposed_branch_local_code_surface": surface,
                    "surface_mode": mode,
                    "surface_file_status": file_status,
                    "surface_exists_on_disk": exists,
                    "surface_hash_if_existing": sha256_file(abs_surface) if exists and abs_surface and abs_surface.is_file() else None,
                    "local_impl_class": surface_row.get("local_impl_class"),
                    "data_status": surface_row.get("data_status"),
                    "replay_readiness_class": readiness,
                    "next_same_resource_computation": surface_row.get("next_same_resource_computation"),
                    "live_surface_boundary": "RESEARCH_TOOLING_ONLY" if mode != "LIVE_SURFACE_REQUIRES_SEPARATE_APPROVAL" else "LIVE_SURFACE_SEPARATE_APPROVAL_REQUIRED",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                }
            )
            bucket_counters["surface_mode"][mode] += 1
            bucket_counters["surface_file_status"][file_status] += 1
            bucket_counters["replay_readiness_class"][readiness] += 1
            bucket_counters["action_family"][str(surface_row.get("action_family"))] += 1

        branch_packet = {
            "branch_code_replay_proposal_id": f"OHLC-GTOS-CODE-REPLAY-BRANCH-{index:05d}",
            **{key: branch.get(key) for key in ["branch_queue_id", "route_candidate_id", "symbol", "route_session", "side", "entry_variant", "target_stop_contract_id", "target_multiple", "stop_multiple"]},
            "branch_result_class": branch.get("branch_result_class"),
            "target_stop_result": branch.get("target_stop_result"),
            "expectancy_style_proxy_method": branch.get("expectancy_style_proxy_method"),
            "rstyle_lower_mean": branch.get("rstyle_lower_mean"),
            "rstyle_midpoint_mean": branch.get("rstyle_midpoint_mean"),
            "rstyle_upper_mean": branch.get("rstyle_upper_mean"),
            "pass_control_delta_status": branch.get("pass_control_delta_status"),
            "effective_n_concentration_class": branch.get("effective_n_concentration_class"),
            "same_route_peer_delta": branch.get("same_route_peer_delta"),
            "positive_control_delta_modifier_class": branch.get("positive_control_delta_modifier_class"),
            "positive_concentration_modifier_class": branch.get("positive_concentration_modifier_class"),
            "source_confidence_status": branch.get("source_confidence_status"),
            "cost_sensitivity_proxy_status": branch.get("source_stress_action_class"),
            "ambiguity_status": branch.get("ambiguity_status"),
            "exact_failure_cause": branch.get("exact_failure_cause"),
            "exact_success_cause": branch.get("exact_success_cause"),
            "exact_missing_geometry_or_source_reason": branch.get("exact_missing_geometry_or_source_reason"),
            "branch_priority": priority,
            "entry_replay_action_class": entry.get("entry_redesign_action_class"),
            "adverse_replay_action_class": adverse.get("adverse_redesign_action_class"),
            "source_deep_action_class": source.get("source_deep_action_class"),
            "ordering_deep_action_class": ordering.get("ordering_deep_action_class"),
            "positive_replay_status": positive_status,
            "positive_replayable_now": positive_replayable,
            "code_surface_rows": len(branch_surfaces),
            "existing_code_surface_rows": current_surface_count,
            "new_code_surface_rows": new_surface_count,
            "current_replay_ready_surface_rows": ready_surface_count,
            "source_required_surface_rows": source_required_count,
            "m15_interval_surface_rows": m15_interval_count,
            "m1_interval_surface_rows": m1_interval_count,
            "branch_local_next_computations": branch.get("branch_local_next_computations"),
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
        branch_packet_rows.append(branch_packet)
        bucket_counters["branch_priority"][priority] += 1
        bucket_counters["positive_replay_status"][positive_status] += 1
        bucket_counters["branch_result_class"][str(branch.get("branch_result_class"))] += 1

        source_ordering_queue_rows.append(
            {
                "source_ordering_replay_queue_id": f"OHLC-GTOS-CODE-REPLAY-SRCORD-{index:05d}",
                **{key: branch.get(key) for key in ["branch_queue_id", "route_candidate_id", "symbol", "route_session", "side", "entry_variant", "target_stop_contract_id", "target_multiple", "stop_multiple"]},
                "source_stress_action_class": branch.get("source_stress_action_class"),
                "source_deep_action_class": source.get("source_deep_action_class"),
                "ordering_collapse_action_class": branch.get("ordering_collapse_action_class"),
                "ordering_deep_action_class": ordering.get("ordering_deep_action_class"),
                "source_support_rows": {
                    "exact_spread_descriptor_delta_rows": source.get("exact_spread_descriptor_delta_rows"),
                    "exact_spread_unavailable_stress_rows": source.get("exact_spread_unavailable_stress_rows"),
                    "m1_spread_adjusted_replay_rows": source.get("m1_spread_adjusted_replay_rows"),
                    "m1_fill_bar_stress_rows": source.get("m1_fill_bar_stress_rows"),
                },
                "ordering_support_rows": {
                    "path_ambiguity_rows": ordering.get("path_ambiguity_rows"),
                    "m1_replay_rows": ordering.get("m1_replay_rows"),
                    "m1_fill_bar_stress_rows": ordering.get("m1_fill_bar_stress_rows"),
                    "recovered_signature_path_rows": ordering.get("recovered_signature_path_rows"),
                },
                "queue_action": priority,
                "m15_only_is_exact_chronology": ordering.get("m15_only_is_exact_chronology"),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )

    positive_surface_by_branch = {
        row.get("branch_queue_id"): row
        for row in surface_resolution_rows
        if row.get("action_family") == "POSITIVE"
    }
    for index, positive in enumerate(positive_rows, 1):
        status, replayable, note = positive_replay_status(positive)
        surface = positive_surface_by_branch.get(positive.get("branch_queue_id"), {})
        positive_replay_rows.append(
            {
                "positive_challenger_replay_spec_id": f"OHLC-GTOS-CODE-REPLAY-POSITIVE-{index:05d}",
                **{key: positive.get(key) for key in ["branch_queue_id", "route_candidate_id", "symbol", "route_session", "side", "entry_variant", "target_stop_contract_id", "target_multiple", "stop_multiple"]},
                "positive_challenger_class": positive.get("positive_challenger_class"),
                "positive_deep_action_class": positive.get("positive_deep_action_class"),
                "positive_replay_status": status,
                "positive_replayable_now": replayable,
                "positive_replay_note": note,
                "source_stress_action_class": positive.get("source_stress_action_class"),
                "ordering_collapse_action_class": positive.get("ordering_collapse_action_class"),
                "positive_control_delta_modifier_class": positive.get("positive_control_delta_modifier_class"),
                "positive_concentration_modifier_class": positive.get("positive_concentration_modifier_class"),
                "same_route_peer_delta": positive.get("same_route_peer_delta"),
                "same_route_peer_count": positive.get("same_route_peer_count"),
                "rstyle_lower_mean": positive.get("rstyle_lower_mean"),
                "rstyle_midpoint_mean": positive.get("rstyle_midpoint_mean"),
                "rstyle_upper_mean": positive.get("rstyle_upper_mean"),
                "target_stop_result": positive.get("target_stop_result"),
                "proposed_branch_local_code_surface": surface.get("proposed_branch_local_code_surface"),
                "surface_file_status": surface.get("surface_file_status"),
                "surface_mode": surface.get("surface_mode"),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        bucket_counters["positive_replay_status_detail"][status] += 1
        bucket_counters["positive_replayable_now"][str(replayable)] += 1

    surface_inventory_rows = []
    for index, (surface, counter) in enumerate(sorted(surface_inventory_counter.items()), 1):
        abs_surface = REPO / surface if surface != "none" else None
        surface_inventory_rows.append(
            {
                "surface_inventory_id": f"OHLC-GTOS-CODE-REPLAY-INVENTORY-{index:04d}",
                "proposed_branch_local_code_surface": surface,
                "surface_rows": int(counter["surface_rows"]),
                "surface_mode": next((key for key in counter if key in {"RESEARCH_HELPER_MODULE", "REPLAY_OR_PACKET_BUILDER_SCRIPT", "LIVE_SURFACE_REQUIRES_SEPARATE_APPROVAL", "OTHER_BRANCH_LOCAL_RESEARCH_SURFACE"}), "NO_CODE_SURFACE"),
                "surface_file_status": "EXISTING_FILE" if bool(abs_surface and abs_surface.exists()) else "BRANCH_LOCAL_NEW_FILE_REQUIRED",
                "surface_exists_on_disk": bool(abs_surface and abs_surface.exists()),
                "surface_hash_if_existing": sha256_file(abs_surface) if abs_surface and abs_surface.exists() and abs_surface.is_file() else None,
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
                    "bucket_id": f"OHLC-GTOS-CODE-REPLAY-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "branch_or_surface_count": int(count),
                    "share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                }
            )

    question_rows = [
        {"question_id": "OHLC-GTOS-CODE-REPLAY-QUESTION-001", "question": "Which proposed code surfaces already exist and which require new branch-local files?", "answer_route": "Use code surface inventory and resolution ledgers."},
        {"question_id": "OHLC-GTOS-CODE-REPLAY-QUESTION-002", "question": "Which positive challenger branches can be replayed now from exact/M1 proxy evidence versus stress-only bounds?", "answer_route": "Use positive challenger replay spec ledger."},
        {"question_id": "OHLC-GTOS-CODE-REPLAY-QUESTION-003", "question": "Which branches require source acquisition or M15/M1 ordering work before a scalar comparison?", "answer_route": "Use source/ordering replay queue ledger."},
    ]
    for row in question_rows:
        row.update({"safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "generated_utc": generated_at, "not_completion": True})

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_REPLAY_PROPOSAL_PACKET",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_branch_candidate_rows": len(branch_rows),
            "input_code_surface_rows": len(code_rows),
            "input_positive_candidate_rows": len(positive_rows),
            "branch_code_replay_rows": len(branch_packet_rows),
            "code_surface_resolution_rows": len(surface_resolution_rows),
            "positive_challenger_replay_spec_rows": len(positive_replay_rows),
            "source_ordering_replay_queue_rows": len(source_ordering_queue_rows),
            "surface_inventory_rows": len(surface_inventory_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_rows),
        },
        "upstream_counts": {
            "local_branch_candidate_rows": local_result.get("counts", {}).get("branch_candidate_rows"),
            "local_code_surface_rows": local_result.get("counts", {}).get("code_surface_exploded_rows"),
            "positive_implementation_candidate_rows": source_order_positive_result.get("counts", {}).get("positive_implementation_candidate_rows"),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "source_manifest_hash": manifest_hash,
    }

    for path, output_rows in [
        (BRANCH_PACKET_PATH, branch_packet_rows),
        (SURFACE_RESOLUTION_PATH, surface_resolution_rows),
        (POSITIVE_REPLAY_SPEC_PATH, positive_replay_rows),
        (SOURCE_ORDERING_QUEUE_PATH, source_ordering_queue_rows),
        (SURFACE_INVENTORY_PATH, surface_inventory_rows),
        (BUCKET_PATH, bucket_rows),
        (QUESTION_PATH, question_rows),
        (SOURCE_MANIFEST_LEDGER_PATH, source_rows),
    ]:
        write_jsonl(path, output_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(result)
    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
