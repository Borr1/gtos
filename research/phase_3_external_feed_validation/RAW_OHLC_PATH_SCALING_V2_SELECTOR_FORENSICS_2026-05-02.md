# V2 Selector Forensics: FVG vs OB Boundary

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Synthesis

V2 selector forensics confirm that FVG can lead headline/2026 returns while still being a weaker V2b level-quality candidate than OB-boundary.

Recommended V2b candidate: `STRUCT_OB_BOUNDARY_V2`

FVG has the larger headline mean delta, but OB-boundary is the only inspected selector that is nonnegative across all major target/control/blocker groups.

## Headline Selector Profile

| Variant | paired n | candidate mean R | mean delta vs J46 | activation rate | all groups >=0 | target mean delta | blocked mean delta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| STRUCT_SWING_PROTECTED_V2 | 4394 | 0.174381 | 0.024514 | 0.421711 | False | -0.037788 | 0.114208 |
| STRUCT_FVG_MID_EDGE_V2 | 4394 | 0.183159 | 0.033292 | 0.484069 | False | -0.067228 | 0.125718 |
| STRUCT_OB_BOUNDARY_V2 | 4394 | 0.173928 | 0.024061 | 0.201183 | True | 0.041812 | 0.012090 |
| STRUCT_COMPOSITE_ANY_V2 | 4394 | 0.107415 | -0.042453 | 0.650205 | False | -0.119764 | -0.032036 |

## Year Profile

| Variant | Year | paired n | candidate mean R | mean delta vs J46 |
| --- | --- | --- | --- | --- |
| STRUCT_SWING_PROTECTED_V2 | 2022 | 495 | 0.012378 | -0.159927 |
| STRUCT_SWING_PROTECTED_V2 | 2023 | 1121 | 0.090285 | 0.021496 |
| STRUCT_SWING_PROTECTED_V2 | 2024 | 765 | 0.145031 | -0.041632 |
| STRUCT_SWING_PROTECTED_V2 | 2025 | 1539 | 0.292812 | 0.031423 |
| STRUCT_SWING_PROTECTED_V2 | 2026 | 474 | 0.205292 | 0.308587 |
| STRUCT_FVG_MID_EDGE_V2 | 2022 | 495 | 0.030184 | -0.142121 |
| STRUCT_FVG_MID_EDGE_V2 | 2023 | 1121 | 0.098368 | 0.029579 |
| STRUCT_FVG_MID_EDGE_V2 | 2024 | 765 | 0.105454 | -0.081209 |
| STRUCT_FVG_MID_EDGE_V2 | 2025 | 1539 | 0.308258 | 0.046868 |
| STRUCT_FVG_MID_EDGE_V2 | 2026 | 474 | 0.262680 | 0.365975 |
| STRUCT_OB_BOUNDARY_V2 | 2022 | 495 | 0.166540 | -0.005765 |
| STRUCT_OB_BOUNDARY_V2 | 2023 | 1121 | 0.044020 | -0.024769 |
| STRUCT_OB_BOUNDARY_V2 | 2024 | 765 | 0.154141 | -0.032522 |
| STRUCT_OB_BOUNDARY_V2 | 2025 | 1539 | 0.294127 | 0.032738 |
| STRUCT_OB_BOUNDARY_V2 | 2026 | 474 | 0.130545 | 0.233839 |
| STRUCT_COMPOSITE_ANY_V2 | 2022 | 495 | -0.023215 | -0.195520 |
| STRUCT_COMPOSITE_ANY_V2 | 2023 | 1121 | 0.101258 | 0.032469 |
| STRUCT_COMPOSITE_ANY_V2 | 2024 | 765 | 0.086979 | -0.099684 |
| STRUCT_COMPOSITE_ANY_V2 | 2025 | 1539 | 0.124460 | -0.136929 |
| STRUCT_COMPOSITE_ANY_V2 | 2026 | 474 | 0.236031 | 0.339326 |

## Major Group Deltas

