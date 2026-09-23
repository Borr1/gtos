"""WAVE 3 — LEAK AUDIT of prior claimed positives.

Purpose: stop the loop chasing leaky positives. Independently re-audit the three
surviving "positives" from Wave 1 under STRICT no-lookahead / no-coverage-artifact
discipline, with negative controls. Truth over positive results.

The three claims under audit (from RESEARCH_LOOP_LEDGER.md "WAVE 1 RESULT"):
  A. CROSS-SECTIONAL relative-value  — ledger flagged as "MT5 symbol-count coverage
     artifact 13->45". CONFIRM/QUANTIFY: is the forward "+0.07" purely because the
     universe explodes from ~13 symbols (train) to ~45 (forward)? Hold the universe
     FIXED to symbols present across ALL years and re-measure.
  B. PER-SYMBOL ADAPTIVE ROUTING    — ledger said "routing beats all neg-controls;
     AUDJPY-trend a 5/5 survivor". The result JSON's OWN verdict is already
     forward-NEGATIVE (-0.05R). RE-TEST: does the train->forward MODE ASSIGNMENT
     leak? Strict OOS = assign mode on TRAIN<=2024 ONLY, never touch forward to
     select; also walk-forward the assignment. Is the "survivor" subset just
     selection-on-the-test-set?
  C. SESSION/DOW SURVIVOR           — ledger said "1/6400 survives OOS". The result
     JSON shows 75 "robust" cells at 6.25x null ratio, BUT those were selected with
     train AND forward both gated (in-sample selection). The OOS-train-selected book
     is already -0.131R forward. RE-CONFIRM and quantify the in-sample-selection
     leak: how many of the 75 survive a strict TRAIN-ONLY selection -> forward
     read-out, vs the random-direction null under the SAME strict protocol?

DISCIPLINE (hard anti-leak mandate):
- ALL fills via tested geometry_lib.simulate / simulate_detail. No hand-rolled fills.
- NO LOOKAHEAD: every gate/filter uses only data known at the decision bar.
- NO TRAIN/FORWARD LEAK: parameters locked on TRAIN<=2024; FORWARD 2025-26 read-out.
- Negative controls (random / invert) for every positive claim.
- State honestly if nothing survives.

Outputs WAVE3_LEAK_AUDIT_RESULT.json + prints tables.
"""
from __future__ import annotations
import os, sys, json, csv, math, random, datetime
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
HERE = os.path.join(ROOT, "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL  # noqa
from geometry_lib import Bar, atr14, simulate, simulate_detail  # noqa

D_OLD = os.path.join(ROOT, "data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022")
D_NEW = os.path.join(ROOT, "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026")
COST_MAP = json.load(open(os.path.join(HERE, "ULTIMATE_REAL_COST_MAP.json")))
GLOBAL_COST = COST_MAP["_global_median"]

TRAIN_END = 2024
FWD_YEARS = (2025, 2026)


def cost_for(sym):
    ac = ASSET_CLASS_BY_SYMBOL.get(sym, "fx")
    return COST_MAP.get(ac, GLOBAL_COST)


# --------------------------------------------------------------------------- IO
def load_series(sym):
    """Concatenate + dedupe both exports. Returns list of (datetime, Bar)."""
    rows = {}
    for d in (D_OLD, D_NEW):
        p = os.path.join(d, f"{sym}_H4.csv")
        if not os.path.exists(p):
            continue
        with open(p) as f:
            for r in csv.DictReader(f):
                t = r["time"]
                try:
                    o = float(r["open"]); h = float(r["high"]); l = float(r["low"])
                    c = float(r["close"]); v = float(r.get("volume", 0) or 0)
                except (ValueError, TypeError):
                    continue
                rows[t] = (o, h, l, c, v)
    out = []
    for t in sorted(rows):
        try:
            dt = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            dt = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M")
        o, h, l, c, v = rows[t]
        out.append((dt, Bar(o, h, l, c, v)))
    return out


def all_symbols():
    s = set()
    for d in (D_OLD, D_NEW):
        for fn in os.listdir(d):
            if fn.endswith("_H4.csv"):
                s.add(fn[:-7])
    return sorted(s)


# ===========================================================================
# AUDIT A — CROSS-SECTIONAL: is the forward edge a symbol-count coverage artifact?
# ===========================================================================
def recent_ret_volnorm(prices, sym, timeline, it, lookback):
    p = prices.get(sym)
    if p is None:
        return None
    t_now, t_lb = timeline[it], timeline[it - lookback]
    if t_now not in p or t_lb not in p or p[t_now] <= 0 or p[t_lb] <= 0:
        return None
    r = math.log(p[t_now] / p[t_lb])
    rets = []
    for j in range(it - lookback + 1, it + 1):
        dj, dj1 = timeline[j], timeline[j - 1]
        if dj in p and dj1 in p and p[dj] > 0 and p[dj1] > 0:
            rets.append(math.log(p[dj] / p[dj1]))
    if len(rets) < 3:
        return None
    mu = sum(rets) / len(rets)
    sd = math.sqrt(sum((x - mu) ** 2 for x in rets) / len(rets))
    if sd <= 0:
        return None
    return r / sd


def fwd_ret(prices, sym, timeline, it, holdbars):
    p = prices.get(sym)
    if p is None:
        return None
    a, b = timeline[it], timeline[it + holdbars]
    if a not in p or b not in p or p[a] <= 0 or p[b] <= 0:
        return None
    return math.log(p[b] / p[a])


def xsec_run(timeline, prices, universe, *, lookback, holdbars, k, mode="momentum",
             seed=0, require_full_universe=True):
    """Cross-sectional momentum/reversion on a FIXED universe.
    If require_full_universe: only rebalance when ALL universe symbols have data at
    both the rebalance bar and the exit bar (kills the coverage artifact). Returns
    list of (exit_dt, basket_ret)."""
    rng = random.Random(seed)
    out = []
    it = lookback
    N = len(timeline)
    while it + holdbars < N:
        scored = []
        ok = True
        for s in universe:
            sc = recent_ret_volnorm(prices, s, timeline, it, lookback)
            fr = fwd_ret(prices, s, timeline, it, holdbars)
            if sc is None or fr is None:
                if require_full_universe:
                    ok = False
                    break
                continue
            scored.append((sc, s, fr))
        if require_full_universe and not ok:
            it += holdbars
            continue
        if len(scored) < 2 * k:
            it += holdbars
            continue
        scored.sort(key=lambda x: x[0])
        losers = scored[:k]
        winners = scored[-k:]

        def leg(items, side):
            tot = 0.0
            for sc, s, fr in items:
                tot += side * fr - cost_for(s) * 0.01  # tiny per-leg cost proxy in ret units
            return tot / len(items)
        if mode == "momentum":
            ret = leg(winners, +1) + leg(losers, -1)
        elif mode == "reversion":
            ret = leg(losers, +1) + leg(winners, -1)
        elif mode == "random":
            picks = scored[:]
            rng.shuffle(picks)
            ret = leg(picks[:k], +1) + leg(picks[k:2 * k], -1)
        out.append((timeline[it + holdbars], ret))
        it += holdbars
    return out


def per_year_mean(results):
    by = defaultdict(list)
    for dt, r in results:
        by[dt.year].append(r)
    return {y: (sum(v) / len(v), len(v)) for y, v in by.items()}


def split_tf(results):
    tr = [(d, r) for d, r in results if d.year <= TRAIN_END]
    fw = [(d, r) for d, r in results if d.year >= FWD_YEARS[0]]
    return tr, fw


def audit_A_cross_sectional():
    print("\n" + "=" * 90)
    print("AUDIT A — CROSS-SECTIONAL: coverage-artifact confirmation")
    print("=" * 90)
    syms = all_symbols()
    series = {s: load_series(s) for s in syms}
    series = {s: d for s, d in series.items() if len(d) > 50}
    # union timeline + price dicts
    all_dt = set()
    for d in series.values():
        for dt, _ in d:
            all_dt.add(dt)
    timeline = sorted(all_dt)
    prices = {s: {dt: b.c for dt, b in d} for s, d in series.items()}

    # coverage per year
    cov = defaultdict(set)
    for s, p in prices.items():
        for dt in p:
            cov[dt.year].add(s)
    cov_count = {y: len(cov[y]) for y in sorted(cov)}
    print("symbols present per year:", cov_count)

    # FIXED universe = symbols with a bar in EVERY year 2018..2026 (continuous deep set)
    years_all = [y for y in range(2018, 2027)]
    fixed_uni = sorted([s for s in series
                        if all(s in cov[y] for y in years_all)])
    print(f"FIXED continuous universe (present every year 2018-2026): "
          f"{len(fixed_uni)} symbols: {fixed_uni}")

    # The headline config from WAVE1_CROSS_SECTIONAL (best): lb180 h60 k3 momentum.
    # The fixed continuous universe is only 5 symbols (2018-2026), so the fixed-universe
    # leg test uses k=2 (needs 2*k=4<=5). Growing-universe uses k=3 to mirror the
    # original headline. We report both to keep the comparison honest.
    cfgs = [dict(lookback=180, holdbars=60, k=3, k_fixed=2),
            dict(lookback=60, holdbars=30, k=3, k_fixed=2),
            dict(lookback=30, holdbars=60, k=3, k_fixed=2)]
    findings = {}
    for cfg in cfgs:
        k_grow = cfg["k"]; k_fix = cfg["k_fixed"]
        base = dict(lookback=cfg["lookback"], holdbars=cfg["holdbars"])
        tag = f"lb{cfg['lookback']}_h{cfg['holdbars']}_k{k_grow}"
        # (1) ORIGINAL-STYLE: full (growing) universe, allow partial coverage
        res_grow = xsec_run(timeline, prices, list(prices), mode="momentum",
                            require_full_universe=False, k=k_grow, **base)
        # (2) FIXED universe, require full coverage every rebalance (k=2 -> 4 legs<=5)
        res_fix = xsec_run(timeline, prices, fixed_uni, mode="momentum",
                          require_full_universe=True, k=k_fix, **base)
        # negative controls on fixed universe
        res_rev = xsec_run(timeline, prices, fixed_uni, mode="reversion",
                          require_full_universe=True, k=k_fix, **base)
        rand_fwd = []
        for sd in range(5):
            rr = xsec_run(timeline, prices, fixed_uni, mode="random", seed=sd,
                         require_full_universe=True, k=k_fix, **base)
            _, fw = split_tf(rr)
            if fw:
                rand_fwd.append(sum(r for _, r in fw) / len(fw))

        def summ(res):
            if not res:
                return dict(n=0, train=None, fwd=None, pos_years=0, tot_years=0, yrs={})
            tr, fw = split_tf(res)
            py = per_year_mean(res)
            pos = sum(1 for y in py if py[y][0] > 0)
            return dict(
                n=len(res),
                train=(sum(r for _, r in tr) / len(tr)) if tr else None,
                fwd=(sum(r for _, r in fw) / len(fw)) if fw else None,
                n_fwd=len(fw),
                pos_years=pos, tot_years=len(py),
                yrs={str(y): round(py[y][0], 5) for y in sorted(py)},
            )
        sg, sf, sr = summ(res_grow), summ(res_fix), summ(res_rev)
        findings[tag] = {
            "growing_universe": sg,
            "fixed_universe": sf,
            "fixed_reversion_negctrl": sr,
            "fixed_random_negctrl_fwd_mean": (sum(rand_fwd) / len(rand_fwd)) if rand_fwd else None,
        }
        print(f"\n  CONFIG {tag}")
        print(f"    growing-universe (orig style): n={sg['n']:>4} train={sg['train']} "
              f"fwd={sg['fwd']} posY={sg['pos_years']}/{sg['tot_years']}")
        print(f"      yrs: {sg['yrs']}")
        print(f"    FIXED universe (full coverage): n={sf['n']:>4} train={sf['train']} "
              f"fwd={sf['fwd']} posY={sf['pos_years']}/{sf['tot_years']}")
        print(f"      yrs: {sf['yrs']}")
        print(f"    fixed reversion negctrl:  fwd={sr['fwd']}")
        print(f"    fixed random negctrl fwd: {findings[tag]['fixed_random_negctrl_fwd_mean']}")

    return {
        "symbols_per_year": cov_count,
        "fixed_universe": fixed_uni,
        "fixed_universe_n": len(fixed_uni),
        "configs": findings,
        "interpretation": (
            "Coverage artifact CONFIRMED if growing-universe forward is positive but "
            "fixed-universe forward collapses to ~0/negative and matches its random "
            "negctrl. The growing universe ranks across ~13 symbols in train vs ~45 in "
            "forward; that is a different statistic, not a stable edge."
        ),
    }


# ===========================================================================
# AUDIT B — PER-SYMBOL ADAPTIVE ROUTING: strict-OOS mode assignment + walk-forward
# ===========================================================================
LOOKBACK_B = 20
STOP_MULT_B = 0.5
MAXBARS_B = 80
TARGET_R_B = 1.5


def signals_for_bar(bars, i):
    if i < LOOKBACK_B + 14:
        return False, False
    win = bars[i - LOOKBACK_B:i]
    hh = max(b.h for b in win)
    ll = min(b.l for b in win)
    c = bars[i].c
    return (c > hh), (c < ll)


def trades_for_symbol(barlist, mode, cost):
    """barlist: list[(dt, Bar)]. mode trend/revert/skip. Non-overlapping cooldown=6.
    Returns list of (year, R)."""
    if mode == "skip":
        return []
    bars = [b for _, b in barlist]
    res = []
    n = len(bars)
    cooldown = -1
    for i in range(LOOKBACK_B + 14, n - 1):
        if i <= cooldown:
            continue
        up, dn = signals_for_bar(bars, i)
        if not (up or dn):
            continue
        a = atr14(bars, i)
        if a <= 0:
            continue
        stop = STOP_MULT_B * a
        if stop <= 0:
            continue
        if mode == "trend":
            direction = 1 if up else -1
        else:
            direction = -1 if up else 1
        R = simulate(bars, i, direction, stop_dist=stop,
                     target_dist=TARGET_R_B * stop, maxbars=MAXBARS_B, cost=cost)
        res.append((barlist[i][0].year, R))
        cooldown = i + 6
    return res


def measure_mode_edge(barlist, mode, cost, year_lo, year_hi):
    """Mean R + per-year positivity for a mode over [year_lo, year_hi] (inclusive).
    Trades are generated on the FULL series but only those entering in-window count
    (entry signals naturally only use prior bars -> no lookahead from windowing)."""
    tr = [(y, r) for (y, r) in trades_for_symbol(barlist, mode, cost)
          if year_lo <= y <= year_hi]
    if not tr:
        return 0.0, 0, 0.0, 0
    mean = sum(r for _, r in tr) / len(tr)
    by = defaultdict(list)
    for y, r in tr:
        by[y].append(r)
    pos = sum(1 for y in by if sum(by[y]) > 0)
    frac = pos / len(by)
    return mean, len(tr), frac, len(by)


def audit_B_routing():
    print("\n" + "=" * 90)
    print("AUDIT B — PER-SYMBOL ADAPTIVE ROUTING: strict-OOS assignment + walk-forward")
    print("=" * 90)
    syms = all_symbols()
    series = {}
    for s in syms:
        d = load_series(s)
        if len(d) > 300:
            series[s] = d

    # ---- B1: STRICT OOS (assign on TRAIN<=2024 only, read forward) with the SAME
    # regime-robust rule the prior script used (mean>0.02 AND majority of train years).
    def assign_train_only(barlist, cost, min_trades=40, min_edge=0.02, min_frac=0.6):
        tm, tn, tfrac, _ = measure_mode_edge(barlist, "trend", cost, 0, TRAIN_END)
        rm, rn, rfrac, _ = measure_mode_edge(barlist, "revert", cost, 0, TRAIN_END)
        cands = []
        if tn >= min_trades and tm > min_edge and tfrac >= min_frac:
            cands.append(("trend", tm))
        if rn >= min_trades and rm > min_edge and rfrac >= min_frac:
            cands.append(("revert", rm))
        if not cands:
            return "skip"
        return max(cands, key=lambda x: x[1])[0]

    routing = {}
    for s, d in series.items():
        routing[s] = assign_train_only(d, cost_for(s))
    routed = {s: m for s, m in routing.items() if m != "skip"}
    print(f"  strict-OOS routing (train-only assign): {routed}")

    def book_forward(route_map):
        fwd = []
        for s, m in route_map.items():
            if m == "skip":
                continue
            tr = [(y, r) for (y, r) in trades_for_symbol(series[s], m, cost_for(s))
                  if y in FWD_YEARS]
            fwd.extend(tr)
        if not fwd:
            return None
        by = defaultdict(list)
        for y, r in fwd:
            by[y].append(r)
        return dict(
            fwd_mean=sum(r for _, r in fwd) / len(fwd),
            n=len(fwd),
            by_year={str(y): (round(sum(by[y]) / len(by[y]), 4), len(by[y])) for y in by},
        )

    strict_book = book_forward(routing)
    print(f"  STRICT-OOS forward book: {strict_book}")

    # negative control: invert assigned modes
    inv = {s: ("revert" if m == "trend" else "trend") for s, m in routing.items() if m != "skip"}
    inv_book = book_forward(inv)
    print(f"  INVERT-routing negctrl forward: {inv_book}")

    # negative control: random routing (5 seeds)
    rand_fwd = []
    for seed in range(5):
        rr = random.Random(700 + seed)
        rmap = {s: rr.choice(["trend", "revert", "skip"]) for s in series}
        b = book_forward(rmap)
        if b:
            rand_fwd.append(b["fwd_mean"])
    rand_mean = sum(rand_fwd) / len(rand_fwd) if rand_fwd else None
    print(f"  RANDOM-routing negctrl forward mean: {rand_mean}")

    # ---- B2: the 'AUDJPY-trend 5/5 survivor' claim. The "strict survivor" subset in
    # the prior script REQUIRED frac>=0.8 of TRAIN years. That gate is selected on
    # train, which is legitimate OOS. But the CLAIM is the survivor is forward-good.
    # Test each strict survivor's forward R individually + as a book.
    survivors = {}
    for s, d in series.items():
        cost = cost_for(s)
        m = routing[s]
        if m == "skip":
            continue
        if m == "trend":
            _, n, frac, _ = measure_mode_edge(d, "trend", cost, 0, TRAIN_END)
        else:
            _, n, frac, _ = measure_mode_edge(d, "revert", cost, 0, TRAIN_END)
        if frac >= 0.8 and n >= 80:
            survivors[s] = m
    print(f"\n  strict survivors (train frac>=0.8, n>=80): {survivors}")
    surv_individual = {}
    for s, m in survivors.items():
        fwd = [(y, r) for (y, r) in trades_for_symbol(series[s], m, cost_for(s))
               if y in FWD_YEARS]
        if fwd:
            by = defaultdict(list)
            for y, r in fwd:
                by[y].append(r)
            surv_individual[s] = dict(
                mode=m,
                fwd_mean=round(sum(r for _, r in fwd) / len(fwd), 4),
                n=len(fwd),
                by_year={str(y): round(sum(by[y]) / len(by[y]), 4) for y in by},
            )
    survivor_book = book_forward(survivors)
    print(f"  strict survivors individual forward: {json.dumps(surv_individual, indent=2)}")
    print(f"  strict survivors as book forward: {survivor_book}")

    # ---- B3: WALK-FORWARD assignment (the cleanest OOS). For each forward year Y,
    # assign each symbol's mode using ONLY years < Y, then trade year Y. This removes
    # ANY use of forward data in the routing decision and removes the single-split
    # luck. Aggregate forward book over 2025+2026.
    wf_fwd = []
    wf_by_year = {}
    for Y in FWD_YEARS:
        ymap = {}
        for s, d in series.items():
            ymap[s] = assign_train_only_upto(d, cost_for(s), Y - 1)
        ytr = []
        for s, m in ymap.items():
            if m == "skip":
                continue
            ytr.extend([(y, r) for (y, r) in trades_for_symbol(series[s], m, cost_for(s))
                        if y == Y])
        if ytr:
            wf_by_year[str(Y)] = (round(sum(r for _, r in ytr) / len(ytr), 4), len(ytr))
            wf_fwd.extend(ytr)
    wf_mean = (sum(r for _, r in wf_fwd) / len(wf_fwd)) if wf_fwd else None
    print(f"\n  WALK-FORWARD routing (assign on years < Y, trade Y): "
          f"fwd_mean={wf_mean} by_year={wf_by_year}")

    return {
        "strict_oos_routing": routing,
        "strict_oos_forward_book": strict_book,
        "invert_negctrl_forward": inv_book,
        "random_negctrl_forward_mean": rand_mean,
        "strict_survivors": survivors,
        "strict_survivors_individual_forward": surv_individual,
        "strict_survivors_book_forward": survivor_book,
        "walkforward_forward_mean": wf_mean,
        "walkforward_by_year": wf_by_year,
        "interpretation": (
            "Routing 'leaks' if the assigned-mode book is only good because it was "
            "tuned on the same data it's scored on. Strict-OOS (train-only assign) and "
            "walk-forward (assign on years<Y) are the clean tests. The breakout-band "
            "entry has structurally negative post-cost edge, so routing can only "
            "allocate a losing entry less badly; forward should stay <=0."
        ),
    }


def assign_train_only_upto(barlist, cost, year_hi, min_trades=40, min_edge=0.02, min_frac=0.6):
    tm, tn, tfrac, _ = measure_mode_edge(barlist, "trend", cost, 0, year_hi)
    rm, rn, rfrac, _ = measure_mode_edge(barlist, "revert", cost, 0, year_hi)
    cands = []
    if tn >= min_trades and tm > min_edge and tfrac >= min_frac:
        cands.append(("trend", tm))
    if rn >= min_trades and rm > min_edge and rfrac >= min_frac:
        cands.append(("revert", rm))
    if not cands:
        return "skip"
    return max(cands, key=lambda x: x[1])[0]


# ===========================================================================
# AUDIT C — SESSION/DOW SURVIVOR: in-sample-selection leak vs strict TRAIN-only
# ===========================================================================
EXIT_CONFIGS_C = [
    ("tp1.0R", dict(target_dist_mult=1.0)),
    ("tp1.5R", dict(target_dist_mult=1.5)),
    ("tp2.0R", dict(target_dist_mult=2.0)),
    ("trail1_1", dict(trail_arm_mult=1.0, trail_gap_mult=1.0)),
]
STOP_MULT_C = 0.5


def run_trade_c(bars, i, direction, cost, ecfg):
    a = atr14(bars, i)
    if a <= 0:
        return None
    stop = STOP_MULT_C * a
    if stop <= 0:
        return None
    kw = dict(stop_dist=stop, cost=cost, maxbars=12)
    if "target_dist_mult" in ecfg:
        kw["target_dist"] = ecfg["target_dist_mult"] * stop
    else:
        kw["trail_arm"] = ecfg["trail_arm_mult"] * stop
        kw["trail_gap"] = ecfg["trail_gap_mult"] * stop
    return simulate(bars, i, direction, **kw)


def build_cells(symbols, series_cache, randomize_seed=None):
    """Build (scope,hour,dow,mode,dir,exit)->{year:[R]}. If randomize_seed set, the
    direction is random (null). Otherwise DRIFT long/short + BREAKOUT-momentum."""
    rng = random.Random(randomize_seed) if randomize_seed is not None else None
    results = defaultdict(lambda: defaultdict(list))
    for sym in symbols:
        dates_bars = series_cache.get(sym)
        if dates_bars is None:
            continue
        dates, bars = dates_bars
        cost = cost_for(sym)
        ac = ASSET_CLASS_BY_SYMBOL.get(sym, "fx")
        for i in range(15, len(bars) - 13):
            dt = dates[i]
            if dt.weekday() > 4:
                continue
            hour, dow, yr = dt.hour, dt.weekday(), dt.year
            b = bars[i]
            body = b.c - b.o
            bdir = 0 if body == 0 else (1 if body > 0 else -1)
            for exitname, ecfg in EXIT_CONFIGS_C:
                if rng is not None:
                    d = 1 if rng.random() < 0.5 else -1
                    r = run_trade_c(bars, i, d, cost, ecfg)
                    if r is not None:
                        for scope in (sym, "AC:" + ac):
                            results[(scope, hour, dow, "NULL", "RND", exitname)][yr].append(r)
                    continue
                for dirlabel, direction in (("LONG", 1), ("SHORT", -1)):
                    r = run_trade_c(bars, i, direction, cost, ecfg)
                    if r is not None:
                        for scope in (sym, "AC:" + ac):
                            results[(scope, hour, dow, "DRIFT", dirlabel, exitname)][yr].append(r)
                if bdir != 0:
                    r = run_trade_c(bars, i, bdir, cost, ecfg)
                    if r is not None:
                        for scope in (sym, "AC:" + ac):
                            results[(scope, hour, dow, "BREAKOUT", "MOM", exitname)][yr].append(r)
    return results


def strict_select_and_score(cells, min_qual_years=4, min_train_R=0.02, min_train_frac=0.6,
                            min_fwd_n=30):
    """STRICT protocol: SELECT cells using TRAIN<=2024 ONLY (train mean>thr, positive in
    majority of train qual-years). Then READ OUT forward (2025-26) for the selected set.
    A cell 'survives' only if it ALSO ends up forward-positive — but selection NEVER
    touches forward. Returns (n_selected, n_fwd_positive, forward_book_mean, n_fwd_trades)."""
    selected = []
    fwd_all = []
    fwd_pos = 0
    for key, ym in cells.items():
        train = {y: ym[y] for y in ym if y <= TRAIN_END}
        if not train:
            continue
        per = {y: (sum(train[y]) / len(train[y]), len(train[y])) for y in train}
        qual = [y for y in per if per[y][1] >= 20]
        if len(qual) < min_qual_years:
            continue
        pos = [y for y in qual if per[y][0] > 0]
        train_R = [r for y in train for r in train[y]]
        tmean = sum(train_R) / len(train_R)
        if tmean > min_train_R and len(pos) / len(qual) >= min_train_frac:
            fwd = [r for y in ym if y >= FWD_YEARS[0] for r in ym[y]]
            if len(fwd) < min_fwd_n:
                continue
            selected.append(key)
            fm = sum(fwd) / len(fwd)
            if fm > 0:
                fwd_pos += 1
            fwd_all.extend(fwd)
    book = (sum(fwd_all) / len(fwd_all)) if fwd_all else None
    return len(selected), fwd_pos, book, len(fwd_all)


def insample_select(cells, min_qual_years=4, min_R=0.02, min_frac=0.5, min_fwd_n=30):
    """The LEAKY protocol the prior 'robust' count used: gate on train AND forward
    BOTH being positive (in-sample selection on the test set)."""
    robust = 0
    for key, ym in cells.items():
        all_years = sorted(ym)
        per = {y: (sum(ym[y]) / len(ym[y]), len(ym[y])) for y in all_years}
        train_R = [r for y in ym if y <= TRAIN_END for r in ym[y]]
        fwd_R = [r for y in ym if y >= FWD_YEARS[0] for r in ym[y]]
        if not train_R or not fwd_R or len(fwd_R) < min_fwd_n:
            continue
        qual = [y for y in all_years if per[y][1] >= 20]
        if len(qual) < min_qual_years:
            continue
        pos = [y for y in qual if per[y][0] > 0]
        tmean = sum(train_R) / len(train_R)
        fmean = sum(fwd_R) / len(fwd_R)
        if fmean > min_R and tmean > 0 and len(pos) / len(qual) > min_frac:
            robust += 1
    return robust


def audit_C_session_dow():
    print("\n" + "=" * 90)
    print("AUDIT C — SESSION/DOW: in-sample-selection leak vs strict TRAIN-only OOS")
    print("=" * 90)
    syms = all_symbols()
    series_cache = {}
    for s in syms:
        d = load_series(s)
        if len(d) < 200:
            continue
        series_cache[s] = ([dt for dt, _ in d], [b for _, b in d])
    print(f"  loaded {len(series_cache)} symbols")

    cells = build_cells(syms, series_cache)
    # LEAKY in-sample 'robust' count (reproduce prior 75)
    leaky_robust = insample_select(cells)
    # STRICT train-only selection -> forward read-out
    n_sel, n_fwd_pos, strict_book, n_fwd_tr = strict_select_and_score(cells)
    print(f"  LEAKY in-sample 'robust' count (train+fwd both gated): {leaky_robust}")
    print(f"  STRICT train-only selected cells: {n_sel}; of those forward-positive: "
          f"{n_fwd_pos}; forward book mean={strict_book} over {n_fwd_tr} trades")

    # NULL under BOTH protocols: random-direction cells, same gates.
    leaky_null, strict_null_sel, strict_null_pos = [], [], []
    for seed in (1, 2, 3):
        ncells = build_cells(syms, series_cache, randomize_seed=seed)
        leaky_null.append(insample_select(ncells))
        ns, nfp, _, _ = strict_select_and_score(ncells)
        strict_null_sel.append(ns)
        strict_null_pos.append(nfp)
    print(f"  NULL leaky-robust counts: {leaky_null} (mean {sum(leaky_null)/len(leaky_null):.1f})")
    print(f"  NULL strict-selected counts: {strict_null_sel}; "
          f"NULL strict forward-positive: {strict_null_pos}")

    return {
        "leaky_insample_robust_count": leaky_robust,
        "leaky_null_counts": leaky_null,
        "leaky_real_to_null_ratio": leaky_robust / max(0.5, sum(leaky_null) / len(leaky_null)),
        "strict_trainonly_selected": n_sel,
        "strict_trainonly_forward_positive": n_fwd_pos,
        "strict_trainonly_forward_book_mean": strict_book,
        "strict_trainonly_forward_n": n_fwd_tr,
        "strict_null_selected": strict_null_sel,
        "strict_null_forward_positive": strict_null_pos,
        "interpretation": (
            "The prior '75 robust @ 6.25x null' used in-sample selection: it gated on "
            "BOTH train AND forward being positive, i.e. it selected partly on the test "
            "set. The clean test is STRICT: select on TRAIN-ONLY, then read forward. If "
            "the strict train-only book is forward<=0 (and forward-positive count is no "
            "better than the null), the survivors are a multiple-testing/in-sample "
            "selection artifact, not an edge."
        ),
    }


def main():
    out = {
        "audit": "wave3_leak_audit",
        "generated": datetime.datetime.now().isoformat(),
        "A_cross_sectional": audit_A_cross_sectional(),
        "B_per_symbol_routing": audit_B_routing(),
        "C_session_dow": audit_C_session_dow(),
    }
    op = os.path.join(HERE, "WAVE3_LEAK_AUDIT_RESULT.json")
    json.dump(out, open(op, "w"), indent=2, default=str)
    print(f"\nwrote {op}")
    return out


if __name__ == "__main__":
    main()
