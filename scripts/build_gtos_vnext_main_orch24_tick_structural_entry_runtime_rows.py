#!/usr/bin/env python3
"""Build runtime rows for Main Orch24 tick/source/entry repair evidence."""

from __future__ import annotations

import os
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
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
SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
DATE = "2026-05-18"
WAVE_ID = "WAVE_MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_main_orch24_tick_structural_entry_runtime"
SOURCE_NAME = "gtos_vnext_main_orch24_tick_structural_entry_runtime_wave"
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME_SUMMARY_{DATE}.json"
)

ACTION_SOURCE = "MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_LEDGER_2026-05-17.jsonl"
ENTRY_SOURCE = "MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_LEDGER_2026-05-16.jsonl"
REGISTRY_SOURCE = "MAIN_ORCH24_STRATEGY_REGISTRY_AFTER_TICK_STRUCTURAL_REPAIR_LEDGER_2026-05-17.jsonl"
TICK_STRUCTURAL_SOURCE = "MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR_LEDGER_2026-05-17.jsonl"

SOURCE_ARTIFACTS = (
    ("UNIT_009527", ACTION_SOURCE, "0cd63e45d6bc5b1b12e007e1dd67e7d68c5fd314"),
    (
        "UNIT_009528",
        "MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_OUTPUT_MANIFEST_2026-05-17.json",
        "812f7a7b3e0bd43d8da3cad41118171377b69d51",
    ),
    (
        "UNIT_009529",
        "MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_SUMMARY_2026-05-17.json",
        "5dfab47285e8acd7117b11696b3a71b58bedb62c",
    ),
    (
        "UNIT_009530",
        "MAIN_ORCH24_ACTION_AFTER_NAS100_TICK_ORDER_REPAIR_VERIFICATION_RESULT_2026-05-17.json",
        "c45304aaada663127603f9844e24474d260eb6ac",
    ),
    ("UNIT_009649", ENTRY_SOURCE, "5a22b62b73eb2f5bff802ab91b44d71b0685ce2a"),
    (
        "UNIT_009650",
        "MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_OUTPUT_MANIFEST_2026-05-16.json",
        "252963ae33add8f1ca573669e90d30d866f79e3d",
    ),
    (
        "UNIT_009651",
        "MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_SUMMARY_2026-05-16.json",
        "91c9d681cc073040134bb8da40be94d25e398632",
    ),
    (
        "UNIT_009652",
        "MAIN_ORCH24_ENTRY_REDESIGN_TICK_OFFSET_RECOMPUTE_VERIFICATION_RESULT_2026-05-16.json",
        "0f6e30bbb4d80f0a1bbc3402214289a74f81fe98",
    ),
    ("UNIT_009889", REGISTRY_SOURCE, "2222d41ecd3e93d905ae31e5c3ba6bd226830534"),
    (
        "UNIT_009890",
        "MAIN_ORCH24_STRATEGY_REGISTRY_AFTER_TICK_STRUCTURAL_REPAIR_OUTPUT_MANIFEST_2026-05-17.json",
        "3607ddd3bfeb045b0844e377f80c7cd01a98545d",
    ),
    (
        "UNIT_009891",
        "MAIN_ORCH24_STRATEGY_REGISTRY_AFTER_TICK_STRUCTURAL_REPAIR_SUMMARY_2026-05-17.json",
        "09d9251fab86d0e567afeb446777e4551eca2092",
    ),
    (
        "UNIT_009892",
        "MAIN_ORCH24_STRATEGY_REGISTRY_AFTER_TICK_STRUCTURAL_REPAIR_VERIFICATION_RESULT_2026-05-17.json",
        "90d709a5b1912294c6c0effae0f8a1cb3478e4d7",
    ),
    ("UNIT_009910", TICK_STRUCTURAL_SOURCE, "b4f59b06714ad5d37a6fc6a9f0cd16e5628a0787"),
    (
        "UNIT_009911",
        "MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR_OUTPUT_MANIFEST_2026-05-17.json",
        "c872bb87a978c9445ad1c678d397b31f8f96eaf2",
    ),
    (
        "UNIT_009912",
        "MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR_SUMMARY_2026-05-17.json",
        "9c66e661dda361c87e994c464d6f84398d5c9079",
    ),
    (
        "UNIT_009913",
        "MAIN_ORCH24_TICK_STRUCTURAL_SOURCE_DERIVATION_REPAIR_VERIFICATION_RESULT_2026-05-17.json",
        "be685976e2b809d2a72af53ef098e640e71dc368",
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


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _float(value: Any) -> float | None:
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


def _path_text(path: Path) -> str:
    try:
        if path.is_relative_to(REPO_ROOT):
            return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        pass
    return str(path).replace("\\", "/")


def _source_path(name: str) -> Path:
    return SOURCE_DIR / name


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(_long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    with open(_long_path(path), "r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(_long_path(path), "r", encoding="utf-8-sig", newline="") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _source_row_count(path: Path) -> int:
    if path.suffix.casefold() == ".jsonl":
        return len(_read_jsonl(path))
    return 1


def _metric(value: float | int | None, *, source_field: str, count: int = 1) -> dict[str, Any] | None:
    if value is None:
        return None
    value = float(value)
    return {
        "sum": round(value, 12),
        "count": count,
        "mean": round(value / count, 12) if count else round(value, 12),
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "match_rows_with_metric": count,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _candidate_session(candidate_id: Any) -> str:
    text = _norm(candidate_id)
    match = re.search(r"T(\d{2}):(\d{2})", text)
    if not match:
        return "ALL_SESSIONS"
    minute = int(match.group(1)) * 60 + int(match.group(2))
    if 0 <= minute < 180:
        return "tokyo_kz"
    if 420 <= minute < 720:
        return "london_core"
    if 780 <= minute < 1020:
        return "ny_core"
    return "off_core_session"


def _base_scope(
    *,
    symbol: str = "",
    side: str = "",
    route_session: str = "",
    route_family: str,
    primitive: str,
    source_component: str,
    entry_variant: str = "",
    target_stop_order_class: str = "",
) -> dict[str, str]:
    scope = {
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": route_session or "ALL_SESSIONS",
        "route_family": route_family,
        "primitive": primitive,
        "source_component": source_component,
    }
    if symbol:
        scope.update(
            {
                "symbol": symbol,
                "source_symbol": symbol,
                "market": symbol,
                "symbol_family": resolve_vnext_symbol_family(symbol),
            }
        )
    if side:
        scope["side"] = side
    if entry_variant:
        scope["entry_variant"] = entry_variant
    if target_stop_order_class:
        scope["target_stop_order_class"] = target_stop_order_class
    return {key: value for key, value in scope.items() if value}


def _runtime_row(
    *,
    row_id: str,
    source_path: Path,
    source_sha: str,
    source_line_no: int,
    source_row: dict[str, Any],
    source_kind: str,
    source_component: str,
    source_role: str,
    source_group: str,
    system_surface: str,
    action_class: str,
    review_action: str,
    r_evidence_class: str,
    proxy_r_class: str,
    event_scope: dict[str, str],
    metrics: dict[str, dict[str, Any]],
    **extra: Any,
) -> dict[str, Any]:
    runtime = {
        "schema_version": "gtos_vnext_main_orch24_tick_structural_entry_runtime_row_v1",
        "row_type": "gtos_vnext_main_orch24_tick_structural_entry_runtime_row",
        "main_orch24_tick_structural_entry_runtime_row_id": row_id,
        "row_key": row_id,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "source_kind": source_kind,
        "source_group": source_group,
        "source_role": source_role,
        "source_component": source_component,
        "system_surface": system_surface,
        "action_class": action_class,
        "review_action": review_action,
        "r_evidence_class": r_evidence_class,
        "proxy_r_class": proxy_r_class,
        "event_scope": event_scope,
        "source_bound": bool(event_scope),
        "candidate_use_allowed_now": review_action in {"FOLLOW", "AVOID"},
        "runtime_candidate_use_permitted": review_action in {"FOLLOW", "AVOID"},
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "runtime_effect_now": "main_orch24_tick_structural_entry_shadow_runtime",
        "batch_wave_id": WAVE_ID,
        "source_artifact": _path_text(source_path),
        "source_file_sha256": source_sha,
        "source_line_no": source_line_no,
        "source_row_id": source_row.get("row_id"),
        "candidate_id": source_row.get("candidate_id"),
        "source_payload_hash": _sha256_text(json.dumps(source_row, sort_keys=True)),
        "r_metrics": metrics,
    }
    runtime.update(event_scope)
    runtime.update(extra)
    return {key: value for key, value in runtime.items() if value not in (None, "", {}, [])}


def _action_behavior(row: dict[str, Any]) -> dict[str, str]:
    action_class = _norm(row.get("action_class")).upper()
    proxy = _float(row.get("after_proxy_r"))
    branch = _norm(row.get("branch_decision")).upper()
    if row.get("nas100_tick_order_repair_status") == "REPAIRED_FROM_LOCAL_TICK_PARQUET":
        return {
            "review_action": "FOLLOW",
            "source_component": "main_orch24_nas100_tick_order_repair_follow",
            "source_role": "nas100_tick_order_repaired_follow",
            "source_group": "main_orch24_tick_order_repair",
            "system_surface": "execution_adjacent_tick_order_repaired_follow",
            "action_class": "main_orch24_nas100_tick_order_repair_follow",
            "r_evidence_class": "MAIN_ORCH24_NAS100_TICK_ORDER_REPAIRED_POSITIVE_PROXY",
            "proxy_r_class": "POSITIVE_PROXY_R",
        }
    if action_class == "KILL":
        return {
            "review_action": "AVOID",
            "source_component": "main_orch24_tick_structural_kill_guard",
            "source_role": "tick_structural_kill_guard",
            "source_group": "main_orch24_tick_structural_avoid_filter",
            "system_surface": "execution_adjacent_tick_structural_guard",
            "action_class": "main_orch24_tick_structural_kill_avoid_filter",
            "r_evidence_class": "MAIN_ORCH24_TICK_STRUCTURAL_KILL_AVOID",
            "proxy_r_class": "NEGATIVE_PROXY_R",
        }
    if action_class == "PRESERVE_REQUIREMENT":
        return {
            "review_action": "MIXED",
            "source_component": "main_orch24_tick_preserve_source_acquisition",
            "source_role": "main_orch24_tick_source_acquisition_guard",
            "source_group": "main_orch24_tick_source_acquisition",
            "system_surface": "execution_adjacent_tick_source_acquisition",
            "action_class": "main_orch24_tick_preserve_requirement_context",
            "r_evidence_class": "MAIN_ORCH24_TICK_SOURCE_ACQUISITION_REQUIRED",
            "proxy_r_class": "MIXED_PROXY_R",
        }
    if action_class == "REDESIGN":
        return {
            "review_action": "MIXED",
            "source_component": "main_orch24_tick_redesign_source_repair",
            "source_role": "main_orch24_tick_redesign_source_repair_guard",
            "source_group": "main_orch24_tick_redesign_or_repair",
            "system_surface": "execution_adjacent_tick_structural_redesign",
            "action_class": "main_orch24_tick_redesign_context",
            "r_evidence_class": "MAIN_ORCH24_TICK_STRUCTURAL_REDESIGN_SOURCE_REPAIR_REQUIRED",
            "proxy_r_class": "MIXED_PROXY_R",
        }
    if proxy is not None and proxy < 0:
        return {
            "review_action": "AVOID",
            "source_component": "main_orch24_tick_negative_proxy_guard",
            "source_role": "main_orch24_tick_negative_proxy_guard",
            "source_group": "main_orch24_tick_negative_proxy_avoid_filter",
            "system_surface": "execution_adjacent_tick_proxy_guard",
            "action_class": "main_orch24_tick_negative_proxy_avoid_filter",
            "r_evidence_class": "MAIN_ORCH24_TICK_NEGATIVE_PROXY_AVOID",
            "proxy_r_class": "NEGATIVE_PROXY_R",
        }
    if proxy is not None and proxy > 0 and (
        action_class in {"KEEP", "IMPLEMENT_DEFAULT_OFF"} or "POSITIVE" in branch
    ):
        return {
            "review_action": "FOLLOW",
            "source_component": "main_orch24_tick_positive_proxy_follow",
            "source_role": "main_orch24_tick_positive_proxy_follow",
            "source_group": "main_orch24_tick_positive_proxy",
            "system_surface": "execution_adjacent_tick_structural_follow",
            "action_class": "main_orch24_tick_positive_proxy_follow",
            "r_evidence_class": "MAIN_ORCH24_TICK_POSITIVE_PROXY",
            "proxy_r_class": "POSITIVE_PROXY_R",
        }
    return {
        "review_action": "MIXED",
        "source_component": "main_orch24_tick_structural_context",
        "source_role": "main_orch24_tick_structural_context",
        "source_group": "main_orch24_tick_structural_context",
        "system_surface": "execution_adjacent_tick_structural_context",
        "action_class": "main_orch24_tick_structural_context",
        "r_evidence_class": "MAIN_ORCH24_TICK_STRUCTURAL_CONTEXT",
        "proxy_r_class": "MIXED_PROXY_R",
    }


def _entry_behavior(row: dict[str, Any]) -> tuple[dict[str, str], str, float | None]:
    impl = _norm(row.get("implementation_decision"))
    tick_status = _norm(row.get("tick_source_status"))
    shift_050 = row.get("offset_shift_outcomes", {}).get("0.5", {})
    proxy = _float(shift_050.get("proxy_r_delta_vs_original_no_fill"))
    if "BAD_PARQUET" in tick_status or impl == "SOURCE_REPAIR_REQUIRED_FOR_ENTRY_OFFSET_SCORER":
        return (
            {
                "review_action": "MIXED",
                "source_component": "main_orch24_entry_offset_tick_source_acquisition",
                "source_role": "main_orch24_entry_offset_tick_source_acquisition_guard",
                "source_group": "main_orch24_entry_offset_source_acquisition",
                "system_surface": "execution_adjacent_entry_offset_source_acquisition",
                "action_class": "main_orch24_entry_offset_source_acquisition_context",
                "r_evidence_class": "MAIN_ORCH24_ENTRY_OFFSET_TICK_SOURCE_ACQUISITION_REQUIRED",
                "proxy_r_class": "MIXED_PROXY_R",
            },
            "spread_aware_050r_offset",
            proxy,
        )
    if impl.startswith("KILL_025R"):
        return (
            {
                "review_action": "AVOID",
                "source_component": "main_orch24_entry_offset_025r_kill_guard",
                "source_role": "main_orch24_entry_offset_025r_kill_guard",
                "source_group": "main_orch24_entry_offset_025r_avoid_filter",
                "system_surface": "execution_adjacent_entry_offset_fillability_guard",
                "action_class": "main_orch24_entry_offset_025r_avoid_filter",
                "r_evidence_class": "MAIN_ORCH24_ENTRY_OFFSET_025R_KILL_AVOID",
                "proxy_r_class": "NEGATIVE_PROXY_R",
            },
            "spread_aware_025r_offset",
            proxy,
        )
    return (
        {
            "review_action": "FOLLOW",
            "source_component": "main_orch24_entry_offset_050r_challenger",
            "source_role": "main_orch24_entry_offset_050r_challenger_follow",
            "source_group": "main_orch24_entry_offset_050r_challenger",
            "system_surface": "execution_adjacent_entry_offset_fillability_challenger",
            "action_class": "main_orch24_entry_offset_050r_challenger_follow",
            "r_evidence_class": "MAIN_ORCH24_ENTRY_OFFSET_050R_CHALLENGER_POSITIVE_PROXY",
            "proxy_r_class": "POSITIVE_PROXY_R",
        },
        "spread_aware_050r_offset",
        proxy,
    )


def _action_runtime_rows() -> list[dict[str, Any]]:
    path = _source_path(ACTION_SOURCE)
    source_sha = _sha256_file(path)
    runtime_rows: list[dict[str, Any]] = []
    for line_no, row in enumerate(_read_jsonl(path), start=1):
        behavior = _action_behavior(row)
        symbol = _norm(row.get("symbol"))
        primitive = _norm(row.get("primitive_family")) or _norm(row.get("strategy_id"))
        scope = _base_scope(
            symbol=symbol,
            side=_norm(row.get("side")),
            route_session=_candidate_session(row.get("candidate_id")),
            route_family="main_orch24_structural_runtime",
            primitive=primitive,
            source_component=behavior["source_component"],
            target_stop_order_class=(
                _norm(row.get("nas100_tick_order_terminal_event"))
                or (
                    "TP_BEFORE_SL_AFTER_ENTRY"
                    if row.get("nas100_tick_order_repair_status")
                    == "REPAIRED_FROM_LOCAL_TICK_PARQUET"
                    else ""
                )
            ),
        )
        proxy = _float(row.get("after_proxy_r"))
        metrics = {
            key: value
            for key, value in {
                "proxy_score": _metric(proxy, source_field="after_proxy_r"),
                "cost_adjusted_simulated_r": _metric(proxy, source_field="after_proxy_r"),
                "proxy_r_delta": _metric(_float(row.get("proxy_r_delta")), source_field="proxy_r_delta"),
            }.items()
            if value is not None
        }
        runtime_rows.append(
            _runtime_row(
                row_id=f"main_orch24:action:{line_no}:{_sha256_text(json.dumps(row, sort_keys=True))[:16]}",
                source_path=path,
                source_sha=source_sha,
                source_line_no=line_no,
                source_row=row,
                source_kind="main_orch24_action_after_tick_order_repair_row",
                event_scope=scope,
                metrics=metrics,
                action_class=behavior["action_class"],
                review_action=behavior["review_action"],
                r_evidence_class=behavior["r_evidence_class"],
                proxy_r_class=behavior["proxy_r_class"],
                source_component=behavior["source_component"],
                source_role=behavior["source_role"],
                source_group=behavior["source_group"],
                system_surface=behavior["system_surface"],
                original_action_class=row.get("action_class"),
                implementation_decision=row.get("implementation_decision"),
                branch_decision=row.get("branch_decision"),
                strategy_id=row.get("strategy_id"),
                source_capture_surface=row.get("source_capture_surface"),
                primitive_family=row.get("primitive_family"),
                after_proxy_r=proxy,
                before_proxy_r=_float(row.get("before_proxy_r")),
                nas100_tick_order_repair_status=row.get("nas100_tick_order_repair_status"),
            )
        )
    return runtime_rows


def _entry_runtime_rows() -> list[dict[str, Any]]:
    path = _source_path(ENTRY_SOURCE)
    source_sha = _sha256_file(path)
    runtime_rows: list[dict[str, Any]] = []
    for line_no, row in enumerate(_read_jsonl(path), start=1):
        bucket = _norm(row.get("entry_retest_redesign_bucket"))
        if bucket == "NOT_A_NO_FILL_TP1_ENTRY_REDESIGN_ROW":
            continue
        behavior, entry_variant, proxy = _entry_behavior(row)
        symbol = _norm(row.get("symbol") or row.get("broker_symbol"))
        scope = _base_scope(
            symbol=symbol,
            side=_norm(row.get("side")),
            route_session=_candidate_session(row.get("candidate_id")),
            route_family="main_orch24_entry_redesign",
            primitive=bucket,
            source_component=behavior["source_component"],
            entry_variant=entry_variant,
            target_stop_order_class=_norm(
                row.get("offset_shift_outcomes", {}).get("0.5", {}).get("outcome_status")
            ),
        )
        metrics = {
            key: value
            for key, value in {
                "proxy_score": _metric(proxy, source_field="offset_shift_outcomes.0.5.proxy_r_delta_vs_original_no_fill"),
                "cost_adjusted_simulated_r": _metric(proxy, source_field="offset_shift_outcomes.0.5.proxy_r_delta_vs_original_no_fill"),
                "minimum_spread_aware_shift_r": _metric(
                    _float(row.get("minimum_spread_aware_shift_r")),
                    source_field="minimum_spread_aware_shift_r",
                ),
            }.items()
            if value is not None
        }
        runtime_rows.append(
            _runtime_row(
                row_id=f"main_orch24:entry:{line_no}:{_sha256_text(json.dumps(row, sort_keys=True))[:16]}",
                source_path=path,
                source_sha=source_sha,
                source_line_no=line_no,
                source_row=row,
                source_kind="main_orch24_entry_redesign_tick_offset_row",
                event_scope=scope,
                metrics=metrics,
                action_class=behavior["action_class"],
                review_action=behavior["review_action"],
                r_evidence_class=behavior["r_evidence_class"],
                proxy_r_class=behavior["proxy_r_class"],
                source_component=behavior["source_component"],
                source_role=behavior["source_role"],
                source_group=behavior["source_group"],
                system_surface=behavior["system_surface"],
                entry_retest_redesign_bucket=bucket,
                entry_variant=entry_variant,
                implementation_decision=row.get("implementation_decision"),
                tick_source_status=row.get("tick_source_status"),
                minimum_spread_aware_shift_r=_float(row.get("minimum_spread_aware_shift_r")),
                selected_shift_proxy_r=proxy,
            )
        )
    return runtime_rows


def _registry_behavior(row: dict[str, Any]) -> dict[str, str]:
    strategy_id = _norm(row.get("strategy_id"))
    if strategy_id == "V2_STRUCT_SWING_PROTECTED":
        return {
            "review_action": "FOLLOW",
            "source_component": "main_orch24_swing_protected_tick_repair_follow",
            "source_role": "main_orch24_swing_protected_tick_repair_follow",
            "source_group": "main_orch24_swing_protected_tick_repair",
            "system_surface": "execution_adjacent_tick_structural_strategy_registry",
            "action_class": "main_orch24_swing_protected_default_off_follow",
            "r_evidence_class": "MAIN_ORCH24_SWING_PROTECTED_TICK_REPAIR_POSITIVE_PROXY",
            "proxy_r_class": "POSITIVE_PROXY_R",
        }
    return {
        "review_action": "AVOID",
        "source_component": "main_orch24_standalone_fvg_negative_guard",
        "source_role": "main_orch24_standalone_fvg_negative_guard",
        "source_group": "main_orch24_standalone_fvg_negative_avoid_filter",
        "system_surface": "execution_adjacent_tick_structural_strategy_registry",
        "action_class": "main_orch24_standalone_fvg_negative_avoid_filter",
        "r_evidence_class": "MAIN_ORCH24_STANDALONE_FVG_TICK_REPAIR_NEGATIVE_PROXY",
        "proxy_r_class": "NEGATIVE_PROXY_R",
    }


def _registry_runtime_rows() -> list[dict[str, Any]]:
    path = _source_path(REGISTRY_SOURCE)
    source_sha = _sha256_file(path)
    runtime_rows: list[dict[str, Any]] = []
    for line_no, row in enumerate(_read_jsonl(path), start=1):
        behavior = _registry_behavior(row)
        strategy_id = _norm(row.get("strategy_id"))
        scope = _base_scope(
            route_session="ALL_SESSIONS",
            route_family=_norm(row.get("family")) or "structural_selector",
            primitive=strategy_id,
            source_component=behavior["source_component"],
        )
        proxy_sum = _float(row.get("current_proxy_r_sum"))
        effective_n = int(row.get("current_numeric_proxy_rows") or 0)
        metrics = {
            key: value
            for key, value in {
                "proxy_score": _metric(proxy_sum, source_field="current_proxy_r_sum", count=max(1, effective_n)),
                "cost_adjusted_simulated_r": _metric(
                    proxy_sum,
                    source_field="current_proxy_r_sum",
                    count=max(1, effective_n),
                ),
                "effective_n": _metric(effective_n, source_field="current_numeric_proxy_rows"),
            }.items()
            if value is not None
        }
        runtime_rows.append(
            _runtime_row(
                row_id=f"main_orch24:strategy_registry:{line_no}:{strategy_id}",
                source_path=path,
                source_sha=source_sha,
                source_line_no=line_no,
                source_row=row,
                source_kind="main_orch24_strategy_registry_tick_structural_row",
                event_scope=scope,
                metrics=metrics,
                action_class=behavior["action_class"],
                review_action=behavior["review_action"],
                r_evidence_class=behavior["r_evidence_class"],
                proxy_r_class=behavior["proxy_r_class"],
                source_component=behavior["source_component"],
                source_role=behavior["source_role"],
                source_group=behavior["source_group"],
                system_surface=behavior["system_surface"],
                strategy_id=strategy_id,
                evidence_role=row.get("evidence_role"),
                branch_decision=row.get("branch_decision"),
                current_target_rows=int(row.get("current_target_rows") or 0),
                current_numeric_proxy_rows=effective_n,
                current_proxy_r_sum=proxy_sum,
            )
        )
    return runtime_rows


def build_rows() -> list[dict[str, Any]]:
    return _action_runtime_rows() + _entry_runtime_rows() + _registry_runtime_rows()


def _counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field))).items()))


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {field: sum(1 for row in rows if not _norm(row.get(field))) for field in ANCHOR_FIELDS}


