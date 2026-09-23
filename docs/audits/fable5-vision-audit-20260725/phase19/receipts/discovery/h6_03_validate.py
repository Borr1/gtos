"""h6 step 3 — validate the joint scorer against the shipped columns, then reproduce
the swarm headline THROUGH IT (not through the shipped columns)."""
import json, os, sys, time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h6_lib as H  # noqa: E402

t0 = time.time()
P, M = H.load()
print("loaded", P["F"].shape, round(time.time() - t0, 1), flush=True)

out = {}
# --- exact-agreement checks against the four shipped K-columns
checks = [("K5_TRAIL025", dict(k=5, target=None, stop=-1.0, trail=0.25, maxbars=None)),
          ("K0_INC", dict(k=0, target=2.0, stop=-1.0, trail=None, maxbars=None)),
          ("K0_TRAIL025", dict(k=0, target=None, stop=-1.0, trail=0.25, maxbars=None)),
          ("K5_INC", dict(k=5, target=2.0, stop=-1.0, trail=None, maxbars=None))]
for col, kw in checks:
    t1 = time.time()
    r, reason, eb, tr, c0 = H.walk_all(P, **kw)
    ship = M[col]
    have = np.isfinite(ship)
    both = have & tr
    d = np.abs(r[both] - ship[both])
    out[col] = {"n_shipped_nonnull": int(have.sum()), "n_tradeable": int(tr.sum()),
                "n_compared": int(both.sum()),
                "exact_frac": float((d < 1e-7).mean()), "max_abs_diff": float(d.max()),
                "mean_mine": float(r[both].mean()), "mean_shipped": float(ship[both].mean()),
                "walk_seconds": round(time.time() - t1, 3)}
    print(col, json.dumps(out[col]), flush=True)

# --- the headline, recomputed through the joint scorer
r, reason, ebar, tr, c0 = H.walk_all(P, k=5, target=None, stop=-1.0, trail=0.25)
sel = H.population(M, tr, c0)
st = H.score(r, M, sel, reason)
out["D1E1G0_through_joint_scorer"] = st
print("D1E1G0", json.dumps({k: (round(v, 6) if isinstance(v, float) else v)
                            for k, v in st.items()}), flush=True)

# per-symbol
ps = H.by_group(r, M, sel, "symbol")
out["D1E1G0_per_symbol"] = ps
out["n_symbols_gross_positive"] = sum(1 for v in ps.values() if v["gross"] > 0)
out["n_symbols_net_positive"] = sum(1 for v in ps.values() if v["net"] > 0)
bd = H.by_day(r, M, sel)
out["n_days"] = len(bd)
out["n_days_gross_positive"] = sum(1 for v in bd.values() if v["gross"] > 0)
print("sym+", out["n_symbols_gross_positive"], "net+", out["n_symbols_net_positive"],
      "days+", out["n_days_gross_positive"], "/", out["n_days"], flush=True)

# --- fill-floor: what values does execution_fill_probability take here at all?
efp = M["efp"]
vals, cnts = np.unique(efp[np.isfinite(efp)], return_counts=True)
out["efp_distribution"] = {"n_finite": int(np.isfinite(efp).sum()),
                           "n_distinct": int(len(vals)),
                           "values": [[float(v), int(c)] for v, c in
                                      zip(vals[:20], cnts[:20])]}
for f in (0.45, 0.70, 0.80, 0.90, 0.93, 0.95):
    out.setdefault("efp_floor_refusals", {})[str(f)] = int((efp < f).sum())
print("efp", json.dumps(out["efp_distribution"]), flush=True)
print("floor refusals", out["efp_floor_refusals"], flush=True)

# --- timing for the sweep budget
t1 = time.time()
for _ in range(5):
    H.walk_all(P, k=5, target=2.0, stop=-1.0, trail=0.25, maxbars=60)
out["seconds_per_walk"] = round((time.time() - t1) / 5, 4)
print("seconds_per_walk", out["seconds_per_walk"], flush=True)

json.dump(out, open(f"{D}/H6_VALIDATE_V1.json", "w"), indent=1)
