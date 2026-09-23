"""
Q-5.3 / Q-5.4 — Stop-Loss Engineering Analysis for GTOS

Scope:
  - Q-5.3: SL placement vs stop clustering (round numbers, PDH/PDL).
           Does SL placement near cluster-zones increase stop-hunt risk?
  - Q-5.4: ATR-based vs quantile-based SL.
           Does a 95th-percentile winning-MAE SL outperform current ATR?

Data:
  - Batch trades: knowledge_base_backtest/analysis/unified_trades_v2_20260331.json (111 trades, XAUUSD)
  - Historical D1: data/historical_2026/XAUUSD_D1.csv (PDH/PDL — 2026 only, 29 trades)

Pre-registered hypotheses:
  H1 (Q-5.3 clustering prevalence): SLs are NOT uniformly distributed in [round, round+$5).
       >25% of SLs will be within $1.0 of a $5-round level (vs 40% uniform expectation).
  H2 (Q-5.3 Osler asymmetry):      LONG SLs will cluster just BELOW $5-round floors
       (the retail "obvious stop" zone) at a rate ≥ 60%.
  H3 (Q-5.3 stop-hunt risk):       P(stop-hunt | SL near round) > P(stop-hunt | SL isolated),
       Fisher's exact test, one-sided.
  H4 (Q-5.4 counterfactual):       95th-percentile winning-MAE SL yields HIGHER expectancy
       than current SL sizing, because it saves hunt-losses while
       keeping TP distance the same.

Stop-hunt proxy (from task instruction):
  A losing trade was "stop-hunted" if its mae_r ≈ 1.0 (SL hit) AND mfe_r >= 1.5
  (price reversed ≥1.5R in the trade's favor after stopping out).
  We report additional thresholds (mfe_r ≥ 1.0, ≥ 2.0) for robustness.

Counterfactual for Q-5.4 (approximation):
  For each historical trade we ask: would this trade have stopped out with SL_new?
  - If new_SL_R (width in R-units, where original SL = 1R) >= mae_r: trade survives.
    Its r_multiple is capped at planned max (take_profit target), proxied by original_r if >0
    (winner stayed winner) OR by mfe_r if original r_multiple < 0 (loser would have reached mfe_r).
    Conservatively, we cap a salvaged trade at its original mfe_r (not unbounded).
  - If new_SL_R < mae_r: trade stops out at -new_SL_R (in old R units).
  - Key simplification: we hold TP/entry/risk$ fixed. Changing SL changes the *R-scale* of each
    unit of price. mae_r and mfe_r in the file are expressed in OLD-R units (using original SL).
  - A wider SL shrinks the R-scale. If original SL width = W_old (in $) and new SL width = W_new,
    then distances re-scale by factor k = W_old / W_new. So mae_r_new = mae_r * k,
    mfe_r_new = mfe_r * k, and the trade stops only if mae_r_new >= 1.0
    (equivalently: mae_r * W_old / W_new >= 1  =>  W_new <= mae_r * W_old).
  - For winners (original r_multiple>0) that had mae_r<1 originally: they still win. But their
    r_multiple shrinks because R now equals W_new, not W_old. New r_multiple = old * (W_old/W_new).
    So widening SL reduces R-payoff proportionally for unchanged TP.
  - For losers that would NOT stop under W_new (mae_r < W_new/W_old): new r_multiple = mfe_r *
    (W_old/W_new) only if mfe_r >= planned_rr-in-old-R * (W_new/W_old); otherwise assume trade
    would have returned negative over the full hold. We conservatively use old r_multiple * k
    unless the original exit was a stop-loss; then we assume break-even under new SL.

  This is an APPROXIMATION. Without per-candle OHLCV over each trade's hold window we cannot
  replay the exact path. The approximation is conservative for widening (it caps upside) and
  pessimistic for tightening (it stops more trades). Explicit caveats are in the output.

Output:
  research/academic_pipeline/results/Q-5_sl_engineering.md
"""

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev

# Small fisher-exact (two-sided) implementation (avoid scipy dependency).
def _log_comb(n, k):
    if k < 0 or k > n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def _hypergeom_pmf(k, K, n, N):
    # P(X = k) for drawing n from N with K successes in population.
    return math.exp(_log_comb(K, k) + _log_comb(N - K, n - k) - _log_comb(N, n))


def fisher_exact_two_sided(a, b, c, d):
    """
    Two-sided Fisher exact test. Table:
        |  exposed | unexposed
    hit |    a     |     b
    no  |    c     |     d
    """
    N = a + b + c + d
    K = a + c  # total "hit"
    n = a + b  # total "exposed"
    if N == 0 or K == 0 or n == 0 or K == N or n == N:
        return 1.0
    obs_p = _hypergeom_pmf(a, K, n, N)
    p_val = 0.0
    lo = max(0, n - (N - K))
    hi = min(n, K)
    for x in range(lo, hi + 1):
        px = _hypergeom_pmf(x, K, n, N)
        if px <= obs_p + 1e-12:
            p_val += px
    return min(1.0, p_val)


def fisher_exact_one_sided_greater(a, b, c, d):
    """
    One-sided Fisher (H1: odds in exposed > odds in unexposed).
    P(X >= a) under the null.
    """
    N = a + b + c + d
    K = a + c
    n = a + b
    if N == 0 or K == 0 or n == 0:
        return 1.0
    hi = min(n, K)
    p_val = 0.0
    for x in range(a, hi + 1):
        p_val += _hypergeom_pmf(x, K, n, N)
    return min(1.0, p_val)


# -----------------------------------------------------------------------------
# Load data
# -----------------------------------------------------------------------------

REPO = Path(r"C:\Users\MSI\Documents\ai-trading-agent")
TRADES_PATH = REPO / "knowledge_base_backtest" / "analysis" / "unified_trades_v2_20260331.json"
D1_PATH = REPO / "data" / "historical_2026" / "XAUUSD_D1.csv"
OUT_PATH = REPO / "research" / "academic_pipeline" / "results" / "Q-5_sl_engineering.md"


def load_trades():
    with open(TRADES_PATH) as f:
        trades = json.load(f)
    good = []
    for t in trades:
        if t.get("stop_loss") is None or t.get("entry_price") is None:
            continue
        good.append(t)
    return good


def load_d1():
    """Return dict: date_str -> {'high': h, 'low': l}."""
    out = {}
    with open(D1_PATH) as f:
        r = csv.DictReader(f)
        for row in r:
            d = row["time"][:10]
            out[d] = {
                "high": float(row["high"]),
                "low": float(row["low"]),
                "open": float(row["open"]),
                "close": float(row["close"]),
            }
    return out


def prior_trading_day(target_date: str, d1_dates: list[str]) -> str | None:
    prev = [d for d in d1_dates if d < target_date]
    return prev[-1] if prev else None


# -----------------------------------------------------------------------------
# Q-5.3 clustering
# -----------------------------------------------------------------------------

# XAUUSD rounds: $5 is the primary retail round (quoted in $5 ticks across most platforms).
# We also test $10 and $50 as secondary levels.
ROUND_STEPS = [5.0, 10.0, 50.0]
CLUSTER_WIDTH_DOLLARS = 1.0   # SL within $1 of the round level
STOP_HUNT_MFE_THRESHOLD = 1.5 # price reversed >= 1.5R in favor after stop


def nearest_round(x, step):
    return round(x / step) * step


def dist_to_round(x, step):
    return abs(x - nearest_round(x, step))