def _source_artifacts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_rows_by_source = Counter(Path(row["source_artifact"]).name for row in rows)
    artifacts: list[dict[str, Any]] = []
    for unit_id, name, git_blob_hash in SOURCE_ARTIFACTS:
        path = _source_path(name)
        role = "supporting_evidence"
        if name in {ACTION_SOURCE, ENTRY_SOURCE, REGISTRY_SOURCE}:
            role = "primary_runtime_rows"
        elif name == TICK_STRUCTURAL_SOURCE:
            role = "upstream_tick_structural_source_repair"
        artifacts.append(
            {
                "unit_id": unit_id,
                "name": name,
                "path": _path_text(path),
                "hash": git_blob_hash,
                "hash_algorithm": "git_blob",
                "sha256": _sha256_file(path),
                "row_count": _source_row_count(path),
                "runtime_rows_read": int(runtime_rows_by_source.get(name, 0)),
                "source_role": role,
            }
        )
    return artifacts


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    artifacts = _source_artifacts(rows)
    coverage = {
        "symbols": _counter(rows, "symbol"),
        "source_symbols": _counter(rows, "source_symbol"),
        "markets": _counter(rows, "market"),
        "timeframes": _counter(rows, "timeframe"),
        "sessions": _counter(rows, "route_session"),
        "route_families": _counter(rows, "route_family"),
        "primitives": _counter(rows, "primitive"),
        "sides": _counter(rows, "side"),
        "entry_variants": _counter(rows, "entry_variant"),
        "target_stop_order_classes": _counter(rows, "target_stop_order_class"),
        "source_components": _counter(rows, "source_component"),
        "action_classes": _counter(rows, "action_class"),
        "source_roles": _counter(rows, "source_role"),
        "source_groups": _counter(rows, "source_group"),
        "system_surfaces": _counter(rows, "system_surface"),
    }
    source_acquisition_required_rows = sum(
        1
        for row in rows
        if row.get("r_evidence_class")
        in {
            "MAIN_ORCH24_TICK_SOURCE_ACQUISITION_REQUIRED",
            "MAIN_ORCH24_ENTRY_OFFSET_TICK_SOURCE_ACQUISITION_REQUIRED",
        }
    )
    return {
        "schema_version": "gtos_vnext_main_orch24_tick_structural_entry_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(rows),
        "runtime_rows_with_event_scope": sum(1 for row in rows if row.get("event_scope")),
        "runtime_rows_without_event_scope": sum(1 for row in rows if not row.get("event_scope")),
        "runtime_source_rows_represented": sum(
            int(item["runtime_rows_read"]) for item in artifacts
        ),
        "wave_source_rows_counted": sum(int(item["row_count"]) for item in artifacts),
        "support_rows_represented": sum(
            int(item["row_count"]) for item in artifacts if item["source_role"] != "primary_runtime_rows"
        ),
        "selected_open_unit_count": len(SOURCE_ARTIFACTS),
        "row_count_unknown_unit_count": 0,
        "source_acquisition_required_rows": source_acquisition_required_rows,
        "decision_counts": _counter(rows, "review_action"),
        "r_evidence_class_counts": _counter(rows, "r_evidence_class"),
        "action_class_counts": _counter(rows, "action_class"),
        "source_component_counts": _counter(rows, "source_component"),
        "source_role_counts": _counter(rows, "source_role"),
        "source_group_counts": _counter(rows, "source_group"),
        "source_kind_counts": _counter(rows, "source_kind"),
        "system_surface_counts": _counter(rows, "system_surface"),
        "proxy_r_class_counts": _counter(rows, "proxy_r_class"),
        "coverage_counts": coverage,
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "source_artifacts": artifacts,
        "proxy_score_sum": round(
            sum(float(row.get("r_metrics", {}).get("proxy_score", {}).get("sum") or 0.0) for row in rows),
            12,
        ),
        "runtime_effect": (
            "Main Orch24 tick/source/entry repair rows become vNext shadow route, "
            "risk, source-acquisition, and entry-redesign evidence."
        ),
    }


def _jsonl_text(rows: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)


def _json_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROWS.write_text(_jsonl_text(rows), encoding="utf-8")
    OUTPUT_SUMMARY.write_text(_json_text(summary), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows = build_rows()
    summary = build_summary(rows)
    rows_text = _jsonl_text(rows)
    summary_text = _json_text(summary)
    if args.check:
        mismatches = []
        if not OUTPUT_ROWS.exists() or OUTPUT_ROWS.read_text(encoding="utf-8") != rows_text:
            mismatches.append(_path_text(OUTPUT_ROWS))
        if not OUTPUT_SUMMARY.exists() or OUTPUT_SUMMARY.read_text(encoding="utf-8") != summary_text:
            mismatches.append(_path_text(OUTPUT_SUMMARY))
        if mismatches:
            print(json.dumps({"ok": False, "mismatched_outputs": mismatches}, indent=2, sort_keys=True))
            return 1
        print("Main Orch24 tick structural/entry runtime outputs are current")
        return 0
    write_outputs(rows, summary)
    print(
        json.dumps(
            {
                "ok": True,
                "runtime_row_count": len(rows),
                "runtime_rows_path": _path_text(OUTPUT_ROWS),
                "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
