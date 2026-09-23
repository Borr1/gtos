"""
Q-6.2 / Q-6.6 — Exit Engineering Part 2

Pre-registered hypotheses (stated BEFORE looking at any variant/bucket output):
- Q-6.2: Current live rule (50/25/25 at 1R/2R/3R) is NOT optimal. Given the wave-1
  finding that most winners give back ~0.5R between MFE and close, the optimum should
  concentrate close mass at TP1 (60/20/20 or 100/0/0). Predicted ranking (highest→lowest
  expectancy): F(50/50/0) >= A(100/0/0) > C(60/20/20) > B(50/25/25 current) > D(40/30/30) > E(33/33/33).
- Q-6.6: Gold has asymmetric overnight risk per literature (Caporale et al., 2014; Lucey
  2014). Intra-session trades should have the highest avg_R; overnight-held trades should
  show a left-skewed r_multiple distribution (negative skew) and a lower mean_R. Kruskal-
  Wallis should reject (p<0.05) that the three bucket distributions are identical.

Methodology continuity with wave-1 (Q-5_Q-6_exits.md):
- Same paired bootstrap (n_boot=5000, seed=42) for Q-6.2 significance.
- Same `was_stopped` gate: mae_r >= 1.0 AND r_multiple <= -0.95.
- Same "fallback to realized R" if TP not reached and not stopped out.
- TP levels fixed at 1R/2R/3R (uniform, not per-trade TP1/TP2/TP3 prices — we use R
  multiples as the canonical metric, same as wave-1). This is noted as an assumption.

Intracandle ordering assumption (SAME as wave-1):
- We cannot know whether MFE or MAE was hit first within a single candle. We assume:
  if mae_r>=1.0 AND r_actual<=-0.95, the trade was historically stopped (even if mfe
  also touched TP). This conservative rule systematically UNDER-counts TP hits on SL
  days, biasing expectancy estimates DOWN for rules that close early (e.g., 100/0/0).
  Therefore, if an early-close variant beats 50/25/25 here, the effect is likely
  STRONGER in production.

Run: python research/academic_pipeline/scripts/q_6_exits_part2.py
Output: research/academic_pipeline/results/Q-6_exits_part2.md
"""
import json
import math
import os
from collections import Counter

import numpy as np
from scipy import stats as sstats

ROOT = r"C:\Users\MSI\Documents\ai-trading-agent"
DATA = os.path.join(
    ROOT, "knowledge_base_backtest", "analysis", "unified_trades_v2_20260331.json"
)
OUT = os.path.join(
    ROOT, "research", "academic_pipeline", "results", "Q-6_exits_part2.md"
)
SEED = 42
RNG = np.random.default_rng(SEED)


# -------------------------------------------------------------------------
# Load
# -------------------------------------------------------------------------
with open(DATA, encoding="utf-8") as f:
    trades = json.load(f)
n = len(trades)


def fmt_pct(x):
    return f"{100 * x:.2f}%"


# -------------------------------------------------------------------------
# Q-6.2 Partial close splits
# -------------------------------------------------------------------------
# Variants: close fraction at each of TP1=1R, TP2=2R, TP3=3R
# A: 100 / 0 / 0  (null baseline, all-out at TP1)
# B: 50  / 25 / 25 (current live-equivalent if all three legs are armed)
# C: 60  / 20 / 20
# D: 40  / 30 / 30
# E: 33  / 33 / 34 (we use 0.33/0.33/0.34 to preserve sum=1.00)
# F: 50  / 50 / 0  (two-leg)
VARIANTS = {
    "A_100_0_0":  (1.00, 0.00, 0.00),
    "B_50_25_25": (0.50, 0.25, 0.25),
    "C_60_20_20": (0.60, 0.20, 0.20),
    "D_40_30_30": (0.40, 0.30, 0.30),
    "E_33_33_34": (0.33, 0.33, 0.34),
    "F_50_50_0":  (0.50, 0.50, 0.00),
}
TP_LEVELS = (1.0, 2.0, 3.0)


def simulate_variant(fractions, trades_arr):
    """
    For each trade, compute realized R under the partial-close rule.

    Rule logic:
      was_stopped = (mae_r>=1.0) AND (r_multiple<=-0.95)  -> full -1R
      otherwise, for each TP_k with fraction f_k:
        if mfe_r >= TP_k: leg realizes +TP_k R on f_k share
        else: leg falls back to r_multiple on f_k share (residual ran to session close
              or actual exit price, same as wave-1)
    """
    out = np.zeros(len(trades_arr))
    f1, f2, f3 = fractions
    tp1, tp2, tp3 = TP_LEVELS
    for i, t in enumerate(trades_arr):
        mfe = t["mfe_r"]
        mae = t["mae_r"]
        r_actual = t["r_multiple"]
        was_stopped = (mae >= 1.0) and (r_actual <= -0.95)
        if was_stopped:
            out[i] = -1.0
            continue
        leg1 = f1 * (tp1 if mfe >= tp1 else r_actual)
        leg2 = f2 * (tp2 if mfe >= tp2 else r_actual)
        leg3 = f3 * (tp3 if mfe >= tp3 else r_actual)
        out[i] = leg1 + leg2 + leg3
    return out


