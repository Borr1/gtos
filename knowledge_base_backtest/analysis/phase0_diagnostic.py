#!/usr/bin/env python3
"""
Phase 0 — Foundation Diagnostic
Does the AI add value over buying at the KZ open when D1 is bullish?
ZERO API calls. Entirely deterministic analysis on existing data.
"""
import sys, json, os
from pathlib import Path
from datetime import date, datetime, timedelta
from collections import defaultdict, Counter
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from scripts.historical_data_loader import parse_tradingview_csv, replay_london_open, replay_ny_open
from src.components.market_state import compute_market_state, detect_swings, identify_structure
from src.components.orchestrator import prescreen_mso

# ═══════════════════════════════════════════════════════════════════════
# 1. LOAD DATA
# ═══════════════════════════════════════════════════════════════════════

print("Loading data...")
HIST = _ROOT / "data" / "historical"
DATA = _ROOT / "data"

# Load candle CSVs
all_candles = {}
for tf in ("D1", "H4", "H1", "M15"):
    csv_path = HIST / f"XAUUSD_{tf}.csv"
    if not csv_path.exists():
        csv_path = DATA / f"XAUUSD_{tf}.csv"
    if csv_path.exists():
        all_candles[tf] = parse_tradingview_csv(csv_path)
        print(f"  {tf}: {len(all_candles[tf])} candles")
    else:
        print(f"  WARNING: No CSV for {tf}")
        all_candles[tf] = []

# Load M15 as DataFrame-like for fast lookups
m15_candles = all_candles["M15"]
m15_by_date = defaultdict(list)
for c in m15_candles:
    d = c["time"][:10]
    m15_by_date[d].append(c)

# Load the 40 AI trades
ai_trades = []
for path in [
    _ROOT / "knowledge_base_backtest/analysis/replay/replay_results.json",
    _ROOT / "knowledge_base_backtest/analysis/supplementary_replay_0_1643.json",
]:
    with open(path) as f:
        ai_trades.extend(json.load(f))
print(f"AI trades loaded: {len(ai_trades)}")

# Check DXY
eurusd_exists = any((DATA / f"EURUSD_{tf}.csv").exists() for tf in ("D1","H4","H1"))
dxy_exists = any((DATA / f"DXY_{tf}.csv").exists() for tf in ("D1","H4","H1"))
print(f"EURUSD data: {'FOUND' if eurusd_exists else 'NOT FOUND'}")
print(f"DXY data: {'FOUND' if dxy_exists else 'NOT FOUND'}")

# ═══════════════════════════════════════════════════════════════════════
# 2. PRE-SCREEN ALL WEEKDAYS
# ═══════════════════════════════════════════════════════════════════════

print("\nRunning pre-screen on all weekdays...")

# Get date range from M15 data
first_date = date.fromisoformat(m15_candles[0]["time"][:10])
last_date = date.fromisoformat(m15_candles[-1]["time"][:10])
print(f"  Date range: {first_date} to {last_date}")

config = {
    "data": {
        "swing_detection_min_bars": {"D1": 2, "H4": 2, "H1": 2, "M15": 2},
        "fvg_min_gap": {"D1": 1.0, "H4": 1.0, "H1": 1.0, "M15": 1.0},
    }
}

# For efficiency: only compute pre-screen using D1+H4 structure at 07:00 UTC each day
# Use the first candle from replay_london_open to get a full raw_data dict
prescreen_results = {}  # date_str -> {passed, reason, d1_dir, h4_dir}
all_weekdays = []

d = first_date + timedelta(days=30)  # Need lookback
end = last_date - timedelta(days=1)

weekdays_checked = 0
weekdays_passed = 0
fail_reasons = Counter()

