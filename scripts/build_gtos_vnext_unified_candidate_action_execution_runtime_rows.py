#!/usr/bin/env python3
"""Build runtime rows for unified candidate action-execution evidence."""

from __future__ import annotations

import os
import argparse
import hashlib
import json
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
MOONSHOT_ROUTE = Path(
    r"research/science_program_2026_05/"
    r"06_outcome_testing/weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
DATE = "2026-05-18"
WAVE_ID = "WAVE_UNIFIED_CANDIDATE_ACTION_EXECUTION_RUNTIME"
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_UNIFIED_CANDIDATE_ACTION_EXECUTION_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_UNIFIED_CANDIDATE_ACTION_EXECUTION_RUNTIME_SUMMARY_{DATE}.json"
)

BRANCH_ACTION_AGGREGATE_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_"
    "BRANCH_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
)
BRANCH_AVOID_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_"
    "BRANCH_AVOID_OR_REDIRECT_LEDGER_2026-05-17.jsonl"
)
BRANCH_FILLABILITY_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_"
    "BRANCH_FILLABILITY_REDESIGN_LEDGER_2026-05-17.jsonl"
)
BRANCH_MARKET_ENTRY_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_"
    "BRANCH_MARKET_ENTRY_COMPARATOR_LEDGER_2026-05-17.jsonl"
)
BRANCH_PROVENANCE_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_"
    "BRANCH_PROVENANCE_LEDGER_2026-05-17.jsonl"
)
MARKET_GAP_AVOID_CONTROL_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_"
    "MARKET_GAP_AVOID_INVERSE_CONTROL_LEDGER_2026-05-17.jsonl"
)
MARKET_GAP_AVOID_POLICY_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_"
    "MARKET_GAP_AVOID_INVERSE_POLICY_VARIANT_LEDGER_2026-05-17.jsonl"
)
MARKET_GAP_ENTRY_GEOMETRY_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_"
    "MARKET_GAP_ENTRY_GEOMETRY_CHALLENGER_LEDGER_2026-05-17.jsonl"
)
MARKET_GAP_SOURCE_EXPANSION_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_"
    "MARKET_GAP_SOURCE_EXPANSION_REQUIREMENT_LEDGER_2026-05-17.jsonl"
)
CONCENTRATION_RESTRESS_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_"
    "CONCENTRATION_ARTIFACT_RESTRESS_LEDGER_2026-05-17.jsonl"
)
SCORER_SPEC_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_"
    "SCORER_SPEC_CHANGE_LEDGER_2026-05-17.jsonl"
)
SYMBOL_SESSION_ACTION_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_"
    "SYMBOL_SESSION_ACTION_LEDGER_2026-05-17.jsonl"
)

