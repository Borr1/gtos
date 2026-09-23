#!/usr/bin/env python3
"""l12b: (1) is candidate_probability already inside candidate_ev_r (double application)?
(2) constant-field census — machinery whose output never varies.
(3) order-of-operations: what the cost gate refuses vs what a stop-validity check would."""
import gzip, json, math, os, sys
from collections import Counter, defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import w0_ws  # noqa
ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")


def st(v):
    n = len(v); m = sum(v)/n
    sd = (sum((x-m)**2 for x in v)/max(1, n-1))**.5
    return n, m, sd


def main():
    rows = w0_ws.load()
    by = {(r["candidate_id"], r["decision_time_utc"]): r for r in rows}
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if line.strip():
                a = json.loads(line)
                t = by.get((a["candidate_id"], a["decision_time_utc"]))
                if t is not None:
                    t["_mkt"] = a.get("mkt_r_prev_close")
    out = {}
    # --- 1. ev vs probability functional relation
    pts = [(r["candidate_probability"], r["candidate_ev_r"]) for r in rows
           if r.get("candidate_probability") is not None and r.get("candidate_ev_r") is not None]
    n, mp, sp = st([a for a, _ in pts]); _, me, se = st([b for _, b in pts])
    cov = sum((a-mp)*(b-me) for a, b in pts)/(n-1)
    pear = cov/(sp*se)
    # exact functional check: how many distinct ev per distinct p
    m = defaultdict(set)
    for a, b in pts:
        m[round(a, 6)].add(round(b, 6))
    multi = sum(1 for v in m.values() if len(v) > 1)
    # residual of the affine fit
    b1 = cov/(sp*sp); b0 = me - b1*mp
    resid = [b - (b0 + b1*a) for a, b in pts]
    _, mr, sr = st(resid)
    out["ev_vs_probability"] = {
        "n": n, "pearson_r": round(pear, 6), "r2": round(pear*pear, 6),
        "affine_fit": {"slope": round(b1, 6), "intercept": round(b0, 6)},
        "residual_sd": round(sr, 6), "ev_sd": round(se, 6),
        "residual_share_of_ev_sd": round(sr/se, 6),
        "distinct_probability_values": len(m),
        "probability_values_mapping_to_more_than_one_ev": multi}
    # --- 2. constant / near-constant field census
    consts = {}
    fields = sorted(rows[0].keys())
    for f in fields:
        vals = Counter()
        nn = 0
        for r in rows:
            v = r.get(f)
            if v is None:
                continue
            nn += 1
            if isinstance(v, float):
                v = round(v, 9)
            try:
                vals[v] += 1
            except TypeError:
                vals[str(v)] += 1
            if len(vals) > 6:
                break
        if 0 < len(vals) <= 6 and nn > 0:
            top, cnt = vals.most_common(1)[0]
            full = sum(1 for r in rows if r.get(f) is not None)
            same = sum(1 for r in rows if (round(r[f], 9) if isinstance(r.get(f), float) else r.get(f)) == top)
            if same/max(1, full) >= 0.95:
                consts[f] = {"non_null": full, "modal_value": str(top)[:60],
                             "modal_share": round(same/full, 6), "distinct_seen": len(vals)}
    out["constant_or_near_constant_fields"] = consts
    # --- 3. order of operations: cost gate vs stop-validity
    SPREAD_CAP, TOTAL_CAP = 0.10, 0.15
    cost_block = [r for r in rows if (r.get("spread_r") or 0) > SPREAD_CAP or (r.get("cost_r") or 0) > TOTAL_CAP]
    cost_pass = [r for r in rows if not ((r.get("spread_r") or 0) > SPREAD_CAP or (r.get("cost_r") or 0) > TOTAL_CAP)]
    past = [r for r in rows if r.get("_mkt") is not None and r["_mkt"] <= -1.0]
    pastset = {id(r) for r in past}

    def blk(sel, y="gross_r"):
        v = [r[y] for r in sel if r.get(y) is not None]
        if not v:
            return None
        n, m, sd = st(v)
        return {"n": n, "mean": round(m, 5),
                "win": round(sum(1 for x in v if x > 0)/n, 5)}
    out["order_of_operations"] = {
        "cost_gate_blocks": {"n": len(cost_block), "gross": blk(cost_block),
                             "honest": blk(cost_block, "fill_honest_walk_r"),
                             "of_which_past_stop": sum(1 for r in cost_block if id(r) in pastset)},
        "cost_gate_passes": {"n": len(cost_pass), "gross": blk(cost_pass),
                             "honest": blk(cost_pass, "fill_honest_walk_r"),
                             "of_which_past_stop": sum(1 for r in cost_pass if id(r) in pastset)},
        "past_stop_total": len(past),
        "past_stop_caught_by_cost_gate_share": round(
            sum(1 for r in cost_block if id(r) in pastset)/max(1, len(past)), 5),
        "past_stop_surviving_cost_gate": sum(1 for r in cost_pass if id(r) in pastset),
        "ALT_stop_validity_first": {
            "n_kept": len(rows)-len(past),
            "gross": blk([r for r in rows if id(r) not in pastset]),
            "honest": blk([r for r in rows if id(r) not in pastset], "fill_honest_walk_r")},
        "ALT_stop_validity_then_cost": {
            "n_kept": sum(1 for r in cost_pass if id(r) not in pastset),
            "gross": blk([r for r in cost_pass if id(r) not in pastset]),
            "honest": blk([r for r in cost_pass if id(r) not in pastset], "fill_honest_walk_r")}}
    # cost_r rank correlation with risk_distance (is the cost gate a stop-width proxy?)
    pts2 = [(r["cost_r"], r["risk_distance"]) for r in rows
            if r.get("cost_r") is not None and r.get("risk_distance")]
    ra = sorted(range(len(pts2)), key=lambda i: pts2[i][0])
    rb = sorted(range(len(pts2)), key=lambda i: pts2[i][1])
    rka = [0]*len(pts2); rkb = [0]*len(pts2)
    for i, j in enumerate(ra):
        rka[j] = i
    for i, j in enumerate(rb):
        rkb[j] = i
    n2, ma, sa = st(rka); _, mb, sb = st(rkb)
    cov2 = sum((rka[i]-ma)*(rkb[i]-mb) for i in range(n2))/(n2-1)
    out["cost_gate_is_a_stop_width_proxy"] = {
        "n": n2, "spearman_cost_r_vs_risk_distance": round(cov2/(sa*sb), 6)}
    dest = os.path.join(HERE, "L12B_DOUBLES_ORDER_V1.json")
    json.dump(out, open(dest, "w"), indent=1)
    e = out["ev_vs_probability"]
    print("EV~P: r2=%.6f slope=%.4f intercept=%.4f resid_sd=%.6f (=%.2f%% of ev sd) p_vals=%d multi=%d"
          % (e["r2"], e["affine_fit"]["slope"], e["affine_fit"]["intercept"], e["residual_sd"],
             100*e["residual_share_of_ev_sd"], e["distinct_probability_values"],
             e["probability_values_mapping_to_more_than_one_ev"]))
    print("CONSTANT/NEAR-CONSTANT FIELDS (>=95%% modal):", len(consts))
    for k, v in sorted(consts.items()):
        print("   %-46s n=%6d modal=%-22s share=%.4f" % (k, v["non_null"], v["modal_value"], v["modal_share"]))
    o = out["order_of_operations"]
    print("ORDER: cost gate blocks n=%d gross %.4f (past_stop inside %d) | passes n=%d gross %.4f (past_stop %d)"
          % (o["cost_gate_blocks"]["n"], o["cost_gate_blocks"]["gross"]["mean"],
             o["cost_gate_blocks"]["of_which_past_stop"], o["cost_gate_passes"]["n"],
             o["cost_gate_passes"]["gross"]["mean"], o["cost_gate_passes"]["of_which_past_stop"]))
    print("       stop-validity-first keeps %d gross %.4f honest %.4f"
          % (o["ALT_stop_validity_first"]["n_kept"], o["ALT_stop_validity_first"]["gross"]["mean"],
             o["ALT_stop_validity_first"]["honest"]["mean"]))
    print("       both keeps %d gross %.4f honest %.4f"
          % (o["ALT_stop_validity_then_cost"]["n_kept"],
             o["ALT_stop_validity_then_cost"]["gross"]["mean"],
             o["ALT_stop_validity_then_cost"]["honest"]["mean"]))
    print("       spearman(cost_r, risk_distance) =", out["cost_gate_is_a_stop_width_proxy"]["spearman_cost_r_vs_risk_distance"])
    print("WROTE", dest)


if __name__ == "__main__":
    main()
