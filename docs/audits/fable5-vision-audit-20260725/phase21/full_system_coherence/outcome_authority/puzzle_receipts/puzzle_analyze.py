#!/usr/bin/env python3
"""Puzzle autopsy stage 2: the answer battery over the five-month cache."""
import gzip
import json
import pickle
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

CACHE = Path("/private/tmp/w21-puzzle-cache")
OUT = {}

RESOLVED = {"RESOLVED_NO_FILL": 0, "RESOLVED_FILLED_TARGET": 1, "RESOLVED_FILLED_STOP": 1,
            "RESOLVED_FILLED_TIME_STOP": 1}


def net(row):
    v = row.get("terminal_net_r")
    return float(v) if v is not None else None


months = ["feb", "apr", "may", "jun", "jul"]
rows_by_month = {}
for m in months:
    with gzip.open(CACHE / f"rows_{m}.pkl.gz", "rb") as fh:
        rows_by_month[m] = pickle.load(fh)

# ---- 1. cell stories: UK100|SDE and top cells per month -----------------------
cell = {}
for m in months:
    rows = rows_by_month[m]
    for r in rows:
        if r["origin_family"] != "structural_distance_extreme":
            continue
        key = r["symbol"]
        n = net(r)
        c = cell.setdefault(m, {}).setdefault(key, [0, 0.0, Counter()])
        if n is not None and r["lifecycle_label_status"].startswith("RESOLVED_FILLED"):
            c[0] += 1
            c[1] += n
            c[2][r["lifecycle_label_status"].replace("RESOLVED_FILLED_", "")] += 1
uk = {m: {"n": v.get("UK100", [0, 0, Counter()])[0],
          "net": round(v.get("UK100", [0, 0, Counter()])[1], 2),
          "mix": dict(v.get("UK100", [0, 0, Counter()])[2])} for m, v in cell.items()}
OUT["uk100_sde_population_by_month"] = uk

# ---- 2. ranking health: spearman + decile spread per month --------------------
from scipy.stats import spearmanr  # noqa

rank_health = {}
for m in months:
    el = [r for r in rows_by_month[m] if r.get("pred_month_boundary") is not None]
    res = [(r["pred_month_boundary"], net(r)) for r in el
           if net(r) is not None and r["lifecycle_label_status"].startswith("RESOLVED")]
    preds = np.array([p for p, _ in res]); nets = np.array([n for _, n in res])
    rho = float(spearmanr(preds, nets).statistic) if len(res) > 10 else None
    order = np.argsort(preds)
    k = len(res) // 10
    rank_health[m] = {
        "n_resolved": len(res),
        "spearman": round(rho, 4) if rho is not None else None,
        "top_decile_mean_net": round(float(nets[order[-k:]].mean()), 4) if k else None,
        "bottom_decile_mean_net": round(float(nets[order[:k]].mean()), 4) if k else None,
        "top_decile_mean_pred": round(float(preds[order[-k:]].mean()), 4) if k else None,
    }
OUT["ranking_health_population"] = rank_health

# ---- 3. winner's curse: top-1 vs ranks 2-5 within window ----------------------
wc = {}
for m in months:
    el = [r for r in rows_by_month[m] if r.get("pred_month_boundary") is not None]
    by_w = defaultdict(list)
    for r in el:
        n = net(r)
        if n is not None and r["lifecycle_label_status"].startswith("RESOLVED"):
            by_w[r["decision_window_id"]].append((r["pred_month_boundary"], n))
    top1, rest = [], []
    for w, items in by_w.items():
        if len(items) < 3:
            continue
        items.sort(key=lambda t: -t[0])
        top1.append(items[0][1])
        rest.extend(n for _p, n in items[1:5])
    wc[m] = {"windows": len(top1),
             "top1_mean_net": round(statistics.mean(top1), 4) if top1 else None,
             "rank2to5_mean_net": round(statistics.mean(rest), 4) if rest else None}
OUT["winners_curse_top1_vs_rank2to5"] = wc

# ---- 4. family completion by month (filled resolved only) ---------------------
fam_comp = {}
for m in months:
    for r in rows_by_month[m]:
        st = r["lifecycle_label_status"]
        if not st.startswith("RESOLVED_FILLED"):
            continue
        f = r["origin_family"]
        c = fam_comp.setdefault(f, {}).setdefault(m, Counter())
        c[st.replace("RESOLVED_FILLED_", "")] += 1
fam_rates = {}
for f, mm in fam_comp.items():
    fam_rates[f] = {}
    for m, c in mm.items():
        t = sum(c.values())
        fam_rates[f][m] = {"n": t, "tgt": round(c["TARGET"] / t, 3),
                           "stp": round(c["STOP"] / t, 3), "ts": round(c["TIME_STOP"] / t, 3)}
OUT["family_completion"] = {f: fam_rates[f] for f in
                            ("liquidity_sweep_reclaim", "structural_distance_extreme",
                             "session_open_range_break", "displacement_continuation")
                            if f in fam_rates}

# ---- 5. LSR: net by month + which symbols in jun/jul --------------------------
lsr = {}
for m in months:
    rr = [r for r in rows_by_month[m] if r["origin_family"] == "liquidity_sweep_reclaim"
          and r["lifecycle_label_status"].startswith("RESOLVED_FILLED")]
    nets = [net(r) for r in rr]
    lsr[m] = {"n": len(rr), "net_sum": round(sum(nets), 2),
              "mean": round(statistics.mean(nets), 4) if nets else None}
OUT["lsr_population_filled"] = lsr

# ---- 6. concentration: top symbol_x_family cell among ELIGIBLE top-preds ------
conc = {}
for m in months:
    el = [r for r in rows_by_month[m] if r.get("pred_month_boundary") is not None]
    by_w = defaultdict(list)
    for r in el:
        by_w[r["decision_window_id"]].append(r)
    tops = []
    for w, items in by_w.items():
        items.sort(key=lambda r: -r["pred_month_boundary"])
        if items[0]["pred_month_boundary"] >= 0.10:
            tops.append(items[0]["symbol"] + "|" + items[0]["origin_family"])
    c = Counter(tops)
    conc[m] = {"threshold_windows": len(tops), "top3_cells": c.most_common(3)}
OUT["top_of_book_cell_concentration"] = conc

# ---- 7. SD5 brake replay on june/july day series ------------------------------
jj = json.load(open("/private/tmp/w21-market-top-junjul-r4/JUNE_JULY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json"))
series = []
for day in sorted(jj["days"]):
    p = jj["days"][day]["policies"]["market_top_abstain"]["portfolio"]
    series.append((day, float(p.get("worst_case_net_r") or 0.0)))
for k, x in ((5, 3.0), (5, 5.0), (10, 3.0)):
    kept, stood = 0.0, []
    for i, (day, v) in enumerate(series):
        trail = sum(v2 for _d, v2 in series[max(0, i - k):i])
        if trail < -x:
            stood.append(day)
        else:
            kept += v
    OUT[f"sd5_brake_k{k}_x{int(x)}"] = {"kept_net": round(kept, 2), "days_stood_down": len(stood)}
OUT["no_brake_net"] = round(sum(v for _d, v in series), 2)

print(json.dumps(OUT, indent=1, sort_keys=True, default=str))
(Path("/private/tmp/w21-puzzle-cache/ANSWERS.json")).write_text(
    json.dumps(OUT, indent=1, sort_keys=True, default=str))
