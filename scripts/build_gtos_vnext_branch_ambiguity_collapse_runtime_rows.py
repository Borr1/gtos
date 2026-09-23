#!/usr/bin/env python3
"""Build runtime rows for CP280 branch ambiguity-collapse evidence."""

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
WAVE_ID = "WAVE_BRANCH_AMBIGUITY_COLLAPSE_RUNTIME"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_BRANCH_AMBIGUITY_COLLAPSE_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_BRANCH_AMBIGUITY_COLLAPSE_RUNTIME_SUMMARY_{DATE}.json"

RUNTIME_SUFFIXES = {".jsonl", ".json", ".csv"}
COUNTABLE_SUFFIXES = {".jsonl", ".json", ".md", ".txt", ".csv", ".py"}
OUTPUT_NAME_TOKENS = (
    "gtos_vnext_branch_ambiguity_collapse_runtime_rows",
    "gtos_vnext_branch_ambiguity_collapse_runtime_summary",
)
ROW_BEARING_TOKENS = (
    "ambiguity_collapse_branch_classification_ledger",
    "ambiguity_collapse_bucket_ledger",
    "ambiguity_collapse_interval_preservation_ledger",
    "ambiguity_collapse_m15_same_bar_classification_ledger",
    "ambiguity_collapse_ordering_route_ledger",
    "ambiguity_collapse_targetstop_na_binding_ledger",
    "cause_implementation_matrix_ambiguity_collapse_ledger",
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() == "none" else text


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
    prefix = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_"
    if name.startswith(prefix):
        name = name[len(prefix):]
    suffix = "_LEDGER_2026-05-16.jsonl"
    if name.endswith(suffix):
        name = name[: -len(suffix)]
    return name.lower()


def _row_kind(path: Path) -> str:
    name = path.name.casefold()
    if "bucket" in name:
        return "bucket"
    if "interval_preservation" in name:
        return "interval"
    if "m15_same_bar" in name:
        return "m15_same_bar"
    if "ordering_route" in name:
        return "ordering"
    if "targetstop_na_binding" in name:
        return "targetstop_na"
    if "cause_implementation_matrix" in name:
        return "cause_matrix"
    return "branch"


def _route_parts(row: dict[str, Any]) -> tuple[str, str, str, str]:
    route_candidate_id = _norm(row.get("route_candidate_id"))
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
    return _norm(row.get("route_session") or route_session)


def _primitive(row: dict[str, Any]) -> str:
    _symbol_part, _session, primitive, _horizon = _route_parts(row)
    return primitive


def _horizon_id(row: dict[str, Any]) -> str:
    _symbol_part, _session, _primitive, horizon = _route_parts(row)
    raw = _norm(row.get("horizon_id") or row.get("horizon") or horizon)
    if raw and raw.isdigit():
        return f"h{raw}"
    return raw


def _side(row: dict[str, Any]) -> str:
    value = _upper(row.get("side") or row.get("direction"))
    if value in {"LONG", "SHORT"}:
        return value
    primitive = _primitive(row).casefold()
    if "sweep_low" in primitive or "close_breakout_up" in primitive:
        return "LONG"
    if "sweep_high" in primitive or "close_breakout_down" in primitive:
        return "SHORT"
    return ""


def _target_stop_order_class(row: dict[str, Any]) -> str:
    result = _upper(row.get("target_stop_result"))
    ambiguity = " ".join(
        _upper(row.get(field))
        for field in (
            "branch_result_class",
            "ambiguity_collapse_class",
            "m15_same_bar_class",
            "interval_preservation_class",
            "ordering_collapse_route",
            "targetstop_na_binding_class",
            "target_stop_contract_id",
            "binding_repair_status",
            "row_type",
        )
    )
    if "STOP_FIRST" in result:
        return "STOP_FIRST_PROXY_DOMINANT"
    if "TARGET_FIRST" in result:
        return "TARGET_FIRST_PROXY_DOMINANT"
    if (
        "NO_FILL" in result
        or "UNFILLED" in result
        or "NO_TARGET_STOP" in result
        or "ENTRY_PROVENANCE" in result
        or "TARGETSTOP_NA" in ambiguity
    ):
        return "TARGET_STOP_ORDER_NOT_SOURCE_BOUND"
    if "AMBIG" in result or "AMBIG" in ambiguity or "STRADDLES_ZERO" in ambiguity:
        return "TARGET_STOP_AMBIGUOUS_OR_MIXED"
    return "TARGET_STOP_AMBIGUOUS_OR_MIXED"


def _source_repair_required(row: dict[str, Any], target_stop_order_class: str) -> bool:
    text = " ".join(
        _upper(row.get(field))
        for field in (
            "source_repair_route_class",
            "source_repairability_class",
            "repair_feasibility_class",
            "exact_spread_repairability_class",
            "source_confidence_status",
            "targetstop_na_binding_class",
            "target_stop_contract_id",
            "binding_repair_status",
            "row_type",
        )
    )
    if target_stop_order_class == "TARGET_STOP_ORDER_NOT_SOURCE_BOUND":
        return True
    return (
        "SOURCE_REPAIR_BLOCKED" in text
        or "SOURCE_REPAIR_OR_PROXY_REQUIRED" in text
        or "STRESS_ONLY" in text
        or "TARGETSTOP_NA" in text
        or "ENTRY_PROVENANCE_ONLY" in text
    )


def _decision(row: dict[str, Any], target_stop_order_class: str) -> str:
    if target_stop_order_class == "STOP_FIRST_PROXY_DOMINANT":
        return "AVOID"
    if target_stop_order_class == "TARGET_FIRST_PROXY_DOMINANT":
        return "FOLLOW"
    return "MIXED"


def _source_component(kind: str, decision: str, source_repair_required: bool) -> str:
    if source_repair_required and decision == "MIXED":
        return "gtos_branch_ambiguity_source_repair"
    return f"gtos_branch_ambiguity_{kind}"


def _action_class(decision: str, source_repair_required: bool) -> str:
    if decision == "AVOID":
        return "branch_ambiguity_stop_first_avoid_filter"
    if decision == "FOLLOW":
        return "branch_ambiguity_target_first_follow_scorer"
    if source_repair_required:
        return "branch_ambiguity_source_repair_guard"
    return "branch_ambiguity_target_stop_context_guard"


def _source_role(decision: str, source_repair_required: bool) -> str:
    if decision == "AVOID":
        return "branch_ambiguity_stop_first_avoid_guard"
    if decision == "FOLLOW":
        return "branch_ambiguity_target_first_follow_pressure"
    if source_repair_required:
        return "source_repair_execution_plan"
    return "branch_ambiguity_interval_context_guard"


def _source_group(decision: str, source_repair_required: bool) -> str:
    if decision == "AVOID":
        return "branch_ambiguity_stop_first_avoid"
    if decision == "FOLLOW":
        return "branch_ambiguity_target_first_follow"
    if source_repair_required:
        return "source_repair_proof"
    return "branch_ambiguity_context_guard"


def _r_evidence_class(
    decision: str,
    target_stop_order_class: str,
    source_repair_required: bool,
) -> str:
    if decision == "AVOID":
        return "BRANCH_AMBIGUITY_STOP_FIRST_PROXY"
    if decision == "FOLLOW":
        return "BRANCH_AMBIGUITY_TARGET_FIRST_PROXY"
    if source_repair_required:
        return "SOURCE_REPAIR_FOR_EXACT_R"
    if target_stop_order_class == "TARGET_STOP_AMBIGUOUS_OR_MIXED":
        return "BRANCH_AMBIGUITY_TARGET_STOP_AMBIGUOUS"
    return "BRANCH_AMBIGUITY_CONTEXT"


def _proxy_r_class(decision: str, target_stop_order_class: str) -> str:
    if decision == "AVOID":
        return "STRONG_NEGATIVE_PROXY_R"
    if decision == "FOLLOW":
        return "STRONG_POSITIVE_PROXY_R"
    if target_stop_order_class == "TARGET_STOP_ORDER_NOT_SOURCE_BOUND":
        return "SOURCE_REPAIR_PROXY_R"
    return "MIXED_PROXY_R"


def _implementation_action(decision: str, source_repair_required: bool) -> str:
    if decision == "AVOID":
        return "AVOID_CURRENT_ENTRY_STOP_FIRST_PROXY"
    if decision == "FOLLOW":
        return "KEEP_POSITIVE_PROXY_R_WITH_CONTROL"
    if source_repair_required:
        return "SOURCE_GEOMETRY_REPAIR_OR_GUARD_BINDING_REQUIRED"
    return "ORDERING_OR_INTERVAL_COLLAPSE_BEFORE_DIRECTIONAL_USE"


def _runtime_effect(decision: str, source_repair_required: bool) -> str:
    if decision == "AVOID":
        return "branch_ambiguity_stop_first_avoid_filter"
    if decision == "FOLLOW":
        return "branch_ambiguity_target_first_follow_pressure"
    if source_repair_required:
        return "branch_ambiguity_source_repair_guard"
    return "branch_ambiguity_target_stop_context_guard"


def _signed_proxy_value(row: dict[str, Any], decision: str) -> float | None:
    value = _first_numeric(
        row.get("rstyle_midpoint_mean"),
        row.get("rstyle_lower_mean"),
        row.get("rstyle_upper_mean"),
    )
    if value is not None:
        return value
    if decision == "AVOID":
        return -1.0
    if decision == "FOLLOW":
        return 1.0
    return None


def _metric(value: float | None, *, source_field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "sum": round(float(value), 12),
        "mean": round(float(value), 12),
        "count": 1,
        "match_rows_with_metric": 1,
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _source_rows_represented(row: dict[str, Any]) -> int:
    value = _first_numeric(
        row.get("unique_event_or_route_ids"),
        row.get("rstyle_interval_rows"),
        row.get("m15_event_id_count"),
        row.get("ambiguous_ordering_rows"),
        row.get("branch_count"),
        1,
    )
    if value is not None:
        return max(1, int(value))
    counted_payloads = (
        row.get("signature_scope_status_counts"),
        row.get("m1_first_touch_status_counts"),
        row.get("touch_class_counts"),
        row.get("m15_same_bar_status_counts"),
    )
    for payload in counted_payloads:
        if isinstance(payload, dict):
            total = sum(int(value or 0) for value in payload.values())
            if total > 0:
                return total
    return 1


def _runtime_row(
    row: dict[str, Any],
    *,
    source_path: Path,
    source_hash: str,
    source_line_no: int,
    source_file_sha256: str,
) -> dict[str, Any] | None:
    kind = _row_kind(source_path)
    target_stop_order_class = _target_stop_order_class(row)
    source_repair_required = _source_repair_required(row, target_stop_order_class)
    decision = _decision(row, target_stop_order_class)
    source_component = _source_component(kind, decision, source_repair_required)
    route_family = "moonshot_branch_ambiguity_collapse"
    action_class = _action_class(decision, source_repair_required)
    proxy_class = _proxy_r_class(decision, target_stop_order_class)
    source_rows_represented = _source_rows_represented(row)

    route_candidate_id = _norm(row.get("route_candidate_id"))
    row_id_seed = (
        route_candidate_id
        or _norm(row.get("bucket_id"))
        or _norm(row.get("ambiguity_collapse_id"))
        or _norm(row.get("ordering_route_id"))
        or f"{source_path.name}:{source_line_no}"
    )
    runtime_row_id = f"branch_ambiguity_collapse:{kind}:{source_line_no}:{row_id_seed}"

    symbol = _symbol(row)
    source_symbol = _norm(row.get("source_symbol") or symbol)
    route_session = _route_session(row)
    side = _side(row)
    horizon_id = _horizon_id(row)
    primitive = _primitive(row)
    event_scope = {
        "symbol": symbol,
        "source_symbol": source_symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol),
        "route_session": route_session,
        "side": side,
        "horizon_id": horizon_id,
        "primitive": primitive,
        "route_family": route_family,
        "action_class": action_class,
        "entry_variant": _norm(row.get("entry_variant")),
        "proxy_r_class": proxy_class,
        "target_stop_order_class": target_stop_order_class,
    }
    event_scope = {key: value for key, value in event_scope.items() if value not in (None, "")}
    if kind == "bucket" or not any((symbol, route_session, side, horizon_id, primitive)):
        event_scope = {}

    proxy_value = _signed_proxy_value(row, decision)
    metrics: dict[str, Any] = {}
    if proxy_metric := _metric(proxy_value, source_field="rstyle_midpoint_mean"):
        metrics["proxy_score"] = proxy_metric
        metrics["cost_adjusted_simulated_r"] = proxy_metric
    lower = _to_float(row.get("rstyle_lower_mean"))
    upper = _to_float(row.get("rstyle_upper_mean"))
    if lower is not None or upper is not None:
        stress_value = sum(value for value in (lower, upper) if value is not None) / (
            int(lower is not None) + int(upper is not None)
        )
        if stress_metric := _metric(stress_value, source_field="rstyle_lower_upper_mean"):
            metrics["stress_simulated_r"] = stress_metric
    if effective_n := _metric(float(source_rows_represented), source_field="source_rows_represented"):
        metrics["effective_n"] = effective_n

    output = {
        "schema_version": "gtos_vnext_branch_ambiguity_collapse_runtime_row_v1",
        "branch_ambiguity_collapse_runtime_row_id": runtime_row_id,
        "row_key": runtime_row_id,
        "source_row_id": row_id_seed,
        "source_line_no": source_line_no,
        "source_artifact": _path_text(source_path),
        "source_path": _path_text(source_path),
        "declared_origin_artifact": _path_text(source_path),
        "declared_origin_line_no": source_line_no,
        "declared_origin_sha256": source_file_sha256,
        "source_file_sha256": source_file_sha256,
        "source_artifact_sha256": source_file_sha256,
        "source_artifact_hash": source_hash or source_file_sha256,
        "source_path_sha256": _sha256_text(_path_text(source_path)),
        "source_file_group": _source_file_group(source_path),
        "source_kind": kind,
        "source_rows_represented": source_rows_represented,
        "source_name": "gtos_vnext_branch_ambiguity_collapse_wave",
        "evidence_family": "gtos_vnext_branch_ambiguity_collapse",
        "source_group": _source_group(decision, source_repair_required),
        "source_role": _source_role(decision, source_repair_required),
        "system_surface": "branch_ambiguity_target_stop_ordering_runtime",
        "source_component": source_component,
        "route_family": route_family,
        "review_action": decision,
        "decision": decision,
        "action_class": action_class,
        "implementation_action": _implementation_action(decision, source_repair_required),
        "r_evidence_class": _r_evidence_class(
            decision,
            target_stop_order_class,
            source_repair_required,
        ),
        "runtime_effect_now": _runtime_effect(decision, source_repair_required),
        "candidate_use_allowed_now": decision in {"FOLLOW", "AVOID"},
        "runtime_candidate_use_permitted": decision in {"FOLLOW", "AVOID"},
        "source_bound": not source_repair_required or decision in {"FOLLOW", "AVOID"},
        "source_complete": decision in {"FOLLOW", "AVOID"},
        "source_repair_required": source_repair_required,
        "source_acquisition_required": source_repair_required,
        "target_stop_order_class": target_stop_order_class,
        "proxy_r_class": proxy_class,
        "route_candidate_id": route_candidate_id,
        "symbol": symbol,
        "source_symbol": source_symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol),
        "route_session": route_session,
        "side": side,
        "horizon_id": horizon_id,
        "primitive": primitive,
        "entry_variant": _norm(row.get("entry_variant")),
        "branch_result_class": _norm(row.get("branch_result_class")),
        "target_stop_result": _norm(row.get("target_stop_result")),
        "ambiguity_collapse_class": _norm(row.get("ambiguity_collapse_class")),
        "m15_same_bar_class": _norm(row.get("m15_same_bar_class")),
        "m1_existing_class": _norm(row.get("m1_existing_class")),
        "ordering_collapse_route": _norm(row.get("ordering_collapse_route")),
        "source_repair_route_class": _norm(row.get("source_repair_route_class")),
        "source_repairability_class": _norm(row.get("source_repairability_class")),
        "repair_feasibility_class": _norm(row.get("repair_feasibility_class")),
        "event_scope": event_scope,
        "r_metrics": metrics,
    }
    return {key: value for key, value in output.items() if value not in (None, "", {})}


