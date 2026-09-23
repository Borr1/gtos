"""
Section 5: Per-framework rejection split.

For tier2 + a2_v2 backtest where raw_response is captured, parse:
  - which framework qualified
  - rejection pattern (L2, NO_TRADE, BLOCKED_LIMIT) per framework
  - forward-resolved R per (framework, decision)

Also includes live data live_evaluations decision per framework.
"""
import json
import os
import re
from pathlib import Path
from collections import Counter, defaultdict
from datetime import timedelta
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


def extract_framework(raw_response):
    if not raw_response:
        return None
    m = re.search(r'"framework"\s*:\s*"(\w+)"', raw_response)
    return m.group(1) if m else None


def main():
    h1_dfs = {inst: load_csv(inst, "H1") for inst in INSTRUMENTS}

    # Tier2 source
    src = ROOT / "research/instrument_expansion_2026-04-25"
    tier2_rows = []
    for inst_dir in os.listdir(src):
        if not inst_dir.startswith("tier2_"):
            continue
        full = src / inst_dir
        if not full.is_dir():
            continue
        for slice_dir in sorted(os.listdir(full)):
            sp = full / slice_dir
            if not sp.is_dir():
                continue
            rfile = sp / "all_results.json"
            if not rfile.exists():
                continue
            with open(rfile, "r") as f:
                data = json.load(f)
            inst_name = inst_dir.replace("tier2_", "").upper()
            for r in data["results"]:
                r["_instrument"] = inst_name
                r["_slice"] = f"{inst_name.lower()}_{slice_dir}"
                tier2_rows.append(r)

    # Tag with framework
    by_fw_decision = defaultdict(list)
    for r in tier2_rows:
        fw = extract_framework(r.get("raw_response", ""))
        decision = r.get("decision")
        by_fw_decision[(fw or "none", decision)].append(r)

    print("=== Per (framework, decision) counts ===")
    for k, v in sorted(by_fw_decision.items()):
        print(f"  {k}: {len(v)}")

    # Forward-resolve filled rows per framework × decision (LIMIT-fill semantics)
    print()
    print("=== Per-framework forward-resolved rejected/blocked rows ===")

    def resolve(row):
        inst = normalize_inst(row.get("_instrument"))
        h1 = h1_dfs.get(inst)
        if h1 is None:
            return None
        ts = pd.to_datetime(row.get("candle_time"), utc=True)
        next_h1 = (ts + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        h1_idx = h1.index[h1["time"] >= next_h1]
        if len(h1_idx) == 0:
            return None
        h1_start = int(h1_idx[0])
        h1_window = h1.iloc[h1_start: h1_start + 12]
        if len(h1_window) == 0:
            return None
        entry = row.get("entry_price"); sl = row.get("stop_loss"); tp1 = row.get("take_profit_1")
        direction = (row.get("direction") or "").upper()
        if not entry or not sl or not tp1 or direction not in ("LONG", "SHORT"):
            return None
        entry = float(entry); sl = float(sl); tp1 = float(tp1)
        r_unit = abs(entry - sl)
        if r_unit == 0:
            return None
        fill_idx = None
        for i, c in h1_window.iterrows():
            if c["low"] <= entry <= c["high"]:
                fill_idx = i; break
        if fill_idx is None:
            return {"filled": False, "r": 0.0, "outcome": "NOT_FILLED"}
        post = h1_window.loc[fill_idx:]
        for i, c in post.iterrows():
            if direction == "LONG":
                sl_hit = c["low"] <= sl; tp_hit = c["high"] >= tp1
            else:
                sl_hit = c["high"] >= sl; tp_hit = c["low"] <= tp1
            if sl_hit and tp_hit:
                return {"filled": True, "r": -1.0, "outcome": "SL"}
            elif sl_hit:
                return {"filled": True, "r": -1.0, "outcome": "SL"}
            elif tp_hit:
                if direction == "LONG":
                    r = (tp1 - entry) / r_unit
                else:
                    r = (entry - tp1) / r_unit
                return {"filled": True, "r": r, "outcome": "TP"}
        last_close = float(post.iloc[-1]["close"])
        if direction == "LONG":
            r = (last_close - entry) / r_unit
        else:
            r = (entry - last_close) / r_unit
        return {"filled": True, "r": r, "outcome": "EXPIRY"}

    target_keys = [
        ("ob_retest", "BLOCKED_LIMIT"),
        ("ob_retest", "REJECTED_L2"),
        ("ob_retest", "CANDIDATE"),
        ("breaker_re_entry", "REJECTED_L2"),
        ("breaker_re_entry", "BLOCKED_LIMIT"),
        ("breaker_re_entry", "CANDIDATE"),
    ]
    print(f"{'framework':22s}{'decision':14s}{'n':>5s}{'filled':>8s}{'WR':>8s}{'ExpR':>8s}{'TotR':>8s}")
    for fw, dec in target_keys:
        rows = by_fw_decision.get((fw, dec), [])
        if not rows:
            continue
        results = [resolve(r) for r in rows]
        results = [r for r in results if r is not None]
        if not results:
            continue
        n_total = len(results)
        not_filled = sum(1 for r in results if not r.get("filled"))
        filled = [r for r in results if r.get("filled")]
        rs = [r["r"] for r in filled]
        wins = sum(1 for x in rs if x >= 1.4 - 1e-9)
        all_rs = rs + [0.0] * not_filled
        wr = wins / n_total
        exp_r = sum(all_rs) / n_total
        total_r = sum(all_rs)
        print(f"{fw:22s}{dec:14s}{n_total:>5d}{len(filled):>8d}{wr:>8.3f}{exp_r:>+8.3f}{total_r:>+8.1f}")


if __name__ == "__main__":
    main()