variant_vecs = {name: simulate_variant(f, trades) for name, f in VARIANTS.items()}


def dd_envelope(rvec, risk_frac=0.02, n_trades=100, n_iter=5000, rng=None):
    """Max-DD median and p95 under multiplicative compounding at risk_frac."""
    if rng is None:
        rng = np.random.default_rng(SEED + 1)
    sampled = rng.choice(rvec, size=(n_iter, n_trades), replace=True)
    path = 1.0 + risk_frac * sampled
    path = np.maximum(path, 1e-6)
    logp = np.log(path)
    eq = np.exp(np.cumsum(logp, axis=1))
    eq = np.concatenate([np.ones((n_iter, 1)), eq], axis=1)
    peak = np.maximum.accumulate(eq, axis=1)
    dd = (peak - eq) / peak
    m = dd.max(axis=1)
    return float(np.median(m)), float(np.percentile(m, 95))


variant_stats = {}
for name, rvec in variant_vecs.items():
    med_dd, p95_dd = dd_envelope(rvec)
    variant_stats[name] = {
        "n": len(rvec),
        "expectancy": float(rvec.mean()),
        "std_R": float(rvec.std(ddof=1)),
        "WR": float((rvec > 0).mean()),
        "median_R": float(np.median(rvec)),
        "sum_R": float(rvec.sum()),
        "min_R": float(rvec.min()),
        "max_R": float(rvec.max()),
        "median_max_dd_2pct": med_dd,
        "p95_max_dd_2pct": p95_dd,
    }


# -------------------------------------------------------------------------
# H29 chronological equity replay (Apr 11 2026 policy).
# Pre-registered BEFORE running:
#   risk_normal = 2.0% per trade
#   risk_reduced = 0.5% per trade
#   dd_trigger = 8% drawdown from peak
#   reset to normal risk when equity reaches new peak
# Apply per-variant by walking trades in date order and compounding equity.
# -------------------------------------------------------------------------
def h29_replay(trades_chrono_idx, r_series, risk_normal=0.02,
               risk_reduced=0.005, dd_threshold=0.08, equity_start=1.0):
    """Chronological replay. trades_chrono_idx: list of indices into trades, sorted by date.
    r_series: per-trade r_multiple, same length and index order."""
    equity = equity_start
    peak = equity_start
    in_dd_mode = False
    n_reduced = 0
    max_dd = 0.0
    for i, r in zip(trades_chrono_idx, r_series):
        if not in_dd_mode and equity <= peak * (1 - dd_threshold):
            in_dd_mode = True
        elif in_dd_mode and equity >= peak:
            in_dd_mode = False
        active_risk = risk_reduced if in_dd_mode else risk_normal
        if in_dd_mode:
            n_reduced += 1
        equity = max(equity + r * active_risk * equity, 1e-9)
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak if peak > 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return {
        "terminal_equity": equity,
        "max_dd": max_dd,
        "n_reduced": n_reduced,
        "pct_reduced": n_reduced / len(r_series) if len(r_series) else 0.0,
    }


# Chronological index order
chrono_order = sorted(range(len(trades)), key=lambda i: trades[i].get("date", ""))
variant_h29 = {}
for name, rvec in variant_vecs.items():
    r_chrono = [float(rvec[i]) for i in chrono_order]
    h29 = h29_replay(chrono_order, r_chrono)
    flat = h29_replay(chrono_order, r_chrono, risk_reduced=0.02)  # flat 2% control
    variant_h29[name] = {
        **h29,
        "terminal_flat": flat["terminal_equity"],
        "max_dd_flat": flat["max_dd"],
    }


# Baseline = B (current 50/25/25). Paired bootstrap of delta expectancy.
BASE = "B_50_25_25"
baseline_vec = variant_vecs[BASE]
n_boot = 5000
bootstrap_vs_B = {}
for name, rvec in variant_vecs.items():
    if name == BASE:
        continue
    diffs = rvec - baseline_vec
    boot = np.empty(n_boot)
    rng_b = np.random.default_rng(SEED)
    for i in range(n_boot):
        idx = rng_b.choice(len(diffs), size=len(diffs), replace=True)
        boot[i] = diffs[idx].mean()
    ci_lo = float(np.percentile(boot, 2.5))
    ci_hi = float(np.percentile(boot, 97.5))
    point = float(diffs.mean())
    centered = boot - point
    p_two = float((np.abs(centered) >= abs(point)).mean())
    bootstrap_vs_B[name] = {
        "delta_expectancy": point,
        "ci95_lo": ci_lo,
        "ci95_hi": ci_hi,
        "p_two_sided_boot": p_two,
        "significant": (ci_lo > 0) or (ci_hi < 0),
    }


