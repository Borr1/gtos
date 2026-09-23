#!/usr/bin/env python3
"""x4 — INTRA-BAR feature builder.

Nobody has ever looked INSIDE the M15 bar the decision is made on. Every one of the 28 fields
l3 ranked (max |d| = 0.152) is computed AT the close. This builds the M1 composition of that
bar and of the minute AFTER it.

ALIGNMENT (verified, see x4_RESULT.md S1):
  decision at T  ->  decision M15 bar is labelled T-15m and spans M1 bars T-15 .. T-1.
  Its CLOSE == entry_price exactly on 82.5 % of rows.
  The path sidecar's bar 1 is T+1m, so the minute [T, T+1m) is UNOBSERVED by every prior lane.

FEATURE CLASSES (stamped in the output):
  PRE      strictly M1 bars with time < T. Legal for an order placed AT T.
  CONFIRM  the single M1 bar labelled T, i.e. [T, T+1m). Legal ONLY for an order placed at
           T+1m or later -- which is exactly the delay L7 already priced at +0.0670 R/trade.

Sign convention matches w0_ws: fav(price) = s*(price-entry)/risk_distance, s=+1 LONG / -1 SHORT.
"""
from __future__ import annotations
import bisect, csv, gzip, json, math, os, sys
from datetime import datetime, timezone

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws

BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/"
        "cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
M1DIRS = ["bridge_ftmo_m1_202512", "bridge_ftmo_m1_202601", "bridge_ftmo_m1_202602"]
OUT = os.path.join(D, "x4_INTRABAR_V1.jsonl.gz")


def ep(s):
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


def load_m1(sym):
    """Concatenate the monthly M1 files for one symbol; return sorted parallel arrays."""
    t, o, h, l, c, v = [], [], [], [], [], []
    for dd in M1DIRS:
        p = os.path.join(BARS, dd, "%s_M1.csv" % sym)
        if not os.path.isfile(p):
            continue
        with open(p, newline="") as fh:
            rd = csv.reader(fh)
            next(rd, None)
            for row in rd:
                t.append(ep(row[0])); o.append(float(row[1])); h.append(float(row[2]))
                l.append(float(row[3])); c.append(float(row[4])); v.append(float(row[5]))
    order = sorted(range(len(t)), key=lambda i: t[i])
    return ([t[i] for i in order], [o[i] for i in order], [h[i] for i in order],
            [l[i] for i in order], [c[i] for i in order], [v[i] for i in order])


def rng(T0, T1, times):
    """indices of bars with T0 <= time < T1"""
    return bisect.bisect_left(times, T0), bisect.bisect_left(times, T1)


def safe(a, b, default=None):
    return a / b if b not in (0, 0.0, None) and b == b else default