# Process in batches - only need first candle per KZ for pre-screen
while d <= end:
    if d.weekday() >= 5:  # Skip weekends
        d += timedelta(days=1)
        continue

    ds = d.isoformat()
    all_weekdays.append(ds)

    try:
        # Get first London candle for this date (07:15 UTC)
        gen = replay_london_open(ds, all_candles)
        first_raw = next(gen, None)

        if first_raw is None:
            prescreen_results[ds] = {"passed": False, "reason": "no_data", "d1_dir": "unknown", "h4_dir": "unknown"}
            fail_reasons["no_data"] += 1
            d += timedelta(days=1)
            weekdays_checked += 1
            continue

        # Compute MSO
        mso = compute_market_state(first_raw, config)

        # Run pre-screen
        passed, reason = prescreen_mso(mso)

        d1_dir = mso.timeframes.get("D1").structure.direction if mso.timeframes.get("D1") else "unknown"
        h4_dir = mso.timeframes.get("H4").structure.direction if mso.timeframes.get("H4") else "unknown"

        prescreen_results[ds] = {
            "passed": passed,
            "reason": reason,
            "d1_dir": d1_dir,
            "h4_dir": h4_dir,
        }

        if passed:
            weekdays_passed += 1
        else:
            fail_reasons[reason] += 1

    except Exception as e:
        prescreen_results[ds] = {"passed": False, "reason": f"error:{str(e)[:50]}", "d1_dir": "unknown", "h4_dir": "unknown"}
        fail_reasons[f"error"] += 1

    weekdays_checked += 1
    if weekdays_checked % 50 == 0:
        print(f"  Checked {weekdays_checked} weekdays, {weekdays_passed} passed...")

    d += timedelta(days=1)

print(f"\n  Total weekdays checked: {weekdays_checked}")
print(f"  Pre-screen passing: {weekdays_passed} ({weekdays_passed/weekdays_checked*100:.1f}%)")
print(f"  Pre-screen failing: {weekdays_checked - weekdays_passed}")
print(f"  Fail reasons:")
for reason, count in fail_reasons.most_common(10):
    print(f"    {reason}: {count}")

passing_dates = [ds for ds, r in prescreen_results.items() if r["passed"]]

# ═══════════════════════════════════════════════════════════════════════
# 3. NAIVE BASELINE SIMULATION
# ═══════════════════════════════════════════════════════════════════════

print(f"\nSimulating naive strategies on {len(passing_dates)} passing dates...")

def get_candle_hour(c):
    """Extract hour from candle time (handles both 'T' and space separator)."""
    t = c["time"]
    if "T" in t:
        return int(t[11:13])
    return int(t[11:13])

def get_candle_hhmm(c):
    """Extract HH:MM from candle time."""
    t = c["time"]
    sep = 11 if "T" in t else 11
    return t[sep:sep+5]

def get_session_candles(date_str, start_hour, end_hour):
    """Get M15 candles within a time window for a given date."""
    candles = m15_by_date.get(date_str, [])
    result = []
    for c in candles:
        h = get_candle_hour(c)
        if start_hour <= h < end_hour:
            result.append(c)
    return result

def compute_atr(candles, period=20):
    """Compute ATR from last N candles."""
    if len(candles) < period:
        return None
    trs = []
    for i in range(1, min(period + 1, len(candles))):
        c = candles[-i]
        prev_c = candles[-(i+1)] if i + 1 <= len(candles) else c
        tr = max(
            c["high"] - c["low"],
            abs(c["high"] - prev_c["close"]),
            abs(c["low"] - prev_c["close"]),
        )
        trs.append(tr)
    return np.mean(trs) if trs else None

