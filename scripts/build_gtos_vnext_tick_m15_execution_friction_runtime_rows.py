#!/usr/bin/env python3
"""Build runtime rows for tick M15 execution-friction diagnostics."""

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
WAVE_ID = "WAVE_TICK_M15_EXECUTION_FRICTION_RUNTIME"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_TICK_M15_EXECUTION_FRICTION_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_TICK_M15_EXECUTION_FRICTION_RUNTIME_SUMMARY_{DATE}.json"

BUILD_SCRIPT_SOURCE = "build_tick_m15_execution_friction_diagnostic_2026_05_16.py"
BUCKET_SOURCE = "TICK_M15_EXECUTION_FRICTION_BUCKET_LEDGER_2026-05-16.jsonl"
RESULT_SOURCE = "TICK_M15_EXECUTION_FRICTION_DIAGNOSTIC_RESULT_2026-05-16.json"
SUMMARY_SOURCE = "TICK_M15_EXECUTION_FRICTION_DIAGNOSTIC_SUMMARY_2026-05-16.md"
QUESTION_SOURCE = "TICK_M15_EXECUTION_FRICTION_QUESTION_LEDGER_2026-05-16.jsonl"
RESIDUAL_SOURCE = "TICK_M15_EXECUTION_FRICTION_RESIDUAL_LEDGER_2026-05-16.jsonl"
ROW_SOURCE = "TICK_M15_EXECUTION_FRICTION_ROW_LEDGER_2026-05-16.jsonl"

PRIMARY_SOURCES = (ROW_SOURCE,)
JOIN_CONTEXT_SOURCES = (BUCKET_SOURCE, RESIDUAL_SOURCE, QUESTION_SOURCE)
SUPPORT_SOURCES = (
    BUILD_SCRIPT_SOURCE,
    RESULT_SOURCE,
    SUMMARY_SOURCE,
)
ALL_SOURCES = (
    BUILD_SCRIPT_SOURCE,
    BUCKET_SOURCE,
    RESULT_SOURCE,
    SUMMARY_SOURCE,
    QUESTION_SOURCE,
    RESIDUAL_SOURCE,
    ROW_SOURCE,
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

BUCKET_BEHAVIOR = {
    "FRICTION_SPREAD_COMPETES_WITH_MOVEMENT": {
        "review_action": "AVOID",
        "source_component": "tick_m15_execution_friction_spread_competes",
        "source_group": "tick_m15_execution_friction_avoid_filter",
        "source_role": "tick_m15_spread_competes_with_movement_guard",
        "system_surface": "execution_adjacent_tick_m15_friction_guard",
        "action_class": "tick_m15_execution_friction_spread_avoid_filter",
        "r_evidence_class": "TICK_M15_EXECUTION_FRICTION_SPREAD_COMPETES",
        "proxy_r_class": "NEGATIVE_PROXY_R",
    },
    "FRICTION_MOVEMENT_DOMINATES_SPREAD_DIAGNOSTIC": {
        "review_action": "MIXED",
        "source_component": "tick_m15_execution_friction_movement_dominates",
        "source_group": "tick_m15_execution_friction_source_acquisition",
        "source_role": "tick_m15_entry_geometry_source_acquisition_guard",
        "system_surface": "execution_adjacent_tick_m15_friction_source_acquisition",
        "action_class": "tick_m15_execution_friction_entry_geometry_context",
        "r_evidence_class": "TICK_M15_EXECUTION_FRICTION_ENTRY_GEOMETRY_SOURCE_ACQUISITION_REQUIRED",
        "proxy_r_class": "MIXED_PROXY_R",
    },
    "FRICTION_WEAKER_THAN_DENOMINATOR": {
        "review_action": "MIXED",
        "source_component": "tick_m15_execution_friction_weak_denominator",
        "source_group": "tick_m15_execution_friction_context",
        "source_role": "tick_m15_weak_denominator_context_guard",
        "system_surface": "execution_adjacent_tick_m15_friction_context",
        "action_class": "tick_m15_execution_friction_denominator_context",
        "r_evidence_class": "TICK_M15_EXECUTION_FRICTION_CONTEXT",
        "proxy_r_class": "MIXED_PROXY_R",
    },
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


def _source_row_count(path: Path) -> int:
    suffix = path.suffix.casefold()
    if suffix == ".jsonl":
        return len(_read_jsonl(path))
    if suffix == ".json":
        return 1
    return 1


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


def _nested_metric(row: dict[str, Any], name: str) -> float | None:
    metrics = row.get("metrics")
    if isinstance(metrics, dict):
        value = _to_float(metrics.get(name))
        if value is not None:
            return value
    source_fields = row.get("source_fields")
    if isinstance(source_fields, dict):
        return _to_float(source_fields.get(name))
    return None


def _route_session(value: Any) -> str:
    text = _norm(value)
    if text == "tokyo_core_0000_0300":
        return "tokyo_kz"
    return text


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
            "route_session": _route_session(row.get("session_bucket")),
            "horizon_id": _norm(row.get("horizon_id")),
            "primitive": _norm(row.get("primitive_flag")),
            "source_component": source_component,
        }.items()
        if value
    }


