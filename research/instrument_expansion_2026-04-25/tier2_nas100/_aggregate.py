"""Aggregate 12 NAS100 F3 backtest slices into headline metrics.

Mirrors XAGUSD/EURUSD aggregation:
- CANDs (raw + final), L2 rejects, fills
- WR with Wilson 95% CI; bootstrap CI on Exp R; MaxDD (chronological)
- Per-month (Jan/Feb/Mar/Apr) breakdown
- Per-direction (LONG/SHORT) breakdown
- Per-framework attribution
- Pre-registered acceptance gate
"""
from __future__ import annotations

import glob
import json
import math
import os
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Sequence

# Optional: numpy for bootstrap; fall back to manual implementation
try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False
    np = None  # type: ignore

BASE = Path(__file__).resolve().parent
SLICES_GLOB = str(BASE / "s*" / "all_results.json")


def wilson_ci(wins: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Wilson 95% CI for binomial proportion. Returns (low_pct, high_pct)."""
    if n == 0:
        return (0.0, 0.0)
    p = wins / n
    z = 1.959963984540054  # 95% z
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    halfw = z * math.sqrt((p * (1 - p) / n) + (z * z / (4 * n * n))) / denom
    return (max(0.0, (centre - halfw) * 100), min(100.0, (centre + halfw) * 100))


def bootstrap_mean_ci(values: Sequence[float], n_boot: int = 5000, alpha: float = 0.05, seed: int = 42) -> tuple[float, float]:
    """Bootstrap percentile CI for the mean."""
    if not values:
        return (0.0, 0.0)
    if HAVE_NUMPY:
        import numpy as _np
        rng = _np.random.default_rng(seed)
        arr = _np.asarray(values, dtype=float)
        n = len(arr)
        idx = rng.integers(0, n, size=(n_boot, n))
        means = arr[idx].mean(axis=1)
        return (float(_np.percentile(means, 100 * alpha / 2)),
                float(_np.percentile(means, 100 * (1 - alpha / 2))))
    # numpy-free fallback
    import random
    random.seed(seed)
    n = len(values)
    means = []
    for _ in range(n_boot):
        sample = [values[random.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(n_boot * alpha / 2)]
    hi = means[int(n_boot * (1 - alpha / 2))]
    return (lo, hi)


def chronological_max_drawdown(filled_trades: list[dict]) -> float:
    """Compute chronological MaxDD across slices.

    Sort all filled trades by candle_time and compute peak-to-trough drawdown
    in cumulative R. Returns DD as positive R (e.g. 6.0 means 6R drawdown).
    """
    sorted_trades = sorted(filled_trades, key=lambda t: t.get("candle_time", ""))
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in sorted_trades:
        r = t.get("r_multiple")
        if r is None:
            continue
        cum += r
        peak = max(peak, cum)
        dd = peak - cum
        max_dd = max(max_dd, dd)
    return max_dd


def parse_framework(cand: dict) -> str:
    """Extract framework label from CANDIDATE record."""
    raw = cand.get("raw_response", "") or ""
    # Try parsed structure first
    fw = cand.get("framework")
    if fw:
        return str(fw)
    # Fallback: regex on raw_response JSON-ish text
    import re
    m = re.search(r'"framework"\s*:\s*"([^"]+)"', raw)
    if m:
        return m.group(1)
    return "unknown"


def main() -> None:
    files = sorted(glob.glob(SLICES_GLOB))
    print(f"Found {len(files)} slice result files")

    all_results: list[dict] = []
    total_cost = 0.0
    slice_meta: list[dict] = []

    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        sid = os.path.basename(os.path.dirname(f))
        slice_meta.append({
            "slice": sid,
            "start": d.get("start"),
            "end": d.get("end"),
            "cost": d.get("total_cost", 0.0),
            "n": len(d.get("results", [])),
        })
        total_cost += d.get("total_cost", 0.0)
        for r in d.get("results", []):
            r["_slice"] = sid
            all_results.append(r)

    print(f"\nTotal results: {len(all_results)}, total cost: ${total_cost:.2f}")

    # --- Funnel ---
    counts: dict[str, int] = defaultdict(int)
    for r in all_results:
        dec = r.get("decision", "?")
        counts[f"decision_{dec}"] += 1
        if dec == "NO_TRADE":
            reason = (r.get("no_trade_reason") or "").split(":")[0]
            counts[f"no_trade_{reason}"] += 1

    candidates = [r for r in all_results if r.get("decision") == "CANDIDATE"]
    raw_cand_count = len(candidates)

    # L2 pass / final filled
    l2_passed = [c for c in candidates if c.get("l2_passed", True)]
    l2_failed_count = raw_cand_count - len(l2_passed)

    # Filled = those with non-null r_multiple
    filled = [c for c in l2_passed if c.get("r_multiple") is not None]
    not_filled_count = len(l2_passed) - len(filled)

    # --- WR ---
    wins = sum(1 for c in filled if (c.get("r_multiple") or 0.0) > 0)
    losses = len(filled) - wins
    wr_pct = (wins / len(filled) * 100) if filled else 0.0
    wr_lo, wr_hi = wilson_ci(wins, len(filled))

    # --- Exp R ---
    r_values = [c["r_multiple"] for c in filled]
    exp_r = (sum(r_values) / len(r_values)) if r_values else 0.0
    exp_r_lo, exp_r_hi = bootstrap_mean_ci(r_values) if r_values else (0.0, 0.0)
    total_r = sum(r_values)

    # --- MaxDD ---
    max_dd = chronological_max_drawdown(filled)

    # --- Per-month ---
    by_month: dict[str, dict] = defaultdict(lambda: {"cands": 0, "filled": 0, "wins": 0, "total_r": 0.0})
    for c in candidates:
        ts = c.get("candle_time", "")[:7]  # YYYY-MM
        by_month[ts]["cands"] += 1
    for c in filled:
        ts = c.get("candle_time", "")[:7]
        by_month[ts]["filled"] += 1
        r = c.get("r_multiple") or 0.0
        if r > 0:
            by_month[ts]["wins"] += 1
        by_month[ts]["total_r"] += r

    # --- Per-direction ---
    by_dir: dict[str, dict] = defaultdict(lambda: {"cands": 0, "filled": 0, "wins": 0, "total_r": 0.0})
    for c in candidates:
        dir_ = c.get("direction") or "UNKNOWN"
        by_dir[dir_]["cands"] += 1
    for c in filled:
        dir_ = c.get("direction") or "UNKNOWN"
        by_dir[dir_]["filled"] += 1
        r = c.get("r_multiple") or 0.0
        if r > 0:
            by_dir[dir_]["wins"] += 1
        by_dir[dir_]["total_r"] += r

    # --- Per-framework ---
    by_fw: dict[str, dict] = defaultdict(lambda: {"cands": 0, "filled": 0, "wins": 0, "total_r": 0.0})
    for c in candidates:
        fw = parse_framework(c)
        by_fw[fw]["cands"] += 1
    for c in filled:
        fw = parse_framework(c)
        by_fw[fw]["filled"] += 1
        r = c.get("r_multiple") or 0.0
        if r > 0:
            by_fw[fw]["wins"] += 1
        by_fw[fw]["total_r"] += r

    # --- KZ split ---
    by_kz: dict[str, dict] = defaultdict(lambda: {"cands": 0, "filled": 0, "wins": 0, "total_r": 0.0})
    for c in candidates:
        kz = c.get("kill_zone") or "UNKNOWN"
        by_kz[kz]["cands"] += 1
    for c in filled:
        kz = c.get("kill_zone") or "UNKNOWN"
        by_kz[kz]["filled"] += 1
        r = c.get("r_multiple") or 0.0
        if r > 0:
            by_kz[kz]["wins"] += 1
        by_kz[kz]["total_r"] += r

    # --- Pre-registered gate ---
    PRE_REG = {
        "wr_min": 55.0,
        "exp_r_min": 0.10,
        "n_min": 30,
        "max_dd_max": 8.0,
    }
    gate_results = {
        "wr_pass": wr_pct >= PRE_REG["wr_min"],
        "exp_r_pass": exp_r >= PRE_REG["exp_r_min"],
        "n_pass": len(filled) >= PRE_REG["n_min"],
        "max_dd_pass": max_dd <= PRE_REG["max_dd_max"],
    }
    all_pass = all(gate_results.values())

    # Verdict ladder
    if all_pass:
        verdict = "PROMOTE-LIVE"
    else:
        # Soft passes: ≥3 of 4 with marginal failures
        passes = sum(1 for v in gate_results.values() if v)
        if passes >= 3 and len(filled) >= 20:
            verdict = "3-DAY-LIVE-OBSERVE"
        elif passes >= 2 and len(filled) >= 15:
            verdict = "OBSERVER-14D"
        else:
            verdict = "REJECT"

    # --- Build aggregate JSON ---
    aggregate = {
        "instrument": "NAS100",
        "tier": 2,
        "detector_version": "v2",
        "kz_config_used": {
            "london": "07:00-10:30 UTC",
            "ny": "13:00-17:00 UTC",
            "source": "agent_config.yaml deep-merged with base XAUUSD london leak (mirrors live)",
        },
        "slices": slice_meta,
        "total_kz_candles": len(all_results),
        "total_cost_usd": round(total_cost, 2),
        "funnel": {
            "raw_candidates": raw_cand_count,
            "l2_failed": l2_failed_count,
            "l2_passed": len(l2_passed),
            "not_filled": not_filled_count,
            "filled": len(filled),
            "decisions": dict(counts),
        },
        "headline": {
            "n_filled": len(filled),
            "wins": wins,
            "losses": losses,
            "wr_pct": round(wr_pct, 1),
            "wr_ci_95_pct": [round(wr_lo, 1), round(wr_hi, 1)],
            "exp_r": round(exp_r, 3),
            "exp_r_ci_95_bootstrap": [round(exp_r_lo, 3), round(exp_r_hi, 3)],
            "total_r": round(total_r, 2),
            "max_dd_r": round(max_dd, 2),
        },
        "by_month": {k: dict(v) for k, v in sorted(by_month.items())},
        "by_direction": {k: dict(v) for k, v in by_dir.items()},
        "by_framework": {k: dict(v) for k, v in by_fw.items()},
        "by_kz": {k: dict(v) for k, v in by_kz.items()},
        "pre_registered_gate": {
            "thresholds": PRE_REG,
            "results": gate_results,
            "all_pass": all_pass,
        },
        "verdict": verdict,
    }

    # Write
    agg_path = BASE / "aggregate.json"
    with open(agg_path, "w", encoding="utf-8") as fh:
        json.dump(aggregate, fh, indent=2)
    print(f"Wrote {agg_path}")

    # Combined all_results.json (no raw_response to keep size sane)
    combined_path = BASE / "all_results.json"
    slim = []
    for r in all_results:
        rcopy = {k: v for k, v in r.items() if k != "raw_response"}
        slim.append(rcopy)
    with open(combined_path, "w", encoding="utf-8") as fh:
        json.dump({"instrument": "NAS100", "results": slim}, fh, indent=2)
    print(f"Wrote {combined_path}")

    # Print short summary
    print("\n=== HEADLINE ===")
    print(f"Filled trades: {len(filled)} (wins {wins}, losses {losses})")
    print(f"WR: {wr_pct:.1f}% [{wr_lo:.1f}%, {wr_hi:.1f}%]")
    print(f"Exp R: {exp_r:+.3f}R [{exp_r_lo:+.3f}, {exp_r_hi:+.3f}]")
    print(f"Total R: {total_r:+.2f}R   MaxDD: {max_dd:.2f}R")
    print(f"Total cost: ${total_cost:.2f}")
    print(f"\nGate: {gate_results}")
    print(f"VERDICT: {verdict}")


if __name__ == "__main__":
    main()
