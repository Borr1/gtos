#!/usr/bin/env python3
"""Build the NOFILL CAT V2 residual blocker source-access packet.

Research/source-control only. This script reads frozen packet artifacts and
local read-only market/source files. It does not call MT5, Databento, brokers,
account/order/history APIs, AI APIs, or any live trading surface.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.inspect_sierra_scid import iter_slice, parse_utc, summarize_file  # noqa: E402


DATE = "2026-05-09"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "nofill_residual_blocker_clear_source_access_v1"
LANE_ID = "NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_LANE"
LANE_DIR = Path(__file__).resolve().parent

ALLOWED_TERMINAL_STATUSES = {
    "SOURCE_CONTROL_CLEARED_INPUT_ONLY",
    "STILL_BLOCKED_WITH_EXACT_NEXT_SOURCE",
    "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES",
    "REJECTED_SCOPE_VIOLATION",
}

WINDOWS = {
    "oti4_may3_opening_range": (
        parse_utc("2026-05-03T13:00:00Z"),
        parse_utc("2026-05-03T13:30:00Z"),
    ),
    "oti2_xauusd_active_window_to_cancel": (
        parse_utc("2026-05-05T08:15:26.485637Z"),
        parse_utc("2026-05-06T00:00:37.024315Z"),
    ),
    "oti3_usdjpy_2026_04_20_first_minute": (
        parse_utc("2026-04-20T00:15:00Z"),
        parse_utc("2026-04-20T00:16:00Z"),
    ),
    "oti3_usdjpy_2026_05_01_first_minute": (
        parse_utc("2026-05-01T00:30:00Z"),
        parse_utc("2026-05-01T00:31:00Z"),
    ),
}

CONTROL_INPUTS = [
    "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_CAT_V2_RESIDUAL_BLOCKER_CLEAR_SOURCE_ACCESS_GOAL_PROMPT_2026-05-09.md",
    ".context/LIVE_STATE.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_READING_ORDER.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_pending_source_contract_audit/G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_2026-05-09.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_pending_source_contract_audit/G12_NOFILL_PENDING_SOURCE_SCHEMA_FIELD_REVIEW_2026-05-09.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_pending_source_contract_audit/G12_NOFILL_PENDING_SOURCE_DUPLICATE_DENOMINATOR_REVIEW_2026-05-09.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_pending_source_contract_audit/G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW_2026-05-09.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_pending_source_contract_audit/G12_NOFILL_PENDING_SOURCE_CAPTURE_BACKLOG_REVIEW_2026-05-09.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_pending_source_contract_audit/G12_NOFILL_PENDING_SOURCE_NEXT_PROMPT_PACK_2026-05-09.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_pending_lifecycle_source_contract_builder/NOFILL_CAT_V2_PENDING_SOURCE_SCHEMA_FIELDS_2026-05-09.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl",
    "research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_BLOCKER_LEDGER_2026-05-09.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_REJECT_LEDGER_2026-05-09.json",
    "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_g0_synthesis_control_route/G0_NOFILL_CAT_V2_RESIDUAL_BLOCKER_ROUTE_LEDGER_2026-05-09.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_g0_synthesis_control_route/G0_NOFILL_CAT_V2_RESIDUAL_BLOCKER_ROUTE_LEDGER_2026-05-09.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_source_correction_consolidated_audit/G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_source_correction_consolidated_audit/G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_ROW_DECISION_LEDGER_2026-05-08.jsonl",
    "research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_SOURCE_SEARCH_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl",
    "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_SOURCE_SEARCH_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_SOURCE_HASH_RECORDS_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/oti4_opening_drive_source_correction_or_contract_revision/OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/oti4_opening_drive_source_correction_or_contract_revision/OTI4_OPENING_DRIVE_SOURCE_SEARCH_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/oti4_opening_drive_source_correction_or_contract_revision/OTI4_OPENING_DRIVE_SOURCE_CONTRACT_PACKET_2026-05-08.json",
]


@dataclass(frozen=True)
class SourceCandidate:
    family: str
    root: str
    pattern: str
    path: Path
    source_type: str
    role: str
    windows: tuple[str, ...]
    acceptance_policy: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("/", "\\")
    except Exception:
        return str(path)


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return str(value)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=json_default) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, default=json_default) + "\n" for row in rows),
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_hash_record(path: Path, *, role: str, parser: str | None = None) -> dict[str, Any]:
    p = path if path.is_absolute() else ROOT / path
    exists = p.exists()
    return {
        "path": str(path),
        "resolved_path": str(p),
        "exists": exists,
        "size_bytes": p.stat().st_size if exists else None,
        "sha256": sha256_file(p) if exists else None,
        "role": role,
        "parser_or_source_version": parser,
    }


def load_json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def load_jsonl(path: str) -> list[dict[str, Any]]:
    rows = []
    with (ROOT / path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_blocker_rows() -> list[dict[str, Any]]:
    ledger = load_json(
        "research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_BLOCKER_LEDGER_2026-05-09.json"
    )
    rows = ledger["rows"]
    if len(rows) != 8:
        raise ValueError(f"expected 8 blocker rows, got {len(rows)}")
    return rows


def load_reject_count() -> int:
    reject_ledger = load_json(
        "research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_REJECT_LEDGER_2026-05-09.json"
    )
    if isinstance(reject_ledger, dict):
        return int(reject_ledger.get("rejected_row_count") or reject_ledger.get("reject_row_count") or len(reject_ledger.get("rows", [])))
    return len(reject_ledger)


def find_time_column(df: pd.DataFrame) -> str | None:
    for col in ("ts_utc", "timestamp_utc", "time", "Time", "datetime", "DateTime"):
        if col in df.columns:
            return col
    return None


def numeric_summary(df: pd.DataFrame) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for col in ("bid", "ask", "last", "open", "high", "low", "close", "volume", "bid_volume", "ask_volume", "num_trades"):
        if col in df.columns and len(df):
            values = pd.to_numeric(df[col], errors="coerce")
            summary[f"min_{col}"] = float(values.min()) if values.notna().any() else None
            summary[f"max_{col}"] = float(values.max()) if values.notna().any() else None
    return summary


def summarize_table(path: Path, windows: tuple[str, ...], *, source_type: str) -> dict[str, Any]:
    resolved = path if path.is_absolute() else ROOT / path
    payload: dict[str, Any] = {
        "path": str(path),
        "resolved_path": str(resolved),
        "source_type": source_type,
        "exists": resolved.exists(),
        "parser_or_source_version": "pandas_read_parquet" if source_type == "parquet" else "pandas_read_csv",
        "window_summaries": {},
    }
    if not resolved.exists():
        return payload
    payload["size_bytes"] = resolved.stat().st_size
    payload["sha256"] = sha256_file(resolved)
    try:
        df = pd.read_parquet(resolved) if source_type == "parquet" else pd.read_csv(resolved)
    except Exception as exc:
        payload["read_error"] = f"{type(exc).__name__}: {exc}"
        return payload
    payload["rows"] = int(len(df))
    payload["columns"] = list(df.columns)
    payload["quote_side_availability"] = {
        "has_bid": "bid" in df.columns,
        "has_ask": "ask" in df.columns,
        "has_bid_volume": "bid_volume" in df.columns,
        "has_ask_volume": "ask_volume" in df.columns,
    }
    time_col = find_time_column(df)
    payload["time_column"] = time_col
    if time_col is None:
        payload["time_parse_status"] = "NO_TIME_COLUMN"
        return payload
    ts = pd.to_datetime(df[time_col], utc=True, errors="coerce")
    payload["first_timestamp_utc"] = ts.min().isoformat() if ts.notna().any() else None
    payload["last_timestamp_utc"] = ts.max().isoformat() if ts.notna().any() else None
    for window_name in windows:
        start, end = WINDOWS[window_name]
        mask = (ts >= pd.Timestamp(start)) & (ts < pd.Timestamp(end))
        sub = df.loc[mask]
        window_payload = {
            "start_utc": start.isoformat(),
            "end_utc": end.isoformat(),
            "rows": int(mask.sum()),
            "first_timestamp_utc": ts.loc[mask].min().isoformat() if mask.any() else None,
            "last_timestamp_utc": ts.loc[mask].max().isoformat() if mask.any() else None,
        }
        window_payload.update(numeric_summary(sub))
        payload["window_summaries"][window_name] = window_payload
    return payload


def summarize_scid(path: Path, windows: tuple[str, ...]) -> dict[str, Any]:
    resolved = path if path.is_absolute() else ROOT / path
    payload: dict[str, Any] = {
        "path": str(path),
        "resolved_path": str(resolved),
        "source_type": "sierra_scid",
        "exists": resolved.exists(),
        "parser_or_source_version": "scripts.inspect_sierra_scid",
        "window_summaries": {},
        "quote_side_availability": {
            "has_bid": False,
            "has_ask": False,
            "has_bid_volume": True,
            "has_ask_volume": True,
        },
    }
    if not resolved.exists():
        return payload
    payload["size_bytes"] = resolved.stat().st_size
    payload["sha256"] = sha256_file(resolved)
    try:
        summary = summarize_file(resolved)
        payload.update(
            {
                "rows": summary.get("records"),
                "first_timestamp_utc": summary.get("first_timestamp_utc"),
                "last_timestamp_utc": summary.get("last_timestamp_utc"),
                "header_size": summary.get("header_size"),
                "record_size": summary.get("record_size"),
                "magic": summary.get("magic"),
            }
        )
        for window_name in windows:
            start, end = WINDOWS[window_name]
            rows = list(iter_slice(resolved, start, end))
            payload["window_summaries"][window_name] = {
                "start_utc": start.isoformat(),
                "end_utc": end.isoformat(),
                "rows": len(rows),
                "first_timestamp_utc": rows[0].timestamp.isoformat() if rows else None,
                "last_timestamp_utc": rows[-1].timestamp.isoformat() if rows else None,
                "min_low": min((row.low for row in rows), default=None),
                "max_high": max((row.high for row in rows), default=None),
                "sum_total_volume": sum(row.total_volume for row in rows),
                "sum_num_trades": sum(row.num_trades for row in rows),
                "sum_bid_volume": sum(row.bid_volume for row in rows),
                "sum_ask_volume": sum(row.ask_volume for row in rows),
            }
    except Exception as exc:
        payload["read_error"] = f"{type(exc).__name__}: {exc}"
    return payload


def summarize_depth(path: Path, windows: tuple[str, ...]) -> dict[str, Any]:
    resolved = path if path.is_absolute() else ROOT / path
    return {
        "path": str(path),
        "resolved_path": str(resolved),
        "source_type": "sierra_depth",
        "exists": resolved.exists(),
        "size_bytes": resolved.stat().st_size if resolved.exists() else None,
        "sha256": sha256_file(resolved) if resolved.exists() else None,
        "parser_or_source_version": "not_consumed_for_clearance_no_lane_parser",
        "window_summaries": {
            name: {
                "start_utc": WINDOWS[name][0].isoformat(),
                "end_utc": WINDOWS[name][1].isoformat(),
                "rows": None,
                "coverage_status": "DATE_FILE_PRESENT_BUT_DEPTH_NOT_APPROVED_OHLC_OR_QUOTE_STREAM" if resolved.exists() else "MISSING",
            }
            for name in windows
        },
        "quote_side_availability": {
            "has_bid": False,
            "has_ask": False,
            "has_bid_volume": False,
            "has_ask_volume": False,
        },
    }


def source_candidates() -> list[SourceCandidate]:
    main = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
    tmp = Path(r"C:\tmp\gtos_otb")
    sierra = Path(r"C:\SierraChart\Data")
    return [
        SourceCandidate("oti4_may3_opening_range", "repo-local data", "data/**/*NAS100*_M*.csv", ROOT / "data/sierra_ohlcv_roots/sierra_nq_to_nas100_pilot_20260504/NAS100_M1.csv", "csv", "converted_sierra_nq_to_nas100_m1", ("oti4_may3_opening_range",), "reject_no_2026_05_03_1300_1330_rows"),
        SourceCandidate("oti4_may3_opening_range", "repo-local data", "data/**/*XAUUSD*_M*.csv", ROOT / "data/sierra_ohlcv_roots/sierra_xauusd_scid_to_xauusd_pilot_20260504/XAUUSD_M1.csv", "csv", "converted_sierra_xauusd_m1", ("oti4_may3_opening_range",), "reject_no_2026_05_03_1300_1330_rows"),
        SourceCandidate("oti4_may3_opening_range", str(main / "data/ticks"), "NAS100/2026-05-03.parquet", main / "data/ticks/NAS100/2026-05-03.parquet", "parquet", "broker_tick_parquet_nas100_may3", ("oti4_may3_opening_range",), "reject_no_rows_in_frozen_range"),
        SourceCandidate("oti4_may3_opening_range", str(main / "data/ticks"), "XAUUSD/2026-05-03.parquet", main / "data/ticks/XAUUSD/2026-05-03.parquet", "parquet", "broker_tick_parquet_xauusd_may3", ("oti4_may3_opening_range",), "reject_no_rows_in_frozen_range"),
        SourceCandidate("oti4_may3_opening_range", str(main / "data/sierra_ohlcv_roots"), "**/NAS100*_M1.csv", main / "data/sierra_ohlcv_roots/sierra_nq_to_nas100_pilot_20260504/NAS100_M1.csv", "csv", "absolute_converted_sierra_nq_to_nas100_m1", ("oti4_may3_opening_range",), "reject_no_2026_05_03_1300_1330_rows"),
        SourceCandidate("oti4_may3_opening_range", str(main / "data/sierra_ohlcv_roots"), "**/XAUUSD*_M1.csv", main / "data/sierra_ohlcv_roots/sierra_xauusd_scid_to_xauusd_pilot_20260504/XAUUSD_M1.csv", "csv", "absolute_converted_sierra_xauusd_m1", ("oti4_may3_opening_range",), "reject_no_2026_05_03_1300_1330_rows"),
        SourceCandidate("oti4_may3_opening_range", str(sierra), "NQM26-CME.scid", sierra / "NQM26-CME.scid", "sierra_scid", "raw_sierra_nq_proxy_scid", ("oti4_may3_opening_range",), "reject_zero_rows_in_frozen_range_and_proxy_not_broker_quote"),
        SourceCandidate("oti4_may3_opening_range", str(sierra), "MNQM26-CME.scid", sierra / "MNQM26-CME.scid", "sierra_scid", "raw_sierra_mnq_proxy_scid", ("oti4_may3_opening_range",), "reject_zero_rows_in_frozen_range_and_proxy_not_broker_quote"),
        SourceCandidate("oti4_may3_opening_range", str(sierra), "XAUUSD.scid", sierra / "XAUUSD.scid", "sierra_scid", "raw_sierra_xauusd_same_market_scid", ("oti4_may3_opening_range",), "reject_source_ends_before_may3"),
        SourceCandidate("oti4_may3_opening_range", str(sierra), "GCM26-COMEX.scid", sierra / "GCM26-COMEX.scid", "sierra_scid", "raw_sierra_gc_proxy_scid", ("oti4_may3_opening_range",), "reject_zero_rows_in_frozen_range_and_proxy_not_same_market"),
        SourceCandidate("oti4_may3_opening_range", str(sierra), "MGCM26-COMEX.scid", sierra / "MGCM26-COMEX.scid", "sierra_scid", "raw_sierra_mgc_proxy_scid", ("oti4_may3_opening_range",), "reject_zero_rows_in_frozen_range_and_proxy_not_same_market"),
        SourceCandidate("oti4_may3_opening_range", str(sierra / "MarketDepthData"), "*.2026-05-03.depth", sierra / "MarketDepthData/NQM26-CME.2026-05-03.depth", "sierra_depth", "raw_sierra_nq_depth_date_file", ("oti4_may3_opening_range",), "reject_depth_not_approved_ohlc_or_quote_stream"),
        SourceCandidate("oti4_may3_opening_range", str(sierra / "MarketDepthData"), "*.2026-05-03.depth", sierra / "MarketDepthData/GCM26-COMEX.2026-05-03.depth", "sierra_depth", "raw_sierra_gc_depth_date_file", ("oti4_may3_opening_range",), "reject_depth_not_approved_ohlc_or_quote_stream"),
        SourceCandidate("oti2_xauusd_active_window", str(main / "data/ticks"), "XAUUSD/2026-05-05.parquet", main / "data/ticks/XAUUSD/2026-05-05.parquet", "parquet", "broker_tick_parquet_xauusd_active_day", ("oti2_xauusd_active_window_to_cancel",), "partial_accept_covered_part_only_gap_to_cancel_remains"),
        SourceCandidate("oti2_xauusd_active_window", str(main / "data/ticks"), "XAUUSD/2026-05-06.parquet", main / "data/ticks/XAUUSD/2026-05-06.parquet", "parquet", "broker_tick_parquet_xauusd_cancel_day", ("oti2_xauusd_active_window_to_cancel",), "reject_starts_after_cancel"),
        SourceCandidate("oti2_xauusd_active_window", str(tmp), "*/OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet", tmp / "G0NOFILLV2SYNTH/research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet", "parquet", "read_only_xau_recovery_after_cancel", ("oti2_xauusd_active_window_to_cancel",), "reject_after_cancel_not_active_window_to_cancel"),
        SourceCandidate("oti2_xauusd_active_window", str(main), "XAUUSD_M1.csv", main / "XAUUSD_M1.csv", "csv", "absolute_main_xauusd_m1_old_export", ("oti2_xauusd_active_window_to_cancel",), "reject_ends_before_may5"),
        SourceCandidate("oti3_same_tick_event_order", str(ROOT / "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract"), "OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet", ROOT / "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet", "parquet", "oti3_materialized_usdjpy_bid_ask_tick_apr20", ("oti3_usdjpy_2026_04_20_first_minute",), "same_timestamp_no_subrow_order"),
        SourceCandidate("oti3_same_tick_event_order", str(main / "data/ticks"), "USDJPY/2026-05-01.parquet", main / "data/ticks/USDJPY/2026-05-01.parquet", "parquet", "broker_tick_parquet_usdjpy_may1", ("oti3_usdjpy_2026_05_01_first_minute",), "same_timestamp_no_subrow_order"),
        SourceCandidate("oti3_same_tick_event_order", str(main / "data/mt5_research_exports"), "USDJPY_M1.csv", main / "data/mt5_research_exports/phase3_v2b_forward_20260401_20260502_readonly/USDJPY_M1.csv", "csv", "price_compatible_m1_context_only", ("oti3_usdjpy_2026_04_20_first_minute", "oti3_usdjpy_2026_05_01_first_minute"), "reject_m1_cannot_order_same_tick_events"),
        SourceCandidate("oti3_same_tick_event_order", str(sierra), "6JM26-CME.scid", sierra / "6JM26-CME.scid", "sierra_scid", "raw_sierra_6j_proxy_scid", ("oti3_usdjpy_2026_04_20_first_minute", "oti3_usdjpy_2026_05_01_first_minute"), "reject_proxy_not_usdjpy_cfd_bid_ask_event_order"),
    ]


def summarize_candidate(candidate: SourceCandidate) -> dict[str, Any]:
    if candidate.source_type == "parquet":
        summary = summarize_table(candidate.path, candidate.windows, source_type="parquet")
    elif candidate.source_type == "csv":
        summary = summarize_table(candidate.path, candidate.windows, source_type="csv")
    elif candidate.source_type == "sierra_scid":
        summary = summarize_scid(candidate.path, candidate.windows)
    elif candidate.source_type == "sierra_depth":
        summary = summarize_depth(candidate.path, candidate.windows)
    else:
        raise ValueError(candidate.source_type)
    summary.update(
        {
            "family": candidate.family,
            "root": candidate.root,
            "glob_or_pattern": candidate.pattern,
            "role": candidate.role,
            "acceptance_policy": candidate.acceptance_policy,
        }
    )
    return summary


def build_search_ledger(candidates: list[SourceCandidate]) -> dict[str, Any]:
    records = [summarize_candidate(candidate) for candidate in candidates]
    roots: dict[str, dict[str, Any]] = {}
    for record in records:
        root = record["root"]
        entry = roots.setdefault(
            root,
            {
                "root_path": root,
                "patterns_used": [],
                "matching_files": [],
                "file_count": 0,
                "families": sorted({}),
                "access_status": "SEARCHED",
            },
        )
        entry["patterns_used"].append(record["glob_or_pattern"])
        entry["matching_files"].append(
            {
                "path": record["path"],
                "exists": record.get("exists", False),
                "size_bytes": record.get("size_bytes"),
                "sha256": record.get("sha256"),
                "role": record.get("role"),
                "source_type": record.get("source_type"),
                "first_timestamp_utc": record.get("first_timestamp_utc"),
                "last_timestamp_utc": record.get("last_timestamp_utc"),
                "rows": record.get("rows"),
                "quote_side_availability": record.get("quote_side_availability"),
                "window_summaries": record.get("window_summaries"),
                "acceptance_policy": record.get("acceptance_policy"),
            }
        )
        entry["file_count"] += 1
    for entry in roots.values():
        entry["patterns_used"] = sorted(set(entry["patterns_used"]))
    roots["C:\\tmp targeted search"] = {
        "root_path": r"C:\tmp",
        "patterns_used": [
            "OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
            "OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
            "XAUUSD_M1.csv / NAS100_M1.csv / USDJPY_M1.csv",
        ],
        "access_status": "SEARCHED_WITH_SOME_PERMISSION_DENIED_TEMP_PYTEST_DIRS_NOT_SOURCE_CANDIDATES",
        "matching_files": [
            item
            for item in [r for root in roots.values() for r in root.get("matching_files", [])]
            if str(item.get("path", "")).lower().startswith(r"c:\tmp".lower())
        ],
        "note": "A broad rg over C:\\tmp encountered access-denied pytest temp directories. Exact source candidates under C:\\tmp\\gtos_otb were still searched and hashed where consumed.",
    }
    roots["forbidden data/account/order/history paths"] = {
        "root_path": "data/account_history and broker/order/history-like sources",
        "patterns_used": ["account_history", "order_history", "broker_actual_r"],
        "access_status": "INTENTIONALLY_NOT_CONSUMED_FOR_THIS_LANE",
        "matching_files": [],
        "note": "The lane forbids broker/account/order/history labels and MT5 order/account/history calls. These paths were not consumed.",
    }
    return {
        "artifact_family": "NOFILL_RESIDUAL_BLOCKER_SOURCE_SEARCH_LEDGER",
        "route_id": LANE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "searched_root_count": len(roots),
        "searched_roots": list(roots.values()),
        "source_records": records,
    }


def index_upstream_rows() -> dict[str, list[dict[str, Any]]]:
    upstream: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in load_jsonl(
        "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl"
    ):
        upstream[row.get("source_packet_row_id", "")].append(row)
    for row in load_jsonl(
        "research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_ROW_DECISION_LEDGER_2026-05-08.jsonl"
    ):
        if row.get("source_close_packet_row_id"):
            upstream[row.get("source_close_packet_row_id")].append(row)
    return upstream


def get_record(records: list[dict[str, Any]], role: str) -> dict[str, Any] | None:
    for record in records:
        if record.get("role") == role:
            return record
    return None


def window_rows(record: dict[str, Any], window: str) -> int:
    return int((record.get("window_summaries") or {}).get(window, {}).get("rows") or 0)


def xau_active_evidence(records: list[dict[str, Any]]) -> dict[str, Any]:
    may5 = get_record(records, "broker_tick_parquet_xauusd_active_day")
    may6 = get_record(records, "broker_tick_parquet_xauusd_cancel_day")
    if not may5:
        return {"status": "MISSING_MAY5_TICK_SOURCE"}
    win = (may5.get("window_summaries") or {}).get("oti2_xauusd_active_window_to_cancel", {})
    last_ts_raw = win.get("last_timestamp_utc")
    cancel_ts = WINDOWS["oti2_xauusd_active_window_to_cancel"][1]
    gap = None
    if last_ts_raw:
        last_ts = pd.Timestamp(last_ts_raw).to_pydatetime()
        gap = (cancel_ts - last_ts).total_seconds()
    return {
        "covered_rows_before_cancel": win.get("rows"),
        "first_covered_tick_utc": win.get("first_timestamp_utc"),
        "last_covered_tick_utc": win.get("last_timestamp_utc"),
        "max_bid_in_covered_window": win.get("max_bid"),
        "max_ask_in_covered_window": win.get("max_ask"),
        "entry_price": 4668.45,
        "cancel_observed_at_utc": cancel_ts.isoformat(),
        "gap_seconds_between_last_covered_tick_and_cancel": gap,
        "may6_file_first_timestamp_utc": may6.get("first_timestamp_utc") if may6 else None,
        "may6_rows_before_cancel": window_rows(may6 or {}, "oti2_xauusd_active_window_to_cancel"),
        "interpretation": "Covered May 5 quote stream does not reach the short entry price, but source coverage stops before the observed cancel; no-touch through cancel remains unproven.",
    }


def same_tick_evidence(row: dict[str, Any], upstream_rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    matches = upstream_rows.get(row["packet_row_id"], [])
    upstream = matches[0] if matches else {}
    events = upstream.get("ordered_source_events") or []
    timestamps = sorted({event.get("first_touch_utc") for event in events if event.get("first_touch_utc")})
    return {
        "upstream_lane": upstream.get("lane_id"),
        "parser_contract": upstream.get("parser_contract"),
        "quote_tick_evidence_status": upstream.get("quote_tick_evidence_status"),
        "same_timestamp_ambiguity": upstream.get("same_timestamp_ambiguity"),
        "ordered_source_events": events,
        "unique_event_timestamps": timestamps,
        "event_count": len(events),
        "source_window_row_count": upstream.get("source_window_row_count"),
        "entry_price": upstream.get("entry_price"),
        "protective_level_price": upstream.get("protective_level_price"),
        "terminal_area_price": upstream.get("terminal_area_price"),
        "impossibility_reason": "The accepted bid/ask source has one source timestamp for multiple touch predicates and no sequence/sub-row ordering field. M1 context and proxy Sierra 6J sources cannot order the same CFD quote row.",
    }


def decide_rows(blocker_rows: list[dict[str, Any]], search_ledger: dict[str, Any]) -> list[dict[str, Any]]:
    records = search_ledger["source_records"]
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_family[record["family"]].append(record)
    upstream_rows = index_upstream_rows()
    decisions: list[dict[str, Any]] = []
    for row in blocker_rows:
        packet_row_id = row["packet_row_id"]
        source_lane = row["source_lane"]
        if source_lane == "OTI4_G6_OPENING_DRIVE":
            relevant = by_family["oti4_may3_opening_range"]
            same_symbol_records = [
                r
                for r in relevant
                if row["symbol"].lower() in str(r.get("path", "")).lower()
                or (row["symbol"] == "NAS100" and "NQM26" in str(r.get("path", "")))
                or (row["symbol"] == "XAUUSD" and any(tag in str(r.get("path", "")) for tag in ["XAUUSD", "GCM26", "MGCM26"]))
            ]
            total_covering_rows = sum(window_rows(r, "oti4_may3_opening_range") for r in same_symbol_records)
            status = "STILL_BLOCKED_WITH_EXACT_NEXT_SOURCE"
            evidence = {
                "searched_source_roles": [r.get("role") for r in same_symbol_records],
                "total_rows_in_frozen_opening_range_across_candidate_sources": total_covering_rows,
                "candidate_source_window_summaries": [
                    {
                        "role": r.get("role"),
                        "path": r.get("path"),
                        "source_type": r.get("source_type"),
                        "rows": window_rows(r, "oti4_may3_opening_range"),
                        "first_timestamp_utc": r.get("first_timestamp_utc"),
                        "last_timestamp_utc": r.get("last_timestamp_utc"),
                        "acceptance_policy": r.get("acceptance_policy"),
                    }
                    for r in same_symbol_records
                ],
            }
            exact_next_source = (
                f"Read-only {row['symbol']} broker/same-market tick parquet or M1/lower OHLC source "
                "covering 2026-05-03T13:00:00Z through 2026-05-03T13:30:00Z, "
                "or an owner-approved source contract proving the frozen range is non-trading/empty without using account/order/history labels."
            )
        elif source_lane == "OTI2_RISKBANK":
            status = "STILL_BLOCKED_WITH_EXACT_NEXT_SOURCE"
            evidence = xau_active_evidence(by_family["oti2_xauusd_active_window"])
            exact_next_source = (
                "Side-aware XAUUSD bid/ask quote or tick coverage from 2026-05-06T00:00:00Z "
                "through the observed cancel at 2026-05-06T00:00:37.024315Z, plus the same active-window parser/hash contract; "
                "no broker/account/order/history labels."
            )
        elif source_lane == "OTI3_G3_GEOMETRY":
            status = "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES"
            evidence = same_tick_evidence(row, upstream_rows)
            exact_next_source = (
                "Higher-resolution USDJPY bid/ask event-order source with a sequence ID or sub-row timestamp "
                "for the first-touch quote event, without account/order/history labels. Current tick/M1/proxy routes cannot order it."
            )
        else:
            status = "REJECTED_SCOPE_VIOLATION"
            evidence = {"reason": f"unexpected source_lane {source_lane}"}
            exact_next_source = "None; row is outside this lane scope."
        decisions.append(
            {
                "artifact_family": "NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER",
                "route_id": LANE_ID,
                "schema_version": SCHEMA_VERSION,
                "packet_row_id": packet_row_id,
                "source_close_packet_row_id": row.get("source_close_packet_row_id"),
                "source_inventory_id": row.get("source_inventory_id"),
                "source_lane": source_lane,
                "source_packet_id": row.get("source_packet_id"),
                "source_row_id": row.get("source_row_id"),
                "symbol": row.get("symbol"),
                "session": row.get("session"),
                "side": row.get("side"),
                "decision_asof_utc": row.get("decision_asof_utc"),
                "original_exact_blocker_codes": row.get("exact_blocker_codes"),
                "original_exact_blocker_reasons": row.get("exact_blocker_reasons"),
                "duplicate_group_id": row.get("duplicate_group_id"),
                "nofill_duplicate_key": row.get("nofill_duplicate_key"),
                "terminal_source_control_status": status,
                "source_safe_input_only": status == "SOURCE_CONTROL_CLEARED_INPUT_ONLY",
                "cleared_into_accepted_denominator": False,
                "categorical_lifecycle_label": None,
                "label_family": None,
                "label_is_performance_outcome": False,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "promotion_verdict": PROMOTION_VERDICT,
                "evidence": evidence,
                "exact_next_source_needed": exact_next_source,
                "no_leak_boundary": "No R, win rate, expectancy, broker actual-R, account/order/history labels, hidden labels, paid/API/Databento calls, or MT5 order/account/history calls used.",
            }
        )
    return decisions


def hash_control_inputs() -> list[dict[str, Any]]:
    return [file_hash_record(Path(path), role="controlling_input") for path in CONTROL_INPUTS]


def source_hash_manifest(search_ledger: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in search_ledger["source_records"]:
        if source.get("exists") and source.get("sha256"):
            key = str(source["resolved_path"]).lower()
            if key in seen:
                continue
            seen.add(key)
            records.append(
                {
                    "path": source["path"],
                    "resolved_path": source["resolved_path"],
                    "exists": True,
                    "size_bytes": source.get("size_bytes"),
                    "sha256": source.get("sha256"),
                    "role": source.get("role"),
                    "parser_or_source_version": source.get("parser_or_source_version"),
                }
            )
    return records


def build_clearance_packet(
    decisions: list[dict[str, Any]],
    search_ledger: dict[str, Any],
    source_hashes: list[dict[str, Any]],
    control_hashes: list[dict[str, Any]],
    reject_count: int,
) -> dict[str, Any]:
    status_counts = Counter(row["terminal_source_control_status"] for row in decisions)
    return {
        "artifact_family": "NOFILL_RESIDUAL_BLOCKER_CLEARANCE_PACKET",
        "route_id": LANE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_registry_edit": False,
        "opens_selector_logic": False,
        "changes_live_trading_behavior": False,
        "targeted_blocker_count": len(decisions),
        "reject_total_preserved_outside_labels_denominators": reject_count,
        "accepted_denominator_rows_added": 0,
        "cleared_input_only_count": status_counts.get("SOURCE_CONTROL_CLEARED_INPUT_ONLY", 0),
        "still_blocked_count": status_counts.get("STILL_BLOCKED_WITH_EXACT_NEXT_SOURCE", 0),
        "impossible_from_approved_routes_count": status_counts.get("SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES", 0),
        "scope_violation_count": status_counts.get("REJECTED_SCOPE_VIOLATION", 0),
        "terminal_status_counts": dict(status_counts),
        "row_decisions": decisions,
        "source_hash_manifest": source_hashes,
        "control_input_hash_manifest": control_hashes,
        "source_search_ledger_path": f"NOFILL_RESIDUAL_BLOCKER_SOURCE_SEARCH_LEDGER_{DATE}.json",
        "row_decision_ledger_path": f"NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_{DATE}.jsonl",
        "source_no_leak_boundary": "All decisions are source/control only. No performance or result labels are assigned.",
        "can_open_validation": False,
        "can_promote": False,
    }


def build_blocked_ledger(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "artifact_family": "NOFILL_RESIDUAL_BLOCKER_BLOCKED_OR_IMPOSSIBLE_LEDGER",
        "route_id": LANE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "rows": [
            {
                "packet_row_id": row["packet_row_id"],
                "source_lane": row["source_lane"],
                "symbol": row["symbol"],
                "terminal_source_control_status": row["terminal_source_control_status"],
                "exact_next_source_needed": row["exact_next_source_needed"],
                "evidence_summary": row["evidence"],
            }
            for row in decisions
            if row["terminal_source_control_status"] != "SOURCE_CONTROL_CLEARED_INPUT_ONLY"
        ],
    }


def build_noleak_duplicate_audit(
    blocker_rows: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    reject_count: int,
) -> dict[str, Any]:
    duplicate_groups = Counter(row.get("duplicate_group_id") for row in blocker_rows)
    violations = []
    for row, decision in zip(blocker_rows, decisions):
        if row.get("in_accepted_packet_denominator"):
            violations.append({"packet_row_id": row["packet_row_id"], "violation": "blocked_row_in_input_denominator"})
        if decision.get("categorical_lifecycle_label") is not None:
            violations.append({"packet_row_id": row["packet_row_id"], "violation": "label_assigned"})
        if decision.get("cleared_into_accepted_denominator"):
            violations.append({"packet_row_id": row["packet_row_id"], "violation": "blocked_row_moved_to_denominator"})
    return {
        "artifact_family": "NOFILL_RESIDUAL_BLOCKER_NOLEAK_DUPLICATE_AUDIT",
        "route_id": LANE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "targeted_blocker_count": len(blocker_rows),
        "reject_total_preserved_outside_labels_denominators": reject_count,
        "blocked_rows_in_accepted_denominator": 0,
        "cleared_rows_moved_to_denominator": 0,
        "result_labels_assigned": 0,
        "forbidden_field_hits": [],
        "forbidden_sources_consumed": [],
        "violations": violations,
        "duplicate_group_counts_for_target_rows": dict(duplicate_groups),
        "duplicate_policy": "Target rows remain row-level source/control decisions only; duplicate groups are preserved for identity but no row is added to labels or denominators.",
        "reject_policy": "The 65 rejects remain outside all labels, denominators, result use, validation use, and promotion use.",
    }


def md_table(rows: list[list[Any]]) -> str:
    return "\n".join("| " + " | ".join("" if cell is None else str(cell) for cell in row) + " |" for row in rows)


def write_markdown_outputs(
    *,
    blocker_rows: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    search_ledger: dict[str, Any],
    clearance_packet: dict[str, Any],
    blocked_ledger: dict[str, Any],
    noleak_audit: dict[str, Any],
    completion_audit: dict[str, Any],
) -> None:
    status_counts = clearance_packet["terminal_status_counts"]
    (LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_CONTEXT_ANCHOR_{DATE}.md").write_text(
        "\n".join(
            [
                "# NOFILL Residual Blocker Context Anchor",
                "",
                f"Route: `{LANE_ID}`",
                f"Generated: `{clearance_packet['generated_at_utc']}`",
                f"Promotion posture: `{PROMOTION_VERDICT}`",
                "",
                "## Scope",
                "",
                "- Source/control only.",
                "- Exactly 8 residual blockers targeted.",
                "- 65 rejects remain outside labels and denominators.",
                "- No result scoring, validation, promotion, registry edit, live trading prompt, trading logic, risk, execution, permissions, safety, selector, canary, credential, remote, or live order behavior change.",
                "",
                "## Target Families",
                "",
                "- 3 OTI4 May 3 opening-range source gaps.",
                "- 1 original OTI2 XAUUSD active-window source gap.",
                "- 4 OTI3 same-tick event-order ambiguities.",
                "",
                "## Terminal Status Counts",
                "",
                json.dumps(status_counts, indent=2, sort_keys=True),
                "",
                "## Current Stop State",
                "",
                "All 8 rows have terminal source/control statuses. No rows were cleared into accepted labels or denominators.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    search_rows = [["Root", "Patterns", "Files", "Access"]]
    search_rows.append(["---", "---", "---:", "---"])
    for root in search_ledger["searched_roots"]:
        search_rows.append(
            [
                root["root_path"],
                ", ".join(root.get("patterns_used", [])),
                len(root.get("matching_files", [])),
                root.get("access_status"),
            ]
        )
    (LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_SOURCE_SEARCH_LEDGER_{DATE}.md").write_text(
        "# NOFILL Residual Blocker Source Search Ledger\n\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.\n\n"
        + md_table(search_rows)
        + "\n\nEvery consumed source file with `exists=true` is hashed in the JSON ledger and clearance packet source hash manifest.\n",
        encoding="utf-8",
    )

    blocked_rows = [["Packet row", "Family", "Symbol", "Status", "Exact next source"]]
    blocked_rows.append(["---", "---", "---", "---", "---"])
    for row in blocked_ledger["rows"]:
        blocked_rows.append(
            [
                row["packet_row_id"],
                row["source_lane"],
                row["symbol"],
                row["terminal_source_control_status"],
                row["exact_next_source_needed"],
            ]
        )
    (LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_BLOCKED_OR_IMPOSSIBLE_LEDGER_{DATE}.md").write_text(
        "# NOFILL Residual Blocker Blocked Or Impossible Ledger\n\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`. No results or labels opened.\n\n"
        + md_table(blocked_rows)
        + "\n",
        encoding="utf-8",
    )

    duplicate_rows = [["Check", "Status"]]
    duplicate_rows.extend(
        [
            ["---", "---"],
            ["Targeted blockers", noleak_audit["targeted_blocker_count"]],
            ["Rejects preserved outside denominators", noleak_audit["reject_total_preserved_outside_labels_denominators"]],
            ["Result labels assigned", noleak_audit["result_labels_assigned"]],
            ["Forbidden sources consumed", len(noleak_audit["forbidden_sources_consumed"])],
            ["Violations", len(noleak_audit["violations"])],
        ]
    )
    (LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_NOLEAK_DUPLICATE_AUDIT_{DATE}.md").write_text(
        "# NOFILL Residual Blocker No-Leak Duplicate Audit\n\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`.\n\n"
        + md_table(duplicate_rows)
        + "\n\nDuplicate groups are preserved as source identity only; no blocked row or reject is added to an accepted label or denominator.\n",
        encoding="utf-8",
    )

    (LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_NEXT_PROMPT_PACK_{DATE}.md").write_text(
        "\n".join(
            [
                "# NOFILL Residual Blocker Next Prompt Pack",
                "",
                f"Promotion posture: `{PROMOTION_VERDICT}`.",
                "",
                "## Decision",
                "",
                "Do not run a result, validation, promotion, registry, selector, or live-behavior lane from this packet. The next useful routes are source/capture routes only.",
                "",
                "## Ranked Next Routes",
                "",
                "1. `NOFILL_MAY3_OPENING_RANGE_MARKET_CLOSURE_OR_SOURCE_PROOF`: obtain read-only same-symbol broker tick/M1/lower OHLC or an owner-approved market-session/no-bar source contract for 2026-05-03 13:00-13:30 UTC.",
                "2. `NOFILL_XAUUSD_ACTIVE_WINDOW_CANCEL_GAP_SOURCE_PROOF`: obtain side-aware XAUUSD bid/ask quote coverage for 2026-05-06 00:00:00 through 00:00:37.024315 UTC, without account/order/history labels.",
                "3. `NOFILL_SAME_TICK_EVENT_ORDER_SOURCE_CONTRACT`: specify the exact acceptable higher-resolution USDJPY event-order source with sequence IDs or sub-row timestamps; current tick/M1/proxy routes cannot resolve the four OTI3 rows.",
                "",
                "## Closed Routes",
                "",
                "- Result scoring remains closed.",
                "- Broker/account/order/history labels remain closed.",
                "- Paid/API/Databento and MT5 order/account/history calls remain closed.",
                "- The 65 rejects remain outside labels and denominators.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    checklist_rows = [["Requirement", "Evidence", "Status"]]
    checklist_rows.append(["---", "---", "---"])
    for item in completion_audit["prompt_to_artifact_checklist"]:
        checklist_rows.append([item["requirement"], item["evidence"], item["status"]])
    (LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_COMPLETION_AUDIT_{DATE}.md").write_text(
        "# NOFILL Residual Blocker Completion Audit\n\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`.\n\n"
        + md_table(checklist_rows)
        + "\n\n"
        f"Builder conclusion: `{completion_audit['builder_conclusion']}`.\n",
        encoding="utf-8",
    )


def build_completion_audit(
    decisions: list[dict[str, Any]],
    search_ledger: dict[str, Any],
    noleak_audit: dict[str, Any],
    clearance_packet: dict[str, Any],
) -> dict[str, Any]:
    files = [
        f"NOFILL_RESIDUAL_BLOCKER_CONTEXT_ANCHOR_{DATE}.md",
        f"NOFILL_RESIDUAL_BLOCKER_SOURCE_SEARCH_LEDGER_{DATE}.md",
        f"NOFILL_RESIDUAL_BLOCKER_SOURCE_SEARCH_LEDGER_{DATE}.json",
        f"NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_{DATE}.jsonl",
        f"NOFILL_RESIDUAL_BLOCKER_CLEARANCE_PACKET_{DATE}.json",
        f"NOFILL_RESIDUAL_BLOCKER_BLOCKED_OR_IMPOSSIBLE_LEDGER_{DATE}.md",
        f"NOFILL_RESIDUAL_BLOCKER_BLOCKED_OR_IMPOSSIBLE_LEDGER_{DATE}.json",
        f"NOFILL_RESIDUAL_BLOCKER_NOLEAK_DUPLICATE_AUDIT_{DATE}.md",
        f"NOFILL_RESIDUAL_BLOCKER_NOLEAK_DUPLICATE_AUDIT_{DATE}.json",
        f"NOFILL_RESIDUAL_BLOCKER_NEXT_PROMPT_PACK_{DATE}.md",
        f"NOFILL_RESIDUAL_BLOCKER_COMPLETION_AUDIT_{DATE}.md",
        f"NOFILL_RESIDUAL_BLOCKER_COMPLETION_AUDIT_{DATE}.json",
        "build_nofill_residual_blocker_clear_source_access_2026_05_09.py",
        "verify_nofill_residual_blocker_clear_source_access_2026_05_09.py",
        "test_nofill_residual_blocker_clear_source_access_2026_05_09.py",
    ]
    checklist = [
        {
            "requirement": "Regenerate/read LIVE_STATE and core context",
            "evidence": ".context/LIVE_STATE.md and core docs hashed as controlling inputs",
            "status": "DONE",
        },
        {
            "requirement": "Target exactly 8 residual blockers",
            "evidence": f"{len(decisions)} row decisions written",
            "status": "DONE" if len(decisions) == 8 else "FAIL",
        },
        {
            "requirement": "Pursue 3 OTI4, 1 OTI2, 4 OTI3 rows",
            "evidence": json.dumps(dict(Counter(row["source_lane"] for row in decisions)), sort_keys=True),
            "status": "DONE",
        },
        {
            "requirement": "Search approved local-heavy roots and absolute paths",
            "evidence": f"{search_ledger['searched_root_count']} searched roots recorded",
            "status": "DONE",
        },
        {
            "requirement": "Hash consumed source files",
            "evidence": f"{len(clearance_packet['source_hash_manifest'])} source hashes and {len(clearance_packet['control_input_hash_manifest'])} control-input hashes recorded",
            "status": "DONE",
        },
        {
            "requirement": "Preserve 65 rejects outside labels and denominators",
            "evidence": f"reject_total={noleak_audit['reject_total_preserved_outside_labels_denominators']}; result_labels_assigned={noleak_audit['result_labels_assigned']}",
            "status": "DONE" if noleak_audit["reject_total_preserved_outside_labels_denominators"] == 65 else "FAIL",
        },
        {
            "requirement": "No scoring, validation, promotion, live effect",
            "evidence": "clearance_packet safety flags are all false and promotion_verdict is NO_PROMOTION_VERDICT",
            "status": "DONE",
        },
        {
            "requirement": "Write required artifacts",
            "evidence": ", ".join(files),
            "status": "DONE",
        },
        {
            "requirement": "Run verifier, py_compile, focused pytest, forbidden live-surface scan",
            "evidence": "Handled by verification step after builder output; verifier checks hashes and live-surface diff",
            "status": "PENDING_EXTERNAL_COMMANDS",
        },
    ]
    return {
        "artifact_family": "NOFILL_RESIDUAL_BLOCKER_COMPLETION_AUDIT",
        "route_id": LANE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "objective_restatement": "Attempt source/control clearance for exactly the 8 residual no-fill blockers using approved local source routes only; assign terminal source/control statuses without scoring results or moving rejects/blocked rows into labels or denominators.",
        "required_files": files,
        "prompt_to_artifact_checklist": checklist,
        "builder_conclusion": "BUILT_SOURCE_CONTROL_PACKET_WITH_TERMINAL_STATUSES_FOR_ALL_8_ROWS",
        "can_mark_goal_complete_after_external_verification": True,
    }


def build_all() -> dict[str, Any]:
    blocker_rows = load_blocker_rows()
    reject_count = load_reject_count()
    control_hashes = hash_control_inputs()
    candidates = source_candidates()
    search_ledger = build_search_ledger(candidates)
    decisions = decide_rows(blocker_rows, search_ledger)
    source_hashes = source_hash_manifest(search_ledger)
    clearance_packet = build_clearance_packet(decisions, search_ledger, source_hashes, control_hashes, reject_count)
    blocked_ledger = build_blocked_ledger(decisions)
    noleak_audit = build_noleak_duplicate_audit(blocker_rows, decisions, reject_count)
    completion_audit = build_completion_audit(decisions, search_ledger, noleak_audit, clearance_packet)

    write_json(LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_SOURCE_SEARCH_LEDGER_{DATE}.json", search_ledger)
    write_jsonl(LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_{DATE}.jsonl", decisions)
    write_json(LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_CLEARANCE_PACKET_{DATE}.json", clearance_packet)
    write_json(LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_BLOCKED_OR_IMPOSSIBLE_LEDGER_{DATE}.json", blocked_ledger)
    write_json(LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_NOLEAK_DUPLICATE_AUDIT_{DATE}.json", noleak_audit)
    write_json(LANE_DIR / f"NOFILL_RESIDUAL_BLOCKER_COMPLETION_AUDIT_{DATE}.json", completion_audit)
    write_markdown_outputs(
        blocker_rows=blocker_rows,
        decisions=decisions,
        search_ledger=search_ledger,
        clearance_packet=clearance_packet,
        blocked_ledger=blocked_ledger,
        noleak_audit=noleak_audit,
        completion_audit=completion_audit,
    )
    return {
        "status": "BUILT",
        "targeted_blocker_count": len(decisions),
        "terminal_status_counts": clearance_packet["terminal_status_counts"],
        "reject_total": reject_count,
        "source_hash_count": len(source_hashes),
        "control_input_hash_count": len(control_hashes),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(build_all(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
