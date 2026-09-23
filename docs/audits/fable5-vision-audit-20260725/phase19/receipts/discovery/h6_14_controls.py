"""h6 step 14 — controls on the winning cell.

  1. LONG/SHORT split. The paying cohort is 87% index CFD over Jan-Mar 2026; if it is
     long-biased the "edge" could be index drift.
  2. PLACEBO ANCHOR. Rebuild the identical cohort with the decision instant shifted
     +60 / +120 / -60 minutes, keeping symbol, hour-band, cost, side and contract
     identical. The signal is decorrelated; everything else survives. If the placebo
     also pays, the cell is instrument/hour structure, not the broad signal.
  3. Drift control: the same contract on a side-flipped book.
"""
import bisect, csv, gzip, json, os, sys, time
from datetime import datetime, timedelta

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h6_lib as H  # noqa: E402
import h6_02_build_cache as B  # noqa: E402

OPT = dict(k=30, trail=0.10, target=None, stop=-2.0, maxbars=60)
CAP = 0.60
HZ = 120


def build_shifted(rows, shift_min):
    n = len(rows)
    F = np.full((n, HZ), np.nan); A = np.full((n, HZ), np.nan); C = np.full((n, HZ), np.nan)
    NB = np.zeros(n, dtype=np.int32)
    cache = {}
    for idx, r in enumerate(rows):
        ck = (r["_mk"], r["symbol"])
        if ck not in cache:
            cache[ck] = B.load_bars(r["_mk"], r["symbol"])
        b = cache[ck]
        if b is None:
            continue
        dt = (datetime.fromisoformat(r["dt"]) + timedelta(minutes=shift_min)).isoformat()
        i = bisect.bisect_right(b["t"], dt) - 1
        if i < 1:
            continue
        entry_bar = b["c"][i]          # placebo entry = the market at the shifted instant
        d = float(r["risk_distance"])  # same risk unit, same instrument, same side
        sgn = 1.0 if r["side"] == "LONG" else -1.0
        end = (datetime.fromisoformat(dt) + timedelta(minutes=120)).isoformat()
        fav, adv, cls = [], [], []
        for kx in range(i + 1, min(i + 126, len(b["t"]))):
            if b["t"][kx] <= dt or b["t"][kx] > end:
                if b["t"][kx] > end:
                    break
                continue
            hi = sgn * (b["h"][kx] - entry_bar) / d
            lo = sgn * (b["l"][kx] - entry_bar) / d
            fav.append(max(hi, lo)); adv.append(min(hi, lo))
            cls.append(sgn * (b["c"][kx] - entry_bar) / d)
            if len(fav) >= HZ:
                break
        if len(fav) < 5:
            continue
        m = len(fav)
        F[idx, :m] = fav; A[idx, :m] = adv; C[idx, :m] = cls; NB[idx] = m
    return {"F": F, "A": A, "C": C, "NB": NB}


def main():
    t0 = time.time()
    P, M = H.load()
    cost_hour = np.load(f"{D}/h6_cost_hour.npy")
    Mh = dict(M); Mh["cost_true"] = cost_hour
    hour_bps = cost_hour * M["bpsfac"]
    out = {}

    r, reason, _e, trd, c0 = H.walk_all(P, **OPT)
    sel = trd & np.isfinite(cost_hour) & (hour_bps <= CAP + 1e-12)
    out["cell_n"] = int(sel.sum())

    # ---- 1. side split
    side = M["side"]
    ss = {}
    for s in ("LONG", "SHORT"):
        m = sel & (side == s)
        nn = int(m.sum())
        g = r[m]; c = cost_hour[m]; nt = g - c
        ss[s] = {"n": nn, "share": round(nn / int(sel.sum()), 4),
                 "gross": round(float(g.mean()), 6), "cost": round(float(c.mean()), 6),
                 "net": round(float(nt.mean()), 6),
                 "t_net": round(float(nt.mean() / (nt.std(ddof=1) / np.sqrt(nn))), 3),
                 "ratio_r": round(float(g.mean() / c.mean()), 4)}
    out["side_split"] = ss
    print("side split", json.dumps(ss), flush=True)

    # ---- 3. side-flipped book (same rows, R negated on the FAV/ADV frame is not a
    # simple negation once a stop exists, so this is reported as the mirror of the
    # realised R only -- an upper bound on what a reversed book would book)
    nt = r[sel] - cost_hour[sel]
    out["mirror_of_realised_R_minus_cost"] = {
        "note": "-(gross) - cost, i.e. the same paths taken the other way with the same "
                "toll; NOT a re-walk (a stop is not sign-symmetric).",
        "net": round(float((-r[sel] - cost_hour[sel]).mean()), 6)}

    # ---- 2. placebo anchors
    rows = []
    for mk, ml, path in B.FILES:
        for x in gzip.open(path, "rt"):
            if x.strip():
                q = json.loads(x); q["_mk"] = mk; rows.append(q)
    pl = {}
    for shift in (-60, 60, 120):
        Pp = build_shifted(rows, shift)
        rp, rsp, _e2, tdp, c0p = H.walk_all(Pp, **OPT)
        selp = tdp & sel                     # SAME cohort rows, same cost gate
        nn = int(selp.sum())
        g = rp[selp]; c = cost_hour[selp]; ntp = g - c
        pl[str(shift)] = {"n": nn, "gross": round(float(g.mean()), 6),
                          "cost": round(float(c.mean()), 6),
                          "net": round(float(ntp.mean()), 6),
                          "t_net": round(float(ntp.mean() / (ntp.std(ddof=1) / np.sqrt(nn))), 3),
                          "t_gross": round(float(g.mean() / (g.std(ddof=1) / np.sqrt(nn))), 3),
                          "ratio_r": round(float(g.mean() / c.mean()), 4),
                          "boot": H.bootstrap_days(rp, Mh, selp, field="net")}
        print("placebo", shift, json.dumps({k: v for k, v in pl[str(shift)].items()
                                            if k != "boot"}), flush=True)
    out["placebo_anchor"] = pl

    # ---- also placebo on the FULL cohort gross (the swarm headline's own control)
    Pp = build_shifted(rows, 60)
    rp, rsp, _e2, tdp, c0p = H.walk_all(Pp, k=5, target=None, stop=-1.0, trail=0.25)
    r5, _rs5, _e5, td5, _c5 = H.walk_all(P, k=5, target=None, stop=-1.0, trail=0.25)
    both = tdp & td5 & np.isfinite(cost_hour)
    out["placebo_full_cohort_swarm_contract"] = {
        "n": int(both.sum()),
        "real_gross": round(float(r5[both].mean()), 6),
        "placebo_gross": round(float(rp[both].mean()), 6),
        "real_t": round(float(r5[both].mean() / (r5[both].std(ddof=1) / np.sqrt(int(both.sum())))), 3),
        "placebo_t": round(float(rp[both].mean() / (rp[both].std(ddof=1) / np.sqrt(int(both.sum())))), 3)}
    print("placebo full cohort", json.dumps(out["placebo_full_cohort_swarm_contract"]), flush=True)

    json.dump(out, open(f"{D}/H6_CONTROLS_V1.json", "w"), indent=1)
    print("wrote H6_CONTROLS_V1.json", round(time.time() - t0, 1), flush=True)


if __name__ == "__main__":
    main()
