#!/usr/bin/env python3
"""Stage E -- does a better label produce a better BOOK?

Two independent questions, kept apart because they have different answers:

  E-*   change the RANKER, book the sealed terminal_net_r.  Paired against the
        shipped rule day by day (primary metric E1).
  X-*   keep the shipped ranker, change the EXIT.  This is the only channel by
        which Stage P's target frontier can reach a deployable book.

Every arm reports MARKET-top share and no-fill share alongside its book,
because B2 established the estate's governing law: realized book R is monotone
in how often the selector transacts (r = -0.9786 across 17 arms), so an arm
that books worse because it fills more has explained itself.
"""
from __future__ import annotations

import gzip
import json
import math
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f2_lib as L

B3 = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725/"
          "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/"
          "outcome_authority/swarm2/breakthrough/b3_selector")
sys.path.insert(0, str(B3))
import b3_lib as B  # the frozen funnel, unmodified

WF = Path("/Users/borr/.claude/jobs/adb9e69b/tmp/f2/wf")
OUTD = Path(__file__).resolve().parent / "receipts"


def book_stats(meta, windows, selected, tgt=None, exit_col=None, ded=None):
    """Realized book. If exit_col is given, re-books each selection under that
    policy's realized net R instead of the sealed terminal_net_r."""
    by_day = defaultdict(float)
    tot = 0.0
    n_res = 0
    nofill = 0
    for i in selected:
        if exit_col is None:
            if not meta[i]["res"]:
                continue
            v = meta[i]["net"]
        else:
            v = tgt[exit_col][i]
            if not np.isfinite(v):
                continue
        n_res += 1
        if meta[i]["c5"] == "NO_FILL":
            nofill += 1
        tot += v
        by_day[meta[i]["day"]] += v
    mkt = sum(1 for w in windows if w["top_order_type"] == "MARKET")
    ranked = len(windows)
    tops_nofill = sum(1 for w in windows if w["pick_actual"] == 0.0)
    tops_res = sum(1 for w in windows if w["pick_actual"] is not None)
    return {"trades": len(selected), "resolved": n_res, "actual_net_r": tot,
            "positive_days": sum(1 for v in by_day.values() if v > 0),
            "negative_days": sum(1 for v in by_day.values() if v < 0),
            "no_fill_share_of_traded": (nofill / n_res) if n_res else None,
            "no_fill_share_of_window_TOPS": (tops_nofill / tops_res) if tops_res else None,
            "market_top_share_of_ranked": (mkt / ranked) if ranked else None,
            "_by_day": dict(by_day)}


def paired_e1(a, b, days):
    d = [a.get(x, 0.0) - b.get(x, 0.0) for x in days]
    return L.boot_day(d, days), float(np.sum(d))


