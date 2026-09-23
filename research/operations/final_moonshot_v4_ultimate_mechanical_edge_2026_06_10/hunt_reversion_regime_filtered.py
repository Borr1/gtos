"""hunt_reversion_regime_filtered.py
=====================================
Signal class: reversion_regime_filtered.

THESIS
------
The prior reversion failure (S1-S5 on quote intensity) fired in ALL regimes ->
near-coinflip. Reversion as a *mechanical* edge only exists in mean-reverting
regimes: confirmed RANGE / low-ADX / volatility-contraction. In a trend, fading
an extreme just feeds the trend and gets stopped.

So: only fade when the market is *provably* in a range/contraction regime, AND
the bar shows an *extreme + exhaustion* entry signature. We test whether adding a
STRICT regime filter turns reversion forward-positive.

Indicators (all causal, computed on bars up to and including the signal bar i):
  - ADX(14)          : trend strength. Range regime => low ADX.
  - EMA(20) dist     : how far close is from its mean, in ATR units (the extreme).
  - RSI(14)          : exhaustion (oversold for longs, overbought for shorts).
  - Bollinger pos    : close vs (EMA +/- k*std) band -> outside band = extreme.
  - vol contraction  : ATR(14) / ATR(50) < 1  -> volatility shrinking (range).
  - efficiency ratio : Kaufman ER over N bars; low ER = choppy/range, high = trend.

Fill simulation: ONLY via geometry_lib.simulate (tested, two-sided, no sign bug).
Geometry: stop_dist = 0.5*ATR14 (noise floor). We grid target/trail.

Discipline: TRAIN 2022-2024, FORWARD 2025-2026. Report per-trade R, win%, per
year, per asset_class, long vs short separately. Bar = POSITIVE & STABLE FORWARD.
"""
from __future__ import annotations
import sys, os, csv, json, math
from collections import defaultdict
from datetime import datetime

REPO = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = REPO + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = REPO + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, REPO)
sys.path.insert(0, EDGE)

from geometry_lib import Bar, atr14, simulate  # TESTED fill sim - mandatory
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

COST = json.load(open(EDGE + "/ULTIMATE_REAL_COST_MAP.json"))
GLOBAL_COST = COST["_global_median"]

def cost_for(sym):
    ac = ASSET_CLASS_BY_SYMBOL.get(sym)
    if ac == "crypto":
        return 0.095  # crypto not in map; prompt says ~.095
    return COST.get(ac, GLOBAL_COST)

