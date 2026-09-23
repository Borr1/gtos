"""S9 - temporal-leakage audit, to the house standard set by the sibling lane's
lookahead kill (regime features aggregated over candidates generated AFTER the
scored trade; survived walk-forward, prior training, daily refit and four
permutation nulls; died on a one-day lag and a past/future split).

Three tests, run on the only cell in this lane that survived the artifact tests
(crypto XS 1-day reversal, A2 anchor):

  L1  LAG.  Rank on r_cc[t-1] instead of r_cc[t], forward unchanged.
  L2  NORMALISER PURITY.  The vol normaliser VOL[t] is a trailing 60-observation
      std ENDING at t, so it contains the very return being ranked.  That is
      legitimate (it is known at the decision instant) but it can carry the
      result on its own: sig = r/VOL is a ratio, and a symbol with an unusually
      large |r| relative to its own recent vol is ALSO a symbol whose VOL just
      jumped.  Re-run with VOL[t-1], which excludes the scored return entirely.
  L3  PAST/FUTURE SPLIT of the signal itself, the direct analogue of the sibling
      lane's decisive test.  The D1 signal is one number spanning 24 hours.  Cut
      day t at broker hour H and rank on the two halves SEPARATELY -- the early
      half (t-1 close -> t H:00) and the late half (t H:00 -> t close) -- with an
      identical forward (t+1 open -> t+1 close) and identical eligible set.  If
      only the LATE half predicts, the "reversal" is reversion of the hours
      nearest the entry, i.e. microstructure adjacent to the anchor, not an
      economic daily reversal.  If both predict, the signal is genuinely about
      the whole day.

L3 uses the M15 archive (24 of 24 crypto symbols present) so the two halves are
built from prices, not from any aggregate.
"""
from __future__ import annotations
import json, math, os, sys, collections
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xs import build_matrices, make_returns    # noqa: E402
from panel import load_one                     # noqa: E402

OUT = os.path.join(HERE, "receipts")
np.seterr(all="ignore")


