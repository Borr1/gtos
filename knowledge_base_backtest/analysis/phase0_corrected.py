#!/usr/bin/env python3
"""
Phase 0 CORRECTED — Naive Baseline with Proper Stop Loss Methodology
Fixes the broken session-low SL from the original Phase 0.
ZERO API calls. Entirely deterministic.
"""
import sys, json, os
from pathlib import Path
from datetime import date, datetime, timedelta
from collections import defaultdict, Counter
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from scripts.historical_data_loader import parse_tradingview_csv
from src.components.market_state import detect_swings, identify_structure

# ═══════════════════════════════════════════════════════════════════════
# 1. LOAD AND VALIDATE DATA
# ═══════════════════════════════════════════════════════════════════════

print("=" * 70)
print("STEP 1: LOADING AND VALIDATING DATA")
print("=" * 70)

DATA_DIRS = [_ROOT / "data" / "historical", _ROOT / "data"]

def find_csv(tf):
    for d in DATA_DIRS:
        p = d / f"XAUUSD_{tf}.csv"
        if p.exists():
            return p
    return None

candle_data = {}
for tf in ("D1", "H4", "H1", "M15"):
    p = find_csv(tf)
    if p is None:
        print(f"  FATAL: No CSV for {tf}")
        sys.exit(1)
    candles = parse_tradingview_csv(p)
    assert len(candles) > 100, f"{tf} has only {len(candles)} candles"
    # Validate OHLC
    for c in candles[:10]:
        assert c["high"] >= c["low"], f"Bad OHLC: {c}"
        assert c["close"] > 1000, f"Not gold data? close={c['close']}"
    candle_data[tf] = candles
    print(f"  {tf}: {len(candles)} candles, {candles[0]['time'][:10]} to {candles[-1]['time'][:10]}")

# Build M15 index by date
m15_all = candle_data["M15"]
m15_by_date = defaultdict(list)
for c in m15_all:
    d = c["time"][:10]
    m15_by_date[d].append(c)

# Build global index for fast lookup
m15_time_to_idx = {c["time"]: i for i, c in enumerate(m15_all)}

# Load AI trades
ai_trades = []
for path in [
    _ROOT / "knowledge_base_backtest/analysis/replay/replay_results.json",
    _ROOT / "knowledge_base_backtest/analysis/supplementary_replay_0_1643.json",
]:
    if path.exists():
        with open(path) as f:
            ai_trades.extend(json.load(f))
print(f"  AI trades loaded: {len(ai_trades)}")

ai_by_date_kz = {}
for t in ai_trades:
    ai_by_date_kz[(t["date"], t["kill_zone"])] = t

# ═══════════════════════════════════════════════════════════════════════
# 2. REPLICATE THE PRE-SCREEN
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("STEP 2: PRE-SCREEN (D1 + H4 alignment)")
print("=" * 70)

def get_candles_before(candles, cutoff_time_str):
    """Return candles whose time < cutoff_time_str."""
    return [c for c in candles if c["time"] < cutoff_time_str]

def get_structure_direction(candles, lookback, min_bars=2):
    """Detect swings and identify structure on last `lookback` candles."""
    recent = candles[-lookback:] if len(candles) >= lookback else candles
    if len(recent) < 5:
        return "insufficient_data"
    swings = detect_swings(recent, min_bars=min_bars)
    structure = identify_structure(swings)
    return structure.direction

# Pre-screen each weekday
first_m15_date = date.fromisoformat(m15_all[0]["time"][:10])
last_m15_date = date.fromisoformat(m15_all[-1]["time"][:10])

# Start 60 days in to ensure D1 lookback
start_date = first_m15_date + timedelta(days=60)
end_date = last_m15_date - timedelta(days=1)

prescreen_results = {}
fail_reasons = Counter()
weekdays_checked = 0