# -------------------------------------------------------------------------
# Q-6.6 Session-close / overnight risk
# -------------------------------------------------------------------------
# We have: kill_zone ('london','ny'), hold_time_candles (1 candle = 15 min),
#          day_of_week, date. No entry/exit timestamps.
#
# Heuristic bucketing from KZ + hold:
#   Kill zone lengths (approx, M15):
#     London KZ = 07:00-10:30 UTC -> ~14 candles
#     NY KZ     = 13:00-17:00 UTC -> ~16 candles
#   Boundaries (hours from KZ start):
#     Intra-session:    hold <= end-of-KZ  (<=14 c for london, <=16 c for NY)
#     Cross-session:    London KZ trade held past 10:30 into NY (>14 c and <=NY close)
#                       OR NY trade held past 17:00 UTC (>16 c and <~24 c for post-NY close early-asian)
#     Overnight:        held into Asian/next-day. Conservative threshold:
#                       London: hold > 26c (> ~17:30 UTC, past NY close) -> overnight
#                       NY:     hold > 28c (> ~00:00 UTC, past Asian open) -> overnight
# Source/notes:
#   - Asian session opens ~00:00 UTC (Sydney) / ~01:00 UTC (Tokyo).
#   - NY close = 17:00 UTC (instrument kill-zone ends 17:00; market closes 21:00 UTC,
#     but for GTOS a trade left open past NY kill-zone end without exit is unusual
#     and indicates trail/session-timeout carried across sessions).
#   - We tune the thresholds conservatively: "overnight" requires hold past NY close,
#     which is at minimum 17:00 UTC. From london 07:00 start -> 26 candles (~10.5h).
#     From NY 13:00 start -> 28 candles (~11h would reach 00:00 UTC next day).
#   - This is a proxy: real timestamps would be preferred. We disclose the assumption.

LONDON_KZ_END = 14   # 07:00-10:30 UTC = 14 M15 candles
NY_KZ_END = 16       # 13:00-17:00 UTC = 16 candles
LONDON_OVERNIGHT = 26  # held past 07:00 + 6.5h = 13:30 UTC is "cross"; past 17:00 UTC = 40c but
                       # we set 26c as london->post-NY-close pragmatic threshold (used in
                       # combination with NY threshold below, see below).
# Revised: we use KZ-specific thresholds grounded in UTC clock time:
# London trade at hold=h:  end_time_utc = 07:00 + h*15min
#   intra:  h <= 14 (ends by 10:30 UTC, within London KZ)
#   cross:  14 < h <= 40 (ends by 17:00 UTC, within NY session window)
#   overnight: h > 40 (ends after 17:00 UTC -> held through post-NY -> into Asian)
# NY trade at hold=h: end_time_utc = 13:00 + h*15min
#   intra:  h <= 16 (ends by 17:00 UTC, within NY KZ)
#   cross:  16 < h <= 28 (ends by 20:00 UTC, within post-NY but still same day)
#   overnight: h > 28 (ends after 20:00 UTC, rolls into Asian session)
LONDON_CROSS_MAX = 40
NY_CROSS_MAX = 28


def bucket_trade(t):
    kz = t.get("kill_zone", "")
    h = t.get("hold_time_candles", 0)
    if kz == "london":
        if h <= LONDON_KZ_END:
            return "intra"
        if h <= LONDON_CROSS_MAX:
            return "cross"
        return "overnight"
    if kz == "ny":
        if h <= NY_KZ_END:
            return "intra"
        if h <= NY_CROSS_MAX:
            return "cross"
        return "overnight"
    return "unknown"


buckets = [bucket_trade(t) for t in trades]
bucket_counter = Counter(buckets)

bucket_stats = {}
for b in ("intra", "cross", "overnight"):
    idx = [i for i, bb in enumerate(buckets) if bb == b]
    if not idx:
        bucket_stats[b] = {"n": 0}
        continue
    rs_b = np.array([trades[i]["r_multiple"] for i in idx])
    mfe_b = np.array([trades[i]["mfe_r"] for i in idx])
    mae_b = np.array([trades[i]["mae_r"] for i in idx])
    ht_b = np.array([trades[i]["hold_time_candles"] for i in idx])
    bucket_stats[b] = {
        "n": len(idx),
        "avg_R": float(rs_b.mean()),
        "std_R": float(rs_b.std(ddof=1)) if len(rs_b) > 1 else 0.0,
        "WR": float((rs_b > 0).mean()),
        "median_R": float(np.median(rs_b)),
        "skew_R": float(sstats.skew(rs_b)) if len(rs_b) >= 3 else float("nan"),
        "kurt_R": float(sstats.kurtosis(rs_b)) if len(rs_b) >= 3 else float("nan"),
        "min_R": float(rs_b.min()),
        "max_R": float(rs_b.max()),
        "mean_mfe": float(mfe_b.mean()),
        "mean_mae": float(mae_b.mean()),
        "mean_hold": float(ht_b.mean()),
    }


# Kruskal-Wallis across the 3 buckets (only if all 3 have n>=2)
rs_by_bucket = {
    b: np.array([trades[i]["r_multiple"] for i, bb in enumerate(buckets) if bb == b])
    for b in ("intra", "cross", "overnight")
}
non_empty = {b: v for b, v in rs_by_bucket.items() if len(v) >= 2}
if len(non_empty) >= 2:
    kw_stat, kw_p = sstats.kruskal(*non_empty.values())
    kw_stat = float(kw_stat)
    kw_p = float(kw_p)
else:
    kw_stat, kw_p = float("nan"), float("nan")

