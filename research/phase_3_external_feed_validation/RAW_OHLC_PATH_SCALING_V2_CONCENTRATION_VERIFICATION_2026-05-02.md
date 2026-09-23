# V2 Structural Path Scaling Concentration Verification

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Verification verdict: `PASS`

## Synthesis

V2 concentration numbers were recomputed from the event log. The headline structural signal remains real but concentration-blocked for general promotion; OB-boundary remains the cleanest V2b validation candidate.

## Pairwise Recompute Versus J46

| Variant | paired n | mean delta | sum delta | candidate better | J46 better |
| --- | --- | --- | --- | --- | --- |
| STRUCT_SWING_PROTECTED_V2 | 4394 | 0.024514 | 107.714286 | 1046 | 807 |
| STRUCT_BOS_LEVEL_V2 | 4394 | 0.022727 | 99.863803 | 777 | 776 |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | 4394 | -0.038580 | -169.521266 | 1153 | 1134 |
| STRUCT_FVG_MID_EDGE_V2 | 4394 | 0.033292 | 146.285141 | 1073 | 1054 |
| STRUCT_OB_BOUNDARY_V2 | 4394 | 0.024061 | 105.724281 | 418 | 466 |
| STRUCT_LIQUIDITY_RUN_V2 | 4394 | 0.010034 | 44.091290 | 781 | 712 |
| STRUCT_COMPOSITE_ANY_V2 | 4394 | -0.042453 | -186.536360 | 1477 | 1380 |

## Summary-JSON Verification

| Variant | all fields passed |
| --- | --- |
| STRUCT_SWING_PROTECTED_V2 | True |
| STRUCT_BOS_LEVEL_V2 | True |
| STRUCT_DISPLACEMENT_HALFBACK_V2 | True |
| STRUCT_FVG_MID_EDGE_V2 | True |
| STRUCT_OB_BOUNDARY_V2 | True |
| STRUCT_LIQUIDITY_RUN_V2 | True |
| STRUCT_COMPOSITE_ANY_V2 | True |

## Decision Readout

- Headline winner concentration status: `CONCENTRATION_BLOCKED`
- Headline winner top-four positive cohort share: 0.962136
- Recommended V2b candidate: `STRUCT_OB_BOUNDARY_V2`
- Recommended comparison arms: ['STRUCT_SWING_PROTECTED_V2', 'STRUCT_FVG_MID_EDGE_V2', 'J46_J49_ONLY']
- Registration action: `REGISTER_OB_BOUNDARY_VALIDATION_HYPOTHESIS_NOT_PROMOTION`

## OB Boundary Group Deltas

| Group | paired n | mean delta | sum delta |
| --- | --- | --- | --- |
| all_enabled | 4394 | 0.024061 | 105.724281 |
| all_excluding_gbpusd_control | 3679 | 0.020134 | 74.074581 |
| target_cohorts | 1399 | 0.041812 | 58.494471 |
| primary_controlled_family | 674 | 0.058222 | 39.241541 |
| cleared_non_primary_targets | 725 | 0.026556 | 19.252930 |
| negative_controls | 1518 | 0.019349 | 29.372254 |
| blocked_dominance_controls | 1477 | 0.012090 | 17.857556 |

## Swing Protected Top Cohorts

| Cohort | paired n | mean delta | sum delta |
| --- | --- | --- | --- |
| NAS100|ny|bullish|D1 | 732 | 0.161424 | 118.162180 |
| GBPJPY|tokyo|bullish|D1 | 455 | 0.140627 | 63.985417 |
| USDJPY|tokyo|bearish|H4+H1_consensus | 257 | 0.220326 | 56.623685 |
| US30_cash|ny|bullish|H4+H1_consensus | 278 | 0.186988 | 51.982632 |
| USDJPY|london|bullish|D1 | 346 | 0.016898 | 5.846673 |
| XAGUSD|london|bullish|D1 | 319 | 0.013774 | 4.393937 |
| USDJPY|tokyo|bullish|D1 | 457 | 0.002629 | 1.201678 |
| XAUUSD|ny|bullish|D1 | 467 | -0.003127 | -1.460202 |

## Ambiguity Ledger

- This verifies internal consistency against the same event log; it is not an out-of-sample validation.
- Cost remains R-sensitivity, not measured historical broker spread/slippage.
- Concentration broadness is diagnostic; final V2b gates must be pre-registered before a new validation run.

## Open Questions

1. Will OB-boundary floors remain positive on a fresh validation lane?
2. Will OB-boundary retain lower truncation once measured on unseen rows?
3. Should V2b be cohort-specific if broadness gates fail again?

## Next Steps

1. Register V2b around OB-boundary floors with swing/FVG comparison arms and explicit concentration gates.
2. Do not proceed to V3 reentry until V2b validation either passes or clearly fails.
3. Keep NO_PROMOTION_VERDICT because this audit is same-event-log verification.
