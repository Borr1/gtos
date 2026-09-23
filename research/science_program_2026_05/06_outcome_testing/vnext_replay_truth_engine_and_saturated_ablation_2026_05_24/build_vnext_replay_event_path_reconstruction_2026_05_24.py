"""Build Stage 04 replay event and path-reconstruction ledgers.

This builder consumes source-safe local shadow/path/lifecycle logs plus the
preregistered data inventory. It preserves every material source event row in
the event ledger, then deduplicates identical trade geometry only for path
simulation work so repeated source rows do not multiply the same replay.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DATA_COVERAGE_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_DATA_COVERAGE_LEDGER_2026-05-24.jsonl"
DECISION_TRACE_PATH = ROUTE_DIR / "VNEXT_REPLAY_DECISION_TRACE_LEDGER_2026-05-24.jsonl"
EVENT_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_EVENT_LEDGER_2026-05-24.jsonl"
PATH_OUTCOME_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_PATH_OUTCOME_LEDGER_2026-05-24.jsonl"
SUMMARY_PATH = ROUTE_DIR / "VNEXT_REPLAY_EVENT_PATH_RECONSTRUCTION_SUMMARY_2026-05-24.json"
SOURCE_GAP_LEDGER_PATH = ROUTE_DIR / "VNEXT_REPLAY_SOURCE_GAP_LEDGER_2026-05-24.jsonl"
OUTPUT_MANIFEST_PATH = ROUTE_DIR / "VNEXT_REPLAY_OUTPUT_MANIFEST_2026-05-24.json"

SOURCE_LOGS = [
    ("candidate_features", REPO_ROOT / "shadow_logs/candidate_features_log.jsonl"),
    ("candidate_path_follow", REPO_ROOT / "shadow_logs/candidate_path_follow.jsonl"),
    ("candidate_path_contract_audit", REPO_ROOT / "shadow_logs/candidate_path_contract_audit.jsonl"),
    ("candidate_ltf_path_order", REPO_ROOT / "shadow_logs/candidate_ltf_path_order.jsonl"),
    ("pending_limit_lifecycle", REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl"),
    ("trade_index_lifecycle_audit", REPO_ROOT / "shadow_logs/trade_index_lifecycle_audit.jsonl"),
]

OHLC_ROOTS = [
    REPO_ROOT / "data/mt5_research_exports",
    REPO_ROOT / "data/historical_2026",
    REPO_ROOT / "data/sierra_ohlcv_roots",
]
TICK_ROOT = REPO_ROOT / "data/ticks"

TIMEFRAMES = ["M1", "M5", "M15"]
SOURCE_GAP_STAGE = "STAGE_04_EVENT_AND_PATH_RECONSTRUCTION"
REQUIRED_REPLAY_MODES = {
    "current_config_shadow",
    "hypothetical_activated_vnext",
    "bar_close_m15",
    "m1_path_aware",
    "m5_path_aware",
    "tick_or_sierra_path_aware",
    "ohlc_only_proxy",
    "missing_source",
}

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover - environment-dependent fallback
    pd = None


@dataclass(frozen=True)
class Bar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None


SHA_CACHE: dict[Path, str] = {}
INVENTORY_BY_PATH: dict[str, dict[str, Any]] | None = None
OHLC_FILE_INDEX: dict[tuple[str, str], list[Path]] | None = None
OHLC_BAR_CACHE: dict[Path, tuple[list[datetime], list[Bar]]] = {}
TICK_CACHE: dict[Path, Any] = {}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def sha256_file(path: Path) -> str:
    if path not in SHA_CACHE:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        SHA_CACHE[path] = digest.hexdigest()
    return SHA_CACHE[path]


def line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(chunk.count(b"\n") for chunk in iter(lambda: handle.read(1024 * 1024), b""))


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                yield line_no, json.loads(line)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            try:
                dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def dt_s(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fnum(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result) or math.isinf(result):
        return None
    return result


def stable_hash(payload: Any, length: int = 16) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:length]


def load_inventory() -> dict[str, dict[str, Any]]:
    global INVENTORY_BY_PATH
    if INVENTORY_BY_PATH is not None:
        return INVENTORY_BY_PATH
    by_path: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(DATA_COVERAGE_LEDGER_PATH):
        path = row.get("path") or row.get("relative_path") or row.get("source_path")
        if path:
            by_path[str(path).replace("\\", "/")] = row
    INVENTORY_BY_PATH = by_path
    return by_path


def inventory_record_for(path: Path) -> dict[str, Any] | None:
    inventory = load_inventory()
    key = rel(path)
    return inventory.get(key) or inventory.get(path.as_posix())


def file_hash_from_inventory(path: Path) -> str:
    record = inventory_record_for(path) or {}
    return str(record.get("sha256") or record.get("hash_sha256") or sha256_file(path))


def source_use_status(row: dict[str, Any]) -> str:
    no_leak = str(row.get("no_leak_status") or "")
    if no_leak.startswith("AS_OF"):
        return "AS_OF_SOURCE_ROW"
    if no_leak.startswith("POST_DECISION"):
        return "POST_DECISION_REPLAY_OR_AUDIT_SOURCE"
    if row.get("schema_version") in {"candidate_path_follow_v1", "candidate_path_contract_audit_v1"}:
        return "POST_DECISION_PATH_SOURCE"
    return "SOURCE_USE_REQUIRES_ROW_CONTEXT"


def trade_params(row: dict[str, Any]) -> dict[str, Any]:
    params = row.get("trade_parameters")
    return params if isinstance(params, dict) else {}


def extract_geometry(row: dict[str, Any]) -> dict[str, Any]:
    params = trade_params(row)
    side = row.get("side") or row.get("direction") or params.get("direction")
    entry = fnum(params.get("entry_price", row.get("entry_price")))
    stop = fnum(params.get("stop_loss", row.get("stop_loss")))
    target = fnum(params.get("take_profit_1", row.get("take_profit_1")))
    if not side and None not in (entry, stop, target):
        if stop < entry < target:
            side = "LONG"
        elif target < entry < stop:
            side = "SHORT"
    return {
        "side": str(side).upper() if side else None,
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit_1": target,
        "risk_reward_ratio": fnum(params.get("risk_reward_ratio", row.get("risk_reward_ratio"))),
    }


def has_geometry(geometry: dict[str, Any]) -> bool:
    return all(geometry.get(key) is not None for key in ["side", "entry_price", "stop_loss", "take_profit_1"])


def event_time(row: dict[str, Any]) -> datetime | None:
    for key in [
        "decision_time_utc",
        "timestamp_utc",
        "asof_latest_candle_utc",
        "checked_candle_time_utc",
        "created_at_utc",
    ]:
        dt = parse_dt(row.get(key))
        if dt:
            return dt
    return None


def window_for(row: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    start = parse_dt(row.get("window_start_utc")) or parse_dt(row.get("decision_time_utc")) or event_time(row)
    end = (
        parse_dt(row.get("window_end_utc"))
        or parse_dt(row.get("asof_latest_candle_utc"))
        or parse_dt(row.get("asof_cutoff_utc"))
        or parse_dt(row.get("latest_m15_time_utc"))
        or parse_dt(row.get("checked_candle_time_utc"))
    )
    if start and (end is None or end <= start):
        end = start + timedelta(hours=2)
    return start, end


def event_row(
    source_name: str,
    source_path: Path,
    line_no: int,
    row: dict[str, Any],
) -> dict[str, Any]:
    geometry = extract_geometry(row)
    start, end = window_for(row)
    candidate_id = row.get("candidate_id") or row.get("evaluation_id")
    trade_id = row.get("trade_id") or row.get("trade_record_trade_id") or row.get("limit_intent_trade_id")
    symbol = row.get("symbol") or row.get("broker_symbol") or row.get("source_symbol")
    source_symbol = row.get("source_symbol") or row.get("broker_symbol")
    duplicate_group_id = (
        candidate_id
        or trade_id
        or "|".join(str(part) for part in [symbol, dt_s(start), source_name] if part)
    )
    source_row_key = row.get("row_key") or row.get("row_id") or row.get("candidate_id") or row.get("trade_id")
    source_rel = rel(source_path)
    forbidden_non_null = [
        key
        for key in ["actual_r", "synthetic_path_r", "broker_actual_r", "outcome_r", "trade_result"]
        if row.get(key) not in (None, "")
    ]
    return {
        "schema_version": "vnext_replay_event_v1",
        "stage_id": SOURCE_GAP_STAGE,
        "event_id": "evt_" + stable_hash([source_name, source_rel, line_no, duplicate_group_id]),
        "source_event_type": source_name,
        "source_schema_version": row.get("schema_version"),
        "source_path": source_rel,
        "source_line_no": line_no,
        "source_sha256": file_hash_from_inventory(source_path),
        "source_row_key": source_row_key,
        "source_use_status": source_use_status(row),
        "no_leak_status": row.get("no_leak_status"),
        "evidence_class": row.get("evidence_class"),
        "promotion_verdict": row.get("promotion_verdict"),
        "candidate_id": candidate_id,
        "trade_id": trade_id,
        "duplicate_group_id": duplicate_group_id,
        "symbol": symbol,
        "source_symbol": source_symbol,
        "broker_symbol": row.get("broker_symbol"),
        "timeframe": row.get("market_timeframe") or row.get("source_timeframe"),
        "session": row.get("session") or row.get("session_tag") or row.get("kill_zone"),
        "kill_zone": row.get("kill_zone"),
        "framework": row.get("framework"),
        "decision": row.get("decision") or row.get("ai_decision"),
        "side": geometry.get("side"),
        "decision_time_utc": dt_s(event_time(row)),
        "window_start_utc": dt_s(start),
        "window_end_utc": dt_s(end),
        "entry_price": geometry.get("entry_price"),
        "stop_loss": geometry.get("stop_loss"),
        "take_profit_1": geometry.get("take_profit_1"),
        "risk_reward_ratio": geometry.get("risk_reward_ratio"),
        "geometry_available": has_geometry(geometry),
        "duplicate_policy": "preserve_source_rows; use duplicate_group_id for replay denominator",
        "forbidden_outcome_fields_non_null": forbidden_non_null,
        "broker_operation_fields": {
            "order_calls": row.get("order_calls"),
            "ai_calls": row.get("ai_calls"),
            "paid_data_calls": row.get("paid_data_calls"),
            "paid_fetch_attempted": row.get("paid_fetch_attempted"),
            "no_execution": row.get("no_execution"),
        },
    }


def build_events() -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    originals_by_event: dict[str, list[dict[str, Any]]] = {}
    geometry_by_group: dict[str, dict[str, Any]] = {}
    for source_name, source_path in SOURCE_LOGS:
        if not source_path.exists():
            continue
        for line_no, source_row in iter_jsonl(source_path):
            event = event_row(source_name, source_path, line_no, source_row)
            rows.append(event)
            originals_by_event[event["event_id"]] = [source_row]
            if event["geometry_available"]:
                geometry_by_group.setdefault(event["duplicate_group_id"], event)
    rows.sort(key=lambda item: (str(item.get("decision_time_utc")), str(item.get("source_event_type")), str(item.get("event_id"))))
    return rows, originals_by_event, geometry_by_group


def split_symbol_timeframe(path: Path) -> tuple[str, str] | None:
    stem = path.stem
    for timeframe in ["M15", "M5", "M1", "H1", "H4", "D1"]:
        suffix = "_" + timeframe
        if stem.endswith(suffix):
            return stem[: -len(suffix)], timeframe
    return None


def build_ohlc_file_index() -> dict[tuple[str, str], list[Path]]:
    global OHLC_FILE_INDEX
    if OHLC_FILE_INDEX is not None:
        return OHLC_FILE_INDEX
    index: dict[tuple[str, str], list[Path]] = defaultdict(list)
    for root in OHLC_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.csv"):
            parsed = split_symbol_timeframe(path)
            if parsed:
                index[parsed].append(path)
    for key in list(index):
        index[key].sort(key=lambda path: (root_priority(path), rel(path)))
    OHLC_FILE_INDEX = dict(index)
    return OHLC_FILE_INDEX


def root_priority(path: Path) -> int:
    path_text = rel(path)
    if "data/mt5_research_exports/" in path_text:
        return 0
    if "data/historical_2026/" in path_text:
        return 1
    if "data/sierra_ohlcv_roots/" in path_text:
        return 2
    return 9


def load_ohlc_bars(path: Path) -> tuple[list[datetime], list[Bar]]:
    if path in OHLC_BAR_CACHE:
        return OHLC_BAR_CACHE[path]
    bars: list[Bar] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            dt = parse_dt(row.get("time") or row.get("timestamp") or row.get("datetime"))
            if dt is None:
                continue
            open_ = fnum(row.get("open"))
            high = fnum(row.get("high"))
            low = fnum(row.get("low"))
            close = fnum(row.get("close"))
            if None in (open_, high, low, close):
                continue
            bars.append(Bar(dt, open_, high, low, close, fnum(row.get("volume"))))
    bars.sort(key=lambda bar: bar.time)
    times = [bar.time for bar in bars]
    OHLC_BAR_CACHE[path] = (times, bars)
    return times, bars


def symbol_aliases(symbol: str | None, source_symbol: str | None = None, broker_symbol: str | None = None) -> list[str]:
    aliases: list[str] = []
    for value in [symbol, source_symbol, broker_symbol]:
        if value and value not in aliases:
            aliases.append(str(value))
    extra = {
        "US30": ["US30_cash", "US30_CASH"],
        "US30_cash": ["US30", "US30_CASH"],
        "NAS100": ["NDX100", "NAS100_NQ", "NAS100_MNQ"],
        "NDX100": ["NAS100"],
        "XAUUSD": ["XAUUSD_GC", "GCM26-COMEX"],
        "XAGUSD": ["XAGUSD_SI", "SIM26-COMEX"],
        "USDJPY": ["USDJPY_6J"],
        "GBPUSD": ["GBPUSD_6B"],
    }
    for base in list(aliases):
        for alias in extra.get(base, []):
            if alias not in aliases:
                aliases.append(alias)
    return aliases


def find_ohlc_bars(
    event: dict[str, Any],
    timeframe: str,
) -> tuple[list[Bar], Path | None, list[str]]:
    start = parse_dt(event.get("window_start_utc"))
    end = parse_dt(event.get("window_end_utc"))
    searched: list[str] = []
    if start is None or end is None:
        return [], None, searched
    index = build_ohlc_file_index()
    for alias in symbol_aliases(event.get("symbol"), event.get("source_symbol"), event.get("broker_symbol")):
        for path in index.get((alias, timeframe), []):
            searched.append(rel(path))
            times, bars = load_ohlc_bars(path)
            left = bisect.bisect_left(times, start)
            right = bisect.bisect_right(times, end)
            selected = bars[left:right]
            if selected:
                return selected, path, searched
    return [], None, searched


def touches(bar: Bar, level: float) -> bool:
    return bar.low <= level <= bar.high


def first_index(indices: Iterable[int]) -> int | None:
    for index in indices:
        return index
    return None


def compute_path_from_bars(event: dict[str, Any], bars: list[Bar], mode: str, source_path: Path) -> dict[str, Any]:
    side = str(event.get("side") or "").upper()
    entry = fnum(event.get("entry_price"))
    stop = fnum(event.get("stop_loss"))
    target = fnum(event.get("take_profit_1"))
    risk = abs(entry - stop) if entry is not None and stop is not None else None
    entry_idx = first_index(index for index, bar in enumerate(bars) if entry is not None and touches(bar, entry))
    stop_idx = None
    target_idx = None
    if entry_idx is not None:
        for index in range(entry_idx, len(bars)):
            bar = bars[index]
            if side == "LONG":
                stop_hit = stop is not None and bar.low <= stop
                target_hit = target is not None and bar.high >= target
            else:
                stop_hit = stop is not None and bar.high >= stop
                target_hit = target is not None and bar.low <= target
            if stop_idx is None and stop_hit:
                stop_idx = index
            if target_idx is None and target_hit:
                target_idx = index
            if stop_idx is not None and target_idx is not None:
                break
    if entry_idx is None:
        terminal_order = "NO_ENTRY_TOUCH"
    elif stop_idx is None and target_idx is None:
        terminal_order = "ENTRY_TOUCHED_TIMEOUT_OR_NO_TERMINAL"
    elif stop_idx is not None and target_idx is not None and stop_idx == target_idx:
        terminal_order = "SAME_BAR_AMBIGUOUS_STOP_AND_TARGET"
    elif target_idx is not None and (stop_idx is None or target_idx < stop_idx):
        terminal_order = "TARGET_FIRST"
    else:
        terminal_order = "STOP_FIRST"
    mfe_r = None
    mae_r = None
    if entry_idx is not None and risk and risk > 0:
        post_bars = bars[entry_idx:]
        if side == "LONG":
            mfe_r = max((bar.high - entry) / risk for bar in post_bars)
            mae_r = min((bar.low - entry) / risk for bar in post_bars)
        else:
            mfe_r = max((entry - bar.low) / risk for bar in post_bars)
            mae_r = min((entry - bar.high) / risk for bar in post_bars)
    return {
        "path_source_status": "SIMULATED_FROM_LOCAL_OHLC",
        "source_path": rel(source_path),
        "source_sha256": file_hash_from_inventory(source_path),
        "bar_count": len(bars),
        "first_bar_utc": dt_s(bars[0].time) if bars else None,
        "last_bar_utc": dt_s(bars[-1].time) if bars else None,
        "entry_touched": entry_idx is not None,
        "entry_first_touch_utc": dt_s(bars[entry_idx].time) if entry_idx is not None else None,
        "sl_first_touch_utc": dt_s(bars[stop_idx].time) if stop_idx is not None else None,
        "tp1_first_touch_utc": dt_s(bars[target_idx].time) if target_idx is not None else None,
        "terminal_order": terminal_order,
        "same_bar_ambiguity": terminal_order == "SAME_BAR_AMBIGUOUS_STOP_AND_TARGET",
        "mfe_r": mfe_r,
        "mae_r": mae_r,
        "confidence": "lower_timeframe_ohlc" if mode in {"m1_path_aware", "m5_path_aware"} else "m15_ohlc_path",
    }


def base_path_row(event: dict[str, Any], mode: str, source_evidence_type: str) -> dict[str, Any]:
    return {
        "schema_version": "vnext_replay_path_outcome_v1",
        "stage_id": SOURCE_GAP_STAGE,
        "path_row_id": "path_" + stable_hash([event.get("event_id"), mode, source_evidence_type]),
        "event_id": event.get("event_id"),
        "duplicate_group_id": event.get("duplicate_group_id"),
        "candidate_id": event.get("candidate_id"),
        "trade_id": event.get("trade_id"),
        "symbol": event.get("symbol"),
        "source_symbol": event.get("source_symbol"),
        "broker_symbol": event.get("broker_symbol"),
        "side": event.get("side"),
        "framework": event.get("framework"),
        "session": event.get("session"),
        "decision_time_utc": event.get("decision_time_utc"),
        "window_start_utc": event.get("window_start_utc"),
        "window_end_utc": event.get("window_end_utc"),
        "entry_price": event.get("entry_price"),
        "stop_loss": event.get("stop_loss"),
        "take_profit_1": event.get("take_profit_1"),
        "replay_mode": mode,
        "source_evidence_type": source_evidence_type,
    }


def missing_path_row(
    event: dict[str, Any],
    mode: str,
    source_evidence_type: str,
    reason: str,
    searched_paths: list[str],
) -> dict[str, Any]:
    row = base_path_row(event, mode, source_evidence_type)
    row.update(
        {
            "path_source_status": "MISSING_SOURCE",
            "terminal_order": "MISSING_SOURCE",
            "entry_touched": None,
            "same_bar_ambiguity": None,
            "source_gap_class": reason,
            "searched_paths": searched_paths,
            "missing_fields": ["source_bars_or_ticks_for_window"],
            "confidence": "missing_source",
        }
    )
    return row


def ohlc_path_rows_for_job(event: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for timeframe, mode in [("M1", "m1_path_aware"), ("M5", "m5_path_aware"), ("M15", "bar_close_m15")]:
        bars, source_path, searched = find_ohlc_bars(event, timeframe)
        if source_path and bars:
            row = base_path_row(event, mode, f"local_{timeframe.lower()}_ohlc_reconstruction")
            row.update(compute_path_from_bars(event, bars, mode, source_path))
            rows.append(row)
        else:
            rows.append(
                missing_path_row(
                    event,
                    "missing_source",
                    f"local_{timeframe.lower()}_ohlc_reconstruction",
                    f"{timeframe}_OHLC_WINDOW_NOT_FOUND",
                    searched,
                )
            )
    m15_rows = [row for row in rows if row.get("replay_mode") == "bar_close_m15" and row.get("path_source_status") != "MISSING_SOURCE"]
    if m15_rows:
        proxy = dict(m15_rows[0])
        proxy["path_row_id"] = "path_" + stable_hash([event.get("event_id"), "ohlc_only_proxy"])
        proxy["replay_mode"] = "ohlc_only_proxy"
        proxy["source_evidence_type"] = "m15_ohlc_proxy_from_best_available_bar_data"
        proxy["confidence"] = "ohlc_only_proxy"
        rows.append(proxy)
    else:
        rows.append(
            missing_path_row(
                event,
                "missing_source",
                "ohlc_only_proxy",
                "OHLC_PROXY_WINDOW_NOT_FOUND",
                [],
            )
        )
    return rows


def tick_file_candidates(event: dict[str, Any]) -> list[Path]:
    start = parse_dt(event.get("window_start_utc"))
    if start is None:
        return []
    date = start.date().isoformat()
    candidates = []
    for alias in symbol_aliases(event.get("symbol"), event.get("source_symbol"), event.get("broker_symbol")):
        path = TICK_ROOT / alias / f"{date}.parquet"
        if path.exists():
            candidates.append(path)
    return candidates


def load_tick_frame(path: Path) -> Any:
    if path in TICK_CACHE:
        return TICK_CACHE[path]
    if pd is None:
        return None
    frame = pd.read_parquet(path)
    if "ts_utc" in frame.columns:
        frame = frame.sort_values("ts_utc")
    TICK_CACHE[path] = frame
    return frame


def compute_path_from_ticks(event: dict[str, Any], path: Path) -> dict[str, Any] | None:
    if pd is None:
        return None
    frame = load_tick_frame(path)
    if frame is None or frame.empty or "ts_utc" not in frame.columns:
        return None
    start = parse_dt(event.get("window_start_utc"))
    end = parse_dt(event.get("window_end_utc"))
    entry = fnum(event.get("entry_price"))
    stop = fnum(event.get("stop_loss"))
    target = fnum(event.get("take_profit_1"))
    side = str(event.get("side") or "").upper()
    if None in (start, end, entry, stop, target) or side not in {"LONG", "SHORT"}:
        return None
    ts = frame["ts_utc"]
    left = ts.searchsorted(start, side="left")
    right = ts.searchsorted(end, side="right")
    window = frame.iloc[left:right]
    if window.empty:
        return None
    bid = window["bid"] if "bid" in window.columns else window.get("last")
    ask = window["ask"] if "ask" in window.columns else window.get("last")
    if bid is None or ask is None:
        return None
    if side == "LONG":
        entry_mask = ask <= entry
        stop_mask = bid <= stop
        target_mask = bid >= target
    else:
        entry_mask = bid >= entry
        stop_mask = ask >= stop
        target_mask = ask <= target
    entry_positions = window.index[entry_mask].tolist()
    entry_pos = entry_positions[0] if entry_positions else None
    stop_pos = None
    target_pos = None
    if entry_pos is not None:
        post = window.loc[entry_pos:]
        stop_hits = post.index[stop_mask.loc[entry_pos:]].tolist()
        target_hits = post.index[target_mask.loc[entry_pos:]].tolist()
        stop_pos = stop_hits[0] if stop_hits else None
        target_pos = target_hits[0] if target_hits else None
    if entry_pos is None:
        terminal_order = "NO_ENTRY_TOUCH"
    elif stop_pos is None and target_pos is None:
        terminal_order = "ENTRY_TOUCHED_TIMEOUT_OR_NO_TERMINAL"
    elif stop_pos is not None and target_pos is not None and stop_pos == target_pos:
        terminal_order = "SAME_TICK_AMBIGUOUS_STOP_AND_TARGET"
    elif target_pos is not None and (stop_pos is None or target_pos < stop_pos):
        terminal_order = "TARGET_FIRST"
    else:
        terminal_order = "STOP_FIRST"
    risk = abs(entry - stop) if entry is not None and stop is not None else None
    mfe_r = None
    mae_r = None
    if entry_pos is not None and risk and risk > 0:
        post = window.loc[entry_pos:]
        if side == "LONG":
            mfe_r = float(((bid.loc[entry_pos:].max() - entry) / risk))
            mae_r = float(((bid.loc[entry_pos:].min() - entry) / risk))
        else:
            mfe_r = float(((entry - ask.loc[entry_pos:].min()) / risk))
            mae_r = float(((entry - ask.loc[entry_pos:].max()) / risk))
    return {
        "path_source_status": "SIMULATED_FROM_LOCAL_TICKS",
        "source_path": rel(path),
        "source_sha256": file_hash_from_inventory(path),
        "tick_count": int(len(window)),
        "first_tick_utc": dt_s(parse_dt(window.iloc[0]["ts_utc"])),
        "last_tick_utc": dt_s(parse_dt(window.iloc[-1]["ts_utc"])),
        "quote_rule": "LONG entry uses ask<=entry and exits use bid; SHORT entry uses bid>=entry and exits use ask",
        "entry_touched": entry_pos is not None,
        "entry_first_touch_utc": dt_s(parse_dt(window.loc[entry_pos]["ts_utc"])) if entry_pos is not None else None,
        "sl_first_touch_utc": dt_s(parse_dt(window.loc[stop_pos]["ts_utc"])) if stop_pos is not None else None,
        "tp1_first_touch_utc": dt_s(parse_dt(window.loc[target_pos]["ts_utc"])) if target_pos is not None else None,
        "terminal_order": terminal_order,
        "same_bar_ambiguity": terminal_order == "SAME_TICK_AMBIGUOUS_STOP_AND_TARGET",
        "mfe_r": mfe_r,
        "mae_r": mae_r,
        "confidence": "tick_quote_path",
    }


def tick_path_row_for_job(event: dict[str, Any]) -> dict[str, Any]:
    searched = [rel(path) for path in tick_file_candidates(event)]
    for path in tick_file_candidates(event):
        result = compute_path_from_ticks(event, path)
        if result:
            row = base_path_row(event, "tick_or_sierra_path_aware", "local_tick_parquet_reconstruction")
            row.update(result)
            return row
    return missing_path_row(
        event,
        "missing_source",
        "local_tick_or_sierra_path_reconstruction",
        "TICK_OR_SIERRA_ORDERED_PATH_NOT_AVAILABLE_FOR_WINDOW",
        searched,
    )


def path_row_from_existing_source(event: dict[str, Any], source_name: str, source_row: dict[str, Any]) -> dict[str, Any]:
    if source_name == "candidate_ltf_path_order":
        mode = "m1_path_aware" if source_row.get("ltf_source") == "MT5_M1" else "missing_source"
        status = source_row.get("ltf_status")
        if status == "SOURCE_BLOCKED":
            return missing_path_row(
                event,
                "missing_source",
                "candidate_ltf_path_order",
                "LTF_SOURCE_BLOCKED_IN_SOURCE_ROW",
                [],
            )
        row = base_path_row(event, mode, "candidate_ltf_path_order")
        row.update(
            {
                "path_source_status": status or "LTF_PATH_ORDER_ROW",
                "source_path": event.get("source_path"),
                "source_sha256": event.get("source_sha256"),
                "entry_touched": source_row.get("entry_first_touch_utc") is not None,
                "entry_first_touch_utc": source_row.get("entry_first_touch_utc"),
                "sl_first_touch_utc": source_row.get("sl_first_touch_utc"),
                "tp1_first_touch_utc": source_row.get("tp1_first_touch_utc"),
                "terminal_order": source_row.get("path_order_label"),
                "same_bar_ambiguity": source_row.get("same_m1_ambiguity"),
                "confidence": "source_ltf_path_order",
            }
        )
        return row
    if source_name == "candidate_path_contract_audit":
        row = base_path_row(event, "m1_path_aware", "candidate_path_contract_audit")
        touches_ = source_row.get("first_touch_times") or {}
        row.update(
            {
                "path_source_status": source_row.get("path_contract_status"),
                "source_path": event.get("source_path"),
                "source_sha256": event.get("source_sha256"),
                "entry_touched": source_row.get("touched_entry"),
                "entry_first_touch_utc": touches_.get("entry_first_touch_utc"),
                "sl_first_touch_utc": touches_.get("sl_first_touch_utc"),
                "tp1_first_touch_utc": touches_.get("tp1_first_touch_utc"),
                "terminal_order": source_row.get("path_label"),
                "same_bar_ambiguity": source_row.get("path_ambiguity_status") == "SAME_BAR_AMBIGUOUS",
                "source_ohlc_range": source_row.get("source_ohlc_range"),
                "confidence": source_row.get("tick_order_claim_status") or "path_contract_source",
            }
        )
        return row
    if source_name == "candidate_path_follow":
        row = base_path_row(event, "bar_close_m15", "candidate_path_follow")
        row.update(
            {
                "path_source_status": "FORWARD_SHADOW_PATH_ROW",
                "source_path": event.get("source_path"),
                "source_sha256": event.get("source_sha256"),
                "entry_touched": source_row.get("touched_entry"),
                "sl_first_touch_utc": None,
                "tp1_first_touch_utc": None,
                "terminal_order": source_row.get("path_label"),
                "hit_sl": source_row.get("hit_sl"),
                "hit_tp1": source_row.get("hit_tp1"),
                "max_high": source_row.get("max_high"),
                "min_low": source_row.get("min_low"),
                "last_close": source_row.get("last_close"),
                "nearest_distance_to_entry": source_row.get("nearest_distance_to_entry"),
                "confidence": "forward_shadow_m15_path_label",
            }
        )
        return row
    if source_name == "pending_limit_lifecycle":
        row = base_path_row(event, "bar_close_m15", "pending_limit_lifecycle")
        row.update(
            {
                "path_source_status": "PENDING_LIMIT_LIFECYCLE_ROW",
                "source_path": event.get("source_path"),
                "source_sha256": event.get("source_sha256"),
                "entry_touched": source_row.get("trigger_condition_met"),
                "terminal_order": source_row.get("fill_no_fill_label"),
                "fill_no_fill_label": source_row.get("fill_no_fill_label"),
                "broker_fill_state": source_row.get("broker_fill_state"),
                "cancel_reason": source_row.get("cancel_reason"),
                "confidence": "asof_pending_lifecycle_or_checked_m15",
            }
        )
        return row
    row = base_path_row(event, "missing_source", source_name)
    row.update(
        {
            "path_source_status": "SOURCE_ROW_HAS_NO_PATH_ORDER_FIELDS",
            "terminal_order": None,
            "entry_touched": None,
            "confidence": "event_only_source",
        }
    )
    return row


def runtime_decision_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    paths: list[dict[str, Any]] = []
    for line_no, trace in iter_jsonl(DECISION_TRACE_PATH):
        input_event = trace.get("input_event") or {}
        event = {
            "schema_version": "vnext_replay_event_v1",
            "stage_id": SOURCE_GAP_STAGE,
            "event_id": "evt_" + stable_hash(["runtime_fixture", trace.get("trace_id")]),
            "source_event_type": "runtime_harness_fixture",
            "source_schema_version": trace.get("schema_version"),
            "source_path": rel(DECISION_TRACE_PATH),
            "source_line_no": line_no,
            "source_sha256": file_hash_from_inventory(DECISION_TRACE_PATH),
            "source_row_key": trace.get("trace_id"),
            "source_use_status": "RUNTIME_DECISION_TRACE_REFERENCE",
            "candidate_id": trace.get("event_id"),
            "trade_id": None,
            "duplicate_group_id": trace.get("event_id"),
            "symbol": input_event.get("symbol"),
            "source_symbol": input_event.get("source_symbol"),
            "broker_symbol": None,
            "timeframe": input_event.get("market_timeframe"),
            "session": input_event.get("route_session"),
            "kill_zone": input_event.get("kill_zone"),
            "framework": input_event.get("framework"),
            "decision": trace.get("route_decision", {}).get("decision"),
            "side": input_event.get("side") or input_event.get("direction"),
            "decision_time_utc": None,
            "window_start_utc": None,
            "window_end_utc": None,
            "entry_price": None,
            "stop_loss": None,
            "take_profit_1": None,
            "geometry_available": False,
            "duplicate_policy": "runtime fixture reference; not an outcome denominator",
            "forbidden_outcome_fields_non_null": [],
        }
        events.append(event)
        path = base_path_row(event, trace.get("replay_mode"), "runtime_harness_decision_trace")
        route_decision = trace.get("route_decision") or {}
        route_evidence = route_decision.get("evidence") or {}
        path.update(
            {
                "path_source_status": "RUNTIME_DECISION_TRACE_ONLY",
                "decision_trace_id": trace.get("trace_id"),
                "decision_trace_path": rel(DECISION_TRACE_PATH),
                "runtime_surface_calls": trace.get("runtime_surface_calls"),
                "route_decision": route_decision.get("decision"),
                "route_matched": route_decision.get("matched"),
                "route_reason": route_decision.get("reason"),
                "route_matched_row_ids": route_evidence.get("matched_row_ids"),
                "route_source_component_counts": route_evidence.get("source_component_counts"),
                "route_evidence_family_counts": route_evidence.get("evidence_family_counts"),
                "route_action_class_counts": route_evidence.get("action_class_counts"),
                "route_decision_resolution": route_evidence.get("decision_resolution"),
                "pre_ai_action": (trace.get("pre_ai_decision") or {}).get("action"),
                "risk_reason": (trace.get("risk_adjustment") or {}).get("reason"),
                "pending_would_action": (trace.get("pending_policy") or {}).get("would_action"),
                "terminal_order": "DECISION_TRACE_NOT_PATH_OUTCOME",
                "confidence": "runtime_truth_harness_reference",
            }
        )
        paths.append(path)
    return events, paths


def build_path_jobs(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    jobs: dict[str, dict[str, Any]] = {}
    for event in events:
        if not event.get("geometry_available"):
            continue
        if not event.get("window_start_utc") or not event.get("window_end_utc"):
            continue
        key = stable_hash(
            [
                event.get("duplicate_group_id"),
                event.get("symbol"),
                event.get("side"),
                event.get("entry_price"),
                event.get("stop_loss"),
                event.get("take_profit_1"),
                event.get("window_start_utc"),
                event.get("window_end_utc"),
            ],
            length=24,
        )
        jobs.setdefault(key, dict(event))
    return [jobs[key] for key in sorted(jobs)]


def build_path_rows(
    events: list[dict[str, Any]],
    originals_by_event: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        source_name = event.get("source_event_type")
        if source_name in {
            "candidate_ltf_path_order",
            "candidate_path_contract_audit",
            "candidate_path_follow",
            "pending_limit_lifecycle",
        }:
            rows.append(path_row_from_existing_source(event, str(source_name), originals_by_event[event["event_id"]][0]))
    for job in build_path_jobs(events):
        rows.extend(ohlc_path_rows_for_job(job))
        rows.append(tick_path_row_for_job(job))
    rows.sort(key=lambda item: (str(item.get("event_id")), str(item.get("replay_mode")), str(item.get("source_evidence_type"))))
    return rows


def source_gap_rows(path_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in path_rows:
        if row.get("path_source_status") != "MISSING_SOURCE":
            continue
        key = (
            str(row.get("symbol")),
            str(row.get("replay_mode")),
            str(row.get("source_evidence_type")),
            str(row.get("source_gap_class")),
        )
        group = groups.setdefault(
            key,
            {
                "schema_version": "vnext_replay_source_gap_v1",
                "stage_id": SOURCE_GAP_STAGE,
                "gap_id": "gap_" + stable_hash(key, length=20),
                "source_gap_class": row.get("source_gap_class"),
                "symbol": row.get("symbol"),
                "replay_mode": row.get("replay_mode"),
                "source_evidence_type": row.get("source_evidence_type"),
                "missing_fields": row.get("missing_fields") or [],
                "searched_paths": [],
                "affected_event_count": 0,
                "status": "SOURCE_GAP_RECORDED_WITH_SEARCH_ATTEMPTS",
                "next_action": "continue approved local/export/reconstruction/proxy pursuit before terminal missing_source use",
            },
        )
        group["affected_event_count"] += 1
        for path in row.get("searched_paths") or []:
            if path not in group["searched_paths"]:
                group["searched_paths"].append(path)
    return [groups[key] for key in sorted(groups)]


def update_source_gap_ledger(stage04_gaps: list[dict[str, Any]]) -> None:
    existing = read_jsonl(SOURCE_GAP_LEDGER_PATH)
    kept = [row for row in existing if row.get("stage_id") != SOURCE_GAP_STAGE]
    write_jsonl(SOURCE_GAP_LEDGER_PATH, kept + stage04_gaps)


def update_output_manifest() -> None:
    existing = read_json(OUTPUT_MANIFEST_PATH) if OUTPUT_MANIFEST_PATH.exists() else {}
    existing_paths = {
        item.get("path"): item
        for item in existing.get("outputs", [])
        if isinstance(item, dict) and item.get("path")
    }
    for path in [
        EVENT_LEDGER_PATH,
        PATH_OUTCOME_LEDGER_PATH,
        SUMMARY_PATH,
        SOURCE_GAP_LEDGER_PATH,
    ]:
        existing_paths[rel(path)] = {
            "path": rel(path),
            "exists": True,
            "bytes": path.stat().st_size,
            "lines": line_count(path),
            "sha256": sha256_file(path),
            "source_kind": "generated_replay_output",
        }
    write_json(
        OUTPUT_MANIFEST_PATH,
        {
            "schema_version": "vnext_replay_output_manifest_v1",
            "generated_utc": utc_now(),
            "route_id": "vnext_replay_truth_engine_and_saturated_ablation_2026_05_24",
            "outputs": [existing_paths[key] for key in sorted(existing_paths)],
            "next_stage": "STAGE_05_SATURATED_REPLAY",
        },
    )


def build_outputs() -> dict[str, Any]:
    events, originals_by_event, _geometry = build_events()
    runtime_events, runtime_paths = runtime_decision_rows()
    all_events = events + runtime_events
    path_rows = runtime_paths + build_path_rows(events, originals_by_event)
    gap_rows = source_gap_rows(path_rows)
    write_jsonl(EVENT_LEDGER_PATH, all_events)
    write_jsonl(PATH_OUTCOME_LEDGER_PATH, path_rows)
    update_source_gap_ledger(gap_rows)
    mode_counts = Counter(row.get("replay_mode") for row in path_rows)
    status_counts = Counter(row.get("path_source_status") for row in path_rows)
    source_event_counts = Counter(row.get("source_event_type") for row in all_events)
    summary = {
        "schema_version": "vnext_replay_event_path_reconstruction_summary_v1",
        "generated_utc": utc_now(),
        "stage_id": SOURCE_GAP_STAGE,
        "event_rows": len(all_events),
        "unique_duplicate_groups": len({row.get("duplicate_group_id") for row in all_events}),
        "source_event_counts": dict(sorted(source_event_counts.items())),
        "path_rows": len(path_rows),
        "path_mode_counts": dict(sorted(mode_counts.items())),
        "path_status_counts": dict(sorted(status_counts.items())),
        "geometry_jobs": len(build_path_jobs(events)),
        "source_gap_rows": len(gap_rows),
        "required_replay_modes_present": sorted(REQUIRED_REPLAY_MODES.intersection(mode_counts)),
        "required_replay_modes_missing": sorted(REQUIRED_REPLAY_MODES.difference(mode_counts)),
        "source_logs_consumed": [rel(path) for _name, path in SOURCE_LOGS if path.exists()],
        "data_inventory_rows_available": line_count(DATA_COVERAGE_LEDGER_PATH),
        "no_live_trading_or_broker_mutation": True,
        "pass": (
            len(all_events) > 0
            and len(path_rows) > 0
            and REQUIRED_REPLAY_MODES.issubset(set(mode_counts))
            and mode_counts.get("current_config_shadow", 0) > 0
            and mode_counts.get("hypothetical_activated_vnext", 0) > 0
        ),
    }
    write_json(SUMMARY_PATH, summary)
    update_output_manifest()
    if not summary["pass"]:
        raise SystemExit("event/path reconstruction verification failed")
    return summary


def check_outputs() -> None:
    expected_summary = build_outputs()
    existing_summary = read_json(SUMMARY_PATH)
    existing_no_time = dict(existing_summary)
    expected_no_time = dict(expected_summary)
    existing_no_time.pop("generated_utc", None)
    expected_no_time.pop("generated_utc", None)
    if existing_no_time != expected_no_time:
        raise AssertionError("Event/path reconstruction summary is stale")
    if not existing_summary.get("pass"):
        raise AssertionError("Event/path reconstruction summary did not pass")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check_outputs()
        print("vNext replay event/path reconstruction check passed")
        return
    summary = build_outputs()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