d = start_date
while d <= end_date:
    if d.weekday() >= 5:
        d += timedelta(days=1)
        continue

    ds = d.isoformat()
    weekdays_checked += 1

    # D1: last 30 candles closing BEFORE this date
    d1_cutoff = f"{ds}T00:00:00Z"
    d1_before = get_candles_before(candle_data["D1"], d1_cutoff)
    d1_dir = get_structure_direction(d1_before, 30, min_bars=2)

    if d1_dir not in ("bullish", "bearish"):
        prescreen_results[ds] = {"passed": False, "reason": f"L1_d1_{d1_dir}", "d1_dir": d1_dir}
        fail_reasons[f"L1_d1_{d1_dir}"] += 1
        d += timedelta(days=1)
        continue

    # H4: last 80 candles closing before London KZ start (07:00)
    h4_cutoff = f"{ds}T07:00:00Z"
    h4_before = get_candles_before(candle_data["H4"], h4_cutoff)
    h4_dir = get_structure_direction(h4_before, 80, min_bars=2)

    if h4_dir not in ("bullish", "bearish"):
        prescreen_results[ds] = {"passed": False, "reason": f"L2_h4_{h4_dir}", "d1_dir": d1_dir}
        fail_reasons[f"L2_h4_{h4_dir}"] += 1
        d += timedelta(days=1)
        continue

    if h4_dir != d1_dir:
        prescreen_results[ds] = {"passed": False, "reason": f"L2_h4_conflict_{h4_dir}_vs_d1_{d1_dir}", "d1_dir": d1_dir}
        fail_reasons[f"L2_h4_conflict_{h4_dir}_vs_d1_{d1_dir}"] += 1
        d += timedelta(days=1)
        continue

    prescreen_results[ds] = {"passed": True, "reason": "", "d1_dir": d1_dir}
    d += timedelta(days=1)

passing_dates = sorted([ds for ds, r in prescreen_results.items() if r["passed"]])
print(f"  Weekdays checked: {weekdays_checked}")
print(f"  Pre-screen passing: {len(passing_dates)} ({len(passing_dates)/weekdays_checked*100:.1f}%)")
print(f"  Fail reasons:")
for reason, count in fail_reasons.most_common(10):
    print(f"    {reason}: {count}")
print(f"  CROSS-CHECK: Original Phase 0 found 166 passing. We found {len(passing_dates)}.")

# ═══════════════════════════════════════════════════════════════════════
# 3. NAIVE STRATEGY SIMULATION
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("STEP 3: NAIVE STRATEGY SIMULATION")
print("=" * 70)

def get_hour_minute(time_str):
    """Extract (hour, minute) from ISO time string."""
    # Format: YYYY-MM-DDTHH:MM:SSZ
    return int(time_str[11:13]), int(time_str[14:16])

def candles_in_window(date_str, start_h, start_m, end_h, end_m):
    """Get M15 candles within a time window. Times are candle OPEN times."""
    candles = m15_by_date.get(date_str, [])
    result = []
    start_min = start_h * 60 + start_m
    end_min = end_h * 60 + end_m
    for c in candles:
        h, m = get_hour_minute(c["time"])
        t_min = h * 60 + m
        if start_min <= t_min < end_min:
            result.append(c)
    return result

def compute_atr(candles, period=20):
    if len(candles) < period + 1:
        return None
    trs = []
    for i in range(-period, 0):
        c = candles[i]
        prev = candles[i - 1]
        tr = max(c["high"] - c["low"], abs(c["high"] - prev["close"]), abs(c["low"] - prev["close"]))
        trs.append(tr)
    return np.mean(trs)

