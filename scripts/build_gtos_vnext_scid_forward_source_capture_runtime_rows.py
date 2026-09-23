#!/usr/bin/env python3
"""Build vNext runtime rows from SCID forward source-capture shadows."""

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
WAVE_ID = "WAVE_SCID_FORWARD_SOURCE_CAPTURE_RUNTIME"
SOURCE_PATH = REPO_ROOT / "shadow_logs" / "scid_forward_source_capture.jsonl"
OUTPUT_ROWS = ROUTE_DIR / (
    f"GTOS_VNEXT_SCID_FORWARD_SOURCE_CAPTURE_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = ROUTE_DIR / (
    f"GTOS_VNEXT_SCID_FORWARD_SOURCE_CAPTURE_RUNTIME_SUMMARY_{DATE}.json"
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


def _symbol_from_candidate_id(row: dict[str, Any]) -> str:
    for key in ("candidate_input_row_id", "pending_intent_id", "candidate_id"):
        raw = _norm(row.get(key))
        if "_2026-" in raw:
            return raw.split("_2026-", 1)[0]
        if raw:
            return raw.split("_", 1)[0]
    return _norm(row.get("symbol") or row.get("source_symbol"))


def _event_time(row: dict[str, Any]) -> datetime | None:
    candidate = _norm(row.get("candidate_input_row_id") or row.get("pending_intent_id"))
    if "_2026-" in candidate:
        raw = "2026-" + candidate.split("_2026-", 1)[1]
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    for key in ("decision_asof_utc", "source_event_utc", "source_observed_asof_utc"):
        raw = _norm(row.get(key))
        if not raw:
            continue
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            continue
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
        "source_shape": "source_capture_row",
    }


def build_runtime_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_hash = _sha256_file(SOURCE_PATH) if SOURCE_PATH.exists() else ""
    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=1):
        symbol = _symbol_from_candidate_id(row)
        route_session = _route_session(row)
        primitive = _norm(row.get("field_group")) or "lifecycle_fill_cancel_expiry_source_status"
        source_row_id = (
            _norm(row.get("source_identifier"))
            or _norm(row.get("pending_intent_id"))
            or _norm(row.get("candidate_input_row_id"))
            or f"scid_forward_source_capture_{index:04d}"
        )
        runtime_row_id = f"SCID_FORWARD_SOURCE_CAPTURE_RUNTIME_{index:04d}"
        source_component = "scid_forward_source_capture_lifecycle"
        source_role = "scid_forward_source_capture_lifecycle_guard"
        event_scope = {
            "symbol": symbol,
            "source_symbol": symbol,
            "market": symbol,
            "timeframe": "M15",
            "market_timeframe": "M15",
            "route_session": route_session,
            "horizon_id": "source_capture_lifecycle",
            "primitive": primitive,
            "route_family": "pending_lifecycle",
            "source_component": source_component,
        }
        output_rows.append(
            {
                "schema_version": "gtos_vnext_scid_forward_source_capture_runtime_row_v1",
                "wave_id": WAVE_ID,
                "scid_forward_source_capture_runtime_row_id": runtime_row_id,
                "source_row_id": source_row_id,
                "source_path": _path_text(SOURCE_PATH),
                "source_artifact": _path_text(SOURCE_PATH),
                "source_artifact_hash": source_hash,
                "source_hash": _norm(row.get("source_hash")),
                "source_identifier": _norm(row.get("source_identifier")),
                "candidate_input_row_id": _norm(row.get("candidate_input_row_id")),
                "pending_intent_id": _norm(row.get("pending_intent_id")),
                "source_event_utc": _norm(row.get("source_event_utc")),
                "source_observed_asof_utc": _norm(row.get("source_observed_asof_utc")),
                "source_event_type": _norm(
                    row.get("source_event_type_created_updated_expired_cancelled_replaced_no_order")
                ),
                "intent_state_after": _norm(row.get("intent_state_after")),
                "field_group": primitive,
                "field_status": _norm(row.get("field_status")),
                "validation_safe": bool(row.get("validation_safe")),
                "live_effect": bool(row.get("live_effect")),
                "promotion_verdict": _norm(row.get("promotion_verdict")),
                "symbol": symbol,
                "source_symbol": symbol,
                "market": symbol,
                "symbol_family": resolve_vnext_symbol_family(symbol),
                "timeframe": "M15",
                "market_timeframe": "M15",
                "route_session": route_session,
                "horizon_id": "source_capture_lifecycle",
                "primitive": primitive,
                "route_family": "pending_lifecycle",
                "source_component": source_component,
                "source_group": "source_materialized_lifecycle_guard",
                "source_role": source_role,
                "evidence_family": "gtos_vnext_scid_forward_source_capture",
                "system_surface": "scid_forward_source_capture_runtime",
                "action_family": "source_capture_guard",
                "action_class": "scid_forward_source_capture_source_acquisition_guard",
                "r_evidence_class": "SCID_FORWARD_CAPTURE_SOURCE_ACQUISITION_REQUIRED",
                "review_action": "MIXED_SOURCE_CAPTURE_GUARD",
                "decision": "MIXED",
                "candidate_use_allowed_now": False,
                "runtime_candidate_use_permitted": False,
                "source_complete": False,
                "source_bound": True,
                "source_acquisition_required": True,
                "source_acquisition_kind": "scid_forward_lifecycle_capture_no_promotion",
                "source_event_rows": 1,
                "unique_scope_registry_match_rows": 1,
                "event_scope": event_scope,
                "r_metrics": {
                    "proxy_score": _metric(0.0, source_field="source_capture_no_promotion_guard"),
                    "effective_n": _metric(1.0, source_field="source_capture_row_count"),
                },
                "runtime_source_key": _sha256_text(
                    "|".join((symbol, route_session, primitive, source_row_id))
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


def summarize(source_rows: list[dict[str, Any]], runtime_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "gtos_vnext_scid_forward_source_capture_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "source_path": _path_text(SOURCE_PATH),
        "source_artifacts": [
            {
                "path": _path_text(SOURCE_PATH),
                "rows": len(source_rows),
                "runtime_rows_read": len(runtime_rows),
                "sha256_or_git_blob": _sha256_file(SOURCE_PATH) if SOURCE_PATH.exists() else "",
            }
        ],
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "source_row_count": len(source_rows),
        "runtime_row_count": len(runtime_rows),
        "runtime_source_rows_represented": len(runtime_rows),
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
        "source_artifact_hash": _sha256_file(SOURCE_PATH) if SOURCE_PATH.exists() else "",
        "row_id_samples": [
            row.get("scid_forward_source_capture_runtime_row_id")
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

    source_rows = _read_jsonl(SOURCE_PATH)
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
