"""
Extend 01 to XAUUSD and EURUSD. Use same ATR-based assumption.

Also compare to the CAND baseline and bias-directional replay (using each
record's 'bias' if present; else fallback to both-direction bounds).
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")


def load_m15(symbol: str) -> list[dict]:
    path = ROOT / "data" / "historical_2026" / f"{symbol}_M15.csv"
    rows = []
    with open(path, "r", encoding="utf-8") as f:
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


def load_sim(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    if "results" in d:
        return d["results"]
    return d


def load_nas100() -> list[dict]:
    results = []
    for i in range(1, 6):
        p = ROOT / "research" / "t3_1_eurusd_nas100_validation_2026-04-19" / f"nas100_slice_{i}" / "NAS100_t7_simulation.json"
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        results += d["results"]
    return results


def normalize_ts(ts: str) -> str:
    t = ts.strip()
    if t.endswith("Z"):
        t = t[:-1]
    t = t.replace("T", " ")
    # ensure seconds
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


def replay_one(m15: list[dict], idx: int, direction: str, entry: float, sl: float, tp: float, horizon_candles: int) -> str:
    end_idx = min(len(m15), idx + horizon_candles + 1)
    for j in range(idx + 1, end_idx):
        c = m15[j]
        if direction == "LONG":
            sl_hit = c["low"] <= sl
            tp_hit = c["high"] >= tp
            if sl_hit and tp_hit:
                return "L"  # conservative
            if sl_hit:
                return "L"
            if tp_hit:
                return "W"
        else:
            sl_hit = c["high"] >= sl
            tp_hit = c["low"] <= tp
            if sl_hit and tp_hit:
                return "L"
            if sl_hit:
                return "L"
            if tp_hit:
                return "W"
    return "U"


def counterfactual(symbol: str, rejects: list[dict], m15: list[dict], horizon_hours: list[int] = (4, 12)) -> dict:
    """
    Replay each reject assuming bias direction when available.
    Also report both-direction upper bound.
    """
    m15_idx = {c["time"]: i for i, c in enumerate(m15)}

    bias_directional = {"LONG": Counter(), "SHORT": Counter()}
    both_longs = {"LONG": Counter(), "SHORT": Counter()}
    n_valid = 0
    n_skipped = 0
    n_no_bias = 0
    bias_dir_r = {"LONG": 0.0, "SHORT": 0.0}
    bias_results = []

    for r in rejects:
        ts = normalize_ts(r.get("candle_time", ""))
        idx = m15_idx.get(ts)
        if idx is None:
            n_skipped += 1
            continue
        atr = atr14(m15, idx)
        if atr <= 0:
            n_skipped += 1
            continue
        n_valid += 1
        signal_close = m15[idx]["close"]

        # Bias-directional replay (best proxy for "what AI might have done")
        bias = r.get("bias") or None
        if bias in ("bullish", "bearish"):
            direction = "LONG" if bias == "bullish" else "SHORT"
            for horizon in horizon_hours:
                horizon_candles = horizon * 4
                if direction == "LONG":
                    entry = signal_close
                    sl = signal_close - atr
                    tp = signal_close + 1.5 * atr
                else:
                    entry = signal_close
                    sl = signal_close + atr
                    tp = signal_close - 1.5 * atr
                out = replay_one(m15, idx, direction, entry, sl, tp, horizon_candles)
                bias_directional[direction][(horizon, out)] += 1
                if horizon == 12:  # main result
                    if out == "W":
                        bias_dir_r[direction] += 1.5
                    elif out == "L":
                        bias_dir_r[direction] -= 1.0
                    bias_results.append({"ts": ts, "bias": bias, "direction": direction, "out": out})
        else:
            n_no_bias += 1

        # Both-direction upper bound
        for direction in ("LONG", "SHORT"):
            for horizon in horizon_hours:
                horizon_candles = horizon * 4
                if direction == "LONG":
                    entry = signal_close
                    sl = signal_close - atr
                    tp = signal_close + 1.5 * atr
                else:
                    entry = signal_close
                    sl = signal_close + atr
                    tp = signal_close - 1.5 * atr
                out = replay_one(m15, idx, direction, entry, sl, tp, horizon_candles)
                both_longs[direction][(horizon, out)] += 1

    return {
        "n_rejects": len(rejects),
        "n_valid": n_valid,
        "n_skipped": n_skipped,
        "n_no_bias": n_no_bias,
        "bias_directional_outcomes": {
            k: {f"{h}h_{o}": v for (h, o), v in d.items()} for k, d in bias_directional.items()
        },
        "bias_directional_R_12h": bias_dir_r,
        "both_direction_upper_bound": {
            k: {f"{h}h_{o}": v for (h, o), v in d.items()} for k, d in both_longs.items()
        },
    }


def main():
    datasets = {}

    # NAS100
    nas_results = load_nas100()
    nas_m15 = load_m15("NAS100")
    nas_ob = [r for r in nas_results if r.get("decision") == "NO_TRADE" and (r.get("no_trade_reason") or "").startswith("ob_proximity:")]
    nas_ps = [r for r in nas_results if r.get("decision") == "NO_TRADE" and (r.get("no_trade_reason") or "").startswith("prescreen:")]
    datasets["NAS100_ob_proximity"] = counterfactual("NAS100", nas_ob, nas_m15)
    datasets["NAS100_prescreen"] = counterfactual("NAS100", nas_ps, nas_m15)

    # XAUUSD
    xau_results = load_sim(ROOT / "research" / "t7_live_simulation" / "all_results_jan_apr10.json")
    xau_m15 = load_m15("XAUUSD")
    xau_ob = [r for r in xau_results if r.get("decision") == "NO_TRADE" and (r.get("no_trade_reason") or "").startswith("ob_proximity:")]
    xau_ps = [r for r in xau_results if r.get("decision") == "NO_TRADE" and (r.get("no_trade_reason") or "").startswith("prescreen:")]
    datasets["XAUUSD_ob_proximity"] = counterfactual("XAUUSD", xau_ob, xau_m15)
    datasets["XAUUSD_prescreen"] = counterfactual("XAUUSD", xau_ps, xau_m15)

    # EURUSD
    eur_results = load_sim(ROOT / "research" / "t7_live_simulation" / "EURUSD_t7_simulation.json")
    eur_m15 = load_m15("EURUSD")
    eur_ob = [r for r in eur_results if r.get("decision") == "NO_TRADE" and (r.get("no_trade_reason") or "").startswith("ob_proximity:")]
    eur_ps = [r for r in eur_results if r.get("decision") == "NO_TRADE" and (r.get("no_trade_reason") or "").startswith("prescreen:")]
    datasets["EURUSD_ob_proximity"] = counterfactual("EURUSD", eur_ob, eur_m15)
    datasets["EURUSD_prescreen"] = counterfactual("EURUSD", eur_ps, eur_m15)

    out_path = ROOT / "research" / "b_deep_audit_2026-04-19" / "phase1" / "_zeta_scratch" / "02_ob_proximity_counterfactual_all.json"
    out_path.write_text(json.dumps(datasets, indent=2, default=str))

    # Print summary
    for name, d in datasets.items():
        print(f"\n=== {name} ===")
        print(f"  n_rejects={d['n_rejects']} n_valid={d['n_valid']} n_skipped={d['n_skipped']} n_no_bias={d['n_no_bias']}")
        print(f"  bias_directional_R (12h, sum):")
        for direction in ("LONG", "SHORT"):
            r = d["bias_directional_R_12h"][direction]
            outcomes = d["bias_directional_outcomes"][direction]
            w = outcomes.get("12h_W", 0)
            l = outcomes.get("12h_L", 0)
            u = outcomes.get("12h_U", 0)
            total = w + l + u
            wr = w / (w + l) if (w + l) > 0 else 0.0
            exp = (1.5 * w - 1.0 * l) / total if total > 0 else 0.0
            print(f"    {direction}: W={w} L={l} U={u} WR={wr:.3f} R_sum={r:+.2f} ExpR/trade={exp:+.3f}")
        print(f"  BOTH-direction UPPER BOUND (12h):")
        for direction in ("LONG", "SHORT"):
            outcomes = d["both_direction_upper_bound"][direction]
            w = outcomes.get("12h_W", 0)
            l = outcomes.get("12h_L", 0)
            u = outcomes.get("12h_U", 0)
            wr = w / (w + l) if (w + l) > 0 else 0.0
            total = w + l + u
            exp = (1.5 * w - 1.0 * l) / total if total > 0 else 0.0
            print(f"    {direction}: W={w} L={l} U={u} WR={wr:.3f} ExpR/trade={exp:+.3f}")

    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