| Variant | Group | paired n | mean delta | sum delta |
| --- | --- | --- | --- | --- |
| STRUCT_SWING_PROTECTED_V2 | all_enabled | 4394 | 0.024514 | 107.714286 |
| STRUCT_SWING_PROTECTED_V2 | all_excluding_gbpusd_control | 3679 | 0.033397 | 122.867972 |
| STRUCT_SWING_PROTECTED_V2 | target_cohorts | 1399 | -0.037788 | -52.864989 |
| STRUCT_SWING_PROTECTED_V2 | primary_controlled_family | 674 | -0.059012 | -39.773892 |
| STRUCT_SWING_PROTECTED_V2 | cleared_non_primary_targets | 725 | -0.018057 | -13.091097 |
| STRUCT_SWING_PROTECTED_V2 | negative_controls | 1518 | -0.005339 | -8.105335 |
| STRUCT_SWING_PROTECTED_V2 | blocked_dominance_controls | 1477 | 0.114208 | 168.684610 |
| STRUCT_FVG_MID_EDGE_V2 | all_enabled | 4394 | 0.033292 | 146.285141 |
| STRUCT_FVG_MID_EDGE_V2 | all_excluding_gbpusd_control | 3679 | 0.027385 | 100.747890 |
| STRUCT_FVG_MID_EDGE_V2 | target_cohorts | 1399 | -0.067228 | -94.051628 |
| STRUCT_FVG_MID_EDGE_V2 | primary_controlled_family | 674 | -0.002547 | -1.716684 |
| STRUCT_FVG_MID_EDGE_V2 | cleared_non_primary_targets | 725 | -0.127359 | -92.334944 |
| STRUCT_FVG_MID_EDGE_V2 | negative_controls | 1518 | 0.036002 | 54.651223 |
| STRUCT_FVG_MID_EDGE_V2 | blocked_dominance_controls | 1477 | 0.125718 | 185.685546 |
| STRUCT_OB_BOUNDARY_V2 | all_enabled | 4394 | 0.024061 | 105.724281 |
| STRUCT_OB_BOUNDARY_V2 | all_excluding_gbpusd_control | 3679 | 0.020134 | 74.074581 |
| STRUCT_OB_BOUNDARY_V2 | target_cohorts | 1399 | 0.041812 | 58.494471 |
| STRUCT_OB_BOUNDARY_V2 | primary_controlled_family | 674 | 0.058222 | 39.241541 |
| STRUCT_OB_BOUNDARY_V2 | cleared_non_primary_targets | 725 | 0.026556 | 19.252930 |
| STRUCT_OB_BOUNDARY_V2 | negative_controls | 1518 | 0.019349 | 29.372254 |
| STRUCT_OB_BOUNDARY_V2 | blocked_dominance_controls | 1477 | 0.012090 | 17.857556 |
| STRUCT_COMPOSITE_ANY_V2 | all_enabled | 4394 | -0.042453 | -186.536360 |
| STRUCT_COMPOSITE_ANY_V2 | all_excluding_gbpusd_control | 3679 | -0.047678 | -175.406151 |
| STRUCT_COMPOSITE_ANY_V2 | target_cohorts | 1399 | -0.119764 | -167.549510 |
| STRUCT_COMPOSITE_ANY_V2 | primary_controlled_family | 674 | -0.123689 | -83.366705 |
| STRUCT_COMPOSITE_ANY_V2 | cleared_non_primary_targets | 725 | -0.116114 | -84.182805 |
| STRUCT_COMPOSITE_ANY_V2 | negative_controls | 1518 | 0.018663 | 28.330552 |
| STRUCT_COMPOSITE_ANY_V2 | blocked_dominance_controls | 1477 | -0.032036 | -47.317402 |

## Ambiguity Ledger

- This is same-event-log forensics and cannot validate V2b.
- The cost key is an R-sensitivity value, not measured spread/slippage.
- All V3 reentry questions remain design-only until V2b has resolved prospective pairs.

## Next Steps

1. Use OB-boundary as the registered V2b level-quality candidate.
2. Keep FVG as a comparison arm, not the primary candidate.
3. Continue post-cutoff replay collection until resolved V2b sample floors are met.
