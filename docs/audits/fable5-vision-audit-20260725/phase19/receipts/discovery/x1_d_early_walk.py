"""x1-D — what EARLINESS books, for the 53.9 % of the pool whose entry IS the bar close.

x1-B measured WHEN each predicate first became true inside its own decision bar and what
price was given up by waiting. It never measured the OUTCOME of acting at that minute.
This does, on the M1 source the sidecar itself names, for the five families whose
predicate is exactly reproducible from closed M15 bars (x1-A: stop reproduction 100 %,
worst relative error 0.0).

Arms, all walked on contiguous M1 with the w0 tie rule (stop wins inside a bar):

  A    as-ran         entry = M15 close, stop/target = the generator's, path T+1min..T+120min
  A1   as-ran+1bar    identical but the path starts at T (the M1 bar the sidecar drops)
  E1   early, same container    entry = close of minute k*, generator's stop/target prices
  E2   early, own geometry      entry = close of minute k*, stop = the RUNNING geometry at k*,
                                target = entry +- target_rr * |entry-stop|, R in its own risk
  E2h  E2 with the horizon measured from the fill instead of from the decision

k* = the first minute of the decision bar at which the family's own predicate is true,
computed from bars 0..k only (plus prior closed M15 bars) -- causal, implementable at a
60 s poll.
"""
from __future__ import annotations

import csv
import gzip
import json
import os
import statistics
import sys
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timedelta

ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
DISC = f"{ROOT}/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
WS = f"{DISC}/w0_WORKING_SET.jsonl.gz"
BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
M1DIRS = ["bridge_ftmo_m1_202512", "bridge_ftmo_m1_202601", "bridge_ftmo_m1_202602"]
M15DIR = "bridge_ftmo_m15_20250601_20260610"

FAMS = {"displacement_continuation", "liquidity_sweep_reclaim", "structural_distance_extreme",
        "volatility_compression_expansion", "regime_transition_break"}


def load_m1(symbol):
    rows, seen = [], set()
    for d in M1DIRS:
        p = f"{BARS}/{d}/{symbol}_M1.csv"
        if not os.path.exists(p):
            continue
        with open(p, newline="") as f:
            rd = csv.reader(f); next(rd)
            for r in rd:
                if r[0] in seen:
                    continue
                seen.add(r[0])
                rows.append((r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4])))
    rows.sort(key=lambda x: x[0])
    return [x[0] for x in rows], rows


def load_m15(symbol):
    p = f"{BARS}/{M15DIR}/{symbol}_M15.csv"
    out = []
    if not os.path.exists(p):
        return [], {}
    with open(p, newline="") as f:
        rd = csv.reader(f); next(rd)
        for r in rd:
            out.append((r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4])))
    out.sort(key=lambda x: x[0])
    return out, {t[0]: i for i, t in enumerate(out)}


def walk(bars, side, entry, stop, tp):
    """First-touch walk. Returns (r_in_own_risk, reason, bar_index)."""
    d = abs(entry - stop)
    if d <= 0 or not bars:
        return None, "no_risk", None
    for i, b in enumerate(bars):
        _, o, h, l, c = b
        if side == "LONG":
            hit_stop, hit_tp = l <= stop, h >= tp
        else:
            hit_stop, hit_tp = h >= stop, l <= tp
        if hit_stop:                      # tie rule: stop wins
            return -1.0, "stop", i
        if hit_tp:
            return (abs(tp - entry) / d), "target", i
    c = bars[-1][4]
    r = (c - entry) / d if side == "LONG" else (entry - c) / d
    return r, "path_end", len(bars) - 1


def summ(v):
    v = [x for x in v if x is not None]
    if not v:
        return None
    return {"n": len(v), "mean": round(statistics.fmean(v), 6),
            "sum": round(sum(v), 4), "median": round(statistics.median(v), 6),
            "stdev": round(statistics.pstdev(v), 6) if len(v) > 1 else 0.0}


