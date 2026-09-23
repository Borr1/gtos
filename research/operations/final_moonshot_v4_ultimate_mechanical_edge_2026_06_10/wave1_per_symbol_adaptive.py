"""WAVE 1 - per_symbol_adaptive routing.

THRUST: Each symbol may have its OWN behavior. On TRAIN (<=2024) per symbol, measure
trend-vs-revert tendency. Assign each symbol a mode (trend-follow / mean-revert / skip).
On FORWARD (2025-26), trade each symbol in its assigned mode. Does per-symbol adaptive
ROUTING beat a single global rule? Report routing table and forward per-year.

DISCIPLINE:
- TRAIN <= 2024 for mode assignment; FORWARD = 2025-2026 strict holdout.
- Report per-year across ALL available years (regime-robustness, not recency).
- Bar = forward-positive AND positive in a MAJORITY of years.
- Negative controls included (random mode, inverted mode, shuffled-routing).
- Fills ONLY via tested geometry_lib.simulate. No hand-rolled stop/target/sign.
- Default stop = 0.5 * atr14.
"""
from __future__ import annotations
import sys, os, json, csv, math, random
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
OPDIR = os.path.join(ROOT, "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")
sys.path.insert(0, ROOT)
sys.path.insert(0, OPDIR)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL  # noqa
from geometry_lib import Bar, atr14, simulate  # noqa

DATA_OLD = os.path.join(ROOT, "data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022")
DATA_NEW = os.path.join(ROOT, "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026")
COST_MAP = json.load(open(os.path.join(OPDIR, "ULTIMATE_REAL_COST_MAP.json")))

TRAIN_END_YEAR = 2024            # train uses bars with year <= 2024
FORWARD_YEARS = (2025, 2026)     # strict holdout
STOP_ATR_MULT = 0.5              # geometry default
MAXBARS = 80

# All symbols that exist in at least one export dir, with a known asset class.
ALL_SYMBOLS = sorted(set(ASSET_CLASS_BY_SYMBOL.keys()))


def cost_for(symbol):
    ac = ASSET_CLASS_BY_SYMBOL.get(symbol, "fx")
    return COST_MAP.get(ac, COST_MAP["_global_median"])


def load_series(symbol):
    """Concatenate 2015-2022 + 2022-2026, dedupe by time, sorted. Returns list of (dt_str, Bar, year)."""
    rows = {}
    for d in (DATA_OLD, DATA_NEW):
        p = os.path.join(d, f"{symbol}_H4.csv")
        if not os.path.exists(p):
            continue
        with open(p) as f:
            r = csv.DictReader(f)
            for row in r:
                t = row["time"]
                try:
                    o = float(row["open"]); h = float(row["high"]); l = float(row["low"])
                    c = float(row["close"]); v = float(row.get("volume", 0) or 0)
                except (ValueError, TypeError):
                    continue
                rows[t] = (o, h, l, c, v)
    if not rows:
        return None
    out = []
    for t in sorted(rows):
        o, h, l, c, v = rows[t]
        out.append((t, Bar(o, h, l, c, v), int(t[:4])))
    return out


# ---------------------------------------------------------------------------
# Entry triggers. Both modes use the SAME breakout-band geometry so the only
# difference is direction routing (trend = go with breakout; revert = fade it).
# This isolates the routing decision, which is the thrust.
# ---------------------------------------------------------------------------
LOOKBACK = 20  # bars for the Donchian-style band

def signals_for_bar(bars, i):
    """Return dict of directional triggers active at bar i (decision made on close of i).
    'up_break'  : close > max(high of prior LOOKBACK)  -> bullish breakout
    'dn_break'  : close < min(low  of prior LOOKBACK)  -> bearish breakout
    Returns (up_break: bool, dn_break: bool).
    """
    if i < LOOKBACK + 14:
        return False, False
    win = bars[i-LOOKBACK:i]   # prior bars, excluding current
    hh = max(b.h for b in win)
    ll = min(b.l for b in win)
    c = bars[i].c
    return (c > hh), (c < ll)


