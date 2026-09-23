#!/usr/bin/env python3
"""Build runtime rows for unified shadow/source-materialization evidence."""

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
WAVE_ID = "WAVE_UNIFIED_SHADOW_SOURCE_MATERIALIZATION_RUNTIME"
OUTPUT_ROWS = ROUTE_DIR / (
    f"GTOS_VNEXT_UNIFIED_SHADOW_SOURCE_MATERIALIZATION_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = ROUTE_DIR / (
    f"GTOS_VNEXT_UNIFIED_SHADOW_SOURCE_MATERIALIZATION_RUNTIME_SUMMARY_{DATE}.json"
)

CANDIDATE_VARIANT_ACTION_SYNTHESIS_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_VARIANT_"
    "EXECUTION_MARKET_GAP_ACTION_SYNTHESIS_LEDGER_2026-05-17.jsonl"
)
SHADOW_SCORER_ROW_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SHADOW_SCORER_"
    "EXECUTION_ROW_LEDGER_2026-05-17.jsonl"
)
SOURCE_MATERIALIZATION_EXECUTION_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SOURCE_"
    "MATERIALIZATION_EXECUTION_MATERIALIZATION_LEDGER_2026-05-17.jsonl"
)
PRIMARY_SOURCES = (
    CANDIDATE_VARIANT_ACTION_SYNTHESIS_SOURCE,
    SHADOW_SCORER_ROW_SOURCE,
    SOURCE_MATERIALIZATION_EXECUTION_SOURCE,
)

SUPPORT_SOURCES = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_VARIANT_EXECUTION_AVOID_INVERSE_POLICY_VARIANT_SCORE_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_VARIANT_EXECUTION_BUCKET_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_VARIANT_EXECUTION_ENTRY_GEOMETRY_PARENT_DECISION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_VARIANT_EXECUTION_ENTRY_GEOMETRY_VARIANT_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_VARIANT_EXECUTION_QUESTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_VARIANT_EXECUTION_SOURCE_EXPANSION_MATERIALIZATION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_VARIANT_EXECUTION_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_VARIANT_EXECUTION_SYMBOL_SESSION_HORIZON_ACTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SHADOW_SCORER_EXECUTION_BUCKET_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SHADOW_SCORER_EXECUTION_CONTROL_GUARD_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SHADOW_SCORER_EXECUTION_IMPLEMENT_ENABLE_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SHADOW_SCORER_EXECUTION_QUESTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SHADOW_SCORER_EXECUTION_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SHADOW_SCORER_EXECUTION_SOURCE_MATERIALIZATION_QUEUE_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SHADOW_SCORER_EXECUTION_SYMBOL_SESSION_ACTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SOURCE_MATERIALIZATION_EXECUTION_BUCKET_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SOURCE_MATERIALIZATION_EXECUTION_FAMILY_PROXY_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SOURCE_MATERIALIZATION_EXECUTION_GAP_CLOSURE_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SOURCE_MATERIALIZATION_EXECUTION_QUESTION_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SOURCE_MATERIALIZATION_EXECUTION_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_SOURCE_MATERIALIZATION_EXECUTION_SYMBOL_SESSION_HORIZON_LEDGER_2026-05-17.jsonl",
)

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

