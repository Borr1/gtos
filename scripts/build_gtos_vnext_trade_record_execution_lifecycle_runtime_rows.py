#!/usr/bin/env python3
"""Build trade-record execution lifecycle runtime rows for GTOS vNext."""

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

from src.research_infra.trade_index_lifecycle_audit import (  # noqa: E402
    build_trade_index_lifecycle_rows,
    read_jsonl_with_lines,
    read_trade_records,
)


ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
DATE = "2026-05-18"
WAVE_ID = "WAVE_TRADE_RECORD_EXECUTION_LIFECYCLE_RUNTIME"
OUTPUT_ROWS_PATH = (
    ROUTE_DIR / f"GTOS_VNEXT_TRADE_RECORD_EXECUTION_LIFECYCLE_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY_PATH = (
    ROUTE_DIR / f"GTOS_VNEXT_TRADE_RECORD_EXECUTION_LIFECYCLE_RUNTIME_SUMMARY_{DATE}.json"
)

TRADE_RECORD_ROOT = REPO_ROOT / "knowledge_base" / "trade_records"
PENDING_LIFECYCLE_AUDIT = REPO_ROOT / "shadow_logs" / "pending_limit_lifecycle_audit.jsonl"
TRADE_INDEX_LIFECYCLE_AUDIT = REPO_ROOT / "shadow_logs" / "trade_index_lifecycle_audit.jsonl"
TRADE_RECORD_INVENTORY_INDEX = (
    REPO_ROOT / "knowledge_base" / "index" / "trade_record_inventory_index_2026-05-05.json"
)
SUPPORT_PATHS = (
    REPO_ROOT / ".context" / "03_analysis" / "apr13_full_execution_audit.md",
    REPO_ROOT / ".context" / "03_analysis" / "research_execution_plan_113q.md",
    TRADE_RECORD_INVENTORY_INDEX,
    TRADE_INDEX_LIFECYCLE_AUDIT,
    PENDING_LIFECYCLE_AUDIT,
)
GENERATED_AT_UTC = "2026-05-21T00:00:00+00:00"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_text(text: str, size: int = 24) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:size]


def _repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _normalized(value: Any) -> str:
    if value in (None, "None"):
        return ""
    return str(value).strip()


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
            "source_shape": "trade_record_execution_lifecycle",
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


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return sum(1 for _ in fh)


def _json_index_count(path: Path) -> int:
    if not path.exists():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return 0
    entries = payload.get("entries")
    if isinstance(entries, list):
        return len(entries)
    return int(payload.get("trade_record_count") or payload.get("index_count") or 0)


def _canonical_session(value: Any) -> str:
    text = _normalized(value).casefold()
    return {
        "london": "london_core",
        "london_core": "london_core",
        "ny": "ny_core",
        "new_york": "ny_core",
        "ny_core": "ny_core",
        "tokyo": "tokyo_kz",
        "tokyo_kz": "tokyo_kz",
        "asia": "tokyo_kz",
    }.get(text, _normalized(value))


def _route_family(framework: str) -> str:
    return {
        "ob_retest": "ob_retest",
        "breaker_re_entry": "breaker_re_entry",
        "fvg_fill": "fvg_fill",
    }.get(framework, framework or "trade_record_execution_lifecycle")


def _source_repair_required(row: dict[str, Any]) -> bool:
    completeness = _normalized(row.get("lifecycle_completeness"))
    outcome = _normalized(row.get("final_outcome"))
    return bool(row.get("action_required_codes")) or completeness in {
        "UNKNOWN_STATE_DOCUMENTED",
        "LIMIT_PLACED_DOCUMENTED_LEGACY_LIFECYCLE_GAP",
    } or outcome == "EXECUTION_FAILED"


def _source_component(row: dict[str, Any]) -> str:
    if _source_repair_required(row):
        return "trade_record_execution_source_repair"
    if row.get("actual_r") is not None or _normalized(row.get("lifecycle_completeness")) == "LIMIT_PLACED_COMPLETE_WITH_EXIT":
        return "trade_record_realized_exit_context"
    if _normalized(row.get("lifecycle_state")) == "LIMIT_PLACED":
        return "trade_record_pending_lifecycle_context"
    if _normalized(row.get("final_outcome")).startswith("REJECTED"):
        return "trade_record_rejected_decision_context"
    return "trade_record_execution_lifecycle_context"


