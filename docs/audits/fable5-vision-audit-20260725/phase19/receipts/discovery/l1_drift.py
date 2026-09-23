#!/usr/bin/env python3
"""l1 pass 5 — THE DRIFT TEST.  No stopping rule at all.

If the path from entry is a martingale, E[R_tau] = 0 for EVERY bounded stopping time, so
no target/stop/trail/partial can create value and the entire exit surface must collapse
onto the drift.  The clean instrument is the unconditional mean R at a FIXED horizon:
mark-to-market at bar k with no exit logic whatsoever.

Measures mean R at bars 5/15/30/60/120 pool-wide and per stratum, on the TAKEABLE
population under the REAL fill convention, plus the same for the paths' own bar arrays so
the horizon curve can be read at 1-minute resolution.
"""
from __future__ import annotations
import gzip, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import w0_ws  # noqa
from l1_lib import load, mean, q, stats, TOUCH  # noqa

OUT = os.path.join(HERE, "l1_DRIFT_V1.json")
MARKS = [1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 90, 120]


def se(xs):
    xs = list(xs)
    n = len(xs)
    if n < 2:
        return None
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    return (v / n) ** 0.5


def main():
    meta = {}
    for r in load(TOUCH):
        meta[(r["candidate_id"], r["decision_time_utc"])] = r
    # accumulate mark-to-market R at each horizon, per stratum
    keys = ("POOL", "family", "symbol", "hour", "session", "side", "born", "family_side")
    acc = {k: {} for k in keys}
    n_used = 0
    for rp in w0_ws.iter_rpaths():
        k = (rp["candidate_id"], rp["decision_time_utc"])
        m = meta.get(k)
        if m is None or m["born"] == "born_past_stop":
            continue
        st = m["s_real"]
        if st is None:
            continue
        cls = rp["cls"]
        n = len(cls)
        vals = []
        for b in MARKS:
            i = st + b - 1
            vals.append(cls[i] if i < n else cls[n - 1])
        n_used += 1
        strata = {"POOL": "POOL", "family": m["family"], "symbol": m["symbol"],
                  "hour": str(m["hour"]) if m["hour"] is not None else "NA",
                  "session": m["session"], "side": m["side"], "born": m["born"],
                  "family_side": "%s|%s" % (m["family"], m["side"])}
        for gk, gv in strata.items():
            d = acc[gk].setdefault(str(gv), [[0.0] * len(MARKS), 0, [[] for _ in MARKS]])
            for j, v in enumerate(vals):
                d[0][j] += v
                if gk in ("POOL", "family", "side", "session", "born"):
                    d[2][j].append(v)
            d[1] += 1
    res = {"population": "TAKEABLE (ex born_past_stop), fill REAL", "n": n_used, "marks_bars": MARKS,
           "note": "mark-to-market close R at bar k after the fill bar; NO exit logic. "
                   "A martingale gives 0 at every k, so any nonzero level is drift."}
    for gk in keys:
        out = {}
        for gv, d in acc[gk].items():
            if d[1] < 25:
                continue
            row = {"n": d[1], "mean_R_at_bar": {str(MARKS[j]): round(d[0][j] / d[1], 6) for j in range(len(MARKS))}}
            if d[2][0]:
                row["se_at_120"] = round(se(d[2][-1]) or 0.0, 6)
                row["t_at_120"] = round((d[0][-1] / d[1]) / (se(d[2][-1]) or 1e9), 3)
                row["median_R_at_120"] = round(q(d[2][-1], .5), 6)
                row["share_pos_at_120"] = round(sum(1 for x in d[2][-1] if x > 0) / d[1], 6)
            out[gv] = row
        res[gk] = out
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    p = res["POOL"]["POOL"]
    print("POOL n=%d  mean mark-to-market R by bar:" % p["n"])
    print("  " + "  ".join("b%d=%+.4f" % (b, p["mean_R_at_bar"][str(b)]) for b in MARKS))
    print("  se@120=%.4f t=%.2f median@120=%+.4f share_pos=%.4f"
          % (p["se_at_120"], p["t_at_120"], p["median_R_at_120"], p["share_pos_at_120"]))
    for gk in ("family", "side", "born", "session"):
        print("--- %s (mean R at bar 120, then 30) ---" % gk)
        for gv, d in sorted(res[gk].items(), key=lambda kv: -kv[1]["mean_R_at_bar"]["120"]):
            print("  %-32s n%6d b120 %+.4f b30 %+.4f b5 %+.4f%s"
                  % (gv[:32], d["n"], d["mean_R_at_bar"]["120"], d["mean_R_at_bar"]["30"],
                     d["mean_R_at_bar"]["5"], ("  t=%.2f" % d["t_at_120"]) if "t_at_120" in d else ""))
    print("--- top/bottom 8 symbols by b120 ---")
    ss = sorted(res["symbol"].items(), key=lambda kv: -kv[1]["mean_R_at_bar"]["120"])
    for gv, d in ss[:8] + ss[-8:]:
        print("  %-12s n%6d b120 %+.4f b30 %+.4f" % (gv, d["n"], d["mean_R_at_bar"]["120"], d["mean_R_at_bar"]["30"]))
    print("--- top/bottom 6 hours by b120 ---")
    hh = sorted(res["hour"].items(), key=lambda kv: -kv[1]["mean_R_at_bar"]["120"])
    for gv, d in hh[:6] + hh[-6:]:
        print("  h%-4s n%6d b120 %+.4f b30 %+.4f" % (gv, d["n"], d["mean_R_at_bar"]["120"], d["mean_R_at_bar"]["30"]))


if __name__ == "__main__":
    main()
