#!/usr/bin/env python3
"""Build runtime rows for target/stop ordering and execution-scoring evidence."""

from __future__ import annotations

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
WAVE_ID = "WAVE_TARGET_STOP_ORDERING_EXECUTION_SCORING_RUNTIME"
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_TARGET_STOP_ORDERING_EXECUTION_SCORING_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_TARGET_STOP_ORDERING_EXECUTION_SCORING_RUNTIME_SUMMARY_{DATE}.json"
)

M15_TARGET_FIRST_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_M15_BOUNDED_ORDERING_DETAIL_"
    "TARGET_FIRST_CHALLENGER_LEDGER_2026-05-16.jsonl"
)
NEXT_ACCEPTED_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_"
    "ACCEPTED_LEDGER_2026-05-16.jsonl"
)
NEXT_REPAIR_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_"
    "REPAIR_LEDGER_2026-05-16.jsonl"
)
NEXT_SOURCE_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_"
    "SOURCE_LEDGER_2026-05-16.jsonl"
)
PARAMETER_M15_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_"
    "M15_BOUNDS_SELECTOR_LEDGER_2026-05-16.jsonl"
)
PARAMETER_M1_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_"
    "M1_SUPPORT_CONFLICT_SELECTOR_LEDGER_2026-05-16.jsonl"
)
PARAMETER_POSITIVE_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_"
    "POSITIVE_REPLAY_REPAIR_LEDGER_2026-05-16.jsonl"
)

PRIMARY_SOURCE_NAMES = (
    M15_TARGET_FIRST_SOURCE,
    NEXT_ACCEPTED_SOURCE,
    NEXT_REPAIR_SOURCE,
    NEXT_SOURCE_SOURCE,
    PARAMETER_M15_SOURCE,
    PARAMETER_M1_SOURCE,
    PARAMETER_POSITIVE_SOURCE,
)
SUPPORT_SOURCE_NAMES = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_BINDING_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_BRANCH_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_BUCKET_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_ENTRY_ADVERSE_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_FAMILY_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_M15_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_M1_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_POSITIVE_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_QUESTION_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_BINDING_PRESERVATION_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_BRANCH_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_BUCKET_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_FAMILY_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_QUESTION_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_PARAMETER_EXECUTION_SCORING_PACKET_SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl",
)
ALL_SOURCE_NAMES = PRIMARY_SOURCE_NAMES + SUPPORT_SOURCE_NAMES
ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "side",
    "entry_variant",
    "target_stop_order_class",
    "source_component",
)


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


@lru_cache(maxsize=None)
def _sha256_file_cached(path_text: str) -> str:
    digest = hashlib.sha256()
    with Path(path_text).open("rb") as handle:
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
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def _source_path(name: str) -> Path:
    return MOONSHOT_ROUTE / name


def _text_blob(row: dict[str, Any]) -> str:
    keys = (
        "branch_decision_class",
        "branch_result_binary",
        "branch_result_class",
        "exact_failure_cause",
        "exact_success_cause",
        "failure_decision",
        "integrated_evidence_action",
        "integrated_evidence_state",
        "m15_builder_next_action",
        "m15_builder_result_status",
        "m15_decision_id",
        "m15_detail_status",
        "m15_selector_action",
        "m15_selector_execution_status",
        "m15_selector_policy",
        "m15_selector_score_class",
        "m1_branch_result_class",
        "m1_selector_action",
        "m1_selector_execution_status",
        "m1_selector_policy",
        "m1_selector_score_class",
        "m1_support_resolution_class",
        "next_layer_branch_action",
        "next_layer_branch_status",
        "next_same_resource_action",
        "ordering_deep_action_class",
        "positive_challenger_class",
        "positive_deep_action_class",
        "positive_selector_action",
        "positive_selector_execution_status",
        "positive_selector_policy",
        "positive_selector_score_class",
        "primary_export_family",
        "sealed_proxy_class",
        "source_deep_action_class",
        "source_repair_route_class",
        "source_stress_action_class",
        "success_decision",
        "target_stop_result",
        "upstream_builder_result_status",
    )
    return " ".join(_norm(row.get(key)).upper() for key in keys)


def _source_kind(path: Path) -> str:
    name = path.name.upper()
    if "M15_BOUNDED_ORDERING_DETAIL" in name:
        return "m15_bounded_ordering_target_first"
    if "NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_ACCEPTED" in name:
        return "next_layer_accepted_execution_detail"
    if "NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_REPAIR" in name:
        return "next_layer_repair_execution_detail"
    if "NEXT_LAYER_EVIDENCE_EXECUTION_PACKET_SOURCE" in name:
        return "next_layer_source_repair_detail"
    if "M15_BOUNDS_SELECTOR" in name:
        return "parameter_m15_bounds_selector"
    if "M1_SUPPORT_CONFLICT_SELECTOR" in name:
        return "parameter_m1_support_selector"
    if "POSITIVE_REPLAY_REPAIR" in name:
        return "parameter_positive_replay_repair"
    return "target_stop_ordering_support"


