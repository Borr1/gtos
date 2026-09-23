#!/usr/bin/env python3
"""Standalone displacement event logger (observation-only, zero trading impact).

Detects and logs large candle displacements across the Stage08 broker-native
vNext production symbol surface.
Runs as a separate process — shares NO code paths with the trading pipeline.

Usage:
    # One-shot (for Task Scheduler every 15 min):
    python scripts/displacement_logger.py

    # Continuous mode (runs forever, checks every 60s):
    python scripts/displacement_logger.py --continuous

Output: shadow_logs/displacement_events.jsonl
State:  shadow_logs/.displacement_state.json (tracks last processed candle)
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.mt5 import create_mt5
from src.safety.runtime_halt import append_runtime_halt_audit, read_runtime_halt_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("displacement_logger")

# --- Configuration ---

OUTPUT_PATH = Path("shadow_logs/displacement_events.jsonl")
STATE_PATH = Path("shadow_logs/.displacement_state.json")
RUNTIME_HALT_CONFIG = {
    "runtime_control": {
        "enabled": True,
        "audit_log_path": "pipeline_state/runtime_control_atomic_halt_audit.jsonl",
    }
}

# Displacement thresholds (body / avg_body over last 20 candles)
THRESHOLD_NOTABLE = 1.5   # displacement_present in market_state.py
THRESHOLD_STRONG = 2.0    # strong move
THRESHOLD_EXTREME = 3.0   # extreme move

# Only log events >= this threshold
LOG_THRESHOLD = THRESHOLD_STRONG

# Instruments and their MT5 symbol names for the Stage08 broker-native vNext
# production surface.
INSTRUMENTS = {
    "AUDJPY": "AUDJPY",
    "AUDUSD": "AUDUSD",
    "BTCUSD": "BTCUSD",
    "CHFJPY": "CHFJPY",
    "ETHUSD": "ETHUSD",
    "EURGBP": "EURGBP",
    "EURJPY": "EURJPY",
    "EURUSD": "EURUSD",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD",
    "GER40": "GER30",
    "JP225": "JP225",
    "NAS100": "NDX100",
    "NZDUSD": "NZDUSD",
    "SPX500": "SPX500",
    "UK100": "UK100",
    "UKOIL_cash": "UKOUSD",
    "US30_cash": "US30",
    "USDCAD": "USDCAD",
    "USDCHF": "USDCHF",
    "USDJPY": "USDJPY",
    "USOIL_cash": "USOUSD",
    "XAGUSD": "XAGUSD",
    "XAUUSD": "XAUUSD",
}

# Kill zone schedule (UTC) — same as agent_config.yaml.
# XAGUSD + NAS100 trade NY only (per agent_config.yaml lines 621-650 +
# 729-740). Both share end_utc 17:00 (extended from 15:30 per Tier 2
# backtest verdicts: NAS100 50.4% cont 1.04 MFE/MAE; XAGUSD 48.6% cont
# 1.02 MFE/MAE).
KILL_ZONES = {
    "AUDJPY": [("tokyo", 0, 0, 3, 0), ("london", 7, 0, 9, 30), ("ny", 13, 0, 15, 30)],
    "AUDUSD": [("tokyo", 0, 0, 3, 0), ("london", 7, 0, 12, 0), ("ny", 13, 0, 15, 30)],
    "BTCUSD": [("off_configured_session", 0, 0, 23, 59)],
    "CHFJPY": [("tokyo", 0, 0, 3, 0), ("london", 7, 0, 9, 30), ("ny", 13, 0, 15, 30)],
    "ETHUSD": [("off_configured_session", 0, 0, 23, 59)],
    "EURGBP": [("london", 7, 0, 12, 0), ("ny", 13, 0, 15, 30)],
    "EURJPY": [("tokyo", 0, 0, 3, 0), ("london", 7, 0, 9, 30), ("ny", 13, 0, 15, 30)],
    "EURUSD": [("london", 7, 0, 12, 0), ("ny", 13, 0, 15, 30)],
    "GBPJPY": [("tokyo", 0, 0, 3, 0), ("london", 7, 0, 9, 30), ("ny", 13, 0, 15, 30)],
    "GBPUSD": [("london", 7, 0, 12, 0), ("ny", 13, 0, 15, 30)],
    "GER40": [("london", 8, 0, 12, 0), ("ny", 14, 0, 19, 0)],
    "JP225": [("tokyo", 0, 0, 3, 0), ("london", 7, 0, 9, 30), ("ny", 13, 0, 15, 30)],
    "NAS100": [("ny", 13, 0, 17, 0)],
    "NZDUSD": [("tokyo", 0, 0, 3, 0), ("london", 7, 0, 12, 0), ("ny", 13, 0, 15, 30)],
    "SPX500": [("ny", 13, 0, 17, 0)],
    "UK100": [("london", 7, 0, 10, 30), ("ny", 13, 0, 15, 30)],
    "UKOIL_cash": [("london", 7, 0, 12, 0), ("ny", 13, 0, 17, 0)],
    "US30_cash": [("london", 8, 0, 10, 30), ("ny", 13, 30, 16, 0)],
    "USDCAD": [("london", 7, 0, 12, 0), ("ny", 13, 0, 15, 30)],
    "USDCHF": [("london", 7, 0, 12, 0), ("ny", 13, 0, 15, 30)],
    "USDJPY": [("tokyo", 0, 0, 3, 0), ("london", 7, 0, 9, 30), ("ny", 13, 0, 15, 30)],
    "USOIL_cash": [("london", 7, 0, 12, 0), ("ny", 13, 0, 17, 0)],
    "XAGUSD": [("london", 7, 0, 10, 30), ("ny", 13, 0, 17, 0)],
    "XAUUSD": [("london", 7, 0, 10, 30), ("ny", 13, 0, 17, 0)],
}

TF_M15 = 15  # MT5 M15 timeframe constant
LOOKBACK_CANDLES = 30  # pull enough for 20-period avg + recent candles
AVG_BODY_PERIOD = 20

# EET/EEST DST ranges for broker time conversion
DST_RANGES = [
    (date(2024, 3, 31), date(2024, 10, 27)),
    (date(2025, 3, 30), date(2025, 10, 26)),
    (date(2026, 3, 29), date(2026, 10, 25)),
    (date(2027, 3, 28), date(2027, 10, 31)),
]


def eet_offset(d: date) -> int:
    for start, end in DST_RANGES:
        if start <= d <= end:
            return 3
    return 2


def broker_to_utc(broker_ts: int | float, d: date) -> datetime:
    broker_dt = datetime.fromtimestamp(broker_ts, tz=timezone.utc)
    return broker_dt - timedelta(hours=eet_offset(d))


def get_active_kz(symbol: str, utc_time: datetime) -> str:
    """Return which kill zone a UTC time falls in, or 'outside_kz'."""
    h, m = utc_time.hour, utc_time.minute
    t_minutes = h * 60 + m
    for kz_name, sh, sm, eh, em in KILL_ZONES.get(symbol, []):
        start_min = sh * 60 + sm
        end_min = eh * 60 + em
        if start_min <= t_minutes < end_min:
            return kz_name
    return "outside_kz"


def compute_avg_body(candles: list[dict], up_to_index: int) -> float:
    """Average absolute body of the N candles ending at up_to_index (exclusive)."""
    start = max(0, up_to_index - AVG_BODY_PERIOD)
    segment = candles[start:up_to_index]
    if not segment:
        return 0.0
    bodies = [abs(c["close"] - c["open"]) for c in segment]
    return sum(bodies) / len(bodies)


def compute_atr(candles: list[dict], up_to_index: int, period: int = 14) -> float:
    """ATR of the N candles ending at up_to_index (exclusive)."""
    start = max(1, up_to_index - period)
    trs = []
    for i in range(start, up_to_index):
        hl = candles[i]["high"] - candles[i]["low"]
        hpc = abs(candles[i]["high"] - candles[i - 1]["close"])
        lpc = abs(candles[i]["low"] - candles[i - 1]["close"])
        trs.append(max(hl, hpc, lpc))
    return sum(trs) / len(trs) if trs else 0.0


def classify_displacement(ratio: float) -> str:
    if ratio >= THRESHOLD_EXTREME:
        return "extreme"
    if ratio >= THRESHOLD_STRONG:
        return "strong"
    if ratio >= THRESHOLD_NOTABLE:
        return "notable"
    return "normal"


# --- State management ---

def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


# --- Core logic ---

def scan_instrument(
    mt5, symbol_key: str, mt5_symbol: str, state: dict, today: date,
) -> list[dict]:
    """Scan one instrument for displacement events. Returns list of events."""
    candles = mt5.get_candles(mt5_symbol, TF_M15, LOOKBACK_CANDLES)
    if not candles or len(candles) < AVG_BODY_PERIOD + 1:
        logger.debug("Not enough candles for %s (%d)", symbol_key, len(candles) if candles else 0)
        return []

    last_processed = state.get(symbol_key, 0)
    events = []

    for i in range(AVG_BODY_PERIOD, len(candles)):
        c = candles[i]
        candle_ts = c["time"]
        if isinstance(candle_ts, str):
            candle_ts_num = datetime.fromisoformat(candle_ts).timestamp()
        else:
            candle_ts_num = float(candle_ts)

        if candle_ts_num <= last_processed:
            continue

        body = abs(c["close"] - c["open"])
        candle_range = c["high"] - c["low"]
        avg_body = compute_avg_body(candles, i)
        atr = compute_atr(candles, i)

        if avg_body <= 0:
            continue

        ratio = body / avg_body
        if ratio < LOG_THRESHOLD:
            state[symbol_key] = candle_ts_num
            continue

        # Convert broker time to UTC
        utc_time = broker_to_utc(candle_ts_num, today)
        direction = "bullish" if c["close"] > c["open"] else "bearish"
        kz = get_active_kz(symbol_key, utc_time)

        event = {
            "timestamp_utc": utc_time.isoformat(),
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol_key,
            "direction": direction,
            "classification": classify_displacement(ratio),
            "displacement_ratio": round(ratio, 2),
            "body": round(body, 5),
            "avg_body_20": round(avg_body, 5),
            "candle_range": round(candle_range, 5),
            "atr_14": round(atr, 5),
            "body_to_atr": round(body / atr, 2) if atr > 0 else 0,
            "open": c["open"],
            "high": c["high"],
            "low": c["low"],
            "close": c["close"],
            "volume": int(c.get("volume", 0)),
            "kill_zone": kz,
            "day_of_week": utc_time.strftime("%A"),
            "hour_utc": utc_time.hour,
        }
        events.append(event)
        state[symbol_key] = candle_ts_num

    return events


def detect_correlations(all_events: list[dict]) -> list[dict]:
    """Tag events that are correlated (same direction, same candle window).

    Groups events by UTC hour+minute bucket (same M15 candle) and direction.
    If 3+ instruments displace in the same direction in the same candle,
    marks them as correlated.
    """
    # Group by time bucket + direction
    buckets: dict[str, list[dict]] = {}
    for ev in all_events:
        # Round to 15-min bucket
        utc = datetime.fromisoformat(ev["timestamp_utc"])
        bucket_min = (utc.minute // 15) * 15
        key = f"{utc.strftime('%Y-%m-%dT%H')}:{bucket_min:02d}_{ev['direction']}"
        buckets.setdefault(key, []).append(ev)

    for key, group in buckets.items():
        if len(group) >= 2:
            symbols = [e["symbol"] for e in group]
            for ev in group:
                ev["correlated_with"] = [s for s in symbols if s != ev["symbol"]]
                ev["correlation_count"] = len(group)
        else:
            for ev in group:
                ev["correlated_with"] = []
                ev["correlation_count"] = 1

    return all_events


def write_events(events: list[dict]):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


def run_once(mt5) -> int:
    """Scan all instruments once. Returns number of events logged."""
    state = load_state()
    today = date.today()
    all_events = []

    for symbol_key, mt5_symbol in INSTRUMENTS.items():
        try:
            events = scan_instrument(mt5, symbol_key, mt5_symbol, state, today)
            all_events.extend(events)
        except Exception as e:
            logger.error("Error scanning %s: %s", symbol_key, e)

    if all_events:
        all_events = detect_correlations(all_events)
        write_events(all_events)
        for ev in all_events:
            corr = f" [CORRELATED: {', '.join(ev.get('correlated_with', []))}]" if ev.get("correlated_with") else ""
            logger.info(
                "DISPLACEMENT: %s %s %s ratio=%.1f body/ATR=%.1f kz=%s%s",
                ev["symbol"], ev["direction"], ev["classification"],
                ev["displacement_ratio"], ev["body_to_atr"],
                ev["kill_zone"], corr,
            )

    save_state(state)
    return len(all_events)


def main():
    parser = argparse.ArgumentParser(description="Displacement Event Logger")
    parser.add_argument("--continuous", action="store_true",
                        help="Run continuously (check every 60s)")
    args = parser.parse_args()

    halt_snapshot = read_runtime_halt_state(RUNTIME_HALT_CONFIG)
    if halt_snapshot.active:
        append_runtime_halt_audit(
            action="displacement_logger_start",
            snapshot=halt_snapshot,
            context={"component": "displacement_logger"},
            config=RUNTIME_HALT_CONFIG,
        )
        logger.info(
            "%s active; displacement logger exiting before MT5 interaction.",
            halt_snapshot.status,
        )
        return

    # 2026-04-28 sibling-daemon-stability fix: claim a single-instance lock
    # via the shared runtime helper so duplicate watchdog spawns from the
    # cmd.exe-PID confusion era cannot pile up multiple loggers writing
    # the same .displacement_state.json. Best-effort -- if the helper is
    # unavailable for any reason, the logger still runs (matches prior
    # behavior; no fail-closed regression).
    lock_name = "displacement_logger"
    runtime = None
    try:
        from src.components import mt5_daemon_runtime as _runtime
        runtime = _runtime
        marker = "displacement_logger.py"
        if args.continuous:
            acquired, conflicting = runtime.acquire_single_instance_lock(
                lock_name, argv_marker=marker,
            )
            if not acquired:
                logger.warning(
                    "displacement_logger already running (pid=%s) -- exiting cleanly",
                    conflicting,
                )
                return
    except ImportError:
        # Helper not on path -- proceed without single-instance enforcement
        # so we don't introduce a new failure mode.
        pass

    try:
        mt5 = create_mt5("demo")
        if not mt5.connect():
            logger.error("Failed to connect to MT5")
            sys.exit(1)
        logger.info("Connected to MT5 - scanning %d instruments", len(INSTRUMENTS))

        if args.continuous:
            logger.info("Running in continuous mode (60s interval)")
            while True:
                try:
                    n = run_once(mt5)
                    if n:
                        logger.info("Logged %d displacement event(s)", n)
                    if runtime is not None:
                        runtime.write_daemon_heartbeat(
                            lock_name,
                            last_progress_at=datetime.now(timezone.utc),
                            extra={"events_this_cycle": n},
                        )
                except Exception as e:
                    logger.error("Scan cycle error: %s", e)
                time.sleep(60)
        else:
            n = run_once(mt5)
            if n:
                logger.info("Logged %d displacement event(s)", n)
            else:
                logger.info("No displacement events detected")
            mt5.disconnect()
    finally:
        if runtime is not None and args.continuous:
            runtime.release_single_instance_lock(lock_name)


if __name__ == "__main__":
    main()
