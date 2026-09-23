"""
hunt_key_level_reaction.py
==========================
Signal class: KEY_LEVEL_REACTION.

Reaction at HTF key levels & liquidity pools:
  - prior-day / prior-week high & low  (PDH/PDL/PWH/PWL)
  - round numbers (psychological levels)
  - multi-touch horizontal S/R
  - equal-highs / equal-lows (liquidity pools)

Two structural entry archetypes at each level:
  REJECTION (fade): price tags the level and closes back away from it
                    -> enter AGAINST the test (mean-revert off the level)
  BREAK-RETEST (continuation): price breaks the level, comes back to retest it
                    from the other side, and holds -> enter WITH the break

Discipline:
  - TRAIN 2022-2024 / FORWARD 2025-2026
  - per-trade R, win%, per-year, by asset_class, long/short separate
  - ALL fills via the TESTED geometry_lib.simulate (no homegrown stop/target logic)
  - real per-asset cost from ULTIMATE_REAL_COST_MAP.json
  - bar is POSITIVE & STABLE IN FORWARD. No rejection theater.

H4 bars. We derive "day"/"week" level references from the H4 series itself
(prior calendar day's H/L, prior calendar week's H/L) — strictly using only
bars STRICTLY BEFORE the signal bar (no lookahead).
"""
from __future__ import annotations
import sys, os, csv, json, math
from datetime import datetime, timedelta
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
DATA = ROOT + "/data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026"
sys.path.insert(0, ROOT)
sys.path.insert(0, EDGE)

from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
from geometry_lib import Bar, atr14, simulate

with open(EDGE + "/ULTIMATE_REAL_COST_MAP.json") as f:
    COSTMAP = json.load(f)
GLOBAL_COST = COSTMAP["_global_median"]

def cost_for(sym):
    ac = ASSET_CLASS_BY_SYMBOL.get(sym)
    return COSTMAP.get(ac, GLOBAL_COST)

# ---------------------------------------------------------------- load
def load(sym):
    path = f"{DATA}/{sym}_H4.csv"
    if not os.path.exists(path): return None, None
    times, bars = [], []
    with open(path) as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                t = datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
                o = float(row["open"]); h = float(row["high"]); l = float(row["low"]); c = float(row["close"])
                v = float(row.get("volume", 0) or 0)
            except Exception:
                continue
            times.append(t); bars.append(Bar(o, h, l, c, v))
    return times, bars

SYMBOLS = [fn[:-7] for fn in sorted(os.listdir(DATA)) if fn.endswith("_H4.csv")]

# ---------------------------------------------------------------- level references (no lookahead)
def build_day_week_levels(times, bars):
    """For each bar index i, return prior-day H/L and prior-week H/L
    computed ONLY from bars with index < i (strict). Returns lists aligned to i."""
    n = len(bars)
    # group bar indices by calendar day and ISO week
    day_key = [t.date() for t in times]
    week_key = [t.isocalendar()[:2] for t in times]  # (year, week)
    # cumulative per-day / per-week H/L as we walk; we want PRIOR completed day/week
    pdh = [None]*n; pdl = [None]*n; pwh = [None]*n; pwl = [None]*n
    # track completed-day extremes
    cur_day = None; cur_dh = None; cur_dl = None
    last_complete_dh = None; last_complete_dl = None
    cur_week = None; cur_wh = None; cur_wl = None
    last_complete_wh = None; last_complete_wl = None
    for i in range(n):
        # at bar i, the "prior completed" day/week reflects everything before today/this-week
        if day_key[i] != cur_day:
            # day rolled -> previous current day becomes last complete
            if cur_day is not None:
                last_complete_dh = cur_dh; last_complete_dl = cur_dl
            cur_day = day_key[i]; cur_dh = bars[i].h; cur_dl = bars[i].l
        else:
            cur_dh = max(cur_dh, bars[i].h); cur_dl = min(cur_dl, bars[i].l)
        if week_key[i] != cur_week:
            if cur_week is not None:
                last_complete_wh = cur_wh; last_complete_wl = cur_wl
            cur_week = week_key[i]; cur_wh = bars[i].h; cur_wl = bars[i].l
        else:
            cur_wh = max(cur_wh, bars[i].h); cur_wl = min(cur_wl, bars[i].l)
        pdh[i] = last_complete_dh; pdl[i] = last_complete_dl
        pwh[i] = last_complete_wh; pwl[i] = last_complete_wl
    return pdh, pdl, pwh, pwl

