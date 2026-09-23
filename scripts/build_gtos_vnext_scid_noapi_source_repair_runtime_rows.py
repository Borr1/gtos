#!/usr/bin/env python3
"""Build vNext runtime rows for remaining SCID/no-API source-repair residue."""

from __future__ import annotations

import os
import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_SCID_NOAPI_SOURCE_REPAIR_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_scid_noapi_source_repair"
SOURCE_NAME = "gtos_vnext_scid_noapi_source_repair_wave"
RUNTIME_SURFACE = "scid_noapi_source_repair_runtime"

BUILDER_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
OUTPUT_ROWS = BUILDER_DIR / f"GTOS_VNEXT_SCID_NOAPI_SOURCE_REPAIR_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = BUILDER_DIR / f"GTOS_VNEXT_SCID_NOAPI_SOURCE_REPAIR_RUNTIME_SUMMARY_{DATE}.json"
MASTER_LEDGER = BUILDER_DIR / f"GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_LEDGER_{DATE}.jsonl"
BATCH_LEDGER = BUILDER_DIR / f"GTOS_VNEXT_BATCH_RUNTIME_CONVERSION_LEDGER_{DATE}.jsonl"

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
    "source_component",
    "target_stop_order_class",
)

SCID_SOURCE_TOKENS = (
    "scid_noapi",
    "scid_no_api",
    "scid_anti_boxing",
    "g12_scid",
    "g0_scid",
    "scid_strategy_field",
    "scid_asof",
    "scid_to_asof",
    "scid_expansion",
    "scid_forward_capture",
)

SUPPORT_NAME_TOKENS = (
    "build_",
    "test_",
    "verify_",
    "verification",
    "manifest",
    "readme",
    "starter",
)

BLOCKING_STATUS_TOKENS = (
    "BLOCKED",
    "PENDING",
    "MISSING",
    "FAIL_CLOSED",
    "PROSPECTIVE",
    "UNAVAILABLE",
    "REQUIRE",
    "FORBIDDEN",
    "SOURCE_REQUIREMENT",
    "NOT_COMPUTABLE",
)

REPLAY_STATUS_TOKENS = (
    "PREREGISTERABLE",
    "NO_RESULTS_OPENED",
    "INPUT_PACKET_DESIGNED",
    "CLOSED_FROM_SOURCE",
    "RESOLVED",
    "ACCEPTED_DESCRIPTOR",
)

SYMBOL_ALIASES = {
    "6E": "EURUSD",
    "6EM26-CME": "EURUSD",
    "EURUSD_6E": "EURUSD",
    "EURUSD_FUTURES_6E_PROXY": "EURUSD",
    "6B": "GBPUSD",
    "6BM26-CME": "GBPUSD",
    "GBPUSD_6B": "GBPUSD",
    "GBPUSD_FUTURES_6B_PROXY": "GBPUSD",
    "NQ": "NAS100",
    "NQM26-CME": "NAS100",
    "NAS100_NQ": "NAS100",
    "NAS100_FUTURES_NQ_PROXY": "NAS100",
    "YM": "US30",
    "YMM26-CBOT": "US30",
    "US30_YM": "US30",
    "US30_FUTURES_YM_PROXY": "US30",
    "6J": "USDJPY",
    "6JM26-CME": "USDJPY",
    "USDJPY_6J": "USDJPY",
    "USDJPY_FUTURES_6J_PROXY": "USDJPY",
    "SI": "XAGUSD",
    "SIM26-COMEX": "XAGUSD",
    "XAGUSD_SI": "XAGUSD",
    "XAGUSD_FUTURES_SI_PROXY": "XAGUSD",
    "GC": "XAUUSD",
    "GCM26-COMEX": "XAUUSD",
    "XAUUSD_GC": "XAUUSD",
    "XAUUSD_FUTURES_GC_PROXY": "XAUUSD",
}

