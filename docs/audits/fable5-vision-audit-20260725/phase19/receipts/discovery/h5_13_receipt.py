#!/usr/bin/env python3
"""h5 step 13 — assemble h5_RESULT.json from every step's artifact.

Carries the FULL enumeration (every cell at n>=50 with ratio_R > 0.5 under both tolls,
with its January split-halves, its three hunt months and its April+May out-of-sample read),
so the receipt is the complete record and the structured return is only an index to it.
"""
import gzip
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h5_lib  # noqa: E402
import h5_01_cells as C  # noqa: E402


def J(name):
    return json.load(open(os.path.join(D, name)))


R = {
    "lane": "h5",
    "question": "enumerate every cell where broker-true edge/cost > 1, or establish with numbers that none exists",
    "contract": {
        "cohort": "LIVE-EXPRESSIBLE (born_at_limit) — market orders only, the sole order type the live engine can place",
        "entry": "market at the close of path bar k=5 (decision + 5 minutes)",
        "exit": "TRAIL025 — no target, initial stop -1R, stop trails 0.25R behind running MFE",
        "gross_column": "K5_TRAIL025",
        "toll_primary": "cost_true_hour = hour-aware tick-median quoted spread + broker commission + measured live slippage",
        "toll_secondary": "cost_true = FLAT per-symbol tick-median spread + commission + slippage (the swarm's own object)",
        "ratio_primary": "ratio_R = mean(gross_R)/mean(cost_R); ratio_R > 1 <=> net R per trade > 0 at constant risk sizing",
        "ratio_secondary": "ratio_bps = mean(gross_R*rdp)/mean(cost_R*rdp) — constant NOTIONAL sizing; the swarm headline's framing",
    },
    "substrate": {
        "hunt_window": "2026-01, 2026-02, 2026-03 — 43,755 trades, 63 trading days, 24 instruments",
        "out_of_sample": "2026-04 (13,837) + 2026-05 (11,888) — built by e_build_atmkt.py from the CS_APRIL/CS_MAY S0R0 lane packs and bridge_ftmo_m1_2026{04,05}; h5 never touched either during the hunt",
        "total_5m": 69480,
        "files": ["h5_SUBSTRATE_V1.jsonl.gz", "h5_SUBSTRATE_V2.jsonl.gz", "h5_SUBSTRATE_5M.jsonl.gz"],
    },
    "reproduction": {
        "headline_reproduced": {"gross_R": 0.038342, "t_gross": 12.345, "cost_R_flat": 0.181834,
                                "edge_bps": 0.2312, "toll_bps": 2.4571, "ratio_bps": 0.0941,
                                "n": 43755, "matches_synthesis": True},
    },
    "census": {
        "axes": C.AXES,
        "groupings_singles_plus_pairs": 78,
        "flat_toll": J("h5_CELLS_CENSUS_V1.json"),
        "hour_aware_toll_same_cell_definitions": J("h5_HOURCOST_V1.json")["hour_cost_census"],
        "hour_aware_toll_cost_deciles_recut": J("h5_MAXSTAT_V1.json")["real"],
        "triples_exploratory": J("h5_DECLARED_V1.json")["triple_census"],
    },
    "book": {
        "3m_flat": J("h5_COSTCUT_V1.json")["book"],
        "3m_hour": J("h5_HOURCOST_V1.json")["book_hour_cost"],
        "5m_hour": J("h5_APRMAY_V1.json")["book_5m"],
        "oos_hour": J("h5_APRMAY_V1.json")["book_2m_oos"],
    },
    "per_symbol_flat": J("h5_RULES_V1.json")["per_symbol"],
    "per_symbol_hour": J("h5_HOURCOST_V1.json")["per_symbol"],
    "affordability_frontier": {
        "break_even_cost_R": J("h5_COSTCUT_V1.json")["break_even_cost_R"],
        "share_of_book_below_break_even": J("h5_COSTCUT_V1.json")["breakeven_share_of_book"],
        "cost_cut_sweep": J("h5_COSTCUT_V1.json")["cost_cut_sweep"],
        "by_cost_decile": J("h5_COSTCUT_V1.json")["by_cost_decile"],
        "spearman_gross_cost_trade_level": J("h5_COSTCUT_V1.json")["spearman_gross_cost_trade_level"],
    },
    "ratio_gt1_decomposition": J("h5_COSTCUT_V1.json")["ratio_gt1_decomposition_summary"],
    "declared_rules_cost_only_and_mechanism": J("h5_DECLARED_V1.json")["declared_rules"],
    "cheap_hour_per_symbol": J("h5_DECLARED_V1.json")["cheap_hour_per_symbol"],
    "index_own_open_mechanism": J("h5_ROBUST_V1.json")["index_own_open_hour"],
    "robustness_concentration": J("h5_ROBUST_V1.json")["robustness"],
    "out_of_sample": {
        "candidates_five_month_read": J("h5_APRMAY_V1.json")["candidates"],
        "survival_all_cells": J("h5_OOS_ALL_V1.json")["survival"],
        "median_oos_ratio_by_hunt_bucket": J("h5_OOS_ALL_V1.json")["median_oos_ratio_by_hunt_bucket"],
        "n_cells_gt1_in_BOTH": J("h5_OOS_ALL_V1.json")["n_cells_gt1_in_BOTH"],
        "cells_gt1_in_BOTH": J("h5_OOS_ALL_V1.json")["cells_gt1_in_BOTH"],
        "spearman_hunt_vs_oos": {
            "ratio": J("h5_OOS_ALL_V1.json")["spearman_hunt_ratio_vs_oos_ratio"],
            "net": J("h5_OOS_ALL_V1.json")["spearman_hunt_net_vs_oos_net"]},
    },
    "control_edge_vs_cost_persistence": J("h5_CONTROL_V1.json"),
    "multiplicity": {
        "flat_toll_placebo": {k: J("h5_PLACEBO_V1.json")["nulls"][k]["summary"]
                              for k in ("P1", "P2", "P3")},
        "flat_toll_real": J("h5_PLACEBO_V1.json")["real"],
        "hour_toll_westfall_young": {
            "real": J("h5_MAXSTAT_V1.json")["real"],
            "P2": {k: v for k, v in J("h5_MAXSTAT_V1.json")["P2"].items() if k != "per_rep"},
            "P3": {k: v for k, v in J("h5_MAXSTAT_V1.json")["P3"].items() if k != "per_rep"}},
    },
    "leads_stressed": J("h5_LEADS_V1.json")["leads"],
}

