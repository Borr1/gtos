#!/usr/bin/env python3
"""Build runtime rows for unified candidate scoring execution evidence."""

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
WAVE_ID = "WAVE_UNIFIED_CANDIDATE_SCORING_EXECUTION_RUNTIME"
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_UNIFIED_CANDIDATE_SCORING_EXECUTION_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_UNIFIED_CANDIDATE_SCORING_EXECUTION_RUNTIME_SUMMARY_{DATE}.json"
)

AVOID_INVERSE_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_SCORING_"
    "AVOID_INVERSE_EXECUTION_LEDGER_2026-05-16.jsonl"
)
ENTRY_GEOMETRY_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_SCORING_"
    "ENTRY_GEOMETRY_EXECUTION_LEDGER_2026-05-16.jsonl"
)
PRIMARY_SOURCES = (AVOID_INVERSE_SOURCE, ENTRY_GEOMETRY_SOURCE)

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

SOURCE_BEHAVIOR = {
    AVOID_INVERSE_SOURCE: {
        "source_kind": "avoid_inverse_execution",
        "review_action": "AVOID",
        "source_component": "unified_candidate_scoring_avoid_inverse_execution",
        "action_class": "unified_candidate_scoring_avoid_inverse_filter",
        "source_group": "execution_adjacent_avoid_filter",
        "source_role": "unified_candidate_scoring_avoid_inverse_guard",
        "system_surface": "execution_adjacent_candidate_scoring_avoid_inverse",
        "r_evidence_class": "UNIFIED_CANDIDATE_SCORING_EXECUTION_AVOID_INVERSE",
    },
    ENTRY_GEOMETRY_SOURCE: {
        "source_kind": "entry_geometry_execution",
        "review_action": "FOLLOW",
        "source_component": "unified_candidate_scoring_entry_geometry_execution",
        "action_class": "unified_candidate_scoring_entry_geometry_follow",
        "source_group": "unified_candidate_scoring_entry_geometry",
        "source_role": "unified_candidate_scoring_entry_geometry_follow",
        "system_surface": "execution_adjacent_candidate_scoring_entry_geometry",
        "r_evidence_class": "UNIFIED_CANDIDATE_SCORING_EXECUTION_ENTRY_GEOMETRY",
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


def _proxy_r_class(decision: str, band: str) -> str:
    strong = _norm(band).upper() == "SCORE_BAND_HIGH"
    if decision == "AVOID":
        return "STRONG_NEGATIVE_PROXY_R" if strong else "NEGATIVE_PROXY_R"
    return "STRONG_POSITIVE_PROXY_R" if strong else "POSITIVE_PROXY_R"


def _event_scope(row: dict[str, Any], behavior: dict[str, str]) -> dict[str, str]:
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
            "source_component": behavior["source_component"],
        }.items()
        if value
    }