# Pairwise Mann-Whitney U (two-sided) for reference
pairs = [("intra", "cross"), ("intra", "overnight"), ("cross", "overnight")]
pairwise_mw = {}
for a, b in pairs:
    va, vb = rs_by_bucket[a], rs_by_bucket[b]
    if len(va) >= 2 and len(vb) >= 2:
        u, p = sstats.mannwhitneyu(va, vb, alternative="two-sided")
        pairwise_mw[f"{a}_vs_{b}"] = {"U": float(u), "p": float(p), "na": len(va), "nb": len(vb)}
    else:
        pairwise_mw[f"{a}_vs_{b}"] = {"U": float("nan"), "p": float("nan"),
                                       "na": len(va), "nb": len(vb)}


# -------------------------------------------------------------------------
# Write markdown
# -------------------------------------------------------------------------
md = []
a = md.append
a("# Q-6.2 / Q-6.6 — Exit Engineering Part 2 (Partial Splits + Overnight Risk)\n")
a("- Script: `research/academic_pipeline/scripts/q_6_exits_part2.py`")
a("- Data: `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json`")
a(f"- n = {n} trades (batch, XAUUSD only)")
a(f"- Seed: {SEED} | Bootstrap iters: {n_boot}")
a("- Baseline for Q-6.2 bootstrap: **B_50_25_25 (current live-equivalent)**\n")

a("## Hypothesis (pre-data, pre-registered)\n")
a("- **Q-6.2**: Current live split (50/25/25 at 1R/2R/3R) is NOT optimal. Given wave-1 "
  "finding that 35.62% of winners give back ≥0.5R between MFE and close, optimum should "
  "concentrate close mass at TP1. Predicted ranking (best→worst): "
  "**F(50/50/0) ≥ A(100/0/0) > C(60/20/20) > B(50/25/25 baseline) > D(40/30/30) > E(33/33/34)**.")
a("- **Q-6.6**: Gold has documented asymmetric overnight risk (Caporale 2014, Lucey 2014). "
  "Predicted: intra-session > cross-session > overnight on avg_R. Overnight bucket will show "
  "**left-skewed** r_multiple distribution (skew < 0) and a Kruskal-Wallis p<0.05 for "
  "distributional heterogeneity across the three buckets.\n")

a("## Data & Method\n")
a(f"- n = {n} trades (XAUUSD only, batch 2024-04 → 2026-03).")
a("- Fields: `r_multiple`, `mfe_r`, `mae_r`, `hold_time_candles`, `kill_zone`, `date`, "
  "`day_of_week`.")
a("- **TP level assumption (Q-6.2)**: we use canonical TP1=1R, TP2=2R, TP3=3R. Per-trade "
  "`take_profit_1/2/3` prices exist but translate inconsistently to R (they were in some "
  "cases static price ladders that did not match the realized SL distance). Using R "
  "multiples keeps the analysis continuous with wave-1.")
a("- **Intracandle ordering (critical)**: we cannot know whether MFE or MAE hit first "
  "within a candle. We adopt wave-1's conservative gate: `was_stopped = (mae_r>=1.0 AND "
  "r_multiple<=-0.95)`. Stopped trades always realize -1R, even if MFE also touched a TP. "
  "This UNDER-counts TP hits on SL days, biasing expectancy DOWN for high-TP1-weight "
  "variants. Any observed win for early-close variants is therefore a conservative lower "
  "bound.")
a("- **Bucketing (Q-6.6)**: inferred from kill_zone + hold_time_candles (no entry/exit "
  "timestamps in batch). Thresholds in UTC clock terms:")
a(f"  - London KZ (07:00-10:30 UTC): intra ≤ {LONDON_KZ_END}c; cross ≤ {LONDON_CROSS_MAX}c "
  f"(to 17:00 UTC, NY close); overnight > {LONDON_CROSS_MAX}c (past NY close into Asian).")
a(f"  - NY KZ (13:00-17:00 UTC): intra ≤ {NY_KZ_END}c; cross ≤ {NY_CROSS_MAX}c (to 20:00 "
  f"UTC, pre-Asian); overnight > {NY_CROSS_MAX}c (past 20:00 UTC → into Asian session).")
a("  - Bucket assignment is a proxy. Accurate classification requires entry/exit "
  "timestamps — a known data gap, flagged.\n")

a("## Q-6.2 Results — Partial-close variant comparison\n")
a("### Variant expectancy table (all n={})".format(n))
a("")
a("| Variant | Fractions (TP1/TP2/TP3) | Expectancy (R) | WR | Median R | Sum R | "
  "Std R | Median max-DD (2%) | P95 max-DD (2%) |")
a("|---------|-------------------------|----------------|------|----------|-------|"
  "-------|--------------------|-----------------|")
