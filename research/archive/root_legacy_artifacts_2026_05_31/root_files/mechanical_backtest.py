"""
Mechanical vs AI Backtest Comparison
=====================================
Tests whether the AI adds value by comparing:
- AI population: trades the AI selected (actual outcomes from sessions)
- Mechanical population: ALL OB retest events entered mechanically

For NO_TRADE events, simulates entry using zone data + M15 candle walk-forward.
"""

import json
import re
import pandas as pd
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timedelta

PROJECT = Path(".")
BATCH_DIR = PROJECT / "knowledge_base_backtest" / "batch_api"
SESSIONS_DIR = PROJECT / "knowledge_base_backtest" / "sessions"
DATA_DIR = PROJECT / "data" / "historical"

# ─── Step 1: Map batch files to instruments ─────────────────────────────
print("=" * 70)
print("STEP 1: Mapping batch files to instruments")
print("=" * 70)

batch_instrument_map = {}  # batch_id -> instrument
for pf in sorted(BATCH_DIR.glob("*_full_prompts.json")):
    prompts = json.load(open(pf))
    if isinstance(prompts, list) and prompts:
        prompt_text = str(prompts[0].get("prompt", ""))
        for inst in ["XAUUSD", "USDJPY", "GBPJPY", "GBPUSD", "EURUSD", "NAS100", "US30", "NZDUSD", "XAGUSD"]:
            if inst in prompt_text:
                batch_id = pf.name.split("_full_prompts")[0]
                batch_instrument_map[batch_id] = inst
                # Also map CIDs from prompts to instrument
                break

# Map CIDs to instruments via raw results files
cid_instrument = {}
for rf in sorted(BATCH_DIR.glob("*_raw_results.json")):
    batch_id = rf.name.split("_raw_results")[0]
    inst = batch_instrument_map.get(batch_id)
    if inst:
        data = json.load(open(rf))
        for cid in data:
            cid_instrument[cid] = inst

print(f"CIDs mapped to instruments: {len(cid_instrument)}")
print(f"Instruments: {Counter(cid_instrument.values())}")

# ─── Step 2: Load all batch evaluations ─────────────────────────────────
print("\n" + "=" * 70)
print("STEP 2: Loading all batch evaluations")
print("=" * 70)

raw_results = {}
for fp in sorted(BATCH_DIR.glob("*_raw_results.json")):
    raw_results.update(json.load(open(fp)))

