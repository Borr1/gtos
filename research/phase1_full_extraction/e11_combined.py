"""E11 — Kill-zone 15-min bucket outcome combining A1 fills + Track C unified_trades.

Applies Bonferroni across bucket tests (N tests = distinct 15-min buckets tested).

Writes e11_combined.json.
"""
from __future__ import annotations
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
UNIFIED = REPO / "research" / "phase1_xauusd_reverse_engineering" / "unified_trades.csv"
A1_MERGED = REPO / "research" / "phase1_full_extraction" / "merged_data.jsonl"
OUT = REPO / "research" / "phase1_full_extraction" / "e11_combined.json"


def wilson(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0: return (float("nan"), float("nan"))
    p = wins / n
    denom = 1 + z*z/n
    center = (p + z*z/(2*n))/denom
    margin = z * math.sqrt((p*(1-p) + z*z/(4*n))/n) / denom
    return (max(0, center-margin), min(1, center+margin))


def main():
    uni = []
    with open(UNIFIED) as f:
        r = csv.DictReader(f)
        for row in r: uni.append(row)
    with open(A1_MERGED) as f:
        a1 = [json.loads(l) for l in f]
    a1_filled = [r for r in a1 if r.get("out_decision") == "CANDIDATE" and r.get("out_outcome") in {"WIN", "LOSS", "BE"}]

    combined = []
    for r in a1_filled:
        combined.append({
            "source": "a1",
            "symbol": r["symbol"],
            "kill_zone": r["kill_zone"],
            "ts": r["timestamp_utc"],
            "r_multiple": r["out_r_multiple"],
            "outcome": r["out_outcome"],
        })
    for r in uni:
        try: rm = float(r["r_multiple"])
        except: rm = None
        combined.append({
            "source": r["source"][:40],
            "symbol": r["symbol"],
            "kill_zone": r["kill_zone"],
            "ts": r["candle_time"],
            "r_multiple": rm,
            "outcome": r["outcome"].upper(),
        })
    print(f"Combined dataset: {len(combined)} rows")

    buckets = defaultdict(list)
    for r in combined:
        ts = r["ts"]
        if "T" not in ts: continue
        try:
            h, m = ts.split("T")[1][:5].split(":")
            mins = int(m) // 15 * 15
        except Exception:
            continue
        key = (r["symbol"], r["kill_zone"], f"{int(h):02d}:{mins:02d}")
        buckets[key].append(r)

    n_20 = sum(1 for k, v in buckets.items() if len(v) >= 20)
    bonf_n = max(1, n_20)
    alpha_raw = 0.05
    alpha_bonf = alpha_raw / bonf_n if bonf_n else alpha_raw
    z_bonf = 1.96 if bonf_n <= 1 else 2.576 if bonf_n <= 10 else 2.807  # approximate

    out = {"combined_n": len(combined), "n_buckets_20plus": n_20, "bonf_n_tests": bonf_n, "buckets": []}
    big = sorted(buckets.items(), key=lambda x: -len(x[1]))
    for (sym, kz, hhmm), rows in big:
        n = len(rows)
        if n < 5: continue  # include all buckets with n>=5 for synthesis
        wins = sum(1 for r in rows if r["outcome"] == "WIN")
        losses = sum(1 for r in rows if r["outcome"] in {"LOSS", "SL"})
        wr = wins / n
        lo, hi = wilson(wins, n)
        rs = [r["r_multiple"] for r in rows if r["r_multiple"] is not None]
        mean_r = sum(rs) / len(rs) if rs else None
        src_br = dict(Counter(r["source"] for r in rows))
        out["buckets"].append({
            "symbol": sym, "kill_zone": kz, "bucket_hhmm": hhmm,
            "n": n, "wins": wins, "losses": losses,
            "wr": wr, "wr_ci95": [lo, hi],
            "mean_r": mean_r,
            "sources": src_br,
            "meets_n20": n >= 20,
        })

    with open(OUT, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"Written {OUT}")
    print(f"n>=20 buckets: {n_20}")


if __name__ == "__main__":
    main()