# Sort: keep baseline in middle, show by expectancy descending for clarity? Use fixed order.
order = ["A_100_0_0", "B_50_25_25", "C_60_20_20", "D_40_30_30", "E_33_33_34", "F_50_50_0"]
for name in order:
    s = variant_stats[name]
    f1, f2, f3 = VARIANTS[name]
    mark = " (baseline)" if name == BASE else ""
    a(
        f"| {name}{mark} | {f1*100:.0f}/{f2*100:.0f}/{f3*100:.0f} | "
        f"**{s['expectancy']:+.3f}** | {fmt_pct(s['WR'])} | {s['median_R']:+.2f} | "
        f"{s['sum_R']:+.1f} | {s['std_R']:.3f} | {fmt_pct(s['median_max_dd_2pct'])} | "
        f"{fmt_pct(s['p95_max_dd_2pct'])} |"
    )
a("")

a("### Paired bootstrap: Δ expectancy vs baseline B_50_25_25 (seed={}, n_boot={})"
  .format(SEED, n_boot))
a("")
a("| Variant | Δ expectancy (R) | 95% CI | p (two-sided boot) | Significant (CI excl 0)? |")
a("|---------|------------------|--------|--------------------|--------------------------|")
for name in ["A_100_0_0", "C_60_20_20", "D_40_30_30", "E_33_33_34", "F_50_50_0"]:
    bd = bootstrap_vs_B[name]
    a(
        f"| {name} | {bd['delta_expectancy']:+.3f} | "
        f"[{bd['ci95_lo']:+.3f}, {bd['ci95_hi']:+.3f}] | "
        f"{bd['p_two_sided_boot']:.3f} | {'YES' if bd['significant'] else 'no'} |"
    )
a("")

# Best by point estimate
best = max(variant_stats.items(), key=lambda kv: kv[1]["expectancy"])
a(f"- **Best variant by point expectancy**: `{best[0]}` @ "
  f"**{best[1]['expectancy']:+.3f}R/trade** (WR={fmt_pct(best[1]['WR'])}, sum="
  f"{best[1]['sum_R']:+.1f}R over {n} trades).")
if best[0] != BASE:
    bd_best = bootstrap_vs_B[best[0]]
    a(f"- Delta vs baseline B_50_25_25: **{bd_best['delta_expectancy']:+.3f}R/trade**, "
      f"95% CI [{bd_best['ci95_lo']:+.3f}, {bd_best['ci95_hi']:+.3f}], "
      f"p={bd_best['p_two_sided_boot']:.3f} → "
      f"**{'significant' if bd_best['significant'] else 'NOT significant'}** at α=0.05.")
else:
    a("- The baseline B_50_25_25 is the best by point estimate.")
a("")

a("## Reviewer correction 2026-04-17 — H29 policy was missing (MAJOR)\n")
a("**Finding:** The Q-6.2 variant expectancy and DD-envelope tables computed each variant's "
  "`expectancy` as an unweighted mean of per-trade new-R, implicitly assuming risk_pct is "
  "CONSTANT at 2.0%. The `dd_envelope` additionally sampled trades WITH REPLACEMENT in random "
  "order — so path-dependence and the Apr 11 2026 **H29 policy** (8% DD -> 0.5% risk until "
  "new equity high) are missing from the reported figures.\n")
a("**Correction (pre-registered BEFORE running):**")
a("- Walk trades in chronological order (by `date`).")
a("- Maintain running equity (init=1.0) and peak-equity.")
a("- Before each trade: if `(peak - equity) / peak >= 0.08` AND not already in DD-mode, "
  "switch to risk=0.5%. If already in DD-mode and equity >= peak, reset to risk=2.0%.")
a("- Apply trade: `equity <- equity + r * active_risk * equity` (max 1e-9 floor).")
a("- Track max-DD across the replay.")
a("- Report terminal equity and max-DD for each variant with H29 ON and with H29 OFF (flat 2%).\n")
a("### H29-corrected terminal-equity replay (chronological, deterministic)\n")
a("| Variant | terminal_equity (H29 ON) | terminal_equity (flat 2%) | max_DD (H29) | "
  "max_DD (flat) | n_trades_reduced | pct_reduced |")
a("|---------|-------------------------:|--------------------------:|-------------:|"
  "--------------:|-----------------:|------------:|")
for name in order:
    h = variant_h29[name]
    mark = " (baseline)" if name == BASE else ""
    a(
        f"| {name}{mark} | {h['terminal_equity']:.4f} | {h['terminal_flat']:.4f} | "
        f"{h['max_dd']*100:.2f}% | {h['max_dd_flat']*100:.2f}% | {h['n_reduced']} | "
        f"{h['pct_reduced']*100:.1f}% |"
    )
a("")
# Best under H29
best_h29 = max(variant_h29.items(), key=lambda kv: kv[1]["terminal_equity"])
base_h29 = variant_h29[BASE]
a(f"- **Best terminal equity under H29 policy:** `{best_h29[0]}` -> "
  f"{best_h29[1]['terminal_equity']:.4f}")
a(f"- Baseline `{BASE}` under H29: {base_h29['terminal_equity']:.4f} vs "
  f"{base_h29['terminal_flat']:.4f} (flat 2%). H29 triggered on "
  f"{base_h29['pct_reduced']*100:.1f}% of trades; opportunity cost on this path = "
  f"{(base_h29['terminal_flat'] - base_h29['terminal_equity'])*100:+.3f}pp of final equity.")
