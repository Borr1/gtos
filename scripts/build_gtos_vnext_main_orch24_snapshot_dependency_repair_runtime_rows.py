#!/usr/bin/env python3
"""Build vNext runtime rows for Main Orch24 snapshot dependency repair evidence."""

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
    _git_blob_sha1,
    _long_path,
    _norm,
    _path_text,
    _read_jsonl,
    _sha256_file,
    _sha256_payload,
    _source_row_count,
)
from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_main_orch24_snapshot_dependency_repair_runtime"
SOURCE_NAME = "gtos_vnext_main_orch24_snapshot_dependency_repair_runtime_wave"
RUNTIME_SURFACE = "main_orch24_snapshot_dependency_repair_runtime"

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
    / f"GTOS_VNEXT_MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME_SUMMARY_{DATE}.json"
)

LEDGER_SOURCES = (
    (
        "current_snapshot_dependency",
        "MAIN_ORCH24_CURRENT_SNAPSHOT_DEPENDENCY_LEDGER_2026-05-16.jsonl",
    ),
    (
        "noncomputable_proof",
        "MAIN_ORCH24_NONCOMPUTABLE_PROOF_LEDGER_2026-05-16.jsonl",
    ),
    (
        "eight_bucket_inventory",
        "MAIN_ORCH24_EIGHT_BUCKET_INVENTORY_2026-05-16.jsonl",
    ),
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


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _route_parts(row: dict[str, Any]) -> dict[str, str]:
    route_candidate_id = _norm(row.get("route_candidate_id"))
    parts = [part for part in route_candidate_id.split("|") if part] if route_candidate_id else []
    return {
        "symbol": _norm(row.get("symbol")) or (parts[0] if len(parts) > 0 else ""),
        "session": _norm(row.get("session")) or (parts[1] if len(parts) > 1 else ""),
        "primitive": _norm(row.get("family")) or (parts[2] if len(parts) > 2 else ""),
        "timeframe": _norm(row.get("timeframe")) or (parts[3].upper() if len(parts) > 3 else ""),
    }


def _has_complete_decision_anchor(row: dict[str, Any]) -> bool:
    parts = _route_parts(row)
    return bool(parts["symbol"] and parts["session"] and _norm(row.get("side")))


def _scope(row: dict[str, Any], source_label: str) -> dict[str, str]:
    if source_label != "noncomputable_proof" or not _has_complete_decision_anchor(row):
        return {}
    parts = _route_parts(row)
    symbol = parts["symbol"]
    target_stop = (
        _norm(row.get("target_stop_contract_id"))
        or _norm(row.get("target_stop_result"))
        or "TARGETSTOP_SOURCE_REPAIR_REQUIRED"
    )
    scope = {
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol),
        "timeframe": parts["timeframe"] or "H4",
        "market_timeframe": parts["timeframe"] or "H4",
        "route_session": parts["session"],
        "route_family": "main_orch24_snapshot_dependency_repair",
        "primitive": parts["primitive"] or "snapshot_dependency_repair",
        "side": _norm(row.get("side")),
        "entry_variant": _norm(row.get("branch_result_class")) or "snapshot_dependency_repair",
        "target_stop_order_class": target_stop,
        "source_component": "main_orch24_snapshot_dependency_source_repair_requirement",
    }
    return {key: value for key, value in scope.items() if value}