def round_levels_near(price, atr, sym):
    """Return nearest round-number levels above & below price.
    Round-number step chosen so step ~ a meaningful fraction of price/atr.
    We use a per-symbol decimal step derived from price magnitude."""
    if price <= 0 or atr <= 0: return None, None
    # choose step = 10^floor(log10(price)) / 10  (e.g. price 1.13 -> step 0.01;
    # price 1900 -> step 100; price 18000 -> step 1000; price 150 -> step 10)
    mag = math.floor(math.log10(abs(price)))
    step = 10 ** (mag - 1)
    if step <= 0: return None, None
    below = math.floor(price / step) * step
    above = below + step
    return below, above

# ---------------------------------------------------------------- equal highs/lows + multitouch
def swing_points(bars, i, lb=2):
    """is bar i a local swing high/low using lb bars each side (only past data ok if i<=end)."""
    pass  # inlined below for speed

# ---------------------------------------------------------------- core experiment
def run_config(cfg):
    """cfg dict -> aggregated stats. Returns dict."""
    level_kinds   = cfg["levels"]        # subset of {'pd','pw','round','eqhl'}
    mode          = cfg["mode"]          # 'reject' or 'breakretest'
    tol_atr       = cfg["tol_atr"]       # proximity tolerance in ATR units
    stop_mult     = cfg["stop_mult"]     # stop_dist = stop_mult*atr  (None => structural)
    structural_pad= cfg.get("structural_pad", 0.25)  # extra atr pad beyond level for structural stop
    exit_mode     = cfg["exit"]          # ('target', mult) or ('trail', arm, gap)
    require_close = cfg.get("require_close", True)
    eqhl_lb       = cfg.get("eqhl_lb", 3)
    eqhl_tol_atr  = cfg.get("eqhl_tol_atr", 0.15)
    multitouch    = cfg.get("multitouch", 0)  # min prior touches required for S/R cluster
    min_atr_frac  = cfg.get("min_atr_frac", 0.0)  # require atr/price >= this (skip dead markets)

    # accumulators: keyed (period, side) -> list of R
    agg = defaultdict(list)
    by_class = defaultdict(lambda: defaultdict(list))  # class -> (period,side) -> R
    by_year  = defaultdict(lambda: defaultdict(list))  # year -> side -> R

    for sym in SYMBOLS:
        times, bars = load(sym)
        if not bars or len(bars) < 200: continue
        ac = ASSET_CLASS_BY_SYMBOL.get(sym, "?")
        cost = cost_for(sym)
        n = len(bars)
        pdh, pdl, pwh, pwl = build_day_week_levels(times, bars)
        atrs = [atr14(bars, i) for i in range(n)]

        # precompute swing highs/lows (confirmed, using only fully-formed neighbors)
        # a swing high at k requires bars[k].h > neighbors within eqhl_lb both sides.
        # We will only USE swings with index < i (strictly past) so no lookahead.
        sw_high_idx = []  # list of (idx, price)
        sw_low_idx  = []
        for k in range(eqhl_lb, n - eqhl_lb):
            seg = bars[k-eqhl_lb:k+eqhl_lb+1]
            if bars[k].h == max(b.h for b in seg) and bars[k].h > bars[k-1].h and bars[k].h >= bars[k+1].h:
                sw_high_idx.append(k)
            if bars[k].l == min(b.l for b in seg) and bars[k].l < bars[k-1].l and bars[k].l <= bars[k+1].l:
                sw_low_idx.append(k)
        # for fast prior-swing lookup keep sorted arrays
        sw_high_idx.sort(); sw_low_idx.sort()

        # pointer-walk for swings confirmed before i (need k+eqhl_lb < i to be confirmed)
        hi_ptr = 0; lo_ptr = 0
        confirmed_highs = []  # prices of confirmed swing highs so far
        confirmed_lows  = []
        confirmed_high_k = []
        confirmed_low_k  = []

        for i in range(60, n - 1):
            atr = atrs[i]
            if atr <= 0: continue
            price = bars[i].c
            if min_atr_frac > 0 and price > 0 and atr/price < min_atr_frac: continue

            # advance confirmed swing lists: a swing at k is confirmed once k+eqhl_lb < i
            while hi_ptr < len(sw_high_idx) and sw_high_idx[hi_ptr] + eqhl_lb < i:
                k = sw_high_idx[hi_ptr]; confirmed_highs.append(bars[k].h); confirmed_high_k.append(k); hi_ptr += 1
            while lo_ptr < len(sw_low_idx) and sw_low_idx[lo_ptr] + eqhl_lb < i:
                k = sw_low_idx[lo_ptr]; confirmed_lows.append(bars[k].l); confirmed_low_k.append(k); lo_ptr += 1

            tol = tol_atr * atr

            # ---- collect candidate levels (level_price, is_resistance) ----
            # is_resistance True => level sits ABOVE/at as overhead supply; a reject there is SHORT.
            res_levels = []  # overhead levels (price tests up into them)
            sup_levels = []  # underfoot levels (price tests down into them)

            if 'pd' in level_kinds:
                if pdh[i] is not None: res_levels.append(('pdh', pdh[i]))
                if pdl[i] is not None: sup_levels.append(('pdl', pdl[i]))
            if 'pw' in level_kinds:
                if pwh[i] is not None: res_levels.append(('pwh', pwh[i]))
                if pwl[i] is not None: sup_levels.append(('pwl', pwl[i]))
            if 'round' in level_kinds:
                below, above = round_levels_near(price, atr, sym)
                if above is not None: res_levels.append(('rnd', above))
                if below is not None: sup_levels.append(('rnd', below))
            if 'eqhl' in level_kinds:
                # equal highs: cluster of confirmed swing highs within eqhl_tol_atr*atr
                # take the most recent confirmed swing high/low above/below price
                etol = eqhl_tol_atr * atr
                # nearest overhead equal-high cluster
                # find recent swing highs above price; count cluster members near the topmost-relevant
                cand_h = [(k,p) for k,p in zip(confirmed_high_k, confirmed_highs) if p >= price - tol]
                if cand_h:
                    # use the closest above price
                    cand_h_above = sorted([(p,k) for k,p in cand_h if p >= price - tol], key=lambda x: x[0])
                    if cand_h_above:
                        lvl = cand_h_above[0][0]
                        cluster = sum(1 for k,p in zip(confirmed_high_k, confirmed_highs) if abs(p-lvl) <= etol)
                        if cluster >= max(1, multitouch):
                            res_levels.append(('eqh', lvl))
                cand_l = [(k,p) for k,p in zip(confirmed_low_k, confirmed_lows) if p <= price + tol]
                if cand_l:
                    cand_l_below = sorted([(p,k) for k,p in cand_l if p <= price + tol], key=lambda x: -x[0])
                    if cand_l_below:
                        lvl = cand_l_below[0][0]
                        cluster = sum(1 for k,p in zip(confirmed_low_k, confirmed_lows) if abs(p-lvl) <= etol)
                        if cluster >= max(1, multitouch):
                            sup_levels.append(('eql', lvl))

            yr = times[i].year
            in_train = yr <= 2024

            # ---- evaluate REJECTION mode ----
            if mode == 'reject':
                # overhead resistance: bar wicks up into level then closes back below -> SHORT
                for name, lvl in res_levels:
                    if bars[i].h >= lvl - tol and bars[i].h >= lvl*0  + (lvl - tol):
                        # test: high reached the level zone
                        if bars[i].h >= lvl - tol:
                            tagged = bars[i].h >= lvl - tol
                            # rejection close: close back below the level (and below open => bearish bar)
                            cond = (bars[i].c < lvl) if require_close else True
                            cond = cond and (bars[i].c < bars[i].o)
                            if tagged and cond:
                                # structural stop just above the tested high / level
                                if stop_mult is not None:
                                    sd = stop_mult * atr
                                else:
                                    sd = (bars[i].h - bars[i].c) + structural_pad*atr
                                    sd = max(sd, 0.2*atr)
                                _emit(-1, sym, ac, name, 'short', i, bars, sd, exit_mode, cost,
                                      agg, by_class, by_year, yr)
                # underfoot support: bar wicks down into level then closes back above -> LONG
                for name, lvl in sup_levels:
                    if bars[i].l <= lvl + tol:
                        cond = (bars[i].c > lvl) if require_close else True
                        cond = cond and (bars[i].c > bars[i].o)
                        if cond:
                            if stop_mult is not None:
                                sd = stop_mult * atr
                            else:
                                sd = (bars[i].c - bars[i].l) + structural_pad*atr
                                sd = max(sd, 0.2*atr)
                            _emit(+1, sym, ac, name, 'long', i, bars, sd, exit_mode, cost,
                                  agg, by_class, by_year, yr)

            # ---- evaluate BREAK-RETEST mode ----
            elif mode == 'breakretest':
                # break of resistance then retest from above -> LONG continuation.
                # Detect: in prior W bars price closed above the level (break), now pulls back to it and holds.
                W = cfg.get("retest_window", 6)
                for name, lvl in res_levels:
                    # was there a recent close above lvl in (i-W, i-1)?
                    broke = any(bars[j].c > lvl + 0.1*tol for j in range(max(0,i-W), i))
                    if broke and bars[i].l <= lvl + tol and bars[i].c > lvl and bars[i].c > bars[i].o:
                        if stop_mult is not None:
                            sd = stop_mult * atr
                        else:
                            sd = (bars[i].c - min(bars[i].l, lvl - structural_pad*atr))
                            sd = max(sd, 0.2*atr)
                        _emit(+1, sym, ac, name, 'long', i, bars, sd, exit_mode, cost,
                              agg, by_class, by_year, yr)
                for name, lvl in sup_levels:
                    broke = any(bars[j].c < lvl - 0.1*tol for j in range(max(0,i-W), i))
                    if broke and bars[i].h >= lvl - tol and bars[i].c < lvl and bars[i].c < bars[i].o:
                        if stop_mult is not None:
                            sd = stop_mult * atr
                        else:
                            sd = (max(bars[i].h, lvl + structural_pad*atr) - bars[i].c)
                            sd = max(sd, 0.2*atr)
                        _emit(-1, sym, ac, name, 'short', i, bars, sd, exit_mode, cost,
                              agg, by_class, by_year, yr)

    return _summarize(agg, by_class, by_year)