PRIMARY_SOURCE_NAMES = (
    BRANCH_AVOID_SOURCE,
    BRANCH_FILLABILITY_SOURCE,
    BRANCH_MARKET_ENTRY_SOURCE,
    BRANCH_PROVENANCE_SOURCE,
    MARKET_GAP_AVOID_CONTROL_SOURCE,
    MARKET_GAP_AVOID_POLICY_SOURCE,
    MARKET_GAP_ENTRY_GEOMETRY_SOURCE,
    MARKET_GAP_SOURCE_EXPANSION_SOURCE,
    CONCENTRATION_RESTRESS_SOURCE,
    SCORER_SPEC_SOURCE,
    SYMBOL_SESSION_ACTION_SOURCE,
)
SUPPORT_SOURCE_NAMES = (
    BRANCH_ACTION_AGGREGATE_SOURCE,
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_BUCKET_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_QUESTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_RESULT_2026-05-17.json",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_ACTION_EXECUTION_SUMMARY_2026-05-17.md",
)
ALL_SOURCE_NAMES = PRIMARY_SOURCE_NAMES + SUPPORT_SOURCE_NAMES

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "primitive",
    "side",
    "entry_variant",
    "target_stop_order_class",
    "source_component",
)
SIDE_OPTIONAL_COMPONENTS = {
    "unified_candidate_action_market_gap_avoid_inverse",
    "unified_candidate_action_market_gap_entry_geometry",
    "unified_candidate_action_source_expansion",
    "unified_candidate_action_concentration_restress",
    "unified_candidate_action_symbol_session",
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return False
    return str(value).strip().casefold() in {"1", "true", "yes", "y", "on"}


def _long_path(path: Path) -> str:
    text = str(path.resolve())
    if os.name == "nt" and len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


@lru_cache(maxsize=None)
def _sha256_file_cached(path_text: str) -> str:
    digest = hashlib.sha256()
    with open(_long_path(Path(path_text)), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_file_cached(str(path))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _path_text(path: Path) -> str:
    try:
        if path.is_relative_to(REPO_ROOT):
            return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        pass
    return str(path).replace("\\", "/")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(_long_path(path), "r", encoding="utf-8-sig", newline="") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _source_path(name: str) -> Path:
    return MOONSHOT_ROUTE / name


def _line_count_or_one(path: Path) -> int:
    if path.suffix.lower() == ".json":
        return 1
    with open(_long_path(path), "rb") as handle:
        return sum(1 for line in handle if line.strip())


def _source_kind(path: Path) -> str:
    upper = path.name.upper()
    if "BRANCH_AVOID_OR_REDIRECT" in upper:
        return "branch_avoid_or_redirect"
    if "BRANCH_FILLABILITY_REDESIGN" in upper:
        return "branch_fillability_redesign"
    if "BRANCH_MARKET_ENTRY_COMPARATOR" in upper:
        return "branch_market_entry_comparator"
    if "BRANCH_PROVENANCE" in upper:
        return "branch_provenance"
    if "MARKET_GAP_AVOID_INVERSE" in upper:
        return "market_gap_avoid_inverse"
    if "MARKET_GAP_ENTRY_GEOMETRY" in upper:
        return "market_gap_entry_geometry"
    if "MARKET_GAP_SOURCE_EXPANSION" in upper:
        return "market_gap_source_expansion"
    if "CONCENTRATION_ARTIFACT_RESTRESS" in upper:
        return "concentration_restress"
    if "SCORER_SPEC_CHANGE" in upper:
        return "scorer_spec_change"
    if "SYMBOL_SESSION_ACTION" in upper:
        return "symbol_session_action"
    return "support"


def _route_parts(row: dict[str, Any]) -> tuple[str, str, str, str]:
    raw = _norm(row.get("route_candidate_id") or row.get("market_gap_combo_id"))
    parts = raw.split("|") if raw else []
    symbol = _norm(row.get("symbol")) or (parts[0] if len(parts) > 0 else "")
    session = (
        _norm(row.get("route_session"))
        or _norm(row.get("session_bucket"))
        or (parts[1] if len(parts) > 1 else "")
    )
    primitive = _norm(row.get("primitive_flag")) or (parts[2] if len(parts) > 2 else "")
    horizon = _norm(row.get("horizon_id")) or (parts[3] if len(parts) > 3 else "")
    return symbol, session, primitive, horizon


def _target_stop_order_class(row: dict[str, Any]) -> str:
    contract = _norm(row.get("target_stop_contract_id"))
    if contract:
        return contract
    result = _norm(row.get("target_stop_result"))
    if result:
        return result
    return ""


def _score_field(row: dict[str, Any]) -> tuple[str, float] | None:
    for key in ("candidate_score_proxy", "candidate_score_proxy_mean"):
        value = _to_float(row.get(key))
        if value is not None:
            return key, value
    return None


def _text_blob(row: dict[str, Any]) -> str:
    keys = (
        "action_execution_class",
        "action_execution_priority",
        "action_class",
        "avoid_inverse_execution_decision",
        "candidate_next_action",
        "candidate_score_class",
        "candidate_score_band",
        "concentration_decision",
        "implementation_candidate_type",
        "keep_kill_redesign_implement_decision",
        "movement_status",
        "policy_variant_decision",
        "policy_variant_type",
        "restress_execution_decision",
        "source_expansion_execution_decision",
        "symbol_session_action",
        "unified_execution_decision",
    )
    return " ".join(_norm(row.get(key)).upper() for key in keys)


def _decision_shape(
    row: dict[str, Any],
    *,
    source_kind: str,
) -> tuple[str, str, str, str, str, str, str]:
    blob = _text_blob(row)
    if source_kind == "branch_avoid_or_redirect":
        return (
            "AVOID",
            "unified_candidate_action_branch_avoid_filter",
            "unified_candidate_action_execution_avoid_filter",
            "UNIFIED_CANDIDATE_ACTION_EXECUTION_AVOID_FILTER",
            "execution_adjacent_avoid_filter",
            "unified_candidate_action_avoid_guard",
            "execution_adjacent_candidate_action_filter",
        )
    if source_kind == "branch_fillability_redesign":
        if "AVOID_FIRST" in blob or "LOW_PRIORITY_OR_AVOID" in blob:
            return (
                "AVOID",
                "unified_candidate_action_fillability_redesign",
                "unified_candidate_action_execution_avoid_filter",
                "UNIFIED_CANDIDATE_ACTION_EXECUTION_FILLABILITY_AVOID",
                "execution_adjacent_avoid_filter",
                "unified_candidate_action_avoid_guard",
                "execution_adjacent_candidate_action_filter",
            )
        if "REPAIR_FIRST" in blob:
            return (
                "MIXED",
                "unified_candidate_action_fillability_redesign",
                "unified_candidate_action_execution_source_repair_guard",
                "SOURCE_REPAIR_FOR_EXACT_R",
                "source_repair_proof",
                "source_repair_execution_plan",
                "execution_adjacent_candidate_action_source_repair",
            )
        return (
            "MIXED",
            "unified_candidate_action_fillability_redesign",
            "unified_candidate_action_execution_redesign_guard",
            "UNIFIED_CANDIDATE_ACTION_EXECUTION_REDESIGN_GUARD",
            "context_guard_input",
            "context_guard_input",
            "execution_adjacent_candidate_action_redesign",
        )
    if source_kind == "branch_market_entry_comparator":
        if "REPAIR_FIRST" in blob:
            return (
                "MIXED",
                "unified_candidate_action_market_entry_comparator",
                "unified_candidate_action_execution_source_repair_guard",
                "SOURCE_REPAIR_FOR_EXACT_R",
                "source_repair_proof",
                "source_repair_execution_plan",
                "execution_adjacent_candidate_action_source_repair",
            )
        return (
            "FOLLOW",
            "unified_candidate_action_market_entry_comparator",
            "unified_candidate_action_execution_market_entry_follow",
            "UNIFIED_CANDIDATE_ACTION_EXECUTION_MARKET_ENTRY_CHALLENGER",
            "unified_candidate_action_market_entry",
            "unified_candidate_action_market_entry_follow",
            "execution_adjacent_market_entry_challenger",
        )
    if source_kind == "branch_provenance":
        return (
            "MIXED",
            "unified_candidate_action_provenance_guard",
            "unified_candidate_action_execution_context_guard",
            "UNIFIED_CANDIDATE_ACTION_EXECUTION_PROVENANCE_GUARD",
            "context_guard_input",
            "context_guard_input",
            "execution_adjacent_candidate_action_provenance",
        )
    if source_kind == "market_gap_avoid_inverse":
        return (
            "AVOID",
            "unified_candidate_action_market_gap_avoid_inverse",
            "unified_candidate_action_execution_avoid_filter",
            "UNIFIED_CANDIDATE_ACTION_EXECUTION_MARKET_GAP_AVOID_INVERSE",
            "execution_adjacent_avoid_filter",
            "unified_candidate_action_avoid_guard",
            "execution_adjacent_market_gap_avoid_inverse",
        )
    if source_kind == "market_gap_entry_geometry":
        return (
            "FOLLOW",
            "unified_candidate_action_market_gap_entry_geometry",
            "unified_candidate_action_execution_entry_geometry_follow",
            "UNIFIED_CANDIDATE_ACTION_EXECUTION_ENTRY_GEOMETRY_CHALLENGER",
            "unified_candidate_action_entry_geometry",
            "unified_candidate_action_entry_geometry_follow",
            "execution_adjacent_entry_geometry_challenger",
        )
    if source_kind == "market_gap_source_expansion":
        return (
            "MIXED",
            "unified_candidate_action_source_expansion",
            "unified_candidate_action_execution_source_acquisition_guard",
            "UNIFIED_CANDIDATE_ACTION_SOURCE_ACQUISITION_REQUIRED",
            "source_acquisition_required",
            "unified_candidate_action_source_acquisition_guard",
            "execution_adjacent_source_acquisition_guard",
        )
    if source_kind == "concentration_restress":
        return (
            "MIXED",
            "unified_candidate_action_concentration_restress",
            "unified_candidate_action_execution_source_acquisition_guard",
            "UNIFIED_CANDIDATE_ACTION_SOURCE_ACQUISITION_REQUIRED",
            "source_acquisition_required",
            "unified_candidate_action_source_acquisition_guard",
            "execution_adjacent_concentration_restress_guard",
        )
    if source_kind == "symbol_session_action":
        return (
            "MIXED",
            "unified_candidate_action_symbol_session",
            "unified_candidate_action_execution_context_guard",
            "UNIFIED_CANDIDATE_ACTION_EXECUTION_SYMBOL_SESSION_CONTEXT",
            "context_guard_input",
            "context_guard_input",
            "execution_adjacent_symbol_session_action_context",
        )
    return (
        "MIXED",
        "unified_candidate_action_scorer_spec",
        "unified_candidate_action_execution_context_guard",
        "UNIFIED_CANDIDATE_ACTION_EXECUTION_SCORER_SPEC",
        "context_guard_input",
        "context_guard_input",
        "execution_adjacent_scorer_spec_context",
    )


def _proxy_r_class(row: dict[str, Any], decision: str) -> str:
    score_item = _score_field(row)
    score = score_item[1] if score_item else None
    if decision == "AVOID":
        return "STRONG_NEGATIVE_PROXY_R"
    if decision == "FOLLOW":
        if score is not None and score >= 0.35:
            return "STRONG_POSITIVE_PROXY_R"
        return "POSITIVE_PROXY_R"
    return ""


def _metric_from_scalar(value: float, source_field: str) -> dict[str, Any]:
    return {
        "sum": value,
        "mean": value,
        "count": 1,
        "match_rows_with_metric": 1,
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _metrics(row: dict[str, Any], decision: str) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {
        "effective_n": _metric_from_scalar(1.0, "runtime_row")
    }
    score_item = _score_field(row)
    if score_item is None:
        if decision == "AVOID":
            metrics["proxy_score"] = _metric_from_scalar(-0.1, "avoid_filter_proxy")
            metrics["stress_simulated_r"] = _metric_from_scalar(
                -0.1,
                "avoid_filter_proxy",
            )
        return metrics
    field, score = score_item
    if decision == "AVOID":
        score = -abs(score)
    if decision == "MIXED":
        metrics["proxy_score"] = _metric_from_scalar(score, field)
        return metrics
    metrics["proxy_score"] = _metric_from_scalar(score, field)
    metrics["cost_adjusted_simulated_r"] = _metric_from_scalar(score, field)
    metrics["stress_simulated_r"] = _metric_from_scalar(score, field)
    return metrics


def _source_row_id(row: dict[str, Any], path: Path, line_no: int) -> str:
    for key in (
        "branch_action_execution_id",
        "avoid_inverse_control_id",
        "avoid_inverse_policy_variant_id",
        "entry_geometry_challenger_id",
        "source_expansion_requirement_id",
        "concentration_artifact_restress_id",
        "scorer_spec_change_id",
        "symbol_session_action_id",
        "market_gap_action_id",
        "branch_queue_id",
        "route_candidate_id",
        "source_row_id",
    ):
        value = _norm(row.get(key))
        if value:
            return value
    return f"{path.name}:{line_no}"


def _runtime_row(
    row: dict[str, Any],
    *,
    line_no: int,
    path: Path,
    source_kind: str,
) -> dict[str, Any]:
    decision, component, action_class, evidence_class, group, role, surface = (
        _decision_shape(row, source_kind=source_kind)
    )
    symbol, session, primitive, horizon = _route_parts(row)
    side = _norm(row.get("side"))
    entry_variant = _norm(row.get("entry_variant"))
    target_stop = _target_stop_order_class(row)
    source_row_id = _source_row_id(row, path, line_no)
    runtime_row_id = (
        f"unified_candidate_action_execution:{source_kind}:{line_no}:"
        f"{_sha256_text(source_row_id)[:16]}"
    )
    event_scope = {
        "symbol": symbol,
        "source_symbol": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
        "market": symbol,
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": session,
        "horizon_id": horizon,
        "primitive": primitive,
        "side": side,
        "entry_variant": entry_variant,
        "target_stop_order_class": target_stop,
        "route_family": "numeric_router",
        "source_component": component,
    }
    event_scope = {key: value for key, value in event_scope.items() if value}
    side_optional = component in SIDE_OPTIONAL_COMPONENTS
    payload = {
        "unified_candidate_action_execution_runtime_row_id": runtime_row_id,
        "row_key": runtime_row_id,
        "source_row_id": source_row_id,
        "source_name": "gtos_vnext_unified_candidate_action_execution_wave",
        "evidence_family": "gtos_vnext_unified_candidate_action_execution",
        "route_family": "numeric_router",
        "source_component": component,
        "action_class": action_class,
        "review_action": decision,
        "r_evidence_class": evidence_class,
        "source_group": group,
        "source_role": role,
        "system_surface": surface,
        "event_scope": event_scope,
        "symbol": symbol,
        "source_symbol": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
        "market": symbol,
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": session,
        "horizon_id": horizon,
        "primitive": primitive,
        "side": side,
        "entry_variant": entry_variant,
        "target_stop_order_class": target_stop,
        "source_bound": bool(symbol and session and component and (side or side_optional)),
        "source_path": _path_text(path),
        "source_file_sha256": _sha256_file(path),
        "source_line_no": line_no,
        "source_kind": source_kind,
        "source_manifest_hash": _norm(row.get("source_manifest_hash")),
        "route_candidate_id": _norm(row.get("route_candidate_id")),
        "branch_queue_id": _norm(row.get("branch_queue_id")),
        "source_market_gap_combo_id": _norm(row.get("market_gap_combo_id")),
        "target_stop_contract_id": _norm(row.get("target_stop_contract_id")),
        "target_stop_result": _norm(row.get("target_stop_result")),
        "candidate_score_class": _norm(row.get("candidate_score_class")),
        "candidate_score_band": _norm(row.get("candidate_score_band")),
        "candidate_next_action": _norm(row.get("candidate_next_action")),
        "action_execution_class": _norm(row.get("action_execution_class")),
        "action_execution_priority": _norm(row.get("action_execution_priority")),
        "unified_execution_decision": _norm(row.get("unified_execution_decision")),
        "keep_kill_redesign_implement_decision": _norm(
            row.get("keep_kill_redesign_implement_decision")
        ),
        "implementation_candidate_type": _norm(row.get("implementation_candidate_type")),
        "execution_pressure_class": _norm(row.get("execution_pressure_class")),
        "source_repair_pressure_class": _norm(row.get("source_repair_pressure_class")),
        "movement_status": _norm(row.get("movement_status")),
        "nofill_sidecar_status": _norm(row.get("nofill_sidecar_status")),
        "policy_variant_type": _norm(row.get("policy_variant_type")),
        "policy_variant_decision": _norm(row.get("policy_variant_decision")),
        "source_expansion_execution_decision": _norm(
            row.get("source_expansion_execution_decision")
        ),
        "additional_flagged_rows_needed_for_n20": _norm(
            row.get("additional_flagged_rows_needed_for_n20")
        ),
        "restress_execution_decision": _norm(row.get("restress_execution_decision")),
        "concentration_artifact_class": _norm(row.get("concentration_artifact_class")),
        "symbol_session_action": _norm(row.get("symbol_session_action")),
        "scorer_spec_action_execution_status": _norm(
            row.get("action_execution_status")
        ),
        "code_surface": _norm(row.get("code_surface")),
        "not_completion": _truthy(row.get("not_completion")),
        "proxy_r_class": _proxy_r_class(row, decision),
        "r_metrics": _metrics(row, decision),
    }
    return {key: value for key, value in payload.items() if value not in ("", None)}


def build_runtime_rows() -> list[dict[str, Any]]:
    runtime_rows: list[dict[str, Any]] = []
    for name in PRIMARY_SOURCE_NAMES:
        path = _source_path(name)
        source_kind = _source_kind(path)
        for line_no, row in enumerate(_read_jsonl(path), start=1):
            runtime_rows.append(
                _runtime_row(
                    row,
                    line_no=line_no,
                    path=path,
                    source_kind=source_kind,
                )
            )
    return runtime_rows


def _coverage(rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    coverage_fields = {
        "symbols": "symbol",
        "source_symbols": "source_symbol",
        "markets": "market",
        "timeframes": "timeframe",
        "sessions": "route_session",
        "horizons": "horizon_id",
        "primitives": "primitive",
        "sides": "side",
        "entry_variants": "entry_variant",
        "target_stop_order_classes": "target_stop_order_class",
        "source_components": "source_component",
        "action_classes": "action_class",
    }
    coverage: dict[str, dict[str, int]] = {}
    blanks: Counter[str] = Counter()
    for label, field in coverage_fields.items():
        counter: Counter[str] = Counter()
        for row in rows:
            value = _norm(row.get(field) or row.get("event_scope", {}).get(field))
            if value:
                counter[value] += 1
            else:
                blanks[field] += 1
        coverage[label] = dict(sorted(counter.items()))
    for field in ANCHOR_FIELDS:
        blanks.setdefault(field, 0)
    return coverage, dict(sorted(blanks.items()))


def build_summary(runtime_rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_artifacts: list[dict[str, Any]] = []
    wave_source_rows = 0
    for name in ALL_SOURCE_NAMES:
        path = _source_path(name)
        exists = path.exists() or Path(_long_path(path)).exists()
        rows = _line_count_or_one(path) if exists else 0
        wave_source_rows += rows
        runtime_rows_read = rows if name in PRIMARY_SOURCE_NAMES else 0
        source_artifacts.append(
            {
                "path": _path_text(path),
                "name": name,
                "sha256_or_git_blob": _sha256_file(path) if exists else "",
                "rows": rows,
                "runtime_rows_read": runtime_rows_read,
                "source_role": (
                    "primary_runtime_rows"
                    if name in PRIMARY_SOURCE_NAMES
                    else "supporting_or_partition_aggregate_rows"
                ),
                "missing_or_broken": not exists,
            }
        )
    coverage, blank_anchors = _coverage(runtime_rows)
    return {
        "schema_version": "gtos_vnext_unified_candidate_action_execution_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(runtime_rows),
        "runtime_source_rows_represented": sum(
            int(item["runtime_rows_read"]) for item in source_artifacts
        ),
        "wave_source_rows_counted": wave_source_rows,
        "source_artifacts": source_artifacts,
        "decision_counts": dict(sorted(Counter(row["review_action"] for row in runtime_rows).items())),
        "source_component_counts": dict(
            sorted(Counter(row["source_component"] for row in runtime_rows).items())
        ),
        "source_role_counts": dict(
            sorted(Counter(row["source_role"] for row in runtime_rows).items())
        ),
        "source_group_counts": dict(
            sorted(Counter(row["source_group"] for row in runtime_rows).items())
        ),
        "system_surface_counts": dict(
            sorted(Counter(row["system_surface"] for row in runtime_rows).items())
        ),
        "r_evidence_class_counts": dict(
            sorted(Counter(row["r_evidence_class"] for row in runtime_rows).items())
        ),
        "action_class_counts": dict(
            sorted(Counter(row["action_class"] for row in runtime_rows).items())
        ),
        "route_family_counts": dict(
            sorted(Counter(row["route_family"] for row in runtime_rows).items())
        ),
        "source_kind_counts": dict(
            sorted(Counter(row["source_kind"] for row in runtime_rows).items())
        ),
        "coverage_counts": coverage,
        "blank_anchor_counts": blank_anchors,
        "runtime_rows_with_event_scope": sum(1 for row in runtime_rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in runtime_rows if not row.get("event_scope")),
    }


def write_outputs(runtime_rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in runtime_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    runtime_rows = build_runtime_rows()
    summary = build_summary(runtime_rows)
    expected = int(summary["runtime_source_rows_represented"])
    if len(runtime_rows) != expected:
        raise SystemExit(
            f"runtime row count {len(runtime_rows)} != represented source rows {expected}"
        )
    if args.check:
        existing_rows = OUTPUT_ROWS.read_text(encoding="utf-8") if OUTPUT_ROWS.exists() else ""
        rendered_rows = "".join(json.dumps(row, sort_keys=True) + "\n" for row in runtime_rows)
        existing_summary = (
            OUTPUT_SUMMARY.read_text(encoding="utf-8") if OUTPUT_SUMMARY.exists() else ""
        )
        rendered_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
        if existing_rows != rendered_rows or existing_summary != rendered_summary:
            raise SystemExit(
                "generated unified candidate action-execution runtime outputs are stale"
            )
        return 0

    write_outputs(runtime_rows, summary)
    print(f"Wrote {OUTPUT_ROWS} ({len(runtime_rows)} rows)")
    print(f"Wrote {OUTPUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