def _source_role(row: dict[str, Any]) -> str:
    if _source_repair_required(row):
        return "source_repair_execution_plan"
    component = _source_component(row)
    if component == "trade_record_realized_exit_context":
        return "trade_record_realized_exit_context"
    if component == "trade_record_pending_lifecycle_context":
        return "trade_record_pending_lifecycle_context"
    if component == "trade_record_rejected_decision_context":
        return "trade_record_rejected_decision_context"
    return "trade_record_execution_lifecycle_context"


def _r_evidence_class(row: dict[str, Any]) -> str:
    if _source_repair_required(row):
        return "SOURCE_REPAIR_FOR_EXACT_R"
    component = _source_component(row)
    if component == "trade_record_realized_exit_context":
        return "TRADE_RECORD_REALIZED_EXIT_CONTEXT"
    if component == "trade_record_pending_lifecycle_context":
        return "TRADE_RECORD_PENDING_LIFECYCLE_CONTEXT"
    if component == "trade_record_rejected_decision_context":
        return "TRADE_RECORD_REJECTED_DECISION_CONTEXT"
    return "TRADE_RECORD_EXECUTION_LIFECYCLE_CONTEXT"


def _implementation_action(row: dict[str, Any]) -> str:
    if _source_repair_required(row):
        return "SOURCE_JOIN_REPAIR_REQUIRED"
    component = _source_component(row)
    if component == "trade_record_realized_exit_context":
        return "MERGE_AS_CONTEXT_STRESS_GUARD_INPUT"
    if component == "trade_record_pending_lifecycle_context":
        return "MERGE_AS_CONTROL_CONTEXT_PENDING_EXACT_GEOMETRY"
    return "MERGE_AS_CONTEXT_STRESS_GUARD_INPUT"


def _runtime_effect(row: dict[str, Any]) -> str:
    if _source_repair_required(row):
        return "trade_record_source_repair_risk_guard"
    return "trade_record_execution_lifecycle_shadow_context"


def _actual_r_class(actual_r: Any) -> str:
    value = _num(actual_r)
    if value is None:
        return ""
    if value >= 1.0:
        return "REALIZED_EXIT_GE_1R"
    if value > 0:
        return "REALIZED_EXIT_POSITIVE_SUB_1R"
    if value <= -1.0:
        return "REALIZED_EXIT_STOP_OR_WORSE"
    if value < 0:
        return "REALIZED_EXIT_NEGATIVE_SUB_1R"
    return "REALIZED_EXIT_FLAT"


def _target_stop_class(row: dict[str, Any]) -> str:
    exit_reason = _normalized(row.get("exit_reason")).casefold()
    actual_r = _num(row.get("actual_r"))
    if not exit_reason and actual_r is None:
        return ""
    if "sl" in exit_reason or (actual_r is not None and actual_r <= -0.95):
        return "STOP_FIRST_PROXY_DOMINANT"
    if "tp" in exit_reason or (actual_r is not None and actual_r >= 1.0):
        return "TARGET_FIRST_PROXY_DOMINANT"
    return "TARGET_STOP_AMBIGUOUS_OR_MIXED"


def _row_by_source_path(
    trade_records: list[tuple[Path, dict[str, Any]]],
) -> dict[str, tuple[Path, dict[str, Any]]]:
    by_path: dict[str, tuple[Path, dict[str, Any]]] = {}
    for path, record in trade_records:
        rel = path.relative_to(TRADE_RECORD_ROOT).as_posix()
        by_path[rel] = (path, record)
    return by_path


