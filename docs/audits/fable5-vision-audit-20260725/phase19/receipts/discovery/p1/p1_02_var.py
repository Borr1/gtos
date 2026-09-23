"""p1 step 2 — IS THERE ANYTHING TO SELECT ON?  Variance decomposition of cell means.

For any cell partition, the observed spread of cell means contains real between-cell
dispersion PLUS sampling noise:

    var(observed cell means) = var(true cell means) + E[SE^2],   SE^2 = s_i^2 / n_i

so   true_sd^2 = var(obs) - mean(s_i^2/n_i)   (clipped at 0).

Reported per window, per cell kind, for GROSS and for COST, with the ratio
true_sd(gross) / true_sd(cost) -- the honest 'how much edge dispersion exists
relative to fee dispersion' number.  Also: signal share = true_var / obs_var.
"""
from __future__ import annotations
import numpy as np, json, sys
sys.path.insert(0, "/tmp/p1")
import p1_lib as L

ws, SYMS = L.load_all()

def kk(w, kind):
    if kind == "instrument":    return w.sym.astype(np.int64)
    if kind == "family":        return w.fam.astype(np.int64)
    if kind == "broker_hour":   return w.bhour.astype(np.int64)
    if kind == "inst_x_family": return w.sym.astype(np.int64) * 100 + w.fam
    if kind == "inst_x_hour":   return w.sym.astype(np.int64) * 100 + w.bhour
    raise KeyError

def decomp(keys, x, minn):
    u, inv = np.unique(keys, return_inverse=True)
    n = np.bincount(inv, minlength=len(u)).astype(float)
    s1 = np.bincount(inv, weights=x, minlength=len(u))
    s2 = np.bincount(inv, weights=x * x, minlength=len(u))
    m = s1 / n
    var_i = np.maximum(s2 / n - m * m, 0.0) * n / np.maximum(n - 1, 1)
    ok = n >= minn
    if ok.sum() < 3:
        return None
    m = m[ok]; n = n[ok]; var_i = var_i[ok]
    obs = float(np.var(m, ddof=1))
    noise = float(np.mean(var_i / n))
    true = max(obs - noise, 0.0)
    return dict(k=int(ok.sum()), n=int(n.sum()), obs_var=obs, noise_var=noise,
                true_var=true, obs_sd=obs ** .5, true_sd=true ** .5,
                signal_share=(true / obs if obs > 0 else float("nan")),
                spread_obs=float(m.max() - m.min()), mean=float(np.average(m, weights=n)))

POPS = {}
for w in ws:
    f = w.fil == 1
    POPS.setdefault("ALL_FILLS", []).append(f)
    POPS.setdefault("CLEAN_FILLS", []).append(f & (w.past == 0) & (w.fam != 1))
    POPS.setdefault("AT_MARKET", []).append(f & (w.atm == 1))

KINDS = ["instrument", "family", "broker_hour", "inst_x_family", "inst_x_hour"]
OUT = {}
for pop, masks in POPS.items():
    OUT[pop] = {}
    for kind in KINDS:
        minn = 50 if kind in ("instrument", "family", "broker_hour") else 30
        rows = []
        for w, m in zip(ws, masks):
            k = kk(w, kind)[m]
            dg = decomp(k, w.g[m], minn); dc = decomp(k, w.c[m], minn)
            if dg is None: continue
            rows.append({"window": w.w, "gross": dg, "cost": dc,
                         "true_sd_ratio_gross_over_cost": dg["true_sd"] / dc["true_sd"] if dc["true_sd"] > 0 else float("nan")})
        agg = {q: {"true_sd": float(np.mean([r[q]["true_sd"] for r in rows])),
                   "obs_sd": float(np.mean([r[q]["obs_sd"] for r in rows])),
                   "signal_share": float(np.mean([r[q]["signal_share"] for r in rows]))}
               for q in ("gross", "cost")}
        agg["true_sd_ratio"] = agg["gross"]["true_sd"] / agg["cost"]["true_sd"]
        OUT[pop][kind] = {"per_window": rows, "pooled_mean": agg}
        print(f"{pop:12s} {kind:14s} k={rows[0]['gross']['k']:4d} | "
              f"GROSS true_sd {agg['gross']['true_sd']:.5f} of obs {agg['gross']['obs_sd']:.5f} "
              f"(signal {agg['gross']['signal_share']*100:5.1f}%) | "
              f"COST true_sd {agg['cost']['true_sd']:.5f} of obs {agg['cost']['obs_sd']:.5f} "
              f"(signal {agg['cost']['signal_share']*100:5.1f}%) | ratio {agg['true_sd_ratio']:.4f}", flush=True)

json.dump(OUT, open("/tmp/p1/P1_VAR_V1.json", "w"))
print("WROTE /tmp/p1/P1_VAR_V1.json")
