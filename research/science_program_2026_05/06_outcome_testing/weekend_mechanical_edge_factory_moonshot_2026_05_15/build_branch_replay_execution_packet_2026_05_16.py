#!/usr/bin/env python3
"""Convert branch code/replay proposals into concrete execution work units."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

CODE_REPLAY_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_REPLAY_PROPOSAL_PACKET_RESULT_2026-05-16.json"
CODE_REPLAY_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_REPLAY_PROPOSAL_BRANCH_LEDGER_2026-05-16.jsonl"
CODE_SURFACE_RESOLUTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_SURFACE_RESOLUTION_LEDGER_2026-05-16.jsonl"
POSITIVE_REPLAY_SPEC_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_POSITIVE_CHALLENGER_REPLAY_SPEC_LEDGER_2026-05-16.jsonl"
SOURCE_ORDERING_QUEUE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_ORDERING_REPLAY_QUEUE_LEDGER_2026-05-16.jsonl"
SURFACE_INVENTORY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CODE_SURFACE_INVENTORY_LEDGER_2026-05-16.jsonl"
SOURCE_DEEP_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_STRESS_DEEP_BRANCH_LEDGER_2026-05-16.jsonl"
ORDERING_DEEP_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ORDERING_COLLAPSE_DEEP_BRANCH_LEDGER_2026-05-16.jsonl"
SOURCE_UNAVAILABLE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_UNAVAILABLE_ACQUISITION_LEDGER_2026-05-16.jsonl"
SOURCE_PROXY_STRESS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SOURCE_PROXY_STRESS_INTERVAL_LEDGER_2026-05-16.jsonl"
ZERO_TO_SPREAD_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ZERO_TO_SPREAD_M1_REPLAY_IMPLICATION_LEDGER_2026-05-16.jsonl"
EXACT_REPAIR_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_EXACT_REPAIR_BRANCH_LEDGER_2026-05-16.jsonl"
M1_CHRONO_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_CHRONOLOGICAL_COLLAPSE_LEDGER_2026-05-16.jsonl"
M1_FILL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M1_FILL_BAR_STRESS_INTERVAL_LEDGER_2026-05-16.jsonl"
M15_ONLY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_ONLY_INTERVAL_ROUTE_LEDGER_2026-05-16.jsonl"
RECOVERED_NO_M1_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RECOVERED_PROXY_NO_M1_KEY_LEDGER_2026-05-16.jsonl"
TARGETSTOP_BINDING_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_TARGETSTOP_NA_BINDING_PRESERVATION_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_PACKET_RESULT_2026-05-16.json"
BRANCH_EXECUTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_BRANCH_LEDGER_2026-05-16.jsonl"
WORK_UNIT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_WORK_UNIT_LEDGER_2026-05-16.jsonl"
SOURCE_ORDERING_EXECUTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_SOURCE_ORDERING_LEDGER_2026-05-16.jsonl"
POSITIVE_EXECUTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_POSITIVE_CHALLENGER_LEDGER_2026-05-16.jsonl"
BLOCKER_REPAIR_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_BLOCKER_REPAIR_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {"NO_PROMOTION_VERDICT": True, "validation_safe": False, "outcome_review_opened": False, "live_effect": False}
CLAIM_BOUNDARY = (
    "Branch replay execution packet only. It converts every branch code/replay "
    "proposal into same-resource work units, source/ordering execution classes, "
    "positive challenger execution classes, and blocker/repair classes. It does "
    "not change live behavior and does not claim broker R/PnL, realized expectancy, "
    "win-rate, validation, live-readiness, or promotion."
)

ACTION_PRIORITY = {
    "SOURCE": 1,
    "ORDERING": 2,
    "POSITIVE": 3,
    "ENTRY": 4,
    "ADVERSE": 5,
}


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


def by_branch(input_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in input_rows}


def many_by_branch(input_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in input_rows:
        grouped[str(row.get("branch_queue_id"))].append(row)
    return grouped


def source_manifest_rows() -> tuple[list[dict[str, Any]], str]:
    source_paths = [
        CODE_REPLAY_RESULT_PATH,
        CODE_REPLAY_BRANCH_PATH,
        CODE_SURFACE_RESOLUTION_PATH,
        POSITIVE_REPLAY_SPEC_PATH,
        SOURCE_ORDERING_QUEUE_PATH,
        SURFACE_INVENTORY_PATH,
        SOURCE_DEEP_BRANCH_PATH,
        ORDERING_DEEP_BRANCH_PATH,
        SOURCE_UNAVAILABLE_PATH,
        SOURCE_PROXY_STRESS_PATH,
        ZERO_TO_SPREAD_PATH,
        EXACT_REPAIR_PATH,
        M1_CHRONO_PATH,
        M1_FILL_PATH,
        M15_ONLY_PATH,
        RECOVERED_NO_M1_PATH,
        TARGETSTOP_BINDING_PATH,
    ]
    manifest_rows = []
    for index, path in enumerate(source_paths, 1):
        manifest_rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-REPLAY-EXEC-SOURCE-{index:03d}",
                "path": str(path.relative_to(REPO)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "status": "HASHED",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(manifest_rows, sort_keys=True).encode("utf-8")).hexdigest()
    return manifest_rows, manifest_hash


def point_or_interval(row: dict[str, Any]) -> str:
    low = row.get("rstyle_lower_mean")
    mid = row.get("rstyle_midpoint_mean")
    high = row.get("rstyle_upper_mean")
    if low is None or mid is None or high is None:
        return "NO_RSTYLE_INTERVAL_AVAILABLE"
    if low == mid == high:
        return "SEALED_POINT_PROXY"
    if low <= 0 <= high:
        return "SEALED_INTERVAL_STRADDLES_ZERO"
    if low > 0:
        return "SEALED_INTERVAL_ALL_POSITIVE"
    if high < 0:
        return "SEALED_INTERVAL_ALL_NEGATIVE"
    return "SEALED_INTERVAL_MIXED_NONZERO"


def source_execution_class(source_class: str) -> str:
    if source_class == "SOURCE_EXACT_REPAIR_RECOMPUTED_READY":
        return "SOURCE_EXACT_REPAIR_COMPUTABLE_NOW"
    if source_class == "SOURCE_EXACT_CLEAN_PRESERVED":
        return "SOURCE_EXACT_CLEAN_COMPUTABLE_NOW"
    if source_class == "SOURCE_ZERO_TO_SPREAD_REPLAY_IMPLICATION":
        return "SOURCE_M1_SPREAD_PROXY_COMPUTABLE_NOW"
    if source_class == "SOURCE_UNAVAILABLE_ACQUIRE_OR_STRESS":
        return "SOURCE_EXACT_UNAVAILABLE_STRESS_OR_ACQUIRE"
    if source_class == "SOURCE_TARGETSTOP_NA_BINDING_ONLY":
        return "SOURCE_BINDING_ONLY_NO_SCALAR"
    return "SOURCE_REVIEW_REQUIRED"


def ordering_execution_class(ordering_class: str) -> str:
    if ordering_class == "ORDERING_M1_CHRONOLOGICAL_COLLAPSE":
        return "ORDERING_M1_CHRONOLOGY_COMPUTABLE_NOW"
    if ordering_class == "ORDERING_NO_COLLAPSE_REQUIRED":
        return "ORDERING_ALREADY_COLLAPSED_OR_NOT_REQUIRED"
    if ordering_class == "ORDERING_M1_FILL_BAR_STRESS_INTERVAL":
        return "ORDERING_M1_FILL_BAR_INTERVAL_BOUND"
    if ordering_class == "ORDERING_M15_ONLY_INTERVAL_ROUTE":
        return "ORDERING_M15_INTERVAL_BOUND"
    if ordering_class == "ORDERING_RECOVERED_PROXY_NO_M1_KEY":
        return "ORDERING_RECOVERED_PROXY_REQUIRES_KEY_REPAIR"
    if ordering_class == "ORDERING_TARGETSTOP_NA_BINDING_PRESERVE":
        return "ORDERING_BINDING_ONLY_NO_SCALAR"
    return "ORDERING_REVIEW_REQUIRED"


def branch_execution_class(branch: dict[str, Any], source_class: str, ordering_class: str, positive_status: str) -> str:
    if "TARGETSTOP_NA" in source_class or "BINDING" in ordering_class:
        return "BINDING_ONLY_NO_SCALAR_EXECUTION"
    if source_class == "SOURCE_UNAVAILABLE_ACQUIRE_OR_STRESS":
        return "SOURCE_STRESS_INTERVAL_EXECUTION_FIRST"
    if ordering_class == "ORDERING_M15_ONLY_INTERVAL_ROUTE":
        return "M15_INTERVAL_EXECUTION_FIRST"
    if ordering_class == "ORDERING_M1_FILL_BAR_STRESS_INTERVAL":
        return "M1_FILL_BAR_INTERVAL_EXECUTION_FIRST"
    if ordering_class == "ORDERING_RECOVERED_PROXY_NO_M1_KEY":
        return "RECOVERED_PROXY_KEY_REPAIR_EXECUTION_FIRST"
    if positive_status in {
        "REPLAYABLE_WITH_EXACT_REPAIR",
        "REPLAYABLE_WITH_EXACT_REPAIR_AND_M1_FILL_BAR_INTERVAL",
        "REPLAYABLE_WITH_M1_SPREAD_ADJUSTED_PROXY",
    }:
        return "POSITIVE_CHALLENGER_REPLAY_EXECUTION_READY"
    if str(branch.get("branch_priority")) == "ENTRY_REDESIGN_REPLAY_FIRST":
        return "ENTRY_REDESIGN_REPLAY_EXECUTION_READY"
    return "SCALAR_OR_POINT_PROXY_EXECUTION_READY"


def work_unit_status(surface_row: dict[str, Any]) -> tuple[str, str]:
    readiness = str(surface_row.get("replay_readiness_class"))
    if readiness == "CURRENT_REPLAY_OR_PROXY_READY":
        return ("RUNNABLE_CURRENT_PROXY_OR_REPAIR", "Current proxy/exact rows are available for this research work unit.")
    if readiness == "SOURCE_ACQUISITION_OR_STRESS_REQUIRED":
        return ("RUN_SOURCE_STRESS_OR_ACQUISITION_FIRST", "Exact source is unavailable; use stress interval and source-acquisition ledger.")
    if readiness == "M15_INTERVAL_NON_EXACT_REPLAY_REQUIRED":
        return ("RUN_M15_INTERVAL_REPLAY_FIRST", "M15 interval path is preserved but exact intra-bar order is unavailable.")
    if readiness == "M1_FILL_BAR_INTERVAL_REPLAY_REQUIRED":
        return ("RUN_M1_FILL_BAR_INTERVAL_REPLAY_FIRST", "M1 fill-bar target/stop ordering remains interval-bounded.")
    if readiness == "SIGNATURE_BINDING_ONLY":
        return ("BINDING_ONLY_NO_REPLAY", "Target/stop NA provenance is preserved as binding scope only.")
    if readiness == "NOT_SCOPE_CONTROL_ROW":
        return ("CONTROL_SCOPE_NO_REPLAY", "This row documents a non-scope/control family.")
    return ("REVIEW_AND_ROUTE", "No automatic execution class matched the current readiness fields.")


def primary_surface(branch_surfaces: list[dict[str, Any]], branch_priority: str) -> str | None:
    if not branch_surfaces:
        return None
    desired = {
        "SOURCE_ACQUISITION_OR_STRESS_FIRST": "SOURCE",
        "ORDERING_COLLAPSE_OR_INTERVAL_FIRST": "ORDERING",
        "POSITIVE_CHALLENGER_REPLAY_FIRST": "POSITIVE",
        "ENTRY_REDESIGN_REPLAY_FIRST": "ENTRY",
    }.get(branch_priority)
    ordered = sorted(
        branch_surfaces,
        key=lambda row: (
            0 if row.get("action_family") == desired else 1,
            ACTION_PRIORITY.get(str(row.get("action_family")), 99),
            str(row.get("proposed_branch_local_code_surface")),
        ),
    )
    return ordered[0].get("proposed_branch_local_code_surface")


def update_manifest(result: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    artifact_paths = [
        RESULT_PATH,
        BRANCH_EXECUTION_PATH,
        WORK_UNIT_PATH,
        SOURCE_ORDERING_EXECUTION_PATH,
        POSITIVE_EXECUTION_PATH,
        BLOCKER_REPAIR_PATH,
        BUCKET_PATH,
        QUESTION_PATH,
        SOURCE_MANIFEST_PATH,
        SUMMARY_PATH,
        Path(__file__).resolve(),
    ]
    records = [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "category": "historical_ohlc_gtos_replay_branch_replay_execution",
        }
        for path in artifact_paths
    ]
    manifest["historical_ohlc_branch_replay_execution_packet_2026_05_16"] = {
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
        "event_type": "branch_replay_execution_packet_built",
        "artifact": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_summary(result: dict[str, Any]) -> None:
    lines = ["# Branch Replay Execution Packet", "", f"Generated UTC: `{result['generated_utc']}`", "", "## Boundary", "", CLAIM_BOUNDARY, "", "## Counts", ""]
    for key, value in result["counts"].items():
        lines.append(f"- {key}: {value}")
    for category in ["branch_execution_class", "source_execution_class", "ordering_execution_class", "work_unit_execution_status", "blocker_repair_class"]:
        lines.extend(["", f"## {category}", ""])
        for bucket, count in result["bucket_distributions"].get(category, {}).items():
            lines.append(f"- {bucket}: {count}")
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    generated_at = now_utc()
    source_rows, manifest_hash = source_manifest_rows()
    code_result = read_json(CODE_REPLAY_RESULT_PATH)
    branches = rows(CODE_REPLAY_BRANCH_PATH)
    surfaces = rows(CODE_SURFACE_RESOLUTION_PATH)
    positive_specs = rows(POSITIVE_REPLAY_SPEC_PATH)
    source_ordering_rows = rows(SOURCE_ORDERING_QUEUE_PATH)
    inventory_rows = rows(SURFACE_INVENTORY_PATH)
    source_deep = by_branch(rows(SOURCE_DEEP_BRANCH_PATH))
    ordering_deep = by_branch(rows(ORDERING_DEEP_BRANCH_PATH))
    source_ordering_by_branch = by_branch(source_ordering_rows)
    surfaces_by_branch = many_by_branch(surfaces)
    positive_by_branch = by_branch(positive_specs)
    source_unavailable_ids = {str(row.get("branch_queue_id")) for row in rows(SOURCE_UNAVAILABLE_PATH)}
    source_proxy_ids = {str(row.get("branch_queue_id")) for row in rows(SOURCE_PROXY_STRESS_PATH)}
    zero_to_spread_ids = {str(row.get("branch_queue_id")) for row in rows(ZERO_TO_SPREAD_PATH)}
    exact_repair_ids = {str(row.get("branch_queue_id")) for row in rows(EXACT_REPAIR_PATH)}
    m1_chrono_ids = {str(row.get("branch_queue_id")) for row in rows(M1_CHRONO_PATH)}
    m1_fill_ids = {str(row.get("branch_queue_id")) for row in rows(M1_FILL_PATH)}
    m15_only_ids = {str(row.get("branch_queue_id")) for row in rows(M15_ONLY_PATH)}
    recovered_no_m1_ids = {str(row.get("branch_queue_id")) for row in rows(RECOVERED_NO_M1_PATH)}
    targetstop_binding_ids = {str(row.get("branch_queue_id")) for row in rows(TARGETSTOP_BINDING_PATH)}

    bucket_counters: dict[str, Counter[str]] = defaultdict(Counter)
    branch_execution_rows: list[dict[str, Any]] = []
    work_unit_rows: list[dict[str, Any]] = []
    source_ordering_execution_rows: list[dict[str, Any]] = []
    positive_execution_rows: list[dict[str, Any]] = []
    blocker_repair_rows: list[dict[str, Any]] = []

    for index, branch in enumerate(branches, 1):
        branch_id = str(branch.get("branch_queue_id"))
        source_ordering = source_ordering_by_branch.get(branch_id, {})
        source_row = source_deep.get(branch_id, {})
        ordering_row = ordering_deep.get(branch_id, {})
        positive = positive_by_branch.get(branch_id, {})
        source_class = str(source_ordering.get("source_deep_action_class") or branch.get("source_deep_action_class"))
        ordering_class = str(source_ordering.get("ordering_deep_action_class") or branch.get("ordering_deep_action_class"))
        positive_status = str(branch.get("positive_replay_status"))
        source_exec = source_execution_class(source_class)
        ordering_exec = ordering_execution_class(ordering_class)
        branch_exec = branch_execution_class(branch, source_class, ordering_class, positive_status)
        sealed_class = point_or_interval(branch)
        branch_surfaces = surfaces_by_branch.get(branch_id, [])
        owner_surface = primary_surface(branch_surfaces, str(branch.get("branch_priority")))
        blocker_class = "NO_BLOCKER_CURRENT_PROXY_OR_CONTROL"
        if branch_id in source_unavailable_ids:
            blocker_class = "SOURCE_EXACT_UNAVAILABLE_ACQUIRE_OR_STRESS"
        elif branch_id in m15_only_ids:
            blocker_class = "ORDERING_M15_INTERVAL_BOUND"
        elif branch_id in m1_fill_ids:
            blocker_class = "ORDERING_M1_FILL_BAR_INTERVAL_BOUND"
        elif branch_id in recovered_no_m1_ids:
            blocker_class = "RECOVERED_PROXY_M1_KEY_REPAIR_REQUIRED"
        elif branch_id in targetstop_binding_ids:
            blocker_class = "TARGETSTOP_NA_BINDING_ONLY"

        branch_execution_rows.append(
            {
                "branch_replay_execution_id": f"OHLC-GTOS-REPLAY-EXEC-BRANCH-{index:05d}",
                **{key: branch.get(key) for key in ["branch_queue_id", "route_candidate_id", "symbol", "route_session", "side", "entry_variant", "target_stop_contract_id", "target_multiple", "stop_multiple"]},
                "branch_result_class": branch.get("branch_result_class"),
                "branch_execution_class": branch_exec,
                "sealed_proxy_class": sealed_class,
                "expectancy_style_proxy_method": branch.get("expectancy_style_proxy_method"),
                "rstyle_lower_mean": branch.get("rstyle_lower_mean"),
                "rstyle_midpoint_mean": branch.get("rstyle_midpoint_mean"),
                "rstyle_upper_mean": branch.get("rstyle_upper_mean"),
                "target_stop_result": branch.get("target_stop_result"),
                "pass_control_delta_status": branch.get("pass_control_delta_status"),
                "cost_sensitivity_proxy_status": branch.get("cost_sensitivity_proxy_status"),
                "effective_n_concentration_class": branch.get("effective_n_concentration_class"),
                "same_route_peer_delta": branch.get("same_route_peer_delta"),
                "source_confidence_status": branch.get("source_confidence_status"),
                "ambiguity_status": branch.get("ambiguity_status"),
                "source_execution_class": source_exec,
                "ordering_execution_class": ordering_exec,
                "positive_replay_status": positive_status,
                "positive_replayable_now": branch.get("positive_replayable_now"),
                "blocker_repair_class": blocker_class,
                "branch_priority": branch.get("branch_priority"),
                "branch_local_next_computations": branch.get("branch_local_next_computations"),
                "primary_branch_local_surface": owner_surface,
                "exact_failure_cause": branch.get("exact_failure_cause"),
                "exact_success_cause": branch.get("exact_success_cause"),
                "exact_missing_geometry_or_source_reason": branch.get("exact_missing_geometry_or_source_reason"),
                "same_resource_execution_implication": branch_exec,
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        source_ordering_execution_rows.append(
            {
                "source_ordering_execution_id": f"OHLC-GTOS-REPLAY-EXEC-SRCORD-{index:05d}",
                **{key: branch.get(key) for key in ["branch_queue_id", "route_candidate_id", "symbol", "route_session", "side", "entry_variant", "target_stop_contract_id", "target_multiple", "stop_multiple"]},
                "source_execution_class": source_exec,
                "source_deep_action_class": source_class,
                "source_support_rows": source_ordering.get("source_support_rows"),
                "source_deep_output_route": source_row.get("source_deep_output_route"),
                "source_repair_route_class": source_row.get("source_repair_route_class"),
                "ordering_execution_class": ordering_exec,
                "ordering_deep_action_class": ordering_class,
                "ordering_support_rows": source_ordering.get("ordering_support_rows"),
                "ordering_deep_output_route": ordering_row.get("ordering_deep_output_route"),
                "interval_preservation_class": ordering_row.get("interval_preservation_class"),
                "interval_rstyle_lower_mean": ordering_row.get("interval_rstyle_lower_mean"),
                "interval_rstyle_midpoint_mean": ordering_row.get("interval_rstyle_midpoint_mean"),
                "interval_rstyle_upper_mean": ordering_row.get("interval_rstyle_upper_mean"),
                "membership_flags": {
                    "source_unavailable": branch_id in source_unavailable_ids,
                    "source_proxy_stress": branch_id in source_proxy_ids,
                    "zero_to_spread": branch_id in zero_to_spread_ids,
                    "exact_repair": branch_id in exact_repair_ids,
                    "m1_chronological": branch_id in m1_chrono_ids,
                    "m1_fill_bar_interval": branch_id in m1_fill_ids,
                    "m15_only_interval": branch_id in m15_only_ids,
                    "recovered_no_m1_key": branch_id in recovered_no_m1_ids,
                    "targetstop_binding": branch_id in targetstop_binding_ids,
                },
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        blocker_repair_rows.append(
            {
                "blocker_repair_id": f"OHLC-GTOS-REPLAY-EXEC-BLOCKER-{index:05d}",
                **{key: branch.get(key) for key in ["branch_queue_id", "route_candidate_id", "symbol", "route_session", "side", "entry_variant", "target_stop_contract_id", "target_multiple", "stop_multiple"]},
                "blocker_repair_class": blocker_class,
                "repair_or_proxy_route": {
                    "source": source_row.get("source_deep_output_route"),
                    "ordering": ordering_row.get("ordering_deep_output_route"),
                    "primary_surface": owner_surface,
                },
                "exact_missing_geometry_or_source_reason": branch.get("exact_missing_geometry_or_source_reason"),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        bucket_counters["branch_execution_class"][branch_exec] += 1
        bucket_counters["sealed_proxy_class"][sealed_class] += 1
        bucket_counters["source_execution_class"][source_exec] += 1
        bucket_counters["ordering_execution_class"][ordering_exec] += 1
        bucket_counters["blocker_repair_class"][blocker_class] += 1
        bucket_counters["primary_surface"][str(owner_surface)] += 1

    for index, surface in enumerate(surfaces, 1):
        status, note = work_unit_status(surface)
        branch_id = str(surface.get("branch_queue_id"))
        work_unit_rows.append(
            {
                "replay_execution_work_unit_id": f"OHLC-GTOS-REPLAY-EXEC-WORK-{index:05d}",
                **{key: surface.get(key) for key in ["branch_queue_id", "route_candidate_id", "symbol", "route_session", "side", "entry_variant", "target_stop_contract_id", "target_multiple", "stop_multiple"]},
                "action_family": surface.get("action_family"),
                "proposed_branch_local_code_surface": surface.get("proposed_branch_local_code_surface"),
                "surface_file_status": surface.get("surface_file_status"),
                "surface_mode": surface.get("surface_mode"),
                "replay_readiness_class": surface.get("replay_readiness_class"),
                "work_unit_execution_status": status,
                "work_unit_execution_note": note,
                "next_same_resource_computation": surface.get("next_same_resource_computation"),
                "branch_execution_class": branch_execution_rows[[row.get("branch_queue_id") for row in branch_execution_rows].index(branch_id)]["branch_execution_class"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        bucket_counters["work_unit_execution_status"][status] += 1
        bucket_counters["work_unit_action_family"][str(surface.get("action_family"))] += 1

    for index, positive in enumerate(positive_specs, 1):
        branch_id = str(positive.get("branch_queue_id"))
        positive_execution_class = "POSITIVE_STRESS_OR_SOURCE_REPAIR_FIRST"
        if positive.get("positive_replayable_now") is True:
            positive_execution_class = "POSITIVE_REPLAYABLE_NOW"
        positive_execution_rows.append(
            {
                "positive_replay_execution_id": f"OHLC-GTOS-REPLAY-EXEC-POSITIVE-{index:05d}",
                **{key: positive.get(key) for key in ["branch_queue_id", "route_candidate_id", "symbol", "route_session", "side", "entry_variant", "target_stop_contract_id", "target_multiple", "stop_multiple"]},
                "positive_execution_class": positive_execution_class,
                "positive_replay_status": positive.get("positive_replay_status"),
                "positive_deep_action_class": positive.get("positive_deep_action_class"),
                "positive_replay_note": positive.get("positive_replay_note"),
                "positive_replayable_now": positive.get("positive_replayable_now"),
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
                "proposed_branch_local_code_surface": positive.get("proposed_branch_local_code_surface"),
                "branch_execution_class": next((row["branch_execution_class"] for row in branch_execution_rows if row.get("branch_queue_id") == branch_id), None),
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
            }
        )
        bucket_counters["positive_execution_class"][positive_execution_class] += 1
        bucket_counters["positive_replay_status"][str(positive.get("positive_replay_status"))] += 1

    bucket_rows = []
    for category, counter in sorted(bucket_counters.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_id": f"OHLC-GTOS-REPLAY-EXEC-BUCKET-{len(bucket_rows) + 1:05d}",
                    "bucket_category": category,
                    "bucket": str(bucket),
                    "branch_or_work_unit_count": int(count),
                    "share": round(count / total, 9) if total else None,
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                    "generated_utc": generated_at,
                }
            )

    question_rows = [
        {"question_id": "OHLC-GTOS-REPLAY-EXEC-QUESTION-001", "question": "Which branches are scalar/proxy executable now versus interval/source bounded?", "answer_route": "Use branch and source/ordering execution ledgers."},
        {"question_id": "OHLC-GTOS-REPLAY-EXEC-QUESTION-002", "question": "Which proposed branch-local surfaces should be created first for full denominator replay?", "answer_route": "Use work-unit and primary-surface bucket ledgers."},
        {"question_id": "OHLC-GTOS-REPLAY-EXEC-QUESTION-003", "question": "Which positive challenger branches are replayable now and which remain stress-only?", "answer_route": "Use positive challenger execution ledger."},
    ]
    for row in question_rows:
        row.update({"safe_flags": SAFE_FLAGS, "claim_boundary": CLAIM_BOUNDARY, "generated_utc": generated_at, "not_completion": True})

    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_REPLAY_EXECUTION_PACKET",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_branch_code_replay_rows": len(branches),
            "input_code_surface_resolution_rows": len(surfaces),
            "input_positive_replay_spec_rows": len(positive_specs),
            "input_source_ordering_queue_rows": len(source_ordering_rows),
            "input_surface_inventory_rows": len(inventory_rows),
            "branch_replay_execution_rows": len(branch_execution_rows),
            "replay_execution_work_unit_rows": len(work_unit_rows),
            "source_ordering_execution_rows": len(source_ordering_execution_rows),
            "positive_replay_execution_rows": len(positive_execution_rows),
            "blocker_repair_rows": len(blocker_repair_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_rows),
        },
        "upstream_counts": code_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_counters.items())},
        "source_manifest_hash": manifest_hash,
    }

    for path, output_rows in [
        (BRANCH_EXECUTION_PATH, branch_execution_rows),
        (WORK_UNIT_PATH, work_unit_rows),
        (SOURCE_ORDERING_EXECUTION_PATH, source_ordering_execution_rows),
        (POSITIVE_EXECUTION_PATH, positive_execution_rows),
        (BLOCKER_REPAIR_PATH, blocker_repair_rows),
        (BUCKET_PATH, bucket_rows),
        (QUESTION_PATH, question_rows),
        (SOURCE_MANIFEST_PATH, source_rows),
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
