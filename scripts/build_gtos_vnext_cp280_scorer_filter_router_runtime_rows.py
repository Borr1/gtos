#!/usr/bin/env python3
"""Build runtime rows for CP280 scorer/filter/router evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_gtos_vnext_master_conversion_ledger as master_ledger
from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
DATE = "2026-05-18"
WAVE_ID = "WAVE_VNEXT_SCORER_FILTER_ROUTER_RUNTIME"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_CP280_SCORER_FILTER_ROUTER_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_CP280_SCORER_FILTER_ROUTER_RUNTIME_SUMMARY_{DATE}.json"

COUNTABLE_SUFFIXES = {".jsonl", ".json", ".md", ".txt", ".csv", ".py"}
RUNTIME_SUFFIXES = {".jsonl", ".json", ".csv"}
OUTPUT_NAME_TOKENS = (
    "gtos_vnext_cp280_scorer_filter_router_runtime_rows",
    "gtos_vnext_cp280_scorer_filter_router_runtime_summary",
)
ANCHOR_FIELDS = (
    "market",
    "symbol",
    "source_symbol",
    "market_timeframe",
    "timeframe",
    "route_session",
    "side",
    "entry_variant",
    "target_stop_order_class",
)
RUNTIME_SOURCE_COMPONENT_RE = re.compile(r"^[A-Za-z0-9_]+$")


def _norm(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _upper(value: Any) -> str:
    return _norm(value).upper()


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_numeric(*values: Any) -> tuple[float | None, str]:
    for value in values:
        if isinstance(value, tuple):
            field_name, raw = value
        else:
            field_name, raw = "", value
        numeric = _to_float(raw)
        if numeric is not None:
            return numeric, str(field_name)
    return None, ""


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path_text(path: Path) -> str:
    try:
        if path.is_relative_to(REPO_ROOT):
            return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        pass
    return str(path).replace("\\", "/")


def _line_count(path: Path) -> int | None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return 1
    if suffix not in COUNTABLE_SUFFIXES:
        return None
    try:
        with path.open("rb") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return None


def _resolve_source_path(path_text: str) -> Path:
    source = Path(path_text)
    if source.is_absolute():
        return source
    candidate = REPO_ROOT / source
    if candidate.exists():
        return candidate
    tmp_candidate = Path("C:/tmp") / source
    if tmp_candidate.exists():
        return tmp_candidate
    return candidate


def _is_wave_unit(row: dict[str, Any]) -> bool:
    if row.get("batch_wave_id") == WAVE_ID:
        return True
    if row.get("affected_runtime_surface") == "vnext_scorer_filter_router_runtime":
        return True
    return master_ledger._batch_wave_id_for_row(row) == WAVE_ID


def _wave_units() -> list[dict[str, Any]]:
    rows = master_ledger.build_rows()
    return sorted(
        [
            row
            for row in rows
            if _is_wave_unit(row)
            and (
                row.get("conversion_state") in master_ledger.OPEN_BATCH_STATES
                or row.get("batch_wave_id") == WAVE_ID
            )
        ],
        key=lambda row: str(row.get("source_artifact_path") or "").casefold(),
    )


def _source_paths() -> list[tuple[Path, str]]:
    paths: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for unit in _wave_units():
        raw_path = _norm(unit.get("source_artifact_path"))
        lower = raw_path.casefold().replace("\\", "/")
        if not raw_path or any(token in lower for token in OUTPUT_NAME_TOKENS):
            continue
        path = _resolve_source_path(raw_path)
        if not path.exists() or path.suffix.lower() not in RUNTIME_SUFFIXES:
            continue
        key = str(path).casefold()
        if key in seen:
            continue
        seen.add(key)
        paths.append((path, _norm(unit.get("source_artifact_hash"))))
    paths.sort(key=lambda item: _path_text(item[0]).casefold())
    return paths


def _all_wave_paths() -> list[tuple[Path, str]]:
    paths: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for unit in _wave_units():
        raw_path = _norm(unit.get("source_artifact_path"))
        lower = raw_path.casefold().replace("\\", "/")
        if not raw_path or any(token in lower for token in OUTPUT_NAME_TOKENS):
            continue
        path = _resolve_source_path(raw_path)
        if not path.exists():
            continue
        key = str(path).casefold()
        if key in seen:
            continue
        seen.add(key)
        paths.append((path, _norm(unit.get("source_artifact_hash"))))
    paths.sort(key=lambda item: _path_text(item[0]).casefold())
    return paths


def _iter_source_rows(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                payload = json.loads(line)
                if isinstance(payload, dict):
                    yield line_no, payload
        return
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, list):
            for line_no, item in enumerate(payload, start=1):
                if isinstance(item, dict):
                    yield line_no, item
        elif isinstance(payload, dict):
            yield 1, payload
        return
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for line_no, row in enumerate(csv.DictReader(handle), start=2):
                yield line_no, dict(row)


def _source_file_group(path: Path) -> str:
    name = path.name
    for prefix in (
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_",
        "HISTORICAL_OHLC_GTOS_REPLAY_",
    ):
        if name.startswith(prefix):
            name = name[len(prefix):]
    for suffix in (
        "_LEDGER_2026-05-17.jsonl",
        "_LEDGER_2026-05-16.jsonl",
        "_2026-05-17.json",
        "_2026-05-16.json",
        ".jsonl",
        ".json",
        ".csv",
    ):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.lower()


def _source_component(path: Path, row: dict[str, Any]) -> str:
    explicit = _norm(row.get("source_component")).casefold()
    if explicit and RUNTIME_SOURCE_COMPONENT_RE.match(explicit):
        return explicit
    group = _source_file_group(path)
    if "numeric_router_system_recommendations" in group:
        return "cp280_numeric_router_system_recommendations"
    if "numeric_module_router_application" in group:
        return "cp280_numeric_module_router_application"
    if "numeric_shadow_scorer" in group:
        return "cp280_numeric_shadow_scorer"
    if "router_application_scoring_spec" in group:
        return "cp280_router_application_scoring"
    if "score_export_packet" in group:
        return "cp280_score_export_packet"
    if "unified_candidate_scoring" in group:
        return "cp280_unified_candidate_scorer"
    if "cost_fill_path_branch_proxy_scoring" in group:
        return "cp280_cost_fill_proxy_scorer"
    if "observable" in group:
        return "cp280_observable_runtime_work"
    if "unified_system_action_result" in group:
        return "cp280_unified_action_result"
    if "baseline_control" in group:
        return "cp280_baseline_control"
    return "cp280_scorer_filter_router"


def _parse_scope_key(value: Any) -> dict[str, str]:
    text = _norm(value)
    if not text:
        return {}
    parsed: dict[str, str] = {}
    for part in text.split("|"):
        if "=" not in part:
            continue
        key, raw_value = part.split("=", 1)
        key = key.strip().casefold()
        raw = _norm(raw_value)
        if not raw:
            continue
        if key == "session":
            key = "route_session"
        elif key == "horizon":
            key = "horizon_id"
        parsed[key] = raw
    return parsed


def _route_parts(row: dict[str, Any]) -> tuple[str, str, str, str]:
    route_candidate_id = _norm(
        row.get("route_candidate_id")
        or row.get("candidate_id")
        or row.get("branch_queue_id")
    )
    if route_candidate_id and "|" in route_candidate_id:
        parts = [part.strip() for part in route_candidate_id.split("|")]
        if len(parts) >= 4:
            return parts[0], parts[1], parts[2], parts[3]
    return "", "", "", ""


def _symbol(row: dict[str, Any]) -> str:
    route_symbol, _session, _primitive, _horizon = _route_parts(row)
    scope = _parse_scope_key(row.get("event_scope_key")) or _parse_scope_key(row.get("mechanical_scope_key"))
    return _norm(
        row.get("symbol")
        or row.get("source_symbol")
        or scope.get("symbol")
        or route_symbol
    )


def _route_session(row: dict[str, Any]) -> str:
    _symbol, route_session, _primitive, _horizon = _route_parts(row)
    scope = _parse_scope_key(row.get("event_scope_key")) or _parse_scope_key(row.get("mechanical_scope_key"))
    return _norm(
        row.get("route_session")
        or row.get("session")
        or row.get("kill_zone")
        or scope.get("route_session")
        or route_session
    )


def _primitive(row: dict[str, Any]) -> str:
    _symbol, _session, primitive, _horizon = _route_parts(row)
    scope = _parse_scope_key(row.get("event_scope_key")) or _parse_scope_key(row.get("mechanical_scope_key"))
    return _norm(
        row.get("primitive_flag")
        or row.get("primitive")
        or row.get("primitive_id")
        or scope.get("primitive")
        or primitive
    )


def _horizon_id(row: dict[str, Any]) -> str:
    _symbol, _session, _primitive, horizon = _route_parts(row)
    scope = _parse_scope_key(row.get("event_scope_key")) or _parse_scope_key(row.get("mechanical_scope_key"))
    return _norm(row.get("horizon_id") or row.get("horizon") or scope.get("horizon_id") or horizon)


def _side(row: dict[str, Any]) -> str:
    side = _upper(row.get("side") or row.get("selected_side") or row.get("direction"))
    if side in {"LONG", "SHORT"}:
        return side
    primitive = _primitive(row).casefold()
    if "sweep_low" in primitive or "lower_wick" in primitive or "breakout_up" in primitive:
        return "LONG"
    if "sweep_high" in primitive or "upper_wick" in primitive or "breakout_down" in primitive:
        return "SHORT"
    return ""


def _timeframe(row: dict[str, Any]) -> str:
    timeframe = _norm(row.get("market_timeframe") or row.get("timeframe") or row.get("entry_timeframe"))
    if timeframe:
        return timeframe.upper()
    available = row.get("available_timeframes")
    if isinstance(available, list) and len(available) == 1:
        return _norm(available[0]).upper()
    return ""


def _entry_variant(row: dict[str, Any]) -> str:
    return _norm(row.get("entry_variant") or row.get("entry_geometry_variant") or row.get("target_stop_contract_id"))


def _metric_from_scalar(value: Any, *, source_field: str) -> dict[str, Any] | None:
    numeric = _to_float(value)
    if numeric is None:
        return None
    return {
        "sum": round(numeric, 12),
        "mean": round(numeric, 12),
        "count": 1,
        "match_rows_with_metric": 1,
        "positive_rows": 1 if numeric > 0 else 0,
        "negative_rows": 1 if numeric < 0 else 0,
        "zero_rows": 1 if numeric == 0 else 0,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _proxy_value(row: dict[str, Any]) -> tuple[float | None, str]:
    return _first_numeric(
        ("registry_surface_score", row.get("registry_surface_score")),
        ("shadow_score", row.get("shadow_score")),
        ("proxy_r_value", row.get("proxy_r_value")),
        ("cost_stress_adjusted_proxy_r", row.get("cost_stress_adjusted_proxy_r")),
        ("expectancy_proxy_value", row.get("expectancy_proxy_value")),
        ("positive_spec_score", row.get("positive_spec_score")),
        ("positive_adjusted_midpoint", row.get("positive_adjusted_midpoint")),
        ("candidate_score_proxy_mean", row.get("candidate_score_proxy_mean")),
        ("proxy_numeric_score", row.get("proxy_numeric_score")),
        ("proxy_or_module_score", row.get("proxy_or_module_score")),
        ("router_application_score", row.get("router_application_score")),
        ("market_gap_score_proxy_mean", row.get("market_gap_score_proxy_mean")),
        ("branch_score_proxy_mean", row.get("branch_score_proxy_mean")),
        ("score", row.get("score")),
        ("default_off_observation_score", row.get("default_off_observation_score")),
    )


def _joined_text(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in (
        "registry_surface_status",
        "shadow_decision",
        "keep_kill_redesign_implement_decision",
        "implementation_decision",
        "implementation_implication",
        "implementation_implication_class",
        "implementation_action",
        "action_class",
        "action_result_family",
        "action_execution_status",
        "executable_next_action",
        "positive_action",
        "positive_spec_action",
        "positive_export_class",
        "positive_followup_class",
        "positive_replay_score_class",
        "positive_spec_score_class",
        "source_status",
        "source_confidence_status",
        "source_requirement",
        "exact_r_compute_status",
        "exact_R_availability",
        "proxy_R_availability",
        "proxy_r_style_result",
        "target_stop_order_class",
        "target_stop_result",
        "tradability_status",
        "market_expansion_decision",
        "fillability_no_fill_status",
        "candidate_score_class_counts",
        "implementation_candidate_type_counts",
        "unified_execution_decision_counts",
        "work_order_family",
    ):
        value = row.get(field)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, (dict, list, tuple)):
            try:
                parts.append(json.dumps(value, sort_keys=True))
            except TypeError:
                parts.append(str(value))
        else:
            parts.append(str(value))
    return " ".join(parts).upper()


def _source_repair_required(row: dict[str, Any]) -> bool:
    text = _joined_text(row)
    if row.get("source_exact_acquisition_required") is True:
        return True
    return any(
        token in text
        for token in (
            "SOURCE_REPAIR",
            "SOURCE_CAPTURE",
            "SOURCE_ACQUISITION",
            "ACQUIRE_EXACT",
            "MISSING_GEOMETRY",
            "MISSING_REQUIRED",
            "SOURCE_JOIN_REPAIR",
            "REPAIR_REQUIRED",
            "DENOMINATOR_GUARD",
        )
    )


def _target_stop_order_class(row: dict[str, Any], source_repair: bool) -> str:
    explicit = _upper(row.get("target_stop_order_class"))
    if explicit:
        return explicit
    text = _joined_text(row)
    if "STOP_FIRST" in text:
        return "STOP_FIRST_PROXY_DOMINANT"
    if "TARGET_FIRST" in text or "INTERVAL_ALL_POSITIVE" in text:
        return "TARGET_FIRST_PROXY_DOMINANT"
    if "TARGET_STOP_ORDER_NOT_SOURCE_BOUND" in text:
        return "TARGET_STOP_ORDER_NOT_SOURCE_BOUND"
    if source_repair and ("TARGET" in text or "STOP" in text or "GEOMETRY" in text):
        return "TARGET_STOP_ORDER_NOT_SOURCE_BOUND"
    if "AMBIGUOUS" in text or "STRADDLES" in text or "INTERVAL" in text:
        return "TARGET_STOP_AMBIGUOUS_OR_MIXED"
    return ""


def _proxy_class(row: dict[str, Any], proxy: float | None, target_stop_class: str) -> str:
    explicit = _upper(row.get("proxy_r_class"))
    if explicit:
        return explicit
    if target_stop_class == "STOP_FIRST_PROXY_DOMINANT":
        return "STRONG_NEGATIVE_PROXY_R"
    if proxy is None:
        return "FLAT_OR_MISSING_PROXY_R"
    if proxy >= 0.25:
        return "STRONG_POSITIVE_PROXY_R"
    if proxy > 0:
        return "POSITIVE_PROXY_R"
    if proxy <= -0.25:
        return "STRONG_NEGATIVE_PROXY_R"
    if proxy < 0:
        return "NEGATIVE_PROXY_R"
    return "FLAT_OR_MISSING_PROXY_R"


def _positive_scorer_status(row: dict[str, Any]) -> bool:
    text = _joined_text(row)
    return any(
        token in text
        for token in (
            "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
            "IMPLEMENT_DEFAULT_OFF_SCORER_SCOPE_WITH_GUARDS",
            "SCORER_SURFACE_READY",
            "FOLLOW_SCORER",
            "POSITIVE_EXPORT",
            "POSITIVE_REPLAY",
            "PROXY_R_STYLE_POSITIVE",
            "PROXY_R_STYLE_STRONG_POSITIVE",
        )
    )


def _avoid_status(row: dict[str, Any]) -> bool:
    text = _joined_text(row)
    return any(
        token in text
        for token in (
            "AVOID_OR_KILL",
            "AVOID_OR_REDIRECT",
            "AVOID_FILTER",
            "INVERSE_FILTER",
            "FAILURE_FILTER",
            "REGISTER_NEGATIVE_PROXY_FAILURE_FEATURE",
            "BRANCH_LOW_PRIORITY_OR_AVOID_FIRST",
            "LOW_PRIORITY_OR_AVOID",
            "KILL_PRESSURE",
            "REJECTED_NONPOSITIVE",
        )
    )


def _decision(row: dict[str, Any], proxy: float | None, target_stop_class: str, source_repair: bool) -> str:
    if target_stop_class == "STOP_FIRST_PROXY_DOMINANT":
        return "AVOID"
    if _avoid_status(row):
        return "AVOID"
    if _positive_scorer_status(row):
        return "FOLLOW" if proxy is None or proxy >= -0.05 else "MIXED"
    if source_repair:
        return "MIXED"
    if target_stop_class == "TARGET_STOP_ORDER_NOT_SOURCE_BOUND":
        return "MIXED"
    if proxy is not None and proxy > 0.05:
        return "FOLLOW"
    if proxy is not None and proxy < -0.05:
        return "AVOID"
    return "MIXED"


def _source_role(
    *,
    decision: str,
    source_repair: bool,
    row: dict[str, Any],
    component: str,
) -> str:
    text = _joined_text(row)
    if "SCORER_REGISTRY_SURFACE" in text or component == "registry_scorer_module":
        return "scorer_registry_surface"
    if source_repair:
        return "cp280_scorer_filter_router_source_repair_guard"
    if decision == "AVOID":
        return "cp280_scorer_filter_router_avoid_guard"
    if decision == "FOLLOW":
        return "cp280_scorer_filter_router_follow_pressure"
    return "cp280_scorer_filter_router_context_guard"


def _system_surface(row: dict[str, Any], source_role: str) -> str:
    if source_role == "scorer_registry_surface":
        return "scorer_registry_surface"
    surface = _norm(
        row.get("registry_source_surface")
        or row.get("shadow_scorer_compute_surface")
        or row.get("unified_system_action_result_surface")
    )
    if "registry" in surface.casefold() and "scorer" in surface.casefold():
        return "numeric_router_default_off_scope_decision_catalog"
    return "cp280_scorer_filter_router_runtime"


def _action_class(decision: str, source_repair: bool) -> str:
    if source_repair:
        return "cp280_scorer_filter_router_source_repair_guard"
    if decision == "AVOID":
        return "cp280_scorer_filter_router_avoid_filter"
    if decision == "FOLLOW":
        return "cp280_scorer_filter_router_follow_scorer"
    return "cp280_scorer_filter_router_context_guard"


def _r_evidence_class(decision: str, source_repair: bool, target_stop_class: str) -> str:
    if source_repair:
        return "SOURCE_REPAIR_FOR_EXACT_R"
    if target_stop_class == "STOP_FIRST_PROXY_DOMINANT":
        return "CP280_SCORER_FILTER_ROUTER_STOP_FIRST_AVOID"
    if decision == "FOLLOW":
        return "CP280_SCORER_FILTER_ROUTER_POSITIVE_PROXY"
    if decision == "AVOID":
        return "CP280_SCORER_FILTER_ROUTER_NEGATIVE_OR_AVOID"
    return "CP280_SCORER_FILTER_ROUTER_CONTEXT"


def _metric_payload(row: dict[str, Any], *, proxy_value: float | None, proxy_field: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    if proxy_value is not None:
        metrics["proxy_score"] = _metric_from_scalar(proxy_value, source_field=proxy_field)
        metrics["cost_adjusted_simulated_r"] = _metric_from_scalar(
            proxy_value,
            source_field=f"{proxy_field}_as_cost_proxy",
        )
    stress_value, stress_field = _first_numeric(
        ("cost_stress_adjusted_proxy_r", row.get("cost_stress_adjusted_proxy_r")),
        ("positive_adjusted_midpoint", row.get("positive_adjusted_midpoint")),
    )
    if stress_value is not None:
        metrics["stress_simulated_r"] = _metric_from_scalar(stress_value, source_field=stress_field)
    effective_n, effective_field = _first_numeric(
        ("all_candidate_rows", row.get("all_candidate_rows")),
        ("branch_score_rows", row.get("branch_score_rows")),
        ("market_gap_score_rows", row.get("market_gap_score_rows")),
        ("candidate_rows", row.get("candidate_rows")),
        ("source_row_count", row.get("source_row_count")),
        ("rows", row.get("rows")),
        ("runtime_score_allowed_row", 1),
    )
    if effective_n is not None:
        metrics["effective_n"] = _metric_from_scalar(effective_n, source_field=effective_field)
    return {key: value for key, value in metrics.items() if value is not None}


def _source_row_id(row: dict[str, Any], path: Path, line_no: int) -> str:
    for field in (
        "scorer_registry_surface_row_id",
        "shadow_scorer_event_score_row_id",
        "input_numeric_result_row_id",
        "input_router_application_row_id",
        "positive_spec_id",
        "symbol_session_decision_id",
        "unified_system_action_result_row_id",
        "source_row_id",
        "route_candidate_id",
        "branch_queue_id",
        "row_id",
        "id",
    ):
        if value := _norm(row.get(field)):
            return value
    return f"{path.name}:{line_no}"


def _runtime_effect(decision: str, source_repair: bool) -> str:
    if source_repair:
        return "cp280_scorer_filter_router_source_repair_guard"
    return {
        "FOLLOW": "cp280_scorer_filter_router_follow_pressure",
        "AVOID": "cp280_scorer_filter_router_avoid_filter",
        "MIXED": "cp280_scorer_filter_router_context_guard",
    }[decision]


def _build_runtime_row(
    *,
    row: dict[str, Any],
    path: Path,
    line_no: int,
    source_hash: str,
    file_sha256: str,
) -> dict[str, Any]:
    component = _source_component(path, row)
    proxy, proxy_field = _proxy_value(row)
    source_repair = _source_repair_required(row)
    target_stop_class = _target_stop_order_class(row, source_repair)
    decision = _decision(row, proxy, target_stop_class, source_repair)
    action_class = _action_class(decision, source_repair)
    proxy_class = _proxy_class(row, proxy, target_stop_class)
    source_role = _source_role(
        decision=decision,
        source_repair=source_repair,
        row=row,
        component=component,
    )
    system_surface = _system_surface(row, source_role)
    source_path = _path_text(path)
    source_row_id = _source_row_id(row, path, line_no)
    symbol = _symbol(row)
    session = _route_session(row)
    side = _side(row)
    timeframe = _timeframe(row)
    event_scope = {
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "market_timeframe": timeframe,
        "timeframe": timeframe,
        "route_session": session,
        "side": side,
        "horizon_id": _horizon_id(row),
        "primitive": _primitive(row),
        "route_family": "numeric_router",
        "source_component": component,
        "action_class": action_class,
        "entry_variant": _entry_variant(row),
        "target_stop_order_class": target_stop_class,
        "proxy_r_class": proxy_class,
    }
    if family := resolve_vnext_symbol_family(symbol):
        event_scope["symbol_family"] = family
    event_scope = {key: value for key, value in event_scope.items() if value not in (None, "")}
    anchor_complete = bool(symbol and session and side)
    if not anchor_complete:
        event_scope = {"source_component": "cp280_blank_anchor_guard"}
    row_id = f"cp280_scorer_filter_router:{component}:{line_no}:{_sha256_text(source_row_id)[:16]}"
    implementation_action = _norm(
        row.get("registry_surface_status")
        or row.get("implementation_action")
        or row.get("implementation_decision")
        or row.get("executable_next_action")
        or row.get("positive_spec_action")
        or row.get("action_class")
        or row.get("action_result_family")
    )
    runtime_row = {
        "schema_version": "gtos_vnext_cp280_scorer_filter_router_runtime_row_v1",
        "cp280_scorer_filter_router_runtime_row_id": row_id,
        "row_key": row_id,
        "source_row_id": source_row_id,
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "market_timeframe": timeframe,
        "timeframe": timeframe,
        "route_session": session,
        "side": side,
        "horizon_id": _horizon_id(row),
        "primitive": _primitive(row),
        "entry_variant": _entry_variant(row),
        "route_family": "numeric_router",
        "source_component": component,
        "source_group": (
            "scorer_registry_surface"
            if source_role == "scorer_registry_surface"
            else f"cp280_scorer_filter_router_{decision.casefold()}"
        ),
        "source_role": source_role,
        "source_name": "gtos_vnext_cp280_scorer_filter_router_wave",
        "evidence_family": "gtos_vnext_cp280_scorer_filter_router",
        "system_surface": system_surface,
        "review_action": decision,
        "decision": decision,
        "action_class": action_class,
        "implementation_action": implementation_action,
        "runtime_effect_now": _runtime_effect(decision, source_repair),
        "runtime_candidate_use_permitted": bool(anchor_complete and decision == "FOLLOW"),
        "candidate_use_allowed_now": bool(anchor_complete and decision in {"FOLLOW", "AVOID"}),
        "r_evidence_class": _r_evidence_class(decision, source_repair, target_stop_class),
        "proxy_r_class": proxy_class,
        "target_stop_order_class": target_stop_class,
        "source_repair_required": source_repair,
        "source_acquisition_required": source_repair,
        "source_bound": anchor_complete,
        "source_complete": bool(anchor_complete and not source_repair),
        "event_scope": event_scope,
        "r_metrics": _metric_payload(row, proxy_value=proxy, proxy_field=proxy_field),
        "source_artifact": source_path,
        "source_path": source_path,
        "declared_origin_artifact": source_path,
        "source_artifact_hash": source_hash,
        "source_artifact_sha256": file_sha256,
        "source_file_sha256": file_sha256,
        "declared_origin_sha256": file_sha256,
        "source_path_sha256": _sha256_text(source_path),
        "source_line_no": line_no,
        "declared_origin_line_no": line_no,
        "source_file_group": _source_file_group(path),
        "source_rows_represented": int(
            _to_float(row.get("all_candidate_rows"))
            or _to_float(row.get("source_row_count"))
            or 1
        ),
        "raw_status_text_sha256": _sha256_text(_joined_text(row)) if _joined_text(row) else "",
        "registry_surface_status": _norm(row.get("registry_surface_status")),
        "shadow_decision": _norm(row.get("shadow_decision")),
        "work_order_family": _norm(row.get("work_order_family")),
        "action_result_family": _norm(row.get("action_result_family")),
        "target_artifact_kind": _norm(row.get("target_artifact_kind")),
    }
    return {key: value for key, value in runtime_row.items() if value not in (None, "", {})}


def _metric_empty(source_field: str) -> dict[str, Any]:
    return {
        "sum": 0.0,
        "count": 0,
        "match_rows_with_metric": 0,
        "positive_rows": 0,
        "negative_rows": 0,
        "zero_rows": 0,
        "source_field": source_field,
        "source_shape": "aggregate",
    }


def _merge_metric(target: dict[str, Any], source: dict[str, Any]) -> None:
    count = int(source.get("count") or 0)
    if count <= 0:
        return
    target["sum"] = float(target.get("sum") or 0.0) + float(source.get("sum") or 0.0)
    target["count"] = int(target.get("count") or 0) + count
    target["match_rows_with_metric"] = int(target.get("match_rows_with_metric") or 0) + int(
        source.get("match_rows_with_metric") or 0
    )
    target["positive_rows"] = int(target.get("positive_rows") or 0) + int(source.get("positive_rows") or 0)
    target["negative_rows"] = int(target.get("negative_rows") or 0) + int(source.get("negative_rows") or 0)
    target["zero_rows"] = int(target.get("zero_rows") or 0) + int(source.get("zero_rows") or 0)


def _finalize_metric(metric: dict[str, Any]) -> dict[str, Any]:
    count = int(metric.get("count") or 0)
    total = float(metric.get("sum") or 0.0)
    finalized = dict(metric)
    finalized["sum"] = round(total, 12)
    finalized["mean"] = round(total / count, 12) if count else None
    return {key: value for key, value in finalized.items() if value is not None}


def _aggregate_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("source_component"),
        row.get("source_file_group"),
        row.get("decision"),
        row.get("action_class"),
        row.get("source_role"),
        row.get("system_surface"),
        row.get("r_evidence_class"),
        row.get("route_family"),
        row.get("symbol"),
        row.get("route_session"),
        row.get("side"),
        row.get("market_timeframe"),
        row.get("primitive"),
        row.get("horizon_id"),
        row.get("entry_variant"),
        row.get("target_stop_order_class"),
        row.get("proxy_r_class"),
        bool(row.get("event_scope")),
    )


def _aggregate_runtime_rows(rows: Iterator[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Counter]]:
    grouped: dict[tuple[Any, ...], dict[str, Any]] = {}
    raw_counters = {
        "blank_anchor_counts": Counter(),
        "anchor_coverage": Counter(),
    }
    for row in rows:
        for field in ANCHOR_FIELDS:
            value = row.get(field)
            if value in (None, "", {}, []):
                raw_counters["blank_anchor_counts"][field] += 1
            else:
                raw_counters["anchor_coverage"][f"{field}:{value}"] += 1
        key = _aggregate_key(row)
        aggregate = grouped.get(key)
        if aggregate is None:
            aggregate = {
                name: value
                for name, value in row.items()
                if name
                not in {
                    "cp280_scorer_filter_router_runtime_row_id",
                    "row_key",
                    "source_row_id",
                    "source_line_no",
                    "declared_origin_line_no",
                    "r_metrics",
                }
            }
            aggregate["event_scope"] = dict(row.get("event_scope") or {})
            aggregate["runtime_aggregate_member_rows"] = 0
            aggregate["source_rows_represented"] = 0
            aggregate["source_row_id_samples"] = []
            aggregate["source_line_no_min"] = row.get("source_line_no")
            aggregate["source_line_no_max"] = row.get("source_line_no")
            aggregate["_metric_accumulator"] = {}
            grouped[key] = aggregate
        aggregate["runtime_aggregate_member_rows"] += 1
        aggregate["source_rows_represented"] += int(row.get("source_rows_represented") or 0)
        samples = aggregate["source_row_id_samples"]
        sample = row.get("source_row_id")
        if sample and sample not in samples and len(samples) < 24:
            samples.append(sample)
        line_no = _to_float(row.get("source_line_no"))
        if line_no is not None:
            current_min = _to_float(aggregate.get("source_line_no_min"))
            current_max = _to_float(aggregate.get("source_line_no_max"))
            aggregate["source_line_no_min"] = int(min(current_min or line_no, line_no))
            aggregate["source_line_no_max"] = int(max(current_max or line_no, line_no))
        metrics = row.get("r_metrics") if isinstance(row.get("r_metrics"), dict) else {}
        metric_accumulator = aggregate["_metric_accumulator"]
        for metric_name, metric in metrics.items():
            if not isinstance(metric, dict):
                continue
            target = metric_accumulator.setdefault(
                metric_name,
                _metric_empty(str(metric.get("source_field") or metric_name)),
            )
            _merge_metric(target, metric)

    aggregated_rows: list[dict[str, Any]] = []
    for index, aggregate in enumerate(
        sorted(
            grouped.values(),
            key=lambda item: (
                str(item.get("source_component") or ""),
                str(item.get("source_file_group") or ""),
                str(item.get("decision") or ""),
                str(item.get("symbol") or ""),
                str(item.get("route_session") or ""),
                str(item.get("side") or ""),
                str(item.get("target_stop_order_class") or ""),
            ),
        ),
        start=1,
    ):
        metric_accumulator = aggregate.pop("_metric_accumulator", {})
        if metric_accumulator:
            aggregate["r_metrics"] = {
                name: _finalize_metric(metric)
                for name, metric in sorted(metric_accumulator.items())
            }
        digest = _sha256_text(
            "|".join(
                _norm(aggregate.get(field))
                for field in (
                    "source_component",
                    "source_file_group",
                    "decision",
                    "symbol",
                    "route_session",
                    "side",
                    "market_timeframe",
                    "primitive",
                    "horizon_id",
                    "entry_variant",
                    "target_stop_order_class",
                    "proxy_r_class",
                    "source_role",
                )
            )
        )[:16]
        row_id = f"cp280_scorer_filter_router:aggregate:{index}:{digest}"
        aggregate["cp280_scorer_filter_router_runtime_row_id"] = row_id
        aggregate["row_key"] = row_id
        samples = aggregate.get("source_row_id_samples") or []
        if samples:
            aggregate["source_row_id"] = samples[0]
        aggregate["declared_origin_line_no"] = aggregate.get("source_line_no_min")
        aggregate["source_line_no"] = aggregate.get("source_line_no_min")
        aggregated_rows.append(
            {name: value for name, value in aggregate.items() if value not in (None, "", {}, [])}
        )
    return aggregated_rows, raw_counters


def _coverage_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    fields = {
        "markets": "market",
        "symbols": "symbol",
        "source_symbols": "source_symbol",
        "timeframes": "market_timeframe",
        "sessions": "route_session",
        "sides": "side",
        "entry_variants": "entry_variant",
        "exit_target_stop_order_classes": "target_stop_order_class",
    }
    result: dict[str, dict[str, int]] = {}
    for name, field in fields.items():
        result[name] = dict(sorted(Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field))).items()))
    return result


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter()
    for row in rows:
        for field in ANCHOR_FIELDS:
            if row.get(field) in (None, "", {}, []):
                counts[field] += 1
        if not row.get("source_bound"):
            counts["event_scope"] += 1
    return dict(sorted(counts.items()))


def build_runtime_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_artifacts: list[dict[str, Any]] = []
    source_artifact_keys: set[str] = set()
    raw_runtime_row_count = 0

    def _row_stream() -> Iterator[dict[str, Any]]:
        nonlocal raw_runtime_row_count
        for path, source_hash in _source_paths():
            file_sha256 = _sha256_file(path)
            runtime_rows_read = 0
            row_count = 0
            for line_no, row in _iter_source_rows(path):
                row_count += 1
                runtime_rows_read += 1
                raw_runtime_row_count += 1
                yield _build_runtime_row(
                    row=row,
                    path=path,
                    line_no=line_no,
                    source_hash=source_hash,
                    file_sha256=file_sha256,
                )
            source_artifacts.append(
                {
                    "path": _path_text(path),
                    "sha256_or_git_blob": source_hash or file_sha256,
                    "file_sha256": file_sha256,
                    "rows": row_count,
                    "line_count": _line_count(path),
                    "runtime_rows_read": runtime_rows_read,
                    "source_component": _source_component(path, {}),
                    "source_file_group": _source_file_group(path),
                }
            )
            source_artifact_keys.add(str(path).casefold())

    runtime_rows, raw_counters = _aggregate_runtime_rows(_row_stream())
    for path, source_hash in _all_wave_paths():
        key = str(path).casefold()
        if key in source_artifact_keys:
            continue
        file_sha256 = _sha256_file(path)
        source_artifacts.append(
            {
                "path": _path_text(path),
                "sha256_or_git_blob": source_hash or file_sha256,
                "file_sha256": file_sha256,
                "rows": _line_count(path) or 0,
                "line_count": _line_count(path),
                "runtime_rows_read": 0,
                "source_component": _source_component(path, {}),
                "source_file_group": _source_file_group(path),
            }
        )
    source_artifacts.sort(key=lambda item: str(item.get("path") or "").casefold())
    decision_counts = Counter(str(row.get("decision")) for row in runtime_rows)
    component_counts = Counter(str(row.get("source_component")) for row in runtime_rows)
    role_counts = Counter(str(row.get("source_role")) for row in runtime_rows)
    route_family_counts = Counter(str(row.get("route_family")) for row in runtime_rows)
    action_class_counts = Counter(str(row.get("action_class")) for row in runtime_rows)
    r_evidence_counts = Counter(str(row.get("r_evidence_class")) for row in runtime_rows)
    target_stop_counts = Counter(
        str(row.get("target_stop_order_class"))
        for row in runtime_rows
        if row.get("target_stop_order_class")
    )
    proxy_counts = Counter(str(row.get("proxy_r_class")) for row in runtime_rows)
    summary = {
        "schema_version": "gtos_vnext_cp280_scorer_filter_router_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(runtime_rows),
        "raw_runtime_row_count": raw_runtime_row_count,
        "runtime_rows_with_event_scope": sum(1 for row in runtime_rows if row.get("source_bound")),
        "runtime_rows_without_event_scope": sum(1 for row in runtime_rows if not row.get("source_bound")),
        "runtime_source_rows_represented": sum(
            int(row.get("source_rows_represented") or 0) for row in runtime_rows
        ),
        "wave_source_artifact_count": len(source_artifacts),
        "wave_source_rows_counted": sum(int(item.get("rows") or 0) for item in source_artifacts),
        "decision_counts": dict(sorted(decision_counts.items())),
        "source_component_counts": dict(sorted(component_counts.items())),
        "source_role_counts": dict(sorted(role_counts.items())),
        "route_family_counts": dict(sorted(route_family_counts.items())),
        "action_class_counts": dict(sorted(action_class_counts.items())),
        "r_evidence_class_counts": dict(sorted(r_evidence_counts.items())),
        "target_stop_order_class_counts": dict(sorted(target_stop_counts.items())),
        "proxy_r_class_counts": dict(sorted(proxy_counts.items())),
        "coverage_counts": _coverage_counts(runtime_rows),
        "blank_anchor_counts": _blank_anchor_counts(runtime_rows),
        "raw_blank_anchor_counts": dict(sorted(raw_counters["blank_anchor_counts"].items())),
        "source_artifacts": source_artifacts,
    }
    return runtime_rows, summary


def write_outputs() -> None:
    rows, summary = build_runtime_rows()
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def check_outputs() -> int:
    rows, summary = build_runtime_rows()
    expected_rows = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows
    )
    expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    issues: list[str] = []
    if not OUTPUT_ROWS.exists() or OUTPUT_ROWS.read_text(encoding="utf-8") != expected_rows:
        issues.append(str(OUTPUT_ROWS))
    if not OUTPUT_SUMMARY.exists() or OUTPUT_SUMMARY.read_text(encoding="utf-8") != expected_summary:
        issues.append(str(OUTPUT_SUMMARY))
    if issues:
        print("CP280 scorer/filter/router runtime outputs are stale:", file=sys.stderr)
        for issue in issues:
            print(f"  {issue}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify outputs are current")
    args = parser.parse_args()
    if args.check:
        return check_outputs()
    write_outputs()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
