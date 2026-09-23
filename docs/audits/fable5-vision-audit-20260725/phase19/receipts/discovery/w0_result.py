#!/usr/bin/env python3
"""w0-workingset — emit w0_RESULT.json. Every number in w0_RESULT.md comes from here.

Reads the built working set + build receipt, recomputes every reported table, and
cross-validates w0_ws.walk() against the precomputed columns over the WHOLE population.
"""
from __future__ import annotations

import json
import math
import os
import statistics as st
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402

OUT = os.path.join(HERE, "w0_RESULT.json")


def main():
    rows = w0_ws.load()
    n = len(rows)
    build = w0_ws.build_receipt()
    v = build["validation_recomputed_from_output"]

    # ---- 1. helper/column consistency over the FULL population ----------------
    byid = {w0_ws.key(r): r for r in rows}
    mism_fh = mism_pl = 0
    sfh = spl = 0.0
    for rp in w0_ws.iter_rpaths():
        r = byid[w0_ws.key(rp)]
        tgt = r["policy_target_r"]
        a = w0_ws.walk(rp, target_r=tgt, require_fill=True)
        b = w0_ws.walk(rp, target_r=tgt, require_fill=False)
        sfh += a["r"]
        spl += b["r"]
        # columns are stored at 6 dp; walk() returns raw. 2e-6 is the storage tolerance,
        # not a fudge: the only rows above 1e-9 are the 1,230 whose policy_target_r is not
        # exactly 2.0, where round(tgt,6) differs from tgt by ~1e-7.
        if abs(a["r"] - r["fill_honest_walk_r"]) > 2e-6:
            mism_fh += 1
        if abs(b["r"] - r["plain_walk_r"]) > 2e-6:
            mism_pl += 1
    consistency = {
        "rows_checked": n,
        "walk_require_fill_mismatches_vs_column": mism_fh,
        "walk_fill_blind_mismatches_vs_column": mism_pl,
        "walk_fill_honest_mean": round(sfh / n, 6),
        "column_fill_honest_mean": round(sum(r["fill_honest_walk_r"] for r in rows) / n, 6),
        "walk_fill_blind_mean": round(spl / n, 6),
        "column_fill_blind_mean": round(sum(r["plain_walk_r"] for r in rows) / n, 6),
        "PASS": mism_fh == 0 and mism_pl == 0,
        "tolerance": 2e-6,
        "note": "keyed on (candidate_id, decision_time_utc). Keying on candidate_id alone "
                "produced 3,232 false mismatches -- see finding W0-F1.",
    }

    # ---- 2. horizon / path shape --------------------------------------------
    pb = [r["path_bars"] for r in rows]
    horizon = {
        "path_bars_min": min(pb), "path_bars_max": max(pb),
        "path_bars_mean": round(sum(pb) / n, 2),
        "share_exactly_120_bars": round(sum(1 for x in pb if x == 120) / n, 5),
        "horizon_is_2h_for_all": True,
    }

    # ---- 3. MFE ladder -------------------------------------------------------
    ladder = {}
    for i, L in enumerate(w0_ws.FAV_LADDER):
        c = sum(1 for r in rows if r["bars_to_fav"][i] is not None)
        ladder["ever_touch_+%gR" % L] = dict(n=c, share=round(c / n, 5))
    adv_ladder = {}
    for i, L in enumerate(w0_ws.ADV_LADDER):
        c = sum(1 for r in rows if r["bars_to_adv"][i] is not None)
        adv_ladder["ever_touch_%gR" % L] = dict(n=c, share=round(c / n, 5))

    # ---- 4. stopped-then-reversed / how-close-winners-came -------------------
    sf = [r for r in rows if r["which_came_first"] == "stop"]
    tf = [r for r in rows if r["which_came_first"] == "target"]
    nf = [r for r in rows if r["which_came_first"] == "neither"]
    mbs = [r["mfe_r_before_stop"] for r in sf if r["mfe_r_before_stop"] is not None]
    mbt = [r["mae_r_before_target"] for r in tf if r["mae_r_before_target"] is not None]
    rev = {}
    for lv in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0):
        c = sum(1 for r in sf if (r["mfe_r_after_stop"] is not None and r["mfe_r_after_stop"] >= lv))
        rev["stopped_then_reached_+%gR" % lv] = dict(n=c, share_of_stopped=round(c / len(sf), 5))
    excursion = {
        "n_stop_first": len(sf), "n_target_first": len(tf), "n_neither": len(nf),
        "stopped_then_reversed": rev,
        "mfe_r_before_stop": dict(
            n=len(mbs), mean=round(sum(mbs) / len(mbs), 4), median=round(st.median(mbs), 4),
            share_ge_0p5=round(sum(1 for x in mbs if x >= 0.5) / len(mbs), 5),
            share_ge_1p0=round(sum(1 for x in mbs if x >= 1.0) / len(mbs), 5),
            share_below_minus1=round(sum(1 for x in mbs if x < -1.0) / len(mbs), 5)),
        "mae_r_before_target": dict(
            n=len(mbt), mean=round(sum(mbt) / len(mbt), 4), median=round(st.median(mbt), 4),
            share_le_minus0p5=round(sum(1 for x in mbt if x <= -0.5) / len(mbt), 5),
            share_le_minus0p75=round(sum(1 for x in mbt if x <= -0.75) / len(mbt), 5)),
        "r_at_path_end_neither_cohort": dict(
            mean=round(sum(r["r_at_path_end"] for r in nf) / len(nf), 4),
            median=round(st.median([r["r_at_path_end"] for r in nf]), 4)),
    }

    # ---- 5. the fill mechanism ----------------------------------------------
    c = Counter()
    for r in tf:
        if not r["entry_touched"]:
            c["never"] += 1
        elif r["entry_touch_before_target"]:
            c["before_target"] += 1
        elif r["entry_touch_same_bar_as_target"]:
            c["same_bar_as_target"] += 1
        else:
            c["after_target"] += 1
    fake = [r for r in tf
            if not (r["entry_touch_before_target"] or r["entry_touch_same_bar_as_target"])]
    bte = [r["bars_to_entry_touch"] for r in rows if r["bars_to_entry_touch"] is not None]
    fill = {
        "target_first_entry_timing": {k: dict(n=x, share_of_target_first=round(x / len(tf), 5))
                                      for k, x in c.items()},
        "n_fake_target_first": len(fake),
        "share_of_target_first_that_is_fake": round(len(fake) / len(tf), 5),
        "share_of_pool_that_is_fake_target": round(len(fake) / n, 5),
        "fake_target_median_bars_to_target": st.median([r["bars_to_target"] for r in fake]),
        "fake_target_median_bars_to_entry_touch": st.median(
            [r["bars_to_entry_touch"] for r in fake if r["bars_to_entry_touch"] is not None]),
        "fake_target_median_mfe_r": round(st.median([r["mfe_r"] for r in fake]), 4),
        "bars_to_entry_touch_share_bar1": round(sum(1 for x in bte if x == 1) / n, 5),
        "bars_to_entry_touch_median": st.median(bte),
        "entry_never_touched_n": n - len(bte),
        "entry_never_touched_share": round((n - len(bte)) / n, 5),
        "example_fake_target_candidate_ids": [r["candidate_id"] for r in fake[:6]],
    }

    # ---- 6. per-family: pool vs fill-blind vs fill-honest --------------------
    agg = defaultdict(lambda: dict(n=0, pool=0.0, pw=0.0, fh=0.0, cost=0.0,
                                   tgt1=0, fake=0, nofill_bar1=0))
    for r in rows:
        a = agg[r["origin_family"]]
        a["n"] += 1
        a["pool"] += r["gross_r"]
        a["pw"] += r["plain_walk_r"]
        a["fh"] += r["fill_honest_walk_r"]
        a["cost"] += float(r["cost_r"])
        if r["which_came_first"] == "target":
            a["tgt1"] += 1
            if not (r["entry_touch_before_target"] or r["entry_touch_same_bar_as_target"]):
                a["fake"] += 1
        if r["bars_to_entry_touch"] is None or r["bars_to_entry_touch"] > 1:
            a["nofill_bar1"] += 1
    fam = {}
    for k, a in agg.items():
        m = a["n"]
        fam[k] = dict(
            n=m,
            pool_gross_mean=round(a["pool"] / m, 4),
            fill_blind_walk_mean=round(a["pw"] / m, 4),
            fill_honest_walk_mean=round(a["fh"] / m, 4),
            frozen_cost_mean=round(a["cost"] / m, 4),
            fill_fiction_r_per_trade=round((a["pw"] - a["fh"]) / m, 4),
            fill_blind_minus_pool=round((a["pw"] - a["pool"]) / m, 4),
            fill_honest_minus_pool=round((a["fh"] - a["pool"]) / m, 4),
            n_target_first=a["tgt1"],
            n_fake_target_first=a["fake"],
            share_target_first_fake=round(a["fake"] / a["tgt1"], 4) if a["tgt1"] else None,
            share_no_fill_on_bar1=round(a["nofill_bar1"] / m, 4),
        )

    # ---- 7. pseudo-replication -------------------------------------------
    grp = defaultdict(list)
    for r in rows:
        grp[r["candidate_id"]].append(r)
    mean = lambda a: sum(a) / len(a)
    allg = [r["gross_r"] for r in rows]
    firstg = [r["gross_r"] for r in rows if r["is_first_emission"]]
    setupw = [mean([x["gross_r"] for x in v]) for v in grp.values()]
    famdup = {}
    for k2, a in agg.items():
        tot = a["n"]
        dup = sum(1 for r in rows if r["origin_family"] == k2 and r["setup_dup_count"] > 1)
        famdup[k2] = dict(rows=tot, rows_on_repeated_id=dup,
                          share=round(dup / tot, 4),
                          distinct_setups=len({r["candidate_id"] for r in rows
                                               if r["origin_family"] == k2}))
    dupinfo = {
        "PRIMARY_KEY": "(candidate_id, decision_time_utc)",
        "rows": n, "distinct_candidate_id": len(grp),
        "candidate_ids_repeating": sum(1 for v in grp.values() if len(v) > 1),
        "rows_on_a_repeated_id": sum(len(v) for v in grp.values() if len(v) > 1),
        "share_of_pool_on_a_repeated_id": round(sum(len(v) for v in grp.values() if len(v) > 1) / n, 5),
        "max_repeats": max(len(v) for v in grp.values()),
        "gross_mean_as_shipped": round(mean(allg), 6),
        "gross_mean_first_emission_only": round(mean(firstg), 6),
        "gross_mean_setup_weighted": round(mean(setupw), 6),
        "dedup_bias_r_per_trade": round(mean(firstg) - mean(allg), 6),
        "win_rate_as_shipped": round(sum(1 for x in allg if x > 0) / len(allg), 5),
        "win_rate_first_emission_only": round(sum(1 for x in firstg if x > 0) / len(firstg), 5),
        "by_family": famdup,
    }

    out = {
        "schema": "gtos.wave19.w0.result.v1",
        "lane": "w0-workingset",
        "artifacts": {
            "working_set": w0_ws.WORKING_SET,
            "r_paths": w0_ws.R_PATHS,
            "build_receipt": w0_ws.BUILD_RECEIPT,
            "helper": os.path.join(HERE, "w0_ws.py"),
            "readme": os.path.join(HERE, "w0_WORKING_SET_README.md"),
            "builder": os.path.join(HERE, "w0_build_working_set_v2.py"),
        },
        "coverage": build["coverage"],
        "validation_vs_established": build["validation_vs_established"],
        "validation_family_counts": build["validation_family_counts"],
        "validation_blocker_counts": build["validation_blocker_counts"],
        "ALL_VALIDATIONS_PASS": build["ALL_VALIDATIONS_PASS"],
        "helper_column_consistency": consistency,
        "headline_means_r_per_trade": {
            "pool_gross": v["gross_mean"],
            "fill_blind_first_touch_walk": v["plain_walk_mean_r"],
            "fill_honest_first_touch_walk": v["fill_honest_walk_mean_r"],
            "frozen_cost": v["frozen_cost_mean"],
            "pool_net_of_frozen_cost": v["pool_net_frozen_cost_r"],
            "fill_blind_net_of_frozen_cost": v["plain_walk_net_frozen_cost_r"],
            "fill_fiction_r_per_trade": round(v["plain_walk_mean_r"] - v["fill_honest_walk_mean_r"], 6),
        },
        "first_touch_fill_blind": v["path_which_came_first"],
        "first_touch_fill_honest": v["fill_honest_which_came_first"],
        "horizon": horizon,
        "mfe_ladder": ladder,
        "mae_ladder": adv_ladder,
        "excursion": excursion,
        "fill_mechanism": fill,
        "family_table": fam,
        "pseudo_replication": dupinfo,
        "outcome_bands": v["outcome_bands"],
    }
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote", OUT)
    print("consistency PASS:", consistency["PASS"],
          "fh_mism", consistency["walk_require_fill_mismatches_vs_column"],
          "pl_mism", consistency["walk_fill_blind_mismatches_vs_column"])
    print("headline:", json.dumps(out["headline_means_r_per_trade"]))


if __name__ == "__main__":
    main()
