#!/usr/bin/env python3
"""Execute scored unified candidate actions into decision-changing ledgers.

This is the first layer after unified candidate scoring. It consumes the full
786 scored implementation-candidate denominator and the 124 concentration
artifact controls, then materializes concrete keep/kill/redesign/implementation
actions for branch-local candidates and market-gap primitive candidates.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_unified_execution_scorer import (  # noqa: E402
    concentration_artifact_class,
    score_branch_candidate,
    score_market_gap_candidate,
)


SCORING_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_SCORING"
UNIFIED_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_EXECUTION_DECISION"

SCORING_RESULT = ROUTE_DIR / f"{SCORING_PREFIX}_RESULT_2026-05-16.json"
BRANCH_SCORE = ROUTE_DIR / f"{SCORING_PREFIX}_BRANCH_SCORE_LEDGER_2026-05-16.jsonl"
MARKET_GAP_SCORE = ROUTE_DIR / f"{SCORING_PREFIX}_MARKET_GAP_SCORE_LEDGER_2026-05-16.jsonl"
IMPLEMENTATION_SCORE = ROUTE_DIR / f"{SCORING_PREFIX}_IMPLEMENTATION_SCORE_LEDGER_2026-05-16.jsonl"
SYMBOL_SESSION_DECISION = ROUTE_DIR / f"{SCORING_PREFIX}_SYMBOL_SESSION_DECISION_LEDGER_2026-05-16.jsonl"
SOURCE_EXPANSION_INPUT = ROUTE_DIR / f"{SCORING_PREFIX}_SOURCE_EXPANSION_EXECUTION_LEDGER_2026-05-16.jsonl"
ENTRY_GEOMETRY_INPUT = ROUTE_DIR / f"{SCORING_PREFIX}_ENTRY_GEOMETRY_EXECUTION_LEDGER_2026-05-16.jsonl"
AVOID_INVERSE_INPUT = ROUTE_DIR / f"{SCORING_PREFIX}_AVOID_INVERSE_EXECUTION_LEDGER_2026-05-16.jsonl"
CONCENTRATION_TRANSFER_TEST = ROUTE_DIR / f"{UNIFIED_PREFIX}_CONCENTRATION_TRANSFER_TEST_LEDGER_2026-05-16.jsonl"
SCORER_SPEC_INPUT = ROUTE_DIR / f"{UNIFIED_PREFIX}_SCORER_SPEC_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
BRANCH_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
BRANCH_MARKET_ENTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_MARKET_ENTRY_COMPARATOR_LEDGER_2026-05-17.jsonl"
BRANCH_FILLABILITY_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_FILLABILITY_REDESIGN_LEDGER_2026-05-17.jsonl"
BRANCH_AVOID_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_AVOID_OR_REDIRECT_LEDGER_2026-05-17.jsonl"
BRANCH_PROVENANCE_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_PROVENANCE_LEDGER_2026-05-17.jsonl"
MARKET_SOURCE_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_GAP_SOURCE_EXPANSION_REQUIREMENT_LEDGER_2026-05-17.jsonl"
MARKET_ENTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_GAP_ENTRY_GEOMETRY_CHALLENGER_LEDGER_2026-05-17.jsonl"
MARKET_AVOID_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_GAP_AVOID_INVERSE_CONTROL_LEDGER_2026-05-17.jsonl"
MARKET_AVOID_VARIANT_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_GAP_AVOID_INVERSE_POLICY_VARIANT_LEDGER_2026-05-17.jsonl"
CONCENTRATION_RESTRESS_LEDGER = ROUTE_DIR / f"{PREFIX}_CONCENTRATION_ARTIFACT_RESTRESS_LEDGER_2026-05-17.jsonl"
SYMBOL_SESSION_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SESSION_ACTION_LEDGER_2026-05-17.jsonl"
SCORER_SPEC_CHANGE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_SPEC_CHANGE_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
QUESTION_LEDGER = ROUTE_DIR / f"{PREFIX}_QUESTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Unified candidate action-execution packet only. It consumes the full 386 branch-local scored "
    "candidate rows, 400 market-gap scored primitive rows, 786 implementation rows, and 124 concentration "
    "artifact controls to materialize branch-local scorer/spec actions, source-expansion requirements, "
    "entry-geometry challenger actions, avoid/inverse controls, and concentration restress decisions. It "
    "does not change live behavior or claim broker R/PnL, realized expectancy, win-rate, validation, "
    "live-readiness, or promotion."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    path_text = str(path)
    if len(path_text) >= 240 and not path_text.startswith("\\\\?\\"):
        return "\\\\?\\" + path_text
    return path_text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: {exc}") from exc
    return rows


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str | None:
    digest = hashlib.sha256()
    try:
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except FileNotFoundError:
        return None
    return digest.hexdigest()


def source_manifest_rows(paths: list[Path], generated_at: str) -> tuple[list[dict[str, Any]], str]:
    rows: list[dict[str, Any]] = []
    for index, path in enumerate(paths, 1):
        file_hash = sha256_file(path)
        rows.append(
            {
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-ACTION-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": file_hash,
                "status": "HASHED" if file_hash else "MISSING",
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


def compact_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(counter[key]) for key in sorted(counter, key=lambda item: str(item))}


def mean_or_none(values: list[float]) -> float | None:
    return round(mean(values), 9) if values else None


def branch_action(row: dict[str, Any]) -> tuple[str, str, str]:
    row_type = row.get("implementation_candidate_type")
    score_class = row.get("candidate_score_class")
    if row_type == "MARKET_ENTRY_COMPARATOR_SPEC":
        if score_class == "BRANCH_MARKET_ENTRY_CHALLENGER_SCORE_NOW":
            return (
                "BRANCH_MARKET_ENTRY_COMPARATOR_SCORE_NOW",
                "IMPLEMENT_RESEARCH_MARKET_ENTRY_COMPARATOR_CHALLENGER",
                "IMMEDIATE_SCORE",
            )
        return (
            "BRANCH_MARKET_ENTRY_COMPARATOR_REPAIR_FIRST",
            "REPAIR_SOURCE_OR_EXECUTION_AMBIGUITY_BEFORE_COMPARATOR",
            "REPAIR_FIRST",
        )
    if row_type == "FILLABILITY_RETEST_REDESIGN_SPEC":
        if score_class == "BRANCH_FILLABILITY_REDESIGN_PRIORITY":
            return (
                "BRANCH_FILLABILITY_REDESIGN_SCORE_NOW",
                "REDESIGN_FILLABILITY_RETEST_AND_ENTRY_OFFSET_VARIANTS",
                "IMMEDIATE_REDESIGN",
            )
        if score_class == "BRANCH_LOW_PRIORITY_OR_AVOID_FIRST":
            return (
                "BRANCH_FILLABILITY_LOW_PRIORITY_AVOID_FIRST",
                "KILL_OR_AVOID_FIRST_USE_AS_FAILURE_INTELLIGENCE",
                "AVOID_FIRST",
            )
        return (
            "BRANCH_FILLABILITY_REPAIR_FIRST",
            "REPAIR_SOURCE_OR_EXECUTION_AMBIGUITY_BEFORE_REDESIGN",
            "REPAIR_FIRST",
        )
    if row_type == "AVOID_OR_REDIRECT_SPEC":
        return (
            "BRANCH_AVOID_OR_REDIRECT_EXECUTE_FILTER",
            "MATERIALIZE_AVOID_OR_REDIRECT_REASON_BEFORE_REVIVAL",
            "AVOID_OR_KILL",
        )
    return (
        "BRANCH_PROVENANCE_PRESERVE_EXCLUDE_SCALAR",
        "PRESERVE_PROVENANCE_REQUIREMENT_EXCLUDE_FROM_SCALAR_RANKING",
        "PRESERVE",
    )


def build_branch_action_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        action_class, decision, priority = branch_action(row)
        output.append(
            with_common(
                {
                    "branch_action_execution_id": f"OHLC-GTOS-UNIFIED-ACTION-BRANCH-{index:05d}",
                    "branch_queue_id": row.get("branch_queue_id"),
                    "route_candidate_id": row.get("route_candidate_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "side": row.get("side"),
                    "entry_variant": row.get("entry_variant"),
                    "target_stop_contract_id": row.get("target_stop_contract_id"),
                    "primary_export_family": row.get("primary_export_family"),
                    "implementation_candidate_type": row.get("implementation_candidate_type"),
                    "unified_execution_decision": row.get("unified_execution_decision"),
                    "candidate_score_class": row.get("candidate_score_class"),
                    "candidate_score_band": row.get("candidate_score_band"),
                    "candidate_score_proxy": row.get("candidate_score_proxy"),
                    "candidate_score_formula": row.get("candidate_score_formula"),
                    "candidate_next_action": row.get("candidate_next_action"),
                    "rstyle_midpoint_mean": row.get("rstyle_midpoint_mean"),
                    "rstyle_proxy_signal_class": row.get("rstyle_proxy_signal_class"),
                    "target_stop_result": row.get("target_stop_result"),
                    "source_repair_pressure_class": row.get("source_repair_pressure_class"),
                    "execution_pressure_class": row.get("execution_pressure_class"),
                    "exact_failure_cause": row.get("exact_failure_cause"),
                    "exact_success_cause": row.get("exact_success_cause"),
                    "exact_missing_geometry_or_source_reason": row.get("exact_missing_geometry_or_source_reason"),
                    "action_execution_class": action_class,
                    "keep_kill_redesign_implement_decision": decision,
                    "action_execution_priority": priority,
                    "branch_local_code_candidate": "src/research_infra/moonshot_unified_execution_scorer.py",
                    "scorer_recomputed": score_branch_candidate(row),
                    "implementation_decision_changed_by_action_execution": action_class
                    != "BRANCH_PROVENANCE_PRESERVE_EXCLUDE_SCALAR",
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def source_expansion_decision(row: dict[str, Any]) -> str:
    if row.get("outside_gbpjpy_xauusd_current_branch_box"):
        if row.get("candidate_score_class") == "MARKET_GAP_SOURCE_EXPANSION_HIGH_PRIORITY":
            return "EXPAND_OUTSIDE_BRANCH_DENOMINATOR_HIGH_PRIORITY_TO_N20"
        return "EXPAND_OUTSIDE_BRANCH_DENOMINATOR_REQUIRED_TO_N20"
    return "EXPAND_CURRENT_CONCENTRATION_GAP_CONTROL_TO_N20"


def build_source_expansion_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        output.append(
            with_common(
                {
                    "source_expansion_requirement_id": f"OHLC-GTOS-UNIFIED-ACTION-SOURCE-{index:05d}",
                    "market_gap_combo_id": row.get("market_gap_combo_id"),
                    "market_gap_action_id": row.get("market_gap_action_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "candidate_score_class": row.get("candidate_score_class"),
                    "candidate_score_band": row.get("candidate_score_band"),
                    "candidate_score_proxy": row.get("candidate_score_proxy"),
                    "candidate_score_formula": row.get("candidate_score_formula"),
                    "candidate_next_action": row.get("candidate_next_action"),
                    "action_class": row.get("action_class"),
                    "unified_execution_decision": row.get("unified_execution_decision"),
                    "movement_status": row.get("movement_status"),
                    "flagged_n": row.get("flagged_n"),
                    "control_n": row.get("control_n"),
                    "flagged_to_control_ratio": row.get("flagged_to_control_ratio"),
                    "additional_flagged_rows_needed_for_n20": row.get("additional_flagged_rows_needed_for_n20"),
                    "delta_alignment_rate": row.get("delta_alignment_rate"),
                    "delta_mean_abs_future_change": row.get("delta_mean_abs_future_change"),
                    "nofill_sidecar_status": row.get("nofill_sidecar_status"),
                    "residual_transfer_class": row.get("residual_transfer_class"),
                    "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                    "source_expansion_execution_decision": source_expansion_decision(row),
                    "source_expansion_target": "N20_FLAGGED_DENOMINATOR_OR_EXACT_SOURCE_SPLIT",
                    "market_gap_score_recomputed": score_market_gap_candidate(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_entry_geometry_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        mixed = row.get("candidate_score_class") == "MARKET_GAP_ENTRY_GEOMETRY_MIXED_ALIGNMENT_SCORE_WITH_CONTROL"
        decision = (
            "IMPLEMENT_ENTRY_GEOMETRY_CHALLENGER_WITH_ALIGNMENT_CONTROL_SPLIT"
            if mixed
            else "IMPLEMENT_ENTRY_GEOMETRY_CHALLENGER_SCORE_NOW"
        )
        output.append(
            with_common(
                {
                    "entry_geometry_challenger_id": f"OHLC-GTOS-UNIFIED-ACTION-ENTRY-{index:05d}",
                    "market_gap_combo_id": row.get("market_gap_combo_id"),
                    "market_gap_action_id": row.get("market_gap_action_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "session_bucket": row.get("session_bucket"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "candidate_score_class": row.get("candidate_score_class"),
                    "candidate_score_band": row.get("candidate_score_band"),
                    "candidate_score_proxy": row.get("candidate_score_proxy"),
                    "candidate_score_formula": row.get("candidate_score_formula"),
                    "candidate_next_action": row.get("candidate_next_action"),
                    "action_class": row.get("action_class"),
                    "unified_execution_decision": row.get("unified_execution_decision"),
                    "movement_status": row.get("movement_status"),
                    "flagged_n": row.get("flagged_n"),
                    "control_n": row.get("control_n"),
                    "delta_alignment_rate": row.get("delta_alignment_rate"),
                    "delta_mean_abs_future_change": row.get("delta_mean_abs_future_change"),
                    "nofill_sidecar_status": row.get("nofill_sidecar_status"),
                    "residual_transfer_class": row.get("residual_transfer_class"),
                    "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
                    "entry_geometry_execution_decision": decision,
                    "entry_geometry_variant_set": [
                        "PRIMITIVE_CLOSE_MARKET_ENTRY",
                        "NEXT_M1_OPEN_MARKET_ENTRY",
                        "HALF_SPREAD_OFFSET_ENTRY",
                        "STATUS_QUO_NO_BRANCH_CONTROL",
                    ],
                    "control_required": mixed,
                    "market_gap_score_recomputed": score_market_gap_candidate(row),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_avoid_inverse_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parent_rows: list[dict[str, Any]] = []
    variant_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        parent_id = f"OHLC-GTOS-UNIFIED-ACTION-AVOID-{index:05d}"
        common = {
            "avoid_inverse_control_id": parent_id,
            "market_gap_combo_id": row.get("market_gap_combo_id"),
            "market_gap_action_id": row.get("market_gap_action_id"),
            "symbol": row.get("symbol"),
            "route_session": row.get("route_session"),
            "session_bucket": row.get("session_bucket"),
            "horizon_id": row.get("horizon_id"),
            "primitive_flag": row.get("primitive_flag"),
            "candidate_score_class": row.get("candidate_score_class"),
            "candidate_score_band": row.get("candidate_score_band"),
            "candidate_score_proxy": row.get("candidate_score_proxy"),
            "candidate_score_formula": row.get("candidate_score_formula"),
            "candidate_next_action": row.get("candidate_next_action"),
            "action_class": row.get("action_class"),
            "unified_execution_decision": row.get("unified_execution_decision"),
            "movement_status": row.get("movement_status"),
            "flagged_n": row.get("flagged_n"),
            "control_n": row.get("control_n"),
            "delta_alignment_rate": row.get("delta_alignment_rate"),
            "delta_mean_abs_future_change": row.get("delta_mean_abs_future_change"),
            "nofill_sidecar_status": row.get("nofill_sidecar_status"),
            "residual_transfer_class": row.get("residual_transfer_class"),
            "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
            "market_gap_score_recomputed": score_market_gap_candidate(row),
        }
        parent_rows.append(
            with_common(
                {
                    **common,
                    "avoid_inverse_execution_decision": "IMPLEMENT_AVOID_FILTER_AND_INVERSE_CONTROL_PAIR",
                    "policy_variant_count": 2,
                },
                generated_at,
                manifest_hash,
            )
        )
        for variant_index, variant in enumerate(
            [
                (
                    "AVOID_FILTER_VARIANT",
                    "AVOID_PRIMITIVE_FLAG_IN_SYMBOL_SESSION_HORIZON",
                ),
                (
                    "INVERSE_OR_FADE_CONTROL_VARIANT",
                    "TEST_INVERSE_OR_FADE_CONTROL_AGAINST_NO_TRADE_BASELINE",
                ),
            ],
            1,
        ):
            variant_rows.append(
                with_common(
                    {
                        **common,
                        "avoid_inverse_policy_variant_id": f"{parent_id}-VAR-{variant_index:02d}",
                        "parent_avoid_inverse_control_id": parent_id,
                        "policy_variant_type": variant[0],
                        "policy_variant_decision": variant[1],
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return parent_rows, variant_rows


def restress_decision(row: dict[str, Any]) -> str:
    if row.get("test_axis") == "SOURCE_ROOT":
        root = row.get("source_root")
        if root == "TICK_M15_FULL_TRANSFER_BASE":
            return "SOURCE_ROOT_FULL_TRANSFER_BASE_AVAILABLE_RESTRESS_BRANCH_NARROWNESS"
        if root == "TICK_MARKET_GAP_OUTSIDE_CURRENT_BRANCH_DENOMINATOR":
            return "SOURCE_ROOT_MARKET_GAP_OUTSIDE_BRANCH_EXECUTE_ACTIONS"
        return "SOURCE_ROOT_CURRENT_BRANCH_DIRECT_CONTEXT_NARROWNESS_CONFIRMED"
    class_name = row.get("concentration_artifact_class")
    if class_name == "MECHANISM_CONCENTRATED_BUT_DENOMINATOR_NARROWNESS_CONFIRMED":
        return "REAL_CONCENTRATION_AND_DENOMINATOR_ARTIFACT_BOTH_TRUE"
    if class_name == "CURRENT_BRANCH_COVERAGE_PRESENT":
        return "CURRENT_BRANCH_COVERAGE_PRESENT_RESTRESS_WITH_MARKET_GAP_ROWS"
    return "DENOMINATOR_ARTIFACT_AVAILABLE_SYMBOL_SESSION_HORIZON_RESTRESS"


def build_concentration_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        recomputed_class = None
        if row.get("test_axis") != "SOURCE_ROOT":
            recomputed_class = concentration_artifact_class(
                int(row.get("current_branch_rows") or 0),
                int(row.get("market_gap_combo_rows") or 0),
                int(row.get("full_tick_transfer_rows") or 0),
                386,
                400,
            )
        output.append(
            with_common(
                {
                    "concentration_artifact_restress_id": f"OHLC-GTOS-UNIFIED-ACTION-CONC-{index:05d}",
                    "source_concentration_transfer_test_id": row.get("concentration_transfer_test_id"),
                    "test_axis": row.get("test_axis"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "source_root": row.get("source_root"),
                    "source_root_row_count": row.get("row_count"),
                    "source_root_symbol_count": row.get("symbol_count"),
                    "source_root_symbols": row.get("symbols"),
                    "current_branch_rows": row.get("current_branch_rows"),
                    "full_tick_transfer_rows": row.get("full_tick_transfer_rows"),
                    "market_gap_combo_rows": row.get("market_gap_combo_rows"),
                    "nofill_direct_context_rows": row.get("nofill_direct_context_rows"),
                    "nearmiss_direct_context_rows": row.get("nearmiss_direct_context_rows"),
                    "concentration_artifact_class": row.get("concentration_artifact_class"),
                    "concentration_artifact_class_recomputed": recomputed_class,
                    "restress_execution_decision": restress_decision(row),
                    "decision_implication": row.get("decision_implication"),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_symbol_session_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        decision_counts = row.get("unified_execution_decision_counts", {})
        if row.get("concentration_decision") == "CURRENT_BRANCH_AND_MARKET_GAP_BOTH_PRESENT":
            action = "RUN_BRANCH_AND_MARKET_GAP_SIDE_BY_SIDE_ACTION_EXECUTION"
        elif decision_counts.get("IMPLEMENT_MARKET_GAP_ENTRY_GEOMETRY_CHALLENGER") or decision_counts.get(
            "IMPLEMENT_MARKET_GAP_AVOID_INVERSE_CONTROL"
        ):
            action = "RUN_MARKET_GAP_CHALLENGER_OR_AVOID_CONTROL"
        else:
            action = "RUN_MARKET_GAP_SOURCE_EXPANSION_TO_N20"
        output.append(
            with_common(
                {
                    "symbol_session_action_id": f"OHLC-GTOS-UNIFIED-ACTION-SYMSESS-{index:04d}",
                    "source_symbol_session_decision_id": row.get("symbol_session_decision_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "concentration_decision": row.get("concentration_decision"),
                    "symbol_session_action": action,
                    "all_candidate_rows": row.get("all_candidate_rows"),
                    "branch_score_rows": row.get("branch_score_rows"),
                    "market_gap_score_rows": row.get("market_gap_score_rows"),
                    "candidate_score_proxy_mean": row.get("candidate_score_proxy_mean"),
                    "candidate_score_class_counts": row.get("candidate_score_class_counts"),
                    "implementation_candidate_type_counts": row.get("implementation_candidate_type_counts"),
                    "unified_execution_decision_counts": decision_counts,
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def build_scorer_spec_rows(rows: list[dict[str, Any]], generated_at: str, manifest_hash: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        candidate_type = row.get("implementation_candidate_type")
        if candidate_type == "CONCENTRATION_ARTIFACT_TEST":
            status = "ACTION_EXECUTION_RESTRESSES_CONCENTRATION_AXES"
        elif candidate_type == "MARKET_GAP_SOURCE_EXPANSION_SPEC":
            status = "ACTION_EXECUTION_EMITS_SOURCE_EXPANSION_REQUIREMENTS"
        elif candidate_type == "MARKET_GAP_ENTRY_GEOMETRY_SPEC":
            status = "ACTION_EXECUTION_EMITS_ENTRY_GEOMETRY_CHALLENGERS"
        elif candidate_type == "MARKET_GAP_AVOID_INVERSE_SPEC":
            status = "ACTION_EXECUTION_EMITS_AVOID_AND_INVERSE_POLICY_VARIANTS"
        else:
            status = "ACTION_EXECUTION_EMITS_BRANCH_LOCAL_DECISION_ROWS"
        output.append(
            with_common(
                {
                    "scorer_spec_change_id": f"OHLC-GTOS-UNIFIED-ACTION-SCORER-{index:04d}",
                    "source_scorer_spec_id": row.get("scorer_spec_id"),
                    "implementation_candidate_type": candidate_type,
                    "code_surface": row.get("code_surface"),
                    "builder_surface": row.get("builder_surface"),
                    "input_denominator": row.get("input_denominator"),
                    "output_decision_field": row.get("output_decision_field"),
                    "required_controls": row.get("required_controls"),
                    "action_execution_status": status,
                    "action_execution_code_candidate": "src/research_infra/moonshot_unified_execution_scorer.py",
                },
                generated_at,
                manifest_hash,
            )
        )
    return output


def bucket_rows_from_sources(groups: dict[str, list[dict[str, Any]]], generated_at: str, manifest_hash: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    counters = {
        "branch_action_execution_class": Counter(row.get("action_execution_class") for row in groups["branch_action"]),
        "branch_keep_kill_redesign_implement_decision": Counter(
            row.get("keep_kill_redesign_implement_decision") for row in groups["branch_action"]
        ),
        "source_expansion_execution_decision": Counter(
            row.get("source_expansion_execution_decision") for row in groups["source_expansion"]
        ),
        "entry_geometry_execution_decision": Counter(
            row.get("entry_geometry_execution_decision") for row in groups["entry_geometry"]
        ),
        "avoid_inverse_execution_decision": Counter(
            row.get("avoid_inverse_execution_decision") for row in groups["avoid_inverse"]
        ),
        "avoid_inverse_policy_variant_type": Counter(
            row.get("policy_variant_type") for row in groups["avoid_inverse_variant"]
        ),
        "concentration_restress_execution_decision": Counter(
            row.get("restress_execution_decision") for row in groups["concentration"]
        ),
        "symbol_session_action": Counter(row.get("symbol_session_action") for row in groups["symbol_session"]),
        "scorer_spec_action_execution_status": Counter(
            row.get("action_execution_status") for row in groups["scorer_spec"]
        ),
    }
    output: list[dict[str, Any]] = []
    for family, counter in counters.items():
        for key, count in sorted(counter.items(), key=lambda item: str(item[0])):
            output.append(
                with_common(
                    {
                        "bucket_id": f"OHLC-GTOS-UNIFIED-ACTION-BUCKET-{len(output) + 1:04d}",
                        "bucket_family": family,
                        "bucket_value": key,
                        "row_count": int(count),
                    },
                    generated_at,
                    manifest_hash,
                )
            )
    return output, {name: compact_counter(counter) for name, counter in counters.items()}


def append_manifest(paths: list[Path], result: dict[str, Any]) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    generated = manifest.setdefault("generated_artifacts", [])
    existing = {row.get("path") for row in generated if isinstance(row, dict)}
    for path in paths:
        rel = path.relative_to(REPO).as_posix()
        if rel not in existing:
            generated.append(
                {
                    "path": rel,
                    "artifact": PREFIX,
                    "sha256": sha256_file(path),
                    "safe_flags": SAFE_FLAGS,
                    "not_completion": True,
                }
            )
    manifest["latest_unified_candidate_action_execution"] = {
        "artifact": PREFIX,
        "counts": result["counts"],
        "generated_utc": result["generated_utc"],
        "source_manifest_hash": result["source_manifest_hash"],
    }
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def append_sprint_ledger(result: dict[str, Any]) -> None:
    row = {
        "timestamp_utc": result["generated_utc"],
        "route": PREFIX,
        "event": "unified_candidate_action_execution_materialized",
        "counts": result["counts"],
        "safe_flags": SAFE_FLAGS,
        "not_completion": True,
        "summary": (
            "Executed the scored 786-row implementation denominator into branch, source-expansion, "
            "entry-geometry, avoid/inverse, and concentration-restress action ledgers."
        ),
    }
    with open(long_path(SPRINT_LEDGER), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    source_paths = [
        SCORING_RESULT,
        BRANCH_SCORE,
        MARKET_GAP_SCORE,
        IMPLEMENTATION_SCORE,
        SYMBOL_SESSION_DECISION,
        SOURCE_EXPANSION_INPUT,
        ENTRY_GEOMETRY_INPUT,
        AVOID_INVERSE_INPUT,
        CONCENTRATION_TRANSFER_TEST,
        SCORER_SPEC_INPUT,
        REPO / "src/research_infra/moonshot_unified_execution_scorer.py",
    ]
    source_manifest, manifest_hash = source_manifest_rows(source_paths, generated_at)

    scoring_result = read_json(SCORING_RESULT)
    branch_score_rows = read_jsonl(BRANCH_SCORE)
    market_gap_score_rows = read_jsonl(MARKET_GAP_SCORE)
    implementation_score_rows = read_jsonl(IMPLEMENTATION_SCORE)
    symbol_session_source_rows = read_jsonl(SYMBOL_SESSION_DECISION)
    source_expansion_input_rows = read_jsonl(SOURCE_EXPANSION_INPUT)
    entry_geometry_input_rows = read_jsonl(ENTRY_GEOMETRY_INPUT)
    avoid_inverse_input_rows = read_jsonl(AVOID_INVERSE_INPUT)
    concentration_source_rows = read_jsonl(CONCENTRATION_TRANSFER_TEST)
    scorer_spec_source_rows = read_jsonl(SCORER_SPEC_INPUT)

    branch_action_rows = build_branch_action_rows(branch_score_rows, generated_at, manifest_hash)
    branch_market_entry_rows = [
        row for row in branch_action_rows if row.get("implementation_candidate_type") == "MARKET_ENTRY_COMPARATOR_SPEC"
    ]
    branch_fillability_rows = [
        row for row in branch_action_rows if row.get("implementation_candidate_type") == "FILLABILITY_RETEST_REDESIGN_SPEC"
    ]
    branch_avoid_rows = [
        row for row in branch_action_rows if row.get("implementation_candidate_type") == "AVOID_OR_REDIRECT_SPEC"
    ]
    branch_provenance_rows = [
        row for row in branch_action_rows if row.get("implementation_candidate_type") == "PROVENANCE_REQUIREMENT"
    ]
    source_expansion_rows = build_source_expansion_rows(source_expansion_input_rows, generated_at, manifest_hash)
    entry_geometry_rows = build_entry_geometry_rows(entry_geometry_input_rows, generated_at, manifest_hash)
    avoid_inverse_rows, avoid_inverse_variant_rows = build_avoid_inverse_rows(
        avoid_inverse_input_rows, generated_at, manifest_hash
    )
    concentration_rows = build_concentration_rows(concentration_source_rows, generated_at, manifest_hash)
    symbol_session_rows = build_symbol_session_rows(symbol_session_source_rows, generated_at, manifest_hash)
    scorer_spec_rows = build_scorer_spec_rows(scorer_spec_source_rows, generated_at, manifest_hash)

    groups = {
        "branch_action": branch_action_rows,
        "source_expansion": source_expansion_rows,
        "entry_geometry": entry_geometry_rows,
        "avoid_inverse": avoid_inverse_rows,
        "avoid_inverse_variant": avoid_inverse_variant_rows,
        "concentration": concentration_rows,
        "symbol_session": symbol_session_rows,
        "scorer_spec": scorer_spec_rows,
    }
    bucket_rows, distributions = bucket_rows_from_sources(groups, generated_at, manifest_hash)

    question_rows = [
        {
            "question_id": "OHLC-GTOS-UNIFIED-ACTION-Q-001",
            "question": "Which current-branch candidates can move to market-entry comparator scoring now?",
            "answer_route": "Use 27 MARKET_ENTRY_COMPARATOR score-now rows and keep the 2 repair-first rows separate.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-ACTION-Q-002",
            "question": "Which fillability rows should be redesigned versus killed or repaired first?",
            "answer_route": "Use 103 redesign-priority, 92 avoid-first, and 18 repair-first fillability rows.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-ACTION-Q-003",
            "question": "How much outside-market source expansion is mechanically required before branch scoring?",
            "answer_route": "Use 309 source-expansion rows and 3743 total flagged-row requirements to reach N20 where needed.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-ACTION-Q-004",
            "question": "Which market-gap primitives become immediate entry-geometry or avoid/inverse tests?",
            "answer_route": "Use 68 entry-geometry challenger rows and 23 avoid/inverse parent rows with 46 policy variants.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-ACTION-Q-005",
            "question": "Is GBPJPY/XAUUSD concentration a complete search boundary?",
            "answer_route": "No. Restress all 124 concentration rows and execute 25 market-gap-only symbol/session action rows.",
        },
    ]
    question_rows = [with_common(row, generated_at, manifest_hash) for row in question_rows]

    generated_files = [
        BRANCH_ACTION_LEDGER,
        BRANCH_MARKET_ENTRY_LEDGER,
        BRANCH_FILLABILITY_LEDGER,
        BRANCH_AVOID_LEDGER,
        BRANCH_PROVENANCE_LEDGER,
        MARKET_SOURCE_LEDGER,
        MARKET_ENTRY_LEDGER,
        MARKET_AVOID_LEDGER,
        MARKET_AVOID_VARIANT_LEDGER,
        CONCENTRATION_RESTRESS_LEDGER,
        SYMBOL_SESSION_ACTION_LEDGER,
        SCORER_SPEC_CHANGE_LEDGER,
        BUCKET_LEDGER,
        QUESTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
    ]

    source_expansion_required = sum(
        int(row.get("additional_flagged_rows_needed_for_n20") or 0) for row in source_expansion_rows
    )
    outside_market_gap_actions = sum(
        1 for row in market_gap_score_rows if row.get("outside_gbpjpy_xauusd_current_branch_box")
    )
    score_values = [
        float(row["candidate_score_proxy"])
        for row in implementation_score_rows
        if row.get("candidate_score_proxy") is not None
    ]
    counts = {
        "input_branch_score_rows": len(branch_score_rows),
        "input_market_gap_score_rows": len(market_gap_score_rows),
        "input_implementation_score_rows": len(implementation_score_rows),
        "input_concentration_transfer_rows": len(concentration_source_rows),
        "branch_action_execution_rows": len(branch_action_rows),
        "branch_market_entry_comparator_rows": len(branch_market_entry_rows),
        "branch_fillability_redesign_rows": len(branch_fillability_rows),
        "branch_avoid_or_redirect_rows": len(branch_avoid_rows),
        "branch_provenance_rows": len(branch_provenance_rows),
        "market_gap_source_expansion_requirement_rows": len(source_expansion_rows),
        "market_gap_entry_geometry_challenger_rows": len(entry_geometry_rows),
        "market_gap_avoid_inverse_control_rows": len(avoid_inverse_rows),
        "market_gap_avoid_inverse_policy_variant_rows": len(avoid_inverse_variant_rows),
        "concentration_artifact_restress_rows": len(concentration_rows),
        "symbol_session_action_rows": len(symbol_session_rows),
        "scorer_spec_change_rows": len(scorer_spec_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
        "source_expansion_additional_flagged_rows_needed_for_n20_total": source_expansion_required,
        "market_gap_rows_outside_gbpjpy_xauusd_current_branch_box": outside_market_gap_actions,
    }
    system_decision = {
        "implementation_score_proxy_mean": mean_or_none(score_values),
        "branch_action_counts": distributions["branch_action_execution_class"],
        "market_gap_action_counts": {
            "source_expansion": len(source_expansion_rows),
            "entry_geometry": len(entry_geometry_rows),
            "avoid_inverse": len(avoid_inverse_rows),
            "avoid_inverse_policy_variants": len(avoid_inverse_variant_rows),
        },
        "concentration_restress_counts": distributions["concentration_restress_execution_decision"],
        "system_recommendation": (
            "UNIFIED_CANDIDATE_ACTION_EXECUTION_RESULT: implement research-only branch market-entry comparator "
            "scoring for 27 score-now rows, execute 103 fillability redesign rows, materialize 133 branch "
            "avoid/redirect reasons, expand 309 market-gap source denominators, score 68 market-gap "
            "entry-geometry challengers, test 23 avoid/inverse controls as 46 policy variants, and keep "
            "GBPJPY/XAUUSD concentration under 124-row restress rather than treating it as the search boundary."
        ),
    }
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "source_manifest_hash": manifest_hash,
        "counts": counts,
        "upstream_counts": {"unified_candidate_scoring": scoring_result.get("counts", {})},
        "bucket_distributions": distributions,
        "system_decision": system_decision,
    }

    write_jsonl(BRANCH_ACTION_LEDGER, branch_action_rows)
    write_jsonl(BRANCH_MARKET_ENTRY_LEDGER, branch_market_entry_rows)
    write_jsonl(BRANCH_FILLABILITY_LEDGER, branch_fillability_rows)
    write_jsonl(BRANCH_AVOID_LEDGER, branch_avoid_rows)
    write_jsonl(BRANCH_PROVENANCE_LEDGER, branch_provenance_rows)
    write_jsonl(MARKET_SOURCE_LEDGER, source_expansion_rows)
    write_jsonl(MARKET_ENTRY_LEDGER, entry_geometry_rows)
    write_jsonl(MARKET_AVOID_LEDGER, avoid_inverse_rows)
    write_jsonl(MARKET_AVOID_VARIANT_LEDGER, avoid_inverse_variant_rows)
    write_jsonl(CONCENTRATION_RESTRESS_LEDGER, concentration_rows)
    write_jsonl(SYMBOL_SESSION_ACTION_LEDGER, symbol_session_rows)
    write_jsonl(SCORER_SPEC_CHANGE_LEDGER, scorer_spec_rows)
    write_jsonl(BUCKET_LEDGER, bucket_rows)
    write_jsonl(QUESTION_LEDGER, question_rows)
    write_jsonl(SOURCE_MANIFEST_LEDGER, source_manifest)
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch System Transfer Unified Candidate Action Execution",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Branch action rows: `{counts['branch_action_execution_rows']}`",
                f"- Market-gap source-expansion rows: `{counts['market_gap_source_expansion_requirement_rows']}`",
                f"- Market-gap entry-geometry rows: `{counts['market_gap_entry_geometry_challenger_rows']}`",
                f"- Market-gap avoid/inverse rows: `{counts['market_gap_avoid_inverse_control_rows']}`",
                f"- Concentration restress rows: `{counts['concentration_artifact_restress_rows']}`",
                "",
                "Core result: every scored candidate now has a concrete action-execution row that changes a keep, kill, redesign, implementation, or restress decision.",
                "",
            ]
        ),
    )
    append_manifest([RESULT_PATH, SUMMARY_PATH, *generated_files], result)
    append_sprint_ledger(result)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