def _source_component_for_kind(source_kind: str, row: dict[str, Any]) -> str:
    source_kind_lower = source_kind.casefold()
    blob = _text_blob(row)
    target_result = _norm(row.get("target_stop_result")).upper()
    if source_kind == "m15_bounded_ordering_target_first":
        return "target_stop_ordering_target_first_follow"
    if "source" in source_kind_lower:
        return "target_stop_ordering_source_repair"
    if "STOP_FIRST" in target_result or "STOP_FIRST" in blob:
        return "target_stop_ordering_stop_first_avoid"
    if "NO_FILL" in blob or "UNFILLED" in blob:
        return "target_stop_ordering_nofill_avoid"
    if "m15" in source_kind_lower:
        score = _score(row)
        return (
            "target_stop_ordering_m15_bounds_follow"
            if score is not None and score > 0
            else "target_stop_ordering_m15_bounds_avoid"
        )
    if "m1" in source_kind_lower:
        return "target_stop_ordering_m1_support_follow"
    if "positive" in source_kind_lower:
        score = _score(row)
        return (
            "target_stop_ordering_positive_replay_follow"
            if score is not None and score > 0
            else "target_stop_ordering_positive_replay_avoid"
        )
    return "target_stop_ordering_context_guard"


def _score(row: dict[str, Any]) -> float | None:
    for key in (
        "integrated_evidence_score",
        "m15_selector_score",
        "m1_selector_score",
        "positive_selector_score",
        "positive_adjusted_midpoint",
        "midpoint_proxy",
        "target_first_bound_proxy",
        "stop_first_bound_proxy",
        "source_selector_score",
    ):
        value = _to_float(row.get(key))
        if value is not None:
            return value
    return None


def _decision_shape(
    row: dict[str, Any],
    *,
    source_kind: str,
) -> tuple[str, str, str, str, str, str, str]:
    source_kind_lower = source_kind.casefold()
    blob = _text_blob(row)
    target_result = _norm(row.get("target_stop_result")).upper()
    component = _source_component_for_kind(source_kind, row)
    score = _score(row)
    source_repair = any(
        token in blob
        for token in (
            "SOURCE_SELECTOR_NONPOSITIVE_OR_REPAIR_FIRST",
            "SOURCE_UNAVAILABLE_ACQUIRE_OR_STRESS",
            "SOURCE_REJECTED_EXACT_SOURCE_REPAIR_REQUIRED",
            "SOURCE_LOW_HIGH_BOUNDS_REPAIR_REQUIRED",
            "SOURCE_EXACT_REPAIR",
            "SOURCE_REPAIR",
            "EXACT_SOURCE_REPAIR",
            "EXACT_SOURCE_QUEUED",
            "EXACT_SPREAD_UNAVAILABLE",
            "LOW_HIGH_STRESS",
            "ACQUIRE_SOURCE",
            "SOURCE_OR_STRESS",
        )
    ) or component == "target_stop_ordering_source_repair"
    stop_or_nofill = any(
        token in blob or token in target_result
        for token in (
            "STOP_FIRST",
            "NO_FILL",
            "UNFILLED",
            "AVOID_OR_REDESIGN",
            "RETEST_REDESIGN_OR_AVOID_FILTER_QUEUE",
        )
    )

    if source_repair and "source" in source_kind_lower:
        return (
            "MIXED",
            "target_stop_ordering_source_repair",
            "target_stop_ordering_source_repair_guard",
            "SOURCE_REPAIR_FOR_EXACT_R",
            "source_repair_proof",
            "source_repair_execution_plan",
            "source_repair_proof",
        )

    if stop_or_nofill or (score is not None and score < 0):
        return (
            "AVOID",
            component,
            "target_stop_ordering_stop_first_avoid_filter",
            "TARGET_STOP_ORDERING_STOP_FIRST_AVOID",
            "target_stop_ordering_execution_guard",
            "target_stop_ordering_stop_first_avoid_guard",
            "target_stop_ordering_execution_guard",
        )

    if score is not None and score > 0:
        evidence_class = "TARGET_STOP_ORDERING_TARGET_FIRST_FOLLOW"
        if "m15" in source_kind_lower and source_kind != "m15_bounded_ordering_target_first":
            evidence_class = "TARGET_STOP_ORDERING_M15_BOUNDS_FOLLOW"
        elif "m1" in source_kind_lower:
            evidence_class = "TARGET_STOP_ORDERING_M1_SUPPORT_FOLLOW"
        elif "positive" in source_kind_lower:
            evidence_class = "TARGET_STOP_ORDERING_POSITIVE_REPLAY_FOLLOW"
        return (
            "FOLLOW",
            component,
            "target_stop_ordering_follow_scorer",
            evidence_class,
            "target_stop_ordering_execution_scoring",
            "target_stop_ordering_target_first_follow",
            "target_stop_ordering_execution_scoring",
        )

    return (
        "MIXED",
        component,
        "target_stop_ordering_context_guard",
        "TARGET_STOP_ORDERING_CONTEXT_GUARD",
        "context_guard_input",
        "target_stop_ordering_context_guard",
        "context_guard_input",
    )


