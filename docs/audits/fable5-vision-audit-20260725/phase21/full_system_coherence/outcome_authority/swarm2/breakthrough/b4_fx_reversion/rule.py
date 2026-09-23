"""S6 - the rule, costed per leg with tape-true spreads, walked forward.

The only construction that survived S3/S5 is the crypto cross-sectional 1-day
reversal on the A2 anchor (signal = yesterday's close-to-close; enter at today's
broker-00:00 open, exit at today's close).  A2 is intraday by construction, so
it pays NO swap -- which matters because FTMO charges crypto swap on both sides
(``swap_mode: 5``, ``swap_long = swap_short = -30.0``), i.e. an overnight
long/short crypto book bleeds on both legs and the open-to-open variant (A3) is
dead on carry before any spread is charged.

Cost accounting, stated because the pilot's convention is wrong for this anchor:
Lane 5's ``breakeven = gross / (2 * turnover)`` is correct for a book that HOLDS
between rebalances and only trades the names that change.  A2 exits every leg at
every close, so every leg pays a full round trip every day and the correct
denominator is 2, not 2 x 0.81.  That alone moves the crypto breakeven from
12.24 to 9.89 bps/leg before any symbol-level spread is charged.

Spreads: measured from the tick archive where it has the symbol (BTCUSD, ETHUSD,
AVAUSD, DASHUSD), otherwise from the estate's own SPREAD_MODEL_V1 anchor, which
covers ADAUSD/DOTUSD/LTCUSD/XRPUSD/XTZUSD.  Symbols with neither are reported
separately and never silently costed at zero.
"""
from __future__ import annotations
import collections, json, math, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = "/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725"
from xs import build_matrices, make_returns   # noqa: E402

OUT = os.path.join(HERE, "receipts")
np.seterr(all="ignore")


# --------------------------------------------------------------------------
def spread_table(panel):
    """bp per symbol, from ticks first, then the estate model.  Returns
    (dict sym->bp, dict sym->provenance)."""
    sp, prov = {}, {}
    tick = pd.read_parquet("/Users/borr/.claude/jobs/adb9e69b/tmp/b4cache/tick_sp_bh_ftmo.parquet")
    w = tick.groupby("sym").apply(
        lambda x: float(np.average(x["med"], weights=x["n"]) * 1e4), include_groups=False)
    for s, v in w.items():
        sp[s] = float(v); prov[s] = "tick_measured"
    # estate model: anchor_spread_price -> bp using the symbol's median close
    med_close = {}
    C = panel["C"]; syms = panel["syms"]
    for i, s in enumerate(syms):
        v = C[:, i]; v = v[np.isfinite(v) & (v > 0)]
        if len(v):
            med_close[s] = float(np.median(v))
    try:
        mdl = json.load(open(f"{REPO}/research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json"))
        for s, d in mdl["accounts"]["FTMO"].items():
            if s in sp or s not in med_close:
                continue
            a = d.get("anchor_spread_price")
            if a is None or not med_close.get(s):
                continue
            sp[s] = float(a) / med_close[s] * 1e4
            prov[s] = "estate_spread_model_v1"
    except Exception as e:
        print("spread model unavailable:", e)
    return sp, prov


