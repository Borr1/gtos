#!/usr/bin/env python3
"""x4 step 4 — explicit rules, stability, and the missing-minute substrate correction.

SUBSTRATE DEFECT FIRST: the M1 path sidecar's bar 1 is [T+1m, T+2m). The minute [T, T+1m)
is in NO prior lane's substrate. So `bars_to_entry_touch == 1` is not "touched within 60 s";
it is "touched between 60 and 120 s", and every candidate whose entry was crossed inside the
FIRST minute is invisible. Measure the true rate and the size of the miss.

Then the rules. A rule here is a REFUSAL: skipped candidates book exactly 0.0 R (you did not
trade), which is the l8 convention, so pool-level R per candidate-opportunity is comparable.
Everything a rule reads is stamped PRE (t < T) or CONFIRM (t in [T, T+1m), legal for an order
placed at T+1m -- the live book already polls at 60 s, run_book.py:99).
"""
from __future__ import annotations
import json, os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import x4_lib as X

recs = X.load_joined()
O = X.outcomes(recs)
n_all = len(recs)
take = O["takeable"]; honr = np.nan_to_num(O["honr"], nan=0.0); hon = O["hon"]
days = np.array([r["_day"] for r in recs])
sym = np.array([r["symbol"] for r in recs])
fam = np.array([str(r.get("origin_family")) for r in recs])
dnum = np.array([int(d[-2:]) for d in days])
res = {}

F = lambda nm: X.col(recs, nm)
c0c = F("c0_close_fav_r"); c0a = F("c0_adv_r")
geo = F("stop_dist_over_bar_range"); atr = F("atr16_m15_r")
b1 = O["bar1"]

# ---------------------------------------------------------------- substrate correction
touched_mm = np.isfinite(c0a) & (c0a <= 0.0)
res["MISSING_MINUTE"] = {
    "definition": "entry level traded inside [T, T+1m) -- the minute the path sidecar omits",
    "n_joined": n_all,
    "c0_bar_present": int(np.isfinite(c0a).sum()),
    "n_touched_in_missing_minute": int(touched_mm.sum()),
    "share_of_joined": round(float(touched_mm.mean()), 5),
    "sidecar_bar1_share": round(float(b1.mean()), 5),
    "true_first_120s_share": round(float((touched_mm | b1).mean()), 5),
    "invisible_to_prior_lanes_n": int((touched_mm & ~b1).sum()),
    "honr_of_invisible_cohort": round(float(np.nanmean(honr[touched_mm & ~b1])), 5),
    "honr_of_sidecar_bar1": round(float(np.nanmean(honr[b1])), 5),
    "honr_of_neither": round(float(np.nanmean(honr[~touched_mm & ~b1])), 5),
}
print(json.dumps(res["MISSING_MINUTE"], indent=1), flush=True)


def evaluate(keep, label, pop=None):
    pop = np.ones(n_all, bool) if pop is None else pop
    k = keep & pop
    booked = np.where(k, honr, 0.0)
    nk = int(k.sum()); npop = int(pop.sum())
    d = {"rule": label, "n_pop": npop, "n_kept": nk, "kept_share": round(nk / npop, 4),
         "mean_honr_kept": round(float(np.nanmean(honr[k])), 5) if nk else None,
         "pool_r_per_candidate": round(float(booked[pop].sum() / npop), 5),
         "total_r": round(float(booked[pop].sum()), 2),
         "target_rate_kept": round(float((hon[k] == "target").mean()), 4) if nk else None,
         "stop_rate_kept": round(float((hon[k] == "stop").mean()), 4) if nk else None}
    m, lo, hi, p = X.day_block_boot(booked[pop], days[pop])
    d["pool_boot"] = {"mean": round(m, 5), "lo95": round(lo, 5), "hi95": round(hi, 5),
                      "p_le_0": round(p, 4)}
    if nk > 200:
        m2, lo2, hi2, p2 = X.day_block_boot(honr[k], days[k])
        d["kept_boot"] = {"mean": round(m2, 5), "lo95": round(lo2, 5), "hi95": round(hi2, 5),
                          "p_le_0": round(p2, 4)}
    for nm, msk in (("odd_days", dnum % 2 == 1), ("even_days", dnum % 2 == 0),
                    ("first_half", dnum <= 15), ("second_half", dnum > 15)):
        pp = pop & msk
        if pp.sum() > 200:
            d[nm] = {"n_pop": int(pp.sum()), "n_kept": int((k & msk).sum()),
                     "pool_r": round(float(np.where(k & msk, honr, 0.0)[pp].sum() / pp.sum()), 5),
                     "kept_mean": round(float(np.nanmean(honr[k & msk])), 5) if (k & msk).sum() > 20 else None}
    return d


