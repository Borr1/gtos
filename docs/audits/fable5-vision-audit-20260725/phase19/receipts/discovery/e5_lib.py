"""e5_lib — one instrument for the L2-F6 stop-width question, reusable across months.

Builds, per candidate, a monotone excursion ladder from the fill bar onward so that the
outcome at ANY stop multiple k can be read in O(log n), then prices it.

CONVENTIONS (identical to l2_07_adaptive_stop.py, verified to reproduce it exactly):
  * population  : filled inside the walk (first bar with adv <= 0) AND ex-born_past_stop
  * walk        : first touch, conservative tie (stop wins inside the same M1 bar)
  * convention A: structural PRICE target held fixed while the stop moves
  * convention B: proportional target -- target moves to 2k when the stop moves to k
  * R conversion: R_new = R_orig / k, cost_new = cost_price / k
  * cost terms  : spread_r + commission_r + swap_cost_r are PRICE-denominated and divide
                  by k. expected_slippage_r is a flat 0.02 R allowance; l2 held it flat,
                  the physical reading divides it too. Both are carried.
"""
from __future__ import annotations

import bisect

INF_K = 1e9


def build_entries(rows_by_key, rpath_iter, anchor_by_key=None, target_default=2.0):
    """rows_by_key: dict key -> pool row. rpath_iter: iterable of R-path rows.
    anchor_by_key: optional dict key -> {'mkt_r_prev_close': float} for born-state.
    Returns (entries, stats)."""
    ents = []
    st = {"paths": 0, "joined": 0, "no_fill": 0, "past_stop": 0}
    for rp in rpath_iter:
        st["paths"] += 1
        k = (rp["candidate_id"], rp["decision_time_utc"])
        r = rows_by_key.get(k)
        if r is None:
            continue
        st["joined"] += 1
        m = None
        if anchor_by_key is not None:
            a = anchor_by_key.get(k)
            m = a.get("mkt_r_prev_close") if a else None
        if m is not None and m <= -1.0:
            st["past_stop"] += 1
            continue
        fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
        n = len(fav)
        fb = next((i for i in range(n) if adv[i] <= 1e-12), None)
        if fb is None:
            st["no_fill"] += 1
            continue
        # monotone ladders from the fill bar onward
        minv = []
        mini = []
        cur = 1e18
        maxv = []
        maxi = []
        curx = -1e18
        for i in range(fb, n):
            if adv[i] < cur:
                cur = adv[i]
                minv.append(-cur)
                mini.append(i)
            if fav[i] > curx:
                curx = fav[i]
                maxv.append(curx)
                maxi.append(i)
        ents.append({
            "cid": rp["candidate_id"], "dt": rp["decision_time_utc"],
            "fam": r.get("origin_family"), "sym": r.get("symbol"),
            "sess": r.get("session_bucket"), "side": r.get("side") or r.get("direction"),
            "hour": (rp["decision_time_utc"][11:13] if rp.get("decision_time_utc") else None),
            "tgt": (r.get("policy_target_r") or target_default),
            "sp": float(r.get("spread_r") or 0.0), "cm": float(r.get("commission_r") or 0.0),
            "sww": float(r.get("swap_cost_r") or 0.0),
            "sl": float(r.get("expected_slippage_r") or 0.0),
            "m": m,
            "lad": (minv, mini, maxv, maxi, cls[n - 1]),
        })
    return ents, st


def walk_k(e, kk, target_mode="A"):
    """R in the ORIGINAL risk unit at stop multiple kk.
    target_mode 'A' = fixed structural price target; 'B' = target at 2*kk."""
    minv, mini, maxv, maxi, endc = e["lad"]
    tgt = e["tgt"] if target_mode == "A" else 2.0 * kk
    j = bisect.bisect_left(minv, kk - 1e-12)
    bs = mini[j] if j < len(mini) else None
    j2 = bisect.bisect_left(maxv, tgt - 1e-12)
    bt = maxi[j2] if j2 < len(maxi) else None
    if bs is not None and (bt is None or bs <= bt):
        return -kk, "stop"
    if bt is not None:
        return tgt, "target"
    return endc, "mark"