def simulate_trade(entry_price, sl_price, direction, future_candles, max_hold):
    """Simulate a trade candle-by-candle. Returns outcome dict."""
    is_long = direction == "long"
    risk = abs(entry_price - sl_price)
    if risk < 0.01:
        return None

    mfe_dollar = 0.0
    mae_dollar = 0.0
    tp_results = {}

    for tp_r in [1.0, 1.5, 2.0, 2.5]:
        tp_price = (entry_price + tp_r * risk) if is_long else (entry_price - tp_r * risk)
        hit = False
        final_r = None
        local_mfe_d = 0.0
        local_mae_d = 0.0

        for i, c in enumerate(future_candles[:max_hold]):
            # Track MFE/MAE
            if is_long:
                fav = c["high"] - entry_price
                adv = entry_price - c["low"]
            else:
                fav = entry_price - c["low"]
                adv = c["high"] - entry_price
            local_mfe_d = max(local_mfe_d, fav)
            local_mae_d = max(local_mae_d, adv)

            # SL check first (conservative)
            if is_long and c["low"] <= sl_price:
                final_r = -1.0
                break
            if not is_long and c["high"] >= sl_price:
                final_r = -1.0
                break

            # TP check
            if is_long and c["high"] >= tp_price:
                hit = True
                final_r = tp_r
                break
            if not is_long and c["low"] <= tp_price:
                hit = True
                final_r = tp_r
                break

        if final_r is None:
            # Timeout
            idx = min(max_hold - 1, len(future_candles) - 1)
            last_close = future_candles[idx]["close"]
            if is_long:
                final_r = (last_close - entry_price) / risk
            else:
                final_r = (entry_price - last_close) / risk

        tp_results[f"tp_{tp_r}r"] = {"hit": hit, "final_r": round(final_r, 4), "candles_held": min(max_hold, len(future_candles))}

    # No-TP run (just hold to timeout)
    no_tp_final = None
    running_mfe_d = 0.0
    running_mae_d = 0.0
    for i, c in enumerate(future_candles[:max_hold]):
        if is_long:
            fav = c["high"] - entry_price
            adv = entry_price - c["low"]
        else:
            fav = entry_price - c["low"]
            adv = c["high"] - entry_price
        running_mfe_d = max(running_mfe_d, fav)
        running_mae_d = max(running_mae_d, adv)

        # SL check
        if is_long and c["low"] <= sl_price:
            no_tp_final = -1.0
            break
        if not is_long and c["high"] >= sl_price:
            no_tp_final = -1.0
            break

    if no_tp_final is None:
        idx = min(max_hold - 1, len(future_candles) - 1)
        last_close = future_candles[idx]["close"]
        if is_long:
            no_tp_final = (last_close - entry_price) / risk
        else:
            no_tp_final = (entry_price - last_close) / risk

    tp_results["no_tp"] = {"final_r": round(no_tp_final, 4), "candles_held": min(max_hold, len(future_candles))}

    return {
        "mfe_dollar": round(running_mfe_d, 2),
        "mae_dollar": round(running_mae_d, 2),
        "mfe_r": round(running_mfe_d / risk, 4) if risk > 0 else 0,
        "mae_r": round(running_mae_d / risk, 4) if risk > 0 else 0,
        "outcomes": tp_results,
    }

# Process all passing dates
all_trades = []
processed = 0