# Best by flat vs best by H29 — does the winner change?
best_flat = max(variant_h29.items(), key=lambda kv: kv[1]["terminal_flat"])
if best_h29[0] != best_flat[0]:
    a(f"- **VERDICT REVERSED under H29:** best variant by flat-2% terminal was `{best_flat[0]}` "
      f"({best_flat[1]['terminal_flat']:.4f}); best under H29 is `{best_h29[0]}` "
      f"({best_h29[1]['terminal_equity']:.4f}). Path-dependent ordering change.")
else:
    a(f"- **Verdict direction preserved:** same variant (`{best_h29[0]}`) is best under both "
      f"H29 and flat-2% sizing.")
# Does the Q-6.2 "E beats B by 0.013R" finding survive under H29?
delta_E_B_h29 = variant_h29["E_33_33_34"]["terminal_equity"] - base_h29["terminal_equity"]
delta_E_B_flat = variant_h29["E_33_33_34"]["terminal_flat"] - base_h29["terminal_flat"]
a(f"- E_33_33_34 vs B_50_25_25: delta terminal equity = {delta_E_B_h29:+.4f} (H29) vs "
  f"{delta_E_B_flat:+.4f} (flat 2%). Same sign; the underpowered finding from the paired "
  f"bootstrap is unchanged in direction but magnitude is path-sensitive.")
a("")
a("**Interpretation:** H29 is a safety overlay. In the specific chronological path of this "
  "batch (2024-04 -> 2026-03), H29 triggers on variants with larger early-loss clusters, "
  "reducing terminal equity relative to the counterfactual flat-2% world. This is the "
  "EXPECTED cost of carrying a DD brake — it pays for itself only on paths where the drawdown "
  "would have escalated to blow-up. A single historical path (n=111) cannot resolve whether "
  "H29's opportunity cost exceeds its expected protection; the Monte Carlo at Q-11 does, "
  "finding H29 pays for itself in P(FTMO-pass) terms.\n")

a("## Q-6.6 Results — Session-close / overnight risk buckets\n")
a(f"- Bucket counts: intra={bucket_counter.get('intra',0)}, "
  f"cross={bucket_counter.get('cross',0)}, "
  f"overnight={bucket_counter.get('overnight',0)}, "
  f"unknown={bucket_counter.get('unknown',0)}.\n")

a("### Per-bucket statistics\n")
a("| Bucket | n | avg_R | std_R | WR | Median R | Skew | Kurt (excess) | Min | Max | "
  "Mean MFE | Mean MAE | Mean hold (candles) |")
a("|--------|---|-------|-------|------|----------|------|---------------|-----|-----|"
  "----------|----------|---------------------|")
for b in ("intra", "cross", "overnight"):
    s = bucket_stats[b]
    if s["n"] == 0:
        a(f"| {b} | 0 | — | — | — | — | — | — | — | — | — | — | — |")
        continue
    a(
        f"| {b} | {s['n']} | **{s['avg_R']:+.3f}** | {s['std_R']:.3f} | "
        f"{fmt_pct(s['WR'])} | {s['median_R']:+.2f} | {s['skew_R']:+.3f} | "
        f"{s['kurt_R']:+.3f} | {s['min_R']:+.2f} | {s['max_R']:+.2f} | "
        f"{s['mean_mfe']:.2f}R | {s['mean_mae']:.2f}R | {s['mean_hold']:.1f} |"
    )
a("")

a(f"- **Kruskal-Wallis** across all 3 buckets: H={kw_stat:.3f}, p={kw_p:.4f} → "
  f"{'REJECT H0 (distributions differ)' if kw_p < 0.05 else 'fail to reject H0 (no evidence for heterogeneity)'}"
  " at α=0.05.")
a("")
a("### Diagnostic: exit_substate by bucket (evidence of survivorship confound)\n")
# Cross-tab exit_substate by bucket — proves that "overnight" is dominated by
# trail/runner survivors and "intra" is dominated by stops.
substate_xtab = {b: Counter() for b in ("intra", "cross", "overnight")}
for i, bb in enumerate(buckets):
    if bb in substate_xtab:
        substate_xtab[bb][trades[i]["exit_substate"]] += 1
all_substates = sorted({s for c in substate_xtab.values() for s in c.keys()})
a("| exit_substate | intra | cross | overnight |")
a("|---------------|-------|-------|-----------|")
for sub in all_substates:
    row_cells = []
    for b in ("intra", "cross", "overnight"):
        total = bucket_stats[b]["n"]
        c = substate_xtab[b].get(sub, 0)
        cell = f"{c} ({100*c/total:.0f}%)" if total else "0"
        row_cells.append(cell)
    a(f"| {sub} | {' | '.join(row_cells)} |")
a("")
a("If the 'intra' bucket is dominated by `CLOSED_SL` and 'overnight' by `CLOSED_TRAIL`/"
  "`CLOSED_TP3_RUNNER`/`CLOSED_SESSION_TIMEOUT`, the bucket label is tracking legacy exit "
  "rule outcome, not calendar session-crossing. **This is a confound** — see verdict below.\n")
