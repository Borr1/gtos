# Phase 3 Truth-Layer Methodology Gate Readiness

**Created UTC:** 2026-05-01T08:28:52.966809+00:00
**Input:** `data\external\validation\calendar_macro_bundle_v1\historical_opportunities\truth_layer\phase3_historical_pre_ai_opportunities_v1_20260501T023603Z_truth_layer_v2_20260501T061655Z.jsonl`
**Spec:** `research\phase_3_external_feed_validation\TRUTH_LAYER_CONTROLLED_HYPOTHESES_V1.json`
**Promotion verdict:** `BLOCKED`

## Boundary

- Research/tooling only; no live trading logic, prompt, config, risk policy, or execution behavior is changed.
- Same-dataset DSR is computed as a diagnostic only.
- PBO is not computable honestly from the two selected primary cohorts alone.
- Historical matrix effective_N is available only as a separate diagnostic; prospective effective_N is still absent.
- No alpha promotion or live improvement is authorized by this report.

## Gate Matrix

| same_dataset_dsr_diagnostic | pbo | true_effective_n | untouched_holdout | prospective_validation |
| --- | --- | --- | --- | --- |
| COMPUTED_DIAGNOSTIC_ONLY | BLOCKED_NOT_COMPUTABLE_FROM_PRIMARY_TWO_ONLY | BLOCKED_HISTORICAL_MATRIX_DIAGNOSTIC_ONLY | ABSENT | ABSENT |

## Same-Dataset DSR Diagnostics

| hypothesis_id | cohort_key | status | n | mean_r | std_r | sharpe_observed | dsr_corrected_p | threshold_p_lt_0_01_met | promotion_usable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H-P3-TL-JPY-001 | USDJPY\|tokyo\|bearish\|D1 | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY | 212 | 0.630181 | 1.187888 | 0.530505 | 0.000219939063 | True | False |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | COMPUTED_SAME_DATASET_DIAGNOSTIC_ONLY | 430 | 0.493024 | 1.196187 | 0.412163 | 5.8104e-07 | True | False |

## Fold Proxy

| hypothesis_id | cohort_key | valid_year_folds | positive_valid_year_folds | max_year_resolved_share | proxy_effective_n_note |
| --- | --- | --- | --- | --- | --- |
| H-P3-TL-JPY-001 | USDJPY\|tokyo\|bearish\|D1 | 3 | 3 | 0.330189 | Calendar-year fold count is a stability proxy only; it is not true ONC/CPCV effective_N. |
| H-P3-TL-JPY-002 | GBPJPY\|tokyo\|bullish\|D1 | 4 | 4 | 0.413953 | Calendar-year fold count is a stability proxy only; it is not true ONC/CPCV effective_N. |

## PBO Blocker

| status | reason | minimum_inputs_for_posthoc_diagnostic | minimum_inputs_for_promotion_grade_pbo |
| --- | --- | --- | --- |
| BLOCKED_NOT_COMPUTABLE_HONESTLY_FROM_CURRENT_PRIMARY_TWO_ONLY | PBO estimates overfit risk from selecting a best strategy or hyperparameter from a candidate matrix. The current artifact has two already-selected primary cohorts and an explicit rule to report both, so there is no valid IS-best/OOS-rank selection matrix. | Full pre-selection cohort universe, not only the two selected primary cohorts; Frozen selection metric used to choose cohorts; Periodized performance matrix with a documented missing-period policy; At least two candidate strategies and enough periods for CSCV splits; Explicit label that any result is post-hoc and not promotion-grade | Selection universe and metric frozen before evaluation; Untouched holdout or prospective period not used for cohort discovery; CSCV/PBO run on all candidates in the registered universe |

## Effective-N Blocker

| status | available_proxy | why_proxy_is_insufficient | separate_matrix_diagnostic | minimum_inputs |
| --- | --- | --- | --- | --- |
| BLOCKED_HISTORICAL_MATRIX_DIAGNOSTIC_ONLY | calendar_year_valid_fold_count | Year-fold count shows temporal spread, but promotion-grade effective_N requires dependence-adjusted path or candidate-matrix returns. A separate historical matrix diagnostic now exists, but it is not promotion-usable because the matrix was frozen after historical discovery. | research/phase_3_external_feed_validation/TRUTH_LAYER_EFFECTIVE_N_DIAGNOSTIC_2026-05-01.md | Registered validation path definitions; Path-level return or score vectors for every registered candidate; Correlation matrix across paths/candidates; ONC or equivalent dependence-adjustment method |

## Next Actions

| rank | action | purpose |
| --- | --- | --- |
| 1 | Review post-hoc PBO diagnostic before any prospective spend | Quantify same-dataset selection pressure without treating it as promotion-grade PBO. |
| 2 | Use prospective holdout plan for future rows | Create the first promotion-eligible validation surface. |
| 3 | Add true effective_N infrastructure for Phase 3 candidate matrices | Replace year-fold proxy with correlation-adjusted path independence. |
| 4 | Enrich actual realized-R records separately | Bridge mechanical truth-layer diagnostics to live architecture evidence. |

## Synthesis

- The two primary cohorts remain controlled-research candidates, not deployable alpha.
- The same-dataset DSR diagnostic is allowed to inform priority, but it cannot override the selection-bias boundary.
- The next non-ambiguous work is future-row collection through the prospective holdout plan plus true effective_N infrastructure.
