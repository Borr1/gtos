"""Build runtime rows for unified execution decision evidence."""

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
WAVE_ID = "WAVE_UNIFIED_EXECUTION_DECISION_RUNTIME"
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_UNIFIED_EXECUTION_DECISION_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_UNIFIED_EXECUTION_DECISION_RUNTIME_SUMMARY_{DATE}.json"
)

BRANCH_EXECUTION_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_EXECUTION_DECISION_"
    "BRANCH_EXECUTION_LEDGER_2026-05-16.jsonl"
)
IMPLEMENTATION_CANDIDATE_SOURCE = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_EXECUTION_DECISION_"
    "IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-16.jsonl"
)
PRIMARY_SOURCES = (BRANCH_EXECUTION_SOURCE, IMPLEMENTATION_CANDIDATE_SOURCE)

SUPPORT_SOURCES = (
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_EXECUTION_DECISION_"
    "BUCKET_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_EXECUTION_DECISION_"
    "QUESTION_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_EXECUTION_DECISION_"
    "SCORER_SPEC_LEDGER_2026-05-16.jsonl",
    "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_EXECUTION_DECISION_"
    "SOURCE_MANIFEST_LEDGER_2026-05-16.jsonl",
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

SHAPES = {
    "AVOID_OR_REDIRECT_SPEC": (
        "AVOID",
        "unified_execution_decision_avoid_redirect",
        "unified_execution_decision_avoid_redirect_filter",
        "UNIFIED_EXECUTION_DECISION_AVOID_OR_REDIRECT",
    ),
    "FILLABILITY_RETEST_REDESIGN_SPEC": (
        "AVOID",
        "unified_execution_decision_fillability_retest_redesign",
        "unified_execution_decision_fillability_retest_avoid_filter",
        "UNIFIED_EXECUTION_DECISION_FILLABILITY_RETEST_REDESIGN",
    ),
    "MARKET_ENTRY_COMPARATOR_SPEC": (
        "FOLLOW",
        "unified_execution_decision_market_entry_challenger",
        "unified_execution_decision_market_entry_follow",
        "UNIFIED_EXECUTION_DECISION_MARKET_ENTRY_CHALLENGER",
    ),
    "MARKET_GAP_ENTRY_GEOMETRY_SPEC": (
        "FOLLOW",
        "unified_execution_decision_market_gap_entry_geometry",
        "unified_execution_decision_market_gap_entry_geometry_follow",
        "UNIFIED_EXECUTION_DECISION_MARKET_GAP_ENTRY_GEOMETRY",
    ),
    "MARKET_GAP_AVOID_INVERSE_SPEC": (
        "AVOID",
        "unified_execution_decision_market_gap_avoid_inverse",
        "unified_execution_decision_market_gap_avoid_inverse_filter",
        "UNIFIED_EXECUTION_DECISION_MARKET_GAP_AVOID_INVERSE",
    ),
    "MARKET_GAP_SOURCE_EXPANSION_SPEC": (
        "AVOID",
        "unified_execution_decision_source_expansion_guard",
        "unified_execution_decision_source_expansion_avoid_filter",
        "UNIFIED_EXECUTION_DECISION_SOURCE_EXPANSION_REQUIRED",
    ),
    "PROVENANCE_REQUIREMENT": (
        "AVOID",
        "unified_execution_decision_provenance_guard",
        "unified_execution_decision_provenance_avoid_filter",
        "UNIFIED_EXECUTION_DECISION_PROVENANCE_REQUIREMENT",
    ),
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


def _shape(row: dict[str, Any]) -> tuple[str, str, str, str]:
    candidate_type = _norm(row.get("implementation_candidate_type"))
    return SHAPES.get(
        candidate_type,
        (
            "AVOID",
            "unified_execution_decision_unclassified_guard",
            "unified_execution_decision_unclassified_avoid_filter",
            "UNIFIED_EXECUTION_DECISION_UNCLASSIFIED_GUARD",
        ),
    )


def _source_kind(source_name: str) -> str:
    if source_name == BRANCH_EXECUTION_SOURCE:
        return "branch_execution_decision"
    return "implementation_candidate_decision"


def _proxy_r_class(decision: str, row: dict[str, Any]) -> str:
    if decision == "FOLLOW":
        return "POSITIVE_PROXY_R"
    if decision == "AVOID":
        midpoint = _to_float(row.get("rstyle_midpoint_mean"))
        if midpoint is not None and abs(midpoint) >= 0.25:
            return "STRONG_NEGATIVE_PROXY_R"
        return "NEGATIVE_PROXY_R"
    return "MIXED_PROXY_R"


def _event_scope(row: dict[str, Any], source_component: str) -> dict[str, str]:
    symbol = _norm(row.get("symbol"))
    target_stop = _norm(row.get("target_stop_contract_id"))
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
            "side": _norm(row.get("side")),
            "entry_variant": _norm(row.get("entry_variant")),
            "target_stop_order_class": target_stop,
            "source_component": source_component,
        }.items()
        if value
    }