def _runtime_row(
    row: dict[str, Any],
    *,
    path: Path,
    record: dict[str, Any],
    line_no: int,
) -> dict[str, Any]:
    metadata = _safe_dict(record.get("metadata"))
    pipeline = _safe_dict(record.get("decision_pipeline"))
    trade_params = _safe_dict(record.get("trade_parameters"))
    exit_payload = _safe_dict(record.get("exit"))
    source_path = _repo_path(path)
    row_id = f"trade_record_execution_lifecycle:{_hash_text(source_path + '|' + _normalized(row.get('row_key')))}"
    symbol = _normalized(row.get("symbol") or metadata.get("symbol") or path.parent.name)
    session = _canonical_session(row.get("kill_zone") or metadata.get("kill_zone"))
    side = _normalized(pipeline.get("ai_direction") or trade_params.get("direction"))
    framework = _normalized(pipeline.get("ai_framework"))
    actual_r = row.get("actual_r")
    source_component = _source_component(row)
    source_role = _source_role(row)
    source_repair = _source_repair_required(row)
    target_stop_class = _target_stop_class({**row, **exit_payload})
    output = {
        "trade_record_execution_lifecycle_runtime_row_id": row_id,
        "row_key": row_id,
        "source_row_id": row.get("row_key"),
        "schema_version": "gtos_vnext_trade_record_execution_lifecycle_runtime_v1",
        "evidence_family": "gtos_vnext_trade_record_execution_lifecycle",
        "source_name": "gtos_vnext_trade_record_execution_lifecycle_wave",
        "source_group": "trade_record_execution_lifecycle",
        "source_role": source_role,
        "system_surface": (
            "trade_record_execution_lifecycle_source_repair_guard"
            if source_repair
            else "trade_record_execution_lifecycle_context"
        ),
        "source_component": source_component,
        "source_path": source_path,
        "source_artifact": source_path,
        "source_artifact_sha256": _sha256(path),
        "source_line_no": line_no,
        "source_symbol": symbol,
        "symbol": symbol,
        "market": symbol,
        "route_session": session,
        "session": session,
        "side": side,
        "timeframe": "M15",
        "market_timeframe": "M15",
        "horizon_id": "",
        "framework": framework,
        "route_family": _route_family(framework),
        "target_stop_order_class": target_stop_class,
        "decision": "MIXED",
        "review_action": "MIXED",
        "action_class": source_component,
        "implementation_action": _implementation_action(row),
        "runtime_effect_now": _runtime_effect(row),
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "validation_safe": False,
        "r_evidence_class": _r_evidence_class(row),
        "source_repair_required": source_repair,
        "source_acquisition_required": False,
        "trade_record_trade_id": row.get("trade_record_trade_id"),
        "limit_intent_trade_id": row.get("limit_intent_trade_id"),
        "candidate_id": row.get("candidate_id"),
        "decision_time_utc": row.get("decision_time_utc"),
        "record_date": row.get("record_date"),
        "ai_decision": row.get("ai_decision"),
        "ai_grade": pipeline.get("ai_grade"),
        "ai_confidence": pipeline.get("ai_confidence"),
        "final_outcome": row.get("final_outcome"),
        "lifecycle_state": row.get("lifecycle_state"),
        "lifecycle_completeness": row.get("lifecycle_completeness"),
        "trade_index_lifecycle_status": row.get("trade_index_lifecycle_status"),
        "documented_limitation_codes": row.get("documented_limitation_codes") or [],
        "action_required_codes": row.get("action_required_codes") or [],
        "has_execution": row.get("has_execution"),
        "has_exit": row.get("has_exit"),
        "has_embedded_pending_lifecycle": row.get("has_embedded_pending_lifecycle"),
        "has_pending_lifecycle_audit": row.get("has_pending_lifecycle_audit"),
        "pending_lifecycle_final_state": row.get("pending_lifecycle_final_state"),
        "pending_lifecycle_final_state_status": row.get("pending_lifecycle_final_state_status"),
        "pending_lifecycle_missed_move_classification": row.get(
            "pending_lifecycle_missed_move_classification"
        ),
        "pending_lifecycle_trade_id_global_uniqueness_status": row.get(
            "pending_lifecycle_trade_id_global_uniqueness_status"
        ),
        "broker_position_mismatch_status": row.get("broker_position_mismatch_status"),
        "raw_trade_id_collision_symbols": row.get("raw_trade_id_collision_symbols") or [],
        "entry_price": row.get("entry_price"),
        "stop_loss": row.get("stop_loss"),
        "take_profit_1": row.get("take_profit_1"),
        "actual_r": actual_r,
        "actual_r_class": _actual_r_class(actual_r),
        "exit_type": exit_payload.get("exit_type"),
        "exit_reason": exit_payload.get("exit_reason") or exit_payload.get("close_reason"),
        "exit_time": exit_payload.get("exit_time"),
        "source_rows_represented": 1,
        "source_event_rows": 1,
        "stores_full_prompt_or_response_text": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "runtime_observability_effect_if_runtime_reenabled": True,
        "r_metrics": {
            "effective_n": _metric(1, source_field="source_event_row"),
            "entry_price_present": _metric(1 if row.get("entry_price") is not None else 0, source_field="entry_price"),
            "stop_loss_present": _metric(1 if row.get("stop_loss") is not None else 0, source_field="stop_loss"),
            "take_profit_1_present": _metric(1 if row.get("take_profit_1") is not None else 0, source_field="take_profit_1"),
            "actual_r": _metric(_num(actual_r), source_field="actual_r"),
            "source_repair_required": _metric(1 if source_repair else 0, source_field="source_repair_required"),
        },
        "row_type": "TRADE_RECORD_EXECUTION_LIFECYCLE_RUNTIME_ROW",
    }
    return output


