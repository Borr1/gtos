#!/usr/bin/env python3
"""Stage P -- the adaptive take-profit.

The ranking question and the EXIT question are independent: a model that cannot
choose which candidate to trade may still choose how far to run the one it took.
The estate's convention is a fixed 2R target measured from the ENTRY price
(verified: 2.0000 for 100 % of candidates, on every month).

realized_R(i,k) is deterministic from the census -- no model is involved in the
outcome, only in the choice of k.  Policies compared:

  P-FIX2      k = 2.0 for every trade                          (the convention)
  P-FIXK      k fixed at each ladder level                     (control)
  P-FIXBEST   k = the single constant maximising STRICTLY PRIOR realized net R,
              re-chosen every scored day                       (the causal control
              that P-ADAPT must beat -- an argmax over 14 noisy estimates is
              biased upward, so "adaptive beats fixed 2R" is not the test)
  P-ADAPT     k_i = argmax_k Ehat[realized_R(i,k) | x_i]
  P-MFEMAP    k_i = ladder level nearest Ehat[MFE | x_i]
  P-ORACLE    k_i = argmax_k realized_R(i,k)                   (upper bound, never a claim)

Reported on two populations: every filled trade in the pool, and the trades the
frozen funnel actually selects.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f2_lib as L

WF = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f2/wf")
OUTD = Path(__file__).resolve().parent / "receipts"


def summarise(realized, hit, days, tag, chosen_k=None):
    b = L.boot_day(realized, days)
    out = {"policy": tag, "n_trades": len(realized),
           "net_r_per_trade": b["point"], "ci95_lo": b["ci95_lo"], "ci95_hi": b["ci95_hi"],
           "p": b["p_two_sided_sign"], "total_net_r": float(np.sum(realized)),
           "hit_rate": float(np.mean(hit))}
    if chosen_k is not None:
        vals, cnts = np.unique(chosen_k, return_counts=True)
        out["k_distribution"] = {str(v): int(c) for v, c in zip(vals, cnts)}
        out["mean_k"] = float(np.mean(chosen_k))
    return out


def main(variant="base"):
    meta, X, names_col, tgt, filled, ded, info = L.build_dataset()
    Z = np.load(WF / f"preds_{variant}.npz", allow_pickle=True)
    preds = Z["preds"].astype(np.float64)
    names = list(Z["names"]); idx = {n: k for k, n in enumerate(names)}
    scored_days = set(str(d) for d in Z["scored"])

    rows = np.asarray([i for i, m in enumerate(meta)
                       if m["cday"] in scored_days and filled[i]], dtype=np.int64)
    days = np.asarray([meta[i]["day"] for i in rows], dtype=object)
    cdays = np.asarray([meta[i]["cday"] for i in rows], dtype=object)
    K = len(L.LADDER)
    # realized net R and target-hit indicator under every constant policy
    Rk = np.column_stack([tgt[f"pol_{k}"][rows] for k in L.LADDER])
    Hk = np.column_stack([np.isclose(tgt[f"pol_{k}"][rows] + ded[rows], k, atol=1e-9)
                          for k in L.LADDER])
    Pk = np.column_stack([preds[rows, idx[f"pol_{k}"]] for k in L.LADDER])
    ok = np.isfinite(Rk).all(axis=1) & np.isfinite(Pk).all(axis=1)
    rows, days, cdays, Rk, Hk, Pk = rows[ok], days[ok], cdays[ok], Rk[ok], Hk[ok], Pk[ok]

    rep = {"variant": variant, "prereg_sha256": L.PREREG_SHA,
           "ladder": L.LADDER, "n_filled_scored": int(len(rows)), "policies": {},
           "reachability": {}}

    # ---- reachability and the break-even arithmetic at each constant k ------
    for j, k in enumerate(L.LADDER):
        hit = Hk[:, j]
        loss = Rk[~hit, j]
        eloss = float(np.mean(loss)) if len(loss) else float("nan")
        net_win = k - float(np.mean(ded[rows][hit])) if hit.any() else float("nan")
        be = (-eloss) / (net_win - eloss) if np.isfinite(eloss) and net_win > eloss else float("nan")
        rep["reachability"][str(k)] = {
            "hit_rate": float(np.mean(hit)),
            "mean_net_r_when_hit": float(np.mean(Rk[hit, j])) if hit.any() else None,
            "mean_net_r_when_missed": eloss,
            "breakeven_hit_rate_required": be,
            "hit_minus_breakeven": float(np.mean(hit)) - be if np.isfinite(be) else None}

    def run_on(sel, label):
        sub = {}
        Rs, Hs, Ps, ds = Rk[sel], Hk[sel], Pk[sel], days[sel]
        cds = cdays[sel]
        j2 = L.LADDER.index(2.0)
        sub["P-FIX2"] = summarise(Rs[:, j2], Hs[:, j2], ds, "P-FIX2",
                                  np.full(len(Rs), 2.0))
        for j, k in enumerate(L.LADDER):
            sub[f"P-FIX{k}"] = summarise(Rs[:, j], Hs[:, j], ds, f"P-FIX{k}",
                                         np.full(len(Rs), k))
        # P-FIXBEST: the best constant on strictly prior scored days, re-chosen daily
        order = sorted(set(cds.tolist()))
        cum_sum = np.zeros(K); cum_n = 0
        best = np.zeros(len(Rs), dtype=int)
        for d in order:
            m = cds == d
            best[m] = int(np.argmax(cum_sum / cum_n)) if cum_n > 0 else j2
            cum_sum += Rs[m].sum(axis=0); cum_n += int(m.sum())
        r = Rs[np.arange(len(Rs)), best]; h = Hs[np.arange(len(Rs)), best]
        sub["P-FIXBEST"] = summarise(r, h, ds, "P-FIXBEST",
                                     np.asarray(L.LADDER)[best])
        # P-ADAPT
        a = np.argmax(Ps, axis=1)
        sub["P-ADAPT"] = summarise(Rs[np.arange(len(Rs)), a], Hs[np.arange(len(Rs)), a],
                                   ds, "P-ADAPT", np.asarray(L.LADDER)[a])
        # P-MFEMAP
        pm = preds[rows[sel], idx["mfe"]]
        lad = np.asarray(L.LADDER)
        mp = np.abs(pm[:, None] - lad[None, :]).argmin(axis=1)
        sub["P-MFEMAP"] = summarise(Rs[np.arange(len(Rs)), mp], Hs[np.arange(len(Rs)), mp],
                                    ds, "P-MFEMAP", lad[mp])
        # P-ORACLE
        o = np.argmax(Rs, axis=1)
        sub["P-ORACLE"] = summarise(Rs[np.arange(len(Rs)), o], Hs[np.arange(len(Rs)), o],
                                    ds, "P-ORACLE", lad[o])
        # paired differences, day-clustered
        pairs = {}
        for tag, arr in (("P-ADAPT", Rs[np.arange(len(Rs)), a]),
                         ("P-MFEMAP", Rs[np.arange(len(Rs)), mp]),
                         ("P-FIXBEST", r)):
            for ref_tag, ref in (("P-FIX2", Rs[:, j2]),
                                 ("P-FIXBEST", r)):
                if tag == ref_tag:
                    continue
                pairs[f"{tag}_minus_{ref_tag}"] = L.boot_day(list(arr - ref), list(ds))
        sub["_paired"] = pairs
        return sub

    rep["policies"]["ALL_FILLED"] = run_on(np.ones(len(rows), dtype=bool), "all")

    # ---- the deployable population: what the frozen funnel selects ----------
    try:
        import pickle, gzip
        with gzip.open(L.B3OUT / "windows_SHIPPED.pkl.gz", "rb") as fh:
            shipped = pickle.load(fh)
        sel_keys = set()
        if isinstance(shipped, dict) and "selected_keys" in shipped:
            sel_keys = set(shipped["selected_keys"])
        rep["shipped_selected_available"] = len(sel_keys)
    except Exception as exc:  # pragma: no cover
        rep["shipped_selected_available"] = f"unavailable: {exc}"

    OUTD.mkdir(parents=True, exist_ok=True)
    (OUTD / f"P1_ADAPTIVE_TARGET_{variant}.json").write_text(json.dumps(rep, indent=1))

    print(f"{'policy':<14}{'n':>8}{'netR/trade':>12}{'ci_lo':>10}{'ci_hi':>10}"
          f"{'hit':>8}{'meanK':>8}{'totalR':>12}")
    P = rep["policies"]["ALL_FILLED"]
    for tag in ["P-FIX2", "P-FIXBEST", "P-ADAPT", "P-MFEMAP", "P-ORACLE"]:
        v = P[tag]
        print(f"{tag:<14}{v['n_trades']:>8,}{v['net_r_per_trade']:>+12.4f}"
              f"{v['ci95_lo']:>+10.4f}{v['ci95_hi']:>+10.4f}{v['hit_rate']:>8.4f}"
              f"{v['mean_k']:>8.2f}{v['total_net_r']:>+12.1f}")
    print("\nCONSTANT-TARGET LADDER")
    print(f"{'k':>6}{'netR/trade':>12}{'hit':>9}{'breakeven':>11}{'hit-be':>9}")
    for k in L.LADDER:
        v = P[f"P-FIX{k}"]; rr = rep["reachability"][str(k)]
        be = rr["breakeven_hit_rate_required"]
        print(f"{k:>6}{v['net_r_per_trade']:>+12.4f}{rr['hit_rate']:>9.4f}"
              f"{be:>11.4f}{(rr['hit_rate']-be):>+9.4f}")
    print("\nPAIRED")
    for k, v in P["_paired"].items():
        print(f"  {k:<32}{v['point']:>+9.4f} [{v['ci95_lo']:+.4f},{v['ci95_hi']:+.4f}] p={v['p_two_sided_sign']:.4f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "base")
