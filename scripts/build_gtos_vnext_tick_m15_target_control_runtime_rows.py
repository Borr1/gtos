#!/usr/bin/env python3
"""Build runtime rows for tick M15 target-control triage evidence."""

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
WAVE_ID = "WAVE_TICK_M15_TARGET_CONTROL_RUNTIME"
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_TICK_M15_TARGET_CONTROL_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_TICK_M15_TARGET_CONTROL_RUNTIME_SUMMARY_{DATE}.json"

BUILD_PACKET_SOURCE = "build_tick_m15_target_movement_packet_2026_05_15.py"
BUILD_TRIAGE_SOURCE = "build_tick_m15_target_control_triage_2026_05_15.py"
BUCKET_SOURCE = "TICK_M15_TARGET_CONTROL_TRIAGE_BUCKET_LEDGER_2026-05-15.jsonl"
TRIAGE_SOURCE = "TICK_M15_TARGET_CONTROL_TRIAGE_LEDGER_2026-05-15.jsonl"
RESULT_SOURCE = "TICK_M15_TARGET_CONTROL_TRIAGE_RESULT_2026-05-15.json"
TARGET_EVENT_SOURCE = "TICK_M15_TARGET_MOVEMENT_EVENT_LEDGER_2026-05-15.jsonl"
FLAG_CONTROL_SOURCE = "TICK_M15_TARGET_MOVEMENT_FLAG_CONTROL_LEDGER_2026-05-15.jsonl"

