#!/usr/bin/env python3
"""DP4 extension analyzer — aggregates results across the 3 slices.

Reads all `mini_backtest_*` directories in the dp4_lira/ tree, computes
per-(variant, slice) stats, then per-variant fleet (3-slice combined)
stats. Writes both a JSON summary (`dp4_extension_summary.json`) and
prints markdown tables suitable for `DP4_EXTENSION.md`.

Run:
    python research/v4_prompt_engineering/dp4_lira/analyze_extension.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent
SLICES = ["xauusd_s3", "xauusd_s7", "usdjpy_s3"]
VARIANTS = ["v3_control", "lira", "nocot"]


def _load(p: Path):
    if not p.exists():
        return None
    return json.loads(p.read_text())


def _per_variant_slice(v: str, slc: str) -> dict | None:
    d = _load(ROOT / f"mini_backtest_{v}_{slc}" / "all_results.json")
    if d is None:
        return None
    results = d["results"]
    cand = [r for r in results if r.get("decision") == "CANDIDATE"]
    fills = [r for r in results if r.get("outcome") in ("WIN", "LOSS")]
    wins = sum(1 for r in fills if r["outcome"] == "WIN")
    losses = sum(1 for r in fills if r["outcome"] == "LOSS")
    rs = [r["r_multiple"] for r in fills]
    nt = sum(1 for r in results if r.get("decision") == "NO_TRADE")
    blk = sum(1 for r in results if r.get("decision") == "BLOCKED_LIMIT")
    rejs = sum(1 for r in results if r.get("decision") == "REJECTED_L2")
    parse_err = sum(1 for r in results if r.get("decision") == "PARSE_ERROR")
    l2_breakdown = Counter()
    for r in results:
        if r.get("decision") == "REJECTED_L2":
            pref = str(r.get("l2_reason", "none")).split(":")[0]
            l2_breakdown[pref] += 1
    cand_dirs = Counter(r.get("direction", "?") for r in cand)
    cand_outcomes = []
    for r in cand:
        cand_outcomes.append({
            "candle_time": r.get("candle_time"),
            "direction": r.get("direction"),
            "outcome": r.get("outcome"),
            "r_multiple": r.get("r_multiple"),
        })
    return {
        "variant": v,
        "slice": slc,
        "total_results": len(results),
        "no_trade": nt,
        "candidates": len(cand),
        "candidates_filled": len(fills),
        "wins": wins,
        "losses": losses,
        "blocked_limit": blk,
        "rejected_l2": rejs,
        "parse_error": parse_err,
        "wr_pct": round(100 * wins / max(len(fills), 1), 1),
        "expectancy_r": round(mean(rs), 3) if rs else 0.0,
        "total_cost_usd": round(d["total_cost"], 4),
        "l2_rejection_breakdown": dict(l2_breakdown),
        "cand_directions": dict(cand_dirs),
        "cand_outcomes": cand_outcomes,
    }


def _fleet(v: str, per_slice: dict) -> dict:
    """Sum across all slices for a variant. Per-instrument expectancy is
    per-slice; this fleet aggregate is total fills / total wins / mean R
    across the union of fills, NOT a weighted average of per-slice
    expectancies."""
    rs_all = []
    fills_all = 0
    wins_all = 0
    losses_all = 0
    cand_all = 0
    parse_err_all = 0
    rejs_all = 0
    cost_all = 0.0
    sl_beyond_ob_all = 0
    for slc in SLICES:
        d = per_slice.get(f"{v}_{slc}")
        if d is None:
            continue
        cand_all += d["candidates"]
        fills_all += d["candidates_filled"]
        wins_all += d["wins"]
        losses_all += d["losses"]
        parse_err_all += d["parse_error"]
        rejs_all += d["rejected_l2"]
        cost_all += d["total_cost_usd"]
        sl_beyond_ob_all += d["l2_rejection_breakdown"].get("sl_beyond_ob", 0)
        # Reconstruct r_multiples for fleet expectancy
        for co in d["cand_outcomes"]:
            if co["outcome"] in ("WIN", "LOSS"):
                rs_all.append(co["r_multiple"])
    return {
        "variant": v,
        "n_slices_completed": sum(1 for slc in SLICES if f"{v}_{slc}" in per_slice),
        "total_candidates": cand_all,
        "total_fills": fills_all,
        "total_wins": wins_all,
        "total_losses": losses_all,
        "total_parse_err": parse_err_all,
        "total_rejected_l2": rejs_all,
        "total_sl_beyond_ob": sl_beyond_ob_all,
        "fleet_wr_pct": round(100 * wins_all / max(fills_all, 1), 1),
        "fleet_expectancy_r": round(mean(rs_all), 3) if rs_all else 0.0,
        "total_cost_usd": round(cost_all, 4),
        "degenerate_rate_pct": round(
            100 * (parse_err_all + sl_beyond_ob_all) / max(cand_all + sl_beyond_ob_all + parse_err_all, 1), 1
        ),
    }


def main() -> None:
    per_slice = {}
    for v in VARIANTS:
        for slc in SLICES:
            d = _per_variant_slice(v, slc)
            if d is not None:
                per_slice[f"{v}_{slc}"] = d

    fleet = {v: _fleet(v, per_slice) for v in VARIANTS}

    summary = {
        "per_variant_slice": per_slice,
        "fleet_3_slice": fleet,
    }
    out = ROOT / "dp4_extension_summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print(f"Wrote {out}")
    print()

    # Per-slice tables
    for slc in SLICES:
        print(f"## {slc}")
        print("| Variant | Total | NO_TRADE | CAND | BLK | L2_REJ | PARSE | $ |")
        print("|---|---|---|---|---|---|---|---|")
        for v in VARIANTS:
            d = per_slice.get(f"{v}_{slc}")
            if d is None:
                print(f"| {v} | (not yet) |  |  |  |  |  |  |")
                continue
            print(f"| {v} | {d['total_results']} | {d['no_trade']} | "
                  f"{d['candidates']} | {d['blocked_limit']} | "
                  f"{d['rejected_l2']} | {d['parse_error']} | "
                  f"${d['total_cost_usd']:.3f} |")
        print()
        print("| Variant | Filled | W | L | WR | Expectancy |")
        print("|---|---|---|---|---|---|")
        for v in VARIANTS:
            d = per_slice.get(f"{v}_{slc}")
            if d is None:
                print(f"| {v} | (not yet) |  |  |  |  |")
                continue
            print(f"| {v} | {d['candidates_filled']} | {d['wins']} | "
                  f"{d['losses']} | {d['wr_pct']:.1f}% | "
                  f"{d['expectancy_r']:+.3f}R |")
        print()
        print("CAND directions per variant:")
        for v in VARIANTS:
            d = per_slice.get(f"{v}_{slc}")
            if d is None:
                continue
            print(f"  {v}: {d['cand_directions']}")
        print()

    # Fleet table
    print("## Combined 3-slice fleet")
    print("| Variant | Slices | CAND | Fills | W | L | WR | Expectancy | "
          "PARSE | sl_beyond_ob | $ |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for v in VARIANTS:
        f = fleet[v]
        print(f"| {v} | {f['n_slices_completed']}/3 | "
              f"{f['total_candidates']} | {f['total_fills']} | "
              f"{f['total_wins']} | {f['total_losses']} | "
              f"{f['fleet_wr_pct']:.1f}% | "
              f"{f['fleet_expectancy_r']:+.3f}R | "
              f"{f['total_parse_err']} | "
              f"{f['total_sl_beyond_ob']} | "
              f"${f['total_cost_usd']:.3f} |")
    print()


if __name__ == "__main__":
    main()
