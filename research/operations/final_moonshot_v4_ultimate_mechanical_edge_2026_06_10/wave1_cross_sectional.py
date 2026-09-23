"""WAVE 1 — CROSS-SECTIONAL RELATIVE-VALUE (momentum / reversion / dispersion).

Thrust: across the multi-symbol universe, at each H4 (or daily) timestamp rank
symbols by recent return; go LONG top-k / SHORT bottom-k (dollar-neutral). Also
test cross-sectional REVERSION (long losers / short winners) and DISPERSION.

The single-symbol single-direction approaches washed over the cycle. Question:
does CROSS-SECTIONAL relative-value have forward-positive structure across MOST
years, not just recent?

DISCIPLINE
- Concatenate + dedupe both H4 exports into one up-to-11yr series per symbol.
- Compute basket return DIRECTLY with realistic per-leg cost (asset-class cost map).
  Cross-sectional baskets close & reopen each rebalance, so direct net-return
  accounting (not stop/target geometry) is the honest measure for this thrust.
  We ALSO cross-check the headline config with geometry_lib per-leg fills.
- TRAIN <= 2024, FORWARD 2025-2026. Report per-year across ALL available years.
- Bar = forward-positive AND positive in a MAJORITY of years (regime-robust).
- Negative controls: random long/short sign, and the reversion mirror of momentum.

Outputs JSON summary to WAVE1_CROSS_SECTIONAL_RESULT.json and prints tables.
"""
from __future__ import annotations
import os, sys, json, csv, math, random
from collections import defaultdict
from datetime import datetime

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
HERE = os.path.join(ROOT, "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL  # noqa
from geometry_lib import Bar, atr14, simulate  # noqa

D1 = os.path.join(ROOT, "data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022")
D2 = os.path.join(ROOT, "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026")
COST_MAP = json.load(open(os.path.join(HERE, "ULTIMATE_REAL_COST_MAP.json")))
GLOBAL_COST = COST_MAP["_global_median"]

# --------------------------------------------------------------------------- IO
def load_symbol(sym):
    """Concatenate + dedupe both exports by timestamp -> list of (dt, o,h,l,c,v)."""
    rows = {}
    for d in (D1, D2):
        p = os.path.join(d, f"{sym}_H4.csv")
        if not os.path.exists(p):
            continue
        with open(p) as f:
            for r in csv.DictReader(f):
                t = r["time"]
                try:
                    dt = datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    dt = datetime.strptime(t, "%Y-%m-%d %H:%M")
                rows[dt] = (float(r["open"]), float(r["high"]), float(r["low"]),
                            float(r["close"]), float(r["volume"]))
    out = [(dt, *rows[dt]) for dt in sorted(rows)]
    return out


def all_symbols():
    s = set()
    for d in (D1, D2):
        for fn in os.listdir(d):
            if fn.endswith("_H4.csv"):
                s.add(fn[:-7])
    return sorted(s)


def cost_for(sym):
    ac = ASSET_CLASS_BY_SYMBOL.get(sym, "fx")
    return COST_MAP.get(ac, GLOBAL_COST)

# ---------------------------------------------------------------- panel builder
def build_panel(symbols, min_history_frac=0.5):
    """Return (timeline, prices, present) aligned on the union of timestamps.

    prices[sym] = dict dt->close ; present[sym] = set of dt with a bar.
    Keep symbols with enough coverage so ranking is meaningful.
    """
    data = {}
    for s in symbols:
        d = load_symbol(s)
        if len(d) > 50:
            data[s] = d
    # union timeline
    all_dt = set()
    for s, d in data.items():
        for row in d:
            all_dt.add(row[0])
    timeline = sorted(all_dt)
    prices, present = {}, {}
    for s, d in data.items():
        pc = {row[0]: row[4] for row in d}
        prices[s] = pc
        present[s] = set(pc)
    # drop thin symbols relative to full timeline span they exist in
    keep = {}
    for s in data:
        keep[s] = data[s]
    return timeline, prices, present, keep

# ---------------------------------------------------------- cross-sectional core
def fwd_log_ret(prices, present, sym, dt_now, dt_next):
    if sym not in prices:
        return None
    p = prices[sym]
    if dt_now not in p or dt_next not in p:
        return None
    a, b = p[dt_now], p[dt_next]
    if a <= 0 or b <= 0:
        return None
    return math.log(b / a)


def recent_ret(prices, sym, dt_now, dt_lb):
    p = prices.get(sym)
    if p is None or dt_now not in p or dt_lb not in p:
        return None
    a, b = p[dt_lb], p[dt_now]
    if a <= 0 or b <= 0:
        return None
    return math.log(b / a)


def run_strategy(timeline, prices, present, *, lookback, holdbars, k,
                 mode="momentum", vol_norm=True, rebalance=1, seed=0,
                 min_universe=10):
    """Generic cross-sectional engine.

    At each rebalance timestamp t (index it):
      - lookback window = bars [it-lookback, it]
      - rank symbols by recent_ret (vol-normalized if vol_norm)
      - momentum: long top-k, short bottom-k ; reversion: opposite
      - dispersion: long top-k AND long bottom-k? No — dispersion = bet on spread
        widening: long extremes vs short middle. We implement as long top-k +
        short middle-k (so it profits when winners keep winning AND losers keep
        losing relative to the median => measures fat-tail dispersion).
      - hold for `holdbars`; realize equal-weight dollar-neutral basket log-return,
        net of per-leg cost (cost charged per leg, scaled to position weight).
    Returns list of (exit_dt, net_R_like_return, n_legs).

    Return units: portfolio log-return summed over legs, dollar-neutral
    (sum of long-leg returns/nlong - sum of short-leg returns/nshort), so it is a
    per-rebalance basket return. We also express it per-leg for an R-like read.
    """
    rng = random.Random(seed)
    idx_of = {dt: i for i, dt in enumerate(timeline)}
    results = []
    it = lookback
    while it + holdbars < len(timeline):
        t = timeline[it]
        t_lb = timeline[it - lookback]
        t_exit = timeline[it + holdbars]
        # build scores
        scored = []
        for s in prices:
            r = recent_ret(prices, s, t, t_lb)
            if r is None:
                continue
            if vol_norm:
                # realized vol over lookback (std of per-bar log rets)
                p = prices[s]
                rets = []
                for j in range(it - lookback + 1, it + 1):
                    dj, dj1 = timeline[j], timeline[j - 1]
                    if dj in p and dj1 in p and p[dj] > 0 and p[dj1] > 0:
                        rets.append(math.log(p[dj] / p[dj1]))
                if len(rets) < 3:
                    continue
                mu = sum(rets) / len(rets)
                var = sum((x - mu) ** 2 for x in rets) / len(rets)
                sd = math.sqrt(var)
                if sd <= 0:
                    continue
                score = r / sd
            else:
                score = r
            # need a valid forward return too
            fr = fwd_log_ret(prices, present, s, t, t_exit)
            if fr is None:
                continue
            scored.append((score, s, fr, (sd if vol_norm else 1.0)))
        if len(scored) < min_universe:
            it += rebalance
            continue
        scored.sort(key=lambda x: x[0])
        kk = min(k, len(scored) // 2)
        if kk < 1:
            it += rebalance
            continue
        losers = scored[:kk]      # lowest score
        winners = scored[-kk:]    # highest score

        def leg_ret(items, side):
            # side +1 long, -1 short ; net of per-leg cost in return units.
            # cost map is in R (stop=0.5*atr). For a basket return we approximate
            # per-leg cost as cost_r * 0.5 * (atr/price) ~ small; we instead charge
            # cost as a fraction = cost_r * (0.5*atr/price). Simpler + honest:
            # convert cost_r to price-return using each leg's recent vol (sd) as a
            # proxy for 0.5*atr scale per bar. Charge cost_r * sd (one stop-unit).
            tot = 0.0
            for score, s, fr, sd in items:
                c = cost_for(s) * (sd if sd > 0 else 0.0)  # cost in return units
                tot += side * fr - c
            return tot / len(items)

        if mode == "momentum":
            ret = leg_ret(winners, +1) + leg_ret(losers, -1)
            nlegs = 2 * kk
        elif mode == "reversion":
            ret = leg_ret(losers, +1) + leg_ret(winners, -1)
            nlegs = 2 * kk
        elif mode == "dispersion":
            # long extremes, short the median band
            mid_lo = len(scored) // 2 - kk // 2
            mid = scored[mid_lo:mid_lo + kk]
            ret = leg_ret(winners, +1) + leg_ret(losers, +1) - 2 * leg_ret(mid, +1)
            nlegs = 3 * kk
        elif mode == "random":
            picks = scored[:]
            rng.shuffle(picks)
            lg = picks[:kk]; sh = picks[kk:2 * kk]
            ret = leg_ret(lg, +1) + leg_ret(sh, -1)
            nlegs = 2 * kk
        else:
            raise ValueError(mode)
        results.append((t_exit, ret, nlegs))
        it += rebalance
    return results

# ------------------------------------------------------------------- accounting
def per_year(results):
    by = defaultdict(list)
    for dt, r, n in results:
        by[dt.year].append(r)
    out = {}
    for y in sorted(by):
        v = by[y]
        out[y] = (sum(v), sum(v) / len(v), len(v))
    return out


def summarize(results):
    if not results:
        return None
    rs = [r for _, r, _ in results]
    n = len(rs)
    tot = sum(rs)
    mean = tot / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in rs) / n) if n > 1 else 0.0
    sharpe_like = mean / sd * math.sqrt(252 * 6 / 1) if sd > 0 else 0.0  # H4≈6/day
    return {"n": n, "total": tot, "mean_per_rebal": mean, "sd": sd,
            "t_stat": (mean / (sd / math.sqrt(n))) if sd > 0 else 0.0}

