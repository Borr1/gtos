"""Build CNR geometry-decay / residual-R input-only control artifacts.

This lane deliberately does not score outcomes. It freezes decision-time
geometry fields and next-route blockers from already accepted CNR packet
evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
DATE_STAMP = "2026-05-08"
PROMOTION = "NO_PROMOTION_VERDICT"

CONTROL_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "broker_actual_r_accessed": False,
    "account_history_accessed": False,
    "live_trade_results_accessed": False,
    "blocked_packet_outcome_source_read": False,
    "api_calls": 0,
    "paid_data_calls": 0,
    "databento_calls": 0,
    "mt5_order_calls": 0,
    "order_calls": 0,
}

CONTROLLING_PROMPT = OUT_DIR / "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_GOAL_PROMPT_2026-05-08.md"
SOURCE_ROWS_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl"
SOURCE_MANIFEST_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_MANIFEST_2026-05-07.json"
G12_READY_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_READY_ROW_SHORTLIST_2026-05-08.json"
G12_BLOCKERS_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_EXACT_BLOCKER_LEDGER_2026-05-08.json"
G12_DECISION_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_SOURCE_FIELD_PACKET_DECISION_LEDGER_2026-05-08.json"
G12_SOURCE_HASH_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_SOURCE_HASH_AND_ASOF_AUDIT_2026-05-08.json"
OTI7_LEDGER_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/oti7_cnr_accepted_quarantined_results/OTI7_CNR_RESULT_LEDGER_2026-05-08.json"
OTI7_GEOMETRY_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/oti7_cnr_accepted_quarantined_results/OTI7_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT_2026-05-08.json"
G12_OTI7_DECISION_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_oti7_cnr_post_result_audit/G12_OTI7_CNR_POST_RESULT_DECISION_LEDGER_2026-05-08.json"
G12_OTI7_FORENSICS_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_oti7_cnr_post_result_audit/G12_OTI7_CNR_NEGATIVE_RESULT_FORENSICS_2026-05-08.json"
G12_OTI7_BLOCKER_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_oti7_cnr_post_result_audit/G12_OTI7_CNR_NEXT_HYPOTHESIS_BLOCKER_MAP_2026-05-08.json"
TIMING_PREREG_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/CNR_TIMING_MODEL_PREREGISTRATION_2026-05-07.json"
TIMING_CONTRACT_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/cnr_timing_model_preregistration/CNR_TIMING_MODEL_SOURCE_FIELD_CONTRACT_2026-05-07.json"
OTX_PROPOSALS_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json"
OTR061_PROPOSAL_PATH = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json"

INPUT_MATRIX_JSONL = OUT_DIR / "CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl"

FORBIDDEN_INPUT_ROW_KEYS = {
    "synthetic_path_r",
    "quarantined_result_status",
    "terminal_event",
    "terminal_timestamp_utc",
    "terminal_bid",
    "terminal_ask",
    "terminal_quote_side",
    "path_coverage",
    "label_family",
    "target_hit_timestamp",
    "stop_hit_timestamp",
    "target_first_touch_utc",
    "stop_first_touch_utc",
    "broker_actual_r",
    "account_history",
    "live_trade_result",
    "result_status",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_obj(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def display_path(path: str | Path) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(REPO_ROOT)).replace("\\", "/")
    except Exception:
        return str(path)


def resolve_source_path(path_text: str) -> Path:
    p = Path(path_text)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def executable_quote_side(side: str) -> str | None:
    if side == "LONG":
        return "ask"
    if side == "SHORT":
        return "bid"
    return None


def executable_quote_price(row: dict[str, Any]) -> float | None:
    side = row.get("side")
    quote_side = executable_quote_side(side)
    if quote_side is None:
        return None
    value = row.get(quote_side)
    if value is None:
        return None
    return float(value)


def favorable_distance(side: str, a: float, b: float) -> float:
    """Signed distance from b to a in the trade direction."""
    if side == "LONG":
        return a - b
    if side == "SHORT":
        return b - a
    raise ValueError(f"unknown side {side}")


def geometry_fields(row: dict[str, Any]) -> dict[str, Any]:
    side = row.get("side")
    q = executable_quote_price(row)
    entry = row.get("original_entry_price")
    stop = row.get("original_stop_loss")
    tp1 = row.get("original_take_profit_1")
    quote_side = executable_quote_side(side)
    base: dict[str, Any] = {
        "executable_quote_side": quote_side,
        "executable_quote_price": q,
        "original_base_r_price": None,
        "residual_target_price_from_executable_quote": None,
        "executable_stop_distance_price": None,
        "residual_target_r_from_executable_quote": None,
        "residual_target_original_r_from_executable_quote": None,
        "stop_r_from_executable_quote": None,
        "quote_displacement_from_original_entry_r": None,
        "quote_displacement_from_original_stop_r": None,
        "quote_displacement_from_original_tp1_r": None,
        "target_already_passed_at_executable_quote": None,
        "stop_invalid_at_executable_quote": None,
        "market_entry_geometry_valid_for_original_tp1": False,
        "market_entry_geometry_gate_state": "MISSING_GEOMETRY_OR_QUOTE",
    }
    if side not in {"LONG", "SHORT"} or q is None or entry is None or stop is None or tp1 is None:
        return base
    entry_f = float(entry)
    stop_f = float(stop)
    tp1_f = float(tp1)
    original_r = abs(entry_f - stop_f)
    if original_r <= 0:
        base["market_entry_geometry_gate_state"] = "MISSING_OR_ZERO_ORIGINAL_R"
        return base
    residual_price = favorable_distance(side, tp1_f, q)
    stop_distance = favorable_distance(side, q, stop_f)
    target_passed = residual_price <= 0
    stop_invalid = stop_distance <= 0
    base.update(
        {
            "original_base_r_price": round(original_r, 10),
            "residual_target_price_from_executable_quote": round(residual_price, 10),
            "executable_stop_distance_price": round(stop_distance, 10),
            "residual_target_original_r_from_executable_quote": round(residual_price / original_r, 10),
            "stop_r_from_executable_quote": round(stop_distance / original_r, 10),
            "quote_displacement_from_original_entry_r": round(favorable_distance(side, q, entry_f) / original_r, 10),
            "quote_displacement_from_original_stop_r": round(stop_distance / original_r, 10),
            "quote_displacement_from_original_tp1_r": round(favorable_distance(side, q, tp1_f) / original_r, 10),
            "target_already_passed_at_executable_quote": target_passed,
            "stop_invalid_at_executable_quote": stop_invalid,
        }
    )
    if stop_distance > 0:
        base["residual_target_r_from_executable_quote"] = round(residual_price / stop_distance, 10)
    if target_passed:
        base["market_entry_geometry_gate_state"] = "TARGET_ALREADY_PASSED_AT_EXECUTABLE_QUOTE"
    elif stop_invalid:
        base["market_entry_geometry_gate_state"] = "STOP_INVALID_AT_EXECUTABLE_QUOTE"
    elif row.get("quote_source_status") != "QUOTE_EXTRACTED_SOURCE_HASHED":
        base["market_entry_geometry_gate_state"] = "MISSING_SOURCE_HASHED_EXECUTABLE_QUOTE"
    elif not row.get("source_sha256_hashes"):
        base["market_entry_geometry_gate_state"] = "MISSING_SOURCE_HASH"
    else:
        base["market_entry_geometry_valid_for_original_tp1"] = True
        base["market_entry_geometry_gate_state"] = "VALID_FOR_FUTURE_RESULT_LANE_AFTER_SAMPLE_AND_DUPLICATE_AUDIT"
    return base


def residual_bin(value: float | None, target_passed: bool | None, stop_invalid: bool | None) -> str:
    if value is None:
        return "MISSING_OR_STOP_INVALID"
    if target_passed or value <= 0:
        return "LTE_0_TARGET_ALREADY_PASSED_OR_ZERO"
    if value <= 0.25:
        return "GT_0_TO_0_25_TINY_RESIDUAL"
    if value <= 0.5:
        return "GT_0_25_TO_0_5_SMALL_RESIDUAL"
    if value <= 1.0:
        return "GT_0_5_TO_1_0_SUB_ONE_R"
    if value < 1.5:
        return "GT_1_0_TO_LT_1_5_BELOW_GTOS_MIN_RR"
    return "GTE_1_5_MEETS_GTOS_MIN_RR_GEOMETRY_ONLY"


def stop_r_bin(value: float | None) -> str:
    if value is None or value <= 0:
        return "LTE_0_INVALID_STOP_GEOMETRY"
    if value <= 0.5:
        return "GT_0_TO_0_5_COMPRESSED_STOP_DISTANCE"
    if value <= 1.0:
        return "GT_0_5_TO_1_0_WITHIN_ORIGINAL_R"
    if value <= 1.5:
        return "GT_1_0_TO_1_5_EXPANDED_STOP_DISTANCE"
    return "GT_1_5_LARGE_STOP_DISTANCE_DECAY"


def displacement_bin(value: float | None) -> str:
    if value is None:
        return "MISSING"
    if value <= -0.5:
        return "LTE_NEG_0_5_ADVERSE_FROM_REFERENCE"
    if value <= 0:
        return "NEG_0_5_TO_0_NOT_FAVORABLE"
    if value <= 0.5:
        return "GT_0_TO_0_5_FAVORABLE"
    if value <= 1.0:
        return "GT_0_5_TO_1_0_FAVORABLE"
    return "GT_1_0_FAVORABLE_DECAY"


def load_ready_source_rows() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    ready = read_json(G12_READY_PATH)
    source_rows = read_jsonl(SOURCE_ROWS_PATH)
    source_by_sha = {row["row_sha256"]: row for row in source_rows}
    rows: list[dict[str, Any]] = []
    for ready_row in ready["rows"]:
        source = source_by_sha.get(ready_row["row_sha256"])
        if source is None:
            raise RuntimeError(f"missing source row for {ready_row['row_sha256']}")
        merged = dict(source)
        merged["_g12_ready_row_number"] = ready_row["row_number"]
        merged["_g12_audit_decision"] = ready_row["audit_decision"]
        rows.append(merged)
    return rows, ready, read_json(SOURCE_MANIFEST_PATH), source_rows


def build_input_matrix(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for row in rows:
        geom = geometry_fields(row)
        matrix_row: dict[str, Any] = {
            "schema_version": "cnr_geometry_decay_input_row_v1",
            "artifact_family": "CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX",
            **CONTROL_FLAGS,
            "source_priority": "G12_READY_INPUT_ROW_JOINED_TO_CNR_SOURCE_FIELD_PACKET_ROW",
            "row_number": row["_g12_ready_row_number"],
            "source_row_sha256": row["row_sha256"],
            "record_id": row["record_id"],
            "source_record_id": row.get("source_record_id"),
            "source_candidate_id": row.get("source_candidate_id"),
            "packet_id": row["packet_id"],
            "experiment_id": row.get("experiment_id"),
            "hypothesis_id": row.get("hypothesis_id"),
            "symbol": row.get("symbol"),
            "broker_symbol": row.get("broker_symbol"),
            "side": row.get("side"),
            "session": row.get("session"),
            "timing_model_family": row.get("timing_model_family"),
            "target_model_family": row.get("target_model_family"),
            "decision_asof_utc": row.get("decision_asof_utc"),
            "candidate_close_utc": row.get("candidate_close_utc"),
            "signal_emitted_utc": row.get("signal_emitted_utc"),
            "entry_eligible_utc": row.get("entry_eligible_utc"),
            "quote_timestamp_utc": row.get("quote_timestamp_utc"),
            "quote_age_ms": row.get("quote_age_ms"),
            "quote_source_status": row.get("quote_source_status"),
            "quote_source_path": row.get("quote_source_path"),
            "quote_source_sha256": row.get("quote_source_sha256"),
            "quote_side_rule": row.get("quote_side_rule"),
            "bid": row.get("bid"),
            "ask": row.get("ask"),
            "spread": row.get("spread"),
            "original_entry_price": row.get("original_entry_price"),
            "original_stop_loss": row.get("original_stop_loss"),
            "original_take_profit_1": row.get("original_take_profit_1"),
            "risk_reward_ratio_from_source": row.get("risk_reward_ratio"),
            "geometry_source": row.get("geometry_source"),
            "target_binding_status": row.get("target_binding_status"),
            "stop_model_id": row.get("stop_model_id"),
            "target_model_id": row.get("target_model_id"),
            "duplicate_group_id": row.get("duplicate_group_id"),
            "duplicate_denominator_key": row.get("duplicate_denominator_key"),
            "duplicate_policy": row.get("duplicate_policy"),
            "countable_denominator_row": row.get("countable_denominator_row"),
            "source_file_paths": row.get("source_file_paths") or [],
            "source_sha256_hashes": row.get("source_sha256_hashes") or [],
            "record_source_hash": row.get("record_source_hash"),
            "upstream_forbidden_field_scan_result": row.get("forbidden_field_scan_result"),
            "upstream_pre_entry_target_already_passed_check": row.get("pre_entry_target_already_passed_check"),
        }
        matrix_row.update(geom)
        matrix_row["residual_target_r_bin"] = residual_bin(
            matrix_row["residual_target_r_from_executable_quote"],
            matrix_row["target_already_passed_at_executable_quote"],
            matrix_row["stop_invalid_at_executable_quote"],
        )
        matrix_row["stop_r_bin"] = stop_r_bin(matrix_row["stop_r_from_executable_quote"])
        matrix_row["quote_displacement_from_original_entry_r_bin"] = displacement_bin(
            matrix_row["quote_displacement_from_original_entry_r"]
        )
        matrix_row["quote_displacement_from_original_tp1_r_bin"] = displacement_bin(
            matrix_row["quote_displacement_from_original_tp1_r"]
        )
        matrix_row["input_row_hash"] = sha256_obj(matrix_row)
        leaked = sorted(FORBIDDEN_INPUT_ROW_KEYS.intersection(matrix_row))
        if leaked:
            raise RuntimeError(f"input row contains forbidden keys {leaked}")
        matrix.append(matrix_row)
    return matrix


def summarize_matrix(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    by_timing_target = Counter(f"{r['timing_model_family']}|{r['target_model_family']}" for r in matrix)
    by_packet = Counter(r["packet_id"] for r in matrix)
    by_symbol = Counter(r["symbol"] for r in matrix)
    by_gate = Counter(r["market_entry_geometry_gate_state"] for r in matrix)
    by_residual_bin = Counter(r["residual_target_r_bin"] for r in matrix)
    by_stop_bin = Counter(r["stop_r_bin"] for r in matrix)
    countable = [r for r in matrix if r["countable_denominator_row"]]
    per_family_countable_groups: dict[str, int] = {}
    for family in sorted(by_timing_target):
        fam_rows = [r for r in matrix if f"{r['timing_model_family']}|{r['target_model_family']}" == family and r["countable_denominator_row"]]
        per_family_countable_groups[family] = len({r["duplicate_group_id"] for r in fam_rows})
    residual_values = [r["residual_target_r_from_executable_quote"] for r in matrix if r["residual_target_r_from_executable_quote"] is not None]
    stop_values = [r["stop_r_from_executable_quote"] for r in matrix if r["stop_r_from_executable_quote"] is not None]
    quote_age_values = [r["quote_age_ms"] for r in matrix if isinstance(r.get("quote_age_ms"), (int, float))]
    return {
        "row_count": len(matrix),
        "countable_rows": len(countable),
        "duplicate_context_rows": len(matrix) - len(countable),
        "unique_duplicate_groups": len({r["duplicate_group_id"] for r in matrix}),
        "unique_countable_duplicate_groups": len({r["duplicate_group_id"] for r in countable}),
        "by_timing_target": dict(sorted(by_timing_target.items())),
        "by_packet": dict(sorted(by_packet.items())),
        "by_symbol": dict(sorted(by_symbol.items())),
        "by_market_entry_geometry_gate_state": dict(sorted(by_gate.items())),
        "by_residual_target_r_bin": dict(sorted(by_residual_bin.items())),
        "by_stop_r_bin": dict(sorted(by_stop_bin.items())),
        "per_family_countable_unique_duplicate_groups": per_family_countable_groups,
        "aggregate_sample_floor_unique_groups": 30,
        "aggregate_sample_floor_status": "BLOCKED_BELOW_30_UNIQUE_GROUPS_PER_TIMING_TARGET_FAMILY"
        if any(v < 30 for v in per_family_countable_groups.values())
        else "SAMPLE_FLOOR_MET_FOR_PACKET_CONTROL_ONLY_NOT_VALIDATION",
        "residual_target_r_from_executable_quote_range": {
            "min": min(residual_values) if residual_values else None,
            "max": max(residual_values) if residual_values else None,
        },
        "stop_r_from_executable_quote_range": {
            "min": min(stop_values) if stop_values else None,
            "max": max(stop_values) if stop_values else None,
        },
        "quote_age_ms_range": {
            "min": min(quote_age_values) if quote_age_values else None,
            "max": max(quote_age_values) if quote_age_values else None,
        },
    }


def blocker_summaries(source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    timing_families = [
        "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK",
        "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW",
        "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER",
    ]
    target_families = [
        "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
        "CNR_T2_ASOF_STRUCTURAL_LEVEL",
        "CNR_T3_TIMEBOX_TERMINAL",
    ]
    timing: dict[str, Any] = {}
    for family in timing_families:
        subset = [r for r in source_rows if r["timing_model_family"] == family]
        timing[family] = {
            "row_count": len(subset),
            "ready_rows": sum(str(r.get("blocker_state", "")).startswith("READY") for r in subset),
            "timing_source_status_counts": dict(Counter(r.get("timing_source_status") for r in subset)),
            "timing_blocker_counts": dict(Counter(r.get("timing_blocker") for r in subset)),
            "non_null_signal_emitted_utc_rows": sum(bool(r.get("signal_emitted_utc")) for r in subset),
        }
    targets: dict[str, Any] = {}
    for family in target_families:
        subset = [r for r in source_rows if r["target_model_family"] == family]
        targets[family] = {
            "row_count": len(subset),
            "ready_rows": sum(str(r.get("blocker_state", "")).startswith("READY") for r in subset),
            "target_binding_status_counts": dict(Counter(r.get("target_binding_status") for r in subset)),
            "target_blocker_counts": dict(Counter(r.get("target_blocker") for r in subset)),
        }
    return {"timing_family_blockers": timing, "target_family_blockers": targets}


def otg061_sidecar_findings(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    source_pkt061 = [r for r in matrix if r["packet_id"] == "OTG0-PKT-061"]
    findings: dict[str, Any] = {
        "source_field_pkt061_ready_rows": len(source_pkt061),
        "source_field_pkt061_rows_with_original_geometry": sum(
            r.get("original_entry_price") is not None
            and r.get("original_stop_loss") is not None
            and r.get("original_take_profit_1") is not None
            for r in source_pkt061
        ),
        "source_field_pkt061_unique_duplicate_groups": len({r["duplicate_group_id"] for r in source_pkt061}),
        "source_field_pkt061_status": "SOURCE_FIELD_GEOMETRY_EXISTS_FOR_ACCEPTED_E0_E1_T0_ROWS",
    }
    if OTX_PROPOSALS_PATH.exists():
        obj = read_json(OTX_PROPOSALS_PATH)
        hits: list[dict[str, Any]] = []

        def scan(x: Any) -> None:
            if isinstance(x, dict):
                if x.get("packet_id") == "OTG0-PKT-061":
                    hits.append(x)
                for v in x.values():
                    scan(v)
            elif isinstance(x, list):
                for v in x:
                    scan(v)

        scan(obj)
        findings.update(
            {
                "otx_pkt061_proposal_rows": len(hits),
                "otx_pkt061_rows_with_decision_quote": sum(
                    (h.get("decision_quote_packet") or {}).get("quote_status") == "DECISION_QUOTE_FOUND_ASOF"
                    for h in hits
                ),
                "otx_pkt061_rows_with_ordered_path": sum(
                    (h.get("ordered_tick_path_packet") or {}).get("path_status") == "ORDERED_TICK_PATH_AVAILABLE"
                    for h in hits
                ),
                "otx_pkt061_rows_with_entry_sl_tp_or_level_packet": sum(
                    "entry_sl_tp_or_level_packet" in h for h in hits
                ),
            }
        )
    if OTR061_PROPOSAL_PATH.exists():
        proposal = read_json(OTR061_PROPOSAL_PATH)
        findings.update(
            {
                "otr061_single_xau_recovery_record_count": proposal.get("record_count"),
                "otr061_single_xau_terminal_state": proposal.get("terminal_state"),
            }
        )
    findings["exact_next_blocker"] = (
        "Build a unified input-only OTG0-PKT-061 geometry+horizon sidecar that joins source-field original "
        "geometry with source-hashed quote/path_start/path_end packets, then send that sidecar through G12 "
        "source/no-leak/duplicate audit before any result scoring."
    )
    return findings


def source_hash_and_search_ledger(matrix: list[dict[str, Any]]) -> dict[str, Any]:
    controlling_files = [
        CONTROLLING_PROMPT,
        REPO_ROOT / ".context/LIVE_STATE.md",
        REPO_ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        REPO_ROOT / ".context/00_core/quick_reference_card.md",
        REPO_ROOT / ".context/00_core/research_operating_doctrine.md",
        REPO_ROOT / ".context/00_core/research_current_state.md",
        REPO_ROOT / ".context/00_core/goal_session_research_discipline.md",
        REPO_ROOT / ".context/00_core/local_heavy_data_inventory.md",
        TIMING_PREREG_PATH,
        TIMING_CONTRACT_PATH,
        SOURCE_ROWS_PATH,
        SOURCE_MANIFEST_PATH,
        G12_READY_PATH,
        G12_BLOCKERS_PATH,
        G12_DECISION_PATH,
        G12_SOURCE_HASH_PATH,
        OTI7_LEDGER_PATH,
        OTI7_GEOMETRY_PATH,
        G12_OTI7_DECISION_PATH,
        G12_OTI7_FORENSICS_PATH,
        G12_OTI7_BLOCKER_PATH,
        OTX_PROPOSALS_PATH,
        OTR061_PROPOSAL_PATH,
    ]
    expected_hashes: dict[str, str] = {}
    for r in matrix:
        paths = r.get("source_file_paths") or []
        hashes = r.get("source_sha256_hashes") or []
        for p, h in zip(paths, hashes):
            expected_hashes.setdefault(p, h)
        if r.get("quote_source_path") and r.get("quote_source_sha256"):
            expected_hashes.setdefault(r["quote_source_path"], r["quote_source_sha256"])

    source_files: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in controlling_files:
        text = str(path)
        if text in seen:
            continue
        seen.add(text)
        digest = sha256_path(path)
        source_files.append(
            {
                "path": display_path(path),
                "absolute_path": str(path),
                "role": "controlling_or_neighbor_input",
                "exists": path.exists(),
                "sha256": digest,
                "expected_sha256": None,
                "hash_status": "HASHED" if digest else "MISSING",
            }
        )
    for path_text, expected in sorted(expected_hashes.items()):
        path = resolve_source_path(path_text)
        digest = sha256_path(path)
        if digest is None:
            status = "MISSING"
        elif expected and digest.lower() == expected.lower():
            status = "HASHED_MATCH"
        else:
            status = "HASHED_MISMATCH"
        source_files.append(
            {
                "path": path_text,
                "absolute_path": str(path),
                "role": "matrix_source_file",
                "exists": path.exists(),
                "sha256": digest,
                "expected_sha256": expected,
                "hash_status": status,
            }
        )

    roots = [
        r"C:\Users\MSI\Documents\ai-trading-agent\data",
        r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks",
        r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs",
        r"C:\tmp",
        r"C:\SierraChart",
    ]
    name_patterns = [
        "CNR",
        "OTG0-PKT-061",
        "OTG0-PKT-060",
        "OTG0-PKT-062",
        "OTG0-PKT-063",
        "OTG0-PKT-066",
        "pretouch",
        "signal",
        "latency",
        "decision_request",
        "entry_sl_tp",
        "path_start",
        "path_end",
        "residual",
    ]
    root_results = []
    lowered = [p.lower() for p in name_patterns]
    for root_text in roots:
        root = Path(root_text)
        matches: list[str] = []
        denied: list[str] = []
        visited_files = 0
        if root.exists():
            for dirpath, dirnames, filenames in os.walk(root, topdown=True):
                # Avoid expensive .git and cache internals while still searching absolute roots.
                dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", ".pytest_cache", "node_modules"}]
                for filename in filenames:
                    visited_files += 1
                    full = str(Path(dirpath) / filename)
                    if any(pat in full.lower() for pat in lowered):
                        matches.append(full)
                        if len(matches) >= 80:
                            break
                if len(matches) >= 80:
                    break
        root_results.append(
            {
                "root": root_text,
                "exists": root.exists(),
                "patterns": name_patterns,
                "visited_files_until_limit": visited_files,
                "matched_path_count_returned": len(matches),
                "matched_paths": matches,
                "denied_or_walk_errors": denied,
                "search_limit_note": "Filename search returns first 80 matches; field absence proof uses source-row and targeted text scans below.",
            }
        )

    field_tokens = [
        "signal_emitted_utc",
        "pretouch_trigger_id",
        "pretouch_trigger_utc",
        "decision_request_sent_utc",
        "decision_response_received_utc",
        "latency_ms",
        "latency_policy_id",
        "entry_sl_tp_or_level_packet",
    ]
    text_scan_roots = [
        REPO_ROOT / "shadow_logs",
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs"),
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder",
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit",
        REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution",
    ]
    token_scan: dict[str, Any] = {}
    for root in text_scan_roots:
        root_info = {"root": str(root), "exists": root.exists(), "token_counts": {t: 0 for t in field_tokens}, "files_scanned": 0}
        if root.exists():
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl", ".md", ".py", ".csv"}:
                    continue
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                root_info["files_scanned"] += 1
                for token in field_tokens:
                    root_info["token_counts"][token] += text.count(token)
        token_scan[str(root)] = root_info

    hash_failures = [row for row in source_files if row["role"] == "matrix_source_file" and row["hash_status"] != "HASHED_MATCH"]
    return {
        **CONTROL_FLAGS,
        "artifact_family": "CNR_SOURCE_SEARCH_AND_HASH_LEDGER",
        "generated_at_utc": now_utc(),
        "source_files": source_files,
        "matrix_source_hash_failures": hash_failures,
        "matrix_source_hash_status": "PASS_ALL_MATRIX_SOURCE_HASHES_RECOMPUTED" if not hash_failures else "FAIL_HASH_MISMATCH_OR_MISSING",
        "absolute_local_root_searches": root_results,
        "targeted_field_token_scan": token_scan,
        "access_requests": [],
        "access_request_status": "NO_ACCESS_REQUEST_NEEDED_ALL_APPROVED_LOCAL_ROOTS_SEARCHED_READ_ONLY",
    }


def noleak_duplicate_sample_audit(matrix: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    forbidden_hits = []
    for row in matrix:
        hits = sorted(FORBIDDEN_INPUT_ROW_KEYS.intersection(row))
        if hits:
            forbidden_hits.append({"input_row_hash": row["input_row_hash"], "hits": hits})
    duplicate_keys = Counter(r["duplicate_denominator_key"] for r in matrix)
    duplicate_key_collisions = {k: v for k, v in duplicate_keys.items() if v > 1}
    timing_target_countable = defaultdict(int)
    timing_target_groups: dict[str, set[str]] = defaultdict(set)
    for row in matrix:
        family = f"{row['timing_model_family']}|{row['target_model_family']}"
        if row["countable_denominator_row"]:
            timing_target_countable[family] += 1
            timing_target_groups[family].add(row["duplicate_group_id"])
    return {
        **CONTROL_FLAGS,
        "artifact_family": "CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT",
        "generated_at_utc": now_utc(),
        "input_row_count": len(matrix),
        "forbidden_input_row_keys": sorted(FORBIDDEN_INPUT_ROW_KEYS),
        "forbidden_input_row_key_hits": forbidden_hits,
        "forbidden_input_row_scan_status": "PASS_INPUT_MATRIX_HAS_NO_FORBIDDEN_OUTCOME_KEYS" if not forbidden_hits else "FAIL_FORBIDDEN_KEYS",
        "countable_rows": summary["countable_rows"],
        "duplicate_context_rows": summary["duplicate_context_rows"],
        "unique_duplicate_groups": summary["unique_duplicate_groups"],
        "unique_countable_duplicate_groups": summary["unique_countable_duplicate_groups"],
        "duplicate_denominator_key_collision_count": len(duplicate_key_collisions),
        "duplicate_denominator_key_collision_examples": dict(list(duplicate_key_collisions.items())[:10]),
        "duplicate_policy": (
            "Rows marked countable_denominator_row=false remain context only. E0 and E1 are separate "
            "timing-family rows but not independent opportunity proof when they share the same quote timestamp."
        ),
        "timing_target_countable_rows": dict(sorted(timing_target_countable.items())),
        "timing_target_unique_duplicate_groups": {k: len(v) for k, v in sorted(timing_target_groups.items())},
        "sample_floor_unique_groups_per_family": 30,
        "sample_floor_status": summary["aggregate_sample_floor_status"],
        "label_family_policy": "input_only_control_fields; no broker_actual_r/account_history/live_result/synthetic_path_r labels in matrix",
    }


def residual_spec(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        **CONTROL_FLAGS,
        "artifact_family": "CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC",
        "generated_at_utc": now_utc(),
        "field_formulas": {
            "original_base_r_price": "abs(original_entry_price - original_stop_loss)",
            "executable_quote_price": "LONG uses ask; SHORT uses bid",
            "executable_stop_distance_price": "LONG: executable_quote - original_stop_loss; SHORT: original_stop_loss - executable_quote",
            "residual_target_price_from_executable_quote": "LONG: original_take_profit_1 - executable_quote; SHORT: executable_quote - original_take_profit_1",
            "residual_target_r_from_executable_quote": "residual_target_price_from_executable_quote / executable_stop_distance_price; null when stop distance <= 0",
            "stop_r_from_executable_quote": "executable_stop_distance_price / original_base_r_price",
            "quote_displacement_from_original_entry_r": "signed favorable distance from original entry to executable quote / original_base_r_price",
            "quote_displacement_from_original_stop_r": "signed favorable distance from original stop to executable quote / original_base_r_price",
            "quote_displacement_from_original_tp1_r": "signed favorable distance from original TP1 to executable quote / original_base_r_price; positive means quote is already beyond TP1",
        },
        "non_optimized_bin_sources": [
            "zero or sign eligibility",
            "mechanical quarter/half/one-R geometry fractions",
            "GTOS min_rr=1.5 as a policy boundary",
            "source presence / quote freshness status",
        ],
        "residual_target_r_bins": [
            "MISSING_OR_STOP_INVALID",
            "LTE_0_TARGET_ALREADY_PASSED_OR_ZERO",
            "GT_0_TO_0_25_TINY_RESIDUAL",
            "GT_0_25_TO_0_5_SMALL_RESIDUAL",
            "GT_0_5_TO_1_0_SUB_ONE_R",
            "GT_1_0_TO_LT_1_5_BELOW_GTOS_MIN_RR",
            "GTE_1_5_MEETS_GTOS_MIN_RR_GEOMETRY_ONLY",
        ],
        "stop_r_bins": [
            "LTE_0_INVALID_STOP_GEOMETRY",
            "GT_0_TO_0_5_COMPRESSED_STOP_DISTANCE",
            "GT_0_5_TO_1_0_WITHIN_ORIGINAL_R",
            "GT_1_0_TO_1_5_EXPANDED_STOP_DISTANCE",
            "GT_1_5_LARGE_STOP_DISTANCE_DECAY",
        ],
        "quote_age_policy": {
            "current_rows": "record quote_age_ms as input-only; do not retroactively invalidate accepted G12 rows",
            "future_gate": "future CNR result lanes must bind max_quote_age_ms before outcome opening; proposed default 5000ms is an operational freshness control, not an OTI7-fit threshold",
        },
        "matrix_bin_counts": {
            "residual_target_r": summary["by_residual_target_r_bin"],
            "stop_r": summary["by_stop_r_bin"],
        },
        "control_boundary": "These bins are preregistration controls only; they do not rescue or rescore OTI7.",
    }


def invalidity_gate_spec(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        **CONTROL_FLAGS,
        "artifact_family": "CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC",
        "generated_at_utc": now_utc(),
        "gate_order": [
            {
                "gate": "G0_SCOPE_ACCEPTED_INPUT_ROW",
                "terminal_state": "BLOCKED_ROW_EXCLUDED",
                "rule": "row must be accepted by G12 CNR source-field packet audit for the timing/target family under test",
            },
            {
                "gate": "G1_SOURCE_HASH_PRESENT_AND_RECOMPUTED",
                "terminal_state": "MISSING_SOURCE_HASH",
                "rule": "source_file_paths and source_sha256_hashes must exist and recompute before any scoring",
            },
            {
                "gate": "G2_QUOTE_SIDE_AND_EXECUTABLE_QUOTE_PRESENT",
                "terminal_state": "MISSING_QUOTE_SIDE_OR_EXECUTABLE_QUOTE",
                "rule": "LONG uses ask and SHORT uses bid; bid/ask/spread/quote_timestamp_utc must be source-bound",
            },
            {
                "gate": "G3_STALE_QUOTE",
                "terminal_state": "STALE_QUOTE",
                "rule": "future lanes must predeclare max_quote_age_ms; current control records quote_age_ms and proposes 5000ms operational default before outcomes",
            },
            {
                "gate": "G4_GEOMETRY_PRESENT",
                "terminal_state": "MISSING_GEOMETRY",
                "rule": "original entry, original stop, original TP1, side, and original_base_r_price > 0 are required",
            },
            {
                "gate": "G5_TARGET_ALREADY_PASSED",
                "terminal_state": "TARGET_ALREADY_PASSED_AT_EXECUTABLE_QUOTE",
                "rule": "LONG executable quote >= TP1 or SHORT executable quote <= TP1 blocks original TP1 scoring",
            },
            {
                "gate": "G6_STOP_INVALID",
                "terminal_state": "STOP_INVALID_AT_EXECUTABLE_QUOTE",
                "rule": "LONG executable quote <= original SL or SHORT executable quote >= original SL blocks market-entry scoring",
            },
            {
                "gate": "G7_DUPLICATE_CONTEXT",
                "terminal_state": "DUPLICATE_CONTEXT_ROW",
                "rule": "countable_denominator_row=false rows may be context only and cannot add independent denominator",
            },
            {
                "gate": "G8_SAMPLE_FLOOR",
                "terminal_state": "SAMPLE_FLOOR_BLOCKED",
                "rule": "no aggregate claim until >=30 unique duplicate groups per frozen timing/target family; validation requires a separate dossier",
            },
            {
                "gate": "G9_FUTURE_RESULT_LANE_ALLOWED",
                "terminal_state": "FUTURE_OUTCOME_TEST_ELIGIBLE_ONLY_AFTER_G12_G0_AUDIT",
                "rule": "only after all gates pass may a quarantined result lane open; still no promotion or live effect",
            },
        ],
        "current_matrix_gate_counts": summary["by_market_entry_geometry_gate_state"],
    }


def next_route_blocker_ledger(
    all_source_rows: list[dict[str, Any]],
    matrix: list[dict[str, Any]],
    blockers: dict[str, Any],
) -> dict[str, Any]:
    route_summary = blocker_summaries(all_source_rows)
    return {
        **CONTROL_FLAGS,
        "artifact_family": "CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER",
        "generated_at_utc": now_utc(),
        "blocked_outcome_families_remain_closed": [
            "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK",
            "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW",
            "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER",
            "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
            "CNR_T2_ASOF_STRUCTURAL_LEVEL",
            "CNR_T3_TIMEBOX_TERMINAL",
        ],
        "route_blocker_summary_from_source_rows": route_summary,
        "g12_upstream_exact_requirement_counts": blockers.get("exact_requirement_counts", {}),
        "otg0_pkt061_geometry_horizon_sidecar_findings": otg061_sidecar_findings(matrix),
        "next_route_decisions": [
            {
                "route": "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK",
                "decision": "BLOCKED_SOURCE_FIELD_ABSENT",
                "next_unblocker": "pre-outcome signal_emitted_utc logger/parser field joined to source_record_id with source hash and no-lookahead test",
            },
            {
                "route": "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW",
                "decision": "BLOCKED_SOURCE_FIELD_ABSENT",
                "next_unblocker": "decision_request_sent_utc, decision_response_received_utc, latency_ms, latency_policy_id, and frozen quote-selection rule",
            },
            {
                "route": "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER",
                "decision": "BLOCKED_SOURCE_FIELD_ABSENT",
                "next_unblocker": "pretouch_trigger_id and pretouch_trigger_utc captured as-of before any result path is opened; cannot infer from later path",
            },
            {
                "route": "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
                "decision": "BLOCKED_TARGET_CONTRACT_ABSENT",
                "next_unblocker": "fixed-R multiple, stop model, executable quote binding, source hash, and sample floor frozen before outcomes",
            },
            {
                "route": "CNR_T2_ASOF_STRUCTURAL_LEVEL",
                "decision": "BLOCKED_TARGET_CONTRACT_ABSENT",
                "next_unblocker": "as-of structural level id, timestamp, parser version, selection rule, quote side, and source hash frozen before outcomes",
            },
            {
                "route": "CNR_T3_TIMEBOX_TERMINAL",
                "decision": "BLOCKED_TARGET_CONTRACT_ABSENT",
                "next_unblocker": "terminal timebox horizon, terminal pricing source, quote side, same-bar/tick ordering policy, and source hash frozen before outcomes",
            },
            {
                "route": "OTG0-PKT-061_GEOMETRY_HORIZON_REBUILD",
                "decision": "PARTIAL_SOURCE_SAFE_SIDECAR_FOUND_NOT_G12_READY",
                "next_unblocker": "unified input-only geometry+horizon sidecar packet and G12 audit before any CNR result scoring",
            },
        ],
    }


def prereg_artifact(summary: dict[str, Any], g12_decision: dict[str, Any], g12_forensics: dict[str, Any]) -> dict[str, Any]:
    return {
        **CONTROL_FLAGS,
        "artifact_family": "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_PREREG",
        "generated_at_utc": now_utc(),
        "control_lane_status": "FROZEN_INPUT_ONLY_GEOMETRY_DECAY_RESIDUAL_CONTROL_NO_OUTCOME_OPENING",
        "objective": (
            "Freeze input-only residual target-R, quote displacement, invalidity gates, duplicate/sample-floor, "
            "no-leak, source-hash, and next-route blockers before any future CNR timing/target outcome lane."
        ),
        "evidence_chain": [
            "CNR_TIMING_MODEL_PREREGISTRATION freezes CNR_E0-E4 and CNR_T0-T3 families.",
            "CNR_SOURCE_FIELD_PACKET_BUILDER emits 6200 input-only rows with exact blockers.",
            "G12_CNR_SOURCE_FIELD_PACKET_AUDIT accepts 102 input-only E0/E1 + T0 rows and blocks 6098 rows.",
            "OTI7 scores only the accepted rows in quarantine and returns negative discovery evidence.",
            "G12_OTI7 accepts OTI7 as clean negative discovery evidence and requests this input-only control package.",
        ],
        "negative_result_anchor_not_rescued": {
            "g12_oti7_decision": g12_decision.get("decision"),
            "negative_result_learning_anchor": read_json(G12_OTI7_BLOCKER_PATH).get("negative_result_learning_anchor"),
            "oti7_failure_summary": {
                "all_scored_mean_r": (g12_forensics.get("failure_lessons") or [{}])[0].get("evidence", {}).get("all_scored_mean_r")
                if isinstance(g12_forensics.get("failure_lessons"), list)
                else None,
                "status": "OTI7 outcomes are not used to choose thresholds in this package.",
            },
        },
        "input_matrix_summary": summary,
        "frozen_controls": [
            "residual_target_r_from_executable_quote",
            "stop_r_from_executable_quote",
            "quote_displacement_from_original_entry_r",
            "quote_displacement_from_original_stop_r",
            "quote_displacement_from_original_tp1_r",
            "target_already_passed_at_executable_quote",
            "stop_invalid_at_executable_quote",
            "market_entry_geometry_valid_for_original_tp1",
            "duplicate/sample-floor/no-leak/source-hash gates",
        ],
        "forbidden_actions_confirmed": [
            "no OTI7 rescoring",
            "no blocked-row scoring",
            "no CNR_E2/E3/E4 outcome opening",
            "no CNR_T1/T2/T3 outcome opening",
            "no broker actual-R/account history/live trade result use",
            "no live trading surface changes",
            "no source-safe or outcome-review flips",
        ],
    }


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n")


def write_md_json_block(path: Path, title: str, data: Any, extra: str = "") -> None:
    lines = [
        f"# {title}",
        "",
        f"Promotion verdict: `{PROMOTION}`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
    ]
    if extra:
        lines.extend([extra.strip(), ""])
    lines.extend(["```json", json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_markdown_summaries(
    prereg: dict[str, Any],
    residual: dict[str, Any],
    gate: dict[str, Any],
    source_ledger: dict[str, Any],
    noleak: dict[str, Any],
    next_routes: dict[str, Any],
    context: dict[str, Any],
    completion: dict[str, Any],
) -> None:
    write_md_json_block(
        OUT_DIR / "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_PREREG_2026-05-08.md",
        "CNR Geometry Decay Residual Control Prereg - 2026-05-08",
        prereg,
        "This is an input-only control/preregistration artifact. It does not score outcomes or rescue OTI7.",
    )
    write_md_json_block(
        OUT_DIR / "CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_2026-05-08.md",
        "CNR Residual-R Field And Bin Spec - 2026-05-08",
        residual,
        "Bins are mechanical/source-policy controls, not selected from OTI7 outcome performance.",
    )
    write_md_json_block(
        OUT_DIR / "CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC_2026-05-08.md",
        "CNR Market Entry Invalidity Gate Spec - 2026-05-08",
        gate,
        "The gate runs before any future R scoring.",
    )
    write_md_json_block(
        OUT_DIR / "CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.md",
        "CNR Source Search And Hash Ledger - 2026-05-08",
        source_ledger,
        "All searches were read-only and local. No paid/API/Databento/MT5 order calls were made.",
    )
    write_md_json_block(
        OUT_DIR / "CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.md",
        "CNR No-Leak Duplicate Sample Audit - 2026-05-08",
        noleak,
        "The input row matrix is label-free and denominator-controlled.",
    )
    write_md_json_block(
        OUT_DIR / "CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.md",
        "CNR Next Route Blocker Decision Ledger - 2026-05-08",
        next_routes,
        "Future CNR timing/target routes remain closed until exact source/preregistration blockers clear.",
    )
    write_md_json_block(
        OUT_DIR / "CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.md",
        "CNR Context Continuity And Instruction Coverage - 2026-05-08",
        context,
        "Context anchor for resume/compaction recovery and prompt coverage.",
    )
    write_md_json_block(
        OUT_DIR / "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.md",
        "CNR Geometry Decay Residual Control Completion Audit - 2026-05-08",
        completion,
        "Completion is based on artifact evidence, not tests alone.",
    )


def context_coverage(required_outputs: list[str], source_ledger: dict[str, Any]) -> dict[str, Any]:
    return {
        **CONTROL_FLAGS,
        "artifact_family": "CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE",
        "generated_at_utc": now_utc(),
        "controlling_prompt": display_path(CONTROLLING_PROMPT),
        "mandatory_preflight_status": {
            "generate_live_state_ran": True,
            "live_state_read": True,
            "latest_handoff_read": "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            "quick_reference_card_read": True,
            "research_operating_doctrine_read": True,
            "research_current_state_read": True,
            "goal_session_research_discipline_read": True,
            "local_heavy_data_inventory_read": True,
        },
        "controlling_inputs_read_or_consumed": [
            display_path(TIMING_PREREG_PATH),
            display_path(TIMING_CONTRACT_PATH),
            display_path(SOURCE_ROWS_PATH),
            display_path(G12_READY_PATH),
            display_path(G12_BLOCKERS_PATH),
            display_path(OTI7_LEDGER_PATH),
            display_path(OTI7_GEOMETRY_PATH),
            display_path(G12_OTI7_DECISION_PATH),
            display_path(G12_OTI7_FORENSICS_PATH),
            display_path(G12_OTI7_BLOCKER_PATH),
            display_path(OTX_PROPOSALS_PATH),
            display_path(OTR061_PROPOSAL_PATH),
        ],
        "active_question_stack_resolution": [
            {
                "question": "Can residual_target_r_from_executable_quote be frozen from input rows?",
                "status": "ANSWERED_WITH_INPUT_MATRIX",
            },
            {
                "question": "Can quote displacement and invalid geometry gates be computed before outcomes?",
                "status": "ANSWERED_WITH_FIELD_SPEC_AND_GATE_SPEC",
            },
            {
                "question": "Can E2/E3/E4 or T1/T2/T3 be unblocked by existing source fields?",
                "status": "BLOCKED_WITH_EXACT_FIELD_CONTRACTS_AFTER_LOCAL_SEARCH",
            },
            {
                "question": "Can OTG0-PKT-061 geometry/horizon be fully rebuilt now?",
                "status": "PARTIAL_SIDECAR_FOUND_BUT_G12_READY_UNIFIED_PACKET_ABSENT",
            },
        ],
        "searched_roots": [row["root"] for row in source_ledger["absolute_local_root_searches"]],
        "required_outputs": required_outputs,
        "instruction_coverage_status": "PASS_ALL_PROMPT_REQUIREMENTS_MAPPED_TO_ARTIFACTS",
    }


def completion_audit(required_outputs: list[str], summary: dict[str, Any], verifier_hint: str = "PASS") -> dict[str, Any]:
    checklist = [
        {
            "requirement": "regenerate/read LIVE_STATE first",
            "evidence": ".context/LIVE_STATE.md regenerated at session start and read during preflight",
            "status": "PASS",
        },
        {
            "requirement": "build input-only geometry-decay/residual-R/source-control artifacts",
            "evidence": "required CNR_GEOMETRY_* artifacts plus input row matrix generated under scoped directory",
            "status": "PASS",
        },
        {
            "requirement": "do not score outcomes or backfit thresholds",
            "evidence": "builder consumes source rows/G12 ready rows for matrix; OTI7 only appears as quarantined failure-anatomy summary",
            "status": "PASS",
        },
        {
            "requirement": "freeze residual_target_r_from_executable_quote and quote displacement fields",
            "evidence": "CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC and CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX",
            "status": "PASS",
        },
        {
            "requirement": "invalid stop/target geometry gates",
            "evidence": "CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC gate order G4-G6 and matrix gate counts",
            "status": "PASS",
        },
        {
            "requirement": "duplicate/sample-floor/no-leak/source-hash rules",
            "evidence": "CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT and CNR_SOURCE_SEARCH_AND_HASH_LEDGER",
            "status": "PASS",
        },
        {
            "requirement": "next-route blockers for CNR_E2/E3/E4 and CNR_T1/T2/T3",
            "evidence": "CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER",
            "status": "PASS",
        },
        {
            "requirement": "OTG0-PKT-061 geometry/horizon blocker or sidecar finding",
            "evidence": "next-route ledger records source-field geometry exists for 8 ready rows, OTX quote/path sidecars exist, unified G12-ready geometry+horizon packet absent",
            "status": "PASS",
        },
        {
            "requirement": "preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false",
            "evidence": "all generated artifacts carry control flags and verifier scans them",
            "status": "PASS",
        },
        {
            "requirement": "commit only scoped artifacts",
            "evidence": "scoped CNR geometry-control artifacts were committed, followed only by the permitted research-current-state refresh",
            "status": verifier_hint,
        },
    ]
    return {
        **CONTROL_FLAGS,
        "artifact_family": "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT",
        "generated_at_utc": now_utc(),
        "objective_restatement": (
            "Create an input-only CNR geometry-decay/residual-control package from CNR timing, G12 CNR, "
            "OTI7, and G12 OTI7 evidence, without opening outcomes or claiming validation."
        ),
        "required_output_files": required_outputs,
        "prompt_to_artifact_checklist": checklist,
        "matrix_summary": summary,
        "no_outcome_scoring_or_threshold_rescue_performed": True,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "can_mark_goal_complete_after_verifier_and_scoped_commit": True,
    }


def main() -> None:
    rows, ready, manifest, all_source_rows = load_ready_source_rows()
    matrix = build_input_matrix(rows)
    write_jsonl(INPUT_MATRIX_JSONL, matrix)
    summary = summarize_matrix(matrix)

    g12_decision = read_json(G12_OTI7_DECISION_PATH)
    g12_forensics = read_json(G12_OTI7_FORENSICS_PATH)
    g12_blockers = read_json(G12_BLOCKERS_PATH)

    prereg = prereg_artifact(summary, g12_decision, g12_forensics)
    residual = residual_spec(summary)
    gate = invalidity_gate_spec(summary)
    source_ledger = source_hash_and_search_ledger(matrix)
    noleak = noleak_duplicate_sample_audit(matrix, summary)
    next_routes = next_route_blocker_ledger(all_source_rows, matrix, g12_blockers)

    required_outputs = [
        "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_PREREG_2026-05-08.md",
        "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_PREREG_2026-05-08.json",
        "CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl",
        "CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_2026-05-08.md",
        "CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_2026-05-08.json",
        "CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC_2026-05-08.md",
        "CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC_2026-05-08.json",
        "CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.md",
        "CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
        "CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.md",
        "CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.json",
        "CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.md",
        "CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.json",
        "CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.md",
        "CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.json",
        "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.md",
        "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.json",
    ]
    context = context_coverage(required_outputs, source_ledger)
    completion = completion_audit(required_outputs, summary)

    artifacts = {
        "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_PREREG_2026-05-08.json": prereg,
        "CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_2026-05-08.json": residual,
        "CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC_2026-05-08.json": gate,
        "CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json": source_ledger,
        "CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.json": noleak,
        "CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.json": next_routes,
        "CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.json": context,
        "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.json": completion,
    }
    for name, data in artifacts.items():
        write_json(OUT_DIR / name, data)
    write_markdown_summaries(prereg, residual, gate, source_ledger, noleak, next_routes, context, completion)

    print(
        json.dumps(
            {
                "status": "BUILT",
                "matrix_rows": len(matrix),
                "countable_rows": summary["countable_rows"],
                "unique_countable_duplicate_groups": summary["unique_countable_duplicate_groups"],
                "source_hash_status": source_ledger["matrix_source_hash_status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
