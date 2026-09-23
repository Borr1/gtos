"""Q-6.2 — Partial Close Scheme Optimization.

Pre-registered multi-scheme replay on existing batch trade data.
Compares 4 partial-close variants against the baseline (actual outcome under
the current system's multi-TP + trailing exit ruleset).

Schemes:
  BASELINE: actual r_multiple under current exit rules (reference = 0.0 delta)
  C       : 33% @ +1.0R, 67% runner to actual_r (BE stop if reversed)
  D1      : 50% @ +1.0R, 50% runner to actual_r (BE stop if reversed)
  D2      : 25% @ +1.0R, 25% @ +1.5R, 50% runner to actual_r (BE stop if reversed)
  D3      : 33% @ +1.0R, 33% @ +1.5R, 34% runner to actual_r (BE stop if reversed)

Triggers:
  C and D1 require mfe_r >= 1.0
  D2 and D3 require mfe_r >= 1.5 (otherwise they reduce to single-level scheme)

Primary metric: mean delta_r vs baseline (i.e., vs actual_r_multiple).
Secondary: Wilcoxon signed-rank p, 95% bootstrap CI on mean, max 20-trade drawdown.
Sample threshold: n >= 30 per scheme (else mark "underpowered").
Multiple comparisons: Bonferroni alpha = 0.05 / 4 = 0.0125.

Universe: union of three batch sources, dedup'd by trade_id:
  knowledge_base_backtest/batch_api/*_results.json (318 unique)
  knowledge_base_backtest/analysis/unified_trades_v2_20260331.json (111, subset)
  knowledge_base_backtest/analysis/phase1_all_trades_merged.json (18, r_path bearer)

For trades with r_path (18 of 251), reversal-past-entry is determined
bar-by-bar (exact mode). For the remaining 233, the approx heuristic is:
  winner (r_multiple > 0) -> did not reverse past entry -> runner = r_multiple
  loser (r_multiple <= 0) -> did reverse past entry       -> runner = 0 (BE stop)
Same heuristic as scripts/variant_c_replay.py (byte-equivalent for Variant C
on the 45-row overlap subset).

Outputs:
  q62_scheme_results.csv    : per-trade per-scheme deltas (long format)
  q62_summary.json          : per-scheme aggregate stats

Usage:
  python research/q62_partial_close_optimization/q62_replay.py
"""
from __future__ import annotations

import csv
import glob
import json
import math
import os
import random
from pathlib import Path

# --- Scheme definitions ------------------------------------------------------
# Each scheme: list of (fraction, target_r). Sum of fractions == 1.0.
# The last entry is the runner leg — its target_r is the realized runner R.
SCHEMES = {
    "C":  [(0.33, 1.0), (0.67, "runner")],
    "D1": [(0.50, 1.0), (0.50, "runner")],
    "D2": [(0.25, 1.0), (0.25, 1.5), (0.50, "runner")],
    "D3": [(0.33, 1.0), (0.33, 1.5), (0.34, "runner")],
}

# Trigger rules — scheme only applies if the minimum R level in the scheme
# was actually reached (mfe_r >= that level). Otherwise scheme == baseline.
SCHEME_TRIGGER_R = {
    "C":  1.0,
    "D1": 1.0,
    "D2": 1.5,  # needs +1.5R MFE to fill both partials
    "D3": 1.5,
}

BOOT_N = 10_000
BOOT_SEED = 20260418

# --- Data loading ------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]


def _load_batch_api():
    """Yield day records from knowledge_base_backtest/batch_api/*_results.json."""
    paths = sorted(glob.glob(str(ROOT / "knowledge_base_backtest" / "batch_api" / "*_results.json")))
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(d, list):
            for rec in d:
                for tr in rec.get("trades", []) or []:
                    yield tr


def _load_unified():
    p = ROOT / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return []


def _load_phase1():
    p = ROOT / "knowledge_base_backtest" / "analysis" / "phase1_all_trades_merged.json"
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return []


