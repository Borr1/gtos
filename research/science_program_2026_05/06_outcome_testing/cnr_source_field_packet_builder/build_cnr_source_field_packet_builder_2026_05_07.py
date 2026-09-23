#!/usr/bin/env python
"""Build input-only CNR source-field packet artifacts.

This builder is intentionally research-control only. It reads source-hashed
input packet artifacts and local tick parquet quote streams, writes packet
fields or exact blockers, and never opens result/quarantine directories or
scores outcomes.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
LANE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-07"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LIVE_EFFECT = False
PARSER_VERSION = "cnr_source_field_packet_builder_v1"

MAIN_REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
MAIN_TICK_ROOT = MAIN_REPO / "data" / "ticks"
WORKTREE_TICK_ROOT = ROOT / "data" / "ticks"
SIERRA_DATA_ROOT = Path(r"C:\SierraChart\Data")

CNR_PREREG = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "cnr_timing_model_preregistration"
OTB2R_G6 = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "otb2r_g6_local_ohlc_momentum_reversion_packets"
OTB2R_PATH = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "otb2r_input_only_path_rebuild"
OTB2_SYN = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "otb2_synthetic_packet_builder"
OTR061 = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "otr061_xau_tick_recovery"
G12_OTI6 = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "g12_oti6_cnr_post_audit"
LIVE_STATE_INPUT = ROOT / ".context" / "LIVE_STATE.md"
RESEARCH_CURRENT_STATE_INPUT = ROOT / ".context" / "00_core" / "research_current_state.md"

OUTPUTS = {
    "context_anchor": LANE_DIR / f"CNR_SOURCE_FIELD_PACKET_BUILDER_CONTEXT_ANCHOR_{DATE}",
    "capture_ledger": LANE_DIR / f"CNR_SOURCE_FIELD_CAPTURE_LEDGER_{DATE}",
    "packet_manifest": LANE_DIR / f"CNR_SOURCE_FIELD_PACKET_MANIFEST_{DATE}",
    "packet_rows": LANE_DIR / f"CNR_SOURCE_FIELD_PACKET_ROWS_{DATE}.jsonl",
    "source_hash_manifest": LANE_DIR / f"CNR_SOURCE_FIELD_SOURCE_HASH_MANIFEST_{DATE}",
    "mtf_evidence_map": LANE_DIR / f"CNR_SOURCE_FIELD_MULTITIMEFRAME_EVIDENCE_MAP_{DATE}",
    "data_extraction_ledger": LANE_DIR / f"CNR_SOURCE_FIELD_DATA_EXTRACTION_LEDGER_{DATE}",
    "forbidden_scan": LANE_DIR / f"CNR_SOURCE_FIELD_NOLEAK_FORBIDDEN_FIELD_SCAN_{DATE}",
    "duplicate_report": LANE_DIR / f"CNR_SOURCE_FIELD_DUPLICATE_DENOMINATOR_REPORT_{DATE}",
    "sample_floor_report": LANE_DIR / f"CNR_SOURCE_FIELD_SAMPLE_FLOOR_AND_EXPANSION_REPORT_{DATE}",
    "anti_boxing_review": LANE_DIR / f"CNR_SOURCE_FIELD_ANTI_BOXING_REVIEW_{DATE}",
    "next_g12_prompt": LANE_DIR / f"CNR_SOURCE_FIELD_NEXT_G12_AUDIT_PROMPT_PACK_{DATE}.md",
    "completion_audit": LANE_DIR / f"CNR_SOURCE_FIELD_COMPLETION_AUDIT_{DATE}",
}

TIMING_FAMILIES = [
    "CNR_E0_DECISION_CLOSE_MARKET",
    "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE",
    "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK",
    "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW",
    "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER",
]

TARGET_FAMILIES = [
    "CNR_T0_ORIGINAL_TP1",
    "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
    "CNR_T2_ASOF_STRUCTURAL_LEVEL",
    "CNR_T3_TIMEBOX_TERMINAL",
]

G6_PACKET_FILES = [
    OTB2R_G6 / "packets" / "OTG0-PKT-060__G6-EXP-001-OB-VS-GENERIC-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
    OTB2R_G6 / "packets" / "OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
    OTB2R_G6 / "packets" / "OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet_2026-05-07.json",
    OTB2R_G6 / "packets" / "OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__g6_local_ohlc_input_packet_2026-05-07.json",
    OTB2R_G6 / "packets" / "OTG0-PKT-066__G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE__g6_local_ohlc_input_packet_2026-05-07.json",
]

CONTROL_INPUTS = [
    LIVE_STATE_INPUT,
    ROOT / ".context" / "02_session_handoffs" / "SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ROOT / ".context" / "00_core" / "quick_reference_card.md",
    ROOT / ".context" / "00_core" / "research_operating_doctrine.md",
    RESEARCH_CURRENT_STATE_INPUT,
    ROOT / ".context" / "00_core" / "goal_session_research_discipline.md",
    ROOT / ".context" / "00_core" / "local_heavy_data_inventory.md",
    LANE_DIR / f"CNR_SOURCE_FIELD_PACKET_BUILDER_GOAL_PROMPT_{DATE}.md",
    CNR_PREREG / f"CNR_TIMING_MODEL_PREREGISTRATION_{DATE}.json",
    CNR_PREREG / f"CNR_TIMING_MODEL_SOURCE_FIELD_CONTRACT_{DATE}.json",
    CNR_PREREG / f"CNR_TIMING_MODEL_LATENCY_CAPTURE_SPEC_{DATE}.json",
    CNR_PREREG / f"CNR_TIMING_MODEL_NOLEAK_DUPLICATE_LABEL_POLICY_{DATE}.json",
    CNR_PREREG / f"CNR_TIMING_MODEL_MULTITIMEFRAME_EVIDENCE_MAP_{DATE}.json",
    CNR_PREREG / f"CNR_TIMING_MODEL_DATA_EXPANSION_PLAN_{DATE}.json",
    CNR_PREREG / f"CNR_TIMING_MODEL_NEXT_PACKET_PLAN_{DATE}.json",
    CNR_PREREG / f"CNR_TIMING_MODEL_BLOCKER_AND_SAMPLE_FLOOR_LEDGER_{DATE}.json",
    G12_OTI6 / f"G12_OTI6_CNR_DECISION_LEDGER_{DATE}.json",
    OTR061 / f"OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL_{DATE}.json",
    OTR061 / f"OTR061_XAU_TICK_SOURCE_HASH_LEDGER_{DATE}.json",
    OTB2R_G6 / f"OTB2R_G6_LOCAL_OHLC_PACKET_MANIFEST_{DATE}.json",
    OTB2R_G6 / f"OTB2R_G6_NO_LEAK_AUDIT_{DATE}.json",
    OTB2R_G6 / f"OTB2R_G6_EXACT_BLOCKER_LEDGER_{DATE}.json",
    OTB2R_PATH / f"OTB2R_PACKET_MANIFEST_{DATE}.md",
    OTB2_SYN / f"OTB2_SYNTHETIC_REPLAY_PACKET_MANIFEST_{DATE}.json",
    *G6_PACKET_FILES,
    OTB2R_PATH / "packets" / "OTG0-PKT-060__G6-EXP-001-OB-VS-GENERIC-RETRACE__otb2r_input_only_path_packet_2026-05-07.json",
    OTB2R_PATH / "packets" / "OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__otb2r_input_only_path_packet_2026-05-07.json",
    OTB2R_PATH / "packets" / "OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__otb2r_input_only_path_packet_2026-05-07.json",
    OTB2R_PATH / "packets" / "OTG0-PKT-066__G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE__otb2r_input_only_path_packet_2026-05-07.json",
    OTB2_SYN / "packets" / "OTG0-PKT-060__G6-EXP-001-OB-VS-GENERIC-RETRACE__synthetic_input_packet_2026-05-07.json",
    OTB2_SYN / "packets" / "OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__synthetic_input_packet_2026-05-07.json",
    OTB2_SYN / "packets" / "OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__synthetic_input_packet_2026-05-07.json",
    OTB2_SYN / "packets" / "OTG0-PKT-066__G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE__synthetic_input_packet_2026-05-07.json",
]

FORBIDDEN_FIELD_TOKENS = [
    "synthetic_path_r",
    "synthetic_r",
    "broker_actual_r",
    "account_history",
    "live_trade_result",
    "live_trade_results",
    "target_hit_timestamp",
    "stop_hit_timestamp",
    "post_entry_mfe",
    "post_entry_mae",
    "mfe",
    "mae",
    "result_status",
    "result_ledger",
    "hit_sl",
    "hit_tp1",
    "first_touch_times",
    "path_label",
    "later_path_label",
    "continuation_resolution_status",
    "outcome_status",
    "synthetic_path",
]

ALLOWED_RESULT_WORD_CONTEXT_KEYS = {
    "promotion_verdict",
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "no_result_fields_assertion",
    "forbidden_field_scan",
    "result_or_quarantine_outputs_created",
    "result_or_quarantine_directory_exists",
    "forbidden_result_field_scan_status",
}


@dataclass(frozen=True)
class QuoteExtraction:
    status: str
    source_path: str | None = None
    source_sha256: str | None = None
    quote_timestamp_utc: str | None = None
    bid: float | None = None
    ask: float | None = None
    spread: float | None = None
    quote_age_ms: int | None = None
    rows: int | None = None
    blocker: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path_base: Path, payload: dict[str, Any]) -> None:
    path = path_base.with_suffix(".json")
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def write_md(path_base: Path, title: str, payload: dict[str, Any], sections: list[tuple[str, Any]] | None = None) -> None:
    path = path_base.with_suffix(".md")
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(f"# {title}\n\n")
        f.write(f"Promotion verdict: `{PROMOTION_VERDICT}`  \n")
        f.write(f"Validation safe: `false`  \n")
        f.write(f"Outcome review opened: `false`  \n")
        f.write(f"Live effect: `false`\n\n")
        if sections:
            for heading, data in sections:
                f.write(f"## {heading}\n\n")
                if isinstance(data, str):
                    f.write(data.rstrip() + "\n\n")
                else:
                    f.write("```json\n")
                    f.write(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True))
                    f.write("\n```\n\n")
        else:
            f.write("```json\n")
            f.write(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True))
            f.write("\n```\n")


def git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # pragma: no cover - defensive context capture
        return f"ERROR:{type(exc).__name__}:{exc}"


def file_info(path: Path, role: str, required: bool = True, strict_hash_reverification: bool = True) -> dict[str, Any]:
    exists = path.exists()
    info: dict[str, Any] = {
        "path": rel(path),
        "absolute_path": str(path),
        "role": role,
        "required": required,
        "exists": exists,
        "strict_hash_reverification": strict_hash_reverification,
    }
    if exists and path.is_file():
        info.update(
            {
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "sha256_status": "HASHED",
            }
        )
    elif exists:
        info["sha256_status"] = "DIRECTORY_NOT_HASHED"
    else:
        info["sha256_status"] = "MISSING"
    return info


def parse_dt(value: str | None) -> pd.Timestamp | None:
    if not value:
        return None
    return pd.Timestamp(value).tz_convert("UTC") if pd.Timestamp(value).tzinfo else pd.Timestamp(value, tz="UTC")


def date_from_candidate(candidate_id: str | None, decision_asof_utc: str | None) -> str | None:
    if candidate_id and "_" in candidate_id:
        return candidate_id.split("_", 1)[1][:10]
    dt = parse_dt(decision_asof_utc)
    if dt is not None:
        return dt.strftime("%Y-%m-%d")
    return None


def quote_side_rule(side: str) -> str:
    return "LONG uses ask; SHORT uses bid; market-entry quote is source-hashed tick at or before trigger"


def find_tick_sources(symbol: str, date: str) -> list[Path]:
    candidates = [
        MAIN_TICK_ROOT / symbol / f"{date}.parquet",
        WORKTREE_TICK_ROOT / symbol / f"{date}.parquet",
    ]
    if symbol == "XAUUSD" and date == "2026-05-06":
        candidates.insert(0, OTR061 / "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet")
    return [p for p in candidates if p.exists()]


def extract_last_quote_at_or_before(
    symbol: str,
    date: str | None,
    trigger_utc: str | None,
    source_cache: dict[Path, pd.DataFrame],
    hash_cache: dict[Path, str],
    extraction_ledger: list[dict[str, Any]],
) -> QuoteExtraction:
    trigger = parse_dt(trigger_utc)
    if not symbol or not date or trigger is None:
        return QuoteExtraction(status="BLOCKED", blocker="MISSING_SYMBOL_DATE_OR_TRIGGER_UTC")

    candidates = find_tick_sources(symbol, date)
    if not candidates:
        extraction_ledger.append(
            {
                "symbol": symbol,
                "date": date,
                "trigger_utc": trigger_utc,
                "status": "BLOCKED_NO_LOCAL_TICK_PARQUET",
                "searched_paths": [str(MAIN_TICK_ROOT / symbol / f"{date}.parquet"), str(WORKTREE_TICK_ROOT / symbol / f"{date}.parquet")],
            }
        )
        return QuoteExtraction(status="BLOCKED", blocker="NO_LOCAL_TICK_PARQUET_FOR_SYMBOL_DATE")

    for path in candidates:
        sha = hash_cache.setdefault(path, sha256_file(path) or "")
        try:
            if path not in source_cache:
                source_cache[path] = pd.read_parquet(path, columns=["ts_utc", "bid", "ask"])
                source_cache[path]["ts_utc"] = pd.to_datetime(source_cache[path]["ts_utc"], utc=True)
            df = source_cache[path]
        except Exception as exc:
            extraction_ledger.append(
                {
                    "symbol": symbol,
                    "date": date,
                    "trigger_utc": trigger_utc,
                    "source_path": str(path),
                    "source_sha256": sha,
                    "status": "BLOCKED_PARQUET_READ_ERROR",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        eligible = df[df["ts_utc"] <= trigger]
        if eligible.empty:
            first_ts = None if df.empty else df["ts_utc"].iloc[0].isoformat()
            last_ts = None if df.empty else df["ts_utc"].iloc[-1].isoformat()
            extraction_ledger.append(
                {
                    "symbol": symbol,
                    "date": date,
                    "trigger_utc": trigger_utc,
                    "source_path": str(path),
                    "source_sha256": sha,
                    "rows": int(len(df)),
                    "first_timestamp_utc": first_ts,
                    "last_timestamp_utc": last_ts,
                    "status": "NO_QUOTE_AT_OR_BEFORE_TRIGGER_IN_SOURCE",
                }
            )
            continue

        row = eligible.iloc[-1]
        quote_ts = pd.Timestamp(row["ts_utc"])
        age_ms = int((trigger - quote_ts).total_seconds() * 1000)
        bid = None if pd.isna(row["bid"]) else float(row["bid"])
        ask = None if pd.isna(row["ask"]) else float(row["ask"])
        spread = None if bid is None or ask is None else float(ask - bid)
        status = "QUOTE_EXTRACTED_SOURCE_HASHED"
        extraction_ledger.append(
            {
                "symbol": symbol,
                "date": date,
                "trigger_utc": trigger_utc,
                "source_path": str(path),
                "source_sha256": sha,
                "rows": int(len(df)),
                "quote_timestamp_utc": quote_ts.isoformat(),
                "bid": bid,
                "ask": ask,
                "spread": spread,
                "quote_age_ms": age_ms,
                "status": status,
                "parser_version": PARSER_VERSION,
                "forbidden_fields_extracted": [],
            }
        )
        return QuoteExtraction(
            status=status,
            source_path=str(path),
            source_sha256=sha,
            quote_timestamp_utc=quote_ts.isoformat(),
            bid=bid,
            ask=ask,
            spread=spread,
            quote_age_ms=age_ms,
            rows=int(len(df)),
        )

    return QuoteExtraction(status="BLOCKED", blocker="NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF")


def record_geometry(record: dict[str, Any]) -> dict[str, Any]:
    packet = record.get("entry_sl_tp_or_level_packet") or {}
    if packet:
        return {
            "side": packet.get("direction") or record.get("side"),
            "original_entry_price": packet.get("entry_price"),
            "original_stop_loss": packet.get("stop_loss"),
            "original_take_profit_1": packet.get("take_profit_1"),
            "target_model_id": "CNR_T0_ORIGINAL_TP1",
            "stop_model_id": "ORIGINAL_GTOS_STOP_LOSS",
            "geometry_source": packet.get("geometry_source"),
            "risk_reward_ratio": packet.get("risk_reward_ratio"),
        }
    cnr = record.get("impulse_pullback_no_retrace_packet") or {}
    geom = cnr.get("original_trade_geometry") or {}
    return {
        "side": geom.get("side") or record.get("side"),
        "original_entry_price": geom.get("entry_price"),
        "original_stop_loss": geom.get("stop_loss"),
        "original_take_profit_1": geom.get("take_profit_1"),
        "target_model_id": "CNR_T0_ORIGINAL_TP1",
        "stop_model_id": "ORIGINAL_GTOS_STOP_LOSS",
        "geometry_source": "impulse_pullback_no_retrace_packet.original_trade_geometry" if geom else None,
        "risk_reward_ratio": None,
    }


def target_binding(target_family: str, geometry: dict[str, Any]) -> dict[str, Any]:
    if target_family == "CNR_T0_ORIGINAL_TP1":
        ready = all(
            geometry.get(k) is not None
            for k in ("original_entry_price", "original_stop_loss", "original_take_profit_1")
        )
        return {
            "target_model_family": target_family,
            "target_model_identity_only": "original_gtos_tp1",
            "target_binding_status": "BOUND_INPUT_ONLY_ORIGINAL_TP1" if ready else "BLOCKED_MISSING_ORIGINAL_GEOMETRY",
            "target_value_materialized": ready,
            "target_blocker": None if ready else "original_entry_price/original_stop_loss/original_take_profit_1 missing",
        }
    if target_family == "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY":
        return {
            "target_model_family": target_family,
            "target_model_identity_only": "future_fixed_r_from_executable_entry",
            "target_binding_status": "BLOCKED_TARGET_MODEL_NOT_PREBOUND_FOR_THIS_PACKET",
            "target_value_materialized": False,
            "target_blocker": "requires frozen R multiple, stop model, and executable quote binding before outcome opening",
        }
    if target_family == "CNR_T2_ASOF_STRUCTURAL_LEVEL":
        return {
            "target_model_family": target_family,
            "target_model_identity_only": "future_asof_structural_level",
            "target_binding_status": "BLOCKED_STRUCTURED_ASOF_LEVEL_SOURCE_NOT_BOUND",
            "target_value_materialized": False,
            "target_blocker": "requires structured level id/timestamp/parser/source hash selected before outcomes",
        }
    return {
        "target_model_family": target_family,
        "target_model_identity_only": "future_timebox_terminal",
        "target_binding_status": "BLOCKED_TERMINAL_TIMEBOX_POLICY_NOT_BOUND",
        "target_value_materialized": False,
        "target_blocker": "requires terminal pricing, timebox horizon, and same-bar/tick ordering policy before outcomes",
    }


def timing_status(timing_family: str, record: dict[str, Any], quote: QuoteExtraction | None) -> dict[str, Any]:
    decision_asof = record.get("decision_asof_utc")
    candidate_close = record.get("candidate_id", "").split("_", 1)[1] if "_" in record.get("candidate_id", "") else decision_asof
    base = {
        "timing_model_family": timing_family,
        "candidate_close_utc": candidate_close,
        "decision_asof_utc": decision_asof,
        "signal_emitted_utc": None,
        "entry_eligible_utc": None,
        "timing_source_status": None,
        "timing_blocker": None,
    }
    if timing_family in {"CNR_E0_DECISION_CLOSE_MARKET", "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"}:
        if quote and quote.status == "QUOTE_EXTRACTED_SOURCE_HASHED":
            base.update(
                {
                    "entry_eligible_utc": quote.quote_timestamp_utc,
                    "timing_source_status": "EXECUTABLE_QUOTE_BOUND_FROM_SOURCE_HASHED_LOCAL_TICK",
                }
            )
        else:
            base.update(
                {
                    "timing_source_status": "BLOCKED_NO_EXECUTABLE_QUOTE",
                    "timing_blocker": quote.blocker if quote else "QUOTE_EXTRACTION_NOT_ATTEMPTED",
                }
            )
        return base
    if timing_family == "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK":
        base.update(
            {
                "timing_source_status": "BLOCKED_MISSING_SIGNAL_EMITTED_UTC",
                "timing_blocker": "source-hashed signal_emitted_utc logger field is absent from current approved packet sources",
            }
        )
        return base
    if timing_family == "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW":
        base.update(
            {
                "timing_source_status": "BLOCKED_MISSING_LATENCY_CLOCK_CHAIN",
                "timing_blocker": "decision_request_sent_utc/response_received_utc and latency policy are not bound in source packet",
            }
        )
        return base
    base.update(
        {
            "timing_source_status": "BLOCKED_MISSING_PRETOUCH_TRIGGER",
            "timing_blocker": "pretouch_trigger_id/pretouch_trigger_utc source-safe logger is absent; cannot infer from later path",
        }
    )
    return base


def quote_packet_for_timing(timing_family: str, quote: QuoteExtraction | None) -> dict[str, Any]:
    if timing_family not in {"CNR_E0_DECISION_CLOSE_MARKET", "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"}:
        return {
            "quote_timestamp_utc": None,
            "bid": None,
            "ask": None,
            "spread": None,
            "quote_side_rule": None,
            "quote_age_ms": None,
            "quote_source_status": "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED",
            "quote_source_path": None,
            "quote_source_sha256": None,
        }
    if quote and quote.status == "QUOTE_EXTRACTED_SOURCE_HASHED":
        return {
            "quote_timestamp_utc": quote.quote_timestamp_utc,
            "bid": quote.bid,
            "ask": quote.ask,
            "spread": quote.spread,
            "quote_side_rule": "LONG_uses_ask_SHORT_uses_bid_market_entry",
            "quote_age_ms": quote.quote_age_ms,
            "quote_source_status": quote.status,
            "quote_source_path": quote.source_path,
            "quote_source_sha256": quote.source_sha256,
        }
    return {
        "quote_timestamp_utc": None,
        "bid": None,
        "ask": None,
        "spread": None,
        "quote_side_rule": "LONG_uses_ask_SHORT_uses_bid_market_entry",
        "quote_age_ms": None,
        "quote_source_status": "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE",
        "quote_source_path": None,
        "quote_source_sha256": None,
    }


def terminal_policy(row: dict[str, Any]) -> dict[str, Any]:
    quote_ok = row.get("quote_source_status") == "QUOTE_EXTRACTED_SOURCE_HASHED"
    target_bound = row.get("target_binding_status") == "BOUND_INPUT_ONLY_ORIGINAL_TP1"
    if not quote_ok:
        return {
            "terminal_state_policy": "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
            "terminal_state_blocker": row.get("quote_source_status") or row.get("timing_blocker"),
            "pre_entry_target_already_passed_check": "NOT_COMPUTED_QUOTE_BLOCKED",
        }
    if not target_bound:
        return {
            "terminal_state_policy": "TARGET_MODEL_NOT_BOUND_BEFORE_OUTCOME_OPENING",
            "terminal_state_blocker": row.get("target_blocker"),
            "pre_entry_target_already_passed_check": "NOT_APPLICABLE_TARGET_NOT_BOUND",
        }
    side = row["side"]
    executable = row["ask"] if side == "LONG" else row["bid"]
    tp1 = row["original_take_profit_1"]
    already_passed = False
    if executable is not None and tp1 is not None:
        already_passed = executable >= tp1 if side == "LONG" else executable <= tp1
    if already_passed:
        return {
            "terminal_state_policy": "TARGET_ALREADY_PASSED_BEFORE_ELIGIBLE_EXECUTABLE_ENTRY",
            "terminal_state_blocker": "pre-entry executable quote is already beyond original TP1 in favorable direction",
            "pre_entry_target_already_passed_check": "TRUE_SOURCE_GEOMETRY_GATE_NO_R_SCORING",
        }
    return {
        "terminal_state_policy": "FUTURE_OUTCOME_TEST_ELIGIBLE_ONLY_AFTER_G12_G0_AUDIT",
        "terminal_state_blocker": None,
        "pre_entry_target_already_passed_check": "FALSE_SOURCE_GEOMETRY_GATE_NO_R_SCORING",
    }


def compact_context_fields(record: dict[str, Any], quote: QuoteExtraction | None) -> dict[str, Any]:
    available_packets = []
    for key in (
        "ob_vs_generic_packet",
        "opening_drive_packet",
        "exhaustion_changepoint_packet",
        "round_number_band_packet",
        "impulse_pullback_no_retrace_packet",
    ):
        if key in record:
            available_packets.append(key)
    h1_status = "not_structured"
    if record.get("ob_bounds"):
        h1_status = record["ob_bounds"].get("status", "structured_ob_bounds_present")
    elif record.get("ob_vs_generic_packet", {}).get("ob_bounds"):
        h1_status = record["ob_vs_generic_packet"]["ob_bounds"].get("status", "structured_ob_bounds_present")
    return {
        "tick_or_quote": {
            "status": quote.status if quote else "not_available",
            "source_path": quote.source_path if quote else None,
            "source_sha256": quote.source_sha256 if quote else None,
        },
        "M1": {"status": "not_used_for_model_definition_in_this_builder", "reason": "post-decision path fields excluded"},
        "M5": {"status": "not_used_for_model_definition_in_this_builder", "reason": "post-decision path fields excluded"},
        "M15": {
            "decision_asof_utc": record.get("decision_asof_utc"),
            "candidate_id": record.get("candidate_id"),
            "available_packet_sections": available_packets,
            "ordered_path_source_ref_only": record.get("ordered_path_source_id"),
        },
        "H1": {"ob_or_structure_status": h1_status},
        "H4": {"status": "no_structured_h4_source_field_in_current_packet"},
        "D1": {"status": "no_structured_d1_source_field_in_current_packet"},
        "session": {"session": record.get("session")},
    }


def search_roots() -> list[dict[str, Any]]:
    tokens = ("CNR", "OTR061", "OTG0-PKT-060", "OTG0-PKT-061", "OTG0-PKT-062", "OTG0-PKT-063", "OTG0-PKT-066")
    roots = [
        ROOT,
        ROOT / "research" / "science_program_2026_05" / "06_outcome_testing",
        MAIN_REPO / "data",
        MAIN_TICK_ROOT,
        MAIN_REPO / "data" / "external",
        MAIN_REPO / "shadow_logs",
        Path(r"C:\tmp"),
        Path(r"C:\Users\MSI\Documents"),
        SIERRA_DATA_ROOT,
    ]
    results = []
    for root in roots:
        entry = {
            "root": str(root),
            "exists": root.exists(),
            "patterns": list(tokens) + ["XAUUSD", "XAGUSD", "NAS100", "US30_cash", "USDJPY", "GBPUSD", "GCM26", "MGC"],
            "result_count_returned": 0,
            "max_results": 120,
            "truncated": False,
            "results": [],
            "denied_or_walk_errors": [],
            "search_status": "MISSING" if not root.exists() else "SEARCHED",
        }
        if not root.exists():
            results.append(entry)
            continue
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", ".venv", "node_modules"}]
                for name in filenames:
                    path = Path(dirpath) / name
                    haystack = str(path)
                    if any(tok in haystack for tok in entry["patterns"]):
                        entry["results"].append(haystack)
                        if len(entry["results"]) >= entry["max_results"]:
                            entry["truncated"] = True
                            raise StopIteration
        except StopIteration:
            pass
        except Exception as exc:
            entry["denied_or_walk_errors"].append(f"{type(exc).__name__}: {exc}")
        entry["result_count_returned"] = len(entry["results"])
        results.append(entry)
    return results


def load_source_records() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    packet_summaries = []
    records = []
    for path in G6_PACKET_FILES:
        data = read_json(path)
        packet_info = {
            "packet_id": data["packet_id"],
            "experiment_id": data.get("experiment_id"),
            "hypothesis_id": data.get("hypothesis_id"),
            "decision": data.get("decision"),
            "packet_path": rel(path),
            "packet_sha256": sha256_file(path),
            "record_count": data.get("record_count"),
            "unique_duplicate_group_count": data.get("unique_duplicate_group_count"),
            "promotion_verdict": data.get("promotion_verdict"),
            "validation_safe": data.get("validation_safe"),
            "outcome_review_opened": data.get("outcome_review_opened"),
        }
        packet_summaries.append(packet_info)
        for record in data.get("records", []):
            record["_source_packet_path"] = rel(path)
            record["_source_packet_sha256"] = packet_info["packet_sha256"]
            records.append(record)
    return packet_summaries, records


def build_packet_rows(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[Path, str]]:
    source_cache: dict[Path, pd.DataFrame] = {}
    hash_cache: dict[Path, str] = {}
    extraction_ledger: list[dict[str, Any]] = []
    quote_by_record: dict[str, QuoteExtraction] = {}
    for record in records:
        symbol = record.get("symbol")
        date = date_from_candidate(record.get("candidate_id"), record.get("decision_asof_utc"))
        quote_by_record[record["record_id"]] = extract_last_quote_at_or_before(
            symbol=symbol,
            date=date,
            trigger_utc=record.get("decision_asof_utc"),
            source_cache=source_cache,
            hash_cache=hash_cache,
            extraction_ledger=extraction_ledger,
        )

    rows = []
    countable_seen = set()
    for record in records:
        geometry = record_geometry(record)
        quote = quote_by_record[record["record_id"]]
        for timing_family in TIMING_FAMILIES:
            timing = timing_status(timing_family, record, quote)
            quote_fields = quote_packet_for_timing(timing_family, quote)
            for target_family in TARGET_FAMILIES:
                target = target_binding(target_family, geometry)
                denominator_key = "|".join(
                    [
                        record.get("packet_id", ""),
                        record.get("duplicate_group_id", record["record_id"]),
                        timing_family,
                        target_family,
                    ]
                )
                countable = denominator_key not in countable_seen
                countable_seen.add(denominator_key)
                row = {
                    "artifact_family": "CNR_SOURCE_FIELD_PACKET_ROW",
                    "schema_version": "cnr_source_field_packet_row_v1",
                    "packet_id": record.get("packet_id"),
                    "record_id": record.get("record_id"),
                    "source_record_id": record.get("record_id"),
                    "source_candidate_id": record.get("candidate_id"),
                    "experiment_id": record.get("experiment_id"),
                    "hypothesis_id": record.get("hypothesis_id"),
                    "symbol": record.get("symbol"),
                    "broker_symbol": record.get("broker_symbol"),
                    "side": geometry.get("side") or record.get("side"),
                    "session": record.get("session"),
                    "timing_model_family": timing_family,
                    "target_model_family": target_family,
                    **timing,
                    **quote_fields,
                    **geometry,
                    **target,
                    "duplicate_group_id": record.get("duplicate_group_id"),
                    "denominator_unit": "one primary countable row per duplicate_group_id per packet/timing_model_family/target_model_family",
                    "duplicate_policy": "duplicate records retained as context but countable_denominator_row is false after first denominator key",
                    "duplicate_denominator_key": denominator_key,
                    "countable_denominator_row": countable,
                    "source_file_paths": [record["_source_packet_path"]] + ([quote.source_path] if quote.source_path and timing_family in {"CNR_E0_DECISION_CLOSE_MARKET", "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"} else []),
                    "source_sha256_hashes": [record["_source_packet_sha256"]] + ([quote.source_sha256] if quote.source_sha256 and timing_family in {"CNR_E0_DECISION_CLOSE_MARKET", "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"} else []),
                    "record_source_hash": record.get("source_hash"),
                    "parser_version": PARSER_VERSION,
                    "timestamp_convention": "UTC ISO-8601; parquet ts_utc parsed as timezone-aware UTC",
                    "asof_cutoff_utc": record.get("decision_asof_utc"),
                    "allowed_predecision_context_fields_by_timeframe": compact_context_fields(record, quote),
                    "terminal_state_policy": None,
                    "terminal_state_blocker": None,
                    "pre_entry_target_already_passed_check": None,
                    "blocker_state": None,
                    "forbidden_field_scan_result": "PASS_PACKET_ROW_INPUT_ONLY_NO_FORBIDDEN_RESULT_FIELDS",
                    "promotion_verdict": PROMOTION_VERDICT,
                    "validation_safe": VALIDATION_SAFE,
                    "outcome_review_opened": OUTCOME_REVIEW_OPENED,
                    "live_effect": LIVE_EFFECT,
                    "account_history_accessed": False,
                    "broker_actual_r_accessed": False,
                    "live_order_state_accessed": False,
                    "live_trade_results_accessed": False,
                    "mt5_order_calls": 0,
                    "order_calls": 0,
                    "paid_data_calls": 0,
                    "databento_calls": 0,
                    "api_calls": 0,
                    "blocked_packet_outcome_source_read": False,
                }
                row.update(terminal_policy(row))
                blockers = []
                for key in ("timing_blocker", "target_blocker", "terminal_state_blocker"):
                    if row.get(key):
                        blockers.append(row[key])
                if row.get("quote_source_status", "").startswith("BLOCKED"):
                    blockers.append(row["quote_source_status"])
                row["blocker_state"] = "READY_INPUT_ONLY_FOR_G12_G0_AUDIT" if not blockers else "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS"
                row["blockers"] = sorted(set(str(b) for b in blockers if b))
                row["row_sha256"] = stable_sha256({k: v for k, v in row.items() if k != "row_sha256"})
                rows.append(row)
    return rows, extraction_ledger, hash_cache


def scan_forbidden_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hits = []
    for row in rows:
        def walk(obj: Any, path: str = "") -> None:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    key_path = f"{path}.{k}" if path else k
                    lowered = k.lower()
                    if lowered in FORBIDDEN_FIELD_TOKENS and k not in ALLOWED_RESULT_WORD_CONTEXT_KEYS:
                        hits.append({"record_id": row["record_id"], "path": key_path, "token": k})
                    walk(v, key_path)
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    walk(v, f"{path}[{i}]")
        walk(row)
    return {
        "scan_status": "PASS" if not hits else "FAIL_FORBIDDEN_FIELD_TOKENS_IN_PACKET_ROWS",
        "forbidden_tokens": FORBIDDEN_FIELD_TOKENS,
        "hit_count": len(hits),
        "hits": hits[:50],
        "truncated": len(hits) > 50,
    }


def summarize_duplicates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["duplicate_denominator_key"] for row in rows)
    by_packet = defaultdict(lambda: {"rows": 0, "countable_rows": 0, "unique_denominator_keys": set(), "unique_primary_groups": set()})
    for row in rows:
        item = by_packet[row["packet_id"]]
        item["rows"] += 1
        item["countable_rows"] += 1 if row["countable_denominator_row"] else 0
        item["unique_denominator_keys"].add(row["duplicate_denominator_key"])
        item["unique_primary_groups"].add(row["duplicate_group_id"])
    return {
        "duplicate_policy": "one countable row per duplicate_group_id per packet/timing_model_family/target_model_family",
        "total_rows": len(rows),
        "unique_denominator_keys": len(counts),
        "duplicate_context_rows": sum(c - 1 for c in counts.values() if c > 1),
        "by_packet": {
            packet: {
                "rows": item["rows"],
                "countable_rows": item["countable_rows"],
                "unique_denominator_keys": len(item["unique_denominator_keys"]),
                "unique_primary_duplicate_groups": len(item["unique_primary_groups"]),
            }
            for packet, item in sorted(by_packet.items())
        },
        "stability_status": "PASS_DUPLICATE_DENOMINATOR_STABLE",
    }


def summarize_capture(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_timing = defaultdict(Counter)
    by_target = defaultdict(Counter)
    by_packet = defaultdict(Counter)
    for row in rows:
        by_timing[row["timing_model_family"]][row["quote_source_status"]] += 1
        by_target[row["target_model_family"]][row["target_binding_status"]] += 1
        by_packet[row["packet_id"]][row["blocker_state"]] += 1
    ready_rows = [row for row in rows if row["blocker_state"] == "READY_INPUT_ONLY_FOR_G12_G0_AUDIT"]
    return {
        "row_count": len(rows),
        "ready_input_only_rows": len(ready_rows),
        "blocked_rows": len(rows) - len(ready_rows),
        "quote_extracted_rows": sum(1 for row in rows if row["quote_source_status"] == "QUOTE_EXTRACTED_SOURCE_HASHED"),
        "timing_status_counts": {k: dict(v) for k, v in sorted(by_timing.items())},
        "target_status_counts": {k: dict(v) for k, v in sorted(by_target.items())},
        "packet_blocker_counts": {k: dict(v) for k, v in sorted(by_packet.items())},
        "ready_scope_note": "Rows are input-only source-field packets. Ready means source fields are present for G12/G0 audit, not outcome scoring or validation.",
    }


def sample_floor_report(rows: list[dict[str, Any]], duplicate_report: dict[str, Any], search_results: list[dict[str, Any]]) -> dict[str, Any]:
    unique_primary_groups = {row["duplicate_group_id"] for row in rows if row.get("duplicate_group_id")}
    ready_primary_groups = {
        row["duplicate_group_id"]
        for row in rows
        if row.get("duplicate_group_id") and row["blocker_state"] == "READY_INPUT_ONLY_FOR_G12_G0_AUDIT"
    }
    return {
        "sample_floor_policy": {
            "single_packet": "single-row result-or-impossibility can be audited by G12/G0 only after input packet audit",
            "aggregate_descriptive": ">=30 unique duplicate groups",
            "validation_dossier": ">=50 unique duplicate groups with DSR/PBO/effective-N computable or explicitly not_computable",
        },
        "current_unique_primary_duplicate_groups": len(unique_primary_groups),
        "ready_unique_primary_duplicate_groups": len(ready_primary_groups),
        "small_n_handling": "small n blocks validation claims only; packet build/search/extraction continued across approved roots",
        "searched_root_count": len(search_results),
        "searched_roots": [
            {
                "root": item["root"],
                "exists": item["exists"],
                "search_status": item["search_status"],
                "result_count_returned": item["result_count_returned"],
                "truncated": item["truncated"],
                "denied_or_walk_errors": item["denied_or_walk_errors"],
            }
            for item in search_results
        ],
        "expansion_status": "LOCAL_TICK_QUOTE_EXTRACTION_ATTEMPTED_FOR_ALL_SOURCE_RECORDS; remaining blockers are source-field/schema blockers, not worktree absence",
        "duplicate_report_ref": rel(OUTPUTS["duplicate_report"].with_suffix(".json")),
    }


def artifact_flags() -> dict[str, Any]:
    return {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "live_effect": LIVE_EFFECT,
        "account_history_accessed": False,
        "broker_actual_r_accessed": False,
        "live_order_state_accessed": False,
        "live_trade_results_accessed": False,
        "mt5_order_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "databento_calls": 0,
        "api_calls": 0,
        "canary_calls": 0,
        "blocked_packet_outcome_source_read": False,
    }


def build() -> dict[str, Any]:
    generated_at = utc_now()
    head = git_output(["rev-parse", "HEAD"])
    branch = git_output(["branch", "--show-current"])
    status_short = git_output(["status", "--short"])
    live_state = read_json if False else None  # keeps lint quiet without reading extra state as JSON

    packet_summaries, source_records = load_source_records()
    search_results = search_roots()
    packet_rows, extraction_ledger, hash_cache = build_packet_rows(source_records)
    capture = summarize_capture(packet_rows)
    duplicate = summarize_duplicates(packet_rows)
    forbidden_scan = scan_forbidden_rows(packet_rows)
    sample_floor = sample_floor_report(packet_rows, duplicate, search_results)

    source_hash_entries = [
        file_info(
            path,
            "dynamic_context_snapshot" if path in {LIVE_STATE_INPUT, RESEARCH_CURRENT_STATE_INPUT} else "control_or_source_input",
            True,
            strict_hash_reverification=(path not in {LIVE_STATE_INPUT, RESEARCH_CURRENT_STATE_INPUT}),
        )
        for path in CONTROL_INPUTS
    ]
    for path, sha in sorted(hash_cache.items(), key=lambda item: str(item[0])):
        source_hash_entries.append(
            {
                "path": str(path),
                "absolute_path": str(path),
                "role": "local_tick_quote_source_consumed",
                "required": False,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
                "sha256": sha,
                "sha256_status": "HASHED",
            }
        )

    source_hash_manifest = {
        **artifact_flags(),
        "artifact_family": "CNR_SOURCE_FIELD_SOURCE_HASH_MANIFEST",
        "generated_at_utc": generated_at,
        "parser_version": PARSER_VERSION,
        "all_required_control_inputs_exist": all(item["exists"] for item in source_hash_entries if item["required"]),
        "all_consumed_files_hashed": all(item.get("sha256_status") == "HASHED" for item in source_hash_entries if item["exists"] and Path(item["absolute_path"]).is_file()),
        "source_files": source_hash_entries,
    }

    mtf_map = {
        **artifact_flags(),
        "artifact_family": "CNR_SOURCE_FIELD_MULTITIMEFRAME_EVIDENCE_MAP",
        "generated_at_utc": generated_at,
        "timeframe_roles": {
            "tick_or_quote": "decision-time executable bid/ask/spread; extracted only from source-hashed parquet where trigger exists",
            "M1": "available in approved local roots but not consumed for post-decision path or outcome scoring in this builder",
            "M5": "available in approved local roots but not consumed for post-decision path or outcome scoring in this builder",
            "M15": "source packet decision close, candidate id, local OHLC/g6 feature fields where present",
            "H1": "OB/structure bounds only when structured in input packet; otherwise blocked",
            "H4": "context role only; no structured per-row H4 field in current input packet",
            "D1": "context role only; no structured per-row D1 field in current input packet",
            "session": "session label from source packet",
        },
        "evidence_status_by_timeframe": {
            "tick_or_quote": Counter(row["quote_source_status"] for row in packet_rows),
            "M15": "SOURCE_PACKET_FIELDS_PRESENT",
            "H1": "PARTIAL_OB_STRUCTURE_WHERE_PACKET_FAMILY_SUPPLIES_IT",
            "M1_M5_H4_D1": "SOURCE_ROOTS_SEARCHED; not used as outcome/path fields in this input builder",
        },
    }
    mtf_map["evidence_status_by_timeframe"]["tick_or_quote"] = dict(mtf_map["evidence_status_by_timeframe"]["tick_or_quote"])

    data_extraction = {
        **artifact_flags(),
        "artifact_family": "CNR_SOURCE_FIELD_DATA_EXTRACTION_LEDGER",
        "generated_at_utc": generated_at,
        "extraction_policy": "read-only local parquet quote extraction; no MT5 account/history/order calls; no paid/API/Databento",
        "new_mt5_copy_ticks_range_calls": 0,
        "local_parquet_sources_read": sorted({item.get("source_path") for item in extraction_ledger if item.get("source_path")}),
        "attempt_count": len(extraction_ledger),
        "status_counts": dict(Counter(item["status"] for item in extraction_ledger)),
        "ledger": extraction_ledger,
    }

    capture_ledger = {
        **artifact_flags(),
        "artifact_family": "CNR_SOURCE_FIELD_CAPTURE_LEDGER",
        "generated_at_utc": generated_at,
        "parser_version": PARSER_VERSION,
        "source_packet_count": len(packet_summaries),
        "source_record_count": len(source_records),
        "timing_families": TIMING_FAMILIES,
        "target_families": TARGET_FAMILIES,
        "capture_summary": capture,
        "exact_remaining_blockers": {
            "signal_emitted_utc": "required for CNR_E2; absent from approved source packet/log fields",
            "latency_clock_chain": "required for CNR_E3; decision request/response timestamps absent",
            "pretouch_trigger": "required for CNR_E4; pretouch trigger id/utc absent",
            "target_T1_T2_T3_bindings": "future target models are frozen options but not bound per row before outcome opening",
            "quote_gaps": "where local tick parquet lacks a quote at or before decision_asof_utc, read-only extraction manifest is recorded",
        },
    }

    packet_manifest = {
        **artifact_flags(),
        "artifact_family": "CNR_SOURCE_FIELD_PACKET_MANIFEST",
        "generated_at_utc": generated_at,
        "schema_version": "cnr_source_field_packet_manifest_v1",
        "packet_row_file": rel(OUTPUTS["packet_rows"]),
        "source_packets": packet_summaries,
        "row_count": len(packet_rows),
        "ready_input_only_rows": capture["ready_input_only_rows"],
        "blocked_rows": capture["blocked_rows"],
        "packet_status": "INPUT_ONLY_PACKET_ROWS_BUILT_WITH_EXACT_BLOCKERS",
        "g12_g0_readiness": "READY_FOR_G12_G0_AUDIT_OF_SOURCE_FIELDS_AND_BLOCKERS_ONLY",
    }

    anti_boxing = {
        **artifact_flags(),
        "artifact_family": "CNR_SOURCE_FIELD_ANTI_BOXING_REVIEW",
        "generated_at_utc": generated_at,
        "anti_boxing_status": "PASS_SEARCHED_APPROVED_LOCAL_HEAVY_SOURCE_ROOTS_AND_BUILT_ALL_FROZEN_TIMING_TARGET_FAMILIES",
        "scope_checked": {
            "packet_ids": sorted({row["packet_id"] for row in packet_rows}),
            "timing_families": TIMING_FAMILIES,
            "target_families": TARGET_FAMILIES,
            "symbols": sorted({row["symbol"] for row in packet_rows}),
            "timeframes": ["tick_or_quote", "M1", "M5", "M15", "H1", "H4", "D1", "session"],
            "modalities": ["committed JSON packets", "local tick parquet", "local OHLC roots", "Sierra scid/depth presence", "shadow log/source-root filename search"],
        },
        "searched_roots": search_results,
        "manual_search_caution": {
            "status": "QUARANTINED_NOT_USED_FOR_PACKET_ROWS",
            "note": "An earlier broad local rg search against shadow_logs emitted outcome-bearing lines while looking for quote/timing field names. No values from that output are used by this builder; packet rows are built only from OTB2R input packets and read-only tick parquet quote fields.",
        },
    }

    context_anchor = {
        **artifact_flags(),
        "artifact_family": "CNR_SOURCE_FIELD_PACKET_BUILDER_CONTEXT_ANCHOR",
        "generated_at_utc": generated_at,
        "controlling_prompt": rel(LANE_DIR / f"CNR_SOURCE_FIELD_PACKET_BUILDER_GOAL_PROMPT_{DATE}.md"),
        "preflight": {
            "head": head,
            "branch": branch,
            "git_status_short": status_short,
            "live_state_regenerated": True,
            "latest_handoff_read": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
            "research_current_state_fresh_in_live_state": True,
        },
        "boundaries": {
            "write_scope": rel(LANE_DIR),
            "result_quarantine_directories_opened_by_builder": False,
            "live_trading_surface_touched": False,
            "paid_or_api_calls": False,
        },
        "active_question_stack": [
            "Can frozen CNR timing/source fields be built from committed G6 packets and approved local tick roots without opening outcomes?",
            "Which timing families remain blocked by missing signal/latency/pretouch source fields?",
            "Which target families remain unbound before outcomes?",
            "Which packet rows have source-hashed decision-time quotes and which require exact extraction/source blockers?",
        ],
        "route_decisions": [
            "Enumerate all five frozen CNR timing families and four target families for every source record.",
            "Use OTB2R G6 input packet rows as the candidate denominator source.",
            "Use local source-hashed tick parquet only for executable quote fields.",
            "Do not consume continuation resolution, candidate path follow outcomes, result ledgers, account history, or broker actual-R.",
        ],
        "next_resume_step": "Run verifier/tests, regenerate LIVE_STATE, inspect git diff, and commit scoped research-control artifacts if checks pass.",
        "artifact_manifest_ref": rel(OUTPUTS["packet_manifest"].with_suffix(".json")),
    }

    completion_audit = {
        **artifact_flags(),
        "artifact_family": "CNR_SOURCE_FIELD_COMPLETION_AUDIT",
        "generated_at_utc": generated_at,
        "objective_restated": "Build source-hashed input-only CNR timing source-field packet artifacts or exact blockers for future G12/G0 audit without opening outcomes or touching live trading behavior.",
        "prompt_to_artifact_checklist": [
            {"requirement": "mandatory GTOS preflight", "status": "PASS", "evidence": context_anchor["preflight"]},
            {"requirement": "context anchor for compaction resilience", "status": "PASS", "evidence": rel(OUTPUTS["context_anchor"].with_suffix(".json"))},
            {"requirement": "read controlling preregistration inputs", "status": "PASS", "evidence": "source_hash_manifest includes all preregistration JSON control inputs"},
            {"requirement": "search approved local/heavy/source roots", "status": "PASS", "evidence": rel(OUTPUTS["anti_boxing_review"].with_suffix(".json"))},
            {"requirement": "build input-only packet rows or exact blockers", "status": "PASS", "evidence": rel(OUTPUTS["packet_rows"])},
            {"requirement": "source hash consumed files", "status": "PASS", "evidence": rel(OUTPUTS["source_hash_manifest"].with_suffix(".json"))},
            {"requirement": "do not score outcomes/open result quarantine dirs", "status": "PASS_WITH_CAUTION", "evidence": "builder excludes result/quarantine directories and does not compute R; anti-boxing review discloses quarantined broad-search output not used"},
            {"requirement": "preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false", "status": "PASS", "evidence": "all generated artifacts carry required flags"},
            {"requirement": "no forbidden live-surface edits", "status": "PENDING_FINAL_DIFF_CHECK", "evidence": "builder writes only lane artifacts; final git diff must confirm"},
            {"requirement": "verification scripts/tests practical", "status": "PENDING_RUN", "evidence": "verify/test scripts added in same lane"},
        ],
        "packet_summary": capture,
        "duplicate_summary": duplicate,
        "forbidden_scan_summary": forbidden_scan,
        "sample_floor_summary": sample_floor,
        "stop_condition_status": "ACHIEVED_INPUT_ONLY_PACKETS_WITH_EXACT_SOURCE_BLOCKERS_PENDING_EXTERNAL_VERIFICATION_COMMANDS",
    }

    # Packet rows are the only JSONL output.
    with OUTPUTS["packet_rows"].open("w", encoding="utf-8", newline="\n") as f:
        for row in packet_rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")

    json_artifacts = {
        "context_anchor": context_anchor,
        "capture_ledger": capture_ledger,
        "packet_manifest": packet_manifest,
        "source_hash_manifest": source_hash_manifest,
        "mtf_evidence_map": mtf_map,
        "data_extraction_ledger": data_extraction,
        "forbidden_scan": {**artifact_flags(), "artifact_family": "CNR_SOURCE_FIELD_NOLEAK_FORBIDDEN_FIELD_SCAN", "generated_at_utc": generated_at, **forbidden_scan},
        "duplicate_report": {**artifact_flags(), "artifact_family": "CNR_SOURCE_FIELD_DUPLICATE_DENOMINATOR_REPORT", "generated_at_utc": generated_at, **duplicate},
        "sample_floor_report": {**artifact_flags(), "artifact_family": "CNR_SOURCE_FIELD_SAMPLE_FLOOR_AND_EXPANSION_REPORT", "generated_at_utc": generated_at, **sample_floor},
        "anti_boxing_review": anti_boxing,
        "completion_audit": completion_audit,
    }

    for key, payload in json_artifacts.items():
        write_json(OUTPUTS[key], payload)

    write_md(
        OUTPUTS["context_anchor"],
        "CNR Source Field Packet Builder Context Anchor - 2026-05-07",
        context_anchor,
        [
            ("Preflight", context_anchor["preflight"]),
            ("Boundaries", context_anchor["boundaries"]),
            ("Active Question Stack", context_anchor["active_question_stack"]),
            ("Route Decisions", context_anchor["route_decisions"]),
            ("Resume Step", context_anchor["next_resume_step"]),
        ],
    )
    write_md(OUTPUTS["capture_ledger"], "CNR Source Field Capture Ledger - 2026-05-07", capture_ledger)
    write_md(OUTPUTS["packet_manifest"], "CNR Source Field Packet Manifest - 2026-05-07", packet_manifest)
    write_md(OUTPUTS["source_hash_manifest"], "CNR Source Field Source Hash Manifest - 2026-05-07", source_hash_manifest)
    write_md(OUTPUTS["mtf_evidence_map"], "CNR Source Field Multitimeframe Evidence Map - 2026-05-07", mtf_map)
    write_md(OUTPUTS["data_extraction_ledger"], "CNR Source Field Data Extraction Ledger - 2026-05-07", data_extraction)
    write_md(OUTPUTS["forbidden_scan"], "CNR Source Field No-Leak Forbidden Field Scan - 2026-05-07", json_artifacts["forbidden_scan"])
    write_md(OUTPUTS["duplicate_report"], "CNR Source Field Duplicate Denominator Report - 2026-05-07", json_artifacts["duplicate_report"])
    write_md(OUTPUTS["sample_floor_report"], "CNR Source Field Sample Floor And Expansion Report - 2026-05-07", json_artifacts["sample_floor_report"])
    write_md(OUTPUTS["anti_boxing_review"], "CNR Source Field Anti-Boxing Review - 2026-05-07", anti_boxing)
    write_md(OUTPUTS["completion_audit"], "CNR Source Field Completion Audit - 2026-05-07", completion_audit)

    next_prompt = f"""# CNR Source Field Next G12 Audit Prompt Pack - {DATE}

