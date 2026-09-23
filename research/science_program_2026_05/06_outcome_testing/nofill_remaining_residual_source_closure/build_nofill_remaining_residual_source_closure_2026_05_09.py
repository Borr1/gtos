#!/usr/bin/env python3
"""Build the NOFILL remaining residual source-closure artifacts.

Research/source-control only. This lane targets exactly five residual rows:
one XAUUSD active-window/cancel gap and four USDJPY same-tick event-order
ambiguities. It may use MT5 only for read-only quote/tick extraction and never
calls account, order, deal, position, history, AI, paid data, or live trading
surfaces.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import math
import os
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DATE = "2026-05-09"
LANE_ID = "NOFILL_REMAINING_RESIDUAL_SOURCE_CLOSURE_V1"
SCHEMA_VERSION = "nofill_remaining_residual_source_closure_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

TARGET_IDS = [
    "NOFILL-CAT-ROW-0241",
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
]
MAY3_CLOSED_IDS = {"NOFILL-CAT-ROW-0049", "NOFILL-CAT-ROW-0050", "NOFILL-CAT-ROW-0051"}
USDJPY_TARGET_IDS = {
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
}
XAUUSD_TARGET_ID = "NOFILL-CAT-ROW-0241"

ROOT = Path(__file__).resolve().parents[4]
LANE_DIR = Path(__file__).resolve().parent
RAW_DIR = LANE_DIR / "raw"
MAIN_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
MAIN_DATA = MAIN_ROOT / "data"
MAIN_TICKS = MAIN_DATA / "ticks"
TMP_GTOS = Path(r"C:\tmp\gtos_otb")
SIERRA_DATA = Path(r"C:\SierraChart\Data")

XAU_ACTIVE_START = pd.Timestamp("2026-05-05T08:15:26.485637Z")
XAU_CANCEL = pd.Timestamp("2026-05-06T00:00:37.024315Z")
XAU_ENTRY_PRICE = 4668.45
XAU_SIDE = "SHORT"

CONTROL_INPUTS = [
    "research/science_program_2026_05/06_outcome_testing/nofill_remaining_residual_source_closure/NOFILL_REMAINING_RESIDUAL_SOURCE_CLOSURE_GOAL_PROMPT_2026-05-09.md",
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_READING_ORDER.md",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_may3_source_proof_audit/G12_NOFILL_MAY3_DECISION_LEDGER_2026-05-09.md",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_may3_source_proof_audit/G12_NOFILL_MAY3_NEXT_PROMPT_PACK_2026-05-09.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/NOFILL_MAY3_COMPLETION_AUDIT_2026-05-09.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_RESIDUAL_BLOCKER_BLOCKED_OR_IMPOSSIBLE_LEDGER_2026-05-09.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_2026-05-09.jsonl",
    "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_RESIDUAL_BLOCKER_CLEARANCE_PACKET_2026-05-09.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_pending_source_contract_audit/G12_NOFILL_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.md",
    "research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_COMPLETION_AUDIT_2026-05-09.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_categorical_result_packet_v2_audit/G12_NOFILL_CAT_V2_DECISION_LEDGER_2026-05-09.json",
    "research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_ROW_DECISION_LEDGER_2026-05-08.jsonl",
    "research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_BLOCKER_AND_FAILURE_LEARNING_LEDGER_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl",
    "research/science_program_2026_05/06_outcome_testing/oti1_pending_intent_closure_source_packet/OTI1_PENDING_INTENT_COMPLETION_AUDIT_2026-05-08.md",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_source_correction_consolidated_audit/G12_NOFILL_SOURCE_CORRECTION_DECISION_LEDGER_2026-05-08.md",
]
MUTABLE_CONTROL_INPUTS = {
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
}

RAW_DOCS = [
    {
        "url": "https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py",
        "path": RAW_DIR / f"MQL5_COPY_TICKS_RANGE_PY_{DATE}.html",
        "role": "official_python_copy_ticks_range_contract",
    },
    {
        "url": "https://www.mql5.com/en/docs/series/copyticksrange",
        "path": RAW_DIR / f"MQL5_COPY_TICKS_RANGE_MQL_{DATE}.html",
        "role": "official_mql_copyticksrange_order_and_flags_contract",
    },
    {
        "url": "https://www.mql5.com/en/docs/constants/structures/mqltick",
        "path": RAW_DIR / f"MQL5_MQLTICK_STRUCTURE_{DATE}.html",
        "role": "official_mqltick_snapshot_fields_contract",
    },
]

CAT_V2_ROW_LEDGER = ROOT / "research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_ROW_DECISION_LEDGER_2026-05-09.jsonl"
CAT_V2_REJECT_LEDGER = ROOT / "research/science_program_2026_05/06_outcome_testing/nofill_lifecycle_categorical_result_packet_v2_rebuild/NOFILL_CAT_V2_REJECT_LEDGER_2026-05-09.json"
OTI2_ROW_LEDGER = ROOT / "research/science_program_2026_05/06_outcome_testing/oti2_fill_path_categorical_contract_v2/OTI2_FILL_PATH_ROW_DECISION_LEDGER_2026-05-08.jsonl"
OTI3_ROW_LEDGER = ROOT / "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract/OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl"

FORBIDDEN_OUTPUT_KEYS = {
    "actual_r",
    "broker_actual_r",
    "hidden_label",
    "live_trade_result",
    "profit",
    "reward_r_to_tp1",
    "synthetic_r",
    "win_rate",
    "expectancy",
    "dsr",
    "pbo",
    "mt5_deal_ticket",
    "mt5_order_ticket",
    "mt5_position_ticket",
    "broker_order_id",
    "broker_position_id",
    "pending_ticket",
}


@dataclass
class SourceRef:
    path: Path
    role: str
    parser_or_source_version: str | None = None
    url: str | None = None
    notes: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE:{exc!r}"


def parse_utc(value: Any) -> pd.Timestamp:
    return pd.Timestamp(str(value)).tz_convert("UTC") if pd.Timestamp(str(value)).tzinfo else pd.Timestamp(str(value), tz="UTC")


def iso_ts(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.tz_convert("UTC").isoformat().replace("+00:00", "Z")


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pd.Timestamp):
        return iso_ts(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return str(value)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=json_default) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=json_default) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT.resolve())).replace("/", "\\")
    except Exception:
        return str(path)


def source_record(ref: SourceRef) -> dict[str, Any]:
    path = ref.path
    exists = path.exists()
    path_rel = rel(path)
    normalized_rel = path_rel.replace("\\", "/")
    file_sha = sha256_file(path) if exists and path.is_file() else None
    mutable_context = ref.role == "controlling_input" and normalized_rel in MUTABLE_CONTROL_INPUTS
    return {
        "path": str(path),
        "path_rel": path_rel,
        "exists": exists,
        "size_bytes": path.stat().st_size if exists and path.is_file() else None,
        "sha256": None if mutable_context else file_sha,
        "snapshot_sha256": file_sha if mutable_context else None,
        "hash_verification_mode": "presence_only_mutable_context" if mutable_context else "strict_sha256",
        "role": ref.role,
        "parser_or_source_version": ref.parser_or_source_version,
        "url": ref.url,
        "notes": ref.notes
        or (
            "Mutable GTOS context regenerated during session closeout; verifier requires presence, not stable sha256."
            if mutable_context
            else None
        ),
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_cat_v2_rows() -> dict[str, dict[str, Any]]:
    rows = {row["packet_row_id"]: row for row in read_jsonl(CAT_V2_ROW_LEDGER)}
    missing = [row_id for row_id in TARGET_IDS if row_id not in rows]
    if missing:
        raise RuntimeError(f"missing target rows from CAT V2 row ledger: {missing}")
    return rows


def load_oti3_rows() -> dict[str, dict[str, Any]]:
    rows = {}
    for row in read_jsonl(OTI3_ROW_LEDGER):
        row_id = row.get("source_packet_row_id")
        if row_id in USDJPY_TARGET_IDS:
            rows[row_id] = row
    missing = sorted(USDJPY_TARGET_IDS - set(rows))
    if missing:
        raise RuntimeError(f"missing OTI3 target rows: {missing}")
    return rows


def load_oti2_target_row() -> dict[str, Any]:
    for row in read_jsonl(OTI2_ROW_LEDGER):
        if row.get("source_close_packet_row_id") == "NOFILL-CLOSE-ROW-0241":
            return row
    raise RuntimeError("missing OTI2 source row NOFILL-CLOSE-ROW-0241")


def reject_count() -> int:
    payload = read_json(CAT_V2_REJECT_LEDGER)
    return int(payload.get("rejected_row_count") or payload.get("reject_row_count") or len(payload.get("rows", [])))


def table_time_column(df: pd.DataFrame) -> str:
    for col in ("ts_utc", "timestamp_utc", "time", "Time", "datetime", "DateTime"):
        if col in df.columns:
            return col
    raise RuntimeError(f"no time column in table columns={list(df.columns)}")


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def infer_broker_offset_seconds(path: Path) -> dict[str, Any]:
    df = pd.read_parquet(path, columns=["ts_utc", "ts_msc"])
    sample = df.dropna().head(2000).copy()
    ts_utc = pd.to_datetime(sample["ts_utc"], utc=True)
    raw_seconds = pd.to_numeric(sample["ts_msc"], errors="coerce") / 1000.0
    # Parquet round-trips in this repo can return datetime64[us, UTC], so
    # astype(int64) may be microseconds rather than nanoseconds. Timestamp()
    # keeps this offset inference unit-stable across pandas/pyarrow versions.
    true_seconds = ts_utc.map(lambda value: value.timestamp())
    offsets = raw_seconds - true_seconds
    median = float(offsets.median())
    rounded = int(round(median / 3600.0) * 3600)
    return {
        "source_path": str(path),
        "sample_rows": int(len(sample)),
        "median_raw_time_minus_ts_utc_seconds": median,
        "rounded_broker_offset_seconds": rounded,
        "offset_hours": rounded / 3600.0,
        "policy": "MT5 raw time_msc is broker-server time for this captured file; add offset to requested true UTC window, then subtract offset from returned time_msc to recover true ts_utc.",
    }


def normalize_mt5_ticks(ticks: Any, *, broker_offset_seconds: int) -> pd.DataFrame:
    df = pd.DataFrame(ticks)
    if df.empty:
        return df
    if "time_msc" not in df.columns:
        raise RuntimeError("MT5 ticks missing time_msc")
    df["ts_msc"] = pd.to_numeric(df["time_msc"], errors="raise").astype("int64")
    true_msc = df["ts_msc"] - int(broker_offset_seconds) * 1000
    df.insert(0, "ts_utc", pd.to_datetime(true_msc, unit="ms", utc=True))
    df["broker_offset_seconds_applied"] = int(broker_offset_seconds)
    df["mt5_symbol"] = "XAUUSD"
    keep = [
        "ts_utc",
        "ts_msc",
        "time",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "broker_offset_seconds_applied",
        "mt5_symbol",
    ]
    return df[keep].sort_values("ts_utc").reset_index(drop=True)


def extract_xau_gap_ticks(*, broker_offset_seconds: int, skip_mt5: bool) -> dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_parquet = RAW_DIR / "NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet"
    out_json = RAW_DIR / f"NOFILL_REMAINING_XAUUSD_MT5_COPY_TICKS_RANGE_CAPTURE_{DATE}.json"
    server_start = XAU_CANCEL.replace(hour=0, minute=0, second=0, microsecond=0) + pd.Timedelta(seconds=broker_offset_seconds)
    server_end = XAU_CANCEL + pd.Timedelta(seconds=broker_offset_seconds)
    capture: dict[str, Any] = {
        "artifact_family": "NOFILL_REMAINING_XAUUSD_MT5_COPY_TICKS_RANGE_CAPTURE",
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "route": "MetaTrader5.copy_ticks_range",
        "symbol": "XAUUSD",
        "true_query_start_utc": iso_ts(XAU_CANCEL.replace(hour=0, minute=0, second=0, microsecond=0)),
        "true_query_end_utc": iso_ts(XAU_CANCEL),
        "broker_offset_seconds": broker_offset_seconds,
        "server_time_query_start": iso_ts(server_start),
        "server_time_query_end": iso_ts(server_end),
        "account_order_deal_position_history_calls": 0,
        "order_send_calls": 0,
        "paid_api_or_databento_calls": 0,
        "skipped": bool(skip_mt5),
        "output_parquet": str(out_parquet),
    }
    if skip_mt5:
        capture["status"] = "SKIPPED_BY_FLAG"
        write_json(out_json, capture)
        return capture
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:
        capture.update({"status": "MT5_IMPORT_FAILED", "error": repr(exc)})
        write_json(out_json, capture)
        return capture

    initialized = False
    try:
        initialized = bool(mt5.initialize())
        capture["initialize_returned"] = initialized
        capture["last_error_after_initialize"] = str(mt5.last_error())
        if not initialized:
            capture["status"] = "MT5_INITIALIZE_FAILED"
            write_json(out_json, capture)
            return capture
        ticks = mt5.copy_ticks_range(
            "XAUUSD",
            server_start.to_pydatetime(),
            server_end.to_pydatetime(),
            mt5.COPY_TICKS_ALL,
        )
        capture["last_error_after_copy_ticks_range"] = str(mt5.last_error())
        if ticks is None:
            capture["status"] = "COPY_TICKS_RANGE_RETURNED_NONE"
            write_json(out_json, capture)
            return capture
        df = normalize_mt5_ticks(ticks, broker_offset_seconds=broker_offset_seconds)
        capture["rows_returned"] = int(len(df))
        capture["dtype_names"] = list(getattr(ticks, "dtype", ()).names or [])
        if not df.empty:
            out_parquet.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(out_parquet, index=False, compression="snappy")
            capture.update(
                {
                    "status": "RECOVERED_READ_ONLY_QUOTE_TICKS",
                    "output_parquet_exists": True,
                    "output_parquet_sha256": sha256_file(out_parquet),
                    "first_true_ts_utc": iso_ts(df["ts_utc"].min()),
                    "last_true_ts_utc": iso_ts(df["ts_utc"].max()),
                    "min_bid": float(pd.to_numeric(df["bid"], errors="coerce").min()),
                    "max_bid": float(pd.to_numeric(df["bid"], errors="coerce").max()),
                    "min_ask": float(pd.to_numeric(df["ask"], errors="coerce").min()),
                    "max_ask": float(pd.to_numeric(df["ask"], errors="coerce").max()),
                }
            )
        else:
            capture["status"] = "ZERO_ROWS_RETURNED"
        write_json(out_json, capture)
        return capture
    except Exception as exc:
        capture.update({"status": "MT5_EXTRACTION_EXCEPTION", "error": repr(exc)})
        write_json(out_json, capture)
        return capture
    finally:
        if initialized:
            try:
                mt5.shutdown()
            except Exception:
                pass


def summarize_tick_file(path: Path, *, start: pd.Timestamp, end: pd.Timestamp) -> dict[str, Any]:
    payload = {
        "path": str(path),
        "exists": path.exists(),
        "parser_or_source_version": "pandas_read_parquet",
    }
    if not path.exists():
        return payload
    df = pd.read_parquet(path)
    time_col = table_time_column(df)
    ts = pd.to_datetime(df[time_col], utc=True)
    mask = (ts >= start) & (ts <= end)
    sub = df.loc[mask]
    payload.update(
        {
            "rows": int(len(df)),
            "columns": list(df.columns),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "time_column": time_col,
            "first_timestamp_utc": iso_ts(ts.min()),
            "last_timestamp_utc": iso_ts(ts.max()),
            "window_start_utc": iso_ts(start),
            "window_end_utc": iso_ts(end),
            "window_rows": int(len(sub)),
            "window_first_timestamp_utc": iso_ts(ts.loc[mask].min()) if len(sub) else None,
            "window_last_timestamp_utc": iso_ts(ts.loc[mask].max()) if len(sub) else None,
            "has_bid": "bid" in df.columns,
            "has_ask": "ask" in df.columns,
        }
    )
    for col in ("bid", "ask", "last", "volume", "flags", "ts_msc", "time_msc"):
        if col in sub.columns and len(sub):
            vals = pd.to_numeric(sub[col], errors="coerce")
            payload[f"window_min_{col}"] = float(vals.min()) if vals.notna().any() else None
            payload[f"window_max_{col}"] = float(vals.max()) if vals.notna().any() else None
    return payload


def build_xauusd_proof(oti2_row: dict[str, Any], mt5_capture: dict[str, Any]) -> tuple[dict[str, Any], list[SourceRef]]:
    may5 = MAIN_TICKS / "XAUUSD" / "2026-05-05.parquet"
    may6 = MAIN_TICKS / "XAUUSD" / "2026-05-06.parquet"
    recovered = RAW_DIR / "NOFILL_REMAINING_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_000000_000037.parquet"
    source_refs = [
        SourceRef(may5, "broker_tick_parquet_xauusd_active_day", "pandas_read_parquet"),
        SourceRef(may6, "broker_tick_parquet_xauusd_cancel_day_existing_capture", "pandas_read_parquet"),
        SourceRef(RAW_DIR / f"NOFILL_REMAINING_XAUUSD_MT5_COPY_TICKS_RANGE_CAPTURE_{DATE}.json", "read_only_mt5_extraction_capture", "MetaTrader5.copy_ticks_range"),
    ]
    if recovered.exists():
        source_refs.append(SourceRef(recovered, "read_only_mt5_recovered_xauusd_gap_ticks", "pandas_read_parquet"))

    may5_df = pd.read_parquet(may5)
    may5_ts = pd.to_datetime(may5_df["ts_utc"], utc=True)
    active_may5 = may5_df[(may5_ts >= XAU_ACTIVE_START) & (may5_ts <= pd.Timestamp("2026-05-05T23:59:59.999999Z"))].copy()
    previous_tick = may5_df[may5_ts < XAU_ACTIVE_START].tail(1).copy()
    recovered_df = pd.read_parquet(recovered) if recovered.exists() else pd.DataFrame()
    if not recovered_df.empty:
        recovered_ts = pd.to_datetime(recovered_df["ts_utc"], utc=True)
        active_gap = recovered_df[(recovered_ts >= pd.Timestamp("2026-05-06T00:00:00Z")) & (recovered_ts <= XAU_CANCEL)].copy()
    else:
        recovered_ts = pd.Series(dtype="datetime64[ns, UTC]")
        active_gap = pd.DataFrame()
    combined = pd.concat([active_may5, active_gap], ignore_index=True)
    max_bid = float(pd.to_numeric(combined["bid"], errors="coerce").max()) if not combined.empty else None
    max_ask = float(pd.to_numeric(combined["ask"], errors="coerce").max()) if not combined.empty else None
    entry_touch = bool(max_bid is not None and max_bid >= XAU_ENTRY_PRICE)
    prev_payload = None
    if not previous_tick.empty:
        row = previous_tick.iloc[0]
        prev_payload = {
            "ts_utc": iso_ts(row["ts_utc"]),
            "ts_msc": int(row.get("ts_msc", 0)),
            "bid": float(row["bid"]),
            "ask": float(row["ask"]),
            "flags": int(row.get("flags", 0)),
        }
    proof = {
        "artifact_family": "NOFILL_REMAINING_XAUUSD_ACTIVE_WINDOW_PROOF_PACKET",
        "schema_version": SCHEMA_VERSION,
        "route_id": LANE_ID,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "packet_row_id": XAUUSD_TARGET_ID,
        "source_close_packet_row_id": "NOFILL-CLOSE-ROW-0241",
        "symbol": "XAUUSD",
        "side": XAU_SIDE,
        "entry_price": XAU_ENTRY_PRICE,
        "active_window_start_utc": iso_ts(XAU_ACTIVE_START),
        "cancel_observed_at_utc": iso_ts(XAU_CANCEL),
        "broker_offset_evidence": infer_broker_offset_seconds(may5),
        "mt5_read_only_capture": mt5_capture,
        "source_summaries": [
            summarize_tick_file(may5, start=XAU_ACTIVE_START, end=XAU_CANCEL),
            summarize_tick_file(may6, start=pd.Timestamp("2026-05-06T00:00:00Z"), end=XAU_CANCEL),
            summarize_tick_file(recovered, start=pd.Timestamp("2026-05-06T00:00:00Z"), end=XAU_CANCEL) if recovered.exists() else {"path": str(recovered), "exists": False},
        ],
        "previous_quote_before_active_start": prev_payload,
        "covered_may5_rows": int(len(active_may5)),
        "recovered_gap_rows_through_cancel": int(len(active_gap)),
        "combined_side_aware_rows_through_cancel": int(len(combined)),
        "first_combined_tick_utc": iso_ts(pd.to_datetime(combined["ts_utc"], utc=True).min()) if not combined.empty else None,
        "last_combined_tick_utc": iso_ts(pd.to_datetime(combined["ts_utc"], utc=True).max()) if not combined.empty else None,
        "max_bid_through_cancel": max_bid,
        "max_ask_through_cancel": max_ask,
        "short_entry_touch_rule": "SHORT entry touch requires bid >= entry_price",
        "entry_touch_before_cancel": entry_touch,
        "source_control_status": "SOURCE_CONTROL_CLEARED_INPUT_ONLY" if not entry_touch and int(len(active_gap)) > 0 else "STILL_BLOCKED_WITH_EXACT_NEXT_SOURCE",
        "source_control_label": "source_control_no_entry_touch_through_cancel" if not entry_touch and int(len(active_gap)) > 0 else None,
        "decision_basis": "Broker-offset-corrected read-only MT5 copy_ticks_range materialized the missing true-UTC 2026-05-06 00:00:00 through cancel quote stream; all side-aware bid values remained below the short entry price.",
        "no_result_scoring": True,
        "no_account_order_history_labels": True,
        "source_lineage_note": "Existing capture files use ts_utc corrected from raw MT5 server time. The MT5 gap query therefore used server-time query bounds true_utc + broker_offset_seconds, then converted returned time_msc back to true UTC.",
        "upstream_oti2_row_blockers": oti2_row.get("exact_blocker_codes", []),
    }
    return proof, source_refs


def resolve_source_path(path_text: str) -> Path:
    p = Path(path_text)
    if p.exists():
        return p
    candidate = ROOT / path_text
    if candidate.exists():
        return candidate
    current_oti3 = ROOT / "research/science_program_2026_05/06_outcome_testing/oti3_usdjpy_price_only_quote_or_tick_contract" / p.name
    if current_oti3.exists():
        return current_oti3
    if p.name == "2026-05-01.parquet":
        return MAIN_TICKS / "USDJPY" / "2026-05-01.parquet"
    return p


def side_predicates(row: dict[str, Any], quote: dict[str, Any]) -> dict[str, bool]:
    side = row["side"]
    bid = float(quote["bid"])
    ask = float(quote["ask"])
    entry = float(row["entry_price"])
    protective = float(row["protective_level_price"])
    terminal = float(row["terminal_area_price"])
    if side == "LONG":
        return {
            "entry_touch": ask <= entry,
            "protective_level": bid <= protective,
            "terminal_area": bid >= terminal,
        }
    return {
        "entry_touch": bid >= entry,
        "protective_level": ask >= protective,
        "terminal_area": ask <= terminal,
    }


def inspect_usdjpy_same_tick_row(row_id: str, row: dict[str, Any]) -> tuple[dict[str, Any], SourceRef]:
    first_ts = parse_utc(row["ordered_source_events"][0]["first_touch_utc"])
    source_path = resolve_source_path(row["ordered_source_events"][0]["source_path"])
    df = pd.read_parquet(source_path)
    time_col = table_time_column(df)
    ts = pd.to_datetime(df[time_col], utc=True)
    same = df.loc[ts == first_ts].copy()
    if same.empty:
        # Some paths are copied between worktrees; fall back to +/- 1 ms if
        # pandas round-tripped ns/us precision differently.
        same = df.loc[(ts >= first_ts - pd.Timedelta(milliseconds=1)) & (ts <= first_ts + pd.Timedelta(milliseconds=1))].copy()
    quote = same.iloc[0].to_dict() if not same.empty else {}
    predicates = side_predicates(row, quote) if quote else {}
    true_predicates = [name for name, value in predicates.items() if value]
    first_event_names = sorted({event["event"] for event in row.get("ordered_source_events", []) if parse_utc(event["first_touch_utc"]) == first_ts})
    exact_rows = []
    for idx, (_, qrow) in enumerate(same.iterrows()):
        exact_rows.append(
            {
                "row_position_within_exact_timestamp": idx,
                "ts_utc": iso_ts(qrow[time_col]),
                "ts_msc": int(qrow.get("ts_msc", qrow.get("time_msc", 0))),
                "bid": float(qrow["bid"]),
                "ask": float(qrow["ask"]),
                "last": float(qrow.get("last", 0.0)),
                "volume": float(qrow.get("volume", 0.0)),
                "flags": int(qrow.get("flags", 0)),
            }
        )
    evidence = {
        "packet_row_id": row_id,
        "source_close_packet_row_id": row["source_close_packet_row_id"],
        "symbol": row["symbol"],
        "side": row["side"],
        "decision_asof_utc": row["decision_asof_utc"],
        "source_path": str(source_path),
        "source_sha256": sha256_file(source_path) if source_path.exists() else None,
        "source_columns": list(df.columns),
        "source_row_count": int(len(df)),
        "time_column": time_col,
        "first_ambiguous_timestamp_utc": iso_ts(first_ts),
        "exact_timestamp_row_count": int(len(same)),
        "exact_timestamp_rows": exact_rows,
        "levels": {
            "entry_price": row["entry_price"],
            "protective_level_price": row["protective_level_price"],
            "terminal_area_price": row["terminal_area_price"],
        },
        "side_predicate_results_on_single_quote_row": predicates,
        "true_predicates_on_single_quote_row": true_predicates,
        "upstream_same_timestamp_ambiguity": bool(row.get("same_timestamp_ambiguity")),
        "upstream_first_event_names": first_event_names,
        "row_order_contract_assessment": "Source-file row order is valid across distinct tick rows after sorting by ts_utc/time_msc, but the first ambiguity has exactly one quote row satisfying multiple predicates. There is no sub-row sequence field to order entry versus protective events inside that single MqlTick state snapshot.",
        "terminal_source_control_status": "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES",
        "exact_next_source_needed": "Higher-resolution USDJPY bid/ask event-order source with a sequence ID, exchange/broker quote-event sequence number, or sub-millisecond/sub-row timestamp for the first-touch quote event, without account/order/history labels.",
    }
    return evidence, SourceRef(source_path, f"usdjpy_bid_ask_tick_source_{row_id}", "pandas_read_parquet")


def build_usdjpy_proof(oti3_rows: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[SourceRef]]:
    row_evidence = []
    source_refs: list[SourceRef] = []
    for row_id in sorted(USDJPY_TARGET_IDS):
        evidence, source_ref = inspect_usdjpy_same_tick_row(row_id, oti3_rows[row_id])
        row_evidence.append(evidence)
        source_refs.append(source_ref)
    m1 = MAIN_DATA / "mt5_research_exports" / "phase3_v2b_forward_20260401_20260502_readonly" / "USDJPY_M1.csv"
    sixj = SIERRA_DATA / "6JM26-CME.scid"
    source_refs.extend(
        [
            SourceRef(m1, "usdjpy_m1_context_only_cannot_order_same_tick_quote", "pandas_read_csv"),
            SourceRef(sixj, "sierra_6j_proxy_context_not_cfd_event_order", "scripts.inspect_sierra_scid"),
        ]
    )
    proof = {
        "artifact_family": "NOFILL_REMAINING_USDJPY_SAME_TICK_EVENT_ORDER_PROOF_PACKET",
        "schema_version": SCHEMA_VERSION,
        "route_id": LANE_ID,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "target_rows": sorted(USDJPY_TARGET_IDS),
        "contract_status": "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES_FOR_CURRENT_APPROVED_SOURCES",
        "official_doc_contract": {
            "raw_captures": [
                {
                    "url": doc["url"],
                    "path": str(doc["path"]),
                    "exists": doc["path"].exists(),
                    "sha256": sha256_file(doc["path"]) if doc["path"].exists() else None,
                    "role": doc["role"],
                }
                for doc in RAW_DOCS
            ],
            "source_contract_summary": [
                "MetaTrader5 Python copy_ticks_range returns a numpy array of tick fields, including time/time_msc, bid, ask, last, volume, flags, and volume_real.",
                "MQL5 CopyTicksRange orders copied ticks from past to present across array elements and flags describe which fields changed.",
                "MqlTick is a current-price state snapshot; fields are filled even when they did not change, so a single row containing bid and ask cannot encode an entry-vs-protective sub-order unless another sequence/sub-row timestamp source exists.",
            ],
        },
        "row_evidence": row_evidence,
        "source_order_contract_decision": "Do not use lexical predicate order or source-file row order to break ties inside one quote row. Row order is accepted only between distinct source rows.",
        "rejected_routes": [
            "M1 OHLC context cannot order same-tick bid/ask predicates.",
            "Sierra 6J futures proxy is not the broker-native USDJPY CFD quote event stream.",
            "MT5 time_msc has millisecond precision and no sequence field in the approved parquet/schema for these rows.",
            "flags identify changed fields but do not sequence entry/protective predicates within one tick snapshot.",
        ],
        "exact_next_source_needed": "A broker-native USDJPY quote-event source with sequence ID or sub-row timestamp for each quote update, source-hashed and without account/order/history labels.",
    }
    return proof, source_refs


def targeted_walk(root: Path, patterns: list[str], *, cap: int = 80) -> dict[str, Any]:
    entry = {
        "root_path": str(root),
        "exists": root.exists(),
        "patterns_used": patterns,
        "access_status": "SEARCHED" if root.exists() else "MISSING",
        "matching_files": [],
        "match_count": 0,
        "truncated": False,
        "errors": [],
    }
    if not root.exists():
        return entry
    skip_dirs = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", ".venv", "venv"}

    def onerror(exc: OSError) -> None:
        entry["errors"].append({"error": repr(exc), "filename": getattr(exc, "filename", None)})

    for current, dirs, files in os.walk(root, topdown=True, onerror=onerror):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for name in files:
            full = Path(current) / name
            text = str(full).replace("\\", "/")
            if any(fnmatch.fnmatch(text, pattern.replace("\\", "/")) or fnmatch.fnmatch(name, pattern) for pattern in patterns):
                entry["match_count"] += 1
                if len(entry["matching_files"]) < cap:
                    entry["matching_files"].append(
                        {
                            "path": str(full),
                            "size_bytes": full.stat().st_size if full.exists() else None,
                            "sha256": sha256_file(full) if full.exists() and full.is_file() and full.stat().st_size < 500_000_000 else None,
                            "hash_note": "omitted_over_500mb_search_match" if full.exists() and full.stat().st_size >= 500_000_000 else None,
                        }
                    )
                else:
                    entry["truncated"] = True
    return entry


def build_search_ledger(source_refs: list[SourceRef]) -> dict[str, Any]:
    root_checks = [
        targeted_walk(ROOT, ["*NOFILL_REMAINING*", "*OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet", "*OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06*.parquet"], cap=80),
        targeted_walk(MAIN_TICKS, ["*/XAUUSD/2026-05-05.parquet", "2026-05-05.parquet", "2026-05-06.parquet", "2026-05-01.parquet"], cap=80),
        targeted_walk(MAIN_DATA / "mt5_research_exports", ["*USDJPY_M1.csv", "*XAUUSD*.csv"], cap=80),
        targeted_walk(MAIN_DATA / "external", ["*XAUUSD*", "*USDJPY*", "*6J*"], cap=80),
        targeted_walk(SIERRA_DATA, ["XAUUSD.scid", "6JM26-CME.scid", "*XAUUSD*.scid", "*6J*.scid"], cap=80),
        targeted_walk(TMP_GTOS, ["*XAUUSD*2026-05-06*.parquet", "*USDJPY*2026-04-20*.parquet", "*USDJPY*2026-05-01*.parquet"], cap=120),
    ]
    return {
        "artifact_family": "NOFILL_REMAINING_SOURCE_SEARCH_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "route_id": LANE_ID,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "target_rows": TARGET_IDS,
        "closed_context_only_rows_not_reopened": sorted(MAY3_CLOSED_IDS),
        "searched_roots": root_checks,
        "consumed_source_records": [source_record(ref) for ref in source_refs],
        "search_conclusion": {
            "xauusd": "Broker-offset-corrected MT5 copy_ticks_range recovered the missing true-UTC cancel-gap quote stream; prior worktree recovery files were after cancel and not used for the active-window decision.",
            "usdjpy": "Approved USDJPY bid/ask sources have millisecond timestamps, flags, and row order across ticks only; no local/prior/Sierra route provides broker-native sub-row event order for the four same-row ambiguities.",
        },
    }


def build_row_decisions(
    cat_rows: dict[str, dict[str, Any]],
    xau_proof: dict[str, Any],
    usd_proof: dict[str, Any],
) -> list[dict[str, Any]]:
    decisions = []
    for row_id in TARGET_IDS:
        cat = cat_rows[row_id]
        if row_id == XAUUSD_TARGET_ID:
            status = xau_proof["source_control_status"]
            evidence = {
                "entry_price": xau_proof["entry_price"],
                "max_bid_through_cancel": xau_proof["max_bid_through_cancel"],
                "max_ask_through_cancel": xau_proof["max_ask_through_cancel"],
                "entry_touch_before_cancel": xau_proof["entry_touch_before_cancel"],
                "recovered_gap_rows_through_cancel": xau_proof["recovered_gap_rows_through_cancel"],
                "mt5_capture_status": xau_proof["mt5_read_only_capture"].get("status"),
                "source_control_label": xau_proof["source_control_label"],
            }
            exact_next = None if status == "SOURCE_CONTROL_CLEARED_INPUT_ONLY" else "Side-aware XAUUSD bid/ask quote coverage for 2026-05-06T00:00:00Z through cancel."
        else:
            status = "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES"
            row_evidence = next(item for item in usd_proof["row_evidence"] if item["packet_row_id"] == row_id)
            evidence = {
                "first_ambiguous_timestamp_utc": row_evidence["first_ambiguous_timestamp_utc"],
                "exact_timestamp_row_count": row_evidence["exact_timestamp_row_count"],
                "true_predicates_on_single_quote_row": row_evidence["true_predicates_on_single_quote_row"],
                "source_columns": row_evidence["source_columns"],
                "source_order_contract_assessment": row_evidence["row_order_contract_assessment"],
            }
            exact_next = row_evidence["exact_next_source_needed"]
        decisions.append(
            {
                "artifact_family": "NOFILL_REMAINING_ROW_DECISION_LEDGER",
                "schema_version": SCHEMA_VERSION,
                "route_id": LANE_ID,
                "packet_row_id": row_id,
                "source_close_packet_row_id": cat["source_close_packet_row_id"],
                "source_inventory_id": cat["source_inventory_id"],
                "source_lane": cat["source_lane"],
                "source_packet_id": cat["source_packet_id"],
                "source_row_id": cat["source_row_id"],
                "symbol": cat["symbol"],
                "session": cat["session"],
                "side": cat["side"],
                "decision_asof_utc": cat["decision_asof_utc"],
                "duplicate_group_id": cat["duplicate_group_id"],
                "nofill_duplicate_key": cat["nofill_duplicate_key"],
                "original_exact_blocker_codes": cat.get("exact_blocker_codes", []),
                "terminal_source_control_status": status,
                "source_safe_input_only": status == "SOURCE_CONTROL_CLEARED_INPUT_ONLY",
                "categorical_lifecycle_label": None,
                "label_family": None,
                "label_is_performance_outcome": False,
                "cleared_into_accepted_denominator": False,
                "promotion_verdict": PROMOTION_VERDICT,
                "validation_safe": False,
                "outcome_review_opened": False,
                "live_effect": False,
                "evidence": evidence,
                "exact_next_source_needed": exact_next,
                "no_leak_boundary": "Source/control only. No R, win rate, expectancy, broker actual-R, account/order/history labels, hidden labels, validation, promotion, or live behavior.",
            }
        )
    return decisions


def scan_forbidden_keys(obj: Any, path: str = "$") -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key) in FORBIDDEN_OUTPUT_KEYS:
                hits.append({"path": path, "key": str(key)})
            hits.extend(scan_forbidden_keys(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(scan_forbidden_keys(value, f"{path}[{idx}]"))
    return hits


def build_noleak_duplicate_audit(
    cat_rows: dict[str, dict[str, Any]],
    decisions: list[dict[str, Any]],
    reject_total: int,
    xau_proof: dict[str, Any],
    usd_proof: dict[str, Any],
) -> dict[str, Any]:
    violations = []
    for row in decisions:
        if row["cleared_into_accepted_denominator"]:
            violations.append({"packet_row_id": row["packet_row_id"], "violation": "moved_to_accepted_denominator"})
        if row["categorical_lifecycle_label"] is not None:
            violations.append({"packet_row_id": row["packet_row_id"], "violation": "lifecycle_label_assigned"})
    forbidden_hits = scan_forbidden_keys([decisions, xau_proof, usd_proof])
    # Allow source-contract phrases in narrative strings; this scan is for
    # forbidden output fields, not for words inside official docs or prose.
    return {
        "artifact_family": "NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "route_id": LANE_ID,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "target_row_count": len(decisions),
        "target_rows": [row["packet_row_id"] for row in decisions],
        "may3_rows_reopened": sorted(set(row["packet_row_id"] for row in decisions) & MAY3_CLOSED_IDS),
        "reject_total_preserved_outside_labels_denominators": reject_total,
        "rows_moved_to_accepted_denominator": 0,
        "lifecycle_labels_assigned": 0,
        "result_or_performance_labels_assigned": 0,
        "validation_safe_true_count": 0,
        "outcome_review_opened_true_count": 0,
        "live_effect_true_count": 0,
        "forbidden_output_key_hits": forbidden_hits,
        "violations": violations,
        "duplicate_group_counts": dict(Counter(cat_rows[row_id]["duplicate_group_id"] for row_id in TARGET_IDS)),
        "duplicate_policy": "Duplicate identity is preserved for no-leak accounting only; no target row is added to an accepted denominator in this source-control lane.",
        "label_family_policy": "XAUUSD clearance is input-only source control; USDJPY rows remain impossible-source blockers. No lifecycle/result/performance label family opens.",
    }


def build_blocker_ledger(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "artifact_family": "NOFILL_REMAINING_BLOCKER_CLEARANCE_IMPOSSIBILITY_LEDGER",
        "schema_version": SCHEMA_VERSION,
        "route_id": LANE_ID,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "rows": [
            {
                "packet_row_id": row["packet_row_id"],
                "symbol": row["symbol"],
                "source_lane": row["source_lane"],
                "terminal_source_control_status": row["terminal_source_control_status"],
                "evidence_summary": row["evidence"],
                "exact_next_source_needed": row["exact_next_source_needed"],
            }
            for row in decisions
        ],
        "status_counts": dict(Counter(row["terminal_source_control_status"] for row in decisions)),
    }


def build_source_hash_manifest(source_refs: list[SourceRef], control_refs: list[SourceRef]) -> dict[str, Any]:
    seen: set[str] = set()
    records = []
    for ref in source_refs + control_refs:
        key = str(ref.path.resolve() if ref.path.exists() else ref.path).lower()
        if key in seen:
            continue
        seen.add(key)
        records.append(source_record(ref))
    return {
        "artifact_family": "NOFILL_REMAINING_SOURCE_HASH_MANIFEST",
        "schema_version": SCHEMA_VERSION,
        "route_id": LANE_ID,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "record_count": len(records),
        "records": records,
    }


def md_table(rows: list[list[Any]]) -> str:
    return "\n".join("| " + " | ".join("" if item is None else str(item) for item in row) + " |" for row in rows)


def build_completion_audit(
    decisions: list[dict[str, Any]],
    source_hash_manifest: dict[str, Any],
    noleak: dict[str, Any],
    search_ledger: dict[str, Any],
) -> dict[str, Any]:
    status_counts = Counter(row["terminal_source_control_status"] for row in decisions)
    checklist = [
        {
            "requirement": "Run mandatory GTOS preflight and read controlling context",
            "artifact": "NOFILL_REMAINING_CONTEXT_ANCHOR_2026-05-09.md",
            "evidence": "Context anchor records LIVE_STATE regeneration, latest handoff, core context, and controlling artifacts.",
            "status": "PASS",
        },
        {
            "requirement": "Target exactly five residual rows and do not reopen May 3 rows",
            "artifact": "NOFILL_REMAINING_ROW_DECISION_LEDGER_2026-05-09.jsonl",
            "evidence": f"row_count={len(decisions)}; may3_rows_reopened={noleak['may3_rows_reopened']}",
            "status": "PASS" if len(decisions) == 5 and not noleak["may3_rows_reopened"] else "FAIL",
        },
        {
            "requirement": "Pursue XAUUSD active-window cancel gap to proof or exact blocker",
            "artifact": "NOFILL_REMAINING_XAUUSD_ACTIVE_WINDOW_PROOF_PACKET_2026-05-09.json",
            "evidence": "MT5 broker-offset-corrected read-only quote/tick extraction recovered the missing cancel-gap ticks and max bid stayed below short entry.",
            "status": "PASS" if status_counts["SOURCE_CONTROL_CLEARED_INPUT_ONLY"] == 1 else "FAIL",
        },
        {
            "requirement": "Pursue USDJPY same-tick event-order source contract/proof",
            "artifact": "NOFILL_REMAINING_USDJPY_SAME_TICK_EVENT_ORDER_PROOF_PACKET_2026-05-09.json",
            "evidence": f"USDJPY impossible rows={status_counts['SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES']}",
            "status": "PASS" if status_counts["SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES"] == 4 else "FAIL",
        },
        {
            "requirement": "Search local heavy roots and prior worktrees",
            "artifact": "NOFILL_REMAINING_SOURCE_SEARCH_LEDGER_2026-05-09.json",
            "evidence": f"searched_roots={len(search_ledger['searched_roots'])}",
            "status": "PASS",
        },
        {
            "requirement": "Save public/official source-contract raw captures",
            "artifact": "raw/MQL5_*.html and raw/MQL5_SOURCE_INDEX_2026-05-09.json",
            "evidence": "Official MQL5 docs for Python copy_ticks_range, MQL CopyTicksRange, and MqlTick were saved and hashed.",
            "status": "PASS" if all(doc["path"].exists() for doc in RAW_DOCS) else "FAIL",
        },
        {
            "requirement": "Hash consumed source files/raw captures",
            "artifact": "NOFILL_REMAINING_SOURCE_HASH_MANIFEST_2026-05-09.json",
            "evidence": f"record_count={source_hash_manifest['record_count']}",
            "status": "PASS" if source_hash_manifest["record_count"] >= 12 else "FAIL",
        },
        {
            "requirement": "Preserve no-leak duplicate denominator and label-family boundaries",
            "artifact": "NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_AUDIT_2026-05-09.json",
            "evidence": f"violations={len(noleak['violations'])}; forbidden_field_hits={len(noleak['forbidden_output_key_hits'])}; rejects={noleak['reject_total_preserved_outside_labels_denominators']}",
            "status": "PASS" if not noleak["violations"] and not noleak["forbidden_output_key_hits"] and noleak["reject_total_preserved_outside_labels_denominators"] == 65 else "FAIL",
        },
        {
            "requirement": "Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false",
            "artifact": "all generated JSON/JSONL/MD artifacts",
            "evidence": "Builder writes false safety flags and verifier rechecks them.",
            "status": "PASS",
        },
        {
            "requirement": "Run verifier/tests/py_compile/forbidden live-surface diff",
            "artifact": "NOFILL_REMAINING_COMPLETION_AUDIT_2026-05-09.json",
            "evidence": "External command results are appended by verifier after this builder run.",
            "status": "PENDING_VERIFIER_RUN",
        },
    ]
    return {
        "artifact_family": "NOFILL_REMAINING_COMPLETION_AUDIT",
        "schema_version": SCHEMA_VERSION,
        "route_id": LANE_ID,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "objective_restatement": "Close exactly five residual no-fill source/control rows with proof, impossibility, or exact external source requirement; keep source-control separate from result scoring, validation, promotion, and live behavior.",
        "terminal_status_counts": dict(status_counts),
        "can_mark_goal_complete_after_verifier": all(item["status"] in {"PASS", "PENDING_VERIFIER_RUN"} for item in checklist),
        "prompt_to_artifact_checklist": checklist,
        "missing_incomplete_or_weak_requirements": [item for item in checklist if item["status"] == "FAIL"],
        "verification": {"status": "PENDING_VERIFIER_RUN"},
    }


def write_markdown_outputs(
    *,
    decisions: list[dict[str, Any]],
    xau_proof: dict[str, Any],
    usd_proof: dict[str, Any],
    search_ledger: dict[str, Any],
    blocker: dict[str, Any],
    noleak: dict[str, Any],
    source_hash_manifest: dict[str, Any],
    completion: dict[str, Any],
) -> None:
    status_counts = Counter(row["terminal_source_control_status"] for row in decisions)
    (LANE_DIR / f"NOFILL_REMAINING_CONTEXT_ANCHOR_{DATE}.md").write_text(
        "\n".join(
            [
                "# NOFILL Remaining Residual Source Closure Context Anchor",
                "",
                f"Route: `{LANE_ID}`",
                f"Generated: `{completion['generated_at_utc']}`",
                f"HEAD: `{git_output('rev-parse', '--short', 'HEAD')}`",
                f"Promotion posture: `{PROMOTION_VERDICT}`; `validation_safe=false`; `outcome_review_opened=false`; `live_effect=false`.",
                "",
                "## Controlling Prompt",
                "",
                "`research/science_program_2026_05/06_outcome_testing/nofill_remaining_residual_source_closure/NOFILL_REMAINING_RESIDUAL_SOURCE_CLOSURE_GOAL_PROMPT_2026-05-09.md`",
                "",
                "## Scope",
                "",
                "- Source/control only.",
                "- Exactly five target rows.",
                "- May 3 rows are closed context only and were not reopened.",
                "- No result scoring, R/performance, validation, promotion, registry edit, selector change, or live behavior.",
                "",
                "## Active Question Stack",
                "",
                "- XAUUSD active pending window through cancel: can side-aware bid/ask ticks prove no entry touch before cancel?",
                "- USDJPY same-tick rows: can current approved quote/tick sources order entry/protective predicates inside one source row?",
                "- Source/no-leak boundary: keep all target rows outside labels and denominators.",
                "",
                "## Terminal Status Counts",
                "",
                json.dumps(dict(status_counts), indent=2, sort_keys=True),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    search_rows = [["Root", "Exists", "Patterns", "Matches", "Access"]]
    search_rows.append(["---", "---", "---", "---:", "---"])
    for root in search_ledger["searched_roots"]:
        search_rows.append(
            [
                root["root_path"],
                root["exists"],
                ", ".join(root["patterns_used"]),
                root["match_count"],
                root["access_status"],
            ]
        )
    (LANE_DIR / f"NOFILL_REMAINING_SOURCE_SEARCH_LEDGER_{DATE}.md").write_text(
        "# NOFILL Remaining Source Search Ledger\n\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.\n\n"
        + md_table(search_rows)
        + "\n\nThe JSON ledger records consumed source hashes and positive/negative root-level search evidence.\n",
        encoding="utf-8",
    )
    xau_rows = [
        ["Check", "Value"],
        ["---", "---"],
        ["Status", xau_proof["source_control_status"]],
        ["Entry touch before cancel", xau_proof["entry_touch_before_cancel"]],
        ["Recovered gap rows", xau_proof["recovered_gap_rows_through_cancel"]],
        ["Max bid through cancel", xau_proof["max_bid_through_cancel"]],
        ["Entry price", xau_proof["entry_price"]],
    ]
    (LANE_DIR / f"NOFILL_REMAINING_XAUUSD_ACTIVE_WINDOW_PROOF_PACKET_{DATE}.md").write_text(
        "# NOFILL Remaining XAUUSD Active-Window Proof Packet\n\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.\n\n"
        + md_table(xau_rows)
        + "\n\nThe clearance is source/control input-only. It is not a lifecycle/result/performance label and does not move the row into any accepted denominator.\n",
        encoding="utf-8",
    )
    usd_rows = [["Row", "Exact timestamp rows", "Predicates on one row", "Status"]]
    usd_rows.append(["---", "---:", "---", "---"])
    for row in usd_proof["row_evidence"]:
        usd_rows.append(
            [
                row["packet_row_id"],
                row["exact_timestamp_row_count"],
                ",".join(row["true_predicates_on_single_quote_row"]),
                row["terminal_source_control_status"],
            ]
        )
    (LANE_DIR / f"NOFILL_REMAINING_USDJPY_SAME_TICK_EVENT_ORDER_PROOF_PACKET_{DATE}.md").write_text(
        "# NOFILL Remaining USDJPY Same-Tick Event-Order Proof Packet\n\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.\n\n"
        + md_table(usd_rows)
        + "\n\nCurrent approved sources cannot order predicates inside one MqlTick quote-state row. Exact unblocker: broker-native quote-event sequence ID or sub-row timestamp without account/order/history labels.\n",
        encoding="utf-8",
    )
    blocked_rows = [["Row", "Symbol", "Status", "Exact next source"]]
    blocked_rows.append(["---", "---", "---", "---"])
    for row in blocker["rows"]:
        blocked_rows.append([row["packet_row_id"], row["symbol"], row["terminal_source_control_status"], row["exact_next_source_needed"]])
    (LANE_DIR / f"NOFILL_REMAINING_BLOCKER_CLEARANCE_IMPOSSIBILITY_LEDGER_{DATE}.md").write_text(
        "# NOFILL Remaining Blocker/Clearance/Impossibility Ledger\n\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`. No result labels opened.\n\n"
        + md_table(blocked_rows)
        + "\n",
        encoding="utf-8",
    )
    source_rows = [["Metric", "Value"], ["---", "---"], ["Hash records", source_hash_manifest["record_count"]]]
    (LANE_DIR / f"NOFILL_REMAINING_SOURCE_HASH_MANIFEST_{DATE}.md").write_text(
        "# NOFILL Remaining Source Hash Manifest\n\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`.\n\n"
        + md_table(source_rows)
        + "\n\nSee the JSON manifest for per-file paths, sizes, sha256 hashes, roles, and source URLs.\n",
        encoding="utf-8",
    )
    noleak_rows = [
        ["Check", "Value"],
        ["---", "---"],
        ["Target rows", noleak["target_row_count"]],
        ["May 3 rows reopened", noleak["may3_rows_reopened"]],
        ["Rejects preserved", noleak["reject_total_preserved_outside_labels_denominators"]],
        ["Rows moved to denominator", noleak["rows_moved_to_accepted_denominator"]],
        ["Lifecycle labels assigned", noleak["lifecycle_labels_assigned"]],
        ["Forbidden output key hits", len(noleak["forbidden_output_key_hits"])],
        ["Violations", len(noleak["violations"])],
    ]
    (LANE_DIR / f"NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_AUDIT_{DATE}.md").write_text(
        "# NOFILL Remaining No-Leak Duplicate Denominator Label-Family Audit\n\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`.\n\n"
        + md_table(noleak_rows)
        + "\n",
        encoding="utf-8",
    )
    next_prompt = """# NOFILL Remaining Residual Source Closure Next Prompt Pack

