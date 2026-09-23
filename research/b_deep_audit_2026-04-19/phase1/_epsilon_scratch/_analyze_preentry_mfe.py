"""Signature #1: Pre-entry MFE distribution.

Across all CANDIDATE records (T7 sims) and across all filled backtest trades (as
null baseline), compute pre-entry MFE (signal → fill, favorable direction) in R.

Liquidity-arbitrage hypothesis: if market is "serving us the fill" after a sweep,
pre-entry MFE should be LARGE (price moves favorably first, then reverses to fill).
If it's growing quarter-over-quarter, that's a stop-hunt signature.

Null: if an edge is pure mean-reversion to OB, pre-entry MFE should be near zero —
the limit fills on the first touch, no "serving" run.
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _loader import (extract_candidates, is_degenerate, load_all_t7,
                     load_m15, median, percentile, quarter_of, _parse_iso)
from _mfe_mae import simulate_fill


def analyze_preentry_mfe() -> dict:
    all_t7 = load_all_t7()
    out = {
        "by_symbol": {},
        "by_symbol_quarter": {},
        "all_pre_mfe": [],
        "detail": [],
    }
    for symbol, results in all_t7.items():
        cands = extract_candidates(results)
        pre_mfe_list = []
        pre_mae_list = []
        per_quarter = defaultdict(list)
        for c in cands:
            if is_degenerate(c):
                continue
            try:
                sig_t = _parse_iso(c["candle_time"])
            except Exception:
                continue
            sim = simulate_fill(
                symbol, sig_t, c["direction"],
                float(c["entry_price"]), float(c["stop_loss"]), float(c["take_profit_1"]),
            )
            if sim is None:
                continue
            q = quarter_of(c["date"])
            pre_mfe_list.append(sim["pre_entry_mfe_R"])
            pre_mae_list.append(sim["pre_entry_mae_R"])
            per_quarter[q].append(sim["pre_entry_mfe_R"])
            out["detail"].append({
                "symbol": symbol, "date": c["date"], "quarter": q,
                "candle_time": c["candle_time"],
                "direction": c["direction"],
                "pre_entry_mfe_R": sim["pre_entry_mfe_R"],
                "pre_entry_mae_R": sim["pre_entry_mae_R"],
                "exit_type": sim["exit_type"],
                "exit_r": sim["exit_r"],
                "outcome_actual": c.get("outcome"),
            })
        if not pre_mfe_list:
            continue
        out["by_symbol"][symbol] = {
            "n": len(pre_mfe_list),
            "mean": statistics.mean(pre_mfe_list),
            "median": median(pre_mfe_list),
            "p25": percentile(pre_mfe_list, 25),
            "p75": percentile(pre_mfe_list, 75),
            "p90": percentile(pre_mfe_list, 90),
            "max": max(pre_mfe_list),
            "pre_mae_median": median(pre_mae_list),
        }
        out["by_symbol_quarter"][symbol] = {
            q: {
                "n": len(vs),
                "median_pre_mfe_R": median(vs),
                "mean_pre_mfe_R": statistics.mean(vs) if vs else None,
            } for q, vs in sorted(per_quarter.items())
        }
        out["all_pre_mfe"].extend(pre_mfe_list)
    out["all_summary"] = {
        "n": len(out["all_pre_mfe"]),
        "median": median(out["all_pre_mfe"]) if out["all_pre_mfe"] else None,
        "p25": percentile(out["all_pre_mfe"], 25) if out["all_pre_mfe"] else None,
        "p75": percentile(out["all_pre_mfe"], 75) if out["all_pre_mfe"] else None,
    }
    return out


if __name__ == "__main__":
    out = analyze_preentry_mfe()
    with open(Path(__file__).parent / "preentry_mfe.json", "w") as f:
        json.dump(out, f, default=str, indent=2)
    # Print summary
    print("# Pre-entry MFE (R) — Signature #1")
    print()
    for sym, s in out["by_symbol"].items():
        print(f"{sym}: n={s['n']} median={s['median']:.3f}R p25={s['p25']:.3f} p75={s['p75']:.3f} mean={s['mean']:.3f} max={s['max']:.3f}")
    print()
    print("## By symbol × quarter")
    for sym, qs in out["by_symbol_quarter"].items():
        print(f"  {sym}:")
        for q, s in qs.items():
            print(f"    {q}: n={s['n']} median={s['median_pre_mfe_R']:.3f if s['median_pre_mfe_R'] else 0}R")
