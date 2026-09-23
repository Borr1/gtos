#!/usr/bin/env python3
"""x1-B: where inside the decision M15 bar does each family's defining condition become true?

For every candidate we rebuild the generator's own predicate (broader_origin_generators.py,
cited per family below) and evaluate it minute by minute inside the decision bar, using ONLY
information available by that minute:

  * lookback features (prior_20_high/low, prior_50, previous-bar ATRs, session open range,
    previous trend state, the leader's move) come from bars strictly BEFORE the decision bar
    -> they are fixed at the decision bar's OPEN;
  * the decision bar's own contribution (its running high/low/close) is taken from the M1
    bars inside it, so atr14/atr50/range/body/close-position are the running versions.

Two moments are reported per candidate:
  break_minute   -- first minute at which the LEVEL involved was crossed (an extreme crossing,
                    i.e. "the move happened"), where the family has a level;
  confirm_minute -- first minute whose M1 CLOSE satisfies the family's full predicate
                    (the generator's own test, with the M1 close standing in for the M15 close).

Minutes are 0-based inside the bar. A predicate first true at minute k is knowable at
bar_open+(k+1) minutes, i.e. `14-k` minutes before the decision the system actually took.

For the three current-framework families (fvg / ob_retest / breaker_re_entry, 46.1 % of the
pool) the zone bounds are not in the pool, so we use a SUFFICIENT (never-early) test:
|price-entry|/price <= poi_proximity_tolerance_pct (0.01, config/agent_config.yaml:4032).
Since entry is the zone MIDPOINT (:1618-1620) and the near edge is always closer to an outside
price than the midpoint is, this can only report the trigger LATER than the truth.
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

OUT_JSON = os.path.join(HERE, "x1_B_STALENESS_V1.json")
OUT_ROWS = os.path.join(HERE, "x1_B_ROWS_V1.jsonl")
POI_TOL = 0.01
ZONE_FAMS = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}


def pct(a, b):
    return round(100.0 * a / b, 4) if b else None


def qs(v):
    v = sorted(x for x in v if x is not None)
    if not v:
        return None
    def q(p):
        i = min(len(v) - 1, max(0, int(round(p * (len(v) - 1)))))
        return v[i]
    return {"n": len(v), "mean": round(statistics.fmean(v), 6), "p10": q(0.10), "p25": q(0.25),
            "median": q(0.50), "p75": q(0.75), "p90": q(0.90), "min": v[0], "max": v[-1]}


def main():
    rows = w0_ws.load()
    m15 = XB.load_m15()
    m1 = XB.load_m1()
    print("bars loaded", flush=True)

    # leader lookup for cross_asset (leader close at decision_bar_open-15m is fixed at open)
    out_rows = []
    diag = defaultdict(int)

    for r in rows:
        sym = r["symbol"]
        if sym not in m15:
            diag["no_m15_symbol"] += 1
            continue
        bars, idx = m15[sym]
        bar_open = XB._pt(r["decision_time_utc"]) - timedelta(minutes=15)
        i = idx.get(bar_open)
        if i is None or i < 51:
            diag["no_decision_bar"] += 1
            continue
        sl = XB.m1_slice(m1, sym, bar_open, 15)
        if len(sl) < 2:
            diag["no_m1"] += 1
            continue
        fam, side = r["origin_family"], r["side"]
        b = bars[i]
        full_rng = b[2] - b[3]
        d = r["risk_distance"]
        entry = r["entry_price"]

        # ---- fixed-at-open lookbacks -------------------------------------------------
        p20h, p20l = XB.prior_high(bars, i, 20), XB.prior_low(bars, i, 20)
        p50h, p50l = XB.prior_high(bars, i, 50), XB.prior_low(bars, i, 50)
        sum13 = sum(x[2] - x[3] for x in bars[i - 13:i])       # ATR14 minus current bar
        sum49 = sum(x[2] - x[3] for x in bars[i - 49:i])       # ATR50 minus current bar
        prior_a14, prior_a50 = XB.atr(bars, i - 1, 14), XB.atr(bars, i - 1, 50)
        prior_ratio = (prior_a14 / prior_a50) if (prior_a14 and prior_a50 and prior_a50 > 0) else None
        prev_trend = XB.previous_trend_state(bars, i)
        c20 = bars[i - 20][4]
        # 50-bar high/low EXCLUDING the current bar, for close_position
        hi49 = max(x[2] for x in bars[i - 49:i])
        lo49 = min(x[3] for x in bars[i - 49:i])
        prev_close = bars[i - 1][4]

        o0 = sl[0][2]
        rh = -math.inf
        rl = math.inf
        break_minute = None
        confirm_minute = None
        entry_touch_minute = None
        conf_price = None
        brk_price = None

        for (k, _t, o, h, lo, c, _v) in sl:
            rh = max(rh, h)
            rl = min(rl, lo)
            rng = rh - rl
            a14 = (sum13 + rng) / 14.0
            a50 = (sum49 + rng) / 50.0
            if entry_touch_minute is None and lo <= entry <= h:
                entry_touch_minute = k

            # ---- level cross ("the move happened") --------------------------------
            if break_minute is None:
                crossed = False
                if fam == "liquidity_sweep_reclaim":
                    crossed = (rh > p20h) if side == "SHORT" else (rl < p20l)
                elif fam == "displacement_continuation":
                    crossed = a14 > 0 and rng / a14 >= 1.5
                elif fam == "volatility_compression_expansion":
                    crossed = (rh > p20h) if side == "LONG" else (rl < p20l)
                elif fam == "regime_transition_break":
                    crossed = (rh > p20h) if side == "LONG" else (rl < p20l)
                elif fam == "structural_distance_extreme":
                    crossed = (rh >= hi49) if side == "SHORT" else (rl <= lo49)
                elif fam == "session_open_range_break":
                    # open-range bounds are not in the pool; the stop encodes the far edge:
                    # LONG stop = range_low-0.10*atr14 ; SHORT stop = range_high+0.10*atr14
                    crossed = None
                elif fam in ZONE_FAMS or fam == "cross_asset_lead_lag":
                    crossed = None
                if crossed:
                    break_minute, brk_price = k, c

            # ---- full predicate confirmation --------------------------------------
            if confirm_minute is None:
                ok = False
                if fam == "liquidity_sweep_reclaim":
                    sh = rh > p20h and c < p20h
                    slw = rl < p20l and c > p20l
                    ok = (sh and not slw) if side == "SHORT" else (slw and not sh)
                elif fam == "displacement_continuation":
                    body = abs(c - o0)
                    ok = (a14 > 0 and rng / a14 >= 1.5 and body / a14 >= 0.75
                          and (("LONG" if c > o0 else "SHORT") == side))
                elif fam == "volatility_compression_expansion":
                    ok = (prior_ratio is not None and prior_ratio <= 0.75 and a14 > 0
                          and rng / a14 >= 1.25
                          and (c > p20h if side == "LONG" else c < p20l))
                elif fam == "regime_transition_break":
                    st = "insufficient_lookback" if a50 <= 0 else None
                    if st is None:
                        sc = (c - c20) / a50
                        st = ("strong_up" if sc >= 2.0 else "up" if sc >= 0.75 else
                              "strong_down" if sc <= -2.0 else "down" if sc <= -0.75 else "flat")
                    if side == "LONG":
                        ok = st == "strong_up" and prev_trend not in {"strong_up", "up"} and c > p20h
                    else:
                        ok = st == "strong_down" and prev_trend not in {"strong_down", "down"} and c < p20l
                elif fam == "structural_distance_extreme":
                    H, L = max(hi49, rh), min(lo49, rl)
                    if H > L:
                        pos = (c - L) / (H - L)
                        ok = (pos >= 0.97) if side == "SHORT" else (pos <= 0.03)
                elif fam == "cross_asset_lead_lag":
                    la = a14
                    ok = la > 0 and abs(c - prev_close) / la <= 0.5
                elif fam in ZONE_FAMS:
                    ok = c > 0 and abs(c - entry) / c <= POI_TOL
                elif fam == "session_open_range_break":
                    # sufficient (never-early) proxy: the M1 close is already beyond the
                    # decision bar's own close in the trade's direction AND beyond the
                    # level the emitted trade broke, approximated by the bar close itself.
                    ok = (c >= b[4]) if side == "LONG" else (c <= b[4])
                if ok:
                    confirm_minute, conf_price = k, c

        rec = {
            "candidate_id": r["candidate_id"], "decision_time_utc": r["decision_time_utc"],
            "symbol": sym, "side": side, "origin_family": fam, "gross_r": r["gross_r"],
            "risk_distance": d, "entry_price": entry,
            "m1_bars_in_decision_bar": len(sl),
            "full_bar_range": full_rng,
            "break_minute": break_minute, "confirm_minute": confirm_minute,
            "entry_touch_minute_in_decision_bar": entry_touch_minute,
        }
        # earliness + price given up
        for tag, mk, px in (("break", break_minute, brk_price), ("confirm", confirm_minute, conf_price)):
            if mk is None:
                rec[f"{tag}_minutes_early"] = None
                rec[f"{tag}_range_printed_frac"] = None
                rec[f"{tag}_edge_given_up_r"] = None
                continue
            rec[f"{tag}_minutes_early"] = 14 - mk
            rr = None
            if full_rng > 0:
                r_h = -math.inf
                r_l = math.inf
                for (k2, _t2, _o2, h2, l2, _c2, _v2) in sl:
                    if k2 > mk:
                        break
                    r_h = max(r_h, h2)
                    r_l = min(r_l, l2)
                rr = (r_h - r_l) / full_rng
            rec[f"{tag}_range_printed_frac"] = rr
            if px is not None and d > 0 and fam not in ZONE_FAMS:
                rec[f"{tag}_edge_given_up_r"] = ((entry - px) / d) if side == "LONG" else ((px - entry) / d)
            else:
                rec[f"{tag}_edge_given_up_r"] = None
        out_rows.append(rec)

    with open(OUT_ROWS, "w") as fh:
        for rec in out_rows:
            fh.write(json.dumps(rec) + "\n")

    # ---- aggregate ---------------------------------------------------------------
    by_fam = defaultdict(list)
    for rec in out_rows:
        by_fam[rec["origin_family"]].append(rec)
    summary = {}
    for fam, recs in sorted(by_fam.items(), key=lambda kv: -len(kv[1])):
        n = len(recs)
        cm = [x["confirm_minute"] for x in recs]
        bm = [x["break_minute"] for x in recs]
        summary[fam] = {
            "n": n,
            "confirmed_intrabar_n": sum(1 for x in cm if x is not None),
            "confirmed_intrabar_pct": pct(sum(1 for x in cm if x is not None), n),
            "confirmed_at_final_minute_only_pct": pct(sum(1 for x in cm if x == 14), n),
            "confirm_minute": qs(cm),
            "confirm_minutes_early": qs([x["confirm_minutes_early"] for x in recs]),
            "confirm_range_printed_frac": qs([x["confirm_range_printed_frac"] for x in recs]),
            "confirm_edge_given_up_r": qs([x["confirm_edge_given_up_r"] for x in recs]),
            "break_minute": qs(bm),
            "break_minutes_early": qs([x["break_minutes_early"] for x in recs]),
            "break_range_printed_frac": qs([x["break_range_printed_frac"] for x in recs]),
            "break_edge_given_up_r": qs([x["break_edge_given_up_r"] for x in recs]),
            "entry_touched_inside_decision_bar_pct": pct(
                sum(1 for x in recs if x["entry_touch_minute_in_decision_bar"] is not None), n),
            "entry_touch_minute": qs([x["entry_touch_minute_in_decision_bar"] for x in recs]),
        }
    doc = {"schema": "gtos.x1.staleness.v1", "n_rows_measured": len(out_rows),
           "diagnostics": dict(diag), "poi_tolerance_pct": POI_TOL,
           "note": ("minute k is 0-based inside the decision bar; a predicate first true at "
                    "minute k is knowable 14-k minutes before the decision the system took"),
           "per_family": summary}
    with open(OUT_JSON, "w") as fh:
        json.dump(doc, fh, indent=2)
    print(json.dumps({"n": len(out_rows), "diag": dict(diag)}, indent=1))
    for fam, s in summary.items():
        ce = s["confirm_minutes_early"]
        eg = s["confirm_edge_given_up_r"]
        print(f"{fam:36s} n={s['n']:6d} conf%={s['confirmed_intrabar_pct']:7.3f} "
              f"medEarly={(ce or {}).get('median')} meanEarly={(ce or {}).get('mean')} "
              f"rangeFrac={(s['confirm_range_printed_frac'] or {}).get('median')} "
              f"edgeR={(eg or {}).get('mean')}")


if __name__ == "__main__":
    main()