def _mean(v):
    return (sum(v) / len(v)) if v else None


def price_space(ents, kk, target_mode="A"):
    """Price-space gross G(k) in ORIGINAL R units, plus the k-invariant cost."""
    g = []
    ex = {"stop": 0, "target": 0, "mark": 0}
    for e in ents:
        ro, x = walk_k(e, kk, target_mode)
        g.append(ro)
        ex[x] += 1
    n = len(ents)
    c_all = _mean([e["sp"] + e["cm"] + e["sww"] + e["sl"] for e in ents])
    c73 = _mean([e["sp"] / 7.3 + e["cm"] + e["sww"] + e["sl"] for e in ents])
    c85 = _mean([e["sp"] / 8.5 + e["cm"] + e["sww"] + e["sl"] for e in ents])
    G = _mean(g)
    return {
        "k": (None if kk >= INF_K else round(kk, 4)), "n": n,
        "G_price": round(G, 6),
        "C_frozen": round(c_all, 6), "C_sp73": round(c73, 6), "C_sp85": round(c85, 6),
        "gap_frozen": round(G - c_all, 6), "gap_sp73": round(G - c73, 6),
        "gap_sp85": round(G - c85, 6),
        "net_new_frozen": round((G - c_all) / kk, 6) if kk < INF_K else 0.0,
        "net_new_sp73": round((G - c73) / kk, 6) if kk < INF_K else 0.0,
        "stop_pct": round(100 * ex["stop"] / n, 3), "target_pct": round(100 * ex["target"] / n, 3),
        "mark_pct": round(100 * ex["mark"] / n, 3),
        "win_pct": round(100 * sum(1 for x in g if x > 0) / n, 3),
    }


def rule_eval(ents, kf, label, target_mode="A", trail=None):
    """Per-row k_i rule, priced exactly as l2 priced it (slippage held flat) AND
    with slippage divided (the physical reading)."""
    gr = []
    nf = []
    n73 = []
    nf_phys = []
    n73_phys = []
    ks = []
    ex = {"stop": 0, "target": 0, "mark": 0}
    for e in ents:
        kk = kf(e)
        if kk is None or kk < 1e-9:
            continue
        ro, x = walk_k(e, kk, target_mode)
        ex[x] += 1
        ks.append(kk)
        gr.append(ro / kk)
        cp = e["sp"] + e["cm"] + e["sww"]
        cp73 = e["sp"] / 7.3 + e["cm"] + e["sww"]
        nf.append(ro / kk - (cp / kk + e["sl"]))
        n73.append(ro / kk - (cp73 / kk + e["sl"]))
        nf_phys.append((ro - cp - e["sl"]) / kk)
        n73_phys.append((ro - cp73 - e["sl"]) / kk)
    if not ks:
        return {"rule": label, "n_eval": 0}
    n = len(ks)
    return {
        "rule": label, "n_eval": n, "k_mean": round(_mean(ks), 4),
        "k_median": round(sorted(ks)[n // 2], 4),
        "share_k_gt_1_pct": round(100 * sum(1 for x in ks if x > 1.000001) / n, 3),
        "gross_newunit": round(_mean(gr), 6),
        "win_pct": round(100 * sum(1 for x in gr if x > 0) / n, 3),
        "stop_pct": round(100 * ex["stop"] / n, 3), "target_pct": round(100 * ex["target"] / n, 3),
        "mark_pct": round(100 * ex["mark"] / n, 3),
        "net_frozen": round(_mean(nf), 6), "net_sp73": round(_mean(n73), 6),
        "net_frozen_physslip": round(_mean(nf_phys), 6),
        "net_sp73_physslip": round(_mean(n73_phys), 6),
    }