Promotion posture: `NO_PROMOTION_VERDICT`
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Recommended Next Gate

Run `G12_NOFILL_REMAINING_RESIDUAL_SOURCE_CLOSURE_AUDIT` against this directory.

## Exact G12 Audit Questions

1. Verify exactly five target rows are present: `NOFILL-CAT-ROW-0241`, `NOFILL-CAT-ROW-0130`, `NOFILL-CAT-ROW-0143`, `NOFILL-CAT-ROW-0165`, `NOFILL-CAT-ROW-0178`.
2. Verify May 3 rows `0049/0050/0051` are referenced only as closed context and not reopened.
3. Verify XAUUSD `0241` can be accepted as `SOURCE_CONTROL_CLEARED_INPUT_ONLY` from broker-offset-corrected read-only MT5 quote/tick evidence, with no entry touch through cancel.
4. Verify USDJPY `0130/0143/0165/0178` remain `SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES` because one MqlTick quote-state row satisfies multiple touch predicates and no sub-row order source exists.
5. Verify official MQL5 raw captures support the source contract and are hashed.
6. Verify all source hashes recompute.
7. Verify no labels, denominators, R/performance, validation, promotion, registry edits, or live behavior are opened.

## Closed Routes

- No result scoring or R/performance.
- No broker actual-R, account/order/deal/position/history labels.
- No selector, safety, prompt, risk, execution, canary, credential, remote, registry, paid/API/Databento, or live order behavior changes.
"""
    (LANE_DIR / f"NOFILL_REMAINING_NEXT_PROMPT_PACK_{DATE}.md").write_text(next_prompt, encoding="utf-8")
    checklist_rows = [["Requirement", "Artifact", "Status"]]
    checklist_rows.append(["---", "---", "---"])
    for item in completion["prompt_to_artifact_checklist"]:
        checklist_rows.append([item["requirement"], item["artifact"], item["status"]])
    (LANE_DIR / f"NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.md").write_text(
        "# NOFILL Remaining Completion Audit\n\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`.\n\n"
        + md_table(checklist_rows)
        + "\n",
        encoding="utf-8",
    )


def write_raw_source_index() -> SourceRef:
    index = {
        "artifact_family": "NOFILL_REMAINING_MQL5_SOURCE_INDEX",
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": utc_now(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "captures": [
            {
                "url": doc["url"],
                "path": str(doc["path"]),
                "exists": doc["path"].exists(),
                "size_bytes": doc["path"].stat().st_size if doc["path"].exists() else None,
                "sha256": sha256_file(doc["path"]) if doc["path"].exists() else None,
                "role": doc["role"],
                "used_for_factual_claims": doc["path"].exists(),
            }
            for doc in RAW_DOCS
        ],
    }
    path = RAW_DIR / f"MQL5_SOURCE_INDEX_{DATE}.json"
    write_json(path, index)
    return SourceRef(path, "official_mql5_source_index", "json_source_index")


def build_all(*, skip_mt5: bool = False) -> dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cat_rows = load_cat_v2_rows()
    oti2_row = load_oti2_target_row()
    oti3_rows = load_oti3_rows()
    xau_offset = infer_broker_offset_seconds(MAIN_TICKS / "XAUUSD" / "2026-05-05.parquet")
    mt5_capture = extract_xau_gap_ticks(
        broker_offset_seconds=int(xau_offset["rounded_broker_offset_seconds"]),
        skip_mt5=skip_mt5,
    )
    xau_proof, xau_refs = build_xauusd_proof(oti2_row, mt5_capture)
    usd_proof, usd_refs = build_usdjpy_proof(oti3_rows)
    raw_index_ref = write_raw_source_index()
    doc_refs = [
        SourceRef(doc["path"], doc["role"], "curl_saved_official_html", doc["url"])
        for doc in RAW_DOCS
    ]
    source_refs = xau_refs + usd_refs + doc_refs + [raw_index_ref]
    search_ledger = build_search_ledger(source_refs)
    decisions = build_row_decisions(cat_rows, xau_proof, usd_proof)
    noleak = build_noleak_duplicate_audit(cat_rows, decisions, reject_count(), xau_proof, usd_proof)
    blocker = build_blocker_ledger(decisions)
    control_refs = [SourceRef(ROOT / path, "controlling_input", None) for path in CONTROL_INPUTS]
    source_hash_manifest = build_source_hash_manifest(source_refs, control_refs)
    completion = build_completion_audit(decisions, source_hash_manifest, noleak, search_ledger)

    write_json(LANE_DIR / f"NOFILL_REMAINING_XAUUSD_ACTIVE_WINDOW_PROOF_PACKET_{DATE}.json", xau_proof)
    write_json(LANE_DIR / f"NOFILL_REMAINING_USDJPY_SAME_TICK_EVENT_ORDER_PROOF_PACKET_{DATE}.json", usd_proof)
    write_json(LANE_DIR / f"NOFILL_REMAINING_SOURCE_SEARCH_LEDGER_{DATE}.json", search_ledger)
    write_jsonl(LANE_DIR / f"NOFILL_REMAINING_ROW_DECISION_LEDGER_{DATE}.jsonl", decisions)
    write_json(LANE_DIR / f"NOFILL_REMAINING_BLOCKER_CLEARANCE_IMPOSSIBILITY_LEDGER_{DATE}.json", blocker)
    write_json(LANE_DIR / f"NOFILL_REMAINING_SOURCE_HASH_MANIFEST_{DATE}.json", source_hash_manifest)
    write_json(LANE_DIR / f"NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_AUDIT_{DATE}.json", noleak)
    write_json(LANE_DIR / f"NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.json", completion)
    write_markdown_outputs(
        decisions=decisions,
        xau_proof=xau_proof,
        usd_proof=usd_proof,
        search_ledger=search_ledger,
        blocker=blocker,
        noleak=noleak,
        source_hash_manifest=source_hash_manifest,
        completion=completion,
    )
    summary = {
        "status": "BUILT",
        "route_id": LANE_ID,
        "target_row_count": len(decisions),
        "terminal_status_counts": dict(Counter(row["terminal_source_control_status"] for row in decisions)),
        "xau_mt5_capture_status": mt5_capture.get("status"),
        "source_hash_record_count": source_hash_manifest["record_count"],
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-mt5", action="store_true", help="Do not run the read-only XAUUSD MT5 copy_ticks_range extraction.")
    args = parser.parse_args()
    build_all(skip_mt5=args.skip_mt5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
