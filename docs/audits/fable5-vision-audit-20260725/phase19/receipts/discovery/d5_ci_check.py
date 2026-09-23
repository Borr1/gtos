"""Validate the day-clustered SE against a genuine trading-day block bootstrap."""
import sys, json
import numpy as np
sys.path.insert(0, "/tmp/d5")
from d5_lib import load, dayblock_ci, WINDOWS

out = {}
for w in ("2026-01", "2026-04"):
    D = load(w)
    day = D["dayi"]
    for tag, m in (("adverse_c0<=-0.15", D["c0"] <= -0.15),
                   ("kept_c0>-0.15", D["c0"] > -0.15),
                   ("filled", D["filled"])):
        v = D["g"][m]; dd = day[m]
        lo, hi = dayblock_ci(v, dd)
        ud = np.unique(dd)
        idx = [np.nonzero(dd == u)[0] for u in ud]
        rs = np.random.default_rng(3)
        means = np.empty(500)
        for b in range(500):
            pick = rs.integers(0, len(ud), len(ud))
            means[b] = v[np.concatenate([idx[p] for p in pick])].mean()
        out["%s|%s" % (w, tag)] = {
            "n": int(v.size), "mean": float(v.mean()),
            "clustered_ci": [lo, hi],
            "block_bootstrap_ci": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))],
        }
        print(w, tag, "clust", round(lo, 5), round(hi, 5), "boot",
              round(float(np.percentile(means, 2.5)), 5), round(float(np.percentile(means, 97.5)), 5),
              flush=True)
json.dump(out, open("/tmp/d5/out/D5_CI_CHECK.json", "w"), indent=1)