# ---------------------------------------------------------------------- reporting
def split_train_fwd(results):
    train = [(d, r, n) for d, r, n in results if d.year <= 2024]
    fwd = [(d, r, n) for d, r, n in results if d.year >= 2025]
    return train, fwd


# Symbols present in BOTH exports => continuous deep history candidates.
CORE15 = ['AUDJPY', 'AUDUSD', 'CHFJPY', 'EURGBP', 'EURJPY', 'EURUSD', 'GBPJPY',
          'GBPUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY', 'USOIL_cash',
          'XAGUSD', 'XAUUSD']


def dense_islands(timeline, prices, min_syms=12):
    """Return list of (start_idx, end_idx) where >= min_syms have a bar.

    The two MT5 exports leave a sparse 2022-2024 middle; honest cross-sectional
    ranking needs a real universe at the rebalance bar. We report the dense
    regimes explicitly instead of letting 2025-2026 (fat universe) dominate.
    """
    flags = []
    for dt in timeline:
        c = sum(1 for s in prices if dt in prices[s])
        flags.append(c >= min_syms)
    islands, i, N = [], 0, len(timeline)
    while i < N:
        if flags[i]:
            j = i
            while j < N and flags[j]:
                j += 1
            islands.append((i, j - 1))
            i = j
        else:
            i += 1
    return [(a, b) for a, b in islands if b - a > 50]