def _emit(direction, sym, ac, name, side, i, bars, sd, exit_mode, cost, agg, by_class, by_year, yr):
    if sd <= 0: return
    if exit_mode[0] == 'target':
        td = exit_mode[1] * sd  # target_dist as multiple of stop_dist (R multiple)
        r = simulate(bars, i, direction, stop_dist=sd, target_dist=td, cost=cost)
    else:  # trail
        arm = exit_mode[1] * sd; gap = exit_mode[2] * sd
        r = simulate(bars, i, direction, stop_dist=sd, trail_arm=arm, trail_gap=gap, cost=cost)
    period = 'train' if yr <= 2024 else 'forward'
    agg[(period, side)].append(r)
    agg[(period, 'all')].append(r)
    by_class[ac][(period, side)].append(r)
    by_class[ac][(period, 'all')].append(r)
    by_year[yr][side].append(r)
    by_year[yr]['all'].append(r)


def _stats(rs):
    if not rs: return {"n": 0, "mean_R": 0.0, "win%": 0.0, "sum_R": 0.0}
    n = len(rs); s = sum(rs); wins = sum(1 for r in rs if r > 0)
    return {"n": n, "mean_R": round(s/n, 4), "win%": round(100*wins/n, 1), "sum_R": round(s, 1)}


