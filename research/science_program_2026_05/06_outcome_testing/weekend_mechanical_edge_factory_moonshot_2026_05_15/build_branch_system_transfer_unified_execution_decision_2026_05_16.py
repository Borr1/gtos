#!/usr/bin/env python3
"""Build unified system-transfer execution decisions from branch result packets.

This packet converts transfer/join evidence into branch-level keep/kill/redesign/
implement decisions, R-style proxy result rows, implementation candidates, and
concentration-artifact tests. It preserves full denominators and does not change
live behavior.
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

from src.research_infra.moonshot_unified_execution_scorer import (
    classify_market_gap_candidate,
    classify_unified_branch_decision,
    concentration_artifact_class,
    summarize_labels,
)


SYSTEM_TRANSFER_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_RECOMMENDATION_RESULT_2026-05-16.json"
SYSTEM_TRANSFER_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_RECOMMENDATION_BRANCH_LEDGER_2026-05-16.jsonl"
SYSTEM_TRANSFER_MARKET_SESSION = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_RECOMMENDATION_MARKET_SESSION_DECISION_LEDGER_2026-05-16.jsonl"
RSTYLE_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_RESULT_2026-05-16.json"
RSTYLE_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_RSTYLE_PROXY_OUTCOME_LAYER_BRANCH_LEDGER_2026-05-16.jsonl"
FULL_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_RESULT_2026-05-16.json"
FULL_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_FULL_OUTCOME_IMPLEMENTATION_SYNTHESIS_BRANCH_LEDGER_2026-05-16.jsonl"
NOFILL_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NOFILL_AVOID_RETEST_JOIN_RESULT_2026-05-16.json"
NOFILL_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NOFILL_AVOID_RETEST_JOIN_BRANCH_SUMMARY_LEDGER_2026-05-16.jsonl"
NEARMISS_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN_RESULT_2026-05-16.json"
NEARMISS_BRANCH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN_BRANCH_SUMMARY_LEDGER_2026-05-16.jsonl"
TICK_CONTEXT_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_TICK_PRIMITIVE_CONTEXT_RESULT_2026-05-16.json"
TICK_BRANCH_SUMMARY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_TICK_PRIMITIVE_CONTEXT_BRANCH_SUMMARY_LEDGER_2026-05-16.jsonl"
TICK_MARKET_GAP = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_TICK_PRIMITIVE_CONTEXT_MARKET_GAP_LEDGER_2026-05-16.jsonl"
CROSS_BASE = ROUTE_DIR / "TICK_M15_CROSS_TRANSFER_BASE_ROW_LEDGER_2026-05-16.jsonl"
MARKET_GAP_RESULT = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_MARKET_GAP_PRIMITIVE_EXPANSION_RESULT_2026-05-16.json"
MARKET_GAP_COMBO = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_MARKET_GAP_PRIMITIVE_EXPANSION_COMBO_LEDGER_2026-05-16.jsonl"
MARKET_GAP_ACTION = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_MARKET_GAP_PRIMITIVE_EXPANSION_ACTION_LEDGER_2026-05-16.jsonl"
MARKET_GAP_KEY = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_MARKET_GAP_PRIMITIVE_EXPANSION_KEY_LEDGER_2026-05-16.jsonl"
MARKET_GAP_SYMBOL_SESSION = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_MARKET_GAP_PRIMITIVE_EXPANSION_SYMBOL_SESSION_LEDGER_2026-05-16.jsonl"

PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_EXECUTION_DECISION"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-16.json"
BRANCH_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_EXECUTION_LEDGER_2026-05-16.jsonl"
BRANCH_RSTYLE_LEDGER = ROUTE_DIR / f"{PREFIX}_BRANCH_RSTYLE_RESULT_LEDGER_2026-05-16.jsonl"
FAMILY_SYMBOL_SESSION_RSTYLE_LEDGER = ROUTE_DIR / f"{PREFIX}_FAMILY_SYMBOL_SESSION_RSTYLE_LEDGER_2026-05-16.jsonl"
IMPLEMENTATION_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-16.jsonl"
CONCENTRATION_TRANSFER_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_CONCENTRATION_TRANSFER_TEST_LEDGER_2026-05-16.jsonl"
MARKET_GAP_IMPLEMENTATION_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_GAP_IMPLEMENTATION_LEDGER_2026-05-16.jsonl"
SCORER_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_SPEC_LEDGER_2026-05-16.jsonl"
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
    "Branch system-transfer unified execution decision packet only. It joins the full 386-branch "
    "system-transfer denominator to R-style proxy outcomes, no-fill/retest, near-miss market-entry, "
    "full-outcome synthesis, and 400 market-gap primitive expansion rows to compute keep/kill/redesign/"
    "implement candidate labels, branch/family/symbol/session proxy-result rows, implementation specs, "
    "and concentration-artifact tests. It does not change live behavior or claim broker R/PnL, realized "
    "expectancy, win-rate, validation, live-readiness, or promotion."
)

MISSING_EXACT_REASON = (
    "Exact broker R/PnL cannot be computed from this evidence class because source-bound broker fills, "
    "account history, true executed stop distance, slippage, partial exits, and order lifecycle are not "
    "available in the historical proxy rows. This packet carries the strongest target/stop/path proxy "
    "and exact missing geometry/source reason forward per branch."
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    path_text = str(path)
    if len(path_text) >= 240 and not path_text.startswith("\\\\?\\"):
        return "\\\\?\\" + path_text
    return path_text


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
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
                "source_manifest_id": f"OHLC-GTOS-UNIFIED-EXEC-SRC-{index:04d}",
                "path": path.relative_to(REPO).as_posix(),
                "sha256": sha256_file(path),
                "status": "HASHED" if path.exists() else "MISSING",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
                "generated_utc": generated_at,
            }
        )
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, digest


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


def by_branch(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("branch_queue_id")): row for row in rows if row.get("branch_queue_id") is not None}


def route_parts(route_candidate_id: Any) -> tuple[str, str, str, str]:
    parts = str(route_candidate_id or "").split("|")
    if len(parts) >= 4:
        return parts[0], parts[1], parts[2], parts[3]
    return "UNKNOWN_SYMBOL", "UNKNOWN_SESSION", "UNKNOWN_DESCRIPTOR", "UNKNOWN_HORIZON"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mean_or_none(values: list[float]) -> float | None:
    return round(mean(values), 9) if values else None


def min_or_none(values: list[float]) -> float | None:
    return round(min(values), 9) if values else None


def max_or_none(values: list[float]) -> float | None:
    return round(max(values), 9) if values else None


def nested_counter_update(counter: Counter[str], mapping: dict[str, int] | None) -> None:
    for key, value in (mapping or {}).items():
        counter[str(key)] += int(value)


def build_branch_rows(
    system_rows: list[dict[str, Any]],
    rstyle_by_id: dict[str, dict[str, Any]],
    full_by_id: dict[str, dict[str, Any]],
    nofill_by_id: dict[str, dict[str, Any]],
    near_by_id: dict[str, dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    branch_execution_rows: list[dict[str, Any]] = []
    branch_rstyle_rows: list[dict[str, Any]] = []
    implementation_rows: list[dict[str, Any]] = []

    for index, system_row in enumerate(system_rows, 1):
        branch_id = system_row["branch_queue_id"]
        rstyle_row = rstyle_by_id.get(branch_id, {})
        full_row = full_by_id.get(branch_id, {})
        nofill_row = nofill_by_id.get(branch_id, {})
        near_row = near_by_id.get(branch_id, {})
        symbol, route_session, descriptor, horizon_id = route_parts(system_row.get("route_candidate_id"))
        family = system_row.get("primary_export_family")

        combined = {}
        for source in (rstyle_row, full_row, nofill_row, near_row, system_row):
            combined.update(source)
        combined["primary_export_family"] = family
        combined["decision_direction"] = system_row.get("decision_direction")
        combined["system_decision_class"] = system_row.get("system_decision_class")

        decision = classify_unified_branch_decision(combined)
        exact_missing_reason = (
            system_row.get("exact_missing_geometry_or_source_reason")
            or rstyle_row.get("missing_exact_geometry_reason")
            or full_row.get("exact_missing_geometry_or_source_reason")
            or MISSING_EXACT_REASON
        )
        rstyle_midpoint = to_float(full_row.get("rstyle_midpoint_mean"))
        if rstyle_midpoint is None:
            proxy = rstyle_row.get("expectancy_style_proxy") or {}
            rstyle_midpoint = to_float(proxy.get("rstyle_midpoint_mean") or proxy.get("midpoint_mean"))

        branch_execution_rows.append(
            with_common(
                {
                    "unified_execution_branch_id": f"OHLC-GTOS-UNIFIED-EXEC-BRANCH-{index:05d}",
                    "branch_queue_id": branch_id,
                    "route_candidate_id": system_row.get("route_candidate_id"),
                    "target_stop_contract_id": system_row.get("target_stop_contract_id"),
                    "entry_variant": system_row.get("entry_variant"),
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "route_descriptor": descriptor,
                    "side": system_row.get("side"),
                    "primary_export_family": family,
                    "system_decision_class": system_row.get("system_decision_class"),
                    "system_decision_direction": system_row.get("decision_direction"),
                    "unified_execution_decision": decision["unified_execution_decision"],
                    "implementation_candidate_type": decision["implementation_candidate_type"],
                    "unified_next_action": decision["unified_next_action"],
                    "rstyle_proxy_signal_class": decision["rstyle_proxy_signal_class"],
                    "source_repair_pressure_class": decision["source_repair_pressure_class"],
                    "execution_pressure_class": decision["execution_pressure_class"],
                    "target_stop_result": system_row.get("target_stop_result") or rstyle_row.get("target_stop_result"),
                    "branch_result_class": full_row.get("branch_result_class") or rstyle_row.get("branch_result_class"),
                    "sealed_or_proxy_outcome_status": full_row.get("sealed_or_proxy_outcome_status"),
                    "rstyle_lower_mean": full_row.get("rstyle_lower_mean"),
                    "rstyle_midpoint_mean": rstyle_midpoint,
                    "rstyle_upper_mean": full_row.get("rstyle_upper_mean"),
                    "pass_control_delta_status": rstyle_row.get("pass_control_delta_status") or full_row.get("pass_control_delta_status"),
                    "cost_sensitivity_proxy_status": full_row.get("cost_sensitivity_proxy_status") or rstyle_row.get("cost_robustness_bucket"),
                    "duplicate_effective_n": full_row.get("duplicate_effective_n") or rstyle_row.get("effective_n_fields"),
                    "effective_n_concentration_class": full_row.get("effective_n_concentration_class"),
                    "concentration_summary": full_row.get("concentration_summary") or rstyle_row.get("concentration_summary"),
                    "source_confidence_status": full_row.get("source_confidence_status") or rstyle_row.get("source_confidence_status"),
                    "ambiguity_status": full_row.get("ambiguity_status") or rstyle_row.get("ambiguity_status"),
                    "nofill_join_status": nofill_row.get("nofill_join_status"),
                    "nofill_transfer_implication": nofill_row.get("nofill_transfer_implication"),
                    "nearmiss_join_status": near_row.get("nearmiss_join_status"),
                    "nearmiss_transfer_implication": near_row.get("nearmiss_transfer_implication"),
                    "market_transfer_class": system_row.get("market_transfer_class"),
                    "market_specific_concentration_flag": system_row.get("market_specific_concentration_flag"),
                    "exact_failure_cause": near_row.get("exact_failure_cause") or nofill_row.get("exact_failure_cause") or system_row.get("exact_failure_cause"),
                    "exact_success_cause": near_row.get("exact_success_cause") or nofill_row.get("exact_success_cause") or system_row.get("exact_success_cause"),
                    "exact_missing_geometry_or_source_reason": exact_missing_reason,
                },
                generated_at,
                manifest_hash,
            )
        )

        branch_rstyle_rows.append(
            with_common(
                {
                    "unified_rstyle_branch_result_id": f"OHLC-GTOS-UNIFIED-EXEC-RSTYLE-BRANCH-{index:05d}",
                    "branch_queue_id": branch_id,
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "primary_export_family": family,
                    "target_stop_contract_id": system_row.get("target_stop_contract_id"),
                    "target_stop_result": system_row.get("target_stop_result") or rstyle_row.get("target_stop_result"),
                    "target_stop_result_counts": rstyle_row.get("target_stop_result_counts") or full_row.get("target_stop_result_counts"),
                    "expectancy_style_proxy": rstyle_row.get("expectancy_style_proxy"),
                    "rstyle_proxy_all_components": rstyle_row.get("rstyle_proxy_all_components"),
                    "rstyle_lower_mean": full_row.get("rstyle_lower_mean"),
                    "rstyle_midpoint_mean": rstyle_midpoint,
                    "rstyle_upper_mean": full_row.get("rstyle_upper_mean"),
                    "rstyle_proxy_signal_class": decision["rstyle_proxy_signal_class"],
                    "branch_result_class": full_row.get("branch_result_class") or rstyle_row.get("branch_result_class"),
                    "sealed_or_proxy_outcome_status": full_row.get("sealed_or_proxy_outcome_status"),
                    "cost_sensitivity": rstyle_row.get("cost_sensitivity") or full_row.get("cost_sensitivity"),
                    "pass_control_delta": full_row.get("pass_control_delta") or rstyle_row.get("pass_control_delta_status"),
                    "duplicate_effective_n": full_row.get("duplicate_effective_n") or rstyle_row.get("effective_n_fields"),
                    "source_confidence_status": full_row.get("source_confidence_status") or rstyle_row.get("source_confidence_status"),
                    "ambiguity_status": full_row.get("ambiguity_status") or rstyle_row.get("ambiguity_status"),
                    "exact_failure_cause": near_row.get("exact_failure_cause") or nofill_row.get("exact_failure_cause") or system_row.get("exact_failure_cause"),
                    "exact_success_cause": near_row.get("exact_success_cause") or nofill_row.get("exact_success_cause") or system_row.get("exact_success_cause"),
                    "exact_missing_geometry_or_source_reason": exact_missing_reason,
                    "unified_execution_decision": decision["unified_execution_decision"],
                    "implementation_candidate_type": decision["implementation_candidate_type"],
                },
                generated_at,
                manifest_hash,
            )
        )

        implementation_rows.append(
            with_common(
                {
                    "implementation_candidate_id": f"OHLC-GTOS-UNIFIED-EXEC-IMPL-BRANCH-{index:05d}",
                    "candidate_scope": "BRANCH_LOCAL",
                    "branch_queue_id": branch_id,
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "primary_export_family": family,
                    "implementation_candidate_type": decision["implementation_candidate_type"],
                    "unified_execution_decision": decision["unified_execution_decision"],
                    "code_surface": "src/research_infra/moonshot_unified_execution_scorer.py",
                    "builder_surface": Path(__file__).relative_to(REPO).as_posix(),
                    "input_contract": [
                        "system_transfer_branch_row",
                        "rstyle_branch_row",
                        "full_outcome_branch_row",
                        "nofill_branch_summary_row",
                        "nearmiss_branch_summary_row",
                    ],
                    "scorer_function": "classify_unified_branch_decision",
                    "same_resource_next_action": decision["unified_next_action"],
                    "exact_failure_cause": near_row.get("exact_failure_cause") or nofill_row.get("exact_failure_cause") or system_row.get("exact_failure_cause"),
                    "exact_success_cause": near_row.get("exact_success_cause") or nofill_row.get("exact_success_cause") or system_row.get("exact_success_cause"),
                    "exact_missing_geometry_or_source_reason": exact_missing_reason,
                },
                generated_at,
                manifest_hash,
            )
        )

    return branch_execution_rows, branch_rstyle_rows, implementation_rows


def build_family_symbol_session_rows(
    branch_rstyle_rows: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in branch_rstyle_rows:
        groups[(str(row.get("primary_export_family")), str(row.get("symbol")), str(row.get("route_session")))].append(row)

    output_rows: list[dict[str, Any]] = []
    for index, ((family, symbol, route_session), rows) in enumerate(sorted(groups.items()), 1):
        midpoints = [to_float(row.get("rstyle_midpoint_mean")) for row in rows]
        midpoint_values = [value for value in midpoints if value is not None]
        target_counts: Counter[str] = Counter()
        for row in rows:
            nested_counter_update(target_counts, row.get("target_stop_result_counts"))
            if not row.get("target_stop_result_counts"):
                target_counts[str(row.get("target_stop_result"))] += 1
        output_rows.append(
            with_common(
                {
                    "family_symbol_session_rstyle_id": f"OHLC-GTOS-UNIFIED-EXEC-FSS-RSTYLE-{index:04d}",
                    "primary_export_family": family,
                    "symbol": symbol,
                    "route_session": route_session,
                    "branch_rows": len(rows),
                    "rstyle_scalar_rows": len(midpoint_values),
                    "rstyle_midpoint_min": min_or_none(midpoint_values),
                    "rstyle_midpoint_mean": mean_or_none(midpoint_values),
                    "rstyle_midpoint_max": max_or_none(midpoint_values),
                    "rstyle_proxy_signal_counts": summarize_labels(rows, "rstyle_proxy_signal_class"),
                    "unified_execution_decision_counts": summarize_labels(rows, "unified_execution_decision"),
                    "implementation_candidate_type_counts": summarize_labels(rows, "implementation_candidate_type"),
                    "target_stop_result_counts": compact_counter(target_counts),
                    "source_confidence_status_counts": summarize_labels(rows, "source_confidence_status"),
                    "ambiguity_status_counts": summarize_labels(rows, "ambiguity_status"),
                    "exact_missing_reason_count": sum(1 for row in rows if row.get("exact_missing_geometry_or_source_reason")),
                },
                generated_at,
                manifest_hash,
            )
        )
    return output_rows


def build_market_gap_rows(
    market_gap_actions: list[dict[str, Any]], generated_at: str, manifest_hash: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    implementation_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    for index, row in enumerate(market_gap_actions, 1):
        decision = classify_market_gap_candidate(row)
        common_payload = {
            "market_gap_implementation_id": f"OHLC-GTOS-UNIFIED-EXEC-MARKET-GAP-{index:05d}",
            "candidate_scope": "MARKET_GAP_PRIMITIVE",
            "market_gap_combo_id": row.get("market_gap_combo_id"),
            "market_gap_action_id": row.get("market_gap_action_id"),
            "symbol": row.get("symbol"),
            "session_bucket": row.get("session_bucket"),
            "mapped_route_session": row.get("mapped_route_session"),
            "horizon_id": row.get("horizon_id"),
            "primitive_flag": row.get("primitive_flag"),
            "movement_status": row.get("movement_status"),
            "action_class": row.get("action_class"),
            "tick_context_decision": row.get("tick_context_decision"),
            "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
            "unified_execution_decision": decision["unified_execution_decision"],
            "implementation_candidate_type": decision["implementation_candidate_type"],
            "same_resource_next_action": decision["unified_next_action"],
            "market_gap_evidence_class": decision["market_gap_evidence_class"],
            "flagged_n": row.get("flagged_n"),
            "control_n": row.get("control_n"),
            "delta_mean_abs_future_change": row.get("delta_mean_abs_future_change"),
            "delta_alignment_rate": row.get("delta_alignment_rate"),
            "nofill_sidecar_status": row.get("nofill_sidecar_status"),
            "residual_transfer_class": row.get("residual_transfer_class"),
        }
        implementation_rows.append(with_common(dict(common_payload), generated_at, manifest_hash))
        candidate_rows.append(
            with_common(
                {
                    "implementation_candidate_id": f"OHLC-GTOS-UNIFIED-EXEC-IMPL-MARKET-GAP-{index:05d}",
                    "candidate_scope": "MARKET_GAP_PRIMITIVE",
                    "branch_queue_id": None,
                    "market_gap_combo_id": row.get("market_gap_combo_id"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("mapped_route_session"),
                    "horizon_id": row.get("horizon_id"),
                    "primitive_flag": row.get("primitive_flag"),
                    "implementation_candidate_type": decision["implementation_candidate_type"],
                    "unified_execution_decision": decision["unified_execution_decision"],
                    "code_surface": "src/research_infra/moonshot_unified_execution_scorer.py",
                    "builder_surface": Path(__file__).relative_to(REPO).as_posix(),
                    "input_contract": ["market_gap_primitive_action_row"],
                    "scorer_function": "classify_market_gap_candidate",
                    "same_resource_next_action": decision["unified_next_action"],
                    "exact_failure_cause": "MARKET_GAP_NOT_IN_CURRENT_386_BRANCH_DENOMINATOR",
                    "exact_success_cause": "MARKET_GAP_SUPPORTIVE_PRIMITIVE" if row.get("action_class") == "ENTRY_GEOMETRY_QUEUE" else "NO_DIRECT_SUCCESS_CAUSE_YET",
                    "exact_missing_geometry_or_source_reason": "Market-gap primitive row is outside the current branch denominator; branch-local R-style geometry is not yet built for this market/session/horizon/primitive.",
                },
                generated_at,
                manifest_hash,
            )
        )
    return implementation_rows, candidate_rows


def build_concentration_rows(
    system_rows: list[dict[str, Any]],
    market_gap_rows: list[dict[str, Any]],
    cross_base_rows: list[dict[str, Any]],
    nofill_rows: list[dict[str, Any]],
    near_rows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    current_total = len(system_rows)
    market_gap_total = len(market_gap_rows)

    current_by_symbol = Counter(row.get("symbol") for row in system_rows)
    gap_by_symbol = Counter(row.get("symbol") for row in market_gap_rows)
    full_tick_by_symbol = Counter(row.get("symbol") for row in cross_base_rows)
    nofill_direct_by_symbol = Counter(row.get("symbol") for row in nofill_rows if row.get("nofill_join_status") != "NO_DIRECT_NOFILL_CONTEXT_FOR_BRANCH_KEY")
    near_direct_by_symbol = Counter(row.get("symbol") for row in near_rows if row.get("nearmiss_join_status") != "NO_DIRECT_NEARMISS_CONTEXT_FOR_BRANCH_KEY")

    all_symbols = sorted(set(current_by_symbol) | set(gap_by_symbol) | set(full_tick_by_symbol))
    for symbol in all_symbols:
        current_rows = current_by_symbol.get(symbol, 0)
        gap_rows = gap_by_symbol.get(symbol, 0)
        full_tick_rows = full_tick_by_symbol.get(symbol, 0)
        rows.append(
            with_common(
                {
                    "concentration_transfer_test_id": f"OHLC-GTOS-UNIFIED-EXEC-CONC-{len(rows) + 1:05d}",
                    "test_axis": "SYMBOL",
                    "symbol": symbol,
                    "route_session": None,
                    "horizon_id": None,
                    "current_branch_rows": current_rows,
                    "market_gap_combo_rows": gap_rows,
                    "full_tick_transfer_rows": full_tick_rows,
                    "nofill_direct_context_rows": nofill_direct_by_symbol.get(symbol, 0),
                    "nearmiss_direct_context_rows": near_direct_by_symbol.get(symbol, 0),
                    "current_branch_share": round(current_rows / current_total, 9) if current_total else None,
                    "market_gap_share": round(gap_rows / market_gap_total, 9) if market_gap_total else None,
                    "concentration_artifact_class": concentration_artifact_class(
                        current_rows, gap_rows, full_tick_rows, current_total, market_gap_total
                    ),
                    "decision_implication": (
                        "Do not treat current GBPJPY/XAUUSD branch concentration as whole-market search coverage; "
                        "symbols with market-gap rows require expansion or explicit avoid/inverse testing."
                    ),
                },
                generated_at,
                manifest_hash,
            )
        )

    current_by_symbol_session = Counter((row.get("symbol"), row.get("route_session")) for row in system_rows)
    gap_by_symbol_session = Counter((row.get("symbol"), row.get("mapped_route_session")) for row in market_gap_rows)
    full_by_symbol_session = Counter((row.get("symbol"), row.get("session_bucket")) for row in cross_base_rows)
    symbol_session_keys = sorted(set(current_by_symbol_session) | set(gap_by_symbol_session))
    for symbol, route_session in symbol_session_keys:
        rows.append(
            with_common(
                {
                    "concentration_transfer_test_id": f"OHLC-GTOS-UNIFIED-EXEC-CONC-{len(rows) + 1:05d}",
                    "test_axis": "SYMBOL_SESSION",
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": None,
                    "current_branch_rows": current_by_symbol_session.get((symbol, route_session), 0),
                    "market_gap_combo_rows": gap_by_symbol_session.get((symbol, route_session), 0),
                    "full_tick_transfer_rows": sum(count for (sym, session_bucket), count in full_by_symbol_session.items() if sym == symbol and str(route_session or "") in str(session_bucket)),
                    "concentration_artifact_class": concentration_artifact_class(
                        current_by_symbol_session.get((symbol, route_session), 0),
                        gap_by_symbol_session.get((symbol, route_session), 0),
                        1,
                        current_total,
                        market_gap_total,
                    ),
                    "decision_implication": "Use symbol/session rows to split transferable mechanics from market-specific or missing-branch-denominator artifacts.",
                },
                generated_at,
                manifest_hash,
            )
        )

    current_by_key = Counter()
    for row in system_rows:
        symbol, session, _descriptor, horizon_id = route_parts(row.get("route_candidate_id"))
        current_by_key[(symbol, session, horizon_id)] += 1
    gap_by_key = Counter((row.get("symbol"), row.get("mapped_route_session"), row.get("horizon_id")) for row in market_gap_rows)
    full_by_key = Counter((row.get("symbol"), row.get("session_bucket"), row.get("horizon_id")) for row in cross_base_rows)
    key_set = sorted(set(current_by_key) | set(gap_by_key))
    for symbol, route_session, horizon_id in key_set:
        rows.append(
            with_common(
                {
                    "concentration_transfer_test_id": f"OHLC-GTOS-UNIFIED-EXEC-CONC-{len(rows) + 1:05d}",
                    "test_axis": "SYMBOL_SESSION_HORIZON",
                    "symbol": symbol,
                    "route_session": route_session,
                    "horizon_id": horizon_id,
                    "current_branch_rows": current_by_key.get((symbol, route_session, horizon_id), 0),
                    "market_gap_combo_rows": gap_by_key.get((symbol, route_session, horizon_id), 0),
                    "full_tick_transfer_rows": sum(
                        count
                        for (sym, session_bucket, horizon), count in full_by_key.items()
                        if sym == symbol and horizon == horizon_id and str(route_session or "") in str(session_bucket)
                    ),
                    "concentration_artifact_class": concentration_artifact_class(
                        current_by_key.get((symbol, route_session, horizon_id), 0),
                        gap_by_key.get((symbol, route_session, horizon_id), 0),
                        1,
                        current_total,
                        market_gap_total,
                    ),
                    "decision_implication": "Use symbol/session/horizon rows as the exact transfer/failure split before preserving or killing a branch family.",
                },
                generated_at,
                manifest_hash,
            )
        )

    source_root_rows = [
        ("CURRENT_386_BRANCH_DENOMINATOR", len(system_rows), sorted(set(current_by_symbol))),
        ("TICK_M15_FULL_TRANSFER_BASE", len(cross_base_rows), sorted(set(full_tick_by_symbol))),
        ("TICK_MARKET_GAP_OUTSIDE_CURRENT_BRANCH_DENOMINATOR", len(market_gap_rows), sorted(set(gap_by_symbol))),
        (
            "NOFILL_DIRECT_CONTEXT_BRANCH_KEYS",
            sum(nofill_direct_by_symbol.values()),
            sorted(symbol for symbol, count in nofill_direct_by_symbol.items() if count),
        ),
        (
            "NEARMISS_DIRECT_CONTEXT_BRANCH_KEYS",
            sum(near_direct_by_symbol.values()),
            sorted(symbol for symbol, count in near_direct_by_symbol.items() if count),
        ),
    ]
    for source_root, row_count, symbols in source_root_rows:
        rows.append(
            with_common(
                {
                    "concentration_transfer_test_id": f"OHLC-GTOS-UNIFIED-EXEC-CONC-{len(rows) + 1:05d}",
                    "test_axis": "SOURCE_ROOT",
                    "source_root": source_root,
                    "row_count": row_count,
                    "symbol_count": len(symbols),
                    "symbols": symbols,
                    "decision_implication": "Source-root coverage is preserved as a concentration-artifact control; absent branch rows are not absent market evidence.",
                },
                generated_at,
                manifest_hash,
            )
        )

    return rows


def build_scorer_spec_rows(generated_at: str, manifest_hash: str, candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_types = sorted({str(row.get("implementation_candidate_type")) for row in candidate_rows})
    rows: list[dict[str, Any]] = []
    for index, candidate_type in enumerate(candidate_types, 1):
        rows.append(
            with_common(
                {
                    "scorer_spec_id": f"OHLC-GTOS-UNIFIED-EXEC-SCORER-SPEC-{index:04d}",
                    "implementation_candidate_type": candidate_type,
                    "code_surface": "src/research_infra/moonshot_unified_execution_scorer.py",
                    "builder_surface": Path(__file__).relative_to(REPO).as_posix(),
                    "input_denominator": "386 branch rows plus 400 market-gap primitive rows where candidate_scope applies",
                    "output_decision_field": "unified_execution_decision",
                    "required_controls": [
                        "source_repair_pressure_class",
                        "execution_pressure_class",
                        "rstyle_proxy_signal_class",
                        "concentration_transfer_test",
                    ],
                    "implementation_status": "BRANCH_LOCAL_RESEARCH_SPEC_READY",
                    "promotion_status": "NO_PROMOTION_VERDICT",
                },
                generated_at,
                manifest_hash,
            )
        )
    rows.append(
        with_common(
            {
                "scorer_spec_id": f"OHLC-GTOS-UNIFIED-EXEC-SCORER-SPEC-{len(rows) + 1:04d}",
                "implementation_candidate_type": "CONCENTRATION_ARTIFACT_TEST",
                "code_surface": "src/research_infra/moonshot_unified_execution_scorer.py",
                "builder_surface": Path(__file__).relative_to(REPO).as_posix(),
                "input_denominator": "current branch rows, tick transfer base rows, market-gap rows, no-fill context, and near-miss context",
                "output_decision_field": "concentration_artifact_class",
                "required_controls": ["symbol", "symbol_session", "symbol_session_horizon", "source_root"],
                "implementation_status": "BRANCH_LOCAL_RESEARCH_SPEC_READY",
                "promotion_status": "NO_PROMOTION_VERDICT",
            },
            generated_at,
            manifest_hash,
        )
    )
    return rows


def main() -> int:
    generated_at = now_utc()
    source_paths = [
        SYSTEM_TRANSFER_RESULT,
        SYSTEM_TRANSFER_BRANCH,
        SYSTEM_TRANSFER_MARKET_SESSION,
        RSTYLE_RESULT,
        RSTYLE_BRANCH,
        FULL_RESULT,
        FULL_BRANCH,
        NOFILL_RESULT,
        NOFILL_BRANCH,
        NEARMISS_RESULT,
        NEARMISS_BRANCH,
        TICK_CONTEXT_RESULT,
        TICK_BRANCH_SUMMARY,
        TICK_MARKET_GAP,
        CROSS_BASE,
        MARKET_GAP_RESULT,
        MARKET_GAP_COMBO,
        MARKET_GAP_ACTION,
        MARKET_GAP_KEY,
        MARKET_GAP_SYMBOL_SESSION,
        REPO / "src/research_infra/moonshot_unified_execution_scorer.py",
    ]
    source_manifest, manifest_hash = source_manifest_rows(source_paths, generated_at)

    system_result = read_json(SYSTEM_TRANSFER_RESULT)
    rstyle_result = read_json(RSTYLE_RESULT)
    full_result = read_json(FULL_RESULT)
    nofill_result = read_json(NOFILL_RESULT)
    near_result = read_json(NEARMISS_RESULT)
    tick_context_result = read_json(TICK_CONTEXT_RESULT)
    market_gap_result = read_json(MARKET_GAP_RESULT)

    system_rows = read_jsonl(SYSTEM_TRANSFER_BRANCH)
    rstyle_rows = read_jsonl(RSTYLE_BRANCH)
    full_rows = read_jsonl(FULL_BRANCH)
    nofill_rows = read_jsonl(NOFILL_BRANCH)
    near_rows = read_jsonl(NEARMISS_BRANCH)
    tick_summary_rows = read_jsonl(TICK_BRANCH_SUMMARY)
    cross_base_rows = read_jsonl(CROSS_BASE)
    market_gap_combo_rows = read_jsonl(MARKET_GAP_COMBO)
    market_gap_action_rows = read_jsonl(MARKET_GAP_ACTION)

    branch_execution_rows, branch_rstyle_rows, implementation_rows = build_branch_rows(
        system_rows,
        by_branch(rstyle_rows),
        by_branch(full_rows),
        by_branch(nofill_rows),
        by_branch(near_rows),
        generated_at,
        manifest_hash,
    )
    family_symbol_session_rows = build_family_symbol_session_rows(branch_rstyle_rows, generated_at, manifest_hash)
    market_gap_implementation_rows, market_gap_candidate_rows = build_market_gap_rows(
        market_gap_action_rows, generated_at, manifest_hash
    )
    implementation_rows.extend(market_gap_candidate_rows)
    concentration_rows = build_concentration_rows(
        system_rows,
        market_gap_combo_rows,
        cross_base_rows,
        nofill_rows,
        near_rows,
        generated_at,
        manifest_hash,
    )
    scorer_spec_rows = build_scorer_spec_rows(generated_at, manifest_hash, implementation_rows)

    bucket_sources = {
        "unified_execution_decision": Counter(row["unified_execution_decision"] for row in branch_execution_rows),
        "implementation_candidate_type": Counter(row["implementation_candidate_type"] for row in implementation_rows),
        "branch_symbol": Counter(row["symbol"] for row in branch_execution_rows),
        "branch_route_session": Counter(row["route_session"] for row in branch_execution_rows),
        "branch_primary_export_family": Counter(row["primary_export_family"] for row in branch_execution_rows),
        "rstyle_proxy_signal_class": Counter(row["rstyle_proxy_signal_class"] for row in branch_execution_rows),
        "source_repair_pressure_class": Counter(row["source_repair_pressure_class"] for row in branch_execution_rows),
        "execution_pressure_class": Counter(row["execution_pressure_class"] for row in branch_execution_rows),
        "market_gap_unified_execution_decision": Counter(row["unified_execution_decision"] for row in market_gap_implementation_rows),
        "concentration_artifact_class": Counter(row["concentration_artifact_class"] for row in concentration_rows if row.get("concentration_artifact_class")),
    }
    bucket_rows: list[dict[str, Any]] = []
    for category, counter in sorted(bucket_sources.items()):
        for value, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                with_common(
                    {
                        "unified_execution_bucket_id": f"OHLC-GTOS-UNIFIED-EXEC-BUCKET-{len(bucket_rows) + 1:05d}",
                        "bucket_category": category,
                        "bucket_value": str(value),
                        "row_count": int(count),
                    },
                    generated_at,
                    manifest_hash,
                )
            )

    question_rows = [
        {
            "question_id": "OHLC-GTOS-UNIFIED-EXEC-QUESTION-001",
            "question": "What is the unified keep/kill/redesign/implement decision for every branch?",
            "answer_route": "Use BRANCH_EXECUTION_LEDGER; it preserves all 386 branch decisions with source, execution, and R-style proxy classes.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-EXEC-QUESTION-002",
            "question": "What exact/proxy R-style result is mechanically available by branch and family/symbol/session?",
            "answer_route": "Use BRANCH_RSTYLE_RESULT_LEDGER and FAMILY_SYMBOL_SESSION_RSTYLE_LEDGER; exact broker R remains explicitly unavailable in this evidence class.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-EXEC-QUESTION-003",
            "question": "Which branch-local code/spec candidates are ready for same-resource implementation work?",
            "answer_route": "Use IMPLEMENTATION_CANDIDATE_LEDGER and SCORER_SPEC_LEDGER; they include 386 branch candidates plus 400 market-gap candidates.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-EXEC-QUESTION-004",
            "question": "Is GBPJPY/XAUUSD concentration real mechanism, data artifact, or both?",
            "answer_route": "Use CONCENTRATION_TRANSFER_TEST_LEDGER; it shows current branch concentration versus tick market-gap coverage across symbols, sessions, horizons, and source roots.",
        },
        {
            "question_id": "OHLC-GTOS-UNIFIED-EXEC-QUESTION-005",
            "question": "Which market-gap primitive rows directly change implementation decisions?",
            "answer_route": "Use MARKET_GAP_IMPLEMENTATION_LEDGER; it converts 400 market-gap rows into source-expansion, entry-geometry, and avoid/inverse implementation candidates.",
        },
    ]
    for row in question_rows:
        with_common(row, generated_at, manifest_hash)

    counts = {
        "input_system_transfer_branch_rows": len(system_rows),
        "input_rstyle_branch_rows": len(rstyle_rows),
        "input_full_outcome_branch_rows": len(full_rows),
        "input_nofill_branch_rows": len(nofill_rows),
        "input_nearmiss_branch_rows": len(near_rows),
        "input_tick_branch_summary_rows": len(tick_summary_rows),
        "input_cross_base_rows": len(cross_base_rows),
        "input_market_gap_combo_rows": len(market_gap_combo_rows),
        "input_market_gap_action_rows": len(market_gap_action_rows),
        "branch_execution_rows": len(branch_execution_rows),
        "branch_rstyle_result_rows": len(branch_rstyle_rows),
        "family_symbol_session_rstyle_rows": len(family_symbol_session_rows),
        "implementation_candidate_rows": len(implementation_rows),
        "branch_implementation_candidate_rows": len([row for row in implementation_rows if row["candidate_scope"] == "BRANCH_LOCAL"]),
        "market_gap_implementation_candidate_rows": len([row for row in implementation_rows if row["candidate_scope"] == "MARKET_GAP_PRIMITIVE"]),
        "concentration_transfer_test_rows": len(concentration_rows),
        "market_gap_implementation_rows": len(market_gap_implementation_rows),
        "scorer_spec_rows": len(scorer_spec_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(source_manifest),
    }

    branch_midpoints = [
        to_float(row.get("rstyle_midpoint_mean"))
        for row in branch_execution_rows
        if to_float(row.get("rstyle_midpoint_mean")) is not None
    ]
    result = {
        "artifact": RESULT_PATH.name,
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_EXECUTION_DECISION",
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_completion": True,
        "counts": counts,
        "upstream_counts": {
            "system_transfer": system_result.get("counts", {}),
            "rstyle": rstyle_result.get("counts", {}),
            "full_outcome": full_result.get("counts", {}),
            "nofill_transfer": nofill_result.get("counts", {}),
            "nearmiss_transfer": near_result.get("counts", {}),
            "tick_context": tick_context_result.get("counts", {}),
            "market_gap": market_gap_result.get("counts", {}),
        },
        "bucket_distributions": {category: compact_counter(counter) for category, counter in sorted(bucket_sources.items())},
        "rstyle_midpoint_stats": {
            "scalar_rows": len(branch_midpoints),
            "min": min_or_none(branch_midpoints),
            "mean": mean_or_none(branch_midpoints),
            "max": max_or_none(branch_midpoints),
        },
        "concentration_decision": {
            "current_branch_symbols": compact_counter(Counter(row.get("symbol") for row in system_rows)),
            "market_gap_symbols": compact_counter(Counter(row.get("symbol") for row in market_gap_combo_rows)),
            "full_tick_transfer_symbols": compact_counter(Counter(row.get("symbol") for row in cross_base_rows)),
            "verdict": (
                "GBPJPY/XAUUSD concentration is real in the current 386 branch queue but is also a denominator "
                "artifact at the tick-transfer coverage layer: 300/400 market-gap primitive combos are outside "
                "GBPJPY/XAUUSD, and the unified scorer must expand or explicitly kill/avoid those rows rather "
                "than treating current branch concentration as full search coverage."
            ),
        },
        "system_decision": {
            "system_recommendation": (
                "UNIFIED_EXECUTION_DECISION_RESULT: use the 386 branch execution ledger for branch-local "
                "keep/kill/redesign/implement decisions, carry 400 market-gap primitive implementation candidates "
                "as denominator-expansion work, and treat GBPJPY/XAUUSD concentration as branch-queue evidence "
                "plus tick-coverage artifact until expanded source/entry/avoid rows are scored."
            ),
            "branch_execution_decision_counts": compact_counter(Counter(row["unified_execution_decision"] for row in branch_execution_rows)),
            "market_gap_decision_counts": compact_counter(Counter(row["unified_execution_decision"] for row in market_gap_implementation_rows)),
        },
        "source_manifest_hash": manifest_hash,
    }

    outputs = [
        (BRANCH_EXECUTION_LEDGER, branch_execution_rows),
        (BRANCH_RSTYLE_LEDGER, branch_rstyle_rows),
        (FAMILY_SYMBOL_SESSION_RSTYLE_LEDGER, family_symbol_session_rows),
        (IMPLEMENTATION_CANDIDATE_LEDGER, implementation_rows),
        (CONCENTRATION_TRANSFER_TEST_LEDGER, concentration_rows),
        (MARKET_GAP_IMPLEMENTATION_LEDGER, market_gap_implementation_rows),
        (SCORER_SPEC_LEDGER, scorer_spec_rows),
        (BUCKET_LEDGER, bucket_rows),
        (QUESTION_LEDGER, question_rows),
        (SOURCE_MANIFEST_LEDGER, source_manifest),
    ]
    for path, rows in outputs:
        write_jsonl(path, rows)
    write_text(RESULT_PATH, json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_text(
        SUMMARY_PATH,
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Branch System Transfer Unified Execution Decision",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                f"- Branch execution rows: `{len(branch_execution_rows)}`",
                f"- Branch R-style result rows: `{len(branch_rstyle_rows)}`",
                f"- Family/symbol/session R-style rows: `{len(family_symbol_session_rows)}`",
                f"- Implementation candidate rows: `{len(implementation_rows)}`",
                f"- Market-gap implementation rows: `{len(market_gap_implementation_rows)}`",
                f"- Concentration transfer test rows: `{len(concentration_rows)}`",
                "",
                "Core concentration result: current branch rows are concentrated in GBPJPY/XAUUSD, while the tick-transfer market-gap denominator preserves available rows across seven symbols. The next concrete work is source expansion, entry-geometry scoring, avoid/inverse scoring, and branch-local scorer execution, not another transfer-only packet.",
            ]
        )
        + "\n",
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
                "type": "branch_system_transfer_unified_execution_decision",
                "generated_utc": generated_at,
                "counts": result["counts"],
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    manifest["safe_flags"] = SAFE_FLAGS
    write_text(OUTPUT_MANIFEST, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with SPRINT_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "timestamp_utc": generated_at,
                    "event_type": "branch_system_transfer_unified_execution_decision_built",
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
    print(json.dumps({"ok": True, "counts": counts, "result": str(RESULT_PATH)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
