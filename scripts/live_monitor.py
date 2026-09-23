#!/usr/bin/env python3
"""
Live monitoring tool for the gold-agent trading system.

Tracks SPRT, CUSUM, autocorrelation, and weekly summaries for
XAUUSD, US30, USDJPY, GBPJPY, GBPUSD on FTMO $100K demo.

Usage:
    python live_monitor.py sprt
    python live_monitor.py cusum
    python live_monitor.py autocorr
    python live_monitor.py weekly
    python live_monitor.py dashboard
    python live_monitor.py trade --result WIN --instrument XAUUSD --r_multiple 1.8
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = PROJECT_ROOT / "knowledge_base"
TRADES_DIR = KB_DIR / "trades"
META_DIR = KB_DIR / "meta"
STATE_FILE = META_DIR / "monitoring_state.json"
HISTORICAL_DIR = PROJECT_ROOT / "data" / "historical"

# ---------------------------------------------------------------------------
# SPRT parameters per instrument
# ---------------------------------------------------------------------------
SPRT_PARAMS = {
    "XAUUSD":    {"h0": 0.357, "h1": 0.620, "alpha": 0.05, "beta": 0.20},
    "US30":      {"h0": 0.345, "h1": 0.585, "alpha": 0.05, "beta": 0.20},
    "USDJPY":    {"h0": 0.400, "h1": 0.758, "alpha": 0.05, "beta": 0.20},
    "GBPJPY":    {"h0": 0.417, "h1": 0.571, "alpha": 0.05, "beta": 0.20},
    "GBPUSD":    {"h0": 0.380, "h1": 0.600, "alpha": 0.05, "beta": 0.20},
    "Portfolio":  {"h0": 0.377, "h1": 0.628, "alpha": 0.05, "beta": 0.20},
}

# CUSUM parameters
CUSUM_ALLOWANCE = 0.05
CUSUM_THRESHOLD = 3.0

# Autocorrelation
AUTOCORR_WINDOW = 20
AUTOCORR_WARNING = 0.03


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------
def load_state() -> dict:
    """Load monitoring state from JSON file."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "trades": [],
        "sprt": {},
        "cusum": {},
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
    }


def save_state(state: dict):
    """Save monitoring state to JSON file."""
    META_DIR.mkdir(parents=True, exist_ok=True)
    state["last_updated"] = datetime.now().isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def get_trades(state: dict) -> list[dict]:
    """Return list of trade records from state."""
    return state.get("trades", [])


def get_trades_for(state: dict, instrument: str) -> list[dict]:
    """Return trades filtered by instrument."""
    return [t for t in get_trades(state) if t["instrument"] == instrument]


