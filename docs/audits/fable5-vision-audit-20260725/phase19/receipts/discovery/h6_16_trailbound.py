"""h6 step 16 — the honest-trail bound (B613 / AD 95.8%-intrabar), applied to the
swarm's repaired contract and to this lane's optimum.

e_lib.walk (and therefore every number the swarm published) arms the trail off a bar's
HIGH and only TESTS the new stop from the NEXT bar. Real intrabar retracement past the
trail level inside the arming bar is never charged. The estate's ratified conservative
bound tests the tightened stop against the SAME bar's low.

If the trail premium the placebo panel measured (+0.051 R/trade on random entries) is a
bar-resolution effect, it collapses under the same-bar test. If it survives, it is a
property of the price process.
"""
import json, os, sys, time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h6_lib as H  # noqa: E402
import h6_14_controls as C  # noqa: E402
import h6_02_build_cache as B  # noqa: E402
import gzip

NEG = -1e18


def walk_trail_mode(P, k=0, target=None, stop=-1.0, trail=None, maxbars=None,
                    same_bar=False):
    """Identical to h6_lib.walk_all except `same_bar=True` also tests the tightened
    stop against the arming bar's own low (the conservative bound)."""
    F, A, Cc, NB = P["F"], P["A"], P["C"], P["NB"]
    n = F.shape[0]
    c0 = np.zeros(n) if k == 0 else np.nan_to_num(Cc[:, k - 1], nan=0.0)
    have = np.ones(n, dtype=bool) if k == 0 else (NB >= k)
    last = NB.copy() if maxbars is None else np.minimum(NB, maxbars)
    trd = have & (last > k) & (k < NB - 2)
    r = np.zeros(n); reason = np.zeros(n, dtype=np.int8)
    active = trd.copy()
    stop_lv = np.full(n, stop if stop is not None else NEG)
    peak = np.full(n, NEG)
    hi = int(last.max())
    for i in range(k, hi):
        val = active & (i < last)
        if not val.any():
            break
        f = F[:, i] - c0
        a = A[:, i] - c0
        hs = val & (a <= stop_lv + 1e-12)
        if hs.any():
            r[hs] = stop_lv[hs]; reason[hs] = 1; active &= ~hs; val = active & (i < last)
        if target is not None:
            ht = val & (f >= target - 1e-12)
            if ht.any():
                r[ht] = target; reason[ht] = 2; active &= ~ht; val = active & (i < last)
        np.maximum(peak, f, out=peak, where=val)
        if trail is not None:
            up = val & (peak >= trail)
            if up.any():
                np.maximum(stop_lv, peak - trail, out=stop_lv, where=up)
            if same_bar:
                hs2 = val & (a <= stop_lv + 1e-12)
                if hs2.any():
                    r[hs2] = stop_lv[hs2]; reason[hs2] = 1; active &= ~hs2
    surv = active & trd
    if surv.any():
        idx = np.clip(last - 1, 0, F.shape[1] - 1)
        r[surv] = Cc[surv, idx[surv]] - c0[surv]
        reason[surv] = 4
    r[~trd] = 0.0
    return r, reason, trd


