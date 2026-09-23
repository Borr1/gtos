#!/usr/bin/env python3
"""B1 — composition control.

The tick window is 5 weeks of a 5-month population. Two compositions can differ between the window
and the full population, and both would bias a transferred conditional:

  (a) the BARRIER mix (stop / target / time-stop shares)  -- handled by using each arm's own
      five-month barrier shares in the deduction (the adjudication's own method), and
  (b) the SYMBOL mix -- NOT handled anywhere yet, and it matters here because the LIMIT arm is far
      more concentrated (crypto-heavy) than the MARKET arm.

This script builds the five-month per-arm symbol x state counts straight from the puzzle cache
(the population Lane 1 measured its edge on) and reweights the in-window measured per-symbol stop
conditional onto the five-month symbol mix.

Writes B1_COMPOSITION.json.
"""
from __future__ import annotations

import gzip
import json
import pickle
from collections import Counter

import numpy as np
import pandas as pd

OUT = "/Users/borr/.claude/jobs/adb9e69b/tmp/b1"
CACHE = "/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz"
MONTHS = ["feb", "apr", "may", "jun", "jul"]
LIMIT_FAMILIES = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
STATE_OF = {"RESOLVED_FILLED_STOP": "STOP", "RESOLVED_FILLED_TARGET": "TARGET",
            "RESOLVED_FILLED_TIME_STOP": "TIME_STOP"}

# ---- 1. five-month per-arm symbol x state counts -----------------------------
cnt = {"LIMIT": Counter(), "MARKET": Counter()}
state_cnt = {"LIMIT": Counter(), "MARKET": Counter()}
ot_check = Counter()
for m in MONTHS:
    for r in pickle.load(gzip.open(CACHE.format(m=m), "rb")):
        st = STATE_OF.get(str(r.get("lifecycle_label_status")))
        if st is None:
            continue
        fam = str(r.get("origin_family"))
        arm = "LIMIT" if fam in LIMIT_FAMILIES else "MARKET"
        ot_check[(arm, str(r.get("proposed_order_type")))] += 1
        cnt[arm][(str(r["symbol"]), st)] += 1
        state_cnt[arm][st] += 1

R = {"schema": "b1_composition_control",
     "family_to_order_type_check": {f"{a}|{o}": n for (a, o), n in sorted(ot_check.items())},
     "five_month_resolved": {a: int(sum(state_cnt[a].values())) for a in cnt},
     "five_month_state_counts": {a: dict(state_cnt[a]) for a in cnt}}

# ---- 2. reweight the measured in-window stop conditional to the 5-month symbol mix ----
for arm, tag in (("MARKET", "ctrlB_lg_market"), ("LIMIT", "limit")):
    D = pd.read_pickle(f"{OUT}/legs_{tag}.pkl")
    s = D[(D.state == "STOP") & (D.found_cross == 1)]
    per_sym = s.groupby("symbol").exit_opt_at_cross_r.agg(["mean", "size"])
    # five-month STOP counts by symbol for this arm
    five = pd.Series({sym: n for (sym, st), n in cnt[arm].items() if st == "STOP"})
    # in-window STOP counts by symbol
    win = per_sym["size"]
    common = per_sym.index.intersection(five.index)
    w5 = five.reindex(common).astype(float)
    ww = win.reindex(common).astype(float)
    mu = per_sym["mean"].reindex(common).astype(float)
    raw = float((mu * ww).sum() / ww.sum())
    rew = float((mu * w5).sum() / w5.sum())
    cov5 = float(w5.sum() / five.sum())
    R[f"{arm}_stop_conditional"] = {
        "in_window_raw": raw,
        "reweighted_to_five_month_symbol_mix": rew,
        "delta": rew - raw,
        "n_symbols_measured": int(len(common)),
        "five_month_stop_rows_covered_frac": cov5,
        "top_window_share": {k: float(v) for k, v in
                             (ww / ww.sum()).sort_values(ascending=False).head(8).items()},
        "top_five_month_share": {k: float(v) for k, v in
                                 (w5 / w5.sum()).sort_values(ascending=False).head(8).items()},
    }

# ---- 3. barrier-mix check: in-window vs five-month, per arm ----
for arm, tag in (("MARKET", "ctrlB_lg_market"), ("LIMIT", "limit")):
    D = pd.read_pickle(f"{OUT}/legs_{tag}.pkl")
    win = {st: float((D.state == st).mean()) for st in ["STOP", "TARGET", "TIME_STOP"]}
    tot = sum(state_cnt[arm].values())
    five = {st: state_cnt[arm][st] / tot for st in ["STOP", "TARGET", "TIME_STOP"]}
    R[f"{arm}_barrier_mix"] = {"in_window": win, "five_month": five,
                               "abs_delta_stop_share": abs(win["STOP"] - five["STOP"])}

json.dump(R, open(f"{OUT}/B1_COMPOSITION.json", "w"), indent=1)
print(json.dumps(R, indent=1))
