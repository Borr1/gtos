"""d5-02b — the achievable action set, priced correctly.

Corrections to the first pass:
  * an exit at the confirm-minute close cannot book worse than -1 R, because the stop is resting
    at -1 R.  Every exit arm is clamped at max(c0, -1.0).
  * the estate's honest-limit contract fills a row at ``e`` even when the market was ALREADY past
    ``e`` at T (a marketable limit -> a fill it cannot have).  Arms are reported both on the whole
    roster and restricted to mkt_r0 >= 0, where the resting fill at ``e`` is real.
  * adds the PRE-decision comparator: refusing on mkt_r0, which is knowable AT T and therefore
    fully achievable by simply not placing the order.
"""
import json, sys
import numpy as np
sys.path.insert(0, "/tmp/d5")
from d5_lib import *

ACC = []
for wi, w in enumerate(WINDOWS):
    D = load(w)
    n = D["g"].size
    ACC.append({k: D[k] for k in ("g", "net", "cost_r", "c0", "mkt_r0", "j", "ra_g", "ra_net",
                                  "reason", "sym", "fam")}
               | {"day": D["dayi"] + 1000 * wi, "win": np.full(n, wi)})
A = {k: np.concatenate([a[k] for a in ACC]) for k in ACC[0]}
N = A["g"].size
g = A["g"]; net = A["net"]; c0 = A["c0"]; mk = A["mkt_r0"]; day = A["day"]; cost = A["cost_r"]
prefilled = A["j"] == 0
honest = mk >= 0.0                # the resting fill at e is physically reachable
R = {"N": int(N), "honest_share": float(honest.mean())}


def arm(gv, nv, tag, mask=None):
    m = np.ones(N, bool) if mask is None else mask
    return {"tag": tag, "n": int(m.sum()),
            "pool_gross": float(gv[m].mean()), "pool_net": float(nv[m].mean()),
            "ci_gross": dayblock_ci(gv[m], day[m]),
            "total_gross_R": float(gv[m].sum()), "total_net_R": float(nv[m].sum())}


for scope, smask in (("ALL_ROSTER", None), ("HONEST_FILLS_mkt_r0>=0", honest)):
    out = {}
    out["P0_baseline"] = arm(g, net, "roster as walked", smask)
    for th in (-0.15, -0.05, 0.0):
        ad = c0 <= th
        # oracle refusal (NOT achievable: 100 % of these rows are already filled)
        out["P1_oracle_refuse@%.2f" % th] = arm(np.where(ad, 0.0, g), np.where(ad, 0.0, net),
                                                "refuse c0<=th (unachievable)", smask)
        # achievable: exit at the confirm close, loss clamped by the resting stop
        ex = np.maximum(c0, -1.0)
        m3 = ad & prefilled
        g3 = np.where(m3, ex, g); n3 = np.where(m3, ex - cost, net)
        out["P3c_exit_at_T1_clamped@%.2f" % th] = arm(g3, n3,
                                                      "already-filled adverse rows exit at close of [T,T+1m), clamped at -1R", smask)
        # achievable: re-anchor at market at T+1m instead of holding the adverse fill
        rg = np.where(np.isfinite(A["ra_g"]), A["ra_g"], 0.0)
        rn = np.where(np.isfinite(A["ra_net"]), A["ra_net"], 0.0)
        g5 = np.where(m3, ex + rg, g); n5 = np.where(m3, ex - cost + rn, net)
        out["P5c_exit_then_reenter@%.2f" % th] = arm(g5, n5,
                                                     "exit at T+1m then re-enter at market with the same risk distance", smask)
    # PRE-decision comparator: refuse on the decision anchor, knowable AT T
    for th in (0.0, -0.25, -0.5, -1.0):
        adp = mk <= th
        out["Q_PRE_refuse_mkt_r0<=%.2f" % th] = arm(np.where(adp, 0.0, g), np.where(adp, 0.0, net),
                                                    "refuse at T on the decision anchor (fully achievable)", smask)
    R[scope] = out

# how much of the oracle refusal's value is already available from the PRE anchor?
ad = c0 <= -0.15
adp = mk < 0.0
R["overlap"] = {
    "n_c0_adverse": int(ad.sum()),
    "n_pre_adverse_mkt_r0<0": int(adp.sum()),
    "n_both": int((ad & adp).sum()),
    "share_of_c0_adverse_already_flagged_at_T": float((ad & adp).sum() / ad.sum()),
    "share_of_c0_adverse_R_already_flagged_at_T": float(g[ad & adp].sum() / g[ad].sum()),
    "gross_c0_adverse_and_pre_clean": float(g[ad & ~adp].mean()),
    "n_c0_adverse_and_pre_clean": int((ad & ~adp).sum()),
    "gross_pre_adverse": float(g[adp].mean()),
}
# conditional: inside the PRE-clean population, what is the confirm minute still worth?
cl = ~adp
for th in (-0.15, -0.05):
    a2 = cl & (c0 <= th)
    R.setdefault("conditional_on_pre_clean", {})["c0<=%.2f" % th] = {
        "n_adverse": int(a2.sum()), "gross_adverse": float(g[a2].mean()),
        "ci": dayblock_ci(g[a2], day[a2]),
        "n_kept": int((cl & ~(c0 <= th)).sum()),
        "gross_kept": float(g[cl & ~(c0 <= th)].mean()),
        "prefilled_share_of_adverse": float(prefilled[a2].mean()),
        "value_per_opportunity_if_refusable": float(-g[a2].sum() / N),
    }
json.dump(R, open("/tmp/d5/out/D5_02B_ARMS.json", "w"), indent=1, default=float)
for scope in ("ALL_ROSTER", "HONEST_FILLS_mkt_r0>=0"):
    print("==", scope, "n=", R[scope]["P0_baseline"]["n"])
    for k, v in R[scope].items():
        print("  %-38s gross %9.5f net %9.5f" % (k, v["pool_gross"], v["pool_net"]))
print(json.dumps(R["overlap"], indent=1, default=float))
print(json.dumps(R["conditional_on_pre_clean"], indent=1, default=float))
