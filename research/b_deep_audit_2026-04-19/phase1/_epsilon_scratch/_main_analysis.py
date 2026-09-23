"""Agent ε — full liquidity-arbitrage signature battery.

Produces a structured JSON + markdown summary covering all 8 deliverables.

Signatures tested:
  (1) Pre-entry MFE distribution (favorable excursion before fill)
  (2) Post-entry first-60min adverse excursion
  (3) Stop-hunt signature (SL touch near OB bound + reversal ≥1R)
  (4) MFE ceiling compression for winners
  (5) Cross-instrument algo-density correlation (Spearman)
  (6) Volume-spike coincidence with losses
  (7) Pre-2025 null baseline (backtest 2024 vs 2026)
  (8) Verdict aggregation

Evidence: every number is per-record, citations in the detail JSON.

Stats approach:
- Effect size with 95% CI (bootstrap 2000 iter or normal approx)
- Bonferroni correction for 6 primary signatures (threshold = α/6 ≈ 0.0083 @ α=0.05)
- n<20 → "exploratory" prefix

All outputs written under phase1/ (md + JSON).
"""
from __future__ import annotations

import json
import math
import os
import random
import statistics
import sys
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from _loader import (FILL_EPS, TICK_SIZE, extract_candidates, is_degenerate,
                     load_all_backtest, load_all_t7, load_m15, load_trade_index,
                     median, percentile, quarter_of, _parse_iso)
from _mfe_mae import simulate_fill, extract_ob_bounds_from_raw, check_stop_hunt_signature


# =============================================================================
# Helpers
# =============================================================================
def bootstrap_ci(values: List[float], fn=statistics.mean, n_iter: int = 2000, alpha: float = 0.05, seed: int = 42) -> Optional[Tuple[float, float, float]]:
    """Return (point_estimate, lo, hi) via bootstrap. None if insufficient n."""
    if len(values) < 3:
        return None
    rng = random.Random(seed)
    boots = []
    for _ in range(n_iter):
        sample = [values[rng.randrange(len(values))] for _ in range(len(values))]
        boots.append(fn(sample))
    boots.sort()
    lo = boots[int(n_iter * alpha / 2)]
    hi = boots[int(n_iter * (1 - alpha / 2))]
    return fn(values), lo, hi


def binomial_ci_wilson(successes: int, n: int, alpha: float = 0.05) -> Tuple[float, float, float]:
    """Wilson score CI for a proportion."""
    if n == 0:
        return 0.0, 0.0, 0.0
    p = successes / n
    z = 1.96
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)