for ds in passing_dates:
    d1_dir = prescreen_results[ds]["d1_dir"]
    direction = "long" if d1_dir == "bullish" else "short"
    day_candles = m15_by_date.get(ds, [])

    if len(day_candles) < 20:
        continue

    for kz in ["london", "ny"]:
        if kz == "london":
            entry_time = f"{ds}T07:00:00Z"
            asian_candles = candles_in_window(ds, 0, 0, 6, 45)
            max_hold = 18  # 07:00 to 11:30 = 4.5h = 18 candles
            sl_session_candles = asian_candles
        else:
            entry_time = f"{ds}T13:00:00Z"
            london_candles = candles_in_window(ds, 7, 0, 12, 45)
            max_hold = 18  # 13:00 to 17:30 = 4.5h = 18 candles
            sl_session_candles = london_candles

        # Find entry candle
        entry_candle = None
        for c in day_candles:
            if c["time"] == entry_time:
                entry_candle = c
                break
        if entry_candle is None:
            continue

        entry_price = entry_candle["open"]  # Enter at the OPEN

        # Skip if insufficient session data for SL computation
        if len(sl_session_candles) < 10:
            continue

        # Get future candles from entry onward (including entry candle itself)
        gi = m15_time_to_idx.get(entry_time)
        if gi is None:
            continue
        future_candles = m15_all[gi: gi + max_hold + 40]  # extra buffer

        # Get ATR
        atr_candles = m15_all[:gi + 1]
        m15_atr = compute_atr(atr_candles, 20) if len(atr_candles) > 21 else None

        # ── Strategy A: Corrected Structural SL ──
        if direction == "long":
            raw_sl_a = min(c["low"] for c in sl_session_candles)
        else:
            raw_sl_a = max(c["high"] for c in sl_session_candles)

        sl_dist_a = abs(entry_price - raw_sl_a)

        # Floor at $5
        sl_floored_a = False
        if sl_dist_a < 5.0:
            sl_dist_a = 5.0
            sl_floored_a = True
            raw_sl_a = (entry_price - 5.0) if direction == "long" else (entry_price + 5.0)

        # Ceiling at 2.5%
        sl_ceiling_a = False
        if sl_dist_a > entry_price * 0.025:
            sl_ceiling_a = True

        # Validate SL is on correct side
        if direction == "long" and raw_sl_a >= entry_price:
            continue
        if direction == "short" and raw_sl_a <= entry_price:
            continue

        strat_a = None
        if not sl_ceiling_a:
            strat_a = simulate_trade(entry_price, raw_sl_a, direction, future_candles, max_hold)
            if strat_a:
                strat_a["sl_price"] = raw_sl_a
                strat_a["sl_distance"] = round(sl_dist_a, 2)
                strat_a["sl_floored"] = sl_floored_a
                strat_a["sl_ceiling_skipped"] = False
        else:
            strat_a = {"sl_ceiling_skipped": True, "sl_distance": round(sl_dist_a, 2)}

        # ── Strategy B: ATR SL ──
        strat_b = None
        if m15_atr:
            atr_sl_dist = 2.0 * m15_atr
            if atr_sl_dist < 5.0:
                atr_sl_dist = 5.0
            if atr_sl_dist <= entry_price * 0.025:
                atr_sl = (entry_price - atr_sl_dist) if direction == "long" else (entry_price + atr_sl_dist)
                strat_b = simulate_trade(entry_price, atr_sl, direction, future_candles, max_hold)
                if strat_b:
                    strat_b["sl_price"] = atr_sl
                    strat_b["sl_distance"] = round(atr_sl_dist, 2)

        # ── Strategy C: Broken (entry candle low/high) ──
        if direction == "long":
            broken_sl = entry_candle["low"]
        else:
            broken_sl = entry_candle["high"]
        broken_sl_dist = abs(entry_price - broken_sl)
        strat_c = None
        if broken_sl_dist >= 0.10 and ((direction == "long" and broken_sl < entry_price) or (direction == "short" and broken_sl > entry_price)):
            strat_c = simulate_trade(entry_price, broken_sl, direction, future_candles, max_hold)
            if strat_c:
                strat_c["sl_price"] = broken_sl
                strat_c["sl_distance"] = round(broken_sl_dist, 2)

        # ── Strategy D: Fixed $15 SL ──
        fixed_sl = (entry_price - 15.0) if direction == "long" else (entry_price + 15.0)
        strat_d = simulate_trade(entry_price, fixed_sl, direction, future_candles, max_hold)
        if strat_d:
            strat_d["sl_price"] = fixed_sl
            strat_d["sl_distance"] = 15.0

        trade_record = {
            "date": ds,
            "kz": kz,
            "d1_direction": d1_dir,
            "trade_direction": direction,
            "entry_price": entry_price,
            "strategy_a": strat_a,
            "strategy_b": strat_b,
            "strategy_c": strat_c,
            "strategy_d": strat_d,
            "ai_traded": (ds, kz) in ai_by_date_kz,
        }

        if trade_record["ai_traded"]:
            ai_t = ai_by_date_kz[(ds, kz)]
            sl_dist = abs(ai_t["entry_price"] - ai_t["stop_loss"])
            trade_record["ai_trade"] = {
                "entry": ai_t["entry_price"],
                "sl": ai_t["stop_loss"],
                "risk": sl_dist,
                "mfe_r": ai_t["mfe_r"],
                "mae_r": ai_t["mae_r"],
                "r_multiple": ai_t["r_multiple"],
                "outcome": ai_t["outcome"],
                "mfe_dollar": round(ai_t["mfe_r"] * sl_dist, 2),
                "mae_dollar": round(ai_t["mae_r"] * sl_dist, 2),
            }

        all_trades.append(trade_record)

    processed += 1
    if processed % 50 == 0:
        print(f"  Processed {processed}/{len(passing_dates)} dates...")

print(f"  Total naive trades simulated: {len(all_trades)}")
matched = [t for t in all_trades if t["ai_traded"]]
print(f"  Matched with AI trades: {len(matched)}")

# ═══════════════════════════════════════════════════════════════════════
# 5. COMPUTE ALL STATISTICS
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("STEP 5: STATISTICS")
print("=" * 70)