def main():
    t0 = time.time()
    P, M = H.load()
    cost_hour = np.load(f"{D}/h6_cost_hour.npy")
    hour_bps = cost_hour * M["bpsfac"]
    rows = []
    for mk, ml, path in B.FILES:
        for x in gzip.open(path, "rt"):
            if x.strip():
                q = json.loads(x); q["_mk"] = mk; rows.append(q)
    PL = C.build_shifted(rows, 60)
    PL2 = C.build_shifted(rows, 120)
    out = {}

    CTR = {"SWARM_TRAIL025_k5": dict(k=5, target=None, stop=-1.0, trail=0.25, maxbars=None),
           "H6_OPTIMUM_k30": dict(k=30, target=None, stop=-2.0, trail=0.10, maxbars=60),
           "TRAIL050_k5": dict(k=5, target=None, stop=-1.0, trail=0.50, maxbars=None),
           "SHIPPED_INC_k5": dict(k=5, target=2.0, stop=-1.0, trail=None, maxbars=None),
           "STOPONLY_k5": dict(k=5, target=None, stop=-1.0, trail=None, maxbars=None)}
    res = {}
    print(f"{'contract':<22}{'book':<10}{'REAL_opt':>11}{'REAL_honest':>13}{'premium':>10}"
          f"{'PLC60_opt':>11}{'PLC60_hon':>11}{'PLC120_opt':>12}{'PLC120_hon':>12}")
    for name, cw in CTR.items():
        row = {}
        for lab, PP in (("REAL", P), ("PLC60", PL), ("PLC120", PL2)):
            for mode in (False, True):
                r, reason, trd = walk_trail_mode(PP, same_bar=mode, **cw)
                r2, _rs2, trd2 = walk_trail_mode(P, same_bar=mode, **cw)
                both = trd & trd2 & np.isfinite(cost_hour)
                g = r[both]
                nn = int(both.sum())
                row[f"{lab}_{'honest' if mode else 'optimistic'}"] = {
                    "n": nn, "gross": round(float(g.mean()), 6),
                    "t": round(float(g.mean() / (g.std(ddof=1) / np.sqrt(nn))), 3)}
        row["trail_bar_premium_REAL"] = round(
            row["REAL_optimistic"]["gross"] - row["REAL_honest"]["gross"], 6)
        res[name] = row
        print(f"{name:<22}{'gross':<10}{row['REAL_optimistic']['gross']:>11.6f}"
              f"{row['REAL_honest']['gross']:>13.6f}{row['trail_bar_premium_REAL']:>10.6f}"
              f"{row['PLC60_optimistic']['gross']:>11.6f}{row['PLC60_honest']['gross']:>11.6f}"
              f"{row['PLC120_optimistic']['gross']:>12.6f}{row['PLC120_honest']['gross']:>12.6f}")
    out["contracts"] = res

    # what the swarm headline and the h6 optimum become under the honest bound
    hh = {}
    for name, cw in (("SWARM_HEADLINE", dict(k=5, target=None, stop=-1.0, trail=0.25,
                                             maxbars=None)),
                     ("H6_OPTIMUM", dict(k=30, target=None, stop=-2.0, trail=0.10,
                                         maxbars=60))):
        for mode in (False, True):
            r, reason, trd = walk_trail_mode(P, same_bar=mode, **cw)
            for pop, pm in (("ALL", trd & np.isfinite(cost_hour)),
                            ("hourbps<=0.60", trd & np.isfinite(cost_hour)
                             & (hour_bps <= 0.60 + 1e-12))):
                g = r[pm]; c = cost_hour[pm]; nt = g - c
                nn = int(pm.sum())
                hh[f"{name}|{'honest' if mode else 'optimistic'}|{pop}"] = {
                    "n": nn, "gross": round(float(g.mean()), 6),
                    "cost": round(float(c.mean()), 6), "net": round(float(nt.mean()), 6),
                    "t_gross": round(float(g.mean() / (g.std(ddof=1) / np.sqrt(nn))), 3),
                    "t_net": round(float(nt.mean() / (nt.std(ddof=1) / np.sqrt(nn))), 3),
                    "ratio_r": round(float(g.mean() / c.mean()), 4),
                    "n_sym_gross_pos": int(sum(
                        1 for s in np.unique(M["symbol"][pm])
                        if r[pm & (M["symbol"] == s)].mean() > 0))}
    out["headline_under_honest_bound"] = hh
    print("\n=== the two headline forms under the ratified honest-trail bound ===")
    for k2, v in hh.items():
        print(f"  {k2:<44} n {v['n']:>6} gross {v['gross']:+.6f} (t {v['t_gross']:+.2f})"
              f" net {v['net']:+.6f} rr {v['ratio_r']:.3f} sym_gross+ {v['n_sym_gross_pos']}")

    json.dump(out, open(f"{D}/H6_TRAILBOUND_V1.json", "w"), indent=1)
    print("wrote H6_TRAILBOUND_V1.json", round(time.time() - t0, 1), flush=True)


if __name__ == "__main__":
    main()