def load_universe():
    """Return dedup'd union of all three batch sources.

    Dedup keys: trade_id where available; synthesised key
    'p1_{date}_{kz}_{candle_time}_{entry_price}' for phase1 rows.
    Priority order (later overwrites earlier): batch_api -> unified -> phase1.
    This ensures r_path-bearing phase1 rows win when they overlap.
    """
    trades: dict[str, dict] = {}
    # 1) batch_api (lowest priority — raw trade dicts, minimal metadata)
    for tr in _load_batch_api():
        tid = tr.get("trade_id")
        if tid and tid not in trades:
            trades[tid] = dict(tr)
    # 2) unified (richer metadata, trade_ids identical to batch_api entries)
    for t in _load_unified():
        tid = t.get("trade_id")
        if tid:
            trades[tid] = dict(t)
    # 3) phase1 (r_path carriers; no trade_ids — synthesise)
    for t in _load_phase1():
        key = f"p1_{t.get('date')}_{t.get('kill_zone')}_{t.get('candle_time', '?')}_{t.get('entry_price')}"
        trades[key] = dict(t)
    return list(trades.values())


def _valid(t: dict) -> bool:
    return (
        t.get("mfe_r") is not None
        and t.get("r_multiple") is not None
        and t.get("direction") in ("LONG", "SHORT")
    )


# --- Scheme computation ------------------------------------------------------
def _runner_r(trade: dict, partials_taken_at: float) -> float:
    """Compute the remaining runner R after the last partial was taken.

    partials_taken_at: the highest R level at which a partial was booked
                       (e.g., 1.0 for C/D1, 1.5 for D2/D3).

    If r_path available: walk bars AFTER the last partial bar; if r_low or
    r_close <= 0 (reversal past entry), return 0. Otherwise return r_multiple.

    If r_path NOT available: approx heuristic — winners (r_multiple > 0) did
    not reverse past entry, so runner = r_multiple. Losers (r_multiple <= 0)
    reversed past entry, so runner = 0 (BE stop).
    """
    r_mult = float(trade["r_multiple"])
    r_path = trade.get("r_path") or []

    if r_path:
        # Find the bar where R first reached partials_taken_at
        trigger_idx = None
        for i, bar in enumerate(r_path):
            r_high = bar.get("r_at_high")
            r_close = bar.get("r_at_close")
            for r in (r_high, r_close):
                if r is not None and r >= partials_taken_at:
                    trigger_idx = i
                    break
            if trigger_idx is not None:
                break
        if trigger_idx is None:
            # Shouldn't happen — caller guaranteed mfe_r >= partials_taken_at.
            # Fall back to approx.
            return r_mult if r_mult > 0 else 0.0
        # Walk bars after trigger for reversal past entry
        for bar in r_path[trigger_idx + 1 :]:
            r_low = bar.get("r_at_low")
            r_close = bar.get("r_at_close")
            for r in (r_low, r_close):
                if r is not None and r <= 0:
                    return 0.0
        return r_mult

    # Approx mode
    return r_mult if r_mult > 0 else 0.0


def scheme_r(trade: dict, scheme_name: str) -> float | None:
    """Blended R under the given partial-close scheme, or None if no trigger."""
    legs = SCHEMES[scheme_name]
    trigger_r = SCHEME_TRIGGER_R[scheme_name]
    mfe_r = float(trade["mfe_r"])
    if mfe_r < trigger_r:
        return None

    # Determine highest fixed-R partial the trade's MFE reached
    fixed_partials = [lev for frac, lev in legs if isinstance(lev, (int, float))]
    highest_reached = 0.0
    for lev in fixed_partials:
        if mfe_r >= lev:
            highest_reached = max(highest_reached, lev)

    # Any fixed-R leg whose target > mfe_r is not filled — scheme un-triggered.
    # (D2 / D3 need +1.5R; we already gate on trigger_r above. But sanity:)
    for frac, lev in legs:
        if isinstance(lev, (int, float)) and lev > mfe_r:
            return None

    runner = _runner_r(trade, highest_reached)
    total = 0.0
    for frac, lev in legs:
        if lev == "runner":
            total += frac * runner
        else:
            total += frac * float(lev)
    return total


