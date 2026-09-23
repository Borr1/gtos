#!/usr/bin/env python3
"""Puzzle autopsy stage 3 — THE POOL QUESTION.

Does any conditioned subpopulation of the candidate pool carry positive
expectancy that is stable across all five read months? If not, no selector
can manufacture one, and V2 must change generation/geometry, not ranking.
"""
import gzip
import json
import pickle
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

CACHE = Path("/private/tmp/w21-puzzle-cache")
MONTHS = ["feb", "apr", "may", "jun", "jul"]
rows_by_month = {}
for m in MONTHS:
    with gzip.open(CACHE / f"rows_{m}.pkl.gz", "rb") as fh:
        rows_by_month[m] = pickle.load(fh)

OUT = {}


def net(row):
    v = row.get("terminal_net_r")
    return float(v) if v is not None else None


def resolved(row):
    return row["lifecycle_label_status"].startswith("RESOLVED")


def filled(row):
    return row["lifecycle_label_status"].startswith("RESOLVED_FILLED")


# ---------- 1. every family: filled vs all-resolved expectancy, order mix ------
fam = {}
for m in MONTHS:
    for r in rows_by_month[m]:
        if not resolved(r):
            continue
        f = r["origin_family"]
        d = fam.setdefault(f, {}).setdefault(m, {"filled": [], "all": [], "ot": Counter()})
        n = net(r)
        if n is None:
            continue
        d["all"].append(n)
        d["ot"][r["proposed_order_type"]] += 1
        if filled(r):
            d["filled"].append(n)

fam_table = {}
for f, mm in fam.items():
    if not all(m in mm for m in MONTHS):
        continue
    per_month_filled = {m: (len(mm[m]["filled"]),
                            round(statistics.mean(mm[m]["filled"]), 4) if mm[m]["filled"] else None)
                        for m in MONTHS}
    per_month_all = {m: round(statistics.mean(mm[m]["all"]), 4) if mm[m]["all"] else None
                     for m in MONTHS}
    all_pooled = [x for m in MONTHS for x in mm[m]["all"]]
    filled_pooled = [x for m in MONTHS for x in mm[m]["filled"]]
    ot = Counter()
    for m in MONTHS:
        ot.update(mm[m]["ot"])
    n_res = sum(len(mm[m]["all"]) for m in MONTHS)
    n_fil = len(filled_pooled)
    fam_table[f] = {
        "n_resolved_5mo": n_res,
        "n_filled_5mo": n_fil,
        "fill_rate": round(n_fil / n_res, 3) if n_res else None,
        "mean_all_resolved": round(statistics.mean(all_pooled), 4) if all_pooled else None,
        "mean_filled": round(statistics.mean(filled_pooled), 4) if filled_pooled else None,
        "months_positive_all": sum(1 for m in MONTHS if (per_month_all[m] or 0) > 0),
        "per_month_all": per_month_all,
        "market_share": round(ot["MARKET"] / max(1, sum(ot.values())), 3),
    }
OUT["family_pool_expectancy"] = dict(sorted(
    fam_table.items(), key=lambda kv: -(kv[1]["mean_all_resolved"] or -9)))

# ---------- 2. cell search: does ANY cell survive all five months? -------------
def cell_scan(keyfn, label, min_n_per_month):
    cells = defaultdict(lambda: {m: [] for m in MONTHS})
    for m in MONTHS:
        for r in rows_by_month[m]:
            if not resolved(r):
                continue
            n = net(r)
            if n is None:
                continue
            cells[keyfn(r)][m].append(n)
    survivors, sized = [], 0
    for key, mm in cells.items():
        if min(len(mm[m]) for m in MONTHS) < min_n_per_month:
            continue
        sized += 1
        means = {m: statistics.mean(mm[m]) for m in MONTHS}
        if all(v > 0 for v in means.values()):
            pooled = [x for m in MONTHS for x in mm[m]]
            survivors.append({
                "cell": key,
                "n_5mo": len(pooled),
                "pooled_mean": round(statistics.mean(pooled), 4),
                "worst_month_mean": round(min(means.values()), 4),
                "per_month_mean": {m: round(v, 4) for m, v in means.items()},
                "per_month_n": {m: len(mm[m]) for m in MONTHS},
            })
    survivors.sort(key=lambda d: -d["pooled_mean"])
    return {
        "cells_meeting_size": sized,
        "expected_survivors_under_coinflip_null": round(sized * 0.5 ** 5, 2),
        "survivors": len(survivors),
        "top": survivors[:12],
    }


OUT["scan_family"] = cell_scan(lambda r: r["origin_family"], "family", 300)
OUT["scan_family_x_symbol"] = cell_scan(
    lambda r: f'{r["origin_family"]}|{r["symbol"]}', "fam_x_sym", 30)
OUT["scan_family_x_session"] = cell_scan(
    lambda r: f'{r["origin_family"]}|{r["utc_session"]}', "fam_x_sess", 30)
OUT["scan_family_x_side"] = cell_scan(
    lambda r: f'{r["origin_family"]}|{r["side"]}', "fam_x_side", 100)
OUT["scan_symbol"] = cell_scan(lambda r: r["symbol"], "symbol", 200)

# ---------- 3. within-family ranking skill ------------------------------------
within = {}
for f in ("liquidity_sweep_reclaim", "structural_distance_extreme",
          "session_open_range_break", "displacement_continuation",
          "current_fvg_fill", "current_breaker_re_entry"):
    per_m = {}
    for m in MONTHS:
        pairs = [(r["pred_month_boundary"], net(r)) for r in rows_by_month[m]
                 if r["origin_family"] == f and r.get("pred_month_boundary") is not None
                 and resolved(r) and net(r) is not None]
        if len(pairs) > 200:
            p = np.array([a for a, _ in pairs]); n = np.array([b for _, b in pairs])
            k = max(1, len(pairs) // 10)
            order = np.argsort(p)
            per_m[m] = {"n": len(pairs), "rho": round(float(spearmanr(p, n).statistic), 4),
                        "top_decile_mean": round(float(n[order[-k:]].mean()), 4)}
    within[f] = per_m
OUT["within_family_ranking_skill"] = within

# ---------- 4. what the traded slice would look like at zero selection --------
# random-pick baseline: mean over MARKET+eligible candidates
base = {}
for m in MONTHS:
    el = [r for r in rows_by_month[m]
          if r.get("pred_month_boundary") is not None and resolved(r) and net(r) is not None]
    mk = [r for r in el if r["proposed_order_type"] == "MARKET"]
    base[m] = {
        "eligible_resolved": len(el),
        "eligible_mean_net": round(statistics.mean([net(r) for r in el]), 4) if el else None,
        "market_only_n": len(mk),
        "market_only_mean_net": round(statistics.mean([net(r) for r in mk]), 4) if mk else None,
    }
OUT["eligible_pool_baseline"] = base

(CACHE / "POOL_ANSWERS.json").write_text(json.dumps(OUT, indent=1, sort_keys=True, default=str))
print(json.dumps({k: OUT[k] for k in ("scan_family", "scan_family_x_symbol",
                                      "scan_family_x_session", "scan_family_x_side",
                                      "scan_symbol", "eligible_pool_baseline")},
                 indent=1, sort_keys=True, default=str))
