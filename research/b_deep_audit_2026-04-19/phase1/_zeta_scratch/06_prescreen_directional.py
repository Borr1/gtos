"""
For `prescreen:L2_h4_conflict_{dir1}_vs_d1_{dir2}` rejects — we KNOW the D1 and H4
directions. Replay forward with each and compute R.

For `prescreen:L1_no_direction_*` rejects — both D1 and H4 lack direction; we
can't infer anything structural, so we skip (covered by the upper-bound analysis).
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")


def load_m15(symbol: str) -> list[dict]:
    p = ROOT / "data" / "historical_2026" / f"{symbol}_M15.csv"
    rows = []
    with open(p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "time": row["time"].strip(),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            })
    return rows


def load_nas100():
    results = []
    for i in range(1, 6):
        p = ROOT / "research" / "t3_1_eurusd_nas100_validation_2026-04-19" / f"nas100_slice_{i}" / "NAS100_t7_simulation.json"
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        results += d["results"]
    return results


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    if "results" in d:
        return d["results"]
    return d


def normalize_ts(ts: str) -> str:
    t = ts.strip()
    if t.endswith("Z"):
        t = t[:-1]
    t = t.replace("T", " ")
    if len(t) == 16:
        t = t + ":00"
    return t


def atr14(m15: list[dict], idx: int, period: int = 14) -> float:
    if idx < period:
        return 0.0
    tr = []
    for k in range(idx - period, idx):
        h, l = m15[k + 1]["high"], m15[k + 1]["low"]
        pc = m15[k]["close"]
        tr.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(tr) / len(tr) if tr else 0.0


def replay(m15: list[dict], idx: int, direction: str, entry: float, sl: float, tp: float, horizon_candles: int = 16) -> str:
    end = min(len(m15), idx + horizon_candles + 1)
    for j in range(idx + 1, end):
        c = m15[j]
        if direction == "LONG":
            if c["low"] <= sl and c["high"] >= tp:
                return "L"
            if c["low"] <= sl:
                return "L"
            if c["high"] >= tp:
                return "W"
        else:
            if c["high"] >= sl and c["low"] <= tp:
                return "L"
            if c["high"] >= sl:
                return "L"
            if c["low"] <= tp:
                return "W"
    return "U"


def parse_prescreen_reason(reason: str):
    # prescreen:L2_h4_conflict_bullish_vs_d1_bearish
    m = re.match(r"prescreen:L2_h4_conflict_(\w+)_vs_d1_(\w+)", reason)
    if m:
        return {"type": "h4_vs_d1_conflict", "h4": m.group(1), "d1": m.group(2)}
    m = re.match(r"prescreen:L1_no_direction_d1_(\S+?)_h4_(\S+)", reason)
    if m:
        return {"type": "L1_no_direction", "d1": m.group(1), "h4": m.group(2)}
    return {"type": "other", "raw": reason}


def analyze(symbol: str, results: list[dict], m15: list[dict]):
    m15_idx = {c["time"]: i for i, c in enumerate(m15)}

    out = {}
    conflict = {"d1_direction": Counter(), "h4_direction": Counter()}
    r_sums = {"d1_direction": 0.0, "h4_direction": 0.0}
    n_valid = 0
    n_total = 0

    for r in results:
        if r.get("decision") != "NO_TRADE":
            continue
        reason = r.get("no_trade_reason", "")
        if not reason.startswith("prescreen:L2_h4_conflict"):
            continue
        parsed = parse_prescreen_reason(reason)
        if parsed["type"] != "h4_vs_d1_conflict":
            continue
        n_total += 1
        ts = normalize_ts(r["candle_time"])
        idx = m15_idx.get(ts)
        if idx is None:
            continue
        atr = atr14(m15, idx)
        if atr <= 0:
            continue
        n_valid += 1
        signal_close = m15[idx]["close"]
        # D1 direction replay
        d1_dir = "LONG" if parsed["d1"] == "bullish" else "SHORT"
        if d1_dir == "LONG":
            entry, sl, tp = signal_close, signal_close - atr, signal_close + 1.5 * atr
        else:
            entry, sl, tp = signal_close, signal_close + atr, signal_close - 1.5 * atr
        d1_out = replay(m15, idx, d1_dir, entry, sl, tp)
        conflict["d1_direction"][d1_out] += 1
        if d1_out == "W":
            r_sums["d1_direction"] += 1.5
        elif d1_out == "L":
            r_sums["d1_direction"] -= 1.0

        # H4 direction replay
        h4_dir = "LONG" if parsed["h4"] == "bullish" else "SHORT"
        if h4_dir == "LONG":
            entry, sl, tp = signal_close, signal_close - atr, signal_close + 1.5 * atr
        else:
            entry, sl, tp = signal_close, signal_close + atr, signal_close - 1.5 * atr
        h4_out = replay(m15, idx, h4_dir, entry, sl, tp)
        conflict["h4_direction"][h4_out] += 1
        if h4_out == "W":
            r_sums["h4_direction"] += 1.5
        elif h4_out == "L":
            r_sums["h4_direction"] -= 1.0

    out["h4_vs_d1_conflict"] = {
        "n_total": n_total,
        "n_valid": n_valid,
        "d1_direction": dict(conflict["d1_direction"]),
        "h4_direction": dict(conflict["h4_direction"]),
        "r_sums": r_sums,
    }
    print(f"\n=== {symbol} — prescreen h4-vs-d1 conflict counterfactual ===")
    print(f"  n_total={n_total} n_valid={n_valid}")
    for dir_name in ("d1_direction", "h4_direction"):
        d = conflict[dir_name]
        w, l, u = d.get("W", 0), d.get("L", 0), d.get("U", 0)
        resolved = w + l
        wr = w / resolved if resolved else 0.0
        total = w + l + u
        exp = (1.5 * w - 1.0 * l) / total if total else 0.0
        r_sum = r_sums[dir_name]
        print(f"  {dir_name}: W={w} L={l} U={u} WR={wr:.3f} R_sum={r_sum:+.2f} ExpR/trade={exp:+.3f}")
    return out


def main():
    nas = load_nas100()
    nas_m15 = load_m15("NAS100")
    analyze("NAS100", nas, nas_m15)

    xau = load(ROOT / "research" / "t7_live_simulation" / "all_results_jan_apr10.json")
    xau_m15 = load_m15("XAUUSD")
    analyze("XAUUSD", xau, xau_m15)

    eur = load(ROOT / "research" / "t7_live_simulation" / "EURUSD_t7_simulation.json")
    eur_m15 = load_m15("EURUSD")
    analyze("EURUSD", eur, eur_m15)


if __name__ == "__main__":
    main()
