"""
Corrected live L2 forward-resolution.

Live trades are LIMIT orders — they only fill if price retraces to entry.
Logic:
  1. Forward window: 12 H1 candles after candle_time.
  2. Find first H1 where price intra-bar touches entry_price (LIMIT fill).
     - If entry not hit in window: outcome = NOT_FILLED (R = 0).
  3. Once filled, check subsequent candles for SL/TP hit (same window remaining).
  4. If neither SL nor TP within window: mark-to-market R using last close.

This properly models: AI proposes a LIMIT, if rejected we still need price to retrace
to even consider what would have happened.
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

INSTRUMENTS = ["XAUUSD", "USDJPY", "GBPJPY", "GBPUSD", "US30_cash"]


def load_csv(symbol, tf):
    fp = DATA_DIR / f"{symbol}_{tf}.csv"
    if not fp.exists():
        return None
    df = pd.read_csv(fp)
    df["time"] = pd.to_datetime(df["time"], utc=True, errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    return df


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


def get_l2_failed_check(trade):
    l2 = trade.get("decision_pipeline", {}).get("level2_verification", {})
    if not isinstance(l2, dict):
        return None
    checks = l2.get("checks", [])
    for c in checks:
        if c.get("status") == "FAIL":
            return c.get("name")
    return None


def main():
    h1_dfs = {}
    for inst in INSTRUMENTS:
        h1_dfs[inst] = load_csv(inst, "H1")

    tr_dir = ROOT / "knowledge_base/trade_records"
    trades = []
    for inst in os.listdir(tr_dir):
        ind = tr_dir / inst
        if not ind.is_dir():
            continue
        for fname in os.listdir(ind):
            if fname.endswith(".json"):
                with open(ind / fname, "r") as f:
                    try:
                        t = json.load(f)
                        t["_instrument"] = inst
                        t["_file"] = fname
                        trades.append(t)
                    except Exception:
                        pass

    l2_rejected = [t for t in trades if t.get("decision_pipeline", {}).get("final_outcome") == "REJECTED_L2"]
    print(f"Live L2 rejected: {len(l2_rejected)}")

    def resolve_with_limit_fill(trade):
        inst = trade["_instrument"]
        if inst not in h1_dfs or h1_dfs[inst] is None:
            return {"resolved": False, "reason": "no_data"}
        h1 = h1_dfs[inst]
        ts_str = trade.get("metadata", {}).get("candle_time")
        if not ts_str:
            return {"resolved": False, "reason": "no_ts"}
        ts = pd.to_datetime(ts_str, utc=True)
        tp = trade.get("trade_parameters", {})
        direction = tp.get("direction")
        entry = tp.get("entry_price")
        sl = tp.get("stop_loss")
        tp1 = tp.get("take_profit_1")
        if direction is None or entry is None or sl is None or tp1 is None:
            return {"resolved": False, "reason": "missing_params"}
        entry = float(entry); sl = float(sl); tp1 = float(tp1)
        next_h1 = (ts + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        h1_matches = h1.index[h1["time"] >= next_h1]
        if len(h1_matches) == 0:
            return {"resolved": False, "reason": "no_h1"}
        h1_start = int(h1_matches[0])
        h1_window = h1.iloc[h1_start: h1_start + 12]
        if len(h1_window) == 0:
            return {"resolved": False, "reason": "empty_window"}
        r_unit = abs(entry - sl)
        if r_unit == 0:
            return {"resolved": False, "reason": "zero_r_unit"}
        # Step 1: find first H1 where entry is touched intra-bar (LIMIT fill)
        # For LONG: low <= entry (price retraced down to limit); for SHORT: high >= entry
        fill_idx = None
        for i, c in h1_window.iterrows():
            chigh = c["high"]; clow = c["low"]
            # Limit fill: price comes back to entry
            if direction == "LONG":
                # Limit-buy at entry (entry below current price); fills when low <= entry
                if clow <= entry <= chigh:
                    fill_idx = i; break
                # Or if H1 opens below entry already
                if clow <= entry:
                    fill_idx = i; break
            else:
                if clow <= entry <= chigh:
                    fill_idx = i; break
                if chigh >= entry:
                    fill_idx = i; break

        if fill_idx is None:
            return {"resolved": True, "filled": False, "outcome": "NOT_FILLED", "r": 0.0}

        # Step 2: from fill_idx onwards, check SL/TP
        post_fill = h1_window.loc[fill_idx:]
        first_filled = True
        for i, c in post_fill.iterrows():
            chigh = c["high"]; clow = c["low"]
            if first_filled:
                first_filled = False
                # On the fill candle, can also resolve if TP/SL hit on same bar.
                # Conservative: assume entry filled mid-bar; rest of candle could still hit either side.
                # Simplification: still check SL/TP this bar.
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
        # Mark-to-market
        last_close = float(post_fill.iloc[-1]["close"])
        if direction == "LONG":
            r = (last_close - entry) / r_unit
        else:
            r = (entry - last_close) / r_unit
        return {"resolved": True, "filled": True, "outcome": "EXPIRY", "r": r}

    # Resolve all
    by_check = defaultdict(list)
    for t in l2_rejected:
        fc = get_l2_failed_check(t)
        res = resolve_with_limit_fill(t)
        by_check[str(fc)].append((t, res))

    # Summary table
    print()
    print("=== Per-failed-check live L2 resolution (with LIMIT fill) ===")
    summary = {}
    for check, pairs in sorted(by_check.items()):
        n_total = len(pairs)
        not_filled = sum(1 for _, res in pairs if res.get("outcome") == "NOT_FILLED")
        filled = [(t, res) for t, res in pairs if res.get("filled")]
        if filled:
            rs = [res["r"] for _, res in filled]
            wins_in_filled = sum(1 for r in rs if r >= 1.4 - 1e-9)
            wr_filled = wins_in_filled / len(filled)
            exp_r_filled = sum(rs) / len(filled)
            # Counting NOT_FILLED as 0 R
            all_rs = rs + [0.0] * not_filled
            exp_r_overall = sum(all_rs) / n_total
            total_r = sum(all_rs)
            wins_overall = wins_in_filled  # not_filled never wins
            lo, hi = wilson_ci(wins_overall, n_total)
            print(f"  {check:18s}  n_total={n_total}  not_filled={not_filled}  filled={len(filled)}  "
                  f"WR(of all)={wins_overall/n_total:.3f} CI[{lo:.3f},{hi:.3f}]  "
                  f"ExpR(all)={exp_r_overall:+.3f}  TotalR={total_r:+.1f}")
            summary[check] = {
                "n_total": n_total, "not_filled": not_filled, "filled": len(filled),
                "wr": wins_overall / n_total, "exp_r": exp_r_overall, "total_r": total_r,
            }
        else:
            print(f"  {check:18s}  n_total={n_total}  not_filled={not_filled}  filled=0")

    # Save detail
    rows = []
    for check, pairs in by_check.items():
        for t, res in pairs:
            rows.append({
                "trade_id": t.get("metadata", {}).get("trade_id"),
                "_instrument": t["_instrument"],
                "candle_time": t.get("metadata", {}).get("candle_time"),
                "kill_zone": t.get("metadata", {}).get("kill_zone"),
                "direction": t.get("trade_parameters", {}).get("direction"),
                "entry": t.get("trade_parameters", {}).get("entry_price"),
                "sl": t.get("trade_parameters", {}).get("stop_loss"),
                "tp1": t.get("trade_parameters", {}).get("take_profit_1"),
                "l2_failed_check": check,
                "filled": res.get("filled"),
                "outcome": res.get("outcome"),
                "fwd_r": res.get("r"),
            })
    with open(OUT_DIR / "live_l2_corrected.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")

    # Direction breakdown
    print()
    print("=== Live L2 by direction (corrected) ===")
    by_dir = defaultdict(list)
    for t in l2_rejected:
        d = t.get("trade_parameters", {}).get("direction", "UNK")
        by_dir[d].append(t)
    for d, ts in sorted(by_dir.items()):
        results = [resolve_with_limit_fill(t) for t in ts]
        rs = [r["r"] for r in results if r.get("filled")]
        not_filled = sum(1 for r in results if r.get("outcome") == "NOT_FILLED")
        n_total = len(results)
        wins = sum(1 for r in rs if r >= 1.4)
        all_rs = rs + [0.0] * not_filled
        if n_total == 0:
            continue
        lo, hi = wilson_ci(wins, n_total)
        print(f"  {d:6s}  n={n_total}, not_filled={not_filled}, filled={len(rs)}, "
              f"WR={wins/n_total:.3f} CI[{lo:.3f},{hi:.3f}], ExpR={sum(all_rs)/n_total:+.3f}, TotalR={sum(all_rs):+.1f}")

    # Per instrument
    print()
    print("=== Live L2 by instrument (corrected) ===")
    by_inst = defaultdict(list)
    for t in l2_rejected:
        by_inst[t["_instrument"]].append(t)
    for inst, ts in sorted(by_inst.items()):
        results = [resolve_with_limit_fill(t) for t in ts]
        rs = [r["r"] for r in results if r.get("filled")]
        not_filled = sum(1 for r in results if r.get("outcome") == "NOT_FILLED")
        n_total = len(results)
        wins = sum(1 for r in rs if r >= 1.4)
        all_rs = rs + [0.0] * not_filled
        if n_total == 0:
            continue
        lo, hi = wilson_ci(wins, n_total)
        print(f"  {inst:14s}  n={n_total}, not_filled={not_filled}, "
              f"WR={wins/n_total:.3f} CI[{lo:.3f},{hi:.3f}], ExpR={sum(all_rs)/n_total:+.3f}")

    # Save summary csv
    import csv
    with open(OUT_DIR / "live_l2_corrected_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["check", "n_total", "not_filled", "filled", "wr", "exp_r", "total_r"])
        for k, v in summary.items():
            w.writerow([k, v["n_total"], v["not_filled"], v["filled"],
                        f"{v['wr']:.3f}", f"{v['exp_r']:+.3f}", f"{v['total_r']:+.1f}"])


if __name__ == "__main__":
    main()
