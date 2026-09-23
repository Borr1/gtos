"""
Apply corrected LIMIT-fill forward-resolution to backtest L2 + BLOCKED_LIMIT rejects.

For each row with entry_price/stop_loss/take_profit_1 set:
  - Step 1: forward window 12 H1 candles from candle_time
  - Step 2: find first H1 where LIMIT entry would have filled
  - Step 3: from fill onwards, check SL/TP intra-bar
  - Step 4: if neither, mark-to-market on last close
  - If never filled: outcome = NOT_FILLED, R = 0

Output:
  bt_corrected_l2.jsonl - per-row corrected results
  bt_corrected_l2_summary.csv - per-bucket summary
"""
import json
import os
from pathlib import Path
from datetime import timedelta
from collections import Counter, defaultdict
import pandas as pd
import math

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
    if inst == "US30":
        return "US30_cash"
    return inst


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    lo = (centre - spread) / denom
    hi = (centre + spread) / denom
    return (lo, hi)


def resolve_limit(entry, sl, tp1, direction, h1_window):
    if not entry or not sl or not tp1:
        return {"resolved": False, "outcome": "no_params", "r": None}
    r_unit = abs(entry - sl)
    if r_unit == 0:
        return {"resolved": False, "outcome": "zero_r", "r": None}
    fill_idx = None
    for i, c in h1_window.iterrows():
        chigh = c["high"]; clow = c["low"]
        if clow <= entry <= chigh:
            fill_idx = i; break
    if fill_idx is None:
        return {"resolved": True, "filled": False, "outcome": "NOT_FILLED", "r": 0.0}
    post_fill = h1_window.loc[fill_idx:]
    for i, c in post_fill.iterrows():
        chigh = c["high"]; clow = c["low"]
        if direction == "LONG":
            sl_hit = clow <= sl
            tp_hit = chigh >= tp1
        else:
            sl_hit = chigh >= sl
            tp_hit = clow <= tp1
        if sl_hit and tp_hit:
            return {"resolved": True, "filled": True, "outcome": "SL_AND_TP", "r": -1.0}
        elif sl_hit:
            return {"resolved": True, "filled": True, "outcome": "SL", "r": -1.0}
        elif tp_hit:
            if direction == "LONG":
                r = (tp1 - entry) / r_unit
            else:
                r = (entry - tp1) / r_unit
            return {"resolved": True, "filled": True, "outcome": "TP", "r": r}
    last_close = float(post_fill.iloc[-1]["close"])
    if direction == "LONG":
        r = (last_close - entry) / r_unit
    else:
        r = (entry - last_close) / r_unit
    return {"resolved": True, "filled": True, "outcome": "EXPIRY", "r": r}


def main():
    h1_dfs = {inst: load_csv(inst, "H1") for inst in INSTRUMENTS}

    rejected = []
    with open(OUT_DIR / "rejected_rows_bucketed.jsonl", "r") as f:
        for line in f:
            rejected.append(json.loads(line))

    # Filter to rows with entry/sl/tp1 (LIMIT semantic)
    has_params = [r for r in rejected if r.get("entry_price") and r.get("stop_loss") and r.get("take_profit_1")]
    print(f"Rows with LIMIT params: {len(has_params)}")
    print(f"  By decision: {Counter(r['decision'] for r in has_params)}")
    print(f"  By bucket_sub: {Counter(r['bucket_sub'] for r in has_params)}")

    # Resolve
    output_rows = []
    for r in has_params:
        inst = normalize_inst(r["_instrument"])
        h1 = h1_dfs.get(inst)
        if h1 is None:
            continue
        ts = pd.to_datetime(r.get("timestamp_utc"), utc=True)
        next_h1 = (ts + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        h1_matches = h1.index[h1["time"] >= next_h1]
        if len(h1_matches) == 0:
            continue
        h1_start = int(h1_matches[0])
        h1_window = h1.iloc[h1_start: h1_start + 12]
        if len(h1_window) == 0:
            continue
        direction = (r.get("out_direction") or r.get("ai_direction_evaluated") or "").upper()
        if direction not in ("LONG", "SHORT"):
            continue
        res = resolve_limit(float(r["entry_price"]), float(r["stop_loss"]), float(r["take_profit_1"]),
                            direction, h1_window)
        if res.get("resolved") is False:
            continue
        out = {
            "_instrument": r["_instrument"],
            "_slice": r.get("_slice"),
            "_source": r.get("_source"),
            "timestamp_utc": r.get("timestamp_utc"),
            "kill_zone": r.get("kill_zone"),
            "decision": r.get("decision"),
            "bucket_sub": r.get("bucket_sub"),
            "direction": direction,
            "entry": r.get("entry_price"),
            "sl": r.get("stop_loss"),
            "tp1": r.get("take_profit_1"),
            "l2_reason": r.get("l2_reason"),
            "filled": res.get("filled"),
            "outcome": res.get("outcome"),
            "fwd_r": res.get("r"),
        }
        output_rows.append(out)

    print(f"Resolved (corrected): {len(output_rows)}")

    # Per-bucket summary
    by_bucket = defaultdict(list)
    for r in output_rows:
        by_bucket[r["bucket_sub"]].append(r)

    print()
    print("=== Per-bucket corrected (LIMIT-fill) summary ===")
    summary = []
    for bucket, rows in sorted(by_bucket.items()):
        n_total = len(rows)
        not_filled = sum(1 for r in rows if r["outcome"] == "NOT_FILLED")
        filled = [r for r in rows if r.get("filled")]
        if not filled:
            print(f"  {bucket:30s}  n={n_total}  not_filled={not_filled}  NO_FILL")
            continue
        rs = [r["fwd_r"] for r in filled]
        wins = sum(1 for x in rs if x >= 1.4 - 1e-9)
        all_rs = rs + [0.0] * not_filled
        total_r = sum(all_rs)
        wr = wins / n_total
        lo, hi = wilson_ci(wins, n_total)
        exp_r = total_r / n_total
        n_months = 4
        per_month = total_r / n_months
        print(f"  {bucket:30s}  n={n_total:4d}  not_filled={not_filled:4d}  filled={len(filled):4d}  "
              f"WR={wr:.3f} CI[{lo:.3f},{hi:.3f}]  ExpR={exp_r:+.3f}  TotalR={total_r:+.1f}  /mo={per_month:+.2f}")
        summary.append({"bucket": bucket, "n_total": n_total, "not_filled": not_filled,
                        "filled": len(filled), "wr": wr, "wr_ci_lo": lo, "wr_ci_hi": hi,
                        "exp_r": exp_r, "total_r": total_r, "per_month_r": per_month})

    # Save
    with open(OUT_DIR / "bt_corrected_l2.jsonl", "w") as f:
        for r in output_rows:
            f.write(json.dumps(r, default=str) + "\n")
    import csv
    if summary:
        with open(OUT_DIR / "bt_corrected_l2_summary.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
            w.writeheader()
            for row in summary:
                w.writerow(row)


if __name__ == "__main__":
    main()
