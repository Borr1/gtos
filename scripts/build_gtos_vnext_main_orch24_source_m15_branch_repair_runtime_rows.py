#!/usr/bin/env python3
"""Build runtime rows for Main Orch24 source/M15 branch-repair evidence."""

from __future__ import annotations

import os
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

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_MAIN_ORCH24_SOURCE_M15_BRANCH_REPAIR_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_main_orch24_source_m15_branch_repair_runtime"
SOURCE_NAME = "gtos_vnext_main_orch24_source_m15_branch_repair_runtime_wave"

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
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_SOURCE_M15_BRANCH_REPAIR_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_SOURCE_M15_BRANCH_REPAIR_RUNTIME_SUMMARY_{DATE}.json"
)

ACTION_AFTER_SRC_ENTRY_M15 = (
    "MAIN_ORCH24_ACTION_AFTER_SRC_ENTRY_M15_REPAIRS_LEDGER_2026-05-16.jsonl"
)
IMPLEMENTATION_ACTION_AFTER_SOURCE_M15 = (
    "MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_M15_REPAIR_LEDGER_2026-05-16.jsonl"
)
SOURCE_M15_ORDERING_REPAIR = (
    "MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_LEDGER_2026-05-16.jsonl"
)
SOURCE_UPGRADED_BRANCH_DECISION = (
    "MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_LEDGER_2026-05-16.jsonl"
)

