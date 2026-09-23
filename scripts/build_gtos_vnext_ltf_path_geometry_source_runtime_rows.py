#!/usr/bin/env python3
"""Build runtime rows for LTF path geometry and source-repair evidence."""

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


DATE = "2026-05-18"
WAVE_ID = "WAVE_LTF_PATH_GEOMETRY_SOURCE_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_ltf_path_geometry_source_runtime"
SOURCE_NAME = "gtos_vnext_ltf_path_geometry_source_runtime_wave"
RUNTIME_SURFACE = "ltf_path_geometry_source_runtime"

SOURCE_BASE = (
    REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
)
OUTPUT_DIR = SOURCE_BASE / "gtos_vnext_research_to_runtime_builder"
OUTPUT_ROWS = (
    OUTPUT_DIR / f"GTOS_VNEXT_LTF_PATH_GEOMETRY_SOURCE_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    OUTPUT_DIR / f"GTOS_VNEXT_LTF_PATH_GEOMETRY_SOURCE_RUNTIME_SUMMARY_{DATE}.json"
)

RUNTIME_SOURCE_FILES = (
    (
        "candidate_ltf_path_order",
        SOURCE_BASE
        / "otb2r_input_only_path_rebuild"
        / "projections"
        / "candidate_ltf_path_order_input_only_projection_2026-05-07.jsonl",
    ),
    (
        "candidate_path_contract_audit",
        SOURCE_BASE
        / "otb2r_input_only_path_rebuild"
        / "projections"
        / "candidate_path_contract_audit_input_only_projection_2026-05-07.jsonl",
    ),
    (
        "candidate_path_follow",
        SOURCE_BASE
        / "otb2r_input_only_path_rebuild"
        / "projections"
        / "candidate_path_follow_input_only_projection_2026-05-07.jsonl",
    ),
    (
        "strategy_follow_candidates",
        SOURCE_BASE
        / "otb2r_input_only_path_rebuild"
        / "projections"
        / "strategy_follow_candidates_input_only_projection_2026-05-07.jsonl",
    ),
    (
        "oti3_g3_geometry_result_rows",
        SOURCE_BASE
        / "oti3_g3_geometry_quarantined_results"
        / "OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
    ),
)