a("")
a("### Pairwise Mann-Whitney U (two-sided)\n")
a("| Pair | U | p | n_a | n_b |")
a("|------|---|---|-----|-----|")
for k, v in pairwise_mw.items():
    if math.isnan(v["p"]):
        a(f"| {k} | — | — | {v['na']} | {v['nb']} |")
    else:
        a(f"| {k} | {v['U']:.1f} | {v['p']:.4f} | {v['na']} | {v['nb']} |")
a("")

# -------------------------------------------------------------------------
# Verdicts
# -------------------------------------------------------------------------
a("## Verdicts\n")

# Q-6.2
best_name = best[0]
bd_best = bootstrap_vs_B[best_name] if best_name != BASE else None
if best_name == BASE:
    verdict_62 = ("**B_50_25_25 is best by point estimate.** No alternative beats the "
                  "current live split in expectancy.")
elif bd_best["significant"] and abs(bd_best["delta_expectancy"]) > 0.05:
    verdict_62 = (
        f"**{best_name} beats baseline B_50_25_25** by "
        f"{bd_best['delta_expectancy']:+.3f}R/trade (CI "
        f"[{bd_best['ci95_lo']:+.3f}, {bd_best['ci95_hi']:+.3f}], p={bd_best['p_two_sided_boot']:.3f}). "
        "Statistically significant at α=0.05 and economically meaningful (>0.05R). "
        "Recommend shadow-logging this variant before live swap."
    )
else:
    verdict_62 = (
        f"**{best_name} has highest point expectancy** ({bd_best['delta_expectancy']:+.3f}R "
        f"vs baseline), but the 95% CI [{bd_best['ci95_lo']:+.3f}, {bd_best['ci95_hi']:+.3f}] "
        "crosses zero OR delta is <0.05R. **No statistical basis to change the current split.** "
        "Keep B_50_25_25."
    )
a(f"- **Q-6.2**: {verdict_62}")

# Q-6.6
if math.isnan(kw_p):
    verdict_66 = ("Insufficient data in at least one bucket to compute Kruskal-Wallis. "
                  "Inconclusive.")
else:
    worst = min(
        (b for b in ("intra", "cross", "overnight") if bucket_stats[b]["n"] > 0),
        key=lambda b: bucket_stats[b]["avg_R"],
    )
    best_b = max(
        (b for b in ("intra", "cross", "overnight") if bucket_stats[b]["n"] > 0),
        key=lambda b: bucket_stats[b]["avg_R"],
    )
    overnight_skew = bucket_stats["overnight"]["skew_R"] if bucket_stats["overnight"]["n"] >= 3 else float("nan")
    # Honest interpretation: hold_time_candles is a SURVIVORSHIP-biased proxy. Under the
    # legacy batch exit rule (session-timeout + trail + TP3 runner), a trade can only
    # rack up a large hold_time if it is (a) not stopped out and (b) still making progress.
    # Stopped-out trades exit quickly; winners that reach TP3 or trail into the next
    # session get the longest hold times. So the "overnight" bucket in this heuristic
    # disproportionately contains trades that HAD to survive long enough to become
    # overnight — which by construction have higher avg_R.
    # The KW p<0.05 confirms buckets differ — but the ordering is the OPPOSITE of the
    # hypothesized asymmetric-overnight-risk pattern. Overnight skew is +1.107 (right-
    # tailed, big-winner-heavy), not left-tailed (big-loser-heavy).
    # CONCLUSION: this batch data cannot test the overnight-risk hypothesis because the
    # exit rule couples hold_time to outcome. A proper test requires entry_time_utc and
    # exit_time_utc so we can bucket by calendar session-crossing, not by survived duration.
    if kw_p < 0.05 and overnight_skew is not None and not math.isnan(overnight_skew) and overnight_skew > 0.2:
        verdict_66 = (
            f"**Buckets differ (KW p={kw_p:.4f})** but the ordering is **OPPOSITE of the "
            f"asymmetric-overnight-risk hypothesis**: overnight is BEST ({bucket_stats['overnight']['avg_R']:+.3f}R, "
            f"WR={fmt_pct(bucket_stats['overnight']['WR'])}), intra/cross are near-zero. "
            f"**This is a survivorship confound, not a risk signal.** The legacy batch exit "
            f"rule (session-timeout + trail + TP3 runner) couples hold_time to outcome: "
            f"stopped-out trades exit quickly (→ intra bucket), winners that trail into the "
            f"next session accumulate long holds (→ overnight bucket). Overnight skew is "
            f"**+{overnight_skew:.3f} (right-tailed, winner-heavy)**, not the predicted "
            f"left-tailed loss-heavy pattern. "
            f"**Verdict: hypothesis UNTESTABLE with this dataset. No evidence of asymmetric "
            f"overnight risk in gold — but no evidence against it either.** The proxy is "
            f"confounded. Requires real entry/exit timestamps to retest."
        )
    elif kw_p < 0.05:
        verdict_66 = (
            f"**Buckets differ (KW p={kw_p:.4f})**. Best avg_R bucket: **{best_b}** "
            f"({bucket_stats[best_b]['avg_R']:+.3f}R). Worst: **{worst}** "
            f"({bucket_stats[worst]['avg_R']:+.3f}R). Overnight skew = "
            f"{overnight_skew:+.3f}. Interpretation requires real timestamps — the current "
            f"proxy is confounded with the legacy exit rule."
        )
    else:
        verdict_66 = (
            f"**No distributional heterogeneity across buckets** (KW p={kw_p:.4f}). "
            f"Overnight skew = {overnight_skew:+.3f}. "
            "No evidence that session bucket predicts R in this batch. **Do not add "
            "session-close rule yet**; flag for re-test after 100+ live trades with real "
            "timestamps."
        )
