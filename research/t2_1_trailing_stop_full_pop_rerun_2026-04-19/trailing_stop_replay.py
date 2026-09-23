"""T2.1 — Full-population trailing-stop rerun.

Compares 4 trailing-stop variants + 1 BE-only variant against the current
"100% at TP1" baseline on the merged batch KB (trades dedup'd across
batch_api, unified_v2, phase1).

See PRE_REGISTRATION.md in this directory for hypotheses and decision rule.
No API calls; pure Python over on-disk JSON.

Outputs:
  variants_comparison.csv      per-variant summary metrics
  per_trade_outcomes.jsonl     one row per trade per variant (audit)
  run_metadata.json            population counts, symbol breakdown, config

Usage:
  python research/t2_1_trailing_stop_full_pop_rerun_2026-04-19/trailing_stop_replay.py
"""
from __future__ import annotations

import csv
import glob
import json
import math
import os
import random
from pathlib import Path
from collections import Counter, defaultdict


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
SYMBOL_MAP_PATH = OUT_DIR / "batch_symbol_map.json"

# -----------------------------------------------------------------------------
# Variants
# -----------------------------------------------------------------------------
# name: (activation_R, trail_distance_R, mode)
# mode "trail" = trailing stop, exit = peak - trail_distance (capped at baseline)
# mode "be"   = breakeven only, exit = max(baseline, 0) once mfe_r >= activation
VARIANTS = {
    "V1_act0.5_tr0.5": (0.5, 0.5, "trail"),
    "V2_act0.5_tr1.5": (0.5, 1.5, "trail"),
    "V3_act1.0_tr0.5": (1.0, 0.5, "trail"),
    "V4_act1.0_BEonly": (1.0, 0.0, "be"),
}

BOOT_N = 10_000
BOOT_SEED = 20260419


# -----------------------------------------------------------------------------
# Data loading
# -----------------------------------------------------------------------------
def _load_batch_api_with_batchid():
    """Yield (batch_id, trade_dict) for every trade in batch_api/*_results.json.

    The batch_id is the filename stem minus the _results / _raw_results suffix,
    which lets us resolve the instrument symbol via batch_symbol_map.json.
    """
    # Prefer non-raw files; avoid double-counting.
    paths = sorted(
        glob.glob(str(ROOT / "knowledge_base_backtest" / "batch_api" / "msgbatch_*_results.json"))
    )
    paths = [p for p in paths if not p.endswith("_raw_results.json")]
    for p in paths:
        bid = os.path.basename(p).replace("_results.json", "")
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        if isinstance(d, list):
            for rec in d:
                for tr in rec.get("trades", []) or []:
                    yield bid, tr


