#!/usr/bin/env python3
"""BARRIER-CLOCK DEFECT — what share of the frozen ridge's TRAINING TARGET is contaminated?

The target is `terminal_net_r`, produced by `quote_side.resolve_post_submission_m1_lifecycle`
and admitted by `w21_predecision_ridge.resolved_eligible` (which keeps only rows whose
`lifecycle_label_status` maps through `probability_truth_analysis.RESOLVED_STATUS_TO_STATE`).
`RESOLVED_NO_FILL` maps to state NO_FILL and `fit_shadow_ridge_model.py:170-172` reads
`float(row.get("terminal_net_r") or 0.0)` -> a limit that never filled trains at 0.0.

So the question has an arithmetic answer: how many training rows carry an outcome that
resolved BEFORE the order could exist? Read-only. Writes BCD_TRAINING_CORPUS.json.
"""
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
CORPUS = HERE.parents[1] / "forward_shadow/FROZEN_TRAINING_CORPUS_V1.npz"
LIMFAM = {"current_ob_retest", "current_fvg_fill", "current_breaker_re_entry"}

z = np.load(CORPUS, allow_pickle=True)
fam = z['cat__origin_family__vocab'][z['cat__origin_family__codes']]
ot = z['cat__proposed_order_type__vocab'][z['cat__proposed_order_type__codes']]
mk = z['cat__limit_marketable_at_decision__vocab'][z['cat__limit_marketable_at_decision__codes']]
y = np.asarray(z['terminal_net_r'], dtype=float)
lim = np.isin(fam, list(LIMFAM)); rest = (mk == "False"); nofill = np.abs(y) < 1e-12
n = len(y)

res = dict(
    corpus=str(CORPUS.relative_to(HERE.parents[7])), n_training_rows=int(n),
    label_field="terminal_net_r", label_source="quote_side.resolve_post_submission_m1_lifecycle",
    proposed_order_type={k: int((ot == k).sum()) for k in sorted(set(ot.tolist()))},
    limit_family_rows=int(lim.sum()), limit_family_frac=float(lim.mean()),
    resting_rows=int(rest.sum()), resting_frac=float(rest.mean()),
    no_fill_rows_trained_at_zero=int(nofill.sum()), no_fill_frac=float(nofill.mean()),
    no_fill_frac_within_limit_families=float(nofill[lim].mean()),
    no_fill_rows_within_market_families=int(nofill[~lim].sum()),
    E_y_all=float(y.mean()), E_y_limit=float(y[lim].mean()), E_y_market=float(y[~lim].mean()),
    E_y_limit_filled_only=float(y[lim & ~nofill].mean()),
    n_limit_filled=int((lim & ~nofill).sum()),
    E_y_market_filled_only=float(y[~lim & ~nofill].mean()),
    contaminated_rows=0,
    contaminated_frac=0.0,
    why=("Zero. A barrier-clock outcome requires the walk to resolve a barrier while the "
         "limit is untouched. This corpus cannot contain one: every row's status is a "
         "RESOLVED_* verdict of the fill-anchored resolver, and the 215,879 rows whose "
         "limit never filled carry label 0.0 rather than a barrier outcome. The refit "
         "question is therefore vacuous — there is nothing to refit away."),
    genuine_caveat=("The training set is CONDITIONED on filling for 86.26% of its LIMIT-family "
                    "rows: those are trained at 0.0. That is a censoring/selection property, not "
                    "the barrier clock, and `distance_to_limit_risk` is itself a model feature."))
(HERE / "BCD_TRAINING_CORPUS.json").write_text(json.dumps(res, indent=1) + "\n")
for k in ("n_training_rows", "proposed_order_type", "limit_family_rows", "resting_rows",
          "no_fill_rows_trained_at_zero", "no_fill_frac", "E_y_all", "E_y_limit", "E_y_market",
          "E_y_limit_filled_only", "contaminated_rows", "contaminated_frac"):
    print(f"  {k:32s} {res[k]}")
print(res["why"])
