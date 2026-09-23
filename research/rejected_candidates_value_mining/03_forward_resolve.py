"""
Section 2: Forward-resolution of every rejected candle.

For each REJECTED row (NO_TRADE / REJECTED_L2 / BLOCKED_LIMIT):
  - Look up M15 candle data + H1 forward 12 candles
  - Synthesize entry / SL / TP
  - Determine if TP or SL hits first

Synthesis rules:
  - Direction: use AI-evaluated direction if available (REJECTED_L2 / candidate-side NO_TRADEs).
    Otherwise use H1 structure direction (mso_h1_structure_direction or out_bias).
  - Entry: M15 close at the rejection candle.
  - Stop loss distance: 1.0 * M15-ATR(14)
  - Take profit: 1.5R (1.5 * SL distance)
  - Forward window: next 12 H1 candles (from candle_time + 1 H1).
    For each H1 candle, intra-bar TP/SL hit check; tie => SL wins (conservative).

Output:
  forward_resolution.jsonl - per-row resolution with R outcome
  forward_summary_per_bucket.csv - per-bucket aggregate stats
"""
import json
import math
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

ROOT = Path("C:/Users/MSI/Documents/ai-trading-agent")
OUT_DIR = ROOT / "research/rejected_candidates_value_mining"
DATA_DIR = ROOT / "data/historical_2026"

INSTRUMENTS = ["XAUUSD", "USDJPY", "GBPJPY", "GBPUSD", "US30_cash",
               "EURUSD", "GER40", "NAS100", "UK100", "XAGUSD"]


def load_csv(symbol, tf):
    fp = DATA_DIR / f"{symbol}_{tf}.csv"
    if not fp.exists():
        return None
    df = pd.read_csv(fp)
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    return df


def normalize_inst(inst):
    """Phase1 / tier2 inst names → CSV file naming."""
    if inst == "US30":
        return "US30_cash"
    return inst


def m15_atr(m15_df, time_idx, period=14):
    """Return ATR(14) value at the M15 candle time_idx."""
    if time_idx < period:
        return None
    sub = m15_df.iloc[time_idx - period: time_idx + 1]
    high = sub["high"]
    low = sub["low"]
    close = sub["close"]
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return float(tr.tail(period).mean())


def find_idx(df, ts):
    """Return integer index of df row whose 'time' equals ts. Else None."""
    try:
        ts_pd = pd.to_datetime(ts, utc=True)
    except Exception:
        return None
    matches = df.index[df["time"] == ts_pd]
    if len(matches) == 0:
        return None
    return int(matches[0])


