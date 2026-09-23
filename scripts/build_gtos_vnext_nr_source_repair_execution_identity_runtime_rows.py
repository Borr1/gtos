#!/usr/bin/env python3
"""Build numeric-router source-repair execution identity runtime rows."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
OUTPUT_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)

DATE = "2026-05-18"
WAVE_ID = "WAVE_MAIN_ORCH48_NR_SOURCE_REPAIR_EXECUTION_IDENTITY_RUNTIME"
OUTPUT_ROWS_PATH = (
    OUTPUT_DIR / f"GTOS_VNEXT_NR_SOURCE_REPAIR_EXECUTION_IDENTITY_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY_PATH = (
    OUTPUT_DIR / f"GTOS_VNEXT_NR_SOURCE_REPAIR_EXECUTION_IDENTITY_RUNTIME_SUMMARY_{DATE}.json"
)

SOURCE_PATHS = (
    SOURCE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_CLOSE_SOURCE_CAPTURE_PATCH_LEDGER_{DATE}.jsonl",
    SOURCE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_CAPTURE_CONTRACT_LEDGER_{DATE}.jsonl",
    SOURCE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_SLIP_JOIN_CHECK_LEDGER_{DATE}.jsonl",
    SOURCE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_FUTURE_SLIP_LIFECYCLE_EMITTER_LEDGER_{DATE}.jsonl",
    SOURCE_DIR / f"MAIN_ORCH48_NR_SRC_REPAIR_SLIP_LIFECYCLE_JOIN_AUDIT_LEDGER_{DATE}.jsonl",
)
SUPPORT_PATHS = tuple(
    path
    for prefix in (
        "MAIN_ORCH48_NR_SRC_REPAIR_CLOSE_SOURCE_CAPTURE_PATCH",
        "MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_CAPTURE_CONTRACT",
        "MAIN_ORCH48_NR_SRC_REPAIR_EXEC_ID_SLIP_JOIN_CHECK",
        "MAIN_ORCH48_NR_SRC_REPAIR_FUTURE_SLIP_LIFECYCLE_EMITTER",
        "MAIN_ORCH48_NR_SRC_REPAIR_SLIP_LIFECYCLE_JOIN_AUDIT",
    )
    for path in (
        SOURCE_DIR / f"{prefix}_LEDGER_{DATE}.jsonl",
        SOURCE_DIR / f"{prefix}_MANIFEST_{DATE}.json",
        SOURCE_DIR / f"{prefix}_SUMMARY_{DATE}.json",
        SOURCE_DIR / f"{prefix}_VERIFY_RESULT_{DATE}.json",
    )
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return sum(1 for _ in fh)


def _repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _normalized(value: Any) -> str:
    if value in (None, "None"):
        return ""
    return str(value).strip()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _metric(value: float | int | None, *, source_field: str) -> dict[str, Any]:
    if isinstance(value, (int, float)):
        return {
            "count": 1,
            "max": float(value),
            "mean": float(value),
            "min": float(value),
            "negative_rows": 1 if value < 0 else 0,
            "positive_rows": 1 if value > 0 else 0,
            "source_field": source_field,
            "source_shape": "nr_source_repair_execution_identity",
            "sum": float(value),
            "zero_rows": 1 if value == 0 else 0,
        }
    return {
        "count": 0,
        "max": None,
        "mean": None,
        "min": None,
        "negative_rows": 0,
        "positive_rows": 0,
        "source_field": source_field,
        "source_shape": "missing",
        "sum": None,
        "zero_rows": 0,
    }


def _row_symbol(row: dict[str, Any]) -> str:
    payload = row.get("source_packet_context_payload")
    if not isinstance(payload, dict):
        payload = {}
    for field in ("symbol", "slippage_row_symbol"):
        value = _normalized(row.get(field) or payload.get(field))
        if value:
            return value
    return ""


def _row_session(row: dict[str, Any], symbol: str) -> str:
    payload = row.get("source_packet_context_payload")
    if not isinstance(payload, dict):
        payload = {}
    session = _normalized(row.get("route_session") or payload.get("route_session"))
    if session:
        return session
    return "ALL_SESSIONS" if symbol else ""


def _source_row_id(row: dict[str, Any], path: Path, line_no: int) -> str:
    for key in (
        "close_source_capture_patch_row_id",
        "execution_identity_capture_contract_row_id",
        "execution_identity_capture_event_row_id",
        "future_slippage_lifecycle_emitter_event_row_id",
        "slippage_lifecycle_join_event_row_id",
        "input_source_repair_plan_row_id",
    ):
        value = _normalized(row.get(key))
        if value:
            return value
    return f"{path.name}:{line_no}"


def _status(row: dict[str, Any]) -> str:
    for key in (
        "close_source_capture_patch_status",
        "execution_identity_capture_contract_status",
        "execution_identity_capture_event_status",
        "future_slippage_lifecycle_emitter_status",
        "slippage_lifecycle_join_status",
        "source_repair_selector_route_status",
    ):
        value = _normalized(row.get(key))
        if value:
            return value
    return ""


def _source_role(path: Path, row: dict[str, Any]) -> str:
    name = path.name
    if "CAPTURE_CONTRACT" in name or "CAPTURE_PATCH" in name:
        return "source_repair_execution_plan"
    if row.get("missing_execution_geometry_fields") or row.get("missing_source_repair_identity_fields"):
        return "exact_r_source_repair_proof"
    return "source_repair_selector_surface"


def _runtime_rows() -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    source_shas = {path: _sha256(path) for path in SOURCE_PATHS}
    for path in SOURCE_PATHS:
        source_rows = _read_jsonl(path)
        for line_no, row in enumerate(source_rows, start=1):
            source_row_id = _source_row_id(row, path, line_no)
            row_hash = _hash_text(f"{path.name}|{line_no}|{source_row_id}")[:24]
            row_id = f"nr_source_repair_execution_identity:{row_hash}"
            symbol = _row_symbol(row)
            route_session = _row_session(row, symbol)
            source_component = _normalized(row.get("source_component")) or "source_repair_proof"
            missing_execution = row.get("missing_execution_geometry_fields")
            missing_identity = row.get("missing_source_repair_identity_fields")
            if not isinstance(missing_execution, list):
                missing_execution = []
            if not isinstance(missing_identity, list):
                missing_identity = []
            captured_order_identity = row.get("captured_order_identity_fields")
            if not isinstance(captured_order_identity, list):
                captured_order_identity = []
            captured_count = row.get("captured_execution_geometry_field_count")
            input_action_rows = row.get("input_action_rows")
            output_rows.append(
                {
                    "nr_source_repair_execution_identity_runtime_row_id": row_id,
                    "row_key": row_id,
                    "source_row_id": source_row_id,
                    "schema_version": "gtos_vnext_nr_source_repair_execution_identity_runtime_v1",
                    "evidence_family": "gtos_vnext_nr_source_repair_execution_identity",
                    "source_name": "gtos_vnext_nr_source_repair_execution_identity_wave",
                    "source_group": "source_repair_proof",
                    "source_role": _source_role(path, row),
                    "system_surface": "source_repair_queue_catalog",
                    "source_component": source_component,
                    "source_path": _repo_path(path),
                    "source_artifact": _repo_path(path),
                    "source_artifact_sha256": source_shas[path],
                    "source_line_no": line_no,
                    "source_symbol": symbol,
                    "symbol": symbol,
                    "market": symbol,
                    "route_session": route_session,
                    "session": route_session,
                    "side": "",
                    "timeframe": "",
                    "market_timeframe": "",
                    "horizon_id": _normalized(row.get("horizon_id")),
                    "primitive": "",
                    "entry_variant": "",
                    "route_family": "numeric_router",
                    "target_stop_order_class": "",
                    "decision": "MIXED",
                    "review_action": "MIXED",
                    "action_class": "nr_source_repair_execution_identity_guard",
                    "runtime_effect_now": "nr_source_repair_execution_identity_guard",
                    "runtime_score_allowed": False,
                    "runtime_candidate_use_permitted": False,
                    "candidate_use_allowed_now": False,
                    "live_effect": False,
                    "validation_safe": False,
                    "r_evidence_class": "SOURCE_REPAIR_FOR_EXACT_R",
                    "source_repair_required": True,
                    "source_acquisition_required": False,
                    "status": _status(row),
                    "repair_action": row.get("repair_action") or row.get("numeric_router_action") or "",
                    "materialization_result_scope": row.get("materialization_result_scope") or "",
                    "exact_r_repaired": bool(
                        row.get("exact_r_repaired_by_this_event")
                        or row.get("exact_r_repaired_by_this_contract")
                        or row.get("exact_r_repaired_by_this_emitter")
                        or row.get("exact_r_repaired_by_this_lifecycle_join")
                    ),
                    "slippage_join_repaired": bool(
                        row.get("slippage_join_repaired_by_this_event")
                        or row.get("slippage_join_repaired_by_this_contract")
                        or row.get("slippage_join_repaired_by_this_emitter")
                        or row.get("slippage_lifecycle_join_repaired_by_this_event")
                    ),
                    "captured_execution_geometry_field_count": captured_count,
                    "captured_order_identity_fields": captured_order_identity,
                    "missing_execution_geometry_fields": missing_execution,
                    "missing_source_repair_identity_fields": missing_identity,
                    "source_repair_identity_key": row.get("source_repair_identity_key") or "",
                    "expected_source_repair_identity_key": row.get("expected_source_repair_identity_key") or "",
                    "input_action_rows": input_action_rows,
                    "source_rows_represented": 1,
                    "source_event_rows": 1,
                    "r_metrics": {
                        "effective_n": _metric(1, source_field="source_event_row"),
                        "input_action_rows": _metric(input_action_rows, source_field="input_action_rows"),
                        "captured_execution_geometry_field_count": _metric(
                            captured_count,
                            source_field="captured_execution_geometry_field_count",
                        ),
                        "missing_execution_geometry_field_count": _metric(
                            len(missing_execution),
                            source_field="missing_execution_geometry_fields",
                        ),
                        "missing_source_repair_identity_field_count": _metric(
                            len(missing_identity),
                            source_field="missing_source_repair_identity_fields",
                        ),
                    },
                    "row_type": "NR_SOURCE_REPAIR_EXECUTION_IDENTITY_ROW",
                }
            )
    return output_rows


def _counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(_normalized(row.get(field)) for row in rows)
    counts.pop("", None)
    return dict(sorted(counts.items()))


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    anchors = (
        "symbol",
        "source_symbol",
        "market",
        "route_session",
        "side",
        "timeframe",
        "market_timeframe",
        "horizon_id",
        "entry_variant",
        "primitive",
        "target_stop_order_class",
    )
    return {
        field: sum(1 for row in rows if _normalized(row.get(field)) == "")
        for field in anchors
        if sum(1 for row in rows if _normalized(row.get(field)) == "")
    }


def _field_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        values = row.get(field)
        if isinstance(values, list):
            for value in values:
                text = _normalized(value)
                if text:
                    counts[text] += 1
    return dict(sorted(counts.items()))


def _source_artifacts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_by_path = Counter(row["source_path"] for row in rows)
    artifacts = []
    for path in SUPPORT_PATHS:
        artifacts.append(
            {
                "path": _repo_path(path),
                "rows": _line_count(path),
                "runtime_rows_read": runtime_by_path.get(_repo_path(path), 0),
                "sha256_or_git_blob": _sha256(path) if path.exists() else "",
                "suffix": path.suffix,
            }
        )
    return artifacts


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_artifacts = _source_artifacts(rows)
    return {
        "schema_version": "gtos_vnext_nr_source_repair_execution_identity_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "output_rows": _repo_path(OUTPUT_ROWS_PATH),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(
            int(row.get("source_rows_represented") or 0) for row in rows
        ),
        "wave_source_artifact_count": len(source_artifacts),
        "wave_source_rows_counted": sum(item["rows"] for item in source_artifacts),
        "decision_counts": _counts(rows, "decision"),
        "source_role_counts": _counts(rows, "source_role"),
        "source_component_counts": _counts(rows, "source_component"),
        "status_counts": _counts(rows, "status"),
        "repair_action_counts": _counts(rows, "repair_action"),
        "r_evidence_class_counts": _counts(rows, "r_evidence_class"),
        "captured_order_identity_field_counts": _field_counts(
            rows,
            "captured_order_identity_fields",
        ),
        "missing_execution_geometry_field_counts": _field_counts(
            rows,
            "missing_execution_geometry_fields",
        ),
        "missing_source_repair_identity_field_counts": _field_counts(
            rows,
            "missing_source_repair_identity_fields",
        ),
        "exact_r_repaired_rows": sum(1 for row in rows if row.get("exact_r_repaired")),
        "slippage_join_repaired_rows": sum(1 for row in rows if row.get("slippage_join_repaired")),
        "coverage_counts": {
            "symbols": _counts(rows, "symbol"),
            "markets": _counts(rows, "market"),
            "source_symbols": _counts(rows, "source_symbol"),
            "sessions": _counts(rows, "route_session"),
            "sides": _counts(rows, "side"),
            "timeframes": _counts(rows, "timeframe"),
            "entry_variants": _counts(rows, "entry_variant"),
            "target_stop_order_classes": _counts(rows, "target_stop_order_class"),
        },
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "source_artifacts": source_artifacts,
    }


def build(*, check: bool = False) -> dict[str, Any]:
    rows = _runtime_rows()
    summary = _summary(rows)
    row_text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    summary_text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if check:
        if not OUTPUT_ROWS_PATH.exists():
            raise SystemExit(f"missing output rows: {OUTPUT_ROWS_PATH}")
        if not OUTPUT_SUMMARY_PATH.exists():
            raise SystemExit(f"missing output summary: {OUTPUT_SUMMARY_PATH}")
        if OUTPUT_ROWS_PATH.read_text(encoding="utf-8") != row_text:
            raise SystemExit(f"stale output rows: {OUTPUT_ROWS_PATH}")
        if OUTPUT_SUMMARY_PATH.read_text(encoding="utf-8") != summary_text:
            raise SystemExit(f"stale output summary: {OUTPUT_SUMMARY_PATH}")
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_ROWS_PATH.write_text(row_text, encoding="utf-8")
        OUTPUT_SUMMARY_PATH.write_text(summary_text, encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), sort_keys=True))


if __name__ == "__main__":
    main()
