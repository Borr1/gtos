#!/usr/bin/env python3
"""Build runtime rows for SCID target-horizon/control execution evidence."""

from __future__ import annotations

import os
import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_SCID_TARGET_HORIZON_CONTROL_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_scid_target_horizon_control"
SOURCE_NAME = "gtos_vnext_scid_target_horizon_control_wave"
RUNTIME_SURFACE = "scid_target_horizon_control_runtime"

BUILDER_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
OUTPUT_ROWS = (
    BUILDER_DIR
    / f"GTOS_VNEXT_SCID_TARGET_HORIZON_CONTROL_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    BUILDER_DIR
    / f"GTOS_VNEXT_SCID_TARGET_HORIZON_CONTROL_RUNTIME_SUMMARY_{DATE}.json"
)
MASTER_LEDGER = BUILDER_DIR / f"GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_LEDGER_{DATE}.jsonl"
BATCH_LEDGER = BUILDER_DIR / f"GTOS_VNEXT_BATCH_RUNTIME_CONVERSION_LEDGER_{DATE}.jsonl"

SOURCE_WAVE_IDS = (
    "WAVE_EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME",
    WAVE_ID,
)
SOURCE_SELECTION_TOKENS = (
    "g0_scid_neutral_target_control_synthesis",
    "g0_scid_noapi_ready8_target_result",
    "ready8_target_result",
    "g12_scid_asof_target_horizon_repair",
    "target_horizon",
    "neutral_target",
    "quarantined_target",
    "sealed_validation_execution_packet",
)
OUTPUT_NAMES = {
    OUTPUT_ROWS.name,
    OUTPUT_SUMMARY.name,
    Path(__file__).name,
}

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
    "target_stop_order_class",
    "source_component",
    "action_class",
)

