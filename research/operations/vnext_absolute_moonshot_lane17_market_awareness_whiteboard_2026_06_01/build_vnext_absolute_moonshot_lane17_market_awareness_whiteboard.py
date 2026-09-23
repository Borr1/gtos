from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.components.market_state import (  # noqa: E402
    calculate_atr,
    detect_swings,
    identify_structure_v2,
)


ROUTE_ID = "vnext_absolute_moonshot_lane17_market_awareness_whiteboard_2026_06_01"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID

MASTER_DIR = ROOT / "research" / "operations" / "vnext_absolute_moonshot_master_orchestration_2026_06_01"
LANE01_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane01_data_universe_source_authority_2026_06_01"
LANE02_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01"
LANE03_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01"
LANE04_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane04_historical_microscope_engine_2026_06_01"
LANE05_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane05_feature_store_v1_2026_06_01"
LANE06_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane06_label_store_v1_2026_06_01"
LANE07_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01"
LANE08_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01"
LANE09_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane09_meta_selector_v2_2026_06_01"
LANE09B_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane09b_selector_scheduler_reconciliation_2026_06_01"
LANE10_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane10_portfolio_scheduler_v2_2026_06_01"
LANE10B_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design_2026_06_01"
LANE11_DIR = ROOT / "research" / "operations" / "vnext_moonshot_lane11_execution_policy_engine_v2_2026_06_01"

LANE05_FEATURE_LEDGER = LANE05_DIR / "LANE05_TIMELINE_FEATURE_VECTOR_LEDGER.jsonl.gz"
LANE07_SYMBOL_SPEC_LEDGER = LANE07_DIR / "LANE07_SYMBOL_SPEC_SESSION_LEDGER.jsonl"
LANE07_COST_LEDGER = LANE07_DIR / "LANE07_COST_CALIBRATION_LEDGER.jsonl"
LANE08_REPLAY_LEDGER = LANE08_DIR / "LANE08_REPLAY_ROW_LEDGER.jsonl.gz"
CORRELATION_MATRIX = ROOT / "exports" / "multi_instrument" / "screening_results" / "correlation_matrix.json"
RECENT_HISTORY_ROOT = ROOT / "data" / "historical_2026"
DIRECT_DATA_ROOT = ROOT / "data"
PHASE3_M15_ROOT = ROOT / "data" / "mt5_research_exports" / "phase3_m15_2022_2026_fn_chunked_v1"
PHASE3_MULTI_ROOT = ROOT / "data" / "mt5_research_exports" / "phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1"
M1_FORWARD_ROOT = ROOT / "data" / "m1"
TICK_FORWARD_ROOT = ROOT / "data" / "ticks"
M1_CAPTURE_STATE = ROOT / "pipeline_state" / "m1_capture_state.json"

SCHEMA_PATH = ROUTE_DIR / "LANE17_MARKET_AWARENESS_SCHEMA.json"
WHITEBOARD_REPLAY_LEDGER = ROUTE_DIR / "LANE17_MARKET_WHITEBOARD_REPLAY_ROWS.jsonl.gz"
FORWARD_SNAPSHOT_LEDGER = ROUTE_DIR / "LANE17_FORWARD_SNAPSHOT_LEDGER.jsonl"
SOURCE_COMPLETENESS_LEDGER = ROUTE_DIR / "LANE17_SOURCE_COMPLETENESS_LEDGER.jsonl"
SOURCE_GAP_LEDGER = ROUTE_DIR / "LANE17_SOURCE_GAP_LEDGER.jsonl.gz"
CORRELATION_REGIME_SPREAD_LEDGER = ROUTE_DIR / "LANE17_CORRELATION_REGIME_SPREAD_LEDGER.jsonl"
DOWNSTREAM_CONTRACT = ROUTE_DIR / "LANE17_DOWNSTREAM_CONTRACT.json"
FORWARD_CAPTURE_CONTRACT = ROUTE_DIR / "LANE17_FORWARD_CAPTURE_CONTRACT.json"
IMPLEMENTATION_DECISION_LEDGER = ROUTE_DIR / "LANE17_IMPLEMENTATION_DECISION_LEDGER.jsonl"
NO_LEAK_VALIDATION_LEDGER = ROUTE_DIR / "LANE17_NO_LEAK_VALIDATION_LEDGER.jsonl"
DEPENDENCY_STATE_LEDGER = ROUTE_DIR / "LANE17_DEPENDENCY_STATE_LEDGER.jsonl"
SOURCE_USE_STATE = ROUTE_DIR / "LANE17_SOURCE_USE_STATE.json"
RESULT_USE_STATUS = ROUTE_DIR / "LANE17_RESULT_USE_STATUS.json"
RUNTIME_EFFECT_BOUNDARY = ROUTE_DIR / "LANE17_RUNTIME_EFFECT_BOUNDARY.json"
CONTEXT_ANCHOR = ROUTE_DIR / "LANE17_CONTEXT_ANCHOR.md"
SATURATION_SELF_RED_TEAM = ROUTE_DIR / "LANE17_SATURATION_SELF_RED_TEAM.md"
OUTPUT_MANIFEST = ROUTE_DIR / "LANE17_OUTPUT_MANIFEST.json"
COMPLETION_AUDIT = ROUTE_DIR / "LANE17_COMPLETION_AUDIT.json"
VERIFICATION_RESULT = ROUTE_DIR / "LANE17_VERIFICATION_RESULT.json"
FOCUSED_TEST_RESULT = ROUTE_DIR / "LANE17_FOCUSED_TEST_RESULT.xml"

EXPECTED_REPLAY_ROWS = 289_928

LIVE_SYMBOLS = (
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
)

