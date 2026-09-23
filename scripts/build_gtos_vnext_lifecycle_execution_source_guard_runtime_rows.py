#!/usr/bin/env python3
"""Build vNext lifecycle execution/source-guard runtime rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_lifecycle_execution_source_guard"
SOURCE_NAME = "gtos_vnext_lifecycle_execution_source_guard_wave"
RUNTIME_SURFACE = "lifecycle_execution_source_guard_runtime"

BUILDER_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
OUTPUT_ROWS = (
    BUILDER_DIR / f"GTOS_VNEXT_LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    BUILDER_DIR / f"GTOS_VNEXT_LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME_SUMMARY_{DATE}.json"
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
    "source_component",
    "target_stop_order_class",
)

SOURCE_ACQUISITION_COMPONENTS = {
    "lifecycle_still_pending_no_fill_source_guard",
    "lifecycle_wrong_side_no_fill_source_guard",
    "trade_index_lifecycle_action_required_source_repair",
    "opportunity_lifecycle_reset_policy_source_guard",
}
REPLAY_COMPONENT = "lifecycle_execution_replay_attribution_only"

SYMBOL_ALIASES = {
    "NDX100": "NAS100",
    "NAS100": "NAS100",
    "US30_cash": "US30",
    "US30_CASH": "US30",
}

SELECTED_SOURCES = (
    ("UNIT_003049", "knowledge_base/index/_trade_index.json", 2540),
    ("UNIT_005075", "research/operations/POST_WINDOW_HEARTBEAT_LIFECYCLE_REVIEW_2026-05-06.md", 124),
    ("UNIT_005131", "research/operations/trade_index_frozen_bug_2026-04-28.md", 26),
    ("UNIT_005527", "research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.json", 52),
    ("UNIT_005528", "research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.md", 30),
    ("UNIT_005573", "research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.json", 310),
    ("UNIT_005574", "research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.md", 296),
    ("UNIT_011269", "research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/build_otb1_lifecycle_packet_builder_2026_05_07.py", 997),
    ("UNIT_011270", "research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/OTB1_AMBIGUITY_LEDGER_2026-05-07.json", 113),
    ("UNIT_011271", "research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/OTB1_AMBIGUITY_LEDGER_2026-05-07.md", 14),
    ("UNIT_011272", "research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/OTB1_ARTIFACT_MANIFEST_2026-05-07.json", 123),
    ("UNIT_011273", "research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/OTB1_COMPLETION_AUDIT_2026-05-07.json", 141),
    ("UNIT_011274", "research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/OTB1_COMPLETION_AUDIT_2026-05-07.md", 50),
    ("UNIT_011275", "research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/OTB1_LIFECYCLE_PACKET_BUILD_LEDGER_2026-05-07.json", 361),
    ("UNIT_011276", "research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/OTB1_LIFECYCLE_PACKET_BUILD_LEDGER_2026-05-07.md", 40),
    ("UNIT_011289", "research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/README_2026-05-07.md", 7),
    ("UNIT_011290", "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/build_otb1r_input_only_lifecycle_rebuild_2026_05_07.py", 1202),
    ("UNIT_011291", "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_AMBIGUITY_LEDGER_2026-05-07.json", 119),
    ("UNIT_011292", "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_AMBIGUITY_LEDGER_2026-05-07.md", 12),
    ("UNIT_011293", "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_ARTIFACT_MANIFEST_2026-05-07.json", 285),
    ("UNIT_011294", "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_COMPLETION_AUDIT_2026-05-07.json", 122),
    ("UNIT_011295", "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_COMPLETION_AUDIT_2026-05-07.md", 24),
    ("UNIT_011298", "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_INPUT_ONLY_LIFECYCLE_REBUILD_LEDGER_2026-05-07.json", 362),
    ("UNIT_011299", "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_INPUT_ONLY_LIFECYCLE_REBUILD_LEDGER_2026-05-07.md", 27),
    ("UNIT_011312", "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/README_2026-05-07.md", 7),
    ("UNIT_011313", "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/source_projections/OTB1R_SANITIZED_LIFECYCLE_SOURCE_PROJECTIONS_2026-05-07.jsonl", 8),
    ("UNIT_011531", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/build_oti1_lifecycle_quarantined_results_2026_05_07.py", 879),
    ("UNIT_011532", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_AMBIGUITY_RESOLUTION_LEDGER_2026-05-07.json", 93),
    ("UNIT_011533", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_AMBIGUITY_RESOLUTION_LEDGER_2026-05-07.md", 19),
    ("UNIT_011534", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_ARTIFACT_MANIFEST_2026-05-07.json", 130),
    ("UNIT_011535", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_BLOCKER_LEDGER_2026-05-07.json", 93),
    ("UNIT_011536", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_BLOCKER_LEDGER_2026-05-07.md", 16),
    ("UNIT_011537", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_COMPLETION_AUDIT_2026-05-07.json", 166),
    ("UNIT_011538", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_COMPLETION_AUDIT_2026-05-07.md", 45),
    ("UNIT_011541", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_LABEL_FAMILY_SEPARATION_REPORT_2026-05-07.json", 109),
    ("UNIT_011542", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_LABEL_FAMILY_SEPARATION_REPORT_2026-05-07.md", 27),
    ("UNIT_011543", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_METHODOLOGY_REPORT_2026-05-07.json", 130),
    ("UNIT_011544", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_METHODOLOGY_REPORT_2026-05-07.md", 65),
    ("UNIT_011545", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_METRIC_FREEZE_2026-05-07.json", 65),
    ("UNIT_011546", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_METRIC_FREEZE_2026-05-07.md", 106),
    ("UNIT_011547", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_RESULT_LEDGER_2026-05-07.json", 1533),
    ("UNIT_011548", "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_RESULT_LEDGER_2026-05-07.md", 60),
)


def _repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _source_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else REPO_ROOT / path


def _sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_text(value: str, size: int = 24) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:size]


def _read_json(path_text: str) -> Any:
    with _source_path(path_text).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _read_jsonl(path_text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with _source_path(path_text).open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            text = line.strip()
            if text:
                rows.append(json.loads(text))
    return rows


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _canonical_symbol(value: Any) -> str:
    text = _norm(value)
    return SYMBOL_ALIASES.get(text, text)


def _canonical_session(value: Any) -> str:
    text = _norm(value).casefold()
    return {
        "london": "london_core",
        "london_core": "london_core",
        "ny": "ny_core",
        "new_york": "ny_core",
        "ny_core": "ny_core",
        "tokyo": "tokyo_kz",
        "tokyo_kz": "tokyo_kz",
        "asia": "tokyo_kz",
        "off_core_session": "off_core_session",
    }.get(text, _norm(value))


def _infer_session_from_candidate(candidate_id: Any) -> str:
    text = _norm(candidate_id)
    match = re.search(r"T(\d{2}):(\d{2})", text)
    if not match:
        return ""
    hour = int(match.group(1))
    minute = int(match.group(2))
    total = hour * 60 + minute
    if 0 <= total < 3 * 60 + 30:
        return "tokyo_kz"
    if 7 * 60 <= total <= 10 * 60 + 30:
        return "london_core"
    if 13 * 60 <= total <= 17 * 60:
        return "ny_core"
    return "off_core_session"


def _metric(count: int = 1, value: float = 1.0) -> dict[str, Any]:
    return {
        "count": count,
        "match_rows_with_metric": count,
        "mean": value,
        "negative_rows": 1 if value < 0 else 0,
        "positive_rows": 1 if value > 0 else 0,
        "source_field": "source_row",
        "source_shape": RUNTIME_SURFACE,
        "sum": value * count,
        "zero_rows": 1 if value == 0 else 0,
    }


def _component_for_state(state: Any, reason: Any = "") -> str:
    state_text = f"{_norm(state)} {_norm(reason)}".casefold()
    if "wrong_side" in state_text or "price_beyond_sl" in state_text:
        return "lifecycle_wrong_side_no_fill_source_guard"
    if "still_pending" in state_text or "pending" in state_text:
        return "lifecycle_still_pending_no_fill_source_guard"
    return "opportunity_lifecycle_reset_policy_source_guard"


def _guard_row(
    *,
    source_path: str,
    unit_id: str,
    source_line_no: int,
    symbol: str,
    source_symbol: str,
    route_session: str,
    side: str,
    source_component: str,
    primitive: str,
    target_stop_order_class: str,
    source_row_id: str,
    source_artifact_hash: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    symbol = _canonical_symbol(symbol or source_symbol)
    source_symbol = _norm(source_symbol) or symbol
    route_session = _canonical_session(route_session)
    side = _norm(side).upper()
    event_scope = {
        "symbol": symbol,
        "source_symbol": source_symbol,
        "market": symbol,
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": route_session,
        "source_component": source_component,
        "primitive": primitive,
        "target_stop_order_class": target_stop_order_class,
    }
    if side:
        event_scope["side"] = side
    row_key = _hash_text(
        f"{WAVE_ID}|{source_path}|{source_line_no}|{source_row_id}|{source_component}",
        32,
    )
    row = {
        "action_class": "lifecycle_execution_source_acquisition_guard",
        "batch_wave_id": WAVE_ID,
        "broker_operation": False,
        "broker_operation_permitted": False,
        "candidate_use_allowed_now": False,
        "decision": "MIXED",
        "event_scope": event_scope,
        "evidence_family": EVIDENCE_FAMILY,
        "horizon_id": "",
        "live_effect": False,
        "market": symbol,
        "market_timeframe": "M15",
        "opens_ai_api": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_paid_or_vendor_access": False,
        "paid_api_or_vendor_call": False,
        "primitive": primitive,
        "production_change_opened_now": False,
        "proxy_r_class": "SOURCE_ACQUISITION_REQUIRED",
        "r_evidence_class": "LIFECYCLE_EXECUTION_SOURCE_ACQUISITION_REQUIRED",
        "r_metrics": {
            "effective_n": _metric(),
            "proxy_score": _metric(value=0.0),
        },
        "replay_r_reference_counted_as_new_main_result": False,
        "review_action": "MIXED_SOURCE_ACQUISITION_GUARD",
        "route_family": "ob_retest",
        "route_session": route_session,
        "row_key": row_key,
        "runtime_candidate_use_permitted": False,
        "runtime_decision_effect": bool(symbol and route_session),
        "runtime_effect_now": "lifecycle_execution_source_acquisition_guard",
        "runtime_trading_or_live_broker_effect": False,
        "schema_version": "gtos_vnext_lifecycle_execution_source_guard_runtime_row_v1",
        "side": side,
        "source_acquisition_required": True,
        "source_artifact_hash": source_artifact_hash,
        "source_artifact_path": source_path,
        "source_artifact_sha256": source_artifact_hash,
        "source_bound": bool(symbol and route_session),
        "source_complete": False,
        "source_component": source_component,
        "source_event_rows": 1,
        "source_group": "lifecycle_execution_source_guard",
        "source_line_no": source_line_no,
        "source_name": SOURCE_NAME,
        "source_path": source_path,
        "source_repair_required": True,
        "source_role": "lifecycle_execution_source_acquisition_guard",
        "source_row_id": source_row_id,
        "source_symbol": source_symbol,
        "symbol": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol),
        "system_surface": RUNTIME_SURFACE,
        "target_stop_order_class": target_stop_order_class,
        "timeframe": "M15",
        "unit_id": unit_id,
        "validation_safe": False,
        "wave_id": WAVE_ID,
        "lifecycle_execution_source_guard_runtime_row_id": (
            f"lifecycle_execution_source_guard:{row_key}"
        ),
    }
    if extra:
        row.update(extra)
    return row


def _replay_row(
    *,
    source_path: str,
    unit_id: str,
    source_line_no: int,
    primitive: str,
    source_row_id: str,
    source_artifact_hash: str,
    count: int = 1,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row_key = _hash_text(
        f"{WAVE_ID}|{source_path}|{source_line_no}|{source_row_id}|{primitive}",
        32,
    )
    row = {
        "action_class": REPLAY_COMPONENT,
        "batch_wave_id": WAVE_ID,
        "broker_operation": False,
        "broker_operation_permitted": False,
        "candidate_use_allowed_now": False,
        "decision": "MIXED",
        "event_scope": {},
        "evidence_family": EVIDENCE_FAMILY,
        "horizon_id": "",
        "live_effect": False,
        "market": "",
        "market_timeframe": "",
        "opens_ai_api": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_paid_or_vendor_access": False,
        "paid_api_or_vendor_call": False,
        "primitive": primitive,
        "production_change_opened_now": False,
        "proxy_r_class": "REPLAY_ATTRIBUTION_ONLY",
        "r_evidence_class": "LIFECYCLE_EXECUTION_REPLAY_ATTRIBUTION",
        "r_metrics": {
            "effective_n": _metric(count=count),
            "proxy_score": _metric(count=count, value=0.0),
        },
        "replay_r_reference_counted_as_new_main_result": False,
        "review_action": "MIXED_REPLAY_ATTRIBUTION_ONLY",
        "route_family": "",
        "route_session": "",
        "row_key": row_key,
        "runtime_candidate_use_permitted": False,
        "runtime_decision_effect": False,
        "runtime_effect_now": "lifecycle_execution_replay_attribution_only",
        "runtime_trading_or_live_broker_effect": False,
        "schema_version": "gtos_vnext_lifecycle_execution_source_guard_runtime_row_v1",
        "side": "",
        "source_acquisition_required": False,
        "source_artifact_hash": source_artifact_hash,
        "source_artifact_path": source_path,
        "source_artifact_sha256": source_artifact_hash,
        "source_bound": False,
        "source_complete": True,
        "source_component": REPLAY_COMPONENT,
        "source_event_rows": count,
        "source_group": "lifecycle_execution_replay_attribution_only",
        "source_line_no": source_line_no,
        "source_name": SOURCE_NAME,
        "source_path": source_path,
        "source_repair_required": False,
        "source_role": "lifecycle_execution_replay_attribution_guard",
        "source_row_id": source_row_id,
        "source_symbol": "",
        "symbol": "",
        "symbol_family": "",
        "system_surface": RUNTIME_SURFACE,
        "target_stop_order_class": "",
        "timeframe": "",
        "unit_id": unit_id,
        "validation_safe": False,
        "wave_id": WAVE_ID,
        "lifecycle_execution_source_guard_runtime_row_id": (
            f"lifecycle_execution_source_guard:{row_key}"
        ),
    }
    if extra:
        row.update(extra)
    return row


def _source_meta_by_path() -> dict[str, dict[str, Any]]:
    meta = {}
    for unit_id, path_text, rows in SELECTED_SOURCES:
        path = _source_path(path_text)
        meta[path_text] = {
            "unit_id": unit_id,
            "path": path_text,
            "rows": int(rows),
            "hash": _sha256(path),
            "runtime_rows_read": 0,
        }
    return meta


def _projection_lookup(rows: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for item in rows:
        setup_id = _norm(item.get("setup_id_or_candidate_id"))
        dependencies = item.get("projected_dependencies")
        if not isinstance(dependencies, list):
            continue
        merged: dict[str, str] = {}
        for dep in dependencies:
            if not isinstance(dep, dict):
                continue
            source_row = dep.get("sanitized_source_row")
            if not isinstance(source_row, dict):
                continue
            if not merged.get("symbol"):
                merged["symbol"] = _canonical_symbol(source_row.get("symbol"))
            if not merged.get("source_symbol"):
                merged["source_symbol"] = _norm(source_row.get("source_symbol"))
            if not merged.get("route_session"):
                merged["route_session"] = _canonical_session(
                    source_row.get("session") or source_row.get("kill_zone")
                )
            if not merged.get("side"):
                merged["side"] = _norm(source_row.get("side")).upper()
            if not merged.get("fill_no_fill_label"):
                merged["fill_no_fill_label"] = _norm(
                    source_row.get("fill_no_fill_label")
                    or source_row.get("final_state")
                )
            if not merged.get("reason"):
                merged["reason"] = _norm(
                    source_row.get("cancel_reason")
                    or source_row.get("reason")
                    or source_row.get("latest_lifecycle_cancel_reason")
                )
        if setup_id:
            lookup[setup_id] = merged
    return lookup


def _build_rows(meta: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    trade_index_path = "knowledge_base/index/_trade_index.json"
    trade_index = _read_json(trade_index_path)
    trade_rows = trade_index.get("trades") if isinstance(trade_index, dict) else []
    if isinstance(trade_rows, list):
        rows.append(
            _replay_row(
                source_path=trade_index_path,
                unit_id=meta[trade_index_path]["unit_id"],
                source_line_no=1,
                primitive="legacy_trade_index_replay_attribution",
                source_row_id="trade_index_legacy_replay_attribution",
                source_artifact_hash=meta[trade_index_path]["hash"],
                count=len(trade_rows),
                extra={
                    "trade_index_trade_count": len(trade_rows),
                    "trade_index_framework_counts": dict(
                        sorted(Counter(_norm(item.get("framework")) for item in trade_rows if isinstance(item, dict)).items())
                    ),
                },
            )
        )
        meta[trade_index_path]["runtime_rows_read"] = len(trade_rows)

    lto004_path = "research/program_control/LTO004_OPPORTUNITY_LIFECYCLE_AUDIT_2026-05-05.json"
    lto004 = _read_json(lto004_path)
    reset_counts = lto004.get("reset_policy_status_counts", {}) if isinstance(lto004, dict) else {}
    if isinstance(reset_counts, dict):
        line_no = 1
        for status, count in sorted(reset_counts.items()):
            rows.append(
                _guard_row(
                    source_path=lto004_path,
                    unit_id=meta[lto004_path]["unit_id"],
                    source_line_no=line_no,
                    symbol="",
                    source_symbol="",
                    route_session="",
                    side="",
                    source_component="opportunity_lifecycle_reset_policy_source_guard",
                    primitive=_norm(status),
                    target_stop_order_class="SOURCE_ACQUISITION_REQUIRED",
                    source_row_id=f"lto004:{status}",
                    source_artifact_hash=meta[lto004_path]["hash"],
                    extra={
                        "runtime_decision_effect": False,
                        "source_bound": False,
                        "event_scope": {
                            "source_component": "opportunity_lifecycle_reset_policy_source_guard",
                            "primitive": _norm(status),
                            "target_stop_order_class": "SOURCE_ACQUISITION_REQUIRED",
                        },
                        "lifecycle_reset_policy_status": status,
                        "source_event_rows": int(count or 0),
                    },
                )
            )
            line_no += 1
        meta[lto004_path]["runtime_rows_read"] = len(reset_counts)

    lto026_path = "research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.json"
    lto026 = _read_json(lto026_path)
    action_examples = lto026.get("action_required_examples", []) if isinstance(lto026, dict) else []
    if isinstance(action_examples, list):
        for line_no, item in enumerate(action_examples, 1):
            if not isinstance(item, dict):
                continue
            candidate_id = _norm(item.get("candidate_id"))
            rows.append(
                _guard_row(
                    source_path=lto026_path,
                    unit_id=meta[lto026_path]["unit_id"],
                    source_line_no=line_no,
                    symbol=_canonical_symbol(item.get("symbol")),
                    source_symbol=_norm(item.get("symbol")),
                    route_session=_infer_session_from_candidate(candidate_id),
                    side="",
                    source_component="trade_index_lifecycle_action_required_source_repair",
                    primitive="trade_index_lifecycle_action_required",
                    target_stop_order_class="SOURCE_ACQUISITION_REQUIRED",
                    source_row_id=f"lto026:{candidate_id}",
                    source_artifact_hash=meta[lto026_path]["hash"],
                    extra={
                        "action_required_codes": item.get("action_required_codes", []),
                        "candidate_id": candidate_id,
                        "source_record_path": item.get("source_path", ""),
                    },
                )
            )
        meta[lto026_path]["runtime_rows_read"] = len(action_examples)

    projection_path = (
        "research/science_program_2026_05/06_outcome_testing/"
        "otb1r_input_only_lifecycle_rebuild/source_projections/"
        "OTB1R_SANITIZED_LIFECYCLE_SOURCE_PROJECTIONS_2026-05-07.jsonl"
    )
    projections = _read_jsonl(projection_path)
    projection_lookup = _projection_lookup(projections)
    for line_no, item in enumerate(projections, 1):
        dependencies = item.get("projected_dependencies")
        source_row: dict[str, Any] = {}
        if isinstance(dependencies, list):
            for dep in dependencies:
                if isinstance(dep, dict) and dep.get("source_role") == "pending_limit_lifecycle_latest_group_row":
                    candidate = dep.get("sanitized_source_row")
                    if isinstance(candidate, dict):
                        source_row = candidate
                        break
        if not source_row:
            continue
        label = _norm(source_row.get("fill_no_fill_label"))
        component = _component_for_state(label, source_row.get("cancel_reason") or source_row.get("reason"))
        rows.append(
            _guard_row(
                source_path=projection_path,
                unit_id=meta[projection_path]["unit_id"],
                source_line_no=line_no,
                symbol=_canonical_symbol(source_row.get("symbol") or item.get("source_symbol")),
                source_symbol=_norm(source_row.get("source_symbol") or item.get("source_symbol")),
                route_session=(
                    _canonical_session(source_row.get("session") or source_row.get("kill_zone"))
                    or _infer_session_from_candidate(item.get("setup_id_or_candidate_id"))
                ),
                side=_norm(source_row.get("side")).upper(),
                source_component=component,
                primitive=label or _norm(source_row.get("intent_after_check")),
                target_stop_order_class="SOURCE_ACQUISITION_REQUIRED",
                source_row_id=f"otb1r_projection:{item.get('source_projection_id')}",
                source_artifact_hash=meta[projection_path]["hash"],
                extra={
                    "candidate_id": _norm(source_row.get("candidate_id") or item.get("setup_id_or_candidate_id")),
                    "cancel_reason": _norm(source_row.get("cancel_reason") or source_row.get("reason")),
                    "entry_price": source_row.get("entry_price"),
                    "stop_loss": source_row.get("stop_loss"),
                    "take_profit_1": source_row.get("take_profit_1"),
                    "lifecycle_state": label,
                    "no_leak_status": source_row.get("no_leak_status", ""),
                },
            )
        )
    meta[projection_path]["runtime_rows_read"] = len(projections)

    oti1_path = (
        "research/science_program_2026_05/06_outcome_testing/"
        "oti1_lifecycle_quarantined_results/OTI1_RESULT_LEDGER_2026-05-07.json"
    )
    oti1 = _read_json(oti1_path)
    group_count = 0
    packet_results = oti1.get("packet_results", []) if isinstance(oti1, dict) else []
    if isinstance(packet_results, list):
        for packet in packet_results:
            if not isinstance(packet, dict):
                continue
            for summary in packet.get("group_summaries", []) or []:
                if not isinstance(summary, dict):
                    continue
                group_count += 1
                setup_ids = summary.get("setup_ids") if isinstance(summary.get("setup_ids"), list) else []
                setup_id = _norm(setup_ids[0] if setup_ids else "")
                lookup = projection_lookup.get(setup_id, {})
                source_symbols = summary.get("source_symbols") if isinstance(summary.get("source_symbols"), list) else []
                source_symbol = _norm(source_symbols[0] if source_symbols else lookup.get("source_symbol"))
                symbol = _canonical_symbol(lookup.get("symbol") or source_symbol)
                route_session = (
                    _canonical_session(lookup.get("route_session"))
                    or _infer_session_from_candidate(setup_id)
                )
                component = _component_for_state(
                    summary.get("fill_or_no_fill_state") or summary.get("lifecycle_state"),
                    summary.get("cancel_expiry_or_wrong_side_reason"),
                )
                rows.append(
                    _guard_row(
                        source_path=oti1_path,
                        unit_id=meta[oti1_path]["unit_id"],
                        source_line_no=group_count,
                        symbol=symbol,
                        source_symbol=source_symbol,
                        route_session=route_session,
                        side=lookup.get("side", ""),
                        source_component=component,
                        primitive=_norm(summary.get("fill_or_no_fill_state") or summary.get("lifecycle_state")),
                        target_stop_order_class="SOURCE_ACQUISITION_REQUIRED",
                        source_row_id=f"oti1:{packet.get('packet_id')}:{summary.get('duplicate_group_id')}",
                        source_artifact_hash=meta[oti1_path]["hash"],
                        extra={
                            "packet_id": packet.get("packet_id"),
                            "duplicate_group_id": summary.get("duplicate_group_id"),
                            "raw_child_rows": summary.get("raw_child_rows"),
                            "lifecycle_state": summary.get("lifecycle_state"),
                            "fill_or_no_fill_state": summary.get("fill_or_no_fill_state"),
                            "cancel_expiry_or_wrong_side_reason": summary.get("cancel_expiry_or_wrong_side_reason"),
                        },
                    )
                )
    meta[oti1_path]["runtime_rows_read"] = group_count

    for path_text in (
        "research/science_program_2026_05/06_outcome_testing/otb1_lifecycle_packet_builder/OTB1_LIFECYCLE_PACKET_BUILD_LEDGER_2026-05-07.json",
        "research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_INPUT_ONLY_LIFECYCLE_REBUILD_LEDGER_2026-05-07.json",
        "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_METRIC_FREEZE_2026-05-07.json",
    ):
        payload = _read_json(path_text)
        primitive = Path(path_text).stem.casefold()
        rows.append(
            _replay_row(
                source_path=path_text,
                unit_id=meta[path_text]["unit_id"],
                source_line_no=1,
                primitive=primitive,
                source_row_id=f"replay:{primitive}",
                source_artifact_hash=meta[path_text]["hash"],
                count=1,
                extra={
                    "artifact_family": payload.get("artifact_family", "") if isinstance(payload, dict) else "",
                    "replay_attribution_reason": (
                        "row-bearing lifecycle support retained only for "
                        "impact attribution after child lifecycle rows are "
                        "converted to guarded runtime behavior"
                    ),
                },
            )
        )
        meta[path_text]["runtime_rows_read"] = 1

    return rows


def _summary(rows: list[dict[str, Any]], meta: dict[str, dict[str, Any]]) -> dict[str, Any]:
    def _counter(field: str) -> dict[str, int]:
        return dict(sorted(Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field))).items()))

    coverage = {
        "symbols": _counter("symbol"),
        "source_symbols": _counter("source_symbol"),
        "markets": _counter("market"),
        "timeframes": _counter("timeframe"),
        "sessions": _counter("route_session"),
        "sides": _counter("side"),
        "entry_variants": {},
        "target_stop_order_classes": _counter("target_stop_order_class"),
        "source_components": _counter("source_component"),
    }
    blank_anchors = {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }
    source_artifacts = []
    for _, path_text, _ in SELECTED_SOURCES:
        item = dict(meta[path_text])
        item["sha256_or_git_blob"] = item["hash"]
        source_artifacts.append(item)
    converted = [item for item in source_artifacts if int(item.get("runtime_rows_read") or 0) > 0]
    runtime_rows_with_event_scope = sum(
        1
        for row in rows
        if isinstance(row.get("event_scope"), dict)
        and bool(row["event_scope"].get("symbol") and row["event_scope"].get("route_session"))
    )
    source_acquisition_rows = sum(1 for row in rows if row.get("source_acquisition_required"))
    replay_rows = len(rows) - source_acquisition_rows
    source_rows_represented = sum(int(item[2]) for item in SELECTED_SOURCES)
    return {
        "schema_version": "gtos_vnext_lifecycle_execution_source_guard_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "runtime_surface": RUNTIME_SURFACE,
        "output_rows_path": _repo_path(OUTPUT_ROWS),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": source_rows_represented,
        "wave_source_rows_counted": source_rows_represented,
        "wave_source_artifact_count": len(SELECTED_SOURCES),
        "selected_source_unit_count": len(SELECTED_SOURCES),
        "converted_source_unit_count": len(converted),
        "support_or_killed_source_unit_count": len(SELECTED_SOURCES) - len(converted),
        "row_count_unknown_unit_count": 0,
        "source_acquisition_required_rows": source_acquisition_rows,
        "source_repair_required_rows": source_acquisition_rows,
        "replay_attribution_rows": replay_rows,
        "runtime_rows_with_event_scope": runtime_rows_with_event_scope,
        "runtime_rows_without_event_scope": len(rows) - runtime_rows_with_event_scope,
        "runtime_candidate_use_permitted_rows": 0,
        "candidate_use_allowed_now_rows": 0,
        "broker_operation_rows": 0,
        "broker_operation_permitted_rows": 0,
        "paid_api_or_vendor_call_rows": 0,
        "runtime_trading_or_live_broker_effect_rows": 0,
        "live_effect_rows": 0,
        "decision_counts": _counter("decision"),
        "action_class_counts": _counter("action_class"),
        "r_evidence_class_counts": _counter("r_evidence_class"),
        "source_component_counts": _counter("source_component"),
        "source_role_counts": _counter("source_role"),
        "source_group_counts": _counter("source_group"),
        "coverage_counts": coverage,
        "blank_anchor_counts": blank_anchors,
        "source_artifacts": source_artifacts,
        "runtime_admission": {
            "admitted_outcome": "TESTED_SOURCE_REPAIR_OR_GUARD",
            "legacy_support_override_allowed": False,
            "replay_attribution_component": REPLAY_COMPONENT,
            "source_acquisition_components": sorted(SOURCE_ACQUISITION_COMPONENTS),
        },
    }


def build() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    meta = _source_meta_by_path()
    rows = _build_rows(meta)
    return rows, _summary(rows, meta)


def write_outputs(*, check: bool = False) -> int:
    rows, summary = build()
    BUILDER_DIR.mkdir(parents=True, exist_ok=True)
    row_text = "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)
    summary_text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if check:
        existing_rows = OUTPUT_ROWS.read_text(encoding="utf-8") if OUTPUT_ROWS.exists() else ""
        existing_summary = OUTPUT_SUMMARY.read_text(encoding="utf-8") if OUTPUT_SUMMARY.exists() else ""
        if existing_rows != row_text or existing_summary != summary_text:
            print("lifecycle execution source guard outputs are stale", file=sys.stderr)
            return 1
        return 0
    OUTPUT_ROWS.write_text(row_text, encoding="utf-8")
    OUTPUT_SUMMARY.write_text(summary_text, encoding="utf-8")
    print(json.dumps({
        "runtime_row_count": summary["runtime_row_count"],
        "source_acquisition_required_rows": summary["source_acquisition_required_rows"],
        "replay_attribution_rows": summary["replay_attribution_rows"],
        "selected_source_unit_count": summary["selected_source_unit_count"],
    }, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return write_outputs(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