def _signed_proxy(decision: str, row: dict[str, Any]) -> float | None:
    midpoint = _to_float(row.get("rstyle_midpoint_mean"))
    if midpoint is None:
        return None
    if decision == "FOLLOW":
        return abs(midpoint)
    if decision == "AVOID":
        return -abs(midpoint)
    return midpoint


def _runtime_row(
    source_name: str,
    source_path: Path,
    source_sha: str,
    source_line_no: int,
    row: dict[str, Any],
) -> dict[str, Any]:
    decision, source_component, action_class, r_evidence_class = _shape(row)
    source_kind = _source_kind(source_name)
    scope = _event_scope(row, source_component)
    source_row_id = (
        _norm(row.get("unified_execution_branch_id"))
        or _norm(row.get("implementation_candidate_id"))
        or _norm(row.get("market_gap_combo_id"))
        or f"{source_name}:{source_line_no}"
    )
    row_id = (
        f"unified_execution_decision:{source_kind}:{source_line_no}:"
        f"{_sha256_text(json.dumps(row, sort_keys=True))[:16]}"
    )

    metrics: dict[str, Any] = {}
    for name, value, source_field in (
        ("proxy_score", _signed_proxy(decision, row), "signed_rstyle_midpoint_mean"),
        ("rstyle_lower_mean", _to_float(row.get("rstyle_lower_mean")), "rstyle_lower_mean"),
        ("rstyle_midpoint_mean", _to_float(row.get("rstyle_midpoint_mean")), "rstyle_midpoint_mean"),
        ("rstyle_upper_mean", _to_float(row.get("rstyle_upper_mean")), "rstyle_upper_mean"),
        ("effective_n", 1.0, "runtime_row"),
    ):
        metric = _metric(value, source_field=source_field)
        if metric is not None:
            metrics[name] = metric

    symbol = scope.get("symbol", "")
    source_group = (
        "unified_execution_decision_follow"
        if decision == "FOLLOW"
        else "unified_execution_decision_avoid_or_repair_guard"
    )
    source_role = (
        action_class.replace("_filter", "_guard")
        if decision == "AVOID"
        else action_class
    )
    runtime = {
        "unified_execution_decision_runtime_row_id": row_id,
        "row_key": row_id,
        "evidence_family": "gtos_vnext_unified_execution_decision",
        "source_name": "gtos_vnext_unified_execution_decision_wave",
        "source_kind": source_kind,
        "source_group": source_group,
        "source_role": source_role,
        "source_component": source_component,
        "system_surface": "execution_adjacent_unified_execution_decision",
        "action_class": action_class,
        "review_action": decision,
        "r_evidence_class": r_evidence_class,
        "proxy_r_class": _proxy_r_class(decision, row),
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
        "side": scope.get("side", ""),
        "entry_variant": scope.get("entry_variant", ""),
        "target_stop_order_class": scope.get("target_stop_order_class", ""),
        "event_scope": scope,
        "source_bound": bool(
            scope.get("symbol")
            and scope.get("route_session")
            and scope.get("horizon_id")
        ),
        "source_complete": True,
        "runtime_candidate_use_permitted": decision in {"FOLLOW", "AVOID"},
        "candidate_use_allowed_now": decision in {"FOLLOW", "AVOID"},
        "orderflow_runtime_validated": True,
        "source_path": _path_text(source_path),
        "source_file_sha256": source_sha,
        "source_line_no": source_line_no,
        "source_row_id": source_row_id,
        "branch_queue_id": row.get("branch_queue_id"),
        "implementation_candidate_id": row.get("implementation_candidate_id"),
        "implementation_candidate_type": row.get("implementation_candidate_type"),
        "primary_export_family": row.get("primary_export_family"),
        "unified_execution_decision": row.get("unified_execution_decision"),
        "unified_next_action": row.get("unified_next_action")
        or row.get("same_resource_next_action"),
        "system_decision_class": row.get("system_decision_class"),
        "system_decision_direction": row.get("system_decision_direction"),
        "target_stop_result": row.get("target_stop_result"),
        "nofill_join_status": row.get("nofill_join_status"),
        "nofill_transfer_implication": row.get("nofill_transfer_implication"),
        "rstyle_proxy_signal_class": row.get("rstyle_proxy_signal_class"),
        "execution_pressure_class": row.get("execution_pressure_class"),
        "source_repair_pressure_class": row.get("source_repair_pressure_class"),
        "sealed_or_proxy_outcome_status": row.get("sealed_or_proxy_outcome_status"),
        "ambiguity_status": row.get("ambiguity_status"),
        "market_gap_combo_id": row.get("market_gap_combo_id"),
        "exact_failure_cause": row.get("exact_failure_cause"),
        "exact_success_cause": row.get("exact_success_cause"),
        "exact_missing_geometry_or_source_reason": row.get(
            "exact_missing_geometry_or_source_reason"
        ),
        "source_manifest_hash": row.get("source_manifest_hash"),
        "source_not_completion": bool(row.get("not_completion", False)),
        "r_metrics": metrics,
    }
    return {key: value for key, value in runtime.items() if value not in (None, "", {}, [])}