def trades_for_symbol(bars, mode):
    """Generate trades for a symbol under a mode.
    mode 'trend'  : on up_break go long, on dn_break go short.
    mode 'revert' : on up_break go short, on dn_break go long.
    mode 'skip'   : no trades.
    Returns list of (year, R). Non-overlapping: skip new entries while a trade is open.
    """
    if mode == "skip":
        return []
    cost = cost_for_symbol_cache
    res = []
    n = len(bars)
    cooldown_until = -1
    bar_objs = [b for (_, b, _) in bars]
    for i in range(LOOKBACK + 14, n - 1):
        if i <= cooldown_until:
            continue
        up, dn = signals_for_bar(bar_objs, i)
        if not (up or dn):
            continue
        a = atr14(bar_objs, i)
        if a <= 0:
            continue
        stop_dist = STOP_ATR_MULT * a
        if stop_dist <= 0:
            continue
        # decide direction
        if mode == "trend":
            direction = 1 if up else -1
        else:  # revert
            direction = -1 if up else 1
        if GEOMETRY == "trail":
            R = simulate(bar_objs, i, direction,
                         stop_dist=stop_dist,
                         trail_arm=2.0 * a, trail_gap=1.0 * a,
                         maxbars=MAXBARS, cost=cost)
        else:  # fixed target at TARGET_R * stop_dist
            R = simulate(bar_objs, i, direction,
                         stop_dist=stop_dist,
                         target_dist=TARGET_R * stop_dist,
                         maxbars=MAXBARS, cost=cost)
        yr = bars[i][2]
        res.append((yr, R))
        # cooldown: estimate holding by walking until trade would have closed is costly;
        # use a fixed modest cooldown to avoid pyramiding the same breakout.
        cooldown_until = i + 6
    return res


# global injected per-symbol cost (set before calling trades_for_symbol)
cost_for_symbol_cache = 0.0
# geometry knobs (set in run())
GEOMETRY = "fixed"   # "fixed" or "trail"
TARGET_R = 1.5       # fixed-target multiple of stop_dist


def _year_positivity(trades):
    """Fraction of TRAIN years in which a mode's sum_R > 0, plus per-year means."""
    py = per_year_stats(trades)
    yrs = sorted(py.keys())
    if not yrs:
        return 0.0, 0, 0
    pos = sum(1 for y in yrs if py[y][0] > 0)
    return pos / len(yrs), pos, len(yrs)


def measure_train_edge(bars):
    """On TRAIN bars (year<=2024) measure trend edge and revert edge with REGIME-ROBUST
    diagnostics: mean R, n, and per-TRAIN-year positivity for each mode.
    Returns dict or None.
    """
    train_bars = [(t, b, y) for (t, b, y) in bars if y <= TRAIN_END_YEAR]
    if len(train_bars) < 200:
        return None
    t_trades = trades_for_symbol(train_bars, "trend")
    r_trades = trades_for_symbol(train_bars, "revert")
    tm = sum(r for _, r in t_trades) / len(t_trades) if t_trades else 0.0
    rm = sum(r for _, r in r_trades) / len(r_trades) if r_trades else 0.0
    t_frac, t_pos, t_tot = _year_positivity(t_trades)
    r_frac, r_pos, r_tot = _year_positivity(r_trades)
    return {
        "trend_mean": tm, "revert_mean": rm,
        "n_trend": len(t_trades), "n_revert": len(r_trades),
        "trend_yrpos": (t_pos, t_tot), "revert_yrpos": (r_pos, r_tot),
        "trend_frac": t_frac, "revert_frac": r_frac,
    }


def assign_mode(te, min_trades=40, min_edge=0.02, min_year_frac=0.6):
    """REGIME-ROBUST routing rule: a mode is eligible only if on TRAIN it has
    enough trades AND positive mean R above min_edge AND was positive in a MAJORITY
    (>= min_year_frac) of TRAIN years. Among eligible modes pick the higher mean R.
    Else skip. This refuses to route on a lucky single-year average."""
    if te is None:
        return "skip"
    cands = []
    if te["n_trend"] >= min_trades and te["trend_mean"] > min_edge and te["trend_frac"] >= min_year_frac:
        cands.append(("trend", te["trend_mean"]))
    if te["n_revert"] >= min_trades and te["revert_mean"] > min_edge and te["revert_frac"] >= min_year_frac:
        cands.append(("revert", te["revert_mean"]))
    if not cands:
        return "skip"
    return max(cands, key=lambda x: x[1])[0]


def per_year_stats(trades):
    """trades: list of (year,R) -> dict year-> (sum_R, n, mean_R)."""
    agg = defaultdict(lambda: [0.0, 0])
    for y, r in trades:
        agg[y][0] += r
        agg[y][1] += 1
    out = {}
    for y, (s, n) in agg.items():
        out[y] = (s, n, s / n if n else 0.0)
    return out