# ── 5A: Per-Strategy Summary ──
def strategy_stats(trades, strategy_key, tp_key):
    """Compute stats for a strategy at a given TP level."""
    valid = []
    for t in trades:
        s = t.get(strategy_key)
        if s is None or s.get("sl_ceiling_skipped"):
            continue
        outcomes = s.get("outcomes", {})
        if tp_key not in outcomes:
            continue
        valid.append(outcomes[tp_key]["final_r"])

    if not valid:
        return None

    wins = sum(1 for r in valid if r > 0.05)
    losses = sum(1 for r in valid if r < -0.05)
    total_r = sum(valid)
    avg_r = np.mean(valid)
    gross_wins = sum(r for r in valid if r > 0)
    gross_losses = abs(sum(r for r in valid if r < 0))
    pf = gross_wins / gross_losses if gross_losses > 0 else float('inf')

    return {
        "n": len(valid), "wins": wins, "losses": losses,
        "wr": round(wins / len(valid) * 100, 1),
        "total_r": round(total_r, 2), "avg_r": round(avg_r, 4),
        "pf": round(pf, 2),
    }

print("\n  5A: Strategy A (Corrected Structural SL) at each TP level:")
print(f"  {'TP Level':10s} {'N':>5s} {'WR':>7s} {'Total R':>10s} {'Avg R':>10s} {'PF':>6s}")
for tp in ["tp_1.0r", "tp_1.5r", "tp_2.0r", "tp_2.5r", "no_tp"]:
    s = strategy_stats(all_trades, "strategy_a", tp)
    if s:
        print(f"  {tp:10s} {s['n']:>5d} {s['wr']:>6.1f}% {s['total_r']:>+10.2f} {s['avg_r']:>+10.4f} {s['pf']:>6.2f}")

print("\n  All strategies at best TP level and no_tp:")
for strat in ["strategy_a", "strategy_b", "strategy_c", "strategy_d"]:
    for tp in ["tp_1.0r", "tp_1.5r", "no_tp"]:
        s = strategy_stats(all_trades, strat, tp)
        label = f"{strat[-1].upper()}/{tp}"
        if s:
            print(f"  {label:15s} N={s['n']:>4d} WR={s['wr']:>5.1f}% TotalR={s['total_r']:>+8.2f} Exp={s['avg_r']:>+.4f} PF={s['pf']:>.2f}")

# ── 5B: SL Distance Distribution ──
print("\n  5B: SL Distance Distribution (Strategy A):")
sl_dists_a = [t["strategy_a"]["sl_distance"] for t in all_trades if t.get("strategy_a") and not t["strategy_a"].get("sl_ceiling_skipped")]
if sl_dists_a:
    floored = sum(1 for t in all_trades if t.get("strategy_a") and t["strategy_a"].get("sl_floored"))
    ceiling_skipped = sum(1 for t in all_trades if t.get("strategy_a") and t["strategy_a"].get("sl_ceiling_skipped"))
    print(f"    Min: ${min(sl_dists_a):.2f}")
    print(f"    P10: ${np.percentile(sl_dists_a, 10):.2f}")
    print(f"    P25: ${np.percentile(sl_dists_a, 25):.2f}")
    print(f"    Median: ${np.median(sl_dists_a):.2f}")
    print(f"    P75: ${np.percentile(sl_dists_a, 75):.2f}")
    print(f"    P90: ${np.percentile(sl_dists_a, 90):.2f}")
    print(f"    Max: ${max(sl_dists_a):.2f}")
    print(f"    Floored to $5: {floored}")
    print(f"    Ceiling skipped (>2.5%): {ceiling_skipped}")

    sl_dists_c = [t["strategy_c"]["sl_distance"] for t in all_trades if t.get("strategy_c")]
    if sl_dists_c:
        print(f"\n    Strategy C (broken) median SL: ${np.median(sl_dists_c):.2f} vs A: ${np.median(sl_dists_a):.2f}")

# ── 5C: Matched Comparison ──
print("\n  5C: Matched Comparison (AI dates only):")
matched_a = [t for t in matched if t.get("strategy_a") and not t["strategy_a"].get("sl_ceiling_skipped") and t["strategy_a"].get("outcomes")]