# ---------------------------------------------------------------------------
# Wilson confidence interval
# ---------------------------------------------------------------------------
def wilson_ci(wins: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for binomial proportion."""
    if total == 0:
        return (0.0, 0.0)
    p = wins / total
    denom = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denom
    return (max(0.0, center - spread), min(1.0, center + spread))


# ---------------------------------------------------------------------------
# SPRT calculations
# ---------------------------------------------------------------------------
def sprt_boundaries(alpha: float, beta: float) -> tuple[float, float]:
    """Compute SPRT confirm and kill boundaries."""
    confirm = math.log((1 - beta) / alpha)
    kill = math.log(beta / (1 - alpha))
    return confirm, kill


def sprt_update(wins: list[bool], p0: float, p1: float) -> float:
    """Compute cumulative SPRT log-likelihood ratio."""
    cumulative = 0.0
    for w in wins:
        if w:
            cumulative += math.log(p1 / p0)
        else:
            cumulative += math.log((1 - p1) / (1 - p0))
    return cumulative


def sprt_decision_table(p0: float, p1: float, alpha: float, beta: float,
                        current_trades: int, max_lookahead: int = 30) -> str:
    """Generate a forward-looking decision table."""
    confirm_b, kill_b = sprt_boundaries(alpha, beta)
    lines = []
    remaining = max_lookahead - current_trades
    if remaining <= 0:
        remaining = 15

    win_llr = math.log(p1 / p0)
    loss_llr = math.log((1 - p1) / (1 - p0))

    # Find min wins to confirm and max wins before kill in next N trades
    target_n = min(remaining, 15)
    for n_ahead in [target_n]:
        confirm_wins = None
        kill_wins = None
        for w in range(n_ahead + 1):
            test_lambda = w * win_llr + (n_ahead - w) * loss_llr
            if test_lambda >= confirm_b and confirm_wins is None:
                confirm_wins = w
            if test_lambda <= kill_b:
                kill_wins = w
        total_at = current_trades + n_ahead
        parts = []
        if confirm_wins is not None:
            parts.append(f"need >={confirm_wins}W in {n_ahead} to CONFIRM")
        else:
            parts.append(f"cannot confirm in {n_ahead} trades")
        if kill_wins is not None:
            parts.append(f"<={kill_wins}W to KILL")
        else:
            parts.append(f"cannot kill in {n_ahead} trades")
        lines.append(f"  Decision table ({n_ahead} more trades): {', '.join(parts)}")
    return "\n".join(lines)


def run_sprt(state: dict):
    """Run SPRT analysis for all instruments and portfolio."""
    trades = get_trades(state)
    if not trades:
        print("No trades recorded yet. Use 'trade' subcommand to add trades.")
        return

    instruments = list(SPRT_PARAMS.keys())
    print("=" * 72)
    print("SPRT — Sequential Probability Ratio Test")
    print("=" * 72)

    for inst in instruments:
        params = SPRT_PARAMS[inst]
        p0, p1 = params["h0"], params["h1"]
        alpha, beta = params["alpha"], params["beta"]
        confirm_b, kill_b = sprt_boundaries(alpha, beta)

        if inst == "Portfolio":
            inst_trades = trades
        else:
            inst_trades = get_trades_for(state, inst)

        if not inst_trades:
            print(f"\n{inst}: 0 trades | No data")
            continue

        wins_list = [t["result"] == "WIN" for t in inst_trades]
        n = len(wins_list)
        w = sum(wins_list)
        wr = w / n if n > 0 else 0
        lambda_val = sprt_update(wins_list, p0, p1)

        if lambda_val >= confirm_b:
            status = "CONFIRMED — system validated"
        elif lambda_val <= kill_b:
            status = "KILLED — system rejected"
        else:
            status = "CONTINUE"

        lo, hi = wilson_ci(w, n)

        print(f"\n{inst}: {n} trades | {w}W {n - w}L | WR={wr:.1%} "
              f"[{lo:.1%}, {hi:.1%}] | L={lambda_val:+.3f} | Status: {status}")
        print(f"  (confirm at {confirm_b:.3f}, kill at {kill_b:.3f})")
        print(sprt_decision_table(p0, p1, alpha, beta, n))

    print()


# ---------------------------------------------------------------------------
# CUSUM calculations
# ---------------------------------------------------------------------------
def cusum_compute(results: list[bool], expected_wr: float,
                  allowance: float = CUSUM_ALLOWANCE) -> tuple[float, float]:
    """Compute CUSUM deterioration and improvement scores."""
    s_det = 0.0
    s_imp = 0.0
    for r in results:
        actual = 1.0 if r else 0.0
        # Deterioration: accumulates when results worse than expected
        s_det = max(0.0, s_det + (expected_wr - actual) - allowance)
        # Improvement: accumulates when results better than expected
        s_imp = max(0.0, s_imp + (actual - expected_wr) - allowance)
    return s_det, s_imp


def run_cusum(state: dict):
    """Run CUSUM analysis for all instruments."""
    trades = get_trades(state)
    if not trades:
        print("No trades recorded yet. Use 'trade' subcommand to add trades.")
        return

    print("=" * 72)
    print("CUSUM — Cumulative Sum Deterioration / Improvement Tracker")
    print("=" * 72)

    for inst, params in SPRT_PARAMS.items():
        if inst == "Portfolio":
            inst_trades = trades
        else:
            inst_trades = get_trades_for(state, inst)

        if not inst_trades:
            print(f"\n{inst}: No trades")
            continue

        results = [t["result"] == "WIN" for t in inst_trades]
        expected_wr = params["h1"]
        s_det, s_imp = cusum_compute(results, expected_wr)

        det_status = "ALERT" if s_det >= CUSUM_THRESHOLD else "OK"
        imp_status = "OUTPERFORMING" if s_imp >= CUSUM_THRESHOLD else "OK"

        print(f"\n{inst} CUSUM Deterioration: {s_det:.2f} "
              f"(threshold: {CUSUM_THRESHOLD}) — {det_status}")
        print(f"{inst} CUSUM Improvement:    {s_imp:.2f} "
              f"(threshold: {CUSUM_THRESHOLD}) — {imp_status}")

    print()


# ---------------------------------------------------------------------------
# Autocorrelation
# ---------------------------------------------------------------------------
def run_autocorr(state: dict):
    """Compute rolling H1 return autocorrelation from historical data."""
    print("=" * 72)
    print("H1 Return Autocorrelation (lag-1, rolling 20-period)")
    print("=" * 72)

    instruments = {
        "XAUUSD": "XAUUSD_H1.csv",
        "US30": "US30_cash_H1.csv",
        "USDJPY": "USDJPY_H1.csv",
        "GBPJPY": "GBPJPY_H1.csv",
        "GBPUSD": "GBPUSD_H1.csv" if (HISTORICAL_DIR / "GBPUSD_H1.csv").exists() else None,
    }

    for inst, filename in instruments.items():
        if filename is None:
            print(f"\n{inst}: No H1 data file available")
            continue

        filepath = HISTORICAL_DIR / filename
        if not filepath.exists():
            print(f"\n{inst}: {filepath} not found")
            continue

        df = pd.read_csv(filepath, parse_dates=["time"])
        df = df.sort_values("time").reset_index(drop=True)
        df["return"] = df["close"].pct_change()
        df = df.dropna(subset=["return"])

        if len(df) < AUTOCORR_WINDOW + 1:
            print(f"\n{inst}: Insufficient data ({len(df)} rows)")
            continue

        # Rolling autocorrelation
        rolling_ac = df["return"].rolling(AUTOCORR_WINDOW).apply(
            lambda x: x.autocorr(lag=1), raw=False
        )
        rolling_ac = rolling_ac.dropna()

        if len(rolling_ac) == 0:
            print(f"\n{inst}: Could not compute autocorrelation")
            continue

        current = rolling_ac.iloc[-1]

        # Approximate periods: 30 days ~ 30*24/1 = 720 H1 bars
        bars_30d = 720
        bars_90d = 2160

        avg_30d = rolling_ac.iloc[-bars_30d:].mean() if len(rolling_ac) >= bars_30d else rolling_ac.mean()
        avg_90d = rolling_ac.iloc[-bars_90d:].mean() if len(rolling_ac) >= bars_90d else rolling_ac.mean()

        # Trend detection: compare last 30d avg to previous 30d avg
        if len(rolling_ac) >= 2 * bars_30d:
            prev_30d = rolling_ac.iloc[-2 * bars_30d:-bars_30d].mean()
            if abs(avg_30d - prev_30d) < 0.01:
                trend = "STABLE"
            elif avg_30d > prev_30d:
                trend = "RISING"
            else:
                trend = "FALLING"
        else:
            trend = "INSUFFICIENT HISTORY"

        # Warning check: 3 consecutive months below threshold
        warning = ""
        if len(rolling_ac) >= 3 * bars_30d:
            m1 = rolling_ac.iloc[-bars_30d:].mean()
            m2 = rolling_ac.iloc[-2 * bars_30d:-bars_30d].mean()
            m3 = rolling_ac.iloc[-3 * bars_30d:-2 * bars_30d].mean()
            if m1 < AUTOCORR_WARNING and m2 < AUTOCORR_WARNING and m3 < AUTOCORR_WARNING:
                warning = " *** WARNING: Below 0.03 for 3 consecutive months ***"

        print(f"\n{inst} H1 autocorrelation (lag-1, {AUTOCORR_WINDOW}-period rolling):")
        print(f"  Current: {current:.3f}")
        print(f"  30-day avg: {avg_30d:.3f}")
        print(f"  90-day avg: {avg_90d:.3f}")
        print(f"  Trend: {trend}{warning}")
        print(f"  Warning threshold: < {AUTOCORR_WARNING} for 3 consecutive months")

    print()


# ---------------------------------------------------------------------------
# Weekly review
# ---------------------------------------------------------------------------
def run_weekly(state: dict):
    """Generate weekly review combining all metrics."""
    trades = get_trades(state)

    print("=" * 72)
    print(f"WEEKLY REVIEW — {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 72)

    if not trades:
        print("\nNo trades recorded yet. Use 'trade' subcommand to add trades.")
        return

    # --- SPRT summary table ---
    print("\n--- SPRT Status ---")
    print(f"{'Instrument':<12} {'Trades':>6} {'W':>4} {'L':>4} {'WR':>7} "
          f"{'Wilson 95%':>14} {'L':>8} {'Status':<12}")
    print("-" * 72)

    for inst, params in SPRT_PARAMS.items():
        p0, p1 = params["h0"], params["h1"]
        alpha, beta = params["alpha"], params["beta"]
        confirm_b, kill_b = sprt_boundaries(alpha, beta)

        if inst == "Portfolio":
            inst_trades = trades
        else:
            inst_trades = get_trades_for(state, inst)

        n = len(inst_trades)
        if n == 0:
            print(f"{inst:<12} {'—':>6}")
            continue

        wins = [t["result"] == "WIN" for t in inst_trades]
        w = sum(wins)
        wr = w / n
        lo, hi = wilson_ci(w, n)
        lam = sprt_update(wins, p0, p1)

        if lam >= confirm_b:
            status = "CONFIRMED"
        elif lam <= kill_b:
            status = "KILLED"
        else:
            status = "CONTINUE"

        print(f"{inst:<12} {n:>6} {w:>4} {n - w:>4} {wr:>6.1%} "
              f"[{lo:.1%}, {hi:.1%}] {lam:>+8.3f} {status:<12}")

    # --- Rolling 10-trade WR ---
    print("\n--- Rolling 10-Trade Win Rate ---")
    for inst in [k for k in SPRT_PARAMS if k != "Portfolio"]:
        inst_trades = get_trades_for(state, inst)
        if len(inst_trades) < 2:
            continue
        recent = inst_trades[-10:]
        w = sum(1 for t in recent if t["result"] == "WIN")
        n = len(recent)
        print(f"  {inst}: {w}/{n} = {w / n:.1%}")

    # --- CUSUM ---
    print("\n--- CUSUM Status ---")
    for inst, params in SPRT_PARAMS.items():
        if inst == "Portfolio":
            inst_trades = trades
        else:
            inst_trades = get_trades_for(state, inst)
        if not inst_trades:
            continue
        results = [t["result"] == "WIN" for t in inst_trades]
        s_det, s_imp = cusum_compute(results, params["h1"])
        det_flag = " ALERT!" if s_det >= CUSUM_THRESHOLD else ""
        imp_flag = " OUTPERFORM!" if s_imp >= CUSUM_THRESHOLD else ""
        print(f"  {inst}: Det={s_det:.2f}{det_flag}  Imp={s_imp:.2f}{imp_flag}")

    # --- Trade frequency ---
    print("\n--- Trade Frequency ---")
    now = datetime.now()
    this_week = [t for t in trades
                 if datetime.fromisoformat(t["timestamp"]) > now - timedelta(days=7)]
    last_4w = [t for t in trades
               if datetime.fromisoformat(t["timestamp"]) > now - timedelta(days=28)]
    avg_4w = len(last_4w) / 4.0
    print(f"  This week: {len(this_week)} trades")
    print(f"  4-week rolling avg: {avg_4w:.1f} trades/week")

    # --- Equity curve ---
    print("\n--- Equity Curve (Cumulative R) ---")
    cum_r = 0.0
    for t in trades:
        r = t.get("r_multiple", 0)
        if t["result"] == "WIN":
            cum_r += r
        else:
            cum_r -= 1.0  # loss = -1R by default
    print(f"  Cumulative R: {cum_r:+.2f}R over {len(trades)} trades")

    # --- Long vs Short ---
    print("\n--- Direction Breakdown ---")
    longs = [t for t in trades if t.get("direction", "").upper() == "LONG"]
    shorts = [t for t in trades if t.get("direction", "").upper() == "SHORT"]
    if longs:
        lw = sum(1 for t in longs if t["result"] == "WIN")
        print(f"  LONG:  {len(longs)} trades, {lw}W {len(longs) - lw}L "
              f"({lw / len(longs):.1%} WR)")
    if shorts:
        sw = sum(1 for t in shorts if t["result"] == "WIN")
        print(f"  SHORT: {len(shorts)} trades, {sw}W {len(shorts) - sw}L "
              f"({sw / len(shorts):.1%} WR)")

    # --- Correlation exposure ---
    print("\n--- Correlation Exposure Check ---")
    yen_trades = [t for t in trades if t["instrument"] in ("USDJPY", "GBPJPY")]
    if len(yen_trades) >= 2:
        # Check for overlapping open times (if we have open/close timestamps)
        yen_open = [(t["instrument"], t.get("open_time"), t.get("close_time"))
                    for t in yen_trades]
        overlap_found = False
        for i, (inst_a, open_a, close_a) in enumerate(yen_open):
            for j, (inst_b, open_b, close_b) in enumerate(yen_open):
                if i >= j or inst_a == inst_b:
                    continue
                if open_a and open_b and close_a and close_b:
                    oa = datetime.fromisoformat(open_a)
                    ca = datetime.fromisoformat(close_a)
                    ob = datetime.fromisoformat(open_b)
                    cb = datetime.fromisoformat(close_b)
                    if oa < cb and ob < ca:
                        overlap_found = True
                        print(f"  WARNING: {inst_a} and {inst_b} were open simultaneously!")
        if not overlap_found:
            print("  No simultaneous JPY exposure detected.")
    else:
        print("  Insufficient JPY pair trades to check.")

    print()


# ---------------------------------------------------------------------------
# Trade entry
# ---------------------------------------------------------------------------
def run_trade(state: dict, result: str, instrument: str, r_multiple: float,
              direction: Optional[str] = None):
    """Record a new trade and update all trackers."""
    trade = {
        "id": len(state.get("trades", [])) + 1,
        "timestamp": datetime.now().isoformat(),
        "instrument": instrument.upper(),
        "result": result.upper(),
        "r_multiple": r_multiple,
        "direction": direction.upper() if direction else "UNKNOWN",
    }

    if "trades" not in state:
        state["trades"] = []
    state["trades"].append(trade)
    save_state(state)

    print(f"Trade #{trade['id']} recorded: {trade['instrument']} "
          f"{trade['result']} {trade['r_multiple']}R {trade['direction']}")
    print()

    # Show updated status
    run_sprt(state)
    run_cusum(state)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Live monitoring for gold-agent trading system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Subcommands:
  sprt      SPRT sequential test per instrument + portfolio
  cusum     CUSUM deterioration / improvement tracker
  autocorr  H1 return autocorrelation analysis
  weekly    Full weekly review summary
  trade     Record a completed trade
        """,
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("sprt", help="Run SPRT analysis")
    sub.add_parser("cusum", help="Run CUSUM analysis")
    sub.add_parser("autocorr", help="Run autocorrelation analysis")
    sub.add_parser("weekly", help="Generate weekly review")
    sub.add_parser("dashboard", help="Combined dashboard for weekly review")
    sub.add_parser("ob_rate", help="OB retest continuation rate (edge decay)")
    sub.add_parser("resolve_obs", help="Resolve PENDING OB events (needs MT5)")

    trade_p = sub.add_parser("trade", help="Record a trade")
    trade_p.add_argument("--result", required=True, choices=["WIN", "LOSS", "BE"],
                         help="Trade outcome")
    trade_p.add_argument("--instrument", required=True,
                         choices=["XAUUSD", "US30", "USDJPY", "GBPJPY", "GBPUSD"],
                         help="Instrument traded")
    trade_p.add_argument("--r_multiple", type=float, required=True,
                         help="R-multiple (e.g. 1.8 for 1.8R win)")
    trade_p.add_argument("--direction", choices=["LONG", "SHORT"],
                         help="Trade direction (optional)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    state = load_state()

    if args.command == "sprt":
        run_sprt(state)
    elif args.command == "cusum":
        run_cusum(state)
    elif args.command == "autocorr":
        run_autocorr(state)
    elif args.command == "weekly":
        run_weekly(state)
    elif args.command == "trade":
        run_trade(state, args.result, args.instrument, args.r_multiple,
                  getattr(args, "direction", None))
    elif args.command == "dashboard":
        run_dashboard(state)
    elif args.command == "ob_rate":
        run_ob_rate()
    elif args.command == "resolve_obs":
        run_resolve_obs()


def run_resolve_obs():
    """Resolve PENDING OB retest events using MT5 H1 data."""
    import glob
    import MetaTrader5 as _mt5
    from datetime import timedelta

    if not _mt5.initialize():
        print("MT5 initialization failed — cannot resolve OB events.")
        return

    # MT5 symbol mapping (config name -> broker name)
    mt5_map = {"US30_cash": "US30.cash"}

    pattern = str(META_DIR / "ob_retest_events_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        print("No OB retest event files found.")
        _mt5.shutdown()
        return

    print("=" * 60)
    print("RESOLVING PENDING OB RETEST EVENTS")
    print("=" * 60)

    for fp in files:
        symbol = os.path.basename(fp).replace("ob_retest_events_", "").replace(".json", "")
        mt5_sym = mt5_map.get(symbol, symbol)

        try:
            with open(fp) as f:
                events = json.load(f)
        except Exception:
            continue

        modified = False
        for event in events:
            if event.get("outcome") != "PENDING":
                continue

            event_time = datetime.fromisoformat(event["timestamp"])
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)

            hours_since = (datetime.now(timezone.utc) - event_time).total_seconds() / 3600
            if hours_since < 16:
                continue

            rates = _mt5.copy_rates_range(
                mt5_sym, _mt5.TIMEFRAME_H1,
                event_time,
                event_time + timedelta(hours=16),
            )
            if rates is None or len(rates) < 4:
                continue

            entry_price = event["entry_price"]
            ob_type = event.get("ob_type", "bullish")
            zone_height = abs(event["ob_zone_high"] - event["ob_zone_low"])
            if zone_height < 0.01:
                continue

            target = 1.5 * zone_height  # 1.5R continuation target

            continued = False
            for bar in rates:
                if ob_type == "bullish" and bar["high"] - entry_price >= target:
                    continued = True
                    break
                elif ob_type == "bearish" and entry_price - bar["low"] >= target:
                    continued = True
                    break

            event["outcome"] = "CONTINUED" if continued else "FAILED"
            event["resolved_at"] = datetime.now(timezone.utc).isoformat()
            modified = True

        if modified:
            tmp = fp + ".tmp"
            with open(tmp, "w") as f:
                json.dump(events, f, indent=2)
            os.replace(tmp, fp)

        # Report
        resolved = [e for e in events if e.get("outcome") != "PENDING"]
        cont = sum(1 for e in resolved if e["outcome"] == "CONTINUED")
        fail = sum(1 for e in resolved if e["outcome"] == "FAILED")
        pending = sum(1 for e in events if e.get("outcome") == "PENDING")

        if resolved:
            rate = cont / len(resolved) if resolved else 0
            print(f"\n  {symbol}: {len(resolved)} resolved ({cont}C / {fail}F = {rate:.1%})"
                  f", {pending} still pending")
        elif pending:
            print(f"\n  {symbol}: {pending} pending (need 16h+ to resolve)")

    _mt5.shutdown()
    print()


# ---------------------------------------------------------------------------
# Dashboard — single-pane weekly review
# ---------------------------------------------------------------------------
BATCH_BASELINES = {
    "XAUUSD": 0.620,
    "US30": 0.585,
    "USDJPY": 0.758,
    "GBPJPY": 0.571,
}

# Terminal color helpers
_SUPPORTS_COLOR = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _color(text: str, code: str) -> str:
    if _SUPPORTS_COLOR:
        return f"\033[{code}m{text}\033[0m"
    return text


def _red(text: str) -> str:
    return _color(text, "91")


def _yellow(text: str) -> str:
    return _color(text, "93")


def _green(text: str) -> str:
    return _color(text, "92")


def _bold(text: str) -> str:
    return _color(text, "1")


def _section_header(title: str) -> str:
    return f"\n{'─' * 72}\n {_bold(title)}\n{'─' * 72}"


def _trade_dates(trades: list[dict]) -> list[datetime]:
    """Parse trade timestamps, skipping unparseable ones."""
    dates = []
    for t in trades:
        try:
            dates.append(datetime.fromisoformat(t["timestamp"]))
        except (KeyError, ValueError):
            pass
    return dates


def run_dashboard(state: dict):
    """Produce a single clean output combining all metrics for weekly review."""
    trades = get_trades(state)
    instruments = [k for k in SPRT_PARAMS if k != "Portfolio"]
    now = datetime.now()

    print("=" * 72)
    print(_bold(f"  DASHBOARD — Weekly Review  {now.strftime('%Y-%m-%d %H:%M')}"))
    print("=" * 72)

    # ------------------------------------------------------------------
    # SECTION 1: SPRT STATUS
    # ------------------------------------------------------------------
    print(_section_header("SECTION 1: SPRT STATUS"))

    if not trades:
        print("  No trades recorded yet.")
    else:
        header = (f"  {'Instrument':<12} {'N':>4} {'W':>3} {'L':>3} {'WR':>6} "
                  f"{'Λ':>8} {'Status':<12} {'Dist to Boundary'}")
        print(header)
        print("  " + "-" * 68)

        for inst in list(SPRT_PARAMS.keys()):
            params = SPRT_PARAMS[inst]
            p0, p1 = params["h0"], params["h1"]
            alpha, beta = params["alpha"], params["beta"]
            confirm_b, kill_b = sprt_boundaries(alpha, beta)

            if inst == "Portfolio":
                inst_trades = trades
            else:
                inst_trades = get_trades_for(state, inst)

            n = len(inst_trades)
            if n == 0:
                print(f"  {inst:<12} {'—':>4}")
                continue

            wins_list = [t["result"] == "WIN" for t in inst_trades]
            w = sum(wins_list)
            wr = w / n
            lam = sprt_update(wins_list, p0, p1)

            if lam >= confirm_b:
                status = _green("CONFIRMED")
            elif lam <= kill_b:
                status = _red("KILLED")
            else:
                status = "CONTINUE"

            # Distance to boundaries
            dist_confirm = confirm_b - lam
            dist_kill = lam - kill_b
            pct_confirm = max(0.0, dist_confirm / (confirm_b - kill_b)) * 100
            pct_kill = max(0.0, dist_kill / (confirm_b - kill_b)) * 100
            dist_str = f"confirm: {pct_confirm:.0f}%  kill: {pct_kill:.0f}%"

            print(f"  {inst:<12} {n:>4} {w:>3} {n - w:>3} {wr:>5.1%} "
                  f"{lam:>+8.3f} {status:<12} {dist_str}")

    # ------------------------------------------------------------------
    # SECTION 2: ROLLING PERFORMANCE
    # ------------------------------------------------------------------
    print(_section_header("SECTION 2: ROLLING PERFORMANCE"))

    has_any = False
    header2 = f"  {'Instrument':<12} {'Last 10 WR':>10} {'Batch Baseline':>15} {'Delta':>8}"
    print(header2)
    print("  " + "-" * 48)

    for inst in instruments:
        inst_trades = get_trades_for(state, inst)
        baseline = BATCH_BASELINES.get(inst)
        baseline_str = f"{baseline:.1%}" if baseline else "—"

        if len(inst_trades) == 0:
            print(f"  {inst:<12} {'No data':>10} {baseline_str:>15} {'—':>8}")
            continue

        has_any = True
        recent = inst_trades[-10:]
        w = sum(1 for t in recent if t["result"] == "WIN")
        n = len(recent)
        wr = w / n
        wr_str = f"{w}/{n} {wr:.1%}"

        if baseline:
            delta = wr - baseline
            delta_str = f"{delta:+.1%}"
            if delta < -0.10:
                delta_str = _red(delta_str)
            elif delta >= 0:
                delta_str = _green(delta_str)
        else:
            delta_str = "—"

        print(f"  {inst:<12} {wr_str:>10} {baseline_str:>15} {delta_str:>8}")

    if not has_any:
        print("  No trade data yet.")

    # ------------------------------------------------------------------
    # SECTION 3: ALERTS
    # ------------------------------------------------------------------
    print(_section_header("SECTION 3: ALERTS"))

    alerts: list[str] = []

    # Alert: SPRT Λ within 30% of kill boundary
    for inst in list(SPRT_PARAMS.keys()):
        params = SPRT_PARAMS[inst]
        p0, p1 = params["h0"], params["h1"]
        alpha, beta = params["alpha"], params["beta"]
        confirm_b, kill_b = sprt_boundaries(alpha, beta)

        if inst == "Portfolio":
            inst_trades = trades
        else:
            inst_trades = get_trades_for(state, inst)

        if not inst_trades:
            continue

        wins_list = [t["result"] == "WIN" for t in inst_trades]
        lam = sprt_update(wins_list, p0, p1)
        total_range = confirm_b - kill_b
        dist_to_kill = lam - kill_b

        if total_range > 0 and (dist_to_kill / total_range) < 0.30:
            alerts.append(_yellow(
                f"  ⚠ {inst}: SPRT Λ={lam:+.3f} within 30% of kill boundary ({kill_b:.3f})"
            ))

    # Alert: WR below 45% on 10+ trades
    for inst in instruments:
        inst_trades = get_trades_for(state, inst)
        if len(inst_trades) >= 10:
            recent = inst_trades[-10:]
            w = sum(1 for t in recent if t["result"] == "WIN")
            wr = w / len(recent)
            if wr < 0.45:
                alerts.append(_red(
                    f"  🔴 {inst}: Win rate {wr:.1%} on last {len(recent)} trades (below 45%)"
                ))

    # Alert: Trade frequency below 2/week for 2+ consecutive weeks
    trade_dates = _trade_dates(trades)
    if trade_dates:
        # Check last 2 full weeks
        two_weeks_ago = now - timedelta(days=14)
        one_week_ago = now - timedelta(days=7)
        week1_trades = [d for d in trade_dates if two_weeks_ago <= d < one_week_ago]
        week2_trades = [d for d in trade_dates if one_week_ago <= d <= now]
        if len(week1_trades) < 2 and len(week2_trades) < 2 and len(trades) > 0:
            alerts.append(_yellow(
                f"  ⚠ Trade frequency below 2/week for 2 consecutive weeks "
                f"(prev: {len(week1_trades)}, curr: {len(week2_trades)})"
            ))

    # Alert: Zero trades across all instruments for 5+ trading days
    if trade_dates:
        last_trade = max(trade_dates)
        # Approximate trading days as weekdays
        days_since = 0
        check_date = now
        while check_date.date() > last_trade.date():
            if check_date.weekday() < 5:  # Mon-Fri
                days_since += 1
            check_date -= timedelta(days=1)
        if days_since >= 5:
            alerts.append(_red(
                f"  🔴 No trades for {days_since} trading days (last: {last_trade.strftime('%Y-%m-%d')})"
            ))
    elif trades:
        # trades exist but no parseable dates — skip
        pass
    else:
        alerts.append(_yellow("  ⚠ No trades recorded yet."))

    if alerts:
        for a in alerts:
            print(a)
    else:
        print(_green("  ✓ No alerts."))

    # ------------------------------------------------------------------
    # SECTION 4: WEEKLY SUMMARY
    # ------------------------------------------------------------------
    print(_section_header("SECTION 4: WEEKLY SUMMARY"))

    one_week_ago = now - timedelta(days=7)
    week_trades = [t for t in trades
                   if _safe_parse_ts(t.get("timestamp")) and
                   _safe_parse_ts(t["timestamp"]) > one_week_ago]

    week_r = 0.0
    for t in week_trades:
        r = t.get("r_multiple", 0)
        if t["result"] == "WIN":
            week_r += r
        else:
            week_r -= 1.0

    cum_r = 0.0
    for t in trades:
        r = t.get("r_multiple", 0)
        if t["result"] == "WIN":
            cum_r += r
        else:
            cum_r -= 1.0

    print(f"  Trades this week:  {len(week_trades)}")
    print(f"  Week P&L:          {week_r:+.2f}R")
    print(f"  Cumulative P&L:    {cum_r:+.2f}R ({len(trades)} total trades)")

    # ------------------------------------------------------------------
    # SECTION 5: OB CONTINUATION
    # ------------------------------------------------------------------
    print(_section_header("SECTION 5: OB CONTINUATION"))

    import glob as _glob
    ob_pattern = str(META_DIR / "ob_retest_events_*.json")
    ob_files = sorted(_glob.glob(ob_pattern))

    if not ob_files:
        print("  No OB retest event files found.")
    else:
        header5 = f"  {'Instrument':<12} {'Total':>6} {'Resolved':>9} {'Cont. Rate':>11}"
        print(header5)
        print("  " + "-" * 42)

        for fp in ob_files:
            symbol = os.path.basename(fp).replace("ob_retest_events_", "").replace(".json", "")
            try:
                with open(fp) as f:
                    events = json.load(f)
            except Exception:
                continue

            total = len(events)
            continued = sum(1 for e in events if e.get("outcome") == "CONTINUED")
            failed = sum(1 for e in events if e.get("outcome") == "FAILED")
            resolved = continued + failed
            rate_str = f"{continued}/{resolved} = {continued / resolved:.1%}" if resolved > 0 else "—"

            print(f"  {symbol:<12} {total:>6} {resolved:>9} {rate_str:>11}")

    # ------------------------------------------------------------------
    # SECTION 6: EVALUATION DISTRIBUTION
    # ------------------------------------------------------------------
    print(_section_header("SECTION 6: EVALUATION DISTRIBUTION"))

    eval_dir = "knowledge_base/live_evaluations"
    if os.path.exists(eval_dir):
        total_by_sym: dict[str, int] = {}
        cand_by_sym: dict[str, int] = {}
        no_trade_reasons_all: dict[str, int] = {}
        memory_at_candidate: list[int] = []

        for symbol_dir in os.listdir(eval_dir):
            dir_path = os.path.join(eval_dir, symbol_dir)
            if not os.path.isdir(dir_path):
                continue
            total_by_sym[symbol_dir] = 0
            cand_by_sym[symbol_dir] = 0

            for jsonl_file in os.listdir(dir_path):
                if not jsonl_file.endswith(".jsonl"):
                    continue
                with open(os.path.join(dir_path, jsonl_file)) as f:
                    for line in f:
                        try:
                            rec = json.loads(line)
                            total_by_sym[symbol_dir] += 1
                            if rec.get("decision") == "CANDIDATE":
                                cand_by_sym[symbol_dir] += 1
                                mem = rec.get("session_memory_count")
                                if mem is not None:
                                    memory_at_candidate.append(mem)
                            elif rec.get("no_trade_reason"):
                                r = rec["no_trade_reason"][:60]
                                no_trade_reasons_all[r] = no_trade_reasons_all.get(r, 0) + 1
                        except Exception:
                            pass

        print(f"  {'Instrument':<12} {'Evaluations':>12} {'CANDIDATEs':>12} {'Rate':>8}")
        print(f"  {'-' * 44}")
        for sym in sorted(total_by_sym.keys()):
            t = total_by_sym[sym]
            c = cand_by_sym[sym]
            rate = f"{c / t:.1%}" if t > 0 else "—"
            print(f"  {sym:<12} {t:>12} {c:>12} {rate:>8}")

        if memory_at_candidate:
            print(f"\n  Session memory at CANDIDATE time:")
            print(f"    Mean: {sum(memory_at_candidate) / len(memory_at_candidate):.1f} prior evals")
            print(f"    Min: {min(memory_at_candidate)}, Max: {max(memory_at_candidate)}")

        if no_trade_reasons_all:
            print(f"\n  Top 5 NO_TRADE reasons:")
            for reason, count in sorted(no_trade_reasons_all.items(), key=lambda x: -x[1])[:5]:
                print(f"    {count:>4}x {reason}")
    else:
        print("  No evaluation logs found yet.")

    # ------------------------------------------------------------------
    # SECTION 7: DEVIL'S ADVOCATE SHADOW
    # ------------------------------------------------------------------
    print(_section_header("SECTION 7: DEVIL'S ADVOCATE SHADOW"))

    da_scores: list[dict] = []
    for t in state.get("trades", []):
        da = t.get("shadow_da", {})
        max_risk = da.get("max_risk_pct")
        if max_risk is not None:
            da_scores.append({
                "instrument": t.get("instrument", "?"),
                "result": t.get("result", "?"),
                "r_multiple": t.get("r_multiple", 0),
                "max_risk_pct": max_risk,
            })

    if da_scores:
        winners = [d for d in da_scores if d["result"] == "WIN"]
        losers = [d for d in da_scores if d["result"] == "LOSS"]

        w_avg = sum(d["max_risk_pct"] for d in winners) / len(winners) if winners else 0
        l_avg = sum(d["max_risk_pct"] for d in losers) / len(losers) if losers else 0

        print(f"  DA evaluations: {len(da_scores)}")
        print(f"  Winner avg max_risk: {w_avg:.0f}%")
        print(f"  Loser avg max_risk:  {l_avg:.0f}%")
        signal = "losers higher — signal!" if l_avg > w_avg else "no signal"
        print(f"  Gap: {l_avg - w_avg:.0f}pp ({signal})")
    else:
        print("  No DA shadow data yet.")

    print("\n" + "=" * 72)


def _safe_parse_ts(ts) -> Optional[datetime]:
    """Safely parse an ISO timestamp, returning None on failure."""
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def run_ob_rate():
    """Report OB retest continuation rates per instrument."""
    import glob
    pattern = str(META_DIR / "ob_retest_events_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        print("No OB retest events logged yet.")
        return

    print("=" * 60)
    print("OB RETEST CONTINUATION RATE (Edge Decay Monitor)")
    print("=" * 60)
    for fp in files:
        symbol = os.path.basename(fp).replace("ob_retest_events_", "").replace(".json", "")
        try:
            with open(fp) as f:
                events = json.load(f)
        except Exception:
            continue

        total = len(events)
        pending = sum(1 for e in events if e.get("outcome") == "PENDING")
        continued = sum(1 for e in events if e.get("outcome") == "CONTINUED")
        failed = sum(1 for e in events if e.get("outcome") == "FAILED")
        resolved = continued + failed
        rate = continued / resolved if resolved > 0 else 0

        print(f"\n  {symbol}: {total} events ({pending} pending, {resolved} resolved)")
        if resolved > 0:
            print(f"    Continuation rate: {continued}/{resolved} = {rate:.1%}"
                  f"  (batch baseline: ~70%)")
        else:
            print("    No resolved events yet — resolve PENDING events after candle outcomes.")

        # Show most recent 3 events
        recent = events[-3:]
        if recent:
            print("    Recent:")
            for e in recent:
                print(f"      {e['timestamp'][:16]} | {e['ob_type']:>7} "
                      f"{e['ob_zone_low']:.2f}-{e['ob_zone_high']:.2f} | {e['outcome']}")
    print()


if __name__ == "__main__":
    main()