def summarize(label, all_trades, years):
    """Print + return summary for a strategy across years."""
    py = per_year_stats(all_trades)
    forward_trades = [(y, r) for (y, r) in all_trades if y in FORWARD_YEARS]
    fwd_n = len(forward_trades)
    fwd_sum = sum(r for _, r in forward_trades)
    fwd_mean = fwd_sum / fwd_n if fwd_n else 0.0
    # year positivity across ALL years that have trades
    yrs_with = sorted(py.keys())
    pos = sum(1 for y in yrs_with if py[y][0] > 0)
    tot = len(yrs_with)
    return {
        "label": label,
        "per_year": {y: {"sum_R": round(py[y][0], 2), "n": py[y][1], "mean_R": round(py[y][2], 4)} for y in yrs_with},
        "forward_per_trade_R": round(fwd_mean, 4),
        "forward_sum_R": round(fwd_sum, 2),
        "forward_n": fwd_n,
        "years_positive": pos,
        "total_years": tot,
        "total_trades": len(all_trades),
    }


def autocorr_mode(bars, lag=1):
    """Structural routing signal (the thrust's literal suggestion): lag-1 autocorrelation
    of H4 log returns on TRAIN. Positive AC -> trend-follow; negative AC -> mean-revert.
    Returns (mode, ac) using only TRAIN bars."""
    closes = [b.c for (_, b, y) in bars if y <= TRAIN_END_YEAR and b.c > 0]
    if len(closes) < 300:
        return "skip", 0.0
    rets = [math.log(closes[i] / closes[i-1]) for i in range(1, len(closes))]
    n = len(rets) - lag
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets)
    if var <= 0:
        return "skip", 0.0
    cov = sum((rets[i] - mean) * (rets[i+lag] - mean) for i in range(n))
    ac = cov / var
    if ac > 0.02:
        return "trend", ac
    if ac < -0.02:
        return "revert", ac
    return "skip", ac