def build_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    runtime_rows: list[dict[str, Any]] = []
    source_artifacts: list[dict[str, Any]] = []
    for source_name in (*PRIMARY_SOURCES, *SUPPORT_SOURCES):
        path = _source_path(source_name)
        rows = _read_jsonl(path)
        source_sha = _sha256_file(path)
        start_len = len(runtime_rows)
        if source_name in PRIMARY_SOURCES:
            for line_no, row in enumerate(rows, start=1):
                runtime_rows.append(
                    _runtime_row(source_name, path, source_sha, line_no, row)
                )
        source_artifacts.append(
            {
                "name": source_name,
                "path": _path_text(path),
                "rows": len(rows),
                "runtime_rows_read": len(runtime_rows) - start_len,
                "sha256_or_git_blob": source_sha,
                "source_role": (
                    "primary_runtime_rows"
                    if source_name in PRIMARY_SOURCES
                    else "supporting_evidence"
                ),
            }
        )
    return runtime_rows, source_artifacts


def _counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(
        sorted(Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field))).items())
    )


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def build_summary(
    rows: list[dict[str, Any]],
    source_artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
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
        "implementation_candidate_types": _counter(rows, "implementation_candidate_type"),
        "unified_execution_decisions": _counter(rows, "unified_execution_decision"),
        "primary_export_families": _counter(rows, "primary_export_family"),
        "target_stop_results": _counter(rows, "target_stop_result"),
        "source_kinds": _counter(rows, "source_kind"),
    }
    source_rows_represented = sum(
        item["runtime_rows_read"]
        for item in source_artifacts
        if item["source_role"] == "primary_runtime_rows"
    )
    support_rows_represented = sum(
        item["rows"]
        for item in source_artifacts
        if item["source_role"] == "supporting_evidence"
    )
    metric_sum = 0.0
    metric_rows = 0
    for row in rows:
        metric = row.get("r_metrics", {}).get("proxy_score", {})
        if isinstance(metric, dict) and "sum" in metric:
            metric_sum += float(metric["sum"])
            metric_rows += 1
    return {
        "schema_version": "gtos_vnext_unified_execution_decision_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": source_rows_represented,
        "support_rows_represented": support_rows_represented,
        "wave_source_rows_counted": source_rows_represented + support_rows_represented,
        "runtime_rows_with_event_scope": sum(1 for row in rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in rows if not row.get("event_scope")),
        "decision_counts": _counter(rows, "review_action"),
        "source_component_counts": _counter(rows, "source_component"),
        "source_role_counts": _counter(rows, "source_role"),
        "source_group_counts": _counter(rows, "source_group"),
        "system_surface_counts": _counter(rows, "system_surface"),
        "r_evidence_class_counts": _counter(rows, "r_evidence_class"),
        "action_class_counts": _counter(rows, "action_class"),
        "route_family_counts": _counter(rows, "route_family"),
        "source_kind_counts": _counter(rows, "source_kind"),
        "proxy_score_sum": round(metric_sum, 12),
        "proxy_score_row_count": metric_rows,
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "coverage_counts": coverage,
        "source_artifacts": source_artifacts,
    }


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows, source_artifacts = build_rows()
    summary = build_summary(rows, source_artifacts)
    if args.check:
        expected_rows = "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"
        expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
        ok = True
        if not OUTPUT_ROWS.exists() or OUTPUT_ROWS.read_text(encoding="utf-8") != expected_rows:
            print(f"{OUTPUT_ROWS} is stale", file=sys.stderr)
            ok = False
        if (
            not OUTPUT_SUMMARY.exists()
            or OUTPUT_SUMMARY.read_text(encoding="utf-8") != expected_summary
        ):
            print(f"{OUTPUT_SUMMARY} is stale", file=sys.stderr)
            ok = False
        return 0 if ok else 1

    write_outputs(rows, summary)
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