def simulate_naive_trade(entry_price, sl_price, future_candles, max_hold_candles):
    """Simulate a LONG trade from entry to exit. Returns dict with MFE/MAE/outcome."""
    if not future_candles or entry_price <= sl_price:
        return None

    risk = entry_price - sl_price
    if risk < 0.01:
        return None

    max_fav_r = 0.0
    max_adv_r = 0.0
    max_fav_dollar = 0.0
    max_adv_dollar = 0.0
    sl_hit = False
    tp_hits = {}  # {r_level: candle_index}

    for i, c in enumerate(future_candles[:max_hold_candles]):
        fav_r = (c["high"] - entry_price) / risk
        adv_r = (entry_price - c["low"]) / risk
        fav_d = c["high"] - entry_price
        adv_d = entry_price - c["low"]

        max_fav_r = max(max_fav_r, fav_r)
        max_adv_r = max(max_adv_r, adv_r)
        max_fav_dollar = max(max_fav_dollar, fav_d)
        max_adv_dollar = max(max_adv_dollar, adv_d)

        # SL check
        if c["low"] <= sl_price:
            sl_hit = True
            return {
                "entry": entry_price, "sl": sl_price, "risk": risk,
                "mfe_r": round(max_fav_r, 3), "mae_r": round(max_adv_r, 3),
                "mfe_dollar": round(max_fav_dollar, 2), "mae_dollar": round(max_adv_dollar, 2),
                "final_r": -1.0, "final_dollar": -risk,
                "sl_hit": True, "hold_candles": i + 1,
                "tp_hits": tp_hits,
            }

        # Track TP level hits
        for tp_r in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
            tp_price = entry_price + tp_r * risk
            if tp_r not in tp_hits and c["high"] >= tp_price:
                tp_hits[tp_r] = i

    # Timeout
    last_close = future_candles[min(max_hold_candles - 1, len(future_candles) - 1)]["close"]
    final_r = (last_close - entry_price) / risk
    final_dollar = last_close - entry_price

    return {
        "entry": entry_price, "sl": sl_price, "risk": risk,
        "mfe_r": round(max_fav_r, 3), "mae_r": round(max_adv_r, 3),
        "mfe_dollar": round(max_fav_dollar, 2), "mae_dollar": round(max_adv_dollar, 2),
        "final_r": round(final_r, 3), "final_dollar": round(final_dollar, 2),
        "sl_hit": False, "hold_candles": min(max_hold_candles, len(future_candles)),
        "tp_hits": tp_hits,
    }

# AI trade dates for matching
ai_trade_dates = set(t["date"] for t in ai_trades)
ai_by_date_kz = {}
for t in ai_trades:
    ai_by_date_kz[(t["date"], t["kill_zone"])] = t

# Simulation results
naive_results = []  # All passing dates
matched_results = []  # Only dates where AI traded