if matched_a:
    ai_mfe_d = [t["ai_trade"]["mfe_dollar"] for t in matched_a]
    ai_mae_d = [t["ai_trade"]["mae_dollar"] for t in matched_a]
    ai_r = [t["ai_trade"]["r_multiple"] for t in matched_a]
    ai_sl_d = [t["ai_trade"]["risk"] for t in matched_a]

    sa_mfe_d = [t["strategy_a"]["mfe_dollar"] for t in matched_a]
    sa_mae_d = [t["strategy_a"]["mae_dollar"] for t in matched_a]
    sa_sl_d = [t["strategy_a"]["sl_distance"] for t in matched_a]

    print(f"    Matched trades: {len(matched_a)}")
    print(f"    {'':25s} {'AI':>12s} {'Strat A':>12s}")
    print(f"    {'Avg MFE ($)':25s} ${np.mean(ai_mfe_d):>10.2f} ${np.mean(sa_mfe_d):>10.2f}")
    print(f"    {'Avg MAE ($)':25s} ${np.mean(ai_mae_d):>10.2f} ${np.mean(sa_mae_d):>10.2f}")
    print(f"    {'MFE-MAE ($)':25s} ${np.mean(ai_mfe_d)-np.mean(ai_mae_d):>10.2f} ${np.mean(sa_mfe_d)-np.mean(sa_mae_d):>10.2f}")
    print(f"    {'Avg SL dist ($)':25s} ${np.mean(ai_sl_d):>10.2f} ${np.mean(sa_sl_d):>10.2f}")

    # Total R at each TP level
    print(f"\n    Total R comparison (matched dates):")
    print(f"    {'TP Level':10s} {'AI':>10s} {'Strat A':>10s}")
    ai_total = sum(ai_r)
    for tp in ["tp_1.0r", "tp_1.5r", "tp_2.0r", "tp_2.5r", "no_tp"]:
        sa_rs = [t["strategy_a"]["outcomes"][tp]["final_r"] for t in matched_a]
        print(f"    {tp:10s} {ai_total:>+10.2f} {sum(sa_rs):>+10.2f}")

    # Dollar P&L
    risk_per_trade = 1000.0
    print(f"\n    Dollar P&L (1% of $100K):")
    print(f"    AI: ${ai_total * risk_per_trade:>+,.0f}")
    for tp in ["tp_1.0r", "tp_1.5r", "no_tp"]:
        sa_rs = [t["strategy_a"]["outcomes"][tp]["final_r"] for t in matched_a]
        print(f"    Strat A ({tp}): ${sum(sa_rs) * risk_per_trade:>+,.0f}")

    # Entry comparison
    ai_entries = [t["ai_trade"]["entry"] for t in matched_a]
    naive_entries = [t["entry_price"] for t in matched_a]
    avg_diff = np.mean([a - n for a, n in zip(ai_entries, naive_entries)])
    print(f"\n    Entry price: AI avg ${np.mean(ai_entries):.2f} vs Naive avg ${np.mean(naive_entries):.2f} (diff ${avg_diff:+.2f})")

# ── 5D: Statistical significance ──
print("\n  5D: Statistical Significance (Strategy A, no_tp):")
sa_all_rs = [t["strategy_a"]["outcomes"]["no_tp"]["final_r"] for t in all_trades if t.get("strategy_a") and not t["strategy_a"].get("sl_ceiling_skipped") and t["strategy_a"].get("outcomes")]
if sa_all_rs:
    from scipy import stats
    t_stat, p_val = stats.ttest_1samp(sa_all_rs, 0)
    ci = stats.t.interval(0.95, len(sa_all_rs)-1, loc=np.mean(sa_all_rs), scale=stats.sem(sa_all_rs))
    print(f"    N={len(sa_all_rs)}, Mean={np.mean(sa_all_rs):+.4f}, Std={np.std(sa_all_rs):.4f}")
    print(f"    t-stat={t_stat:.3f}, p-value={p_val:.4f}")
    print(f"    95% CI: [{ci[0]:+.4f}, {ci[1]:+.4f}]")

    # Best TP
    best_tp = None
    best_exp = -999
    for tp in ["tp_1.0r", "tp_1.5r", "tp_2.0r", "tp_2.5r", "no_tp"]:
        rs = [t["strategy_a"]["outcomes"][tp]["final_r"] for t in all_trades if t.get("strategy_a") and not t["strategy_a"].get("sl_ceiling_skipped") and t["strategy_a"].get("outcomes")]
        exp = np.mean(rs) if rs else -999
        if exp > best_exp:
            best_exp = exp
            best_tp = tp

    print(f"    Best TP: {best_tp} (exp={best_exp:+.4f}R)")

    best_rs = [t["strategy_a"]["outcomes"][best_tp]["final_r"] for t in all_trades if t.get("strategy_a") and not t["strategy_a"].get("sl_ceiling_skipped") and t["strategy_a"].get("outcomes")]
    if best_rs:
        t2, p2 = stats.ttest_1samp(best_rs, 0)
        ci2 = stats.t.interval(0.95, len(best_rs)-1, loc=np.mean(best_rs), scale=stats.sem(best_rs))
        print(f"    At best TP: t={t2:.3f}, p={p2:.4f}, CI=[{ci2[0]:+.4f}, {ci2[1]:+.4f}]")