def cell_from_signal(M, SIG, VOLM, classes=("crypto",), quant=5, min_hist=120,
                     min_univ=8, start=None, end=None, label=""):
    """A2 forward (O[t+1]->C[t+1]) against an arbitrary pre-supplied signal."""
    C = M["C"]; T, N = C.shape
    r_oc = M["r_oc"]; nxt = M["nextC"]; CL = M["CL"]; dates = M["dates"]
    HC = np.cumsum(np.isfinite(C), axis=0)
    mask = np.isin(CL, list(classes))
    rets, dts, ns = [], [], []
    for t in range(2, T - 3):
        d = str(dates[t])[:10]
        if (start and d < start) or (end and d >= end):
            continue
        t1 = nxt[t]
        ok = mask & np.isfinite(SIG[t]) & np.isfinite(VOLM[t]) & (VOLM[t] > 0) \
            & (HC[t] >= min_hist) & (t1 >= 0)
        ii = np.where(ok)[0]
        if len(ii) < min_univ:
            continue
        fwd = r_oc[t1[ii], ii]
        g = np.isfinite(fwd); ii = ii[g]; fwd = fwd[g]
        if len(ii) < min_univ:
            continue
        v = VOLM[t, ii]; s = SIG[t, ii] / v; f = fwd / v
        o = np.argsort(s); q = max(1, min(len(ii) // 2, len(ii) // quant))
        rets.append(float(f[o[:q]].mean() - f[o[-q:]].mean()))
        dts.append(d); ns.append(len(ii))
    if len(rets) < 60:
        return None
    a = np.array(rets); n = len(a); sd = a.std(ddof=1)
    yr = collections.defaultdict(list)
    for d, x in zip(dts, a):
        yr[d[:4]].append(x)
    return dict(label=label, n=n, mean_sigma=float(a.mean()),
                t=float(a.mean() / (sd / math.sqrt(n))),
                ci95=[float(a.mean() - 1.96 * sd / math.sqrt(n)),
                      float(a.mean() + 1.96 * sd / math.sqrt(n))],
                sharpe_ann=float(a.mean() / sd * math.sqrt(252)),
                first=dts[0], last=dts[-1], median_universe=int(np.median(ns)),
                pos_years=int(sum(1 for y in yr if np.mean(yr[y]) > 0)), tot_years=len(yr))


def split_signals(M, cut_hour=12):
    """Build the early-half and late-half signals for day t from M15 bars.

    early[t] = log P(t, cut_hour) - log C[t-1]        (t-1 close -> t cut)
    late[t]  = log C[t]           - log P(t, cut_hour)(t cut -> t close)
    early + late == r_cc[t] by construction, so the two halves partition exactly
    the signal that produced the headline.
    """
    syms = M["syms"]; CL = M["CL"]; dates = M["dates"]
    di = {pd.Timestamp(d).normalize(): i for i, d in enumerate(dates)}
    T, N = M["C"].shape
    EARLY = np.full((T, N), np.nan); LATE = np.full((T, N), np.nan)
    cross = np.full((T, N), np.nan)
    for j, s in enumerate(syms):
        if CL[j] != "crypto":
            continue
        m = load_one(s, "M15")
        if m is None or len(m) < 5000:
            continue
        bt = pd.DatetimeIndex(m["bt"])
        day = bt.normalize()
        # last bar at or before cut_hour:00 on each broker day
        sel = (bt.hour * 60 + bt.minute) <= cut_hour * 60
        sub = m[sel].groupby(day[sel]).last()
        for d, row in sub.iterrows():
            i = di.get(d)
            if i is not None:
                cross[i, j] = float(row["close"])
    lC = np.log(M["C"]); prevC = M["prevC"]; idx = np.arange(N)
    lX = np.log(cross)
    for t in range(1, T):
        p = prevC[t]
        ok = (p >= 0) & np.isfinite(lX[t]) & np.isfinite(lC[t])
        EARLY[t, ok] = lX[t, ok] - lC[p[ok], idx[ok]]
        LATE[t, ok] = lC[t, ok] - lX[t, ok]
    return EARLY, LATE


def main():
    M = make_returns(build_matrices())
    r_cc = M["r_cc"]
    VOL_t = pd.DataFrame(r_cc).rolling(60, min_periods=30).std().values
    VOL_tm1 = np.roll(VOL_t, 1, axis=0); VOL_tm1[0] = np.nan     # strictly excludes r_cc[t]
    SIG_t = r_cc.copy()
    SIG_tm1 = np.roll(r_cc, 1, axis=0); SIG_tm1[0] = np.nan       # one FULL day older
    res = {}

    print("=== construction audit (by inspection, then by test) ===")
    print("  signal   r_cc[t] = log C[t] - log C[prev] .......... known at day-t close   OK")
    print("  ranking  cross-sectional over symbols at date t .... all inputs t-or-earlier OK")
    print("  vol      rolling(60).std() ENDING at t ............. known at day-t close   OK")
    print("  forward  O[t+1] -> C[t+1] ......................... strictly after entry   OK")
    print("  NOTE: nxt[t] ('next day this symbol trades') is an indexing device that")
    print("        encodes the symbol WILL trade again -- survivorship-adjacent, already")
    print("        disclosed in S5; it is not a within-day information leak.\n")

    print("=== L1  LAG TEST: rank on r_cc[t-1], forward unchanged ===")
    for nm, S in (("baseline r_cc[t]", SIG_t), ("LAGGED r_cc[t-1]", SIG_tm1)):
        for win, (a, b) in {"FULL": (None, None),
                            "TEST_2023_2026": ("2023-01-01", "2026-07-01")}.items():
            r = cell_from_signal(M, S, VOL_t, start=a, end=b, label=f"{nm}|{win}")
            if r:
                res[r["label"]] = r
                print(f"  {r['label']:32s} n={r['n']:5d} m={r['mean_sigma']:+.5f} "
                      f"t={r['t']:+6.2f} SR={r['sharpe_ann']:+5.2f} yrs {r['pos_years']}/{r['tot_years']}")

    print("\n=== L2  NORMALISER PURITY: VOL[t] (contains r_cc[t]) vs VOL[t-1] (does not) ===")
    for nm, V in (("VOL[t]", VOL_t), ("VOL[t-1] pure", VOL_tm1)):
        for win, (a, b) in {"FULL": (None, None),
                            "TEST_2023_2026": ("2023-01-01", "2026-07-01")}.items():
            r = cell_from_signal(M, SIG_t, V, start=a, end=b, label=f"norm {nm}|{win}")
            if r:
                res[r["label"]] = r
                print(f"  {r['label']:32s} n={r['n']:5d} m={r['mean_sigma']:+.5f} "
                      f"t={r['t']:+6.2f} SR={r['sharpe_ann']:+5.2f} yrs {r['pos_years']}/{r['tot_years']}")

    print("\n=== L3  PAST/FUTURE SPLIT of the signal, identical forward and eligible set ===")
    for cut in (8, 12, 18):
        E, L = split_signals(M, cut_hour=cut)
        for nm, S in ((f"EARLY half (prev close -> broker {cut:02d}:00)", E),
                      (f"LATE  half (broker {cut:02d}:00 -> close)", L),
                      ("FULL day (control)", SIG_t)):
            r = cell_from_signal(M, S, VOL_t, label=f"cut{cut:02d}|{nm}")
            if r:
                res[r["label"]] = r
                print(f"  {r['label']:52s} n={r['n']:5d} m={r['mean_sigma']:+.5f} "
                      f"t={r['t']:+6.2f} SR={r['sharpe_ann']:+5.2f}")
        print()

    json.dump(res, open(f"{OUT}/S9_LEAKAGE_AUDIT.json", "w"), indent=1, default=str)
    print("written", f"{OUT}/S9_LEAKAGE_AUDIT.json")


if __name__ == "__main__":
    main()
