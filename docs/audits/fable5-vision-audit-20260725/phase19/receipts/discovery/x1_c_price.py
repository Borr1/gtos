#!/usr/bin/env python3
"""x1-C: pool-weighted aggregates, fill latency (Q5), and what earliness is WORTH for the
three current-framework families, where the entry level does not depend on the bar close at all.

ARM A  (as the system ran it): the limit at `entry_price` exists from decision_time.
       Fill = first M1 bar at/after decision_time+1min that trades through entry.
ARM B  (order placed at the decision bar's OPEN, 15 minutes earlier — the SAME order, the
       SAME price, the SAME signal, only the placement clock moved): fill = first M1 bar
       at/after the decision bar's open that trades through entry.
Both arms are walked with one identical walker and both are capped at the SAME absolute
horizon (decision_time + 120 min), so ARM B is never credited with extra time.

ARM B2 is the same but with 120 minutes measured from the fill, which is what a real order
would get; reported separately so the horizon effect is visible and not smuggled in.
"""
from __future__ import annotations

import json
import math
import os
import statistics
import sys
from collections import defaultdict
from datetime import timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402
import x1_bars as XB  # noqa: E402

OUT = os.path.join(HERE, "x1_C_PRICE_V1.json")
ZONE_FAMS = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}


def stat(v):
    v = [x for x in v if x is not None]
    if not v:
        return None
    return {"n": len(v), "mean": round(statistics.fmean(v), 6),
            "sum": round(sum(v), 4),
            "median": round(statistics.median(v), 6),
            "stdev": round(statistics.pstdev(v), 6) if len(v) > 1 else 0.0}


def walk(m1, sym, start_t, horizon_end, entry, stop, target, side, d):
    """First-touch walk on M1. Returns (fill_time, r, exit_reason, fill_minute_offset)."""
    bars = m1.get(sym) or {}
    t = start_t
    fill_t = None
    last_close = None
    while t <= horizon_end:
        b = bars.get(t)
        if b is None:
            t += timedelta(minutes=1)
            continue
        o, h, lo, c, _v = b
        if fill_t is None:
            if lo <= entry <= h:
                fill_t = t
            else:
                t += timedelta(minutes=1)
                continue
        # from the fill bar onward (inclusive), first-touch with tie -> stop
        if side == "LONG":
            hit_t = h >= target
            hit_s = lo <= stop
        else:
            hit_t = lo <= target
            hit_s = h >= stop
        if hit_s:
            return fill_t, -1.0, "stop", None
        if hit_t:
            return fill_t, (abs(target - entry) / d), "target", None
        last_close = c
        t += timedelta(minutes=1)
    if fill_t is None:
        return None, 0.0, "no_fill", None
    r = ((last_close - entry) / d) if side == "LONG" else ((entry - last_close) / d)
    return fill_t, r, "path_end", None


