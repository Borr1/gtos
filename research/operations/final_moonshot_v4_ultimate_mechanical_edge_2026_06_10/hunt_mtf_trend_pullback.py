"""HUNT: mtf_trend_pullback — multi-timeframe trend continuation.

Thesis (orthogonal to the failed reversion family): align entries WITH the
higher-timeframe trend. Define HTF trend from H4 SMA / Donchian and a DAILY
proxy (resample 6 H4 bars). Enter on a PULLBACK in trend direction (price dips
to a fast MA / prior structure while HTF trend stays up, or vice versa) and ride
with a trail. Question: does trend continuation produce POSITIVE & STABLE
FORWARD per-trade R?

Rules of engagement (campaign discipline):
  * fill sim ONLY via the TESTED geometry_lib.simulate (no homemade stop/target).
  * stop_dist = 0.5*atr14 noise floor; trail_arm=2*stop, trail_gap=1*stop default.
  * TRAIN 2022-2024 / FORWARD 2025-2026. Report per-trade R, win%, per-year,
    by asset_class, long & short separately. The bar is POSITIVE & STABLE FWD.
  * Honest. If nothing is forward-positive, say so with numbers.
"""
from __future__ import annotations
import sys, os, csv, json, math
from datetime import datetime
from collections import defaultdict

REPO = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
OPDIR = os.path.join(REPO, "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")
DATA = os.path.join(REPO, "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026")
sys.path.insert(0, REPO)
sys.path.insert(0, OPDIR)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL  # noqa
from geometry_lib import Bar, atr14, simulate  # noqa

COSTS = json.load(open(os.path.join(OPDIR, "ULTIMATE_REAL_COST_MAP.json")))
GLOBAL_COST = COSTS["_global_median"]

def cost_for(sym):
    ac = ASSET_CLASS_BY_SYMBOL.get(sym)
    return COSTS.get(ac, GLOBAL_COST)  # agri -> global median fallback