def _row_kind(row: dict[str, Any], source_label: str, scope: dict[str, str]) -> dict[str, Any]:
    disposition = _norm(row.get("disposition"))
    if scope:
        return {
            "source_component": "main_orch24_snapshot_dependency_source_repair_requirement",
            "source_role": "main_orch24_snapshot_dependency_source_repair_guard",
            "source_group": "main_orch24_snapshot_dependency_source_repair",
            "system_surface": "main_orch24_snapshot_dependency_source_repair_guard",
            "action_class": "main_orch24_snapshot_dependency_source_repair_requirement",
            "r_evidence_class": "MAIN_ORCH24_SNAPSHOT_DEPENDENCY_SOURCE_REPAIR_REQUIRED",
            "source_acquisition_required": True,
            "source_acquisition_kind": "main_orch24_snapshot_dependency_target_stop_or_exact_r_repair_required",
            "replay_attribution_only": False,
            "row_scope_status": "SCOPED_SOURCE_REPAIR_GUARD",
        }
    if source_label == "eight_bucket_inventory":
        return {
            "source_component": "main_orch24_snapshot_dependency_control_inventory",
            "source_role": "main_orch24_snapshot_dependency_control_inventory",
            "source_group": "main_orch24_snapshot_dependency_control_inventory",
            "system_surface": "main_orch24_snapshot_dependency_control_guard",
            "action_class": "main_orch24_snapshot_dependency_control_inventory",
            "r_evidence_class": "MAIN_ORCH24_SNAPSHOT_DEPENDENCY_CONTROL_GUARD",
            "source_acquisition_required": False,
            "source_acquisition_kind": None,
            "replay_attribution_only": True,
            "row_scope_status": "REPLAY_ATTRIBUTION_CONTROL_ONLY",
        }
    component = "main_orch24_snapshot_dependency_replay_attribution"
    if disposition == "convert_to_feature_control_failure_intelligence":
        component = "main_orch24_snapshot_dependency_failure_intelligence"
    return {
        "source_component": component,
        "source_role": "main_orch24_snapshot_dependency_replay_attribution_only",
        "source_group": "main_orch24_snapshot_dependency_replay_attribution",
        "system_surface": "main_orch24_snapshot_dependency_replay_attribution_only",
        "action_class": "main_orch24_snapshot_dependency_replay_attribution_only",
        "r_evidence_class": "MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPLAY_ATTRIBUTION_ONLY",
        "source_acquisition_required": False,
        "source_acquisition_kind": None,
        "replay_attribution_only": True,
        "row_scope_status": "BLANK_ANCHOR_REPLAY_ATTRIBUTION_ONLY",
    }


def _missing_fields(row: dict[str, Any]) -> list[str]:
    return [str(item) for item in _as_list(row.get("missing_fields")) if _norm(item)]


def _required_capture_fields(row: dict[str, Any]) -> list[str]:
    fields = []
    for field in (
        "required_capture_fields",
        "required_source_fields",
        "missing_fields",
    ):
        fields.extend(str(item) for item in _as_list(row.get(field)) if _norm(item))
    deduped: list[str] = []
    seen: set[str] = set()
    for field in fields:
        if field not in seen:
            seen.add(field)
            deduped.append(field)
    return deduped