processed = 0
for ds in passing_dates:
    candles = m15_by_date.get(ds, [])
    if not candles:
        continue

    # Get direction from pre-screen
    d1_dir = prescreen_results[ds]["d1_dir"]

    for kz in ["london", "ny"]:
        if kz == "london":
            kz_start_h, kz_end_h = 7, 10  # 07:00-09:30 + buffer
            entry_time_prefix = f"{ds} 07:15"
            sl_window_start_h, sl_window_end_h = 0, 7  # Asian session
            hold_end_h = 12  # 2h after KZ end ~11:30
        else:
            kz_start_h, kz_end_h = 13, 16
            entry_time_prefix = f"{ds} 13:15"
            sl_window_start_h, sl_window_end_h = 7, 13  # London session
            hold_end_h = 18

        # Get entry candle (first M15 close in KZ)
        # Time format: YYYY-MM-DDTHH:MM:SSZ
        entry_time_iso = entry_time_prefix.replace(" ", "T") + ":00Z"
        entry_candle = None
        for c in candles:
            if c["time"] == entry_time_iso:
                entry_candle = c
                break

        if entry_candle is None:
            continue

        entry_price = entry_candle["close"]

        # Find global index in M15 array
        entry_global_idx = None
        for gi, gc in enumerate(m15_candles):
            if gc["time"] == entry_candle["time"]:
                entry_global_idx = gi
                break

        if entry_global_idx is None or entry_global_idx < 20:
            continue

        # Strategy 1: Session Low SL
        sl_candles = get_session_candles(ds, sl_window_start_h, sl_window_end_h)
        if not sl_candles:
            continue
        session_low = min(c["low"] for c in sl_candles)

        # Strategy 2: ATR SL
        m15_atr = compute_atr(m15_candles[:entry_global_idx + 1], 20)
        atr_sl = entry_price - 2.0 * m15_atr if m15_atr else session_low

        future = m15_candles[entry_global_idx + 1: entry_global_idx + 1 + 80]  # 80 candles = 20 hours

        # Compute max hold candles (session timeout equivalent)
        # London: entry at 07:15, timeout ~11:30 = ~17 candles
        # NY: entry at 13:15, timeout ~17:30 = ~17 candles
        max_hold = 17  # ~4.25 hours, matches AI system hold period

        # Strategy 1: Session Low SL
        s1 = simulate_naive_trade(entry_price, session_low, future, max_hold)

        # Strategy 2: ATR SL
        s2 = simulate_naive_trade(entry_price, atr_sl, future, max_hold)

        # Strategy 3: Every candle average
        kz_candles = get_session_candles(ds, kz_start_h - (0 if kz == "london" else 6), kz_end_h - (0 if kz == "london" else 6))
        # Actually get KZ candles properly
        if kz == "london":
            kz_candle_list = [c for c in candles if 7 <= get_candle_hour(c) < 10]
        else:
            kz_candle_list = [c for c in candles if 13 <= get_candle_hour(c) < 16]

        s3_results = []
        for kc in kz_candle_list:
            kc_entry = kc["close"]
            # Get future from global M15 list
            kc_gi = None
            for gi2, gc2 in enumerate(m15_candles):
                if gc2["time"] == kc["time"]:
                    kc_gi = gi2
                    break
            kc_future = m15_candles[kc_gi + 1: kc_gi + 1 + 80] if kc_gi else []
            kc_result = simulate_naive_trade(kc_entry, session_low, kc_future, max_hold)
            if kc_result:
                s3_results.append(kc_result)

        s3_avg = None
        if s3_results:
            s3_avg = {
                "mfe_r": np.mean([r["mfe_r"] for r in s3_results]),
                "mae_r": np.mean([r["mae_r"] for r in s3_results]),
                "mfe_dollar": np.mean([r["mfe_dollar"] for r in s3_results]),
                "mae_dollar": np.mean([r["mae_dollar"] for r in s3_results]),
                "final_r": np.mean([r["final_r"] for r in s3_results]),
                "n_candles": len(s3_results),
                "wr_1r": sum(1 for r in s3_results if 1.0 in r.get("tp_hits", {})) / len(s3_results),
            }

        result = {
            "date": ds, "kz": kz, "d1_dir": d1_dir,
            "entry_price": entry_price, "session_low": session_low,
            "strategy1": s1, "strategy2": s2, "strategy3_avg": s3_avg,
            "ai_traded": (ds, kz) in ai_by_date_kz,
        }

        if result["ai_traded"]:
            ai_t = ai_by_date_kz[(ds, kz)]
            result["ai_trade"] = {
                "entry": ai_t["entry_price"],
                "sl": ai_t["stop_loss"],
                "risk": abs(ai_t["entry_price"] - ai_t["stop_loss"]),
                "mfe_r": ai_t["mfe_r"],
                "mae_r": ai_t["mae_r"],
                "r_multiple": ai_t["r_multiple"],
                "outcome": ai_t["outcome"],
                "mfe_dollar": ai_t["mfe_r"] * abs(ai_t["entry_price"] - ai_t["stop_loss"]),
                "mae_dollar": ai_t["mae_r"] * abs(ai_t["entry_price"] - ai_t["stop_loss"]),
                "setup_grade": ai_t.get("setup_grade"),
                "confidence": ai_t.get("confidence_score"),
            }
            matched_results.append(result)

        naive_results.append(result)

    processed += 1
    if processed % 50 == 0:
        print(f"  Processed {processed}/{len(passing_dates)} dates...")

print(f"  Total naive simulations: {len(naive_results)} (trades across {len(passing_dates)} dates)")
print(f"  Matched with AI: {len(matched_results)} trades on {len(ai_trade_dates)} AI dates")

# ═══════════════════════════════════════════════════════════════════════
# 4. ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("SECTION 1: PRE-SCREEN POPULATION")
print("="*70)