# ---- the FULL enumeration, both tolls, with the OOS read attached ------------
oos = {(c["grouping"], c["cell"]): c for c in
       (J("h5_OOS_ALL_V1.json")["hunt_gt1_cells_best_oos"] +
        J("h5_OOS_ALL_V1.json")["hunt_gt1_cells_worst_oos"] +
        J("h5_OOS_ALL_V1.json")["cells_gt1_in_BOTH"])}

h5_lib.COST = "cost_true_hour"
rows5 = [json.loads(x) for x in gzip.open(os.path.join(D, "h5_SUBSTRATE_5M.jsonl.gz"), "rt") if x.strip()]
oosmap = {}
for gname, g in C.groupings(rows5):
    for label, rs in g.items():
        o = [r for r in rs if r["month"] > "2026-03"]
        h = [r for r in rs if r["month"] <= "2026-03"]
        if len(h) < 50:
            continue
        s = h5_lib.cell_stats(o) if len(o) >= 30 else None
        oosmap[(gname, label)] = (None if s is None else
                                  {"n": s["n"], "gross_R": s["gross_R"], "cost_R": s["cost_R"],
                                   "net_R": s["net_R"], "ratio_R": s["ratio_R"],
                                   "t_net_day": s["t_net_day"], "days_net_pos": s["days_net_pos"],
                                   "days": s["days"]})


def enrich(cells, floor):
    out = []
    for c in cells:
        if c["n"] < 50 or not c.get("ratio_R") or c["ratio_R"] <= floor:
            continue
        d = dict(c)
        d["OOS_APR_MAY"] = oosmap.get((c["grouping"], c["cell"]))
        out.append(d)
    return out


flatcells = J("h5_CELLS_V1.json")
hourcells = J("h5_CELLS_HOUR_V1.json")
R["ENUMERATION"] = {
    "flat_toll_ratio_gt_1_n_ge_50": enrich(flatcells, 1.0),
    "flat_toll_ratio_gt_05_le_1_n_ge_50": [c for c in enrich(flatcells, 0.5) if c["ratio_R"] <= 1.0],
    "hour_toll_ratio_gt_1_n_ge_50": enrich(hourcells, 1.0),
    "triple_survivors_all_7_hour_toll": J("h5_DECLARED_V1.json")["triple_survivors_all_7"],
    "triple_top_by_t_net_day": J("h5_DECLARED_V1.json")["triple_top_by_t_net_day"],
}
R["ENUMERATION_counts"] = {k: len(v) for k, v in R["ENUMERATION"].items()}

json.dump(R, open(os.path.join(D, "h5_RESULT.json"), "w"), indent=1)
print(json.dumps(R["ENUMERATION_counts"], indent=1))
print("bytes", os.path.getsize(os.path.join(D, "h5_RESULT.json")))
