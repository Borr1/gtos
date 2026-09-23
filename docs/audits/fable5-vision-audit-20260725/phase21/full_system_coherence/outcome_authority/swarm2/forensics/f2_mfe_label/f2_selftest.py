#!/usr/bin/env python3
"""F2 estimator fidelity receipt: MultiRidge == sklearn Pipeline(Ridge).

F2 solves ~25 targets per scored day.  Doing that with 25 sklearn fits is 25x
B3's cost, so F2 shares one Cholesky factor across targets with the same
training mask.  That is only legitimate if it is the SAME estimator.  This
asserts it against sklearn directly, including the different-mask grouping path
and the sparse one-hot + scaled-numeric layout the real design matrix uses.
"""
import json
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
from sklearn.linear_model import Ridge

sys.path.insert(0, str(Path(__file__).resolve().parent))
from f2_lib import MultiRidge, RIDGE_ALPHA

OUT = Path(__file__).resolve().parent / "receipts"


def main():
    rng = np.random.default_rng(20260812)
    n, pc, pn = 6000, 40, 15
    C = np.zeros((n, pc)); C[np.arange(n), rng.integers(0, pc, n)] = 1.0
    N = rng.normal(size=(n, pn)) * rng.uniform(0.05, 200.0, pn) + rng.uniform(-9, 9, pn)
    X = sp.csr_matrix(np.hstack([C, N]))
    scale = np.array([False] * pc + [True] * pn)
    Y = np.column_stack([N @ rng.normal(size=pn) + 3 * rng.normal(size=n),
                         rng.normal(size=n),
                         C @ rng.normal(size=pc) + rng.normal(size=n)])
    w = rng.uniform(0.02, 1.0, n)

    rep = {"cases": []}
    for tag, mask in (("all_same_mask", np.ones((n, 3), dtype=bool)),
                      ("mixed_masks", None)):
        if mask is None:
            mask = np.ones((n, 3), dtype=bool)
            mask[:1500, 1] = False
            mask[rng.random(n) < 0.3, 2] = False
        mr = MultiRidge(alpha=RIDGE_ALPHA, scale_cols=scale).fit(X, Y, w, mask)
        P = mr.predict(X)
        for k in range(3):
            idx = np.nonzero(mask[:, k])[0]
            mu = N[idx].mean(0); sd = N[idx].std(0)
            Z = np.hstack([C, (N - mu) / np.where(sd > 1e-12, sd, 1.0)])
            ref = Ridge(alpha=RIDGE_ALPHA, solver="lsqr", tol=1e-13,
                        max_iter=200000).fit(Z[idx], Y[idx, k], sample_weight=w[idx])
            d = float(np.abs(P[:, k] - ref.predict(Z)).max())
            rep["cases"].append({"case": tag, "target": k, "n_train": int(len(idx)),
                                 "max_abs_pred_diff_vs_sklearn": d, "pass": bool(d < 1e-7)})
            print(json.dumps(rep["cases"][-1]), flush=True)
    rep["all_pass"] = all(c["pass"] for c in rep["cases"])
    rep["tolerance"] = 1e-7
    rep["prereg_sha256"] = "8b038d866c95412baba06ddf420267ac2d254bdaffa28cf2de8b2b3b38025ff4"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "V2_ESTIMATOR_FIDELITY.json").write_text(json.dumps(rep, indent=1))
    print("ALL_PASS", rep["all_pass"])
    return 0 if rep["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