SOURCE_ARTIFACTS: tuple[tuple[str, str, str], ...] = (
    (
        "UNIT_009358",
        "build_main_orchestrator_action_after_source_and_entry_m15_repairs_2026_05_16.py",
        "762d1f98a008bb7ad40f15f88e717608a30c4348",
    ),
    (
        "UNIT_009387",
        "build_main_orchestrator_implementation_action_after_source_m15_repair_2026_05_16.py",
        "9f7cf6bcdabfd61abbcf8b0f795ccca562810a14",
    ),
    (
        "UNIT_009473",
        "build_main_orchestrator_source_implication_branch_decisions_2026_05_16.py",
        "ca6b0e1df88be6b1dba79e7895f74aabce954b32",
    ),
    (
        "UNIT_009474",
        "build_main_orchestrator_source_m15_ordering_repair_2026_05_16.py",
        "02e0f2a99c95239b28431ea12725abf95694fc81",
    ),
    ("UNIT_009595", ACTION_AFTER_SRC_ENTRY_M15, "374c664c977a0e9c6b4348fe8830f36844401a84"),
    (
        "UNIT_009596",
        "MAIN_ORCH24_ACTION_AFTER_SRC_ENTRY_M15_REPAIRS_OUTPUT_MANIFEST_2026-05-16.json",
        "cfad71f1410be3b485e86ace63a0f4094ea85483",
    ),
    (
        "UNIT_009597",
        "MAIN_ORCH24_ACTION_AFTER_SRC_ENTRY_M15_REPAIRS_SUMMARY_2026-05-16.json",
        "cd3db46a8c2206c31f80d8006e5c13fe43106fa8",
    ),
    (
        "UNIT_009598",
        "MAIN_ORCH24_ACTION_AFTER_SRC_ENTRY_M15_REPAIRS_VERIFICATION_RESULT_2026-05-16.json",
        "fece11296f36a5d0c9ba0954e350a65dcb09c269",
    ),
    (
        "UNIT_009696",
        IMPLEMENTATION_ACTION_AFTER_SOURCE_M15,
        "d374d72899efcf12ff1b97833876520fbaf89189",
    ),
    (
        "UNIT_009697",
        "MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_M15_REPAIR_OUTPUT_MANIFEST_2026-05-16.json",
        "2fa9a210dbbe652c9138e21bc298eea6a4875211",
    ),
    (
        "UNIT_009698",
        "MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_M15_REPAIR_SUMMARY_2026-05-16.json",
        "fb11c56eba11600eaa9253e7dfabf075e34ca0ad",
    ),
    (
        "UNIT_009699",
        "MAIN_ORCH24_IMPLEMENTATION_ACTION_AFTER_SOURCE_M15_REPAIR_VERIFICATION_RESULT_2026-05-16.json",
        "1a43a94012e6026894b436df035bdb1e2425a3eb",
    ),
    ("UNIT_009879", SOURCE_M15_ORDERING_REPAIR, "6eea687074e201cc71ad81310757612d926e2b8e"),
    (
        "UNIT_009880",
        "MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_OUTPUT_MANIFEST_2026-05-16.json",
        "9ea8c88787e71bf91e5f6f95f6816c3fadd89a31",
    ),
    (
        "UNIT_009881",
        "MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_SUMMARY_2026-05-16.json",
        "249a7e4cc1c060f6f4f05c71dd616bd2a51cefd7",
    ),
    (
        "UNIT_009882",
        "MAIN_ORCH24_SOURCE_M15_ORDERING_REPAIR_VERIFICATION_RESULT_2026-05-16.json",
        "0cd3886c52adf8fb25824540a11058bf2a3e2cd5",
    ),
    (
        "UNIT_009887",
        SOURCE_UPGRADED_BRANCH_DECISION,
        "f3f8bd0f3ec78b15c6637d384fd705de12c415e2",
    ),
    (
        "UNIT_009888",
        "MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_OUTPUT_MANIFEST_2026-05-16.json",
        "12aefbe184f7a5c07e08d6fe3ca1412b03fbad46",
    ),
    (
        "UNIT_009889",
        "MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_SUMMARY_2026-05-16.json",
        "dea3cef193442e36ee2755bf13161592d931a86d",
    ),
    (
        "UNIT_009890",
        "MAIN_ORCH24_SOURCE_UPGRADED_DEGRADED_BRANCH_DECISION_VERIFICATION_RESULT_2026-05-16.json",
        "19cfa135f0816e39a34e85e2dd9722d874d89fa1",
    ),
    (
        "UNIT_010284",
        "verify_main_orchestrator_action_after_source_and_entry_m15_repairs_2026_05_16.py",
        "81facaceb8a9969eed01690b32885dab86c634d9",
    ),
    (
        "UNIT_010313",
        "verify_main_orchestrator_implementation_action_after_source_m15_repair_2026_05_16.py",
        "6de7348a706ec63ca20d516bb7372e817c3f7dea",
    ),
    (
        "UNIT_010399",
        "verify_main_orchestrator_source_implication_branch_decisions_2026_05_16.py",
        "949708c65ce0c8feacbe7523969fc8e55b245196",
    ),
    (
        "UNIT_010400",
        "verify_main_orchestrator_source_m15_ordering_repair_2026_05_16.py",
        "eb115b78376dfbbeedcd23e860327c73485a3a93",
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
    "source_component",
    "entry_variant",
    "target_stop_order_class",
)


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


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _upper(value: Any) -> str:
    return _norm(value).upper()


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(_long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


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
    suffix = path.suffix.casefold()
    if suffix == ".jsonl":
        return len(_read_jsonl(path))
    if suffix == ".json":
        return 1
    if suffix in {".py", ".md"}:
        return sum(
            1
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.strip()
        )
    return 1


def _metric(value: float | int | None, *, source_field: str) -> dict[str, Any]:
    if value is None:
        return {
            "sum": None,
            "count": 0,
            "mean": None,
            "min": None,
            "max": None,
            "positive_rows": 0,
            "negative_rows": 0,
            "zero_rows": 0,
            "match_rows_with_metric": 0,
            "source_field": source_field,
            "source_shape": "missing",
        }
    fvalue = float(value)
    return {
        "sum": fvalue,
        "count": 1,
        "mean": fvalue,
        "min": fvalue,
        "max": fvalue,
        "positive_rows": 1 if fvalue > 0 else 0,
        "negative_rows": 1 if fvalue < 0 else 0,
        "zero_rows": 1 if fvalue == 0 else 0,
        "match_rows_with_metric": 1,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _session(value: Any) -> str:
    raw = _norm(value).casefold()
    return {
        "ny": "ny_core",
        "new_york": "ny_core",
        "tokyo": "tokyo_kz",
        "tokyo_core_0000_0300": "tokyo_kz",
        "london": "london_core",
    }.get(raw, raw)


def _symbol(row: dict[str, Any]) -> str:
    for key in ("symbol", "source_symbol"):
        value = _norm(row.get(key))
        if value:
            return value.split("|", 1)[0]
    for key in ("candidate_id", "route_candidate_id"):
        value = _norm(row.get(key))
        if value:
            return value.split("|", 1)[0].split("_", 1)[0]
    return ""


def _side(row: dict[str, Any]) -> str:
    value = _upper(row.get("side"))
    return value if value in {"LONG", "SHORT"} else ""


def _target_stop_class(row: dict[str, Any]) -> str:
    return _upper(row.get("target_stop_result") or row.get("target_stop_order_class"))


def _proxy_value(row: dict[str, Any]) -> tuple[float | None, str]:
    fields = (
        "ordering_proxy_midpoint_r",
        "selected_shift_proxy_r",
        "selected_shift_r",
        "after_proxy_r",
        "proxy_r_delta",
        "before_proxy_r",
    )
    for field in fields:
        value = _float(row.get(field))
        if value is not None:
            return value, field
    return None, "missing"


def _text_blob(row: dict[str, Any]) -> str:
    keys = (
        "action_class",
        "branch_decision",
        "after_branch_decision",
        "implementation_decision",
        "current_action",
        "next_action",
        "data_requirement_state",
        "ordering_score_status",
        "source_implication_class",
        "m15_ordering_repair_status",
        "target_stop_result",
    )
    return " ".join(_upper(row.get(key)) for key in keys)


def _classify(row: dict[str, Any], *, row_family: str) -> dict[str, Any]:
    text = _text_blob(row)
    proxy_value, proxy_field = _proxy_value(row)
    source_missing = any(
        token in text
        for token in (
            "SOURCE_CAPTURE_REQUIRED",
            "MISSING_REQUIRED_LIVE_METADATA",
            "SOURCE_REPAIR_REQUIRED",
            "EXACT_TICK_STILL_UNAVAILABLE",
            "TICK_SOURCE_INCOMPLETE",
        )
    )
    nofill_or_kill = any(
        token in text
        for token in (
            "KILL",
            "NO_FILL",
            "HARD_NO_FILL",
            "NEGATIVE_PROXY",
            "COMPUTED_BOUNDED_ORDERING_PROXY_NEGATIVE",
        )
    )
    positive_ordering = any(
        token in text
        for token in (
            "KEEP_SOURCE_ACCEPTED_AFTER_M15_ORDERING_POSITIVE_PROXY",
            "COMPUTED_BOUNDED_ORDERING_PROXY_POSITIVE",
            "TARGET_FIRST_PROXY_DOMINANT",
        )
    ) and not nofill_or_kill
    redesign = "REDESIGN" in text or "NOT_COMPUTABLE" in text
    default_off = "IMPLEMENT_DEFAULT_OFF" in text

    if positive_ordering or (proxy_value is not None and proxy_value > 0 and not source_missing):
        return {
            "review_action": "FOLLOW",
            "source_component": "main_orch24_source_m15_ordering_positive_follow",
            "source_role": "main_orch24_source_m15_ordering_positive_follow",
            "source_group": "main_orch24_source_m15_positive_proxy",
            "action_class": "main_orch24_source_m15_positive_proxy_follow",
            "r_evidence_class": "MAIN_ORCH24_SOURCE_M15_POSITIVE_PROXY",
            "proxy_r_class": "POSITIVE_PROXY_R",
            "candidate_use_allowed_now": True,
            "source_acquisition_required": False,
            "source_complete": True,
            "source_acquisition_kind": "",
            "proxy_value": proxy_value if proxy_value is not None else 1.0,
            "proxy_field": proxy_field if proxy_value is not None else "positive_ordering",
        }
    if nofill_or_kill and not source_missing:
        return {
            "review_action": "AVOID",
            "source_component": "main_orch24_source_m15_kill_or_no_fill_guard",
            "source_role": "main_orch24_source_m15_kill_or_no_fill_guard",
            "source_group": "main_orch24_source_m15_kill_or_no_fill",
            "action_class": "main_orch24_source_m15_kill_or_no_fill_avoid_filter",
            "r_evidence_class": "MAIN_ORCH24_SOURCE_M15_NOFILL_AVOID_FILTER",
            "proxy_r_class": "NEGATIVE_OR_NOFILL_PROXY_R",
            "candidate_use_allowed_now": True,
            "source_acquisition_required": False,
            "source_complete": True,
            "source_acquisition_kind": "",
            "proxy_value": proxy_value if proxy_value is not None else -1.0,
            "proxy_field": proxy_field if proxy_value is not None else "kill_or_no_fill",
        }
    if redesign and not source_missing:
        return {
            "review_action": "AVOID",
            "source_component": "main_orch24_source_m15_redesign_guard",
            "source_role": "main_orch24_source_m15_redesign_guard",
            "source_group": "main_orch24_source_m15_redesign",
            "action_class": "main_orch24_source_m15_redesign_avoid_filter",
            "r_evidence_class": "MAIN_ORCH24_SOURCE_M15_REDESIGN_AVOID_FILTER",
            "proxy_r_class": "REDESIGN_REQUIRED",
            "candidate_use_allowed_now": True,
            "source_acquisition_required": False,
            "source_complete": True,
            "source_acquisition_kind": "",
            "proxy_value": proxy_value if proxy_value is not None else -0.5,
            "proxy_field": proxy_field if proxy_value is not None else "redesign_required",
        }
    if source_missing:
        return {
            "review_action": "MIXED",
            "source_component": "main_orch24_source_m15_source_acquisition",
            "source_role": "main_orch24_source_m15_source_acquisition_guard",
            "source_group": "main_orch24_source_m15_source_acquisition",
            "action_class": "main_orch24_source_m15_source_acquisition_context",
            "r_evidence_class": "MAIN_ORCH24_SOURCE_M15_SOURCE_ACQUISITION_REQUIRED",
            "proxy_r_class": "SOURCE_ACQUISITION_REQUIRED",
            "candidate_use_allowed_now": False,
            "source_acquisition_required": True,
            "source_complete": False,
            "source_acquisition_kind": "main_orch24_source_m15_missing_live_metadata_or_exact_tick",
            "proxy_value": proxy_value,
            "proxy_field": proxy_field,
        }
    if default_off:
        return {
            "review_action": "MIXED",
            "source_component": "main_orch24_source_m15_default_off_context",
            "source_role": "main_orch24_source_m15_default_off_context",
            "source_group": "main_orch24_source_m15_default_off_context",
            "action_class": "main_orch24_source_m15_default_off_context",
            "r_evidence_class": "MAIN_ORCH24_SOURCE_M15_DEFAULT_OFF_CONTEXT",
            "proxy_r_class": "DEFAULT_OFF_CONTEXT",
            "candidate_use_allowed_now": False,
            "source_acquisition_required": False,
            "source_complete": True,
            "source_acquisition_kind": "",
            "proxy_value": proxy_value,
            "proxy_field": proxy_field,
        }
    return {
        "review_action": "MIXED",
        "source_component": "main_orch24_source_m15_neutral_context",
        "source_role": "main_orch24_source_m15_neutral_context",
        "source_group": "main_orch24_source_m15_neutral_context",
        "action_class": "main_orch24_source_m15_neutral_context",
        "r_evidence_class": f"MAIN_ORCH24_SOURCE_M15_{row_family.upper()}_CONTEXT",
        "proxy_r_class": "NEUTRAL_OR_CONTEXT",
        "candidate_use_allowed_now": False,
        "source_acquisition_required": False,
        "source_complete": True,
        "source_acquisition_kind": "",
        "proxy_value": proxy_value,
        "proxy_field": proxy_field,
    }


def _event_scope(
    *,
    symbol: str,
    session: str,
    side: str,
    primitive: str,
    source_component: str,
    entry_variant: str,
    target_stop_class: str,
) -> dict[str, str]:
    return {
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "timeframe": "M15",
        "market_timeframe": f"{symbol}:M15" if symbol else "M15",
        "route_session": session,
        "route_family": "main_orch24_source_m15_branch_repair",
        "primitive": primitive,
        "side": side,
        "source_component": source_component,
        "entry_variant": entry_variant,
        "target_stop_order_class": target_stop_class,
    }


def _runtime_row(
    *,
    row: dict[str, Any],
    source_path: Path,
    source_sha256: str,
    source_line_no: int,
    row_family: str,
    sequence: int,
) -> dict[str, Any]:
    classification = _classify(row, row_family=row_family)
    symbol = _symbol(row)
    side = _side(row)
    session = _session(row.get("route_session"))
    primitive = _norm(row.get("primitive_family") or row.get("source_capture_surface"))
    if not primitive:
        primitive = "source_cost_spread_bar_proxy_implication"
    entry_variant = _norm(row.get("entry_variant"))
    target_stop_class = _target_stop_class(row)
    event_scope = _event_scope(
        symbol=symbol,
        session=session,
        side=side,
        primitive=primitive,
        source_component=classification["source_component"],
        entry_variant=entry_variant,
        target_stop_class=target_stop_class,
    )
    source_payload_hash = _sha256_payload(
        {
            key: value
            for key, value in row.items()
            if key not in {"generated_utc"}
        }
    )
    proxy_value = classification["proxy_value"]
    proxy_field = classification["proxy_field"]
    row_key = f"main_orch24:source_m15:{sequence}:{source_payload_hash[:16]}"
    metrics = {
        "proxy_score": _metric(proxy_value, source_field=proxy_field),
        "proxy_r_delta": _metric(_float(row.get("proxy_r_delta")), source_field="proxy_r_delta"),
        "effective_n": _metric(1.0, source_field="main_orch24_source_m15_target_row"),
    }
    return {
        "schema_version": "gtos_vnext_main_orch24_source_m15_branch_repair_runtime_row_v1",
        "row_type": "gtos_vnext_main_orch24_source_m15_branch_repair_runtime_row",
        "main_orch24_source_m15_branch_repair_runtime_row_id": row_key,
        "row_key": row_key,
        "batch_wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "source_kind": f"main_orch24_source_m15_{row_family}_row",
        "source_artifact": _path_text(source_path),
        "source_file_sha256": source_sha256,
        "source_line_no": source_line_no,
        "source_payload_hash": source_payload_hash,
        "source_row_id": _norm(row.get("row_id") or row.get("source_row_id")),
        "candidate_id": _norm(row.get("candidate_id") or row.get("route_candidate_id")),
        "route_candidate_id": _norm(row.get("route_candidate_id")),
        "source_branch_queue_id": _norm(row.get("source_branch_queue_id")),
        "source_implication_implementation_id": _norm(
            row.get("source_implication_implementation_id")
        ),
        "target_stop_contract_id": _norm(row.get("target_stop_contract_id")),
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "timeframe": "M15",
        "market_timeframe": event_scope["market_timeframe"],
        "route_session": session,
        "side": side,
        "entry_variant": entry_variant,
        "target_stop_order_class": target_stop_class,
        "route_family": event_scope["route_family"],
        "primitive": primitive,
        "primitive_family": primitive,
        "source_component": classification["source_component"],
        "source_role": classification["source_role"],
        "source_group": classification["source_group"],
        "system_surface": f"execution_adjacent_{classification['source_component']}",
        "action_class": classification["action_class"],
        "original_action_class": _norm(row.get("action_class")),
        "branch_decision": _norm(row.get("branch_decision")),
        "after_branch_decision": _norm(row.get("after_branch_decision")),
        "implementation_decision": _norm(row.get("implementation_decision")),
        "current_action": _norm(row.get("current_action")),
        "next_action": _norm(row.get("next_action")),
        "data_requirement_state": _norm(row.get("data_requirement_state")),
        "source_capture_surface": _norm(row.get("source_capture_surface")),
        "source_implication_class": _norm(row.get("source_implication_class")),
        "m15_ordering_repair_status": _norm(row.get("m15_ordering_repair_status")),
        "ordering_score_status": _norm(row.get("ordering_score_status")),
        "ordering_evidence_source": _norm(row.get("ordering_evidence_source")),
        "review_action": classification["review_action"],
        "r_evidence_class": classification["r_evidence_class"],
        "proxy_r_class": classification["proxy_r_class"],
        "proxy_r_delta": _float(row.get("proxy_r_delta")),
        "proxy_score": proxy_value,
        "r_metrics": metrics,
        "event_scope": event_scope,
        "source_acquisition_required": classification["source_acquisition_required"],
        "source_acquisition_kind": classification["source_acquisition_kind"],
        "source_complete": classification["source_complete"],
        "source_bound": classification["source_complete"],
        "candidate_use_allowed_now": classification["candidate_use_allowed_now"],
        "runtime_candidate_use_permitted": classification["candidate_use_allowed_now"],
        "runtime_effect_now": "main_orch24_source_m15_branch_repair_shadow_runtime",
        "runtime_trading_or_live_broker_effect": False,
        "broker_operation": False,
        "live_effect": False,
        "paid_api_or_vendor_call": False,
        "no_live_behavior": bool(row.get("no_live_behavior", True)),
        "no_promotion": bool(row.get("no_promotion", True)),
        "claim_boundary": _norm(row.get("claim_boundary")),
    }


def _unique_action_rows() -> list[tuple[dict[str, Any], Path, str, int, str]]:
    selected: dict[str, tuple[dict[str, Any], Path, str, int, str]] = {}
    for source_name in (ACTION_AFTER_SRC_ENTRY_M15, IMPLEMENTATION_ACTION_AFTER_SOURCE_M15):
        source_path = _source_path(source_name)
        source_sha = _sha256_file(source_path)
        for line_no, row in enumerate(_read_jsonl(source_path), start=1):
            payload = {key: value for key, value in row.items() if key != "generated_utc"}
            key = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            selected.setdefault(
                key,
                (row, source_path, source_sha, line_no, "source_entry_m15_action"),
            )
    return list(selected.values())


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    runtime_rows: list[dict[str, Any]] = []
    source_row_totals: Counter[str] = Counter()
    duplicate_rows_removed = 0

    raw_action_counts = []
    for source_name in (ACTION_AFTER_SRC_ENTRY_M15, IMPLEMENTATION_ACTION_AFTER_SOURCE_M15):
        count = _source_row_count(_source_path(source_name))
        raw_action_counts.append(count)
        source_row_totals[source_name] = count
    unique_action_rows = _unique_action_rows()
    duplicate_rows_removed = sum(raw_action_counts) - len(unique_action_rows)
    for args in unique_action_rows:
        runtime_rows.append(
            _runtime_row(row=args[0], source_path=args[1], source_sha256=args[2], source_line_no=args[3], row_family=args[4], sequence=len(runtime_rows) + 1)
        )

    for source_name, row_family in (
        (SOURCE_M15_ORDERING_REPAIR, "ordering_repair"),
        (SOURCE_UPGRADED_BRANCH_DECISION, "upgraded_degraded_branch"),
    ):
        source_path = _source_path(source_name)
        source_sha = _sha256_file(source_path)
        rows = _read_jsonl(source_path)
        source_row_totals[source_name] = len(rows)
        for line_no, row in enumerate(rows, start=1):
            runtime_rows.append(
                _runtime_row(
                    row=row,
                    source_path=source_path,
                    source_sha256=source_sha,
                    source_line_no=line_no,
                    row_family=row_family,
                    sequence=len(runtime_rows) + 1,
                )
            )

    coverage = {
        "symbols": Counter(row["symbol"] for row in runtime_rows if row["symbol"]),
        "source_symbols": Counter(row["source_symbol"] for row in runtime_rows if row["source_symbol"]),
        "markets": Counter(row["market"] for row in runtime_rows if row["market"]),
        "timeframes": Counter(row["timeframe"] for row in runtime_rows if row["timeframe"]),
        "sessions": Counter(row["route_session"] for row in runtime_rows if row["route_session"]),
        "sides": Counter(row["side"] for row in runtime_rows if row["side"]),
        "entry_variants": Counter(row["entry_variant"] for row in runtime_rows if row["entry_variant"]),
        "target_stop_order_classes": Counter(
            row["target_stop_order_class"] for row in runtime_rows if row["target_stop_order_class"]
        ),
        "primitives": Counter(row["primitive"] for row in runtime_rows if row["primitive"]),
        "route_families": Counter(row["route_family"] for row in runtime_rows if row["route_family"]),
        "source_components": Counter(row["source_component"] for row in runtime_rows),
        "source_roles": Counter(row["source_role"] for row in runtime_rows),
        "source_groups": Counter(row["source_group"] for row in runtime_rows),
        "action_classes": Counter(row["action_class"] for row in runtime_rows),
        "r_evidence_classes": Counter(row["r_evidence_class"] for row in runtime_rows),
        "proxy_r_classes": Counter(row["proxy_r_class"] for row in runtime_rows),
        "system_surfaces": Counter(row["system_surface"] for row in runtime_rows),
        "source_capture_surfaces": Counter(
            row["source_capture_surface"] for row in runtime_rows if row["source_capture_surface"]
        ),
        "implementation_decisions": Counter(
            row["implementation_decision"] for row in runtime_rows if row["implementation_decision"]
        ),
        "branch_decisions": Counter(row["branch_decision"] for row in runtime_rows if row["branch_decision"]),
        "data_requirement_states": Counter(
            row["data_requirement_state"] for row in runtime_rows if row["data_requirement_state"]
        ),
    }
    blank_anchor_counts = {
        field: sum(1 for row in runtime_rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }
    summary = {
        "schema_version": "gtos_vnext_main_orch24_source_m15_branch_repair_runtime_summary_v1",
        "batch_wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(runtime_rows),
        "runtime_source_rows_represented": len(runtime_rows),
        "wave_source_rows_counted": sum(source_row_totals.values()),
        "raw_action_rows_represented": sum(raw_action_counts),
        "unique_action_rows_represented": len(unique_action_rows),
        "duplicate_action_rows_removed": duplicate_rows_removed,
        "ordering_repair_rows_represented": source_row_totals[SOURCE_M15_ORDERING_REPAIR],
        "upgraded_degraded_branch_rows_represented": source_row_totals[
            SOURCE_UPGRADED_BRANCH_DECISION
        ],
        "selected_open_unit_count": len(SOURCE_ARTIFACTS),
        "row_count_unknown_unit_count": 0,
        "source_acquisition_required_rows": sum(
            1 for row in runtime_rows if row["source_acquisition_required"]
        ),
        "candidate_use_allowed_now_rows": sum(
            1 for row in runtime_rows if row["candidate_use_allowed_now"]
        ),
        "runtime_rows_with_event_scope": sum(1 for row in runtime_rows if row["event_scope"]),
        "runtime_rows_without_event_scope": sum(1 for row in runtime_rows if not row["event_scope"]),
        "broker_operation_rows": sum(1 for row in runtime_rows if row["broker_operation"]),
        "live_effect_rows": sum(1 for row in runtime_rows if row["live_effect"]),
        "paid_api_or_vendor_call_rows": sum(
            1 for row in runtime_rows if row["paid_api_or_vendor_call"]
        ),
        "runtime_trading_or_live_broker_effect_rows": sum(
            1 for row in runtime_rows if row["runtime_trading_or_live_broker_effect"]
        ),
        "decision_counts": dict(Counter(row["review_action"] for row in runtime_rows)),
        "source_component_counts": dict(coverage["source_components"]),
        "r_evidence_class_counts": dict(coverage["r_evidence_classes"]),
        "source_acquisition_kind_counts": dict(
            Counter(
                row["source_acquisition_kind"]
                for row in runtime_rows
                if row["source_acquisition_kind"]
            )
        ),
        "positive_proxy_rows": sum(
            1 for row in runtime_rows if row["proxy_r_class"] == "POSITIVE_PROXY_R"
        ),
        "avoid_or_redesign_rows": sum(
            1
            for row in runtime_rows
            if row["review_action"] == "AVOID"
        ),
        "coverage_counts": {
            key: dict(counter)
            for key, counter in coverage.items()
        },
        "blank_anchor_counts": blank_anchor_counts,
        "source_row_totals": dict(source_row_totals),
        "source_artifacts": _source_artifacts_summary(runtime_rows),
    }
    return runtime_rows, summary


def _source_artifacts_summary(runtime_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_rows_by_name = Counter(Path(row["source_artifact"]).name for row in runtime_rows)
    artifacts: list[dict[str, Any]] = []
    for unit_id, name, git_hash in SOURCE_ARTIFACTS:
        path = _source_path(name)
        artifacts.append(
            {
                "unit_id": unit_id,
                "name": name,
                "path": _path_text(path),
                "hash": git_hash,
                "hash_algorithm": "git_blob",
                "sha256": _sha256_file(path),
                "row_count": _source_row_count(path),
                "runtime_rows_read": runtime_rows_by_name.get(name, 0),
                "source_role": (
                    "primary_runtime_rows"
                    if name
                    in {
                        ACTION_AFTER_SRC_ENTRY_M15,
                        IMPLEMENTATION_ACTION_AFTER_SOURCE_M15,
                        SOURCE_M15_ORDERING_REPAIR,
                        SOURCE_UPGRADED_BRANCH_DECISION,
                    }
                    else "supporting_source_m15_branch_repair_evidence"
                ),
            }
        )
    return artifacts


def write_artifacts(*, check: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows, summary = build_rows()
    row_text = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows
    )
    summary_text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if check:
        if not OUTPUT_ROWS.exists() or OUTPUT_ROWS.read_text(encoding="utf-8") != row_text:
            raise SystemExit(f"{OUTPUT_ROWS} is stale")
        if not OUTPUT_SUMMARY.exists() or OUTPUT_SUMMARY.read_text(encoding="utf-8") != summary_text:
            raise SystemExit(f"{OUTPUT_SUMMARY} is stale")
    else:
        OUTPUT_ROWS.write_text(row_text, encoding="utf-8")
        OUTPUT_SUMMARY.write_text(summary_text, encoding="utf-8")
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    _, summary = write_artifacts(check=args.check)
    action = "verified" if args.check else "wrote"
    print(
        f"Main Orch24 source/M15 branch-repair runtime artifacts {action}: "
        f"{summary['runtime_row_count']} rows."
    )


if __name__ == "__main__":
    main()