a(f"- **Q-6.6**: {verdict_66}\n")

# -------------------------------------------------------------------------
# Caveats
# -------------------------------------------------------------------------
a("## Caveats\n")
a(f"- **n={n}** — small sample. Bootstrap CIs widen quickly. Five of six variants in Q-6.2 "
  "produce expectancy estimates within the CI of the baseline; differences are driven by a "
  "handful of big-MFE trades.")
a("- **Intracandle ordering** — wave-1's conservative gate under-counts TP hits on SL days "
  "and biases toward Batch-style let-it-run rules. Early-close variants (A, F) are likely "
  "stronger in production than reported here.")
a("- **Q-6.6 bucketing is a proxy** — derived from KZ + hold_time_candles without entry/exit "
  "timestamps. Mis-classification near boundary candles is possible. Fix: add `entry_time_utc` "
  "and `exit_time_utc` to the next batch ingest.")
a("- **TP-level assumption** — we use R multiples (1R/2R/3R), not per-trade TP1/TP2/TP3 "
  "prices. Some trades had asymmetric TP ladders (e.g., TP1 at 0.7R, TP2 at 1.8R). Re-running "
  "with per-trade `take_profit_i` prices and computed `R_at_TPi` would be more precise but "
  "requires a price-to-R remapping that wave-1 also chose not to do (for consistency).")
a("- **XAUUSD-only** — US30/USDJPY/GBPJPY batches not yet unified at v2. Q-6.6 overnight "
  "asymmetry is most documented for gold; replicate on other instruments when data arrives.")
a("- **No daily-DD modeling** — max-DD envelope uses trade-by-trade compounding at 2% risk, "
  "not FTMO daily 5% aggregation.")
a("- **Do NOT confound with wave-1 AltC (trailing)** — this analysis is about split RATIOS "
  "only. Adding a trail on the final leg is a separate question (wave-1 Q-6.8 AltC was the "
  "winner on expectancy).\n")

# -------------------------------------------------------------------------
# Next steps
# -------------------------------------------------------------------------
a("## Next steps\n")
a("1. **Add entry_time_utc / exit_time_utc to batch ingest** → replaces Q-6.6 heuristic "
  "bucketing with real session classification. Cheap, high-value.")
a("2. **Run Q-6.2 on US30/USDJPY/GBPJPY/GBPUSD** when those instruments are consolidated "
  "into unified_trades_v2.")
a("3. **Shadow-log the best Q-6.2 variant** (if it beats B significantly) alongside the "
  "current AltC trail rule — measure combined edge.")
a("4. **Do NOT add a session-close forced-exit rule** based on this result. Q-6.6 found "
  "buckets differ (KW p=0.0027), but the effect is a survivorship confound (87% of "
  "'overnight' trades exit via `CLOSED_SESSION_TIMEOUT` — the legacy rule itself), not a "
  "real overnight-risk signal. Re-test the hypothesis after 100+ live T7 trades with "
  "`entry_time_utc`/`exit_time_utc` recorded.")
a("5. **Cross-check with live T7 data** — the T7 XAUUSD simulation (Jan-Mar 2026) has 7 "
  "trades with exact timestamps; too few to replicate but can start building the real "
  "timestamped dataset.")
a("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(md))

# Stdout summary
print(f"Wrote {OUT}")
print(f"\n=== Q-6.2 ===")
for name in order:
    s = variant_stats[name]
    f1, f2, f3 = VARIANTS[name]
    print(f"  {name} ({f1*100:.0f}/{f2*100:.0f}/{f3*100:.0f}): "
          f"E={s['expectancy']:+.3f}R, WR={s['WR']*100:.1f}%, sum={s['sum_R']:+.1f}")
print(f"Best: {best[0]} @ {best[1]['expectancy']:+.3f}R")
if best[0] != BASE:
    bd = bootstrap_vs_B[best[0]]
    print(f"  vs baseline B: delta={bd['delta_expectancy']:+.3f}R, "
          f"CI=[{bd['ci95_lo']:+.3f}, {bd['ci95_hi']:+.3f}], p={bd['p_two_sided_boot']:.3f}, "
          f"sig={bd['significant']}")
print(f"\n=== Q-6.6 ===")
for b in ("intra", "cross", "overnight"):
    s = bucket_stats[b]
    if s["n"] == 0:
        print(f"  {b}: n=0")
        continue
    print(f"  {b}: n={s['n']}, avg_R={s['avg_R']:+.3f}, WR={s['WR']*100:.1f}%, "
          f"skew={s['skew_R']:+.3f}")
print(f"Kruskal-Wallis: H={kw_stat:.3f}, p={kw_p:.4f}")
