"""B5 step (c) — the cross-sectional pilot at full scale, per asset class, costed per symbol.

Reproduces Lane 5's construction exactly (lane5_receipts/xs4.py, xs5.py) so the numbers
compose, and adds the three things the pilot did not have:

  1. PER-SYMBOL COST, charged inside the backtest.  Lane 5 reported a single break-even
     bps/leg and compared it to EURUSD.  The expanded universe's round-trip cost spans
     0.19 bps (USDJPY) to 514 bps (an illiquid alt), so a single number cannot decide it.
     Cost enters in the same units as the return: c_vol = (rt_bps/1e4) / sigma_t, and the
     FULL round trip is charged to each name at the rebalance where it ENTERS a leg (which
     correctly books the eventual exit).
  2. COST-CLEARING UNIVERSES, so the question "is there a tradeable subset" is asked directly.
  3. ERA DECAY, reported on the same cells rather than only on the headline.

Signals (own-observation sequence, strictly past):
    sig_t = logclose_{t-skip} - logclose_{t-skip-lb},  vol-normalised by sqrt(lb)*sigma_t
    fwd_t = logclose_{t+hold} - logclose_t,            vol-normalised by sigma_t
Portfolio = long top quintile, short bottom quintile, equal weight, non-overlapping
(t advances by `hold` after each rebalance).  Sign convention: a NEGATIVE mean is reversal.

Null: within-date permutation, random DISJOINT legs (Lane 5's, which is the correct one --
it holds the date set and the leg sizes fixed and tests only whether the RANKING carries
information).  The t-statistic additionally prices time-variation of the effect and is the
conservative bar; both are reported, per Lane 5's standing warning 2.

Usage:  python3 b5_06_xs.py <universe> [<universe> ...]
Writes one JSON per universe to <OUT>/xs_cells/<universe>.json  (resumable: skips existing).
"""
import json, math, os, sys, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "b5_receipts")
CELLS = os.path.join(OUT, "xs_cells")
SCRATCH = "/Users/borr/.claude/jobs/adb9e69b/tmp/b5"
os.makedirs(CELLS, exist_ok=True)
VOL_N = 60
NPERM = 1000
SEED = 20260812

LIVE24 = {"AUDJPY", "AUDUSD", "BTCUSD", "CHFJPY", "ETHUSD", "EURGBP", "EURJPY", "EURUSD",
          "GBPJPY", "GBPUSD", "GER40_cash", "JP225_cash", "US100_cash", "NZDUSD", "US500_cash",
          "UK100_cash", "UKOIL_cash", "US30_cash", "USDCAD", "USDCHF", "USDJPY", "USOIL_cash",
          "XAGUSD", "XAUUSD"}

# The declared cell grid.  Stated here, in code, BEFORE any result is read -- this is the
# look count the multiplicity section prices.
SIGNALS = [("XS_REV_1D", 1, 0, 1, 120), ("XS_REV_5D", 5, 0, 5, 120),
           ("XS_MOM_1M", 21, 0, 21, 120), ("XS_MOM_12_1", 252, 21, 21, 300)]
ERAS = [("pre2020", None, "2020-01-01"), ("2020_2023", "2020-01-01", "2024-01-01"),
        ("2024plus", "2024-01-01", None)]


def load():
    import pickle
    d = pickle.load(open(os.path.join(SCRATCH, "panel_d1.pkl"), "rb"))
    panel, dates, cls = d["panel"], d["dates"], d["cls"]
    syms = sorted({s for dt in dates for s in panel[dt]})
    S = {s: i for i, s in enumerate(syms)}
    T, N = len(dates), len(syms)
    LC = np.full((T, N), np.nan)
    for ti, dt in enumerate(dates):
        for s, v in panel[dt].items():
            LC[ti, S[s]] = math.log(v[3])
    OWN = {s: np.where(~np.isnan(LC[:, S[s]]))[0] for s in syms}
    VOL = np.full((T, N), np.nan)
    HC = np.zeros((T, N), np.int32)
    for s in syms:
        j = S[s]; ts = OWN[s]; lc = LC[ts, j]
        HC[ts, j] = np.arange(1, len(ts) + 1)
        r = np.diff(lc); n = VOL_N
        if len(r) >= n:
            cs = np.cumsum(np.insert(r, 0, 0.0)); cs2 = np.cumsum(np.insert(r * r, 0, 0.0))
            m = (cs[n:] - cs[:-n]) / n; m2 = (cs2[n:] - cs2[:-n]) / n
            VOL[ts[n:], j] = np.sqrt(np.maximum(m2 - m * m, 0.0) * n / (n - 1))
    return dates, syms, S, LC, OWN, VOL, HC, cls