def main(variant="base"):
    meta, X, names_col, tgt, filled, ded, info = L.build_dataset()
    Z = np.load(WF / f"preds_{variant}.npz", allow_pickle=True)
    preds = Z["preds"].astype(np.float64)
    names = list(Z["names"]); idx = {n: k for k, n in enumerate(names)}
    scored_days = set(str(d) for d in Z["scored"])
    n = len(meta)
    rows = np.asarray([i for i, m in enumerate(meta) if m["cday"] in scored_days],
                      dtype=np.int64)
    days = sorted({meta[i]["day"] for i in rows})

    # ---- the ranking statistics -------------------------------------------
    lad = np.asarray(L.LADDER)
    EV = np.full((n, len(lad)), np.nan)
    for j, k in enumerate(lad):
        EV[:, j] = preds[:, idx[f"pol_{k}"]]
    ev_max = np.nanmax(EV, axis=1)
    pfill = np.clip(preds[:, idx["fill"]], 0.0, 1.0)

    stats = {
        "E-SHIP-F2": preds[:, idx["tnr"]],                   # shipped label, F2 estimator
        "E-MFE-RAW": preds[:, idx["mfe"]],
        "E-MFE-EV": ev_max,
        "E-MAE": preds[:, idx["mae"]],
        "E-HURDLE-EV": pfill * np.where(np.isfinite(ev_max), ev_max, np.nan),
        "E-NEGCOST": -np.asarray([m["cost"] for m in meta], dtype=float),
    }

    rep = {"variant": variant, "prereg_sha256": L.PREREG_SHA, "arms": {}, "E1": {}}

    # control: the shipped rule under the identical funnel
    w_ship, s_ship = B.run_windows(meta, rows, stats["E-SHIP-F2"], occupancy=True,
                                   policy="market_top_abstain",
                                   min_pred=L.MIN_EXPECTED_NET_R)
    b_ship = book_stats(meta, w_ship, s_ship)
    rep["arms"]["E-SHIP-F2"] = {k: v for k, v in b_ship.items() if k != "_by_day"}

    for tag, stat in stats.items():
        for gate, mp in (("gated", L.MIN_EXPECTED_NET_R), ("ungated", -1e18)):
            if tag == "E-SHIP-F2" and gate == "gated":
                w, s, bb = w_ship, s_ship, b_ship
            else:
                w, s = B.run_windows(meta, rows, stat, occupancy=True,
                                     policy="market_top_abstain", min_pred=mp)
                bb = book_stats(meta, w, s)
            key = f"{tag}::{gate}"
            rep["arms"][key] = {k: v for k, v in bb.items() if k != "_by_day"}
            e1, tot = paired_e1(bb["_by_day"], b_ship["_by_day"], days)
            rep["E1"][key] = {"sum_diff_r": tot, **{k: e1[k] for k in
                              ("point", "ci95_lo", "ci95_hi", "p_two_sided_sign", "n")}}

    # ---- matched trade counts (PREREG_V1_2's rule): the min_pred floor is not
    # scale-invariant, so every cross-arm economic comparison is repeated at the
    # shipped rule's own trade count and at a declared ladder of counts.
    rep["matched_N"] = {}
    N_ship = len(s_ship)
    for tag, stat in stats.items():
        w, s_all = B.run_windows(meta, rows, stat, occupancy=True,
                                 policy="market_top_abstain", min_pred=-1e18)
        order = sorted(range(len(s_all)),
                       key=lambda z: -float(stat[s_all[z]]))
        rep["matched_N"][tag] = {}
        for N in (50, 100, N_ship, 300, 600):
            take = [s_all[z] for z in order[:N]]
            bd = defaultdict(float); tot = 0.0
            for i in take:
                if not meta[i]["res"]:
                    continue
                tot += meta[i]["net"]; bd[meta[i]["day"]] += meta[i]["net"]
            e1, sd_ = paired_e1(bd, b_ship["_by_day"], days)
            rep["matched_N"][tag][str(N)] = {
                "trades": len(take), "book_r": tot,
                "vs_shipped_total_r": sd_, "vs_shipped_per_day": e1["point"],
                "ci95_lo": e1["ci95_lo"], "ci95_hi": e1["ci95_hi"],
                "p": e1["p_two_sided_sign"]}

    # ---- X-* : shipped ranker, changed EXIT ---------------------------------
    j2 = L.LADDER.index(2.0)
    # causal best-constant target, re-chosen daily on strictly prior scored days
    Rk_all = np.column_stack([tgt[f"pol_{k}"] for k in L.LADDER])
    cds = np.asarray([m["cday"] for m in meta], dtype=object)
    order = sorted({c for c in cds[rows]})
    cum = np.zeros(len(lad)); cn = 0
    bestk = np.full(n, j2, dtype=int)
    for d in order:
        m = rows[cds[rows] == d]
        if cn > 0:
            bestk[m] = int(np.argmax(cum / cn))
        good = m[np.isfinite(Rk_all[m]).all(axis=1)]
        if len(good):
            cum += Rk_all[good].sum(axis=0); cn += len(good)
    exit_arms = {}
    for tag, chooser in (("X-FIX2", lambda i: j2),
                         ("X-FIXBEST", lambda i: bestk[i]),
                         ("X-ADAPT", lambda i: int(np.nanargmax(EV[i]))
                          if np.isfinite(EV[i]).any() else j2)):
        vals, dys = [], []
        for i in s_ship:
            if not filled[i]:
                # a pick that never filled books exactly 0.0 under every exit
                vals.append(0.0 if meta[i]["res"] else np.nan)
                dys.append(meta[i]["day"]); continue
            j = chooser(i)
            vals.append(Rk_all[i, j]); dys.append(meta[i]["day"])
        vals = np.asarray(vals, dtype=float)
        keep = np.isfinite(vals)
        by_day = defaultdict(float)
        for v, d in zip(vals[keep], np.asarray(dys)[keep]):
            by_day[d] += v
        exit_arms[tag] = {"trades": int(keep.sum()), "actual_net_r": float(vals[keep].sum()),
                          "positive_days": sum(1 for v in by_day.values() if v > 0),
                          "negative_days": sum(1 for v in by_day.values() if v < 0),
                          "_by_day": dict(by_day)}
    for tag in ("X-FIXBEST", "X-ADAPT"):
        e1, tot = paired_e1(exit_arms[tag]["_by_day"], exit_arms["X-FIX2"]["_by_day"], days)
        rep["E1"][f"{tag}_minus_X-FIX2"] = {"sum_diff_r": tot,
                                            **{k: e1[k] for k in ("point", "ci95_lo",
                                               "ci95_hi", "p_two_sided_sign", "n")}}
    rep["exit_arms"] = {k: {kk: vv for kk, vv in v.items() if kk != "_by_day"}
                        for k, v in exit_arms.items()}
    # sanity: X-FIX2 must reproduce the sealed book on the same selections
    rep["exit_arms"]["X-FIX2"]["sealed_book_on_same_selections"] = b_ship["actual_net_r"]

    # per month
    rep["per_month"] = {}
    mon = {m["day"]: m["month"] for m in meta}
    for key in ("E-MFE-EV::gated", "E-MAE::gated", "E-NEGCOST::gated"):
        pass
    OUTD.mkdir(parents=True, exist_ok=True)
    (OUTD / f"E1_ECONOMICS_{variant}.json").write_text(json.dumps(rep, indent=1, default=str))

    print(f"{'arm':<26}{'trades':>8}{'bookR':>11}{'MKTtop%':>9}{'nofill%':>9}"
          f"{'E1/day':>10}{'ci_lo':>9}{'ci_hi':>9}{'p':>7}")
    for key, v in rep["arms"].items():
        e = rep["E1"].get(key)
        mt = v.get("market_top_share_of_ranked") or 0
        nf = v.get("no_fill_share_of_picks") or 0
        if e:
            print(f"{key:<26}{v['trades']:>8}{v['actual_net_r']:>+11.2f}{mt*100:>9.2f}"
                  f"{nf*100:>9.2f}{e['point']:>+10.4f}{e['ci95_lo']:>+9.4f}"
                  f"{e['ci95_hi']:>+9.4f}{e['p_two_sided_sign']:>7.3f}")
        else:
            print(f"{key:<26}{v['trades']:>8}{v['actual_net_r']:>+11.2f}{mt*100:>9.2f}{nf*100:>9.2f}")
    print("\nMATCHED TRADE COUNT (book R; shipped = %+.2f on %d)" % (b_ship["actual_net_r"], N_ship))
    hdr = [50, 100, N_ship, 300, 600]
    print(f"{'arm':<16}" + "".join(f"{('N='+str(h)):>13}" for h in hdr))
    for tag in stats:
        print(f"{tag:<16}" + "".join(
            f"{rep['matched_N'][tag][str(h)]['book_r']:>+13.2f}" for h in hdr))

    print("\nEXIT OVERLAY on the shipped selections")
    for k, v in rep["exit_arms"].items():
        print(f"  {k:<12}{v['trades']:>6} trades  book {v['actual_net_r']:>+9.3f} R "
              f"(+{v['positive_days']}/-{v['negative_days']} days)")
    for k in ("X-FIXBEST_minus_X-FIX2", "X-ADAPT_minus_X-FIX2"):
        e = rep["E1"][k]
        print(f"  {k:<26}{e['sum_diff_r']:>+9.3f} R total, per day {e['point']:+.4f} "
              f"[{e['ci95_lo']:+.4f},{e['ci95_hi']:+.4f}] p={e['p_two_sided_sign']:.4f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "base")