# ----------------------------------------------------------------------------
def load(sym):
    path = os.path.join(DATA, f"{sym}_H4.csv")
    bars, times = [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            bars.append(Bar(float(row["open"]), float(row["high"]), float(row["low"]),
                            float(row["close"]), float(row["volume"])))
            times.append(datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S"))
    return bars, times

SYMBOLS = sorted(s[:-7] for s in os.listdir(DATA) if s.endswith("_H4.csv"))

def sma(vals, i, n):
    if i+1 < n: return None
    return sum(vals[i-n+1:i+1]) / n

def donchian(highs, lows, i, n):
    if i+1 < n: return None, None
    return max(highs[i-n+1:i+1]), min(lows[i-n+1:i+1])

# ----------------------------------------------------------------------------
# Daily proxy: resample 6 consecutive H4 bars -> 1 daily bar. For each H4 index i
# we want the daily SMA/trend computed ONLY from CLOSED daily bars (no lookahead).
def build_daily_close_sma(bars, times, n_days):
    """Return array aligned to H4 index: daily SMA of the last n_days COMPLETED
    daily closes as of (and not including) the current forming day. No lookahead."""
    # group H4 bars into calendar days
    day_close = {}      # date -> last close seen so far
    day_order = []      # ordered list of dates
    daily_closes = []   # completed daily closes in order
    out = [None]*len(bars)
    cur_date = None
    for i in range(len(bars)):
        d = times[i].date()
        if cur_date is None:
            cur_date = d
        elif d != cur_date:
            # previous day completed -> push its close
            daily_closes.append(day_close[cur_date])
            cur_date = d
        day_close[d] = bars[i].c
        # SMA over completed daily closes (strictly before today)
        if len(daily_closes) >= n_days:
            out[i] = sum(daily_closes[-n_days:]) / n_days
    return out

# ----------------------------------------------------------------------------
def year_of(t): return t.year

def agg(rs):
    if not rs: return dict(n=0, mean=0.0, win=0.0, sum=0.0)
    n = len(rs); s = sum(rs); w = sum(1 for r in rs if r > 0)
    return dict(n=n, mean=s/n, win=w/n, sum=s)

def split_stats(trades):
    """trades: list of (year, asset_class, direction, R)."""
    out = {}
    out["all"] = agg([t[3] for t in trades])
    out["long"] = agg([t[3] for t in trades if t[2] > 0])
    out["short"] = agg([t[3] for t in trades if t[2] < 0])
    by_year = {}
    for y in sorted(set(t[0] for t in trades)):
        by_year[y] = agg([t[3] for t in trades if t[0] == y])
    out["by_year"] = by_year
    by_ac = {}
    for ac in sorted(set(t[1] for t in trades)):
        by_ac[ac] = agg([t[3] for t in trades if t[1] == ac])
    out["by_ac"] = by_ac
    return out

# ----------------------------------------------------------------------------
# A single configurable strategy run across all symbols.
def run_config(cfg, symbols=SYMBOLS, verbose=False):
    """cfg keys:
        htf_mode: 'sma' (H4 slow SMA), 'don' (H4 Donchian), 'daily' (daily SMA)
        htf_n: lookback for HTF trend filter
        daily_n: daily SMA lookback (for 'daily' or as extra gate if use_daily)
        use_daily_gate: also require daily SMA slope agreement
        fast_n: fast SMA for pullback reference
        pull_mode: 'touch_fast' (low<=fastMA<=... pullback to fast MA),
                   'pct_atr' (price pulled back >= pb_atr*atr from recent extreme)
        pb_atr: pullback depth in ATR for 'pct_atr'
        trigger: 'close_back' (close re-crosses above/below fast MA in trend dir),
                 'none' (enter on pullback bar itself)
        stop_mult, exit: 'trail' or 'target', target_mult, trail_arm_mult, trail_gap_mult
        maxbars
        cooldown: bars to wait after a trade on same symbol
    Returns trades list (year, ac, dir, R)."""
    trades = []
    for sym in symbols:
        try:
            bars, times = load(sym)
        except FileNotFoundError:
            continue
        ac = ASSET_CLASS_BY_SYMBOL.get(sym, "unknown")
        cost = cost_for(sym)
        closes = [b.c for b in bars]; highs=[b.h for b in bars]; lows=[b.l for b in bars]
        n = len(bars)
        daily_sma = None
        if cfg["htf_mode"] == "daily" or cfg.get("use_daily_gate"):
            daily_sma = build_daily_close_sma(bars, times, cfg.get("daily_n", 20))
        htf_n = cfg["htf_n"]; fast_n = cfg["fast_n"]
        last_exit_i = -10**9
        stop_mult = cfg["stop_mult"]
        for i in range(60, n-2):
            a = atr14(bars, i)
            if a <= 0: continue
            if i - last_exit_i < cfg.get("cooldown", 0): continue
            # --- HTF trend direction ---
            trend = 0
            if cfg["htf_mode"] == "sma":
                slow = sma(closes, i, htf_n)
                slow_prev = sma(closes, i-cfg.get("slope_lag",6), htf_n)
                if slow is None or slow_prev is None: continue
                if closes[i] > slow and slow > slow_prev: trend = 1
                elif closes[i] < slow and slow < slow_prev: trend = -1
            elif cfg["htf_mode"] == "don":
                hi, lo = donchian(highs, lows, i, htf_n)
                if hi is None: continue
                # trend up if near top of channel, down if near bottom
                mid = (hi+lo)/2
                if closes[i] >= mid: trend = 1
                else: trend = -1
            elif cfg["htf_mode"] == "daily":
                ds = daily_sma[i]
                if ds is None: continue
                # need slope of daily sma
                ds_prev = daily_sma[i-6] if i-6 >= 0 else None
                if ds_prev is None: continue
                if closes[i] > ds and ds > ds_prev: trend = 1
                elif closes[i] < ds and ds < ds_prev: trend = -1
            if trend == 0: continue
            # --- optional daily gate ---
            if cfg.get("use_daily_gate") and daily_sma is not None:
                ds = daily_sma[i]; ds_prev = daily_sma[i-6] if i-6>=0 else None
                if ds is None or ds_prev is None: continue
                dtrend = 1 if (closes[i] > ds and ds > ds_prev) else (-1 if (closes[i] < ds and ds < ds_prev) else 0)
                if dtrend != trend: continue
            # --- pullback detection in trend direction ---
            fast = sma(closes, i, fast_n)
            if fast is None: continue
            entered = False
            if cfg["pull_mode"] == "touch_fast":
                # pullback: this bar's low dipped to/below fast MA (uptrend) and
                # close back above; symmetric for down.
                if trend == 1:
                    pulled = lows[i] <= fast
                    if cfg["trigger"] == "close_back":
                        ok = pulled and closes[i] > fast
                    else:
                        ok = pulled and closes[i] >= lows[i]  # any pullback bar
                    entered = ok
                else:
                    pulled = highs[i] >= fast
                    if cfg["trigger"] == "close_back":
                        ok = pulled and closes[i] < fast
                    else:
                        ok = pulled
                    entered = ok
            elif cfg["pull_mode"] == "pct_atr":
                # recent extreme over last `ext_n` bars; require price pulled back
                # pb_atr*ATR from it, then re-thrust in trend dir on this close.
                ext_n = cfg.get("ext_n", 10)
                if trend == 1:
                    recent_high = max(highs[i-ext_n:i+1])
                    pulled = (recent_high - lows[i]) >= cfg.get("pb_atr",1.0)*a
                    if cfg["trigger"] == "close_back":
                        ok = pulled and closes[i] > closes[i-1]
                    else:
                        ok = pulled
                    entered = ok
                else:
                    recent_low = min(lows[i-ext_n:i+1])
                    pulled = (highs[i] - recent_low) >= cfg.get("pb_atr",1.0)*a
                    if cfg["trigger"] == "close_back":
                        ok = pulled and closes[i] < closes[i-1]
                    else:
                        ok = pulled
                    entered = ok
            if not entered: continue
            # --- simulate via tested lib ---
            sd = stop_mult * a
            if cfg["exit"] == "target":
                R = simulate(bars, i, trend, stop_dist=sd,
                             target_dist=cfg["target_mult"]*a,
                             maxbars=cfg.get("maxbars",80), cost=cost)
            else:
                R = simulate(bars, i, trend, stop_dist=sd,
                             trail_arm=cfg["trail_arm_mult"]*sd,
                             trail_gap=cfg["trail_gap_mult"]*sd,
                             maxbars=cfg.get("maxbars",80), cost=cost)
            trades.append((year_of(times[i]), ac, trend, R))
            last_exit_i = i
    return trades

def in_train(y): return 2022 <= y <= 2024
def in_fwd(y):   return 2025 <= y <= 2026

def evaluate(cfg, label):
    trades = run_config(cfg)
    tr = [t for t in trades if in_train(t[0])]
    fw = [t for t in trades if in_fwd(t[0])]
    return {
        "label": label, "cfg": cfg,
        "train": split_stats(tr),
        "forward": split_stats(fw),
        "n_total": len(trades),
    }

def fmt(s):
    return f"n={s['n']:>5} mean={s['mean']:+.4f}R win={s['win']*100:5.1f}%"

def print_result(res):
    print(f"\n=== {res['label']} ===")
    print(f"  TRAIN all : {fmt(res['train']['all'])}")
    print(f"  TRAIN long: {fmt(res['train']['long'])}   short: {fmt(res['train']['short'])}")
    print(f"  FWD   all : {fmt(res['forward']['all'])}")
    print(f"  FWD   long: {fmt(res['forward']['long'])}   short: {fmt(res['forward']['short'])}")
    print(f"  FWD by year: " + "  ".join(f"{y}:{fmt(res['forward']['by_year'][y])}" for y in res['forward']['by_year']))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="screen")
    args = ap.parse_args()

    base_trail = dict(stop_mult=0.5, exit="trail", trail_arm_mult=2.0, trail_gap_mult=1.0, maxbars=80, cooldown=2)
    base_tgt   = dict(stop_mult=0.5, exit="target", target_mult=2.0, maxbars=80, cooldown=2)

    configs = []
    # Family A: H4 SMA trend + touch_fast pullback + close_back trigger
    for htf_n in (50, 100):
        for fast_n in (10, 20):
            for ex in ("trail","target"):
                base = dict(base_trail if ex=="trail" else base_tgt)
                cfg = dict(base, htf_mode="sma", htf_n=htf_n, fast_n=fast_n,
                           pull_mode="touch_fast", trigger="close_back", slope_lag=6)
                configs.append((f"A_sma{htf_n}_fast{fast_n}_{ex}_closeback", cfg))
    # Family B: daily SMA trend
    for daily_n in (10, 20):
        for fast_n in (10, 20):
            base = dict(base_trail)
            cfg = dict(base, htf_mode="daily", daily_n=daily_n, htf_n=50, fast_n=fast_n,
                       pull_mode="touch_fast", trigger="close_back")
            configs.append((f"B_daily{daily_n}_fast{fast_n}_trail", cfg))
    # Family C: SMA trend + pct_atr pullback
    for htf_n in (50, 100):
        for pb in (0.8, 1.2):
            base = dict(base_trail)
            cfg = dict(base, htf_mode="sma", htf_n=htf_n, fast_n=20, slope_lag=6,
                       pull_mode="pct_atr", pb_atr=pb, ext_n=10, trigger="close_back")
            configs.append((f"C_sma{htf_n}_pb{pb}_trail", cfg))

    results = []
    for label, cfg in configs:
        res = evaluate(cfg, label)
        results.append(res)
        print_result(res)

    # rank by forward all mean among configs with enough fwd trades
    ranked = sorted([r for r in results if r["forward"]["all"]["n"] >= 150],
                    key=lambda r: r["forward"]["all"]["mean"], reverse=True)
    print("\n\n########## TOP BY FORWARD MEAN R (n>=150) ##########")
    for r in ranked[:8]:
        print(f"{r['label']:45s} FWD {fmt(r['forward']['all'])}  TRAIN {fmt(r['train']['all'])}")

    json.dump([{k:v for k,v in r.items() if k!='cfg'} | {'cfg':r['cfg']} for r in results],
              open(os.path.join(OPDIR,"hunt_mtf_trend_pullback_screen.json"),"w"), indent=1, default=str)
    print("\nwrote hunt_mtf_trend_pullback_screen.json")
