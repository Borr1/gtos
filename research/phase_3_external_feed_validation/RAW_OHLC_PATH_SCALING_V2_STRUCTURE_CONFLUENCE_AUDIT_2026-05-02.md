# V2 Structural Confluence And Disagreement Audit

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

Structural variants are alternative management policies on the same setup rows, not additive trade streams. Agreement/disagreement is informative, especially FVG-only rescue pockets, OB-after-FVG tail preservation, and Composite overlock.

## Direct Answers

- The Swing/FVG/OB/Composite R sums cannot be added; they mostly score the same event keys.
- Composite is the current 'use all registered selectors' policy, and it is not the sum of single-selector returns.
- The current V2 log can audit post-entry confluence and disagreement.
- The current V2 log cannot validate a separate pre-fill delivery-leg trade into the POI.

## Slice Summary

| Slice | n | entry consistency violations | J46 mean | Swing mean | FVG mean | OB mean | Composite mean | FVG-OB mean | Composite-best-single mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| full_resolved | 4394 | 0 | 0.149867 | 0.174381 | 0.183159 | 0.173928 | 0.107415 | 0.009231 | -0.296092 |
| year_2026 | 474 | 0 | -0.103295 | 0.205292 | 0.262680 | 0.130545 | 0.236031 | 0.132135 | -0.234958 |

## FVG vs OB Improvement Buckets

Full resolved:

| bucket | n | share | J46 mean | FVG mean | OB mean | Composite mean | FVG-OB mean | Composite-best mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| both_improve_vs_j46 | 330 | 0.075102 | -0.150523 | 0.873038 | 0.854362 | 0.704530 | 0.018676 | -0.313046 |
| fvg_only_improves_vs_j46 | 743 | 0.169094 | -0.004319 | 0.806693 | -0.048428 | 0.710383 | 0.855121 | -0.160283 |
| neither_improves_vs_j46 | 3233 | 0.735776 | 0.203136 | -0.034502 | 0.131119 | -0.101647 | -0.165621 | -0.315800 |
| ob_only_improves_vs_j46 | 88 | 0.020027 | 0.621118 | 0.328067 | 1.072442 | 0.457901 | -0.744375 | -0.655135 |

2026 only:

| bucket | n | share | J46 mean | FVG mean | OB mean | Composite mean | FVG-OB mean | Composite-best mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| both_improve_vs_j46 | 167 | 0.352321 | -0.588538 | 0.541800 | 0.651406 | 0.392131 | -0.109606 | -0.350500 |
| fvg_only_improves_vs_j46 | 86 | 0.181435 | -0.405842 | 0.813132 | -0.489932 | 0.820591 | 1.303064 | -0.122547 |
| neither_improves_vs_j46 | 215 | 0.453586 | 0.359628 | -0.180529 | -0.060479 | -0.113399 | -0.120050 | -0.159392 |
| ob_only_improves_vs_j46 | 6 | 0.012658 | 1.151082 | 0.485696 | 1.371758 | 0.033769 | -0.886062 | -1.337989 |

## Lock-Firing Buckets

Full resolved:

| bucket | n | share | J46 mean | FVG mean | OB mean | Composite mean | FVG-OB mean | Composite-best mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| both_fired | 1256 | 0.285844 | 1.362035 | 1.203571 | 1.470482 | 0.761517 | -0.266912 | -0.860874 |
| fvg_only_fired | 1136 | 0.258534 | 0.486000 | 0.799047 | 0.458096 | 0.685724 | 0.340951 | -0.319417 |
| neither_fired | 1972 | 0.448794 | -0.815319 | -0.820545 | -0.820545 | -0.649152 | 0.000000 | 0.073372 |
| ob_only_fired | 30 | 0.006827 | 0.117143 | 0.117143 | 0.501072 | 0.555304 | -0.383929 | -0.053472 |

2026 only:

| bucket | n | share | J46 mean | FVG mean | OB mean | Composite mean | FVG-OB mean | Composite-best mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| both_fired | 305 | 0.643460 | 0.286359 | 0.524723 | 0.649768 | 0.349248 | -0.125045 | -0.408950 |
| fvg_only_fired | 71 | 0.149789 | -0.726295 | 0.693013 | -0.726295 | 0.782035 | 1.419308 | -0.079491 |
| neither_fired | 98 | 0.206751 | -0.864635 | -0.864635 | -0.864635 | -0.511903 | 0.000000 | 0.193915 |

## Sequence When Both FVG And OB Fire

Full both-lock events: 1256

