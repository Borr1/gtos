#!/usr/bin/env python3
"""x4 wave-2 intra-bar features. Wave 1 found a coherent direction — CHOPPY bars where the
entry level was worked repeatedly continue; clean directional thrusts revert. Wave 2 builds
the sharper instruments for exactly that mechanism, plus VWAP (a genuinely intra-bar quantity
no M15 close can carry), overlap-based choppiness, and 2-bar structure.

Same timing contract as wave 1: M1 bars stamped T-15 .. T-1 only. Nothing at or after T.
Output: x4_INTRABAR2_V1.jsonl.gz
"""
import bisect, csv, gzip, json, math, os, sys
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws
from x4_build_intrabar import BARS, MONTHS, load_sym, tmin, slice_idx, safediv

OUT = os.path.join(D, "x4_INTRABAR2_V1.jsonl.gz")


def feats2(b, r):
    T = tmin(r["decision_time_utc"])
    e = float(r["entry_price"]); d = float(r["risk_distance"])
    sgn = 1.0 if r["side"] == "LONG" else -1.0
    if d <= 0:
        return {"n2": 0}

    def rr(px):
        return sgn * (px - e) / d

    a, z = slice_idx(b, T - 15, T)
    n = z - a
    f = {"n2": n}
    if n < 2:
        return f
    oo = b["o"][a:z]; hh = b["h"][a:z]; ll = b["l"][a:z]; cc = b["c"][a:z]; vv = b["v"][a:z]
    O = oo[0]; C = cc[-1]; H = max(hh); L = min(ll); rng = H - L

    # ---- thrust / concentration -------------------------------------------
    bodies = [sgn * (cc[i] - oo[i]) / d for i in range(n)]
    ranges = [(hh[i] - ll[i]) / d for i in range(n)]
    f["thrust_max_body_R"] = max(bodies, key=abs)
    f["thrust_max_range_R"] = max(ranges)
    f["thrust_body_share"] = safediv(abs(max(bodies, key=abs)), sum(abs(x) for x in bodies))
    f["thrust_range_share"] = safediv(max(ranges), sum(ranges))
    f["max_range_over_bar"] = safediv(max(ranges) * d, rng)

    # ---- overlap-based choppiness (rigorous): mean pairwise overlap -------
    ov = []
    for i in range(1, n):
        lo = max(ll[i], ll[i - 1]); hi = min(hh[i], hh[i - 1])
        u = max(hh[i], hh[i - 1]) - min(ll[i], ll[i - 1])
        ov.append(max(0.0, hi - lo) / u if u > 0 else 1.0)
    f["overlap_frac"] = sum(ov) / len(ov) if ov else None
    # how many M1 bars extended the bar's extreme in the trade direction
    ext = 0; cur = (hh[0] if sgn > 0 else ll[0])
    for i in range(1, n):
        p = hh[i] if sgn > 0 else ll[i]
        if (p > cur) if sgn > 0 else (p < cur):
            ext += 1; cur = p
    f["n_new_fav_extreme"] = ext
    ext2 = 0; cur = (ll[0] if sgn > 0 else hh[0])
    for i in range(1, n):
        p = ll[i] if sgn > 0 else hh[i]
        if (p < cur) if sgn > 0 else (p > cur):
            ext2 += 1; cur = p
    f["n_new_adv_extreme"] = ext2
    f["extreme_balance"] = ext - ext2

    # ---- VWAP: a genuinely intra-bar quantity -------------------------------
    tv = sum(vv)
    if tv > 0:
        vwap = sum(((hh[i] + ll[i] + cc[i]) / 3.0) * vv[i] for i in range(n)) / tv
    else:
        vwap = sum((hh[i] + ll[i] + cc[i]) / 3.0 for i in range(n)) / n
    f["close_vs_vwap_R"] = sgn * (C - vwap) / d
    f["entry_vs_vwap_R"] = sgn * (e - vwap) / d
    f["vwap_pos_side"] = safediv((vwap - L) if sgn > 0 else (H - vwap), rng)
    # dispersion of price around vwap, volume weighted
    if tv > 0:
        var = sum(vv[i] * (((hh[i] + ll[i] + cc[i]) / 3.0) - vwap) ** 2 for i in range(n)) / tv
        f["vwap_disp_R"] = math.sqrt(var) / d
    else:
        f["vwap_disp_R"] = None

    # ---- time spent relative to the entry level -----------------------------
    f["frac_close_fav_of_entry"] = sum(1 for c in cc if sgn * (c - e) > 0) / n
    f["frac_m1_spanning_entry"] = sum(1 for i in range(n) if ll[i] <= e <= hh[i]) / n
    f["frac_m1_beyond_entry"] = sum(1 for i in range(n)
                                    if (ll[i] > e if sgn > 0 else hh[i] < e)) / n
    f["entry_dwell_010R"] = sum(1 for c in cc if abs(c - e) / d <= 0.10) / n
    f["entry_dwell_025R"] = sum(1 for c in cc if abs(c - e) / d <= 0.25) / n

    # ---- rejection wicks on the M1 series ------------------------------------
    wf = []; wa = []
    for i in range(n):
        rg = hh[i] - ll[i]
        if rg <= 0:
            continue
        wf.append((((hh[i] - max(oo[i], cc[i])) if sgn > 0 else (min(oo[i], cc[i]) - ll[i])) / rg))
        wa.append((((min(oo[i], cc[i]) - ll[i]) if sgn > 0 else (hh[i] - max(oo[i], cc[i]))) / rg))
    f["m1_wick_fav_mean"] = sum(wf) / len(wf) if wf else None
    f["m1_wick_adv_mean"] = sum(wa) / len(wa) if wa else None
    f["m1_wick_balance"] = ((f["m1_wick_adv_mean"] - f["m1_wick_fav_mean"])
                            if wf and wa else None)
    f["n_zero_vol_m1"] = sum(1 for x in vv if x == 0)
    f["mean_vol_per_m1"] = tv / n

    # ---- late reversal against the bar's own body ------------------------------
    body = sgn * (C - O) / d
    last3 = sgn * (C - cc[-4]) / d if n >= 4 else body
    f["late_reversal"] = 1 if (body * last3 < 0) else 0
    f["late_vs_body"] = safediv(last3, abs(body)) if body != 0 else None

    # ---- 2-bar structure: the PREVIOUS M15 bar --------------------------------
    a1, z1 = slice_idx(b, T - 30, T - 15)
    if z1 - a1 >= 2:
        O1 = b["o"][a1]; C1 = b["c"][z1 - 1]
        H1 = max(b["h"][a1:z1]); L1 = min(b["l"][a1:z1])
        f["prev_bar_body_R"] = sgn * (C1 - O1) / d
        f["prev_bar_range_R"] = (H1 - L1) / d
        f["bar_reverses_prev"] = 1 if (sgn * (C - O)) * (sgn * (C1 - O1)) < 0 else 0
        f["range_expansion_2bar"] = safediv(rng, H1 - L1)
        f["inside_bar"] = 1 if (H <= H1 and L >= L1) else 0
        f["outside_bar"] = 1 if (H >= H1 and L <= L1) else 0
        f["two_bar_thrust_R"] = sgn * (C - O1) / d
    else:
        for k in ("prev_bar_body_R", "prev_bar_range_R", "bar_reverses_prev",
                  "range_expansion_2bar", "inside_bar", "outside_bar", "two_bar_thrust_R"):
            f[k] = None

    # ---- how many M1 bars had ANY move at all (dead-tape detector) -------------
    f["frac_m1_flat"] = sum(1 for i in range(n) if hh[i] == ll[i]) / n
    return f


def main():
    rows = w0_ws.load()
    cache = {s: load_sym(s) for s in sorted({r["symbol"] for r in rows})}
    nb = 0
    with gzip.open(OUT, "wt") as fh:
        for r in rows:
            f = feats2(cache[r["symbol"]], r)
            if f.get("n2", 0) < 2:
                nb += 1
            f["candidate_id"] = r["candidate_id"]; f["decision_time_utc"] = r["decision_time_utc"]
            fh.write(json.dumps(f) + "\n")
    print(json.dumps({"rows": len(rows), "too_few_bars": nb, "out": OUT}))


if __name__ == "__main__":
    main()