def main():
    rows = []
    with gzip.open(WS, "rt") as f:
        for line in f:
            r = json.loads(line)
            if r["origin_family"] in FAMS:
                rows.append(r)
    by_sym = defaultdict(list)
    for r in rows:
        by_sym[r["symbol"]].append(r)
    sys.stderr.write(f"rows={len(rows)}\n")

    out = []
    diag = defaultdict(int)
    for sym in sorted(by_sym):
        m1t, m1 = load_m1(sym)
        ser, spos = load_m15(sym)
        if not m1 or not ser:
            diag["no_source"] += len(by_sym[sym]); continue
        for r in by_sym[sym]:
            T = datetime.fromisoformat(r["decision_time_utc"])
            Topen = T - timedelta(minutes=15)
            i = spos.get(Topen.isoformat())
            if i is None or i < 50:
                diag["no_decision_bar"] += 1; continue
            lo = bisect_left(m1t, Topen.isoformat()); hi = bisect_left(m1t, T.isoformat())
            win = m1[lo:hi]
            if not win:
                diag["no_m1"] += 1; continue
            end = bisect_left(m1t, (T + timedelta(minutes=121)).isoformat())
            fwd_from_T1 = m1[bisect_left(m1t, (T + timedelta(minutes=1)).isoformat()):end]
            fwd_from_T = m1[bisect_left(m1t, T.isoformat()):end]

            fam = r["origin_family"]; side = r["side"]
            trr = float(r["policy_target_r"] or 2.0)
            e0 = float(r["entry_price"]); s0 = float(r["stop_loss"]); t0 = float(r["take_profit_1"])
            d0 = float(r["risk_distance"])

            # prior-bar (closed before this bar) quantities
            prev_rng = [b[2] - b[3] for b in ser[i - 49:i]]          # 49 prior ranges
            ph20 = max(b[2] for b in ser[i - 20:i]); pl20 = min(b[3] for b in ser[i - 20:i])
            ph50p = max(b[2] for b in ser[i - 49:i]); pl50p = min(b[3] for b in ser[i - 49:i])
            c_20back = ser[i - 20][4]
            # prior-bar atr for volatility_compression_expansion gate (index-1, full bars)
            pa14 = sum(b[2] - b[3] for b in ser[i - 14:i]) / 14.0
            pa50 = sum(b[2] - b[3] for b in ser[i - 50:i]) / 50.0
            prior_ratio = pa14 / pa50 if pa50 > 0 else None
            prev_trend_atr50 = sum(b[2] - b[3] for b in ser[i - 50:i]) / 50.0
            sc = (ser[i - 1][4] - ser[i - 21][4]) / prev_trend_atr50 if prev_trend_atr50 > 0 else 0.0
            prev_trend = ("strong_up" if sc >= 2 else "up" if sc >= .75 else
                          "strong_down" if sc <= -2 else "down" if sc <= -.75 else "flat")

            o0 = win[0][1]
            rh = -1e300; rl = 1e300
            kstar = None; e_k = s_k = None; side_k = None
            for k in range(len(win)):
                _, _, h, l, c = win[k]
                rh = max(rh, h); rl = min(rl, l)
                a14 = (sum(prev_rng[-13:]) + (rh - rl)) / 14.0
                a50 = (sum(prev_rng) + (rh - rl)) / 50.0
                if a14 <= 0:
                    continue
                rr_ = (rh - rl) / a14
                hit = None
                if fam == "displacement_continuation":
                    if rr_ >= 1.5 and abs(c - o0) / a14 >= 0.75:
                        sd = "LONG" if c > o0 else "SHORT"
                        st = rl - .25 * a14 if sd == "LONG" else rh + .25 * a14
                        hit = (sd, st)
                elif fam == "liquidity_sweep_reclaim":
                    sh = rh > ph20 and c < ph20
                    sl = rl < pl20 and c > pl20
                    if sh and not sl:
                        hit = ("SHORT", rh + .25 * a14)
                    elif sl and not sh:
                        hit = ("LONG", rl - .25 * a14)
                elif fam == "structural_distance_extreme":
                    h50 = max(ph50p, rh); l50 = min(pl50p, rl)
                    if h50 > l50:
                        pos = (c - l50) / (h50 - l50)
                        if pos >= .97:
                            hit = ("SHORT", rh + .25 * a14)
                        elif pos <= .03:
                            hit = ("LONG", rl - .25 * a14)
                elif fam == "volatility_compression_expansion":
                    if prior_ratio is not None and prior_ratio <= .75 and rr_ >= 1.25:
                        if c > ph20:
                            hit = ("LONG", min(rl, pl20) - .20 * a14)
                        elif c < pl20:
                            hit = ("SHORT", max(rh, ph20) + .20 * a14)
                elif fam == "regime_transition_break":
                    tsc = (c - c_20back) / a50 if a50 > 0 else 0.0
                    tr = ("strong_up" if tsc >= 2 else "up" if tsc >= .75 else
                          "strong_down" if tsc <= -2 else "down" if tsc <= -.75 else "flat")
                    if tr == "strong_up" and prev_trend not in {"strong_up", "up"} and c > ph20:
                        hit = ("LONG", pl20 - .10 * a14)
                    elif tr == "strong_down" and prev_trend not in {"strong_down", "down"} and c < pl20:
                        hit = ("SHORT", ph20 + .10 * a14)
                if hit is not None:
                    kstar, side_k, s_k = k, hit[0], hit[1]
                    e_k = c
                    break
            rec = {"candidate_id": r["candidate_id"], "decision_time_utc": r["decision_time_utc"],
                   "symbol": sym, "origin_family": fam, "side": side, "kstar": kstar,
                   "side_k": side_k, "n_m1": len(win), "cost_r": r.get("cost_r"),
                   "gross_r": r.get("gross_r"), "risk_distance": d0}
            # ARM A / A1
            ra, rsn, _ = walk(fwd_from_T1, side, e0, s0, t0)
            rec["A_r"], rec["A_reason"] = ra, rsn
            ra1, rsn1, _ = walk(fwd_from_T, side, e0, s0, t0)
            rec["A1_r"], rec["A1_reason"] = ra1, rsn1
            if kstar is not None and side_k == side and e_k is not None:
                tail = win[kstar + 1:] + fwd_from_T
                r1, rn1, _ = walk(tail, side, e_k, s0, t0)
                rec["E1_r"], rec["E1_reason"] = r1, rn1
                rec["E1_r_in_orig_risk"] = (
                    None if r1 is None else round(r1 * abs(e_k - s0) / d0, 6))
                dk = abs(e_k - s_k)
                tk = e_k + trr * dk if side == "LONG" else e_k - trr * dk
                r2, rn2, _ = walk(tail, side, e_k, s_k, tk)
                rec["E2_r"], rec["E2_reason"] = r2, rn2
                rec["E2_risk_ratio"] = round(dk / d0, 6) if d0 > 0 else None
                tail_h = win[kstar + 1:] + m1[
                    bisect_left(m1t, T.isoformat()):
                    bisect_left(m1t, (T + timedelta(minutes=121 - (14 - kstar))).isoformat())]
                # horizon measured from the fill: 120 minutes after the entry minute
                fill_end = bisect_left(
                    m1t, (Topen + timedelta(minutes=kstar + 121)).isoformat())
                tail_f = win[kstar + 1:] + m1[bisect_left(m1t, T.isoformat()):fill_end]
                r2h, rn2h, _ = walk(tail_f, side, e_k, s_k, tk)
                rec["E2h_r"], rec["E2h_reason"] = r2h, rn2h
                rec["entry_k"] = e_k; rec["stop_k"] = s_k
            else:
                diag["no_confirm" if kstar is None else "side_flip"] += 1
            out.append(rec)

    with gzip.open(f"{DISC}/x1_D_EARLYWALK_ROWS_V1.jsonl.gz", "wt") as f:
        for rec in out:
            f.write(json.dumps(rec) + "\n")

    res = {"schema": "gtos.x1.early_walk.v1", "n": len(out), "diag": dict(diag),
           "families": sorted(FAMS), "per_family": {}, "pooled": {}}
    groups = defaultdict(list)
    for rec in out:
        groups[rec["origin_family"]].append(rec)
        groups["ALL_FIVE"].append(rec)
    for g, rs in groups.items():
        ok = [x for x in rs if x.get("E2_r") is not None]
        blk = {
            "n": len(rs), "n_with_confirm_and_side_match": len(ok),
            "kstar": summ([x["kstar"] for x in rs if x["kstar"] is not None]),
            "A_r_all": summ([x["A_r"] for x in rs]),
            "A1_r_all": summ([x["A1_r"] for x in rs]),
            "paired": {
                "A_r": summ([x["A_r"] for x in ok]),
                "E1_r": summ([x["E1_r"] for x in ok]),
                "E1_r_in_orig_risk": summ([x["E1_r_in_orig_risk"] for x in ok]),
                "E2_r": summ([x["E2_r"] for x in ok]),
                "E2h_r": summ([x["E2h_r"] for x in ok]),
                "delta_E1_minus_A": summ([x["E1_r"] - x["A_r"] for x in ok
                                          if x["E1_r"] is not None and x["A_r"] is not None]),
                "delta_E2_minus_A": summ([x["E2_r"] - x["A_r"] for x in ok
                                          if x["E2_r"] is not None and x["A_r"] is not None]),
                "E2_risk_ratio": summ([x["E2_risk_ratio"] for x in ok]),
            },
            "exit_reason_A": dict(sorted(
                {k: sum(1 for x in ok if x["A_reason"] == k)
                 for k in {y["A_reason"] for y in ok}}.items())),
            "exit_reason_E2": dict(sorted(
                {k: sum(1 for x in ok if x["E2_reason"] == k)
                 for k in {y["E2_reason"] for y in ok}}.items())),
        }
        # cost-adjusted: price-denominated costs scale as d_orig / d_new
        net_a, net_e2 = [], []
        for x in ok:
            c = x.get("cost_r")
            if c is None or x["E2_risk_ratio"] in (None, 0):
                continue
            net_a.append(x["A_r"] - c)
            net_e2.append(x["E2_r"] - c / x["E2_risk_ratio"])
        blk["net_A_r"] = summ(net_a)
        blk["net_E2_r_cost_scaled"] = summ(net_e2)
        blk["net_delta_E2_minus_A"] = summ(
            [b - a for a, b in zip(net_a, net_e2)]) if net_a else None
        if g == "ALL_FIVE":
            res["pooled"] = blk
        else:
            res["per_family"][g] = blk
    with open(f"{DISC}/x1_D_EARLYWALK_V1.json", "w") as f:
        json.dump(res, f, indent=1)
    sys.stderr.write(json.dumps({"n": len(out), "diag": dict(diag)}) + "\n")


if __name__ == "__main__":
    main()