PRIMARY_SOURCES = (FLAG_CONTROL_SOURCE,)
JOIN_CONTEXT_SOURCES = (BUCKET_SOURCE, TRIAGE_SOURCE, TARGET_EVENT_SOURCE)
SUPPORT_SOURCES = (BUILD_PACKET_SOURCE, BUILD_TRIAGE_SOURCE, RESULT_SOURCE)
ALL_SOURCES = (
    BUILD_PACKET_SOURCE,
    BUILD_TRIAGE_SOURCE,
    BUCKET_SOURCE,
    TRIAGE_SOURCE,
    RESULT_SOURCE,
    TARGET_EVENT_SOURCE,
    FLAG_CONTROL_SOURCE,
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
    "PLACEBO_READY_N_GE20_POSITIVE_ABS_AND_NONNEGATIVE_ALIGNMENT_DELTA": {
        "review_action": "MIXED",
        "source_component": "tick_m15_target_control_placebo_ready_positive",
        "source_group": "tick_m15_target_control_source_acquisition",
        "source_role": "tick_m15_target_control_placebo_source_acquisition_guard",
        "system_surface": "execution_adjacent_tick_m15_target_control_source_acquisition",
        "action_class": "tick_m15_target_control_placebo_ready_context",
        "r_evidence_class": "TICK_M15_TARGET_CONTROL_PLACEBO_READY_SOURCE_ACQUISITION_REQUIRED",
        "proxy_r_class": "MIXED_PROXY_R",
    },
    "PLACEBO_READY_N_GE20_POSITIVE_ABS_NEGATIVE_ALIGNMENT_DELTA": {
        "review_action": "AVOID",
        "source_component": "tick_m15_target_control_negative_alignment",
        "source_group": "tick_m15_target_control_avoid_filter",
        "source_role": "tick_m15_target_control_negative_alignment_guard",
        "system_surface": "execution_adjacent_tick_m15_target_control_guard",
        "action_class": "tick_m15_target_control_negative_alignment_avoid_filter",
        "r_evidence_class": "TICK_M15_TARGET_CONTROL_NEGATIVE_ALIGNMENT_AVOID",
        "proxy_r_class": "NEGATIVE_PROXY_R",
    },
    "PLACEBO_READY_N_GE20_FLAT_OR_NEGATIVE_ABS_DELTA": {
        "review_action": "MIXED",
        "source_component": "tick_m15_target_control_flat_or_negative_abs",
        "source_group": "tick_m15_target_control_context",
        "source_role": "tick_m15_target_control_flat_context_guard",
        "system_surface": "execution_adjacent_tick_m15_target_control_context",
        "action_class": "tick_m15_target_control_flat_context",
        "r_evidence_class": "TICK_M15_TARGET_CONTROL_FLAT_OR_NEGATIVE_CONTEXT",
        "proxy_r_class": "MIXED_PROXY_R",
    },
    "SMALL_N_LT20_NO_SIGNIFICANCE_CLAIM": {
        "review_action": "MIXED",
        "source_component": "tick_m15_target_control_small_n_context",
        "source_group": "tick_m15_target_control_context",
        "source_role": "tick_m15_target_control_small_n_context_guard",
        "system_surface": "execution_adjacent_tick_m15_target_control_context",
        "action_class": "tick_m15_target_control_small_n_context",
        "r_evidence_class": "TICK_M15_TARGET_CONTROL_SMALL_N_CONTEXT",
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


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


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


def _read_json(path: Path) -> dict[str, Any]:
    with open(_long_path(path), "r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


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


def _metric(value: float | int | None, *, source_field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    value = float(value)
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


def _route_session(value: Any) -> str:
    text = _norm(value)
    mapping = {
        "tokyo_core_0000_0300": "tokyo_kz",
        "london_core_0700_1030": "london_core",
        "ny_core_1300_1700": "ny_core",
    }
    return mapping.get(text, text)


def _event_scope(row: dict[str, Any], source_component: str) -> dict[str, str]:
    symbol = _norm(row.get("symbol"))
    return {
        key: value
        for key, value in {
            "symbol": symbol,
            "source_symbol": symbol,
            "market": symbol,
            "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
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


def _triage_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        _norm(row.get("symbol")),
        _norm(row.get("session_bucket")),
        _norm(row.get("primitive_flag")),
        _norm(row.get("horizon_id")),
    )


def _triage_rows_by_key(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    out: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in rows:
        out[_triage_key(row)] = row
    return out


def _runtime_row(
    source_path: Path,
    source_sha: str,
    line_no: int,
    row: dict[str, Any],
    triage_row: dict[str, Any],
) -> dict[str, Any]:
    bucket = _norm(triage_row.get("triage_bucket")) or "SMALL_N_LT20_NO_SIGNIFICANCE_CLAIM"
    behavior = BUCKET_BEHAVIOR.get(bucket, BUCKET_BEHAVIOR["SMALL_N_LT20_NO_SIGNIFICANCE_CLAIM"])
    source_component = behavior["source_component"]
    decision = behavior["review_action"]
    flagged_n = _to_int(row.get("flagged_n"))
    control_n = _to_int(row.get("control_n"))
    delta_abs = _to_float(row.get("delta_mean_abs_future_change"))
    delta_alignment = _to_float(triage_row.get("delta_alignment_rate"))
    proxy_score = None
    if decision == "AVOID":
        proxy_score = -abs(delta_alignment if delta_alignment is not None else delta_abs or 0.0)
    elif bucket == "PLACEBO_READY_N_GE20_POSITIVE_ABS_AND_NONNEGATIVE_ALIGNMENT_DELTA":
        proxy_score = delta_alignment if delta_alignment is not None else delta_abs
    else:
        proxy_score = 0.0 if delta_abs is None else min(0.0, delta_abs)
    scope = _event_scope(row, source_component)
    source_row_id = "|".join(_triage_key(row))
    row_key = (
        f"tick_m15_target_control:{line_no}:"
        f"{_sha256_text(json.dumps(row, sort_keys=True, default=str))[:16]}"
    )
    metrics = {
        name: metric
        for name, metric in {
            "effective_n": _metric(flagged_n, source_field="flagged_n"),
            "control_n": _metric(control_n, source_field="control_n"),
            "delta_mean_abs_future_change": _metric(delta_abs, source_field="delta_mean_abs_future_change"),
            "delta_alignment_rate": _metric(delta_alignment, source_field="delta_alignment_rate"),
            "flagged_mean_abs_future_change": _metric(
                _to_float(row.get("flagged_mean_abs_future_change")),
                source_field="flagged_mean_abs_future_change",
            ),
            "control_mean_abs_future_change": _metric(
                _to_float(row.get("control_mean_abs_future_change")),
                source_field="control_mean_abs_future_change",
            ),
            "proxy_score": _metric(proxy_score, source_field="target_control_proxy_score"),
        }.items()
        if metric is not None
    }
    return {
        "tick_m15_target_control_runtime_row_id": row_key,
        "row_key": row_key,
        "source_name": "gtos_vnext_tick_m15_target_control_wave",
        "source_path": _path_text(source_path),
        "source_file_sha256": source_sha,
        "source_line_no": line_no,
        "source_row_id": source_row_id,
        "source_kind": "tick_m15_target_control_flag_control_row",
        "source_group": behavior["source_group"],
        "source_role": behavior["source_role"],
        "source_component": source_component,
        "system_surface": behavior["system_surface"],
        "action_class": behavior["action_class"],
        "evidence_family": "gtos_vnext_tick_m15_target_control",
        "review_action": decision,
        "r_evidence_class": behavior["r_evidence_class"],
        "proxy_r_class": behavior["proxy_r_class"],
        "route_family": "numeric_router",
        "symbol": _norm(row.get("symbol")),
        "source_symbol": _norm(row.get("symbol")),
        "market": _norm(row.get("symbol")),
        "symbol_family": resolve_vnext_symbol_family(_norm(row.get("symbol"))),
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": _route_session(row.get("session_bucket")),
        "session_bucket": _norm(row.get("session_bucket")),
        "horizon_id": _norm(row.get("horizon_id")),
        "horizon_bars": row.get("horizon_bars"),
        "primitive": _norm(row.get("primitive_flag")),
        "primitive_flag": _norm(row.get("primitive_flag")),
        "target_control_bucket": bucket,
        "sample_status": _norm(row.get("sample_status")),
        "flagged_n": flagged_n,
        "control_n": control_n,
        "flagged_delta_alignment_rate": row.get("flagged_delta_alignment_rate"),
        "control_delta_alignment_rate": row.get("control_delta_alignment_rate"),
        "delta_alignment_rate": delta_alignment,
        "flagged_mean_abs_future_change": row.get("flagged_mean_abs_future_change"),
        "control_mean_abs_future_change": row.get("control_mean_abs_future_change"),
        "delta_mean_abs_future_change": delta_abs,
        "flagged_mean_future_change": row.get("flagged_mean_future_change"),
        "control_mean_future_change": row.get("control_mean_future_change"),
        "flagged_mean_future_change_per_current_range": row.get(
            "flagged_mean_future_change_per_current_range"
        ),
        "control_mean_future_change_per_current_range": row.get(
            "control_mean_future_change_per_current_range"
        ),
        "control_scope": row.get("control_scope"),
        "next_gate": triage_row.get("next_gate"),
        "target_movement_runtime_interpretation": (
            "development target-control evidence: negative alignment becomes "
            "scoped avoid pressure; placebo-ready positive rows require "
            "source acquisition before candidate ranking; weak and small-n "
            "rows remain scoped context"
        ),
        "candidate_use_allowed_now": False,
        "runtime_candidate_use_permitted": False,
        "source_bound": True,
        "source_complete": bucket.startswith("PLACEBO_READY_N_GE20_POSITIVE_ABS_NEGATIVE"),
        "orderflow_runtime_validated": True,
        "source_transfer_validated": True,
        "not_completion": True,
        "placebo_or_shuffle_required_before_ranking": True,
        "r_metrics": metrics,
        "proxy_score": proxy_score,
        "event_scope": scope,
    }


def _coverage(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    fields = {
        "symbols": "symbol",
        "source_symbols": "source_symbol",
        "markets": "market",
        "symbol_families": "symbol_family",
        "timeframes": "timeframe",
        "sessions": "route_session",
        "horizons": "horizon_id",
        "primitives": "primitive",
        "sides": "side",
        "entry_variants": "entry_variant",
        "target_stop_order_classes": "target_stop_order_class",
        "source_components": "source_component",
        "source_groups": "source_group",
        "source_roles": "source_role",
        "source_kinds": "source_kind",
        "system_surfaces": "system_surface",
        "action_classes": "action_class",
        "target_control_buckets": "target_control_bucket",
    }
    coverage: dict[str, dict[str, int]] = {}
    for name, field in fields.items():
        counter: Counter[str] = Counter()
        for row in rows:
            value = _norm(row.get(field))
            if value:
                counter[value] += 1
        coverage[name] = dict(sorted(counter.items()))
    return coverage


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def _source_artifacts(runtime_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_read_by_name = Counter(
        Path(row["source_path"]).name for row in runtime_rows if row.get("source_path")
    )
    artifacts = []
    for name in ALL_SOURCES:
        path = _source_path(name)
        if name in PRIMARY_SOURCES:
            role = "primary_runtime_rows"
        elif name == TARGET_EVENT_SOURCE:
            role = "denominator_target_event_support"
        elif name in JOIN_CONTEXT_SOURCES:
            role = "joined_runtime_context"
        else:
            role = "supporting_evidence"
        artifacts.append(
            {
                "name": name,
                "path": _path_text(path),
                "rows": _source_row_count(path),
                "runtime_rows_read": runtime_read_by_name.get(name, 0),
                "sha256_or_git_blob": _sha256_file(path),
                "source_role": role,
            }
        )
    return artifacts


def _build_runtime_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    control_path = _source_path(FLAG_CONTROL_SOURCE)
    triage_path = _source_path(TRIAGE_SOURCE)
    control_sha = _sha256_file(control_path)
    control_rows = _read_jsonl(control_path)
    triage_by_key = _triage_rows_by_key(_read_jsonl(triage_path))
    runtime_rows = [
        _runtime_row(
            control_path,
            control_sha,
            line_no,
            row,
            triage_by_key.get(_triage_key(row), {}),
        )
        for line_no, row in enumerate(control_rows, start=1)
    ]
    result = _read_json(_source_path(RESULT_SOURCE))
    source_artifacts = _source_artifacts(runtime_rows)
    coverage = _coverage(runtime_rows)
    decision_counts = Counter(row["review_action"] for row in runtime_rows)
    source_component_counts = Counter(row["source_component"] for row in runtime_rows)
    source_role_counts = Counter(row["source_role"] for row in runtime_rows)
    source_group_counts = Counter(row["source_group"] for row in runtime_rows)
    source_kind_counts = Counter(row["source_kind"] for row in runtime_rows)
    system_surface_counts = Counter(row["system_surface"] for row in runtime_rows)
    r_evidence_class_counts = Counter(row["r_evidence_class"] for row in runtime_rows)
    action_class_counts = Counter(row["action_class"] for row in runtime_rows)
    proxy_r_class_counts = Counter(row["proxy_r_class"] for row in runtime_rows)
    route_family_counts = Counter(row["route_family"] for row in runtime_rows)
    bucket_counts = Counter(row["target_control_bucket"] for row in runtime_rows)
    source_acquisition_rows = sum(
        1
        for row in runtime_rows
        if row["r_evidence_class"]
        == "TICK_M15_TARGET_CONTROL_PLACEBO_READY_SOURCE_ACQUISITION_REQUIRED"
    )
    runtime_source_rows = len(control_rows)
    wave_source_rows = sum(int(item["rows"]) for item in source_artifacts)
    summary = {
        "schema_version": "gtos_vnext_tick_m15_target_control_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(runtime_rows),
        "runtime_rows_with_event_scope": sum(1 for row in runtime_rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in runtime_rows if not row.get("event_scope")),
        "runtime_source_rows_represented": runtime_source_rows,
        "target_event_rows_represented": _source_row_count(_source_path(TARGET_EVENT_SOURCE)),
        "joined_triage_rows_represented": _source_row_count(_source_path(TRIAGE_SOURCE)),
        "source_acquisition_required_rows": source_acquisition_rows,
        "support_rows_represented": wave_source_rows - runtime_source_rows,
        "wave_source_rows_counted": wave_source_rows,
        "decision_counts": dict(sorted(decision_counts.items())),
        "target_control_bucket_counts": dict(sorted(bucket_counts.items())),
        "source_component_counts": dict(sorted(source_component_counts.items())),
        "source_role_counts": dict(sorted(source_role_counts.items())),
        "source_group_counts": dict(sorted(source_group_counts.items())),
        "source_kind_counts": dict(sorted(source_kind_counts.items())),
        "system_surface_counts": dict(sorted(system_surface_counts.items())),
        "r_evidence_class_counts": dict(sorted(r_evidence_class_counts.items())),
        "action_class_counts": dict(sorted(action_class_counts.items())),
        "proxy_r_class_counts": dict(sorted(proxy_r_class_counts.items())),
        "route_family_counts": dict(sorted(route_family_counts.items())),
        "coverage_counts": coverage,
        "blank_anchor_counts": _blank_anchor_counts(runtime_rows),
        "proxy_score_sum": round(
            sum(float(row.get("proxy_score") or 0.0) for row in runtime_rows),
            12,
        ),
        "source_artifacts": source_artifacts,
        "source_result_counts": result.get("counts", {}),
        "source_open_blockers": result.get("open_blockers", []),
    }
    return runtime_rows, summary


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _write_outputs() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows, summary = _build_runtime_rows()
    _write_jsonl(OUTPUT_ROWS, rows)
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return rows, summary


def _check_outputs() -> None:
    rows, summary = _build_runtime_rows()
    current_rows = OUTPUT_ROWS.read_text(encoding="utf-8")
    expected_rows = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )
    if current_rows != expected_rows:
        raise SystemExit(f"{OUTPUT_ROWS} is stale; rerun without --check")
    current_summary = OUTPUT_SUMMARY.read_text(encoding="utf-8")
    expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if current_summary != expected_summary:
        raise SystemExit(f"{OUTPUT_SUMMARY} is stale; rerun without --check")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        _check_outputs()
        print(json.dumps({"ok": True, "checked": [str(OUTPUT_ROWS), str(OUTPUT_SUMMARY)]}, sort_keys=True))
        return 0
    rows, summary = _write_outputs()
    print(
        json.dumps(
            {
                "ok": True,
                "runtime_rows": len(rows),
                "source_acquisition_required_rows": summary["source_acquisition_required_rows"],
                "output_rows": _path_text(OUTPUT_ROWS),
                "output_summary": _path_text(OUTPUT_SUMMARY),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