print(f"Total weekdays in data: {weekdays_checked}")
print(f"Pre-screen passing: {weekdays_passed} ({weekdays_passed/weekdays_checked*100:.1f}%)")
print(f"Pre-screen failing: {weekdays_checked - weekdays_passed}")
for reason, count in fail_reasons.most_common(10):
    label = reason.replace("L1_d1_", "D1 ").replace("L2_h4_", "H4 ").replace("L2_h4_conflict_", "H4 conflict: ")
    print(f"  {label}: {count}")
print(f"\nAI system traded on: {len(ai_trade_dates)} dates")
print(f"AI system skipped: {weekdays_passed - len(ai_trade_dates)} passing dates")

print("\n" + "="*70)
print("SECTION 2: NAIVE vs AI — MATCHED COMPARISON (AI trade dates)")
print("="*70)

# Filter to valid matched results with both AI and naive data
valid_matched = [r for r in matched_results if r["strategy1"] is not None and "ai_trade" in r]

print(f"\nMatched trades: {len(valid_matched)}")

if valid_matched:
    # 2A: Entry price comparison
    ai_entries = [r["ai_trade"]["entry"] for r in valid_matched]
    naive_entries = [r["entry_price"] for r in valid_matched]
    ai_risks = [r["ai_trade"]["risk"] for r in valid_matched]
    naive_risks_s1 = [r["strategy1"]["risk"] for r in valid_matched if r["strategy1"]]
    naive_risks_s2 = [r["strategy2"]["risk"] for r in valid_matched if r["strategy2"]]

    print(f"\n  2A: Entry Price Comparison")
    print(f"  {'':25s} {'AI System':>15s} {'Naive (1st candle)':>18s} {'Diff':>10s}")
    print(f"  {'Avg entry price':25s} ${np.mean(ai_entries):>13.2f} ${np.mean(naive_entries):>16.2f} ${np.mean(ai_entries) - np.mean(naive_entries):>+8.2f}")
    print(f"  {'Avg SL distance ($)':25s} ${np.mean(ai_risks):>13.2f} ${np.mean(naive_risks_s1):>16.2f}")
    ai_sl_pcts = [r["ai_trade"]["risk"] / r["ai_trade"]["entry"] * 100 for r in valid_matched]
    naive_sl_pcts = [r["strategy1"]["risk"] / r["entry_price"] * 100 for r in valid_matched if r["strategy1"]]
    print(f"  {'Avg SL distance (%)':25s} {np.mean(ai_sl_pcts):>14.2f}% {np.mean(naive_sl_pcts):>16.2f}%")

    # Entry price: is AI entering higher or lower?
    ai_higher = sum(1 for r in valid_matched if r["ai_trade"]["entry"] > r["entry_price"])
    ai_lower = sum(1 for r in valid_matched if r["ai_trade"]["entry"] < r["entry_price"])
    print(f"\n  AI enters HIGHER than KZ open: {ai_higher}/{len(valid_matched)} ({ai_higher/len(valid_matched)*100:.0f}%)")
    print(f"  AI enters LOWER than KZ open:  {ai_lower}/{len(valid_matched)} ({ai_lower/len(valid_matched)*100:.0f}%)")
    avg_entry_diff = np.mean([r["ai_trade"]["entry"] - r["entry_price"] for r in valid_matched])
    print(f"  Avg entry difference: ${avg_entry_diff:+.2f} (positive = AI enters higher)")

    # 2B: MFE/MAE comparison
    print(f"\n  2B: MFE/MAE Comparison (matched dates)")
    print(f"  {'':20s} {'AI System':>12s} {'Naive S1':>12s} {'Naive S2':>12s}")

    ai_mfe_r = [r["ai_trade"]["mfe_r"] for r in valid_matched]
    ai_mae_r = [r["ai_trade"]["mae_r"] for r in valid_matched]
    ai_mfe_d = [r["ai_trade"]["mfe_dollar"] for r in valid_matched]
    ai_mae_d = [r["ai_trade"]["mae_dollar"] for r in valid_matched]

    s1_valid = [r for r in valid_matched if r["strategy1"]]
    s1_mfe_r = [r["strategy1"]["mfe_r"] for r in s1_valid]
    s1_mae_r = [r["strategy1"]["mae_r"] for r in s1_valid]
    s1_mfe_d = [r["strategy1"]["mfe_dollar"] for r in s1_valid]
    s1_mae_d = [r["strategy1"]["mae_dollar"] for r in s1_valid]

    s2_valid = [r for r in valid_matched if r["strategy2"]]
    s2_mfe_r = [r["strategy2"]["mfe_r"] for r in s2_valid]
    s2_mae_r = [r["strategy2"]["mae_r"] for r in s2_valid]
    s2_mfe_d = [r["strategy2"]["mfe_dollar"] for r in s2_valid]
    s2_mae_d = [r["strategy2"]["mae_dollar"] for r in s2_valid]

    print(f"  {'Avg MFE (R)':20s} {np.mean(ai_mfe_r):>12.3f} {np.mean(s1_mfe_r):>12.3f} {np.mean(s2_mfe_r):>12.3f}")
    print(f"  {'Avg MFE ($)':20s} ${np.mean(ai_mfe_d):>10.2f} ${np.mean(s1_mfe_d):>10.2f} ${np.mean(s2_mfe_d):>10.2f}")
    print(f"  {'Avg MAE (R)':20s} {np.mean(ai_mae_r):>12.3f} {np.mean(s1_mae_r):>12.3f} {np.mean(s2_mae_r):>12.3f}")
    print(f"  {'Avg MAE ($)':20s} ${np.mean(ai_mae_d):>10.2f} ${np.mean(s1_mae_d):>10.2f} ${np.mean(s2_mae_d):>10.2f}")
    print(f"  {'MFE-MAE (R)':20s} {np.mean(ai_mfe_r)-np.mean(ai_mae_r):>12.3f} {np.mean(s1_mfe_r)-np.mean(s1_mae_r):>12.3f} {np.mean(s2_mfe_r)-np.mean(s2_mae_r):>12.3f}")
    print(f"  {'MFE-MAE ($)':20s} ${np.mean(ai_mfe_d)-np.mean(ai_mae_d):>10.2f} ${np.mean(s1_mfe_d)-np.mean(s1_mae_d):>10.2f} ${np.mean(s2_mfe_d)-np.mean(s2_mae_d):>10.2f}")

    # 2C: Outcome comparison at TP levels
    print(f"\n  2C: Win Rate at Various TP Levels (matched dates)")
    print(f"  {'TP Level':10s} {'AI WR':>8s} {'Naive S1':>10s} {'Naive S2':>10s}")

    for tp_r in [0.5, 1.0, 1.5, 2.0, 2.5]:
        ai_wr = sum(1 for r in valid_matched if r["ai_trade"]["mfe_r"] >= tp_r) / len(valid_matched) * 100
        s1_wr = sum(1 for r in s1_valid if tp_r in r["strategy1"].get("tp_hits", {})) / len(s1_valid) * 100 if s1_valid else 0
        s2_wr = sum(1 for r in s2_valid if tp_r in r["strategy2"].get("tp_hits", {})) / len(s2_valid) * 100 if s2_valid else 0
        print(f"  {tp_r}R{'':<6s} {ai_wr:>7.0f}% {s1_wr:>9.0f}% {s2_wr:>9.0f}%")

    # 2D: Dollar P&L (1% risk on $100K)
    print(f"\n  2D: Dollar P&L (1% risk on $100K = $1000 risk per trade)")
    risk_per_trade = 1000.0

    ai_pnl = [r["ai_trade"]["r_multiple"] * risk_per_trade for r in valid_matched]
    s1_pnl = [r["strategy1"]["final_r"] * risk_per_trade for r in s1_valid]
    s2_pnl = [r["strategy2"]["final_r"] * risk_per_trade for r in s2_valid]

    print(f"  {'':25s} {'AI System':>12s} {'Naive S1':>12s} {'Naive S2':>12s}")
    print(f"  {'Avg $ P&L per trade':25s} ${np.mean(ai_pnl):>+10.2f} ${np.mean(s1_pnl):>+10.2f} ${np.mean(s2_pnl):>+10.2f}")
    print(f"  {'Total $ P&L':25s} ${sum(ai_pnl):>+10.2f} ${sum(s1_pnl):>+10.2f} ${sum(s2_pnl):>+10.2f}")

