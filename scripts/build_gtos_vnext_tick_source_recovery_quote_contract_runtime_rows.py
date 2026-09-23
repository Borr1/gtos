#!/usr/bin/env python3
"""Build runtime rows for tick/source recovery and quote/tick contract evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_TICK_SOURCE_RECOVERY_QUOTE_CONTRACT_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_tick_source_recovery_quote_contract_runtime"
SOURCE_NAME = "gtos_vnext_tick_source_recovery_quote_contract_runtime_wave"

ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
MASTER_LEDGER = (
    ROUTE_DIR / f"GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_LEDGER_{DATE}.jsonl"
)
OUTPUT_ROWS = (
    ROUTE_DIR / f"GTOS_VNEXT_TICK_SOURCE_RECOVERY_QUOTE_CONTRACT_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR / f"GTOS_VNEXT_TICK_SOURCE_RECOVERY_QUOTE_CONTRACT_RUNTIME_SUMMARY_{DATE}.json"
)

SOURCE_PATH_TOKENS = (
    "otx_g6_tick_aware_end_to_end_resolution",
    "otr061_xau_tick_recovery",
    "oti3_usdjpy_price_only_quote_or_tick_contract",
    "oti4_g6_opening_drive_quarantined_results",
    "oti5_g6_cusum_changepoint_quarantined_results",
    "oti8_cnr061_quarantined_results",
    "cnr061_geometry_horizon_sidecar",
    "g12_otx_g6_post_audit",
)

RUNTIME_SOURCE_FILES: tuple[tuple[str, str], ...] = (
    (
        "otx_packet_proposals",
        "research/science_program_2026_05/06_outcome_testing/"
        "otx_g6_tick_aware_end_to_end_resolution/"
        "OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
    ),
    (
        "otx_tick_coverage",
        "research/science_program_2026_05/06_outcome_testing/"
        "otx_g6_tick_aware_end_to_end_resolution/"
        "OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.json",
    ),
    (
        "otx_opening_drive_quarantine",
        "research/science_program_2026_05/06_outcome_testing/"
        "otx_g6_tick_aware_end_to_end_resolution/"
        "OTX_G6_OTI4B_QUARANTINED_RESULT_ROWS_2026-05-07.jsonl",
    ),
    (
        "oti3_usdjpy_quote_tick_contract",
        "research/science_program_2026_05/06_outcome_testing/"
        "oti3_usdjpy_price_only_quote_or_tick_contract/"
        "OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl",
    ),
    (
        "oti4_opening_drive_quarantine",
        "research/science_program_2026_05/06_outcome_testing/"
        "oti4_g6_opening_drive_quarantined_results/"
        "OTI4_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    ),
    (
        "oti5_cusum_quarantine",
        "research/science_program_2026_05/06_outcome_testing/"
        "oti5_g6_cusum_changepoint_quarantined_results/"
        "OTI5_G6_CUSUM_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    ),
    (
        "cnr061_geometry_sidecar",
        "research/science_program_2026_05/06_outcome_testing/"
        "cnr061_geometry_horizon_sidecar/"
        "CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.jsonl",
    ),
    (
        "oti8_cnr061_result",
        "research/science_program_2026_05/06_outcome_testing/"
        "oti8_cnr061_quarantined_results/"
        "OTI8_CNR061_RESULT_LEDGER_2026-05-08_ROWS.jsonl",
    ),
    (
        "otr061_xau_tick_search",
        "research/science_program_2026_05/06_outcome_testing/"
        "otr061_xau_tick_recovery/"
        "OTR061_XAU_TICK_RECOVERY_SEARCH_LEDGER_2026-05-07.json",
    ),
    (
        "otr061_xau_source_hash",
        "research/science_program_2026_05/06_outcome_testing/"
        "otr061_xau_tick_recovery/"
        "OTR061_XAU_TICK_SOURCE_HASH_LEDGER_2026-05-07.json",
    ),
    (
        "g12_otx_source_tick_coverage",
        "research/science_program_2026_05/06_outcome_testing/"
        "g12_otx_g6_post_audit/"
        "G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07.json",
    ),
)

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "side",
    "source_component",
    "entry_variant",
    "target_stop_order_class",
)

SESSION_MAP = {
    "london": "london_core",
    "ny": "ny_core",
    "new_york": "ny_core",
    "tokyo": "tokyo_kz",
}


def _repo_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else REPO_ROOT / path


def _path_text(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _upper(value: Any) -> str:
    return _norm(value).upper()


def _session(value: Any) -> str:
    raw = _norm(value).casefold()
    return SESSION_MAP.get(raw, raw)


def _session_from_utc(symbol: str, timestamp: str) -> str:
    if not timestamp:
        return ""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return ""
    minutes = dt.hour * 60 + dt.minute
    symbol_key = symbol.upper()
    if symbol_key in {"XAUUSD", "XAGUSD"}:
        windows = ((7 * 60, 10 * 60 + 30, "london_core"), (13 * 60, 17 * 60, "ny_core"))
    elif symbol_key == "NAS100":
        windows = ((13 * 60, 17 * 60, "ny_core"),)
    elif symbol_key in {"US30", "US30_CASH"}:
        windows = ((8 * 60, 10 * 60 + 30, "london_core"), (13 * 60 + 30, 16 * 60, "ny_core"))
    elif symbol_key in {"USDJPY", "GBPJPY"}:
        windows = (
            (0, 3 * 60, "tokyo_kz"),
            (7 * 60, 9 * 60 + 30, "london_core"),
            (13 * 60, 15 * 60 + 30, "ny_core"),
        )
    else:
        windows = ()
    for start, end, session in windows:
        if start <= minutes < end:
            return session
    return "off_core_session"


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _proxy_class(value: float | None) -> str:
    if value is None:
        return ""
    if value >= 1.0:
        return "STRONG_POSITIVE_PROXY_R"
    if value > 0:
        return "POSITIVE_PROXY_R"
    if value <= -1.0:
        return "STRONG_NEGATIVE_PROXY_R"
    if value < 0:
        return "NEGATIVE_PROXY_R"
    return "FLAT_PROXY_R"


@lru_cache(maxsize=None)
def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _read_json_records(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("records", "rows", "source_files", "root_search_results"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [item for item in rows if isinstance(item, dict)]
        return [payload]
    return []


def _read_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.casefold() == ".jsonl":
        return _read_jsonl(path)
    if path.suffix.casefold() == ".json":
        return _read_json_records(path)
    return []


def _source_row_count(path: Path) -> int | None:
    try:
        size = path.stat().st_size
    except OSError:
        return None
    suffix = path.suffix.casefold()
    if suffix == ".json":
        return 1
    if suffix not in {".jsonl", ".csv", ".txt", ".md"}:
        return None
    if size > 5_000_000:
        return None
    try:
        with path.open("rb") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return None


def _metric(value: float | None, source_field: str) -> dict[str, Any]:
    if value is None:
        return {}
    return {
        "sum": value,
        "count": 1,
        "mean": value,
        "min": value,
        "max": value,
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "match_rows_with_metric": 1,
        "source_field": source_field,
        "source_shape": "scalar_proxy",
    }


def _event_scope(row: dict[str, Any]) -> dict[str, str]:
    return {
        field: _norm(row.get(field))
        for field in ANCHOR_FIELDS
        if _norm(row.get(field))
    }


def _runtime_row(
    *,
    source_row: dict[str, Any],
    source_artifact: Path,
    source_row_id: str,
    decision: str,
    source_component: str,
    source_role: str,
    r_evidence_class: str,
    action_class: str,
    runtime_effect: str,
    symbol: str = "",
    side: str = "",
    route_session: str = "",
    target_stop_order_class: str = "",
    proxy_r: float | None = 0.0,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    symbol = _norm(symbol)
    side = _upper(side)
    row: dict[str, Any] = {
        "schema_version": "gtos_vnext_tick_source_recovery_quote_contract_runtime_v1",
        "wave_id": WAVE_ID,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "source_group": "tick_source_recovery_quote_contract",
        "source_role": source_role,
        "system_surface": "tick_source_recovery_quote_contract_runtime",
        "source_component": source_component,
        "decision": decision,
        "action_class": action_class,
        "implementation_action": runtime_effect,
        "runtime_effect_now": runtime_effect,
        "r_evidence_class": r_evidence_class,
        "source_row_id": source_row_id,
        "row_key": source_row_id,
        "source_artifact": _path_text(source_artifact),
        "source_artifact_sha256": _sha256_file(source_artifact),
        "source_path": _path_text(source_artifact),
        "drill_through_path": _path_text(source_artifact),
        "symbol": symbol,
        "source_symbol": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
        "market": symbol,
        "timeframe": "M15" if symbol else "",
        "market_timeframe": "M15" if symbol else "",
        "route_session": route_session,
        "side": side,
        "horizon_id": "ordered_tick_path_or_quote_contract",
        "primitive": "tick_source_recovery_quote_contract",
        "source_bound": bool(symbol or source_artifact),
        "source_complete": decision in {"FOLLOW", "AVOID"} and bool(symbol and side),
        "target_stop_order_class": target_stop_order_class,
        "proxy_r_class": _proxy_class(proxy_r),
        "source_candidate_id": source_row.get("candidate_id")
        or source_row.get("source_candidate_id")
        or source_row.get("source_row_id"),
        "source_record_id": source_row.get("record_id")
        or source_row.get("source_record_id"),
        "source_packet_id": source_row.get("packet_id") or source_row.get("source_packet_id"),
        "source_status": source_row.get("result_status")
        or source_row.get("terminal_result_status")
        or source_row.get("path_status")
        or source_row.get("eligibility_decision")
        or source_row.get("opening_drive_status")
        or source_row.get("terminal_status")
        or source_row.get("score_status"),
        "source_path_status": source_row.get("path_status"),
        "source_opening_drive_status": source_row.get("opening_drive_status"),
        "source_score_status": source_row.get("score_status"),
        "source_terminal_status": source_row.get("terminal_status")
        or source_row.get("terminal_result_status"),
        "validation_safe": source_row.get("validation_safe"),
        "promotion_verdict": source_row.get("promotion_verdict"),
        "row_count": 1,
    }
    metric = _metric(proxy_r, "tick_source_recovery_proxy_r")
    row["r_metrics"] = {
        "effective_n": {
            "sum": 1,
            "count": 1,
            "mean": 1,
            "min": 1,
            "max": 1,
            "positive_rows": 1,
            "negative_rows": 0,
            "zero_rows": 0,
            "match_rows_with_metric": 1,
            "source_field": "runtime_row",
            "source_shape": "row_count",
        }
    }
    if metric:
        row["r_metrics"]["proxy_score"] = metric
    if extra:
        row.update(extra)
    row["event_scope"] = _event_scope(row)
    row["runtime_row_id"] = (
        "tick-source-recovery:"
        + _hash_payload(
            {
                "source_row_id": row["source_row_id"],
                "source_artifact": row["source_artifact"],
                "source_component": row["source_component"],
                "decision": row["decision"],
            }
        )[:24]
    )
    return row


def _target_class_from_status(status: str) -> str:
    status = _upper(status)
    if "TP" in status or "TARGET_REACHED" in status:
        return "TARGET_FIRST_PROXY_DOMINANT"
    if "SL" in status or "STOP" in status:
        return "STOP_FIRST_PROXY_DOMINANT"
    if "NO_ENTRY" in status or "NOFILL" in status or "NO_FILL" in status:
        return "NO_FILL_OR_UNFILLED_DOMINANT"
    if "AMBIG" in status:
        return "TARGET_STOP_AMBIGUOUS_OR_MIXED"
    return ""


def _status_decision(status: str) -> tuple[str, str, str, str, str, float]:
    status = _upper(status)
    if status in {"ENTRY_TOUCHED_THEN_TP1", "TARGET_REACHED_BEFORE_STOP"}:
        return (
            "FOLLOW",
            "tick_source_recovery_target_first_follow",
            "tick_source_recovery_target_first_follow_scorer",
            "TICK_SOURCE_RECOVERY_TARGET_FIRST_FOLLOW",
            "tick_source_recovery_target_first_follow",
            1.0,
        )
    if status == "ENTRY_TOUCHED_THEN_SL":
        return (
            "AVOID",
            "tick_source_recovery_stop_first_avoid",
            "tick_source_recovery_stop_first_avoid_guard",
            "TICK_SOURCE_RECOVERY_STOP_FIRST_AVOID_FILTER",
            "tick_source_recovery_stop_first_avoid_filter",
            -1.0,
        )
    if status in {"NO_ENTRY_TOUCH_NO_R_SCORED", "NO_FILL_NO_ENTRY_TOUCH"}:
        return (
            "MIXED",
            "tick_source_recovery_no_entry_touch_source_acquisition",
            "tick_source_recovery_no_entry_touch_source_acquisition_guard",
            "TICK_SOURCE_RECOVERY_NO_ENTRY_TOUCH_SOURCE_ACQUISITION_REQUIRED",
            "tick_source_recovery_no_entry_touch_source_acquisition_guard",
            0.0,
        )
    if status == "NO_TERMINAL_WITHIN_ORDERED_HORIZON":
        return (
            "MIXED",
            "tick_source_recovery_no_terminal_pending_guard",
            "tick_source_recovery_no_terminal_pending_guard",
            "TICK_SOURCE_RECOVERY_NO_TERMINAL_PENDING_SOURCE_ACQUISITION_REQUIRED",
            "tick_source_recovery_no_terminal_pending_guard",
            0.0,
        )
    if "SOURCE_BLOCKED" in status or "FILTER_FAILED" in status or "NOT_COUNTABLE" in status:
        return (
            "MIXED",
            "tick_source_recovery_opening_drive_source_acquisition",
            "tick_source_recovery_opening_drive_source_acquisition_guard",
            "TICK_SOURCE_RECOVERY_OPENING_DRIVE_SOURCE_ACQUISITION_REQUIRED",
            "tick_source_recovery_opening_drive_source_acquisition_guard",
            0.0,
        )
    return (
        "MIXED",
        "tick_source_recovery_path_ready_context",
        "tick_source_recovery_path_ready_context_guard",
        "TICK_SOURCE_RECOVERY_PATH_READY_CONTEXT",
        "tick_source_recovery_path_ready_context",
        0.0,
    )


def _row_symbol(row: dict[str, Any]) -> str:
    return _norm(row.get("symbol") or row.get("broker_symbol") or row.get("target_symbol"))


def _row_session(row: dict[str, Any]) -> str:
    return _session(row.get("session")) or _session_from_utc(
        _row_symbol(row),
        _norm(
            row.get("decision_asof_utc")
            or row.get("candidate_close_utc")
            or row.get("quote_timestamp_utc")
        ),
    )


def _build_otx_proposal_rows(path: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_rows = []
    for row in rows:
        path_packet = row.get("ordered_tick_path_packet") or {}
        path_status = _upper(path_packet.get("path_status") or row.get("path_status"))
        if path_status == "ORDERED_TICK_PATH_EMPTY_OR_MISSING":
            decision, component, role, r_class, effect, proxy_r = (
                "MIXED",
                "tick_source_recovery_ordered_path_source_acquisition",
                "tick_source_recovery_ordered_path_source_acquisition_guard",
                "TICK_SOURCE_RECOVERY_ORDERED_PATH_SOURCE_ACQUISITION_REQUIRED",
                "tick_source_recovery_ordered_path_source_acquisition_guard",
                0.0,
            )
        else:
            decision, component, role, r_class, effect, proxy_r = (
                "MIXED",
                "tick_source_recovery_path_ready_context",
                "tick_source_recovery_path_ready_context_guard",
                "TICK_SOURCE_RECOVERY_PATH_READY_CONTEXT",
                "tick_source_recovery_path_ready_context",
                0.0,
            )
        runtime_rows.append(
            _runtime_row(
                source_row=row,
                source_artifact=path,
                source_row_id=_norm(row.get("record_id") or row.get("packet_id")),
                decision=decision,
                source_component=component,
                source_role=role,
                r_evidence_class=r_class,
                action_class=effect,
                runtime_effect=effect,
                symbol=_row_symbol(row),
                side=row.get("side"),
                route_session=_row_session(row),
                target_stop_order_class="NO_FILL_OR_UNFILLED_DOMINANT"
                if component.endswith("source_acquisition")
                else "",
                proxy_r=proxy_r,
                extra={
                    "ordered_tick_path_status": path_status,
                    "decision_quote_status": (row.get("decision_quote_packet") or {}).get(
                        "decision_quote_status"
                    ),
                    "path_row_count": path_packet.get("path_row_count"),
                    "duplicate_group_id": row.get("duplicate_group_id"),
                    "validation_safe": row.get("validation_safe"),
                },
            )
        )
    return runtime_rows


def _build_tick_coverage_rows(path: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_rows = []
    for row in rows:
        status = _upper(row.get("path_status"))
        quote_status = _upper(row.get("decision_quote_status"))
        if status != "ORDERED_TICK_PATH_AVAILABLE" or "NOT_FOUND" in quote_status:
            decision, component, role, r_class, effect, proxy_r = (
                "MIXED",
                "tick_source_recovery_ordered_path_source_acquisition",
                "tick_source_recovery_ordered_path_source_acquisition_guard",
                "TICK_SOURCE_RECOVERY_ORDERED_PATH_SOURCE_ACQUISITION_REQUIRED",
                "tick_source_recovery_ordered_path_source_acquisition_guard",
                0.0,
            )
        else:
            decision, component, role, r_class, effect, proxy_r = (
                "MIXED",
                "tick_source_recovery_path_ready_context",
                "tick_source_recovery_path_ready_context_guard",
                "TICK_SOURCE_RECOVERY_PATH_READY_CONTEXT",
                "tick_source_recovery_path_ready_context",
                0.0,
            )
        runtime_rows.append(
            _runtime_row(
                source_row=row,
                source_artifact=path,
                source_row_id=_norm(row.get("record_id") or row.get("packet_id")),
                decision=decision,
                source_component=component,
                source_role=role,
                r_evidence_class=r_class,
                action_class=effect,
                runtime_effect=effect,
                symbol=_row_symbol(row),
                route_session=_session_from_utc(
                    _row_symbol(row),
                    _norm(row.get("decision_asof_utc")),
                ),
                target_stop_order_class="NO_FILL_OR_UNFILLED_DOMINANT"
                if component.endswith("source_acquisition")
                else "",
                proxy_r=proxy_r,
                extra={
                    "ordered_tick_path_status": status,
                    "decision_quote_status": quote_status,
                    "packet_specific_status": row.get("packet_specific_status"),
                    "path_row_count": row.get("path_row_count"),
                },
            )
        )
    return runtime_rows


def _build_status_rows(path: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_rows = []
    for row in rows:
        status = _upper(
            row.get("terminal_result_status")
            or row.get("result_status")
            or row.get("quarantined_result_status")
            or row.get("terminal_status")
        )
        decision, component, role, r_class, effect, default_proxy = _status_decision(status)
        proxy_r = _float(row.get("synthetic_r")) or default_proxy
        if decision == "AVOID" and proxy_r > 0:
            proxy_r = -abs(default_proxy)
        runtime_rows.append(
            _runtime_row(
                source_row=row,
                source_artifact=path,
                source_row_id=_norm(row.get("record_id") or row.get("duplicate_group_id")),
                decision=decision,
                source_component=component,
                source_role=role,
                r_evidence_class=r_class,
                action_class=effect,
                runtime_effect=effect,
                symbol=_row_symbol(row),
                side=row.get("side"),
                route_session=_row_session(row),
                target_stop_order_class=_target_class_from_status(status),
                proxy_r=proxy_r,
                extra={
                    "source_result_status": row.get("result_status")
                    or row.get("quarantined_result_status"),
                    "terminal_result_status": row.get("terminal_result_status")
                    or row.get("terminal_status"),
                    "opening_drive_status": row.get("opening_drive_status"),
                    "countable_denominator_row": row.get("countable_denominator_row"),
                    "countable_for_discovery_summary": row.get(
                        "countable_for_discovery_summary"
                    ),
                    "duplicate_group_id": row.get("duplicate_group_id"),
                    "path_tick_count": row.get("path_tick_count"),
                    "path_source_files": row.get("path_source_files"),
                    "matrix_residual_target_r_from_executable_quote": row.get(
                        "matrix_residual_target_r_from_executable_quote"
                    ),
                },
            )
        )
    return runtime_rows


def _build_oti3_rows(path: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_rows = []
    for row in rows:
        eligibility = _upper(row.get("eligibility_decision"))
        quote_status = _upper(row.get("quote_tick_evidence_status"))
        same_timestamp_ambiguity = bool(row.get("same_timestamp_ambiguity"))
        if eligibility == "ELIGIBLE_CONTRACT_EVIDENCE":
            decision, component, role, r_class, effect, proxy_r = (
                "AVOID",
                "tick_source_recovery_quote_tick_nofill_avoid",
                "tick_source_recovery_quote_tick_nofill_avoid_guard",
                "TICK_SOURCE_RECOVERY_QUOTE_TICK_NOFILL_AVOID_FILTER",
                "tick_source_recovery_quote_tick_nofill_avoid_filter",
                -0.5,
            )
            target_class = "NO_FILL_OR_UNFILLED_DOMINANT"
        else:
            decision, component, role, r_class, effect, proxy_r = (
                "MIXED",
                "tick_source_recovery_separate_fill_path_source_acquisition",
                "tick_source_recovery_separate_fill_path_source_acquisition_guard",
                "TICK_SOURCE_RECOVERY_SEPARATE_FILL_PATH_SOURCE_ACQUISITION_REQUIRED",
                "tick_source_recovery_separate_fill_path_source_acquisition_guard",
                0.0,
            )
            target_class = (
                "TARGET_STOP_AMBIGUOUS_OR_MIXED"
                if same_timestamp_ambiguity
                else "NO_FILL_OR_UNFILLED_DOMINANT"
            )
        runtime_rows.append(
            _runtime_row(
                source_row=row,
                source_artifact=path,
                source_row_id=_norm(row.get("source_row_id") or row.get("source_packet_row_id")),
                decision=decision,
                source_component=component,
                source_role=role,
                r_evidence_class=r_class,
                action_class=effect,
                runtime_effect=effect,
                symbol=_row_symbol(row),
                side=row.get("side"),
                route_session=_row_session(row),
                target_stop_order_class=target_class,
                proxy_r=proxy_r,
                extra={
                    "quote_tick_evidence_status": quote_status,
                    "eligibility_decision": eligibility,
                    "categorical_lifecycle_label": row.get(
                        "categorical_lifecycle_label"
                    ),
                    "exact_blocker_codes": row.get("exact_blocker_codes"),
                    "same_timestamp_ambiguity": same_timestamp_ambiguity,
                    "source_window_row_count": row.get("source_window_row_count"),
                    "ordered_source_events": row.get("ordered_source_events"),
                },
            )
        )
    return runtime_rows


def _build_cnr_sidecar_rows(path: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_rows = []
    for row in rows:
        runtime_rows.append(
            _runtime_row(
                source_row=row,
                source_artifact=path,
                source_row_id=_norm(row.get("record_id") or row.get("source_record_id")),
                decision="MIXED",
                source_component="tick_source_recovery_geometry_join_context",
                source_role="tick_source_recovery_geometry_join_context_guard",
                r_evidence_class="TICK_SOURCE_RECOVERY_GEOMETRY_JOIN_CONTEXT",
                action_class="tick_source_recovery_geometry_join_context",
                runtime_effect="tick_source_recovery_geometry_join_context",
                symbol=_row_symbol(row),
                side=row.get("side"),
                route_session=_row_session(row),
                proxy_r=0.0,
                extra={
                    "source_join_status": row.get("source_join_status"),
                    "tick_coverage_summary": row.get("tick_coverage_summary"),
                    "timing_model_family": row.get("timing_model_family"),
                    "target_model_family": row.get("target_model_family"),
                },
            )
        )
    return runtime_rows


def _build_support_row(kind: str, path: Path, row: dict[str, Any]) -> dict[str, Any]:
    symbol = _row_symbol(row) or "XAUUSD"
    source_component = "tick_source_recovery_source_hash_context"
    source_role = "tick_source_recovery_source_hash_context_guard"
    r_class = "TICK_SOURCE_RECOVERY_SOURCE_HASH_CONTEXT"
    effect = "tick_source_recovery_source_hash_context"
    target_class = ""
    if kind == "g12_otx_source_tick_coverage":
        verdict = _upper(row.get("tick_coverage_verdict"))
        windows = (row.get("critical_xau_2026_05_06") or {}).get("windows") or []
        missing_required_window = any(
            isinstance(item, dict) and int(item.get("row_count") or 0) == 0
            for item in windows
        )
        if missing_required_window or "PARTIAL" in verdict:
            source_component = "tick_source_recovery_partial_coverage_source_acquisition"
            source_role = "tick_source_recovery_partial_coverage_source_acquisition_guard"
            r_class = "TICK_SOURCE_RECOVERY_PARTIAL_COVERAGE_SOURCE_ACQUISITION_REQUIRED"
            effect = "tick_source_recovery_partial_coverage_source_acquisition_guard"
            target_class = "NO_FILL_OR_UNFILLED_DOMINANT"
    return _runtime_row(
        source_row=row,
        source_artifact=path,
        source_row_id=f"{kind}:{path.name}",
        decision="MIXED",
        source_component=source_component,
        source_role=source_role,
        r_evidence_class=r_class,
        action_class=effect,
        runtime_effect=effect,
        symbol=symbol,
        route_session=_session_from_utc(
            symbol,
            _norm(
                ((row.get("required_window_utc") or {}).get("decision_asof"))
                or row.get("generated_at_utc")
            ),
        ),
        target_stop_order_class=target_class,
        proxy_r=0.0,
        extra={
            "coverage_status": (row.get("mt5_read_only_route") or {}).get(
                "coverage_status"
            ),
            "tick_coverage_verdict": row.get("tick_coverage_verdict"),
            "source_hash_verdict": row.get("source_hash_verdict"),
            "mt5_read_only_rows": (row.get("mt5_read_only_route") or {}).get("rows"),
            "source_file_count": len(row.get("source_files") or []),
        },
    )


def _rows_for_source(kind: str, path: Path) -> list[dict[str, Any]]:
    rows = _read_rows(path)
    if kind == "otx_packet_proposals":
        return _build_otx_proposal_rows(path, rows)
    if kind == "otx_tick_coverage":
        return _build_tick_coverage_rows(path, rows)
    if kind == "oti3_usdjpy_quote_tick_contract":
        return _build_oti3_rows(path, rows)
    if kind in {
        "otx_opening_drive_quarantine",
        "oti4_opening_drive_quarantine",
        "oti5_cusum_quarantine",
        "oti8_cnr061_result",
    }:
        return _build_status_rows(path, rows)
    if kind == "cnr061_geometry_sidecar":
        return _build_cnr_sidecar_rows(path, rows)
    if rows:
        return [_build_support_row(kind, path, rows[0])]
    return []


@lru_cache(maxsize=1)
def _source_units() -> tuple[dict[str, Any], ...]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    with MASTER_LEDGER.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            path = _norm(row.get("source_artifact_path")).replace("\\", "/")
            path_l = path.casefold()
            if not any(token in path_l for token in SOURCE_PATH_TOKENS):
                continue
            state = _norm(row.get("conversion_state"))
            if state not in {
                "NOT_STARTED",
                "REPAIR_NEEDED_WITH_EXACT_FIELD_SOURCE_CODE_ACTION",
                "CONVERTED_EXECUTION_ADJACENT_FRICTION_BEHAVIOR",
                "IMPLEMENTED_RUNTIME_CODE_CONFIG_TESTS",
            }:
                continue
            if state in {
                "CONVERTED_EXECUTION_ADJACENT_FRICTION_BEHAVIOR",
                "IMPLEMENTED_RUNTIME_CODE_CONFIG_TESTS",
            } and row.get("batch_wave_id") != WAVE_ID:
                continue
            if path in seen:
                continue
            seen.add(path)
            source_path = _repo_path(path)
            selected.append(
                {
                    "unit_id": row.get("intelligence_unit_id"),
                    "path": path,
                    "name": source_path.name,
                    "hash": row.get("source_artifact_hash"),
                    "hash_algorithm": row.get("source_artifact_hash_algorithm"),
                    "row_count": _source_row_count(source_path),
                }
            )
    return tuple(selected)


def _source_artifacts_summary(runtime_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_source = Counter(row["source_artifact"] for row in runtime_rows)
    artifacts = []
    for unit in _source_units():
        artifacts.append(
            {
                **unit,
                "runtime_rows_read": rows_by_source.get(str(unit["path"]), 0),
            }
        )
    return artifacts


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def build_runtime_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for kind, path_text in RUNTIME_SOURCE_FILES:
        rows.extend(_rows_for_source(kind, _repo_path(path_text)))
    rows.sort(key=lambda row: (row["source_component"], row["source_row_id"]))
    coverage = {
        "symbols": dict(sorted(Counter(row.get("symbol") for row in rows if row.get("symbol")).items())),
        "source_symbols": dict(sorted(Counter(row.get("source_symbol") for row in rows if row.get("source_symbol")).items())),
        "markets": dict(sorted(Counter(row.get("market") for row in rows if row.get("market")).items())),
        "timeframes": dict(sorted(Counter(row.get("timeframe") for row in rows if row.get("timeframe")).items())),
        "sessions": dict(sorted(Counter(row.get("route_session") for row in rows if row.get("route_session")).items())),
        "sides": dict(sorted(Counter(row.get("side") for row in rows if row.get("side")).items())),
        "entry_variants": dict(sorted(Counter(row.get("entry_variant") for row in rows if row.get("entry_variant")).items())),
        "target_stop_order_classes": dict(sorted(Counter(row.get("target_stop_order_class") for row in rows if row.get("target_stop_order_class")).items())),
    }
    source_artifacts = _source_artifacts_summary(rows)
    known_counts = [item["row_count"] for item in source_artifacts if item["row_count"] is not None]
    source_component_counts = Counter(row["source_component"] for row in rows)
    r_class_counts = Counter(row["r_evidence_class"] for row in rows)
    summary = {
        "schema_version": "gtos_vnext_tick_source_recovery_quote_contract_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": len(rows),
        "wave_source_rows_counted": sum(known_counts),
        "selected_open_unit_count": len(source_artifacts),
        "row_count_unknown_unit_count": sum(
            1 for item in source_artifacts if item["row_count"] is None
        ),
        "decision_counts": dict(sorted(Counter(row["decision"] for row in rows).items())),
        "source_component_counts": dict(sorted(source_component_counts.items())),
        "source_role_counts": dict(sorted(Counter(row["source_role"] for row in rows).items())),
        "r_evidence_class_counts": dict(sorted(r_class_counts.items())),
        "action_class_counts": dict(sorted(Counter(row["action_class"] for row in rows).items())),
        "proxy_r_class_counts": dict(sorted(Counter(row.get("proxy_r_class") for row in rows if row.get("proxy_r_class")).items())),
        "source_acquisition_required_rows": sum(
            count
            for component, count in source_component_counts.items()
            if component.endswith("source_acquisition")
            or component == "tick_source_recovery_no_terminal_pending_guard"
        ),
        "positive_proxy_rows": sum(1 for row in rows if row["decision"] == "FOLLOW"),
        "avoid_or_redesign_rows": sum(1 for row in rows if row["decision"] == "AVOID"),
        "coverage_counts": coverage,
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "source_artifacts": source_artifacts,
    }
    return rows, summary


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _outputs_match(rows: list[dict[str, Any]], summary: dict[str, Any]) -> bool:
    if not OUTPUT_ROWS.exists() or not OUTPUT_SUMMARY.exists():
        return False
    expected_rows = [
        json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows
    ]
    if OUTPUT_ROWS.read_text(encoding="utf-8").splitlines() != expected_rows:
        return False
    try:
        actual_summary = json.loads(OUTPUT_SUMMARY.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return actual_summary == summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows, summary = build_runtime_rows()
    if args.check:
        if not _outputs_match(rows, summary):
            print("Generated tick/source recovery quote-contract runtime outputs are stale.")
            return 1
        print(
            "Tick/source recovery quote-contract runtime outputs are current: "
            f"{summary['runtime_row_count']} rows"
        )
        return 0
    write_outputs(rows, summary)
    print(
        "Wrote tick/source recovery quote-contract runtime outputs: "
        f"{OUTPUT_ROWS} ({summary['runtime_row_count']} rows)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
