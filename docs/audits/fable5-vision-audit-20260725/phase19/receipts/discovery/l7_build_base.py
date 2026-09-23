#!/usr/bin/env python3
"""l7_build_base — one row per candidate with ORIGINAL and INVERSE walks, symmetric.

INVERSE definition (same entry level, stop and target reflected):
    fav_inv = -adv ; adv_inv = -fav ; cls_inv = -cls
So the inverse is the opposite side at the SAME price, with the SAME risk distance.
Fill contract for the inverse is the mirror of the original: price must trade at/through
the entry level from the other side (adv_inv <= 0  <=>  fav >= 0).

Both sides walked at a FLAT +2.0R target / -1.0R stop (take_profit_1 is exactly 2.0000R on
all 27,658 rows; policy_target_r disagrees on 4.44% -- see W0-F4), conservative same-bar tie
to the stop, 120-bar horizon, mark-to-market at path end.
"""
import gzip, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws

OUT = os.path.join(HERE, "l7_BASE.jsonl.gz")
ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")

def born(m):
    if m is None: return "unknown"
    return "born_past_stop" if m <= -1.0 else ("born_marketable" if m < 0.0 else ("born_at_limit" if m == 0.0 else "born_resting"))

def walk(fav, adv, cls, target_r=2.0, stop_r=-1.0, require_fill=True, max_bars=None):
    n = len(fav); start = 0
    if require_fill:
        start = next((i for i in range(n) if adv[i] <= 1e-12), None)
        if start is None: return 0.0, "no_fill", None
    last = min(n, max_bars) if max_bars else n
    if last <= start: return 0.0, "no_fill", None
    for i in range(start, last):
        if adv[i] <= stop_r + 1e-12: return stop_r, "stop", i + 1
        if fav[i] >= target_r - 1e-12: return target_r, "target", i + 1
    return cls[last - 1], "path_end", last

def main():
    rows = w0_ws.load()
    anc = {}
    with gzip.open(ANCHOR, "rt") as fh:
        for l in fh:
            r = json.loads(l)
            anc[(r["candidate_id"], r["decision_time_utc"])] = r
    # symbol-relative volatility state from decision-time geometry (no look-ahead)
    bysym = {}
    for r in rows:
        rd = float(r["risk_distance"]); px = float(r["entry_price"])
        r["_rdpct"] = 100.0 * rd / px if px else None
        bysym.setdefault(r["symbol"], []).append(r["_rdpct"])
    cuts = {}
    for s, v in bysym.items():
        v = sorted(x for x in v if x is not None)
        if len(v) < 6: cuts[s] = (None, None); continue
        cuts[s] = (v[len(v)//3], v[2*len(v)//3])
    paths = {}
    for rp in w0_ws.iter_rpaths():
        paths[(rp["candidate_id"], rp["decision_time_utc"])] = rp
    nw = 0
    with gzip.open(OUT, "wt") as out:
        for r in rows:
            k = (r["candidate_id"], r["decision_time_utc"])
            rp = paths[k]
            fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
            ifav = [-a for a in adv]; iadv = [-f for f in fav]; icls = [-c for c in cls]
            o_h, o_hr, o_hb = walk(fav, adv, cls, require_fill=True)
            o_b, o_br, o_bb = walk(fav, adv, cls, require_fill=False)
            i_h, i_hr, i_hb = walk(ifav, iadv, icls, require_fill=True)
            i_b, i_br, i_bb = walk(ifav, iadv, icls, require_fill=False)
            a = anc.get(k)
            m = a["mkt_r_prev_close"] if a else None   # CLEAN no-look-ahead anchor
            mL = a["mkt_r_close"] if a else None
            # AT-MARKET pair: enter at the decision-instant market price instead of the
            # generator's limit level, same risk distance d, +2R/-1R. PERFECTLY SYMMETRIC:
            # fav_inv_atm == -adv_atm and adv_inv_atm == -fav_atm, both fill at bar 1 by
            # construction, so no fill contract can bias the inversion comparison.
            if m is None:
                oa_r=oa_x=ia_r=ia_x=None; oaL_r=iaL_r=None
            else:
                fa=[x-m for x in fav]; aa=[x-m for x in adv]; ca=[x-m for x in cls]
                oa_r,oa_x,_ = walk(fa,aa,ca,require_fill=False)
                ia_r,ia_x,_ = walk([-x for x in aa],[-x for x in fa],[-x for x in ca],require_fill=False)
                fL=[x-mL for x in fav]; aL=[x-mL for x in adv]; cL=[x-mL for x in cls]
                oaL_r,_,_ = walk(fL,aL,cL,require_fill=False)
                iaL_r,_,_ = walk([-x for x in aL],[-x for x in fL],[-x for x in cL],require_fill=False)   # CLEAN no-look-ahead anchor (w0-capture V2); mkt_r_close is the look-ahead one
            lo, hi = cuts.get(r["symbol"], (None, None))
            rd = r["_rdpct"]
            vs = "unknown"
            if lo is not None and rd is not None:
                vs = "lo_vol" if rd <= lo else ("hi_vol" if rd > hi else "mid_vol")
            hh = int(r["decision_time_utc"][11:13])
            out.write(json.dumps({
                "candidate_id": r["candidate_id"], "decision_time_utc": r["decision_time_utc"],
                "family": r["origin_family"], "symbol": r["symbol"], "side": r["side"],
                "session": r["session_bucket"], "route_session": r["route_session"],
                "hour": hh, "vol_state": vs, "rd_pct": rd,
                "risk_pct": r.get("risk_per_trade_pct"),
                "gross_r": r["gross_r"], "cost_r": r["cost_r"], "spread_r": r.get("spread_r"),
                "plain_walk_r": r.get("plain_walk_r"),
                "policy_target_r": r.get("policy_target_r"),
                "which_came_first": r["which_came_first"],
                "mfe_r": r["mfe_r"], "mae_r": r["mae_r"],
                "mkt_r_prev_close": m, "born_state": born(m),
                "orig_atm_r": oa_r, "orig_atm_reason": oa_x, "inv_atm_r": ia_r, "inv_atm_reason": ia_x,
                "orig_atm_lag1_r": oaL_r, "inv_atm_lag1_r": iaL_r,
                "mkt_r_close_LOOKAHEAD": (a["mkt_r_close"] if a else None),
                "orig_honest_r": o_h, "orig_honest_reason": o_hr, "orig_honest_bar": o_hb,
                "orig_blind_r": o_b, "orig_blind_reason": o_br,
                "inv_honest_r": i_h, "inv_honest_reason": i_hr, "inv_honest_bar": i_hb,
                "inv_blind_r": i_b, "inv_blind_reason": i_br,
                "is_first_emission": r.get("is_first_emission"),
                "setup_dup_count": r.get("setup_dup_count"),
                "blocker": r.get("final_blocker_class"),
            }) + "\n")
            nw += 1
    print("wrote", nw, OUT)

if __name__ == "__main__":
    main()