def _runtime_rows() -> list[dict[str, Any]]:
    trade_records = read_trade_records(TRADE_RECORD_ROOT)
    by_source_path = _row_by_source_path(trade_records)
    lifecycle_rows = build_trade_index_lifecycle_rows(
        trade_records=trade_records,
        trade_records_root=TRADE_RECORD_ROOT,
        pending_lifecycle_audit_rows=read_jsonl_with_lines(PENDING_LIFECYCLE_AUDIT),
        generated_at_utc=GENERATED_AT_UTC,
    )
    rows: list[dict[str, Any]] = []
    for line_no, row in enumerate(lifecycle_rows, start=1):
        source_path = _normalized(row.get("source_path"))
        source = by_source_path.get(source_path)
        if source is None:
            continue
        path, record = source
        rows.append(_runtime_row(row, path=path, record=record, line_no=line_no))
    return rows


def _counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(_normalized(row.get(field)) for row in rows)
    counts.pop("", None)
    return dict(sorted(counts.items()))


def _list_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        value = row.get(field)
        if isinstance(value, list):
            for item in value:
                text = _normalized(item)
                if text:
                    counts[text] += 1
        elif _normalized(value):
            counts[_normalized(value)] += 1
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
        "framework",
        "target_stop_order_class",
    )
    result = {}
    for field in anchors:
        count = sum(1 for row in rows if not _normalized(row.get(field)))
        if count:
            result[field] = count
    return result


def _trade_record_artifacts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "path": row["source_path"],
            "sha256": row["source_artifact_sha256"],
            "source_row_id": row["source_row_id"],
        }
        for row in rows
    ]