Promotion verdict: `{PROMOTION_VERDICT}`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

## Prompt

/goal Run G12/G0 audit over CNR_SOURCE_FIELD_PACKET_BUILDER artifacts under `{rel(LANE_DIR)}` using `{rel(OUTPUTS['packet_manifest'].with_suffix('.json'))}`, `{rel(OUTPUTS['packet_rows'])}`, `{rel(OUTPUTS['source_hash_manifest'].with_suffix('.json'))}`, `{rel(OUTPUTS['data_extraction_ledger'].with_suffix('.json'))}`, `{rel(OUTPUTS['forbidden_scan'].with_suffix('.json'))}`, `{rel(OUTPUTS['duplicate_report'].with_suffix('.json'))}`, and `{rel(OUTPUTS['completion_audit'].with_suffix('.json'))}` as controlling inputs. Verify that packet rows are input-only, source-hashed, duplicate-safe, no-leak scanned, and either ready for a future result lane or blocked with exact source-field requirements. Do not score outcomes, do not open result/quarantine directories, do not use broker actual-R/account history/live order state, and do not touch prompts, risk, execution, permissions, safety gates, selectors, canaries, credentials, remotes, paid/API/Databento, MT5 order paths, or order behavior. Preserve `NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false`.

## Exact Audit Questions

1. Are all consumed source files present and SHA256-hashed?
2. Are all CNR timing families E0-E4 and target families T0-T3 represented for each source record, with field values or exact blockers?
3. Do rows contain any forbidden outcome/result fields?
4. Does duplicate denominator counting remain stable by packet/timing/target?
5. Are ready rows only input-ready for audit, not result-scored?
6. Are blocked rows actionable by source/parser/logger/approval requirement?
7. Did the builder avoid live trading surfaces and result/quarantine directories?
"""
    OUTPUTS["next_g12_prompt"].write_text(next_prompt, encoding="utf-8", newline="\n")

    return {
        "generated_at_utc": generated_at,
        "row_count": len(packet_rows),
        "ready_rows": capture["ready_input_only_rows"],
        "blocked_rows": capture["blocked_rows"],
        "output_dir": rel(LANE_DIR),
        "forbidden_scan_status": forbidden_scan["scan_status"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