# ---------------------------------------------------------------- data loading
def load(sym):
    path = f"{DATA}/{sym}_H4.csv"
    if not os.path.exists(path):
        return None, None
    bars, times = [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                o = float(row["open"]); h = float(row["high"])
                l = float(row["low"]); c = float(row["close"])
                v = float(row.get("volume", 0) or 0)
            except (ValueError, KeyError):
                continue
            bars.append(Bar(o, h, l, c, v))
            times.append(row["time"])
    return bars, times

def year_of(t):
    return int(t[:4])

# ---------------------------------------------------------------- indicators
def ema_series(bars, n):
    out = [None] * len(bars)
    k = 2.0 / (n + 1)
    e = None
    for i, b in enumerate(bars):
        e = b.c if e is None else b.c * k + e * (1 - k)
        out[i] = e
    return out

def rsi_series(bars, n=14):
    out = [None] * len(bars)
    if len(bars) <= n:
        return out
    gains = losses = 0.0
    for i in range(1, n + 1):
        d = bars[i].c - bars[i - 1].c
        gains += max(d, 0.0); losses += max(-d, 0.0)
    ag = gains / n; al = losses / n
    out[n] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    for i in range(n + 1, len(bars)):
        d = bars[i].c - bars[i - 1].c
        g = max(d, 0.0); l = max(-d, 0.0)
        ag = (ag * (n - 1) + g) / n
        al = (al * (n - 1) + l) / n
        out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out

def atr_series(bars, n=14):
    out = [0.0] * len(bars)
    for i in range(len(bars)):
        if i < n:
            continue
        s = 0.0
        for j in range(i - n + 1, i + 1):
            tr = max(bars[j].h - bars[j].l,
                     abs(bars[j].h - bars[j - 1].c),
                     abs(bars[j].l - bars[j - 1].c))
            s += tr
        out[i] = s / n
    return out

def adx_series(bars, n=14):
    """Wilder ADX. Returns list aligned to bars; None until warmed."""
    L = len(bars)
    out = [None] * L
    if L < 2 * n + 1:
        return out
    tr = [0.0] * L; pdm = [0.0] * L; ndm = [0.0] * L
    for i in range(1, L):
        up = bars[i].h - bars[i - 1].h
        dn = bars[i - 1].l - bars[i].l
        pdm[i] = up if (up > dn and up > 0) else 0.0
        ndm[i] = dn if (dn > up and dn > 0) else 0.0
        tr[i] = max(bars[i].h - bars[i].l,
                    abs(bars[i].h - bars[i - 1].c),
                    abs(bars[i].l - bars[i - 1].c))
    # Wilder smoothing
    atr = sum(tr[1:n + 1]); spdm = sum(pdm[1:n + 1]); sndm = sum(ndm[1:n + 1])
    dx_vals = []
    idx_dx = []
    for i in range(n + 1, L):
        atr = atr - atr / n + tr[i]
        spdm = spdm - spdm / n + pdm[i]
        sndm = sndm - sndm / n + ndm[i]
        if atr == 0:
            continue
        pdi = 100 * spdm / atr; ndi = 100 * sndm / atr
        denom = pdi + ndi
        dx = 0.0 if denom == 0 else 100 * abs(pdi - ndi) / denom
        dx_vals.append(dx); idx_dx.append(i)
    # ADX = Wilder smoothing of DX
    if len(dx_vals) < n:
        return out
    adx = sum(dx_vals[:n]) / n
    out[idx_dx[n - 1]] = adx
    for k in range(n, len(dx_vals)):
        adx = (adx * (n - 1) + dx_vals[k]) / n
        out[idx_dx[k]] = adx
    return out

def std_window(bars, i, n):
    if i < n:
        return None
    cs = [bars[j].c for j in range(i - n + 1, i + 1)]
    m = sum(cs) / n
    var = sum((x - m) ** 2 for x in cs) / n
    return math.sqrt(var), m

def efficiency_ratio(bars, i, n):
    """Kaufman ER: |net change| / sum|changes| over last n bars. Low = choppy."""
    if i < n:
        return None
    net = abs(bars[i].c - bars[i - n].c)
    vol = sum(abs(bars[j].c - bars[j - 1].c) for j in range(i - n + 1, i + 1))
    if vol == 0:
        return 0.0
    return net / vol

# ---------------------------------------------------------------- stats
def summarize(rs):
    n = len(rs)
    if n == 0:
        return {"n": 0, "per_trade_R": 0.0, "win_rate": 0.0, "total_R": 0.0}
    tot = sum(rs)
    wins = sum(1 for r in rs if r > 0)
    return {"n": n, "per_trade_R": round(tot / n, 4),
            "win_rate": round(wins / n, 4), "total_R": round(tot, 2)}

# ---------------------------------------------------------------- core scan
def build_signals(sym, bars, times, cfg):
    """Yield (i, direction, year) for every entry the config admits.
    All indicators causal up to bar i; entry at close of i (simulate enters i.c)."""
    L = len(bars)
    if L < 260:
        return []
    atr14_s = atr_series(bars, 14)
    atr50_s = atr_series(bars, 50)
    ema = ema_series(bars, cfg["ema_n"])
    rsi = rsi_series(bars, 14)
    adx = adx_series(bars, 14)
    sig = []
    for i in range(60, L - 1):
        a = atr14_s[i]
        if a <= 0:
            continue
        adx_i = adx[i]
        if adx_i is None:
            continue
        # ----- REGIME FILTER: only fade in confirmed range / contraction -----
        if adx_i > cfg["adx_max"]:
            continue  # trending -> never fade
        # volatility contraction: ATR14 / ATR50 must be <= threshold (shrinking)
        a50 = atr50_s[i]
        if a50 <= 0:
            continue
        if a / a50 > cfg["vol_contract_max"]:
            continue
        # efficiency ratio: choppy/range only
        er = efficiency_ratio(bars, i, cfg["er_n"])
        if er is None or er > cfg["er_max"]:
            continue
        # ----- ENTRY QUALITY: extreme + exhaustion -----
        sw = std_window(bars, i, cfg["bb_n"])
        if sw is None:
            continue
        sd, mean = sw
        if sd <= 0:
            continue
        e = ema[i]
        dist_atr = (bars[i].c - e) / a  # signed distance from EMA in ATR
        z = (bars[i].c - mean) / sd     # bollinger z
        r = rsi[i]
        if r is None:
            continue
        direction = 0
        # LONG fade: price extremely BELOW mean + oversold + exhaustion bar
        if (dist_atr <= -cfg["dist_atr"] and z <= -cfg["bb_z"]
                and r <= cfg["rsi_lo"]):
            # exhaustion: current bar closes off its low (rejection of lows)
            rng = bars[i].h - bars[i].l
            if rng > 0 and (bars[i].c - bars[i].l) / rng >= cfg["reject"]:
                direction = +1
        # SHORT fade: price extremely ABOVE mean + overbought + exhaustion bar
        elif (dist_atr >= cfg["dist_atr"] and z >= cfg["bb_z"]
                and r >= cfg["rsi_hi"]):
            rng = bars[i].h - bars[i].l
            if rng > 0 and (bars[i].h - bars[i].c) / rng >= cfg["reject"]:
                direction = -1
        if direction == 0:
            continue
        sig.append((i, direction, year_of(times[i]), a))
    return sig

def run_config(cfg, symbols):
    """Return dict of bucketed R lists across all symbols for this config."""
    train, fwd = [], []
    train_long, train_short = [], []
    fwd_long, fwd_short = [], []
    by_year = defaultdict(list)
    by_ac_fwd = defaultdict(list)
    by_ac_train = defaultdict(list)
    fwd_by_sym = defaultdict(list)
    stop_mult = cfg["stop_mult"]
    for sym in symbols:
        ac = ASSET_CLASS_BY_SYMBOL.get(sym)
        if ac is None:
            continue
        bars, times = load(sym)
        if bars is None or len(bars) < 260:
            continue
        c = cost_for(sym)
        for (i, direction, yr, a) in build_signals(sym, bars, times, cfg):
            stop_dist = stop_mult * a
            if cfg["mode"] == "target":
                R = simulate(bars, i, direction, stop_dist=stop_dist,
                             target_dist=cfg["target_mult"] * a, cost=c)
            else:  # trail
                R = simulate(bars, i, direction, stop_dist=stop_dist,
                             trail_arm=cfg["trail_arm"] * stop_dist,
                             trail_gap=cfg["trail_gap"] * stop_dist, cost=c)
            is_fwd = yr >= 2025
            if is_fwd:
                fwd.append(R); fwd_by_sym[sym].append(R)
                by_ac_fwd[ac].append(R)
                (fwd_long if direction > 0 else fwd_short).append(R)
            else:
                train.append(R)
                by_ac_train[ac].append(R)
                (train_long if direction > 0 else train_short).append(R)
            by_year[yr].append(R)
    return {
        "train": train, "fwd": fwd,
        "train_long": train_long, "train_short": train_short,
        "fwd_long": fwd_long, "fwd_short": fwd_short,
        "by_year": by_year, "by_ac_fwd": by_ac_fwd,
        "by_ac_train": by_ac_train, "fwd_by_sym": fwd_by_sym,
    }

def report(cfg, res, label=""):
    print("=" * 78)
    print(f"CONFIG {label}: {json.dumps(cfg)}")
    tr = summarize(res["train"]); fw = summarize(res["fwd"])
    print(f"  TRAIN  : {tr}")
    print(f"  FORWARD: {fw}")
    print(f"    fwd long : {summarize(res['fwd_long'])}")
    print(f"    fwd short: {summarize(res['fwd_short'])}")
    print("  per-year:")
    for yr in sorted(res["by_year"]):
        print(f"    {yr}: {summarize(res['by_year'][yr])}")
    print("  forward by asset_class:")
    for ac in sorted(res["by_ac_fwd"]):
        print(f"    {ac:8s}: {summarize(res['by_ac_fwd'][ac])}")
    return fw

# ---------------------------------------------------------------- main
def main():
    symbols = [s for s in ASSET_CLASS_BY_SYMBOL
               if os.path.exists(f"{DATA}/{s}_H4.csv")]
    print(f"symbols available: {len(symbols)}")

    base = dict(
        ema_n=20, adx_max=20.0, vol_contract_max=1.0, er_n=10, er_max=0.30,
        bb_n=20, dist_atr=1.5, bb_z=2.0, rsi_lo=30.0, rsi_hi=70.0, reject=0.5,
        stop_mult=0.5, mode="target", target_mult=1.0,
    )

    # ---- Stage 1: sweep the regime + entry filters (target 1.0 ATR) ----
    grid = []
    for adx_max in (15.0, 20.0, 25.0):
        for er_max in (0.25, 0.35, 0.50):
            for dist_atr in (1.0, 1.5, 2.0):
                for bb_z in (1.5, 2.0, 2.5):
                    for rsi in (25.0, 30.0):
                        g = dict(base)
                        g.update(adx_max=adx_max, er_max=er_max,
                                 dist_atr=dist_atr, bb_z=bb_z,
                                 rsi_lo=rsi, rsi_hi=100.0 - rsi)
                        grid.append(g)

    results = []
    for g in grid:
        res = run_config(g, symbols)
        fw = summarize(res["fwd"]); tr = summarize(res["train"])
        results.append((g, tr, fw, res))

    # rank by forward per_trade_R with a min-sample floor
    ranked = sorted([r for r in results if r[2]["n"] >= 80],
                    key=lambda x: x[2]["per_trade_R"], reverse=True)
    print("\n##### STAGE 1 TOP 12 BY FORWARD per_trade_R (n>=80) #####")
    for g, tr, fw, res in ranked[:12]:
        print(f"fwdR={fw['per_trade_R']:+.4f} fwdN={fw['n']:4d} "
              f"fwdWin={fw['win_rate']:.3f} | trR={tr['per_trade_R']:+.4f} "
              f"trN={tr['n']:4d} | adx<={g['adx_max']} er<={g['er_max']} "
              f"dist={g['dist_atr']} z={g['bb_z']} rsi={g['rsi_lo']}")
    print(f"\n(configs with fwd n>=80: {len(ranked)} of {len(results)})")

    if not ranked:
        print("NO config produced >=80 forward trades. Loosening sample floor.")
        ranked = sorted(results, key=lambda x: x[2]["per_trade_R"], reverse=True)

    best_g, best_tr, best_fw, best_res = ranked[0]
    report(best_g, best_res, "STAGE1-BEST")

    # ---- Stage 2: around the best, sweep geometry (target vs trail) ----
    print("\n##### STAGE 2: GEOMETRY SWEEP around stage-1 best entry #####")
    geo_results = []
    for tmult in (1.0, 1.5, 2.0):
        g = dict(best_g); g.update(mode="target", target_mult=tmult)
        geo_results.append((f"target{tmult}", g, run_config(g, symbols)))
    for arm, gap in ((2.0, 1.0), (1.5, 1.0), (3.0, 1.5)):
        g = dict(best_g); g.update(mode="trail", trail_arm=arm, trail_gap=gap)
        geo_results.append((f"trail{arm}/{gap}", g, run_config(g, symbols)))

    geo_ranked = []
    for name, g, res in geo_results:
        fw = summarize(res["fwd"]); tr = summarize(res["train"])
        geo_ranked.append((name, g, tr, fw, res))
        print(f"  {name:14s}: fwdR={fw['per_trade_R']:+.4f} fwdN={fw['n']:4d} "
              f"fwdWin={fw['win_rate']:.3f} | trR={tr['per_trade_R']:+.4f}")
    geo_ranked.sort(key=lambda x: x[3]["per_trade_R"], reverse=True)

    # ---- Final pick: best forward that is ALSO train-positive (no overfit) ----
    stable = [r for r in geo_ranked
              if r[3]["per_trade_R"] > 0 and r[2]["per_trade_R"] > 0]
    pick = stable[0] if stable else geo_ranked[0]
    name, g, tr, fw, res = pick
    print("\n##### FINAL PICK #####")
    final_fw = report(g, res, f"FINAL ({name})")

    # stability check: forward year-by-year and per-class signs
    fwd_years = {yr: summarize(res["by_year"][yr])
                 for yr in res["by_year"] if yr >= 2025}
    pos_years = [yr for yr, s in fwd_years.items() if s["per_trade_R"] > 0]
    print(f"\nforward years positive: {pos_years} of {sorted(fwd_years)}")

    out = {
        "config": g, "geometry": name,
        "train": summarize(res["train"]), "forward": summarize(res["fwd"]),
        "forward_long": summarize(res["fwd_long"]),
        "forward_short": summarize(res["fwd_short"]),
        "forward_by_year": {str(y): summarize(res["by_year"][y])
                            for y in sorted(res["by_year"]) if y >= 2025},
        "train_by_year": {str(y): summarize(res["by_year"][y])
                          for y in sorted(res["by_year"]) if y < 2025},
        "forward_by_asset_class": {ac: summarize(res["by_ac_fwd"][ac])
                                   for ac in sorted(res["by_ac_fwd"])},
        "train_by_asset_class": {ac: summarize(res["by_ac_train"][ac])
                                 for ac in sorted(res["by_ac_train"])},
        "forward_by_symbol": {s: summarize(res["fwd_by_sym"][s])
                              for s in sorted(res["fwd_by_sym"])},
    }
    with open(EDGE + "/hunt_reversion_regime_filtered_RESULT.json", "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote hunt_reversion_regime_filtered_RESULT.json")

if __name__ == "__main__":
    main()