def resolve_one(row, m15_dfs, h1_dfs):
    """Forward-resolve one rejected row. Return dict with outcome fields."""
    inst = normalize_inst(row["_instrument"])
    m15 = m15_dfs.get(inst)
    h1 = h1_dfs.get(inst)
    if m15 is None or h1 is None:
        return {"resolved": False, "reason": "no_data_csv"}

    ts = row.get("timestamp_utc")
    if not ts:
        return {"resolved": False, "reason": "no_timestamp"}

    m15_idx = find_idx(m15, ts)
    if m15_idx is None:
        return {"resolved": False, "reason": "ts_not_in_m15"}

    # ATR(14) on M15
    atr = m15_atr(m15, m15_idx, period=14)
    if atr is None or atr <= 0:
        return {"resolved": False, "reason": "atr_unavailable"}

    # Entry = M15 close at rejection candle
    entry_price = float(m15.iloc[m15_idx]["close"])

    # Direction inference order:
    # 1) ai_direction_evaluated (LONG/SHORT)
    # 2) out_direction (LONG/SHORT)
    # 3) h1_direction (bullish→LONG, bearish→SHORT)
    direction = None
    aid = (row.get("ai_direction_evaluated") or "").upper()
    if aid in ("LONG", "SHORT"):
        direction = aid
    if not direction:
        od = (row.get("out_direction") or "").upper()
        if od in ("LONG", "SHORT"):
            direction = od
    if not direction:
        h1d = (row.get("h1_direction") or "").lower()
        if "bull" in h1d:
            direction = "LONG"
        elif "bear" in h1d:
            direction = "SHORT"
    if direction not in ("LONG", "SHORT"):
        return {"resolved": False, "reason": "no_direction"}

    if direction == "LONG":
        sl = entry_price - atr
        tp = entry_price + 1.5 * atr
    else:
        sl = entry_price + atr
        tp = entry_price - 1.5 * atr

    # Find H1 start: next H1 candle after the M15 candle
    candle_time = pd.to_datetime(ts, utc=True)
    # M15 candle covers [candle_time, candle_time + 15 min]; entry is at candle close.
    next_h1_ts = (candle_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

    # Find H1 idx
    h1_matches = h1.index[h1["time"] >= next_h1_ts]
    if len(h1_matches) == 0:
        return {"resolved": False, "reason": "no_h1_forward"}
    h1_start = int(h1_matches[0])
    h1_window = h1.iloc[h1_start: h1_start + 12]
    if len(h1_window) == 0:
        return {"resolved": False, "reason": "h1_window_empty"}

    # Check for TP/SL in window
    outcome = None
    exit_idx = None
    for i, cand in h1_window.iterrows():
        chigh = cand["high"]
        clow = cand["low"]
        if direction == "LONG":
            sl_hit = clow <= sl
            tp_hit = chigh >= tp
            # if both hit in same candle, SL wins (conservative)
            if sl_hit and tp_hit:
                outcome = "SL"
                exit_idx = i
                break
            elif sl_hit:
                outcome = "SL"
                exit_idx = i
                break
            elif tp_hit:
                outcome = "TP"
                exit_idx = i
                break
        else:
            sl_hit = chigh >= sl
            tp_hit = clow <= tp
            if sl_hit and tp_hit:
                outcome = "SL"
                exit_idx = i
                break
            elif sl_hit:
                outcome = "SL"
                exit_idx = i
                break
            elif tp_hit:
                outcome = "TP"
                exit_idx = i
                break

    if outcome is None:
        # Use last close to compute partial R (mark-to-market)
        last_close = float(h1_window.iloc[-1]["close"])
        if direction == "LONG":
            r_mtm = (last_close - entry_price) / atr
        else:
            r_mtm = (entry_price - last_close) / atr
        return {
            "resolved": True,
            "outcome": "EXPIRY",
            "r_multiple": float(r_mtm),
            "entry": entry_price,
            "sl": sl,
            "tp": tp,
            "atr": atr,
            "direction": direction,
            "exit_h1_idx": int(h1_window.index[-1]),
        }

    r_mult = 1.5 if outcome == "TP" else -1.0
    return {
        "resolved": True,
        "outcome": outcome,
        "r_multiple": r_mult,
        "entry": entry_price,
        "sl": sl,
        "tp": tp,
        "atr": atr,
        "direction": direction,
        "exit_h1_idx": int(exit_idx),
    }


def main():
    # Load rejected
    rejected = []
    with open(OUT_DIR / "rejected_rows_bucketed.jsonl", "r") as f:
        for line in f:
            rejected.append(json.loads(line))
    print(f"Total rejected: {len(rejected)}")

    # Load CSVs
    m15_dfs = {}
    h1_dfs = {}
    for inst in INSTRUMENTS:
        m = load_csv(inst, "M15")
        h = load_csv(inst, "H1")
        if m is not None and h is not None:
            m15_dfs[inst] = m
            h1_dfs[inst] = h
            print(f"Loaded {inst}: M15 {len(m)} rows, H1 {len(h)} rows")

    # Resolve
    resolved_rows = []
    for i, row in enumerate(rejected):
        res = resolve_one(row, m15_dfs, h1_dfs)
        out = {
            "_instrument": row["_instrument"],
            "_slice": row.get("_slice"),
            "_source": row.get("_source"),
            "timestamp_utc": row.get("timestamp_utc"),
            "kill_zone": row.get("kill_zone"),
            "decision": row.get("decision"),
            "bucket_top": row.get("bucket_top"),
            "bucket_sub": row.get("bucket_sub"),
            "ai_direction_evaluated": row.get("ai_direction_evaluated"),
            "h1_direction": row.get("h1_direction"),
            "no_trade_reason": row.get("no_trade_reason"),
            "l2_reason": row.get("l2_reason"),
            "_resolved": res.get("resolved"),
            "_resolve_reason": res.get("reason"),
            "fwd_outcome": res.get("outcome"),
            "fwd_r": res.get("r_multiple"),
            "fwd_entry": res.get("entry"),
            "fwd_sl": res.get("sl"),
            "fwd_tp": res.get("tp"),
            "fwd_atr": res.get("atr"),
            "fwd_direction": res.get("direction"),
        }
        resolved_rows.append(out)

    # Save
    with open(OUT_DIR / "forward_resolution.jsonl", "w") as f:
        for r in resolved_rows:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"Wrote {OUT_DIR / 'forward_resolution.jsonl'}")

    # Summary
    total_resolved = sum(1 for r in resolved_rows if r["_resolved"])
    total_unresolved = len(resolved_rows) - total_resolved
    print(f"Resolved: {total_resolved} ({100*total_resolved/len(resolved_rows):.1f}%)")
    print(f"Unresolved: {total_unresolved}")

    # Reason breakdown for unresolved
    from collections import Counter
    unresolved_reasons = Counter(r["_resolve_reason"] for r in resolved_rows if not r["_resolved"])
    print("Unresolved reasons:")
    for k, v in unresolved_reasons.most_common():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