def _runtime_row(
    *,
    source_label: str,
    source_path: Path,
    source_sha: str,
    line_no: int,
    row: dict[str, Any],
) -> dict[str, Any]:
    scope = _scope(row, source_label)
    kind = _row_kind(row, source_label, scope)
    row_hash = _sha256_payload(row)
    route_parts = _route_parts(row)
    source_row_id = (
        row.get("dependency_id")
        or row.get("proof_id")
        or row.get("inventory_id")
        or row.get("row_id")
        or f"{source_label}:{line_no}"
    )
    runtime = {
        "schema_version": "gtos_vnext_main_orch24_snapshot_dependency_repair_runtime_row_v1",
        "row_type": "gtos_vnext_main_orch24_snapshot_dependency_repair_runtime_row",
        "main_orch24_snapshot_dependency_repair_runtime_row_id": (
            f"main_orch24_snapshot_dependency_repair:{source_label}:{line_no}:{row_hash[:16]}"
        ),
        "row_key": f"main_orch24_snapshot_dependency_repair:{source_label}:{line_no}:{row_hash[:16]}",
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "batch_wave_id": WAVE_ID,
        "source_artifact": _path_text(source_path),
        "source_file_sha256": source_sha,
        "source_line_no": line_no,
        "source_row_id": source_row_id,
        "source_payload_hash": row_hash,
        "source_label": source_label,
        "source_group": kind["source_group"],
        "source_role": kind["source_role"],
        "source_component": kind["source_component"],
        "system_surface": kind["system_surface"],
        "action_class": kind["action_class"],
        "review_action": "MIXED",
        "decision": "MIXED",
        "r_evidence_class": kind["r_evidence_class"],
        "proxy_r_class": "SOURCE_REPAIR_REQUIRED" if scope else "REPLAY_ATTRIBUTION_ONLY",
        "event_scope": scope,
        "source_bound": bool(scope),
        "candidate_use_allowed_now": False,
        "runtime_candidate_use_permitted": False,
        "fresh_moonshot_cp_evidence_override_allowed": False,
        "legacy_cannot_override_fresher_cp280_cp281_cp282": True,
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "runtime_effect_now": "main_orch24_snapshot_dependency_repair_shadow_runtime",
        "source_acquisition_required": kind["source_acquisition_required"],
        "source_acquisition_kind": kind["source_acquisition_kind"],
        "replay_attribution_only": kind["replay_attribution_only"],
        "row_scope_status": kind["row_scope_status"],
        "candidate_id": row.get("candidate_id"),
        "route_candidate_id": row.get("route_candidate_id"),
        "source_original_row_id": row.get("row_id"),
        "dependency_id": row.get("dependency_id"),
        "proof_id": row.get("proof_id"),
        "inventory_id": row.get("inventory_id"),
        "disposition": row.get("disposition"),
        "bucket": row.get("bucket"),
        "family": row.get("family"),
        "owner": row.get("owner") or row.get("owning_builder_family"),
        "owner_boundary": row.get("owner_boundary"),
        "branch_result_class": row.get("branch_result_class"),
        "target_stop_contract_id": row.get("target_stop_contract_id"),
        "target_stop_result": row.get("target_stop_result"),
        "target_multiple": row.get("target_multiple"),
        "stop_multiple": row.get("stop_multiple"),
        "interval_rows": row.get("interval_rows"),
        "validation_safe": row.get("validation_safe"),
        "missing_fields": _missing_fields(row),
        "missing_field_count": row.get("missing_field_count") or len(_missing_fields(row)),
        "required_capture_fields": _required_capture_fields(row),
        "current_snapshot_dependency_reason": row.get("current_snapshot_dependency_reason")
        or row.get("why_no_weaker_proxy_r_is_computable"),
        "source_rows_represented": 1,
        "source_repair_not_route_pressure_reason": (
            "Blank-anchor rows remain replay attribution only; only complete symbol/session/side rows "
            "can match runtime events and trigger source-acquisition risk."
        ),
    }
    for field, value in {
        "symbol": route_parts["symbol"],
        "source_symbol": route_parts["symbol"],
        "market": route_parts["symbol"],
        "symbol_family": resolve_vnext_symbol_family(route_parts["symbol"]) if route_parts["symbol"] else "",
        "timeframe": route_parts["timeframe"],
        "market_timeframe": route_parts["timeframe"],
        "route_session": route_parts["session"],
        "route_family": scope.get("route_family", ""),
        "primitive": route_parts["primitive"],
        "side": row.get("side"),
        "entry_variant": scope.get("entry_variant", ""),
        "target_stop_order_class": scope.get("target_stop_order_class", ""),
    }.items():
        if _norm(value):
            runtime[field] = value
    return {key: value for key, value in runtime.items() if value not in (None, "", [], {})}


def build_rows() -> list[dict[str, Any]]:
    runtime_rows: list[dict[str, Any]] = []
    for source_label, filename in LEDGER_SOURCES:
        path = _source_path(filename)
        source_sha = _sha256_file(path)
        for line_no, row in enumerate(_read_jsonl(path), start=1):
            runtime_rows.append(
                _runtime_row(
                    source_label=source_label,
                    source_path=path,
                    source_sha=source_sha,
                    line_no=line_no,
                    row=row,
                )
            )
    return runtime_rows


def _coverage_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        "symbols": dict(Counter(row.get("symbol") for row in rows if row.get("symbol"))),
        "source_symbols": dict(Counter(row.get("source_symbol") for row in rows if row.get("source_symbol"))),
        "markets": dict(Counter(row.get("market") for row in rows if row.get("market"))),
        "timeframes": dict(Counter(row.get("timeframe") for row in rows if row.get("timeframe"))),
        "sessions": dict(Counter(row.get("route_session") for row in rows if row.get("route_session"))),
        "sides": dict(Counter(row.get("side") for row in rows if row.get("side"))),
        "entry_variants": dict(Counter(row.get("entry_variant") for row in rows if row.get("entry_variant"))),
        "target_stop_order_classes": dict(
            Counter(row.get("target_stop_order_class") for row in rows if row.get("target_stop_order_class"))
        ),
    }