SYMBOL_ALIASES = {
    "6B": "GBPUSD",
    "GBPJPY_6B": "GBPJPY",
    "GBPUSD_6B": "GBPUSD",
    "NAS100_NQ": "NAS100",
    "NAS100_NQ_FUTURES_PROXY": "NAS100",
    "NQ": "NAS100",
    "US30_YM": "US30",
    "US30_YM_FUTURES_PROXY": "US30",
    "YM": "US30",
    "USDJPY_6J": "USDJPY",
    "USDJPY_6J_FUTURES_PROXY": "USDJPY",
    "6J": "USDJPY",
    "XAGUSD_SI": "XAGUSD",
    "XAGUSD_SILVER_FUTURES_PROXY": "XAGUSD",
    "SI": "XAGUSD",
    "XAUUSD_GC": "XAUUSD",
    "XAUUSD_GC_FUTURES_PROXY": "XAUUSD",
    "GC": "XAUUSD",
}
KNOWN_SYMBOL_TOKENS = tuple(sorted(SYMBOL_ALIASES, key=len, reverse=True))


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
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
    return _sha256_file_cached(str(path))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _path_text(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _read_json(path: Path) -> Any:
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
    if not path.exists():
        return None, False
    suffix = path.suffix.casefold()
    if suffix == ".jsonl":
        return sum(1 for _line_no, _row in _iter_jsonl(path)), True
    if suffix == ".json":
        payload = _read_json(path)
        if isinstance(payload, list):
            return len(payload), True
        return 1, True
    if suffix in {".md", ".txt"}:
        with open(_long_path(path), "rb") as handle:
            return sum(1 for line in handle if line.strip()), True
    return None, False


def _source_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _matches_source_family(path_text: str) -> bool:
    normalized = path_text.casefold().replace("\\", "/")
    if Path(normalized).name in {name.casefold() for name in OUTPUT_NAMES}:
        return False
    return any(token in normalized for token in SOURCE_SELECTION_TOKENS)


def _read_batch_source_units() -> list[dict[str, Any]]:
    units: dict[str, dict[str, Any]] = {}
    if BATCH_LEDGER.exists():
        for line in BATCH_LEDGER.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            wave = json.loads(line)
            if wave.get("wave_id") not in SOURCE_WAVE_IDS:
                continue
            for item in wave.get("unit_dispositions", []):
                path_text = _norm(item.get("source_artifact_path"))
                unit_id = _norm(item.get("unit_id"))
                if path_text and unit_id and _matches_source_family(path_text):
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
            if path_text and unit_id and _matches_source_family(path_text):
                units[unit_id] = {
                    "unit_id": unit_id,
                    "source_artifact_path": path_text,
                    "source_artifact_hash": row.get("source_artifact_hash"),
                    "row_count": row.get("row_count"),
                }
    return list(units.values())


def _metric(value: float | int | None, *, source_field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    numeric = float(value)
    return {
        "sum": round(numeric, 12),
        "count": 1,
        "mean": round(numeric, 12),
        "positive_rows": 1 if numeric > 0 else 0,
        "negative_rows": 1 if numeric < 0 else 0,
        "zero_rows": 1 if numeric == 0 else 0,
        "match_rows_with_metric": 1,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _effective_n(count: int | float | None, *, source_field: str) -> dict[str, Any]:
    return _metric(count if count is not None else 1, source_field=source_field) or {}


def _canonical_symbol(symbol: str) -> str:
    token = _norm(symbol).upper()
    if token in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[token]
    if token.endswith("_FUTURES_PROXY"):
        token = token.removesuffix("_FUTURES_PROXY")
        return SYMBOL_ALIASES.get(token, token)
    return token


def _canonical_session(value: str) -> str:
    text = _norm(value).upper()
    if not text:
        return ""
    if "TOKYO" in text or "ASIA" in text or "UTC_00_05" in text:
        return "tokyo_kz"
    if "LONDON" in text or "UTC_06_11" in text or "UTC_07" in text:
        return "london_core"
    if "NEW_YORK" in text or "UTC_12_17" in text or "UTC_13" in text:
        return "ny_core"
    return "ALL_SESSIONS"


def _extract_binding_scope(row: dict[str, Any]) -> dict[str, str]:
    values = row.get("source_binding_values")
    if not isinstance(values, list):
        values = []
    strings = [_norm(item) for item in values if _norm(item)]

    source_symbol = ""
    if len(strings) > 8 and strings[8].upper() in SYMBOL_ALIASES:
        source_symbol = strings[8].upper()
    if not source_symbol and len(strings) > 9:
        candidate = strings[9].upper().split("::", 1)[0]
        if candidate in SYMBOL_ALIASES:
            source_symbol = candidate
    if not source_symbol:
        for value in strings:
            upper = value.upper()
            if upper.startswith("CANDIDATE_INPUT:"):
                candidate = upper.split(":", 2)[1].split("::", 1)[0]
                if candidate in SYMBOL_ALIASES:
                    source_symbol = candidate
                    break
            if "::" in upper:
                candidate = upper.split("::", 1)[0]
                if candidate in SYMBOL_ALIASES:
                    source_symbol = candidate
                    break
            if upper in SYMBOL_ALIASES:
                source_symbol = upper
                break

    session = ""
    if len(strings) > 10:
        session = _canonical_session(strings[10])
    if not session:
        for value in strings:
            upper = value.upper()
            if (
                upper.startswith(("ASIA_", "LONDON_", "NEW_YORK_", "GLOBAL_OFF_"))
                or upper.startswith("UTC_")
            ):
                session = _canonical_session(upper)
                if session:
                    break

    symbol = _canonical_symbol(source_symbol) if source_symbol else ""
    return {
        "symbol": symbol,
        "source_symbol": source_symbol,
        "market": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
        "route_session": session,
    }


def _horizon_id(value: Any) -> str:
    text = _norm(value)
    if not text:
        return ""
    try:
        return f"M15_BARS_{int(float(text))}"
    except ValueError:
        return text


def _target_family(row: dict[str, Any]) -> str:
    return _norm(row.get("target_family_id") or row.get("target_family") or row.get("target_id"))


def _base_row(
    *,
    source_path: Path,
    source_line_no: int,
    source_payload: dict[str, Any],
    row_suffix: str,
    decision: str,
    source_component: str,
    source_group: str,
    source_role: str,
    action_class: str,
    r_evidence_class: str,
    proxy_r_class: str,
    target_stop_order_class: str,
    runtime_effect_now: str,
    effective_n: dict[str, Any],
    scope: dict[str, str] | None = None,
    source_bound: bool = False,
    source_complete: bool = False,
    runtime_decision_effect: bool = False,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scope = dict(scope or {})
    row_id = f"scid_target_horizon_control:{row_suffix}"
    event_scope = {
        key: value
        for key, value in {
            "symbol": scope.get("symbol", ""),
            "source_symbol": scope.get("source_symbol", ""),
            "market": scope.get("market", ""),
            "symbol_family": scope.get("symbol_family", ""),
            "timeframe": "M15",
            "market_timeframe": "M15",
            "route_session": scope.get("route_session", ""),
            "horizon_id": scope.get("horizon_id", ""),
            "side": scope.get("side", ""),
            "framework": scope.get("framework", ""),
            "route_family": scope.get("route_family", "scid_target_control"),
            "source_component": source_component,
            "action_class": action_class,
            "target_stop_order_class": target_stop_order_class,
        }.items()
        if value not in (None, "")
    }
    row = {
        "schema_version": "gtos_vnext_scid_target_horizon_control_runtime_v1",
        "scid_target_horizon_control_runtime_row_id": row_id,
        "row_key": _sha256_text(f"{_path_text(source_path)}|{source_line_no}|{row_suffix}"),
        "source_row_id": _norm(source_payload.get("row_id") or source_payload.get("candidate_id") or row_suffix),
        "source_line_no": source_line_no,
        "source_artifact_path": _path_text(source_path),
        "source_path": _path_text(source_path),
        "source_artifact_sha256": _sha256_file(source_path),
        "source_name": SOURCE_NAME,
        "batch_wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "system_surface": RUNTIME_SURFACE,
        "decision": decision,
        "review_action": decision,
        "runtime_decision_effect": runtime_decision_effect,
        "runtime_effect_now": runtime_effect_now,
        "source_component": source_component,
        "source_group": source_group,
        "source_role": source_role,
        "action_class": action_class,
        "r_evidence_class": r_evidence_class,
        "proxy_r_class": proxy_r_class,
        "target_stop_order_class": target_stop_order_class,
        "event_scope": event_scope,
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_family": event_scope.get("route_family", "scid_target_control"),
        "framework": event_scope.get("framework", ""),
        "horizon_id": event_scope.get("horizon_id", ""),
        "symbol": event_scope.get("symbol", ""),
        "source_symbol": event_scope.get("source_symbol", ""),
        "market": event_scope.get("market", ""),
        "symbol_family": event_scope.get("symbol_family", ""),
        "route_session": event_scope.get("route_session", ""),
        "side": event_scope.get("side", ""),
        "source_bound": source_bound,
        "source_complete": source_complete,
        "orderflow_runtime_validated": True,
        "source_transfer_validated": True,
        "effective_n": effective_n,
        "r_metrics": {"effective_n": effective_n},
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "gate_config_change_now": False,
        "production_change_opened_now": False,
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "target_family_id": _target_family(source_payload),
        "card_id": _norm(source_payload.get("card_id")),
        "classification": _norm(source_payload.get("classification")),
        "promotion_verdict": _norm(source_payload.get("promotion_verdict")),
        "artifact_family": _norm(source_payload.get("artifact_family")),
    }
    if extra:
        row.update({key: value for key, value in extra.items() if value not in (None, "")})
    return row


def _candidate_example_rows(source_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, payload in _iter_jsonl(source_path):
        scope = _extract_binding_scope(payload)
        target_bindings = payload.get("target_binding_values")
        horizons = []
        if isinstance(target_bindings, list):
            for item in target_bindings:
                if isinstance(item, list) and len(item) > 1:
                    horizon = _horizon_id(item[1])
                    if horizon:
                        horizons.append(horizon)
        scope["horizon_id"] = "M15_BARS_MIXED_" + "_".join(
            sorted({h.removeprefix("M15_BARS_") for h in horizons})
        ) if horizons else ""

        status_counts = payload.get("status_counts") if isinstance(payload.get("status_counts"), dict) else {}
        fail_closed = payload.get("fail_closed_primary_reason_counts")
        fail_closed_count = sum(int(value or 0) for value in fail_closed.values()) if isinstance(fail_closed, dict) else 0
        status_total = sum(int(value or 0) for value in status_counts.values()) if status_counts else 1
        if fail_closed_count:
            behavior = {
                "decision": "MIXED",
                "source_component": "scid_target_horizon_fail_closed_source_repair",
                "source_group": "source_repair_proof",
                "source_role": "scid_target_horizon_fail_closed_source_repair_guard",
                "action_class": "source_repair_guard",
                "r_evidence_class": "SOURCE_REPAIR_FOR_EXACT_R",
                "proxy_r_class": "SOURCE_REPAIR_REQUIRED",
                "target_stop_order_class": "SOURCE_REPAIR_REQUIRED",
                "runtime_effect_now": "scid_target_horizon_source_repair_risk_guard",
                "runtime_decision_effect": True,
                "source_bound": bool(scope.get("symbol") or scope.get("route_session")),
                "source_complete": False,
            }
        else:
            behavior = {
                "decision": "MIXED",
                "source_component": "scid_neutral_target_candidate_context",
                "source_group": "context_guard_input",
                "source_role": "scid_neutral_target_candidate_context_guard",
                "action_class": "context_guard_input",
                "r_evidence_class": "SCID_NEUTRAL_TARGET_CANDIDATE_CONTEXT",
                "proxy_r_class": "MIXED_NEUTRAL_PROXY",
                "target_stop_order_class": "NEUTRAL_TARGET_CONTROL_CONTEXT",
                "runtime_effect_now": "scid_neutral_target_candidate_context",
                "runtime_decision_effect": False,
                "source_bound": bool(scope.get("symbol") or scope.get("route_session")),
                "source_complete": True,
            }
        rows.append(
            _base_row(
                source_path=source_path,
                source_line_no=line_no,
                source_payload=payload,
                row_suffix=f"candidate:{line_no:05d}",
                effective_n=_effective_n(status_total, source_field="status_counts"),
                scope=scope,
                extra={
                    "status_counts": status_counts,
                    "fail_closed_primary_reason_counts": fail_closed if isinstance(fail_closed, dict) else {},
                    "example_selection_rule": _norm(payload.get("example_selection_rule")),
                    "duplicate_proxy_denominator_key": _norm(payload.get("duplicate_proxy_denominator_key")),
                    "max_absolute_close_to_close_percent_return": payload.get("max_absolute_close_to_close_percent_return"),
                    "max_high_low_total_excursion_percent": payload.get("max_high_low_total_excursion_percent"),
                },
                **behavior,
            )
        )
    return rows


def _matrix_rows(source_path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    matrix_rows = payload.get("rows")
    if not isinstance(matrix_rows, list):
        return rows
    for index, item in enumerate(matrix_rows, start=1):
        if not isinstance(item, dict):
            continue
        classification = _norm(item.get("classification")).upper()
        fail_closed_share = _safe_float(item.get("fail_closed_share")) or 0.0
        computable_rows = int(item.get("computable_rows") or 0)
        fail_closed_rows = int(item.get("fail_closed_rows") or 0)
        total = computable_rows + fail_closed_rows or 1
        horizon = _horizon_id(item.get("horizon_m15_bars"))
        scope = {"horizon_id": horizon}
        if "NON_DISCRIMINATIVE" in classification or "KILL_FAST" in classification or fail_closed_share >= 0.5:
            behavior = {
                "decision": "AVOID",
                "source_component": "scid_target_control_card_rank_non_discriminative",
                "source_group": "scid_target_control_avoid_filter",
                "source_role": "scid_target_control_card_rank_avoid_guard",
                "action_class": "scid_target_control_card_rank_avoid_filter",
                "r_evidence_class": "SCID_TARGET_CONTROL_NON_DISCRIMINATIVE_AVOID",
                "proxy_r_class": "NEGATIVE_PROXY_R",
                "target_stop_order_class": "CARD_LEVEL_NON_DISCRIMINATIVE",
                "runtime_effect_now": "scid_target_control_card_rank_avoid_risk_guard",
                "runtime_decision_effect": True,
                "source_bound": bool(horizon),
                "source_complete": True,
            }
        else:
            behavior = {
                "decision": "MIXED",
                "source_component": "scid_target_control_matrix_context",
                "source_group": "context_guard_input",
                "source_role": "scid_target_control_matrix_context_guard",
                "action_class": "context_guard_input",
                "r_evidence_class": "SCID_TARGET_CONTROL_MATRIX_CONTEXT",
                "proxy_r_class": "MIXED_NEUTRAL_PROXY",
                "target_stop_order_class": "NEUTRAL_TARGET_CONTROL_CONTEXT",
                "runtime_effect_now": "scid_target_control_matrix_context",
                "runtime_decision_effect": False,
                "source_bound": bool(horizon),
                "source_complete": True,
            }
        rows.append(
            _base_row(
                source_path=source_path,
                source_line_no=index,
                source_payload=item,
                row_suffix=f"matrix:{index:05d}",
                effective_n=_effective_n(total, source_field="computable_plus_fail_closed_rows"),
                scope=scope,
                extra={
                    "computable_rows": computable_rows,
                    "fail_closed_rows": fail_closed_rows,
                    "fail_closed_share": fail_closed_share,
                    "direction_positive_share": item.get("direction_positive_share"),
                    "direction_negative_share": item.get("direction_negative_share"),
                },
                **behavior,
            )
        )
    return rows


def _negative_ledger_rows(source_path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sources = (
        ("baseline_delta_rows", "baseline_delta"),
        ("card_horizon_family_negative_evidence_complete", "card_negative"),
        ("partition_negative_evidence_complete_by_explicit_rules", "partition_negative"),
        ("kill_fast_conclusions", "kill_fast"),
    )
    line_no = 0
    for key, suffix in sources:
        values = payload.get(key)
        if not isinstance(values, list):
            continue
        for item in values:
            if not isinstance(item, dict):
                continue
            line_no += 1
            scope = {"horizon_id": _horizon_id(item.get("horizon_m15_bars"))}
            rows.append(
                _base_row(
                    source_path=source_path,
                    source_line_no=line_no,
                    source_payload=item,
                    row_suffix=f"{suffix}:{line_no:05d}",
                    decision="AVOID",
                    source_component="scid_target_control_card_rank_non_discriminative",
                    source_group="scid_target_control_avoid_filter",
                    source_role="scid_target_control_card_rank_avoid_guard",
                    action_class="scid_target_control_card_rank_avoid_filter",
                    r_evidence_class="SCID_TARGET_CONTROL_NON_DISCRIMINATIVE_AVOID",
                    proxy_r_class="NEGATIVE_PROXY_R",
                    target_stop_order_class="CARD_LEVEL_NON_DISCRIMINATIVE",
                    runtime_effect_now="scid_target_control_card_rank_avoid_risk_guard",
                    effective_n=_effective_n(
                        item.get("computable_rows")
                        or item.get("unique_duplicate_proxy_denominator_keys")
                        or 1,
                        source_field=key,
                    ),
                    scope=scope,
                    source_bound=bool(scope.get("horizon_id")),
                    source_complete=True,
                    runtime_decision_effect=True,
                    extra={
                        "negative_or_kill_fast_reasons": item.get("negative_or_kill_fast_reasons", []),
                        "partition_field": _norm(item.get("partition_field")),
                        "partition_value": _norm(item.get("partition_value")),
                        "finding": _norm(item.get("finding")),
                    },
                )
            )
    return rows


def _neutral_behavior_rows(source_path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    line_no = 0
    for item in payload.get("availability_by_target_family_and_horizon", []) or []:
        if not isinstance(item, dict):
            continue
        line_no += 1
        not_computable = int(item.get("not_computable_count") or 0)
        behavior = {
            "decision": "MIXED",
            "source_component": "scid_target_horizon_fail_closed_source_repair" if not_computable else "scid_neutral_target_control_context",
            "source_group": "source_repair_proof" if not_computable else "context_guard_input",
            "source_role": "scid_target_horizon_fail_closed_source_repair_guard" if not_computable else "scid_neutral_target_control_context_guard",
            "action_class": "source_repair_guard" if not_computable else "context_guard_input",
            "r_evidence_class": "SOURCE_REPAIR_FOR_EXACT_R" if not_computable else "SCID_NEUTRAL_TARGET_CONTROL_CONTEXT",
            "proxy_r_class": "SOURCE_REPAIR_REQUIRED" if not_computable else "MIXED_NEUTRAL_PROXY",
            "target_stop_order_class": "SOURCE_REPAIR_REQUIRED" if not_computable else "NEUTRAL_TARGET_CONTROL_CONTEXT",
            "runtime_effect_now": "scid_target_horizon_source_repair_risk_guard" if not_computable else "scid_neutral_target_control_context",
            "runtime_decision_effect": bool(not_computable),
            "source_bound": bool(item.get("horizon_m15_bars")),
            "source_complete": not bool(not_computable),
        }
        rows.append(
            _base_row(
                source_path=source_path,
                source_line_no=line_no,
                source_payload=item,
                row_suffix=f"availability:{line_no:05d}",
                effective_n=_effective_n(
                    int(item.get("computable_count") or 0) + not_computable,
                    source_field="computable_plus_not_computable_count",
                ),
                scope={"horizon_id": _horizon_id(item.get("horizon_m15_bars"))},
                extra={
                    "computable_count": item.get("computable_count"),
                    "not_computable_count": not_computable,
                    "primary_not_computable_reasons": item.get("primary_not_computable_reasons", {}),
                },
                **behavior,
            )
        )
    for item in payload.get("notable_neutral_descriptor_slices_from_packet", []) or []:
        if not isinstance(item, dict):
            continue
        line_no += 1
        slice_payload = item.get("high_slice") if isinstance(item.get("high_slice"), dict) else {}
        session = _canonical_session(_norm(slice_payload.get("descriptor_buckets.session_bucket")))
        rows.append(
            _base_row(
                source_path=source_path,
                source_line_no=line_no,
                source_payload=item,
                row_suffix=f"neutral_slice:{line_no:05d}",
                decision="MIXED",
                source_component="scid_neutral_target_control_context",
                source_group="context_guard_input",
                source_role="scid_neutral_target_control_context_guard",
                action_class="context_guard_input",
                r_evidence_class="SCID_NEUTRAL_TARGET_CONTROL_CONTEXT",
                proxy_r_class="MIXED_NEUTRAL_PROXY",
                target_stop_order_class="NEUTRAL_TARGET_CONTROL_CONTEXT",
                runtime_effect_now="scid_neutral_target_control_context",
                effective_n=_effective_n(1, source_field="neutral_descriptor_slice"),
                scope={"route_session": session},
                source_bound=bool(session),
                source_complete=True,
                runtime_decision_effect=False,
                extra={"diagnostic_type": _norm(item.get("diagnostic_type"))},
            )
        )
    return rows


def _failure_anatomy_rows(source_path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    line_no = 0
    sources = (
        ("by_family_horizon_reason", "family_horizon_reason"),
        ("by_reason_symbol", "reason_symbol"),
    )
    for key, suffix in sources:
        values = payload.get(key)
        if not isinstance(values, list):
            continue
        for item in values:
            if not isinstance(item, dict):
                continue
            line_no += 1
            symbol = _canonical_symbol(_norm(item.get("symbol"))) if item.get("symbol") else ""
            rows.append(
                _base_row(
                    source_path=source_path,
                    source_line_no=line_no,
                    source_payload=item,
                    row_suffix=f"{suffix}:{line_no:05d}",
                    decision="MIXED",
                    source_component="scid_target_horizon_fail_closed_source_repair",
                    source_group="source_repair_proof",
                    source_role="scid_target_horizon_fail_closed_source_repair_guard",
                    action_class="source_repair_guard",
                    r_evidence_class="SOURCE_REPAIR_FOR_EXACT_R",
                    proxy_r_class="SOURCE_REPAIR_REQUIRED",
                    target_stop_order_class="SOURCE_REPAIR_REQUIRED",
                    runtime_effect_now="scid_target_horizon_source_repair_risk_guard",
                    effective_n=_effective_n(item.get("count") or 1, source_field=key),
                    scope={
                        "symbol": symbol,
                        "source_symbol": _norm(item.get("symbol")),
                        "market": symbol,
                        "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
                        "horizon_id": _horizon_id(item.get("horizon_m15_bars")),
                    },
                    source_bound=bool(symbol or item.get("horizon_m15_bars")),
                    source_complete=False,
                    runtime_decision_effect=True,
                    extra={"reason": _norm(item.get("reason"))},
                )
            )
    for text in payload.get("source_control_expansion_needs", []) or []:
        line_no += 1
        item = {"requirement": text}
        rows.append(
            _base_row(
                source_path=source_path,
                source_line_no=line_no,
                source_payload=item,
                row_suffix=f"source_need:{line_no:05d}",
                decision="MIXED",
                source_component="scid_target_horizon_source_field_requirement",
                source_group="source_repair_proof",
                source_role="scid_target_horizon_source_field_requirement_guard",
                action_class="source_repair_guard",
                r_evidence_class="SOURCE_REPAIR_FOR_EXACT_R",
                proxy_r_class="SOURCE_REPAIR_REQUIRED",
                target_stop_order_class="SOURCE_REPAIR_REQUIRED",
                runtime_effect_now="scid_target_horizon_source_repair_risk_guard",
                effective_n=_effective_n(1, source_field="source_control_expansion_needs"),
                source_bound=False,
                source_complete=False,
                runtime_decision_effect=True,
                extra={"requirement": _norm(text)},
            )
        )
    return rows


def _source_field_requirement_rows(source_path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(payload.get("required_fields", []) or [], start=1):
        if not isinstance(item, dict):
            continue
        rows.append(
            _base_row(
                source_path=source_path,
                source_line_no=index,
                source_payload=item,
                row_suffix=f"required_field:{index:05d}",
                decision="MIXED",
                source_component="scid_target_horizon_source_field_requirement",
                source_group="source_repair_proof",
                source_role="scid_target_horizon_source_field_requirement_guard",
                action_class="source_repair_guard",
                r_evidence_class="SOURCE_REPAIR_FOR_EXACT_R",
                proxy_r_class="SOURCE_REPAIR_REQUIRED",
                target_stop_order_class="SOURCE_REPAIR_REQUIRED",
                runtime_effect_now="scid_target_horizon_source_repair_risk_guard",
                effective_n=_effective_n(1, source_field="required_fields"),
                source_bound=False,
                source_complete=False,
                runtime_decision_effect=True,
                extra={
                    "field_group": _norm(item.get("field_group")),
                    "needed_for": _norm(item.get("needed_for")),
                    "next_route_status": _norm(item.get("next_route_status")),
                    "status_now": _norm(item.get("status_now")),
                },
            )
        )
    return rows


def _target_horizon_repair_rows(source_path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    status_by_family = payload.get("status_by_family")
    if isinstance(status_by_family, dict):
        for index, (family, status) in enumerate(sorted(status_by_family.items()), start=1):
            framework = family if family in {"ob_retest", "fvg_fill", "breaker_re_entry"} else ""
            rows.append(
                _base_row(
                    source_path=source_path,
                    source_line_no=index,
                    source_payload={
                        "target_family_id": family,
                        "classification": status,
                    },
                    row_suffix=f"family_status:{index:05d}",
                    decision="MIXED",
                    source_component="scid_target_horizon_neutral_only",
                    source_group="source_repair_proof",
                    source_role="scid_target_horizon_neutral_only_guard",
                    action_class="source_repair_guard",
                    r_evidence_class="SOURCE_REPAIR_FOR_EXACT_R",
                    proxy_r_class="SOURCE_REPAIR_REQUIRED",
                    target_stop_order_class="TARGET_HORIZON_NEUTRAL_ONLY",
                    runtime_effect_now="scid_target_horizon_source_repair_risk_guard",
                    effective_n=_effective_n(1, source_field="status_by_family"),
                    scope={
                        "framework": framework,
                        "route_family": framework or "scid_target_control",
                    },
                    source_bound=bool(framework),
                    source_complete=False,
                    runtime_decision_effect=True,
                    extra={"family_status": _norm(status)},
                )
            )
    if isinstance(payload.get("actual_counts"), dict):
        total = sum(int(value or 0) for value in payload["actual_counts"].values() if isinstance(value, int))
        rows.append(
            _base_row(
                source_path=source_path,
                source_line_no=len(rows) + 1,
                source_payload=payload,
                row_suffix="count_reconciliation",
                decision="MIXED",
                source_component="scid_target_horizon_source_field_requirement",
                source_group="source_repair_proof",
                source_role="scid_target_horizon_source_field_requirement_guard",
                action_class="source_repair_guard",
                r_evidence_class="SOURCE_REPAIR_FOR_EXACT_R",
                proxy_r_class="SOURCE_REPAIR_REQUIRED",
                target_stop_order_class="SOURCE_REPAIR_REQUIRED",
                runtime_effect_now="scid_target_horizon_source_repair_risk_guard",
                effective_n=_effective_n(total or 1, source_field="actual_counts"),
                source_bound=False,
                source_complete=False,
                runtime_decision_effect=True,
                extra={"actual_counts": payload.get("actual_counts", {})},
            )
        )
    return rows


def _generic_control_row(source_path: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not payload:
        return []
    artifact_family = _norm(payload.get("artifact_family"))
    if not artifact_family:
        return []
    text = " ".join(
        _norm(payload.get(field))
        for field in (
            "terminal_decision",
            "accepted_g12_decision",
            "promotion_verdict",
            "rank_1_blocker_statement",
            "failure_boundary",
        )
    )
    needs_repair = any(token in text.upper() for token in ("MISSING", "REPAIR", "BLOCKED", "NO_PROMOTION"))
    return [
        _base_row(
            source_path=source_path,
            source_line_no=1,
            source_payload=payload,
            row_suffix=f"generic:{_sha256_text(artifact_family)[:12]}",
            decision="MIXED",
            source_component="scid_target_horizon_source_field_requirement" if needs_repair else "scid_neutral_target_control_context",
            source_group="source_repair_proof" if needs_repair else "context_guard_input",
            source_role="scid_target_horizon_source_field_requirement_guard" if needs_repair else "scid_neutral_target_control_context_guard",
            action_class="source_repair_guard" if needs_repair else "context_guard_input",
            r_evidence_class="SOURCE_REPAIR_FOR_EXACT_R" if needs_repair else "SCID_NEUTRAL_TARGET_CONTROL_CONTEXT",
            proxy_r_class="SOURCE_REPAIR_REQUIRED" if needs_repair else "MIXED_NEUTRAL_PROXY",
            target_stop_order_class="SOURCE_REPAIR_REQUIRED" if needs_repair else "NEUTRAL_TARGET_CONTROL_CONTEXT",
            runtime_effect_now="scid_target_horizon_source_repair_risk_guard" if needs_repair else "scid_neutral_target_control_context",
            effective_n=_effective_n(1, source_field="generic_control_artifact"),
            source_bound=False,
            source_complete=not needs_repair,
            runtime_decision_effect=needs_repair,
            extra={"control_text": text[:500]},
        )
    ]


def _rows_for_source(source_path: Path) -> list[dict[str, Any]]:
    name = source_path.name
    if name == "G0_SCID_READY8_CANDIDATE_EXAMPLE_LEDGER_2026-05-13.jsonl":
        return _candidate_example_rows(source_path)
    if source_path.suffix.casefold() != ".json":
        return []
    payload = _read_json(source_path)
    if not isinstance(payload, dict):
        return []
    rows: list[dict[str, Any]] = []
    if name == "G0_SCID_READY8_CARD_HORIZON_TARGET_FAMILY_MATRIX_2026-05-13.json":
        rows.extend(_matrix_rows(source_path, payload))
    if name == "G0_SCID_READY8_NEGATIVE_EVIDENCE_AND_KILL_FAST_LEDGER_2026-05-13.json":
        rows.extend(_negative_ledger_rows(source_path, payload))
    if name == "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_NEUTRAL_BEHAVIOR_SYNTHESIS_2026-05-12.json":
        rows.extend(_neutral_behavior_rows(source_path, payload))
    if name == "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_NOT_COMPUTABLE_FAILURE_ANATOMY_SYNTHESIS_2026-05-12.json":
        rows.extend(_failure_anatomy_rows(source_path, payload))
    if name == "G0_SCID_NEUTRAL_TARGET_SYNTHESIS_FUTURE_SOURCE_FIELD_REQUIREMENT_LEDGER_2026-05-12.json":
        rows.extend(_source_field_requirement_rows(source_path, payload))
    if "TARGET_HORIZON_REPAIR_AUDIT" in name:
        rows.extend(_target_horizon_repair_rows(source_path, payload))
    if rows:
        return rows
    return _generic_control_row(source_path, payload)


def build_runtime_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    units = _read_batch_source_units()
    rows: list[dict[str, Any]] = []
    source_artifacts: list[dict[str, Any]] = []
    rows_by_path: Counter[str] = Counter()
    decision_by_path: dict[str, Counter[str]] = defaultdict(Counter)
    components_by_path: dict[str, Counter[str]] = defaultdict(Counter)

    for unit in units:
        path_text = _norm(unit.get("source_artifact_path"))
        if not path_text:
            continue
        path = _source_path(path_text)
        if not path.exists():
            source_artifacts.append(
                {
                    "unit_id": unit.get("unit_id"),
                    "path": path_text,
                    "rows": unit.get("row_count"),
                    "row_count_known": unit.get("row_count") is not None,
                    "runtime_rows_read": 0,
                    "missing": True,
                }
            )
            continue
        source_rows, row_count_known = _source_row_count(path)
        runtime_rows = _rows_for_source(path)
        for row in runtime_rows:
            rows_by_path[_path_text(path)] += 1
            decision_by_path[_path_text(path)][row["decision"]] += 1
            components_by_path[_path_text(path)][row["source_component"]] += 1
        rows.extend(runtime_rows)
        source_artifacts.append(
            {
                "unit_id": unit.get("unit_id"),
                "path": _path_text(path),
                "rows": source_rows,
                "row_count_known": row_count_known,
                "runtime_rows_read": len(runtime_rows),
                "sha256_or_git_blob": _sha256_file(path),
                "source_components": sorted(components_by_path[_path_text(path)]),
                "decision_counts": dict(sorted(decision_by_path[_path_text(path)].items())),
            }
        )

    coverage = _coverage(rows)
    summary = {
        "schema_version": "gtos_vnext_scid_target_horizon_control_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "runtime_surface": RUNTIME_SURFACE,
        "selected_source_unit_count": len(units),
        "wave_source_artifact_count": len(source_artifacts),
        "wave_source_rows_counted": sum(int(item.get("rows") or 0) for item in source_artifacts),
        "row_count_unknown_unit_count": sum(1 for item in source_artifacts if not item.get("row_count_known")),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": len(rows),
        "decision_counts": dict(sorted(Counter(row["decision"] for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(row["source_component"] for row in rows).items())),
        "source_group_counts": dict(sorted(Counter(row["source_group"] for row in rows).items())),
        "source_role_counts": dict(sorted(Counter(row["source_role"] for row in rows).items())),
        "action_class_counts": dict(sorted(Counter(row["action_class"] for row in rows).items())),
        "r_evidence_class_counts": dict(sorted(Counter(row["r_evidence_class"] for row in rows).items())),
        "proxy_r_class_counts": dict(sorted(Counter(row["proxy_r_class"] for row in rows).items())),
        "target_stop_order_class_counts": dict(sorted(Counter(row["target_stop_order_class"] for row in rows).items())),
        "source_repair_required_rows": sum(1 for row in rows if row["r_evidence_class"] == "SOURCE_REPAIR_FOR_EXACT_R"),
        "avoid_veto_rows": sum(1 for row in rows if row["decision"] == "AVOID"),
        "context_rows": sum(1 for row in rows if row["decision"] == "MIXED" and row["r_evidence_class"] != "SOURCE_REPAIR_FOR_EXACT_R"),
        "runtime_candidate_use_permitted_rows": sum(1 for row in rows if row.get("runtime_candidate_use_permitted")),
        "candidate_use_allowed_now_rows": sum(1 for row in rows if row.get("candidate_use_allowed_now")),
        "live_effect_rows": sum(1 for row in rows if row.get("live_effect")),
        "broker_operation_rows": sum(1 for row in rows if row.get("broker_operation")),
        "paid_api_or_vendor_call_rows": sum(1 for row in rows if row.get("paid_api_or_vendor_call")),
        "runtime_trading_or_live_broker_effect_rows": sum(1 for row in rows if row.get("runtime_trading_or_live_broker_effect")),
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "coverage_counts": coverage,
        "source_artifacts": source_artifacts,
    }
    return rows, summary


def _coverage(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    fields = {
        "symbols": "symbol",
        "source_symbols": "source_symbol",
        "markets": "market",
        "timeframes": "timeframe",
        "market_timeframes": "market_timeframe",
        "sessions": "route_session",
        "horizons": "horizon_id",
        "sides": "side",
        "frameworks": "framework",
        "target_stop_order_classes": "target_stop_order_class",
        "source_components": "source_component",
        "action_classes": "action_class",
    }
    coverage: dict[str, dict[str, int]] = {}
    for output_key, field_name in fields.items():
        counts = Counter(_norm(row.get(field_name)) for row in rows if _norm(row.get(field_name)))
        coverage[output_key] = dict(sorted(counts.items()))
    return coverage


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for field in ANCHOR_FIELDS:
        blank = sum(1 for row in rows if not _norm(row.get(field)))
        if blank:
            counts[field] = blank
    return counts


def write_outputs() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows, summary = build_runtime_rows()
    OUTPUT_ROWS.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return rows, summary


def _check_outputs() -> int:
    rows, summary = build_runtime_rows()
    expected_rows = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )
    expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    mismatches = []
    if not OUTPUT_ROWS.exists() or OUTPUT_ROWS.read_text(encoding="utf-8") != expected_rows:
        mismatches.append(str(OUTPUT_ROWS))
    if not OUTPUT_SUMMARY.exists() or OUTPUT_SUMMARY.read_text(encoding="utf-8") != expected_summary:
        mismatches.append(str(OUTPUT_SUMMARY))
    if mismatches:
        print("Output mismatch:", ", ".join(mismatches), file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        return _check_outputs()
    rows, summary = write_outputs()
    print(json.dumps({
        "rows": len(rows),
        "summary": str(OUTPUT_SUMMARY),
        "blank_anchor_counts": summary["blank_anchor_counts"],
        "coverage_counts": summary["coverage_counts"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