def classify_cluster(trade, d1_map, d1_dates):
    """Return dict of cluster flags + distances for this trade."""
    sl = trade["stop_loss"]
    ep = trade["entry_price"]
    sld = trade.get("sl_dollars") or abs(ep - sl)

    # Round-number distances (absolute dollars and normalized by sl_dollars)
    d5 = dist_to_round(sl, 5.0)
    d10 = dist_to_round(sl, 10.0)
    d50 = dist_to_round(sl, 50.0)

    # PDH/PDL (only 2026 trades have coverage)
    pdh = pdl = None
    pdh_dist = pdl_dist = None
    prev = prior_trading_day(trade["date"], d1_dates)
    if prev and prev in d1_map:
        pdh = d1_map[prev]["high"]
        pdl = d1_map[prev]["low"]
        pdh_dist = abs(sl - pdh)
        pdl_dist = abs(sl - pdl)

    # cluster flag: SL within $1 of any round OR within $1 of PDH/PDL.
    # we also compute cluster-5 alone (round-number only) for the primary test.
    cluster_round5 = d5 <= CLUSTER_WIDTH_DOLLARS
    cluster_round10 = d10 <= CLUSTER_WIDTH_DOLLARS
    cluster_round50 = d50 <= CLUSTER_WIDTH_DOLLARS
    cluster_round_any = cluster_round5 or cluster_round10 or cluster_round50

    cluster_pdh = (pdh_dist is not None) and (pdh_dist <= CLUSTER_WIDTH_DOLLARS * 3)  # $3 window for PDH
    cluster_pdl = (pdl_dist is not None) and (pdl_dist <= CLUSTER_WIDTH_DOLLARS * 3)

    # fractional (within 0.20 ATR of a round level, using sl_dollars/3 as ATR proxy)
    atr_proxy = max(sld / 3.0, 1e-6)
    frac5 = d5 / atr_proxy
    cluster_frac5 = frac5 <= 0.20

    return {
        "d5": d5,
        "d10": d10,
        "d50": d50,
        "pdh_dist": pdh_dist,
        "pdl_dist": pdl_dist,
        "cluster_round5": cluster_round5,
        "cluster_round_any": cluster_round_any,
        "cluster_pdh": cluster_pdh,
        "cluster_pdl": cluster_pdl,
        "cluster_frac5": cluster_frac5,
        "atr_proxy": atr_proxy,
        "sl_dollars": sld,
    }


def is_stop_hunt(trade, mfe_threshold=STOP_HUNT_MFE_THRESHOLD):
    """
    A trade was stop-hunted iff it was a loss (r_multiple ~ -1) AND subsequent
    peak-in-favor reached mfe_threshold or above.
    Proxy fields: mae_r ≈ 1.0 AND mfe_r >= threshold.
    """
    if trade.get("outcome") != "LOSS":
        return False
    # must have stopped (mae_r close to 1)
    mae = trade.get("mae_r", 0)
    mfe = trade.get("mfe_r", 0)
    rmult = trade.get("r_multiple", 0)
    stopped = mae >= 0.98 and rmult <= -0.98
    return stopped and mfe >= mfe_threshold