def _event_scope_coverage_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    scopes = [row.get("event_scope") for row in rows if isinstance(row.get("event_scope"), dict) and row["event_scope"]]
    return {
        "symbols": dict(Counter(scope.get("symbol") for scope in scopes if scope.get("symbol"))),
        "timeframes": dict(Counter(scope.get("timeframe") for scope in scopes if scope.get("timeframe"))),
        "sessions": dict(Counter(scope.get("route_session") for scope in scopes if scope.get("route_session"))),
        "sides": dict(Counter(scope.get("side") for scope in scopes if scope.get("side"))),
        "source_components": dict(Counter(scope.get("source_component") for scope in scopes if scope.get("source_component"))),
        "target_stop_order_classes": dict(
            Counter(scope.get("target_stop_order_class") for scope in scopes if scope.get("target_stop_order_class"))
        ),
    }


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected_paths = [_source_path(filename) for _, filename in LEDGER_SOURCES]
    source_artifacts = [
        {
            "path": _path_text(path),
            "name": path.name,
            "hash": _git_blob_sha1(path),
            "hash_algorithm": "git_blob",
            "row_count": _source_row_count(path),
            "source_batch_wave_id": WAVE_ID,
        }
        for path in selected_paths
    ]
    return {
        "schema_version": "gtos_vnext_main_orch24_snapshot_dependency_repair_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "runtime_surface": RUNTIME_SURFACE,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(int(row.get("source_rows_represented") or 1) for row in rows),
        "wave_source_rows_counted": sum(item["row_count"] for item in source_artifacts),
        "selected_open_unit_count": len(source_artifacts),
        "row_count_unknown_unit_count": 0,
        "source_artifacts": source_artifacts,
        "source_rows_by_label": dict(Counter(row["source_label"] for row in rows)),
        "decision_counts": dict(Counter(row["decision"] for row in rows)),
        "row_scope_status_counts": dict(Counter(row["row_scope_status"] for row in rows)),
        "disposition_counts": dict(Counter(row["disposition"] for row in rows if row.get("disposition"))),
        "bucket_counts": dict(Counter(row["bucket"] for row in rows if row.get("bucket"))),
        "family_counts": dict(Counter(row["family"] for row in rows if row.get("family"))),
        "source_component_counts": dict(Counter(row["source_component"] for row in rows)),
        "source_role_counts": dict(Counter(row["source_role"] for row in rows)),
        "r_evidence_class_counts": dict(Counter(row["r_evidence_class"] for row in rows)),
        "proxy_r_class_counts": dict(Counter(row["proxy_r_class"] for row in rows)),
        "source_acquisition_required_rows": sum(1 for row in rows if row.get("source_acquisition_required")),
        "replay_attribution_only_rows": sum(1 for row in rows if row.get("replay_attribution_only")),
        "matchable_event_scope_rows": sum(
            1 for row in rows if isinstance(row.get("event_scope"), dict) and bool(row["event_scope"])
        ),
        "blank_event_scope_rows": sum(
            1 for row in rows if not (isinstance(row.get("event_scope"), dict) and bool(row["event_scope"]))
        ),
        "runtime_candidate_use_permitted_rows": sum(1 for row in rows if row["runtime_candidate_use_permitted"]),
        "candidate_use_allowed_now_rows": sum(1 for row in rows if row["candidate_use_allowed_now"]),
        "runtime_trading_or_live_broker_effect_rows": 0,
        "broker_operation_rows": 0,
        "paid_api_or_vendor_call_rows": 0,
        "coverage_counts": _coverage_counts(rows),
        "event_scope_coverage_counts": _event_scope_coverage_counts(rows),
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "missing_field_counts": dict(
            Counter(field for row in rows for field in row.get("missing_fields", []))
        ),
        "required_capture_field_counts": dict(
            Counter(field for row in rows for field in row.get("required_capture_fields", []))
        ),
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
    return True, f"Main Orch24 snapshot dependency repair runtime outputs are current: {len(rows)} rows"


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
                "summary": str(OUTPUT_SUMMARY),
                "runtime_rows": str(OUTPUT_ROWS),
                "decision_counts": summary["decision_counts"],
                "source_acquisition_required_rows": summary[
                    "source_acquisition_required_rows"
                ],
                "matchable_event_scope_rows": summary["matchable_event_scope_rows"],
                "blank_anchor_counts": summary["blank_anchor_counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