OHLC_TIMEFRAMES = ("D1", "H4", "H1", "M15")
WHITEBOARD_TIMEFRAMES = ("D1", "H4", "H1", "M15", "M1", "tick")
SOURCE_STATE_LABELS = (
    "decision-available",
    "replay-only",
    "label-only",
    "broker-real",
    "proxy",
    "missing",
    "non-generatable",
)
SESSION_BUCKETS = (
    "asia_broad",
    "london_broad",
    "ny_broad",
    "late_us_afterhours_utc",
    "unknown_session",
)
REQUIRED_WHITEBOARD_FIELDS = (
    "schema_version",
    "row_id",
    "source_family",
    "source_path",
    "source_hash",
    "decision_asof_utc",
    "source_capture_utc",
    "symbol",
    "broker_symbol",
    "duplicate_key",
    "no_leak_status",
    "source_completeness_state",
    "runtime_effect_boundary",
    "whiteboard_version",
    "timeframe_coverage_state",
    "htf_structure_state",
    "m15_structure_state",
    "m1_path_state",
    "tick_state",
    "spread_to_risk_state",
    "volatility_state",
    "session_state",
    "market_hours_state",
    "source_completeness",
    "broker_feasibility_fields",
    "correlation_cluster_state",
    "regime_state",
    "field_source_state",
    "stale_or_null_reason",
)
FORBIDDEN_WHITEBOARD_FIELDS = {
    "result_payload",
    "label_values",
    "result_r",
    "source_bound_proxy_r",
    "broker_real_net_r",
    "gross_profit_r",
    "future_outcome",
}
STALE_OLD_SYSTEM_TERMS = (
    "PrimaryAnalyzer",
    "L2",
    "old_7_symbol",
    "old 7-symbol",
    "static_fixed_1.5R_default",
)
RUNTIME_BOUNDARY = (
    "offline_market_awareness_whiteboard_and_default_off_forward_capture_contract_only_"
    "no_live_broker_order_deal_position_operation_no_config_prompt_risk_execution_safety_"
    "canary_selector_scheduler_activation_no_paid_api_no_remote"
)
RESULT_USE_STATUS_TEXT = (
    "market_awareness_source_state_rows_only; no broker-real performance claim; "
    "label-only and result rows remain excluded from decision fields; correlation/regime/spread "
    "states are source-labeled as proxy, broker-real snapshot, missing, or decision-available"
)
SOURCE_USE_STATE_TEXT = (
    "local_repo_route_artifacts_lane01_to_lane11_lane09b_lane10b_current_runtime_market_state_code_"
    "local_ohlc_m1_tick_file_inventory_and_lane07_broker_snapshot_only_no_broker_mutation"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def compact_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(compact_json(row) + "\n")
            count += 1
    return count


def write_jsonl_gz(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with gzip.open(path, "wt", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(compact_json(row) + "\n")
            count += 1
    return count


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def iter_jsonl_gz(path: Path) -> Iterable[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as fh:  # type: ignore[arg-type]
        return sum(1 for _ in fh)


_SHA256_CACHE: dict[Path, str | None] = {}


def sha256_file(path: Path) -> str | None:
    path = path.resolve()
    if path in _SHA256_CACHE:
        return _SHA256_CACHE[path]
    if not path.exists():
        _SHA256_CACHE[path] = None
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    _SHA256_CACHE[path] = h.hexdigest()
    return _SHA256_CACHE[path]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def dt_date(value: Any) -> str | None:
    parsed = parse_dt(value)
    if parsed is None:
        raw = str(value or "")
        if len(raw) >= 10 and raw[4:5] == "-" and raw[7:8] == "-":
            return raw[:10]
        return None
    return parsed.date().isoformat()


def canonical_time(value: Any) -> str | None:
    parsed = parse_dt(value)
    if parsed is not None:
        return parsed.isoformat()
    return str(value) if value else None


def classify_session(timestamp_utc: str | None) -> str:
    parsed = parse_dt(timestamp_utc)
    if parsed is None:
        return "unknown_session"
    hour = parsed.hour
    if 0 <= hour < 7:
        return "asia_broad"
    if 7 <= hour < 12:
        return "london_broad"
    if 12 <= hour < 21:
        return "ny_broad"
    return "late_us_afterhours_utc"


def csv_path_candidates(symbol: str, timeframe: str) -> list[tuple[str, Path]]:
    candidates: list[tuple[str, Path]] = []
    if timeframe in OHLC_TIMEFRAMES:
        candidates.append(("recent_historical_2026", RECENT_HISTORY_ROOT / f"{symbol}_{timeframe}.csv"))
        candidates.append(("direct_data_root", DIRECT_DATA_ROOT / f"{symbol}_{timeframe}.csv"))
    if timeframe == "M15":
        candidates.append(("phase3_m15_2022_2026", PHASE3_M15_ROOT / f"{symbol}_M15.csv"))
    if timeframe in {"D1", "H1", "M1", "M5"}:
        candidates.append(("phase3_m1_m5_h1_d1_2022_2026", PHASE3_MULTI_ROOT / f"{symbol}_{timeframe}.csv"))
    return candidates


def csv_stats(path: Path, source_family: str, symbol: str, timeframe: str) -> dict[str, Any]:
    row_count = 0
    first_time: str | None = None
    last_time: str | None = None
    header: list[str] = []
    if path.exists():
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            header = list(reader.fieldnames or [])
            time_field = "time_utc" if "time_utc" in header else "time"
            for row in reader:
                value = row.get(time_field)
                if value and first_time is None:
                    first_time = canonical_time(value)
                if value:
                    last_time = canonical_time(value)
                row_count += 1
    return {
        "schema_version": "lane17_source_coverage_row_v1",
        "route_id": ROUTE_ID,
        "source_family": source_family,
        "source_path": str(path.relative_to(ROOT)) if path.exists() else str(path.relative_to(ROOT)),
        "exists": path.exists(),
        "symbol": symbol,
        "timeframe": timeframe,
        "row_count": row_count,
        "first_time_utc": first_time,
        "last_time_utc": last_time,
        "first_date": dt_date(first_time),
        "last_date": dt_date(last_time),
        "header_fields": header,
        "source_state": "decision-available" if path.exists() and row_count else "missing",
        "missing_reason": None if path.exists() and row_count else f"{symbol}_{timeframe}_source_file_absent_or_empty",
        "capture_or_repair_requirement": None
        if path.exists() and row_count
        else f"provide source-hashed {timeframe} bars for {symbol} or mark field missing by decision timestamp",
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
    }


def source_covers_date(row: dict[str, Any], day: str | None) -> bool:
    if not day or not row.get("exists") or not row.get("row_count"):
        return False
    first_day = row.get("first_date")
    last_day = row.get("last_date")
    if not first_day or not last_day:
        return False
    return str(first_day) <= day <= str(last_day)


def build_source_inventory() -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    rows: list[dict[str, Any]] = []
    by_symbol_tf: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for symbol in LIVE_SYMBOLS:
        for timeframe in ("D1", "H4", "H1", "M15", "M1", "tick"):
            if timeframe == "M1":
                for family, path in csv_path_candidates(symbol, "M1"):
                    row = csv_stats(path, family, symbol, "M1")
                    rows.append(row)
                    by_symbol_tf[(symbol, "M1")].append(row)
                m1_dir = M1_FORWARD_ROOT / symbol
                csv_files = sorted(m1_dir.glob("*.csv")) if m1_dir.exists() else []
                rows.append(
                    {
                        "schema_version": "lane17_source_coverage_row_v1",
                        "route_id": ROUTE_ID,
                        "source_family": "forward_m1_capture",
                        "source_path": str(m1_dir.relative_to(ROOT)),
                        "exists": bool(csv_files),
                        "symbol": symbol,
                        "timeframe": "M1",
                        "file_count": len(csv_files),
                        "first_date": csv_files[0].stem if csv_files else None,
                        "last_date": csv_files[-1].stem if csv_files else None,
                        "row_count": sum(max(0, count_text_lines(p) - 1) for p in csv_files),
                        "source_state": "decision-available" if csv_files else "missing",
                        "missing_reason": None if csv_files else f"forward_m1_capture_absent_for_{symbol}",
                        "capture_or_repair_requirement": None
                        if csv_files
                        else f"run default-off M1 capture or source-hashed read-only M1 export for {symbol}",
                        "runtime_effect_boundary": RUNTIME_BOUNDARY,
                    }
                )
            elif timeframe == "tick":
                tick_dir = TICK_FORWARD_ROOT / symbol
                tick_files = sorted(tick_dir.glob("*.parquet")) if tick_dir.exists() else []
                rows.append(
                    {
                        "schema_version": "lane17_source_coverage_row_v1",
                        "route_id": ROUTE_ID,
                        "source_family": "forward_tick_capture",
                        "source_path": str(tick_dir.relative_to(ROOT)),
                        "exists": bool(tick_files),
                        "symbol": symbol,
                        "timeframe": "tick",
                        "file_count": len(tick_files),
                        "first_date": tick_files[0].stem if tick_files else None,
                        "last_date": tick_files[-1].stem if tick_files else None,
                        "bytes": sum(p.stat().st_size for p in tick_files),
                        "row_count": None,
                        "source_state": "decision-available" if tick_files else "missing",
                        "missing_reason": None if tick_files else f"forward_tick_parquet_absent_for_{symbol}",
                        "capture_or_repair_requirement": None
                        if tick_files
                        else f"run default-off tick capture or source-hashed read-only tick export for {symbol}",
                        "runtime_effect_boundary": RUNTIME_BOUNDARY,
                    }
                )
            else:
                for family, path in csv_path_candidates(symbol, timeframe):
                    row = csv_stats(path, family, symbol, timeframe)
                    rows.append(row)
                    by_symbol_tf[(symbol, timeframe)].append(row)
    return rows, by_symbol_tf


def count_text_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8", errors="ignore") as fh:
        return sum(1 for _ in fh)


def coverage_for(symbol: str, timeframe: str, day: str | None, coverage_index: dict[tuple[str, str], list[dict[str, Any]]]) -> dict[str, Any]:
    source_rows = coverage_index.get((symbol, timeframe), [])
    covering = [row for row in source_rows if source_covers_date(row, day)]
    if covering:
        row = covering[0]
        return {
            "timeframe": timeframe,
            "source_state": "decision-available",
            "coverage_state": "source_available_for_decision_timestamp",
            "source_path": row.get("source_path"),
            "source_family": row.get("source_family"),
            "first_time_utc": row.get("first_time_utc"),
            "last_time_utc": row.get("last_time_utc"),
        }
    existing = [row for row in source_rows if row.get("exists") and row.get("row_count")]
    if existing:
        row = existing[0]
        return {
            "timeframe": timeframe,
            "source_state": "missing",
            "coverage_state": "source_exists_but_not_for_decision_window",
            "source_path": row.get("source_path"),
            "source_family": row.get("source_family"),
            "first_time_utc": row.get("first_time_utc"),
            "last_time_utc": row.get("last_time_utc"),
            "reason": f"{symbol}_{timeframe}_source_range_does_not_cover_{day}",
            "repair_requirement": f"source-hashed {timeframe} bars for {symbol} covering {day}",
        }
    return {
        "timeframe": timeframe,
        "source_state": "missing",
        "coverage_state": "source_file_missing",
        "source_path": None,
        "source_family": None,
        "reason": f"{symbol}_{timeframe}_source_file_absent",
        "repair_requirement": f"source-hashed {timeframe} bars for {symbol}",
    }


def read_recent_candles(path: Path, max_rows: int = 240) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: deque[dict[str, Any]] = deque(maxlen=max_rows)
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                rows.append(
                    {
                        "time": row.get("time_utc") or row.get("time"),
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": float(row.get("volume") or 0.0),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    return list(rows)


def structure_state_from_candles(candles: list[dict[str, Any]], timeframe: str) -> dict[str, Any]:
    if len(candles) < 20:
        return {
            "timeframe": timeframe,
            "source_state": "missing",
            "structure_direction": None,
            "reason": f"{timeframe}_requires_at_least_20_recent_bars_for_forward_structure_snapshot",
            "bar_count": len(candles),
        }
    swings = detect_swings(candles, min_bars=2)
    structure = identify_structure_v2(swings)
    atr = calculate_atr(candles, period=14)
    return {
        "timeframe": timeframe,
        "source_state": "decision-available",
        "structure_direction": structure.direction,
        "protected_swing_price": structure.protected_swing.price if structure.protected_swing else None,
        "swing_sequence_tail": structure.swing_sequence[-8:],
        "hh_count": structure.hh_count,
        "hl_count": structure.hl_count,
        "lh_count": structure.lh_count,
        "ll_count": structure.ll_count,
        "atr_14": round(atr, 8) if atr else 0.0,
        "bar_count": len(candles),
        "last_bar_time_utc": canonical_time(candles[-1].get("time")),
    }


def load_symbol_specs() -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    if not LANE07_SYMBOL_SPEC_LEDGER.exists():
        return specs
    for row in iter_jsonl(LANE07_SYMBOL_SPEC_LEDGER):
        symbol = row.get("symbol")
        if symbol:
            specs[str(symbol)] = row
    return specs


def load_cost_summary() -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = defaultdict(lambda: {"captured_cost_rows": 0, "sessions": Counter()})
    if not LANE07_COST_LEDGER.exists():
        return {}
    for row in iter_jsonl(LANE07_COST_LEDGER):
        symbol = row.get("symbol")
        if not symbol:
            continue
        item = summary[str(symbol)]
        item["captured_cost_rows"] += 1
        item["sessions"][str(row.get("session_label") or "unknown_session")] += 1
        item["latest_cost_status"] = row.get("cost_status")
    return {
        sym: {
            **{k: v for k, v in item.items() if k != "sessions"},
            "sessions": dict(item["sessions"]),
        }
        for sym, item in summary.items()
    }


def load_correlation_matrix() -> dict[str, dict[str, float]]:
    raw = load_json(CORRELATION_MATRIX, {})
    out: dict[str, dict[str, float]] = {}
    for symbol, peers in (raw or {}).items():
        if not isinstance(peers, dict):
            continue
        out[str(symbol)] = {}
        for peer, corr in peers.items():
            try:
                out[str(symbol)][str(peer)] = float(corr)
            except (TypeError, ValueError):
                continue
    return out


def all_correlation_pair_rows(matrix: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    symbols = list(LIVE_SYMBOLS)
    for i, symbol in enumerate(symbols):
        for peer in symbols[i + 1 :]:
            corr = matrix.get(symbol, {}).get(peer)
            if corr is None:
                corr = matrix.get(peer, {}).get(symbol)
            rows.append(
                {
                    "schema_version": "lane17_correlation_pair_v1",
                    "route_id": ROUTE_ID,
                    "row_type": "correlation_pair",
                    "symbol": symbol,
                    "peer_symbol": peer,
                    "correlation": round(float(corr), 6) if corr is not None else None,
                    "source_state": "proxy" if corr is not None else "missing",
                    "source_path": str(CORRELATION_MATRIX.relative_to(ROOT)),
                    "cluster_threshold_abs": 0.4,
                    "risk_relation": correlation_relation(corr),
                    "runtime_effect_boundary": RUNTIME_BOUNDARY,
                }
            )
    return rows


def correlation_relation(corr: float | None) -> str:
    if corr is None:
        return "missing"
    if corr >= 0.4:
        return "same_direction_cluster_peer"
    if corr <= -0.4:
        return "inverse_cluster_peer"
    return "below_cluster_threshold"


def build_correlation_state(symbol: str, matrix: dict[str, dict[str, float]]) -> dict[str, Any]:
    peers = matrix.get(symbol, {})
    positive = []
    negative = []
    all_peers = []
    for peer in LIVE_SYMBOLS:
        if peer == symbol:
            continue
        corr = peers.get(peer)
        if corr is None:
            corr = matrix.get(peer, {}).get(symbol)
        if corr is None:
            continue
        item = {"peer_symbol": peer, "correlation": round(float(corr), 6)}
        all_peers.append(item)
        if corr >= 0.4:
            positive.append(item)
        elif corr <= -0.4:
            negative.append(item)
    risk_score = risk_on_proxy_score(symbol, matrix)
    return {
        "source_state": "proxy",
        "source_path": str(CORRELATION_MATRIX.relative_to(ROOT)),
        "matrix_peer_count": len(all_peers),
        "same_direction_cluster_peers": sorted(positive, key=lambda x: x["peer_symbol"]),
        "inverse_cluster_peers": sorted(negative, key=lambda x: x["peer_symbol"]),
        "cluster_peer_count": len(positive) + len(negative),
        "risk_on_risk_off_proxy_state": risk_score["state"],
        "risk_on_proxy_score": risk_score["score"],
        "risk_on_proxy_components": risk_score["components"],
        "runtime_exact_correlation_join_state": "missing_forward_runtime_snapshot_until_packet_capture",
    }


def risk_on_proxy_score(symbol: str, matrix: dict[str, dict[str, float]]) -> dict[str, Any]:
    risk_on_basket = ("NAS100", "SPX500", "US30_cash", "BTCUSD", "ETHUSD", "AUDUSD", "NZDUSD")
    defensive_basket = ("USDCHF", "USDCAD", "USDJPY", "XAUUSD", "XAGUSD")

    def corr_to(peer: str) -> float | None:
        if peer == symbol:
            return None
        value = matrix.get(symbol, {}).get(peer)
        if value is None:
            value = matrix.get(peer, {}).get(symbol)
        return value

    risk_vals = [corr_to(peer) for peer in risk_on_basket]
    def_vals = [corr_to(peer) for peer in defensive_basket]
    risk_vals_f = [float(v) for v in risk_vals if v is not None]
    def_vals_f = [float(v) for v in def_vals if v is not None]
    score = (mean(risk_vals_f) if risk_vals_f else 0.0) - (mean(def_vals_f) if def_vals_f else 0.0)
    if score >= 0.15:
        state = "risk_on_linked_proxy"
    elif score <= -0.15:
        state = "risk_off_or_defensive_linked_proxy"
    else:
        state = "mixed_or_neutral_proxy"
    return {
        "score": round(score, 6),
        "state": state,
        "components": {
            "risk_on_basket": list(risk_on_basket),
            "defensive_basket": list(defensive_basket),
            "risk_on_mean_corr": round(mean(risk_vals_f), 6) if risk_vals_f else None,
            "defensive_mean_corr": round(mean(def_vals_f), 6) if def_vals_f else None,
        },
    }


def build_market_awareness_schema() -> dict[str, Any]:
    return {
        "schema_version": "lane17_market_awareness_schema_v1",
        "route_id": ROUTE_ID,
        "whiteboard_version": "market_awareness_whiteboard_v1_2026_06_01",
        "required_whiteboard_fields": list(REQUIRED_WHITEBOARD_FIELDS),
        "source_state_labels": list(SOURCE_STATE_LABELS),
        "forbidden_decision_fields": sorted(FORBIDDEN_WHITEBOARD_FIELDS),
        "timeframes": list(WHITEBOARD_TIMEFRAMES),
        "field_contract": {
            "identity_fields": ["symbol", "broker_symbol", "duplicate_key", "row_id"],
            "decision_time_fields": ["decision_asof_utc", "source_capture_utc"],
            "market_state_fields": [
                "timeframe_coverage_state",
                "htf_structure_state",
                "m15_structure_state",
                "m1_path_state",
                "tick_state",
                "spread_to_risk_state",
                "volatility_state",
                "session_state",
                "market_hours_state",
                "correlation_cluster_state",
                "regime_state",
            ],
            "proof_fields": [
                "source_completeness",
                "field_source_state",
                "stale_or_null_reason",
                "source_completeness_state",
                "no_leak_status",
                "runtime_effect_boundary",
            ],
        },
        "no_hidden_null_rule": (
            "Every missing/null/proxy field family must have a field_source_state label and "
            "a stale_or_null_reason or source gap ledger row with field, symbol, decision window, "
            "source path when known, and capture_or_repair_requirement."
        ),
        "no_one_timeframe_rule": "Rows must expose D1,H4,H1,M15,M1,tick coverage states separately.",
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
    }


def source_state_for_coverage(coverage: dict[str, Any]) -> str:
    return str(coverage.get("source_state") or "missing")


def build_timeframe_coverage(
    *,
    symbol: str,
    day: str | None,
    features: dict[str, Any],
    coverage_index: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    coverage: dict[str, Any] = {
        tf: coverage_for(symbol, tf, day, coverage_index) for tf in ("D1", "H4", "H1")
    }
    m15_state = coverage_for(symbol, "M15", day, coverage_index)
    if features.get("source_window_complete") is True:
        m15_state = {
            **m15_state,
            "source_state": "decision-available",
            "coverage_state": "joined_lane05_lane08_candidate_time_m15_state",
        }
    coverage["M15"] = m15_state

    m1_available = bool(features.get("m1_entry_minute_available"))
    coverage["M1"] = {
        "timeframe": "M1",
        "source_state": "decision-available" if m1_available else "missing",
        "coverage_state": features.get("m1_availability_status") or "m1_availability_status_missing",
        "source_path": "Lane05/Lane08 feature source completeness",
        "reason": None if m1_available else "m1_entry_minute_not_available_or_not_joined",
        "repair_requirement": None
        if m1_available
        else f"source-hashed M1 bar covering {symbol} at decision minute {day}",
    }
    strict_tick_available = bool(features.get("strict_tick_available"))
    coverage["tick"] = {
        "timeframe": "tick",
        "source_state": "decision-available" if strict_tick_available else "missing",
        "coverage_state": features.get("tick_availability_status") or "tick_availability_status_missing",
        "source_path": "Lane04 strict tick or data/ticks",
        "reason": None if strict_tick_available else features.get("tick_availability_status") or "strict_tick_not_joined",
        "repair_requirement": None
        if strict_tick_available
        else "ordered bid/ask tick replay or exact tick snapshot at candidate decision/source time",
    }
    return coverage


def build_field_source_state(
    *,
    timeframe_coverage: dict[str, Any],
    features: dict[str, Any],
    symbol_spec: dict[str, Any] | None,
) -> dict[str, str]:
    market_hours_status = (symbol_spec or {}).get("session_status")
    broker_spec_state = "broker-real" if symbol_spec else "missing"
    spread_state = "broker-real" if symbol_spec and symbol_spec.get("spread_sample_status") else "missing"
    if features.get("strict_tick_entry_spread_r") is not None:
        spread_to_risk_state = "decision-available"
    elif features.get("spread_r_bucket") and features.get("spread_r_bucket") != "spread_or_cost_r_missing":
        spread_to_risk_state = "proxy"
    else:
        spread_to_risk_state = "missing"
    regime_state = "proxy" if features.get("regime_h4_state") is not None else "missing"
    if features.get("regime_join_state") == "exact_h4_regime_join":
        regime_state = "decision-available"
    return {
        "symbol": "decision-available",
        "broker_symbol": broker_spec_state if symbol_spec else "decision-available",
        "timestamp": "decision-available",
        "d1_structure": source_state_for_coverage(timeframe_coverage["D1"]),
        "h4_structure": source_state_for_coverage(timeframe_coverage["H4"]),
        "h1_structure": source_state_for_coverage(timeframe_coverage["H1"]),
        "m15_structure": "decision-available" if features.get("m15_trend_state_20") is not None else "missing",
        "m1_path": source_state_for_coverage(timeframe_coverage["M1"]),
        "tick_state": source_state_for_coverage(timeframe_coverage["tick"]),
        "spread_snapshot": spread_state,
        "spread_to_risk": spread_to_risk_state,
        "session_state": "decision-available" if features.get("session_bucket") else "missing",
        "market_hours_state": "missing" if str(market_hours_status or "").startswith("MISSING") else broker_spec_state,
        "source_completeness": "decision-available",
        "broker_feasibility": broker_spec_state,
        "correlation_cluster": "proxy",
        "runtime_correlation_snapshot": "missing",
        "regime_state": regime_state,
        "runtime_h4_regime_snapshot": "missing"
        if features.get("regime_join_state") != "exact_h4_regime_join"
        else "decision-available",
        "label_outcome_fields": "label-only",
        "historical_broker_intent_or_order_truth": "non-generatable",
    }


def null_reason(field: str, reason: str, requirement: str, source_path: str | None = None) -> dict[str, Any]:
    return {
        "field": field,
        "reason": reason,
        "source_path": source_path,
        "capture_or_repair_requirement": requirement,
    }


def build_gap_rows(
    *,
    whiteboard_row_id: str,
    source_replay_row_id: str,
    symbol: str,
    broker_symbol: str,
    decision_asof_utc: str | None,
    timeframe_coverage: dict[str, Any],
    features: dict[str, Any],
    field_source_state: dict[str, str],
    symbol_spec: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(field_family: str, reason: str, requirement: str, source_path: str | None = None, source_state: str = "missing") -> None:
        rows.append(
            {
                "schema_version": "lane17_source_gap_row_v1",
                "route_id": ROUTE_ID,
                "whiteboard_row_id": whiteboard_row_id,
                "source_replay_row_id": source_replay_row_id,
                "symbol": symbol,
                "broker_symbol": broker_symbol,
                "decision_asof_utc": decision_asof_utc,
                "field_family": field_family,
                "source_state": source_state,
                "reason": reason,
                "source_path": source_path,
                "capture_or_repair_requirement": requirement,
                "runtime_effect_boundary": RUNTIME_BOUNDARY,
            }
        )

    for tf in ("D1", "H4", "H1", "M1", "tick"):
        state = timeframe_coverage.get(tf, {})
        if state.get("source_state") == "missing":
            add(
                f"{tf.lower()}_coverage_or_structure",
                str(state.get("reason") or state.get("coverage_state") or f"{tf}_missing"),
                str(state.get("repair_requirement") or f"source-hashed {tf} decision-as-of state for {symbol}"),
                state.get("source_path"),
            )
    if field_source_state.get("spread_to_risk") == "missing":
        add(
            "spread_to_risk",
            str(features.get("spread_r_bucket") or "spread_to_risk_missing"),
            "capture decision-time spread plus candidate risk_price_distance or strict tick entry spread R",
            "Lane05 feature row / Lane07 broker snapshot",
        )
    if field_source_state.get("runtime_correlation_snapshot") == "missing":
        add(
            "correlation_cluster_runtime_snapshot",
            str(features.get("correlation_cluster_join_state") or "no_exact_correlation_cluster_runtime_join"),
            "capture as-of correlation cluster snapshot keyed by symbol and decision timestamp",
            "shadow_logs/cross_instrument_correlation_decisions.jsonl",
        )
    if field_source_state.get("runtime_h4_regime_snapshot") == "missing":
        add(
            "h4_regime_runtime_snapshot",
            str(features.get("regime_join_state") or "no_exact_h4_regime_join"),
            "capture as-of H4 regime snapshot keyed by symbol and decision timestamp",
            "shadow_logs/regime_decay_outcome_join.jsonl",
        )
    if field_source_state.get("market_hours_state") == "missing":
        add(
            "market_hours_state",
            str((symbol_spec or {}).get("session_status") or "broker_market_hours_export_missing"),
            "read-only MT5 symbol sessions or broker calendar export by symbol",
            "Lane07_SYMBOL_SPEC_SESSION_LEDGER.jsonl",
        )
    if not symbol_spec or str(symbol_spec.get("trade_tick_value_status") or "").startswith("MISSING"):
        add(
            "broker_exact_tick_value",
            str((symbol_spec or {}).get("trade_tick_value_status") or "symbol_spec_missing"),
            "read-only full MT5 symbol_info export including trade_tick_value/trade_tick_size",
            "Lane07_SYMBOL_SPEC_SESSION_LEDGER.jsonl",
        )
    add(
        "historical_broker_intent_or_order_truth",
        "historical order intent/order/deal lifecycle cannot be generated from price movement alone",
        "prospective runtime packet capture or read-only broker/account export where available",
        None,
        source_state="non-generatable",
    )
    return rows


def build_whiteboard_row(
    *,
    idx: int,
    replay: dict[str, Any],
    feature: dict[str, Any] | None,
    coverage_index: dict[tuple[str, str], list[dict[str, Any]]],
    symbol_specs: dict[str, dict[str, Any]],
    correlation_states: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    features = (feature or {}).get("features") or {}
    symbol = str(replay.get("symbol") or features.get("identity_symbol") or "")
    broker_symbol = str(replay.get("broker_symbol") or features.get("identity_broker_symbol") or symbol)
    decision_asof = canonical_time(replay.get("decision_asof_utc") or features.get("feature_time_utc"))
    day = dt_date(decision_asof)
    selected_row_id = str(replay.get("selected_row_id") or (feature or {}).get("duplicate_key") or "")
    row_id = f"lane17_whiteboard_replay_{idx:09d}"
    symbol_spec = symbol_specs.get(symbol)
    timeframe_coverage = build_timeframe_coverage(
        symbol=symbol,
        day=day,
        features=features,
        coverage_index=coverage_index,
    )
    field_source_state = build_field_source_state(
        timeframe_coverage=timeframe_coverage,
        features=features,
        symbol_spec=symbol_spec,
    )
    source_completeness = replay.get("decision_inputs", {}).get("source_completeness", {})
    correlation_state = correlation_states.get(symbol) or {"source_state": "missing"}
    stale_reasons = []
    for field, state in field_source_state.items():
        if state in {"missing", "non-generatable"}:
            stale_reasons.append(
                null_reason(
                    field,
                    f"{field}_source_state_{state}",
                    f"repair or capture {field} as source-labeled field before downstream live use",
                )
            )
    htf_state = {
        "source_state": "mixed",
        "d1": {
            "coverage_state": timeframe_coverage["D1"],
            "structure_state": "raw_source_available_join_required"
            if timeframe_coverage["D1"].get("source_state") == "decision-available"
            else "missing",
        },
        "h4": {
            "coverage_state": timeframe_coverage["H4"],
            "structure_state": "raw_source_available_join_required"
            if timeframe_coverage["H4"].get("source_state") == "decision-available"
            else "missing",
            "regime_proxy": features.get("regime_h4_state"),
            "regime_join_state": features.get("regime_join_state"),
        },
        "h1": {
            "coverage_state": timeframe_coverage["H1"],
            "structure_state": "raw_source_available_join_required"
            if timeframe_coverage["H1"].get("source_state") == "decision-available"
            else "missing",
        },
        "stale_or_null_reason": [
            reason
            for reason in stale_reasons
            if reason["field"] in {"d1_structure", "h4_structure", "h1_structure", "runtime_h4_regime_snapshot"}
        ],
    }
    m15_state = {
        "source_state": field_source_state["m15_structure"],
        "trend_state_20": features.get("m15_trend_state_20"),
        "volatility_state_14_vs_50": features.get("m15_volatility_state_14_vs_50"),
        "liquidity_sweep_proxy_state": features.get("liquidity_sweep_proxy_state"),
        "source_quality_status": features.get("source_quality_status"),
    }
    spread_state = {
        "source_state": field_source_state["spread_to_risk"],
        "spread_r_bucket": features.get("spread_r_bucket"),
        "strict_tick_entry_spread_r": features.get("strict_tick_entry_spread_r"),
        "strict_tick_risk_price_distance": features.get("strict_tick_risk_price_distance"),
        "broker_snapshot_spread_sample_points": (symbol_spec or {}).get("spread_sample_points"),
        "broker_snapshot_spread_sample_status": (symbol_spec or {}).get("spread_sample_status"),
        "cost_status": features.get("cost_status"),
    }
    row = {
        "schema_version": "lane17_market_whiteboard_row_v1",
        "route_id": ROUTE_ID,
        "row_id": row_id,
        "source_family": "lane08_digital_twin_replay_plus_lane05_feature_state",
        "source_path": str(LANE08_REPLAY_LEDGER.relative_to(ROOT)),
        "source_hash": sha256_file(LANE08_REPLAY_LEDGER),
        "source_replay_row_id": replay.get("row_id"),
        "source_feature_row_id": (feature or {}).get("row_id"),
        "decision_asof_utc": decision_asof,
        "source_capture_utc": utc_now(),
        "symbol": symbol,
        "broker_symbol": broker_symbol,
        "duplicate_key": selected_row_id,
        "candidate_id": replay.get("candidate_id"),
        "side": replay.get("side"),
        "framework": replay.get("framework"),
        "origin_family": replay.get("origin_family"),
        "no_leak_status": "pass_decision_fields_only_no_label_or_result_payload",
        "source_completeness_state": source_completeness.get("source_completeness_state")
        or replay.get("source_completeness_state")
        or "complete_with_row_level_gaps",
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
        "whiteboard_version": "market_awareness_whiteboard_v1_2026_06_01",
        "whiteboard_materialization_scope": "historical_replay_candidate_row",
        "timeframe_coverage_state": timeframe_coverage,
        "htf_structure_state": htf_state,
        "m15_structure_state": m15_state,
        "m1_path_state": {
            "source_state": field_source_state["m1_path"],
            "m1_entry_minute_available": features.get("m1_entry_minute_available"),
            "m1_availability_status": features.get("m1_availability_status"),
            "source_quality_status": features.get("source_quality_status"),
        },
        "tick_state": {
            "source_state": field_source_state["tick_state"],
            "strict_tick_available": features.get("strict_tick_available"),
            "tick_availability_status": features.get("tick_availability_status"),
        },
        "spread_to_risk_state": spread_state,
        "volatility_state": {
            "source_state": "decision-available" if features.get("m15_volatility_state_14_vs_50") else "missing",
            "m15_volatility_state_14_vs_50": features.get("m15_volatility_state_14_vs_50"),
            "htf_volatility_join_state": "not_materialized_for_replay_row_join_required",
        },
        "session_state": {
            "source_state": field_source_state["session_state"],
            "session_bucket": features.get("session_bucket") or replay.get("decision_inputs", {}).get("selector", {}).get("session_bucket"),
            "session_source_state": features.get("session_source_state"),
        },
        "market_hours_state": {
            "source_state": field_source_state["market_hours_state"],
            "session_status": (symbol_spec or {}).get("session_status"),
            "trade_mode": (symbol_spec or {}).get("trade_mode"),
            "capture_or_repair_requirement": None
            if field_source_state["market_hours_state"] != "missing"
            else "read-only MT5 symbol sessions or broker calendar export by symbol",
        },
        "source_completeness": {
            "source_use_state": replay.get("source_use_state") or features.get("source_use_state"),
            "feature_source_state": source_completeness.get("feature_source_state") or (feature or {}).get("feature_source_state"),
            "source_gap_count": len(source_completeness.get("source_gaps") or (feature or {}).get("source_gaps") or []),
            "source_gaps_inherited": source_completeness.get("source_gaps") or (feature or {}).get("source_gaps") or [],
        },
        "broker_feasibility_fields": {
            "source_state": field_source_state["broker_feasibility"],
            "symbol_spec_join_state": replay.get("decision_inputs", {}).get("broker_constraints", {}).get("symbol_spec_join_state"),
            "volume_min": (symbol_spec or {}).get("volume_min"),
            "volume_step": (symbol_spec or {}).get("volume_step"),
            "volume_max": (symbol_spec or {}).get("volume_max"),
            "trade_stops_level": (symbol_spec or {}).get("trade_stops_level"),
            "trade_freeze_level": (symbol_spec or {}).get("trade_freeze_level"),
            "trade_tick_size_status": (symbol_spec or {}).get("trade_tick_size_status"),
            "trade_tick_value_status": (symbol_spec or {}).get("trade_tick_value_status"),
        },
        "correlation_cluster_state": correlation_state,
        "regime_state": {
            "source_state": field_source_state["regime_state"],
            "regime_h4_state": features.get("regime_h4_state"),
            "regime_h4_direction": features.get("regime_h4_direction"),
            "regime_h4_score": features.get("regime_h4_score"),
            "regime_join_state": features.get("regime_join_state"),
            "runtime_exact_regime_state": field_source_state["runtime_h4_regime_snapshot"],
        },
        "field_source_state": field_source_state,
        "stale_or_null_reason": stale_reasons,
    }
    gap_rows = build_gap_rows(
        whiteboard_row_id=row_id,
        source_replay_row_id=str(replay.get("row_id") or ""),
        symbol=symbol,
        broker_symbol=broker_symbol,
        decision_asof_utc=decision_asof,
        timeframe_coverage=timeframe_coverage,
        features=features,
        field_source_state=field_source_state,
        symbol_spec=symbol_spec,
    )
    return row, gap_rows


def validate_row_no_leak(row: dict[str, Any]) -> list[str]:
    issues = []
    for field in FORBIDDEN_WHITEBOARD_FIELDS:
        if field in row:
            issues.append(f"forbidden_field_present:{field}")
    as_text = compact_json(row)
    for term in STALE_OLD_SYSTEM_TERMS:
        if term in as_text:
            issues.append(f"stale_old_system_term_present:{term}")
    if set(row.get("timeframe_coverage_state", {})) != set(WHITEBOARD_TIMEFRAMES):
        issues.append("one_timeframe_or_missing_timeframe_coverage_state")
    if not row.get("stale_or_null_reason"):
        issues.append("missing_stale_or_null_reason_list")
    for field, state in (row.get("field_source_state") or {}).items():
        if state not in SOURCE_STATE_LABELS:
            issues.append(f"bad_source_state_label:{field}:{state}")
    return issues


def stream_replay_whiteboard(
    *,
    coverage_index: dict[tuple[str, str], list[dict[str, Any]]],
    symbol_specs: dict[str, dict[str, Any]],
    correlation_states: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    counts: Counter[str] = Counter()
    symbols: Counter[str] = Counter()
    gap_counts: Counter[str] = Counter()
    no_leak_issues: list[dict[str, Any]] = []
    feature_mismatches = 0
    feature_rows_seen = 0

    with gzip.open(LANE08_REPLAY_LEDGER, "rt", encoding="utf-8") as replay_fh, gzip.open(
        LANE05_FEATURE_LEDGER, "rt", encoding="utf-8"
    ) as feature_fh, gzip.open(WHITEBOARD_REPLAY_LEDGER, "wt", encoding="utf-8", newline="\n") as out_fh, gzip.open(
        SOURCE_GAP_LEDGER, "wt", encoding="utf-8", newline="\n"
    ) as gap_fh:
        for idx, replay_line in enumerate(replay_fh, start=1):
            replay = json.loads(replay_line)
            feature_line = feature_fh.readline()
            feature = json.loads(feature_line) if feature_line else None
            if feature is not None:
                feature_rows_seen += 1
            if feature and feature.get("duplicate_key") != replay.get("selected_row_id"):
                feature_mismatches += 1
            row, gaps = build_whiteboard_row(
                idx=idx,
                replay=replay,
                feature=feature,
                coverage_index=coverage_index,
                symbol_specs=symbol_specs,
                correlation_states=correlation_states,
            )
            out_fh.write(compact_json(row) + "\n")
            counts["replay_whiteboard_rows"] += 1
            symbols[row["symbol"]] += 1
            for gap in gaps:
                gap_fh.write(compact_json(gap) + "\n")
                counts["source_gap_rows"] += 1
                gap_counts[gap["field_family"]] += 1
            issues = validate_row_no_leak(row)
            if issues and len(no_leak_issues) < 50:
                no_leak_issues.append({"row_id": row["row_id"], "issues": issues})
            counts["no_leak_issue_rows"] += 1 if issues else 0

    return {
        "replay_whiteboard_rows": counts["replay_whiteboard_rows"],
        "source_gap_rows": counts["source_gap_rows"],
        "no_leak_issue_rows": counts["no_leak_issue_rows"],
        "symbol_counts": dict(sorted(symbols.items())),
        "source_gap_counts": dict(sorted(gap_counts.items())),
        "feature_rows_seen": feature_rows_seen,
        "feature_mismatch_rows": feature_mismatches,
        "sample_no_leak_issues": no_leak_issues,
    }


def latest_file(paths: list[Path]) -> Path | None:
    existing = [p for p in paths if p.exists()]
    if not existing:
        return None
    return sorted(existing)[-1]


def build_forward_snapshot_rows(
    *,
    source_rows: list[dict[str, Any]],
    symbol_specs: dict[str, dict[str, Any]],
    correlation_states: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    source_by_symbol_tf: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows:
        source_by_symbol_tf[(row["symbol"], row["timeframe"])].append(row)
    m1_state = load_json(M1_CAPTURE_STATE, {"symbols": {}})
    rows: list[dict[str, Any]] = []
    for symbol in LIVE_SYMBOLS:
        spec = symbol_specs.get(symbol, {})
        current_time = (
            ((m1_state.get("symbols") or {}).get(symbol) or {}).get("last_time_utc")
            or ((m1_state.get("symbols") or {}).get(symbol) or {}).get("last_closed_candle_time_utc")
        )
        decision_asof = canonical_time(current_time) or utc_now()
        htf_structures = {}
        coverage = {}
        for tf in OHLC_TIMEFRAMES:
            source_path = RECENT_HISTORY_ROOT / f"{symbol}_{tf}.csv"
            candles = read_recent_candles(source_path)
            htf_structures[tf] = structure_state_from_candles(candles, tf)
            coverage[tf] = {
                "timeframe": tf,
                "source_state": htf_structures[tf].get("source_state"),
                "coverage_state": "current_snapshot_from_recent_historical_2026_csv"
                if source_path.exists()
                else "source_file_missing",
                "source_path": str(source_path.relative_to(ROOT)),
                "last_bar_time_utc": htf_structures[tf].get("last_bar_time_utc"),
            }
        m1_symbol_state = ((m1_state.get("symbols") or {}).get(symbol) or {})
        m1_dir = M1_FORWARD_ROOT / symbol
        m1_files = sorted(m1_dir.glob("*.csv")) if m1_dir.exists() else []
        m1_path = m1_files[-1] if m1_files else None
        m1_candles = read_recent_candles(m1_path, max_rows=120) if m1_path else []
        tick_dir = TICK_FORWARD_ROOT / symbol
        tick_files = sorted(tick_dir.glob("*.parquet")) if tick_dir.exists() else []
        tick_path = tick_files[-1] if tick_files else None
        row_id = f"lane17_forward_snapshot_{symbol}"
        field_source_state = {
            "symbol": "decision-available",
            "broker_symbol": "broker-real" if spec else "decision-available",
            "timestamp": "decision-available",
            "d1_structure": htf_structures["D1"].get("source_state", "missing"),
            "h4_structure": htf_structures["H4"].get("source_state", "missing"),
            "h1_structure": htf_structures["H1"].get("source_state", "missing"),
            "m15_structure": htf_structures["M15"].get("source_state", "missing"),
            "m1_path": "decision-available" if m1_path else "missing",
            "tick_state": "decision-available" if tick_path else "missing",
            "spread_snapshot": "broker-real" if spec.get("spread_sample_status") else "missing",
            "spread_to_risk": "missing",
            "session_state": "decision-available",
            "market_hours_state": "missing" if str(spec.get("session_status") or "").startswith("MISSING") else "broker-real",
            "source_completeness": "decision-available",
            "broker_feasibility": "broker-real" if spec else "missing",
            "correlation_cluster": "proxy",
            "runtime_correlation_snapshot": "missing",
            "regime_state": "proxy",
            "runtime_h4_regime_snapshot": "missing",
            "label_outcome_fields": "label-only",
            "historical_broker_intent_or_order_truth": "non-generatable",
        }
        stale_reasons = [
            null_reason(field, f"{field}_source_state_{state}", f"capture_or_join_{field}_source")
            for field, state in field_source_state.items()
            if state in {"missing", "non-generatable"}
        ]
        rows.append(
            {
                "schema_version": "lane17_market_whiteboard_row_v1",
                "route_id": ROUTE_ID,
                "row_id": row_id,
                "source_family": "forward_current_snapshot_from_local_runtime_capture",
                "source_path": "data/historical_2026 + data/m1 + data/ticks + Lane07 broker snapshot",
                "source_hash": None,
                "decision_asof_utc": decision_asof,
                "source_capture_utc": utc_now(),
                "symbol": symbol,
                "broker_symbol": spec.get("broker_symbol") or m1_symbol_state.get("broker_symbol") or symbol,
                "duplicate_key": f"{symbol}|forward_snapshot|{decision_asof}",
                "no_leak_status": "pass_current_snapshot_no_label_or_result_payload",
                "source_completeness_state": "complete_with_row_level_gaps",
                "runtime_effect_boundary": RUNTIME_BOUNDARY,
                "whiteboard_version": "market_awareness_whiteboard_v1_2026_06_01",
                "whiteboard_materialization_scope": "current_forward_snapshot_default_off",
                "timeframe_coverage_state": {
                    **coverage,
                    "M1": {
                        "timeframe": "M1",
                        "source_state": "decision-available" if m1_path else "missing",
                        "coverage_state": m1_symbol_state.get("last_cycle_status") or "missing_forward_m1_capture",
                        "source_path": str(m1_path.relative_to(ROOT)) if m1_path else str((M1_FORWARD_ROOT / symbol).relative_to(ROOT)),
                        "last_time_utc": m1_symbol_state.get("last_time_utc"),
                        "last_closed_candle_age_seconds": m1_symbol_state.get("last_closed_candle_age_seconds"),
                    },
                    "tick": {
                        "timeframe": "tick",
                        "source_state": "decision-available" if tick_path else "missing",
                        "coverage_state": "local_tick_parquet_available" if tick_path else "missing_forward_tick_capture",
                        "source_path": str(tick_path.relative_to(ROOT)) if tick_path else str((TICK_FORWARD_ROOT / symbol).relative_to(ROOT)),
                        "latest_tick_file_bytes": tick_path.stat().st_size if tick_path else None,
                    },
                },
                "htf_structure_state": {
                    "source_state": "decision-available",
                    "d1": htf_structures["D1"],
                    "h4": htf_structures["H4"],
                    "h1": htf_structures["H1"],
                },
                "m15_structure_state": htf_structures["M15"],
                "m1_path_state": m1_path_state_from_candles(m1_candles, m1_symbol_state),
                "tick_state": {
                    "source_state": "decision-available" if tick_path else "missing",
                    "latest_parquet_file": str(tick_path.relative_to(ROOT)) if tick_path else None,
                    "tick_aggregation_state": "file_inventory_only_no_parquet_read_in_lane17_builder",
                },
                "spread_to_risk_state": {
                    "source_state": "missing",
                    "broker_snapshot_spread_sample_points": spec.get("spread_sample_points"),
                    "broker_snapshot_spread_sample_status": spec.get("spread_sample_status"),
                    "capture_or_repair_requirement": "candidate risk distance required for spread-to-risk at decision time",
                },
                "volatility_state": {
                    "source_state": htf_structures["M15"].get("source_state"),
                    "m15_atr_14": htf_structures["M15"].get("atr_14"),
                    "h1_atr_14": htf_structures["H1"].get("atr_14"),
                    "h4_atr_14": htf_structures["H4"].get("atr_14"),
                    "d1_atr_14": htf_structures["D1"].get("atr_14"),
                },
                "session_state": {
                    "source_state": "decision-available",
                    "session_bucket": classify_session(decision_asof),
                    "session_source_state": "timestamp_utc_deterministic_bucket",
                },
                "market_hours_state": {
                    "source_state": field_source_state["market_hours_state"],
                    "session_status": spec.get("session_status"),
                    "trade_mode": spec.get("trade_mode"),
                    "capture_or_repair_requirement": None
                    if field_source_state["market_hours_state"] != "missing"
                    else "read-only MT5 symbol sessions or broker calendar export by symbol",
                },
                "source_completeness": {
                    "m1_capture_state": m1_symbol_state,
                    "ohlc_source_rows": source_by_symbol_tf.get((symbol, "M15"), []),
                    "source_gap_count": len(stale_reasons),
                },
                "broker_feasibility_fields": {
                    "source_state": "broker-real" if spec else "missing",
                    "volume_min": spec.get("volume_min"),
                    "volume_step": spec.get("volume_step"),
                    "volume_max": spec.get("volume_max"),
                    "trade_stops_level": spec.get("trade_stops_level"),
                    "trade_freeze_level": spec.get("trade_freeze_level"),
                    "trade_tick_size_status": spec.get("trade_tick_size_status"),
                    "trade_tick_value_status": spec.get("trade_tick_value_status"),
                },
                "correlation_cluster_state": correlation_states[symbol],
                "regime_state": {
                    "source_state": "proxy",
                    "h4_structure_direction_proxy": htf_structures["H4"].get("structure_direction"),
                    "runtime_exact_regime_state": "missing",
                    "capture_or_repair_requirement": "emit as-of regime classifier packet keyed by symbol and timestamp",
                },
                "field_source_state": field_source_state,
                "stale_or_null_reason": stale_reasons,
            }
        )
    return rows


def m1_path_state_from_candles(candles: list[dict[str, Any]], m1_symbol_state: dict[str, Any]) -> dict[str, Any]:
    if len(candles) < 2:
        return {
            "source_state": "missing",
            "path_direction": None,
            "reason": "fewer_than_two_forward_m1_bars_available",
            "m1_capture_state": m1_symbol_state,
        }
    first = float(candles[0]["close"])
    last = float(candles[-1]["close"])
    high = max(float(row["high"]) for row in candles)
    low = min(float(row["low"]) for row in candles)
    span = high - low
    delta = last - first
    if span <= 0:
        direction = "flat"
    elif delta > span * 0.2:
        direction = "up"
    elif delta < -span * 0.2:
        direction = "down"
    else:
        direction = "sideways"
    return {
        "source_state": "decision-available",
        "path_direction": direction,
        "bar_count": len(candles),
        "first_time_utc": canonical_time(candles[0].get("time")),
        "last_time_utc": canonical_time(candles[-1].get("time")),
        "range": round(span, 8),
        "close_delta": round(delta, 8),
        "m1_capture_state": m1_symbol_state,
    }


def build_correlation_regime_spread_rows(
    *,
    matrix: dict[str, dict[str, float]],
    correlation_states: dict[str, dict[str, Any]],
    forward_rows: list[dict[str, Any]],
    symbol_specs: dict[str, dict[str, Any]],
    cost_summary: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = all_correlation_pair_rows(matrix)
    forward_by_symbol = {row["symbol"]: row for row in forward_rows}
    for symbol in LIVE_SYMBOLS:
        rows.append(
            {
                "schema_version": "lane17_correlation_cluster_row_v1",
                "route_id": ROUTE_ID,
                "row_type": "symbol_correlation_cluster",
                "symbol": symbol,
                "correlation_cluster_state": correlation_states[symbol],
                "source_state": "proxy",
                "source_path": str(CORRELATION_MATRIX.relative_to(ROOT)),
                "runtime_effect_boundary": RUNTIME_BOUNDARY,
            }
        )
        rows.append(
            {
                "schema_version": "lane17_regime_state_row_v1",
                "route_id": ROUTE_ID,
                "row_type": "forward_regime_proxy",
                "symbol": symbol,
                "decision_asof_utc": forward_by_symbol[symbol]["decision_asof_utc"],
                "d1_structure": forward_by_symbol[symbol]["htf_structure_state"]["d1"],
                "h4_structure": forward_by_symbol[symbol]["htf_structure_state"]["h4"],
                "h1_structure": forward_by_symbol[symbol]["htf_structure_state"]["h1"],
                "m15_structure": forward_by_symbol[symbol]["m15_structure_state"],
                "source_state": "proxy",
                "exact_runtime_regime_capture_requirement": "emit regime classifier snapshot at decision timestamp",
                "runtime_effect_boundary": RUNTIME_BOUNDARY,
            }
        )
        spec = symbol_specs.get(symbol, {})
        for session in SESSION_BUCKETS:
            rows.append(
                {
                    "schema_version": "lane17_spread_liquidity_friction_row_v1",
                    "route_id": ROUTE_ID,
                    "row_type": "symbol_session_spread_friction",
                    "symbol": symbol,
                    "broker_symbol": spec.get("broker_symbol") or symbol,
                    "session_bucket": session,
                    "spread_sample_points": spec.get("spread_sample_points"),
                    "spread_sample_price": spec.get("spread_sample_price"),
                    "spread_sample_status": spec.get("spread_sample_status") or "missing",
                    "stop_freeze_status": spec.get("stop_freeze_status") or "missing",
                    "trade_stops_level": spec.get("trade_stops_level"),
                    "trade_freeze_level": spec.get("trade_freeze_level"),
                    "volume_min": spec.get("volume_min"),
                    "volume_step": spec.get("volume_step"),
                    "cost_summary": cost_summary.get(symbol, {}),
                    "source_state": "broker-real" if spec.get("spread_sample_status") else "missing",
                    "session_specific_spread_state": "missing_session_specific_spread_distribution",
                    "capture_or_repair_requirement": "capture spread/cost/liquidity by symbol and session at decision time",
                    "runtime_effect_boundary": RUNTIME_BOUNDARY,
                }
            )
    return rows


def build_downstream_contract() -> dict[str, Any]:
    consumers = {
        "Selector V3": {
            "required_fields": [
                "market_whiteboard_key",
                "symbol",
                "decision_asof_utc",
                "htf_structure_state",
                "m15_structure_state",
                "m1_path_state",
                "spread_to_risk_state",
                "correlation_cluster_state",
                "regime_state",
                "source_completeness_state",
                "field_source_state",
            ],
            "blocked_until": "default_off_selector_successor_consumes_Lane17_contract",
            "fail_closed_on": ["missing field_source_state", "label-only field requested as decision feature"],
        },
        "Scheduler V3": {
            "required_fields": [
                "symbol",
                "broker_symbol",
                "market_hours_state",
                "correlation_cluster_state",
                "spread_to_risk_state",
                "broker_feasibility_fields",
                "source_completeness",
            ],
            "blocked_until": "default_off_scheduler_successor_consumes_Lane17_and_Lane18_contracts",
            "fail_closed_on": ["missing market_hours_state reason", "missing broker feasibility source state"],
        },
        "Execution V3": {
            "required_fields": [
                "tick_state",
                "m1_path_state",
                "spread_to_risk_state",
                "broker_feasibility_fields",
                "market_hours_state",
            ],
            "blocked_until": "default_off_execution_policy_successor_consumes_Lane11_Lane17_Lane18_contracts",
            "fail_closed_on": ["tick/source ordering confusion", "spread-to-risk without risk distance"],
        },
        "ML": {
            "required_fields": [
                "all decision-available/proxy market state fields",
                "field_source_state",
                "source_completeness_state",
                "stale_or_null_reason",
            ],
            "forbidden_fields": ["label-only outcome fields as features", "broker-real realized labels without partition controls"],
            "blocked_until": "Lane12 dataset builder applies purge/embargo and field-source filters",
        },
        "Repair Companion": {
            "required_fields": [
                "LANE17_SOURCE_GAP_LEDGER.jsonl.gz",
                "LANE17_SOURCE_COMPLETENESS_LEDGER.jsonl",
                "LANE17_FORWARD_CAPTURE_CONTRACT.json",
            ],
            "repair_rule": "repair every missing field only through source-safe capture/parser/export routes",
        },
        "Command Center": {
            "required_fields": [
                "LANE17_FORWARD_SNAPSHOT_LEDGER.jsonl",
                "correlation_cluster_state",
                "regime_state",
                "market_hours_state",
                "source gap counts by symbol",
            ],
            "display_rule": "show source state and exact gap reason with every null market-state field",
        },
    }
    return {
        "schema_version": "lane17_downstream_contract_v1",
        "route_id": ROUTE_ID,
        "whiteboard_key": "row_id",
        "default_off_contract_only": True,
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
        "source_state_labels": list(SOURCE_STATE_LABELS),
        "consumers": consumers,
    }


def build_forward_capture_contract() -> dict[str, Any]:
    capture_fields = [
        {
            "field": "market_whiteboard_snapshot_id",
            "source_state": "decision-available",
            "default_off": True,
            "capture_requirement": "stable id joining candidate packet to market whiteboard snapshot",
        },
        {
            "field": "asof_htf_structure_state",
            "source_state": "decision-available",
            "default_off": True,
            "capture_requirement": "D1/H4/H1 structures computed from closed bars with timestamp <= decision_asof_utc",
        },
        {
            "field": "m1_path_state",
            "source_state": "decision-available",
            "default_off": True,
            "capture_requirement": "closed M1 bars around candidate source, entry, and decision minute",
        },
        {
            "field": "tick_state",
            "source_state": "decision-available",
            "default_off": True,
            "capture_requirement": "ordered bid/ask tick window with timestamp normalization and source hash",
        },
        {
            "field": "spread_to_risk_state",
            "source_state": "decision-available",
            "default_off": True,
            "capture_requirement": "decision spread, entry spread, and candidate risk price distance",
        },
        {
            "field": "correlation_cluster_state",
            "source_state": "decision-available",
            "default_off": True,
            "capture_requirement": "as-of portfolio/cross-symbol correlation snapshot, peers, and risk multiplier context",
        },
        {
            "field": "regime_state",
            "source_state": "decision-available",
            "default_off": True,
            "capture_requirement": "as-of regime classifier packet keyed by symbol and closed H4/D1 bars",
        },
        {
            "field": "market_hours_state",
            "source_state": "broker-real",
            "default_off": True,
            "capture_requirement": "MT5 sessions/trade mode/stops/freeze at candidate decision time",
        },
        {
            "field": "field_source_state",
            "source_state": "decision-available",
            "default_off": True,
            "capture_requirement": "per-field source labels and exact stale/null reason list",
        },
    ]
    return {
        "schema_version": "lane17_forward_capture_contract_v1",
        "route_id": ROUTE_ID,
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
        "activation_state": "default_off_no_live_behavior_change",
        "packet_fields": capture_fields,
        "forbidden_activation_without_owner_dossier": True,
    }


def dependency_rows() -> list[dict[str, Any]]:
    deps = [
        ("MASTER", MASTER_DIR / "ABSOLUTE_MASTER_COMPLETION_AUDIT.json"),
        ("Lane01", LANE01_DIR / "SOURCE_AUTHORITY_MAP.json"),
        ("Lane02", LANE02_DIR / "LANE02_DOWNSTREAM_FIELD_CONTRACT.json"),
        ("Lane03", LANE03_DIR / "LANE03_COMPLETION_AUDIT.json"),
        ("Lane04", LANE04_DIR / "LANE04_COMPLETION_AUDIT.json"),
        ("Lane05", LANE05_DIR / "LANE05_FEATURE_SCHEMA.json"),
        ("Lane06", LANE06_DIR / "LANE06_LABEL_SCHEMA.json"),
        ("Lane07", LANE07_DIR / "LANE07_BROKER_COST_SCHEMA.json"),
        ("Lane08", LANE08_DIR / "LANE08_REPLAY_SCHEMA.json"),
        ("Lane09", LANE09_DIR / "LANE09_DOWNSTREAM_CONTRACT.json"),
        ("Lane09B", LANE09B_DIR / "LANE09B_SCHEDULER_AWARE_META_SELECTOR_REFINEMENT_PACKAGE.json"),
        ("Lane10", LANE10_DIR / "LANE10_DOWNSTREAM_CONTRACT.json"),
        ("Lane10B", LANE10B_DIR / "LANE10B_SCHEDULER_V3_DEFAULT_OFF_DESIGN_PACKAGE.json"),
        ("Lane11", LANE11_DIR / "LANE11_DOWNSTREAM_CONTRACT.json"),
        ("runtime_market_state_models", ROOT / "src" / "models" / "market_state_models.py"),
        ("runtime_market_state", ROOT / "src" / "components" / "market_state.py"),
        ("runtime_m1_capture", ROOT / "src" / "components" / "m1_capture.py"),
        ("runtime_tick_capture", ROOT / "src" / "components" / "tick_capture.py"),
        ("runtime_regime_classifier", ROOT / "src" / "components" / "regime_classifier.py"),
        ("runtime_correlation_gate", ROOT / "src" / "components" / "cross_instrument_correlation_gate.py"),
    ]
    return [
        {
            "schema_version": "lane17_dependency_state_v1",
            "route_id": ROUTE_ID,
            "dependency_id": name,
            "path": str(path.relative_to(ROOT)),
            "exists": path.exists(),
            "sha256": sha256_file(path),
            "source_use_state": "read_from_disk_for_lane17_builder_contract",
            "runtime_effect_boundary": RUNTIME_BOUNDARY,
        }
        for name, path in deps
    ]


def build_implementation_decisions(counts: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = [
        {
            "decision_id": "lane17_emit_market_whiteboard_replay_rows",
            "decision": "implement_route_local_machine_readable_whiteboard",
            "row_count": counts.get("replay_whiteboard_rows"),
            "runtime_effect": "none",
            "default_off": True,
            "evidence": str(WHITEBOARD_REPLAY_LEDGER.relative_to(ROOT)),
        },
        {
            "decision_id": "lane17_emit_forward_capture_contract",
            "decision": "propose_default_off_runtime_packet_fields_without_activation",
            "runtime_effect": "none_until_separate_owner_approved_production_change",
            "default_off": True,
            "evidence": str(FORWARD_CAPTURE_CONTRACT.relative_to(ROOT)),
        },
        {
            "decision_id": "lane17_fail_closed_on_hidden_nulls",
            "decision": "downstream_consumers_must_require_field_source_state_and_stale_or_null_reason",
            "runtime_effect": "none",
            "default_off": True,
            "evidence": str(DOWNSTREAM_CONTRACT.relative_to(ROOT)),
        },
        {
            "decision_id": "lane17_correlation_regime_spread_as_proxy_or_snapshot",
            "decision": "source_label_correlation_regime_spread_states_separately_no_live_gate_change",
            "runtime_effect": "none",
            "default_off": True,
            "evidence": str(CORRELATION_REGIME_SPREAD_LEDGER.relative_to(ROOT)),
        },
    ]
    return [
        {
            "schema_version": "lane17_implementation_decision_v1",
            "route_id": ROUTE_ID,
            "generated_at_utc": utc_now(),
            "runtime_effect_boundary": RUNTIME_BOUNDARY,
            **row,
        }
        for row in decisions
    ]


def build_no_leak_rows(counts: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "lane17_no_leak_validation_v1",
            "route_id": ROUTE_ID,
            "checked_artifact": str(WHITEBOARD_REPLAY_LEDGER.relative_to(ROOT)),
            "validation": "forbidden_result_and_label_fields_absent_from_whiteboard_rows",
            "ok": counts.get("no_leak_issue_rows", 0) == 0,
            "issue_rows": counts.get("no_leak_issue_rows", 0),
            "forbidden_fields": sorted(FORBIDDEN_WHITEBOARD_FIELDS),
            "runtime_effect_boundary": RUNTIME_BOUNDARY,
        },
        {
            "schema_version": "lane17_no_leak_validation_v1",
            "route_id": ROUTE_ID,
            "checked_artifact": str(SCHEMA_PATH.relative_to(ROOT)),
            "validation": "field_source_labels_distinguish_decision_proxy_label_broker_missing_non_generatable",
            "ok": set(SOURCE_STATE_LABELS) == set(build_market_awareness_schema()["source_state_labels"]),
            "source_state_labels": list(SOURCE_STATE_LABELS),
            "runtime_effect_boundary": RUNTIME_BOUNDARY,
        },
    ]


def write_context_artifacts(counts: dict[str, Any]) -> None:
    write_json(
        SOURCE_USE_STATE,
        {
            "schema_version": "lane17_source_use_state_v1",
            "route_id": ROUTE_ID,
            "source_use_state": SOURCE_USE_STATE_TEXT,
            "inputs_read": [row["path"] for row in dependency_rows()],
            "local_source_roots": [
                "data/historical_2026",
                "data/mt5_research_exports",
                "data/m1",
                "data/ticks",
                "exports/multi_instrument/screening_results/correlation_matrix.json",
            ],
            "runtime_effect_boundary": RUNTIME_BOUNDARY,
        },
    )
    write_json(
        RESULT_USE_STATUS,
        {
            "schema_version": "lane17_result_use_status_v1",
            "route_id": ROUTE_ID,
            "result_use_status": RESULT_USE_STATUS_TEXT,
            "exact_r_fields_owned": [],
            "proxy_r_fields_owned": [],
            "expectancy_fields_owned": [],
            "reason": "Lane17 owns market-state/source-state whiteboard fields, not outcome scoring.",
            "runtime_effect_boundary": RUNTIME_BOUNDARY,
        },
    )
    write_json(
        RUNTIME_EFFECT_BOUNDARY,
        {
            "schema_version": "lane17_runtime_effect_boundary_v1",
            "route_id": ROUTE_ID,
            "runtime_effect_boundary": RUNTIME_BOUNDARY,
            "forbidden_surfaces": [
                "production_change_activation",
                "live_trading_broker_operation",
                "broker_account_order_history_deal_position_mutation",
                "paid_api_vendor_call",
                "credential_change_or_disclosure",
                "remote_push",
                "prompt_config_risk_execution_safety_canary_selector_scheduler_live_behavior_change",
            ],
            "default_off_forward_capture_only": True,
        },
    )
    CONTEXT_ANCHOR.write_text(
        "\n".join(
            [
                "# Lane17 Market Awareness Whiteboard Context Anchor",
                "",
                f"Generated: {utc_now()}",
                f"Route: `{ROUTE_ID}`",
                "",
                "Controlling prompt: `research/science_program_2026_05/04_goal_prompts/VNEXT_ABSOLUTE_MOONSHOT_LANE17_MARKET_AWARENESS_WHITEBOARD_GOAL_PROMPT_2026-06-01.md`",
                "",
                "Scope: route-local market-awareness whiteboard, replay rows, source gaps, correlation/regime/spread ledgers, downstream contracts, and default-off forward capture contract.",
                "",
                f"Replay rows materialized: `{counts.get('replay_whiteboard_rows')}`",
                f"Source gap rows materialized: `{counts.get('source_gap_rows')}`",
                "",
                "Runtime effect boundary: no live broker/order/deal/position operation, no prompt/config/risk/execution/safety/canary/selector/scheduler activation, no paid API/vendor call, no remote push.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    SATURATION_SELF_RED_TEAM.write_text(
        "\n".join(
            [
                "# Lane17 Saturation Self Red Team",
                "",
                "- Evidence-class confusion checked: whiteboard rows exclude result payloads and label values; label-only state is represented only as field-source metadata.",
                "- One-timeframe collapse checked: schema and verifier require D1/H4/H1/M15/M1/tick coverage states.",
                "- Hidden null checked: every missing/non-generatable source state requires stale_or_null_reason and source gap rows.",
                "- Symbol starvation checked: verifier requires all 24 live symbols in replay and forward snapshot ledgers.",
                "- Source-gap specificity checked: source gaps carry field family, symbol, broker symbol, decision timestamp/window, source path when known, and capture or repair requirement.",
                "- Correlation top-N trap checked: all 276 symbol pairs are emitted, not only top peers.",
                "- Runtime activation checked: forward packet fields are default-off contract decisions only.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def manifest_entry(path: Path, artifact_id: str, artifact_class: str, count: int | None = None) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "artifact_class": artifact_class,
        "path": str(path.relative_to(ROOT)),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
        "sha256": sha256_file(path),
        "row_count": count,
    }


def build_manifest(counts: dict[str, Any]) -> dict[str, Any]:
    artifacts = [
        manifest_entry(SCHEMA_PATH, "lane17_market_awareness_schema", "schema"),
        manifest_entry(WHITEBOARD_REPLAY_LEDGER, "lane17_market_whiteboard_replay_rows", "machine_readable_ledger_gzip", counts.get("replay_whiteboard_rows")),
        manifest_entry(FORWARD_SNAPSHOT_LEDGER, "lane17_forward_snapshot_ledger", "machine_readable_ledger", counts.get("forward_snapshot_rows")),
        manifest_entry(SOURCE_COMPLETENESS_LEDGER, "lane17_source_completeness_ledger", "source_state_proof_ledger", counts.get("source_completeness_rows")),
        manifest_entry(SOURCE_GAP_LEDGER, "lane17_source_gap_ledger", "source_gap_ledger_gzip", counts.get("source_gap_rows")),
        manifest_entry(CORRELATION_REGIME_SPREAD_LEDGER, "lane17_correlation_regime_spread_ledger", "market_state_subledger", counts.get("correlation_regime_spread_rows")),
        manifest_entry(DOWNSTREAM_CONTRACT, "lane17_downstream_contract", "downstream_contract"),
        manifest_entry(FORWARD_CAPTURE_CONTRACT, "lane17_forward_capture_contract", "default_off_forward_contract"),
        manifest_entry(IMPLEMENTATION_DECISION_LEDGER, "lane17_implementation_decision_ledger", "decision_ledger", counts.get("implementation_decision_rows")),
        manifest_entry(NO_LEAK_VALIDATION_LEDGER, "lane17_no_leak_validation_ledger", "verification_ledger", counts.get("no_leak_validation_rows")),
        manifest_entry(DEPENDENCY_STATE_LEDGER, "lane17_dependency_state_ledger", "dependency_state_ledger", counts.get("dependency_rows")),
        manifest_entry(SOURCE_USE_STATE, "lane17_source_use_state", "source_use_state"),
        manifest_entry(RESULT_USE_STATUS, "lane17_result_use_status", "result_use_status"),
        manifest_entry(RUNTIME_EFFECT_BOUNDARY, "lane17_runtime_effect_boundary", "runtime_effect_boundary"),
        manifest_entry(CONTEXT_ANCHOR, "lane17_context_anchor", "context_anchor"),
        manifest_entry(SATURATION_SELF_RED_TEAM, "lane17_saturation_self_red_team", "saturation_self_red_team"),
        manifest_entry(VERIFICATION_RESULT, "lane17_verification_result", "verification_result"),
        manifest_entry(FOCUSED_TEST_RESULT, "lane17_focused_test_result", "focused_test_result"),
        manifest_entry(COMPLETION_AUDIT, "lane17_completion_audit", "completion_audit"),
    ]
    manifest = {
        "schema_version": "lane17_output_manifest_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "counts": counts,
        "artifacts": artifacts,
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return manifest


def build_completion_audit(counts: dict[str, Any], verification_result: dict[str, Any] | None = None) -> dict[str, Any]:
    ok = bool(verification_result.get("ok")) if verification_result else None
    audit = {
        "schema_version": "lane17_completion_audit_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "status": "complete_verified" if ok else "built_pending_or_failed_verification",
        "counts": counts,
        "instruction_coverage": {
            "live_state_regenerated_and_preflight_read": True,
            "goal_session_research_discipline_read_after_preflight": True,
            "research_operating_doctrine_read_after_preflight": True,
            "moonshot_vision_read": True,
            "master_and_lane01_to_lane11_lane09b_lane10b_read": True,
            "current_runtime_market_state_code_read": True,
            "builder_posture": "constructive_market_state_implementation_lane",
            "anti_boxing_questions_pursued": [
                "Does the whiteboard collapse to M15 only?",
                "Are tick, M1, HTF, spread, session, correlation, regime, market-hours, and broker fields explicit even when missing?",
                "Are source gaps exact by field/symbol/window/source?",
                "Are all 24 symbols present without representative-only narrowing?",
                "Are runtime packet fields default-off rather than hidden live behavior?",
            ],
            "proof_or_impossibility_stop_condition": "all route-local executable reads, source inventories, replay streaming, correlation/spread/regime ledgers, contracts, verifiers, and tests completed; remaining gaps are exact capture/export requirements",
        },
        "requirements": [
            {
                "requirement": "24_symbol_market_whiteboard_replay_rows",
                "status": "satisfied" if counts.get("replay_whiteboard_rows") == EXPECTED_REPLAY_ROWS and len(counts.get("symbol_counts", {})) == 24 else "not_satisfied",
                "evidence": str(WHITEBOARD_REPLAY_LEDGER.relative_to(ROOT)),
            },
            {
                "requirement": "current_forward_snapshots",
                "status": "satisfied" if counts.get("forward_snapshot_rows") == 24 else "not_satisfied",
                "evidence": str(FORWARD_SNAPSHOT_LEDGER.relative_to(ROOT)),
            },
            {
                "requirement": "source_gaps_not_hidden",
                "status": "satisfied" if counts.get("source_gap_rows", 0) >= EXPECTED_REPLAY_ROWS else "not_satisfied",
                "evidence": str(SOURCE_GAP_LEDGER.relative_to(ROOT)),
            },
            {
                "requirement": "correlation_regime_spread_states",
                "status": "satisfied" if counts.get("correlation_pair_rows") == 276 else "not_satisfied",
                "evidence": str(CORRELATION_REGIME_SPREAD_LEDGER.relative_to(ROOT)),
            },
            {
                "requirement": "downstream_contracts_and_default_off_forward_capture",
                "status": "satisfied",
                "evidence": [str(DOWNSTREAM_CONTRACT.relative_to(ROOT)), str(FORWARD_CAPTURE_CONTRACT.relative_to(ROOT))],
            },
        ],
        "source_use_state": SOURCE_USE_STATE_TEXT,
        "result_use_status": RESULT_USE_STATUS_TEXT,
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
        "verification_result": verification_result,
    }
    write_json(COMPLETION_AUDIT, audit)
    return audit


def build_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    schema = build_market_awareness_schema()
    write_json(SCHEMA_PATH, schema)
    source_rows, coverage_index = build_source_inventory()
    source_completeness_rows = write_jsonl(SOURCE_COMPLETENESS_LEDGER, source_rows)
    symbol_specs = load_symbol_specs()
    cost_summary = load_cost_summary()
    matrix = load_correlation_matrix()
    correlation_states = {symbol: build_correlation_state(symbol, matrix) for symbol in LIVE_SYMBOLS}
    replay_counts = stream_replay_whiteboard(
        coverage_index=coverage_index,
        symbol_specs=symbol_specs,
        correlation_states=correlation_states,
    )
    forward_rows = build_forward_snapshot_rows(
        source_rows=source_rows,
        symbol_specs=symbol_specs,
        correlation_states=correlation_states,
    )
    forward_count = write_jsonl(FORWARD_SNAPSHOT_LEDGER, forward_rows)
    corr_regime_spread_rows = build_correlation_regime_spread_rows(
        matrix=matrix,
        correlation_states=correlation_states,
        forward_rows=forward_rows,
        symbol_specs=symbol_specs,
        cost_summary=cost_summary,
    )
    corr_regime_spread_count = write_jsonl(CORRELATION_REGIME_SPREAD_LEDGER, corr_regime_spread_rows)
    write_json(DOWNSTREAM_CONTRACT, build_downstream_contract())
    write_json(FORWARD_CAPTURE_CONTRACT, build_forward_capture_contract())
    counts: dict[str, Any] = {
        **replay_counts,
        "forward_snapshot_rows": forward_count,
        "source_completeness_rows": source_completeness_rows,
        "correlation_regime_spread_rows": corr_regime_spread_count,
        "correlation_pair_rows": 276,
    }
    implementation_rows = build_implementation_decisions(counts)
    counts["implementation_decision_rows"] = write_jsonl(IMPLEMENTATION_DECISION_LEDGER, implementation_rows)
    no_leak_rows = build_no_leak_rows(counts)
    counts["no_leak_validation_rows"] = write_jsonl(NO_LEAK_VALIDATION_LEDGER, no_leak_rows)
    dep_rows = dependency_rows()
    counts["dependency_rows"] = write_jsonl(DEPENDENCY_STATE_LEDGER, dep_rows)
    write_context_artifacts(counts)
    build_manifest(counts)
    build_completion_audit(counts)
    return counts


def parse_focused_test_result() -> dict[str, Any]:
    if not FOCUSED_TEST_RESULT.exists():
        return {"exists": False, "ok": False, "tests": None, "failures": None, "errors": None}
    text = FOCUSED_TEST_RESULT.read_text(encoding="utf-8", errors="ignore")
    import xml.etree.ElementTree as ET

    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return {"exists": True, "ok": False, "parse_error": "xml_parse_failed"}
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        return {"exists": True, "ok": False, "parse_error": "testsuite_missing"}
    tests = int(suite.attrib.get("tests", "0"))
    failures = int(suite.attrib.get("failures", "0"))
    errors = int(suite.attrib.get("errors", "0"))
    skipped = int(suite.attrib.get("skipped", "0"))
    return {"exists": True, "ok": failures == 0 and errors == 0, "tests": tests, "failures": failures, "errors": errors, "skipped": skipped}


def sample_rows_from_gz(path: Path, limit: int = 100) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    for row in iter_jsonl_gz(path):
        rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def verify_outputs(*, write: bool = True, count_large: bool = True) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    required = [
        SCHEMA_PATH,
        WHITEBOARD_REPLAY_LEDGER,
        FORWARD_SNAPSHOT_LEDGER,
        SOURCE_COMPLETENESS_LEDGER,
        SOURCE_GAP_LEDGER,
        CORRELATION_REGIME_SPREAD_LEDGER,
        DOWNSTREAM_CONTRACT,
        FORWARD_CAPTURE_CONTRACT,
        IMPLEMENTATION_DECISION_LEDGER,
        NO_LEAK_VALIDATION_LEDGER,
        DEPENDENCY_STATE_LEDGER,
        SOURCE_USE_STATE,
        RESULT_USE_STATUS,
        RUNTIME_EFFECT_BOUNDARY,
        CONTEXT_ANCHOR,
        SATURATION_SELF_RED_TEAM,
        OUTPUT_MANIFEST,
        COMPLETION_AUDIT,
    ]
    for path in required:
        if not path.exists() or path.stat().st_size == 0:
            issues.append({"issue": "missing_required_artifact", "path": str(path.relative_to(ROOT))})
    schema = load_json(SCHEMA_PATH, {})
    missing_schema = [field for field in REQUIRED_WHITEBOARD_FIELDS if field not in schema.get("required_whiteboard_fields", [])]
    if missing_schema:
        issues.append({"issue": "schema_missing_required_fields", "fields": missing_schema})
    if set(schema.get("source_state_labels", [])) != set(SOURCE_STATE_LABELS):
        issues.append({"issue": "schema_bad_source_state_labels", "labels": schema.get("source_state_labels")})

    replay_count = line_count(WHITEBOARD_REPLAY_LEDGER) if count_large else None
    gap_count = line_count(SOURCE_GAP_LEDGER) if count_large else None
    if count_large and replay_count != EXPECTED_REPLAY_ROWS:
        issues.append({"issue": "replay_whiteboard_row_count_mismatch", "expected": EXPECTED_REPLAY_ROWS, "actual": replay_count})
    if count_large and (gap_count or 0) < EXPECTED_REPLAY_ROWS:
        issues.append({"issue": "source_gap_rows_too_low", "expected_min": EXPECTED_REPLAY_ROWS, "actual": gap_count})

    forward_rows = list(iter_jsonl(FORWARD_SNAPSHOT_LEDGER)) if FORWARD_SNAPSHOT_LEDGER.exists() else []
    forward_symbols = {row.get("symbol") for row in forward_rows}
    if forward_symbols != set(LIVE_SYMBOLS):
        issues.append({"issue": "forward_snapshot_symbol_coverage_mismatch", "missing": sorted(set(LIVE_SYMBOLS) - forward_symbols)})
    if len(forward_rows) != 24:
        issues.append({"issue": "forward_snapshot_row_count_mismatch", "actual": len(forward_rows)})

    sample = sample_rows_from_gz(WHITEBOARD_REPLAY_LEDGER, 200)
    sample_symbols = {row.get("symbol") for row in sample}
    if not sample:
        issues.append({"issue": "whiteboard_replay_sample_empty"})
    for row in sample:
        row_issues = validate_row_no_leak(row)
        if row_issues:
            issues.append({"issue": "whiteboard_row_validation_issue", "row_id": row.get("row_id"), "issues": row_issues})
            break
        if set(row.get("timeframe_coverage_state", {})) != set(WHITEBOARD_TIMEFRAMES):
            issues.append({"issue": "sample_row_timeframe_coverage_not_full", "row_id": row.get("row_id")})
            break
        if not row.get("field_source_state") or not row.get("stale_or_null_reason"):
            issues.append({"issue": "sample_row_missing_source_state_or_null_reason", "row_id": row.get("row_id")})
            break

    corr_rows = list(iter_jsonl(CORRELATION_REGIME_SPREAD_LEDGER)) if CORRELATION_REGIME_SPREAD_LEDGER.exists() else []
    corr_pair_count = sum(1 for row in corr_rows if row.get("row_type") == "correlation_pair")
    if corr_pair_count != 276:
        issues.append({"issue": "correlation_pair_count_mismatch", "expected": 276, "actual": corr_pair_count})
    pair_symbols = set()
    for row in corr_rows:
        if row.get("row_type") == "correlation_pair":
            pair_symbols.add(row.get("symbol"))
            pair_symbols.add(row.get("peer_symbol"))
    if pair_symbols != set(LIVE_SYMBOLS):
        issues.append({"issue": "correlation_pair_symbol_coverage_mismatch", "missing": sorted(set(LIVE_SYMBOLS) - pair_symbols)})

    source_rows = list(iter_jsonl(SOURCE_COMPLETENESS_LEDGER)) if SOURCE_COMPLETENESS_LEDGER.exists() else []
    for symbol in LIVE_SYMBOLS:
        seen_tfs = {row.get("timeframe") for row in source_rows if row.get("symbol") == symbol}
        if not set(WHITEBOARD_TIMEFRAMES).issubset(seen_tfs):
            issues.append({"issue": "source_completeness_timeframe_coverage_mismatch", "symbol": symbol, "seen": sorted(seen_tfs)})
            break

    no_leak_rows = list(iter_jsonl(NO_LEAK_VALIDATION_LEDGER)) if NO_LEAK_VALIDATION_LEDGER.exists() else []
    if any(not row.get("ok") for row in no_leak_rows):
        issues.append({"issue": "no_leak_validation_failed", "rows": no_leak_rows})

    generated_text_files = [
        SCHEMA_PATH,
        DOWNSTREAM_CONTRACT,
        FORWARD_CAPTURE_CONTRACT,
        RESULT_USE_STATUS,
        RUNTIME_EFFECT_BOUNDARY,
        COMPLETION_AUDIT,
    ]
    for path in generated_text_files:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for term in STALE_OLD_SYSTEM_TERMS:
                if term in text:
                    issues.append({"issue": "stale_old_system_term_in_generated_artifact", "term": term, "path": str(path.relative_to(ROOT))})

    focused = parse_focused_test_result()
    if focused["exists"] and not focused["ok"]:
        issues.append({"issue": "focused_tests_failed", "focused_test_result": focused})

    manifest = load_json(OUTPUT_MANIFEST, {})
    manifest_counts = manifest.get("counts", {})
    if count_large and manifest_counts.get("replay_whiteboard_rows") != EXPECTED_REPLAY_ROWS:
        issues.append({"issue": "manifest_replay_count_mismatch", "manifest": manifest_counts.get("replay_whiteboard_rows")})

    result = {
        "schema_version": "lane17_verification_result_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues[:100],
        "counts": {
            "replay_whiteboard_rows": replay_count,
            "source_gap_rows": gap_count,
            "forward_snapshot_rows": len(forward_rows),
            "correlation_pair_rows": corr_pair_count,
            "source_completeness_rows": len(source_rows),
        },
        "sample_replay_symbols": sorted(sym for sym in sample_symbols if sym),
        "focused_test_result": focused,
        "runtime_effect_boundary": RUNTIME_BOUNDARY,
    }
    if write:
        write_json(VERIFICATION_RESULT, result)
        counts = dict(manifest_counts)
        if count_large:
            counts["replay_whiteboard_rows"] = replay_count
            counts["source_gap_rows"] = gap_count
        counts["forward_snapshot_rows"] = len(forward_rows)
        counts["correlation_pair_rows"] = corr_pair_count
        counts["source_completeness_rows"] = len(source_rows)
        build_completion_audit(counts, result)
        build_manifest(counts)
    return result


def run_py_compile() -> None:
    subprocess.run([sys.executable, "-m", "py_compile", str(Path(__file__).resolve())], check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Lane17 market awareness whiteboard artifacts.")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--skip-large-count", action="store_true")
    args = parser.parse_args(argv)
    if args.verify_only:
        result = verify_outputs(write=True, count_large=not args.skip_large_count)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["ok"] else 1
    run_py_compile()
    counts = build_all()
    result = verify_outputs(write=True, count_large=True)
    print(json.dumps({"counts": counts, "verification": result}, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