def main():
    rows = w0_ws.load()
    m1 = XB.load_m1()
    m15 = XB.load_m15()
    print("loaded", flush=True)

    # ---------- pool-weighted staleness aggregate (from x1-B rows) ----------
    brows = {}
    with open(os.path.join(HERE, "x1_B_ROWS_V1.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            brows[(r["candidate_id"], r["decision_time_utc"])] = r
    early = [r["confirm_minutes_early"] for r in brows.values()]
    frac = [r["confirm_range_printed_frac"] for r in brows.values()]
    edge = [r["confirm_edge_given_up_r"] for r in brows.values()]
    agg = {"pool_confirm_minutes_early": stat(early),
           "pool_confirm_range_printed_frac": stat(frac),
           "pool_confirm_edge_given_up_r_close_entry_families_only": stat(edge)}

    # ---------- Q5: decision-to-fill latency implied by the pool ----------
    lat = defaultdict(list)
    touched1 = defaultdict(lambda: [0, 0])
    for r in rows:
        fam = r["origin_family"]
        cls = "zone_entry" if fam in ZONE_FAMS else "close_entry"
        bt = r["bars_to_entry_touch"]
        lat[("all", cls)].append(bt)
        lat[("fam", fam)].append(bt)
        lat[("realism", r["fill_realism_class"])].append(bt)
        lat[("ordertype", r["effective_order_type"])].append(bt)
        t = touched1[fam]
        t[1] += 1
        if bt == 1:
            t[0] += 1
    def latsum(v):
        n = len(v)
        got = [x for x in v if x is not None]
        s = sorted(got)
        def q(p):
            return s[min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))] if s else None
        return {"n": n, "never_touched": n - len(got),
                "never_touched_pct": round(100 * (n - len(got)) / n, 4) if n else None,
                "touched_in_bar_1_pct": round(100 * sum(1 for x in got if x == 1) / n, 4) if n else None,
                "touched_within_5min_pct": round(100 * sum(1 for x in got if x <= 5) / n, 4) if n else None,
                "median_minutes": q(0.5), "p25": q(0.25), "p75": q(0.75), "p90": q(0.90),
                "mean_minutes": round(statistics.fmean(got), 4) if got else None}
    latency = {f"{a}:{b}": latsum(v) for (a, b), v in sorted(lat.items())}

    # ---------- duplicate persistence (how long the same setup stood) ----------
    dup = defaultdict(list)
    for r in rows:
        dup[r["origin_family"]].append(r["setup_dup_count"])
    dupsum = {}
    for fam, v in dup.items():
        v = [x for x in v if x]
        s = sorted(v)
        dupsum[fam] = {"n": len(v), "mean_emissions_per_setup": round(statistics.fmean(v), 4),
                       "median": s[len(s) // 2], "max": max(v),
                       "pct_rows_on_repeated_setup": round(100 * sum(1 for x in v if x > 1) / len(v), 4)}

    # ---------- ARM A vs ARM B on the zone families ----------
    res = {"A": defaultdict(list), "B": defaultdict(list), "B2": defaultdict(list)}
    fillinfo = defaultdict(lambda: {"n": 0, "A_filled": 0, "B_filled": 0, "B_earlier": 0,
                                    "B_fill_only": 0, "A_fill_only": 0})
    paired = defaultdict(list)
    n_done = 0
    for r in rows:
        fam = r["origin_family"]
        if fam not in ZONE_FAMS:
            continue
        sym = r["symbol"]
        dt = XB._pt(r["decision_time_utc"])
        bar_open = dt - timedelta(minutes=15)
        d = r["risk_distance"]
        if not d or d <= 0:
            continue
        side = r["side"]
        entry = r["entry_price"]
        stop = r["stop_loss"]
        tgt = entry + r["policy_target_r"] * d if side == "LONG" else entry - r["policy_target_r"] * d
        hz = dt + timedelta(minutes=120)
        fa, ra, xa, _ = walk(m1, sym, dt + timedelta(minutes=1), hz, entry, stop, tgt, side, d)
        fb, rb, xb, _ = walk(m1, sym, bar_open, hz, entry, stop, tgt, side, d)
        fb2 = fb
        rb2 = rb
        if fb is not None:
            fb2, rb2, xb2, _ = walk(m1, sym, fb, fb + timedelta(minutes=120), entry, stop, tgt, side, d)
        else:
            rb2 = 0.0
        res["A"][fam].append(ra)
        res["B"][fam].append(rb)
        res["B2"][fam].append(rb2)
        paired[fam].append(rb - ra)
        fi = fillinfo[fam]
        fi["n"] += 1
        fi["A_filled"] += int(fa is not None)
        fi["B_filled"] += int(fb is not None)
        if fa is not None and fb is not None and fb < fa:
            fi["B_earlier"] += 1
        if fa is None and fb is not None:
            fi["B_fill_only"] += 1
        if fb is None and fa is not None:
            fi["A_fill_only"] += 1
        n_done += 1
        if n_done % 3000 == 0:
            print("walked", n_done, flush=True)

    arms = {}
    tot = {"A": [], "B": [], "B2": [], "delta": []}
    for fam in sorted(res["A"]):
        arms[fam] = {
            "n": len(res["A"][fam]),
            "ARM_A_as_ran": stat(res["A"][fam]),
            "ARM_B_placed_at_bar_open_same_horizon": stat(res["B"][fam]),
            "ARM_B2_placed_at_bar_open_120min_from_fill": stat(res["B2"][fam]),
            "paired_delta_B_minus_A": stat(paired[fam]),
            "fills": dict(fillinfo[fam]),
        }
        tot["A"] += res["A"][fam]
        tot["B"] += res["B"][fam]
        tot["B2"] += res["B2"][fam]
        tot["delta"] += paired[fam]
    arms["ALL_ZONE_FAMILIES"] = {
        "n": len(tot["A"]),
        "ARM_A_as_ran": stat(tot["A"]),
        "ARM_B_placed_at_bar_open_same_horizon": stat(tot["B"]),
        "ARM_B2_placed_at_bar_open_120min_from_fill": stat(tot["B2"]),
        "paired_delta_B_minus_A": stat(tot["delta"]),
    }

    doc = {"schema": "gtos.x1.price.v1",
           "aggregate_staleness": agg,
           "decision_to_fill_latency_minutes": latency,
           "touched_in_first_path_bar_by_family": {
               k: {"n": v[1], "bars_to_entry_touch_eq_1": v[0],
                   "pct": round(100 * v[0] / v[1], 4)} for k, v in sorted(touched1.items())},
           "setup_persistence": dupsum,
           "zone_family_earliness_arms": arms,
           "walker": {"target": "policy_target_r", "stop": "-1R", "tie": "stop",
                      "horizon": "decision_time+120min for A and B; fill+120min for B2",
                      "no_fill_books": 0.0}}
    with open(OUT, "w") as fh:
        json.dump(doc, fh, indent=2)
    print(json.dumps(agg, indent=1))
    print(json.dumps(arms["ALL_ZONE_FAMILIES"], indent=1))
    for fam in ZONE_FAMS:
        if fam in arms:
            print(fam, json.dumps(arms[fam]["paired_delta_B_minus_A"]), json.dumps(arms[fam]["fills"]))


if __name__ == "__main__":
    main()
