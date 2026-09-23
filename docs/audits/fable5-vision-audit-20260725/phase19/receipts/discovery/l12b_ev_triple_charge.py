#!/usr/bin/env python3
"""l12b: prove the triple cost charge and price the EV reward haircut.
ev_r is built at probability_debate_v4.py:673-678 as
   ev = p*reward_r - (1-p)*loss_r - cost_r - 0.20*uncertainty
so cost_r is ALREADY inside ev. The scheduler then subtracts it again inside the
executable-transfer net edge (:15753) and a third time as cost_penalty (:22077).
Regress ev on (p, cost_r): the cost coefficient should be -1."""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import w0_ws  # noqa


def ols(y, X):
    k = len(X[0]); n = len(y)
    A = [[sum(X[i][a]*X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    B = [sum(X[i][a]*y[i] for i in range(n)) for a in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(A[r][c]))
        A[c], A[p] = A[p], A[c]; B[c], B[p] = B[p], B[c]
        pv = A[c][c]
        for j in range(c, k):
            A[c][j] /= pv
        B[c] /= pv
        for r in range(k):
            if r != c and A[r][c]:
                f = A[r][c]
                for j in range(c, k):
                    A[r][j] -= f*A[c][j]
                B[r] -= f*B[c]
    coef = B
    pred = [sum(coef[a]*X[i][a] for a in range(k)) for i in range(n)]
    res = [y[i]-pred[i] for i in range(n)]
    m = sum(y)/n
    sst = sum((v-m)**2 for v in y); sse = sum(v*v for v in res)
    return coef, 1-sse/sst, (sse/(n-k))**.5


def main():
    rows = w0_ws.load()
    sel = [r for r in rows if r.get("candidate_ev_r") is not None
           and r.get("candidate_probability") is not None and r.get("cost_r") is not None]
    y = [r["candidate_ev_r"] for r in sel]
    X = [[1.0, r["candidate_probability"], r["cost_r"]] for r in sel]
    c1, r2_1, rmse1 = ols(y, X)
    X2 = [[1.0, r["candidate_probability"]] for r in sel]
    c2, r2_2, rmse2 = ols(y, X2)
    out = {"n": len(sel),
           "ols_ev_on_p_and_cost": {"intercept": round(c1[0], 6), "coef_probability": round(c1[1], 6),
                                    "coef_cost_r": round(c1[2], 6), "r2": round(r2_1, 8),
                                    "rmse": round(rmse1, 8)},
           "ols_ev_on_p_only": {"intercept": round(c2[0], 6), "coef_probability": round(c2[1], 6),
                                "r2": round(r2_2, 8), "rmse": round(rmse2, 8)}}
    # implied reward multiple per row, assuming loss=1 and cost inside
    rr = []
    for r in sel:
        p = r["candidate_probability"]
        if p > 0.01:
            rr.append((r["candidate_ev_r"] + 1.0 + r["cost_r"])/p - 1.0)
    rr.sort()
    out["implied_reward_multiple_given_loss1_cost_inside"] = {
        "n": len(rr), "mean": round(sum(rr)/len(rr), 5),
        "p05": round(rr[int(.05*len(rr))], 5), "p50": round(rr[len(rr)//2], 5),
        "p95": round(rr[int(.95*len(rr))], 5),
        "declared_take_profit_1_reward_multiple": 2.0,
        "note": "the residual below 2.0 is the 0.20*uncertainty term plus any rr<2 fallback"}
    # price the absolute expected-net floors under haircut EV vs declared-geometry EV
    floors = [0.10, 0.20, 0.70, 0.80, 1.10]
    fl = {}
    for f in floors:
        a = sum(1 for r in sel if (r["candidate_ev_r"] - r["cost_r"]) >= f)
        b = sum(1 for r in sel if (3.0*r["candidate_probability"] - 1.0 - r["cost_r"]) >= f)
        c = sum(1 for r in sel if r["candidate_ev_r"] >= f)
        fl["min_expected_net_r_%.2f" % f] = {
            "passing_as_shipped_ev_minus_cost": a,
            "passing_if_ev_used_declared_2R_geometry": b,
            "extra_candidates_unlocked": b-a,
            "extra_share_of_pool": round((b-a)/len(sel), 5),
            "passing_on_raw_ev_no_extra_cost": c}
    out["absolute_ev_floor_sensitivity"] = fl
    # what the three charges cost in absolute R terms
    mc = sum(r["cost_r"] for r in sel)/len(sel)
    out["cost_charge_accounting"] = {
        "mean_cost_r": round(mc, 6),
        "charge_1_inside_ev_probability_debate_v4_673_678": round(mc, 6),
        "charge_2_inside_executable_transfer_net_edge_scheduler_15753": round(mc, 6),
        "charge_3_cost_penalty_scheduler_22077_weight_0p80": round(0.80*mc, 6),
        "total_score_units_charged": round(mc + mc + 0.80*mc, 6),
        "ratio_to_single_charge": round((mc + mc + 0.80*mc)/mc, 4)}
    dest = os.path.join(HERE, "L12B_EV_TRIPLE_CHARGE_V1.json")
    json.dump(out, open(dest, "w"), indent=1)
    print("OLS ev ~ 1 + p + cost_r : intercept %.6f  p %.6f  cost_r %.6f  R2 %.8f rmse %.8f"
          % (c1[0], c1[1], c1[2], r2_1, rmse1))
    print("OLS ev ~ 1 + p         : intercept %.6f  p %.6f            R2 %.8f rmse %.8f"
          % (c2[0], c2[1], r2_2, rmse2))
    print("implied reward multiple (loss=1, cost inside): mean %.4f p05 %.4f p50 %.4f p95 %.4f vs declared 2.0"
          % (out["implied_reward_multiple_given_loss1_cost_inside"]["mean"],
             out["implied_reward_multiple_given_loss1_cost_inside"]["p05"],
             out["implied_reward_multiple_given_loss1_cost_inside"]["p50"],
             out["implied_reward_multiple_given_loss1_cost_inside"]["p95"]))
    for k, v in fl.items():
        print("  %-24s shipped %6d | declared-2R %6d | unlocked %6d (%.2f%% of pool)"
              % (k, v["passing_as_shipped_ev_minus_cost"], v["passing_if_ev_used_declared_2R_geometry"],
                 v["extra_candidates_unlocked"], 100*v["extra_share_of_pool"]))
    print("cost charged %.4fx over in score units (mean cost_r %.4f -> %.4f score units)"
          % (out["cost_charge_accounting"]["ratio_to_single_charge"], mc,
             out["cost_charge_accounting"]["total_score_units_charged"]))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