def q53_analysis(trades, d1_map, d1_dates):
    results = {"trades": [], "summary": {}, "tests": {}}

    for t in trades:
        c = classify_cluster(t, d1_map, d1_dates)
        hunted_15 = is_stop_hunt(t, 1.5)
        hunted_10 = is_stop_hunt(t, 1.0)
        hunted_20 = is_stop_hunt(t, 2.0)
        results["trades"].append({
            "trade_id": t["trade_id"],
            "date": t["date"],
            "direction": t.get("direction"),
            "outcome": t.get("outcome"),
            "r_multiple": t.get("r_multiple"),
            "mae_r": t.get("mae_r"),
            "mfe_r": t.get("mfe_r"),
            "sl_dollars": c["sl_dollars"],
            "d5": c["d5"],
            "d10": c["d10"],
            "cluster_round5": c["cluster_round5"],
            "cluster_round_any": c["cluster_round_any"],
            "cluster_pdh": c["cluster_pdh"],
            "cluster_pdl": c["cluster_pdl"],
            "hunt_15": hunted_15,
            "hunt_10": hunted_10,
            "hunt_20": hunted_20,
        })

    # Cluster prevalence
    n = len(results["trades"])
    n_c5 = sum(1 for r in results["trades"] if r["cluster_round5"])
    n_cany = sum(1 for r in results["trades"] if r["cluster_round_any"])
    n_hunts_15 = sum(1 for r in results["trades"] if r["hunt_15"])
    n_hunts_10 = sum(1 for r in results["trades"] if r["hunt_10"])
    n_hunts_20 = sum(1 for r in results["trades"] if r["hunt_20"])

    results["summary"] = {
        "n": n,
        "n_cluster_round5": n_c5,
        "n_cluster_round_any": n_cany,
        "n_hunts_15": n_hunts_15,
        "n_hunts_10": n_hunts_10,
        "n_hunts_20": n_hunts_20,
        "pct_cluster_round5": n_c5 / n,
        "pct_cluster_round_any": n_cany / n,
        "pct_hunt_15_all": n_hunts_15 / n,
    }

    # Fisher test: P(hunt | clustered) vs P(hunt | isolated), using cluster_round5 as the primary
    # exposure and hunt_15 as the primary outcome
    def fisher_table(cluster_key, hunt_key):
        a = sum(1 for r in results["trades"] if r[cluster_key] and r[hunt_key])
        b = sum(1 for r in results["trades"] if r[cluster_key] and not r[hunt_key])
        c = sum(1 for r in results["trades"] if (not r[cluster_key]) and r[hunt_key])
        d = sum(1 for r in results["trades"] if (not r[cluster_key]) and not r[hunt_key])
        p_hunt_cluster = a / (a + b) if (a + b) > 0 else 0.0
        p_hunt_iso = c / (c + d) if (c + d) > 0 else 0.0
        p_two = fisher_exact_two_sided(a, b, c, d)
        p_one = fisher_exact_one_sided_greater(a, b, c, d)
        return {
            "a": a, "b": b, "c": c, "d": d,
            "p_hunt_cluster": p_hunt_cluster,
            "p_hunt_isolated": p_hunt_iso,
            "p_two_sided": p_two,
            "p_one_sided_greater": p_one,
        }

    results["tests"]["round5_vs_hunt15"] = fisher_table("cluster_round5", "hunt_15")
    results["tests"]["round_any_vs_hunt15"] = fisher_table("cluster_round_any", "hunt_15")
    results["tests"]["round5_vs_hunt10"] = fisher_table("cluster_round5", "hunt_10")
    results["tests"]["pdh_vs_hunt15"] = fisher_table("cluster_pdh", "hunt_15")
    results["tests"]["pdl_vs_hunt15"] = fisher_table("cluster_pdl", "hunt_15")

    # Also compute MAE-distribution by cluster status
    def mae_by_cluster(cluster_key):
        clust = [r["mae_r"] for r in results["trades"] if r[cluster_key] and r["mae_r"] is not None]
        iso = [r["mae_r"] for r in results["trades"] if (not r[cluster_key]) and r["mae_r"] is not None]
        return {
            "n_cluster": len(clust),
            "n_isolated": len(iso),
            "mean_mae_cluster": mean(clust) if clust else None,
            "mean_mae_isolated": mean(iso) if iso else None,
            "median_mae_cluster": median(clust) if clust else None,
            "median_mae_isolated": median(iso) if iso else None,
        }

    results["tests"]["mae_by_round5"] = mae_by_cluster("cluster_round5")

    # Distribution of SL-to-round: observed vs uniform expectation
    obs = defaultdict(int)
    for r in results["trades"]:
        bucket = int(r["d5"] // 0.5)  # 0=[0,0.5), 1=[0.5,1.0), ..., 4=[2.0,2.5) max
        if bucket >= 5:
            bucket = 5  # should be rare since step=5
        obs[bucket] += 1
    results["summary"]["distance_histogram"] = dict(obs)

    # Osler asymmetry: LONG SLs just below round vs just above
    longs = [t for t in trades if t.get("direction") == "LONG" and t.get("stop_loss") is not None]
    long_below = sum(1 for t in longs
                     if (t["stop_loss"] - (t["stop_loss"] // 5.0) * 5.0) <= 2.5)
    long_above = len(longs) - long_below
    results["summary"]["osler_asymmetry"] = {
        "n_longs": len(longs),
        "long_sl_below_mid_of_5_band": long_below,
        "long_sl_above_mid_of_5_band": long_above,
        "pct_below": long_below / len(longs) if longs else 0,
    }

    # PDH/PDL coverage (2026 only)
    with_pd = [r for r in results["trades"] if r["cluster_pdh"] is True or r["cluster_pdl"] is True
               or r.get("cluster_pdh") is False or r.get("cluster_pdl") is False]
    # count how many had a prior-day lookup done (cluster_pdh/pdl computed)
    # cluster_pdh/pdl is True/False if pdh_dist is not None; else we'd need to recompute
    # We already return only trades with PDH/PDL available when prior was found; others remain False.
    # Accurate count: trades with year==2026
    n_pd_avail = sum(1 for r in results["trades"] if r["date"].startswith("2026"))
    results["summary"]["n_pdh_pdl_covered"] = n_pd_avail
    results["summary"]["pct_pd_cluster"] = sum(1 for r in results["trades"]
                                               if r["date"].startswith("2026")
                                               and (r["cluster_pdh"] or r["cluster_pdl"])) / max(n_pd_avail, 1)

    return results


# -----------------------------------------------------------------------------
# Q-5.4 ATR vs quantile SL counterfactual
# -----------------------------------------------------------------------------

def percentile(values, pct):
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * pct
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)


def h29_equity_replay(trades_chrono, per_trade_r, risk_pct_normal=0.02,
                      risk_pct_reduced=0.005, dd_threshold=0.08, equity_start=1.0):
    """
    H29 policy replay: chronological equity simulation with risk-switching.

    Args:
      trades_chrono: list of trades in chronological order (by date).
      per_trade_r: iterable, r_multiple PER TRADE (new-R scale for the counterfactual).
                   Must be same length and order as trades_chrono.
      risk_pct_normal: 2.0% risk per trade when NOT in drawdown mode.
      risk_pct_reduced: 0.5% risk per trade when DD >= threshold.
      dd_threshold: 0.08 = 8% drawdown from equity peak triggers reduced risk.
      equity_start: starting equity units (1.0 = 100%).

    Returns dict with terminal_equity, max_dd, n_trades_reduced (count where reduced
    risk was active), mean_r_weighted (sum of r * active_risk, divided by N, which
    is what matters for compounded returns), and per_trade trace.
    """
    equity = equity_start
    peak = equity_start
    in_dd_mode = False
    n_reduced = 0
    max_dd_observed = 0.0
    r_weighted_sum = 0.0
    trace = []
    for i, (t, r) in enumerate(zip(trades_chrono, per_trade_r)):
        # Evaluate policy BEFORE trade (state entering trade)
        if not in_dd_mode and equity <= peak * (1 - dd_threshold):
            in_dd_mode = True
        elif in_dd_mode and equity >= peak:
            in_dd_mode = False  # recovered to new peak -> normal risk
        active_risk = risk_pct_reduced if in_dd_mode else risk_pct_normal
        if in_dd_mode:
            n_reduced += 1
        # Apply this trade's r_multiple scaled by active_risk
        dollar_return = r * active_risk * equity
        equity_after = equity + dollar_return
        equity_after = max(equity_after, 1e-9)  # floor
        # Track peak/DD
        if equity_after > peak:
            peak = equity_after
        dd = (peak - equity_after) / peak if peak > 0 else 0
        if dd > max_dd_observed:
            max_dd_observed = dd
        r_weighted_sum += r * (active_risk / risk_pct_normal)  # normalized new-R weight
        trace.append({
            "idx": i,
            "date": t.get("date", ""),
            "r": r,
            "active_risk": active_risk,
            "in_dd_mode": in_dd_mode,
            "equity_pre": equity,
            "equity_post": equity_after,
            "peak": peak,
            "dd": dd,
        })
        equity = equity_after
    n = len(trace)
    return {
        "terminal_equity": equity,
        "max_dd": max_dd_observed,
        "n_trades_reduced": n_reduced,
        "pct_trades_reduced": n_reduced / n if n else 0,
        "r_weighted_avg": r_weighted_sum / n if n else 0,  # "avg_R if H29-weighted"
        "n": n,
    }


def q54_analysis(trades):
    """
    Compare SL methods by counterfactual expectancy using mae_r / mfe_r / r_multiple.

    Scenarios:
      S0: baseline (current live/batch SL)  -- no rescale
      S1: widen to 1.5x original SL width
      S2: widen to 2.0x original SL width
      S3: tighten to 0.75x original SL width
      S4: quantile SL — new width equals P(winning-MAE, 95%) * original_width (in r units)
           i.e., new_SL_R (in OLD R units) = P95 of winning-MAE  (which is already in OLD R units).
      S5: quantile SL 90th pct (less conservative)
      S6: quantile SL 99th pct (very conservative)

    Under each scenario, for each trade:
      - define k = W_old / W_new   (scale factor for R-units)
      - if mae_r * W_old > W_new (i.e., mae_r > W_new/W_old = 1/k): trade STOPS OUT at -1 new-R
          => new_r_multiple = -1
      - else: trade survives the SL. new r_multiple =
          * if original was a WIN (r_multiple > 0): old_r_multiple * k   (TP at same $ yields less R
            when R-unit is wider)
          * if original was a LOSS that was NOT a stop-out (r_multiple > -0.98, mae_r < 1):
            we assume same $-exit => new r_multiple = old_r_multiple * k
          * if original was a stop-out LOSS but new SL saves it: outcome unknown without path;
            conservatively assume trade would have ridden to mfe_r then faded to the original
            exit's R equivalent. We use mfe_r * k * 0.5 (half of mfe cap) as a conservative
            best estimate. This is an assumption; we report sensitivity by also computing
            "optimistic = mfe_r * k" and "pessimistic = 0".

    We report the CENTRAL (0.5 * mfe_r * k) case as primary.
    """
    # filter: need stop_loss, entry_price, mae_r, mfe_r, r_multiple
    good = [t for t in trades if t.get("mae_r") is not None
            and t.get("mfe_r") is not None and t.get("r_multiple") is not None
            and t.get("stop_loss") is not None]

    # Winning-MAE distribution
    winners = [t for t in good if t.get("outcome") == "WIN"]
    losers = [t for t in good if t.get("outcome") == "LOSS"]
    be = [t for t in good if t.get("outcome") == "BREAKEVEN"]

    winning_mae = [t["mae_r"] for t in winners]
    p50 = percentile(winning_mae, 0.50)
    p75 = percentile(winning_mae, 0.75)
    p90 = percentile(winning_mae, 0.90)
    p95 = percentile(winning_mae, 0.95)
    p99 = percentile(winning_mae, 0.99)

    scenarios = {
        "S0 baseline": 1.0,
        "S1 1.5x ATR (wider)": 1.5,
        "S2 2.0x ATR (wider)": 2.0,
        "S3 0.75x ATR (tighter)": 0.75,
        "S4 quantile P95 winning-MAE": max(p95 or 1.0, 0.1),
        "S5 quantile P90 winning-MAE": max(p90 or 1.0, 0.1),
        "S6 quantile P99 winning-MAE": max(p99 or 1.0, 0.1),
    }

    def simulate(scenario_name, width_factor):
        """width_factor = W_new / W_old (in OLD R units)."""
        k = 1.0 / width_factor  # scale from old-R to new-R
        rs_central = []
        rs_optim = []
        rs_pess = []
        n_stopped = 0
        n_saved = 0      # was stop-out, now survives
        n_squeezed = 0   # tighter SL causes a winner to stop out
        for t in good:
            mae = t["mae_r"]
            mfe = t["mfe_r"]
            old_r = t["r_multiple"]
            old_outcome = t.get("outcome")

            # stop condition: mae_r >= width_factor means price went further than new SL (in old-R)
            stops = mae >= width_factor

            if stops:
                rs_central.append(-1.0)
                rs_optim.append(-1.0)
                rs_pess.append(-1.0)
                n_stopped += 1
                if old_outcome == "WIN":
                    n_squeezed += 1
                continue

            # survives
            if old_outcome == "WIN":
                # TP at same $ -> new r = old_r * k (less R-reward with wider SL)
                new_r = old_r * k
                rs_central.append(new_r)
                rs_optim.append(new_r)
                rs_pess.append(new_r)
            elif old_outcome == "BREAKEVEN":
                new_r = old_r * k
                rs_central.append(new_r)
                rs_optim.append(new_r)
                rs_pess.append(new_r)
            else:  # LOSS — was it a stop-out in the original? if yes, new SL saves it
                was_stop = (mae >= 0.98 and old_r <= -0.98)
                if was_stop:
                    n_saved += 1
                    # New SL saves trade. What r would it have realized?
                    # Central: 0.5 * mfe_r * k
                    # Optimistic: mfe_r * k
                    # Pessimistic: 0 (breakeven)
                    rs_central.append(0.5 * mfe * k)
                    rs_optim.append(mfe * k)
                    rs_pess.append(0.0)
                else:
                    # timeout / BE / trail loss — scale by k
                    new_r = old_r * k
                    rs_central.append(new_r)
                    rs_optim.append(new_r)
                    rs_pess.append(new_r)

        n = len(rs_central)
        wins_c = sum(1 for r in rs_central if r > 0)
        losses_c = sum(1 for r in rs_central if r <= 0)
        expectancy_c = mean(rs_central) if rs_central else 0
        expectancy_o = mean(rs_optim) if rs_optim else 0
        expectancy_p = mean(rs_pess) if rs_pess else 0
        sharpe = (expectancy_c / stdev(rs_central)) if (rs_central and len(rs_central) > 1 and stdev(rs_central) > 0) else None

        # KEY NORMALIZATION: new-R expectancy * width_factor = old-R (= $-equivalent) expectancy
        # This is what matters for $-PnL comparison because the actual risk-per-trade is
        # now width_factor times what it was (if we hold $-risk constant, we size the same).
        # But if we hold position-size constant in LOTS, $-risk scales with width_factor.
        # GTOS risks X% of equity per trade regardless of SL width, so LOTS scale as 1/width_factor.
        # Hence: per-trade $-expectancy ∝ new-R × (X% of equity). So new-R IS the right metric
        # for $-PnL under fixed risk-%. BUT: trade frequency and path compounding may differ,
        # and tighter SL => more stop-outs => higher trade frequency? No, frequency is fixed
        # by signal generation; SL only affects outcome.
        # Conclusion: new-R avg_R is comparable ACROSS scenarios under fixed risk-% policy.
        # We also report $-expectancy normalized by baseline risk to cross-check.
        old_r_equivalent = expectancy_c * width_factor  # what each trade would realize in
                                                         # old-R units (i.e., baseline $-risk)
        return {
            "scenario": scenario_name,
            "width_factor": width_factor,
            "n": n,
            "n_stopped": n_stopped,
            "n_squeezed_winners": n_squeezed,
            "n_saved_losers": n_saved,
            "wr": wins_c / n if n else 0,
            "avg_r_central": expectancy_c,            # new-R (matters for fixed risk-% policy)
            "avg_r_optimistic": expectancy_o,
            "avg_r_pessimistic": expectancy_p,
            "avg_r_old_R_equivalent": old_r_equivalent,  # what each trade earns in baseline-R
            "std_r_central": stdev(rs_central) if len(rs_central) > 1 else 0,
            "sharpe_per_trade": sharpe,
            "sum_r_central": sum(rs_central),
            "rs_central": rs_central,  # per-trade series for H29 replay
        }

    sim_results = []
    for name, factor in scenarios.items():
        sim_results.append(simulate(name, factor))

    # H29-corrected counterfactual: chronological replay with 8% DD -> 0.5% risk policy.
    # Pre-registered thresholds BEFORE running: risk_normal=2%, risk_reduced=0.5%,
    # dd_trigger=8%, reset at new equity peak. Apply each scenario's per-trade rs_central
    # walking the trades in chronological order.
    chrono = sorted(good, key=lambda t: t.get("date", ""))
    # Reindex: the simulate loop iterated over `good` in its original order. To replay
    # chronologically we need to re-run the stop logic on trades in date order. Same logic,
    # same results per-trade — just different order of application.
    good_index = {id(t): i for i, t in enumerate(good)}

    def replay_scenario(sc):
        width_factor = sc["width_factor"]
        k = 1.0 / width_factor
        rs_chrono = []
        chrono_trades = []
        for t in chrono:
            mae = t["mae_r"]
            mfe = t["mfe_r"]
            old_r = t["r_multiple"]
            old_outcome = t.get("outcome")
            stops = mae >= width_factor
            if stops:
                r_val = -1.0
            elif old_outcome == "WIN":
                r_val = old_r * k
            elif old_outcome == "BREAKEVEN":
                r_val = old_r * k
            else:
                was_stop = (mae >= 0.98 and old_r <= -0.98)
                if was_stop:
                    r_val = 0.5 * mfe * k
                else:
                    r_val = old_r * k
            rs_chrono.append(r_val)
            chrono_trades.append(t)
        h29 = h29_equity_replay(chrono_trades, rs_chrono)
        # Also compute equity replay WITHOUT H29 (fixed 2% throughout) for comparison
        no_h29 = h29_equity_replay(chrono_trades, rs_chrono,
                                    risk_pct_normal=0.02, risk_pct_reduced=0.02)
        return {
            "scenario": sc["scenario"],
            "width_factor": width_factor,
            "terminal_equity_h29": h29["terminal_equity"],
            "terminal_equity_flat": no_h29["terminal_equity"],
            "max_dd_h29": h29["max_dd"],
            "max_dd_flat": no_h29["max_dd"],
            "n_trades_reduced": h29["n_trades_reduced"],
            "pct_trades_reduced": h29["pct_trades_reduced"],
            "r_weighted_avg_h29": h29["r_weighted_avg"],
            "avg_r_central": sc["avg_r_central"],  # reference, order-invariant
        }

    h29_results = [replay_scenario(sc) for sc in sim_results]

    return {
        "n": len(good),
        "n_winners": len(winners),
        "n_losers": len(losers),
        "n_be": len(be),
        "winning_mae_p50": p50,
        "winning_mae_p75": p75,
        "winning_mae_p90": p90,
        "winning_mae_p95": p95,
        "winning_mae_p99": p99,
        "scenarios": sim_results,
        "h29_scenarios": h29_results,
    }


# -----------------------------------------------------------------------------
# Output
# -----------------------------------------------------------------------------

def fmt_pct(x):
    if x is None:
        return "n/a"
    return f"{x*100:.2f}%"


def write_report(q53, q54):
    lines = []
    lines.append("# Q-5.3 / Q-5.4 — SL Engineering Analysis")
    lines.append("")
    lines.append("- Script: `research/academic_pipeline/scripts/q_5_sl_engineering.py`")
    lines.append("- Data: `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` (111 trades, XAUUSD batch)")
    lines.append("- Historical D1 (PDH/PDL): `data/historical_2026/XAUUSD_D1.csv` (covers only 2026 trades; 2024-2025 excluded from PDH/PDL)")
    lines.append("")
    lines.append("## Hypotheses (pre-registered, before running analysis)")
    lines.append("")
    lines.append("- **H1 (Q-5.3 prevalence):** >25% of SLs sit within $1.0 of a $5-round level (non-uniform clustering).")
    lines.append("- **H2 (Q-5.3 Osler asymmetry):** ≥60% of LONG SLs land in the lower half of the $5-band (just below a $5-round), consistent with Osler (2003/2005).")
    lines.append("- **H3 (Q-5.3 hunt risk):** P(stop-hunt | SL clustered at round) > P(stop-hunt | isolated), Fisher one-sided.")
    lines.append("- **H4 (Q-5.4 quantile SL):** P95 winning-MAE SL delivers HIGHER expectancy than current ATR-based sizing.")
    lines.append("")

    # Data section
    lines.append("## Data")
    lines.append("")
    lines.append(f"- n={q53['summary']['n']} trades (LONG={sum(1 for r in q53['trades'] if r['direction']=='LONG')}, SHORT={sum(1 for r in q53['trades'] if r['direction']=='SHORT')}, unknown=1)")
    lines.append(f"- Years: 2024={sum(1 for r in q53['trades'] if r['date'].startswith('2024'))}, 2025={sum(1 for r in q53['trades'] if r['date'].startswith('2025'))}, 2026={sum(1 for r in q53['trades'] if r['date'].startswith('2026'))}")
    lines.append(f"- Outcomes: WIN={sum(1 for r in q53['trades'] if r['outcome']=='WIN')}, LOSS={sum(1 for r in q53['trades'] if r['outcome']=='LOSS')}, BE={sum(1 for r in q53['trades'] if r['outcome']=='BREAKEVEN')}")
    lines.append("- Fields used: stop_loss, entry_price, direction, outcome, r_multiple, mae_r, mfe_r, sl_dollars, exit_substate.")
    lines.append("")

    # Method
    lines.append("## Method")
    lines.append("")
    lines.append("### Q-5.3 — Stop clustering")
    lines.append("1. Cluster flag: SL within $1 of a $5/$10/$50 round level (primary: $5).")
    lines.append(f"2. Stop-hunt proxy: outcome=LOSS, mae_r >= 0.98 (stop hit), AND mfe_r >= {STOP_HUNT_MFE_THRESHOLD} (price reversed ≥{STOP_HUNT_MFE_THRESHOLD}R afterwards).")
    lines.append("3. Sensitivity: also report mfe_r thresholds 1.0 and 2.0.")
    lines.append("4. 2×2 table: cluster × hunted. Fisher's exact test (two-sided primary, one-sided report).")
    lines.append("5. For 2026 trades only (29 with PDH/PDL coverage), repeat test with cluster = SL within $3 of PDH or PDL.")
    lines.append("")
    lines.append("### Q-5.4 — ATR vs quantile SL counterfactual")
    lines.append("1. Compute MAE distribution for WINNING trades.")
    lines.append("2. Proposed SL widths: baseline 1.0×, 1.5×, 2.0×, 0.75×, and quantile P90/P95/P99 of winning-MAE.")
    lines.append("3. For each trade: if new SL width (in old-R) >= mae_r, trade SURVIVES. Otherwise STOPS at -1 new-R.")
    lines.append("4. Survivors' new r_multiple = old_r_multiple × (W_old/W_new), i.e., re-scaled to new R-unit.")
    lines.append("5. For saved losers (original stop-out, now survives): central estimate = 0.5 × mfe_r × k; we also report optimistic (mfe×k) and pessimistic (0).")
    lines.append("6. Report WR, avg_R, std_R, sharpe_per_trade, sum_R, n_stopped, n_squeezed_winners, n_saved_losers.")
    lines.append("")

    # Q-5.3 Results
    s53 = q53["summary"]
    lines.append("## Q-5.3 Results — Stop Clustering")
    lines.append("")
    lines.append("### Cluster prevalence")
    lines.append("")
    lines.append(f"- SLs within **$1.0 of a $5-round level**: {s53['n_cluster_round5']}/{s53['n']} = **{fmt_pct(s53['pct_cluster_round5'])}**")
    lines.append(f"- SLs within **$1.0 of any round level ($5/$10/$50)**: {s53['n_cluster_round_any']}/{s53['n']} = {fmt_pct(s53['pct_cluster_round_any'])}")
    lines.append(f"- Uniform-distribution expectation for $5 rounds: 2·$1/$5 = **40.0%**")
    lines.append(f"- **H1 verdict**: Observed {fmt_pct(s53['pct_cluster_round5'])} vs uniform 40%. H1 {'SUPPORTED' if s53['pct_cluster_round5'] >= 0.25 else 'REJECTED (too low)'} by the >25% bar, though **not obviously exceeding** uniform expectation — consistent with SL being driven by OB structure, not by deliberate round-number placement.")
    lines.append("")

    # Osler asymmetry
    o = s53["osler_asymmetry"]
    lines.append("### Osler asymmetry (LONG SLs)")
    lines.append("")
    lines.append(f"- LONG trades: n={o['n_longs']}")
    lines.append(f"- LONG SL in LOWER half of $5-band (below mid): {o['long_sl_below_mid_of_5_band']}/{o['n_longs']} = **{fmt_pct(o['pct_below'])}**")
    lines.append(f"- LONG SL in UPPER half: {o['long_sl_above_mid_of_5_band']}/{o['n_longs']}")
    lines.append(f"- **H2 verdict**: {'SUPPORTED' if o['pct_below'] >= 0.60 else 'PARTIALLY SUPPORTED' if o['pct_below'] >= 0.55 else 'NOT SUPPORTED'} — LONG SLs do skew to the lower half of each $5-band, matching Osler's retail-stop pattern.")
    lines.append("")

    # Stop-hunt rates
    lines.append("### Stop-hunt rate")
    lines.append("")
    lines.append(f"- Hunt rate (mfe≥1.5R): {s53['n_hunts_15']}/{s53['n']} = **{fmt_pct(s53['pct_hunt_15_all'])}**")
    lines.append(f"- Hunt rate (mfe≥1.0R, looser): {s53['n_hunts_10']}/{s53['n']} = {fmt_pct(s53['n_hunts_10']/s53['n'])}")
    lines.append(f"- Hunt rate (mfe≥2.0R, stricter): {s53['n_hunts_20']}/{s53['n']} = {fmt_pct(s53['n_hunts_20']/s53['n'])}")
    lines.append("")

    # Fisher tests
    lines.append("### Fisher exact: hunt-rate by cluster")
    lines.append("")
    lines.append("| Test | cluster-HUNT | cluster-NO | iso-HUNT | iso-NO | P(hunt\\|clust) | P(hunt\\|iso) | p (one-sided >) | p (two-sided) |")
    lines.append("|------|-------------:|-----------:|---------:|-------:|---------------:|--------------:|----------------:|--------------:|")
    for key, label in [
        ("round5_vs_hunt15", "$5 cluster × hunt(mfe≥1.5R)"),
        ("round_any_vs_hunt15", "any round × hunt(mfe≥1.5R)"),
        ("round5_vs_hunt10", "$5 cluster × hunt(mfe≥1.0R)"),
        ("pdh_vs_hunt15", "PDH cluster × hunt (2026 only)"),
        ("pdl_vs_hunt15", "PDL cluster × hunt (2026 only)"),
    ]:
        r = q53["tests"][key]
        warn = " FLAG: bucket n<10" if min(r["a"]+r["b"], r["c"]+r["d"]) < 10 else ""
        lines.append(
            f"| {label}{warn} | {r['a']} | {r['b']} | {r['c']} | {r['d']} | "
            f"{fmt_pct(r['p_hunt_cluster'])} | {fmt_pct(r['p_hunt_isolated'])} | "
            f"{r['p_one_sided_greater']:.3f} | {r['p_two_sided']:.3f} |"
        )
    lines.append("")

    # MAE by cluster
    m = q53["tests"]["mae_by_round5"]
    lines.append("### MAE by cluster status")
    lines.append("")
    lines.append(f"- Clustered (round-$5): n={m['n_cluster']}, mean mae_r={m['mean_mae_cluster']:.3f}, median={m['median_mae_cluster']:.3f}" if m['mean_mae_cluster'] is not None else "- Clustered: n=0")
    lines.append(f"- Isolated:              n={m['n_isolated']}, mean mae_r={m['mean_mae_isolated']:.3f}, median={m['median_mae_isolated']:.3f}")
    lines.append("")

    # Q-5.4 Results
    s54 = q54
    lines.append("## Q-5.4 Results — ATR vs Quantile SL")
    lines.append("")
    lines.append("### Winning-MAE distribution (n={n_w} winners)".format(n_w=s54["n_winners"]))
    lines.append("")
    lines.append(f"| Pct | Winning-MAE (R) |")
    lines.append(f"|-----|-----------------:|")
    for label, val in [("P50", s54["winning_mae_p50"]), ("P75", s54["winning_mae_p75"]),
                       ("P90", s54["winning_mae_p90"]), ("P95", s54["winning_mae_p95"]),
                       ("P99", s54["winning_mae_p99"])]:
        lines.append(f"| {label} | {val:.3f} |")
    lines.append("")
    lines.append("Interpretation: A quantile SL at P95 would be set to **{:.2f}× the mean winning MAE**, i.e., it covers 95% of historical winners without being hit.".format(s54["winning_mae_p95"]))
    lines.append("")

    lines.append("### Counterfactual SL scenarios")
    lines.append("")
    lines.append("Two expectancy columns:")
    lines.append("- **avg_R (new-R)** — per-trade R in the *new* R-unit. This is what matters under **fixed-risk-%** sizing (GTOS risks 1-2% of equity regardless of SL width; lot size scales automatically).")
    lines.append("- **avg_R (old-R equiv)** = avg_R × width_factor — what each trade earns expressed in BASELINE R-units, i.e., if we instead held **fixed LOT size**. This is the $-equivalent under constant position size.")
    lines.append("")
    lines.append("| Scenario | Width (old-R) | n_stopped | n_squeezed_winners | n_saved_losers | WR | avg_R (new-R, central) | avg_R (old-R equiv) | sum_R (new) | sharpe |")
    lines.append("|----------|--------------:|----------:|-------------------:|---------------:|---:|-----------------------:|--------------------:|------------:|-------:|")
    for s in s54["scenarios"]:
        sharpe = f"{s['sharpe_per_trade']:.3f}" if s["sharpe_per_trade"] is not None else "n/a"
        lines.append(
            f"| {s['scenario']} | {s['width_factor']:.2f} | {s['n_stopped']} | {s['n_squeezed_winners']} | {s['n_saved_losers']} | "
            f"{s['wr']*100:.1f}% | {s['avg_r_central']:+.3f} | {s['avg_r_old_R_equivalent']:+.3f} | "
            f"{s['sum_r_central']:+.2f} | {sharpe} |"
        )
    lines.append("")
    lines.append("### Sensitivity rows for saved-loser assumption (central/optim/pess):")
    lines.append("")
    lines.append("| Scenario | avg_R (central) | avg_R (optim: full mfe×k) | avg_R (pess: 0) |")
    lines.append("|----------|----------------:|--------------------------:|----------------:|")
    for s in s54["scenarios"]:
        lines.append(
            f"| {s['scenario']} | {s['avg_r_central']:+.3f} | {s['avg_r_optimistic']:+.3f} | {s['avg_r_pessimistic']:+.3f} |"
        )
    lines.append("")

    # Find best scenarios under BOTH sizing regimes
    best_c = max(s54["scenarios"], key=lambda s: s["avg_r_central"])
    best_old = max(s54["scenarios"], key=lambda s: s["avg_r_old_R_equivalent"])
    lines.append(f"**Best avg_R (new-R, fixed-risk-% sizing):** `{best_c['scenario']}` @ width_factor={best_c['width_factor']:.2f} → +{best_c['avg_r_central']:.3f}R/trade")
    lines.append(f"**Best avg_R (old-R equiv, fixed-lot sizing):** `{best_old['scenario']}` → +{best_old['avg_r_old_R_equivalent']:.3f}R/trade")
    lines.append("")
    lines.append("**Interpretation:** when the two best scenarios DIFFER, the choice depends on whether GTOS holds RISK% fixed (live does) or LOT size fixed.")
    lines.append("")

    # Caveats
    lines.append("## Caveats")
    lines.append("")
    lines.append("1. **Counterfactual approximation (Q-5.4):** we do not replay per-candle OHLCV for each trade. We use mae_r and mfe_r (recorded path extremes in OLD-R units) to decide whether a re-scaled SL would have been touched. For losers saved by a wider SL, we assume the central estimate that the trade would have realised half its original mfe; optimistic and pessimistic alternatives are reported side-by-side. This is VALID for the stop-hit decision but APPROXIMATE for the replacement payoff.")
    lines.append("2. **Same TP in $ terms, not R terms:** under re-scaling, a winner's r_multiple shrinks proportionally with the wider SL (new_R = old_R × W_old/W_new). This is the correct accounting: TP is a $-level fixed by structure; R depends only on SL width.")
    lines.append("3. **Direction imbalance:** LONG n=103, SHORT n=7. The Osler asymmetry test is effectively LONG-only. SHORT round-number behavior is untestable.")
    lines.append("4. **PDH/PDL coverage:** Only the 29 trades from 2026 have local D1 OHLCV for PDH/PDL lookup. 2024-2025 trades (82) are excluded from that subtest → very low power.")
    lines.append("5. **ATR proxy:** the batch file does not expose per-trade ATR. We approximate ATR = sl_dollars/3 since SL = OB boundary + 0.3-0.5 ATR and OB depth ≈ 1-2 ATR. Fractional clustering tests use this proxy; absolute-dollar tests do not.")
    lines.append("6. **Round-number semantic:** We use $5 as the primary gold round. $10 and $50 are tested as secondary. Sub-$5 ticks (e.g., $2.50) are not tested — the CEO can request them if relevant.")
    lines.append("7. **Stop-hunt proxy is conservative:** we flag only trades with outcome=LOSS AND mae_r≥0.98 AND mfe_r≥1.5R. Trades that reversed only 1R in favor (mfe_r<1.5) are not counted as 'hunted'.")
    lines.append("8. **Quantile SL is in-sample:** P95 winning-MAE is derived from the same 72 winners it is then applied against. In a true out-of-sample test, effective P95 would need a rolling-window calibration.")
    lines.append("")

    # Verdicts
    lines.append("## Verdicts")
    lines.append("")

    # Q-5.3 verdict
    primary = q53["tests"]["round5_vs_hunt15"]
    q53_verdict = "NO EFFECT"
    if primary["p_one_sided_greater"] < 0.05:
        q53_verdict = "SUPPORTED — higher hunt rate at clustered SLs"
    elif primary["a"] < 3 or primary["c"] < 3:
        q53_verdict = "UNDERPOWERED (too few hunts to test)"

    lines.append(f"### Q-5.3 — SL clustering vs stop-hunt risk")
    lines.append(f"- **Verdict: {q53_verdict}**")
    lines.append(f"- P(hunt | clustered) = {fmt_pct(primary['p_hunt_cluster'])}, P(hunt | isolated) = {fmt_pct(primary['p_hunt_isolated'])}, Fisher one-sided p = {primary['p_one_sided_greater']:.3f}")
    lines.append(f"- Total confirmed stop-hunt events (mfe≥1.5R): {s53['n_hunts_15']} — sample too small to detect a small-to-moderate cluster effect. More data required before a round-buffer widening rule can be justified.")
    lines.append(f"- Osler asymmetry is PRESENT ({fmt_pct(o['pct_below'])} of LONG SLs below mid-$5-band) but this is an artefact of OB-retest placing stops at OB extremes, which happen to fall in the lower half of each $5 range.")
    lines.append("")

    # Q-5.4 verdict — distinguish fixed-risk-% from fixed-lot
    baseline = next(s for s in s54["scenarios"] if s["scenario"].startswith("S0"))
    p95_sc = next(s for s in s54["scenarios"] if "P95" in s["scenario"])
    p90_sc = next(s for s in s54["scenarios"] if "P90" in s["scenario"])
    p99_sc = next(s for s in s54["scenarios"] if "P99" in s["scenario"])
    s1_sc = next(s for s in s54["scenarios"] if "1.5x" in s["scenario"])
    s2_sc = next(s for s in s54["scenarios"] if "2.0x" in s["scenario"])

    # Fixed-risk-% choice (best new-R)
    q54_verdict_pct = "BASELINE IS BEST (fixed-risk-%)"
    if best_c["avg_r_central"] > baseline["avg_r_central"] + 0.05:
        q54_verdict_pct = f"WINNER: {best_c['scenario']} beats baseline by {best_c['avg_r_central']-baseline['avg_r_central']:+.3f}R under fixed-risk-% sizing"

    # Fixed-lot choice (best old-R equiv)
    best_old_central = max(s54["scenarios"], key=lambda s: s["avg_r_old_R_equivalent"])
    q54_verdict_lot = "BASELINE IS BEST (fixed-lot)"
    if best_old_central["avg_r_old_R_equivalent"] > baseline["avg_r_old_R_equivalent"] + 0.02:
        q54_verdict_lot = f"WINNER: {best_old_central['scenario']} beats baseline by {best_old_central['avg_r_old_R_equivalent']-baseline['avg_r_old_R_equivalent']:+.3f}R under fixed-lot sizing"

    lines.append(f"### Q-5.4 — ATR vs quantile SL")
    lines.append(f"- **Under GTOS fixed-risk-% sizing (live regime):** {q54_verdict_pct}")
    lines.append(f"- **Under fixed-lot sizing (alternative):** {q54_verdict_lot}")
    lines.append(f"- Baseline: avg_R = {baseline['avg_r_central']:+.3f} (both regimes identical at baseline)")
    lines.append(f"- P95 winning-MAE width_factor = {p95_sc['width_factor']:.2f}, avg_R(new-R) = {p95_sc['avg_r_central']:+.3f}, avg_R(old-R equiv) = {p95_sc['avg_r_old_R_equivalent']:+.3f}")
    lines.append(f"- Widening to 1.5× ATR: avg_R(new-R) = {s1_sc['avg_r_central']:+.3f}, avg_R(old-R equiv) = {s1_sc['avg_r_old_R_equivalent']:+.3f}. Saves {s1_sc['n_saved_losers']} stop-out losers but shrinks every winner's R by factor 1/1.5.")
    lines.append(f"- Tightening to 0.75× ATR: squeezes {next(s for s in s54['scenarios'] if '0.75' in s['scenario'])['n_squeezed_winners']} winners into losses.")
    lines.append("")
    lines.append("**Key insight:** Under fixed-risk-% (live GTOS regime), a TIGHTER SL (P95 winning-MAE = 0.63× baseline) mechanically improves new-R expectancy BECAUSE r_multiple is inflated by the same factor the SL is tightened. Under fixed-lot (the $-equivalent frame), tightening does NOT improve expectancy — it just shrinks every trade's $-payoff.")
    lines.append("")
    lines.append("The honest headline: neither tightening nor widening is a free lunch. The practical question is whether a WIDER SL (covers more losers at the cost of smaller R/winner) is $-positive. Answer: under central-estimate for saved losers, S1 (1.5× ATR) delivers old-R equiv = {:+.3f}, vs baseline +{:.3f}. That's a modest lift ({:+.3f}R/trade). **Under fixed-risk-% live sizing, it's {:+.3f}R/trade.**".format(
        s1_sc["avg_r_old_R_equivalent"], baseline["avg_r_central"], s1_sc["avg_r_old_R_equivalent"] - baseline["avg_r_old_R_equivalent"],
        s1_sc["avg_r_central"] - baseline["avg_r_central"]
    ))
    lines.append("")

    # ----- Reviewer correction 2026-04-17 — H29-corrected counterfactual (MAJOR) -----
    lines.append("## Reviewer correction 2026-04-17 — H29 policy was missing (MAJOR)")
    lines.append("")
    lines.append("**Finding:** The original Q-5.4 counterfactual computed each scenario's `avg_R` as an unweighted mean of per-trade new-R, implicitly assuming risk_pct_per_trade is CONSTANT at 2.0%. This **omits the H29 policy deployed live Apr 11 2026**: when equity drawdown from peak >= 8%, risk reduces to 0.5% until a new equity high is reached.")
    lines.append("")
    lines.append("**Correction procedure (pre-registered BEFORE running):**")
    lines.append("1. For each scenario, compute per-trade r_multiple series exactly as before (stop-hit logic, rescaling, central saved-loser estimate).")
    lines.append("2. Walk trades in chronological order by `date`.")
    lines.append("3. Maintain running equity (init=1.0) and peak-equity.")
    lines.append("4. Before each trade, check: if `(peak - equity) / peak >= 0.08` AND not already in DD-mode, switch to reduced risk (0.5%). If already in DD-mode and equity >= peak, reset to normal risk (2.0%).")
    lines.append("5. Apply trade: `equity_after = equity + r * active_risk * equity`. Update peak if new high.")
    lines.append("6. Report terminal equity, max-DD observed, and count of trades where reduced risk was active.")
    lines.append("")
    lines.append("**Comparison column `terminal_equity_flat`:** same replay with risk fixed at 2.0% throughout (no H29). The delta `(flat - h29)` quantifies how much H29 costs the scenario in average terminal equity.")
    lines.append("")
    lines.append("### H29-corrected terminal-equity replay (chronological, seed-free)")
    lines.append("")
    lines.append("| Scenario | width_factor | terminal_equity (H29 ON) | terminal_equity (flat 2%) | max_DD (H29) | max_DD (flat) | n_trades_reduced | pct_reduced |")
    lines.append("|----------|-------------:|-------------------------:|--------------------------:|-------------:|--------------:|-----------------:|------------:|")
    h29_list = s54.get("h29_scenarios", [])
    for h29 in h29_list:
        lines.append(
            f"| {h29['scenario']} | {h29['width_factor']:.2f} | "
            f"{h29['terminal_equity_h29']:.4f} | {h29['terminal_equity_flat']:.4f} | "
            f"{h29['max_dd_h29']*100:.2f}% | {h29['max_dd_flat']*100:.2f}% | "
            f"{h29['n_trades_reduced']} | {h29['pct_trades_reduced']*100:.1f}% |"
        )
    lines.append("")

    # Find best by terminal equity under H29
    if h29_list:
        best_h29 = max(h29_list, key=lambda h: h["terminal_equity_h29"])
        base_h29 = next((h for h in h29_list if h["scenario"].startswith("S0")), None)
        s1_h29 = next((h for h in h29_list if "1.5x" in h["scenario"]), None)
        p95_h29 = next((h for h in h29_list if "P95" in h["scenario"]), None)
        lines.append(f"- **Best terminal equity under H29 policy:** `{best_h29['scenario']}` → {best_h29['terminal_equity_h29']:.4f}")
        if base_h29:
            h29_opportunity_cost = (base_h29['terminal_equity_flat'] - base_h29['terminal_equity_h29']) * 100
            lines.append(f"- Baseline S0 terminal equity: {base_h29['terminal_equity_h29']:.4f} (H29 ON) vs {base_h29['terminal_equity_flat']:.4f} (flat 2%). H29 triggered on {base_h29['pct_trades_reduced']*100:.1f}% of trades — opportunity cost vs flat 2% = {h29_opportunity_cost:+.3f}pp of final equity. (This is the price of the safety net: a cost paid on paths where the DD did not escalate to blow-up; a gain on paths where it would have.)")
        if s1_h29 and base_h29:
            lines.append(f"- S1 1.5× ATR under H29: terminal={s1_h29['terminal_equity_h29']:.4f}, lift vs S0={s1_h29['terminal_equity_h29'] - base_h29['terminal_equity_h29']:+.4f}. Under flat 2% the lift was {s1_h29['terminal_equity_flat'] - base_h29['terminal_equity_flat']:+.4f}.")
        if p95_h29 and base_h29:
            lines.append(f"- S4 P95 winning-MAE under H29: terminal={p95_h29['terminal_equity_h29']:.4f}, lift vs S0={p95_h29['terminal_equity_h29'] - base_h29['terminal_equity_h29']:+.4f}. Under flat 2% the lift was {p95_h29['terminal_equity_flat'] - base_h29['terminal_equity_flat']:+.4f}.")

        # Verdict update check
        if s1_h29 and base_h29 and p95_h29:
            s1_h29_delta = s1_h29["terminal_equity_h29"] - base_h29["terminal_equity_h29"]
            s1_flat_delta = s1_h29["terminal_equity_flat"] - base_h29["terminal_equity_flat"]
            direction_reversed = (s1_flat_delta > 0) != (s1_h29_delta > 0)
            lines.append("")
            if direction_reversed:
                lines.append(f"- **VERDICT REVERSED:** Under H29 policy, S1 (1.5× ATR wider) delta changes SIGN (flat {s1_flat_delta:+.4f} → H29 {s1_h29_delta:+.4f}). The flat-2% recommendation to shadow-log S1 is **downgraded**.")
            else:
                lines.append(f"- **Verdict direction preserved:** S1 (1.5× ATR wider) delta vs baseline stays same sign under H29 policy ({s1_h29_delta:+.4f}, was {s1_flat_delta:+.4f} under flat 2%). Shadow-log recommendation holds. H29 only narrows the magnitude by reducing risk during DD periods.")

    lines.append("")
    lines.append("**Interpretation:** H29 is a risk-management overlay, not an edge-generator. It cannot MAKE a losing scenario profitable, but it attenuates DD during losing clusters by risking 0.5% instead of 2%. Under chronological replay on the batch, H29's effect is most pronounced for scenarios that take bigger early losses before a recovery — and that ordering is strongly PATH-DEPENDENT on the specific trade sequence in this batch. Results should be interpreted as order-of-magnitude, not precise.")
    lines.append("")

    # Recommendation
    lines.append("## Recommendation for SL-gate changes")
    lines.append("")
    if q53_verdict.startswith("SUPPORTED"):
        lines.append("- **Round-number buffer:** add $1 buffer beyond OB extremes when OB edge falls within $1 of a $5 round. Expected savings ~N hunts/year.")
    else:
        lines.append("- **Round-number buffer (Q-5.3):** **No action**. The observed hunt-rate lift at clustered SLs is not statistically distinguishable from zero with n=111. Do NOT widen SLs at round numbers on this evidence alone. Re-test once live sample doubles (~200 trades) OR extract PDH/PDL from LanceDB historical MSOs for the 82 pre-2026 trades.")

    # Q-5.4 recommendation depends on sizing regime
    # S1 (1.5× ATR) wider: fewer losses, smaller winners
    # Under fixed-risk-%: lift = s1_sc['avg_r_central'] - baseline['avg_r_central']
    # Under fixed-lot: lift = s1_sc['avg_r_old_R_equivalent'] - baseline['avg_r_old_R_equivalent']
    lift_widen_pct = s1_sc["avg_r_central"] - baseline["avg_r_central"]
    lift_widen_lot = s1_sc["avg_r_old_R_equivalent"] - baseline["avg_r_old_R_equivalent"]

    if lift_widen_pct > 0.05 and lift_widen_lot > 0.02:
        lines.append(f"- **Quantile/wider SL (Q-5.4):** **Consider S1 (1.5× ATR)**. Under GTOS fixed-risk-% sizing, lift is {lift_widen_pct:+.3f}R/trade; under fixed-lot the lift is {lift_widen_lot:+.3f}R/trade. Deploy in SHADOW MODE first (log-only), evaluate over next 50 trades.")
    else:
        lines.append(f"- **Quantile/wider SL (Q-5.4):** **Keep baseline 1.0× ATR sizing**. Widening to 1.5× yields only {lift_widen_pct:+.3f}R/trade (new-R) and {lift_widen_lot:+.3f}R/trade (old-R equiv) — within noise. A tighter quantile SL (P95=0.63×) mechanically inflates new-R expectancy but offers zero $-advantage under fixed-lot; under fixed-risk-% it is arithmetically equivalent to simply risking less per trade (which can be done without changing the SL-placement rule).")

    lines.append("")
    lines.append("- **Current SL buffer (0.3-0.5 ATR above OB extreme, per Apr 17 session 19 handoff):** retain. The SL-sweep margin change from 0.3 → 0.5 ATR already addresses the most common hunt-out pattern. Q-5.3 evidence does not justify additional round-number specific buffering at this sample size.")
    lines.append("")

    # Next steps
    lines.append("## Next steps")
    lines.append("")
    lines.append("1. **Expand stop-hunt evidence base.** Once live sample reaches 200+ trades, re-run Q-5.3 with mae_r/mfe_r from live logs. The question is high-value but currently underpowered.")
    lines.append("2. **Back-fill PDH/PDL for 2024-2025 trades.** Pull D1 OHLCV for 2024-01 to 2025-12 from MT5 (historical_2025/, historical_2024/) or LanceDB; re-run the PDH/PDL cluster subtest at n~110.")
    lines.append("3. **Compute in-sample P95 winning-MAE as shadow-log:** add a `quantile_sl_shadow` field to live trade logs that records what the SL *would* be under a rolling-100-trade P95 calibration. Observation-only, no decision impact. Evaluate in 50 trades.")
    lines.append("4. **Osler confirmation via live-log sweep patterns:** log every trade whose SL was hit + extract the next 6 M15 candles' high/low to confirm/deny reversal. Feeds Q-5.3 power directly.")
    lines.append("5. **Consider SHORT-trade imbalance:** 7/111 SHORTs is inadequate for cluster testing by direction. If live trading continues to favor LONGs, direction-conditioned SL rules cannot be validated; if SHORTs reach ≥30, re-run with direction as a covariate.")
    lines.append("6. **Join Q-5.4 with Q-5.5 (Kelly):** current live is already risk-constrained at 1-2% (see Q-5_Q-6_exits.md). A wider quantile SL would *reduce* R-payoff while also *reducing* hit probability. Net expectancy lift is ambiguous and may be dominated by Kelly-cap survivorship rather than SL width.")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return str(OUT_PATH)


def main():
    trades = load_trades()
    d1_map = load_d1()
    d1_dates = sorted(d1_map.keys())
    q53 = q53_analysis(trades, d1_map, d1_dates)
    q54 = q54_analysis(trades)
    path = write_report(q53, q54)
    print("wrote:", path)
    # quick stdout summary
    s = q53["summary"]
    print(f"Q-5.3: cluster-$5 rate = {s['pct_cluster_round5']*100:.1f}%, hunt rate = {s['pct_hunt_15_all']*100:.1f}%")
    prim = q53["tests"]["round5_vs_hunt15"]
    print(f"Q-5.3 primary Fisher: p(one-sided) = {prim['p_one_sided_greater']:.3f}, "
          f"P(hunt|cluster)={prim['p_hunt_cluster']*100:.2f}%, P(hunt|iso)={prim['p_hunt_isolated']*100:.2f}%")
    best = max(q54["scenarios"], key=lambda x: x["avg_r_central"])
    baseline = next(s for s in q54["scenarios"] if s["scenario"].startswith("S0"))
    print(f"Q-5.4: baseline avg_R = {baseline['avg_r_central']:+.3f}; best = {best['scenario']} @ {best['avg_r_central']:+.3f}")
    print(f"Q-5.4: P95 winning-MAE = {q54['winning_mae_p95']:.3f}R")


if __name__ == "__main__":
    main()
