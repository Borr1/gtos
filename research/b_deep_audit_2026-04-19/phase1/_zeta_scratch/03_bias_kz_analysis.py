"""
Bias-source impact and KZ boundary analysis on CANDIDATE + REJECTED_L2 records
across NAS100, XAUUSD, EURUSD.

Uses r_multiple where present (outcome replay is authoritative).
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(r"C:\Users\MSI\Documents\ai-trading-agent")


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


def analyze_bias(name: str, results: list[dict]):
    # Only CANDIDATE + REJECTED_L2 have bias fields
    cands = [r for r in results if r.get("decision") == "CANDIDATE"]
    rejs = [r for r in results if r.get("decision") == "REJECTED_L2"]
    print(f"\n=== {name} — bias source analysis ===")
    print(f"  n CAND={len(cands)} n REJECTED_L2={len(rejs)}")
    # CAND bias_source distribution
    bs = Counter(r.get("bias_source") for r in cands)
    print(f"  CAND bias_source distribution: {dict(bs)}")

    # For each bias_source — WR / R_sum (only outcomes present)
    by_src = defaultdict(lambda: {"W": 0, "L": 0, "U": 0, "R": 0.0, "n": 0})
    for r in cands:
        src = r.get("bias_source") or "unknown"
        out = r.get("outcome")
        r_mul = r.get("r_multiple")
        by_src[src]["n"] += 1
        if out == "WIN":
            by_src[src]["W"] += 1
        elif out == "LOSS":
            by_src[src]["L"] += 1
        else:
            by_src[src]["U"] += 1
        if isinstance(r_mul, (int, float)):
            by_src[src]["R"] += r_mul
    for src, s in by_src.items():
        resolved = s["W"] + s["L"]
        wr = s["W"] / resolved if resolved else 0.0
        exp = s["R"] / s["n"] if s["n"] else 0.0
        print(f"    {src}: n={s['n']} W={s['W']} L={s['L']} U={s['U']} WR={wr:.3f} R_sum={s['R']:+.2f} ExpR/trade={exp:+.3f}")


def analyze_kz_timing(name: str, results: list[dict]):
    # For CANDIDATEs: extract minutes-from-KZ-start / minutes-to-KZ-end
    # KZ table (UTC) per CLAUDE.md
    KZ_RANGES = {
        "XAUUSD": {"london": (7, 0, 10, 30), "ny": (13, 0, 17, 0)},
        "US30": {"london": (8, 0, 10, 30), "ny": (13, 30, 16, 0)},
        "USDJPY": {"london": (7, 0, 9, 30), "ny": (13, 0, 15, 30), "tokyo": (0, 0, 3, 0)},
        "GBPJPY": {"london": (7, 0, 9, 30), "ny": (13, 0, 15, 30), "tokyo": (0, 0, 3, 0)},
        "GBPUSD": {"london": (7, 0, 12, 0), "ny": (13, 0, 15, 30)},
        "NAS100": {"london": (8, 0, 10, 30), "ny": (13, 30, 16, 0)},  # approximate (index KZ mirrors US30)
        "EURUSD": {"london": (7, 0, 12, 0), "ny": (13, 0, 15, 30)},
    }
    symbol = None
    for r in results:
        if r.get("symbol"):
            symbol = r["symbol"]
            break
    kzs = KZ_RANGES.get(symbol, {})
    print(f"\n=== {name} — KZ boundary analysis (symbol={symbol}) ===")
    cands = [r for r in results if r.get("decision") == "CANDIDATE"]

    def kz_window_minutes(kz_name, ts_str):
        rng = kzs.get(kz_name)
        if not rng:
            return None, None
        ts = ts_str.strip()
        if ts.endswith("Z"):
            ts = ts[:-1]
        ts = ts.replace("T", " ")
        try:
            dt = datetime.fromisoformat(ts)
        except Exception:
            return None, None
        start_h, start_m, end_h, end_m = rng
        start_mins = start_h * 60 + start_m
        end_mins = end_h * 60 + end_m
        cur_mins = dt.hour * 60 + dt.minute
        return cur_mins - start_mins, end_mins - cur_mins

    bins = {
        "first_15min": {"W": 0, "L": 0, "U": 0, "R": 0.0},
        "middle": {"W": 0, "L": 0, "U": 0, "R": 0.0},
        "last_15min": {"W": 0, "L": 0, "U": 0, "R": 0.0},
    }
    for r in cands:
        kz = r.get("kill_zone")
        ts = r.get("candle_time")
        from_start, to_end = kz_window_minutes(kz, ts)
        if from_start is None:
            continue
        out = r.get("outcome")
        r_mul = r.get("r_multiple")
        # Bin
        if from_start <= 15:
            bin_name = "first_15min"
        elif to_end <= 15:
            bin_name = "last_15min"
        else:
            bin_name = "middle"
        b = bins[bin_name]
        if out == "WIN":
            b["W"] += 1
        elif out == "LOSS":
            b["L"] += 1
        else:
            b["U"] += 1
        if isinstance(r_mul, (int, float)):
            b["R"] += r_mul
    for name2, s in bins.items():
        total = s["W"] + s["L"] + s["U"]
        resolved = s["W"] + s["L"]
        wr = s["W"] / resolved if resolved else 0.0
        print(f"  {name2}: n={total} W={s['W']} L={s['L']} U={s['U']} WR={wr:.3f} R={s['R']:+.2f}")


def main():
    # NAS100
    nas = load_nas100()
    analyze_bias("NAS100", nas)
    analyze_kz_timing("NAS100", nas)

    # XAUUSD
    xau = load(ROOT / "research" / "t7_live_simulation" / "all_results_jan_apr10.json")
    analyze_bias("XAUUSD", xau)
    analyze_kz_timing("XAUUSD", xau)

    # EURUSD
    eur = load(ROOT / "research" / "t7_live_simulation" / "EURUSD_t7_simulation.json")
    analyze_bias("EURUSD", eur)
    analyze_kz_timing("EURUSD", eur)


if __name__ == "__main__":
    main()