IMPLEMENT_FOLLOW_COMPONENTS = {
    "entry_geometry",
    "market_gap_entry_geometry",
    "market_entry_comparator",
    "branch_proxy_scorer",
}
IMPLEMENT_AVOID_COMPONENTS = {
    "branch_failure_avoid_filter",
    "avoid_filter",
    "market_gap_avoid_filter",
}
SHADOW_AVOID_ACTION_CLASSES = {
    "branch_failure_avoid_filter": "unified_shadow_scorer_branch_failure_avoid_filter",
    "avoid_filter": "unified_shadow_scorer_avoid_filter",
    "market_gap_avoid_filter": "unified_shadow_scorer_market_gap_avoid_filter",
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


def _source_path(name: str) -> Path:
    return MOONSHOT_ROUTE / name


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


def _metric(value: float | None, *, source_field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "sum": round(value, 12),
        "count": 1,
        "mean": round(value, 12),
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "match_rows_with_metric": 1,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _event_scope(row: dict[str, Any], source_component: str) -> dict[str, str]:
    symbol = _norm(row.get("symbol"))
    return {
        key: value
        for key, value in {
            "symbol": symbol,
            "source_symbol": symbol,
            "market": symbol,
            "timeframe": "M15",
            "market_timeframe": "M15",
            "route_family": "numeric_router",
            "route_session": _norm(row.get("route_session")),
            "horizon_id": _norm(row.get("horizon_id")),
            "primitive": _norm(row.get("primitive_flag")),
            "source_component": source_component,
        }.items()
        if value
    }


def _proxy_r_class(decision: str, score: float | None, *, strong: bool = False) -> str:
    if decision == "AVOID":
        return "STRONG_NEGATIVE_PROXY_R" if strong else "NEGATIVE_PROXY_R"
    if decision == "FOLLOW":
        return "STRONG_POSITIVE_PROXY_R" if strong else "POSITIVE_PROXY_R"
    if score is not None and score < 0:
        return "NEGATIVE_PROXY_R"
    if score is not None and score > 0:
        return "POSITIVE_PROXY_R"
    return "MIXED_PROXY_R"


def _candidate_variant_row(source_path: Path, sha: str, line_no: int, row: dict[str, Any]) -> dict[str, Any]:
    action = _norm(row.get("market_gap_action"))
    action_decision = _norm(row.get("market_gap_action_decision"))
    score_class = _norm(row.get("candidate_score_class"))
    if action == "AVOID_INVERSE_VARIANTS_INSTANTIATED":
        decision = "AVOID"
        source_component = "unified_candidate_variant_avoid_inverse"
        source_role = "unified_candidate_variant_avoid_inverse_guard"
        action_class = "unified_candidate_variant_avoid_inverse_filter"
        r_evidence_class = "UNIFIED_CANDIDATE_VARIANT_AVOID_INVERSE"
        signed_score = -abs(_to_float(row.get("candidate_score_proxy")) or 0.0)
        strong = True
    elif action == "ENTRY_GEOMETRY_VARIANTS_INSTANTIATED":
        decision = "FOLLOW"
        source_component = "unified_candidate_variant_entry_geometry"
        source_role = "unified_candidate_variant_entry_geometry_follow"
        action_class = "unified_candidate_variant_entry_geometry_follow"
        r_evidence_class = "UNIFIED_CANDIDATE_VARIANT_ENTRY_GEOMETRY"
        signed_score = abs(_to_float(row.get("candidate_score_proxy")) or 0.0)
        strong = "READY" in action_decision
    else:
        decision = "MIXED"
        source_component = "unified_candidate_variant_source_expansion"
        source_role = "unified_candidate_variant_source_expansion_guard"
        action_class = "unified_candidate_variant_source_acquisition_guard"
        r_evidence_class = "UNIFIED_CANDIDATE_VARIANT_SOURCE_ACQUISITION_REQUIRED"
        signed_score = _to_float(row.get("candidate_score_proxy"))
        strong = "HIGH_PRIORITY" in score_class
    scope = _event_scope(row, source_component)
    source_row_id = _norm(row.get("market_gap_action_synthesis_id")) or f"{source_path.name}:{line_no}"
    row_id = f"unified_shadow_source_materialization:candidate_variant:{line_no}:{_sha256_text(json.dumps(row, sort_keys=True))[:16]}"
    effective_n = _to_float(row.get("flagged_n")) or _to_float(row.get("control_n"))
    metrics = {
        key: metric
        for key, metric in {
            "proxy_score": _metric(signed_score, source_field="signed_candidate_score_proxy"),
            "effective_n": _metric(effective_n, source_field="flagged_n_or_control_n"),
            "delta_alignment_rate": _metric(_to_float(row.get("delta_alignment_rate")), source_field="delta_alignment_rate"),
            "delta_mean_abs_future_change": _metric(_to_float(row.get("delta_mean_abs_future_change")), source_field="delta_mean_abs_future_change"),
        }.items()
        if metric is not None
    }
    return _runtime_payload(
        row_id=row_id,
        source_path=source_path,
        source_sha=sha,
        source_line_no=line_no,
        source_row_id=source_row_id,
        source_kind="candidate_variant_market_gap_action_synthesis",
        source_group="candidate_variant_execution",
        source_role=source_role,
        source_component=source_component,
        system_surface="unified_candidate_variant_execution_runtime",
        action_class=action_class,
        decision=decision,
        r_evidence_class=r_evidence_class,
        proxy_r_class=_proxy_r_class(decision, signed_score, strong=strong),
        scope=scope,
        source_row=row,
        metrics=metrics,
        extra={
            "market_gap_action": action,
            "market_gap_action_decision": action_decision,
            "candidate_score_class": score_class,
            "candidate_score_proxy_signed": signed_score,
        },
    )


def _shadow_scorer_row(source_path: Path, sha: str, line_no: int, row: dict[str, Any]) -> dict[str, Any]:
    family = _norm(row.get("shadow_scorer_action_family"))
    component = _norm(row.get("shadow_scorer_component"))
    score = _to_float(row.get("shadow_scorer_score"))
    if family == "IMPLEMENT_SHADOW_RULE" and component in IMPLEMENT_AVOID_COMPONENTS:
        decision = "AVOID"
        source_component = f"unified_shadow_scorer_{component}"
        source_role = "unified_shadow_scorer_avoid_guard"
        action_class = SHADOW_AVOID_ACTION_CLASSES[component]
        r_evidence_class = "UNIFIED_SHADOW_SCORER_AVOID_FILTER"
        signed_score = -abs(score or 0.0)
    elif family == "IMPLEMENT_SHADOW_RULE" and component in IMPLEMENT_FOLLOW_COMPONENTS:
        decision = "FOLLOW"
        source_component = f"unified_shadow_scorer_{component}"
        source_role = "unified_shadow_scorer_follow"
        action_class = f"unified_shadow_scorer_{component}_follow"
        r_evidence_class = "UNIFIED_SHADOW_SCORER_FOLLOW_SCORER"
        signed_score = abs(score or 0.0)
    elif family in {"MATERIALIZE_SOURCE", "DENOMINATOR_GUARD"}:
        decision = "MIXED"
        source_component = "unified_shadow_scorer_source_materialization"
        source_role = "unified_shadow_scorer_source_materialization_guard"
        action_class = "unified_shadow_scorer_source_acquisition_guard"
        r_evidence_class = "UNIFIED_SHADOW_SCORER_SOURCE_ACQUISITION_REQUIRED"
        signed_score = score
    else:
        decision = "MIXED"
        source_component = f"unified_shadow_scorer_{component or 'control_context'}"
        source_role = "unified_shadow_scorer_control_context"
        action_class = "unified_shadow_scorer_control_context_guard"
        r_evidence_class = "UNIFIED_SHADOW_SCORER_CONTROL_CONTEXT"
        signed_score = score
    scope = _event_scope(row, source_component)
    source_row_id = _norm(row.get("shadow_scorer_execution_id")) or f"{source_path.name}:{line_no}"
    row_id = f"unified_shadow_source_materialization:shadow_scorer:{line_no}:{_sha256_text(json.dumps(row, sort_keys=True))[:16]}"
    metrics = {
        key: metric
        for key, metric in {
            "proxy_score": _metric(signed_score, source_field="signed_shadow_scorer_score"),
            "effective_n": _metric(_to_float(row.get("source_rows_needed_to_n20")), source_field="source_rows_needed_to_n20"),
        }.items()
        if metric is not None
    }
    return _runtime_payload(
        row_id=row_id,
        source_path=source_path,
        source_sha=sha,
        source_line_no=line_no,
        source_row_id=source_row_id,
        source_kind="shadow_scorer_execution_row",
        source_group=family.lower() if family else "shadow_scorer_context",
        source_role=source_role,
        source_component=source_component,
        system_surface="unified_shadow_scorer_execution_runtime",
        action_class=action_class,
        decision=decision,
        r_evidence_class=r_evidence_class,
        proxy_r_class=_proxy_r_class(decision, signed_score, strong=_norm(row.get("shadow_scorer_score_band")) == "SHADOW_SCORE_HIGH"),
        scope=scope,
        source_row=row,
        metrics=metrics,
        extra={
            "shadow_scorer_action_family": family,
            "shadow_scorer_component": component,
            "shadow_scorer_score_signed": signed_score,
            "implementation_eligibility": row.get("implementation_eligibility"),
            "code_candidate_status": row.get("code_candidate_status"),
        },
    )


def _source_materialization_row(source_path: Path, sha: str, line_no: int, row: dict[str, Any]) -> dict[str, Any]:
    score = _to_float(row.get("materialization_proxy_score"))
    midpoint = _to_float(row.get("materialization_proxy_r_style_midpoint"))
    decision = "MIXED"
    source_component = "unified_source_materialization_execution"
    source_role = "unified_source_materialization_execution_guard"
    action_class = "unified_source_materialization_source_acquisition_guard"
    r_evidence_class = "UNIFIED_SOURCE_MATERIALIZATION_SOURCE_ACQUISITION_REQUIRED"
    scope = _event_scope(row, source_component)
    source_row_id = _norm(row.get("source_materialization_execution_id")) or f"{source_path.name}:{line_no}"
    row_id = f"unified_shadow_source_materialization:source_materialization:{line_no}:{_sha256_text(json.dumps(row, sort_keys=True))[:16]}"
    metrics = {
        key: metric
        for key, metric in {
            "proxy_score": _metric(score, source_field="materialization_proxy_score"),
            "cost_adjusted_simulated_r": _metric(midpoint, source_field="materialization_proxy_r_style_midpoint"),
            "effective_n": _metric(_to_float(row.get("current_targetable_flagged_n")), source_field="current_targetable_flagged_n"),
            "source_gap_to_n20": _metric(_to_float(row.get("current_exact_gap_to_n20")), source_field="current_exact_gap_to_n20"),
        }.items()
        if metric is not None
    }
    return _runtime_payload(
        row_id=row_id,
        source_path=source_path,
        source_sha=sha,
        source_line_no=line_no,
        source_row_id=source_row_id,
        source_kind="source_materialization_execution_row",
        source_group="source_materialization_execution",
        source_role=source_role,
        source_component=source_component,
        system_surface="unified_source_materialization_execution_runtime",
        action_class=action_class,
        decision=decision,
        r_evidence_class=r_evidence_class,
        proxy_r_class=_proxy_r_class(decision, midpoint),
        scope=scope,
        source_row=row,
        metrics=metrics,
        extra={
            "source_materialization_execution_status": row.get("source_materialization_execution_status"),
            "source_materialization_decision": row.get("source_materialization_decision"),
            "source_acquisition_status": row.get("source_acquisition_status"),
            "source_proxy_replay_result": row.get("source_proxy_replay_result"),
            "materialization_proxy_r_style_result_class": row.get("materialization_proxy_r_style_result_class"),
            "materialization_proxy_scope": row.get("materialization_proxy_scope"),
        },
    )


def _runtime_payload(
    *,
    row_id: str,
    source_path: Path,
    source_sha: str,
    source_line_no: int,
    source_row_id: str,
    source_kind: str,
    source_group: str,
    source_role: str,
    source_component: str,
    system_surface: str,
    action_class: str,
    decision: str,
    r_evidence_class: str,
    proxy_r_class: str,
    scope: dict[str, str],
    source_row: dict[str, Any],
    metrics: dict[str, Any],
    extra: dict[str, Any],
) -> dict[str, Any]:
    symbol = scope.get("symbol", "")
    runtime = {
        "unified_shadow_source_materialization_runtime_row_id": row_id,
        "row_key": row_id,
        "evidence_family": "gtos_vnext_unified_shadow_source_materialization",
        "source_name": "gtos_vnext_unified_shadow_source_materialization_wave",
        "source_kind": source_kind,
        "source_group": source_group,
        "source_role": source_role,
        "source_component": source_component,
        "system_surface": system_surface,
        "action_class": action_class,
        "review_action": decision,
        "r_evidence_class": r_evidence_class,
        "proxy_r_class": proxy_r_class,
        "route_family": "numeric_router",
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol),
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": scope.get("route_session", ""),
        "horizon_id": scope.get("horizon_id", ""),
        "primitive": scope.get("primitive", ""),
        "event_scope": scope,
        "source_bound": bool(scope.get("symbol") and scope.get("route_session") and scope.get("horizon_id") and scope.get("primitive")),
        "source_complete": decision in {"FOLLOW", "AVOID"},
        "runtime_candidate_use_permitted": decision in {"FOLLOW", "AVOID"},
        "candidate_use_allowed_now": decision in {"FOLLOW", "AVOID"},
        "orderflow_runtime_validated": True,
        "source_path": _path_text(source_path),
        "source_file_sha256": source_sha,
        "source_line_no": source_line_no,
        "source_row_id": source_row_id,
        "source_manifest_hash": source_row.get("source_manifest_hash"),
        "market_gap_combo_id": source_row.get("market_gap_combo_id"),
        "primitive_flag": source_row.get("primitive_flag"),
        "session_bucket": source_row.get("session_bucket"),
        "not_completion": bool(source_row.get("not_completion", True)),
        "r_metrics": metrics,
        **extra,
    }
    return {key: value for key, value in runtime.items() if value not in (None, "", {}, [])}


def _runtime_row(source_name: str, source_path: Path, sha: str, line_no: int, row: dict[str, Any]) -> dict[str, Any]:
    if source_name == CANDIDATE_VARIANT_ACTION_SYNTHESIS_SOURCE:
        return _candidate_variant_row(source_path, sha, line_no, row)
    if source_name == SHADOW_SCORER_ROW_SOURCE:
        return _shadow_scorer_row(source_path, sha, line_no, row)
    return _source_materialization_row(source_path, sha, line_no, row)


def build_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    runtime_rows: list[dict[str, Any]] = []
    source_artifacts: list[dict[str, Any]] = []
    for source_name in PRIMARY_SOURCES:
        path = _source_path(source_name)
        rows = _read_jsonl(path)
        source_sha = _sha256_file(path)
        start_len = len(runtime_rows)
        for line_no, row in enumerate(rows, start=1):
            runtime_rows.append(_runtime_row(source_name, path, source_sha, line_no, row))
        source_artifacts.append(
            {
                "name": source_name,
                "path": _path_text(path),
                "rows": len(rows),
                "runtime_rows_read": len(runtime_rows) - start_len,
                "sha256_or_git_blob": source_sha,
                "source_role": "primary_runtime_rows",
            }
        )
    for source_name in SUPPORT_SOURCES:
        if source_name in PRIMARY_SOURCES:
            continue
        path = _source_path(source_name)
        rows = _read_jsonl(path)
        source_artifacts.append(
            {
                "name": source_name,
                "path": _path_text(path),
                "rows": len(rows),
                "runtime_rows_read": 0,
                "sha256_or_git_blob": _sha256_file(path),
                "source_role": "supporting_evidence",
            }
        )
    return runtime_rows, source_artifacts


def _counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field))).items()))


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {field: sum(1 for row in rows if not _norm(row.get(field))) for field in ANCHOR_FIELDS}


