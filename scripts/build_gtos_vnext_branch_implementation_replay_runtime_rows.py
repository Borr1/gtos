#!/usr/bin/env python3
"""Build runtime rows for CP280 branch implementation/replay evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
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
WAVE_ID = "WAVE_BRANCH_IMPLEMENTATION_REPLAY_RUNTIME"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_BRANCH_IMPLEMENTATION_REPLAY_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_BRANCH_IMPLEMENTATION_REPLAY_RUNTIME_SUMMARY_{DATE}.json"

COUNTABLE_SUFFIXES = {".jsonl", ".json", ".md", ".txt", ".csv", ".py"}
OUTPUT_NAME_TOKENS = (
    "gtos_vnext_branch_implementation_replay_runtime_rows",
    "gtos_vnext_branch_implementation_replay_runtime_summary",
)
ROW_BEARING_TOKENS = (
    "branch_cause_implementation_matrix",
    "branch_code_replay_proposal",
    "branch_full_outcome_implementation_synthesis",
    "branch_implementation_action_synthesis",
    "branch_implementation_replay_decision_matrix",
    "branch_local_control_source_split_bundle",
    "branch_local_guarded_scope_scorer_registration_bundle",
    "branch_local_implementation_candidate_packet",
    "branch_local_numeric_decision_modules",
    "branch_local_numeric_module_router_application",
    "branch_m1_chronological_collapse",
    "branch_m1_fill_bar_interval_collapse",
    "branch_m1_support_conflict_detail",
    "branch_next_compute_scoring",
    "branch_ordering_collapse_deep",
    "branch_positive_challenger",
    "branch_replay_builder_parameter_packet",
    "branch_router_application_scoring_spec",
    "branch_score_export_packet",
    "branch_source_bar_spread_recompute",
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
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


def _first_numeric(*values: Any) -> float | None:
    for value in values:
        numeric = _to_float(value)
        if numeric is not None:
            return numeric
    return None


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


def _is_branch_implementation_path(path_text: str) -> bool:
    lower = path_text.casefold().replace("\\", "/")
    if any(token in lower for token in OUTPUT_NAME_TOKENS):
        return True
    return any(token in lower for token in ROW_BEARING_TOKENS)


def _wave_units() -> list[dict[str, Any]]:
    rows = master_ledger.build_rows()
    return sorted(
        [
            row
            for row in rows
            if row.get("batch_wave_id") == WAVE_ID
            or (
                row.get("conversion_state") in master_ledger.OPEN_BATCH_STATES
                and master_ledger._batch_wave_id_for_row(row) == WAVE_ID
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
        if not raw_path:
            continue
        if any(token in lower for token in OUTPUT_NAME_TOKENS):
            continue
        if not any(token in lower for token in ROW_BEARING_TOKENS):
            continue
        if any(
            token in lower
            for token in (
                "build_",
                "verify_",
                "question_ledger",
                "source_manifest",
                "summary_2026",
                "packet_result_2026",
                "result_2026",
            )
        ):
            continue
        path = _resolve_source_path(raw_path)
        if not path.exists():
            continue
        if path.suffix.lower() not in {".jsonl", ".json", ".csv"}:
            continue
        key = str(path).casefold()
        if key in seen:
            continue
        seen.add(key)
        paths.append((path, _norm(unit.get("source_artifact_hash"))))
    paths.sort(key=lambda item: _path_text(item[0]).casefold())
    return paths


def _read_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
        return rows
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            return [payload]
        return []
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    return []


def _source_file_group(path: Path) -> str:
    name = path.name
    for prefix in (
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_",
        "HISTORICAL_OHLC_GTOS_REPLAY_",
    ):
        if name.startswith(prefix):
            name = name[len(prefix):]
    for suffix in (
        "_LEDGER_2026-05-17.jsonl",
        "_LEDGER_2026-05-16.jsonl",
        ".jsonl",
        ".json",
        ".csv",
    ):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.lower()


def _source_component(path: Path) -> str:
    group = _source_file_group(path)
    if group.startswith("cause_implementation_matrix"):
        return "gtos_branch_impl_cause_matrix"
    if group.startswith("code_replay_proposal"):
        return "gtos_branch_impl_code_replay"
    if group.startswith("full_outcome_implementation_synthesis"):
        return "gtos_branch_impl_full_outcome"
    if group.startswith("implementation_action_synthesis"):
        return "gtos_branch_impl_action"
    if group.startswith("implementation_replay_decision_matrix"):
        return "gtos_branch_impl_replay_matrix"
    if group.startswith("control_source_split_bundle"):
        return "gtos_branch_impl_control_source_split"
    if group.startswith("guarded_scope_scorer_registration_bundle"):
        return "gtos_branch_impl_guarded_scope_scorer"
    if group.startswith("implementation_candidate_packet"):
        return "gtos_branch_impl_candidate"
    if group.startswith("numeric_decision_modules"):
        return "gtos_branch_impl_numeric_decision"
    if group.startswith("numeric_module_router_application"):
        return "gtos_branch_impl_numeric_router"
    if group.startswith("m1_chronological_collapse"):
        return "gtos_branch_impl_m1_chronology"
    if group.startswith("m1_fill_bar_interval_collapse"):
        return "gtos_branch_impl_m1_interval"
    if group.startswith("m1_support_conflict_detail"):
        return "gtos_branch_impl_m1_support"
    if group.startswith("next_compute_scoring"):
        return "gtos_branch_impl_next_compute"
    if group.startswith("ordering_collapse_deep"):
        return "gtos_branch_impl_ordering_collapse"
    if group.startswith("positive_challenger"):
        return "gtos_branch_impl_positive_challenger"
    if group.startswith("replay_builder_parameter_packet"):
        return "gtos_branch_impl_replay_builder"
    if group.startswith("router_application_scoring_spec"):
        return "gtos_branch_impl_router_scoring"
    if group.startswith("score_export_packet"):
        return "gtos_branch_impl_score_export"
    if group.startswith("source_bar_spread_recompute"):
        return "gtos_branch_impl_source_spread_recompute"
    return "gtos_branch_impl_replay"


def _route_parts(row: dict[str, Any]) -> tuple[str, str, str, str]:
    route_candidate_id = _norm(row.get("route_candidate_id") or row.get("candidate_id"))
    if route_candidate_id and "|" in route_candidate_id:
        parts = [part.strip() for part in route_candidate_id.split("|")]
        if len(parts) >= 4:
            return parts[0], parts[1], parts[2], parts[3]
    return "", "", "", ""


def _symbol(row: dict[str, Any]) -> str:
    route_symbol, _session, _primitive, _horizon = _route_parts(row)
    return _norm(row.get("symbol") or row.get("source_symbol") or route_symbol)


def _route_session(row: dict[str, Any]) -> str:
    _symbol_part, route_session, _primitive, _horizon = _route_parts(row)
    return _norm(row.get("route_session") or row.get("session") or route_session)


def _primitive(row: dict[str, Any]) -> str:
    _symbol_part, _session, primitive, _horizon = _route_parts(row)
    return _norm(row.get("primitive") or row.get("primitive_id") or primitive)


def _horizon_id(row: dict[str, Any]) -> str:
    _symbol_part, _session, _primitive, horizon = _route_parts(row)
    return _norm(row.get("horizon_id") or row.get("horizon") or horizon)


def _side(row: dict[str, Any]) -> str:
    side = _upper(row.get("side"))
    if side in {"LONG", "SHORT"}:
        return side
    primitive = _primitive(row).casefold()
    if "sweep_low" in primitive or "lower_wick" in primitive or "breakout_up" in primitive:
        return "LONG"
    if "sweep_high" in primitive or "upper_wick" in primitive or "breakout_down" in primitive:
        return "SHORT"
    return ""


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


def _metric_value(row: dict[str, Any]) -> tuple[float | None, str]:
    fields = (
        "router_application_score",
        "proxy_actionability_score",
        "expectancy_style_proxy_value",
        "rstyle_midpoint_mean",
        "positive_adjusted_midpoint",
        "positive_spec_score",
        "source_spec_score",
        "m1_spec_score",
        "entry_adverse_spec_score",
        "same_route_peer_delta",
        "same_symbol_session_side_targetstop_delta",
        "neighbor_directional_close_vs_permuted",
    )
    for field in fields:
        value = _to_float(row.get(field))
        if value is not None:
            return value, field
    return None, ""


def _target_stop_order_class(row: dict[str, Any]) -> str:
    joined = " ".join(
        _upper(row.get(field))
        for field in (
            "target_stop_result",
            "entry_target_stop_balance_class",
            "exact_failure_cause",
            "sealed_proxy_class",
            "implementation_implication_class",
        )
    )
    if "STOP_FIRST" in joined:
        return "STOP_FIRST_PROXY_DOMINANT"
    if "TARGET_FIRST" in joined or "ALL_POSITIVE" in joined:
        return "TARGET_FIRST_PROXY_DOMINANT"
    if "SOURCE" in joined and ("UNAVAILABLE" in joined or "ACQUIRE" in joined or "REPAIR" in joined):
        return "TARGET_STOP_ORDER_NOT_SOURCE_BOUND"
    if "AMBIGUOUS" in joined or "STRADDLES" in joined or "INTERVAL" in joined:
        return "TARGET_STOP_AMBIGUOUS_OR_MIXED"
    return ""


def _proxy_class(row: dict[str, Any], proxy: float | None, target_stop_class: str) -> str:
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


def _source_repair_required(row: dict[str, Any]) -> bool:
    if row.get("source_exact_acquisition_required") is True:
        return True
    joined = " ".join(
        _upper(row.get(field))
        for field in (
            "source_requirement",
            "source_acquisition_cost_cap_requirement_class",
            "exact_source_requirement_status",
            "source_repairability_class",
            "source_repair_route_class",
            "repair_feasibility_class",
            "source_stress_action_class",
            "action_class",
            "deep_class",
        )
    )
    return any(token in joined for token in ("SOURCE_REPAIR", "SOURCE_ACQUISITION", "ACQUIRE_EXACT", "UNAVAILABLE"))


def _decision(row: dict[str, Any], proxy: float | None, target_stop_class: str) -> str:
    joined = " ".join(
        _upper(row.get(field))
        for field in (
            "action_class",
            "action_family",
            "implementation_primary_action_class",
            "immediate_action_class",
            "branch_router_application_class",
            "branch_primary_followup_class",
            "primary_export_family",
            "primary_export_class",
            "replay_builder_class",
            "work_unit_status",
            "implementation_implication",
            "implementation_implication_class",
            "positive_challenger_class",
            "positive_modifier_class",
        )
    )
    if target_stop_class == "STOP_FIRST_PROXY_DOMINANT":
        return "AVOID"
    if any(token in joined for token in ("AVOID", "FAILURE_FILTER", "NEGATIVE_SCORE", "REJECTED_NONPOSITIVE")):
        return "AVOID"
    if "ENTRY" in joined and "REDESIGN" in joined:
        return "AVOID"
    if _source_repair_required(row) and not (
        target_stop_class == "TARGET_FIRST_PROXY_DOMINANT" and proxy is not None and proxy > 0
    ):
        return "MIXED"
    if any(token in joined for token in ("POSITIVE", "CHALLENGER", "FOLLOW", "SCORER", "TARGET_STABLE")):
        return "FOLLOW" if proxy is None or proxy >= -0.05 else "MIXED"
    if proxy is not None and proxy > 0 and target_stop_class != "TARGET_STOP_ORDER_NOT_SOURCE_BOUND":
        return "FOLLOW"
    if proxy is not None and proxy < -0.05:
        return "AVOID"
    return "MIXED"


def _source_role(decision: str, source_repair_required: bool) -> str:
    if source_repair_required:
        return "branch_impl_replay_source_repair_guard"
    if decision == "AVOID":
        return "branch_impl_replay_avoid_guard"
    if decision == "FOLLOW":
        return "branch_impl_replay_follow_pressure"
    return "branch_impl_replay_context_guard"


def _action_class(decision: str, source_repair_required: bool) -> str:
    if source_repair_required:
        return "branch_impl_replay_source_repair_guard"
    if decision == "AVOID":
        return "branch_impl_replay_avoid_filter"
    if decision == "FOLLOW":
        return "branch_impl_replay_follow_scorer"
    return "branch_impl_replay_context_guard"


def _r_evidence_class(decision: str, source_repair_required: bool, target_stop_class: str) -> str:
    if source_repair_required:
        return "SOURCE_REPAIR_FOR_EXACT_R"
    if target_stop_class == "STOP_FIRST_PROXY_DOMINANT":
        return "BRANCH_IMPLEMENTATION_REPLAY_STOP_FIRST_AVOID"
    if decision == "FOLLOW":
        return "BRANCH_IMPLEMENTATION_REPLAY_POSITIVE_PROXY"
    if decision == "AVOID":
        return "BRANCH_IMPLEMENTATION_REPLAY_NEGATIVE_OR_REDESIGN"
    return "BRANCH_IMPLEMENTATION_REPLAY_CONTEXT"


def _metric_payload(
    row: dict[str, Any],
    *,
    proxy_value: float | None,
    proxy_field: str,
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    if proxy_value is not None:
        metrics["proxy_score"] = _metric_from_scalar(proxy_value, source_field=proxy_field)
        metrics["cost_adjusted_simulated_r"] = _metric_from_scalar(
            _first_numeric(row.get("rstyle_midpoint_mean"), proxy_value),
            source_field="rstyle_midpoint_mean_or_proxy",
        )
    lower = _to_float(row.get("rstyle_lower_mean"))
    upper = _to_float(row.get("rstyle_upper_mean"))
    if lower is not None and upper is not None:
        metrics["stress_simulated_r"] = _metric_from_scalar(
            (lower + upper) / 2,
            source_field="rstyle_lower_upper_mean",
        )
    effective_n = _first_numeric(
        row.get("unique_event_or_route_ids"),
        row.get("event_count"),
        row.get("material_joined_rows"),
        row.get("same_route_peer_count"),
        row.get("branch_count"),
        row.get("rows"),
    )
    if effective_n is not None:
        metrics["effective_n"] = _metric_from_scalar(
            effective_n,
            source_field="branch_impl_effective_n_proxy",
        )
    return {key: value for key, value in metrics.items() if value is not None}


def _build_runtime_row(
    *,
    row: dict[str, Any],
    path: Path,
    line_no: int,
    source_hash: str,
    file_sha256: str,
) -> dict[str, Any]:
    component = _source_component(path)
    route_candidate_id = _norm(row.get("route_candidate_id") or row.get("candidate_id"))
    proxy_value, proxy_field = _metric_value(row)
    target_stop_class = _target_stop_order_class(row)
    proxy_class = _proxy_class(row, proxy_value, target_stop_class)
    source_repair = _source_repair_required(row)
    decision = _decision(row, proxy_value, target_stop_class)
    action_class = _action_class(decision, source_repair)
    source_role = _source_role(decision, source_repair)
    source_path = _path_text(path)
    symbol = _symbol(row)
    side = _side(row)
    event_scope = {
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "route_session": _route_session(row),
        "horizon_id": _horizon_id(row),
        "primitive": _primitive(row),
        "side": side,
        "route_family": "moonshot_branch_implementation_replay",
        "source_component": component,
        "action_class": action_class,
        "entry_variant": _norm(row.get("entry_variant")),
        "target_stop_order_class": target_stop_class,
        "proxy_r_class": proxy_class,
    }
    if family := resolve_vnext_symbol_family(symbol):
        event_scope["symbol_family"] = family
    event_scope = {key: value for key, value in event_scope.items() if value not in (None, "")}
    source_row_id = (
        route_candidate_id
        or _norm(row.get("branch_queue_id"))
        or _norm(row.get("matrix_branch_id"))
        or _norm(row.get("full_outcome_action_id"))
        or f"{path.name}:{line_no}"
    )
    row_id = f"branch_implementation_replay:{component}:{line_no}:{source_row_id}"
    runtime_effect = {
        "FOLLOW": "branch_implementation_replay_follow_pressure",
        "AVOID": "branch_implementation_replay_avoid_filter",
        "MIXED": "branch_implementation_replay_context_or_source_repair_guard",
    }[decision]
    runtime_row = {
        "schema_version": "gtos_vnext_branch_implementation_replay_runtime_row_v1",
        "branch_implementation_replay_runtime_row_id": row_id,
        "row_key": row_id,
        "source_row_id": source_row_id,
        "route_candidate_id": route_candidate_id,
        "symbol": symbol,
        "source_symbol": symbol,
        "route_session": _route_session(row),
        "primitive": _primitive(row),
        "horizon_id": _horizon_id(row),
        "side": side,
        "entry_variant": _norm(row.get("entry_variant")),
        "route_family": "moonshot_branch_implementation_replay",
        "source_component": component,
        "source_group": (
            "branch_impl_source_repair"
            if source_repair
            else f"branch_impl_{decision.casefold()}"
        ),
        "source_role": source_role,
        "source_name": "gtos_vnext_branch_implementation_replay_wave",
        "evidence_family": "gtos_vnext_branch_implementation_replay",
        "system_surface": "branch_implementation_replay_runtime",
        "review_action": decision,
        "decision": decision,
        "action_class": action_class,
        "implementation_action": _norm(
            row.get("implementation_primary_action_class")
            or row.get("immediate_action_class")
            or row.get("action_class")
            or row.get("router_application_action")
            or row.get("work_unit_status")
        ),
        "runtime_effect_now": runtime_effect,
        "runtime_candidate_use_permitted": decision == "FOLLOW",
        "candidate_use_allowed_now": decision in {"FOLLOW", "AVOID"},
        "r_evidence_class": _r_evidence_class(decision, source_repair, target_stop_class),
        "proxy_r_class": proxy_class,
        "target_stop_order_class": target_stop_class,
        "target_stop_result": _norm(row.get("target_stop_result")),
        "source_repair_required": source_repair,
        "source_acquisition_required": source_repair,
        "source_bound": bool(event_scope),
        "source_complete": not source_repair,
        "event_scope": event_scope,
        "r_metrics": _metric_payload(row, proxy_value=proxy_value, proxy_field=proxy_field),
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
            _first_numeric(
                row.get("unique_event_or_route_ids"),
                row.get("material_joined_rows"),
                row.get("event_count"),
                1,
            )
            or 1
        ),
        "branch_result_class": _norm(row.get("branch_result_class")),
        "primary_export_family": _norm(row.get("primary_export_family")),
        "primary_export_class": _norm(row.get("primary_export_class")),
        "immediate_action_class": _norm(row.get("immediate_action_class")),
        "branch_router_application_class": _norm(row.get("branch_router_application_class")),
        "replay_builder_class": _norm(row.get("replay_builder_class")),
        "work_unit_status": _norm(row.get("work_unit_status")),
        "safe_flags": row.get("safe_flags"),
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


def _aggregate_runtime_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        scope = row.get("event_scope") if isinstance(row.get("event_scope"), dict) else {}
        key = (
            row.get("source_component"),
            row.get("source_file_group"),
            row.get("decision"),
            row.get("action_class"),
            row.get("source_role"),
            row.get("r_evidence_class"),
            row.get("route_family"),
            row.get("symbol"),
            row.get("route_session"),
            row.get("side"),
            row.get("primitive"),
            row.get("horizon_id"),
            row.get("entry_variant"),
            row.get("target_stop_order_class"),
            row.get("proxy_r_class"),
        )
        aggregate = grouped.get(key)
        if aggregate is None:
            aggregate = {
                name: value
                for name, value in row.items()
                if name
                not in {
                    "branch_implementation_replay_runtime_row_id",
                    "row_key",
                    "source_row_id",
                    "source_line_no",
                    "declared_origin_line_no",
                    "r_metrics",
                }
            }
            aggregate["event_scope"] = dict(scope)
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
                str(item.get("proxy_r_class") or ""),
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
                    "primitive",
                    "horizon_id",
                    "entry_variant",
                    "target_stop_order_class",
                    "proxy_r_class",
                )
            )
        )[:16]
        row_id = f"branch_implementation_replay:aggregate:{index}:{digest}"
        aggregate["branch_implementation_replay_runtime_row_id"] = row_id
        aggregate["row_key"] = row_id
        samples = aggregate.get("source_row_id_samples") or []
        if samples:
            aggregate["source_row_id"] = samples[0]
        aggregate["declared_origin_line_no"] = aggregate.get("source_line_no_min")
        aggregate["source_line_no"] = aggregate.get("source_line_no_min")
        aggregated_rows.append(
            {name: value for name, value in aggregate.items() if value not in (None, "", {}, [])}
        )
    return aggregated_rows


def build_runtime_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_runtime_rows: list[dict[str, Any]] = []
    source_artifacts: list[dict[str, Any]] = []
    for path, source_hash in _source_paths():
        rows = _read_rows(path)
        file_sha256 = _sha256_file(path)
        before = len(raw_runtime_rows)
        for line_no, row in enumerate(rows, start=1):
            raw_runtime_rows.append(
                _build_runtime_row(
                    row=row,
                    path=path,
                    line_no=line_no,
                    source_hash=source_hash,
                    file_sha256=file_sha256,
                )
            )
        runtime_rows_read = len(raw_runtime_rows) - before
        source_artifacts.append(
            {
                "path": _path_text(path),
                "sha256_or_git_blob": source_hash or file_sha256,
                "file_sha256": file_sha256,
                "rows": len(rows),
                "line_count": _line_count(path),
                "runtime_rows_read": runtime_rows_read,
                "source_component": _source_component(path),
                "source_file_group": _source_file_group(path),
            }
        )

    runtime_rows = _aggregate_runtime_rows(raw_runtime_rows)
    decision_counts = Counter(str(row.get("decision")) for row in runtime_rows)
    component_counts = Counter(str(row.get("source_component")) for row in runtime_rows)
    role_counts = Counter(str(row.get("source_role")) for row in runtime_rows)
    route_family_counts = Counter(str(row.get("route_family")) for row in runtime_rows)
    action_class_counts = Counter(str(row.get("action_class")) for row in runtime_rows)
    r_evidence_counts = Counter(str(row.get("r_evidence_class")) for row in runtime_rows)
    target_stop_counts = Counter(
        str(row.get("target_stop_order_class")) for row in runtime_rows if row.get("target_stop_order_class")
    )
    proxy_counts = Counter(str(row.get("proxy_r_class")) for row in runtime_rows)
    summary = {
        "schema_version": "gtos_vnext_branch_implementation_replay_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(runtime_rows),
        "raw_runtime_row_count": len(raw_runtime_rows),
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
        print("branch implementation replay runtime outputs are stale:", file=sys.stderr)
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
