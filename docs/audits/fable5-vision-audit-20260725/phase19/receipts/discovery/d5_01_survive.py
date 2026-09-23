"""d5-01 — does the separator survive the object change (pool -> roster)?

Reports, per window and pooled over 8 open windows:
  * roster census (fills, resolutions, prefilled share)
  * Cohen's d and AUC of c0_close_fav_r on target-first vs stop-first
  * the cohort economics x4 published, re-measured on the roster
"""
import json, sys
import numpy as np
sys.path.insert(0, "/tmp/d5")
from d5_lib import *

R = {"windows": {}, "pooled": {}}
POP = {}


def pop_masks(D):
    return {
        "ALL_ROSTER": np.ones(D["g"].size, bool),
        "FILLED": D["filled"],
        "RESOLVED": D["resolved"],
        "CLEAN_RESOLVED": D["resolved"] & ~D["past_stop"] &
                          (D["fam"] != D["_meta"]["famids"].get("current_breaker_re_entry", -999)),
        "RESOLVED_FILL_LE2M": D["resolved"] & (D["j"] >= 0) & (D["j"] <= 1),
        "RESOLVED_J0": D["resolved"] & (D["j"] == 0),
        "RESOLVED_J1PLUS": D["resolved"] & (D["j"] >= 1),
    }


agg = {k: {"c0_t": [], "c0_s": []} for k in
       ["ALL_ROSTER", "FILLED", "RESOLVED", "CLEAN_RESOLVED", "RESOLVED_FILL_LE2M",
        "RESOLVED_J0", "RESOLVED_J1PLUS"]}
econ_pool = {}

for w in WINDOWS:
    D = load(w)
    n = D["g"].size
    m = pop_masks(D)
    row = {
        "n_roster_k15": D["_meta"]["n_roster_k15"], "n_kept": n,
        "drops": D["_meta"]["drops"],
        "fill_rate": float(D["filled"].mean()),
        "prefilled_share_of_fills": float(D["prefilled"][D["filled"]].mean()),
        "resolved_share": float(D["resolved"].mean()),
        "target_share_of_resolved": float(D["is_target"][D["resolved"]].mean()),
        "past_stop_share": float(D["past_stop"].mean()),
        "gross_mean_all": float(D["g"].mean()),
        "gross_mean_filled": float(D["g"][D["filled"]].mean()),
        "cost_mean_filled": float(D["cost_r"][D["filled"]].mean()),
        "net_mean_filled": float(D["net"][D["filled"]].mean()),
        "sep": {},
    }
    for k, mm in m.items():
        if k in ("ALL_ROSTER", "FILLED"):
            # d on resolved subset only (needs a label)
            mm2 = mm & D["resolved"]
        else:
            mm2 = mm
        t = D["c0"][mm2 & D["is_target"]]
        s = D["c0"][mm2 & (~D["is_target"])]
        agg[k]["c0_t"].append(t); agg[k]["c0_s"].append(s)
        row["sep"][k] = {"n_target": int(t.size), "n_stop": int(s.size),
                         "cohens_d": cohens_d(t, s), "auc": auc(t, s),
                         "mean_target": float(t.mean()) if t.size else None,
                         "mean_stop": float(s.mean()) if s.size else None}
    # economics of the split, on the whole roster and on fills
    for tag, mask in (("ALL_ROSTER", np.ones(n, bool)), ("FILLED", D["filled"])):
        for th in (-0.15, -0.05, 0.0):
            lo = mask & (D["c0"] <= th)
            hi = mask & (D["c0"] > th)
            key = "%s@%.2f" % (tag, th)
            row.setdefault("split_econ", {})[key] = {
                "n_adverse": int(lo.sum()), "R_adverse": float(D["g"][lo].mean()) if lo.sum() else None,
                "net_adverse": float(D["net"][lo].mean()) if lo.sum() else None,
                "n_ok": int(hi.sum()), "R_ok": float(D["g"][hi].mean()) if hi.sum() else None,
                "net_ok": float(D["net"][hi].mean()) if hi.sum() else None,
                "gap": (float(D["g"][hi].mean() - D["g"][lo].mean()) if (lo.sum() and hi.sum()) else None),
            }
    R["windows"][w] = row
    econ_pool[w] = {"g": D["g"], "c0": D["c0"], "filled": D["filled"], "net": D["net"],
                    "day": D["dayi"] + 1000 * WINDOWS.index(w)}
    print(w, "n", n, "d(RESOLVED)", round(row["sep"]["RESOLVED"]["cohens_d"], 4),
          "auc", round(row["sep"]["RESOLVED"]["auc"], 4),
          "d(J0)", round(row["sep"]["RESOLVED_J0"]["cohens_d"], 4),
          "d(J1+)", round(row["sep"]["RESOLVED_J1PLUS"]["cohens_d"], 4), flush=True)

for k, v in agg.items():
    t = np.concatenate(v["c0_t"]); s = np.concatenate(v["c0_s"])
    R["pooled"][k] = {"n_target": int(t.size), "n_stop": int(s.size),
                      "cohens_d": cohens_d(t, s), "auc": auc(t, s),
                      "mean_target": float(t.mean()), "mean_stop": float(s.mean())}

# pooled economics of the split with day-block CI
gg = np.concatenate([econ_pool[w]["g"] for w in WINDOWS])
nn = np.concatenate([econ_pool[w]["net"] for w in WINDOWS])
cc = np.concatenate([econ_pool[w]["c0"] for w in WINDOWS])
ff = np.concatenate([econ_pool[w]["filled"] for w in WINDOWS])
dd = np.concatenate([econ_pool[w]["day"] for w in WINDOWS])
R["pooled_econ"] = {}
for tag, mask in (("ALL_ROSTER", np.ones(gg.size, bool)), ("FILLED", ff)):
    for th in (-0.15, -0.05, 0.0):
        lo = mask & (cc <= th); hi = mask & (cc > th)
        R["pooled_econ"]["%s@%.2f" % (tag, th)] = {
            "n_adverse": int(lo.sum()), "R_adverse": float(gg[lo].mean()),
            "ci_adverse": dayblock_ci(gg[lo], dd[lo]),
            "net_adverse": float(nn[lo].mean()),
            "n_ok": int(hi.sum()), "R_ok": float(gg[hi].mean()),
            "ci_ok": dayblock_ci(gg[hi], dd[hi]), "net_ok": float(nn[hi].mean()),
            "gap": float(gg[hi].mean() - gg[lo].mean())}
R["pooled_census"] = {"n": int(gg.size), "gross_all": float(gg.mean()),
                      "gross_filled": float(gg[ff].mean()), "net_filled": float(nn[ff].mean()),
                      "fill_rate": float(ff.mean())}
json.dump(R, open("/tmp/d5/out/D5_01_SURVIVE.json", "w"), indent=1, default=float)
print(json.dumps(R["pooled"], indent=1, default=float))
print(json.dumps(R["pooled_econ"], indent=1, default=float))
