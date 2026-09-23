#!/usr/bin/env python3
"""x4 step 3 — the full battery over BOTH intra-bar waves plus the engine's own fields, on
three populations and two outcome definitions, with within-symbol standardisation and an
honest train/test split.

Populations
  POOL      all 27,658
  TAKE      not born_past_stop (24,125-ish) -- the population lane l3 uses
  BAR1      TAKE and entry touched on path bar 1 (the <=60 s adverse-selection cohort)

Outcomes
  gross_r               the pool's own realised gross R (fill-blind)
  fill_honest_walk_r    only credits excursion from the fill bar onward

Everything is measured; nothing is fitted here except the explicitly-labelled train/test rule.
"""
import collections, gzip, json, math, os, statistics as st, sys
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import x4_lib as X

INTRA2 = os.path.join(D, "x4_INTRABAR2_V1.jsonl.gz")


def load_all():
    rows = X.load_joined()
    f2 = {}
    with gzip.open(INTRA2, "rt") as fh:
        for line in fh:
            f = json.loads(line)
            f2[(f["candidate_id"], f["decision_time_utc"])] = f
    for r in rows:
        for k, v in f2.get((r["candidate_id"], r["decision_time_utc"]), {}).items():
            if k not in ("candidate_id", "decision_time_utc", "n2"):
                r["x4_" + k] = v
    return rows


ENGINE = ["risk_distance_pct_of_price", "candidate_ev_r", "candidate_probability", "commission_r",
          "fill_probability", "expected_net_r", "swap_cost_r", "setup_dup_rank",
          "source_bound_signal_r", "cost_r", "effective_admission_count", "spread_r", "utc_hour",
          "execution_fill_probability", "risk_finalizer_rank", "expected_cost_r",
          "expected_slippage_r", "broker_pretrade_diag_expected_cost_r", "matched_sleeve_count",
          "policy_target_r", "raw_target_r", "risk_per_trade_pct"]


def zmap(pop, col, minn=25):
    by = collections.defaultdict(list)
    for r in pop:
        if X._num(r.get(col)):
            by[r["symbol"]].append(r[col])
    stats = {}
    for s, v in by.items():
        if len(v) >= minn:
            sd = st.pstdev(v)
            if sd > 0:
                stats[s] = (st.mean(v), sd)
    return {id(r): (r[col] - stats[r["symbol"]][0]) / stats[r["symbol"]][1]
            for r in pop if X._num(r.get(col)) and r["symbol"] in stats}


def scan(pop, ycol, cols, winfn):
    out = []
    pos = [r for r in pop if winfn(r) == 1]
    neg = [r for r in pop if winfn(r) == 0]
    for c in cols:
        z = zmap(pop, c)
        vv = [(z[id(r)], r[ycol]) for r in pop if id(r) in z and X._num(r.get(ycol))]
        if len(vv) < 300:
            continue
        sp = X.spearman([v[0] for v in vv], [v[1] for v in vv])
        vv.sort(key=lambda x: x[0]); m = len(vv)
        q = m // 5
        d1 = X.mean([y for _, y in vv[:q]]); d5 = X.mean([y for _, y in vv[-q:]])
        a = [z[id(r)] for r in pos if id(r) in z]
        b = [z[id(r)] for r in neg if id(r) in z]
        d = X.cohend(a, b)
        t = X.welch_t(a, b)
        # significance of the spearman (Fisher z, n large)
        zz = 0.5 * math.log((1 + sp) / (1 - sp)) * math.sqrt(max(1, m - 3)) if abs(sp) < 1 else None
        out.append({"feature": c, "n": m,
                    "spearman_vs_R": round(sp, 4),
                    "sp_z": round(zz, 2) if zz else None,
                    "sp_p": X.two_sided_p_from_t(zz) if zz else None,
                    "R_q1": round(d1, 5), "R_q5": round(d5, 5), "R_gap_q5_q1": round(d5 - d1, 5),
                    "d_win_vs_stop": round(d, 4) if d else None,
                    "d_p": X.two_sided_p_from_t(t) if t else None,
                    "known_axis": c.replace("x4_", "") in X.KNOWN_AXIS,
                    "engine_field": c in ENGINE})
    out.sort(key=lambda r: -abs(r["spearman_vs_R"]))
    return out


def main():
    rows = load_all()
    cols = sorted({k for r in rows[:500] for k in r if k.startswith("x4_")}
                  - {"x4_n_m1_in_bar", "x4_n_m1_60", "x4_n_m1_300", "x4_bar_end_lag_min"}) + ENGINE
    take = [r for r in rows if r["takeable"]]
    bar1 = [r for r in take if r.get("bars_to_entry_touch") == 1]
    notbar1 = [r for r in take if r.get("bars_to_entry_touch") != 1]

    def wf_band(r):
        return 1 if r["outcome_band"] == "ge_target" else (0 if r["outcome_band"] == "full_stop" else None)

    def wf_honest(r):
        c = r.get("fill_honest_which_came_first")
        return 1 if c == "target" else (0 if c == "stop" else None)

    res = {"n_features_scanned": len(cols),
           "populations": {"pool": len(rows), "takeable": len(take), "bar1": len(bar1),
                           "not_bar1": len(notbar1)},
           "base_rates": {}}
    for nm, pop in (("pool", rows), ("takeable", take), ("bar1", bar1), ("not_bar1", notbar1)):
        res["base_rates"][nm] = {
            "mean_gross_r": round(X.mean([r["gross_r"] for r in pop]), 5),
            "mean_fill_honest_r": round(X.mean([r["fill_honest_walk_r"] for r in pop
                                                if X._num(r.get("fill_honest_walk_r"))]), 5),
            "n": len(pop)}

    res["scan_takeable_gross"] = scan(take, "gross_r", cols, wf_band)
    res["scan_takeable_honest"] = scan(take, "fill_honest_walk_r", cols, wf_honest)
    res["scan_bar1_honest"] = scan(bar1, "fill_honest_walk_r", cols, wf_honest)
    res["scan_notbar1_honest"] = scan(notbar1, "fill_honest_walk_r", cols, wf_honest)
    res["scan_pool_gross"] = scan(rows, "gross_r", cols, wf_band)

    json.dump(res, open(os.path.join(D, "x4_SCAN_V1.json"), "w"), indent=1)
    for k in ("scan_pool_gross", "scan_takeable_gross", "scan_takeable_honest",
              "scan_bar1_honest", "scan_notbar1_honest"):
        print(f"\n=== {k} (top 16 by |spearman vs R|) ===")
        for r in res[k][:16]:
            tag = "ENG" if r["engine_field"] else ("KNOWN" if r["known_axis"] else "   ")
            print(f"  {tag} {r['feature']:32s} sp={r['spearman_vs_R']:+.4f} p={r['sp_p']:.1e} "
                  f"q1={r['R_q1']:+.4f} q5={r['R_q5']:+.4f} gap={r['R_gap_q5_q1']:+.4f} "
                  f"d={r['d_win_vs_stop']}")
    print("\nbase rates:", json.dumps(res["base_rates"]))
    print("\nwrote x4_SCAN_V1.json")


if __name__ == "__main__":
    main()
