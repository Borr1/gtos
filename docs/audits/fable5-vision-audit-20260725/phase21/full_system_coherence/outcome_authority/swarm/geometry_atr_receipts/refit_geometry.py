"""Part 1.3 — refit the frozen ridge with features carrying the TRUE (as-traded) geometry.

Two arms on the frozen training corpus, using the frozen rule's exact pipeline
(`daily_refit.make_rule_pipeline`: constant-0 impute + indicator, StandardScaler,
OneHotEncoder, Ridge(alpha=10, solver="lsqr")) and the rule's 1/window sample weights:

  AS_IS     `target_distance_atr` exactly as exported (1.5*stop for Feb/Apr/May,
            2.0*stop for Oct/Nov/Jan)
  REPAIRED  `target_distance_atr` = traded_rr * stop_distance_atr, traded_rr = 2.0
            (measured: order RR 2.0 on 81,968/81,968 walked rows and on 100% of the
            Oct-27 / Nov-07 / Jan-05 sealed ledgers opened directly)

Reported on (a) the homogeneous single-basis sub-corpus, where the repair is a uniform
rescale and the arms should be provably identical after standardisation, and (b) the full
mixed-basis corpus, where the repair removes a generation-epoch marker.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/Users/borr/GTOSActive/worktrees/swarm-geom-20260811")
sys.path.insert(0, str(REPO))

from src.research_infra.wave21_forward_shadow.daily_refit import (  # noqa: E402
    load_frozen_corpus,
    make_rule_pipeline,
)
from src.research_infra.wave21_forward_shadow.feature_contract import (  # noqa: E402
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)

CORPUS = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence"
    / "outcome_authority/forward_shadow/FROZEN_TRAINING_CORPUS_V1.npz"
)
TRADED_RR = 2.0
OUT = Path("/private/tmp/geom-refit-20260811/GEOMETRY_REFIT_V1.json")


def frame_of(corpus, target_distance_atr):
    data = {name: corpus.columns[name] for name in CATEGORICAL_FEATURES}
    for name in NUMERIC_FEATURES:
        data[name] = (
            target_distance_atr
            if name == "target_distance_atr"
            else corpus.columns[name]
        )
    return pd.DataFrame(data)


def window_weights(window_ids):
    _, inverse, counts = np.unique(window_ids, return_inverse=True, return_counts=True)
    return 1.0 / counts[inverse]


def top1_by_window(pred, y, window_ids):
    """Decision-relevant metric: mean realised net R of the top-1 pick per window."""
    order = np.lexsort((-pred, window_ids))
    ws = window_ids[order]
    first = np.ones(len(ws), dtype=bool)
    first[1:] = ws[1:] != ws[:-1]
    picked = y[order][first]
    return float(picked.mean()), int(picked.size), float(picked.std(ddof=1))


def evaluate(name, corpus, mask, train_mask, test_mask, arms):
    out = {"population": name, "n_rows": int(mask.sum())}
    y = corpus.y[mask]
    wid = corpus.window_ids[mask]
    w = window_weights(wid)
    tr = train_mask[mask]
    te = test_mask[mask]
    out["n_train"] = int(tr.sum())
    out["n_test"] = int(te.sum())
    preds = {}
    for arm, tdatr in arms.items():

        frame = frame_of(corpus, tdatr).iloc[mask.nonzero()[0]].reset_index(drop=True)
        model = make_rule_pipeline()
        model.fit(frame[tr], y[tr], ridge__sample_weight=w[tr])
        p = model.predict(frame)
        preds[arm] = p
        ss_res = float(np.sum((y[te] - p[te]) ** 2))
        ss_tot = float(np.sum((y[te] - y[te].mean()) ** 2))
        mean_r, n_pick, sd_pick = top1_by_window(p[te], y[te], wid[te])
        ci = 1.959963985 * sd_pick / np.sqrt(n_pick) if n_pick > 1 else float("nan")
        out[arm] = {
            "oos_r2": 1.0 - ss_res / ss_tot,
            "oos_rmse": float(np.sqrt(ss_res / te.sum())),
            "oos_pred_mean": float(p[te].mean()),
            "oos_pred_sd": float(p[te].std(ddof=1)),
            "top1_per_window_mean_net_r": mean_r,
            "top1_per_window_n": n_pick,
            "top1_per_window_ci95_halfwidth": float(ci),
        }
    a, b = preds["as_is"], preds["repaired"]
    out["arm_agreement"] = {
        "max_abs_prediction_diff": float(np.max(np.abs(a - b))),
        "mean_abs_prediction_diff": float(np.mean(np.abs(a - b))),
        "pearson_r": float(np.corrcoef(a, b)[0, 1]),
        "identical_to_1e_12": bool(np.max(np.abs(a - b)) < 1e-12),
    }
    return out


def main():
    corpus = load_frozen_corpus(CORPUS)
    sd = corpus.columns["stop_distance_atr"]
    td = corpus.columns["target_distance_atr"]
    with np.load(CORPUS, allow_pickle=False) as b:
        vocab = np.asarray([str(t) for t in b["decision_window_vocab"]], dtype=object)
        wid = vocab[b["decision_window_codes"]]
    day = np.asarray([s.split(":", 1)[1][:10] for s in wid])
    month = np.asarray([d[:7] for d in day])

    ratio = np.round(td / sd, 9)
    basis_15 = ratio == 1.5
    basis_20 = ratio == 2.0

    repaired = TRADED_RR * sd

    report = {
        "corpus": str(CORPUS),
        "rows": int(corpus.row_count),
        "traded_rr_applied": TRADED_RR,
        "basis_split": {
            "rows_frame_1p5": int(basis_15.sum()),
            "rows_frame_2p0": int(basis_20.sum()),
            "months_at_1p5": sorted(set(month[basis_15].tolist())),
            "months_at_2p0": sorted(set(month[basis_20].tolist())),
        },
        "repair_delta": {
            "rows_changed": int(np.sum(np.abs(repaired - td) > 1e-12)),
            "rows_unchanged": int(np.sum(np.abs(repaired - td) <= 1e-12)),
        },
        "populations": [],
    }

    arms_full = {"as_is": td, "repaired": repaired}

    # (a) homogeneous single-basis sub-corpus: Feb/Apr/May, frame at 1.5, traded at 2.0
    homo = basis_15
    days_h = np.unique(day[homo])
    cut_h = days_h[int(len(days_h) * 0.7)]
    report["populations"].append(
        evaluate(
            "homogeneous_1p5_basis_feb_apr_may",
            corpus,
            homo,
            day < cut_h,
            day >= cut_h,
            arms_full,
        )
    )

    # (b) full mixed-basis corpus
    days_a = np.unique(day)
    cut_a = days_a[int(len(days_a) * 0.7)]
    report["populations"].append(
        evaluate("full_mixed_basis_corpus", corpus, np.ones_like(homo), day < cut_a,
                 day >= cut_a, arms_full)
    )
    report["time_splits"] = {
        "homogeneous_test_from": str(cut_h),
        "full_test_from": str(cut_a),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