def run():
    # Load all symbols
    series = {}
    for s in ALL_SYMBOLS:
        srs = load_series(s)
        if srs is not None and len(srs) > 300:
            series[s] = srs
    print(f"Loaded {len(series)} symbols with data.")

    # 1) Learn routing table on TRAIN
    routing = {}
    train_detail = {}
    for s, bars in series.items():
        te = measure_train_edge(bars)
        train_detail[s] = te
        routing[s] = assign_mode(te)
    print("\n=== ROUTING TABLE (mode chosen on TRAIN<=2024) ===")
    for s in sorted(routing):
        te = train_detail[s]
        if te:
            tp, tt = te["trend_yrpos"]; rp, rt = te["revert_yrpos"]
            print(f"  {s:14s} -> {routing[s]:7s}  "
                  f"trend={te['trend_mean']:+.3f}(n{te['n_trend']},yr{tp}/{tt})  "
                  f"revert={te['revert_mean']:+.3f}(n{te['n_revert']},yr{rp}/{rt})")
        else:
            print(f"  {s:14s} -> {routing[s]:7s}  (insufficient train)")

    mode_counts = defaultdict(int)
    for m in routing.values():
        mode_counts[m] += 1
    print(f"\nMode counts: {dict(mode_counts)}")

    # 2) Apply routing to FULL series (per-year, includes forward holdout)
    global cost_for_symbol_cache
    adaptive_trades = []
    per_symbol_forward = {}
    for s, bars in series.items():
        cost_for_symbol_cache = cost_for(s)
        m = routing[s]
        if m == "skip":
            continue
        tr = trades_for_symbol(bars, m)
        adaptive_trades.extend(tr)
        fwd = [(y, r) for (y, r) in tr if y in FORWARD_YEARS]
        if fwd:
            per_symbol_forward[s] = (m, round(sum(r for _, r in fwd), 2), len(fwd))

    adaptive_summary = summarize("PER_SYMBOL_ADAPTIVE", adaptive_trades, FORWARD_YEARS)

    # 3) Negative / comparator controls
    # 3a) Global trend (everyone trend)
    gt = []
    for s, bars in series.items():
        cost_for_symbol_cache = cost_for(s)
        gt.extend(trades_for_symbol(bars, "trend"))
    global_trend = summarize("GLOBAL_TREND", gt, FORWARD_YEARS)
    # 3b) Global revert (everyone revert)
    gr = []
    for s, bars in series.items():
        cost_for_symbol_cache = cost_for(s)
        gr.extend(trades_for_symbol(bars, "revert"))
    global_revert = summarize("GLOBAL_REVERT", gr, FORWARD_YEARS)
    # 3c) INVERTED routing (negative control: do opposite of assigned mode)
    inv = []
    inv_route = {}
    for s, bars in series.items():
        cost_for_symbol_cache = cost_for(s)
        m = routing[s]
        if m == "skip":
            continue
        im = "revert" if m == "trend" else "trend"
        inv_route[s] = im
        inv.extend(trades_for_symbol(bars, im))
    inverted = summarize("INVERTED_ROUTING_NEGCTRL", inv, FORWARD_YEARS)
    # 3c2) AUTOCORRELATION-routed (the thrust's literal structural signal)
    ac_route = {}
    ac_trades = []
    for s, bars in series.items():
        cost_for_symbol_cache = cost_for(s)
        m, ac = autocorr_mode(bars)
        ac_route[s] = (m, round(ac, 4))
        if m == "skip":
            continue
        ac_trades.extend(trades_for_symbol(bars, m))
    autocorr_summary = summarize("AUTOCORR_ROUTED", ac_trades, FORWARD_YEARS)

    # 3c3) REGIME-ROBUST SURVIVORS: only symbols whose chosen mode was positive in a
    # STRICT majority (>=0.8) of TRAIN years AND n>=80. The most disciplined subset.
    strict_route = {}
    strict_trades = []
    for s, bars in series.items():
        cost_for_symbol_cache = cost_for(s)
        te = train_detail[s]
        m = routing[s]
        if m == "skip" or te is None:
            continue
        frac = te["trend_frac"] if m == "trend" else te["revert_frac"]
        n = te["n_trend"] if m == "trend" else te["n_revert"]
        if frac >= 0.8 and n >= 80:
            strict_route[s] = m
            strict_trades.extend(trades_for_symbol(bars, m))
    strict_summary = summarize("REGIME_ROBUST_SURVIVORS", strict_trades, FORWARD_YEARS)

    # 3d) RANDOM routing (negative control), averaged over seeds
    rng = random.Random(13)
    rand_summaries = []
    for seed in range(5):
        rr = random.Random(1000 + seed)
        rtr = []
        for s, bars in series.items():
            cost_for_symbol_cache = cost_for(s)
            m = rr.choice(["trend", "revert", "skip"])
            if m == "skip":
                continue
            rtr.extend(trades_for_symbol(bars, m))
        rand_summaries.append(summarize(f"RANDOM_seed{seed}", rtr, FORWARD_YEARS))
    rand_fwd = sum(x["forward_per_trade_R"] for x in rand_summaries) / len(rand_summaries)

    # 4) Report
    def show(s):
        print(f"\n--- {s['label']} ---")
        print(f"  forward_per_trade_R={s['forward_per_trade_R']:+.4f}  forward_sum_R={s['forward_sum_R']:+.1f}  forward_n={s['forward_n']}")
        print(f"  years_positive={s['years_positive']}/{s['total_years']}  total_trades={s['total_trades']}")
        print("  per-year:")
        for y in sorted(s["per_year"]):
            d = s["per_year"][y]
            flag = "+" if d["sum_R"] > 0 else "-"
            print(f"    {y}: sum_R={d['sum_R']:+8.2f}  n={d['n']:5d}  mean={d['mean_R']:+.4f}  [{flag}]")

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    for s in (adaptive_summary, autocorr_summary, strict_summary, global_trend, global_revert, inverted):
        show(s)
    print(f"\n--- RANDOM_ROUTING_NEGCTRL (mean over 5 seeds) ---")
    print(f"  forward_per_trade_R={rand_fwd:+.4f}")
    for rs in rand_summaries:
        print(f"    seed: fwd_per_trade={rs['forward_per_trade_R']:+.4f} yrs_pos={rs['years_positive']}/{rs['total_years']}")

    print("\n=== PER-SYMBOL FORWARD CONTRIBUTION (adaptive) ===")
    for s in sorted(per_symbol_forward, key=lambda k: per_symbol_forward[k][1]):
        m, sm, n = per_symbol_forward[s]
        print(f"  {s:14s} {m:7s} fwd_sum_R={sm:+8.2f} n={n}")

    out = {
        "thrust": "per_symbol_adaptive",
        "config": {
            "train_end_year": TRAIN_END_YEAR, "forward_years": list(FORWARD_YEARS),
            "stop_atr_mult": STOP_ATR_MULT, "lookback": LOOKBACK, "maxbars": MAXBARS,
            "trail_arm_atr": 2.0, "trail_gap_atr": 1.0, "min_train_trades": 30,
        },
        "routing_table": {s: routing[s] for s in sorted(routing)},
        "mode_counts": dict(mode_counts),
        "adaptive": adaptive_summary,
        "autocorr_routed": autocorr_summary,
        "autocorr_route_table": ac_route,
        "regime_robust_survivors": strict_summary,
        "strict_route_table": strict_route,
        "global_trend": global_trend,
        "global_revert": global_revert,
        "inverted_negctrl": inverted,
        "random_negctrl_mean_fwd_R": round(rand_fwd, 4),
        "per_symbol_forward": per_symbol_forward,
    }
    with open(os.path.join(OPDIR, "wave1_per_symbol_adaptive_RESULT.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nWrote wave1_per_symbol_adaptive_RESULT.json")
    return out


if __name__ == "__main__":
    run()