def build_summary(rows: list[dict[str, Any]], source_artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    coverage = {
        "symbols": _counter(rows, "symbol"),
        "source_symbols": _counter(rows, "source_symbol"),
        "markets": _counter(rows, "market"),
        "timeframes": _counter(rows, "timeframe"),
        "sessions": _counter(rows, "route_session"),
        "horizons": _counter(rows, "horizon_id"),
        "primitives": _counter(rows, "primitive"),
        "sides": _counter(rows, "side"),
        "entry_variants": _counter(rows, "entry_variant"),
        "target_stop_order_classes": _counter(rows, "target_stop_order_class"),
        "source_components": _counter(rows, "source_component"),
        "action_classes": _counter(rows, "action_class"),
        "source_kinds": _counter(rows, "source_kind"),
        "source_roles": _counter(rows, "source_role"),
        "source_groups": _counter(rows, "source_group"),
        "system_surfaces": _counter(rows, "system_surface"),
    }
    source_acquisition_rows = sum(
        1
        for row in rows
        if row.get("r_evidence_class")
        in {
            "UNIFIED_CANDIDATE_VARIANT_SOURCE_ACQUISITION_REQUIRED",
            "UNIFIED_SHADOW_SCORER_SOURCE_ACQUISITION_REQUIRED",
            "UNIFIED_SOURCE_MATERIALIZATION_SOURCE_ACQUISITION_REQUIRED",
        }
    )
    return {
        "schema_version": "gtos_vnext_unified_shadow_source_materialization_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(rows),
        "runtime_rows_with_event_scope": sum(1 for row in rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in rows if not row.get("event_scope")),
        "runtime_source_rows_represented": len(rows),
        "support_rows_represented": sum(int(item["rows"]) for item in source_artifacts if item["source_role"] == "supporting_evidence"),
        "wave_source_rows_counted": sum(int(item["rows"]) for item in source_artifacts),
        "source_acquisition_required_rows": source_acquisition_rows,
        "proxy_score_sum": round(sum(float(row.get("r_metrics", {}).get("proxy_score", {}).get("sum") or 0.0) for row in rows), 12),
        "decision_counts": _counter(rows, "review_action"),
        "r_evidence_class_counts": _counter(rows, "r_evidence_class"),
        "action_class_counts": _counter(rows, "action_class"),
        "source_component_counts": _counter(rows, "source_component"),
        "source_role_counts": _counter(rows, "source_role"),
        "source_group_counts": _counter(rows, "source_group"),
        "source_kind_counts": _counter(rows, "source_kind"),
        "system_surface_counts": _counter(rows, "system_surface"),
        "route_family_counts": _counter(rows, "route_family"),
        "proxy_r_class_counts": _counter(rows, "proxy_r_class"),
        "coverage_counts": coverage,
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "source_artifacts": source_artifacts,
    }


def _jsonl_text(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows, source_artifacts = build_rows()
    summary = build_summary(rows, source_artifacts)
    rows_text = _jsonl_text(rows)
    summary_text = _json_text(summary)
    if args.check:
        mismatches = []
        if not OUTPUT_ROWS.exists() or OUTPUT_ROWS.read_text(encoding="utf-8") != rows_text:
            mismatches.append(_path_text(OUTPUT_ROWS))
        if not OUTPUT_SUMMARY.exists() or OUTPUT_SUMMARY.read_text(encoding="utf-8") != summary_text:
            mismatches.append(_path_text(OUTPUT_SUMMARY))
        if mismatches:
            print(json.dumps({"ok": False, "mismatched_outputs": mismatches}, indent=2, sort_keys=True))
            return 1
        return 0
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROWS.write_text(rows_text, encoding="utf-8")
    OUTPUT_SUMMARY.write_text(summary_text, encoding="utf-8")
    print(json.dumps({"ok": True, "runtime_row_count": len(rows), "runtime_rows_path": _path_text(OUTPUT_ROWS), "runtime_summary_path": _path_text(OUTPUT_SUMMARY)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