| sequence | n | share | J46 mean | FVG mean | OB mean | Composite mean | FVG-OB mean | OB floor - FVG floor | OB index - FVG index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fvg_then_ob | 1075 | 0.855892 | 1.341060 | 1.124681 | 1.427288 | 0.763450 | -0.302607 | 0.142855 | 11.861395 |
| ob_then_fvg | 130 | 0.103503 | 1.589570 | 1.595068 | 1.663110 | 0.763749 | -0.068043 | -0.626425 | -2.846154 |
| same_time | 51 | 0.040605 | 1.224162 | 1.868510 | 1.889935 | 0.715085 | -0.021425 | -0.628866 | 0.000000 |

2026 both-lock events: 305

| sequence | n | share | J46 mean | FVG mean | OB mean | Composite mean | FVG-OB mean | OB floor - FVG floor | OB index - FVG index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fvg_then_ob | 282 | 0.924590 | 0.351392 | 0.520626 | 0.650964 | 0.354092 | -0.130338 | 0.100535 | 22.790780 |
| ob_then_fvg | 8 | 0.026230 | 0.499626 | 0.554562 | 0.489936 | 0.420050 | 0.064625 | -0.157906 | -10.500000 |
| same_time | 15 | 0.049180 | -1.050000 | 0.585828 | 0.712526 | 0.220429 | -0.126698 | -0.523884 | 0.000000 |

## Composite vs Best Single Selector

- Full resolved mean Composite minus best single: `-0.296092`, sum `-1301.028648`.
- 2026 mean Composite minus best single: `-0.234958`, sum `-111.369935`.

Full resolved:

| bucket | n | share | J46 mean | FVG mean | OB mean | Composite mean | FVG-OB mean | Composite-best mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| composite_above_best_single | 590 | 0.134274 | -0.019065 | 0.355055 | 0.056183 | 0.899656 | 0.298872 | 0.408375 |
| composite_below_best_single | 1669 | 0.379836 | 1.262178 | 1.083043 | 1.309092 | 0.582309 | -0.226049 | -0.923888 |
| composite_matches_best_single | 2135 | 0.485890 | -0.672979 | -0.567812 | -0.680928 | -0.482759 | 0.113116 | 0.000000 |

2026 only:

| bucket | n | share | J46 mean | FVG mean | OB mean | Composite mean | FVG-OB mean | Composite-best mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| composite_above_best_single | 95 | 0.200422 | -0.202370 | 0.352073 | -0.102188 | 0.837959 | 0.454260 | 0.308881 |
| composite_below_best_single | 270 | 0.569620 | 0.207864 | 0.557360 | 0.596289 | 0.279724 | -0.038929 | -0.521162 |
| composite_matches_best_single | 109 | 0.229958 | -0.787705 | -0.545172 | -0.820295 | -0.396816 | 0.275123 | 0.000000 |

## Example Disagreements

Largest 2026 FVG-over-OB examples:

| event | symbol | session | side | J46 | FVG | OB | Composite | FVG-OB | FVG fired | OB fired | FVG outcome | OB outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD\|2026-01-13T15:15:00+00:00 | XAUUSD | ny | LONG | -1.050000 | 1.314986 | -1.050000 | 0.681998 | 2.364986 | True | False | LOCK_STOP | SL |
| XAUUSD\|2026-01-13T15:30:00+00:00 | XAUUSD | ny | LONG | -1.050000 | 1.314162 | -1.050000 | 0.681556 | 2.364162 | True | False | LOCK_STOP | SL |
| XAUUSD\|2026-01-13T16:15:00+00:00 | XAUUSD | ny | LONG | -1.050000 | 1.297409 | -1.050000 | 1.041794 | 2.347409 | True | False | LOCK_STOP | SL |
| XAUUSD\|2026-01-13T16:30:00+00:00 | XAUUSD | ny | LONG | -1.050000 | 1.288524 | -1.050000 | 1.034594 | 2.338524 | True | False | LOCK_STOP | SL |
| XAUUSD\|2026-01-13T15:45:00+00:00 | XAUUSD | ny | LONG | -1.050000 | 1.286134 | -1.050000 | 0.666525 | 2.336134 | True | False | LOCK_STOP | SL |
| XAUUSD\|2026-01-13T16:00:00+00:00 | XAUUSD | ny | LONG | -1.050000 | 1.285067 | -1.050000 | 1.031793 | 2.335067 | True | False | LOCK_STOP | SL |
| XAUUSD\|2026-01-13T16:45:00+00:00 | XAUUSD | ny | LONG | -1.050000 | 1.283761 | -1.050000 | 1.030735 | 2.333761 | True | False | LOCK_STOP | SL |
| XAUUSD\|2026-01-13T17:00:00+00:00 | XAUUSD | ny | LONG | -1.050000 | 1.267286 | -1.050000 | 0.656418 | 2.317286 | True | False | LOCK_STOP | SL |

Largest 2026 OB-over-FVG examples:

| event | symbol | session | side | J46 | FVG | OB | Composite | FVG-OB | FVG fired | OB fired | FVG outcome | OB outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| XAUUSD\|2026-01-22T16:45:00+00:00 | XAUUSD | ny | LONG | 4.329986 | 0.217985 | 2.584211 | 0.240155 | -2.366226 | True | True | LOCK_STOP | LOCK_STOP |
| XAUUSD\|2026-01-12T15:15:00+00:00 | XAUUSD | ny | LONG | 1.531889 | 0.567306 | 1.759844 | -0.030316 | -1.192538 | True | True | LOCK_STOP | LOCK_STOP |
| XAUUSD\|2026-01-12T15:30:00+00:00 | XAUUSD | ny | LONG | 1.528837 | 0.566115 | 1.756353 | -0.030354 | -1.190238 | True | True | LOCK_STOP | LOCK_STOP |
| XAUUSD\|2026-01-12T15:45:00+00:00 | XAUUSD | ny | LONG | 1.524585 | 0.564456 | 1.751488 | -0.030407 | -1.187032 | True | True | LOCK_STOP | LOCK_STOP |
| XAUUSD\|2026-01-12T16:00:00+00:00 | XAUUSD | ny | LONG | 1.511369 | 0.559298 | 1.736368 | -0.030571 | -1.177070 | True | True | LOCK_STOP | LOCK_STOP |
| XAUUSD\|2026-01-20T16:15:00+00:00 | XAUUSD | ny | LONG | 2.035141 | 0.273434 | 1.083383 | 0.289797 | -0.809949 | True | True | LOCK_STOP | LOCK_STOP |
| XAUUSD\|2026-01-20T16:30:00+00:00 | XAUUSD | ny | LONG | 2.027754 | 0.272288 | 1.079368 | 0.272288 | -0.807080 | True | True | LOCK_STOP | LOCK_STOP |
| XAGUSD\|2026-02-03T10:15:00+00:00 | XAGUSD | london | LONG | 0.822860 | -0.026804 | 0.660104 | 0.077321 | -0.686908 | True | True | LOCK_STOP | LOCK_STOP |

## Approach-Leg Assessment

Status: `NOT_ANSWERABLE_FROM_CURRENT_V2_EVENT_LOG`

The V2 event log is a post-fill path-management log. It has same-event entry/SL/TP and post-fill locks, but it does not retain the full pre-fill delivery path from setup decision to pending-limit touch.

Required future fields:

- `original_poi_type_and_bounds`
- `pending_limit_created_utc`
- `setup_decision_close_utc`
- `pre_fill_m1_or_m5_path_rows_until_fill_expiry_or_cancel`
- `as_of_delivery_direction_structures_before_fill`
- `delivery_leg_candidate_entry_sl_tp_and_costs`
- `reversal_leg_candidate_entry_sl_tp_and_costs`
- `mutual_exclusion_or_aggregate_risk_budget_policy`
- `broker_fill_or_pending_intent_lifecycle_state`

## Candidate Hypotheses

- `H1_POST_ENTRY_OB_AFTER_FVG_TAIL_PRESERVATION` (DISCOVERY_ONLY_NOT_REGISTERED): When FVG and OB both fire post-entry, FVG usually fires first and OB often preserves more right tail; test whether FVG should confirm delivery while OB sets the protective floor.
- `H2_FVG_ONLY_RESCUE_WHEN_OB_DOES_NOT_FORM` (DISCOVERY_ONLY_NOT_REGISTERED): Rows where FVG fires but OB does not may be a separate rescue pocket; test for concentration, regime, and forward survival before any rule registration.
- `H3_COMPOSITE_OVERLOCK_ARBITRATION` (DISCOVERY_ONLY_NOT_REGISTERED): Composite highest-floor policy often underperforms the best single selector; future composite logic should require arbitration, not blind highest-floor use.
- `H4_DELIVERY_LEG_AND_REVERSAL_LEG_DOUBLE_SETUP` (DATA_GAP_SPEC_ONLY): The owner's two-move idea is coherent but needs pre-fill path and risk-budget telemetry before it can be scored.

## Ambiguity Ledger

- Same-event confluence is still discovery-set evidence and cannot validate live logic.
- FVG-only and OB-only pockets may be concentrated by symbol/session/side/role.
- The event log has first lock metadata but not every pre-fill structure needed for the two-leg delivery/reversal hypothesis.
- R costs are still sensitivity assumptions, not broker-reconciled spread/slippage/commission.

## Next Steps

1. Register a forward-only confluence ledger for FVG/OB agreement and disagreement after V2b resolved rows exist.
2. Add pre-fill delivery-path capture to future path replay before testing the two-leg setup.
3. Do not promote Composite; study arbitration rules only as discovery until forward evidence exists.
4. Keep every confluence hypothesis at NO_PROMOTION_VERDICT until pre-registered unseen validation exists.