def _load_unified():
    p = ROOT / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _load_phase1():
    p = ROOT / "knowledge_base_backtest" / "analysis" / "phase1_all_trades_merged.json"
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def load_symbol_map() -> dict[str, str]:
    if not SYMBOL_MAP_PATH.exists():
        return {}
    with open(SYMBOL_MAP_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_universe() -> list[dict]:
    """Return dedup'd merged universe with `symbol` attribution where possible.

    Order: batch_api -> unified -> phase1 (later overwrites earlier).
    Symbol is attached from batch_symbol_map.json on first encounter.
    """
    symbol_map = load_symbol_map()
    trades: dict[str, dict] = {}

    for bid, tr in _load_batch_api_with_batchid():
        tid = tr.get("trade_id")
        if tid and tid not in trades:
            trades[tid] = dict(tr)
            if not trades[tid].get("symbol"):
                trades[tid]["symbol"] = symbol_map.get(bid, "UNKNOWN")

    for t in _load_unified():
        tid = t.get("trade_id")
        if tid:
            prior_symbol = trades.get(tid, {}).get("symbol")
            trades[tid] = dict(t)
            # preserve symbol already resolved from batch_api
            if prior_symbol and not trades[tid].get("symbol"):
                trades[tid]["symbol"] = prior_symbol

    for t in _load_phase1():
        key = f"p1_{t.get('date')}_{t.get('kill_zone')}_{t.get('candle_time', '?')}_{t.get('entry_price')}"
        trades[key] = dict(t)

    out = list(trades.values())
    # ensure every record has `symbol` field (UNKNOWN if not resolved)
    for t in out:
        if "symbol" not in t or not t["symbol"]:
            t["symbol"] = "UNKNOWN"
    return out


def _valid(t: dict) -> bool:
    return (
        t.get("mfe_r") is not None
        and t.get("r_multiple") is not None
        and t.get("direction") in ("LONG", "SHORT")
    )


# -----------------------------------------------------------------------------
# Variant evaluation
# -----------------------------------------------------------------------------
def variant_r(trade: dict, variant_name: str) -> tuple[float, bool, bool]:
    """Return (variant_R, triggered, used_r_path).

    triggered: True iff the activation threshold was reached (mfe_r >= act).
    used_r_path: True iff per-bar r_path walk was used (not MFE-approx).
    """
    act_r, trail_r, mode = VARIANTS[variant_name]
    baseline_r = float(trade["r_multiple"])
    mfe_r = float(trade["mfe_r"])
    r_path = trade.get("r_path") or []

    if mfe_r < act_r:
        return baseline_r, False, False

    if mode == "be":
        # BE mode: once armed, SL at 0R. If baseline was a loss (r < 0), BE
        # stop would have taken it out at 0 BEFORE it went to -1.  If baseline
        # was a win, variant = max(baseline, 0) = baseline.
        if r_path:
            # exact: find activation bar, walk forward, exit at 0 if r touches <= 0
            armed = False
            for bar in r_path:
                r_high = bar.get("r_at_high")
                r_close = bar.get("r_at_close")
                r_low = bar.get("r_at_low")
                if not armed:
                    for r in (r_high, r_close):
                        if r is not None and r >= act_r:
                            armed = True
                            break
                    if armed:
                        continue
                if armed:
                    for r in (r_low, r_close):
                        if r is not None and r <= 0:
                            return 0.0, True, True
            # never stopped out at BE; trade exited normally
            return baseline_r, True, True
        # approx: winners keep their R; losers get lifted to 0 (BE saves them)
        if baseline_r < 0:
            return 0.0, True, False
        return baseline_r, True, False

    # trail mode
    trail_exit = mfe_r - trail_r
    if r_path:
        # exact: find first bar where mfe_r >= act (arm), then walk trail
        armed = False
        peak_r = 0.0
        trailed_sl = None
        for bar in r_path:
            r_high = bar.get("r_at_high")
            r_low = bar.get("r_at_low")
            r_close = bar.get("r_at_close")
            if not armed:
                if r_high is not None and r_high >= act_r:
                    armed = True
                    peak_r = max(peak_r, r_high)
                    trailed_sl = peak_r - trail_r
                    continue
            else:
                # ratchet trail higher
                if r_high is not None and r_high > peak_r:
                    peak_r = r_high
                    trailed_sl = peak_r - trail_r
                # stop hit?
                if trailed_sl is not None and r_low is not None and r_low <= trailed_sl:
                    return trailed_sl, True, True
        # never stopped out; realized at baseline, but floor at trailed_sl so
        # we at least keep (peak - trail_r) if baseline was lower
        if trailed_sl is not None:
            return max(baseline_r, trailed_sl), True, True
        return baseline_r, True, True

    # approx mode (no r_path): assume trail exit lifts the realized R floor
    # to (peak - trail_r) whenever MFE >= activation. If baseline already >=
    # trail_exit, the trail wouldn't have helped (trade kept running).
    if baseline_r >= trail_exit:
        return baseline_r, True, False
    # baseline was lower than trail_exit => trail locked in a better result
    return trail_exit, True, False


# -----------------------------------------------------------------------------
# Statistics
# -----------------------------------------------------------------------------
def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    radius = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (centre - radius) / denom, (centre + radius) / denom


def wilcoxon_signed_rank(deltas: list[float]) -> tuple[float, float]:
    try:
        from scipy.stats import wilcoxon  # type: ignore
    except ImportError:
        return float("nan"), float("nan")
    nz = [d for d in deltas if d != 0]
    if len(nz) < 6:
        return float("nan"), float("nan")
    res = wilcoxon(nz, alternative="two-sided", zero_method="wilcox")
    return float(res.statistic), float(res.pvalue)


def bootstrap_mean_ci(
    x: list[float], n_boot: int = BOOT_N, ci: float = 0.95, seed: int = BOOT_SEED
) -> tuple[float, float]:
    if not x:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    n = len(x)
    means = []
    for _ in range(n_boot):
        s = 0.0
        for _ in range(n):
            s += x[rng.randrange(n)]
        means.append(s / n)
    means.sort()
    lo = means[int((1 - ci) / 2 * n_boot)]
    hi = means[int((1 + ci) / 2 * n_boot) - 1]
    return lo, hi


def max_window_drawdown(series: list[float], window: int = 20) -> float:
    """Worst sum over any `window`-length slice. Negative = drawdown."""
    if len(series) < window:
        return sum(series)
    worst = 0.0
    for i in range(len(series) - window + 1):
        s = sum(series[i : i + window])
        if s < worst:
            worst = s
    return worst


def stdev(x: list[float]) -> float:
    if len(x) < 2:
        return 0.0
    m = sum(x) / len(x)
    return math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1))


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> int:
    universe = load_universe()
    total = len(universe)
    valid = [t for t in universe if _valid(t)]
    dropped = total - len(valid)

    print(f"Merged universe size: {total}")
    print(f"Valid trades (has r_multiple + mfe_r + direction): {len(valid)}")
    print(f"Dropped (missing required fields): {dropped}")
    print("Symbol breakdown:", dict(Counter(t["symbol"] for t in valid)))
    print("Framework breakdown:", dict(Counter(t.get("framework") for t in valid)))
    print("r_path carriers:", sum(1 for t in valid if t.get("r_path")))
    print()

    # Per-variant evaluation
    per_trade_rows = []
    variant_stats = {}
    baseline_r_list = [float(t["r_multiple"]) for t in valid]

    for vname in VARIANTS:
        r_list = []
        delta_list = []
        triggered_count = 0
        hurt_count = 0  # variant R < baseline R
        exact_count = 0  # used r_path
        for t in valid:
            base = float(t["r_multiple"])
            vr, triggered, exact = variant_r(t, vname)
            if triggered:
                triggered_count += 1
            if exact:
                exact_count += 1
            delta = vr - base
            if delta < -1e-9:
                hurt_count += 1
            r_list.append(vr)
            delta_list.append(delta)
            per_trade_rows.append(
                {
                    "trade_id": t.get("trade_id") or t.get("date", "") + "_" + t.get("kill_zone", ""),
                    "symbol": t.get("symbol"),
                    "framework": t.get("framework"),
                    "variant": vname,
                    "baseline_r": round(base, 4),
                    "variant_r": round(vr, 4),
                    "delta_r": round(delta, 4),
                    "mfe_r": round(float(t["mfe_r"]), 4),
                    "mae_r": round(float(t["mae_r"]), 4) if t.get("mae_r") is not None else None,
                    "triggered": triggered,
                    "used_r_path": exact,
                }
            )

        n = len(r_list)
        wins = sum(1 for r in r_list if r > 0)
        base_wins = sum(1 for r in baseline_r_list if r > 0)
        wr = wins / n if n else 0.0
        base_wr = base_wins / n if n else 0.0
        wilson_lo, wilson_hi = wilson_ci(wins, n)

        mean_r = sum(r_list) / n if n else 0.0
        base_mean_r = sum(baseline_r_list) / n if n else 0.0
        mean_delta = sum(delta_list) / n if n else 0.0
        sd_delta = stdev(delta_list)
        total_r = sum(r_list)
        base_total_r = sum(baseline_r_list)
        total_delta = total_r - base_total_r

        boot_lo, boot_hi = bootstrap_mean_ci(delta_list)
        w_stat, w_p = wilcoxon_signed_rank(delta_list)
        dd_20 = max_window_drawdown(delta_list, window=20)

        variant_stats[vname] = {
            "n": n,
            "triggered": triggered_count,
            "triggered_pct": round(100.0 * triggered_count / n, 2) if n else 0.0,
            "exact_via_r_path": exact_count,
            "hurt_count": hurt_count,
            "hurt_pct_of_triggered": round(100.0 * hurt_count / triggered_count, 2) if triggered_count else 0.0,
            "wr_variant": round(wr, 4),
            "wr_baseline": round(base_wr, 4),
            "wr_wilson95": [round(wilson_lo, 4), round(wilson_hi, 4)],
            "mean_r_variant": round(mean_r, 4),
            "mean_r_baseline": round(base_mean_r, 4),
            "mean_delta_r": round(mean_delta, 4),
            "delta_sd": round(sd_delta, 4),
            "total_r_variant": round(total_r, 2),
            "total_r_baseline": round(base_total_r, 2),
            "total_delta_r": round(total_delta, 2),
            "bootstrap_ci95_mean_delta": [round(boot_lo, 4), round(boot_hi, 4)],
            "wilcoxon_stat": round(w_stat, 2) if not math.isnan(w_stat) else None,
            "wilcoxon_p": round(w_p, 6) if not math.isnan(w_p) else None,
            "max_20trade_dd_r": round(dd_20, 2),
        }

    # Baseline summary row (for reference)
    base_wins = sum(1 for r in baseline_r_list if r > 0)
    base_wr = base_wins / len(baseline_r_list) if baseline_r_list else 0.0
    base_wilson_lo, base_wilson_hi = wilson_ci(base_wins, len(baseline_r_list))
    baseline_row = {
        "n": len(baseline_r_list),
        "triggered": None,
        "triggered_pct": None,
        "exact_via_r_path": sum(1 for t in valid if t.get("r_path")),
        "hurt_count": None,
        "hurt_pct_of_triggered": None,
        "wr_variant": round(base_wr, 4),
        "wr_baseline": round(base_wr, 4),
        "wr_wilson95": [round(base_wilson_lo, 4), round(base_wilson_hi, 4)],
        "mean_r_variant": round(sum(baseline_r_list) / len(baseline_r_list), 4) if baseline_r_list else 0.0,
        "mean_r_baseline": round(sum(baseline_r_list) / len(baseline_r_list), 4) if baseline_r_list else 0.0,
        "mean_delta_r": 0.0,
        "delta_sd": 0.0,
        "total_r_variant": round(sum(baseline_r_list), 2),
        "total_r_baseline": round(sum(baseline_r_list), 2),
        "total_delta_r": 0.0,
        "bootstrap_ci95_mean_delta": [0.0, 0.0],
        "wilcoxon_stat": None,
        "wilcoxon_p": None,
        "max_20trade_dd_r": 0.0,
    }

    # Write outputs
    # variants_comparison.csv
    fields = [
        "variant", "n", "triggered", "triggered_pct", "exact_via_r_path",
        "hurt_count", "hurt_pct_of_triggered",
        "wr_variant", "wr_baseline", "wr_wilson95",
        "mean_r_variant", "mean_r_baseline", "mean_delta_r", "delta_sd",
        "total_r_variant", "total_r_baseline", "total_delta_r",
        "bootstrap_ci95_mean_delta", "wilcoxon_stat", "wilcoxon_p",
        "max_20trade_dd_r",
    ]
    with open(OUT_DIR / "variants_comparison.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fields)
        # baseline first
        row = {"variant": "V0_baseline", **baseline_row}
        w.writerow([row[k] for k in fields])
        for vname, s in variant_stats.items():
            row = {"variant": vname, **s}
            w.writerow([row[k] for k in fields])

    with open(OUT_DIR / "variants_comparison.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "baseline": {"V0_baseline": baseline_row},
                "variants": variant_stats,
            },
            f,
            indent=2,
        )

    # per-trade audit
    with open(OUT_DIR / "per_trade_outcomes.jsonl", "w", encoding="utf-8") as f:
        for row in per_trade_rows:
            f.write(json.dumps(row) + "\n")

    # metadata
    meta = {
        "run_utc": "2026-04-19",
        "universe_total": total,
        "valid_trades": len(valid),
        "dropped_missing_fields": dropped,
        "r_path_carriers": sum(1 for t in valid if t.get("r_path")),
        "symbol_breakdown": dict(Counter(t.get("symbol") for t in valid)),
        "framework_breakdown": dict(Counter(t.get("framework") for t in valid)),
        "variants_tested": list(VARIANTS.keys()),
        "boot_seed": BOOT_SEED,
        "boot_n": BOOT_N,
        "bonferroni_alpha": 0.05 / len(VARIANTS),
        "notes": [
            "Merged universe de-dups batch_api + unified_v2 + phase1 (same rule as q62, q65).",
            "336 unique after dedup vs CLAUDE.md 'canonical 367'. 367 is stale; 336 is the current dedup'd batch KB.",
            "Per-bar OHLC not available for 95% of trades. Approximation: trail exit = peak - trail_r, floored at baseline when baseline > trail_exit. See PRE_REGISTRATION.md.",
            "r_path available for 18 trades -> exact simulation on that subset.",
            "Symbol recovered from batch_api/*_full_prompts.json (one batch = one instrument). 1 batch (msgbatch_016WB5a5VNzuK7ibgz6uSD93) could not be attributed -> UNKNOWN.",
        ],
    }
    with open(OUT_DIR / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # console preview
    print("=" * 80)
    print("VARIANT COMPARISON (sorted by mean_delta_r desc)")
    print("=" * 80)
    sorted_v = sorted(variant_stats.items(), key=lambda x: x[1]["mean_delta_r"], reverse=True)
    for vname, s in sorted_v:
        print(
            f"{vname:22s}  dR/trade={s['mean_delta_r']:+.4f}  "
            f"totdR={s['total_delta_r']:+.2f}  "
            f"triggered={s['triggered']}/{s['n']} ({s['triggered_pct']}%)  "
            f"hurt={s['hurt_count']} ({s['hurt_pct_of_triggered']}% of trig)  "
            f"p={s['wilcoxon_p']}  "
            f"bootCI=[{s['bootstrap_ci95_mean_delta'][0]:+.3f}, {s['bootstrap_ci95_mean_delta'][1]:+.3f}]  "
            f"max20-DD={s['max_20trade_dd_r']:+.2f}"
        )
    print(
        f"{'V0_baseline':22s}  mean R/trade={baseline_row['mean_r_baseline']:+.4f}  "
        f"total R={baseline_row['total_r_baseline']:+.2f}  "
        f"WR={baseline_row['wr_baseline']:.3f} "
        f"Wilson95=[{baseline_row['wr_wilson95'][0]:.3f}, {baseline_row['wr_wilson95'][1]:.3f}]"
    )
    print()
    print(f"Outputs written to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
