#!/usr/bin/env python3
"""Build vNext runtime rows for Main Orch24 implementation-selection evidence."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_gtos_vnext_main_orch24_action_completeness_residual_r_runtime_rows import (
    _action_behavior,
    _candidate_session,
    _float,
    _git_blob_sha1,
    _long_path,
    _metric,
    _norm,
    _path_text,
    _proxy_class,
    _proxy_value,
    _read_jsonl,
    _sha256_file,
    _sha256_payload,
    _source_row_count,
)
from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_main_orch24_implementation_selection_runtime"
SOURCE_NAME = "gtos_vnext_main_orch24_implementation_selection_runtime_wave"
RUNTIME_SURFACE = "main_orch24_implementation_selection_action_runtime"

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
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME_SUMMARY_{DATE}.json"
)

LEDGER_SOURCES = (
    (
        "implementation_recompute_branch_action",
        "MAIN_ORCH24_IMPLEMENTATION_RECOMPUTE_BRANCH_ACTION_LEDGER_2026-05-16.jsonl",
    ),
    (
        "implementation_selection",
        "MAIN_ORCH24_IMPLEMENTATION_SELECTION_LEDGER_2026-05-17.jsonl",
    ),
    (
        "captured_metadata_scorer_split",
        "MAIN_ORCH24_ACTION_AFTER_CAPTURED_METADATA_SCORER_SPLIT_LEDGER_2026-05-17.jsonl",
    ),
    (
        "scorer_source_capture_recompute_delta",
        "MAIN_ORCH24_SCORER_SOURCE_CAPTURE_RECOMPUTE_DELTA_LEDGER_2026-05-16.jsonl",
    ),
)

SELECTED_SOURCE_ARTIFACTS = (
    "build_main_orchestrator_implementation_recompute_branch_action_ledger_2026_05_16.py",
    "MAIN_ORCH24_IMPLEMENTATION_RECOMPUTE_BRANCH_ACTION_LEDGER_2026-05-16.jsonl",
    "MAIN_ORCH24_IMPLEMENTATION_RECOMPUTE_BRANCH_ACTION_OUTPUT_MANIFEST_2026-05-16.json",
    "MAIN_ORCH24_IMPLEMENTATION_RECOMPUTE_BRANCH_ACTION_SUMMARY_2026-05-16.json",
    "MAIN_ORCH24_IMPLEMENTATION_RECOMPUTE_BRANCH_ACTION_VERIFICATION_RESULT_2026-05-16.json",
    "verify_main_orchestrator_implementation_recompute_branch_action_ledger_2026_05_16.py",
    "build_main_orchestrator_implementation_selection_2026_05_17.py",
    "MAIN_ORCH24_IMPLEMENTATION_SELECTION_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_IMPLEMENTATION_SELECTION_OUTPUT_MANIFEST_2026-05-17.json",
    "MAIN_ORCH24_IMPLEMENTATION_SELECTION_SUMMARY_2026-05-17.json",
    "MAIN_ORCH24_IMPLEMENTATION_SELECTION_VERIFICATION_RESULT_2026-05-17.json",
    "verify_main_orchestrator_implementation_selection_2026_05_17.py",
    "build_main_orchestrator_action_after_captured_metadata_scorer_split_2026_05_17.py",
    "MAIN_ORCH24_ACTION_AFTER_CAPTURED_METADATA_SCORER_SPLIT_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_ACTION_AFTER_CAPTURED_METADATA_SCORER_SPLIT_OUTPUT_MANIFEST_2026-05-17.json",
    "MAIN_ORCH24_ACTION_AFTER_CAPTURED_METADATA_SCORER_SPLIT_SUMMARY_2026-05-17.json",
    "MAIN_ORCH24_CAPTURED_METADATA_SCORER_SPLIT_VERIFICATION_RESULT_2026-05-17.json",
    "verify_main_orchestrator_action_after_captured_metadata_scorer_split_2026_05_17.py",
    "build_main_orchestrator_scorer_source_capture_recompute_delta_2026_05_16.py",
    "MAIN_ORCH24_SCORER_SOURCE_CAPTURE_RECOMPUTE_DELTA_LEDGER_2026-05-16.jsonl",
    "MAIN_ORCH24_SCORER_SOURCE_CAPTURE_RECOMPUTE_DELTA_OUTPUT_MANIFEST_2026-05-16.json",
    "MAIN_ORCH24_SCORER_SOURCE_CAPTURE_RECOMPUTE_DELTA_SUMMARY_2026-05-16.json",
    "MAIN_ORCH24_SCORER_SOURCE_CAPTURE_RECOMPUTE_DELTA_VERIFICATION_RESULT_2026-05-16.json",
    "verify_main_orchestrator_scorer_source_capture_recompute_delta_2026_05_16.py",
)

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "route_family",
    "primitive",
    "side",
    "entry_variant",
    "target_stop_order_class",
    "source_component",
)


def _source_path(name: str) -> Path:
    return SOURCE_DIR / name


def _scope(row: dict[str, Any], behavior: dict[str, Any]) -> dict[str, str]:
    symbol = _norm(row.get("symbol"))
    side = _norm(row.get("side")) or "ALL_SIDES"
    surface = _norm(row.get("source_capture_surface")) or _norm(row.get("primitive_family"))
    primitive = surface or _norm(row.get("strategy_id")) or "main_orch24_implementation_selection"
    entry = surface or _norm(row.get("strategy_id")) or "implementation_selection"
    target_stop = (
        _norm(row.get("data_requirement_state"))
        or _norm(row.get("coverage_status"))
        or _norm(row.get("implementation_decision"))
        or "implementation_selection"
    )
    scope = {
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": _candidate_session(symbol, row.get("candidate_id"), row),
        "route_family": "main_orch24_implementation_selection",
        "primitive": primitive,
        "source_component": behavior["source_component"],
        "side": side,
        "entry_variant": entry,
        "target_stop_order_class": target_stop,
    }
    if symbol:
        scope.update(
            {
                "symbol": symbol,
                "source_symbol": symbol,
                "market": symbol,
                "symbol_family": resolve_vnext_symbol_family(symbol),
            }
        )
    return {key: value for key, value in scope.items() if value}


def _runtime_row(
    *,
    source_label: str,
    source_path: Path,
    source_sha: str,
    line_no: int,
    row: dict[str, Any],
) -> dict[str, Any]:
    behavior = _action_behavior(row)
    scope = _scope(row, behavior)
    proxy, proxy_field = _proxy_value(row)
    proxy_class = _proxy_class(proxy, behavior["decision"])
    row_hash = _sha256_payload(row)
    metrics = {
        key: value
        for key, value in {
            "proxy_score": _metric(proxy, source_field=proxy_field) if proxy_field else None,
            "cost_adjusted_simulated_r": _metric(proxy, source_field=proxy_field) if proxy_field else None,
            "proxy_r_delta": _metric(_float(row.get("proxy_r_delta")), source_field="proxy_r_delta"),
        }.items()
        if value is not None
    }
    runtime = {
        "schema_version": "gtos_vnext_main_orch24_implementation_selection_runtime_row_v1",
        "row_type": "gtos_vnext_main_orch24_implementation_selection_runtime_row",
        "main_orch24_implementation_selection_runtime_row_id": (
            f"main_orch24_implementation_selection:{source_label}:{line_no}:{row_hash[:16]}"
        ),
        "row_key": f"main_orch24_implementation_selection:{source_label}:{line_no}:{row_hash[:16]}",
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "batch_wave_id": WAVE_ID,
        "source_artifact": _path_text(source_path),
        "source_file_sha256": source_sha,
        "source_line_no": line_no,
        "source_row_id": row.get("row_id"),
        "candidate_id": row.get("candidate_id"),
        "source_payload_hash": row_hash,
        "source_label": source_label,
        "source_group": behavior["source_group"],
        "source_role": behavior["source_role"],
        "source_component": behavior["source_component"],
        "system_surface": behavior["system_surface"],
        "action_class": behavior["action_class"],
        "review_action": behavior["decision"],
        "decision": behavior["decision"],
        "r_evidence_class": behavior["r_evidence_class"],
        "proxy_r_class": proxy_class,
        "event_scope": scope,
        "source_bound": bool(scope.get("source_component")),
        "candidate_use_allowed_now": False,
        "runtime_candidate_use_permitted": behavior["decision"] == "FOLLOW",
        "fresh_moonshot_cp_evidence_override_allowed": False,
        "legacy_cannot_override_fresher_cp280_cp281_cp282": True,
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "runtime_effect_now": "main_orch24_implementation_selection_shadow_runtime",
        "source_acquisition_required": behavior.get("source_acquisition_required", False),
        "source_acquisition_kind": behavior.get("source_acquisition_kind"),
        "original_action_class": row.get("action_class"),
        "implementation_decision": row.get("implementation_decision"),
        "branch_decision": row.get("branch_decision"),
        "coverage_status": row.get("coverage_status"),
        "data_requirement_state": row.get("data_requirement_state"),
        "source_capture_surface": row.get("source_capture_surface"),
        "primitive_family": row.get("primitive_family"),
        "source_plate": row.get("source_plate"),
        "strategy_id": row.get("strategy_id"),
        "framework": row.get("framework"),
        "after_proxy_r": _float(row.get("after_proxy_r")),
        "before_proxy_r": _float(row.get("before_proxy_r")),
        "proxy_r_delta": _float(row.get("proxy_r_delta")),
        "exact_r": _float(row.get("exact_r")),
        "r_metrics": metrics,
    }
    runtime.update(scope)
    return {key: value for key, value in runtime.items() if value not in (None, "", {}, [])}


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_label, filename in LEDGER_SOURCES:
        path = _source_path(filename)
        source_sha = _sha256_file(path)
        for line_no, row in enumerate(_read_jsonl(path), start=1):
            rows.append(
                _runtime_row(
                    source_label=source_label,
                    source_path=path,
                    source_sha=source_sha,
                    line_no=line_no,
                    row=row,
                )
            )
    return rows


def _coverage_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    keys = {
        "symbols": "symbol",
        "source_symbols": "source_symbol",
        "markets": "market",
        "timeframes": "timeframe",
        "market_timeframes": "market_timeframe",
        "sessions": "route_session",
        "sides": "side",
        "source_components": "source_component",
        "entry_variants": "entry_variant",
        "target_stop_order_classes": "target_stop_order_class",
        "route_families": "route_family",
    }
    return {
        label: dict(Counter(row.get(field) for row in rows if row.get(field)))
        for label, field in keys.items()
    }


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not row.get(field))
        for field in ANCHOR_FIELDS
    }


def _source_artifacts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_reads = Counter(Path(row["source_artifact"]).name for row in rows)
    artifacts: list[dict[str, Any]] = []
    for name in SELECTED_SOURCE_ARTIFACTS:
        path = _source_path(name)
        row_count = _source_row_count(path)
        artifacts.append(
            {
                "path": _path_text(path),
                "row_count": row_count,
                "runtime_rows_read": int(runtime_reads.get(name, 0)),
                "hash": _sha256_file(path) if path.suffix.casefold() in {".jsonl", ".json"} else _git_blob_sha1(path),
            }
        )
    return artifacts


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_artifacts = _source_artifacts(rows)
    runtime_source_rows = sum(item["runtime_rows_read"] for item in source_artifacts)
    total_source_rows = sum(item["row_count"] for item in source_artifacts)
    return {
        "schema_version": "gtos_vnext_main_orch24_implementation_selection_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "runtime_surface": RUNTIME_SURFACE,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "source_artifacts": source_artifacts,
        "selected_open_unit_count": len(SELECTED_SOURCE_ARTIFACTS),
        "row_count_unknown_unit_count": 0,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": runtime_source_rows,
        "wave_source_rows_counted": total_source_rows,
        "support_rows_represented": total_source_rows - runtime_source_rows,
        "decision_counts": dict(Counter(row["decision"] for row in rows)),
        "original_action_class_counts": dict(Counter(row.get("original_action_class", "") for row in rows)),
        "source_label_counts": dict(Counter(row["source_label"] for row in rows)),
        "source_component_counts": dict(Counter(row["source_component"] for row in rows)),
        "source_role_counts": dict(Counter(row["source_role"] for row in rows)),
        "r_evidence_class_counts": dict(Counter(row["r_evidence_class"] for row in rows)),
        "proxy_r_class_counts": dict(Counter(row["proxy_r_class"] for row in rows)),
        "source_acquisition_required_rows": sum(1 for row in rows if row.get("source_acquisition_required")),
        "runtime_candidate_use_permitted_rows": sum(1 for row in rows if row["runtime_candidate_use_permitted"]),
        "candidate_use_allowed_now_rows": 0,
        "runtime_trading_or_live_broker_effect_rows": 0,
        "broker_operation_rows": 0,
        "paid_api_or_vendor_call_rows": 0,
        "coverage_counts": _coverage_counts(rows),
        "blank_anchor_counts": _blank_anchor_counts(rows),
    }


def write_outputs() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = build_rows()
    summary = build_summary(rows)
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return rows, summary


def _current_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def check_outputs() -> tuple[bool, str]:
    rows = build_rows()
    summary = build_summary(rows)
    expected_rows = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )
    expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if _current_text(OUTPUT_ROWS) != expected_rows:
        return False, f"{OUTPUT_ROWS} is stale or missing"
    if _current_text(OUTPUT_SUMMARY) != expected_summary:
        return False, f"{OUTPUT_SUMMARY} is stale or missing"
    return True, f"Main Orch24 implementation-selection runtime outputs are current: {len(rows)} rows"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify generated outputs are current")
    args = parser.parse_args()
    if args.check:
        ok, message = check_outputs()
        print(message)
        return 0 if ok else 1
    rows, summary = write_outputs()
    print(
        json.dumps(
            {
                "rows": len(rows),
                "runtime_rows": str(OUTPUT_ROWS),
                "summary": str(OUTPUT_SUMMARY),
                "decision_counts": summary["decision_counts"],
                "source_acquisition_required_rows": summary[
                    "source_acquisition_required_rows"
                ],
                "blank_anchor_counts": summary["blank_anchor_counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