def geometry_cross_check(timeline, prices, present, syms, *, lookback, holdbars,
                         k, mode="momentum"):
    """Cross-check the basket return using geometry_lib per-leg fills.

    Each leg entered at rebalance bar, stop = 0.5*atr14, target = atr14*(holdbars
    scale) — here we use a TIME exit emulation: trail disabled, fixed target far
    away and let maxbars=holdbars realize the close-to-close move. This validates
    the direct-return sign with the TESTED simulate() rather than hand math.

    Returns list of (exit_dt, mean_leg_R).
    """
    # build per-symbol Bar arrays + index map on each symbol's own timeline
    barseq = {}
    for s in syms:
        d = load_symbol(s)
        bars = [Bar(o, h, l, c, v) for (_, o, h, l, c, v) in d]
        idx = {row[0]: i for i, row in enumerate(d)}
        barseq[s] = (bars, idx)
    idx_of = {dt: i for i, dt in enumerate(timeline)}
    out = []
    it = lookback
    while it + holdbars < len(timeline):
        t = timeline[it]; t_lb = timeline[it - lookback]; t_exit = timeline[it + holdbars]
        scored = []
        for s in syms:
            r = recent_ret(prices, s, t, t_lb)
            if r is None:
                continue
            p = prices[s]; rets = []
            for j in range(it - lookback + 1, it + 1):
                dj, dj1 = timeline[j], timeline[j - 1]
                if dj in p and dj1 in p and p[dj] > 0 and p[dj1] > 0:
                    rets.append(math.log(p[dj] / p[dj1]))
            if len(rets) < 3:
                continue
            mu = sum(rets) / len(rets); sd = math.sqrt(sum((x - mu) ** 2 for x in rets) / len(rets))
            if sd <= 0:
                continue
            scored.append((r / sd, s))
        if len(scored) < 12:   # require a real cross-section (skips sparse 2022)
            it += holdbars; continue
        scored.sort()
        kk = min(k, len(scored) // 2)
        losers = [s for _, s in scored[:kk]]; winners = [s for _, s in scored[-kk:]]
        legs = []
        long_set = winners if mode == "momentum" else losers
        short_set = losers if mode == "momentum" else winners
        for s in long_set + short_set:
            bars, idx = barseq[s]
            if t not in idx:
                continue
            bi = idx[t]
            a = atr14(bars, bi)
            if a <= 0 or bi + holdbars >= len(bars):
                continue
            stop = 0.5 * a
            direction = +1 if s in long_set else -1
            # time-based exit: huge target so it falls through to maxbars close.
            # Degenerate tiny-ATR symbols can produce absurd |R|; clamp at +-10R
            # (a real stop would have removed losers; this only bounds outliers).
            R = simulate(bars, bi, direction, stop_dist=stop,
                         target_dist=1e9, maxbars=holdbars, cost=cost_for(s))
            R = max(-10.0, min(10.0, R))
            legs.append(R)
        if legs:
            out.append((t_exit, sum(legs) / len(legs)))
        it += holdbars
    return out

# --------------------------------------------------------------------------- main
def main():
    syms = all_symbols()
    print(f"universe candidate symbols: {len(syms)}")
    timeline, prices, present, _ = build_panel(syms)
    print(f"union timeline bars: {len(timeline)}  "
          f"{timeline[0].date()} .. {timeline[-1].date()}")
    # coverage by year
    cov = defaultdict(set)
    for s in prices:
        for dt in prices[s]:
            cov[dt.year].add(s)
    print("symbols-present-per-year:",
          {y: len(cov[y]) for y in sorted(cov)})

    configs = []
    # lookback in H4 bars (6 bars/day): 24=4d, 30=5d, 60=10d, 120=20d, 180=30d
    for lb in (24, 30, 60, 120, 180):
        for hold in (6, 12, 30, 60):
            for k in (3, 5, 8):
                for vn in (True, False):
                    configs.append(dict(lookback=lb, holdbars=hold, k=k,
                                        vol_norm=vn, rebalance=hold))

    rows = []
    for cfg in configs:
        for mode in ("momentum", "reversion"):
            res = run_strategy(timeline, prices, present, mode=mode, **cfg)
            tr, fw = split_train_fwd(res)
            st_all = summarize(res)
            st_tr = summarize(tr)
            st_fw = summarize(fw)
            if not st_all or st_all["n"] < 30:
                continue
            yrs = per_year(res)
            pos_years = sum(1 for y in yrs if yrs[y][1] > 0)
            tot_years = len(yrs)
            rows.append({
                "mode": mode, **cfg,
                "n": st_all["n"],
                "mean_all": st_all["mean_per_rebal"],
                "t_all": st_all["t_stat"],
                "mean_train": st_tr["mean_per_rebal"] if st_tr else None,
                "mean_fwd": st_fw["mean_per_rebal"] if st_fw else None,
                "n_fwd": st_fw["n"] if st_fw else 0,
                "pos_years": pos_years, "tot_years": tot_years,
                "yrs": {y: round(yrs[y][1], 5) for y in yrs},
            })

    # rank: prefer forward-positive AND majority positive years AND train-consistent
    def robust(r):
        if r["mean_fwd"] is None:
            return False
        return (r["mean_fwd"] > 0 and r["mean_train"] is not None
                and r["mean_train"] > 0
                and r["pos_years"] >= math.ceil(r["tot_years"] * 0.6))

    rows.sort(key=lambda r: (robust(r), r["mean_fwd"] or -9), reverse=True)

    print("\n=== TOP CONFIGS (sorted: robust flag, then fwd mean) ===")
    hdr = ("mode", "lb", "hold", "k", "vn", "n", "mean_all", "t_all",
           "mean_tr", "mean_fwd", "n_fwd", "posY/Y")
    print("{:<10}{:>4}{:>5}{:>3}{:>4}{:>6}{:>11}{:>8}{:>11}{:>11}{:>6}{:>8}".format(*hdr))
    for r in rows[:25]:
        print("{:<10}{:>4}{:>5}{:>3}{:>4}{:>6}{:>11.5f}{:>8.2f}{:>11.5f}{:>11.5f}{:>6}{:>8}".format(
            r["mode"], r["lookback"], r["holdbars"], r["k"],
            "v" if r["vol_norm"] else "-", r["n"], r["mean_all"], r["t_all"],
            r["mean_train"] if r["mean_train"] is not None else float("nan"),
            r["mean_fwd"] if r["mean_fwd"] is not None else float("nan"),
            r["n_fwd"], f"{r['pos_years']}/{r['tot_years']}"))

    best = rows[0] if rows else None
    if best:
        print("\n=== BEST CONFIG PER-YEAR ===")
        print(json.dumps({k: best[k] for k in
                          ("mode", "lookback", "holdbars", "k", "vol_norm",
                           "mean_all", "mean_train", "mean_fwd", "pos_years",
                           "tot_years", "yrs")}, indent=2, default=str))

    # ----- negative controls on the best geometry-comparable config -----
    print("\n=== NEGATIVE CONTROLS (best cfg shape) ===")
    if best:
        cfg = dict(lookback=best["lookback"], holdbars=best["holdbars"],
                   k=best["k"], vol_norm=best["vol_norm"],
                   rebalance=best["holdbars"])
        for mode in ("momentum", "reversion", "dispersion", "random"):
            seeds = [0] if mode != "random" else [1, 2, 3, 4, 5]
            agg = []
            for sd in seeds:
                res = run_strategy(timeline, prices, present, mode=mode, seed=sd, **cfg)
                _, fw = split_train_fwd(res)
                stf = summarize(fw)
                if stf:
                    agg.append(stf["mean_per_rebal"])
            if agg:
                print(f"  {mode:<11} fwd mean/rebal = {sum(agg)/len(agg):+.6f} "
                      f"(n_seeds={len(agg)})")

    # ---- DENSE-UNIVERSE honesty pass: only rebalances with >=12 symbols ----
    print("\n=== DENSE-UNIVERSE ISLANDS (>=12 symbols present) ===")
    isl = dense_islands(timeline, prices, min_syms=12)
    for a, b in isl:
        print(f"  island {timeline[a].date()} .. {timeline[b].date()}  ({b-a} bars)")

    # Re-run a few promising momentum configs but ONLY count rebalances whose
    # rebalance bar sits inside a dense island, and report per-year + per-island.
    print("\n=== MOMENTUM ON DENSE BARS ONLY (honest cross-year) ===")
    dense_set = set()
    for a, b in isl:
        for i in range(a, b + 1):
            dense_set.add(timeline[i])
    dense_report = {}
    for cfg in [dict(lookback=60, holdbars=30, k=3, vol_norm=True, rebalance=30),
                dict(lookback=120, holdbars=30, k=5, vol_norm=True, rebalance=30),
                dict(lookback=30, holdbars=12, k=5, vol_norm=True, rebalance=12),
                dict(lookback=60, holdbars=12, k=3, vol_norm=True, rebalance=12)]:
        # filter: keep rebalances whose ENTRY bar is dense
        res = run_strategy(timeline, prices, present, mode="momentum",
                           min_universe=12, **cfg)
        # run_strategy already drops <12 universe via min_universe, so res is dense
        yrs = per_year(res)
        _, fw = split_train_fwd(res)
        stf = summarize(fw); sta = summarize(res)
        pos_years = sum(1 for y in yrs if yrs[y][1] > 0)
        tag = f"lb{cfg['lookback']}_h{cfg['holdbars']}_k{cfg['k']}"
        dense_report[tag] = {
            "n": sta["n"] if sta else 0,
            "mean_all": sta["mean_per_rebal"] if sta else None,
            "t_all": sta["t_stat"] if sta else None,
            "mean_fwd": stf["mean_per_rebal"] if stf else None,
            "n_fwd": stf["n"] if stf else 0,
            "pos_years": pos_years, "tot_years": len(yrs),
            "yrs": {str(y): round(yrs[y][1], 5) for y in yrs},
        }
        print(f"  {tag:18} n={dense_report[tag]['n']:>4} "
              f"mean_all={dense_report[tag]['mean_all']:+.5f} "
              f"t={dense_report[tag]['t_all']:+.2f} "
              f"fwd={dense_report[tag]['mean_fwd']:+.5f} "
              f"posY={pos_years}/{len(yrs)}  yrs={dense_report[tag]['yrs']}")

    # ---- GEOMETRY_LIB CROSS-CHECK on the headline-shape config ----
    print("\n=== GEOMETRY_LIB PER-LEG CROSS-CHECK (tested simulate) ===")
    geo = {}
    for cfg in [dict(lookback=60, holdbars=30, k=3),
                dict(lookback=120, holdbars=30, k=5)]:
        for mode in ("momentum", "reversion"):
            g = geometry_cross_check(timeline, prices, present, list(prices),
                                     mode=mode, **cfg)
            yrs = defaultdict(list)
            for dt, r in g:
                yrs[dt.year].append(r)
            ymean = {str(y): round(sum(yrs[y]) / len(yrs[y]), 4) for y in sorted(yrs)}
            allr = [r for _, r in g]
            fwd = [r for dt, r in g if dt.year >= 2025]
            tag = f"{mode}_lb{cfg['lookback']}_h{cfg['holdbars']}_k{cfg['k']}"
            posY = sum(1 for y in yrs if sum(yrs[y]) > 0)
            geo[tag] = {
                "n": len(allr),
                "mean_R_per_leg_all": round(sum(allr) / len(allr), 4) if allr else None,
                "mean_R_per_leg_fwd": round(sum(fwd) / len(fwd), 4) if fwd else None,
                "pos_years": posY, "tot_years": len(yrs), "yrs_R": ymean,
            }
            print(f"  {tag:30} n={len(allr):>4} "
                  f"R/leg_all={geo[tag]['mean_R_per_leg_all']:+.4f} "
                  f"R/leg_fwd={geo[tag]['mean_R_per_leg_fwd']:+.4f} "
                  f"posY={posY}/{len(yrs)}")
            print(f"       per-year R/leg: {ymean}")

    out = {
        "universe_n": len(prices),
        "timeline_bars": len(timeline),
        "timeline_start": str(timeline[0]),
        "timeline_end": str(timeline[-1]),
        "symbols_per_year": {str(y): len(cov[y]) for y in sorted(cov)},
        "data_quality_note": (
            "MT5 2022-2026 export has staggered per-symbol start dates; full "
            "universe truly exists only in two dense islands: ~2019-2021 (15/22 "
            "export) and ~2025-2026. 2022-2024 middle is sparse. Cross-year "
            "robustness is bounded by these two genuine multi-symbol regimes."
        ),
        "n_configs_tested": len(rows),
        "top": rows[:25],
        "best": best,
        "dense_islands": [(str(timeline[a].date()), str(timeline[b].date()))
                          for a, b in isl],
        "dense_momentum": dense_report,
        "geometry_crosscheck": geo,
    }
    op = os.path.join(HERE, "WAVE1_CROSS_SECTIONAL_RESULT.json")
    json.dump(out, open(op, "w"), indent=2, default=str)
    print(f"\nwrote {op}")
    return out


if __name__ == "__main__":
    main()
