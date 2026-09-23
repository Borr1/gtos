#!/usr/bin/env python3
"""Build ENTRY_ADVERSE accepted redesign detail rows from branch-local ledgers."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

ACCEPTED_BUILDER_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_RESULT_2026-05-16.json"
ACCEPTED_BUILDER_ENTRY_ADVERSE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_ENTRY_ADVERSE_RESULT_LEDGER_2026-05-16.jsonl"
NEXT_LAYER_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_RESULT_2026-05-16.json"
NEXT_LAYER_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
NEXT_LAYER_ENTRY_ADVERSE = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl"
ENTRY_ADVERSE_PROXY_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_PROXY_REDESIGN_RESULT_2026-05-16.json"
UNIFIED_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_UNIFIED_BRANCH_LOCAL_IMPLEMENTATION_LEDGER_2026-05-16.jsonl"
ENTRY_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_GEOMETRY_BRANCH_REDESIGN_LEDGER_2026-05-16.jsonl"
ENTRY_VARIANT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_GEOMETRY_VARIANT_EXPLODED_LEDGER_2026-05-16.jsonl"
ADVERSE_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ADVERSE_STOP_FIRST_BRANCH_REDESIGN_LEDGER_2026-05-16.jsonl"
ADVERSE_ACTION = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ADVERSE_STOP_FIRST_ACTION_EXPLODED_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_REDESIGN_DETAIL"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_LEDGER_2026-05-16.jsonl"
BRANCH_DETAIL_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_DETAIL_LEDGER_2026-05-16.jsonl"
ENTRY_VARIANT_DETAIL_LEDGER = ROUTE_DIR / f"{PREFIX}_ENTRY_VARIANT_DETAIL_LEDGER_2026-05-16.jsonl"
ADVERSE_VARIANT_DETAIL_LEDGER = ROUTE_DIR / f"{PREFIX}_ADVERSE_VARIANT_DETAIL_LEDGER_2026-05-16.jsonl"
COMBINED_VARIANT_LEDGER = ROUTE_DIR / f"{PREFIX}_COMBINED_VARIANT_LEDGER_2026-05-16.jsonl"
REJECTED_REPAIR_LEDGER = ROUTE_DIR / f"{PREFIX}_REJECTED_REPAIR_LEDGER_2026-05-16.jsonl"
SIDECAR_CONTEXT_LEDGER = ROUTE_DIR / f"{PREFIX}_SIDECAR_CONTEXT_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-16.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "ENTRY_ADVERSE redesign detail packet only. It consumes branch-local accepted-builder "
    "and redesign ledgers, preserves the full ENTRY_ADVERSE denominator, computes accepted "
    "entry/adverse variant detail rows and combined branch-local redesign variants, and keeps "
    "rejected/context rows explicit. It does not change live behavior and does not claim broker "
    "R/PnL, realized expectancy, win-rate, validation, live-readiness, or promotion."
)

ACCEPTED_STATUS = "ENTRY_AND_ADVERSE_REDESIGN_ACCEPTED"
REJECTED_STATUS = "ENTRY_ADVERSE_REJECTED_NONPOSITIVE"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(paths, 1):
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-ENTRY-ADVERSE-DETAIL-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": sha256_file(path),
                "status": "HASHED" if path.exists() else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def with_common(row: dict[str, Any], generated_at: str, manifest_hash: str) -> dict[str, Any]:
    row.update(
        {
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
            "not_completion": True,
            "generated_utc": generated_at,
            "source_manifest_hash": manifest_hash,
        }
    )
    return row


def by_branch(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["branch_queue_id"]: row for row in rows if row.get("branch_queue_id")}


def group_by_branch(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("branch_queue_id"):
            grouped[row["branch_queue_id"]].append(row)
    return grouped


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stat_triplet(values: list[float], prefix: str) -> dict[str, float | None]:
    if not values:
        return {f"{prefix}_min": None, f"{prefix}_mean": None, f"{prefix}_max": None}
    return {
        f"{prefix}_min": round(min(values), 6),
        f"{prefix}_mean": round(mean(values), 6),
        f"{prefix}_max": round(max(values), 6),
    }


def scope_class(status: str) -> str:
    if status == ACCEPTED_STATUS:
        return "ACCEPTED_PRIMARY_ENTRY_ADVERSE_EXECUTION_SCOPE"
    if status == REJECTED_STATUS:
        return "ENTRY_ADVERSE_REJECTED_NONPOSITIVE_SCOPE"
    if status == "ENTRY_ADVERSE_SIDE_CAR_REDESIGN_CONTEXT":
        return "ENTRY_ADVERSE_SIDECAR_REDESIGN_CONTEXT_SCOPE"
    return "ENTRY_ADVERSE_PRESERVE_CONTEXT_SCOPE"


def carry_identity(source: dict[str, Any], unified: dict[str, Any] | None = None) -> dict[str, Any]:
    unified = unified or {}
    route_session = source.get("route_session") or unified.get("route_session")
    if not route_session and source.get("route_candidate_id"):
        route_session = str(source.get("route_candidate_id")).split("|")[1]
    return {
        "branch_queue_id": source.get("branch_queue_id"),
        "matrix_branch_id": source.get("matrix_branch_id") or unified.get("matrix_branch_id"),
        "route_candidate_id": source.get("route_candidate_id") or unified.get("route_candidate_id"),
        "route_session": route_session,
        "symbol": source.get("symbol") or unified.get("symbol"),
        "side": source.get("side") or unified.get("side"),
        "entry_variant": source.get("entry_variant") or unified.get("entry_variant"),
        "target_stop_contract_id": source.get("target_stop_contract_id") or unified.get("target_stop_contract_id"),
        "target_multiple": source.get("target_multiple") or unified.get("target_multiple"),
        "stop_multiple": source.get("stop_multiple") or unified.get("stop_multiple"),
    }


def main() -> int:
    generated_at = now_utc()
    accepted_builder_result = read_json(ACCEPTED_BUILDER_RESULT)
    next_layer_result = read_json(NEXT_LAYER_RESULT)
    proxy_result = read_json(ENTRY_ADVERSE_PROXY_RESULT)
    accepted_builder_rows = read_jsonl(ACCEPTED_BUILDER_ENTRY_ADVERSE)
    next_branch_rows = read_jsonl(NEXT_LAYER_BRANCH)
    next_entry_adverse_rows = read_jsonl(NEXT_LAYER_ENTRY_ADVERSE)
    unified_rows = read_jsonl(UNIFIED_BRANCH)
    entry_branch_rows_input = read_jsonl(ENTRY_BRANCH)
    entry_variant_rows_input = read_jsonl(ENTRY_VARIANT)
    adverse_branch_rows_input = read_jsonl(ADVERSE_BRANCH)
    adverse_action_rows_input = read_jsonl(ADVERSE_ACTION)

    next_branch_by_id = by_branch(next_branch_rows)
    next_ea_by_id = by_branch(next_entry_adverse_rows)
    unified_by_id = by_branch(unified_rows)
    entry_branch_by_id = by_branch(entry_branch_rows_input)
    adverse_branch_by_id = by_branch(adverse_branch_rows_input)
    entry_variants_by_id = group_by_branch(entry_variant_rows_input)
    adverse_actions_by_id = group_by_branch(adverse_action_rows_input)

    source_manifest, manifest_hash = source_manifest_rows(
        [
            ACCEPTED_BUILDER_RESULT,
            ACCEPTED_BUILDER_ENTRY_ADVERSE,
            NEXT_LAYER_RESULT,
            NEXT_LAYER_BRANCH,
            NEXT_LAYER_ENTRY_ADVERSE,
            ENTRY_ADVERSE_PROXY_RESULT,
            UNIFIED_BRANCH,
            ENTRY_BRANCH,
            ENTRY_VARIANT,
            ADVERSE_BRANCH,
            ADVERSE_ACTION,
        ],
        generated_at,
    )

    scope_rows: list[dict[str, Any]] = []
    branch_detail_rows: list[dict[str, Any]] = []
    entry_variant_detail_rows: list[dict[str, Any]] = []
    adverse_variant_detail_rows: list[dict[str, Any]] = []
    combined_variant_rows: list[dict[str, Any]] = []
    rejected_repair_rows: list[dict[str, Any]] = []
    sidecar_context_rows: list[dict[str, Any]] = []

    for row in accepted_builder_rows:
        branch_id = row.get("branch_queue_id")
        status = str(row.get("entry_adverse_builder_result_status"))
        unified = unified_by_id.get(branch_id, {})
        next_branch = next_branch_by_id.get(branch_id, {})
        next_ea = next_ea_by_id.get(branch_id, {})
        entry_branch = entry_branch_by_id.get(branch_id, {})
        adverse_branch = adverse_branch_by_id.get(branch_id, {})
        identity = carry_identity(row, unified)
        accepted = status == ACCEPTED_STATUS
        rejected = status == REJECTED_STATUS
        scope = with_common(
            {
                "entry_adverse_scope_id": f"OHLC-GTOS-ENTRY-ADVERSE-DETAIL-SCOPE-{len(scope_rows) + 1:05d}",
                **identity,
                "primary_export_family": "ENTRY_ADVERSE",
                "scope_class": scope_class(status),
                "accepted_for_next_executable_builder": accepted,
                "entry_adverse_builder_result_status": status,
                "entry_adverse_builder_score": row.get("entry_adverse_builder_score"),
                "entry_adverse_builder_score_class": row.get("entry_adverse_builder_score_class"),
                "entry_adverse_action_scope": row.get("entry_adverse_action_scope"),
                "entry_adverse_builder_next_action": row.get("entry_adverse_builder_next_action"),
                "integrated_evidence_action": next_branch.get("integrated_evidence_action"),
                "integrated_evidence_state": next_branch.get("integrated_evidence_state"),
                "source_deep_action_class": next_ea.get("source_deep_action_class") or unified.get("source_stress_action_class"),
                "ordering_deep_action_class": next_ea.get("ordering_deep_action_class") or unified.get("ordering_collapse_action_class"),
                "positive_deep_action_class": next_ea.get("positive_deep_action_class") or unified.get("positive_challenger_class"),
                "target_stop_result": unified.get("target_stop_result"),
                "entry_geometry_retest_class": entry_branch.get("entry_geometry_retest_class") or unified.get("entry_geometry_retest_class"),
                "adverse_stop_first_class": adverse_branch.get("adverse_stop_first_class") or unified.get("adverse_stop_first_class"),
                "m15_exact_chronology_claim": False,
                "m1_exact_chronology_claim": False,
                "m1_tick_ordering_exact": False,
            },
            generated_at,
            manifest_hash,
        )
        scope_rows.append(scope)

        if accepted:
            detail = with_common(
                {
                    "entry_adverse_detail_branch_id": f"OHLC-GTOS-ENTRY-ADVERSE-DETAIL-BRANCH-{len(branch_detail_rows) + 1:05d}",
                    **identity,
                    "primary_export_family": "ENTRY_ADVERSE",
                    "accepted_for_next_executable_builder": True,
                    "entry_adverse_builder_result_status": status,
                    "entry_adverse_builder_score": row.get("entry_adverse_builder_score"),
                    "redesign_pressure_score": row.get("redesign_pressure_score"),
                    "stop_first_rate": row.get("stop_first_rate"),
                    "target_first_rate": row.get("target_first_rate"),
                    "fillability_rate": row.get("fillability_rate"),
                    "no_fill_or_unfilled_rate": row.get("no_fill_or_unfilled_rate"),
                    "entry_target_stop_balance_class": row.get("entry_target_stop_balance_class"),
                    "target_stop_result": unified.get("target_stop_result"),
                    "target_stop_reward_to_risk_ratio": unified.get("target_stop_reward_to_risk_ratio"),
                    "branch_result_class": unified.get("branch_result_class"),
                    "rstyle_lower_mean": unified.get("rstyle_lower_mean"),
                    "rstyle_midpoint_mean": unified.get("rstyle_midpoint_mean"),
                    "rstyle_upper_mean": unified.get("rstyle_upper_mean"),
                    "rstyle_interval_rows": unified.get("rstyle_interval_rows"),
                    "stop_first_rows": unified.get("stop_first_rows"),
                    "target_first_rows": unified.get("target_first_rows"),
                    "no_fill_or_unfilled_rows": unified.get("no_fill_or_unfilled_rows"),
                    "entry_geometry_retest_class": unified.get("entry_geometry_retest_class"),
                    "entry_redesign_action_class": unified.get("entry_redesign_action_class"),
                    "adverse_stop_first_class": unified.get("adverse_stop_first_class"),
                    "adverse_redesign_action_class": unified.get("adverse_redesign_action_class"),
                    "entry_proxy_variants": unified.get("entry_proxy_variants"),
                    "adverse_action_variants": unified.get("adverse_action_variants"),
                    "source_deep_action_class": next_ea.get("source_deep_action_class"),
                    "ordering_deep_action_class": next_ea.get("ordering_deep_action_class"),
                    "positive_deep_action_class": next_ea.get("positive_deep_action_class"),
                    "source_stress_action_class": unified.get("source_stress_action_class"),
                    "source_repairability_class": unified.get("source_repairability_class"),
                    "exact_spread_repairability_class": unified.get("exact_spread_repairability_class"),
                    "repair_feasibility_class": unified.get("repair_feasibility_class"),
                    "pass_control_delta_status": unified.get("pass_control_delta_status"),
                    "effective_n_concentration_class": unified.get("effective_n_concentration_class"),
                    "exact_success_cause": unified.get("exact_success_cause"),
                    "exact_failure_cause": unified.get("exact_failure_cause"),
                    "exact_missing_geometry_or_source_reason": (
                        "Accepted ENTRY_ADVERSE detail uses branch-local proxy redesign ledgers; exact broker fill, "
                        "slippage, ticket lifecycle, realized account PnL, and live execution state are absent."
                    ),
                    "next_same_resource_action": "BUILD_ENTRY_AND_ADVERSE_VARIANT_GRID_AND_SOURCE_SPLIT",
                    "m15_exact_chronology_claim": False,
                    "m1_exact_chronology_claim": False,
                    "m1_tick_ordering_exact": False,
                },
                generated_at,
                manifest_hash,
            )
            branch_detail_rows.append(detail)

            for variant in entry_variants_by_id.get(branch_id, []):
                entry_variant_detail_rows.append(
                    with_common(
                        {
                            "entry_adverse_entry_variant_detail_id": f"OHLC-GTOS-ENTRY-ADVERSE-DETAIL-ENTRY-VAR-{len(entry_variant_detail_rows) + 1:05d}",
                            **identity,
                            "entry_geometry_variant_id": variant.get("entry_geometry_variant_id"),
                            "entry_variant_action": variant.get("entry_variant_action"),
                            "entry_geometry_retest_class": variant.get("entry_geometry_retest_class"),
                            "entry_redesign_action_class": variant.get("entry_redesign_action_class"),
                            "source_requirement_status": variant.get("source_requirement_status"),
                            "entry_next_same_resource_actions": variant.get("entry_next_same_resource_actions"),
                            "source_deep_action_class": next_ea.get("source_deep_action_class"),
                            "fillability_rate": row.get("fillability_rate"),
                            "target_stop_reward_to_risk_ratio": variant.get("target_stop_reward_to_risk_ratio"),
                            "variant_scope": "ACCEPTED_ENTRY_VARIANT_DETAIL",
                        },
                        generated_at,
                        manifest_hash,
                    )
                )
            for variant in adverse_actions_by_id.get(branch_id, []):
                adverse_variant_detail_rows.append(
                    with_common(
                        {
                            "entry_adverse_adverse_variant_detail_id": f"OHLC-GTOS-ENTRY-ADVERSE-DETAIL-ADV-VAR-{len(adverse_variant_detail_rows) + 1:05d}",
                            **identity,
                            "adverse_stop_first_action_id": variant.get("adverse_stop_first_action_id"),
                            "adverse_action_variant": variant.get("adverse_action_variant"),
                            "adverse_stop_first_class": variant.get("adverse_stop_first_class"),
                            "adverse_redesign_action_class": variant.get("adverse_redesign_action_class"),
                            "adverse_next_same_resource_actions": variant.get("adverse_next_same_resource_actions"),
                            "exact_failure_cause": variant.get("exact_failure_cause"),
                            "stop_first_rate": row.get("stop_first_rate"),
                            "target_stop_reward_to_risk_ratio": variant.get("target_stop_reward_to_risk_ratio"),
                            "variant_scope": "ACCEPTED_ADVERSE_VARIANT_DETAIL",
                        },
                        generated_at,
                        manifest_hash,
                    )
                )
            for entry_variant in entry_variants_by_id.get(branch_id, []):
                for adverse_variant in adverse_actions_by_id.get(branch_id, []):
                    combined_variant_rows.append(
                        with_common(
                            {
                                "entry_adverse_combined_variant_id": f"OHLC-GTOS-ENTRY-ADVERSE-DETAIL-COMBINED-{len(combined_variant_rows) + 1:05d}",
                                **identity,
                                "entry_geometry_variant_id": entry_variant.get("entry_geometry_variant_id"),
                                "adverse_stop_first_action_id": adverse_variant.get("adverse_stop_first_action_id"),
                                "entry_variant_action": entry_variant.get("entry_variant_action"),
                                "adverse_action_variant": adverse_variant.get("adverse_action_variant"),
                                "combined_variant_pair": f"{entry_variant.get('entry_variant_action')}__{adverse_variant.get('adverse_action_variant')}",
                                "combined_variant_decision": (
                                    "SOURCE_SPLIT_BEFORE_ADVERSE_REDESIGN"
                                    if entry_variant.get("entry_variant_action") == "SOURCE_SPLIT_BRANCH"
                                    else "PRESERVE_DESCRIPTOR_AND_TEST_ADVERSE_REDESIGN"
                                ),
                                "entry_adverse_builder_score": row.get("entry_adverse_builder_score"),
                                "stop_first_rate": row.get("stop_first_rate"),
                                "fillability_rate": row.get("fillability_rate"),
                                "rstyle_midpoint_mean": unified.get("rstyle_midpoint_mean"),
                                "source_deep_action_class": next_ea.get("source_deep_action_class"),
                                "target_stop_result": unified.get("target_stop_result"),
                                "combined_scope": "ACCEPTED_ENTRY_ADVERSE_COMBINED_VARIANT",
                            },
                            generated_at,
                            manifest_hash,
                        )
                    )
        elif rejected:
            rejected_repair_rows.append(
                with_common(
                    {
                        "entry_adverse_rejected_repair_id": f"OHLC-GTOS-ENTRY-ADVERSE-DETAIL-REJECTED-{len(rejected_repair_rows) + 1:05d}",
                        **identity,
                        "primary_export_family": "ENTRY_ADVERSE",
                        "entry_adverse_builder_result_status": status,
                        "entry_adverse_builder_score": row.get("entry_adverse_builder_score"),
                        "redesign_pressure_score": row.get("redesign_pressure_score"),
                        "target_stop_result": unified.get("target_stop_result"),
                        "branch_result_class": unified.get("branch_result_class"),
                        "rstyle_midpoint_mean": unified.get("rstyle_midpoint_mean"),
                        "entry_geometry_retest_class": unified.get("entry_geometry_retest_class"),
                        "adverse_stop_first_class": unified.get("adverse_stop_first_class"),
                        "source_deep_action_class": next_ea.get("source_deep_action_class"),
                        "ordering_deep_action_class": next_ea.get("ordering_deep_action_class"),
                        "positive_deep_action_class": next_ea.get("positive_deep_action_class"),
                        "exact_failure_cause": unified.get("exact_failure_cause"),
                        "next_same_resource_action": "PRESERVE_REJECTED_PRIMARY_ENTRY_ADVERSE_REPAIR_ROW",
                        "m15_exact_chronology_claim": False,
                        "m1_exact_chronology_claim": False,
                        "m1_tick_ordering_exact": False,
                    },
                    generated_at,
                    manifest_hash,
                )
            )
        else:
            sidecar_context_rows.append(
                with_common(
                    {
                        "entry_adverse_sidecar_context_id": f"OHLC-GTOS-ENTRY-ADVERSE-DETAIL-SIDECAR-{len(sidecar_context_rows) + 1:05d}",
                        **identity,
                        "primary_export_family": "ENTRY_ADVERSE",
                        "scope_class": scope_class(status),
                        "entry_adverse_builder_result_status": status,
                        "entry_adverse_builder_score": row.get("entry_adverse_builder_score"),
                        "entry_adverse_action_scope": row.get("entry_adverse_action_scope"),
                        "target_stop_result": unified.get("target_stop_result"),
                        "branch_result_class": unified.get("branch_result_class"),
                        "entry_geometry_retest_class": unified.get("entry_geometry_retest_class"),
                        "adverse_stop_first_class": unified.get("adverse_stop_first_class"),
                        "context_preservation_reason": "SIDE_CAR_OR_PRESERVE_CONTEXT_NOT_ACCEPTED_PRIMARY_ENTRY_ADVERSE_DETAIL",
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    bucket_sources = {
        "scope_class": Counter(row.get("scope_class") for row in scope_rows),
        "entry_adverse_builder_result_status": Counter(row.get("entry_adverse_builder_result_status") for row in scope_rows),
        "entry_adverse_action_scope": Counter(row.get("entry_adverse_action_scope") for row in scope_rows),
        "accepted_symbol": Counter(row.get("symbol") for row in branch_detail_rows),
        "accepted_route_session": Counter(row.get("route_session") for row in branch_detail_rows),
        "accepted_side": Counter(row.get("side") for row in branch_detail_rows),
        "accepted_entry_variant": Counter(row.get("entry_variant") for row in branch_detail_rows),
        "accepted_target_stop_result": Counter(row.get("target_stop_result") for row in branch_detail_rows),
        "accepted_source_deep_action_class": Counter(row.get("source_deep_action_class") for row in branch_detail_rows),
        "accepted_branch_result_class": Counter(row.get("branch_result_class") for row in branch_detail_rows),
        "accepted_entry_geometry_retest_class": Counter(row.get("entry_geometry_retest_class") for row in branch_detail_rows),
        "accepted_adverse_stop_first_class": Counter(row.get("adverse_stop_first_class") for row in branch_detail_rows),
        "accepted_entry_variant_action": Counter(row.get("entry_variant_action") for row in entry_variant_detail_rows),
        "accepted_adverse_action_variant": Counter(row.get("adverse_action_variant") for row in adverse_variant_detail_rows),
        "combined_variant_pair": Counter(row.get("combined_variant_pair") for row in combined_variant_rows),
        "sidecar_scope_class": Counter(row.get("scope_class") for row in sidecar_context_rows),
    }
    bucket_rows: list[dict[str, Any]] = []
    for category, counter in sorted(bucket_sources.items()):
        total = sum(counter.values())
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-ENTRY-ADVERSE-DETAIL-BUCKET-{len(bucket_rows) + 1:05d}",
                        "bucket_category": category,
                        "bucket": str(bucket),
                        "row_count": int(count),
                        "share": round(count / total, 9) if total else None,
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-ENTRY-ADVERSE-DETAIL-QUESTION-001",
            "question": "Which ENTRY_ADVERSE rows are accepted primary executable redesign rows?",
            "answer_route": "Use BRANCH_DETAIL_LEDGER and accepted scope branch IDs.",
        },
        {
            "question_id": "OHLC-GTOS-ENTRY-ADVERSE-DETAIL-QUESTION-002",
            "question": "Which entry and adverse variants are mechanically available for accepted rows?",
            "answer_route": "Use ENTRY_VARIANT_DETAIL, ADVERSE_VARIANT_DETAIL, and COMBINED_VARIANT ledgers.",
        },
        {
            "question_id": "OHLC-GTOS-ENTRY-ADVERSE-DETAIL-QUESTION-003",
            "question": "Is the accepted redesign concentrated by market and session?",
            "answer_route": "Yes: accepted rows are GBPJPY tokyo_kz SHORT; preserve this as concentration and continue transfer testing.",
        },
        {
            "question_id": "OHLC-GTOS-ENTRY-ADVERSE-DETAIL-QUESTION-004",
            "question": "What immediate same-resource work follows?",
            "answer_route": "Join ENTRY_ADVERSE accepted variants to SOURCE/M15/M1/POSITIVE implications and broaden transfer/failure decisions by symbol/session/market.",
        },
    ]
    for row in question_rows:
        with_common(row, generated_at, manifest_hash)

    builder_scores = [value for value in (as_float(row.get("entry_adverse_builder_score")) for row in branch_detail_rows) if value is not None]
    stop_rates = [value for value in (as_float(row.get("stop_first_rate")) for row in branch_detail_rows) if value is not None]
    fill_rates = [value for value in (as_float(row.get("fillability_rate")) for row in branch_detail_rows) if value is not None]
    rstyle_mids = [value for value in (as_float(row.get("rstyle_midpoint_mean")) for row in branch_detail_rows) if value is not None]
    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_REDESIGN_DETAIL",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": {
            "input_accepted_builder_entry_adverse_rows": len(accepted_builder_rows),
            "input_next_layer_branch_rows": len(next_branch_rows),
            "input_next_layer_entry_adverse_rows": len(next_entry_adverse_rows),
            "input_unified_branch_rows": len(unified_rows),
            "input_entry_branch_rows": len(entry_branch_rows_input),
            "input_entry_variant_rows": len(entry_variant_rows_input),
            "input_adverse_branch_rows": len(adverse_branch_rows_input),
            "input_adverse_action_rows": len(adverse_action_rows_input),
            "scope_rows": len(scope_rows),
            "branch_detail_rows": len(branch_detail_rows),
            "entry_variant_detail_rows": len(entry_variant_detail_rows),
            "adverse_variant_detail_rows": len(adverse_variant_detail_rows),
            "combined_variant_rows": len(combined_variant_rows),
            "rejected_repair_rows": len(rejected_repair_rows),
            "sidecar_context_rows": len(sidecar_context_rows),
            "bucket_rows": len(bucket_rows),
            "question_rows": len(question_rows),
            "source_manifest_rows": len(source_manifest),
        },
        "upstream_accepted_builder_counts": accepted_builder_result.get("counts", {}),
        "upstream_next_layer_counts": next_layer_result.get("counts", {}),
        "upstream_entry_adverse_proxy_counts": proxy_result.get("counts", {}),
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_sources.items())},
        "accepted_score_stats": {
            **stat_triplet(builder_scores, "entry_adverse_builder_score"),
            **stat_triplet(stop_rates, "stop_first_rate"),
            **stat_triplet(fill_rates, "fillability_rate"),
            **stat_triplet(rstyle_mids, "rstyle_midpoint_mean"),
        },
        "system_decision": {
            "system_recommendation": (
                "ENTRY_ADVERSE_REDESIGN_DETAIL_RESULT: preserve the five accepted GBPJPY tokyo_kz SHORT "
                "entry/adverse redesign rows as concentrated challenger-detail candidates, preserve the one "
                "rejected primary row, keep all sidecar/context rows out of scalar accepted scope, and continue "
                "market/session transfer plus non-OB primitive broadening."
            ),
            "scope_rows": len(scope_rows),
            "accepted_primary_rows": len(branch_detail_rows),
            "rejected_primary_rows": len(rejected_repair_rows),
            "sidecar_context_rows": len(sidecar_context_rows),
            "entry_variant_detail_rows": len(entry_variant_detail_rows),
            "adverse_variant_detail_rows": len(adverse_variant_detail_rows),
            "combined_variant_rows": len(combined_variant_rows),
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (SCOPE_LEDGER, scope_rows),
        (BRANCH_DETAIL_LEDGER, branch_detail_rows),
        (ENTRY_VARIANT_DETAIL_LEDGER, entry_variant_detail_rows),
        (ADVERSE_VARIANT_DETAIL_LEDGER, adverse_variant_detail_rows),
        (COMBINED_VARIANT_LEDGER, combined_variant_rows),
        (REJECTED_REPAIR_LEDGER, rejected_repair_rows),
        (SIDECAR_CONTEXT_LEDGER, sidecar_context_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]
    for path, rows in outputs:
        write_jsonl(path, rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch ENTRY_ADVERSE Redesign Detail",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Full scope rows: `{len(scope_rows)}`",
                f"- Accepted primary branch detail rows: `{len(branch_detail_rows)}`",
                f"- Rejected primary repair rows: `{len(rejected_repair_rows)}`",
                f"- Sidecar/context rows: `{len(sidecar_context_rows)}`",
                f"- Combined variant rows: `{len(combined_variant_rows)}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = read_json(OUTPUT_MANIFEST) if OUTPUT_MANIFEST.exists() else {"schema": "weekend_mechanical_edge_factory_output_manifest_v1", "artifacts": []}
    output_paths = [RESULT_PATH, SUMMARY_PATH] + [path for path, _rows in outputs]
    path_strings = {path.relative_to(REPO).as_posix() for path in output_paths}
    manifest["artifacts"] = [item for item in manifest.get("artifacts", []) if item.get("path") not in path_strings]
    for path in output_paths:
        manifest["artifacts"].append(
            {
                "path": path.relative_to(REPO).as_posix(),
                "status": "created",
                "type": "branch_entry_adverse_redesign_detail",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["safe_flags"] = SAFE_FLAGS
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "branch_entry_adverse_redesign_detail_built",
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
    print(json.dumps({"ok": True, "counts": result["counts"], "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