all_events = []
for cid, data in raw_results.items():
    text = data.get("text", "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        response = json.loads(text)
    except:
        continue

    reasoning = response.get("reasoning", {})
    h1_setup = reasoning.get("h1_setup", {})
    m15 = reasoning.get("m15_confirmation", {})
    tp = response.get("trade_parameters") or {}

    all_events.append({
        "cid": cid,
        "instrument": cid_instrument.get(cid, "unknown"),
        "decision": response.get("decision", ""),
        "framework": response.get("framework", ""),
        "poi_identified": h1_setup.get("poi_identified"),
        "poi_type": h1_setup.get("poi_type"),
        "poi_price": h1_setup.get("poi_price_level"),
        "zone": h1_setup.get("zone"),
        "daily_bias": reasoning.get("daily_bias", {}).get("direction"),
        "h4_aligned": reasoning.get("h4_alignment", {}).get("aligned"),
        "sweep": reasoning.get("liquidity_sweep", {}).get("detected"),
        "m15_choch": m15.get("choch_detected"),
        "displacement_quality": m15.get("displacement_quality"),
        "confidence": response.get("confidence_score"),
        "setup_grade": reasoning.get("setup_grade"),
        "entry": tp.get("entry_price") or tp.get("entry") if isinstance(tp, dict) else None,
        "sl": tp.get("stop_loss") or tp.get("sl") if isinstance(tp, dict) else None,
        "tp1": tp.get("take_profit_1") or tp.get("tp1") or tp.get("take_profit") if isinstance(tp, dict) else None,
        "direction": tp.get("direction") if isinstance(tp, dict) else None,
    })

print(f"Total events: {len(all_events)}")
print(f"Decisions: {Counter(e['decision'] for e in all_events)}")

# ─── Step 3: Load session trade outcomes ────────────────────────────────
print("\n" + "=" * 70)
print("STEP 3: Loading session trade outcomes")
print("=" * 70)

session_trades = []
for f in sorted(SESSIONS_DIR.glob("*.json")):
    d = json.load(open(f))
    date_str = d.get("date", "")
    ts = d.get("trade_summary", {})
    if not isinstance(ts, dict):
        continue
    trades_list = ts.get("trades", [])
    if trades_list:
        for trade in trades_list:
            session_trades.append({
                "date": date_str,
                "trade_id": trade.get("trade_id", ""),
                "kill_zone": trade.get("kill_zone", ""),
                "outcome": trade.get("outcome", ""),
                "r_multiple": trade.get("r_multiple", 0),
                "framework": trade.get("framework", ""),
                "mfe_r": trade.get("mfe_r"),
                "mae_r": trade.get("mae_r"),
            })
    elif ts.get("trade_taken") and ts.get("outcome"):
        session_trades.append({
            "date": date_str,
            "trade_id": ts.get("trade_id", ""),
            "kill_zone": "",
            "outcome": ts.get("outcome", ""),
            "r_multiple": ts.get("r_multiple", 0),
            "framework": "",
        })

print(f"Session trades: {len(session_trades)}")
ai_wins = sum(1 for t in session_trades if t["outcome"] == "WIN")
ai_total = len(session_trades)
ai_r = sum(t["r_multiple"] for t in session_trades)
print(f"AI WR: {ai_wins}/{ai_total} = {ai_wins/ai_total:.1%}")
print(f"AI Total R: {ai_r:+.2f}")
print(f"AI Avg R/trade: {ai_r/ai_total:+.3f}")

# ─── Step 4: Load M15 data for each instrument ─────────────────────────
print("\n" + "=" * 70)
print("STEP 4: Loading M15 data")
print("=" * 70)

m15_data = {}
instrument_file_map = {
    "XAUUSD": "XAUUSD_M15.csv",
    "USDJPY": "USDJPY_M15.csv",
    "GBPJPY": "GBPJPY_M15.csv",
    "GBPUSD": "GBPUSD_M15.csv",
    "NZDUSD": "NZDUSD_M15.csv",
    "US30": "US30_cash_M15.csv",
}

for inst, fname in instrument_file_map.items():
    fpath = DATA_DIR / fname
    if fpath.exists():
        df = pd.read_csv(fpath)
        df["time"] = pd.to_datetime(df["time"])
        m15_data[inst] = df
        print(f"  {inst}: {len(df)} candles ({df['time'].min()} to {df['time'].max()})")
    else:
        print(f"  {inst}: FILE NOT FOUND ({fname})")

# ─── Step 5: Define mechanical populations ──────────────────────────────
print("\n" + "=" * 70)
print("STEP 5: Defining mechanical populations")
print("=" * 70)

# Mechanical signal = OB POI identified + m15 CHoCH confirmed
# This is the core entry trigger without AI judgment
mech_all = [e for e in all_events
            if e.get("poi_identified")
            and e.get("poi_type") == "OB"
            and e.get("m15_choch") == True]

print(f"Mechanical signal (OB + m15_choch): {len(mech_all)}")
print(f"  CANDIDATE: {sum(1 for e in mech_all if e['decision'] == 'CANDIDATE')}")
print(f"  NO_TRADE: {sum(1 for e in mech_all if e['decision'] == 'NO_TRADE')}")
print(f"  By instrument: {Counter(e['instrument'] for e in mech_all)}")

# Stricter: also require h4 alignment
mech_strict = [e for e in mech_all if e.get("h4_aligned") == True]
print(f"\nStrict mechanical (+ h4 aligned): {len(mech_strict)}")
print(f"  CANDIDATE: {sum(1 for e in mech_strict if e['decision'] == 'CANDIDATE')}")
print(f"  NO_TRADE: {sum(1 for e in mech_strict if e['decision'] == 'NO_TRADE')}")

# ─── Step 6: Simulate mechanical entries ────────────────────────────────
print("\n" + "=" * 70)
print("STEP 6: Simulating mechanical entries for NO_TRADE events")
print("=" * 70)


def parse_cid_time(cid):
    """Parse CID like '2025-10-01_london_0715' to datetime."""
    parts = cid.split("_")
    date_str = parts[0]
    time_str = parts[-1]
    if len(time_str) == 4 and time_str.isdigit():
        h, m = int(time_str[:2]), int(time_str[2:])
        return datetime.strptime(date_str, "%Y-%m-%d").replace(hour=h, minute=m)
    return None


def simulate_trade(entry_time, entry_price, sl_price, tp_price,
                   direction, candle_df, max_bars=48):
    """Walk forward through M15 candles to determine WIN/LOSS/TIMEOUT."""
    future = candle_df[candle_df["time"] > entry_time].head(max_bars)
    if len(future) == 0:
        return "NO_DATA", 0.0

    sl_dist = abs(entry_price - sl_price)
    if sl_dist < 1e-6:
        return "INVALID", 0.0

    for _, bar in future.iterrows():
        if direction == "LONG":
            if bar["low"] <= sl_price:
                return "LOSS", -1.0
            if bar["high"] >= tp_price:
                return "WIN", abs(tp_price - entry_price) / sl_dist
        else:  # SHORT
            if bar["high"] >= sl_price:
                return "LOSS", -1.0
            if bar["low"] <= tp_price:
                return "WIN", abs(entry_price - tp_price) / sl_dist

    # Timeout at last bar
    last_close = future.iloc[-1]["close"]
    if direction == "LONG":
        pnl = (last_close - entry_price) / sl_dist
    else:
        pnl = (entry_price - last_close) / sl_dist
    return "TIMEOUT", round(pnl, 3)


def get_pip_size(instrument):
    """Return approximate pip/point size for SL buffer."""
    if instrument == "XAUUSD":
        return 1.0  # $1 per point
    elif instrument in ("USDJPY", "GBPJPY"):
        return 0.01
    elif instrument in ("GBPUSD", "EURUSD", "NZDUSD"):
        return 0.0001
    elif instrument in ("US30", "NAS100"):
        return 1.0
    return 0.01


# For CANDIDATE events: use actual session outcomes where available
# For NO_TRADE events: simulate using zone/poi_price + M15 data
# Mechanical entry rules:
#   - Direction: zone=discount -> LONG, zone=premium -> SHORT, neutral -> skip
#   - Entry: poi_price (the OB level price retested)
#   - SL: 30 pips beyond OB level (instrument-adjusted)
#   - TP: 2.0R from entry (conservative mechanical target)

MECHANICAL_RR = 2.0  # Fixed R:R for mechanical entries
SL_BUFFER_MULTIPLIER = 1.5  # SL = entry ± (buffer * pip_size * N)

# Map session outcomes by date+kz for matching
session_outcome_map = {}
for t in session_trades:
    key = f"{t['date']}_{t['kill_zone']}"
    session_outcome_map[key] = t

# Deduplicate mechanical events: same date+kz = same trade opportunity
# Take the first CANDIDATE or first NO_TRADE per date+kz
mech_deduped = {}
for e in mech_all:
    parts = e["cid"].split("_")
    if len(parts) >= 3:
        date = parts[0]
        kz = parts[1]
        key = f"{date}_{kz}"
        # Prefer CANDIDATE (actual trade) over NO_TRADE
        if key not in mech_deduped or (e["decision"] == "CANDIDATE" and mech_deduped[key]["decision"] != "CANDIDATE"):
            mech_deduped[key] = e

print(f"Deduplicated mechanical events: {len(mech_deduped)}")
print(f"  CANDIDATE: {sum(1 for e in mech_deduped.values() if e['decision'] == 'CANDIDATE')}")
print(f"  NO_TRADE: {sum(1 for e in mech_deduped.values() if e['decision'] == 'NO_TRADE')}")

# Simulate
mech_results = []
sim_stats = Counter()

for key, event in sorted(mech_deduped.items()):
    result = {
        "key": key,
        "cid": event["cid"],
        "instrument": event["instrument"],
        "decision": event["decision"],
        "zone": event["zone"],
        "h4_aligned": event["h4_aligned"],
        "sweep": event["sweep"],
        "displacement_quality": event["displacement_quality"],
    }

    if event["decision"] == "CANDIDATE":
        # Use actual outcome from session
        session_key = key
        if session_key in session_outcome_map:
            so = session_outcome_map[session_key]
            result["outcome"] = so["outcome"]
            result["r_multiple"] = so["r_multiple"]
            result["source"] = "actual"
            sim_stats["actual"] += 1
        elif event["entry"] and event["sl"] and event["tp1"]:
            # CANDIDATE but no session match — simulate
            entry_time = parse_cid_time(event["cid"])
            inst = event["instrument"]
            if entry_time and inst in m15_data:
                outcome, r = simulate_trade(
                    entry_time, event["entry"], event["sl"], event["tp1"],
                    event["direction"] or ("LONG" if event["zone"] == "discount" else "SHORT"),
                    m15_data[inst],
                )
                result["outcome"] = outcome
                result["r_multiple"] = r
                result["source"] = "simulated_candidate"
                sim_stats["simulated_candidate"] += 1
            else:
                result["outcome"] = "NO_DATA"
                result["r_multiple"] = 0
                result["source"] = "no_data"
                sim_stats["no_data_candidate"] += 1
        else:
            result["outcome"] = "NO_PARAMS"
            result["r_multiple"] = 0
            result["source"] = "no_params"
            sim_stats["no_params"] += 1
    else:
        # NO_TRADE — simulate mechanical entry
        inst = event["instrument"]
        poi_price = event["poi_price"]
        zone = event["zone"]
        entry_time = parse_cid_time(event["cid"])

        if not poi_price or not isinstance(poi_price, (int, float)):
            result["outcome"] = "NO_PRICE"
            result["r_multiple"] = 0
            result["source"] = "no_price"
            sim_stats["no_price"] += 1
            mech_results.append(result)
            continue

        if zone == "neutral" or not zone:
            # Can't determine direction mechanically
            result["outcome"] = "SKIP_NEUTRAL"
            result["r_multiple"] = 0
            result["source"] = "neutral_zone"
            sim_stats["neutral_zone"] += 1
            mech_results.append(result)
            continue

        if inst not in m15_data or not entry_time:
            result["outcome"] = "NO_DATA"
            result["r_multiple"] = 0
            result["source"] = "no_data"
            sim_stats["no_data_notrade"] += 1
            mech_results.append(result)
            continue

        # Determine direction and SL/TP
        pip = get_pip_size(inst)

        # Get the M15 candle at entry time for actual price
        df = m15_data[inst]
        entry_candle = df[df["time"] == pd.Timestamp(entry_time)]
        if entry_candle.empty:
            # Find nearest candle
            entry_candle = df[df["time"] <= pd.Timestamp(entry_time)].tail(1)
        if entry_candle.empty:
            result["outcome"] = "NO_DATA"
            result["r_multiple"] = 0
            result["source"] = "no_candle"
            sim_stats["no_candle"] += 1
            mech_results.append(result)
            continue

        actual_price = entry_candle.iloc[0]["close"]

        if zone == "discount":
            direction = "LONG"
            # SL below POI
            sl_dist = abs(actual_price - poi_price) + pip * 30
            if sl_dist < pip * 10:
                sl_dist = pip * 30
            entry = actual_price
            sl = entry - sl_dist
            tp = entry + sl_dist * MECHANICAL_RR
        elif zone == "premium":
            direction = "SHORT"
            sl_dist = abs(poi_price - actual_price) + pip * 30
            if sl_dist < pip * 10:
                sl_dist = pip * 30
            entry = actual_price
            sl = entry + sl_dist
            tp = entry - sl_dist * MECHANICAL_RR
        else:
            result["outcome"] = "SKIP_ZONE"
            result["r_multiple"] = 0
            result["source"] = "unknown_zone"
            sim_stats["unknown_zone"] += 1
            mech_results.append(result)
            continue

        outcome, r = simulate_trade(entry_time, entry, sl, tp, direction, df)
        result["outcome"] = outcome
        result["r_multiple"] = r
        result["source"] = "simulated_notrade"
        result["sim_entry"] = entry
        result["sim_sl"] = sl
        result["sim_tp"] = tp
        result["sim_direction"] = direction
        sim_stats["simulated_notrade"] += 1

    mech_results.append(result)

print(f"\nSimulation stats: {dict(sim_stats)}")

# ─── Step 7: Compare populations ────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 7: RESULTS — MECHANICAL vs AI COMPARISON")
print("=" * 70)

# AI population = session trades (actual outcomes)
print(f"\n{'AI-SELECTED TRADES':^50}")
print("-" * 50)
ai_total = len(session_trades)
ai_wins = sum(1 for t in session_trades if t["outcome"] == "WIN")
ai_losses = sum(1 for t in session_trades if t["outcome"] == "LOSS")
ai_r = sum(t["r_multiple"] for t in session_trades)
print(f"  Trades:     {ai_total}")
print(f"  Wins:       {ai_wins}")
print(f"  Losses:     {ai_losses}")
print(f"  Win Rate:   {ai_wins/ai_total:.1%}")
print(f"  Total R:    {ai_r:+.2f}")
print(f"  Avg R/trade: {ai_r/ai_total:+.3f}")

# Mechanical population = all simulated + actual
valid_mech = [r for r in mech_results if r["outcome"] in ("WIN", "LOSS", "TIMEOUT")]
mech_total = len(valid_mech)
mech_wins = sum(1 for r in valid_mech if r["outcome"] == "WIN")
mech_losses = sum(1 for r in valid_mech if r["outcome"] == "LOSS")
mech_timeouts = sum(1 for r in valid_mech if r["outcome"] == "TIMEOUT")
mech_r = sum(r["r_multiple"] for r in valid_mech)

print(f"\n{'MECHANICAL TRADES (all OB + m15_choch)':^50}")
print("-" * 50)
print(f"  Trades:     {mech_total}")
print(f"  Wins:       {mech_wins}")
print(f"  Losses:     {mech_losses}")
print(f"  Timeouts:   {mech_timeouts}")
print(f"  Win Rate:   {mech_wins/mech_total:.1%}" if mech_total else "  N/A")
print(f"  Total R:    {mech_r:+.2f}")
print(f"  Avg R/trade: {mech_r/mech_total:+.3f}" if mech_total else "  N/A")

# Break down NO_TRADE simulated results
nt_sim = [r for r in valid_mech if r["source"] == "simulated_notrade"]
nt_total = len(nt_sim)
nt_wins = sum(1 for r in nt_sim if r["outcome"] == "WIN")
nt_losses = sum(1 for r in nt_sim if r["outcome"] == "LOSS")
nt_timeouts = sum(1 for r in nt_sim if r["outcome"] == "TIMEOUT")
nt_r = sum(r["r_multiple"] for r in nt_sim)

print(f"\n{'AI-REJECTED EVENTS (simulated)':^50}")
print("-" * 50)
print(f"  Trades:     {nt_total}")
print(f"  Wins:       {nt_wins}")
print(f"  Losses:     {nt_losses}")
print(f"  Timeouts:   {nt_timeouts}")
if nt_total > 0:
    print(f"  Win Rate:   {nt_wins/nt_total:.1%}")
    print(f"  Total R:    {nt_r:+.2f}")
    print(f"  Avg R/trade: {nt_r/nt_total:+.3f}")

# Gap analysis
print(f"\n{'COMPARISON':^50}")
print("=" * 50)
if mech_total > 0:
    ai_avg = ai_r / ai_total
    mech_avg = mech_r / mech_total
    gap = ai_avg - mech_avg

    print(f"  AI avg R/trade:         {ai_avg:+.3f}")
    print(f"  Mechanical avg R/trade: {mech_avg:+.3f}")
    print(f"  Gap (AI - Mechanical):  {gap:+.3f}")
    print(f"  AI WR:                  {ai_wins/ai_total:.1%}")
    print(f"  Mechanical WR:          {mech_wins/mech_total:.1%}")
    print()
    if gap > 0.05:
        print("  >>> AI ADDS VALUE (+0.05R threshold met)")
        print(f"  >>> The AI filter improves avg R/trade by {gap:+.3f}")
    elif gap < -0.05:
        print("  >>> AI HURTS PERFORMANCE (-0.05R threshold breached)")
        print(f"  >>> Mechanical entries beat AI by {-gap:+.3f} R/trade")
    else:
        print("  >>> AI IS NEUTRAL (within +/-0.05R)")
        print("  >>> Consider removing AI for cost savings")

# By instrument breakdown
print(f"\n{'BY INSTRUMENT':^50}")
print("-" * 50)
for inst in sorted(set(e["instrument"] for e in valid_mech)):
    inst_events = [r for r in valid_mech if r["instrument"] == inst]
    inst_total = len(inst_events)
    inst_wins = sum(1 for r in inst_events if r["outcome"] == "WIN")
    inst_r = sum(r["r_multiple"] for r in inst_events)
    if inst_total > 0:
        print(f"  {inst:10s}: {inst_total:3d} trades, WR={inst_wins/inst_total:.0%}, TotalR={inst_r:+.1f}, AvgR={inst_r/inst_total:+.3f}")

# AI vs Mechanical by instrument (for AI, we need to match instruments)
# Session trades don't have instrument — match via batch data
print(f"\n{'AI TRADES BY INSTRUMENT (estimated)':^50}")
print("-" * 50)
ai_by_inst = [r for r in valid_mech if r["source"] == "actual"]
for inst in sorted(set(r["instrument"] for r in ai_by_inst)):
    ie = [r for r in ai_by_inst if r["instrument"] == inst]
    if ie:
        t = len(ie)
        w = sum(1 for r in ie if r["outcome"] == "WIN")
        r_sum = sum(r["r_multiple"] for r in ie)
        print(f"  {inst:10s}: {t:3d} trades, WR={w/t:.0%}, TotalR={r_sum:+.1f}, AvgR={r_sum/t:+.3f}")

# ─── Step 8: Detailed NO_TRADE analysis ─────────────────────────────────
print(f"\n{'NO_TRADE EVENTS: WOULD-HAVE-BEEN RESULTS':^60}")
print("=" * 60)

nt_winners = [r for r in nt_sim if r["outcome"] == "WIN"]
nt_losers = [r for r in nt_sim if r["outcome"] == "LOSS"]
nt_to = [r for r in nt_sim if r["outcome"] == "TIMEOUT"]

print(f"\nMissed winners (AI correctly rejected = NO):   {len(nt_losers)} losers avoided")
print(f"Missed winners (AI incorrectly rejected = YES): {len(nt_winners)} winners missed")
print(f"Timeouts:                                       {len(nt_to)}")

if nt_winners:
    print(f"\nMissed winners R: {sum(r['r_multiple'] for r in nt_winners):+.2f}")
if nt_losers:
    print(f"Avoided losers R: {sum(r['r_multiple'] for r in nt_losers):+.2f}")
if nt_to:
    print(f"Timeout R:        {sum(r['r_multiple'] for r in nt_to):+.2f}")

net_from_rejected = nt_r
print(f"\nNet R from ALL rejected events: {net_from_rejected:+.2f}")
if net_from_rejected < 0:
    print(">>> AI was RIGHT to reject these — net negative R avoided")
else:
    print(">>> AI was WRONG to reject these — net positive R missed")

# Save detailed results
output = {
    "ai_population": {
        "trades": ai_total,
        "wins": ai_wins,
        "losses": ai_losses,
        "win_rate": round(ai_wins / ai_total, 3),
        "total_r": round(ai_r, 2),
        "avg_r_per_trade": round(ai_r / ai_total, 3),
    },
    "mechanical_population": {
        "trades": mech_total,
        "wins": mech_wins,
        "losses": mech_losses,
        "timeouts": mech_timeouts,
        "win_rate": round(mech_wins / mech_total, 3) if mech_total else 0,
        "total_r": round(mech_r, 2),
        "avg_r_per_trade": round(mech_r / mech_total, 3) if mech_total else 0,
    },
    "rejected_events": {
        "total": nt_total,
        "wins": nt_wins,
        "losses": nt_losses,
        "timeouts": nt_timeouts,
        "net_r": round(nt_r, 2),
    },
    "gap": {
        "avg_r_gap": round((ai_r / ai_total) - (mech_r / mech_total), 3) if mech_total else 0,
        "wr_gap_pp": round((ai_wins / ai_total - mech_wins / mech_total) * 100, 1) if mech_total else 0,
    },
    "simulation_stats": dict(sim_stats),
    "all_results": mech_results,
}

with open("mechanical_backtest_results.json", "w") as f:
    json.dump(output, f, indent=2, default=str)

print(f"\nResults saved to mechanical_backtest_results.json")
