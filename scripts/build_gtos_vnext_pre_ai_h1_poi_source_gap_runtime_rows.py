#!/usr/bin/env python3
"""Build vNext runtime rows from pre-AI H1 POI source-gap evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_PRE_AI_H1_POI_SOURCE_GAP_RUNTIME"
ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
SOURCE_ROWS_PATH = SOURCE_DIR / "MAIN_ORCH48_PRE_AI_H1_POI_OUTCOME_JOIN_LEDGER_2026-05-18.jsonl"
CAPTURE_ENRICHMENT_LEDGER_PATH = (
    SOURCE_DIR / "MAIN_ORCH48_PRE_AI_H1_POI_CAPTURE_ENRICHMENT_LEDGER_2026-05-18.jsonl"
)
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_PRE_AI_H1_POI_SOURCE_GAP_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_PRE_AI_H1_POI_SOURCE_GAP_RUNTIME_SUMMARY_{DATE}.json"

SOURCE_GAP_ACTION = "PRE_AI_H1_POI_SKIP_NO_OUTCOME_JOIN_SOURCE_CAPTURE_REQUIRED"

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

SESSION_ALIASES = {
    "london": "london_core",
    "london_core": "london_core",
    "ny": "ny_core",
    "new_york": "ny_core",
    "ny_core": "ny_core",
    "tokyo": "tokyo_kz",
    "tokyo_kz": "tokyo_kz",
    "asia": "tokyo_kz",
    "off_core": "off_core_session",
    "off_core_session": "off_core_session",
}

SIDE_BY_SKIP_BIAS = {
    "bullish": "LONG",
    "bearish": "SHORT",
}

SOURCE_COMPONENT_BY_SKIP_BIAS = {
    "bullish": "pre_ai_h1_poi_bullish_source_gap",
    "bearish": "pre_ai_h1_poi_bearish_source_gap",
}

SUPPORT_NAMES = (
    "MAIN_ORCH48_PRE_AI_H1_POI_OUTCOME_JOIN_MANIFEST_2026-05-18.json",
    "MAIN_ORCH48_PRE_AI_H1_POI_OUTCOME_JOIN_SUMMARY_2026-05-18.json",
    "MAIN_ORCH48_PRE_AI_H1_POI_OUTCOME_JOIN_VERIFY_RESULT_2026-05-18.json",
    "MAIN_ORCH48_PRE_AI_H1_POI_CAPTURE_ENRICHMENT_LEDGER_2026-05-18.jsonl",
    "MAIN_ORCH48_PRE_AI_H1_POI_CAPTURE_ENRICHMENT_MANIFEST_2026-05-18.json",
    "MAIN_ORCH48_PRE_AI_H1_POI_CAPTURE_ENRICHMENT_SUMMARY_2026-05-18.json",
    "MAIN_ORCH48_PRE_AI_H1_POI_CAPTURE_ENRICHMENT_VERIFY_RESULT_2026-05-18.json",
    "build_main_orch48_pre_ai_h1_poi_capture_enrichment_2026_05_18.py",
    "build_main_orch48_pre_ai_h1_poi_outcome_join_2026_05_18.py",
    "verify_main_orch48_pre_ai_h1_poi_capture_enrichment_2026_05_18.py",
    "verify_main_orch48_pre_ai_h1_poi_outcome_join_2026_05_18.py",
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _path_text(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _count_nonempty_lines(path: Path) -> int:
    if path.suffix.lower() == ".json":
        return 1
    if path.suffix.lower() not in {".jsonl", ".csv", ".txt", ".md", ".py"}:
        return 0
    try:
        with path.open("rb") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


def _support_paths() -> list[Path]:
    paths: list[Path] = []
    for name in SUPPORT_NAMES:
        path = SOURCE_DIR / name
        if path.exists():
            paths.append(path)
    return paths


def _route_session(row: dict[str, Any]) -> str:
    raw = _norm(row.get("session_tag") or row.get("kill_zone")).casefold()
    return SESSION_ALIASES.get(raw, "off_core_session")


def _side_from_row(row: dict[str, Any]) -> str:
    bias = _norm(row.get("pre_ai_gate_skip_bias")).casefold()
    return SIDE_BY_SKIP_BIAS.get(bias, "")


def _component_from_row(row: dict[str, Any]) -> str:
    bias = _norm(row.get("pre_ai_gate_skip_bias")).casefold()
    return SOURCE_COMPONENT_BY_SKIP_BIAS.get(
        bias,
        "pre_ai_h1_poi_directional_source_gap",
    )


def _metric(value: float, *, source_field: str) -> dict[str, Any]:
    return {
        "sum": value,
        "count": 1,
        "mean": value,
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "source_field": source_field,
        "source_shape": "pre_ai_h1_poi_source_gap_row",
    }


def build_runtime_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_hash = _sha256_file(SOURCE_ROWS_PATH) if SOURCE_ROWS_PATH.exists() else ""
    runtime_rows: list[dict[str, Any]] = []
    skip_rows = [
        row
        for row in source_rows
        if _norm(row.get("pre_ai_h1_poi_outcome_action")) == SOURCE_GAP_ACTION
    ]
    for index, row in enumerate(skip_rows, start=1):
        symbol = _norm(row.get("symbol"))
        side = _side_from_row(row)
        route_session = _route_session(row)
        source_component = _component_from_row(row)
        source_row_id = (
            _norm(row.get("pre_ai_h1_poi_outcome_join_row_id"))
            or _norm(row.get("row_key"))
            or f"pre_ai_h1_poi_source_gap_{index:05d}"
        )
        runtime_row_id = f"PRE_AI_H1_POI_SOURCE_GAP_RUNTIME_{index:05d}"
        event_scope = {
            "symbol": symbol,
            "source_symbol": symbol,
            "market": symbol,
            "timeframe": "M15",
            "market_timeframe": "M15",
            "route_session": route_session,
            "side": side,
            "route_family": "source_discovery",
            "source_component": source_component,
        }
        runtime_rows.append(
            {
                "schema_version": "gtos_vnext_pre_ai_h1_poi_source_gap_runtime_row_v1",
                "wave_id": WAVE_ID,
                "pre_ai_h1_poi_source_gap_runtime_row_id": runtime_row_id,
                "source_row_id": source_row_id,
                "source_path": _path_text(SOURCE_ROWS_PATH),
                "source_artifact": _path_text(SOURCE_ROWS_PATH),
                "source_artifact_hash": source_hash,
                "candidate_features_source_line_no": row.get("candidate_features_source_line_no"),
                "candidate_features_source_path": _norm(row.get("candidate_features_source_path")),
                "candidate_features_source_sha256": _norm(row.get("candidate_features_source_sha256")),
                "outcome_source_path": _norm(row.get("outcome_source_path")),
                "outcome_source_sha256": _norm(row.get("outcome_source_sha256")),
                "evaluation_id": _norm(row.get("evaluation_id")),
                "normalized_evaluation_id": _norm(row.get("normalized_evaluation_id")),
                "timestamp_utc": _norm(row.get("timestamp_utc")),
                "pre_ai_gate_decision": _norm(row.get("pre_ai_gate_decision")),
                "pre_ai_gate_reason": _norm(row.get("pre_ai_gate_reason")),
                "pre_ai_gate_skip_bias": _norm(row.get("pre_ai_gate_skip_bias")),
                "directional_poi_detail_capture_state": _norm(
                    row.get("directional_poi_detail_capture_state")
                ),
                "source_gap_action": SOURCE_GAP_ACTION,
                "saved_ai_call_reference": bool(row.get("saved_ai_call_reference")),
                "decision_at_capture": _norm(row.get("decision")),
                "symbol": symbol,
                "source_symbol": symbol,
                "market": symbol,
                "symbol_family": resolve_vnext_symbol_family(symbol),
                "timeframe": "M15",
                "market_timeframe": "M15",
                "route_session": route_session,
                "side": side,
                "route_family": "source_discovery",
                "source_component": source_component,
                "source_group": "pre_ai_h1_poi_source_gap_materialization",
                "source_role": "pre_ai_h1_poi_source_gap_guard",
                "source_name": "gtos_vnext_pre_ai_h1_poi_source_gap_wave",
                "evidence_family": "gtos_vnext_pre_ai_h1_poi_source_gap",
                "system_surface": "pre_ai_h1_poi_directional_source_gap_runtime",
                "action_family": "pre_ai_h1_poi_source_materialization_guard",
                "action_class": "pre_ai_h1_poi_directional_source_capture_required",
                "r_evidence_class": "PRE_AI_H1_POI_DIRECTIONAL_SOURCE_CAPTURE_REQUIRED",
                "review_action": "MIXED_SOURCE_CAPTURE_GUARD",
                "decision": "MIXED",
                "candidate_use_allowed_now": False,
                "runtime_candidate_use_permitted": False,
                "source_complete": False,
                "source_bound": True,
                "source_acquisition_required": True,
                "source_acquisition_kind": "pre_ai_h1_poi_directional_framework_source_gap",
                "runtime_decision_effect": False,
                "gate_config_change_now": False,
                "event_scope": event_scope,
                "r_metrics": {
                    "proxy_score": _metric(0.0, source_field="source_gap_no_candidate_use"),
                    "effective_n": _metric(1.0, source_field="source_gap_runtime_row"),
                    "saved_ai_call_reference": _metric(
                        1.0 if row.get("saved_ai_call_reference") else 0.0,
                        source_field="saved_ai_call_reference",
                    ),
                },
                "runtime_source_key": _sha256_text(
                    "|".join((symbol, route_session, side, source_component, source_row_id))
                ),
            }
        )
    return runtime_rows


def _dimension_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field)))
    return dict(sorted(counts.items()))


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def _source_artifact_stats(
    source_rows: list[dict[str, Any]],
    runtime_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stats = [
        {
            "path": _path_text(SOURCE_ROWS_PATH),
            "rows": len(source_rows),
            "runtime_rows_read": len(runtime_rows),
            "sha256_or_git_blob": _sha256_file(SOURCE_ROWS_PATH),
            "source_role": "runtime_source_rows",
        }
    ]
    for path in _support_paths():
        role = (
            "capture_enrichment_child"
            if path == CAPTURE_ENRICHMENT_LEDGER_PATH
            else "supporting_evidence"
        )
        stats.append(
            {
                "path": _path_text(path),
                "rows": _count_nonempty_lines(path),
                "runtime_rows_read": 0,
                "sha256_or_git_blob": _sha256_file(path),
                "source_role": role,
            }
        )
    return stats


def summarize(source_rows: list[dict[str, Any]], runtime_rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_artifacts = _source_artifact_stats(source_rows, runtime_rows)
    skip_rows = [
        row
        for row in source_rows
        if _norm(row.get("pre_ai_h1_poi_outcome_action")) == SOURCE_GAP_ACTION
    ]
    return {
        "schema_version": "gtos_vnext_pre_ai_h1_poi_source_gap_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "source_path": _path_text(SOURCE_ROWS_PATH),
        "source_artifacts": source_artifacts,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "source_row_count": len(source_rows),
        "source_gap_row_count": len(skip_rows),
        "runtime_row_count": len(runtime_rows),
        "runtime_source_rows_represented": len(runtime_rows),
        "capture_enrichment_child_rows_represented": _count_nonempty_lines(
            CAPTURE_ENRICHMENT_LEDGER_PATH
        ),
        "support_rows_represented": sum(
            item["rows"]
            for item in source_artifacts
            if item["source_role"] in {"supporting_evidence", "capture_enrichment_child"}
        ),
        "runtime_wave_source_rows_counted": len(runtime_rows)
        + sum(
            item["rows"]
            for item in source_artifacts
            if item["source_role"] in {"supporting_evidence", "capture_enrichment_child"}
        ),
        "runtime_rows_with_event_scope": sum(1 for row in runtime_rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in runtime_rows if not row.get("event_scope")),
        "source_acquisition_required_rows": sum(
            1 for row in runtime_rows if row.get("source_acquisition_required")
        ),
        "decision_counts": _dimension_counts(runtime_rows, "decision"),
        "r_evidence_class_counts": _dimension_counts(runtime_rows, "r_evidence_class"),
        "source_component_counts": _dimension_counts(runtime_rows, "source_component"),
        "source_role_counts": _dimension_counts(runtime_rows, "source_role"),
        "source_group_counts": _dimension_counts(runtime_rows, "source_group"),
        "action_class_counts": _dimension_counts(runtime_rows, "action_class"),
        "pre_ai_gate_reason_counts": _dimension_counts(runtime_rows, "pre_ai_gate_reason"),
        "blank_anchor_counts": _blank_anchor_counts(runtime_rows),
        "coverage_counts": {
            "symbols": _dimension_counts(runtime_rows, "symbol"),
            "markets": _dimension_counts(runtime_rows, "market"),
            "source_symbols": _dimension_counts(runtime_rows, "source_symbol"),
            "timeframes": _dimension_counts(runtime_rows, "timeframe"),
            "sessions": _dimension_counts(runtime_rows, "route_session"),
            "sides": _dimension_counts(runtime_rows, "side"),
            "entry_variants": _dimension_counts(runtime_rows, "entry_variant"),
            "target_stop_order_classes": _dimension_counts(runtime_rows, "target_stop_order_class"),
            "source_components": _dimension_counts(runtime_rows, "source_component"),
            "source_roles": _dimension_counts(runtime_rows, "source_role"),
            "primitives": _dimension_counts(runtime_rows, "primitive"),
        },
        "source_artifact_hash": _sha256_file(SOURCE_ROWS_PATH) if SOURCE_ROWS_PATH.exists() else "",
        "capture_enrichment_artifact_hash": (
            _sha256_file(CAPTURE_ENRICHMENT_LEDGER_PATH)
            if CAPTURE_ENRICHMENT_LEDGER_PATH.exists()
            else ""
        ),
        "row_id_samples": [
            row.get("pre_ai_h1_poi_source_gap_runtime_row_id")
            for row in runtime_rows[:10]
        ],
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Build without writing outputs")
    args = parser.parse_args()

    source_rows = _read_jsonl(SOURCE_ROWS_PATH)
    runtime_rows = build_runtime_rows(source_rows)
    summary = summarize(source_rows, runtime_rows)
    if not args.check:
        write_jsonl(OUTPUT_ROWS, runtime_rows)
        OUTPUT_SUMMARY.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
