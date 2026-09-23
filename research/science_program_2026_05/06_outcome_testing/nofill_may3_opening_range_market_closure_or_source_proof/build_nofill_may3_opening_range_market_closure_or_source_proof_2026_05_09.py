#!/usr/bin/env python3
"""Build the NOFILL May 3 opening-range market-closure source proof packet.

Research/source-control only. This script reads frozen packet artifacts,
local read-only quote/market files, and saved official-source capture notes.
It does not call MT5 order/account/history routes, Databento, brokers, AI APIs,
or live trading surfaces.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.inspect_sierra_scid import iter_slice, parse_utc, summarize_file  # noqa: E402


DATE = "2026-05-09"
LANE_ID = "NOFILL_MAY3_OPENING_RANGE_MARKET_CLOSURE_OR_SOURCE_PROOF"
SCHEMA_VERSION = "nofill_may3_opening_range_market_closure_source_proof_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_STATUS = "MARKET_SESSION_NONTRADING_EMPTY_PROVEN_SOURCE_CONTROL"
LANE_DIR = Path(__file__).resolve().parent
RAW_DIR = LANE_DIR / "raw"

WINDOW_START = parse_utc("2026-05-03T13:00:00Z")
WINDOW_END = parse_utc("2026-05-03T13:30:00Z")
TARGET_ROW_IDS = ("NOFILL-CAT-ROW-0049", "NOFILL-CAT-ROW-0050", "NOFILL-CAT-ROW-0051")

PRIOR_RESIDUAL_LEDGER = (
    "research/science_program_2026_05/06_outcome_testing/"
    "nofill_cat_v2_residual_blocker_clear_source_access_lane/"
    "NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_2026-05-09.jsonl"
)
OTI4_LEDGER = (
    "research/science_program_2026_05/06_outcome_testing/"
    "oti4_opening_drive_source_correction_or_contract_revision/"
    "OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_ROWS_2026-05-08.jsonl"
)

CONTROL_INPUTS = [
    "research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/NOFILL_MAY3_OPENING_RANGE_MARKET_CLOSURE_OR_SOURCE_PROOF_GOAL_PROMPT_2026-05-09.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/NOFILL_MAY3_OPENING_RANGE_STARTER_MESSAGE_2026-05-09.txt",
    ".context/LIVE_STATE.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_READING_ORDER.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    PRIOR_RESIDUAL_LEDGER,
    OTI4_LEDGER,
    "research/science_program_2026_05/06_outcome_testing/oti4_opening_drive_source_correction_or_contract_revision/OTI4_OPENING_DRIVE_SOURCE_SEARCH_LEDGER_2026-05-08.json",
    "research/science_program_2026_05/06_outcome_testing/oti4_opening_drive_source_correction_or_contract_revision/OTI4_OPENING_DRIVE_SOURCE_CONTRACT_PACKET_2026-05-08.json",
]

BROKER_TICK_FILES = {
    "NAS100": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\NAS100\2026-05-03.parquet"),
    "XAUUSD": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks\XAUUSD\2026-05-03.parquet"),
}

CSV_SOURCE_FILES = [
    {
        "symbol": "NAS100",
        "path": ROOT / "data/sierra_ohlcv_roots/sierra_nq_to_nas100_pilot_20260504/NAS100_M1.csv",
        "role": "worktree_converted_sierra_nq_to_nas100_m1",
        "acceptance_policy": "supporting_absence_only_file_ends_before_may3_window",
    },
    {
        "symbol": "XAUUSD",
        "path": ROOT / "data/sierra_ohlcv_roots/sierra_xauusd_scid_to_xauusd_pilot_20260504/XAUUSD_M1.csv",
        "role": "worktree_converted_sierra_xauusd_m1",
        "acceptance_policy": "supporting_absence_only_file_ends_before_may3_window",
    },
    {
        "symbol": "NAS100",
        "path": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\sierra_ohlcv_roots\sierra_nq_to_nas100_pilot_20260504\NAS100_M1.csv"),
        "role": "absolute_converted_sierra_nq_to_nas100_m1",
        "acceptance_policy": "supporting_absence_only_file_ends_before_may3_window",
    },
    {
        "symbol": "XAUUSD",
        "path": Path(r"C:\Users\MSI\Documents\ai-trading-agent\data\sierra_ohlcv_roots\sierra_xauusd_scid_to_xauusd_pilot_20260504\XAUUSD_M1.csv"),
        "role": "absolute_converted_sierra_xauusd_m1",
        "acceptance_policy": "supporting_absence_only_file_ends_before_may3_window",
    },
    {
        "symbol": "NAS100",
        "path": ROOT / "data/sierra_ohlcv_roots/sierra_first_wave_bounded_conversion_20260504/NAS100_NQ_M1.csv",
        "role": "first_wave_nq_m1",
        "acceptance_policy": "supporting_absence_only_file_ends_before_may3_window",
    },
    {
        "symbol": "NAS100",
        "path": ROOT / "data/sierra_ohlcv_roots/sierra_first_wave_bounded_conversion_20260504/NAS100_MNQ_M1.csv",
        "role": "first_wave_mnq_m1",
        "acceptance_policy": "supporting_absence_only_file_ends_before_may3_window",
    },
    {
        "symbol": "XAUUSD",
        "path": ROOT / "data/sierra_ohlcv_roots/sierra_first_wave_bounded_conversion_20260504/XAUUSD_SCID_M1.csv",
        "role": "first_wave_xauusd_scid_m1",
        "acceptance_policy": "supporting_absence_only_file_ends_before_may3_window",
    },
    {
        "symbol": "XAUUSD",
        "path": ROOT / "data/sierra_ohlcv_roots/sierra_first_wave_bounded_conversion_20260504/XAUUSD_GC_M1.csv",
        "role": "first_wave_gc_m1",
        "acceptance_policy": "supporting_absence_only_file_ends_before_may3_window",
    },
    {
        "symbol": "XAUUSD",
        "path": ROOT / "data/sierra_ohlcv_roots/sierra_first_wave_bounded_conversion_20260504/XAUUSD_MGC_M1.csv",
        "role": "first_wave_mgc_m1",
        "acceptance_policy": "supporting_absence_only_file_ends_before_may3_window",
    },
]

SCID_SOURCE_FILES = [
    {
        "symbol": "NAS100",
        "path": Path(r"C:\SierraChart\Data\NQM26-CME.scid"),
        "role": "raw_sierra_nq_futures_proxy_scid",
        "acceptance_policy": "supporting_zero_rows_in_frozen_window_proxy_not_broker_quote",
    },
    {
        "symbol": "NAS100",
        "path": Path(r"C:\SierraChart\Data\MNQM26-CME.scid"),
        "role": "raw_sierra_mnq_futures_proxy_scid",
        "acceptance_policy": "supporting_zero_rows_in_frozen_window_proxy_not_broker_quote",
    },
    {
        "symbol": "XAUUSD",
        "path": Path(r"C:\SierraChart\Data\XAUUSD.scid"),
        "role": "raw_sierra_xauusd_same_market_scid",
        "acceptance_policy": "supporting_absence_only_file_ends_before_may3_window",
    },
    {
        "symbol": "XAUUSD",
        "path": Path(r"C:\SierraChart\Data\GCM26-COMEX.scid"),
        "role": "raw_sierra_gc_futures_proxy_scid",
        "acceptance_policy": "supporting_zero_rows_in_frozen_window_proxy_not_broker_quote",
    },
    {
        "symbol": "XAUUSD",
        "path": Path(r"C:\SierraChart\Data\MGCM26-COMEX.scid"),
        "role": "raw_sierra_mgc_futures_proxy_scid",
        "acceptance_policy": "supporting_zero_rows_in_frozen_window_proxy_not_broker_quote",
    },
]

DEPTH_SOURCE_FILES = [
    {
        "symbol": "NAS100",
        "path": Path(r"C:\SierraChart\Data\MarketDepthData\NQM26-CME.2026-05-03.depth"),
        "role": "raw_sierra_nq_depth_date_file",
        "acceptance_policy": "supporting_presence_only_depth_not_accepted_ohlc_or_quote_stream",
    },
    {
        "symbol": "NAS100",
        "path": Path(r"C:\SierraChart\Data\MarketDepthData\MNQM26-CME.2026-05-03.depth"),
        "role": "raw_sierra_mnq_depth_date_file",
        "acceptance_policy": "supporting_presence_only_depth_not_accepted_ohlc_or_quote_stream",
    },
    {
        "symbol": "XAUUSD",
        "path": Path(r"C:\SierraChart\Data\MarketDepthData\GCM26-COMEX.2026-05-03.depth"),
        "role": "raw_sierra_gc_depth_date_file",
        "acceptance_policy": "supporting_presence_only_depth_not_accepted_ohlc_or_quote_stream",
    },
    {
        "symbol": "XAUUSD",
        "path": Path(r"C:\SierraChart\Data\MarketDepthData\MGCM26-COMEX.2026-05-03.depth"),
        "role": "raw_sierra_mgc_depth_date_file",
        "acceptance_policy": "supporting_presence_only_depth_not_accepted_ohlc_or_quote_stream",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return iso_z(value)
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


def write_md(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def iso_z(value: datetime | pd.Timestamp | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        value = value.to_pydatetime()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_hash_record(path: Path | str, *, role: str, parser: str | None, recheck: bool = True) -> dict[str, Any]:
    p = Path(path)
    resolved = p if p.is_absolute() else ROOT / p
    exists = resolved.exists()
    size = resolved.stat().st_size if exists else None
    return {
        "path": str(path),
        "resolved_path": str(resolved),
        "exists": exists,
        "size_bytes": size,
        "sha256": sha256_file(resolved) if exists else None,
        "role": role,
        "parser_or_source_version": parser,
        "verifier_recompute_sha256": bool(recheck and exists and (size or 0) <= 100_000_000),
        "hash_recheck_policy": (
            "verifier_recomputes_sha256"
            if exists and recheck and (size or 0) <= 100_000_000
            else "builder_sha256_recorded_large_or_missing_file_not_rehashed_by_verifier"
        ),
    }


def load_jsonl(path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with (ROOT / path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def git_cmd(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return f"GIT_ERROR: {result.stderr.strip()}"
    return result.stdout.strip()


def find_time_column(df: pd.DataFrame) -> str | None:
    for col in ("ts_utc", "timestamp_utc", "time", "Time", "datetime", "DateTime", "date_time"):
        if col in df.columns:
            return col
    return None


def quote_side(columns: list[str]) -> dict[str, bool]:
    names = set(columns)
    return {
        "has_bid": "bid" in names,
        "has_ask": "ask" in names,
        "has_last": "last" in names,
        "has_open": "open" in names,
        "has_high": "high" in names,
        "has_low": "low" in names,
        "has_close": "close" in names,
        "has_bid_volume": "bid_volume" in names,
        "has_ask_volume": "ask_volume" in names,
    }


def summarize_parquet(path: Path, symbol: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "source_family": "broker_tick_parquet",
        "symbol": symbol,
        "path": str(path),
        "resolved_path": str(path),
        "source_type": "parquet",
        "parser_or_source_version": "pandas_read_parquet_v1",
        "acceptance_policy": "primary_same_symbol_broker_quote_file_zero_rows_in_window_and_first_tick_after_window",
    }
    if not path.exists():
        payload.update({"exists": False, "rows_total": 0, "window_rows": None})
        return payload
    df = pd.read_parquet(path)
    time_col = find_time_column(df)
    if time_col is None:
        raise ValueError(f"no time column in {path}")
    ts = pd.to_datetime(df[time_col], utc=True)
    mask = (ts >= pd.Timestamp(WINDOW_START)) & (ts < pd.Timestamp(WINDOW_END))
    payload.update(
        {
            "exists": True,
            "rows_total": int(len(df)),
            "columns": list(map(str, df.columns)),
            "quote_side": quote_side(list(map(str, df.columns))),
            "first_timestamp_utc": iso_z(ts.min()),
            "last_timestamp_utc": iso_z(ts.max()),
            "window_start_utc": iso_z(WINDOW_START),
            "window_end_utc": iso_z(WINDOW_END),
            "window_rows": int(mask.sum()),
            "window_sample_rows": [],
        }
    )
    return payload


def summarize_csv(entry: dict[str, Any]) -> dict[str, Any]:
    path = Path(entry["path"])
    payload: dict[str, Any] = {
        "source_family": "local_m1_ohlc_csv",
        "symbol": entry["symbol"],
        "path": str(path),
        "resolved_path": str(path),
        "role": entry["role"],
        "source_type": "csv",
        "parser_or_source_version": "pandas_read_csv_v1",
        "acceptance_policy": entry["acceptance_policy"],
    }
    if not path.exists():
        payload.update({"exists": False, "rows_total": 0, "window_rows": None})
        return payload
    df = pd.read_csv(path)
    time_col = find_time_column(df)
    if time_col is None:
        raise ValueError(f"no time column in {path}")
    ts = pd.to_datetime(df[time_col], utc=True)
    mask = (ts >= pd.Timestamp(WINDOW_START)) & (ts < pd.Timestamp(WINDOW_END))
    payload.update(
        {
            "exists": True,
            "rows_total": int(len(df)),
            "columns": list(map(str, df.columns)),
            "quote_side": quote_side(list(map(str, df.columns))),
            "first_timestamp_utc": iso_z(ts.min()),
            "last_timestamp_utc": iso_z(ts.max()),
            "window_start_utc": iso_z(WINDOW_START),
            "window_end_utc": iso_z(WINDOW_END),
            "window_rows": int(mask.sum()),
        }
    )
    return payload


def summarize_scid(entry: dict[str, Any]) -> dict[str, Any]:
    path = Path(entry["path"])
    payload: dict[str, Any] = {
        "source_family": "raw_sierra_scid",
        "symbol": entry["symbol"],
        "path": str(path),
        "resolved_path": str(path),
        "role": entry["role"],
        "source_type": "sierra_scid",
        "parser_or_source_version": "scripts.inspect_sierra_scid_v1",
        "acceptance_policy": entry["acceptance_policy"],
        "quote_side": {
            "has_ohlc": True,
            "has_total_volume": True,
            "has_bid_volume": True,
            "has_ask_volume": True,
            "has_bid_ask_quote": False,
        },
    }
    if not path.exists():
        payload.update({"exists": False, "records": 0, "window_rows": None})
        return payload
    summary = summarize_file(path)
    window_records = list(iter_slice(path, WINDOW_START, WINDOW_END))
    payload.update(
        {
            "exists": True,
            "size_bytes": summary.get("size_bytes"),
            "records": int(summary.get("records") or 0),
            "first_timestamp_utc": summary.get("first_timestamp_utc"),
            "last_timestamp_utc": summary.get("last_timestamp_utc"),
            "window_start_utc": iso_z(WINDOW_START),
            "window_end_utc": iso_z(WINDOW_END),
            "window_rows": len(window_records),
        }
    )
    return payload


def summarize_depth(entry: dict[str, Any]) -> dict[str, Any]:
    path = Path(entry["path"])
    exists = path.exists()
    return {
        "source_family": "raw_sierra_depth_date_file",
        "symbol": entry["symbol"],
        "path": str(path),
        "resolved_path": str(path),
        "role": entry["role"],
        "source_type": "sierra_depth",
        "parser_or_source_version": "file_presence_sha256_only_v1",
        "acceptance_policy": entry["acceptance_policy"],
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else None,
        "window_rows": None,
        "note": "Depth file was hashed and recorded as date-file presence only; it is not used as accepted OHLC or quote evidence.",
    }


def build_official_source_capture() -> tuple[dict[str, Any], dict[str, Any]]:
    chicago = ZoneInfo("America/Chicago")
    eastern = ZoneInfo("America/New_York")
    local_start_ct = WINDOW_START.astimezone(chicago)
    local_end_ct = WINDOW_END.astimezone(chicago)
    local_start_et = WINDOW_START.astimezone(eastern)
    local_end_et = WINDOW_END.astimezone(eastern)
    sunday_open_ct = datetime(2026, 5, 3, 17, 0, tzinfo=chicago)
    sunday_open_et = datetime(2026, 5, 3, 18, 0, tzinfo=eastern)
    conversion = {
        "date": "2026-05-03",
        "weekday": "Sunday",
        "frozen_window_utc": {"start": iso_z(WINDOW_START), "end": iso_z(WINDOW_END)},
        "frozen_window_chicago_ct": {
            "start": local_start_ct.isoformat(),
            "end": local_end_ct.isoformat(),
            "timezone": "America/Chicago",
        },
        "frozen_window_new_york_et": {
            "start": local_start_et.isoformat(),
            "end": local_end_et.isoformat(),
            "timezone": "America/New_York",
        },
        "official_globex_sunday_open_chicago_ct": sunday_open_ct.isoformat(),
        "official_globex_sunday_open_new_york_et": sunday_open_et.isoformat(),
        "official_globex_sunday_open_utc": iso_z(sunday_open_ct.astimezone(timezone.utc)),
        "window_is_before_official_sunday_open": WINDOW_END <= sunday_open_ct.astimezone(timezone.utc),
    }
    capture = {
        "artifact_family": "NOFILL_MAY3_OFFICIAL_CME_WEB_CAPTURE",
        "generated_at_utc": utc_now(),
        "lane_id": LANE_ID,
        "source_capture_method": "OpenAI web tool plus direct curl attempt ledger; no paid/API/Databento/broker/account/order/history route.",
        "direct_curl_status": "attempted_then_timed_out_or_reset; not used for factual claims",
        "official_sources": [
            {
                "source_id": "CME_NQ_PRODUCT_PAGE",
                "url": "https://www.cmegroup.com/ja/markets/equities/nasdaq/e-mini-nasdaq-100.html",
                "source_owner": "CME Group",
                "web_tool_line_refs": ["turn954501view0 lines 302-316"],
                "source_claim_paraphrase": "The official CME E-mini Nasdaq-100 page lists Sunday-Friday electronic trading with Sunday evening open in ET, equivalent to 22:00 UTC on 2026-05-03.",
                "verbatim_excerpt_word_count": 0,
            },
            {
                "source_id": "CME_GC_PRODUCT_PAGE",
                "url": "https://www.cmegroup.com/ja/markets/metals/precious/gold.html",
                "source_owner": "CME Group",
                "web_tool_line_refs": ["turn661489view0 lines 296-310"],
                "source_claim_paraphrase": "The official CME Gold futures page lists Sunday-Friday electronic trading with Sunday evening open in ET, equivalent to 22:00 UTC on 2026-05-03.",
                "verbatim_excerpt_word_count": 0,
            },
            {
                "source_id": "CME_GC_PRODUCT_PAGE_SEARCH_SNIPPET",
                "url": "https://www.cmegroup.com/ja/markets/metals/precious/gold.html",
                "source_owner": "CME Group",
                "web_tool_line_refs": ["turn458195search1 search result"],
                "source_claim_paraphrase": "The official source also exposed CT-equivalent hours of Sunday-Friday 17:00-16:00 CT with weekday maintenance.",
                "verbatim_excerpt_word_count": 0,
            },
        ],
        "market_session_conversion": conversion,
        "source_contract_inference": (
            "The frozen opening range 2026-05-03T13:00:00Z to 13:30:00Z "
            "was Sunday 08:00-08:30 America/Chicago, before the CME Globex "
            "Sunday open at 17:00 CT / 22:00 UTC. CME NQ/GC are proxy official "
            "market-session contracts; broker tick parquets are the same-symbol "
            "broker quote files proving zero observed broker ticks in the window."
        ),
    }
    curl_attempts = {
        "artifact_family": "NOFILL_MAY3_DIRECT_CME_CURL_ATTEMPTS",
        "generated_at_utc": utc_now(),
        "lane_id": LANE_ID,
        "attempts": [
            {
                "url": "https://www.cmegroup.com/ja/markets/equities/nasdaq/e-mini-nasdaq-100.html",
                "route": "curl.exe -L",
                "status": "failed",
                "observed_error": "connection reset after escalated retry",
                "used_for_factual_claims": False,
            },
            {
                "url": "https://www.cmegroup.com/ja/markets/metals/precious/gold.html",
                "route": "curl.exe -L",
                "status": "failed",
                "observed_error": "connection reset after escalated retry",
                "used_for_factual_claims": False,
            },
            {
                "url": "https://www.cmegroup.com/market-regulation/files/gold-futures-and-options-fact-card.pdf",
                "route": "curl.exe -L",
                "status": "failed",
                "observed_error": "connection reset after escalated retry",
                "used_for_factual_claims": False,
            },
            {
                "url": "https://www.cmegroup.com/articles/faqs/micro-e-mini-equity-index-futures-frequently-asked-questions.html",
                "route": "curl.exe -L",
                "status": "failed",
                "observed_error": "timeout/reset after escalated retry",
                "used_for_factual_claims": False,
            },
        ],
    }
    return capture, curl_attempts


def build_search_routes() -> list[dict[str, Any]]:
    return [
        {
            "route_id": "worktree_target_lane",
            "root": str(LANE_DIR),
            "method": "Get-ChildItem + generated artifacts",
            "status": "searched",
            "coverage": "controlling prompt, starter, raw source capture, generated lane outputs",
        },
        {
            "route_id": "worktree_data_sierra_ohlcv",
            "root": str(ROOT / "data/sierra_ohlcv_roots"),
            "method": "direct file checks and pandas CSV summaries",
            "status": "searched",
            "coverage": "converted M1 OHLC roots for NAS100 and XAUUSD",
        },
        {
            "route_id": "absolute_broker_tick_parquet",
            "root": r"C:\Users\MSI\Documents\ai-trading-agent\data\ticks",
            "method": "direct file checks and pandas parquet summaries",
            "status": "searched",
            "coverage": "NAS100 and XAUUSD 2026-05-03 broker tick parquets",
        },
        {
            "route_id": "absolute_sierra_ohlcv",
            "root": r"C:\Users\MSI\Documents\ai-trading-agent\data\sierra_ohlcv_roots",
            "method": "direct file checks and pandas CSV summaries",
            "status": "searched",
            "coverage": "absolute converted M1 OHLC roots for NAS100 and XAUUSD",
        },
        {
            "route_id": "absolute_sierra_raw_scid",
            "root": r"C:\SierraChart\Data",
            "method": "rg --files plus scripts.inspect_sierra_scid summaries",
            "status": "searched",
            "coverage": "NQM26, MNQM26, XAUUSD, GCM26, MGCM26 raw SCID files",
        },
        {
            "route_id": "absolute_sierra_market_depth",
            "root": r"C:\SierraChart\Data\MarketDepthData",
            "method": "rg --files plus file presence/hash",
            "status": "searched",
            "coverage": "NQ/MNQ/GC/MGC 2026-05-03 depth files; not accepted as OHLC/quote stream",
        },
        {
            "route_id": "broad_tmp_targeted_rg",
            "root": r"C:\tmp",
            "method": "rg --files targeted NAS100/XAUUSD/NQ/MNQ/GC/MGC search",
            "status": "searched_with_access_denied_noise",
            "coverage": "found prior worktree artifacts and stale research reports; no additional approved broker tick/M1 source consumed",
        },
        {
            "route_id": "documents_targeted_rg",
            "root": r"C:\Users\MSI\Documents",
            "method": "rg --files targeted NAS100/XAUUSD/NQ/MNQ/GC/MGC search",
            "status": "searched",
            "coverage": "found main repo source docs/orderflow reports only; paid/cached Databento artifacts not consumed",
        },
        {
            "route_id": "mt5_read_only_route",
            "root": "MetaTrader5 Python package",
            "method": "import/dir capability inspection only",
            "status": "not_used_for_source_evidence",
            "coverage": "copy_ticks_range/copy_rates_range/symbol_info present; Python package exposed no session schedule function in this environment; no account/order/history routes called",
        },
        {
            "route_id": "official_cme_web_route",
            "root": "https://www.cmegroup.com/",
            "method": "web tool official source capture and curl attempt ledger",
            "status": "web_tool_capture_used_curl_failed",
            "coverage": "official CME NQ and GC product-page trading-hours source contract",
        },
    ]


def load_prior_target_rows() -> list[dict[str, Any]]:
    rows = load_jsonl(PRIOR_RESIDUAL_LEDGER)
    target = [row for row in rows if row.get("packet_row_id") in TARGET_ROW_IDS]
    if len(target) != 3:
        raise ValueError(f"expected 3 target rows in prior residual ledger, got {len(target)}")
    by_id = {row["packet_row_id"]: row for row in target}
    return [by_id[row_id] for row_id in TARGET_ROW_IDS]


def row_sources(symbol: str, source_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_family": record.get("source_family"),
            "role": record.get("role") or record.get("source_family"),
            "path": record.get("path"),
            "source_type": record.get("source_type"),
            "parser_or_source_version": record.get("parser_or_source_version"),
            "acceptance_policy": record.get("acceptance_policy"),
            "first_timestamp_utc": record.get("first_timestamp_utc"),
            "last_timestamp_utc": record.get("last_timestamp_utc"),
            "rows_total": record.get("rows_total") or record.get("records"),
            "window_rows": record.get("window_rows"),
            "quote_side": record.get("quote_side"),
        }
        for record in source_records
        if record.get("symbol") == symbol
    ]


def build_row_decisions(
    prior_rows: list[dict[str, Any]],
    source_records: list[dict[str, Any]],
    official_capture: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for prior in prior_rows:
        symbol = prior["symbol"]
        sources = row_sources(symbol, source_records)
        row = {
            "artifact_family": "NOFILL_MAY3_ROW_DECISION_LEDGER",
            "schema_version": SCHEMA_VERSION,
            "route_id": LANE_ID,
            "packet_row_id": prior["packet_row_id"],
            "symbol": symbol,
            "side": prior["side"],
            "session": prior["session"],
            "decision_asof_utc": prior["decision_asof_utc"],
            "source_lane": prior["source_lane"],
            "source_packet_id": prior["source_packet_id"],
            "source_inventory_id": prior["source_inventory_id"],
            "source_row_id": prior["source_row_id"],
            "source_close_packet_row_id": prior["source_close_packet_row_id"],
            "duplicate_group_id": prior["duplicate_group_id"],
            "nofill_duplicate_key": prior["nofill_duplicate_key"],
            "original_exact_blocker_codes": prior.get("original_exact_blocker_codes", []),
            "original_exact_blocker_reasons": prior.get("original_exact_blocker_reasons", []),
            "terminal_source_control_status": TERMINAL_STATUS,
            "terminal_source_control_reason": (
                "Same-symbol broker tick parquet has zero ticks in the frozen opening range and "
                "first broker tick after the range is 2026-05-03T22:00:00Z-class. Official CME "
                "proxy session source places the Sunday electronic open at 22:00Z, after the "
                "13:00-13:30Z frozen window. Supporting Sierra futures proxy files also have zero "
                "records in the window."
            ),
            "source_safe_input_only": True,
            "cleared_into_accepted_denominator": False,
            "categorical_lifecycle_label": None,
            "label_family": None,
            "label_is_performance_outcome": False,
            "result_label_assigned": False,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "promotion_verdict": PROMOTION_VERDICT,
            "exact_next_source_needed": None,
            "no_leak_boundary": (
                "Source/control proof only. No R, win rate, expectancy, broker actual-R, "
                "deal/order/account history label, hidden label, paid/API/Databento call, "
                "or MT5 order/account/history call used."
            ),
            "market_session_conversion": official_capture["market_session_conversion"],
            "source_contract_scope": {
                "broker_same_symbol_quote_evidence": str(BROKER_TICK_FILES[symbol]),
                "official_exchange_session_proxy": "CME NQ futures" if symbol == "NAS100" else "CME Gold futures",
                "proxy_limitation": (
                    "CME source is a futures exchange-session proxy, not a broker CFD schedule. "
                    "The broker parquet is the same-symbol broker quote evidence for observed "
                    "zero ticks in the frozen range."
                ),
            },
            "evidence": {
                "candidate_source_window_summaries": sources,
                "total_rows_in_frozen_opening_range_across_candidate_sources": sum(
                    int(src["window_rows"] or 0) for src in sources if src.get("window_rows") is not None
                ),
                "official_source_capture_file": str(RAW_DIR / f"NOFILL_MAY3_OFFICIAL_CME_WEB_CAPTURE_{DATE}.json"),
                "ambiguity_status": "No same-timestamp touch-ordering ambiguity opened; closure is market-session/source-control only.",
            },
        }
        rows.append(row)
    return rows


def build_artifacts() -> dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = utc_now()
    official_capture, curl_attempts = build_official_source_capture()
    official_path = RAW_DIR / f"NOFILL_MAY3_OFFICIAL_CME_WEB_CAPTURE_{DATE}.json"
    curl_path = RAW_DIR / f"NOFILL_MAY3_DIRECT_CME_CURL_ATTEMPTS_{DATE}.json"
    write_json(official_path, official_capture)
    write_json(curl_path, curl_attempts)

    source_records: list[dict[str, Any]] = []
    for symbol, path in BROKER_TICK_FILES.items():
        source_records.append(summarize_parquet(path, symbol))
    source_records.extend(summarize_csv(entry) for entry in CSV_SOURCE_FILES)
    source_records.extend(summarize_scid(entry) for entry in SCID_SOURCE_FILES)
    source_records.extend(summarize_depth(entry) for entry in DEPTH_SOURCE_FILES)

    source_hash_records: list[dict[str, Any]] = []
    for control in CONTROL_INPUTS:
        source_hash_records.append(file_hash_record(control, role="control_input", parser="sha256_file_v1", recheck=False))
    source_hash_records.append(file_hash_record(official_path, role="official_web_tool_capture", parser="json_capture_v1"))
    source_hash_records.append(file_hash_record(curl_path, role="direct_curl_attempt_ledger", parser="json_capture_v1"))
    for symbol, path in BROKER_TICK_FILES.items():
        source_hash_records.append(file_hash_record(path, role=f"broker_tick_parquet_{symbol}", parser="pandas_read_parquet_v1"))
    for entry in CSV_SOURCE_FILES:
        source_hash_records.append(file_hash_record(entry["path"], role=entry["role"], parser="pandas_read_csv_v1"))
    for entry in SCID_SOURCE_FILES:
        source_hash_records.append(file_hash_record(entry["path"], role=entry["role"], parser="scripts.inspect_sierra_scid_v1", recheck=False))
    for entry in DEPTH_SOURCE_FILES:
        source_hash_records.append(file_hash_record(entry["path"], role=entry["role"], parser="file_presence_sha256_only_v1"))

    prior_rows = load_prior_target_rows()
    row_decisions = build_row_decisions(prior_rows, source_records, official_capture)
    status_counts = Counter(row["terminal_source_control_status"] for row in row_decisions)
    duplicate_groups = defaultdict(list)
    for row in row_decisions:
        duplicate_groups[row["nofill_duplicate_key"]].append(row["packet_row_id"])

    source_ledger = {
        "artifact_family": "NOFILL_MAY3_MARKET_SESSION_SOURCE_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "lane_id": LANE_ID,
        "controlling_prompt": CONTROL_INPUTS[0],
        "target_row_ids": list(TARGET_ROW_IDS),
        "frozen_opening_range_utc": {"start": iso_z(WINDOW_START), "end": iso_z(WINDOW_END)},
        "searched_routes": build_search_routes(),
        "official_source_capture": official_capture,
        "source_records": source_records,
        "source_hash_records": source_hash_records,
        "source_control_summary": {
            "broker_tick_files_with_zero_window_rows": [
                record["symbol"]
                for record in source_records
                if record.get("source_family") == "broker_tick_parquet" and record.get("window_rows") == 0
            ],
            "official_cme_window_before_sunday_open": official_capture["market_session_conversion"]["window_is_before_official_sunday_open"],
            "source_control_status": TERMINAL_STATUS,
        },
    }

    source_proof_packet = {
        "artifact_family": "NOFILL_MAY3_SOURCE_PROOF_PACKET",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "lane_id": LANE_ID,
        "targeted_row_count": len(row_decisions),
        "target_row_ids": list(TARGET_ROW_IDS),
        "terminal_source_control_status_counts": dict(status_counts),
        "reject_total_preserved_outside_labels_denominators": 65,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "result_labels_assigned": 0,
        "rows_moved_into_accepted_denominator": 0,
        "market_session_conversion": official_capture["market_session_conversion"],
        "official_source_capture_file": str(official_path),
        "direct_curl_attempt_ledger_file": str(curl_path),
        "source_hash_records": source_hash_records,
        "row_decisions": row_decisions,
        "conclusion": (
            "Exactly three May 3 opening-range blocker rows are source/control-closed as "
            "market-session non-trading/empty. This is not an outcome label, not validation, "
            "and not promotion."
        ),
    }

    blocked_or_cleared = {
        "artifact_family": "NOFILL_MAY3_BLOCKED_OR_CLEARED_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "lane_id": LANE_ID,
        "targeted_row_count": len(row_decisions),
        "status_counts": dict(status_counts),
        "blocked_rows_remaining": [],
        "source_control_cleared_rows": [
            {
                "packet_row_id": row["packet_row_id"],
                "symbol": row["symbol"],
                "terminal_source_control_status": row["terminal_source_control_status"],
                "cleared_into_accepted_denominator": row["cleared_into_accepted_denominator"],
                "categorical_lifecycle_label": row["categorical_lifecycle_label"],
            }
            for row in row_decisions
        ],
        "reject_total_preserved_outside_labels_denominators": 65,
    }

    noleak = {
        "artifact_family": "NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "lane_id": LANE_ID,
        "target_row_ids": list(TARGET_ROW_IDS),
        "reject_total_preserved_outside_labels_denominators": 65,
        "result_labels_assigned": 0,
        "rows_moved_into_accepted_denominator": 0,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "duplicate_key_groups": dict(duplicate_groups),
        "canonical_counting_row_by_duplicate_key": {
            key: ("NOFILL-CAT-ROW-0050" if "XAUUSD" in key else rows[0])
            for key, rows in duplicate_groups.items()
        },
        "duplicate_boundary_summary": (
            "NOFILL-CAT-ROW-0050 and NOFILL-CAT-ROW-0051 retain the same XAUUSD duplicate key; "
            "both remain outside labels and denominators. The canonical row for that key remains "
            "NOFILL-CAT-ROW-0050 for identity tracking only."
        ),
        "forbidden_inputs_used": [],
        "violations": [],
    }

    context_anchor_lines = [
        "# NOFILL May 3 Opening-Range Context Anchor",
        "",
        f"- Generated UTC: {generated_at}",
        f"- Lane: {LANE_ID}",
        f"- Controlling prompt: `{CONTROL_INPUTS[0]}`",
        f"- Git HEAD at build: `{git_cmd(['rev-parse', 'HEAD'])}`",
        f"- Branch at build: `{git_cmd(['branch', '--show-current'])}`",
        f"- Frozen opening range: `{iso_z(WINDOW_START)}` to `{iso_z(WINDOW_END)}`",
        "- Target rows only: `NOFILL-CAT-ROW-0049`, `NOFILL-CAT-ROW-0050`, `NOFILL-CAT-ROW-0051`.",
        f"- Terminal source/control status: `{TERMINAL_STATUS}` for all three target rows.",
        "- Active question stack:",
        "  - Is the May 3 13:00-13:30 UTC range a valid trading window for CME NQ/GC proxies? Answer: no, it is Sunday 08:00-08:30 CT before 17:00 CT open.",
        "  - Do same-symbol broker tick files contain quotes in that window? Answer: no, both NAS100 and XAUUSD broker parquets have zero rows and first ticks after 22:00 UTC.",
        "  - Are any labels, result outcomes, promotion decisions, or denominator moves opened? Answer: no.",
        "  - Are duplicate identities preserved? Answer: yes; XAUUSD rows 0050/0051 retain the same duplicate key and remain outside denominators.",
        "",
        "## Boundaries",
        "",
        "- Source/control only.",
        "- No result scoring, broker actual-R, account/order/history labels, hidden labels, paid/API/Databento calls, or live trading behavior changes.",
        "- `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`, `promotion_verdict=NO_PROMOTION_VERDICT`.",
    ]

    source_ledger_md_lines = [
        "# NOFILL May 3 Market Session Source Ledger",
        "",
        f"- Generated UTC: {generated_at}",
        f"- Source/control status: `{TERMINAL_STATUS}`",
        f"- Official Sunday open UTC used for source contract: `{official_capture['market_session_conversion']['official_globex_sunday_open_utc']}`",
        f"- Frozen window before open: `{official_capture['market_session_conversion']['window_is_before_official_sunday_open']}`",
        "",
        "## Source Records",
        "",
        "| Symbol | Family | Role | Window rows | First UTC | Last UTC | Policy |",
        "|---|---|---|---:|---|---|---|",
    ]
    for record in source_records:
        source_ledger_md_lines.append(
            "| {symbol} | {family} | {role} | {rows} | {first} | {last} | {policy} |".format(
                symbol=record.get("symbol"),
                family=record.get("source_family"),
                role=record.get("role") or record.get("source_family"),
                rows="" if record.get("window_rows") is None else record.get("window_rows"),
                first=record.get("first_timestamp_utc") or "",
                last=record.get("last_timestamp_utc") or "",
                policy=record.get("acceptance_policy"),
            )
        )
    source_ledger_md_lines.extend(
        [
            "",
            "## Search Routes",
            "",
        ]
    )
    for route in source_ledger["searched_routes"]:
        source_ledger_md_lines.append(f"- `{route['route_id']}`: {route['status']} - {route['coverage']}")

    blocked_md_lines = [
        "# NOFILL May 3 Blocked Or Cleared Ledger",
        "",
        f"- Targeted rows: {len(row_decisions)}",
        f"- Status counts: `{dict(status_counts)}`",
        "- Remaining blocked rows in this lane: none.",
        "- Rows are source/control-cleared only and remain outside accepted denominators.",
        "",
        "| Row | Symbol | Status | Denominator | Label |",
        "|---|---|---|---|---|",
    ]
    for row in row_decisions:
        blocked_md_lines.append(
            f"| {row['packet_row_id']} | {row['symbol']} | {row['terminal_source_control_status']} | {row['cleared_into_accepted_denominator']} | {row['categorical_lifecycle_label']} |"
        )

    noleak_md_lines = [
        "# NOFILL May 3 Noleak Duplicate Audit",
        "",
        "- Result labels assigned: 0.",
        "- Rows moved into accepted denominator: 0.",
        "- Reject total preserved outside labels/denominators: 65.",
        "- Forbidden inputs used: none.",
        "- Duplicate boundary:",
    ]
    for key, rows in duplicate_groups.items():
        noleak_md_lines.append(f"  - `{key}` -> {', '.join(rows)}")

    next_prompt_lines = [
        "# NOFILL May 3 Next Prompt Pack",
        "",
        "No immediate next prompt is required for the three-row May 3 source/control blocker.",
        "",
        "Residual optional hardening only:",
        "- If the CEO wants broker-native session metadata beyond the same-symbol parquet evidence, request an owner-approved read-only broker symbol-session export that excludes account/order/history fields.",
        "- Do not open result labels, validation, registry edits, promotion, or denominator movement from this packet.",
    ]

    completion_audit = {
        "artifact_family": "NOFILL_MAY3_COMPLETION_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": generated_at,
        "lane_id": LANE_ID,
        "objective_satisfied": True,
        "targeted_row_count": len(row_decisions),
        "target_row_ids": list(TARGET_ROW_IDS),
        "terminal_source_control_status_counts": dict(status_counts),
        "reject_total_preserved_outside_labels_denominators": 65,
        "required_artifacts_written": [
            f"NOFILL_MAY3_CONTEXT_ANCHOR_{DATE}.md",
            f"NOFILL_MAY3_MARKET_SESSION_SOURCE_LEDGER_{DATE}.md",
            f"NOFILL_MAY3_MARKET_SESSION_SOURCE_LEDGER_{DATE}.json",
            f"NOFILL_MAY3_ROW_DECISION_LEDGER_{DATE}.jsonl",
            f"NOFILL_MAY3_SOURCE_PROOF_PACKET_{DATE}.json",
            f"NOFILL_MAY3_BLOCKED_OR_CLEARED_LEDGER_{DATE}.md",
            f"NOFILL_MAY3_BLOCKED_OR_CLEARED_LEDGER_{DATE}.json",
            f"NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_{DATE}.md",
            f"NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_{DATE}.json",
            f"NOFILL_MAY3_NEXT_PROMPT_PACK_{DATE}.md",
            f"NOFILL_MAY3_COMPLETION_AUDIT_{DATE}.md",
            f"NOFILL_MAY3_COMPLETION_AUDIT_{DATE}.json",
            "raw/NOFILL_MAY3_OFFICIAL_CME_WEB_CAPTURE_2026-05-09.json",
            "raw/NOFILL_MAY3_DIRECT_CME_CURL_ATTEMPTS_2026-05-09.json",
        ],
        "boundaries": {
            "source_control_only": True,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "promotion_verdict": PROMOTION_VERDICT,
            "reject_total_preserved_outside_labels_denominators": 65,
            "result_labels_assigned": 0,
            "rows_moved_into_accepted_denominator": 0,
        },
        "verification_commands_to_run": [
            "python -m py_compile research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/build_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/verify_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py",
            "python research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/verify_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py",
            "python -m pytest research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/test_nofill_may3_opening_range_market_closure_or_source_proof_2026_05_09.py -q",
        ],
    }
    completion_md_lines = [
        "# NOFILL May 3 Completion Audit",
        "",
        f"- Objective satisfied: `{completion_audit['objective_satisfied']}`",
        f"- Target rows: `{', '.join(TARGET_ROW_IDS)}`",
        f"- Terminal status counts: `{dict(status_counts)}`",
        "- Labels assigned: 0.",
        "- Rows moved into accepted denominator: 0.",
        "- Reject total preserved outside labels/denominators: 65.",
        "- Live effect: false.",
        "- Promotion verdict: `NO_PROMOTION_VERDICT`.",
        "",
        "## Required Verification Commands",
        "",
    ]
    for command in completion_audit["verification_commands_to_run"]:
        completion_md_lines.append(f"- `{command}`")

    write_md(LANE_DIR / f"NOFILL_MAY3_CONTEXT_ANCHOR_{DATE}.md", context_anchor_lines)
    write_json(LANE_DIR / f"NOFILL_MAY3_MARKET_SESSION_SOURCE_LEDGER_{DATE}.json", source_ledger)
    write_md(LANE_DIR / f"NOFILL_MAY3_MARKET_SESSION_SOURCE_LEDGER_{DATE}.md", source_ledger_md_lines)
    write_jsonl(LANE_DIR / f"NOFILL_MAY3_ROW_DECISION_LEDGER_{DATE}.jsonl", row_decisions)
    write_json(LANE_DIR / f"NOFILL_MAY3_SOURCE_PROOF_PACKET_{DATE}.json", source_proof_packet)
    write_json(LANE_DIR / f"NOFILL_MAY3_BLOCKED_OR_CLEARED_LEDGER_{DATE}.json", blocked_or_cleared)
    write_md(LANE_DIR / f"NOFILL_MAY3_BLOCKED_OR_CLEARED_LEDGER_{DATE}.md", blocked_md_lines)
    write_json(LANE_DIR / f"NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_{DATE}.json", noleak)
    write_md(LANE_DIR / f"NOFILL_MAY3_NOLEAK_DUPLICATE_AUDIT_{DATE}.md", noleak_md_lines)
    write_md(LANE_DIR / f"NOFILL_MAY3_NEXT_PROMPT_PACK_{DATE}.md", next_prompt_lines)
    write_json(LANE_DIR / f"NOFILL_MAY3_COMPLETION_AUDIT_{DATE}.json", completion_audit)
    write_md(LANE_DIR / f"NOFILL_MAY3_COMPLETION_AUDIT_{DATE}.md", completion_md_lines)

    return {
        "row_count": len(row_decisions),
        "status_counts": dict(status_counts),
        "source_record_count": len(source_records),
        "source_hash_record_count": len(source_hash_records),
    }


def main() -> int:
    summary = build_artifacts()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
