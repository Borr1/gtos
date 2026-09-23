# Lane 1 Remaining Methodology Triage

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Question

Audit the remaining Lane 1 methodology backlog items M-10, M-11, M-14, M-15, M-5, and M-6 from committed artifacts. Close only the items with sufficient evidence and convert the rest into precise blockers/triggers.

## Classification

| id | status | classification | blocker/trigger |
| --- | --- | --- | --- |
| M-10 | DONE | Hansen SPA-style stationary bootstrap applied across current K54-class CPCV lift series. | Diagnostic only for CPCV paths; path overlap means naive SPA over-rejects if interpreted as promotion evidence. |
| M-11 | DONE | Diebold-Mariano-style HAC test computed on fold-aggregated paired AUC differences where prediction arrays exist. | K54 v4 has no stored per-row prediction arrays, so DM is path-level only for v4 and fold-aggregated for K54 v2/v3. |
| M-14 | DONE | K54 v3 conformal interval coverage has a Christoffersen unconditional coverage proxy. | Holdout 2026-04-29 to 2026-05-12 remains unopened/deferred; CPCV proxy failed coverage at p=0.00158. |
| M-15 | DONE | Bayesian normal-normal posterior track applied to K54-class lift series under CPCV-weighted SE and skeptical prior. | Bayesian posterior is parallel evidence only; it does not override DSR/PBO/effective-N promotion gates. |
| M-5 | BLOCKED_WITH_REASON | Current empirical read documented, but exact per-symbol Inoue-Kilian/Diebold vs AFML resolution is blocked. | Exact 7-symbol per-instrument resolution needs full 2022-2023 v2/v3 feature catalog and old mechanical labels for missing symbols; current K54 v3 cross-period test is v1-schema and per effective group, not full per-symbol v3. |
| M-6 | BLOCKED_WITH_REASON | Romano-Wolf StepM implementation smoke-tested on K54 v4 architecture columns, but required 47-cell panel is absent. | No observations x 47 instrument-side-regime cell performance-differential matrix was found in current artifacts. |

## K54 Lift Methodology Results

SPA and Bayesian results are diagnostic controls. They do not expose promotion p-values because DSR/PBO/effective-N gates still bind.

| series | n | mean diff | CPCV weighted SE | CPCV one-sided p | SPA-style p | Bayes P(theta>=0.04) |
| --- | --- | --- | --- | --- | --- | --- |
| k54_v2_fixed_hp | 15 | 0.0308963 | 0.064857 | 0.316903 | 0.018 | 0.235984 |
| k54_v3_master_bundle | 15 | 0.0578945 | 0.0370812 | 0.0592277 | 0 | 0.464567 |
| k54_v4_master | 15 | 0.0583554 | 0.075625 | 0.220163 | 0.004 | 0.296854 |
| k54_v4_arch_a | 15 | 0.0419095 | 0.070481 | 0.276048 | 0.014 | 0.262124 |
| k54_v4_hybrid_5 | 15 | 0.0616595 | 0.0749294 | 0.205282 | 0.0015 | 0.30678 |
| k54_v4_hybrid_4 | 15 | 0.0536141 | 0.0709732 | 0.225 | 0.0045 | 0.293383 |

## Diebold-Mariano Fold Diagnostics

K54 v2 and K54 v3 store per-row CPCV prediction arrays, so fold-level paired AUC diffs can be reconstructed by averaging predictions for each row across the CPCV paths that tested that row.

| series | folds | mean diff | HAC SE | DM stat | one-sided p |
| --- | --- | --- | --- | --- | --- |
| k54_v2_fixed_hp_fold_aggregated | 6 | 0.0449455 | 0.0324609 | 1.3846 | 0.0830867 |
| k54_v3_master_bundle_fold_aggregated | 6 | 0.0753223 | 0.0227498 | 3.31089 | 0.000464995 |

## Christoffersen Coverage

- K54 v3 conformal target coverage: `0.9`.
- Observed CPCV proxy coverage: `0.881061`.
- Christoffersen LR stat: `9.98241`.
- Christoffersen p: `0.00158043`.
- Status: `DEFERRED (holdout 2026-04-29 to 2026-05-12 not yet opened); CPCV proxy reported`.

Interpretation: the available proxy fails unconditional coverage and the true holdout gate remains unopened. This closes M-14 as a methodology test artifact, not as validation.

## M-5 Empirical Resolution

Keep AFML/CPCV-honest as promotion doctrine. Inoue-Kilian/Diebold-style in-sample or older-period evidence can be used as a diagnostic, but current artifacts do not justify replacing CPCV-honest gates.

Blocker: Exact 7-symbol per-instrument resolution needs full 2022-2023 v2/v3 feature catalog and old mechanical labels for missing symbols; current K54 v3 cross-period test is v1-schema and per effective group, not full per-symbol v3.

Trigger: After D11 missing old labels and v2/v3 feature backfill are generated, rerun per-symbol old-train/recent-test, recent-train/2026-test, and CPCV-honest comparisons side by side.

Current K54 v3 evidence is mixed: cross-period v1-schema old-train to recent-test is positive in 4/4 effective groups, but the within-recent 2024-2026 split is positive in only 1/4 groups. That is enough to keep older/in-sample evidence as discovery context, not enough to replace CPCV-honest promotion doctrine.

## M-6 StepM State

The reusable Romano-Wolf StepM harness is implemented in `src/research_infra/methodology_alternatives.py` and smoke-tested here on four K54 v4 architecture columns. This is not the requested 47-cell panel.

- Smoke-test columns: `['k54_v4_master', 'k54_v4_arch_a', 'k54_v4_hybrid_5', 'k54_v4_hybrid_4']`.
- Smoke-test rejected columns: `[]`.
- 47-cell panel candidates found: `[]`.

M-6 remains blocked until a real observations x 47 instrument-side-regime cell performance-differential matrix exists.

## Ambiguity Ledger

- SPA over CPCV path diffs is deliberately reported with the path-dependence caveat; it can over-reject and is not a promotion gate.
- K54 v4 lacks stored row-level prediction arrays, so fold-level DM reconstruction is only available for K54 v2/v3.
- M-5 exact per-symbol resolution is blocked by data shape, not by literature ambiguity.
- M-6 has a reusable implementation but lacks the required 47-cell empirical panel.

## NO_PROMOTION_VERDICT

This artifact changes research methodology bookkeeping only. It does not validate, promote, or modify any live trading behavior.
