"""Identify the most robust hour-specific directional edges.

Approach:
  For each (instrument, hour, direction) tuple, compute:
    - n, w, wr
    - binomial test against the instrument-specific directional null (~0.38-0.41)
    - Bonferroni correction for 7 instruments × 24 hours × 2 directions = 336 tests
    - Filter: n >= 100 AND wr >= 0.48 AND p_bonf < 0.05 → STRONG EDGE
              n >= 50  AND wr >= 0.48 AND p_bonf < 0.10 → SUGGESTIVE

This is the opposite-side check: what if we *shorted* a direction blindly at an hour
(no setup filter), does the base rate beat the directional null?
"""
import json
import math
from collections import defaultdict
from pathlib import Path

OUT_DIR = Path(r"C:\Users\MSI\Documents\ai-trading-agent\research\b_deep_audit_2026-04-19\phase1\_eta_scratch")


def _binomial_p(wins, n, p0=0.5):
    if n == 0:
        return 1.0
    if n < 30:
        from math import comb
        p_at_least = sum(comb(n, i) * (p0 ** i) * ((1 - p0) ** (n - i)) for i in range(wins, n + 1))
        p_at_most = sum(comb(n, i) * (p0 ** i) * ((1 - p0) ** (n - i)) for i in range(0, wins + 1))
        return min(1.0, 2 * min(p_at_least, p_at_most))
    p_hat = wins / n
    se = math.sqrt(p0 * (1 - p0) / n)
    z = (p_hat - p0) / se
    from math import erfc
    return erfc(abs(z) / math.sqrt(2))


def main():
    with open(OUT_DIR / "full_scan_output.json", "r", encoding="utf-8") as f:
        d = json.load(f)

    # Build matrix
    baselines = d["baselines"]
    rows = []
    for inst, hours in d["hour_of_day"].items():
        b = baselines.get(inst, {})
        p0_long = b.get("wr_long") or 0.5
        p0_short = b.get("wr_short") or 0.5
        for h_str, v in hours.items():
            h = int(h_str)
            lr, wl = v["long_resolved"], v["long_wins"]
            sr, ws = v["short_resolved"], v["short_wins"]
            if lr >= 20:
                wr_l = wl / lr
                p_l = _binomial_p(wl, lr, p0_long)
                rows.append({
                    "instrument": inst,
                    "hour_utc": h,
                    "direction": "LONG",
                    "n": lr,
                    "wins": wl,
                    "wr": wr_l,
                    "null_p": p0_long,
                    "p_raw": p_l,
                    "exp_r": (wl * 1.5 - (lr - wl) * 1.0) / lr,
                })
            if sr >= 20:
                wr_s = ws / sr
                p_s = _binomial_p(ws, sr, p0_short)
                rows.append({
                    "instrument": inst,
                    "hour_utc": h,
                    "direction": "SHORT",
                    "n": sr,
                    "wins": ws,
                    "wr": wr_s,
                    "null_p": p0_short,
                    "p_raw": p_s,
                    "exp_r": (ws * 1.5 - (sr - ws) * 1.0) / sr,
                })

    # Bonferroni across all tests
    k = len(rows)
    for r in rows:
        r["p_bonf"] = min(1.0, r["p_raw"] * k)

    # Sort by highest WR × n combined
    rows.sort(key=lambda r: -r["wr"])

    # Filter to strong edges
    strong = [r for r in rows if r["n"] >= 100 and r["wr"] >= 0.48 and r["p_bonf"] < 0.05]
    suggestive = [r for r in rows if r["n"] >= 100 and r["wr"] >= 0.46 and r["p_bonf"] < 0.20 and r not in strong]
    weak = [r for r in rows if r["n"] >= 50 and r["wr"] >= 0.48 and r["p_raw"] < 0.05 and r not in strong and r not in suggestive]

    with open(OUT_DIR / "hour_edges.json", "w", encoding="utf-8") as f:
        json.dump({
            "n_tests": k,
            "strong": strong,
            "suggestive": suggestive,
            "weak_raw_only": weak,
            "all_rows": rows,
        }, f, indent=2)

    print("=== STRONG HOUR-SPECIFIC DIRECTIONAL EDGES (n&gt;=100, WR&gt;=0.48, Bonf<0.05) ===")
    print(f"Family size (n_tests): {k}")
    print(f"{'Inst':8s} {'Hr':2s} {'Dir':5s} {'n':5s} {'W':5s} {'WR':6s} {'nullWR':7s} {'ExpR':7s} {'p_raw':10s} {'p_bonf':10s}")
    for r in strong:
        print(f"{r['instrument']:8s} {r['hour_utc']:2d} {r['direction']:5s} {r['n']:5d} {r['wins']:5d} {r['wr']:.3f}  {r['null_p']:.3f}  {r['exp_r']:+.3f}  {r['p_raw']:.2e}  {r['p_bonf']:.2e}")

    print(f"\n=== SUGGESTIVE (n&gt;=100, WR&gt;=0.46, Bonf<0.20) ===")
    for r in suggestive:
        print(f"{r['instrument']:8s} {r['hour_utc']:2d} {r['direction']:5s} {r['n']:5d} {r['wins']:5d} {r['wr']:.3f}  {r['null_p']:.3f}  {r['exp_r']:+.3f}  {r['p_raw']:.2e}  {r['p_bonf']:.2e}")


if __name__ == "__main__":
    main()