def _runtime_row(
    source_name: str,
    source_path: Path,
    source_sha: str,
    source_line_no: int,
    row: dict[str, Any],
) -> dict[str, Any]:
    behavior = SOURCE_BEHAVIOR[source_name]
    decision = behavior["review_action"]
    raw_proxy = _to_float(row.get("candidate_score_proxy"))
    signed_proxy = None
    if raw_proxy is not None:
        signed_proxy = -abs(raw_proxy) if decision == "AVOID" else abs(raw_proxy)
    flagged_n = _to_float(row.get("flagged_n"))
    control_n = _to_float(row.get("control_n"))
    scope = _event_scope(row, behavior)
    source_row_id = (
        _norm(row.get("market_gap_candidate_score_id"))
        or _norm(row.get("market_gap_action_id"))
        or f"{source_name}:{source_line_no}"
    )
    row_id = (
        f"unified_candidate_scoring_execution:{behavior['source_kind']}:"
        f"{source_line_no}:{_sha256_text(json.dumps(row, sort_keys=True))[:16]}"
    )

    metrics: dict[str, Any] = {}
    for name, value, source_field in (
        ("proxy_score", signed_proxy, "signed_candidate_score_proxy"),
        ("effective_n", flagged_n, "flagged_n"),
        ("control_n", control_n, "control_n"),
        ("flagged_to_control_ratio", _to_float(row.get("flagged_to_control_ratio")), "flagged_to_control_ratio"),
        ("delta_alignment_rate", _to_float(row.get("delta_alignment_rate")), "delta_alignment_rate"),
        ("delta_mean_abs_future_change", _to_float(row.get("delta_mean_abs_future_change")), "delta_mean_abs_future_change"),
    ):
        metric = _metric(value, source_field=source_field)
        if metric is not None:
            metrics[name] = metric

    symbol = scope.get("symbol", "")
    runtime = {
        "unified_candidate_scoring_execution_runtime_row_id": row_id,
        "row_key": row_id,
        "evidence_family": "gtos_vnext_unified_candidate_scoring_execution",
        "source_name": "gtos_vnext_unified_candidate_scoring_execution_wave",
        "source_kind": behavior["source_kind"],
        "source_group": behavior["source_group"],
        "source_role": behavior["source_role"],
        "source_component": behavior["source_component"],
        "system_surface": behavior["system_surface"],
        "action_class": behavior["action_class"],
        "review_action": decision,
        "r_evidence_class": behavior["r_evidence_class"],
        "proxy_r_class": _proxy_r_class(decision, _norm(row.get("candidate_score_band"))),
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
        "source_complete": True,
        "runtime_candidate_use_permitted": decision in {"FOLLOW", "AVOID"},
        "candidate_use_allowed_now": decision in {"FOLLOW", "AVOID"},
        "orderflow_runtime_validated": True,
        "source_path": _path_text(source_path),
        "source_file_sha256": source_sha,
        "source_line_no": source_line_no,
        "source_row_id": source_row_id,
        "market_gap_action_id": row.get("market_gap_action_id"),
        "market_gap_candidate_score_id": row.get("market_gap_candidate_score_id"),
        "source_market_gap_combo_id": row.get("market_gap_combo_id"),
        "implementation_candidate_type": row.get("implementation_candidate_type"),
        "candidate_scope": row.get("candidate_scope"),
        "candidate_score_band": row.get("candidate_score_band"),
        "candidate_score_class": row.get("candidate_score_class"),
        "candidate_score_formula": row.get("candidate_score_formula"),
        "candidate_score_proxy_raw": raw_proxy,
        "candidate_score_proxy_signed": signed_proxy,
        "candidate_next_action": row.get("candidate_next_action"),
        "movement_status": row.get("movement_status"),
        "nofill_sidecar_status": row.get("nofill_sidecar_status"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get(
            "outside_gbpjpy_xauusd_current_branch_box"
        ),
        "flagged_n": flagged_n,
        "control_n": control_n,
        "flagged_to_control_ratio": _to_float(row.get("flagged_to_control_ratio")),
        "delta_alignment_rate": _to_float(row.get("delta_alignment_rate")),
        "delta_mean_abs_future_change": _to_float(row.get("delta_mean_abs_future_change")),
        "unified_execution_decision": row.get("unified_execution_decision"),
        "source_manifest_hash": row.get("source_manifest_hash"),
        "not_completion": bool(row.get("not_completion", True)),
        "r_metrics": metrics,
    }
    return {key: value for key, value in runtime.items() if value not in (None, "", {}, [])}


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
    return runtime_rows, source_artifacts


def _counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field))).items()))


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


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
        "candidate_score_bands": _counter(rows, "candidate_score_band"),
        "movement_statuses": _counter(rows, "movement_status"),
    }
    flagged_rows = sum(float(row.get("flagged_n") or 0.0) for row in rows)
    control_rows = sum(float(row.get("control_n") or 0.0) for row in rows)
    signed_proxy_sum = sum(float(row.get("candidate_score_proxy_signed") or 0.0) for row in rows)
    raw_proxy_sum = sum(float(row.get("candidate_score_proxy_raw") or 0.0) for row in rows)
    return {
        "schema_version": "gtos_vnext_unified_candidate_scoring_execution_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(rows),
        "runtime_rows_with_event_scope": sum(1 for row in rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in rows if not row.get("event_scope")),
        "runtime_source_rows_represented": len(rows),
        "wave_source_rows_counted": sum(int(item["rows"]) for item in source_artifacts),
        "flagged_rows_represented": flagged_rows,
        "control_rows_represented": control_rows,
        "signed_proxy_score_sum": round(signed_proxy_sum, 12),
        "raw_candidate_score_proxy_sum": round(raw_proxy_sum, 12),
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
            print(
                json.dumps(
                    {"ok": False, "mismatched_outputs": mismatches},
                    indent=2,
                    sort_keys=True,
                )
            )
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