def feats(row, M):
    times, O, H, L, C, V = M
    T = ep(row["decision_time_utc"])
    e = float(row["entry_price"]); d = float(row["risk_distance"])
    s = 1.0 if row["side"] == "LONG" else -1.0
    if d <= 0:
        return None
    fav = lambda p: s * (p - e) / d

    i0, i1 = rng(T - 900, T, times)          # the decision bar's M1 constituents
    n = i1 - i0
    if n < 5:
        return None                           # too thin to characterise
    o = O[i0:i1]; hi = H[i0:i1]; lo = L[i0:i1]; cl = C[i0:i1]; vv = V[i0:i1]
    tt = times[i0:i1]

    F = {"candidate_id": row["candidate_id"], "decision_time_utc": row["decision_time_utc"],
         "n_m1_in_bar": n}

    # ---------------- whole-bar geometry, oriented to the trade's own side ----------------
    bo = o[0]; bc = cl[-1]
    bh = max(hi); bl = min(lo)
    favext = bh if s > 0 else bl        # favourable extreme
    advext = bl if s > 0 else bh
    brange = bh - bl
    F["bar_range_r"] = brange / d
    F["bar_ret_r"] = s * (bc - bo) / d
    F["bar_fav_ext_r"] = s * (favext - bo) / d
    F["bar_adv_ext_r"] = s * (advext - bo) / d
    F["clv_fav"] = (s * (bc - bl) / brange) if brange > 0 else 0.5
    if s < 0:
        F["clv_fav"] = ((bh - bc) / brange) if brange > 0 else 0.5
    # retrace from the favourable extreme by the close, as a fraction of the bar's range
    F["retrace_from_fav"] = (abs(favext - bc) / brange) if brange > 0 else 0.0
    F["wick_beyond_close_fav_r"] = abs(favext - bc) / d
    F["wick_adv_r"] = abs(advext - bo) / d if s > 0 else abs(advext - bo) / d

    # ---------------- WHERE in the bar the move happened ----------------
    kf = (hi.index(bh) if s > 0 else lo.index(bl))
    ka = (lo.index(bl) if s > 0 else hi.index(bh))
    F["argmax_fav_pos"] = kf / (n - 1) if n > 1 else 0.5
    F["argmax_adv_pos"] = ka / (n - 1) if n > 1 else 0.5
    F["fav_after_adv"] = 1.0 if kf > ka else 0.0
    mrng = [hi[i] - lo[i] for i in range(n)]
    kr = mrng.index(max(mrng))
    F["argmax_range_pos"] = kr / (n - 1) if n > 1 else 0.5
    F["max_min_range_r"] = max(mrng) / d
    F["max_min_range_share"] = safe(max(mrng), sum(mrng), 0.0)

    # ---------------- trend vs retrace ----------------
    mret = [s * (cl[i] - o[i]) for i in range(n)]
    up = sum(1 for x in mret if x > 0); dn = sum(1 for x in mret if x < 0)
    F["up_min_frac"] = up / n
    F["net_min_frac"] = (up - dn) / n
    flips = 0; run = 0; bestf = 0; besta = 0; cur = 0
    prev = 0
    for x in mret:
        sg = 1 if x > 0 else (-1 if x < 0 else 0)
        if sg != 0 and prev != 0 and sg != prev:
            flips += 1
        if sg == prev and sg != 0:
            cur += 1
        elif sg != 0:
            cur = 1
        else:
            cur = 0
        if sg > 0:
            bestf = max(bestf, cur)
        elif sg < 0:
            besta = max(besta, cur)
        if sg != 0:
            prev = sg
    F["n_dir_flips"] = flips
    F["max_run_fav"] = bestf
    F["max_run_adv"] = besta
    F["max_run_diff"] = bestf - besta
    # directional efficiency: net displacement over summed absolute minute moves
    absmove = sum(abs(cl[i] - o[i]) for i in range(n))
    F["dir_eff"] = safe(abs(bc - bo), absmove, 0.0)
    F["dir_eff_signed"] = safe(s * (bc - bo), absmove, 0.0)
    F["range_eff"] = safe(brange, sum(mrng), 0.0)

    # ---------------- WHEN: early vs late segments ----------------
    def seg(a, b):
        a = max(0, a); b = min(n, b)
        if b <= a:
            return 0.0
        return s * (cl[b - 1] - o[a]) / d
    F["first5_r"] = seg(0, 5)
    F["mid5_r"] = seg(5, 10)
    F["late5_r"] = seg(n - 5, n)
    F["late3_r"] = seg(n - 3, n)
    F["late1_r"] = seg(n - 1, n)
    F["accel_late_minus_first"] = F["late5_r"] - F["first5_r"]
    F["late5_share_of_bar"] = safe(F["late5_r"], F["bar_ret_r"]) if abs(F["bar_ret_r"]) > 1e-9 else None
    # favourable excursion achieved in the last 5 minutes only
    lo5 = min(lo[max(0, n - 5):]); hi5 = max(hi[max(0, n - 5):])
    F["late5_range_r"] = (hi5 - lo5) / d
    F["late5_range_share"] = safe(hi5 - lo5, brange, None)

    # ---------------- volume / participation ----------------
    tv = sum(vv)
    F["bar_volume"] = tv
    F["vol_late3_share"] = safe(sum(vv[max(0, n - 3):]), tv, None)
    F["vol_late5_share"] = safe(sum(vv[max(0, n - 5):]), tv, None)
    F["vol_first5_share"] = safe(sum(vv[:5]), tv, None)
    F["vol_at_fav_min_share"] = safe(vv[kf], tv, None)
    F["vol_at_maxrange_share"] = safe(vv[kr], tv, None)
    mv = tv / n if n else 0.0
    F["vol_late1_ratio"] = safe(vv[-1], mv, None)
    # volume-weighted position of the bar's activity (0 early .. 1 late)
    F["vol_centroid"] = safe(sum(vv[i] * i for i in range(n)), tv * (n - 1)) if n > 1 and tv > 0 else 0.5

    # ---------------- the approach to the entry level ----------------
    ntouch = sum(1 for i in range(n) if lo[i] <= e <= hi[i])
    F["entry_touch_minutes"] = ntouch
    F["entry_touch_frac"] = ntouch / n
    tix = [i for i in range(n) if lo[i] <= e <= hi[i]]
    F["entry_first_touch_pos"] = (tix[0] / (n - 1)) if tix and n > 1 else None
    F["entry_last_touch_pos"] = (tix[-1] / (n - 1)) if tix and n > 1 else None
    F["minutes_since_entry_touch"] = (n - 1 - tix[-1]) if tix else None
    xs = 0; pv = None
    for i in range(n):
        sg = 1 if cl[i] > e else (-1 if cl[i] < e else 0)
        if sg != 0 and pv is not None and sg != pv:
            xs += 1
        if sg != 0:
            pv = sg
    F["entry_close_crossings"] = xs
    F["entry_pos_in_bar"] = ((e - bl) / brange) if brange > 0 else 0.5
    if s < 0:
        F["entry_pos_in_bar"] = ((bh - e) / brange) if brange > 0 else 0.5
    F["mkt_at_bar_close_r"] = fav(bc)
    F["entry_is_bar_close"] = 1.0 if abs(bc - e) < 1e-9 else 0.0

    # ---------------- the stop / target vs what the bar actually does ----------------
    F["stop_dist_over_bar_range"] = safe(d, brange, None)
    F["bar_range_over_stop"] = brange / d
    tgt = float(row.get("policy_target_r") or 2.0)
    F["target_dist_over_bar_range"] = safe(tgt * d, brange, None)
    # would the stop have been inside this bar's own range?
    stop_p = e - s * d
    F["stop_inside_bar"] = 1.0 if bl <= stop_p <= bh else 0.0

    # ---------------- prior context: extension, volatility regime ----------------
    def block(a, b):
        j0, j1 = rng(a, b, times)
        if j1 <= j0:
            return None
        return (O[j0], max(H[j0:j1]), min(L[j0:j1]), C[j1 - 1], sum(V[j0:j1]), j1 - j0)
    trs = []
    for k in range(1, 17):
        b = block(T - 900 * (k + 1), T - 900 * k)
        if b:
            trs.append(b[1] - b[2])
    F["atr16_m15_r"] = (sum(trs) / len(trs) / d) if trs else None
    F["bar_range_over_atr16"] = safe(brange / d, F["atr16_m15_r"], None) if F["atr16_m15_r"] else None
    for k, mins in (("15", 900), ("30", 1800), ("60", 3600), ("240", 14400)):
        b = block(T - mins, T)
        if b:
            F["ret_prior%s_r" % k] = s * (b[3] - b[0]) / d
            F["range_prior%s_r" % k] = (b[1] - b[2]) / d
            hh, ll = b[1], b[2]
            F["pos_in_prior%s_range" % k] = (((bc - ll) / (hh - ll)) if hh > ll else 0.5) if s > 0 \
                else (((hh - bc) / (hh - ll)) if hh > ll else 0.5)
            F["run_from_prior%s_ext_r" % k] = (s * (bc - (ll if s > 0 else hh))) / d
        else:
            for nm in ("ret_prior%s_r", "range_prior%s_r", "pos_in_prior%s_range",
                       "run_from_prior%s_ext_r"):
                F[nm % k] = None
    pb = block(T - 1800, T - 900)
    if pb:
        F["prev_bar_ret_r"] = s * (pb[3] - pb[0]) / d
        F["prev_bar_range_r"] = (pb[1] - pb[2]) / d
        F["range_expansion"] = safe(brange, pb[1] - pb[2], None)
        F["vol_expansion"] = safe(tv, pb[4], None)
        F["gap_from_prev_close_r"] = s * (bo - pb[3]) / d
        F["same_dir_as_prev"] = 1.0 if (F["prev_bar_ret_r"] > 0) == (F["bar_ret_r"] > 0) else 0.0
    else:
        for nm in ("prev_bar_ret_r", "prev_bar_range_r", "range_expansion", "vol_expansion",
                   "gap_from_prev_close_r", "same_dir_as_prev"):
            F[nm] = None
    # consecutive prior M15 bars closing in the trade direction
    ncons = 0
    for k in range(1, 9):
        b = block(T - 900 * (k + 1), T - 900 * k)
        if not b:
            break
        if s * (b[3] - b[0]) > 0:
            ncons += 1
        else:
            break
    F["prior_same_dir_bars"] = ncons

    # ---------------- CONFIRM: the single minute [T, T+1m) ----------------
    j = bisect.bisect_left(times, T)
    if j < len(times) and times[j] == T:
        F["c0_present"] = 1
        F["c0_ret_r"] = s * (C[j] - O[j]) / d
        F["c0_fav_r"] = fav(H[j] if s > 0 else L[j])
        F["c0_adv_r"] = fav(L[j] if s > 0 else H[j])
        F["c0_close_fav_r"] = fav(C[j])
        F["c0_range_r"] = (H[j] - L[j]) / d
        F["c0_vol_ratio"] = safe(V[j], mv, None)
        F["c0_touch_entry"] = 1.0 if L[j] <= e <= H[j] else 0.0
        F["c0_clv_fav"] = ((C[j] - L[j]) / (H[j] - L[j])) if H[j] > L[j] else 0.5
        if s < 0:
            F["c0_clv_fav"] = ((H[j] - C[j]) / (H[j] - L[j])) if H[j] > L[j] else 0.5
        F["c0_cont_vs_bar"] = 1.0 if (F["c0_ret_r"] > 0) == (F["bar_ret_r"] > 0) else 0.0
    else:
        for nm in ("c0_ret_r", "c0_fav_r", "c0_adv_r", "c0_close_fav_r", "c0_range_r",
                   "c0_vol_ratio", "c0_touch_entry", "c0_clv_fav", "c0_cont_vs_bar"):
            F[nm] = None
        F["c0_present"] = 0
    return F


def main():
    rows = w0_ws.load()
    bysym = {}
    for r in rows:
        bysym.setdefault(r["symbol"], []).append(r)
    nout = 0; nskip = 0
    with gzip.open(OUT, "wt") as fh:
        for sym in sorted(bysym):
            M = load_m1(sym)
            if not M[0]:
                print("NO M1", sym, file=sys.stderr); nskip += len(bysym[sym]); continue
            for r in bysym[sym]:
                F = feats(r, M)
                if F is None:
                    nskip += 1; continue
                fh.write(json.dumps(F) + "\n"); nout += 1
            print("%-12s rows=%5d m1=%d" % (sym, len(bysym[sym]), len(M[0])), flush=True)
    print("WROTE", nout, "SKIPPED", nskip, "->", OUT)


if __name__ == "__main__":
    main()