def _proxy_r_class(row: dict[str, Any], decision: str) -> str:
    score = _score(row)
    if decision == "AVOID":
        return "STRONG_NEGATIVE_PROXY_R"
    if decision == "FOLLOW":
        if score is None:
            return "POSITIVE_PROXY_R"
        if score >= 0.35:
            return "STRONG_POSITIVE_PROXY_R"
        if score > 0:
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


def _score_field(row: dict[str, Any]) -> tuple[str, float] | None:
    for key in (
        "integrated_evidence_score",
        "m15_selector_score",
        "m1_selector_score",
        "positive_selector_score",
        "positive_adjusted_midpoint",
        "midpoint_proxy",
        "target_first_bound_proxy",
        "stop_first_bound_proxy",
        "source_selector_score",
    ):
        value = _to_float(row.get(key))
        if value is not None:
            return key, value
    return None


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
    if decision == "AVOID" and score > 0:
        score = -abs(score)
    metrics["proxy_score"] = _metric_from_scalar(score, field)
    metrics["cost_adjusted_simulated_r"] = _metric_from_scalar(score, field)
    metrics["stress_simulated_r"] = _metric_from_scalar(score, field)
    return metrics


def _source_row_id(row: dict[str, Any], path: Path, line_no: int) -> str:
    for key in (
        "m15_bounded_ordering_branch_detail_id",
        "next_layer_accepted_id",
        "next_layer_repair_id",
        "source_evidence_detail_id",
        "m15_selector_execution_id",
        "m1_selector_execution_id",
        "positive_selector_execution_id",
        "branch_queue_id",
        "matrix_branch_id",
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
    symbol = _norm(row.get("symbol"))
    session = _norm(row.get("route_session"))
    side = _norm(row.get("side"))
    entry_variant = _norm(row.get("entry_variant"))
    target_stop = _norm(row.get("target_stop_result") or row.get("target_stop_contract_id"))
    source_row_id = _source_row_id(row, path, line_no)
    runtime_row_id = (
        f"target_stop_ordering_execution_scoring:{source_kind}:{line_no}:"
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
        "side": side,
        "entry_variant": entry_variant,
        "target_stop_order_class": target_stop,
        "route_family": "numeric_router",
        "source_component": component,
    }
    event_scope = {key: value for key, value in event_scope.items() if value}
    payload = {
        "target_stop_ordering_execution_scoring_runtime_row_id": runtime_row_id,
        "row_key": runtime_row_id,
        "source_row_id": source_row_id,
        "input_source_row_id": _norm(row.get("source_row_id")),
        "source_name": "gtos_vnext_target_stop_ordering_execution_scoring_wave",
        "evidence_family": "gtos_vnext_target_stop_ordering_execution_scoring",
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
        "side": side,
        "entry_variant": entry_variant,
        "target_stop_order_class": target_stop,
        "source_bound": bool(symbol and session and side and component),
        "source_path": _path_text(path),
        "source_file_sha256": _sha256_file(path),
        "source_line_no": line_no,
        "source_kind": source_kind,
        "source_manifest_hash": _norm(row.get("source_manifest_hash")),
        "route_candidate_id": _norm(row.get("route_candidate_id")),
        "branch_queue_id": _norm(row.get("branch_queue_id")),
        "matrix_branch_id": _norm(row.get("matrix_branch_id")),
        "target_stop_contract_id": _norm(row.get("target_stop_contract_id")),
        "target_stop_result": _norm(row.get("target_stop_result")),
        "branch_decision_class": _norm(row.get("branch_decision_class")),
        "branch_result_binary": _norm(row.get("branch_result_binary")),
        "integrated_evidence_action": _norm(row.get("integrated_evidence_action")),
        "integrated_evidence_state": _norm(row.get("integrated_evidence_state")),
        "m15_selector_action": _norm(row.get("m15_selector_action")),
        "m1_selector_action": _norm(row.get("m1_selector_action")),
        "positive_selector_action": _norm(row.get("positive_selector_action")),
        "source_repair_route_class": _norm(row.get("source_repair_route_class")),
        "exact_failure_cause": _norm(row.get("exact_failure_cause")),
        "exact_success_cause": _norm(row.get("exact_success_cause")),
        "not_completion": bool(row.get("not_completion")),
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
        exists = path.exists()
        rows = _line_count(path) if exists else 0
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
                    else "supporting_sidecar_rows"
                ),
                "missing_or_broken": not exists,
            }
        )
    coverage, blank_anchors = _coverage(runtime_rows)
    return {
        "schema_version": "gtos_vnext_target_stop_ordering_execution_scoring_runtime_summary_v1",
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
            raise SystemExit("generated target/stop ordering execution outputs are stale")
        return 0

    write_outputs(runtime_rows, summary)
    print(f"Wrote {OUTPUT_ROWS} ({len(runtime_rows)} rows)")
    print(f"Wrote {OUTPUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
