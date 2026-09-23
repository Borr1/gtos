#!/usr/bin/env python3
"""Build vNext runtime rows from SCID combined source-capture status rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
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
DATE = "2026-05-18"
WAVE_ID = "WAVE_SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME"
SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_combined_source_search_and_forward_capture_route"
)
G0_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g0_scid_combined_source_capture_route_synthesis_control"
)
G12_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_scid_combined_source_search_and_forward_capture_route_audit"
)
POI_CONTRACT_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_blocked15_poi_bounds_source_capture_contract_repair"
)
SOURCE_ROWS_PATH = (
    SOURCE_DIR
    / "SCID_COMBINED_SOURCE_CAPTURE_CANDIDATE_SOURCE_CAPTURE_STATUS_2026-05-12.jsonl"
)
SOURCE_SUMMARY_PATH = (
    SOURCE_DIR
    / "SCID_COMBINED_SOURCE_CAPTURE_CANDIDATE_SOURCE_CAPTURE_STATUS_SUMMARY_2026-05-12.json"
)
FORWARD_CONTRACT_PATH = (
    SOURCE_DIR
    / "SCID_COMBINED_SOURCE_CAPTURE_FORWARD_CAPTURE_CONTRACT_2026-05-12.json"
)
POI_CONTRACT_PATH = (
    POI_CONTRACT_DIR
    / "SCID_BLOCKED15_POI_BOUNDS_SOURCE_LOGGER_CONTRACT_2026-05-13.json"
)
OUTPUT_ROWS = ROUTE_DIR / (
    f"GTOS_VNEXT_SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = ROUTE_DIR / (
    f"GTOS_VNEXT_SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME_SUMMARY_{DATE}.json"
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

SOURCE_REQUIRED_STATUSES = {
    "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN",
    "RECOVERABLE_MARKET_CONTEXT_CAPTURE_CONTRACT_FROZEN",
}

FIELD_GROUP_COMPONENTS = {
    "framework_setup_family": "scid_combined_framework_setup_source_gap",
    "future_orderflow_depth_proxy_requirements": "scid_combined_orderflow_depth_source_gap",
    "intended_entry_reference": "scid_combined_entry_reference_source_gap",
    "intended_side_direction": "scid_combined_side_direction_source_gap",
    "intended_stop_reference": "scid_combined_stop_reference_source_gap",
    "intended_target_reference": "scid_combined_target_reference_source_gap",
    "lifecycle_fill_cancel_expiry_source_status": "scid_combined_lifecycle_source_gap",
    "lower_timeframe_asof_path_availability": "scid_combined_ltf_path_source_gap",
    "poi_type_bounds_source": "scid_combined_poi_bounds_source_gap",
}


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


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload if isinstance(payload, dict) else {}


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


def _support_paths() -> list[Path]:
    paths: list[Path] = []
    for directory in (SOURCE_DIR, G0_DIR, G12_DIR, POI_CONTRACT_DIR):
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*"), key=lambda item: item.as_posix()):
            if path.is_file() and path.name != ".gitignore":
                paths.append(path)
    return paths


def _symbol_from_row(row: dict[str, Any]) -> str:
    return _norm(row.get("symbol") or row.get("source_symbol"))


def _event_time(row: dict[str, Any]) -> datetime | None:
    for key in ("decision_asof_utc", "entry_reference_time_utc"):
        raw = _norm(row.get(key))
        if not raw:
            continue
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
    candidate = _norm(row.get("candidate_input_row_id"))
    if ":2026-" in candidate:
        raw = "2026-" + candidate.split(":2026-", 1)[1]
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    return None


def _route_session(row: dict[str, Any]) -> str:
    event_time = _event_time(row)
    if event_time is None:
        return "off_core_session"
    minutes = event_time.hour * 60 + event_time.minute
    if 0 <= minutes < 3 * 60:
        return "tokyo_kz"
    if 7 * 60 <= minutes < 10 * 60 + 30:
        return "london_core"
    if 13 * 60 <= minutes < 17 * 60:
        return "ny_core"
    return "off_core_session"


def _metric(value: float, *, source_field: str) -> dict[str, Any]:
    return {
        "sum": value,
        "count": 1,
        "mean": value,
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "source_field": source_field,
        "source_shape": "combined_source_capture_status_row",
    }


def _field_status(field_payload: Any) -> str:
    if isinstance(field_payload, dict):
        return _norm(field_payload.get("status"))
    return _norm(field_payload)


def _component_for_group(field_group: str) -> str:
    return FIELD_GROUP_COMPONENTS.get(
        field_group,
        "scid_combined_generic_source_gap",
    )


def _r_evidence_for_group(field_group: str) -> str:
    if field_group == "poi_type_bounds_source":
        return "SCID_POI_BOUNDS_SOURCE_CAPTURE_REQUIRED"
    return "SCID_COMBINED_SOURCE_CAPTURE_REQUIRED"


def _source_role_for_group(field_group: str) -> str:
    if field_group == "poi_type_bounds_source":
        return "scid_poi_bounds_source_capture_guard"
    return "scid_combined_source_capture_guard"


def build_runtime_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_hash = _sha256_file(SOURCE_ROWS_PATH) if SOURCE_ROWS_PATH.exists() else ""
    output_rows: list[dict[str, Any]] = []
    for source_index, row in enumerate(source_rows, start=1):
        symbol = _symbol_from_row(row)
        route_session = _route_session(row)
        candidate_id = _norm(row.get("candidate_input_row_id"))
        duplicate_key = _norm(row.get("duplicate_proxy_denominator_key"))
        field_statuses = row.get("field_statuses") if isinstance(row.get("field_statuses"), dict) else {}
        for field_group in sorted(FIELD_GROUP_COMPONENTS):
            status_payload = field_statuses.get(field_group) or {}
            status = _field_status(status_payload)
            if status not in SOURCE_REQUIRED_STATUSES:
                continue
            component = _component_for_group(field_group)
            source_role = _source_role_for_group(field_group)
            row_number = len(output_rows) + 1
            runtime_row_id = f"SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME_{row_number:05d}"
            source_row_id = (
                _norm(row.get("combined_source_capture_row_hash"))
                or duplicate_key
                or candidate_id
                or f"scid_combined_source_capture_{source_index:05d}"
            )
            event_scope = {
                "symbol": symbol,
                "source_symbol": symbol,
                "market": symbol,
                "timeframe": "M15",
                "market_timeframe": "M15",
                "route_session": route_session,
                "horizon_id": "combined_source_capture",
                "primitive": field_group,
                "route_family": "source_discovery",
                "source_component": component,
            }
            output_rows.append(
                {
                    "schema_version": "gtos_vnext_scid_combined_source_capture_poi_bounds_runtime_row_v1",
                    "wave_id": WAVE_ID,
                    "scid_combined_source_capture_poi_bounds_runtime_row_id": runtime_row_id,
                    "source_row_id": source_row_id,
                    "source_path": _path_text(SOURCE_ROWS_PATH),
                    "source_artifact": _path_text(SOURCE_ROWS_PATH),
                    "source_artifact_hash": source_hash,
                    "source_hash": _norm(row.get("combined_source_capture_row_hash")),
                    "candidate_input_row_id": candidate_id,
                    "duplicate_proxy_denominator_key": duplicate_key,
                    "canonical_economic_group": _norm(row.get("canonical_economic_group")),
                    "source_proxy_group": _norm(row.get("source_proxy_group")),
                    "decision_asof_utc": _norm(row.get("decision_asof_utc")),
                    "entry_reference_time_utc": _norm(row.get("entry_reference_time_utc")),
                    "field_group": field_group,
                    "field_status": status,
                    "field_requirement_id": _norm(
                        status_payload.get("requirement_id")
                        if isinstance(status_payload, dict)
                        else ""
                    ),
                    "field_capture_contract_ref": _norm(
                        status_payload.get("capture_contract_ref")
                        if isinstance(status_payload, dict)
                        else ""
                    ),
                    "field_prior_packet_status": _norm(
                        status_payload.get("prior_packet_status")
                        if isinstance(status_payload, dict)
                        else ""
                    ),
                    "field_source_truth_class": _norm(
                        status_payload.get("source_truth_class")
                        if isinstance(status_payload, dict)
                        else ""
                    ),
                    "validation_safe": bool(row.get("validation_safe")),
                    "live_effect": bool(row.get("live_effect")),
                    "promotion_verdict": _norm(row.get("promotion_verdict")),
                    "opens_ai_api": bool(row.get("opens_ai_api")),
                    "opens_broker_account_order_history_deal_position_evidence": bool(
                        row.get("opens_broker_account_order_history_deal_position_evidence")
                    ),
                    "opens_paid_or_vendor_access": bool(row.get("opens_paid_or_vendor_access")),
                    "symbol": symbol,
                    "source_symbol": symbol,
                    "market": symbol,
                    "symbol_family": resolve_vnext_symbol_family(symbol),
                    "timeframe": "M15",
                    "market_timeframe": "M15",
                    "route_session": route_session,
                    "horizon_id": "combined_source_capture",
                    "primitive": field_group,
                    "route_family": "source_discovery",
                    "source_component": component,
                    "source_group": "scid_combined_source_capture_required",
                    "source_role": source_role,
                    "evidence_family": "gtos_vnext_scid_combined_source_capture_poi_bounds",
                    "system_surface": "scid_combined_source_capture_runtime",
                    "action_family": "source_capture_guard",
                    "action_class": "scid_combined_source_capture_source_acquisition_guard",
                    "r_evidence_class": _r_evidence_for_group(field_group),
                    "review_action": "MIXED_SOURCE_CAPTURE_GUARD",
                    "decision": "MIXED",
                    "candidate_use_allowed_now": False,
                    "runtime_candidate_use_permitted": False,
                    "broker_operation_permitted": False,
                    "source_complete": False,
                    "source_bound": True,
                    "source_acquisition_required": True,
                    "source_acquisition_kind": status,
                    "source_event_rows": 1,
                    "unique_scope_registry_match_rows": 1,
                    "event_scope": event_scope,
                    "r_metrics": {
                        "proxy_score": _metric(0.0, source_field="source_capture_no_promotion_guard"),
                        "effective_n": _metric(1.0, source_field="combined_source_capture_status_row"),
                    },
                    "runtime_source_key": _sha256_text(
                        "|".join((symbol, route_session, field_group, source_row_id))
                    ),
                }
            )
    return output_rows


def _dimension_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field)))
    return dict(sorted(counts.items()))


def _field_status_counts(source_rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in source_rows:
        statuses = row.get("field_statuses") if isinstance(row.get("field_statuses"), dict) else {}
        for field_group, payload in statuses.items():
            status = _field_status(payload)
            if status:
                counts[f"{field_group}|{status}"] += 1
    return dict(sorted(counts.items()))


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def summarize(source_rows: list[dict[str, Any]], runtime_rows: list[dict[str, Any]]) -> dict[str, Any]:
    forward_contract = _read_json(FORWARD_CONTRACT_PATH)
    poi_contract = _read_json(POI_CONTRACT_PATH)
    support_paths = _support_paths()
    return {
        "schema_version": "gtos_vnext_scid_combined_source_capture_poi_bounds_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "source_path": _path_text(SOURCE_ROWS_PATH),
        "source_artifacts": [
            {
                "path": _path_text(path),
                "rows": len(source_rows) if path == SOURCE_ROWS_PATH else 1,
                "sha256_or_git_blob": _sha256_file(path) if path.exists() else "",
            }
            for path in (
                SOURCE_ROWS_PATH,
                SOURCE_SUMMARY_PATH,
                FORWARD_CONTRACT_PATH,
                POI_CONTRACT_PATH,
            )
        ],
        "support_artifact_count": len(support_paths),
        "support_artifact_nonempty_line_count": sum(
            1
            for path in support_paths
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.strip()
        ),
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "source_row_count": len(source_rows),
        "runtime_row_count": len(runtime_rows),
        "runtime_source_rows_represented": len(source_rows),
        "runtime_rows_with_event_scope": sum(1 for row in runtime_rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in runtime_rows if not row.get("event_scope")),
        "source_acquisition_required_rows": sum(
            1 for row in runtime_rows if row.get("source_acquisition_required")
        ),
        "candidate_use_allowed_now_rows": sum(
            1 for row in runtime_rows if row.get("candidate_use_allowed_now")
        ),
        "broker_operation_permitted_rows": sum(
            1 for row in runtime_rows if row.get("broker_operation_permitted")
        ),
        "decision_counts": _dimension_counts(runtime_rows, "decision"),
        "field_status_counts": _field_status_counts(source_rows),
        "r_evidence_class_counts": _dimension_counts(runtime_rows, "r_evidence_class"),
        "source_component_counts": _dimension_counts(runtime_rows, "source_component"),
        "source_role_counts": _dimension_counts(runtime_rows, "source_role"),
        "source_group_counts": _dimension_counts(runtime_rows, "source_group"),
        "action_class_counts": _dimension_counts(runtime_rows, "action_class"),
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
        "forward_contract_candidate_rows_covered": forward_contract.get("candidate_rows_covered"),
        "forward_contract_field_groups_required": forward_contract.get("field_groups_required_by_prompt", []),
        "poi_contract_field_count": len(poi_contract.get("field_contracts") or []),
        "poi_contract_append_only_path": poi_contract.get("proposed_append_only_path", ""),
        "poi_contract_schema_version_required": poi_contract.get("schema_version_required", ""),
        "poi_contract_target_cards": poi_contract.get("target_card_ids") or poi_contract.get("target_cards") or [],
        "row_id_samples": [
            row.get("scid_combined_source_capture_poi_bounds_runtime_row_id")
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