SOURCE_UNITS: tuple[tuple[str, str, int | None], ...] = (
    ("UNIT_011350", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_COMPLETION_AUDIT_2026-05-07.json", 1),
    ("UNIT_011351", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_COMPLETION_AUDIT_2026-05-07.md", 24),
    ("UNIT_011352", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_COVERAGE_AUDIT_2026-05-07.json", 1),
    ("UNIT_011354", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_EXACT_BLOCKER_LEDGER_2026-05-07.json", 1),
    ("UNIT_011355", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_EXACT_BLOCKER_LEDGER_ROWS_2026-05-07.jsonl", 732),
    ("UNIT_011356", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_G12_AUDIT_HANDOFF_2026-05-07.md", 14),
    ("UNIT_011357", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_LABEL_FAMILY_AUDIT_2026-05-07.json", 1),
    ("UNIT_011358", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_NO_LEAK_AUDIT_2026-05-07.json", 1),
    ("UNIT_011359", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_PACKET_CONTRACT_AND_REJECTED_ALTERNATIVES_2026-05-07.md", 19),
    ("UNIT_011360", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_PACKET_MANIFEST_2026-05-07.json", 1),
    ("UNIT_011361", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_PACKET_MANIFEST_2026-05-07.md", 17),
    ("UNIT_011362", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_REJECTED_ALTERNATIVES_LEDGER_2026-05-07.json", 1),
    ("UNIT_011363", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_SAME_BAR_POLICY_2026-05-07.json", 1),
    ("UNIT_011364", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_SOURCE_HASH_LEDGER_2026-05-07.json", 1),
    ("UNIT_011365", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_VERIFICATION_AUDIT_2026-05-07.json", 1),
    ("UNIT_011366", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/OTB2R_G3_GEOMETRY_VERIFICATION_AUDIT_2026-05-07.md", 15),
    ("UNIT_011367", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/packets/OTG0-PKT-031__EXP-G3-DC-OVERSHOOT-002__otb2r_g3_dc_overshoot_input_packet_2026-05-07.json", 1),
    ("UNIT_011368", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/packets/OTG0-PKT-032__EXP-G3-DC-SWING-001__otb2r_g3_dc_swing_input_packet_2026-05-07.json", 1),
    ("UNIT_011369", "research/science_program_2026_05/06_outcome_testing/otb2r_g3_geometry_input_packet_builders/packets/OTG0-PKT-036__EXP-G3-TDA-007__otb2r_g3_tda_h0_embedding_input_packet_2026-05-07.json", 1),
    ("UNIT_011400", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/build_otb2r_input_only_path_rebuild_2026_05_07.py", None),
    ("UNIT_011401", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_COMPLETION_AUDIT_2026-05-07.json", 1),
    ("UNIT_011402", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_COMPLETION_AUDIT_2026-05-07.md", 25),
    ("UNIT_011403", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_COVERAGE_AUDIT_2026-05-07.json", 1),
    ("UNIT_011404", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_COVERAGE_AUDIT_2026-05-07.md", 17),
    ("UNIT_011405", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_DUPLICATE_GROUP_POLICY_2026-05-07.json", 1),
    ("UNIT_011406", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_DUPLICATE_GROUP_POLICY_2026-05-07.md", 9),
    ("UNIT_011407", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_FORBIDDEN_FIELD_SCAN_2026-05-07.json", 1),
    ("UNIT_011408", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_PACKET_MANIFEST_2026-05-07.json", 1),
    ("UNIT_011409", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_PACKET_MANIFEST_2026-05-07.md", 28),
    ("UNIT_011410", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.json", 1),
    ("UNIT_011411", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_SAME_BAR_AMBIGUITY_POLICY_2026-05-07.md", 14),
    ("UNIT_011412", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_SANITIZED_SOURCE_HASHES_2026-05-07.json", 1),
    ("UNIT_011413", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_SANITIZED_SOURCE_HASHES_2026-05-07.md", 11),
    ("UNIT_011415", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-031__EXP-G3-DC-OVERSHOOT-002__otb2r_input_only_path_packet_2026-05-07.json", 1),
    ("UNIT_011416", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-032__EXP-G3-DC-SWING-001__otb2r_input_only_path_packet_2026-05-07.json", 1),
    ("UNIT_011417", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-036__EXP-G3-TDA-007__otb2r_input_only_path_packet_2026-05-07.json", 1),
    ("UNIT_011420", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-052__EXP-G5-AMH-004__otb2r_input_only_path_packet_2026-05-07.json", 1),
    ("UNIT_011421", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-053__EXP-G5-CROWD-001__otb2r_input_only_path_packet_2026-05-07.json", 1),
    ("UNIT_011422", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-056__EXP-G5-PRED-003__otb2r_input_only_path_packet_2026-05-07.json", 1),
    ("UNIT_011423", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-060__G6-EXP-001-OB-VS-GENERIC-RETRACE__otb2r_input_only_path_packet_2026-05-07.json", 1),
    ("UNIT_011424", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__otb2r_input_only_path_packet_2026-05-07.json", 1),
    ("UNIT_011425", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__otb2r_input_only_path_packet_2026-05-07.json", 1),
    ("UNIT_011428", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-074__EXP-G7-LBMA-FIX-004__otb2r_input_only_path_packet_2026-05-07.json", 1),
    ("UNIT_011429", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/packets/OTG0-PKT-075__EXP-G7-USD-REALRATE-001__otb2r_input_only_path_packet_2026-05-07.json", 1),
    ("UNIT_011430", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/projections/candidate_ltf_path_order_input_only_projection_2026-05-07.jsonl", 1985),
    ("UNIT_011431", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/projections/candidate_path_contract_audit_input_only_projection_2026-05-07.jsonl", 921),
    ("UNIT_011432", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/projections/candidate_path_follow_input_only_projection_2026-05-07.jsonl", 1826),
    ("UNIT_011434", "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/projections/strategy_follow_candidates_input_only_projection_2026-05-07.jsonl", 86),
    ("UNIT_011596", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/build_oti3_g3_geometry_quarantined_results_2026_05_07.py", None),
    ("UNIT_011597", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_ALTERNATIVE_PACKETIZATION_REVIEW_2026-05-07.json", 1),
    ("UNIT_011598", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_ALTERNATIVE_PACKETIZATION_REVIEW_2026-05-07.md", 18),
    ("UNIT_011599", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_AMBIGUITY_RESOLUTION_LEDGER_2026-05-07.json", 1),
    ("UNIT_011600", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_AMBIGUITY_RESOLUTION_LEDGER_2026-05-07.md", 7),
    ("UNIT_011601", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_ARTIFACT_MANIFEST_2026-05-07.json", 1),
    ("UNIT_011602", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_BLOCKER_LEDGER_2026-05-07.json", 1),
    ("UNIT_011603", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_BLOCKER_LEDGER_2026-05-07.md", 9),
    ("UNIT_011604", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_COMPLETION_AUDIT_2026-05-07.json", 1),
    ("UNIT_011605", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_COMPLETION_AUDIT_2026-05-07.md", 30),
    ("UNIT_011608", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_LABEL_FAMILY_SEPARATION_REPORT_2026-05-07.json", 1),
    ("UNIT_011609", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_LABEL_FAMILY_SEPARATION_REPORT_2026-05-07.md", 10),
    ("UNIT_011610", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_METHOD_FREEZE_2026-05-07.json", 1),
    ("UNIT_011611", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_METHOD_FREEZE_2026-05-07.md", 24),
    ("UNIT_011612", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_METHODOLOGY_REPORT_2026-05-07.json", 1),
    ("UNIT_011613", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_METHODOLOGY_REPORT_2026-05-07.md", 23),
    ("UNIT_011614", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_RESULT_LEDGER_2026-05-07.json", 1),
    ("UNIT_011615", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_RESULT_LEDGER_2026-05-07.md", 27),
    ("UNIT_011616", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_2026-05-07.jsonl", 199),
    ("UNIT_011617", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_SELF_REVIEW_2026-05-07.json", 1),
    ("UNIT_011618", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_SELF_REVIEW_2026-05-07.md", 8),
    ("UNIT_011619", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json", 1),
    ("UNIT_011620", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/OTI3_G3_GEOMETRY_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.md", 22),
    ("UNIT_011621", "research/science_program_2026_05/06_outcome_testing/oti3_g3_geometry_quarantined_results/verify_oti3_g3_geometry_quarantined_results_2026_05_07.py", None),
)

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "symbol_family",
    "market_timeframe",
    "timeframe",
    "horizon_id",
    "route_session",
    "route_family",
    "side",
    "source_component",
    "source_role",
    "entry_variant",
    "target_stop_order_class",
    "r_evidence_class",
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_payload(payload: Any) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


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


def _session_from_time(value: str) -> str:
    if not value:
        return "off_core_session"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return "off_core_session"
    hour = parsed.hour + parsed.minute / 60.0
    if 0 <= hour < 3:
        return "tokyo_kz"
    if 7 <= hour < 12:
        return "london_core"
    if 13 <= hour < 17:
        return "ny_core"
    return "off_core_session"


def _route_session(row: dict[str, Any]) -> str:
    value = _norm(row.get("session") or row.get("kill_zone"))
    if value:
        lowered = value.casefold()
        if lowered in {"london", "london_core"}:
            return "london_core"
        if lowered in {"ny", "new_york", "ny_core"}:
            return "ny_core"
        if lowered in {"tokyo", "tokyo_kz"}:
            return "tokyo_kz"
        return value
    return _session_from_time(
        _norm(
            row.get("decision_time_utc")
            or row.get("decision_asof_utc")
            or row.get("asof_cutoff_utc")
        )
    )


def _symbol(row: dict[str, Any]) -> str:
    return _norm(row.get("symbol") or row.get("source_symbol") or row.get("broker_symbol"))


def _side(row: dict[str, Any]) -> str:
    packet = row.get("entry_sl_tp_or_level_packet")
    if not isinstance(packet, dict):
        packet = {}
    return _norm(row.get("side") or packet.get("direction") or "UNKNOWN").upper()


def _framework(row: dict[str, Any]) -> str:
    return _norm(row.get("framework") or row.get("experiment_id") or "g3_geometry")


def _timeframe(source_name: str, row: dict[str, Any]) -> str:
    coverage = row.get("source_ohlc_coverage_input_only")
    if isinstance(coverage, dict):
        value = _norm(coverage.get("source_timeframe"))
        if value:
            return value
    if source_name in {"candidate_ltf_path_order", "oti3_g3_geometry_result_rows"}:
        return "M1"
    return "M15"


def _metric(value: float | int | None, *, source_field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    value = float(value)
    return {
        "sum": round(value, 12),
        "count": 1,
        "mean": round(value, 12),
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "match_rows_with_metric": 1,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _behavior(source_name: str, row: dict[str, Any]) -> dict[str, str]:
    ltf_status = _norm(row.get("ltf_status")).upper()
    outcome_status = _norm(row.get("outcome_source_status")).upper()
    terminal_label = _norm(row.get("terminal_label"))
    contract_status = _norm(row.get("path_contract_status")).upper()
    manual_status = _norm(row.get("manual_backfill_status")).upper()

    if ltf_status == "SOURCE_BLOCKED":
        return {
            "decision": "AVOID",
            "review_action": "AVOID_LTF_PATH_SOURCE_BLOCKED",
            "source_component": "ltf_path_source_blocked_guard",
            "source_role": "source_repair_guard",
            "action_class": "ltf_path_source_blocked_avoid_filter",
            "r_evidence_class": "LTF_PATH_SOURCE_REPAIR_REQUIRED",
            "target_stop_order_class": "SOURCE_BLOCKED_NO_M1_PATH",
            "runtime_guard": "source_acquisition_required",
        }
    if outcome_status in {"NO_PRICE_COMPATIBLE_M1_SOURCE", "NO_LOCAL_M1_SOURCE_FOR_SYMBOL"}:
        return {
            "decision": "AVOID",
            "review_action": "AVOID_G3_GEOMETRY_SOURCE_REPAIR_REQUIRED",
            "source_component": "g3_geometry_source_repair_guard",
            "source_role": "source_repair_guard",
            "action_class": "g3_geometry_source_repair_avoid_filter",
            "r_evidence_class": "G3_GEOMETRY_SOURCE_REPAIR_REQUIRED",
            "target_stop_order_class": outcome_status,
            "runtime_guard": "source_acquisition_required",
        }
    if terminal_label == "entry_then_sl_before_tp1":
        return {
            "decision": "AVOID",
            "review_action": "AVOID_G3_GEOMETRY_STOP_FIRST",
            "source_component": "g3_geometry_stop_first_avoid",
            "source_role": "stop_first_risk_guard",
            "action_class": "g3_geometry_stop_first_avoid_filter",
            "r_evidence_class": "G3_GEOMETRY_STOP_FIRST_AVOID",
            "target_stop_order_class": "STOP_FIRST_PROXY_DOMINANT",
            "runtime_guard": "stop_first_zero_risk",
        }
    if terminal_label == "entry_then_tp1_before_sl":
        return {
            "decision": "FOLLOW",
            "review_action": "FOLLOW_G3_GEOMETRY_TARGET_FIRST",
            "source_component": "g3_geometry_target_first_follow",
            "source_role": "positive_path_geometry_support",
            "action_class": "g3_geometry_target_first_follow_pressure",
            "r_evidence_class": "G3_GEOMETRY_POSITIVE_PATH_FOLLOW",
            "target_stop_order_class": "TARGET_FIRST_PROXY_DOMINANT",
            "runtime_guard": "source_bound_positive_path",
        }
    if terminal_label == "tp1_area_reached_without_entry_touch":
        return {
            "decision": "MIXED",
            "review_action": "MIXED_G3_GEOMETRY_ENTRY_MISSED_NOFILL",
            "source_component": "g3_geometry_entry_missed_nofill",
            "source_role": "nofill_entry_geometry_context",
            "action_class": "g3_geometry_entry_missed_retest_redesign_context",
            "r_evidence_class": "G3_GEOMETRY_ENTRY_MISSED_NOFILL_CONTEXT",
            "target_stop_order_class": "NO_FILL_ENTRY_MISSED_TARGET_AREA",
            "runtime_guard": "entry_geometry_redesign_context",
        }
    if terminal_label == "same_m1_ambiguous_entry_terminal" or bool(row.get("same_m1_ambiguity")):
        return {
            "decision": "MIXED",
            "review_action": "MIXED_G3_GEOMETRY_SAME_M1_AMBIGUITY",
            "source_component": "g3_geometry_same_m1_ambiguity_guard",
            "source_role": "ambiguous_path_context",
            "action_class": "g3_geometry_same_m1_ambiguity_context",
            "r_evidence_class": "G3_GEOMETRY_AMBIGUOUS_PATH_CONTEXT",
            "target_stop_order_class": "TARGET_STOP_AMBIGUOUS_OR_MIXED",
            "runtime_guard": "same_m1_ambiguity_pending_guard",
        }
    if ltf_status == "M1_PATH_RECOVERED":
        return {
            "decision": "MIXED",
            "review_action": "MIXED_LTF_PATH_SOURCE_RECOVERED_CONTEXT",
            "source_component": "ltf_path_source_recovered_context",
            "source_role": "source_readiness_context",
            "action_class": "ltf_path_source_recovered_context",
            "r_evidence_class": "LTF_PATH_SOURCE_RECOVERED_CONTEXT",
            "target_stop_order_class": "M1_PATH_RECOVERED",
            "runtime_guard": "source_recovered_context",
        }
    if contract_status.startswith("PATH_CONTRACT_COMPLETE"):
        return {
            "decision": "MIXED",
            "review_action": "MIXED_LTF_PATH_CONTRACT_COMPLETE_CONTEXT",
            "source_component": "ltf_path_contract_complete_context",
            "source_role": "path_contract_context",
            "action_class": "ltf_path_contract_complete_context",
            "r_evidence_class": "LTF_PATH_CONTRACT_COMPLETE_CONTEXT",
            "target_stop_order_class": "PATH_CONTRACT_COMPLETE_WITH_LIMITATIONS",
            "runtime_guard": "path_contract_context",
        }
    if source_name == "strategy_follow_candidates" or manual_status:
        return {
            "decision": "MIXED",
            "review_action": "MIXED_LTF_PATH_STRATEGY_CANDIDATE_CONTEXT",
            "source_component": "ltf_path_strategy_candidate_context",
            "source_role": "candidate_path_context",
            "action_class": "ltf_path_strategy_candidate_context",
            "r_evidence_class": "LTF_PATH_STRATEGY_CANDIDATE_CONTEXT",
            "target_stop_order_class": "CANDIDATE_CONTEXT_NO_TERMINAL_PATH",
            "runtime_guard": "candidate_path_context",
        }
    return {
        "decision": "MIXED",
        "review_action": "MIXED_LTF_PATH_CONTEXT",
        "source_component": "ltf_path_source_context",
        "source_role": "path_geometry_context",
        "action_class": "ltf_path_geometry_context",
        "r_evidence_class": "LTF_PATH_GEOMETRY_CONTEXT",
        "target_stop_order_class": "PATH_CONTEXT",
        "runtime_guard": "path_geometry_context",
    }


def _row_metrics(row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {"effective_n": _metric(1.0, source_field="row")}
    descriptive = _to_float(row.get("descriptive_synthetic_path_r"))
    conservative = _to_float(row.get("conservative_lower_bound_r"))
    m1_bar_count = _to_float(row.get("m1_bar_count"))
    if descriptive is not None:
        metrics["proxy_score"] = _metric(descriptive, source_field="descriptive_synthetic_path_r")
        metrics["descriptive_synthetic_path_r"] = _metric(descriptive, source_field="descriptive_synthetic_path_r")
    if conservative is not None:
        metrics["cost_adjusted_simulated_r"] = _metric(
            conservative,
            source_field="conservative_lower_bound_r",
        )
    if m1_bar_count is not None:
        metrics["source_event_rows"] = _metric(m1_bar_count, source_field="m1_bar_count")
    return {key: value for key, value in metrics.items() if value is not None}


def _build_runtime_row(
    *,
    source_name: str,
    source_path: Path,
    source_hash: str,
    source_line_no: int,
    row: dict[str, Any],
) -> dict[str, Any]:
    behavior = _behavior(source_name, row)
    symbol = _symbol(row)
    timeframe = _timeframe(source_name, row)
    route_session = _route_session(row)
    side = _side(row)
    source_row_id = _norm(
        row.get("row_key")
        or row.get("outcome_row_hash")
        or row.get("projection_hash")
        or row.get("candidate_id")
        or f"{source_name}:{source_line_no}"
    )
    runtime_id = f"ltf_path_geometry_source:{_sha256_payload([source_name, source_line_no, source_row_id])[:24]}"
    source_symbol = _norm(row.get("source_symbol")) or symbol
    symbol_family = resolve_vnext_symbol_family(symbol) or symbol
    event_scope = {
        "symbol": symbol,
        "source_symbol": source_symbol,
        "market": symbol,
        "symbol_family": symbol_family,
        "market_timeframe": timeframe,
        "timeframe": timeframe,
        "horizon_id": "m1_path_window" if timeframe == "M1" else "m15_candidate_window",
        "route_session": route_session,
        "route_family": RUNTIME_SURFACE,
        "side": side,
        "source_component": behavior["source_component"],
        "source_role": behavior["source_role"],
        "entry_variant": _norm(row.get("source_name") or source_name),
        "target_stop_order_class": behavior["target_stop_order_class"],
        "r_evidence_class": behavior["r_evidence_class"],
    }
    packet = row.get("entry_sl_tp_or_level_packet")
    if not isinstance(packet, dict):
        packet = {}
    trade_parameters = row.get("trade_parameters")
    if not isinstance(trade_parameters, dict):
        trade_parameters = {}
    source_repair_required = behavior["runtime_guard"] in {
        "source_acquisition_required",
        "source_repair_required",
    }
    return {
        "schema_version": "gtos_vnext_ltf_path_geometry_source_runtime_v1",
        "wave_id": WAVE_ID,
        "runtime_surface": RUNTIME_SURFACE,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "source_group": source_name,
        "source_artifact": _repo_path(source_path),
        "source_artifact_sha256": source_hash,
        "source_line_no": source_line_no,
        "source_row_id": source_row_id,
        "row_key": f"{runtime_id}:{source_row_id}",
        "ltf_path_geometry_source_runtime_row_id": runtime_id,
        "decision": behavior["decision"],
        "review_action": behavior["review_action"],
        "action_class": behavior["action_class"],
        "source_component": behavior["source_component"],
        "source_role": behavior["source_role"],
        "r_evidence_class": behavior["r_evidence_class"],
        "target_stop_order_class": behavior["target_stop_order_class"],
        "system_surface": RUNTIME_SURFACE,
        "event_scope": event_scope,
        "symbol": symbol,
        "source_symbol": source_symbol,
        "market": symbol,
        "symbol_family": symbol_family,
        "framework": _framework(row),
        "timeframe": timeframe,
        "market_timeframe": timeframe,
        "route_session": route_session,
        "horizon_id": event_scope["horizon_id"],
        "route_family": RUNTIME_SURFACE,
        "side": side,
        "entry_variant": event_scope["entry_variant"],
        "source_status": _norm(
            row.get("ltf_status")
            or row.get("outcome_source_status")
            or row.get("path_contract_status")
            or row.get("manual_backfill_status")
            or row.get("analysis_decision")
        ),
        "terminal_label": _norm(row.get("terminal_label")),
        "path_contract_status": _norm(row.get("path_contract_status")),
        "ltf_status": _norm(row.get("ltf_status")),
        "outcome_source_status": _norm(row.get("outcome_source_status")),
        "same_m1_ambiguity": bool(row.get("same_m1_ambiguity")),
        "source_repair_required": source_repair_required,
        "source_acquisition_required": source_repair_required,
        "source_complete": True,
        "runtime_evidence_executable": True,
        "risk_zero_when_activated": behavior["decision"] == "AVOID" or source_repair_required,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "broker_operation_permitted": False,
        "live_execution_permitted": False,
        "replay_shadow_activation_path": (
            "load artifact via gtos_vnext_runtime.artifact_paths; replay or shadow "
            "pre-AI/post-L2 route decisions before broker execution"
        ),
        "fresh_moonshot_cp_evidence_override_allowed": False,
        "legacy_cannot_override_fresher_cp280_cp281_cp282": True,
        "stale_legacy_assumption_override_blocked": True,
        "implementation_action": (
            "EXECUTE_SOURCE_REPAIR_OR_ZERO_RISK_GUARD"
            if source_repair_required
            else "MERGE_AS_LTF_PATH_GEOMETRY_RUNTIME_CONTEXT"
        ),
        "r_metric_traces": _row_metrics(row),
        "source_event_rows": int(_to_float(row.get("m1_bar_count")) or 1),
        "entry_price": packet.get("entry_price") or trade_parameters.get("entry_price"),
        "stop_loss": packet.get("stop_loss") or trade_parameters.get("stop_loss"),
        "take_profit_1": packet.get("take_profit_1") or trade_parameters.get("take_profit_1"),
        "decision_time_utc": _norm(row.get("decision_time_utc") or row.get("decision_asof_utc")),
        "asof_latest_candle_utc": _norm(row.get("asof_latest_candle_utc") or row.get("asof_cutoff_utc")),
        "no_leak_status": _norm(row.get("no_leak_status")),
        "promotion_verdict": _norm(row.get("promotion_verdict")),
        "source_payload_hash": _sha256_payload(row),
    }


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_name, source_path in RUNTIME_SOURCE_FILES:
        source_hash = _sha256_file(source_path)
        for line_no, row in enumerate(_read_jsonl(source_path), start=1):
            rows.append(
                _build_runtime_row(
                    source_name=source_name,
                    source_path=source_path,
                    source_hash=source_hash,
                    source_line_no=line_no,
                    row=row,
                )
            )
    rows.sort(key=lambda item: item["ltf_path_geometry_source_runtime_row_id"])
    return rows


def _coverage_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    mapping = {
        "symbols": "symbol",
        "source_symbols": "source_symbol",
        "markets": "market",
        "timeframes": "timeframe",
        "sessions": "route_session",
        "sides": "side",
        "frameworks": "framework",
        "horizon_ids": "horizon_id",
        "entry_variants": "entry_variant",
        "target_stop_order_classes": "target_stop_order_class",
    }
    return {
        label: dict(sorted(Counter(row.get(field) or "" for row in rows).items()))
        for label, field in mapping.items()
    }


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def _source_artifacts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_path = Counter(row["source_artifact"] for row in rows)
    artifacts: list[dict[str, Any]] = []
    for source_name, source_path in RUNTIME_SOURCE_FILES:
        repo_path = _repo_path(source_path)
        artifacts.append(
            {
                "source_name": source_name,
                "path": repo_path,
                "hash": _sha256_file(source_path),
                "row_count": len(_read_jsonl(source_path)),
                "runtime_rows_read": by_path.get(repo_path, 0),
            }
        )
    return artifacts


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_artifacts = _source_artifacts(rows)
    decision_counts = Counter(row["decision"] for row in rows)
    source_component_counts = Counter(row["source_component"] for row in rows)
    r_evidence_class_counts = Counter(row["r_evidence_class"] for row in rows)
    source_status_counts = Counter(row["source_status"] for row in rows)
    terminal_label_counts = Counter(row["terminal_label"] for row in rows)
    return {
        "schema_version": "gtos_vnext_ltf_path_geometry_source_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "runtime_surface": RUNTIME_SURFACE,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": len(rows),
        "wave_source_rows_counted": sum(row_count or 0 for _, _, row_count in SOURCE_UNITS),
        "selected_open_unit_count": len(SOURCE_UNITS),
        "row_count_unknown_unit_count": sum(1 for _, _, row_count in SOURCE_UNITS if row_count is None),
        "runtime_candidate_use_permitted_rows": sum(
            1 for row in rows if row.get("runtime_candidate_use_permitted")
        ),
        "candidate_use_allowed_now_rows": sum(
            1 for row in rows if row.get("candidate_use_allowed_now")
        ),
        "broker_operation_permitted_rows": sum(
            1 for row in rows if row.get("broker_operation_permitted")
        ),
        "source_acquisition_required_rows": sum(
            1 for row in rows if row.get("source_acquisition_required")
        ),
        "risk_zero_when_activated_rows": sum(
            1 for row in rows if row.get("risk_zero_when_activated")
        ),
        "positive_path_follow_rows": r_evidence_class_counts.get(
            "G3_GEOMETRY_POSITIVE_PATH_FOLLOW", 0
        ),
        "stop_first_avoid_rows": r_evidence_class_counts.get(
            "G3_GEOMETRY_STOP_FIRST_AVOID", 0
        ),
        "entry_missed_nofill_context_rows": r_evidence_class_counts.get(
            "G3_GEOMETRY_ENTRY_MISSED_NOFILL_CONTEXT", 0
        ),
        "same_m1_ambiguity_context_rows": r_evidence_class_counts.get(
            "G3_GEOMETRY_AMBIGUOUS_PATH_CONTEXT", 0
        ),
        "source_repair_required_rows": (
            r_evidence_class_counts.get("LTF_PATH_SOURCE_REPAIR_REQUIRED", 0)
            + r_evidence_class_counts.get("G3_GEOMETRY_SOURCE_REPAIR_REQUIRED", 0)
        ),
        "decision_counts": dict(sorted(decision_counts.items())),
        "r_evidence_class_counts": dict(sorted(r_evidence_class_counts.items())),
        "source_component_counts": dict(sorted(source_component_counts.items())),
        "source_role_counts": dict(sorted(Counter(row["source_role"] for row in rows).items())),
        "source_status_counts": dict(sorted(source_status_counts.items())),
        "terminal_label_counts": dict(sorted(terminal_label_counts.items())),
        "coverage_counts": _coverage_counts(rows),
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "source_artifacts": source_artifacts,
        "selected_source_units": [
            {"unit_id": unit_id, "path": path, "row_count": row_count}
            for unit_id, path, row_count in SOURCE_UNITS
        ],
        "expected_runtime_effect": (
            "LTF path source-blocked and G3 no-source rows zero execution risk "
            "through source-repair guards; G3 stop-first rows become AVOID "
            "pressure; G3 target-first rows add scoped FOLLOW pressure; recovered "
            "path, contract-complete, candidate, missed-entry, and same-M1 rows "
            "remain route-context/no-fill geometry pressure for replay/shadow."
        ),
    }


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _read_existing_jsonl(path: Path) -> list[dict[str, Any]]:
    return _read_jsonl(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows = build_rows()
    summary = build_summary(rows)
    if args.check:
        existing_rows = _read_existing_jsonl(OUTPUT_ROWS)
        existing_summary = json.loads(OUTPUT_SUMMARY.read_text(encoding="utf-8"))
        if existing_rows != rows or existing_summary != summary:
            raise SystemExit("generated LTF path geometry source runtime rows are stale")
    else:
        write_outputs(rows, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
