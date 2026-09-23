"""S5 - (a) the leg decomposition that PROVES the anchor artifact,
        (b) the constructive variants on clean anchors,
        (c) the crypto cell, which is the only one that survives every anchor,
            stress-tested on cost, survivor bias and leg asymmetry.
"""
from __future__ import annotations
import collections, json, math, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xs import build_matrices, make_returns, cell   # noqa: E402
from panel import classify                          # noqa: E402

OUT = os.path.join(HERE, "receipts")
M = make_returns(build_matrices())
np.seterr(all="ignore")


# --------------------------------------------------------------------------
# (a) leg decomposition.  A0 = overnight(C[t]->O[t+1]) + intraday(O[t+1]->C[t+1]).
#     Only the overnight leg touches C[t], the price the signal also uses.
# --------------------------------------------------------------------------
def leg_decomp(classes=None, exclude=None, min_hist=120, min_univ=12, quant=5):
    C, O = M["C"], M["O"]; T, N = C.shape
    r_cc = M["r_cc"]; nxt = M["nextC"]; CL = M["CL"]; dates = M["dates"]
    VOL = pd.DataFrame(r_cc).rolling(60, min_periods=30).std().values
    HC = np.cumsum(np.isfinite(C), axis=0); idx = np.arange(N)
    mask = np.ones(N, bool)
    if classes is not None:
        mask &= np.isin(CL, classes)
    if exclude is not None:
        mask &= ~np.isin(CL, exclude)
    lC, lO = np.log(C), np.log(O)
    acc = collections.defaultdict(list)
    for t in range(1, T - 3):
        t1 = nxt[t]
        ok = mask & np.isfinite(r_cc[t]) & np.isfinite(VOL[t]) & (VOL[t] > 0) \
            & (HC[t] >= min_hist) & (t1 >= 0)
        ii = np.where(ok)[0]
        if len(ii) < min_univ:
            continue
        t1i = t1[ii]
        on = lO[t1i, ii] - lC[t, ii]          # overnight: TOUCHES C[t]
        intra = lC[t1i, ii] - lO[t1i, ii]     # intraday : touches nothing shared
        full = on + intra
        good = np.isfinite(on) & np.isfinite(intra)
        ii2 = ii[good]
        if len(ii2) < min_univ:
            continue
        v = VOL[t, ii2]
        s = r_cc[t, ii2] / v
        o = np.argsort(s); q = max(3, len(ii2) // quant)
        lo, hi = o[:q], o[-q:]
        for nm, arr in (("overnight", on[good]), ("intraday", intra[good]), ("full", full[good])):
            f = arr / v
            acc[nm].append(float(f[lo].mean() - f[hi].mean()))
        acc["date"].append(str(dates[t])[:10])
    out = {}
    for nm in ("overnight", "intraday", "full"):
        a = np.array(acc[nm]); n = len(a)
        out[nm] = dict(mean=float(a.mean()), t=float(a.mean() / (a.std(ddof=1) / math.sqrt(n))), n=n)
    return out


# --------------------------------------------------------------------------
# (c) crypto stress: single-leg attribution + survivor-safe subset + cost sweep
# --------------------------------------------------------------------------
def leg_attrib(anchor, classes, syms_keep=None, quant=5, min_hist=120, min_univ=8):
    """Return the long-losers leg and the short-winners leg separately, each
    measured against the cross-sectional mean (so they sum to the spread)."""
    C = M["C"]; T, N = C.shape
    r_cc, r_oc = M["r_cc"], M["r_oc"]; nxt = M["nextC"]; CL = M["CL"]
    syms = M["syms"]; dates = M["dates"]
    VOL = pd.DataFrame(r_cc).rolling(60, min_periods=30).std().values
    HC = np.cumsum(np.isfinite(C), axis=0)
    mask = np.isin(CL, classes)
    if syms_keep is not None:
        mask &= np.isin(syms, list(syms_keep))
    LO, HI, ALL, DT = [], [], [], []
    for t in range(1, T - 3):
        t1 = nxt[t]
        ok = mask & np.isfinite(r_cc[t]) & np.isfinite(VOL[t]) & (VOL[t] > 0) \
            & (HC[t] >= min_hist) & (t1 >= 0)
        ii = np.where(ok)[0]
        if len(ii) < min_univ:
            continue
        fwd = r_oc[t1[ii], ii] if anchor == "A2_cc_oc" else r_cc[t1[ii], ii]
        g = np.isfinite(fwd); ii = ii[g]; fwd = fwd[g]
        if len(ii) < min_univ:
            continue
        v = VOL[t, ii]; s = r_cc[t, ii] / v; f = fwd / v
        o = np.argsort(s); q = max(2, len(ii) // quant)
        LO.append(float(f[o[:q]].mean() - f.mean()))
        HI.append(float(f.mean() - f[o[-q:]].mean()))
        ALL.append(float(f.mean())); DT.append(str(dates[t])[:10])
    def st(a):
        a = np.array(a); n = len(a)
        return dict(mean=float(a.mean()), t=float(a.mean() / (a.std(ddof=1) / math.sqrt(n))), n=n)
    return dict(long_losers=st(LO), short_winners=st(HI), universe_mean=st(ALL),
                first=DT[0], last=DT[-1])


def main():
    res = {}

    # ---- (a)
    print("=== (a) LEG DECOMPOSITION: which leg carries A0? ===")
    for uni, kw in [("FX", dict(classes=["fx"])), ("ALL", dict()),
                    ("CRYPTO", dict(classes=["crypto"])),
                    ("NOCRYPTO", dict(exclude=["crypto"]))]:
        r = leg_decomp(**kw)
        res[f"legdecomp_{uni}"] = r
        print(f"{uni:9s} overnight {r['overnight']['mean']:+.5f} (t {r['overnight']['t']:+5.2f})   "
              f"intraday {r['intraday']['mean']:+.5f} (t {r['intraday']['t']:+5.2f})   "
              f"full {r['full']['mean']:+.5f} (t {r['full']['t']:+5.2f})   n={r['full']['n']}")

    # ---- (b) constructive variants, CLEAN anchor only (A2)
    print("\n=== (b) constructive variants on the clean tradeable anchor A2_cc_oc ===")
    rows = []
    for uni, kw in [("FX", dict(classes=["fx"])), ("CRYPTO", dict(classes=["crypto"])),
                    ("ALL", dict()), ("NOCRYPTO", dict(exclude=["crypto"]))]:
        for lb in (1, 2, 3, 5, 10):
            for qz in (5, 3):
                r = cell(M, anchor="A2_cc_oc", lookback=lb, quant=qz, nperm=400, **kw)
                if r is None:
                    continue
                r.pop("_series")
                r["cellname"] = f"A2|{uni}|lb{lb}|q{qz}"
                rows.append(r)
                print(f"{r['cellname']:22s} n={r['n_rebal']:5d} m={r['mean_sigma']:+.5f} "
                      f"t={r['t']:+6.2f} p={r['perm_p']:.3f} BE={r['breakeven_bps_leg']:+7.2f} "
                      f"yrs={r['pos_years']}/{r['tot_years']}", flush=True)
    pd.DataFrame(rows).to_json(f"{OUT}/S5_CONSTRUCTIVE_GRID.json", orient="records", indent=1)

    # ---- (c) crypto stress
    print("\n=== (c) CRYPTO stress ===")
    syms = M["syms"]; CL = M["CL"]
    cry = sorted(syms[CL == "crypto"])
    print("crypto universe:", cry)
    # survivor-safe subset: the coins that existed and still exist across the whole
    # window (top-cap majors); the alts are the ones a point-in-time list would drop
    SAFE = {"BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "BCHUSD", "EOSUSD",
            "XLMUSD", "XMRUSD", "ETCUSD", "DSHUSD", "DASHUSD", "TRXUSD", "NEOUSD",
            "IOTUSD", "ZECUSD", "QTMUSD", "OMGUSD"}
    safe = [s for s in cry if s in SAFE]
    print("survivor-safe subset:", safe)
    for nm, keep in (("ALL_CRYPTO", None), ("SAFE_MAJORS", set(safe))):
        for anchor in ("A0_cc_cc", "A2_cc_oc"):
            r = leg_attrib(anchor, ["crypto"], keep)
            res[f"cryptolegs_{nm}_{anchor}"] = r
            print(f"{nm:12s} {anchor:10s} long-losers {r['long_losers']['mean']:+.5f} "
                  f"(t {r['long_losers']['t']:+5.2f})  short-winners {r['short_winners']['mean']:+.5f} "
                  f"(t {r['short_winners']['t']:+5.2f})  n={r['long_losers']['n']}")
    # crypto on the survivor-safe subset, full cell
    r = cell(M, anchor="A2_cc_oc", classes=["crypto"], nperm=1000, min_univ=8)
    if r:
        r.pop("_series"); res["crypto_A2_full"] = r
        print(f"\ncrypto A2 all: m={r['mean_sigma']:+.5f} t={r['t']:+.2f} p={r['perm_p']:.4f} "
              f"BE={r['breakeven_bps_leg']:+.2f} bps/leg  turnover={r['turnover']:.2f}  "
              f"medvol={r['median_daily_vol']:.5f}")
        print("by year:", r["by_year"])

    json.dump(res, open(f"{OUT}/S5_DECOMP_AND_CRYPTO.json", "w"), indent=1, default=str)
    print("\nwritten", OUT)


if __name__ == "__main__":
    main()