print("\n" + "="*70)
print("SECTION 3: NAIVE vs AI — SELECTIVITY TEST (ALL passing dates)")
print("="*70)

# Naive on ALL passing dates
all_s1 = [r["strategy1"] for r in naive_results if r["strategy1"] is not None]
all_s2 = [r["strategy2"] for r in naive_results if r["strategy2"] is not None]

if all_s1:
    s1_wins = sum(1 for r in all_s1 if r["final_r"] > 0.05)
    s1_losses = sum(1 for r in all_s1 if r["final_r"] < -0.05)
    s1_total_r = sum(r["final_r"] for r in all_s1)
    s1_wr = s1_wins / len(all_s1) * 100

    s2_wins = sum(1 for r in all_s2 if r["final_r"] > 0.05)
    s2_total_r = sum(r["final_r"] for r in all_s2)
    s2_wr = s2_wins / len(all_s2) * 100

    ai_wins = sum(1 for t in ai_trades if t["outcome"] == "WIN")
    ai_total_r = sum(t["r_multiple"] for t in ai_trades)
    ai_wr = ai_wins / len(ai_trades) * 100

    print(f"  {'':25s} {'AI System':>12s} {'Naive S1':>12s} {'Naive S2':>12s}")
    print(f"  {'Dates traded':25s} {len(ai_trade_dates):>12d} {len(passing_dates):>12d} {len(passing_dates):>12d}")
    print(f"  {'Total trades':25s} {len(ai_trades):>12d} {len(all_s1):>12d} {len(all_s2):>12d}")
    print(f"  {'Win rate':25s} {ai_wr:>11.1f}% {s1_wr:>11.1f}% {s2_wr:>11.1f}%")
    print(f"  {'Total R':25s} {ai_total_r:>+12.2f} {s1_total_r:>+12.2f} {s2_total_r:>+12.2f}")
    print(f"  {'Expectancy':25s} {ai_total_r/len(ai_trades):>+12.3f} {s1_total_r/len(all_s1):>+12.3f} {s2_total_r/len(all_s2):>+12.3f}")

    # Per-trade dollar P&L
    print(f"\n  Dollar P&L (1% of $100K):")
    print(f"  {'AI total $':25s} ${ai_total_r * risk_per_trade:>+10.2f}")
    print(f"  {'Naive S1 total $':25s} ${s1_total_r * risk_per_trade:>+10.2f}")
    print(f"  {'Naive S2 total $':25s} ${s2_total_r * risk_per_trade:>+10.2f}")

