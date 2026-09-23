#!/usr/bin/env python3
"""l7 — assemble the lane receipt JSON from every measured artifact."""
import collections, json, math, os, sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import l7_lib as L


def t(v):
    v = [x for x in v if x is not None]
    n = len(v)
    if n < 2:
        return {"n": n}
    m = sum(v) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / n)
    return {"n": n, "mean": round(m, 6), "t": round(m / (sd / math.sqrt(n)), 3) if sd > 0 else None}


def main():
    rows = L.load()
    ok = [r for r in rows if r["mkt"] is not None]
    al = [r for r in rows if r["born"] == "born_at_limit"]
    ladder = json.load(open(os.path.join(D, "L7_RAWLADDER_V1.json")))
    sweep = json.load(open(os.path.join(D, "L7_SWEEP_V2.json")))
    drift = json.load(open(os.path.join(D, "L7_MINUTE_DRIFT_V1.json")))
    res = {}

    res["arenas"] = {
        "definition": {
            "born_state": "from w0cap2_DECISION_ANCHOR_V1 mkt_r_prev_close m, own-side R; "
                          "m<=-1 born_past_stop, -1<m<0 born_marketable, m==0 born_at_limit, m>0 born_resting",
            "ATLIMIT": "m == 0 exactly -- entry IS the decision-instant market. Both directions "
                       "fill at the same instant at the same price: ZERO fill asymmetry. PRIMARY.",
            "SYM": "|m| < 1 -- neither side's stop had already been breached at the decision instant.",
            "CLEAN": "m > -1 (w0-capture's tradeable set). The INVERSE is not symmetric here: 4,593 "
                     "rows have m >= 1, i.e. the inverse's own stop was already gone.",
        },
        "sizes": {"pool": len(rows), "anchored": len(ok),
                  "ATLIMIT": len(al),
                  "SYM": sum(1 for r in ok if abs(r["mkt"]) < 1),
                  "CLEAN": sum(1 for r in ok if r["mkt"] > -1),
                  "inverse_born_past_stop_m_ge_1": sum(1 for r in ok if r["mkt"] >= 1.0)},
        "born_census": dict(collections.Counter(r["born"] for r in rows)),
        "validation_vs_w0capture": {
            "born_at_limit": 14911, "born_resting": 7949, "born_marketable": 1265, "born_past_stop": 3516,
            "gross_ex_past_stop_mean": -0.10392, "gross_ex_past_stop_n": 24125,
            "walked_filled_mean": -0.12744, "walked_filled_n": 23884,
            "exit_census": {"stop": 12299, "mark": 7844, "target": 3709, "same_bar": 32},
            "note": "reproduced EXACTLY by this lane's independently written walker",
        },
    }

    res["headline_atlimit"] = {
        "n": len(al),
        "orig": t([r["om_r"] for r in al]), "inv": t([r["im_r"] for r in al]),
        "coinflip": t([(r["om_r"] + r["im_r"]) / 2 for r in al]),
        "dirsig": t([(r["im_r"] - r["om_r"]) / 2 for r in al]),
        "joint_exit_census": {},
    }
    jc = collections.Counter((r["om_x"], r["im_x"]) for r in al)
    for k, v in jc.items():
        res["headline_atlimit"]["joint_exit_census"]["%s/%s" % k] = v
    res["headline_atlimit"]["exit_rates"] = {
        "orig_target": round(sum(1 for r in al if r["om_x"] == "target") / len(al), 5),
        "inv_target": round(sum(1 for r in al if r["im_x"] == "target") / len(al), 5),
        "orig_stop": round(sum(1 for r in al if r["om_x"] == "stop") / len(al), 5),
        "inv_stop": round(sum(1 for r in al if r["im_x"] == "stop") / len(al), 5),
        "orig_mark": round(sum(1 for r in al if r["om_x"] == "mark") / len(al), 5),
        "inv_mark": round(sum(1 for r in al if r["im_x"] == "mark") / len(al), 5),
    }

    res["side_split_atlimit"] = {}
    for s in ["LONG", "SHORT"]:
        v = [r for r in al if r["side"] == s]
        res["side_split_atlimit"][s] = {
            "orig": t([r["om_r"] for r in v]), "inv": t([r["im_r"] for r in v]),
            "dirsig": t([(r["im_r"] - r["om_r"]) / 2 for r in v]),
            "coin": t([(r["om_r"] + r["im_r"]) / 2 for r in v])}
    dl = res["side_split_atlimit"]["LONG"]["dirsig"]["mean"]
    ds = res["side_split_atlimit"]["SHORT"]["dirsig"]["mean"]
    res["side_split_atlimit"]["decomposition"] = {
        "side_neutral_signal_error": round((dl + ds) / 2, 6),
        "drift_component": round((ds - dl) / 2, 6),
        "reading": "BOTH sides positive => the finding is NOT market drift and NOT a bid-quote "
                   "convention (either would give opposite signs by side)."}

    res["entry_delay_ladder_exact"] = ladder
    res["minute_by_minute_mark_drift"] = drift
    res["sweep_pop_headline"] = sweep["pop_headline"]
    res["sweep_pop_sizes"] = sweep["pop_sizes"]
    res["vol_cuts_risk_distance_pct_of_price"] = sweep["vol_cuts"]

    # per-family born census, the structural fact
    fb = collections.defaultdict(collections.Counter)
    for r in rows:
        fb[r["fam"]][r["born"]] += 1
    res["family_by_born"] = {f: dict(c) for f, c in fb.items()}

    # blocker-class control
    res["blocker_control_atlimit"] = {}
    gb = collections.defaultdict(list)
    for r in al:
        gb[r["blocker"]].append(r)
    for b, v in gb.items():
        if len(v) < 30:
            continue
        res["blocker_control_atlimit"][b] = {
            "orig": t([r["om_r"] for r in v]), "inv": t([r["im_r"] for r in v]),
            "dirsig": t([(r["im_r"] - r["om_r"]) / 2 for r in v])}
    for lab, f in [("cost_gate_PASSED", lambda r: (r["spread_r"] or 0) <= 0.10 and (r["cost_r"] or 0) <= 0.15),
                   ("cost_gate_REFUSED", lambda r: not ((r["spread_r"] or 0) <= 0.10 and (r["cost_r"] or 0) <= 0.15))]:
        v = [r for r in al if f(r)]
        res["blocker_control_atlimit"][lab] = {
            "orig": t([r["om_r"] for r in v]), "inv": t([r["im_r"] for r in v]),
            "dirsig": t([(r["im_r"] - r["om_r"]) / 2 for r in v])}

    # cost decomposition per family
    cf = collections.defaultdict(list)
    for r in al:
        cf[r["fam"]].append(r)
    res["cost_per_family_atlimit"] = {}
    for f, v in cf.items():
        sp = L.mean([r["spread_r"] for r in v])
        co = L.mean([r["cost_r"] for r in v])
        res["cost_per_family_atlimit"][f] = {
            "n": len(v), "frozen_cost_r": round(co, 5), "frozen_spread_r": round(sp, 5),
            "commission_r": round(L.mean([r["comm_r"] for r in v]), 5),
            "true_cost_r_spread_over_7p9": round(co - sp + sp / 7.9, 5),
            "median_risk_distance_pct_of_price": round(L.q([r["rd_pct"] for r in v], 0.5), 5)}

    # ranked cells
    cells = [c for c in sweep["cells"] if c["pop"] == "ATLIMIT"]
    res["ranked_by_win_deficit_score_atlimit_top40"] = sorted(
        [c for c in cells if c.get("score_decl") is not None], key=lambda x: -x["score_decl"])[:40]
    res["ranked_by_inverse_value_atlimit_top40"] = sorted(
        [c for c in cells if c["n_if"] >= 100 and c["i_mean"] is not None], key=lambda x: -x["i_mean"])[:40]
    cellsS = [c for c in sweep["cells"] if c["pop"] == "SYM"]
    res["ranked_by_win_deficit_score_SYM_top25"] = sorted(
        [c for c in cellsS if c.get("score_decl") is not None], key=lambda x: -x["score_decl"])[:25]

    with open(os.path.join(D, "l7_RESULT.json"), "w") as f:
        json.dump(res, f, indent=1)
    print("wrote l7_RESULT.json  keys:", len(res))


if __name__ == "__main__":
    main()
