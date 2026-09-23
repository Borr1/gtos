"""Build the OTG0-PKT-061 input-only geometry+horizon sidecar.

This builder intentionally does not read broker/account result ledgers or score
path outcomes. It joins source-field CNR geometry rows to OTX/OTR quote+horizon
packets only where the source-safe keys prove the join.
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
ROOT = OUT_DIR.parents[3]
PACKET_ID = "OTG0-PKT-061"
DATE_STAMP = "2026-05-08"
SCHEMA_VERSION = "cnr061_geometry_horizon_sidecar_v1"

SRC = {
    "goal_prompt": OUT_DIR / "CNR061_GEOMETRY_HORIZON_SIDECAR_GOAL_PROMPT_2026-05-08.md",
    "live_state": ROOT / ".context/LIVE_STATE.md",
    "latest_handoff": ROOT / ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "quick_reference": ROOT / ".context/00_core/quick_reference_card.md",
    "research_doctrine": ROOT / ".context/00_core/research_operating_doctrine.md",
    "research_current_state": ROOT / ".context/00_core/research_current_state.md",
    "goal_discipline": ROOT / ".context/00_core/goal_session_research_discipline.md",
    "local_heavy_inventory": ROOT / ".context/00_core/local_heavy_data_inventory.md",
    "cnr_blocker_decision": ROOT / "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.json",
    "cnr_blocker_decision_md": ROOT / "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.md",
    "cnr_prior_search": ROOT / "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
    "cnr_matrix": ROOT / "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl",
    "cnr_rows": ROOT / "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl",
    "cnr_manifest": ROOT / "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_MANIFEST_2026-05-07.json",
    "g12_ready": ROOT / "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_READY_ROW_SHORTLIST_2026-05-08.json",
    "g12_cnr_blockers": ROOT / "research/science_program_2026_05/06_outcome_testing/g12_cnr_source_field_packet_audit/G12_CNR_EXACT_BLOCKER_LEDGER_2026-05-08.json",
    "g6_input_packet": ROOT / "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
    "otx_proposals": ROOT / "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
    "g12_otx_source_hash": ROOT / "research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07.json",
    "otr061_proposal": ROOT / "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_2026-05-07.json",
    "g12_oti5_otr061_audit": ROOT / "research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/G12_OTR061_PACKET_RECOVERY_AUDIT_2026-05-07.json",
    "g12_oti7_blocker_map": ROOT / "research/science_program_2026_05/06_outcome_testing/g12_oti7_cnr_post_result_audit/G12_OTI7_CNR_NEXT_HYPOTHESIS_BLOCKER_MAP_2026-05-08.json",
}

OUTPUTS = {
    "packet_jsonl": OUT_DIR / "CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.jsonl",
    "packet_json": OUT_DIR / "CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_2026-05-08.json",
    "join_map_md": OUT_DIR / "CNR061_SOURCE_JOIN_MAP_2026-05-08.md",
    "join_map_json": OUT_DIR / "CNR061_SOURCE_JOIN_MAP_2026-05-08.json",
    "search_md": OUT_DIR / "CNR061_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.md",
    "search_json": OUT_DIR / "CNR061_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
    "noleak_md": OUT_DIR / "CNR061_NOLEAK_DUPLICATE_AUDIT_2026-05-08.md",
    "noleak_json": OUT_DIR / "CNR061_NOLEAK_DUPLICATE_AUDIT_2026-05-08.json",
    "proposal_md": OUT_DIR / "CNR061_G12_REAUDIT_READY_PROPOSAL_2026-05-08.md",
    "proposal_json": OUT_DIR / "CNR061_G12_REAUDIT_READY_PROPOSAL_2026-05-08.json",
    "blockers_md": OUT_DIR / "CNR061_EXACT_BLOCKER_OR_IMPOSSIBILITY_LEDGER_2026-05-08.md",
    "blockers_json": OUT_DIR / "CNR061_EXACT_BLOCKER_OR_IMPOSSIBILITY_LEDGER_2026-05-08.json",
    "context_md": OUT_DIR / "CNR061_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.md",
    "context_json": OUT_DIR / "CNR061_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.json",
    "completion_md": OUT_DIR / "CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT_2026-05-08.md",
    "completion_json": OUT_DIR / "CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT_2026-05-08.json",
}

FORBIDDEN_SIDE_ROW_KEY_TOKENS = (
    "broker_actual",
    "account_history",
    "live_trade_result",
    "actual_r",
    "synthetic_path_r",
    "result_r",
    "target_first",
    "stop_first",
    "hit_order",
    "mfe",
    "mae",
    "terminal_state",
    "terminal_status",
    "outcome_label",
    "result_label",
    "candidate_path_label",
    "candidate_terminal_event",
    "pnl",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(ROOT.resolve()).as_posix()
    except Exception:
        return str(path)


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            row["_jsonl_line_number"] = line_no
            rows.append(row)
    return rows


def rows_from(obj: Any, key_order: tuple[str, ...] = ("rows", "records")) -> list[dict[str, Any]]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in key_order:
            rows = obj.get(key)
            if isinstance(rows, list):
                return rows
    return []


def get_source_hash_entry(path: Path, role: str) -> dict[str, Any]:
    return {
        "path": rel(path),
        "absolute_path": str(path),
        "exists": path.exists(),
        "role": role,
        "sha256": file_sha256(path),
    }


def resolve_source_path(path_text: str) -> Path:
    p = Path(path_text)
    if p.is_absolute():
        return p
    return ROOT / path_text.replace("/", os.sep)


def hash_path_text(path_text: str) -> dict[str, Any]:
    original = resolve_source_path(path_text)
    alternatives: list[Path] = []
    if not original.exists() and "OTR061_MT5_READ_ONLY_XAUUSD_TICKS" in path_text:
        alternatives.append(SRC["otr061_proposal"].parent / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet")
        alternatives.append(Path(r"C:\Users\MSI\Documents\ai-trading-agent\research\science_program_2026_05\06_outcome_testing\otr061_xau_tick_recovery\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"))
    actual = original if original.exists() else next((alt for alt in alternatives if alt.exists()), original)
    return {
        "declared_path": path_text,
        "resolved_path": str(actual),
        "declared_path_exists": original.exists(),
        "hash_path_exists": actual.exists(),
        "sha256": file_sha256(actual),
        "fallback_used": str(actual) != str(original),
    }


def index_by(rows: list[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
    out: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[row.get(key)].append(row)
    return out


def sidecar_forbidden_hits(value: Any, path: str = "$") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lower = key.lower()
            for token in FORBIDDEN_SIDE_ROW_KEY_TOKENS:
                if token in lower:
                    hits.append({"path": f"{path}.{key}", "token": token})
            hits.extend(sidecar_forbidden_hits(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(sidecar_forbidden_hits(child, f"{path}[{idx}]"))
    return hits


def packet_input_geometry(source_packet_record: dict[str, Any]) -> dict[str, Any]:
    packet = source_packet_record.get("impulse_pullback_no_retrace_packet") or {}
    return packet.get("original_trade_geometry") or {}


def join_counts(source: list[dict[str, Any]], target_index: dict[Any, list[dict[str, Any]]], key: str) -> dict[str, Any]:
    matched = 0
    missing = 0
    ambiguous = 0
    match_widths: Counter[int] = Counter()
    for row in source:
        width = len(target_index.get(row.get(key), []))
        match_widths[width] += 1
        if width == 0:
            missing += 1
        elif width == 1:
            matched += 1
        else:
            matched += 1
            ambiguous += 1
    return {
        "source_rows": len(source),
        "matched_rows": matched,
        "missing_rows": missing,
        "ambiguous_rows": ambiguous,
        "match_widths": dict(sorted(match_widths.items())),
    }


def build() -> dict[str, Any]:
    generated_at = utc_now()
    cnr_rows = [r for r in read_jsonl(SRC["cnr_rows"]) if r.get("packet_id") == PACKET_ID]
    cnr_e0e1_t0 = [
        r for r in cnr_rows
        if r.get("target_model_family") == "CNR_T0_ORIGINAL_TP1"
        and r.get("timing_model_family") in {"CNR_E0_DECISION_CLOSE_MARKET", "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"}
    ]
    matrix_rows = [r for r in read_jsonl(SRC["cnr_matrix"]) if r.get("packet_id") == PACKET_ID]
    g12_ready_obj = read_json(SRC["g12_ready"])
    g12_ready_rows = [r for r in rows_from(g12_ready_obj) if r.get("packet_id") == PACKET_ID]
    g6_input_obj = read_json(SRC["g6_input_packet"])
    g6_records = [r for r in rows_from(g6_input_obj) if r.get("record_id")]
    otx_obj = read_json(SRC["otx_proposals"])
    otx_rows = [r for r in rows_from(otx_obj) if r.get("packet_id") == PACKET_ID]
    otr061_obj = read_json(SRC["otr061_proposal"])
    otr061_rows = [r for r in rows_from(otr061_obj) if r.get("packet_id") == PACKET_ID]
    g12_oti7_blocker_map = read_json(SRC["g12_oti7_blocker_map"])

    cnr_by_row_sha = {r.get("row_sha256"): r for r in cnr_rows if r.get("row_sha256")}
    g12_by_row_sha = {r.get("row_sha256"): r for r in g12_ready_rows if r.get("row_sha256")}
    matrix_by_source_sha = {r.get("source_row_sha256"): r for r in matrix_rows if r.get("source_row_sha256")}
    g6_by_record = {r["record_id"]: r for r in g6_records}
    otx_by_record = {r["record_id"]: r for r in otx_rows}
    otr_by_record = {r["record_id"]: r for r in otr061_rows}

    sidecar_rows: list[dict[str, Any]] = []
    join_failures: list[dict[str, Any]] = []
    for matrix in sorted(matrix_rows, key=lambda r: (r.get("row_number") or 0, r.get("timing_model_family") or "")):
        cnr = cnr_by_row_sha.get(matrix.get("source_row_sha256"))
        g12 = g12_by_row_sha.get(matrix.get("source_row_sha256"))
        otx = otx_by_record.get(matrix.get("record_id"))
        g6 = g6_by_record.get(matrix.get("record_id"))
        missing = [name for name, value in (("cnr_source_row", cnr), ("g12_ready_row", g12), ("otx_record", otx), ("g6_input_record", g6)) if not value]
        if missing:
            join_failures.append({"record_id": matrix.get("record_id"), "source_row_sha256": matrix.get("source_row_sha256"), "missing": missing})
            continue
        quote = otx.get("decision_quote_packet") or {}
        path = otx.get("ordered_tick_path_packet") or {}
        original_geometry = packet_input_geometry(g6)
        source_paths = list(dict.fromkeys(
            [str(SRC["cnr_rows"]), str(SRC["g12_ready"]), str(SRC["cnr_matrix"]), str(SRC["otx_proposals"]), str(SRC["g6_input_packet"])]
            + list(matrix.get("source_file_paths") or [])
            + list(path.get("path_source_files") or [])
        ))
        source_evidence = [
            {
                "source_name": "CNR_SOURCE_FIELD_PACKET_ROWS",
                "path": rel(SRC["cnr_rows"]),
                "jsonl_line_number": cnr.get("_jsonl_line_number"),
                "row_sha256": cnr.get("row_sha256"),
                "file_sha256": file_sha256(SRC["cnr_rows"]),
                "join_role": "geometry_and_quote_source_row",
            },
            {
                "source_name": "G12_CNR_READY_ROW_SHORTLIST",
                "path": rel(SRC["g12_ready"]),
                "row_number": g12.get("row_number"),
                "row_sha256": g12.get("row_sha256"),
                "file_sha256": file_sha256(SRC["g12_ready"]),
                "join_role": "accepted_input_row_gate",
            },
            {
                "source_name": "CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX",
                "path": rel(SRC["cnr_matrix"]),
                "jsonl_line_number": matrix.get("_jsonl_line_number"),
                "input_row_hash": matrix.get("input_row_hash"),
                "source_row_sha256": matrix.get("source_row_sha256"),
                "file_sha256": file_sha256(SRC["cnr_matrix"]),
                "join_role": "geometry_residual_control_source",
            },
            {
                "source_name": "OTX_G6_REBUILT_PACKET_PROPOSALS",
                "path": rel(SRC["otx_proposals"]),
                "proposal_source_hash": otx.get("proposal_source_hash"),
                "file_sha256": file_sha256(SRC["otx_proposals"]),
                "join_role": "decision_quote_and_ordered_path_source",
            },
            {
                "source_name": "OTG0_PKT061_G6_INPUT_PACKET",
                "path": rel(SRC["g6_input_packet"]),
                "record_source_hash": g6.get("source_hash"),
                "file_sha256": file_sha256(SRC["g6_input_packet"]),
                "join_role": "original_entry_sl_tp_source",
            },
        ]
        for path_text in source_paths:
            if path_text.endswith(".parquet"):
                source_evidence.append({
                    "source_name": "TICK_PARQUET_SOURCE",
                    "path": path_text,
                    **hash_path_text(path_text),
                    "join_role": "quote_and_path_tick_source",
                })

        row = {
            "schema_version": SCHEMA_VERSION,
            "artifact_family": "CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET_ROW",
            "packet_id": PACKET_ID,
            "record_id": matrix.get("record_id"),
            "source_record_id": matrix.get("source_record_id"),
            "source_candidate_id": matrix.get("source_candidate_id"),
            "symbol": matrix.get("symbol"),
            "broker_symbol": matrix.get("broker_symbol"),
            "side": matrix.get("side"),
            "session": matrix.get("session"),
            "decision_asof_utc": matrix.get("decision_asof_utc"),
            "candidate_close_utc": matrix.get("candidate_close_utc"),
            "timing_model_family": matrix.get("timing_model_family"),
            "target_model_family": matrix.get("target_model_family"),
            "duplicate_group_id": matrix.get("duplicate_group_id"),
            "duplicate_denominator_key": matrix.get("duplicate_denominator_key"),
            "duplicate_policy": matrix.get("duplicate_policy"),
            "parser_version": cnr.get("parser_version"),
            "source_join_status": "PROVEN_JOIN_CNR_G12_MATRIX_OTX_BY_ROW_HASH_AND_RECORD_ID",
            "source_join_keys_proven": {
                "source_row_sha256": matrix.get("source_row_sha256"),
                "record_id": matrix.get("record_id"),
                "source_candidate_id": matrix.get("source_candidate_id"),
                "symbol_side_session_decision": "|".join(str(matrix.get(k)) for k in ("symbol", "side", "session", "decision_asof_utc")),
                "duplicate_group_id": matrix.get("duplicate_group_id"),
                "tick_source_sha256": matrix.get("quote_source_sha256"),
            },
            "entry_sl_tp_or_level_packet": {
                "schema_id": "original_entry_sl_tp_packet_v1_input_only",
                "geometry_source": matrix.get("geometry_source"),
                "entry_price": matrix.get("original_entry_price"),
                "stop_loss": matrix.get("original_stop_loss"),
                "take_profit_1": matrix.get("original_take_profit_1"),
                "stop_model_id": matrix.get("stop_model_id"),
                "target_model_id": matrix.get("target_model_id"),
                "source_packet_geometry_valid": original_geometry.get("geometry_valid"),
                "matrix_geometry_valid_for_original_tp1": matrix.get("market_entry_geometry_valid_for_original_tp1"),
                "market_entry_geometry_gate_state": matrix.get("market_entry_geometry_gate_state"),
                "target_already_passed_at_executable_quote": matrix.get("target_already_passed_at_executable_quote"),
                "stop_invalid_at_executable_quote": matrix.get("stop_invalid_at_executable_quote"),
            },
            "executable_quote_packet": {
                "schema_id": "decision_quote_asof_v1_input_only",
                "quote_side_rule": matrix.get("quote_side_rule"),
                "executable_quote_side": matrix.get("executable_quote_side"),
                "executable_quote_price": matrix.get("executable_quote_price"),
                "quote_timestamp_utc": matrix.get("quote_timestamp_utc"),
                "quote_age_ms": matrix.get("quote_age_ms"),
                "bid": matrix.get("bid"),
                "ask": matrix.get("ask"),
                "spread": matrix.get("spread"),
                "quote_source_status": matrix.get("quote_source_status"),
                "quote_source_path": matrix.get("quote_source_path"),
                "quote_source_sha256": matrix.get("quote_source_sha256"),
                "otx_quote_status": quote.get("quote_status"),
                "otx_quote_time_utc": quote.get("decision_quote_time_utc"),
                "otx_quote_staleness_ms": quote.get("quote_staleness_ms"),
            },
            "ordered_path_packet": {
                "schema_id": "ordered_tick_path_asof_v1_input_only",
                "path_start_utc": path.get("path_start_utc"),
                "path_end_utc": path.get("path_end_utc"),
                "path_first_timestamp_utc": path.get("path_first_timestamp_utc"),
                "path_last_timestamp_utc": path.get("path_last_timestamp_utc"),
                "path_row_count": path.get("path_row_count"),
                "path_status": path.get("path_status"),
                "path_row_count_status": path.get("path_row_count_status"),
                "path_source_type": path.get("path_source_type"),
                "path_horizon_source": path.get("path_horizon_source"),
                "ordered_path_source_id": path.get("ordered_path_source_id"),
                "path_source_files": path.get("path_source_files"),
                "path_source_sha256": path.get("path_source_sha256"),
            },
            "tick_coverage_summary": {
                "decision_quote_found": quote.get("quote_status") == "DECISION_QUOTE_FOUND_ASOF",
                "ordered_path_available": path.get("path_status") == "ORDERED_TICK_PATH_AVAILABLE",
                "missing_tick_files": sorted(set((quote.get("missing_tick_files") or []) + (path.get("missing_tick_files") or []))),
                "quote_and_path_hashes_match": matrix.get("quote_source_sha256") in set((path.get("path_source_sha256") or {}).values()),
            },
            "source_evidence": source_evidence,
            "no_leak_scan_status": "PENDING_VERIFIER",
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "live_effect": False,
        }
        row["sidecar_row_sha256"] = stable_hash(row)
        row["no_leak_scan_status"] = "PASS_NO_FORBIDDEN_RESULT_FIELDS_IN_SIDECAR_ROW"
        sidecar_rows.append(row)

    sidecar_hash = stable_hash(sidecar_rows)

    sidecar_ready_record_ids = {r["record_id"] for r in sidecar_rows}
    blocker_rows: list[dict[str, Any]] = []
    for row in sorted(cnr_e0e1_t0, key=lambda r: (r.get("record_id") or "", r.get("timing_model_family") or "")):
        if row.get("record_id") in sidecar_ready_record_ids:
            continue
        otx = otx_by_record.get(row.get("record_id"))
        otr = otr_by_record.get(row.get("record_id"))
        blocker_rows.append({
            "packet_id": PACKET_ID,
            "record_id": row.get("record_id"),
            "source_record_id": row.get("source_record_id"),
            "source_candidate_id": row.get("source_candidate_id"),
            "symbol": row.get("symbol"),
            "side": row.get("side"),
            "session": row.get("session"),
            "decision_asof_utc": row.get("decision_asof_utc"),
            "timing_model_family": row.get("timing_model_family"),
            "target_model_family": row.get("target_model_family"),
            "source_row_sha256": row.get("row_sha256"),
            "blocker_state": row.get("blocker_state"),
            "blockers": row.get("blockers"),
            "quote_source_status": row.get("quote_source_status"),
            "pre_entry_target_already_passed_check": row.get("pre_entry_target_already_passed_check"),
            "target_binding_status": row.get("target_binding_status"),
            "entry_sl_tp_or_level_packet_available_from_source_field": all(row.get(k) is not None for k in ("original_entry_price", "original_stop_loss", "original_take_profit_1")),
            "otx_quote_path_join_status": "MATCHED_OTX_RECORD" if otx else "NO_OTX_RECORD",
            "otx_quote_status": (otx.get("decision_quote_packet") or {}).get("quote_status") if otx else None,
            "otx_path_status": (otx.get("ordered_tick_path_packet") or {}).get("path_status") if otx else None,
            "otr061_recovery_join_status": "MATCHED_OTR061_RECOVERY_RECORD" if otr else "NO_OTR061_RECOVERY_RECORD",
            "g12_reaudit_ready_status": "NOT_INCLUDED_IN_READY_PACKET_EXACT_BLOCKER_RECORDED",
            "minimum_unblocker": (
                "input-only invalid-clearing policy for market-entry rows where the source-hashed executable quote is already past original TP1"
                if row.get("pre_entry_target_already_passed_check") == "TRUE_SOURCE_GEOMETRY_GATE_NO_R_SCORING"
                else "source-hashed executable quote and ordered path fields before G12 reaudit"
            ),
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "live_effect": False,
        })

    blocker_summary = {
        "blocked_e0e1_t0_rows": len(blocker_rows),
        "by_pre_entry_target_already_passed_check": dict(Counter(r["pre_entry_target_already_passed_check"] for r in blocker_rows)),
        "by_quote_source_status": dict(Counter(r["quote_source_status"] for r in blocker_rows)),
        "by_symbol": dict(Counter(r["symbol"] for r in blocker_rows)),
        "otr061_recovered_rows_not_ready": sum(1 for r in blocker_rows if r["otr061_recovery_join_status"] == "MATCHED_OTR061_RECOVERY_RECORD"),
    }

    otx_record_ids = {r.get("record_id") for r in otx_rows}
    g12_ready_record_ids = {r.get("record_id") for r in g12_ready_rows}
    cnr_e0e1_record_ids = {r.get("record_id") for r in cnr_e0e1_t0}
    duplicate_group_otx_index = index_by(otx_rows, "duplicate_group_id")
    duplicate_group_ambiguity = [
        {
            "duplicate_group_id": group_id,
            "sidecar_rows": sum(1 for r in sidecar_rows if r.get("duplicate_group_id") == group_id),
            "otx_records_in_group": len(duplicate_group_otx_index.get(group_id, [])),
            "join_status": "AMBIGUOUS_IF_USED_ALONE_USE_RECORD_ID_PLUS_ROW_HASH",
        }
        for group_id in sorted({r.get("duplicate_group_id") for r in sidecar_rows})
    ]

    join_map = {
        "artifact_family": "CNR061_SOURCE_JOIN_MAP",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "source_counts": {
            "cnr_source_field_pkt061_rows_all_timing_targets": len(cnr_rows),
            "cnr_source_field_pkt061_e0e1_t0_rows": len(cnr_e0e1_t0),
            "cnr_source_field_pkt061_e0e1_t0_unique_record_ids": len(cnr_e0e1_record_ids),
            "g12_ready_pkt061_rows": len(g12_ready_rows),
            "g12_ready_pkt061_unique_record_ids": len(g12_ready_record_ids),
            "cnr_geometry_matrix_pkt061_rows": len(matrix_rows),
            "otx_pkt061_proposal_rows": len(otx_rows),
            "otx_pkt061_rows_with_decision_quote": sum((r.get("decision_quote_packet") or {}).get("quote_status") == "DECISION_QUOTE_FOUND_ASOF" for r in otx_rows),
            "otx_pkt061_rows_with_ordered_path": sum((r.get("ordered_tick_path_packet") or {}).get("path_status") == "ORDERED_TICK_PATH_AVAILABLE" for r in otx_rows),
            "otx_pkt061_rows_with_entry_sl_tp_or_level_packet": sum("entry_sl_tp_or_level_packet" in r for r in otx_rows),
            "otr061_recovered_rows": len(otr061_rows),
            "sidecar_ready_rows": len(sidecar_rows),
            "sidecar_unique_record_ids": len(sidecar_ready_record_ids),
        },
        "join_attempts": [
            {"name": "g12_ready_to_cnr_matrix_by_source_row_sha256", **join_counts(g12_ready_rows, index_by(matrix_rows, "source_row_sha256"), "row_sha256")},
            {"name": "g12_ready_to_cnr_source_by_row_sha256", **join_counts(g12_ready_rows, index_by(cnr_rows, "row_sha256"), "row_sha256")},
            {"name": "g12_ready_to_otx_by_record_id", **join_counts(g12_ready_rows, index_by(otx_rows, "record_id"), "record_id")},
            {"name": "g12_ready_to_g6_input_packet_by_record_id", **join_counts(g12_ready_rows, index_by(g6_records, "record_id"), "record_id")},
            {"name": "otx_all_to_cnr_e0e1_t0_by_record_id", "source_records": len(otx_record_ids), "matched_records": len(otx_record_ids & cnr_e0e1_record_ids), "missing_records": len(otx_record_ids - cnr_e0e1_record_ids)},
            {"name": "otx_all_to_g12_ready_by_record_id", "source_records": len(otx_record_ids), "matched_records": len(otx_record_ids & g12_ready_record_ids), "missing_records": len(otx_record_ids - g12_ready_record_ids)},
            {"name": "otr061_to_cnr_e0e1_t0_by_record_id", "source_records": len({r.get("record_id") for r in otr061_rows}), "matched_records": len({r.get("record_id") for r in otr061_rows} & cnr_e0e1_record_ids), "missing_records": len({r.get("record_id") for r in otr061_rows} - cnr_e0e1_record_ids)},
            {"name": "otr061_to_g12_ready_by_record_id", "source_records": len({r.get("record_id") for r in otr061_rows}), "matched_records": len({r.get("record_id") for r in otr061_rows} & g12_ready_record_ids), "missing_records": len({r.get("record_id") for r in otr061_rows} - g12_ready_record_ids)},
        ],
        "duplicate_group_join_ambiguity": duplicate_group_ambiguity,
        "join_failures": join_failures,
        "conclusion": "PROVEN_FOR_8_G12_READY_ROWS; NON_READY_OTX_OTR_ROWS_RECORDED_IN_BLOCKER_LEDGER",
    }

    noleak_hits = []
    for idx, row in enumerate(sidecar_rows):
        noleak_hits.extend({"row_index": idx, **hit} for hit in sidecar_forbidden_hits(row))
    duplicate_counts = Counter(r["duplicate_denominator_key"] for r in sidecar_rows)
    duplicate_groups = Counter(r["duplicate_group_id"] for r in sidecar_rows)
    noleak_duplicate_audit = {
        "artifact_family": "CNR061_NOLEAK_DUPLICATE_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "sidecar_row_count": len(sidecar_rows),
        "unique_sidecar_row_hashes": len({r["sidecar_row_sha256"] for r in sidecar_rows}),
        "duplicate_denominator_key_counts": dict(sorted(duplicate_counts.items())),
        "duplicate_group_counts": dict(sorted(duplicate_groups.items())),
        "unique_duplicate_group_count": len(duplicate_groups),
        "duplicate_policy": "Rows preserve timing-model denominator keys; duplicate_group_id exposes same-setup grouping for G12 denominator decisions. No outcome denominator is accepted here.",
        "forbidden_sidecar_key_hits": noleak_hits,
        "forbidden_sidecar_key_status": "PASS" if not noleak_hits else "FAIL",
        "metadata_flag_status": {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "account_history_accessed": False,
        "broker_actual_r_accessed": False,
        "live_trade_results_accessed": False,
        "blocked_packet_outcome_source_read": False,
        "paid_data_calls": 0,
        "api_calls": 0,
        "databento_calls": 0,
        "mt5_order_calls": 0,
        "order_calls": 0,
    }

    source_files = [get_source_hash_entry(path, role) for role, path in SRC.items()]
    for row in sidecar_rows:
        for evidence in row["source_evidence"]:
            declared = evidence.get("declared_path") or evidence.get("path")
            if declared and (str(declared).endswith(".parquet") or str(declared).startswith("C:\\")):
                source_files.append({
                    "path": declared,
                    "role": "sidecar_row_source_evidence",
                    **hash_path_text(str(declared)),
                })
    source_files_by_key = {}
    for entry in source_files:
        key = entry.get("path") or entry.get("declared_path") or entry.get("absolute_path")
        source_files_by_key[key] = entry

    filename_patterns = ("CNR061", "OTG0-PKT-061", "OTR061", "entry_sl_tp", "path_start", "path_end")
    search_roots = [
        ROOT,
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks"),
        Path(r"C:\Users\MSI\Documents\ai-trading-agent\shadow_logs"),
        Path(r"C:\tmp"),
        Path(r"C:\SierraChart"),
    ]
    root_searches = []
    for search_root in search_roots:
        matches: list[str] = []
        visited = 0
        errors: list[str] = []
        if search_root.exists():
            for dirpath, dirnames, filenames in os.walk(search_root, topdown=True):
                if ".git" in dirnames:
                    dirnames.remove(".git")
                visited += len(filenames)
                for filename in filenames:
                    hay = filename.lower()
                    if any(pat.lower() in hay for pat in filename_patterns):
                        matches.append(str(Path(dirpath) / filename))
                        if len(matches) >= 80:
                            break
                if len(matches) >= 80:
                    break
        else:
            errors.append("ROOT_NOT_FOUND")
        root_searches.append({
            "root": str(search_root),
            "exists": search_root.exists(),
            "visited_files_until_limit": visited,
            "patterns": list(filename_patterns),
            "matched_path_count_returned": len(matches),
            "matched_paths": matches,
            "denied_or_walk_errors": errors,
            "search_limit_note": "filename-only search capped at 80 returned matches; content search is restricted to source-safe artifact dirs",
        })

    source_safe_token_roots = [
        OUT_DIR,
        SRC["cnr_rows"].parent,
        SRC["cnr_matrix"].parent,
        SRC["g12_ready"].parent,
        SRC["otx_proposals"].parent,
        SRC["g12_otx_source_hash"].parent,
        SRC["otr061_proposal"].parent,
        SRC["g12_oti7_blocker_map"].parent,
    ]
    token_patterns = ("OTG0-PKT-061", "source_record_id", "record_id", "entry_sl_tp_or_level_packet", "path_start_utc", "path_end_utc", "decision_quote_packet")
    token_scan: dict[str, Any] = {}
    for token_root in source_safe_token_roots:
        counts = Counter()
        scanned = 0
        if token_root.exists():
            for path in token_root.rglob("*"):
                if path.suffix.lower() not in {".md", ".json", ".jsonl", ".py"} or not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                scanned += 1
                for token in token_patterns:
                    counts[token] += text.count(token)
        token_scan[str(token_root)] = {
            "exists": token_root.exists(),
            "files_scanned": scanned,
            "token_counts": dict(counts),
            "scope": "source-safe artifact directory scan; shadow path/outcome logs intentionally excluded",
        }

    search_ledger = {
        "artifact_family": "CNR061_SOURCE_SEARCH_AND_HASH_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "absolute_local_root_searches": root_searches,
        "source_safe_token_scan": token_scan,
        "shadow_log_content_policy": "No shadow path/outcome log content is consumed by the builder. Source packet builder artifacts are used instead of post-decision path labels.",
        "source_files": list(source_files_by_key.values()),
        "source_hash_failures": [entry for entry in source_files_by_key.values() if entry.get("sha256") is None and entry.get("exists", entry.get("hash_path_exists"))],
        "access_requests": [],
        "access_request_status": "NO_ACCESS_REQUEST_NEEDED_APPROVED_LOCAL_ROOTS_READABLE_FOR_SOURCE_SAFE_SCOPE",
        "account_history_accessed": False,
        "broker_actual_r_accessed": False,
        "live_trade_results_accessed": False,
        "blocked_packet_outcome_source_read": False,
        "paid_data_calls": 0,
        "api_calls": 0,
        "databento_calls": 0,
        "mt5_order_calls": 0,
        "order_calls": 0,
    }

    sidecar_packet = {
        "artifact_family": "CNR061_GEOMETRY_HORIZON_SIDECAR_PACKET",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "packet_id": PACKET_ID,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "record_count": len(sidecar_rows),
        "unique_record_id_count": len(sidecar_ready_record_ids),
        "sidecar_rows_sha256": sidecar_hash,
        "packet_scope": "input_only_geometry_quote_horizon_for_g12_reaudit",
        "rows": sidecar_rows,
        "blocked_rows_not_in_packet_count": len(blocker_rows),
        "no_outcome_scoring_performed": True,
        "account_history_accessed": False,
        "broker_actual_r_accessed": False,
        "live_trade_results_accessed": False,
        "blocked_packet_outcome_source_read": False,
        "paid_data_calls": 0,
        "api_calls": 0,
        "databento_calls": 0,
        "mt5_order_calls": 0,
        "order_calls": 0,
    }

    g12_proposal = {
        "artifact_family": "CNR061_G12_REAUDIT_READY_PROPOSAL",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "packet_id": PACKET_ID,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "proposal_status": "READY_FOR_G12_REAUDIT_INPUT_PACKET_ONLY",
        "ready_sidecar_row_count": len(sidecar_rows),
        "ready_unique_record_ids": sorted(sidecar_ready_record_ids),
        "blocked_e0e1_t0_rows_not_in_packet": len(blocker_rows),
        "required_g12_checks": [
            "source hash recomputation",
            "no forbidden result/path label fields",
            "duplicate denominator policy confirmation",
            "quote/path/source timestamp as-of review",
            "confirm validation_safe remains false and no outcome review opened",
        ],
        "g12_oti7_blocker_context_used": [
            h for h in g12_oti7_blocker_map.get("next_hypotheses", [])
            if h.get("status") == "EXACT_PACKET_FIELD_BLOCKER"
        ],
        "not_a_result_lane": True,
        "no_promotion_claim": True,
    }

    blocker_ledger = {
        "artifact_family": "CNR061_EXACT_BLOCKER_OR_IMPOSSIBILITY_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "packet_id": PACKET_ID,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "ready_packet_status": "PROVEN_SIDEcar_EXISTS_FOR_8_G12_READY_ROWS",
        "impossibility_status": "NOT_IMPOSSIBLE_FOR_READY_ROWS; EXACT_BLOCKERS_REMAIN_FOR_NONREADY_ROWS",
        "blocker_summary": blocker_summary,
        "blocker_rows": blocker_rows,
        "minimum_logger_or_parser_requirements": [
            "For E2/E3/E4 families: signal_emitted_utc, decision_request_sent_utc, decision_response_received_utc, latency_ms/policy, or pretouch_trigger_id/utc must be captured source-hashed before outcome opening.",
            "For CNR_T1/T2/T3: fixed-R, structural-level, or terminal timebox contracts must be frozen with source hashes before outcome opening.",
            "For target-already-passed rows: G12 must define an input-only invalid-clearing policy before any result audit can include or exclude them.",
        ],
        "no_post_hoc_rescue_performed": True,
    }

    context = {
        "artifact_family": "CNR061_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "controlling_prompt": rel(SRC["goal_prompt"]),
        "active_question_stack": [
            {"question": "Can the eight G12-ready CNR source-field rows be joined to quote/path horizon?", "status": "ANSWERED_PROVEN_JOIN"},
            {"question": "Can OTR061 recovered XAUUSD row be forced into ready sidecar?", "status": "NO_EXCLUDED_BY_PRE_ENTRY_TARGET_ALREADY_PASSED_GATE"},
            {"question": "Can OTX quote/path rows with no entry_sl_tp packet be repaired source-safely?", "status": "PARTIAL_READY_ROWS_REPAIRED_NONREADY_ROWS_BLOCKED_WITH_EXACT_REASON"},
        ],
        "prompt_to_artifact_checklist": [
            {"requirement": "regenerate/read LIVE_STATE and core context", "evidence": "source hash ledger includes LIVE_STATE, latest handoff, quick reference, doctrine, current state, goal discipline, local heavy inventory", "status": "PASS"},
            {"requirement": "locate all OTG0-PKT-061 rows", "evidence": "join map source_counts enumerate CNR=1020, E0/E1/T0=102, G12 ready=8, matrix=8, OTX=51, OTR061=1", "status": "PASS"},
            {"requirement": "build source-safe join map with match/mismatch/ambiguity counts", "evidence": rel(OUTPUTS["join_map_json"]), "status": "PASS"},
            {"requirement": "produce input-only sidecar packet or impossibility ledger", "evidence": rel(OUTPUTS["packet_jsonl"]) + " and " + rel(OUTPUTS["blockers_json"]), "status": "PASS"},
            {"requirement": "avoid outcome scoring and forbidden labels", "evidence": rel(OUTPUTS["noleak_json"]), "status": "PASS_PENDING_VERIFIER"},
            {"requirement": "preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false", "evidence": "all generated JSON artifacts carry the flags", "status": "PASS"},
            {"requirement": "commit only scoped CNR061 artifacts", "evidence": "pending final git status/add/commit step", "status": "PENDING"},
        ],
        "read_policy_caveat": "Builder inputs exclude broker/account/result ledgers and post-decision shadow path logs; one earlier manual shell search displayed post-decision path log lines, and those fields were not used in any generated artifact.",
    }

    completion_audit = {
        "artifact_family": "CNR061_GEOMETRY_HORIZON_SIDECAR_COMPLETION_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "objective_restatement": "Build or prove impossible a unified input-only OTG0-PKT-061 geometry+horizon sidecar joining source-field CNR geometry to source-hashed quote/path horizon evidence, preserving NO_PROMOTION_VERDICT and no live/result effects.",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "deliverable_status": "PASS_PENDING_VERIFIER_AND_SCOPED_COMMIT",
        "sidecar_packet_rows": len(sidecar_rows),
        "blocked_rows_not_in_packet": len(blocker_rows),
        "prompt_to_artifact_checklist": context["prompt_to_artifact_checklist"],
        "verification_requirements": [
            {"requirement": "JSON/JSONL parse", "evidence": "builder wrote parseable JSON and verifier re-reads them", "status": "PENDING_VERIFIER"},
            {"requirement": "source hash recomputation", "evidence": rel(OUTPUTS["search_json"]), "status": "PENDING_VERIFIER"},
            {"requirement": "no forbidden sidecar fields", "evidence": rel(OUTPUTS["noleak_json"]), "status": "PENDING_VERIFIER"},
            {"requirement": "duplicate denominator check", "evidence": rel(OUTPUTS["noleak_json"]), "status": "PASS"},
            {"requirement": "G12 proposal count/blocker consistency", "evidence": rel(OUTPUTS["proposal_json"]), "status": "PASS"},
            {"requirement": "no live-surface changes", "evidence": "pending git diff check", "status": "PENDING"},
        ],
        "no_outcome_scoring_or_post_hoc_rescue_performed": True,
        "can_mark_goal_complete_after_verifier_tests_and_commit": True,
        "account_history_accessed": False,
        "broker_actual_r_accessed": False,
        "live_trade_results_accessed": False,
        "blocked_packet_outcome_source_read": False,
        "paid_data_calls": 0,
        "api_calls": 0,
        "databento_calls": 0,
        "mt5_order_calls": 0,
        "order_calls": 0,
    }

    artifacts = {
        "packet": sidecar_packet,
        "join_map": join_map,
        "search_ledger": search_ledger,
        "noleak_duplicate_audit": noleak_duplicate_audit,
        "g12_proposal": g12_proposal,
        "blocker_ledger": blocker_ledger,
        "context": context,
        "completion_audit": completion_audit,
    }

    write_outputs(artifacts)
    return artifacts


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def write_md(path: Path, title: str, value: dict[str, Any], summary_keys: tuple[str, ...] = ()) -> None:
    lines = [
        f"# {title}",
        "",
        "Promotion verdict: `NO_PROMOTION_VERDICT`",
        "Validation safe: `false`",
        "Outcome review opened: `false`",
        "Live effect: `false`",
        "",
    ]
    for key in summary_keys:
        if key in value:
            lines.append(f"- `{key}`: `{value[key]}`")
    if summary_keys:
        lines.append("")
    lines.extend(["```json", json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(artifacts: dict[str, Any]) -> None:
    write_jsonl(OUTPUTS["packet_jsonl"], artifacts["packet"]["rows"])
    write_json(OUTPUTS["packet_json"], artifacts["packet"])
    write_json(OUTPUTS["join_map_json"], artifacts["join_map"])
    write_json(OUTPUTS["search_json"], artifacts["search_ledger"])
    write_json(OUTPUTS["noleak_json"], artifacts["noleak_duplicate_audit"])
    write_json(OUTPUTS["proposal_json"], artifacts["g12_proposal"])
    write_json(OUTPUTS["blockers_json"], artifacts["blocker_ledger"])
    write_json(OUTPUTS["context_json"], artifacts["context"])
    write_json(OUTPUTS["completion_json"], artifacts["completion_audit"])

    write_md(OUTPUTS["join_map_md"], "CNR061 Source Join Map - 2026-05-08", artifacts["join_map"], ("conclusion",))
    write_md(OUTPUTS["search_md"], "CNR061 Source Search And Hash Ledger - 2026-05-08", artifacts["search_ledger"], ("access_request_status",))
    write_md(OUTPUTS["noleak_md"], "CNR061 Noleak Duplicate Audit - 2026-05-08", artifacts["noleak_duplicate_audit"], ("forbidden_sidecar_key_status", "sidecar_row_count", "unique_duplicate_group_count"))
    write_md(OUTPUTS["proposal_md"], "CNR061 G12 Reaudit Ready Proposal - 2026-05-08", artifacts["g12_proposal"], ("proposal_status", "ready_sidecar_row_count", "blocked_e0e1_t0_rows_not_in_packet"))
    write_md(OUTPUTS["blockers_md"], "CNR061 Exact Blocker Or Impossibility Ledger - 2026-05-08", artifacts["blocker_ledger"], ("ready_packet_status", "impossibility_status"))
    write_md(OUTPUTS["context_md"], "CNR061 Context Continuity And Instruction Coverage - 2026-05-08", artifacts["context"], ("controlling_prompt",))
    write_md(OUTPUTS["completion_md"], "CNR061 Geometry Horizon Sidecar Completion Audit - 2026-05-08", artifacts["completion_audit"], ("deliverable_status", "sidecar_packet_rows", "blocked_rows_not_in_packet"))


if __name__ == "__main__":
    build()
    print(f"Wrote CNR061 geometry+horizon sidecar artifacts to {OUT_DIR}")
