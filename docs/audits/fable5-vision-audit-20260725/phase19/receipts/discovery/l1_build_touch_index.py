#!/usr/bin/env python3
"""l1 — build the TOUCH INDEX substrate.

For every candidate with a path, record the first bar index at which each favourable
level and each adverse level is touched, under three fill conventions:

  BLIND    start at bar 0 regardless of whether entry_price was ever traded
           (this is the pool's own convention; W0-F2 shows it manufactures +0.2776 R/trade)
  STRICT   start at the first bar with adv <= 0 (price actually traded at entry_price)
  REAL     start at bar 0 when the order was born at-or-through the market
           (mkt_r_prev_close <= 0, i.e. a market order or an already-marketable limit),
           otherwise STRICT.  This is the honest live contract.

From (tf, ta, n, cls_end) ANY (target, stop) cell is recomputable in O(1), so every
downstream l1 question is a fast pass over this file instead of the 34 MB sidecar.

Emits l1_TOUCH_INDEX_V1.jsonl.gz  (one row per candidate, key = candidate_id+decision_time_utc)
"""
from __future__ import annotations
import gzip, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa

ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
OUT = os.path.join(HERE, "l1_TOUCH_INDEX_V1.jsonl.gz")

FAV = [0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0, 10.0]
ADV = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]

WS_COLS = ["candidate_id", "decision_time_utc", "origin_family", "symbol", "side",
           "utc_hour_bucket", "session_bucket", "route_session", "gross_r", "cost_r",
           "spread_r", "commission_r", "swap_cost_r", "expected_slippage_r",
           "is_first_emission", "setup_dup_count", "risk_distance", "entry_price",
           "risk_per_trade_pct", "final_blocker_class", "decision_timeframe",
           "mfe_r", "mae_r", "which_came_first", "policy_target_r"]


def first_touch(vals, start, levels, sign):
    """vals[start:] monotone-running extremum; return first index >= start reaching each level.
    sign=+1 -> running max vs +level ; sign=-1 -> running min vs -level."""
    out = [None] * len(levels)
    p = 0
    if sign > 0:
        run = -1e18
        for i in range(start, len(vals)):
            v = vals[i]
            if v > run:
                run = v
                while p < len(levels) and run >= levels[p] - 1e-12:
                    out[p] = i
                    p += 1
                if p >= len(levels):
                    break
    else:
        run = 1e18
        for i in range(start, len(vals)):
            v = vals[i]
            if v < run:
                run = v
                while p < len(levels) and run <= -levels[p] + 1e-12:
                    out[p] = i
                    p += 1
                if p >= len(levels):
                    break
    return out


def main():
    t0 = time.time()
    ws = {}
    for r in w0_ws.iter_rows():
        ws[(r["candidate_id"], r["decision_time_utc"])] = {k: r.get(k) for k in WS_COLS}
    anch = {}
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if line.strip():
                a = json.loads(line)
                anch[(a["candidate_id"], a["decision_time_utc"])] = a.get("mkt_r_prev_close")
    sys.stderr.write("ws=%d anchor=%d %.1fs\n" % (len(ws), len(anch), time.time() - t0))

    n_out = 0
    miss_anchor = 0
    with gzip.open(OUT, "wt") as out:
        for rp in w0_ws.iter_rpaths():
            k = (rp["candidate_id"], rp["decision_time_utc"])
            w = ws.get(k)
            if w is None:
                continue
            fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
            n = len(fav)
            m = anch.get(k)
            if m is None:
                miss_anchor += 1
            born = None
            if m is not None:
                born = ("born_past_stop" if m <= -1.0 else
                        "born_marketable" if m < 0.0 else
                        "born_at_limit" if m == 0.0 else "born_resting")
            s_strict = next((i for i in range(n) if adv[i] <= 1e-12), None)
            s_real = 0 if (m is not None and m <= 1e-12) else s_strict
            rec = {
                "candidate_id": k[0], "decision_time_utc": k[1],
                "family": w["origin_family"], "symbol": w["symbol"], "side": w["side"],
                "hour": w["utc_hour_bucket"], "session": w["session_bucket"],
                "route_session": w["route_session"], "tf_decision": w["decision_timeframe"],
                "blocker": w["final_blocker_class"],
                "gross_r": w["gross_r"], "cost_r": w["cost_r"], "spread_r": w["spread_r"],
                "commission_r": w["commission_r"], "swap_r": w["swap_cost_r"],
                "slip_r": w["expected_slippage_r"],
                "first_em": w["is_first_emission"], "dup_n": w["setup_dup_count"],
                "risk_distance": w["risk_distance"], "risk_pct": w["risk_per_trade_pct"],
                "policy_target_r": w["policy_target_r"],
                "mkt_r": m, "born": born,
                "n": n, "cls_end": cls[n - 1],
                "s_strict": s_strict, "s_real": s_real,
            }
            for tag, st in (("b", 0), ("s", s_strict), ("r", s_real)):
                if st is None:
                    rec["tf_" + tag] = None
                    rec["ta_" + tag] = None
                    rec["mfe_" + tag] = None
                    rec["mae_" + tag] = None
                    rec["bmfe_" + tag] = None
                    continue
                rec["tf_" + tag] = first_touch(fav, st, FAV, +1)
                rec["ta_" + tag] = first_touch(adv, st, ADV, -1)
                mx = -1e18
                bmx = None
                mn = 1e18
                for i in range(st, n):
                    if fav[i] > mx:
                        mx = fav[i]
                        bmx = i
                    if adv[i] < mn:
                        mn = adv[i]
                rec["mfe_" + tag] = round(mx, 6)
                rec["mae_" + tag] = round(mn, 6)
                rec["bmfe_" + tag] = bmx
            out.write(json.dumps(rec) + "\n")
            n_out += 1
    sys.stderr.write("wrote %d rows, miss_anchor=%d, %.1fs -> %s\n"
                     % (n_out, miss_anchor, time.time() - t0, OUT))


if __name__ == "__main__":
    main()