def own_cum(LC, OWN, S, T, N, syms, lb, skip):
    out = np.full((T, N), np.nan); k = lb + skip
    for s in syms:
        j = S[s]; ts = OWN[s]; lc = LC[ts, j]; L = len(lc)
        if L <= k:
            continue
        out[ts[k:], j] = lc[k - skip:L - skip] - lc[k - skip - lb:L - skip - lb]
    return out


def own_fwd(LC, OWN, S, T, N, syms, hold):
    out = np.full((T, N), np.nan)
    for s in syms:
        j = S[s]; ts = OWN[s]; lc = LC[ts, j]; L = len(lc)
        if L <= hold:
            continue
        out[ts[:L - hold], j] = lc[hold:] - lc[:L - hold]
    return out


def backtest(ctx, cols, lb, skip, hold, minhist, start=None, end=None, cost_bps=None,
             nperm=NPERM, min_names=20):
    dates, syms, S, LC, OWN, VOL, HC, _ = ctx["base"]
    T, N = len(dates), len(syms)
    SIG = ctx["sig"][(lb, skip)]
    FW = ctx["fwd"][hold]
    mask = np.zeros(N, bool); mask[cols] = True
    rets_g, rets_n, ns, dts, keep = [], [], [], [], []
    prevL, prevS = set(), set()
    turn = []
    t = 1
    while t < T:
        if (start and dates[t] < start) or (end and dates[t] >= end):
            t += 1; continue
        ok = (~np.isnan(SIG[t])) & (~np.isnan(FW[t])) & (~np.isnan(VOL[t])) & (VOL[t] > 0) & (HC[t] >= minhist) & mask
        idx = np.where(ok)[0]
        if len(idx) >= min_names:
            sig = SIG[t, idx] / (VOL[t, idx] * math.sqrt(lb))
            f = FW[t, idx] / VOL[t, idx]
            o = np.argsort(sig); q = max(3, len(idx) // 5)
            Lidx, Sidx = idx[o[-q:]], idx[o[:q]]
            gross = float(f[o[-q:]].mean() - f[o[:q]].mean())
            cost = 0.0
            if cost_bps is not None:
                newL = [j for j in Lidx if j not in prevL]
                newS = [j for j in Sidx if j not in prevS]
                for j in list(newL) + list(newS):
                    cb = cost_bps.get(j)
                    if cb is None or not np.isfinite(VOL[t, j]) or VOL[t, j] <= 0:
                        cost = float("nan"); break
                    cost += (cb / 1e4) / VOL[t, j] / q
            rets_g.append(gross); rets_n.append(gross - cost)
            ns.append(len(idx)); dts.append(dates[t])
            keep.append((sig, f))
            if prevL:
                turn.append((len(set(Lidx) - prevL) + len(set(Sidx) - prevS)) / (len(Lidx) + len(Sidx)))
            prevL, prevS = set(Lidx), set(Sidx)
            t += hold
        else:
            t += 1
    if len(rets_g) < 5:
        return None
    a = np.array(rets_g); n_ = np.array(rets_n)
    m, sd = a.mean(), a.std(ddof=1)
    tt = m / (sd / math.sqrt(len(a)))
    finite = np.isfinite(n_)
    costed_frac = float(finite.mean())
    # A net figure computed on the subsample of rebalances where no unknown-cost name was
    # selected is a SELECTED subsample, not a cost estimate.  Only report net when the cost
    # table covers essentially every rebalance.
    if costed_frac >= 0.98 and finite.sum() > 5:
        mn = float(np.nanmean(n_))
        tn = float(np.nanmean(n_) / (np.nanstd(n_, ddof=1) / math.sqrt(finite.sum())))
    else:
        mn = tn = None
    rng = np.random.default_rng(SEED)
    pm = np.empty(nperm)
    for p in range(nperm):
        acc = 0.0
        for (sg, f) in keep:
            k = len(sg); pr = rng.permutation(k); qq = max(3, k // 5)
            acc += f[pr[:qq]].mean() - f[pr[qq:2 * qq]].mean()
        pm[p] = acc / len(keep)
    yr = collections.defaultdict(list)
    for dd, rr in zip(dts, rets_g):
        yr[dd[:4]].append(rr)
    return {
        "n_rebal": len(a), "median_universe": int(np.median(ns)),
        "gross_mean_volnorm": float(m), "gross_t": float(tt),
        "gross_ci95": [float(m - 1.96 * sd / math.sqrt(len(a))), float(m + 1.96 * sd / math.sqrt(len(a)))],
        "perm_p_two_sided": float((np.abs(pm - pm.mean()) >= abs(m)).mean()),
        "net_mean_volnorm": mn, "net_t": tn,
        "n_rebal_costed": int(finite.sum()), "costed_fraction": costed_frac,
        "turnover": float(np.mean(turn)) if turn else None,
        "first": dts[0], "last": dts[-1],
        "pos_years": int(sum(1 for y in yr if np.mean(yr[y]) > 0)), "tot_years": len(yr),
        "by_year": {y: [round(float(np.mean(v)), 5), len(v)] for y, v in sorted(yr.items())},
    }


def universes(S, syms, cls, trade, cost):
    def C(pred):
        return [S[s] for s in syms if pred(s)]
    kn = lambda s: cost[s]["roundtrip_cost_known"]
    rt = lambda s: cost[s]["roundtrip_cost_bps"]
    return {
        "ALL_166": C(lambda s: True),
        "LIVE24": C(lambda s: s in LIVE24),
        "TRADEABLE_NOW_41": C(lambda s: cost[s]["gtos_configured"]),
        "BOTH_BROKERS_61": C(lambda s: trade[s]["ftmo_listed"] and trade[s]["redacted_account_listed"]),
        "FX_ALL_43": C(lambda s: cls.get(s) == "fx"),
        "FX_COST_CLEARING_14": C(lambda s: cls.get(s) == "fx" and kn(s) and rt(s) <= 1.5),
        "FX_G10_KNOWN_COST": C(lambda s: cls.get(s) == "fx" and kn(s)),
        "EQUITY_58": C(lambda s: cls.get(s) == "equity"),
        "CRYPTO_31": C(lambda s: cls.get(s) == "crypto"),
        "INDEX_14": C(lambda s: cls.get(s) == "index"),
        "COMMOD_20": C(lambda s: cls.get(s) == "commodity"),
        "CHEAP_ANY_CLASS_27": C(lambda s: kn(s) and rt(s) <= 2.0),
        "TRADEABLE_NOW_KNOWN_COST": C(lambda s: cost[s]["gtos_configured"] and kn(s)),
        "ALL_KNOWN_COST_84": C(lambda s: kn(s)),
    }


def main():
    want = sys.argv[1:]
    base = load()
    dates, syms, S, LC, OWN, VOL, HC, cls = base
    T, N = len(dates), len(syms)
    trade = json.load(open(os.path.join(OUT, "B5_TRADEABILITY_V1.json")))["symbols"]
    cost = json.load(open(os.path.join(OUT, "B5_SYMBOL_COST_V1.json")))["symbols"]
    cost_bps = {S[s]: cost[s]["roundtrip_cost_bps"] for s in syms if s in cost}
    ctx = {"base": base,
           "sig": {(lb, sk): own_cum(LC, OWN, S, T, N, syms, lb, sk) for _, lb, sk, _, _ in SIGNALS},
           "fwd": {h: own_fwd(LC, OWN, S, T, N, syms, h) for _, _, _, h, _ in SIGNALS}}
    U = universes(S, syms, cls, trade, cost)
    for uname in (want or list(U)):
        path = os.path.join(CELLS, uname + ".json")
        if os.path.exists(path):
            print("skip (exists)", uname); continue
        cols = U[uname]
        out = {"universe": uname, "n_symbols": len(cols),
               "symbols": sorted(syms[j] for j in cols), "cells": {}}
        MIN_NAMES = {"FX_COST_CLEARING_14": 12, "INDEX_14": 12, "CHEAP_ANY_CLASS_27": 20,
                     "COMMOD_20": 14}.get(uname, 20)
        out["min_names_per_rebalance"] = MIN_NAMES
        if len(cols) < MIN_NAMES:
            out["note"] = f"fewer than {MIN_NAMES} symbols"
            json.dump(out, open(path, "w"), indent=1); print(uname, "-> too few symbols"); continue
        for name, lb, sk, hold, mh in SIGNALS:
            r = backtest(ctx, cols, lb, sk, hold, mh, cost_bps=cost_bps, min_names=MIN_NAMES)
            if not r:
                continue
            out["cells"][name] = r
            print(f"{uname:20s} {name:12s} n={r['n_rebal']:5d} u={r['median_universe']:3d} "
                  f"g={r['gross_mean_volnorm']:+.5f} t={r['gross_t']:+.2f} p={r['perm_p_two_sided']:.4f} "
                  f"net={('%+.5f' % r['net_mean_volnorm']) if r['net_mean_volnorm'] is not None else 'NA':>9s} "
                  f"tn={('%+.2f' % r['net_t']) if r['net_t'] is not None else 'NA':>6s} "
                  f"turn={r['turnover']:.2f} yrs={r['pos_years']}/{r['tot_years']}")
            for ename, s0, s1 in ERAS:
                er = backtest(ctx, cols, lb, sk, hold, mh, start=s0, end=s1, cost_bps=cost_bps, nperm=200, min_names=MIN_NAMES)
                if er:
                    out["cells"][name].setdefault("eras", {})[ename] = {
                        k: er[k] for k in ("n_rebal", "gross_mean_volnorm", "gross_t",
                                           "perm_p_two_sided", "net_mean_volnorm", "net_t", "median_universe")}
        json.dump(out, open(path, "w"), indent=1)
        print("  written", path)


if __name__ == "__main__":
    main()