print("\n" + "="*70)
print("SECTION 4: VERDICT ON AI VALUE")
print("="*70)

if valid_matched and all_s1:
    # Precision value
    ai_avg_mfe_d = np.mean(ai_mfe_d)
    naive_avg_mfe_d = np.mean(s1_mfe_d)
    mfe_ratio = (ai_avg_mfe_d - naive_avg_mfe_d) / naive_avg_mfe_d * 100 if naive_avg_mfe_d > 0 else 0

    if mfe_ratio >= 20:
        precision_verdict = "YES"
    elif mfe_ratio >= 5:
        precision_verdict = "PARTIAL"
    else:
        precision_verdict = "NO"

    print(f"\n  PRECISION VALUE: {precision_verdict}")
    print(f"    AI avg MFE ($): ${ai_avg_mfe_d:.2f}")
    print(f"    Naive avg MFE ($): ${naive_avg_mfe_d:.2f}")
    print(f"    Difference: {mfe_ratio:+.1f}%")

    # Selectivity value
    ai_total = ai_total_r
    naive_total = s1_total_r
    if ai_total > naive_total:
        selectivity_verdict = "YES"
    elif abs(ai_total - naive_total) < 5:
        selectivity_verdict = "PARTIAL"
    else:
        selectivity_verdict = "NO"

    print(f"\n  SELECTIVITY VALUE: {selectivity_verdict}")
    print(f"    AI total R (40 trades): {ai_total:+.2f}R")
    print(f"    Naive S1 total R ({len(all_s1)} trades): {naive_total:+.2f}R")

    # Overall verdict
    if precision_verdict == "YES" and selectivity_verdict in ("YES", "PARTIAL"):
        overall = "STRONG VALUE"
    elif precision_verdict in ("YES", "PARTIAL") or selectivity_verdict in ("YES", "PARTIAL"):
        overall = "PARTIAL VALUE"
    else:
        overall = "NO VALUE"

    print(f"\n  OVERALL VERDICT: {overall}")