def _summarize(agg, by_class, by_year):
    out = {"overall": {}, "by_class": {}, "by_year": {}}
    for key in [('train','all'),('train','long'),('train','short'),
                ('forward','all'),('forward','long'),('forward','short')]:
        out["overall"]["_".join(key)] = _stats(agg.get(key, []))
    for ac, d in by_class.items():
        out["by_class"][ac] = {
            "forward_all": _stats(d.get(('forward','all'), [])),
            "forward_long": _stats(d.get(('forward','long'), [])),
            "forward_short": _stats(d.get(('forward','short'), [])),
            "train_all": _stats(d.get(('train','all'), [])),
        }
    for yr, d in sorted(by_year.items()):
        out["by_year"][str(yr)] = {
            "all": _stats(d.get('all', [])),
            "long": _stats(d.get('long', [])),
            "short": _stats(d.get('short', [])),
        }
    return out


def main():
    base_exits = {
        "t1.0": ('target', 1.0),
        "t1.5": ('target', 1.5),
        "t2.0": ('target', 2.0),
        "trail": ('trail', 2.0, 1.0),
    }
    configs = []
    # Mode: rejection at various level families, fixed 0.5 ATR stop (vindicated noise floor)
    for levels in [('pd',), ('pw',), ('round',), ('eqhl',), ('pd','pw'), ('pd','pw','round','eqhl')]:
        for exname, ex in base_exits.items():
            configs.append({
                "name": f"reject|{'+'.join(levels)}|stop0.5|{exname}",
                "levels": levels, "mode": "reject", "tol_atr": 0.25,
                "stop_mult": 0.5, "exit": ex, "require_close": True,
                "eqhl_lb": 3, "eqhl_tol_atr": 0.15, "multitouch": 2,
            })
    # Break-retest
    for levels in [('pd','pw'), ('pd','pw','round'), ('eqhl',), ('pd','pw','round','eqhl')]:
        for exname, ex in base_exits.items():
            configs.append({
                "name": f"breakretest|{'+'.join(levels)}|stop0.5|{exname}",
                "levels": levels, "mode": "breakretest", "tol_atr": 0.25,
                "stop_mult": 0.5, "exit": ex, "require_close": True,
                "retest_window": 6, "eqhl_lb": 3, "eqhl_tol_atr": 0.15, "multitouch": 2,
            })

    results = {}
    for cfg in configs:
        res = run_config(cfg)
        results[cfg["name"]] = {"cfg": {k:v for k,v in cfg.items() if k!='name'}, "result": res}
        ov = res["overall"]
        print(f"\n=== {cfg['name']} ===")
        print(f"  TRAIN   all  n={ov['train_all']['n']:6d} meanR={ov['train_all']['mean_R']:+.4f} win={ov['train_all']['win%']:.1f}%")
        print(f"  FORWARD all  n={ov['forward_all']['n']:6d} meanR={ov['forward_all']['mean_R']:+.4f} win={ov['forward_all']['win%']:.1f}%")
        print(f"  FORWARD long n={ov['forward_long']['n']:6d} meanR={ov['forward_long']['mean_R']:+.4f} | short n={ov['forward_short']['n']:6d} meanR={ov['forward_short']['mean_R']:+.4f}")

    with open(EDGE + "/HUNT_KEY_LEVEL_REACTION_RESULT.json", "w") as f:
        json.dump(results, f, indent=1)
    print("\nWROTE HUNT_KEY_LEVEL_REACTION_RESULT.json")

if __name__ == "__main__":
    main()
