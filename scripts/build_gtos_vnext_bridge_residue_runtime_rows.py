#!/usr/bin/env python3
"""Build diagnostic runtime rows for the gtos_vnext bridge residue wave."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

DATE = "2026-05-18"
WAVE_ID = "WAVE_GTOS_VNEXT_BRIDGE_RESIDUE_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_bridge_residue_runtime"
SOURCE_NAME = "gtos_vnext_bridge_residue_runtime_wave"

ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
OUTPUT_ROWS = ROUTE_DIR / f"GTOS_VNEXT_BRIDGE_RESIDUE_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"GTOS_VNEXT_BRIDGE_RESIDUE_RUNTIME_SUMMARY_{DATE}.json"

SOURCE_UNITS: tuple[tuple[str, str, int | None, str], ...] = (
    ("UNIT_009059", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/build_gtos_vnext_evidence_system_matrix_2026_05_18.py", None, "bridge_support_artifact"),
    ("UNIT_009060", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/build_gtos_vnext_scorer_filter_router_event_validation_2026_05_18.py", None, "bridge_support_artifact"),
    ("UNIT_009061", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/build_gtos_vnext_scorer_filter_router_registry_2026_05_18.py", None, "bridge_support_artifact"),
    ("UNIT_009079", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_BUILD_MATRIX_SUMMARY_2026-05-18.json", 1, "bridge_support_artifact"),
    ("UNIT_009080", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_BUILD_MATRIX_VERIFY_RESULT_2026-05-18.json", 1, "bridge_support_artifact"),
    ("UNIT_009081", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_CHECKPOINT_COMPLETION_AUDIT_2026-05-18.json", 1, "bridge_support_artifact"),
    ("UNIT_009100", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_INSTRUCTION_COVERAGE_LEDGER_2026-05-18.jsonl", 7, "bridge_support_artifact"),
    ("UNIT_009103", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_LEGACY_RESEARCH_MERGER_LEDGER_2026-05-18.jsonl", 3, "bridge_support_artifact"),
    ("UNIT_009119", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_OUTPUT_MANIFEST_2026-05-18.json", 1, "bridge_support_artifact"),
    ("UNIT_009143", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_SCORER_FILTER_ROUTER_EVENT_VALIDATION_MANIFEST_2026-05-18.json", 1, "bridge_support_artifact"),
    ("UNIT_009144", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_SCORER_FILTER_ROUTER_EVENT_VALIDATION_SCOPE_ROLLUP_LEDGER_2026-05-18.jsonl", 109, "bridge_event_scope_rollup"),
    ("UNIT_009145", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_SCORER_FILTER_ROUTER_EVENT_VALIDATION_SOURCE_SUMMARY_LEDGER_2026-05-18.jsonl", 7, "bridge_event_source_summary"),
    ("UNIT_009146", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_SCORER_FILTER_ROUTER_EVENT_VALIDATION_SUMMARY_2026-05-18.json", 1, "bridge_support_artifact"),
    ("UNIT_009147", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_SCORER_FILTER_ROUTER_EVENT_VALIDATION_VERIFY_RESULT_2026-05-18.json", 1, "bridge_support_artifact"),
    ("UNIT_009148", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_SCORER_FILTER_ROUTER_REGISTRY_CATALOG_LEDGER_2026-05-18.jsonl", None, "bridge_registry_catalog"),
    ("UNIT_009149", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_SCORER_FILTER_ROUTER_REGISTRY_MANIFEST_2026-05-18.json", 1, "bridge_support_artifact"),
    ("UNIT_009150", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_SCORER_FILTER_ROUTER_REGISTRY_SELF_CHECK_LEDGER_2026-05-18.jsonl", None, "bridge_registry_self_check"),
    ("UNIT_009151", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_SCORER_FILTER_ROUTER_REGISTRY_SUMMARY_2026-05-18.json", 1, "bridge_support_artifact"),
    ("UNIT_009152", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/GTOS_VNEXT_SCORER_FILTER_ROUTER_REGISTRY_VERIFY_RESULT_2026-05-18.json", 1, "bridge_support_artifact"),
    ("UNIT_009183", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/verify_gtos_vnext_evidence_system_matrix_2026_05_18.py", None, "bridge_support_artifact"),
    ("UNIT_009184", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/verify_gtos_vnext_scorer_filter_router_event_validation_2026_05_18.py", None, "bridge_support_artifact"),
    ("UNIT_009185", "research/science_program_2026_05/06_outcome_testing/gtos_vnext_research_to_runtime_builder/verify_gtos_vnext_scorer_filter_router_registry_2026_05_18.py", None, "bridge_support_artifact"),
)

MATERIAL_COMPONENTS = {
    "bridge_event_scope_rollup",
    "bridge_event_source_summary",
    "bridge_registry_catalog",
    "bridge_registry_self_check",
}

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "side",
    "framework",
    "route_family",
    "source_component",
    "action_class",
    "entry_variant",
    "target_stop_order_class",
)


def _repo_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else REPO_ROOT / path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().casefold() in {"1", "true", "yes", "y", "on"}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                rows.append(parsed)
    return rows


def _safe_row_count(path: Path) -> int:
    suffix = path.suffix.casefold()
    if suffix == ".jsonl":
        try:
            return len(_read_jsonl(path))
        except json.JSONDecodeError:
            return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())
    if suffix == ".json":
        parsed = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(parsed, list):
            return len(parsed)
        if isinstance(parsed, dict) and isinstance(parsed.get("rows"), list):
            return len(parsed["rows"])
        return 1
    if suffix in {".py", ".md", ".txt", ".yaml", ".yml"}:
        return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())
    return 1


def _event_scope(source_component: str, row: dict[str, Any]) -> dict[str, str]:
    raw_scope: Any = {}
    if source_component == "bridge_event_scope_rollup":
        raw_scope = row.get("event_scope")
    elif source_component == "bridge_registry_catalog":
        raw_scope = row.get("required_event_scope")
    if not isinstance(raw_scope, dict):
        raw_scope = {}
    scope = {
        field: _norm(raw_scope.get(field))
        for field in ANCHOR_FIELDS
        if _norm(raw_scope.get(field))
    }
    if source_component == "bridge_registry_catalog" and not _truthy(row.get("callable_event_match_enabled")):
        return {}
    return scope


def _source_row_id(source_component: str, row: dict[str, Any], row_number: int) -> str:
    for field in (
        "event_scope_rollup_row_id",
        "source_summary_row_id",
        "registry_catalog_row_id",
        "registry_self_check_row_id",
        "row_id",
        "row_key",
    ):
        if value := _norm(row.get(field)):
            return value
    return f"{source_component}:{row_number}"


def _base_runtime_row(
    *,
    unit_id: str,
    path_text: str,
    source_hash: str,
    source_component: str,
    row_number: int,
    row_count: int,
) -> dict[str, Any]:
    return {
        "schema_version": "gtos_vnext_bridge_residue_runtime_row_v1",
        "row_type": "gtos_vnext_bridge_residue_runtime_diagnostic",
        "wave_id": WAVE_ID,
        "source_unit_id": unit_id,
        "source_artifact": path_text,
        "source_path": path_text,
        "source_file_sha256": source_hash,
        "source_row_number": row_number,
        "source_rows_represented": row_count,
        "source_component": source_component,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "system_surface": "vnext_runtime_bridge",
        "decision": "MIXED",
        "action_class": "bridge_diagnostic_non_scoring",
        "source_group": "vnext_bridge_residue_diagnostic",
        "source_role": "bridge_registry_event_validation_health",
        "r_evidence_class": "BRIDGE_DIAGNOSTIC_ONLY",
        "bridge_diagnostic_only": True,
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "runtime_effect_now": False,
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
    }


def _convert_material_source(
    *,
    unit_id: str,
    path_text: str,
    source_hash: str,
    source_component: str,
) -> list[dict[str, Any]]:
    path = _repo_path(path_text)
    rows = _read_jsonl(path)
    converted: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, 1):
        event_scope = _event_scope(source_component, row)
        runtime_row = _base_runtime_row(
            unit_id=unit_id,
            path_text=path_text,
            source_hash=source_hash,
            source_component=source_component,
            row_number=row_number,
            row_count=1,
        )
        runtime_row.update(
            {
                "source_row_id": _source_row_id(source_component, row, row_number),
                "event_scope": event_scope,
                "bridge_source_kind": source_component,
                "bridge_original_source_name": row.get("source_name"),
                "bridge_original_evidence_family": row.get("evidence_family"),
                "bridge_original_system_surface": row.get("system_surface"),
                "bridge_original_implementation_action": row.get("implementation_action"),
                "callable_event_match_enabled": row.get("callable_event_match_enabled"),
                "self_check_status": row.get("self_check_status"),
                "matched_event_rows": int(row.get("matched_event_rows") or 0),
                "unmatched_event_rows": int(row.get("unmatched_event_rows") or 0),
                "registry_match_rows": int(row.get("registry_match_rows") or 0),
                "source_rows": int(row.get("source_rows") or 0),
                "parse_error_rows": int(row.get("parse_error_rows") or 0),
                "event_scope_field_count": int(row.get("event_scope_field_count") or len(event_scope) or 0),
            }
        )
        for field, value in event_scope.items():
            if field in {"source_component", "action_class"}:
                continue
            runtime_row[field] = value
        converted.append(runtime_row)
    return converted


def _support_source_row(
    *,
    unit_id: str,
    path_text: str,
    source_hash: str,
    source_component: str,
    row_count: int,
) -> dict[str, Any]:
    runtime_row = _base_runtime_row(
        unit_id=unit_id,
        path_text=path_text,
        source_hash=source_hash,
        source_component=source_component,
        row_number=1,
        row_count=row_count,
    )
    runtime_row.update(
        {
            "source_row_id": f"{source_component}:{unit_id}",
            "event_scope": {},
            "bridge_source_kind": source_component,
            "support_artifact_runtime_role": "path_hash_count_reference_for_bridge_wave",
        }
    )
    return runtime_row


def build_runtime_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    runtime_rows: list[dict[str, Any]] = []
    source_artifacts: list[dict[str, Any]] = []
    selected_rows_counted = 0
    unknown_units = 0

    for unit_id, path_text, ledger_count, source_component in SOURCE_UNITS:
        path = _repo_path(path_text)
        source_hash = _sha256(path)
        actual_count = _safe_row_count(path)
        row_count = ledger_count if ledger_count is not None else actual_count
        if ledger_count is None:
            unknown_units += 1
        selected_rows_counted += int(row_count or 0)
        source_artifacts.append(
            {
                "unit_id": unit_id,
                "path": path_text,
                "hash": source_hash,
                "hash_algorithm": "sha256",
                "row_count": row_count,
                "actual_source_row_count": actual_count,
                "source_component": source_component,
                "material_row_bearing": source_component in MATERIAL_COMPONENTS,
            }
        )
        if source_component in MATERIAL_COMPONENTS:
            runtime_rows.extend(
                _convert_material_source(
                    unit_id=unit_id,
                    path_text=path_text,
                    source_hash=source_hash,
                    source_component=source_component,
                )
            )
        else:
            runtime_rows.append(
                _support_source_row(
                    unit_id=unit_id,
                    path_text=path_text,
                    source_hash=source_hash,
                    source_component=source_component,
                    row_count=int(row_count or 0),
                )
            )

    source_component_counts = Counter(row.get("source_component", "") for row in runtime_rows)
    evidence_family_counts = Counter(row.get("bridge_original_evidence_family", "") for row in runtime_rows if row.get("bridge_original_evidence_family"))
    system_surface_counts = Counter(row.get("bridge_original_system_surface", "") for row in runtime_rows if row.get("bridge_original_system_surface"))
    implementation_action_counts = Counter(row.get("bridge_original_implementation_action", "") for row in runtime_rows if row.get("bridge_original_implementation_action"))
    self_check_status_counts = Counter(row.get("self_check_status", "") for row in runtime_rows if row.get("self_check_status"))
    symbol_counts = Counter(row.get("symbol", "") for row in runtime_rows if row.get("symbol"))
    source_symbol_counts = Counter(row.get("source_symbol", "") for row in runtime_rows if row.get("source_symbol"))
    session_counts = Counter(row.get("route_session", "") for row in runtime_rows if row.get("route_session"))
    side_counts = Counter(row.get("side", "") for row in runtime_rows if row.get("side"))

    event_source_rows = sum(int(row.get("source_rows") or 0) for row in runtime_rows if row.get("source_component") == "bridge_event_source_summary")
    event_matched_rows = sum(int(row.get("matched_event_rows") or 0) for row in runtime_rows if row.get("source_component") == "bridge_event_scope_rollup")
    event_unmatched_rows = sum(int(row.get("unmatched_event_rows") or 0) for row in runtime_rows if row.get("source_component") == "bridge_event_scope_rollup")
    event_registry_match_rows = sum(int(row.get("registry_match_rows") or 0) for row in runtime_rows if row.get("source_component") == "bridge_event_scope_rollup")
    event_parse_errors = sum(int(row.get("parse_error_rows") or 0) for row in runtime_rows if row.get("source_component") == "bridge_event_source_summary")
    blank_anchor_counts = {
        field: sum(1 for row in runtime_rows if not row.get(field))
        for field in ANCHOR_FIELDS
    }

    summary = {
        "schema_version": "gtos_vnext_bridge_residue_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "source_artifacts": source_artifacts,
        "selected_open_unit_count": len(SOURCE_UNITS),
        "row_count_unknown_unit_count": unknown_units,
        "wave_source_rows_counted": selected_rows_counted,
        "runtime_row_count": len(runtime_rows),
        "material_runtime_row_count": sum(1 for row in runtime_rows if row.get("source_component") in MATERIAL_COMPONENTS),
        "support_runtime_row_count": sum(1 for row in runtime_rows if row.get("source_component") == "bridge_support_artifact"),
        "source_component_counts": dict(sorted(source_component_counts.items())),
        "bridge_original_evidence_family_counts": dict(evidence_family_counts.most_common()),
        "bridge_original_system_surface_counts": dict(system_surface_counts.most_common()),
        "bridge_original_implementation_action_counts": dict(implementation_action_counts.most_common()),
        "self_check_status_counts": dict(self_check_status_counts),
        "callable_event_match_enabled_rows": sum(1 for row in runtime_rows if _truthy(row.get("callable_event_match_enabled"))),
        "catalog_only_no_event_scope_rows": self_check_status_counts.get("CATALOG_ONLY_NO_EVENT_SCOPE", 0),
        "self_check_pass_rows": self_check_status_counts.get("PASS_SELF_MATCH_FOUND", 0),
        "event_validation_source_rows": event_source_rows,
        "event_validation_matched_event_rows": event_matched_rows,
        "event_validation_unmatched_event_rows": event_unmatched_rows,
        "event_validation_registry_match_rows": event_registry_match_rows,
        "event_validation_parse_error_rows": event_parse_errors,
        "runtime_score_allowed_rows": sum(1 for row in runtime_rows if _truthy(row.get("runtime_score_allowed"))),
        "runtime_candidate_use_permitted_rows": sum(1 for row in runtime_rows if _truthy(row.get("runtime_candidate_use_permitted"))),
        "candidate_use_allowed_now_rows": sum(1 for row in runtime_rows if _truthy(row.get("candidate_use_allowed_now"))),
        "live_effect_rows": sum(1 for row in runtime_rows if _truthy(row.get("live_effect"))),
        "broker_operation_rows": sum(1 for row in runtime_rows if _truthy(row.get("broker_operation"))),
        "paid_api_or_vendor_call_rows": sum(1 for row in runtime_rows if _truthy(row.get("paid_api_or_vendor_call"))),
        "runtime_trading_or_live_broker_effect_rows": sum(1 for row in runtime_rows if _truthy(row.get("runtime_trading_or_live_broker_effect"))),
        "symbol_counts": dict(sorted(symbol_counts.items())),
        "source_symbol_counts": dict(sorted(source_symbol_counts.items())),
        "route_session_counts": dict(sorted(session_counts.items())),
        "side_counts": dict(sorted(side_counts.items())),
        "timeframe_counts": {},
        "market_counts": {},
        "entry_variant_counts": {},
        "exit_variant_counts": {},
        "blank_anchor_counts": blank_anchor_counts,
    }
    return runtime_rows, summary


def _render_outputs() -> tuple[str, str]:
    rows, summary = build_runtime_rows()
    row_text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    summary_text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    return row_text, summary_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated outputs differ")
    args = parser.parse_args()
    row_text, summary_text = _render_outputs()
    if args.check:
        mismatches = []
        if not OUTPUT_ROWS.exists() or OUTPUT_ROWS.read_text(encoding="utf-8") != row_text:
            mismatches.append(str(OUTPUT_ROWS))
        if not OUTPUT_SUMMARY.exists() or OUTPUT_SUMMARY.read_text(encoding="utf-8") != summary_text:
            mismatches.append(str(OUTPUT_SUMMARY))
        if mismatches:
            print("Bridge residue runtime outputs are stale:", ", ".join(mismatches), file=sys.stderr)
            return 1
        print("Bridge residue runtime outputs are current")
        return 0
    OUTPUT_ROWS.write_text(row_text, encoding="utf-8")
    OUTPUT_SUMMARY.write_text(summary_text, encoding="utf-8")
    print(f"Wrote {OUTPUT_ROWS}")
    print(f"Wrote {OUTPUT_SUMMARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