# --- Statistics --------------------------------------------------------------
def _wilcoxon(x: list[float]) -> tuple[float, float]:
    try:
        from scipy.stats import wilcoxon
    except ImportError:
        return float("nan"), float("nan")
    nz = [d for d in x if d != 0]
    if len(nz) < 6:
        return float("nan"), float("nan")
    res = wilcoxon(nz, alternative="two-sided", zero_method="wilcox")
    return float(res.statistic), float(res.pvalue)


def _bootstrap_ci(x: list[float], n_boot: int = BOOT_N, ci: float = 0.95) -> tuple[float, float]:
    if not x:
        return float("nan"), float("nan")
    rng = random.Random(BOOT_SEED)
    n = len(x)
    means = []
    for _ in range(n_boot):
        sample = [x[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_idx = int((1 - ci) / 2 * n_boot)
    hi_idx = int((1 + ci) / 2 * n_boot) - 1
    return means[lo_idx], means[hi_idx]


def _max_window_drawdown(deltas: list[float], window: int = 20) -> float:
    """Max cumulative loss over any `window`-length slice of the delta series.

    Interpretation: the worst 20-trade rolling sum of delta_r. Negative = scheme
    was worse than baseline over a stretch.
    """
    if len(deltas) < window:
        return sum(deltas)  # single window
    worst = 0.0
    for i in range(len(deltas) - window + 1):
        s = sum(deltas[i : i + window])
        if s < worst:
            worst = s
    return worst


def _stdev(x: list[float]) -> float:
    if len(x) < 2:
        return 0.0
    m = sum(x) / len(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1))


# --- Main --------------------------------------------------------------------
def main() -> int:
    out_dir = ROOT / "research" / "q62_partial_close_optimization"
    out_dir.mkdir(parents=True, exist_ok=True)

    universe = load_universe()
    valid = [t for t in universe if _valid(t)]
    print(f"universe total: {len(universe)}, valid (mfe_r+r+direction): {len(valid)}")

    # --- Per-trade per-scheme replay ---------------------------------------
    per_trade_rows = []
    # scheme -> list of (trade_id, delta_r, has_rpath)
    scheme_deltas: dict[str, list[tuple[str, float, bool]]] = {k: [] for k in SCHEMES}

    for t in valid:
        tid = t.get("trade_id") or f"p1_{t.get('date')}_{t.get('kill_zone')}_{t.get('candle_time', '?')}_{t.get('entry_price')}"
        actual_r = float(t["r_multiple"])
        has_rpath = bool(t.get("r_path"))
        mfe_r = float(t["mfe_r"])
        row = {
            "trade_id": tid,
            "date": t.get("date", ""),
            "kill_zone": t.get("kill_zone", ""),
            "direction": t.get("direction", ""),
            "mfe_r": mfe_r,
            "mae_r": float(t.get("mae_r") or 0.0),
            "actual_r_multiple": actual_r,
            "has_r_path": has_rpath,
        }
        for scheme in SCHEMES:
            r_blended = scheme_r(t, scheme)
            if r_blended is None:
                row[f"scheme_{scheme}_r"] = None
                row[f"scheme_{scheme}_delta"] = None
                row[f"scheme_{scheme}_triggered"] = False
            else:
                delta = r_blended - actual_r
                row[f"scheme_{scheme}_r"] = round(r_blended, 4)
                row[f"scheme_{scheme}_delta"] = round(delta, 4)
                row[f"scheme_{scheme}_triggered"] = True
                scheme_deltas[scheme].append((tid, delta, has_rpath))
        per_trade_rows.append(row)

    # --- Write per-trade CSV (long format) ---------------------------------
    csv_path = out_dir / "q62_scheme_results.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "trade_id", "date", "kill_zone", "direction",
            "mfe_r", "mae_r", "actual_r_multiple", "has_r_path",
            "scheme", "scheme_blended_r", "delta_r_vs_baseline", "triggered",
        ])
        for row in per_trade_rows:
            for scheme in SCHEMES:
                w.writerow([
                    row["trade_id"], row["date"], row["kill_zone"], row["direction"],
                    row["mfe_r"], row["mae_r"], row["actual_r_multiple"], row["has_r_path"],
                    scheme,
                    row[f"scheme_{scheme}_r"] if row[f"scheme_{scheme}_r"] is not None else "",
                    row[f"scheme_{scheme}_delta"] if row[f"scheme_{scheme}_delta"] is not None else "",
                    row[f"scheme_{scheme}_triggered"],
                ])
    print(f"wrote {csv_path}")

    # --- Per-scheme aggregate stats ----------------------------------------
    BONFERRONI_ALPHA = 0.05 / 4  # 4 schemes vs baseline
    summary = {
        "universe_size": len(universe),
        "valid_universe_size": len(valid),
        "sample_threshold": 30,
        "bonferroni_alpha": BONFERRONI_ALPHA,
        "schemes": {},
    }
    per_scheme_rows = []
    for scheme, trips in scheme_deltas.items():
        deltas = [d for _, d, _ in trips]
        n_exact = sum(1 for _, _, hp in trips if hp)
        n_approx = len(trips) - n_exact
        if not deltas:
            summary["schemes"][scheme] = {"n": 0, "underpowered": True}
            continue
        mean = sum(deltas) / len(deltas)
        std = _stdev(deltas)
        med = sorted(deltas)[len(deltas) // 2]
        wilc_w, wilc_p = _wilcoxon(deltas)
        boot_lo, boot_hi = _bootstrap_ci(deltas)
        max_dd = _max_window_drawdown(deltas, window=20)
        wins = sum(1 for d in deltas if d > 0)
        losses = sum(1 for d in deltas if d < 0)
        ties = sum(1 for d in deltas if d == 0)
        # Bonferroni pass
        passes_bonf = (wilc_p == wilc_p) and (wilc_p < BONFERRONI_ALPHA)
        passes_uncorrected = (wilc_p == wilc_p) and (wilc_p < 0.05)
        passes_n = len(deltas) >= 30
        summary["schemes"][scheme] = {
            "n": len(deltas),
            "n_exact": n_exact,
            "n_approx": n_approx,
            "underpowered": not passes_n,
            "mean_delta_r": round(mean, 4),
            "median_delta_r": round(med, 4),
            "stdev_delta_r": round(std, 4),
            "min_delta_r": round(min(deltas), 4),
            "max_delta_r": round(max(deltas), 4),
            "cum_delta_r": round(sum(deltas), 4),
            "wins": wins, "losses": losses, "ties": ties,
            "win_rate_pct": round(100 * wins / len(deltas), 2),
            "wilcoxon_W": round(wilc_w, 2) if wilc_w == wilc_w else None,
            "wilcoxon_p_two_sided": round(wilc_p, 6) if wilc_p == wilc_p else None,
            "passes_uncorrected_p05": passes_uncorrected,
            "passes_bonferroni_0125": passes_bonf,
            "bootstrap_ci95_lo": round(boot_lo, 4),
            "bootstrap_ci95_hi": round(boot_hi, 4),
            "max_20_trade_drawdown_r": round(max_dd, 4),
        }
        per_scheme_rows.append((scheme, summary["schemes"][scheme]))

    # Ranking
    ranked = sorted(
        [(s, st) for s, st in per_scheme_rows if st["n"] > 0],
        key=lambda sst: sst[1]["mean_delta_r"],
        reverse=True,
    )
    summary["ranking_by_mean_delta"] = [s for s, _ in ranked]

    # Verdict logic (pre-registered):
    #   PROMOTE scheme X if X passes Bonferroni (p < 0.0125) AND mean_delta > 0
    #                      AND X is top-ranked.
    #   DEFER if no scheme clears Bonferroni.
    #   NULL / KILL if top-ranked has mean_delta <= 0.
    verdict = "DEFER"
    verdict_note = ""
    if ranked:
        top_s, top_st = ranked[0]
        if top_st["passes_bonferroni_0125"] and top_st["mean_delta_r"] > 0:
            verdict = f"PROMOTE_{top_s}"
            verdict_note = f"{top_s} clears Bonferroni (p={top_st['wilcoxon_p_two_sided']}) and is top-ranked"
        elif top_st["mean_delta_r"] <= 0:
            verdict = "NULL"
            verdict_note = "best scheme has mean delta <= 0; no partial scheme improves expectancy"
        else:
            weakest_uncor = top_st["passes_uncorrected_p05"]
            verdict_note = (
                f"top-ranked {top_s} mean_delta={top_st['mean_delta_r']} "
                f"but Wilcoxon p={top_st['wilcoxon_p_two_sided']} fails Bonferroni (alpha=0.0125)"
                + (" [passes uncorrected p<0.05]" if weakest_uncor else "")
            )
    summary["verdict"] = verdict
    summary["verdict_note"] = verdict_note

    # --- Apples-to-apples sub-analysis on +1.5R-triggered subset ----------
    # This is the only subset where all 4 schemes fire, so rankings here are
    # not trigger-population confounded.
    common_subset = [t for t in valid if float(t["mfe_r"]) >= 1.5]
    summary["common_subset_analysis"] = {
        "subset_n": len(common_subset),
        "subset_mean_actual_r": round(
            sum(float(t["r_multiple"]) for t in common_subset) / max(len(common_subset), 1), 4
        ),
        "schemes": {},
    }
    for scheme in SCHEMES:
        deltas_cs = []
        for t in common_subset:
            r = scheme_r(t, scheme)
            if r is not None:
                deltas_cs.append(r - float(t["r_multiple"]))
        if not deltas_cs:
            summary["common_subset_analysis"]["schemes"][scheme] = {"n": 0}
            continue
        mean = sum(deltas_cs) / len(deltas_cs)
        wilc_w, wilc_p = _wilcoxon(deltas_cs)
        summary["common_subset_analysis"]["schemes"][scheme] = {
            "n": len(deltas_cs),
            "mean_delta_r": round(mean, 4),
            "cum_delta_r": round(sum(deltas_cs), 4),
            "wilcoxon_W": round(wilc_w, 2) if wilc_w == wilc_w else None,
            "wilcoxon_p_two_sided": round(wilc_p, 6) if wilc_p == wilc_p else None,
        }

    # Write summary
    sj = out_dir / "q62_summary.json"
    with open(sj, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"wrote {sj}")

    # --- Console report ----------------------------------------------------
    print()
    print("=== Q-6.2 partial close scheme replay ===")
    print(f"universe valid trades: {len(valid)}")
    print(f"Bonferroni alpha: {BONFERRONI_ALPHA} (4 comparisons)")
    print()
    print(f"{'scheme':<6} {'n':>4} {'n_exact':>8} {'mean_d':>9} {'med_d':>8} {'std':>6} {'W':>9} {'p(2s)':>9} {'CI95':<22} {'max_20_dd':>11} {'wins':>5}")
    for scheme, st in ranked:
        if st["n"] == 0:
            continue
        p_display = f"{st['wilcoxon_p_two_sided']:.4f}" if st["wilcoxon_p_two_sided"] is not None else "NA"
        ci_display = f"[{st['bootstrap_ci95_lo']:+.3f},{st['bootstrap_ci95_hi']:+.3f}]"
        print(f"{scheme:<6} {st['n']:>4d} {st['n_exact']:>8d} {st['mean_delta_r']:>+9.4f} {st['median_delta_r']:>+8.4f} "
              f"{st['stdev_delta_r']:>6.3f} {st['wilcoxon_W']:>9.2f} {p_display:>9} "
              f"{ci_display:<22} {st['max_20_trade_drawdown_r']:>+11.4f} {st['wins']:>5d}")
    print()
    print(f"Ranking by mean delta: {summary['ranking_by_mean_delta']}")
    print(f"VERDICT: {verdict}")
    print(f"NOTE: {verdict_note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