rules = [evaluate(np.ones(n_all, bool), "A0_take_everything"),
         evaluate(np.ones(n_all, bool), "A0_take_everything_TAKEABLE", pop=take),
         evaluate(~b1, "B_l8_refuse_sidecar_bar1"),
         evaluate(~b1, "B_l8_refuse_sidecar_bar1_TAKEABLE", pop=take),
         evaluate(~(b1 | touched_mm), "B2_refuse_any_touch_in_first_2min")]

res["C0_SWEEP"] = []
for th in [-0.60, -0.50, -0.40, -0.30, -0.25, -0.20, -0.15, -0.10, -0.05, 0.0]:
    keep = ~(np.isfinite(c0c) & (c0c <= th))
    r = evaluate(keep, "C_c0_close_fav_gt_%.2f" % th)
    rt = evaluate(keep, "C_c0_close_fav_gt_%.2f_TAKEABLE" % th, pop=take)
    res["C0_SWEEP"].append({"theta": th, "all": r, "takeable": rt})
    print("C theta=%6.2f  kept=%5d (%.3f)  poolR=%8.5f  keptMean=%8.5f  [%s,%s]" % (
        th, r["n_kept"], r["kept_share"], r["pool_r_per_candidate"], r["mean_honr_kept"],
        r["pool_boot"]["lo95"], r["pool_boot"]["hi95"]), flush=True)

res["GEO_SWEEP"] = []
for th in [0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]:
    keep = ~(np.isfinite(geo) & (geo <= th))
    r = evaluate(keep, "G_geo_gt_%.2f" % th)
    res["GEO_SWEEP"].append({"theta": th, "all": r})
    print("G theta=%5.2f  kept=%5d (%.3f)  poolR=%8.5f  keptMean=%8.5f" % (
        th, r["n_kept"], r["kept_share"], r["pool_r_per_candidate"], r["mean_honr_kept"]), flush=True)

COMBOS = {
    "X4_A_confirm_only": ~(np.isfinite(c0c) & (c0c <= -0.15)),
    "X4_B_geo_only": ~(np.isfinite(geo) & (geo <= 0.60)),
    "X4_C_confirm_AND_geo": ~((np.isfinite(c0c) & (c0c <= -0.15)) | (np.isfinite(geo) & (geo <= 0.60))),
    "X4_D_confirm_geo_atr": ~((np.isfinite(c0c) & (c0c <= -0.15)) |
                              (np.isfinite(geo) & (geo <= 0.60)) |
                              (np.isfinite(atr) & (atr >= 2.0))),
    "X4_E_confirm_strict": ~(np.isfinite(c0c) & (c0c <= -0.05)),
    "L8_plus_confirm": ~(b1 | (np.isfinite(c0c) & (c0c <= -0.15))),
}
res["COMBOS"] = {}
for nm, keep in COMBOS.items():
    r = evaluate(keep, nm)
    res["COMBOS"][nm] = r
    imp_s = sum(1 for s in np.unique(sym)
                if np.where(keep & (sym == s), honr, 0.0).mean() > honr[sym == s].mean())
    fams = [s for s in np.unique(fam) if (fam == s).sum() > 100]
    imp_f = sum(1 for s in fams
                if np.where(keep & (fam == s), honr, 0.0).mean() > honr[fam == s].mean())
    r["symbols_improved"] = "%d/%d" % (imp_s, len(np.unique(sym)))
    r["families_improved"] = "%d/%d" % (imp_f, len(fams))
    print("%-24s kept=%5d (%.3f) poolR=%8.5f [%s,%s] p=%s keptMean=%8.5f sym %s fam %s" % (
        nm, r["n_kept"], r["kept_share"], r["pool_r_per_candidate"],
        r["pool_boot"]["lo95"], r["pool_boot"]["hi95"], r["pool_boot"]["p_le_0"],
        r["mean_honr_kept"], r["symbols_improved"], r["families_improved"]), flush=True)

res["RULES"] = rules
for r in rules:
    print("%-42s kept=%5d poolR=%9.5f keptMean=%9s odd=%s even=%s" % (
        r["rule"], r["n_kept"], r["pool_r_per_candidate"], r["mean_honr_kept"],
        r.get("odd_days", {}).get("pool_r"), r.get("even_days", {}).get("pool_r")), flush=True)

with open(os.path.join(D, "X4_RULES_V1.json"), "w") as f:
    json.dump(res, f, indent=1)
print("wrote X4_RULES_V1.json")