def build_runtime_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    runtime_rows: list[dict[str, Any]] = []
    source_artifacts: list[dict[str, Any]] = []
    wave_source_rows_counted = 0

    for source_path, source_hash in _source_paths():
        source_file_sha256 = _sha256_file(source_path)
        rows = _read_rows(source_path) if source_path.suffix.lower() in RUNTIME_SUFFIXES else []
        line_count = _line_count(source_path) or len(rows)
        wave_source_rows_counted += int(line_count or 0)
        runtime_rows_read = 0
        for index, row in enumerate(rows, start=1):
            runtime_row = _runtime_row(
                row,
                source_path=source_path,
                source_hash=source_hash,
                source_line_no=index,
                source_file_sha256=source_file_sha256,
            )
            if runtime_row is None:
                continue
            runtime_rows.append(runtime_row)
            runtime_rows_read += 1
        source_artifacts.append(
            {
                "path": _path_text(source_path),
                "sha256_or_git_blob": source_hash or source_file_sha256,
                "file_sha256": source_file_sha256,
                "rows": int(line_count or 0),
                "runtime_rows_read": runtime_rows_read,
            }
        )

    runtime_rows.sort(
        key=lambda row: (
            str(row.get("source_artifact") or ""),
            int(row.get("source_line_no") or 0),
            str(row.get("branch_ambiguity_collapse_runtime_row_id") or ""),
        )
    )
    summary = _build_summary(runtime_rows, source_artifacts, wave_source_rows_counted)
    return runtime_rows, summary