FIELD_COMPONENT_OVERRIDES = {
    "baseline_control_fields": "scid_noapi_descriptor_control_replay_attribution",
    "source_symbol_session_partition": "scid_noapi_descriptor_control_replay_attribution",
    "source_control_coverage_not_computable_reasons": "scid_noapi_descriptor_control_replay_attribution",
    "lower_timeframe_asof_path_availability": "scid_noapi_ltf_orderflow_source_acquisition",
    "future_orderflow_depth_proxy_requirements": "scid_noapi_ltf_orderflow_source_acquisition",
    "broker_account_order_history_deal_position_evidence": "scid_noapi_forbidden_surface_guard",
    "intended_side_direction": "scid_noapi_future_capture_source_acquisition",
    "intended_entry_reference": "scid_noapi_future_capture_source_acquisition",
    "intended_stop_reference": "scid_noapi_future_capture_source_acquisition",
    "intended_target_reference": "scid_noapi_future_capture_source_acquisition",
    "poi_type_bounds_source": "scid_noapi_future_capture_source_acquisition",
    "lifecycle_fill_cancel_expiry_source_status": "scid_noapi_future_capture_source_acquisition",
    "framework_setup_family": "scid_noapi_future_capture_source_acquisition",
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _safe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _long_path(path: Path) -> str:
    text = str(path.resolve())
    if os.name == "nt" and len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


@lru_cache(maxsize=None)
def _sha256_file_cached(path_text: str) -> str:
    digest = hashlib.sha256()
    with open(_long_path(Path(path_text)), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return _sha256_file_cached(str(path))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _path_text(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _source_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else REPO_ROOT / path


def _is_scid_source_path(path_text: str) -> bool:
    normalized = path_text.casefold().replace("\\", "/")
    if Path(normalized).name in {OUTPUT_ROWS.name.casefold(), OUTPUT_SUMMARY.name.casefold(), Path(__file__).name.casefold()}:
        return False
    return any(token in normalized for token in SCID_SOURCE_TOKENS)


def _is_support_unit(path_text: str) -> bool:
    name = Path(path_text).name.casefold()
    if name.endswith(".py"):
        return True
    return any(token in name for token in SUPPORT_NAME_TOKENS)


def _read_json_file(path: Path) -> Any:
    with open(_long_path(path), "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _iter_jsonl(path: Path):
    with open(_long_path(path), "r", encoding="utf-8-sig", newline="") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                yield line_no, payload


def _source_row_count(path: Path) -> tuple[int | None, bool]:
    if not path.exists() or not path.is_file():
        return None, False
    suffix = path.suffix.casefold()
    if suffix == ".jsonl":
        return sum(1 for _line_no, _payload in _iter_jsonl(path)), True
    if suffix == ".json":
        payload = _read_json_file(path)
        if isinstance(payload, list):
            return len(payload), True
        return 1, True
    if suffix in {".md", ".txt", ".py", ".csv"}:
        with open(_long_path(path), "rb") as handle:
            return sum(1 for line in handle if line.strip()), True
    return None, False


def _read_batch_source_units() -> list[dict[str, Any]]:
    units: dict[str, dict[str, Any]] = {}
    if BATCH_LEDGER.exists():
        for line in BATCH_LEDGER.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            wave = json.loads(line)
            if wave.get("wave_id") == WAVE_ID:
                for item in wave.get("unit_dispositions", []):
                    unit_id = _norm(item.get("unit_id"))
                    path_text = _norm(item.get("source_artifact_path"))
                    if unit_id and path_text and _is_scid_source_path(path_text):
                        units[unit_id] = dict(item)
                continue
            for item in wave.get("unit_dispositions", []):
                state = _norm(item.get("conversion_state"))
                action = _norm(item.get("planned_or_actual_action"))
                path_text = _norm(item.get("source_artifact_path"))
                unit_id = _norm(item.get("unit_id"))
                if (
                    unit_id
                    and path_text
                    and _is_scid_source_path(path_text)
                    and (state in {"NOT_STARTED", "REPAIR_DEFINED"} or action == "convert_or_kill_by_wave_runtime_surface")
                ):
                    units[unit_id] = dict(item)
    if units:
        return list(units.values())

    if MASTER_LEDGER.exists():
        for line in MASTER_LEDGER.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            path_text = _norm(row.get("source_artifact_path"))
            unit_id = _norm(row.get("intelligence_unit_id"))
            if not unit_id or not path_text or not _is_scid_source_path(path_text):
                continue
            if _norm(row.get("conversion_state")) not in {"NOT_STARTED", "REPAIR_DEFINED"}:
                continue
            units[unit_id] = {
                "unit_id": unit_id,
                "source_artifact_path": path_text,
                "source_artifact_hash": row.get("source_artifact_hash"),
                "row_count": row.get("row_count"),
            }
    return list(units.values())


def _canonical_symbol(value: str) -> str:
    text = _norm(value).upper()
    if not text:
        return ""
    if ":" in text:
        parts = [part for part in re.split(r"[:|]", text) if part]
        for part in parts:
            if part in SYMBOL_ALIASES:
                return SYMBOL_ALIASES[part]
    if text in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[text]
    text = text.replace("_FUTURES_PROXY", "")
    return SYMBOL_ALIASES.get(text, text)


def _source_symbol(value: str) -> str:
    text = _norm(value).upper()
    if "::" in text:
        text = text.split("::", 1)[0]
    if ":" in text:
        parts = [part for part in re.split(r"[:|]", text) if part]
        for part in parts:
            if part in SYMBOL_ALIASES:
                return part
    return text


def _symbol_from_payload(payload: dict[str, Any]) -> tuple[str, str]:
    for key in (
        "symbol",
        "source_symbol",
        "canonical_economic_group",
        "source_proxy_group",
        "source_instrument",
        "candidate_input_row_id",
    ):
        raw = _norm(payload.get(key))
        if not raw:
            continue
        source = _source_symbol(raw)
        symbol = _canonical_symbol(source or raw)
        if symbol:
            return symbol, source or symbol
    return "", ""


def _session_from_payload(payload: dict[str, Any]) -> str:
    for key in ("route_session", "session", "session_bucket", "time_of_day_bucket"):
        raw = _norm(payload.get(key)).upper()
        if not raw:
            continue
        if "TOKYO" in raw or "ASIA" in raw or "UTC_00" in raw:
            return "tokyo_kz"
        if "LONDON" in raw or "UTC_06" in raw or "UTC_07" in raw:
            return "london_core"
        if "NEW_YORK" in raw or "NY" == raw or "UTC_12" in raw or "UTC_13" in raw:
            return "ny_core"
        if "OFF" in raw or "TRANSITION" in raw or "UTC_18_23" in raw:
            return "off_core_session"
    hour = _safe_int(payload.get("utc_hour"))
    if hour is None:
        for key in ("decision_asof_utc", "source_observed_asof_utc", "entry_reference_time_utc"):
            raw = _norm(payload.get(key))
            if not raw:
                continue
            try:
                hour = datetime.fromisoformat(raw.replace("Z", "+00:00")).hour
                break
            except ValueError:
                continue
    if hour is None:
        return ""
    if 0 <= hour < 3:
        return "tokyo_kz"
    if 7 <= hour < 11:
        return "london_core"
    if 13 <= hour < 17:
        return "ny_core"
    return "off_core_session"


def _source_component(field_name: str, *, status: str, path_text: str) -> str:
    field = _norm(field_name).casefold()
    if status.upper().startswith("FORBIDDEN") or "broker" in field:
        return "scid_noapi_forbidden_surface_guard"
    if "strategy_field" in path_text.casefold():
        if "ltf" in field or "orderflow" in field or "lower_timeframe" in field:
            return "scid_strategy_field_ltf_orderflow_source_acquisition"
        return "scid_strategy_field_missing_source_acquisition"
    if "forward_capture_readonly" in path_text.casefold():
        return "scid_forward_readonly_alignment_source_acquisition"
    return FIELD_COMPONENT_OVERRIDES.get(field, "scid_noapi_missing_source_acquisition")


def _status_is_blocking(status: str) -> bool:
    upper = _norm(status).upper()
    return any(token in upper for token in BLOCKING_STATUS_TOKENS)


def _status_is_replay(status: str) -> bool:
    upper = _norm(status).upper()
    return any(token in upper for token in REPLAY_STATUS_TOKENS)


def _metric(value: int | float, *, source_field: str) -> dict[str, Any]:
    numeric = float(value)
    return {
        "sum": numeric,
        "count": 1,
        "mean": numeric,
        "positive_rows": 1 if numeric > 0 else 0,
        "negative_rows": 1 if numeric < 0 else 0,
        "zero_rows": 1 if numeric == 0 else 0,
        "match_rows_with_metric": 1,
        "source_field": source_field,
        "source_shape": "scid_noapi_source_repair",
    }


def _base_runtime_row(
    *,
    unit: dict[str, Any],
    source_path: Path,
    source_line_no: int,
    payload: dict[str, Any],
    row_suffix: str,
    source_component: str,
    primitive: str,
    status: str,
    source_acquisition_required: bool,
    replay_only: bool,
    missing_field: str = "",
) -> dict[str, Any]:
    symbol, source_symbol = _symbol_from_payload(payload)
    route_session = _session_from_payload(payload)
    has_source_scope = bool(symbol and route_session and source_acquisition_required)
    event_scope = (
        {
            "symbol": symbol,
            "source_symbol": source_symbol or symbol,
            "market": symbol,
            "symbol_family": resolve_vnext_symbol_family(symbol),
            "timeframe": "M15",
            "market_timeframe": "M15",
            "route_session": route_session,
            "horizon_id": "scid_noapi_source_repair",
            "primitive": primitive,
            "route_family": "source_discovery",
            "source_component": source_component,
        }
        if has_source_scope
        else {}
    )
    r_evidence_class = (
        "SCID_NOAPI_REPLAY_ATTRIBUTION_ONLY"
        if replay_only
        else (
            "SCID_NOAPI_FORBIDDEN_SURFACE_GUARD"
            if source_component == "scid_noapi_forbidden_surface_guard"
            else "SCID_NOAPI_SOURCE_ACQUISITION_REQUIRED"
        )
    )
    source_role = (
        "scid_noapi_replay_attribution_guard"
        if replay_only
        else "scid_noapi_source_acquisition_guard"
    )
    source_group = (
        "scid_noapi_replay_attribution_only"
        if replay_only
        else "scid_noapi_source_acquisition_required"
    )
    row_id = f"SCID_NOAPI_SOURCE_REPAIR_RUNTIME_{len(row_suffix) % 100000:05d}_{_sha256_text(row_suffix)[:12]}"
    row = {
        "schema_version": "gtos_vnext_scid_noapi_source_repair_runtime_row_v1",
        "wave_id": WAVE_ID,
        "batch_wave_id": WAVE_ID,
        "scid_noapi_source_repair_runtime_row_id": row_id,
        "row_key": _sha256_text(f"{_path_text(source_path)}|{source_line_no}|{row_suffix}"),
        "unit_id": unit.get("unit_id"),
        "source_row_id": _norm(
            payload.get("field_closure_row_hash")
            or payload.get("card_id")
            or payload.get("candidate_input_row_id")
            or payload.get("packet_id")
            or row_suffix
        ),
        "source_line_no": source_line_no,
        "source_artifact_path": _path_text(source_path),
        "source_path": _path_text(source_path),
        "source_artifact_sha256": _sha256_file(source_path),
        "source_artifact_hash": unit.get("source_artifact_hash") or _sha256_file(source_path),
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "system_surface": RUNTIME_SURFACE,
        "decision": "MIXED",
        "review_action": "MIXED_SOURCE_ACQUISITION_GUARD" if source_acquisition_required else "MIXED_REPLAY_ATTRIBUTION_ONLY",
        "runtime_decision_effect": bool(source_acquisition_required and has_source_scope),
        "runtime_effect_now": (
            "scid_noapi_source_acquisition_risk_guard"
            if source_acquisition_required
            else "scid_noapi_replay_attribution_only"
        ),
        "source_component": source_component,
        "source_group": source_group,
        "source_role": source_role,
        "action_family": "source_acquisition_guard" if source_acquisition_required else "replay_attribution",
        "action_class": "scid_noapi_source_acquisition_guard" if source_acquisition_required else "scid_noapi_replay_attribution_only",
        "r_evidence_class": r_evidence_class,
        "proxy_r_class": "SOURCE_ACQUISITION_REQUIRED" if source_acquisition_required else "REPLAY_ATTRIBUTION_ONLY",
        "target_stop_order_class": "SOURCE_ACQUISITION_REQUIRED" if source_acquisition_required else "",
        "event_scope": event_scope,
        "symbol": event_scope.get("symbol", ""),
        "source_symbol": event_scope.get("source_symbol", ""),
        "market": event_scope.get("market", ""),
        "symbol_family": event_scope.get("symbol_family", ""),
        "timeframe": event_scope.get("timeframe", ""),
        "market_timeframe": event_scope.get("market_timeframe", ""),
        "route_session": event_scope.get("route_session", ""),
        "horizon_id": event_scope.get("horizon_id", ""),
        "primitive": primitive,
        "route_family": event_scope.get("route_family", ""),
        "side": "",
        "field_name": missing_field or primitive,
        "field_status": status,
        "terminal_status": _norm(payload.get("terminal_status")),
        "accepted_readiness": _norm(payload.get("accepted_readiness")),
        "exact_next_source_control_route": _norm(payload.get("exact_next_source_control_route")),
        "future_result_gate": _norm(payload.get("future_result_gate")),
        "mechanism_family": _norm(payload.get("mechanism_family")),
        "science_domain": _norm(payload.get("science_domain")),
        "card_id": _norm(payload.get("card_id")),
        "candidate_input_row_id": _norm(payload.get("candidate_input_row_id")),
        "duplicate_proxy_denominator_key": _norm(payload.get("duplicate_proxy_denominator_key")),
        "source_proxy_group": _norm(payload.get("source_proxy_group")),
        "source_complete": False if source_acquisition_required else True,
        "source_bound": bool(has_source_scope),
        "source_acquisition_required": source_acquisition_required,
        "source_repair_required": source_acquisition_required,
        "candidate_use_allowed_now": False,
        "runtime_candidate_use_permitted": False,
        "broker_operation_permitted": False,
        "broker_operation": False,
        "opens_broker_account_order_history_deal_position_evidence": bool(
            payload.get("opens_broker_account_order_history_deal_position_evidence")
        ),
        "opens_paid_or_vendor_access": bool(payload.get("opens_paid_or_vendor_access")),
        "opens_ai_api": bool(payload.get("opens_ai_api")),
        "live_effect": False,
        "runtime_trading_or_live_broker_effect": False,
        "production_change_opened_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "source_event_rows": 1,
        "selected_source_unit_row_count": unit.get("row_count"),
        "r_metrics": {
            "proxy_score": _metric(0.0, source_field="source_acquisition_guard"),
            "effective_n": _metric(1.0, source_field="source_row"),
        },
    }
    return row


def _payload_status_entries(payload: dict[str, Any], *, path_text: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    statuses = payload.get("field_statuses")
    if isinstance(statuses, dict):
        for field_name, status_payload in statuses.items():
            status = ""
            if isinstance(status_payload, dict):
                status = _norm(status_payload.get("status") or status_payload.get("source_truth_class"))
            else:
                status = _norm(status_payload)
            if status:
                entries.append((_norm(field_name), status))
    for key in ("unavailable_fields_blocking_result_design", "exact_missing_fields_or_source_status"):
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                field = _norm(item)
                if field:
                    entries.append((field, "MISSING_SOURCE_FIELD"))
    for key in ("required_capture_groups", "future_capture_groups_required", "source_groups_required_for_packet_design"):
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                field = _norm(item)
                if field:
                    entries.append((field, "SOURCE_CAPTURE_GROUP_REQUIRED"))
    for key in ("accepted_readiness", "terminal_status", "status"):
        value = _norm(payload.get(key))
        if value and _status_is_blocking(value):
            entries.append((key, value))
    if not entries and "strategy_field" in path_text.casefold():
        entries.append(("strategy_field_source_expansion", "SOURCE_STATE_REPLAY_ATTRIBUTION"))
    if not entries:
        entries.append(("replay_attribution", _norm(payload.get("terminal_status") or payload.get("accepted_readiness") or "REPLAY_ATTRIBUTION_ONLY")))
    return entries


def _rows_from_payload(
    *,
    unit: dict[str, Any],
    source_path: Path,
    source_line_no: int,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    path_text = _path_text(source_path)
    rows: list[dict[str, Any]] = []
    for entry_index, (field_name, status) in enumerate(_payload_status_entries(payload, path_text=path_text), start=1):
        blocking = _status_is_blocking(status)
        replay_only = not blocking or _status_is_replay(status)
        component = _source_component(field_name, status=status, path_text=path_text)
        if replay_only and component != "scid_noapi_descriptor_control_replay_attribution":
            component = "scid_noapi_replay_attribution_only"
        rows.append(
            _base_runtime_row(
                unit=unit,
                source_path=source_path,
                source_line_no=source_line_no,
                payload=payload,
                row_suffix=f"{unit.get('unit_id')}:{source_line_no}:{entry_index}:{field_name}:{status}",
                source_component=component,
                primitive=_norm(field_name) or "scid_noapi_source_repair",
                status=status,
                source_acquisition_required=blocking,
                replay_only=not blocking,
                missing_field=_norm(field_name),
            )
        )
    return rows


def build_runtime_rows(units: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    runtime_rows: list[dict[str, Any]] = []
    stats: dict[str, dict[str, Any]] = {}
    for unit in sorted(units, key=lambda item: _norm(item.get("unit_id"))):
        path_text = _norm(unit.get("source_artifact_path"))
        if not path_text:
            continue
        source_path = _source_path(path_text)
        row_count, known = _source_row_count(source_path)
        stat = {
            "path": _path_text(source_path),
            "unit_id": unit.get("unit_id"),
            "rows": row_count if row_count is not None else unit.get("row_count"),
            "row_count_known": known or unit.get("row_count") is not None,
            "runtime_rows_read": 0,
            "sha256_or_git_blob": _sha256_file(source_path) or unit.get("source_artifact_hash") or "",
            "source_role": "supporting_evidence" if _is_support_unit(path_text) else "candidate_source_repair_evidence",
        }
        stats[path_text] = stat
        if _is_support_unit(path_text) or not source_path.exists() or not source_path.is_file():
            continue
        suffix = source_path.suffix.casefold()
        try:
            if suffix == ".jsonl":
                for line_no, payload in _iter_jsonl(source_path):
                    rows = _rows_from_payload(
                        unit=unit,
                        source_path=source_path,
                        source_line_no=line_no,
                        payload=payload,
                    )
                    runtime_rows.extend(rows)
                    stat["runtime_rows_read"] += len(rows)
            elif suffix == ".json":
                payload = _read_json_file(source_path)
                payloads = payload if isinstance(payload, list) else [payload]
                for line_no, item in enumerate(payloads, start=1):
                    if isinstance(item, dict):
                        rows = _rows_from_payload(
                            unit=unit,
                            source_path=source_path,
                            source_line_no=line_no,
                            payload=item,
                        )
                        runtime_rows.extend(rows)
                        stat["runtime_rows_read"] += len(rows)
        except (OSError, json.JSONDecodeError):
            stat["source_role"] = "supporting_evidence_unparsed"
    return runtime_rows, stats


def _dimension_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field)))
    return dict(sorted(counts.items()))


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def summarize(units: list[dict[str, Any]], runtime_rows: list[dict[str, Any]], stats: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_artifacts = sorted(stats.values(), key=lambda item: (str(item.get("unit_id")), item.get("path", "")))
    source_rows_counted = 0
    unknown = 0
    for item in source_artifacts:
        rows = item.get("rows")
        if isinstance(rows, int):
            source_rows_counted += rows
        else:
            unknown += 1
    runtime_paths = {row.get("source_artifact_path") for row in runtime_rows}
    converted_units = {
        item.get("unit_id")
        for item in source_artifacts
        if item.get("path") in runtime_paths and int(item.get("runtime_rows_read") or 0) > 0
    }
    coverage = {
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
    }
    return {
        "schema_version": "gtos_vnext_scid_noapi_source_repair_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "source_artifacts": source_artifacts,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "selected_source_unit_count": len(units),
        "converted_source_unit_count": len(converted_units),
        "support_or_killed_source_unit_count": len(units) - len(converted_units),
        "wave_source_artifact_count": len(source_artifacts),
        "wave_source_rows_counted": source_rows_counted,
        "row_count_unknown_unit_count": unknown,
        "runtime_row_count": len(runtime_rows),
        "runtime_source_rows_represented": source_rows_counted,
        "runtime_rows_with_event_scope": sum(1 for row in runtime_rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in runtime_rows if not row.get("event_scope")),
        "source_acquisition_required_rows": sum(1 for row in runtime_rows if row.get("source_acquisition_required")),
        "source_repair_required_rows": sum(1 for row in runtime_rows if row.get("source_repair_required")),
        "replay_attribution_rows": sum(
            1 for row in runtime_rows if row.get("r_evidence_class") == "SCID_NOAPI_REPLAY_ATTRIBUTION_ONLY"
        ),
        "runtime_candidate_use_permitted_rows": sum(
            1 for row in runtime_rows if row.get("runtime_candidate_use_permitted")
        ),
        "candidate_use_allowed_now_rows": sum(
            1 for row in runtime_rows if row.get("candidate_use_allowed_now")
        ),
        "broker_operation_permitted_rows": sum(
            1 for row in runtime_rows if row.get("broker_operation_permitted")
        ),
        "broker_operation_rows": sum(1 for row in runtime_rows if row.get("broker_operation")),
        "paid_api_or_vendor_call_rows": sum(
            1 for row in runtime_rows if row.get("opens_paid_or_vendor_access")
        ),
        "runtime_trading_or_live_broker_effect_rows": sum(
            1 for row in runtime_rows if row.get("runtime_trading_or_live_broker_effect")
        ),
        "decision_counts": _dimension_counts(runtime_rows, "decision"),
        "r_evidence_class_counts": _dimension_counts(runtime_rows, "r_evidence_class"),
        "source_component_counts": _dimension_counts(runtime_rows, "source_component"),
        "source_role_counts": _dimension_counts(runtime_rows, "source_role"),
        "source_group_counts": _dimension_counts(runtime_rows, "source_group"),
        "action_class_counts": _dimension_counts(runtime_rows, "action_class"),
        "field_status_counts": _dimension_counts(runtime_rows, "field_status"),
        "blank_anchor_counts": _blank_anchor_counts(runtime_rows),
        "coverage_counts": coverage,
        "row_id_samples": [
            row.get("scid_noapi_source_repair_runtime_row_id")
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

    units = _read_batch_source_units()
    runtime_rows, stats = build_runtime_rows(units)
    summary = summarize(units, runtime_rows, stats)
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