print("\n" + "="*70)
print("SECTION 5: DXY DIAGNOSTIC")
print("="*70)
if not eurusd_exists and not dxy_exists:
    print("  SKIPPED — No EURUSD or DXY data available.")
    print("  To enable: Export EURUSD D1/H4/H1 from MT5 on Windows machine to data/EURUSD_D1.csv etc.")

print("\n" + "="*70)
print("SUPPLEMENTARY: DAY-OF-WEEK (Naive)")
print("="*70)

dow_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
naive_by_dow = defaultdict(list)
for r in naive_results:
    if r["strategy1"]:
        d = date.fromisoformat(r["date"])
        dow = dow_names[d.weekday()]
        naive_by_dow[dow].append(r["strategy1"]["final_r"])

print(f"  {'Day':6s} {'Trades':>8s} {'WR':>8s} {'Total R':>10s} {'Avg R':>10s}")
for dow in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
    rs = naive_by_dow[dow]
    if rs:
        wins = sum(1 for r in rs if r > 0.05)
        print(f"  {dow:6s} {len(rs):>8d} {wins/len(rs)*100:>7.0f}% {sum(rs):>+10.2f} {np.mean(rs):>+10.3f}")

print("\n" + "="*70)
print("SUPPLEMENTARY: ENTRY CANDLE INDEX vs OUTCOME (Naive S3)")
print("="*70)

# For every-candle strategy: how does entry position affect outcome?
for kz in ["london", "ny"]:
    kz_results = [r for r in naive_results if r["kz"] == kz and r["strategy3_avg"]]
    if kz_results:
        avg_mfe = np.mean([r["strategy3_avg"]["mfe_r"] for r in kz_results])
        avg_wr1r = np.mean([r["strategy3_avg"]["wr_1r"] for r in kz_results])
        print(f"  {kz.upper():8s}: avg candle MFE={avg_mfe:.2f}R, avg 1.0R hit rate={avg_wr1r*100:.0f}%")

# ═══════════════════════════════════════════════════════════════════════
# 5. SAVE DATA
# ═══════════════════════════════════════════════════════════════════════

ts = datetime.now().strftime("%Y%m%d_%H%M")

# Save raw data (convert numpy types for JSON serialization)
def convert(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

save_data = {
    "metadata": {"timestamp": ts, "passing_dates": len(passing_dates), "ai_trades": len(ai_trades)},
    "prescreen_summary": {
        "total_weekdays": weekdays_checked,
        "passing": weekdays_passed,
        "fail_reasons": dict(fail_reasons),
    },
    "naive_results_sample": naive_results[:20],  # Save sample to keep size manageable
    "matched_count": len(valid_matched),
    "naive_all_count": len(all_s1) if all_s1 else 0,
}

data_path = _ROOT / f"knowledge_base_backtest/analysis/phase0_naive_baseline_data_{ts}.json"
with open(data_path, "w") as f:
    json.dump(save_data, f, indent=2, default=convert)
print(f"\nData saved: {data_path}")
print("Script complete.")