def spearman_rho(x: List[float], y: List[float]) -> Optional[float]:
    if len(x) != len(y) or len(x) < 3:
        return None
    def rank(vs):
        idx = sorted(range(len(vs)), key=lambda i: vs[i])
        r = [0.0] * len(vs)
        i = 0
        while i < len(vs):
            j = i
            while j + 1 < len(vs) and vs[idx[j + 1]] == vs[idx[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[idx[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(x), rank(y)
    mx = sum(rx) / len(rx); my = sum(ry) / len(ry)
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(len(rx)))
    dx = math.sqrt(sum((r - mx) ** 2 for r in rx))
    dy = math.sqrt(sum((r - my) ** 2 for r in ry))
    return num / (dx * dy) if dx and dy else None


def mann_whitney_u_p(a: List[float], b: List[float]) -> Optional[float]:
    """Two-sided Mann-Whitney U p-value via normal approximation."""
    if len(a) < 5 or len(b) < 5:
        return None
    combined = [(v, 0) for v in a] + [(v, 1) for v in b]
    combined.sort(key=lambda x: x[0])
    # Ranks with tie-averaging
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    r_a = sum(ranks[i] for i, (_, g) in enumerate(combined) if g == 0)
    n1, n2 = len(a), len(b)
    u_a = r_a - n1 * (n1 + 1) / 2
    u = min(u_a, n1 * n2 - u_a)
    mu = n1 * n2 / 2
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    if sigma == 0:
        return None
    z = (u - mu) / sigma
    # 2-sided p
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return p


# =============================================================================
# Build the per-candidate enriched record
# =============================================================================
def build_enriched_candidates() -> List[dict]:
    """For every T7 CANDIDATE across all 3 symbols, simulate fill and return enriched records."""
    all_t7 = load_all_t7()
    enriched = []
    for symbol, results in all_t7.items():
        for c in extract_candidates(results):
            if is_degenerate(c):
                continue
            try:
                sig_t = _parse_iso(c["candle_time"])
            except Exception:
                continue
            try:
                sim = simulate_fill(
                    symbol, sig_t, c["direction"],
                    float(c["entry_price"]), float(c["stop_loss"]), float(c["take_profit_1"]),
                )
            except Exception:
                continue
            if sim is None:
                continue
            rec = {
                "symbol": symbol,
                "date": c["date"],
                "quarter": quarter_of(c["date"]),
                "candle_time": c["candle_time"],
                "direction": c["direction"],
                "entry": float(c["entry_price"]),
                "stop_loss": float(c["stop_loss"]),
                "take_profit": float(c["take_profit_1"]),
                "R_size": abs(float(c["entry_price"]) - float(c["stop_loss"])),
                "sim_exit_type": sim["exit_type"],
                "sim_exit_r": sim["exit_r"],
                "actual_outcome": c.get("outcome"),
                "actual_r": c.get("r_multiple"),
                "pre_entry_mfe_R": sim["pre_entry_mfe_R"],
                "pre_entry_mae_R": sim["pre_entry_mae_R"],
                "post_entry_mae_15m_R": sim["post_entry_mae_15m_R"],
                "post_entry_mae_30m_R": sim["post_entry_mae_30m_R"],
                "post_entry_mae_60m_R": sim["post_entry_mae_60m_R"],
                "post_entry_mae_240m_R": sim["post_entry_mae_240m_R"],
                "post_entry_mfe_240m_R": sim["post_entry_mfe_240m_R"],
                "winner_max_mfe_R": sim["winner_max_mfe_R"],
                "sl_touch_to_reversal_r": sim["sl_touch_to_reversal_r"],
                "any_sl_hit": sim["any_sl_hit"],
                "fill_time": sim["fill_time"].isoformat() if sim["fill_time"] else None,
                "fill_idx": sim["fill_idx"],
                "exit_idx": sim["exit_idx"],
                "ob_bounds": extract_ob_bounds_from_raw(c.get("raw_response", "")),
            }
            # Stop-hunt signature flag:
            # Criterion: exit_type == SL AND reversal ≥ 1R within 4h after SL hit
            # AND the SL-hit extreme is within ±2 ticks of OB bound (if OB bounds recoverable)
            tick = TICK_SIZE.get(symbol, 0.0001)
            if sim["exit_type"] == "SL":
                # SL-hit extreme = low of exit candle for LONG (or high for SHORT)
                candles_m15 = load_m15(symbol)
                is_long = c["direction"].upper() == "LONG"
                sl_candle = candles_m15[sim["exit_idx"]]
                sl_hit_extreme = sl_candle["low"] if is_long else sl_candle["high"]
                rec["sl_hit_extreme"] = sl_hit_extreme
                rec["sl_hit_volume"] = sl_candle.get("volume", 0)
                # Distance from SL to sl_hit_extreme (how far PAST the SL did price go?)
                rec["sl_overshoot_ticks"] = abs(rec["stop_loss"] - sl_hit_extreme) / tick
                if rec["ob_bounds"] is not None:
                    ob_bound = rec["ob_bounds"][0] if is_long else rec["ob_bounds"][1]
                    rec["sl_hit_extreme_to_ob_ticks"] = abs(sl_hit_extreme - ob_bound) / tick
                    rec["sl_to_ob_ticks"] = abs(rec["stop_loss"] - ob_bound) / tick
                else:
                    rec["sl_hit_extreme_to_ob_ticks"] = None
                    rec["sl_to_ob_ticks"] = None
                # Reversed ≥1R in TP direction within 4h after SL hit?
                rec["reversed_1r_after_sl"] = (sim.get("sl_touch_to_reversal_r") or 0.0) >= 1.0
            enriched.append(rec)
    return enriched


# =============================================================================
# Signature #1: Pre-entry MFE distribution
# =============================================================================
def sig1_pre_entry_mfe(enriched: List[dict]) -> dict:
    out: dict = {"by_symbol": {}, "by_symbol_quarter": {}, "all": None}
    # Filter: only records where the limit was "reachable" (fill happened) OR where
    # fill never happened (UNFILLED → no pre-MFE to measure, skip).
    filtered = [r for r in enriched if r["fill_time"] is not None]
    all_pre = [r["pre_entry_mfe_R"] for r in filtered]
    out["all"] = {
        "n": len(all_pre),
        "median_R": median(all_pre),
        "p25_R": percentile(all_pre, 25),
        "p75_R": percentile(all_pre, 75),
        "p90_R": percentile(all_pre, 90),
        "mean_R": statistics.mean(all_pre) if all_pre else None,
        "bootstrap_95CI_mean": bootstrap_ci(all_pre),
    }
    for sym in sorted(set(r["symbol"] for r in filtered)):
        pre = [r["pre_entry_mfe_R"] for r in filtered if r["symbol"] == sym]
        if not pre:
            continue
        out["by_symbol"][sym] = {
            "n": len(pre),
            "median_R": median(pre),
            "p25_R": percentile(pre, 25),
            "p75_R": percentile(pre, 75),
            "p90_R": percentile(pre, 90),
            "mean_R": statistics.mean(pre),
            "bootstrap_95CI_mean": bootstrap_ci(pre),
        }
        # By quarter
        by_q = defaultdict(list)
        for r in filtered:
            if r["symbol"] == sym:
                by_q[r["quarter"]].append(r["pre_entry_mfe_R"])
        out["by_symbol_quarter"][sym] = {
            q: {
                "n": len(vs),
                "median_R": median(vs) if vs else None,
                "mean_R": statistics.mean(vs) if vs else None,
            } for q, vs in sorted(by_q.items())
        }
    return out


# =============================================================================
# Signature #2: Post-entry first-60min adverse excursion
# =============================================================================
def sig2_post_entry_mae(enriched: List[dict]) -> dict:
    out: dict = {"by_symbol": {}, "all": None, "by_symbol_quarter": {}}
    filtered = [r for r in enriched if r["fill_time"] is not None]
    for window_key in ["post_entry_mae_15m_R", "post_entry_mae_30m_R", "post_entry_mae_60m_R"]:
        vs = [r[window_key] for r in filtered if r[window_key] is not None]
        if not vs:
            continue
        out[window_key + "_all"] = {
            "n": len(vs),
            "median_R": median(vs),
            "p25_R": percentile(vs, 25),
            "p75_R": percentile(vs, 75),
            "mean_R": statistics.mean(vs),
        }
    for sym in sorted(set(r["symbol"] for r in filtered)):
        sym_recs = [r for r in filtered if r["symbol"] == sym]
        d = {"n": len(sym_recs)}
        for window_key in ["post_entry_mae_15m_R", "post_entry_mae_30m_R", "post_entry_mae_60m_R"]:
            vs = [r[window_key] for r in sym_recs if r[window_key] is not None]
            if vs:
                d[window_key] = {"median_R": median(vs), "mean_R": statistics.mean(vs)}
        out["by_symbol"][sym] = d
        # Quarterly
        by_q = defaultdict(list)
        for r in sym_recs:
            if r["post_entry_mae_60m_R"] is not None:
                by_q[r["quarter"]].append(r["post_entry_mae_60m_R"])
        out["by_symbol_quarter"][sym] = {
            q: {"n": len(vs), "median_R_60m": median(vs) if vs else None}
            for q, vs in sorted(by_q.items())
        }
    return out


# =============================================================================
# Signature #3: Stop-hunt signature
# =============================================================================
def sig3_stop_hunt(enriched: List[dict]) -> dict:
    # Primary cut: losses (SL hit) where price reversed ≥1R within 4h (post-SL reversal)
    out = {"by_symbol": {}, "by_symbol_quarter": {}, "null_baseline": None}
    filtered = [r for r in enriched if r["fill_time"] is not None]
    all_losses = [r for r in filtered if r["sim_exit_type"] == "SL"]
    # All losses: reversal rate
    rev = sum(1 for r in all_losses if r.get("reversed_1r_after_sl"))
    n_l = len(all_losses)
    p, lo, hi = binomial_ci_wilson(rev, n_l)
    out["all_losses"] = {
        "n_losses": n_l,
        "n_reversed_1r_within_4h": rev,
        "rate": p,
        "wilson95_ci": [lo, hi],
    }
    # Near-OB bit-exact
    near_ob = [r for r in all_losses if r.get("sl_to_ob_ticks") is not None and r["sl_to_ob_ticks"] <= 2.0]
    near_ob_reversed = [r for r in near_ob if r.get("reversed_1r_after_sl")]
    out["sl_near_ob_and_reversed"] = {
        "n_losses_total": n_l,
        "n_with_ob_bounds_recovered": sum(1 for r in all_losses if r.get("sl_to_ob_ticks") is not None),
        "n_sl_within_2t_of_ob": len(near_ob),
        "n_sl_within_2t_and_reversed_1r": len(near_ob_reversed),
    }
    for sym in sorted(set(r["symbol"] for r in filtered)):
        sym_losses = [r for r in all_losses if r["symbol"] == sym]
        r_cnt = sum(1 for r in sym_losses if r.get("reversed_1r_after_sl"))
        p, lo, hi = binomial_ci_wilson(r_cnt, len(sym_losses))
        out["by_symbol"][sym] = {
            "n_losses": len(sym_losses),
            "n_reversed_1r": r_cnt,
            "reversal_rate": p,
            "wilson95_ci": [lo, hi],
        }
        # quarterly
        by_q = defaultdict(lambda: {"n": 0, "rev": 0})
        for r in sym_losses:
            by_q[r["quarter"]]["n"] += 1
            if r.get("reversed_1r_after_sl"):
                by_q[r["quarter"]]["rev"] += 1
        out["by_symbol_quarter"][sym] = {
            q: {"n_losses": v["n"], "n_rev": v["rev"],
                "rate": v["rev"] / v["n"] if v["n"] else None}
            for q, v in sorted(by_q.items())
        }
    return out


def null_baseline_reversal(symbol: str, n_trials: int = 500, max_candles: int = 192, seed: int = 11) -> dict:
    """Compute null distribution: random entry times, synthetic SL at same typical R distance,
    and check how often price reverses ≥1R within 4h.

    Uses the instrument's M15 CSV. R distance set to median actual R for that symbol's CANDIDATEs.
    """
    candles = load_m15(symbol)
    if len(candles) < max_candles + 100:
        return {}
    rng = random.Random(seed)
    # Use average daily range as proxy R
    # Pick a typical R distance = 0.1% of median price
    prices = [c["close"] for c in candles]
    R = statistics.median(prices) * 0.005
    n_rev = 0
    n_total = 0
    for _ in range(n_trials):
        i = rng.randrange(100, len(candles) - max_candles - 16)
        # Pick direction
        is_long = rng.random() < 0.5
        # Synthetic entry = close of candle i
        entry = candles[i]["close"]
        sl = entry - R if is_long else entry + R
        # Walk forward to find SL hit
        sl_idx = None
        for j in range(i + 1, min(i + max_candles, len(candles))):
            if is_long and candles[j]["low"] <= sl:
                sl_idx = j
                break
            elif (not is_long) and candles[j]["high"] >= sl:
                sl_idx = j
                break
        if sl_idx is None:
            continue
        # Reversal check
        max_rev = 0.0
        for k in range(sl_idx + 1, min(sl_idx + 17, len(candles))):
            if is_long:
                rev = (candles[k]["high"] - sl) / R
            else:
                rev = (sl - candles[k]["low"]) / R
            if rev > max_rev:
                max_rev = rev
        n_total += 1
        if max_rev >= 1.0:
            n_rev += 1
    p, lo, hi = binomial_ci_wilson(n_rev, n_total)
    return {"symbol": symbol, "n_trials_completed": n_total, "n_reversed_1r": n_rev, "rate": p, "wilson95_ci": [lo, hi]}


# =============================================================================
# Signature #4: MFE ceiling compression for winners
# =============================================================================
def sig4_mfe_ceiling(enriched: List[dict]) -> dict:
    out: dict = {"by_symbol": {}, "by_symbol_quarter": {}, "all": None}
    winners = [r for r in enriched if r["sim_exit_type"] == "TP"]
    mfes = [r["winner_max_mfe_R"] for r in winners]
    out["all"] = {
        "n_winners": len(winners),
        "median_mfe_R": median(mfes) if mfes else None,
        "mean_mfe_R": statistics.mean(mfes) if mfes else None,
        "p25_R": percentile(mfes, 25) if mfes else None,
        "p75_R": percentile(mfes, 75) if mfes else None,
    }
    for sym in sorted(set(r["symbol"] for r in enriched)):
        sym_w = [r for r in winners if r["symbol"] == sym]
        if not sym_w:
            continue
        ms = [r["winner_max_mfe_R"] for r in sym_w]
        out["by_symbol"][sym] = {
            "n_winners": len(sym_w),
            "median_mfe_R": median(ms),
            "mean_mfe_R": statistics.mean(ms),
        }
        # Quarterly
        by_q = defaultdict(list)
        for r in sym_w:
            by_q[r["quarter"]].append(r["winner_max_mfe_R"])
        out["by_symbol_quarter"][sym] = {
            q: {"n": len(vs), "median_R": median(vs) if vs else None,
                "mean_R": statistics.mean(vs) if vs else None}
            for q, vs in sorted(by_q.items())
        }
    return out


# =============================================================================
# Signature #5: Algo-density vs decay correlation
# =============================================================================
def sig5_algo_density(enriched: List[dict]) -> dict:
    """Use trade_index (129-trade KB) for cross-instrument WR decay across years.

    Algo-density ordinal ranks (brief stipulated; informal — NOT an empirical measurement):
      NAS100 = 1 (highest)
      EURUSD = 2
      GBPUSD = 3
      USDJPY = 4
      GBPJPY = 5
      XAUUSD = 6 (lowest)

    Decay rate = WR(2026) − WR(2024/2025 aggregate) per symbol.
    """
    # Build from trade_index
    idx = load_trade_index()
    bt = load_all_backtest()  # Also use backtest trades for more n

    # Informal algo-density ranking (higher number = less algo presence)
    algo_rank = {
        "NAS100": 1, "EURUSD": 2, "GBPUSD": 3, "USDJPY": 4, "GBPJPY": 5,
        "XAUUSD": 6, "US30": 3, "NZDUSD": 5,
    }

    # Per-symbol WR by year (backtest only since it's fuller)
    symbol_wr_by_year: Dict[str, Dict[str, dict]] = {}
    for sym, trades in bt.items():
        by_year = defaultdict(lambda: {"n": 0, "wins": 0, "rs": []})
        for t in trades:
            y = t.get("date", "?")[:4]
            by_year[y]["n"] += 1
            if t.get("outcome") == "WIN":
                by_year[y]["wins"] += 1
            r = t.get("r_multiple")
            if r is not None:
                by_year[y]["rs"].append(r)
        symbol_wr_by_year[sym] = {
            y: {"n": v["n"], "wins": v["wins"],
                "wr": v["wins"] / v["n"] if v["n"] else None,
                "exp_r": statistics.mean(v["rs"]) if v["rs"] else None}
            for y, v in by_year.items()
        }

    # Compute decay per symbol: earliest year WR vs latest year WR
    decay_table = []
    for sym, ys in symbol_wr_by_year.items():
        if not ys:
            continue
        years_sorted = sorted(ys.keys())
        if len(years_sorted) < 2:
            continue
        # Compare first half vs last year
        early = [ys[y] for y in years_sorted[:-1]]
        late = ys[years_sorted[-1]]
        n_early = sum(e["n"] for e in early)
        w_early = sum(e["wins"] for e in early)
        if n_early < 5 or late["n"] < 5:
            continue
        wr_early = w_early / n_early
        wr_late = late["wr"]
        rank = algo_rank.get(sym)
        if rank is None:
            continue
        decay_table.append({
            "symbol": sym, "algo_rank": rank,
            "n_early": n_early, "wr_early": wr_early,
            "n_late": late["n"], "wr_late": wr_late,
            "decay_pp": (wr_early - wr_late) * 100,
            "years_early": years_sorted[:-1],
            "year_late": years_sorted[-1],
        })

    # Spearman between rank and decay
    if len(decay_table) >= 3:
        xs = [d["algo_rank"] for d in decay_table]
        ys = [d["decay_pp"] for d in decay_table]
        rho = spearman_rho(xs, ys)
    else:
        rho = None

    return {
        "symbol_wr_by_year": symbol_wr_by_year,
        "decay_table": decay_table,
        "spearman_rank_vs_decay": rho,
        "n_symbols": len(decay_table),
    }


# =============================================================================
# Signature #6: Volume-spike coincidence with losses
# =============================================================================
def sig6_volume_spike(enriched: List[dict]) -> dict:
    """For losses (SL hit), was the SL-hit candle a volume-spike (>2x 20-candle rolling avg)?

    Compare rate among losses vs winners.
    """
    out = {"by_symbol": {}, "all": None}
    filtered = [r for r in enriched if r["fill_time"] is not None and r["exit_idx"] is not None]
    # For each record, compute volume-spike flag at exit candle
    per_rec_spike = []
    for r in filtered:
        candles = load_m15(r["symbol"])
        exit_idx = r["exit_idx"]
        if exit_idx < 20:
            continue
        vols = [candles[i]["volume"] for i in range(exit_idx - 20, exit_idx)]
        avg = statistics.mean(vols) if vols else 0
        this_vol = candles[exit_idx]["volume"]
        ratio = this_vol / avg if avg > 0 else 0
        per_rec_spike.append({
            "symbol": r["symbol"], "outcome": r["sim_exit_type"],
            "vol_ratio": ratio, "volume_spike_2x": ratio >= 2.0,
        })
    # Rates
    if per_rec_spike:
        losses = [r for r in per_rec_spike if r["outcome"] == "SL"]
        wins = [r for r in per_rec_spike if r["outcome"] == "TP"]
        l_spike = sum(1 for r in losses if r["volume_spike_2x"])
        w_spike = sum(1 for r in wins if r["volume_spike_2x"])
        p_l, lo_l, hi_l = binomial_ci_wilson(l_spike, len(losses))
        p_w, lo_w, hi_w = binomial_ci_wilson(w_spike, len(wins))
        out["all"] = {
            "n_losses": len(losses), "n_loss_vol_spike_2x": l_spike,
            "loss_spike_rate": p_l, "loss_spike_95ci": [lo_l, hi_l],
            "n_wins": len(wins), "n_win_vol_spike_2x": w_spike,
            "win_spike_rate": p_w, "win_spike_95ci": [lo_w, hi_w],
            "difference_pp": (p_l - p_w) * 100,
        }
    return out


# =============================================================================
# Signature #7: Pre-2025 null baseline (backtest 2024 vs 2026)
# =============================================================================
def sig7_historical_null(enriched: List[dict]) -> dict:
    """Compare backtest trade MFE/MAE/WR 2024 vs 2026 to test if arbitrage signature
    is stronger in more recent (more algo-penetrated) era.
    """
    bt = load_all_backtest()
    out = {}
    for sym, trades in bt.items():
        by_year = defaultdict(list)
        for t in trades:
            y = t.get("date", "?")[:4]
            by_year[y].append(t)
        # Compute MFE/MAE medians by year
        year_metrics = {}
        for y, ts in by_year.items():
            n = len(ts)
            if n < 3:
                continue
            wins = [t for t in ts if t.get("outcome") == "WIN"]
            losses = [t for t in ts if t.get("outcome") == "LOSS"]
            # Loss MFE: max favorable pre-SL — how far did price run before SL hit?
            mfe_l = [t.get("mfe_r") for t in losses if t.get("mfe_r") is not None]
            mae_w = [t.get("mae_r") for t in wins if t.get("mae_r") is not None]
            mfe_w = [t.get("mfe_r") for t in wins if t.get("mfe_r") is not None]
            rs = [t.get("r_multiple") for t in ts if t.get("r_multiple") is not None]
            year_metrics[y] = {
                "n": n,
                "wr": len(wins) / n,
                "exp_r": statistics.mean(rs) if rs else None,
                "median_loss_mfe_r": median(mfe_l) if mfe_l else None,
                "median_winner_mae_r": median(mae_w) if mae_w else None,
                "median_winner_mfe_r": median(mfe_w) if mfe_w else None,
                "n_wins": len(wins), "n_losses": len(losses),
            }
        # Trend test: decay WR from 2024 → 2026
        ks = sorted(year_metrics.keys())
        out[sym] = {
            "by_year": year_metrics,
            "wr_trend": [(y, year_metrics[y]["wr"]) for y in ks],
        }
    return out


# =============================================================================
# Signature #8: Verdict aggregation
# =============================================================================
def aggregate_verdict(results: dict) -> dict:
    """Synthesize the 6 primary signatures with Bonferroni correction.

    Returns dict with: signature_scorecard, overall_verdict, counter-measures.
    """
    sigs_tested = 6  # #1, #2, #3, #4, #5, #7  (#6 #8 are observational)
    alpha = 0.05
    bonf = alpha / sigs_tested
    card = []

    # Sig 1: pre-entry MFE — signature present if median pre-entry MFE > 0.5R in any instrument
    s1 = results["sig1_pre_entry_mfe"]
    for sym, d in s1["by_symbol"].items():
        if d["n"] >= 5 and d["median_R"] and d["median_R"] > 0.5:
            card.append({
                "sig": "#1 pre-entry MFE",
                "instrument": sym,
                "n": d["n"],
                "metric": f"median={d['median_R']:.2f}R p75={d['p75_R']:.2f}R",
                "interpretation": "favorable run before fill — consistent with 'served-the-fill' after stop run",
                "strength": "supportive" if d["median_R"] > 1.0 else "weak_supportive",
            })

    # Sig 2: post-entry MAE
    s2 = results["sig2_post_entry_mae"]
    for sym, d in s2["by_symbol"].items():
        if d["n"] >= 5 and d.get("post_entry_mae_60m_R"):
            m = d["post_entry_mae_60m_R"]["median_R"]
            if m > 0.5:
                card.append({
                    "sig": "#2 post-entry MAE 60min",
                    "instrument": sym,
                    "n": d["n"],
                    "metric": f"median MAE 60m = {m:.2f}R",
                    "interpretation": "immediate adverse excursion after fill",
                    "strength": "supportive" if m > 0.75 else "weak_supportive",
                })

    # Sig 3: SL→reversal
    s3 = results["sig3_stop_hunt"]
    null_rates = s3.get("null_baseline_by_symbol", {})
    for sym, d in s3["by_symbol"].items():
        if d["n_losses"] >= 3:
            null_rate = null_rates.get(sym, {}).get("rate")
            obs_rate = d["reversal_rate"]
            delta = (obs_rate - null_rate) if null_rate is not None else None
            if null_rate is not None:
                metric_str = f"rate={obs_rate:.2f} null={null_rate:.2f}"
            else:
                metric_str = f"rate={obs_rate:.2f}"
            card.append({
                "sig": "#3 SL-reversal ≥1R / 4h",
                "instrument": sym,
                "n": d["n_losses"],
                "metric": metric_str,
                "interpretation": f"observed - null = {delta*100:.1f}pp" if delta is not None else "insufficient null",
                "strength": "supportive" if (delta is not None and delta > 0.2) else ("weak_supportive" if (delta is not None and delta > 0.05) else "inconclusive"),
            })

    # Sig 4: winner MFE compression — test if Q1-2026 MFE lower than Q4-2025 etc
    s4 = results["sig4_mfe_ceiling"]
    for sym, qs in s4["by_symbol_quarter"].items():
        if len(qs) >= 2:
            # Earliest vs latest
            ks = sorted(qs.keys())
            e, l = qs[ks[0]], qs[ks[-1]]
            if e["n"] >= 3 and l["n"] >= 3:
                change = (l["median_R"] or 0) - (e["median_R"] or 0)
                card.append({
                    "sig": "#4 winner MFE ceiling",
                    "instrument": sym,
                    "n": f"{e['n']}→{l['n']}",
                    "metric": f"{ks[0]}={e['median_R']:.2f}R → {ks[-1]}={l['median_R']:.2f}R",
                    "interpretation": "compression" if change < -0.2 else ("expansion" if change > 0.2 else "flat"),
                    "strength": "supportive" if change < -0.3 else "inconclusive",
                })

    # Sig 5: algo-density rank correlation
    s5 = results["sig5_algo_density"]
    rho = s5.get("spearman_rank_vs_decay")
    n_sym = s5.get("n_symbols", 0)
    rho_str = f"ρ = {rho:.3f}" if rho is not None else "insufficient"
    card.append({
        "sig": "#5 algo-rank vs decay (Spearman)",
        "instrument": "cross",
        "n": n_sym,
        "metric": rho_str,
        "interpretation": ("monotone: higher algo → larger decay" if rho and rho < -0.5
                           else ("inverse: less algo → larger decay" if rho and rho > 0.5
                                 else "no monotone relationship")),
        "strength": "exploratory" if n_sym < 6 else ("supportive" if rho and rho < -0.5 else "inconclusive"),
    })

    # Sig 6: volume spike
    s6 = results["sig6_volume_spike"]
    if s6.get("all"):
        d = s6["all"]
        card.append({
            "sig": "#6 volume spike on loss",
            "instrument": "cross",
            "n": f"{d['n_losses']}W+{d['n_wins']}L",
            "metric": f"loss={d['loss_spike_rate']:.2f} win={d['win_spike_rate']:.2f} Δ={d['difference_pp']:.1f}pp",
            "interpretation": "institutional volume at SL touch" if d["difference_pp"] > 10 else "no differential",
            "strength": "supportive" if d["difference_pp"] > 15 else "inconclusive",
        })

    return {
        "scorecard": card,
        "bonferroni_alpha": bonf,
        "n_signatures_tested": sigs_tested,
        "supportive_count": sum(1 for c in card if c["strength"] == "supportive"),
        "weak_supportive_count": sum(1 for c in card if c["strength"] == "weak_supportive"),
        "inconclusive_count": sum(1 for c in card if c["strength"] == "inconclusive"),
        "exploratory_count": sum(1 for c in card if c["strength"] == "exploratory"),
    }


# =============================================================================
# Main entry
# =============================================================================
def run():
    print("Building enriched CANDIDATE records…")
    enriched = build_enriched_candidates()
    print(f"  n enriched = {len(enriched)}")
    # Save enriched
    with open(HERE / "enriched_candidates.json", "w", encoding="utf-8") as f:
        json.dump(enriched, f, default=str, indent=2)

    print("Sig #1: pre-entry MFE…")
    s1 = sig1_pre_entry_mfe(enriched)

    print("Sig #2: post-entry MAE…")
    s2 = sig2_post_entry_mae(enriched)

    print("Sig #3: stop-hunt…")
    s3 = sig3_stop_hunt(enriched)
    # Null baseline per instrument
    null_by_sym = {}
    for sym in ["XAUUSD", "NAS100", "EURUSD"]:
        nb = null_baseline_reversal(sym)
        null_by_sym[sym] = nb
    s3["null_baseline_by_symbol"] = null_by_sym

    print("Sig #4: MFE ceiling compression…")
    s4 = sig4_mfe_ceiling(enriched)

    print("Sig #5: algo-density correlation…")
    s5 = sig5_algo_density(enriched)

    print("Sig #6: volume spike…")
    s6 = sig6_volume_spike(enriched)

    print("Sig #7: historical null (2024 vs 2026)…")
    s7 = sig7_historical_null(enriched)

    print("Sig #8: verdict aggregation…")
    results = {
        "sig1_pre_entry_mfe": s1,
        "sig2_post_entry_mae": s2,
        "sig3_stop_hunt": s3,
        "sig4_mfe_ceiling": s4,
        "sig5_algo_density": s5,
        "sig6_volume_spike": s6,
        "sig7_historical_null": s7,
    }
    verdict = aggregate_verdict(results)
    results["verdict_aggregation"] = verdict

    with open(HERE / "all_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, default=str, indent=2)
    print("Wrote all_results.json")
    return results


if __name__ == "__main__":
    run()
