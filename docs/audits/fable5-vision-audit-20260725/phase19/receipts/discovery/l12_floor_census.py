#!/usr/bin/env python3
"""l12 step 7: what does each hard FLOOR constant in config actually refuse, and what
was the refused cohort worth?

Eleven separate min_fill_probability floors (config/agent_config.yaml:794-1080) all key
on execution_fill_probability, which is 0.92-flat on 70.3% of rows. Measure the cohort
below each floor.
"""
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402

ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")

FLOORS = [
    ("ultimate_candidate_package_soften_selector_fill_floor_min_fill_probability", 0.25, 798),
    ("scheduler_v4..package_cooldown_release_fill_floor_authority_min_fill_probability", 0.25, 1080),
    ("ultimate_candidate_package_strong_fill_floor_bypass_min_execution_fill_probability", 0.35, 801),
    ("selector_v4_calibrated_min_fill_probability", 0.45, 811),
    ("scheduler_v4..selector_reduce_risk_package_fill_floor_min_fill_probability", 0.45, 1030),
    ("scheduler_v4..dynamic_budget_package_fill_floor_authority_bypass_min_fill_probability", 0.45, 1043),
    ("ultimate_candidate_package_positive_predecision_off_session_min_fill_probability", 0.70, 794),
    ("scheduler_v4..dynamic_budget_min_fill_probability", 0.80, 1002),
    ("scheduler_v4..selector_reduce_risk_new_entry_min_fill_probability", 0.80, 1016),
    ("scheduler_v4..package_cooldown_release_min_fill_probability", 0.80, 1075),
    ("ultimate_candidate_package_numeric_disagreement_open_reduced_risk_min_fill_probability", 0.90, 1049),
    ("ultimate_candidate_package_positive_predecision_router_refusal_min_fill_probability", 0.90, 1053),
    ("scheduler_v4..source_bound_router_refusal_replay_materialization_min_fill_probability", 0.90, 1058),
]


def st(rows, y="gross_r"):
    v = [r[y] for r in rows if r.get(y) is not None]
    if not v:
        return None
    return {"n": len(v), "mean": round(sum(v) / len(v), 6),
            "win": round(sum(1 for x in v if x > 0) / len(v), 5)}


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

    out = {"pool_n": len(rows), "clean_n": len(clean), "floors": {}}
    for pname, pop in (("ALL", rows), ("CLEAN", clean)):
        out["floors"][pname] = {}
        for name, thr, line in FLOORS:
            below = [r for r in pop
                     if r.get("execution_fill_probability") is not None
                     and r["execution_fill_probability"] < thr]
            above = [r for r in pop
                     if r.get("execution_fill_probability") is not None
                     and r["execution_fill_probability"] >= thr]
            out["floors"][pname][name] = {
                "threshold": thr, "config_line": line,
                "below_gross": st(below), "above_gross": st(above),
                "below_honest": st(below, "fill_honest_walk_r"),
                "above_honest": st(above, "fill_honest_walk_r"),
                "share_below": round(len(below) / len(pop), 5),
            }
    # the 0.92 flat block vs everything else
    for pname, pop in (("ALL", rows), ("CLEAN", clean)):
        flat = [r for r in pop if r.get("execution_fill_probability") == 0.92]
        other = [r for r in pop if r.get("execution_fill_probability") is not None
                 and r["execution_fill_probability"] != 0.92]
        out.setdefault("flat_block", {})[pname] = {
            "flat_0.92": {"gross": st(flat), "honest": st(flat, "fill_honest_walk_r")},
            "not_0.92": {"gross": st(other), "honest": st(other, "fill_honest_walk_r")},
        }

    dest = os.path.join(HERE, "L12_FLOOR_CENSUS_V1.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)

    for pname in ("ALL", "CLEAN"):
        print("== %s" % pname)
        print("   %-5s %7s %8s %8s %8s %8s" % (
            "thr", "share<", "belowG", "aboveG", "belowH", "aboveH"))
        seen = set()
        for name, thr, line in FLOORS:
            if thr in seen:
                continue
            seen.add(thr)
            d = out["floors"][pname][name]
            print("   %-5.2f %7.4f %8.4f %8.4f %8.4f %8.4f" % (
                thr, d["share_below"], d["below_gross"]["mean"],
                d["above_gross"]["mean"], d["below_honest"]["mean"],
                d["above_honest"]["mean"]))
        fb = out["flat_block"][pname]
        print("   flat0.92 g=%.4f h=%.4f n=%d | not0.92 g=%.4f h=%.4f n=%d" % (
            fb["flat_0.92"]["gross"]["mean"], fb["flat_0.92"]["honest"]["mean"],
            fb["flat_0.92"]["gross"]["n"],
            fb["not_0.92"]["gross"]["mean"], fb["not_0.92"]["honest"]["mean"],
            fb["not_0.92"]["gross"]["n"]))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