def _counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field))).items()))


def _build_summary(
    rows: list[dict[str, Any]],
    source_artifacts: list[dict[str, Any]],
    wave_source_rows_counted: int,
) -> dict[str, Any]:
    return {
        "schema_version": "gtos_vnext_branch_ambiguity_collapse_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(int(row.get("source_rows_represented") or 0) for row in rows),
        "wave_source_artifact_count": len(source_artifacts),
        "wave_source_rows_counted": wave_source_rows_counted,
        "row_count_unknown_source_artifact_count": sum(1 for item in source_artifacts if not item.get("rows")),
        "decision_counts": _counter(rows, "decision"),
        "source_component_counts": _counter(rows, "source_component"),
        "source_role_counts": _counter(rows, "source_role"),
        "source_group_counts": _counter(rows, "source_group"),
        "r_evidence_class_counts": _counter(rows, "r_evidence_class"),
        "action_class_counts": _counter(rows, "action_class"),
        "route_family_counts": _counter(rows, "route_family"),
        "target_stop_order_class_counts": _counter(rows, "target_stop_order_class"),
        "proxy_r_class_counts": _counter(rows, "proxy_r_class"),
        "symbol_counts": _counter(rows, "symbol"),
        "route_session_counts": _counter(rows, "route_session"),
        "side_counts": _counter(rows, "side"),
        "horizon_counts": _counter(rows, "horizon_id"),
        "source_artifacts": source_artifacts,
        "sample_runtime_row_ids": [
            row["branch_ambiguity_collapse_runtime_row_id"]
            for row in rows[:20]
            if row.get("branch_ambiguity_collapse_runtime_row_id")
        ],
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _check_current_files(rows: list[dict[str, Any]], summary: dict[str, Any]) -> bool:
    try:
        current_rows = [
            json.loads(line)
            for line in OUTPUT_ROWS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        current_summary = json.loads(OUTPUT_SUMMARY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return current_rows == rows and current_summary == summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if outputs are stale")
    args = parser.parse_args(argv)

    rows, summary = build_runtime_rows()
    if args.check:
        if not _check_current_files(rows, summary):
            print("branch ambiguity-collapse runtime outputs are stale", file=sys.stderr)
            return 1
        return 0
    _write_jsonl(OUTPUT_ROWS, rows)
    _write_json(OUTPUT_SUMMARY, summary)
    print(
        json.dumps(
            {
                "runtime_rows": len(rows),
                "runtime_source_rows_represented": summary[
                    "runtime_source_rows_represented"
                ],
                "wave_source_artifacts": summary["wave_source_artifact_count"],
                "wave_source_rows_counted": summary["wave_source_rows_counted"],
                "output_rows": _path_text(OUTPUT_ROWS),
                "output_summary": _path_text(OUTPUT_SUMMARY),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
