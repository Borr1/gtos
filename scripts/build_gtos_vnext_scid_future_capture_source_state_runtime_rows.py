#!/usr/bin/env python3
"""Build vNext runtime rows from SCID future-capture source-state materialization."""

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
WAVE_ID = "WAVE_SCID_FUTURE_CAPTURE_SOURCE_STATE_RUNTIME"
SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "scid_future_capture_field_source_state_materialization_for_blocked15"
)
AUDIT_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_scid_future_capture_blocked15_source_state_materialization_audit"
)
GOAL_PROMPT_PATH = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_AUDIT_GOAL_PROMPT_2026-05-12.md"
)
SOURCE_ROWS_PATH = SOURCE_DIR / "SCID_FUTURE_CAPTURE_RECOVERED_SOURCE_STATE_ROWS_2026-05-12.jsonl"
OUTPUT_ROWS = ROUTE_DIR / (
    f"GTOS_VNEXT_SCID_FUTURE_CAPTURE_SOURCE_STATE_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = ROUTE_DIR / (
    f"GTOS_VNEXT_SCID_FUTURE_CAPTURE_SOURCE_STATE_RUNTIME_SUMMARY_{DATE}.json"
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

FIELD_GROUP_COMPONENTS = {
    "baseline_control_fields": "scid_future_capture_baseline_control",
    "framework_setup_family": "scid_future_capture_framework_setup",
    "intended_entry_reference": "scid_future_capture_entry_reference",
    "intended_side_direction": "scid_future_capture_side_direction",
    "intended_stop_reference": "scid_future_capture_stop_reference",
    "intended_target_reference": "scid_future_capture_target_reference",
    "lifecycle_fill_cancel_expiry_source_status": "scid_future_capture_lifecycle_status",
}

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
    if GOAL_PROMPT_PATH.exists():
        paths.append(GOAL_PROMPT_PATH)
    for directory in (SOURCE_DIR, AUDIT_DIR):
        if not directory.exists():
            continue
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if not path.is_file() or path.name == ".gitignore":
                continue
            paths.append(path)
    return paths


def _symbol_from_row(row: dict[str, Any]) -> str:
    if symbol := _norm(row.get("symbol") or row.get("source_symbol")):
        return symbol
    candidate = _norm(row.get("candidate_input_row_id"))
    if "_2026-" in candidate:
        return candidate.split("_2026-", 1)[0]
    return candidate.split("_", 1)[0] if candidate else ""


def _event_time(row: dict[str, Any]) -> datetime | None:
    candidate = _norm(row.get("candidate_input_row_id"))
    if "_2026-" in candidate:
        raw = "2026-" + candidate.split("_2026-", 1)[1]
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    for key in ("decision_asof_utc", "source_observed_asof_utc"):
        raw = _norm(row.get(key))
        if not raw:
            continue
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
    return None


def _route_session(row: dict[str, Any]) -> str:
    raw = _norm(row.get("session_bucket") or row.get("time_of_day_bucket")).casefold()
    if raw in SESSION_ALIASES:
        return SESSION_ALIASES[raw]
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


def _component_for_group(field_group: str) -> str:
    return FIELD_GROUP_COMPONENTS.get(
        field_group,
        "scid_future_capture_source_state_materialization",
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
        "source_shape": "source_state_materialization_row",
    }


def build_runtime_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_hash = _sha256_file(SOURCE_ROWS_PATH) if SOURCE_ROWS_PATH.exists() else ""
    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=1):
        symbol = _symbol_from_row(row)
        route_session = _route_session(row)
        field_group = _norm(row.get("field_group")) or "unknown_source_state_group"
        source_component = _component_for_group(field_group)
        source_role = "scid_future_capture_source_state_guard"
        source_row_id = (
            _norm(row.get("duplicate_proxy_denominator_key"))
            or _norm(row.get("source_identifier"))
            or _norm(row.get("candidate_input_row_id"))
            or f"scid_future_capture_source_state_{index:05d}"
        )
        runtime_row_id = f"SCID_FUTURE_CAPTURE_SOURCE_STATE_RUNTIME_{index:05d}"
        event_scope = {
            "symbol": symbol,
            "source_symbol": symbol,
            "market": symbol,
            "timeframe": "M15",
            "market_timeframe": "M15",
            "route_session": route_session,
            "horizon_id": "source_state_materialization",
            "primitive": field_group,
            "route_family": "source_discovery",
            "source_component": source_component,
        }
        output_rows.append(
            {
                "schema_version": "gtos_vnext_scid_future_capture_source_state_runtime_row_v1",
                "wave_id": WAVE_ID,
                "scid_future_capture_source_state_runtime_row_id": runtime_row_id,
                "source_row_id": source_row_id,
                "source_path": _path_text(SOURCE_ROWS_PATH),
                "source_artifact": _path_text(SOURCE_ROWS_PATH),
                "source_artifact_hash": source_hash,
                "source_hash": _norm(row.get("source_hash")),
                "source_hash_policy": _norm(row.get("source_hash_policy")),
                "source_identifier": _norm(row.get("source_identifier")),
                "candidate_input_row_id": _norm(row.get("candidate_input_row_id")),
                "decision_asof_utc": _norm(row.get("decision_asof_utc")),
                "source_observed_asof_utc": _norm(row.get("source_observed_asof_utc")),
                "field_group": field_group,
                "field_status": _norm(row.get("field_status")),
                "captured_source_safe": _norm(row.get("field_status")) == "CAPTURED_SOURCE_SAFE",
                "validation_safe": bool(row.get("validation_safe")),
                "live_effect": bool(row.get("live_effect")),
                "promotion_verdict": _norm(row.get("promotion_verdict")),
                "downstream_g12_acceptance_rule": _norm(
                    row.get("downstream_g12_acceptance_rule")
                ),
                "symbol": symbol,
                "source_symbol": symbol,
                "market": symbol,
                "symbol_family": resolve_vnext_symbol_family(symbol),
                "timeframe": "M15",
                "market_timeframe": "M15",
                "route_session": route_session,
                "horizon_id": "source_state_materialization",
                "primitive": field_group,
                "route_family": "source_discovery",
                "source_component": source_component,
                "source_group": "scid_future_capture_source_state_materialization",
                "source_role": source_role,
                "source_name": "gtos_vnext_scid_future_capture_source_state_wave",
                "evidence_family": "gtos_vnext_scid_future_capture_source_state",
                "system_surface": "scid_future_capture_source_state_materialization_runtime",
                "action_family": "source_state_materialization_guard",
                "action_class": "scid_future_capture_source_state_materialization_guard",
                "r_evidence_class": "SCID_FUTURE_CAPTURE_SOURCE_STATE_MATERIALIZATION_REQUIRED",
                "review_action": "MIXED_SOURCE_STATE_GUARD",
                "decision": "MIXED",
                "candidate_use_allowed_now": False,
                "runtime_candidate_use_permitted": False,
                "source_complete": False,
                "source_bound": True,
                "source_acquisition_required": True,
                "source_acquisition_kind": "scid_future_capture_source_state_no_promotion",
                "accepted_40_denominator_unblocked": False,
                "source_event_rows": 1,
                "unique_scope_registry_match_rows": 1,
                "event_scope": event_scope,
                "r_metrics": {
                    "proxy_score": _metric(0.0, source_field="source_state_no_promotion_guard"),
                    "effective_n": _metric(1.0, source_field="source_state_materialized_row_count"),
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


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def _source_artifact_stats(
    source_rows: list[dict[str, Any]],
    runtime_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stats: list[dict[str, Any]] = []
    for path in _support_paths():
        role = "runtime_source_rows" if path == SOURCE_ROWS_PATH else "supporting_evidence"
        stats.append(
            {
                "path": _path_text(path),
                "rows": len(source_rows) if path == SOURCE_ROWS_PATH else _count_nonempty_lines(path),
                "runtime_rows_read": len(runtime_rows) if path == SOURCE_ROWS_PATH else 0,
                "sha256_or_git_blob": _sha256_file(path),
                "source_role": role,
            }
        )
    return stats


def summarize(source_rows: list[dict[str, Any]], runtime_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "gtos_vnext_scid_future_capture_source_state_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "source_path": _path_text(SOURCE_ROWS_PATH),
        "source_artifacts": _source_artifact_stats(source_rows, runtime_rows),
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "source_row_count": len(source_rows),
        "runtime_row_count": len(runtime_rows),
        "runtime_source_rows_represented": len(runtime_rows),
        "support_rows_represented": sum(
            item["rows"]
            for item in _source_artifact_stats(source_rows, runtime_rows)
            if item["source_role"] == "supporting_evidence"
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
        "field_group_counts": _dimension_counts(runtime_rows, "field_group"),
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
        "row_id_samples": [
            row.get("scid_future_capture_source_state_runtime_row_id")
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