def _support_artifacts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_paths = Counter(row["source_path"] for row in rows)
    artifacts = []
    for path in SUPPORT_PATHS:
        if not path.exists():
            artifacts.append(
                {
                    "path": _repo_path(path),
                    "rows": 0,
                    "runtime_rows_read": 0,
                    "sha256_or_git_blob": "",
                    "suffix": path.suffix,
                }
            )
            continue
        artifacts.append(
            {
                "path": _repo_path(path),
                "rows": _json_index_count(path) if path.suffix.lower() == ".json" else _line_count(path),
                "runtime_rows_read": runtime_paths.get(_repo_path(path), 0),
                "sha256_or_git_blob": _sha256(path),
                "suffix": path.suffix,
            }
        )
    return artifacts


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    support_artifacts = _support_artifacts(rows)
    trade_record_artifacts = _trade_record_artifacts(rows)
    inventory_count = _json_index_count(TRADE_RECORD_INVENTORY_INDEX)
    return {
        "schema_version": "gtos_vnext_trade_record_execution_lifecycle_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "output_rows": _repo_path(OUTPUT_ROWS_PATH),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(int(row.get("source_rows_represented") or 0) for row in rows),
        "wave_source_artifact_count": len(support_artifacts) + len(trade_record_artifacts),
        "wave_source_rows_counted": (
            sum(int(item.get("rows") or 0) for item in support_artifacts)
            + len(trade_record_artifacts)
        ),
        "support_artifacts": support_artifacts,
        "trade_record_artifact_count": len(trade_record_artifacts),
        "trade_record_artifacts": trade_record_artifacts,
        "trade_record_artifacts_sha256": _hash_text(
            "\n".join(f"{item['path']}:{item['sha256']}" for item in trade_record_artifacts),
            size=64,
        ),
        "inventory_index_count": inventory_count,
        "inventory_delta_to_current_trade_records": len(rows) - inventory_count,
        "decision_counts": _counts(rows, "decision"),
        "source_role_counts": _counts(rows, "source_role"),
        "source_component_counts": _counts(rows, "source_component"),
        "source_repair_required_rows": sum(1 for row in rows if row.get("source_repair_required")),
        "action_required_rows": sum(1 for row in rows if row.get("action_required_codes")),
        "documented_blocker_rows": sum(1 for row in rows if row.get("documented_limitation_codes")),
        "stores_full_prompt_or_response_text_rows": sum(
            1 for row in rows if row.get("stores_full_prompt_or_response_text")
        ),
        "broker_operation_rows": sum(1 for row in rows if row.get("broker_operation")),
        "paid_api_or_vendor_call_rows": sum(1 for row in rows if row.get("paid_api_or_vendor_call")),
        "runtime_trading_or_live_broker_effect_rows": sum(
            1 for row in rows if row.get("runtime_trading_or_live_broker_effect")
        ),
        "runtime_candidate_use_permitted_rows": sum(
            1 for row in rows if row.get("runtime_candidate_use_permitted")
        ),
        "candidate_use_allowed_now_rows": sum(1 for row in rows if row.get("candidate_use_allowed_now")),
        "final_outcome_counts": _counts(rows, "final_outcome"),
        "lifecycle_state_counts": _counts(rows, "lifecycle_state"),
        "lifecycle_completeness_counts": _counts(rows, "lifecycle_completeness"),
        "trade_index_lifecycle_status_counts": _counts(rows, "trade_index_lifecycle_status"),
        "documented_limitation_code_counts": _list_counts(rows, "documented_limitation_codes"),
        "action_required_code_counts": _list_counts(rows, "action_required_codes"),
        "actual_r_class_counts": _counts(rows, "actual_r_class"),
        "target_stop_order_class_counts": _counts(rows, "target_stop_order_class"),
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "coverage_counts": {
            "symbols": _counts(rows, "symbol"),
            "source_symbols": _counts(rows, "source_symbol"),
            "markets": _counts(rows, "market"),
            "sessions": _counts(rows, "route_session"),
            "sides": _counts(rows, "side"),
            "timeframes": _counts(rows, "timeframe"),
            "market_timeframes": _counts(rows, "market_timeframe"),
            "frameworks": _counts(rows, "framework"),
            "route_families": _counts(rows, "route_family"),
            "source_components": _counts(rows, "source_component"),
            "source_roles": _counts(rows, "source_role"),
            "target_stop_order_classes": _counts(rows, "target_stop_order_class"),
        },
        "geometry_coverage_counts": {
            "entry_price": sum(1 for row in rows if row.get("entry_price") is not None),
            "stop_loss": sum(1 for row in rows if row.get("stop_loss") is not None),
            "take_profit_1": sum(1 for row in rows if row.get("take_profit_1") is not None),
            "actual_r": sum(1 for row in rows if row.get("actual_r") is not None),
            "has_execution": sum(1 for row in rows if row.get("has_execution")),
            "has_exit": sum(1 for row in rows if row.get("has_exit")),
            "has_embedded_pending_lifecycle": sum(
                1 for row in rows if row.get("has_embedded_pending_lifecycle")
            ),
            "has_pending_lifecycle_audit": sum(
                1 for row in rows if row.get("has_pending_lifecycle_audit")
            ),
        },
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _existing_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _render_jsonl(rows: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
        for row in rows
    )


def _render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows = _runtime_rows()
    summary = _summary(rows)
    rows_text = _render_jsonl(rows)
    summary_text = _render_json(summary)

    if args.check:
        mismatches = []
        if _existing_text(OUTPUT_ROWS_PATH) != rows_text:
            mismatches.append(_repo_path(OUTPUT_ROWS_PATH))
        if _existing_text(OUTPUT_SUMMARY_PATH) != summary_text:
            mismatches.append(_repo_path(OUTPUT_SUMMARY_PATH))
        if mismatches:
            print("Runtime lifecycle artifacts are not up to date:")
            for item in mismatches:
                print(f"  {item}")
            return 1
        print(
            "Runtime lifecycle artifacts are up to date: "
            f"{len(rows)} rows, {summary['source_repair_required_rows']} source-repair rows"
        )
        return 0

    _write_jsonl(OUTPUT_ROWS_PATH, rows)
    _write_json(OUTPUT_SUMMARY_PATH, summary)
    print(
        f"Wrote {len(rows)} rows to {_repo_path(OUTPUT_ROWS_PATH)} "
        f"and summary to {_repo_path(OUTPUT_SUMMARY_PATH)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
