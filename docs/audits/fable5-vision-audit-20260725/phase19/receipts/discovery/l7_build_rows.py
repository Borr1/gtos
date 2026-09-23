#!/usr/bin/env python3
"""l7 lane pass 1 — build the inversion substrate.

For every one of the 27,658 January candidates, walk BOTH directions under one
identical, fill-honest, no-look-ahead contract:

  FORWARD  entry E, stop -1R, target policy_target_r
  INVERSE  entry E, stop +1R (original units), target -2R (original units)

The inverse R path is the exact reflection of the original:
    fav_i = -adv   adv_i = -fav   cls_i = -cls   m_i = -m
so R units, risk distance and therefore R-denominated costs are identical between
the two directions and the comparison needs no rescaling.

FILL RULE (same for both directions), using the CLEAN no-look-ahead decision-instant
market offset m = mkt_r_prev_close from w0cap2_DECISION_ANCHOR_V1.jsonl.gz (the close of
the M1 bar that CLOSES at the decision minute; bars are open-stamped, so the bar stamped
at the decision minute is entirely post-decision -- see w0-capture_RESULT.md sec 0.1):

    m <= -1.0  born_past_stop  -> order is stopped before it can be worked; r = -1.0,
                                  excluded from the takeable book
    -1 < m < 0 born_marketable -> fills immediately (at a price BETTER than E; we book E,
                                  which is conservative)
    m == 0     born_at_limit   -> fills immediately
    m > 0      born_resting    -> genuine passive limit; requires the path to trade at E
                                  (adv <= 0) before the walk starts; never traded = no_fill

Conservative tie rule inside a bar: stop wins over target.

Writes l7_ROWS_V1.jsonl.gz (one scalar row per candidate) — every downstream cell
aggregation reads that, never the paths.
"""
from __future__ import annotations
import gzip, json, os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402

ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
OUT = os.path.join(HERE, "l7_ROWS_V1.jsonl.gz")

EPS = 1e-12


def born(m):
    if m is None:
        return "born_unanchored"
    if m <= -1.0:
        return "born_past_stop"
    if m < 0.0:
        return "born_marketable"
    if m == 0.0:
        return "born_at_limit"
    return "born_resting"


def walk(fav, adv, cls, m, target_r, stop_r=-1.0, max_bars=None):
    """Honest first-touch walk with the born-state fill rule. Returns dict."""
    n = len(fav)
    b = born(m)
    if b == "born_past_stop":
        return {"r": stop_r, "reason": "born_past_stop", "bar": 0, "filled": True,
                "born": b, "takeable": False}
    if b == "born_resting":
        start = next((i for i in range(n) if adv[i] <= EPS), None)
        if start is None:
            return {"r": 0.0, "reason": "no_fill", "bar": None, "filled": False,
                    "born": b, "takeable": True}
    else:
        start = 0
    last = min(n, max_bars) if max_bars else n
    if last <= start:
        return {"r": 0.0, "reason": "no_fill", "bar": None, "filled": False,
                "born": b, "takeable": True}
    for i in range(start, last):
        f, a = fav[i], adv[i]
        if a <= stop_r + EPS:
            return {"r": stop_r, "reason": "stop", "bar": i + 1, "filled": True,
                    "born": b, "takeable": True}
        if target_r is not None and f >= target_r - EPS:
            return {"r": target_r, "reason": "target", "bar": i + 1, "filled": True,
                    "born": b, "takeable": True}
    return {"r": cls[last - 1], "reason": "mark_at_horizon", "bar": last, "filled": True,
            "born": b, "takeable": True}


def main():
    # ---- anchor
    anch = {}
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            a = json.loads(line)
            anch[(a["candidate_id"], a["decision_time_utc"])] = a.get("mkt_r_prev_close")

    # ---- pool scalars
    keep_cols = ["candidate_id", "decision_time_utc", "symbol", "side", "direction",
                 "origin_family", "setup_family", "bucket_source_family",
                 "session_bucket", "authority_session", "kill_zone", "route_session",
                 "utc_hour_bucket", "decision_timeframe", "market_timeframe",
                 "entry_price", "stop_loss", "take_profit_1", "risk_distance",
                 "policy_target_r", "raw_target_r", "gross_r", "cost_r", "spread_r",
                 "commission_r", "swap_cost_r", "expected_slippage_r",
                 "opportunity_net_proxy_r", "final_blocker_class",
                 "is_first_emission", "setup_dup_count", "setup_dup_rank",
                 "risk_per_trade_pct", "candidate_probability", "candidate_ev_r",
                 "which_came_first", "mfe_r", "mae_r", "path_bars",
                 "scheduler_materialization_status", "limit_marketable_at_decision",
                 "fill_realism_class", "execution_fill_probability"]
    pool = {}
    for r in w0_ws.iter_rows():
        pool[(r["candidate_id"], r["decision_time_utc"])] = {k: r.get(k) for k in keep_cols}

    n_written = 0
    miss_path = 0
    with gzip.open(OUT, "wt") as out:
        for rp in w0_ws.iter_rpaths():
            k = (rp["candidate_id"], rp["decision_time_utc"])
            p = pool.get(k)
            if p is None:
                miss_path += 1
                continue
            fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
            m = anch.get(k)
            T = p.get("policy_target_r") or 2.0
            # forward
            fw = walk(fav, adv, cls, m, target_r=T)
            fw2 = walk(fav, adv, cls, m, target_r=2.0)
            # inverse — exact reflection
            ifav = [-x for x in adv]
            iadv = [-x for x in fav]
            icls = [-x for x in cls]
            mi = None if m is None else -m
            iw = walk(ifav, iadv, icls, mi, target_r=2.0)
            iw1 = walk(ifav, iadv, icls, mi, target_r=1.0)
            iw3 = walk(ifav, iadv, icls, mi, target_r=3.0)
            iwT = walk(ifav, iadv, icls, mi, target_r=None)  # ride to horizon, stop -1

            ep = p.get("entry_price") or 0.0
            rd = p.get("risk_distance") or 0.0
            row = dict(p)
            row["mkt_r_at_decision"] = m
            row["born_fwd"] = fw["born"]
            row["born_inv"] = iw["born"]
            row["risk_pct_of_price"] = (rd / ep) if ep else None
            row["hour_utc"] = int(rp["decision_time_utc"][11:13])
            row["day_utc"] = rp["decision_time_utc"][:10]
            row["n_bars"] = len(fav)
            for tag, w in (("fwd", fw), ("fwd2", fw2), ("inv", iw),
                           ("inv1", iw1), ("inv3", iw3), ("invR", iwT)):
                row[tag + "_r"] = round(w["r"], 6)
                row[tag + "_reason"] = w["reason"]
                row[tag + "_bar"] = w["bar"]
                row[tag + "_filled"] = w["filled"]
                row[tag + "_takeable"] = w["takeable"]
            out.write(json.dumps(row) + "\n")
            n_written += 1

    print(json.dumps({"written": n_written, "paths_without_pool_row": miss_path,
                      "anchor_rows": len(anch), "out": OUT}))


if __name__ == "__main__":
    main()