# ── 5E: Concentration ──
print("\n  5E: Concentration Analysis (Strategy A, no_tp):")
if sa_all_rs:
    sorted_rs = sorted(sa_all_rs, reverse=True)
    top_10pct_n = max(1, int(len(sorted_rs) * 0.1))
    top_10pct_r = sum(sorted_rs[:top_10pct_n])
    total_pos = sum(r for r in sa_all_rs if r > 0)
    print(f"    Top 10% of trades ({top_10pct_n} trades): {top_10pct_r:+.2f}R")
    print(f"    Total positive R: {total_pos:+.2f}R")
    if total_pos > 0:
        print(f"    Concentration: {top_10pct_r/total_pos*100:.0f}% of gains from top 10%")

# ── 5F: Segmented Analysis ──
print("\n  5F: Segmented Analysis (Strategy A, no_tp):")
for segment_key, segment_fn, label in [
    ("kz", lambda t: t["kz"], "Kill Zone"),
    ("dow", lambda t: date.fromisoformat(t["date"]).strftime("%A"), "Day of Week"),
    ("direction", lambda t: t["d1_direction"], "D1 Direction"),
]:
    print(f"\n    {label}:")
    groups = defaultdict(list)
    for t in all_trades:
        if t.get("strategy_a") and not t["strategy_a"].get("sl_ceiling_skipped") and t["strategy_a"].get("outcomes"):
            groups[segment_fn(t)].append(t["strategy_a"]["outcomes"]["no_tp"]["final_r"])

    for k in sorted(groups.keys()):
        rs = groups[k]
        wins = sum(1 for r in rs if r > 0.05)
        print(f"      {k:12s} N={len(rs):>4d} WR={wins/len(rs)*100:>5.1f}% TotalR={sum(rs):>+8.2f} AvgR={np.mean(rs):>+.4f}")

# First half vs second half
if sa_all_rs:
    half = len(all_trades) // 2
    first_half = [t["strategy_a"]["outcomes"]["no_tp"]["final_r"] for t in all_trades[:half] if t.get("strategy_a") and not t["strategy_a"].get("sl_ceiling_skipped") and t["strategy_a"].get("outcomes")]
    second_half = [t["strategy_a"]["outcomes"]["no_tp"]["final_r"] for t in all_trades[half:] if t.get("strategy_a") and not t["strategy_a"].get("sl_ceiling_skipped") and t["strategy_a"].get("outcomes")]
    print(f"\n    Time Period:")
    if first_half:
        print(f"      First half   N={len(first_half):>4d} WR={sum(1 for r in first_half if r>0.05)/len(first_half)*100:>5.1f}% TotalR={sum(first_half):>+8.2f} AvgR={np.mean(first_half):>+.4f}")
    if second_half:
        print(f"      Second half  N={len(second_half):>4d} WR={sum(1 for r in second_half if r>0.05)/len(second_half)*100:>5.1f}% TotalR={sum(second_half):>+8.2f} AvgR={np.mean(second_half):>+.4f}")

# ═══════════════════════════════════════════════════════════════════════
# 6. SAVE DATA
# ═══════════════════════════════════════════════════════════════════════

ts = datetime.now().strftime("%Y%m%d_%H%M")
data_path = _ROOT / f"knowledge_base_backtest/analysis/phase0_corrected_data_{ts}.json"

def convert(obj):
    if isinstance(obj, (np.integer,)): return int(obj)
    if isinstance(obj, (np.floating,)): return float(obj)
    if isinstance(obj, np.ndarray): return obj.tolist()
    return obj

with open(data_path, "w") as f:
    json.dump(all_trades, f, indent=1, default=convert)
print(f"\n  Data saved: {data_path} ({len(all_trades)} trades)")
print("Script complete.")