# --------------------------------------------------------------------------
def run(M, SP, classes=("crypto",), quant=5, lookback=1, min_hist=120, min_univ=8,
        keep=None, start=None, end=None, cost_mult=1.0, impute_bp=None,
        commission_bp=0.0, slip_mult=0.0):
    """A2 anchor.  Returns the per-day gross/cost/net series in sigma units AND
    in bp of notional, charging each selected leg its own spread twice."""
    C, O = M["C"], M["O"]; T, N = C.shape
    r_cc, r_oc = M["r_cc"], M["r_oc"]; nxt = M["nextC"]
    CL = M["CL"]; syms = M["syms"]; dates = M["dates"]
    VOL = pd.DataFrame(r_cc).rolling(60, min_periods=30).std().values
    HC = np.cumsum(np.isfinite(C), axis=0)
    mask = np.isin(CL, list(classes))
    if keep is not None:
        mask &= np.isin(syms, list(keep))
    spv = np.array([SP.get(s, np.nan) for s in syms])
    if impute_bp is not None:
        spv = np.where(np.isfinite(spv), spv, impute_bp)

    rows = []
    for t in range(1, T - 3):
        d = str(dates[t])[:10]
        if (start and d < start) or (end and d >= end):
            continue
        t1 = nxt[t]
        ok = mask & np.isfinite(r_cc[t]) & np.isfinite(VOL[t]) & (VOL[t] > 0) \
            & (HC[t] >= min_hist) & (t1 >= 0) & np.isfinite(spv)
        ii = np.where(ok)[0]
        if len(ii) < min_univ:
            continue
        fwd = r_oc[t1[ii], ii]
        g = np.isfinite(fwd); ii = ii[g]; fwd = fwd[g]
        if len(ii) < min_univ:
            continue
        v = VOL[t, ii]; s = r_cc[t, ii] / v; f = fwd / v
        o = np.argsort(s); q = max(1, min(len(ii) // 2, len(ii) // quant))
        lo, hi = o[:q], o[-q:]
        gross_sig = float(f[lo].mean() - f[hi].mean())
        legs = np.concatenate([ii[lo], ii[hi]])
        # weights are 1/vol per leg, normalised so total gross notional = 2 units
        wl = 1.0 / v[lo]; wh = 1.0 / v[hi]
        wl = wl / wl.sum(); wh = wh / wh.sum()
        legsp = np.concatenate([spv[ii[lo]] * wl, spv[ii[hi]] * wh])   # bp x weight
        # every leg round-trips every day: 2 crossings, half-spread each = 1 full spread
        cost_bp = float(legsp.sum()) * cost_mult + 2.0 * commission_bp
        cost_bp += slip_mult * float(legsp.sum())
        medv = float(np.median(v))
        rows.append(dict(date=d, n=len(ii), gross_sig=gross_sig,
                         gross_bp=gross_sig * medv * 1e4,
                         cost_bp=cost_bp, medvol=medv,
                         net_bp=gross_sig * medv * 1e4 - cost_bp,
                         lo=";".join(syms[ii[lo]]), hi=";".join(syms[ii[hi]])))
    if len(rows) < 60:
        return None
    df = pd.DataFrame(rows)
    return df


def stats(df, label):
    n = len(df)
    g = df.gross_bp.values; c = df.cost_bp.values; net = df.net_bp.values
    sd = net.std(ddof=1)
    tt = net.mean() / (sd / math.sqrt(n))
    yr = df.groupby(df.date.str[:4]).net_bp.agg(["mean", "size"])
    return dict(label=label, n_days=n, first=df.date.iloc[0], last=df.date.iloc[-1],
                gross_bp=float(g.mean()), cost_bp=float(c.mean()),
                net_bp=float(net.mean()), t_net=float(tt),
                ci95_net_bp=[float(net.mean() - 1.96 * sd / math.sqrt(n)),
                             float(net.mean() + 1.96 * sd / math.sqrt(n))],
                sd_bp=float(sd), sharpe_net_ann=float(net.mean() / sd * math.sqrt(252)),
                median_universe=int(df.n.median()),
                pos_years=int((yr["mean"] > 0).sum()), tot_years=int(len(yr)),
                by_year={k: [round(float(v["mean"]), 3), int(v["size"])]
                         for k, v in yr.iterrows()})


def main():
    M = make_returns(build_matrices())
    SP, PROV = spread_table(M)
    syms = M["syms"]; CL = M["CL"]
    cry = sorted(syms[CL == "crypto"])
    known = [s for s in cry if s in SP]
    unknown = [s for s in cry if s not in SP]
    print("=== crypto universe cost coverage ===")
    for s in known:
        print(f"  {s:9s} {SP[s]:8.2f} bp   {PROV[s]}")
    print(f"  UNPRICED ({len(unknown)}): {unknown}")
    res = {"spreads_bp": {s: round(SP[s], 3) for s in known},
           "spread_provenance": {s: PROV[s] for s in known},
           "unpriced_crypto": unknown}

    out = []
    # (1) full universe, alts imputed at the measured alt anchors
    for imp_name, imp in [("impute_AVAUSD_32.9", 32.9), ("impute_median_known", None),
                          ("impute_optimistic_5bp", 5.0)]:
        v = imp
        if imp is None:
            v = float(np.median([SP[s] for s in known]))
        df = run(M, SP, quant=5, impute_bp=v)
        if df is not None:
            st = stats(df, f"ALLCRYPTO|q5|{imp_name}({v:.1f}bp)")
            out.append(st)
            print(f"\n{st['label']}: gross {st['gross_bp']:+.2f} cost {st['cost_bp']:.2f} "
                  f"net {st['net_bp']:+.2f} bp/day  t {st['t_net']:+.2f}  SR {st['sharpe_net_ann']:+.2f} "
                  f"yrs {st['pos_years']}/{st['tot_years']}")
    # (2) cost-known universe only
    for qz in (5, 3, 2):
        df = run(M, SP, quant=qz, keep=set(known), min_univ=6)
        if df is None:
            continue
        st = stats(df, f"COSTKNOWN({len(known)})|q{qz}")
        out.append(st)
        print(f"{st['label']}: gross {st['gross_bp']:+.2f} cost {st['cost_bp']:.2f} "
              f"net {st['net_bp']:+.2f} bp/day  t {st['t_net']:+.2f}  SR {st['sharpe_net_ann']:+.2f} "
              f"univ {st['median_universe']}  yrs {st['pos_years']}/{st['tot_years']}")
    # (3) gross-only, to isolate what the cost is eating
    df0 = run(M, SP, quant=5, impute_bp=0.0, cost_mult=0.0)
    if df0 is not None:
        st = stats(df0, "ALLCRYPTO|q5|ZERO_COST_reference")
        out.append(st)
        print(f"\n{st['label']}: gross {st['gross_bp']:+.2f} bp/day  t {st['t_net']:+.2f} "
              f"SR {st['sharpe_net_ann']:+.2f} yrs {st['pos_years']}/{st['tot_years']}")
        st["by_year"] and print("  by year:", st["by_year"])
        df0.to_csv(f"{OUT}/S6_CRYPTO_XS_DAILY_SERIES.csv", index=False)
    # (4) the cost at which it breaks even, measured
    if df0 is not None:
        print(f"\nBREAKEVEN: mean gross {df0.gross_bp.mean():.3f} bp/day over "
              f"{len(df0)} days -> the book pays for itself only if the AVERAGE "
              f"weighted leg spread is below {df0.gross_bp.mean()/2:.3f} bp "
              f"(2 legs x 1 full spread each, round-tripped daily).")
        res["breakeven_weighted_leg_spread_bp"] = float(df0.gross_bp.mean() / 2)
        res["measured_leg_spreads_bp"] = {s: round(SP[s], 2) for s in known}

    # (5) walk forward: strictly prior training window decides nothing here (the
    #     rule has no fitted parameter) but the SPLIT is still reported.
    for nm, (a, b) in {"TRAIN_2019_2022": ("2019-01-01", "2023-01-01"),
                       "TEST_2023_2026": ("2023-01-01", "2026-07-01")}.items():
        d = run(M, SP, quant=5, impute_bp=0.0, cost_mult=0.0, start=a, end=b)
        if d is None:
            continue
        st = stats(d, f"ZERO_COST|{nm}")
        out.append(st)
        print(f"{st['label']}: gross {st['gross_bp']:+.2f} bp/day t {st['t_net']:+.2f} "
              f"n={st['n_days']} SR {st['sharpe_net_ann']:+.2f}")

    res["cells"] = out
    json.dump(res, open(f"{OUT}/S6_CRYPTO_RULE_COSTED.json", "w"), indent=1, default=str)
    print("\nwritten", f"{OUT}/S6_CRYPTO_RULE_COSTED.json")


if __name__ == "__main__":
    main()
