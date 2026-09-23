#!/usr/bin/env python3
"""x1-A: establish the decision anchor and prove the feature reconstruction is exact.

Q: is the decision bar the M15 bar OPENING at decision_time, or the one CLOSING at it?
A test that cannot be argued with: 6 of the 10 origin families set entry = bar.close
(broader_origin_generators.py:711/739/752/778/795/842/933/952/1031/1101...). Compare
entry_price to both candidates' closes.

Then reproduce each family's stop from the M15 series. If the stop reproduces to float
tolerance the whole feature stack (atr14/atr50/prior20/prior50) is exact and the intrabar
work in x1-B is trustworthy.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402
import x1_bars as XB  # noqa: E402

OUT = os.path.join(HERE, "x1_A_ANCHOR_V1.json")

CLOSE_ENTRY_FAMILIES = {
    "liquidity_sweep_reclaim", "displacement_continuation", "volatility_compression_expansion",
    "session_open_range_break", "regime_transition_break", "structural_distance_extreme",
    "cross_asset_lead_lag",
}
ZONE_ENTRY_FAMILIES = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}


def rel(a, b):
    if a is None or b is None:
        return None
    d = max(abs(a), abs(b), 1e-12)
    return abs(a - b) / d


def main():
    rows = w0_ws.load()
    m15 = XB.load_m15()
    print(f"m15 symbols loaded: {len(m15)}")

    stats = {"n": len(rows), "prev_bar_close_match": 0, "cur_bar_close_match": 0,
             "no_prev_bar": 0, "no_cur_bar": 0, "close_entry_n": 0}
    fam_anchor = {}
    stop_repro = {}
    tol = 1e-6

    for r in rows:
        sym = r["symbol"]
        if sym not in m15:
            continue
        bars, idx = m15[sym]
        dt = XB._pt(r["decision_time_utc"])
        prev_open = dt - timedelta(minutes=15)
        i_prev = idx.get(prev_open)
        i_cur = idx.get(dt)
        fam = r["origin_family"]
        if fam in CLOSE_ENTRY_FAMILIES:
            stats["close_entry_n"] += 1
            e = r["entry_price"]
            if i_prev is None:
                stats["no_prev_bar"] += 1
            elif rel(e, bars[i_prev][4]) < tol:
                stats["prev_bar_close_match"] += 1
            if i_cur is None:
                stats["no_cur_bar"] += 1
            elif rel(e, bars[i_cur][4]) < tol:
                stats["cur_bar_close_match"] += 1
            d = fam_anchor.setdefault(fam, {"n": 0, "prev": 0, "cur": 0})
            d["n"] += 1
            if i_prev is not None and rel(e, bars[i_prev][4]) < tol:
                d["prev"] += 1
            if i_cur is not None and rel(e, bars[i_cur][4]) < tol:
                d["cur"] += 1

    # ---- stop reproduction on the anchor that won ----
    anchor_prev = stats["prev_bar_close_match"] >= stats["cur_bar_close_match"]
    off = timedelta(minutes=15) if anchor_prev else timedelta(0)

    for r in rows:
        sym = r["symbol"]
        if sym not in m15:
            continue
        bars, idx = m15[sym]
        i = idx.get(XB._pt(r["decision_time_utc"]) - off)
        if i is None or i < 51:
            continue
        fam = r["origin_family"]
        a14 = XB.atr(bars, i, 14)
        b = bars[i]
        pred = None
        side = r["side"]
        if fam == "liquidity_sweep_reclaim":
            pred = b[2] + 0.25 * a14 if side == "SHORT" else b[3] - 0.25 * a14
        elif fam == "displacement_continuation":
            pred = b[3] - 0.25 * a14 if side == "LONG" else b[2] + 0.25 * a14
        elif fam == "structural_distance_extreme":
            pred = b[2] + 0.25 * a14 if side == "SHORT" else b[3] - 0.25 * a14
        elif fam == "cross_asset_lead_lag":
            pred = b[3] - 0.25 * a14 if side == "LONG" else b[2] + 0.25 * a14
        elif fam == "volatility_compression_expansion":
            p20h, p20l = XB.prior_high(bars, i, 20), XB.prior_low(bars, i, 20)
            pred = (min(b[3], p20l) - 0.20 * a14) if side == "LONG" else (max(b[2], p20h) + 0.20 * a14)
        elif fam == "regime_transition_break":
            p20h, p20l = XB.prior_high(bars, i, 20), XB.prior_low(bars, i, 20)
            pred = (p20l - 0.10 * a14) if side == "LONG" else (p20h + 0.10 * a14)
        if pred is None:
            continue
        d = stop_repro.setdefault(fam, {"n": 0, "match": 0, "worst_rel": 0.0})
        d["n"] += 1
        rr = rel(r["stop_loss"], pred)
        if rr < 1e-6:
            d["match"] += 1
        d["worst_rel"] = max(d["worst_rel"], rr)

    out = {
        "schema": "gtos.x1.anchor.v1",
        "anchor_verdict": ("decision_bar_is_the_M15_BAR_CLOSING_AT_decision_time_utc"
                           if anchor_prev else "decision_bar_OPENS_at_decision_time_utc"),
        "decision_time_equals": "M15 bar open + 15min (v4_timewarp_simulated_live_research_loop.py:58997)",
        "stats": stats,
        "per_family_close_entry_anchor": fam_anchor,
        "stop_reproduction": {k: {**v, "match_pct": round(100 * v["match"] / v["n"], 4)}
                              for k, v in sorted(stop_repro.items())},
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2)[:4000])


if __name__ == "__main__":
    main()
