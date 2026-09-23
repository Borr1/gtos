#!/usr/bin/env python3
"""l12b: exact marginal charge accounting for the scheduler score, and how often the
max(0, ev-cost) floor kills the dominant term outright."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import w0_ws  # noqa


def main():
    rows = w0_ws.load()
    sel = [r for r in rows if None not in (r.get("candidate_ev_r"), r.get("candidate_probability"),
                                           r.get("cost_r"), r.get("source_completeness"))]
    n = len(sel)
    dcost, mults, floored, floored_gross, live_gross = [], [], 0, [], []
    for r in sel:
        ev, c, p = r["candidate_ev_r"], r["cost_r"], r["candidate_probability"]
        f = r.get("execution_fill_probability") or 0.0
        k = max(0., min(1., r["source_completeness"]))
        pm, fm = max(0., min(1., p)), max(0., min(1., f))
        live = 1.0 if (ev - c) > 0 else 0.0
        dcost.append(-6.00*pm*fm*k*live - 0.80)
        mults.append(pm*fm*k)
        if not live:
            floored += 1
            if r.get("gross_r") is not None:
                floored_gross.append(r["gross_r"])
        elif r.get("gross_r") is not None:
            live_gross.append(r["gross_r"])
    out = {"n": n,
           "mean_marginal_d_score_d_cost": round(sum(dcost)/n, 5),
           "intended_single_charge": -1.0,
           "over_charge_ratio": round(abs(sum(dcost)/n), 4),
           "mean_probability_x_fill_x_completeness_multiplier": round(sum(mults)/n, 5),
           "xfer_floor": {
               "rows_with_ev_minus_cost_le_0_term_is_zero": floored,
               "share_of_pool": round(floored/n, 5),
               "floored_cohort_gross_mean": round(sum(floored_gross)/len(floored_gross), 5) if floored_gross else None,
               "floored_cohort_n": len(floored_gross),
               "live_cohort_gross_mean": round(sum(live_gross)/len(live_gross), 5) if live_gross else None,
               "live_cohort_n": len(live_gross)}}
    # uncertainty: charged inside ev (probability_debate_v4:678, weight 0.20) AND again as
    # scheduler uncertainty_penalty (:22076, weight 0.20). Both use the same constant.
    out["uncertainty_double_charge"] = {
        "inside_ev_site": "src/components/probability_debate_v4.py:678 (- uncertainty * 0.20)",
        "scheduler_site": "src/research/moonshot_scheduler_v4_best_trade_allocator.py:22076 (-uncertainty * 0.20)",
        "scheduler_uncertainty_is_default_constant": 0.35,
        "scheduler_uncertainty_default_site": "moonshot_scheduler_v4_best_trade_allocator.py:19264",
        "scheduler_charge_score_units": 0.07,
        "implied_mean_uncertainty_inside_ev_from_intercept": 0.5934,
        "note": "the scheduler limb is a constant on this pool so it cannot move a rank; "
                "the ev limb is real and is charged before the scheduler charges it again"}
    dest = os.path.join(HERE, "L12B_CHARGE_ACCOUNTING_V1.json")
    json.dump(out, open(dest, "w"), indent=1)
    print(json.dumps(out, indent=1)[:1600])
    print("WROTE", dest)


if __name__ == "__main__":
    main()
