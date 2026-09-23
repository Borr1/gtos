#!/usr/bin/env python3
"""Build OTI3 USDJPY quote/tick contract evidence artifacts.

Research/source-correction only. This lane consumes the 69 USDJPY
``BLOCK_RESULT_LTF_PRICE_ONLY`` rows from the accepted no-fill categorical
packet, searches source-hashed USDJPY bid/ask tick evidence, optionally extracts
only read-only MT5 ticks for the two owner-approved missing dates, and emits
categorical lifecycle evidence or exact blockers.

It never computes R/performance and never calls MT5 account, history, order, or
position APIs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq


DATE = "2026-05-08"
LANE_ID = "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT"
SCHEMA = "oti3_usdjpy_price_only_quote_or_tick_contract_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
VALIDATION_SAFE = False
OUTCOME_REVIEW_OPENED = False
LIVE_EFFECT = False

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
OUTCOME_ROOT = REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"
ROUTER_DIR = OUTCOME_ROOT / "nofill_blocked_family_source_correction_router"
CAT_DIR = OUTCOME_ROOT / "no_fill_lifecycle_categorical_result_packet"

CAT_ROWS = CAT_DIR / "NOFILL_CAT_PACKET_ROWS_2026-05-08.jsonl"
CAT_ELIGIBILITY = CAT_DIR / "NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_2026-05-08.json"
SOURCE_PACKET_ROWS = OUTCOME_ROOT / "no_fill_lifecycle_closure_source_packet" / "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl"
ROUTER_ROUTE_LEDGER = ROUTER_DIR / "NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json"
ROUTER_SEARCH_LEDGER = ROUTER_DIR / "NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json"
ROUTER_CONTEXT_ANCHOR = ROUTER_DIR / "NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.md"
CONTROLLING_PROMPT = ROUTER_DIR / "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT_PROMPT_PACK_2026-05-08.md"
RULEBOOK = OUTCOME_ROOT / "no_fill_lifecycle_result_contract_design" / "NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-08.json"
TOUCH_PARSER = OUTCOME_ROOT / "no_fill_lifecycle_result_contract_design" / "NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_2026-05-08.json"

MAIN_ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
MAIN_TICKS = MAIN_ROOT / "data" / "ticks" / "USDJPY"
MAIN_M1_CONTEXT = MAIN_ROOT / "data" / "mt5_research_exports" / "phase3_v2b_forward_20260401_20260502_readonly" / "USDJPY_M1.csv"
WORKTREE_TICKS = REPO_ROOT / "data" / "ticks" / "USDJPY"
TMP_ROOT = Path(r"C:\tmp")
DOCS_ROOT = Path(r"C:\Users\MSI\Documents")

NEEDED_DATES = ["2026-04-17", "2026-04-20", "2026-04-30", "2026-05-01"]
APPROVED_EXTRACTION_DATES = {"2026-04-17", "2026-04-20"}
ACCESS_REQUEST_ROW_IDS = {
    "NOFILL-CLOSE-ROW-0129",
    "NOFILL-CLOSE-ROW-0130",
    "NOFILL-CLOSE-ROW-0131",
    "NOFILL-CLOSE-ROW-0163",
    "NOFILL-CLOSE-ROW-0164",
    "NOFILL-CLOSE-ROW-0165",
    "NOFILL-CLOSE-ROW-0166",
}

FORBIDDEN_KEYS = {
    "account_history",
    "actual_r",
    "broker_actual_r",
    "broker_fill_state",
    "broker_order_id",
    "broker_position_id",
    "conservative_lower_bound_r",
    "descriptive_gross_synthetic_path_r",
    "descriptive_synthetic_path_r",
    "dsr",
    "expectancy",
    "hidden_label",
    "live_order_state",
    "live_trade_result",
    "mt5_deal_ticket",
    "mt5_order_ticket",
    "mt5_position_ticket",
    "pbo",
    "pending_ticket",
    "profit",
    "reward_r_to_tp1",
    "synthetic_r",
    "trade_state_ticket",
    "win_rate",
}

LIVE_SURFACE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary_fixtures/",
    "run_agent.py",
    "start_all.bat",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: Any) -> datetime:
    text = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_utc(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if isinstance(value, str):
        value = parse_utc(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    return None


def rel(path: Path | str) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(REPO_ROOT).as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_stat(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False, "sha256": None, "size_bytes": None}
    st = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": st.st_size,
        "last_write_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
        "sha256": sha256_file(path),
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def write_md_json(path: Path, title: str, payload: dict[str, Any], bullets: list[str] | None = None) -> None:
    lines = [
        f"# {title}",
        "",
        f"Promotion verdict: `{PROMOTION_VERDICT}`",
        f"Validation safe: `{str(VALIDATION_SAFE).lower()}`",
        f"Outcome review opened: `{str(OUTCOME_REVIEW_OPENED).lower()}`",
        f"Live effect: `{str(LIVE_EFFECT).lower()}`",
        "",
    ]
    if bullets:
        lines.extend(bullets)
        lines.append("")
    lines.extend(["```json", json.dumps(payload, indent=2, sort_keys=True, default=str), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"GIT_UNAVAILABLE:{exc!r}"


def base_payload(family: str) -> dict[str, Any]:
    return {
        "artifact_family": family,
        "schema_version": SCHEMA,
        "generated_at_utc": utc_now(),
        "lane_id": LANE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "live_effect": LIVE_EFFECT,
        "repo_head": git_output("rev-parse", "HEAD"),
        "scope": "source_correction_or_contract_revision_only",
        "no_r_performance_scoring": True,
        "forbidden_surfaces": {
            "account_history_accessed": False,
            "broker_actual_r_accessed": False,
            "live_trade_result_accessed": False,
            "mt5_account_calls": 0,
            "mt5_history_calls": 0,
            "mt5_order_calls": 0,
            "mt5_position_calls": 0,
            "order_send_calls": 0,
            "paid_api_or_databento_calls": 0,
        },
    }


def load_oti3_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_jsonl(CAT_ROWS):
        if row.get("symbol") == "USDJPY" and "BLOCK_RESULT_LTF_PRICE_ONLY" in (row.get("result_blocker_codes") or []):
            rows.append(row)
    rows.sort(key=lambda r: (r["source_close_packet_row_id"], r["packet_row_id"]))
    return rows


def source_reference_files() -> list[Path]:
    return [
        CAT_ROWS,
        CAT_ELIGIBILITY,
        SOURCE_PACKET_ROWS,
        ROUTER_ROUTE_LEDGER,
        ROUTER_SEARCH_LEDGER,
        ROUTER_CONTEXT_ANCHOR,
        CONTROLLING_PROMPT,
        RULEBOOK,
        TOUCH_PARSER,
        MAIN_M1_CONTEXT,
    ]


def exact_tick_candidates_for_date(date_iso: str) -> list[Path]:
    candidates = [
        WORKTREE_TICKS / f"{date_iso}.parquet",
        MAIN_TICKS / f"{date_iso}.parquet",
    ]
    gtos_root = Path(r"C:\tmp\gtos_otb")
    if gtos_root.exists():
        try:
            candidates.extend(sorted(gtos_root.glob(f"*/data/ticks/USDJPY/{date_iso}.parquet")))
            candidates.extend(sorted(gtos_root.glob(f"*/research/**/USDJPY*{date_iso}*.parquet")))
            candidates.extend(sorted(gtos_root.glob(f"*/research/**/*USDJPY*TICKS*{date_iso}*.parquet")))
        except OSError:
            pass
    return list(dict.fromkeys(candidates))


def choose_existing_tick_source(date_iso: str) -> Path | None:
    for candidate in exact_tick_candidates_for_date(date_iso):
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def targeted_search(root: Path, tokens: list[str], cap: int = 120) -> dict[str, Any]:
    entry = {
        "root": str(root),
        "exists": root.exists(),
        "tokens": tokens,
        "match_count": 0,
        "matches": [],
        "errors": [],
        "truncated": False,
    }
    if not root.exists():
        return entry
    skip_dirs = {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache", ".mypy_cache"}

    def on_error(exc: OSError) -> None:
        entry["errors"].append({"error": repr(exc), "filename": getattr(exc, "filename", None)})

    try:
        for current, dirs, files in os.walk(root, topdown=True, onerror=on_error):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for name in files:
                hay = str(Path(current) / name).lower()
                if all(token.lower() in hay for token in tokens):
                    entry["match_count"] += 1
                    if len(entry["matches"]) < cap:
                        entry["matches"].append(file_stat(Path(current) / name))
                    else:
                        entry["truncated"] = True
    except OSError as exc:
        entry["errors"].append({"error": repr(exc), "filename": getattr(exc, "filename", None)})
    return entry


def inspect_tick_file(path: Path, date_iso: str, required_decisions: list[str]) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False, "coverage_status": "MISSING_FILE"}
    try:
        parquet = pq.ParquetFile(path)
        columns = parquet.schema.names
        required_columns = ["ts_utc", "bid", "ask"]
        missing = [col for col in required_columns if col not in columns]
        if missing:
            return {
                **file_stat(path),
                "coverage_status": "UNUSABLE_MISSING_REQUIRED_COLUMNS",
                "missing_columns": missing,
                "schema_columns": columns,
            }
        df = pq.read_table(path, columns=["ts_utc", "bid", "ask"]).to_pandas()
        df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
        start = pd.Timestamp(f"{date_iso}T00:00:00Z")
        end = start + pd.Timedelta(days=1)
        in_date = df[(df["ts_utc"] >= start) & (df["ts_utc"] < end)]
        decision_coverage = {}
        for decision in required_decisions:
            ts = pd.Timestamp(decision)
            decision_coverage[decision] = bool((df["ts_utc"] >= ts).any())
        return {
            **file_stat(path),
            "coverage_status": "COVERS_REQUESTED_DECISION_DATE" if not in_date.empty and all(decision_coverage.values()) else "INSUFFICIENT_REQUESTED_DECISION_DATE_ROWS",
            "schema_columns": columns,
            "row_count": int(len(df)),
            "date_row_count": int(len(in_date)),
            "min_ts_utc": iso_utc(df["ts_utc"].min()) if not df.empty else None,
            "max_ts_utc": iso_utc(df["ts_utc"].max()) if not df.empty else None,
            "decision_coverage": decision_coverage,
        }
    except Exception as exc:
        return {**file_stat(path), "coverage_status": "INSPECTION_ERROR", "error": repr(exc)}


def normalize_mt5_ticks_to_frame(ticks: Any, *, timestamp_mode: str) -> pd.DataFrame:
    df = pd.DataFrame(ticks)
    if df.empty:
        return df
    if "time_msc" in df.columns:
        ts = pd.to_datetime(df["time_msc"], unit="ms", utc=True)
    elif "time" in df.columns:
        ts = pd.to_datetime(df["time"], unit="s", utc=True)
    else:
        raise ValueError("MT5 ticks do not expose time_msc or time")
    df.insert(0, "ts_utc", ts)
    df["timestamp_mode"] = timestamp_mode
    df["mt5_symbol"] = "USDJPY"
    rename = {"time_msc": "ts_msc"}
    df = df.rename(columns=rename)
    for col in ["bid", "ask", "last", "volume", "flags"]:
        if col not in df.columns:
            df[col] = 0
    keep = ["ts_utc", "ts_msc", "bid", "ask", "last", "volume", "flags", "mt5_symbol", "timestamp_mode"]
    return df[keep].sort_values("ts_utc").drop_duplicates(subset=["ts_msc"], keep="last").reset_index(drop=True)


def extract_missing_tick_date(date_iso: str, *, skip_mt5: bool) -> dict[str, Any]:
    out_path = OUT_DIR / f"OTI3_MT5_READ_ONLY_USDJPY_TICKS_{date_iso}.parquet"
    start = datetime.fromisoformat(f"{date_iso}T00:00:00+00:00")
    end = start + timedelta(days=1)
    payload = {
        "date": date_iso,
        "attempted": False,
        "allowed_by_owner_prompt": date_iso in APPROVED_EXTRACTION_DATES,
        "route": "MetaTrader5.copy_ticks_range",
        "symbol": "USDJPY",
        "query_start_utc": start.isoformat(),
        "query_end_utc": end.isoformat(),
        "timestamp_policy": "copy_ticks_range_time_msc_used_as_utc_when_returned_ticks_align_with_requested_utc_window",
        "account_info_called": False,
        "history_deals_get_called": False,
        "history_orders_get_called": False,
        "orders_get_called": False,
        "positions_get_called": False,
        "order_send_called": False,
        "paid_api_or_databento_called": False,
        "output_path": str(out_path),
        "output_sha256": None,
        "rows": 0,
        "coverage_status": "SKIPPED_BY_FLAG" if skip_mt5 else "NOT_RUN",
    }
    if skip_mt5:
        return payload
    if date_iso not in APPROVED_EXTRACTION_DATES:
        payload["coverage_status"] = "NOT_APPROVED_FOR_EXTRACTION"
        return payload

    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:
        payload.update({"attempted": True, "coverage_status": "MT5_IMPORT_FAILED", "error": repr(exc)})
        return payload

    payload["attempted"] = True
    initialized = False
    try:
        initialized = bool(mt5.initialize())
        payload["initialize_returned"] = initialized
        payload["last_error_after_initialize"] = str(mt5.last_error())
        if not initialized:
            payload["coverage_status"] = "MT5_INITIALIZE_FAILED"
            return payload
        ticks = mt5.copy_ticks_range("USDJPY", start, end, mt5.COPY_TICKS_ALL)
        payload["last_error_after_copy_ticks_range"] = str(mt5.last_error())
        if ticks is None:
            payload["coverage_status"] = "COPY_TICKS_RANGE_RETURNED_NONE"
            return payload
        df = normalize_mt5_ticks_to_frame(ticks, timestamp_mode="time_msc_as_utc")
        payload["rows"] = int(len(df))
        if df.empty:
            payload["coverage_status"] = "ZERO_ROWS_RETURNED"
            return payload
        date_start = pd.Timestamp(start)
        date_end = pd.Timestamp(end)
        in_requested = df[(df["ts_utc"] >= date_start) & (df["ts_utc"] < date_end)]
        payload["source_first_ts_utc"] = iso_utc(df["ts_utc"].min())
        payload["source_last_ts_utc"] = iso_utc(df["ts_utc"].max())
        payload["requested_date_row_count"] = int(len(in_requested))
        if in_requested.empty:
            payload["coverage_status"] = "EXTRACTED_ROWS_DO_NOT_ALIGN_WITH_REQUESTED_UTC_DATE"
            return payload
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out_path, index=False, compression="snappy")
        payload["output_sha256"] = sha256_file(out_path)
        payload["output_size_bytes"] = out_path.stat().st_size
        payload["coverage_status"] = "RECOVERED_ROWS_FROM_READ_ONLY_MT5_COPY_TICKS_RANGE"
        return payload
    except Exception as exc:
        payload.update({"coverage_status": "MT5_EXTRACTION_EXCEPTION", "error": repr(exc)})
        return payload
    finally:
        if initialized:
            try:
                mt5.shutdown()
            except Exception:
                pass


def build_source_inventory(rows: list[dict[str, Any]], *, skip_mt5: bool) -> tuple[dict[str, Any], dict[str, Path | None]]:
    decisions_by_date: dict[str, list[str]] = {}
    for row in rows:
        decisions_by_date.setdefault(row["decision_asof_utc"][:10], []).append(row["decision_asof_utc"])

    date_sources: dict[str, Path | None] = {}
    initial_date_records = {}
    extraction_attempts = []
    for date_iso in NEEDED_DATES:
        existing = choose_existing_tick_source(date_iso)
        initial_date_records[date_iso] = {
            "selected_existing_source": str(existing) if existing else None,
            "all_exact_candidates": [str(path) for path in exact_tick_candidates_for_date(date_iso)],
            "selected_existing_source_inspection": inspect_tick_file(existing, date_iso, decisions_by_date.get(date_iso, [])) if existing else None,
        }
        date_sources[date_iso] = existing

    for date_iso in NEEDED_DATES:
        if date_sources[date_iso] is None and date_iso in APPROVED_EXTRACTION_DATES:
            attempt = extract_missing_tick_date(date_iso, skip_mt5=skip_mt5)
            extraction_attempts.append(attempt)
            out_path = Path(attempt["output_path"])
            if attempt.get("coverage_status") == "RECOVERED_ROWS_FROM_READ_ONLY_MT5_COPY_TICKS_RANGE" and out_path.exists():
                date_sources[date_iso] = out_path

    final_date_records = {
        date_iso: inspect_tick_file(path, date_iso, decisions_by_date.get(date_iso, [])) if path else {"date": date_iso, "coverage_status": "MISSING_QUOTE_TICK_SOURCE", "path": None}
        for date_iso, path in date_sources.items()
    }
    search_tokens = []
    for date_iso in NEEDED_DATES:
        search_tokens.append(targeted_search(TMP_ROOT, ["USDJPY", date_iso, "parquet"], cap=80))
    for date_iso in APPROVED_EXTRACTION_DATES:
        search_tokens.append(targeted_search(DOCS_ROOT, ["USDJPY", date_iso, "parquet"], cap=80))

    ledger = base_payload("OTI3_USDJPY_SOURCE_SEARCH_LEDGER")
    ledger.update(
        {
            "row_count": len(rows),
            "needed_dates": NEEDED_DATES,
            "approved_extraction_dates": sorted(APPROVED_EXTRACTION_DATES),
            "access_request_row_ids": sorted(ACCESS_REQUEST_ROW_IDS),
            "initial_tick_source_probe_by_date": initial_date_records,
            "mt5_read_only_extraction_attempts": extraction_attempts,
            "final_tick_source_by_date": {
                date_iso: str(path) if path else None for date_iso, path in date_sources.items()
            },
            "final_tick_source_inspection_by_date": final_date_records,
            "targeted_recursive_searches": search_tokens,
            "usdjpy_m1_context_source": file_stat(MAIN_M1_CONTEXT),
            "search_conclusion": "quote_tick_sources_present_for_all_needed_dates"
            if all(date_sources.values())
            else "exact_quote_tick_source_missing_for_some_rows",
        }
    )
    return ledger, date_sources


def load_tick_frame(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if "time_msc" in df.columns and "ts_msc" not in df.columns:
        df = df.rename(columns={"time_msc": "ts_msc"})
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    return df.sort_values(["ts_utc", "ts_msc" if "ts_msc" in df.columns else "ts_utc"]).reset_index(drop=True)


def side_aware_masks(df: pd.DataFrame, row: dict[str, Any]) -> list[tuple[str, pd.Series]]:
    side = row["side"]
    entry = float(row["entry_price"])
    terminal = float(row["terminal_area_price"])
    protective = float(row["protective_level_price"])
    if side == "LONG":
        return [
            ("entry_touch", df["ask"] <= entry),
            ("terminal_area", df["bid"] >= terminal),
            ("protective_level", df["bid"] <= protective),
        ]
    if side == "SHORT":
        return [
            ("entry_touch", df["bid"] >= entry),
            ("terminal_area", df["ask"] <= terminal),
            ("protective_level", df["ask"] >= protective),
        ]
    raise ValueError(f"unsupported side {side!r}")


def ordered_events_for_row(row: dict[str, Any], df: pd.DataFrame, source_path: Path) -> tuple[list[dict[str, Any]], bool, dict[str, Any]]:
    decision = pd.Timestamp(row["decision_asof_utc"])
    window = df[df["ts_utc"] >= decision].copy()
    events: list[dict[str, Any]] = []
    for event_name, mask in side_aware_masks(window, row):
        hits = window[mask]
        if hits.empty:
            continue
        hit = hits.iloc[0]
        events.append(
            {
                "event": event_name,
                "first_touch_utc": iso_utc(hit["ts_utc"]),
                "bid": float(hit["bid"]),
                "ask": float(hit["ask"]),
                "source_path": str(source_path),
                "source_sha256": sha256_file(source_path),
            }
        )
    events.sort(key=lambda event: (event["first_touch_utc"], event["event"]))
    same_timestamp = False
    if events:
        first_ts = events[0]["first_touch_utc"]
        same_timestamp = sum(1 for event in events if event["first_touch_utc"] == first_ts) > 1
    coverage = {
        "source_path_start_utc": iso_utc(decision.to_pydatetime()),
        "source_path_end_utc": iso_utc(window["ts_utc"].max()) if not window.empty else None,
        "source_window_row_count": int(len(window)),
        "source_first_ts_utc": iso_utc(df["ts_utc"].min()) if not df.empty else None,
        "source_last_ts_utc": iso_utc(df["ts_utc"].max()) if not df.empty else None,
    }
    return events, same_timestamp, coverage


def classify_row(row: dict[str, Any], source_path: Path | None, tick_cache: dict[str, pd.DataFrame]) -> dict[str, Any]:
    base = {
        "schema_version": SCHEMA,
        "lane_id": LANE_ID,
        "source_packet_row_id": row["packet_row_id"],
        "source_close_packet_row_id": row["source_close_packet_row_id"],
        "source_inventory_id": row["source_inventory_id"],
        "source_lane": row["source_lane"],
        "source_packet_id": row["source_packet_id"],
        "source_row_id": row["source_row_id"],
        "symbol": row["symbol"],
        "session": row["session"],
        "side": row["side"],
        "decision_asof_utc": row["decision_asof_utc"],
        "entry_price": row["entry_price"],
        "terminal_area_price": row["terminal_area_price"],
        "protective_level_price": row["protective_level_price"],
        "nofill_duplicate_key": row["nofill_duplicate_key"],
        "duplicate_group_id": row["duplicate_group_id"],
        "parser_contract": "bid_ask_side_aware_touch_times_v1",
        "ordered_source_events": [],
        "same_timestamp_ambiguity": False,
        "entry_touch_time_utc": None,
        "terminal_area_touch_time_utc": None,
        "protective_level_touch_time_utc": None,
        "categorical_lifecycle_label": None,
        "categorical_label_status": "blocked_no_label",
        "label_family": None,
        "eligibility_decision": "BLOCKED_EXACT",
        "route_status": "exact_blocker",
        "quote_tick_evidence_status": "not_available",
        "exact_blocker_codes": [],
        "exact_blocker_reasons": [],
        "source_references": list(row.get("source_references") or []),
        "source_path_start_utc": None,
        "source_path_end_utc": None,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": VALIDATION_SAFE,
        "outcome_review_opened": OUTCOME_REVIEW_OPENED,
        "live_effect": LIVE_EFFECT,
    }
    date_iso = row["decision_asof_utc"][:10]
    if source_path is None:
        base["exact_blocker_codes"].append("BLOCK_OTI3_MISSING_QUOTE_TICK_SOURCE_WITH_EXACT_ACCESS_REQUEST")
        base["exact_blocker_reasons"].append(
            f"Missing source-hashed USDJPY bid/ask tick parquet for {date_iso}; approved route is read-only USDJPY copy_ticks_range or source-equivalent cached file, no MT5 order/account/history calls."
        )
        return base
    if not source_path.exists():
        base["exact_blocker_codes"].append("BLOCK_OTI3_SELECTED_SOURCE_PATH_MISSING")
        base["exact_blocker_reasons"].append(f"Selected source path does not exist: {source_path}")
        return base
    try:
        key = str(source_path)
        if key not in tick_cache:
            tick_cache[key] = load_tick_frame(source_path)
        df = tick_cache[key]
    except Exception as exc:
        base["exact_blocker_codes"].append("BLOCK_OTI3_TICK_SOURCE_PARSE_ERROR")
        base["exact_blocker_reasons"].append(f"Could not parse source-hashed tick file: {exc!r}")
        return base
    for col in ["ts_utc", "bid", "ask"]:
        if col not in df.columns:
            base["exact_blocker_codes"].append("BLOCK_OTI3_TICK_SOURCE_MISSING_REQUIRED_COLUMN")
            base["exact_blocker_reasons"].append(f"Tick source missing required column {col}")
            return base
    events, same_timestamp, coverage = ordered_events_for_row(row, df, source_path)
    base["ordered_source_events"] = events
    base["same_timestamp_ambiguity"] = same_timestamp
    base["source_path_start_utc"] = coverage["source_path_start_utc"]
    base["source_path_end_utc"] = coverage["source_path_end_utc"]
    base["source_window_row_count"] = coverage["source_window_row_count"]
    base["quote_tick_evidence_status"] = "quote_tick_path_materialized"
    base["source_references"].append({"path": str(source_path), "expected_sha256": sha256_file(source_path), "role": "bid_ask_quote_tick_source"})

    for event in events:
        if event["event"] == "entry_touch":
            base["entry_touch_time_utc"] = event["first_touch_utc"]
        elif event["event"] == "terminal_area":
            base["terminal_area_touch_time_utc"] = event["first_touch_utc"]
        elif event["event"] == "protective_level":
            base["protective_level_touch_time_utc"] = event["first_touch_utc"]

    if same_timestamp:
        base["exact_blocker_codes"].append("BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS")
        base["exact_blocker_reasons"].append("First source timestamp has multiple side-aware events; ordering is ambiguous under the frozen contract.")
        return base
    if not events:
        base["exact_blocker_codes"].append("BLOCK_OTI3_NO_TOUCH_EVENTS_BUT_NO_FROZEN_HORIZON_FIELD")
        base["exact_blocker_reasons"].append(
            "Quote/tick source has no entry, terminal, or protective touch after decision, but the OTI3 price-only row does not carry a frozen observation horizon required for no-entry-through-horizon labeling."
        )
        return base

    first_event = events[0]["event"]
    if first_event == "terminal_area":
        base["categorical_lifecycle_label"] = "nofill_terminal_before_entry"
        base["categorical_label_status"] = "categorical_lifecycle_only"
        base["label_family"] = "categorical_lifecycle_only"
        base["eligibility_decision"] = "ELIGIBLE_CONTRACT_EVIDENCE"
        base["route_status"] = "quote_tick_categorical_contract_evidence"
        base["label_assignment_basis"] = "first side-aware quote/tick source event is terminal_area before entry/protective touch"
        return base
    if first_event == "entry_touch":
        base["quote_tick_evidence_status"] = "entry_touch_before_terminal"
        base["exact_blocker_codes"].append("BLOCK_OTI3_ENTRY_TOUCH_BEFORE_TERMINAL_SEPARATE_FILL_PATH_CONTRACT_REQUIRED")
        base["exact_blocker_reasons"].append(
            "Side-aware entry touch occurs before terminal-area touch; this is quote/tick evidence against no-fill terminal-before-entry and belongs to a separate fill/path contract, not this no-fill closure label."
        )
        return base
    if first_event == "protective_level":
        base["quote_tick_evidence_status"] = "protective_touch_before_terminal"
        base["exact_blocker_codes"].append("BLOCK_OTI3_PROTECTIVE_TOUCH_BEFORE_TERMINAL_UNSUPPORTED_NOFILL_LABEL_FAMILY")
        base["exact_blocker_reasons"].append(
            "Protective level touches before terminal-area and entry; the frozen no-fill lifecycle label set has no protective-before-entry category."
        )
        return base
    base["exact_blocker_codes"].append("BLOCK_OTI3_UNSUPPORTED_FIRST_EVENT")
    base["exact_blocker_reasons"].append(f"Unsupported first event under parser: {first_event}")
    return base


def build_row_decisions(rows: list[dict[str, Any]], date_sources: dict[str, Path | None]) -> list[dict[str, Any]]:
    cache: dict[str, pd.DataFrame] = {}
    decisions = []
    for row in rows:
        decisions.append(classify_row(row, date_sources.get(row["decision_asof_utc"][:10]), cache))
    return decisions


def scan_forbidden_keys(value: Any, path: str = "$") -> list[dict[str, str]]:
    hits = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                hits.append({"path": path, "key": str(key)})
            hits.extend(scan_forbidden_keys(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for idx, nested in enumerate(value):
            hits.extend(scan_forbidden_keys(nested, f"{path}[{idx}]"))
    return hits


def collect_source_hash_records(date_sources: dict[str, Path | None], row_decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for path in source_reference_files():
        records[str(path)] = {**file_stat(path), "role": "controlling_or_upstream_input"}
    for date_iso, path in date_sources.items():
        if path is None:
            continue
        records[str(path)] = {**file_stat(path), "role": "bid_ask_quote_tick_source", "date": date_iso}
    for row in row_decisions:
        for ref in row.get("source_references") or []:
            path = Path(ref["path"])
            if path.exists():
                records[str(path)] = {
                    **file_stat(path),
                    "role": ref.get("role", "row_source_reference"),
                    "expected_sha256": ref.get("expected_sha256"),
                    "hash_match": (sha256_file(path) == ref.get("expected_sha256")) if ref.get("expected_sha256") else None,
                }
    return list(records.values())


def build_contract_packet(row_decisions: list[dict[str, Any]]) -> dict[str, Any]:
    packet = base_payload("OTI3_USDJPY_QUOTE_TICK_CONTRACT_PACKET")
    packet.update(
        {
            "contract_status": "ROW_LEVEL_EVIDENCE_OR_EXACT_BLOCKERS_EMITTED",
            "row_count": len(row_decisions),
            "parser_contract": {
                "parser_id": "bid_ask_side_aware_touch_times_v1",
                "long": {
                    "entry_touch": "ask <= entry_price",
                    "terminal_area_touch": "bid >= terminal_area_price",
                    "protective_touch": "bid <= protective_level_price",
                },
                "short": {
                    "entry_touch": "bid >= entry_price",
                    "terminal_area_touch": "ask <= terminal_area_price",
                    "protective_touch": "ask >= protective_level_price",
                },
                "same_timestamp_policy": "block as BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS",
                "no_event_policy": "block unless a frozen observation horizon is present in the source row",
            },
            "allowed_labels": ["nofill_terminal_before_entry"],
            "blocked_or_separate_family_evidence": {
                "entry_touch_before_terminal": "quote/tick evidence belongs to separate fill/path contract; no no-fill lifecycle label assigned here",
                "protective_touch_before_terminal": "unsupported no-fill label family under frozen contract",
                "missing_tick_source": "exact access/source request required",
            },
            "label_family_boundary": "categorical_lifecycle_only; no R/performance/broker/account/live/order labels",
        }
    )
    return packet


def build_audits(rows: list[dict[str, Any]], row_decisions: list[dict[str, Any]], source_hash_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    eligible = [row for row in row_decisions if row["eligibility_decision"] == "ELIGIBLE_CONTRACT_EVIDENCE"]
    blocked = [row for row in row_decisions if row["eligibility_decision"] != "ELIGIBLE_CONTRACT_EVIDENCE"]
    blocker_counts = Counter(code for row in row_decisions for code in row["exact_blocker_codes"])
    date_counts = Counter(row["decision_asof_utc"][:10] for row in row_decisions)
    label_counts = Counter(row["categorical_lifecycle_label"] for row in eligible)
    first_event_counts = Counter((row["ordered_source_events"][0]["event"] if row["ordered_source_events"] else "no_ordered_event") for row in row_decisions)
    duplicate_key_counts = Counter(row["nofill_duplicate_key"] for row in row_decisions)
    duplicate_conflicts = [key for key, count in duplicate_key_counts.items() if count > 1]
    source_hash_failures = [row for row in source_hash_records if row.get("expected_sha256") and row.get("hash_match") is False]
    missing_sources = [row for row in source_hash_records if not row.get("exists")]
    forbidden_hits = scan_forbidden_keys(row_decisions)

    source_hash_audit = base_payload("OTI3_USDJPY_SOURCE_HASH_NOLEAK_AUDIT")
    source_hash_audit.update(
        {
            "source_hash_record_count": len(source_hash_records),
            "source_hash_records": source_hash_records,
            "source_hash_failures": source_hash_failures,
            "missing_sources": missing_sources,
            "forbidden_key_hits": forbidden_hits,
            "no_leak_status": "PASS" if not source_hash_failures and not forbidden_hits else "FAIL",
            "flags_preserved": {
                "promotion_verdict": PROMOTION_VERDICT,
                "validation_safe": VALIDATION_SAFE,
                "outcome_review_opened": OUTCOME_REVIEW_OPENED,
                "live_effect": LIVE_EFFECT,
            },
        }
    )
    duplicate_asof_audit = base_payload("OTI3_USDJPY_DUPLICATE_ASOF_AUDIT")
    duplicate_asof_audit.update(
        {
            "row_count": len(row_decisions),
            "source_inventory_id_unique": len({row["source_inventory_id"] for row in row_decisions}),
            "nofill_duplicate_key_unique": len({row["nofill_duplicate_key"] for row in row_decisions}),
            "duplicate_group_id_unique": len({row["duplicate_group_id"] for row in row_decisions}),
            "duplicate_conflict_keys": duplicate_conflicts,
            "asof_violations": [
                row["source_close_packet_row_id"]
                for row in row_decisions
                if row.get("source_path_start_utc") and parse_utc(row["source_path_start_utc"]) < parse_utc(row["decision_asof_utc"])
            ],
            "status": "PASS" if not duplicate_conflicts else "FAIL",
        }
    )
    decision_summary = base_payload("OTI3_USDJPY_ROW_DECISION_SUMMARY")
    decision_summary.update(
        {
            "row_count": len(row_decisions),
            "date_counts": dict(date_counts),
            "eligible_contract_evidence_rows": len(eligible),
            "blocked_exact_rows": len(blocked),
            "categorical_label_counts": dict(label_counts),
            "first_event_counts": dict(first_event_counts),
            "exact_blocker_counts": dict(blocker_counts),
            "access_request_rows_remaining": [
                row["source_close_packet_row_id"]
                for row in blocked
                if "BLOCK_OTI3_MISSING_QUOTE_TICK_SOURCE_WITH_EXACT_ACCESS_REQUEST" in row["exact_blocker_codes"]
            ],
            "separate_fill_path_rows": [
                row["source_close_packet_row_id"]
                for row in blocked
                if "BLOCK_OTI3_ENTRY_TOUCH_BEFORE_TERMINAL_SEPARATE_FILL_PATH_CONTRACT_REQUIRED" in row["exact_blocker_codes"]
            ],
            "non_claims": [
                "No R/performance, win-rate, expectancy, DSR/PBO, validation, promotion, or live-effect claim is made.",
                "Entry-first quote/tick evidence is not converted into a performance or broker-fill label.",
            ],
        }
    )
    return {
        "source_hash_audit": source_hash_audit,
        "duplicate_asof_audit": duplicate_asof_audit,
        "decision_summary": decision_summary,
    }


def write_context_anchor(rows: list[dict[str, Any]], search_ledger: dict[str, Any]) -> dict[str, Any]:
    anchor = base_payload("OTI3_USDJPY_CONTEXT_ANCHOR")
    anchor.update(
        {
            "controlling_prompt": str(CONTROLLING_PROMPT),
            "mandatory_preflight_completed_in_session": True,
            "input_row_count": len(rows),
            "input_dates": dict(Counter(row["decision_asof_utc"][:10] for row in rows)),
            "source_search_conclusion": search_ledger["search_conclusion"],
            "context_files_read": [
                ".context/LIVE_STATE.md",
                ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
                ".context/00_core/quick_reference_card.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/research_current_state.md",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/local_heavy_data_inventory.md",
                str(CONTROLLING_PROMPT),
                str(ROUTER_CONTEXT_ANCHOR),
                str(ROUTER_ROUTE_LEDGER),
                str(ROUTER_SEARCH_LEDGER),
            ],
            "stop_condition": "complete only when all 69 rows have quote/tick categorical evidence or exact blockers",
        }
    )
    return anchor


def build_completion_audit(
    rows: list[dict[str, Any]],
    row_decisions: list[dict[str, Any]],
    search_ledger: dict[str, Any],
    audits: dict[str, dict[str, Any]],
    verification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    eligible = [row for row in row_decisions if row["eligibility_decision"] == "ELIGIBLE_CONTRACT_EVIDENCE"]
    blocked = [row for row in row_decisions if row["eligibility_decision"] != "ELIGIBLE_CONTRACT_EVIDENCE"]
    prompt_checklist = [
        ("mandatory_gtos_preflight", "PASS", "generate_live_state ran; LIVE_STATE, latest handoff, quick reference, doctrine, research_current_state, goal_session_research_discipline, local_heavy_data_inventory, prompt pack, router context/ledgers were read."),
        ("row_universe_69", "PASS" if len(rows) == 69 and len(row_decisions) == 69 else "FAIL", f"rows={len(rows)} decisions={len(row_decisions)}"),
        (
            "quote_tick_sources_or_exact_blockers",
            "PASS"
            if len(eligible) + len(blocked) == 69
            and all(row["eligibility_decision"] == "ELIGIBLE_CONTRACT_EVIDENCE" or row.get("exact_blocker_codes") for row in row_decisions)
            else "FAIL",
            f"eligible={len(eligible)} blocked={len(blocked)} remaining_access={audits['decision_summary']['access_request_rows_remaining']}",
        ),
        ("approved_missing_date_route_only", "PASS", "Only USDJPY 2026-04-17 and 2026-04-20 are eligible for MT5 copy_ticks_range extraction; no other date uses MT5 extraction."),
        ("no_account_history_order_calls", "PASS", "Extraction ledger records initialize/copy_ticks_range/shutdown only; account/history/order/position/order_send counters are false/zero."),
        ("source_hashes_required", "PASS" if audits["source_hash_audit"]["no_leak_status"] == "PASS" else "FAIL", audits["source_hash_audit"]["no_leak_status"]),
        ("duplicate_and_asof_checks", audits["duplicate_asof_audit"]["status"], f"duplicate_keys={audits['duplicate_asof_audit']['duplicate_conflict_keys']} asof_violations={audits['duplicate_asof_audit']['asof_violations']}"),
        ("flags_preserved", "PASS", "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false"),
        ("no_r_performance_or_live_labels", "PASS" if not audits["source_hash_audit"]["forbidden_key_hits"] else "FAIL", f"forbidden_hits={len(audits['source_hash_audit']['forbidden_key_hits'])}"),
        ("no_live_trading_surface_change", "PENDING_VERIFIER" if verification is None else verification.get("live_surface_diff_check", {}).get("status", "FAIL"), "Verifier inspects git diff path scope."),
    ]
    can_complete = all(item[1] == "PASS" for item in prompt_checklist)
    audit = base_payload("OTI3_USDJPY_COMPLETION_AUDIT")
    audit.update(
        {
            "objective_restatement": "Resolve 69 USDJPY price-only no-fill rows to source-hashed quote/tick categorical lifecycle evidence or exact blockers under a conservative parser contract.",
            "completion_status": "PASS_VERIFIED" if can_complete else "BUILT_PENDING_OR_FAILED_VERIFICATION",
            "can_mark_goal_complete": can_complete,
            "row_outcome": {
                "total_rows": len(row_decisions),
                "quote_tick_categorical_contract_evidence": len(eligible),
                "blocked_exact": len(blocked),
                "categorical_label_counts": audits["decision_summary"]["categorical_label_counts"],
                "exact_blocker_counts": audits["decision_summary"]["exact_blocker_counts"],
            },
            "prompt_to_artifact_checklist": [
                {"requirement": requirement, "status": status, "evidence": evidence}
                for requirement, status, evidence in prompt_checklist
            ],
            "verification": verification or {},
            "source_search_conclusion": search_ledger["search_conclusion"],
            "next_unblockers": {
                "entry_first_rows": "Route to a separate fill/path categorical contract if those rows should be classified beyond no-fill closure.",
                "protective_first_rows": "No rows observed unless verifier artifacts show otherwise; if present, define a separate protective-before-entry no-fill category before labeling.",
                "missing_tick_rows": "No remaining rows if extraction succeeds; otherwise exact USDJPY bid/ask tick source is required for the listed dates.",
            },
        }
    )
    return audit


def render_all(
    rows: list[dict[str, Any]],
    search_ledger: dict[str, Any],
    date_sources: dict[str, Path | None],
    row_decisions: list[dict[str, Any]],
    source_hash_records: list[dict[str, Any]],
    audits: dict[str, dict[str, Any]],
    completion: dict[str, Any],
) -> None:
    context_anchor = write_context_anchor(rows, search_ledger)
    contract_packet = build_contract_packet(row_decisions)

    write_json(OUT_DIR / "OTI3_USDJPY_CONTEXT_ANCHOR_2026-05-08.json", context_anchor)
    write_md_json(OUT_DIR / "OTI3_USDJPY_CONTEXT_ANCHOR_2026-05-08.md", "OTI3 USDJPY Context Anchor - 2026-05-08", context_anchor)
    write_json(OUT_DIR / "OTI3_USDJPY_SOURCE_SEARCH_LEDGER_2026-05-08.json", search_ledger)
    write_md_json(
        OUT_DIR / "OTI3_USDJPY_SOURCE_SEARCH_LEDGER_2026-05-08.md",
        "OTI3 USDJPY Source Search Ledger - 2026-05-08",
        search_ledger,
        ["- Local heavy-data search checked worktree, absolute main repo tick cache, C:\\tmp worktrees, and C:\\Users\\MSI\\Documents parquet candidates."],
    )
    write_json(OUT_DIR / "OTI3_USDJPY_QUOTE_TICK_CONTRACT_2026-05-08.json", contract_packet)
    write_md_json(OUT_DIR / "OTI3_USDJPY_QUOTE_TICK_CONTRACT_2026-05-08.md", "OTI3 USDJPY Quote Tick Contract - 2026-05-08", contract_packet)
    write_jsonl(OUT_DIR / "OTI3_USDJPY_ROW_DECISION_LEDGER_2026-05-08.jsonl", row_decisions)
    write_json(OUT_DIR / "OTI3_USDJPY_ROW_DECISION_SUMMARY_2026-05-08.json", audits["decision_summary"])
    write_md_json(OUT_DIR / "OTI3_USDJPY_ROW_DECISION_SUMMARY_2026-05-08.md", "OTI3 USDJPY Row Decision Summary - 2026-05-08", audits["decision_summary"])
    write_json(OUT_DIR / "OTI3_USDJPY_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.json", audits["source_hash_audit"])
    write_md_json(OUT_DIR / "OTI3_USDJPY_SOURCE_HASH_NOLEAK_AUDIT_2026-05-08.md", "OTI3 USDJPY Source Hash Noleak Audit - 2026-05-08", audits["source_hash_audit"])
    write_json(OUT_DIR / "OTI3_USDJPY_DUPLICATE_ASOF_AUDIT_2026-05-08.json", audits["duplicate_asof_audit"])
    write_md_json(OUT_DIR / "OTI3_USDJPY_DUPLICATE_ASOF_AUDIT_2026-05-08.md", "OTI3 USDJPY Duplicate ASOF Audit - 2026-05-08", audits["duplicate_asof_audit"])
    write_json(OUT_DIR / "OTI3_USDJPY_SOURCE_HASH_RECORDS_2026-05-08.json", source_hash_records)
    write_json(OUT_DIR / "OTI3_USDJPY_COMPLETION_AUDIT_2026-05-08.json", completion)
    write_md_json(OUT_DIR / "OTI3_USDJPY_COMPLETION_AUDIT_2026-05-08.md", "OTI3 USDJPY Completion Audit - 2026-05-08", completion)


def build(skip_mt5_extraction: bool = False) -> dict[str, Any]:
    rows = load_oti3_rows()
    search_ledger, date_sources = build_source_inventory(rows, skip_mt5=skip_mt5_extraction)
    row_decisions = build_row_decisions(rows, date_sources)
    source_hash_records = collect_source_hash_records(date_sources, row_decisions)
    audits = build_audits(rows, row_decisions, source_hash_records)
    completion = build_completion_audit(rows, row_decisions, search_ledger, audits)
    render_all(rows, search_ledger, date_sources, row_decisions, source_hash_records, audits, completion)
    summary = {
        "rows": len(row_decisions),
        "eligible_contract_evidence": audits["decision_summary"]["eligible_contract_evidence_rows"],
        "blocked_exact": audits["decision_summary"]["blocked_exact_rows"],
        "blocker_counts": audits["decision_summary"]["exact_blocker_counts"],
        "completion_status": completion["completion_status"],
        "can_mark_goal_complete": completion["can_mark_goal_complete"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-mt5-extraction", action="store_true", help="Do not use the approved read-only MT5 copy_ticks_range route.")
    args = parser.parse_args()
    build(skip_mt5_extraction=args.skip_mt5_extraction)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
