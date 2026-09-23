#!/usr/bin/env python3
"""l12 step 9: three order-of-operations / sizing questions.

(a) The EV is attached BEFORE the geometry rewrite (v4_timewarp:67448-67450 vs
    :67680-67712). Measure raw_target_r vs the 2.0R contract the walk uses.
(b) The selector halves risk on every risk-bearing action except 'trade'
    (selector_v4.py:4930-4935, reduce_multiplier 0.5). Measure how much of the
    admitted population is halved and what that cohort earned.
(c) risk_per_trade_pct takes 4 values. Is size allocated toward the better cohort or
    away from it? Size-weighted R is the money question.
"""
import gzip
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402

ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")


def st(rows, y="gross_r"):
    v = [r[y] for r in rows if r.get(y) is not None]
    if not v:
        return None
    return {"n": len(v), "mean": round(sum(v) / len(v), 6),
            "win": round(sum(1 for x in v if x > 0) / len(v), 5),
            "sum": round(sum(v), 3)}


def main():
    rows = w0_ws.load()
    by = {(r["candidate_id"], r["decision_time_utc"]): r for r in rows}
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if line.strip():
                a = json.loads(line)
                t = by.get((a.get("candidate_id"), a.get("decision_time_utc")))
                if t is not None:
                    t["_mkt_r"] = a.get("mkt_r_prev_close")
    clean = [r for r in rows if r.get("_mkt_r") is not None and r["_mkt_r"] > -1.0]
    out = {}

    # (a) geometry: what target was the EV computed at, vs what the walk used
    rt = Counter(round(r.get("raw_target_r"), 4) if r.get("raw_target_r") is not None
                 else None for r in rows)
    pt = Counter(round(r.get("policy_target_r"), 4) if r.get("policy_target_r") is not None
                 else None for r in rows)
    out["geometry"] = {
        "raw_target_r_top": {str(k): v for k, v in rt.most_common(12)},
        "policy_target_r_top": {str(k): v for k, v in pt.most_common(12)},
        "n_raw_ne_policy": sum(
            1 for r in rows
            if r.get("raw_target_r") is not None and r.get("policy_target_r") is not None
            and abs(r["raw_target_r"] - r["policy_target_r"]) > 1e-9),
        "dynamic_geometry_policy": {
            str(k): v for k, v in
            Counter(r.get("dynamic_geometry_policy") for r in rows).most_common(6)},
    }
    # EV implied by the generator's rr vs the walked 2.0R:
    # thesis EV = p*reward - (1-p)*1.0 - ... ; recompute at reward 1.5 and 2.0
    for reward in (1.5, 2.0):
        vals = []
        for r in rows:
            p = r.get("candidate_probability")
            if p is None:
                continue
            vals.append(p * reward - (1 - p) * 1.0)
        out["geometry"]["implied_ev_at_reward_%.1f" % reward] = {
            "n": len(vals), "mean": round(sum(vals) / len(vals), 6)}
    out["geometry"]["stamped_candidate_ev_r_mean"] = round(
        sum(r["candidate_ev_r"] for r in rows) / len(rows), 6)

    # (b) selector reduce multiplier
    RISK_BEARING = {"trade", "reduce-risk", "open-reduced-risk"}
    for pname, pop in (("ALL", rows), ("CLEAN", clean)):
        cens = defaultdict(list)
        for r in pop:
            cens[str(r.get("selector_action"))].append(r)
        rb = {k: v for k, v in cens.items() if k in RISK_BEARING}
        n_rb = sum(len(v) for v in rb.values())
        halved = sum(len(v) for k, v in rb.items() if k != "trade")
        out.setdefault("reduce_multiplier", {})[pname] = {
            "risk_bearing_n": n_rb,
            "halved_n": halved,
            "halved_share_of_risk_bearing": round(halved / n_rb, 5) if n_rb else None,
            "by_action": {k: {"gross": st(v), "honest": st(v, "fill_honest_walk_r")}
                          for k, v in sorted(cens.items(), key=lambda kv: -len(kv[1]))},
        }
        # size-weighted: what the halving costs / saves
        full = [r for r in rb.get("trade", [])]
        half = [r for k, v in rb.items() if k != "trade" for r in v]
        gf = st(full) or {"mean": 0, "n": 0}
        gh = st(half) or {"mean": 0, "n": 0}
        out["reduce_multiplier"][pname]["halving_effect"] = {
            "full_size_cohort": gf, "halved_cohort": gh,
            "halved_cohort_is_better_by": round(
                (gh["mean"] - gf["mean"]), 6) if gf["n"] and gh["n"] else None,
        }

    # (c) risk_per_trade_pct allocation
    for pname, pop in (("ALL", rows), ("CLEAN", clean)):
        buckets = defaultdict(list)
        for r in pop:
            buckets[r.get("risk_per_trade_pct")].append(r)
        tbl = {}
        for k, v in sorted(buckets.items(), key=lambda kv: -(kv[0] or 0)):
            s = st(v)
            h = st(v, "fill_honest_walk_r")
            tbl[str(k)] = {"gross": s, "honest": h,
                           "size_weighted_gross": round(s["mean"] * (k or 0), 6)}
        num = sum((r.get("risk_per_trade_pct") or 0) * (r.get("gross_r") or 0)
                  for r in pop)
        den = sum((r.get("risk_per_trade_pct") or 0) for r in pop)
        eq = sum((r.get("gross_r") or 0) for r in pop) / len(pop)
        out.setdefault("risk_pct_allocation", {})[pname] = {
            "by_bucket": tbl,
            "size_weighted_mean_gross_per_unit_risk": round(num / den, 6),
            "equal_weighted_mean_gross": round(eq, 6),
            "sizing_lift": round(num / den - eq, 6),
        }

    dest = os.path.join(HERE, "L12_SIZING_GEOMETRY_V1.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)

    print("geometry raw_target_r:", list(out["geometry"]["raw_target_r_top"].items())[:6])
    print("geometry policy_target_r:", list(out["geometry"]["policy_target_r_top"].items())[:6])
    print("raw!=policy rows:", out["geometry"]["n_raw_ne_policy"])
    print("implied EV @1.5:", out["geometry"]["implied_ev_at_reward_1.5"]["mean"],
          "@2.0:", out["geometry"]["implied_ev_at_reward_2.0"]["mean"],
          "stamped:", out["geometry"]["stamped_candidate_ev_r_mean"])
    for pname in ("ALL", "CLEAN"):
        d = out["reduce_multiplier"][pname]
        print("== reduce %s: risk_bearing=%d halved=%d (%.1f%%)" % (
            pname, d["risk_bearing_n"], d["halved_n"],
            100 * d["halved_share_of_risk_bearing"]))
        for k, v in d["by_action"].items():
            print("   %-22s n=%6d gross=%8.4f honest=%8.4f" % (
                k, v["gross"]["n"], v["gross"]["mean"],
                v["honest"]["mean"] if v["honest"] else float("nan")))
        print("   halved cohort better by:", d["halving_effect"]["halved_cohort_is_better_by"])
        a = out["risk_pct_allocation"][pname]
        print("== risk_pct %s: sw=%.5f eq=%.5f lift=%.5f" % (
            pname, a["size_weighted_mean_gross_per_unit_risk"],
            a["equal_weighted_mean_gross"], a["sizing_lift"]))
        for k, v in a["by_bucket"].items():
            print("   pct=%-6s n=%6d gross=%8.4f honest=%8.4f" % (
                k, v["gross"]["n"], v["gross"]["mean"],
                v["honest"]["mean"] if v["honest"] else float("nan")))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
