"""
Section 4 (live): Extract live L2 rejects + live NO_TRADEs and forward-resolve.

Live data sources:
  - knowledge_base/trade_records/*/*.json  (148 records, 92 L2-rejected)
  - knowledge_base/live_evaluations/*/*.jsonl  (1240 rows)
  - shadow_logs/candidate_features_log.jsonl  (126 rows)

For trade_records (highest fidelity, has trade_parameters):
  - Use trade_parameters.entry_price / stop_loss / take_profit_1 directly
  - Forward-resolve via H1 csv from candle_time
"""
import json
import os
from pathlib import Path
from datetime import timedelta
from collections import Counter, defaultdict
import pandas as pd

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

    # Filter L2 rejected
    l2_rejected = [t for t in trades if t.get("decision_pipeline", {}).get("final_outcome") == "REJECTED_L2"]
    gate1_rejected = [t for t in trades if t.get("decision_pipeline", {}).get("final_outcome") == "REJECTED_GATE1_SAFETY"]
    print(f"L2 rejected (live): {len(l2_rejected)}")
    print(f"Gate1 rejected (live): {len(gate1_rejected)}")

    def resolve(trade):
        inst = trade["_instrument"]
        if inst not in h1_dfs or h1_dfs[inst] is None:
            return None
        h1 = h1_dfs[inst]
        ts_str = trade.get("metadata", {}).get("candle_time")
        if not ts_str:
            return None
        ts = pd.to_datetime(ts_str, utc=True)
        tp = trade.get("trade_parameters", {})
        direction = tp.get("direction")
        entry = tp.get("entry_price")
        sl = tp.get("stop_loss")
        tp1 = tp.get("take_profit_1")
        if direction is None or entry is None or sl is None or tp1 is None:
            return None
        entry = float(entry); sl = float(sl); tp1 = float(tp1)
        # 1.5R logic on TP1 already; we just check forward resolution
        next_h1 = (ts + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        h1_matches = h1.index[h1["time"] >= next_h1]
        if len(h1_matches) == 0:
            return None
        h1_start = int(h1_matches[0])
        h1_window = h1.iloc[h1_start: h1_start + 12]
        if len(h1_window) == 0:
            return None
        # 1R = |entry - sl|
        r_unit = abs(entry - sl)
        for _, c in h1_window.iterrows():
            if direction == "LONG":
                sl_hit = c["low"] <= sl
                tp_hit = c["high"] >= tp1
            else:
                sl_hit = c["high"] >= sl
                tp_hit = c["low"] <= tp1
            if sl_hit and tp_hit:
                return -1.0
            elif sl_hit:
                return -1.0
            elif tp_hit:
                # Compute actual R based on TP1 / entry / SL
                if direction == "LONG":
                    r = (tp1 - entry) / r_unit
                else:
                    r = (entry - tp1) / r_unit
                return r
        # Expiry — partial R
        last_close = float(h1_window.iloc[-1]["close"])
        if direction == "LONG":
            r = (last_close - entry) / r_unit
        else:
            r = (entry - last_close) / r_unit
        return r

    def summarize(label, group):
        rs = [resolve(t) for t in group]
        rs = [r for r in rs if r is not None]
        if not rs:
            print(f"{label}: 0 resolved")
            return
        n = len(rs)
        wins = sum(1 for x in rs if x >= 1.4 - 1e-9)
        losses = sum(1 for x in rs if x <= -0.9 + 1e-9)
        print(f"{label}: n={n}, WR={wins/n:.3f}, ExpR={sum(rs)/n:+.3f}, TotalR={sum(rs):+.1f}, losses={losses}")

    summarize("Live L2 rejected (forward-resolved)", l2_rejected)
    summarize("Live Gate1 rejected (forward-resolved)", gate1_rejected)

    # Get L2 reason patterns from live
    l2_reasons = Counter()
    for t in l2_rejected:
        l2 = t.get("decision_pipeline", {}).get("level2_verification", {})
        if isinstance(l2, dict):
            reason = (l2.get("reason") or "").split(":")[0]
            l2_reasons[reason] += 1
    print("\nLive L2 reason buckets:")
    for k, v in l2_reasons.most_common():
        print(f"  {v}: {k}")

    # Per-bucket resolution for live L2
    print("\nLive L2 forward-resolution by reason bucket:")
    by_reason = defaultdict(list)
    for t in l2_rejected:
        l2 = t.get("decision_pipeline", {}).get("level2_verification", {})
        reason = (l2.get("reason") or "").split(":")[0] if isinstance(l2, dict) else "unknown"
        by_reason[reason].append(t)
    for reason, ts in sorted(by_reason.items()):
        rs = [resolve(t) for t in ts]
        rs = [r for r in rs if r is not None]
        if not rs:
            continue
        n = len(rs)
        wins = sum(1 for x in rs if x >= 1.4)
        print(f"  {reason:25s}: n={n}, WR={wins/n:.3f}, ExpR={sum(rs)/n:+.3f}")

    # Save
    live_l2_data = []
    for t in l2_rejected:
        r = resolve(t)
        l2 = t.get("decision_pipeline", {}).get("level2_verification", {})
        live_l2_data.append({
            "trade_id": t.get("metadata", {}).get("trade_id"),
            "_instrument": t["_instrument"],
            "candle_time": t.get("metadata", {}).get("candle_time"),
            "kill_zone": t.get("metadata", {}).get("kill_zone"),
            "direction": t.get("trade_parameters", {}).get("direction"),
            "entry": t.get("trade_parameters", {}).get("entry_price"),
            "sl": t.get("trade_parameters", {}).get("stop_loss"),
            "tp1": t.get("trade_parameters", {}).get("take_profit_1"),
            "l2_reason": (l2.get("reason") or "") if isinstance(l2, dict) else "",
            "fwd_r": r,
        })
    with open(OUT_DIR / "live_l2_resolved.jsonl", "w") as f:
        for r in live_l2_data:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"\nWrote live_l2_resolved.jsonl ({len(live_l2_data)} rows)")


if __name__ == "__main__":
    main()