def _behavior_for_row(
    row: dict[str, Any],
    residual_by_queue: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, str], dict[str, Any]]:
    queue_id = _norm(row.get("queue_id"))
    residual = residual_by_queue.get(queue_id, {})
    bucket = _norm(residual.get("friction_bucket"))
    if not bucket:
        ratio = _nested_metric(row, "future_abs_to_spread_max")
        if ratio is not None and ratio <= 1.0:
            bucket = "FRICTION_SPREAD_COMPETES_WITH_MOVEMENT"
        else:
            bucket = "FRICTION_WEAKER_THAN_DENOMINATOR"
    behavior = BUCKET_BEHAVIOR.get(bucket, BUCKET_BEHAVIOR["FRICTION_WEAKER_THAN_DENOMINATOR"])
    return bucket, behavior, residual


def _runtime_row(
    source_path: Path,
    source_sha: str,
    source_line_no: int,
    row: dict[str, Any],
    residual_by_queue: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    friction_bucket, behavior, residual = _behavior_for_row(row, residual_by_queue)
    decision = behavior["review_action"]
    scope = _event_scope(row, behavior["source_component"])
    source_row_id = _norm(row.get("queue_id")) or f"{source_path.name}:{source_line_no}"
    row_hash = _sha256_text(json.dumps(row, sort_keys=True))
    row_id = f"tick_m15_execution_friction:{source_line_no}:{row_hash[:16]}"
    future_abs_to_spread_max = _nested_metric(row, "future_abs_to_spread_max")
    signed_proxy = None
    if decision == "AVOID" and future_abs_to_spread_max is not None:
        signed_proxy = -abs(1.0 / max(abs(future_abs_to_spread_max), 1e-9))
    metrics = {
        key: metric
        for key, metric in {
            "proxy_score": _metric(signed_proxy, source_field="signed_inverse_future_abs_to_spread_max"),
            "effective_n": _metric(1.0, source_field="tick_m15_friction_row"),
            "execution_friction_ratio": _metric(future_abs_to_spread_max, source_field="future_abs_to_spread_max"),
            "spread_max": _metric(_nested_metric(row, "spread_max"), source_field="spread_max"),
            "spread_median": _metric(_nested_metric(row, "spread_median"), source_field="spread_median"),
            "tick_velocity_per_sec": _metric(_nested_metric(row, "tick_velocity_per_sec"), source_field="tick_velocity_per_sec"),
        }.items()
        if metric is not None
    }
    symbol = scope.get("symbol", "")
    source_fields = row.get("source_fields") if isinstance(row.get("source_fields"), dict) else {}
    runtime = {
        "tick_m15_execution_friction_runtime_row_id": row_id,
        "row_key": row_id,
        "evidence_family": "gtos_vnext_tick_m15_execution_friction",
        "source_name": "gtos_vnext_tick_m15_execution_friction_wave",
        "source_kind": "tick_m15_execution_friction_row",
        "source_group": behavior["source_group"],
        "source_role": behavior["source_role"],
        "source_component": behavior["source_component"],
        "system_surface": behavior["system_surface"],
        "action_class": behavior["action_class"],
        "review_action": decision,
        "r_evidence_class": behavior["r_evidence_class"],
        "proxy_r_class": behavior["proxy_r_class"],
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
        "source_bound": bool(
            scope.get("symbol")
            and scope.get("route_session")
            and scope.get("horizon_id")
            and scope.get("primitive")
        ),
        "source_complete": decision == "AVOID",
        "runtime_candidate_use_permitted": decision == "AVOID",
        "candidate_use_allowed_now": decision == "AVOID",
        "orderflow_runtime_validated": True,
        "source_path": _path_text(source_path),
        "source_file_sha256": source_sha,
        "source_line_no": source_line_no,
        "source_row_id": source_row_id,
        "queue_id": row.get("queue_id"),
        "friction_bucket": friction_bucket,
        "transfer_class": residual.get("transfer_class"),
        "diagnostic_interpretation": residual.get("diagnostic_interpretation"),
        "bar_open_utc": row.get("bar_open_utc"),
        "future_bar_open_utc": row.get("future_bar_open_utc"),
        "future_abs_change": row.get("future_abs_change"),
        "future_abs_to_spread_max": future_abs_to_spread_max,
        "future_abs_le_one_spread_max": (
            row.get("metrics", {}).get("future_abs_le_one_spread_max")
            if isinstance(row.get("metrics"), dict)
            else None
        ),
        "future_abs_le_two_spread_max": (
            row.get("metrics", {}).get("future_abs_le_two_spread_max")
            if isinstance(row.get("metrics"), dict)
            else None
        ),
        "source_file": source_fields.get("source_file"),
        "trade_date": source_fields.get("trade_date"),
        "primitive_flag": row.get("primitive_flag"),
        "session_bucket": row.get("session_bucket"),
        "not_completion": True,
        "r_metrics": metrics,
    }
    return {key: value for key, value in runtime.items() if value not in (None, "", {}, [])}


def build_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    row_path = _source_path(ROW_SOURCE)
    residual_path = _source_path(RESIDUAL_SOURCE)
    row_rows = _read_jsonl(row_path)
    residual_rows = _read_jsonl(residual_path)
    residual_by_queue = {
        _norm(row.get("queue_id")): row
        for row in residual_rows
        if _norm(row.get("queue_id"))
    }
    row_sha = _sha256_file(row_path)
    runtime_rows = [
        _runtime_row(row_path, row_sha, line_no, row, residual_by_queue)
        for line_no, row in enumerate(row_rows, start=1)
    ]
    source_artifacts: list[dict[str, Any]] = []
    for source_name in ALL_SOURCES:
        path = _source_path(source_name)
        source_role = "supporting_evidence"
        runtime_rows_read = 0
        if source_name in PRIMARY_SOURCES:
            source_role = "primary_runtime_rows"
            runtime_rows_read = len(runtime_rows)
        elif source_name in JOIN_CONTEXT_SOURCES:
            source_role = "joined_runtime_context"
        source_artifacts.append(
            {
                "name": source_name,
                "path": _path_text(path),
                "rows": _source_row_count(path),
                "runtime_rows_read": runtime_rows_read,
                "sha256_or_git_blob": _sha256_file(path),
                "source_role": source_role,
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
        "friction_buckets": _counter(rows, "friction_bucket"),
    }
    source_acquisition_rows = sum(
        1
        for row in rows
        if row.get("r_evidence_class")
        == "TICK_M15_EXECUTION_FRICTION_ENTRY_GEOMETRY_SOURCE_ACQUISITION_REQUIRED"
    )
    return {
        "schema_version": "gtos_vnext_tick_m15_execution_friction_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(rows),
        "runtime_rows_with_event_scope": sum(1 for row in rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in rows if not row.get("event_scope")),
        "runtime_source_rows_represented": len(rows),
        "support_rows_represented": sum(
            int(item["rows"]) for item in source_artifacts if item["source_role"] != "primary_runtime_rows"
        ),
        "wave_source_rows_counted": sum(int(item["rows"]) for item in source_artifacts),
        "source_acquisition_required_rows": source_acquisition_rows,
        "proxy_score_sum": round(
            sum(float(row.get("r_metrics", {}).get("proxy_score", {}).get("sum") or 0.0) for row in rows),
            12,
        ),
        "decision_counts": _counter(rows, "review_action"),
        "friction_bucket_counts": _counter(rows, "friction_bucket"),
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
    print(
        json.dumps(
            {
                "ok": True,
                "runtime_row_count": len(rows),
                "runtime_rows_path": _path_text(OUTPUT_ROWS),
                "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
